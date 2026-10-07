// 디자인 토큰의 판정 스토리. 열 벌(테마 다섯 × 모드 둘)의 쓰임새 토큰과 명암비, 기준 폭 둘, 글꼴 일곱 벌, rem 0,
// shadow root 의 계산값을 실제 chromium 에서 본다. `judgment` 태그를 단 이 스토리들은 사진 비교(`visual/`)가 찍지 않는다.
// 쓰임새 토큰의 값은 디자인 파일과 맞대지 않는다. 형식(#RRGGBB), 테마 사이의 차이, 명암비로 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, waitFor } from "storybook/test";
import { Button } from "../components/atoms/Button";
import { ShadowFrame } from "../storybook/ShadowFrame";
import { sheetsDefining } from "../testing";
import { MODES, THEMES } from "../themes";
import { CONTRAST_PAIRS, SEMANTIC_TOKENS, contrastFailures } from "./contrast";
import themeCss from "./theme.css?inline";

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

export const Matrix: Story = {
  name: "열 벌 모두 쓰임새 토큰 26개가 #RRGGBB 로 풀리고 명암비 짝 43개가 기준을 넘는다",
  render: () => (
    <div data-sample="matrix" className="bg-bg p-4 text-text">
      테마 표
    </div>
  ),
  play: async ({ canvasElement }) => {
    const target = element(canvasElement, "[data-sample=matrix]");
    const malformed: string[] = [];
    const failures: string[] = [];
    const accents = new Map<string, Set<string>>(MODES.map((mode) => [mode, new Set<string>()]));
    for (const { key } of THEMES) {
      for (const mode of MODES) {
        target.dataset["theme"] = key;
        target.dataset["mode"] = mode;
        const style = getComputedStyle(target);
        const value = (name: string): string => style.getPropertyValue(`--${name}`).trim();
        for (const name of SEMANTIC_TOKENS) {
          if (!/^#[0-9a-f]{6}$/i.test(value(name))) {
            malformed.push(`${key}/${mode} --${name} "${value(name)}"`);
          }
        }
        accents.get(mode)?.add(value("accent").toLowerCase());
        if (malformed.length === 0) {
          failures.push(...contrastFailures(key, mode, value));
        }
      }
    }
    await expect([SEMANTIC_TOKENS.length, CONTRAST_PAIRS.length]).toEqual([26, 43]);
    await expect(malformed).toEqual([]);
    await expect(failures).toEqual([]);
    await expect(Object.fromEntries([...accents].map(([mode, set]) => [mode, set.size]))).toEqual({
      light: THEMES.length,
      dark: THEMES.length,
    });
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
  ["JetBrains Mono", 400, "a"],
  ["JetBrains Mono", 500, "a"],
  ["IBM Plex Mono", 400, "a"],
  ["IBM Plex Mono", 500, "a"],
] as const;

export const Fonts: Story = {
  name: "글꼴 일곱 벌이 모두 적재된다",
  render: () => (
    <div className="flex flex-col gap-4">
      {THEMES.map(({ key, name }) => (
        <div key={key} data-theme={key} className="bg-bg p-4 text-text">
          <p className="font-sans text-body">{name}: 승인을 기다리고 있습니다.</p>
          <p className="font-sans text-body font-mid">허가하거나 거부해 주세요.</p>
          <p className="font-sans text-body font-strong">실행이 실패했습니다.</p>
          <p className="font-mono text-code font-medium">payments.refund</p>
        </div>
      ))}
    </div>
  ),
  play: async () => {
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

export const ShadowRoot: Story = {
  name: "shadow 안의 계산값이 문서와 같고 사이트의 * 규칙이 감싼 요소 안에 닿지 않는다",
  render: () => (
    <div className="flex flex-col gap-4">
      <div data-sample="document" data-theme="muk" data-mode="light" data-ui-root="">
        {SHADOW_SAMPLE}
      </div>
      <ShadowFrame shadow="on" css={themeCss} theme="muk" mode="light">
        {SHADOW_SAMPLE}
      </ShadowFrame>
    </div>
  ),
  play: async ({ canvasElement }) => {
    const host = element(canvasElement, "[data-shadow-frame]");
    await waitFor(() => expect(host.shadowRoot?.querySelector("button")).not.toBeNull());
    const shadow = host.shadowRoot;
    if (shadow === null) {
      throw new Error("shadow root 가 없다");
    }
    // 문서 쪽을 먼저 읽는다. 미리보기가 디자인 토큰 CSS 를 전역으로 실어, 그대로 두면 문서의 @property 등록과 :root
    // 변수가 shadow 안에 닿아 보정 없이도 같아 보인다(ADR 0026). 그래서 문서의 시트를 모두 끄고 shadow 를 읽는다.
    const expected = computed(element(canvasElement, "[data-sample=document]"));
    const sheets = Array.from(document.styleSheets);
    const before = sheets.map((sheet) => sheet.disabled);
    const site = document.createElement("style");
    site.textContent = SITE_RULE;
    try {
      for (const sheet of sheets) {
        sheet.disabled = true;
      }
      const isolated = computed(shadow);
      document.head.append(site);
      const underSite = computed(shadow);
      await expect(isolated).toEqual(expected);
      await expect(underSite).toEqual(expected);
      await expect(getComputedStyle(host).fontFamily).toBe("serif");
    } finally {
      site.remove();
      sheets.forEach((sheet, index) => {
        sheet.disabled = before[index] ?? false;
      });
    }
  },
};
