import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import {
  TRANSPARENT,
  colorsOf,
  expectedFocusRing,
  focusRingOf,
  semanticColor,
} from "../../storybook/expect";
import { IconButton } from "./IconButton";

const meta = {
  title: "atoms/IconButton",
  component: IconButton,
  args: { icon: "send", label: "보내기", onClick: fn() },
} satisfies Meta<typeof IconButton>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Ghost: Story = {
  name: "투명 아이콘 버튼은 label 이 이름과 title 이고 바탕 없이 text-muted 로 그린 40px 정사각형이다",
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
      text: semanticColor(button, "text-muted"),
    });
    await expect(button.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
    await userEvent.click(button);
    await expect(args.onClick).toHaveBeenCalledOnce();
  },
};

// 주 아이콘 버튼은 주 버튼과 같은 갈래다. 녹청(이 스토리)과 군청(PrimaryGuncheong)에서 바탕을, 녹청 다크(GhostDark)에서
// 글자를 `on-accent` 와 가른다(design-refresh 명세의 "계산값으로 가를 수 없는 짝").
export const Primary: Story = {
  name: "주 아이콘 버튼은 primary 바탕에 on-primary 아이콘이다",
  args: { variant: "primary" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "보내기" });
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "primary"),
      text: semanticColor(button, "on-primary"),
    });
  },
};

export const Secondary: Story = {
  name: "보조 아이콘 버튼은 바탕 없이 border 테두리에 text 아이콘이다",
  args: { variant: "secondary", icon: "ellipsis", label: "더 보기" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "더 보기" });
    await expect(colorsOf(button)).toEqual({
      background: TRANSPARENT,
      text: semanticColor(button, "text"),
      border: semanticColor(button, "border"),
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
      background: semanticColor(button, "primary"),
      text: semanticColor(button, "on-primary"),
    });
    const spinner = button.querySelector("svg");
    await expect(spinner === null ? null : getComputedStyle(spinner).animationName).toBe("spin");
    await userEvent.click(button);
    await expect(args.onClick).not.toHaveBeenCalled();
    await expect(document.activeElement).toBe(button);
  },
};

export const Disabled: Story = {
  name: "쓸 수 없는 아이콘 버튼은 불리지 않고 주·보조는 bg-disabled 바탕과 테두리, 투명은 바탕 없이 text-disabled 다",
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
      await expect(colorsOf(button)).toEqual({
        background: semanticColor(button, "bg-disabled"),
        text: semanticColor(button, "text-disabled"),
        border: semanticColor(button, "bg-disabled"),
      });
    }
    await expect(colorsOf(ghost)).toMatchObject({
      background: TRANSPARENT,
      text: semanticColor(ghost, "text-disabled"),
    });
    for (const button of [primary, secondary, ghost]) {
      await userEvent.click(button);
    }
    await expect(args.onClick).not.toHaveBeenCalled();
  },
};

// `text-disabled` 는 라이트에서 `border-control` 과 같은 값이라 다크에서도 잰다.
export const DisabledDark: Story = {
  ...Disabled,
  name: "다크 모드의 쓸 수 없는 아이콘 버튼도 주·보조는 bg-disabled 바탕과 테두리, 투명은 text-disabled 다",
  globals: { mode: "dark" },
};

export const GhostDark: Story = {
  name: "다크 모드의 투명 아이콘 버튼은 text-muted 로, 주 아이콘 버튼은 primary 바탕에 on-primary 로 그린다",
  globals: { mode: "dark" },
  render: (args) => (
    <div className="flex gap-2">
      <IconButton {...args} />
      <IconButton {...args} variant="primary" label="보내기 확인" />
    </div>
  ),
  play: async ({ canvas }) => {
    const ghost = canvas.getByRole("button", { name: "보내기" });
    const primary = canvas.getByRole("button", { name: "보내기 확인" });
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    await expect(colorsOf(ghost).text).toBe(semanticColor(ghost, "text-muted"));
    await expect(colorsOf(primary)).toMatchObject({
      background: semanticColor(primary, "primary"),
      text: semanticColor(primary, "on-primary"),
    });
  },
};

// 군청은 주 버튼을 강조색으로 칠하는 갈래라 `primary` 가 `text` 와 다르다. 기본 테마가 아닌 테마에서 값을 재는 판정
// 스토리라 사진에서 뺀다(사진은 기본 테마만 찍는다, ADR 0026 의 2026-10-06 이력).
export const PrimaryGuncheong: Story = {
  name: "군청의 주 아이콘 버튼도 primary 바탕에 on-primary 아이콘이다",
  tags: ["judgment"],
  args: { variant: "primary" },
  globals: { theme: "guncheong" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "보내기" });
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "primary"),
      text: semanticColor(button, "on-primary"),
    });
  },
};

// 녹청에서 `focus-ring` 은 `accent` 와 같은 값이라 그 둘은 가르지 못하지만 `primary`·`border` 와는 가른다.
export const Focus: Story = {
  name: "Tab 으로 포커스하면 focus-ring 색의 2px 실선이 2px 바깥에 그려진다",
  play: async ({ canvas, userEvent }) => {
    const button = canvas.getByRole("button", { name: "보내기" });
    await userEvent.tab();
    await expect(document.activeElement).toBe(button);
    await expect(focusRingOf(button)).toEqual(expectedFocusRing(button));
  },
};
