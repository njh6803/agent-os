// 승인 묻기(화면 디자인 mk-approval). 에이전트가 승인 대상 도구에서 멈추면 대화 안에 서는 테두리 카드다. 위젯은 남의
// 화면을 덮지 않고 대화 안에 묻는다(web-design.md 의 패턴 기준).
//
// - 도구 이름은 고정폭 `font-medium` 이고, 인자는 lib/approval 의 글을 고정폭으로, 줄바꿈을 지키고 긴 값은 아무
//   자리에서나 꺾어 그린다. 고치거나 줄이지 않는다.
// - 버튼은 "거부"(보조)가 먼저이고 "승인"(주)이 나중이다. 창의 폭이 360px 미만이면 둘이 위아래로 꽉 차고, 이상이면
//   오른쪽에 나란히 선다(`@wide:`).
// - 사유를 서버처럼 다듬어 비거나(lib/approval 의 `blankReason`) 입력창과 같은 글자 수 상한을 넘으면 "거부"가 막힌다.
// - 보내는 동안 누른 버튼은 불러오는 중이고 다른 버튼과 사유 칸은 막힌다. 결정하면 버튼과 칸이 걷히고 한 줄이 남는다.
// - 결정이 거절되면 그 까닭의 알림이 카드 아래에 선다. 더 받을 수 없게 됐으면 카드의 버튼과 칸을 걷고 정보 알림을
//   남긴다(web-widget 명세 "요청이 거절될 때"의 결정 행).
// - 카드는 이름 "승인 묻기"의 묶음(`role="group"`)이다. 화면 디자인은 이름 있는 `<section>`(영역)이었지만, 한 대화에
//   카드가 여럿 서면 같은 이름의 영역이 겹친다(axe 의 landmark-unique 가 스토리에서 잡았다).
// - 카드가 서면 포커스가 제목으로 가고, 결정한 뒤에는 결과 줄로 간다(명세 "접근성"). 둘은 포커스 차례에 들지 않는다.
import { Alert, Button, Icon, TextField } from "@agent-os/ui";
import { useEffect, useRef, useState } from "react";
import { blankReason } from "../../lib/approval";
import { charNote } from "../../lib/chars";
import type { Approval, DecisionNotice, Decision } from "../../lib/conversation";

export interface ApprovalCardProps {
  readonly approval: Approval;
  /** 사유의 글자 수 상한(코드 포인트). 입력창과 같다. */
  readonly limit: number;
  /** 결정의 상한(429)을 기다리는 중이라 결정 버튼을 막는다. */
  readonly blocked: boolean;
  readonly onDecide: (decision: Decision) => void;
}

const FOCUS_RING =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring";

const NOTICES = {
  unauthorized: { title: "로그인 정보를 받지 못했습니다.", sentence: "페이지를 새로 고쳐 주세요." },
  conflict: { title: "결정을 보내지 못했습니다.", sentence: "잠시 뒤 다시 골라 주세요." },
  error: { title: "요청을 처리하지 못했습니다.", sentence: "잠시 뒤 다시 보내 주세요." },
} satisfies Record<DecisionNotice, { readonly title: string; readonly sentence: string }>;

export function ApprovalCard({ approval, limit, blocked, onDecide }: ApprovalCardProps) {
  const { state } = approval;
  const [reason, setReason] = useState("");
  const title = useRef<HTMLSpanElement>(null);
  const result = useRef<HTMLParagraphElement>(null);

  // 처음 설 때 결정을 기다리면 제목으로, 기다리다 결정이 서면 결과 줄로 포커스를 보낸다. 이미 결정된 채 그려진 카드는
  // 포커스를 가져가지 않는다. 스크롤은 옮기지 않는다. 포커스가 대화를 위로 굴리면 대화가 끝을 보고 있지 않은 것이 되어,
  // 결정 뒤에 오는 출력으로 내려가지 않는다(organisms/Conversation 의 스크롤 규칙).
  const decided = state.kind === "approved" || state.kind === "denied";
  const waited = useRef(state.kind === "waiting");
  useEffect(() => {
    if (decided && waited.current) {
      waited.current = false;
      result.current?.focus({ preventScroll: true });
    }
  }, [decided]);
  useEffect(() => {
    if (waited.current) {
      title.current?.focus({ preventScroll: true });
    }
  }, []);

  let footer = null;
  if (state.kind === "waiting") {
    const note = charNote(reason, limit);
    const sending = state.sending !== null;
    footer = (
      <>
        <TextField
          label="거부 사유"
          value={reason}
          onChange={setReason}
          disabled={sending}
          help={note.count ?? "거부하려면 사유를 적어 주세요."}
          error={note.overText}
        />
        <div className="grid gap-2 @wide:flex @wide:justify-end">
          <Button
            variant="secondary"
            loading={state.sending === "deny"}
            disabled={blocked || state.sending === "approve" || note.over || blankReason(reason)}
            onClick={() => {
              onDecide({ decision: "deny", reason });
            }}
          >
            거부
          </Button>
          <Button
            variant="primary"
            loading={state.sending === "approve"}
            disabled={blocked || state.sending === "deny"}
            onClick={() => {
              onDecide({ decision: "approve" });
            }}
          >
            승인
          </Button>
        </div>
      </>
    );
  } else if (decided) {
    footer = (
      <p
        ref={result}
        tabIndex={-1}
        className={`flex items-start gap-2 rounded-s text-body ${FOCUS_RING}`}
      >
        <Icon name={state.kind === "approved" ? "check" : "x"} size="16" />
        <span className="min-w-0 wrap-anywhere whitespace-pre-wrap">
          {state.kind === "approved" ? "승인했습니다" : `거부했습니다: ${state.reason}`}
        </span>
      </p>
    );
  }

  let notice = null;
  if (state.kind === "expired") {
    notice = <Alert title="이 승인 묻기는 더 이상 받을 수 없습니다." />;
  } else if (state.kind === "waiting" && state.notice !== null) {
    const { title: noticeTitle, sentence } = NOTICES[state.notice];
    notice = (
      <Alert tone="danger" title={noticeTitle}>
        <p>{sentence}</p>
      </Alert>
    );
  }

  return (
    <>
      <div
        role="group"
        aria-label="승인 묻기"
        className="flex flex-col gap-3 rounded-m border border-border p-4"
      >
        <div className="flex items-center gap-2">
          <Icon name="circle-pause" size="16" />
          <span
            ref={title}
            tabIndex={-1}
            className={`rounded-s text-body font-semibold ${FOCUS_RING}`}
          >
            승인이 필요합니다
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-small text-text-muted">도구</span>
          <span className="font-mono text-body font-medium wrap-anywhere">{approval.tool}</span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-small text-text-muted">인자</span>
          <pre className="rounded-s border border-border bg-bg p-3 font-mono text-mono wrap-anywhere whitespace-pre-wrap">
            {approval.args}
          </pre>
        </div>
        {footer}
      </div>
      {notice}
    </>
  );
}
