import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import { TRANSPARENT, colorsOf, semanticColor } from "../../storybook/expect";
import { Button } from "./Button";

const meta = {
  title: "atoms/Button",
  component: Button,
  args: { children: "승인", onClick: fn() },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  name: "주 버튼은 이름으로 찾히고 기본 type 이 button 이며 누르면 onClick 이 한 번 불린다",
  args: { variant: "primary" },
  play: async ({ args, canvas, userEvent }) => {
    const button = canvas.getByRole("button", { name: "승인" });
    await expect(button.getAttribute("type")).toBe("button");
    await expect(getComputedStyle(button).height).toBe("40px");
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "accent"),
      text: semanticColor(button, "on-accent"),
    });
    await userEvent.click(button);
    await expect(args.onClick).toHaveBeenCalledOnce();
  },
};

export const Secondary: Story = {
  name: "보조 버튼은 tint 바탕에 text 글자다",
  args: { variant: "secondary", children: "거부" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "거부" });
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "tint"),
      text: semanticColor(button, "text"),
    });
  },
};

export const Danger: Story = {
  name: "위험 버튼은 raised 바탕에 danger 글자와 테두리다",
  args: { variant: "danger", children: "실행 지우기" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "실행 지우기" });
    await expect(colorsOf(button)).toEqual({
      background: semanticColor(button, "raised"),
      text: semanticColor(button, "danger"),
      border: semanticColor(button, "danger"),
    });
  },
};

export const Small: Story = {
  name: "작은 버튼의 높이는 32px 이다",
  args: { size: "s" },
  play: async ({ canvas }) => {
    await expect(getComputedStyle(canvas.getByRole("button", { name: "승인" })).height).toBe(
      "32px",
    );
  },
};

export const WithIcon: Story = {
  name: "아이콘은 글자 앞에 있고 이름에 들지 않는다",
  args: { icon: "check" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "승인" });
    const svg = button.querySelector("svg");
    await expect(svg?.getAttribute("aria-hidden")).toBe("true");
    // 아이콘과 글자가 같은 자리에 있고 아이콘이 첫째다.
    await expect(svg?.parentElement?.firstChild).toBe(svg);
    await expect(svg?.parentElement?.textContent).toBe("승인");
  },
};

export const SmallWithIcon: Story = {
  name: "작은 버튼의 아이콘은 16px 이다",
  args: { size: "s", icon: "send", children: "보내기" },
  play: async ({ canvas }) => {
    const svg = canvas.getByRole("button", { name: "보내기" }).querySelector("svg");
    await expect(svg === null ? null : getComputedStyle(svg).width).toBe("16px");
  },
};

export const Loading: Story = {
  name: "불러오는 중은 aria-busy 이고 누름을 무시하며 색·포커스·너비가 그대로다",
  render: (args) => (
    <div className="flex flex-col items-start gap-2">
      <Button {...args} />
      <Button {...args} loading />
    </div>
  ),
  play: async ({ args, canvas, userEvent }) => {
    const [idle, busy] = canvas.getAllByRole("button", { name: "승인" });
    if (idle === undefined || busy === undefined) {
      throw new Error("버튼 둘이 없다");
    }
    await expect({
      busy: busy.getAttribute("aria-busy"),
      ariaDisabled: busy.getAttribute("aria-disabled"),
      disabled: busy.hasAttribute("disabled"),
    }).toEqual({ busy: "true", ariaDisabled: "true", disabled: false });
    await expect(colorsOf(busy)).toEqual(colorsOf(idle));
    await expect(busy.getBoundingClientRect().width).toBe(idle.getBoundingClientRect().width);
    const spinner = busy.querySelector("svg");
    await expect(spinner === null ? null : getComputedStyle(spinner).animationName).toBe("spin");
    await userEvent.click(busy);
    await expect(args.onClick).not.toHaveBeenCalled();
    busy.focus();
    await userEvent.keyboard("{Enter}");
    await expect(args.onClick).not.toHaveBeenCalled();
    await expect(document.activeElement).toBe(busy);
  },
};

export const LoadingSubmit: Story = {
  name: "불러오는 중인 제출 버튼은 폼을 보내지 않는다",
  args: { type: "submit", loading: true, children: "보내기" },
  render: (args) => (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        args.onClick?.();
      }}
    >
      <Button {...args} />
    </form>
  ),
  play: async ({ args, canvas, userEvent }) => {
    await userEvent.click(canvas.getByRole("button", { name: "보내기" }));
    await expect(args.onClick).not.toHaveBeenCalled();
  },
};

export const Disabled: Story = {
  name: "쓸 수 없는 버튼은 눌러도 onClick 이 불리지 않고 disabled-surface·disabled-text 로 칠한다",
  render: (args) => (
    <div className="flex gap-2">
      <Button {...args} variant="primary" disabled />
      <Button {...args} variant="secondary" disabled />
      <Button {...args} variant="danger" disabled />
    </div>
  ),
  play: async ({ args, canvas, userEvent }) => {
    const buttons = canvas.getAllByRole("button", { name: "승인" });
    for (const button of buttons) {
      await expect(colorsOf(button)).toEqual({
        background: semanticColor(button, "disabled-surface"),
        text: semanticColor(button, "disabled-text"),
        border: TRANSPARENT,
      });
      await userEvent.click(button);
    }
    await expect(args.onClick).not.toHaveBeenCalled();
  },
};

export const PrimaryDark: Story = {
  name: "다크 모드의 주 버튼도 accent 바탕에 on-accent 글자다",
  args: { variant: "primary" },
  globals: { mode: "dark" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "승인" });
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "accent"),
      text: semanticColor(button, "on-accent"),
    });
  },
};

// 공문에서 잰다. 먹은 focus 와 accent 가 같은 색이라 링이 accent 를 읽어도 지난다.
export const Focus: Story = {
  name: "Tab 으로 포커스하면 focus 색의 실선 테두리가 바깥에 그려진다",
  args: { variant: "danger" },
  globals: { theme: "gongmun" },
  play: async ({ canvas, userEvent }) => {
    const button = canvas.getByRole("button", { name: "승인" });
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

export const NarrowRow: Story = {
  name: "버튼 셋을 한 줄로 폭 320px 자리에 그려도 가로로 넘치지 않는다",
  render: (args) => (
    <div data-sample="row" className="flex gap-2" style={{ width: 320 }}>
      <Button {...args} variant="secondary">
        거부
      </Button>
      <Button {...args} icon="check" />
      <Button {...args} variant="danger" size="s">
        실행 지우기
      </Button>
    </div>
  ),
  play: async ({ canvasElement }) => {
    const row = canvasElement.querySelector("[data-sample=row]");
    await expect(row instanceof HTMLElement && row.scrollWidth <= row.clientWidth).toBe(true);
  },
};
