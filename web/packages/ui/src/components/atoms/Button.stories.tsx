import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import {
  TRANSPARENT,
  colorsOf,
  expectedFocusRing,
  focusRingOf,
  semanticColor,
} from "../../storybook/expect";
import { Button } from "./Button";
import { Card } from "./Card";

const meta = {
  title: "atoms/Button",
  component: Button,
  args: { children: "승인", onClick: fn() },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

// 주 버튼의 바탕(`primary`)은 녹청에서 `text` 와, 군청에서 `accent` 와 같은 값이다. 녹청(이 스토리)과 군청
// (PrimaryGuncheong)에서 하나씩 잰다. 글자(`on-primary`)는 녹청 라이트에서 `bg` 와, 녹청 다크(PrimaryDark)에서 `on-accent`
// 와 가른다(design-refresh 명세의 "계산값으로 가를 수 없는 짝").
export const Primary: Story = {
  name: "주 버튼은 이름으로 찾히고 기본 type 이 button 이며 primary 바탕에 on-primary 글자이고 누르면 onClick 이 한 번 불린다",
  args: { variant: "primary" },
  play: async ({ args, canvas, userEvent }) => {
    const button = canvas.getByRole("button", { name: "승인" });
    await expect(button.getAttribute("type")).toBe("button");
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "primary"),
      text: semanticColor(button, "on-primary"),
    });
    await userEvent.click(button);
    await expect(args.onClick).toHaveBeenCalledOnce();
  },
};

export const Secondary: Story = {
  name: "보조 버튼은 바탕 없이 border 테두리에 text 글자다",
  args: { variant: "secondary", children: "거부" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "거부" });
    await expect(colorsOf(button)).toEqual({
      background: TRANSPARENT,
      text: semanticColor(button, "text"),
      border: semanticColor(button, "border"),
    });
  },
};

export const Danger: Story = {
  name: "위험 버튼은 바탕 없이 border 테두리에 danger 글자다",
  args: { variant: "danger", children: "실행 지우기" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "실행 지우기" });
    await expect(colorsOf(button)).toEqual({
      background: TRANSPARENT,
      text: semanticColor(button, "danger"),
      border: semanticColor(button, "border"),
    });
  },
};

// 위험 버튼의 누름(`bg-selected`)이 기준과 가장 가까운 자리다(녹청 다크의 카드 안 4.507, design-refresh 명세의 "위험 버튼의
// 누름"). 스토리 테스트의 userEvent 는 `:active` 를 걸지 못해, 사진 비교가 실제 마우스로 누르고 그 바탕과 칠한 픽셀을 잰다.
export const DangerInCardDark: Story = {
  name: "다크 모드의 카드 안 위험 버튼도 바탕 없이 카드의 bg-raised 가 비치고 danger 글자다",
  args: { variant: "danger", children: "실행 지우기" },
  globals: { mode: "dark" },
  render: (args) => (
    <Card>
      <p className="text-body text-text">실행 2024-1187</p>
      <div className="flex">
        <Button {...args} />
      </div>
    </Card>
  ),
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "실행 지우기" });
    const card = button.closest("div")?.parentElement;
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    await expect(colorsOf(button)).toEqual({
      background: TRANSPARENT,
      text: semanticColor(button, "danger"),
      border: semanticColor(button, "border"),
    });
    await expect(card === null || card === undefined ? null : colorsOf(card).background).toBe(
      semanticColor(button, "bg-raised"),
    );
  },
};

/**
 * 버튼의 치수. 높이와 글자 크기는 밀도를 따르고, 안쪽 좌우 12px, 모서리 8px, 굵기 500, 아이콘 16px, 아이콘과 글자 사이
 * 8px 은 밀도와 상관없다.
 */
async function expectButtonSize(button: HTMLElement, height: string, fontSize: string) {
  const style = getComputedStyle(button);
  const svg = button.querySelector("svg");
  const content = svg?.parentElement ?? null;
  await expect({
    height: style.height,
    padding: `${style.paddingLeft} ${style.paddingRight}`,
    radius: style.borderTopLeftRadius,
    font: `${style.fontSize} ${style.fontWeight}`,
    icon: svg === null ? null : getComputedStyle(svg).width,
    gap: content === null ? null : getComputedStyle(content).columnGap,
  }).toEqual({
    height,
    padding: "12px 12px",
    radius: "8px",
    font: `${fontSize} 500`,
    icon: "16px",
    gap: "8px",
  });
}

export const Compact: Story = {
  name: "촘촘 밀도의 버튼은 높이 32px 에 14px·500 글자이고 안쪽 좌우 12px, 모서리 8px, 16px 아이콘과 글자 사이가 8px 이다",
  args: { icon: "check" },
  globals: { density: "compact" },
  play: async ({ canvas }) => {
    await expectButtonSize(canvas.getByRole("button", { name: "승인" }), "32px", "14px");
  },
};

export const Regular: Story = {
  name: "보통 밀도의 버튼은 높이 40px 에 15px·500 글자이고 나머지 치수는 촘촘과 같다",
  args: { icon: "check" },
  globals: { density: "regular" },
  play: async ({ canvas }) => {
    await expectButtonSize(canvas.getByRole("button", { name: "승인" }), "40px", "15px");
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
    await expect(
      spinner === null
        ? null
        : {
            animation: getComputedStyle(spinner).animationName,
            width: getComputedStyle(spinner).width,
          },
    ).toEqual({ animation: "spin", width: "16px" });
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
  name: "쓸 수 없는 버튼은 눌러도 onClick 이 불리지 않고 bg-disabled 바탕과 테두리, text-disabled 글자다",
  render: (args) => (
    <div className="flex gap-2">
      <Button {...args} variant="primary" disabled />
      <Button {...args} variant="secondary" disabled />
      <Button {...args} variant="danger" disabled />
    </div>
  ),
  play: async ({ args, canvas, userEvent }) => {
    const buttons = canvas.getAllByRole("button", { name: "승인" });
    await expect(buttons.length).toBe(3);
    for (const button of buttons) {
      await expect(colorsOf(button)).toEqual({
        background: semanticColor(button, "bg-disabled"),
        text: semanticColor(button, "text-disabled"),
        border: semanticColor(button, "bg-disabled"),
      });
      await userEvent.click(button);
    }
    await expect(args.onClick).not.toHaveBeenCalled();
  },
};

// `text-disabled` 는 라이트에서 `border-control` 과 같은 값이라 다크에서도 잰다. `bg-disabled` 와 `border` 는 다크에서 같아
// 라이트(Disabled)가 가른다.
export const DisabledDark: Story = {
  ...Disabled,
  name: "다크 모드의 쓸 수 없는 버튼도 bg-disabled 바탕과 테두리, text-disabled 글자다",
  globals: { mode: "dark" },
};

export const PrimaryDark: Story = {
  name: "다크 모드의 주 버튼도 primary 바탕에 on-primary 글자다",
  args: { variant: "primary" },
  globals: { mode: "dark" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "승인" });
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "primary"),
      text: semanticColor(button, "on-primary"),
    });
  },
};

// 군청은 주 버튼을 강조색으로 칠하는 갈래라 `primary` 가 `text` 와 다르다. 기본 테마가 아닌 테마에서 값을 재는 판정
// 스토리라 사진에서 뺀다(사진은 기본 테마만 찍는다, ADR 0026 의 2026-10-06 이력).
export const PrimaryGuncheong: Story = {
  name: "군청의 주 버튼도 primary 바탕에 on-primary 글자다",
  tags: ["judgment"],
  args: { variant: "primary" },
  globals: { theme: "guncheong" },
  play: async ({ canvas }) => {
    const button = canvas.getByRole("button", { name: "승인" });
    await expect(colorsOf(button)).toMatchObject({
      background: semanticColor(button, "primary"),
      text: semanticColor(button, "on-primary"),
    });
  },
};

// 녹청에서 `focus-ring` 은 `accent` 와 같은 값이라 그 둘은 가르지 못하지만 `primary`(= `text`)·`border` 와는 가른다.
export const Focus: Story = {
  name: "Tab 으로 포커스하면 focus-ring 색의 2px 실선이 2px 바깥에 그려진다",
  args: { variant: "danger" },
  play: async ({ canvas, userEvent }) => {
    const button = canvas.getByRole("button", { name: "승인" });
    await userEvent.tab();
    await expect(document.activeElement).toBe(button);
    await expect(focusRingOf(button)).toEqual(expectedFocusRing(button));
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
      <Button {...args} variant="danger">
        실행 지우기
      </Button>
    </div>
  ),
  play: async ({ canvasElement }) => {
    const row = canvasElement.querySelector("[data-sample=row]");
    await expect(row instanceof HTMLElement && row.scrollWidth <= row.clientWidth).toBe(true);
  },
};

/** 보여 주기용(`showcase`). 승인 묻기의 버튼 쌍이다. "거부"(보조)가 먼저, "승인"(주)이 나중이다. */
export const ShowcaseApprovalPair: Story = {
  name: "쓰임: 승인 묻기의 버튼 쌍",
  tags: ["showcase"],
  render: () => (
    <div className="flex flex-col gap-3">
      <p className="text-body text-text">
        <span className="font-mono text-mono font-medium">payments.refund</span>를 실행할까요
      </p>
      <div className="flex gap-2">
        <Button variant="secondary">거부</Button>
        <Button>승인</Button>
      </div>
    </div>
  ),
};

/** 보여 주기용(`showcase`). 관리 화면의 다른 동작이다. 읽는 화면의 새로 고침은 불러오는 중이고, 설정의 토큰 지우기는 위험 버튼이다. */
export const ShowcaseAdminActions: Story = {
  name: "쓰임: 새로 고침과 토큰 지우기",
  tags: ["showcase"],
  render: () => (
    <div className="flex gap-2">
      <Button variant="secondary" loading>
        새로 고침
      </Button>
      <Button variant="danger">토큰 지우기</Button>
    </div>
  ),
};
