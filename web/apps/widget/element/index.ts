// 페이지 안 번들의 입구(tools/element.ts 가 Vite 라이브러리 빌드로 묶는다). 사이트가 `<script src="https://<위젯
// 출처>/widget/element.js">` 로 실으면 `<agent-os-widget>` 를 정의한다(web-widget 명세 "임베드"의 페이지 안 방식).
//
// - 기준 주소는 이 파일이 최상위를 실행하는 동안의 `document.currentScript` 에서 읽는다(base.ts). 요소가 붙을 때는 그
//   값이 이미 없다. 읽지 못하면 글꼴도 등록하지 않는다. 그 출처로는 아무것도 받지 않는다.
// - 글꼴은 위젯만 쓰는 family 이름으로 사이트 문서에 한 번 등록한다(fonts.ts). 문서에 더한 face 는 그 글꼴로 그릴 글자가
//   생길 때 받는다.
// - shadow root 의 시트는 위젯의 CSS(`?inline`)와 그 `@property` 대체 블록(디자인 시스템의 shadowSheets), 호스트와 감싼
//   요소의 규칙(styles.ts)이다. 구성한 시트는 같은 문서의 위젯이 함께 든다.
// - 같은 문서에서 번들이 두 번 실려도 먼저 정의한 것을 둔다. 둘째는 아무것도 하지 않는다.
// - 아무것도 내보내지 않는다. 내보내면 IIFE 가 사이트 페이지에 전역 이름을 짓는다.

import { shadowSheets } from "@agent-os/ui";
import { FONT_FACES } from "virtual:agent-os-widget/fonts";
import css from "../styles/widget.css?inline";
import { scriptBaseUrl } from "./base";
import { registerFonts } from "./fonts";
import { hostRules } from "./styles";
import { ELEMENT_NAME, widgetElement } from "./WidgetElement";

const baseUrl = scriptBaseUrl(document.currentScript);

if (customElements.get(ELEMENT_NAME) === undefined) {
  if (baseUrl !== null) {
    registerFonts(
      FONT_FACES,
      baseUrl,
      (family, source, descriptors) => new FontFace(family, source, descriptors),
      (face) => document.fonts.add(face),
    );
  }
  const host = new CSSStyleSheet();
  host.replaceSync(hostRules());
  customElements.define(
    ELEMENT_NAME,
    widgetElement({ sheets: [...shadowSheets(css), host], baseUrl }),
  );
}
