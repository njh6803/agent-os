// 판정 함수의 음성 사례. 판정이 늘 지나도 초록이 되지 않게, 심은 클래스와 기준 미달 짝을 판정이 실제로 잡는지 본다
// (design-system 명세 스토리 29~33). 심은 것을 그리므로 afterEach 의 클래스 판정(planted 태그)과 axe 에서 빠진다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { judgeClasses } from "../storybook/preview";
import { contrastFailures, type ContrastPair } from "../styles/contrast";
import { arbitraryClasses, classesWithoutRules, contrastRatio, sheetsDefining } from ".";

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

export const FailingPair: Story = {
  name: "기준 미달 짝의 메시지가 테마·모드·짝을 든다",
  render: () => <p>기준 미달 짝</p>,
  play: async () => {
    const values: Readonly<Record<string, string>> = { text: "#777777", bg: "#888888" };
    const pairs: readonly ContrastPair[] = [["text", "bg", 4.5]];
    await expect(
      contrastFailures("cheongnok", "dark", (name) => values[name] ?? "", pairs),
    ).toEqual(["cheongnok/dark text/bg 1.26 < 4.5"]);
  },
};
