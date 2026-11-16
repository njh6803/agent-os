// 위젯 테스트 페이지 서버 대역(스텁). node:http 서버이고 의존성이 없다. 같은 폴더의 probe.mjs 가 자기 프로세스 안에 띄운다.
//
// 위젯 테스트 페이지의 서버(web/apps/portal/server)에 운영자의 문은 아직 없다(portal-admin 이 짓는다). 이 대역은
// ADR 0065 결정 "위젯 테스트 페이지"가 적은 흐름만 흉내 낸다. 받은 운영자 로그인 쿠키를 Agent OS 의 "지금 누구인지"와
// "갱신" 경로에 전하고, 갱신 때 Agent OS 가 내는 Set-Cookie 줄을 응답에 그대로 싣는다.
//
// Agent OS 를 부르는 길은 셋이고 경로의 첫 마디가 고른다.
//   /fetch/...   Node 의 전역 fetch(undici)
//   /http/...    node:http 의 request(기본 전역 Agent)
//   /oaf/...     openapi-fetch 의 클라이언트(그 안에서 전역 fetch 를 부른다). createTester 에 createClient 를 줄 때만 선다.
//                web/ 의 판정자가 전역 fetch 를 직접 쓰는 것을 막으므로, 실제 서버가 쓸 호출 방식이 이 길이다
//
// 그 뒤의 경로
//   plain-cookie      대조. Secure 없는 쿠키를 내는 Agent OS 대역의 경로를 부른다(클라이언트가 쿠키를 기억하는지 볼 때)
//   timeout/refresh   갱신을 AbortSignal.timeout(주소의 timeout_ms) 과 함께 부르고, 던져진 것이 있으면 그 모양을 504 로 돌려준다
//   page          빈 문서. Agent OS 를 부르지 않는다
//   gate          문서. 주소로 들어오는 요청에서 로그인을 확인하고, 만료됐으면 그 자리에서 갱신한다(설계 1 과 같은 일)
//   d1/data       설계 1. 중계가 스스로 갱신한다
//   d2/data       설계 2. "지금 누구인지"의 답을 그대로 돌려준다
//   d2/refresh    설계 2. 화면이 부르는 갱신 경로(POST)
//   raw/gate      대조. 브라우저가 보낸 머리를 그대로 Agent OS 에 전한다(갱신하지 않는다)
//
// 대조를 뺀 경로가 Agent OS 에 보내는 요청에는 이 대역이 Cookie 머리 하나만 더한다. 나머지 머리는 fetch 나 node:http 가
// 스스로 붙인 것이다. 요청을 서로 맞대려고 주소에 probe=<태그>.<길> 을 붙인다(머리가 아니다).
// 받은 요청은 머리(rawHeaders) 그대로 log 에 쌓는다. 쿠키 값은 프로브가 지은 무작위 값이고 비밀이 아니다.

import http from "node:http";

const NOT_FORWARDED = new Set(["host", "connection", "keep-alive", "transfer-encoding", "content-length"]);

/** rawHeaders(이름, 값, 이름, 값 …)를 [이름, 값] 쌍의 배열로. 줄의 차례와 겹친 이름을 지킨다. */
export function pairs(raw) {
  const out = [];
  for (let i = 0; i < raw.length; i += 2) out.push([raw[i], raw[i + 1]]);
  return out;
}

export function listen(server) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve(server.address().port));
  });
}

export function close(server) {
  return new Promise((resolve) => {
    server.closeAllConnections?.();
    server.close(() => resolve());
  });
}

/** 부를 자리. base 는 Agent OS 대역의 주소, probe 는 요청을 맞대는 태그다(주소의 probe=). */
const urlOf = ({ base, path, probe }) => `${base}${path}?probe=${encodeURIComponent(probe)}`;

async function viaFetch(method, target, headers, { signal } = {}) {
  const answer = await fetch(urlOf(target), { method, headers, redirect: "manual", signal });
  const text = await answer.text();
  return { status: answer.status, setCookie: answer.headers.getSetCookie(), text };
}

/**
 * openapi-fetch 의 클라이언트로 부른다. 클라이언트는 서버가 사는 동안 하나를 함께 쓴다. 돌려받은 객체의 response 칸이 원래의
 * Response 이고, Set-Cookie 줄은 거기서 getSetCookie() 로 줄마다 꺼낸다. 이 대역이 더하는 머리는 headers 뿐이다.
 */
function viaOpenapiFetch(client) {
  return async (method, target, headers, { signal } = {}) => {
    const result = await client[method](target.path, {
      params: { query: { probe: target.probe } },
      headers: Object.fromEntries(headers),
      signal,
    });
    return {
      status: result.response.status,
      setCookie: result.response.headers.getSetCookie(),
      text: JSON.stringify(result.data ?? result.error ?? null),
    };
  };
}

/** 던져진 것의 모양. 제한 시간에 끊긴 호출이 무엇을 던지는지 적을 때 쓴다. */
function shapeOf(error) {
  return {
    name: error?.name ?? null,
    constructorName: error?.constructor?.name ?? null,
    message: typeof error?.message === "string" ? error.message : null,
    code: error?.code ?? null,
    isDomException: error instanceof DOMException,
    causeName: error?.cause?.name ?? null,
  };
}

function viaHttp(method, target, headers) {
  const url = urlOf(target);
  return new Promise((resolve, reject) => {
    const request = http.request(url, { method, headers: Object.fromEntries(headers), timeout: 30_000 }, (answer) => {
      const chunks = [];
      answer.on("data", (chunk) => chunks.push(chunk));
      answer.on("end", () =>
        resolve({
          status: answer.statusCode,
          setCookie: answer.headers["set-cookie"] ?? [],
          text: Buffer.concat(chunks).toString("utf-8"),
        }),
      );
    });
    request.on("timeout", () => request.destroy(new Error(`${url} 시간 초과`)));
    request.on("error", reject);
    request.end();
  });
}

/** 받은 Cookie 머리에 Set-Cookie 줄들의 이름과 값을 덮어, 같은 요청 안의 다음 호출에 쓸 머리를 짓는다. */
function merged(cookie, lines) {
  const jar = new Map();
  for (const part of (cookie ?? "").split("; ")) {
    const at = part.indexOf("=");
    if (at > 0) jar.set(part.slice(0, at), part.slice(at + 1));
  }
  for (const line of lines) {
    const first = line.split(";", 1)[0];
    const at = first.indexOf("=");
    if (at > 0) jar.set(first.slice(0, at), first.slice(at + 1));
  }
  return jar.size === 0 ? undefined : [...jar].map(([name, value]) => `${name}=${value}`).join("; ");
}

const cookieOnly = (cookie) => (cookie === undefined ? [] : [["cookie", cookie]]);

function reasonOf(answer) {
  try {
    return JSON.parse(answer.text).reason ?? null;
  } catch {
    return null;
  }
}

/**
 * agentOs 는 Agent OS 대역의 주소(http://127.0.0.1:<포트>). 돌려주는 log 에 받은 요청과 Agent OS 에 한 호출이 쌓인다.
 * openapiFetch 는 openapi-fetch 의 createClient 다. 주면 /oaf/... 길이 선다. 이 파일은 그것을 import 하지 않는다(의존성 없음).
 */
export function createTester({ agentOs, openapiFetch }) {
  const log = [];
  const callers = { fetch: viaFetch, http: viaHttp };
  if (openapiFetch !== undefined) callers.oaf = viaOpenapiFetch(openapiFetch({ baseUrl: agentOs }));

  async function call(entry, method, path, headers, via, options) {
    const target = { base: agentOs, path, probe: `${entry.tag}.${via}` };
    const answer = await callers[entry.kind](method, target, headers, options);
    entry.calls.push({ method, path, status: answer.status, setCookie: answer.setCookie });
    return answer;
  }

  function send(res, entry, status, body, lines, type = "application/json") {
    res.statusCode = status;
    res.setHeader("Content-Type", type);
    res.setHeader("Cache-Control", "no-store");
    // Agent OS 가 낸 Set-Cookie 줄을 줄마다 그대로 싣는다.
    if (lines.length > 0) res.setHeader("Set-Cookie", lines);
    entry.replied = { status, setCookie: lines };
    res.end(typeof body === "string" ? body : JSON.stringify(body));
  }

  /** 설계 1 의 몸통. "지금 누구인지"가 401 이면 그 자리에서 "갱신"을 부른다. */
  async function selfRefreshing(entry, cookie) {
    const via = entry.kind;
    let who = await call(entry, "GET", "/auth/me", cookieOnly(cookie), via);
    let lines = [];
    if (who.status === 401) {
      const refreshed = await call(entry, "POST", "/auth/refresh", cookieOnly(cookie), via);
      lines = refreshed.setCookie;
      if (refreshed.status !== 200) {
        return { status: refreshed.status, body: { stage: "refresh", reason: reasonOf(refreshed) }, lines };
      }
      who = await call(entry, "GET", "/auth/me", cookieOnly(merged(cookie, lines)), via);
    }
    if (who.status !== 200) return { status: who.status, body: { stage: "me", reason: reasonOf(who) }, lines };
    return { status: 200, body: { account: JSON.parse(who.text).account, refreshed: lines.length > 0 }, lines };
  }

  async function handle(req, res) {
    const url = new URL(req.url, "http://placeholder");
    const [, kind, ...rest] = url.pathname.split("/");
    const route = rest.join("/");
    const entry = {
      seq: log.length,
      tag: url.searchParams.get("tag"),
      method: req.method,
      path: url.pathname,
      kind,
      headers: pairs(req.rawHeaders),
      calls: [],
    };
    log.push(entry);
    const cookie = req.headers.cookie;
    if (!(kind in callers)) {
      send(res, entry, 404, { reason: "not_found" }, []);
      return;
    }
    if (route === "plain-cookie" && req.method === "GET") {
      const answer = await call(entry, "GET", "/__probe/plain-cookie", [], `${kind}-plain`);
      send(res, entry, answer.status, { stage: "plain-cookie" }, []);
      return;
    }
    if (route === "timeout/refresh" && req.method === "POST") {
      const limit = Number(url.searchParams.get("timeout_ms"));
      const startedAt = performance.now();
      const elapsed = () => Math.round(performance.now() - startedAt);
      try {
        const refreshed = await call(entry, "POST", "/auth/refresh", cookieOnly(cookie), kind, { signal: AbortSignal.timeout(limit) });
        send(res, entry, refreshed.status, { stage: "refresh", threw: false, elapsedMs: elapsed() }, refreshed.setCookie);
      } catch (error) {
        entry.threw = shapeOf(error);
        send(res, entry, 504, { stage: "refresh", threw: true, elapsedMs: elapsed(), error: entry.threw }, []);
      }
      return;
    }
    if (route === "page" && req.method === "GET") {
      send(res, entry, 200, "<!doctype html><title>login_relay C</title><p>tester origin</p>", [], "text/html; charset=utf-8");
      return;
    }
    if ((route === "d1/data" || route === "gate") && req.method === "GET") {
      const done = await selfRefreshing(entry, cookie);
      if (route === "d1/data") {
        send(res, entry, done.status, done.body, done.lines);
        return;
      }
      const text = `<!doctype html><title>login_relay C gate</title><p id="gate">${done.status === 200 ? "tester" : "login required"}</p>`;
      send(res, entry, done.status === 200 ? 200 : 401, text, done.lines, "text/html; charset=utf-8");
      return;
    }
    if (route === "d2/data" && req.method === "GET") {
      const who = await call(entry, "GET", "/auth/me", cookieOnly(cookie), kind);
      const body = who.status === 200 ? { account: JSON.parse(who.text).account } : { stage: "me", reason: reasonOf(who) };
      send(res, entry, who.status, body, []);
      return;
    }
    if (route === "d2/refresh" && req.method === "POST") {
      const refreshed = await call(entry, "POST", "/auth/refresh", cookieOnly(cookie), kind);
      const body = refreshed.status === 200 ? { stage: "refresh" } : { stage: "refresh", reason: reasonOf(refreshed) };
      send(res, entry, refreshed.status, body, refreshed.setCookie);
      return;
    }
    if (route === "raw/gate" && req.method === "GET") {
      const verbatim = pairs(req.rawHeaders).filter(([name]) => !NOT_FORWARDED.has(name.toLowerCase()));
      const who = await call(entry, "GET", "/auth/me", verbatim, `${kind}-raw`);
      const text = `<!doctype html><title>login_relay C raw gate</title><p id="gate">${who.status}</p>`;
      send(res, entry, who.status, text, [], "text/html; charset=utf-8");
      return;
    }
    send(res, entry, 404, { reason: "not_found" }, []);
  }

  const server = http.createServer((req, res) => {
    // 요청 몸은 쓰지 않는다. 흘려보내야 연결이 다음 요청을 받는다.
    req.resume();
    handle(req, res).catch((error) => {
      log.push({ seq: log.length, error: String(error?.stack ?? error) });
      if (!res.headersSent) res.statusCode = 500;
      res.end();
    });
  });
  return { server, log };
}
