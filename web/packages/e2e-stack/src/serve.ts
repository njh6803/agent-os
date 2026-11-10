// e2e 의 준비가 실제 `serve` 를 띄우는 길. 위젯 e2e 의 준비(`apps/widget/e2e/stack.ts`)에서 옮겼다. `serve` 는 `uv run` 이
// 쓰는 가상 환경의 파이썬으로 띄운다. 플러그인 루트(`plugins.ts`), 트레이스 폴더, 사이트 파일(`siteFileToml`)은 준비가 만들어
// 준다. 환경에는 부모의 환경을 펼친다(키는 그렇게 물려 간다).
//
// - `serve` 의 구성 검사는 운영자 토큰과 채널 토큰을 요구한다. e2e 가 쓰지 않아 이 프로세스가 무작위로 짓고 시험에는 넘기지
//   않는다.
// - `serve` 가 띄운 MCP 서버는 작업 폴더를 물려받고 `serve` 를 끈 뒤에도 잠시 남는다. 그래서 작업 폴더를 임시 폴더의 루트로
//   두어, 준비의 작업 폴더(`Stack.work`)를 지우는 정리가 막히지 않게 한다.

import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DEFAULT_MODEL } from "./plugins.ts";
import { until } from "./process.ts";
import type { Stack } from "./stack.ts";
import { AUDIENCE, ISSUER, KEY_ID } from "./token.ts";

/** 저장소 루트. 이 파일은 `web/packages/e2e-stack/src/` 에 있다. */
export const REPO = join(import.meta.dirname, "..", "..", "..", "..");
/** 플러그인 `mcp/fixture` 가 띄우는 MCP 서버. */
export const MCP_FIXTURE_SERVER = join(REPO, "tests", "adapters", "mcp_fixture_server.py");

const LISTENING = /Uvicorn running on (http:\/\/127\.0\.0\.1:\d+)/;
const UNUSED_TOKEN_BYTES = 24;

export interface ServeOptions {
  /** `serve --plugins-root`. */
  readonly plugins: string;
  /** `serve --traces`. 시험이 이 폴더를 읽으려면 준비가 `publish` 로 넘긴다. */
  readonly traces: string;
  /** `serve --site-file`. */
  readonly siteFile: string;
  /** `interpreter()` 가 준 파이썬. */
  readonly python: string;
}

/** `uv run` 이 쓰는 가상 환경의 파이썬 인터프리터. */
export function interpreter(): string {
  const found = spawnSync("uv", ["run", "python", "-c", "import sys; print(sys.executable)"], {
    cwd: REPO,
    encoding: "utf-8",
  });
  // `uv` 를 실행하지 못하면 선언과 달리 stdout·stderr 가 null 이고 이유는 `error` 에만 있다.
  const stdout: unknown = found.stdout;
  const stderr: unknown = found.stderr;
  const path = typeof stdout === "string" ? stdout.trim() : "";
  if (found.status !== 0 || path === "") {
    const reason = found.error?.message ?? (typeof stderr === "string" ? stderr : "");
    throw new Error(`파이썬 인터프리터를 찾지 못했다(uv run python):\n${reason}`);
  }
  return path;
}

/** `serve` 를 띄우고 서는 것을 기다려 그 주소(`http://127.0.0.1:<포트>`)를 준다. */
export async function startServe(stack: Stack, options: ServeOptions): Promise<string> {
  const serve = stack.launch(
    "serve",
    options.python,
    [
      "-m",
      "agent_os.main",
      "serve",
      "--port",
      "0",
      "--plugins-root",
      options.plugins,
      "--traces",
      options.traces,
      "--site-file",
      options.siteFile,
      "--model",
      DEFAULT_MODEL,
    ],
    tmpdir(),
    {
      ...process.env,
      PYTHONUTF8: "1",
      AGENT_OS_ADMIN_TOKEN: unusedToken(),
      AGENT_OS_CHANNEL_TOKEN: unusedToken(),
    },
  );
  return until(serve, "serve 가 서지 않았다", () => LISTENING.exec(serve.output())?.[1] ?? null);
}

function unusedToken(): string {
  return `e2e-unused-${randomBytes(UNUSED_TOKEN_BYTES).toString("hex")}`;
}

/** 사이트 하나의 사이트 파일. 허용 출처는 `origin` 하나이고 글자 수 상한은 적지 않아 기본값이다. */
export function siteFileToml(origin: string, publicPem: string, agents: readonly string[]): string {
  return [
    'schema_version = "1"',
    "",
    "[[sites]]",
    `issuer = ${JSON.stringify(ISSUER)}`,
    `audience = ${JSON.stringify(AUDIENCE)}`,
    `allowed_origins = [${JSON.stringify(origin)}]`,
    `agents = [${agents.map((name) => JSON.stringify(name)).join(", ")}]`,
    "",
    "[[sites.public_keys]]",
    `kid = ${JSON.stringify(KEY_ID)}`,
    `pem = ${JSON.stringify(publicPem)}`,
    "",
  ].join("\n");
}
