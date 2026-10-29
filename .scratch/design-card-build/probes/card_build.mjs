// 저장소가 이미 가진 도구(디자인 시스템 패키지의 vite 8과 Tailwind CLI)만으로 Design System 형식의 컴포넌트 묶음과
// 컴포넌트 카드의 장면을 지을 수 있는지, 지은 카드가 페이지와 같은 차례로 실린 문서에서 그려지는지, 페이지의 토큰
// CSS(층 없음)가 묶음 CSS의 층(`@layer theme`) 안 디자인 토큰을 이기는지 잰다(design-card-build 명세).
//
// 돌리는 법(저장소 뿌리에서, `pnpm -C web install` 뒤):
//   node .scratch/design-card-build/probes/card_build.mjs <작업 폴더의 절대 경로>
// 작업 폴더는 아직 없는 경로여야 한다. 이 프로브는 어떤 폴더도 지우지 않고, 있는 경로를 받으면 아무것도 하지 않고
// 2로 끝난다. 산출(묶음, CSS, 카드 문서, 요약 JSON)은 그 폴더에만 쓴다.
//
// 회차와 표지(표지가 없는 회차는 측정이 아니라고 따로 세고 종료 코드를 1로 둔다):
// - `bundle`: `src/index.ts`를 IIFE 하나(전역 `AgentOsUi`)로 짓는다. React·ReactDOM은 밖에 두고 전역 `React`·
//   `ReactDOM`으로 받으며, `react/jsx-runtime`은 전역 React의 `createElement`를 부르는 대체 모듈로 바꾼다. 페이지와
//   화면 형식은 React 18.3.1 UMD를 싣는데 React 19의 jsx-runtime이 만드는 요소(`react.transitional.element`)는
//   18이 그리지 못하기 때문이다. 표지: 산출에 `AgentOsUi`의 대입이 있고, `require(`·`import `·`react.transitional.element`
//   가 0번이다.
// - `css`: Tailwind CLI로 디자인 토큰 CSS(`src/styles/theme.css`)를 짓는다. 표지: `@layer theme`과 `--accent-600:`이 있다.
// - `fonts`: 글꼴 CSS(`src/styles/fonts.css`)를 vite로 지어 글꼴 파일 이름을 낸다. 표지: 글꼴 파일이 700개를 넘는다.
//   지난 산출 목록(`.design-sync/upload-output.json`, 커밋 `35028cba`에서 꺼낸다)의 `fonts/` 이름과 같은 것을 센다.
// - `scene:<컴포넌트>`: 컴포넌트 스토리 파일 하나를 IIFE로 짓는다. 스토리가 상대 경로로 부르는 컴포넌트 모듈은
//   묶음의 전역 `AgentOsUi`로, `storybook/test`는 빈 대체물로 바꾼다. 표지: 산출이 지어졌다.
// - `render:<컴포넌트>`: 페이지의 `ict()`(판 `1793146503-9e85`의 `app.js`를 읽었다)와 같은 차례로 카드 문서를 짓는다.
//   `<html data-theme data-mode>`, 토큰 CSS(받은 사본 `received/page-tokens.css`), 묶음 CSS, React 전역, 묶음 JS,
//   카드(뿌리 요소 하나와 장면 스크립트 하나)의 차례다. React 전역은 이 저장소의 React 19.3.0을 같은 대체 없이 IIFE로
//   지은 것이다(React 18.3.1 사본은 이 저장소에 없다). 표지: 장면 스크립트가 `window.__sceneCount`에 showcase 수를 적었고
//   그만큼의 `[data-scene]`이 그려졌다. 결과: 페이지 오류와 콘솔 오류의 수.
// - `cascade:<컴포넌트>:<갈래>`: 같은 카드를 세 갈래로 띄워 `#root` 아래 요소의 배경색·글자색을 모은다.
//   `edit`는 토큰 CSS 뒤에 층 없는 `[data-theme="nokcheong-light"]`로 `tokens.json`의 색 토큰 이름을 모두 `#ff0000`으로
//   덮어(웹 편집의 흉내) 빨간 요소를 센다. `layered`는 같은 덮기를 받은 토큰 CSS와 함께 묶음 CSS보다 먼저 선언한 층
//   (`@layer page`) 안에 둔다. 두 갈래를 가르는 것은 페이지 토큰 CSS가 층 밖이라는 것 하나다. `edit`에서 빨갛고
//   `layered`에서 빨갛지 않으면, 페이지 쪽이 이기는 까닭이 층 밖이라는 데 있다는 해석이 선다(뒤에 실린 쪽이 이긴다는
//   해석이면 두 갈래 모두 빨갛지 않다). 표지: 그 카드의 `render` 표지가 있다.
// - `mode:<컴포넌트>`: `data-theme="nokcheong-dark"`로 띄우고 `data-mode`만 `light`와 `dark`로 바꿔 요소 색을 견준다.
//   페이지는 테마 이름이 `/dark|night/i`에 맞을 때만 `dark`를 붙인다. 표지: 두 갈래 모두 `render` 표지가 있다.
// - `mode-bare:<컴포넌트>`: `mode`의 양성 대조. 토큰 CSS 없이 `data-theme="nokcheong"`로 띄우고 `data-mode`만 바꾼다.
//   이 문서에서 `data-mode`가 색을 바꿀 수 있다면 여기서 다른 요소가 나온다. 표지: 두 갈래 모두 그려졌다.
// - `dark-match:<컴포넌트>`: 토큰 CSS와 `nokcheong-dark`에 `data-mode="light"`(이름이 한국어일 때 페이지가 붙이는 값)로
//   띄운 색을, 토큰 CSS 없이 코드의 선택자(`nokcheong`, `dark`)로 띄운 색과 견준다. 표지: 두 갈래 모두 그려졌다.
// - `theme-match:<컴포넌트>`: 페이지 id(`guncheong-light`)와 코드 선택자(`guncheong`)의 어긋남을 본다. 토큰 CSS와 페이지 id,
//   토큰 CSS 없이 코드 선택자, 토큰 CSS 없이 페이지 id의 세 갈래다. 앞의 둘이 같고 뒤의 둘이 다르면, 어긋남은 토큰 CSS가
//   덮고 토큰 CSS가 없을 때만 드러난다는 해석이 선다. 표지: 세 갈래 모두 그려졌다.
// - `stage`: 임시 디자인 시스템 아티팩트에 올릴 정식 자리 배치를 `<작업 폴더>/stage/`에 쓴다. `tokens.json`(테마 이름
//   끝에 ` (Light)`·` (Dark)`를 붙인다. ADR 0025 2026-10-28 이력의 다크 테마), `components/bundle.js`(1행 `@ds-bundle`
//   머리), `components/bundle.css`(빌드 CSS 뒤에 글꼴 CSS를 붙이고 글꼴 주소를 `../fonts/<이름>`으로 바꾼다),
//   `components/<컴포넌트>/preview.html`(1행 `@dsCard` 표지, 뿌리 요소, 장면 스크립트), `components/<컴포넌트>/README.md`
//   (컴포넌트 옆 `<이름>.md`의 사본), `fonts/`(글꼴 파일. 인라인 한도는 vite 기본값이라 지난 산출과 같은 이름이 나온다)다.
//   색인(`design-system.json`)은 쓰지 않는다. 표지: 카드 아홉과 글꼴 700개 넘게 썼고 묶음 CSS의 글꼴 주소가 모두
//   `../fonts/`나 `data:`다.
//
// 저장소 쪽은 작업 트리를 읽는다. 요약에 그때의 `HEAD`와 `web/packages/ui` 아래 커밋하지 않은 변경의 수를 적는다.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const out = process.argv[2];
if (out === undefined || !path.isAbsolute(out)) {
  console.error("작업 폴더를 절대 경로로 준다");
  process.exit(2);
}
if (fs.existsSync(out)) {
  console.error(`작업 폴더가 이미 있다: ${out}. 지우지 않으니 없는 경로를 준다`);
  process.exit(2);
}
fs.mkdirSync(out, { recursive: true });

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const ui = path.join(repo, "web/packages/ui");
const posix = (p) => p.replaceAll("\\", "/");
const componentsDir = posix(path.join(ui, "src/components")).toLowerCase();
const vite = await import(pathToFileURL(path.join(ui, "node_modules/vite/dist/node/index.js")).href);
const { chromium } = await import(pathToFileURL(path.join(repo, "web/node_modules/playwright/index.mjs")).href);

const rounds = [];
function round(name, fn) {
  return Promise.resolve()
    .then(fn)
    .then(
      (r) => rounds.push({ name, marked: r.marked === true, ...r }),
      (e) => rounds.push({ name, marked: false, error: String(e?.stack ?? e).slice(0, 1500) }),
    );
}
const marked = (name) => rounds.find((r) => r.name === name)?.marked === true;

const define = { "process.env.NODE_ENV": JSON.stringify("production") };
const GLOBALS = { react: "React", "react-dom": "ReactDOM", "react-dom/client": "ReactDOM", "agent-os-ui-global": "AgentOsUi" };
const JSX_SHIM = `import { createElement, Fragment } from "react";
export { Fragment };
function split(props, key) {
  const { children, ...rest } = props ?? {};
  if (key !== undefined) rest.key = key;
  return [rest, children];
}
export function jsx(type, props, key) {
  const [rest, children] = split(props, key);
  return children === undefined ? createElement(type, rest) : createElement(type, rest, children);
}
export function jsxs(type, props, key) {
  const [rest, children] = split(props, key);
  return createElement(type, rest, ...children);
}
export const jsxDEV = jsx;`;
const SB_TEST_STUB = `const noop = () => {};
export const fn = () => noop;
export const expect = () => new Proxy({}, { get: () => noop });
export const within = () => ({});
export const userEvent = {};
export const waitFor = noop;`;

function virtual(id, code, match) {
  return {
    name: `virtual:${id}`,
    enforce: "pre",
    resolveId: (source) => (match(source) ? `\0${id}` : null),
    load: (loaded) => (loaded === `\0${id}` ? code : null),
  };
}
const jsxShim = () => virtual("jsx-shim", JSX_SHIM, (s) => s === "react/jsx-runtime" || s === "react/jsx-dev-runtime");
const sbStub = () => virtual("sb-test", SB_TEST_STUB, (s) => s === "storybook/test");
function uiGlobal() {
  return {
    name: "ui-global",
    enforce: "pre",
    async resolveId(source, importer, opts) {
      if (importer === undefined || !source.startsWith(".")) return null;
      const r = await this.resolve(source, importer, { ...opts, skipSelf: true });
      if (r === null || r.external) return null;
      const id = posix(r.id).toLowerCase();
      if (id.startsWith(componentsDir) && !id.endsWith(".stories.tsx")) return { id: "agent-os-ui-global", external: true };
      return null;
    },
  };
}

async function buildIife({ entry, name, plugins, external, alias = {} }) {
  const result = await vite.build({
    configFile: false,
    root: ui,
    logLevel: "silent",
    define,
    plugins,
    resolve: { alias },
    build: {
      write: false,
      minify: true,
      lib: { entry, formats: ["iife"], name, fileName: () => "out.js" },
      rolldownOptions: { external, output: { globals: GLOBALS } },
    },
  });
  const outputs = (Array.isArray(result) ? result : [result]).flatMap((r) => r.output);
  const chunk = outputs.find((o) => o.type === "chunk");
  if (chunk === undefined) throw new Error("산출 조각이 없다");
  return chunk.code;
}
const count = (text, needle) => text.split(needle).length - 1;

// bundle
let bundleJs = "";
await round("bundle", async () => {
  bundleJs = await buildIife({
    entry: path.join(ui, "src/index.ts"),
    name: "AgentOsUi",
    plugins: [jsxShim()],
    external: ["react", "react-dom", "react-dom/client"],
  });
  fs.writeFileSync(path.join(out, "bundle.js"), bundleJs);
  const assigns = /\bAgentOsUi\s*=/.test(bundleJs);
  const bad = { require: count(bundleJs, "require("), importStatement: (bundleJs.match(/(^|[;\n])\s*import\s/g) ?? []).length, transitional: count(bundleJs, "react.transitional.element") };
  return { marked: assigns && bad.require === 0 && bad.importStatement === 0 && bad.transitional === 0, bytes: Buffer.byteLength(bundleJs), assigns, ...bad, scriptClose: count(bundleJs, "</script"), htmlComment: count(bundleJs, "<!--") };
});

// css
let bundleCss = "";
await round("css", async () => {
  const cli = path.join(ui, "node_modules/@tailwindcss/cli/dist/index.mjs");
  const file = path.join(out, "bundle.css");
  const r = spawnSync(process.execPath, [cli, "-i", "src/styles/theme.css", "-o", file, "--minify"], { cwd: ui, encoding: "utf8" });
  if (r.status !== 0) throw new Error(`tailwindcss ${r.status}: ${r.stderr}`);
  bundleCss = fs.readFileSync(file, "utf8");
  return { marked: bundleCss.includes("@layer theme") && bundleCss.includes("--accent-600:"), bytes: Buffer.byteLength(bundleCss), fontFace: count(bundleCss, "@font-face") };
});

// fonts
await round("fonts", async () => {
  const result = await vite.build({
    configFile: false,
    root: ui,
    logLevel: "silent",
    build: { write: false, assetsInlineLimit: 0, assetsDir: "fonts", rolldownOptions: { input: path.join(ui, "src/styles/fonts.css") } },
  });
  const assets = (Array.isArray(result) ? result : [result]).flatMap((r) => r.output).filter((o) => o.type === "asset");
  const fonts = assets.map((a) => a.fileName).filter((n) => /\.woff2?$/.test(n));
  const shown = spawnSync("git", ["-C", repo, "show", "35028cba:.design-sync/upload-output.json"], { encoding: "utf8" });
  if (shown.status !== 0) throw new Error(`git show ${shown.status}: ${shown.stderr}`);
  const previous = new Set(JSON.parse(shown.stdout).filter((p) => /^project\/fonts\/.+\.woff2?$/.test(p)).map((p) => p.slice("project/".length)));
  const same = fonts.filter((n) => previous.has(n)).length;
  return { marked: fonts.length > 700, emitted: fonts.length, previous: previous.size, sameName: same, sample: fonts.slice(0, 2), previousSample: [...previous].slice(0, 2) };
});

// 엔트리는 작업 폴더의 파일로 쓴다. lib 모드는 엔트리를 `root` 기준 경로로 풀어 가상 모듈 이름을 받지 않는다.
const entries = path.join(out, "entries");
fs.mkdirSync(entries);
function entryFile(name, code) {
  const file = path.join(entries, `${name}.mjs`);
  fs.writeFileSync(file, code);
  return file;
}

// React 전역(시험 문서용)
const reactGlobals = await buildIife({
  entry: entryFile("react-globals", `import * as React from "react"; import * as ReactDOM from "react-dom"; import { createRoot } from "react-dom/client"; window.React = React; window.ReactDOM = { ...ReactDOM, createRoot };`),
  name: "__reactGlobals",
  plugins: [],
  external: [],
  // 엔트리가 작업 폴더에 있어 맨 이름 import 가 패키지의 node_modules 에 닿지 않는다.
  alias: { react: path.join(ui, "node_modules/react"), "react-dom": path.join(ui, "node_modules/react-dom") },
}).catch((e) => {
  rounds.push({ name: "react-globals", marked: false, error: String(e) });
  return "";
});

// 장면
const storyFiles = fs
  .readdirSync(path.join(ui, "src/components"), { recursive: true })
  .map(String)
  .filter((f) => f.endsWith(".stories.tsx"))
  .map((f) => path.join(ui, "src/components", f));
const scenes = new Map();
for (const file of storyFiles) {
  const comp = path.basename(file, ".stories.tsx");
  await round(`scene:${comp}`, async () => {
    const entry = `import * as mod from ${JSON.stringify(posix(file))};
const R = window.React, D = window.ReactDOM, meta = mod.default;
const shown = Object.entries(mod).filter(([k, s]) => k !== "default" && s && Array.isArray(s.tags) && s.tags.includes("showcase"));
const tree = R.createElement(R.Fragment, null, ...shown.map(([k, s]) => {
  const args = { ...(meta.args ?? {}), ...(s.args ?? {}) };
  const body = typeof s.render === "function" ? s.render(args, { args }) : R.createElement(meta.component, args);
  return R.createElement("section", { key: k, "data-scene": k }, body);
}));
D.createRoot(document.getElementById("root")).render(tree);
window.__sceneCount = shown.length;`;
    const code = await buildIife({
      entry: entryFile(`scene-${comp}`, entry),
      name: "__scene",
      plugins: [uiGlobal(), jsxShim(), sbStub()],
      external: ["react", "react-dom", "react-dom/client"],
    });
    scenes.set(comp, code);
    return { marked: true, bytes: Buffer.byteLength(code), scriptClose: count(code, "</script"), mentionsUiGlobal: code.includes("AgentOsUi") };
  });
}

// 카드 문서
const pageTokens = fs.readFileSync(path.join(repo, ".scratch/design-card-build/probes/received/page-tokens.css"), "utf8");
const tokensJson = JSON.parse(spawnSync(process.execPath, [path.join(repo, "web/tools/sync-design-system/main.ts"), "build", "--out", path.join(out, "tokens.json")], { cwd: repo, encoding: "utf8" }).status === 0 ? fs.readFileSync(path.join(out, "tokens.json"), "utf8") : "{}");
const colorNames = (tokensJson?.color?.tokens ?? []).map((t) => t.name).filter(Boolean);
if (colorNames.length === 0) rounds.push({ name: "tokens.json", marked: false, error: "색 토큰을 읽지 못했다" });
const redOverride = `[data-theme="nokcheong-light"]{${colorNames.map((n) => `--${n}:#ff0000;`).join("")}}`;
const esc = (code) => code.replaceAll("</script", "<\\/script");
function cardDoc({ theme, mode, tokensCss }) {
  return `<!doctype html><html data-theme="${theme}" data-mode="${mode}" style="color-scheme:${mode}" class="${theme} ${mode}"><head><meta name="referrer" content="no-referrer"></head><body>
<style>html{overflow:hidden!important}</style><style>${tokensCss}</style><style>${bundleCss}</style>
<script>${esc(reactGlobals)}</script><script>${esc(bundleJs)}</script>
<!-- @dsCard group="probe" -->
<div id="root" data-ui-root></div>
<script>window.__sceneError = null; try { SCENE } catch (e) { window.__sceneError = String(e && e.stack || e); }</script>
</body></html>`;
}
const browser = await chromium.launch();
async function show(comp, opts) {
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(`console: ${m.text()}`);
  });
  const html = cardDoc(opts).replace("SCENE", () => esc(scenes.get(comp)));
  fs.writeFileSync(path.join(out, `${comp}-${opts.label}.html`), html);
  await page.setContent(html, { waitUntil: "load" });
  await page.waitForTimeout(300);
  const seen = await page.evaluate(() => {
    const root = document.getElementById("root");
    const els = root === null ? [] : [...root.querySelectorAll("*")];
    return {
      sceneCount: window.__sceneCount ?? null,
      sceneError: window.__sceneError,
      sections: document.querySelectorAll("[data-scene]").length,
      elements: els.length,
      colors: els.map((e) => {
        const s = getComputedStyle(e);
        return `${s.backgroundColor}|${s.color}`;
      }),
    };
  });
  await page.close();
  return { ...seen, errors };
}
const rendered = (s) => typeof s.sceneCount === "number" && s.sceneCount > 0 && s.sections === s.sceneCount;
const RED = "rgb(255, 0, 0)";
const reds = (s) => s.colors.filter((c) => c.includes(RED)).length;
// 같은 장면이라 요소의 차례가 같다. 요소 수가 다르면 그 차이도 다른 것으로 센다.
const differ = (a, b) => a.colors.filter((c, i) => c !== b.colors[i]).length + Math.abs(a.colors.length - b.colors.length);
const firstDiff = (a, b) => {
  const i = a.colors.findIndex((c, j) => c !== b.colors[j]);
  return i < 0 ? null : { index: i, a: a.colors[i], b: b.colors[i] };
};

for (const comp of scenes.keys()) {
  await round(`render:${comp}`, async () => {
    const s = await show(comp, { theme: "nokcheong-light", mode: "light", tokensCss: pageTokens, label: "light" });
    return { marked: rendered(s), sceneCount: s.sceneCount, sections: s.sections, elements: s.elements, sceneError: s.sceneError, errors: s.errors.slice(0, 5) };
  });
}
for (const comp of scenes.keys()) {
  if (!marked(`render:${comp}`)) continue;
  for (const [label, tokensCss] of [
    ["edit", `${pageTokens}\n${redOverride}`],
    ["layered", `@layer page{${pageTokens}\n${redOverride}}`],
  ]) {
    await round(`cascade:${comp}:${label}`, async () => {
      const s = await show(comp, { theme: "nokcheong-light", mode: "light", tokensCss, label });
      return { marked: rendered(s), redElements: reds(s), elements: s.elements, errors: s.errors.slice(0, 3) };
    });
  }
  await round(`mode:${comp}`, async () => {
    const light = await show(comp, { theme: "nokcheong-dark", mode: "light", tokensCss: pageTokens, label: "dark-theme-light-mode" });
    const dark = await show(comp, { theme: "nokcheong-dark", mode: "dark", tokensCss: pageTokens, label: "dark-theme-dark-mode" });
    return { marked: rendered(light) && rendered(dark), elements: light.elements, colorsDiffer: differ(light, dark) };
  });
  await round(`mode-bare:${comp}`, async () => {
    const light = await show(comp, { theme: "nokcheong", mode: "light", tokensCss: "", label: "bare-light" });
    const dark = await show(comp, { theme: "nokcheong", mode: "dark", tokensCss: "", label: "bare-dark" });
    return { marked: rendered(light) && rendered(dark), elements: light.elements, colorsDiffer: differ(light, dark) };
  });
  await round(`dark-match:${comp}`, async () => {
    const page = await show(comp, { theme: "nokcheong-dark", mode: "light", tokensCss: pageTokens, label: "page-dark-as-light" });
    const code = await show(comp, { theme: "nokcheong", mode: "dark", tokensCss: "", label: "bare-dark" });
    return { marked: rendered(page) && rendered(code), elements: page.elements, colorsDiffer: differ(page, code), sample: firstDiff(page, code) };
  });
  await round(`theme-match:${comp}`, async () => {
    const page = await show(comp, { theme: "guncheong-light", mode: "light", tokensCss: pageTokens, label: "page-guncheong" });
    const code = await show(comp, { theme: "guncheong", mode: "light", tokensCss: "", label: "bare-guncheong" });
    const bareId = await show(comp, { theme: "guncheong-light", mode: "light", tokensCss: "", label: "bare-guncheong-light" });
    return {
      marked: rendered(page) && rendered(code) && rendered(bareId),
      elements: page.elements,
      pageVsCode: differ(page, code),
      bareIdVsCode: differ(bareId, code),
      sample: firstDiff(page, code),
    };
  });
}
await browser.close();

// stage
await round("stage", async () => {
  const stage = path.join(out, "stage");
  const write = (rel, data) => {
    const file = path.join(stage, rel);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, data);
  };
  const suffix = (id) => (id.endsWith("-dark") ? " (Dark)" : " (Light)");
  const renamed = { ...tokensJson, color: { ...tokensJson.color, themes: tokensJson.color.themes.map((t) => ({ ...t, name: `${t.name}${suffix(t.id)}` })) } };
  write("tokens.json", `${JSON.stringify(renamed, null, 2)}\n`);
  const names = [...scenes.keys()];
  const header = `/* @ds-bundle: ${JSON.stringify({ format: 4, namespace: "AgentOsUi", components: names.map((name) => ({ name })) })} */\n`;
  write("components/bundle.js", header + bundleJs);
  const result = await vite.build({
    configFile: false,
    root: ui,
    logLevel: "silent",
    build: { write: false, assetsDir: "fonts", rolldownOptions: { input: path.join(ui, "src/styles/fonts.css") } },
  });
  const assets = (Array.isArray(result) ? result : [result]).flatMap((r) => r.output).filter((o) => o.type === "asset");
  const fontAssets = assets.filter((a) => /\.woff2?$/.test(a.fileName));
  for (const a of fontAssets) write(`fonts/${path.basename(a.fileName)}`, a.source);
  const fontsCss = String(assets.find((a) => a.fileName.endsWith(".css"))?.source ?? "");
  const rewritten = fontsCss.replace(/url\((["']?)(?!data:)[^)"']*\/([^/)"']+\.woff2?)\1\)/g, "url(../fonts/$2)");
  const urls = rewritten.match(/url\([^)]*\)/g) ?? [];
  const badUrls = urls.filter((u) => !u.startsWith("url(../fonts/") && !/^url\(["']?data:/.test(u));
  write("components/bundle.css", `${bundleCss}\n${rewritten}`);
  const storyDir = new Map(storyFiles.map((f) => [path.basename(f, ".stories.tsx"), path.dirname(f)]));
  for (const [comp, code] of scenes) {
    const dir = storyDir.get(comp);
    const group = path.basename(dir);
    write(`components/${comp}/preview.html`, `<!-- @dsCard group="${group}" -->\n<div id="root" data-ui-root></div>\n<script>${esc(code)}</script>\n`);
    const doc = path.join(dir, `${comp}.md`);
    if (fs.existsSync(doc)) write(`components/${comp}/README.md`, fs.readFileSync(doc));
  }
  write("README.md", "# Agent OS 디자인 시스템 (임시 측정)\n\ndesign-card-build 명세의 측정용 임시 사본이다. 지우기 전까지 이 페이지를 고치지 않는다.\n");
  const cards = names.filter((c) => fs.existsSync(path.join(stage, `components/${c}/preview.html`))).length;
  const readmes = names.filter((c) => fs.existsSync(path.join(stage, `components/${c}/README.md`))).length;
  return {
    marked: cards === names.length && fontAssets.length > 700 && badUrls.length === 0 && urls.length > 0,
    cards,
    readmes,
    fonts: fontAssets.length,
    fontBytes: fontAssets.reduce((n, a) => n + a.source.length, 0),
    fontUrls: urls.length,
    badUrls: badUrls.slice(0, 3),
    bundleCssBytes: Buffer.byteLength(`${bundleCss}\n${rewritten}`),
    themeNames: renamed.color.themes.map((t) => t.name),
  };
});

const git =(...args) => spawnSync("git", ["-C", repo, ...args], { encoding: "utf8" }).stdout.trim();
const summary = {
  head: git("rev-parse", "HEAD"),
  uiUncommitted: git("status", "--porcelain", "--", "web/packages/ui").split("\n").filter(Boolean).length,
  colorTokens: colorNames.length,
  measured: rounds.filter((r) => r.marked).length,
  notMeasured: rounds.filter((r) => !r.marked).map((r) => r.name),
  rounds,
};
fs.writeFileSync(path.join(out, "summary.json"), JSON.stringify(summary, null, 2));
console.log(JSON.stringify(summary, null, 2));
process.exit(summary.notMeasured.length === 0 ? 0 : 1);
