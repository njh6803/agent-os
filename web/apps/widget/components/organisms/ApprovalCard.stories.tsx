// 승인 묻기를 폭 320px 과 400px 에서 긴 인자와 함께 그린다(web-widget 티켓 08, 화면 디자인 mk-approval). 미리보기의
// afterEach 가 클래스를, addon-a11y 가 접근성을, 사진 비교(visual/)가 그림을 판정한다. 결정과 거절의 규칙은 화면 동작
// 테스트(pages/WidgetApproval.test)가 본다.
//
// 카드의 버튼 배치는 창의 폭으로 가른다(`@wide:`). 그래서 틀이 창처럼 컨테이너다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import { argsText } from "../../lib/approval";
import type { Approval, ApprovalState } from "../../lib/conversation";
import { ApprovalCard } from "./ApprovalCard";

/** 줄 끝에서 꺾을 자리가 없는 긴 값과 한글 문장, 겹친 객체가 든 인자. */
const LONG_ARGS = argsText({
  order_id: "ORD-2026-10-22-000184",
  amount: 18900,
  reason: "배송 지연",
  note: "예정일보다 하루 늦게 도착해 고객이 우산 값 전액을 돌려받기로 함",
  receipt:
    "https://shop.example/receipts/ORD-2026-10-22-000184?token=7f3a9c2e5b1d4f8a6c0e2b4d6f8a1c3e",
  notify: { channel: "email", template: "refund-completed-v2" },
});

const SHORT_ARGS = argsText({
  order_id: "ORD-2026-10-22-000184",
  amount: 18900,
  reason: "배송 지연",
});

function approval(state: ApprovalState, args = LONG_ARGS): Approval {
  return { pauseId: 7, tool: "payments.refund", args, after: 1, state };
}

const WAITING: ApprovalState = { kind: "waiting", sending: null, notice: null };

type ListProps = Omit<Parameters<typeof ApprovalCard>[0], "approval"> & {
  readonly approvals: readonly Approval[];
};

/** 카드를 대화 목록의 자리처럼 위에서 아래로 늘어놓는다. */
function CardList({ approvals, ...rest }: ListProps) {
  return (
    <ol className="flex flex-col gap-4 p-4">
      {approvals.map((item, index) => (
        <li key={index} className="flex flex-col gap-2">
          <ApprovalCard approval={item} {...rest} />
        </li>
      ))}
    </ol>
  );
}

const meta = {
  title: "organisms/ApprovalCard",
  component: CardList,
  args: {
    approvals: [approval(WAITING)],
    limit: 20_000,
    blocked: false,
    onDecide: fn(),
  },
  decorators: [
    (Story, { parameters }) => (
      <div
        className="@container bg-bg-raised text-text"
        style={{ width: parameters["width"] === 400 ? 400 : 320 }}
      >
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof CardList>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 카드 안의 요소가 카드보다 넓지 않다. 가로 스크롤 없이 다시 흐른다. */
async function fitsWithoutScroll(canvasElement: HTMLElement): Promise<void> {
  for (const pre of canvasElement.querySelectorAll("pre")) {
    await expect(pre.scrollWidth).toBeLessThanOrEqual(pre.clientWidth);
  }
  await expect(canvasElement.scrollWidth).toBeLessThanOrEqual(canvasElement.clientWidth);
}

/**
 * 가장 좁은 폭에서 결정을 기다린다. 긴 인자는 줄을 바꿔 흐르고, 사유가 비어 "거부"가 막혔으며, 창이 360px 미만이라
 * 버튼이 위아래로 꽉 찬다.
 */
export const Waiting: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await fitsWithoutScroll(canvasElement);
    const deny = canvas.getByRole("button", { name: "거부" });
    const approve = canvas.getByRole("button", { name: "승인" });
    await expect(deny).toBeDisabled();
    await expect(approve).toBeEnabled();
    // "거부"가 먼저이고 위에 선다. 둘의 폭이 같다.
    await expect(deny.getBoundingClientRect().bottom).toBeLessThanOrEqual(
      approve.getBoundingClientRect().top,
    );
    await expect(deny.getBoundingClientRect().width).toBe(approve.getBoundingClientRect().width);
  },
};

/** 기준 폭을 넘는 폭에서 결정을 기다린다. 버튼이 오른쪽에 나란히 선다. 다크 모드다. */
export const WaitingWideDark: Story = {
  parameters: { width: 400 },
  globals: { mode: "dark" },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await fitsWithoutScroll(canvasElement);
    const deny = canvas.getByRole("button", { name: "거부" });
    const approve = canvas.getByRole("button", { name: "승인" });
    await expect(deny.getBoundingClientRect().top).toBe(approve.getBoundingClientRect().top);
    await expect(deny.getBoundingClientRect().right).toBeLessThan(
      approve.getBoundingClientRect().left,
    );
  },
};

/** 결정을 보내는 중. 누른 "승인"이 불러오는 중이고 "거부"와 사유 칸은 막힌다. */
export const SendingWide: Story = {
  parameters: { width: 400 },
  args: {
    approvals: [approval({ kind: "waiting", sending: "approve", notice: null }, SHORT_ARGS)],
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "승인" })).toHaveAttribute("aria-busy", "true");
    await expect(canvas.getByRole("button", { name: "거부" })).toBeDisabled();
    await expect(canvas.getByRole("textbox", { name: "거부 사유" })).toBeDisabled();
  },
};

/** 결정의 상한을 기다리는 중. 두 버튼이 막힌다. */
export const Blocked: Story = {
  args: { approvals: [approval(WAITING, SHORT_ARGS)], blocked: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "승인" })).toBeDisabled();
    await expect(canvas.getByRole("button", { name: "거부" })).toBeDisabled();
  },
};

/** 결정한 뒤. 버튼과 사유 칸이 걷히고 한 줄이 남는다. 긴 사유도 다시 흐른다. */
export const Decided: Story = {
  args: {
    approvals: [
      approval({ kind: "approved" }, SHORT_ARGS),
      approval(
        {
          kind: "denied",
          reason:
            "고객센터에 먼저 물어보겠습니다. 영수증 주소 https://shop.example/receipts/ORD-2026-10-22-000184 를 확인해 주세요.",
        },
        SHORT_ARGS,
      ),
    ],
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await fitsWithoutScroll(canvasElement);
    await expect(canvas.queryAllByRole("button")).toHaveLength(0);
    await expect(canvas.getByText("승인했습니다")).toBeVisible();
    // 이미 결정된 채 그려진 카드는 포커스를 가져가지 않는다.
    await expect(canvasElement.contains(document.activeElement)).toBe(false);
  },
};

/** 결정의 거절. 다시 결정을 받는 카드 아래의 위험 알림 셋과, 더 받을 수 없게 된 카드 아래의 정보 알림이다. */
export const NoticesWide: Story = {
  parameters: { width: 400 },
  args: {
    approvals: [
      approval({ kind: "waiting", sending: null, notice: "unauthorized" }, SHORT_ARGS),
      approval({ kind: "waiting", sending: null, notice: "conflict" }, SHORT_ARGS),
      approval({ kind: "waiting", sending: null, notice: "error" }, SHORT_ARGS),
      approval({ kind: "expired" }, SHORT_ARGS),
    ],
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getAllByRole("alert")).toHaveLength(3);
    await expect(canvas.getByRole("status")).toHaveTextContent(
      "이 승인 묻기는 더 이상 받을 수 없습니다.",
    );
  },
};
