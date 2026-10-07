// 카드(디자인 파일 02.8 표면 · 카드). 플러그인 하나, 실행 하나처럼 한 대상을 올라온 면(`raised`, `divider` 테두리,
// 10px 모서리)에 묶는다. 그림자는 단계 넷(`"0"` 은 없음)이고 안의 줄 사이는 8px 이다. 카드 전체를 누르는 곳으로
// 만들지 않는다. 누르는 곳은 안의 버튼과 링크다.
import type { ReactNode } from "react";
import type { NativeProps } from "../../props";

export type CardElement = "div" | "section" | "article";
export const CARD_ELEVATIONS = ["0", "1", "2", "3"] as const;
export type CardElevation = (typeof CARD_ELEVATIONS)[number];
export type CardPadding = "3" | "4";

const BASE = "flex flex-col gap-2 rounded-l border border-divider bg-raised text-text";

// `"0"` 은 그림자 유틸리티를 두지 않아 `box-shadow` 가 `none` 이다.
const ELEVATION_CLASS = {
  "0": "",
  "1": " shadow-1",
  "2": " shadow-2",
  "3": " shadow-3",
} satisfies Record<CardElevation, string>;

const PADDING_CLASS = { "3": "p-3", "4": "p-4" } satisfies Record<CardPadding, string>;

interface CardOwnProps {
  /** 감싸는 요소. */
  as?: CardElement;
  elevation?: CardElevation;
  padding?: CardPadding;
  children: ReactNode;
}

// 나머지 속성은 `div` 의 것이라 `as` 가 section·article 이어도 ref 와 이벤트의 요소가 `HTMLDivElement` 로 적힌다. 실제
// 요소와 다른 것은 `HTMLDivElement` 가 `HTMLElement` 에 더하는 낡은 `align` 하나다(TypeScript 5.9 의 lib.dom). 셋이 함께
// 지는 `HTMLElement` 의 것(`section` 의 속성)으로 받으면 그 ref 가 div 의 ref 에 맞지 않아 tsc 가 거부했고, 다형
// 제네릭은 타입 단언 없이 넘기기 어렵다(원칙 III).
export type CardProps = CardOwnProps & NativeProps<"div", keyof CardOwnProps>;

export function Card({
  as: Element = "div",
  elevation = "1",
  padding = "4",
  children,
  ...rest
}: CardProps) {
  return (
    <Element {...rest} className={`${BASE} ${PADDING_CLASS[padding]}${ELEVATION_CLASS[elevation]}`}>
      {children}
    </Element>
  );
}
