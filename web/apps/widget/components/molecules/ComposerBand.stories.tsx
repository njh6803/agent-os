// 입력창 위의 띠를 폭 320px 과 400px 에서 그린다(web-widget 티켓 07, 화면 디자인 mk-limit, mk-reconnect, mk-approval).
// 미리보기의 afterEach 가 클래스를, addon-a11y 가 접근성을, 사진 비교(visual/)가 그림을 판정한다. 재접속의 글은 09 가
// 채울 명세의 문구이고 승인 기다림의 글은 08 이 채운 문구다. 여기서는 하나만 서는 차례를 보이려고 쓴다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import type { ReactNode } from "react";
import { expect, within } from "storybook/test";
import { ComposerBand, type Band } from "./ComposerBand";

function Sized({ width, children }: { readonly width: number; readonly children: ReactNode }) {
  return (
    <div className="bg-bg-raised text-text" style={{ width }}>
      {children}
    </div>
  );
}

const RECONNECT: Band = {
  kind: "progress",
  label: "연결이 끊겨 다시 잇고 있습니다. 받은 내용은 그대로 있습니다.",
};

const LIMIT: Band = {
  kind: "notice",
  icon: "info",
  text: "동시에 처리할 수 있는 요청이 가득 찼습니다. 5초 뒤에 다시 보낼 수 있습니다.",
};

const APPROVAL: Band = { kind: "notice", icon: "info", text: "승인이나 거부를 먼저 골라 주세요." };

const meta = {
  title: "molecules/ComposerBand",
  component: ComposerBand,
  args: { reconnect: null, limit: LIMIT, approval: null },
  decorators: [
    (Story, { parameters }) => (
      <Sized width={parameters["width"] === 400 ? 400 : 320}>
        <Story />
      </Sized>
    ),
  ],
} satisfies Meta<typeof ComposerBand>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 상한의 띠. 가장 좁은 폭에서 글이 두 줄로 꺾여도 아이콘은 첫 줄에 맞는다. */
export const Limit: Story = {
  play: async ({ canvasElement }) => {
    const band = within(canvasElement).getByRole("status");
    await expect(band).toHaveTextContent(
      "동시에 처리할 수 있는 요청이 가득 찼습니다. 5초 뒤에 다시 보낼 수 있습니다.",
    );
    // 아이콘은 글 옆의 꾸밈이라 숨는다.
    await expect(band.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  },
};

/** 기준 폭을 넘는 폭의 상한 띠. 다크 모드다. */
export const LimitWideDark: Story = {
  parameters: { width: 400 },
  globals: { mode: "dark" },
};

/** 재접속의 띠는 진행 표시와 그 이름이다. */
export const Reconnect: Story = {
  parameters: { width: 400 },
  args: { reconnect: RECONNECT, limit: null },
  play: async ({ canvasElement }) => {
    const band = within(canvasElement).getByRole("status");
    await expect(within(band).getByRole("progressbar", { name: RECONNECT.label })).toBeVisible();
  },
};

/** 셋이 겹치면 재접속만 선다. */
export const ReconnectFirst: Story = {
  args: { reconnect: RECONNECT, limit: LIMIT, approval: APPROVAL },
  play: async ({ canvasElement }) => {
    const band = within(canvasElement).getByRole("status");
    await expect(band).toHaveTextContent(RECONNECT.label);
    await expect(band).not.toHaveTextContent("동시에 처리할");
    await expect(band).not.toHaveTextContent("승인이나 거부");
  },
};

/** 상한과 승인 기다림이 겹치면 상한이 선다. */
export const LimitBeforeApproval: Story = {
  parameters: { width: 400 },
  args: { limit: LIMIT, approval: APPROVAL },
  play: async ({ canvasElement }) => {
    const band = within(canvasElement).getByRole("status");
    await expect(band).toHaveTextContent("동시에 처리할 수 있는 요청이 가득 찼습니다.");
    await expect(band).not.toHaveTextContent("승인이나 거부");
  },
};

/** 승인 기다림만 있으면 그것이 선다. */
export const Approval: Story = {
  args: { limit: null, approval: APPROVAL },
  play: async ({ canvasElement }) => {
    await expect(within(canvasElement).getByRole("status")).toHaveTextContent(
      "승인이나 거부를 먼저 골라 주세요.",
    );
  },
};

/** 띠가 없어도 읽기 영역의 틀은 서 있고, 위 테두리만 남는다. */
export const Empty: Story = {
  args: { limit: null },
  play: async ({ canvasElement }) => {
    const band = within(canvasElement).getByRole("status");
    await expect(band.textContent).toBe("");
    await expect(getComputedStyle(band).borderTopWidth).toBe("1px");
  },
};
