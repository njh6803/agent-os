// admin-login 티켓 09: 관리 화면 e2e 가 서버에 계정을 만든 뒤 로그인 요청으로 받은 쿠키(`__Host-` 접두, HttpOnly; Secure;
// SameSite=Strict; Path=/)를 브라우저 문맥에 심어야 한다. Playwright 가 `http://127.0.0.1:<포트>` 에서 Secure 쿠키를
// 저장하고 보내는지, 어느 길(요청 문맥, 브라우저 문맥의 request, storageState 넘기기, 페이지 fetch, addCookies)이 되는지
// 실제 Chromium 으로 잰다. 결정은 하지 않고 결과만 낸다.
//   node .scratch/admin-login/probes/playwright_secure_cookie/probe.mjs [--out <폴더>]
//
// 띄우는 것: node http 서버 하나(127.0.0.1 의 빈 포트). 앱도 파이썬 서버도 띄우지 않는다.
//   POST /login-plain   대조용. `t_plain=v3; HttpOnly; SameSite=Strict; Path=/`(Secure 도 접두사도 없다) 하나를 싣고 204
//   POST /login   Set-Cookie 둘(`__Host-t_at=v1; HttpOnly; Secure; SameSite=Strict; Path=/` 와
//                 `__Host-t_rt=v2; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=3600`)을 싣고 204
//   GET  /who     받은 Cookie 머리를 JSON 으로 돌려준다(`{"cookie": "<머리 글자 그대로>" | null}`)
//   GET  /        간단한 HTML
//
// 갈래(결과의 키)
//   a  playwright.request.newContext({ baseURL }) 로 POST /login 한 뒤 같은 문맥의 GET /who 에 쿠키가 실리는가, storageState() 에 드는가
//   b  브라우저 문맥의 context.request 로 POST /login 한 뒤 page.goto('/') 한 페이지의 fetch('/who') 에 쿠키가 실리는가,
//      context.cookies() 의 httpOnly·secure·sameSite
//   c  a 의 storageState() 를 browser.newContext({ storageState }) 에 넘기면 그 문맥의 페이지 fetch('/who') 에 쿠키가 실리는가
//   d  대조. 페이지에서 fetch('/login', { method: 'POST' }) 로 로그인해도 같은가
//   a-control-plain  a 의 대조. 같은 요청 문맥 흐름에 Secure 없는 쿠키를 실으면 GET /who 에 실리는가(흐름 자체가 쿠키를 나르는지)
//   a-localhost      a 의 대조. 같은 흐름을 `http://localhost:<포트>` 로 치면 Secure 쿠키가 실리는가(호스트 예외가 있는지)
//   e  덤. a 의 storageState 쿠키 값을 context.addCookies 로 심는 길(url 로 주는 모양 둘과 domain·path 로 주는 모양)
//
// 표지(재려던 상황이 났는지). 하나라도 없으면 종료 코드가 0 이 아니다. 갈래의 결과(되는지, 안 되는지) 자체는 단언하지 않는다.
//   - 서버가 POST /login 마다 Set-Cookie 둘을(대조의 /login-plain 은 하나를) 실어 답했다(서버 쪽 셈)와, a·b 에서는 클라이언트가 받은 응답 머리에도 그 줄 둘이 있다
//   - 쿠키가 실렸는지 읽은 /who 요청마다 서버가 그 요청을 받았고, 서버가 본 Cookie 머리가 응답 본문의 것과 같다
//   - 페이지 갈래의 출처가 `http://127.0.0.1:<포트>` 이고 그 페이지의 window.isSecureContext 가 true 다(루프백 예외가 이 브라우저에서 선다)
//
// 쿠키 값(v1, v2)은 이 스크립트가 지은 고정 문자열이고 비밀이 아니다. 네트워크를 타지 않는다. 한 회차에 3초쯤 걸린다(README 에 잰 값을 적었다).

import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import http from "node:http";
import { createRequire } from "node:module";
import { release, tmpdir } from "node:os";
import { join } from "node:path";
import { parseArgs } from "node:util";

const HERE = import.meta.dirname;
const ROOT = join(HERE, "..", "..", "..", "..");
const load = createRequire(join(ROOT, "web", "apps", "admin", "package.json"));
const { chromium, request } = load("@playwright/test");

const { values: args } = parseArgs({ options: { out: { type: "string" } } });
const OUT = args.out ?? mkdtempSync(join(tmpdir(), "playwright-secure-cookie-"));
mkdirSync(OUT, { recursive: true });

const SET_COOKIE = [
  "__Host-t_at=v1; HttpOnly; Secure; SameSite=Strict; Path=/",
  "__Host-t_rt=v2; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=3600",
];

const PLAIN_COOKIE = "t_plain=v3; HttpOnly; SameSite=Strict; Path=/";

const markers = [];
const mark = (name, ok, detail = "") => {
  markers.push({ name, ok, detail });
  console.log(`${ok ? "표지 있음" : "표지 없음"}  ${name}${detail ? `  (${detail})` : ""}`);
};

// ---------------------------------------------------------------------------------------------------------------------
// 서버

const log = [];
let loginsServed = 0;
let plainLoginsServed = 0;
const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://placeholder");
  const entry = {
    seq: log.length,
    method: req.method,
    path: url.pathname,
    tag: url.searchParams.get("tag"),
    cookie: req.headers.cookie ?? null,
  };
  log.push(entry);
  req.resume();
  req.on("end", () => {
    if (req.method === "POST" && url.pathname === "/login") {
      loginsServed += 1;
      res.writeHead(204, { "Set-Cookie": SET_COOKIE, "Cache-Control": "no-store" });
      res.end();
      return;
    }
    if (req.method === "POST" && url.pathname === "/login-plain") {
      plainLoginsServed += 1;
      res.writeHead(204, { "Set-Cookie": PLAIN_COOKIE, "Cache-Control": "no-store" });
      res.end();
      return;
    }
    if (req.method === "GET" && url.pathname === "/who") {
      res.writeHead(200, { "Content-Type": "application/json", "Cache-Control": "no-store" });
      res.end(JSON.stringify({ cookie: req.headers.cookie ?? null }));
      return;
    }
    if (req.method === "GET" && url.pathname === "/") {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
      res.end("<!doctype html><title>playwright_secure_cookie</title><p>probe page</p>");
      return;
    }
    res.writeHead(404);
    res.end();
  });
});
await new Promise((resolve, reject) => {
  server.once("error", reject);
  server.listen(0, "127.0.0.1", resolve);
});
const port = server.address().port;
const baseURL = `http://127.0.0.1:${port}`;

// ---------------------------------------------------------------------------------------------------------------------
// 관찰 도구

const cookieView = (cookie) => ({
  name: cookie.name,
  value: cookie.value,
  domain: cookie.domain,
  path: cookie.path,
  httpOnly: cookie.httpOnly,
  secure: cookie.secure,
  sameSite: cookie.sameSite,
  session: cookie.expires === -1,
});

const sortedCookies = (cookies) => cookies.map(cookieView).sort((a, b) => a.name.localeCompare(b.name));

/** 요청 문맥으로 /who 를 읽는다. 서버가 본 Cookie 와 응답 본문의 것이 같은지 표지에 쓰려고 함께 돌려준다. */
async function whoViaRequest(api, tag) {
  const response = await api.get(`/who?tag=${tag}`);
  return { status: response.status(), body: await response.json(), tag };
}

/** 페이지에서 fetch 로 /who 를 읽는다. */
async function whoViaPage(page, tag) {
  return page.evaluate(async (target) => {
    try {
      const answer = await fetch(target);
      return { status: answer.status, body: await answer.json() };
    } catch (error) {
      return { error: `${error.name}: ${error.message}` };
    }
  }, `/who?tag=${tag}`);
}

const whoChecks = []; // [tag, 응답 본문의 cookie] — 표지에서 서버 기록과 맞댄다.
function noteWho(tag, result) {
  const body = result?.body;
  whoChecks.push([tag, body === undefined ? undefined : body.cookie]);
  return {
    status: result?.status ?? null,
    error: result?.error ?? null,
    cookieHeaderAtServer: body === undefined ? null : body.cookie,
  };
}

function setCookieLines(response) {
  return response
    .headersArray()
    .filter((header) => header.name.toLowerCase() === "set-cookie")
    .map((header) => header.value);
}

async function pageAt(context) {
  const page = await context.newPage();
  await page.goto("/");
  const origin = await page.evaluate(() => location.origin);
  const secureContext = await page.evaluate(() => window.isSecureContext);
  const documentCookie = await page.evaluate(() => document.cookie);
  return { page, origin, secureContext, documentCookie };
}

// ---------------------------------------------------------------------------------------------------------------------
// 갈래

const versions = {
  playwright: load("@playwright/test/package.json").version,
  node: process.version,
  os: `${process.platform} ${release()}`,
};
const browser = await chromium.launch();
versions.chromium = browser.version();
console.log(`판: ${JSON.stringify(versions)}`);

const facts = {};
const pageFacts = []; // 페이지를 연 갈래마다 [갈래, origin, isSecureContext]
const setCookieReceived = { a: null, b: null, aLocalhost: null };
let failure = null;
try {
  // a. 요청 문맥.
  const api = await request.newContext({ baseURL });
  const loginA = await api.post("/login");
  setCookieReceived.a = setCookieLines(loginA);
  const whoA = await whoViaRequest(api, "a");
  const state = await api.storageState();
  facts.a = {
    loginStatus: loginA.status(),
    setCookieAtClient: setCookieReceived.a,
    who: noteWho("a", whoA),
    storageStateCookies: sortedCookies(state.cookies),
  };
  await api.dispose();

  // a 의 대조 둘.
  {
    const plainApi = await request.newContext({ baseURL });
    const plainLogin = await plainApi.post("/login-plain");
    const plainWho = await whoViaRequest(plainApi, "a-plain");
    facts.aControlPlain = {
      loginStatus: plainLogin.status(),
      setCookieAtClient: setCookieLines(plainLogin),
      who: noteWho("a-plain", plainWho),
      storageStateCookies: sortedCookies((await plainApi.storageState()).cookies),
    };
    await plainApi.dispose();

    const localhostApi = await request.newContext({ baseURL: `http://localhost:${port}` });
    const localhostLogin = await localhostApi.post("/login");
    setCookieReceived.aLocalhost = setCookieLines(localhostLogin);
    const localhostWho = await whoViaRequest(localhostApi, "a-localhost");
    facts.aLocalhost = {
      loginStatus: localhostLogin.status(),
      setCookieAtClient: setCookieReceived.aLocalhost,
      who: noteWho("a-localhost", localhostWho),
      storageStateCookies: sortedCookies((await localhostApi.storageState()).cookies),
    };
    await localhostApi.dispose();
  }

  // b. 브라우저 문맥의 request 로 로그인, 그 문맥의 페이지.
  {
    const context = await browser.newContext({ baseURL });
    const loginB = await context.request.post("/login");
    setCookieReceived.b = setCookieLines(loginB);
    const jarRightAfterLogin = sortedCookies(await context.cookies());
    const opened = await pageAt(context);
    pageFacts.push(["b", opened.origin, opened.secureContext]);
    const whoPage = await whoViaPage(opened.page, "b-page");
    const whoCtx = await whoViaRequest(context.request, "b-context-request");
    facts.b = {
      loginStatus: loginB.status(),
      setCookieAtClient: setCookieReceived.b,
      jarRightAfterLogin,
      page: { origin: opened.origin, isSecureContext: opened.secureContext, documentCookie: opened.documentCookie },
      whoFromPageFetch: noteWho("b-page", whoPage),
      whoFromContextRequest: noteWho("b-context-request", whoCtx),
      jarAfter: sortedCookies(await context.cookies()),
    };
    await context.close();
  }

  // c. a 의 storageState 를 새 브라우저 문맥에 넘긴다.
  {
    const context = await browser.newContext({ baseURL, storageState: state });
    const jarAtStart = sortedCookies(await context.cookies());
    const opened = await pageAt(context);
    pageFacts.push(["c", opened.origin, opened.secureContext]);
    const whoPage = await whoViaPage(opened.page, "c-page");
    facts.c = {
      jarAtStart,
      page: { origin: opened.origin, isSecureContext: opened.secureContext, documentCookie: opened.documentCookie },
      whoFromPageFetch: noteWho("c-page", whoPage),
    };
    await context.close();
  }

  // d. 대조. 페이지의 fetch 로 로그인.
  {
    const context = await browser.newContext({ baseURL });
    const opened = await pageAt(context);
    pageFacts.push(["d", opened.origin, opened.secureContext]);
    const login = await opened.page.evaluate(async () => {
      try {
        const answer = await fetch("/login", { method: "POST" });
        return { status: answer.status };
      } catch (error) {
        return { error: `${error.name}: ${error.message}` };
      }
    });
    const jarRightAfterLogin = sortedCookies(await context.cookies());
    const whoPage = await whoViaPage(opened.page, "d-page");
    facts.d = {
      login,
      jarRightAfterLogin,
      whoFromPageFetch: noteWho("d-page", whoPage),
    };
    await context.close();
  }

  // e. 덤. 로그인 요청 없이 addCookies 로 심는다. 값은 a 의 storageState 에서 옮긴다.
  {
    const fromState = state.cookies.map((cookie) => ({ name: cookie.name, value: cookie.value }));
    const shapes = {
      byUrlBare: fromState.map((cookie) => ({ ...cookie, url: baseURL })),
      byUrl: fromState.map((cookie) => ({
        ...cookie,
        url: baseURL,
        httpOnly: true,
        secure: true,
        sameSite: "Strict",
      })),
      byDomainPath: fromState.map((cookie) => ({
        ...cookie,
        domain: "127.0.0.1",
        path: "/",
        httpOnly: true,
        secure: true,
        sameSite: "Strict",
      })),
    };
    facts.e = {};
    for (const [shape, cookies] of Object.entries(shapes)) {
      const context = await browser.newContext({ baseURL });
      try {
        await context.addCookies(cookies);
        const jarAfterAdd = sortedCookies(await context.cookies());
        const opened = await pageAt(context);
        pageFacts.push([`e-${shape}`, opened.origin, opened.secureContext]);
        const whoPage = await whoViaPage(opened.page, `e-${shape}`);
        facts.e[shape] = { jarAfterAdd, whoFromPageFetch: noteWho(`e-${shape}`, whoPage) };
      } catch (error) {
        facts.e[shape] = { addCookiesError: `${error.name}: ${error.message}`.slice(0, 400) };
      } finally {
        await context.close();
      }
    }
  }
} catch (error) {
  failure = error;
  console.error(error);
} finally {
  await browser.close().catch(() => undefined);
  await new Promise((resolve) => {
    server.closeAllConnections();
    server.close(() => resolve());
  });
}

// ---------------------------------------------------------------------------------------------------------------------
// 표지

const loginsAtServer = log.filter((entry) => entry.method === "POST" && entry.path === "/login").length;
// a, b, c(로그인 없음), d, e(로그인 없음): 로그인은 a, b, d 에서 한 번씩이다.
const plainAtServer = log.filter((entry) => entry.method === "POST" && entry.path === "/login-plain").length;
mark(
  "서버가 POST /login 을 받아 Set-Cookie 둘을 실어 답했다(a, a-localhost, b, d 한 번씩)와 /login-plain 에 하나를 실어 답했다(한 번)",
  loginsServed === 4 && loginsAtServer === 4 && plainLoginsServed === 1 && plainAtServer === 1,
  `서버가 답한 로그인 ${loginsServed}, 받은 로그인 ${loginsAtServer}, plain ${plainLoginsServed}/${plainAtServer}`,
);
mark(
  "a-control-plain: 클라이언트가 받은 응답 머리에 Set-Cookie 한 줄이 서버가 실은 글자 그대로 있다",
  JSON.stringify(facts.aControlPlain?.setCookieAtClient) === JSON.stringify([PLAIN_COOKIE]),
  JSON.stringify(facts.aControlPlain?.setCookieAtClient),
);
for (const key of ["a", "aLocalhost", "b"]) {
  const lines = setCookieReceived[key];
  mark(
    `${key}: 클라이언트가 받은 응답 머리에 Set-Cookie 두 줄이 서버가 실은 글자 그대로 있다`,
    JSON.stringify(lines) === JSON.stringify(SET_COOKIE),
    JSON.stringify(lines),
  );
}
const whoSeenAtServer = whoChecks.map(([tag, cookieInBody]) => {
  const entries = log.filter((entry) => entry.method === "GET" && entry.path === "/who" && entry.tag === tag);
  return { tag, count: entries.length, same: entries.length === 1 && entries[0].cookie === cookieInBody };
});
mark(
  "/who 를 읽은 갈래마다 서버가 그 요청을 하나 받았고 서버가 본 Cookie 머리가 응답 본문의 것과 같다",
  whoSeenAtServer.length > 0 && whoSeenAtServer.every((item) => item.same),
  whoSeenAtServer.map((item) => `${item.tag}:${item.count}${item.same ? "" : "!"}`).join(" "),
);
mark(
  "페이지를 연 갈래마다 출처가 http://127.0.0.1:<포트> 이고 window.isSecureContext 가 true 다",
  pageFacts.length > 0 && pageFacts.every(([, origin, secure]) => origin === baseURL && secure === true),
  pageFacts.map(([name, origin, secure]) => `${name}:${origin === baseURL ? "ok" : origin}:${secure}`).join(" "),
);

writeFileSync(join(OUT, "results.json"), JSON.stringify({ versions, baseURLShape: "http://127.0.0.1:<포트>", markers, facts, serverLog: log }, null, 2));
console.log(JSON.stringify(facts, null, 2));
console.log(`원본 기록: ${join(OUT, "results.json")}`);

const unmarked = markers.filter((marker) => !marker.ok);
if (unmarked.length > 0) console.log(`표지 없는 것 ${unmarked.length}: 이 회차는 측정으로 세지 않는다`);
process.exit(failure === null && unmarked.length === 0 ? 0 : 1);
