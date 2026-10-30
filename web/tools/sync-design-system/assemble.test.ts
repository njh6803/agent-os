// 짓기 명령(assemble)의 테스트(design-card-build 명세 Testing Decisions "이음매", "자리", "파일 검사"와 그 2026-10-29
// 주석). 명령을 임시 폴더로 한 번 돌리고, 같은 산출 폴더를 파일 검사와 규칙 판정과 chromium 그리기가 함께 읽는다. 짓기는
// 패키지의 vite·Tailwind CLI 를 열두 번 남짓 띄워 한 번에 십몇 초가 든다.
//
// 사용 규약은 README 원본(`artifact-source/README.md`)이고 디자인 에이전트가 읽는다. 컴포넌트가 `className`·`style` 을
// 받지 않아, 에이전트의 배치는 묶음 CSS 에 있는 클래스와 `var(--…)` 로만 짓는다는 것이 요지다. 클래스 목록은 소스가
// 클래스를 더하거나 빼면 바뀌므로, 다시 올릴 때 README 를 고쳐 쓰지 않고 README 가 든 이름을 여기서 정식 자리의
// 묶음(`components/bundle.css`·`components/bundle.js`)과 다시 맞댄다. 판정이 README 의 문장 모양에 기대므로 README 를
// 고쳐 모양이 바뀌면 여기도 고친다. 내보내기는 묶음 JS 를 글로 풀지 않고 chromium 에서 실은 뒤의 전역 `AgentOsUi` 로
// 본다(압축한 IIFE 라 내보내기 블록의 꼴이 짓는 도구를 따라 바뀐다).

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
import { buildTokensJson, DEFAULT_CSS } from "./build.ts";
import { CommandError, type ErrorKind } from "./command.ts";
import { byPath, isRecord } from "./io.ts";
import { run } from "./main.ts";

const WEB = dirname(dirname(import.meta.dirname));
const REPO = dirname(WEB);
const COMPONENTS = join(WEB, "packages", "ui", "src", "components");
/** 산출에 바이트 그대로 놓이는 저장소 원본. */
const README_SOURCE = join(import.meta.dirname, "artifact-source", "README.md");
const FOUNDATIONS_SOURCE = join(import.meta.dirname, "artifact-source", "foundations");
const WEB_DESIGN_SOURCE = join(REPO, ".claude", "rules", "web-design.md");
/** 기초 카드 넷의 폴더. 폴더가 빠지거나 이름이 바뀌면 그 카드가 말없이 빠진 채 올라간다. */
const FOUNDATIONS = ["colors", "density", "spacing", "type"];
const DS_CARD = /^<!--\s*@dsCard\s+group="[^"]*"[^>]*-->$/;
/** 스토리 파일 글에서 태그 `showcase` 가 든 `tags` 배열. 명령과 따로 세어 그리기 시험이 장면 수와 맞댄다. */
const SHOWCASE_TAGS = /\btags:\s*\[[^\]]*["']showcase["'][^\]]*\]/g;
// 파일 검사의 금지 문자열은 명령의 판정과 따로 짓되 그보다 느슨하지 않게 둔다(대소문자는 모두 가리지 않는다).
const FORBIDDEN = ["</script", "<!--", "require(", "react.transitional.element"];
const IMPORT_STATEMENT = /(?:^|[;\n}])\s*import\s*[\w$*{"']/;

interface StoryFile {
  readonly name: string;
  readonly layer: string;
  readonly path: string;
  /** 소스 글에서 센 showcase 스토리의 수. */
  readonly scenes: number;
}

/** 층 폴더의 스토리 파일. 층의 차례, 같은 층 안에서는 이름 차례다. */
function layerStoryFiles(): StoryFile[] {
  return LAYERS.flatMap((layer) =>
    readdirSync(join(COMPONENTS, layer))
      .filter((file) => file.endsWith(".stories.tsx"))
      .map((file) => {
        const path = join(COMPONENTS, layer, file);
        return {
          name: file.slice(0, -".stories.tsx".length),
          layer,
          path,
          scenes: (readFileSync(path, "utf-8").match(SHOWCASE_TAGS) ?? []).length,
        };
      })
      .sort((left, right) => byPath(left.name, right.name)),
  );
}

/** 층 폴더의 스토리 파일 가운데 showcase 스토리를 가진 것. 층의 차례, 같은 층 안에서는 이름 차례다. */
function expectedCards(): StoryFile[] {
  return layerStoryFiles().filter((card) => card.scenes > 0);
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

/** 글의 백틱 묶음 안 글. */
function ticks(text: string): string[] {
  return [...text.matchAll(/`([^`]+)`/g)].map((match) => match[1] ?? "");
}

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** README 에서 `pattern` 의 첫 묶음. 없으면 던져 그 사례가 빨갛다(문장 모양이 바뀌었다). */
function section(md: string, pattern: RegExp, what: string): string {
  const found = pattern.exec(md)?.[1];
  if (found === undefined) {
    throw new Error(`README 에서 ${what} 를 찾지 못했다`);
  }
  return found;
}

/**
 * CSS 에 클래스 선택자가 있는지. 선택자의 클래스 글자(`hover\:bg-bg-hover`, `w-3\/10`)가 있고 바로 뒤가 이름 글자가
 * 아니어야 한다. `.flex` 가 `.flex-col` 안에서, `.border` 가 `.border-border` 안에서 맞지 않게 한다.
 */
function hasClass(css: string, name: string): boolean {
  const selector = `.${name.replace(/[:/.[\]%]/g, (char) => `\\${char}`)}`;
  return new RegExp(`${escapeRegExp(selector)}(?![\\w\\\\-])`).test(css);
}

/** CSS 에 `--이름:` 선언이 있는지. 앞이 다른 이름 글자가 아니어야 한다(`--text-body--line-height:` 안의 `--line-height:`). */
function declares(css: string, name: string): boolean {
  return new RegExp(`(?<![a-z0-9-])${escapeRegExp(name)}\\s*:`).test(css);
}

function hasSelector(css: string, attribute: string, key: string): boolean {
  return css.includes(`[${attribute}="${key}"]`) || css.includes(`[${attribute}=${key}]`);
}

/**
 * README 가 든 `--이름` 변수. "테마의 재료" 문장(원색 토큰)의 것은 쓰지 말라는 예시라 빼고, `<이름>` 이 든 자리 표시는
 * 통째로 걷고(남기면 `--text-<이름>--line-height` 에서 `--line-height` 가 뽑힌다), 여백 줄의 `-2` 꼴은 `--spacing-2` 로 푼다.
 */
function readmeVariables(md: string): string[] {
  const variables = new Set<string>();
  for (const raw of md.split("\n")) {
    if (raw.includes("테마의 재료")) {
      continue;
    }
    const line = raw.replace(/--[a-z0-9-]*<[^>]*>[a-z0-9-]*/g, "");
    for (const [name] of line.matchAll(/--[a-z][a-z0-9-]*(?:--[a-z0-9-]+)?/g)) {
      if (!name.endsWith("-")) {
        variables.add(name);
      }
    }
    if (line.includes("--spacing-")) {
      for (const token of ticks(line).filter((token) => /^-\d+$/.test(token))) {
        variables.add(`--spacing${token}`);
      }
    }
  }
  return [...variables];
}

/** README 의 `AgentOsUi.<이름>` 과 예시의 `const { … } = window.AgentOsUi` 가 든 이름. */
function readmeExports(md: string): string[] {
  const names = new Set(
    [...md.matchAll(/AgentOsUi\.([A-Z_][A-Za-z0-9_]*)/g)].map((match) => match[1] ?? ""),
  );
  for (const match of md.matchAll(/const \{([^}]+)\} = window\.AgentOsUi/g)) {
    for (const name of (match[1] ?? "").split(",").map((part) => part.trim())) {
      if (name !== "") {
        names.add(name);
      }
    }
  }
  return [...names];
}

/**
 * README 가 `` `data-theme`(…) ``·`` `data-density`(…) `` 의 값으로 든 키. 괄호 안의 백틱 낱말을 모두 키로 본다. 옛 검사처럼
 * 글자(`^[a-z]+$`)로 거르면 이름이 바뀐 키(`ocean-2`)가 선택자를 보지 않은 채 말없이 빠진다.
 */
function readmeKeys(md: string, attribute: string): string[] {
  return ticks(section(md, new RegExp(`\`${attribute}\`\\(([^)]*)\\)`), `${attribute} 의 값`));
}

interface StoryBlock {
  readonly name: string;
  readonly body: string;
}

/** 스토리 파일 글을 맨 앞 줄의 `const`·`export const` 마다 끊은 덩이와 그 이름. */
function storyBlocks(text: string): StoryBlock[] {
  const starts = [...text.matchAll(/^(?:export )?const (\w+)/gm)];
  return starts.map((match, index) => ({
    name: match[1] ?? "",
    body: text.slice(match.index, starts[index + 1]?.index ?? text.length),
  }));
}

/**
 * 덩이와, 그 덩이가 펼쳐 넣는(`...이름`) 같은 파일의 덩이를 거듭 따라간 것. 펼친 덩이의 필드도 물려받는다. `...이름.args`
 * 처럼 필드 하나만 펼쳐도 그 덩이 전체를 따라가 더 엄격하게 본다.
 */
function withSpreads(start: StoryBlock, blocks: readonly StoryBlock[]): StoryBlock[] {
  const byName = new Map(blocks.map((block) => [block.name, block]));
  const seen = new Set<StoryBlock>();
  const queue = [start];
  for (let block = queue.pop(); block !== undefined; block = queue.pop()) {
    if (seen.has(block)) {
      continue;
    }
    seen.add(block);
    for (const match of block.body.matchAll(/\.\.\.(\w+)/g)) {
      const spread = byName.get(match[1] ?? "");
      if (spread !== undefined) {
        queue.push(spread);
      }
    }
  }
  return [...seen];
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

  test("tokens.json 은 build 가 패키지의 디자인 토큰 CSS 에서 짓는 것과 같은 바이트다", () => {
    expect(read("tokens.json")).toBe(buildTokensJson(readFileSync(DEFAULT_CSS, "utf-8")));
  });

  test("tokens.json 의 테마 이름은 모두 (Light) 나 (Dark) 로 끝나고 그 낱말이 테마 id 의 모드와 같다", () => {
    const parsed: unknown = JSON.parse(read("tokens.json"));
    const color = isRecord(parsed) ? parsed["color"] : undefined;
    const themes = isRecord(color) && Array.isArray(color["themes"]) ? color["themes"] : [];
    const named = themes.map((theme) => ({
      id: isRecord(theme) ? String(theme["id"]) : "",
      name: isRecord(theme) ? String(theme["name"]) : "",
    }));

    expect(named.length).toBeGreaterThan(0);
    // 모드 낱말이 이름 끝에 없거나 id 의 모드와 다른 테마.
    const word = (id: string): string =>
      id.endsWith("-dark")
        ? " (Dark)"
        : id.endsWith("-light")
          ? " (Light)"
          : " (id 에 모드가 없다)";
    expect(named.filter((theme) => !theme.name.endsWith(word(theme.id)))).toEqual([]);
  });

  test("README.md 는 README 원본의 바이트 그대로다", () => {
    expect(readFileSync(join(out, "README.md")).equals(readFileSync(README_SOURCE))).toBe(true);
  });

  test("기초 카드 넷이 폴더마다 HTML 하나로 있고 첫 줄이 @dsCard 표지이며 원본과 같은 바이트다", () => {
    const files = walk(join(out, "foundations"));
    // 넷은 모두 있어야 하고, 넷 밖의 폴더도 HTML 하나와 표지를 지킨다(옛 검사가 모든 폴더를 봤다).
    const folders = [
      ...new Set([
        ...FOUNDATIONS,
        ...files.filter((file) => file.includes("/")).map((file) => file.split("/", 1)[0] ?? ""),
      ]),
    ].sort();
    const seen = folders.map((folder) => {
      const htmls = files.filter((file) => file.startsWith(`${folder}/`) && file.endsWith(".html"));
      return {
        folder,
        htmls: htmls.length,
        marked: htmls.every((file) =>
          DS_CARD.test(read(`foundations/${file}`).split("\n", 1)[0] ?? ""),
        ),
        same: htmls.every((file) => {
          const source = join(FOUNDATIONS_SOURCE, file);
          return (
            existsSync(source) &&
            readFileSync(join(out, "foundations", file)).equals(readFileSync(source))
          );
        }),
      };
    });

    expect(seen).toEqual(folders.map((folder) => ({ folder, htmls: 1, marked: true, same: true })));
    expect(files).toEqual(walk(FOUNDATIONS_SOURCE));
  });

  test("guidelines 의 web-design.md 는 규칙 파일의 바이트이고 index.md 는 그 파일 하나를 가리키는 목록이다", () => {
    expect(walk(join(out, "guidelines"))).toEqual(["index.md", "web-design.md"]);
    expect(
      readFileSync(join(out, "guidelines", "web-design.md")).equals(
        readFileSync(WEB_DESIGN_SOURCE),
      ),
    ).toBe(true);
    // 아티팩트 판 1793259788-d3cd 의 그 파일과 같은 바이트다. 2026-10-30 Artifact 도구의 read 가 그 판의 46 바이트와
    // sha256 a9bd8e3a… 를 냈고, 지은 파일과 cmp 로 맞댔다(손으로 봤다).
    expect(read("guidelines/index.md")).toBe("# Guidelines\n\n- [web-design](./web-design.md)\n");
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

describe("사용 규약: README 와 기초 카드가 드는 이름이 묶음에 있다", () => {
  const md = (): string => read("README.md");
  const css = (): string => read("components/bundle.css");

  test("README 가 이미 있다고 든 유틸리티 클래스가 묶음 CSS 에 모두 있다", () => {
    const names = section(
      md(),
      /이미 있는 유틸리티 클래스: `([^`]+)`/s,
      "'이미 있는 유틸리티 클래스' 묶음",
    )
      .split(/\s+/)
      .filter((name) => name !== "");

    expect(names.length).toBeGreaterThan(0);
    expect({ missingClasses: names.filter((name) => !hasClass(css(), name)) }).toEqual({
      missingClasses: [],
    });
  });

  test("README 가 CSS 가 없다고 든 흔한 Tailwind 이름은 묶음 CSS 에 없다", () => {
    const names = ticks(
      section(md(), /흔한\s+Tailwind 이름 가운데([\s\S]*?)CSS 가 없어/, "'CSS 가 없다'는 문장"),
    );
    // 끝이 `:` 인 것은 변형이고 `.<변형>\:` 꼴로 찾는다.
    const present = names.filter((name) =>
      name.endsWith(":") ? css().includes(`.${name.slice(0, -1)}\\:`) : hasClass(css(), name),
    );

    expect(names.length).toBeGreaterThan(0);
    expect({ presentButSaidAbsent: present }).toEqual({ presentButSaidAbsent: [] });
  });

  test("README 가 든 CSS 변수는 묶음 CSS 에 선언이 있다", () => {
    const names = readmeVariables(md());

    expect(names.length).toBeGreaterThan(0);
    expect({ undeclared: names.filter((name) => !declares(css(), name)) }).toEqual({
      undeclared: [],
    });
  });

  test("README 가 data-theme·data-density 의 값으로 든 키마다 묶음 CSS 에 그 선택자가 있다", () => {
    const attributes = ["data-theme", "data-density"].map((attribute) => ({
      attribute,
      keys: readmeKeys(md(), attribute),
    }));

    // 속성마다 센다. 합쳐 세면 한 속성의 키가 모두 빠져도 다른 속성의 키로 지난다.
    expect({
      withoutKeys: attributes
        .filter(({ keys }) => keys.length === 0)
        .map(({ attribute }) => attribute),
    }).toEqual({ withoutKeys: [] });
    expect({
      noSelector: attributes.flatMap(({ attribute, keys }) =>
        keys
          .filter((key) => !hasSelector(css(), attribute, key))
          .map((key) => `${attribute}=${key}`),
      ),
    }).toEqual({ noSelector: [] });
  });

  test("기초 카드가 읽는 변수는 묶음 CSS 에 선언이 있고 카드가 쓰는 data-theme·data-density 값은 선택자가 있다", () => {
    const cards = walk(join(out, "foundations"))
      .filter((file) => file.endsWith(".html"))
      .map((file) => ({ file, text: read(`foundations/${file}`) }));
    const variables = new Set(
      cards.flatMap(({ text }) => [
        ...[...text.matchAll(/var\(\s*(--[a-z][a-z0-9-]*)/g)].map((match) => match[1] ?? ""),
        ...[...text.matchAll(/data-value="(--[a-z][a-z0-9-]*)"/g)].map((match) => match[1] ?? ""),
      ]),
    );
    const selectors = cards.flatMap(({ file, text }) =>
      [...text.matchAll(/(data-theme|data-density)="([^"]+)"/g)].map((match) => ({
        file,
        attribute: match[1] ?? "",
        key: match[2] ?? "",
      })),
    );

    expect(variables.size).toBeGreaterThan(0);
    expect({
      cardUndeclared: [...variables].filter((name) => !declares(css(), name)),
      cardNoSelector: selectors
        .filter(({ attribute, key }) => !hasSelector(css(), attribute, key))
        .map(({ file, attribute, key }) => `${file} ${attribute}=${key}`),
    }).toEqual({ cardUndeclared: [], cardNoSelector: [] });
  });
});

describe("산출 밖: 층 폴더의 스토리 파일", () => {
  test("층 폴더의 스토리 파일마다 showcase 스토리가 하나 이상 있다", () => {
    // 없으면 그 컴포넌트의 카드가 말없이 빠진다.
    expect({
      withoutShowcase: layerStoryFiles()
        .filter((file) => file.scenes === 0)
        .map((file) => file.name),
    }).toEqual({ withoutShowcase: [] });
  });

  test("showcase 스토리와 그 파일의 meta 에 globals 가 없다", () => {
    // 카드의 테마와 모드는 페이지가 정해, 스토리가 고른 globals 는 카드에 닿지 않는다. meta 의 것은 모든 스토리가 물려받고,
    // 펼쳐 넣은(`...이름`) 스토리의 것은 펼친 스토리가 물려받는다. 펼친 것은 `<스토리> <펼친 덩이>` 로 든다.
    const showcase = new RegExp(SHOWCASE_TAGS.source);
    const files = layerStoryFiles().map((file) => {
      const text = readFileSync(file.path, "utf-8");
      const blocks = storyBlocks(text);
      const meta = /^export default (\w+);?$/m.exec(text)?.[1];
      return { name: file.name, blocks, meta: blocks.find((block) => block.name === meta) };
    });

    expect({
      metaNotFound: files.filter((file) => file.meta === undefined).map((file) => file.name),
      globalsInShowcase: files.flatMap((file) =>
        file.blocks
          .filter((block) => block === file.meta || showcase.test(block.body))
          .flatMap((block) =>
            withSpreads(block, file.blocks)
              .filter((source) => /\bglobals\s*:/.test(source.body))
              .map((source) =>
                source === block
                  ? `${file.name} ${block.name}`
                  : `${file.name} ${block.name} ${source.name}`,
              ),
          ),
      ),
    }).toEqual({ metaNotFound: [], globalsInShowcase: [] });
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

  test("사용 규약: README 가 든 AgentOsUi 의 이름은 묶음이 전역으로 내보내고, 컴포넌트 이름이면 묶음 머리의 목록에도 있다", async () => {
    if (browser === undefined) {
      throw new Error("브라우저가 뜨지 않았다");
    }
    const page = await browser.newPage();
    let keys: unknown;
    try {
      await page.setContent(
        `<!doctype html><html><head><meta charset="utf-8"></head><body><script>${react}</script><script>${read("components/bundle.js")}</script></body></html>`,
      );
      keys = await page.evaluate("Object.keys(window.AgentOsUi ?? {})");
    } finally {
      await page.close();
    }
    const exported = new Set(Array.isArray(keys) ? keys.map(String) : []);
    const [head = ""] = read("components/bundle.js").split("\n", 1);
    const parsed: unknown = JSON.parse(/^\/\* @ds-bundle: (.*) \*\/$/.exec(head)?.[1] ?? "null");
    const listed = new Set(
      (isRecord(parsed) && Array.isArray(parsed["components"]) ? parsed["components"] : []).map(
        (component) => (isRecord(component) ? String(component["name"]) : ""),
      ),
    );
    const names = readmeExports(read("README.md"));
    // 대문자 뒤에 소문자가 오는 이름(`Card`)이 컴포넌트이고, `THEMES`·`DEFAULT_THEME` 은 아니다.
    const isComponent = (name: string): boolean => /^[A-Z][a-z]/.test(name);

    expect(names.length).toBeGreaterThan(0);
    expect({
      notExported: names.filter((name) => !exported.has(name)),
      notListed: names.filter((name) => isComponent(name) && !listed.has(name)),
    }).toEqual({ notExported: [], notListed: [] });
  });
});
