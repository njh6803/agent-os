// 디자인 시스템의 판정 함수(프로브 표본). 스토리의 play 가 실제 chromium 에서 부른다. 의존성이 없다.
// - contrastRatio: WCAG 2.2 의 대비. 쓰임새 토큰의 계산값(#RRGGBB)을 받는다.
// - classesWithoutRules: 그린 요소의 class 낱말 가운데 그것을 고르는 규칙이 시트에 하나도 없는 것. Tailwind 의 기본
//   테마를 비우면 `text-base` 같은 익숙한 클래스가 오류 없이 아무 CSS 도 만들지 않는다(ADR 0026).
// - undefinedCustomProperties: 시트가 대체값 없이 `var()` 로 읽는데 어느 규칙도 정의하지 않는 사용자 정의 속성.
//   `--spacing` 을 비운 뒤의 `p-5` 처럼 CSS 는 생기지만 값이 비는 클래스를 잡는다.

type Channels = readonly [number, number, number];

/** WCAG 2.2 의 대비. 인자는 `#RRGGBB` 다. */
export function contrastRatio(a: string, b: string): number {
  const first = luminance(hexChannels(a));
  const second = luminance(hexChannels(b));
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

function hexChannels(hex: string): Channels {
  const match = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(hex.trim());
  if (match === null) {
    throw new Error(`#RRGGBB 가 아니다: "${hex}"`);
  }
  const [, red = "", green = "", blue = ""] = match;
  return [Number.parseInt(red, 16), Number.parseInt(green, 16), Number.parseInt(blue, 16)];
}

function luminance([red, green, blue]: Channels): number {
  const linear = (value: number): number => {
    const channel = value / 255;
    return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * linear(red) + 0.7152 * linear(green) + 0.0722 * linear(blue);
}

/** 시트들의 스타일 규칙 전부. `@media`·`@layer`·`@supports`·`@container` 와 CSS 중첩 안까지 내려간다. */
export function styleRules(sheets: Iterable<CSSStyleSheet>): CSSStyleRule[] {
  const rules: CSSStyleRule[] = [];
  const visit = (list: CSSRuleList): void => {
    for (const rule of list) {
      if (rule instanceof CSSStyleRule) {
        rules.push(rule);
        visit(rule.cssRules);
      } else if (rule instanceof CSSGroupingRule) {
        visit(rule.cssRules);
      }
    }
  };
  for (const sheet of sheets) {
    visit(sheet.cssRules);
  }
  return rules;
}

/** 이 사용자 정의 속성을 정의하는 규칙이 있는 시트만. 디자인 시스템의 시트를 Storybook 의 시트와 가른다. */
export function sheetsDefining(name: string, sheets: Iterable<CSSStyleSheet>): CSSStyleSheet[] {
  return Array.from(sheets).filter((sheet) =>
    styleRules([sheet]).some((rule) => rule.style.getPropertyValue(name) !== ""),
  );
}

/** root 와 그 아래 요소의 class 낱말 가운데 그것을 고르는 규칙이 시트에 없는 것. 정렬해 돌려준다. */
export function classesWithoutRules(root: Element, sheets: Iterable<CSSStyleSheet>): string[] {
  const selectors = styleRules(sheets).map((rule) => rule.selectorText);
  const tokens = new Set<string>();
  for (const element of [root, ...root.querySelectorAll("*")]) {
    for (const token of element.classList) {
      tokens.add(token);
    }
  }
  return [...tokens].filter((token) => !selectors.some((selector) => selects(selector, token))).sort();
}

function selects(selector: string, token: string): boolean {
  const needle = `.${CSS.escape(token)}`;
  let at = selector.indexOf(needle);
  while (at !== -1) {
    const next = selector.charAt(at + needle.length);
    if (next === "" || !/[\w\\-]/.test(next)) {
      return true;
    }
    at = selector.indexOf(needle, at + 1);
  }
  return false;
}

/** root 와 그 아래 요소의 class 낱말 가운데 임의값(`[...]`)을 쓰는 것. 규칙은 있지만 디자인 토큰을 건너뛴다. */
export function arbitraryClasses(root: Element): string[] {
  const tokens = new Set<string>();
  for (const element of [root, ...root.querySelectorAll("*")]) {
    for (const token of element.classList) {
      if (token.includes("[")) {
        tokens.add(token);
      }
    }
  }
  return [...tokens].sort();
}

/** 대체값 없는 `var(--x)` 가운데 어느 규칙도(`@property` 도) 정의하지 않는 --x. 정렬해 돌려준다. */
export function undefinedCustomProperties(sheets: Iterable<CSSStyleSheet>): string[] {
  const defined = new Set<string>();
  const used = new Set<string>();
  const visit = (list: CSSRuleList): void => {
    for (const rule of list) {
      if (rule instanceof CSSPropertyRule) {
        defined.add(rule.name);
      } else if (rule instanceof CSSStyleRule) {
        for (const property of rule.style) {
          if (property.startsWith("--")) {
            defined.add(property);
          }
        }
        for (const match of rule.style.cssText.matchAll(/var\(\s*(--[\w-]+)\s*\)/g)) {
          used.add(match[1] ?? "");
        }
        visit(rule.cssRules);
      } else if (rule instanceof CSSGroupingRule) {
        visit(rule.cssRules);
      }
    }
  };
  for (const sheet of sheets) {
    visit(sheet.cssRules);
  }
  return [...used].filter((name) => !defined.has(name)).sort();
}
