import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { TRANSPARENT, colorsOf, semanticColor } from "../../storybook/expect";
import { STATUS_BADGE_STATUSES, StatusBadge, type StatusBadgeStatus } from "./StatusBadge";

const meta = {
  title: "atoms/StatusBadge",
  component: StatusBadge,
  args: { status: "paused" },
} satisfies Meta<typeof StatusBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 상태마다 배지가 적을 용어집의 말과 글자·아이콘의 쓰임새 토큰. */
const EXPECTED = {
  paused: { text: "일시정지", foreground: "warning" },
  done: { text: "끝남", foreground: "success" },
  failed: { text: "실패", foreground: "danger" },
  "no-outcome": { text: "결말 없음", foreground: "text-muted" },
} satisfies Record<StatusBadgeStatus, { text: string; foreground: string }>;

/**
 * 그 상태의 배지 하나의 글자, 숨은 아이콘, 치수와 색을 본다. 바탕은 칠하지 않고(투명) 테두리는 `border` 이며, 글자와
 * 아이콘이 상태의 쓰임새 토큰이다. 치수는 밀도와 상관없다(높이 22px, 안쪽 왼쪽 6px·오른쪽 8px, 아이콘과 글자 사이
 * 4px, 아이콘 14px, 모서리 4px, 글자 12/16px·500).
 */
async function expectBadge(canvasElement: HTMLElement, status: StatusBadgeStatus): Promise<void> {
  const { text, foreground } = EXPECTED[status];
  const badge = Array.from(canvasElement.querySelectorAll("span")).find(
    (span) => span.textContent === text,
  );
  if (badge === undefined) {
    throw new Error(`글자가 "${text}" 인 배지가 없다`);
  }
  const icon = badge.querySelector("svg");
  await expect(icon?.getAttribute("aria-hidden")).toBe("true");
  await expect(colorsOf(badge)).toEqual({
    background: TRANSPARENT,
    text: semanticColor(badge, foreground),
    border: semanticColor(badge, "border"),
  });
  await expect(icon === null ? null : getComputedStyle(icon).color).toBe(
    semanticColor(badge, foreground),
  );
  const style = getComputedStyle(badge);
  await expect({
    height: style.height,
    padding: `${style.paddingLeft} ${style.paddingRight}`,
    gap: style.columnGap,
    radius: style.borderTopLeftRadius,
    font: `${style.fontSize}/${style.lineHeight} ${style.fontWeight}`,
    icon: icon === null ? null : getComputedStyle(icon).width,
  }).toEqual({
    height: "22px",
    padding: "6px 8px",
    gap: "4px",
    radius: "4px",
    font: "12px/16px 500",
    icon: "14px",
  });
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
  name: "일시정지 배지는 바탕 없이 border 테두리에 warning 글자로 일시정지라 적고 아이콘은 숨는다",
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "paused");
  },
};

export const Done: Story = {
  name: "끝남 배지는 바탕 없이 border 테두리에 success 글자로 끝남이라 적는다",
  args: { status: "done" },
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "done");
  },
};

export const Failed: Story = {
  name: "실패 배지는 바탕 없이 border 테두리에 danger 글자로 실패라 적는다",
  args: { status: "failed" },
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "failed");
  },
};

export const NoOutcome: Story = {
  name: "결말 없음 배지는 바탕 없이 border 테두리에 text-muted 글자로 결말 없음이라 적는다",
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
