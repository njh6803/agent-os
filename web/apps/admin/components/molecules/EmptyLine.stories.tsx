// 빈 줄(admin-style 티켓 04, 명세 "화면 머리와 공통 상태"). 빈 종류의 줄(아이콘 16)과 거른 빈 목록(아이콘 20)이다. 문구는
// 플러그인 목록(05)과 실행 목록(06)이 쓸 그 글자다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, within } from "storybook/test";
import { EmptyLine } from "./EmptyLine";

const meta = {
  title: "molecules/EmptyLine",
  component: EmptyLine,
  args: { icon: "circle-minus", iconSize: "16", children: "등록된 것이 없다" },
} satisfies Meta<typeof EmptyLine>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 빈 종류. 아이콘은 글자와 함께 놓인 꾸밈이라 화면 읽기 프로그램에서 숨는다. */
export const EmptyKind: Story = {
  play: async ({ canvasElement }) => {
    const line = within(canvasElement).getByText("등록된 것이 없다");
    const icon = line.querySelector("svg");
    await expect(icon).toHaveAttribute("aria-hidden", "true");
    await expect(`${String(icon?.getBoundingClientRect().width)}px`).toBe("16px");
  },
};

/** 거른 빈 목록. 거른 상태의 배지 아이콘을 20 으로 쓴다. */
export const FilteredEmpty: Story = {
  args: { icon: "circle-pause", iconSize: "20", children: "일시정지한 실행이 없다" },
  play: async ({ canvasElement }) => {
    const icon = within(canvasElement).getByText("일시정지한 실행이 없다").querySelector("svg");
    await expect(`${String(icon?.getBoundingClientRect().width)}px`).toBe("20px");
  },
};
