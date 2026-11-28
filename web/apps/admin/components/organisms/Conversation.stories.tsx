// 대화 화면(admin-login 티켓 10, 화면 디자인 ch-a, ch-run, ch-running). 틀 없이 그리고 미리보기의 데코레이터가 본문 칸과
// 같은 컨테이너를 두른다. 가운데 한 열에 요청과 출력이 말풍선으로 이어진다. 폭 둘(1280, 320)에서 모두 같은 한 열이다.
// 시각은 사진을 찍는 Asia/Seoul 로 적히고(visual/playwright.config.ts) play 는 시각 글자를 단언하지 않는다. 읽는 일과
// 다시 읽는 일은 페이지 시험(pages/ConversationPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import type { Turn } from "../../api/conversation";
import type { Trace } from "../../api/traces";
import { Conversation, type ConversationData } from "./Conversation";
import { RunPanel } from "./RunPanel";

const FIRST_OUTPUT = `지난주 환불 요청 가운데 아직 처리하지 않은 것은 **2건**입니다.

- ORD-2026-11-08-000184: 배송 지연
- ORD-2026-11-09-000201: 상품 파손`;

const SECOND_OUTPUT =
  "ORD-2026-11-08-000184 환불을 접수했습니다. 영업일 기준 3일 안에 카드로 돌아갑니다.";

const FIRST: Turn = {
  runId: "3c1e9b07-5d2a-4f6e-8b13-a7d0c4e2f981",
  agent: "support-bot",
  principal: "operator",
  requestingAccount: "kim.dev",
  startedAt: "2026-11-15T07:03:50+00:00",
  request: "지난주 환불 요청 가운데 아직 처리하지 않은 것을 찾아 줘",
  tools: [{ tool: "orders.search", ok: true }],
  approvals: [],
  outcome: { kind: "finished", output: FIRST_OUTPUT, at: "2026-11-15T07:03:58+00:00" },
};

const SECOND: Turn = {
  runId: "7f3a2c91-4b8e-4d1a-9c2f-0e6b5a8d3f12",
  agent: "support-bot",
  principal: "operator",
  requestingAccount: "kim.dev",
  startedAt: "2026-11-15T07:04:02+00:00",
  request: "ORD-2026-11-08-000184 환불을 진행해 줘",
  tools: [
    { tool: "orders.lookup", ok: true },
    { tool: "payments.refund", ok: true },
  ],
  approvals: [
    {
      state: "granted",
      tool: "payments.refund",
      at: "2026-11-15T07:05:12+00:00",
      by: "kim.dev",
      pauseIndex: 4,
    },
  ],
  outcome: { kind: "finished", output: SECOND_OUTPUT, at: "2026-11-15T07:05:15+00:00" },
};

const DATA: ConversationData = { turns: [FIRST, SECOND], earlier: "start" };

const meta = {
  title: "organisms/Conversation",
  component: Conversation,
  args: {
    data: DATA,
    error: undefined,
    isValidating: false,
    onRefresh: fn(),
    fresh: false,
    actions: {
      canAct: true,
      busy: false,
      invalid: null,
      plugins: { data: [], error: undefined },
      onDecide: fn(),
      onRetry: fn(),
    },
    stale: false,
    timeoutSeconds: 300,
    openRun: null,
    onOpenRun: fn(),
  },
} satisfies Meta<typeof Conversation>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 두 실행의 대화. 요청은 오른쪽의 말풍선이고 도구 호출은 "도구 N개를 불렀다"로 접혀 있으며 출력은 마크다운으로 그린다.
 * 둘째 실행의 승인은 "<결정한 계정>가 <시각>에 승인했다: <도구>" 한 줄이다. 실행마다 상태 배지와 시각과 "자세히"가 선다.
 */
export const Thread: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("heading", { level: 1 })).toHaveTextContent(/^대화$/);
    const sections = canvas.getAllByRole("region", { name: /^실행 \d+$/ });
    await expect(sections).toHaveLength(2);
    await expect(within(sections[0] ?? canvasElement).getByText("도구 1개를 불렀다")).toBeVisible();
    await expect(within(sections[1] ?? canvasElement).getByText("도구 2개를 불렀다")).toBeVisible();
    await expect(
      within(sections[1] ?? canvasElement).getByText(/kim.dev가 .*에 승인했다/),
    ).toBeVisible();
    await expect(within(sections[0] ?? canvasElement).getByText("2건").tagName).toBe("STRONG");
    for (const button of canvas.getAllByRole("button", { name: "자세히" })) {
      await expect(button.getBoundingClientRect().height).toBeGreaterThanOrEqual(24);
    }
    // 가로로 밀리지 않는다.
    await expect(canvasElement.scrollWidth).toBeLessThanOrEqual(canvasElement.clientWidth);
  },
};

/** 도구 호출 묶음을 펼친 모습. 이름은 글자 그대로 고정폭이고 성공과 실패가 아이콘과 글자로 함께 보인다. */
export const ToolsOpen: Story = {
  args: {
    data: {
      turns: [
        {
          ...SECOND,
          tools: [
            { tool: "orders.lookup", ok: true },
            { tool: "payments.refund", ok: false },
          ],
        },
      ],
      earlier: "start",
    },
  },
  play: async ({ canvasElement, userEvent }) => {
    const canvas = within(canvasElement);
    await userEvent.click(canvas.getByText("도구 2개를 불렀다"));
    await expect(canvas.getByText("orders.lookup")).toBeVisible();
    await expect(canvas.getByText("실패")).toBeVisible();
  },
};

/** 실패한 실행. 위험 알림에 실패 이벤트의 글이 든다. */
export const Failed: Story = {
  args: {
    data: {
      turns: [
        FIRST,
        {
          ...SECOND,
          approvals: [],
          tools: [],
          outcome: {
            kind: "failed",
            error: "모델이 답하지 않았다(제한 시간 초과)",
            at: "2026-11-15T07:04:40+00:00",
          },
        },
      ],
      earlier: "start",
    },
  },
  play: async ({ canvasElement, userEvent, args }) => {
    const alert = within(canvasElement).getByRole("alert");
    await expect(within(alert).getByText("실행이 실패했다")).toBeVisible();
    await expect(within(alert).getByText("모델이 답하지 않았다(제한 시간 초과)")).toBeVisible();
    await userEvent.click(within(alert).getByRole("button", { name: "다시 보내기" }));
    await expect(args.actions.onRetry).toHaveBeenCalledTimes(1);
  },
};

/** 최종 사용자의 대화에서 실패한 실행에는 "다시 보내기"가 없다. */
export const FailedEndUser: Story = {
  args: {
    data: {
      turns: [
        {
          ...SECOND,
          approvals: [],
          tools: [],
          outcome: {
            kind: "failed",
            error: "모델이 답하지 않았다",
            at: "2026-11-15T07:04:40+00:00",
          },
        },
      ],
      earlier: "start",
    },
    actions: { ...meta.args.actions, canAct: false },
  },
  play: async ({ canvasElement }) => {
    await expect(within(canvasElement).queryByRole("button", { name: "다시 보내기" })).toBeNull();
  },
};

const WAITING: ConversationData = {
  turns: [
    {
      ...SECOND,
      approvals: [
        {
          state: "waiting",
          tool: "payments.refund",
          args: { order_id: "ORD-2026-11-08-000184", amount: 32000, reason: "배송 지연" },
          at: "2026-11-15T07:04:07+00:00",
          pauseIndex: 4,
        },
      ],
      outcome: { kind: "paused" },
    },
  ],
  earlier: "start",
};

/**
 * 승인을 기다리는 실행. 도구 호출 자리에 승인 묻기가 선다. 도구와 인자는 글자 그대로 고정폭이고 "거부"(보조)가 먼저, "승인"(주)이
 * 나중이다(`.claude/rules/web-design.md`). 거부 사유를 적어야 거부를 보낼 수 있다.
 */
export const Waiting: Story = {
  args: { data: WAITING },
  play: async ({ canvasElement, userEvent, args }) => {
    const canvas = within(canvasElement);
    const ask = canvas.getByRole("region", { name: "승인 묻기" });
    await expect(ask).toBeVisible();
    // 같은 도구의 앞 결정이 대화에 한 줄로 남아 있어, 도구 이름은 승인 묻기 안에서 찾는다.
    await expect(within(ask).getByText("payments.refund")).toBeVisible();
    const buttons = canvas
      .getAllByRole("button")
      .filter((button) => /^(거부|승인)$/.test(button.textContent));
    await expect(buttons.map((button) => button.textContent)).toEqual(["거부", "승인"]);
    await expect(canvas.getByRole("button", { name: "거부" })).toBeDisabled();
    await userEvent.type(canvas.getByLabelText("거부 사유"), "금액을 다시 확인한다");
    await userEvent.click(canvas.getByRole("button", { name: "거부" }));
    await expect(args.actions.onDecide).toHaveBeenCalledWith(SECOND.runId, {
      decision: "deny",
      pause_index: 4,
      reason: "금액을 다시 확인한다",
    });
  },
};

/** 최종 사용자의 대화는 볼 수만 있다. 승인 묻기가 서지 않고 기다리는 중이라는 한 줄이 남는다. */
export const WaitingEndUser: Story = {
  args: { data: WAITING, actions: { ...meta.args.actions, canAct: false } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText(/승인을 기다리는 중/)).toBeVisible();
    await expect(canvas.queryByRole("button", { name: /^(승인|거부)$/ })).toBeNull();
  },
};

/** 새 대화. 읽을 것이 없어 머리만 서고 "새로 고침"이 없다. */
export const Fresh: Story = {
  args: { fresh: true, data: { turns: [], earlier: "start" } },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("heading", { level: 1 })).toHaveTextContent(/^새 대화$/);
    await expect(canvas.queryByRole("button", { name: "새로 고침" })).toBeNull();
  },
};

/** 도는 실행. 마지막으로 받은 이벤트의 다음 일을 진행 표시가 보인다. */
export const Running: Story = {
  args: {
    data: {
      turns: [FIRST, { ...SECOND, approvals: [], outcome: { kind: "running", step: "model" } }],
      earlier: "start",
    },
  },
  play: async ({ canvasElement }) => {
    await expect(
      within(canvasElement).getByRole("progressbar", { name: "모델을 부르는 중" }),
    ).toBeVisible();
  },
};

/** 마지막 이벤트 뒤 실행 제한 시간이 지나도 결말이 없다. 경고 알림이 서고 진행 표시는 없다. */
export const Stale: Story = {
  args: {
    stale: true,
    data: {
      turns: [FIRST, { ...SECOND, approvals: [], outcome: { kind: "running", step: "tool" } }],
      earlier: "start",
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("끝맺지 못한 것으로 보입니다")).toBeVisible();
    await expect(canvas.queryByRole("progressbar")).toBeNull();
    // 결말 없음 배지가 넓어 좁은 폭에서 한 줄에 모자라도 "자세히" 는 글자가 쪼개지지 않고 줄을 바꿔 내려간다. 줄바꿈은 글꼴
    // 폭에 달려 시험 환경의 글꼴로는 재현되지 않아, 그 일을 맡은 계산값을 본다(사진 정답은 Docker 의 글꼴로 찍는다).
    for (const button of canvas.getAllByRole("button", { name: "자세히" })) {
      await expect(getComputedStyle(button).whiteSpace).toBe("nowrap");
      const footer = button.parentElement;
      await expect(footer === null ? null : getComputedStyle(footer).flexWrap).toBe("wrap");
    }
  },
};

/** 거슬러 읽다 상한(100)에 닿았다. 맨 위에 정보 알림이 선다. */
export const EarlierCapped: Story = {
  args: { data: { turns: [SECOND], earlier: "cap" } },
  play: async ({ canvasElement }) => {
    await expect(
      within(canvasElement).getByText("더 앞의 대화는 이 화면에 보이지 않는다"),
    ).toBeVisible();
  },
};

/** 앞 실행을 읽지 못했다. 읽은 데까지 그리고 맨 위에 경고 알림이 선다. */
export const EarlierBroken: Story = {
  args: { data: { turns: [SECOND], earlier: "broken" } },
  play: async ({ canvasElement }) => {
    await expect(within(canvasElement).getByText("앞부분을 읽지 못했다")).toBeVisible();
  },
};

/** 패널이 보이는 실행의 이벤트. 짧게 시작과 끝만 둔다. */
const PANEL_TRACE: Trace = {
  run_id: SECOND.runId,
  schema_version: "3",
  events: [
    {
      type: "run_started",
      run_id: SECOND.runId,
      ts: "2026-11-15T07:04:02.311+00:00",
      agent: "support-bot",
      principal: "operator",
      request: SECOND.request,
      previous_run: FIRST.runId,
      requesting_account: "kim.dev",
      shortcuts: null,
    },
    {
      type: "run_finished",
      run_id: SECOND.runId,
      ts: "2026-11-15T07:05:15.100+00:00",
      output: SECOND_OUTPUT,
    },
  ],
};

/**
 * 둘째 실행의 패널이 열려 있다. 실제 화면처럼 대화 옆에 패널을 함께 그린다. 그 실행의 "자세히"가 눌린 모양이고
 * `aria-expanded` 가 참이며 `aria-controls` 가 가리키는 패널이 같은 화면에 있다. 넓은 폭에서는 오른쪽 480px 이고 좁은 폭에서는
 * 화면 전체를 덮는다.
 */
export const PanelOpen: Story = {
  args: { openRun: SECOND.runId },
  render: (args) => (
    <>
      <Conversation {...args} />
      <RunPanel
        runId={SECOND.runId}
        data={PANEL_TRACE}
        error={undefined}
        isValidating={false}
        onRefresh={fn()}
        onClose={fn()}
      />
    </>
  ),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const panel = canvas.getByRole("complementary", { name: "실행 패널" });
    await expect(panel).toBeVisible();
    const pressed = canvas.getAllByRole("button", { name: "자세히", hidden: true });
    await expect(pressed.map((button) => button.getAttribute("aria-expanded"))).toEqual([
      "false",
      "true",
    ]);
    await expect(pressed[1]?.getAttribute("aria-controls")).toBe(panel.id);
  },
};

/** 처음 불러오는 중. 아직 아무것도 그리지 못해 진행 표시 "대화를 불러오는 중"만 선다. */
export const Loading: Story = {
  args: { data: undefined, isValidating: true },
  play: async ({ canvasElement }) => {
    await expect(
      await within(canvasElement).findByRole("progressbar", { name: "대화를 불러오는 중" }),
    ).toBeVisible();
  },
};
