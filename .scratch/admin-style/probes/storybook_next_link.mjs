// admin-style Storybook next/link 프로브: 관리 화면의 스토리를 위젯처럼 `@storybook/react-vite`(Next 프레임워크가 아님)로
// 세울 때, `next/link` 의 `Link` 를 그리는 스토리가 오류 없이 `<a href="…">` 로 그려지는지 본다.
//   node .scratch/admin-style/probes/storybook_next_link.mjs
//
// 까닭: 관리 화면의 organisms(PluginList, RunList, EventItem)와 pages 가 `import Link from "next/link"` 를 쓴다. Next 밖의
// 번들러에서 그 모듈이 Next 의 라우터 문맥이나 `process.env` 없이 도는지는 명세가 고를 길(그대로 둔다, 별칭으로 바꾼다)을
// 가른다.
//
// 자리: `web/apps/` 아래 `package.json` 없는 임시 폴더(위젯과 같은 깊이)를 만들고 그 `node_modules` 를
// `web/apps/widget/node_modules` 로 잇는 junction 을 둔다. 그래서 next·react·`@agent-os/ui`·`@tailwindcss/vite` 는 위젯의 것으로,
// storybook·`@storybook/*`·vitest·playwright 는 위로 올라가 `web/node_modules` 의 것으로 풀린다(위젯의 Storybook 과 같다).
// 그 안에 위젯의 `.storybook/main.ts`·`preview.tsx` 와 같은 모양의 설정 둘을 둔다(react-vite, addon-a11y·addon-vitest, viteFinal
// 의 Tailwind 와 빈 PostCSS, 미리보기는 디자인 토큰 CSS 를 `@import` 하고 스토리 폴더를 `@source` 로 덮은 CSS 와 글꼴 CSS 를
// 싣고 `storyPreview(css)` 를 부른다). 스토리는 둘이다. 패키지의 `Button` 하나(양성 대조)와 `next/link` 의 `Link` 하나(RunList
// 처럼 `/runs/…`). 둘 다 play 가 그린 요소를 찾지 못하면 `PROBE_NO_…` 를 던진다. 위젯과 다른 것은 넷이다. 스토리가 TSX 한
// 파일씩이고, 설정이 `main.mjs` 이며, vitest 설정이 Vite 캐시를 임시 폴더에 두고(`cacheDir`), `vitest run` 에
// `--configLoader runner` 를 준다. 마지막 것은 첫 실행에서 기본 로더(bundle)가 설정 파일 옆의 가장 가까운 `node_modules`,
// 곧 junction 너머 위젯의 `node_modules` 에 빈 `.vite-temp` 폴더를 남겨서다. Storybook 의 캐시는 환경 변수 `CACHE_DIR` 로 임시
// 폴더에 둔다(storybook 10.6.1 설치본의 `resolvePathInStorybookCache` 가 empathic 의 `cache` 를 부르고 그것이 `CACHE_DIR` 을
// 먼저 읽는다). 스토리 테스트가 미리 묶은 의존성도 그 아래(`cache/storybook/<판>/…/sb-vitest/vitest/…/deps/`)에 생겨,
// vitest 설정의 `cacheDir` 보다 storybookTest 플러그인의 자리가 이긴다(2026-10-26 실행의 스택 줄에서 봤다). 끝에 위젯과
// `web/` 의 `node_modules` 에 `.vite-temp`·`.vite`·`.cache` 가 새로 생겼는지 보고, 생겼으면 빈 폴더만 지우고 그 경로를 찍으며
// 종료 코드를 1 로 둔다.
//
// 갈래: 설정 `sb-noalias` 는 별칭이 없고, `sb-alias` 는 viteFinal 에서 `next/link` 를 평범한 `<a>` 를 그리는 임시 파일로 바꾸는
// 별칭(resolve.alias)을 둔다. 갈래마다 두 길로 연다.
//   - 정적 빌드: `storybook build -c <설정> -o <폴더>` 의 결과를 Chromium 으로 연다. 사진 비교의 길(`web/packages/ui/visual/
//     index.ts`)처럼 `http://storybook.invalid/` 를 그 폴더로 route 하고 밖으로 나가는 요청은 abort 해 센다.
//   - 스토리 테스트: 뿌리 `web/vitest.config.ts` 의 `widget-storybook` 프로젝트와 같은 모양(storybookTest 플러그인, Vitest 브라우저
//     모드, Playwright 의 chromium 하나, headless)의 임시 vitest 설정으로 `vitest run` 을 돌리고 JSON 보고를 읽는다.
//
// 측정의 표지
//   - 정적 빌드의 회차: 미리보기의 `currentRender` 가 그 스토리 id 로 `finished` 에 닿았거나, 오류 화면(`body.sb-show-errordisplay`)
//     이 떴다. 둘 다 아니면(제한 시간, 빌드 실패) 측정 아님이다.
//   - 스토리 테스트의 회차: JSON 보고에 그 스토리 파일이 있고, 그 스토리 이름의 결과(passed|failed)가 있거나 파일 수준의 실패
//     메시지(불러오다 던짐)가 있다. 없으면 측정 아님이다. 파일 수준의 메시지는 `Failed to import test file <경로>` 한 줄이고
//     원인(`Caused by: …`)과 그 스택은 vitest 의 stdout 에만 있어(2026-10-26 첫 실행의 원본에서 봤다), 그 덩어리를
//     `vitest run` 줄의 `causeBlock` 에 옮긴다.
// 양성 대조: 같은 빌드·같은 vitest 실행의 `Button` 스토리가 그려진다(`button` 하나, 오류 화면 없음, 예외 없음).
// 갈래가 실제로 갈렸는지는 정적 빌드의 JS 에 next/link 의 prop 이름 `legacyBehavior` 가 있는지로 본다(별칭 없는 빌드에만 있어야
// 한다). 스토리 테스트 쪽은 실패의 스택이 미리 묶은 `next_link.js` 를 가리키는지로 읽는다(`causeBlock`).
// 기대: 양성 대조가 네 자리(정적·테스트 × 갈래 둘)에서 모두 그려지고, 별칭 갈래의 `Link` 가 두 길에서 모두 `<a href="/runs/run-1">`
// 로 그려지며, `legacyBehavior` 가 별칭 없는 빌드에만 있다. 별칭 없는 `Link` 는 정적 빌드에서 그려지고, 스토리 테스트에서는
// 그 스토리 파일을 불러오다 실패하며(파일 수준 메시지 `Failed to import test file`) 그 실행의 원인 줄이
// `ReferenceError: process is not defined` 다.
// 결과를 본 뒤 바꾼 기준: 별칭 없는 `Link` 는 셋째 실행(2026-10-26)까지 질문이라 기대를 두지 않고 결과만 적었다. 명세가 그
// 결과(스토리 테스트에서만 그 까닭으로 실패한다)에 기대어 별칭을 정했으므로, 넷째 실행부터 그 결과를 기대로 단언한다.
// stdout 은 판 줄, 회차마다 JSON 한 줄, 끝의 집계 줄이다. 측정 아닌 회차가 있거나 기대와 다른 것이 있으면 종료 코드가 1 이다.
//
// 지우기: 이 프로브가 만든 임시 폴더만 지운다. junction 을 먼저 재귀 없이 떼고(unlink, 안 되면 rmdir), 잇던 대상이 그대로
// 있는지 단언하고, 폴더 안에 다른 링크가 없을 때만 폴더를 재귀로 지운다. 링크가 남았으면 지우지 않고 경로를 찍는다.

import { spawnSync } from "node:child_process";
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
const WIDGET = join(WEB, "apps", "widget");
const WIDGET_MODULES = join(WIDGET, "node_modules");
const ORIGIN = "http://storybook.invalid";
const HREF = "/runs/run-1";
const STORIES = {
  plain: { id: "probe-plain--package-button", name: "Package Button", file: "Plain.stories.tsx" },
  link: { id: "probe-link--next-link", name: "Next Link", file: "Link.stories.tsx" },
};
const VARIANTS = ["noalias", "alias"];

/** `from` 에서 위로 올라가며 처음 만나는 `node_modules/<name>/package.json` 의 판. 없으면 null. */
function versionOf(from, name) {
  for (let dir = from; ; dir = dirname(dir)) {
    const manifest = join(dir, "node_modules", ...name.split("/"), "package.json");
    if (existsSync(manifest)) {
      return JSON.parse(readFileSync(manifest, "utf8")).version;
    }
    if (dirname(dir) === dir) {
      return null;
    }
  }
}

const PACKAGES = [
  "storybook",
  "@storybook/react-vite",
  "@storybook/addon-vitest",
  "@storybook/addon-a11y",
  "vitest",
  "@vitest/browser-playwright",
  "playwright",
  "vite",
  "@tailwindcss/vite",
  "tailwindcss",
  "next",
  "react",
  "react-dom",
];
const versions = Object.fromEntries(PACKAGES.map((name) => [name, versionOf(WIDGET, name)]));
const missing = Object.entries(versions).filter(([, version]) => version === null);
if (missing.length > 0 || !existsSync(join(WIDGET_MODULES, "@agent-os", "ui", "package.json"))) {
  console.error(`위젯 자리에서 풀리지 않는 패키지가 있다: ${missing.map(([name]) => name).join(", ")}`);
  process.exit(1);
}
console.log(`판 ${JSON.stringify(versions)}`);

function lexists(path) {
  try {
    lstatSync(path);
    return true;
  } catch {
    return false;
  }
}

/** 폴더 아래의 링크(심볼릭 링크와 junction)를 찾는다. 링크 안으로는 내려가지 않는다. */
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

// 임시 폴더 밖에 생기면 안 되는 캐시 자리. 처음에 없던 것이 끝에 있으면 프로브가 남긴 것이다.
const WATCHED = [WIDGET_MODULES, join(WEB, "node_modules")].flatMap((dir) =>
  [".vite-temp", ".vite", ".cache"].map((name) => join(dir, name)),
);
const watchedBefore = new Set(WATCHED.filter((path) => existsSync(path)));

const work = mkdtempSync(join(WEB, "apps", "probe-sb-next-link-"));
const junction = join(work, "node_modules");

/** junction 을 재귀 없이 떼고, 대상이 남았는지 보고, 다른 링크가 없으면 임시 폴더를 지운다. 지웠으면 true. */
function removeWork() {
  if (!work.startsWith(join(WEB, "apps", "probe-sb-next-link-"))) {
    console.error(`지우지 않는다. 이 프로브가 만든 폴더가 아니다: ${work}`);
    return false;
  }
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
  const targetIntact =
    existsSync(join(WIDGET_MODULES, "next", "package.json")) &&
    existsSync(join(WIDGET_MODULES, "@agent-os", "ui", "package.json"));
  if (!targetIntact) {
    console.error(`잇던 대상이 온전하지 않다: ${WIDGET_MODULES}`);
    return false;
  }
  const links = linksUnder(work);
  if (links.length > 0) {
    console.error(`지우지 않는다. 임시 폴더에 링크가 남았다: ${links.join(", ")}`);
    return false;
  }
  rmSync(work, { recursive: true, force: true });
  return !existsSync(work);
}

symlinkSync(WIDGET_MODULES, junction, "junction");
if (!lstatSync(junction).isSymbolicLink()) {
  // 지우기의 안전장치(linksUnder)가 junction 을 링크로 알아보지 못하면 아무것도 돌리지 않는다.
  rmdirSync(junction);
  console.error("lstat 이 junction 을 링크로 보지 않는다. 지우기 안전장치를 믿을 수 없어 멈춘다");
  process.exit(1);
}

function write(relative, text) {
  const path = join(work, relative);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, text);
}

// 관리 화면의 tsconfig 와 같은 모양(web/apps/admin/tsconfig.json). Vite 는 타입을 보지 않고 jsx 만 읽는다.
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
      },
      include: ["**/*.ts", "**/*.tsx"],
      exclude: ["node_modules"],
    },
    null,
    2,
  )}\n`,
);
write("styles/admin.css", '@import "@agent-os/ui/theme.css";\n@source "../stories";\n');
write(
  `stories/${STORIES.plain.file}`,
  `import { Button } from "@agent-os/ui";

export default { title: "Probe/Plain" };

export const PackageButton = {
  render: () => <Button>확인</Button>,
  play: ({ canvasElement }: { canvasElement: HTMLElement }) => {
    if (canvasElement.querySelector("button") === null) {
      throw new Error("PROBE_NO_BUTTON");
    }
  },
};
`,
);
write(
  `stories/${STORIES.link.file}`,
  `import Link from "next/link";

export default { title: "Probe/Link" };

export const NextLink = {
  render: () => <Link href={\`/runs/\${encodeURIComponent("run-1")}\`}>run-1</Link>,
  play: ({ canvasElement }: { canvasElement: HTMLElement }) => {
    const anchor = canvasElement.querySelector('a[href="${HREF}"]');
    if (anchor === null || anchor.textContent !== "run-1") {
      throw new Error("PROBE_NO_ANCHOR");
    }
  },
};
`,
);
write(
  "link-shim.tsx",
  `import type { ReactNode } from "react";

export default function Link({ href, children }: { href: string; children: ReactNode }) {
  return <a href={href}>{children}</a>;
}
`,
);
for (const variant of VARIANTS) {
  const alias = variant === "alias" ? JSON.stringify(join(work, "link-shim.tsx")) : "null";
  write(
    `sb-${variant}/main.mjs`,
    `import tailwindcss from "@tailwindcss/vite";

const ALIAS = ${alias};

export default {
  framework: "@storybook/react-vite",
  stories: ["../stories/*.stories.tsx"],
  addons: ["@storybook/addon-a11y", "@storybook/addon-vitest"],
  core: { disableTelemetry: true },
  viteFinal: (viteConfig) => {
    const given = viteConfig.resolve?.alias;
    const aliases =
      given === undefined
        ? []
        : Array.isArray(given)
          ? given
          : Object.entries(given).map(([find, replacement]) => ({ find, replacement }));
    return {
      ...viteConfig,
      css: { ...viteConfig.css, postcss: { plugins: [] } },
      plugins: [...(viteConfig.plugins ?? []), tailwindcss()],
      ...(ALIAS === null
        ? {}
        : { resolve: { ...viteConfig.resolve, alias: [{ find: /^next\\/link$/, replacement: ALIAS }, ...aliases] } }),
    };
  },
};
`,
  );
  write(
    `sb-${variant}/preview.tsx`,
    `import "../styles/admin.css";
import "@agent-os/ui/fonts.css";
import { storyPreview } from "@agent-os/ui/storybook";
import css from "../styles/admin.css?inline";

const base = storyPreview(css);

export default { ...base };
`,
  );
  write(
    `vitest.${variant}.config.mjs`,
    `import { storybookTest } from "@storybook/addon-vitest/vitest-plugin";
import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vitest/config";

export default defineConfig({
  root: ${JSON.stringify(work)},
  cacheDir: ${JSON.stringify(join(work, "cache", `vite-${variant}`))},
  plugins: [storybookTest({ configDir: ${JSON.stringify(join(work, `sb-${variant}`))} })],
  test: {
    name: "probe-storybook-${variant}",
    testTimeout: 60_000,
    hookTimeout: 120_000,
    browser: {
      enabled: true,
      headless: true,
      provider: playwright(),
      instances: [{ browser: "chromium" }],
      screenshotFailures: false,
    },
  },
});
`,
  );
}

const env = {
  ...process.env,
  CACHE_DIR: join(work, "cache"),
  NO_COLOR: "1",
  FORCE_COLOR: "0",
  STORYBOOK_DISABLE_TELEMETRY: "1",
};
const storybookBin = join(dirname(createRequire(join(WEB, "package.json")).resolve("storybook/package.json")), "dist", "bin", "dispatcher.js");
const vitestBin = join(dirname(createRequire(join(WEB, "package.json")).resolve("vitest/package.json")), "vitest.mjs");

function run(args) {
  const result = spawnSync(process.execPath, args, {
    cwd: work,
    env,
    encoding: "utf8",
    maxBuffer: 256 * 1024 * 1024,
    timeout: 600_000,
  });
  return { status: result.status, error: result.error?.message, out: `${result.stdout ?? ""}\n${result.stderr ?? ""}` };
}

/** 출력에서 오류로 보이는 줄을 겹치지 않게 모은다. */
function errorLines(text, limit = 20) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => /error|exception|not defined|invariant|PROBE_/i.test(line));
  return [...new Set(lines)].slice(0, limit);
}

/** vitest 출력에서 처음 `Caused by:` 줄과 그 뒤 여덟 줄(스택). 없으면 빈 배열. */
function causeBlock(text) {
  const lines = text.split(/\r?\n/).map((line) => line.trim());
  const at = lines.findIndex((line) => line.startsWith("Caused by:"));
  return at < 0 ? [] : lines.slice(at, at + 9).filter((line) => line !== "");
}

/** 폴더 아래 `.js` 파일 가운데 `needle` 을 품은 것이 있는가. */
function anyJsIncludes(root, needle) {
  for (const name of readdirSync(root)) {
    const path = join(root, name);
    const stat = lstatSync(path);
    if (stat.isDirectory() && anyJsIncludes(path, needle)) {
      return true;
    }
    if (stat.isFile() && name.endsWith(".js") && readFileSync(path, "utf8").includes(needle)) {
      return true;
    }
  }
  return false;
}

// 별칭이 실제로 갈래를 갈랐는지 보는 글자. next 16.3.6 의 `dist/client/link.js` 에 18번 있고 Link 의 prop 이름이라 줄여도
// 남는다. 패키지 소스와 storybook 의 dist 에는 없다(2026-10-26 grep 으로 봤다). 별칭 없는 정적 빌드에는 있고 별칭 갈래에는
// 없어야 한다.
const NEXT_LINK_NEEDLE = "legacyBehavior";

const rounds = [];
const builds = {};
let removed = false;
try {
  for (const variant of VARIANTS) {
    const out = join(work, `static-${variant}`);
    const built = run([storybookBin, "build", "-c", join(work, `sb-${variant}`), "-o", out]);
    const index = join(out, "index.json");
    const entries = existsSync(index) ? Object.keys(JSON.parse(readFileSync(index, "utf8")).entries) : [];
    const ok = built.status === 0 && existsSync(join(out, "iframe.html"));
    builds[variant] = { out, ok, entries, nextLinkBundled: ok ? anyJsIncludes(out, NEXT_LINK_NEEDLE) : null };
    console.log(
      JSON.stringify({
        step: "storybook build",
        variant,
        status: built.status,
        spawnError: built.error,
        indexEntries: entries,
        nextLinkBundled: builds[variant].nextLinkBundled,
        errorLines: built.status === 0 ? [] : errorLines(built.out),
      }),
    );
  }

  const { chromium } = createRequire(join(WEB, "package.json"))("playwright");
  const browser = await chromium.launch();
  try {
    for (const variant of VARIANTS) {
      for (const [kind, story] of Object.entries(STORIES)) {
        const build = builds[variant];
        if (!build.ok) {
          rounds.push({ path: "static", variant, story: kind, measurement: false, reason: "빌드 실패" });
          continue;
        }
        const page = await browser.newPage();
        const consoleErrors = [];
        const consoleWarnings = [];
        const pageErrors = [];
        const outside = [];
        page.on("console", (message) => {
          if (message.type() === "error") {
            consoleErrors.push(message.text());
          } else if (message.type() === "warning") {
            consoleWarnings.push(message.text());
          }
        });
        page.on("pageerror", (error) => pageErrors.push(`${error.name}: ${error.message}`));
        await page.addInitScript(() => {
          const events = [];
          window.__probeEvents = events;
          let channel;
          Object.defineProperty(window, "__STORYBOOK_ADDONS_CHANNEL__", {
            configurable: true,
            get: () => channel,
            set: (value) => {
              channel = value;
              value.on("storyRenderPhaseChanged", (payload) => events.push(`phase:${payload?.newPhase}`));
              for (const name of ["storyThrewException", "storyErrored", "playFunctionThrewException", "storyMissing"]) {
                value.on(name, (payload) =>
                  events.push(`${name}:${payload?.message ?? payload?.description ?? payload?.title ?? String(payload)}`),
                );
              }
            },
          });
        });
        await page.route("**/*", async (route) => {
          const url = new URL(route.request().url());
          if (url.origin !== ORIGIN) {
            outside.push(url.href);
            await route.abort();
            return;
          }
          const path = join(build.out, decodeURIComponent(url.pathname));
          if (!path.startsWith(build.out + sep) || !existsSync(path) || statSync(path).isDirectory()) {
            await route.fulfill({ status: 404 });
            return;
          }
          await route.fulfill({ path });
        });
        await page.goto(`${ORIGIN}/iframe.html?id=${story.id}&viewMode=story`);
        let settled = true;
        try {
          await page.waitForFunction(
            (id) => {
              const render = window.__STORYBOOK_PREVIEW__?.currentRender;
              return (
                (render?.id === id && render?.phase === "finished") ||
                document.body.classList.contains("sb-show-errordisplay")
              );
            },
            story.id,
            { timeout: 30_000 },
          );
        } catch {
          settled = false;
        }
        const read = await page.evaluate((id) => {
          const render = window.__STORYBOOK_PREVIEW__?.currentRender;
          const root = document.getElementById("storybook-root");
          return {
            finished: render?.id === id && render?.phase === "finished",
            errorDisplay: document.body.classList.contains("sb-show-errordisplay"),
            errorMessage: document.getElementById("error-message")?.textContent?.trim() ?? "",
            errorStack: (document.getElementById("error-stack")?.textContent ?? "").split("\n").slice(0, 4).join(" | "),
            anchors: [...(root?.querySelectorAll("a") ?? [])].map((a) => ({ href: a.getAttribute("href"), text: a.textContent })),
            buttons: root?.querySelectorAll("button").length ?? 0,
            events: window.__probeEvents ?? [],
          };
        }, story.id);
        await page.close();
        const marker = settled && (read.finished || read.errorDisplay);
        const threw = read.events.filter((event) => !event.startsWith("phase:"));
        const drawn =
          kind === "plain"
            ? read.buttons === 1
            : read.anchors.some((a) => a.href === HREF && a.text === "run-1");
        const rendered = marker && read.finished && !read.errorDisplay && threw.length === 0 && pageErrors.length === 0 && drawn;
        rounds.push({
          path: "static",
          variant,
          story: kind,
          measurement: marker,
          rendered,
          ...read,
          pageErrors,
          consoleErrors: consoleErrors.map((text) => text.split("\n").slice(0, 3).join(" | ")),
          consoleWarnings: consoleWarnings.map((text) => text.split("\n")[0]),
          outside,
        });
      }
    }
    console.log(`chromium ${browser.version()}`);
  } finally {
    await browser.close();
  }

  for (const variant of VARIANTS) {
    const report = join(work, `vitest-${variant}.json`);
    const tested = run([
      vitestBin,
      "run",
      "--config",
      join(work, `vitest.${variant}.config.mjs`),
      "--configLoader",
      "runner",
      "--reporter=default",
      "--reporter=json",
      `--outputFile.json=${report}`,
    ]);
    const data = existsSync(report) ? JSON.parse(readFileSync(report, "utf8")) : null;
    const cause = causeBlock(tested.out);
    console.log(
      JSON.stringify({
        step: "vitest run",
        variant,
        status: tested.status,
        spawnError: tested.error,
        report: data !== null,
        errorLines: errorLines(tested.out),
        causeBlock: cause,
      }),
    );
    for (const [kind, story] of Object.entries(STORIES)) {
      const file = data?.testResults?.find((result) => result.name.endsWith(story.file));
      const assertion = file?.assertionResults?.find((result) => result.title === story.name);
      const fileMessage = (file?.message ?? "").trim();
      const marker =
        file !== undefined &&
        ((assertion !== undefined && ["passed", "failed"].includes(assertion.status)) || fileMessage !== "");
      rounds.push({
        path: "vitest",
        variant,
        story: kind,
        measurement: marker,
        rendered: marker && assertion?.status === "passed",
        status: assertion?.status ?? null,
        failure: (assertion?.failureMessages ?? []).map((text) => text.split("\n").slice(0, 4).join(" | ")),
        fileMessage: fileMessage.split("\n").slice(0, 4).join(" | "),
        cause,
      });
    }
  }
} finally {
  removed = removeWork();
}

/** 회차가 기대대로인가(머리 주석의 기대). */
function asExpected(round) {
  if (round.story === "plain" || round.variant === "alias" || round.path === "static") {
    return round.rendered === true;
  }
  // 별칭 없는 Link 의 스토리 테스트: 파일을 불러오다 그 까닭으로 실패한다(넷째 실행부터의 기대).
  return (
    round.rendered === false &&
    round.fileMessage.includes("Failed to import test file") &&
    round.cause.some((line) => line.includes("ReferenceError: process is not defined"))
  );
}

let measured = 0;
let notMeasured = 0;
let unexpected = 0;
for (const round of rounds) {
  console.log(JSON.stringify(round));
  if (!round.measurement) {
    notMeasured += 1;
    continue;
  }
  measured += 1;
  if (!asExpected(round)) {
    unexpected += 1;
  }
}
// 갈래가 실제로 갈렸는지: 별칭 없는 빌드에만 next/link 의 코드가 든다. 빌드가 실패한 갈래는 위 회차가 측정 아님으로 센다.
for (const variant of VARIANTS) {
  const bundled = builds[variant]?.nextLinkBundled;
  if (bundled !== null && bundled !== undefined && bundled !== (variant === "noalias")) {
    console.log(`갈래가 갈리지 않았다: ${variant} 빌드의 next/link 코드 ${bundled}`);
    unexpected += 1;
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
console.log(`임시 폴더 지움 ${removed}, junction 대상 남음 ${target}, 밖에 새로 생긴 캐시 ${JSON.stringify(strays)}`);
console.log(`측정 ${measured}, 측정 아님 ${notMeasured}, 기대와 다름 ${unexpected}`);
process.exit(notMeasured > 0 || unexpected > 0 || !removed || !target || strays.length > 0 ? 1 : 0);
