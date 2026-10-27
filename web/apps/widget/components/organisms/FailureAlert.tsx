// 실패 알림(화면 디자인 mk-failure, mk-rejection). 출력이 올 자리에 서는 위험 알림이다. 실행의 실패는 원인(`cause`)마다,
// 거절은 갈래마다 web-widget 명세의 표대로 제목, 본문, 버튼을 고른다.
//
// - 제목은 알림 부품의 `title` 이고, 본문은 나머지 문장과 실행 식별자 줄(고정폭 작은 글자)이다. 버튼은 `actions`
//   자리다. 디자인은 캔버스의 제약 때문에 제목을 비우고 버튼을 본문에 넣었는데, 부품의 쓰는 법("제목에 일어난 일을,
//   본문에 까닭이나 할 일을")대로 바꿨다.
// - 실패 항목의 `message` 는 그리지 않는다. 모르는 원인과 원인 없음은 `other` 의 행이다.
// - 끝내지 못함은 원인을 단정하지 않는다. 계약의 그 항목은 실행이 결말 없이 사라졌다는 것만 말한다.
// - 다시 잇기를 멈춘 것(구독이 처리하지 못한 거절을 세 번 거듭 받았다)은 처리하지 못한 거절과 같은 문구이고 "새 대화"만
//   단다(명세 "요청이 거절될 때"의 구독 행).
import { Alert, Button } from "@agent-os/ui";
import type { FailureCause, Outcome } from "../../lib/conversation";

type NextStep = "retry" | "new";

interface Notice {
  readonly title: string;
  readonly sentence: string | null;
  readonly steps: readonly NextStep[];
}

const RETRY_LATER = "잠시 뒤 다시 보내 주세요.";

const CAUSES = {
  conversation_summary: {
    title: "앞선 대화를 정리하지 못해 끝내지 못했습니다.",
    sentence: null,
    steps: ["retry", "new"],
  },
  timeout: {
    title: "정해진 시간 안에 끝나지 않았습니다.",
    sentence: null,
    steps: ["retry", "new"],
  },
  tool_connection: {
    title: "에이전트가 쓰는 도구에 연결하지 못했습니다.",
    sentence: RETRY_LATER,
    steps: ["retry"],
  },
  model_call: {
    title: "에이전트가 모델을 부르지 못했습니다.",
    sentence: RETRY_LATER,
    steps: ["retry"],
  },
  tool_failure: {
    title: "도구가 실패했거나 거부되어 끝내지 못했습니다.",
    sentence: null,
    steps: ["retry"],
  },
  // 버튼이 없고 포커스가 입력창으로 간다(pages/WidgetScreen 의 `focusFor` 를 organisms/Composer 가 받는다).
  loop_limit: {
    title: "정해진 단계 안에 끝내지 못했습니다.",
    sentence: "요청을 나눠 보내 주세요.",
    steps: [],
  },
  resume_mismatch: {
    title: "멈춘 실행을 이어서 끝내지 못했습니다.",
    sentence: null,
    steps: ["retry"],
  },
  agent_code: {
    title: "에이전트에 문제가 있어 끝내지 못했습니다.",
    sentence: null,
    steps: ["retry"],
  },
  other: { title: "실행이 실패로 끝났습니다.", sentence: null, steps: ["retry"] },
} satisfies Record<FailureCause, Notice>;

// 받은 원인으로 찾는다. 계약 밖의 값은 생성 타입이 막지 못하고 실행 중에 온다. 객체의 키로 찾으면 `toString` 같은
// 상속된 이름이 걸린다.
const BY_CAUSE: ReadonlyMap<string, Notice> = new Map(Object.entries(CAUSES));

function causeNotice(cause: FailureCause | null): Notice {
  return (cause === null ? undefined : BY_CAUSE.get(cause)) ?? CAUSES.other;
}

const UNFINISHED: Notice = {
  title: "실행을 끝내지 못했습니다.",
  sentence: "다시 보내 주세요.",
  steps: ["retry"],
};

// 거절의 알림. 문구의 첫 문장이 제목이고 나머지가 본문이다. 실행이 서지 않아 실행 식별자가 없다. 새로 고침은 사이트의
// 일이고, 없는 에이전트는 다시 보내도 같아 둘에는 버튼이 없다.
const UNAUTHORIZED: Notice = {
  title: "로그인 정보를 받지 못했습니다.",
  sentence: "페이지를 새로 고쳐 주세요.",
  steps: [],
};

const NOT_FOUND: Notice = {
  title: "이 에이전트를 찾을 수 없습니다.",
  sentence: "사이트 관리자에게 알려 주세요.",
  steps: [],
};

const ERROR_TITLE = "요청을 처리하지 못했습니다.";

const UNAVAILABLE: Notice = {
  title: "에이전트를 지금 쓸 수 없습니다.",
  sentence: RETRY_LATER,
  steps: ["retry"],
};

export interface FailureAlertProps {
  readonly outcome: Outcome;
  /** "다시 보내기". 그 교환의 요청을 같은 규칙으로 다시 보낸다. 다시 보낼 요청 글이 없으면 null 이고 버튼을 두지 않는다. */
  readonly onRetry: (() => void) | null;
  readonly retryBlocked: boolean;
  /** "새 대화". 위쪽 띠의 것과 같다. */
  readonly onNewConversation: () => void;
  readonly newConversationBlocked: boolean;
}

interface Shown {
  readonly notice: Notice;
  /** 실행이 서지 않은 거절에는 없다. */
  readonly runId: string | null;
}

/** 결말에 맞는 알림. 실패나 거절이 아니면 null 이다. */
function shownFor(outcome: Outcome): Shown | null {
  switch (outcome.kind) {
    // 승인 묻기의 결말은 카드(organisms/ApprovalCard)가 그린다.
    case "finished":
    case "paused":
    case "expired":
      return null;
    case "failed":
      return { notice: causeNotice(outcome.cause), runId: outcome.runId };
    case "unfinished":
      return { notice: UNFINISHED, runId: outcome.runId };
    case "unauthorized":
      return { notice: UNAUTHORIZED, runId: null };
    case "not-found":
      return { notice: NOT_FOUND, runId: null };
    case "unavailable":
      return { notice: UNAVAILABLE, runId: null };
    case "error":
      return {
        notice: {
          title: ERROR_TITLE,
          sentence: RETRY_LATER,
          steps: outcome.offerNew ? ["retry", "new"] : ["retry"],
        },
        runId: null,
      };
    // 다시 이으려 한 실행이 서버에 남아 있을 수 있어 "다시 보내기"를 두지 않는다. 새로 고치면 다시 붙는다.
    case "lost":
      return { notice: { title: ERROR_TITLE, sentence: RETRY_LATER, steps: ["new"] }, runId: null };
  }
}

/** 결말이 실패나 거절이면 그 알림을, 아니면 아무것도 그리지 않는다. */
export function FailureAlert({
  outcome,
  onRetry,
  retryBlocked,
  onNewConversation,
  newConversationBlocked,
}: FailureAlertProps) {
  const shown = shownFor(outcome);
  if (shown === null) {
    return null;
  }
  const { notice, runId } = shown;
  const actions = notice.steps.flatMap((step) =>
    step === "retry" ? (
      onRetry === null ? (
        []
      ) : (
        <Button key={step} variant="secondary" disabled={retryBlocked} onClick={onRetry}>
          다시 보내기
        </Button>
      )
    ) : (
      <Button
        key={step}
        variant="secondary"
        disabled={newConversationBlocked}
        onClick={onNewConversation}
      >
        새 대화
      </Button>
    ),
  );
  return (
    <Alert tone="danger" title={notice.title} actions={actions.length === 0 ? null : actions}>
      {notice.sentence === null && runId === null ? null : (
        <div className="flex flex-col gap-1">
          {notice.sentence === null ? null : <p>{notice.sentence}</p>}
          {runId === null ? null : (
            <p className="text-small">
              실행 식별자: <span className="font-mono">{runId}</span>
            </p>
          )}
        </div>
      )}
    </Alert>
  );
}
