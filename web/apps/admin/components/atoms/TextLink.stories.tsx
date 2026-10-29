// 글자 링크(admin-style 티켓 04, 명세 "앱 부품"). Storybook 에서 `next/link` 는 평범한 `<a>` 를 그리는 대역이다
// (.storybook/main.ts). 포커스 링은 play 가 키보드로 포커스를 옮겨 계산값으로 본다.
import { expectedFocusRing, focusRingOf, hoverAwareColor } from "@agent-os/ui/storybook/expect";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, within } from "storybook/test";
import { TextLink } from "./TextLink";

const meta = {
  title: "atoms/TextLink",
  component: TextLink,
  args: { href: "/runs", children: "실행 목록" },
} satisfies Meta<typeof TextLink>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 강조색 글자이고 포인터 목표가 24px 이상이다. */
export const Default: Story = {
  play: async ({ canvasElement, userEvent }) => {
    const link = within(canvasElement).getByRole("link", { name: "실행 목록" });
    await expect(link).toHaveAttribute("href", "/runs");
    await expect(link.getBoundingClientRect().height).toBeGreaterThanOrEqual(24);
    await expect(getComputedStyle(link).color).toBe(hoverAwareColor(link, "accent", "text"));

    // 사진은 이 앞의 그림이다(`.claude/rules/web-design.md`).
    await userEvent.tab();
    await expect(link).toHaveFocus();
    await expect(focusRingOf(link)).toEqual(expectedFocusRing(link));
  },
};
