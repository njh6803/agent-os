import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import { TRANSPARENT, colorsOf, semanticColor } from "../../storybook/expect";
import { IconButton } from "./IconButton";

const meta = {
  title: "atoms/IconButton",
  component: IconButton,
  args: { icon: "send", label: "보내기", onClick: fn() },
} satisfies Meta<typeof IconButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Ghost: Story = {
  name: "투명 아이콘 버튼은 label 이 이름과 title 이고 바탕 없이 muted 로 그린 40px 정사각형이다",
  play: async ({ args, canvas, userEvent }) => {
    const button = canvas.getByRole("button", { name: "보내기" });
    const style = getComputedStyle(button);
    await expect({
      title: button.getAttribute("title"),
      type: button.getAttribute("type"),
      width: style.width,
      height: style.height,
    }).toEqual({ title: "보내기", type: "button", width: "40px", height: "40px" });
    await expect(colorsOf(button)).toMatchObject({
      background: TRANSPARENT,
      text: semanticColor(button, "muted"),
    });
    await expect(button.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
    await userEvent.click(button);
    await expect(args.onClick).toHaveBeenCalledOnce();
  },
};

export const Primary: Story = {
  name: "주 아이콘 버튼은 accent 바탕에 on-accent 아이콘이다",
  args: { variant: "primary" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "보내기" });
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "accent"),
      text: semanticColor(button, "on-accent"),
    });
  },
};

export const Secondary: Story = {
  name: "보조 아이콘 버튼은 tint 바탕에 text 아이콘이다",
  args: { variant: "secondary", icon: "ellipsis", label: "더 보기" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "더 보기" });
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "tint"),
      text: semanticColor(button, "text"),
    });
  },
};

export const Small: Story = {
  name: "작은 아이콘 버튼은 32px 정사각형이고 아이콘이 16px 이다",
  args: { size: "s", icon: "x", label: "닫기" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "닫기" });
    const svg = button.querySelector("svg");
    await expect({
      width: getComputedStyle(button).width,
      height: getComputedStyle(button).height,
      icon: svg === null ? null : getComputedStyle(svg).width,
    }).toEqual({ width: "32px", height: "32px", icon: "16px" });
  },
};

export const Loading: Story = {
  name: "불러오는 중에도 이름이 그대로이고 아이콘 자리에 도는 표시를 두며 누름을 무시한다",
  args: { variant: "primary", loading: true },
  play: async ({ args, canvas, userEvent }) => {
    const button = canvas.getByRole("button", { name: "보내기" });
    await expect({
      busy: button.getAttribute("aria-busy"),
      ariaDisabled: button.getAttribute("aria-disabled"),
      disabled: button.hasAttribute("disabled"),
      title: button.getAttribute("title"),
      width: getComputedStyle(button).width,
    }).toEqual({
      busy: "true",
      ariaDisabled: "true",
      disabled: false,
      title: "보내기",
      width: "40px",
    });
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "accent"),
      text: semanticColor(button, "on-accent"),
    });
    const spinner = button.querySelector("svg");
    await expect(spinner === null ? null : getComputedStyle(spinner).animationName).toBe("spin");
    await userEvent.click(button);
    await expect(args.onClick).not.toHaveBeenCalled();
    await expect(document.activeElement).toBe(button);
  },
};

export const Disabled: Story = {
  name: "쓸 수 없는 아이콘 버튼은 불리지 않고 주·보조는 disabled-surface 바탕, 투명은 바탕 없이 disabled-text 다",
  render: (args) => (
    <div className="flex gap-2">
      <IconButton {...args} variant="primary" disabled />
      <IconButton {...args} variant="secondary" disabled />
      <IconButton {...args} variant="ghost" disabled />
    </div>
  ),
  play: async ({ args, canvas, userEvent }) => {
    const [primary, secondary, ghost] = canvas.getAllByRole("button", { name: "보내기" });
    if (primary === undefined || secondary === undefined || ghost === undefined) {
      throw new Error("버튼 셋이 없다");
    }
    for (const button of [primary, secondary]) {
      await expect(colorsOf(button)).toMatchObject({
        background: semanticColor(button, "disabled-surface"),
        text: semanticColor(button, "disabled-text"),
      });
    }
    await expect(colorsOf(ghost)).toMatchObject({
      background: TRANSPARENT,
      text: semanticColor(ghost, "disabled-text"),
    });
    for (const button of [primary, secondary, ghost]) {
      await userEvent.click(button);
    }
    await expect(args.onClick).not.toHaveBeenCalled();
  },
};

export const GhostDark: Story = {
  name: "다크 모드의 투명 아이콘 버튼도 muted 로 그린다",
  globals: { mode: "dark" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "보내기" });
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    await expect(colorsOf(button).text).toBe(semanticColor(button, "muted"));
  },
};

// 공문에서 잰다. 먹은 focus 와 accent 가 같은 색이라 링이 accent 를 읽어도 지난다.
export const Focus: Story = {
  name: "Tab 으로 포커스하면 focus 색의 실선 테두리가 바깥에 그려진다",
  globals: { theme: "gongmun" },
  play: async ({ canvas, userEvent }) => {
    const button = canvas.getByRole("button", { name: "보내기" });
    await userEvent.tab();
    await expect(document.activeElement).toBe(button);
    const style = getComputedStyle(button);
    await expect({
      style: style.outlineStyle,
      width: style.outlineWidth,
      offset: style.outlineOffset,
      color: style.outlineColor,
    }).toEqual({
      style: "solid",
      width: "2px",
      offset: "2px",
      color: semanticColor(button, "focus"),
    });
  },
};
