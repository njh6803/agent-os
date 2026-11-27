// 대화 화면이 트레이스를 읽어 그리는 데 쓰는 순수한 규칙(admin-login 명세 "대화 화면", "대화를 다시 그리는 읽기", "도는
// 실행을 이어 보기"). 요청은 부르는 쪽이 준 읽기 함수로만 보내고, 이 파일은 네트워크도 SWR도 모른다.
// 트레이스의 이벤트 열을 화면이 그리는 차례(`Turn`)로 바꾸는 일, 다시 읽을 간격을 정하는 일, 앞 실행을 거슬러 읽는 일이
// 여기 있다.

import { RequestFailure } from "../failure";
import type { Trace, TraceEvent } from "../traces";

/** 거슬러 읽는 실행의 상한. 끝 실행은 세지 않는다. core 가 이어 가기에서 거슬러 읽는 상한(`READ_CAP`)과 같은 수다. */
export const EARLIER_CAP = 100;

/** 도는 실행을 다시 읽는 간격(밀리초). */
export const POLL_MS = 3000;

/** 승인 묻기 하나. 일시정지 이벤트에서 서고 뒤따르는 결정 이벤트가 상태를 바꾼다. */
export type Approval =
  | {
      readonly state: "waiting";
      readonly tool: string;
      readonly at: string;
      /** 그 일시정지 이벤트가 트레이스의 `events` 에서 서는 0부터 센 자리. 결정 경로가 이 자리를 받는다. */
      readonly pauseIndex: number;
    }
  | {
      readonly state: "granted";
      readonly tool: string;
      /** 결정한 시각. */
      readonly at: string;
      /** 결정한 계정. 비어 있으면(명령줄에서 내린 결정) 주체 이름이다. */
      readonly by: string;
      readonly pauseIndex: number;
    }
  | {
      readonly state: "denied";
      readonly tool: string;
      readonly at: string;
      readonly by: string;
      readonly reason: string;
      readonly pauseIndex: number;
    };

/** 실행의 결말. 도는 중이면 `step` 이 마지막 이벤트의 다음 일이다(모델을 부르는 중인지 도구를 부르는 중인지). */
export type Outcome =
  | { readonly kind: "finished"; readonly output: string; readonly at: string }
  | { readonly kind: "failed"; readonly error: string; readonly at: string }
  | { readonly kind: "paused" }
  | { readonly kind: "running"; readonly step: "model" | "tool" };

/** 대화 화면에 한 실행으로 그려지는 것. */
export interface Turn {
  readonly runId: string;
  readonly agent: string;
  readonly principal: string;
  readonly requestingAccount: string | null;
  readonly startedAt: string;
  readonly request: string;
  readonly tools: readonly { readonly tool: string; readonly ok: boolean }[];
  readonly approvals: readonly Approval[];
  readonly outcome: Outcome;
}

/** 트레이스를 대화의 한 차례로 바꾼다. 모델 호출과 대화 요약은 대화에 싣지 않는다(패널에서 본다). */
export function turnOf(trace: Trace): Turn {
  const tools: { tool: string; ok: boolean }[] = [];
  const approvals: Approval[] = [];
  let agent = "";
  let principal = "";
  let requestingAccount: string | null = null;
  let startedAt = "";
  let request = "";
  trace.events.forEach((event, index) => {
    switch (event.type) {
      case "run_started":
        agent = event.agent;
        principal = event.principal;
        requestingAccount = event.requesting_account;
        startedAt = event.ts;
        request = event.request;
        break;
      case "tool_called":
        tools.push({ tool: event.tool, ok: event.ok });
        break;
      case "run_paused":
        approvals.push({ state: "waiting", tool: event.tool, at: event.ts, pauseIndex: index });
        break;
      case "approval_granted":
      case "approval_denied":
        decide(approvals, event, principal);
        break;
      default:
        break;
    }
  });
  return {
    runId: trace.run_id,
    agent,
    principal,
    requestingAccount,
    startedAt,
    request,
    tools,
    approvals,
    outcome: outcomeOf(trace.events),
  };
}

type Decision = Extract<TraceEvent, { type: "approval_granted" | "approval_denied" }>;

/** 결정 이벤트는 가장 뒤의 기다리는 승인을 닫는다. 기다리는 승인이 없는 결정(깨진 기록)은 싣지 않는다. */
function decide(approvals: Approval[], event: Decision, principal: string): void {
  const index = approvals.findLastIndex((approval) => approval.state === "waiting");
  const waiting = approvals[index];
  if (waiting === undefined) {
    return;
  }
  const by = event.deciding_account ?? principal;
  approvals[index] =
    event.type === "approval_granted"
      ? { state: "granted", tool: waiting.tool, at: event.ts, by, pauseIndex: waiting.pauseIndex }
      : {
          state: "denied",
          tool: waiting.tool,
          at: event.ts,
          by,
          reason: event.reason,
          pauseIndex: waiting.pauseIndex,
        };
}

function outcomeOf(events: readonly TraceEvent[]): Outcome {
  const last = events.at(-1);
  if (last?.type === "run_finished") {
    return { kind: "finished", output: last.output, at: last.ts };
  }
  if (last?.type === "run_failed") {
    return { kind: "failed", error: last.error, at: last.ts };
  }
  if (last?.type === "run_paused") {
    return { kind: "paused" };
  }
  // 모델 호출과 도구 호출의 이벤트는 호출이 끝난 뒤에 온다. 그래서 단계는 마지막으로 받은 이벤트의 다음 일로 짐작한다.
  const shown = events.findLast(
    (event) => event.type !== "conversation_summarized" && event.type !== "unknown",
  );
  return { kind: "running", step: shown?.type === "llm_called" ? "tool" : "model" };
}

/**
 * 트레이스에 결말이 있는가. 실행 상태는 마지막 이벤트 하나로 파생하므로, 승인으로 다시 도는 실행은 앞의 일시정지
 * 이벤트가 남아 있어도 마지막 이벤트가 아니라 결말이 없다.
 */
export function hasOutcome(trace: Trace): boolean {
  const last = trace.events.at(-1);
  return (
    last?.type === "run_finished" || last?.type === "run_failed" || last?.type === "run_paused"
  );
}

/** 마지막 이벤트의 시각에 실행 제한 시간을 더한 때가 지났는가. 지난 실행은 서버가 더 쓰지 않는다. */
export function isPastTimeout(trace: Trace, timeoutSeconds: number, now: number): boolean {
  // 모르는 종류의 이벤트는 시각이 없어, 시각이 있는 가장 뒤의 이벤트로 잰다.
  const last = trace.events.findLast((event) => event.type !== "unknown");
  return last !== undefined && now >= Date.parse(last.ts) + timeoutSeconds * 1000;
}

/**
 * 끝 실행을 다시 읽을 간격(밀리초). 0 이면 멈춘다. 데이터가 아직 없으면 3000, 결말이 있거나 멈출 때가 지났으면 0, 그
 * 밖은 3000 이다. SWR 의 `refreshInterval` 에 그릴 때마다 새로 만든 함수로 넘긴다(인라인 꼴, 명세 "간격 함수").
 */
export function pollInterval(
  trace: Trace | undefined,
  timeoutSeconds: number,
  now: number,
): number {
  if (trace === undefined) {
    return POLL_MS;
  }
  return hasOutcome(trace) || isPastTimeout(trace, timeoutSeconds, now) ? 0 : POLL_MS;
}

/** 시작 이벤트의 앞 실행. 처음 실행이거나 시작 이벤트가 없으면 null 이다. */
export function previousRunOf(trace: Trace): string | null {
  const start = trace.events.find((event) => event.type === "run_started");
  return start === undefined ? null : start.previous_run;
}

/** 앞 실행을 거슬러 읽은 결과. `traces` 는 가장 오래된 실행부터다. */
export interface Earlier {
  readonly traces: readonly Trace[];
  /** `start` 는 첫 실행에 닿았다, `cap` 은 상한에 닿았고 더 앞이 남았다, `broken` 은 읽지 못한 고리에서 멈췄다. */
  readonly end: "start" | "cap" | "broken";
}

/**
 * 앞 실행을 하나씩 거슬러 읽는다. 앞 실행을 알려면 그 실행을 읽어야 하므로 차례로 돈다. 상한은 끝 실행을 뺀
 * `EARLIER_CAP` 개이고, 앞 실행이 404 나 500 이거나 이미 지난 실행(끝 실행 포함)으로 돌아오는 순환이면 읽은 데까지
 * 돌려주고 끊겼다고 알린다. 서버에 닿지 못한 것과 그 밖의 실패는 던져 읽기의 실패가 되게 한다.
 */
export async function readEarlier(
  previousRun: string | null,
  endRunId: string,
  read: (runId: string) => Promise<Trace>,
): Promise<Earlier> {
  const seen = new Set<string>([endRunId]);
  const newestFirst: Trace[] = [];
  let cursor = previousRun;
  let end: Earlier["end"] = "start";
  while (cursor !== null) {
    if (newestFirst.length >= EARLIER_CAP) {
      end = "cap";
      break;
    }
    if (seen.has(cursor)) {
      end = "broken";
      break;
    }
    seen.add(cursor);
    const found = await readOrNull(read, cursor);
    if (found === null) {
      end = "broken";
      break;
    }
    newestFirst.push(found);
    cursor = previousRunOf(found);
  }
  return { traces: newestFirst.toReversed(), end };
}

/** 없는 트레이스(404)와 읽히지 않는 트레이스(500)는 null 이고, 그 밖의 실패는 던진다. */
async function readOrNull(
  read: (runId: string) => Promise<Trace>,
  runId: string,
): Promise<Trace | null> {
  try {
    return await read(runId);
  } catch (failure) {
    if (failure instanceof RequestFailure && (failure.status === 404 || failure.status === 500)) {
      return null;
    }
    throw failure;
  }
}
