// 입력 칸(admin-login 티켓 11, 화면 디자인 ch-new·ch-new-none·ch-a·ch-running·ch-failed·ch-enduser). 틀 없이 그리고 미리보기의
// 데코레이터가 본문 칸과 같은 컨테이너를 두른다. 보내는 일과 막힌 동안에도 글을 쓰는 일은 여기서 보고, 보내기가 어느 실행에서
// 이어 가는지는 페이지 시험(pages/ConversationPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import { Composer } from "./Composer";

const meta = {
  title: "organisms/Composer",
  component: Composer,
  args: {
    state: { kind: "open", help: null },
    onSend: fn(),
  },
} satisfies Meta<typeof Composer>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 끝난 대화. 글을 적고 보내면 요청 글을 알리고 칸을 비운다. 에이전트는 끝 실행의 것이라 고르지 않는다. */
export const Open: Story = {
  play: async ({ canvasElement, userEvent, args }) => {
    const canvas = within(canvasElement);
    const send = canvas.getByRole("button", { name: "보내기" });
    await expect(send).toBeDisabled();
    await userEvent.type(canvas.getByLabelText("요청"), "  다음 요청  ");
    await userEvent.click(send);
    await expect(args.onSend).toHaveBeenCalledWith("다음 요청", null);
    await expect(canvas.getByLabelText("요청")).toHaveValue("");
    await expect(canvas.queryByLabelText("에이전트")).toBeNull();
  },
};

/** 새 대화. 켜진 에이전트를 고르는 칸이 서고 첫 에이전트가 고른 채다. */
export const New: Story = {
  args: { state: { kind: "new", agents: { kind: "some", names: ["support-bot", "calc"] } } },
  play: async ({ canvasElement, userEvent, args }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByLabelText("에이전트")).toHaveValue("support-bot");
    await userEvent.selectOptions(canvas.getByLabelText("에이전트"), "calc");
    await userEvent.type(canvas.getByLabelText("요청"), "2+3은?");
    await userEvent.click(canvas.getByRole("button", { name: "보내기" }));
    await expect(args.onSend).toHaveBeenCalledWith("2+3은?", "calc");
  },
};

/** 켜진 에이전트가 없다. 고르는 칸 대신 그 까닭과 플러그인 화면으로 가는 링크가 서고 보낼 수 없다. */
export const NewWithoutAgents: Story = {
  args: { state: { kind: "new", agents: { kind: "none" } } },
  play: async ({ canvasElement, userEvent }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText(/켜진 에이전트가 없다/)).toBeVisible();
    await expect(canvas.getByRole("link", { name: "플러그인 목록" })).toHaveAttribute("href", "/");
    await userEvent.type(canvas.getByLabelText("요청"), "안녕");
    await expect(canvas.getByRole("button", { name: "보내기" })).toBeDisabled();
  },
};

/** 실행이 도는 동안. 글은 쓸 수 있고(실행이 끝나면 보낼 초안) 보내기만 막힌다. */
export const Running: Story = {
  args: {
    state: { kind: "blocked", help: "실행이 끝나면 보낼 수 있다.", waitingTool: null },
  },
  play: async ({ canvasElement, userEvent }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByLabelText("요청"), "초안");
    await expect(canvas.getByLabelText("요청")).toHaveValue("초안");
    await expect(canvas.getByRole("button", { name: "보내기" })).toBeDisabled();
    await expect(canvas.getByText("실행이 끝나면 보낼 수 있다.")).toBeVisible();
  },
};

/** 승인을 기다리는 일시정지. 입력 칸 위에 어느 도구인지와 승인 묻기로 가는 링크가 선다. */
export const Paused: Story = {
  args: {
    state: {
      kind: "blocked",
      help: "승인이나 거부를 먼저 고른다.",
      waitingTool: "payments.refund",
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("payments.refund")).toBeVisible();
    await expect(canvas.getByRole("link", { name: "승인 묻기로 가기" })).toHaveAttribute(
      "href",
      "#approval",
    );
  },
};

/** 실패한 끝 실행. 보내면 그 앞의 실행에서 이어 간다고 알린다. */
export const AfterFailure: Story = {
  args: {
    state: {
      kind: "open",
      help: "실패한 실행은 이어 가지 못해, 보내면 그 앞의 실행에서 이어 간다.",
    },
  },
  play: async ({ canvasElement }) => {
    await expect(within(canvasElement).getByText(/그 앞의 실행에서 이어 간다/)).toBeVisible();
  },
};

/** 최종 사용자의 대화. 입력 칸 대신 한 줄이 선다. */
export const EndUser: Story = {
  args: { state: { kind: "endUser" } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("최종 사용자의 대화라 이어 가거나 결정할 수 없다")).toBeVisible();
    await expect(canvas.queryByLabelText("요청")).toBeNull();
  },
};
