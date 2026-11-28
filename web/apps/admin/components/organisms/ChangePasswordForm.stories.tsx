// 내 비밀번호 바꾸기(admin-login 티켓 12, 화면 디자인 mk-my-password). 틀 없이 본문만 그린다. 칸 둘과 규칙 목록과 단추 하나이고,
// 바꿨을 때와 잠겼을 때의 알림, 서버가 칸에 단 글이 칸 아래에 선다. 규칙의 셈과 보내는 행동은 페이지 시험(pages/PasswordPage.test)이
// 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import { RequestFailure } from "../../api/failure";
import { ChangePasswordForm, type ChangePasswordState } from "./ChangePasswordForm";

const IDLE: ChangePasswordState = {
  pending: false,
  changed: false,
  locked: false,
  currentError: null,
  newError: null,
  changes: 0,
  failure: null,
};

const meta = {
  title: "organisms/ChangePasswordForm",
  component: ChangePasswordForm,
  args: { name: "kim.dev", state: IDLE, tokenMinutes: 5, onSubmit: fn(async () => {}) },
} satisfies Meta<typeof ChangePasswordForm>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 처음 연 모양. 칸 둘은 비밀번호 칸이고 규칙 넷이 처음부터 보인다. 단추는 넓은 폭에서 카드 오른쪽 끝에 선다. */
export const Empty: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("heading", { level: 1 })).toHaveTextContent("내 비밀번호 바꾸기");
    await expect(canvas.getByLabelText("지금 비밀번호")).toHaveAttribute("type", "password");
    await expect(canvas.getByLabelText("새 비밀번호")).toHaveAttribute("type", "password");
    await expect(canvas.getByRole("list", { name: "비밀번호 규칙" })).toBeVisible();
    await expect(canvas.getByRole("button", { name: "비밀번호 바꾸기" })).toBeVisible();
  },
};

/** 바꿨다. 정보 알림이 로그인이 끊기는 분을 알린다. */
export const Changed: Story = {
  args: { state: { ...IDLE, changed: true, changes: 1 } },
  play: async ({ canvasElement }) => {
    const notice = within(canvasElement).getByRole("status");
    await expect(notice).toHaveTextContent("비밀번호를 바꿨다");
    await expect(notice).toHaveTextContent("다른 곳의 로그인은 길어야 5분 안에 끊긴다");
  },
};

/** 계정이 잠겼다. */
export const Locked: Story = {
  args: { state: { ...IDLE, locked: true } },
  play: async ({ canvasElement }) => {
    await expect(within(canvasElement).getByRole("alert")).toHaveTextContent(
      "계정이 잠겼다. 잠시 뒤에 다시 한다",
    );
  },
};

/** 서버가 두 칸에 글을 달았다. 칸 아래에 위험 색의 글이 서고 칸은 잘못된 값이다. */
export const FieldErrors: Story = {
  args: {
    state: {
      ...IDLE,
      currentError: "지금 비밀번호가 맞지 않는다",
      newError: "지금 비밀번호와 같다",
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByLabelText("지금 비밀번호")).toBeInvalid();
    await expect(canvas.getByLabelText("새 비밀번호")).toBeInvalid();
    await expect(canvas.getByText("지금 비밀번호가 맞지 않는다")).toBeVisible();
    await expect(canvas.getByText("지금 비밀번호와 같다")).toBeVisible();
  },
};

/** 서버에 닿지 못했다. */
export const Unreachable: Story = {
  args: { state: { ...IDLE, failure: new RequestFailure(null, null) } },
  play: async ({ canvasElement }) => {
    const alert = within(canvasElement).getByRole("alert");
    await expect(alert).toHaveTextContent("비밀번호를 바꾸지 못했다");
    await expect(alert).toHaveTextContent("서버에 닿지 못했다");
  },
};
