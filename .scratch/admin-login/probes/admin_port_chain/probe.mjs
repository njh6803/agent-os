// admin-login 명세: 관리 화면을 단독 배포의 프록시(nginx)가 새 포트에서 TLS 를 끝내 넘길 때, 그 길에서 쿠키와 요청 머리가
// 움직이는 모양을 실제 nginx 와 실제 관리 화면 이미지(Next 중계)로 잰다. 앞선 cookie_relay 프로브가 앞단을 node 로 흉내 내
// "재지 못한 것"으로 남긴 자리를 채운다. 결정은 하지 않고 결과만 낸다.
//
//   node .scratch/admin-login/probes/admin_port_chain/probe.mjs [--web <web 폴더>] [--out <폴더>] [--keep] [--channel chromium]
//
// 띄우는 것(같은 폴더의 compose.yaml. 프로젝트 이름은 실행마다 `aos-port-chain-<난수>` 이고 끝에 그 이름으로 내린다)
//   serve          serve 자리의 대역(serve_stub.py, 이미지 python:3.12-slim-trixie). 받은 머리와 TCP 상대를 적는다
//   admin          실제 관리 화면 이미지(agent-os-e2e/agent-os-admin:0.1.0-rc.1). 상류가 빌드 때 http://serve:8000 으로 굳었다
//   proxy          후보 nginx(nginx/candidate). 관리 화면용 리스너 9443 과 방문자용 리스너 자리 8443
//   proxy_control  대조 nginx(nginx/control). X-Forwarded-For 를 덧붙이고 X-Real-IP 를 적지 않는다
// 이미지는 내려받지 않는다(compose 의 pull_policy: never). 호스트 포트는 실행마다 OS 가 비었다고 준 높은 번호다.
// Playwright 와 Chromium 은 --web 폴더(기본 저장소의 web/)에 설치된 것을 cookie_relay 처럼 createRequire 로 쓴다.
//
// 재는 것(README 의 1~6)
//   1 머리      nginx 와 Next 를 지나 대역에 닿는 Host, X-Forwarded-For, X-Real-IP, X-Forwarded-Proto 와 nginx 의 $remote_addr.
//               클라이언트가 그 셋을 지어 보낸 회차, 후보와 대조, nginx 를 거치지 않는 직접 길, 호스트의 LAN 주소로 건 길,
//               네트워크 안의 컨테이너가 건 길(양성 대조)
//   2 쿠키 줄   대역이 낸 Set-Cookie 두 줄(심기, 지우기)이 날 HTTPS 클라이언트와 브라우저(CDP)에 줄마다 닿는지, 저장소의 속성
//   3 다른 이름 admin.test 에서 쿠키를 심은 뒤 evil.test(같은 주소, 같은 포트)의 페이지가 보낸 fetch 에 쿠키가 실리는지
//   4 출처 머리 주소창 이동과 같은 이름의 다른 포트(방문자용 자리)에서 온 요청의 Sec-Fetch-Site
//   5 API 요청  Playwright 의 request.newContext() 와 브라우저 컨텍스트의 request 가 보내는 머리와 쿠키
//   6 렌더      발행 포트 후보 모양을 docker compose config 로 렌더한 값(띄우지 않는다)
//
// 표지(회차마다 재려는 상황이 실제로 났는지. 없으면 그 회차는 측정이 아니고 종료 코드가 0 이 아니다)
//   - 요청이 그 nginx 와 Next 를 지났다: 대역이 받은 X-Probe-Hop 이 그 설정의 이름이고(nginx 가 붙인다), x-forwarded-host 가
//     있고(Next 의 중계가 붙인다), TCP 상대가 관리 화면 컨테이너의 주소다. 직접 길은 X-Probe-Hop 이 없어야 한다
//   - 그 태그의 요청이 대역에 하나만 닿았다
//   - 지어 보낸 값이 nginx 에 실제로 닿았다: nginx 접근 기록(log_format probe)의 그 요청 줄에 지어 보낸 값이 있다
//   - 브라우저가 그 요청을 실제로 보냈다: CDP 의 requestWillBeSent 에 그 태그가 있다
//   - 쿠키가 실릴 수 있는 상황이었다: 그 요청 직전에 브라우저 저장소에 admin.test 의 쿠키 둘이 있다
//   - 렌더가 그 회차의 환경으로 났다: 렌더 결과의 PROBE_RENDER_CASE 가 그 회차의 이름이다
// 이 셈은 tools/probe_kit.py 의 Rounds 와 같은 뜻이다(본문이 예외로 끝나거나 mark 없이 끝나면 측정이 아니다).
//
// 결과는 쿠키 값, 포트, 컨테이너 주소를 이름표로 바꿔 찍고, 원본은 --out 폴더(없으면 임시 폴더)의 results.json 과
// compose 로그에 남긴다. 미리 적은 기대와 견주지 않는다. --keep 은 끝에 묶음을 내리지 않는다(손으로 볼 때).

import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import http from "node:http";
import https from "node:https";
import { createRequire } from "node:module";
import { createServer } from "node:net";
import { networkInterfaces, tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { parseArgs } from "node:util";

const HERE = import.meta.dirname;
const ROOT = join(HERE, "..", "..", "..", "..");
const COMPOSE = join(HERE, "compose.yaml");
const SHAPE = join(HERE, "compose.port-shape.yaml");
const NONCE = randomBytes(4).toString("hex");
const PROJECT = `aos-port-chain-${NONCE}`;
const FORGED = { xff: "203.0.113.7", xri: "203.0.113.8", xfp: "gopher" };
const SETTLE_MS = 4000;

const { values: args } = parseArgs({
  options: {
    web: { type: "string" },
    out: { type: "string" },
    keep: { type: "boolean", default: false },
    channel: { type: "string" },
  },
});
const WEB = resolve(args.web ?? join(ROOT, "web"));
const OUT = resolve(args.out ?? mkdtempSync(join(tmpdir(), "admin-port-chain-")));
mkdirSync(OUT, { recursive: true });

const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
const t = (id) => `${id}-${NONCE}`;

let load;
try {
  load = createRequire(join(WEB, "apps", "admin", "package.json"));
  load.resolve("@playwright/test");
} catch (error) {
  console.error(`Playwright 를 ${WEB} 에서 찾지 못했다. --web 에 의존성을 설치한 web 폴더를 준다: ${error.message}`);
  process.exit(2);
}

// ---------------------------------------------------------------------------------------------------------------------
// 회차의 셈(tools/probe_kit.py 의 Rounds 와 같은 뜻)

class Rounds {
  entries = [];
  async round(label, body) {
    const slot = {
      entry: null,
      mark(measured, result = "") {
        slot.entry = { label, measured, result };
      },
    };
    try {
      await body(slot);
    } catch (error) {
      this.entries.push({ label, measured: false, result: `예외: ${error?.stack ?? error}` });
      return;
    }
    this.entries.push(slot.entry ?? { label, measured: false, result: "표지를 적지 않았다" });
  }
  get measured() {
    return this.entries.filter((entry) => entry.measured);
  }
  get unmeasured() {
    return this.entries.filter((entry) => !entry.measured);
  }
  exitCode() {
    return this.measured.length > 0 && this.unmeasured.length === 0 ? 0 : 1;
  }
  summary() {
    const lines = [`측정 ${this.measured.length}회차, 측정 아님 ${this.unmeasured.length}회차`];
    for (const entry of this.unmeasured) lines.push(`측정 아님 ${entry.label}: ${entry.result}`);
    return lines.join("\n");
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// 이름표. 쿠키 값, 포트, 주소를 읽을 수 있는 이름으로 바꾼다. 원본은 results.json 의 raw 에 남는다.

const labels = [];
function label(value, name) {
  if (value === undefined || value === null || value === "") return;
  if (!labels.some(([known]) => known === String(value))) labels.push([String(value), name]);
}
function norm(value) {
  if (value === null || value === undefined) return value;
  if (typeof value !== "string") return JSON.parse(norm(JSON.stringify(value)));
  let text = value;
  for (const [known, name] of [...labels].sort((left, right) => right[0].length - left[0].length)) {
    const escaped = known.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    text = text.replace(new RegExp(`(?<![\\w.])${escaped}(?![\\w])`, "g"), name);
  }
  return text;
}

// ---------------------------------------------------------------------------------------------------------------------
// docker

function run(command, argv, { env = process.env, timeout = 120_000 } = {}) {
  const done = spawnSync(command, argv, { encoding: "utf-8", env, timeout, maxBuffer: 64 * 1024 * 1024 });
  return { status: done.status, stdout: done.stdout ?? "", stderr: done.stderr ?? "", error: done.error?.message ?? null };
}

let composeEnv = process.env;
const compose = (argv, timeout) =>
  run("docker", ["compose", "-p", PROJECT, "-f", COMPOSE, ...argv], { env: composeEnv, timeout });

function parseLines(text) {
  const trimmed = text.trim();
  if (trimmed === "") return [];
  if (trimmed.startsWith("[")) return JSON.parse(trimmed);
  return trimmed.split(/\r?\n/).map((line) => JSON.parse(line));
}

// ---------------------------------------------------------------------------------------------------------------------
// 포트와 인증서

async function freePort() {
  const server = createServer();
  await new Promise((done) => server.listen(0, "0.0.0.0", done));
  const { port } = server.address();
  await new Promise((done) => server.close(done));
  return port;
}

async function pickPorts(count) {
  const taken = new Set([80, 443, 3000, 8443]);
  const ports = [];
  while (ports.length < count) {
    const port = await freePort();
    if (port < 20000 || taken.has(port)) continue;
    taken.add(port);
    ports.push(port);
  }
  return ports;
}

function makeCert(folder) {
  mkdirSync(folder, { recursive: true });
  const key = join(folder, "privkey.pem");
  const cert = join(folder, "fullchain.pem");
  const made = run(
    "openssl",
    [
      ...["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cert, "-days", "2"],
      ...["-subj", "/CN=admin.test", "-addext", "subjectAltName=DNS:admin.test,DNS:evil.test"],
    ],
    { timeout: 60_000 },
  );
  if (made.status !== 0 || !existsSync(cert) || !existsSync(key)) {
    throw new Error(`openssl 로 인증서를 짓지 못했다: ${made.error ?? made.stderr}`);
  }
  return run("openssl", ["version"]).stdout.trim();
}

// ---------------------------------------------------------------------------------------------------------------------
// 대역의 기록과 날 HTTP

let stubPort = 0;
function stubLog() {
  return new Promise((done, fail) => {
    const request = http.get({ host: "127.0.0.1", port: stubPort, path: "/log?since=0", timeout: 10_000 }, (response) => {
      const chunks = [];
      response.on("data", (chunk) => chunks.push(chunk));
      response.on("end", () => {
        try {
          done(JSON.parse(Buffer.concat(chunks).toString("utf-8")));
        } catch (error) {
          fail(error);
        }
      });
    });
    request.on("timeout", () => request.destroy(new Error("대역의 기록을 읽다 시간을 넘겼다")));
    request.on("error", fail);
  });
}

/** 그 태그로 대역에 닿은 요청들. 메서드가 닿을 때까지(또는 SETTLE_MS) 기다린 뒤 겹침을 보려고 조금 더 기다린다. */
async function entriesOf(tag, method) {
  const deadline = Date.now() + SETTLE_MS;
  for (;;) {
    const found = (await stubLog()).filter((entry) => entry.tag === tag);
    if (found.some((entry) => method === undefined || entry.method === method)) {
      await sleep(300);
      return (await stubLog()).filter((entry) => entry.tag === tag);
    }
    if (Date.now() > deadline) return found;
    await sleep(100);
  }
}

function headerOf(entry, name) {
  if (entry === null || entry === undefined) return null;
  const found = entry.headers.filter(([key]) => key.toLowerCase() === name).map(([, value]) => value);
  return found.length === 0 ? null : found.join(" | ");
}

function rawRequest({ port, host = "127.0.0.1", hostHeader, path, method = "GET", headers = {}, body, plain = false }) {
  const client = plain ? http : https;
  return new Promise((done, fail) => {
    const request = client.request(
      {
        host,
        port,
        method,
        path,
        agent: false,
        timeout: 20_000,
        ...(plain ? {} : { servername: "admin.test", rejectUnauthorized: false }),
        headers: {
          Host: hostHeader ?? `admin.test:${port}`,
          ...headers,
          ...(body === undefined ? {} : { "Content-Length": Buffer.byteLength(body) }),
        },
      },
      (response) => {
        const chunks = [];
        response.on("data", (chunk) => chunks.push(chunk));
        response.on("end", () =>
          done({
            status: response.statusCode,
            setCookie: response.headers["set-cookie"] ?? [],
            setCookieRawCount: response.rawHeaders.filter((_, index) => index % 2 === 0)
              .filter((name) => name.toLowerCase() === "set-cookie").length,
            body: Buffer.concat(chunks).toString("utf-8"),
          }),
        );
      },
    );
    request.on("timeout", () => request.destroy(new Error("날 요청이 시간을 넘겼다")));
    request.on("error", fail);
    if (body !== undefined) request.write(body);
    request.end();
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// 표지와 고른 머리

const topo = {};

/** 요청이 그 길을 지났다는 표지. 빈 배열이면 다 있다. */
function chainProblems(entries, method, hop) {
  const matching = entries.filter((entry) => method === undefined || entry.method === method);
  if (matching.length !== 1) return [`대역에 닿은 ${method ?? ""} 요청이 ${matching.length}개다`];
  const entry = matching[0];
  const problems = [];
  const seenHop = headerOf(entry, "x-probe-hop");
  if (hop === "direct" ? seenHop !== null : seenHop !== hop) problems.push(`X-Probe-Hop 이 ${seenHop} 이다(기대한 길 ${hop})`);
  if (headerOf(entry, "x-forwarded-host") === null) problems.push("x-forwarded-host 가 없다(Next 의 중계를 지나지 않았다)");
  if (entry.peer !== topo.admin?.ip) problems.push(`TCP 상대가 관리 화면 컨테이너가 아니다(${entry.peer})`);
  return problems;
}

const PICKED = [
  "host",
  "x-forwarded-for",
  "x-real-ip",
  "x-forwarded-proto",
  "x-forwarded-host",
  "x-forwarded-port",
  "forwarded",
  "origin",
  "sec-fetch-site",
  "sec-fetch-mode",
  "cookie",
  "x-probe-remote-addr",
];

function picked(entry) {
  if (entry === null || entry === undefined) return null;
  const out = { peer: norm(entry.peer) };
  for (const name of PICKED) out[name] = norm(headerOf(entry, name));
  out.names = entry.headers.map(([key]) => key.toLowerCase());
  return out;
}

function nginxLine(service, tag) {
  const logs = compose(["logs", "--no-color", "--no-log-prefix", service], 60_000);
  const line = logs.stdout.split(/\r?\n/).find((text) => text.startsWith("probe ") && text.includes(tag));
  if (line === undefined) return null;
  const field = (key) => new RegExp(`${key}="([^"]*)"`).exec(line)?.[1] ?? null;
  return {
    remote: /remote=(\S+)/.exec(line)?.[1] ?? null,
    xff: field("xff"),
    xri: field("xri"),
    xfp: field("xfp"),
    host: field("host"),
  };
}

const SERVICE_OF = { candidate: "proxy", control: "proxy_control" };

// ---------------------------------------------------------------------------------------------------------------------
// 브라우저 쪽 기록(CDP). cookie_relay 의 기록기를 줄였다.

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
      cdp.on("Network.requestWillBeSentExtraInfo", (event) => requestCookies.set(event.requestId, event.associatedCookies));
      cdp.on("Network.responseReceivedExtraInfo", (event) => responses.set(event.requestId, event));
    },
    attempted: (tag, method) => wait(() => (find(tag, method) === null ? null : true)).then((found) => found === true),
    async cookies(tag, method) {
      const associated = await wait(() => {
        const id = find(tag, method);
        return id === null ? null : requestCookies.get(id);
      });
      if (associated === null) return null;
      return {
        sent: associated.filter((item) => item.blockedReasons.length === 0).map((item) => `${item.cookie.name}@${item.cookie.domain}`).sort(),
        withheld: associated
          .filter((item) => item.blockedReasons.length > 0)
          .map((item) => `${item.cookie.name}@${item.cookie.domain}: ${[...item.blockedReasons].sort().join(",")}`)
          .sort(),
      };
    },
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

function jarLines(cookies) {
  return cookies
    .filter((cookie) => cookie.name.startsWith("__Host-aos_"))
    .map(
      (cookie) =>
        `${cookie.name}=${norm(cookie.value)}; domain=${cookie.domain}; path=${cookie.path}; httpOnly=${cookie.httpOnly}; ` +
        `secure=${cookie.secure}; sameSite=${cookie.sameSite}; ` +
        `${cookie.expires === -1 ? "session" : `expires(+${Math.round(cookie.expires - Date.now() / 1000)}s)`}`,
    )
    .sort();
}

const hasAdminCookies = (cookies) =>
  ["__Host-aos_at", "__Host-aos_rt"].every((name) => cookies.some((cookie) => cookie.name === name && cookie.domain === "admin.test"));

/** 대역이 낸 쿠키 값에 이름표를 단다. 누가 심었는지(admin, evil, api …)를 이름표에 싣는다. */
function labelSetCookies(entry, who) {
  for (const line of entry?.set_cookie ?? []) {
    const [pair] = line.split(";");
    const [name, value] = pair.split("=");
    if (value) label(value, `<${name.endsWith("_at") ? "at" : "rt"}(${who})>`);
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// 6. 렌더(띄우지 않는다)

async function renderRounds(rounds, facts) {
  const emptyEnv = join(OUT, "empty.env");
  writeFileSync(emptyEnv, "");
  const fileEnv = join(OUT, "shape.env");
  writeFileSync(fileEnv, "AGENT_OS_ADMIN_ADDRESS=127.0.0.1\nAGENT_OS_ADMIN_PORT=28443\n");
  const cases = [
    { id: "default", given: {}, envFile: emptyEnv },
    { id: "port", given: { AGENT_OS_ADMIN_PORT: "18443" }, envFile: emptyEnv },
    { id: "loopback", given: { AGENT_OS_ADMIN_ADDRESS: "127.0.0.1" }, envFile: emptyEnv },
    { id: "both", given: { AGENT_OS_ADMIN_ADDRESS: "127.0.0.1", AGENT_OS_ADMIN_PORT: "18443" }, envFile: emptyEnv },
    { id: "empty", given: { AGENT_OS_ADMIN_ADDRESS: "", AGENT_OS_ADMIN_PORT: "" }, envFile: emptyEnv },
    { id: "envfile", given: {}, envFile: fileEnv },
    { id: "bad-port", given: { AGENT_OS_ADMIN_PORT: "abc" }, envFile: emptyEnv },
  ];
  facts.render = {};
  for (const item of cases) {
    await rounds.round(`6-렌더-${item.id}`, async (slot) => {
      const env = { ...process.env };
      delete env.AGENT_OS_ADMIN_ADDRESS;
      delete env.AGENT_OS_ADMIN_PORT;
      Object.assign(env, { PROBE_RENDER_CASE: item.id }, item.given);
      const done = run(
        "docker",
        ["compose", "-p", `aos-port-shape-${NONCE}`, "-f", SHAPE, "--env-file", item.envFile, "config", "--format", "json"],
        { env, timeout: 60_000 },
      );
      const envFile = item.envFile === fileEnv ? "AGENT_OS_ADMIN_ADDRESS=127.0.0.1, AGENT_OS_ADMIN_PORT=28443" : "빈 파일";
      if (done.status !== 0) {
        facts.render[item.id] = { given: item.given, envFile, status: done.status, stderr: done.stderr.trim() };
        // 실패한 렌더는 그 회차의 값이 compose 에 닿았다는 것을 오류 글에 그 값이 있는 것으로 본다.
        const reached = Object.values(item.given).some((value) => value !== "" && done.stderr.includes(value));
        slot.mark(reached, reached ? `렌더 실패(종료 ${done.status})` : `렌더 실패인데 오류 글에 그 회차의 값이 없다: ${done.stderr.trim()}`);
        return;
      }
      const rendered = JSON.parse(done.stdout);
      const service = rendered.services?.proxy;
      const ports = (service?.ports ?? []).map((entry) => ({
        host_ip: entry.host_ip ?? null,
        published: entry.published ?? null,
        target: entry.target,
        protocol: entry.protocol ?? null,
      }));
      facts.render[item.id] = { given: item.given, envFile, status: 0, ports };
      const ok = service?.environment?.PROBE_RENDER_CASE === item.id && ports.some((entry) => entry.target === 9443);
      const admin = ports.find((entry) => entry.target === 9443);
      slot.mark(ok, ok ? `${admin.host_ip}:${admin.published}->9443` : `렌더 결과에 그 회차의 표지나 9443 줄이 없다`);
    });
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// 1·2. 날 HTTP 로 건 회차

async function headerRound(rounds, facts, { label: name, id, port, hop, host = "127.0.0.1", forged = false, plain = false }) {
  await rounds.round(name, async (slot) => {
    const tag = t(id);
    const headers = forged
      ? { "X-Forwarded-For": FORGED.xff, "X-Real-IP": FORGED.xri, "X-Forwarded-Proto": FORGED.xfp }
      : {};
    const answer = await rawRequest({
      port,
      host,
      plain,
      path: `/api/echo?tag=${tag}`,
      headers,
      hostHeader: plain ? `127.0.0.1:${port}` : `admin.test:${port}`,
    });
    const entries = await entriesOf(tag, "GET");
    const problems = chainProblems(entries, "GET", hop);
    let nginx = null;
    if (hop !== "direct") {
      nginx = nginxLine(SERVICE_OF[hop], tag);
      if (nginx === null) problems.push("nginx 접근 기록에 그 요청이 없다");
      else if (forged && (nginx.xff !== FORGED.xff || nginx.xri !== FORGED.xri || nginx.xfp !== FORGED.xfp)) {
        problems.push(`지어 보낸 값이 nginx 에 그대로 닿지 않았다(${JSON.stringify(nginx)})`);
      }
    }
    const entry = entries.find((item) => item.method === "GET") ?? null;
    facts.headers[name] = {
      client: norm(host),
      sent: forged ? FORGED : "지어 보낸 머리 없음",
      status: answer.status,
      nginxSaw: norm(nginx),
      atServe: picked(entry),
    };
    slot.mark(
      problems.length === 0,
      problems.length === 0
        ? `XFF=${norm(headerOf(entry, "x-forwarded-for"))} XRI=${norm(headerOf(entry, "x-real-ip"))} XFP=${headerOf(entry, "x-forwarded-proto")}`
        : problems.join("; "),
    );
  });
}

function lanAddress() {
  const found = [];
  for (const [name, list] of Object.entries(networkInterfaces())) {
    for (const item of list ?? []) {
      if (item.family === "IPv4" && !item.internal && !item.address.startsWith("169.254.")) found.push({ name, address: item.address });
    }
  }
  // WSL 과 Hyper-V 의 가상 어댑터(vEthernet)보다 실제 어댑터를 먼저 고른다.
  found.sort((left, right) => Number(left.name.startsWith("vEthernet")) - Number(right.name.startsWith("vEthernet")));
  return found[0] ?? null;
}

async function cookieLineRound(rounds, facts, { label: name, id, path, port }) {
  await rounds.round(name, async (slot) => {
    const tag = t(id);
    const answer = await rawRequest({ port, path: `${path}?tag=${tag}` });
    const entries = await entriesOf(tag, "GET");
    const problems = chainProblems(entries, "GET", "candidate");
    const entry = entries.find((item) => item.method === "GET") ?? null;
    labelSetCookies(entry, "raw");
    const same = JSON.stringify(answer.setCookie) === JSON.stringify(entry?.set_cookie ?? null);
    facts.cookieLines[name] = {
      atServe: norm(entry?.set_cookie ?? null),
      atClient: norm(answer.setCookie),
      rawLineCount: answer.setCookieRawCount,
      same,
    };
    if ((entry?.set_cookie ?? []).length !== 2) problems.push("대역이 Set-Cookie 두 줄을 내지 않았다");
    slot.mark(problems.length === 0, problems.length === 0 ? (same ? "줄마다 같다" : "다르다") : problems.join("; "));
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// 브라우저 회차의 뼈대

/** 페이지가 요청 하나를 보내고, 대역의 기록과 CDP 의 기록을 맞대 표지를 본다. */
async function browserRequest(slot, { context, recorder, page, tag, method, send, hop = "candidate", needAdminCookies = true }) {
  if (page === null) throw new Error("이 회차의 페이지를 열지 못했다");
  const before = await context.cookies();
  const problems = [];
  if (needAdminCookies && !hasAdminCookies(before)) problems.push("요청 직전 저장소에 admin.test 의 쿠키 둘이 없다");
  const fetched = await send();
  const entries = await entriesOf(tag, method);
  problems.push(...chainProblems(entries, method, hop));
  if (!(await recorder.attempted(tag, method))) problems.push("CDP 에 그 요청이 없다");
  const entry = entries.find((item) => item.method === method) ?? null;
  const fact = {
    page: norm(new URL(page.url()).origin),
    fetch: fetched ?? null,
    atServe: picked(entry),
    browserCookies: norm(await recorder.cookies(tag, method)),
    reached: entries.map((item) => item.method),
  };
  return { problems, fact, entry };
}

function finish(slot, problems, result) {
  slot.mark(problems.length === 0, problems.length === 0 ? result : problems.join("; "));
}

// ---------------------------------------------------------------------------------------------------------------------
// 본문

const rounds = new Rounds();
const facts = { headers: {}, cookieLines: {}, browser: {}, apiContext: {}, render: {} };
const info = { project: PROJECT, out: OUT, web: WEB, versions: {}, ports: {}, topology: topo };
let failure = null;
let browser = null;
let torn = false;

function teardown() {
  if (torn) return { skipped: true };
  torn = true;
  if (args.keep) {
    console.log(`--keep: 묶음을 내리지 않았다. 내리는 명령: docker compose -p ${PROJECT} -f ${COMPOSE} down -v --remove-orphans`);
    return { kept: true };
  }
  const down = compose(["down", "-v", "--remove-orphans", "--timeout", "5"], 180_000);
  const left = run("docker", ["ps", "-a", "-q", "--filter", `label=com.docker.compose.project=${PROJECT}`]).stdout.trim();
  const networks = run("docker", ["network", "ls", "-q", "--filter", `label=com.docker.compose.project=${PROJECT}`]).stdout.trim();
  return { status: down.status, containersLeft: left, networksLeft: networks, stderr: down.stderr.trim().split(/\r?\n/).slice(-5) };
}

process.on("SIGINT", () => {
  console.error("끊겼다. 묶음을 내린다.");
  console.error(JSON.stringify(teardown()));
  process.exit(130);
});

try {
  const [adminPort, visitorPort, controlPort, directPort, stub] = await pickPorts(5);
  stubPort = stub;
  info.ports = { adminPort, visitorPort, controlPort, directPort, stubPort };
  label(adminPort, "<관리 포트>");
  label(visitorPort, "<방문자 포트>");
  label(controlPort, "<대조 포트>");
  label(directPort, "<직접 포트>");
  label(NONCE, "<N>");
  const tlsDir = join(OUT, "tls");
  composeEnv = {
    ...process.env,
    PROBE_ADMIN_PORT: String(adminPort),
    PROBE_VISITOR_PORT: String(visitorPort),
    PROBE_CONTROL_PORT: String(controlPort),
    PROBE_DIRECT_PORT: String(directPort),
    PROBE_STUB_PORT: String(stubPort),
    PROBE_TLS_DIR: tlsDir,
  };
  info.versions.openssl = makeCert(tlsDir);

  // 6 은 묶음 없이 돈다.
  await renderRounds(rounds, facts);

  console.log(`묶음을 띄운다: ${PROJECT}`);
  const up = compose(["up", "-d", "--wait", "--wait-timeout", "300"], 420_000);
  info.up = { status: up.status, stderr: up.stderr.trim().split(/\r?\n/).slice(-15) };
  if (up.status !== 0) throw new Error(`docker compose up 이 ${up.status} 로 끝났다: ${up.stderr}`);

  // 컨테이너의 주소와 네트워크.
  for (const row of parseLines(compose(["ps", "-a", "--format", "json"]).stdout)) {
    const networks = JSON.parse(run("docker", ["inspect", "--format", "{{json .NetworkSettings.Networks}}", row.ID]).stdout);
    const [network] = Object.values(networks);
    topo[row.Service] = { ip: network.IPAddress, gateway: network.Gateway };
  }
  const gateway = topo.serve?.gateway;
  label(topo.admin?.ip, "<관리 화면 컨테이너>");
  label(topo.proxy?.ip, "<프록시 컨테이너>");
  label(topo.proxy_control?.ip, "<대조 프록시 컨테이너>");
  label(topo.serve?.ip, "<serve 대역 컨테이너>");
  label(gateway, "<안쪽 게이트웨이>");
  const ipam = run("docker", ["network", "inspect", "--format", "{{json .IPAM.Config}}", `${PROJECT}_default`]).stdout.trim();
  info.network = ipam;

  // 판.
  info.versions.docker = run("docker", ["version", "--format", "{{.Server.Version}}"]).stdout.trim();
  info.versions.compose = run("docker", ["compose", "version", "--short"]).stdout.trim();
  info.versions.nginx = compose(["exec", "-T", "proxy", "nginx", "-v"]).stderr.trim();
  info.versions.next = compose(["exec", "-T", "-w", "/app/web/apps/admin", "admin", "node", "-p", "require('next/package.json').version"]).stdout.trim();
  info.versions.adminImage = run("docker", ["image", "inspect", "--format", "{{.Id}} {{json .Config.Labels}}", composeEnv.PROBE_ADMIN_IMAGE ?? "agent-os-e2e/agent-os-admin:0.1.0-rc.1"]).stdout.trim();
  info.versions.nginxImage = run("docker", ["image", "inspect", "--format", "{{.Id}} {{json .RepoDigests}}", composeEnv.PROBE_NGINX_IMAGE ?? "nginx:alpine"]).stdout.trim();

  // 길이 열릴 때까지(관리 화면이 건강해도 nginx 가 이름을 풀기까지 잠깐 걸릴 수 있다).
  const readyBy = Date.now() + 90_000;
  for (let attempt = 0; ; attempt += 1) {
    const tag = t(`ready${attempt}`);
    const answer = await rawRequest({ port: adminPort, path: `/api/echo?tag=${tag}` }).catch((error) => ({ status: String(error) }));
    if (answer.status === 200 && (await stubLog()).some((entry) => entry.tag === tag)) break;
    if (Date.now() > readyBy) throw new Error(`후보 길이 열리지 않았다(마지막 응답 ${answer.status})`);
    await sleep(1000);
  }
  info.versions.python = await new Promise((done) =>
    http.get({ host: "127.0.0.1", port: stubPort, path: "/health" }, (response) => {
      const chunks = [];
      response.on("data", (chunk) => chunks.push(chunk));
      response.on("end", () => done(JSON.parse(Buffer.concat(chunks).toString("utf-8")).python));
    }),
  );
  console.log(`판: ${JSON.stringify(info.versions)}`);

  // 1. 머리.
  const lan = lanAddress();
  if (lan !== null) label(lan.address, "<호스트의 LAN 주소>");
  const headerCases = [
    { label: "1-후보-루프백", id: "h-cand-lo", port: adminPort, hop: "candidate" },
    { label: "1-후보-루프백-지어보냄", id: "h-cand-lo-forged", port: adminPort, hop: "candidate", forged: true },
    { label: "1-후보-LAN주소", id: "h-cand-lan", port: adminPort, hop: "candidate", host: lan?.address ?? "없음" },
    { label: "1-대조-루프백", id: "h-ctrl-lo", port: controlPort, hop: "control" },
    { label: "1-대조-루프백-지어보냄", id: "h-ctrl-lo-forged", port: controlPort, hop: "control", forged: true },
    { label: "1-직접-루프백", id: "h-direct-lo", port: directPort, hop: "direct", plain: true },
    { label: "1-직접-루프백-지어보냄", id: "h-direct-lo-forged", port: directPort, hop: "direct", plain: true, forged: true },
  ];
  for (const item of headerCases) await headerRound(rounds, facts, item);
  info.lan = lan === null ? null : { adapter: lan.name };

  // 네트워크 안의 컨테이너가 프록시에 건 길(주소 변환이 없는 길의 양성 대조).
  await rounds.round("1-안쪽-컨테이너", async (slot) => {
    const tag = t("h-inner");
    const done = compose(["exec", "-T", "serve", "python", "-I", "/probe/serve_stub.py", "client", "proxy", "9443", tag], 60_000);
    const entries = await entriesOf(tag, "GET");
    const problems = chainProblems(entries, "GET", "candidate");
    if (done.status !== 0 || !done.stdout.includes(tag)) problems.push(`안쪽 클라이언트가 ${done.status} 로 끝났다: ${done.stderr.trim()}`);
    const nginx = nginxLine("proxy", tag);
    if (nginx === null) problems.push("nginx 접근 기록에 그 요청이 없다");
    const entry = entries.find((item) => item.method === "GET") ?? null;
    facts.headers["1-안쪽-컨테이너"] = { client: "<serve 대역 컨테이너>(compose 네트워크 안)", status: done.status, nginxSaw: norm(nginx), atServe: picked(entry) };
    finish(slot, problems, `nginx 가 본 주소 ${norm(nginx?.remote)}`);
  });

  // 2. 날 HTTP 로 본 Set-Cookie 줄.
  await cookieLineRound(rounds, facts, { label: "2-날HTTPS-심기", id: "c-raw-set", path: "/api/set", port: adminPort });
  await cookieLineRound(rounds, facts, { label: "2-날HTTPS-지우기", id: "c-raw-clear", path: "/api/clear", port: adminPort });

  // 브라우저.
  const { chromium, request: apiRequest } = load("@playwright/test");
  info.versions.playwright = load("@playwright/test/package.json").version;
  browser = await chromium.launch({
    args: ["--host-resolver-rules=MAP admin.test 127.0.0.1, MAP evil.test 127.0.0.1"],
    ...(args.channel === undefined ? {} : { channel: args.channel }),
  });
  info.versions.chromium = browser.version();
  info.versions.chromiumChannel = args.channel ?? "기본(headless shell)";
  const A = `https://admin.test:${adminPort}`;
  const E = `https://evil.test:${adminPort}`;
  const V = `https://admin.test:${visitorPort}`;
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const recorder = newRecorder();
  const tryOpen = (url) => openPage(context, recorder, url).catch((error) => {
    console.error(`페이지를 열지 못했다 ${url}: ${error.message}`);
    return null;
  });

  const pageA = await tryOpen(`${A}/api/page?tag=${t("a-page")}`);

  await rounds.round("2-브라우저-심기", async (slot) => {
    if (pageA === null) throw new Error("admin.test 페이지를 열지 못했다");
    const tag = t("b-set");
    const fetched = await pageFetch(pageA, `/api/set?tag=${tag}`);
    const entries = await entriesOf(tag, "GET");
    const problems = chainProblems(entries, "GET", "candidate");
    const entry = entries.find((item) => item.method === "GET") ?? null;
    labelSetCookies(entry, "admin");
    const answer = await recorder.response(tag, "GET");
    if (answer === null) problems.push("CDP 가 그 응답을 적지 않았다");
    const jar = await context.cookies();
    const same = JSON.stringify(answer?.setCookie ?? null) === JSON.stringify(entry?.set_cookie ?? null);
    facts.browser["2-브라우저-심기"] = {
      fetch: fetched,
      atServe: norm(entry?.set_cookie ?? null),
      atBrowser: norm(answer?.setCookie ?? null),
      blocked: answer?.blocked ?? null,
      same,
      jar: jarLines(jar),
    };
    finish(slot, problems, `${same ? "줄마다 같다" : "다르다"}, 거절 ${answer?.blocked?.length ?? "?"}줄, 저장소 ${jarLines(jar).length}개`);
  });

  // 3. 진짜 이름(양성 대조)과 다른 이름.
  const adminRequest = async (name, id, init) => {
    await rounds.round(name, async (slot) => {
      const tag = t(id);
      const method = init?.method ?? "GET";
      const { problems, fact } = await browserRequest(slot, {
        context,
        recorder,
        page: pageA,
        tag,
        method,
        send: () => pageFetch(pageA, `/api/echo?tag=${tag}`, init),
      });
      facts.browser[name] = fact;
      finish(slot, problems, `Cookie=${fact.atServe?.cookie ?? "없음"} SFS=${fact.atServe?.["sec-fetch-site"]} Origin=${fact.atServe?.origin ?? "없음"}`);
    });
  };
  await adminRequest("3-진짜이름-GET", "r-admin-get");
  await adminRequest("3-진짜이름-POST", "r-admin-post", { method: "POST", body: "a=1" });

  const pageE = await tryOpen(`${E}/api/page?tag=${t("e-page")}`);
  const evilRequest = async (name, id, target, init, extra = {}) => {
    await rounds.round(name, async (slot) => {
      const tag = t(id);
      const method = init?.method ?? "GET";
      const { problems, fact } = await browserRequest(slot, {
        context,
        recorder,
        page: pageE,
        tag,
        method,
        send: () => pageFetch(pageE, `${target}/api/echo?tag=${tag}`, init),
        ...extra,
      });
      if (pageE !== null && new URL(pageE.url()).hostname !== "evil.test") problems.push("페이지가 evil.test 가 아니다");
      facts.browser[name] = fact;
      finish(slot, problems, `Cookie=${fact.atServe?.cookie ?? "없음"} SFS=${fact.atServe?.["sec-fetch-site"]} Origin=${fact.atServe?.origin ?? "없음"}`);
    });
  };
  await evilRequest("3-다른이름-GET", "r-evil-get", "");
  await evilRequest("3-다른이름-POST", "r-evil-post", "", { method: "POST", body: "a=1" });
  await evilRequest("3-다른이름에서-진짜이름으로", "r-evil-cross", A, { credentials: "include", mode: "no-cors" });

  // 갈래: evil.test 에도 쿠키가 실리는 길이 있는지(그 이름으로 심은 쿠키), 그 뒤 admin.test 의 쿠키가 그대로인지.
  await rounds.round("3-다른이름-자기쿠키", async (slot) => {
    if (pageE === null || pageA === null) throw new Error("페이지를 열지 못했다");
    const setTag = t("r-evil-set");
    await pageFetch(pageE, `/api/set?tag=${setTag}`);
    const setEntries = await entriesOf(setTag, "GET");
    const problems = chainProblems(setEntries, "GET", "candidate");
    labelSetCookies(setEntries[0], "evil");
    const jarAfterSet = await context.cookies();
    if (!["__Host-aos_at", "__Host-aos_rt"].every((name) => jarAfterSet.some((cookie) => cookie.name === name && cookie.domain === "evil.test"))) {
      problems.push("evil.test 의 쿠키 둘이 저장소에 들지 않았다");
    }
    const own = await browserRequest(slot, {
      context,
      recorder,
      page: pageE,
      tag: t("r-evil-own"),
      method: "GET",
      send: () => pageFetch(pageE, `/api/echo?tag=${t("r-evil-own")}`),
    });
    const back = await browserRequest(slot, {
      context,
      recorder,
      page: pageA,
      tag: t("r-admin-after"),
      method: "GET",
      send: () => pageFetch(pageA, `/api/echo?tag=${t("r-admin-after")}`),
    });
    problems.push(...own.problems, ...back.problems);
    facts.browser["3-다른이름-자기쿠키"] = { jar: jarLines(jarAfterSet), evilOwn: own.fact, adminAfter: back.fact };
    finish(slot, problems, `evil.test 요청의 Cookie=${own.fact.atServe?.cookie ?? "없음"}, admin.test 요청의 Cookie=${back.fact.atServe?.cookie ?? "없음"}`);
  });

  // 4. 주소창 이동과 같은 이름의 다른 포트.
  await rounds.round("4-주소창-이동", async (slot) => {
    const tag = t("n-nav");
    const page = await context.newPage();
    await recorder.attach(context, page);
    const { problems, fact } = await browserRequest(slot, {
      context,
      recorder,
      page,
      tag,
      method: "GET",
      send: async () => {
        await page.goto(`${A}/api/echo?tag=${tag}`, { waitUntil: "load" });
        return "이동";
      },
    });
    facts.browser["4-주소창-이동"] = fact;
    finish(slot, problems, `SFS=${fact.atServe?.["sec-fetch-site"]} mode=${fact.atServe?.["sec-fetch-mode"]} Cookie=${fact.atServe?.cookie ?? "없음"}`);
  });

  const pageV = await tryOpen(`${V}/probe/visitor-page`);
  const visitorTitle = pageV === null ? null : await pageV.title();
  const visitorRequest = async (name, id, send) => {
    await rounds.round(name, async (slot) => {
      const tag = t(id);
      const { problems, fact } = await browserRequest(slot, {
        context,
        recorder,
        page: pageV,
        tag,
        method: id.endsWith("post") ? "POST" : "GET",
        send: () => send(tag),
      });
      if (visitorTitle !== "visitor") problems.push(`방문자 포트의 페이지가 아니다(제목 ${visitorTitle})`);
      facts.browser[name] = fact;
      finish(slot, problems, `SFS=${fact.atServe?.["sec-fetch-site"]} Origin=${fact.atServe?.origin ?? "없음"} Cookie=${fact.atServe?.cookie ?? "없음"}`);
    });
  };
  await visitorRequest("4-다른포트-GET", "v-get", (tag) => pageFetch(pageV, `${A}/api/echo?tag=${tag}`, { credentials: "include" }));
  await visitorRequest("4-다른포트-POST", "v-post", (tag) =>
    pageFetch(pageV, `${A}/api/echo?tag=${tag}`, { method: "POST", body: "a=1", credentials: "include" }),
  );
  await visitorRequest("4-다른포트-링크", "v-link", async (tag) => {
    await pageV.evaluate((href) => {
      const link = document.createElement("a");
      link.id = "l";
      link.href = href;
      link.textContent = "go";
      document.body.append(link);
    }, `${A}/api/echo?tag=${tag}`);
    const arrived = pageV.waitForURL((url) => url.searchParams.get("tag") === tag, { waitUntil: "load" });
    await pageV.click("#l");
    await arrived;
    return "링크 이동";
  });

  // 2. 지우기(브라우저).
  await rounds.round("2-브라우저-지우기", async (slot) => {
    if (pageA === null) throw new Error("admin.test 페이지를 열지 못했다");
    const tag = t("b-clear");
    const before = await context.cookies();
    const problems = hasAdminCookies(before) ? [] : ["지우기 직전 저장소에 admin.test 의 쿠키 둘이 없다"];
    const fetched = await pageFetch(pageA, `/api/clear?tag=${tag}`);
    const entries = await entriesOf(tag, "GET");
    problems.push(...chainProblems(entries, "GET", "candidate"));
    const entry = entries.find((item) => item.method === "GET") ?? null;
    const answer = await recorder.response(tag, "GET");
    if (answer === null) problems.push("CDP 가 그 응답을 적지 않았다");
    const after = await context.cookies();
    const same = JSON.stringify(answer?.setCookie ?? null) === JSON.stringify(entry?.set_cookie ?? null);
    facts.browser["2-브라우저-지우기"] = {
      fetch: fetched,
      atServe: norm(entry?.set_cookie ?? null),
      atBrowser: norm(answer?.setCookie ?? null),
      blocked: answer?.blocked ?? null,
      same,
      jarBefore: jarLines(before),
      jarAfter: jarLines(after),
    };
    finish(slot, problems, `${same ? "줄마다 같다" : "다르다"}, 지운 뒤 admin.test 쿠키 ${after.filter((cookie) => cookie.domain === "admin.test").length}개`);
  });
  await context.close();

  // 5. API 요청 문맥.
  const B = `https://127.0.0.1:${adminPort}`;
  const apiRound = async (name, id, call) => {
    await rounds.round(name, async (slot) => {
      const tag = t(id);
      const method = id.endsWith("post") ? "POST" : "GET";
      const response = await call(`${B}/api/echo?tag=${tag}`);
      const entries = await entriesOf(tag, method);
      const problems = chainProblems(entries, method, "candidate");
      const entry = entries.find((item) => item.method === method) ?? null;
      const fact = { status: response.status(), atServe: picked(entry), all: norm(entry?.headers ?? null) };
      facts.apiContext[name] = fact;
      const browserish = (entry?.headers ?? []).filter(([key]) => /^(origin|sec-fetch-.*)$/i.test(key)).map(([key, value]) => `${key}: ${value}`);
      finish(slot, problems, browserish.length === 0 ? "Origin 과 Sec-Fetch-* 없음" : browserish.join(", "));
    });
  };
  const standalone = await apiRequest.newContext({ ignoreHTTPSErrors: true });
  await apiRound("5-독립문맥-GET", "a-solo-get", (url) => standalone.get(url));
  await apiRound("5-독립문맥-POST", "a-solo-post", (url) => standalone.post(url, { data: { name: "probe" } }));
  const bound = await browser.newContext({ ignoreHTTPSErrors: true });
  await apiRound("5-브라우저문맥-GET", "a-bound-get", (url) => bound.request.get(url));
  await apiRound("5-브라우저문맥-POST", "a-bound-post", (url) => bound.request.post(url, { data: { name: "probe" } }));

  // 덤: API 문맥이 받은 Set-Cookie 를 다음 요청에 싣는가(e2e 가 로그인 경로를 직접 부른 뒤의 모양).
  const apiCookieRound = async (name, id, requestContext, followWithPage) => {
    await rounds.round(name, async (slot) => {
      const setTag = t(`${id}-set`);
      const echoTag = t(`${id}-echo`);
      const setResponse = await requestContext.get(`${B}/api/set?tag=${setTag}`);
      const setEntries = await entriesOf(setTag, "GET");
      const problems = chainProblems(setEntries, "GET", "candidate");
      labelSetCookies(setEntries[0], id);
      const setLines = setResponse.headersArray().filter((item) => item.name.toLowerCase() === "set-cookie").map((item) => item.value);
      if (setLines.length !== 2) problems.push(`API 문맥이 받은 Set-Cookie 가 ${setLines.length}줄이다`);
      if (followWithPage) {
        const page = await bound.newPage();
        await page.goto(`${B}/api/echo?tag=${echoTag}`, { waitUntil: "load" });
      } else {
        await requestContext.get(`${B}/api/echo?tag=${echoTag}`);
      }
      const echoEntries = await entriesOf(echoTag, "GET");
      problems.push(...chainProblems(echoEntries, "GET", "candidate"));
      const stored = followWithPage ? await bound.cookies() : (await requestContext.storageState()).cookies;
      const cookie = norm(headerOf(echoEntries[0], "cookie"));
      facts.apiContext[name] = {
        setLinesAtContext: norm(setLines),
        stored: jarLines(stored),
        nextRequestCookie: cookie,
        nextBy: followWithPage ? "같은 브라우저 문맥의 페이지 이동" : "같은 API 문맥",
      };
      finish(slot, problems, `다음 요청의 Cookie=${cookie ?? "없음"}`);
    });
  };
  await apiCookieRound("5-독립문맥-쿠키", "a-solo-jar", standalone, false);
  await apiCookieRound("5-브라우저문맥-쿠키", "a-bound-jar", bound.request, true);
  await standalone.dispose();
  await bound.close();
} catch (error) {
  failure = String(error?.stack ?? error);
  console.error(`실행이 멈췄다: ${failure}`);
} finally {
  if (browser !== null) await browser.close().catch(() => undefined);
  for (const service of ["proxy", "proxy_control", "admin", "serve"]) {
    const logs = compose(["logs", "--no-color", "--timestamps", service], 60_000);
    writeFileSync(join(OUT, `compose-${service}.log`), `${logs.stdout}\n${logs.stderr}`);
  }
  // 대역의 기록은 내리기 전에 읽는다.
  const raw = stubPort === 0 ? null : await stubLog().catch(() => null);
  info.teardown = teardown();
  writeFileSync(join(OUT, "results.json"), `${JSON.stringify({ info, facts, rounds: rounds.entries, failure, labels, raw }, null, 2)}\n`);
}

console.log("\n===== 결과(이름표로 바꾼 값) =====");
console.log(JSON.stringify({ topology: norm(topo), facts }, null, 2));
console.log(`\n원본: ${join(OUT, "results.json")}`);
console.log(`내림: ${JSON.stringify(info.teardown)}`);
console.log(rounds.summary());
const tornOk = args.keep || (info.teardown?.status === 0 && info.teardown?.containersLeft === "" && info.teardown?.networksLeft === "");
const code = failure === null && tornOk ? rounds.exitCode() : 1;
console.log(`종료 코드 ${code}${failure === null ? "" : " (실행이 멈췄다)"}${tornOk ? "" : " (묶음을 다 내리지 못했다)"}`);
process.exit(code);
