/**
 * 짓기 명령(assemble). 디자인 시스템 패키지의 소스에서 Design System 형식의 컴포넌트 묶음과 컴포넌트 카드, 글꼴, 목업이
 * 싣는 옛 이름의 파일, `tokens.json`, 디자인 시스템 README, 기초 카드, 지침을 산출 폴더 하나에 짓는다(design-card-build
 * 명세 "짓기 명령", "tokens.json", "디자인 시스템 README와 나머지 파일", ADR 0025 의 2026-10-28 이력). 산출 폴더는
 * 아티팩트의 `project/` 아래에 놓일 내용이다.
 *
 * - `components/bundle.js`: 패키지 엔트리(`src/index.ts`)를 IIFE 하나로 묶은 것이고 전역 이름은 `AgentOsUi` 다. 1행은
 *   `@ds-bundle` 머리(format 4)이고 컴포넌트 목록은 카드가 있는 컴포넌트를 층의 차례(`LAYERS`), 같은 층 안에서는 이름
 *   차례로 든다. React·ReactDOM 은 묶지 않고 전역으로 읽고, JSX 런타임은 `createElement` 로 다시 짓는 대체 모듈로
 *   바꾼다. 패키지의 React 19 가 JSX 로 내는 요소 표식을 페이지의 React 18.3.1 이 그리지 않는다고 보기 때문이다(두 판의
 *   표식이 다르다는 지식에서 낸 명세의 어림이다. React 18.3.1 에 그 표식을 넣어 그려 보지는 않았다).
 * - `components/bundle.css`: 패키지의 Tailwind 빌드(`src/styles/theme.css`, `--minify`) 뒤에 글꼴의 `@font-face` 를
 *   붙인 것이다. 디자인 토큰은 Tailwind 가 둔 대로 `@layer theme` 안에 남아, 층 없는 페이지 토큰 CSS 가 이긴다.
 * - `components/<이름>/preview.html`: 층 폴더(`LAYERS`)의 스토리 파일 가운데 태그 `showcase` 가 든 스토리를 가진 파일마다
 *   카드 하나다. 1행 `@dsCard` 표지, 뿌리 요소, 장면 스크립트 하나의 차례다. 장면은 그 스토리 파일을 IIFE 로 묶은
 *   것이고, 패키지의 컴포넌트 모듈은 묶지 않고 전역 `AgentOsUi` 에서 읽는다. showcase 스토리마다 meta 와 그 스토리의
 *   `args` 를 합쳐 `render`(없으면 meta 의 `component`)로 그려 `<section data-scene="<내보낸 이름>">` 에 넣고, 그 모두를
 *   React 루트 하나로 그린다. `play`·`globals`·`parameters` 는 쓰지 않고 테마와 모드는 정하지 않는다.
 * - `components/<이름>/README.md`: 컴포넌트 옆의 쓰임 설명(`<이름>.md`)의 바이트 그대로다.
 * - `fonts/`: 패키지의 글꼴 CSS(`src/styles/fonts.css`)를 vite 로 지어 나온 글꼴 파일과 그 CSS(`fonts/fonts.css`)다.
 *   인라인 한도는 vite 기본값이다. 글꼴 주소는 놓일 자리에 맞춰 세 벌로 쓴다(`FONT_PREFIXES`). data URL 은 그대로 둔다.
 * - 옛 이름: `_ds_bundle.js` 는 `components/bundle.js` 와 같은 바이트, `_ds_bundle.css` 는 같은 Tailwind 빌드에 주소가
 *   `./fonts/` 인 `@font-face` 를 붙인 것, `styles.css` 는 `fonts/fonts.css` 와 `_ds_bundle.css` 를 차례로 들인다.
 * - `tokens.json`: 이미 있는 `build` 가 패키지의 디자인 토큰 CSS 에서 짓는 것과 같은 바이트다.
 * - `README.md`: README 원본(`artifact-source/README.md`)의 바이트 그대로다. 페이지가 저장할 때 붙이는 생성 몫
 *   (Consuming, Index)이 컴포넌트 목록을 대신한다.
 * - `foundations/`: 기초 카드 원본 폴더(`artifact-source/foundations/`)의 파일을 바이트 그대로 둔다. 카드의 규칙은 그
 *   곁의 `artifact-source/foundations.md` 다.
 * - `guidelines/web-design.md` 는 규칙 파일 `.claude/rules/web-design.md` 의 바이트이고, `guidelines/index.md` 는 그 파일
 *   하나를 가리키는 목록이다.
 *
 * vite 와 Tailwind 는 import 하지 않는다(새 의존이 들지 않는다). 패키지에 깔린 두 CLI 를 패키지 폴더를 작업 폴더로 삼아
 * 셸 없이 node 로 바로 띄운다. vite 설정은 import 없는 글로 지어 명령의 임시 폴더에 쓰고, 플러그인 셋(JSX 대체 모듈,
 * `storybook/test` 대체 모듈, 컴포넌트 모듈을 전역으로 돌리는 해석기)은 그 글 안의 객체다. 빌드의 성공은 종료 코드 0 과
 * 산출 파일로 가른다. 성공한 빌드도 stderr 에 rolldown 의 `"use client"` 경고를 싣는다.
 *
 * 명령은 임시 폴더에 지은 뒤 그 폴더를 규칙(`assertAssembled`: 금지 문자열, 크기 한도, 카드 README)으로 판정하고, 지날
 * 때만 `--out` 에 옮긴다. 빌드가 실패하거나 저장소 원본(README 원본, 기초 카드 원본, 규칙 파일)을 읽지 못하거나 기초
 * 카드 원본 폴더가 비었으면 `input` 이고, `tokens.json` 은 `build` 와 같은 오류(풀 수 없으면 `input`, 한도를 넘으면
 * `limit`)로 끝난다. 규칙을 어기면 크기만 넘었을 때 `limit`, 그 밖은 `input` 오류다. 산출에는
 * 시각과 임시 폴더 경로, `--out` 경로를 넣지 않아 같은 소스에서 다시 지으면 같은 바이트다(명세 스토리 12).
 *
 * 명령: `assemble --out <산출 폴더> --paths <목록 파일>`. 산출 폴더는 없거나 빈 폴더여야 하고, 그렇지 않으면(파일이다,
 * 비어 있지 않다) 아무것도 쓰지 않고 `output` 오류다. 목록 파일이 산출 폴더 안이면 `usage` 오류다. 임시 폴더를 만들지
 * 못해도 아무것도 쓰지 않고 `output` 오류다. 명령은 자기가 만든 임시 폴더 말고는 어떤 폴더도 지우지 않는다.
 *
 * 목록 파일에는 산출 폴더의 모든 파일을 `project/<경로>` 로 적어 경로 차례(`byPath`)로 놓은 JSON 배열을 두 칸 들여쓰고
 * 끝에 줄바꿈을 붙여 쓴다. 목록 파일은 산출을 옮기기 전에 써서, 쓰지 못하면 산출 폴더에 아무것도 없다.
 * 보고는 산출 폴더(`out`)와 목록 파일(`paths`)의 절대 경로, 파일 수(`files`), 카드 이름(`cards`), 바이트(`bytes`)다.
 *
 * 못 보는 것:
 * - showcase 스토리를 가진 파일은 소스 글에서 `tags: [... "showcase" ...]` 를 찾아 가른다. 태그를 모두 변수로 든 파일은
 *   카드가 빠지고, meta 의 `tags` 에만 든 파일은 장면 없는 카드가 된다. 장면은 실제 스토리 객체의 `tags` 로 다시 고르므로,
 *   글자 그대로 쓴 스토리가 있는 파일에서는 태그를 변수로 든 스토리도 장면에 든다.
 * - 패키지 엔트리가 내보내지 않는 이름(지금 `ICON_NAMES` 등)은 장면에서 비고, 그것을 쓰는 showcase 스토리는 그릴 때에야
 *   오류가 난다.
 * - 장면이 meta 와 스토리의 `args` 를 합친 값이 그리기에 닿는지와 `render` 없이 meta 의 `component` 로 그리는 갈래는,
 *   지금 showcase 스토리가 모두 `args` 를 받지 않는 `render` 를 가져 시험이 보지 않는다.
 * - 판정은 묶음 JS 와 카드만 금지 문자열을 본다. `_ds_bundle.js` 는 같은 바이트로 지어 따로 보지 않는다.
 * - 산출을 옮기다 끊기면 산출 폴더에 옮긴 데까지 남고, 목록 파일은 이미 쓰여 있다. 없던 산출 폴더는 이름을 바꿔 한 번에
 *   옮기지만, 이름을 바꾸지 못하면(다른 드라이브 등) 비어 있던 폴더처럼 복사로 옮긴다.
 * - 명령이 임시 폴더에 직접 쓰다(vite 설정, 장면 엔트리, 산출 파일) 실패하면(디스크가 찼다 등) `CommandError` 가 아닌
 *   예외로 끝나 JSON 보고가 없다. vite 와 Tailwind 가 쓰다 실패하면 그 도구가 0 으로 끝나지 않아 `input` 오류다.
 * - 임시 폴더를 지우지 못하면(다른 프로세스가 그 안을 작업 폴더로 쓰는 등) 결과를 덮지 않고 그 폴더를 남기며, 남겼다고
 *   알리지 않는다. 이 길은 시험이 지나지 않는다.
 */

import { spawnSync } from "node:child_process";
import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  renameSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { parseArgs } from "node:util";
import { buildTokensJson, DEFAULT_CSS } from "./build.ts";
import {
  CommandError,
  messageOf,
  parsedArgs,
  readInput,
  writeOutput,
  type ErrorKind,
  type ReportFields,
} from "./command.ts";
import { byPath, isRecord, parseJson } from "./io.ts";

const WEB = dirname(dirname(import.meta.dirname));

/** 디자인 시스템 패키지의 폴더. */
export const UI_PACKAGE = join(WEB, "packages", "ui");

/** 산출에 바이트 그대로 두는 저장소 원본. README 원본과 기초 카드 원본은 이 폴더의 `artifact-source/` 에 있다. */
const SOURCES = {
  readme: join(import.meta.dirname, "artifact-source", "README.md"),
  foundations: join(import.meta.dirname, "artifact-source", "foundations"),
  webDesign: join(dirname(WEB), ".claude", "rules", "web-design.md"),
} as const;

/** `guidelines/index.md`. 지침 파일 하나를 가리키는 목록이고, 아티팩트 판 `1793259788-d3cd` 의 그 파일과 같은 바이트다. */
const GUIDELINES_INDEX = "# Guidelines\n\n- [web-design](./web-design.md)\n";

/** 카드를 짓는 컴포넌트 층 폴더. 묶음 머리의 컴포넌트 목록이 이 차례다. */
export const LAYERS = ["atoms", "molecules"] as const;

/** 명령이 만드는 임시 폴더 이름의 앞머리. 산출에 이 글이 들지 않는지 시험이 본다. */
export const ASSEMBLE_TEMP_PREFIX = "agent-os-assemble-";

/** 형식의 한도(바이트). */
export const SIZE_LIMITS = {
  bundleJs: 6_000_000,
  bundleCss: 2_000_000,
  card: 256_000,
  readme: 64_000,
} as const;

/** 글꼴 CSS 를 싣는 파일마다 글꼴 주소의 앞머리. 파일 이름 앞에 붙인다. */
export const FONT_PREFIXES = {
  "fonts/fonts.css": "./",
  "_ds_bundle.css": "./fonts/",
  "components/bundle.css": "../../fonts/",
} as const;

/** 빌드 하나의 시간 제한(밀리초). 넘으면 그 빌드의 실패로 센다. */
const BUILD_TIMEOUT = 300_000;

const SHOWCASE_TAGS = /\btags:\s*\[[^\]]*["']showcase["'][^\]]*\]/;

/** 묶음과 장면이 묶지 않고 전역으로 읽는 모듈. */
const GLOBALS = {
  react: "React",
  "react-dom": "ReactDOM",
  "react-dom/client": "ReactDOM",
  "agent-os-ui-global": "AgentOsUi",
} as const;

/** React 19 의 JSX 런타임 대신 전역 React 의 `createElement` 로 요소를 짓는 대체 모듈. */
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

/** 스토리가 부르는 Storybook 시험 도구 대신 아무 일도 하지 않는 대체 모듈. 장면은 `play` 를 돌리지 않는다. */
const SB_TEST_STUB = `const noop = () => {};
export const fn = () => noop;
export const expect = () => new Proxy({}, { get: () => noop });
export const within = () => ({});
export const userEvent = {};
export const waitFor = noop;`;

const posix = (path: string): string => path.split(sep).join("/");

/** 패키지에 깔린 의존의 실행 파일. 그 의존의 `package.json` 의 `bin` 에서 찾는다. */
function packageBin(name: string, command: string): string {
  const folder = join(UI_PACKAGE, "node_modules", ...name.split("/"));
  let manifest: unknown;
  try {
    manifest = parseJson(readFileSync(join(folder, "package.json"), "utf-8"));
  } catch (error) {
    throw new CommandError(
      "input",
      `${name} 가 디자인 시스템 패키지에 깔려 있지 않다: ${messageOf(error)}`,
    );
  }
  const bin = isRecord(manifest) ? manifest["bin"] : undefined;
  const path = isRecord(bin) ? bin[command] : bin;
  if (typeof path !== "string") {
    throw new CommandError("input", `${name} 의 package.json 에 실행 파일 ${command} 가 없다`);
  }
  return join(folder, path);
}

/** 패키지 폴더에서 node 로 실행 파일을 셸 없이 띄운다. 0 으로 끝나지 않으면 `input` 오류다. */
function runTool(script: string, args: readonly string[]): void {
  const result = spawnSync(process.execPath, [script, ...args], {
    cwd: UI_PACKAGE,
    encoding: "utf-8",
    env: { ...process.env, NODE_ENV: "production" },
    stdio: ["ignore", "pipe", "pipe"],
    timeout: BUILD_TIMEOUT,
    maxBuffer: 16 * 1024 * 1024,
  });
  if (result.error !== undefined || result.status !== 0) {
    const why =
      result.error === undefined ? `종료 코드 ${String(result.status)}` : result.error.message;
    throw new CommandError(
      "input",
      `${basename(script)} ${args[0] ?? ""} 가 실패했다(${why}): ${result.stderr.slice(-1500)}`,
    );
  }
}

/** vite 설정 글을 임시 폴더에 쓰고 그 설정으로 짓는다. */
export function viteBuild(work: string, name: string, config: string): void {
  const file = join(work, `${name}.config.mjs`);
  writeFileSync(file, config);
  runTool(packageBin("vite", "vite"), ["build", "--config", file]);
}

/** 짓기가 낸 파일 하나. 없으면 `input` 오류다. */
function builtFile(path: string): string {
  try {
    return readFileSync(path, "utf-8");
  } catch (error) {
    throw new CommandError("input", `빌드가 ${basename(path)} 를 내지 않았다: ${messageOf(error)}`);
  }
}

/** 설정 글 안의 가상 모듈 플러그인. `match` 는 모듈 이름을 받는 함수의 글이다. */
function virtualPlugin(id: string, code: string, match: string): string {
  return `{
    name: ${JSON.stringify(`virtual:${id}`)},
    enforce: "pre",
    resolveId: (source) => (${match} ? ${JSON.stringify(`\0${id}`)} : null),
    load: (loaded) => (loaded === ${JSON.stringify(`\0${id}`)} ? ${JSON.stringify(code)} : null),
  }`;
}

/** 스토리 파일이 상대 경로로 부르는 컴포넌트 모듈을 전역 `AgentOsUi` 로 돌리는 해석기. */
function uiGlobalPlugin(): string {
  const components = posix(join(UI_PACKAGE, "src", "components")).toLowerCase();
  return `{
    name: "ui-global",
    enforce: "pre",
    async resolveId(source, importer, options) {
      if (importer === undefined || !source.startsWith(".")) return null;
      const resolved = await this.resolve(source, importer, { ...options, skipSelf: true });
      if (resolved === null || resolved.external) return null;
      const id = resolved.id.replaceAll("\\\\", "/").toLowerCase();
      if (id.startsWith(${JSON.stringify(components)}) && !id.endsWith(".stories.tsx")) {
        return { id: "agent-os-ui-global", external: true };
      }
      return null;
    },
  }`;
}

interface LibBuild {
  readonly entry: string;
  readonly name: string;
  readonly outDir: string;
  /** `scene` 이면 Storybook 시험 도구를 대체하고 컴포넌트 모듈을 전역으로 돌린다. */
  readonly kind: "bundle" | "scene";
}

/** IIFE 하나를 `out.js` 로 짓는 vite 설정 글. */
function libConfig({ entry, name, outDir, kind }: LibBuild): string {
  const plugins = [
    virtualPlugin(
      "jsx-shim",
      JSX_SHIM,
      `source === "react/jsx-runtime" || source === "react/jsx-dev-runtime"`,
    ),
    ...(kind === "scene"
      ? [virtualPlugin("sb-test", SB_TEST_STUB, `source === "storybook/test"`), uiGlobalPlugin()]
      : []),
  ];
  return `export default {
  root: ${JSON.stringify(posix(UI_PACKAGE))},
  publicDir: false,
  logLevel: "warn",
  define: { "process.env.NODE_ENV": ${JSON.stringify(JSON.stringify("production"))} },
  plugins: [${plugins.join(", ")}],
  build: {
    outDir: ${JSON.stringify(posix(outDir))},
    emptyOutDir: false,
    minify: true,
    lib: { entry: ${JSON.stringify(posix(entry))}, formats: ["iife"], name: ${JSON.stringify(name)}, fileName: () => "out.js" },
    rolldownOptions: {
      external: ${JSON.stringify(Object.keys(GLOBALS))},
      output: { globals: ${JSON.stringify(GLOBALS)} },
    },
  },
};
`;
}

/** 패키지의 글꼴 CSS 를 지어 글꼴 파일을 `fonts/` 에 내는 vite 설정 글. 인라인 한도는 기본값이다. */
function fontsConfig(outDir: string): string {
  return `export default {
  root: ${JSON.stringify(posix(UI_PACKAGE))},
  publicDir: false,
  logLevel: "warn",
  build: {
    outDir: ${JSON.stringify(posix(outDir))},
    emptyOutDir: false,
    assetsDir: "fonts",
    rolldownOptions: { input: ${JSON.stringify(posix(join(UI_PACKAGE, "src", "styles", "fonts.css")))} },
  },
};
`;
}

/** 폴더 안의 파일(`/` 로 이은 상대 경로)과 그 바이트 수. 경로 차례다. */
function walk(folder: string): { readonly path: string; readonly size: number }[] {
  return readdirSync(folder, { withFileTypes: true, recursive: true })
    .filter((entry) => entry.isFile())
    .map((entry) => {
      const absolute = join(entry.parentPath, entry.name);
      return { path: posix(relative(folder, absolute)), size: statSync(absolute).size };
    })
    .sort((left, right) => byPath(left.path, right.path));
}

/** Tailwind 빌드. */
function tailwindCss(work: string): string {
  const file = join(work, "tailwind.css");
  runTool(packageBin("@tailwindcss/cli", "tailwindcss"), [
    "-i",
    join("src", "styles", "theme.css"),
    "-o",
    file,
    "--minify",
  ]);
  return builtFile(file);
}

interface Fonts {
  /** vite 가 낸 글꼴 CSS. 주소는 아직 vite 의 것이다. */
  readonly css: string;
  /** 글꼴 파일 이름과 그 파일의 절대 경로. */
  readonly files: ReadonlyMap<string, string>;
}

function buildFonts(work: string): Fonts {
  const outDir = join(work, "fonts-build");
  viteBuild(work, "fonts", fontsConfig(outDir));
  const built = existsSync(outDir) ? walk(outDir) : [];
  const sheets = built.filter((file) => file.path.endsWith(".css"));
  const [sheet] = sheets;
  if (sheet === undefined || sheets.length > 1) {
    throw new CommandError(
      "input",
      `글꼴 빌드가 CSS 를 하나 내지 않았다(${String(sheets.length)})`,
    );
  }
  const files = new Map(
    built
      .filter((file) => /\.woff2?$/.test(file.path))
      .map((file) => [basename(file.path), join(outDir, file.path)]),
  );
  return { css: builtFile(join(outDir, sheet.path)), files };
}

/** 글꼴 CSS 의 data URL 이 아닌 주소를 파일 이름만 남겨 `prefix` 를 붙인 것. */
export function relocateFonts(css: string, prefix: string): string {
  return css.replace(/url\(\s*(["']?)([^"')]*)\1\s*\)/g, (whole, _quote: string, url: string) =>
    url.startsWith("data:") ? whole : `url(${prefix}${url.slice(url.lastIndexOf("/") + 1)})`,
  );
}

interface Story {
  readonly name: string;
  readonly layer: (typeof LAYERS)[number];
  readonly file: string;
}

/** 층 폴더의 스토리 파일 가운데 showcase 스토리를 가진 것. 층의 차례, 같은 층 안에서는 이름 차례다. */
function showcaseStories(): Story[] {
  return LAYERS.flatMap((layer) => {
    const folder = join(UI_PACKAGE, "src", "components", layer);
    return readdirSync(folder)
      .filter((file) => file.endsWith(".stories.tsx"))
      .sort(byPath)
      .filter((file) => SHOWCASE_TAGS.test(readFileSync(join(folder, file), "utf-8")))
      .map((file) => ({
        name: file.slice(0, -".stories.tsx".length),
        layer,
        file: join(folder, file),
      }));
  });
}

/** 스토리 파일 하나의 showcase 스토리를 `#root` 에 그리는 장면의 엔트리. */
function sceneEntry(story: string): string {
  return `import * as stories from ${JSON.stringify(posix(story))};
const R = window.React;
const meta = stories.default;
const shown = Object.entries(stories).filter(
  ([key, story]) => key !== "default" && story && Array.isArray(story.tags) && story.tags.includes("showcase"),
);
const tree = R.createElement(
  R.Fragment,
  null,
  ...shown.map(([key, story]) => {
    const args = { ...(meta.args ?? {}), ...(story.args ?? {}) };
    const body = typeof story.render === "function" ? story.render(args, { args }) : R.createElement(meta.component, args);
    return R.createElement("section", { key, "data-scene": key }, body);
  }),
);
window.ReactDOM.createRoot(document.getElementById("root")).render(tree);
`;
}

/** 이름이 `name` 인 IIFE 를 지어 그 글을 돌려준다. 끝의 줄바꿈은 뺀다. */
function buildIife(work: string, label: string, build: Omit<LibBuild, "outDir">): string {
  const outDir = join(work, label);
  viteBuild(work, label, libConfig({ ...build, outDir }));
  return builtFile(join(outDir, "out.js")).trimEnd();
}

function write(stage: string, path: string, data: string | Uint8Array): void {
  const file = join(stage, ...path.split("/"));
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, data);
}

/** 저장소 원본 파일의 바이트. 없으면 `input` 오류다. */
function sourceBytes(path: string): Buffer {
  try {
    return readFileSync(path);
  } catch (error) {
    throw new CommandError("input", `${path} 를 읽을 수 없다: ${messageOf(error)}`);
  }
}

/** 묶음 JS·CSS, 글꼴, 옛 이름을 `stage` 에 짓는다. 머리의 컴포넌트 목록은 카드가 있는 컴포넌트다. */
function writeBundles(stage: string, work: string, stories: readonly Story[]): void {
  const tailwind = tailwindCss(work);
  const fonts = buildFonts(work);
  const bundle = buildIife(work, "bundle", {
    entry: join(UI_PACKAGE, "src", "index.ts"),
    name: "AgentOsUi",
    kind: "bundle",
  });

  const head = JSON.stringify({
    format: 4,
    namespace: "AgentOsUi",
    components: stories.map((story) => ({ name: story.name })),
  });
  const bundleJs = `/* @ds-bundle: ${head} */\n${bundle}\n`;
  write(stage, "components/bundle.js", bundleJs);
  write(stage, "_ds_bundle.js", bundleJs);
  write(
    stage,
    "components/bundle.css",
    `${tailwind}\n${relocateFonts(fonts.css, FONT_PREFIXES["components/bundle.css"])}`,
  );
  write(
    stage,
    "_ds_bundle.css",
    `${tailwind}\n${relocateFonts(fonts.css, FONT_PREFIXES["_ds_bundle.css"])}`,
  );
  write(stage, "fonts/fonts.css", relocateFonts(fonts.css, FONT_PREFIXES["fonts/fonts.css"]));
  for (const [name, file] of fonts.files) {
    write(stage, `fonts/${name}`, readFileSync(file));
  }
  write(stage, "styles.css", `@import "./fonts/fonts.css";\n@import "./_ds_bundle.css";\n`);
}

/** showcase 스토리를 가진 스토리 파일마다 카드와 그 README 를 `stage` 에 짓는다. 장면 엔트리는 `work` 에 쓴다. */
function writeCards(stage: string, work: string, stories: readonly Story[]): void {
  const entries = join(work, "entries");
  mkdirSync(entries);
  for (const story of stories) {
    const entry = join(entries, `scene-${story.name}.mjs`);
    writeFileSync(entry, sceneEntry(story.file));
    const scene = buildIife(work, `scene-${story.name}`, { entry, name: "__scene", kind: "scene" });
    write(
      stage,
      `components/${story.name}/preview.html`,
      `<!-- @dsCard group="${story.layer}" -->\n<div id="root" data-ui-root></div>\n<script>${scene}</script>\n`,
    );
    const readme = join(dirname(story.file), `${story.name}.md`);
    if (existsSync(readme)) {
      write(stage, `components/${story.name}/README.md`, readFileSync(readme));
    }
  }
}

/** `tokens.json`, 디자인 시스템 README, 기초 카드, 지침을 `stage` 에 둔다. 토큰 밖은 저장소 원본의 바이트 그대로다. */
function writeDocuments(stage: string): void {
  write(stage, "tokens.json", buildTokensJson(readInput(DEFAULT_CSS)));
  write(stage, "README.md", sourceBytes(SOURCES.readme));
  let foundations: { readonly path: string }[];
  try {
    foundations = walk(SOURCES.foundations);
  } catch (error) {
    throw new CommandError("input", `${SOURCES.foundations} 를 읽을 수 없다: ${messageOf(error)}`);
  }
  if (foundations.length === 0) {
    throw new CommandError("input", `${SOURCES.foundations} 에 기초 카드가 없다`);
  }
  for (const file of foundations) {
    write(stage, `foundations/${file.path}`, sourceBytes(join(SOURCES.foundations, file.path)));
  }
  write(stage, "guidelines/web-design.md", sourceBytes(SOURCES.webDesign));
  write(stage, "guidelines/index.md", GUIDELINES_INDEX);
}

interface Problem {
  readonly kind: Extract<ErrorKind, "input" | "limit">;
  readonly message: string;
}

const FORBIDDEN = ["</script", "<!--", "require(", "react.transitional.element"] as const;
const IMPORT_STATEMENT = /(?:^|[;\n}])\s*import\s*[\w$*{"']/;

/** 글에 든 금지 문자열과 `import` 문의 문제. `</script` 와 `<!--` 는 HTML 처럼 대소문자를 가리지 않는다. */
function forbiddenProblems(path: string, text: string, where: string): Problem[] {
  const lower = text.toLowerCase();
  const found: Problem[] = FORBIDDEN.filter((needle) =>
    needle.startsWith("<") ? lower.includes(needle) : text.includes(needle),
  ).map((needle) => ({ kind: "input", message: `${path} ${where} ${needle} 가 있다` }));
  return IMPORT_STATEMENT.test(text)
    ? [...found, { kind: "input", message: `${path} ${where} import 문이 있다` }]
    : found;
}

function sizeProblem(path: string, size: number, limit: number): Problem[] {
  return size > limit
    ? [{ kind: "limit", message: `${path} 가 ${String(limit)} 바이트를 넘는다(${String(size)})` }]
    : [];
}

/** 카드의 장면 본문. 첫 줄 표지와 장면을 싸는 `<script>` 태그는 본문이 아니다. */
function sceneBody(card: string): string | undefined {
  const open = card.indexOf("<script>");
  const close = card.lastIndexOf("</script>");
  return open === -1 || close < open ? undefined : card.slice(open + "<script>".length, close);
}

function problemsOf(folder: string): Problem[] {
  const files = new Map(walk(folder).map((file) => [file.path, file.size]));
  const text = (path: string): string => readFileSync(join(folder, ...path.split("/")), "utf-8");
  const cards = [...files.keys()].filter((path) => /^components\/[^/]+\/preview\.html$/.test(path));
  /** 있어야 하는 파일과 그 한도. 카드는 있는 것만 들고, 카드마다 같은 폴더의 README 가 있어야 한다. */
  const limits: readonly (readonly [path: string, limit: number])[] = [
    ["components/bundle.js", SIZE_LIMITS.bundleJs],
    ["components/bundle.css", SIZE_LIMITS.bundleCss],
    ...cards.flatMap((card): (readonly [string, number])[] => [
      [card, SIZE_LIMITS.card],
      [card.replace(/preview\.html$/, "README.md"), SIZE_LIMITS.readme],
    ]),
  ];
  const sized = limits.flatMap(([path, limit]): Problem[] => {
    const size = files.get(path);
    return size === undefined
      ? [{ kind: "input", message: `${path} 가 없다` }]
      : sizeProblem(path, size, limit);
  });
  const bundle = files.has("components/bundle.js")
    ? forbiddenProblems("components/bundle.js", text("components/bundle.js"), "에")
    : [];
  const scenes = cards.flatMap((card): Problem[] => {
    const body = sceneBody(text(card));
    return body === undefined
      ? [{ kind: "input", message: `${card} 에 장면 스크립트가 없다` }]
      : forbiddenProblems(card, body, "의 장면에");
  });
  return [...sized, ...bundle, ...scenes];
}

/**
 * 지은 산출 폴더를 규칙으로 판정해, 어기면 `CommandError` 를 던진다. 묶음 JS 와 카드의 장면 본문에 `</script`·`<!--`·
 * `require(`·`import` 문·`react.transitional.element` 가 없고, 묶음 JS·묶음 CSS·카드·카드 README 가 한도(`SIZE_LIMITS`)
 * 아래이며, 카드마다 같은 폴더에 README 가 있어야 한다. 앞의 둘은 형식이 금한다(페이지가 묶음과 카드를 문서에
 * 인라인한다). 뒤의 셋이 있으면 페이지에서 돌지 않는다. 오류의 종류는 크기만 넘었으면 `limit`, 그 밖은 `input` 이고,
 * 문구는 문제마다의 문구를 `; ` 로 이은 것이다. 명령과, 시험에서 지은 산출이나 그 사본을 판정하는 사례(`failureOf`)가
 * 이 함수로 판정한다. 시험의 파일 검사는 금지 문자열을 따로 본다.
 */
export function assertAssembled(folder: string): void {
  const problems = problemsOf(folder);
  if (problems.length > 0) {
    const kind = problems.every((problem) => problem.kind === "limit") ? "limit" : "input";
    throw new CommandError(kind, problems.map((problem) => problem.message).join("; "));
  }
}

/** 산출 폴더가 없거나 빈 폴더가 아니면 `output` 오류다. */
function refuseBusy(target: string): void {
  if (!existsSync(target)) {
    return;
  }
  if (!statSync(target).isDirectory()) {
    throw new CommandError("output", `${target} 가 폴더가 아니다. 아무것도 쓰지 않는다`);
  }
  if (readdirSync(target).length > 0) {
    throw new CommandError("output", `${target} 가 비어 있지 않다. 아무것도 쓰지 않는다`);
  }
}

/** 지은 산출을 산출 폴더로 옮긴다. 없던 폴더면 이름을 바꾸고, 빈 폴더면 그 안에 복사한다. */
function place(stage: string, target: string): void {
  refuseBusy(target);
  try {
    if (!existsSync(target)) {
      mkdirSync(dirname(target), { recursive: true });
      try {
        renameSync(stage, target);
        return;
      } catch {
        // 이름을 바꾸지 못하면(다른 드라이브 등) 복사로 옮긴다. 복사도 실패하면 아래에서 `output` 오류다.
      }
    }
    cpSync(stage, target, { recursive: true, errorOnExist: true, force: false });
  } catch (error) {
    throw new CommandError("output", `${target} 에 산출을 옮길 수 없다: ${messageOf(error)}`);
  }
}

/** 명령의 임시 폴더를 만든다. 만들지 못하면 `output` 오류다. */
function workFolder(): string {
  try {
    return mkdtempSync(join(tmpdir(), ASSEMBLE_TEMP_PREFIX));
  } catch (error) {
    throw new CommandError("output", `임시 폴더를 만들 수 없다: ${messageOf(error)}`);
  }
}

/**
 * 명령의 임시 폴더를 지운다. 지우지 못해도(다른 프로세스가 그 안을 작업 폴더로 쓰는 등) 명령의 결과를 덮지 않는다. 그
 * 폴더는 시스템 임시 폴더에 남는다.
 */
function removeWorkFolder(work: string): void {
  try {
    rmSync(work, { recursive: true, force: true, maxRetries: 3 });
  } catch {
    // 위 독스트링대로 실패를 삼킨다.
  }
}

/** 짓기 명령. */
export function assemble(args: readonly string[]): ReportFields {
  const { out, paths } = parsedArgs(
    () =>
      parseArgs({
        args: [...args],
        options: { out: { type: "string" }, paths: { type: "string" } },
        strict: true,
        allowPositionals: false,
      }).values,
  );
  if (out === undefined || paths === undefined) {
    throw new CommandError("usage", "--out <산출 폴더> 와 --paths <목록 파일> 을 준다");
  }
  const target = resolve(out);
  const fromTarget = relative(target, resolve(paths));
  if (fromTarget !== ".." && !fromTarget.startsWith(`..${sep}`) && !isAbsolute(fromTarget)) {
    throw new CommandError("usage", "--paths 를 산출 폴더 밖에 둔다");
  }
  refuseBusy(target);

  const work = workFolder();
  try {
    const stage = join(work, "stage");
    // 저장소 원본을 읽는 문서가 먼저다. 원본이 없으면 vite·Tailwind 빌드를 띄우기 전에 `input` 으로 끝난다.
    writeDocuments(stage);
    const stories = showcaseStories();
    writeBundles(stage, work, stories);
    writeCards(stage, work, stories);
    assertAssembled(stage);
    const files = walk(stage);
    const list = files.map((file) => `project/${file.path}`);
    const listFile = writeOutput(paths, `${JSON.stringify(list, null, 2)}\n`);
    place(stage, target);
    return {
      out: target,
      paths: listFile,
      files: files.length,
      cards: stories.map((story) => story.name),
      bytes: files.reduce((sum, file) => sum + file.size, 0),
    };
  } finally {
    removeWorkFolder(work);
  }
}
