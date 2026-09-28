// web-admin 프로브: Next 서버와 파이썬 채널 사이 배치를 고르려고 잰다. 결정은 하지 않고 숫자만 낸다.
//   node next_measure.mjs <appDir> [section...]
// appDir  next_app/ 사본에 `pnpm install`을 마친 폴더(저장소 밖). node_modules와 .next*는 거기에만 생긴다
// section bind origin sse compress abort headers action gap gaplong   (없으면 gaplong 밖 전부. gaplong은 5분 넘게 걸린다)
//
// 쓰는 포트: Next 3000, 상류 8765(next_sse_upstream.mjs를 이 스크립트가 띄운다). 둘 다 비어 있어야 한다.
// 띄운 프로세스는 섹션마다 트리째 내린다(Windows는 taskkill /T /F).
import { spawn, spawnSync } from "node:child_process";
import http from "node:http";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { measure, verdict } from "./next_sse_client.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.resolve(process.argv[2] ?? ".");
const wanted = process.argv.slice(3);
const sections = wanted.length ? wanted : ["bind", "origin", "sse", "compress", "abort", "headers", "action", "gap"];
const NEXT_BIN = path.join(appDir, "node_modules", "next", "dist", "bin", "next");
const PORT = 3000;
const UP_PORT = 8765;
const FAKE_TOKEN = "Bearer probe-token-not-a-secret";

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...a) => console.log(...a);

// ---------- 프로세스 ----------
function startProc(cmd, args, env = {}, cwd = appDir) {
  const child = spawn(cmd, args, {
    cwd,
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1", ...env },
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });
  child.out = [];
  const push = (d) => child.out.push(...d.toString("utf8").split(/\r?\n/).filter(Boolean));
  child.stdout.on("data", push);
  child.stderr.on("data", push);
  return child;
}

function killTree(child) {
  if (!child || child.exitCode !== null) return;
  if (process.platform === "win32") spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" });
  else child.kill("SIGKILL");
}

function tcpOpen(host, port) {
  return new Promise((resolve) => {
    const s = net.connect({ host, port });
    s.once("connect", () => {
      s.destroy();
      resolve(true);
    });
    s.once("error", () => resolve(false));
  });
}

async function waitPort(port, timeoutMs = 60000) {
  const end = Date.now() + timeoutMs;
  while (Date.now() < end) {
    if ((await tcpOpen("127.0.0.1", port)) || (await tcpOpen("::1", port))) return true;
    await sleep(200);
  }
  throw new Error(`port ${port} did not open`);
}

function assertPortFree(port) {
  const r = spawnSync("netstat", ["-ano"], { encoding: "utf8" });
  const busy = r.stdout.split(/\r?\n/).filter((l) => /LISTENING/.test(l) && l.includes(`:${port} `));
  if (busy.length) throw new Error(`port ${port} busy:\n${busy.join("\n")}`);
}

// 루트 PID와 그 자손이 듣는 소켓(netstat -ano의 LISTENING 줄)
function listeningOfTree(rootPid) {
  const ps = spawnSync(
    "powershell",
    ["-NoProfile", "-Command", "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId | ConvertTo-Json -Compress"],
    { encoding: "utf8" },
  );
  const procs = JSON.parse(ps.stdout);
  const tree = new Set([rootPid]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const p of procs) {
      if (tree.has(p.ParentProcessId) && !tree.has(p.ProcessId)) {
        tree.add(p.ProcessId);
        grew = true;
      }
    }
  }
  const ns = spawnSync("netstat", ["-ano", "-p", "TCP"], { encoding: "utf8" }).stdout;
  const ns6 = spawnSync("netstat", ["-ano", "-p", "TCPv6"], { encoding: "utf8" }).stdout;
  return (ns + ns6)
    .split(/\r?\n/)
    .filter((l) => /LISTENING/.test(l))
    .map((l) => l.trim().split(/\s+/))
    .filter((cols) => tree.has(Number(cols[cols.length - 1])))
    .map((cols) => cols[1]);
}

// ---------- HTTP ----------
// 본문이 있으면 content-length를 붙인다(브라우저 fetch처럼). chunked로 보내려면 headers에 transfer-encoding을 준다
function raw({ port = PORT, host = "127.0.0.1", method = "GET", path: p = "/", headers = {}, body }) {
  if (body !== undefined && headers["transfer-encoding"] === undefined) {
    headers = { ...headers, "content-length": String(Buffer.byteLength(body)) };
  }
  return new Promise((resolve) => {
    const req = http.request({ host, port, method, path: p, headers }, (res) => {
      const bufs = [];
      res.on("data", (d) => bufs.push(d));
      res.on("end", () => resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(bufs).toString("utf8") }));
    });
    req.setTimeout(30000, () => req.destroy(new Error("timeout")));
    req.on("error", (e) => resolve({ status: null, headers: {}, body: `ERR ${e.message}` }));
    if (body !== undefined) req.write(body);
    req.end();
  });
}

function wsUpgrade(p, headers) {
  return new Promise((resolve) => {
    const req = http.request({
      host: "127.0.0.1",
      port: PORT,
      path: p,
      headers: {
        connection: "Upgrade",
        upgrade: "websocket",
        "sec-websocket-version": "13",
        "sec-websocket-key": "dGhlIHNhbXBsZSBub25jZQ==",
        ...headers,
      },
    });
    req.on("upgrade", (res, socket) => {
      socket.destroy();
      resolve(`${res.statusCode} upgrade`);
    });
    req.on("response", (res) => {
      res.resume();
      resolve(`${res.statusCode}`);
    });
    req.setTimeout(10000, () => {
      req.destroy();
      resolve("timeout");
    });
    req.on("error", (e) => resolve(`ERR ${e.message}`));
    req.end();
  });
}

// ---------- Next 서버 ----------
function buildApp(dist, compressOff) {
  const env = { PROBE_DIST: dist, ...(compressOff ? { PROBE_COMPRESS: "0" } : {}) };
  log(`# build ${dist} compress=${compressOff ? "false" : "기본"}`);
  const r = spawnSync(process.execPath, [NEXT_BIN, "build"], {
    cwd: appDir,
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1", ...env },
    encoding: "utf8",
  });
  if (r.status !== 0) throw new Error(`build failed\n${r.stdout}\n${r.stderr}`);
}

const builds = new Set();
function ensureBuild(compressOff) {
  const dist = compressOff ? ".next-c0" : ".next-c1";
  if (!builds.has(dist)) {
    buildApp(dist, compressOff);
    builds.add(dist);
  }
  return dist;
}

// mode: "dev" | "start". extraArgs 예: ["-H", "127.0.0.1"]. portArgs가 false면 -p를 붙이지 않는다
async function withNext({ mode, compressOff = false, extraArgs = [], portArgs = true, env: extraEnv = {} }, fn) {
  assertPortFree(PORT);
  const env = { ...(compressOff ? { PROBE_COMPRESS: "0" } : {}), ...extraEnv };
  if (mode === "start") env.PROBE_DIST = ensureBuild(compressOff);
  else env.PROBE_DIST = compressOff ? ".next-dev-c0" : ".next-dev-c1";
  const args = [NEXT_BIN, mode, ...(portArgs ? ["-p", String(PORT)] : []), ...extraArgs];
  const child = startProc(process.execPath, args, env);
  try {
    await waitPort(PORT);
    await sleep(500);
    return await fn(child);
  } finally {
    killTree(child);
    await sleep(800);
  }
}

async function warmUp() {
  // dev는 첫 요청에 라우트를 컴파일한다. 잴 경로를 한 번씩 부른다
  for (const p of ["/", "/action", "/api/echo", "/apiopt/echo", "/apisig/echo", "/rw/echo"]) await raw({ path: p });
}

const label = (o) => `${o.mode}${o.compressOff ? " compress:false" : " compress 기본"}`;

// ---------- 섹션 ----------
async function sectionBind() {
  log("\n## 1. 바인딩 (인자 없이, -H 127.0.0.1, -H localhost)");
  for (const mode of ["dev", "start"]) {
    for (const extra of [[], ["-H", "127.0.0.1"], ["-H", "localhost"]]) {
      await withNext({ mode, extraArgs: extra, portArgs: false }, async (child) => {
        const lst = listeningOfTree(child.pid);
        const banner = child.out.filter((l) => /Local:|Network:/.test(l)).map((l) => l.trim());
        log(`${mode} ${extra.join(" ") || "(인자 없음)"} -> LISTEN ${[...new Set(lst)].join(", ")} | ${banner.join(" | ")}`);
      });
    }
  }
}

async function sectionOrigin() {
  log("\n## 2. 교차 출처·Host (dev의 allowedDevOrigins 차단)");
  for (const mode of ["dev", "start"]) {
    await withNext({ mode }, async (child) => {
      await warmUp();
      const html = (await raw({ path: "/" })).body;
      const chunk = (html.match(/\/_next\/static\/[^"']+\.js/) ?? ["/_next/static/none.js"])[0];
      const evil = "http://evil.example";
      const cases = [
        ["GET / Host: evil.example:3000", { path: "/", headers: { host: "evil.example:3000" } }],
        ["GET / Origin: evil", { path: "/", headers: { origin: evil } }],
        ["GET chunk (기준)", { path: chunk }],
        ["GET chunk Origin: evil", { path: chunk, headers: { origin: evil } }],
        [
          "GET chunk no-cors cross-site Referer evil",
          { path: chunk, headers: { "sec-fetch-mode": "no-cors", "sec-fetch-site": "cross-site", referer: `${evil}/` } },
        ],
        ["GET chunk Host: evil.example:3000", { path: chunk, headers: { host: "evil.example:3000" } }],
        [
          "GET chunk Host+Origin evil.example:3000 (재바인딩 모양)",
          { path: chunk, headers: { host: "evil.example:3000", origin: "http://evil.example:3000" } },
        ],
        ["GET /rw/echo Origin: evil", { path: "/rw/echo", headers: { origin: evil } }],
        ["GET /api/echo Origin: evil", { path: "/api/echo", headers: { origin: evil } }],
        [
          "POST /rw/echo Origin: evil, Sec-Fetch-Site cross-site",
          { method: "POST", path: "/rw/echo", headers: { origin: evil, "sec-fetch-site": "cross-site", "content-type": "text/plain" }, body: "{}" },
        ],
        [
          "POST /api/echo Origin: evil, Sec-Fetch-Site cross-site",
          { method: "POST", path: "/api/echo", headers: { origin: evil, "sec-fetch-site": "cross-site", "content-type": "text/plain" }, body: "{}" },
        ],
      ];
      log(`### ${mode} (chunk ${chunk})`);
      for (const [name, req] of cases) {
        const r = await raw(req);
        const up = r.body.includes('"upstream":true') ? " 상류 도달" : "";
        const acao = r.headers["access-control-allow-origin"] ? ` ACAO=${r.headers["access-control-allow-origin"]}` : "";
        log(`${name} -> ${r.status}${up}${acao}${r.status === 403 ? ` body=${r.body.slice(0, 20)}` : ""}`);
      }
      log(`WS /_next/hmr Origin: evil -> ${await wsUpgrade("/_next/hmr", { origin: evil })}`);
      log(`WS /_next/hmr Origin: http://localhost:3000 -> ${await wsUpgrade("/_next/hmr", { origin: "http://localhost:3000" })}`);
      log(`WS /_next/hmr Host: evil.example:3000, Origin 없음 -> ${await wsUpgrade("/_next/hmr", { host: "evil.example:3000" })}`);
      const blocked = child.out.filter((l) => l.includes("Blocked cross-origin"));
      log(`서버 기록의 "Blocked cross-origin" 줄: ${blocked.length}개${blocked.length ? ` 예: ${blocked[0].trim()}` : ""}`);
    });
  }
}

async function sectionSse() {
  log("\n## 3. SSE 중계 (상류는 0ms부터 500ms마다 data 한 줄, 10번)");
  // Accept-Encoding: 없음, gzip, 브라우저가 보내는 값(Chrome·Firefox 최신판)
  const encodings = [undefined, "gzip", "gzip, deflate, br, zstd"];
  const aeLabel = (ae) => (ae === undefined ? "없음" : JSON.stringify(ae));
  const up = [];
  for (const ae of encodings) {
    const r = await measure({ url: `http://127.0.0.1:${UP_PORT}/sse`, acceptEncoding: ae });
    up.push(`AE ${aeLabel(ae)} ${r.status} ce=${r.headers["content-encoding"] ?? "-"} ${verdict(r)}`);
  }
  log(`상류 직접: ${up.join(" / ")}`);
  const servers = [
    { mode: "dev", compressOff: false },
    { mode: "dev", compressOff: true },
    { mode: "start", compressOff: false },
    { mode: "start", compressOff: true },
  ];
  for (const s of servers) {
    await withNext(s, async () => {
      await warmUp();
      log(`### ${label(s)}`);
      for (const [pathLabel, p] of [
        ["(a) rewrites", "/rw/sse"],
        ["(b) route handler", "/api/sse"],
      ]) {
        for (const method of ["GET", "POST"]) {
          for (const ae of encodings) {
            const r = await measure({ url: `http://127.0.0.1:${PORT}${p}`, method, acceptEncoding: ae });
            const at = r.events.map((e) => e.at_ms).join(",");
            log(
              `${pathLabel} ${method} AE ${aeLabel(ae)} -> ${r.status} ce=${r.headers["content-encoding"] ?? "-"} ` +
                `te=${r.headers["transfer-encoding"] ?? "-"} | ${verdict(r)} | 도착 ms [${at}]`,
            );
          }
        }
      }
    });
  }
}

// 3의 곁가지: 무엇이 압축되는가. 상류가 Cache-Control에 no-transform을 실으면 rewrites가 압축을 건너뛰는지,
// 보통 JSON(8KB)이 (a)·(b)에서 압축되는지
async function sectionCompress() {
  log("\n## 3b. 압축 여부 (compress 기본, AE는 브라우저 값)");
  const ae = "gzip, deflate, br, zstd";
  for (const mode of ["dev", "start"]) {
    await withNext({ mode }, async () => {
      await warmUp();
      log(`### ${mode}`);
      for (const [name, p] of [
        ["(a) rewrites /sse (Cache-Control: no-cache)", "/rw/sse"],
        ["(a) rewrites /sse-nt (Cache-Control: no-cache, no-transform)", "/rw/sse-nt"],
        ["(b) route handler /sse-nt", "/api/sse-nt"],
      ]) {
        const r = await measure({ url: `http://127.0.0.1:${PORT}${p}`, acceptEncoding: ae });
        log(`${name} -> ${r.status} ce=${r.headers["content-encoding"] ?? "-"} | ${verdict(r)}`);
      }
      for (const [name, p] of [
        ["(a) rewrites /big 8KB JSON", "/rw/big"],
        ["(b) route handler /big 8KB JSON", "/api/big"],
      ]) {
        const r = await raw({ path: p, headers: { "accept-encoding": ae } });
        log(`${name} -> ${r.status} ce=${r.headers["content-encoding"] ?? "-"}`);
      }
    });
  }
}

// 3의 곁가지: 클라이언트가 스트림 중간에 끊으면 상류 연결도 닫히는가. 채널의 실행은 연결에 묶이지 않으므로(ADR 0014)
// 여기서 재는 것은 중계가 상류 연결을 닫는지뿐이다.
// route handler(lib/relay.ts)는 request.signal을 fetch에 넘기지 않는다
async function sectionAbort() {
  log("\n## 3c. 끊김 전파 (클라이언트가 1200ms에 끊는다. 상류 /sse는 500ms마다 한 줄, 10번)");
  let n = 0;
  for (const mode of ["dev", "start"]) {
    await withNext({ mode }, async () => {
      await warmUp();
      log(`### ${mode}`);
      for (const [name, p] of [
        ["(a) rewrites", "/rw/sse"],
        ["(b) route handler, signal 안 넘김", "/api/sse"],
        ["(b') route handler, request.signal 넘김", "/apisig/sse"],
      ]) {
        for (const method of ["GET", "POST"]) {
          const got = [];
          for (let rep = 0; rep < 3; rep += 1) {
            n += 1;
            const id = `abort${n}`;
            const body = method === "POST" ? "{}" : undefined;
            const headers = { accept: "text/event-stream", ...(body ? { "content-type": "application/json", "content-length": "2" } : {}) };
            const req = http.request({ host: "127.0.0.1", port: PORT, method, path: `${p}?id=${id}`, headers });
            req.on("error", () => {});
            req.on("response", (res) => res.on("error", () => {}).resume());
            req.end(body);
            await sleep(1200);
            const abortedAt = Date.now();
            req.destroy();
            // 상류는 끊김이 안 오면 끊은 뒤 약 3.3초에 다 보내고 닫는다(finished=true)
            await sleep(3800);
            const line = upstream.out.find((l) => l.includes("\"closed\"") && l.includes(`id=${id}\"`));
            if (!line) {
              got.push("기록 없음");
              continue;
            }
            const c = JSON.parse(line);
            got.push(`${c.t - abortedAt}ms/${c.finished ? "다 보냄" : `끊김(${c.sent}줄)`}`);
          }
          log(`${name} ${method} -> 끊은 뒤 상류가 닫힌 때 [${got.join(", ")}]`);
        }
      }
    });
  }
}

async function sectionHeaders() {
  log("\n## 4. 헤더 전달 (상류 /echo가 받은 헤더를 되돌린다)");
  for (const mode of ["dev", "start"]) {
    await withNext({ mode }, async (child) => {
      await warmUp();
      log(`### ${mode}`);
      const sent = {
        host: `localhost:${PORT}`,
        authorization: FAKE_TOKEN,
        cookie: "probe=1",
        origin: `http://localhost:${PORT}`,
        "x-probe": "1",
        "accept-encoding": "gzip",
      };
      for (const [pathLabel, p] of [
        ["(a) rewrites", "/rw/echo"],
        ["(b) route handler", "/api/echo"],
      ]) {
        for (const method of ["GET", "POST"]) {
          const r = await raw({ method, path: p, headers: { ...sent, "content-type": "application/json" }, body: method === "POST" ? "{}" : undefined });
          let seen = {};
          try {
            seen = JSON.parse(r.body).headers;
          } catch {
            log(`${pathLabel} ${method} -> ${r.status} 본문이 JSON이 아니다: ${r.body.slice(0, 80)}`);
            continue;
          }
          const pick = ["authorization", "cookie", "origin", "host", "x-probe", "accept-encoding", "x-forwarded-host", "x-forwarded-for", "x-forwarded-proto", "x-forwarded-port", "connection"];
          const shown = pick.map((k) => `${k}=${seen[k] === undefined ? "(없음)" : JSON.stringify(seen[k])}`).join(" ");
          const extra = Object.keys(seen).filter((k) => !pick.includes(k) && !["content-type", "content-length", "accept", "user-agent", "transfer-encoding", "sec-fetch-mode", "accept-language"].includes(k));
          log(`${pathLabel} ${method} -> ${r.status} 상류가 받은 것: ${shown}${extra.length ? ` 그 밖: ${extra.join(",")}` : ""}`);
        }
      }
      const pre = {
        origin: "http://localhost:5173",
        "access-control-request-method": "POST",
        "access-control-request-headers": "authorization,content-type",
      };
      for (const [pathLabel, p] of [
        ["(a) rewrites", "/rw/echo"],
        ["(b) route handler, OPTIONS 안 내보냄", "/api/echo"],
        ["(b') route handler, OPTIONS 내보냄", "/apiopt/echo"],
      ]) {
        const r = await raw({ method: "OPTIONS", path: p, headers: pre });
        const reached = r.body.includes('"upstream":true');
        log(`OPTIONS ${pathLabel} -> ${r.status} 상류 ${reached ? "도달" : "안 감"} allow=${r.headers.allow ?? "-"} ACAO=${r.headers["access-control-allow-origin"] ?? "-"}`);
      }
      // 본문 길이 대신 chunked로 보낸 POST. route handler는 요청 헤더를 그대로 fetch에 넘긴다
      for (const [pathLabel, p] of [
        ["(a) rewrites", "/rw/echo"],
        ["(b) route handler", "/api/echo"],
      ]) {
        const before = child.out.length;
        const r = await raw({ method: "POST", path: p, headers: { "content-type": "application/json", "transfer-encoding": "chunked" }, body: "{}" });
        await sleep(200);
        const err = child.out.slice(before).find((l) => /InvalidArgumentError|invalid .* header/i.test(l));
        log(`chunked POST ${pathLabel} -> ${r.status} 상류 ${r.body.includes('"upstream":true') ? "도달" : "안 감"}${err ? ` 서버 기록: ${err.trim()}` : ""}`);
      }
    });
  }
  // 상류를 이름 localhost로 가리키고 상류는 127.0.0.1에만 듣는다(파이썬 서버의 기본 바인딩과 같은 모양).
  // rewrites 목적지는 빌드 때 굳으므로 설정을 매번 읽는 dev에서만 잰다
  await withNext({ mode: "dev", env: { PROBE_UPSTREAM: `http://localhost:${UP_PORT}` } }, async () => {
    await warmUp();
    for (const [pathLabel, p] of [
      ["(a) rewrites", "/rw/echo"],
      ["(b) route handler", "/api/echo"],
    ]) {
      const r = await raw({ path: p });
      log(`상류 이름 localhost(상류는 127.0.0.1만) ${pathLabel} -> ${r.status} 상류 ${r.body.includes('"upstream":true') ? "도달" : "안 감"}`);
    }
  });
}

async function sectionAction() {
  log("\n## 5. Server Actions CSRF (Origin과 Host 비교)");
  for (const mode of ["dev", "start"]) {
    await withNext({ mode }, async (child) => {
      await warmUp();
      const html = (await raw({ path: "/action", headers: { host: `localhost:${PORT}` } })).body;
      const m = html.match(/\$ACTION_ID_([0-9a-f]+)/);
      if (!m) {
        log(`${mode}: 액션 ID를 찾지 못했다`);
        return;
      }
      const id = m[1];
      const boundary = "----probe";
      const form = `--${boundary}\r\nContent-Disposition: form-data; name="$ACTION_ID_${id}"\r\n\r\n\r\n--${boundary}--\r\n`;
      const mpa = { "content-type": `multipart/form-data; boundary=${boundary}` };
      const cases = [
        ["폼 POST, Origin 없음", { host: `localhost:${PORT}` }],
        ["폼 POST, Origin=Host (localhost:3000)", { host: `localhost:${PORT}`, origin: `http://localhost:${PORT}` }],
        ["폼 POST, Origin: http://evil.example", { host: `localhost:${PORT}`, origin: "http://evil.example" }],
        ["폼 POST, Origin: null", { host: `localhost:${PORT}`, origin: "null" }],
        ["폼 POST, Host·Origin 모두 evil.example:3000 (재바인딩 모양)", { host: "evil.example:3000", origin: "http://evil.example:3000" }],
        [
          "폼 POST, Origin evil + X-Forwarded-Host evil.example",
          { host: `localhost:${PORT}`, origin: "http://evil.example", "x-forwarded-host": "evil.example" },
        ],
      ];
      log(`### ${mode} (action ${id.slice(0, 8)}…)`);
      for (const [name, h] of cases) {
        const before = child.out.filter((l) => l.includes("[probe] server action ran")).length;
        const r = await raw({ method: "POST", path: "/action", headers: { ...mpa, ...h }, body: form });
        await sleep(200);
        const after = child.out.filter((l) => l.includes("[probe] server action ran")).length;
        log(`${name} -> ${r.status} 액션 실행 ${after > before ? "됨" : "안 됨"}`);
      }
      for (const [name, origin] of [
        ["fetch 액션(Next-Action 헤더), Origin=Host", `http://localhost:${PORT}`],
        ["fetch 액션(Next-Action 헤더), Origin evil", "http://evil.example"],
      ]) {
        const before = child.out.filter((l) => l.includes("[probe] server action ran")).length;
        const r = await raw({
          method: "POST",
          path: "/action",
          headers: { host: `localhost:${PORT}`, origin, "next-action": id, "content-type": "text/plain;charset=UTF-8", accept: "text/x-component" },
          body: "[]",
        });
        await sleep(200);
        const after = child.out.filter((l) => l.includes("[probe] server action ran")).length;
        log(`${name} -> ${r.status} 액션 실행 ${after > before ? "됨" : "안 됨"}`);
      }
      const errs = child.out.filter((l) => /does not match `origin`|Missing `origin`/.test(l)).map((l) => l.trim().slice(0, 140));
      log(`서버 기록: ${[...new Set(errs)].join(" || ") || "(없음)"}`);
    });
  }
}

async function sectionGap(long) {
  const gap = long ? 310000 : 35000;
  log(`\n## 부록. 침묵 ${gap / 1000}초 (rewrites의 proxyTimeout 기본 30초, undici fetch의 bodyTimeout 기본 300초)`);
  for (const mode of long ? ["start"] : ["dev", "start"]) {
    await withNext({ mode }, async () => {
      await warmUp();
      const runs = [
        ["(a) rewrites, ping 없음", `/rw/sse-gap?gap=${gap}`],
        ["(a) rewrites, 15초 ping", `/rw/sse-gap?gap=${gap}&ping=15000`],
        ["(b) route handler, ping 없음", `/api/sse-gap?gap=${gap}`],
        ["(b) route handler, 15초 ping", `/api/sse-gap?gap=${gap}&ping=15000`],
      ];
      const results = await Promise.all(
        runs.map(([, p]) => measure({ url: `http://127.0.0.1:${PORT}${p}`, timeoutMs: gap + 30000 })),
      );
      log(`### ${mode}`);
      runs.forEach(([name], i) => {
        const r = results[i];
        log(`${name} -> ${r.status} 이벤트 ${r.events.length}/2 도착 ms [${r.events.map((e) => e.at_ms).join(",")}] 끝 ${r.total_ms}ms${r.error ? ` 오류 ${r.error}` : ""}`);
      });
    });
  }
}

// ---------- main ----------
assertPortFree(UP_PORT);
const upstream = startProc(process.execPath, [path.join(here, "next_sse_upstream.mjs"), String(UP_PORT)], {}, here);
await waitPort(UP_PORT);
log(`# next ${(await import("node:fs")).readFileSync(path.join(appDir, "node_modules", "next", "package.json"), "utf8").match(/"version":\s*"([^"]+)"/)[1]}, node ${process.version}, ${process.platform}`);
try {
  for (const s of sections) {
    if (s === "bind") await sectionBind();
    else if (s === "origin") await sectionOrigin();
    else if (s === "sse") await sectionSse();
    else if (s === "compress") await sectionCompress();
    else if (s === "abort") await sectionAbort();
    else if (s === "headers") await sectionHeaders();
    else if (s === "action") await sectionAction();
    else if (s === "gap") await sectionGap(false);
    else if (s === "gaplong") await sectionGap(true);
    else log(`알 수 없는 섹션 ${s}`);
  }
} finally {
  killTree(upstream);
}
