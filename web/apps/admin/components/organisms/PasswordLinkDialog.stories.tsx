// 비밀번호 링크 창(admin-login 티켓 12, 화면 디자인 mk-accounts-link). 링크와 "복사" 단추, 두 줄과 알림, 닫기다. 창은 `body` 에
// 포털로 서므로 데코레이터가 이름만 든 본문을 뒤에 둔다. 복사한 글을 클립보드에서 읽는 일과 닫은 뒤 링크가 사라지는 일은 페이지
// 시험(pages/AccountsPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, screen, within } from "storybook/test";
import { PasswordLinkDialog } from "./PasswordLinkDialog";

const meta = {
  title: "organisms/PasswordLinkDialog",
  component: PasswordLinkDialog,
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
  args: {
    // 끝나는 시각은 그림의 Asia/Seoul 글자가 나오는 UTC 값이다.
    link: { name: "lee.qa", token: "7Hq2xK9mTz", expiresAt: "2026-11-16T06:18:00Z" },
    addressOf: (token: string) => `https://agent.example.com:8443/set-password#${token}`,
    onClose: fn(),
  },
} satisfies Meta<typeof PasswordLinkDialog>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 만든 직후의 링크 창. 링크는 고정폭으로 길어도 줄을 바꿔 창을 넘지 않고, 복사와 닫기가 서며, 네 줄(전하는 법, 한 번만 쓰임과
 * 기한, 다시 만들면 쓸 수 없음, 서버가 다시 보여 주지 못함)이 모두 보인다.
 */
export const Created: Story = {
  play: async () => {
    const dialog = screen.getByRole("dialog", { name: "lee.qa의 비밀번호 링크" });
    await expect(dialog).toBeVisible();
    const address = within(dialog).getByText(
      "https://agent.example.com:8443/set-password#7Hq2xK9mTz",
    );
    await expect(address).toBeVisible();
    await expect(address.getBoundingClientRect().right).toBeLessThanOrEqual(
      dialog.getBoundingClientRect().right,
    );
    await expect(within(dialog).getByRole("button", { name: "복사" })).toBeVisible();
    await expect(dialog).toHaveTextContent(
      "이 링크를 lee.qa에게 직접 전한다. 메일은 보내지 않는다.",
    );
    await expect(dialog).toHaveTextContent(/한 번만 쓰인다\. .+에 끝난다\(만든 뒤 24시간\)\./);
    await expect(dialog).toHaveTextContent("다시 만들면 이 링크는 쓸 수 없다.");
    await expect(dialog).toHaveTextContent(
      "서버는 링크를 다시 보여 주지 못한다. 잃으면 새로 만든다.",
    );
    await expect(within(dialog).getByRole("button", { name: "닫기" })).toBeVisible();
  },
};

/** Esc 는 창을 닫는다. */
export const CloseWithEscape: Story = {
  play: async ({ args, userEvent }) => {
    await userEvent.keyboard("{Escape}");
    await expect(args.onClose).toHaveBeenCalledTimes(1);
  },
};
