import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { colorsOf, semanticColor } from "../../storybook/expect";
import { STATUS_BADGE_STATUSES, StatusBadge, type StatusBadgeStatus } from "./StatusBadge";

const meta = {
  title: "atoms/StatusBadge",
  component: StatusBadge,
  args: { status: "paused" },
} satisfies Meta<typeof StatusBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 상태마다 배지가 적을 용어집의 말과 글자색·바탕색의 쓰임새 토큰. */
const EXPECTED = {
  paused: { text: "일시정지", foreground: "warning", surface: "warning-tint" },
  done: { text: "끝남", foreground: "success", surface: "success-tint" },
  failed: { text: "실패", foreground: "danger", surface: "danger-tint" },
  "no-outcome": { text: "결말 없음", foreground: "muted", surface: "tint" },
} satisfies Record<StatusBadgeStatus, { text: string; foreground: string; surface: string }>;

/** 그 상태의 배지 하나의 글자, 숨은 아이콘, 쓰임새 토큰의 글자색과 바탕색, 높이를 본다. */
async function expectBadge(canvasElement: HTMLElement, status: StatusBadgeStatus): Promise<void> {
  const { text, foreground, surface } = EXPECTED[status];
  const badge = Array.from(canvasElement.querySelectorAll("span")).find(
    (span) => span.textContent === text,
  );
  if (badge === undefined) {
    throw new Error(`글자가 "${text}" 인 배지가 없다`);
  }
  await expect(badge.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  await expect(colorsOf(badge)).toMatchObject({
    background: semanticColor(badge, surface),
    text: semanticColor(badge, foreground),
  });
  await expect(getComputedStyle(badge).height).toBe("24px");
}

/** 넷을 한 줄에 그린다. */
const renderAll: Story["render"] = (args) => (
  <div className="flex gap-2">
    {STATUS_BADGE_STATUSES.map((status) => (
      <StatusBadge key={status} {...args} status={status} />
    ))}
  </div>
);

export const Paused: Story = {
  name: "일시정지 배지는 warning-tint 바탕에 warning 글자로 일시정지라 적고 아이콘은 숨는다",
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "paused");
  },
};

export const Done: Story = {
  name: "끝남 배지는 success-tint 바탕에 success 글자로 끝남이라 적는다",
  args: { status: "done" },
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "done");
  },
};

export const Failed: Story = {
  name: "실패 배지는 danger-tint 바탕에 danger 글자로 실패라 적는다",
  args: { status: "failed" },
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "failed");
  },
};

export const NoOutcome: Story = {
  name: "결말 없음 배지는 tint 바탕에 muted 글자로 결말 없음이라 적는다",
  args: { status: "no-outcome" },
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "no-outcome");
  },
};

export const NotInteractive: Story = {
  name: "배지는 누르는 곳이 아니어서 Tab 이 지나가지 않는다",
  render: renderAll,
  play: async ({ canvasElement, userEvent }) => {
    await userEvent.tab();
    await expect(canvasElement.contains(document.activeElement)).toBe(false);
    await expect(canvasElement.querySelectorAll("button, a, [tabindex]").length).toBe(0);
  },
};

export const AllDark: Story = {
  name: "다크 모드에서도 넷이 각자의 쓰임새 토큰으로 칠해진다",
  globals: { mode: "dark" },
  render: renderAll,
  play: async ({ canvasElement }) => {
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    for (const status of STATUS_BADGE_STATUSES) {
      await expectBadge(canvasElement, status);
    }
  },
};
