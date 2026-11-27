// 실행 패널(admin-login 티켓 10, 화면 디자인 ch-run). 대화 화면 위 오른쪽에 뜨는 폭 480px 의 칸이다. 넓은 폭(1280)에서는
// 오른쪽 가장자리에 붙은 480px 이고, 좁은 폭(320)에서는 화면 전체를 덮는다. 시각은 트레이스의 UTC 값 그대로다(대화 화면의
// 시각과 달리 시간대로 바꾸지 않는다). 읽는 일과 다시 읽는 일은 페이지 시험(pages/ConversationPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import type { Trace } from "../../api/traces";
import { RunPanel } from "./RunPanel";

const RUN_ID = "7f3a2c91-4b8e-4d1a-9c2f-0e6b5a8d3f12";

const TRACE: Trace = {
  run_id: RUN_ID,
  schema_version: "3",
  events: [
    {
      type: "run_started",
      run_id: RUN_ID,
      ts: "2026-11-15T07:04:02.311+00:00",
      agent: "support-bot",
      principal: "operator",
      request: "ORD-2026-11-08-000184 환불을 진행해 줘",
      previous_run: "3c1e9b07-5d2a-4f6e-8b13-a7d0c4e2f981",
      requesting_account: "ops-lead",
      shortcuts: null,
    },
    {
      type: "tool_called",
      run_id: RUN_ID,
      ts: "2026-11-15T07:04:05.402+00:00",
      tool: "orders.lookup",
      ok: true,
      args: {},
      content: '{"order_id": "ORD-2026-11-08-000184", "paid": 32000, "status": "delayed"}',
      rule: null,
    },
    {
      type: "run_paused",
      run_id: RUN_ID,
      ts: "2026-11-15T07:04:07.305+00:00",
      tool: "payments.refund",
      args: { order_id: "ORD-2026-11-08-000184", amount: 32000 },
      rule: null,
      server: null,
    },
    {
      type: "approval_granted",
      run_id: RUN_ID,
      ts: "2026-11-15T07:05:12.044+00:00",
      approver: "operator",
      deciding_account: "kim.dev",
    },
    {
      type: "run_finished",
      run_id: RUN_ID,
      ts: "2026-11-15T07:05:15.100+00:00",
      output: "환불을 접수했습니다.",
    },
  ],
};

const meta = {
  title: "organisms/RunPanel",
  component: RunPanel,
  args: {
    runId: RUN_ID,
    data: TRACE,
    error: undefined,
    isValidating: false,
    onRefresh: fn(),
    onClose: fn(),
  },
} satisfies Meta<typeof RunPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 열린 패널. 머리에 제목 "실행", "새로 고침"과 "닫기", 그 아래 실행 식별자와 에이전트·주체 줄이 서고, 본문에 이벤트가 쓴
 * 순서 그대로 선다. 요청한 계정과 결정한 계정은 필드 이름 표의 화면 이름으로 보이고 결정 자리는 없다.
 */
export const Open: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const panel = canvas.getByRole("complementary", { name: "실행 패널" });
    await expect(panel).toBeVisible();
    await expect(within(panel).getByRole("heading", { level: 2 })).toHaveTextContent(/^실행$/);
    await expect(within(panel).getByRole("button", { name: "새로 고침" })).toBeVisible();
    await expect(within(panel).getByRole("button", { name: "닫기" })).toBeVisible();
    await expect(within(panel).getByText(RUN_ID)).toBeVisible();
    await expect(within(panel).getAllByRole("heading", { level: 3 })).toHaveLength(5);
    await expect(within(panel).getByText("ops-lead")).toBeVisible();
    await expect(within(panel).getByText("kim.dev")).toBeVisible();
    await expect(within(panel).queryByRole("button", { name: /승인|거부/ })).toBeNull();
    // 넓은 폭에서는 폭이 480px 이고 좁은 폭에서는 창 전체다.
    const { width } = panel.getBoundingClientRect();
    if (window.innerWidth >= 768) {
      await expect(width).toBe(
        Number.parseFloat(
          getComputedStyle(document.documentElement).getPropertyValue("--spacing-panel"),
        ),
      );
    } else {
      await expect(width).toBe(window.innerWidth);
    }
  },
};

/** 읽는 중. 머리는 서 있고 본문 자리에 진행 표시 "실행을 불러오는 중"이 선다. */
export const Loading: Story = {
  args: { data: undefined, isValidating: true },
  play: async ({ canvasElement }) => {
    await expect(
      await within(canvasElement).findByRole("progressbar", { name: "실행을 불러오는 중" }),
    ).toBeVisible();
  },
};

/** 읽지 못했다. 보인 이벤트를 지우고 위험 알림만 선다. 머리의 "닫기"는 남는다. */
export const Failed: Story = {
  args: { data: undefined, error: new Error("없는 실행이다") },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("alert")).toBeVisible();
    await expect(canvas.getByText("실행을 읽지 못했다")).toBeVisible();
    await expect(canvas.getByRole("button", { name: "닫기" })).toBeVisible();
  },
};
