// shadow root 에 디자인 토큰 CSS 를 싣는 도구(ADR 0024 의 스타일, ADR 0026 의 상속).
//
// shadow root 안에서는 `@property` 가 등록되지 않는다. 그래서 Tailwind 가 `@layer properties` 안의 `@supports` 조건
// 아래에 내는 대체 블록을 조건 없이 같은 층에 다시 넣는다. 층 밖에 두면 유틸리티를 이긴다(ADR 0024).
// 상속 속성(글꼴, 글자색, 줄 높이, 자간 등)은 :host 가 아니라 shadow 안의 감싼 요소에서 다시 정한다. 그 규칙은 디자인
// 토큰 CSS 의 `[data-ui-root]` 다. 쓰는 쪽은 shadow root 의 그림을 이 속성을 단 요소 하나로 감싼다.

/** 감싼 요소의 표시. shadow root 안에서 그림 전체를 감싸는 요소에 단다(값은 빈 글자). */
export const UI_ROOT_ATTRIBUTE = "data-ui-root";

/** 빌드한 디자인 토큰 CSS(`?inline` 글자)로 shadow root 의 `adoptedStyleSheets` 에 넣을 시트를 만든다. */
export function shadowSheets(css: string): CSSStyleSheet[] {
  const sheet = new CSSStyleSheet();
  sheet.replaceSync(css);
  const defaults = new CSSStyleSheet();
  defaults.replaceSync(propertyDefaults(sheet));
  return [sheet, defaults];
}

/** 시트의 `@layer properties` 안 `@supports` 대체 규칙을 조건 없이 같은 층에 둔 글자. 없으면 빈 글자다. */
export function propertyDefaults(sheet: CSSStyleSheet): string {
  const rules: string[] = [];
  for (const rule of sheet.cssRules) {
    if (!(rule instanceof CSSLayerBlockRule) || rule.name !== "properties") {
      continue;
    }
    for (const inner of rule.cssRules) {
      if (inner instanceof CSSSupportsRule) {
        rules.push(...Array.from(inner.cssRules, (fallback) => fallback.cssText));
      }
    }
  }
  return rules.length === 0 ? "" : `@layer properties { ${rules.join(" ")} }`;
}
