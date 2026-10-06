import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import { Button } from "./Button";

const meta = {
  title: "atoms/Button",
  component: Button,
  args: { children: "승인", onClick: fn() },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = { args: { variant: "primary" } };

export const Secondary: Story = { args: { variant: "secondary", children: "거부" } };

export const Danger: Story = { args: { variant: "danger", children: "실행 지우기" } };

export const Small: Story = { args: { variant: "primary", size: "s" } };

export const PrimaryDark: Story = { args: { variant: "primary" }, globals: { mode: "dark" } };

export const Disabled: Story = { args: { variant: "primary", disabled: true } };

/** 상태 색을 스토리 테스트로 볼 수 있는지 잰다. storybook/test 의 userEvent 로 올리고 누르고 Tab 으로 포커스한 뒤의
 * 계산값을 기록한다(기대값은 이 프로브의 측정 결과다). userEvent 는 합성 이벤트라 :hover·:active 가 걸리지 않고 배경이
 * 그대로였다. Tab 은 :focus-visible 이 걸렸다. 실제 입력의 올림·누름은 measure.mjs 의 states 가 Playwright 로 잰다. */
export const States: Story = {
  args: { variant: "primary" },
  play: async ({ canvas, userEvent }) => {
    const button = canvas.getByRole("button", { name: "승인" });
    const root = getComputedStyle(document.documentElement);
    const token = (name: string): string => root.getPropertyValue(`--${name}`).trim();
    const background = (): string => getComputedStyle(button).backgroundColor;
    const seen: string[] = [`default ${background()}`];
    await userEvent.hover(button);
    seen.push(`hover ${background()} matches:${String(button.matches(":hover"))}`);
    await userEvent.unhover(button);
    await userEvent.pointer({ keys: "[MouseLeft>]", target: button });
    seen.push(`press ${background()} matches:${String(button.matches(":active"))}`);
    await userEvent.pointer({ keys: "[/MouseLeft]", target: button });
    button.blur();
    await userEvent.tab();
    seen.push(
      `tab focus:${String(document.activeElement === button)} visible:${String(button.matches(":focus-visible"))} outline:${getComputedStyle(button).outlineStyle}`,
    );
    await expect({
      seen,
      accentHover: token("accent-hover"),
      accentPress: token("accent-press"),
    }).toEqual({
      seen: [
        "default rgb(40, 92, 194)",
        "hover rgb(40, 92, 194) matches:false",
        "press rgb(40, 92, 194) matches:false",
        "tab focus:true visible:true outline:solid",
      ],
      accentHover: "#1745a0",
      accentPress: "#092e78",
    });
  },
};

export const Click: Story = {
  args: { variant: "primary" },
  play: async ({ args, canvas, userEvent }) => {
    await userEvent.click(canvas.getByRole("button", { name: "승인" }));
    await expect(args.onClick).toHaveBeenCalledOnce();
  },
};
