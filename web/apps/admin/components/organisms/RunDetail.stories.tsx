// 실행 하나의 본문(admin-style 티켓 07·08, 화면 디자인 mk-run, mk-run-resumed, mk-run-m, mk-decision). 읽기 골격
// (RunDetail)과 그 본문(RunDecision)을 함께 그린다. 틀 없이 그리고, 미리보기의 데코레이터가 본문 칸과 같은 컨테이너를
// 두른다. 표본 값(실행 식별자, 에이전트, 주체 operator, 시각, 도구와 인자)은 그림의 것이다.
//
// 결정 칸의 위치는 play 가 본다. 넓은 폭(admin-storybook-wide)에서는 이벤트 칸의 오른쪽이고, 좁은 폭(admin-storybook-narrow)
// 에서는 이벤트 칸 아래, 재개 스트림 위다. 옆 칸이 스크롤해도 머무는 것(`sticky`)은 사진만 본다. 결정 칸의 버튼도
// 위치로 본다. 넓은 폭의 옆 칸(360px)에서는 "거부" 다음 "승인"이 오른쪽에 나란히, 좁은 폭의 칸(288px)에서는 둘이 위아래로
// 칸을 꽉 채운다. 결정 칸의 변형은 그림 mk-decision 의 다섯 가운데 형식 1 을 뺀 넷(형식 1 은 아래 FormatOne)과 그림에
// 없는 셋(꺼진 플러그인을 미리 알 수 없음, 결정을 보내지 못한 알림, 422)이다. 결정과 재개 스트림의 행동은 페이지
// 시험(pages/RunPage.decision.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import type { StreamFrame } from "../../api/approval";
import { failureOf, type RequestFailure } from "../../api/failure";
import type { PluginRow } from "../../api/plugins";
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

/** 실행 에이전트의 행. 매니페스트가 MCP 하나를 쓴다. */
const AGENT_ROW: PluginRow = {
  kind: "agent",
  name: "support-bot",
  enabled: true,
  manifest: {
    schema_version: "1",
    kind: "agent",
    name: "support-bot",
    version: "0.1.0",
    entrypoint: "agent:SupportBot",
    mcp: ["filesystem"],
    requires_approval: ["payments.refund"],
    conversation_limit: null,
    server: null,
  },
};
const MCP_ROW: PluginRow = {
  kind: "mcp",
  name: "filesystem",
  enabled: true,
  manifest: {
    schema_version: "1",
    kind: "mcp",
    name: "filesystem",
    version: "0.1.0",
    entrypoint: null,
    mcp: [],
    requires_approval: [],
    conversation_limit: null,
    server: { command: "python", args: ["filesystem.py"], secret_args: {} },
  },
};

interface RunScreenProps {
  readonly trace: Trace;
  readonly channelTokenEntered: boolean;
  readonly busy: boolean;
  readonly frames: readonly StreamFrame[];
  readonly cut: boolean;
  readonly failure: RequestFailure | null;
  readonly plugins: { readonly data: readonly PluginRow[] | undefined; readonly error: unknown };
  readonly onRefresh: () => void;
  readonly onDecide: () => void;
}

/** 실행 하나의 본문. 트레이스를 읽었다. 기본은 플러그인 목록이 모두 켜져 있다(꺼짐 미리 알림 없음). */
function RunScreen({ trace: shown, onRefresh, ...decision }: RunScreenProps) {
  return (
    <RunDetail
      runId={RUN}
      data={shown}
      error={undefined}
      isValidating={false}
      onRefresh={onRefresh}
      body={(read, events) => <RunDecision trace={read} events={events} {...decision} />}
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
    failure: null,
    plugins: { data: [AGENT_ROW, MCP_ROW], error: undefined },
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
    await buttonsByWidth(canvasElement);
  },
};

/**
 * 결정 자리의 버튼 둘. "거부" 다음 "승인"이다. 넓은 폭의 옆 칸(360px)에서는 한 줄에 나란히 오른쪽 끝으로 모이고, 좁은
 * 폭의 칸(288px)에서는 둘이 위아래로 서서 칸(카드의 안쪽)을 꽉 채운다.
 */
async function buttonsByWidth(canvasElement: HTMLElement): Promise<void> {
  const place = region(canvasElement, "결정");
  const buttons = within(place).getAllByRole("button");
  await expect(buttons.map((found) => found.textContent)).toEqual(["거부", "승인"]);
  const [deny, approve] = buttons.map((found) => found.getBoundingClientRect());
  if (deny === undefined || approve === undefined) {
    throw new Error("결정 버튼이 둘이 아니다");
  }
  const form = place.querySelector("form");
  if (form === null) {
    throw new Error("결정 폼이 없다");
  }
  const row = form.getBoundingClientRect();
  // 버튼 줄은 뷰포트가 아니라 결정 칸의 폭으로 갈린다. 두 폭에서는 본문 칸으로 갈려도 같은 그림이라 선언을 본다.
  await expect(getComputedStyle(panelOf(canvasElement)).containerType).toBe("inline-size");
  if (isWide()) {
    await expect(approve.top).toBe(deny.top);
    await expect(approve.left).toBeGreaterThan(deny.right);
    await expect(approve.right).toBe(row.right);
    await expect(deny.left).toBeGreaterThan(row.left);
  } else {
    await expect(approve.top).toBeGreaterThan(deny.bottom);
    for (const box of [deny, approve]) {
      await expect(box.left).toBe(row.left);
      await expect(box.right).toBe(row.right);
    }
  }
}

/** 결정 칸. 결정 자리가 없을 때는 그 글을 품은 칸이다. */
function columnHolding(canvasElement: HTMLElement, text: string): HTMLElement {
  const found = within(canvasElement).getByText(text).closest(".\\@container");
  if (!(found instanceof HTMLElement)) {
    throw new Error(`결정 칸이 없다: ${text}`);
  }
  return found;
}

/** 꺼진 플러그인으로 막힌 결정 자리. 경고가 머리 설명 아래에 서고 사유 칸과 버튼 둘이 막힌다. */
export const DisabledPlugins: Story = {
  args: {
    plugins: {
      data: [
        { ...AGENT_ROW, enabled: false },
        { ...MCP_ROW, enabled: false },
      ],
      error: undefined,
    },
  },
  play: async ({ canvasElement }) => {
    const place = within(region(canvasElement, "결정"));
    const warning = place
      .getByText("꺼진 플러그인이 있어 재개할 수 없다: 에이전트 support-bot, MCP filesystem")
      .closest('[role="status"]');
    if (!(warning instanceof HTMLElement)) {
      throw new Error("꺼짐 경고가 상태 영역이 아니다");
    }
    await expect(within(warning).getByText(/다시 켜면 결정을 낼 수 있다/)).toBeVisible();
    await expect(within(warning).getByRole("link", { name: "플러그인 목록" })).toBeVisible();
    await expect(place.getByRole("textbox", { name: "거부 사유" })).toBeDisabled();
    await expect(place.getByRole("button", { name: "거부" })).toBeDisabled();
    await expect(place.getByRole("button", { name: "승인" })).toBeDisabled();
  },
};

/** 플러그인 목록을 읽지 못해 꺼진 플러그인을 미리 알 수 없다. 정보 알림이 서고 결정은 막지 않는다. */
export const PluginsUnknown: Story = {
  args: { plugins: { data: undefined, error: new Error("플러그인 목록을 읽지 못했다") } },
  play: async ({ canvasElement }) => {
    const place = within(region(canvasElement, "결정"));
    await expect(
      place.getByText("플러그인 목록을 읽지 못해 꺼진 플러그인을 미리 알 수 없다"),
    ).toBeVisible();
    await expect(place.getByRole("button", { name: "승인" })).toBeEnabled();
  },
};

/** 최종 사용자의 실행. 결정 자리 대신 한 줄만 서고, 채널 토큰이 없어도 같다. 재개 스트림은 서지 않는다. */
export const EndUserRun: Story = {
  args: {
    trace: trace([{ ...STARTED, principal: "https://shop.example|user-42" }, CALLED, PAUSED]),
    channelTokenEntered: false,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const line = "최종 사용자의 실행이라 결정은 그 사람만 낸다";
    await expect(canvas.getByText(line)).toBeVisible();
    await expect(canvas.queryByRole("region", { name: "결정" })).toBeNull();
    await expect(canvas.queryByRole("region", { name: "재개 스트림" })).toBeNull();
    await columnBesideOrBelowEvents(canvasElement, columnHolding(canvasElement, line));
  },
};

/** 운영자의 실행인데 채널 토큰이 없다. 결정 자리 대신 설정에서 넣으라는 한 줄과 "설정 열기"가 선다. */
export const NoChannelToken: Story = {
  args: { channelTokenEntered: false },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const line = "결정을 내리려면 설정에서 채널 토큰을 넣는다";
    await expect(canvas.getByText(line)).toBeVisible();
    await expect(canvas.getByRole("link", { name: "설정 열기" })).toBeVisible();
    await expect(canvas.queryByRole("region", { name: "결정" })).toBeNull();
    await columnBesideOrBelowEvents(canvasElement, columnHolding(canvasElement, line));
  },
};

/** 결정 칸이 넓은 폭에서는 이벤트 칸의 오른쪽 옆 칸이고, 좁은 폭에서는 이벤트 칸 아래다. */
async function columnBesideOrBelowEvents(
  canvasElement: HTMLElement,
  column: HTMLElement,
): Promise<void> {
  const events = region(canvasElement, /^이벤트 \d+$/).getBoundingClientRect();
  const box = column.getBoundingClientRect();
  if (isWide()) {
    await expect(box.left).toBeGreaterThanOrEqual(events.right);
    await expect(box.width).toBe(360);
  } else {
    await expect(box.top).toBeGreaterThanOrEqual(events.bottom);
  }
}

/**
 * 결정을 보내지 못했다(409). 알림이 머리 바로 아래, 이벤트 칸 위에 서고 결정 자리 밖이다. 화면은 트레이스를 다시
 * 읽어 지금의 일시정지를 보인다.
 */
export const DecisionFailed: Story = {
  args: {
    failure: failureOf(409, {
      code: "conflict",
      message: "결정이 가리킨 자리 2 는 지금의 일시정지(자리 6)가 아니다",
      request_id: "req-7c41e2",
      violations: [],
    }),
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const alert = canvas.getByRole("alert");
    await expect(within(alert).getByText("결정을 보내지 못했다")).toBeVisible();
    await expect(within(alert).getByText("req-7c41e2")).toBeVisible();
    await expect(alert.getBoundingClientRect().bottom).toBeLessThanOrEqual(
      region(canvasElement, /^이벤트 \d+$/).getBoundingClientRect().top,
    );
    await expect(region(canvasElement, "결정").contains(alert)).toBe(false);
  },
};

/**
 * 결정 본문의 형식 오류(422). 사유 칸 바로 아래의 알림이 메시지, 추적 식별자, 위반을 모두 담고, 사유에 걸린 위반은
 * 사유 칸이 오류로 그린다. 이 스토리는 넣은 사유를 그리지 않아 사유 칸이 비어 있다.
 */
export const DecisionInvalid: Story = {
  args: {
    failure: failureOf(422, {
      code: "invalid_request",
      message: "요청의 형식이 올바르지 않다",
      request_id: "req-4220",
      violations: [{ field: "body.deny.reason", message: "사유는 비어 있을 수 없다" }],
    }),
  },
  play: async ({ canvasElement }) => {
    const place = within(region(canvasElement, "결정"));
    const alert = place.getByRole("alert");
    await expect(within(alert).getByText("결정을 보내지 못했다")).toBeVisible();
    await expect(within(alert).getByText("body.deny.reason")).toBeVisible();
    await expect(
      place.getByRole("textbox", { name: "거부 사유", description: "사유는 비어 있을 수 없다" }),
    ).toHaveAttribute("aria-invalid", "true");
    await expect(within(canvasElement).queryAllByRole("alert")).toHaveLength(1);
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
