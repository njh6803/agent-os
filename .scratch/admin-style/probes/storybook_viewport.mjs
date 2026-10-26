// admin-style Storybook 폭 프로브: 관리 화면의 스토리 테스트(Vitest 브라우저 모드 + `storybookTest`)를 폭마다 돌리는 길을 본다.
//   node .scratch/admin-style/probes/storybook_viewport.mjs
//
// 까닭: ADR 0026 의 첫째 2026-10-12 이력은 관리 화면의 스토리 테스트와 사진 비교를 폭 320px 과 1280px 에서 돌린다고 정했다.
// 사진 비교는 Playwright 프로젝트의 viewport 로 되지만 스토리 테스트를 폭마다 돌리는 선례가 저장소에 없다. 뿌리
// `web/vitest.config.ts` 의 storybook 프로젝트에는 viewport 가 없는데 `.claude/rules/web-design.md` 는 "스토리 테스트의 창은
// 1200×900" 이라 적는다. 그 값은 `@storybook/addon-vitest` 10.6.1 설치본 `dist/vitest-plugin/test-utils.js` 의
// `DEFAULT_VIEWPORT_DIMENSIONS`(1200×900)이고, 스토리마다 `setViewport` 가 `page.viewport(...)` 를 부르며 viewport 전역값이
// 고른 항목이 없으면 그 값을 쓴다(코드를 읽었다). 그래서 `test.browser.viewport` 가 덮일 수 있다는 것을 이 프로브가 잰다.
//
// 자리: `storybook_next_link.mjs` 의 alias 갈래와 같은 임시 폴더(`web/apps/` 아래 `package.json` 없는 폴더, `node_modules` 는
// `web/apps/widget/node_modules` 로 잇는 junction, 위젯 모양의 `.storybook`, viteFinal 의 Tailwind·빈 PostCSS·next/link 별칭).
// 다른 것은 미리보기가 `parameters.viewport.options` 에 `probe-narrow`(320×640)와 `probe-wide`(1280×900)를 더하는 것이다. 스토리는
// 셋이다. `Probe/Viewport` 의 `Measure`(play 가 `innerWidth`·`innerHeight`·`matchMedia("(min-width: 768px)")`·문서 뿌리의
// `--control-h`, 그리고 같은 문서에 `data-density="compact"`·`"regular"` 를 단 탐침의 `--control-h` 를 `PROBE_VIEWPORT` 줄로
// 찍는다. 스토리 파일을 불러올 때의 창 크기 `atImport` 도 함께 찍는다. 테스트가 돌기 전이라 setViewport 앞의 값이고, 폭이 설정을
// 따르지 않을 때 "설정이 아예 닿지 않았다"와 "닿았다가 setViewport 가 덮었다"를 가르는 갈래다), `Probe/Storage` 의 `Write`(play 가 무작위 값을 localStorage 에 쓰고 `PROBE_STORAGE_WRITE` 로 찍는다)와 그 뒤의
// `Read`(앞 값을 읽고, 자기 키를 쓰고 다시 읽어 `PROBE_STORAGE_READ` 로 찍는다).
//
// 실행 둘(vitest run 한 번씩, 같은 configDir 의 storybookTest 를 프로젝트마다 둔다)
//   - `browser-viewport`: `probe-wide`(test.browser.viewport 1280×900), `probe-narrow`(320×640), `probe-default`(viewport 없음, 양성
//     대조로 기본 폭을 찍는다).
//   - `sb-globals`: `probe-g-wide`, `probe-g-narrow`. viewport 를 주지 않고 storybookTest 의 `initialGlobals` 로
//     `viewport: { value: "probe-wide" | "probe-narrow" }` 를 준다(Storybook 의 viewport 전역값 길).
// 찍힌 줄은 설정 파일 안의 보고자(onUserConsoleLog·onTestRunEnd)가 taskId 로 테스트와 그 프로젝트 이름에 잇고, 테스트마다
// 상태와 오류 첫 줄, 처리되지 않은 오류와 함께 임시 폴더의 JSON 에 쓴다. 보고자가 받는 프로젝트 이름에는 브라우저 인스턴스가
// 붙어(`probe-wide (chromium)`) 그것을 떼고 잇는다(첫 실행의 원본에서 봤다). `vitest run` 에는 `--configLoader runner` 를 준다(기본
// 로더는 junction 너머 위젯의 `node_modules` 에 빈 `.vite-temp` 를 남겼다, `storybook_next_link.mjs` 머리 주석). vitest 설정의
// 뿌리 `cacheDir` 를 임시 폴더에 둔다. 첫 실행은 그것이 없어 vitest 의 결과 캐시(`.vite/vitest/<해시>/results.json`)가 junction
// 너머 위젯의 `node_modules` 에 생겼다. Storybook 의 캐시는 `CACHE_DIR` 로 임시 폴더에 둔다.
//
// 측정의 표지
//   - 실행 회차: 보고자가 JSON 을 썼다(onTestRunEnd 가 돌았다). 결과는 설정한 프로젝트마다 돈 스토리 수와 상태, 처리되지 않은
//     오류, stdout 의 오류 줄이다. 같은 configDir 의 플러그인이 부딪혔는지(오류, 한쪽만 돈 것)를 이것으로 본다.
//   - 폭 회차(프로젝트마다): 그 프로젝트의 `PROBE_VIEWPORT` 줄이 있고, 두 탐침의 `--control-h` 가 다르며(밀도를 가를 수 있다),
//     뿌리의 `--control-h` 가 비지 않았다.
//   - 저장소 회차(프로젝트마다): 그 프로젝트의 `PROBE_STORAGE_WRITE` 와 `PROBE_STORAGE_READ` 줄이 있고, 읽기가 쓰기 뒤에 돌았으며
//     (`at` 비교), 읽기 스토리가 자기 키를 쓰고 다시 읽었다(양성 대조, localStorage 가 그 자리에서 동작한다).
// 기대
//   - 실행마다 설정한 프로젝트가 모두 스토리 셋을 돌렸고 처리되지 않은 오류가 없다(부딪히지 않는다).
//   - 폭 회차마다 `matchMedia` 가 `innerWidth >= 768` 과 같고, 뿌리의 `--control-h` 가 그 폭의 탐침(768 이상 촘촘, 미만 보통)과 같으며,
//     뿌리에 `data-density` 가 없다(밀도가 폭을 따른다).
//   - `probe-default` 는 1200×900 이다(위 코드 읽기의 예측).
//   - `browser-viewport` 의 설정한 프로젝트는 스토리 파일을 불러올 때 설정한 크기였다가 play 에서 1200×900 이다(닿았다가 덮였다).
//   - `sb-globals` 의 프로젝트는 play 에서 고른 항목의 크기다(`followsConfig`).
//   - 같은 프로젝트에서 앞 스토리가 쓴 localStorage 값이 다음 스토리에 보인다(`visible`).
//   읽은 값이 다른 프로젝트가 쓴 값이면 그 프로젝트 이름을 `seenFrom` 에 적는다.
// 결과를 본 뒤 바꾼 기준: 폭이 설정을 따르는지와 `visible` 은 셋째 실행(2026-10-26)까지 질문이라 기대를 두지 않고 결과만
// 적었다. 명세가 그 결과(덮이는 길과 따르는 길, 스토리 사이에 남는 저장소)에 기대어 정했으므로, 넷째 실행부터 위 셋을 기대로
// 단언한다.
// stdout 은 판 줄, 실행마다의 줄, 회차마다 JSON 한 줄, 끝의 집계 줄이다. 측정 아닌 회차가 있거나 기대와 다른 것이 있으면 종료
// 코드가 1 이다.
//
// 지우기: 이 프로브가 만든 임시 폴더만 지운다. junction 을 먼저 재귀 없이 떼고(unlink, 안 되면 rmdir), 잇던 대상이 그대로
// 있는지 단언하고, 폴더 안에 다른 링크가 없을 때만 폴더를 재귀로 지운다. 링크가 남았으면 지우지 않고 경로를 찍는다. 끝에 위젯과
// `web/` 의 `node_modules` 에 `.vite-temp`·`.vite`·`.cache` 가 새로 생겼는지 보고, 생겼으면 빈 폴더만 지우고 그 경로를 찍으며 종료
// 코드를 1 로 둔다.

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
  symlinkSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";

const REPO = resolve(import.meta.dirname, "..", "..", "..");
const WEB = join(REPO, "web");
const WIDGET = join(WEB, "apps", "widget");
const WIDGET_MODULES = join(WIDGET, "node_modules");
const PREFIX = join(WEB, "apps", "probe-sb-viewport-");
const VIEWPORT_OPTIONS = {
  "probe-narrow": { width: 320, height: 640 },
  "probe-wide": { width: 1280, height: 900 },
};
const RUNS = [
  {
    name: "browser-viewport",
    projects: [
      { name: "probe-wide", viewport: { width: 1280, height: 900 }, configured: { width: 1280, height: 900 } },
      { name: "probe-narrow", viewport: { width: 320, height: 640 }, configured: { width: 320, height: 640 } },
      { name: "probe-default", viewport: null, configured: null },
    ],
  },
  {
    name: "sb-globals",
    projects: [
      { name: "probe-g-wide", globals: "probe-wide", configured: VIEWPORT_OPTIONS["probe-wide"] },
      { name: "probe-g-narrow", globals: "probe-narrow", configured: VIEWPORT_OPTIONS["probe-narrow"] },
    ],
  },
];
const STORY_NAMES = ["Measure", "Write", "Read"];

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
  "react",
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

const work = mkdtempSync(PREFIX);
const junction = join(work, "node_modules");

/** junction 을 재귀 없이 떼고, 대상이 남았는지 보고, 다른 링크가 없으면 임시 폴더를 지운다. 지웠으면 true. */
function removeWork() {
  if (!work.startsWith(PREFIX)) {
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
  rmdirSync(junction);
  console.error("lstat 이 junction 을 링크로 보지 않는다. 지우기 안전장치를 믿을 수 없어 멈춘다");
  process.exit(1);
}

function write(relative, text) {
  const path = join(work, relative);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, text);
}

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
  "link-shim.tsx",
  `import type { ReactNode } from "react";

export default function Link({ href, children }: { href: string; children: ReactNode }) {
  return <a href={href}>{children}</a>;
}
`,
);
write(
  "stories/Viewport.stories.tsx",
  `export default { title: "Probe/Viewport" };

// 스토리 파일을 불러올 때(테스트가 돌기 전, addon-vitest 의 setViewport 전)의 창 크기.
const AT_IMPORT = { innerWidth: window.innerWidth, innerHeight: window.innerHeight };

function controlHeight(density: string | null): string {
  const probe = document.createElement("div");
  if (density !== null) {
    probe.setAttribute("data-density", density);
  }
  document.body.append(probe);
  const value = getComputedStyle(probe).getPropertyValue("--control-h").trim();
  probe.remove();
  return value;
}

export const Measure = {
  render: () => <p>폭 재기</p>,
  play: () => {
    const root = document.documentElement;
    const values = {
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight,
      wide768: matchMedia("(min-width: 768px)").matches,
      rootControlH: getComputedStyle(root).getPropertyValue("--control-h").trim(),
      compactRef: controlHeight("compact"),
      regularRef: controlHeight("regular"),
      rootDensityAttr: root.getAttribute("data-density"),
      rootTheme: root.getAttribute("data-theme"),
      atImport: AT_IMPORT,
    };
    console.log(\`PROBE_VIEWPORT \${JSON.stringify(values)}\`);
  },
};
`,
);
write(
  "stories/Storage.stories.tsx",
  `export default { title: "Probe/Storage" };

const KEY = "probe-storage-key";
const SELF = "probe-storage-self";

export const Write = {
  render: () => <p>쓰기</p>,
  play: () => {
    const value = \`\${Date.now()}-\${Math.random().toString(36).slice(2)}\`;
    localStorage.setItem(KEY, value);
    console.log(\`PROBE_STORAGE_WRITE \${JSON.stringify({ value, at: Date.now(), origin: location.origin })}\`);
  },
};

export const Read = {
  render: () => <p>읽기</p>,
  play: () => {
    const seen = localStorage.getItem(KEY);
    localStorage.setItem(SELF, "self");
    const self = localStorage.getItem(SELF);
    console.log(
      \`PROBE_STORAGE_READ \${JSON.stringify({ seen, self, at: Date.now(), origin: location.origin, keys: localStorage.length })}\`,
    );
  },
};
`,
);
const configDir = join(work, "sb");
write(
  "sb/main.mjs",
  `import tailwindcss from "@tailwindcss/vite";

const ALIAS = ${JSON.stringify(join(work, "link-shim.tsx"))};

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
      resolve: { ...viteConfig.resolve, alias: [{ find: /^next\\/link$/, replacement: ALIAS }, ...aliases] },
    };
  },
};
`,
);
const viewportOptions = Object.fromEntries(
  Object.entries(VIEWPORT_OPTIONS).map(([key, { width, height }]) => [
    key,
    { name: key, styles: { width: `${width}px`, height: `${height}px` }, type: "other" },
  ]),
);
write(
  "sb/preview.tsx",
  `import "../styles/admin.css";
import "@agent-os/ui/fonts.css";
import { storyPreview } from "@agent-os/ui/storybook";
import css from "../styles/admin.css?inline";

const base = storyPreview(css);

export default {
  ...base,
  parameters: { ...base.parameters, viewport: { options: ${JSON.stringify(viewportOptions)} } },
};
`,
);

for (const run of RUNS) {
  const report = join(work, `report-${run.name}.json`);
  const projects = run.projects.map((project) => {
    const plugin =
      project.globals === undefined
        ? `storybookTest({ configDir: ${JSON.stringify(configDir)} })`
        : `storybookTest({ configDir: ${JSON.stringify(configDir)}, initialGlobals: { viewport: { value: ${JSON.stringify(project.globals)}, isRotated: false } } })`;
    const viewport = project.viewport ? `, viewport: ${JSON.stringify(project.viewport)}` : "";
    return `    {
      extends: true,
      plugins: [${plugin}],
      test: {
        name: ${JSON.stringify(project.name)},
        browser: { enabled: true, headless: true, provider: playwright(), instances: [{ browser: "chromium" }]${viewport} },
      },
    }`;
  });
  write(
    `vitest.${run.name}.config.mjs`,
    `import { writeFileSync } from "node:fs";
import { storybookTest } from "@storybook/addon-vitest/vitest-plugin";
import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vitest/config";

const logs = [];
const probeReporter = {
  onUserConsoleLog(log) {
    if (log.content.includes("PROBE_")) {
      logs.push({ taskId: log.taskId ?? null, content: log.content.trim() });
    }
  },
  onTestRunEnd(testModules, unhandledErrors, reason) {
    const tests = [];
    const byId = new Map();
    const moduleErrors = [];
    for (const module of testModules) {
      for (const error of module.errors?.() ?? []) {
        moduleErrors.push({ project: module.project?.name ?? null, module: module.moduleId, message: String(error?.message ?? error).split("\\n")[0] });
      }
      for (const test of module.children.allTests()) {
        const result = test.result();
        const row = {
          project: test.project?.name ?? null,
          module: module.moduleId,
          name: test.name,
          state: result?.state ?? null,
          errors: (result?.errors ?? []).map((error) => String(error?.message ?? error).split("\\n")[0]),
        };
        tests.push(row);
        byId.set(test.id, row);
      }
    }
    writeFileSync(
      ${JSON.stringify(report)},
      JSON.stringify({
        reason,
        tests,
        moduleErrors,
        unhandled: unhandledErrors.map((error) => String(error?.message ?? error).split("\\n")[0]),
        logs: logs.map((log) => ({ ...log, project: byId.get(log.taskId)?.project ?? null, test: byId.get(log.taskId)?.name ?? null })),
      }),
    );
  },
};

export default defineConfig({
  root: ${JSON.stringify(work)},
  cacheDir: ${JSON.stringify(join(work, "cache", `vite-${run.name}`))},
  test: {
    fileParallelism: false,
    testTimeout: 60_000,
    hookTimeout: 120_000,
    reporters: ["default", probeReporter],
    projects: [
${projects.join(",\n")}
    ],
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
const vitestBin = join(dirname(createRequire(join(WEB, "package.json")).resolve("vitest/package.json")), "vitest.mjs");

function errorLines(text, limit = 20) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => /error|exception|not defined|invariant|failed|outdated|optimiz/i.test(line));
  return [...new Set(lines)].slice(0, limit);
}

function parsed(content, prefix) {
  const line = content.split(/\r?\n/).find((text) => text.startsWith(prefix));
  return line === undefined ? null : JSON.parse(line.slice(prefix.length).trim());
}

const rounds = [];
const reports = {};
let removed = false;
try {
  for (const run of RUNS) {
    const tested = spawnSync(
      process.execPath,
      [vitestBin, "run", "--config", join(work, `vitest.${run.name}.config.mjs`), "--configLoader", "runner"],
      { cwd: work, env, encoding: "utf8", maxBuffer: 256 * 1024 * 1024, timeout: 900_000 },
    );
    const out = `${tested.stdout ?? ""}\n${tested.stderr ?? ""}`;
    const reportPath = join(work, `report-${run.name}.json`);
    const raw = existsSync(reportPath) ? JSON.parse(readFileSync(reportPath, "utf8")) : null;
    // 보고자가 받는 프로젝트 이름에는 브라우저 인스턴스가 붙는다(`probe-wide (chromium)`, 첫 실행의 원본에서 봤다).
    const bare = (name) => (name ?? "").replace(/ \(chromium\)$/, "");
    const report =
      raw === null
        ? null
        : {
            ...raw,
            tests: raw.tests.map((test) => ({ ...test, project: bare(test.project) })),
            logs: raw.logs.map((log) => ({ ...log, project: bare(log.project) })),
          };
    reports[run.name] = report;
    const ran = Object.fromEntries(
      run.projects.map((project) => [
        project.name,
        Object.fromEntries(
          (report?.tests ?? [])
            .filter((test) => test.project === project.name)
            .map((test) => [test.name, test.errors.length > 0 ? `${test.state}: ${test.errors[0]}` : test.state]),
        ),
      ]),
    );
    const allRan = run.projects.every((project) =>
      STORY_NAMES.every((name) => ["passed", "failed"].includes((ran[project.name][name] ?? "").split(":")[0])),
    );
    const noErrors =
      report !== null &&
      report.unhandled.length === 0 &&
      report.moduleErrors.length === 0 &&
      report.tests.every((test) => test.state === "passed");
    rounds.push({
      kind: "run",
      run: run.name,
      measurement: report !== null,
      expected: report !== null ? allRan && noErrors : null,
      status: tested.status,
      spawnError: tested.error?.message,
      reason: report?.reason ?? null,
      ran,
      unhandled: report?.unhandled ?? [],
      moduleErrors: report?.moduleErrors ?? [],
      foreignProjects: [...new Set((report?.tests ?? []).map((test) => test.project))].filter(
        (name) => !run.projects.some((project) => project.name === name),
      ),
      errorLines: errorLines(out),
    });

    const logsOf = (project, prefix) =>
      (report?.logs ?? []).filter((log) => log.project === project && log.content.startsWith(prefix));
    for (const project of run.projects) {
      const viewportLog = logsOf(project.name, "PROBE_VIEWPORT")[0];
      const v = viewportLog ? parsed(viewportLog.content, "PROBE_VIEWPORT") : null;
      const marker = v !== null && v.compactRef !== "" && v.compactRef !== v.regularRef && v.rootControlH !== "";
      const densityFollowsWidth =
        marker &&
        v.wide768 === v.innerWidth >= 768 &&
        v.rootControlH === (v.wide768 ? v.compactRef : v.regularRef) &&
        v.rootDensityAttr === null;
      const followsConfig =
        marker && project.configured !== null
          ? v.innerWidth === project.configured.width && v.innerHeight === project.configured.height
          : null;
      const is1200 = marker && v.innerWidth === 1200 && v.innerHeight === 900;
      const importedAsConfigured =
        marker &&
        project.configured !== null &&
        v.atImport.innerWidth === project.configured.width &&
        v.atImport.innerHeight === project.configured.height;
      // 머리 주석의 기대: 지정 없음은 1200×900, browser-viewport 는 불러올 때 설정한 크기였다가 덮이고, sb-globals 는 따른다.
      const widthAsExpected =
        project.configured === null
          ? is1200
          : run.name === "browser-viewport"
            ? importedAsConfigured && is1200
            : followsConfig === true;
      rounds.push({
        kind: "viewport",
        run: run.name,
        project: project.name,
        configured: project.configured,
        measurement: marker,
        expected: marker ? densityFollowsWidth && widthAsExpected : null,
        followsConfig,
        density: marker ? (v.rootControlH === v.compactRef ? "compact" : v.rootControlH === v.regularRef ? "regular" : "other") : null,
        values: v,
      });

      const writeLog = logsOf(project.name, "PROBE_STORAGE_WRITE")[0];
      const readLog = logsOf(project.name, "PROBE_STORAGE_READ")[0];
      const w = writeLog ? parsed(writeLog.content, "PROBE_STORAGE_WRITE") : null;
      const r = readLog ? parsed(readLog.content, "PROBE_STORAGE_READ") : null;
      const storageMarker = w !== null && r !== null && r.at >= w.at && r.self === "self";
      const writers = Object.values(reports)
        .flatMap((rep) => rep?.logs ?? [])
        .filter((log) => log.content.startsWith("PROBE_STORAGE_WRITE"))
        .map((log) => ({ project: log.project, value: parsed(log.content, "PROBE_STORAGE_WRITE").value }));
      rounds.push({
        kind: "storage",
        run: run.name,
        project: project.name,
        measurement: storageMarker,
        expected: storageMarker ? r.seen === w.value : null,
        visible: storageMarker ? r.seen === w.value : null,
        seenFrom: r?.seen ? (writers.find((writer) => writer.value === r.seen)?.project ?? "알 수 없음") : null,
        write: w,
        read: r,
      });
    }
  }
} finally {
  removed = removeWork();
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
