// 로그인 화면을 틀(EntryFrame)과 입력 자리(LoginForm), 첫 계정 안내(FirstAccountGuide)로 그린다(admin-login 티켓 09, 화면
// 디자인 mk-login-m, mk-login-notices, mk-login-empty). 빈 상태, 이전 화면이 남긴 알림 셋, 로그인 실패, 서버에 닿지 못함,
// https 가 아닌 주소, 계정이 없는 서버를 하나씩 둔다. organisms 는 templates 를 들이지 못해(판정자의 층 경계) 화면째 그리는
// 스토리는 이 자리에 둔다. 미리보기의 afterEach 가 클래스와 가로 스크롤을, addon-a11y 가 접근성을, 사진 비교(visual/)가
// 그림을 판정한다. 로그인하고 돌아가는 행동은 페이지 테스트(pages/LoginPage.test)가 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import type { ComponentProps } from "react";
import { expect, fn, within } from "storybook/test";
import { RequestFailure } from "../../api/failure";
import { FirstAccountGuide } from "../organisms/FirstAccountGuide";
import { LoginForm } from "../organisms/LoginForm";
import { EntryFrame } from "./EntryFrame";

/** 문서 뿌리에 선언된 디자인 토큰의 값. */
function rootToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** 로그인 화면. */
function LoginScreen(props: ComponentProps<typeof LoginForm>) {
  return (
    <EntryFrame>
      <LoginForm {...props} />
    </EntryFrame>
  );
}

const meta = {
  title: "templates/EntryFrame",
  component: LoginScreen,
  parameters: { layout: "fullscreen" },
  args: {
    notice: null,
    insecure: false,
    rejected: false,
    rejections: 0,
    failure: null,
    pending: false,
    onSubmit: fn(async () => {}),
  },
} satisfies Meta<typeof LoginScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 처음 연 상태. 한 칸이 최대 폭 `form` 이고, 로그인 버튼은 넓은 폭(`wide` 이상)에서 카드의 오른쪽 끝에, 좁은 폭에서 칸의
 * 폭으로 선다.
 */
export const Empty: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(getComputedStyle(canvas.getByRole("main")).maxWidth).toBe(
      rootToken("--container-form"),
    );
    await expect(canvas.getByLabelText("비밀번호")).toHaveAttribute("type", "password");
    const field = canvas.getByLabelText("계정 이름").getBoundingClientRect();
    const button = canvas.getByRole("button", { name: "로그인" }).getBoundingClientRect();
    await expect(button.right).toBe(field.right);
    if (window.matchMedia(`(min-width: ${rootToken("--breakpoint-wide")})`).matches) {
      await expect(button.width).toBeLessThan(field.width);
    } else {
      await expect(button.left).toBe(field.left);
    }
  },
};

/** 로그아웃한 뒤. 정보 알림 하나가 입력 칸 위에 선다. */
export const LoggedOut: Story = {
  args: { notice: "logged-out" },
  play: async ({ canvasElement }) => {
    await expect(within(canvasElement).getByRole("status")).toHaveTextContent("로그아웃했다");
  },
};

/** 로그인이 끝난 뒤. */
export const Expired: Story = {
  args: { notice: "expired" },
  play: async ({ canvasElement }) => {
    const notice = within(canvasElement).getByRole("status");
    await expect(notice).toHaveTextContent("로그인이 끝났다");
    await expect(notice).toHaveTextContent("다시 로그인한다");
  },
};

/** 링크로 비밀번호를 정한 뒤. */
export const PasswordSet: Story = {
  args: { notice: "password-set" },
  play: async ({ canvasElement }) => {
    await expect(within(canvasElement).getByRole("status")).toHaveTextContent("비밀번호를 정했다");
  },
};

/** 이름이나 비밀번호가 맞지 않아 거절됐다. 실패 알림이 입력 칸 위에 남고 비밀번호 칸은 비었다. */
export const Rejected: Story = {
  args: { rejected: true, rejections: 1 },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("alert")).toHaveTextContent("로그인하지 못했다");
    await expect(canvas.getByLabelText("비밀번호")).toHaveValue("");
  },
};

/** 요청이 서버에 닿지 못했다. */
export const Unreachable: Story = {
  args: { failure: new RequestFailure(null, null) },
  play: async ({ canvasElement }) => {
    const notice = within(canvasElement).getByRole("alert");
    await expect(notice).toHaveTextContent("로그인을 보내지 못했다");
    await expect(notice).toHaveTextContent("서버에 닿지 못했다");
  },
};

/** https 가 아닌 주소로 열었다. 경고가 서고 입력 칸과 버튼이 막힌다. */
export const Insecure: Story = {
  args: { insecure: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("이 주소에서는 로그인할 수 없다")).toBeVisible();
    await expect(canvas.getByLabelText("계정 이름")).toBeDisabled();
    await expect(canvas.getByLabelText("비밀번호")).toBeDisabled();
    await expect(canvas.getByRole("button", { name: "로그인" })).toBeDisabled();
  },
};

/** 계정이 하나도 없는 서버. 입력 칸 대신 첫 계정을 만드는 명령 두 꼴이 선다. */
export const FirstAccount: Story = {
  render: () => (
    <EntryFrame>
      <FirstAccountGuide />
    </EntryFrame>
  ),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("heading", { level: 1, name: "첫 계정을 만든다" })).toBeVisible();
    await expect(canvas.getByText("agent-os operator system-admin <계정 이름>")).toBeVisible();
    await expect(
      canvas.getByText("docker compose exec serve agent-os operator system-admin <계정 이름>"),
    ).toBeVisible();
    await expect(canvas.getAllByRole("button", { name: "명령 복사" })).toHaveLength(2);
    await expect(canvas.getByRole("button", { name: "새로 고침" })).toBeVisible();
  },
};
