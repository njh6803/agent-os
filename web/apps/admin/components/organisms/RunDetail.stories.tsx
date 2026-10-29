// 실행 하나의 본문(admin-style 티켓 07, 화면 디자인 mk-run, mk-run-resumed, mk-run-m). 읽기 골격(RunDetail)과 그
// 본문(RunDecision)을 함께 그린다. 틀 없이 그리고, 미리보기의 데코레이터가 본문 칸과 같은 컨테이너를 두른다. 표본 값(실행
// 식별자, 에이전트, 주체 operator, 시각)은 그림의 것이다.
//
// 결정 칸의 위치는 play 가 본다. 넓은 폭(admin-storybook-wide)에서는 이벤트 칸의 오른쪽이고, 좁은 폭(admin-storybook-narrow)
// 에서는 이벤트 칸 아래, 재개 스트림 위다. 옆 칸이 스크롤해도 머무는 것(`sticky`)은 사진만 본다. 결정 칸 안의 모양은
// 티켓 08 이 다시 그린다. 결정과 재개 스트림의 행동은 페이지 시험(pages/RunPage.decision.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import type { StreamFrame } from "../../api/approval";
import type { Trace } from "../../api/traces";
import { RunDecision } from "./RunDecision";
import { RunDetail } from "./RunDetail";

const RUN = "7f3a2c91-4b8e-4d1a-9c2f-0e6b5a8d3f12";
const ARGS = { order_id: "A-1042", amount: 32000, reason: "damaged" };
const REQUEST = "주문 A-1042를 환불해 줘. 상품이 파손돼 도착했다.";

type Event = Trace["events"][number];

const STARTED: Event = {
  type: "run_started",
  run_id: RUN,
  ts: "2026-10-12T14:03:22.418Z",
  agent: "support-bot",
  request: REQUEST,
  principal: "operator",
  previous_run: null,
  shortcuts: null,
};
const CALLED: Event = {
  type: "llm_called",
  run_id: RUN,
  ts: "2026-10-12T14:03:24.902Z",
  model: "claude-sonnet-5-5",
  input_tokens: 812,
  output_tokens: 64,
  prompt: REQUEST,
  text: "",
  tool_calls: [{ id: "toolu_01", name: "payments.refund", args: ARGS }],
};
const PAUSED: Event = {
  type: "run_paused",
  run_id: RUN,
  ts: "2026-10-12T14:03:25.117Z",
  tool: "payments.refund",
  args: ARGS,
};
const GRANTED: Event = {
  type: "approval_granted",
  run_id: RUN,
  ts: "2026-10-12T14:07:41.006Z",
  approver: "ops",
};
const RESUMED: Event = { type: "run_resumed", run_id: RUN, ts: "2026-10-12T14:07:41.233Z" };
const TOOL: Event = {
  type: "tool_called",
  run_id: RUN,
  ts: "2026-10-12T14:07:42.871Z",
  tool: "payments.refund",
  ok: true,
  args: ARGS,
  content: '{"refund_id": "rf_8812", "status": "succeeded"}',
};
const FINISHED: Event = {
  type: "run_finished",
  run_id: RUN,
  ts: "2026-10-12T14:07:43.090Z",
  output: "주문 A-1042를 환불했다(rf_8812).",
};

const trace = (events: readonly Event[], schemaVersion: Trace["schema_version"] = "3"): Trace => ({
  run_id: RUN,
  schema_version: schemaVersion,
  events: [...events],
});

/** 재개 스트림의 이벤트 조각. 스트림의 이벤트는 트레이스의 모르는 종류를 갖지 않는다. */
function received(event: Event): StreamFrame {
  if (event.type === "unknown") {
    throw new Error("재개 스트림의 이벤트는 모르는 종류가 아니다");
  }
  return { kind: "event", event };
}

interface RunScreenProps {
  readonly trace: Trace;
  readonly channelTokenEntered: boolean;
  readonly busy: boolean;
  readonly frames: readonly StreamFrame[];
  readonly cut: boolean;
  readonly onRefresh: () => void;
  readonly onDecide: () => void;
}

/** 실행 하나의 본문. 트레이스를 읽었고 플러그인 목록은 모두 켜져 있다(꺼짐 미리 알림 없음). */
function RunScreen({ trace: shown, onRefresh, ...decision }: RunScreenProps) {
  return (
    <RunDetail
      runId={RUN}
      data={shown}
      error={undefined}
      isValidating={false}
      onRefresh={onRefresh}
      body={(read, events) => (
        <RunDecision
          trace={read}
          events={events}
          failure={null}
          plugins={{ data: [], error: undefined }}
          {...decision}
        />
      )}
    />
  );
}

const meta = {
  title: "organisms/RunDetail",
  component: RunScreen,
  args: {
    trace: trace([STARTED, CALLED, PAUSED]),
    channelTokenEntered: true,
    busy: false,
    frames: [],
    cut: false,
    onRefresh: fn(),
    onDecide: fn(),
  },
} satisfies Meta<typeof RunScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 문서 뿌리에 선언된 디자인 토큰의 값. */
function rootToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** 창이 화면 중단점 `wide` 이상인가. 스토리 테스트의 넓은 폭(1280)은 본문 칸도 `split` 이상이다. */
function isWide(): boolean {
  return window.matchMedia(`(min-width: ${rootToken("--breakpoint-wide")})`).matches;
}

function region(canvasElement: HTMLElement, name: string | RegExp): HTMLElement {
  return within(canvasElement).getByRole("region", { name });
}

/** 결정 칸. 결정 자리 구역을 품은 칸이다. */
function panelOf(canvasElement: HTMLElement): HTMLElement {
  const panel = region(canvasElement, "결정").parentElement;
  if (panel === null) {
    throw new Error("결정 칸이 없다");
  }
  return panel;
}

/** 이벤트 칸은 넓어도 최대 폭 `content`(880px)를 넘지 않는다. */
async function eventsWithinContent(canvasElement: HTMLElement): Promise<void> {
  await expect(
    region(canvasElement, /^이벤트 \d+$/).getBoundingClientRect().width,
  ).toBeLessThanOrEqual(880);
}

/** 끝난 실행. 결정 칸도 재개 스트림도 없고 이벤트 칸이 넓어진다. */
export const EventsOnly: Story = {
  args: { trace: trace([STARTED, CALLED, PAUSED, GRANTED, RESUMED, TOOL, FINISHED]) },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("heading", { level: 1, name: RUN })).toBeVisible();
    await expect(canvas.getByText("에이전트 support-bot")).toBeVisible();
    await expect(canvas.getByText("주체 operator")).toBeVisible();
    await expect(
      canvas.getByRole("heading", { level: 3, name: "run_started 2026-10-12T14:03:22.418Z" }),
    ).toBeVisible();
    await expect(canvas.queryByRole("region", { name: "결정" })).toBeNull();
    await expect(canvas.queryByRole("region", { name: "재개 스트림" })).toBeNull();
    await eventsWithinContent(canvasElement);
  },
};

/**
 * 결정 칸이 선 실행. 넓은 폭에서는 이벤트 칸의 오른쪽 옆 칸(360px)이고, 좁은 폭에서는 이벤트 칸 아래, 재개 스트림 위다.
 * 재개 스트림은 조각이 없어 빈 줄이다.
 */
export const DecisionPanel: Story = {
  play: async ({ canvasElement }) => {
    const events = region(canvasElement, /^이벤트 \d+$/).getBoundingClientRect();
    const panel = panelOf(canvasElement).getBoundingClientRect();
    const stream = region(canvasElement, "재개 스트림").getBoundingClientRect();
    if (isWide()) {
      await expect(panel.left).toBeGreaterThanOrEqual(events.right);
      await expect(panel.top).toBe(events.top);
      await expect(panel.width).toBe(360);
      await expect(stream.top).toBeGreaterThanOrEqual(events.bottom);
      await expect(stream.left).toBe(events.left);
    } else {
      await expect(panel.top).toBeGreaterThanOrEqual(events.bottom);
      await expect(stream.top).toBeGreaterThanOrEqual(panel.bottom);
      await expect(panel.left).toBe(events.left);
    }
    await expect(
      within(region(canvasElement, "재개 스트림")).getByText(
        "결정을 내면 재개한 이벤트가 여기에 차례로 붙는다.",
      ),
    ).toBeVisible();
    await eventsWithinContent(canvasElement);
  },
};

/** 결정 뒤 재개 스트림에 조각이 붙는 중. 받은 이벤트는 이벤트 칸과 같은 카드다. */
export const StreamFrames: Story = {
  args: { busy: true, frames: [received(GRANTED), received(RESUMED)] },
  play: async ({ canvasElement }) => {
    const stream = within(region(canvasElement, "재개 스트림"));
    await expect(stream.getAllByRole("heading", { level: 3 }).map((h) => h.textContent)).toEqual([
      "approval_granted 2026-10-12T14:07:41.006Z",
      "run_resumed 2026-10-12T14:07:41.233Z",
    ]);
  },
};

/** 읽지 못한 조각은 "읽지 못한 프레임"과 원문 카드다. */
export const UnreadableFrame: Story = {
  args: {
    busy: true,
    frames: [received(GRANTED), { kind: "raw", raw: '{"type":"run_exploded","run_id":"r-gated"}' }],
  },
  play: async ({ canvasElement }) => {
    const stream = within(region(canvasElement, "재개 스트림"));
    await expect(stream.getByRole("heading", { level: 3, name: "읽지 못한 프레임" })).toBeVisible();
    await expect(stream.getByText('{"type":"run_exploded","run_id":"r-gated"}')).toBeVisible();
  },
};

/**
 * 승인 뒤 재개 스트림이 결말 없이 끊겨 트레이스를 다시 읽었다. 정보 알림이 머리 바로 아래, 이벤트 칸 위에 서고, 결정할
 * 것이 없어 결정 칸이 걷힌다.
 */
export const StreamCut: Story = {
  args: { trace: trace([STARTED, CALLED, PAUSED, GRANTED, RESUMED, TOOL]), cut: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const title = canvas.getByText("재개 스트림이 끊겼다. 실행은 서버에서 계속된다");
    await expect(title).toBeVisible();
    const alert = title.closest('[role="status"]');
    if (alert === null) {
      throw new Error("끊긴 알림이 상태 영역이 아니다");
    }
    await expect(
      canvas.getByText("창을 닫거나 떠나도 실행은 끝까지 간다. 돌아오면 트레이스로 이어 본다."),
    ).toBeVisible();
    await expect(alert.getBoundingClientRect().bottom).toBeLessThanOrEqual(
      region(canvasElement, /^이벤트 \d+$/).getBoundingClientRect().top,
    );
    await expect(canvas.queryByRole("region", { name: "결정" })).toBeNull();
    await eventsWithinContent(canvasElement);
  },
};

/** 형식 1 트레이스. 머리 아래에 재개할 수 없다는 흐린 줄만 서고 멈춰 있어도 결정 칸이 없다. */
export const FormatOne: Story = {
  args: { trace: trace([STARTED, CALLED, PAUSED], "1") },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("형식 1 트레이스라 읽을 수 있지만 재개할 수 없다")).toBeVisible();
    await expect(canvas.queryByRole("region", { name: "결정" })).toBeNull();
    await expect(canvas.queryByRole("region", { name: "재개 스트림" })).toBeNull();
  },
};
