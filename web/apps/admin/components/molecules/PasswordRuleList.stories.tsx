// 비밀번호 규칙 목록(admin-login 티켓 12, 화면 디자인 mk-set-password-states). 처음부터 보이고 규칙마다 맞음과 맞지 않음을 글자와
// 아이콘으로 함께 보인다. 눌러 보내기 전에는 맞지 않는 규칙이 흐리고, 눌러 본 뒤에 위험 색이 된다. 칸에 적는 대로 셈이 바뀌는 일은
// 페이지 시험(pages/PasswordPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, within } from "storybook/test";
import { PasswordRuleList } from "./PasswordRuleList";
import { checkPassword } from "./passwordRules";

const meta = {
  title: "molecules/PasswordRuleList",
  component: PasswordRuleList,
  args: { check: checkPassword(""), submitted: false },
} satisfies Meta<typeof PasswordRuleList>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 비어 있을 때. 규칙 넷이 모두 맞지 않음이고 아직 틀린 것이 아니라 흐린 색이다. */
export const Untouched: Story = {
  play: async ({ canvasElement }) => {
    const list = within(canvasElement).getByRole("list", { name: "비밀번호 규칙" });
    const items = within(list).getAllByRole("listitem");
    await expect(items.map((item) => item.textContent)).toEqual([
      "8자 이상맞지 않음",
      "영문 대문자 1자 이상맞지 않음",
      "숫자 1자 이상맞지 않음",
      "특수문자 1자 이상맞지 않음",
    ]);
    await expect(within(list).queryByText("맞음")).toBeNull();
  },
};

/** 일부만 맞는다. 맞는 규칙은 성공 색의 아이콘과 "맞음"이다. */
export const Partly: Story = {
  args: { check: checkPassword("abcdefgh1") },
  play: async ({ canvasElement }) => {
    const list = within(canvasElement).getByRole("list", { name: "비밀번호 규칙" });
    const items = within(list).getAllByRole("listitem");
    await expect(items.map((item) => item.textContent)).toEqual([
      "8자 이상맞음",
      "영문 대문자 1자 이상맞지 않음",
      "숫자 1자 이상맞음",
      "특수문자 1자 이상맞지 않음",
    ]);
  },
};

/** 모두 맞는다. */
export const AllMet: Story = {
  args: { check: checkPassword("Abcdefg1!") },
  play: async ({ canvasElement }) => {
    const list = within(canvasElement).getByRole("list", { name: "비밀번호 규칙" });
    await expect(within(list).getAllByText("맞음")).toHaveLength(4);
    await expect(within(list).queryByText("맞지 않음")).toBeNull();
  },
};

/** 규칙을 다 맞추지 않고 눌러 본 뒤. 맞지 않는 규칙이 위험 색의 아이콘(`circle-x`)과 글자다. */
export const Submitted: Story = {
  args: { check: checkPassword("abc"), submitted: true },
  play: async ({ canvasElement }) => {
    const list = within(canvasElement).getByRole("list", { name: "비밀번호 규칙" });
    await expect(within(list).getAllByText("맞지 않음")).toHaveLength(4);
    const first = within(list).getByText("8자 이상").closest("li");
    await expect(first?.querySelector("svg")).not.toBeNull();
  },
};
