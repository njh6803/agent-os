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

/**
 * 그 이름의 아이콘 모양(svg 안쪽의 마크업). 그린 svg 의 `innerHTML` 과 견줘 어느 아이콘인지 클래스가 아니라 모양으로
 * 본다. 크기와 선 굵기는 svg 자신의 속성이라 모양에 들지 않는다. 문서에 붙이지 않은 요소에 그렸다가 걷는다.
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
