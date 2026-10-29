// `vite_cli.mjs`가 잰 길을 올리기 도구가 쓸 모양 그대로 지나게 한다. 도구는 TypeScript이고(`web/tsconfig.json`의 strict),
// vite를 import하지 않으며, 설정을 import 없는 글로 지어 파일에 쓰고, 셸을 거치지 않고 `process.execPath`로 디자인 시스템
// 패키지의 vite 실행 파일(`node_modules/vite/bin/vite.js`)을 패키지 자리에서 띄운다. 이 파일이 타입 검사와 실행을 지나는지가
// 소비 지점이다(`docs/agents/issue-tracker.md` 프로브와 근거).
//
// 타입 검사(저장소 루트에서): pnpm -C web exec tsc -p ../.scratch/design-card-build/probes/tsconfig.json
// 실행(저장소 루트에서): node .scratch/design-card-build/probes/vite_cli_tool.mts <작업 폴더의 절대 경로> <card_build의 bundle.js>
// 작업 폴더는 아직 없는 절대 경로여야 한다(이 프로브는 아무 폴더도 지우지 않는다). 공백이 든 경로를 주면 셸 없이 넘긴
// 인자가 공백에서 갈리지 않는지도 함께 본다(요약의 `outHasSpace`).
//
// 회차와 표지:
// - `bundle:bin`: vite가 0으로 끝났고, 산출 파일에 `AgentOsUi` 대입이 있다. `card_build`의 묶음과 바이트로 견준다.
// - `control:compare`: 견주기의 양성 대조. 같은 산출을 한 바이트 바꾼 글과 견주면 같지 않다고 나온다.
// 표지가 없는 회차는 측정이 아니라고 세고, 그런 회차가 하나라도 있으면 종료 1이다.
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";

interface Round {
  readonly name: string;
  readonly marked: boolean;
  readonly detail: Readonly<Record<string, string | number | boolean | null>>;
}

const [out, apiBundle] = process.argv.slice(2);
if (out === undefined || apiBundle === undefined || !isAbsolute(out) || existsSync(out)) {
  console.error("작업 폴더는 아직 없는 절대 경로여야 하고, card_build의 bundle.js를 함께 준다");
  process.exit(2);
}
mkdirSync(out);
const ui = join(process.cwd(), "web", "packages", "ui");
const posix = (p: string): string => p.replaceAll("\\", "/");
const rounds: Round[] = [];

function configText(entry: string, outDir: string): string {
  return `export default {
  root: ${JSON.stringify(posix(ui))},
  logLevel: "warn",
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  plugins: [{
    name: "virtual:jsx-shim",
    enforce: "pre",
    resolveId: (s) => (s === "react/jsx-runtime" || s === "react/jsx-dev-runtime" ? "\\0jsx-shim" : null),
    load: (id) => (id === "\\0jsx-shim" ? ${JSON.stringify(JSX_SHIM)} : null),
  }],
  build: {
    outDir: ${JSON.stringify(posix(outDir))},
    emptyOutDir: false,
    minify: true,
    lib: { entry: ${JSON.stringify(posix(entry))}, formats: ["iife"], name: "AgentOsUi", fileName: () => "out.js" },
    rolldownOptions: {
      external: ["react", "react-dom", "react-dom/client"],
      output: { globals: { react: "React", "react-dom": "ReactDOM", "react-dom/client": "ReactDOM" } },
    },
  },
};
`;
}

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

let built: string | null = null;
{
  const outDir = join(out, "bundle");
  const config = join(out, "bundle.config.mjs");
  writeFileSync(config, configText(join(ui, "src", "index.ts"), outDir));
  const started = Date.now();
  const run = spawnSync(process.execPath, [join(ui, "node_modules", "vite", "bin", "vite.js"), "build", "--config", config], {
    cwd: ui,
    encoding: "utf8",
  });
  const file = join(outDir, "out.js");
  const ok = run.error === undefined && run.status === 0 && existsSync(file);
  built = ok ? readFileSync(file, "utf8") : null;
  const api = existsSync(apiBundle) ? readFileSync(apiBundle, "utf8") : null;
  rounds.push({
    name: "bundle:bin",
    marked: built !== null && /\bAgentOsUi\s*=/.test(built),
    detail: {
      status: run.status,
      ms: Date.now() - started,
      bytes: built === null ? null : Buffer.byteLength(built),
      sameAsApiBuild: built === null || api === null ? null : built === api,
      stderr: run.stderr.slice(-400),
    },
  });
}

{
  const changed = built === null ? null : `${built} `;
  rounds.push({
    name: "control:compare",
    marked: changed !== null,
    detail: { sameAsChanged: changed === null ? null : changed === built },
  });
}

const notMeasured = rounds.filter((r) => !r.marked).map((r) => r.name);
const head = spawnSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).stdout.trim();
const summary = { head, outHasSpace: out.includes(" "), rounds, notMeasured };
writeFileSync(join(out, "summary.json"), `${JSON.stringify(summary, null, 2)}\n`);
console.log(JSON.stringify(summary, null, 2));
process.exit(notMeasured.length > 0 ? 1 : 0);
