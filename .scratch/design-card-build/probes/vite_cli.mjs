// 짓기 명령이 vite를 디자인 시스템 패키지의 자리에서 CLI로 불러도(`pnpm -C web/packages/ui exec vite build --config <파일>`)
// `card_build.mjs`가 vite의 JS API로 지은 것과 같은 묶음과 장면이 나오는지 잰다. 올리기 도구는 `web/` 뿌리 쪽이라
// vite를 import할 수 없다(`web/node_modules/vite`가 없다). 그래서 도구가 설정 파일을 글로 지어 임시 폴더에 쓰고 CLI에 넘기는
// 길을 잰다. 설정 파일은 아무것도 import하지 않는 `.mjs`다.
//
// 돌리는 법(저장소 루트에서): node .scratch/design-card-build/probes/vite_cli.mjs <작업 폴더의 절대 경로> [<card_build의 작업 폴더>]
// 작업 폴더는 아직 없는 절대 경로여야 한다(이 프로브는 아무 폴더도 지우지 않는다). 둘째 인자를 주면 지은 것을 같은 커밋에서
// 돈 `card_build.mjs`의 산출(`bundle.js`, `bundle.css`, `stage/components/<이름>/preview.html`의 스크립트, `stage/fonts/`)과
// 바이트나 이름으로 견준다.
//
// 회차와 표지:
// - `bundle`: CLI가 0으로 끝났고, 산출 파일에 `AgentOsUi` 대입이 있다. `require(`·`import` 문·`react.transitional.element`를 센다.
// - `scene:Button`: CLI가 0으로 끝났고, 산출 파일이 `window.__sceneCount`를 적고 패키지를 전역 `AgentOsUi`로 부른다.
// - `control:scene-differs`: 견주기의 양성 대조. 다른 컴포넌트(Alert)의 카드 스크립트가 있고, 그것과 견주면 같지 않다고 나온다.
//   이 회차가 없으면 `sameAsApiBuild: true`가 견주기가 늘 참을 내는 것과 갈리지 않는다.
// - `css`: `pnpm exec tailwindcss`가 0으로 끝났고, 산출에 `@layer theme`과 `--accent-600:`이 있다.
// - `fonts`: CLI가 0으로 끝났고, 산출 폴더 `fonts/`에 woff·woff2가 700개를 넘는다.
// - `config-has-no-import`: 지은 설정 파일 셋에 `import` 문이 0이다(표지는 파일을 다시 읽은 글자다).
// 표지가 없는 회차는 측정이 아니라고 세고, 그런 회차가 하나라도 있으면 종료 1이다.
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const [out, apiRun] = process.argv.slice(2);
if (out === undefined || !path.isAbsolute(out) || fs.existsSync(out)) {
  console.error("작업 폴더는 아직 없는 절대 경로여야 한다");
  process.exit(2);
}
fs.mkdirSync(out);
const repo = process.cwd();
const ui = path.join(repo, "web/packages/ui");
const posix = (p) => p.replaceAll("\\", "/");
const count = (text, needle) => text.split(needle).length - 1;
const rounds = [];
// card_build 산출의 파일. 둘째 인자가 없거나 파일이 없으면 null이다.
const apiFile = (rel) => {
  if (apiRun === undefined) return null;
  const file = path.join(apiRun, rel);
  return fs.existsSync(file) ? fs.readFileSync(file, "utf8") : null;
};
const cardScript = (name) => apiFile(`stage/components/${name}/preview.html`)?.match(/<script>([\s\S]*)<\/script>/)?.[1] ?? null;

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

// 설정 파일의 글. 플러그인은 객체 글자로 두고 vite를 import하지 않는다.
function configText({ entry, name, outDir, uiGlobal }) {
  const componentsDir = posix(path.join(ui, "src/components")).toLowerCase();
  return `const GLOBALS = { react: "React", "react-dom": "ReactDOM", "react-dom/client": "ReactDOM", "agent-os-ui-global": "AgentOsUi" };
const virtual = (id, code, match) => ({
  name: "virtual:" + id,
  enforce: "pre",
  resolveId: (source) => (match(source) ? "\\0" + id : null),
  load: (loaded) => (loaded === "\\0" + id ? code : null),
});
const plugins = [
  virtual("jsx-shim", ${JSON.stringify(JSX_SHIM)}, (s) => s === "react/jsx-runtime" || s === "react/jsx-dev-runtime"),
  virtual("sb-test", ${JSON.stringify(SB_TEST_STUB)}, (s) => s === "storybook/test"),
];
${
  uiGlobal
    ? `plugins.push({
  name: "ui-global",
  enforce: "pre",
  async resolveId(source, importer, opts) {
    if (importer === undefined || !source.startsWith(".")) return null;
    const r = await this.resolve(source, importer, { ...opts, skipSelf: true });
    if (r === null || r.external) return null;
    const id = r.id.replaceAll("\\\\", "/").toLowerCase();
    if (id.startsWith(${JSON.stringify(componentsDir)}) && !id.endsWith(".stories.tsx")) return { id: "agent-os-ui-global", external: true };
    return null;
  },
});`
    : ""
}
export default {
  root: ${JSON.stringify(posix(ui))},
  logLevel: "warn",
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  plugins,
  build: {
    outDir: ${JSON.stringify(posix(outDir))},
    emptyOutDir: false,
    minify: true,
    lib: { entry: ${JSON.stringify(posix(entry))}, formats: ["iife"], name: ${JSON.stringify(name)}, fileName: () => "out.js" },
    rolldownOptions: { external: ["react", "react-dom", "react-dom/client"], output: { globals: GLOBALS } },
  },
};
`;
}

// 글꼴은 lib 모드가 아니라 CSS 하나를 입력으로 지어 그 자산만 받는다(card_build의 `fonts` 회차와 같은 옵션).
function fontsConfigText({ outDir }) {
  return `export default {
  root: ${JSON.stringify(posix(ui))},
  logLevel: "warn",
  build: {
    outDir: ${JSON.stringify(posix(outDir))},
    emptyOutDir: false,
    assetsInlineLimit: 0,
    assetsDir: "fonts",
    rolldownOptions: { input: ${JSON.stringify(posix(path.join(ui, "src/styles/fonts.css")))} },
  },
};
`;
}

function runPnpm(args) {
  const started = Date.now();
  const r = spawnSync("pnpm", ["-C", posix(ui), "exec", ...args], { encoding: "utf8", shell: true });
  return { status: r.status, ms: Date.now() - started, stderr: (r.stderr ?? "").slice(-600) };
}
const runVite = (config) => runPnpm(["vite", "build", "--config", posix(config)]);

function round(name, fn) {
  try {
    const result = fn();
    rounds.push({ name, ...result });
  } catch (e) {
    rounds.push({ name, marked: false, error: String(e) });
  }
}

const configs = [];
let sceneButton = null;

round("bundle", () => {
  const outDir = path.join(out, "bundle");
  const config = path.join(out, "bundle.config.mjs");
  fs.writeFileSync(config, configText({ entry: path.join(ui, "src/index.ts"), name: "AgentOsUi", outDir, uiGlobal: false }));
  configs.push(config);
  const run = runVite(config);
  const file = path.join(outDir, "out.js");
  if (run.status !== 0 || !fs.existsSync(file)) return { marked: false, ...run };
  const code = fs.readFileSync(file, "utf8");
  const api = apiFile("bundle.js");
  const same = api === null ? null : api === code;
  return {
    marked: /\bAgentOsUi\s*=/.test(code),
    status: run.status,
    ms: run.ms,
    bytes: Buffer.byteLength(code),
    require: count(code, "require("),
    importStatement: (code.match(/(^|[;\n])\s*import\s/g) ?? []).length,
    transitional: count(code, "react.transitional.element"),
    sameAsApiBuild: same,
  };
});

round("scene:Button", () => {
  const story = path.join(ui, "src/components/atoms/Button.stories.tsx");
  const entry = path.join(out, "scene-Button.mjs");
  fs.writeFileSync(
    entry,
    `import * as mod from ${JSON.stringify(posix(story))};
const R = window.React, D = window.ReactDOM, meta = mod.default;
const shown = Object.entries(mod).filter(([k, s]) => k !== "default" && s && Array.isArray(s.tags) && s.tags.includes("showcase"));
const tree = R.createElement(R.Fragment, null, ...shown.map(([k, s]) => {
  const args = { ...(meta.args ?? {}), ...(s.args ?? {}) };
  const body = typeof s.render === "function" ? s.render(args, { args }) : R.createElement(meta.component, args);
  return R.createElement("section", { key: k, "data-scene": k }, body);
}));
D.createRoot(document.getElementById("root")).render(tree);
window.__sceneCount = shown.length;`,
  );
  const outDir = path.join(out, "scene-Button");
  const config = path.join(out, "scene-Button.config.mjs");
  fs.writeFileSync(config, configText({ entry, name: "__scene", outDir, uiGlobal: true }));
  configs.push(config);
  const run = runVite(config);
  const file = path.join(outDir, "out.js");
  if (run.status !== 0 || !fs.existsSync(file)) return { marked: false, ...run };
  const code = fs.readFileSync(file, "utf8");
  sceneButton = code;
  const api = cardScript("Button");
  return {
    marked: code.includes("__sceneCount") && code.includes("AgentOsUi"),
    status: run.status,
    ms: run.ms,
    bytes: Buffer.byteLength(code),
    transitional: count(code, "react.transitional.element"),
    sameAsApiBuild: api === null ? null : api === code,
  };
});

round("control:scene-differs", () => {
  const other = cardScript("Alert");
  return { marked: other !== null && sceneButton !== null, sameAsAlert: other === sceneButton };
});

round("css", () => {
  const file = path.join(out, "bundle.css");
  const run = runPnpm(["tailwindcss", "-i", "src/styles/theme.css", "-o", posix(file), "--minify"]);
  if (run.status !== 0 || !fs.existsSync(file)) return { marked: false, ...run };
  const css = fs.readFileSync(file, "utf8");
  const api = apiFile("bundle.css");
  return {
    marked: css.includes("@layer theme") && css.includes("--accent-600:"),
    status: run.status,
    ms: run.ms,
    bytes: Buffer.byteLength(css),
    sameAsApiBuild: api === null ? null : api === css,
  };
});

round("fonts", () => {
  const outDir = path.join(out, "fonts-build");
  const config = path.join(out, "fonts.config.mjs");
  fs.writeFileSync(config, fontsConfigText({ outDir }));
  configs.push(config);
  const run = runVite(config);
  const dir = path.join(outDir, "fonts");
  if (run.status !== 0 || !fs.existsSync(dir)) return { marked: false, ...run };
  const names = fs.readdirSync(dir).filter((n) => /\.woff2?$/.test(n));
  const apiDir = apiRun === undefined ? null : path.join(apiRun, "stage/fonts");
  const apiNames = apiDir !== null && fs.existsSync(apiDir) ? new Set(fs.readdirSync(apiDir).filter((n) => /\.woff2?$/.test(n))) : null;
  return {
    marked: names.length > 700,
    status: run.status,
    ms: run.ms,
    emitted: names.length,
    apiEmitted: apiNames === null ? null : apiNames.size,
    sameName: apiNames === null ? null : names.filter((n) => apiNames.has(n)).length,
  };
});

round("config-has-no-import", () => {
  const imports = configs.map((c) => (fs.readFileSync(c, "utf8").match(/(^|\n)\s*import\s/g) ?? []).length);
  return { marked: configs.length === 3, imports };
});

const notMeasured = rounds.filter((r) => r.marked !== true).map((r) => r.name);
const summary = { head: spawnSync("git", ["-C", repo, "rev-parse", "HEAD"], { encoding: "utf8" }).stdout.trim(), rounds, notMeasured };
fs.writeFileSync(path.join(out, "summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
console.log(JSON.stringify(summary, null, 2));
process.exit(notMeasured.length > 0 ? 1 : 0);
