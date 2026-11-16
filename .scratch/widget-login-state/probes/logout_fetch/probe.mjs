// widget-login-state 프로브: 창 없이 부르는 로그아웃이 통하는 조건.
//
// ADR 0061 결정 "로그아웃"은 위젯이 위젯 설정의 로그아웃 주소를 "브라우저가 쿠키를 실어 보내는 요청으로 직접" 부른다고 정했고,
// 그것이 통하는 조건(같은 출처, 같은 등록 도메인, 끝점이 출처를 허용할 때)을 어림으로 적은 뒤 이 기능의 명세가 재라고 넘겼다
// (같은 ADR Consequences "재지 않은 것"). 이 스크립트가 그것을 잰다. 위젯 코드는 아직 없으므로 위젯이 보낼 요청을 흉내 낸다.
// 본문 없는 POST 이고 fetch 의 credentials 는 "include" 다.
//
// 띄우는 것(모두 127.0.0.1, 네트워크를 타지 않는다)
//   - https 서버 하나. 다섯 이름으로 답한다. 자체 서명 인증서를 openssl 로 짓고 브라우저는 인증서 오류를 무시한다
//       app.site.test      사이트의 페이지 (S)
//       auth.site.test     사이트가 로그인과 API 를 따로 둔 주소 (A). S 와 등록 도메인이 같고 출처가 다르다
//       auth.other.test    사이트가 로그인을 맡긴, S 와 등록 도메인이 다른 주소 (X)
//       widget.site.test   사이트와 등록 도메인이 같은 위젯의 출처 (W1)
//       widget.other.test  사이트와 등록 도메인이 다른 위젯의 출처 (W2)
//   - 그 다섯 이름으로 가는 CONNECT 만 위 서버로 잇는 프록시 하나. 브라우저를 이 프록시로 띄워 이름을 127.0.0.1 에 맞춘다.
//     hosts 파일은 건드리지 않는다. 세 엔진이 같은 방법을 쓴다(Chromium 의 --host-resolver-rules 는 다른 엔진에 없다).
//     인증서와 프록시는 ../kit.mjs 의 것이다
//
// 재는 칸(엔진마다). 본 갈래는 끝점이 204 로 답한다. 위젯이 도는 자리 일곱 x 쿠키의 SameSite 셋 x 부르는 법 다섯
//   위젯이 도는 자리
//     inPageSameOrigin           페이지 안 방식. S 의 페이지가 S 의 로그아웃 주소를 부른다
//     inPageOtherOriginSameSite  페이지 안 방식. S 의 페이지가 A 의 로그아웃 주소를 부른다
//     inPageCrossSite            페이지 안 방식. S 의 페이지가 X 의 로그아웃 주소를 부른다
//     iframeSameSite             iframe 방식. S 의 페이지 안 W1 문서가 S 의 로그아웃 주소를 부른다
//     iframeCrossSite            iframe 방식. S 의 페이지 안 W2 문서가 S 의 로그아웃 주소를 부른다
//     windowSameSite             URL 방식. S 의 페이지가 window.open 으로 연 W1 창이 S 의 로그아웃 주소를 부른다
//     windowCrossSite            URL 방식. S 의 페이지가 연 W2 창이 S 의 로그아웃 주소를 부른다
//   쿠키의 SameSite  Lax, Strict, None (셋 다 Secure, HttpOnly, Path=/ 이고 Domain 을 적지 않는다)
//   부르는 법
//     corsModeNoHeaders    fetch mode "cors", redirect "follow". 끝점이 CORS 응답 머리를 내지 않는다
//     corsModeAllowed      fetch mode "cors", redirect "follow". 끝점이 요청의 Origin 을 Access-Control-Allow-Origin 으로
//                          되돌리고 자격 증명을 허용한다
//     noCorsMode           fetch mode "no-cors", redirect "follow". 끝점이 CORS 응답 머리를 내지 않는다
//     corsManualNoHeaders  fetch mode "cors", redirect "manual". 끝점이 CORS 응답 머리를 내지 않는다
//     corsManualAllowed    fetch mode "cors", redirect "manual". 끝점이 출처를 허용한다
//   뒤의 둘이 명세가 고른 부르는 법이다(명세 "로그아웃"의 "창 없이 부르기"). 앞의 셋은 그것을 고르기 전에 견준 것이다
//   칸마다 적는 것
//     secFetchSite  끝점이 받은 Sec-Fetch-Site        originSeen  끝점이 받은 Origin (포트는 <port> 로 바꾼다)
//     cookieSent    로그아웃 요청에 쿠키가 실렸는가     preflight   그 요청 앞에 OPTIONS 가 왔는가
//     fetch         위젯 쪽에서 본 fetch 의 끝(resolved 면 응답의 type 과 status, rejected 면 오류 이름)
//     loggedOut     그 뒤 새 탭에서 연 로그아웃 주소의 출처로 가는 요청에 쿠키가 없는가(= 사이트가 보기에 로그아웃됐는가)
//   덤(redirect). 끝점이 303 으로 답하며 그 응답에 지우는 Set-Cookie 를 실을 때, fetch 의 redirect 가 "follow" 와 "manual"
//   일 때 각각 쿠키가 지워지는지와 다음 주소(/after)를 브라우저가 부르는지. 본 갈래와 같은 자리 일곱과 SameSite 셋에서
//   부르는 법 셋(mode 와 끝점의 CORS 응답 머리의 짝: noCorsMode, corsModeNoHeaders, corsModeAllowed)을 redirect 두 값으로
//   본다. 이 갈래의 칸은 sent(요청이 끝점에 닿았는가)도 적는다. 브라우저가 요청을 아예 보내지 않는 조합이 있어서다(첫
//   실행에서 다른 출처로 가는 mode "no-cors" 와 redirect "manual" 이 그랬다). 닿지 않은 칸은 그 조합(다른 출처, mode
//   "no-cors", redirect "manual")이고, 같은 자리와 SameSite 와 부르는 법의 "follow" 칸이 끝점에 닿았고, fetch 가 TypeError 로
//   거절됐을 때만 측정으로 센다. 주소가 틀렸거나 서버가 죽어 닿지 않은 것이라면 "follow" 칸도 닿지 않기 때문이다. 그 밖의
//   조합이 닿지 않으면 측정이 아니라고 센다. 그 밖의 조합이 닿지 않은 것은 아직 본 적이 없어, 나면 사람이 원본 기록을 보고 가른다
//
// 표지(측정이 재려던 상황에서 났는지). 하나라도 없으면 종료 코드가 0 이 아니다.
//   칸마다
//     - 쿠키가 심겼다: 로그아웃을 부르기 전에 로그아웃 주소의 출처로 보낸 요청에 이 회차의 쿠키 값이 실렸다
//     - 요청이 끝점에 닿았다: 이 회차의 이름표가 붙은 POST /logout 이 서버 기록에 정확히 하나다
//     - 재려던 출처 관계가 났다: 끝점이 받은 Sec-Fetch-Site 가 그 자리의 기대(same-origin, same-site, cross-site)와 같다.
//       이름 넷이 뜻한 대로 "같은 등록 도메인"과 "다른 등록 도메인"으로 읽혔다는 것을 브라우저의 판정으로 본다
//     표지가 빠진 칸은 측정이 아니라고 세어 결과(facts)에 넣지 않고 unmeasured 에 까닭과 함께 적는다
//   엔진마다
//     - 대조(로그아웃을 부르지 않은 회차): 새 탭에서 연 요청에 쿠키가 실린다. 이것이 없으면 loggedOut 을 읽을 수 없다.
//       SameSite=Strict 쿠키가 새 탭의 첫 이동에 실리지 않는 엔진이라면 "지워졌다"와 가를 수 없기 때문이다
//     - 양성 대조: inPageSameOrigin 의 SameSite=Lax 칸에서 loggedOut 이 참이다(지우는 Set-Cookie 가 받아들여지면 참이 된다).
//       견주려던 부르는 법(noCorsMode)과 명세가 고른 부르는 법(corsManualNoHeaders)을 따로 본다
//     - SameSite 가 걸리는 환경이다: SameSite=Strict 쿠키가 windowSameSite 에서는 실리고 windowCrossSite 에서는 실리지 않는다
//
// 결과는 포트를 <port> 로 바꾼 뒤 같은 폴더의 expected.json 과 견준다. 다르면 다른 자리를 찍고 1 로 끝난다.
// expected.json 은 미리 적은 기대가 아니라 첫 측정의 결과를 --update 로 받아 적은 것이다. 원본 기록(서버가 받은 요청 전부)은
// --out 폴더의 results.json 에 쓴다. 쿠키 값은 이 스크립트가 지은 회차 이름표이고 비밀이 아니다.
//
// 엔진은 Playwright 가 내려받은 빌드다(Chromium 은 headless shell). 제품 브라우저(Chrome, Firefox, Safari)가 아니고 프로필은
// Playwright 의 기본값이다. 서드파티 쿠키를 막는 설정은 사람마다 달라, 등록 도메인이 다른 칸의 결과는 "이 빌드의 기본값에서"다.
//
// 돌리기: node .scratch/widget-login-state/probes/logout_fetch/probe.mjs [--engine chromium|firefox|webkit|all] [--out 폴더] [--update]

import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import https from "node:https";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parseArgs } from "node:util";

import { createProxy, differences, listen, makeCert, writeExpected } from "../kit.mjs";

const HERE = import.meta.dirname;
const ROOT = join(HERE, "..", "..", "..", "..");
const APP = join(ROOT, "web", "apps", "widget");
const EXPECTED = join(HERE, "expected.json");
const load = createRequire(join(APP, "package.json"));

const HOSTS = {
  S: "app.site.test",
  A: "auth.site.test",
  X: "auth.other.test",
  W1: "widget.site.test",
  W2: "widget.other.test",
};
const HOST_NAMES = new Set(Object.values(HOSTS));

const CONTEXTS = [
  { key: "inPageSameOrigin", actor: "page", widget: null, logout: "S", relation: "same-origin" },
  { key: "inPageOtherOriginSameSite", actor: "page", widget: null, logout: "A", relation: "same-site" },
  { key: "inPageCrossSite", actor: "page", widget: null, logout: "X", relation: "cross-site" },
  { key: "iframeSameSite", actor: "iframe", widget: "W1", logout: "S", relation: "same-site" },
  { key: "iframeCrossSite", actor: "iframe", widget: "W2", logout: "S", relation: "cross-site" },
  { key: "windowSameSite", actor: "window", widget: "W1", logout: "S", relation: "same-site" },
  { key: "windowCrossSite", actor: "window", widget: "W2", logout: "S", relation: "cross-site" },
];
const SAME_SITES = ["Lax", "Strict", "None"];
const VARIANTS = [
  { key: "corsModeNoHeaders", mode: "cors", cors: "none", redirect: "follow" },
  { key: "corsModeAllowed", mode: "cors", cors: "allow", redirect: "follow" },
  { key: "noCorsMode", mode: "no-cors", cors: "none", redirect: "follow" },
  { key: "corsManualNoHeaders", mode: "cors", cors: "none", redirect: "manual" },
  { key: "corsManualAllowed", mode: "cors", cors: "allow", redirect: "manual" },
];
// 덤 갈래는 mode 와 끝점의 CORS 응답 머리의 짝만 여기서 고르고 redirect 는 REDIRECT_MODES 의 두 값으로 따로 돈다.
const REDIRECT_VARIANTS = ["noCorsMode", "corsModeNoHeaders", "corsModeAllowed"];
// 덤 갈래에서 명세가 고른 부르는 법(mode "cors", redirect "manual")에 해당하는 짝이다. 요약 줄이 이 둘을 센다.
const CHOSEN_REDIRECT_VARIANTS = ["corsModeNoHeaders", "corsModeAllowed"];
// "follow" 가 먼저다. "manual" 칸이 끝점에 닿지 않았을 때 그 앞의 "follow" 칸이 닿았는지를 본다.
const REDIRECT_MODES = ["follow", "manual"];
const ALL_ENGINES = ["chromium", "firefox", "webkit"];
const STEP_TIMEOUT_MS = 20_000;
const ARRIVAL_TIMEOUT_MS = 5_000;

const { values: args } = parseArgs({
  options: {
    engine: { type: "string", default: "all" },
    out: { type: "string" },
    update: { type: "boolean", default: false },
  },
});
const ENGINES = args.engine === "all" ? ALL_ENGINES : [args.engine];
if (!ENGINES.every((engine) => ALL_ENGINES.includes(engine))) {
  console.error("--engine 은 chromium, firefox, webkit, all 가운데 하나다");
  process.exit(2);
}
const OUT = args.out ?? mkdtempSync(join(tmpdir(), "logout-fetch-"));
mkdirSync(OUT, { recursive: true });

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const markers = [];
const mark = (name, ok, detail = "") => {
  markers.push({ name, ok, detail });
  console.log(`${ok ? "표지 있음" : "표지 없음"}  ${name}${detail ? `  (${detail})` : ""}`);
};

// ---------------------------------------------------------------------------------------------------------------------
// 서버

const BLANK = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>probe</title></head><body></body></html>';

function createSite(tls) {
  const log = [];
  const server = https.createServer(tls, (request, response) => {
    const url = new URL(request.url ?? "/", `https://${request.headers.host}`);
    const run = url.searchParams.get("run");
    const sameSite = url.searchParams.get("ss");
    const cookie = /(?:^|;\s*)sid=([^;]*)/.exec(request.headers.cookie ?? "")?.[1] ?? null;
    log.push({
      host: url.hostname,
      path: url.pathname,
      method: request.method,
      run,
      phase: url.searchParams.get("phase"),
      cookie,
      origin: request.headers.origin ?? null,
      secFetchSite: request.headers["sec-fetch-site"] ?? null,
      secFetchMode: request.headers["sec-fetch-mode"] ?? null,
    });
    const allow = url.searchParams.get("cors") === "allow" && request.headers.origin !== undefined;
    const corsHeaders = allow
      ? {
          "Access-Control-Allow-Origin": request.headers.origin,
          "Access-Control-Allow-Credentials": "true",
          Vary: "Origin",
        }
      : {};
    const html = (body) => {
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
      response.end(body);
    };
    if (url.pathname === "/login" && request.method === "GET") {
      response.writeHead(200, {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
        "Set-Cookie": `sid=${run}; Path=/; Secure; HttpOnly; SameSite=${sameSite}`,
      });
      response.end("logged in");
      return;
    }
    if (url.pathname === "/whoami" && request.method === "GET") {
      response.writeHead(200, { "Content-Type": "application/json", "Cache-Control": "no-store" });
      response.end(JSON.stringify({ cookie }));
      return;
    }
    if (url.pathname === "/logout" && request.method === "OPTIONS") {
      response.writeHead(204, {
        ...corsHeaders,
        ...(allow ? { "Access-Control-Allow-Methods": "POST", "Access-Control-Allow-Headers": "content-type" } : {}),
      });
      response.end();
      return;
    }
    if (url.pathname === "/logout" && request.method === "POST") {
      const cleared = `sid=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=${sameSite}`;
      if (url.searchParams.get("redirect") === "1") {
        response.writeHead(303, {
          ...corsHeaders,
          "Cache-Control": "no-store",
          "Set-Cookie": cleared,
          Location: `/after?run=${run}`,
        });
      } else {
        response.writeHead(204, { ...corsHeaders, "Cache-Control": "no-store", "Set-Cookie": cleared });
      }
      response.end();
      return;
    }
    if (url.pathname === "/after" && request.method === "GET") {
      response.writeHead(200, { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" });
      response.end("after");
      return;
    }
    if ((url.pathname === "/page" || url.pathname === "/widget") && request.method === "GET") {
      html(BLANK);
      return;
    }
    if (url.pathname === "/host" && request.method === "GET") {
      const frame = new URL(url.searchParams.get("frame") ?? "about:blank");
      if (!HOST_NAMES.has(frame.hostname)) {
        response.writeHead(400);
        response.end();
        return;
      }
      html(BLANK.replace("<body></body>", `<body><iframe src="${frame.href.replaceAll('"', "%22")}"></iframe></body>`));
      return;
    }
    response.writeHead(404);
    response.end();
  });
  return { server, log };
}

// ---------------------------------------------------------------------------------------------------------------------
// 한 칸

// 위젯이 보낼 요청을 흉내 낸다. 본문과 덧붙인 머리가 없는 POST 이고 응답은 읽지 않는다.
const callLogout = async ({ url, mode, redirect }) => {
  try {
    const answer = await fetch(url, { method: "POST", credentials: "include", mode, redirect });
    return { settled: "resolved", type: answer.type, status: answer.status };
  } catch (error) {
    return { settled: "rejected", name: error instanceof Error ? error.name : "unknown" };
  }
};

let counter = 0;
const newRun = () => `r${++counter}x${randomBytes(4).toString("hex")}`;

async function whoami(page, origin, run, phase) {
  const answer = await page.goto(`${origin}/whoami?run=${run}&phase=${phase}`);
  const body = await answer.json();
  return body.cookie;
}

async function arrived(log, run, path, method) {
  const deadline = Date.now() + ARRIVAL_TIMEOUT_MS;
  for (;;) {
    const found = log.filter((entry) => entry.run === run && entry.path === path && entry.method === method);
    if (found.length > 0 || Date.now() > deadline) return found;
    await sleep(50);
  }
}

async function openActor(context, env, spec, run) {
  const origin = (name) => `https://${HOSTS[name]}:${env.port}`;
  const page = await context.newPage();
  page.setDefaultTimeout(STEP_TIMEOUT_MS);
  if (spec.actor === "page") {
    await page.goto(`${origin("S")}/page?run=${run}`);
    return page.mainFrame();
  }
  const widgetUrl = `${origin(spec.widget)}/widget?run=${run}`;
  if (spec.actor === "iframe") {
    await page.goto(`${origin("S")}/host?run=${run}&frame=${encodeURIComponent(widgetUrl)}`);
    const frame = page.frames().find((candidate) => candidate.url() === widgetUrl);
    if (frame === undefined) throw new Error(`iframe 문서가 뜨지 않았다: ${widgetUrl}`);
    return frame;
  }
  await page.goto(`${origin("S")}/page?run=${run}`);
  const [popup] = await Promise.all([
    context.waitForEvent("page"),
    page.evaluate((target) => {
      window.open(target);
    }, widgetUrl),
  ]);
  popup.setDefaultTimeout(STEP_TIMEOUT_MS);
  await popup.waitForLoadState("load");
  if (popup.url() !== widgetUrl) throw new Error(`연 창의 주소가 다르다: ${popup.url()}`);
  return popup.mainFrame();
}

const portless = (value, port) => (value === null ? null : value.replaceAll(`:${port}`, ":<port>"));

// redirect 가 null 이면 본 갈래다. 끝점은 204 로 답하고 fetch 의 redirect 는 부르는 법이 정한다. 값이 있으면 덤 갈래다.
// 끝점은 303 으로 답하고 fetch 의 redirect 는 그 값이다.
// siblingArrived 는 덤 갈래의 "manual" 칸에만 준다. 같은 자리와 SameSite 와 부르는 법의 "follow" 칸이 끝점에 닿았다는 뜻이다.
async function runCell(browser, env, spec, sameSite, variant, redirect, siblingArrived = false) {
  const run = newRun();
  const logoutOrigin = `https://${HOSTS[spec.logout]}:${env.port}`;
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  try {
    const first = await context.newPage();
    first.setDefaultTimeout(STEP_TIMEOUT_MS);
    await first.goto(`${logoutOrigin}/login?run=${run}&ss=${sameSite}`);
    const before = await whoami(first, logoutOrigin, run, "before");
    const actor = await openActor(context, env, spec, run);
    const query = `run=${run}&ss=${sameSite}&cors=${variant.cors}${redirect === null ? "" : "&redirect=1"}`;
    const fetched = await actor.evaluate(callLogout, {
      url: `${logoutOrigin}/logout?${query}`,
      mode: variant.mode,
      redirect: redirect ?? variant.redirect,
    });
    const posts = await arrived(env.log, run, "/logout", "POST");
    const preflights = env.log.filter((entry) => entry.run === run && entry.path === "/logout" && entry.method === "OPTIONS");
    const last = await context.newPage();
    last.setDefaultTimeout(STEP_TIMEOUT_MS);
    const after = await whoami(last, logoutOrigin, run, "after");
    const follow = env.log.filter((entry) => entry.run === run && entry.path === "/after");

    const problems = [];
    if (before !== run) problems.push(`쿠키가 심기지 않았다(부르기 전 요청의 쿠키 ${JSON.stringify(before)})`);
    // 닿지 않은 것을 측정으로 세는 조합은 첫 실행에서 본 하나다. 그 밖의 조합이 닿지 않으면 아래에서 측정이 아니라고 센다.
    const unsentCombination = redirect === "manual" && variant.mode === "no-cors" && spec.relation !== "same-origin";
    const refused = fetched.settled === "rejected" && fetched.name === "TypeError";
    if (problems.length === 0 && posts.length === 0 && siblingArrived && unsentCombination && refused) {
      return { run, fact: { sent: false, fetch: fetched, loggedOut: after === null, afterRequested: follow.length > 0 } };
    }
    if (posts.length !== 1) problems.push(`POST /logout 이 ${posts.length}번 닿았다(fetch ${JSON.stringify(fetched)})`);
    else if (posts[0].secFetchSite !== spec.relation) {
      problems.push(`Sec-Fetch-Site 가 ${JSON.stringify(posts[0].secFetchSite)} 이다(기대 ${spec.relation})`);
    }
    if (problems.length > 0) return { run, problems };
    const fact = {
      secFetchSite: posts[0].secFetchSite,
      originSeen: portless(posts[0].origin, env.port),
      cookieSent: posts[0].cookie === run,
      preflight: preflights.length > 0,
      fetch: fetched,
      loggedOut: after === null,
    };
    if (redirect !== null) {
      fact.sent = true;
      fact.afterRequested = follow.length > 0;
      fact.afterCookieSent = follow.length > 0 ? follow[0].cookie === run : null;
    }
    return { run, fact };
  } finally {
    await context.close();
  }
}

async function runControl(browser, env, sameSite) {
  const run = newRun();
  const origin = `https://${HOSTS.S}:${env.port}`;
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  try {
    const first = await context.newPage();
    first.setDefaultTimeout(STEP_TIMEOUT_MS);
    await first.goto(`${origin}/login?run=${run}&ss=${sameSite}`);
    const last = await context.newPage();
    last.setDefaultTimeout(STEP_TIMEOUT_MS);
    return (await whoami(last, origin, run, "control")) === run;
  } finally {
    await context.close();
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// 한 엔진

const yes = (value) => (value ? "예" : "아니오");
const fetchText = (fetched) =>
  fetched.settled === "resolved" ? `resolved(${fetched.type}, ${fetched.status})` : `rejected(${fetched.name})`;

async function runEngine(name, env, playwright) {
  let browser;
  try {
    browser = await playwright[name].launch({ proxy: { server: `http://127.0.0.1:${env.proxyPort}` } });
  } catch (error) {
    mark(`${name}: 브라우저를 띄웠다`, false, String(error?.message ?? error).split("\n")[0]);
    return null;
  }
  mark(`${name}: 브라우저를 띄웠다`, true, browser.version());
  const version = browser.version();
  const facts = { control: {}, cells: {}, redirect: {} };
  const unmeasured = [];
  try {
    for (const sameSite of SAME_SITES) facts.control[sameSite] = await runControl(browser, env, sameSite);
    for (const spec of CONTEXTS) {
      facts.cells[spec.key] = {};
      for (const sameSite of SAME_SITES) {
        facts.cells[spec.key][sameSite] = {};
        for (const variant of VARIANTS) {
          const label = `${name} ${spec.key} ${sameSite} ${variant.key}`;
          let done;
          try {
            done = await runCell(browser, env, spec, sameSite, variant, null);
          } catch (error) {
            done = { run: null, problems: [`예외: ${String(error?.message ?? error).split("\n")[0]}`] };
          }
          if (done.fact === undefined) {
            unmeasured.push({ cell: label, problems: done.problems });
            console.log(`측정 아님  ${label}: ${done.problems.join("; ")}`);
            continue;
          }
          facts.cells[spec.key][sameSite][variant.key] = done.fact;
          console.log(
            `${label}: site=${done.fact.secFetchSite} origin=${done.fact.originSeen} 쿠키 실림=${yes(done.fact.cookieSent)} ` +
              `fetch=${fetchText(done.fact.fetch)} 로그아웃됨=${yes(done.fact.loggedOut)}${done.fact.preflight ? " (OPTIONS 가 먼저 왔다)" : ""}`,
          );
        }
      }
    }
    for (const spec of CONTEXTS) {
      facts.redirect[spec.key] = {};
      for (const sameSite of SAME_SITES) {
        facts.redirect[spec.key][sameSite] = {};
        for (const variantKey of REDIRECT_VARIANTS) {
          const variant = VARIANTS.find((candidate) => candidate.key === variantKey);
          facts.redirect[spec.key][sameSite][variantKey] = {};
          let followArrived = false;
          for (const redirect of REDIRECT_MODES) {
            const label = `${name} redirect ${spec.key} ${sameSite} ${variantKey} ${redirect}`;
            let done;
            try {
              done = await runCell(browser, env, spec, sameSite, variant, redirect, redirect === "manual" && followArrived);
            } catch (error) {
              done = { run: null, problems: [`예외: ${String(error?.message ?? error).split("\n")[0]}`] };
            }
            if (done.fact === undefined) {
              unmeasured.push({ cell: label, problems: done.problems });
              console.log(`측정 아님  ${label}: ${done.problems.join("; ")}`);
              continue;
            }
            if (redirect === "follow") followArrived = done.fact.sent;
            facts.redirect[spec.key][sameSite][variantKey][redirect] = done.fact;
            console.log(
              `${label}: 끝점에 닿았다=${yes(done.fact.sent)}` +
                `${done.fact.sent ? ` 쿠키 실림=${yes(done.fact.cookieSent)}` : ""} fetch=${fetchText(done.fact.fetch)} ` +
                `로그아웃됨=${yes(done.fact.loggedOut)} /after 를 불렀다=${yes(done.fact.afterRequested)}`,
            );
          }
        }
      }
    }
  } finally {
    await browser.close().catch(() => undefined);
  }

  mark(`${name}: 표지가 빠진 칸이 없다`, unmeasured.length === 0, `측정 아님 ${unmeasured.length}칸`);
  const controls = SAME_SITES.filter((sameSite) => facts.control[sameSite] !== true);
  mark(
    `${name}: 대조. 로그아웃을 부르지 않으면 새 탭의 요청에 쿠키가 실린다`,
    controls.length === 0,
    controls.length === 0 ? "Lax, Strict, None" : `실리지 않은 것 ${controls.join(", ")}`,
  );
  const positive = facts.cells.inPageSameOrigin?.Lax?.noCorsMode;
  mark(
    `${name}: 양성 대조. 같은 출처의 로그아웃 뒤에는 새 탭의 요청에 쿠키가 없다`,
    positive !== undefined && positive.cookieSent && positive.loggedOut,
  );
  const chosen = facts.cells.inPageSameOrigin?.Lax?.corsManualNoHeaders;
  mark(
    `${name}: 양성 대조. 명세가 고른 부르는 법(mode "cors", redirect "manual")으로 부른 같은 출처의 로그아웃 뒤에도 쿠키가 없다`,
    chosen !== undefined && chosen.cookieSent && chosen.loggedOut,
  );
  const strictSame = Object.values(facts.cells.windowSameSite?.Strict ?? {});
  const strictCross = Object.values(facts.cells.windowCrossSite?.Strict ?? {});
  mark(
    `${name}: SameSite 가 걸리는 환경이다(Strict 쿠키가 같은 등록 도메인의 창에서는 실리고 다른 등록 도메인의 창에서는 빠진다)`,
    strictSame.length > 0 &&
      strictCross.length > 0 &&
      strictSame.every((fact) => fact.cookieSent) &&
      strictCross.every((fact) => !fact.cookieSent),
  );
  return { version, facts, unmeasured };
}

// README 의 표가 드는 줄임이다. 손으로 세지 않게 여기서 세어 찍는다.
//   rows          본 갈래. 자리와 SameSite 마다 부르는 법 다섯의 결과가 같은지
//   redirectRows  덤 갈래. 자리와 SameSite 마다 명세가 고른 부르는 법(mode "cors", redirect "manual")의 두 칸
//   unsent        덤 갈래에서 요청이 끝점에 닿지 않은 칸.   followed  덤 갈래에서 브라우저가 다음 주소를 부른 칸.
//                 둘 다 "자리 부르는 법 redirect" 마다 그 일이 난 SameSite 를 모은다
function summarize(facts) {
  const rows = {};
  const redirectRows = {};
  const unsent = {};
  const followed = {};
  let preflights = 0;
  const collect = (bucket, key, sameSite) => {
    bucket[key] = [...(bucket[key] ?? []), sameSite];
  };
  for (const spec of CONTEXTS) {
    rows[spec.key] = {};
    redirectRows[spec.key] = {};
    for (const sameSite of SAME_SITES) {
      const cells = Object.values(facts.cells[spec.key]?.[sameSite] ?? {});
      preflights += cells.filter((fact) => fact.preflight).length;
      if (cells.length !== VARIANTS.length) rows[spec.key][sameSite] = "빠진 칸이 있다";
      else if (cells.every((fact) => fact.cookieSent && fact.loggedOut)) rows[spec.key][sameSite] = "통했다";
      else if (cells.every((fact) => !fact.cookieSent && !fact.loggedOut)) rows[spec.key][sameSite] = "통하지 않았다";
      else rows[spec.key][sameSite] = "부르는 법마다 다르다";

      const byVariant = facts.redirect[spec.key]?.[sameSite] ?? {};
      for (const variantKey of REDIRECT_VARIANTS) {
        for (const redirect of REDIRECT_MODES) {
          const fact = byVariant[variantKey]?.[redirect];
          if (fact === undefined) continue;
          preflights += fact.preflight === true ? 1 : 0;
          if (!fact.sent) collect(unsent, `${spec.key} ${variantKey} ${redirect}`, sameSite);
          if (fact.afterRequested) collect(followed, `${spec.key} ${variantKey} ${redirect}`, sameSite);
        }
      }
      const chosen = CHOSEN_REDIRECT_VARIANTS.map((variantKey) => byVariant[variantKey]?.manual);
      if (chosen.some((fact) => fact === undefined)) redirectRows[spec.key][sameSite] = "빠진 칸이 있다";
      else if (chosen.some((fact) => !fact.sent || fact.afterRequested)) {
        redirectRows[spec.key][sameSite] = "끝점에 닿지 않았거나 다음 주소를 부른 칸이 있다";
      } else if (chosen.every((fact) => fact.cookieSent && fact.loggedOut)) redirectRows[spec.key][sameSite] = "통했다";
      else if (chosen.every((fact) => !fact.cookieSent && !fact.loggedOut)) {
        redirectRows[spec.key][sameSite] = "통하지 않았다";
      } else redirectRows[spec.key][sameSite] = "끝점의 CORS 응답 머리마다 다르다";
    }
  }
  return { rows, redirectRows, unsent, followed, preflights };
}

// ---------------------------------------------------------------------------------------------------------------------

const versions = {
  playwright: load("@playwright/test/package.json").version,
  node: process.version,
  platform: process.platform,
};
const cert = makeCert(OUT, [...HOST_NAMES]);
if ("problem" in cert) {
  console.error(`인증서를 짓지 못했다(openssl): ${cert.problem}`);
  process.exit(1);
}
const site = createSite(cert);
const port = await listen(site.server);
const proxy = createProxy(() => port, [...HOST_NAMES]);
const proxyPort = await listen(proxy.server);
const playwright = load("@playwright/test");

const facts = {};
const unmeasured = {};
let failure = null;
try {
  for (const name of ENGINES) {
    const done = await runEngine(name, { port, proxyPort, log: site.log }, playwright);
    if (done === null) continue;
    versions[name] = done.version;
    facts[name] = done.facts;
    unmeasured[name] = done.unmeasured;
  }
} catch (error) {
  failure = error;
  console.error(error);
} finally {
  for (const socket of proxy.sockets) socket.destroy();
  await new Promise((resolve) => proxy.server.close(resolve));
  site.server.closeAllConnections();
  await new Promise((resolve) => site.server.close(resolve));
}
console.log(`판: ${JSON.stringify(versions)}`);
if (proxy.refusedHosts.size > 0) console.log(`프록시가 잇지 않은 이름: ${[...proxy.refusedHosts].join(", ")}`);

const summaries = {};
for (const [name, measured] of Object.entries(facts)) {
  summaries[name] = summarize(measured);
  const perSameSite = (row) => SAME_SITES.map((sameSite) => `${sameSite}=${row[sameSite]}`).join(", ");
  const perCell = (bucket) => {
    const entries = Object.entries(bucket);
    if (entries.length === 0) return " 없음";
    return entries.map(([key, sameSites]) => `\n        ${key} (SameSite ${sameSites.join(", ")})`).join("");
  };
  for (const [key, row] of Object.entries(summaries[name].rows)) {
    console.log(`요약  ${name} 204 끝점, 부르는 법 다섯  ${key}: ${perSameSite(row)}`);
  }
  for (const [key, row] of Object.entries(summaries[name].redirectRows)) {
    console.log(`요약  ${name} 303 끝점, 고른 부르는 법  ${key}: ${perSameSite(row)}`);
  }
  console.log(`요약  ${name} 303 끝점에서 요청이 끝점에 닿지 않은 칸:${perCell(summaries[name].unsent)}`);
  console.log(`요약  ${name} 303 끝점에서 브라우저가 다음 주소를 부른 칸:${perCell(summaries[name].followed)}`);
  console.log(`요약  ${name} 요청 앞에 OPTIONS 가 온 칸: ${summaries[name].preflights}`);
}

writeFileSync(
  join(OUT, "results.json"),
  JSON.stringify(
    { versions, markers, summaries, facts, unmeasured, refusedHosts: [...proxy.refusedHosts], log: site.log },
    null,
    2,
  ),
);
console.log(`원본 기록: ${join(OUT, "results.json")}`);

let expectedOk = true;
if (failure === null) {
  const previous = existsSync(EXPECTED) ? JSON.parse(readFileSync(EXPECTED, "utf-8")) : { versions: {}, facts: {} };
  if (args.update) {
    const { written, skipped } = writeExpected(EXPECTED, previous, versions, facts, markers);
    console.log(
      written.length > 0
        ? `expected.json 에 표지가 모두 선 엔진의 결과를 썼다: ${written.join(", ")}`
        : "expected.json 에 쓴 것이 없다",
    );
    if (skipped.length > 0) console.log(`표지가 빠져 expected.json 에 쓰지 않은 엔진: ${skipped.join(", ")}`);
  } else if (existsSync(EXPECTED)) {
    const drift = ENGINES.flatMap((name) => differences(previous.facts[name], facts[name], `facts.${name}`));
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
