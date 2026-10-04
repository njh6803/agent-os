// web-widget 위젯 스택 프로브: 위젯을 빌드하고 산출물의 크기를 잰다. 빌드 산출물이 판정자와 Prettier 를 지나는지도 본다.
//   node .scratch/web-widget/probes/widget_stack/measure.mjs <작업 루트>/<후보>
// setup.mjs 가 지은 트리를 받는다. 빌드는 셋이다.
//   element  vite build --mode element  (1) script 하나로 커스텀 요소를 정의하는 IIFE 번들. dist/element/
//   page     vite build --mode page     (2) iframe 용 정적 페이지(Next 를 쓰지 않을 때의 견줌). dist/page/
//   next     next build                 (2) iframe 페이지를 Next 앱이 서빙할 때. next.config.ts 가 있는 후보만
// 크기는 파일 바이트(min)와 gzip(zlib 9단계)이다. Next 페이지는 미리 그린 index.html 과 그것이 싣는 script·stylesheet 의
// 합이다(noModule 폴리필은 뺀다).
// 끝에 eslint(verify 의 lint 인자 그대로)와 prettier --check 를 apps/widget 에 친다. dist/ 는 저장소 .gitignore 가 빼지
// 않는 자리라 빌드 뒤에 판정 범위에 드는지 본다. 결과는 <작업 루트>/<후보>/measure.json 에도 쓴다.

import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve, sep } from "node:path";
import { gzipSync } from "node:zlib";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const widget = join(web, "apps", "widget");
const fromWidget = createRequire(join(widget, "package.json"));
const fromWeb = createRequire(join(web, "package.json"));

const result = { candidate: relative(dirname(ws), ws), builds: {}, sizes: {}, afterBuild: {} };

function run(label, bin, args, cwd, env = {}) {
  const started = Date.now();
  const proc = spawnSync(process.execPath, [bin, ...args], {
    cwd,
    encoding: "utf-8",
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1", ...env },
  });
  const output = `${proc.stdout}${proc.stderr}`;
  result.builds[label] = {
    status: proc.status,
    ms: Date.now() - started,
    tail: output.split(/\r?\n/).filter(Boolean).slice(-12),
  };
  return proc.status === 0;
}

function sizeOf(path) {
  const bytes = readFileSync(path);
  return { min: bytes.length, gzip: gzipSync(bytes, { level: 9 }).length };
}

function filesUnder(dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...filesUnder(path));
    } else {
      out.push(path);
    }
  }
  return out.sort();
}

function sum(files) {
  const each = Object.fromEntries(files.map(([name, path]) => [name, sizeOf(path)]));
  const total = Object.values(each).reduce(
    (acc, size) => ({ min: acc.min + size.min, gzip: acc.gzip + size.gzip }),
    { min: 0, gzip: 0 },
  );
  return { total, files: each };
}

function distSizes(dir) {
  return sum(filesUnder(dir).map((path) => [relative(dir, path).split(sep).join("/"), path]));
}

const vite = join(dirname(fromWidget.resolve("vite/package.json")), "bin", "vite.js");
if (run("element", vite, ["build", "--mode", "element"], widget)) {
  result.sizes.element = distSizes(join(widget, "dist", "element"));
}
if (run("page", vite, ["build", "--mode", "page"], widget)) {
  result.sizes.page = distSizes(join(widget, "dist", "page"));
}

if (existsSync(join(widget, "next.config.ts"))) {
  const next = join(dirname(fromWidget.resolve("next/package.json")), "dist", "bin", "next");
  if (run("next", next, ["build"], widget)) {
    const html = join(widget, ".next", "server", "app", "index.html");
    const text = readFileSync(html, "utf-8");
    // noModule script(폴리필)는 모듈을 아는 브라우저가 받지 않으므로 뺀다. 동적 import 조각은 HTML 에 없어 여기
    // 들지 않는다. 브라우저가 실제로 받은 바이트는 shadow.mjs 의 loaded 다.
    const tags = [...text.matchAll(/<(?:script|link)\b[^>]*>/g)]
      .map((match) => match[0])
      .filter((tag) => !/\bnoModule\b/i.test(tag));
    const assets = [
      ...new Set(
        tags.flatMap((tag) => {
          const found = /(?:src|href)="\/_next\/(static\/[^"]+\.(?:js|css))"/.exec(tag);
          return found === null ? [] : [found[1]];
        }),
      ),
    ];
    result.sizes.next = sum([
      ["index.html", html],
      ...assets.map((asset) => [asset, join(widget, ".next", asset)]),
    ]);
  }
}

// 빌드 산출물이 남은 채로 verify 의 lint 와 format 이 apps/widget 을 어떻게 보는지.
const eslint = join(dirname(fromWeb.resolve("eslint/package.json")), "bin", "eslint.js");
const lint = spawnSync(
  process.execPath,
  [eslint, "--max-warnings", "0", "--format", "json", "apps/widget"],
  { cwd: web, encoding: "utf-8", maxBuffer: 1 << 28 },
);
const reports = lint.stdout.trim() === "" ? [] : JSON.parse(lint.stdout);
const problems = reports.filter((report) => report.messages.length > 0);
result.afterBuild.eslint = {
  status: lint.status,
  files: problems.map((report) => ({
    file: relative(web, report.filePath).split(sep).join("/"),
    count: report.messages.length,
    rules: [...new Set(report.messages.map((message) => message.ruleId ?? message.message))].slice(
      0,
      6,
    ),
  })),
};
const prettier = join(dirname(fromWeb.resolve("prettier/package.json")), "bin", "prettier.cjs");
const format = spawnSync(
  process.execPath,
  [
    prettier,
    "--check",
    "apps/widget",
    "--ignore-path",
    "../.gitignore",
    "--ignore-path",
    ".prettierignore",
  ],
  { cwd: web, encoding: "utf-8" },
);
result.afterBuild.prettier = {
  status: format.status,
  flagged: `${format.stdout}${format.stderr}`
    .replace(/\u001b\[\d+m/g, "")
    .split(/\r?\n/)
    .filter((line) => line.includes("[warn]") && !line.includes("Code style issues"))
    .map((line) => line.replace(/.*\[warn\]\s*/, "")),
};

writeFileSync(join(ws, "measure.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
const failed = Object.entries(result.builds).filter(([, build]) => build.status !== 0);
process.exitCode = failed.length > 0 ? 1 : 0;
