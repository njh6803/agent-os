// 위젯 테스트 페이지 서버 대역. `node:http` 서버 하나이고 의존성이 없다(`web/node_modules` 없이 돈다).
// `run.py` 가 띄운다. 요청 하나를 받아 작은 HTML 을 답하기 전에, 질의가 고른 대로 다른 서버를 부른다.
//
//   GET /page?calls=none|sites|seq|par&via=fetch|http&conn=keep|close&up=admin|alt|down|hang
//             [&ttl=<ms>][&delay_ms=<ms>][&timeout_ms=<ms>]
//
// - calls: 다른 서버를 부르지 않는다(none, 지금의 모양), 사이트 목록만(sites), 사이트 목록 다음에 "지금 누구인지"를
//   차례로(seq), 둘을 함께(par).
// - via: 전역 `fetch`(Node 에 든 undici) 또는 `node:http` 의 `request`.
// - conn: 연결을 이어 쓴다(keep) 또는 요청마다 새 연결(close). fetch 는 `Connection: close` 헤더로, `node:http` 는
//   `keepAlive: false` 인 Agent 로 한다.
// - up: 부를 대역. 살아 있는 대역(admin), 같은 대역의 둘째 포트(alt), 내려간 대역의 자리(down), 답하지 않는
//   대역(hang). fetch 는 주소(출처)마다 연결 묶음을 따로 둔다. `Connection: close` 를 보내는 fetch 갈래가 admin 을 부르면
//   이어 쓰는 갈래의 연결까지 닫혀(첫 실행에서 이어 쓰는 갈래의 상대 포트가 요청마다 바뀌었다) alt 를 부르게 한다.
// - ttl: 주면 사이트 목록을 그 시간 동안 메모리에 기억한다(calls=sites 에서만).
// - delay_ms: 대역이 답하기 전에 자게 한다. timeout_ms: 부르는 쪽이 거는 제한 시간(`AbortSignal.timeout`).
//
// 답의 `x-probe` 헤더(JSON)가 표지다. 부른 호출마다 대역이 돌려준 일련번호(seq), 대역이 본 상대 포트와 `Connection`
// 헤더, 읽은 줄 수와 회차 표지(nonce), 시작·끝 시각(이 요청의 시작 기준 ms), 오류의 이름과 코드가 든다. 오류의 메시지는
// 싣지 않는다.

import { Agent, createServer, request as httpRequest } from "node:http";
import { parseArgs } from "node:util";

const { values: args } = parseArgs({
  options: {
    port: { type: "string" },
    admin: { type: "string" },
    alt: { type: "string" },
    down: { type: "string" },
    hang: { type: "string" },
    "run-token": { type: "string" },
  },
  strict: true,
});

const BASES = { admin: args.admin, alt: args.alt, down: args.down, hang: args.hang };
const SESSION_COOKIE = `probe_session=probe-session-${args["run-token"]}`;

// 다른 서버를 부르지 않는 갈래가 그리는 목록. 지금의 서버가 뜰 때 설정 파일에서 읽어 메모리에 둔 것에 해당한다.
const STATIC_SITES = Array.from({ length: 10 }, (_, index) => {
  const number = String(index + 1).padStart(2, "0");
  return {
    name: `site-${number}`,
    issuer: `https://issuer-${number}.example.test`,
    assurance_mode: index % 2 === 0 ? "anonymous" : "login",
    report_link: `https://reports.example.test/site-${number}`,
  };
});

const keepAliveAgent = new Agent({ keepAlive: true });
const freshAgent = new Agent({ keepAlive: false });

/** 오류의 이름과 코드만 꺼낸다. fetch 의 실패는 `TypeError` 이고 까닭은 `cause` 에 있다. */
function describeError(error) {
  const cause = error instanceof Error ? error.cause : undefined;
  return {
    name: error instanceof Error ? error.name : "unknown",
    code: error?.code ?? null,
    cause_name: cause instanceof Error ? cause.name : null,
    cause_code: cause?.code ?? null,
  };
}

async function getJsonViaFetch(url, { close, timeoutMs, cookie }) {
  const headers = {};
  if (close) headers.connection = "close";
  if (cookie !== undefined) headers.cookie = cookie;
  const init = { headers };
  if (timeoutMs !== undefined) init.signal = AbortSignal.timeout(timeoutMs);
  const response = await fetch(url, init);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return { data: await response.json(), reused: null };
}

function getJsonViaHttp(url, { close, timeoutMs, cookie }) {
  return new Promise((resolve, reject) => {
    const options = { agent: close ? freshAgent : keepAliveAgent, method: "GET", headers: {} };
    if (cookie !== undefined) options.headers.cookie = cookie;
    if (timeoutMs !== undefined) options.signal = AbortSignal.timeout(timeoutMs);
    const outgoing = httpRequest(url, options, (incoming) => {
      const chunks = [];
      incoming.on("data", (chunk) => chunks.push(chunk));
      incoming.on("error", reject);
      incoming.on("end", () => {
        try {
          if (incoming.statusCode !== 200) throw new Error(`HTTP ${incoming.statusCode}`);
          const data = JSON.parse(Buffer.concat(chunks).toString("utf8"));
          resolve({ data, reused: outgoing.reusedSocket });
        } catch (error) {
          reject(error);
        }
      });
    });
    outgoing.on("error", reject);
    outgoing.end();
  });
}

/** 대역 하나를 부르고 표지를 적는다. 실패해도 던지지 않고 오류를 적어 돌려준다. */
async function call(what, base, options, origin) {
  const record = { what, start: performance.now() - origin };
  const path = what === "sites" ? "/sites" : "/whoami";
  const query = what === "sites" && options.delayMs !== undefined ? `?delay_ms=${options.delayMs}` : "";
  const get = options.via === "http" ? getJsonViaHttp : getJsonViaFetch;
  try {
    const { data, reused } = await get(`${base}${path}${query}`, {
      close: options.close,
      timeoutMs: options.timeoutMs,
      cookie: what === "whoami" ? SESSION_COOKIE : undefined,
    });
    record.ok = true;
    record.data = data;
    record.reused = reused;
    record.seq = data.probe.seq;
    record.port = data.probe.client_port;
    record.connection = data.probe.connection;
    record.rows = data.probe.rows;
    record.nonce = data.probe.nonce;
    record.query_ms = data.probe.query_ms;
    record.delay_ms = data.probe.delay_ms ?? null;
  } catch (error) {
    record.ok = false;
    record.error = describeError(error);
  }
  record.end = performance.now() - origin;
  return record;
}

let cache = null;

function escapeHtml(text) {
  return String(text).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function renderPage(sites, username) {
  const items = sites
    .map(
      (site) =>
        `<li><b>${escapeHtml(site.name)}</b> ${escapeHtml(site.issuer)} ${escapeHtml(site.assurance_mode)} <a href="${escapeHtml(site.report_link)}">보고서</a></li>`,
    )
    .join("");
  const who = username === null ? "" : `<p>${escapeHtml(username)}</p>`;
  return `<!doctype html><html lang="ko"><meta charset="utf-8"><title>settings_fetch</title>${who}<ul>${items}</ul></html>`;
}

function numberParam(params, name) {
  const raw = params.get(name);
  return raw === null ? undefined : Number(raw);
}

async function page(params) {
  const origin = performance.now();
  const calls = params.get("calls") ?? "none";
  const base = BASES[params.get("up") ?? "admin"];
  const options = {
    via: params.get("via") ?? "fetch",
    close: params.get("conn") === "close",
    delayMs: numberParam(params, "delay_ms"),
    timeoutMs: numberParam(params, "timeout_ms"),
  };
  const ttl = numberParam(params, "ttl");
  const probe = { calls: [], cache: null, cached_seq: null };
  let sites = STATIC_SITES;
  let username = null;
  let records = [];

  if (calls === "sites" && ttl !== undefined) {
    if (cache !== null && performance.now() - cache.at < ttl) {
      probe.cache = "hit";
      probe.cached_seq = cache.seq;
      probe.cached_nonce = cache.nonce;
      sites = cache.sites;
    } else {
      probe.cache = "miss";
      const record = await call("sites", base, options, origin);
      if (record.ok) {
        cache = { at: performance.now(), sites: record.data.sites, seq: record.seq, nonce: record.nonce };
      }
      records = [record];
    }
  } else if (calls === "sites") {
    records = [await call("sites", base, options, origin)];
  } else if (calls === "seq") {
    const first = await call("sites", base, options, origin);
    records = [first, await call("whoami", base, options, origin)];
  } else if (calls === "par") {
    records = await Promise.all([
      call("sites", base, options, origin),
      call("whoami", base, options, origin),
    ]);
  }

  let failed = false;
  for (const record of records) {
    if (!record.ok) failed = true;
    else if (record.what === "sites") sites = record.data.sites;
    else username = record.data.username;
    delete record.data;
    probe.calls.push(record);
  }
  probe.upstream_ms = records.length === 0 ? 0 : performance.now() - origin;
  const body = failed
    ? `<!doctype html><html lang="ko"><meta charset="utf-8"><title>settings_fetch</title><p>설정을 받아 오지 못했습니다.</p></html>`
    : renderPage(sites, username);
  return { status: failed ? 502 : 200, body, probe };
}

function send(outgoing, status, headers, body) {
  outgoing.writeHead(status, { "cache-control": "no-store", ...headers });
  outgoing.end(body);
}

const server = createServer((incoming, outgoing) => {
  const url = new URL(incoming.url ?? "/", "http://probe.invalid");
  if (url.pathname === "/__ready") {
    send(outgoing, 200, { "content-type": "application/json" }, JSON.stringify({
      pid: process.pid,
      run_token: args["run-token"],
      node: process.versions.node,
      undici: process.versions.undici,
    }));
    return;
  }
  if (url.pathname === "/__cache-reset") {
    cache = null;
    send(outgoing, 204, {}, "");
    return;
  }
  if (url.pathname !== "/page") {
    send(outgoing, 404, { "content-type": "text/plain; charset=utf-8" }, "찾을 수 없습니다.");
    return;
  }
  page(url.searchParams).then(
    ({ status, body, probe }) => {
      send(outgoing, status, {
        "content-type": "text/html; charset=utf-8",
        "x-probe": JSON.stringify(probe),
      }, body);
    },
    (error) => {
      send(outgoing, 500, {
        "content-type": "text/plain; charset=utf-8",
        "x-probe": JSON.stringify({ calls: [], crashed: describeError(error) }),
      }, "서버 오류입니다.");
    },
  );
});

server.listen({ host: "127.0.0.1", port: Number(args.port) });
