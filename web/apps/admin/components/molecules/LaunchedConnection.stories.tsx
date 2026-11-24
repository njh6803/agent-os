// 켜 둔 stdio MCP 서버 행의 접속 확인(connection-check 티켓 04). 버튼을 누르기 전, 응답을 기다리는 중, 응답 뒤, 요청이
// 실패했을 때, 꺼 둔 행이다. 누르면 요청이 가고 응답까지 버튼이 눌리지 않는 행동은 페이지 시험이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import { LaunchedConnection } from "./LaunchedConnection";

/** 시각은 고정한다. 사진이 실행한 때에 따라 달라지지 않게 한다. */
const AT = new Date(Date.UTC(2026, 10, 24, 3, 4, 5));

const meta = {
  title: "molecules/LaunchedConnection",
  component: LaunchedConnection,
  args: { enabled: true, pending: false, latest: undefined, onRun: fn() },
} satisfies Meta<typeof LaunchedConnection>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 누르기 전에는 결과가 없다. */
export const Idle: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "접속 확인" })).toBeEnabled();
    await expect(canvas.queryByRole("status")).toBeNull();
  },
};

/** 응답을 기다리는 중. 버튼은 눌리지 않고 확인하는 중이 보인다. */
export const Pending: Story = {
  args: { pending: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "접속 확인" })).toHaveAttribute(
      "aria-busy",
      "true",
    );
    await expect(canvas.getByRole("status")).toHaveTextContent("확인하는 중");
  },
};

export const Reached: Story = {
  args: { latest: { result: { state: "reached" }, at: AT } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("status")).toHaveTextContent("붙음");
    await expect(canvas.getByText("확인한 시각")).toBeVisible();
  },
};

export const Unreached: Story = {
  args: {
    latest: {
      result: { state: "unreached", reason: "프로세스가 시작하자마자 끝났다(종료 코드 1)" },
      at: AT,
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("붙지 못함")).toBeVisible();
    await expect(canvas.getByText("프로세스가 시작하자마자 끝났다(종료 코드 1)")).toBeVisible();
  },
};

/** 누른 확인의 요청이 실패했다. 누른 시각이 붙고 버튼은 다시 눌린다. */
export const RequestFailed: Story = {
  args: { latest: { result: { state: "failed", message: "서버에 닿지 못했다" }, at: AT } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("확인하지 못함")).toBeVisible();
    await expect(canvas.getByText("누른 시각")).toBeVisible();
    await expect(canvas.getByRole("button", { name: "접속 확인" })).toBeEnabled();
  },
};

/** 꺼 둔 행. 버튼은 누를 수 없고 결과는 보이지 않는다. */
export const Disabled: Story = {
  args: { enabled: false, latest: { result: { state: "reached" }, at: AT } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "접속 확인" })).toBeDisabled();
    await expect(canvas.queryByRole("status")).toBeNull();
  },
};
