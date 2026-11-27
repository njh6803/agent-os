import { Alert, Button, Card, Icon, TextField } from "@agent-os/ui";
import { useId, useState } from "react";
import type { Decision } from "../../api/approval";
import type { Approval } from "../../api/conversation";
import { describeFailure, type RequestFailure } from "../../api/failure";
import type { PluginRow } from "../../api/plugins";
import { CodeBlock } from "../atoms/CodeBlock";
import { TextLink } from "../atoms/TextLink";
import { FailureAlert } from "../molecules/FailureAlert";
import { disabledFor } from "./disabledPlugins";
import { asText } from "./EventItem";

/** 꺼짐 미리 알림이 읽는 플러그인 목록(`GET /plugins`). */
export interface PluginsRead {
  /** 읽은 목록. 아직 없으면 undefined 다. 다시 읽다 실패해도 앞서 읽은 목록이 남아 있을 수 있다. */
  readonly data: readonly PluginRow[] | undefined;
  /** 마지막 읽기의 실패. 없으면 undefined 다. */
  readonly error: unknown;
}

/**
 * 거부 사유 칸에 걸린 위반의 필드. 서버의 결정 본문에서 거부 사유의 자리이고, 서버 시험
 * `tests/channel/http/test_router.py` 가 이 이름을 고정한다.
 */
const REASON_FIELD = "body.deny.reason";

/** 승인 묻기 구역의 고리. 입력 칸 위의 "승인 묻기로 가기" 링크가 여기로 온다. */
export const APPROVAL_ANCHOR = "approval";

interface ApprovalAskProps {
  readonly approval: Extract<Approval, { state: "waiting" }>;
  /** 이 실행의 에이전트. 꺼짐 미리 알림이 그 매니페스트를 본다. */
  readonly agent: string;
  /** 요청 하나가 끝날 때까지 참이다. 버튼을 막는다. */
  readonly busy: boolean;
  /** 결정 본문의 형식 오류(422). 사유 칸 아래에 보인다. */
  readonly invalid: RequestFailure | null;
  readonly plugins: PluginsRead;
  readonly onDecide: (decision: Decision) => void;
}

/**
 * 승인 묻기(admin-login 명세 "대화 화면"의 일시정지, 스토리 38~41). 대화 안의 그 도구 호출 자리에 서서 무엇을 승인하는지(도구와
 * 인자)를 보이고 거부와 승인을 받는다. 결정은 이 일시정지의 자리를 든다. 새 일시정지면 새 폼이다. 앞의 일시정지에 적던
 * 거부 사유는 남기지 않는다.
 *
 * 입력 칸의 글자는 이 부품 안에 둔다. 글을 칠 때마다 대화를 다시 그리지 않으려는 것이다.
 */
export function ApprovalAsk({
  approval,
  agent,
  busy,
  invalid,
  plugins,
  onDecide,
}: ApprovalAskProps) {
  const headingId = useId();
  // 목록을 다시 읽다 실패하면 SWR 은 옛 목록을 들고 있다. 옛 켜짐을 믿지 않는다(.claude/rules/web-admin.md). 그때는
  // 미리 알 수 없다고 말하고 버튼을 막지 않는다. 누르면 서버의 봉투가 말한다.
  const unknown = plugins.error !== undefined;
  const disabled = disabledFor(agent, unknown ? undefined : plugins.data);

  return (
    <Card as="section" padding="4" aria-labelledby={headingId} id={APPROVAL_ANCHOR}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 id={headingId} className="flex items-center gap-2 text-body font-semibold">
            <Icon name="shield-check" size="16" />
            승인 묻기
          </h2>
          <p className="text-body text-text-muted">이 도구를 부르기 전에 결정을 기다린다.</p>
        </div>
        {disabled.length > 0 ? (
          <Alert
            tone="warning"
            title={`꺼진 플러그인이 있어 재개할 수 없다: ${disabled.join(", ")}`}
          >
            다시 켜면 결정을 낼 수 있다. <TextLink href="/">플러그인 목록</TextLink>
          </Alert>
        ) : null}
        {unknown ? (
          <Alert tone="info" title="플러그인 목록을 읽지 못해 꺼진 플러그인을 미리 알 수 없다" />
        ) : null}
        <dl className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <dt className="text-small text-text-muted">
              도구 <code className="font-mono">tool</code>
            </dt>
            <dd className="font-mono text-mono font-medium wrap-anywhere">{approval.tool}</dd>
          </div>
          <div className="flex flex-col gap-2">
            <dt className="text-small text-text-muted">
              인자 <code className="font-mono">args</code>
            </dt>
            <dd>
              <CodeBlock surface="card">{asText(approval.args)}</CodeBlock>
            </dd>
          </div>
        </dl>
        <p className="text-small text-text-muted">
          결정은 로그인한 운영자 누구나 낼 수 있고 결정한 계정이 실행 기록에 남는다.
        </p>
        <DecisionForm
          key={approval.pauseIndex}
          pauseIndex={approval.pauseIndex}
          busy={busy}
          stopped={disabled.length > 0}
          invalid={invalid}
          onDecide={onDecide}
        />
      </div>
    </Card>
  );
}

interface DecisionFormProps {
  readonly pauseIndex: number;
  readonly busy: boolean;
  /** 꺼진 플러그인 때문에 재개할 수 없다. 사유 칸과 버튼 둘을 막는다. */
  readonly stopped: boolean;
  readonly invalid: RequestFailure | null;
  readonly onDecide: (decision: Decision) => void;
}

/**
 * 거부 사유와 버튼 둘. 사유 칸이 버튼 위에 서고, 버튼은 "거부"(보조) 다음 "승인"(주)이다(`.claude/rules/web-design.md`의
 * 승인 묻기). 칸의 폭이 `wide`(360px) 이상이면 버튼이 오른쪽에 나란히, 미만이면 둘이 위아래로 꽉 찬다. 거부는 사유를 적어야
 * 보낼 수 있고, 다듬어 비면 보내지 않는다(스토리 40, 41). 서버의 422 는 사유 칸 바로 아래의 알림이 메시지와 추적 식별자와
 * 위반을 모두 보이고, 사유에 걸린 위반은 사유 칸이 오류로 받는다.
 */
function DecisionForm({ pauseIndex, busy, stopped, invalid, onDecide }: DecisionFormProps) {
  const [reason, setReason] = useState("");
  const trimmed = reason.trim();
  const violations = invalid?.envelope?.violations ?? [];
  const reasonViolations = violations.filter(({ field }) => field === REASON_FIELD);
  const blocked = busy || stopped;

  return (
    <form
      className="flex flex-col gap-4"
      onSubmit={(event) => {
        // 막힌 버튼으로는 보낼 수 없고, 사유 칸(textarea)은 Enter 로 폼을 보내지 않는다. 문은 거부 버튼 하나다.
        event.preventDefault();
        onDecide({ decision: "deny", pause_index: pauseIndex, reason: trimmed });
      }}
    >
      <TextField
        variant="multi"
        rows={3}
        label="거부 사유"
        value={reason}
        onChange={setReason}
        disabled={stopped}
        help={stopped ? null : "거부하려면 적는다. 비어 있으면 거부를 보낼 수 없다."}
        error={
          reasonViolations.length === 0
            ? null
            : reasonViolations.map(({ message }) => message).join(" ")
        }
      />
      {invalid === null ? null : (
        <FailureAlert title="결정을 보내지 못했다" {...describeFailure(invalid)}>
          {violations.length === 0 ? null : (
            <ul className="flex flex-col gap-1">
              {violations.map(({ field, message }, index) => (
                // 봉투가 준 차례로만 갈린다. 같은 필드의 위반이 여럿일 수 있다.
                <li key={index}>
                  <code className="font-mono text-mono wrap-anywhere">{field}</code> {message}
                </li>
              ))}
            </ul>
          )}
        </FailureAlert>
      )}
      <div className="flex flex-col gap-2 @wide:flex-row @wide:justify-end">
        <Button variant="secondary" type="submit" disabled={blocked || trimmed === ""}>
          거부
        </Button>
        <Button
          disabled={blocked}
          onClick={() => {
            onDecide({ decision: "approve", pause_index: pauseIndex });
          }}
        >
          승인
        </Button>
      </div>
    </form>
  );
}
