// admin-style 그리기 전 테마 프로브: 관리 화면(Next 앱 라우터)이 운영자가 고른 테마를 첫 그림 전에 `<html data-theme>` 에
// 다는 길을 잰다. 같은 출처의 `public/theme.js` 를 뿌리 레이아웃의 `<head>` 에 막는(`async`·`defer` 없는) `<script src>` 로
// 싣는 후보와, 견줄 갈래 둘(클라이언트 컴포넌트의 `useEffect`, `next/script` 의 `beforeInteractive`)을 같은 임시 앱에서 잰다.
//   node .scratch/admin-style/probes/prepaint_theme.mjs [node_modules 가 있는 web 폴더, 기본 web]
//
// 까닭: ADR 0026 의 첫째 2026-10-12 이력은 테마를 localStorage 에 두고 그리기 전에 도는 스크립트가 `html` 에 달기로 했고,
// 인라인 스크립트(`dangerouslySetInnerHTML`)는 `web/eslint.config.mjs` 가 막으므로 `public/` 파일을 막는 `<script src>` 로
// 싣는 길이 판정자를 지나고 첫 그림 전에 다는지, `beforeInteractive` 가 그 대신이 되는지, 저장 값이 틀리거나 저장소가 예외를
// 던질 때와 하이드레이션의 불일치 경고를 어떻게 다루는지를 명세에 넘겼다. 이 프로브가 그 근거를 잰다.
//
// 자리: `web/apps/zz-probe-prepaint-<임의>/` 에 `package.json` 없는 임시 Next 앱을 짓고, `node_modules` 를
// `web/apps/widget/node_modules` 로 잇는 junction 을 둔다(위젯이 같은 next·react 와 `@agent-os/ui`·`@tailwindcss/postcss` 를
// 가진다). Turbopack 이 프로젝트 루트(`web/` 의 잠금 파일) 밖의 파일을 받지 않아 `web/` 안에 둔다. 페이지는 패키지의 디자인
// 토큰 CSS(`@agent-os/ui/theme.css`)를 싣고, 그것으로 첫 그림의 `--accent` 가 어느 테마의 값인지 읽는다. 빌드는 관리 화면처럼
// 플래그 없는 `next build`(Turbopack)이고 `next start`·`next dev` 는 127.0.0.1 의 빈 포트에 선다. 끝에 junction 을 재귀 없이
// 먼저 떼고, 떼어 낸 뒤 대상이 그대로인지 단언한 다음 이 실행이 만든 폴더만 지운다. 띄운 서버는 pid 의 명령줄에 이 실행의
// 임시 폴더 경로가 있을 때만 프로세스 트리째 끈다.
//
// 후보 `public/theme.js` 는 아래 THEME_SCRIPT 다. 키 목록을 그 파일에 적고, 저장 값이 목록에 없거나 저장소를 읽다 예외가 나면
// 아무것도 달지 않는다(속성이 없는 문서는 기본 테마 nokcheong 으로 그린다, `web/packages/ui/src/themes.ts`). 저장 키는
// `agent-os-admin-theme`, 저장 형식은 키 글자 그대로다(이 프로브가 고른 후보이고 결정이 아니다).
//
// 회차와 표지(표지가 없는 회차는 측정이 아니라고 따로 센다):
// 1 HTML: `next start` 의 첫 HTML 을 받는다. 표지는 응답 200, 페이지 표지 글(`probe-page`), Next 의 RSC 데이터
//   (`self.__next_f`), 그리고 탐지기 대조로 `<head>` 의 Next 자체 스크립트에서 `async` 를 하나 이상 찾은 것이다.
//   갈래: useEffect 빌드에는 `/theme.js` 가 없고, beforeInteractive 빌드의 모양은 따로 적는다.
// 2·5 첫 그림: 새 브라우저 문맥에서 저장소에 jjokbit 을 둔 뒤 연다(차가운 회차는 초기화 스크립트로 넣고 바로 열고, 따뜻한
//   회차는 한 번 연 뒤 넣고 다시 연다). 초기화 스크립트(`addInitScript`)가 `html` 의 `data-theme` 변이를 MutationObserver 로,
//   매 프레임의 속성과 `--accent` 를 문서가 생기자마자 건 `requestAnimationFrame` 고리로, `Storage.prototype.getItem` 의
//   부름을 감싸 기록한다. 첫 그림 시각은 `first-paint` 항목의 `paintTime`(없으면 `startTime`)이고, 첫 그림의 프레임은 그
//   시각 이전에 콜백이 돈 마지막 프레임이다. 표지는 테마 코드가 저장 키를 읽어 jjokbit 을 받은 것, `first-paint` 항목,
//   그 이전의 프레임 하나 이상, 하이드레이션 표지, 테마 넷의 기준 `--accent` 가 서로 다른 것이다.
//   양성 대조: useEffect 갈래는 첫 그림 뒤에 단다(방법이 늦은 것을 잡는다).
// 3 하이드레이션 뒤: 같은 빌드에서 하이드레이션 표지 뒤와 `Link` 로 다른 화면에 옮긴 뒤 속성과 변이 기록을 읽는다. 표지는
//   속성이 하이드레이션 전에 달린 것(불일치가 있었다)과, 옮긴 뒤 같은 window 인 것(전체 새로 고침이 아니다)이다.
//   덧붙인 갈래: 글이 서버와 다른 클라이언트 컴포넌트가 든 화면(`/mismatch`)에서 하이드레이션이 실패한 뒤의 속성. 표지는
//   `#mm` 의 글이 client 인 것(클라이언트가 다시 그렸다)이다. 첫 실행의 표지는 그것과 하이드레이션 오류 가운데 하나였고,
//   둘째 실행부터 앞의 것 하나로 좁혔다(첫 실행도 모든 회차가 client 였다). 둘째 실행까지는 기대를 두지 않은 관찰이었고
//   속성이 지워진 채 남았다(React 가 html 을 클라이언트에서 새로 붙이면 속성을 모두 지운다는 해석은 코드를 읽은 어림이다).
//   되살리기 갈래(`/mismatch-restore`): 같은 화면에 마운트될 때 저장 값을 다시 읽어, 목록에 있고 `html` 의 속성과 다르면
//   다시 다는 클라이언트 컴포넌트(ThemeRestore, 명세의 되살리기 후보)를 더한다. 표지는 `#mm` 이 client 이고 jjokbit 이던
//   속성이 바뀐 변이(지워짐)가 있는 것이다. 기대는 끝의 속성이 jjokbit 인 것이다.
//   결과를 본 뒤 바꾼 기준: 셋째 실행부터 `/mismatch`(prod)는 되살리기 갈래의 대조로 기대를 둔다. 같은 표지에 끝의 속성이
//   비어 있는 것이다(되살리지 않으면 지워진 채 남는다).
// 4 dev 콘솔: `next dev` 에서 `suppressHydrationWarning` 이 있는 뿌리와 없는 뿌리를 따로 띄워 콘솔의 하이드레이션 오류를 센다.
//   표지는 속성이 하이드레이션 전에 달렸고 하이드레이션 표지가 선 것이다. 양성 대조 둘(같은 서버): `/attr-mismatch` 는 html
//   밖의 요소(`data-side`)의 속성 불일치가 같은 길(`console.error`)로 잡히는 것이고, 있는 뿌리에서도 그 줄은 나오되
//   data-theme 줄은 없어야 한다(그 속성이 html 하나의 경고만 끈다). `/mismatch` 는 글 불일치가 하이드레이션 오류로 잡히는 것이다.
//   결과를 본 뒤 바꾼 기준: 첫 실행(2026-10-26)의 `/mismatch` 대조는 콘솔의 error 만 세어 두 서버 모두 기대와 달랐다. 글
//   불일치는 콘솔이 아니라 `pageerror`("Hydration failed because the server rendered text didn't match the client")로 왔다.
//   그래서 그 대조는 콘솔과 pageerror 를 함께 세고, 속성 불일치를 콘솔로 내는 `/attr-mismatch` 대조를 더했다.
// 6 저장 값과 예외: 목록에 없는 값, `getItem` 이 던질 때, `localStorage` 접근자가 던질 때. 표지는 각각 테마 코드가 그 값을
//   읽은 기록, 던진 횟수다. 양성 대조: 예외를 받지 않는 스크립트를 같은 자리로 바꿔 내면 `pageerror` 가 잡힌다.
// 7 ESLint: 레이아웃 후보와 `public/theme.js` 후보를 표준 입력으로 실제 판정자에 넣는다. 표지는 결과가 그 경로 하나로
//   돌고 무시된 파일 경고가 없는 것과, 같은 경로에 일부러 넣은 위반이 기대한 규칙 ID 로 잡히는 짝 대조다. 갈래: `.js` 에
//   타입 표기를 넣으면 파싱 오류가 난다(JS 파서가 읽는다).
//
// 기대(코드 읽기와 어림에서 온 것): 1 막는 태그가 `<head>` 에 그대로 있다. 2 후보는 첫 그림 전에 jjokbit 을 달고 첫 그림의
// `--accent` 가 jjokbit 의 값이다. useEffect 는 첫 그림 뒤에 단다. 3 하이드레이션 뒤와 옮긴 뒤에도 남고 변이는 하나다.
// 하이드레이션이 실패하면 `/mismatch` 는 지워진 채 남고 `/mismatch-restore` 는 되살린다(셋째 실행부터, 결과를 본 뒤의 기대).
// 4 없는 뿌리만 data-theme 을 든 하이드레이션 오류를 낸다. 5 beforeInteractive 는 `__next_s` 로 미뤄 첫 그림 뒤에 단다
// (`next/dist/client/script.js` 를 읽었다). 6 셋 다 오류 없이 속성을 달지 않고 첫 그림이 nokcheong 의 `--accent` 다.
// 7 후보 둘은 아무것도 보고되지 않는다.
//
// stdout 은 판(버전), 빌드와 서버의 요지, 회차마다 JSON 한 줄, 끝의 집계 줄이다. 측정 아닌 회차가 있거나 기대와 다른 것이
// 있으면 종료 코드가 1 이다. 관찰 회차(기대 없음)는 따로 센다.

import { spawn, spawnSync } from "node:child_process";
import {
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmdirSync,
  rmSync,
  symlinkSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import { connect, createServer } from "node:net";
import { dirname, isAbsolute, join, resolve, sep } from "node:path";
import { pathToFileURL } from "node:url";

const web = resolve(process.argv[2] ?? "web");
const requireWeb = createRequire(join(web, "package.json"));
const widgetModules = join(web, "apps", "widget", "node_modules");
const nextBin = join(widgetModules, "next", "dist", "bin", "next");
const { chromium } = (await import(pathToFileURL(requireWeb.resolve("playwright")).href)).default;

const THEMES = ["guncheong", "nokcheong", "jacho", "jjokbit"];
const DEFAULT_THEME = "nokcheong";
const KEY = "agent-os-admin-theme";
const CHOSEN = "jjokbit";
const OWNED = ".prepaint-probe-owned";
const PREFIX = "zz-probe-prepaint-";

const THEME_SCRIPT = `// 관리 화면의 테마를 첫 그림 전에 <html data-theme> 에 단다. 키 목록은 @agent-os/ui 의 THEMES 와 같아야 한다.
// 저장 값이 목록에 없거나 저장소를 읽지 못하면 아무것도 달지 않는다. 속성이 없는 문서는 기본 테마로 그린다.
try {
  const theme = localStorage.getItem("${KEY}");
  if (theme !== null && ["guncheong", "nokcheong", "jacho", "jjokbit"].includes(theme)) {
    document.documentElement.dataset.theme = theme;
  }
} catch {
  // 저장소를 막은 브라우저. 기본 테마로 그린다.
}
`;

// 양성 대조: 예외를 받지 않는 같은 스크립트.
const UNGUARDED_SCRIPT = `const theme = localStorage.getItem("${KEY}");
if (theme !== null && ["guncheong", "nokcheong", "jacho", "jjokbit"].includes(theme)) {
  document.documentElement.dataset.theme = theme;
}
`;

const LAYOUT_HEAD = (suppress) => `import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "관리 화면",
};

export default function RootLayout({ children }: { readonly children: ReactNode }) {
  return (
    <html lang="ko"${suppress ? " suppressHydrationWarning" : ""}>
      <head>
        <script src="/theme.js" />
      </head>
      <body>{children}</body>
    </html>
  );
}
`;

const LAYOUT_EFFECT = `import type { Metadata } from "next";
import type { ReactNode } from "react";
import { ThemeEffect } from "../components/ThemeEffect";

export const metadata: Metadata = {
  title: "관리 화면",
};

export default function RootLayout({ children }: { readonly children: ReactNode }) {
  return (
    <html lang="ko">
      <body>
        {children}
        <ThemeEffect />
      </body>
    </html>
  );
}
`;

const LAYOUT_BEFORE_INTERACTIVE = `import type { Metadata } from "next";
import Script from "next/script";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "관리 화면",
};

export default function RootLayout({ children }: { readonly children: ReactNode }) {
  return (
    <html lang="ko">
      <body>
        {children}
        <Script src="/theme.js" strategy="beforeInteractive" />
      </body>
    </html>
  );
}
`;

const APP_FILES = {
  "next.config.mjs": "export default { compress: false, agentRules: false };\n",
  "postcss.config.mjs": 'export default { plugins: { "@tailwindcss/postcss": {} } };\n',
  "tsconfig.json": `${JSON.stringify(
    {
      extends: "../../tsconfig.base.json",
      compilerOptions: {
        target: "es2024",
        lib: ["es2024", "dom", "dom.iterable"],
        module: "esnext",
        moduleResolution: "bundler",
        jsx: "react-jsx",
        allowImportingTsExtensions: true,
        types: ["node"],
        plugins: [{ name: "next" }],
      },
      include: ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts", ".next/dev/types/**/*.ts"],
      exclude: ["node_modules"],
    },
    null,
    2,
  )}\n`,
  "public/theme.js": THEME_SCRIPT,
  "styles/probe.css": '@import "@agent-os/ui/theme.css";\n',
  "components/Shell.tsx": `import type { ReactNode } from "react";
import "../styles/probe.css";
import { Hydrated } from "./Hydrated";

export function Shell({ id, children }: { readonly id: string; readonly children: ReactNode }) {
  return (
    <main id={id}>
      {children}
      <Hydrated />
    </main>
  );
}
`,
  "components/Hydrated.tsx": `"use client";

import { useEffect, useState } from "react";

export function Hydrated() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    if (!Reflect.has(window, "__probeHydratedAt")) {
      Reflect.set(window, "__probeHydratedAt", performance.now());
    }
    setMounted(true);
  }, []);
  return <span id="hydrated">{mounted ? "hydrated" : "server"}</span>;
}
`,
  "components/Mismatch.tsx": `"use client";

export function Mismatch() {
  return <span id="mm">{typeof window === "undefined" ? "server" : "client"}</span>;
}
`,
  "components/AttrMismatch.tsx": `"use client";

export function AttrMismatch() {
  return (
    <span id="am" data-side={typeof window === "undefined" ? "server" : "client"}>
      attr
    </span>
  );
}
`,
  "app/attr-mismatch/page.tsx": `import { AttrMismatch } from "../../components/AttrMismatch";
import { Shell } from "../../components/Shell";

export default function Page() {
  return (
    <Shell id="probe-attr-mismatch">
      <AttrMismatch />
    </Shell>
  );
}
`,
  "components/ThemeEffect.tsx": `"use client";

import { useEffect } from "react";

const KEYS: readonly string[] = ${JSON.stringify(THEMES)};

export function ThemeEffect() {
  useEffect(() => {
    try {
      const theme = localStorage.getItem("${KEY}");
      if (theme !== null && KEYS.includes(theme)) {
        document.documentElement.setAttribute("data-theme", theme);
      }
    } catch {
      // 기본 테마
    }
  }, []);
  return null;
}
`,
  "app/page.tsx": `import Link from "next/link";
import { Shell } from "../components/Shell";

export default function Page() {
  return (
    <Shell id="probe-main">
      <p>probe-page</p>
      <Link id="to-other" href="/other">
        다른 화면
      </Link>
    </Shell>
  );
}
`,
  "app/other/page.tsx": `import { Shell } from "../../components/Shell";

export default function Page() {
  return (
    <Shell id="probe-other">
      <p>other-page</p>
    </Shell>
  );
}
`,
  "app/mismatch/page.tsx": `import { Mismatch } from "../../components/Mismatch";
import { Shell } from "../../components/Shell";

export default function Page() {
  return (
    <Shell id="probe-mismatch">
      <Mismatch />
    </Shell>
  );
}
`,
  "components/ThemeRestore.tsx": `"use client";

import { useEffect } from "react";

const KEYS: readonly string[] = ${JSON.stringify(THEMES)};

export function ThemeRestore() {
  useEffect(() => {
    try {
      const theme = localStorage.getItem("${KEY}");
      const html = document.documentElement;
      if (theme !== null && KEYS.includes(theme) && html.getAttribute("data-theme") !== theme) {
        html.setAttribute("data-theme", theme);
      }
    } catch {
      // 기본 테마
    }
  }, []);
  return null;
}
`,
  "app/mismatch-restore/page.tsx": `import { Mismatch } from "../../components/Mismatch";
import { Shell } from "../../components/Shell";
import { ThemeRestore } from "../../components/ThemeRestore";

export default function Page() {
  return (
    <Shell id="probe-mismatch-restore">
      <Mismatch />
      <ThemeRestore />
    </Shell>
  );
}
`,
};

// ---------------------------------------------------------------------------------------------- 셈

let measured = 0;
let notMeasured = 0;
let unexpected = 0;
let observed = 0;

/** 회차 하나를 적는다. expected 가 null 이면 관찰(기대 없음)이다. */
function report(record) {
  const { measurement, expected } = record;
  if (!measurement) {
    notMeasured += 1;
  } else {
    measured += 1;
    if (expected === null) {
      observed += 1;
    } else if (!expected) {
      unexpected += 1;
    }
  }
  console.log(JSON.stringify(record));
}

const version = (path) => JSON.parse(readFileSync(path, "utf8")).version;

// ---------------------------------------------------------------------------------------------- 7 ESLint

const eslintPackage = join(web, "node_modules", "eslint", "package.json");
const eslintBin = join(dirname(eslintPackage), JSON.parse(readFileSync(eslintPackage, "utf8")).bin.eslint);

function lint(filename, source) {
  const run = spawnSync(
    process.execPath,
    [eslintBin, "--max-warnings", "0", "--format", "json", "--stdin", "--stdin-filename", filename],
    { cwd: web, input: source, encoding: "utf8", timeout: 600_000 },
  );
  let results = null;
  try {
    results = JSON.parse(run.stdout);
  } catch {
    results = null;
  }
  const wanted = join(web, filename);
  const result = Array.isArray(results) && results.length === 1 ? results[0] : null;
  const messages = result === null ? [] : result.messages;
  const ignored = messages.some((m) => /File ignored/.test(m.message));
  const linted = result !== null && resolve(result.filePath) === wanted && !ignored;
  return {
    status: run.status,
    linted,
    rules: messages.map((m) => (m.ruleId === null ? `fatal: ${m.message}` : m.ruleId)),
    stderr: run.stderr.trim().split("\n").slice(0, 3).join(" | "),
  };
}

function printConfig(filename) {
  const run = spawnSync(process.execPath, [eslintBin, "--print-config", filename], {
    cwd: web,
    encoding: "utf8",
    timeout: 600_000,
  });
  try {
    const config = JSON.parse(run.stdout);
    const rules = Object.keys(config.rules ?? {});
    return {
      status: run.status,
      parser: config.languageOptions?.parser ?? null,
      typescriptRules: rules.filter((r) => r.startsWith("@typescript-eslint/")).length,
      hasRestrictedGlobals: rules.includes("no-restricted-globals"),
    };
  } catch {
    return { status: run.status, error: run.stderr.trim().split("\n").slice(0, 3).join(" | ") };
  }
}

function eslintRounds() {
  const LAYOUT = "apps/admin/app/layout.tsx";
  const SCRIPT = "apps/admin/public/theme.js";
  const inlineControl = LAYOUT_HEAD(false).replace(
    '<script src="/theme.js" />',
    '<script dangerouslySetInnerHTML={{ __html: "1" }} />',
  );
  const typedControl = `${LAYOUT_HEAD(false)}\nexport const 수: number = JSON.parse("1");\n`;

  const controls = {
    inline: lint(LAYOUT, inlineControl),
    typed: lint(LAYOUT, typedControl),
    fetch: lint(SCRIPT, `${THEME_SCRIPT}fetch("/x");\n`),
  };
  const controlOk = {
    inline: controls.inline.linted && controls.inline.rules.includes("no-restricted-syntax"),
    typed: controls.typed.linted && controls.typed.rules.includes("@typescript-eslint/no-unsafe-assignment"),
    fetch: controls.fetch.linted && controls.fetch.rules.includes("no-restricted-globals"),
  };
  for (const [name, result] of Object.entries(controls)) {
    report({
      item: 7,
      round: `대조 ${name}`,
      path: name === "fetch" ? SCRIPT : LAYOUT,
      measurement: result.linted,
      expected: result.linted ? controlOk[name] : false,
      ...result,
    });
  }

  const candidates = [
    { round: "레이아웃 후보(막는 script)", path: LAYOUT, source: LAYOUT_HEAD(false), pair: ["inline", "typed"] },
    {
      round: "레이아웃 후보 + suppressHydrationWarning",
      path: LAYOUT,
      source: LAYOUT_HEAD(true),
      pair: ["inline", "typed"],
    },
    {
      round: "레이아웃 갈래(next/script beforeInteractive)",
      path: LAYOUT,
      source: LAYOUT_BEFORE_INTERACTIVE,
      pair: ["inline", "typed"],
    },
    { round: "public/theme.js 후보", path: SCRIPT, source: THEME_SCRIPT, pair: ["fetch"] },
  ];
  for (const { round, path, source, pair } of candidates) {
    const result = lint(path, source);
    const measurement = result.linted && pair.every((name) => controlOk[name]);
    report({
      item: 7,
      round,
      path,
      measurement,
      expected: result.rules.length === 0 && result.status === 0,
      pairedControls: pair,
      ...result,
    });
  }

  const parse = lint(SCRIPT, `${THEME_SCRIPT}const 수: number = 1;\n`);
  report({
    item: 7,
    round: "갈래: theme.js 에 타입 표기",
    path: SCRIPT,
    measurement: parse.linted,
    expected: parse.rules.some((r) => r.startsWith("fatal: Parsing error")),
    ...parse,
  });

  for (const path of [LAYOUT, SCRIPT]) {
    const config = printConfig(path);
    report({ item: 7, round: "print-config", path, measurement: config.status === 0, expected: null, ...config });
  }
}

// ---------------------------------------------------------------------------------------------- 임시 앱

function write(app, relative, content) {
  const path = join(app, relative);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content);
}

/** dir 아래의 심볼릭 링크와 junction 을 재귀 없이 떼어 낸다. 링크는 따라 들어가지 않는다. */
function detachLinks(dir, detached) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const stat = lstatSync(path);
    if (stat.isSymbolicLink()) {
      try {
        unlinkSync(path);
      } catch {
        rmdirSync(path);
      }
      detached.push(path);
    } else if (stat.isDirectory()) {
      detachLinks(path, detached);
    }
  }
}

const widgetListing = () => readdirSync(widgetModules).sort().join(",");

/** 이 실행이 만든 임시 앱(표지 파일이 있는 절대 경로) 안의 dir 만, 링크를 먼저 뗀 뒤 지운다. */
function removeTree(dir, app, appsDir, before) {
  const appShaped = isAbsolute(app) && dirname(app) === appsDir && app.slice(appsDir.length + 1).startsWith(PREFIX);
  if (!appShaped || !(dir === app || dir.startsWith(app + sep))) {
    throw new Error(`지우지 않는다: ${dir} 는 이 프로브의 임시 앱 안이 아니다`);
  }
  if (!existsSync(join(app, OWNED))) {
    throw new Error(`지우지 않는다: ${app} 에 표지 파일이 없다`);
  }
  const detached = [];
  if (existsSync(dir)) {
    detachLinks(dir, detached);
  }
  const intact = existsSync(join(widgetModules, "next", "package.json")) && widgetListing() === before;
  if (!intact) {
    throw new Error(`링크를 뗀 뒤 ${widgetModules} 가 바뀌었다. 지우지 않는다`);
  }
  rmSync(dir, { recursive: true, force: true });
  return { detached: detached.map((p) => p.slice(app.length + 1)), widgetModulesIntact: intact };
}

// ---------------------------------------------------------------------------------------------- 서버

function freePort() {
  return new Promise((resolvePort, reject) => {
    const server = createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => resolvePort(typeof address === "object" && address !== null ? address.port : 0));
    });
  });
}

function portOpen(port) {
  return new Promise((resolveOpen) => {
    const socket = connect(port, "127.0.0.1");
    socket.once("connect", () => {
      socket.destroy();
      resolveOpen(true);
    });
    socket.once("error", () => resolveOpen(false));
  });
}

const childEnv = { ...process.env, NEXT_TELEMETRY_DISABLED: "1" };

function build(app) {
  const run = spawnSync(process.execPath, [nextBin, "build", app], {
    cwd: app,
    env: childEnv,
    encoding: "utf8",
    timeout: 900_000,
  });
  const lines = `${run.stdout}\n${run.stderr}`.split(/\r?\n/);
  const summary = lines.filter((line) =>
    /Next\.js|Turbopack|webpack|Compiled|Route|error|Error|warn|○|ƒ|Failed/.test(line),
  );
  return { status: run.status, summary, tail: lines.slice(-25) };
}

function start(app, command, port) {
  const child = spawn(process.execPath, [nextBin, command, app, "--port", String(port), "--hostname", "127.0.0.1"], {
    cwd: app,
    env: childEnv,
    stdio: ["ignore", "pipe", "pipe"],
    detached: process.platform !== "win32",
  });
  let log = "";
  child.stdout.on("data", (chunk) => {
    log += chunk;
  });
  child.stderr.on("data", (chunk) => {
    log += chunk;
  });
  const ready = new Promise((resolveReady) => {
    const deadline = setTimeout(() => resolveReady(false), 180_000);
    const poll = setInterval(() => {
      if (/Ready in/.test(log)) {
        clearTimeout(deadline);
        clearInterval(poll);
        resolveReady(true);
      } else if (child.exitCode !== null || child.signalCode !== null) {
        clearTimeout(deadline);
        clearInterval(poll);
        resolveReady(false);
      }
    }, 100);
  });
  return { child, ready, log: () => log };
}

function commandLine(pid) {
  const run = spawnSync(
    "powershell.exe",
    ["-NoProfile", "-NonInteractive", "-Command", `(Get-CimInstance Win32_Process -Filter "ProcessId=${pid}").CommandLine`],
    { encoding: "utf8" },
  );
  return run.stdout.trim();
}

function processesMentioning(marker) {
  const run = spawnSync(
    "powershell.exe",
    [
      "-NoProfile",
      "-NonInteractive",
      "-Command",
      `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*${marker}*' -and $_.ProcessId -ne $PID } | ForEach-Object { $_.ProcessId }`,
    ],
    { encoding: "utf8" },
  );
  return run.stdout
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line !== "");
}

async function stop(server, app, port) {
  const { child } = server;
  let how = "이미 끝났다";
  if (child.exitCode === null && child.signalCode === null) {
    if (process.platform === "win32") {
      const line = commandLine(child.pid);
      if (line.includes(app)) {
        spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { encoding: "utf8" });
        how = "taskkill /T (명령줄에 임시 폴더가 있었다)";
      } else {
        how = `끄지 않았다: pid ${child.pid} 의 명령줄에 임시 폴더가 없다`;
      }
    } else {
      process.kill(-child.pid, "SIGTERM");
      how = "프로세스 그룹에 SIGTERM";
    }
    await new Promise((resolveExit) => {
      const deadline = setTimeout(resolveExit, 15_000);
      child.once("exit", () => {
        clearTimeout(deadline);
        resolveExit();
      });
    });
  }
  return { how, portStillOpen: await portOpen(port) };
}

// ---------------------------------------------------------------------------------------------- 브라우저

/** 문서가 생기자마자 도는 기록기. Playwright 가 직렬화해 넣는다. */
function initRecorder({ key, seed, mode }) {
  const rec = { muts: [], frames: [], gets: [], getItemThrew: 0, getterThrew: 0, seeded: null, initError: null };
  Object.defineProperty(window, "__probe", { value: rec });
  try {
    if (seed !== null) {
      localStorage.setItem(key, seed);
      rec.seeded = seed;
    }
    const original = Storage.prototype.getItem;
    Storage.prototype.getItem = function getItem(name) {
      if (mode === "getItemThrows") {
        rec.getItemThrew += 1;
        rec.gets.push({ at: performance.now(), key: name, threw: true });
        throw new DOMException("probe: getItem denied", "SecurityError");
      }
      const value = original.call(this, name);
      rec.gets.push({ at: performance.now(), key: name, value });
      return value;
    };
    if (mode === "getterThrows") {
      Object.defineProperty(window, "localStorage", {
        configurable: true,
        get() {
          rec.getterThrew += 1;
          throw new DOMException("probe: storage denied", "SecurityError");
        },
      });
    }
  } catch (error) {
    rec.initError = String(error);
  }
  new MutationObserver((list) => {
    const at = performance.now();
    for (const m of list) {
      if (m.target === document.documentElement) {
        rec.muts.push({ at, old: m.oldValue, value: document.documentElement.getAttribute("data-theme") });
      }
    }
  }).observe(document, { subtree: true, attributes: true, attributeFilter: ["data-theme"], attributeOldValue: true });
  const frame = (ts) => {
    const html = document.documentElement;
    rec.frames.push({
      ts,
      now: performance.now(),
      theme: html === null ? null : html.getAttribute("data-theme"),
      accent: html === null ? "" : getComputedStyle(html).getPropertyValue("--accent").trim(),
      body: document.body !== null,
    });
    if (rec.frames.length < 60) {
      requestAnimationFrame(frame);
    }
  };
  requestAnimationFrame(frame);
}

function readPage(themes) {
  const rec = Reflect.get(window, "__probe");
  const refs = {};
  for (const theme of themes) {
    const div = document.createElement("div");
    div.setAttribute("data-theme", theme);
    document.body.append(div);
    refs[theme] = getComputedStyle(div).getPropertyValue("--accent").trim();
    div.remove();
  }
  return {
    rec: JSON.parse(JSON.stringify(rec)),
    paint: performance.getEntriesByType("paint").map((e) => ({
      name: e.name,
      startTime: e.startTime,
      paintTime: "paintTime" in e ? e.paintTime : null,
      presentationTime: "presentationTime" in e ? e.presentationTime : null,
    })),
    theme: document.documentElement.getAttribute("data-theme"),
    hydratedAt: Reflect.get(window, "__probeHydratedAt") ?? null,
    hydrated: document.getElementById("hydrated")?.textContent ?? null,
    path: location.pathname,
    refs,
  };
}

const themeOfAccent = (refs, accent) => Object.keys(refs).find((t) => refs[t] === accent) ?? null;

/** 새 문맥에서 한 번 연다. warm 이면 한 번 연 뒤 저장소에 넣고 다시 연다. */
async function openRound(browser, base, { path = "/", seed = CHOSEN, warm = false, mode = null, route = null }) {
  const context = await browser.newContext();
  const page = await context.newPage();
  const pageErrors = [];
  const consoleMessages = [];
  const themeResponses = [];
  let routed = 0;
  page.on("pageerror", (error) => pageErrors.push(String(error.message)));
  page.on("console", (message) => {
    if (message.type() === "error" || message.type() === "warning") {
      consoleMessages.push(`${message.type()}: ${message.text()}`);
    }
  });
  page.on("response", (response) => {
    if (new URL(response.url()).pathname === "/theme.js") {
      themeResponses.push(response.status());
    }
  });
  if (route !== null) {
    await page.route("**/theme.js", (r) => {
      routed += 1;
      return r.fulfill({ contentType: "text/javascript", body: route });
    });
  }
  await page.addInitScript(initRecorder, { key: KEY, seed: warm ? null : seed, mode });
  if (warm) {
    await page.goto(base + path, { waitUntil: "load", timeout: 180_000 });
    await page.evaluate(([k, v]) => localStorage.setItem(k, v), [KEY, seed]);
    pageErrors.length = 0;
    consoleMessages.length = 0;
    themeResponses.length = 0;
    routed = 0;
  }
  await page.goto(base + path, { waitUntil: "load", timeout: 180_000 });
  let hydratedOk = true;
  try {
    await page.waitForFunction(() => document.getElementById("hydrated")?.textContent === "hydrated", null, {
      timeout: 60_000,
    });
  } catch {
    hydratedOk = false;
  }
  try {
    await page.waitForFunction(() => performance.getEntriesByType("paint").some((e) => e.name === "first-paint"), null, {
      timeout: 10_000,
    });
  } catch {
    // 표지에서 걸린다
  }
  await page.waitForTimeout(1_500);
  const read = await page.evaluate(readPage, THEMES);
  return { context, page, read, hydratedOk, pageErrors, consoleMessages, themeResponses, routed: () => routed };
}

/** 첫 그림 기준의 요지. */
function paintSummary(read) {
  const fp = read.paint.find((e) => e.name === "first-paint") ?? null;
  const fpTime = fp === null ? null : (fp.paintTime ?? fp.startTime);
  const frames = read.rec.frames;
  const before = fpTime === null ? [] : frames.filter((f) => f.now <= fpTime);
  const paintFrame = before.length === 0 ? null : before[before.length - 1];
  const setRecord = read.rec.muts.find((m) => m.value !== null) ?? null;
  const keyGets = read.rec.gets.filter((g) => g.key === KEY);
  const distinctRefs = new Set(Object.values(read.refs)).size === THEMES.length && !Object.values(read.refs).includes("");
  return {
    fpTime,
    fpStartTime: fp?.startTime ?? null,
    hasPaintTime: fp !== null && fp.paintTime !== null,
    framesBeforePaint: before.length,
    paintFrameTheme: paintFrame?.theme ?? null,
    paintFrameAccentTheme: paintFrame === null ? null : themeOfAccent(read.refs, paintFrame.accent),
    firstFrame: frames[0] === undefined ? null : { now: frames[0].now, theme: frames[0].theme, body: frames[0].body },
    setAt: setRecord?.at ?? null,
    setValue: setRecord?.value ?? null,
    mutations: read.rec.muts.length,
    firstKeyGetAt: keyGets[0]?.at ?? null,
    keyGetValues: keyGets.map((g) => (g.threw ? "threw" : g.value)),
    hydratedAt: read.hydratedAt,
    finalTheme: read.theme,
    distinctRefs,
    paintFrame,
  };
}

const round2 = (n) => (n === null ? null : Math.round(n * 10) / 10);

// ---------------------------------------------------------------------------------------------- 회차

async function htmlRound(base, variant) {
  const response = await fetch(`${base}/`);
  const html = await response.text();
  const head = html.match(/<head>([\s\S]*?)<\/head>/)?.[1] ?? "";
  const headTags = [...head.matchAll(/<(script|link|meta|title|style)\b[^>]*>/g)].map((m) => m[0]);
  const themeTags = headTags.filter((tag) => /^<script\b[^>]*\bsrc="\/theme\.js"/.test(tag));
  const nextScripts = headTags.filter((tag) => /^<script\b[^>]*\bsrc="\/_next\//.test(tag));
  const nextAsync = nextScripts.filter((tag) => /\basync\b/.test(tag)).length;
  const bodyPart = html.slice(html.indexOf("</head>"));
  const bodyThemeTags = (bodyPart.match(/<script\b[^>]*\bsrc="\/theme\.js"/g) ?? []).length;
  const bodyMentions = (bodyPart.match(/\/theme\.js/g) ?? []).length;
  const measurement =
    response.status === 200 && html.includes("probe-page") && html.includes("self.__next_f") && nextAsync > 0;
  const abbreviate = (tag) => (tag.length > 140 ? `${tag.slice(0, 137)}...` : tag);
  const shape = {
    themeTags,
    themeTagIndexInHead: themeTags.length === 1 ? headTags.indexOf(themeTags[0]) : null,
    headTagCount: headTags.length,
    headTags: headTags.map(abbreviate),
    nextScriptsInHead: nextScripts.length,
    nextScriptsAsync: nextAsync,
    bodyThemeScriptTags: bodyThemeTags,
    bodyThemeJsMentions: bodyMentions,
    nextS: html.includes("__next_s"),
    preloadThemeJs: /<link\b[^>]*rel="preload"[^>]*href="\/theme\.js"|<link\b[^>]*href="\/theme\.js"[^>]*rel="preload"/.test(html),
  };
  let expected;
  if (variant === "head") {
    expected =
      themeTags.length === 1 && !/\b(async|defer|type=)/.test(themeTags[0]) && shape.bodyThemeScriptTags === 0;
  } else if (variant === "effect") {
    expected = !html.includes("/theme.js");
  } else {
    expected = themeTags.length === 0 && shape.nextS && shape.preloadThemeJs;
  }
  report({ item: variant === "beforeInteractive" ? 5 : 1, round: `HTML ${variant}`, measurement, expected, status: response.status, ...shape });
}

async function paintRounds(browser, base, variant) {
  for (const warm of [false, true]) {
    for (let i = 1; i <= 3; i += 1) {
      const result = await openRound(browser, base, { warm });
      const s = paintSummary(result.read);
      await result.context.close();
      const measurement =
        result.hydratedOk &&
        s.fpTime !== null &&
        s.framesBeforePaint > 0 &&
        s.distinctRefs &&
        s.keyGetValues.includes(CHOSEN) &&
        result.read.path === "/";
      let expected;
      if (variant === "head") {
        expected =
          s.setAt !== null &&
          s.setAt < s.fpTime &&
          s.paintFrameTheme === CHOSEN &&
          s.paintFrameAccentTheme === CHOSEN &&
          s.mutations === 1 &&
          result.pageErrors.length === 0;
      } else {
        // useEffect(양성 대조)와 beforeInteractive(코드 읽기의 기대): 첫 그림 뒤에 단다
        expected =
          s.setAt !== null &&
          s.setAt > s.fpTime &&
          s.paintFrameTheme === null &&
          s.paintFrameAccentTheme === DEFAULT_THEME &&
          s.finalTheme === CHOSEN;
      }
      report({
        item: variant === "beforeInteractive" ? 5 : 2,
        round: `첫 그림 ${variant} ${warm ? "따뜻한" : "차가운"} ${i}`,
        measurement,
        expected,
        fpTime: round2(s.fpTime),
        fpStartTime: round2(s.fpStartTime),
        hasPaintTime: s.hasPaintTime,
        setAt: round2(s.setAt),
        firstKeyGetAt: round2(s.firstKeyGetAt),
        hydratedAt: round2(s.hydratedAt),
        framesBeforePaint: s.framesBeforePaint,
        paintFrameTheme: s.paintFrameTheme,
        paintFrameAccentTheme: s.paintFrameAccentTheme,
        firstFrame: s.firstFrame === null ? null : { ...s.firstFrame, now: round2(s.firstFrame.now) },
        mutations: s.mutations,
        finalTheme: s.finalTheme,
        themeResponses: result.themeResponses,
        pageErrors: result.pageErrors,
      });
    }
  }
}

async function hydrationRound(browser, base) {
  const result = await openRound(browser, base, { warm: true });
  const { page } = result;
  const s = paintSummary(result.read);
  const afterHydration = { theme: result.read.theme, mutations: result.read.rec.muts.length };
  await page.evaluate(() => Reflect.set(window, "__probeSameWindow", true));
  await page.click("#to-other");
  let navigated = true;
  try {
    await page.waitForFunction(
      () => document.getElementById("probe-other") !== null && document.getElementById("hydrated")?.textContent === "hydrated",
      null,
      { timeout: 30_000 },
    );
  } catch {
    navigated = false;
  }
  await page.waitForTimeout(1_000);
  const afterNav = await page.evaluate(() => ({
    sameWindow: Reflect.get(window, "__probeSameWindow") === true,
    path: location.pathname,
    theme: document.documentElement.getAttribute("data-theme"),
    mutations: Reflect.get(window, "__probe").muts,
  }));
  await result.context.close();
  const measurement =
    result.hydratedOk &&
    s.setAt !== null &&
    s.hydratedAt !== null &&
    s.setAt < s.hydratedAt &&
    navigated &&
    afterNav.sameWindow &&
    afterNav.path === "/other";
  report({
    item: 3,
    round: "하이드레이션 뒤와 Link 로 옮긴 뒤(prod)",
    measurement,
    expected:
      afterHydration.theme === CHOSEN &&
      afterHydration.mutations === 1 &&
      afterNav.theme === CHOSEN &&
      afterNav.mutations.length === 1,
    setAt: round2(s.setAt),
    hydratedAt: round2(s.hydratedAt),
    afterHydration,
    afterNav: { ...afterNav, mutations: afterNav.mutations.length },
    pageErrors: result.pageErrors,
  });
}

const hydrationErrors = (messages) => messages.filter((m) => /^error: /.test(m) && /hydrat/i.test(m));

async function mismatchRound(browser, base, mode) {
  const result = await openRound(browser, base, { path: "/mismatch", warm: mode === "prod" });
  const mm = await result.page.evaluate(() => document.getElementById("mm")?.textContent ?? null);
  await result.context.close();
  const errors = hydrationErrors(result.consoleMessages);
  const pageHydrationErrors = result.pageErrors.filter((m) => /hydrat/i.test(m));
  const situation = mm === "client";
  const shortMessages = [...result.consoleMessages, ...result.pageErrors.map((m) => `pageerror: ${m}`)].map((m) =>
    m.split("\n")[0].slice(0, 220),
  );
  const s = paintSummary(result.read);
  const cleared = result.read.rec.muts.some((m) => m.old === CHOSEN);
  report({
    item: mode === "prod" ? 3 : 4,
    round: mode === "prod" ? "대조: /mismatch 하이드레이션 실패 뒤(prod)" : `대조: /mismatch 콘솔(${mode})`,
    measurement: situation && s.keyGetValues.includes(CHOSEN) && (mode !== "prod" || cleared),
    // dev 의 첫 판은 콘솔만 셌다. prod 는 둘째 실행까지 관찰이었다(머리 주석의 "결과를 본 뒤 바꾼 기준")
    expected: mode === "prod" ? s.finalTheme === null : errors.length + pageHydrationErrors.length > 0,
    mm,
    setAt: round2(s.setAt),
    themeAfter: s.finalTheme,
    mutations: result.read.rec.muts.map((m) => ({ at: round2(m.at), old: m.old, value: m.value })),
    hydrationConsoleErrors: errors.length,
    hydrationPageErrors: pageHydrationErrors.length,
    messages: shortMessages,
  });
}

async function restoreRound(browser, base) {
  const result = await openRound(browser, base, { path: "/mismatch-restore", warm: true });
  const mm = await result.page.evaluate(() => document.getElementById("mm")?.textContent ?? null);
  await result.context.close();
  const s = paintSummary(result.read);
  const cleared = result.read.rec.muts.some((m) => m.old === CHOSEN);
  report({
    item: 3,
    round: "되살리기 갈래: /mismatch-restore 하이드레이션 실패 뒤(prod)",
    measurement: mm === "client" && s.keyGetValues.includes(CHOSEN) && cleared,
    expected: s.finalTheme === CHOSEN,
    mm,
    setAt: round2(s.setAt),
    themeAfter: s.finalTheme,
    mutations: result.read.rec.muts.map((m) => ({ at: round2(m.at), old: m.old, value: m.value })),
    pageErrors: result.pageErrors.map((m) => m.split("\n")[0].slice(0, 220)),
  });
}

async function attrMismatchRound(browser, base, suppress) {
  const result = await openRound(browser, base, { path: "/attr-mismatch" });
  const side = await result.page.evaluate(() => document.getElementById("am")?.getAttribute("data-side") ?? null);
  await result.context.close();
  const s = paintSummary(result.read);
  const errors = hydrationErrors(result.consoleMessages);
  const lines = errors.flatMap((m) => m.split("\n"));
  const sideLines = lines.filter((line) => line.includes("data-side"));
  const themeLines = lines.filter((line) => line.includes("data-theme"));
  // 속성 불일치는 고치지 않는다(React 의 경고 문구). 서버 값이 남아 있으면 클라이언트가 다시 그리지 않은 것이다.
  const measurement =
    result.hydratedOk && side === "server" && s.setAt !== null && s.hydratedAt !== null && s.setAt < s.hydratedAt;
  report({
    item: 4,
    round: `대조: /attr-mismatch 콘솔(${suppress ? "dev-suppress" : "dev-plain"})`,
    measurement,
    expected: sideLines.length > 0 && (suppress ? themeLines.length === 0 : themeLines.length > 0),
    side,
    themeAfter: s.finalTheme,
    mutations: s.mutations,
    hydrationConsoleErrors: errors.length,
    sideLines: sideLines.slice(0, 2),
    themeLines: themeLines.slice(0, 2),
    messages: [...result.consoleMessages, ...result.pageErrors.map((m) => `pageerror: ${m}`)].map((m) =>
      m.split("\n")[0].slice(0, 220),
    ),
  });
}

async function devRound(browser, base, suppress) {
  const result = await openRound(browser, base, {});
  await result.page.waitForTimeout(1_500);
  const late = await result.page.evaluate(() => Reflect.get(window, "__probe").muts.length);
  await result.context.close();
  const s = paintSummary(result.read);
  const errors = hydrationErrors(result.consoleMessages);
  const measurement =
    result.hydratedOk && s.setAt !== null && s.hydratedAt !== null && s.setAt < s.hydratedAt && s.keyGetValues.includes(CHOSEN);
  report({
    item: 4,
    round: `dev / ${suppress ? "suppressHydrationWarning 있음" : "suppressHydrationWarning 없음"}`,
    measurement,
    expected: suppress ? errors.length === 0 : errors.length > 0 && errors.some((m) => m.includes("data-theme")),
    setAt: round2(s.setAt),
    hydratedAt: round2(s.hydratedAt),
    themeAfter: s.finalTheme,
    mutationsAfter: late,
    hydrationConsoleErrors: errors.length,
    messages: [...result.consoleMessages, ...result.pageErrors.map((m) => `pageerror: ${m}`)].map((m) =>
      m.split("\n").slice(0, 2).join(" ⏎ ").slice(0, 400),
    ),
    dataThemeLines: errors.flatMap((m) => m.split("\n").filter((line) => line.includes("data-theme"))).slice(0, 4),
  });
}

async function storageRounds(browser, base) {
  const cases = [
    { round: "저장 값이 목록에 없다", seed: "bogus", mode: null, route: null },
    { round: "getItem 이 던진다", seed: CHOSEN, mode: "getItemThrows", route: null },
    { round: "localStorage 접근자가 던진다", seed: CHOSEN, mode: "getterThrows", route: null },
    { round: "대조: 예외를 받지 않는 스크립트 + getItem 이 던진다", seed: CHOSEN, mode: "getItemThrows", route: UNGUARDED_SCRIPT },
  ];
  for (const { round, seed, mode, route } of cases) {
    const result = await openRound(browser, base, { seed, mode, route });
    const routed = result.routed();
    await result.context.close();
    const s = paintSummary(result.read);
    const rec = result.read.rec;
    let situation;
    if (mode === null) {
      situation = s.keyGetValues.includes("bogus");
    } else if (mode === "getItemThrows") {
      situation = rec.getItemThrew > 0 && s.keyGetValues.includes("threw") && (route === null || routed > 0);
    } else {
      situation = rec.getterThrew > 0;
    }
    const measurement =
      situation && rec.initError === null && result.hydratedOk && s.fpTime !== null && s.framesBeforePaint > 0 && s.distinctRefs;
    const fellBack =
      s.paintFrameTheme === null && s.finalTheme === null && s.mutations === 0 && s.paintFrameAccentTheme === DEFAULT_THEME;
    const expected =
      route === null
        ? fellBack && result.pageErrors.length === 0
        : result.pageErrors.some((m) => m.includes("probe: getItem denied"));
    report({
      item: 6,
      round,
      measurement,
      expected,
      keyGetValues: s.keyGetValues,
      getItemThrew: rec.getItemThrew,
      getterThrew: rec.getterThrew,
      initError: rec.initError,
      routed,
      paintFrameTheme: s.paintFrameTheme,
      paintFrameAccentTheme: s.paintFrameAccentTheme,
      finalTheme: s.finalTheme,
      mutations: s.mutations,
      hydrated: result.hydratedOk,
      pageErrors: result.pageErrors,
    });
  }
}

// ---------------------------------------------------------------------------------------------- 실행

const versions = {
  node: process.version,
  next: version(join(widgetModules, "next", "package.json")),
  react: version(join(widgetModules, "react", "package.json")),
  reactDom: version(join(widgetModules, "react-dom", "package.json")),
  nextBundledReact:
    readFileSync(join(widgetModules, "next", "dist", "compiled", "react", "cjs", "react.production.js"), "utf8").match(
      /exports\.version = "([^"]+)"/,
    )?.[1] ?? null,
  playwright: version(join(web, "node_modules", "playwright", "package.json")),
  eslint: version(eslintPackage),
  tailwindPostcss: version(join(widgetModules, "@tailwindcss", "postcss", "package.json")),
};
console.log(`판: ${JSON.stringify(versions)}`);

eslintRounds();

const appsDir = join(web, "apps");
const before = widgetListing();
const app = mkdtempSync(join(appsDir, PREFIX));
writeFileSync(join(app, OWNED), "");
const marker = app.slice(appsDir.length + 1);
const link = join(app, "node_modules");
symlinkSync(widgetModules, link, "junction");
if (!lstatSync(link).isSymbolicLink()) {
  throw new Error(`${link} 가 lstat 에서 링크로 보이지 않는다. 지우기 안전을 판정하지 못하므로 멈춘다`);
}
for (const [relative, content] of Object.entries(APP_FILES)) {
  write(app, relative, content);
}
console.log(`임시 앱: ${app}`);

const browser = await chromium.launch();
console.log(`chromium ${browser.version()}`);
const servers = [];
try {
  const phases = [
    { name: "head", command: "start", layout: LAYOUT_HEAD(false) },
    { name: "effect", command: "start", layout: LAYOUT_EFFECT },
    { name: "beforeInteractive", command: "start", layout: LAYOUT_BEFORE_INTERACTIVE },
    { name: "dev-plain", command: "dev", layout: LAYOUT_HEAD(false) },
    { name: "dev-suppress", command: "dev", layout: LAYOUT_HEAD(true) },
  ];
  for (const phase of phases) {
    const nextDir = join(app, ".next");
    if (existsSync(nextDir)) {
      const removed = removeTree(nextDir, app, appsDir, before);
      console.log(`.next 지움: 뗀 링크 ${removed.detached.length}`);
    }
    write(app, "app/layout.tsx", phase.layout);
    if (phase.command === "start") {
      const built = build(app);
      console.log(`빌드 ${phase.name}: 종료 ${built.status}\n  ${built.summary.join("\n  ")}`);
      if (built.status !== 0) {
        console.log(`  끝 줄:\n  ${built.tail.join("\n  ")}`);
        report({ item: 1, round: `빌드 ${phase.name}`, measurement: false, expected: false });
        continue;
      }
    }
    const port = await freePort();
    const server = start(app, phase.command, port);
    servers.push({ server, port });
    const ready = await server.ready;
    const base = `http://127.0.0.1:${port}`;
    console.log(`${phase.command} ${phase.name}: ${ready ? "Ready" : "준비되지 않음"} ${base}`);
    if (!ready) {
      console.log(server.log().split(/\r?\n/).slice(-20).join("\n"));
      report({ item: 1, round: `서버 ${phase.name}`, measurement: false, expected: false });
    } else if (phase.name === "head") {
      await htmlRound(base, "head");
      await paintRounds(browser, base, "head");
      await hydrationRound(browser, base);
      await mismatchRound(browser, base, "prod");
      await restoreRound(browser, base);
      await storageRounds(browser, base);
    } else if (phase.name === "effect") {
      await htmlRound(base, "effect");
      await paintRounds(browser, base, "effect");
    } else if (phase.name === "beforeInteractive") {
      await htmlRound(base, "beforeInteractive");
      await paintRounds(browser, base, "beforeInteractive");
    } else {
      const suppress = phase.name === "dev-suppress";
      await devRound(browser, base, suppress);
      await attrMismatchRound(browser, base, suppress);
      await mismatchRound(browser, base, phase.name);
      const devLog = server.log();
      console.log(`  dev 로그의 하이드레이션 언급: ${(devLog.match(/hydrat/gi) ?? []).length}`);
    }
    const stopped = await stop(server, app, port);
    servers.pop();
    console.log(`  서버 끔: ${stopped.how}, 포트 열림 ${stopped.portStillOpen}`);
  }
} finally {
  for (const { server, port } of servers) {
    const stopped = await stop(server, app, port);
    console.log(`  (finally) 서버 끔: ${stopped.how}, 포트 열림 ${stopped.portStillOpen}`);
  }
  await browser.close();
  if (process.platform === "win32") {
    const left = processesMentioning(marker);
    console.log(`임시 폴더를 명령줄에 든 남은 프로세스: ${left.length === 0 ? "없음" : left.join(",")}`);
  }
  const removed = removeTree(app, app, appsDir, before);
  console.log(
    `임시 앱 지움: 뗀 링크 ${JSON.stringify(removed.detached)}, 위젯 node_modules 그대로 ${removed.widgetModulesIntact}, 폴더 남음 ${existsSync(app)}`,
  );
}

console.log(`측정 ${measured}(관찰 ${observed}), 측정 아님 ${notMeasured}, 기대와 다름 ${unexpected}`);
process.exit(notMeasured > 0 || unexpected > 0 ? 1 : 0);
