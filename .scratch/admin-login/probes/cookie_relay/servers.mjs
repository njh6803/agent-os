// cookie_relay 프로브가 띄우는 서버 셋. 모두 이 프로세스 안의 node 서버이고 의존성이 없다. 쓰는 쪽은 같은 폴더의 probe.mjs.
//
//   backend   파이썬 서버(상류)의 자리에 서는 스텁. 관리 화면의 중계(Next rewrites)가 /api/* 를 여기로 넘긴다. 받은 요청을
//             머리(rawHeaders) 그대로 기록하고 JSON 으로 돌려준다. /set, /set-controls, /set-open 은 Set-Cookie 를 싣고,
//             /set-status?code=N 은 상태 N 의 응답에 쿠키를 지우는 Set-Cookie 를 싣는다.
//             OPTIONS 는 CORS 머리 없는 204 다(상류에 CORS 가 없다는 것만 흉내 낸다. 실제 serve 는 토큰 없는 OPTIONS 에 401 이다).
//   visitor   방문자용 페이지의 자리에 서는 서버(B). 빈 페이지, 폼 페이지, 받은 요청의 기록, 그리고 자기 응답으로
//             같은 이름의 쿠키를 싣는 /set-evil 을 낸다. 평문과 TLS 둘 다 같은 처리기를 쓴다.
//   tlsFront  TLS 를 끝내고 관리 화면(평문)으로 넘기는 앞단. 배포의 프록시(nginx)를 띄우지 않고 흉내 낸 것이다.
//             release-image 의 측정한 설정(.scratch/release-image/probes/proxy_config/nginx/proxy.conf)처럼
//             X-Forwarded-For 와 X-Forwarded-Proto 를 덮어쓴다. Host 는 hostMode 가 "pass" 면 받은 그대로(포트까지),
//             "name" 이면 포트를 뗀 이름만 넘긴다. 뒤의 것은 그 설정의 `proxy_set_header Host $host` 를 흉내 낸 것이다
//             ($host 가 포트를 떼는 것은 그 프로브 README 4번이 Location 으로 쟀다. 뒷단이 받는 Host 를 nginx 로 재지는 않았다).

import http from "node:http";
import https from "node:https";
import net from "node:net";

const HTML = { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" };
const JSON_TYPE = { "Content-Type": "application/json", "Cache-Control": "no-store" };

/** rawHeaders(이름, 값, 이름, 값 …)를 [이름, 값] 쌍의 배열로. 줄의 차례와 겹친 이름을 지킨다. */
export function pairs(raw) {
  const out = [];
  for (let i = 0; i < raw.length; i += 2) out.push([raw[i], raw[i + 1]]);
  return out;
}

export function listen(server, host = "127.0.0.1") {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, host, () => resolve(server.address().port));
  });
}

export function close(server) {
  return new Promise((resolve) => {
    server.closeAllConnections?.();
    server.close(() => resolve());
  });
}

function record(log, role, req, body) {
  const url = new URL(req.url, "http://placeholder");
  const entry = {
    seq: log.length,
    role,
    tag: url.searchParams.get("tag"),
    method: req.method,
    path: url.pathname,
    headers: pairs(req.rawHeaders),
    body,
  };
  log.push(entry);
  return { url, entry };
}

function withBody(handler) {
  return (req, res) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => handler(req, res, Buffer.concat(chunks).toString("utf-8")));
  };
}

function echo(res, entry, extra = {}) {
  res.writeHead(200, { ...JSON_TYPE, ...extra });
  res.end(JSON.stringify(entry));
}

/** 상류 스텁이 /set 에 싣는 Set-Cookie 줄. 차례가 응답의 줄 차례다. */
export function setLines(values) {
  const base = "HttpOnly; Secure; SameSite=Strict";
  return [
    `__Host-probe_at=${values.at}; ${base}; Path=/`,
    `__Host-probe_rt=${values.rt}; Max-Age=1209600; ${base}; Path=/`,
    `probe_plain=${values.plain}; ${base}; Path=/`,
    `probe_scoped=${values.scoped}; ${base}; Path=/api/echo`,
  ];
}

/** 접두사 규칙이 이 브라우저에서 실제로 걸리는지 보는 대조 둘. 둘 다 거절돼야 한다. */
export function controlLines(values) {
  return [
    `__Host-probe_badpath=${values.badpath}; HttpOnly; Secure; SameSite=Strict; Path=/api`,
    `__Host-probe_nosecure=${values.nosecure}; HttpOnly; SameSite=Strict; Path=/`,
  ];
}

/** HttpOnly 만 뺀 쿠키 하나. B 의 스크립트가 같은 키를 덮지 못하는 까닭이 HttpOnly 인지 가르는 대조다. */
export function openLines(values) {
  return [`__Host-probe_open=${values.open}; Secure; SameSite=Strict; Path=/`];
}

/** 쿠키를 지우는 줄 둘. /set-status 가 200 이 아닌 상태에 싣는다. */
export function clearLines() {
  const base = "Max-Age=0; HttpOnly; Secure; SameSite=Strict; Path=/";
  return [`__Host-probe_at=; ${base}`, `probe_plain=; ${base}`];
}

export function createBackend(values) {
  const log = [];
  const server = http.createServer(
    withBody((req, res, body) => {
      const { url, entry } = record(log, "backend", req, body);
      if (req.method === "OPTIONS") {
        res.writeHead(204);
        res.end();
        return;
      }
      if (url.pathname === "/page") {
        res.writeHead(200, HTML);
        res.end("<!doctype html><title>cookie_relay admin</title><p>admin origin</p>");
        return;
      }
      if (url.pathname === "/set") {
        echo(res, entry, { "Set-Cookie": setLines(values) });
        return;
      }
      if (url.pathname === "/set-controls") {
        echo(res, entry, { "Set-Cookie": controlLines(values) });
        return;
      }
      if (url.pathname === "/set-open") {
        echo(res, entry, { "Set-Cookie": openLines(values) });
        return;
      }
      if (url.pathname === "/set-status") {
        // 200 이 아닌 응답(로그아웃의 204, 만료의 401, 넘김의 303)에 실은 Set-Cookie.
        const code = Number(url.searchParams.get("code"));
        res.writeHead(code, {
          "Cache-Control": "no-store",
          "Set-Cookie": clearLines(),
          ...(code === 303 ? { Location: "/page" } : {}),
        });
        res.end();
        return;
      }
      echo(res, entry);
    }),
  );
  return { server, log };
}

function escapeAttribute(text) {
  return text.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
}

function visitorHandler(log) {
  return withBody((req, res, body) => {
    const { url, entry } = record(log, "visitor", req, body);
    if (url.pathname === "/") {
      res.writeHead(200, HTML);
      res.end("<!doctype html><title>cookie_relay visitor</title><p>visitor origin</p>");
      return;
    }
    if (url.pathname === "/form") {
      const to = escapeAttribute(url.searchParams.get("to") ?? "");
      res.writeHead(200, HTML);
      res.end(
        `<!doctype html><title>cookie_relay form</title>` +
          `<form id="f" method="post" action="${to}"><input name="a" value="1"></form>` +
          `<a id="l" href="${to}">link</a>`,
      );
      return;
    }
    if (url.pathname === "/set-evil") {
      echo(res, entry, {
        "Set-Cookie": [
          "__Host-probe_at=EVILHTTP; HttpOnly; Secure; SameSite=Strict; Path=/",
          "probe_plain=EVILHTTP; HttpOnly; Secure; SameSite=Strict; Path=/",
        ],
      });
      return;
    }
    echo(res, entry);
  });
}

export function createVisitor() {
  const log = [];
  return { server: http.createServer(visitorHandler(log)), log };
}

/** B 와 같은 처리기(기록도 같은 log)를 쓰는 평문 서버. `[::1]` 갈래에서 B 를 IPv6 루프백에 세울 때 쓴다. */
export function createPlainVisitor(log) {
  return http.createServer(visitorHandler(log));
}

/**
 * `[::1]` 갈래의 앞단. 받은 바이트를 그대로 `127.0.0.1:<upstreamPort>` 로 넘기는 TCP 중계라 HTTP 는 건드리지 않는다
 * (브라우저가 보낸 Host 는 `[::1]:<앞단 포트>` 그대로 관리 화면에 닿는다). 다른 갈래와 같은 관리 화면 프로세스를 `::1`
 * 로도 받아 같은 질문(같은 쿠키, 같은 요청)을 던지려는 것이다. 연결을 모아 두었다가 `closeAllConnections` 로 끊는다.
 */
export function tcpFront6(upstreamPort) {
  const sockets = new Set();
  const server = net.createServer((client) => {
    const upstream = net.connect({ host: "127.0.0.1", port: upstreamPort });
    for (const socket of [client, upstream]) {
      sockets.add(socket);
      socket.on("close", () => sockets.delete(socket));
      socket.on("error", () => socket.destroy());
    }
    client.pipe(upstream);
    upstream.pipe(client);
  });
  server.closeAllConnections = () => {
    for (const socket of sockets) socket.destroy();
  };
  return server;
}

export function createTlsVisitor(tls, log) {
  return https.createServer({ key: tls.key, cert: tls.cert }, visitorHandler(log));
}

const HOP_BY_HOP = new Set(["connection", "keep-alive", "transfer-encoding"]);

export function tlsFront(tls, upstreamPort, hostMode) {
  return https.createServer({ key: tls.key, cert: tls.cert }, (req, res) => {
    // node 는 Host 를 문자열로만 받는다. 이름이 겹친 머리만 배열로 둔다(줄을 따로 보낸다).
    const headers = {};
    for (const [name, value] of pairs(req.rawHeaders)) {
      const lower = name.toLowerCase();
      if (lower === "x-forwarded-for" || lower === "x-forwarded-proto" || HOP_BY_HOP.has(lower)) continue;
      if (lower === "host") continue;
      const had = headers[name];
      headers[name] = had === undefined ? value : [...(Array.isArray(had) ? had : [had]), value];
    }
    const host = req.headers.host ?? "";
    headers.Host = hostMode === "name" ? host.replace(/:\d+$/, "") : host;
    headers["X-Forwarded-For"] = req.socket.remoteAddress ?? "";
    headers["X-Forwarded-Proto"] = "https";
    const upstream = http.request(
      { host: "127.0.0.1", port: upstreamPort, method: req.method, path: req.url, headers },
      (answer) => {
        // 겹친 Set-Cookie 줄을 지키려고 받은 머리를 줄 그대로 넘긴다.
        const raw = [];
        for (const [name, value] of pairs(answer.rawHeaders)) {
          if (!HOP_BY_HOP.has(name.toLowerCase())) raw.push(name, value);
        }
        res.writeHead(answer.statusCode ?? 502, raw);
        answer.pipe(res);
      },
    );
    upstream.on("error", () => {
      if (!res.headersSent) res.writeHead(502);
      res.end();
    });
    req.pipe(upstream);
  });
}
