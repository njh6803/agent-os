// design-system 디자인 토큰 프로브: storybook 프로브의 작업 루트 위에 디자인 파일 v3 의 디자인 토큰(두 층), 테마
// 글꼴, 판정 스토리를 얹고 글꼴 패키지와 관리 화면의 Tailwind 를 설치한다.
//   node .scratch/design-system/probes/storybook/setup.mjs <작업 루트>     (먼저. web/ 사본과 Storybook 설치)
//   node .scratch/design-system/probes/tokens/setup.mjs <작업 루트>
//
// 하는 일(저장소는 읽기만 한다. 작업 루트는 저장소 밖이어야 한다)
//   1. ui/ 를 <작업 루트>/storybook/web 위에 덮어쓰고 storybook 프로브의 Switch 표본을 지운다
//   2. 설치(npm 레지스트리에 닿는다). packages/ui 의 dependencies 에 글꼴 셋(@fontsource/noto-sans-kr,
//      @fontsource/jetbrains-mono, @ibm/plex-mono), apps/admin 에 @agent-os/ui(workspace)와 @tailwindcss/postcss,
//      tailwindcss 를 더하고, pnpm-workspace.yaml 의 allowBuilds 에 `"@ibm/plex-mono": false` 를 더해 pnpm install
//      → pnpm-lock.tokens.yaml. 설치가 pnpm-workspace.yaml 을 더 바꾸면 멈춘다(유예를 풀지 않는다)
//   3. 생성: design.mjs 로 디자인 파일을 읽어 packages/ui/src/styles/ 에 theme.css(디자인 토큰), fonts.css(글꼴),
//      design-tokens.ts(스토리의 기대값)를 쓴다
//   4. 관리 화면: postcss.config.mjs, app/globals.css(@agent-os/ui/theme.css 를 import), layout.tsx 의 import
//   5. 쓴 파일을 Prettier 로 맞추고(verify 의 format 단계) git add
//
// theme.css 의 모양(이것이 재는 대상이다)
//   - @theme 에 길이·글자·모서리·기준 폭(값이 글자 그대로인 것), @theme inline 에 쓰임새 토큰·글꼴·그림자처럼 테마나
//     모드마다 바뀌는 CSS 변수를 읽는 것. inline 이라 유틸리티가 `var(--bg)` 를 바로 읽는다
//   - 원색 토큰(--gray-500 등)과 쓰임새 토큰(--bg 등)은 @theme 밖의 CSS 변수다. 원색은 테마마다, 쓰임새는 테마를 다는
//     요소마다 다시 선언한다. 사용자 정의 속성의 var() 는 선언한 요소에서 풀리므로, 쓰임새를 :root 에만 두면 안쪽
//     요소의 data-theme 이 바꾼 원색을 다시 읽지 않는다
//   - 고르는 것: data-theme(테마 키), data-mode(light, dark). 둘 다 같은 요소에 둔다. 모드가 없으면
//     prefers-color-scheme 을 따른다. 속성이 없는 문서와 호스트는 먹(muk)이다. shadow 안에서는 :host(...) 로 호스트를 본다

import { spawnSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  readdirSync,
  readFileSync,
  rmSync,
  utimesSync,
  writeFileSync,
  copyFileSync,
} from "node:fs";
import { join, relative, resolve } from "node:path";
import { expectedSemantic, readDesign, semanticNames } from "./design.mjs";

const HERE = import.meta.dirname;
const REPO = resolve(HERE, "..", "..", "..", "..");
const OVERLAY = join(HERE, "ui");

const UI_DEPS = {
  "@fontsource/jetbrains-mono": "5.3.0",
  "@fontsource/noto-sans-kr": "5.3.0",
  "@ibm/plex-mono": "2.5.0",
};
const ADMIN_DEPS = { "@agent-os/ui": "workspace:*" };
const ADMIN_DEV_DEPS = { "@tailwindcss/postcss": "^4.3.3", tailwindcss: "^4.3.3" };

// 디자인 파일이 재는 짝(대응표에서 기준이 있는 열과 상태용 토큰)에, 컴포넌트가 실제로 쓰는데 디자인 파일이 재지 않은
// 짝(알림 제목과 그 안 버튼의 포커스 링, 진행 막대와 트랙)을 더했다. 알림에 성공 톤은 없어 `success-tint` 위의 제목
// 짝은 두지 않는다(2026-10-06 명세 리뷰).
const CONTRAST_PAIRS = [
  ...["text", "muted", "accent", "danger", "warning", "success", "info"].flatMap((name) => [
    [name, "bg", 4.5],
    [name, "raised", 4.5],
  ]),
  ...["border", "focus"].flatMap((name) => [
    [name, "bg", 3],
    [name, "raised", 3],
  ]),
  ["on-accent", "accent", 4.5],
  ["text", "tint", 4.5],
  ["muted", "tint", 4.5],
  ["text", "tint-hover", 4.5],
  ["text", "tint-press", 4.5],
  ["on-accent", "accent-hover", 4.5],
  ["on-accent", "accent-press", 4.5],
  ["border-hover", "bg", 3],
  ["border-hover", "raised", 3],
  ["danger", "danger-tint", 4.5],
  ["muted", "danger-tint", 4.5],
  ["danger", "danger-tint-press", 4.5],
  ["warning", "warning-tint", 4.5],
  ["muted", "warning-tint", 4.5],
  ["success", "success-tint", 4.5],
  ["info", "info-tint", 4.5],
  ["muted", "info-tint", 4.5],
  ["text", "danger-tint", 4.5],
  ["text", "warning-tint", 4.5],
  ["text", "info-tint", 4.5],
  ["focus", "danger-tint", 3],
  ["focus", "warning-tint", 3],
  ["focus", "info-tint", 3],
  ["accent", "tint", 3],
  ["danger", "tint", 3],
];

// 디자인 파일에 없는 움직임과 부품 치수(명세가 정했다). 기본 테마를 비우면 Tailwind 의 `animate-spin` 과 그 keyframes
// 도 사라지므로 우리 값으로 다시 둔다. 부품 치수는 임의값을 쓰지 않으려고 이름 있는 간격으로 둔다.
const MOTION = [
  ["--animate-spin", "spin 1s linear infinite"],
  ["--animate-progress", "progress 1.2s ease-in-out infinite"],
];
const KEYFRAMES = [
  "  @keyframes spin {",
  "    to {",
  "      transform: rotate(360deg);",
  "    }",
  "  }",
  "  @keyframes progress {",
  "    from {",
  "      left: -30%;",
  "    }",
  "    to {",
  "      left: 100%;",
  "    }",
  "  }",
];
// 간격 0 도 둔다. `--spacing` 을 비우면 `inset-y-0` 같은 0 도 규칙을 만들지 않았다(2026-10-06 Motion 스토리).
const PART_SIZES = [
  ["--spacing-0", "0px"],
  ["--spacing-switch-w", "36px"],
  ["--spacing-switch-h", "20px"],
  ["--spacing-row-touch", "48px"],
  ["--spacing-progress", "6px"],
  ["--spacing-field-multi", "88px"],
];

const FONT_FACES = [
  ["Noto Sans KR", 400, "가"],
  ["Noto Sans KR", 500, "가"],
  ["Noto Sans KR", 600, "가"],
  ["JetBrains Mono", 400, "a"],
  ["JetBrains Mono", 500, "a"],
  ["IBM Plex Mono", 400, "a"],
  ["IBM Plex Mono", 500, "a"],
];

const [workRoot] = process.argv.slice(2);
if (workRoot === undefined) {
  console.error("사용: node setup.mjs <작업 루트>");
  process.exit(2);
}
const ws = resolve(workRoot, "storybook");
const web = join(ws, "web");
if (ws.startsWith(REPO)) {
  console.error(`작업 루트는 저장소 밖이어야 한다: ${ws}`);
  process.exit(2);
}
if (!existsSync(join(web, "node_modules", ".bin", "storybook"))) {
  console.error(`storybook 프로브의 setup.mjs 를 먼저 돌린다: ${web}`);
  process.exit(2);
}
const ui = join(web, "packages", "ui");
const admin = join(web, "apps", "admin");

// 1. 덮어쓰기
cpSync(OVERLAY, web, { recursive: true });
const now = new Date();
for (const path of filesUnder(OVERLAY)) {
  utimesSync(join(web, relative(OVERLAY, path)), now, now);
}
for (const stale of ["Switch.tsx", "Switch.stories.tsx"]) {
  rmSync(join(ui, "src", "components", "atoms", stale), { force: true });
}

// 2. 설치. @ibm/plex-mono 2.5.0 은 postinstall 로 IBM 원격 측정(`ibmtelemetry --config=telemetry.yml`)을 돌리고
// pnpm 11 은 정하지 않은 빌드 스크립트에서 ERR_PNPM_IGNORED_BUILDS 로 멈춘다(2026-10-06 이 프로브의 첫 실행). 돌리지
// 않는 쪽(false)을 미리 적는다. 그 실패가 써 둔 자리 줄(`set this to true or false`)이 있으면 지운다.
const workspacePath = join(web, "pnpm-workspace.yaml");
const IBM_BUILD = '  "@ibm/plex-mono": false\n';
const cleaned = readFileSync(workspacePath, "utf-8")
  .split("\n")
  .filter((line) => !line.includes("set this to true or false"))
  .join("\n");
writeFileSync(workspacePath, cleaned.includes(IBM_BUILD) ? cleaned : `${cleaned}${IBM_BUILD}`);
const workspaceBefore = readFileSync(workspacePath, "utf-8");
addDeps(join(ui, "package.json"), "dependencies", UI_DEPS);
addDeps(join(admin, "package.json"), "dependencies", ADMIN_DEPS);
addDeps(join(admin, "package.json"), "devDependencies", ADMIN_DEV_DEPS);
writeFileSync(join(ws, "install-tokens.log"), timed("pnpm", ["install"], web));
if (readFileSync(join(web, "pnpm-workspace.yaml"), "utf-8") !== workspaceBefore) {
  throw new Error("설치가 pnpm-workspace.yaml 을 바꿨다. 유예를 풀지 않는다. 판을 내려 다시 잰다");
}
copyFileSync(join(web, "pnpm-lock.yaml"), join(ws, "pnpm-lock.tokens.yaml"));

// 3. 생성
const design = readDesign();
const styles = join(ui, "src", "styles");
writeFileSync(join(styles, "theme.css"), themeCss(design.tokens));
writeFileSync(join(styles, "fonts.css"), fontsCss());
writeFileSync(join(styles, "design-tokens.ts"), designTokensTs(design.tokens));

// 4. 관리 화면
writeFileSync(
  join(admin, "postcss.config.mjs"),
  '// 관리 화면의 Tailwind(프로브). 디자인 시스템 패키지의 CSS 원본을 globals.css 가 import 한다.\nexport default { plugins: { "@tailwindcss/postcss": {} } };\n',
);
writeFileSync(join(admin, "app", "globals.css"), '@import "@agent-os/ui/theme.css";\n');
patch(join(admin, "app", "layout.tsx"), (text) =>
  text.includes('import "./globals.css";')
    ? text
    : replaceOnce(text, 'import type { ReactNode } from "react";\n', 'import type { ReactNode } from "react";\nimport "./globals.css";\n'),
);

// 5. 모양과 git
const written = [
  "packages/ui/src/styles/theme.css",
  "packages/ui/src/styles/fonts.css",
  "packages/ui/src/styles/design-tokens.ts",
  "packages/ui/package.json",
  "apps/admin/package.json",
  "apps/admin/postcss.config.mjs",
  "apps/admin/app/globals.css",
  ...filesUnder(OVERLAY).map((path) => relative(OVERLAY, path).replaceAll("\\", "/")),
];
run("pnpm", ["exec", "prettier", "--write", ...written], web);
run("git", ["add", "-A"], ws);
console.log(`준비됨: ${ws}`);

// ---------------------------------------------------------------------------------------------------------------

function themeCss(tokens) {
  const { size, themes } = tokens;
  const keys = Object.keys(themes);
  const muk = themes.muk;
  const semantic = semanticNames(tokens);
  const decl = (entries) => entries.map(([name, value]) => `    ${name}: ${value};`).join("\n");
  const rule = (selectors, body) => `  ${selectors.join(",\n  ")} {\n${body}\n  }`;
  const both = (selector) => [selector, `:host(${selector})`];
  const primitives = (theme) =>
    decl([
      ...Object.entries(theme.primitive).flatMap(([family, steps]) =>
        Object.entries(steps).map(([step, hex]) => [`--${family}-${step}`, hex.toUpperCase()]),
      ),
      ["--sans", `"${theme.font.sans}", system-ui, sans-serif`],
      ["--mono", `"${theme.font.mono}", ui-monospace, monospace`],
      ["--weight-mid", String(theme.font.weight.mid)],
    ]);
  const mapping = (map, mode) =>
    decl([
      ["color-scheme", mode],
      ...semantic.filter((name) => name in map).map((name) => [`--${name}`, `var(--${map[name]})`]),
      ...(mode === "light"
        ? [["--shadow-color", "color-mix(in srgb, var(--gray-900) 14%, transparent)"]]
        : [["--shadow-color", "color-mix(in srgb, color-mix(in srgb, var(--gray-950), black) 70%, transparent)"]]),
    ]);
  const overrides = (theme, mode) => {
    const base = muk.semantic[mode];
    return Object.fromEntries(
      Object.entries(theme.semantic[mode]).filter(([name, value]) => name !== "shadow" && base[name] !== value),
    );
  };
  const text = Object.entries(size.text).flatMap(([name, t]) => [
    [`--text-${name}`, `${String(t.size)}px`],
    [`--text-${name}--line-height`, `${String(t.lineHeight)}px`],
    ...(t.weight === "strong" ? [[`--text-${name}--font-weight`, "600"]] : []),
  ]);
  const mid = Object.entries(size.text)
    .filter(([, t]) => t.weight === "mid")
    .map(([name]) => [`--text-${name}--font-weight`, "var(--weight-mid)"]);
  const lines = [
    "/*",
    " * 생성물(.scratch/design-system/probes/tokens/setup.mjs). 디자인 파일 v3 의 디자인 토큰을 두 층으로 옮긴 프로브 표본.",
    " */",
    '@import "tailwindcss" source(none);',
    '@import "./fonts.css";',
    // 스토리(src/styles/Tokens.stories.tsx)의 클래스까지 훑는다. "../components" 로 두자 그 파일의 flex·flex-col 이
    // CSS 를 만들지 않았고 classesWithoutRules 가 잡았다(2026-10-06 이 프로브의 첫 실행).
    '@source "..";',
    "",
    "@theme {",
    "  --*: initial;",
    decl([
      ...text,
      ...Object.entries(size.space).map(([name, px]) => [`--spacing-${name}`, `${String(px)}px`]),
      ...Object.entries(size.control).map(([name, px]) => [`--spacing-control-${name}`, `${String(px)}px`]),
      ...Object.entries(size.icon).map(([name, px]) => [`--spacing-icon-${name}`, `${String(px)}px`]),
      ...Object.entries(size.radius).map(([name, px]) => [`--radius-${name}`, `${String(px)}px`]),
      ["--font-weight-regular", "400"],
      ["--font-weight-strong", "600"],
      ["--breakpoint-wide", `${String(size.breakpoint.admin.minWidth)}px`],
      ["--container-wide", `${String(size.breakpoint.widget.minWidth)}px`],
      ...PART_SIZES,
      ...MOTION,
    ]).replaceAll("    ", "  "),
    ...KEYFRAMES,
    "}",
    "",
    "@theme inline {",
    decl([
      ...semantic.map((name) => [`--color-${name}`, `var(--${name})`]),
      ["--font-sans", "var(--sans)"],
      ["--font-mono", "var(--mono)"],
      ["--default-font-family", "var(--sans)"],
      ["--default-mono-font-family", "var(--mono)"],
      ["--font-weight-mid", "var(--weight-mid)"],
      ...mid,
      ...Object.entries(size.shadow)
        .filter(([, s]) => s !== null)
        .map(([name, s]) => [`--shadow-${name}`, `0 ${String(s.y)}px ${String(s.blur)}px var(--shadow-color)`]),
    ]).replaceAll("    ", "  "),
    "}",
    "",
    "@layer theme {",
    rule([":root", ":host", ...both('[data-theme="muk"]')], primitives(muk)),
    ...keys.filter((key) => key !== "muk").map((key) => rule(both(`[data-theme="${key}"]`), primitives(themes[key]))),
    rule([":root", ":host", "[data-theme]", "[data-mode]"], mapping(muk.semantic.light, "light")),
    rule(both('[data-mode="dark"]'), mapping(muk.semantic.dark, "dark")),
    "  @media (prefers-color-scheme: dark) {",
    rule([":root:not([data-mode])", ":host(:not([data-mode]))", "[data-theme]:not([data-mode])"], mapping(muk.semantic.dark, "dark")),
    "  }",
    ...keys.flatMap((key) =>
      ["light", "dark"].flatMap((mode) => {
        const changed = overrides(themes[key], mode);
        if (Object.keys(changed).length === 0) {
          return [];
        }
        const body = decl(Object.entries(changed).map(([name, value]) => [`--${name}`, `var(--${value})`]));
        return [
          rule(both(`[data-theme="${key}"][data-mode="${mode}"]`), body),
          `  @media (prefers-color-scheme: ${mode}) {`,
          rule(both(`[data-theme="${key}"]:not([data-mode])`), body),
          "  }",
        ];
      }),
    ),
    "}",
    "",
    "@layer base {",
    "  html,",
    "  :host {",
    "    background-color: var(--bg);",
    "    color: var(--text);",
    "  }",
    "}",
    "",
  ];
  return lines.join("\n");
}

function fontsCss() {
  // IBM 의 CSS 는 `local("IBM Plex Mono")` 를 원본 앞에 두어 깔린 기계마다 다르게 그린다. 저자가 낸 split 파일만
  // local() 없이 다시 선언한다(굵기 400·500, 바른 모양). url 은 이 파일에서 패키지 폴더로 가는 상대 경로다.
  const ibmCss = readFileSync(join(ui, "node_modules", "@ibm", "plex-mono", "css", "ibm-plex-mono-all.css"), "utf-8");
  const blocks = [...ibmCss.matchAll(/@font-face\s*\{[^}]*\}/g)].map((m) => m[0]);
  const split = blocks.filter(
    (block) =>
      /font-style:\s*normal/.test(block) &&
      /font-weight:\s*(400|500)\b/.test(block) &&
      /unicode-range/.test(block) &&
      /fonts\/split\/woff2\//.test(block),
  );
  const ibm = split.map((block) => {
    const weight = /font-weight:\s*(\d+)/.exec(block)[1];
    const file = /url\("?\.\.\/(fonts\/split\/woff2\/[^")]+)"?\)/.exec(block)[1];
    const range = /unicode-range:\s*([^;]+);/.exec(block)[1].trim();
    return [
      "@font-face {",
      '  font-family: "IBM Plex Mono";',
      "  font-style: normal;",
      `  font-weight: ${weight};`,
      "  font-display: swap;",
      `  src: url("../../node_modules/@ibm/plex-mono/${file}") format("woff2");`,
      `  unicode-range: ${range};`,
      "}",
    ].join("\n");
  });
  return [
    "/* 생성물(.scratch/design-system/probes/tokens/setup.mjs). 테마 다섯이 쓰는 글꼴. */",
    '@import "@fontsource/noto-sans-kr/400.css";',
    '@import "@fontsource/noto-sans-kr/500.css";',
    '@import "@fontsource/noto-sans-kr/600.css";',
    '@import "@fontsource/jetbrains-mono/400.css";',
    '@import "@fontsource/jetbrains-mono/500.css";',
    "",
    ...ibm,
    "",
  ].join("\n");
}

function designTokensTs(tokens) {
  const { themes } = tokens;
  const semantic = semanticNames(tokens);
  const expected = Object.fromEntries(
    Object.keys(themes).map((key) => [
      key,
      Object.fromEntries(["light", "dark"].map((mode) => [mode, expectedSemantic(tokens, key, mode)])),
    ]),
  );
  return [
    "// 생성물(.scratch/design-system/probes/tokens/setup.mjs). 디자인 파일 v3 가 그린 값이고 스토리의 기대값이다.",
    `export const THEMES = ${JSON.stringify(Object.keys(themes))} as const;`,
    "export type Theme = (typeof THEMES)[number];",
    'export const MODES = ["light", "dark"] as const;',
    `export const SEMANTIC = ${JSON.stringify(semantic)} as const;`,
    `export const EXPECTED = ${JSON.stringify(expected)} as const;`,
    `export const CONTRAST_PAIRS = ${JSON.stringify(CONTRAST_PAIRS)} as const;`,
    `export const FONT_FACES = ${JSON.stringify(FONT_FACES)} as const;`,
    "",
  ].join("\n");
}

function addDeps(path, field, deps) {
  const manifest = JSON.parse(readFileSync(path, "utf-8"));
  const merged = { ...manifest[field], ...deps };
  manifest[field] = Object.fromEntries(
    Object.keys(merged)
      .sort()
      .map((name) => [name, merged[name]]),
  );
  writeFileSync(path, `${JSON.stringify(manifest, null, 2)}\n`);
  utimesSync(path, new Date(), new Date());
}

function filesUnder(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() ? filesUnder(join(dir, entry.name)) : [join(dir, entry.name)],
  );
}

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

function timed(command, args, cwd) {
  const started = Date.now();
  const output = run(command, args, cwd);
  return `${output}\n[걸린 시간] ${String(Date.now() - started)}ms\n`;
}

function run(command, args, cwd) {
  // 윈도우의 pnpm 은 .cmd 라 셸로 부른다. 인자는 이 파일의 상수와 overlay 의 파일 이름뿐이다.
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
