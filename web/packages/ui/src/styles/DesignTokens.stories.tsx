// 디자인 토큰의 판정 스토리. 여덟 벌(테마 넷 × 모드 둘)의 쓰임새 토큰과 명암비, 밀도 두 벌, 기준 폭 다섯, 글꼴 다섯 벌,
// rem 0, `@theme` 토큰이 모두 CSS 변수로 나오는 것, 떠 있는 것의 그림자, shadow root 의 계산값을 실제 chromium 에서
// 본다. `judgment` 태그를 단 이 스토리들은 사진 비교(`visual/`)가 찍지 않는다.
// 쓰임새 토큰의 값은 디자인 파일과 맞대지 않는다. 형식(#RRGGBB, 반투명은 #RRGGBBAA), 테마 사이의 차이, 명암비로 본다.
// 밀도 변수는 디자인 파일의 값 그대로라 그 값과 맞댄다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, waitFor } from "storybook/test";
import { Button } from "../components/atoms/Button";
import { ShadowFrame } from "../storybook/ShadowFrame";
import { semanticColor } from "../storybook/expect";
import { sheetsDefining } from "../testing";
import {
  DEFAULT_THEME,
  DENSITIES,
  MODES,
  THEMES,
  type Density as DensityKey,
  type Mode,
  type ThemeKey,
} from "../themes";
import {
  CONTRAST_PAIRS,
  SEMANTIC_TOKENS,
  TRANSLUCENT_TOKENS,
  contrastFailures,
  type SemanticToken,
} from "./contrast";
import themeCss from "./theme.css?inline";
import themeSource from "./theme.css?raw";

// 태그는 글자 그대로 적는다. Storybook 의 색인이 정적으로 읽어 상수를 받지 않는다(태그 둘은 storybook/preview.tsx 머리).
const meta = {
  title: "디자인 토큰/판정",
  tags: ["judgment"],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

function designSheets(): CSSStyleSheet[] {
  return sheetsDefining("--gray-50", document.styleSheets);
}

function element(root: HTMLElement, selector: string): HTMLElement {
  const found = root.querySelector(selector);
  if (!(found instanceof HTMLElement)) {
    throw new Error(`표본이 없다: ${selector}`);
  }
  return found;
}

/** 시트의 규칙 전부(`@import` 한 시트 안까지). */
function allRules(sheet: CSSStyleSheet): CSSRule[] {
  return Array.from(sheet.cssRules).flatMap((rule) =>
    rule instanceof CSSImportRule && rule.styleSheet !== null ? allRules(rule.styleSheet) : [rule],
  );
}

// 테마가 바꾸지 않는 것의 표본. 테마 블록이 글꼴이나 크기를 다시 정하면 여덟 벌의 값이 갈린다.
const THEME_FREE = ["--sans", "--mono", "--radius-m"] as const;

// 주 버튼이 강조색인 테마. 나머지는 글자색을 뒤집은 먹색이다(ADR 0026 의 셋째 2026-10-12 이력).
const ACCENT_PRIMARY: readonly ThemeKey[] = ["guncheong", "jacho"];

/**
 * 한 벌의 주 버튼 묶음이 그 테마의 갈래인지. 강조색 갈래는 `primary` 가 `accent` 와, 먹색 갈래는 `text` 와 같고, 다크의
 * `on-primary` 는 강조색 갈래에서 `on-accent`, 먹색 갈래에서 `bg` 와 같다(라이트는 두 갈래 모두 `bg-raised` 와 같은
 * 흰색이라 가르지 않는다). 이웃 토큰과 맞대므로 디자인 파일을 읽지 않는다. 어긋나면 메시지 하나씩이다.
 */
function primaryBranchFailures(
  at: string,
  key: ThemeKey,
  dark: boolean,
  value: (name: string) => string,
): string[] {
  const accent = ACCENT_PRIMARY.includes(key);
  const expected: [string, string][] = [["primary", accent ? "accent" : "text"]];
  if (dark) {
    expected.push(["on-primary", accent ? "on-accent" : "bg"]);
  }
  return expected
    .filter(([name, twin]) => value(name).toLowerCase() !== value(twin).toLowerCase())
    .map(
      ([name, twin]) => `${at} --${name} "${value(name)}" 가 --${twin} "${value(twin)}" 와 다르다`,
    );
}

/** 쓰임새 토큰의 형식. 반투명 넷은 알파까지 든 hex 8자리다. */
function wellFormed(name: SemanticToken, value: string): boolean {
  const translucent: readonly string[] = TRANSLUCENT_TOKENS;
  return (translucent.includes(name) ? /^#[0-9a-f]{8}$/i : /^#[0-9a-f]{6}$/i).test(value);
}

export const Matrix: Story = {
  name: "여덟 벌 모두 쓰임새 토큰 23개가 풀리고 명암비 짝 43개가 기준을 넘으며 주 버튼이 테마의 갈래이고 글꼴과 모서리는 테마마다 같다",
  render: () => (
    <div data-sample="matrix" className="bg-bg p-4 text-text">
      테마 표
    </div>
  ),
  play: async ({ canvasElement }) => {
    const target = element(canvasElement, "[data-sample=matrix]");
    const malformed: string[] = [];
    const failures: string[] = [];
    const branches: string[] = [];
    const accents = new Map<string, Set<string>>(MODES.map((mode) => [mode, new Set<string>()]));
    const themeFree = new Map<string, Set<string>>(THEME_FREE.map((name) => [name, new Set()]));
    for (const { key } of THEMES) {
      for (const mode of MODES) {
        target.dataset["theme"] = key;
        target.dataset["mode"] = mode;
        const style = getComputedStyle(target);
        const value = (name: string): string => style.getPropertyValue(`--${name}`).trim();
        for (const name of SEMANTIC_TOKENS) {
          if (!wellFormed(name, value(name))) {
            malformed.push(`${key}/${mode} --${name} "${value(name)}"`);
          }
        }
        accents.get(mode)?.add(value("accent").toLowerCase());
        for (const name of THEME_FREE) {
          themeFree.get(name)?.add(style.getPropertyValue(name).trim());
        }
        branches.push(...primaryBranchFailures(`${key}/${mode}`, key, mode === "dark", value));
        if (malformed.length === 0) {
          failures.push(...contrastFailures(key, mode, value));
        }
      }
      // 모드 속성이 없으면 시스템 설정을 따른다. 그 갈래(`@media (prefers-color-scheme: …)` 안의 덮기)도 본다.
      delete target.dataset["mode"];
      const style = getComputedStyle(target);
      branches.push(
        ...primaryBranchFailures(`${key}/system`, key, style.colorScheme === "dark", (name) =>
          style.getPropertyValue(`--${name}`).trim(),
        ),
      );
    }
    await expect([SEMANTIC_TOKENS.length, CONTRAST_PAIRS.length]).toEqual([23, 43]);
    await expect({ keys: THEMES.map(({ key }) => key), default: DEFAULT_THEME }).toEqual({
      keys: ["guncheong", "nokcheong", "jacho", "jjokbit"],
      default: "nokcheong",
    });
    await expect(malformed).toEqual([]);
    await expect(failures).toEqual([]);
    await expect(branches).toEqual([]);
    await expect(Object.fromEntries([...accents].map(([mode, set]) => [mode, set.size]))).toEqual({
      light: THEMES.length,
      dark: THEMES.length,
    });
    // 여덟 벌이 한 값이고 그 값이 비지 않았다.
    await expect(
      Object.fromEntries(
        [...themeFree].map(([name, set]) => [name, set.size === 1 && !set.has("")]),
      ),
    ).toEqual({ "--sans": true, "--mono": true, "--radius-m": true });
  },
};

// 밀도 변수 일곱의 값(디자인 파일의 밀도 두 벌, design-refresh 명세의 "밀도").
const DENSITY_VALUES = {
  compact: {
    "--body-size": "14px",
    "--body-lh": "20px",
    "--table-size": "13px",
    "--table-lh": "18px",
    "--mono-size": "13px",
    "--row-h": "36px",
    "--control-h": "32px",
  },
  regular: {
    "--body-size": "15px",
    "--body-lh": "22px",
    "--table-size": "14px",
    "--table-lh": "20px",
    "--mono-size": "14px",
    "--row-h": "44px",
    "--control-h": "40px",
  },
} as const satisfies Record<DensityKey, Record<string, string>>;

const DENSITY_VARIABLES = Object.keys(DENSITY_VALUES.compact);

const OPPOSITE_DENSITY: Readonly<Record<DensityKey, DensityKey>> = {
  compact: "regular",
  regular: "compact",
};

/** 요소에서 풀린 밀도 변수 일곱. */
function densityVariables(target: Element): Record<string, string> {
  const style = getComputedStyle(target);
  return Object.fromEntries(
    DENSITY_VARIABLES.map((name) => [name, style.getPropertyValue(name).trim()]),
  );
}

/** 밀도를 따르는 유틸리티 다섯과 감싼 요소가 풀린 계산값. */
function densityUtilities(sample: HTMLElement): Record<string, string> {
  const style = (part: string): CSSStyleDeclaration =>
    getComputedStyle(element(sample, `[data-part=${part}]`));
  return {
    control: style("control").height,
    body: `${style("body").fontSize}/${style("body").lineHeight}`,
    table: `${style("table").fontSize}/${style("table").lineHeight}`,
    mono: `${style("mono").fontSize}/${style("mono").lineHeight}`,
    row: style("row").height,
    wrapper: `${style("wrapper").fontSize}/${style("wrapper").lineHeight}`,
  };
}

/** 그 밀도의 변수 값에서 나와야 할 유틸리티와 감싼 요소의 계산값. 고정폭의 줄 높이는 표의 줄 높이다. */
function expectedUtilities(density: DensityKey): Record<string, string> {
  const value = DENSITY_VALUES[density];
  return {
    control: value["--control-h"],
    body: `${value["--body-size"]}/${value["--body-lh"]}`,
    table: `${value["--table-size"]}/${value["--table-lh"]}`,
    mono: `${value["--mono-size"]}/${value["--table-lh"]}`,
    row: value["--row-h"],
    wrapper: `${value["--body-size"]}/${value["--body-lh"]}`,
  };
}

// 표본마다 반대 밀도의 조상 안에 둔다. 스토리 테스트의 창(1200×900)에서 속성이 없는 문서 뿌리는 촘촘이라, 뿌리에서
// 물려받기만 해도 맞는 자리를 피한다(design-refresh 명세의 Density 주석). 감싼 요소(`data-ui-root`)도 넣는다. 그 규칙이
// 밀도의 별칭을 `var()` 로 읽으면 별칭이 뿌리에 선언으로 나오고(design-refresh 프로브 `tailwind.mjs`) 뿌리의 밀도로
// 풀린 값이 물려져 보통 표본이 빨갛다(design-refresh 변이 표 `density_sizes_mutations.toml`).
export const Density: Story = {
  name: "data-density 가 촘촘과 보통이면 밀도 변수 일곱이 디자인 파일의 값이고 유틸리티와 감싼 요소가 그 값을 따르며 여덟 벌에서 같다",
  render: () => (
    <div className="flex flex-col gap-4 bg-bg p-4 text-text">
      {DENSITIES.map((density) => (
        <div key={density} data-density={OPPOSITE_DENSITY[density]}>
          <div data-sample={density} data-density={density} className="flex flex-col gap-2">
            <div data-part="control" className="h-control bg-bg-raised" />
            <p data-part="body" className="text-body">
              승인을 기다리고 있습니다.
            </p>
            <p data-part="table" className="text-table">
              실행 2024-1187
            </p>
            <p data-part="mono" className="font-mono text-mono">
              run_01JA7Q2W0D
            </p>
            <div data-part="row" className="h-row bg-bg-raised" />
            <div data-part="wrapper" data-ui-root="">
              감싼 요소
            </div>
          </div>
        </div>
      ))}
    </div>
  ),
  play: async ({ canvasElement }) => {
    const measured: Record<string, unknown> = {};
    const expected: Record<string, unknown> = {};
    const themed: string[] = [];
    for (const density of DENSITIES) {
      const sample = element(canvasElement, `[data-sample=${density}]`);
      measured[density] = {
        variables: densityVariables(sample),
        utilities: densityUtilities(sample),
      };
      expected[density] = {
        variables: DENSITY_VALUES[density],
        utilities: expectedUtilities(density),
      };
      // 테마와 모드는 밀도를 바꾸지 않는다. 테마 블록이 밀도 변수를 다시 정하면 여덟 벌의 값이 갈린다.
      for (const { key } of THEMES) {
        for (const mode of MODES) {
          sample.dataset["theme"] = key;
          sample.dataset["mode"] = mode;
          const variables = densityVariables(sample);
          if (JSON.stringify(variables) !== JSON.stringify(DENSITY_VALUES[density])) {
            themed.push(`${density} ${key}/${mode} ${JSON.stringify(variables)}`);
          }
        }
      }
      delete sample.dataset["theme"];
      delete sample.dataset["mode"];
    }
    await expect(measured).toEqual(expected);
    await expect(themed).toEqual([]);
  },
};

// Tailwind 는 쓰인 변형만 규칙을 내므로(어림, admin-style 명세의 Testing Decisions "패키지" 주석) 기준 폭마다 표본을
// 둔다. 기준 폭마다의 쓰임은 디자인 토큰 CSS(`theme.css`)의 기준 폭 주석이다.
export const Responsive: Story = {
  name: "기준 폭이 359px·360px 사이와 783px·784px 사이에서 갈리고 시트의 조건 셋에 들며, 최대 폭 form 과 content 가 440px 과 880px 이다",
  render: () => (
    <div className="flex flex-col gap-2">
      <div data-sample="container" className="@container" style={{ width: 320 }}>
        <div data-sample="wide" className="flex flex-col gap-2 @wide:flex-row wide:gap-4">
          <span>거부</span>
          <span>승인</span>
        </div>
        <div data-sample="split" className="flex flex-col gap-2 @split:flex-row">
          <span>이벤트</span>
          <span>결정</span>
        </div>
      </div>
      <div data-sample="form" className="max-w-form">
        관리 토큰
      </div>
      <div data-sample="content" className="max-w-content">
        플러그인
      </div>
    </div>
  ),
  play: async ({ canvasElement }) => {
    const container = element(canvasElement, "[data-sample=container]");
    const wide = element(canvasElement, "[data-sample=wide]");
    const split = element(canvasElement, "[data-sample=split]");
    const directions: string[] = [];
    for (const width of [359, 360, 783, 784]) {
      container.style.width = `${String(width)}px`;
      directions.push(
        `${String(width)} ${getComputedStyle(wide).flexDirection} ${getComputedStyle(split).flexDirection}`,
      );
    }
    await expect(directions).toEqual([
      "359 column column",
      "360 row column",
      "783 row column",
      "784 row row",
    ]);
    await expect({
      form: getComputedStyle(element(canvasElement, "[data-sample=form]")).maxWidth,
      content: getComputedStyle(element(canvasElement, "[data-sample=content]")).maxWidth,
    }).toEqual({ form: "440px", content: "880px" });
    const conditions = new Set<string>();
    const visit = (list: CSSRuleList): void => {
      for (const rule of list) {
        if (rule instanceof CSSMediaRule || rule instanceof CSSContainerRule) {
          conditions.add(rule.conditionText);
        }
        if (rule instanceof CSSGroupingRule || rule instanceof CSSStyleRule) {
          visit(rule.cssRules);
        }
      }
    };
    for (const sheet of designSheets()) {
      visit(sheet.cssRules);
    }
    await expect([...conditions].filter((text) => text.includes("px")).sort()).toEqual([
      "(width >= 360px)",
      "(width >= 768px)",
      "(width >= 784px)",
    ]);
  },
};

const FONT_FACES = [
  ["Noto Sans KR", 400, "가"],
  ["Noto Sans KR", 500, "가"],
  ["Noto Sans KR", 600, "가"],
  ["Noto Sans Mono", 400, "a"],
  ["Noto Sans Mono", 500, "a"],
] as const;

export const Fonts: Story = {
  name: "글꼴 다섯 벌이 모두 적재되고 본문과 고정폭이 그 글꼴로 그려진다",
  render: () => (
    <div className="flex flex-col gap-2 bg-bg p-4 text-text">
      <p data-sample="sans" className="font-sans text-body font-regular">
        승인을 기다리고 있습니다.
      </p>
      <p className="font-sans text-body font-medium">허가하거나 거부해 주세요.</p>
      <p className="font-sans text-body font-semibold">실행이 실패했습니다.</p>
      <p data-sample="mono" className="font-mono text-mono font-regular">
        payments.refund(amount=1200)
      </p>
      <p className="font-mono text-mono font-medium">payments.refund</p>
    </div>
  ),
  play: async ({ canvasElement }) => {
    // 적재는 글꼴 이름만 본다. 글꼴 변수가 비거나 다른 이름이면 적재는 초록이어도 그림은 대체 글꼴이라 계산값도 본다.
    const firstFamily = (selector: string): string =>
      getComputedStyle(element(canvasElement, selector))
        .fontFamily.split(",")[0]
        ?.trim()
        .replace(/^"|"$/g, "") ?? "";
    await expect({
      sans: firstFamily("[data-sample=sans]"),
      mono: firstFamily("[data-sample=mono]"),
    }).toEqual({ sans: "Noto Sans KR", mono: "Noto Sans Mono" });
    // 그 굵기의 글꼴이 없으면 브라우저는 가장 가까운 굵기를 받아도 `loaded` 로 답한다. 받은 글꼴의 굵기까지 본다.
    const missing: string[] = [];
    for (const [family, weight, sample] of FONT_FACES) {
      const faces = await document.fonts.load(`${String(weight)} 16px "${family}"`, sample);
      const exact = faces.filter((face) => face.weight === String(weight));
      if (exact.length === 0 || exact.some((face) => face.status !== "loaded")) {
        missing.push(
          `${family} ${String(weight)}: ${faces.map((face) => `${face.weight} ${face.status}`).join(", ") || "없음"}`,
        );
      }
    }
    await expect(missing).toEqual([]);
  },
};

/**
 * 디자인 토큰 CSS 소스에서 `@theme` 블록(inline 이 아닌 것)의 맨 위 단계 토큰 이름. `--*: initial` 과
 * `@keyframes` 안의 선언은 뺀다.
 */
function themeTokenNames(source: string): string[] {
  const start = source.search(/@theme (?:static )?\{/);
  if (start === -1) {
    throw new Error("디자인 토큰 CSS 에 inline 이 아닌 @theme 블록이 없다");
  }
  const names: string[] = [];
  let depth = 0;
  for (const line of source.slice(start).split("\n")) {
    const declared = depth === 1 ? /^\s*(--[a-z0-9-]+)\s*:/.exec(line) : null;
    if (declared?.[1] !== undefined) {
      names.push(declared[1]);
    }
    depth += (line.match(/\{/g) ?? []).length - (line.match(/\}/g) ?? []).length;
    if (depth === 0) {
      break;
    }
  }
  return names;
}

// Tailwind v4 는 쓰인 토큰만 CSS 변수로 낸다. 그래서 /design-sync 가 Claude Design 에 올린 CSS 에 소스가 쓰지 않은
// 토큰(제목 글자, 넓은 여백 등)이 없었다(2026-10-12 첫 /design-sync). `@theme static` 이 모두 낸다. 아래 셋은 블록을
// 바로 읽었는지 보는 표본이다. 이 파일이 글자로 적어 Tailwind 가 쓰인 것으로 보므로 판정은 나머지 이름이 가른다.
export const ThemeTokensEmitted: Story = {
  name: "@theme 의 디자인 토큰은 쓰이지 않아도 모두 문서 뿌리에서 풀린다",
  render: () => <p className="text-body">토큰</p>,
  play: async () => {
    const names = themeTokenNames(themeSource);
    const root = getComputedStyle(document.documentElement);
    const unresolved = names.filter((name) => root.getPropertyValue(name).trim() === "");
    await expect(names).toEqual(
      expect.arrayContaining(["--text-title", "--spacing-8", "--radius-s"]),
    );
    await expect(unresolved).toEqual([]);
  },
};

// 떠 있는 것(위젯 창, 메뉴)의 그림자 `float`. 그림자 색(`--shadow-color`)이 모드마다 달라, 유틸리티가 그 색을 놓인
// 요소에서 읽어야 한다. 모드마다 하나씩 그려 뿌리와 다른 모드에서도 그 자리의 색인지 본다. 그림자 색을 모드와 무관한
// 값으로 두면 빨갛다(design-refresh 변이 표 `density_sizes_mutations.toml`).
export const FloatShadow: Story = {
  name: "떠 있는 것의 그림자 float 는 두 겹이고 색이 놓인 자리의 모드의 shadow-color 다",
  render: () => (
    <div className="flex gap-4">
      {MODES.map((mode) => (
        <div key={mode} data-mode={mode} className="bg-bg p-6 text-text">
          <div data-sample={mode} className="rounded-l bg-bg-raised p-4 shadow-float">
            위젯 창
          </div>
        </div>
      ))}
    </div>
  ),
  play: async ({ canvasElement }) => {
    const shadows = MODES.map((mode) => {
      const sample = element(canvasElement, `[data-sample=${mode}]`);
      const color = semanticColor(sample, "shadow-color");
      return {
        actual: getComputedStyle(sample).boxShadow,
        expected: `${color} 0px 8px 24px 0px, ${color} 0px 1px 2px 0px`,
      };
    });
    // 계산값에는 Tailwind 가 앞에 두는 투명한 고리 그림자들이 붙는다. 끝의 두 겹을 본다.
    for (const { actual, expected } of shadows) {
      await expect(actual.endsWith(expected), `${actual} 의 끝이 ${expected}`).toBe(true);
    }
    await expect(new Set(shadows.map(({ expected }) => expected)).size).toBe(MODES.length);
  },
};

export const RemFree: Story = {
  name: "디자인 토큰 CSS 와 글꼴 CSS 의 시트에 rem 이 없다",
  render: () => <p className="text-body">rem 0</p>,
  play: async () => {
    // 글꼴 CSS 는 `--gray-50` 을 정의하지 않는다. @font-face 로 Noto Sans KR 을 선언하는 시트를 고른다.
    const fontSheets = Array.from(document.styleSheets).filter((sheet) =>
      allRules(sheet).some(
        (rule) =>
          rule instanceof CSSFontFaceRule &&
          rule.style.getPropertyValue("font-family").includes("Noto Sans KR"),
      ),
    );
    const sheets = [...designSheets(), ...fontSheets];
    const rems = sheets.flatMap((sheet) =>
      allRules(sheet).flatMap((rule) =>
        Array.from(
          rule.cssText.matchAll(/(?<![\w.-])-?(?:\d+\.?\d*|\.\d+)rem\b/g),
          ([match]) => match,
        ),
      ),
    );
    await expect({ design: designSheets().length > 0, fonts: fontSheets.length > 0 }).toEqual({
      design: true,
      fonts: true,
    });
    await expect(rems).toEqual([]);
  },
};

// shadow 표본이 견주는 계산값. 상속 속성(글꼴, 글자색, 줄 높이, 자간 등)과 버튼의 모양.
const SHADOW_PROPERTIES = [
  "color",
  "background-color",
  "font-family",
  "font-size",
  "font-weight",
  "font-style",
  "line-height",
  "letter-spacing",
  "word-spacing",
  "text-transform",
  "height",
  "padding-left",
  "border-top-width",
  "border-top-color",
  "border-top-left-radius",
] as const;

// 사이트를 흉내 낸 문서 규칙. 사이트의 `*` 는 호스트 요소를 직접 겨냥해 :host 의 보통 선언을 이긴다(ADR 0026).
const SITE_RULE =
  "* { font-family: serif; color: rgb(255, 0, 0); line-height: 3; letter-spacing: 5px; word-spacing: 9px; text-transform: uppercase; font-style: italic; }";

function computed(root: ParentNode): Record<string, string> {
  const values: Record<string, string> = {};
  for (const [part, selector] of [
    ["text", "[data-part=text]"],
    ["button", "button"],
  ] as const) {
    const target = root.querySelector(selector);
    if (target === null) {
      throw new Error(`표본이 없다: ${selector}`);
    }
    const style = getComputedStyle(target);
    for (const property of SHADOW_PROPERTIES) {
      values[`${part} ${property}`] = style.getPropertyValue(property);
    }
  }
  return values;
}

const SHADOW_SAMPLE = (
  <>
    <p data-part="text">승인을 기다리고 있습니다.</p>
    <Button>승인</Button>
  </>
);

// 문서 쪽과 shadow 쪽에 같이 다는 테마와 모드. 기본 테마 라이트에 더해, 주 버튼을 덮는 `:host(…)` 짝을 지나는 군청
// 다크를 둔다. 군청 다크의 버튼 바탕은 그 덮기가 있어야 문서 쪽과 같다.
const SHADOW_PAIRS = [
  [DEFAULT_THEME, "light"],
  ["guncheong", "dark"],
] as const satisfies readonly (readonly [ThemeKey, Mode])[];

// 문서 뿌리(globals)와 표본 양쪽의 밀도. 표본이 뿌리와 같으면 뿌리에서 물려받은 값으로도 맞아, 감싼 요소가 밀도의 별칭을
// 뿌리에서 풀린 값으로 받는 것을 가린다(design-refresh 명세의 ShadowRoot 주석). shadow 호스트가 촘촘이면 문서의 시트를
// 끈 뒤 `:host([data-density="compact"])` 만이 그 값을 준다.
const SHADOW_ROOT_DENSITY: DensityKey = "regular";
const SHADOW_SAMPLE_DENSITY: DensityKey = "compact";

export const ShadowRoot: Story = {
  name: "shadow 안의 계산값이 기본 테마 라이트와 군청 다크 모두 문서와 같고 뿌리와 다른 밀도의 크기이며 사이트의 * 규칙이 감싼 요소 안에 닿지 않는다",
  globals: { density: SHADOW_ROOT_DENSITY },
  render: () => (
    <div className="flex flex-col gap-4">
      {SHADOW_PAIRS.map(([theme, mode]) => (
        <div key={theme} data-pair={theme} className="flex flex-col gap-4">
          <div
            data-sample="document"
            data-theme={theme}
            data-mode={mode}
            data-density={SHADOW_SAMPLE_DENSITY}
            data-ui-root=""
            className="bg-bg"
          >
            {SHADOW_SAMPLE}
          </div>
          <ShadowFrame
            shadow="on"
            css={themeCss}
            theme={theme}
            mode={mode}
            density={SHADOW_SAMPLE_DENSITY}
          >
            {SHADOW_SAMPLE}
          </ShadowFrame>
        </div>
      ))}
    </div>
  ),
  play: async ({ canvasElement }) => {
    const pairs = SHADOW_PAIRS.map(([theme]) => {
      const pair = element(canvasElement, `[data-pair=${theme}]`);
      return {
        theme,
        document: element(pair, "[data-sample=document]"),
        host: element(pair, "[data-shadow-frame]"),
      };
    });
    const roots = new Map<string, ParentNode>();
    for (const { theme, host } of pairs) {
      await waitFor(() => expect(host.shadowRoot?.querySelector("button")).not.toBeNull());
      if (host.shadowRoot === null) {
        throw new Error(`shadow root 가 없다: ${theme}`);
      }
      roots.set(theme, host.shadowRoot);
    }
    // 문서 쪽을 먼저 읽는다. 미리보기가 디자인 토큰 CSS 를 전역으로 실어, 그대로 두면 문서의 @property 등록과 :root
    // 변수가 shadow 안에 닿아 보정 없이도 같아 보인다(ADR 0026). 그래서 문서의 시트를 모두 끄고 shadow 를 읽는다.
    const expected = Object.fromEntries(
      pairs.map(({ theme, document: sample }) => [theme, computed(sample)]),
    );
    // 문서 쪽이 표본의 밀도로 그려졌다. 양쪽이 같은 틀린 값이면 아래 맞댐은 지나므로 크기를 값으로도 본다. 호스트의
    // 속성도 본다. 창(1200px)에서는 속성이 없는 호스트도 촘촘이라, 틀이 밀도를 빠뜨려도 값은 맞는다.
    await expect(densityVariables(document.documentElement)["--control-h"]).toBe(
      DENSITY_VALUES[SHADOW_ROOT_DENSITY]["--control-h"],
    );
    await expect(pairs.map(({ host }) => host.dataset["density"])).toEqual(
      pairs.map(() => SHADOW_SAMPLE_DENSITY),
    );
    const sampleValue = DENSITY_VALUES[SHADOW_SAMPLE_DENSITY];
    for (const values of Object.values(expected)) {
      await expect({
        text: `${values["text font-size"] ?? ""}/${values["text line-height"] ?? ""}`,
        button: values["button height"],
      }).toEqual({
        text: `${sampleValue["--body-size"]}/${sampleValue["--body-lh"]}`,
        button: sampleValue["--control-h"],
      });
    }
    const sheets = Array.from(document.styleSheets);
    const before = sheets.map((sheet) => sheet.disabled);
    const site = document.createElement("style");
    site.textContent = SITE_RULE;
    const shadowValues = (): Record<string, Record<string, string>> =>
      Object.fromEntries([...roots].map(([theme, root]) => [theme, computed(root)]));
    try {
      for (const sheet of sheets) {
        sheet.disabled = true;
      }
      const isolated = shadowValues();
      document.head.append(site);
      const underSite = shadowValues();
      await expect(isolated).toEqual(expected);
      await expect(underSite).toEqual(expected);
      for (const { host } of pairs) {
        await expect(getComputedStyle(host).fontFamily).toBe("serif");
      }
    } finally {
      site.remove();
      sheets.forEach((sheet, index) => {
        sheet.disabled = before[index] ?? false;
      });
    }
  },
};
