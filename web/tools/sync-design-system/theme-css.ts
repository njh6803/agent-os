/**
 * 디자인 토큰 CSS(`web/packages/ui/src/styles/theme.css`)를 푸는 공용 모듈. 짓기, 들이기, 기록과 확인이 같이 쓴다
 * (design-reverse-sync 명세 "이음매"의 2026-10-22 주석).
 *
 * - 벌(테마 × 모드)마다의 값은 블록을 이름으로 골라 읽지 않고 캐스케이드로 낸다. 문서 뿌리(`html`)에
 *   `data-theme="<테마>"` 와 `data-mode="<모드>"` 를 단 것으로 보고, 선택자가 그 요소에 맞는 규칙 가운데 브라우저처럼
 *   레이어, 특정성, 차례로 이기는 사용자 정의 속성의 선언을 고른다. 그래서 군청·자초의 주 버튼 덮기 같은 갈래가
 *   목록 없이 그대로 나온다. 고른 선언은 줄 번호와 줄 끝 주석을 함께 든다.
 * - `@media` 안의 규칙은 보지 않는다. 시스템 모드(`prefers-color-scheme`)와 폭에 따른 밀도의 사본이고, 페이지의 벌은
 *   모드를 명시한 요소다.
 * - `@theme` 블록(Tailwind)은 캐스케이드와 따로, `inline` 이 아닌 블록의 선언을 그대로 낸다. 글자 크기, 간격, 모서리의
 *   값이 거기 있다.
 * - 주석은 선언을 끝낸 `;` 와 같은 줄에서 시작하는 것만 그 선언의 것이다(명세 "토큰 설명의 자리"). 앞 줄의 주석은
 *   어느 선언의 것도 아니다.
 *
 * 못 보는 것: 선택자는 이 파일이 쓰는 꼴(`:root`, `:host(…)`, 속성 선택자, `:not(…)`, 태그)만 푼다. 다른 의사 클래스나
 * 속성 연산자가 사용자 정의 속성을 선언한 규칙에 오면 입력 오류로 멈춘다. `!important` 와 이름 있는 레이어의 미리
 * 선언(`@layer a, b;`)은 보지 않고, 레이어의 차례는 블록이 처음 나온 차례다.
 */

import { CommandError } from "./command.ts";

export const MODES = ["light", "dark"] as const;

export type Mode = (typeof MODES)[number];

/** 선언 하나. */
export interface Declaration {
  readonly property: string;
  readonly value: string;
  /** 선언을 끝낸 `;` 와 같은 줄에서 시작하는 주석의 글. 없으면 빈 글이다. */
  readonly comment: string;
  /** 선언이 시작한 줄. 1 부터 센다. */
  readonly line: number;
}

/** 디자인 토큰 CSS 를 푼 것. */
export interface ThemeCss {
  /** `[data-theme="…"]` 이 처음 나온 차례의 테마 키. 기본 테마의 블록이 앞이라 첫째가 기본 테마다. */
  readonly themes: readonly string[];
  /** `inline` 이 아닌 `@theme` 블록의 선언. 속성 이름으로 찾고 CSS 의 차례를 지킨다. */
  readonly themeStatic: ReadonlyMap<string, Declaration>;
  /** 그 테마와 모드를 단 문서 뿌리에서 이기는 사용자 정의 속성의 선언. CSS 에 처음 나온 차례다. */
  winners(theme: string, mode: Mode): ReadonlyMap<string, Declaration>;
}

interface MutableDeclaration {
  property: string;
  value: string;
  comment: string;
  line: number;
  endLine: number;
}

interface StyleRule {
  readonly selectors: readonly string[];
  readonly declarations: readonly Declaration[];
  /** 감싼 at-rule 의 머리. 바깥부터다. */
  readonly context: readonly string[];
}

interface Parsed {
  readonly rules: readonly StyleRule[];
  readonly themeStatic: readonly Declaration[];
}

class Scanner {
  readonly text: string;
  at = 0;
  line = 1;

  constructor(text: string) {
    this.text = text;
  }

  peek(length = 1): string {
    return this.text.slice(this.at, this.at + length);
  }

  done(): boolean {
    return this.at >= this.text.length;
  }

  advance(count = 1): string {
    const taken = this.text.slice(this.at, this.at + count);
    for (const character of taken) {
      if (character === "\n") {
        this.line += 1;
      }
    }
    this.at += taken.length;
    return taken;
  }

  skipSpace(): void {
    while (!this.done() && /\s/.test(this.peek())) {
      this.advance();
    }
  }

  /** `/*` 에서 시작해 주석을 읽고 안의 글을 낸다. */
  comment(): string {
    const end = this.text.indexOf("*/", this.at + 2);
    if (end < 0) {
      throw new CommandError(
        "input",
        `디자인 토큰 CSS 의 ${String(this.line)} 줄 주석이 닫히지 않았다`,
      );
    }
    const body = this.text.slice(this.at + 2, end);
    this.advance(end + 2 - this.at);
    return body.trim();
  }

  /**
   * `;`, `{`, `}` 가운데 괄호·따옴표 밖에서 처음 나오는 것까지 읽는다. 글과 끝낸 글자를 낸다. 안의 주석은 버린다.
   */
  prelude(): { text: string; end: string } {
    let text = "";
    let depth = 0;
    let quote = "";
    while (!this.done()) {
      const character = this.peek();
      if (quote !== "") {
        text += this.advance();
        if (character === "\\") {
          text += this.advance();
        } else if (character === quote) {
          quote = "";
        }
        continue;
      }
      if (this.peek(2) === "/*") {
        this.comment();
        continue;
      }
      if (character === '"' || character === "'") {
        quote = character;
      } else if (character === "(" || character === "[") {
        depth += 1;
      } else if (character === ")" || character === "]") {
        depth -= 1;
      } else if (depth === 0 && (character === ";" || character === "{" || character === "}")) {
        return { text, end: character };
      }
      text += this.advance();
    }
    return { text, end: "" };
  }
}

function freeze(declaration: MutableDeclaration): Declaration {
  return {
    property: declaration.property,
    value: declaration.value,
    comment: declaration.comment,
    line: declaration.line,
  };
}

function parseDeclaration(text: string, line: number): MutableDeclaration | undefined {
  const colon = text.indexOf(":");
  if (colon < 0) {
    return undefined;
  }
  return {
    property: text.slice(0, colon).trim(),
    value: text.slice(colon + 1).trim(),
    comment: "",
    line,
    endLine: line,
  };
}

/** 위에서 아래로 한 번 읽어 스타일 규칙과 `@theme` 선언을 모은다. */
function parse(css: string): Parsed {
  const scanner = new Scanner(css);
  const rules: StyleRule[] = [];
  const themeStatic: Declaration[] = [];

  // 블록 하나를 읽고 그 블록에 바로 든 선언을 낸다. `}` 에서 끝난다(바깥 블록은 글 끝).
  const block = (context: readonly string[]): MutableDeclaration[] => {
    const declarations: MutableDeclaration[] = [];
    let last: MutableDeclaration | undefined;
    for (;;) {
      scanner.skipSpace();
      if (scanner.done()) {
        if (context.length > 0) {
          throw new CommandError("input", "디자인 토큰 CSS 의 블록이 닫히지 않았다");
        }
        return declarations;
      }
      if (scanner.peek(2) === "/*") {
        const startLine = scanner.line;
        const body = scanner.comment();
        if (last !== undefined && last.comment === "" && last.endLine === startLine) {
          last.comment = body;
        }
        continue;
      }
      if (scanner.peek() === "}") {
        if (context.length === 0) {
          throw new CommandError(
            "input",
            `디자인 토큰 CSS 의 ${String(scanner.line)} 줄에 짝 없는 } 가 있다`,
          );
        }
        scanner.advance();
        return declarations;
      }
      const startLine = scanner.line;
      const { text, end } = scanner.prelude();
      if (end === "{") {
        scanner.advance();
        const head = text.trim().replace(/\s+/g, " ");
        const inner = block([...context, head]);
        last = undefined;
        if (head.startsWith("@")) {
          if (/^@theme\b/.test(head) && !/\binline\b/.test(head)) {
            themeStatic.push(...inner.map(freeze));
          }
        } else {
          rules.push({ selectors: splitTopLevel(head), declarations: inner.map(freeze), context });
        }
        continue;
      }
      // `;` 나 `}` 앞에서 끝난 글. at-문(`@import`)이 아니면 선언이다.
      const declaration = text.trim().startsWith("@")
        ? undefined
        : parseDeclaration(text, startLine);
      if (end === ";") {
        scanner.advance();
      }
      if (declaration !== undefined) {
        declaration.endLine = scanner.line;
        declarations.push(declaration);
      }
      last = declaration;
      if (end === "") {
        throw new CommandError("input", "디자인 토큰 CSS 가 선언 중간에서 끝났다");
      }
    }
  };

  block([]);
  return { rules, themeStatic };
}

/** 괄호·따옴표 밖의 쉼표로 가른다. */
function splitTopLevel(text: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let quote = "";
  let current = "";
  for (const character of text) {
    if (quote !== "") {
      if (character === quote) {
        quote = "";
      }
    } else if (character === '"' || character === "'") {
      quote = character;
    } else if (character === "(" || character === "[") {
      depth += 1;
    } else if (character === ")" || character === "]") {
      depth -= 1;
    } else if (character === "," && depth === 0) {
      parts.push(current.trim());
      current = "";
      continue;
    }
    current += character;
  }
  parts.push(current.trim());
  return parts.filter((part) => part !== "");
}

type Specificity = readonly [number, number, number];

const ZERO: Specificity = [0, 0, 0];

function add(left: Specificity, right: Specificity): Specificity {
  return [left[0] + right[0], left[1] + right[1], left[2] + right[2]];
}

function compare(left: Specificity, right: Specificity): number {
  return left[0] - right[0] || left[1] - right[1] || left[2] - right[2];
}

/** 문서 뿌리에 단 속성. */
type Attributes = ReadonlyMap<string, string>;

/** 괄호 짝을 맞춰 `open` 위치의 `(` 를 닫는 `)` 의 위치. */
function closing(text: string, open: number): number {
  let depth = 0;
  for (let index = open; index < text.length; index += 1) {
    if (text[index] === "(") {
      depth += 1;
    } else if (text[index] === ")") {
      depth -= 1;
      if (depth === 0) {
        return index;
      }
    }
  }
  return -1;
}

const ATTRIBUTE = /^\[\s*([A-Za-z_-][\w-]*)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|([\w-]+))\s*)?\]/;

/** 복합 선택자 하나를 이루는 단순 선택자. */
type Simple =
  | { readonly kind: "root" }
  | { readonly kind: "host" }
  | { readonly kind: "attribute"; readonly name: string; readonly value: string | undefined }
  | { readonly kind: "not"; readonly arguments: readonly string[] }
  | { readonly kind: "tag"; readonly name: string }
  | { readonly kind: "universal" };

/** 복합 선택자를 단순 선택자로 가른다. 결합자가 든 선택자는 undefined 다. */
function simples(selector: string): Simple[] | undefined {
  const text = selector.trim();
  if (hasCombinator(text)) {
    return undefined;
  }
  const found: Simple[] = [];
  let at = 0;
  while (at < text.length) {
    const rest = text.slice(at);
    const functional = /^:(not|host)\(/.exec(rest);
    if (functional !== null) {
      const open = at + functional[0].length - 1;
      const end = closing(text, open);
      if (end < 0) {
        throw unsupported(selector);
      }
      found.push(
        functional[1] === "not"
          ? { kind: "not", arguments: splitTopLevel(text.slice(open + 1, end)) }
          : { kind: "host" },
      );
      at = end + 1;
    } else if (/^:host(?![\w-])/.test(rest)) {
      found.push({ kind: "host" });
      at += 5;
    } else if (/^:root(?![\w-])/.test(rest)) {
      found.push({ kind: "root" });
      at += 5;
    } else if (rest.startsWith("[")) {
      const attribute = ATTRIBUTE.exec(rest);
      if (attribute === null) {
        throw unsupported(selector);
      }
      found.push({
        kind: "attribute",
        name: attribute[1] ?? "",
        value: attribute[2] ?? attribute[3] ?? attribute[4],
      });
      at += attribute[0].length;
    } else if (rest.startsWith("*")) {
      found.push({ kind: "universal" });
      at += 1;
    } else {
      const tag = /^[A-Za-z][\w-]*/.exec(rest);
      if (tag === null) {
        throw unsupported(selector);
      }
      found.push({ kind: "tag", name: tag[0].toLowerCase() });
      at += tag[0].length;
    }
  }
  return found;
}

/** 선택자의 특정성. `:not(…)` 은 인자 가운데 가장 센 것이다(Selectors 4). */
function specificityOf(selector: string): Specificity {
  return (simples(selector) ?? []).reduce<Specificity>((total, simple) => {
    switch (simple.kind) {
      case "root":
      case "host":
      case "attribute":
        return add(total, [0, 1, 0]);
      case "not":
        return add(
          total,
          simple.arguments
            .map(specificityOf)
            .reduce((left, right) => (compare(left, right) >= 0 ? left : right), ZERO),
        );
      case "tag":
        return add(total, [0, 0, 1]);
      case "universal":
        return total;
    }
  }, ZERO);
}

/**
 * 선택자 하나가 문서 뿌리에 맞는지. 결합자가 든 선택자는 맞지 않는다(뿌리에는 조상도 형제도 없고, 결합자 오른쪽이
 * 주어다). `:host` 는 shadow 호스트에만 맞아 문서 뿌리에는 맞지 않는다.
 */
function matchesRoot(selector: string, attributes: Attributes): boolean {
  const parts = simples(selector);
  if (parts === undefined) {
    return false;
  }
  return parts.every((simple) => {
    switch (simple.kind) {
      case "root":
      case "universal":
        return true;
      case "host":
        return false;
      case "attribute": {
        const actual = attributes.get(simple.name);
        return actual !== undefined && (simple.value === undefined || actual === simple.value);
      }
      case "not":
        return !simple.arguments.some((argument) => matchesRoot(argument, attributes));
      case "tag":
        return simple.name === "html";
    }
  });
}

/** 선택자 목록 가운데 뿌리에 맞는 것의 가장 센 특정성. 맞는 것이 없으면 undefined. */
function matchRoot(selectors: readonly string[], attributes: Attributes): Specificity | undefined {
  return selectors
    .filter((selector) => matchesRoot(selector, attributes))
    .map(specificityOf)
    .reduce<Specificity | undefined>(
      (left, right) => (left === undefined || compare(right, left) > 0 ? right : left),
      undefined,
    );
}

function hasCombinator(selector: string): boolean {
  let depth = 0;
  for (const character of selector) {
    if (character === "(" || character === "[") {
      depth += 1;
    } else if (character === ")" || character === "]") {
      depth -= 1;
    } else if (
      depth === 0 &&
      (/\s/.test(character) || character === ">" || character === "+" || character === "~")
    ) {
      return true;
    }
  }
  return false;
}

function unsupported(selector: string): CommandError {
  return new CommandError("input", `디자인 토큰 CSS 의 선택자를 풀 수 없다: ${selector}`);
}

interface Candidate {
  readonly declaration: Declaration;
  /** 레이어 밖이면 무한대, 안이면 레이어가 처음 나온 차례. 큰 쪽이 이긴다. */
  readonly layer: number;
  readonly specificity: Specificity;
  readonly order: number;
}

function beats(challenger: Candidate, holder: Candidate): boolean {
  if (challenger.layer !== holder.layer) {
    return challenger.layer > holder.layer;
  }
  const bySpecificity = compare(challenger.specificity, holder.specificity);
  if (bySpecificity !== 0) {
    return bySpecificity > 0;
  }
  return challenger.order > holder.order;
}

const THEME_KEY = /\[\s*data-theme\s*=\s*["']?([^"'\]\s]+)["']?\s*\]/g;

/** 디자인 토큰 CSS 를 푼다. 풀 수 없으면 `input` 오류다. */
export function parseThemeCss(css: string): ThemeCss {
  const { rules, themeStatic } = parse(css);

  const themes: string[] = [];
  for (const rule of rules) {
    for (const selector of rule.selectors) {
      for (const found of selector.matchAll(THEME_KEY)) {
        const key = found[1] ?? "";
        if (!themes.includes(key)) {
          themes.push(key);
        }
      }
    }
  }

  const layers: string[] = [];
  const cascading = rules.flatMap((rule, order) => {
    if (rule.context.some((head) => !head.startsWith("@layer"))) {
      return [];
    }
    const custom = rule.declarations.filter((declaration) => declaration.property.startsWith("--"));
    if (custom.length === 0) {
      return [];
    }
    const layerHead = rule.context.findLast((head) => head.startsWith("@layer"));
    if (layerHead !== undefined && !layers.includes(layerHead)) {
      layers.push(layerHead);
    }
    const layer = layerHead === undefined ? Number.POSITIVE_INFINITY : layers.indexOf(layerHead);
    return [{ rule, custom, layer, order }];
  });

  const winners = (theme: string, mode: Mode): ReadonlyMap<string, Declaration> => {
    const attributes: Attributes = new Map([
      ["data-theme", theme],
      ["data-mode", mode],
    ]);
    const held = new Map<string, Candidate>();
    for (const { rule, custom, layer, order } of cascading) {
      const specificity = matchRoot(rule.selectors, attributes);
      if (specificity === undefined) {
        continue;
      }
      for (const declaration of custom) {
        const challenger: Candidate = { declaration, layer, specificity, order };
        const holder = held.get(declaration.property);
        if (holder === undefined || beats(challenger, holder)) {
          held.set(declaration.property, challenger);
        }
      }
    }
    const ordered = [...held.values()].sort(
      (left, right) => left.declaration.line - right.declaration.line,
    );
    return new Map(
      ordered.map((candidate) => [candidate.declaration.property, candidate.declaration]),
    );
  };

  return {
    themes,
    themeStatic: new Map(themeStatic.map((declaration) => [declaration.property, declaration])),
    winners,
  };
}
