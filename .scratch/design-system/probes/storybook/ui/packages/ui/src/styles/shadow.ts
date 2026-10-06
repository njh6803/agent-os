// Tailwind 로 빌드한 CSS 를 shadow root 에 넣을 시트로 만든다(ADR 0024 의 스타일, widget_tailwind 의 lib/shadow-styles.ts
// 와 같은 것). shadow root 안에서는 `@property` 가 등록되지 않으므로, Tailwind 가 `@layer properties` 안의 `@supports`
// 조건 아래에 내는 대체 블록을 조건 없이 같은 층에 다시 넣는다.

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
