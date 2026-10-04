// web-widget 위젯 스타일 프로브: React 위젯에 Tailwind(와 lucide-react 아이콘)를 얹은 임시 워크스페이스를 짓는다.
//   node .scratch/web-widget/probes/widget_tailwind/setup.mjs <작업 루트>
//
// 차례
//   1. widget_stack/setup.mjs 로 React 후보 트리를 <작업 루트>/react 에 짓는다(저장소 web/ 사본, 설치까지)
//   2. 덮어쓰기 전에 그 트리에서 element 번들을 한 번 빌드해 크기를 baseline.json 에 남긴다(Tailwind 도 아이콘도
//      없는 기준. widget_stack 의 react 후보와 같은 것이다). 빌드 산출물은 지운다
//   3. 그 트리의 락과 pnpm-workspace.yaml 을 *.before.* 로 떠 둔다(deps.mjs 가 견준다)
//   4. tailwind/ 를 web/ 위에 덮어쓰고, 더는 쓰지 않는 lib/styles.ts(손으로 쓴 CSS 글자)를 지운다
//   5. pnpm install(npm 레지스트리에 닿는다)과 git add -A(eslint.config.test.ts 가 추적 파일로 판정 범위를 잰다)
// 저장소의 web/ 은 읽기만 한다. 작업 루트는 저장소 밖이어야 한다.

import { spawnSync } from "node:child_process";
import {
  copyFileSync,
  cpSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  utimesSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve } from "node:path";
import { gzipSync } from "node:zlib";

const HERE = import.meta.dirname;
const REPO = resolve(HERE, "..", "..", "..", "..");
const STACK_SETUP = join(HERE, "..", "widget_stack", "setup.mjs");

const [workRoot] = process.argv.slice(2);
if (workRoot === undefined) {
  console.error("사용: node setup.mjs <작업 루트>");
  process.exit(2);
}
const root = resolve(workRoot);
if (root.startsWith(REPO)) {
  console.error(`작업 루트는 저장소 밖이어야 한다: ${root}`);
  process.exit(2);
}

run(process.execPath, [STACK_SETUP, root, "react"], REPO);
const ws = join(root, "react");
const web = join(ws, "web");
const widget = join(web, "apps", "widget");

// 2. 기준 번들
const vite = join(
  dirname(createRequire(join(widget, "package.json")).resolve("vite/package.json")),
  "bin",
  "vite.js",
);
run(process.execPath, [vite, "build", "--mode", "element"], widget);
const bundle = readFileSync(join(widget, "dist", "element", "widget.js"));
writeFileSync(
  join(ws, "baseline.json"),
  `${JSON.stringify(
    {
      what: "widget_stack 의 react 후보 element 번들(Tailwind·아이콘 없음, 손으로 쓴 CSS 글자)",
      min: bundle.length,
      gzip: gzipSync(bundle, { level: 9 }).length,
      cssChars: statSync(join(widget, "lib", "styles.ts")).size,
    },
    null,
    2,
  )}\n`,
);
rmSync(join(widget, "dist"), { recursive: true, force: true });

// 3. 견줄 기준
copyFileSync(join(web, "pnpm-lock.yaml"), join(ws, "pnpm-lock.before.yaml"));
copyFileSync(join(web, "pnpm-workspace.yaml"), join(ws, "pnpm-workspace.before.yaml"));

// 4. 덮어쓰기. 윈도우의 복사는 수정 시각을 원본 그대로 둔다. pnpm 11 은 package.json 이 마지막 검사
// (node_modules/.pnpm-workspace-state-v1.json)보다 오래됐으면 "Already up to date" 로 설치를 건너뛰므로 시각을 지금으로 바꾼다.
cpSync(join(HERE, "tailwind"), web, { recursive: true });
const now = new Date();
for (const path of filesUnder(join(HERE, "tailwind"))) {
  utimesSync(join(web, relative(join(HERE, "tailwind"), path)), now, now);
}
rmSync(join(widget, "lib", "styles.ts"));

// 5. 설치
const install = run("pnpm", ["install"], web);
writeFileSync(join(ws, "install.log"), install);
run("git", ["add", "-A"], ws);
console.log(`준비됨: ${ws}`);

function filesUnder(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() ? filesUnder(join(dir, entry.name)) : [join(dir, entry.name)],
  );
}

function run(command, args, cwd) {
  // 윈도우의 pnpm 은 .cmd 라 셸로 부른다. 인자는 이 파일의 상수와 경로뿐이다.
  const viaShell = process.platform === "win32" && command === "pnpm";
  const result = viaShell
    ? spawnSync([command, ...args].join(" "), { cwd, encoding: "utf-8", shell: true })
    : spawnSync(command, args, { cwd, encoding: "utf-8" });
  const output = `${result.stdout ?? ""}${result.stderr ?? ""}`;
  process.stdout.write(output);
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} 가 ${String(result.status)} 로 끝났다(${cwd})`);
  }
  return output;
}
