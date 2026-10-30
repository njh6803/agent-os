// 설정 화면의 테마 구역(ThemePicker)(admin-style 티켓 09, 그림 mk-settings, mk-settings-m). 스토리는 둘로 가른다. 네
// 카드를 보이는 스토리는 사진에 든다. 문서 뿌리는 기본 테마(녹청)이고 카드 안의 표본만 저마다의 테마로 칠해진다. 표본이 그
// 카드 테마의 쓰임새 토큰 값인지 계산값으로 재는 판정 스토리는 뿌리를 기본이 아닌 테마로 두어 사진에서 빠진다(`judgment`).
// 고르면 바로 적용되고 저장되는 행동은 페이지 시험(pages/SettingsPage.theme.test)이 본다. 틀 없이 그리고, 미리보기의
// 데코레이터가 본문 칸과 같은 컨테이너를 두른다.
import { DEFAULT_THEME, THEMES, type ThemeKey } from "@agent-os/ui";
import { SEMANTIC_TOKENS } from "@agent-os/ui/contrast";
import { semanticColor } from "@agent-os/ui/storybook/expect";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import { ThemePicker } from "./ThemePicker";

/** 판정 스토리의 문서 뿌리 테마. 카드의 표본이 뿌리를 물려받지 않는지 가르려고 기본이 아닌 테마로 둔다. */
const JUDGMENT_ROOT: ThemeKey = "jjokbit";

function rootToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/**
 * 창이 화면 중단점 `wide` 이상인가. 넓은 프로젝트(admin-storybook-wide)와 좁은 프로젝트를 가른다. 갈래를 잰 컨테이너
 * 폭으로 고르지 않는다. 그러면 넓은 창에서 데코레이터의 컨테이너가 본문 칸보다 좁게 서도 두 줄 갈래를 단언해 지나간다.
 */
function isWide(): boolean {
  return window.matchMedia(`(min-width: ${rootToken("--breakpoint-wide")})`).matches;
}

/** 테마 묶음의 카드들. 카드는 라디오를 품은 라벨이다. */
function cardsOf(canvasElement: HTMLElement): HTMLElement[] {
  const group = within(canvasElement).getByRole("group", { name: "테마" });
  return within(group)
    .getAllByRole("radio")
    .map((radio) => {
      const card = radio.closest("label");
      if (card === null) {
        throw new Error("라디오를 품은 카드가 없다");
      }
      return card;
    });
}

/** 카드 안의 표본. `data-theme` 을 단 요소다. */
function sampleOf(card: HTMLElement): HTMLElement {
  const sample = card.querySelector<HTMLElement>("[data-theme]");
  if (sample === null) {
    throw new Error("카드 안에 테마를 단 표본이 없다");
  }
  return sample;
}

/** 지금 시스템의 모드. 관리 화면은 문서 뿌리에 모드를 달지 않아 표본도 이 모드의 값을 받는다. */
function systemMode(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

const meta = {
  title: "organisms/ThemePicker",
  component: ThemePicker,
  args: { theme: DEFAULT_THEME, onChoose: fn() },
} satisfies Meta<typeof ThemePicker>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 네 카드. 아무것도 고르지 않아 기본인 녹청이 골라져 있다. 고른 카드는 강조색 두 줄 테두리, 나머지는 조작 테두리다.
 * 넓은 프로젝트에서 한 줄에 넷, 좁은 프로젝트에서 두 줄에 둘씩이다(admin-style 명세 "갈래의 단언").
 */
export const Cards: Story = {
  play: async ({ canvasElement }) => {
    await expect(document.documentElement.getAttribute("data-theme")).toBe(DEFAULT_THEME);
    const cards = cardsOf(canvasElement);
    await expect(cards.map((card) => card.textContent)).toEqual(
      THEMES.map(({ name }) => `${name}승인끝남payments.refund`),
    );
    await expect(cards.map((card) => sampleOf(card).dataset["theme"])).toEqual(
      THEMES.map(({ key }) => key),
    );
    for (const [index, card] of cards.entries()) {
      const chosen = THEMES[index]?.key === DEFAULT_THEME;
      const style = getComputedStyle(card);
      await expect([style.borderTopWidth, style.borderTopColor]).toEqual(
        chosen
          ? ["2px", semanticColor(card, "accent")]
          : ["1px", semanticColor(card, "border-control")],
      );
      await expect(sampleOf(card).hasAttribute("data-mode")).toBe(false);
      await expect(sampleOf(card).inert).toBe(true);
    }
    await expect(canvasElement).toHaveTextContent("모드(라이트·다크)는 시스템 설정을 따른다.");

    const tops = cards.map((card) => Math.round(card.getBoundingClientRect().top));
    const lefts = cards.map((card) => Math.round(card.getBoundingClientRect().left));
    if (isWide()) {
      await expect(new Set(tops).size).toBe(1);
      await expect(lefts).toEqual([...lefts].sort((a, b) => a - b));
      await expect(new Set(lefts).size).toBe(4);
    } else {
      const [first = 0, second = 0, third = 0, fourth = 0] = tops;
      await expect([second, fourth]).toEqual([first, third]);
      await expect(third).toBeGreaterThan(first);
      const [left = 0, right = 0, nextLeft = 0, nextRight = 0] = lefts;
      await expect([nextLeft, nextRight]).toEqual([left, right]);
      await expect(right).toBeGreaterThan(left);
    }
  },
};

/**
 * 판정: 카드의 표본이 그 카드 테마의 지금 시스템 모드 값을 쓰임새 토큰 전부에서 받는다. 기준은 같은 테마에 그 모드를
 * 명시한 요소다. 문서 뿌리를 쪽빛으로 두어 표본이 뿌리를 물려받는 구현을 가른다. 테마 넷의 기준 강조색이 서로 다른 것과
 * 뿌리가 쪽빛의 값인 것을 먼저 본다. 둘이 아니면 맞대기가 테마를 가르지 못한다.
 */
export const SampleTokens: Story = {
  tags: ["judgment"],
  globals: { theme: JUDGMENT_ROOT },
  play: async ({ canvasElement }) => {
    const html = document.documentElement;
    await expect(html.getAttribute("data-theme")).toBe(JUDGMENT_ROOT);
    await expect(html.hasAttribute("data-mode")).toBe(false);

    const mode = systemMode();
    const references = new Map<ThemeKey, HTMLElement>();
    for (const { key } of THEMES) {
      const reference = document.createElement("span");
      reference.dataset["theme"] = key;
      reference.dataset["mode"] = mode;
      reference.append(document.createElement("span"));
      canvasElement.append(reference);
      references.set(key, reference);
    }
    const tokenOf = (element: Element, name: string): string =>
      getComputedStyle(element).getPropertyValue(`--${name}`).trim();
    const referenceOf = (theme: ThemeKey): HTMLElement => {
      const reference = references.get(theme);
      if (reference === undefined) {
        throw new Error(`${theme} 의 기준이 없다`);
      }
      return reference;
    };

    try {
      await expect(new Set(THEMES.map(({ key }) => tokenOf(referenceOf(key), "accent"))).size).toBe(
        THEMES.length,
      );
      await expect(tokenOf(html, "accent")).toBe(tokenOf(referenceOf(JUDGMENT_ROOT), "accent"));

      for (const card of cardsOf(canvasElement)) {
        const sample = sampleOf(card);
        const theme = THEMES.find(({ key }) => key === sample.dataset["theme"])?.key;
        if (theme === undefined) {
          throw new Error(`표본의 테마가 목록에 없다: ${String(sample.dataset["theme"])}`);
        }
        const reference = referenceOf(theme);
        await expect(SEMANTIC_TOKENS.map((name) => [name, tokenOf(sample, name)])).toEqual(
          SEMANTIC_TOKENS.map((name) => [name, tokenOf(reference, name)]),
        );
        // 표본이 칠한 바탕과 글자도 그 테마의 값이다. 쓰임새 유틸리티가 표본의 범위에서 풀린다.
        const probe = reference.firstElementChild ?? reference;
        const painted = getComputedStyle(sample);
        await expect([painted.backgroundColor, painted.color]).toEqual([
          semanticColor(probe, "bg"),
          semanticColor(probe, "text"),
        ]);
      }
    } finally {
      for (const reference of references.values()) {
        reference.remove();
      }
    }
  },
};
