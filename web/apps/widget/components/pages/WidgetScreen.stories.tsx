// 위젯의 첫 화면을 iframe 의 크기로 그린다. 폭은 지원하는 가장 좁은 320px 과 기준 폭(360px)을 넘는 400px 이고, 높이는
// 화면 디자인의 예시 560px 이다(web-widget 명세 "임베드"의 크기). 미리보기의 afterEach 가 클래스를, addon-a11y 가
// 접근성을, 사진 비교(visual/)가 그림을 판정한다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import type { ReactNode } from "react";
import { expect, fn, within } from "storybook/test";
import type { Exchange } from "../../lib/conversation";
import { WidgetScreen } from "./WidgetScreen";

const HEIGHT = 560;

function Sized({ width, children }: { readonly width: number; readonly children: ReactNode }) {
  return <div style={{ width, height: HEIGHT }}>{children}</div>;
}

const meta = {
  title: "pages/WidgetScreen",
  component: WidgetScreen,
  args: {
    heading: "주문 도우미",
    intro: "주문, 배송, 환불을 물어볼 수 있습니다.",
    misconfigured: false,
    exchanges: [],
    restarted: false,
    wait: null,
    invalid: false,
    announcements: [],
    sendBlocked: false,
    paused: false,
    newConversationDisabled: false,
    draft: "",
    onDraftChange: fn(),
    onSend: fn(),
    onRetry: fn(),
    onNewConversation: fn(),
    onDecide: fn(),
    requestChars: 20_000,
  },
  decorators: [
    (Story, { parameters }) => (
      <Sized width={parameters["width"] === 400 ? 400 : 320}>
        <Story />
      </Sized>
    ),
  ],
} satisfies Meta<typeof WidgetScreen>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 가장 좁은 폭의 첫 화면. 위젯의 CSS 가 Storybook 에서 서는지도 본다. 위쪽 띠의 이름을 줄이는 `truncate` 는 디자인
 * 시스템 패키지의 소스에 없는 클래스라, 위젯의 CSS 가 `@source` 로 위젯 소스를 덮지 않으면 규칙이 생기지 않는다.
 */
export const Narrow: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const heading = canvas.getByRole("heading", { name: "주문 도우미" });
    await expect(getComputedStyle(heading).textOverflow).toBe("ellipsis");
    // 창이 자리를 채운다.
    const frame = canvas.getByRole("main").parentElement;
    await expect(frame?.getBoundingClientRect().width).toBe(320);
    await expect(frame?.getBoundingClientRect().height).toBe(HEIGHT);
  },
};

/** 기준 폭을 넘는 폭의 첫 화면. */
export const Wide: Story = {
  parameters: { width: 400 },
};

/** 할 수 있는 일을 주지 않은 첫 화면. 안내 한 줄만 선다. */
export const WithoutIntro: Story = {
  args: { heading: "order-helper", intro: null },
};

/** 설정이 잘못된 첫 화면. 대화 자리에 위험 알림이 서고 입력 자리가 막힌다. */
export const Misconfigured: Story = {
  args: { heading: "", intro: null, misconfigured: true },
};

/**
 * 다크 모드의 첫 화면. 기준 폭을 넘는 폭으로 그린다. 스토리 테스트는 모드를 정하지 않은 스토리를 시스템 모드(헤드리스
 * chromium 에서는 라이트)로만 돌아, 다크의 대비는 이 스토리의 axe 가 본다. 사진은 `Wide` 의 다크 사진과 같다.
 */
export const WideDark: Story = {
  parameters: { width: 400 },
  globals: { mode: "dark" },
};

/**
 * 실행이 도는 동안의 화면(화면 디자인 mk-conversation 의 둘째). 보내기와 새 대화가 막힌다. 막힌 새 대화는 포커스를
 * 받지 않는다.
 */
export const Conversing: Story = {
  args: {
    exchanges: [
      {
        id: 0,
        request: "늦으면 환불 받을 수 있어요?",
        runId: "run_0",
        calling: ["refunds.policy"],
        tools: [{ tool: "orders.lookup", ok: true }],
        approvals: [],
        outcome: null,
      },
    ],
    sendBlocked: true,
    newConversationDisabled: true,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "보내기" })).toBeDisabled();
    await expect(canvas.getByRole("button", { name: "새 대화" })).toBeDisabled();
    await expect(
      canvas.getByRole("progressbar", { name: "refunds.policy 부르는 중" }),
    ).toBeVisible();
  },
};

const PAUSED_EXCHANGE: Exchange = {
  id: 0,
  request: "배송이 늦었으니 우산 값 환불해 주세요.",
  runId: "run_0",
  calling: ["payments.refund"],
  tools: [{ tool: "orders.lookup", ok: true }],
  approvals: [
    {
      pauseId: 3,
      tool: "payments.refund",
      args: JSON.stringify(
        { order_id: "ORD-2026-10-22-000184", amount: 18900, reason: "배송 지연" },
        null,
        2,
      ),
      after: 1,
      state: { kind: "waiting", sending: null, notice: null },
    },
  ],
  outcome: { kind: "paused" },
};

/**
 * 승인 묻기가 결정을 기다리는 화면(화면 디자인 mk-approval 의 첫째). 입력창과 보내기가 막히고 그 위 띠가 먼저 고르라고
 * 하며, 새 대화는 열려 있다. 입력창에는 글을 넣지 않는다(위 RETURNED_NARROW 의 주석).
 */
export const Paused: Story = {
  args: {
    exchanges: [PAUSED_EXCHANGE],
    paused: true,
    sendBlocked: true,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("group", { name: "승인 묻기" })).toBeVisible();
    await expect(canvas.getByRole("textbox", { name: "요청" })).toBeDisabled();
    await expect(canvas.getByRole("button", { name: "보내기" })).toBeDisabled();
    await expect(canvas.getByRole("button", { name: "새 대화" })).toBeEnabled();
    await expect(canvas.getByText("승인이나 거부를 먼저 골라 주세요.")).toBeVisible();
    // 포커스는 카드의 제목으로 가지만 대화를 굴리지 않아, 대화는 끝(카드의 버튼)을 보고 있다.
    await expect(document.activeElement?.textContent).toBe("승인이 필요합니다");
    const region = canvas.getByRole("region", { name: "대화" });
    await expect(region.scrollHeight).toBeGreaterThan(region.clientHeight);
    await expect(region.scrollHeight - region.scrollTop - region.clientHeight).toBeLessThanOrEqual(
      2,
    );
  },
};

/** 기준 폭을 넘는 폭에서 결정의 상한을 기다리는 화면. 띠가 "다시 고를 수 있습니다"로 끝맺고 결정 버튼이 막힌다. */
export const PausedLimitedWide: Story = {
  parameters: { width: 400 },
  args: {
    exchanges: [PAUSED_EXCHANGE],
    paused: true,
    sendBlocked: true,
    wait: { purpose: "decide", limit: "concurrent_runs", seconds: 5, until: 0, remaining: 5 },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "승인" })).toBeDisabled();
    await expect(canvas.getByText(/다시 고를 수 있습니다\.$/)).toBeVisible();
  },
};

const NEAR = "가".repeat(19_850);

/**
 * 글자 수 상한 근처(화면 디자인 mk-limit 의 다섯째). 입력창 아래에 센 수가 서고, 보내기는 입력창의 아래 끝에 맞춘
 * 그대로 그 글만큼 올라간다.
 */
export const NearLimit: Story = {
  args: { draft: NEAR },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const box = canvas.getByRole("textbox", { name: "요청" });
    await expect(canvas.getByText("19,850 / 20,000")).toBeVisible();
    const send = canvas.getByRole("button", { name: "보내기" });
    await expect(send).toBeEnabled();
    await expect(Math.round(send.getBoundingClientRect().bottom)).toBe(
      Math.round(box.getBoundingClientRect().bottom),
    );
  },
};

const RETURNED = "내일 오후까지 안 오면 환불도 되나요?";

// 폭 320px 에서 한 줄에 드는 요청이다. 입력창을 넘치는 글(RETURNED)이면 레이아웃은 같은데도 옆의 보내기 버튼
// 가장자리 픽셀이 찍을 때마다 색 값 1씩 갈려 사진 비교가 흔들렸다(손으로 봤다, 일지 2026-10-24-15 의 "사진
// 비교의 흔들림"). 가장 좁은 폭의 스토리는 이 글을 넣는다.
const RETURNED_NARROW = "환불도 되나요?";

const FINISHED_EXCHANGE: Exchange = {
  id: 0,
  request: "어제 주문한 우산 배송 어디쯤이에요?",
  runId: "run_0",
  calling: [],
  tools: [{ tool: "shipping.track", ok: true }],
  approvals: [],
  outcome: { kind: "finished", output: "오늘 저녁 6시 전에 도착할 예정입니다." },
};

/**
 * 상한에 걸려 기다리는 중(화면 디자인 mk-limit 의 첫째). 요청이 입력창으로 돌아오고, 입력창 위 띠가 상한의 문구와 남은
 * 시간을 보이며 보내기가 막힌다. 화면 읽기 프로그램은 숨긴 사본의 처음 시간(5초)을 읽는다.
 */
export const Limited: Story = {
  args: {
    exchanges: [FINISHED_EXCHANGE],
    draft: RETURNED_NARROW,
    wait: { purpose: "send", limit: "concurrent_runs", seconds: 5, until: 0, remaining: 3 },
    sendBlocked: true,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const band = canvas.getAllByRole("status").at(-1);
    await expect(band).toHaveTextContent("동시에 처리할 수 있는 요청이 가득 찼습니다.");
    await expect(band?.querySelector("[aria-hidden='true']:not(svg)")).toHaveTextContent("3초");
    await expect(canvas.getByRole("button", { name: "보내기" })).toBeDisabled();
  },
};

/** 시간당 상한에 걸려 분으로 적은 기다림. 기준 폭을 넘는 폭이고 다크 모드다. */
export const LimitedHourlyWideDark: Story = {
  parameters: { width: 400 },
  globals: { mode: "dark" },
  args: {
    exchanges: [FINISHED_EXCHANGE],
    draft: RETURNED,
    wait: { purpose: "send", limit: "hourly_runs", seconds: 720, until: 0, remaining: 720 },
    sendBlocked: true,
  },
};

/** 시간이 다 된 뒤. 띠는 다음에 보낼 때까지 남고 보내기가 열린다. */
export const LimitReady: Story = {
  parameters: { width: 400 },
  args: {
    exchanges: [FINISHED_EXCHANGE],
    draft: RETURNED,
    wait: { purpose: "send", limit: "concurrent_runs", seconds: 5, until: 0, remaining: 0 },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getAllByRole("status").at(-1)).toHaveTextContent(
      "이제 다시 보낼 수 있습니다.",
    );
    await expect(canvas.getByRole("button", { name: "보내기" })).toBeEnabled();
  },
};

/**
 * 422 로 돌아온 요청. 입력창 아래에 고쳐 보내라는 글이 서고, 그 글이 가장 좁은 폭에서 두 줄로 꺾여도 보내기는 입력창의
 * 아래 끝에 맞는다.
 */
export const Invalid: Story = {
  args: { exchanges: [FINISHED_EXCHANGE], draft: RETURNED_NARROW, invalid: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const box = canvas.getByRole("textbox", { name: "요청" });
    await expect(box).toHaveAccessibleDescription(
      "요청을 보낼 수 없습니다. 요청을 고쳐 다시 보내 주세요.",
    );
    const send = canvas.getByRole("button", { name: "보내기" });
    await expect(send).toBeEnabled();
    await expect(Math.round(send.getBoundingClientRect().bottom)).toBe(
      Math.round(box.getBoundingClientRect().bottom),
    );
  },
};

/**
 * 앞 교환의 실패 알림과 상한의 띠가 같이 선 화면. 알림은 `role="alert"`(곧바로 읽힌다)이고 띠는 `role="status"`(하던
 * 말을 마친 뒤 읽힌다)라 알림이 먼저 읽힌다. 기다리는 동안 알림의 "다시 보내기"도 막힌다.
 */
export const FailureWithLimit: Story = {
  parameters: { width: 400 },
  args: {
    exchanges: [
      {
        id: 0,
        request: "어제 주문한 우산 배송 어디쯤이에요?",
        runId: null,
        calling: [],
        tools: [],
        approvals: [],
        outcome: { kind: "error", offerNew: false },
      },
    ],
    draft: RETURNED,
    wait: { purpose: "send", limit: "concurrent_runs", seconds: 5, until: 0, remaining: 5 },
    sendBlocked: true,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const alert = canvas.getByRole("alert");
    await expect(alert).toHaveTextContent("요청을 처리하지 못했습니다.");
    await expect(within(alert).getByRole("button", { name: "다시 보내기" })).toBeDisabled();
    await expect(canvas.getAllByRole("status").at(-1)).toHaveTextContent(
      "5초 뒤에 다시 보낼 수 있습니다.",
    );
  },
};

/**
 * 글자 수 상한을 넘음(화면 디자인 mk-limit 의 여섯째). 넘었다는 글을 위험 색으로 보이고 보내기가 막힌다.
 * 상한을 20자로 작게 준다. 2만 자를 넣어 입력창이 넘치던 판은 사진 비교가 실행마다 보내기 버튼 둥근 모서리의
 * 픽셀 몇 개를 한 단계씩 다르게 그려 흔들렸다(일지 2026-10-24-09).
 */
export const OverLimit: Story = {
  parameters: { width: 400 },
  args: { draft: "가".repeat(21), requestChars: 20 },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("20자를 넘었습니다")).toBeVisible();
    await expect(canvas.getByRole("button", { name: "보내기" })).toBeDisabled();
  },
};
