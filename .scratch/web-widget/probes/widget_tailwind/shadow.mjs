// web-widget 위젯 스타일 프로브: 실제 브라우저(Playwright chromium)에서 Tailwind CSS 를 shadow root 와 light DOM 에 넣고
// 계산 스타일을 견준다. 그리고 실제 위젯(element, iframe 정적 페이지, iframe Next 페이지)을 그려 스타일과 아이콘을 본다.
//   node .scratch/web-widget/probes/widget_tailwind/shadow.mjs <작업 루트>/react
// measure.mjs 가 빌드를 마친 트리를 받는다. Playwright 는 그 트리의 apps/admin 에 깔린 @playwright/test 로 부른다.
//
// 1. swatch. 흔한 유틸리티를 든 표본(아래 CASES)을 apps/widget/.swatch-probe/ 에 잠깐 쓰고 element 와 같은 길(Vite 라이브러리
//    빌드, @tailwindcss/vite, `?inline`, 압축)로 CSS 를 빌드한 뒤 지운다. 같은 표본을 변형마다 새 페이지에 그리고 표본 요소
//    (와 표시한 의사 요소)의 계산 스타일 전부(사용자 정의 속성 제외)를 light DOM 의 것과 견준다. 색 체계 light·dark 둘 다.
//      light                  문서의 <style> 에 CSS, 표본은 문서에(기준)
//      shadow-style           shadow root 안의 <style>
//      shadow-adopted         shadow root 의 adoptedStyleSheets
//      shadow-host-defaults   + `@layer properties { :host { <@property 의 초기값> } }`
//      shadow-star-defaults   + `@layer properties { *, ::before, ::after, ::backdrop { <같은 것> } }`
//      shadow-host-fallback   + `@layer properties { :host { <Tailwind 대체 블록의 선언> } }`
//      shadow-star-fallback   + `@layer properties { *, ::before, ::after, ::backdrop { <같은 것> } }`(위젯의 lib/shadow-styles.ts)
//      shadow-star-unlayered  + 대체 블록의 선언을 층 밖에
//      shadow-doc-property    문서의 adoptedStyleSheets 에 `@property` 규칙만 넣고 shadow root 에는 CSS 만
//    페이지는 body 여백을 0 으로 둔다(light 변형에서만 preflight 가 문서의 body 에 닿아 배치가 갈리지 않게).
//    `@property` 의 초기값은 브라우저가 파싱한 시트의 CSSPropertyRule 에서, 대체 블록은 CSSLayerBlockRule(properties) 안
//    CSSSupportsRule 의 규칙에서 읽는다. 대체 블록은 Tailwind 가 `@property` 를 모르는 브라우저(@supports 조건)에만 내는
//    `*, ::before, ::after, ::backdrop` 규칙이다. 변형마다 문서의 body 에서
//    `--tw-border-style` 을 읽어 등록이 사이트 문서로 새는지도 본다.
// 2. 위젯. 가짜 Agent OS(8790, SSE 와 dist/page), 사이트(8791), next start(3107)를 띄우고 모드마다 입력·보내기·프레임 붙이기를
//    한 뒤 위젯 요소들의 계산 스타일 전부를 element 의 것과 견준다. 아이콘(svg.lucide-send, svg.lucide-x)이 그려졌는지(크기,
//    path 수, stroke)도 본다.
//      element          사이트(사이트 CSS 없음)의 커스텀 요소(dist/element/widget.js)
//      element-hostile  사이트 CSS 가 있는 페이지(html 의 font-size, body 의 color·font-size·letter-spacing·line-height)
//      iframe-static    Agent OS 출처의 Vite 정적 페이지(iframe)
//      iframe-next      Agent OS 출처의 Next 페이지(iframe)
//    색 체계 dark 에서 element 와 iframe-next 를 한 번 더 그린다.
// 결과는 JSON 으로 내고 <작업 루트>/react/shadow.json 에도 쓴다. 포트 8790·8791·3107 이 비어 있어야 한다.

import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import http from "node:http";
import { createRequire } from "node:module";
import { dirname, extname, join, normalize, relative, resolve } from "node:path";
import { gzipSync } from "node:zlib";

const ws = resolve(process.argv[2] ?? ".");
const widget = join(ws, "web", "apps", "widget");
const fromWidget = createRequire(join(widget, "package.json"));
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
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css" };
const sleep = (ms) => new Promise((resolveSleep) => setTimeout(resolveSleep, ms));

// ---------- swatch 표본 ----------
// cls 는 표본 요소의 클래스. parent 는 감싸는 요소의 클래스(물려받기를 보는 사례), children 은 자식 셋을 두는 사례(space, divide),
// pseudo 는 함께 읽을 의사 요소, focus 는 읽기 전에 focus() 하는 입력창, wrap 은 감싸는 요소의 클래스(cdark 변형).
const CASES = [
  { k: "bg", cls: "bg-blue-600" },
  { k: "text", cls: "text-gray-900" },
  { k: "spacing", cls: "m-2 mt-6 p-3 px-4" },
  { k: "rounded", cls: "rounded-lg" },
  { k: "border", cls: "border" },
  { k: "border-2-color", cls: "border-2 border-gray-300" },
  { k: "border-dashed", cls: "border-4 border-dashed border-red-500" },
  { k: "border-b", cls: "border-b border-gray-200" },
  { k: "shadow", cls: "shadow" },
  { k: "shadow-md", cls: "shadow-md" },
  { k: "shadow-color", cls: "shadow-lg shadow-blue-500/50" },
  { k: "inset-shadow", cls: "inset-shadow-sm" },
  { k: "ring", cls: "ring" },
  { k: "ring-2-color", cls: "ring-2 ring-blue-500" },
  { k: "ring-offset", cls: "ring-2 ring-blue-500 ring-offset-2 ring-offset-white" },
  { k: "inset-ring", cls: "inset-ring-2 inset-ring-red-500" },
  { k: "shadow-ring", cls: "shadow-md ring-1 ring-black/5" },
  { k: "outline", cls: "outline-2 outline-offset-2 outline-blue-500" },
  { k: "outline-dashed", cls: "outline-2 outline-dashed" },
  { k: "translate-x", cls: "translate-x-2" },
  { k: "translate-y-neg", cls: "-translate-y-1" },
  { k: "translate-xy", cls: "translate-x-2 translate-y-3" },
  { k: "scale", cls: "scale-110" },
  { k: "scale-x", cls: "scale-x-75" },
  { k: "rotate", cls: "rotate-45" },
  { k: "skew", cls: "skew-x-6" },
  { k: "gradient", cls: "bg-linear-to-r from-blue-500 to-purple-500" },
  { k: "gradient-via", cls: "bg-linear-to-r from-blue-500 via-green-500 to-purple-500" },
  { k: "gradient-pos", cls: "bg-linear-to-r from-blue-500 from-10% to-purple-500 to-90%" },
  { k: "gradient-v3-name", cls: "bg-gradient-to-r from-pink-500 to-yellow-500" },
  { k: "gradient-radial", cls: "bg-radial from-white to-black" },
  { k: "opacity", cls: "opacity-50" },
  { k: "alpha-bg", cls: "bg-black/50" },
  { k: "font", cls: "text-sm leading-6 font-semibold tracking-wide" },
  { k: "text-shadow", cls: "text-shadow-md" },
  { k: "text-shadow-color", cls: "text-shadow-lg text-shadow-blue-500" },
  { k: "blur", cls: "blur-sm" },
  { k: "drop-shadow", cls: "drop-shadow-md" },
  { k: "backdrop-blur", cls: "backdrop-blur-sm" },
  { k: "grayscale", cls: "grayscale" },
  { k: "transition", cls: "transition duration-200 ease-in-out" },
  { k: "dark-media", cls: "bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100" },
  { k: "dark-class", cls: "bg-white cdark:bg-gray-900", wrap: "cdark" },
  { k: "space-y", cls: "space-y-2", children: true },
  { k: "divide-y", cls: "divide-y divide-gray-200", children: true },
  { k: "before-content", cls: "before:content-['*'] before:text-red-500", pseudo: "before" },
  { k: "after-no-content", cls: "relative after:absolute after:inset-0", pseudo: "after" },
  { k: "focus-ring", cls: "focus:ring-2 focus:ring-blue-500 focus:outline-none", focus: true },
  { k: "leak-shadow-ring", parent: "shadow-md", cls: "ring-2 ring-blue-500" },
  { k: "leak-translate", parent: "translate-x-4", cls: "translate-y-2" },
  { k: "leak-border-style", parent: "border-2 border-dashed", cls: "border" },
  {
    k: "leak-gradient",
    parent: "bg-linear-to-r from-red-500 to-blue-500",
    cls: "bg-linear-to-r to-green-500",
  },
];
const VARIANTS = [
  "light",
  "shadow-style",
  "shadow-adopted",
  "shadow-host-defaults",
  "shadow-star-defaults",
  "shadow-host-fallback",
  "shadow-star-fallback",
  "shadow-star-unlayered",
  "shadow-doc-property",
];

function caseHtml(c) {
  const attrs = `data-k="${c.k}" class="${c.cls}"${c.pseudo === undefined ? "" : ` data-pseudo="${c.pseudo}"`}`;
  let inner = c.focus
    ? `<input ${attrs} data-focus value="x">`
    : c.children
      ? `<div ${attrs}><div>가</div><div>나</div><div>다</div></div>`
      : `<div ${attrs}>표본</div>`;
  if (c.parent !== undefined) {
    inner = `<div data-k="${c.k}:parent" class="${c.parent}">${inner}</div>`;
  }
  if (c.wrap !== undefined) {
    inner = `<div class="${c.wrap}">${inner}</div>`;
  }
  return `<div style="padding: 8px">${inner}</div>`;
}
const SWATCH_HTML = CASES.map(caseHtml).join("\n");

function buildSwatch() {
  const dir = join(widget, ".swatch-probe");
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  try {
    writeFileSync(join(dir, "cases.html"), SWATCH_HTML);
    writeFileSync(
      join(dir, "swatch.css"),
      '@import "tailwindcss" source(none);\n@source "./cases.html";\n@custom-variant cdark (&:where(.cdark, .cdark *));\n',
    );
    writeFileSync(
      join(dir, "entry.js"),
      'import css from "./swatch.css?inline";\nexport default css;\n',
    );
    writeFileSync(
      join(dir, "vite.config.mjs"),
      `import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
export default defineConfig({
  root: import.meta.dirname,
  logLevel: "warn",
  plugins: [tailwindcss()],
  build: {
    outDir: "out",
    emptyOutDir: true,
    minify: true,
    lib: { entry: "entry.js", formats: ["iife"], name: "SwatchCss", fileName: () => "swatch.js" },
  },
});
`,
    );
    const vite = join(dirname(fromWidget.resolve("vite/package.json")), "bin", "vite.js");
    const proc = spawnSync(
      process.execPath,
      [vite, "build", "--config", join(dir, "vite.config.mjs")],
      {
        cwd: widget,
        encoding: "utf-8",
      },
    );
    if (proc.status !== 0) {
      throw new Error(`swatch 빌드 실패: ${proc.stdout}${proc.stderr}`);
    }
    return readFileSync(join(dir, "out", "swatch.js"), "utf-8");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

// 브라우저 안에서 돈다. 변형 하나를 그리고 표본의 계산 스타일을 읽는다.
function renderSwatch(variant) {
  const css = window.SwatchCss;
  const html = window.SWATCH_HTML;
  const sheet = new CSSStyleSheet();
  sheet.replaceSync(css);
  const propertyRules = [...sheet.cssRules].filter((rule) => rule instanceof CSSPropertyRule);
  const declarations = propertyRules
    .map((rule) => `${rule.name}: ${rule.initialValue ?? "initial"};`)
    .join(" ");
  // Tailwind 가 `@property` 를 모르는 브라우저에 내는 대체 블록(@layer properties > @supports > 규칙)의 선언.
  const fallback = [...sheet.cssRules]
    .filter((rule) => rule instanceof CSSLayerBlockRule && rule.name === "properties")
    .flatMap((layer) => [...layer.cssRules])
    .filter((rule) => rule instanceof CSSSupportsRule)
    .flatMap((supports) => [...supports.cssRules])
    .map((rule) => rule.style.cssText)
    .join(" ");
  const sheetOf = (text) => {
    const made = new CSSStyleSheet();
    made.replaceSync(text);
    return made;
  };
  const box = document.createElement("div");
  box.innerHTML = html;
  let scope = box;
  if (variant === "light") {
    const style = document.createElement("style");
    style.textContent = css;
    document.head.append(style);
    document.body.append(box);
  } else {
    const host = document.createElement("swatch-host");
    host.style.display = "block";
    document.body.append(host);
    const root = host.attachShadow({ mode: "open" });
    const STAR = "*, ::before, ::after, ::backdrop";
    if (variant === "shadow-style") {
      const style = document.createElement("style");
      style.textContent = css;
      root.append(style);
    } else {
      const extra = {
        "shadow-adopted": [],
        "shadow-host-defaults": [sheetOf(`@layer properties { :host { ${declarations} } }`)],
        "shadow-star-defaults": [sheetOf(`@layer properties { ${STAR} { ${declarations} } }`)],
        "shadow-host-fallback": [sheetOf(`@layer properties { :host { ${fallback} } }`)],
        "shadow-star-fallback": [sheetOf(`@layer properties { ${STAR} { ${fallback} } }`)],
        "shadow-star-unlayered": [sheetOf(`${STAR} { ${fallback} }`)],
        "shadow-doc-property": [],
      }[variant];
      root.adoptedStyleSheets = [sheet, ...extra];
    }
    if (variant === "shadow-doc-property") {
      const only = sheetOf(propertyRules.map((rule) => rule.cssText).join("\n"));
      document.adoptedStyleSheets = [...document.adoptedStyleSheets, only];
    }
    root.append(box);
    scope = root;
  }
  const read = (element, pseudo) => {
    const style = getComputedStyle(element, pseudo);
    const out = {};
    for (const name of style) {
      if (!name.startsWith("--")) {
        out[name] = style.getPropertyValue(name);
      }
    }
    return out;
  };
  const styles = {};
  for (const element of scope.querySelectorAll("[data-k]")) {
    const key = element.dataset.k;
    if (element.hasAttribute("data-focus")) {
      element.focus();
    }
    styles[key] = read(element, null);
    if (element.dataset.pseudo !== undefined) {
      styles[`${key}::${element.dataset.pseudo}`] = read(element, `::${element.dataset.pseudo}`);
    }
    if (element.hasAttribute("data-focus")) {
      element.blur();
    }
  }
  const border = scope.querySelector('[data-k="border"]');
  return {
    styles,
    propertyRules: propertyRules.length,
    fallbackDeclarations: fallback.split(";").filter((part) => part.trim() !== "").length,
    sheetRules: sheet.cssRules.length,
    borderStyleVar: getComputedStyle(border).getPropertyValue("--tw-border-style"),
    siteBodyBorderStyleVar: getComputedStyle(document.body).getPropertyValue("--tw-border-style"),
  };
}

function diffStyles(reference, other) {
  const byKey = {};
  for (const [key, props] of Object.entries(reference)) {
    const theirs = other[key] ?? {};
    const differs = Object.keys(props)
      .filter((name) => props[name] !== theirs[name])
      .map((name) => ({
        prop: name,
        light: String(props[name]).slice(0, 90),
        other: String(theirs[name]).slice(0, 90),
      }));
    if (differs.length > 0) {
      byKey[key] = differs;
    }
  }
  return byKey;
}

// ---------- 가짜 Agent OS 와 사이트 ----------
const requests = [];
let release = () => undefined;

function cors(req) {
  const origin = req.headers.origin;
  return origin === undefined
    ? {}
    : {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "authorization, content-type",
        "Access-Control-Allow-Methods": "POST",
        Vary: "Origin",
      };
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
  const url = new URL(req.url ?? "/", `http://${HOST}:${String(AGENT)}`);
  const runPath = /^\/(?:api\/)?runs$/.test(url.pathname);
  if (runPath && req.method === "OPTIONS") {
    res.writeHead(204, cors(req)).end();
    return;
  }
  if (runPath && req.method === "POST") {
    req.resume();
    req.on("end", async () => {
      requests.push({ path: url.pathname, origin: req.headers.origin ?? null });
      res.writeHead(200, {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        ...cors(req),
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

const HOSTILE_CSS = `
html { font-size: 10px; }
body { color: rgb(0, 128, 0); font-size: 30px; letter-spacing: 5px; line-height: 3; }
`;
let swatchJs = "";

const site = http.createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://${HOST}:${String(SITE)}`);
  const page = (head, body) => {
    res
      .writeHead(200, { "Content-Type": TYPES[".html"] })
      .end(
        `<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>사이트</title>${head}</head><body>${body}</body></html>`,
      );
  };
  const element = `<agent-os-widget api-base="http://${HOST}:${String(AGENT)}" agent="echo" token="${TOKEN}"></agent-os-widget><script src="/widget.js"></script>`;
  const iframe = (port) =>
    `<iframe title="위젯" width="400" height="460" src="http://${HOST}:${String(port)}/?agent=echo&token=${TOKEN}"></iframe>`;
  switch (url.pathname) {
    case "/swatch.html":
      // light 변형만 preflight 가 문서의 body 여백을 지운다. 변형끼리 배치가 같게 body 여백을 미리 지운다.
      page(
        "<style>body { margin: 0; }</style>",
        `<script src="/swatch.js"></script><script>window.SWATCH_HTML = ${JSON.stringify(SWATCH_HTML).replaceAll("</", "<\\/")};</script>`,
      );
      return;
    case "/swatch.js":
      res.writeHead(200, { "Content-Type": TYPES[".js"] }).end(swatchJs);
      return;
    case "/element.html":
      page("", element);
      return;
    case "/element-hostile.html":
      page(`<style>${HOSTILE_CSS}</style>`, element);
      return;
    case "/iframe-static.html":
      page("", iframe(AGENT));
      return;
    case "/iframe-next.html":
      page("", iframe(NEXT));
      return;
    case "/widget.js":
      serveFile(res, join(widget, "dist", "element"), "/widget.js");
      return;
    default:
      res.writeHead(404).end();
  }
});

// ---------- 위젯 ----------
const PARTS = {
  section: "section",
  close: 'button[aria-label="닫기"]',
  list: "ul",
  userLine: 'li[data-role="user"]',
  agentLine: 'li[data-role="agent"]',
  eventLine: 'li[data-role="event"]',
  input: "input",
  send: 'button[type="submit"]',
  sendIcon: "svg.lucide-send",
  closeIcon: "svg.lucide-x",
};

// 브라우저 안에서 돈다. 위젯 요소들의 계산 스타일, 아이콘, 시트를 읽는다.
function readWidget(parts) {
  const host = document.querySelector("agent-os-widget");
  const root = host === null ? document : host.shadowRoot;
  if (root === null) {
    return null;
  }
  const styles = {};
  for (const [name, selector] of Object.entries(parts)) {
    const element = root.querySelector(selector);
    if (element === null) {
      continue;
    }
    const style = getComputedStyle(element);
    const out = {};
    for (const prop of style) {
      if (!prop.startsWith("--")) {
        out[prop] = style.getPropertyValue(prop);
      }
    }
    styles[name] = out;
  }
  const icons = {};
  for (const name of ["sendIcon", "closeIcon"]) {
    const svg = root.querySelector(parts[name]);
    if (svg === null) {
      icons[name] = null;
      continue;
    }
    const box = svg.getBoundingClientRect();
    const first = svg.querySelector("path");
    icons[name] = {
      width: box.width,
      height: box.height,
      paths: svg.querySelectorAll("path").length,
      class: svg.getAttribute("class"),
      ariaHidden: svg.getAttribute("aria-hidden"),
      stroke: getComputedStyle(svg).stroke,
      firstPath: first === null ? null : (first.getAttribute("d") ?? "").slice(0, 24),
    };
  }
  const sheets =
    host === null
      ? null
      : root.adoptedStyleSheets.map((sheet) => ({
          rules: sheet.cssRules.length,
          head: sheet.cssRules[0]?.cssText.slice(0, 120) ?? null,
        }));
  return { styles, icons, sheets };
}

// 브라우저 안에서 돈다. 값 안의 색 함수(oklch, lab, rgb 등)를 sRGB 0~255 정수로 바꾼다. Next 의 CSS 처리는 oklch 를
// lab 으로 다시 쓰므로 표기만 다른 것을 가르려는 것이다.
function normalizeColors(values) {
  const probe = document.createElement("div");
  document.body.append(probe);
  const toSrgb = (color) => {
    probe.style.color = "";
    probe.style.color = `color-mix(in srgb, ${color} 100%, transparent)`;
    const out = getComputedStyle(probe).color;
    const match = /^color\(srgb (\S+) (\S+) ([^\s)]+)(?: \/ ([^\s)]+))?\)$/.exec(out);
    if (match === null) {
      return out;
    }
    const channels = [match[1], match[2], match[3]].map((value) => Math.round(Number(value) * 255));
    const alpha = match[4] === undefined ? 1 : Number(match[4]);
    return `srgb(${channels.join(",")},${alpha.toFixed(2)})`;
  };
  return values.map((value) =>
    value.replace(/\b(?:oklch|oklab|lab|lch|rgba?|hsla?|color)\([^()]*\)/g, toSrgb),
  );
}

/** 두 정규화 값이 색 채널 ±1, 알파 ±0.01 안에서 같은가. 색 밖의 글자는 그대로 같아야 한다. */
function sameish(a, b) {
  const pattern = /srgb\((\d+),(\d+),(\d+),([\d.]+)\)/g;
  const tuples = (value) => [...value.matchAll(pattern)].map((match) => match.slice(1).map(Number));
  if (a.replace(pattern, "C") !== b.replace(pattern, "C")) {
    return false;
  }
  const [left, right] = [tuples(a), tuples(b)];
  return left.every((tuple, i) =>
    tuple.every((value, j) => Math.abs(value - right[i][j]) <= (j === 3 ? 0.01 : 1)),
  );
}

async function diffParts(normalizer, reference, other) {
  const pairs = [];
  const missing = [];
  for (const [name, props] of Object.entries(reference ?? {})) {
    const theirs = other?.[name];
    if (theirs === undefined) {
      missing.push(name);
      continue;
    }
    for (const prop of Object.keys(props)) {
      if (props[prop] !== theirs[prop]) {
        pairs.push({ name, prop, a: props[prop], b: String(theirs[prop]) });
      }
    }
  }
  const normalized = await normalizer.evaluate(
    normalizeColors,
    pairs.flatMap((pair) => [pair.a, pair.b]),
  );
  const real = {};
  let notationOnly = 0;
  pairs.forEach((pair, i) => {
    if (sameish(normalized[2 * i], normalized[2 * i + 1])) {
      notationOnly += 1;
      return;
    }
    (real[pair.name] ??= []).push(`${pair.prop}: ${pair.a.slice(0, 70)} → ${pair.b.slice(0, 70)}`);
  });
  return { missing, notationOnly, real };
}

async function chat(page, scope) {
  const list = scope.getByRole("list", { name: "메시지" });
  const out = {};
  try {
    await scope.getByRole("textbox", { name: "메시지 입력" }).click({ timeout: 5_000 });
    await page.keyboard.type("안녕");
    await scope.getByRole("button", { name: "보내기" }).click();
    await list.getByText("run_started").waitFor({ timeout: 5_000 });
    release();
    await list.getByText("안녕하세요").waitFor({ timeout: 5_000 });
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
  return out;
}

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
        files.push({
          url: `${url.port}${url.pathname}`,
          type,
          min: body.length,
          gzip: gzipSync(body, { level: 9 }).length,
        });
      }
    }
    return files;
  };
}

function startNext() {
  const bin = join(dirname(fromWidget.resolve("next/package.json")), "dist", "bin", "next");
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

// ---------- 돌리기 ----------
const result = { candidate: relative(dirname(ws), ws), swatch: {}, widget: {} };
swatchJs = buildSwatch();
result.swatch.cssBytes = Buffer.byteLength(swatchJs);
await new Promise((ok) => agent.listen(AGENT, HOST, ok));
await new Promise((ok) => site.listen(SITE, HOST, ok));
const next = startNext();
const browser = await chromium.launch();
result.browser = `chromium ${browser.version()}`;
const errors = [];
try {
  // 1. swatch
  for (const scheme of ["light", "dark"]) {
    const context = await browser.newContext({ colorScheme: scheme });
    const rendered = {};
    for (const variant of VARIANTS) {
      const page = await context.newPage();
      page.on("pageerror", (error) => errors.push(`swatch ${variant}: ${String(error)}`));
      await page.goto(`http://${HOST}:${String(SITE)}/swatch.html`);
      rendered[variant] = await page.evaluate(renderSwatch, variant);
      await page.close();
    }
    const reference = rendered.light.styles;
    result.swatch[scheme] = Object.fromEntries(
      VARIANTS.filter((variant) => variant !== "light").map((variant) => {
        const byKey = diffStyles(reference, rendered[variant].styles);
        return [
          variant,
          {
            propertyRules: rendered[variant].propertyRules,
            borderStyleVar: rendered[variant].borderStyleVar,
            siteBodyBorderStyleVar: rendered[variant].siteBodyBorderStyleVar,
            mismatchedCases: Object.keys(byKey),
            matchedCases: Object.keys(reference).filter((key) => !(key in byKey)).length,
            details: byKey,
          },
        ];
      }),
    );
    result.swatch[scheme].light = {
      cases: Object.keys(reference).length,
      sheetRules: rendered.light.sheetRules,
      propertyRules: rendered.light.propertyRules,
      borderStyleVar: rendered.light.borderStyleVar,
      siteBodyBorderStyleVar: rendered.light.siteBodyBorderStyleVar,
    };
    result.swatch[`${scheme}Reference`] = {
      darkMedia: {
        "background-color": reference["dark-media"]["background-color"],
        color: reference["dark-media"].color,
      },
      darkClass: { "background-color": reference["dark-class"]["background-color"] },
    };
    await context.close();
  }

  // 2. 위젯
  const nextUp = await waitHttp(`http://${HOST}:${String(NEXT)}/`);
  result.widget.nextUp = nextUp;
  const read = {};
  for (const scheme of ["light", "dark"]) {
    const context = await browser.newContext({ colorScheme: scheme });
    const modes =
      scheme === "light"
        ? ["element", "element-hostile", "iframe-static", "iframe-next"]
        : ["element", "iframe-next"];
    for (const mode of modes) {
      if (mode === "iframe-next" && !nextUp) {
        result.widget[`${scheme}:${mode}`] = { ok: false, error: "next start 가 서지 않았다" };
        continue;
      }
      const page = await context.newPage();
      page.on("pageerror", (error) => errors.push(`${mode}: ${String(error)}`));
      page.on("console", (message) => {
        if (message.type() === "error") {
          errors.push(`${mode}: ${message.text()}`);
        }
      });
      const loaded = collect(page);
      await page.goto(`http://${HOST}:${String(SITE)}/${mode}.html`);
      const scope = mode.startsWith("iframe") ? page.frameLocator("iframe") : page;
      const outcome = scheme === "light" ? await chat(page, scope) : {};
      if (scheme === "dark") {
        await scope.getByRole("textbox", { name: "메시지 입력" }).waitFor({ timeout: 5_000 });
      }
      // 보내기 단추는 transition 이 있어 busy 가 풀린 직후 opacity 가 0.5 에서 1 로 움직이는 중이다. 멎은 뒤 읽는다.
      await sleep(600);
      const frame = mode.startsWith("iframe")
        ? page.frames().find((candidate) => candidate !== page.mainFrame())
        : page.mainFrame();
      const seen = frame === undefined ? null : await frame.evaluate(readWidget, PARTS);
      read[`${scheme}:${mode}`] = seen;
      outcome.icons = seen?.icons ?? null;
      outcome.sheets = seen?.sheets ?? null;
      outcome.parts = seen === null ? [] : Object.keys(seen.styles);
      outcome.loaded = await loaded();
      result.widget[`${scheme}:${mode}`] = outcome;
      await page.close();
    }
    await context.close();
  }
  const element = read["light:element"]?.styles;
  const normalizer = await browser.newPage();
  // notationOnly 는 색 표기만 달라 sRGB 로 바꾸면 같은 값의 수다. real 은 그래도 다른 것이다.
  result.widget.diff = {
    "element→iframe-static": await diffParts(
      normalizer,
      element,
      read["light:iframe-static"]?.styles,
    ),
    "element→iframe-next": await diffParts(normalizer, element, read["light:iframe-next"]?.styles),
    "element→element-hostile": await diffParts(
      normalizer,
      element,
      read["light:element-hostile"]?.styles,
    ),
    "dark:element→dark:iframe-next": await diffParts(
      normalizer,
      read["dark:element"]?.styles,
      read["dark:iframe-next"]?.styles,
    ),
    "light:element→dark:element(section)": await diffParts(
      normalizer,
      { section: element?.section },
      { section: read["dark:element"]?.styles.section },
    ),
  };
  result.consoleErrors = errors;
} finally {
  await browser.close();
  result.nextLog = next.log.slice(-6);
  next.kill();
  agent.close();
  site.close();
  agent.closeAllConnections();
  site.closeAllConnections();
}

writeFileSync(join(ws, "shadow.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
