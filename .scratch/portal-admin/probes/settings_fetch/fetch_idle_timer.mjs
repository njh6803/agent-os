// 이어 쓰는 연결에서 전역 `fetch` 가 `node:http` 보다 느린 까닭을 가르는 작은 프로브. 의존성이 없고 PostgreSQL 도 쓰지 않는다.
// `run.py` 의 측정에서 이어 쓰는 fetch 갈래가 새 연결 갈래보다 느렸고, 그 차이가 어디서 나는지를 본다.
//
//   node fetch_idle_timer.mjs [--count 200]
//
// 하는 일. 자식 프로세스로 작은 HTTP 서버(`node:http`, 포트 둘)를 띄우고 네 갈래를 요청 하나마다 번갈아 잰다.
// fetch 이어 쓰기, node:http 이어 쓰기, fetch 새 연결(`Connection: close`, 둘째 포트), node:http 새 연결.
// 그 뒤 자식 프로세스 하나를 더 띄워(`--trace`) 이어 쓰는 fetch 에서 fetch 호출과 소켓 쓰기 사이에 걸리는 `setTimeout` 을
// 스택과 함께 적는다. 끝으로 아무 일도 없는 `setTimeout(0)` 이 얼마 뒤에 불리는지를 잰다(양성 대조).
//
// 표지. 이어 쓰는 갈래는 서버가 본 상대 포트가 한 가지여야 하고, 새 연결 갈래는 서버가 요청마다 `Connection: close` 를
// 봐야 한다. 추적은 요청마다 소켓 쓰기를 한 번 봐야 한다. 하나라도 어긋나면 종료 코드가 1 이다.
//
// 해석의 갈래. "이어 쓰는 fetch 가 느린 것은 쓰기 전에 0ms 타이머 하나를 기다리기 때문이고, 그 값은 그 플랫폼에서
// `setTimeout(0)` 이 불리는 데 걸리는 시간이다"가 맞으면 셋이 함께 나온다. (가) 추적에서 fetch 호출과 소켓 쓰기 사이에
// 타이머가 걸리고 쓰기가 그 타이머가 불린 직후다. (나) fetch 이어 쓰기와 node:http 이어 쓰기의 차가 맨 `setTimeout(0)` 의
// 시간과 비슷하다. (다) 새 연결의 fetch 에는 그 차가 없다. 서버가 늦게 답한다는 해석이면 (다)에도 차가 난다.
// 타이머를 거는 함수의 이름은 Node 에 든 undici 의 판마다 다를 수 있어 스택의 맨 위 줄을 그대로 적는다.

import { spawn } from "node:child_process";
import { Agent, createServer, request as httpRequest } from "node:http";
import net from "node:net";
import { createInterface } from "node:readline";
import timers from "node:timers";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

const { values: args } = parseArgs({
  options: {
    count: { type: "string", default: "200" },
    server: { type: "boolean", default: false },
    trace: { type: "string" },
  },
  strict: true,
});

const SELF = fileURLToPath(import.meta.url);
const now = () => performance.now();
const sleep = (ms) => new Promise((resolve) => timers.setTimeout(resolve, ms));

function summarize(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const at = (percent) => sorted[Math.max(1, Math.ceil((percent / 100) * sorted.length)) - 1];
  return {
    n: sorted.length,
    median: Number(at(50).toFixed(3)),
    p95: Number(at(95).toFixed(3)),
    max: Number(sorted[sorted.length - 1].toFixed(3)),
  };
}

// ---- 서버 역할: 포트 둘에서 듣고, 본 상대 포트와 Connection 헤더를 돌려준다. 표준 입력이 닫히면 끝난다.
async function runServer() {
  const servers = [];
  for (let index = 0; index < 2; index += 1) {
    const server = createServer((incoming, outgoing) => {
      const body = JSON.stringify({
        port: incoming.socket.remotePort,
        connection: incoming.headers.connection ?? null,
        sites: Array.from({ length: 10 }, (_, site) => `https://issuer-${site}.example.test`),
      });
      outgoing.writeHead(200, { "content-type": "application/json", "content-length": Buffer.byteLength(body) });
      outgoing.end(body);
    });
    await new Promise((resolve) => server.listen({ host: "127.0.0.1", port: 0 }, resolve));
    servers.push(server);
  }
  console.log(JSON.stringify({ ports: servers.map((server) => server.address().port) }));
  process.stdin.on("end", () => process.exit(0));
  process.stdin.resume();
}

// ---- 추적 역할: 타이머와 소켓 쓰기를 감싼 뒤 이어 쓰는 fetch 를 부른다. 감싸기는 첫 fetch 앞에 한다.
async function runTrace(url) {
  // 부모는 첫 줄을 FIRST_LINE_MS 까지만 기다리고 떠난다. 요청이 멎어도 이 프로세스가 남지 않게 같은 한도에서 스스로 끝낸다.
  // 타이머를 감싸기 전에 걸어 추적에 섞이지 않게 한다.
  timers.setTimeout(() => process.exit(3), FIRST_LINE_MS).unref();
  let tracing = null;
  const wrapTimer = (target, kind) => {
    const original = target[kind];
    target[kind] = function traced(callback, ...rest) {
      if (tracing === null) return original.call(this, callback, ...rest);
      const entry = {
        kind,
        delay: kind === "setTimeout" ? (rest[0] ?? null) : null,
        set_ms: now() - tracing.origin,
        fired_ms: null,
        top: (new Error().stack ?? "").split("\n")[2]?.trim() ?? "",
      };
      const mine = tracing;
      mine.timers.push(entry);
      const wrapped = (...inner) => {
        entry.fired_ms = now() - mine.origin;
        return callback(...inner);
      };
      return original.call(this, wrapped, ...rest);
    };
  };
  for (const target of [globalThis, timers]) {
    wrapTimer(target, "setTimeout");
    wrapTimer(target, "setImmediate");
  }
  const originalWrite = net.Socket.prototype.write;
  net.Socket.prototype.write = function patched(...inner) {
    if (tracing !== null) tracing.writes.push(now() - tracing.origin);
    return originalWrite.apply(this, inner);
  };

  const requests = [];
  for (let index = 0; index < 35; index += 1) {
    await sleep(20);
    const mine = { origin: now(), timers: [], writes: [] };
    tracing = mine;
    const response = await fetch(url);
    const data = await response.json();
    tracing = null;
    // 첫 다섯은 연결을 맺는 요청과 몸풀기라 뺀다.
    if (index >= 5) requests.push({ port: data.port, timers: mine.timers, writes: mine.writes });
  }
  console.log(JSON.stringify(requests));
}

// ---- 재는 역할
function viaHttp(url, agent) {
  return new Promise((resolve, reject) => {
    const outgoing = httpRequest(url, { agent }, (incoming) => {
      const chunks = [];
      incoming.on("data", (chunk) => chunks.push(chunk));
      incoming.on("error", reject);
      incoming.on("end", () => resolve(JSON.parse(Buffer.concat(chunks).toString("utf8"))));
    });
    outgoing.on("error", reject);
    outgoing.end();
  });
}

async function viaFetch(url, close) {
  const response = await fetch(url, close ? { headers: { connection: "close" } } : {});
  return await response.json();
}

// 자식의 첫 줄을 기다리는 한도. 추적 자식은 요청 서른다섯을 20ms 씩 쉬며 보낸 뒤에 한 줄을 낸다.
const FIRST_LINE_MS = 30_000;

/** 자식의 첫 줄. 줄을 내기 전에 끝나거나 한도 안에 줄을 내지 않으면 던진다. 끝없이 기다리지 않는다. */
function firstLine(child, what) {
  return new Promise((resolve, reject) => {
    const lines = createInterface({ input: child.stdout });
    const limit = timers.setTimeout(() => {
      lines.close();
      reject(new Error(`${what}이 ${FIRST_LINE_MS}ms 안에 줄을 내지 않았다`));
    }, FIRST_LINE_MS);
    lines.once("line", (line) => {
      timers.clearTimeout(limit);
      resolve(line);
    });
    // `exit` 가 아니라 `close` 에서 판정한다. `exit` 는 자식이 낸 출력을 다 읽기 전에 올 수 있어, 한 줄을 내고 바로
    // 끝나는 추적 자식의 줄을 버릴 수 있다. `close` 는 출력의 흐름이 닫힌 뒤에 온다. 줄을 이미 받았으면 아래는 아무 일도 않는다.
    child.once("close", () => {
      timers.clearTimeout(limit);
      reject(new Error(`${what}이 줄을 내기 전에 끝났다`));
    });
  });
}

/** 추적 자식이 낸 요청들의 요약. 어긋난 표지는 `problems` 에 더한다. */
function traceSummary(traced, problems) {
  const withWrite = traced.filter((request) => request.writes.length === 1);
  if (withWrite.length !== traced.length) problems.push(`추적: 소켓 쓰기를 한 번 본 요청이 ${withWrite.length}/${traced.length}`);
  if (new Set(traced.map((request) => request.port)).size !== 1) problems.push("추적: 연결을 이어 쓰지 않았다");
  // fetch 호출과 소켓 쓰기 사이에 걸리고 쓰기 전에 불린 `setTimeout`. `setImmediate` 는 기다림이 없어 따로 센다.
  const label = (timer) => `${timer.kind} delay=${timer.delay} ${timer.top}`;
  const tally = (lists) => {
    const counts = {};
    for (const list of lists) for (const timer of list) counts[label(timer)] = (counts[label(timer)] ?? 0) + 1;
    return counts;
  };
  const setBefore = withWrite.map((request) => request.timers.filter((timer) => timer.set_ms <= request.writes[0]));
  const before = withWrite.map((request) =>
    request.timers.filter(
      (timer) => timer.kind === "setTimeout" && timer.fired_ms !== null && timer.fired_ms <= request.writes[0],
    ),
  );
  const gated = before.filter((list) => list.length > 0);
  return {
    requests: traced.length,
    requests_with_timer_before_write: gated.length,
    timer_wait_ms: gated.length === 0 ? null : summarize(gated.map((list) => list[0].fired_ms - list[0].set_ms)),
    write_after_fetch_ms: withWrite.length === 0 ? null : summarize(withWrite.map((request) => request.writes[0])),
    write_after_timer_ms: gated.length === 0 ? null : summarize(
      withWrite.filter((_, index) => before[index].length > 0).map((request, index) => request.writes[0] - gated[index][0].fired_ms),
    ),
    timer_set_by: tally(gated),
    // 쓰기 전에 걸린 것 전부(불렸든 아니든). 위가 비었을 때 타이머가 아예 걸리지 않았는지를 가른다.
    set_before_write_by: tally(setBefore),
  };
}

// 재는 실행 전체의 한도. 기본값(--count 200)의 실행은 몇 초에 끝난다.
const RUN_LIMIT_MS = 300_000;

async function runMeasure() {
  const count = Number(args.count);
  // 재는 요청(`viaFetch`, `viaHttp`)에는 요청마다 제한 시간을 걸지 않는다. 걸면 호출마다 타이머가 하나 더 걸려,
  // 타이머 하나의 기다림을 가르려는 이 프로브의 재는 길이 달라진다. 대신 실행 전체에 한도를 둔다.
  // 서버 자식이 답을 멈춰 요청이 끝나지 않으면 여기서 끝나고, 종료 코드는 측정이 아닌 실행의 1 이다.
  timers
    .setTimeout(() => {
      console.error(`재는 실행이 ${RUN_LIMIT_MS}ms 안에 끝나지 않았다. 측정이 아니다`);
      process.exit(1);
    }, RUN_LIMIT_MS)
    .unref();
  const server = spawn(process.execPath, [SELF, "--server"], { stdio: ["pipe", "pipe", "inherit"] });
  const problems = [];
  let output = null;
  try {
    const { ports } = JSON.parse(await firstLine(server, "서버 자식"));
    const main = `http://127.0.0.1:${ports[0]}/`;
    const alt = `http://127.0.0.1:${ports[1]}/`;
    const keepAgent = new Agent({ keepAlive: true });
    const freshAgent = new Agent({ keepAlive: false });
    const branches = {
      "fetch-keep": { call: () => viaFetch(main, false), close: false },
      "http-keep": { call: () => viaHttp(main, keepAgent), close: false },
      "fetch-close": { call: () => viaFetch(alt, true), close: true },
      "http-close": { call: () => viaHttp(alt, freshAgent), close: true },
    };
    const names = Object.keys(branches);
    const times = Object.fromEntries(names.map((name) => [name, []]));
    const seen = Object.fromEntries(names.map((name) => [name, []]));
    for (let index = 0; index < count + 10; index += 1) {
      for (let offset = 0; offset < names.length; offset += 1) {
        const name = names[(index + offset) % names.length];
        const started = now();
        const data = await branches[name].call();
        const elapsed = now() - started;
        if (index >= 10) {
          times[name].push(elapsed);
          seen[name].push(data);
        }
      }
    }
    const results = {};
    for (const name of names) {
      const distinct = new Set(seen[name].map((data) => data.port)).size;
      const closes = seen[name].filter((data) => data.connection === "close").length;
      if (!branches[name].close && distinct !== 1) problems.push(`${name}: 상대 포트가 ${distinct}가지다`);
      if (branches[name].close && closes !== count) problems.push(`${name}: close 를 본 요청이 ${closes}개다`);
      results[name] = { ...summarize(times[name]), distinct_ports: distinct, close_seen: closes };
    }

    // 맨 타이머. 아무 일도 없을 때 `setTimeout(0)` 이 얼마 뒤에 불리는가.
    const bare = [];
    for (let index = 0; index < 60; index += 1) {
      await sleep(20);
      const started = now();
      await new Promise((resolve) => timers.setTimeout(resolve, 0));
      bare.push(now() - started);
    }

    // 추적이 실패해도 위에서 모은 값은 낸다. 아래에서 추적 자리만 채운다.
    output = {
      platform: `${process.platform} ${process.arch}`,
      node: process.versions.node,
      undici: process.versions.undici,
      count,
      branches: results,
      keep_fetch_minus_http_median: Number((results["fetch-keep"].median - results["http-keep"].median).toFixed(3)),
      close_fetch_minus_http_median: Number((results["fetch-close"].median - results["http-close"].median).toFixed(3)),
      bare_set_timeout_0: summarize(bare),
      trace: null,
      problems,
    };

    const tracer = spawn(process.execPath, [SELF, "--trace", main], { stdio: ["ignore", "pipe", "inherit"] });
    try {
      const traced = JSON.parse(await firstLine(tracer, "추적 자식"));
      output.trace = traceSummary(traced, problems);
    } catch (error) {
      problems.push(`추적: ${error.message}`);
    }
  } finally {
    server.stdin.end();
  }
  console.log(JSON.stringify(output, null, 1));
  process.exit(output === null || problems.length > 0 ? 1 : 0);
}

if (args.server) await runServer();
else if (args.trace !== undefined) await runTrace(args.trace);
else await runMeasure();
