import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { TRANSPARENT, colorsOf, semanticColor } from "../../storybook/expect";
import {
  ACCOUNT_STATUS_BADGE_STATUSES,
  AccountStatusBadge,
  type AccountStatusBadgeStatus,
} from "./AccountStatusBadge";

const meta = {
  title: "atoms/AccountStatusBadge",
  component: AccountStatusBadge,
  args: { status: "active" },
} satisfies Meta<typeof AccountStatusBadge>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 상태마다 배지가 적을 말(admin-login 명세 "배지의 이름"), 앞의 아이콘, 글자·아이콘의 쓰임새 토큰. 앞의 셋은 상태 점
 * (`circle`)이고 잠김은 자물쇠(`lock`)다. 아이콘 모양은 그림의 자식 요소로 가른다(점은 `circle`, 자물쇠는 `rect`와
 * `path`).
 */
const EXPECTED = {
  active: { text: "활성", foreground: "text", shape: "circle" },
  inactive: { text: "비활성", foreground: "text-muted", shape: "circle" },
  "password-unset": { text: "비밀번호 미설정", foreground: "text-muted", shape: "circle" },
  locked: { text: "잠김", foreground: "warning", shape: "rect" },
} satisfies Record<
  AccountStatusBadgeStatus,
  { text: string; foreground: string; shape: "circle" | "rect" }
>;

/**
 * 그 상태의 배지 하나의 글자, 숨은 아이콘, 치수와 색을 본다. 바탕은 칠하지 않고(투명) 테두리는 `border` 이며, 글자와
 * 아이콘이 상태의 쓰임새 토큰이다. 치수는 실행의 상태 배지와 같다(높이 22px, 안쪽 왼쪽 6px·오른쪽 8px, 아이콘과 글자
 * 사이 4px, 아이콘 14px, 모서리 4px, 글자 12/16px·500).
 */
async function expectBadge(
  canvasElement: HTMLElement,
  status: AccountStatusBadgeStatus,
): Promise<void> {
  const { text, foreground, shape } = EXPECTED[status];
  const badge = Array.from(canvasElement.querySelectorAll("span")).find(
    (span) => span.textContent === text,
  );
  if (badge === undefined) {
    throw new Error(`글자가 "${text}" 인 배지가 없다`);
  }
  const icon = badge.querySelector("svg");
  await expect(icon?.getAttribute("aria-hidden")).toBe("true");
  await expect(icon?.querySelector(shape) === null).toBe(false);
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
  <div className="flex flex-wrap gap-2">
    {ACCOUNT_STATUS_BADGE_STATUSES.map((status) => (
      <AccountStatusBadge key={status} {...args} status={status} />
    ))}
  </div>
);

export const Active: Story = {
  name: "활성 배지는 바탕 없이 border 테두리에 text 글자로 활성이라 적고 상태 점은 숨는다",
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "active");
  },
};

export const Inactive: Story = {
  name: "비활성 배지는 바탕 없이 border 테두리에 text-muted 글자로 비활성이라 적는다",
  args: { status: "inactive" },
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "inactive");
  },
};

export const PasswordUnset: Story = {
  name: "비밀번호 미설정 배지는 바탕 없이 border 테두리에 text-muted 글자로 비밀번호 미설정이라 적는다",
  args: { status: "password-unset" },
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "password-unset");
  },
};

export const Locked: Story = {
  name: "잠김 배지는 바탕 없이 border 테두리에 warning 글자로 잠김이라 적고 상태 점 대신 자물쇠를 붙인다",
  args: { status: "locked" },
  play: async ({ canvasElement }) => {
    await expectBadge(canvasElement, "locked");
  },
};

export const NotOnlyColor: Story = {
  name: "넷이 글자로 서로 갈리고 앞의 셋은 상태 점, 잠김은 자물쇠라 색만으로 가르지 않는다",
  render: renderAll,
  play: async ({ canvasElement }) => {
    const texts = Array.from(canvasElement.querySelectorAll("span")).map(
      (span) => span.textContent,
    );
    await expect(texts).toEqual(["활성", "비활성", "비밀번호 미설정", "잠김"]);
    // 같은 색(text-muted)인 비활성과 비밀번호 미설정도 글자가 다르다.
    await expect(new Set(texts).size).toBe(4);
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
    for (const status of ACCOUNT_STATUS_BADGE_STATUSES) {
      await expectBadge(canvasElement, status);
    }
  },
};

/** 계정 목록 표본. 상태 넷이 한 번씩 나온다. 이름은 꾸민 값이다. */
const ACCOUNTS = [
  { name: "kim.admin", status: "active" },
  { name: "lee.ops", status: "inactive" },
  { name: "park.new", status: "password-unset" },
  { name: "choi.ops", status: "locked" },
] as const satisfies readonly { name: string; status: AccountStatusBadgeStatus }[];

/** 보여 주기용(`showcase`). 운영자 계정 목록에서 계정마다 상태를 배지로 보인다. 색이 아니라 글자와 아이콘이 상태를 말한다. */
export const ShowcaseAccountList: Story = {
  name: "쓰임: 운영자 계정 목록의 상태",
  tags: ["showcase"],
  render: () => (
    <ul className="flex flex-col gap-2 text-text" style={{ width: 280 }}>
      {ACCOUNTS.map(({ name, status }) => (
        <li key={name} className="flex items-center justify-between gap-4">
          <span className="font-mono text-mono">{name}</span>
          <AccountStatusBadge status={status} />
        </li>
      ))}
    </ul>
  ),
};
