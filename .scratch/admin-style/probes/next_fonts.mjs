// admin-style Next 글꼴 프로브: 플래그 없는 `next build`(Turbopack)가 관리 화면이 들일 모양(전역 CSS 를 pages 컴포넌트에서
// import, 뿌리 레이아웃은 CSS 를 import 하지 않음)에서 디자인 토큰 CSS 와 글꼴 CSS 를 어떻게 내는지 본다.
//   node .scratch/admin-style/probes/next_fonts.mjs
//
// 까닭: 패키지는 디자인 토큰 CSS(`@agent-os/ui/theme.css`)와 글꼴 CSS(`@agent-os/ui/fonts.css`, Noto Sans KR 400·500·600 과
// Noto Sans Mono 400·500 의 fontsource CSS 를 `@import`)를 나눠 낸다. 관리 화면은 위젯처럼 `postcss.config.mjs`
// (`@tailwindcss/postcss`)와 앱 CSS(`@import "@agent-os/ui/theme.css"; @source …`)로 들일 예정이다. 그때 (1) Noto Sans KR 과
// Noto Sans Mono 의 woff2 가 모두 빌드 산출물에 나오고 산출 CSS 의 `@font-face` 가 그 파일을 가리키는지, (2) 앱 소스에만 있는
// 클래스가 `@source` 덕에 규칙을 만드는지 명세가 근거로 든다.
//
// 자리: `web/apps/` 아래 `package.json` 없는 임시 앱 폴더(관리 화면과 같은 깊이)를 갈래마다 하나 만들고 그 `node_modules` 를
// `web/apps/widget/node_modules` 로 잇는 junction 을 둔다(next·react·`@agent-os/ui`·`@tailwindcss/postcss`·typescript 가 위젯의
// 것으로 풀린다). 잠금 파일(`web/pnpm-lock.yaml`)이 위에 있어 Turbopack 의 뿌리도 관리 화면처럼 `web/` 으로 잡힌다. 앱은
// 관리 화면의 tsconfig 모양, 위젯의 `postcss.config.mjs` 그대로, `next.config.mjs`(`agentRules: false` 만), 뿌리 레이아웃(CSS 없음),
// `app/page.tsx` → `components/pages/HomePage.tsx`("use client", 글꼴 CSS 와 앱 CSS 를 import)이다. 위젯 자체는 빌드하지 않는다.
//
// 갈래(빌드 셋, 다른 것은 같다)
//   - `source+fonts`: 앱 CSS 가 `@source "../app"; @source "../components";` 를 두고 HomePage 가 글꼴 CSS 를 import 한다.
//   - `nosource+fonts`: 앱 CSS 에 `@source` 가 없다. 앱에만 있는 클래스의 규칙이 `@source` 덕인지 가르는 음성 대조다.
//   - `source+nofonts`: HomePage 가 글꼴 CSS 를 import 하지 않는다. 산출물의 Noto 글꼴이 글꼴 CSS 의 import 에서 온 것인지 가르는
//     음성 대조다.
// 앱에만 있는 클래스는 `w-nav`·`h-top-bar`(관리 화면 틀의 토큰)이고, 패키지 소스(`web/packages/ui/src`, 디자인 토큰 CSS 의
// `@source ".."`)에 그 글자가 없는 것을 먼저 단언한다. 패키지 소스에 있는 `bg-bg-raised` 를 HomePage 도 쓴다. 그 규칙은 세 갈래
// 모두에 있어야 한다(규칙을 찾는 방법과 Tailwind 가 돈 것의 양성 대조).
//
// 글꼴을 재는 법: fontsource 의 굵기 CSS 다섯에서 `@font-face` 와 그 woff2 파일의 sha256 을 읽어 기준으로 삼는다. 산출 CSS
// (`.next/static` 아래 `.css`)의 `@font-face` 를 가족마다 세고, 그 `url()`(`/_next/…` 는 `.next/…`, 상대 경로는 CSS 파일 기준)을
// 파일로 풀어 있는지와 sha256 이 기준에 드는지 본다. 소비 지점으로, 미리 그린 HTML(`.next/server/app/index.html`)을 Chromium 에서
// `http://next.invalid/` 로 route 해 열고(`/_next/static/…` 은 `.next/static/…`) 가족·굵기마다 `document.fonts.load` 로 실제로
// 받아지는지 본다(Noto Sans KR 은 "가", Noto Sans Mono 는 "a").
//
// 측정의 표지(회차는 빌드 하나): `next build` 가 0 으로 끝나고, 출력에 `Turbopack` 이 있으며, `.next/BUILD_ID` 가 있고, 산출 CSS 가운데
// 디자인 토큰(`--gray-50`)을 품고 Tailwind 지시문(`@theme`, `@source`)이 남지 않은 파일이 있으며, 브라우저에서 `/_next/static/` 의
// 시트가 규칙을 하나 이상 실었다. 하나라도 빠지면 측정 아님이다.
// 기대: `source+fonts` 는 두 가족의 기준 woff2 가 모두 산출물에 있고 산출 `@font-face` 수가 기준과 같으며 모든 woff2 `url()` 이
// 있는 파일을 가리키고, 브라우저가 다섯 굵기를 모두 받으며, `w-nav`·`h-top-bar`·`bg-bg-raised` 규칙이 있다. `nosource+fonts` 는
// 글꼴이 같고 `w-nav`·`h-top-bar` 규칙이 없으며 `bg-bg-raised` 는 있다. `source+nofonts` 는 Noto `@font-face` 와 기준 woff2 가
// 산출물에 하나도 없고 브라우저가 받는 Noto 글꼴이 없으며, 클래스 셋은 `source+fonts` 와 같다.
// stdout 은 판 줄, 회차마다 JSON 한 줄, 끝의 집계 줄이다. 측정 아닌 회차가 있거나 기대와 다른 것이 있으면 종료 코드가 1 이다.
//
// 지우기: 이 프로브가 만든 임시 폴더만 지운다. junction 을 먼저 재귀 없이 떼고(unlink, 안 되면 rmdir), 잇던 대상이 그대로
// 있는지 단언하고, 폴더 안에 다른 링크가 없을 때만 폴더를 재귀로 지운다. 링크가 남았으면 지우지 않고 경로를 찍는다. 끝에
// 위젯과 `web/` 의 `node_modules` 에 `.vite-temp`·`.vite`·`.cache` 가 새로 생겼는지 보고, 생겼으면 빈 폴더만 지우고 그 경로를
// 찍으며 종료 코드를 1 로 둔다(같은 폴더의 storybook_next_link.mjs 첫 실행이 junction 너머에 빈 `.vite-temp` 를 남겼다).

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  existsSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmdirSync,
  rmSync,
  statSync,
  symlinkSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve, sep } from "node:path";

const REPO = resolve(import.meta.dirname, "..", "..", "..");
const WEB = join(REPO, "web");
const UI = join(WEB, "packages", "ui");
const WIDGET = join(WEB, "apps", "widget");
const WIDGET_MODULES = join(WIDGET, "node_modules");
const PREFIX = join(WEB, "apps", "probe-next-fonts-");
const ORIGIN = "http://next.invalid";
const APP_ONLY = ["w-nav", "h-top-bar"];
const PACKAGE_CLASS = "bg-bg-raised";
const FAMILIES = {
  "Noto Sans KR": { pkg: "@fontsource/noto-sans-kr", weights: [400, 500, 600], text: "가" },
  "Noto Sans Mono": { pkg: "@fontsource/noto-sans-mono", weights: [400, 500], text: "a" },
};
const VARIANTS = [
  { name: "source+fonts", source: true, fonts: true },
  { name: "nosource+fonts", source: false, fonts: true },
  { name: "source+nofonts", source: true, fonts: false },
];

/** `from` 에서 위로 올라가며 처음 만나는 `node_modules/<name>` 폴더. 없으면 null. */
function packageDir(from, name) {
  for (let dir = from; ; dir = dirname(dir)) {
    const candidate = join(dir, "node_modules", ...name.split("/"));
    if (existsSync(join(candidate, "package.json"))) {
      return candidate;
    }
    if (dirname(dir) === dir) {
      return null;
    }
  }
}

function versionOf(from, name) {
  const dir = packageDir(from, name);
  return dir === null ? null : JSON.parse(readFileSync(join(dir, "package.json"), "utf8")).version;
}

const versions = {
  ...Object.fromEntries(
    ["next", "react", "react-dom", "tailwindcss", "@tailwindcss/postcss", "typescript"].map((name) => [
      name,
      versionOf(WIDGET, name),
    ]),
  ),
  ...Object.fromEntries(Object.values(FAMILIES).map(({ pkg }) => [pkg, versionOf(UI, pkg)])),
  playwright: versionOf(WEB, "playwright"),
};
const missing = Object.entries(versions).filter(([, version]) => version === null);
if (missing.length > 0) {
  console.error(`풀리지 않는 패키지가 있다: ${missing.map(([name]) => name).join(", ")}`);
  process.exit(1);
}
console.log(`판 ${JSON.stringify(versions)}`);

const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");

function filesUnder(root) {
  const found = [];
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      const path = join(dir, name);
      const stat = lstatSync(path);
      if (stat.isDirectory()) {
        walk(path);
      } else if (stat.isFile()) {
        found.push(path);
      }
    }
  };
  walk(root);
  return found;
}

// 앱에만 있어야 하는 클래스가 패키지 소스에 없는지(디자인 토큰 CSS 의 `@source ".."` 가 훑는 자리).
const packageSources = filesUnder(join(UI, "src")).map((path) => readFileSync(path, "utf8"));
const appOnlyInPackage = APP_ONLY.filter((name) => packageSources.some((text) => text.includes(name)));
const packageClassInPackage = packageSources.some((text) => text.includes(PACKAGE_CLASS));
if (appOnlyInPackage.length > 0 || !packageClassInPackage) {
  console.error(
    `클래스 전제가 맞지 않는다. 패키지 소스에 있는 앱 전용 클래스 ${JSON.stringify(appOnlyInPackage)}, 패키지 클래스 있음 ${packageClassInPackage}`,
  );
  process.exit(1);
}

/** `@font-face` 블록을 가족·굵기·woff2·woff url 로 읽는다. */
function fontFaces(css) {
  return [...css.matchAll(/@font-face\s*\{([^}]*)\}/g)].map(([, body]) => {
    const family = body.match(/font-family\s*:\s*([^;]+)/)?.[1].trim().replace(/^["']|["']$/g, "") ?? "";
    const weight = Number(body.match(/font-weight\s*:\s*(\d+)/)?.[1] ?? NaN);
    const urls = [...body.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)].map((m) => m[1]);
    return {
      family,
      weight,
      woff2: urls.filter((url) => /\.woff2(?:[?#].*)?$/.test(url)),
      woff: urls.filter((url) => /\.woff(?:[?#].*)?$/.test(url)),
    };
  });
}

// 기준: fontsource 굵기 CSS 의 `@font-face` 와 그 woff2 의 sha256.
const baseline = {};
for (const [family, { pkg, weights }] of Object.entries(FAMILIES)) {
  const dir = packageDir(UI, pkg);
  const faces = weights.flatMap((weight) => fontFaces(readFileSync(join(dir, `${weight}.css`), "utf8")));
  baseline[family] = {
    faces: faces.filter((face) => face.family === family).length,
    woff2: new Set(faces.flatMap((face) => face.woff2.map((url) => sha256(join(dir, url))))),
  };
}
console.log(
  `기준 ${JSON.stringify(Object.fromEntries(Object.entries(baseline).map(([family, b]) => [family, { faces: b.faces, woff2Files: b.woff2.size }])))}`,
);

function lexists(path) {
  try {
    lstatSync(path);
    return true;
  } catch {
    return false;
  }
}

function linksUnder(root) {
  const found = [];
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      const path = join(dir, name);
      const stat = lstatSync(path);
      if (stat.isSymbolicLink()) {
        found.push(path);
      } else if (stat.isDirectory()) {
        walk(path);
      }
    }
  };
  walk(root);
  return found;
}

/** junction 을 재귀 없이 떼고, 대상이 남았는지 보고, 다른 링크가 없으면 임시 폴더를 지운다. 지웠으면 true. */
function removeApp(app) {
  if (!app.startsWith(PREFIX)) {
    console.error(`지우지 않는다. 이 프로브가 만든 폴더가 아니다: ${app}`);
    return false;
  }
  const junction = join(app, "node_modules");
  if (lexists(junction)) {
    if (!lstatSync(junction).isSymbolicLink()) {
      console.error(`지우지 않는다. junction 자리가 링크가 아니다: ${junction}`);
      return false;
    }
    try {
      unlinkSync(junction);
    } catch {
      rmdirSync(junction);
    }
  }
  if (!existsSync(join(WIDGET_MODULES, "next", "package.json"))) {
    console.error(`잇던 대상이 온전하지 않다: ${WIDGET_MODULES}`);
    return false;
  }
  const links = linksUnder(app);
  if (links.length > 0) {
    console.error(`지우지 않는다. 임시 폴더에 링크가 남았다: ${links.join(", ")}`);
    return false;
  }
  rmSync(app, { recursive: true, force: true });
  return !existsSync(app);
}

function makeApp(variant) {
  const app = mkdtempSync(PREFIX);
  const junction = join(app, "node_modules");
  symlinkSync(WIDGET_MODULES, junction, "junction");
  if (!lstatSync(junction).isSymbolicLink()) {
    rmdirSync(junction);
    throw new Error("lstat 이 junction 을 링크로 보지 않는다. 지우기 안전장치를 믿을 수 없어 멈춘다");
  }
  const write = (relative, text) => {
    const path = join(app, relative);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, text);
  };
  // 관리 화면의 tsconfig 와 같은 모양(web/apps/admin/tsconfig.json).
  write(
    "tsconfig.json",
    `${JSON.stringify(
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
  );
  write("next.config.mjs", "export default { agentRules: false };\n");
  write("postcss.config.mjs", 'export default {\n  plugins: { "@tailwindcss/postcss": {} },\n};\n');
  write(
    "app/layout.tsx",
    `import type { ReactNode } from "react";

export default function RootLayout({ children }: { readonly children: ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
`,
  );
  write(
    "app/page.tsx",
    `import { HomePage } from "../components/pages/HomePage";

export default function Page() {
  return <HomePage />;
}
`,
  );
  write(
    "components/pages/HomePage.tsx",
    `"use client";

${variant.fonts ? 'import "@agent-os/ui/fonts.css";\n' : ""}import "../../styles/admin.css";

export function HomePage() {
  return (
    <main className="${PACKAGE_CLASS}">
      <nav className="${APP_ONLY.join(" ")}">관리 화면</nav>
      <p className="font-mono">run_01JA7Q8M2K</p>
    </main>
  );
}
`,
  );
  write(
    "styles/admin.css",
    `@import "@agent-os/ui/theme.css";\n${variant.source ? '@source "../app";\n@source "../components";\n' : ""}`,
  );
  return app;
}

// 임시 폴더 밖에 생기면 안 되는 캐시 자리. 처음에 없던 것이 끝에 있으면 프로브가 남긴 것이다.
const WATCHED = [WIDGET_MODULES, join(WEB, "node_modules")].flatMap((dir) =>
  [".vite-temp", ".vite", ".cache"].map((name) => join(dir, name)),
);
const watchedBefore = new Set(WATCHED.filter((path) => existsSync(path)));

const nextBin = join(packageDir(WIDGET, "next"), "dist", "bin", "next");
const { chromium } = createRequire(join(WEB, "package.json"))("playwright");

/** 산출 CSS 의 url 을 `.next` 아래 파일로 푼다. */
function fileOf(app, cssFile, url) {
  const clean = url.replace(/[?#].*$/, "");
  if (clean.startsWith("/_next/")) {
    return join(app, ".next", ...clean.slice("/_next/".length).split("/"));
  }
  return resolve(dirname(cssFile), clean);
}

const classRule = (css, name) => new RegExp(`\\.${name.replace(/[-]/g, "\\-")}\\s*\\{`).test(css);

async function inBrowser(browser, app) {
  const html = join(app, ".next", "server", "app", "index.html");
  if (!existsSync(html)) {
    return { html: false };
  }
  const page = await browser.newPage();
  const notFound = [];
  const fontRequests = [];
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(`${error.name}: ${error.message}`));
  const staticRoot = join(app, ".next", "static");
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.origin !== ORIGIN) {
      notFound.push(url.href);
      await route.abort();
      return;
    }
    let path = null;
    if (url.pathname === "/") {
      path = html;
    } else if (url.pathname.startsWith("/_next/static/")) {
      path = join(staticRoot, ...decodeURIComponent(url.pathname.slice("/_next/static/".length)).split("/"));
      if (!path.startsWith(staticRoot + sep)) {
        path = null;
      }
    }
    if (path === null || !existsSync(path) || statSync(path).isDirectory()) {
      notFound.push(url.pathname);
      await route.fulfill({ status: 404 });
      return;
    }
    if (/\.woff2?$/.test(path)) {
      fontRequests.push(url.pathname);
    }
    await route.fulfill({ path });
  });
  await page.goto(`${ORIGIN}/`);
  await page.waitForLoadState("load");
  const read = await page.evaluate(async (families) => {
    const sheets = [...document.styleSheets].filter((sheet) => sheet.href?.includes("/_next/static/"));
    const rules = sheets.reduce((sum, sheet) => sum + sheet.cssRules.length, 0);
    const loads = {};
    for (const [family, { weights, text }] of Object.entries(families)) {
      for (const weight of weights) {
        const faces = await document.fonts.load(`${weight} 16px "${family}"`, text);
        loads[`${family} ${weight}`] = faces.filter((face) => face.status === "loaded").length;
      }
    }
    return { sheets: sheets.length, rules, loads };
  }, FAMILIES);
  await page.close();
  return { html: true, ...read, fontRequests: fontRequests.length, notFound, pageErrors };
}

const rounds = [];
const leftovers = [];
const browser = await chromium.launch();
try {
  for (const variant of VARIANTS) {
    const app = makeApp(variant);
    try {
      const built = spawnSync(process.execPath, [nextBin, "build", app], {
        cwd: app,
        env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1", NO_COLOR: "1", FORCE_COLOR: "0" },
        encoding: "utf8",
        maxBuffer: 256 * 1024 * 1024,
        timeout: 600_000,
      });
      const out = `${built.stdout ?? ""}\n${built.stderr ?? ""}`;
      const turbopackLine = out.split(/\r?\n/).find((line) => line.includes("Turbopack"))?.trim() ?? null;
      const buildId = existsSync(join(app, ".next", "BUILD_ID"));
      const staticDir = join(app, ".next", "static");
      const cssFiles = existsSync(staticDir) ? filesUnder(staticDir).filter((path) => path.endsWith(".css")) : [];
      const cssTexts = cssFiles.map((path) => ({ path, text: readFileSync(path, "utf8") }));
      const tailwindCss = cssTexts.filter(({ text }) => text.includes("--gray-50") && !/@theme|@source/.test(text));
      const allCss = cssTexts.map(({ text }) => text).join("\n");

      const fonts = {};
      for (const family of Object.keys(FAMILIES)) {
        const faces = cssTexts.flatMap(({ path, text }) =>
          fontFaces(text)
            .filter((face) => face.family === family)
            .map((face) => ({ ...face, cssFile: path })),
        );
        const woff2Files = faces.flatMap((face) => face.woff2.map((url) => fileOf(app, face.cssFile, url)));
        const existing = woff2Files.filter((path) => existsSync(path));
        const hashes = new Set(existing.map(sha256));
        const woffFiles = faces.flatMap((face) => face.woff.map((url) => fileOf(app, face.cssFile, url)));
        fonts[family] = {
          faces: faces.length,
          woff2Urls: woff2Files.length,
          woff2UrlsExisting: existing.length,
          baselineWoff2Present: [...baseline[family].woff2].filter((hash) => hashes.has(hash)).length,
          woffUrls: woffFiles.length,
          woffUrlsExisting: woffFiles.filter((path) => existsSync(path)).length,
          sampleUrl: faces[0]?.woff2[0] ?? null,
        };
      }
      const media = existsSync(staticDir) ? filesUnder(staticDir).filter((path) => path.endsWith(".woff2")) : [];
      const allBaseline = new Set(Object.values(baseline).flatMap((b) => [...b.woff2]));
      const emittedBaselineWoff2 = media.filter((path) => allBaseline.has(sha256(path))).length;
      const classes = Object.fromEntries([...APP_ONLY, PACKAGE_CLASS].map((name) => [name, classRule(allCss, name)]));
      const browserRead = built.status === 0 ? await inBrowser(browser, app) : { html: false };

      const marker =
        built.status === 0 &&
        turbopackLine !== null &&
        buildId &&
        tailwindCss.length > 0 &&
        browserRead.html &&
        browserRead.sheets > 0 &&
        browserRead.rules > 0;

      const fontsComplete = Object.keys(FAMILIES).every((family) => {
        const f = fonts[family];
        return (
          f.faces === baseline[family].faces &&
          f.woff2UrlsExisting === f.woff2Urls &&
          f.woff2Urls === baseline[family].faces &&
          f.baselineWoff2Present === baseline[family].woff2.size
        );
      });
      const fontsAbsent =
        Object.values(fonts).every((f) => f.faces === 0) && emittedBaselineWoff2 === 0;
      const loadsAll = Object.values(browserRead.loads ?? {}).every((count) => count > 0);
      const loadsNone = Object.values(browserRead.loads ?? {}).every((count) => count === 0);
      const appClasses = APP_ONLY.every((name) => classes[name]);
      const noAppClasses = APP_ONLY.every((name) => !classes[name]);
      const expected =
        classes[PACKAGE_CLASS] &&
        (variant.source ? appClasses : noAppClasses) &&
        (variant.fonts ? fontsComplete && loadsAll : fontsAbsent && loadsNone);

      rounds.push({
        variant: variant.name,
        measurement: marker,
        expected: marker ? expected : null,
        status: built.status,
        turbopackLine,
        buildId,
        cssFiles: cssFiles.length,
        tailwindCssFiles: tailwindCss.length,
        classes,
        fonts,
        emittedWoff2: media.length,
        emittedBaselineWoff2,
        browser: browserRead,
        errorLines:
          built.status === 0
            ? []
            : [...new Set(out.split(/\r?\n/).filter((line) => /error|failed|not found/i.test(line)))].slice(0, 20),
      });
    } finally {
      if (!removeApp(app)) {
        leftovers.push(app);
      }
    }
  }
  console.log(`chromium ${browser.version()}`);
} finally {
  await browser.close();
}

let measured = 0;
let notMeasured = 0;
let unexpected = 0;
for (const round of rounds) {
  console.log(JSON.stringify(round));
  if (!round.measurement) {
    notMeasured += 1;
  } else {
    measured += 1;
    if (!round.expected) {
      unexpected += 1;
    }
  }
}
const target = existsSync(join(WIDGET_MODULES, "next", "package.json"));
// 새로 생긴 캐시 자리는 빈 폴더만 재귀 없이 지운다. 내용이 있으면 남기고 찍는다.
const strays = WATCHED.filter((path) => !watchedBefore.has(path) && existsSync(path)).map((path) => {
  const empty = !lstatSync(path).isSymbolicLink() && readdirSync(path).length === 0;
  if (empty) {
    rmdirSync(path);
  }
  return { path, empty, removed: !existsSync(path) };
});
console.log(
  `남은 임시 폴더 ${JSON.stringify(leftovers)}, junction 대상 남음 ${target}, 밖에 새로 생긴 캐시 ${JSON.stringify(strays)}`,
);
console.log(`측정 ${measured}, 측정 아님 ${notMeasured}, 기대와 다름 ${unexpected}`);
process.exit(notMeasured > 0 || unexpected > 0 || leftovers.length > 0 || !target || strays.length > 0 ? 1 : 0);
