// 판정 함수의 음성 사례. 판정이 늘 지나도 초록이 되지 않게, 심은 클래스와 기준 미달 짝을 판정이 실제로 잡는지 본다
// (design-system 명세 스토리 29~33). 심은 것을 그리므로 afterEach 의 클래스 판정(planted 태그)과 axe 에서 빠진다.
// 컴포넌트 스토리의 계산값 도우미가 조용히 맞지 않는지도 여기서 본다(HelperScope).
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { colorsOf, semanticColor } from "../storybook/expect";
import { judgeClasses } from "../storybook/preview";
import { contrastFailures, type ContrastPair } from "../styles/contrast";
import { arbitraryClasses, classesWithoutRules, composite, contrastRatio, sheetsDefining } from ".";

// 태그는 글자 그대로 적는다(태그 둘은 storybook/preview.tsx 머리). Storybook 의 색인이 정적으로 읽는다.
const meta = {
  title: "디자인 토큰/판정의 음성 사례",
  tags: ["judgment", "planted"],
  parameters: { a11y: { test: "off" } },
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

// 기본 테마를 비운 뒤 CSS 를 만들지 않는 것(text-base, rounded, font-bold, shadow, text-red-500), 원색 토큰 이름
// (bg-gray-500), --spacing 을 읽는 것(p-5, w-64), 정의하지 않은 움직임(animate-pulse), 임의값(p-[13px],
// bg-[var(--nope)])과 우리 디자인 토큰(bg-bg, text-text, p-4)을 섞는다.
const PLANTED =
  "text-base rounded font-bold shadow text-red-500 bg-gray-500 p-5 w-64 animate-pulse p-[13px] bg-[var(--nope)] bg-bg text-text p-4";

export const PlantedClasses: Story = {
  name: "심은 클래스를 규칙 없는 클래스의 판정과 임의값의 판정이 잡는다",
  render: () => <div className={PLANTED}>심은 클래스</div>,
  play: async ({ canvasElement }) => {
    await expect(
      classesWithoutRules(canvasElement, sheetsDefining("--gray-50", document.styleSheets)),
    ).toEqual([
      "animate-pulse",
      "bg-gray-500",
      "font-bold",
      "p-5",
      "rounded",
      "shadow",
      "text-base",
      "text-red-500",
      "w-64",
    ]);
    await expect(arbitraryClasses(canvasElement)).toEqual(["bg-[var(--nope)]", "p-[13px]"]);
    await expect(() => {
      judgeClasses(canvasElement);
    }).toThrow("규칙 없는 클래스 text-base");
  },
};

export const KnownContrast: Story = {
  name: "검정과 흰색의 명암비는 21 이고 같은 색끼리는 1 이다",
  render: () => <p>명암비</p>,
  play: async () => {
    await expect(contrastRatio("#000000", "#ffffff")).toBe(21);
    await expect(contrastRatio("#FFFFFF", "#000000")).toBe(21);
    await expect(contrastRatio("#285cc2", "#285cc2")).toBe(1);
  },
};

// 겹친 바탕의 짝은 1.476 이라 메시지가 두 자리로 내려 적는 것(1.47)을 반올림(1.48)과 가른다.
export const FailingPair: Story = {
  name: "기준 미달 짝의 메시지가 테마·모드·짝과 내려 적은 값을 들고 겹친 바탕은 위에서 아래로 적는다",
  render: () => <p>기준 미달 짝</p>,
  play: async () => {
    const values: Readonly<Record<string, string>> = {
      text: "#777777",
      bg: "#888888",
      "bg-selected": "#ffffff1a",
    };
    const pairs: readonly ContrastPair[] = [
      ["text", "bg", 4.5],
      ["text", ["bg-selected", "bg"], 4.5],
    ];
    await expect(
      contrastFailures("nokcheong", "dark", (name) => values[name] ?? "", pairs),
    ).toEqual([
      "nokcheong/dark text/bg 1.26 < 4.5",
      "nokcheong/dark text/bg-selected+bg 1.47 < 4.5",
    ]);
  },
};

// 녹청 다크의 카드 안 위험 버튼 누름(design-refresh 명세의 "반투명 바탕의 명암비"). 반투명 `bg-selected` 를 `bg-raised` 에
// 겹친 색은 채널마다 반올림해 #2f3133 이고 `danger` 와 4.507 이다. 반올림 없이 재면 4.494 로 기준 아래라, 반올림이 판정의
// 일부라는 것을 이 사례가 잡는다. 내림(#2e3133)은 4.520 으로 지나므로 겹친 색도 본다. 값은 디자인 토큰 JSON 의 것이다.
export const LayeredSurface: Story = {
  name: "반투명 바탕은 아래 바탕에 겹쳐 채널마다 반올림한 색으로 잰다",
  render: () => <p>겹친 바탕</p>,
  play: async () => {
    const values: Readonly<Record<string, string>> = {
      danger: "#fa695e",
      "bg-raised": "#171a1c",
      "bg-selected": "#ffffff1a",
    };
    await expect(composite("#ffffff1a", "#171a1c")).toBe("#2f3133");
    await expect(composite("#FA695E", "#171a1c")).toBe("#fa695e");
    await expect(contrastRatio("#fa695e", "#2f3133").toFixed(3)).toBe("4.507");
    await expect(
      contrastFailures("nokcheong", "dark", (name) => values[name] ?? "", [
        ["danger", ["bg-selected", "bg-raised"], 4.5],
      ]),
    ).toEqual([]);
  },
};

// 스토리 도우미 `semanticColor` 는 대상과 같은 부모 안의 탐침으로 잰다. 쓰임새 토큰은 테마나 모드를 다는 요소마다 다시
// 선언되어, 문서 뿌리에 붙인 탐침은 뿌리의 값을 읽는다. 그러면 뿌리와 다른 테마·모드 안의 대상을 재는 스토리는 두
// 범위에서 같은 값으로 풀리는 토큰에서만 맞고 나머지에서는 엉뚱한 값과 견준다(design-refresh 티켓 03 의 계산값 단언).
export const HelperScope: Story = {
  name: "스토리 도우미는 대상이 놓인 테마·모드에서 풀린 쓰임새 토큰으로 재고 반투명도 받는다",
  render: () => (
    <div data-theme="guncheong" data-mode="dark" className="flex gap-2">
      <span data-sample="primary" className="bg-primary text-on-primary">
        주
      </span>
      <span data-sample="selected" className="bg-bg-selected text-text">
        고름
      </span>
    </div>
  ),
  play: async ({ canvasElement }) => {
    const sample = (name: string): Element => {
      const found = canvasElement.querySelector(`[data-sample=${name}]`);
      if (found === null) {
        throw new Error(`표본이 없다: ${name}`);
      }
      return found;
    };
    const primary = sample("primary");
    const selected = sample("selected");
    await expect(colorsOf(primary).background).toBe(semanticColor(primary, "primary"));
    await expect(semanticColor(primary, "primary")).not.toBe(
      semanticColor(canvasElement, "primary"),
    );
    await expect(colorsOf(selected).background).toBe(semanticColor(selected, "bg-selected"));
    await expect(semanticColor(selected, "bg-selected")).toMatch(/^rgba\(/);
  },
};
