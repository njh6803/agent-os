import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { colorsOf, semanticColor } from "../../storybook/expect";
import { Button } from "./Button";
import { CARD_ELEVATIONS, Card } from "./Card";
import { StatusBadge } from "./StatusBadge";

const meta = {
  title: "atoms/Card",
  component: Card,
  args: {
    children: (
      <>
        <h2 className="text-heading text-text">결제 환불</h2>
        <p className="text-body text-muted">환불 요청을 결제 서비스에 넘깁니다.</p>
      </>
    ),
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 제목 "결제 환불" 을 담은 카드. 카드는 제목의 부모다. */
function cardOf(canvasElement: HTMLElement, title = "결제 환불"): HTMLElement {
  const heading = Array.from(canvasElement.querySelectorAll("h2")).find(
    (element) => element.textContent === title,
  );
  const card = heading?.parentElement;
  if (card === null || card === undefined) {
    throw new Error(`제목이 "${title}" 인 카드가 없다`);
  }
  return card;
}

export const Default: Story = {
  name: "기본 카드는 div 이고 raised 바탕에 divider 테두리, 10px 모서리, 16px 여백, 그림자가 있다",
  play: async ({ canvasElement }) => {
    const card = cardOf(canvasElement);
    const style = getComputedStyle(card);
    await expect(card.tagName).toBe("DIV");
    await expect(colorsOf(card)).toEqual({
      background: semanticColor(card, "raised"),
      text: semanticColor(card, "text"),
      border: semanticColor(card, "divider"),
    });
    await expect({
      border: style.borderTopWidth,
      radius: style.borderTopLeftRadius,
      padding: style.paddingTop,
    }).toEqual({ border: "1px", radius: "10px", padding: "16px" });
    await expect(style.boxShadow).not.toBe("none");
  },
};

export const Section: Story = {
  name: "as 가 section 이면 section 으로 그리고 padding 3 은 12px 여백이다",
  args: { as: "section", padding: "3" },
  play: async ({ canvasElement }) => {
    const card = cardOf(canvasElement);
    await expect(card.tagName).toBe("SECTION");
    await expect(getComputedStyle(card).paddingTop).toBe("12px");
  },
};

export const Article: Story = {
  name: "as 가 article 이면 글 한 편의 역할로 찾힌다",
  args: { as: "article", elevation: "2" },
  play: async ({ canvas, canvasElement }) => {
    await expect(canvas.getByRole("article")).toBe(cardOf(canvasElement));
  },
};

export const Elevations: Story = {
  name: "elevation 0 은 그림자가 없고 1·2·3 은 있다",
  render: (args) => (
    <div className="flex flex-col gap-4">
      {CARD_ELEVATIONS.map((elevation) => (
        <Card key={elevation} {...args} elevation={elevation}>
          <h2 className="text-heading text-text">{`그림자 ${elevation}`}</h2>
        </Card>
      ))}
    </div>
  ),
  play: async ({ canvasElement }) => {
    const shadows = CARD_ELEVATIONS.map(
      (elevation) => getComputedStyle(cardOf(canvasElement, `그림자 ${elevation}`)).boxShadow,
    );
    await expect(shadows.map((shadow) => shadow === "none")).toEqual([true, false, false, false]);
    await expect(new Set(shadows).size).toBe(CARD_ELEVATIONS.length);
  },
};

export const DefaultDark: Story = {
  name: "다크 모드의 카드도 raised 바탕에 divider 테두리다",
  globals: { mode: "dark" },
  play: async ({ canvasElement }) => {
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    const card = cardOf(canvasElement);
    await expect(colorsOf(card)).toMatchObject({
      background: semanticColor(card, "raised"),
      border: semanticColor(card, "divider"),
    });
  },
};

export const NarrowSlot: Story = {
  name: "상태 배지와 버튼 둘을 담은 카드를 폭 320px 자리에 그려도 가로로 넘치지 않는다",
  args: {
    as: "article",
    children: (
      <>
        <StatusBadge status="paused" />
        <h2 className="text-heading text-text">결제 환불을 승인할까요</h2>
        <p className="text-body text-muted">
          주문 2024-1187의 결제 32,000원을 환불합니다. 승인하면 결제 서비스에 요청을 넘기고 되돌릴
          수 없습니다.
        </p>
        <div className="flex gap-2">
          <Button variant="secondary">거부</Button>
          <Button>승인</Button>
        </div>
      </>
    ),
  },
  render: (args) => (
    <div data-sample="slot" style={{ width: 320 }}>
      <Card {...args} />
    </div>
  ),
  play: async ({ canvas, canvasElement }) => {
    const slot = canvasElement.querySelector("[data-sample=slot]");
    const card = canvas.getByRole("article");
    await expect(slot instanceof HTMLElement && slot.scrollWidth <= slot.clientWidth).toBe(true);
    await expect(card.scrollWidth <= card.clientWidth).toBe(true);
    // 카드의 줄은 폭을 채우지만(글 입력이 늘어나야 한다) 배지는 내용의 폭이다.
    const badge = canvas.getByText("일시정지");
    await expect(badge.getBoundingClientRect().width).toBeLessThan(card.clientWidth / 2);
  },
};
