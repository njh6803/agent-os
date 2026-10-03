// web-widget 위젯 스택 프로브: 후보 하나를 실제로 설치한 임시 워크스페이스를 짓는다.
//   node .scratch/web-widget/probes/widget_stack/setup.mjs <작업 루트> <후보>
// 후보  react | react-pkg | preact | preact-next | lit | lit-std | lit-legacy | vanilla
//   덮어쓰는 차례는 아래 LAYERS 다. react-pkg 는 그 뒤에 apps/widget 의 api/, lib/, components/organisms/ 를
//   packages/widget-ui/ 로 옮긴다(공유 컴포넌트를 packages/ 로 뺀 모양). preact-next 는 Preact 의 TSX 셋 머리에
//   jsxImportSource 프라그마를 단다(tsconfig 는 Next 의 React JSX 이고 Preact 파일만 파일 단위로 바꾼다).
//
// <작업 루트>/<후보>/ 에 저장소의 web/ 사본과 web/ 이 기대는 뿌리 파일 둘(.gitignore, openapi.json)을 두고, 그 위에
// common/ 과 후보 폴더를 덮어쓴다. 저장소의 web/ 은 읽기만 한다. 사본에는 다음을 더한다.
//   - packages/api-client 에 프로브 전용 클라이언트(common/packages/api-client/src/widget.ts)와 그 export 한 줄
//   - vitest.config.ts 에 apps/widget 의 jsdom 프로젝트 하나(관리 화면의 jsdom 프로젝트가 admin 경로만 잡기 때문이다)
// 그리고 git init 과 git add 를 친다. eslint.config.test.ts 가 git 이 추적하는 파일로 판정 범위를 재기 때문이다.
// 끝으로 pnpm install 을 친다(npm 레지스트리에 닿는다). 이미 있으면 지우고 다시 짓는다.

import { spawnSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  renameSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { basename, dirname, join, resolve } from "node:path";

const HERE = import.meta.dirname;
const REPO = resolve(HERE, "..", "..", "..", "..");
const CANDIDATES = [
  "react",
  "react-pkg",
  "preact",
  "preact-next",
  "lit",
  "lit-std",
  "lit-legacy",
  "vanilla",
];
// 후보마다 덮어쓰는 폴더. next/ 는 iframe 페이지를 서빙하는 Next 앱의 뼈대다. preact 는 Next 없이 Vite 만이고,
// preact-next 는 같은 Preact 위젯을 Next 앱과 한 폴더에 둔다.
const LAYERS = {
  react: ["common", "next", "react"],
  "react-pkg": ["common", "next", "react", "react-pkg"],
  preact: ["common", "preact"],
  "preact-next": ["common", "next", "preact", "preact-next"],
  lit: ["common", "next", "lit"],
  "lit-std": ["common", "next", "lit", "lit-std"],
  "lit-legacy": ["common", "next", "lit", "lit-legacy"],
  vanilla: ["common", "next", "vanilla"],
};
// Preact 의 JSX 를 쓰는 파일(preact-next 가 프라그마를 단다).
const PREACT_TSX = ["element.tsx", "page.tsx", "components/organisms/ChatWidget.tsx"];
// packages/ 로 옮기는 것(react-pkg).
const MOVED = ["api", "lib", "components/organisms"];
// 사본에 들이지 않는 것. 설치물, 빌드와 테스트 산출물, 판정자 테스트의 임시 트리.
const SKIPPED = new Set([
  "node_modules",
  ".next",
  "dist",
  "test-results",
  "playwright-report",
  "blob-report",
  "coverage",
]);

const [workRoot, candidate] = process.argv.slice(2);
if (workRoot === undefined || candidate === undefined || !CANDIDATES.includes(candidate)) {
  console.error(`사용: node setup.mjs <작업 루트> <${CANDIDATES.join("|")}>`);
  process.exit(2);
}

const ws = resolve(workRoot, candidate);
if (ws.startsWith(REPO)) {
  console.error(`작업 루트는 저장소 밖이어야 한다: ${ws}`);
  process.exit(2);
}
rmSync(ws, { recursive: true, force: true });

for (const file of [".gitignore", "openapi.json"]) {
  cpSync(join(REPO, file), join(ws, file));
}
cpSync(join(REPO, "web"), join(ws, "web"), {
  recursive: true,
  filter: (source) => !SKIPPED.has(basename(source)) && !basename(source).startsWith("judge-"),
});
for (const layer of LAYERS[candidate]) {
  cpSync(join(HERE, layer), join(ws, "web"), { recursive: true });
}
if (candidate === "preact-next") {
  for (const path of PREACT_TSX) {
    patch(
      join(ws, "web", "apps", "widget", path),
      (text) => `/** @jsxImportSource preact */\n${text}`,
    );
  }
}
if (candidate === "react-pkg") {
  for (const path of MOVED) {
    const to = join(ws, "web", "packages", "widget-ui", path);
    mkdirSync(dirname(to), { recursive: true });
    renameSync(join(ws, "web", "apps", "widget", path), to);
  }
}

patch(
  join(ws, "web", "packages", "api-client", "src", "index.ts"),
  (text) =>
    `${text}export { createWidgetClient, type WidgetClient, type WidgetPaths } from "./widget";\n`,
);

const WIDGET_PROJECT = `      {
        extends: true,
        test: {
          name: "widget",
          include: [WIDGET],
          environment: "jsdom",
        },
      },
`;
// Prettier 가 고치지 않을 모양으로 쓴다(verify 의 format 단계).
const NODE_PROJECT = `      {
        extends: true,
        test: { name: "node", exclude: [...configDefaults.exclude, PAGES, WIDGET] },
      },
`;
patch(join(ws, "web", "vitest.config.ts"), (text) =>
  replaceOnce(
    replaceOnce(
      replaceOnce(
        text,
        'const PAGES = "apps/admin/components/**/*.test.tsx";\n',
        'const PAGES = "apps/admin/components/**/*.test.tsx";\nconst WIDGET = "apps/widget/**/*.test.{ts,tsx}";\n',
      ),
      '      { extends: true, test: { name: "node", exclude: [...configDefaults.exclude, PAGES] } },\n',
      NODE_PROJECT,
    ),
    '          setupFiles: ["apps/admin/testing/setup.ts"],\n        },\n      },\n',
    `          setupFiles: ["apps/admin/testing/setup.ts"],\n        },\n      },\n${WIDGET_PROJECT}`,
  ),
);

run("git", ["init", "-q"], ws);
run("git", ["add", "-A"], ws);
run("pnpm", ["install"], join(ws, "web"));
console.log(`준비됨: ${ws}`);

function patch(path, change) {
  writeFileSync(path, change(readFileSync(path, "utf-8")));
}

function replaceOnce(text, anchor, replacement) {
  const count = text.split(anchor).length - 1;
  if (count !== 1) {
    throw new Error(`고칠 자리가 ${String(count)}개다(1이어야 한다): ${anchor}`);
  }
  return text.replace(anchor, replacement);
}

function run(command, args, cwd) {
  // 윈도우의 pnpm 은 .cmd 라 셸로 부른다. 인자는 이 파일의 상수뿐이다.
  const viaShell = process.platform === "win32" && command === "pnpm";
  const result = viaShell
    ? spawnSync([command, ...args].join(" "), { cwd, stdio: "inherit", shell: true })
    : spawnSync(command, args, { cwd, stdio: "inherit" });
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} 가 ${String(result.status)} 로 끝났다(${cwd})`);
  }
}

if (!existsSync(join(ws, "web", "node_modules"))) {
  throw new Error("node_modules 가 없다");
}
