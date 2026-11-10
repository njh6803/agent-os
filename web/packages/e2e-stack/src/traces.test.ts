import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, expect, test } from "vitest";
import { startedRuns } from "./traces.ts";

let folder = "";

beforeEach(() => {
  folder = mkdtempSync(join(tmpdir(), "e2e-stack-traces-"));
});

afterEach(() => {
  rmSync(folder, { recursive: true, force: true, maxRetries: 5 });
});

const HEADER = JSON.stringify({ schema_version: "3", run_id: "run" });

function started(agent: string, request: string, principal: string): string {
  return JSON.stringify({
    type: "run_started",
    run_id: "run",
    agent,
    request,
    principal,
    previous_run: null,
    shortcuts: null,
  });
}

function trace(name: string, ...lines: string[]): void {
  writeFileSync(join(folder, `${name}.jsonl`), `${lines.join("\n")}\n`);
}

test("헤더 다음 줄의 시작 이벤트에서 에이전트와 요청과 주체를 읽는다", () => {
  trace("a1", HEADER, started("echo", "안녕", "https://site.e2e.example|alice"));

  expect(startedRuns(folder)).toEqual([
    {
      runId: "a1",
      agent: "echo",
      request: "안녕",
      principal: "https://site.e2e.example|alice",
    },
  ]);
});

test("트레이스마다 한 실행씩 이름 순으로 낸다", () => {
  trace("b2", HEADER, started("echo", "둘째", "p|2"));
  trace("a1", HEADER, started("tools", "첫째", "p|1"));

  expect(startedRuns(folder).map((run) => [run.runId, run.agent])).toEqual([
    ["a1", "tools"],
    ["b2", "echo"],
  ]);
});

test("시작 이벤트가 쓰는 도중이라 잘렸으면 아직 실행으로 세지 않고 던지지도 않는다", () => {
  trace("a1", HEADER, '{"type":"run_started","agent":"ec');

  expect(startedRuns(folder)).toEqual([]);
});

test("시작 이벤트가 아직 없는 트레이스는 실행으로 세지 않는다", () => {
  trace("a1", HEADER);

  expect(startedRuns(folder)).toEqual([]);
});

test("칸의 종류가 틀린 시작 이벤트는 실행으로 세지 않는다", () => {
  trace("a1", HEADER, JSON.stringify({ type: "run_started", agent: "echo", request: "x" }));

  expect(startedRuns(folder)).toEqual([]);
});

test("jsonl 이 아닌 파일은 읽지 않는다", () => {
  writeFileSync(join(folder, "note.txt"), `${HEADER}\n${started("echo", "x", "p|1")}\n`);

  expect(startedRuns(folder)).toEqual([]);
});

test("폴더 대신 파일을 주면 폴더가 없다는 오류가 아니므로 그대로 던진다", () => {
  const file = join(folder, "file");
  writeFileSync(file, "");

  expect(() => startedRuns(file)).toThrow(/ENOTDIR/);
});

test("폴더가 없으면 빈 목록이다", () => {
  expect(startedRuns(join(folder, "없는 폴더"))).toEqual([]);
});
