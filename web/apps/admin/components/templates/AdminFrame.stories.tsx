// 관리 화면의 틀(AdminFrame)을 탐색(AdminNav)과 계정 자리(AccountMenu)와 설정 화면의 본문(Settings)으로 그린다(admin-style
// 티켓 04, admin-login 티켓 09, 화면 디자인 mk-settings, mk-account-menu, mk-account-menu-m). 스토리 테스트의 넓은 폭
// (admin-storybook-wide)에서는 왼쪽 옆 탐색의 맨 아래에 계정 자리가 서고, 좁은 폭(admin-storybook-narrow)에서는 위 막대가 두
// 줄이 되어 첫 줄에 "Agent OS"와 계정 단추, 둘째 줄에 탐색이 선다. 메뉴가 열린 모양, 로그아웃이 실패한 모양, "지금
// 누구인지"를 읽기 전의 틀만 선 모양을 둔다. 탐색 항목의 포커스 링은 play 가 키보드로 포커스를 옮겨 계산값으로 본다.
// 화면을 옮기고 로그아웃하는 행동은 페이지 시험(pages/SettingsPage.test, pages/AdminScreen.test)이 본다.
import { DEFAULT_THEME } from "@agent-os/ui";
import { expectedFocusRing, focusRingOf, semanticColor } from "@agent-os/ui/storybook/expect";
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import { AccountMenu } from "../organisms/AccountMenu";
import { AdminNav } from "../organisms/AdminNav";
import { Settings } from "../organisms/Settings";
import { AdminFrame } from "./AdminFrame";

/** 문서 뿌리에 선언된 디자인 토큰의 값. */
function rootToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** 창이 화면 중단점 `wide` 이상인가. */
function isWide(): boolean {
  return window.matchMedia(`(min-width: ${rootToken("--breakpoint-wide")})`).matches;
}

interface SettingsScreenProps {
  /** false 면 "지금 누구인지"를 읽기 전이라 틀만 서고 계정 자리와 본문이 비었다. */
  readonly signedIn: boolean;
  readonly tier: "system_admin" | "admin";
  readonly logoutFailed: boolean;
  /** 계정 메뉴가 열린 채 그린다(사진에 열린 모양을 남긴다). */
  readonly menuOpen: boolean;
}

/** 설정 화면. 탐색의 지금 항목은 설정이다. */
function SettingsScreen({ signedIn, tier, logoutFailed, menuOpen }: SettingsScreenProps) {
  return (
    <AdminFrame
      nav={<AdminNav current="settings" showAccounts={tier === "system_admin"} />}
      account={
        signedIn ? (
          <AccountMenu
            name="kim.dev"
            tier={tier}
            pending={false}
            failed={logoutFailed}
            initiallyOpen={menuOpen}
            onLogOut={fn(async () => {})}
          />
        ) : undefined
      }
    >
      {signedIn ? <Settings theme={DEFAULT_THEME} onChooseTheme={fn()} /> : null}
    </AdminFrame>
  );
}

const meta = {
  title: "templates/AdminFrame",
  component: SettingsScreen,
  parameters: { layout: "fullscreen" },
  args: { signedIn: true, tier: "admin", logoutFailed: false, menuOpen: false },
} satisfies Meta<typeof SettingsScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 로그인한 설정 화면. 넓은 폭에서 옆 탐색은 폭 `nav` 이고 항목은 아이콘과 글자, 높이 `nav-item` 이다. 계정 자리는 그 맨
 * 아래에 이름과 단계가 두 줄로 선다. 좁은 폭에서는 위 막대 첫 줄 오른쪽에 이름만 든 단추가 서고 항목은 글자만이다. 지금
 * 항목은 `aria-current="page"` 와 `bg-selected` 다.
 */
export const SignedIn: Story = {
  play: async ({ canvasElement, userEvent }) => {
    const canvas = within(canvasElement);
    const nav = canvas.getByRole("navigation", { name: "관리 화면" });
    const links = within(nav).getAllByRole("link");
    await expect(links.map((link) => link.textContent)).toEqual(["플러그인", "대화", "설정"]);
    const current = within(nav).getByRole("link", { current: "page" });
    await expect(current).toHaveTextContent("설정");
    await expect(getComputedStyle(current).backgroundColor).toBe(
      semanticColor(current, "bg-selected"),
    );
    await expect(canvas.queryByRole("heading", { name: "Agent OS" })).toBeNull();
    await expect(canvas.getByRole("heading", { level: 1, name: "설정" })).toBeVisible();
    // 본문 칸은 이름 없는 컨테이너다. 그 안의 컨테이너 기준 폭(`@split:`)이 본문 칸의 폭을 따른다.
    await expect(getComputedStyle(canvas.getByRole("main")).containerType).toBe("inline-size");

    const account = canvas.getByRole("button", { name: /kim\.dev/ });
    await expect(account).toHaveAttribute("aria-haspopup", "menu");
    await expect(account).toHaveAttribute("aria-expanded", "false");
    const icons = Array.from(nav.querySelectorAll("svg"));
    await expect(icons).toHaveLength(3);
    if (isWide()) {
      // 폭 `nav` 는 옆 탐색 전체(머리 요소)의 폭이다. 탐색 항목의 줄(`nav` 요소)은 그 안의 좌우 여백과 테두리를 뺀 폭이다.
      const side = nav.closest("header");
      await expect(`${String(side?.getBoundingClientRect().width)}px`).toBe(
        rootToken("--spacing-nav"),
      );
      await expect(`${String(current.getBoundingClientRect().height)}px`).toBe(
        rootToken("--spacing-nav-item"),
      );
      for (const icon of icons) {
        await expect(icon).toBeVisible();
      }
      // 계정 자리는 탐색 항목 아래, 옆 탐색의 맨 아래에 선다. 단계가 단추 안에 보인다.
      await expect(account.getBoundingClientRect().top).toBeGreaterThan(
        current.getBoundingClientRect().bottom,
      );
      await expect(within(account).getByText("관리자")).toBeVisible();
    } else {
      // 위 막대는 두 줄이다. 첫 줄에 계정 단추, 그 아래 줄에 탐색이 선다. 단계는 단추가 아니라 메뉴에 보인다.
      await expect(account.getBoundingClientRect().bottom).toBeLessThanOrEqual(
        nav.getBoundingClientRect().top,
      );
      await expect(within(account).getByText("관리자")).not.toBeVisible();
      for (const icon of icons) {
        await expect(icon).not.toBeVisible();
      }
    }

    // 키보드로 첫 항목에 포커스를 옮긴다. 사진은 이 앞의 그림이다(`.claude/rules/web-design.md`).
    await userEvent.tab();
    const first = within(nav).getByRole("link", { name: "플러그인" });
    await expect(first).toHaveFocus();
    await expect(focusRingOf(first)).toEqual(expectedFocusRing(first));
  },
};

/** 시스템 관리자. 단계 글이 다르고 탐색에 "계정"이 더 선다(관리자에게는 없다). */
export const SystemAdmin: Story = {
  args: { tier: "system_admin" },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const account = canvas.getByRole("button", { name: /kim\.dev/ });
    await expect(account).toHaveTextContent("시스템 관리자");
    const nav = canvas.getByRole("navigation", { name: "관리 화면" });
    await expect(
      within(nav)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(["플러그인", "대화", "계정", "설정"]);
    await expect(within(nav).getByRole("link", { name: "계정" })).toHaveAttribute(
      "href",
      "/accounts",
    );
  },
};

/** 계정 자리를 눌러 연 메뉴. 넓은 폭에서는 위로, 좁은 폭에서는 아래로 열리고 좁은 폭의 메뉴 맨 위에 이름과 단계가 선다. */
export const MenuOpen: Story = {
  args: { menuOpen: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const account = canvas.getByRole("button", { name: /kim\.dev/ });
    await expect(account).toHaveAttribute("aria-expanded", "true");
    const menu = canvas.getByRole("menu", { name: "kim.dev 계정" });
    await expect(
      within(menu).getByRole("menuitem", { name: "내 비밀번호 바꾸기" }),
    ).toHaveAttribute("href", "/password");
    await expect(within(menu).getByRole("menuitem", { name: "로그아웃" })).toBeVisible();
    const box = menu.getBoundingClientRect();
    const spot = account.getBoundingClientRect();
    if (isWide()) {
      await expect(box.bottom).toBeLessThanOrEqual(spot.top);
    } else {
      await expect(box.top).toBeGreaterThanOrEqual(spot.bottom);
      await expect(within(menu).getByText("관리자")).toBeVisible();
    }
    // 그림자와 테두리는 메뉴를 감싼 카드에 있다(알림이 메뉴 밖, 같은 카드 안에 서기 때문이다).
    await expect(getComputedStyle(menu.parentElement ?? menu).boxShadow).not.toBe("none");
  },
};

/** 쿠키를 지우는 응답을 받지 못해 로그아웃하지 못했다. 메뉴가 열린 채 그 자리에 알린다. */
export const LogoutFailed: Story = {
  args: { logoutFailed: true, menuOpen: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("alert")).toHaveTextContent("로그아웃하지 못했다. 다시 누른다");
  },
};

/** "지금 누구인지"를 읽기 전. 틀만 서고 계정 자리와 본문은 비었다. */
export const BeforeSignedIn: Story = {
  args: { signedIn: false },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("navigation", { name: "관리 화면" })).toBeVisible();
    await expect(canvas.queryByRole("button", { name: /kim\.dev/ })).toBeNull();
    await expect(canvas.getByRole("main")).toBeEmptyDOMElement();
  },
};
