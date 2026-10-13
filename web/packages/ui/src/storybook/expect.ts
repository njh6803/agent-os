// 컴포넌트 스토리의 play 가 쓰는 도우미. 클래스 글자를 단언하지 않고 쓰임새 토큰이 풀린 계산값으로 본다.
import { createElement } from "react";
import { flushSync } from "react-dom";
import { createRoot } from "react-dom/client";
import { Icon, type IconName } from "../components/atoms/Icon";

/**
 * 대상이 놓인 부모의 범위에서 풀린 쓰임새 토큰 `--<name>` 의 색을 getComputedStyle 의 색 모양으로 돌려준다(불투명은
 * `rgb(r, g, b)`, 반투명은 `rgba(r, g, b, a)`). 대상 바로 앞에 `background-color: var(--<name>)` 을 둔 숨은 탐침 요소를
 * 잠깐 붙여 그 계산값을 읽는다. 대상 자신이 `data-theme`·`data-mode` 를 달면 그 범위는 보지 못한다. 브라우저가 대상의 색을 직렬화하는 것과 같은 길이라 hex 를 손으로 바꾸며 생기는 알파 자릿수의
 * 차이가 없다. 쓰임새 토큰은 테마나 모드를 다는 요소마다 다시 선언되어, 같은 부모(같은 테마·모드, 같은 shadow root)에
 * 두어야 대상과 같은 값으로 풀린다. 문서 뿌리에 붙인 탐침은 다른 범위의 값으로 풀려 두 범위가 같은 값일 때만 조용히
 * 맞는다. 토큰이 `#RRGGBB` 나 `#RRGGBBAA` 로 풀리지 않으면 던진다.
 */
export function semanticColor(element: Element, name: string): string {
  const parent = element.parentNode;
  if (parent === null) {
    throw new Error(`--${name} 을 잴 자리가 없다: 대상이 문서에 붙지 않았다`);
  }
  const probe = document.createElement("span");
  probe.hidden = true;
  probe.style.backgroundColor = `var(--${name})`;
  parent.insertBefore(probe, element);
  try {
    const style = getComputedStyle(probe);
    const hex = style.getPropertyValue(`--${name}`).trim();
    if (!/^#[0-9a-f]{6}(?:[0-9a-f]{2})?$/i.test(hex)) {
      throw new Error(`--${name} 이 #RRGGBB 나 #RRGGBBAA 로 풀리지 않았다: "${hex}"`);
    }
    return style.backgroundColor;
  } finally {
    probe.remove();
  }
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

/** 그려야 할 포커스 링. `focus-ring` 쓰임새 토큰으로 2px 실선을 2px 띄운다. */
export function expectedFocusRing(element: Element): FocusRing {
  return {
    style: "solid",
    width: "2px",
    offset: "2px",
    color: semanticColor(element, "focus-ring"),
  };
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
