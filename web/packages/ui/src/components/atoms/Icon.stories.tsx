import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
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
  name: "크기 넷의 폭이 14·16·20·24px 이고 작은 둘의 선이 더 굵다",
  render: (args) => (
    <div className="flex items-center gap-4 text-text">
      {ICON_SIZES.map((size) => (
        <Icon key={size} {...args} size={size} />
      ))}
    </div>
  ),
  play: async ({ canvasElement }) => {
    const svgs = Array.from(canvasElement.querySelectorAll("svg"));
    await expect(svgs.map((svg) => getComputedStyle(svg).width)).toEqual([
      "14px",
      "16px",
      "20px",
      "24px",
    ]);
    await expect(svgs.map((svg) => svg.getAttribute("stroke-width"))).toEqual([
      "2",
      "2",
      "1.75",
      "1.75",
    ]);
  },
};

export const AllNames: Story = {
  name: "열여섯 이름이 모두 선이 있는 그림으로 그려진다",
  render: (args) => (
    <ul className="flex flex-wrap gap-4 text-text">
      {ICON_NAMES.map((name) => (
        <li key={name} className="flex flex-col items-center gap-1 text-caption">
          <Icon {...args} name={name} size="24" />
          {name}
        </li>
      ))}
    </ul>
  ),
  play: async ({ canvasElement }) => {
    const drawn = Array.from(
      canvasElement.querySelectorAll("svg"),
      (svg) => svg.querySelectorAll("path, circle, line, rect, polyline, polygon").length > 0,
    );
    await expect(drawn).toEqual(ICON_NAMES.map(() => true));
  },
};

export const AllNamesDark: Story = {
  ...AllNames,
  name: "다크 모드에서도 열여섯 이름이 그려진다",
  globals: { mode: "dark" },
};
