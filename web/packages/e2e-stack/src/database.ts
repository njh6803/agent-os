// e2e 의 준비가 `serve` 에 줄 데이터베이스를 만드는 길. `serve` 는 표의 판이 맞는 데이터베이스에 닿아야 뜬다(ADR 0066).
// 테스트 컨테이너(`compose.test.yaml`)에 이 준비만의 빈 데이터베이스를 만들고, 같은 주소로 `agent-os migrate` 를 돌려 표를
// 올린 뒤 그 주소를 준다. 부모의 환경에 같은 변수(`AGENT_OS_DATABASE_URL`)가 있어도 이 값으로 덮는다. 거둘 때 지운다.
//
// 만들고 지우는 일은 `tools/database_for_tests.py` 의 명령줄이 한다(pytest 픽스처와 같은 일, 같은 컨테이너, 같은 이름의
// 꼴). 테스트 컨테이너가 떠 있지 않으면 그 도구가 시험 쪽 글(띄우는 명령)을 표준 오류에 찍고 1 로 끝나, 그 글이 이 준비의
// 오류에 그대로 실린다. 주소에는 비밀번호가 들어 있어 오류에 싣지 않는다.

import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { REPO } from "./serve.ts";
import type { Stack } from "./stack.ts";

/** 데이터베이스 이름의 접두. 도구가 `<접두>_e2e_<32자>` 로 짓는다. */
export const DATABASE_PREFIX = "agent_os";
/** `serve` 가 주소를 읽는 환경 변수. */
export const DATABASE_URL_ENV = "AGENT_OS_DATABASE_URL";

const TOOL = join(REPO, "tools", "database_for_tests.py");
const CALL_MS = 120_000;

/** 주소(`postgresql://계정:비밀번호@호스트:포트/이름`)의 데이터베이스 이름. */
export function databaseName(address: string): string {
  const name = new URL(address).pathname.replace(/^\//, "");
  if (name === "") {
    throw new Error("데이터베이스 주소에 이름이 없다");
  }
  return name;
}

/**
 * 이 준비만의 빈 데이터베이스를 만들어 표를 올리고 그 주소를 준다. 거둘 때 지우도록 묶음에 맡긴다. 지우기는 만든 직후에
 * 맡겨 두므로 표를 올리다 실패해도 지워진다.
 */
export function prepareDatabase(stack: Stack, python: string): string {
  const address = succeed(python, [TOOL, "create", DATABASE_PREFIX], REPO, {}, "만들지 못했다");
  const name = databaseName(address);
  stack.cleanup(() => {
    succeed(python, [TOOL, "drop", name], REPO, {}, "지우지 못했다");
  });
  // `serve` 와 같은 길로 표를 올린다. 작업 폴더는 `serve` 와 같이 임시 폴더의 루트다.
  succeed(
    python,
    ["-m", "agent_os.main", "migrate"],
    tmpdir(),
    { [DATABASE_URL_ENV]: address },
    "표를 올리지 못했다",
  );
  return address;
}

/** 명령을 돌려 표준 출력(앞뒤 공백을 걷은 것)을 준다. 실패하면 이유와 표준 오류를 싣고 던진다. */
function succeed(
  command: string,
  args: readonly string[],
  cwd: string,
  extra: Readonly<Record<string, string>>,
  failure: string,
): string {
  const found = spawnSync(command, args, {
    cwd,
    encoding: "utf-8",
    timeout: CALL_MS,
    env: { ...process.env, PYTHONUTF8: "1", ...extra },
  });
  // 명령을 실행하지 못하면 선언과 달리 stdout·stderr 가 null 이고 이유는 `error` 에만 있다.
  const stdout: unknown = found.stdout;
  const stderr: unknown = found.stderr;
  if (found.status !== 0) {
    const reason = found.error?.message ?? (typeof stderr === "string" ? stderr.trim() : "");
    throw new Error(`테스트 데이터베이스를 ${failure}:\n${reason}`);
  }
  return typeof stdout === "string" ? stdout.trim() : "";
}
