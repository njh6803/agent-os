// 트레이스의 이벤트와 트레이스를 짓는 도우미. 대화 화면의 규칙 시험(`api/conversation/turns.test.ts`)과 페이지 시험이 함께
// 쓴다. 이벤트는 계약의 생성 타입 그대로라 계약이 바뀌면 여기가 컴파일에서 깨진다.

import type { Trace, TraceEvent } from "../api/traces";

export type RunStarted = Extract<TraceEvent, { type: "run_started" }>;

/** 기본 시각. 대화 화면 시험의 시간대(America/New_York)에서 전날 저녁으로 보인다. */
export const T0 = "2026-11-27T01:00:00+00:00";

export function started(
  runId: string,
  previous: string | null = null,
  ts = T0,
  extra: Partial<RunStarted> = {},
): RunStarted {
  return {
    type: "run_started",
    run_id: runId,
    ts,
    agent: "support-bot",
    principal: "operator",
    request: `${runId}의 요청`,
    previous_run: previous,
    requesting_account: "kim.dev",
    shortcuts: null,
    ...extra,
  };
}

export function toolCalled(
  runId: string,
  tool: string,
  result: "ok" | "error",
  ts = T0,
  extra: Partial<Pick<Extract<TraceEvent, { type: "tool_called" }>, "args" | "content">> = {},
): TraceEvent {
  return {
    type: "tool_called",
    run_id: runId,
    ts,
    tool,
    ok: result === "ok",
    args: {},
    content: "",
    rule: null,
    ...extra,
  };
}

export function paused(runId: string, tool: string, ts = T0): TraceEvent {
  return { type: "run_paused", run_id: runId, ts, tool, args: {}, rule: null, server: null };
}

export function granted(
  runId: string,
  account: string | null,
  ts = T0,
  approver = "operator",
): TraceEvent {
  return {
    type: "approval_granted",
    run_id: runId,
    ts,
    approver,
    deciding_account: account,
  };
}

export function denied(
  runId: string,
  account: string | null,
  reason: string,
  ts = T0,
  approver = "operator",
): TraceEvent {
  return {
    type: "approval_denied",
    run_id: runId,
    ts,
    approver,
    deciding_account: account,
    reason,
  };
}

export function finished(runId: string, output: string, ts = T0): TraceEvent {
  return { type: "run_finished", run_id: runId, ts, output };
}

export function failed(runId: string, error: string, ts = T0): TraceEvent {
  return { type: "run_failed", run_id: runId, ts, error, cause: null };
}

export function resumed(runId: string, ts = T0): TraceEvent {
  return { type: "run_resumed", run_id: runId, ts };
}

export function llm(runId: string, ts = T0): TraceEvent {
  return {
    type: "llm_called",
    run_id: runId,
    ts,
    model: "m",
    input_tokens: 1,
    output_tokens: 1,
    prompt: "",
    text: "",
    tool_calls: [],
  };
}

export function summarized(runId: string, ts = T0): TraceEvent {
  return {
    type: "conversation_summarized",
    run_id: runId,
    ts,
    input_tokens: 1,
    output_tokens: 1,
    model: "m",
    last_covered_run: "r0",
    summary: "요약",
  };
}

export function trace(runId: string, events: TraceEvent[]): Trace {
  return { run_id: runId, schema_version: "3", events };
}
