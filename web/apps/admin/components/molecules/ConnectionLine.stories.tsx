// 접속 확인 한 줄(connection-check 티켓 04, 명세 "행에 보이는 것"). 상태 넷과 눌러서 한 확인 옆의 시각이다. 상태는 색만이
// 아니라 아이콘 모양과 글자로 읽힌다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, within } from "storybook/test";
import { ConnectionLine } from "./ConnectionLine";

const REASON =
  "연결을 거부했다: https://docs.example.com/mcp (HTTP 401 Unauthorized). 헤더에 실은 토큰이 서버가 아는 값과 다를 수 있다.";
/** 시각은 고정한다. 사진이 실행한 때에 따라 달라지지 않게 한다. */
const AT = new Date(Date.UTC(2026, 10, 24, 3, 4, 5));

const meta = {
  title: "molecules/ConnectionLine",
  component: ConnectionLine,
  args: { result: undefined },
} satisfies Meta<typeof ConnectionLine>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 응답을 기다리는 중. 아이콘은 글자와 함께 놓인 꾸밈이라 화면 읽기 프로그램에서 숨는다. */
export const Checking: Story = {
  play: async ({ canvasElement }) => {
    const status = within(canvasElement).getByRole("status");
    await expect(status).toHaveTextContent("확인하는 중");
    await expect(status.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  },
};

export const Reached: Story = {
  args: { result: { state: "reached" } },
  play: async ({ canvasElement }) => {
    await expect(within(canvasElement).getByRole("status")).toHaveTextContent("붙음");
  },
};

/** 붙지 못함은 까닭의 글 전체를 보인다. 긴 글은 접지 않고 줄을 바꾼다. */
export const Unreached: Story = {
  args: { result: { state: "unreached", reason: REASON } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("붙지 못함")).toBeVisible();
    await expect(canvas.getByText(REASON)).toBeVisible();
    await expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(
      document.documentElement.clientWidth,
    );
  },
};

/** 확인 요청이 실패했다. 붙었는지 아닌지 모른다는 뜻이라 붙지 못함과 다른 아이콘이다. */
export const Failed: Story = {
  args: { result: { state: "failed", message: "서버에 닿지 못했다" } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("확인하지 못함")).toBeVisible();
    await expect(canvas.getByText("서버에 닿지 못했다")).toBeVisible();
  },
};

/** 눌러서 한 확인은 스스로 새로워지지 않아 확인한 시각이 함께 보인다. */
export const Stamped: Story = {
  args: { result: { state: "reached" }, stamp: { at: AT, label: "확인한 시각" } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("확인한 시각")).toBeVisible();
    await expect(canvasElement.querySelector("time")).toHaveTextContent(/^\d{2}:\d{2}:\d{2}$/);
    // 시각은 상태 영역 밖에 있어 시각만 바뀌어도 화면 읽기 프로그램이 읽지 않는다.
    await expect(canvas.getByRole("status")).not.toHaveTextContent("확인한 시각");
  },
};

/** 누른 확인의 요청이 실패하면 누른 시각이 붙는다. */
export const StampedFailure: Story = {
  args: {
    result: { state: "failed", message: "서버에 닿지 못했다" },
    stamp: { at: AT, label: "누른 시각" },
  },
  play: async ({ canvasElement }) => {
    await expect(within(canvasElement).getByText("누른 시각")).toBeVisible();
  },
};
