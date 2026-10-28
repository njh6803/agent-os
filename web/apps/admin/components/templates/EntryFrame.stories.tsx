// 관리 토큰 넣기 화면을 틀(EntryFrame)과 넣는 자리(AdminTokenForm)로 그린다(admin-style 티켓 03, 화면 디자인 mk-token,
// mk-token-m). 빈 상태, 거부, 서버에 닿지 못함, 이 탭에 채널 토큰이 남은 상태를 하나씩 둔다. organisms 는 templates 를
// 들이지 못해(판정자의 층 경계) 화면째 그리는 스토리는 이 자리에 둔다. 미리보기의 afterEach 가 클래스와 가로 스크롤을,
// addon-a11y 가 접근성을, 사진 비교(visual/)가 그림을 판정한다. 넣고 지우는 행동은 페이지 테스트(pages/HomePage.test)가 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import type { ComponentProps } from "react";
import { expect, fn, within } from "storybook/test";
import { AdminTokenForm } from "../organisms/AdminTokenForm";
import { EntryFrame } from "./EntryFrame";

/** 문서 뿌리에 선언된 디자인 토큰의 값. */
function rootToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** 관리 토큰을 넣기 전의 화면. */
function TokenEntry(props: ComponentProps<typeof AdminTokenForm>) {
  return (
    <EntryFrame>
      <AdminTokenForm {...props} />
    </EntryFrame>
  );
}

const meta = {
  title: "templates/EntryFrame",
  component: TokenEntry,
  parameters: { layout: "fullscreen" },
  args: { notice: null, onEnter: fn(async () => {}), onClearTokens: null },
} satisfies Meta<typeof TokenEntry>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 처음 연 상태. 한 칸이 최대 폭 `form` 이고, 넣기 버튼은 넓은 폭(`wide` 이상)에서 카드의 오른쪽 끝에, 좁은 폭에서 칸의
 * 폭으로 선다.
 */
export const Empty: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(getComputedStyle(canvas.getByRole("main")).maxWidth).toBe(
      rootToken("--container-form"),
    );
    const field = canvas.getByLabelText("관리 토큰").getBoundingClientRect();
    const button = canvas.getByRole("button", { name: "넣기" }).getBoundingClientRect();
    await expect(button.right).toBe(field.right);
    if (window.matchMedia(`(min-width: ${rootToken("--breakpoint-wide")})`).matches) {
      await expect(button.width).toBeLessThan(field.width);
    } else {
      await expect(button.left).toBe(field.left);
    }
  },
};

/** 확인 요청이 401 이었다. */
export const Rejected: Story = {
  args: { notice: "rejected" },
  play: async ({ canvasElement }) => {
    const notice = within(canvasElement).getByRole("alert");
    await expect(notice).toHaveTextContent("관리 토큰이 거부됐다");
    await expect(notice).toHaveTextContent("서버를 띄울 때 준 값과 같은지 보고 다시 넣는다.");
  },
};

/** 확인 요청이 서버에 닿지 못했다. */
export const Unreachable: Story = {
  args: { notice: "unreachable" },
  play: async ({ canvasElement }) => {
    const notice = within(canvasElement).getByRole("alert");
    await expect(notice).toHaveTextContent("서버에 닿지 못했다");
    await expect(notice).toHaveTextContent("agent-os serve가 떠 있는지 보고 다시 넣는다.");
  },
};

/** 관리 토큰이 거부돼 넣는 자리로 돌아왔는데 이 탭에 채널 토큰이 남아 있다. */
export const ChannelTokenLeft: Story = {
  args: { notice: "rejected", onClearTokens: fn() },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("이 탭에 채널 토큰이 남아 있다.")).toBeVisible();
    await expect(canvas.getByRole("button", { name: "토큰 지우기" })).toBeVisible();
  },
};
