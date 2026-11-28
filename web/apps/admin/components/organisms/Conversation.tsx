import {
  Alert,
  Button,
  Icon,
  Markdown,
  Progress,
  StatusBadge,
  type StatusBadgeStatus,
} from "@agent-os/ui";
import type { Decision } from "../../api/approval";
import type { Approval, Outcome, Turn } from "../../api/conversation";
import type { RequestFailure } from "../../api/failure";
import { TextLink } from "../atoms/TextLink";
import { formatTime, localClock } from "../atoms/clock";
import { ScreenHeader } from "../molecules/ScreenHeader";
import { ApprovalAsk, type PluginsRead } from "./ApprovalAsk";
import { ReadSection, type ReadState } from "./ReadSection";

/** 대화 화면이 그리는 것. 첫 실행부터 끝 실행까지 차례로 든다. */
export interface ConversationData {
  readonly turns: readonly Turn[];
  /** 거슬러 읽기가 어떻게 끝났는가. `cap` 은 상한에 닿았고, `broken` 은 읽지 못한 고리에서 멈췄다. */
  readonly earlier: "start" | "cap" | "broken";
}

/** 대화 안에서 하는 일(승인 묻기와 다시 보내기)과 그것이 서는지. */
export interface ConversationActions {
  /**
   * 승인 묻기와 다시 보내기를 서게 한다. 최종 사용자의 대화는 볼 수만 있어 거짓이고, 그때는 승인 묻기가 기다리는 중인 한 줄로
   * 남고 실패에도 다시 보내기가 없다.
   */
  readonly canAct: boolean;
  /** 요청 하나가 끝날 때까지 참이다. 승인·거부·다시 보내기 버튼을 막는다. */
  readonly busy: boolean;
  /** 결정 본문의 형식 오류(422). 승인 묻기의 사유 칸 아래에 보인다. */
  readonly invalid: RequestFailure | null;
  /** 꺼짐 미리 알림이 읽는 플러그인 목록. 승인 묻기가 서 있을 때만 읽는다. */
  readonly plugins: PluginsRead;
  readonly onDecide: (runId: string, decision: Decision) => void;
  /** 끝 실행의 요청을 그 앞에서 다시 보낸다. */
  readonly onRetry: () => void;
}

interface ConversationProps extends ReadState<ConversationData> {
  /** 끝 실행이 아직 없는 새 대화. 읽을 것이 없어 읽기 골격 대신 머리만 서고, 보낸 요청이 말풍선으로 붙는다. */
  readonly fresh: boolean;
  readonly actions: ConversationActions;
  /** 마지막 실행이 결말 없이 멈출 때(마지막 이벤트 뒤 실행 제한 시간)가 지났는가. */
  readonly stale: boolean;
  /** 마지막 이벤트 뒤 멈출 때까지의 길이(초). 알림의 글에 든다. */
  readonly timeoutSeconds: number;
  /** 패널이 열려 있는 실행. 없으면 닫혀 있다. */
  readonly openRun: string | null;
  readonly onOpenRun: (runId: string) => void;
}

/** 실행의 결말이 잇는 배지. 도는 실행은 결말 없음이다(용어집). */
const BADGE = {
  finished: "done",
  failed: "failed",
  paused: "paused",
  running: "no-outcome",
} as const satisfies Record<Outcome["kind"], StatusBadgeStatus>;

/** 진행 표시의 이름. 마지막으로 받은 이벤트의 다음 일이다(명세 "대화 화면"의 진행 표시). */
const STEP_LABEL = {
  model: "모델을 부르는 중",
  tool: "도구를 부르는 중",
} as const satisfies Record<"model" | "tool", string>;

/**
 * 대화 화면(admin-login 명세 "대화 화면"). 가운데 한 열에 요청과 출력이 말풍선으로 이어진다. 끝 실행이 일시정지면 승인 묻기가
 * 그 도구 호출 자리에 서고, 실패면 실패 알림에 "다시 보내기"가 선다(`actions`). 입력 칸은 이 부품이 아니라 `Composer` 가 그린다.
 *
 * 읽는 동안은 "대화를 불러오는 중"이고 거슬러 읽기가 끝난 뒤 첫 실행부터 한 번에 그린다(위에 하나씩 덧붙이면 화면이 위로
 * 밀려 보던 자리를 잃는다). 보인 대화를 남긴 채 다시 읽는 동안은 "다시 확인하는 중"이다. 다시 읽다 실패하면 보인 것을
 * 지우고 실패만 보인다. 새로 고침과 실패의 표시는 읽기 골격(`ReadSection`)이다.
 *
 * 시각은 이 브라우저의 시간대다. 프롬프트와 도구 결과는 대화에 보이지 않고 실행 패널에서 본다.
 */
export function Conversation({
  fresh,
  actions,
  stale,
  timeoutSeconds,
  openRun,
  onOpenRun,
  ...read
}: ConversationProps) {
  const clock = localClock();
  const agent = read.data?.turns.at(-1)?.agent;
  const thread = ({ turns, earlier }: ConversationData) => (
    <div className="flex flex-col gap-8">
      <EarlierNotice earlier={earlier} />
      {turns.map((turn, index) => {
        const place = placeOf({ isEnd: index === turns.length - 1, stale });
        return (
          <TurnView
            key={turn.runId}
            turn={turn}
            number={index + 1}
            clock={clock}
            place={place}
            actions={actions}
            timeoutSeconds={timeoutSeconds}
            open={openRun === turn.runId}
            onOpen={() => {
              onOpenRun(turn.runId);
            }}
          />
        );
      })}
    </div>
  );
  return (
    <div className="mx-auto flex w-full max-w-content flex-col gap-6">
      <span className="self-start">
        <TextLink href="/chat">대화 목록</TextLink>
      </span>
      {fresh ? (
        // 새 대화는 읽을 것이 없다. 읽기 골격의 "새로 고침"이 서지 않고, 보낸 요청이 말풍선으로 붙는다.
        <section aria-label="새 대화" className="flex flex-col gap-6">
          <ScreenHeader title="새 대화" description="에이전트를 고르고 요청을 보낸다." />
          {read.data === undefined ? null : thread(read.data)}
        </section>
      ) : (
        <ReadSection
          title="대화"
          description={
            agent === undefined || read.error !== undefined ? undefined : (
              <span className="wrap-anywhere">
                에이전트 <span className="font-mono text-mono text-text">{agent}</span>
              </span>
            )
          }
          {...read}
          loadingLabel="대화를 불러오는 중"
          failureTitle="대화를 읽지 못했다"
          actions={<TextLink href="/chat/new">새 대화</TextLink>}
        >
          {thread}
        </ReadSection>
      )}
    </div>
  );
}

/** 맨 위의 알림. 상한에 닿았거나 읽지 못한 고리에서 멈췄을 때 그 사실을 알린다. */
function EarlierNotice({ earlier }: { readonly earlier: ConversationData["earlier"] }) {
  if (earlier === "cap") {
    return <Alert tone="info" title="더 앞의 대화는 이 화면에 보이지 않는다" />;
  }
  if (earlier === "broken") {
    return <Alert tone="warning" title="앞부분을 읽지 못했다" />;
  }
  return null;
}

/**
 * 실행이 대화에서 선 자리. 끝 실행이 아니면 `earlier`(앞 실행), 끝 실행이면 `end`, 끝 실행인데 주기 읽기가 멈출 때까지
 * 결말이 오지 않았으면 `end-stale`이다. 결말이 없는 실행을 어떻게 보일지가 이 셋으로 갈린다.
 */
type Place = "earlier" | "end" | "end-stale";

function placeOf({ isEnd, stale }: { readonly isEnd: boolean; readonly stale: boolean }): Place {
  if (!isEnd) {
    return "earlier";
  }
  return stale ? "end-stale" : "end";
}

interface TurnViewProps {
  readonly turn: Turn;
  /** 화면에서 센 차례(1부터). 구역의 이름이다. */
  readonly number: number;
  readonly clock: Intl.DateTimeFormat;
  readonly place: Place;
  readonly actions: ConversationActions;
  readonly timeoutSeconds: number;
  readonly open: boolean;
  readonly onOpen: () => void;
}

/**
 * 실행 하나. 요청, 도구 호출 묶음, 승인 묻기와 결정, 출력이나 실패, 그리고 상태와 시각과 "자세히"다. 기다리는 승인은 끝
 * 실행에서 `actions.canAct` 일 때 버튼이 있는 승인 묻기로 서고, 그 밖에는 기다리는 중이라는 한 줄이다.
 */
function TurnView({
  turn,
  number,
  clock,
  place,
  actions,
  timeoutSeconds,
  open,
  onOpen,
}: TurnViewProps) {
  const acts = place !== "earlier" && actions.canAct;
  return (
    <section
      aria-label={`실행 ${String(number)}`}
      aria-busy={turn.outcome.kind === "running" && place === "end"}
      className="flex flex-col gap-4"
    >
      <p className="max-w-form self-end rounded-l border border-border bg-bg-raised px-3 py-2 text-body whitespace-pre-wrap wrap-anywhere">
        {turn.request}
      </p>
      <ToolsFold tools={turn.tools} />
      {turn.approvals.map((approval) =>
        approval.state === "waiting" && acts ? (
          <ApprovalAsk
            key={approval.pauseIndex}
            approval={approval}
            agent={turn.agent}
            busy={actions.busy}
            invalid={actions.invalid}
            plugins={actions.plugins}
            onDecide={(decision) => {
              actions.onDecide(turn.runId, decision);
            }}
          />
        ) : (
          <ApprovalLine key={approval.pauseIndex} approval={approval} clock={clock} />
        ),
      )}
      <OutcomeView
        outcome={turn.outcome}
        place={place}
        timeoutSeconds={timeoutSeconds}
        retry={acts ? { busy: actions.busy, onRetry: actions.onRetry } : null}
      />
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <StatusBadge status={BADGE[turn.outcome.kind]} />
        {turn.startedAt === "" ? null : (
          // 시작 이벤트가 없는 기록(쓰기가 중간에 끊겼다)은 시각이 없다. 빈 값으로 시각을 만들면 렌더링이 던진다.
          <span className="font-mono text-mono whitespace-nowrap text-text-muted">
            {formatTime(clock, turn.startedAt)}
          </span>
        )}
        {turn.runId === "" ? null : (
          // 시작 이벤트가 오기 전의 보낸 요청은 아직 실행이 없어 패널로 열 것이 없다.
          <button
            type="button"
            aria-expanded={open}
            aria-controls={open ? "run-panel" : undefined}
            onClick={onOpen}
            className={`min-h-6 rounded-s px-2 text-small whitespace-nowrap hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring ${open ? "bg-bg-selected font-medium text-text" : "text-accent"}`}
          >
            자세히
          </button>
        )}
      </div>
    </section>
  );
}

/** 도구 호출 묶음. 접혀 있고 펼치면 도구 이름과 성공·실패가 보인다. 이름은 글자 그대로 고정폭이다. */
function ToolsFold({ tools }: { readonly tools: Turn["tools"] }) {
  if (tools.length === 0) {
    return null;
  }
  return (
    <details className="text-small text-text-muted">
      <summary className="cursor-pointer">도구 {tools.length}개를 불렀다</summary>
      <ul className="flex flex-col gap-2 pt-2 pl-6">
        {tools.map(({ tool, ok }, index) => (
          // 같은 도구를 여러 번 부를 수 있어 차례로 가른다. 차례는 바뀌지 않는다.
          <li key={index} className="flex items-center gap-2 text-table">
            <Icon name="wrench" size="14" />
            <span className="font-mono text-mono font-medium text-text">{tool}</span>
            <span className={`flex items-center gap-1 ${ok ? "text-success" : "text-danger"}`}>
              <Icon name={ok ? "circle-check" : "circle-x"} size="14" />
              {ok ? "성공" : "실패"}
            </span>
          </li>
        ))}
      </ul>
    </details>
  );
}

/** 승인 묻기 한 줄. 기다리는 중이거나 지난 결정이다. 버튼은 쓰기 티켓이 더한다. */
function ApprovalLine({
  approval,
  clock,
}: {
  readonly approval: Approval;
  readonly clock: Intl.DateTimeFormat;
}) {
  return (
    <p className="flex flex-wrap items-center gap-2 text-table">
      <span className={approval.state === "denied" ? "text-danger" : "text-success"}>
        <Icon name="shield-check" size="14" />
      </span>
      {approval.state === "waiting" ? (
        <span>
          승인을 기다리는 중: <ToolName>{approval.tool}</ToolName>
        </span>
      ) : (
        <span>
          {approval.by}가 {formatTime(clock, approval.at)}에{" "}
          {approval.state === "granted" ? "승인했다" : "거부했다"}:{" "}
          <ToolName>{approval.tool}</ToolName>
          {approval.state === "denied" && approval.reason !== "" ? ` (${approval.reason})` : null}
        </span>
      )}
    </p>
  );
}

function ToolName({ children }: { readonly children: string }) {
  return <span className="font-mono text-mono font-medium">{children}</span>;
}

/** 결말. 출력은 마크다운 부품이고 실패는 실패의 글이다. 도는 중이면 진행 표시이고, 멈출 때가 지났으면 알림이다. */
function OutcomeView({
  outcome,
  place,
  timeoutSeconds,
  retry,
}: {
  readonly outcome: Outcome;
  readonly place: Place;
  readonly timeoutSeconds: number;
  /** 실패한 끝 실행에 "다시 보내기"를 둔다. 없으면 두지 않는다. */
  readonly retry: { readonly busy: boolean; readonly onRetry: () => void } | null;
}) {
  switch (outcome.kind) {
    case "finished":
      return <Markdown text={outcome.output} />;
    case "failed":
      return (
        <Alert tone="danger" title="실행이 실패했다">
          <div className="flex flex-col gap-3">
            <span className="whitespace-pre-wrap wrap-anywhere">{outcome.error}</span>
            {retry === null || place === "earlier" ? null : (
              <span className="self-start">
                <Button variant="secondary" disabled={retry.busy} onClick={retry.onRetry}>
                  다시 보내기
                </Button>
              </span>
            )}
          </div>
        </Alert>
      );
    case "paused":
      return null;
    case "running":
      if (place === "earlier") {
        return <p className="text-small text-text-muted">이 실행은 결말 없이 끝났다</p>;
      }
      return place === "end-stale" ? (
        <Alert tone="warning" title="끝맺지 못한 것으로 보입니다">
          마지막 이벤트 뒤 {String(timeoutSeconds)}초가 지나도 결말이 오지 않아 더 읽지 않는다. 새로
          고침으로 다시 읽을 수 있다.
        </Alert>
      ) : (
        <Progress label={STEP_LABEL[outcome.step]} />
      );
  }
}
