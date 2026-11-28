// 승인 묻기(admin-login 티켓 11, 옛 실행 상세 화면의 결정 자리를 옮긴 것. 화면 디자인 ch-a의 승인 묻기). 대화 안의 도구 호출 자리에
// 서는 카드다. 도구와 인자를 글자 그대로 고정폭으로 보이고 거부 사유 칸과 "거부"(보조), "승인"(주)이 아래에 선다. 폭 둘(1280, 320)
// 에서 모두 같은 한 열이고, 칸 폭이 360px 미만(320 폭)이면 버튼 둘이 위아래로 꽉 찬다. 결정을 보내는 일과 다시 읽는 일은
// 페이지 시험(pages/ConversationPage.write.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import type { PluginRow } from "../../api/plugins";
import { RequestFailure } from "../../api/failure";
import { ApprovalAsk } from "./ApprovalAsk";

/** 매니페스트를 읽은 에이전트 행. 쓰는 MCP 서버 하나를 든다. */
function agentRow({ enabled }: { readonly enabled: boolean }): PluginRow {
  return {
    kind: "agent",
    name: "support-bot",
    enabled,
    manifest: {
      schema_version: "1",
      kind: "agent",
      name: "support-bot",
      version: "0.1.0",
      entrypoint: "agent:Agent",
      mcp: ["payments"],
      requires_approval: ["payments.refund"],
      conversation_limit: null,
      max_turns: null,
      max_tool_calls: null,
      model: null,
      skills: [],
      provider: null,
      model_id: null,
      max_tokens: null,
      temperature: null,
      base_url: null,
      api_key_env: null,
      server: null,
    },
  };
}

function mcpRow({ enabled }: { readonly enabled: boolean }): PluginRow {
  return {
    kind: "mcp",
    name: "payments",
    enabled,
    manifest: {
      schema_version: "1",
      kind: "mcp",
      name: "payments",
      version: "0.1.0",
      entrypoint: null,
      mcp: [],
      requires_approval: [],
      conversation_limit: null,
      max_turns: null,
      max_tool_calls: null,
      model: null,
      skills: [],
      provider: null,
      model_id: null,
      max_tokens: null,
      temperature: null,
      base_url: null,
      api_key_env: null,
      server: { transport: "stdio", command: "payments-mcp", args: [], secret_args: {} },
    },
  };
}

const ON: readonly PluginRow[] = [agentRow({ enabled: true }), mcpRow({ enabled: true })];

const meta = {
  title: "organisms/ApprovalAsk",
  component: ApprovalAsk,
  args: {
    approval: {
      state: "waiting",
      tool: "payments.refund",
      args: { order_id: "ORD-2026-11-08-000184", amount: 38000, currency: "KRW" },
      at: "2026-11-15T07:04:07+00:00",
      pauseIndex: 4,
    },
    agent: "support-bot",
    busy: false,
    invalid: null,
    plugins: { data: ON, error: undefined },
    onDecide: fn(),
  },
} satisfies Meta<typeof ApprovalAsk>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 기다리는 승인. 도구는 `font-medium` 고정폭이고 인자는 글자 그대로의 JSON 이다. 버튼은 "거부"가 먼저이고 "승인"이 나중이다.
 * 사유가 비어 있으면 거부를 보낼 수 없고, 승인은 그 일시정지의 자리와 함께 간다.
 */
export const Default: Story = {
  play: async ({ canvasElement, userEvent, args }) => {
    const canvas = within(canvasElement);
    const ask = canvas.getByRole("region", { name: "승인 묻기" });
    await expect(within(ask).getByText("payments.refund")).toBeVisible();
    await expect(within(ask).getByText(/"amount": 38000/)).toBeVisible();
    const buttons = within(ask).getAllByRole("button");
    await expect(buttons.map((button) => button.textContent)).toEqual(["거부", "승인"]);
    await expect(within(ask).getByRole("button", { name: "거부" })).toBeDisabled();
    await userEvent.click(within(ask).getByRole("button", { name: "승인" }));
    await expect(args.onDecide).toHaveBeenCalledWith({ decision: "approve", pause_index: 4 });
  },
};

/** 보내는 동안. 거부 사유 칸은 그대로 두고 버튼 둘이 막힌다. */
export const Busy: Story = {
  args: { busy: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "거부" })).toBeDisabled();
    await expect(canvas.getByRole("button", { name: "승인" })).toBeDisabled();
  },
};

/** 에이전트가 꺼져 있다. 무엇이 꺼졌는지 경고로 알리고 사유 칸과 버튼 둘이 막힌다. 켜면 풀린다. */
export const DisabledAgent: Story = {
  args: {
    plugins: { data: [agentRow({ enabled: false }), mcpRow({ enabled: true })], error: undefined },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(
      canvas.getByText("꺼진 플러그인이 있어 재개할 수 없다: 에이전트 support-bot"),
    ).toBeVisible();
    await expect(canvas.getByRole("link", { name: "플러그인 목록" })).toHaveAttribute("href", "/");
    await expect(canvas.getByLabelText("거부 사유")).toBeDisabled();
    await expect(canvas.getByRole("button", { name: "승인" })).toBeDisabled();
  },
};

/** 에이전트가 쓰는 MCP 서버가 꺼져 있다. 꺼진 것의 종류와 이름이 함께 보인다. */
export const DisabledMcp: Story = {
  args: {
    plugins: { data: [agentRow({ enabled: true }), mcpRow({ enabled: false })], error: undefined },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(
      canvas.getByText("꺼진 플러그인이 있어 재개할 수 없다: MCP payments"),
    ).toBeVisible();
  },
};

/** 목록을 다시 읽다 실패했다. 옛 목록을 믿지 않고 미리 알 수 없다고 말하며 버튼은 막지 않는다. */
export const PluginsUnknown: Story = {
  args: { plugins: { data: ON, error: new Error("읽지 못했다") } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(
      canvas.getByText("플러그인 목록을 읽지 못해 꺼진 플러그인을 미리 알 수 없다"),
    ).toBeVisible();
    await expect(canvas.getByRole("button", { name: "승인" })).toBeEnabled();
  },
};

/**
 * 서버가 결정을 형식 오류(422)로 돌려줬다. 사유 칸 아래의 알림이 메시지와 추적 식별자와 위반을 모두 보이고, 사유에 걸린 위반은
 * 사유 칸이 오류 상태로 받는다.
 */
export const Invalid: Story = {
  args: {
    invalid: new RequestFailure(422, {
      code: "invalid_request",
      message: "요청의 형식이 올바르지 않다",
      request_id: "req-4220",
      violations: [
        { field: "body.deny.reason", message: "사유는 비어 있을 수 없다" },
        { field: "body.pause_index", message: "음수일 수 없다" },
      ],
    }),
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const alert = canvas.getByRole("alert");
    await expect(within(alert).getByText("결정을 보내지 못했다")).toBeVisible();
    await expect(within(alert).getByText("req-4220")).toBeVisible();
    await expect(within(alert).getByText("body.pause_index")).toBeVisible();
    await expect(canvas.getByLabelText("거부 사유")).toHaveAttribute("aria-invalid", "true");
  },
};

/** 서버에 닿지 못해 결정을 보내지 못했다. 승인 묻기는 그대로 서서 다시 누를 수 있다. */
export const Unreachable: Story = {
  args: { invalid: new RequestFailure(null, null) },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(within(canvas.getByRole("alert")).getByText("결정을 보내지 못했다")).toBeVisible();
    await expect(canvas.getByRole("button", { name: "승인" })).toBeEnabled();
  },
};
