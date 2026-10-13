// 컴포넌트 스토리의 play 가 쓰는 도우미. 클래스 글자를 단언하지 않고 쓰임새 토큰이 풀린 계산값으로 본다.
import { createElement } from "react";
import { flushSync } from "react-dom";
import { createRoot } from "react-dom/client";
import { Icon, type IconName } from "../components/atoms/Icon";

/** 요소에서 풀린 쓰임새 토큰 `--<name>` 의 값(#RRGGBB)을 getComputedStyle 의 색 모양(`rgb(r, g, b)`)으로 돌려준다. */
export function semanticColor(element: Element, name: string): string {
  const hex = getComputedStyle(element).getPropertyValue(`--${name}`).trim();
  const match = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex);
  if (match === null) {
    throw new Error(`--${name} 이 #RRGGBB 로 풀리지 않았다: "${hex}"`);
  }
  const [, red = "", green = "", blue = ""] = match;
  return `rgb(${[red, green, blue].map((channel) => String(Number.parseInt(channel, 16))).join(", ")})`;
}

/** 배경색, 글자색, 테두리색을 한 번에. 상태마다 쓰임새 토큰과 맞댄다. */
export function colorsOf(element: Element): { background: string; text: string; border: string } {
  const style = getComputedStyle(element);
  return { background: style.backgroundColor, text: style.color, border: style.borderTopColor };
}

/** 투명한 배경의 계산값. */
export const TRANSPARENT = "rgba(0, 0, 0, 0)";

/**
 * 올림을 칠하는 요소의 기대 색. 그 요소가 `:hover` 면 올림의 쓰임새 토큰(`hover`), 아니면 쉬는 토큰(`rest`)이다. 스토리
 * 테스트의 userEvent 는 합성 이벤트라 실제 포인터를 옮기지 못하는데, CI 의 한 실행(PR #165)에서 포인터가 화면 위쪽에 머물러
 * 폭을 채운 라벨이 `:hover` 였다. 라벨의 `:hover` 는 그 칸에도 걸린다. 쉬는 모양은 포인터를 다루는 사진 비교가 지킨다.
 */
export function hoverAwareColor(element: Element, rest: string, hover: string): string {
  return semanticColor(element, element.matches(":hover") ? hover : rest);
}

interface FocusRing {
  style: string;
  width: string;
  offset: string;
  color: string;
}

/** 포커스 링(outline)의 모양, 굵기, 띄움, 색. */
export function focusRingOf(element: Element): FocusRing {
  const style = getComputedStyle(element);
  return {
    style: style.outlineStyle,
    width: style.outlineWidth,
    offset: style.outlineOffset,
    color: style.outlineColor,
  };
}

/** 그려야 할 포커스 링. `focus` 쓰임새 토큰으로 2px 실선을 2px 띄운다. */
export function expectedFocusRing(element: Element): FocusRing {
  return { style: "solid", width: "2px", offset: "2px", color: semanticColor(element, "focus") };
}

/** 아이콘이 그린 요소(선) 하나의 계산된 `vector-effect` 와 `stroke-width`. */
interface Stroke {
  effect: string;
  width: string;
}

/** 아이콘의 선. 그린 요소마다 `vector-effect` 가 `non-scaling-stroke` 라 크기와 상관없이 화면의 1.5px 이다. */
export const SCREEN_STROKE: Stroke = { effect: "non-scaling-stroke", width: "1.5px" };

/**
 * svg 가 그린 요소마다의 선. 그린 요소가 없으면 던진다. 스토리는 이 목록을 자기 길이만큼의 `SCREEN_STROKE` 와 맞대는데,
 * 빈 목록은 그 기대(빈 목록)에 늘 맞기 때문이다.
 */
export function strokesOf(svg: Element): Stroke[] {
  const strokes = Array.from(
    svg.querySelectorAll("path, circle, ellipse, line, rect, polyline, polygon"),
    (shape) => {
      const style = getComputedStyle(shape);
      return { effect: style.vectorEffect, width: style.strokeWidth };
    },
  );
  if (strokes.length === 0) {
    throw new Error("svg 에 그린 요소가 없다");
  }
  return strokes;
}

/**
 * 그 이름의 아이콘 모양(svg 안쪽의 마크업). 그린 svg 의 `innerHTML` 과 견줘 어느 아이콘인지 클래스가 아니라 모양으로
 * 본다. 크기와 선 굵기는 svg 자신의 속성이라 모양에 들지 않는다. 그린 요소마다 붙는 `vector-effect` 는 모양에 들므로,
 * 기대 모양도 컴포넌트가 쓰는 같은 `Icon` 으로 그린다. 문서에 붙이지 않은 요소에 그렸다가 걷는다.
 * `react-dom/server` 를 쓰지 않는 것은 스토리 테스트가 처음 보는 의존성을 Vite 가 도중에 최적화하며 테스트를 다시
 * 불러와서다(첫 실행에서 "Vite unexpectedly reloaded a test" 로 파일 하나가 빨갰다).
 */
export function iconShape(name: IconName): string {
  const host = document.createElement("div");
  const root = createRoot(host);
  flushSync(() => {
    root.render(createElement(Icon, { name }));
  });
  const shape = host.firstElementChild?.innerHTML ?? "";
  root.unmount();
  return shape;
}
