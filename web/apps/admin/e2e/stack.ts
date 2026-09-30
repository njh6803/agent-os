/**
 * e2e 의 준비(globalSetup). 실제 `serve` 와, 시작 래퍼로 띄운 실제 관리 화면을 띄운다(web-admin 명세 "e2e").
 * e2e 는 실제 `serve` 의 둘째 구동자이고 모델을 부르지 않는다. 첫째는 `tests/test_main.py` 의 `-m llm` 테스트다.
 *
 * - 픽스처 플러그인 루트는 임시 디렉터리에 쓴다. MCP 매니페스트가 이 기계의 파이썬 인터프리터 경로를 들어야 해서
 *   커밋할 수 없다. 인터프리터는 `uv run` 이 쓰는 가상 환경의 것이다(`tests/test_main.py` 가 `sys.executable` 로
 *   짓는 것과 같다). 목록에 종류마다 행이 서고, 표지 행 둘(읽을 수 없는 매니페스트, 이름이 패턴 밖인 디렉터리)과
 *   꺼진 행 하나가 서게 채운다. 켜고 끄기 흐름이 그 루트의 운영자 파일을 읽도록 경로를 워커의 환경에 넘긴다.
 * - 결정 흐름의 에이전트 둘은 모델 없이 승인 대상 도구(MCP 픽스처 서버의 add)를 `ctx.tool()` 로 직접 부른다. 그래서
 *   결정 뒤의 재개가 모델 없이 끝까지 간다. 멈춘 실행은 흐름이 채널 토큰으로 만든다(`channel.ts`).
 * - 읽기 흐름이 볼 트레이스는 serve 를 띄우기 전에 트레이스 디렉터리에 쓴다(`traces.ts`).
 * - 토큰 둘은 여기서 무작위로 만들어 `serve` 의 환경에 넘긴다. 테스트가 화면에 넣고 흐름의 요청이 싣도록 워커의
 *   환경에도 넘긴다. 관리 화면(Next)에는 넘기지 않는다. 무상태 중계라 토큰을 모른다(ADR 0019). 이 셸의 환경에 토큰
 *   변수가 있어도 Next 에는 벗겨서 준다. 어느 것도 커밋하지 않는다.
 * - `serve` 는 `--port 0` 으로 띄우고 기동 줄에서 주소를 읽는다(`tests/test_main.py` 의 `_serving` 과 같다). 그 주소를
 *   상류로 관리 화면을 빌드한 뒤 `start` 로 띄운다. `rewrites` 는 빌드 산출물에 박히므로 상류는 빌드 전에 정해야 하고,
 *   `dev` 는 설정을 바로 읽어 운영과 다른 길을 잰다. 빌드는 앱의 `.next/` 를 다시 쓴다.
 * - 거두는 것은 `kill()` 이다(제때 끝나지 않을 때만 SIGKILL). 운영체제별 명령(taskkill, 프로세스 그룹)에 기대지
 *   않는다. 래퍼는 next CLI 를 같은 프로세스에서 부르고 `next start` 는 서버를 자식으로 띄우지 않는다. 윈도우 가상
 *   환경의 python.exe 는 기반 인터프리터를 자식으로 띄우지만 부모와 함께 죽는다
 *   (`.scratch/web-admin/probes/e2e_process_tree.mjs`, 쟀다).
 * - 두 프로세스의 출력은 끝에 `test-results/` 에 남긴다. 실패를 서버 쪽 원인과 함께 보기 위해서다. 토큰은 싣지 않는다.
 */

import { type ChildProcess, spawn, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { connect, createServer } from "node:net";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { ADMIN_TOKEN_ENV, ADMIN_URL_ENV, CHANNEL_TOKEN_ENV, PLUGINS_ROOT_ENV } from "./env";
import { writeReadTraces } from "./traces";

const APP = dirname(import.meta.dirname);
const REPO = join(APP, "..", "..", "..");
const MCP_FIXTURE_SERVER = join(REPO, "tests", "adapters", "mcp_fixture_server.py");
const LOGS = join(APP, "test-results");
const LISTENING = /Uvicorn running on (http:\/\/127\.0\.0\.1:\d+)/;
const STARTUP_MS = 60_000;
const QUIET = { NEXT_TELEMETRY_DISABLED: "1" };
// serve 가 읽는 토큰 변수. Next 로 가는 환경에서는 벗긴다.
const SERVE_TOKENS = ["AGENT_OS_ADMIN_TOKEN", "AGENT_OS_CHANNEL_TOKEN"];

interface Launched {
  readonly name: string;
  readonly child: ChildProcess;
  /** 지금까지의 표준 출력과 표준 에러. */
  readonly output: () => string;
}

export default async function globalSetup(): Promise<() => Promise<void>> {
  const work = mkdtempSync(join(tmpdir(), "agent-os-e2e-"));
  const launched: Launched[] = [];
  const teardown = async (): Promise<void> => {
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
    const python = interpreter();
    const plugins = join(work, "plugins");
    writeFixturePlugins(plugins, python);
    const traces = join(work, "traces");
    writeReadTraces(traces);
    const adminToken = token("admin");
    const channelToken = token("channel");

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
      ],
      work,
      {
        ...process.env,
        PYTHONUTF8: "1",
        AGENT_OS_ADMIN_TOKEN: adminToken,
        AGENT_OS_CHANNEL_TOKEN: channelToken,
      },
    );
    launched.push(serve);
    const upstream = await until(serve, "serve 가 서지 않았다", () => {
      return LISTENING.exec(serve.output())?.[1] ?? null;
    });

    await build(upstream);
    const port = await freePort();
    const admin = launch(
      "admin",
      process.execPath,
      [join(APP, "tools", "start.ts"), "start", "--port", String(port)],
      APP,
      nextEnv(upstream),
    );
    launched.push(admin);
    await until(admin, "관리 화면이 서지 않았다", async () =>
      (await accepts(port)) ? port : null,
    );

    process.env[ADMIN_URL_ENV] = `http://127.0.0.1:${String(port)}`;
    process.env[ADMIN_TOKEN_ENV] = adminToken;
    process.env[CHANNEL_TOKEN_ENV] = channelToken;
    process.env[PLUGINS_ROOT_ENV] = plugins;
    return teardown;
  } catch (error: unknown) {
    await teardown();
    throw error;
  }
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

/** 이 serve 만 아는 토큰. 같은 기계의 다른 프로세스가 짐작할 수 없는 값이다. */
function token(role: string): string {
  return `e2e-${role}-${randomBytes(24).toString("hex")}`;
}

/** 관리 화면(빌드와 start)의 환경. 이 셸의 환경에서 serve 의 토큰 변수를 벗기고 상류를 준다. */
function nextEnv(upstream: string): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = { ...process.env, ...QUIET, AGENT_OS_UPSTREAM: upstream };
  for (const name of SERVE_TOKENS) {
    Reflect.deleteProperty(env, name);
  }
  return env;
}

/**
 * 종류 넷의 행, 표지 행 둘, 꺼진 행 하나, 결정 흐름의 에이전트 둘. TOML 기본 문자열은 JSON 문자열과 이스케이프가
 * 같아 경로를 `JSON.stringify` 로 적는다(윈도우 경로의 역슬래시).
 */
function writeFixturePlugins(root: string, python: string): void {
  const write = (path: string, text: string): void => {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), text);
  };
  const manifest = (kind: string, name: string, extra = ""): string =>
    `schema_version = "1"\nkind = "${kind}"\nname = "${name}"\nversion = "0.1.0"\n${extra}`;
  // MCP 픽스처 서버의 add 를 승인 대상으로 두는 에이전트. `tests/test_main.py` 의 `_gated_manifest` 와 같다.
  const gated = (name: string, body: readonly string[]): void => {
    write(
      `agents/${name}/plugin.toml`,
      manifest(
        "agent",
        name,
        'entrypoint = "agent:Agent"\nmcp = ["fixture"]\nrequires_approval = ["add"]\n',
      ),
    );
    write(
      `agents/${name}/agent.py`,
      [
        "import asyncio",
        "from collections.abc import AsyncIterator",
        "",
        "from agent_os.sdk import AgentContext, Event, RunFinished",
        "",
        "",
        "class Agent:",
        "    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:",
        ...body.map((line) => `        ${line}`),
        "",
      ].join("\n"),
    );
  };

  write("agents/echo/plugin.toml", manifest("agent", "echo", 'entrypoint = "agent:Agent"\n'));
  write(
    "agents/echo/agent.py",
    [
      "from collections.abc import AsyncIterator",
      "",
      "from agent_os.sdk import AgentContext, Event, RunFinished",
      "",
      "",
      "class Agent:",
      "    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:",
      '        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"echo:{request}")',
      "",
    ].join("\n"),
  );
  // 승인하면 도구를 부르고 2초 뒤에 끝난다. 그 틈에 재개 스트림이 조각으로 오는지(첫 이벤트가 결말보다 먼저 화면에
  // 있는지) 결정 흐름이 본다. 켜고 끄기 흐름이 끄는 에이전트도 이것이다.
  gated("gated", [
    'total = await ctx.tool("add", a=2, b=3)',
    "await asyncio.sleep(2)",
    "yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=total)",
  ]);
  // 한 턴에 승인 대상이 둘이다. 오래된 화면 흐름이 첫 일시정지를 다른 곳에서 허가하면 둘째에서 다시 멈춘다.
  gated("twice", [
    'first = await ctx.tool("add", a=2, b=3)',
    'second = await ctx.tool("add", a=4, b=5)',
    'yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"{first}/{second}")',
  ]);
  write("agents/broken/plugin.toml", 'schema_version = "1"\nkind = \n');
  // 디렉터리 이름이 패턴 밖인 표지. 주소에서 인코딩해야 하는 글자(띄어쓰기)가 든다.
  write("agents/Old Calc/plugin.toml", manifest("agent", "old-calc"));
  write(
    "mcp/fixture/plugin.toml",
    manifest(
      "mcp",
      "fixture",
      `[server]\ncommand = ${JSON.stringify(python)}\nargs = [${JSON.stringify(MCP_FIXTURE_SERVER)}]\n`,
    ),
  );
  write("skills/summarize/plugin.toml", manifest("skill", "summarize"));
  write("models/sonnet/plugin.toml", manifest("model", "sonnet"));
  write(
    "disabled.toml",
    'schema_version = "1"\nagent = []\nmcp = []\nskill = ["summarize"]\nmodel = []\n',
  );
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
    if (launched.child.exitCode !== null) {
      break;
    }
    await sleep(100);
  }
  throw new Error(`${failure}:\n${launched.output()}`);
}

/** 그 상류로 관리 화면을 빌드한다. 빌드 때의 상류가 `rewrites` 에 박힌다. */
async function build(upstream: string): Promise<void> {
  const next = createRequire(join(APP, "package.json")).resolve("next/dist/bin/next");
  const built = launch("build", process.execPath, [next, "build"], APP, nextEnv(upstream));
  const code = await new Promise<number | null>((resolve) => {
    built.child.once("exit", resolve);
  });
  if (code !== 0) {
    throw new Error(`관리 화면을 빌드하지 못했다(종료 ${String(code)}):\n${built.output()}`);
  }
}

/** 비어 있는 루프백 포트. 닫은 뒤 곧바로 관리 화면이 가져간다. */
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
