// 티켓 04: 실제 `serve` 와 실제 관리 화면(래퍼로 띄운 next start)을 띄워 중계를 잰다. 결정은 하지 않고 결과만 낸다.
//   node .scratch/web-admin/probes/admin_relay.mjs      (저장소 루트에서)
//
// 재는 것
//   relay    토큰을 실은 GET /api/plugins 가 파이썬의 JSON 그대로 돌아온다(상태, content-type, 본문 바이트). 토큰이
//            없으면 401, 다른 출처의 preflight(OPTIONS)도 401 이다. gzip 을 청해도 Next 의 페이지가 압축되지 않는다
//            (compress: false 가 빌드된 서버에 걸렸다. /api 의 본문은 압축 하한 1KB 아래라 이것으로 재지 못한다)
//   baked    rewrites 가 빌드 산출물(routes-manifest.json)에 박히고, start 때 상류 입력을 다른 루프백 값으로 바꿔도
//            빌드 때의 상류로 넘긴다
//   refuse   루프백이 아닌 상류는 build, start, dev 가 설정을 읽는 자리에서 구성 오류로 끝난다. ::1 상류는 build 에서
//            잰다(같은 설정 파일이라 start·dev 도 같은 자리를 지난다). dev 는 포트를 루프백에 먼저 열고 설정을 읽는다
//   ipv6     관리 화면은 ::1 에도 서서 127.0.0.1 상류로 넘긴다. Next 의 prepareDestination 은 여전히 IPv6 리터럴
//            목적지에서 던진다. 던지지 않게 되면 상류에 ::1 을 다시 받을 수 있다(ADR 0011 의 2026-09-30 이력)
//
// 토큰은 이 스크립트가 무작위로 만들어 두 프로세스의 환경에만 넘긴다. 출력에 싣지 않는다.
// 앱의 .next 는 이 스크립트가 빌드마다 다시 쓴다. 트레이스는 임시 디렉터리에 쓴다.
// 포트 8765(serve), 3919·3920·3921(관리 화면)이 비어 있어야 한다. 띄운 프로세스는 트리째 내린다(윈도우는
// taskkill /T /F, 그 밖은 프로세스 그룹). 약 1분. 종료 코드: 모두 기대대로면 0, 아니면 1.
// 2026-09-30 결과(Next 16.3.6, 윈도우): 모두 기대대로. 이 판정을 두기 전에는 상류 http://[::1]:8766 이 빌드를 지나고
// /api 요청마다 500(`TypeError: Missing parameter name at 1`)이었다.

import { spawn, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join } from "node:path";

const ROOT = process.cwd();
const APP = join(ROOT, "web", "apps", "admin");
const START = join(APP, "tools", "start.ts");
const NEXT_BIN = join(APP, "node_modules", "next", "dist", "bin", "next");
const TRACES = mkdtempSync(join(tmpdir(), "admin-relay-"));
const ADMIN_TOKEN = `probe-admin-${randomBytes(12).toString("hex")}`;
const CHANNEL_TOKEN = `probe-channel-${randomBytes(12).toString("hex")}`;
const QUIET = { NEXT_TELEMETRY_DISABLED: "1" };

const results = [];
const check = (name, ok, detail = "") => {
  results.push(ok);
  console.log(`${ok ? "기대대로" : "어긋남 "}  ${name}${detail ? `  (${detail})` : ""}`);
};
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function launch(command, args, env, cwd = ROOT) {
  const child = spawn(command, args, {
    cwd,
    env: { ...process.env, ...QUIET, ...env },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
    detached: process.platform !== "win32",
  });
  child.log = "";
  child.stdout.on("data", (chunk) => (child.log += chunk));
  child.stderr.on("data", (chunk) => (child.log += chunk));
  return child;
}

function stop(child) {
  if (child.exitCode !== null) return;
  if (process.platform === "win32") {
    spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" });
  } else {
    process.kill(-child.pid, "SIGKILL");
  }
}

async function until(url, child) {
  for (let i = 0; i < 120; i += 1) {
    if (child.exitCode !== null) throw new Error(`${url} 전에 끝났다:\n${child.log}`);
    try {
      await fetch(url);
      return;
    } catch {
      await sleep(500);
    }
  }
  throw new Error(`${url} 가 서지 않았다:\n${child.log}`);
}

function serve(host, port) {
  return launch(
    "uv",
    ["run", "agent-os", "serve", "--host", host, "--port", String(port), "--traces", TRACES],
    { AGENT_OS_ADMIN_TOKEN: ADMIN_TOKEN, AGENT_OS_CHANNEL_TOKEN: CHANNEL_TOKEN },
  );
}

function build(upstream) {
  return spawnSync(process.execPath, [NEXT_BIN, "build"], {
    cwd: APP,
    env: { ...process.env, ...QUIET, AGENT_OS_UPSTREAM: upstream },
    encoding: "utf-8",
  });
}

function start(host, port, upstream) {
  const env = upstream === undefined ? {} : { AGENT_OS_UPSTREAM: upstream };
  return launch(process.execPath, [START, "start", "--hostname", host, "--port", String(port)], env);
}

function bracket(host) {
  return host.includes(":") ? `[${host}]` : host;
}

function bakedDestinations() {
  const manifest = JSON.parse(readFileSync(join(APP, ".next", "routes-manifest.json"), "utf-8"));
  return manifest.rewrites.afterFiles.map((rewrite) => `${rewrite.source} -> ${rewrite.destination}`);
}

async function relay(label, appHost, appPort) {
  const upstream = "http://127.0.0.1:8765";
  const built = build(upstream);
  check(`${label}: ${upstream} 로 빌드된다`, built.status === 0, `종료 ${built.status}`);
  check(
    `${label}: rewrites 가 routes-manifest.json 에 박힌다`,
    JSON.stringify(bakedDestinations()) === JSON.stringify([`/api/:path* -> ${upstream}/:path*`]),
    bakedDestinations().join(", "),
  );

  const python = serve("127.0.0.1", 8765);
  // start 때의 상류 입력은 일부러 다른 루프백 포트다. 넘기는 곳이 빌드 때 값인지 본다(9 번 포트에는 아무것도 없다).
  const app = start(appHost, appPort, "http://127.0.0.1:9");
  try {
    await until(`${upstream}/health`, python);
    const origin = `http://${bracket(appHost)}:${appPort}`;
    await until(`${origin}/`, app);

    const auth = { Authorization: `Bearer ${ADMIN_TOKEN}` };
    const direct = await fetch(`${upstream}/plugins`, { headers: auth });
    const directBody = Buffer.from(await direct.arrayBuffer());
    const relayed = await fetch(`${origin}/api/plugins`, { headers: auth });
    const relayedBody = Buffer.from(await relayed.arrayBuffer());
    check(
      `${label}: 토큰을 실은 /api/plugins 가 파이썬의 JSON 그대로다(start 때 상류 입력과 무관하게 빌드 때 상류로)`,
      relayed.status === 200 &&
        direct.status === 200 &&
        relayed.headers.get("content-type") === direct.headers.get("content-type") &&
        relayedBody.equals(directBody),
      `상태 ${relayed.status}, ${relayed.headers.get("content-type")}, ${relayedBody.length} 바이트`,
    );

    // fetch 는 압축을 풀어 주므로 머리만 본다. 본문 크기는 압축 하한(1KB)을 넘는지 보려고 싣는다.
    const page = await fetch(`${origin}/`, { headers: { "Accept-Encoding": "gzip" } });
    const pageBody = await page.text();
    check(
      `${label}: gzip 을 청해도 Next 의 페이지를 압축하지 않는다(compress: false)`,
      page.headers.get("content-encoding") === null && pageBody.length > 1024,
      `content-encoding ${page.headers.get("content-encoding")}, ${pageBody.length} 자`,
    );

    const bare = await fetch(`${origin}/api/plugins`);
    check(`${label}: 토큰이 없으면 401`, bare.status === 401, `상태 ${bare.status}`);

    const preflight = await fetch(`${origin}/api/plugins`, {
      method: "OPTIONS",
      headers: {
        Origin: "http://evil.example",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization",
      },
    });
    check(
      `${label}: 다른 출처의 preflight 는 401 이고 CORS 허용 헤더가 없다`,
      preflight.status === 401 && preflight.headers.get("access-control-allow-origin") === null,
      `상태 ${preflight.status}`,
    );
  } finally {
    stop(app);
    stop(python);
  }
}

/** 스스로 끝나면 그 종료 코드, 1분 안에 끝나지 않으면 "시간 초과"다. 어느 쪽이든 트리를 내린다. */
async function exited(child) {
  const code = await new Promise((resolve) => {
    const timer = setTimeout(() => resolve("시간 초과"), 60_000);
    child.on("exit", (exit) => {
      clearTimeout(timer);
      resolve(exit);
    });
  });
  stop(child);
  return code;
}

function refuses(label, run) {
  const out = `${run.stdout ?? ""}${run.stderr ?? ""}`;
  check(
    label,
    run.status !== 0 && out.includes("AGENT_OS_UPSTREAM") && out.includes("ssh -L"),
    `종료 ${run.status}`,
  );
}

function nextCompilesIpv6Destination() {
  const load = createRequire(join(APP, "package.json"));
  const { prepareDestination } = load("next/dist/shared/lib/router/utils/prepare-destination.js");
  try {
    prepareDestination({
      destination: "http://[::1]:8766/:path*",
      params: { path: ["plugins"] },
      query: {},
      appendParamsToQuery: false,
    });
    return "던지지 않는다";
  } catch (error) {
    return `${error.name}: ${error.message}`;
  }
}

try {
  await relay("관리 화면 127.0.0.1", "127.0.0.1", 3919);
  await relay("관리 화면 ::1", "::1", 3920);

  const ipv6 = nextCompilesIpv6Destination();
  check(
    "Next 의 prepareDestination 은 IPv6 리터럴 목적지에서 던진다(던지지 않게 되면 ::1 상류를 다시 볼 때다)",
    ipv6 === "TypeError: Missing parameter name at 1",
    ipv6,
  );

  refuses("루프백이 아닌 상류는 build 가 설정을 읽을 때 구성 오류다", build("http://192.168.0.10:8000"));
  const v6 = build("http://[::1]:8000");
  check(
    "::1 상류는 build 가 설정을 읽을 때 구성 오류이고 127.0.0.1 을 안내한다",
    v6.status !== 0 && `${v6.stdout}${v6.stderr}`.includes("--host 127.0.0.1"),
    `종료 ${v6.status}`,
  );

  // 빌드 산출물이 있는 채로 start 만 다른 상류를 받는다. start 도 설정 파일을 읽어 거기서 끝나야 한다.
  build("http://127.0.0.1:8765");
  const late = start("127.0.0.1", 3919, "http://0.0.0.0:8000");
  refuses("루프백이 아닌 상류는 start 가 설정을 읽을 때 구성 오류다", {
    status: await exited(late),
    stdout: late.log,
  });

  const dev = launch(process.execPath, [START, "dev", "--port", "3921"], {
    AGENT_OS_UPSTREAM: "http://0.0.0.0:8000",
  });
  refuses("루프백이 아닌 상류는 dev 가 설정을 읽을 때 구성 오류다", {
    status: await exited(dev),
    stdout: dev.log,
  });
} finally {
  rmSync(TRACES, { recursive: true, force: true });
}

process.exitCode = results.every(Boolean) ? 0 : 1;
