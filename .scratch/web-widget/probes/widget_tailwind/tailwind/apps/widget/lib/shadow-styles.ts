// Tailwind 로 빌드한 CSS 를 shadow root 에 넣을 시트로 만든다.
//
// Tailwind v4 는 합성 유틸리티(border, shadow, ring, translate, gradient, outline 등)가 읽는 변수의 초기값을 `@property` 로
// 등록한다. 브라우저는 shadow root 안의 `@property` 를 등록하지 않아 그 변수가 비고, 그것을 읽는 선언이 무효가 된다.
// Tailwind 는 `@property` 를 모르는 브라우저에만(@supports 조건) 같은 초기값을 `*, ::before, ::after, ::backdrop` 에 두는
// 대체 블록을 `@layer properties` 안에 낸다. 그 규칙을 조건 없이 다시 넣는다(widget_tailwind/shadow.mjs 의 swatch 가 잰다).
// - `@property` 의 초기값을 읽어 만들면 `--tw-ring-offset-width` 가 `0`(단위 없음)이 되어 ring 의 `calc(2px + 0)` 이
//   무효다. 대체 블록은 `0px` 이다.
// - `:host` 한 곳에 두면 물려받아 부모가 정한 값(shadow, translate, border-style, gradient)이 자식에게 샌다.
// - 층 밖에 두면 층 안의 유틸리티를 이긴다. Tailwind 가 `properties` 층을 맨 앞(가장 약한 자리)에 둔다.

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
