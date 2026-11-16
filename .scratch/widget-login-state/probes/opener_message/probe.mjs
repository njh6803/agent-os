// widget-login-state 프로브: URL 방식의 창이 자기를 연 페이지와 메시지를 주고받는 조건.
//
// ADR 0061 결정 "URL 방식"은 사이트의 페이지가 연 창 전체가 위젯이고, 그 창이 자기를 연 창(window.opener)에 토큰을 묻는다고
// 정했다. 다른 출처의 창끼리 그 통로가 서는지는 재지 않은 채 이 기능의 e2e 에 넘겼다(같은 ADR Consequences "재지 않은 것").
// 통로가 서지 않으면 URL 방식의 결정을 다시 봐야 하므로 명세를 쓰는 자리에서 잰다. 위젯 코드는 아직 없으므로 위젯 창이 보낼
// 물음과 사이트의 페이지가 낼 답을 흉내 낸다. 메시지의 이름은 프로브의 것이고(probe/ask, probe/answer) 위젯의 것이 아니다.
//
// 띄우는 것(모두 127.0.0.1, 네트워크를 타지 않는다). 인증서와 프록시는 ../kit.mjs 의 것이고 logout_fetch 와 같은 방법이다
//   - https 서버 하나. 세 이름으로 답한다
//       app.site.test      사이트의 페이지 (S)
//       widget.site.test   사이트와 등록 도메인이 같은 위젯의 출처 (W1)
//       widget.other.test  사이트와 등록 도메인이 다른 위젯의 출처 (W2)
//
// 재는 칸(엔진마다). 위젯 창의 출처 셋 x 여는 법과 그 뒤의 일 열하나
//   위젯 창의 출처   sameOrigin (S 자신), sameSite (W1), crossSite (W2)
//   여는 법과 그 뒤의 일
//     open                 window.open(주소)
//     openSized            window.open(주소, "_blank", "width=420,height=680"). 크기를 준 창
//     openNoopener         window.open(주소, "_blank", "noopener"). 연결을 끊는 옵션
//     anchorBlank          <a target="_blank"> 를 눌러 연다. rel 을 적지 않는다
//     anchorOpener         <a target="_blank" rel="opener"> 를 눌러 연다
//     widgetCoop           open 과 같고, 위젯 창의 응답이 Cross-Origin-Opener-Policy: same-origin 을 싣는다
//     siteCoop             open 과 같고, 사이트의 페이지의 응답이 Cross-Origin-Opener-Policy: same-origin 을 싣는다
//     siteCoopAllowPopups  open 과 같고, 사이트의 페이지의 응답이 same-origin-allow-popups 를 싣는다
//     widgetReloaded       open 으로 연 뒤 위젯 창을 새로 고친다
//     siteNavigated        open 으로 연 뒤 사이트의 페이지가 같은 출처의 다른 문서로 간다(답하는 코드가 없는 문서다)
//     siteClosed           open 으로 연 뒤 사이트의 페이지를 닫는다
//   칸마다 하는 일. 사이트의 페이지가 message 를 듣기 시작하고 위젯 창을 연다. 위젯 창이 window.opener 를 보고, 있으면
//   사이트의 출처를 대상 출처로 적어 묻는다. 사이트의 페이지는 보낸 창이 자기가 연 창이고(손잡이가 있을 때) 출처가 위젯의
//   출처일 때만, 그 창에 위젯의 출처를 대상 출처로 적어 답한다. 위젯 창은 2초까지 답을 기다린다
//   칸마다 적는 것
//     handle            사이트의 페이지가 받은 창 손잡이. window, null(window.open 이 null 을 돌려줬다), none(링크로 열었다)
//     handleClosed      그 손잡이의 closed (손잡이가 없거나 사이트의 페이지를 읽을 수 없으면 null)
//     opener            위젯 창이 본 window.opener. open, null, closed
//     asked             사이트의 페이지가 물음을 받았는가 (사이트의 페이지를 읽을 수 없으면 null)
//     askOrigin         그 물음의 event.origin (포트는 <port> 로 바꾼다)
//     askFromChild      그 물음의 event.source 가 사이트가 든 손잡이와 같은가 (손잡이가 없으면 null)
//     answered          위젯 창이 답을 받았는가
//     answerOrigin      그 답의 event.origin        answerFromOpener  그 답의 event.source 가 window.opener 와 같은가
//
// 표지(측정이 재려던 상황에서 났는지). 하나라도 없으면 종료 코드가 0 이 아니다.
//   칸마다
//     - 위젯 창이 떴다: 새로 뜬 창의 주소가 열려던 위젯 주소와 같다
//     - 보안 컨텍스트다: 위젯 창의 isSecureContext 가 참이다. Cross-Origin-Opener-Policy 는 보안 컨텍스트에서만 걸린다
//     - 응답 머리가 실렸다(머리를 싣는 칸): 서버가 이 회차의 그 문서에 그 값의 머리를 냈다고 기록했다
//     - 그 뒤의 일이 났다: widgetReloaded 는 이 회차의 위젯 문서 요청이 둘이다, siteNavigated 는 사이트의 창의 주소가 다른
//       문서로 바뀌었다, siteClosed 는 사이트의 창이 닫혔다
//     표지가 빠진 칸은 측정이 아니라고 세어 결과(facts)에 넣지 않고 unmeasured 에 까닭과 함께 적는다
//   엔진마다
//     - 양성 대조: open 의 sameOrigin 칸에서 물음이 닿았고 답이 돌아왔다. 프로브의 묻고 답하는 코드가 돈다는 뜻이다
//     - 음성 대조: openNoopener 의 세 칸에서 위젯 창의 window.opener 가 null 이고 답이 없다. 주고받은 칸의 답이 연결을
//       타고 온 것이고, 연결이 끊긴 것을 프로브가 볼 줄 안다는 뜻이다
//   머리를 실은 칸이 주고받지 못한 까닭이 머리인지는 같은 출처 관계의 open 칸(머리만 없다)이 주고받았는지와 견줘 가른다
//
// 결과는 포트를 <port> 로 바꾼 뒤 같은 폴더의 expected.json 과 견준다. 다르면 다른 자리를 찍고 1 로 끝난다.
// expected.json 은 미리 적은 기대가 아니라 첫 측정의 결과를 --update 로 받아 적은 것이다. 원본 기록은 --out 폴더의
// results.json 에 쓴다.
//
// 엔진은 Playwright 가 내려받은 빌드다(Chromium 은 headless shell). 제품 브라우저가 아니고 프로필은 Playwright 의 기본값이다.
// Playwright 는 스크립트가 여는 창을 막지 않는다. 그래서 이 프로브는 브라우저의 팝업 차단을 재지 않는다.
//
// 돌리기: node .scratch/widget-login-state/probes/opener_message/probe.mjs [--engine chromium|firefox|webkit|all] [--out 폴더] [--update]

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
  W1: "widget.site.test",
  W2: "widget.other.test",
};
const HOST_NAMES = Object.values(HOSTS);

const RELATIONS = [
  { key: "sameOrigin", widget: "S" },
  { key: "sameSite", widget: "W1" },
  { key: "crossSite", widget: "W2" },
];
const CASES = [
  { key: "open", how: "open" },
  { key: "openSized", how: "open", features: "width=420,height=680" },
  { key: "openNoopener", how: "open", features: "noopener" },
  { key: "anchorBlank", how: "anchor" },
  { key: "anchorOpener", how: "anchor", rel: "opener" },
  { key: "widgetCoop", how: "open", widgetCoop: "same-origin" },
  { key: "siteCoop", how: "open", siteCoop: "same-origin" },
  { key: "siteCoopAllowPopups", how: "open", siteCoop: "same-origin-allow-popups" },
  { key: "widgetReloaded", how: "open", then: "reloadWidget" },
  { key: "siteNavigated", how: "open", then: "navigateSite" },
  { key: "siteClosed", how: "open", then: "closeSite" },
];
const ALL_ENGINES = ["chromium", "firefox", "webkit"];
const STEP_TIMEOUT_MS = 20_000;
const ANSWER_WAIT_MS = 2_000;

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
const OUT = args.out ?? mkdtempSync(join(tmpdir(), "opener-message-"));
mkdirSync(OUT, { recursive: true });

const markers = [];
const mark = (name, ok, detail = "") => {
  markers.push({ name, ok, detail });
  console.log(`${ok ? "표지 있음" : "표지 없음"}  ${name}${detail ? `  (${detail})` : ""}`);
};

// ---------------------------------------------------------------------------------------------------------------------
// 서버

const BLANK = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>probe</title></head><body></body></html>';
const COOP_VALUES = new Set(["same-origin", "same-origin-allow-popups"]);

function createSite(tls) {
  const log = [];
  const server = https.createServer(tls, (request, response) => {
    const url = new URL(request.url ?? "/", `https://${request.headers.host}`);
    const known = ["/site", "/widget", "/elsewhere"].includes(url.pathname) && request.method === "GET";
    const asked = url.searchParams.get("coop");
    const coop = known && asked !== null && COOP_VALUES.has(asked) ? asked : null;
    log.push({ host: url.hostname, path: url.pathname, method: request.method, run: url.searchParams.get("run"), coop });
    if (!known) {
      response.writeHead(404);
      response.end();
      return;
    }
    response.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      ...(coop === null ? {} : { "Cross-Origin-Opener-Policy": coop }),
    });
    response.end(BLANK);
  });
  return { server, log };
}

// ---------------------------------------------------------------------------------------------------------------------
// 한 칸

// 사이트의 페이지가 할 일을 흉내 낸다. 듣기 시작한 뒤에 창을 연다. 링크로 여는 칸은 링크만 놓고 누르는 것은 바깥에서 한다.
const installSite = ({ widgetUrl, widgetOrigin, how, features, rel }) => {
  window.__seen = [];
  window.__child = null;
  window.addEventListener("message", (event) => {
    if (event.data?.type !== "probe/ask") return;
    const fromChild = window.__child === null ? null : event.source === window.__child;
    window.__seen.push({ origin: event.origin, fromChild });
    if (fromChild === false || event.origin !== widgetOrigin || event.source === null) return;
    event.source.postMessage({ type: "probe/answer", id: event.data.id }, widgetOrigin);
  });
  if (how === "open") {
    window.__child = features === null ? window.open(widgetUrl) : window.open(widgetUrl, "_blank", features);
    return window.__child === null ? "null" : "window";
  }
  const link = document.createElement("a");
  link.id = "open";
  link.href = widgetUrl;
  link.target = "_blank";
  if (rel !== null) link.rel = rel;
  link.textContent = "open";
  document.body.append(link);
  return "none";
};

const readSite = () => ({
  seen: window.__seen,
  handleClosed: window.__child === null ? null : window.__child.closed,
});

// 위젯 창이 할 일을 흉내 낸다. 자기를 연 창이 없거나 닫혔으면 묻지 않는다.
const askOpener = async ({ siteOrigin, id, waitMs }) => {
  const secure = window.isSecureContext;
  const opener = window.opener;
  if (opener === null) return { secure, opener: "null", answer: null };
  if (opener.closed) return { secure, opener: "closed", answer: null };
  const answer = await new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), waitMs);
    window.addEventListener("message", (event) => {
      if (event.data?.type !== "probe/answer" || event.data.id !== id) return;
      clearTimeout(timer);
      resolve({ origin: event.origin, fromOpener: event.source === window.opener });
    });
    opener.postMessage({ type: "probe/ask", id }, siteOrigin);
  });
  return { secure, opener: "open", answer };
};

let counter = 0;
const newRun = () => `r${++counter}x${randomBytes(4).toString("hex")}`;
const portless = (value, port) => (value === null ? null : value.replaceAll(`:${port}`, ":<port>"));

async function runCell(browser, env, relation, spec) {
  const run = newRun();
  const origin = (name) => `https://${HOSTS[name]}:${env.port}`;
  const siteOrigin = origin("S");
  const widgetOrigin = origin(relation.widget);
  const widgetUrl = `${widgetOrigin}/widget?run=${run}${spec.widgetCoop === undefined ? "" : `&coop=${spec.widgetCoop}`}`;
  const siteUrl = `${siteOrigin}/site?run=${run}${spec.siteCoop === undefined ? "" : `&coop=${spec.siteCoop}`}`;
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  try {
    const page = await context.newPage();
    page.setDefaultTimeout(STEP_TIMEOUT_MS);
    await page.goto(siteUrl);
    const opened = context.waitForEvent("page", { timeout: STEP_TIMEOUT_MS });
    const handle = await page.evaluate(installSite, {
      widgetUrl,
      widgetOrigin,
      how: spec.how,
      features: spec.features ?? null,
      rel: spec.rel ?? null,
    });
    if (spec.how === "anchor") await page.click("#open");
    const popup = await opened;
    popup.setDefaultTimeout(STEP_TIMEOUT_MS);
    await popup.waitForLoadState("load");

    const problems = [];
    if (spec.then === "reloadWidget") {
      await popup.reload();
      await popup.waitForLoadState("load");
      const loads = env.log.filter((entry) => entry.run === run && entry.path === "/widget").length;
      if (loads !== 2) problems.push(`위젯 문서 요청이 ${loads}번이다(새로 고친 뒤 기대 2)`);
    }
    if (spec.then === "navigateSite") {
      await page.goto(`${siteOrigin}/elsewhere?run=${run}`);
      if (new URL(page.url()).pathname !== "/elsewhere") problems.push(`사이트의 창이 옮겨 가지 않았다: ${page.url()}`);
    }
    if (spec.then === "closeSite") {
      await page.close();
      if (!page.isClosed()) problems.push("사이트의 창이 닫히지 않았다");
    }
    if (popup.url() !== widgetUrl) problems.push(`새로 뜬 창의 주소가 다르다: ${popup.url()}`);
    for (const [path, value] of [
      ["/site", spec.siteCoop],
      ["/widget", spec.widgetCoop],
    ]) {
      if (value === undefined) continue;
      const sent = env.log.some((entry) => entry.run === run && entry.path === path && entry.coop === value);
      if (!sent) problems.push(`${path} 의 응답에 Cross-Origin-Opener-Policy: ${value} 가 실렸다는 기록이 없다`);
    }

    const asked = await popup.evaluate(askOpener, { siteOrigin, id: run, waitMs: ANSWER_WAIT_MS });
    if (asked.secure !== true) problems.push("위젯 창이 보안 컨텍스트가 아니다");
    const siteReadable = spec.then !== "navigateSite" && spec.then !== "closeSite";
    const site = siteReadable ? await page.evaluate(readSite) : null;
    if (problems.length > 0) return { run, problems };

    const question = site === null ? null : (site.seen[0] ?? null);
    return {
      run,
      fact: {
        handle,
        handleClosed: site === null ? null : site.handleClosed,
        opener: asked.opener,
        asked: site === null ? null : site.seen.length > 0,
        askOrigin: question === null ? null : portless(question.origin, env.port),
        askFromChild: question === null ? null : question.fromChild,
        answered: asked.answer !== null,
        answerOrigin: asked.answer === null ? null : portless(asked.answer.origin, env.port),
        answerFromOpener: asked.answer === null ? null : asked.answer.fromOpener,
      },
    };
  } finally {
    await context.close();
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// 한 엔진

const outcome = (fact) => {
  if (fact.answered) return "주고받았다";
  if (fact.opener !== "open") return `주고받지 못했다(window.opener 가 ${fact.opener})`;
  return "주고받지 못했다(답이 없다)";
};

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
  const facts = {};
  const unmeasured = [];
  try {
    for (const spec of CASES) {
      facts[spec.key] = {};
      for (const relation of RELATIONS) {
        const label = `${name} ${spec.key} ${relation.key}`;
        let done;
        try {
          done = await runCell(browser, env, relation, spec);
        } catch (error) {
          done = { run: null, problems: [`예외: ${String(error?.message ?? error).split("\n")[0]}`] };
        }
        if (done.fact === undefined) {
          unmeasured.push({ cell: label, problems: done.problems });
          console.log(`측정 아님  ${label}: ${done.problems.join("; ")}`);
          continue;
        }
        facts[spec.key][relation.key] = done.fact;
        console.log(`${label}: ${JSON.stringify(done.fact)}`);
      }
    }
  } finally {
    await browser.close().catch(() => undefined);
  }

  mark(`${name}: 표지가 빠진 칸이 없다`, unmeasured.length === 0, `측정 아님 ${unmeasured.length}칸`);
  const positive = facts.open?.sameOrigin;
  mark(
    `${name}: 양성 대조. 같은 출처로 연 창이 물었고 답을 받았다`,
    positive !== undefined && positive.asked === true && positive.answered && positive.answerFromOpener === true,
  );
  const cut = Object.values(facts.openNoopener ?? {});
  mark(
    `${name}: 음성 대조. noopener 로 연 창은 window.opener 가 null 이고 답을 받지 못했다`,
    cut.length === RELATIONS.length && cut.every((fact) => fact.opener === "null" && !fact.answered),
  );
  return { version, facts, unmeasured };
}

// README 의 표가 드는 줄임이다. 여는 법마다 출처 셋의 결과를 한 줄로 찍는다.
function summarize(facts) {
  const rows = {};
  for (const spec of CASES) {
    rows[spec.key] = {};
    for (const relation of RELATIONS) {
      const fact = facts[spec.key]?.[relation.key];
      rows[spec.key][relation.key] = fact === undefined ? "빠진 칸" : outcome(fact);
    }
  }
  return rows;
}

// ---------------------------------------------------------------------------------------------------------------------

const versions = {
  playwright: load("@playwright/test/package.json").version,
  node: process.version,
  platform: process.platform,
};
const cert = makeCert(OUT, HOST_NAMES);
if ("problem" in cert) {
  console.error(`인증서를 짓지 못했다(openssl): ${cert.problem}`);
  process.exit(1);
}
const site = createSite(cert);
const port = await listen(site.server);
const proxy = createProxy(() => port, HOST_NAMES);
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
  for (const [key, row] of Object.entries(summaries[name])) {
    console.log(`요약  ${name} ${key}: ${RELATIONS.map((relation) => `${relation.key}=${row[relation.key]}`).join(", ")}`);
  }
}

writeFileSync(
  join(OUT, "results.json"),
  JSON.stringify({ versions, markers, summaries, facts, unmeasured, refusedHosts: [...proxy.refusedHosts], log: site.log }, null, 2),
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
