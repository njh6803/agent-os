// portal-admin 명세: 운영자의 로그인 쿠키를 다른 포트의 서버가 Agent OS 에 전해 로그인을 확인하고 이어 주는 흐름(ADR 0064 결정
// "로그인", ADR 0065 결정 "위젯 테스트 페이지")을 대역(스텁)과 실제 Chromium 으로 잰다. 결정은 하지 않고 결과만 낸다.
//   node .scratch/portal-admin/probes/login_relay/probe.mjs [--mode start|dev] [--rounds 5] [--ttl 2] [--grace 1]
//        [--out <폴더>] [--update] [--channel chromium] [--only <묶음,…>] [--keep-alive 300]
//
// 띄우는 것
//   A  Agent OS 대역(agentos_stub.py, FastAPI). 관리 화면의 자리이기도 하다. 브라우저가 http://localhost:<A> 로 직접 친다
//   W  위젯 관리 서버 대역(widget_admin_stub.py, FastAPI). Agent OS 를 부르는 클라이언트는 경로의 첫 마디가 고른다. 마디가
//      없으면 httpx, /x2 는 httpx2, /x2n 은 쿠키를 받지 않는 통을 준 httpx2 다. 브라우저는 치지 않는다
//   B  실제 관리 화면 앱(web/apps/admin)을 시작 래퍼로 띄우고 AGENT_OS_UPSTREAM 을 W 로 준다. 위젯 관리 화면도 같은 Next
//      rewrites 중계를 쓸 것이라 그 자리에 세웠다. 브라우저의 http://localhost:<B>/api/<경로> 가 W 의 /<경로> 로 간다
//   C  위젯 테스트 페이지 서버 대역(tester_stub.mjs, node:http). 이 프로세스 안에 선다. Agent OS 를 부르는 길은 경로의 첫 마디가
//      고른다. /fetch 는 Node 의 전역 fetch, /http 는 node:http, /oaf 는 openapi-fetch 의 클라이언트다
//   앱의 소스와 설정은 고치지 않는다. start 모드는 빌드가 앱의 .next/ 를 다시 쓴다(무시되는 폴더).
//
// 회차와 재는 것(결과의 키는 회차 이름이다)
//   대조      대역의 동작. 옛 번호 재사용이 끊는다, 유예 둘의 뜻, 요청 출처 검사의 판정, JWT 의 만료
//   1         httpx, Node 의 fetch, node:http 가 Agent OS 에 보낸 GET(지금 누구인지)과 POST(갱신)의 머리와 요청 출처 검사의 판정
//   2         갱신 응답의 Set-Cookie 줄이 중계를 지나 브라우저에 닿은 모양(Agent OS 대역이 낸 줄과 CDP 가 받은 줄을 견준다),
//             쿠키 저장소의 속성, 갱신이 거절될 때의 지우는 줄. 대조로 줄을 한 값으로 합쳐 옮기는 중계를 둔다
//   3         포트 A 로그인 → 다른 포트에서 확인 → 만료 → 다른 포트의 요청이 갱신을 거쳐 이어짐 → 포트 A 가 그 쿠키로 이어짐
//   4         만료 직후 포트 B 의 페이지가 요청 넷을 동시에 보낼 때(설계 1: 중계가 스스로 갱신, 설계 2: 화면이 갱신을 한 번
//             부름)와 탭 둘이 동시에 갱신할 때. 유예 0, 유예 chain, 유예 family 에서 각각. 응답의 차례를 뒤집는 갈래를 둔다
//   5         대조. 브라우저가 보낸 머리를 그대로 Agent OS 에 전하는 중계와 Cookie 만 전하는 중계
//   덤        httpx 와 httpx2 의 함께 쓰는 클라이언트가 Set-Cookie 로 받은 쿠키를 들고 있는가. 대조로 쿠키를 받지 않는 통을 준
//             httpx2 클라이언트를 둔다
//   6         openapi-fetch 로 부르는 길에만 있는 둘. 함께 쓰는 클라이언트가 받은 쿠키를 다음 요청에 싣는가, 호출에
//             AbortSignal.timeout 을 넘겼을 때 답을 늦추는 대역에서 무엇이 던져지는가(견주려고 전역 fetch 의 길도 같이 잰다)
// 1 과 2 는 httpx, Node 의 fetch, node:http, httpx2, openapi-fetch 다섯 길에서 잰다. 4 의 설계 2(유예 0)는 포트 C 의 fetch 와
// node:http 두 길과 httpx2 에서도 잰다.
//
// 표지(재려는 상황이 그 회차에 실제로 났는지). 회차마다 아래를 단언하고, 하나라도 없는 회차는 측정으로 세지 않는다. 그런 회차나
// 예외로 끝난 회차가 있으면 종료 코드가 0 이 아니다.
//   - JWT 가 실제로 만료됐다: Agent OS 대역의 기록에 그 요청의 "지금 누구인지"가 401 access_expired 로 있다
//   - 갱신 요청이 중계에서 왔다: 그 갱신의 기록에 브라우저만 붙이는 Sec-Fetch-Site 가 없고 주소의 probe 가 그 중계의 길이다
//   - 쿠키 값이 실제로 바뀌었다: 브라우저 저장소의 값이 대역이 그 갱신에서 낸 이름표(at1·rt1 …)다
//   - 동시 갱신이 실제로 났다: 같은 번호(rt0)를 든 갱신이 둘 이상 대역에 닿았다
//   - 화면이 갱신을 한 번 부르는 설계가 실제로 시험됐다: 요청 넷이 모두 401 을 받았다(페이지가 센 수)
//   - 늦은 401 이 실제로 갱신이 끝난 뒤에 닿았다: 화면이 갱신을 두 번 불렀고 둘째가 든 번호가 첫 갱신이 낸 rt1 이다
//   - 응답의 차례가 실제로 뒤집혔다: 브라우저에 남은 번호가 대역이 먼저 낸 rt1 이다
//   - 브라우저의 머리가 그대로 전해졌다/전해지지 않았다: 중계가 받은 Sec-Fetch-Site 와 대역이 받은 머리를 맞댄다
//   - 클라이언트가 쿠키가 든 응답을 실제로 받았다: 그 회차에 중계가 한 호출의 기록에 Set-Cookie 줄이 있다
//   - 제한 시간이 실제로 걸렸다: 끊긴 호출이 대역에 닿았고(대역의 기록), 던져진 것의 이름이 TimeoutError 이고, 걸린 시간이 제한
//     시간과 대역이 답을 잡아 둔 시간 사이다. 대역이 답을 잡아 두었다는 것은 긴 제한 시간의 호출이 그 시간 뒤에 답을 받은 것으로 본다
// 대역이 "끊는다"는 동작 자체는 대조 회차가 먼저 보인다.
//
// 결과는 stable(다시 돌아도 같아야 하는 값)과 racy(응답이 닿는 차례에 달려 회차마다 갈릴 수 있는 값)로 나눈다. stable 은 포트와
// 쿠키 값을 이름표로 바꾼 뒤 같은 폴더의 expected.json 과 견주고, 다르면 다른 자리를 찍고 1 로 끝난다. expected.json 은 미리 적은
// 기대가 아니라 첫 측정의 결과를 --update 로 받아 적은 것이다. 원본 기록은 --out 폴더의 results.json 에 쓴다.
// 쿠키 값은 대역이 지은 무작위 값이고 비밀이 아니다.
// 띄운 프로세스는 트리째 내린다. 끄기 직전에 그 pid 의 명령줄에 이 회차의 포트가 있을 때만 끈다(윈도우는 taskkill /T /F,
// 그 밖은 프로세스 그룹). 없으면 끄지 않고 알린다.

import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import http from "node:http";
import { createRequire } from "node:module";
import { connect, createServer } from "node:net";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";
import { close, createTester, listen } from "./tester_stub.mjs";

const HERE = import.meta.dirname;
const ROOT = join(HERE, "..", "..", "..", "..");
const APP = join(ROOT, "web", "apps", "admin");
const START = join(APP, "tools", "start.ts");
const EXPECTED = join(HERE, "expected.json");
const load = createRequire(join(APP, "package.json"));
const NEXT_BIN = load.resolve("next/dist/bin/next");
// openapi-fetch 는 web/packages/api-client 가 의존하는 것을 그 패키지를 기준으로 푼다(설치하지 않는다). require 로 풀리는
// 것은 CJS 빌드라, 같은 패키지의 ESM 빌드(api-client 가 import 하는 쪽)를 파일 주소로 불러온다.
const OPENAPI_FETCH_DIR = dirname(dirname(createRequire(join(ROOT, "web", "packages", "api-client", "package.json")).resolve("openapi-fetch")));
const OPENAPI_FETCH_VERSION = JSON.parse(readFileSync(join(OPENAPI_FETCH_DIR, "package.json"), "utf-8")).version;
const { default: createOpenapiClient } = await import(pathToFileURL(join(OPENAPI_FETCH_DIR, "dist", "index.mjs")).href);
const ACCOUNT = "probe-operator";
const AT = "__Host-aos_at";
const RT = "__Host-aos_rt";
const REFRESH_MAX_AGE = 1800;
const SETTLE_MS = 2500;

const { values: args } = parseArgs({
  options: {
    mode: { type: "string", default: "start" },
    rounds: { type: "string", default: "5" },
    ttl: { type: "string", default: "2" },
    grace: { type: "string", default: "1" },
    out: { type: "string" },
    update: { type: "boolean", default: false },
    channel: { type: "string" },
    only: { type: "string" },
    // 대역 둘(uvicorn)이 쉬는 연결을 닫기까지의 초. uvicorn 의 기본값은 5 다. 기본값으로 돈 전체 실행 하나에서 포트 B 의
    // 요청 넷 가운데 둘이 대역에 닿지 못하고 500 으로 돌아왔다(README "측정 밖에서 본 것"). 그 회차는 표지가 없어 측정으로
    // 세지 않았다. 재려는 것이 연결의 수명이 아니라 쿠키와 갱신이라 길게 준다. 5 를 주면 그때의 조건으로 돈다.
    "keep-alive": { type: "string", default: "300" },
  },
});
const MODE = args.mode;
const ROUNDS = Number(args.rounds);
const TTL = Number(args.ttl);
const GRACE = Number(args.grace);
const KEEP_ALIVE = Number(args["keep-alive"]);
if ((MODE !== "start" && MODE !== "dev") || !(ROUNDS >= 1) || !(TTL > 0) || !(GRACE > 0) || !(GRACE < TTL)) {
  console.error("--mode 는 start 나 dev, --rounds 는 1 이상, --ttl 과 --grace 는 0 보다 크고 grace 가 ttl 보다 작아야 한다");
  process.exit(2);
}
if (!Number.isInteger(KEEP_ALIVE) || KEEP_ALIVE < 1) {
  console.error("--keep-alive 는 1 이상의 정수(초)다");
  process.exit(2);
}
const OUT = args.out ?? mkdtempSync(join(tmpdir(), "login-relay-"));
mkdirSync(OUT, { recursive: true });
// JWT 를 낸 뒤 이만큼 기다리면 만료다. 다음 갱신은 유예(GRACE)보다 늦게 온다(실제 설정에서도 JWT 의 수명이 유예보다 길다).
const EXPIRY_MS = TTL * 1000 + 400;
const GRACES = {
  none: { grace_seconds: 0 },
  chain: { grace_seconds: GRACE, grace_kind: "chain" },
  family: { grace_seconds: GRACE, grace_kind: "family" },
};

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const same = (left, right) => JSON.stringify(left) === JSON.stringify(right);

// ---------------------------------------------------------------------------------------------------------------------
// 프로세스와 포트

async function freePort() {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();
  await new Promise((resolve) => server.close(resolve));
  return port;
}

function refused(port) {
  return new Promise((resolve) => {
    const socket = connect({ host: "127.0.0.1", port });
    socket.once("connect", () => {
      socket.destroy();
      resolve(false);
    });
    socket.once("error", () => resolve(true));
  });
}

function nextEnv(upstream) {
  const env = { ...process.env, NEXT_TELEMETRY_DISABLED: "1", AGENT_OS_UPSTREAM: upstream };
  delete env.AGENT_OS_ADMIN_TOKEN;
  delete env.AGENT_OS_CHANNEL_TOKEN;
  return env;
}

function launch(command, commandArgs, options, port, commandTail) {
  const child = spawn(command, commandArgs, {
    ...options,
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
    detached: process.platform !== "win32",
  });
  let output = "";
  let failed = null;
  child.stdout.on("data", (chunk) => (output += chunk));
  child.stderr.on("data", (chunk) => (output += chunk));
  child.on("error", (error) => (failed = error));
  return { child, port, commandTail, output: () => output, failed: () => failed };
}

/** 대역(파이썬)을 프로젝트 인터프리터로 띄운다. 명령줄의 `--port <포트>` 가 이 회차의 표지다. */
function launchStub(file, port, extra = []) {
  const tail = ["--port", String(port)];
  const rest = [...extra, "--keep-alive", String(KEEP_ALIVE)];
  return launch("uv", ["run", "python", join(HERE, file), ...tail, ...rest], { cwd: ROOT }, port, tail.join(" "));
}

function launchAdmin(mode, port, upstream) {
  const tail = [mode, "--hostname", "127.0.0.1", "--port", String(port)];
  return launch(process.execPath, [START, ...tail], { cwd: APP, env: nextEnv(upstream) }, port, tail.join(" "));
}

/** 그 pid 의 명령줄. 읽지 못하면 빈 글이다. 윈도우는 PowerShell 로, 그 밖은 `ps` 로 읽는다. */
function commandLine(pid) {
  const asked =
    process.platform === "win32"
      ? spawnSync(
          "powershell",
          ["-NoProfile", "-Command", `(Get-CimInstance Win32_Process -Filter "ProcessId=${pid}").CommandLine`],
          { encoding: "utf-8", timeout: 30_000 },
        )
      : spawnSync("ps", ["-o", "args=", "-p", String(pid)], { encoding: "utf-8", timeout: 30_000 });
  return typeof asked.stdout === "string" ? asked.stdout : "";
}

/**
 * 트리째 내린다. 끄기 직전에 그 pid 의 명령줄을 읽어 이 회차의 인자(포트)가 있을 때만 끈다(`.claude/rules/probes.md` 의
 * 끄기 항목). 없으면 끄지 않고 그 pid 를 찍는다. 그때 프로세스가 남아 있으면 아래의 포트 확인이 거짓을 돌려주어 실행이
 * "내리지 못했다"로 끝난다. POSIX 갈래(`ps` 로 읽고 프로세스 그룹을 끈다)는 돌려 보지 않았다. 이 프로브를 돌린 곳은
 * 윈도우뿐이다.
 */
async function stop(started) {
  const { child } = started;
  if (child.exitCode === null && child.signalCode === null && child.pid !== undefined) {
    if (commandLine(child.pid).includes(started.commandTail)) {
      const exited = new Promise((resolve) => child.once("exit", resolve));
      if (process.platform === "win32") {
        spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore", timeout: 30_000 });
      } else {
        process.kill(-child.pid, "SIGKILL");
      }
      await Promise.race([exited, sleep(15_000)]);
    } else {
      console.log(`pid ${child.pid} 의 명령줄에 이 회차의 인자(${started.commandTail})가 없어 끄지 않았다`);
    }
  }
  for (let i = 0; i < 100; i += 1) {
    if (await refused(started.port)) return true;
    await sleep(100);
  }
  return false;
}

function rawRequest(method, url, headers = {}, body) {
  return new Promise((resolve, reject) => {
    const payload = body === undefined ? null : Buffer.from(JSON.stringify(body));
    const extra = payload === null ? {} : { "Content-Type": "application/json", "Content-Length": payload.length };
    const request = http.request(url, { method, agent: false, timeout: 30_000, headers: { ...headers, ...extra } }, (answer) => {
      const chunks = [];
      answer.on("data", (chunk) => chunks.push(chunk));
      answer.on("end", () => {
        const text = Buffer.concat(chunks).toString("utf-8");
        let json = null;
        try {
          json = JSON.parse(text);
        } catch {
          // JSON 이 아닌 답(문서)이다.
        }
        resolve({ status: answer.statusCode, setCookie: answer.headers["set-cookie"] ?? [], text, json });
      });
      // 응답이 끝나기 전에 연결이 닫히면 `end` 가 오지 않는다. 그때 끝없이 기다리지 않게 던진다.
      answer.on("error", reject);
      answer.on("close", () => {
        if (!answer.complete) reject(new Error(`${url} 의 응답이 끝나기 전에 연결이 닫혔다`));
      });
    });
    request.on("timeout", () => request.destroy(new Error(`${url} 시간 초과`)));
    request.on("error", reject);
    request.end(payload ?? undefined);
  });
}

async function untilUp(started, url, what) {
  const deadline = Date.now() + 180_000;
  while (Date.now() < deadline) {
    if (started.failed() !== null) throw new Error(`${what} 을 띄우지 못했다: ${started.failed()}`);
    if (started.child.exitCode !== null) throw new Error(`${what} 이 서기 전에 끝났다:\n${started.output()}`);
    try {
      const answer = await rawRequest("GET", url);
      if (answer.status === 200) return answer;
    } catch {
      // 아직 서지 않았다.
    }
    await sleep(300);
  }
  throw new Error(`${what} 이 서지 않았다:\n${started.output()}`);
}

// ---------------------------------------------------------------------------------------------------------------------
// 대역과 말하기

const ports = { a: await freePort(), w: await freePort(), b: await freePort(), c: 0 };
const aosBase = `http://127.0.0.1:${ports.a}`;
const widgetBase = `http://127.0.0.1:${ports.w}`;
const aOrigin = `http://localhost:${ports.a}`;
const bOrigin = `http://localhost:${ports.b}`;
let cOrigin = "";

async function control(base, path, body) {
  const answer = await rawRequest(body === undefined ? "GET" : "POST", `${base}${path}`, {}, body);
  if (answer.status !== 200 || answer.json === null) throw new Error(`${path} 가 ${answer.status} 로 답했다: ${answer.text}`);
  if (typeof answer.json.problem === "string") throw new Error(`${path}: ${answer.json.problem}`);
  return answer.json;
}

const resetStub = (config) => control(aosBase, "/__probe/reset", { access_ttl: TTL, ...config });
const stubLogin = async () => (await control(aosBase, "/__probe/state")).logins.at(-1);

const aosLog = [];
async function syncAos() {
  aosLog.push(...(await control(aosBase, `/__probe/log?since=${aosLog.length}`)));
}
const widgetLog = [];
async function syncWidget() {
  widgetLog.push(...(await control(widgetBase, `/__probe/log?since=${widgetLog.length}`)));
  return widgetLog;
}
/** 그 태그와 길로 Agent OS 대역에 닿은 요청들(닿은 차례). */
const aosBy = (tag, via) => aosLog.filter((entry) => entry.probe === `${tag}.${via}`);
/** 태그가 그 머리로 시작하는 요청들. 한 걸음이 요청 여럿(확인, 갱신, 다시 보내기)으로 될 때 쓴다. */
const aosWith = (head, via) =>
  aosLog.filter((entry) => typeof entry.probe === "string" && entry.probe.startsWith(head) && entry.probe.endsWith(`.${via}`));

function headerOf(entry, name) {
  if (entry === undefined || entry === null) return null;
  const found = entry.headers.filter(([key]) => key.toLowerCase() === name).map(([, value]) => value);
  return found.length === 0 ? null : found.join(" | ");
}

const WATCHED = ["sec-fetch-site", "sec-fetch-mode", "sec-fetch-dest", "origin", "referer"];
function watched(entry) {
  if (entry === undefined || entry === null) return null;
  const out = {};
  for (const name of WATCHED) out[name] = headerOf(entry, name);
  out.cookieNames = (headerOf(entry, "cookie") ?? "")
    .split("; ")
    .filter((part) => part !== "")
    .map((part) => part.split("=")[0])
    .sort();
  return out;
}

/** Set-Cookie 줄들에서 다음 요청에 실을 Cookie 머리를 짓는다(대조 회차가 브라우저 없이 쓴다). */
function cookieFrom(lines) {
  return lines
    .map((line) => line.split(";", 1)[0])
    .filter((pair) => !pair.endsWith("=") && !pair.endsWith('=""'))
    .join("; ");
}

const direct = (method, path, tag, headers = {}, body) =>
  rawRequest(method, `${aosBase}${path}?probe=${tag}.probe`, headers, body);

// ---------------------------------------------------------------------------------------------------------------------
// 회차

const rounds = [];
let tagHead = "r0";
const T = (name) => `${tagHead}-${name}`;

function deepMap(value, change) {
  if (typeof value === "string") return change(value);
  if (Array.isArray(value)) return value.map((item) => deepMap(item, change));
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, deepMap(item, change)]));
  }
  return value;
}

/** 포트와 이 회차에 대역이 낸 쿠키 값을 이름표로 바꾸는 함수. 값은 회차마다 reset 으로 새로 시작한다. */
async function normalizer() {
  const labels = await control(aosBase, "/__probe/labels");
  const swaps = [
    ...Object.entries(labels).map(([value, label]) => [value, `<${label}>`]),
    [`:${ports.a}`, ":<A>"],
    [`:${ports.w}`, ":<W>"],
    [`:${ports.b}`, ":<B>"],
    [`:${ports.c}`, ":<C>"],
  ];
  // Starlette 의 delete_cookie 는 지우는 줄에 그 순간의 시각을 expires 로 싣는다. 견줌(identical)은 바꾸기 전의 줄로 한다.
  const stamp = /expires=[A-Za-z]{3}, \d{2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2} GMT/g;
  return (text) => swaps.reduce((acc, [literal, label]) => acc.split(literal).join(label), text).replace(stamp, "expires=<그때의 시각>");
}

/**
 * 회차 하나. body 는 mark(표지 이름, 봤는가, 덧붙임)를 받아 표지를 적고 { stable, racy } 를 돌려준다. 표지를 하나도 적지
 * 않았거나 하나라도 없거나 예외로 끝나면 측정이 아니다.
 */
async function round(name, body) {
  tagHead = `r${rounds.length + 1}`;
  const current = { name, measured: false, markers: [], stable: null, racy: null, error: null };
  rounds.push(current);
  console.log(`\n[회차 ${rounds.length}] ${name}`);
  const mark = (label, ok, detail = "") => {
    current.markers.push({ label, ok: ok === true, detail });
    console.log(`  ${ok === true ? "표지 있음" : "표지 없음"}  ${label}${detail ? `  (${detail})` : ""}`);
  };
  try {
    const facts = await body(mark);
    const normalize = await normalizer();
    current.stable = deepMap(facts.stable ?? null, normalize);
    current.racy = deepMap(facts.racy ?? null, normalize);
  } catch (error) {
    current.error = String(error?.stack ?? error);
    console.log(`  예외: ${current.error}`);
  }
  current.measured = current.error === null && current.markers.length > 0 && current.markers.every((marker) => marker.ok);
  if (current.stable !== null) console.log(`  결과: ${JSON.stringify(current.stable)}`);
  if (current.racy !== null) console.log(`  결과(회차마다 갈릴 수 있다): ${JSON.stringify(current.racy)}`);
  if (!current.measured) console.log("  이 회차는 측정으로 세지 않는다");
}

/** facts 에서 racyKeys 의 키를 racy 로, 나머지를 stable 로 나눈다. */
function split(facts, racyKeys) {
  const stable = {};
  const racy = {};
  for (const [key, value] of Object.entries(facts)) (racyKeys.includes(key) ? racy : stable)[key] = value;
  return { stable, racy: Object.keys(racy).length === 0 ? null : racy };
}

// ---------------------------------------------------------------------------------------------------------------------
// 브라우저 쪽 기록(CDP)과 관찰

const tagOf = (url) => URL.parse(url)?.searchParams.get("tag") ?? null;

function setCookieLines(event) {
  const key = Object.keys(event.headers).find((name) => name.toLowerCase() === "set-cookie");
  return key === undefined ? [] : event.headers[key].split("\n");
}

function newRecorder() {
  const requests = new Map();
  const responses = new Map();
  const arrived = [];
  let pages = 0;
  const find = (tag, method) => {
    for (const [key, request] of requests) {
      if (request.method === method && tagOf(request.url) === tag) return key;
    }
    return null;
  };
  return {
    async attach(context, page) {
      const head = `${pages}:`;
      pages += 1;
      const cdp = await context.newCDPSession(page);
      await cdp.send("Network.enable");
      cdp.on("Network.requestWillBeSent", (event) =>
        requests.set(head + event.requestId, { url: event.request.url, method: event.request.method }),
      );
      cdp.on("Network.responseReceivedExtraInfo", (event) => {
        responses.set(head + event.requestId, event);
        arrived.push(head + event.requestId);
      });
    },
    /** 브라우저가 받은 그 응답의 Set-Cookie 줄과 거절한 줄. 기록이 없으면 null. */
    async response(tag, method) {
      const deadline = Date.now() + SETTLE_MS;
      for (;;) {
        const key = find(tag, method);
        const event = key === null ? undefined : responses.get(key);
        if (event !== undefined) {
          return {
            setCookie: setCookieLines(event),
            blocked: (event.blockedCookies ?? []).map(
              (item) => `${item.cookieLine.split("=")[0]}: ${[...item.blockedReasons].sort().join(",")}`,
            ),
          };
        }
        if (Date.now() > deadline) return null;
        await sleep(50);
      }
    },
    /** 태그가 그 머리로 시작하는 응답 가운데 Set-Cookie 를 실은 것들의 줄(브라우저에 닿은 차례). */
    landed(head) {
      return arrived
        .filter((key) => tagOf(requests.get(key)?.url ?? "")?.startsWith(head) === true)
        .map((key) => setCookieLines(responses.get(key)))
        .filter((lines) => lines.length > 0);
    },
  };
}

let browser = null;

async function withContext(body) {
  const context = await browser.newContext();
  const recorder = newRecorder();
  const open = async (url) => {
    const page = await context.newPage();
    await recorder.attach(context, page);
    await page.goto(url, { waitUntil: "load" });
    return page;
  };
  try {
    return await body({ context, recorder, open });
  } finally {
    await context.close();
  }
}

function pageFetch(page, url, init) {
  return page.evaluate(
    async ([target, options]) => {
      try {
        const answer = await fetch(target, options);
        const text = await answer.text();
        let body = null;
        try {
          body = JSON.parse(text);
        } catch {
          body = text.slice(0, 200);
        }
        return { status: answer.status, body };
      } catch (error) {
        return { status: null, body: `${error.name}: ${error.message}` };
      }
    },
    [url, init ?? {}],
  );
}

/** 포트 A 의 페이지가 직접 부른다(브라우저의 same-origin 요청). */
const onA = (page, method, path, tag, body) =>
  pageFetch(page, `${path}?tag=${tag}&probe=${tag}.browser`, {
    method,
    ...(body === undefined ? {} : { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
  });
const loginOn = (page, tag) => onA(page, "POST", "/auth/login", tag, { account: ACCOUNT });

/** 브라우저 저장소의 로그인 쿠키. at 과 rt 는 대역의 이름표(없으면 null)다. */
async function jar(context) {
  const labels = await control(aosBase, "/__probe/labels");
  const cookies = await context.cookies();
  const labelOf = (name) => {
    const found = cookies.find((cookie) => cookie.name === name);
    return found === undefined ? null : (labels[found.value] ?? "모르는 값");
  };
  return {
    at: labelOf(AT),
    rt: labelOf(RT),
    rtExpires: cookies.find((cookie) => cookie.name === RT)?.expires ?? null,
    lines: cookies
      .map(
        (cookie) =>
          `${cookie.name}=${cookie.value}; domain=${cookie.domain}; path=${cookie.path}; httpOnly=${cookie.httpOnly}; ` +
          `secure=${cookie.secure}; sameSite=${cookie.sameSite}; ${cookie.expires === -1 ? "session" : "expires"}`,
      )
      .sort(),
  };
}

/** Set-Cookie 줄들에서 갱신용 번호의 이름표를 읽는다. */
async function refreshLabelIn(lines) {
  const labels = await control(aosBase, "/__probe/labels");
  const line = lines.find((item) => item.startsWith(`${RT}=`));
  if (line === undefined) return null;
  const value = line.split(";", 1)[0].slice(RT.length + 1);
  return labels[value] ?? (value === "" || value === '""' ? "(지움)" : "모르는 값");
}

// 설계 1: 중계가 스스로 갱신한다. 페이지는 요청을 그냥 보낸다.
const D1_BURST = async ([prefix, tag, count]) => {
  const one = async (index) => (await fetch(`${prefix}/d1/data?tag=${tag}-${index}`)).status;
  return { statuses: await Promise.all(Array.from({ length: count }, (_, index) => one(index))) };
};

// 설계 2: 화면이 갱신을 한 번 부른다. 401 을 받은 요청들은 탭 안에서 하나뿐인 갱신을 기다렸다가 다시 보낸다(ADR 0062 결정
// "로그인 상태"의 "화면은 요청이 401로 돌아오면 갱신을 한 번 부르고 그 요청을 다시 보낸다"). 함께 기다리는 것은 진행 중인
// 갱신뿐이다. 갱신이 끝난 뒤에 닿은 401 은 갱신을 새로 부른다. lateMs 를 주면 마지막 요청의 답을 중계가 그만큼 늦춰 그 경우를
// 만든다.
const D2_CLIENT = async ([prefix, tag, count, lateMs]) => {
  let refreshing = null;
  let refreshCalls = 0;
  let unauthorized = 0;
  const refreshOnce = () => {
    if (refreshing === null) {
      refreshCalls += 1;
      refreshing = fetch(`${prefix}/d2/refresh?tag=${tag}-refresh${refreshCalls}`, { method: "POST" })
        .then((answer) => answer.status)
        .finally(() => {
          refreshing = null;
        });
    }
    return refreshing;
  };
  const one = async (index) => {
    const late = lateMs !== undefined && lateMs !== null && index === count - 1 ? `&delay_ms=${lateMs}` : "";
    let answer = await fetch(`${prefix}/d2/data?tag=${tag}-${index}${late}`);
    if (answer.status === 401) {
      unauthorized += 1;
      if ((await refreshOnce()) === 200) answer = await fetch(`${prefix}/d2/data?tag=${tag}-${index}-retry`);
    }
    return answer.status;
  };
  const statuses = await Promise.all(Array.from({ length: count }, (_, index) => one(index)));
  return { statuses, refreshCalls, unauthorized };
};

// httpx2 는 위젯 관리 서버 대역의 `/x2/...` 길이다. 같은 대역이 Agent OS 를 httpx2 의 클라이언트로 부른다.
const RELAYS = {
  httpx: { via: "httpx", where: "포트 B", origin: () => bOrigin, prefix: "/api", log: syncWidget },
  fetch: { via: "fetch", where: "포트 C", origin: () => cOrigin, prefix: "/fetch", log: () => Promise.resolve(tester.log) },
  http: { via: "http", where: "포트 C", origin: () => cOrigin, prefix: "/http", log: () => Promise.resolve(tester.log) },
  httpx2: { via: "httpx2", where: "포트 B", origin: () => bOrigin, prefix: "/api/x2", log: syncWidget },
  // oaf 는 위젯 테스트 페이지 서버 대역의 `/oaf/...` 길이다. Agent OS 를 openapi-fetch 의 클라이언트로 부른다.
  oaf: { via: "oaf", where: "포트 C", origin: () => cOrigin, prefix: "/oaf", log: () => Promise.resolve(tester.log) },
};
// httpx2 와 oaf 는 뒤에 더한 길이라 맨 끝이다. 앞의 셋이 도는 차례(와 그 회차의 이름표)를 바꾸지 않는다.
const KINDS = ["httpx", "fetch", "http", "httpx2", "oaf"];
const NAMES = {
  httpx: "포트 B, httpx",
  fetch: "포트 C, Node fetch",
  http: "포트 C, node:http",
  httpx2: "포트 B, httpx2",
  oaf: "포트 C, openapi-fetch",
};

// ---------------------------------------------------------------------------------------------------------------------
// 대조: 대역의 동작(브라우저 없이)

async function controlRounds() {
  await round("대조 유예 0: 이미 바꾼 옛 번호가 다시 오면 그 로그인을 끊는다", async (mark) => {
    await resetStub(GRACES.none);
    const login = await direct("POST", "/auth/login", T("login"), {}, { account: ACCOUNT });
    const old = cookieFrom(login.setCookie);
    const first = await direct("POST", "/auth/refresh", T("first"), { cookie: old });
    const again = await direct("POST", "/auth/refresh", T("again"), { cookie: old });
    const state = await stubLogin();
    mark(
      "옛 번호(rt0)가 다시 오자 대역이 401 refresh_reuse 로 답하고 그 로그인을 끊었다",
      first.status === 200 && again.status === 401 && again.json?.reason === "refresh_reuse" && state.revoked === "refresh_reuse",
    );
    const next = await direct("POST", "/auth/refresh", T("next"), { cookie: cookieFrom(first.setCookie) });
    mark("끊긴 뒤에는 새 번호(rt1)도 401 session_revoked 다", next.status === 401 && next.json?.reason === "session_revoked");
    return {
      stable: {
        statuses: [login.status, first.status, again.status, next.status],
        loginLines: login.setCookie,
        refusedLines: again.setCookie,
      },
    };
  });

  await round("대조 유예 chain: 유예 안의 옛 번호는 받고 앞서 낸 번호를 옛 번호로 돌린다", async (mark) => {
    await resetStub(GRACES.chain);
    const login = await direct("POST", "/auth/login", T("login"), {}, { account: ACCOUNT });
    const old = cookieFrom(login.setCookie);
    const first = await direct("POST", "/auth/refresh", T("first"), { cookie: old });
    const again = await direct("POST", "/auth/refresh", T("again"), { cookie: old });
    const state = await stubLogin();
    mark(
      "유예 안에 다시 온 옛 번호(rt0)를 받아 rt2 를 냈고, 통하는 번호는 rt2 하나다",
      first.status === 200 && again.status === 200 && state.revoked === null && same(state.valid, ["rt2"]),
      `통하는 번호 ${JSON.stringify(state.valid)}`,
    );
    const viaDemoted = await direct("POST", "/auth/refresh", T("demoted"), { cookie: cookieFrom(first.setCookie) });
    mark("옛 번호로 돌린 rt1 도 유예 안에서는 받는다", viaDemoted.status === 200);
    await sleep(GRACE * 1000 + 300);
    const late = await direct("POST", "/auth/refresh", T("late"), { cookie: old });
    const after = await stubLogin();
    mark(
      "유예가 지난 옛 번호(rt0)가 오자 끊었다",
      late.status === 401 && late.json?.reason === "refresh_reuse" && after.revoked === "refresh_reuse",
    );
    return { stable: { statuses: [first.status, again.status, viaDemoted.status, late.status], validAfterGrace: state.valid } };
  });

  await round("대조 유예 family: 유예 안의 옛 번호는 받고 앞서 낸 번호도 그대로 통한다", async (mark) => {
    await resetStub(GRACES.family);
    const login = await direct("POST", "/auth/login", T("login"), {}, { account: ACCOUNT });
    const old = cookieFrom(login.setCookie);
    const first = await direct("POST", "/auth/refresh", T("first"), { cookie: old });
    const again = await direct("POST", "/auth/refresh", T("again"), { cookie: old });
    const state = await stubLogin();
    mark(
      "유예 안에 다시 온 옛 번호(rt0)를 받아 rt2 를 냈고, rt1 과 rt2 가 모두 통한다",
      first.status === 200 && again.status === 200 && state.revoked === null && same(state.valid, ["rt1", "rt2"]),
      `통하는 번호 ${JSON.stringify(state.valid)}`,
    );
    await sleep(GRACE * 1000 + 300);
    const viaFirst = await direct("POST", "/auth/refresh", T("via-first"), { cookie: cookieFrom(first.setCookie) });
    const viaSecond = await direct("POST", "/auth/refresh", T("via-second"), { cookie: cookieFrom(again.setCookie) });
    mark("유예가 지난 뒤에도 rt1 과 rt2 는 각각 받는다", viaFirst.status === 200 && viaSecond.status === 200);
    const late = await direct("POST", "/auth/refresh", T("late"), { cookie: old });
    const after = await stubLogin();
    mark(
      "유예가 지난 옛 번호(rt0)가 오자 끊었다",
      late.status === 401 && late.json?.reason === "refresh_reuse" && after.revoked === "refresh_reuse",
    );
    return { stable: { statuses: [first.status, again.status, viaFirst.status, viaSecond.status, late.status], validAfterGrace: state.valid } };
  });

  await round("대조 요청 출처 검사: 대역이 ADR 0062 의 규칙대로 가른다", async (mark) => {
    await resetStub(GRACES.none);
    const cases = [
      ["머리 없음", {}, "pass"],
      ["Sec-Fetch-Site: same-origin", { "Sec-Fetch-Site": "same-origin" }, "pass"],
      ["Sec-Fetch-Site: same-site", { "Sec-Fetch-Site": "same-site" }, "reject"],
      ["Sec-Fetch-Site: cross-site", { "Sec-Fetch-Site": "cross-site" }, "reject"],
      ["Sec-Fetch-Site: none", { "Sec-Fetch-Site": "none" }, "reject"],
      ["Origin 만", { Origin: "http://localhost:1" }, "reject"],
      ["Sec-Fetch-Site: same-origin 과 Origin", { "Sec-Fetch-Site": "same-origin", Origin: "http://localhost:1" }, "pass"],
      ["Sec-Fetch-Mode: cors 만", { "Sec-Fetch-Mode": "cors" }, "pass"],
    ];
    const verdicts = {};
    let asDesigned = 0;
    for (const [index, [name, headers, expected]] of cases.entries()) {
      const answer = await direct("GET", "/auth/me", T(`case${index}`), headers);
      await syncAos();
      const entry = aosBy(T(`case${index}`), "probe")[0];
      verdicts[name] = `${entry?.check ?? "기록 없음"} -> ${answer.status}`;
      const passed = entry?.check === "pass" && answer.status === 401 && answer.json?.reason === "access_missing";
      const rejected = entry?.check.startsWith("reject") && answer.status === 403 && answer.json?.reason === "origin_check";
      if (expected === "pass" ? passed : rejected) asDesigned += 1;
    }
    mark("여덟 경우 모두 대역이 규칙대로 받거나 403 origin_check 로 거절했다", asDesigned === cases.length, `${asDesigned}/${cases.length}`);
    return { stable: { verdicts } };
  });

  await round("대조 만료: JWT 는 수명이 지나면 401 access_expired 다", async (mark) => {
    await resetStub(GRACES.none);
    const login = await direct("POST", "/auth/login", T("login"), {}, { account: ACCOUNT });
    const cookie = cookieFrom(login.setCookie);
    const fresh = await direct("GET", "/auth/me", T("fresh"), { cookie });
    await sleep(EXPIRY_MS);
    const stale = await direct("GET", "/auth/me", T("stale"), { cookie });
    mark(
      "같은 JWT 가 만료 전에는 200, 수명이 지난 뒤에는 401 access_expired 다",
      fresh.status === 200 && fresh.json?.account === ACCOUNT && stale.status === 401 && stale.json?.reason === "access_expired",
    );
    return { stable: { statuses: [fresh.status, stale.status], staleLines: stale.setCookie } };
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// 1. 서버 사이 요청의 머리

async function clientRound() {
  await round("1. 서버 사이 요청이 스스로 붙이는 머리와 요청 출처 검사", async (mark) => {
    await resetStub(GRACES.none);
    return withContext(async ({ open }) => {
      const pageA = await open(`${aOrigin}/page`);
      const pagesByKind = {};
      for (const kind of KINDS) pagesByKind[kind] = await open(`${RELAYS[kind].origin()}${RELAYS[kind].prefix}/page`);
      const login = await loginOn(pageA, T("login"));
      const got = {};
      for (const kind of KINDS) {
        got[kind] = { me: await pageFetch(pagesByKind[kind], `${RELAYS[kind].prefix}/d2/data?tag=${T(`me-${kind}`)}`) };
      }
      for (const kind of KINDS) {
        got[kind].refresh = await pageFetch(pagesByKind[kind], `${RELAYS[kind].prefix}/d2/refresh?tag=${T(`refresh-${kind}`)}`, {
          method: "POST",
        });
      }
      await syncAos();
      mark("포트 A 의 페이지가 로그인했다", login.status === 200);
      const throughNext = (await syncWidget()).find((item) => item.tag === T("me-httpx"));
      mark(
        "포트 B 의 요청이 Next 중계를 지났다(위젯 관리 서버 대역이 받은 머리에 Next 의 프록시가 붙이는 x-forwarded-host 가 있다)",
        headerOf(throughNext, "x-forwarded-host") === `localhost:${ports.b}`,
        `${headerOf(throughNext, "x-forwarded-host")}`,
      );
      const stable = {};
      for (const kind of KINDS) {
        const relay = RELAYS[kind];
        const relayLog = await relay.log();
        stable[NAMES[kind]] = {};
        for (const [what, path] of [
          ["me", "/auth/me"],
          ["refresh", "/auth/refresh"],
        ]) {
          const tag = T(`${what}-${kind}`);
          const entry = aosBy(tag, relay.via)[0];
          const atRelay = relayLog.find((item) => item.tag === tag);
          mark(
            `${NAMES[kind]}: ${what === "me" ? "GET(지금 누구인지)" : "POST(갱신)"} 가 중계를 지나 Agent OS 대역에 닿았다`,
            entry !== undefined && entry.path === path && atRelay !== undefined && headerOf(atRelay, "sec-fetch-site") === "same-origin",
            entry === undefined ? "대역의 기록 없음" : `${entry.check} -> ${entry.status}`,
          );
          stable[NAMES[kind]][what] = {
            statusAtPage: got[kind][what].status,
            check: entry?.check ?? null,
            statusAtAgentOs: entry?.status ?? null,
            headersAtAgentOs: entry?.headers.map(([name, value]) => `${name}: ${value}`) ?? null,
            browserHeadersAtRelay: watched(atRelay),
          };
        }
      }
      return { stable };
    });
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// 2. Set-Cookie 가 중계를 지나는 모양

async function setCookieRound(kind) {
  const relay = RELAYS[kind];
  await round(`2. 갱신의 Set-Cookie 가 중계를 지나 브라우저에 닿는 모양 (${NAMES[kind]})`, async (mark) => {
    await resetStub(GRACES.none);
    return withContext(async ({ context, recorder, open }) => {
      const pageA = await open(`${aOrigin}/page`);
      const page = await open(`${relay.origin()}${relay.prefix}/page`);
      await loginOn(pageA, T("login"));
      const before = await jar(context);
      const sentAt = Date.now() / 1000;
      const got = await pageFetch(page, `${relay.prefix}/d2/refresh?tag=${T("refresh")}`, { method: "POST" });
      const atBrowser = await recorder.response(T("refresh"), "POST");
      await syncAos();
      const entry = aosBy(T("refresh"), relay.via)[0];
      const after = await jar(context);
      mark("갱신 요청이 중계에서 Agent OS 대역에 닿아 번호가 바뀌었다", entry?.outcome === "rotated" && headerOf(entry, "sec-fetch-site") === null);
      mark("Agent OS 대역이 Set-Cookie 두 줄을 냈다", entry?.setCookie.length === 2);
      mark("브라우저 쪽 기록(CDP)에 그 응답이 있다", atBrowser !== null);
      mark(
        "브라우저의 쿠키 값이 실제로 바뀌었다(at0·rt0 → at1·rt1)",
        before.at === "at0" && before.rt === "rt0" && after.at === "at1" && after.rt === "rt1",
        `${before.at}·${before.rt} → ${after.at}·${after.rt}`,
      );
      await control(aosBase, "/__probe/revoke", {});
      const refusedGot = await pageFetch(page, `${relay.prefix}/d2/refresh?tag=${T("refused")}`, { method: "POST" });
      const refusedAtBrowser = await recorder.response(T("refused"), "POST");
      await syncAos();
      const refusedEntry = aosBy(T("refused"), relay.via)[0];
      const cleared = await jar(context);
      mark(
        "끊긴 로그인의 갱신이 거절됐고 Agent OS 대역이 지우는 줄 둘을 냈다",
        refusedEntry?.reason === "session_revoked" &&
          refusedEntry.setCookie.length === 2 &&
          refusedEntry.setCookie.every((line) => line.includes("Max-Age=0")),
      );
      mark("지우는 줄이 닿기 전 브라우저에 쿠키 둘이 있었다", after.lines.length === 2);
      return {
        stable: {
          refreshed: {
            statusAtPage: got.status,
            emittedByAgentOs: entry?.setCookie ?? null,
            receivedByBrowser: atBrowser?.setCookie ?? null,
            identical: atBrowser !== null && entry !== undefined && same(atBrowser.setCookie, entry.setCookie),
            blockedByBrowser: atBrowser?.blocked ?? null,
            jarBefore: before.lines,
            jarAfter: after.lines,
            refreshExpiryFollowsMaxAge: after.rtExpires !== null && Math.abs(after.rtExpires - (sentAt + REFRESH_MAX_AGE)) < 15,
          },
          refused: {
            statusAtPage: refusedGot.status,
            emittedByAgentOs: refusedEntry?.setCookie ?? null,
            receivedByBrowser: refusedAtBrowser?.setCookie ?? null,
            identical:
              refusedAtBrowser !== null && refusedEntry !== undefined && same(refusedAtBrowser.setCookie, refusedEntry.setCookie),
            jarAfter: cleared.lines,
          },
        },
      };
    });
  });
}

async function naiveRound() {
  await round("2. 대조: Set-Cookie 를 한 값으로 합쳐 옮기는 중계 (포트 B, httpx)", async (mark) => {
    await resetStub(GRACES.none);
    return withContext(async ({ context, recorder, open }) => {
      const pageA = await open(`${aOrigin}/page`);
      const page = await open(`${bOrigin}/api/page`);
      await loginOn(pageA, T("login"));
      const before = await jar(context);
      const got = await pageFetch(page, `/api/naive/refresh?tag=${T("refresh")}`, { method: "POST" });
      const atBrowser = await recorder.response(T("refresh"), "POST");
      await syncAos();
      const entry = aosBy(T("refresh"), "httpx-naive")[0];
      const after = await jar(context);
      mark("갱신 요청이 중계에서 Agent OS 대역에 닿아 번호가 바뀌었고 대역이 두 줄을 냈다", entry?.outcome === "rotated" && entry.setCookie.length === 2);
      mark("브라우저 쪽 기록(CDP)에 그 응답이 있다", atBrowser !== null);
      mark("갱신 전 브라우저에 at0·rt0 이 있었다", before.at === "at0" && before.rt === "rt0");
      return {
        stable: {
          statusAtPage: got.status,
          emittedByAgentOs: entry?.setCookie ?? null,
          receivedByBrowser: atBrowser?.setCookie ?? null,
          identical: atBrowser !== null && entry !== undefined && same(atBrowser.setCookie, entry.setCookie),
          blockedByBrowser: atBrowser?.blocked ?? null,
          jarAfter: after.lines,
          browserHolds: { at: after.at, rt: after.rt },
          serverLastIssued: (await stubLogin()).lastIssued,
        },
      };
    });
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// 3. 흐름 전체

/** 중계를 거치는 요청 하나. 설계에 따라 걸음이 다르다. cookieTag 는 Set-Cookie 를 실어 오는 응답의 태그다. */
async function relayStep(page, relay, step, tag) {
  if (step === "gate") {
    const answer = await page.goto(`${relay.origin()}${relay.prefix}/gate?tag=${tag}`, { waitUntil: "load" });
    return { status: answer?.status() ?? null, cookieTag: tag, method: "GET" };
  }
  if (step === "d1") {
    const got = await pageFetch(page, `${relay.prefix}/d1/data?tag=${tag}`);
    return { status: got.status, cookieTag: tag, method: "GET" };
  }
  const got = await page.evaluate(D2_CLIENT, [relay.prefix, tag, 1]);
  return { status: got.statuses[0], cookieTag: `${tag}-refresh1`, method: "POST" };
}

const FLOWS = [
  { kind: "httpx", step: "d1", name: "포트 B, httpx, 설계 1(중계가 스스로 갱신)" },
  { kind: "httpx", step: "d2", name: "포트 B, httpx, 설계 2(화면이 갱신을 부름)" },
  { kind: "fetch", step: "d1", name: "포트 C, Node fetch, 설계 1" },
  { kind: "http", step: "d1", name: "포트 C, node:http, 설계 1" },
  { kind: "fetch", step: "gate", name: "포트 C, Node fetch, 주소로 문서 열기" },
  { kind: "http", step: "gate", name: "포트 C, node:http, 주소로 문서 열기" },
];

async function flowRound(flow) {
  const relay = RELAYS[flow.kind];
  await round(`3. 흐름 전체: ${flow.name}`, async (mark) => {
    await resetStub(GRACES.none);
    return withContext(async ({ context, recorder, open }) => {
      const pageA = await open(`${aOrigin}/page`);
      const page = await open(`${relay.origin()}${relay.prefix}/page`);
      const login = await loginOn(pageA, T("login"));
      const first = await relayStep(page, relay, flow.step, T("first"));
      await syncAos();
      mark(
        "포트 A 의 페이지가 로그인했다(대역이 same-origin 요청으로 받았다)",
        login.status === 200 && headerOf(aosBy(T("login"), "browser")[0], "sec-fetch-site") === "same-origin",
      );
      const firstMe = aosWith(T("first"), relay.via).filter((entry) => entry.path === "/auth/me");
      mark(
        "만료 전: 중계가 전한 쿠키(at0)에 대역이 200 을 냈다",
        first.status === 200 && firstMe.length === 1 && firstMe[0].status === 200 && firstMe[0].presented.at === "at0",
      );
      const before = await jar(context);
      await sleep(EXPIRY_MS);
      const second = await relayStep(page, relay, flow.step, T("second"));
      const atBrowser = await recorder.response(second.cookieTag, second.method);
      await syncAos();
      const inStep = aosWith(T("second"), relay.via);
      const expired = inStep.filter((entry) => entry.path === "/auth/me" && entry.reason === "access_expired");
      const refreshed = inStep.filter((entry) => entry.path === "/auth/refresh");
      mark("JWT 가 실제로 만료됐다(중계가 전한 at0 에 대역이 401 access_expired)", expired.length === 1 && expired[0].presented.at === "at0");
      mark(
        "갱신 요청이 중계에서 왔다(브라우저의 Sec-Fetch-Site 가 없고 rt0 이 rt1 로 바뀌었다)",
        refreshed.length === 1 &&
          refreshed[0].outcome === "rotated" &&
          refreshed[0].presented.rt === "rt0" &&
          headerOf(refreshed[0], "sec-fetch-site") === null,
      );
      const after = await jar(context);
      mark(
        "브라우저의 쿠키 값이 실제로 바뀌었다(at0·rt0 → at1·rt1)",
        before.at === "at0" && before.rt === "rt0" && after.at === "at1" && after.rt === "rt1",
        `${before.at}·${before.rt} → ${after.at}·${after.rt}`,
      );
      const aMe = await onA(pageA, "GET", "/auth/me", T("a-me"));
      await syncAos();
      mark("포트 A 의 요청이 중계가 받아 온 쿠키(at1)를 실었다", aosBy(T("a-me"), "browser")[0]?.presented.at === "at1");
      await sleep(EXPIRY_MS);
      const aExpired = await onA(pageA, "GET", "/auth/me", T("a-expired"));
      const aRefresh = await onA(pageA, "POST", "/auth/refresh", T("a-refresh"));
      const aAgain = await onA(pageA, "GET", "/auth/me", T("a-again"));
      const third = await relayStep(page, relay, flow.step, T("third"));
      await syncAos();
      const aRefreshEntry = aosBy(T("a-refresh"), "browser")[0];
      mark(
        "포트 A 가 다시 만료된 뒤 중계가 받아 온 번호(rt1)로 직접 갱신했다",
        aosBy(T("a-expired"), "browser")[0]?.reason === "access_expired" && aRefreshEntry?.presented.rt === "rt1",
      );
      const thirdMe = aosWith(T("third"), relay.via).filter((entry) => entry.path === "/auth/me");
      mark("중계의 다음 요청이 포트 A 가 갱신한 쿠키(at2)를 전했다", thirdMe.length === 1 && thirdMe[0].presented.at === "at2");
      return {
        stable: {
          statuses: {
            login: login.status,
            relayBeforeExpiry: first.status,
            relayAfterExpiry: second.status,
            portAWithRelayedCookie: aMe.status,
            portAExpired: aExpired.status,
            portARefresh: aRefresh.status,
            portAAfterOwnRefresh: aAgain.status,
            relayWithPortACookie: third.status,
          },
          refreshOutcomes: { viaRelay: refreshed.map((entry) => entry.outcome), fromPortA: aRefreshEntry?.outcome ?? null },
          setCookieIdentical: atBrowser !== null && refreshed.length === 1 && same(atBrowser.setCookie, refreshed[0].setCookie),
          blockedByBrowser: atBrowser?.blocked ?? null,
          loginRevoked: (await stubLogin()).revoked,
        },
      };
    });
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// 4. 동시에 여러 요청이 갱신을 일으킬 때

// 설계 2 의 늦은 401. 갱신 하나가 끝나고도 남는 시간이고 JWT 의 수명보다 짧다.
const LATE_MS = 800;

// 중계가 Agent OS 에 보낸 요청이라는 것을 가르는 User-Agent. 브라우저의 것과 겹치지 않는다(회차 1 이 잰 머리 그대로다).
const RELAY_AGENTS = {
  httpx: { word: "User-Agent 가 httpx 다", holds: (agent) => (agent ?? "").startsWith("python-httpx/") },
  fetch: { word: "User-Agent 가 node 다", holds: (agent) => agent === "node" },
  http: { word: "User-Agent 가 없다", holds: (agent) => agent === null },
  httpx2: { word: "User-Agent 가 httpx2 다", holds: (agent) => (agent ?? "").startsWith("python-httpx2/") },
};

// relay 는 요청 넷을 보내는 페이지의 자리다. 기본은 포트 B(Next 중계와 httpx)이고, 포트 C 는 설계 2 만 잰다.
async function burstRound({ design, grace, forced, late = false, relay = RELAYS.httpx, name, racyKeys }) {
  const { where } = relay;
  const agent = RELAY_AGENTS[relay.via];
  await round(name, async (mark) => {
    await resetStub({ ...GRACES[grace], ...(forced ? { refresh_delays_ms: [600, 400, 200, 0] } : {}) });
    return withContext(async ({ context, recorder, open }) => {
      const pageA = await open(`${aOrigin}/page`);
      const pageB = await open(`${relay.origin()}${relay.prefix}/page`);
      const login = await loginOn(pageA, T("login"));
      const first = await pageFetch(pageB, `${relay.prefix}/d2/data?tag=${T("first")}`);
      mark(`만료 전: 포트 A 에서 로그인했고 ${where} 의 요청이 200 이다`, login.status === 200 && first.status === 200);
      await sleep(EXPIRY_MS);
      const burst = await pageB.evaluate(design === "d1" ? D1_BURST : D2_CLIENT, [relay.prefix, T("burst"), 4, late ? LATE_MS : null]);
      await syncAos();
      const seen = aosWith(T("burst"), relay.via);
      const expired = seen.filter((entry) => entry.path === "/auth/me" && entry.reason === "access_expired");
      const refreshes = seen.filter((entry) => entry.path === "/auth/refresh");
      mark("JWT 가 실제로 만료됐다(요청 넷 모두에서 대역이 401 access_expired)", expired.length === 4, `${expired.length}/4`);
      mark(
        `갱신 요청이 모두 중계에서 왔다(Sec-Fetch-Site 가 없고 ${agent.word})`,
        refreshes.length >= 1 &&
          refreshes.every((entry) => headerOf(entry, "sec-fetch-site") === null && agent.holds(headerOf(entry, "user-agent"))),
        `갱신 ${refreshes.length}개`,
      );
      const sameNumber = refreshes.filter((entry) => entry.presented.rt === "rt0").length;
      if (design === "d1") {
        mark("동시 갱신이 실제로 났다(같은 번호 rt0 을 든 갱신이 둘 이상 대역에 닿았다)", sameNumber >= 2, `rt0 을 든 갱신 ${sameNumber}개`);
      } else {
        mark("요청 넷이 모두 401 을 받았다(넷 다 화면이 갱신을 부를 까닭이 있었다)", burst.unauthorized === 4, `401 ${burst.unauthorized}개`);
        if (late) {
          mark(
            "늦은 401 이 실제로 갱신이 끝난 뒤에 닿았다(화면이 갱신을 두 번 불렀고 둘째가 든 번호가 첫 갱신이 낸 rt1 이다)",
            burst.refreshCalls === 2 && refreshes.length === 2 && refreshes[1].presented.rt === "rt1",
            `갱신 ${burst.refreshCalls}번, 든 번호 ${refreshes.map((entry) => entry.presented.rt).join(", ")}`,
          );
        }
      }
      const state = await stubLogin();
      const cookies = await jar(context);
      const landed = [];
      for (const lines of recorder.landed(T("burst"))) landed.push(await refreshLabelIn(lines));
      if (forced) mark("응답의 차례가 실제로 뒤집혔다(브라우저에 남은 번호가 대역이 먼저 낸 rt1 이다)", cookies.rt === "rt1", `남은 번호 ${cookies.rt}`);
      await sleep(EXPIRY_MS);
      const follow =
        design === "d1"
          ? (await pageFetch(pageB, `${relay.prefix}/d1/data?tag=${T("follow")}`)).status
          : (await pageB.evaluate(D2_CLIENT, [relay.prefix, T("follow"), 1])).statuses[0];
      await syncAos();
      const followSeen = aosWith(T("follow"), relay.via);
      mark(
        "다음 만료 뒤의 요청이 대역에 닿았고 그때 JWT 는 통하지 않았다",
        followSeen.some((entry) => entry.path === "/auth/me" && entry.status === 401),
      );
      const followRefresh = followSeen.find((entry) => entry.path === "/auth/refresh");
      const finalState = await stubLogin();
      return split(
        {
          refreshRequestsAtAgentOs: refreshes.length,
          refreshOutcomesInArrivalOrder: refreshes.map((entry) => entry.outcome ?? entry.reason),
          numbersPresented: refreshes.map((entry) => entry.presented.rt),
          // 갱신의 수가 회차마다 갈려도 같아야 하는 것. 판정의 가짓수와, 같은 번호를 든 갱신이 둘 이상이었는가.
          refreshOutcomeKinds: [...new Set(refreshes.map((entry) => entry.outcome ?? entry.reason))].sort(),
          sameNumberPresentedTwice: new Set(refreshes.map((entry) => entry.presented.rt)).size !== refreshes.length,
          statusesAtPageSorted: [...burst.statuses].sort(),
          pageRefreshCalls: burst.refreshCalls ?? null,
          revokedAfterBurst: state.revoked,
          validNumbersAfterBurst: state.revoked === null ? state.valid : [],
          serverLastIssued: state.lastIssued,
          statusesAtPageByIndex: burst.statuses,
          setCookieLandedInOrder: landed,
          browserHoldsAfterBurst: { at: cookies.at, rt: cookies.rt },
          browserHoldsValidNumber: cookies.rt !== null && state.revoked === null && state.valid.includes(cookies.rt),
          browserHoldsLastIssued: cookies.rt === state.lastIssued,
          followStatusAtPage: follow,
          followRefreshOutcome: followRefresh === undefined ? null : (followRefresh.outcome ?? followRefresh.reason),
          revokedAtEnd: finalState.revoked,
          aliveAfterNextExpiry: follow === 200 && finalState.revoked === null,
        },
        racyKeys,
      );
    });
  });
}

async function twoTabRound({ grace, forced, name, racyKeys }) {
  await round(name, async (mark) => {
    // 탭 둘의 갱신이 겹치게 응답을 잡아 둔다. 번호를 바꾸는 일은 닿은 차례대로 바로 하고 응답만 늦춘다.
    await resetStub({ ...GRACES[grace], ...(forced ? { refresh_delays_ms: [400, 0] } : { hold_ms: 150 }) });
    return withContext(async ({ context, open }) => {
      const pageA = await open(`${aOrigin}/page`);
      const pageB = await open(`${bOrigin}/api/page`);
      const login = await loginOn(pageA, T("login"));
      const first = await pageFetch(pageB, `/api/d2/data?tag=${T("first")}`);
      mark("만료 전: 포트 A 에서 로그인했고 포트 B 의 요청이 200 이다", login.status === 200 && first.status === 200);
      await sleep(EXPIRY_MS);
      const stale = await onA(pageA, "GET", "/auth/me", T("stale"));
      const [fromA, fromB] = await Promise.all([
        onA(pageA, "POST", "/auth/refresh", T("tab-a")),
        pageFetch(pageB, `/api/d2/refresh?tag=${T("tab-b")}`, { method: "POST" }),
      ]);
      await syncAos();
      const a = aosBy(T("tab-a"), "browser")[0];
      const b = aosBy(T("tab-b"), "httpx")[0];
      mark("JWT 가 실제로 만료됐다(포트 A 의 요청에 대역이 401 access_expired)", stale.status === 401 && aosBy(T("stale"), "browser")[0]?.reason === "access_expired");
      mark(
        "갱신 둘이 대역에 닿았다. 하나는 브라우저가 직접(same-origin), 하나는 중계가(Sec-Fetch-Site 없음)",
        headerOf(a, "sec-fetch-site") === "same-origin" && b !== undefined && headerOf(b, "sec-fetch-site") === null,
      );
      mark("동시 갱신이 실제로 났다(둘 다 같은 번호 rt0 을 들었다)", a?.presented.rt === "rt0" && b?.presented.rt === "rt0", `${a?.presented.rt}, ${b?.presented.rt}`);
      const state = await stubLogin();
      const cookies = await jar(context);
      if (forced) mark("응답의 차례가 실제로 뒤집혔다(브라우저에 남은 번호가 대역이 먼저 낸 rt1 이다)", cookies.rt === "rt1", `남은 번호 ${cookies.rt}`);
      await sleep(EXPIRY_MS);
      const aStale = await onA(pageA, "GET", "/auth/me", T("follow-a-me"));
      const aRefresh = await onA(pageA, "POST", "/auth/refresh", T("follow-a-refresh"));
      const bAfter = await pageFetch(pageB, `/api/d2/data?tag=${T("follow-b")}`);
      await syncAos();
      mark("다음 만료 뒤의 요청이 대역에 닿았고 그때 JWT 는 통하지 않았다", aStale.status === 401 && aosBy(T("follow-a-me"), "browser")[0] !== undefined);
      const followRefresh = aosBy(T("follow-a-refresh"), "browser")[0];
      const finalState = await stubLogin();
      const arrival = [a, b].filter((entry) => entry !== undefined).sort((left, right) => left.seq - right.seq);
      return split(
        {
          refreshOutcomesInArrivalOrder: arrival.map((entry) => entry.outcome ?? entry.reason),
          revokedAfterBurst: state.revoked,
          validNumbersAfterBurst: state.revoked === null ? state.valid : [],
          serverLastIssued: state.lastIssued,
          arrivedFirst: arrival[0] === a ? "포트 A(직접)" : "포트 B(중계)",
          statusesAtPage: { portA: fromA.status, portB: fromB.status },
          browserHoldsAfterBurst: { at: cookies.at, rt: cookies.rt },
          browserHoldsValidNumber: cookies.rt !== null && state.revoked === null && state.valid.includes(cookies.rt),
          browserHoldsLastIssued: cookies.rt === state.lastIssued,
          followStatuses: { portARefresh: aRefresh.status, portBData: bAfter.status },
          followRefreshOutcome: followRefresh === undefined ? null : (followRefresh.outcome ?? followRefresh.reason),
          revokedAtEnd: finalState.revoked,
          aliveAfterNextExpiry: aRefresh.status === 200 && bAfter.status === 200 && finalState.revoked === null,
        },
        racyKeys,
      );
    });
  });
}

// 응답이 닿는 차례에 달린 값들. 갈래마다 어느 값이 그런지 다르다.
const BROWSER_SIDE = ["setCookieLandedInOrder", "browserHoldsAfterBurst", "browserHoldsLastIssued", "arrivedFirst", "statusesAtPage"];
const FOLLOW_SIDE = ["followStatusAtPage", "followStatuses", "followRefreshOutcome", "revokedAtEnd", "aliveAfterNextExpiry"];
const D2_COUNT_SIDE = [
  "refreshRequestsAtAgentOs",
  "refreshOutcomesInArrivalOrder",
  "numbersPresented",
  "pageRefreshCalls",
  "validNumbersAfterBurst",
  "serverLastIssued",
  "setCookieLandedInOrder",
  "browserHoldsAfterBurst",
];

async function concurrencyRounds() {
  // 설계 1, 유예 0: 끊기는 것은 차례와 무관하다. 브라우저에 무엇이 남는지와 그 뒤의 거절 까닭은 차례에 달렸다.
  await burstRound({
    design: "d1",
    grace: "none",
    forced: false,
    name: "4. 요청 넷 동시, 설계 1(중계가 스스로 갱신), 유예 0",
    racyKeys: [...BROWSER_SIDE, "statusesAtPageByIndex", "followRefreshOutcome"],
  });
  for (let index = 1; index <= ROUNDS; index += 1) {
    await burstRound({
      design: "d1",
      grace: "chain",
      forced: false,
      name: `4. 요청 넷 동시, 설계 1, 유예 chain, 응답의 차례를 건드리지 않음 ${index}/${ROUNDS}`,
      racyKeys: [...BROWSER_SIDE, ...FOLLOW_SIDE, "statusesAtPageByIndex", "browserHoldsValidNumber"],
    });
  }
  await burstRound({
    design: "d1",
    grace: "chain",
    forced: true,
    name: "4. 요청 넷 동시, 설계 1, 유예 chain, 응답의 차례를 뒤집음",
    racyKeys: ["statusesAtPageByIndex"],
  });
  await burstRound({
    design: "d1",
    grace: "family",
    forced: false,
    name: "4. 요청 넷 동시, 설계 1, 유예 family, 응답의 차례를 건드리지 않음",
    racyKeys: [...BROWSER_SIDE, "statusesAtPageByIndex"],
  });
  await burstRound({
    design: "d1",
    grace: "family",
    forced: true,
    name: "4. 요청 넷 동시, 설계 1, 유예 family, 응답의 차례를 뒤집음",
    racyKeys: ["statusesAtPageByIndex"],
  });
  for (const grace of ["none", "chain", "family"]) {
    await burstRound({
      design: "d2",
      grace,
      forced: false,
      name: `4. 요청 넷 동시, 설계 2(화면이 갱신을 한 번 부름), 유예 ${grace === "none" ? "0" : grace}`,
      // 화면이 함께 기다리는 것은 진행 중인 갱신뿐이라, 401 하나가 갱신이 끝난 뒤에 닿으면 갱신이 둘이 된다(dev 모드의 한
      // 회차에서 났다). 그래서 갱신의 수와 번호는 회차마다 갈릴 수 있는 값이다. 그 경우는 아래 회차가 일부러 만든다.
      racyKeys: D2_COUNT_SIDE,
    });
  }
  await burstRound({
    design: "d2",
    grace: "none",
    forced: false,
    late: true,
    name: "4. 요청 넷 동시, 설계 2, 유예 0, 401 하나가 갱신이 끝난 뒤에 닿음",
    racyKeys: [],
  });
  // 포트 C(위젯 테스트 페이지 서버 대역)의 설계 2 와, 포트 B 의 중계가 httpx2 로 부르는 설계 2. 페이지의 스크립트와 표지는
  // 포트 B(httpx)의 설계 2 회차와 같다.
  for (const kind of ["fetch", "http", "httpx2"]) {
    await burstRound({
      design: "d2",
      grace: "none",
      forced: false,
      relay: RELAYS[kind],
      name: `4. 요청 넷 동시, 설계 2(화면이 갱신을 한 번 부름), 유예 0 (${NAMES[kind]})`,
      racyKeys: D2_COUNT_SIDE,
    });
  }
  await twoTabRound({
    grace: "none",
    forced: false,
    name: "4. 탭 둘이 동시에 갱신(포트 A 직접, 포트 B 중계), 유예 0",
    racyKeys: [...BROWSER_SIDE, "followRefreshOutcome"],
  });
  for (const grace of ["chain", "family"]) {
    await twoTabRound({
      grace,
      forced: false,
      name: `4. 탭 둘이 동시에 갱신, 유예 ${grace}, 응답을 같은 시간만큼 잡아 둠`,
      racyKeys: grace === "chain" ? [...BROWSER_SIDE, ...FOLLOW_SIDE, "browserHoldsValidNumber"] : BROWSER_SIDE,
    });
    await twoTabRound({
      grace,
      forced: true,
      name: `4. 탭 둘이 동시에 갱신, 유예 ${grace}, 응답의 차례를 뒤집음`,
      racyKeys: ["arrivedFirst", "statusesAtPage"],
    });
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// 5. 대조: 브라우저의 머리를 그대로 전하는 중계

async function rawRound() {
  await round("5. 대조: 브라우저가 보낸 머리를 그대로 전하는 중계와 Cookie 만 전하는 중계", async (mark) => {
    await resetStub(GRACES.none);
    return withContext(async ({ open }) => {
      const pageA = await open(`${aOrigin}/page`);
      const cases = {};
      const observe = async (name, { tag, via, relayLog, site, forwarded }) => {
        await syncAos();
        const atRelay = watched((await relayLog()).find((item) => item.tag === tag));
        const entry = aosBy(tag, via)[0];
        const atAgentOs = watched(entry);
        mark(`${name}: 브라우저가 중계에 Sec-Fetch-Site: ${site} 를 보냈다`, atRelay?.["sec-fetch-site"] === site, `${atRelay?.["sec-fetch-site"]}`);
        if (forwarded) {
          mark(`${name}: 그 머리가 Agent OS 대역에 그대로 닿았다`, atAgentOs?.["sec-fetch-site"] === site);
        } else {
          mark(
            `${name}: Agent OS 대역에 닿은 요청에 브라우저의 머리가 없고 쿠키 둘은 있다`,
            atAgentOs !== null &&
              atAgentOs["sec-fetch-site"] === null &&
              atAgentOs.origin === null &&
              atAgentOs.referer === null &&
              atAgentOs.cookieNames.length === 2,
          );
        }
        cases[name] = { browserHeadersAtRelay: atRelay, headersAtAgentOs: atAgentOs, check: entry?.check ?? null, statusAtAgentOs: entry?.status ?? null };
      };
      const fresh = async (name) => {
        const login = await loginOn(pageA, T(`login-${name}`));
        if (login.status !== 200) throw new Error(`로그인이 ${login.status} 로 끝났다`);
      };
      const viaLink = async (target) => {
        const page = await open(`${bOrigin}/api/page`);
        await page.evaluate((href) => {
          const link = document.createElement("a");
          link.id = "l";
          link.href = href;
          link.textContent = "테스트";
          document.body.append(link);
        }, target);
        const arrived = page.waitForURL(target, { waitUntil: "load" });
        await page.click("#l");
        await arrived;
      };

      await fresh("typed-cookie");
      await open(`${bOrigin}/api/d2/data?tag=${T("typed-cookie")}`);
      await observe("주소창으로 포트 B 의 경로 열기, Cookie 만", { tag: T("typed-cookie"), via: "httpx", relayLog: syncWidget, site: "none", forwarded: false });

      await fresh("typed-raw");
      await open(`${bOrigin}/api/raw/data?tag=${T("typed-raw")}`);
      await observe("주소창으로 포트 B 의 경로 열기, 그대로", { tag: T("typed-raw"), via: "httpx-raw", relayLog: syncWidget, site: "none", forwarded: true });

      await fresh("fetch-raw");
      const pageB = await open(`${bOrigin}/api/page`);
      await pageFetch(pageB, `/api/raw/data?tag=${T("fetch-get-raw")}`);
      await observe("포트 B 페이지의 fetch GET, 그대로", { tag: T("fetch-get-raw"), via: "httpx-raw", relayLog: syncWidget, site: "same-origin", forwarded: true });
      await pageFetch(pageB, `/api/raw/refresh?tag=${T("fetch-post-raw")}`, { method: "POST" });
      await observe("포트 B 페이지의 fetch POST, 그대로", { tag: T("fetch-post-raw"), via: "httpx-raw", relayLog: syncWidget, site: "same-origin", forwarded: true });

      await fresh("link-cookie");
      await viaLink(`${cOrigin}/http/gate?tag=${T("link-cookie")}`);
      await observe("포트 B 의 링크로 포트 C 의 문서 열기, Cookie 만", { tag: T("link-cookie"), via: "http", relayLog: () => Promise.resolve(tester.log), site: "same-site", forwarded: false });

      await fresh("link-raw");
      await viaLink(`${cOrigin}/http/raw/gate?tag=${T("link-raw")}`);
      await observe("포트 B 의 링크로 포트 C 의 문서 열기, 그대로", { tag: T("link-raw"), via: "http-raw", relayLog: () => Promise.resolve(tester.log), site: "same-site", forwarded: true });

      return { stable: cases };
    });
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// 덤: httpx 의 함께 쓰는 클라이언트가 쿠키를 들고 있는가. 쿠키 통에 Secure 없는 쿠키를 남기므로 맨 끝에 돈다.

// key 는 위젯 관리 서버 대역의 클라이언트 이름이고 prefix 는 그 클라이언트를 고르는 경로의 첫 마디다. 통은 클라이언트마다 따로다.
const JAR_CLIENTS = [
  { key: "httpx", prefix: "", name: "덤: httpx 의 함께 쓰는 클라이언트가 Set-Cookie 로 받은 쿠키를 들고 있는가" },
  { key: "httpx2", prefix: "/x2", name: "덤: httpx2 의 함께 쓰는 클라이언트가 Set-Cookie 로 받은 쿠키를 들고 있는가" },
  { key: "httpx2-nojar", prefix: "/x2n", name: "덤 대조: 쿠키를 받지 않는 통을 준 httpx2 클라이언트는 쿠키를 들지도 싣지도 않는다" },
];

async function clientJarRounds() {
  for (const client of JAR_CLIENTS) await clientJarRound(client);
}

async function clientJarRound({ key, prefix, name }) {
  const jarOf = async () => (await control(widgetBase, "/__probe/state")).jars[key];
  await round(name, async (mark) => {
    await resetStub(GRACES.none);
    const login = await direct("POST", "/auth/login", T("login"), {}, { account: ACCOUNT });
    const refreshed = await rawRequest("POST", `${widgetBase}${prefix}/d2/refresh?tag=${T("refresh")}`, { cookie: cookieFrom(login.setCookie) });
    await syncAos();
    const refreshEntry = aosBy(T("refresh"), key)[0];
    mark(
      "이 회차에 함께 쓰는 클라이언트가 Set-Cookie 두 줄이 든 갱신 응답을 받았다",
      refreshed.status === 200 && refreshEntry?.outcome === "rotated" && refreshEntry.setCookie.length === 2,
    );
    const held = await jarOf();
    await rawRequest("GET", `${widgetBase}${prefix}/d2/data?tag=${T("bare")}`);
    await syncAos();
    const bare = aosBy(T("bare"), key)[0];
    mark("쿠키 없이 온 요청이 중계를 지나 Agent OS 대역에 닿았다", bare !== undefined && bare.path === "/auth/me");
    await rawRequest("GET", `${widgetBase}${prefix}/plain-cookie?tag=${T("plain")}`);
    await rawRequest("GET", `${widgetBase}${prefix}/d2/data?tag=${T("bare-after-plain")}`);
    // 쿠키를 싣고 온 요청에는 통의 쿠키가 섞이는가.
    await rawRequest("GET", `${widgetBase}${prefix}/d2/data?tag=${T("own-after-plain")}`, { cookie: cookieFrom(refreshed.setCookie) });
    await syncAos();
    // /__probe/ 아래는 Agent OS 대역의 기록에 남지 않는다. 그 응답을 받았다는 것은 중계의 호출 기록으로 본다.
    const plainCall = (await syncWidget()).find((item) => item.tag === T("plain"))?.calls[0];
    const afterPlain = aosBy(T("bare-after-plain"), key)[0];
    mark(
      "대조: 함께 쓰는 클라이언트가 Secure 없는 쿠키가 든 응답을 받았고, 그 뒤 쿠키 없이 온 요청이 대역에 닿았다",
      plainCall?.setCookie.some((line) => line.startsWith("probe_plain=")) === true && afterPlain !== undefined,
    );
    return {
      stable: {
        clientJarAfterRefresh: held.map((cookie) => `${cookie.name}; domain=${cookie.domain}; path=${cookie.path}; secure=${cookie.secure}`).sort(),
        cookieSentForBareRequest: headerOf(bare, "cookie"),
        statusForBareRequest: bare?.status ?? null,
        clientJarAfterPlain: (await jarOf()).map((cookie) => `${cookie.name}; secure=${cookie.secure}`).sort(),
        cookieSentForBareRequestAfterPlain: headerOf(afterPlain, "cookie"),
        cookieNamesSentForRequestWithOwnCookieAfterPlain: watched(aosBy(T("own-after-plain"), key)[0])?.cookieNames ?? null,
      },
    };
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// openapi-fetch 로 부르는 갈래에만 있는 회차 둘. 머리(1)와 Set-Cookie(2)는 KINDS 에 든 oaf 가 앞의 회차에서 잰다.

/** 위젯 테스트 페이지 서버 대역을 프로브가 직접 부를 때의 주소(브라우저를 거치지 않는다). */
const testerBase = () => `http://127.0.0.1:${ports.c}`;

// 클라이언트가 받은 쿠키를 기억하는가. httpx 의 쿠키 통 회차와 같은 걸음이다. 로그인 쿠키는 Secure 라 http 상류에서는 통이
// 있어도 실리지 않으므로, Secure 없는 쿠키의 걸음이 "통이 없다"와 "통은 있는데 싣지 않았다"를 가른다.
async function openapiJarRound() {
  await round("6. openapi-fetch 의 함께 쓰는 클라이언트는 받은 쿠키를 다음 요청에 싣지 않는다", async (mark) => {
    await resetStub(GRACES.none);
    const login = await direct("POST", "/auth/login", T("login"), {}, { account: ACCOUNT });
    const refreshed = await rawRequest("POST", `${testerBase()}/oaf/d2/refresh?tag=${T("refresh")}`, { cookie: cookieFrom(login.setCookie) });
    await syncAos();
    const refreshEntry = aosBy(T("refresh"), "oaf")[0];
    mark(
      "이 회차에 함께 쓰는 클라이언트가 Set-Cookie 두 줄이 든 갱신 응답을 받았다",
      refreshed.status === 200 && refreshEntry?.outcome === "rotated" && refreshEntry.setCookie.length === 2 && refreshed.setCookie.length === 2,
    );
    await rawRequest("GET", `${testerBase()}/oaf/d2/data?tag=${T("bare")}`);
    await syncAos();
    const bare = aosBy(T("bare"), "oaf")[0];
    mark("쿠키 없이 온 요청이 중계를 지나 Agent OS 대역에 닿았다", bare !== undefined && bare.path === "/auth/me");
    await rawRequest("GET", `${testerBase()}/oaf/plain-cookie?tag=${T("plain")}`);
    await rawRequest("GET", `${testerBase()}/oaf/d2/data?tag=${T("bare-after-plain")}`);
    await syncAos();
    const plainCall = tester.log.find((item) => item.tag === T("plain"))?.calls[0];
    const afterPlain = aosBy(T("bare-after-plain"), "oaf")[0];
    mark(
      "갈래: 같은 클라이언트가 Secure 없는 쿠키가 든 응답을 받았고, 그 뒤 쿠키 없이 온 요청이 대역에 닿았다",
      plainCall?.setCookie.some((line) => line.startsWith("probe_plain=")) === true && afterPlain !== undefined,
    );
    return {
      stable: {
        cookieSentForBareRequest: headerOf(bare, "cookie"),
        statusForBareRequest: bare?.status ?? null,
        cookieSentForBareRequestAfterPlain: headerOf(afterPlain, "cookie"),
      },
    };
  });
}

// 답을 늦추는 대역에 AbortSignal.timeout 을 건 호출. 대역은 갱신의 응답을 HOLD_MS 만큼 잡아 둔다. 긴 제한 시간의 호출이
// 답을 받는다는 것이 양성 대조이고, 견주려고 전역 fetch 를 직접 부르는 길도 같은 걸음으로 잰다.
const HOLD_MS = 1200;
const SHORT_MS = 300;
const LONG_MS = 5000;

async function openapiTimeoutRound() {
  await round("6. openapi-fetch 호출에 AbortSignal.timeout 을 넘겼을 때", async (mark) => {
    await resetStub({ ...GRACES.none, hold_ms: HOLD_MS });
    const stable = {};
    const racy = {};
    for (const kind of ["oaf", "fetch"]) {
      // 짧은 호출은 대역의 번호만 바꾸고 끊기므로 길마다 새로 로그인한다.
      const login = await direct("POST", "/auth/login", T(`login-${kind}`), {}, { account: ACCOUNT });
      const long = await rawRequest("POST", `${testerBase()}/${kind}/timeout/refresh?tag=${T(`long-${kind}`)}&timeout_ms=${LONG_MS}`, {
        cookie: cookieFrom(login.setCookie),
      });
      mark(
        `${NAMES[kind]}: 대역이 답을 ${HOLD_MS}ms 잡아 두었고, 제한 시간 ${LONG_MS}ms 의 호출은 답을 받았다`,
        long.status === 200 && long.json?.threw === false && long.json.elapsedMs >= HOLD_MS - 50,
        `${long.status}, ${long.json?.elapsedMs}ms`,
      );
      const short = await rawRequest("POST", `${testerBase()}/${kind}/timeout/refresh?tag=${T(`short-${kind}`)}&timeout_ms=${SHORT_MS}`, {
        cookie: cookieFrom(long.setCookie),
      });
      await syncAos();
      const reached = aosBy(T(`short-${kind}`), kind)[0];
      mark(
        `${NAMES[kind]}: 제한 시간 ${SHORT_MS}ms 의 호출이 대역에 닿았고 제한 시간에 끊겼다(던져진 것의 이름이 TimeoutError 이고 걸린 시간이 제한 시간과 잡아 둔 시간 사이다)`,
        reached !== undefined &&
          reached.path === "/auth/refresh" &&
          short.json?.threw === true &&
          short.json.error.name === "TimeoutError" &&
          short.json.elapsedMs >= SHORT_MS - 20 &&
          short.json.elapsedMs < HOLD_MS,
        `${short.json?.error?.name}, ${short.json?.elapsedMs}ms`,
      );
      stable[NAMES[kind]] = {
        longTimeout: { statusAtRelay: long.status, threw: long.json?.threw ?? null },
        shortTimeout: { threw: short.json?.threw ?? null, thrown: short.json?.error ?? null },
      };
      racy[NAMES[kind]] = { longElapsedMs: long.json?.elapsedMs ?? null, shortElapsedMs: short.json?.elapsedMs ?? null };
    }
    return { stable, racy };
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// 견줌

function differences(left, right, path = "") {
  if (same(left, right)) return [];
  const bothObjects =
    left !== null && right !== null && typeof left === "object" && typeof right === "object" && !Array.isArray(left) && !Array.isArray(right);
  if (!bothObjects) return [`${path || "(뿌리)"}: ${JSON.stringify(left)} != ${JSON.stringify(right)}`];
  const keys = new Set([...Object.keys(left), ...Object.keys(right)]);
  return [...keys].flatMap((key) => differences(left[key], right[key], path === "" ? key : `${path}.${key}`));
}

// ---------------------------------------------------------------------------------------------------------------------

// 회차의 묶음과 도는 차례. jar 는 함께 쓰는 클라이언트의 쿠키 통에 Secure 없는 쿠키를 남기므로 맨 끝이다.
const GROUPS = {
  control: controlRounds,
  clients: clientRound,
  setcookie: async () => {
    for (const kind of KINDS) await setCookieRound(kind);
    await naiveRound();
  },
  flow: async () => {
    for (const flow of FLOWS) await flowRound(flow);
  },
  concurrency: concurrencyRounds,
  raw: rawRound,
  jar: clientJarRounds,
  openapi: async () => {
    await openapiJarRound();
    await openapiTimeoutRound();
  },
};
const CHOSEN = args.only === undefined ? Object.keys(GROUPS) : args.only.split(",");
if (!CHOSEN.every((group) => group in GROUPS)) {
  console.error(`--only 는 ${Object.keys(GROUPS).join(", ")} 가운데 고른다(쉼표로 여럿)`);
  process.exit(2);
}

const startedAt = Date.now();
const versions = {
  next: load("next/package.json").version,
  playwright: load("@playwright/test/package.json").version,
  node: process.version,
  platform: process.platform,
};
// 모드는 스냅샷과 견주지 않는다. dev 로 돌아도 stable 은 start 의 스냅샷과 같아야 한다.
const settings = { rounds: ROUNDS, ttlSeconds: TTL, graceSeconds: GRACE };
const started = [];
let tester = null;
let failure = null;
let crashed = null;
const onCrash = (error) => {
  if (crashed !== null) return;
  crashed = error;
  console.error("처리되지 않은 예외로 멈춘다:", error);
  browser?.close().catch(() => undefined);
};
process.on("uncaughtException", onCrash);
process.on("unhandledRejection", onCrash);

try {
  const agentOs = launchStub("agentos_stub.py", ports.a);
  started.push(["Agent OS 대역", agentOs]);
  const widget = launchStub("widget_admin_stub.py", ports.w, ["--agent-os", aosBase]);
  started.push(["위젯 관리 서버 대역", widget]);
  const aosHealth = (await untilUp(agentOs, `${aosBase}/__probe/health`, "Agent OS 대역")).json;
  const widgetHealth = (await untilUp(widget, `${widgetBase}/__probe/health`, "위젯 관리 서버 대역")).json;
  Object.assign(versions, {
    python: aosHealth.python,
    fastapi: aosHealth.fastapi,
    starlette: aosHealth.starlette,
    uvicorn: aosHealth.uvicorn,
    httpx: widgetHealth.httpx,
    httpx2: widgetHealth.httpx2,
    openapiFetch: OPENAPI_FETCH_VERSION,
  });

  tester = createTester({ agentOs: aosBase, openapiFetch: createOpenapiClient });
  ports.c = await listen(tester.server);
  cOrigin = `http://localhost:${ports.c}`;

  if (MODE === "start") {
    const built = spawnSync(process.execPath, [NEXT_BIN, "build"], { cwd: APP, env: nextEnv(widgetBase), encoding: "utf-8", timeout: 600_000 });
    if (built.status !== 0) throw new Error(`next build 실패(종료 ${built.status}):\n${built.stdout}\n${built.stderr}`);
    const manifest = JSON.parse(readFileSync(join(APP, ".next", "routes-manifest.json"), "utf-8"));
    const baked = manifest.rewrites.afterFiles.map((rewrite) => `${rewrite.source} -> ${rewrite.destination}`);
    if (!same(baked, [`/api/:path* -> ${widgetBase}/:path*`])) throw new Error(`빌드 산출물의 rewrites 가 이 회차의 상류가 아니다: ${baked.join(", ")}`);
  }
  const admin = launchAdmin(MODE, ports.b, widgetBase);
  started.push(["포트 B 의 관리 화면 앱", admin]);
  await untilUp(admin, `http://127.0.0.1:${ports.b}/api/page`, "포트 B 의 관리 화면 앱");

  const { chromium } = load("@playwright/test");
  browser = await chromium.launch(args.channel === undefined ? {} : { channel: args.channel });
  versions.chromium = browser.version();
  versions.chromiumChannel = args.channel ?? "기본(headless shell)";
  console.log(`판: ${JSON.stringify(versions)}`);
  console.log(`설정: ${JSON.stringify({ mode: MODE, keepAliveSeconds: KEEP_ALIVE, ...settings })}`);

  for (const group of CHOSEN) await GROUPS[group]();
} catch (error) {
  failure = error;
  console.error(error);
} finally {
  await browser?.close().catch(() => undefined);
  if (tester !== null) await close(tester.server);
  http.globalAgent.destroy();
  for (const [what, one] of started.reverse()) {
    const freed = await stop(one);
    console.log(`${freed ? "내렸다" : "내리지 못했다"}  ${what}(포트 ${one.port})`);
    if (!freed) failure ??= new Error(`${what} 을 내리지 못했다`);
  }
}
failure ??= crashed;

const widgetOutput = started.find(([what]) => what === "위젯 관리 서버 대역")?.[1].output() ?? "";
const agentOsOutput = started.find(([what]) => what === "Agent OS 대역")?.[1].output() ?? "";
// Next 의 중계가 상류에 닿지 못하면 여기에 "Failed to proxy" 줄이 남는다.
const adminOutput = started.find(([what]) => what === "포트 B 의 관리 화면 앱")?.[1].output() ?? "";
writeFileSync(
  join(OUT, "results.json"),
  JSON.stringify(
    {
      versions,
      settings: { mode: MODE, keepAliveSeconds: KEEP_ALIVE, ...settings },
      ports,
      rounds,
      agentOsLog: aosLog,
      widgetLog,
      testerLog: tester?.log ?? [],
      agentOsOutput,
      widgetOutput,
      adminOutput,
    },
    null,
    2,
  ),
);
console.log(`\n원본 기록: ${join(OUT, "results.json")}`);

const unmeasured = rounds.filter((one) => !one.measured);
const markerCount = rounds.reduce((sum, one) => sum + one.markers.length, 0);
const markersSeen = rounds.reduce((sum, one) => sum + one.markers.filter((marker) => marker.ok).length, 0);
console.log(`회차 ${rounds.length}개 가운데 측정 ${rounds.length - unmeasured.length}개, 측정 아님 ${unmeasured.length}개. 표지 ${markersSeen}/${markerCount}`);
for (const one of unmeasured) console.log(`  측정 아님: ${one.name}`);

let expectedOk = true;
if (failure === null && args.only !== undefined) {
  console.log("--only 로 일부만 돌아 expected.json 과 견주지 않았다");
} else if (failure === null) {
  const stable = Object.fromEntries(rounds.map((one) => [one.name, one.stable]));
  if (args.update && unmeasured.length > 0) {
    // 측정이 아닌 회차의 값을 기준으로 받아 적지 않는다.
    expectedOk = false;
    console.log("측정이 아닌 회차가 있어 expected.json 을 쓰지 않았다");
  } else if (args.update) {
    writeFileSync(EXPECTED, `${JSON.stringify({ versions, settings, stable }, null, 2)}\n`);
    console.log("expected.json 을 이 회차의 결과로 썼다");
  } else if (existsSync(EXPECTED)) {
    const expected = JSON.parse(readFileSync(EXPECTED, "utf-8"));
    const drift = [...differences(expected.settings, settings, "settings"), ...differences(expected.stable, stable, "stable")];
    expectedOk = drift.length === 0;
    console.log(expectedOk ? "expected.json 과 모두 같다" : `expected.json 과 다른 자리 ${drift.length}(왼쪽이 expected):\n  ${drift.join("\n  ")}`);
  } else {
    expectedOk = false;
    console.log("expected.json 이 없다. --update 로 이 회차의 결과를 적는다");
  }
}
console.log(`걸린 시간 ${Math.round((Date.now() - startedAt) / 1000)}초`);
process.exit(failure === null && unmeasured.length === 0 && expectedOk ? 0 : 1);
