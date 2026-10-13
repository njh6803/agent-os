// 디자인 토큰의 판정 스토리. 여덟 벌(테마 넷 × 모드 둘)의 쓰임새 토큰과 명암비, 기준 폭 둘, 글꼴 다섯 벌, rem 0,
// `@theme` 토큰이 모두 CSS 변수로 나오는 것, shadow root 의 계산값을 실제 chromium 에서 본다. `judgment` 태그를 단 이 스토리들은 사진 비교(`visual/`)가 찍지 않는다.
// 쓰임새 토큰의 값은 디자인 파일과 맞대지 않는다. 형식(#RRGGBB, 반투명은 #RRGGBBAA), 테마 사이의 차이, 명암비로 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, waitFor } from "storybook/test";
import { Button } from "../components/atoms/Button";
import { ShadowFrame } from "../storybook/ShadowFrame";
import { sheetsDefining } from "../testing";
import { DEFAULT_THEME, MODES, THEMES, type Mode, type ThemeKey } from "../themes";
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

export const Responsive: Story = {
  name: "기준 폭 둘이 359px 과 360px 사이와 시트의 조건 둘에서 갈린다",
  render: () => (
    <div data-sample="container" className="@container" style={{ width: 320 }}>
      <div data-sample="row" className="flex flex-col gap-2 @wide:flex-row wide:gap-4">
        <span>거부</span>
        <span>승인</span>
      </div>
    </div>
  ),
  play: async ({ canvasElement }) => {
    const container = element(canvasElement, "[data-sample=container]");
    const row = element(canvasElement, "[data-sample=row]");
    const directions: string[] = [];
    for (const width of [359, 360]) {
      container.style.width = `${String(width)}px`;
      directions.push(`${String(width)} ${getComputedStyle(row).flexDirection}`);
    }
    await expect(directions).toEqual(["359 column", "360 row"]);
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
      <p data-sample="mono" className="font-mono text-code font-regular">
        payments.refund(amount=1200)
      </p>
      <p className="font-mono text-code font-medium">payments.refund</p>
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

export const ShadowRoot: Story = {
  name: "shadow 안의 계산값이 기본 테마 라이트와 군청 다크 모두 문서와 같고 사이트의 * 규칙이 감싼 요소 안에 닿지 않는다",
  render: () => (
    <div className="flex flex-col gap-4">
      {SHADOW_PAIRS.map(([theme, mode]) => (
        <div key={theme} data-pair={theme} className="flex flex-col gap-4">
          <div
            data-sample="document"
            data-theme={theme}
            data-mode={mode}
            data-ui-root=""
            className="bg-bg"
          >
            {SHADOW_SAMPLE}
          </div>
          <ShadowFrame shadow="on" css={themeCss} theme={theme} mode={mode}>
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
