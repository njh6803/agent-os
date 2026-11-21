import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, expect, test } from "vitest";
import {
  saveLogsAtFailure,
  type FinishedTest,
  type LogOutcome,
  type LogSource,
} from "./failure-logs.ts";

let dir = "";

beforeEach(() => {
  dir = mkdtempSync(join(tmpdir(), "failure-logs-"));
});

afterEach(() => {
  rmSync(dir, { recursive: true, force: true, maxRetries: 5 });
});

function finishedAs(
  status: FinishedTest["status"],
  expectedStatus: FinishedTest["expectedStatus"],
): FinishedTest {
  return { status, expectedStatus, outputPath: (name: string) => join(dir, name) };
}

function logsSaying(outcome: Partial<LogOutcome>): LogSource & { readonly calls: string[][] } {
  const calls: string[][] = [];
  return {
    calls,
    call: (rest) => {
      calls.push([...rest]);
      return Promise.resolve({ code: 0, stdout: "", stderr: "", timedOut: false, ...outcome });
    },
  };
}

function savedLog(): string {
  return readFileSync(join(dir, "compose-at-failure.log"), "utf-8");
}

test("시험이 실패하면 그 순간의 배치 로그를 그 시험의 결과 폴더에 쓴다", async () => {
  const logs = logsSaying({ stdout: "proxy-1  | 502\n", stderr: "경고\n" });

  await saveLogsAtFailure(finishedAs("failed", "passed"), logs);

  expect(savedLog()).toBe("proxy-1  | 502\n\n경고\n");
  expect(logs.calls).toEqual([["logs", "--no-color", "--timestamps"]]);
});

test("시간 초과로 끝난 시험도 실패로 보고 로그를 쓴다", async () => {
  await saveLogsAtFailure(finishedAs("timedOut", "passed"), logsSaying({ stdout: "로그" }));

  expect(savedLog()).toBe("로그\n");
});

test("기대한 대로 끝난 시험은 로그를 부르지도 쓰지도 않는다", async () => {
  const logs = logsSaying({ stdout: "로그" });

  await saveLogsAtFailure(finishedAs("passed", "passed"), logs);
  await saveLogsAtFailure(finishedAs("failed", "failed"), logs);

  expect(logs.calls).toEqual([]);
  expect(existsSync(join(dir, "compose-at-failure.log"))).toBe(false);
});

test("로그 명령이 0 이 아닌 코드로 끝나면 첫 줄에 그 사실을 적고 받은 것을 남긴다", async () => {
  const logs = logsSaying({ code: 1, stdout: "", stderr: "daemon 이 답하지 않는다\n" });

  await saveLogsAtFailure(finishedAs("failed", "passed"), logs);

  expect(savedLog()).toBe(
    "[docker compose logs 가 1 로 끝났다. 아래는 받은 것이다]\n\ndaemon 이 답하지 않는다\n",
  );
});

test("로그 명령이 제한 시간을 넘겨 죽으면 첫 줄에 그 사실을 적고 그때까지 받은 것을 남긴다", async () => {
  const logs = logsSaying({ code: null, stdout: "proxy-1  | 일부\n", timedOut: true });

  await saveLogsAtFailure(finishedAs("failed", "passed"), logs);

  expect(savedLog()).toBe(
    "[docker compose logs 가 제한 시간을 넘겨 죽었다. 아래는 그때까지 받은 것이다]\nproxy-1  | 일부\n\n",
  );
});

test("로그를 부르는 일이 던져도 시험의 실패가 가려지지 않는다", async () => {
  const broken: LogSource = {
    call: () => Promise.reject(new Error("docker 를 찾지 못했다")),
  };

  await expect(saveLogsAtFailure(finishedAs("failed", "passed"), broken)).resolves.toBeUndefined();
});

test("결과 폴더에 쓰지 못해도 던지지 않는다", async () => {
  const unwritable: FinishedTest = {
    status: "failed",
    expectedStatus: "passed",
    outputPath: (name: string) => join(dir, "없는 폴더", name),
  };

  await expect(
    saveLogsAtFailure(unwritable, logsSaying({ stdout: "로그" })),
  ).resolves.toBeUndefined();
});
