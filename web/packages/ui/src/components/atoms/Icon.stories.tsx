import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { SCREEN_STROKE, strokesOf } from "../../storybook/expect";
import { ICON_NAMES, ICON_SIZES, Icon } from "./Icon";

const meta = {
  title: "atoms/Icon",
  component: Icon,
  args: { name: "send" },
} satisfies Meta<typeof Icon>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Decorative: Story = {
  name: "label 이 없으면 화면 읽기 프로그램에서 숨고 놓인 곳의 글자 색과 둥근 선으로 그린다",
  play: async ({ canvasElement }) => {
    const svg = canvasElement.querySelector("svg");
    await expect({
      hidden: svg?.getAttribute("aria-hidden"),
      role: svg?.getAttribute("role"),
      stroke: svg?.getAttribute("stroke"),
      cap: svg?.getAttribute("stroke-linecap"),
      join: svg?.getAttribute("stroke-linejoin"),
    }).toEqual({ hidden: "true", role: null, stroke: "currentColor", cap: "round", join: "round" });
  },
};

export const Labelled: Story = {
  name: "label 이 있으면 그 이름의 그림이다",
  args: { name: "triangle-alert", label: "경고" },
  play: async ({ canvas }) => {
    const image = canvas.getByRole("img", { name: "경고" });
    await expect(image.hasAttribute("aria-hidden")).toBe(false);
  },
};

export const Sizes: Story = {
  name: "크기 셋의 폭이 14·16·20px 이고 그린 요소마다 선이 크기와 상관없이 화면의 1.5px 이다",
  render: (args) => (
    <div className="flex items-center gap-4 text-text">
      {ICON_SIZES.map((size) => (
        <Icon key={size} {...args} size={size} />
      ))}
    </div>
  ),
  play: async ({ canvasElement }) => {
    const svgs = Array.from(canvasElement.querySelectorAll("svg"));
    await expect(svgs.map((svg) => getComputedStyle(svg).width)).toEqual(["14px", "16px", "20px"]);
    for (const svg of svgs) {
      const strokes = strokesOf(svg);
      await expect(strokes).toEqual(strokes.map(() => SCREEN_STROKE));
    }
  },
};

export const AllNames: Story = {
  name: "열여섯 이름이 모두 화면 1.5px 의 선으로 그려진다",
  render: (args) => (
    <ul className="flex flex-wrap gap-4 text-text">
      {ICON_NAMES.map((name) => (
        <li key={name} className="flex flex-col items-center gap-1 text-small">
          <Icon {...args} name={name} />
          {name}
        </li>
      ))}
    </ul>
  ),
  play: async ({ canvasElement }) => {
    const svgs = Array.from(canvasElement.querySelectorAll("svg"));
    await expect(svgs).toHaveLength(ICON_NAMES.length);
    for (const svg of svgs) {
      // strokesOf 는 그린 요소가 없으면 던진다.
      const strokes = strokesOf(svg);
      await expect(strokes).toEqual(strokes.map(() => SCREEN_STROKE));
    }
  },
};

export const AllNamesDark: Story = {
  ...AllNames,
  name: "다크 모드에서도 열여섯 이름이 화면 1.5px 의 선으로 그려진다",
  globals: { mode: "dark" },
};

/** 보여 주기용(`showcase`). 관리 화면 탐색 항목 앞의 아이콘이다. 글자와 함께 놓여 꾸밈이므로 숨는다. */
export const ShowcaseNavItems: Story = {
  name: "쓰임: 탐색 항목 앞의 아이콘",
  tags: ["showcase"],
  render: () => (
    <ul className="flex flex-col gap-2 text-body text-text">
      <li className="flex items-center gap-2">
        <Icon name="plug" size="16" />
        플러그인
      </li>
      <li className="flex items-center gap-2">
        <Icon name="list" size="16" />
        실행
      </li>
    </ul>
  ),
};
