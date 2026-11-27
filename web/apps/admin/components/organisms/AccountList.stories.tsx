// 계정 목록(admin-login 티켓 12, 화면 디자인 mk-accounts, mk-accounts-m). 틀 없이 그리고, 미리보기의 데코레이터가 본문 칸과 같은
// 컨테이너를 두른다. 넓은 폭(admin-storybook-wide)에서는 표, 좁은 폭(admin-storybook-narrow)에서는 계정마다 카드다. 그 갈래는
// 사진만이 아니라 위치와 역할로 본다(실행 목록의 스토리와 같은 까닭이다).
//
// 잠김은 시각이 먼 미래(2099년)라 언제 열어도 잠겨 있다. 시각 글자는 시간대에 따라 달라 play 가 글자를 단언하지 않는다. 사진은
// Asia/Seoul 로 찍힌다. 메뉴의 규칙과 창을 지나는 행동은 페이지 시험(pages/AccountsPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import type { AccountRow } from "../../api/accounts";
import { RequestFailure } from "../../api/failure";
import { AccountList } from "./AccountList";

/** 문서 뿌리에 선언된 디자인 토큰의 값. */
function rootToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** 넓은 폭의 프로젝트인가(`wide` 이상). */
function isWideProject(): boolean {
  return window.matchMedia(`(min-width: ${rootToken("--breakpoint-wide")})`).matches;
}

/** 그림 mk-accounts 의 계정. 시각은 그림의 Asia/Seoul 글자가 나오는 UTC 값이다. */
const ACCOUNTS: readonly AccountRow[] = [
  {
    name: "ops-lead",
    tier: "system_admin",
    state: "active",
    locked_until: null,
    created_at: "2026-11-01T00:12:00Z",
  },
  {
    name: "kim.dev",
    tier: "admin",
    state: "active",
    locked_until: null,
    created_at: "2026-11-03T05:20:00Z",
  },
  {
    name: "park.sre",
    tier: "admin",
    state: "active",
    locked_until: "2099-01-01T06:42:00Z",
    created_at: "2026-11-04T01:05:00Z",
  },
  {
    name: "lee.qa",
    tier: "admin",
    state: "password_unset",
    locked_until: null,
    created_at: "2026-11-15T06:18:00Z",
  },
  {
    name: "choi.ml",
    tier: "admin",
    state: "disabled",
    locked_until: null,
    created_at: "2026-11-08T02:30:00Z",
  },
];

const meta = {
  title: "organisms/AccountList",
  component: AccountList,
  args: {
    data: ACCOUNTS,
    error: undefined,
    isValidating: false,
    onRefresh: fn(),
    currentName: "ops-lead",
    tokenMinutes: 5,
    addressOf: (token: string) => `https://agent.example.com:8443/set-password#${token}`,
    actions: {
      create: fn(() => Promise.resolve({ kind: "taken" as const })),
      issueLink: fn(() =>
        Promise.resolve({
          name: "lee.qa",
          token: "7Hq2xK9mTz",
          expiresAt: "2026-11-16T06:18:00Z",
        }),
      ),
      enable: fn(async () => {}),
      disable: fn(async () => {}),
      unlock: fn(async () => {}),
    },
  },
} satisfies Meta<typeof AccountList>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 보이는 갈래 하나를 돌려준다. 역할 조회는 숨은 갈래를 넘으므로 폭에 따라 표나 목록을 고른다. */
function shownIn(region: HTMLElement): HTMLElement {
  const inside = within(region);
  return isWideProject() ? inside.getByRole("table") : inside.getByRole("list");
}

/**
 * 기본 목록. 비활성 계정(choi.ml)은 숨었고 로그인한 계정의 줄에 "지금 계정"이 붙는다. 넓은 폭에서는 표이고 열 머리는 `<th
 * scope="col">`, 행 높이는 `h-row` 다. 좁은 폭에서는 계정마다 카드다. 잠긴 계정에는 잠김 배지와 풀리는 시각이 선다.
 */
export const List: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("heading", { level: 1 })).toHaveTextContent(/^운영자 계정$/);
    const shown = shownIn(canvas.getByRole("region", { name: "운영자 계정" }));
    await expect(shown).toBeVisible();
    if (isWideProject()) {
      const heads = within(shown).getAllByRole("columnheader");
      await expect(heads.map((head) => head.textContent)).toEqual([
        "계정 이름",
        "단계",
        "상태",
        "만든 시각",
        "동작",
      ]);
      const [, first] = within(shown).getAllByRole("row");
      await expect(first?.getBoundingClientRect().height).toBe(
        Number.parseFloat(rootToken("--row-h")),
      );
    } else {
      await expect(within(shown).getAllByRole("listitem")).toHaveLength(4);
    }
    await expect(within(shown).getByText("지금 계정")).toBeVisible();
    await expect(within(shown).queryByText("choi.ml")).toBeNull();
    await expect(within(shown).getByText("잠김")).toBeVisible();
    await expect(within(shown).getByText(/^\d\d:\d\d까지$/)).toBeVisible();
    await expect(canvas.getByRole("button", { name: "계정 만들기" })).toBeVisible();
    await expect(canvas.getByRole("switch", { name: "비활성 계정도 보기" })).not.toBeChecked();
    // 시스템 관리자의 줄에는 메뉴 단추가 없고, 다른 계정마다 하나씩 있다.
    await expect(within(shown).queryByRole("button", { name: "ops-lead의 동작" })).toBeNull();
    await expect(within(shown).getAllByRole("button", { name: /의 동작$/ })).toHaveLength(3);
  },
};

/** "비활성 계정도 보기"를 켠 모양. 비활성 계정이 흐린 배지와 함께 보인다. */
export const WithInactive: Story = {
  args: { preview: { showInactive: true } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const shown = shownIn(canvas.getByRole("region", { name: "운영자 계정" }));
    await expect(canvas.getByRole("switch", { name: "비활성 계정도 보기" })).toBeChecked();
    await expect(within(shown).getByText("choi.ml")).toBeVisible();
    await expect(within(shown).getByText("비활성")).toBeVisible();
  },
};

/** 잠긴 계정의 줄 끝 메뉴가 열린 모양(그림 mk-accounts). 링크 만들기, 잠금 풀기, 가름선 아래 비활성으로 바꾸기다. */
export const MenuOpen: Story = {
  args: { preview: { openMenuOf: "park.sre" } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const shown = shownIn(canvas.getByRole("region", { name: "운영자 계정" }));
    const menu = within(shown).getByRole("menu", { name: "park.sre의 동작" });
    await expect(menu).toBeVisible();
    const items = within(menu).getAllByRole("menuitem");
    await expect(items.map((item) => item.textContent)).toEqual([
      "비밀번호 링크 만들기",
      "잠금 풀기",
      "비활성으로 바꾸기",
    ]);
    await expect(getComputedStyle(menu).boxShadow).not.toBe("none");
  },
};

/** 계정 목록을 읽지 못했다. 이미 보인 목록은 지우고 실패만 보이며 "계정 만들기"와 거르기는 남는다. */
export const ReadFailed: Story = {
  args: { data: undefined, error: new RequestFailure(null, null) },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("alert")).toHaveTextContent("계정 목록을 읽지 못했다");
    await expect(canvas.queryByRole("table")).toBeNull();
    await expect(canvas.getByRole("button", { name: "계정 만들기" })).toBeVisible();
  },
};
