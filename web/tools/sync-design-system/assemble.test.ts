// 짓기 명령(assemble)의 테스트(design-card-build 명세 Testing Decisions "이음매", "자리", "파일 검사"와 그 2026-10-29
// 주석). 명령을 임시 폴더로 한 번 돌리고, 같은 산출 폴더를 파일 검사와 규칙 판정과 chromium 그리기가 함께 읽는다. 짓기는
// 패키지의 vite·Tailwind CLI 를 열두 번 남짓 띄워 한 번에 십몇 초가 든다.

import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, sep } from "node:path";
import { chromium, type Browser } from "playwright";
import { afterAll, beforeAll, describe, expect, test, vi } from "vitest";
import {
  ASSEMBLE_TEMP_PREFIX,
  assertAssembled,
  LAYERS,
  UI_PACKAGE,
  viteBuild,
} from "./assemble.ts";
import { CommandError, type ErrorKind } from "./command.ts";
import { byPath, isRecord } from "./io.ts";
import { run } from "./main.ts";

const WEB = dirname(dirname(import.meta.dirname));
const COMPONENTS = join(WEB, "packages", "ui", "src", "components");
/** 스토리 파일 글에서 태그 `showcase` 가 든 `tags` 배열. 명령과 따로 세어 그리기 시험이 장면 수와 맞댄다. */
const SHOWCASE_TAGS = /\btags:\s*\[[^\]]*["']showcase["'][^\]]*\]/g;
// 파일 검사의 금지 문자열은 명령의 판정과 따로 짓되 그보다 느슨하지 않게 둔다(대소문자는 모두 가리지 않는다).
const FORBIDDEN = ["</script", "<!--", "require(", "react.transitional.element"];
const IMPORT_STATEMENT = /(?:^|[;\n}])\s*import\s*[\w$*{"']/;

interface ExpectedCard {
  readonly name: string;
  readonly layer: string;
  /** 소스 글에서 센 showcase 스토리의 수. */
  readonly scenes: number;
}

/** 층 폴더의 스토리 파일 가운데 showcase 스토리를 가진 것. 층의 차례, 같은 층 안에서는 이름 차례다. */
function expectedCards(): ExpectedCard[] {
  return LAYERS.flatMap((layer) =>
    readdirSync(join(COMPONENTS, layer))
      .filter((file) => file.endsWith(".stories.tsx"))
      .map((file) => ({
        name: file.slice(0, -".stories.tsx".length),
        layer,
        scenes: (readFileSync(join(COMPONENTS, layer, file), "utf-8").match(SHOWCASE_TAGS) ?? [])
          .length,
      }))
      .filter((card) => card.scenes > 0)
      .sort((left, right) => byPath(left.name, right.name)),
  );
}

/** 폴더 안의 파일 경로(`/` 로 이은 상대 경로). 경로 차례다. */
function walk(folder: string): string[] {
  return readdirSync(folder, { withFileTypes: true, recursive: true })
    .filter((entry) => entry.isFile())
    .map((entry) => relative(folder, join(entry.parentPath, entry.name)).split(sep).join("/"))
    .sort(byPath);
}

/** 카드의 장면 본문. 첫 줄 표지와 장면을 싸는 `<script>` 태그는 빼고 그 안의 글이다. */
function sceneBody(card: string): string {
  const open = card.indexOf("<script>");
  const close = card.lastIndexOf("</script>");
  return open === -1 || close < open ? "" : card.slice(open + "<script>".length, close);
}

/** 글에 든 금지 문자열과 `import` 문. */
function forbiddenIn(text: string): string[] {
  const found = FORBIDDEN.filter((needle) => text.toLowerCase().includes(needle));
  return IMPORT_STATEMENT.test(text) ? [...found, "import 문"] : found;
}

/** CSS 의 `url(…)` 주소. */
function urlsOf(css: string): string[] {
  return [...css.matchAll(/url\(\s*(["']?)([^"')]*)\1\s*\)/g)].map((match) => match[2] ?? "");
}

let scratch = "";
let out = "";
let pathsFile = "";
let report: unknown = null;
let code = -1;

beforeAll(() => {
  scratch = mkdtempSync(join(tmpdir(), "assemble-test-"));
  out = join(scratch, "out");
  pathsFile = join(scratch, "paths.json");
  ({ report, code } = run(["assemble", "--out", out, "--paths", pathsFile]));
}, 300_000);

afterAll(() => {
  rmSync(scratch, { recursive: true, force: true });
});

const read = (path: string): string => readFileSync(join(out, path), "utf-8");

describe("짓기 명령의 산출", () => {
  test("짓기는 0 으로 끝나고 보고가 파일 수와 카드 이름과 바이트를 든다", () => {
    const files = walk(out);
    const bytes = files.reduce((sum, file) => sum + statSync(join(out, file)).size, 0);

    expect(code).toBe(0);
    expect(report).toMatchObject({
      command: "assemble",
      ok: true,
      files: files.length,
      cards: expectedCards().map((card) => card.name),
      bytes,
    });
  });

  test("카드는 showcase 스토리를 가진 컴포넌트마다 하나이고 첫 줄의 무리가 그 층 폴더 이름이다", () => {
    const cards = walk(out).filter((file) => /^components\/[^/]+\/preview\.html$/.test(file));
    const expected = expectedCards();

    expect(cards).toEqual(
      expected.map((card) => `components/${card.name}/preview.html`).sort(byPath),
    );
    for (const card of expected) {
      const text = read(`components/${card.name}/preview.html`);
      const lines = text.split("\n");
      expect(lines[0]).toBe(`<!-- @dsCard group="${card.layer}" -->`);
      expect(lines[1]).toBe(`<div id="root" data-ui-root></div>`);
      expect(lines[2]?.startsWith("<script>")).toBe(true);
      expect(text.endsWith("</script>\n")).toBe(true);
      expect(text.split("<script>")).toHaveLength(2);
    }
  });

  test("카드마다 같은 폴더의 README 가 컴포넌트 옆 쓰임 설명과 같은 바이트다", () => {
    for (const card of expectedCards()) {
      const readme = readFileSync(join(out, "components", card.name, "README.md"));
      const source = readFileSync(join(COMPONENTS, card.layer, `${card.name}.md`));
      expect(readme.equals(source), card.name).toBe(true);
    }
  });

  test("묶음 JS 의 첫 줄이 format 4 의 머리이고 컴포넌트 목록이 카드 이름과 같은 차례다", () => {
    const [head = ""] = read("components/bundle.js").split("\n", 1);
    const json = /^\/\* @ds-bundle: (.*) \*\/$/.exec(head)?.[1] ?? "null";

    expect(JSON.parse(json)).toEqual({
      format: 4,
      namespace: "AgentOsUi",
      components: expectedCards().map((card) => ({ name: card.name })),
    });
  });

  test("묶음 JS 와 장면 본문에 금지 문자열과 import 문이 없다", () => {
    expect(forbiddenIn(read("components/bundle.js"))).toEqual([]);
    for (const card of expectedCards()) {
      expect(
        forbiddenIn(sceneBody(read(`components/${card.name}/preview.html`))),
        card.name,
      ).toEqual([]);
    }
  });

  test("크기가 형식의 한도 아래다", () => {
    const size = (path: string): number => statSync(join(out, path)).size;

    expect(size("components/bundle.js")).toBeLessThanOrEqual(6_000_000);
    expect(size("components/bundle.css")).toBeLessThanOrEqual(2_000_000);
    for (const card of expectedCards()) {
      expect(size(`components/${card.name}/preview.html`)).toBeLessThanOrEqual(256_000);
      expect(size(`components/${card.name}/README.md`)).toBeLessThanOrEqual(64_000);
    }
  });

  test("글꼴 주소가 파일마다 정한 앞머리이고 가리키는 글꼴 파일이 모두 있다", () => {
    const fonts = new Set(walk(join(out, "fonts")));
    const sheets = [
      ["fonts/fonts.css", "./"],
      ["_ds_bundle.css", "./fonts/"],
      ["components/bundle.css", "../../fonts/"],
    ] as const;
    const named = sheets.map(([path]) =>
      urlsOf(read(path)).filter((url) => !url.startsWith("data:")),
    );

    // 파일마다 앞머리가 틀린 주소와 가리키는 파일이 없는 주소를 앞의 셋까지 모아 한 번에 맞댄다.
    const seen = sheets.map(([path, prefix], index) => {
      const urls = named[index] ?? [];
      return {
        path,
        hasUrls: urls.length > 0,
        misplaced: urls
          .filter((url) => !url.startsWith(prefix) || url.slice(prefix.length).includes("/"))
          .slice(0, 3),
        missing: urls.filter((url) => !fonts.has(url.slice(prefix.length))).slice(0, 3),
      };
    });
    expect(seen).toEqual(
      sheets.map(([path]) => ({ path, hasUrls: true, misplaced: [], missing: [] })),
    );
    expect(named[1]?.map((url) => url.slice("./fonts/".length))).toEqual(
      named[0]?.map((url) => url.slice("./".length)),
    );
    expect(named[2]?.map((url) => url.slice("../../fonts/".length))).toEqual(
      named[0]?.map((url) => url.slice("./".length)),
    );
  });

  test("옛 이름의 묶음 JS 가 정식 자리와 같고 styles.css 가 글꼴 CSS 와 옛 묶음 CSS 를 차례로 들인다", () => {
    const imports = [...read("styles.css").matchAll(/@import\s+(?:url\()?["']([^"']+)["']/g)].map(
      (match) => match[1],
    );

    expect(read("_ds_bundle.js")).toBe(read("components/bundle.js"));
    expect(imports).toEqual(["./fonts/fonts.css", "./_ds_bundle.css"]);
  });

  test("경로 목록은 산출 폴더를 훑은 것을 project/ 아래 경로 차례로 두 칸 들여쓴 JSON 이다", () => {
    const text = readFileSync(pathsFile, "utf-8");
    const expected = walk(out).map((file) => `project/${file}`);

    expect(text).toBe(`${JSON.stringify(expected, null, 2)}\n`);
    expect(expected.every((path) => path.startsWith("project/"))).toBe(true);
    expect([...expected].sort(byPath)).toEqual(expected);
  });

  test("산출에 짓기의 임시 폴더 경로와 산출 폴더 경로가 없다", () => {
    const needles = [ASSEMBLE_TEMP_PREFIX, out, out.split(sep).join("/"), tmpdir()].map((needle) =>
      needle.toLowerCase(),
    );
    const leaked = walk(out)
      .filter((file) => !/\.woff2?$/.test(file))
      .filter((file) => needles.some((needle) => read(file).toLowerCase().includes(needle)));

    expect(leaked).toEqual([]);
  });
});

describe("짓기 명령의 규칙 판정", () => {
  interface Failure {
    readonly kind: ErrorKind;
    readonly message: string;
  }

  /** 판정이 던진 오류의 종류와 문구. 지나면 `null` 이다. 명령도 같은 판정으로 멈춘다. */
  function failureOf(folder: string): Failure | null {
    try {
      assertAssembled(folder);
      return null;
    } catch (error) {
      if (error instanceof CommandError) {
        return { kind: error.kind, message: error.message };
      }
      throw error;
    }
  }

  /** 지은 산출의 사본을 `change` 로 고친 뒤 판정한 오류. */
  function judgeChanged(label: string, change: (copy: string) => void): Failure | null {
    const copy = join(scratch, `judged-${label}`);
    cpSync(out, copy, { recursive: true });
    change(copy);
    return failureOf(copy);
  }

  /** 사본의 파일 끝에 공백을 붙여 한도보다 한 바이트 크게 한다. */
  function pad(copy: string, path: string, limit: number): void {
    const file = join(copy, path);
    const text = readFileSync(file, "utf-8");
    writeFileSync(file, text + " ".repeat(limit + 1 - Buffer.byteLength(text)));
  }

  const card = (): string => expectedCards()[0]?.name ?? "";

  test("지은 산출은 판정을 지난다", () => {
    expect(failureOf(out)).toBeNull();
  });

  test("카드 폴더의 README 가 없으면 판정이 input 오류로 멈춘다", () => {
    const failure = judgeChanged("readme", (copy) => {
      rmSync(join(copy, "components", card(), "README.md"));
    });

    expect(failure).toEqual({ kind: "input", message: `components/${card()}/README.md 가 없다` });
  });

  test("장면 본문에 </script 가 있으면 판정이 input 오류로 멈춘다", () => {
    const failure = judgeChanged("script-close", (copy) => {
      const file = join(copy, "components", card(), "preview.html");
      writeFileSync(file, readFileSync(file, "utf-8").replace("<script>", "<script>'</script>';"));
    });

    expect(failure).toEqual({
      kind: "input",
      message: `components/${card()}/preview.html 의 장면에 </script 가 있다`,
    });
  });

  test("장면 본문에 import 문이 있으면 판정이 input 오류로 멈춘다", () => {
    const failure = judgeChanged("import", (copy) => {
      const file = join(copy, "components", card(), "preview.html");
      writeFileSync(file, readFileSync(file, "utf-8").replace("<script>", '<script>import"x";'));
    });

    expect(failure).toEqual({
      kind: "input",
      message: `components/${card()}/preview.html 의 장면에 import 문이 있다`,
    });
  });

  test("묶음 JS 에 React 19 의 요소 표식이 있으면 판정이 input 오류로 멈춘다", () => {
    const failure = judgeChanged("transitional", (copy) => {
      const file = join(copy, "components", "bundle.js");
      writeFileSync(
        file,
        `${readFileSync(file, "utf-8")}\nSymbol.for("react.transitional.element");`,
      );
    });

    expect(failure).toEqual({
      kind: "input",
      message: "components/bundle.js 에 react.transitional.element 가 있다",
    });
  });

  test("한도를 넘는 파일이 있으면 판정이 넘은 파일마다의 문구를 이은 limit 오류로 멈춘다", () => {
    const failure = judgeChanged("limits", (copy) => {
      pad(copy, "components/bundle.js", 6_000_000);
      pad(copy, "components/bundle.css", 2_000_000);
      pad(copy, `components/${card()}/preview.html`, 256_000);
      pad(copy, `components/${card()}/README.md`, 64_000);
    });

    expect(failure).toEqual({
      kind: "limit",
      message: [
        "components/bundle.js 가 6000000 바이트를 넘는다(6000001)",
        "components/bundle.css 가 2000000 바이트를 넘는다(2000001)",
        `components/${card()}/preview.html 가 256000 바이트를 넘는다(256001)`,
        `components/${card()}/README.md 가 64000 바이트를 넘는다(64001)`,
      ].join("; "),
    });
  });

  test("한도를 넘으면서 다른 규칙도 어기면 판정이 input 오류로 멈춘다", () => {
    const failure = judgeChanged("limit-and-readme", (copy) => {
      pad(copy, "components/bundle.css", 2_000_000);
      rmSync(join(copy, "components", card(), "README.md"));
    });

    expect(failure).toEqual({
      kind: "input",
      message: [
        "components/bundle.css 가 2000000 바이트를 넘는다(2000001)",
        `components/${card()}/README.md 가 없다`,
      ].join("; "),
    });
  });

  test("목록 파일이 산출 폴더 안이면 아무것도 쓰지 않고 usage 오류로 끝난다", () => {
    const inside = join(scratch, "inside");

    const outcome = run(["assemble", "--out", inside, "--paths", join(inside, "paths.json")]);

    expect(outcome.code).toBe(1);
    expect(outcome.report).toMatchObject({
      command: "assemble",
      ok: false,
      error: { kind: "usage", message: "--paths 를 산출 폴더 밖에 둔다" },
    });
    expect(existsSync(inside)).toBe(false);
  });

  test("비지 않은 산출 폴더를 받으면 아무것도 쓰지 않고 오류로 끝난다", () => {
    const busy = join(scratch, "busy");
    const busyPaths = join(scratch, "busy-paths.json");
    mkdirSync(busy);
    writeFileSync(join(busy, "keep.txt"), "남긴다");

    const outcome = run(["assemble", "--out", busy, "--paths", busyPaths]);

    expect(outcome.code).toBe(1);
    expect(outcome.report).toMatchObject({
      command: "assemble",
      ok: false,
      error: { kind: "output", message: `${busy} 가 비어 있지 않다. 아무것도 쓰지 않는다` },
    });
    expect(walk(busy)).toEqual(["keep.txt"]);
    expect(() => statSync(busyPaths)).toThrow();
  });

  test("임시 폴더를 만들지 못하면 아무것도 쓰지 않고 output 오류로 끝난다", () => {
    const missing = join(scratch, "no-temp");
    const target = join(scratch, "no-temp-out");
    const targetPaths = join(scratch, "no-temp-paths.json");
    // `tmpdir()` 은 부를 때마다 환경 변수를 읽고, 윈도는 TEMP·TMP 를, 그 밖은 TMPDIR·TMP·TEMP 를 차례로 본다. 셋을 모두
    // 없는 폴더로 두면 어느 쪽에서든 그 폴더를 고른다.
    for (const name of ["TEMP", "TMP", "TMPDIR"]) {
      vi.stubEnv(name, missing);
    }
    try {
      const outcome = run(["assemble", "--out", target, "--paths", targetPaths]);

      expect(outcome.code).toBe(1);
      expect(outcome.report).toMatchObject({
        command: "assemble",
        ok: false,
        error: { kind: "output" },
      });
      // 문구 끝에 `mkdtemp` 가 고른 무작위 경로가 붙어 앞부분만 본다.
      expect(JSON.stringify(outcome.report)).toContain('"message":"임시 폴더를 만들 수 없다: ');
    } finally {
      vi.unstubAllEnvs();
    }
    expect(existsSync(target)).toBe(false);
    expect(existsSync(targetPaths)).toBe(false);
  });
});

/** 받아 둔 페이지 토큰 CSS 의 사본. 테마 id 가 `<테마>-<모드>` 이고 층이 없다. 페이지가 카드 문서에 싣는 꼴이다. */
const PAGE_TOKENS = readFileSync(join(import.meta.dirname, "fixtures", "page-tokens.css"), "utf-8");
/** 시험 문서의 출처. 요청 가로채기(`route`)가 산출 폴더를 이 출처로 내준다. */
const ORIGIN = "http://card.test";

/** 패키지의 React 19 에서 전역 React·ReactDOM 을 내는 IIFE. 패키지에 그런 파일(UMD)이 없어 시험이 짓는다. */
function reactGlobals(work: string): string {
  const posix = (path: string): string => path.split(sep).join("/");
  mkdirSync(work, { recursive: true });
  const entry = join(work, "react-globals.mjs");
  const outDir = join(work, "react-globals");
  const modules = join(UI_PACKAGE, "node_modules");
  writeFileSync(
    entry,
    `import * as React from "react";
import * as ReactDOM from "react-dom";
import { createRoot } from "react-dom/client";
window.React = React;
window.ReactDOM = { ...ReactDOM, createRoot };
`,
  );
  // 엔트리가 패키지 밖이라 맨 이름 import 를 패키지의 React 로 돌린다.
  viteBuild(
    work,
    "react-globals",
    `export default {
  root: ${JSON.stringify(posix(UI_PACKAGE))},
  publicDir: false,
  logLevel: "warn",
  define: { "process.env.NODE_ENV": '"production"' },
  resolve: {
    alias: {
      react: ${JSON.stringify(posix(join(modules, "react")))},
      "react-dom": ${JSON.stringify(posix(join(modules, "react-dom")))},
    },
  },
  build: {
    outDir: ${JSON.stringify(posix(outDir))},
    emptyOutDir: false,
    minify: true,
    lib: { entry: ${JSON.stringify(posix(entry))}, formats: ["iife"], name: "__reactGlobals", fileName: () => "out.js" },
  },
};
`,
  );
  return readFileSync(join(outDir, "out.js"), "utf-8").replaceAll("</script", "<\\/script");
}

/** 카드 문서에서 본 것. */
interface Seen {
  /** `[data-scene]` 의 수와 그 가운데 요소를 품은 것의 수. */
  readonly sections: number;
  readonly filled: number;
  /** 실린 Noto Sans KR 글꼴의 수와 실리지 못한 글꼴의 수. */
  readonly korean: number;
  readonly fontErrors: number;
  /** `#root` 아래 바탕색이 빨강인 요소의 수. */
  readonly red: number;
  /** 페이지 오류와 콘솔 오류. */
  readonly errors: readonly string[];
}

/** 그려진 뒤의 장면, 글꼴, 색을 모으는 식. 시험의 tsconfig 에는 DOM 타입이 없어 글로 넘긴다. */
const SEEN = `(async () => {
  const frame = () => new Promise((resolve) => requestAnimationFrame(() => setTimeout(resolve, 0)));
  await frame();
  await frame();
  await document.fonts.ready;
  await new Promise((resolve) => setTimeout(resolve, 200));
  await document.fonts.ready;
  const faces = [...document.fonts];
  const sections = [...document.querySelectorAll("[data-scene]")];
  const root = document.getElementById("root");
  const elements = root === null ? [] : [...root.querySelectorAll("*")];
  return {
    sections: sections.length,
    filled: sections.filter((section) => section.childElementCount > 0).length,
    korean: faces.filter((face) => face.family.replaceAll('"', "") === "Noto Sans KR" && face.status === "loaded").length,
    fontErrors: faces.filter((face) => face.status === "error").length,
    red: elements.filter((element) => getComputedStyle(element).backgroundColor === "rgb(255, 0, 0)").length,
  };
})()`;

function count(seen: unknown, key: string): number {
  const value = isRecord(seen) ? seen[key] : undefined;
  return typeof value === "number" ? value : -1;
}

describe("chromium 그리기", () => {
  let browser: Browser | undefined;
  let react = "";

  beforeAll(async () => {
    react = reactGlobals(join(scratch, "react"));
    browser = await chromium.launch();
  }, 300_000);

  afterAll(async () => {
    await browser?.close();
  });

  /** 페이지와 같은 차례(토큰 CSS, 묶음 CSS, React 전역, 묶음 JS, 카드)로 실은 카드 문서. 테마는 페이지 id 의 꼴이다. */
  function cardDocument(name: string, tokens: string): string {
    return `<!doctype html><html data-theme="nokcheong-light" data-mode="light" style="color-scheme:light" class="nokcheong-light light"><head><meta charset="utf-8"></head><body>
<style>${tokens}</style><style>${read("components/bundle.css")}</style>
<script>${react}</script><script>${read("components/bundle.js")}</script>
${read(`components/${name}/preview.html`)}</body></html>`;
  }

  /** 카드 문서를 산출 폴더의 `components/<이름>/preview.html` 자리에서 띄워 본 것. */
  async function show(name: string, tokens: string): Promise<Seen> {
    if (browser === undefined) {
      throw new Error("브라우저가 뜨지 않았다");
    }
    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));
    page.on("console", (message) => {
      if (message.type() === "error") {
        errors.push(`console: ${message.text()}`);
      }
    });
    await page.route(`${ORIGIN}/**`, async (route) => {
      const { pathname } = new URL(route.request().url());
      if (pathname === `/components/${name}/preview.html`) {
        await route.fulfill({
          contentType: "text/html; charset=utf-8",
          body: cardDocument(name, tokens),
        });
        return;
      }
      const parts = decodeURIComponent(pathname)
        .split("/")
        .filter((part) => part !== "");
      const file = join(out, ...parts);
      await (existsSync(file)
        ? route.fulfill({ path: file })
        : route.fulfill({ status: 404, body: "" }));
    });
    try {
      await page.goto(`${ORIGIN}/components/${name}/preview.html`);
      const seen: unknown = await page.evaluate(SEEN);
      return {
        sections: count(seen, "sections"),
        filled: count(seen, "filled"),
        korean: count(seen, "korean"),
        fontErrors: count(seen, "fontErrors"),
        red: count(seen, "red"),
        errors,
      };
    } finally {
      await page.close();
    }
  }

  test.each(expectedCards())(
    "$name 카드는 showcase 스토리 수만큼 장면이 그려지고 오류가 없으며 한글 글꼴이 실린다",
    async (card) => {
      const seen = await show(card.name, PAGE_TOKENS);

      // 한 객체로 맞대어 실패가 어긋난 칸을 모두 diff 에 보인다.
      expect({
        errors: seen.errors,
        sections: seen.sections,
        filled: seen.filled,
        fontErrors: seen.fontErrors,
      }).toEqual({ errors: [], sections: card.scenes, filled: card.scenes, fontErrors: 0 });
      expect(seen.korean).toBeGreaterThan(0);
    },
  );

  test("층 밖에서 디자인 토큰 하나를 덮은 토큰 CSS 를 실으면 그 토큰을 쓰는 요소의 색이 바뀐다", async () => {
    const plain = await show("Button", PAGE_TOKENS);
    const edited = await show(
      "Button",
      `${PAGE_TOKENS}\n[data-theme="nokcheong-light"] { --primary: #ff0000; }\n`,
    );

    expect(plain.red).toBe(0);
    expect(edited.red).toBeGreaterThan(0);
  });
});
