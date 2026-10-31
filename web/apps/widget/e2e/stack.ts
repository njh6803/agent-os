/**
 * 위젯 e2e 의 준비(globalSetup, web-widget 티켓 06). 실제 `serve`, 같은 사이트 파일로 빌드한 실제 위젯 Next, 둘을 한
 * 출처 아래에 모으는 같은 출처의 중계(`relay.ts`), 두 방식으로 위젯을 품는 다른 출처의 사이트(`site.ts`)를 띄운다.
 * 기본은 모델을 부르지 않는다. 선례는 관리 화면 e2e 의 준비(`apps/admin/e2e/stack.ts`)다.
 *
 * 실제 모델 e2e(티켓 11)를 감싸는 파이썬 시험이 `LLM_ENV` 를 `1` 로 주면 둘이 더해진다. 임시 플러그인 루트에 저장소의
 * 플러그인 루트를 먼저 옮기고(`plugins.ts`), 사이트 파일의 에이전트에 계산 에이전트를 넣는다. 그 에이전트만 모델을 부르고,
 * 키는 아래의 serve 환경이 물려준다. 그 시험이 `TRACES_ENV` 로 준 자리에 serve 가 트레이스를 남기고, 주지 않으면 작업
 * 폴더에 남겨 끝에 지운다.
 *
 * - 출처는 모두 `*.localhost` 호스트 이름이다. 위젯은 `widget.localhost`, 허용 출처의 사이트는 `site.localhost`, 허용 밖
 *   출처의 사이트는 `other.localhost` 이고 포트로 가른다. 표기 규칙은 IP 호스트의 출처도 지나보내지만 CSP3 의 문법은
 *   host-part 대조를 domain 에만 맞춘다(`tests/fixtures/site_file/README.md`). 브라우저는 `*.localhost` 를 보안 맥락으로
 *   보아 TLS 없이도 위젯의 `crypto.randomUUID` 가 선다. 이름 풀기는 Playwright 설정이 맡는다.
 * - 포트를 먼저 고른다. 허용 출처가 사이트 파일에 실리고 그것이 위젯 빌드의 `frame-ancestors` 와 번들에 박히기 때문이다.
 * - 사이트 파일은 사이트 하나이고 `request_chars` 를 적지 않는다. 그래서 입력창과 서버의 글자 수 상한이 둘 다 기본값이다.
 * - 사이트의 키 쌍은 `node:crypto` 가 짓고(`token.ts`) 개인 키는 이 프로세스의 사이트 서버만 든다.
 * - serve 의 환경에는 부모의 환경을 펼친다(관리 화면 e2e 와 같다). 위젯 Next 에는 serve 의 토큰 변수를 벗겨서 준다.
 *   위젯 Next 는 API 를 모르고(ADR 0024) 사이트 파일만 읽는다.
 * - 거두는 것은 관리 화면 e2e 와 같이 `kill()` 이다(제때 끝나지 않을 때만 SIGKILL). 그 준비가 잰 프로세스 트리의 모양
 *   (`.scratch/web-admin/probes/e2e_process_tree.mjs`, 관리 화면의 래퍼를 쟀다)을 위젯에도 쓴다. 위젯의 시작 래퍼도 next CLI
 *   를 같은 프로세스에서 부른다는 것은 재지 않고 `tools/start.ts` 를 읽었다. 중계와 사이트는 이 프로세스 안의 서버라 닫는다.
 * - 세 프로세스(serve, build, widget)의 출력은 끝에 `test-results/` 에 남긴다. 토큰과 개인 키는 싣지 않는다.
 */

import { type ChildProcess, spawn, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import type { Server } from "node:http";
import { createRequire } from "node:module";
import { connect, createServer } from "node:net";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import {
  GATES_ENV,
  LLM_ENV,
  OTHER_ORIGIN_ENV,
  SITE_ORIGIN_ENV,
  TRACES_ENV,
  WIDGET_ORIGIN_ENV,
} from "./env";
import { AGENTS, copyRepoPlugins, DEFAULT_MODEL, LLM_AGENT, writeFixturePlugins } from "./plugins";
import { startRelay } from "./relay";
import { startSite } from "./site";
import { AUDIENCE, ISSUER, KEY_ID, siteKey } from "./token";

const APP = dirname(import.meta.dirname);
const REPO = join(APP, "..", "..", "..");
const MCP_FIXTURE_SERVER = join(REPO, "tests", "adapters", "mcp_fixture_server.py");
const LOGS = join(APP, "test-results");
const LISTENING = /Uvicorn running on (http:\/\/127\.0\.0\.1:\d+)/;
const STARTUP_MS = 60_000;
const QUIET = { NEXT_TELEMETRY_DISABLED: "1" };
// serve 가 읽는 토큰 변수. 위젯 Next 로 가는 환경에서는 벗긴다.
const SERVE_TOKENS = ["AGENT_OS_ADMIN_TOKEN", "AGENT_OS_CHANNEL_TOKEN"];
// serve 의 구성 검사는 운영자 토큰과 채널 토큰을 요구한다. 위젯 e2e 는 둘 다 쓰지 않아 이 프로세스가 무작위로 짓는다.
const UNUSED_TOKEN_BYTES = 24;

interface Launched {
  readonly name: string;
  readonly child: ChildProcess;
  readonly output: () => string;
}

export default async function globalSetup(): Promise<() => Promise<void>> {
  const work = mkdtempSync(join(tmpdir(), "agent-os-widget-e2e-"));
  const launched: Launched[] = [];
  const servers: Server[] = [];
  const teardown = async (): Promise<void> => {
    for (const server of servers.toReversed()) {
      await new Promise<void>((resolve) => {
        server.close(() => {
          resolve();
        });
        server.closeAllConnections();
      });
    }
    for (const { child } of launched.toReversed()) {
      await stop(child);
    }
    mkdirSync(LOGS, { recursive: true });
    for (const { name, output } of launched) {
      writeFileSync(join(LOGS, `${name}.log`), output());
    }
    rmSync(work, { recursive: true, force: true });
  };
  try {
    const [relayPort, sitePort, nextPort] = [await freePort(), await freePort(), await freePort()];
    const widgetOrigin = `http://widget.localhost:${String(relayPort)}`;
    const siteOrigin = `http://site.localhost:${String(sitePort)}`;
    const otherOrigin = `http://other.localhost:${String(sitePort)}`;

    const llm = process.env[LLM_ENV] === "1";
    const python = interpreter();
    const plugins = join(work, "plugins");
    const gates = join(work, "gates");
    mkdirSync(gates);
    if (llm) {
      copyRepoPlugins(REPO, plugins);
    }
    writeFixturePlugins(plugins, python, MCP_FIXTURE_SERVER, gates);
    const key = siteKey();
    const siteFile = join(work, "sites.toml");
    const agents: readonly string[] = llm ? [...AGENTS, LLM_AGENT] : AGENTS;
    writeFileSync(siteFile, siteToml(siteOrigin, key.publicPem, agents));
    const traces = process.env[TRACES_ENV] ?? join(work, "traces");

    const serve = launch(
      "serve",
      python,
      [
        "-m",
        "agent_os.main",
        "serve",
        "--port",
        "0",
        "--plugins-root",
        plugins,
        "--traces",
        traces,
        "--site-file",
        siteFile,
        "--model",
        DEFAULT_MODEL,
      ],
      // serve 가 띄운 MCP 서버는 작업 폴더를 물려받고 serve 를 끈 뒤에도 잠시 남는다. work 를 작업 폴더로 두면
      // teardown 이 그 폴더를 지우지 못한다.
      tmpdir(),
      {
        ...process.env,
        PYTHONUTF8: "1",
        AGENT_OS_ADMIN_TOKEN: unusedToken(),
        AGENT_OS_CHANNEL_TOKEN: unusedToken(),
      },
    );
    launched.push(serve);
    const serveUrl = await until(serve, "serve 가 서지 않았다", () => {
      return LISTENING.exec(serve.output())?.[1] ?? null;
    });

    await build(siteFile, launched);
    const widget = launch(
      "widget",
      process.execPath,
      [join(APP, "tools", "start.ts"), "start", "--port", String(nextPort)],
      APP,
      nextEnv(siteFile),
    );
    launched.push(widget);
    await until(widget, "위젯 Next 가 서지 않았다", async () =>
      (await accepts(nextPort)) ? nextPort : null,
    );

    servers.push(
      await startRelay(relayPort, {
        serve: serveUrl,
        next: `http://127.0.0.1:${String(nextPort)}`,
      }),
    );
    servers.push(await startSite(sitePort, { widget: widgetOrigin, other: otherOrigin }, key));

    process.env[WIDGET_ORIGIN_ENV] = widgetOrigin;
    process.env[SITE_ORIGIN_ENV] = siteOrigin;
    process.env[OTHER_ORIGIN_ENV] = otherOrigin;
    process.env[GATES_ENV] = gates;
    return teardown;
  } catch (error: unknown) {
    await teardown();
    throw error;
  }
}

/** 사이트 하나. 허용 출처는 `site.localhost` 하나이고 글자 수 상한은 기본값이다. */
function siteToml(siteOrigin: string, publicPem: string, agents: readonly string[]): string {
  return [
    'schema_version = "1"',
    "",
    "[[sites]]",
    `issuer = ${JSON.stringify(ISSUER)}`,
    `audience = ${JSON.stringify(AUDIENCE)}`,
    `allowed_origins = [${JSON.stringify(siteOrigin)}]`,
    `agents = [${agents.map((name) => JSON.stringify(name)).join(", ")}]`,
    "",
    "[[sites.public_keys]]",
    `kid = ${JSON.stringify(KEY_ID)}`,
    `pem = ${JSON.stringify(publicPem)}`,
    "",
  ].join("\n");
}

/** `uv run` 이 쓰는 가상 환경의 파이썬 인터프리터. */
function interpreter(): string {
  const found = spawnSync("uv", ["run", "python", "-c", "import sys; print(sys.executable)"], {
    cwd: REPO,
    encoding: "utf-8",
  });
  const path = found.stdout.trim();
  if (found.status !== 0 || path === "") {
    throw new Error(`파이썬 인터프리터를 찾지 못했다(uv run python):\n${found.stderr}`);
  }
  return path;
}

function unusedToken(): string {
  return `widget-e2e-unused-${randomBytes(UNUSED_TOKEN_BYTES).toString("hex")}`;
}

/** 위젯 Next(빌드와 start)의 환경. 이 셸의 환경에서 serve 의 토큰 변수를 벗기고 사이트 파일을 준다. */
function nextEnv(siteFile: string): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = { ...process.env, ...QUIET, AGENT_OS_SITE_FILE: siteFile };
  for (const name of SERVE_TOKENS) {
    Reflect.deleteProperty(env, name);
  }
  return env;
}

function launch(
  name: string,
  command: string,
  args: readonly string[],
  cwd: string,
  env: NodeJS.ProcessEnv,
): Launched {
  const child = spawn(command, args, {
    cwd,
    env,
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });
  let output = "";
  // 비우는 쪽이 없는 파이프는 차면 서버를 쓰기에서 세운다. 받는 대로 모은다.
  child.stdout.on("data", (chunk: Buffer) => (output += chunk.toString("utf-8")));
  child.stderr.on("data", (chunk: Buffer) => (output += chunk.toString("utf-8")));
  return { name, child, output: () => output };
}

/** `check` 가 값을 줄 때까지 기다린다. 그 전에 프로세스가 끝나거나 상한을 넘기면 그 출력과 함께 실패한다. */
async function until<T>(
  launched: Launched,
  failure: string,
  check: () => T | null | Promise<T | null>,
): Promise<T> {
  const deadline = Date.now() + STARTUP_MS;
  while (Date.now() < deadline) {
    const found = await check();
    if (found !== null) {
      return found;
    }
    // 신호로 죽으면 exitCode 는 null 이고 signalCode 만 찬다.
    if (launched.child.exitCode !== null || launched.child.signalCode !== null) {
      break;
    }
    await sleep(100);
  }
  throw new Error(`${failure}:\n${launched.output()}`);
}

/**
 * 그 사이트 파일로 위젯을 빌드한다. 허용 출처와 글자 수 상한이 빌드에 박힌다. 시작 래퍼로 빌드해 글꼴 파일의 복사와
 * 페이지 안 번들의 빌드까지 운영과 같은 길을 지난다. 빌드는 앱의 `.next/`, `public/fonts/`, `public/element.js` 를 다시
 * 쓴다.
 */
async function build(siteFile: string, launched: Launched[]): Promise<void> {
  // 시작 래퍼가 next 를 같은 프로세스에서 부르므로 next 의 진입점이 깔렸는지만 먼저 본다.
  createRequire(join(APP, "package.json")).resolve("next/dist/bin/next");
  const built = launch(
    "build",
    process.execPath,
    [join(APP, "tools", "start.ts"), "build"],
    APP,
    nextEnv(siteFile),
  );
  launched.push(built);
  const code = await new Promise<number | null>((resolve) => {
    built.child.once("exit", resolve);
  });
  if (code !== 0) {
    throw new Error(`위젯을 빌드하지 못했다(종료 ${String(code)}):\n${built.output()}`);
  }
}

/** 비어 있는 루프백 포트. 닫은 뒤 곧바로 가져간다. */
async function freePort(): Promise<number> {
  const server = createServer();
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const bound = server.address();
  await new Promise<void>((resolve) =>
    server.close(() => {
      resolve();
    }),
  );
  if (bound === null || typeof bound === "string") {
    throw new Error("빈 포트를 얻지 못했다");
  }
  return bound.port;
}

function accepts(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = connect({ host: "127.0.0.1", port });
    socket.once("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.once("error", () => {
      resolve(false);
    });
  });
}

/** 거두고 끝날 때까지 기다린다. 제때 끝나지 않으면 죽인다. */
async function stop(child: ChildProcess): Promise<void> {
  if (child.exitCode !== null || child.signalCode !== null) {
    return;
  }
  const exited = new Promise<void>((resolve) =>
    child.once("exit", () => {
      resolve();
    }),
  );
  child.kill();
  const timer = setTimeout(() => child.kill("SIGKILL"), 10_000);
  await exited;
  clearTimeout(timer);
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
