import { Alert, Button, Card, Icon, TextField } from "@agent-os/ui";
import { useId, useState, type ReactNode } from "react";
import type { Decision, StreamFrame } from "../../api/approval";
import { describeFailure, isRejection, type RequestFailure } from "../../api/failure";
import type { PluginRow } from "../../api/plugins";
import type { Trace } from "../../api/traces";
import { CodeBlock } from "../atoms/CodeBlock";
import { TextLink } from "../atoms/TextLink";
import { EmptyLine } from "../molecules/EmptyLine";
import { FailureAlert } from "../molecules/FailureAlert";
import { asText, EventItem } from "./EventItem";
import { RunColumns } from "./RunColumns";

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
 * 주체 이름 `<발급자>|<sub>` 의 구분자. 서버의 `PRINCIPAL_SEPARATOR`(`agent_os.http.sites`)와 같은 글자이고 sdk 계약
 * 밖의 결합이다. 구분자를 바꾸는 결정은 이것을 함께 바꾼다.
 */
const PRINCIPAL_SEPARATOR = "|";

/**
 * 최종 사용자의 실행인지. 시작 이벤트(`run_started`)의 주체에 구분자가 들었는지로 본다(end-user-channel 명세 "관리
 * 화면"). 최종 사용자가 아닌 주체는 OS 사용자 이름이고, `serve`·`run`·`resume` 이 그 이름에 이 글자를 금지한다
 * (end-user-channel 티켓 01). 그래서 그 가드 뒤에 쓴 트레이스에서 이것이 든 주체는 최종 사용자다.
 */
function isEndUserRun(trace: Trace): boolean {
  const first = trace.events[0];
  return first?.type === "run_started" && first.principal.includes(PRINCIPAL_SEPARATOR);
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
 * 결정 칸에 서는 것(admin-style 명세 "실행 하나와 결정 자리"). 결정 자리(`place`), 최종 사용자의 실행이라는 한 줄
 * (`endUser`), 채널 토큰을 넣으라는 한 줄(`noChannelToken`) 가운데 하나이고, 결정할 일시정지가 없으면 null 이라 결정
 * 칸이 서지 않는다.
 */
type Column =
  | { readonly kind: "place"; readonly pause: Pause }
  | { readonly kind: "endUser" }
  | { readonly kind: "noChannelToken" };

/**
 * 결정 칸의 갈래를 한 번 고른다. 결정 칸의 내용, 재개 스트림이 서는 조건, 꺼짐 미리 알림의 플러그인 목록을 읽는
 * 조건이 모두 이것을 쓴다(admin-style 티켓 08).
 *
 * 결정 칸은 실행이 일시정지이고 형식 1 트레이스가 아닐 때만 선다. 형식 1 만 재개할 수 없으므로 "형식 1 이 아니다"로
 * 가른다 — 형식이 늘 때마다 결정 칸이 조용히 사라지지 않게(conversation 명세, 스토리 56). 재개할 수 없다는 이유는 실행
 * 하나의 한 줄이 이미 말한다(스토리 52). 최종 사용자의 실행은 그 실행의 주체만 결정하므로(ADR 0023) 채널 토큰과
 * 상관없이 그 이유 한 줄이다. 서버에 묻지 않는다. 눌러 봐야 서버가 409 로 막는다. 그 밖에 채널 토큰이 없으면 설정에서
 * 넣으라는 한 줄이고, 있으면 결정 자리다.
 */
function columnOf(
  trace: Trace,
  { channelTokenEntered }: { readonly channelTokenEntered: boolean },
): Column | null {
  const pause = trace.schema_version !== "1" ? pauseOf(trace) : null;
  if (pause === null) {
    return null;
  }
  if (isEndUserRun(trace)) {
    return { kind: "endUser" };
  }
  return channelTokenEntered ? { kind: "place", pause } : { kind: "noChannelToken" };
}

/**
 * 결정 자리가 서는가. 실행 하나의 화면은 이것이 참일 때만 꺼짐 미리 알림의 플러그인 목록을 읽어 넘긴다(`plugins`).
 */
export function decisionPlaceStands(
  trace: Trace,
  { channelTokenEntered }: { readonly channelTokenEntered: boolean },
): boolean {
  return columnOf(trace, { channelTokenEntered })?.kind === "place";
}

/** 꺼짐 미리 알림이 읽는 플러그인 목록(`GET /plugins`). */
interface PluginsRead {
  /** 읽은 목록. 아직 없으면 undefined 다. 다시 읽다 실패해도 앞서 읽은 목록이 남아 있을 수 있다. */
  readonly data: readonly PluginRow[] | undefined;
  /** 마지막 읽기의 실패. 없으면 undefined 다. */
  readonly error: unknown;
}

interface RunDecisionProps {
  readonly trace: Trace;
  /** 실행 하나의 이벤트 칸(`RunDetail`). 결정 칸과 재개 스트림이 이것 둘레에 선다. */
  readonly events: ReactNode;
  /** 이 탭에 채널 토큰이 있는가. 없으면 결정 자리 대신 채널 토큰을 넣으라는 한 줄이 선다. */
  readonly channelTokenEntered: boolean;
  /** 결정 하나가 끝날 때까지 참이다(`useDecision` 의 `busy`). 결정 버튼을 막는다. */
  readonly busy: boolean;
  /** 받는 대로 쌓은 재개 스트림의 프레임. */
  readonly frames: readonly StreamFrame[];
  /** 마지막 재개 스트림이 결말 없이 끊겼다. */
  readonly cut: boolean;
  /** 마지막 결정이 받아들여지지 않은 실패. 없으면 null 이다. */
  readonly failure: RequestFailure | null;
  readonly onDecide: (decision: Decision) => void;
  /** 결정 자리가 설 때만 읽는다(`decisionPlaceStands`). 서지 않으면 쓰지 않는다. */
  readonly plugins: PluginsRead;
}

/**
 * 실행 하나의 본문. 이벤트 칸 둘레에 결정 칸, 재개 스트림, 결정 뒤의 알림을 놓는다(web-admin 티켓 08, admin-style 티켓
 * 07·08). 결정 칸의 갈래는 `columnOf` 가 고른다. 다시 읽은 트레이스가 일시정지가 아니면 결정 칸이 걷히고 이벤트 칸이
 * 넓어지지만 무엇이 있었는지는 남는다.
 *
 * 재개 스트림은 결정 자리가 섰거나 받은 조각이 있으면 선다. 결정 뒤의 실패와 끊긴 재개 스트림의 알림은 머리 바로 아래,
 * 이벤트 칸 위다. 끊긴 알림은 패키지 `Alert`(정보, `role="status"`)가 끊길 때 영역째 들어온다. 늘 서는 빈 상태 영역에
 * 글만 바꾸는 꼴(`ReadSection`)로 두지 않았다. `Alert` 가 자기 역할을 들어 그 둘레에 상태 영역을 또 두면 겹친다.
 */
export function RunDecision({
  trace,
  events,
  channelTokenEntered,
  busy,
  frames,
  cut,
  failure,
  onDecide,
  plugins,
}: RunDecisionProps) {
  const column = columnOf(trace, { channelTokenEntered });
  const notice = noticeOf(failure, { channelTokenEntered });

  return (
    <>
      {notice === null ? null : <FailureAlert {...notice} />}
      {cut ? (
        <Alert tone="info" title="재개 스트림이 끊겼다. 실행은 서버에서 계속된다">
          창을 닫거나 떠나도 실행은 끝까지 간다. 돌아오면 트레이스로 이어 본다.
        </Alert>
      ) : null}
      <RunColumns
        events={events}
        panel={
          column === null ? null : (
            <ColumnContent
              column={column}
              busy={busy}
              invalid={failure?.status === 422 ? failure : null}
              onDecide={onDecide}
              plugins={plugins}
            />
          )
        }
        stream={
          column?.kind === "place" || frames.length > 0 ? <ResumeStream frames={frames} /> : null
        }
      />
    </>
  );
}

interface ColumnContentProps {
  readonly column: Column;
  readonly busy: boolean;
  readonly invalid: RequestFailure | null;
  readonly onDecide: (decision: Decision) => void;
  readonly plugins: PluginsRead;
}

/** 결정 칸의 내용. 갈래마다 하나다. */
function ColumnContent({ column, busy, invalid, onDecide, plugins }: ColumnContentProps) {
  switch (column.kind) {
    case "place":
      return (
        <DecisionPlace
          pause={column.pause}
          busy={busy}
          invalid={invalid}
          onDecide={onDecide}
          plugins={plugins}
        />
      );
    case "endUser":
      return (
        <div className="rounded-l border border-border bg-bg-raised px-4 py-3">
          <GuideLine icon="info">최종 사용자의 실행이라 결정은 그 사람만 낸다</GuideLine>
        </div>
      );
    case "noChannelToken":
      return (
        <div className="flex flex-col gap-3 rounded-l border border-border bg-bg-raised px-4 py-3">
          <GuideLine icon="shield-check">결정을 내리려면 설정에서 채널 토큰을 넣는다</GuideLine>
          <span className="self-start">
            <TextLink href="/settings">설정 열기</TextLink>
          </span>
        </div>
      );
  }
}

/** 결정 칸의 안내 한 줄. 아이콘은 꾸밈이라 화면 읽기 프로그램에서 숨는다(이름을 주지 않은 `Icon`). */
function GuideLine({
  icon,
  children,
}: {
  readonly icon: "info" | "shield-check";
  readonly children: string;
}) {
  return (
    <p className="flex items-start gap-2 text-body text-text">
      <Icon name={icon} size="16" />
      <span>{children}</span>
    </p>
  );
}

/**
 * 재개 스트림. 받은 이벤트는 이벤트 칸과 같은 카드이고, 읽지 못한 조각은 "읽지 못한 프레임"과 원문 카드다. 조각이
 * 없으면 빈 줄이다. 스트림이 끝나면 트레이스를 다시 읽고 이 절은 걷힌다. 기록의 원천은 다시 읽은 트레이스다.
 */
function ResumeStream({ frames }: { readonly frames: readonly StreamFrame[] }) {
  const streamId = useId();
  return (
    <section aria-labelledby={streamId} className="flex flex-col gap-3">
      <h2 id={streamId} className="text-body font-semibold">
        재개 스트림
      </h2>
      {frames.length === 0 ? (
        <EmptyLine icon="circle-minus" iconSize="16">
          결정을 내면 재개한 이벤트가 여기에 차례로 붙는다.
        </EmptyLine>
      ) : (
        <ol className="flex flex-col gap-3">
          {frames.map((frame, index) =>
            // 프레임은 받은 차례로만 갈린다. 한 번의 결정 안에서 그 차례는 바뀌지 않는다.
            frame.kind === "event" ? (
              <EventItem key={index} event={frame.event} />
            ) : (
              <li key={index}>
                <Card padding="3">
                  <h3 className="font-mono text-mono font-medium">읽지 못한 프레임</h3>
                  <p className="font-mono text-mono whitespace-pre-wrap wrap-anywhere">
                    {frame.raw}
                  </p>
                </Card>
              </li>
            ),
          )}
        </ol>
      )}
    </section>
  );
}

/** 결정 자리 밖, 화면 머리 아래에 보일 실패 알림. */
interface Notice {
  readonly title: string;
  readonly message: string;
  readonly requestId: string | null;
}

/**
 * 결정 자리 밖에 보일 실패(admin-style 명세 "화면 머리와 공통 상태"의 실패 알림 표). 형식 오류(422)는 사유 칸 아래에
 * 서므로 여기 없다. 401 은 채널 토큰이 거부됐다는 것이고, 그 토큰은 이미 내려놓았다. 결정 칸이 채널 토큰 안내 줄로
 * 바뀌어 설정으로 가는 링크는 그 줄의 하나라, 알림에는 링크를 두지 않는다(사용자가 2026-10-27에 골랐다). 새 채널
 * 토큰을 넣으면 걷힌다. 그 밖(409 의 뜻 넷, 없는 실행, 서버 오류)은 "결정을 보내지 못했다"와 봉투의 메시지와 추적
 * 식별자이고, 봉투가 없으면(닿지 못함) "서버에 닿지 못했다"다.
 */
function noticeOf(
  failure: RequestFailure | null,
  { channelTokenEntered }: { readonly channelTokenEntered: boolean },
): Notice | null {
  if (failure === null || failure.status === 422) {
    return null;
  }
  if (isRejection(failure)) {
    return channelTokenEntered
      ? null
      : { title: "채널 토큰이 거부됐다", message: "설정에서 다시 넣는다.", requestId: null };
  }
  return { title: "결정을 보내지 못했다", ...describeFailure(failure) };
}

/**
 * 거부 사유 칸에 걸린 위반의 필드. 서버의 결정 본문에서 거부 사유의 자리이고, 서버 시험
 * `tests/channel/http/test_router.py` 가 이 이름을 고정한다.
 */
const REASON_FIELD = "body.deny.reason";

interface DecisionPlaceProps {
  readonly pause: Pause;
  /** 결정 하나가 끝날 때까지 참이다(`useDecision` 의 `busy`). 결정 버튼을 막는다. */
  readonly busy: boolean;
  /** 결정 본문의 형식 오류(422). 사유 칸 아래에 보인다. */
  readonly invalid: RequestFailure | null;
  readonly onDecide: (decision: Decision) => void;
  readonly plugins: PluginsRead;
}

/**
 * 결정 자리(스토리 38~41, admin-style 명세 "결정 자리"). 카드에 무엇을 승인하는지(도구와 인자)를 보이고 거부와 승인을
 * 받는다. 결정은 이 일시정지의 자리를 든다. 다시 읽은 트레이스가 새 일시정지에서 멈추면 자리는 그대로 서고 내용만 새
 * 일시정지다.
 */
function DecisionPlace({ pause, busy, invalid, onDecide, plugins }: DecisionPlaceProps) {
  const headingId = useId();
  // 목록을 다시 읽다 실패하면 SWR 은 옛 목록을 들고 있다. 옛 켜짐을 믿지 않는다(.claude/rules/web-admin.md). 그때는
  // 미리 알 수 없다고 말하고 버튼을 막지 않는다. 누르면 서버의 봉투가 말한다.
  const unknown = plugins.error !== undefined;
  const disabled = disabledFor(pause.agent, unknown ? undefined : plugins.data);

  return (
    <Card as="section" padding="4" aria-labelledby={headingId}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 id={headingId} className="text-body font-semibold">
            결정
          </h2>
          <p className="text-body text-text-muted">
            이 실행은 도구 호출 하나의 승인을 기다리며 일시정지했다. 결정은 이 호출 하나에 대한
            답이다.
          </p>
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
            <dd className="font-mono text-mono font-medium wrap-anywhere">{pause.tool}</dd>
          </div>
          <div className="flex flex-col gap-2">
            <dt className="text-small text-text-muted">
              인자 <code className="font-mono">args</code>
            </dt>
            <dd>
              <CodeBlock surface="card">{asText(pause.args)}</CodeBlock>
            </dd>
          </div>
        </dl>
        <p className="text-small text-text-muted">
          결정의 승인자는 이 화면이 고르지 않는다. <code className="font-mono">agent-os serve</code>{" "}
          를 띄운 OS 사용자로 기록된다.
        </p>
        {/* 새 일시정지면 새 폼이다. 앞의 일시정지에 적던 거부 사유는 남기지 않는다. */}
        <DecisionForm
          key={pause.index}
          pauseIndex={pause.index}
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
 * 승인 묻기). 결정 칸의 폭이 `wide`(360px) 이상이면 버튼이 오른쪽에 나란히, 미만이면 둘이 위아래로 꽉 찬다. 거부는
 * 사유를 적어야 보낼 수 있고, 다듬어 비면 보내지 않는다(스토리 40, 41). 서버의 422 는 사유 칸 바로 아래의 알림이
 * 메시지와 추적 식별자와 위반을 모두 보이고, 사유에 걸린 위반은 사유 칸이 오류로 받는다.
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
