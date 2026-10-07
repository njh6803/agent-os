// 컴포넌트 스토리의 play 가 쓰는 도우미. 클래스 글자를 단언하지 않고 쓰임새 토큰이 풀린 계산값으로 본다.

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
