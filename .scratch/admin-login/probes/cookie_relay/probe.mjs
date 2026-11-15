// admin-login 설계: 관리 화면의 로그인 상태를 "스크립트가 읽지 못하는 쿠키"에 둘 때, 쿠키가 관리 화면의 중계(Next rewrites,
// ADR 0019)와 같은 호스트의 다른 포트 사이에서 실제로 어떻게 움직이는지 실제 Chromium 으로 잰다. 결정은 하지 않고 결과만 낸다.
//   node .scratch/admin-login/probes/cookie_relay/probe.mjs [--mode start|dev|both] [--out <폴더>] [--update] [--channel chromium]
//
// 띄우는 것(같은 폴더의 servers.mjs)
//   backend   상류(파이썬 서버) 자리의 스텁. 받은 요청 머리를 그대로 기록하고 Set-Cookie 를 여러 줄 싣는다
//   admin     실제 관리 화면. 앱의 시작 래퍼(tools/start.ts)로 next start(빌드 뒤)와 next dev 를 차례로 띄운다. 상류는
//             AGENT_OS_UPSTREAM 으로 스텁을 가리킨다. 앱의 소스와 설정은 고치지 않는다. 빌드는 앱의 .next/ 를 다시 쓴다
//   visitor   방문자용 페이지 자리의 서버(B). 관리 화면(A)과 호스트가 같고 포트가 다르다
//   tlsFront  https 갈래에서만. TLS 를 끝내고 관리 화면으로 넘기는 node 앞단(nginx 를 흉내 낸 것이고 nginx 가 아니다)
//
// 갈래(브라우저가 치는 주소)
//   http://localhost      개발에서 쓰는 주소
//   http://127.0.0.1      e2e 가 쓰는 주소
//   http://probe.test     루프백이 아닌 이름의 평문(대조). Secure 쿠키가 거절되는 것이 이 브라우저에서 보이는지
//   https://probe.test    배포와 닮은 꼴(루프백이 아닌 이름, https, 포트만 다른 둘). 자체 서명 인증서를 openssl 로 짓고
//                         브라우저는 인증서 오류를 무시한다. openssl 이 없으면 이 갈래는 재지 못했다고 적는다
//   probe.test 와 other.test 는 Chromium 의 --host-resolver-rules 로 127.0.0.1 에 맞춘다. hosts 파일은 건드리지 않는다.
//
// 재는 것(결과의 키)
//   wire          중계를 지난 응답의 Set-Cookie 줄을 node 의 날 HTTP 로 받아 상류가 낸 줄과 글자 그대로 견준다. 200 과
//                 204·401·303 응답을 본다. 클라이언트가 X-Forwarded-* 와 Origin 을 지어 보낼 때 상류가 받는 값도 본다
//   setCookie     브라우저가 받은 Set-Cookie 줄(CDP), 거절된 줄과 그 까닭(CDP blockedCookies), 쿠키 저장소에 든 것
//   sameOrigin    관리 화면 출처의 페이지가 보낸 요청(GET, 단순 POST, JSON POST, 주소창 이동)을 상류가 어떤 머리로 받는지
//   toVisitor     A 가 심은 쿠키가 B 로 가는 요청에 실리는지
//   crossPort     B 의 페이지가 A 로 보내는 요청(fetch 넷, 폼 POST, 링크)이 상류에 닿는지와 실린 쿠키·머리
//   crossSite     대조. 사이트가 다른 페이지(C)에서 같은 요청을 보내면 SameSite=Strict 쿠키가 빠지는지(CDP 의 SameSiteStrict)
//   overwrite     B 의 스크립트가 document.cookie 로 같은 이름의 쿠키를 심거나 덮을 수 있는지와 그 뒤 A 의 요청에 실리는 값
//   clearOn401    401 응답에 실린 지우는 Set-Cookie 를 브라우저가 받아들이는지
//   visitorServerSetCookie, plantFirst   덤. B 의 서버 응답이 같은 이름을 심는 경우와, A 가 심기 전에 B 가 먼저 심는 경우
//   frontHostWithoutPort   https 갈래에서 앞단이 Host 에서 포트를 떼어 넘겼을 때(release-image 의 proxy.conf 가 쓰는
//                 `Host $host` 를 흉내 낸 것) 상류가 받는 머리. 다른 관찰은 Host 를 받은 그대로 넘기는 앞단을 지난다
//
// 표지(측정이 재려던 상황에서 났는지). 하나라도 없으면 종료 코드가 0 이 아니다.
//   - 요청이 중계를 지났다: 상류가 받은 머리에 Next 의 프록시만 붙이는 x-forwarded-host 가 있다
//   - 모드: start 는 routes-manifest.json 에 이 회차의 상류가 박혔고 dev 전용 경로(/__nextjs_server_status)가 404 다.
//     dev 는 그 경로가 executionId 를 든 JSON 으로 답한다
//   - 브라우저가 그 요청을 실제로 보내려 했다: 태그마다 CDP 의 requestWillBeSent 가 있다
//   - 서버 쪽 기록과 브라우저 쪽 기록이 같은 요청의 것이다: 그 태그·메서드의 요청이 이 갈래에서 하나뿐이고, 서버가 받은
//     쿠키 이름이 CDP 가 실었다고 적은 이름과 같다(첫 판은 앞 갈래의 기록을 읽었다. 이 표지가 그것을 잡는다)
//   - document.cookie 로 쓰기가 되는 환경이다: 새 이름의 쿠키(probe_new)는 저장소에 든다. 이것이 없으면 "덮지 못했다"를 읽을 수 없다
//   - SameSite=Strict 가 걸리는 환경이다: 사이트가 다른 C 에서 보낸 요청에서 CDP 가 SameSiteStrict 로 뺐다고 적는다
//
// 결과는 포트와 무작위 쿠키 값을 이름표로 바꾼 뒤 같은 폴더의 expected.json 과 견준다. 다르면 다른 자리를 찍고 1 로 끝난다.
// expected.json 은 미리 적은 기대가 아니라 첫 측정(2026-11-14)의 결과를 --update 로 받아 적은 것이다. 원본 기록(상류와 B 의
// 요청 기록, 관리 화면의 출력)은 --out 폴더의 results.json 에 쓴다. 쿠키 값은 이 스크립트가 지은 무작위 값이고 비밀이 아니다.
// 띄운 관리 화면은 트리째 내린다(윈도우는 명령줄에 이 회차의 포트가 있을 때만 taskkill /T /F, 그 밖은 프로세스 그룹).
// 약 3분(빌드 포함). 네트워크를 타지 않는다.
// --channel chromium 은 기본(headless shell) 대신 전체 Chromium 으로 돈다. 2026-11-14 에 그 채널은 expected.json 과
// headerNamesAtBackend 만 달라(상류가 받는 머리에 accept-language 가 하나 더 온다) 1 로 끝났다.

import { spawn, spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import http from "node:http";
import { createRequire } from "node:module";
import { connect, createServer } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parseArgs } from "node:util";
import { close, createBackend, createTlsVisitor, createVisitor, listen, pairs, tlsFront } from "./servers.mjs";

const HERE = import.meta.dirname;
const ROOT = join(HERE, "..", "..", "..", "..");
const APP = join(ROOT, "web", "apps", "admin");
const START = join(APP, "tools", "start.ts");
const EXPECTED = join(HERE, "expected.json");
const load = createRequire(join(APP, "package.json"));
const NEXT_BIN = load.resolve("next/dist/bin/next");
const RESOLVER_RULES = "MAP probe.test 127.0.0.1, MAP other.test 127.0.0.1";
const SETTLE_MS = 2500;

const { values: args } = parseArgs({
  options: {
    mode: { type: "string", default: "both" },
    out: { type: "string" },
    update: { type: "boolean", default: false },
    channel: { type: "string" },
  },
});
const MODES = args.mode === "both" ? ["start", "dev"] : [args.mode];
if (!MODES.every((mode) => mode === "start" || mode === "dev")) {
  console.error("--mode 는 start, dev, both 가운데 하나다");
  process.exit(2);
}
const OUT = args.out ?? mkdtempSync(join(tmpdir(), "cookie-relay-"));
mkdirSync(OUT, { recursive: true });

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const markers = [];
const mark = (name, ok, detail = "") => {
  markers.push({ name, ok, detail });
  console.log(`${ok ? "표지 있음" : "표지 없음"}  ${name}${detail ? `  (${detail})` : ""}`);
};

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
  // 관리 화면은 토큰을 모른다(ADR 0019). 이 셸의 환경에 있어도 벗긴다.
  delete env.AGENT_OS_ADMIN_TOKEN;
  delete env.AGENT_OS_CHANNEL_TOKEN;
  return env;
}

function build(upstream) {
  return spawnSync(process.execPath, [NEXT_BIN, "build"], {
    cwd: APP,
    env: nextEnv(upstream),
    encoding: "utf-8",
    timeout: 600_000,
  });
}

function launchAdmin(mode, port, upstream) {
  const tail = [mode, "--hostname", "127.0.0.1", "--port", String(port)];
  const child = spawn(process.execPath, [START, ...tail], {
    cwd: APP,
    env: nextEnv(upstream),
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
    detached: process.platform !== "win32",
  });
  let output = "";
  child.stdout.on("data", (chunk) => (output += chunk));
  child.stderr.on("data", (chunk) => (output += chunk));
  return { child, port, commandTail: tail.join(" "), output: () => output };
}

/**
 * 트리째 내린다. 윈도우에서는 끄기 직전에 그 pid 의 명령줄에 이 회차의 인자(포트)가 있는지 본다.
 * POSIX 갈래는 명령줄을 보지 않는다. `exitCode` 와 `signalCode` 가 null 인 직접 자식은 node 가 아직
 * 거두지 않은 프로세스라, 그 pid 와 프로세스 그룹 번호가 다른 프로세스로 넘어가지 않는다고 봤다
 * (POSIX 의 pid 재사용 규칙과 node 의 동작에서 끌어낸 어림이고 재지 않았다).
 */
async function stopAdmin(admin) {
  const { child } = admin;
  if (child.exitCode === null && child.signalCode === null) {
    const exited = new Promise((resolve) => child.once("exit", resolve));
    if (process.platform === "win32") {
      const asked = spawnSync(
        "powershell",
        ["-NoProfile", "-Command", `(Get-CimInstance Win32_Process -Filter "ProcessId=${child.pid}").CommandLine`],
        { encoding: "utf-8", timeout: 30_000 },
      );
      if (typeof asked.stdout === "string" && asked.stdout.includes(admin.commandTail)) {
        spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore", timeout: 30_000 });
      } else {
        console.log(`pid ${child.pid} 의 명령줄에 이 회차의 인자가 없어 taskkill 을 치지 않고 kill() 만 했다`);
        child.kill();
      }
    } else {
      process.kill(-child.pid, "SIGKILL");
    }
    await Promise.race([exited, sleep(15_000)]);
  }
  for (let i = 0; i < 100; i += 1) {
    if (await refused(admin.port)) return true;
    await sleep(100);
  }
  return false;
}

function rawRequest(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, { agent: false, timeout: 30_000, headers }, (answer) => {
      const chunks = [];
      answer.on("data", (chunk) => chunks.push(chunk));
      answer.on("end", () =>
        resolve({
          status: answer.statusCode,
          rawHeaders: answer.rawHeaders,
          body: Buffer.concat(chunks).toString("utf-8"),
        }),
      );
    });
    request.on("timeout", () => request.destroy(new Error(`${url} 시간 초과`)));
    request.on("error", reject);
  });
}

async function untilRelay(admin, url) {
  const deadline = Date.now() + 180_000;
  while (Date.now() < deadline) {
    if (admin.child.exitCode !== null) throw new Error(`관리 화면이 서기 전에 끝났다:\n${admin.output()}`);
    try {
      const answer = await rawRequest(url);
      if (answer.status === 200) return;
    } catch {
      // 아직 서지 않았다.
    }
    await sleep(300);
  }
  throw new Error(`관리 화면의 중계가 서지 않았다:\n${admin.output()}`);
}

function makeCert() {
  const key = join(OUT, "key.pem");
  const cert = join(OUT, "cert.pem");
  const made = spawnSync(
    "openssl",
    [
      ...["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cert, "-days", "2"],
      ...["-subj", "/CN=probe.test", "-addext", "subjectAltName=DNS:probe.test,DNS:other.test"],
    ],
    { encoding: "utf-8", timeout: 60_000 },
  );
  if (made.status !== 0 || !existsSync(cert) || !existsSync(key)) {
    return { problem: made.error?.message ?? `openssl 종료 ${made.status}: ${made.stderr ?? ""}` };
  }
  return { key: readFileSync(key), cert: readFileSync(cert) };
}

// ---------------------------------------------------------------------------------------------------------------------
// 브라우저 쪽 기록(CDP)과 관찰

function newRecorder() {
  const requests = new Map();
  const requestCookies = new Map();
  const responses = new Map();
  const find = (tag, method) => {
    for (const [id, request] of requests) {
      if ((method === undefined || request.method === method) && URL.parse(request.url)?.searchParams.get("tag") === tag) {
        return id;
      }
    }
    return null;
  };
  const wait = async (probe) => {
    const deadline = Date.now() + SETTLE_MS;
    for (;;) {
      const found = probe();
      if (found !== null && found !== undefined) return found;
      if (Date.now() > deadline) return null;
      await sleep(50);
    }
  };
  return {
    async attach(context, page) {
      const cdp = await context.newCDPSession(page);
      await cdp.send("Network.enable");
      cdp.on("Network.requestWillBeSent", (event) =>
        requests.set(event.requestId, { url: event.request.url, method: event.request.method }),
      );
      cdp.on("Network.requestWillBeSentExtraInfo", (event) =>
        requestCookies.set(event.requestId, event.associatedCookies),
      );
      cdp.on("Network.responseReceivedExtraInfo", (event) => responses.set(event.requestId, event));
    },
    /** 브라우저가 그 태그의 요청을 보내려 했는가(메서드 무관). */
    attempted: (tag) => find(tag) !== null,
    /** 그 요청에 브라우저가 실은 쿠키 이름과, 뺀 쿠키와 그 까닭. */
    async cookies(tag, method) {
      const associated = await wait(() => {
        const id = find(tag, method);
        return id === null ? null : requestCookies.get(id);
      });
      if (associated === null) return null;
      return {
        sent: associated
          .filter((item) => item.blockedReasons.length === 0)
          .map((item) => item.cookie.name)
          .sort(),
        withheld: associated
          .filter((item) => item.blockedReasons.length > 0)
          .map((item) => `${item.cookie.name}: ${[...item.blockedReasons].sort().join(",")}`)
          .sort(),
      };
    },
    /** 브라우저가 받은 응답의 Set-Cookie 줄과 거절한 줄. */
    async response(tag, method) {
      const event = await wait(() => {
        const id = find(tag, method);
        return id === null ? null : responses.get(id);
      });
      if (event === null) return null;
      const key = Object.keys(event.headers).find((name) => name.toLowerCase() === "set-cookie");
      return {
        setCookie: key === undefined ? [] : event.headers[key].split("\n"),
        blocked: (event.blockedCookies ?? []).map(
          (item) => `${item.cookieLine.split("=")[0]}: ${[...item.blockedReasons].sort().join(",")}`,
        ),
      };
    },
  };
}

async function openPage(context, recorder, url) {
  const page = await context.newPage();
  await recorder.attach(context, page);
  await page.goto(url, { waitUntil: "load" });
  return page;
}

function pageFetch(page, url, init) {
  return page.evaluate(
    async ([target, options]) => {
      try {
        const answer = await fetch(target, options);
        return `응답 ${answer.status} type=${answer.type}`;
      } catch (error) {
        return `거부 ${error.name}: ${error.message}`;
      }
    },
    [url, init ?? {}],
  );
}

const WATCHED = [
  "host",
  "origin",
  "referer",
  "sec-fetch-site",
  "sec-fetch-mode",
  "sec-fetch-dest",
  "content-type",
  "cookie",
];
const FORWARDED = /^(x-forwarded-.*|forwarded|x-real-ip)$/i;

function received(entry, normalize) {
  const out = {};
  for (const name of WATCHED) {
    const found = entry.headers.filter(([key]) => key.toLowerCase() === name).map(([, value]) => normalize(value));
    out[name] = found.length === 0 ? null : found.join(" | ");
  }
  out.forwarded = entry.headers
    .filter(([key]) => FORWARDED.test(key))
    .map(([key, value]) => `${key.toLowerCase()}: ${normalize(value)}`)
    .sort();
  return out;
}

/**
 * 그 태그로 서버에 닿은 요청들. 태그는 갈래와 모드마다 다시 쓰이고 기록은 회차 내내 쌓이므로, 이 갈래가 시작한 뒤의
 * 기록(since)만 본다. 그러지 않으면 앞 갈래의 요청을 이 갈래의 것으로 읽는다.
 */
async function seen(log, tag, method, since) {
  const deadline = Date.now() + SETTLE_MS;
  for (;;) {
    const entries = log.filter((entry) => entry.seq >= since && entry.tag === tag);
    if (entries.some((entry) => entry.method === method) || Date.now() > deadline) return entries;
    await sleep(50);
  }
}

/** 태그 하나의 관찰: 그 서버에 닿은 메서드, 받은 머리, 브라우저가 실은·뺀 쿠키. */
async function observe(scope, log, tag, method, fetched) {
  const entries = await seen(log, tag, method, scope.since.get(log));
  const main = entries.find((entry) => entry.method === method) ?? null;
  const browserCookies = await scope.recorder.cookies(tag, method);
  scope.attempted.push([tag, scope.recorder.attempted(tag)]);
  // 서버 쪽 기록과 브라우저 쪽 기록이 같은 요청의 것인지: 그 메서드의 요청이 하나뿐이고, 서버가 받은 쿠키 이름이
  // 브라우저가 실었다고 적은 이름과 같다.
  if (entries.filter((entry) => entry.method === method).length > 1) scope.mismatched.push(`${tag}(요청이 둘 이상)`);
  if (main !== null && browserCookies !== null) {
    const header = main.headers.find(([key]) => key.toLowerCase() === "cookie")?.[1] ?? "";
    const atServer = header
      .split("; ")
      .filter((part) => part !== "")
      .map((part) => part.split("=")[0])
      .sort();
    if (JSON.stringify(atServer) !== JSON.stringify(browserCookies.sent)) scope.mismatched.push(tag);
  }
  return {
    ...(fetched === undefined ? {} : { fetch: fetched }),
    reached: entries.map((entry) => entry.method),
    received: main === null ? null : received(main, scope.normalize),
    browserCookies,
  };
}

function jar(cookies, normalize, names) {
  return cookies
    .filter((cookie) => names === undefined || names.includes(cookie.name))
    .map(
      (cookie) =>
        `${cookie.name}=${normalize(cookie.value)}; domain=${cookie.domain}; path=${cookie.path}; ` +
        `httpOnly=${cookie.httpOnly}; secure=${cookie.secure}; sameSite=${cookie.sameSite}; ` +
        `${cookie.expires === -1 ? "session" : "expires"}`,
    )
    .sort();
}

async function submitForm(page, tag) {
  const arrived = page.waitForURL((url) => url.searchParams.get("tag") === tag, { waitUntil: "load" });
  // 폼을 내면 문서가 바뀌어 evaluate 가 끊길 수 있다. 끊김은 이동이 일어났다는 뜻이라 삼킨다.
  await page.evaluate(() => document.getElementById("f").submit()).catch(() => undefined);
  await arrived;
}

async function clickLink(page, tag) {
  const arrived = page.waitForURL((url) => url.searchParams.get("tag") === tag, { waitUntil: "load" });
  await page.click("#l");
  await arrived;
}

// ---------------------------------------------------------------------------------------------------------------------
// 갈래 하나

// B 의 스크립트가 document.cookie 에 넣는 글. A 가 쿠키를 심은 뒤의 새 컨텍스트에서 하나씩 넣는다.
const ATTEMPTS = [
  { id: "ow-host-same-key", name: "__Host-probe_at", text: "__Host-probe_at=EVIL1; Secure; Path=/" },
  { id: "ow-plain-same-key", name: "probe_plain", text: "probe_plain=EVIL2; Secure; Path=/" },
  { id: "ow-plain-other-path-secure", name: "probe_plain", text: "probe_plain=EVIL3; Secure; Path=/api" },
  { id: "ow-plain-other-path", name: "probe_plain", text: "probe_plain=EVIL4; Path=/api" },
  { id: "ow-host-other-path", name: "__Host-probe_at", text: "__Host-probe_at=EVIL5; Secure; Path=/api" },
  { id: "ow-host-new-name", name: "__Host-probe_new", text: "__Host-probe_new=EVIL6; Secure; Path=/" },
  { id: "ow-plain-new-name", name: "probe_new", text: "probe_new=EVIL7; Path=/" },
  // 대조: A 가 HttpOnly 만 뺀 같은 속성으로 심은 쿠키(/set-open)를 같은 키로 덮는다. 첫 시도와 다른 것은 HttpOnly 하나다.
  {
    id: "ow-host-same-key-not-httponly",
    name: "__Host-probe_open",
    adminPath: "/api/set-open",
    text: "__Host-probe_open=EVIL8; Secure; Path=/",
  },
];

async function inContext(browser, env, family, body) {
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const scope = {
    recorder: newRecorder(),
    normalize: env.normalize,
    backend: env.backend,
    since: env.since,
    attempted: [],
    mismatched: [],
    context,
    family,
  };
  try {
    const result = await body(scope);
    const missing = scope.attempted.filter(([, ok]) => !ok).map(([tag]) => tag);
    return { result, missing, mismatched: scope.mismatched, count: scope.attempted.length };
  } finally {
    await context.close();
  }
}

async function runFamily(browser, shared, family) {
  const { backend, visitor } = shared;
  // 이 갈래가 시작한 자리. 관찰은 이 뒤의 기록만 본다(seen 의 주석).
  const env = { ...shared, since: new Map([[backend.log, backend.log.length], [visitor.log, visitor.log.length]]) };
  const out = {};
  const missing = [];
  const mismatched = [];
  let observed = 0;
  const run = async (body) => {
    const done = await inContext(browser, env, family, body);
    missing.push(...done.missing);
    mismatched.push(...done.mismatched);
    observed += done.count;
    return done.result;
  };

  await run(async (scope) => {
    const { context, recorder, normalize } = scope;
    const pageA = await openPage(context, recorder, `${family.a}/api/page?tag=a-page`);

    // 쿠키를 심는다(같은 출처의 fetch). 브라우저가 받은 줄, 거절한 줄, 저장소.
    const set = await pageFetch(pageA, "/api/set?tag=set");
    const controls = await pageFetch(pageA, "/api/set-controls?tag=set-controls");
    const setAnswer = await recorder.response("set", "GET");
    const controlsAnswer = await recorder.response("set-controls", "GET");
    scope.attempted.push(["set", recorder.attempted("set")], ["set-controls", recorder.attempted("set-controls")]);
    out.setCookie = {
      fetch: [set, controls],
      linesAtBrowser: setAnswer?.setCookie.map(normalize) ?? null,
      controlLinesAtBrowser: controlsAnswer?.setCookie.map(normalize) ?? null,
      rejected: [...(setAnswer?.blocked ?? []), ...(controlsAnswer?.blocked ?? [])],
      jar: jar(await context.cookies(), normalize),
    };

    // 같은 출처에서 보낸 요청을 상류가 어떻게 받는가.
    const sameOrigin = {};
    sameOrigin.get = await observe(scope, backend.log, "so-get", "GET", await pageFetch(pageA, "/api/echo?tag=so-get"));
    const sample = backend.log.find(
      (entry) => entry.seq >= scope.since.get(backend.log) && entry.tag === "so-get" && entry.method === "GET",
    );
    out.headerNamesAtBackend = sample === undefined ? null : sample.headers.map(([key]) => key.toLowerCase()).sort();
    if (family.scope === "cookies") {
      out.sameOrigin = sameOrigin;
      return;
    }
    sameOrigin.postSimple = await observe(
      scope,
      backend.log,
      "so-post-simple",
      "POST",
      await pageFetch(pageA, "/api/echo?tag=so-post-simple", { method: "POST", body: "a=1" }),
    );
    sameOrigin.postJson = await observe(
      scope,
      backend.log,
      "so-post-json",
      "POST",
      await pageFetch(pageA, "/api/echo?tag=so-post-json", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: '{"a":1}',
      }),
    );
    sameOrigin.otherPath = await observe(
      scope,
      backend.log,
      "so-other",
      "GET",
      await pageFetch(pageA, "/api/other?tag=so-other"),
    );
    const typed = await openPage(context, recorder, `${family.a}/api/echo?tag=so-nav`);
    sameOrigin.navigation = await observe(scope, backend.log, "so-nav", "GET");
    await typed.close();
    out.sameOrigin = sameOrigin;

    // A 가 심은 쿠키가 B 로 가는 요청에 실리는가.
    const pageB = await openPage(context, recorder, `${family.b}/?tag=b-nav`);
    out.toVisitor = {
      navigation: await observe(scope, visitor.log, "b-nav", "GET"),
      fetch: await observe(scope, visitor.log, "b-fetch", "GET", await pageFetch(pageB, "/echo?tag=b-fetch")),
      fetchUnderApiEcho: await observe(
        scope,
        visitor.log,
        "b-fetch-scoped",
        "GET",
        await pageFetch(pageB, "/api/echo?tag=b-fetch-scoped"),
      ),
      documentCookie: normalize(await pageB.evaluate(() => document.cookie)),
    };

    // B 의 페이지가 A 로 보내는 요청.
    out.crossPort = await fromOtherPage(scope, pageB, family.b, "xp");
    // 대조: 사이트가 다른 C 의 페이지가 A 로 보내는 요청.
    const pageC = await openPage(context, recorder, `${family.c}/?tag=c-nav`);
    out.crossSite = await fromOtherPage(scope, pageC, family.c, "cs");

    if (family.a2 !== undefined) {
      const pageA2 = await openPage(context, recorder, `${family.a2}/api/page?tag=a2-page`);
      out.frontHostWithoutPort = {
        get: await observe(scope, backend.log, "a2-get", "GET", await pageFetch(pageA2, "/api/echo?tag=a2-get")),
        postJson: await observe(
          scope,
          backend.log,
          "a2-post-json",
          "POST",
          await pageFetch(pageA2, "/api/echo?tag=a2-post-json", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: '{"a":1}',
          }),
        ),
      };
    }
  });
  if (family.scope === "cookies") return { out, missing, mismatched, observed };

  // B 의 스크립트가 같은 이름의 쿠키를 심거나 덮을 수 있는가. 시도마다 새 컨텍스트.
  out.overwrite = {};
  for (const attempt of ATTEMPTS) {
    out.overwrite[attempt.id] = await run(async (scope) => {
      const { context, recorder, normalize } = scope;
      const pageA = await openPage(context, recorder, `${family.a}/api/page?tag=${attempt.id}-a`);
      await pageFetch(pageA, `/api/set?tag=${attempt.id}-set`);
      if (attempt.adminPath !== undefined) await pageFetch(pageA, `${attempt.adminPath}?tag=${attempt.id}-set-more`);
      const pageB = await openPage(context, recorder, `${family.b}/?tag=${attempt.id}-b`);
      const before = jar(await context.cookies(), normalize, [attempt.name]);
      await pageB.evaluate((text) => {
        document.cookie = text;
      }, attempt.text);
      const scriptSees = normalize(await pageB.evaluate(() => document.cookie));
      const after = jar(await context.cookies(), normalize, [attempt.name]);
      const echoed = await observe(
        scope,
        backend.log,
        `${attempt.id}-echo`,
        "GET",
        await pageFetch(pageA, `/api/echo?tag=${attempt.id}-echo`),
      );
      return {
        wrote: attempt.text,
        scriptSees,
        jarBefore: before,
        jarAfter: after,
        cookieAtBackend: echoed.received?.cookie ?? null,
      };
    });
  }

  // 덤: B 의 서버가 자기 응답으로 같은 이름을 싣는다(스크립트가 아니라 HTTP).
  out.visitorServerSetCookie = await run(async (scope) => {
    const { context, recorder, normalize } = scope;
    const names = ["__Host-probe_at", "probe_plain"];
    const pageA = await openPage(context, recorder, `${family.a}/api/page?tag=vs-a`);
    await pageFetch(pageA, "/api/set?tag=vs-set");
    const pageB = await openPage(context, recorder, `${family.b}/?tag=vs-b`);
    const fetched = await pageFetch(pageB, "/set-evil?tag=vs-evil");
    const answer = await recorder.response("vs-evil", "GET");
    scope.attempted.push(["vs-evil", recorder.attempted("vs-evil")]);
    const after = jar(await context.cookies(), normalize, names);
    const echoed = await observe(scope, backend.log, "vs-echo", "GET", await pageFetch(pageA, "/api/echo?tag=vs-echo"));
    return { fetch: fetched, rejected: answer?.blocked ?? null, jarAfter: after, cookieAtBackend: echoed.received?.cookie ?? null };
  });

  // 200 이 아닌 응답에 실린 Set-Cookie(지우는 줄)를 브라우저가 받아들이는가. 만료를 알리는 401 로 본다.
  out.clearOn401 = await run(async (scope) => {
    const { context, recorder, normalize } = scope;
    const names = ["__Host-probe_at", "probe_plain", "__Host-probe_rt"];
    const pageA = await openPage(context, recorder, `${family.a}/api/page?tag=clear-a`);
    await pageFetch(pageA, "/api/set?tag=clear-set");
    const before = jar(await context.cookies(), normalize, names);
    const fetched = await pageFetch(pageA, "/api/set-status?code=401&tag=clear-401");
    const answer = await recorder.response("clear-401", "GET");
    scope.attempted.push(["clear-401", recorder.attempted("clear-401")]);
    return {
      fetch: fetched,
      linesAtBrowser: answer?.setCookie ?? null,
      jarBefore: before,
      jarAfter: jar(await context.cookies(), normalize, names),
    };
  });

  // 덤: A 가 심기 전에 B 의 스크립트가 먼저 심는다.
  out.plantFirst = await run(async (scope) => {
    const { context, recorder, normalize } = scope;
    const names = ["__Host-probe_at"];
    const pageB = await openPage(context, recorder, `${family.b}/?tag=pf-b`);
    await pageB.evaluate(() => {
      document.cookie = "__Host-probe_at=PLANTED; Secure; Path=/";
    });
    const planted = jar(await context.cookies(), normalize, names);
    const pageA = await openPage(context, recorder, `${family.a}/api/page?tag=pf-a`);
    const first = await observe(scope, backend.log, "pf-echo-1", "GET", await pageFetch(pageA, "/api/echo?tag=pf-echo-1"));
    await pageFetch(pageA, "/api/set?tag=pf-set");
    const afterSet = jar(await context.cookies(), normalize, names);
    const second = await observe(scope, backend.log, "pf-echo-2", "GET", await pageFetch(pageA, "/api/echo?tag=pf-echo-2"));
    return {
      jarAfterPlant: planted,
      cookieAtBackendBeforeLogin: first.received?.cookie ?? null,
      jarAfterAdminSet: afterSet,
      cookieAtBackendAfterLogin: second.received?.cookie ?? null,
    };
  });

  return { out, missing, mismatched, observed };
}

/** 다른 출처의 페이지(B 나 C)가 A 로 보내는 요청 여섯. prefix 는 태그의 머리(xp, cs). */
async function fromOtherPage(scope, page, origin, prefix) {
  const { context, recorder, family, backend } = scope;
  const target = (name) => `${family.a}/api/echo?tag=${prefix}-${name}`;
  const out = {};
  out.get = await observe(
    scope,
    backend.log,
    `${prefix}-get`,
    "GET",
    await pageFetch(page, target("get"), { credentials: "include" }),
  );
  out.postSimple = await observe(
    scope,
    backend.log,
    `${prefix}-post-simple`,
    "POST",
    await pageFetch(page, target("post-simple"), { method: "POST", credentials: "include", body: "a=1" }),
  );
  out.postNoCors = await observe(
    scope,
    backend.log,
    `${prefix}-post-nocors`,
    "POST",
    await pageFetch(page, target("post-nocors"), {
      method: "POST",
      credentials: "include",
      mode: "no-cors",
      body: "a=1",
    }),
  );
  out.postJson = await observe(
    scope,
    backend.log,
    `${prefix}-post-json`,
    "POST",
    await pageFetch(page, target("post-json"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: '{"a":1}',
    }),
  );
  const formPage = await openPage(
    context,
    recorder,
    `${origin}/form?tag=${prefix}-form-page&to=${encodeURIComponent(target("form"))}`,
  );
  await submitForm(formPage, `${prefix}-form`);
  out.formPost = await observe(scope, backend.log, `${prefix}-form`, "POST");
  await formPage.close();
  const linkPage = await openPage(
    context,
    recorder,
    `${origin}/form?tag=${prefix}-link-page&to=${encodeURIComponent(target("link"))}`,
  );
  await clickLink(linkPage, `${prefix}-link`);
  out.linkGet = await observe(scope, backend.log, `${prefix}-link`, "GET");
  await linkPage.close();
  return out;
}

// ---------------------------------------------------------------------------------------------------------------------
// 모드 하나(start 나 dev)

function setCookieLines(answer) {
  return pairs(answer.rawHeaders)
    .filter(([key]) => key.toLowerCase() === "set-cookie")
    .map(([, value]) => value);
}

async function runMode(mode, shared) {
  const { browser, backend, visitor, tls, values, stubPort, bPort, upstream } = shared;
  const info = { mode };
  if (mode === "start") {
    const built = build(upstream);
    if (built.status !== 0) throw new Error(`next build 실패(종료 ${built.status}):\n${built.stdout}\n${built.stderr}`);
    const manifest = JSON.parse(readFileSync(join(APP, ".next", "routes-manifest.json"), "utf-8"));
    const baked = manifest.rewrites.afterFiles.map((rewrite) => `${rewrite.source} -> ${rewrite.destination}`);
    mark(
      "start: 빌드 산출물의 rewrites 에 이 회차의 상류가 박혔다",
      JSON.stringify(baked) === JSON.stringify([`/api/:path* -> ${upstream}/:path*`]),
      baked.join(", "),
    );
  }
  const aPort = await freePort();
  const admin = launchAdmin(mode, aPort, upstream);
  const servers = [];
  try {
    await untilRelay(admin, `http://127.0.0.1:${aPort}/api/echo?tag=warmup`);

    // 모드의 표지: dev 서버만 답하는 경로(next-devtools 의 restart-dev-server-middleware). dev 는 executionId 를 든
    // JSON, start 는 404 다.
    const devOnly = await rawRequest(`http://127.0.0.1:${aPort}/__nextjs_server_status`);
    const answersAsDev = devOnly.status === 200 && devOnly.body.includes("executionId");
    info.devOnlyPathStatus = devOnly.status;
    mark(
      `${mode}: 서버가 ${mode === "dev" ? "dev 전용 경로에 executionId 로 답한다" : "dev 전용 경로를 모른다(404)"}`,
      mode === "dev" ? answersAsDev : devOnly.status === 404,
      `GET /__nextjs_server_status -> ${devOnly.status}`,
    );

    const labels = [
      [`:${stubPort}`, ":<STUB>"],
      [`:${aPort}`, ":<A>"],
      [`:${bPort}`, ":<B>"],
      ...Object.entries(values).map(([key, value]) => [value, `<${key}>`]),
    ];
    const families = [
      {
        name: "http://localhost",
        a: `http://localhost:${aPort}`,
        b: `http://localhost:${bPort}`,
        c: `http://127.0.0.1:${bPort}`,
        scope: "full",
      },
      {
        name: "http://127.0.0.1",
        a: `http://127.0.0.1:${aPort}`,
        b: `http://127.0.0.1:${bPort}`,
        c: `http://localhost:${bPort}`,
        scope: "full",
      },
      {
        name: "http://probe.test",
        a: `http://probe.test:${aPort}`,
        b: `http://probe.test:${bPort}`,
        c: `http://other.test:${bPort}`,
        scope: "cookies",
      },
    ];
    if (tls !== null) {
      const front = tlsFront(tls, aPort, "pass");
      const frontHostName = tlsFront(tls, aPort, "name");
      const tlsVisitor = createTlsVisitor(tls, visitor.log);
      servers.push(front, frontHostName, tlsVisitor);
      const taPort = await listen(front);
      const ta2Port = await listen(frontHostName);
      const tbPort = await listen(tlsVisitor);
      labels.push([`:${taPort}`, ":<TA>"], [`:${ta2Port}`, ":<TA2>"], [`:${tbPort}`, ":<TB>"]);
      families.push({
        name: "https://probe.test",
        a: `https://probe.test:${taPort}`,
        a2: `https://probe.test:${ta2Port}`,
        b: `https://probe.test:${tbPort}`,
        c: `https://other.test:${tbPort}`,
        scope: "full",
      });
    }
    const normalize = (text) => labels.reduce((acc, [literal, label]) => acc.split(literal).join(label), text);
    const env = { backend, visitor, normalize };

    // 날 HTTP 로 본 Set-Cookie 줄: 상류가 낸 것과 중계를 지난 것.
    const wireStart = backend.log.length;
    const direct = await rawRequest(`http://127.0.0.1:${stubPort}/set?tag=wire-direct`);
    const relayed = await rawRequest(`http://127.0.0.1:${aPort}/api/set?tag=wire-relay`);
    const relayEntry = backend.log.find((entry) => entry.seq >= wireStart && entry.tag === "wire-relay");
    const facts = {
      wire: {
        directSetCookie: setCookieLines(direct).map(normalize),
        relayedSetCookie: setCookieLines(relayed).map(normalize),
        identical: JSON.stringify(setCookieLines(direct)) === JSON.stringify(setCookieLines(relayed)),
        relayedHeaderNames: pairs(relayed.rawHeaders).map(([key]) => key.toLowerCase()),
        directHeaderNames: pairs(direct.rawHeaders).map(([key]) => key.toLowerCase()),
        backendReceived: relayEntry === undefined ? null : received(relayEntry, normalize),
      },
    };
    mark(
      `${mode}: 요청이 중계를 지났다(상류가 받은 머리에 x-forwarded-host 가 있다)`,
      facts.wire.backendReceived?.forwarded.some((line) => line.startsWith("x-forwarded-host:")) === true,
    );

    // 200 이 아닌 응답의 Set-Cookie 도 줄 그대로 지나는가(날 HTTP. 303 은 따라가지 않는다).
    facts.wire.otherStatuses = {};
    for (const code of [204, 401, 303]) {
      const plain = await rawRequest(`http://127.0.0.1:${stubPort}/set-status?code=${code}&tag=wire-direct-${code}`);
      const through = await rawRequest(`http://127.0.0.1:${aPort}/api/set-status?code=${code}&tag=wire-relay-${code}`);
      facts.wire.otherStatuses[code] = {
        relayedStatus: through.status,
        relayedSetCookie: setCookieLines(through),
        identical: JSON.stringify(setCookieLines(plain)) === JSON.stringify(setCookieLines(through)),
        relayedLocation: pairs(through.rawHeaders).find(([key]) => key.toLowerCase() === "location")?.[1] ?? null,
      };
    }

    // 클라이언트가 X-Forwarded-* 와 Origin 을 지어 보내면 상류는 무엇을 받는가(날 HTTP).
    const spoofStart = backend.log.length;
    await rawRequest(`http://127.0.0.1:${aPort}/api/echo?tag=wire-spoof`, {
      "X-Forwarded-Host": "evil.example",
      "X-Forwarded-For": "203.0.113.9",
      "X-Forwarded-Proto": "https",
      "X-Forwarded-Port": "443",
      Forwarded: "for=203.0.113.9;host=evil.example;proto=https",
      Origin: "https://evil.example",
    });
    const spoofEntry = backend.log.find((entry) => entry.seq >= spoofStart && entry.tag === "wire-spoof");
    facts.wire.clientSuppliedForwarded = spoofEntry === undefined ? null : received(spoofEntry, normalize);

    for (const family of families) {
      const done = await runFamily(browser, env, family);
      facts[family.name] = done.out;
      mark(
        `${mode} ${family.name}: 관찰한 요청마다 브라우저가 실제로 보내려 했다(CDP requestWillBeSent)`,
        done.missing.length === 0 && done.observed > 0,
        `${done.observed - done.missing.length}/${done.observed}${done.missing.length ? `, 없음: ${done.missing.join(" ")}` : ""}`,
      );
      mark(
        `${mode} ${family.name}: 서버 쪽 기록과 브라우저 쪽 기록이 같은 요청의 것이다(요청은 하나씩이고 쿠키 이름이 같다)`,
        done.mismatched.length === 0,
        done.mismatched.join(" "),
      );
      if (family.scope === "full") {
        const fresh = done.out.overwrite["ow-plain-new-name"];
        mark(
          `${mode} ${family.name}: document.cookie 쓰기가 되는 환경이다(새 이름 probe_new 가 저장소에 든다)`,
          fresh.jarAfter.some((line) => line.startsWith("probe_new=EVIL7")),
        );
        const withheld = done.out.crossSite.postSimple.browserCookies?.withheld ?? [];
        // 쿠키가 하나도 저장되지 않은 갈래에서는 뺄 쿠키가 없어 이 표지를 볼 수 없다. 그때는 표지가 아니라 결과로 남긴다.
        if (done.out.setCookie.jar.length > 0) {
          mark(
            `${mode} ${family.name}: SameSite=Strict 가 걸리는 환경이다(사이트가 다른 C 의 요청에서 CDP 가 SameSiteStrict 로 뺐다)`,
            withheld.some((line) => line.includes("SameSiteStrict")),
            withheld.join(" / "),
          );
        }
      }
    }
    info.adminOutputHead = normalize(admin.output()).slice(0, 800);
    return { facts, info };
  } finally {
    for (const server of servers) await close(server);
    const freed = await stopAdmin(admin);
    mark(`${mode}: 띄운 관리 화면을 내렸다(포트가 연결을 거절한다)`, freed);
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// 견줌

function differences(left, right, path = "") {
  if (JSON.stringify(left) === JSON.stringify(right)) return [];
  const bothObjects =
    left !== null && right !== null && typeof left === "object" && typeof right === "object" && !Array.isArray(left) && !Array.isArray(right);
  if (!bothObjects) return [`${path || "(뿌리)"}: ${JSON.stringify(left)} != ${JSON.stringify(right)}`];
  const keys = new Set([...Object.keys(left), ...Object.keys(right)]);
  return [...keys].flatMap((key) => differences(left[key], right[key], path === "" ? key : `${path}.${key}`));
}

// ---------------------------------------------------------------------------------------------------------------------

const versions = {
  next: load("next/package.json").version,
  playwright: load("@playwright/test/package.json").version,
  node: process.version,
  platform: process.platform,
};
const values = Object.fromEntries(
  ["at", "rt", "plain", "scoped", "badpath", "nosecure", "open"].map((key) => [
    key,
    `${key}-${randomBytes(6).toString("hex")}`,
  ]),
);
const backend = createBackend(values);
const visitor = createVisitor();
const stubPort = await listen(backend.server);
const bPort = await listen(visitor.server);
const upstream = `http://127.0.0.1:${stubPort}`;
const cert = makeCert();
const tls = "problem" in cert ? null : cert;
if (tls === null) console.log(`https 갈래는 재지 못한다(openssl): ${cert.problem}`);

const { chromium } = load("@playwright/test");
const browser = await chromium.launch({
  args: [`--host-resolver-rules=${RESOLVER_RULES}`],
  ...(args.channel === undefined ? {} : { channel: args.channel }),
});
versions.chromium = browser.version();
// 채널을 주지 않으면 Playwright 는 headless 에서 chrome-headless-shell 을 띄운다. --channel chromium 이면 같은 판의 온전한 Chromium 이다.
versions.chromiumChannel = args.channel ?? "기본(headless shell)";
console.log(`판: ${JSON.stringify(versions)}`);

const facts = {};
const infos = {};
let failure = null;
// 서버 처리기 안에서 던져진 예외로 프로세스가 죽으면 관리 화면과 브라우저가 남는다. 죽지 않고 브라우저를 닫아, 걸려 있던
// 페이지 호출이 거절되고 finally 가 관리 화면을 내리게 한다.
let crashed = null;
const onCrash = (error) => {
  if (crashed !== null) return;
  crashed = error;
  console.error("처리되지 않은 예외로 멈춘다:", error);
  browser.close().catch(() => undefined);
};
process.on("uncaughtException", onCrash);
process.on("unhandledRejection", onCrash);
try {
  for (const mode of MODES) {
    const done = await runMode(mode, { browser, backend, visitor, tls, values, stubPort, bPort, upstream });
    facts[mode] = done.facts;
    infos[mode] = done.info;
  }
} catch (error) {
  failure = error;
  console.error(error);
} finally {
  await browser.close().catch(() => undefined);
  await close(backend.server);
  await close(visitor.server);
}
failure ??= crashed;

const modeDifferences = MODES.length === 2 && failure === null ? differences(facts.start, facts.dev) : null;
writeFileSync(
  join(OUT, "results.json"),
  JSON.stringify(
    { versions, httpsMeasured: tls !== null, markers, modeDifferences, facts, infos, backendLog: backend.log, visitorLog: visitor.log },
    null,
    2,
  ),
);
console.log(`원본 기록: ${join(OUT, "results.json")}`);

if (modeDifferences !== null) {
  console.log(
    modeDifferences.length === 0
      ? "start 와 dev 의 결과가 모두 같다"
      : `start 와 dev 가 다른 자리 ${modeDifferences.length}:\n  ${modeDifferences.join("\n  ")}`,
  );
}

let expectedOk = true;
if (failure === null) {
  const snapshot = { httpsMeasured: tls !== null, facts };
  if (args.update) {
    writeFileSync(EXPECTED, `${JSON.stringify({ versions, ...snapshot }, null, 2)}\n`);
    console.log(`expected.json 을 이 회차의 결과로 썼다`);
  } else if (existsSync(EXPECTED)) {
    const expected = JSON.parse(readFileSync(EXPECTED, "utf-8"));
    const partial = Object.fromEntries(MODES.map((mode) => [mode, expected.facts[mode]]));
    const drift = [
      ...differences(expected.httpsMeasured, snapshot.httpsMeasured, "httpsMeasured"),
      ...differences(partial, facts, "facts"),
    ];
    expectedOk = drift.length === 0;
    console.log(
      expectedOk
        ? "expected.json 과 모두 같다"
        : `expected.json 과 다른 자리 ${drift.length}(왼쪽이 expected):\n  ${drift.join("\n  ")}`,
    );
  } else {
    expectedOk = false;
    console.log("expected.json 이 없다. --update 로 이 회차의 결과를 적는다");
  }
}

const unmarked = markers.filter((marker) => !marker.ok);
if (unmarked.length > 0) console.log(`표지 없는 것 ${unmarked.length}: 이 회차는 측정으로 세지 않는다`);
process.exit(failure === null && unmarked.length === 0 && expectedOk ? 0 : 1);
