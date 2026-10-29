// 관리 화면의 틀(AdminFrame)을 탐색(AdminNav)과 설정 화면의 본문(Settings)으로 그린다(admin-style 티켓 04, 화면 디자인
// mk-settings, mk-settings-m). 스토리 테스트의 넓은 폭(admin-storybook-wide)에서는 왼쪽 옆 탐색, 좁은 폭
// (admin-storybook-narrow)에서는 위 막대로 선다. 채널 토큰을 넣은 상태와 넣기 전, 하이드레이션 전의 틀만 선 모양을 둔다.
// 탐색 항목의 포커스 링은 play 가 키보드로 포커스를 옮겨 계산값으로 본다. 화면을 옮기는 행동과 토큰을 넣고 지우는 행동은
// 페이지 시험(pages/SettingsPage.test)이 본다.
import { expectedFocusRing, focusRingOf, semanticColor } from "@agent-os/ui/storybook/expect";
import type { Meta, StoryObj } from "@storybook/react-vite";
import type { ComponentProps } from "react";
import { expect, fn, within } from "storybook/test";
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

interface SettingsScreenProps extends ComponentProps<typeof Settings> {
  /** false 면 하이드레이션 전이라 틀만 서고 본문이 비었다. */
  readonly hydrated: boolean;
}

/** 설정 화면. 탐색의 지금 항목은 설정이다. */
function SettingsScreen({ hydrated, ...settings }: SettingsScreenProps) {
  return (
    <AdminFrame nav={<AdminNav current="settings" />}>
      {hydrated ? <Settings {...settings} /> : null}
    </AdminFrame>
  );
}

const meta = {
  title: "templates/AdminFrame",
  component: SettingsScreen,
  parameters: { layout: "fullscreen" },
  args: {
    hydrated: true,
    channelTokenEntered: true,
    onEnterChannelToken: fn(),
    onClearTokens: fn(),
  },
} satisfies Meta<typeof SettingsScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 채널 토큰을 넣은 설정 화면. 넓은 폭에서 옆 탐색은 폭 `nav` 이고 항목은 아이콘과 글자, 높이 `nav-item` 이다. 좁은 폭에서
 * 위 막대는 높이 `top-bar` 이고 항목은 글자만이다. 지금 항목은 `aria-current="page"` 와 `bg-selected` 다.
 */
export const ChannelTokenEntered: Story = {
  play: async ({ canvasElement, userEvent }) => {
    const canvas = within(canvasElement);
    const nav = canvas.getByRole("navigation", { name: "관리 화면" });
    const links = within(nav).getAllByRole("link");
    await expect(links.map((link) => link.textContent)).toEqual(["플러그인", "실행", "설정"]);
    const current = within(nav).getByRole("link", { current: "page" });
    await expect(current).toHaveTextContent("설정");
    await expect(getComputedStyle(current).backgroundColor).toBe(
      semanticColor(current, "bg-selected"),
    );
    await expect(canvas.queryByRole("heading", { name: "Agent OS" })).toBeNull();
    await expect(canvas.getByRole("heading", { level: 1, name: "설정" })).toBeVisible();
    // 본문 칸은 이름 없는 컨테이너다. 그 안의 컨테이너 기준 폭(`@split:`)이 본문 칸의 폭을 따른다.
    await expect(getComputedStyle(canvas.getByRole("main")).containerType).toBe("inline-size");
    await expect(canvas.getByText("채널 토큰을 넣었다")).toBeVisible();

    const icons = Array.from(nav.querySelectorAll("svg"));
    await expect(icons).toHaveLength(3);
    if (isWide()) {
      await expect(`${String(nav.getBoundingClientRect().width)}px`).toBe(
        rootToken("--spacing-nav"),
      );
      await expect(`${String(current.getBoundingClientRect().height)}px`).toBe(
        rootToken("--spacing-nav-item"),
      );
      for (const icon of icons) {
        await expect(icon).toBeVisible();
      }
    } else {
      await expect(`${String(nav.getBoundingClientRect().height)}px`).toBe(
        rootToken("--spacing-top-bar"),
      );
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

/** 채널 토큰을 넣기 전. 카드 안에 가린 입력과 주 버튼이 선다. */
export const ChannelTokenEmpty: Story = {
  args: { channelTokenEntered: false },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByLabelText("채널 토큰")).toHaveAttribute("type", "password");
    await expect(canvas.getByRole("button", { name: "채널 토큰 넣기" })).toBeVisible();
    await expect(canvas.getByRole("button", { name: "토큰 지우기" })).toBeVisible();
  },
};

/** 하이드레이션 전. 이 탭에 관리 토큰이 있는지 아직 모르는 동안 틀만 서고 본문은 비었다. */
export const BeforeHydration: Story = {
  args: { hydrated: false },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("navigation", { name: "관리 화면" })).toBeVisible();
    await expect(canvas.getByRole("main")).toBeEmptyDOMElement();
  },
};
