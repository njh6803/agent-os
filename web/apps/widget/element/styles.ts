// 페이지 안 위젯의 호스트와 감싼 요소의 규칙. 디자인 토큰 CSS 다음에 shadow root 의 시트로 싣는다(index.ts).
//
// - 호스트는 `display: block` 이고 폭과 높이는 사이트가 정한다. 위젯은 자기 자리를 채운다(web-widget 명세 "크기").
//   `hidden` 속성은 브라우저 기본 시트의 것이라 이 규칙에 진다. 그래서 따로 받는다. 사이트 문서의 규칙(태그 선택자
//   포함)은 :host 를 이기므로 사이트는 호스트의 display 를 바꿀 수 있다.
// - 감싼 요소가 컨테이너이고, 레이아웃의 기준 폭은 `@wide:`(360px)다(명세 "테마·모드·밀도·글꼴"). 상속 속성은 디자인
//   토큰 CSS 의 `[data-ui-root]` 가 다시 정한다.
// - 감싼 요소에서 두 글꼴 변수를 사이트 문서에 등록한 이름으로 다시 정한다(fonts.ts). 대체 목록은 디자인 토큰 CSS 의
//   것과 같다.
//
// 층 밖의 규칙이라 층 안의 디자인 토큰 CSS 를 이긴다. 겹치는 속성은 두 글꼴 변수뿐이고 그것은 이겨야 한다.

import { UI_ROOT_ATTRIBUTE } from "@agent-os/ui";
import { WIDGET_MONO, WIDGET_SANS } from "./fonts";

export function hostRules(): string {
  return [
    ":host { display: block; }",
    ":host([hidden]) { display: none; }",
    `[${UI_ROOT_ATTRIBUTE}] {`,
    "  height: 100%;",
    "  container-type: inline-size;",
    `  --sans: "${WIDGET_SANS}", system-ui, sans-serif;`,
    `  --mono: "${WIDGET_MONO}", ui-monospace, monospace;`,
    "}",
  ].join("\n");
}
