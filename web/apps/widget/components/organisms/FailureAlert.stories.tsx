// 실패 알림을 폭 320px 과 400px 에서 그린다(web-widget 티켓 07·09, 화면 디자인 mk-failure, mk-rejection). 원인마다의
// 알림과 거절의 알림(다시 잇기를 멈춘 것 포함)을 늘어놓는다. 미리보기의 afterEach 가 클래스를, addon-a11y 가 접근성을, 사진 비교(visual/)가
// 그림을 판정한다. 문구와 버튼의 규칙은 화면 동작 테스트(pages/WidgetFailures.test)가 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import type { Outcome } from "../../lib/conversation";
import { FailureAlert, type FailureAlertProps } from "./FailureAlert";

const RUN = "run_01JA7Q8M2K";

const CAUSES: readonly Outcome[] = [
  { kind: "failed", cause: "conversation_summary", runId: RUN },
  { kind: "failed", cause: "timeout", runId: RUN },
  { kind: "failed", cause: "tool_connection", runId: RUN },
  { kind: "failed", cause: "model_call", runId: RUN },
  { kind: "failed", cause: "tool_failure", runId: RUN },
  { kind: "failed", cause: "loop_limit", runId: RUN },
  { kind: "failed", cause: "resume_mismatch", runId: RUN },
  { kind: "failed", cause: "agent_code", runId: RUN },
  { kind: "failed", cause: "other", runId: RUN },
];

const REJECTIONS: readonly Outcome[] = [
  { kind: "unfinished", runId: RUN },
  { kind: "unauthorized" },
  { kind: "not-found" },
  { kind: "unavailable" },
  { kind: "error", offerNew: false },
  { kind: "error", offerNew: true },
  { kind: "lost" },
];

type ListProps = Omit<FailureAlertProps, "outcome"> & { readonly outcomes: readonly Outcome[] };

/** 알림을 대화 목록의 자리처럼 위에서 아래로 늘어놓는다. */
function AlertList({ outcomes, ...rest }: ListProps) {
  return (
    <ol className="flex flex-col gap-4 p-4">
      {outcomes.map((outcome, index) => (
        <li key={index}>
          <FailureAlert outcome={outcome} {...rest} />
        </li>
      ))}
    </ol>
  );
}

const meta = {
  title: "organisms/FailureAlert",
  component: AlertList,
  args: {
    outcomes: CAUSES,
    onRetry: fn(),
    retryBlocked: false,
    onNewConversation: fn(),
    newConversationBlocked: false,
  },
  decorators: [
    (Story, { parameters }) => (
      <div
        className="bg-bg-raised text-text"
        style={{ width: parameters["width"] === 400 ? 400 : 320 }}
      >
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof AlertList>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 실패 원인마다의 알림. 가장 좁은 폭이다. */
export const Causes: Story = {
  play: async ({ canvasElement }) => {
    const alerts = within(canvasElement).getAllByRole("alert");
    await expect(alerts).toHaveLength(CAUSES.length);
    // 단계 상한은 버튼 없이 입력창으로 포커스를 보낸다.
    const loopLimit = alerts.find((alert) => alert.textContent.includes("정해진 단계"));
    await expect(loopLimit).toBeDefined();
    await expect(loopLimit?.querySelectorAll("button")).toHaveLength(0);
  },
};

/** 기준 폭을 넘는 폭의 실패 원인 알림. 다크 모드다. */
export const CausesWideDark: Story = {
  parameters: { width: 400 },
  globals: { mode: "dark" },
};

/** 끝내지 못함과 거절의 알림. 실행이 서지 않은 거절에는 실행 식별자가 없다. */
export const Rejections: Story = {
  args: { outcomes: REJECTIONS },
  play: async ({ canvasElement }) => {
    const alerts = within(canvasElement).getAllByRole("alert");
    await expect(alerts).toHaveLength(REJECTIONS.length);
    await expect(alerts.filter((alert) => alert.textContent.includes("실행 식별자"))).toHaveLength(
      1,
    );
  },
};

/** 기준 폭을 넘는 폭의 거절 알림. 보낼 수 없는 동안이라 버튼이 막혀 있다. */
export const RejectionsWideBlocked: Story = {
  parameters: { width: 400 },
  args: { outcomes: REJECTIONS, retryBlocked: true, newConversationBlocked: true },
  play: async ({ canvasElement }) => {
    for (const button of within(canvasElement).getAllByRole("button")) {
      await expect(button).toBeDisabled();
    }
  },
};
