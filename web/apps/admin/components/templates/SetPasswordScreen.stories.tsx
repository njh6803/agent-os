// 링크로 비밀번호 정하기(admin-login 티켓 12, 화면 디자인 mk-set-password, mk-set-password-states). 로그인 없이 열리는 화면이라
// 틀(EntryFrame) 안에 그린다. 입력 모양과 링크를 쓸 수 없는 모양을 둔다. 주소의 # 뒤를 지우는 일과 규칙의 셈, 두 칸이 다른 때는
// 페이지 시험(pages/SetPasswordPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import { RequestFailure } from "../../api/failure";
import { SetPasswordForm, type SetPasswordState } from "../organisms/SetPasswordForm";
import { EntryFrame } from "./EntryFrame";

const IDLE: SetPasswordState = {
  pending: false,
  unusable: false,
  passwordError: null,
  failure: null,
};

interface SetPasswordScreenProps {
  readonly insecure: boolean;
  readonly state: SetPasswordState;
  readonly onSubmit: (password: string) => Promise<void>;
}

/** 로그인 없이 열리는 화면: 입구 틀 안에 폼을 놓는다. */
function SetPasswordScreen({ insecure, state, onSubmit }: SetPasswordScreenProps) {
  return (
    <EntryFrame>
      <SetPasswordForm insecure={insecure} state={state} onSubmit={onSubmit} />
    </EntryFrame>
  );
}

const meta = {
  title: "templates/SetPasswordScreen",
  component: SetPasswordScreen,
  parameters: { layout: "fullscreen" },
  args: { insecure: false, state: IDLE, onSubmit: fn(() => Promise.resolve()) },
} satisfies Meta<typeof SetPasswordScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 처음 연 모양. 새 비밀번호 칸 둘과 규칙 넷이 서고 계정 이름은 어디에도 없다. */
export const Empty: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("heading", { level: 1 })).toHaveTextContent("비밀번호 정하기");
    await expect(canvas.getByLabelText("새 비밀번호")).toHaveAttribute("type", "password");
    await expect(canvas.getByLabelText("새 비밀번호 다시")).toHaveAttribute("type", "password");
    await expect(canvas.getByRole("list", { name: "비밀번호 규칙" })).toBeVisible();
    await expect(canvas.getByRole("button", { name: "비밀번호 정하기" })).toBeVisible();
  },
};

/** 링크를 더 쓸 수 없다(404). 입력 칸은 걷히고 안내와 로그인 화면으로 가는 링크만 남는다. */
export const Unusable: Story = {
  args: { state: { ...IDLE, unusable: true } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const alert = canvas.getByRole("alert");
    await expect(alert).toHaveTextContent("이 링크는 더 쓸 수 없다");
    await expect(alert).toHaveTextContent("관리하는 사람에게 새 링크를 받는다");
    await expect(canvas.queryByLabelText("새 비밀번호")).toBeNull();
    await expect(canvas.getByRole("link", { name: "로그인 화면으로" })).toHaveAttribute(
      "href",
      "/login",
    );
  },
};

/** https가 아닌 주소로 열었다. 알림이 서고 정하기 단추만 막히며 입력 칸은 열려 있다. */
export const Insecure: Story = {
  args: { insecure: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("status")).toHaveTextContent(
      "이 주소에서는 비밀번호를 정할 수 없다",
    );
    await expect(canvas.getByLabelText("새 비밀번호")).toBeEnabled();
    await expect(canvas.getByRole("button", { name: "비밀번호 정하기" })).toBeDisabled();
  },
};

/** 서버가 비밀번호 칸에 글을 달았다. */
export const ServerRejected: Story = {
  args: { state: { ...IDLE, passwordError: "제어 문자는 쓸 수 없다" } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByLabelText("새 비밀번호")).toBeInvalid();
    await expect(canvas.getByText("제어 문자는 쓸 수 없다")).toBeVisible();
  },
};

/** 서버에 닿지 못했다. */
export const Unreachable: Story = {
  args: { state: { ...IDLE, failure: new RequestFailure(null, null) } },
  play: async ({ canvasElement }) => {
    const alert = within(canvasElement).getByRole("alert");
    await expect(alert).toHaveTextContent("비밀번호를 정하지 못했다");
    await expect(alert).toHaveTextContent("서버에 닿지 못했다");
  },
};
