// 위젯의 첫 화면을 iframe 의 크기로 그린다. 폭은 지원하는 가장 좁은 320px 과 기준 폭(360px)을 넘는 400px 이고, 높이는
// 화면 디자인의 예시 560px 이다(web-widget 명세 "임베드"의 크기). 미리보기의 afterEach 가 클래스를, addon-a11y 가
// 접근성을, 사진 비교(visual/)가 그림을 판정한다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import type { ReactNode } from "react";
import { expect, fn, within } from "storybook/test";
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
    announcements: [],
    sendBlocked: false,
    paused: false,
    newConversationDisabled: false,
    draft: "",
    onDraftChange: fn(),
    onSend: fn(),
    onRetry: fn(),
    onNewConversation: fn(),
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

/** 글자 수 상한을 넘음(화면 디자인 mk-limit 의 여섯째). 넘었다는 글을 위험 색으로 보이고 보내기가 막힌다. */
export const OverLimit: Story = {
  parameters: { width: 400 },
  args: { draft: `${NEAR}${"가".repeat(151)}` },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("20,000자를 넘었습니다")).toBeVisible();
    await expect(canvas.getByRole("button", { name: "보내기" })).toBeDisabled();
  },
};
