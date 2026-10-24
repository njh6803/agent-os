// 대화 목록을 폭 320px 과 400px 에서 그린다(web-widget 티켓 05, 화면 디자인 mk-conversation). 미리보기의 afterEach 가
// 클래스를, addon-a11y 가 접근성을, 사진 비교(visual/)가 그림을 판정한다. 스크롤은 jsdom 이 레이아웃을 하지 않아 화면
// 동작 테스트가 재지 못하므로 여기서 잰다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { expect, fn, waitFor, within } from "storybook/test";
import type { Exchange } from "../../lib/conversation";
import { Conversation } from "./Conversation";

const HEIGHT = 420;

function Sized({ width, children }: { readonly width: number; readonly children: ReactNode }) {
  return (
    <div className="flex flex-col bg-bg-raised text-text" style={{ width, height: HEIGHT }}>
      {children}
    </div>
  );
}

function exchange(id: number, request: string, rest: Partial<Exchange> = {}): Exchange {
  return {
    id,
    request,
    runId: `run_${String(id)}`,
    calling: [],
    tools: [],
    outcome: null,
    ...rest,
  };
}

const OUTPUT =
  "어제 주문하신 우산(주문 번호 ORD-2026-10-22-000184)은 오늘 오전 9시에 물류센터를 떠났습니다.\n지금은 배송 기사에게 넘어가 있고, 오늘 저녁 6시 전에 도착할 예정입니다.";

const FINISHED = exchange(0, "어제 주문한 우산 배송 어디쯤이에요?", {
  tools: [
    { tool: "orders.lookup", ok: true },
    { tool: "shipping.track", ok: false },
    { tool: "shipping.track", ok: true },
  ],
  outcome: { kind: "finished", output: OUTPUT },
});

const RUNNING = exchange(1, "늦으면 환불 받을 수 있어요?", {
  calling: ["refunds.policy"],
  tools: [{ tool: "orders.lookup", ok: true }],
});

const meta = {
  title: "organisms/Conversation",
  component: Conversation,
  args: {
    exchanges: [FINISHED, RUNNING],
    restarted: false,
    onRetry: fn(),
    retryBlocked: false,
    onNewConversation: fn(),
    newConversationBlocked: false,
  },
  decorators: [
    (Story, { parameters }) => (
      <Sized width={parameters["width"] === 400 ? 400 : 320}>
        <Story />
      </Sized>
    ),
  ],
} satisfies Meta<typeof Conversation>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 실행이 도는 동안. 끝난 교환은 접힌 도구 줄과 출력이고, 도는 교환은 끝난 도구 줄과 진행 표시다. */
export const Running: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(
      canvas.getByRole("progressbar", { name: "refunds.policy 부르는 중" }),
    ).toBeVisible();
    const summary = canvas.getByRole("button", { name: "도구 3개를 불렀습니다" });
    await expect(summary).toHaveAttribute("aria-expanded", "false");
    // 포인터 대상은 24px 이상이다.
    await expect(summary.getBoundingClientRect().height).toBeGreaterThanOrEqual(24);
  },
};

/**
 * 끝난 뒤. 기준 폭을 넘는 폭이다. play 가 접힌 줄을 눌러 펴는 것을 본다. 사진은 play 가 누르기 전의 접힌 모습이다
 * (`.claude/rules/web-design.md` 의 사진 절).
 */
export const Finished: Story = {
  parameters: { width: 400 },
  args: { exchanges: [FINISHED] },
  play: async ({ canvasElement, userEvent }) => {
    const canvas = within(canvasElement);
    const summary = canvas.getByRole("button", { name: "도구 3개를 불렀습니다" });
    await userEvent.click(summary);
    await expect(summary).toHaveAttribute("aria-expanded", "true");
    await expect(
      within(canvas.getByRole("list", { name: "부른 도구" })).getAllByRole("listitem"),
    ).toHaveLength(3);
  },
};

/** 출력은 글자 그대로이고 긴 낱말은 줄 끝에서 꺾인다. 상자를 넘지 않는다. */
export const LongWord: Story = {
  args: {
    exchanges: [
      exchange(0, "a".repeat(80), {
        outcome: { kind: "finished", output: `<b>굵게</b>\n${"ORD-".repeat(30)}` },
      }),
    ],
  },
  play: async ({ canvasElement }) => {
    const region = within(canvasElement).getByRole("region", { name: "대화" });
    await expect(region.scrollWidth).toBe(region.clientWidth);
    await expect(region.querySelector("b")).toBeNull();
  },
};

/**
 * 대화 안의 실패와 거절 알림(화면 디자인 mk-failure, mk-rejection). 출력이 올 자리에 서고, 요청 글은 대화에 남는다.
 * 다크 모드다. 알림마다의 문구는 organisms/FailureAlert 의 스토리가 늘어놓는다.
 */
export const Failures: Story = {
  parameters: { width: 400 },
  globals: { mode: "dark" },
  args: {
    exchanges: [
      exchange(0, "배송 어디쯤이에요?", {
        tools: [{ tool: "orders.lookup", ok: true }],
        outcome: { kind: "failed", cause: "timeout", runId: "run_01JA7Q8M2K" },
      }),
      exchange(1, "다시 물어볼게요", { runId: null, outcome: { kind: "error", offerNew: false } }),
      exchange(2, "한 번 더요", { runId: null, outcome: { kind: "unauthorized" } }),
    ],
  },
};

/**
 * 이어 갈 대화를 서버가 찾지 못해 새 대화로 다시 시작한 뒤(화면 디자인 mk-rejection 의 셋째). 맨 위에 정보 알림이 서고,
 * 같은 요청이 시작으로 돈다.
 */
export const Restarted: Story = {
  args: {
    restarted: true,
    exchanges: [exchange(3, "늦으면 환불 받을 수 있어요?", { calling: ["orders.lookup"] })],
  },
  play: async ({ canvasElement }) => {
    const notice = within(canvasElement).getByRole("status");
    await expect(notice).toHaveTextContent("이전 대화를 이어 갈 수 없어 새 대화로 시작합니다.");
  },
};

/** 메시지 하나가 대화를 하나 더 붙이게 하는 틀. 스크롤의 시험이 화면 밖에서 새 내용을 넣는다. */
function Growing({ start }: { readonly start: number }) {
  const [count, setCount] = useState(start);
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const element = root.current;
    const grow = () => {
      setCount((value) => value + 1);
    };
    element?.addEventListener("grow", grow);
    return () => {
      element?.removeEventListener("grow", grow);
    };
  }, []);
  const exchanges = Array.from({ length: count }, (_, index) =>
    exchange(index, `${String(index + 1)}번째 요청`, {
      outcome: { kind: "finished", output: `${String(index + 1)}번째 출력\n둘째 줄` },
    }),
  );
  return (
    <div ref={root} className="flex min-h-0 flex-1 flex-col">
      <Conversation
        exchanges={exchanges}
        restarted={false}
        onRetry={() => {}}
        retryBlocked={false}
        onNewConversation={() => {}}
        newConversationBlocked={false}
      />
    </div>
  );
}

function scrollerOf(canvasElement: HTMLElement): HTMLElement {
  return within(canvasElement).getByRole("region", { name: "대화" });
}

function atBottom(element: HTMLElement): boolean {
  return element.scrollHeight - element.scrollTop - element.clientHeight <= 2;
}

/**
 * 새 내용이 오면, 대화의 끝을 보고 있었을 때만 끝으로 내린다. 위로 올려 둔 동안에는 그 자리에 머문다. 사진을 찍지
 * 않는다(판정 스토리).
 */
export const Scroll: Story = {
  tags: ["judgment"],
  render: () => <Growing start={6} />,
  play: async ({ canvasElement }) => {
    const scroller = scrollerOf(canvasElement);
    const grow = () => scroller.parentElement?.dispatchEvent(new Event("grow"));
    await expect(scroller.scrollHeight).toBeGreaterThan(scroller.clientHeight);
    await expect(atBottom(scroller)).toBe(true);

    grow();
    await waitFor(() =>
      expect(within(canvasElement).getByText("7번째 출력", { exact: false })).toBeVisible(),
    );
    await expect(atBottom(scroller)).toBe(true);

    scroller.scrollTop = 0;
    scroller.dispatchEvent(new Event("scroll"));
    grow();
    await waitFor(() =>
      expect(within(canvasElement).getByText("8번째 출력", { exact: false })).toBeInTheDocument(),
    );
    await expect(scroller.scrollTop).toBe(0);
  },
};
