import { useId, useState } from "react";
import type { Decision } from "../../api/approval";
import { describeFailure, type RequestFailure } from "../../api/failure";
import type { PluginRow } from "../../api/plugins";
import type { Trace } from "../../api/traces";
import { isRejection } from "../../hooks/queries/admin";
import { useDecision } from "../../hooks/queries/approval";
import { usePlugins } from "../../hooks/queries/plugins";
import { useTokens } from "../../stores/tokens";
import { FailureNotice, type FailureNoticeProps } from "../molecules/FailureNotice";
import { asText, EventItem } from "./EventItem";

/** 트레이스가 멈춘 일시정지. 결정이 답할 자리와 무엇을 승인하는지다. */
interface Pause {
  /** 트레이스 상세 `events` 에서 `run_paused` 가 서는 인덱스. 결정이 이것을 든다(ADR 0019 이력). */
  readonly index: number;
  readonly tool: string;
  readonly args: unknown;
  /** 실행의 에이전트. 첫 이벤트(`run_started`)의 것이다. 첫 이벤트가 그것이 아니면 null 이다. */
  readonly agent: string | null;
}

/**
 * 트레이스가 일시정지에서 멈췄으면 그 일시정지. 마지막 이벤트의 종류가 `run_paused` 인지로 본다. 상세의 응답에는
 * 요약이 없어서 트레이스에서 읽는 상태는 core `run_status()` 의 이 한 갈래뿐이다(web-admin 명세 "실행 하나"). 상태의
 * 이름을 보이는 것은 목록의 요약에 맡긴다. 재개 스트림이 결말로 끝났는지는 결정의 훅이 따로 가른다. 화면은 자리를
 * 짐작하거나 스트림에서 세지 않는다.
 */
function pauseOf(trace: Trace): Pause | null {
  const index = trace.events.length - 1;
  const last = trace.events[index];
  if (last?.type !== "run_paused") {
    return null;
  }
  const first = trace.events[0];
  return {
    index,
    tool: last.tool,
    args: last.args,
    agent: first?.type === "run_started" ? first.agent : null,
  };
}

/**
 * 이 실행을 재개할 수 없게 꺼진 플러그인(ADR 0017, 0019). 실행의 에이전트와 그 매니페스트의 `mcp` 를 목록의 행과
 * 잇는다. 목록이 없거나(아직 읽는 중이거나 읽다 실패했다), 에이전트를 모르거나, 에이전트 행이 표지이거나 없으면 미리
 * 알 수 없어 비어 있다. 그때는 누르면 서버의 봉투가 말한다.
 */
function disabledFor(agent: string | null, rows: readonly PluginRow[] | undefined): string[] {
  if (agent === null || rows === undefined) {
    return [];
  }
  const row = rows.find(({ kind, name }) => kind === "agent" && name === agent);
  if (row === undefined || !("manifest" in row)) {
    return [];
  }
  const found = row.enabled ? [] : [`에이전트 ${row.name}`];
  for (const mcp of row.manifest.mcp) {
    if (rows.some(({ kind, name, enabled }) => kind === "mcp" && name === mcp && !enabled)) {
      found.push(`MCP ${mcp}`);
    }
  }
  return found;
}

/**
 * 결정 자리와 재개 스트림(web-admin 티켓 08). 실행 하나의 이벤트 아래에 선다.
 *
 * 결정 자리가 보이는 조건은 셋이다. 채널 토큰이 있고, 실행이 일시정지이고, 형식 2 트레이스다. 형식 1 이면 두지 않는다.
 * 재개할 수 없다는 이유는 실행 하나의 한 줄이 이미 말한다(스토리 52). 결정 뒤의 알림과 재개 스트림은 결정 자리 밖에
 * 선다. 다시 읽은 트레이스가 일시정지가 아니면 결정 자리는 걷히지만 무엇이 있었는지는 남는다.
 */
export function RunDecision({ runId, trace }: { readonly runId: string; readonly trace: Trace }) {
  const channelToken = useTokens((state) => state.channelToken);
  const { busy, frames, cut, failure, decide } = useDecision(runId);
  const streamId = useId();
  const pause = trace.schema_version === "2" ? pauseOf(trace) : null;
  const notice = noticeOf(failure, channelToken);

  return (
    <>
      {channelToken !== null && pause !== null ? (
        <DecisionPlace
          pause={pause}
          busy={busy}
          invalid={failure?.status === 422 ? failure : null}
          onDecide={decide}
        />
      ) : null}
      {notice === null ? null : <FailureNotice {...notice} />}
      {frames.length > 0 ? (
        <section aria-labelledby={streamId}>
          <h3 id={streamId}>재개 스트림</h3>
          <ol>
            {frames.map((frame, index) =>
              // 프레임은 받은 차례로만 갈린다. 한 번의 결정 안에서 그 차례는 바뀌지 않는다.
              frame.kind === "event" ? (
                <EventItem key={index} event={frame.event} />
              ) : (
                <li key={index}>
                  <h4>읽지 못한 프레임</h4>
                  <p style={{ whiteSpace: "pre-wrap" }}>{frame.raw}</p>
                </li>
              ),
            )}
          </ol>
        </section>
      ) : null}
      {cut ? (
        <div role="status">
          <p>재개 스트림이 끊겼다. 실행은 서버에서 계속된다</p>
          <p>창을 닫거나 떠나도 실행은 끝까지 간다. 돌아오면 트레이스로 이어 본다</p>
        </div>
      ) : null}
    </>
  );
}

/**
 * 결정 자리 밖에 보일 실패. 형식 오류(422)는 사유 옆에 서므로 여기 없다. 401 은 채널 토큰이 거부됐다는 것이고, 그
 * 토큰은 이미 내려놓았다. 새 채널 토큰을 넣으면 걷힌다. 그 밖(409 의 뜻 넷, 없는 실행, 서버 오류)은 봉투의 메시지와
 * 추적 식별자이고, 봉투가 없으면(닿지 못함) "서버에 닿지 못했다"다.
 */
function noticeOf(
  failure: RequestFailure | null,
  channelToken: string | null,
): FailureNoticeProps | null {
  if (failure === null || failure.status === 422) {
    return null;
  }
  if (isRejection(failure)) {
    return channelToken === null ? { message: "채널 토큰이 거부됐다", requestId: null } : null;
  }
  return describeFailure(failure);
}

interface DecisionPlaceProps {
  readonly pause: Pause;
  /** 결정 하나가 끝날 때까지 참이다(`useDecision` 의 `busy`). 결정 버튼을 막는다. */
  readonly busy: boolean;
  /** 결정 본문의 형식 오류(422). 사유 옆에 보인다. */
  readonly invalid: RequestFailure | null;
  readonly onDecide: (decision: Decision) => void;
}

/**
 * 결정 자리. 무엇을 승인하는지(도구와 인자)를 보이고 허가와 거부를 받는다(스토리 38~41). 허가는 버튼 하나다. 결정은
 * 이 일시정지의 자리를 든다. 다시 읽은 트레이스가 새 일시정지에서 멈추면 자리는 그대로 서고 내용만 새 일시정지다.
 */
function DecisionPlace({ pause, busy, invalid, onDecide }: DecisionPlaceProps) {
  const plugins = usePlugins();
  const headingId = useId();
  // 목록을 다시 읽다 실패하면 SWR 은 옛 목록을 들고 있다. 옛 켜짐을 믿지 않는다(.claude/rules/web-admin.md). 그때는
  // 미리 알 수 없다고 말하고 버튼을 막지 않는다. 누르면 서버의 봉투가 말한다.
  const unknown = plugins.error !== undefined;
  const disabled = disabledFor(pause.agent, unknown ? undefined : plugins.data);
  const blocked = busy || disabled.length > 0;

  return (
    <section aria-labelledby={headingId}>
      <h3 id={headingId}>결정</h3>
      <p>
        이 실행은 도구 호출 하나의 승인을 기다리며 일시정지했다. 결정은 이 호출 하나에 대한 답이다.
      </p>
      <dl>
        <dt>
          도구 <code>tool</code>
        </dt>
        <dd>{pause.tool}</dd>
        <dt>
          인자 <code>args</code>
        </dt>
        <dd style={{ whiteSpace: "pre-wrap" }}>{asText(pause.args)}</dd>
      </dl>
      <p>
        결정의 승인자는 이 화면이 고르지 않는다. <code>agent-os serve</code> 를 띄운 OS 사용자로
        기록된다.
      </p>
      {disabled.length > 0 ? (
        <p>
          꺼진 플러그인이 있어 재개할 수 없다: {disabled.join(", ")}. 다시 켜면 결정을 낼 수 있다.
        </p>
      ) : null}
      {unknown ? <p>플러그인 목록을 읽지 못해 꺼진 플러그인을 미리 알 수 없다.</p> : null}
      <button
        type="button"
        disabled={blocked}
        onClick={() => {
          onDecide({ decision: "approve", pause_index: pause.index });
        }}
      >
        허가
      </button>
      {/* 새 일시정지면 새 폼이다. 앞의 일시정지에 적던 거부 사유는 남기지 않는다. */}
      <DenyForm
        key={pause.index}
        pauseIndex={pause.index}
        blocked={blocked}
        invalid={invalid}
        onDecide={onDecide}
      />
    </section>
  );
}

interface DenyFormProps {
  readonly pauseIndex: number;
  readonly blocked: boolean;
  readonly invalid: RequestFailure | null;
  readonly onDecide: (decision: Decision) => void;
}

/** 거부. 사유를 적어야 보낼 수 있고, 다듬어 비면 보내지 않는다(스토리 40, 41). 서버의 422 는 사유 옆에 보인다. */
function DenyForm({ pauseIndex, blocked, invalid, onDecide }: DenyFormProps) {
  const [reason, setReason] = useState("");
  const invalidId = useId();
  const trimmed = reason.trim();

  return (
    <form
      onSubmit={(event) => {
        // 막힌 버튼으로는 보낼 수 없고, 사유 칸(textarea)은 Enter 로 폼을 보내지 않는다. 문은 버튼 하나다.
        event.preventDefault();
        onDecide({ decision: "deny", pause_index: pauseIndex, reason: trimmed });
      }}
    >
      <label>
        거부 사유{" "}
        <textarea
          value={reason}
          onChange={(event) => {
            setReason(event.currentTarget.value);
          }}
          aria-describedby={invalid === null ? undefined : invalidId}
        />
      </label>
      {invalid === null ? null : (
        <div id={invalidId}>
          <FailureNotice {...describeFailure(invalid)} />
          <ul>
            {invalid.envelope?.violations.map(({ field, message }, index) => (
              // 봉투가 준 차례로만 갈린다. 같은 필드의 위반이 여럿일 수 있다.
              <li key={index}>
                <code>{field}</code> {message}
              </li>
            ))}
          </ul>
        </div>
      )}
      <button type="submit" disabled={blocked || trimmed === ""}>
        거부
      </button>
    </form>
  );
}
