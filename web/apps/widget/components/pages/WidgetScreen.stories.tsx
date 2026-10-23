// 위젯의 첫 화면을 iframe 의 크기로 그린다. 폭은 지원하는 가장 좁은 320px 과 기준 폭(360px)을 넘는 400px 이고, 높이는
// 화면 디자인의 예시 560px 이다(web-widget 명세 "임베드"의 크기). 미리보기의 afterEach 가 클래스를, addon-a11y 가
// 접근성을, 사진 비교(visual/)가 그림을 판정한다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import type { ReactNode } from "react";
import { expect, within } from "storybook/test";
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
