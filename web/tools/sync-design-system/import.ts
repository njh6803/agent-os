/**
 * 들이기 명령. 웹의 `tokens.json`, 기준본, 지금 디자인 토큰 CSS 를 셋으로 맞대, 웹만 바뀐 값과 설명을 디자인 토큰 CSS 의
 * 그 줄로 옮기고 나머지는 사람에게 물을 목록으로 낸다(design-reverse-sync 명세 "거꾸로 동기화", ADR 0025 의
 * 2026-10-21 이력 "옮기는 규칙"). 옮긴 뒤의 여덟 벌을 명암비 모듈(`@agent-os/ui/contrast`)로 판정하고, 걸리면 가장 가까운
 * 통과 값을 낸다. 같은 입력과 답에는 같은 결과다.
 *
 * - 맞대기: 기준본과 웹, 기준본과 코드(지금 디자인 토큰 CSS 로 지은 것)의 차이(`tokens-json.ts`)를 자리마다 본다. 웹만
 *   바뀌었으면 웹 편집, 코드만 바뀌었으면 들일 것이 없음(`codeOnly`), 둘이 같은 값으로 바뀌었으면 이미 들인 것
 *   (`alreadyImported`), 둘이 다르게 바뀌었으면 묻는다(`conflict`). 기준본이 어디서 왔는지(기록, 이어받는 claim)는 모른다.
 * - 자리: 색 값은 벌마다 문서 뿌리에서 이기는 선언(`theme-css.ts`)의 줄이고, 그 줄을 나누는 벌이 한 자리다(원색은 한
 *   테마의 라이트·다크, 반투명은 여덟 벌). 자리의 모든 벌이 같은 값으로 바뀌었을 때만 옮긴다. 설명은 첫 벌에서 이기는 선언의
 *   줄, 글자 크기·줄 높이·굵기와 간격·모서리는 `@theme` 의 그 줄이다. 자리 id 는 색 값이 `color/<토큰>@<벌>+<벌>`, 다른
 *   값과 설명이 `<계열>/<토큰>`·`<계열>/<토큰>#<칸>` 이다.
 * - 옮기는 값: hex 는 6·8 자리로 펴고(`#rrggbbff` 도 그대로), 색 함수는 sRGB 안이면 hex 로 바꾼다(`color.ts`). 크기는 px 와
 *   `0`, 굵기는 수 하나만 옮긴다. 소수 끝에 0 이 붙은 px(`20.50px`)는 Prettier 가 고쳐 써 포맷 검사에 걸리고 고쳐 쓰면 다시
 *   지은 값이 웹 값과 글자가 달라지므로 옮기지 않는다. 설명은 선언을 끝낸 `;` 뒤의 주석으로 옮기고, 비우면 그 주석을 지운다.
 * - 묻는 것(`reason`): 둘이 다르게 바뀐 것(`conflict`. 웹 값을 옮기지 못하면 그 까닭을 `webReason` 에 든다), 쓰임새 토큰의
 *   대응(`mapping`, 별칭이 아닌 값으로 바꾼 것 포함),
 *   자리의 일부 벌만 바꾸거나 벌마다 다르게 바꾼 것(`partial`), 원색·반투명을 별칭으로 바꾼 것(`alias`), sRGB 밖
 *   (`outOfGamut`), `lab()`·`lch()`·`color()`(`colorSpace`), 읽지 못하는 색 함수(`unreadableColor`), 불투명한 쓰임새 토큰이
 *   가리키는 원색에 투명도를 준 것(`alpha`), 위에서 옮기는 꼴 밖의 크기와 단위 없는 줄 높이(`unit`), 굵기 범위(`weightRange`), 주석을
 *   끝내는 글자·줄바꿈·앞뒤 공백이 든 설명(`usageText`), 옮길 한 줄 선언이 없는 것(`noLine`, 그림자와 다른 계열 포함), 토큰·글자 묶음·
 *   벌·계열의 더하기와 지우기(`added`, `removed`. 한 계열에서 토큰을 더하고 지웠으면 이름을 바꾼 것일 수 있다고 적는다),
 *   글자 스타일의 다른 칸(`typeField`), 계열·글자 묶음의 설명(`familyNote`).
 * - 판정: 옮긴 뒤의 벌마다 짝 표를 잰다. 걸린 짝에 든 옮긴 원색마다, 다른 옮긴 값을 둔 채 그 원색만 바꿔 그 원색이 드는
 *   벌에서 그 원색을 풀어 쓰는 짝을 모두 지나는 첫 값을 낸다. 불투명한 원색은 웹 값의 OKLCH 밝기를 0.001 씩 양쪽으로
 *   옮겨(차이가 같으면 밝은 쪽 먼저) sRGB 안의 hex 를 본다. 투명도가 1 이 아닌 원색은 색을 두고 투명도를 1/255 씩 옮긴다
 *   (차이가 같으면 투명한 쪽 먼저). 없으면 제안 값이 null 이다.
 * - 답: `{"<자리 id>": "web" | "code" | "suggested"}`. 둘이 다르게 바뀐 자리는 "web"(웹 값을 옮길 수 있을 때)과 "code",
 *   제안이 난 자리는 "code" 와 "suggested"(제안 값이 있을 때)를 받는다(명세 "판정"의 세 선택지 가운데 "웹에서 다시 고친다"는
 *   답 파일에 없다). 둘이 다르게 바뀐 자리에서 "web" 이나 "suggested" 를 고르면 웹 값을 옮겨 판정하므로, 거기서 제안이 나면
 *   그 자리는 "web"·"code" 와, 제안 값이 있으면 "suggested" 를 받는다. 이번 들이기에 없는 자리나 그 자리에서 고를 수 없는
 *   답은 `input` 오류다.
 *
 * 명령: `import --web <tokens.json> --base <tokens.json> [--css <디자인 토큰 CSS>] --out <디자인 토큰 CSS>
 * [--answers <답 JSON>]`. CSS 를 주지 않으면 패키지의 디자인 토큰 CSS 를 읽는다. 바뀐 것이 없어도 `--out` 을 쓴다. 보고는
 * 쓴 파일의 절대 경로(`out`)와 `ImportReport` 의 칸이다.
 *
 * 못 보는 것: 옮길 줄은 `--이름: 값;` 과 같은 줄에서 닫히는 주석 하나까지만 고친다. 여러 줄에 걸친 선언, 한 줄의 여러 선언,
 * 값 안의 `;` 는 `noLine` 으로 묻는다. 코드의 쓰임새 토큰이 풀리지 않거나(없는 토큰, 도는 별칭), sRGB 의 hex 로 읽지 못하는
 * 원색을 가리키거나, 불투명해야 할 자리에 반투명이 오면 판정하지 못해 `input` 오류다. 제안의 방식은 옮긴 값이 투명한지로
 * 가른다. 반투명 원색(오버레이)을 웹이 불투명하게 바꾸면(투명도가 ff 로 반올림되는 0.999 포함) 밝기로 제안하고, 투명도를
 * 되돌리는 제안은 내지 않는다.
 */

import { parseArgs } from "node:util";
import {
  CONTRAST_PAIRS,
  measureContrast,
  SEMANTIC_TOKENS,
  TRANSLUCENT_TOKENS,
  type ContrastPair,
  type PairMeasure,
  type SemanticToken,
} from "@agent-os/ui/contrast";
import { buildTokensFile, DEFAULT_CSS, pageThemes, type Bench } from "./build.ts";
import {
  expandHex,
  nearestByAlpha,
  nearestByLightness,
  readColor,
  readOklch,
  toHex,
} from "./color.ts";
import {
  CommandError,
  messageOf,
  parsedArgs,
  readInput,
  writeOutput,
  type ReportFields,
} from "./command.ts";
import { parseThemeCss, type Declaration } from "./theme-css.ts";
import {
  diffTokens,
  readTokens,
  valueAt,
  type CanonicalTokens,
  type JsonValue,
  type TokenDiff,
} from "./tokens-json.ts";

/** 사람이 고르는 답. 웹 값, 코드 값, 제안 값이다. */
export const CHOICES = ["web", "code", "suggested"] as const;

export type Choice = (typeof CHOICES)[number];

/** 묻는 까닭. 뜻은 모듈 독스트링의 "묻는 것"이다. */
export const ASK_REASONS = [
  "conflict",
  "mapping",
  "partial",
  "alias",
  "outOfGamut",
  "colorSpace",
  "unreadableColor",
  "alpha",
  "unit",
  "weightRange",
  "usageText",
  "noLine",
  "added",
  "removed",
  "typeField",
  "familyNote",
] as const;

export type AskReason = (typeof ASK_REASONS)[number];

const RENAME_NOTE = "이름을 바꾼 것일 수 있다";
const ALIAS_DEPTH = 32;
const PIXELS = /^-?\d+(?:\.\d*[1-9])?px$|^0$/;
const LINE = /^(\s*)(--[A-Za-z0-9_.-]+)(\s*:\s*)([^;]*?)\s*;(.*)$/;
const TRAILING_COMMENT = /^\s*\/\*(.*)\*\/\s*$/;

/**
 * 옮긴 것 하나. `line` 은 고친 줄, `before` 는 그 줄의 옛 값(설명이면 옛 주석), `after` 는 쓴 값, `web` 은 웹의 값(정규
 * 꼴. 색 함수면 바꾸기 전의 글)이다. `themes` 는 색 값이 옮겨진 벌이고 다른 것은 비어 있다.
 */
export type Moved = {
  readonly id: string;
  readonly family: string;
  readonly token: string;
  readonly field: string;
  readonly themes: readonly string[];
  readonly line: number;
  readonly before: string;
  readonly after: string;
  readonly web: string;
};

/** 묻는 자리의 한 벌(색 값이 아니면 `theme` 이 null)에서 기준본, 웹, 코드의 값. 없는 쪽은 null 이다. */
export type Change = {
  readonly theme: string | null;
  readonly base: JsonValue;
  readonly web: JsonValue;
  readonly code: JsonValue;
};

/**
 * 묻는 것 하나. `choices` 는 답 파일로 고를 수 있는 답이고, 비었으면 들이기 세션이 고친다(07 의 스킬). `webReason` 은 둘이
 * 다르게 바뀐 자리(`conflict`)에서 스크립트가 웹 값을 옮기지 못하는 까닭이고, 그때 `choices` 에 "web" 이 없다. 사람이 웹
 * 값을 고르면 들이기 세션이 그 까닭의 묻는 것처럼 고친다. 다른 자리는 null 이다.
 */
export type Asked = {
  readonly id: string;
  readonly reason: AskReason;
  readonly family: string;
  readonly token: string | null;
  readonly group: string | null;
  readonly field: string | null;
  readonly themes: readonly string[];
  readonly changes: readonly Change[];
  readonly choices: readonly Choice[];
  readonly webReason: AskReason | null;
  readonly note: string;
};

/** 들일 것이 없는 차이 하나(이미 들인 것, 코드만 바뀐 것). `before` 는 기준본, `after` 는 웹이나 코드의 값이다. */
export type Settled = {
  readonly id: string;
  readonly family: string;
  readonly token: string | null;
  readonly theme: string | null;
  readonly field: string | null;
  readonly before: JsonValue;
  readonly after: JsonValue;
};

/** 걸린 짝 하나. `ratio` 는 둘째 자리에서 내린 명암비, `tokens` 는 그 짝이 풀어 쓰는 옮긴 원색의 자리 id 다. */
export type Failure = {
  readonly theme: string;
  readonly foreground: string;
  readonly surface: string;
  readonly ratio: number;
  readonly minimum: number;
  readonly tokens: readonly string[];
};

/**
 * 옮긴 원색 하나의 가장 가까운 통과 값. `from` 은 옮긴 값, `steps` 는 옮긴 단계(밝기 0.001 이나 투명도 1/255, 밝거나
 * 불투명한 쪽이 양수)다. 통과하는 값이 없으면 `steps`·`value` 가 null 이다.
 */
export type Suggestion = {
  readonly id: string;
  readonly token: string;
  readonly themes: readonly string[];
  readonly from: string;
  readonly by: "lightness" | "alpha";
  readonly steps: number | null;
  readonly value: string | null;
};

/** 답을 따른 것 하나. `value` 는 그 답으로 남은 값이다. */
export type Answered = { readonly id: string; readonly choice: Choice; readonly value: JsonValue };

export type ImportReport = {
  /** 디자인 토큰 CSS 가 바뀌었는지. */
  readonly changed: boolean;
  readonly moved: readonly Moved[];
  readonly asked: readonly Asked[];
  readonly alreadyImported: readonly Settled[];
  readonly codeOnly: readonly Settled[];
  readonly contrast: {
    /** 잰 짝의 수(벌 × 짝 표). */
    readonly measured: number;
    readonly failures: readonly Failure[];
    readonly suggestions: readonly Suggestion[];
  };
  readonly answered: readonly Answered[];
};

export interface ImportInput {
  readonly css: string;
  /** 기준본 `tokens.json` 을 JSON 으로 푼 값. */
  readonly base: unknown;
  /** 웹의 `tokens.json` 을 JSON 으로 푼 값. */
  readonly web: unknown;
  readonly answers: Readonly<Record<string, string>>;
}

export interface ImportResult {
  /** 고친 디자인 토큰 CSS. */
  readonly css: string;
  readonly report: ImportReport;
}

/** 지금 디자인 토큰 CSS. */
interface Code {
  readonly benches: readonly Bench[];
  readonly themeStatic: ReadonlyMap<string, Declaration>;
  readonly tokens: CanonicalTokens;
  readonly lines: readonly string[];
}

/** 웹이 기준본과 다르고 코드가 웹과 다른 차이 하나. */
interface Pending {
  readonly diff: TokenDiff;
  readonly code: JsonValue;
  /** 코드도 기준본과 다르다(둘이 다르게 바뀌었다). */
  readonly conflict: boolean;
}

/** 디자인 토큰 CSS 의 한 줄에 옮길 자리. 색 값은 그 줄을 나누는 벌의 차이를 모으고, 나머지는 차이 하나다. */
interface Slot {
  readonly id: string;
  readonly diff: TokenDiff;
  readonly entries: Pending[];
  /** 색 값이면 자리의 벌, 아니면 비었다. */
  readonly benches: readonly string[];
  readonly declaration: Declaration | undefined;
}

/** 고칠 수 있는 한 줄 선언. 줄을 `head` + 값 + `;` + `tail` + `end` 로 다시 쓴다. */
interface LineParts {
  readonly line: number;
  readonly head: string;
  readonly value: string;
  readonly comment: string;
  readonly tail: string;
  readonly end: string;
}

type Decision =
  { readonly text: string; readonly parts: LineParts } | { readonly reason: AskReason };

/** 자리 하나의 결정. 묻는 것이면 `ask`, 옮기면 `move` 다. 둘이 다르게 바뀐 자리는 웹 값을 고르면 옮길 `move` 를 함께 든다. */
interface Plan {
  readonly slot: Slot;
  readonly ask:
    | {
        readonly reason: AskReason;
        readonly choices: readonly Choice[];
        readonly webReason: AskReason | null;
      }
    | undefined;
  readonly move: { readonly text: string; readonly parts: LineParts } | undefined;
}

/** 옮길 것 하나. */
interface Move {
  readonly slot: Slot;
  readonly text: string;
  readonly parts: LineParts;
}

/** `<토큰>@<벌>` 에서 옮긴 색 값. */
type ColorMoves = ReadonlyMap<string, string>;

/** 쓰임새 토큰을 한 벌에서 푼 값과, 풀며 거친 토큰의 이름. */
interface Resolved {
  readonly hex: string;
  readonly names: readonly string[];
}

function same(left: JsonValue, right: JsonValue): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function moveKey(token: string, bench: string): string {
  return `${token}@${bench}`;
}

function isColorValue(diff: TokenDiff): boolean {
  return diff.kind === "value" && diff.family === "color" && diff.token !== undefined;
}

/** 차이가 가리키는 자리의 id. 색 값은 벌 하나의 id 이고, 자리는 `slotsOf` 가 벌을 모아 다시 짓는다. */
function idOf(diff: TokenDiff): string {
  const { kind, family, token, theme, group, field } = diff;
  if (token !== undefined) {
    const named = `${family}/${token}`;
    if (kind === "added" || kind === "removed") {
      return named;
    }
    if (kind === "usage") {
      return `${named}#usage`;
    }
    if (field !== undefined) {
      return `${named}#${field}`;
    }
    return theme === undefined ? named : `${named}@${theme}`;
  }
  if (group !== undefined) {
    const named = `${family}/group:${group}`;
    if (kind === "added" || kind === "removed") {
      return named;
    }
    return `${named}#${kind === "familyNote" ? "note" : (field ?? "")}`;
  }
  if (theme !== undefined) {
    return `${family}@${theme}`;
  }
  if (kind === "familyNote") {
    return `${family}#note`;
  }
  return field === undefined ? family : `${family}#${field}`;
}

/** 차이의 칸. 값은 `value`(글자 스타일이면 그 칸), 설명은 `usage`, 계열·묶음 설명은 `note` 다. */
function fieldOf(diff: TokenDiff): string | null {
  switch (diff.kind) {
    case "value":
      return diff.field ?? "value";
    case "usage":
      return "usage";
    case "familyNote":
      return "note";
    case "typeField":
      return diff.field ?? null;
    case "added":
    case "removed":
      return null;
  }
}

function settled(diff: TokenDiff, after: JsonValue): Settled {
  return {
    id: idOf(diff),
    family: diff.family,
    token: diff.token ?? null,
    theme: diff.theme ?? null,
    field: fieldOf(diff),
    before: diff.before,
    after,
  };
}

/** 차이를 옮길 디자인 토큰 CSS 의 선언. 색 값은 그 벌, 색 설명은 첫 벌에서 이기는 선언이다. */
function declarationOf(code: Code, diff: TokenDiff): Declaration | undefined {
  const { kind, family, token, theme, field } = diff;
  if (token === undefined || (kind !== "value" && kind !== "usage")) {
    return undefined;
  }
  if (family === "color") {
    const bench =
      kind === "usage" ? code.benches[0] : code.benches.find((item) => item.theme.id === theme);
    return bench?.winners.get(`--${token}`);
  }
  if (family === "spacing" || family === "radius") {
    return code.themeStatic.get(`--${token}`);
  }
  if (family !== "type") {
    return undefined;
  }
  const suffix =
    kind === "usage" || field === "fontSize"
      ? ""
      : field === "lineHeight"
        ? "--line-height"
        : field === "fontWeight"
          ? "--font-weight"
          : undefined;
  return suffix === undefined ? undefined : code.themeStatic.get(`--${token}${suffix}`);
}

/** 선언의 줄을 고칠 수 있으면 그 조각. 한 줄에 선언 하나와 그 줄에서 닫히는 주석 하나까지만 받는다. */
function lineParts(code: Code, declaration: Declaration): LineParts | undefined {
  const raw = code.lines[declaration.line - 1] ?? "";
  const end = raw.endsWith("\r") ? "\r" : "";
  const found = LINE.exec(end === "" ? raw : raw.slice(0, -1));
  if (found === null || found[2] !== declaration.property || found[4] !== declaration.value) {
    return undefined;
  }
  const tail = found[5] ?? "";
  if (tail.trim() !== "") {
    const comment = TRAILING_COMMENT.exec(tail);
    if (comment === null || (comment[1] ?? "").includes("*/")) {
      return undefined;
    }
  }
  return {
    line: declaration.line,
    head: `${found[1] ?? ""}${found[2]}${found[3] ?? ""}`,
    value: declaration.value,
    comment: declaration.comment,
    tail,
    end,
  };
}

/** 웹의 차이를 자리로 모은다. 차례는 자리의 첫 차이가 나온 차례다. */
function slotsOf(code: Code, pending: readonly Pending[]): Slot[] {
  const slots = new Map<string, Slot>();
  for (const entry of pending) {
    const { diff } = entry;
    const declaration = declarationOf(code, diff);
    let id = idOf(diff);
    let benches: readonly string[] = [];
    if (isColorValue(diff)) {
      benches =
        declaration === undefined
          ? [diff.theme ?? ""]
          : code.benches
              .filter((bench) => bench.winners.get(declaration.property)?.line === declaration.line)
              .map((bench) => bench.theme.id);
      id = `color/${diff.token ?? ""}@${benches.join("+")}`;
    }
    const found = slots.get(id);
    if (found === undefined) {
      slots.set(id, { id, diff, entries: [entry], benches, declaration });
    } else {
      found.entries.push(entry);
    }
  }
  return [...slots.values()];
}

/** 색 토큰의 한 벌의 값(정규 꼴). */
function colorOf(tokens: CanonicalTokens, name: string, bench: string): string | undefined {
  const value = tokens.families.get("color")?.tokens.get(name)?.value;
  return typeof value === "string" ? value : value?.get(bench);
}

/** 웹의 색 값을 옮길 hex. 옮기지 못하면 묻는 까닭이다. */
function colorText(value: string): { readonly hex: string } | { readonly reason: AskReason } {
  if (value.startsWith("{")) {
    return { reason: "alias" };
  }
  const expanded = expandHex(value);
  if (expanded !== undefined) {
    return { hex: expanded };
  }
  const color = readColor(value);
  if (color === undefined) {
    return { reason: /^(?:lab|lch|color)\(/.test(value) ? "colorSpace" : "unreadableColor" };
  }
  const hex = toHex(color);
  return hex === undefined ? { reason: "outOfGamut" } : { hex };
}

function translucent(hex: string): boolean {
  return hex.length === 9 && !hex.endsWith("ff");
}

/** 한 벌에서 토큰을 풀며 거치는 이름. 풀리지 않으면 거기서 멈춘다. */
function chainOf(tokens: CanonicalTokens, name: string, bench: string): string[] {
  const names = [name];
  let value = colorOf(tokens, name, bench);
  while (value?.startsWith("{") === true && names.length < ALIAS_DEPTH) {
    const next = value.slice(1, -1);
    names.push(next);
    value = colorOf(tokens, next, bench);
  }
  return names;
}

/** 자리의 벌에서 불투명한 쓰임새 토큰이 이 원색을 풀어 쓰는지. */
function opaqueUse(code: Code, slot: Slot): boolean {
  const translucentTokens: readonly string[] = TRANSLUCENT_TOKENS;
  const token = slot.diff.token ?? "";
  return slot.benches.some((bench) =>
    SEMANTIC_TOKENS.some(
      (name) =>
        !translucentTokens.includes(name) && chainOf(code.tokens, name, bench).includes(token),
    ),
  );
}

/** 자리의 벌마다 기준본, 웹, 코드의 값. */
function benchValues(
  slot: Slot,
  base: CanonicalTokens,
  web: CanonicalTokens,
  code: Code,
): {
  readonly theme: string;
  readonly base: JsonValue;
  readonly web: JsonValue;
  readonly code: JsonValue;
}[] {
  return slot.benches.map((theme) => {
    const at: TokenDiff = { ...slot.diff, theme };
    return {
      theme,
      base: valueAt(base, at),
      web: valueAt(web, at),
      code: valueAt(code.tokens, at),
    };
  });
}

/** 웹 값을 옮길지, 옮기지 못하면 묻는 까닭. 둘이 다르게 바뀌었는지는 보지 않는다. */
function decide(slot: Slot, base: CanonicalTokens, web: CanonicalTokens, code: Code): Decision {
  const { kind, family, field, after } = slot.diff;
  if (kind === "added" || kind === "removed" || kind === "typeField" || kind === "familyNote") {
    return { reason: kind };
  }
  const parts = slot.declaration === undefined ? undefined : lineParts(code, slot.declaration);
  if (parts === undefined) {
    return { reason: "noLine" };
  }
  const value = typeof after === "string" ? after : "";
  if (kind === "usage") {
    return value.includes("*/") || /[\n\r\f\u2028\u2029]/.test(value) || value !== value.trim()
      ? { reason: "usageText" }
      : { text: value, parts };
  }
  if (family === "color") {
    const values = benchValues(slot, base, web, code);
    if (values.some((item) => typeof item.code === "string" && item.code.startsWith("{"))) {
      return { reason: "mapping" };
    }
    const webValues = new Set(values.map((item) => JSON.stringify(item.web)));
    if (values.some((item) => same(item.web, item.base)) || webValues.size > 1) {
      return { reason: "partial" };
    }
    const color = colorText(value);
    if ("reason" in color) {
      return color;
    }
    return translucent(color.hex) && opaqueUse(code, slot)
      ? { reason: "alpha" }
      : { text: color.hex, parts };
  }
  if (field === "fontWeight") {
    return /^\d+$/.test(value) ? { text: value, parts } : { reason: "weightRange" };
  }
  return PIXELS.test(value) ? { text: value, parts } : { reason: "unit" };
}

/** 자리마다 결정한다(답을 보기 전). */
function plansOf(
  slots: readonly Slot[],
  base: CanonicalTokens,
  web: CanonicalTokens,
  code: Code,
): Plan[] {
  return slots.map((slot) => {
    const decision = decide(slot, base, web, code);
    const move = "text" in decision ? decision : undefined;
    if (slot.entries.some((entry) => entry.conflict)) {
      const webReason = "reason" in decision ? decision.reason : null;
      const choices: readonly Choice[] = move === undefined ? ["code"] : ["web", "code"];
      return { slot, ask: { reason: "conflict", choices, webReason }, move };
    }
    return "reason" in decision
      ? { slot, ask: { reason: decision.reason, choices: [], webReason: null }, move }
      : { slot, ask: undefined, move };
  });
}

function pairTokens(pair: ContrastPair): SemanticToken[] {
  const [foreground, surface] = pair;
  return [foreground, ...(typeof surface === "string" ? [surface] : surface)];
}

/** 한 벌에서 토큰을 푼다. 옮긴 값이 코드의 값을 덮는다. 풀 수 없으면 `input` 오류다. */
function resolve(
  tokens: CanonicalTokens,
  moves: ColorMoves,
  name: string,
  bench: string,
): Resolved {
  const names: string[] = [];
  let current = name;
  while (names.length < ALIAS_DEPTH) {
    names.push(current);
    const value = moves.get(moveKey(current, bench)) ?? colorOf(tokens, current, bench);
    if (value === undefined) {
      throw new CommandError("input", `${bench} 에서 ${name} 를 풀 수 없다: ${current} 가 없다`);
    }
    if (!value.startsWith("{")) {
      const color = readColor(value);
      const hex = color === undefined ? undefined : toHex(color);
      if (hex === undefined) {
        throw new CommandError(
          "input",
          `${bench} 의 ${current} 값 ${value} 를 sRGB 의 hex 로 읽을 수 없어 판정하지 못한다`,
        );
      }
      return { hex, names };
    }
    current = value.slice(1, -1);
  }
  throw new CommandError(
    "input",
    `${bench} 에서 ${name} 를 푸는 별칭이 ${String(ALIAS_DEPTH)} 번을 넘게 이어진다`,
  );
}

/** 한 벌의 토큰을 푸는 함수. 푼 값을 기억한다. */
function benchView(
  tokens: CanonicalTokens,
  moves: ColorMoves,
  bench: string,
): (name: string) => Resolved {
  const cache = new Map<string, Resolved>();
  return (name) => {
    const found = cache.get(name);
    if (found !== undefined) {
      return found;
    }
    const resolved = resolve(tokens, moves, name, bench);
    cache.set(name, resolved);
    return resolved;
  };
}

/** 한 벌의 짝을 잰다. 명암비 모듈이 값의 꼴로 멈추면(불투명해야 할 자리의 반투명) `input` 오류다. */
function measure(
  view: (name: string) => Resolved,
  bench: string,
  pairs: readonly ContrastPair[],
): PairMeasure[] {
  try {
    return measureContrast((name) => view(name).hex, pairs);
  } catch (error) {
    if (error instanceof CommandError || !(error instanceof Error)) {
      throw error;
    }
    throw new CommandError("input", `${bench} 의 명암비를 잴 수 없다: ${error.message}`);
  }
}

/** 옮긴 뒤의 벌을 모두 판정한다. `owners` 는 `<토큰>@<벌>` 에서 그 값을 옮긴 자리의 id 다. */
function judge(
  tokens: CanonicalTokens,
  moves: ColorMoves,
  owners: ReadonlyMap<string, string>,
  benches: readonly string[],
): Failure[] {
  return benches.flatMap((bench) => {
    const view = benchView(tokens, moves, bench);
    return measure(view, bench, CONTRAST_PAIRS).flatMap(({ pair, surface, ratio }) => {
      const [foreground, , minimum] = pair;
      if (ratio >= minimum) {
        return [];
      }
      const names = pairTokens(pair).flatMap((name) => view(name).names);
      const owned = names.flatMap((name) => {
        const owner = owners.get(moveKey(name, bench));
        return owner === undefined ? [] : [owner];
      });
      return [
        {
          theme: bench,
          foreground,
          surface,
          ratio: Math.floor(ratio * 100) / 100,
          minimum,
          tokens: [...new Set(owned)],
        },
      ];
    });
  });
}

/** 옮길 것의 웹 값(정규 꼴. 색 함수면 hex 로 바꾸기 전의 글). 글이 아니면 옮길 글이다. */
function webTextOf({ slot, text }: Move): string {
  return typeof slot.diff.after === "string" ? slot.diff.after : text;
}

/** 옮긴 원색 하나의 가장 가까운 통과 값. 다른 옮긴 값을 둔 채 그 원색이 드는 벌에서 그 원색을 풀어 쓰는 짝을 본다. */
function suggest(tokens: CanonicalTokens, moves: ColorMoves, move: Move): Suggestion {
  const { slot, text } = move;
  const token = slot.diff.token ?? "";
  const pairs = slot.benches.map((bench) => {
    const view = benchView(tokens, moves, bench);
    return {
      bench,
      pairs: CONTRAST_PAIRS.filter((pair) =>
        pairTokens(pair).some((name) => view(name).names.includes(token)),
      ),
    };
  });
  const passes = (hex: string): boolean => {
    const trial = new Map(moves);
    for (const bench of slot.benches) {
      trial.set(moveKey(token, bench), hex);
    }
    return pairs.every(({ bench, pairs: judged }) =>
      measure(benchView(tokens, trial, bench), bench, judged).every(
        ({ pair, ratio }) => ratio >= pair[2],
      ),
    );
  };
  const alpha = translucent(text);
  const origin = readOklch(webTextOf(move));
  const found = alpha
    ? nearestByAlpha(text, passes)
    : origin === undefined
      ? undefined
      : nearestByLightness(origin, passes);
  return {
    id: slot.id,
    token,
    themes: slot.benches,
    from: text,
    by: alpha ? "alpha" : "lightness",
    steps: found?.steps ?? null,
    value: found?.value ?? null,
  };
}

/** 옮길 것 가운데 색 값과, 그 값을 옮긴 자리. */
function colorMoves(moves: readonly Move[]): {
  readonly values: ColorMoves;
  readonly owners: ReadonlyMap<string, string>;
} {
  const values = new Map<string, string>();
  const owners = new Map<string, string>();
  for (const { slot, text } of moves) {
    if (!isColorValue(slot.diff)) {
      continue;
    }
    for (const bench of slot.benches) {
      values.set(moveKey(slot.diff.token ?? "", bench), text);
      owners.set(moveKey(slot.diff.token ?? "", bench), slot.id);
    }
  }
  return { values, owners };
}

/** 판정하고, 걸린 짝에 든 옮긴 원색마다 가장 가까운 통과 값을 낸다. */
function contrastOf(
  code: Code,
  moves: readonly Move[],
): { readonly failures: Failure[]; readonly suggestions: Suggestion[] } {
  const { values, owners } = colorMoves(moves);
  const benches = code.benches.map((bench) => bench.theme.id);
  const failures = judge(code.tokens, values, owners, benches);
  const failing = new Set(failures.flatMap((failure) => failure.tokens));
  const suggestions = moves
    .filter((move) => failing.has(move.slot.id))
    .map((move) => suggest(code.tokens, values, move));
  return { failures, suggestions };
}

/** 옮길 것을 디자인 토큰 CSS 에 쓴다. 한 줄의 값과 설명은 한 번에 고친다. */
function written(code: Code, moves: readonly Move[]): string {
  const edits = new Map<number, { parts: LineParts; value?: string; usage?: string }>();
  for (const { slot, text, parts } of moves) {
    const edit = edits.get(parts.line) ?? { parts };
    if (slot.diff.kind === "usage") {
      edit.usage = text;
    } else {
      edit.value = text;
    }
    edits.set(parts.line, edit);
  }
  return code.lines
    .map((line, index) => {
      const edit = edits.get(index + 1);
      if (edit === undefined) {
        return line;
      }
      const { parts, value = parts.value, usage } = edit;
      const tail = usage === undefined ? parts.tail : usage === "" ? "" : ` /* ${usage} */`;
      return `${parts.head}${value};${tail}${parts.end}`;
    })
    .join("\n");
}

function movedOf(move: Move): Moved {
  const { slot, text, parts } = move;
  const usage = slot.diff.kind === "usage";
  return {
    id: slot.id,
    family: slot.diff.family,
    token: slot.diff.token ?? "",
    field: fieldOf(slot.diff) ?? "value",
    themes: slot.benches,
    line: parts.line,
    before: usage ? parts.comment : parts.value,
    after: text,
    web: webTextOf(move),
  };
}

/** 한 계열에서 토큰을 더하고 지운 계열. 이름을 바꾼 것일 수 있다. */
function renamedFamilies(pending: readonly Pending[]): Set<string> {
  const kinds = (kind: string): Set<string> =>
    new Set(
      pending
        .filter(({ diff }) => diff.kind === kind && diff.token !== undefined)
        .map(({ diff }) => diff.family),
    );
  const added = kinds("added");
  return new Set([...kinds("removed")].filter((family) => added.has(family)));
}

function askedOf(
  slot: Slot,
  ask: NonNullable<Plan["ask"]>,
  base: CanonicalTokens,
  web: CanonicalTokens,
  code: Code,
  renamed: ReadonlySet<string>,
): Asked {
  const { diff } = slot;
  const changes: Change[] =
    slot.benches.length === 0
      ? slot.entries.map((entry) => ({
          theme: entry.diff.theme ?? null,
          base: entry.diff.before,
          web: entry.diff.after,
          code: entry.code,
        }))
      : benchValues(slot, base, web, code).filter(
          (item) => !same(item.web, item.base) || !same(item.code, item.base),
        );
  const tokenChange =
    diff.token !== undefined && (diff.kind === "added" || diff.kind === "removed");
  return {
    id: slot.id,
    reason: ask.reason,
    family: diff.family,
    token: diff.token ?? null,
    group: diff.group ?? null,
    field: fieldOf(diff),
    themes: slot.benches,
    changes,
    choices: ask.choices,
    webReason: ask.webReason,
    note: tokenChange && renamed.has(diff.family) ? RENAME_NOTE : "",
  };
}

function isChoice(value: string): value is Choice {
  return CHOICES.some((choice) => choice === value);
}

/**
 * 답할 수 있는 자리와 그 자리에서 고를 수 있는 답. 둘이 다르게 바뀐 자리는 그 자리의 `choices` 다. 제안이 난 자리는
 * "code" 와, 제안 값이 있으면 "suggested" 를 받는다. 걸린 웹 값("web")은 둘이 다르게 바뀐 자리에서만 고른다.
 */
function answerableOf(
  plans: readonly Plan[],
  suggestions: readonly Suggestion[],
): Map<string, readonly Choice[]> {
  const answerable = new Map<string, readonly Choice[]>(
    plans.flatMap(({ slot, ask }) => (ask?.reason === "conflict" ? [[slot.id, ask.choices]] : [])),
  );
  for (const { id, value } of suggestions) {
    const before = answerable.get(id) ?? [];
    const added: readonly Choice[] = value === null ? ["code"] : ["code", "suggested"];
    answerable.set(
      id,
      CHOICES.filter((choice) => before.includes(choice) || added.includes(choice)),
    );
  }
  return answerable;
}

/** 답이 가리키는 자리와 고른 답을 본다. 답할 수 없는 자리나 답이면 `input` 오류다. */
function checkAnswers(
  answers: Readonly<Record<string, string>>,
  answerable: ReadonlyMap<string, readonly Choice[]>,
): void {
  for (const [id, choice] of Object.entries(answers)) {
    const choices = answerable.get(id);
    if (choices === undefined) {
      throw new CommandError("input", `답의 자리 ${id} 가 이번 들이기에서 답할 자리가 아니다`);
    }
    if (!isChoice(choice) || !choices.includes(choice)) {
      throw new CommandError(
        "input",
        `답의 자리 ${id} 에서 ${choice} 는 고를 수 없다. 고를 수 있는 답: ${choices.join(", ")}`,
      );
    }
  }
}

/** 웹, 기준본, 지금 디자인 토큰 CSS 와 답으로 들인다. 풀 수 없는 입력과 답할 수 없는 답은 `input` 오류다. */
export function importTokens(input: ImportInput): ImportResult {
  const parsed = parseThemeCss(input.css);
  const code: Code = {
    benches: pageThemes(parsed),
    themeStatic: parsed.themeStatic,
    tokens: readTokens(buildTokensFile(input.css)),
    lines: input.css.split("\n"),
  };
  const base = readTokens(input.base);
  const web = readTokens(input.web);

  const alreadyImported: Settled[] = [];
  const pending: Pending[] = [];
  for (const diff of diffTokens(base, web)) {
    const codeValue = valueAt(code.tokens, diff);
    if (same(codeValue, diff.after)) {
      alreadyImported.push(settled(diff, diff.after));
    } else {
      pending.push({ diff, code: codeValue, conflict: !same(codeValue, diff.before) });
    }
  }
  const codeOnly = diffTokens(base, code.tokens)
    .filter((diff) => same(valueAt(web, diff), diff.before))
    .map((diff) => settled(diff, diff.after));

  const plans = plansOf(slotsOf(code, pending), base, web, code);
  const answerOf = (id: string): string | undefined =>
    Object.hasOwn(input.answers, id) ? input.answers[id] : undefined;

  // 둘이 다르게 바뀐 자리의 답을 먼저 따른다. 웹 값이나 제안 값을 고른 자리는 웹 값으로 판정에 든다.
  const firstMoves: Move[] = plans.flatMap(({ slot, ask, move }) => {
    const choice = answerOf(slot.id);
    return move !== undefined && (ask === undefined || choice === "web" || choice === "suggested")
      ? [{ slot, ...move }]
      : [];
  });
  const first = contrastOf(code, firstMoves);
  checkAnswers(input.answers, answerableOf(plans, first.suggestions));
  const suggested = new Map(first.suggestions.map((suggestion) => [suggestion.id, suggestion]));

  // 제안이 난 자리의 답을 따른다.
  const moves = firstMoves.flatMap((move): Move[] => {
    const suggestion = suggested.get(move.slot.id);
    const choice = suggestion === undefined ? undefined : answerOf(move.slot.id);
    if (choice === "code") {
      return [];
    }
    const value = choice === "suggested" ? suggestion?.value : undefined;
    return [value === undefined || value === null ? move : { ...move, text: value }];
  });
  const final = contrastOf(code, moves);
  const css = written(code, moves);

  const renamed = renamedFamilies(pending);
  const asked = plans.flatMap((plan) => {
    if (
      plan.ask === undefined ||
      (plan.ask.reason === "conflict" && answerOf(plan.slot.id) !== undefined)
    ) {
      return [];
    }
    return [askedOf(plan.slot, plan.ask, base, web, code, renamed)];
  });
  const answered = plans.flatMap(({ slot }): Answered[] => {
    const choice = answerOf(slot.id);
    if (choice === undefined || !isChoice(choice)) {
      return [];
    }
    const kept = moves.find((move) => move.slot.id === slot.id);
    const value = choice === "code" ? (slot.entries[0]?.code ?? null) : (kept?.text ?? null);
    return [{ id: slot.id, choice, value }];
  });

  return {
    css,
    report: {
      changed: css !== input.css,
      moved: moves.map(movedOf),
      asked,
      alreadyImported,
      codeOnly,
      contrast: {
        measured: code.benches.length * CONTRAST_PAIRS.length,
        failures: final.failures,
        suggestions: final.suggestions,
      },
      answered,
    },
  };
}

/** JSON 입력 파일을 푼다. 풀 수 없으면 `input` 오류다. */
function readJson(path: string): unknown {
  const text = readInput(path);
  try {
    const parsed: unknown = JSON.parse(text);
    return parsed;
  } catch (error) {
    throw new CommandError("input", `${path} 를 JSON 으로 풀 수 없다: ${messageOf(error)}`);
  }
}

/** 답 파일. 자리 id 에서 답(글)으로 가는 객체여야 한다. */
function readAnswers(path: string): Record<string, string> {
  const parsed = readJson(path);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new CommandError("input", `${path} 는 자리 id 에서 답으로 가는 객체여야 한다`);
  }
  const answers: Record<string, string> = {};
  for (const [id, choice] of Object.entries(parsed)) {
    if (typeof choice !== "string") {
      throw new CommandError("input", `${path} 의 ${id} 답이 글이 아니다`);
    }
    answers[id] = choice;
  }
  return answers;
}

/** 들이기 명령. */
export function importCommand(args: readonly string[]): ReportFields {
  const {
    css = DEFAULT_CSS,
    web,
    base,
    out,
    answers,
  } = parsedArgs(
    () =>
      parseArgs({
        args: [...args],
        options: {
          css: { type: "string" },
          web: { type: "string" },
          base: { type: "string" },
          out: { type: "string" },
          answers: { type: "string" },
        },
        strict: true,
        allowPositionals: false,
      }).values,
  );
  if (web === undefined || base === undefined || out === undefined) {
    throw new CommandError(
      "usage",
      "import 에는 --web <tokens.json>, --base <tokens.json>, --out <디자인 토큰 CSS> 가 있어야 한다",
    );
  }
  const result = importTokens({
    css: readInput(css),
    base: readJson(base),
    web: readJson(web),
    answers: answers === undefined ? {} : readAnswers(answers),
  });
  return { out: writeOutput(out, result.css), ...result.report };
}
