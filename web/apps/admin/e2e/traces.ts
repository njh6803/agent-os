// 읽기 흐름이 볼 트레이스(web-admin 명세 "e2e"). 준비(stack.ts)가 serve 를 띄우기 전에 트레이스 디렉터리에 쓰고, 흐름은
// 여기 적은 식별자와 글자로 화면을 본다. 끝남, 실패, 형식 1, 모르는 종류의 줄, 읽을 수 없는 파일이다. 끝난 실행의 도구
// 결과에는 HTML 을 넣어 실제 브라우저에서 요소로 그려지지 않는지 본다(ADR 0019).
//
// 줄의 모양은 JSONL 트레이스 저장소의 것이다(`src/agent_os/adapters/jsonl.py`). 첫 줄이 형식 버전과 실행 식별자의
// 헤더이고 이어서 이벤트가 한 줄에 하나다. 이벤트는 모르는 필드를 받지 않으므로 계약의 필드만 적는다.

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export const READ_RUNS = {
  finished: "e2e-finished",
  failed: "e2e-failed",
  formatOne: "e2e-format-one",
  unknown: "e2e-unknown",
  unreadable: "e2e-unreadable",
} as const;

/** 끝난 실행의 도구 결과. 요소로 그려지면 이미지를 불러오지 못해 전역에 표시를 남긴다. */
export const HOSTILE_CONTENT = '<img src=x onerror="window.__agentOsXss = true">';

/** 이 런타임이 모르는 종류의 줄. 목록에서 마지막 줄이라 실행은 결말 없음이다. */
export const UNKNOWN_LINE = `{"type":"future_kind","run_id":"${READ_RUNS.unknown}","ts":"2026-09-30T09:03:01+00:00","note":"다음 판의 이벤트"}`;

export function writeReadTraces(directory: string): void {
  mkdirSync(directory, { recursive: true });
  const write = (runId: string, lines: readonly string[]): void => {
    writeFileSync(join(directory, `${runId}.jsonl`), lines.map((line) => `${line}\n`).join(""));
  };
  const header = (runId: string, version: "1" | "2"): string =>
    JSON.stringify({ schema_version: version, run_id: runId });
  const started = (runId: string, ts: string): string =>
    JSON.stringify({
      type: "run_started",
      run_id: runId,
      ts,
      agent: "echo",
      request: `${runId} 의 요청`,
      principal: "e2e",
    });

  write(READ_RUNS.finished, [
    header(READ_RUNS.finished, "2"),
    started(READ_RUNS.finished, "2026-09-30T09:00:00+00:00"),
    JSON.stringify({
      type: "tool_called",
      run_id: READ_RUNS.finished,
      ts: "2026-09-30T09:00:01+00:00",
      tool: "fetch",
      ok: true,
      args: { url: "https://example.test" },
      content: HOSTILE_CONTENT,
    }),
    JSON.stringify({
      type: "run_finished",
      run_id: READ_RUNS.finished,
      ts: "2026-09-30T09:00:02+00:00",
      output: "끝났다",
    }),
  ]);
  write(READ_RUNS.failed, [
    header(READ_RUNS.failed, "2"),
    started(READ_RUNS.failed, "2026-09-30T09:01:00+00:00"),
    JSON.stringify({
      type: "run_failed",
      run_id: READ_RUNS.failed,
      ts: "2026-09-30T09:01:01+00:00",
      error: "도구 연결이 끊겼다",
    }),
  ]);
  write(READ_RUNS.formatOne, [
    header(READ_RUNS.formatOne, "1"),
    started(READ_RUNS.formatOne, "2026-09-30T09:02:00+00:00"),
    JSON.stringify({
      type: "run_finished",
      run_id: READ_RUNS.formatOne,
      ts: "2026-09-30T09:02:01+00:00",
      output: "형식 1 의 출력",
    }),
  ]);
  write(READ_RUNS.unknown, [
    header(READ_RUNS.unknown, "2"),
    started(READ_RUNS.unknown, "2026-09-30T09:03:00+00:00"),
    UNKNOWN_LINE,
  ]);
  write(READ_RUNS.unreadable, ["이것은 JSON 이 아니다"]);
}
