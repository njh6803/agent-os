// design-system Storybook 프로브: 패키지 빌드(dist/)와 빌드 산출물이 판정자 범위에서 빠지는지 잰다.
//   node .scratch/design-system/probes/storybook/build.mjs <작업 루트>/storybook
// setup.mjs 가 지은 트리에서 돈다. 결과는 <작업 루트>/storybook/build.json 에도 쓴다. 뿌리 .gitignore 와 사례 파일은
// 제자리에 잠깐 쓰고 되돌린다.
//
// build    packages/ui 의 `pnpm run build`(tsc -p tsconfig.build.json 으로 JS 와 .d.ts, @tailwindcss/cli 로 CSS)의 성패와
//          걸린 시간, dist/ 의 파일과 크기, 생성 CSS 의 @property·테마 변수 수와 rem 의 자리
// theme    Tailwind 기본 테마의 유틸리티 이름(@source inline 으로 넣는다)이 비운 테마에서 무엇을 내는지와 그 CSS 의 rem
// ignore   빌드 산출물(packages/ui/dist/, packages/ui/storybook-static/)이 있을 때 verify 의 lint·format 과
//          eslint.config.test.ts 가 어떻게 되는지. 뿌리 .gitignore 를 네 모양으로 바꿔 본다
//            as-is      저장소 그대로(`/dist/` 는 뿌리에 앵커되어 있다)
//            anchored   `/web/packages/ui/dist/`, `/web/packages/ui/storybook-static/` 를 더한다
//            nested     뿌리는 그대로 두고 packages/ui/.gitignore 에 `dist/`, `storybook-static/` 를 둔다
//            bare       앵커 없는 `dist/`, `storybook-static/` 를 더한다
//          그리고 산출물 안에 vitest 의 기본 include(*.test.*, *.spec.*)에 걸리는 파일이 있는지, 저장소 그대로일 때
//          산출물의 어느 파일이 어느 ESLint 규칙에 걸리는지(outputsLint)

import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { gzipSync } from "node:zlib";

const ws = resolve(process.argv[2] ?? ".");
const web = join(ws, "web");
const ui = join(web, "packages", "ui");
const dist = join(ui, "dist");
const result = {};

// ---------- build ----------
rmSync(dist, { recursive: true, force: true });
let started = Date.now();
const build = pnpm(["run", "build"], ui);
result.build = { status: build.status, ms: Date.now() - started, tail: build.lines.slice(-4) };
const css = existsSync(join(dist, "ui.css")) ? readFileSync(join(dist, "ui.css"), "utf-8") : "";
result.dist = {
  files: filesUnder(dist).map((path) => ({
    file: relative(ui, path).replaceAll("\\", "/"),
    bytes: statSync(path).size,
  })),
  css: {
    bytes: Buffer.byteLength(css),
    gzip: gzipSync(css, { level: 9 }).length,
    banner: css.split("\n")[0],
    properties: (css.match(/@property /g) ?? []).length,
    themeVars: [
      ...new Set(css.match(/--(color|spacing|text|radius|shadow|font)[\w-]*(?=:)/g) ?? []),
    ],
    rem: remSites(css),
  },
  indexJs: existsSync(join(dist, "index.js"))
    ? readFileSync(join(dist, "index.js"), "utf-8")
    : null,
};

// ---------- theme: 기본 테마의 유틸리티 이름 ----------
const DEFAULT_THEME_CLASSES = [
  "text-xs",
  "text-sm",
  "text-base",
  "text-lg",
  "leading-tight",
  "leading-6",
  "tracking-wide",
  "font-bold",
  "font-medium",
  "font-sans",
  "font-mono",
  "p-4",
  "m-2",
  "gap-3",
  "size-8",
  "w-64",
  "h-10",
  "max-w-md",
  "min-h-screen",
  "container",
  "columns-2",
  "basis-1/2",
  "translate-x-4",
  "scroll-mt-4",
  "indent-4",
  "space-x-2",
  "rounded",
  "rounded-md",
  "rounded-lg",
  "shadow",
  "shadow-sm",
  "shadow-md",
  "inset-shadow-sm",
  "drop-shadow-md",
  "text-shadow-sm",
  "blur-sm",
  "backdrop-blur-sm",
  "ring",
  "ring-2",
  "outline-2",
  "underline-offset-2",
  "text-red-500",
  "bg-blue-500",
  "border-gray-200",
  "bg-accent",
  "duration-150",
  "ease-in",
  "animate-spin",
  "perspective-normal",
  "aspect-video",
  "sr-only",
];
const probeCss = join(ui, "src", "styles", "rem-probe.css");
const probeOut = join(ws, "rem-probe.out.css");
try {
  writeFileSync(
    probeCss,
    `@import "./theme.css";\n@source inline("${DEFAULT_THEME_CLASSES.join(" ")}");\n`,
  );
  const cli = pnpm(["exec", "tailwindcss", "-i", "src/styles/rem-probe.css", "-o", probeOut], ui);
  const text = existsSync(probeOut) ? readFileSync(probeOut, "utf-8") : "";
  // CSS 선택자(`.basis-1\/2`)를 만들고 그것을 정규식 글자로 다시 이스케이프한다.
  const selector = (name) => `.${name.replace(/[/:.]/g, (ch) => `\\${ch}`)}`;
  const literal = (text) => text.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&");
  const generated = DEFAULT_THEME_CLASSES.filter((name) =>
    new RegExp(`${literal(selector(name))}[\\s,:{]`).test(text),
  );
  result.defaultTheme = {
    status: cli.status,
    generated,
    missing: DEFAULT_THEME_CLASSES.filter((name) => !generated.includes(name)),
    rem: remSites(text),
  };
} finally {
  rmSync(probeCss, { force: true });
  rmSync(probeOut, { force: true });
}

// ---------- ignore ----------
if (!existsSync(join(ui, "storybook-static", "index.json"))) {
  pnpm(["run", "build-storybook"], ui);
}
const outputs = [dist, join(ui, "storybook-static")];
result.testLikeFiles = outputs.flatMap((dir) =>
  filesUnder(dir)
    .filter((path) => /\.(test|spec)\.[cm]?[jt]sx?$/.test(path))
    .map((path) => relative(web, path).replaceAll("\\", "/")),
);
result.outputCounts = Object.fromEntries(
  outputs.map((dir) => [relative(web, dir).replaceAll("\\", "/"), filesUnder(dir).length]),
);

const gitignore = join(ws, ".gitignore");
const nested = join(ui, ".gitignore");
const original = readFileSync(gitignore, "utf-8");
const VARIANTS = {
  "as-is": { root: original, nested: null },
  anchored: {
    root: `${original}/web/packages/ui/dist/\n/web/packages/ui/storybook-static/\n`,
    nested: null,
  },
  nested: { root: original, nested: "dist/\nstorybook-static/\n" },
  bare: { root: `${original}dist/\nstorybook-static/\n`, nested: null },
};
result.ignore = {};
try {
  for (const [name, variant] of Object.entries(VARIANTS)) {
    writeFileSync(gitignore, variant.root);
    if (variant.nested === null) {
      rmSync(nested, { force: true });
    } else {
      writeFileSync(nested, variant.nested);
    }
    started = Date.now();
    const lint = pnpm(["run", "lint"], web);
    const format = pnpm(["run", "format"], web);
    const guard = node(
      [
        join(web, "node_modules", "vitest", "vitest.mjs"),
        "run",
        "--project",
        "node",
        "eslint.config.test.ts",
        "-t",
        "판정 범위",
      ],
      web,
    );
    const gitView = spawnSync(
      "git",
      [
        "check-ignore",
        "-v",
        "web/packages/ui/dist/index.js",
        "web/packages/ui/storybook-static/index.json",
      ],
      { cwd: ws, encoding: "utf-8" },
    );
    result.ignore[name] = {
      lint: summarize(lint, /packages[\\/]ui[\\/](dist|storybook-static)/),
      format: summarize(format, /packages[\\/]ui[\\/](dist|storybook-static)/),
      eslintConfigTest: {
        status: guard.status,
        lines: guard.lines
          .filter((line) => /✓|×|Tests|FAIL|AssertionError|expected/.test(line))
          .slice(0, 12),
      },
      git: gitView.stdout.split(/\r?\n/).filter(Boolean),
      ms: Date.now() - started,
    };
  }
} finally {
  writeFileSync(gitignore, original);
  rmSync(nested, { force: true });
}

// 저장소 그대로의 .gitignore 에서 산출물만 린트해 어느 파일이 어느 규칙에 걸리는지 남긴다.
const outputsLint = spawnSync(
  process.execPath,
  [
    join(web, "node_modules", "eslint", "bin", "eslint.js"),
    "--format",
    "json",
    ...outputs.map((dir) => relative(web, dir)),
  ],
  { cwd: web, encoding: "utf-8", maxBuffer: 1 << 28 },
);
result.outputsLint = JSON.parse(outputsLint.stdout)
  .filter((file) => file.messages.length > 0)
  .map((file) => ({
    file: relative(web, file.filePath).replaceAll("\\", "/"),
    count: file.messages.length,
    rules: [...new Set(file.messages.map((message) => String(message.ruleId)))],
    first: file.messages[0].message.split("\n")[0].slice(0, 120),
  }));

writeFileSync(join(ws, "build.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));

function summarize(run, pattern) {
  const hits = run.lines.filter((line) => pattern.test(line));
  return {
    status: run.status,
    outputLines: hits.length,
    sample: hits.slice(0, 4),
    tail: run.lines.slice(-2),
  };
}

function remSites(text) {
  return [...text.matchAll(/([^{};]*)\{([^{}]*?(-?\d*\.?\d+rem\b)[^{}]*)\}/g)].map((match) => ({
    selector: match[1].trim().slice(-80),
    declaration: match[2]
      .split(";")
      .filter((part) => /\d*\.?\d+rem\b/.test(part))
      .map((part) => part.trim()),
  }));
}

function filesUnder(dir) {
  if (!existsSync(dir)) {
    return [];
  }
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() ? filesUnder(join(dir, entry.name)) : [join(dir, entry.name)],
  );
}

function lines(text) {
  return text
    .replace(/\u001b\[[\d;]*m/g, "")
    .split(/\r?\n/)
    .map((line) => line.trimEnd())
    .filter((line) => line.trim() !== "");
}

function pnpm(args, cwd) {
  // 윈도우의 pnpm 은 .cmd 라 셸로 부른다. 인자는 이 파일의 상수와 경로뿐이다.
  const run = spawnSync(`pnpm ${args.join(" ")}`, {
    cwd,
    encoding: "utf-8",
    shell: true,
    maxBuffer: 1 << 28,
    env: { ...process.env, STORYBOOK_DISABLE_TELEMETRY: "1" },
  });
  return { status: run.status, lines: lines(`${run.stdout}${run.stderr}`) };
}

function node(args, cwd) {
  const run = spawnSync(process.execPath, args, { cwd, encoding: "utf-8", maxBuffer: 1 << 28 });
  return { status: run.status, lines: lines(`${run.stdout}${run.stderr}`) };
}
