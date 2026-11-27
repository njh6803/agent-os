// 계정 만들기 창(admin-login 티켓 12, 화면 디자인 mk-accounts-create). 창은 `body` 에 포털로 서서 어두운 막이 화면을 덮는다.
// 뒤에 화면이 있어야 하므로 데코레이터가 이름만 든 본문을 둔다. 이름 규칙을 어긴 모양은 칸을 떠나야 알려서 사진이 아니라 play 가
// 본다. 서버의 답(409, 422)과 만든 뒤의 링크 창은 페이지 시험(pages/AccountsPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, screen } from "storybook/test";
import { CreateAccountDialog } from "./CreateAccountDialog";

const meta = {
  title: "organisms/CreateAccountDialog",
  component: CreateAccountDialog,
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
    onCreate: fn(() => Promise.resolve({ kind: "taken" as const })),
    onCreated: fn(),
    onClose: fn(),
  },
} satisfies Meta<typeof CreateAccountDialog>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 처음 연 모양. 이름 칸에 포커스가 있고 "단계: 관리자" 글이 서며 만들기와 취소가 오른쪽 끝에 선다. */
export const Empty: Story = {
  play: async () => {
    const dialog = screen.getByRole("dialog", { name: "계정 만들기" });
    await expect(dialog).toBeVisible();
    await expect(screen.getByLabelText("계정 이름")).toHaveFocus();
    await expect(dialog).toHaveTextContent("단계: 관리자");
    await expect(screen.getByRole("button", { name: "만들기" })).toBeVisible();
    await expect(screen.getByRole("button", { name: "취소" })).toBeVisible();
    // 창은 본문 칸이 아니라 `body` 에 서서 화면 전체를 덮는다.
    await expect(dialog.closest("body")).toBe(document.body);
    await expect(getComputedStyle(dialog).boxShadow).not.toBe("none");
  },
};

/** 규칙을 어긴 이름은 칸을 떠날 때 알리고 창을 닫지 않는다. Esc 는 창을 닫는다. */
export const InvalidName: Story = {
  play: async ({ args, userEvent }) => {
    await userEvent.type(screen.getByLabelText("계정 이름"), "ab");
    await userEvent.tab();
    await expect(screen.getByText(/^규칙에 맞지 않는 이름이다/)).toBeVisible();
    await expect(screen.getByLabelText("계정 이름")).toBeInvalid();
    await expect(args.onCreate).not.toHaveBeenCalled();

    await userEvent.keyboard("{Escape}");
    await expect(args.onClose).toHaveBeenCalledTimes(1);
  },
};
