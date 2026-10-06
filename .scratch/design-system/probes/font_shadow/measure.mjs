// design-system 글꼴 프로브: 페이지 안 위젯(Shadow DOM 커스텀 요소)에 한글 웹폰트를 싣는 길을 실제 브라우저에서 잰다.
//   node .scratch/design-system/probes/font_shadow/measure.mjs <pretendard 패키지 폴더> [--browsers chromium,firefox,webkit]
//        [--playwright <playwright-core 폴더>] [--out <결과 json>]
// <pretendard 패키지 폴더>는 sizes.mjs 와 같은 자리(저장소 밖에서 푼 `package/`)다. 글꼴 파일은 거기서 바로 낸다.
// Playwright 는 기본으로 저장소 web/apps/admin 에 깔린 @playwright/test 를 부른다(`pnpm -C web install` 뒤).
// 그 판이 기대하는 브라우저 빌드가 %LOCALAPPDATA%\ms-playwright 에 없으면 그 브라우저는 "launch 실패"로 남는다.
// 다른 판의 브라우저 빌드만 깔려 있으면 그 판의 playwright-core 폴더를 --playwright 로 준다(이 프로브는 아무것도
// 설치하지 않는다). 브라우저는 Playwright 기본값(헤드리스)으로 띄운다. stdout 에는 브라우저마다 참조 폭과 사례별 한 줄
// 요약을 내고, 사례의 세부(detail)까지 든 JSON 은 --out 이 있을 때 그 파일에 쓴다.
//
// 띄우는 것(127.0.0.1, 8890~8899 에서 빈 포트 둘을 고른다)
//   사이트    /case/<이름> 은 사례 페이지다. 사이트 CSS·본문을 두고, 끝의 인라인 script 가 위젯 번들을 흉내 낸다
//             (문서에 무엇을 더하고 shadow root 에 무엇을 넣는가). /font/<경로> 는 패키지 dist/web 의 파일이다.
//   글꼴 출처 /font/<경로> 만 낸다. 위젯 번들의 출처(Agent OS)에서 글꼴을 받는 경우다. ?cors=1 이면
//             Access-Control-Allow-Origin: * 를 붙인다.
// 사례마다 새 브라우저 컨텍스트(빈 캐시)를 열고, load → networkidle → document.fonts.ready → 300ms → networkidle 뒤에 잰다.
//
// 판정 재료(사례마다)
//   network  서버가 받은 /font/ 요청(어느 서버, 경로, Origin, Sec-Fetch-Mode, 낸 바이트)과 브라우저의 requestfailed
//   fonts    document.fonts 의 항목(family, weight, status)과 document.fonts.status
//   width    같은 글자열(20px)의 폭. 참조 페이지(ref)에서 같은 브라우저로 잰 폭과 0.02px 안에서 맞으면 그 이름을 붙이고,
//            어느 것과도 맞지 않으면 other(폭)이다(q2 에서 font-family 가 없는 사이트 글자는 브라우저 기본 글꼴이라 other).
//            font = agent-os-sans(Pretendard Regular), black = Pretendard Black, mono = 없는 이름 뒤의 monospace,
//            serif = serif. 글꼴이 적용됐을 때만 font(또는 black)와 맞는다
//   platform chromium 만. CDP CSS.getPlatformFontsForNode 로 그 요소의 글자를 그린 글꼴 이름과 isCustomFont
//   rules    shadow 안 <style> 의 sheet.cssRules 와 adoptedStyleSheets 의 규칙 종류(@font-face 규칙이 파싱되어 남았나)
//   console  error·warning 메시지(CORS 차단 등)
//
// 사례
//   q1-*  @font-face 를 어디에 선언하나. 위젯 글자는 인라인 style 로 font-family: "agent-os-sans", monospace 를 가진다.
//         사이트에도 같은 family 를 가진 글자를 둬서 shadow 에 선언한 글꼴이 문서로 새는지 같이 본다.
//   q2-*  상속. 문서에 agent-os-sans 를 선언해 두고(글꼴 적용은 q1 과 떼어 낸다) 위젯 글자는 font-family 가 없다.
//         사이트의 body·*·호스트 태그 규칙과 shadow 의 :host·감싼 요소 규칙 가운데 무엇이 이기나.
//   q3-*  문서에 선언하는 길이 사이트에 새는 것. 사이트 글자는 font-family: "Pretendard", monospace 다.
//   q4-*  Pretendard 패키지 CSS 를 그대로 문서에 걸고 SENTENCE 하나만 그릴 때 받는 파일 수와 바이트.

import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs";
import http from "node:http";
import { createRequire } from "node:module";
import { release } from "node:os";
import { dirname, extname, join, normalize, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SENTENCE = "승인을 기다리고 있습니다. 허가하거나 거부해 주세요.";
const LATIN = "Agent OS widget 0123456789";
const HOST = "127.0.0.1";
const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "..");

const args = process.argv.slice(2);
const option = (name) => {
  const i = args.indexOf(name);
  return i === -1 ? null : args[i + 1];
};
const positional = args.filter((arg, i) => !arg.startsWith("--") && !args[i - 1]?.startsWith("--"));
const pkg = resolve(positional[0] ?? ".");
const web = join(pkg, "dist", "web");
const out = option("--out") === null ? null : resolve(option("--out"));
const browserNames = (option("--browsers") ?? "chromium,firefox,webkit").split(",");
const playwrightPath = option("--playwright");
const playwright =
  playwrightPath === null
    ? createRequire(join(REPO, "web", "apps", "admin", "package.json"))("@playwright/test")
    : createRequire(import.meta.url)(resolve(playwrightPath));
const playwrightVersion = (() => {
  const base =
    playwrightPath === null
      ? dirname(
          createRequire(join(REPO, "web", "apps", "admin", "package.json")).resolve(
            "@playwright/test/package.json",
          ),
        )
      : resolve(playwrightPath);
  return JSON.parse(readFileSync(join(base, "package.json"), "utf-8")).version;
})();

const sleep = (ms) => new Promise((ok) => setTimeout(ok, ms));
const TYPES = {
  ".css": "text/css; charset=utf-8",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".html": "text/html; charset=utf-8",
};

// ---------- 서버 ----------
const log = [];
const ports = { site: 0, font: 0 };

function serveFont(res, req, url, server) {
  const rel = decodeURIComponent(url.pathname.slice("/font/".length));
  const file = normalize(join(web, rel));
  const entry = {
    server,
    path: rel,
    case: url.searchParams.get("case"),
    origin: req.headers.origin ?? null,
    secFetchMode: req.headers["sec-fetch-mode"] ?? null,
    bytes: 0,
    status: 404,
  };
  log.push(entry);
  if (relative(web, file).startsWith("..") || !existsSync(file)) {
    res.writeHead(404).end();
    return;
  }
  const headers = { "Content-Type": TYPES[extname(file)] ?? "application/octet-stream" };
  if (url.searchParams.get("cors") === "1") {
    headers["Access-Control-Allow-Origin"] = "*";
  }
  const body = readFileSync(file);
  entry.bytes = body.length;
  entry.status = 200;
  res.writeHead(200, headers).end(body);
}

function listen(server, from) {
  return new Promise((ok, fail) => {
    const attempt = (port) => {
      if (port > 8899) {
        fail(new Error("8890~8899 에 빈 포트가 없다"));
        return;
      }
      server.once("error", () => attempt(port + 1));
      server.listen(port, HOST, () => ok(port));
    };
    attempt(from);
  });
}

// ---------- 사례 페이지 ----------
const fontUrl = (name, file, { origin = "site", cors = false } = {}) => {
  const port = origin === "site" ? ports.site : ports.font;
  const query = `case=${name}${cors ? "&cors=1" : ""}`;
  return `http://${HOST}:${String(port)}/font/static/woff2/${file}?${query}`;
};
const face = (family, url) =>
  `@font-face { font-family: "${family}"; src: url("${url}") format("woff2"); font-weight: 400; font-style: normal; font-display: block; }`;

const SPAN = "display: inline-block; white-space: nowrap; font-size: 20px; font-weight: 400;";
const spans = (prefix, family) => {
  const style = family === null ? SPAN : `${SPAN} font-family: ${family};`;
  return `<span id="${prefix}-ko" style='${style}'>${SENTENCE}</span><br><span id="${prefix}-en" style='${style}'>${LATIN}</span>`;
};

// 위젯 번들을 흉내 낸다. 문자열로 페이지에 들어가 사이트 출처에서 돈다.
function widgetBundle(cfg) {
  if (cfg.docStyle) {
    const style = document.createElement("style");
    style.id = "widget-doc-style";
    style.textContent = cfg.docStyle;
    document.head.append(style);
  }
  if (cfg.docApi) {
    const fontFace = new FontFace(cfg.docApi.family, `url("${cfg.docApi.url}")`, {
      weight: "400",
      style: "normal",
      display: "block",
    });
    document.fonts.add(fontFace);
  }
  class AgentOsWidget extends HTMLElement {
    constructor() {
      super();
      const root = this.attachShadow({ mode: "open" });
      if (cfg.shadowStyle) {
        const style = document.createElement("style");
        style.textContent = cfg.shadowStyle;
        root.append(style);
      }
      if (cfg.shadowAdopted) {
        const sheet = new CSSStyleSheet();
        sheet.replaceSync(cfg.shadowAdopted);
        root.adoptedStyleSheets = [sheet];
      }
      const wrap = document.createElement("div");
      wrap.id = "w-wrap";
      wrap.innerHTML = cfg.inner;
      root.append(wrap);
    }
  }
  customElements.define("agent-os-widget", AgentOsWidget);
  document.body.append(document.createElement("agent-os-widget"));
}

const FONT = '"agent-os-sans", monospace';
const PRET = '"Pretendard", monospace';

function cases() {
  const regular = (name, opts) => fontUrl(name, "Pretendard-Regular.woff2", opts);
  const black = (name) => fontUrl(name, "Pretendard-Black.woff2");
  const list = [];
  const add = (name, spec) => list.push({ name, ...spec });

  // 참조 폭. 사이트 글자 넷(이름마다 ko·en)을 light DOM 에 두고 위젯은 없다.
  add("ref", {
    group: "ref",
    siteHead: `<style>${face("agent-os-sans", regular("ref"))}${face("ref-black", black("ref"))}</style>`,
    siteBody: [
      spans("ref-font", FONT),
      spans("ref-black", '"ref-black", monospace'),
      spans("ref-mono", '"agent-os-missing", monospace'),
      spans("ref-serif", "serif"),
    ].join("<br>"),
    widget: null,
  });

  // q1: @font-face 의 자리
  const q1 = (name, widget, siteHead = "") =>
    add(name, {
      group: "q1",
      siteHead,
      siteBody: spans("site", FONT),
      widget: { inner: spans("w", FONT), ...widget },
    });
  q1("q1-none", {});
  q1("q1-doc-style", { docStyle: face("agent-os-sans", regular("q1-doc-style")) });
  q1("q1-doc-api", { docApi: { family: "agent-os-sans", url: regular("q1-doc-api") } });
  q1("q1-shadow-style", { shadowStyle: face("agent-os-sans", regular("q1-shadow-style")) });
  q1("q1-shadow-adopted", { shadowAdopted: face("agent-os-sans", regular("q1-shadow-adopted")) });
  q1("q1-shadow-style-host", {
    // :host 규칙과 같은 시트에 둔 경우. 위젯이 실제로 쓸 모양이다.
    shadowStyle: `${face("agent-os-sans", regular("q1-shadow-style-host"))} :host { display: block; }`,
  });
  q1("q1-xorigin-nocors", {
    docStyle: face("agent-os-sans", regular("q1-xorigin-nocors", { origin: "font" })),
  });
  q1("q1-xorigin-cors", {
    docStyle: face("agent-os-sans", regular("q1-xorigin-cors", { origin: "font", cors: true })),
  });
  q1("q1-xorigin-cors-api", {
    docApi: { family: "agent-os-sans", url: regular("q1-xorigin-cors-api", { origin: "font", cors: true }) },
  });

  // q2: 상속. agent-os-sans 는 문서에 선언해 둔다(widget docStyle). 위젯 글자는 font-family 가 없다.
  const q2 = (name, siteCss, shadowStyle) =>
    add(name, {
      group: "q2",
      siteHead: `<style>${siteCss}</style>`,
      siteBody: spans("site", null),
      widget: { docStyle: face("agent-os-sans", regular(name)), shadowStyle, inner: spans("w", null) },
    });
  q2("q2-body", "body { font-family: serif; }", "");
  q2("q2-body-host", "body { font-family: serif; }", `:host { font-family: ${FONT}; }`);
  q2("q2-star-host", "* { font-family: serif; }", `:host { font-family: ${FONT}; }`);
  q2("q2-tag-host", "agent-os-widget { font-family: serif; }", `:host { font-family: ${FONT}; }`);
  q2("q2-star-host-important", "* { font-family: serif; }", `:host { font-family: ${FONT} !important; }`);
  q2(
    "q2-tag-important-host-important",
    "agent-os-widget { font-family: serif !important; }",
    `:host { font-family: ${FONT} !important; }`,
  );
  q2("q2-star-wrap", "* { font-family: serif; }", `#w-wrap { font-family: ${FONT}; }`);
  q2("q2-star-wrap-all", "* { font-family: serif; }", `:host, #w-wrap, #w-wrap * { font-family: ${FONT}; }`);

  // q3: 문서 선언이 사이트에 새는 것
  const q3 = (name, { siteHead = "", widget = {}, widgetFamily = PRET }) =>
    add(name, {
      group: "q3",
      siteHead,
      siteBody: spans("site", PRET),
      widget: { inner: spans("w", widgetFamily), ...widget },
    });
  const siteOwn = (name) => `<style>${face("Pretendard", black(name))}</style>`;
  q3("q3-site-none", {});
  q3("q3-site-none-widget-doc", { widget: { docStyle: face("Pretendard", regular("q3-site-none-widget-doc")) } });
  q3("q3-site-none-widget-api", {
    widget: { docApi: { family: "Pretendard", url: regular("q3-site-none-widget-api") } },
  });
  q3("q3-site-own", { siteHead: siteOwn("q3-site-own") });
  q3("q3-site-own-widget-doc", {
    siteHead: siteOwn("q3-site-own-widget-doc"),
    widget: { docStyle: face("Pretendard", regular("q3-site-own-widget-doc")) },
  });
  q3("q3-site-own-widget-api", {
    siteHead: siteOwn("q3-site-own-widget-api"),
    widget: { docApi: { family: "Pretendard", url: regular("q3-site-own-widget-api") } },
  });
  q3("q3-site-own-widget-shadow", {
    siteHead: siteOwn("q3-site-own-widget-shadow"),
    widget: { shadowStyle: face("Pretendard", regular("q3-site-own-widget-shadow")) },
  });
  q3("q3-unique-doc", {
    widget: { docStyle: face("agent-os-sans", regular("q3-unique-doc")) },
    widgetFamily: FONT,
  });
  q3("q3-unique-api", {
    widget: { docApi: { family: "agent-os-sans", url: regular("q3-unique-api") } },
    widgetFamily: FONT,
  });

  // q4: 패키지 CSS 를 그대로 걸고 SENTENCE 하나만 그린다
  const q4 = (name, css, family) =>
    add(name, {
      group: "q4",
      siteHead: `<link rel="stylesheet" href="/font/${css}?case=${name}"><style>body { font-family: ${family}; font-weight: 400; }</style>`,
      siteBody: `<p>${SENTENCE}</p>`,
      widget: null,
    });
  // pretendard.css 는 9 굵기를 굵기마다 전체 파일 하나로 선언한다(src 첫머리가 local('Pretendard Regular') 다).
  // Pretendard-Regular.css 는 이름과 달리 400 굵기 하나의 동적 서브셋(92 조각) CSS 다.
  q4("q4-full-static", "static/pretendard.css", "'Pretendard'");
  q4("q4-dynamic-static", "static/pretendard-dynamic-subset.css", "'Pretendard'");
  q4("q4-dynamic-static-one-weight-css", "static/Pretendard-Regular.css", "'Pretendard'");
  q4("q4-full-variable", "variable/pretendardvariable.css", "'Pretendard Variable'");
  q4("q4-dynamic-variable", "variable/pretendardvariable-dynamic-subset.css", "'Pretendard Variable'");
  return list;
}

function casePage(spec) {
  const script =
    spec.widget === null ? "" : `<script>(${widgetBundle.toString()})(${JSON.stringify(spec.widget)});</script>`;
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>${spec.name}</title>${spec.siteHead}</head><body>${spec.siteBody}${script}</body></html>`;
}

// ---------- 재기 ----------
function snapshot() {
  const host = document.querySelector("agent-os-widget");
  const root = host?.shadowRoot ?? null;
  const box = (element) =>
    element === null || element === undefined
      ? null
      : {
          width: Math.round(element.getBoundingClientRect().width * 100) / 100,
          fontFamily: getComputedStyle(element).fontFamily,
        };
  const ruleKinds = (sheet) => (sheet === null ? null : [...sheet.cssRules].map((rule) => rule.constructor.name));
  const widths = {};
  for (const element of document.querySelectorAll("span[id]")) {
    widths[element.id] = box(element);
  }
  if (root !== null) {
    for (const element of root.querySelectorAll("span[id]")) {
      widths[element.id] = box(element);
    }
  }
  return {
    widths,
    host: host === null ? null : { fontFamily: getComputedStyle(host).fontFamily },
    wrap: box(root?.querySelector("#w-wrap")),
    fonts: [...document.fonts].map((font) => ({ family: font.family, weight: font.weight, status: font.status })),
    fontsStatus: document.fonts.status,
    documentStyleSheets: document.styleSheets.length,
    shadowStyleRules: root === null ? null : ruleKinds(root.querySelector("style")?.sheet ?? null),
    adoptedRules: root === null ? null : root.adoptedStyleSheets.map((sheet) => ruleKinds(sheet)),
  };
}

async function platformFonts(page, ids) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("DOM.enable");
  await cdp.send("CSS.enable");
  await cdp.send("DOM.getDocument", { depth: -1, pierce: true });
  const found = {};
  for (const id of ids) {
    const expression = `document.getElementById(${JSON.stringify(id)}) ?? document.querySelector("agent-os-widget")?.shadowRoot?.getElementById(${JSON.stringify(id)}) ?? null`;
    const { result } = await cdp.send("Runtime.evaluate", { expression });
    if (result.objectId === undefined) {
      continue;
    }
    const { nodeId } = await cdp.send("DOM.requestNode", { objectId: result.objectId });
    const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId });
    found[id] = fonts.map((font) => `${font.familyName}${font.isCustomFont ? " (custom)" : ""} x${String(font.glyphCount)}`);
  }
  await cdp.detach();
  return found;
}

// 같은 글꼴·글자열·크기면 폭은 소수 둘째 자리까지 같다. 0.5px 로 두었더니 chromium 에서 사이트 기본 글꼴(Malgun Gothic)의
// 라틴 폭 273.28 이 font 참조 272.95 와 맞아 버렸다.
const WIDTH_TOLERANCE = 0.02;

function classify(widths, refs) {
  const labels = {};
  for (const [id, value] of Object.entries(widths)) {
    if (value === null || id.startsWith("ref-")) {
      continue;
    }
    const lang = id.endsWith("-ko") ? "ko" : "en";
    const matches = Object.entries(refs)
      .filter(([, ref]) => Math.abs(ref[lang] - value.width) < WIDTH_TOLERANCE)
      .map(([name]) => name);
    labels[id] = matches.length === 0 ? `other(${String(value.width)})` : matches.join("|");
  }
  return labels;
}

async function runCase(browser, browserName, spec) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const consoleLines = [];
  const failed = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      consoleLines.push(`${message.type()}: ${message.text().slice(0, 240)}`);
    }
  });
  page.on("pageerror", (error) => consoleLines.push(`pageerror: ${String(error).slice(0, 240)}`));
  page.on("requestfailed", (request) => {
    if (request.url().includes("/font/")) {
      failed.push({ url: new URL(request.url()).pathname, error: request.failure()?.errorText ?? null });
    }
  });
  const before = log.length;
  try {
    await page.goto(`http://${HOST}:${String(ports.site)}/case/${spec.name}`, { waitUntil: "load" });
    await page.waitForLoadState("networkidle");
    await page.evaluate(async () => {
      await document.fonts.ready;
      await new Promise((ok) => setTimeout(ok, 300));
    });
    await page.waitForLoadState("networkidle");
    await sleep(200);
    const snap = await page.evaluate(snapshot);
    // CDP 의 CSS.enable 이 걸린 시트를 다시 받으므로 서버 기록은 그 전에 끊는다.
    const network = log.slice(before);
    if (browserName === "chromium") {
      snap.platform = await platformFonts(page, Object.keys(snap.widths));
    }
    snap.network = network.map(({ server, path, origin, secFetchMode, bytes, status }) => ({
      server,
      path,
      origin,
      secFetchMode,
      bytes,
      status,
    }));
    snap.requestFailed = failed;
    snap.console = consoleLines;
    return snap;
  } finally {
    await context.close();
  }
}

function summarize(spec, snap, refs) {
  const fontRequests = snap.network.filter((entry) => /\.woff2?$/.test(entry.path));
  const summary = {
    labels: classify(snap.widths, refs),
    fontRequests: fontRequests.length,
    fontBytes: fontRequests.reduce((acc, entry) => acc + entry.bytes, 0),
    cssRequests: snap.network.filter((entry) => entry.path.endsWith(".css")).map((entry) => `${entry.path} ${String(entry.bytes)}`),
    // document.fonts 의 항목을 family:status 마다 센다(동적 서브셋은 항목이 수백 개다).
    fonts: snap.fonts.reduce((acc, font) => {
      const key = `${font.family}:${font.status}`;
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    }, {}),
  };
  if (snap.host !== null) {
    summary.hostFamily = snap.host.fontFamily;
  }
  if (snap.shadowStyleRules !== null || (snap.adoptedRules ?? []).length > 0) {
    summary.shadowRules = { style: snap.shadowStyleRules, adopted: snap.adoptedRules };
  }
  if (snap.platform !== undefined) {
    summary.platform = Object.fromEntries(
      Object.entries(snap.platform).map(([id, fonts]) => [id, fonts.join(" + ")]),
    );
  }
  if (snap.requestFailed.length > 0 || snap.console.length > 0) {
    summary.failed = { requests: snap.requestFailed.length, console: snap.console.length };
  }
  if (spec.group === "q4") {
    summary.slices = fontRequests
      .map((entry) => /\.subset\.(\d+)\.woff2$/.exec(entry.path)?.[1] ?? entry.path)
      .sort((a, b) => Number(a) - Number(b));
  }
  return summary;
}

// ---------- 실행 ----------
const site = http.createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://${HOST}`);
  if (url.pathname.startsWith("/font/")) {
    serveFont(res, req, url, "site");
    return;
  }
  const match = /^\/case\/([\w-]+)$/.exec(url.pathname);
  const spec = match === null ? undefined : cases().find((candidate) => candidate.name === match[1]);
  if (spec === undefined) {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { "Content-Type": TYPES[".html"], "Cache-Control": "no-store" }).end(casePage(spec));
});
const fontOrigin = http.createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://${HOST}`);
  if (url.pathname.startsWith("/font/")) {
    serveFont(res, req, url, "font");
    return;
  }
  res.writeHead(404).end();
});

if (!existsSync(join(web, "static", "woff2", "Pretendard-Regular.woff2"))) {
  console.error(`Pretendard 패키지 폴더가 아니다: ${pkg}`);
  process.exit(2);
}
ports.site = await listen(site, 8890);
ports.font = await listen(fontOrigin, ports.site + 1);

const result = {
  measuredAt: new Date().toISOString(),
  node: process.version,
  playwright: playwrightVersion,
  pretendard: JSON.parse(readFileSync(join(pkg, "package.json"), "utf-8")).version,
  regularBytes: statSync(join(web, "static", "woff2", "Pretendard-Regular.woff2")).size,
  ports,
  os: `${process.platform} ${release()}`,
  browsers: [],
};

try {
  for (const browserName of browserNames) {
    const entry = { browser: browserName };
    result.browsers.push(entry);
    let browser;
    try {
      browser = await playwright[browserName].launch();
    } catch (error) {
      entry.launchError = String(error).split("\n").slice(0, 3).join(" ");
      continue;
    }
    entry.version = browser.version();
    entry.executable = relative(process.env.LOCALAPPDATA ?? "", playwright[browserName].executablePath());
    try {
      const all = cases();
      const refSnap = await runCase(browser, browserName, all[0]);
      const refs = {};
      for (const name of ["font", "black", "mono", "serif"]) {
        refs[name] = { ko: refSnap.widths[`ref-${name}-ko`].width, en: refSnap.widths[`ref-${name}-en`].width };
      }
      entry.refs = refs;
      entry.refPlatform = refSnap.platform ?? null;
      entry.cases = [];
      for (const spec of all.slice(1)) {
        const snap = await runCase(browser, browserName, spec);
        entry.cases.push({ name: spec.name, group: spec.group, summary: summarize(spec, snap, refs), detail: snap });
      }
    } finally {
      await browser.close();
    }
  }
} finally {
  site.close();
  fontOrigin.close();
  site.closeAllConnections();
  fontOrigin.closeAllConnections();
}

const text = `${JSON.stringify(result, null, 2)}\n`;
if (out !== null) {
  writeFileSync(out, text);
}
// stdout 에는 사례마다 한 줄 요약만 낸다. 세부(detail)는 --out 파일에 있다.
for (const entry of result.browsers) {
  console.log(`== ${entry.browser} ${entry.version ?? ""} ${entry.launchError ?? ""}`);
  if (entry.refs !== undefined) {
    console.log(`refs ${JSON.stringify(entry.refs)}`);
  }
  for (const item of entry.cases ?? []) {
    console.log(`${item.name} ${JSON.stringify(item.summary)}`);
  }
}
