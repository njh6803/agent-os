// 비활성으로 바꾸기 창(admin-login 티켓 12, 화면 디자인 mk-accounts-disable). 제목과 네 줄, 취소와 비활성으로 바꾸기다. 창은
// `body` 에 포털로 서므로 데코레이터가 이름만 든 본문을 뒤에 둔다. 바꾼 뒤에 창이 닫히고 목록을 다시 읽는 일, 실패하면 창 안에서
// 알리는 일은 페이지 시험(pages/AccountsPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, screen, within } from "storybook/test";
import { DisableAccountDialog } from "./DisableAccountDialog";

const meta = {
  title: "organisms/DisableAccountDialog",
  component: DisableAccountDialog,
  parameters: { layout: "fullscreen" },
  decorators: [
    (Story) => (
      <>
        <main className="p-4">
          <h1 className="text-title">운영자 계정</h1>
        </main>
        <Story />
      </>
    ),
  ],
  args: { name: "choi.ml", tokenMinutes: 5, onConfirm: fn(async () => {}), onClose: fn() },
} satisfies Meta<typeof DisableAccountDialog>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 처음 연 모양. 제목에 계정 이름이 있고 줄이 넷이며, 첫 줄은 로그인이 끊기는 분과 도는 실행이 끝까지 간다는 말이다. */
export const Confirm: Story = {
  play: async () => {
    const dialog = screen.getByRole("dialog", { name: "choi.ml을 비활성으로 바꾼다" });
    await expect(dialog).toBeVisible();
    const lines = within(dialog).getAllByRole("listitem");
    await expect(lines.map((line) => line.textContent)).toEqual([
      "이 계정의 로그인은 길어야 5분 안에 모두 끊긴다. 도는 실행은 끝까지 간다.",
      "이 이름으로 새 계정을 만들 수 없다.",
      "실행 기록에 남은 이름은 그대로다.",
      "언제든 활성으로 되돌릴 수 있다.",
    ]);
    // 포커스는 창 안의 첫 조작 요소(취소)에 있다. 되돌릴 수 있는 쪽이 먼저다.
    await expect(within(dialog).getByRole("button", { name: "취소" })).toHaveFocus();
    await expect(within(dialog).getByRole("button", { name: "비활성으로 바꾸기" })).toBeVisible();
  },
};

/** Tab 은 창 안에서 돈다. 마지막 단추에서 Tab 을 누르면 첫 단추로 돌아간다. */
export const FocusStaysInside: Story = {
  play: async ({ userEvent }) => {
    const dialog = screen.getByRole("dialog", { name: "choi.ml을 비활성으로 바꾼다" });
    await userEvent.tab();
    await expect(within(dialog).getByRole("button", { name: "비활성으로 바꾸기" })).toHaveFocus();
    await userEvent.tab();
    await expect(within(dialog).getByRole("button", { name: "취소" })).toHaveFocus();
    await userEvent.tab({ shift: true });
    await expect(within(dialog).getByRole("button", { name: "비활성으로 바꾸기" })).toHaveFocus();
  },
};
