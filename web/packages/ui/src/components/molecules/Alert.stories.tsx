import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import { Button } from "../atoms/Button";
import type { IconName } from "../atoms/Icon";
import {
  TRANSPARENT,
  colorsOf,
  expectedFocusRing,
  focusRingOf,
  iconShape,
  semanticColor,
} from "../../storybook/expect";
import { Alert, type AlertTone } from "./Alert";

const meta = {
  title: "molecules/Alert",
  component: Alert,
  args: {
    title: "실행이 실패했습니다",
    children: "payments.refund가 30초 안에 끝나지 않았습니다.",
  },
} satisfies Meta<typeof Alert>;

export default meta;
type Story = StoryObj<typeof meta>;

const ACTIONS = (
  <>
    <Button variant="secondary" size="s">
      다시 실행
    </Button>
    <a href="#runs" className="text-small text-text underline">
      실행 보기
    </a>
  </>
);

/** 알림의 톤이 칠한 것. 바탕, 아이콘(모양과 색), 제목과 본문의 글자색이다. */
async function expectTone(
  alert: HTMLElement,
  tone: AlertTone,
  icon: IconName,
  title: string,
  body: string,
): Promise<void> {
  const svg = alert.querySelector("svg");
  const scope = within(alert);
  await expect({
    background: colorsOf(alert).background,
    icon: svg === null ? null : getComputedStyle(svg).color,
    shape: svg?.innerHTML,
    hidden: svg?.getAttribute("aria-hidden"),
    title: getComputedStyle(scope.getByText(title)).color,
    body: getComputedStyle(scope.getByText(body)).color,
  }).toEqual({
    background: semanticColor(alert, `${tone}-tint`),
    icon: semanticColor(alert, tone),
    shape: iconShape(icon),
    hidden: "true",
    title: semanticColor(alert, "text"),
    body: semanticColor(alert, "muted"),
  });
}

export const Danger: Story = {
  name: "실패 알림은 role=alert 이고 danger-tint 바탕에 danger 색 circle-x 아이콘이며 제목은 text, 본문은 muted 다",
  args: { tone: "danger" },
  play: async ({ canvas, canvasElement, userEvent }) => {
    const alert = canvas.getByRole("alert");
    await expectTone(
      alert,
      "danger",
      "circle-x",
      "실행이 실패했습니다",
      "payments.refund가 30초 안에 끝나지 않았습니다.",
    );
    await expect(canvas.queryByRole("status")).toBeNull();
    await expect(canvas.queryByRole("button", { name: "닫기" })).toBeNull();
    // 알림 자체는 포커스를 받지 않는다. 누를 것이 없으면 Tab 이 알림 밖으로 간다.
    await expect(alert.hasAttribute("tabindex")).toBe(false);
    await userEvent.tab();
    await expect(canvasElement.contains(document.activeElement)).toBe(false);
  },
};

export const Warning: Story = {
  name: "경고 알림은 role=status 이고 warning-tint 바탕에 warning 색 triangle-alert 아이콘이다",
  args: {
    tone: "warning",
    title: "결제 환불 플러그인이 꺼짐입니다",
    children: "켜기 전에는 환불 요청에 출력이 나오지 않습니다.",
  },
  play: async ({ canvas }) => {
    await expect(canvas.queryByRole("alert")).toBeNull();
    await expectTone(
      canvas.getByRole("status"),
      "warning",
      "triangle-alert",
      "결제 환불 플러그인이 꺼짐입니다",
      "켜기 전에는 환불 요청에 출력이 나오지 않습니다.",
    );
  },
};

export const Info: Story = {
  name: "톤을 고르지 않으면 정보 알림이고 role=status 에 info-tint 바탕, info 색 info 아이콘이다",
  args: {
    title: "이 대화는 30일 동안 보관됩니다",
    children: "운영자가 품질 확인을 위해 볼 수 있습니다.",
  },
  play: async ({ canvas }) => {
    await expect(canvas.queryByRole("alert")).toBeNull();
    await expectTone(
      canvas.getByRole("status"),
      "info",
      "info",
      "이 대화는 30일 동안 보관됩니다",
      "운영자가 품질 확인을 위해 볼 수 있습니다.",
    );
  },
};

export const WithActions: Story = {
  name: "actions 자리에 둔 버튼과 링크가 알림 안 본문 아래에 있다",
  args: { tone: "danger", actions: ACTIONS },
  play: async ({ canvas }) => {
    const alert = canvas.getByRole("alert");
    const scope = within(alert);
    const retry = scope.getByRole("button", { name: "다시 실행" });
    const link = scope.getByRole("link", { name: "실행 보기" });
    const body = scope.getByText("payments.refund가 30초 안에 끝나지 않았습니다.");
    await expect(retry.getBoundingClientRect().top).toBeGreaterThanOrEqual(
      body.getBoundingClientRect().bottom,
    );
    await expect(link.getAttribute("href")).toBe("#runs");
    await expect(scope.queryByRole("button", { name: "닫기" })).toBeNull();
  },
};

export const WithClose: Story = {
  name: "onClose 가 있으면 이름이 닫기인 투명·작은 아이콘 버튼이 있고 누르면 불리며 알림을 거두는 것은 쓰는 쪽이다",
  args: {
    tone: "info",
    title: "이 대화는 30일 동안 보관됩니다",
    children: "운영자가 품질 확인을 위해 볼 수 있습니다.",
    onClose: fn(),
  },
  play: async ({ args, canvas, userEvent }) => {
    const close = within(canvas.getByRole("status")).getByRole("button", { name: "닫기" });
    const style = getComputedStyle(close);
    await expect({ width: style.width, height: style.height }).toEqual({
      width: "32px",
      height: "32px",
    });
    await expect(colorsOf(close)).toMatchObject({
      background: TRANSPARENT,
      text: semanticColor(close, "muted"),
    });
    await userEvent.click(close);
    await expect(args.onClose).toHaveBeenCalledOnce();
    // 알림은 스스로 사라지지 않는다. 쓰는 쪽이 onClose 에서 그리지 않기로 해야 거둬진다.
    await expect(canvas.getByRole("status").contains(close)).toBe(true);
  },
};

const TONES = [
  ["danger", "실행이 실패했습니다"],
  ["warning", "결제 환불 플러그인이 꺼짐입니다"],
  ["info", "이 대화는 30일 동안 보관됩니다"],
] as const;

export const Combinations: Story = {
  name: "톤 셋마다 actions 와 닫기의 있음·없음 넷을 그리면 실패만 alert 이고 닫기는 onClose 가 있는 여섯이다",
  render: () => (
    <div className="flex flex-col gap-3">
      {TONES.flatMap(([tone, title]) =>
        [
          { actions: null, onClose: null },
          { actions: ACTIONS, onClose: null },
          { actions: null, onClose: fn() },
          { actions: ACTIONS, onClose: fn() },
        ].map(({ actions, onClose }, index) => (
          <Alert
            key={`${tone}-${String(index)}`}
            tone={tone}
            title={title}
            actions={actions}
            onClose={onClose}
          >
            운영자가 품질 확인을 위해 볼 수 있습니다.
          </Alert>
        )),
      )}
    </div>
  ),
  play: async ({ canvas }) => {
    await expect({
      alerts: canvas.getAllByRole("alert").length,
      statuses: canvas.getAllByRole("status").length,
      close: canvas.getAllByRole("button", { name: "닫기" }).length,
      retry: canvas.getAllByRole("button", { name: "다시 실행" }).length,
    }).toEqual({ alerts: 4, statuses: 8, close: 6, retry: 6 });
  },
};

export const WithActionsAndClose: Story = {
  name: "경고 알림에 actions 와 닫기를 함께 두면 닫기가 오른쪽 끝에 있다",
  args: {
    tone: "warning",
    title: "결제 환불 플러그인이 꺼짐입니다",
    children: "켜기 전에는 환불 요청에 출력이 나오지 않습니다.",
    actions: (
      <Button variant="secondary" size="s">
        켜기
      </Button>
    ),
    onClose: fn(),
  },
  play: async ({ canvas }) => {
    const scope = within(canvas.getByRole("status"));
    const close = scope.getByRole("button", { name: "닫기" });
    const action = scope.getByRole("button", { name: "켜기" });
    await expect(close.getBoundingClientRect().left).toBeGreaterThan(
      action.getBoundingClientRect().right,
    );
  },
};

export const DangerDark: Story = {
  name: "다크 모드의 실패 알림도 danger-tint 바탕에 danger 아이콘, text 제목, muted 본문이다",
  args: { tone: "danger", actions: ACTIONS, onClose: fn() },
  globals: { mode: "dark" },
  play: async ({ canvas }) => {
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    await expectTone(
      canvas.getByRole("alert"),
      "danger",
      "circle-x",
      "실행이 실패했습니다",
      "payments.refund가 30초 안에 끝나지 않았습니다.",
    );
  },
};

export const NarrowColumn: Story = {
  name: "actions 와 닫기를 둔 알림을 폭 320px 자리에 그려도 가로로 넘치지 않는다",
  args: {
    tone: "danger",
    actions: ACTIONS,
    onClose: fn(),
    children: "payments.refund가 30초 안에 끝나지 않았습니다. 주문 52건 모두 환불되지 않았습니다.",
  },
  render: (args) => (
    <div data-sample="column" style={{ width: 320 }}>
      <Alert {...args} />
    </div>
  ),
  play: async ({ canvasElement }) => {
    const column = canvasElement.querySelector("[data-sample=column]");
    await expect(column instanceof HTMLElement && column.scrollWidth <= column.clientWidth).toBe(
      true,
    );
  },
};

// 공문에서 잰다. 먹은 focus 와 accent 가 같은 색이다. 기본 테마가 아닌 테마에서 값을 재는 판정 스토리라 사진에서
// 뺀다(사진은 기본 테마만 찍는다, ADR 0026 의 2026-10-06 이력).
export const CloseFocus: Story = {
  name: "Tab 은 알림을 건너 닫기 버튼에 오고 그 바깥에 focus 색의 실선 테두리가 그려진다",
  tags: ["judgment"],
  args: { onClose: fn() },
  globals: { theme: "gongmun" },
  play: async ({ canvas, userEvent }) => {
    const close = canvas.getByRole("button", { name: "닫기" });
    await userEvent.tab();
    await expect(document.activeElement).toBe(close);
    await expect(focusRingOf(close)).toEqual(expectedFocusRing(close));
  },
};
