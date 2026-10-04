// web-widget 위젯 스택 프로브: 실제 브라우저(Playwright chromium)에서 위젯을 돌린다.
//   node .scratch/web-widget/probes/widget_stack/shadow.mjs <작업 루트>/<후보>
// measure.mjs 가 빌드를 마친 트리를 받는다. Playwright 는 그 트리의 apps/admin 에 깔린 @playwright/test 로 부른다.
//
// 띄우는 것(127.0.0.1, 셋 다 비어 있어야 한다)
//   8790  가짜 Agent OS. POST /runs·/api/runs 에 SSE 로 run_started 를 내고, 프로브가 풀 때까지 기다렸다 run_finished 를
//         내고 닫는다. CORS 는 Origin 을 그대로 허용한다. /nocors/runs 는 CORS 머리글 없이 답한다. GET / 와 /assets/ 는
//         dist/page(Vite 정적 iframe 페이지)다.
//   8791  사이트. 위젯 CSS 와 겹치는 선택자를 일부러 심은 페이지에 커스텀 요소(dist/element/widget.js)나 iframe 을 둔다.
//   3107  next start(next.config.ts 가 있는 후보만). rewrites 가 /api/* 를 8790 으로 넘긴다(빌드 때 박힌다).
//
// 모드마다 보는 것
//   element        사이트 출처 페이지의 shadow DOM 위젯이 다른 출처로 preflight 와 POST 를 내고, 프레임을 받는 대로 붙이는가.
//                  키보드로 친 글자와 클릭이 위젯에 닿는가. 사이트 CSS 가 들어오는가, 위젯 CSS 가 나가는가.
//   element-nocors 채널이 CORS 를 답하지 않으면 위젯에 무엇이 보이는가
//   iframe-static  Agent OS 출처의 정적 페이지(iframe)가 같은 출처로 부르는가
//   iframe-next    Agent OS 출처의 Next 페이지(iframe)가 같은 출처의 /api 중계로 부르고 프레임을 받는 대로 붙이는가
// 결과는 JSON 으로 내고 <작업 루트>/<후보>/shadow.json 에도 쓴다.

import { spawn } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import http from "node:http";
import { createRequire } from "node:module";
import { dirname, extname, join, normalize, relative, resolve } from "node:path";
import { gzipSync } from "node:zlib";

const ws = resolve(process.argv[2] ?? ".");
const widget = join(ws, "web", "apps", "widget");
const { chromium } = createRequire(join(ws, "web", "apps", "admin", "package.json"))(
  "@playwright/test",
);

const AGENT = 8790;
const SITE = 8791;
const NEXT = 3107;
const HOST = "127.0.0.1";
const TOKEN = "probe-token-not-a-secret";
const TS = "2026-10-03T10:00:00+00:00";
const STARTED = {
  type: "run_started",
  run_id: "r1",
  ts: TS,
  agent: "echo",
  request: "",
  principal: "widget",
};
const FINISHED = { type: "run_finished", run_id: "r1", ts: TS, output: "안녕하세요" };
const REACTIVE = ["apiBase", "agent", "token", "lines", "draft", "busy"];
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css" };

const sleep = (ms) => new Promise((resolveSleep) => setTimeout(resolveSleep, ms));

// ---------- 가짜 Agent OS ----------
const requests = [];
let release = () => undefined;

function cors(req, allow) {
  const origin = req.headers.origin;
  return allow && origin !== undefined
    ? {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "authorization, content-type",
        "Access-Control-Allow-Methods": "POST",
        Vary: "Origin",
      }
    : {};
}

function serveFile(res, root, path) {
  const file = normalize(join(root, path === "/" ? "index.html" : path));
  if (relative(root, file).startsWith("..") || !existsSync(file)) {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { "Content-Type": TYPES[extname(file)] ?? "application/octet-stream" });
  res.end(readFileSync(file));
}

const agent = http.createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://${HOST}:${AGENT}`);
  const runPath = /^\/(?:api\/|nocors\/)?runs$/.test(url.pathname);
  const allow = !url.pathname.startsWith("/nocors/");
  if (runPath && req.method === "OPTIONS") {
    requests.push({ method: "OPTIONS", path: url.pathname, origin: req.headers.origin ?? null });
    res.writeHead(204, cors(req, allow)).end();
    return;
  }
  if (runPath && req.method === "POST") {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
    });
    req.on("end", async () => {
      requests.push({
        method: "POST",
        path: url.pathname,
        origin: req.headers.origin ?? null,
        authorization: req.headers.authorization ?? null,
        body,
      });
      res.writeHead(200, {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        ...cors(req, allow),
      });
      res.write(`data: ${JSON.stringify(STARTED)}\n\n`);
      const held = new Promise((resolveHeld) => {
        release = resolveHeld;
      });
      await Promise.race([held, sleep(10_000)]);
      res.end(`data: ${JSON.stringify(FINISHED)}\n\n`);
    });
    return;
  }
  serveFile(res, join(widget, "dist", "page"), url.pathname);
});

// ---------- 사이트 ----------
// 위젯 CSS 의 선택자(button, li, form, .messages)와 겹치는 규칙을 일부러 둔다. 상속 속성(body 의 color, font-size)과
// 호스트 요소를 겨냥한 규칙(letter-spacing)도 둔다.
const SITE_CSS = `
body { color: rgb(0, 128, 0); font-size: 30px; font-family: serif; }
button { outline: 7px solid rgb(255, 0, 0) !important; }
li { display: none !important; }
.messages { border: 9px solid rgb(255, 0, 0); }
agent-os-widget { letter-spacing: 5px; }
`;
const SITE_BODY = `
<form id="site-form"><button id="site-button" type="button">사이트 버튼</button></form>
<ul class="site-list"><li id="site-li">사이트 항목</li></ul>
`;

function sitePage(inner) {
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>사이트</title><style>${SITE_CSS}</style></head><body>${SITE_BODY}${inner}</body></html>`;
}

const site = http.createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://${HOST}:${SITE}`);
  const html = (inner) => {
    res.writeHead(200, { "Content-Type": TYPES[".html"] }).end(sitePage(inner));
  };
  const element = (base) =>
    `<agent-os-widget api-base="${base}" agent="echo" token="${TOKEN}"></agent-os-widget><script src="/widget.js"></script>`;
  const iframe = (port) =>
    `<iframe title="위젯" width="400" height="420" src="http://${HOST}:${String(port)}/?agent=echo&token=${TOKEN}"></iframe>`;
  switch (url.pathname) {
    case "/element.html":
      html(element(`http://${HOST}:${String(AGENT)}`));
      return;
    case "/element-nocors.html":
      html(element(`http://${HOST}:${String(AGENT)}/nocors`));
      return;
    case "/iframe-static.html":
      html(iframe(AGENT));
      return;
    case "/iframe-next.html":
      html(iframe(NEXT));
      return;
    case "/widget.js":
      serveFile(res, join(widget, "dist", "element"), "/widget.js");
      return;
    default:
      res.writeHead(404).end();
  }
});

// ---------- 시나리오 ----------
async function chat(page, scope, mode) {
  const before = requests.length;
  const list = scope.getByRole("list", { name: "메시지" });
  const out = { mode };
  try {
    // 위젯이 그려지지 않으면(번들이 브라우저에서 깨지면) 여기서 멈춘다. 그것도 결과로 남긴다.
    await scope.getByRole("textbox", { name: "메시지 입력" }).click({ timeout: 5_000 });
    await page.keyboard.type("안녕");
    const sentAt = Date.now();
    await scope.getByRole("button", { name: "보내기" }).click();
    await list.getByText("run_started").waitFor({ timeout: 5_000 });
    out.firstFrameMs = Date.now() - sentAt;
    out.finishedBeforeRelease = (await list.getByText("안녕하세요").count()) > 0;
    release();
    await list.getByText("안녕하세요").waitFor({ timeout: 5_000 });
    out.userLine = (await list.getByText("안녕", { exact: true }).count()) === 1;
    out.ok = true;
  } catch (error) {
    out.ok = false;
    out.error = String(error).split("\n")[0];
    release();
  }
  out.items = await list
    .locator("li")
    .allInnerTexts()
    .catch(() => []);
  out.requests = requests.slice(before);
  return out;
}

async function styles(page) {
  return page.evaluate(() => {
    const host = document.querySelector("agent-os-widget");
    const root = host?.shadowRoot;
    const pick = (element, names) => {
      if (!element) {
        return null;
      }
      const style = getComputedStyle(element);
      return Object.fromEntries(names.map((name) => [name, style.getPropertyValue(name)]));
    };
    return {
      shadowMode: root ? "open" : "none",
      inbound: {
        widgetButton: pick(root?.querySelector("button"), ["outline-width", "background-color"]),
        widgetLi: pick(root?.querySelector("li"), ["display"]),
        widgetList: pick(root?.querySelector(".messages"), ["border-top-width"]),
        widgetSection: pick(root?.querySelector("section"), [
          "color",
          "font-size",
          "font-family",
          "letter-spacing",
        ]),
      },
      outbound: {
        siteButton: pick(document.querySelector("#site-button"), ["background-color"]),
        siteForm: pick(document.querySelector("#site-form"), ["display"]),
        siteLi: pick(document.querySelector("#site-li"), ["padding-top"]),
      },
      documentQueries: {
        sections: document.querySelectorAll("section").length,
        inputs: document.querySelectorAll("input").length,
      },
    };
  });
}

// 모드 하나에서 브라우저가 실제로 받은 위젯의 바이트. 문서, script, stylesheet 응답의 본문(압축 전)과 그 gzip(9단계)이다.
// 사이트의 페이지 자체는 뺀다. 동적 import 로 나중에 받은 조각도 든다(measure.mjs 의 Next 합은 미리 그린 HTML 이 싣는 것만).
function collect(page) {
  const seen = [];
  const listener = (response) => {
    seen.push(response);
  };
  page.on("response", listener);
  return async () => {
    page.off("response", listener);
    const files = [];
    for (const response of seen) {
      const type = response.request().resourceType();
      const url = new URL(response.url());
      if (!["document", "script", "stylesheet"].includes(type)) {
        continue;
      }
      if (url.port === String(SITE) && url.pathname.endsWith(".html")) {
        continue;
      }
      const body = await response.body().catch(() => null);
      if (body !== null) {
        const size = { min: body.length, gzip: gzipSync(body, { level: 9 }).length };
        files.push({ url: `${url.port}${url.pathname}`, type, ...size });
      }
    }
    const total = files.reduce(
      (acc, file) => ({ min: acc.min + file.min, gzip: acc.gzip + file.gzip }),
      { min: 0, gzip: 0 },
    );
    return { total, files };
  };
}

function startNext() {
  const bin = join(
    dirname(createRequire(join(widget, "package.json")).resolve("next/package.json")),
    "dist",
    "bin",
    "next",
  );
  const child = spawn(process.execPath, [bin, "start", "-H", HOST, "-p", String(NEXT)], {
    cwd: widget,
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  child.log = [];
  const push = (data) => child.log.push(...data.toString("utf-8").split(/\r?\n/).filter(Boolean));
  child.stdout.on("data", push);
  child.stderr.on("data", push);
  return child;
}

async function waitHttp(url) {
  for (let i = 0; i < 100; i += 1) {
    try {
      const response = await fetch(url);
      if (response.status < 500) {
        return true;
      }
    } catch {
      // 아직 서지 않았다
    }
    await sleep(200);
  }
  return false;
}

const result = { candidate: relative(dirname(ws), ws), modes: [] };
await new Promise((ok) => agent.listen(AGENT, HOST, ok));
await new Promise((ok) => site.listen(SITE, HOST, ok));
const hasNext = existsSync(join(widget, ".next", "BUILD_ID"));
const next = hasNext ? startNext() : null;
const browser = await chromium.launch();
result.browser = `chromium ${browser.version()}`;
try {
  const context = await browser.newContext();
  const errors = [];
  context.on("weberror", (error) => errors.push(String(error.error()).split("\n")[0]));
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });

  const modes = ["element", "element-nocors", "iframe-static"];
  if (next !== null) {
    modes.push((await waitHttp(`http://${HOST}:${String(NEXT)}/`)) ? "iframe-next" : "next-down");
  }
  for (const mode of modes) {
    if (mode === "next-down") {
      result.modes.push({ mode: "iframe-next", ok: false, error: "next start 가 서지 않았다" });
      continue;
    }
    const loaded = collect(page);
    await page.goto(`http://${HOST}:${String(SITE)}/${mode}.html`);
    const scope = mode.startsWith("iframe") ? page.frameLocator("iframe") : page;
    const outcome = await chat(page, scope, mode);
    outcome.loaded = await loaded();
    // Lit 의 반응 속성이 인스턴스의 자기 속성이면 클래스 필드가 접근자를 가린 것이다(갱신이 그려지지 않는다).
    // 컴파일러가 useDefineForClassFields·데코레이터를 어떻게 다뤘는지 보는 자리다. 요소가 없으면 null 이다.
    const frame = mode.startsWith("iframe")
      ? page.frames().find((candidate) => candidate !== page.mainFrame())
      : page.mainFrame();
    outcome.ownReactiveProps =
      frame === undefined
        ? null
        : await frame.evaluate((names) => {
            const host = document.querySelector("agent-os-widget");
            return host === null ? null : names.filter((name) => Object.hasOwn(host, name));
          }, REACTIVE);
    if (mode === "element") {
      outcome.styles = await styles(page);
    }
    result.modes.push(outcome);
  }
  result.consoleErrors = errors;
} finally {
  await browser.close();
  if (next !== null) {
    result.nextLog = next.log.slice(-8);
    next.kill();
  }
  agent.close();
  site.close();
  agent.closeAllConnections();
  site.closeAllConnections();
}

writeFileSync(join(ws, "shadow.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
const expected = result.modes.filter((mode) => mode.mode !== "element-nocors");
process.exitCode = expected.every((mode) => mode.ok) ? 0 : 1;
