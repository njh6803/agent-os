/**
 * `tokens.json` 의 모델과 두 벌의 차이. 짓기가 쓰는 꼴, 페이지가 저장한 꼴까지 받는 정규 꼴, 차이 목록, 맞대는 값을
 * 낸다. 들이기, 기록, `pending`, `claim`, 확인이 모두 이 모듈로 맞댄다(design-reverse-sync 명세 "기록"의
 * 2026-10-22 주석의 넷째, "맞대는 것"의 2026-10-22 주석).
 *
 * 맞대는 몫은 토큰·벌마다의 값과 설명, 글자 스타일의 모든 칸(글꼴 묶음과 글꼴 목록을 포함한다), 계열 설명(`note`),
 * 계열과 토큰의 목록이다. 맞대는 값은 그 몫을 정규 꼴로 적은 JSON 의 sha256 이고, 차이가 없는 두 벌은 맞대는 값이
 * 같다. 테마는 벌의 목록으로만 본다.
 *
 * 정규 꼴은 Design System 형식의 페이지(판 1792564314-af13 의 `artifact-type/app.js`)가 `tokens.json` 을 읽을 때
 * 하는 정리를 따라 한다. 그래서 페이지가 저장하며 꼴만 다시 쓴 파일(문자열 색 값을 첫 테마의 객체로, 빈 설명 칸, 소문자
 * hex, 글자 스타일의 기본값과 문자열 굵기, 키의 차례)은 차이가 없다. 색과 그림자의 값은 벌마다 풀어 둔다. 값이 없는
 * 벌은 첫 테마의 값을 물려받기 때문이다(형식 설명 `format.md` 의 "tokens.json grammar"). 페이지가 버리는 값(읽지
 * 못하는 색, 같은 이름의 둘째 토큰, 한도 뒤의 것)도 버린다.
 *
 * 맞대지 않는 것: 맨 위의 `name`·`version`·`meta`, 테마의 표시 이름과 차례, 토큰과 묶음의 차례. 페이지는 이것들을
 * 지키거나 다시 쓰지만 디자인 토큰 CSS 로 옮길 값이 아니다. 다른 토큰을 가리키는 값이 실제로 있는 토큰인지는 보지
 * 않는다(페이지는 그런 값을 버린다).
 */

import { createHash } from "node:crypto";

/** JSON 으로 적을 수 있는 값. */
export type JsonValue =
  string | number | boolean | null | readonly JsonValue[] | { readonly [key: string]: JsonValue };

/** 색 계열의 페이지 테마. 이 기능에서는 벌(테마 × 모드) 하나다. */
export interface Theme {
  readonly id: string;
  readonly name: string;
}

/** 색 토큰. 값이 문자열이면 첫 테마의 값이고 나머지 벌이 물려받는다. */
export interface ColorToken {
  readonly name: string;
  readonly value: string | Readonly<Record<string, string>>;
  readonly usage: string;
}

/** 색과 글자 밖 계열(간격, 모서리)의 토큰. */
export interface Token {
  readonly name: string;
  readonly value: string;
  readonly usage: string;
}

export interface TypeStyle {
  readonly name: string;
  readonly fontSize: string;
  readonly lineHeight?: string;
  readonly fontWeight?: number | string;
  readonly usage: string;
}

export interface TypeGroup {
  readonly name: string;
  readonly family: string;
  readonly styles: readonly TypeStyle[];
}

export interface TokenFamily {
  readonly note: string;
  readonly tokens: readonly Token[];
}

/** 짓기가 쓰는 tokens.json. */
export interface TokensFile {
  readonly version: 1;
  readonly color: { readonly themes: readonly Theme[]; readonly tokens: readonly ColorToken[] };
  readonly type: {
    readonly families: Readonly<Record<string, string>>;
    readonly groups: readonly TypeGroup[];
  };
  readonly spacing: TokenFamily;
  readonly radius: TokenFamily;
}

/** 형식의 한도(`format.md` 의 caps 줄). 넘는 것을 페이지가 버리므로 정규 꼴도 버린다. */
export const LIMITS = {
  themes: 8,
  colors: 600,
  familyTokens: 60,
  families: 12,
  typeGroups: 12,
  typeStyles: 80,
  extraFamilies: 12,
  fonts: 4096,
  usage: 1000,
  note: 400,
  sample: 200,
  name: 120,
} as const;

/** 지은 파일의 바이트. 두 칸 들여 쓴 JSON 과 끝 줄바꿈이다(페이지가 저장하는 꼴과 같다). */
export function serializeTokensFile(file: TokensFile): string {
  return `${JSON.stringify(file, null, 2)}\n`;
}

/** 정규 꼴의 토큰. 색과 그림자의 값은 벌마다 풀어 둔다. */
export interface CanonicalToken {
  readonly value: string | ReadonlyMap<string, string>;
  readonly usage: string;
}

export interface CanonicalFamily {
  readonly note: string;
  readonly tokens: ReadonlyMap<string, CanonicalToken>;
}

export interface CanonicalStyle {
  readonly group: string;
  readonly fontSize: string;
  readonly lineHeight: string;
  readonly fontWeight: string;
  readonly letterSpacing: string;
  readonly fontStyle: string;
  readonly opticalSize: number | null;
  readonly family: string;
  readonly sample: string;
  readonly usage: string;
}

export interface CanonicalType {
  /** 글꼴 묶음의 키와 글꼴 스택. */
  readonly families: ReadonlyMap<string, string>;
  /** 글꼴 파일 목록. 칸마다 정리한 객체이고 차례는 보지 않는다. */
  readonly fonts: readonly JsonValue[];
  readonly groups: ReadonlyMap<string, { readonly family: string; readonly note: string }>;
  readonly styles: ReadonlyMap<string, CanonicalStyle>;
}

/** 정규 꼴의 tokens.json. 맞대는 몫만 든다. */
export interface CanonicalTokens {
  /** 벌의 id. 파일의 차례이고 첫째가 첫 테마다. */
  readonly themes: readonly string[];
  /** 색, 간격, 모서리와 토큰이 있는 그림자·다른 계열. 계열 키로 찾는다. */
  readonly families: ReadonlyMap<string, CanonicalFamily>;
  readonly type: CanonicalType;
}

const NAME = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$/;
const HEX = /^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/;
const COLOR_FUNCTION = /^(?:rgb|rgba|hsl|hsla|oklch|oklab|lab|lch|color)\([0-9a-z.,%/ -]{1,60}\)$/;
const ALIAS = /^\{([A-Za-z0-9][A-Za-z0-9_.-]{0,63})\}$/;
const LENGTH = /^-?\d{1,4}(?:\.\d{1,6})?(?:px|rem|em|%)$|^0$/;
const WEIGHT = /^(?:[1-9]\d{0,2}|1000)(?: (?:[1-9]\d{0,2}|1000))?$/;
const EXTRA_FAMILY = /^(?!(?:__proto__|constructor|prototype)$)[A-Za-z][A-Za-z0-9_-]{0,31}$/;
const BUILT_IN = ["version", "color", "type", "spacing", "radius", "shadow"];

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function own(value: Readonly<Record<string, unknown>>, key: string): unknown {
  return Object.hasOwn(value, key) ? value[key] : undefined;
}

function items(value: unknown): readonly unknown[] {
  return Array.isArray(value) ? value.map((item: unknown) => item) : [];
}

/** 문자열이면 글자 수(코드 포인트)를 `limit` 에서 자른 것, 아니면 빈 글. */
function text(value: unknown, limit: number): string {
  if (typeof value !== "string") {
    return "";
  }
  const characters = Array.from(value);
  return characters.length > limit ? characters.slice(0, limit).join("") : value;
}

function tokenName(value: unknown): string {
  return typeof value === "string" ? value.trim().replace(/^--/, "") : "";
}

/** 색 값. hex 와 색 함수는 소문자, 다른 토큰을 가리키는 값은 `{이름}` 이다. 읽지 못하면 undefined. */
function colorValue(value: unknown): string | undefined {
  if (typeof value !== "string") {
    return undefined;
  }
  const lower = value.trim().toLowerCase();
  if (HEX.test(lower) || (COLOR_FUNCTION.test(lower) && !/url|var|expression/.test(lower))) {
    return lower;
  }
  const alias = value.trim().replace(/^\{--/, "{");
  return ALIAS.test(alias) ? alias : undefined;
}

/** 길이. 수는 px 로 읽는다. 모서리의 `full` 은 9999px 이다. */
function length(value: unknown, radius = false): string | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    if (Math.abs(value) >= 1e4) {
      return undefined;
    }
    return value === 0 ? "0" : `${String(Math.round(value * 1000) / 1000)}px`;
  }
  if (typeof value !== "string") {
    return undefined;
  }
  const lower = value.trim().toLowerCase();
  if (radius && lower === "full") {
    return "9999px";
  }
  return LENGTH.test(lower) ? lower : undefined;
}

function lineHeight(value: unknown): string | undefined {
  if (typeof value === "number" && Number.isFinite(value) && value > 0 && value < 10) {
    return String(Math.round(value * 1000) / 1000);
  }
  if (typeof value === "string" && /^\d(?:\.\d{1,6})?$/.test(value.trim())) {
    return Number(value) > 0 ? value.trim() : undefined;
  }
  return length(value);
}

function weight(value: unknown): string | undefined {
  if (typeof value === "number" && Number.isInteger(value) && value >= 1 && value <= 1000) {
    return String(value);
  }
  if (typeof value !== "string") {
    return undefined;
  }
  const collapsed = value.trim().replace(/\s+/g, " ");
  if (collapsed === "normal") {
    return "400";
  }
  if (collapsed === "bold") {
    return "700";
  }
  return WEIGHT.test(collapsed) ? collapsed : undefined;
}

function opticalSize(value: unknown): number | null {
  const trimmed = typeof value === "string" ? value.trim() : value;
  if (trimmed === null || trimmed === "" || trimmed === "auto" || trimmed === "none") {
    return null;
  }
  const number =
    typeof trimmed === "number"
      ? trimmed
      : typeof trimmed === "string" && /^\d{1,4}(?:\.\d{1,3})?$/.test(trimmed)
        ? Number(trimmed)
        : Number.NaN;
  return Number.isFinite(number) && number >= 1 && number <= 1000 ? number : null;
}

/** 그림자와 다른 계열의 값. 공백을 하나로 줄인 글이다. */
function plainValue(value: unknown): string | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  if (typeof value !== "string") {
    return undefined;
  }
  const collapsed = value.trim().replace(/\s+/g, " ");
  return collapsed === "" || /(?:url|var|expression)\s*\(/i.test(collapsed) ? undefined : collapsed;
}

/** 벌마다의 값을 읽어 모든 벌로 푼다. 첫 테마의 값이 없으면 앞에서 처음 값이 있는 벌의 것을 빌린다. */
function perTheme(
  value: unknown,
  themes: readonly string[],
  read: (raw: unknown) => string | undefined,
): ReadonlyMap<string, string> | undefined {
  const first = themes[0] ?? "";
  const found = new Map<string, string>();
  if (isRecord(value)) {
    for (const theme of themes) {
      const parsed = Object.hasOwn(value, theme) ? read(value[theme]) : undefined;
      if (parsed !== undefined) {
        found.set(theme, parsed);
      }
    }
  } else {
    const single = read(value);
    if (single !== undefined) {
      found.set(first, single);
    }
  }
  const base =
    found.get(first) ?? themes.map((theme) => found.get(theme)).find((item) => item !== undefined);
  if (base === undefined) {
    return undefined;
  }
  return new Map(themes.map((theme) => [theme, found.get(theme) ?? base]));
}

function readThemes(color: Readonly<Record<string, unknown>>): string[] {
  const themes: string[] = [];
  for (const item of items(own(color, "themes"))) {
    if (themes.length >= LIMITS.themes) {
      break;
    }
    const raw = isRecord(item) ? own(item, "id") : item;
    const id = typeof raw === "string" ? raw.trim().toLowerCase() : "";
    if (
      NAME.test(id) &&
      !themes.includes(id) &&
      id !== "prototype" &&
      !Object.hasOwn(Object.prototype, id)
    ) {
      themes.push(id);
    }
  }
  return themes.length > 0 ? themes : ["light"];
}

function readFamily(
  value: unknown,
  taken: Set<string>,
  read: (raw: unknown) => string | ReadonlyMap<string, string> | undefined,
): CanonicalFamily {
  const family = isRecord(value) ? value : {};
  const tokens = new Map<string, CanonicalToken>();
  for (const item of items(own(family, "tokens"))) {
    if (tokens.size >= LIMITS.familyTokens) {
      break;
    }
    if (!isRecord(item)) {
      continue;
    }
    const name = tokenName(own(item, "name"));
    const parsed = read(own(item, "value"));
    if (!NAME.test(name) || taken.has(name) || parsed === undefined) {
      continue;
    }
    taken.add(name);
    tokens.set(name, { value: parsed, usage: text(own(item, "usage"), LIMITS.usage) });
  }
  return { note: text(own(family, "note"), LIMITS.note), tokens };
}

function readType(value: unknown): CanonicalType {
  const type = isRecord(value) ? value : {};
  const families = new Map<string, string>();
  const rawFamilies = own(type, "families");
  if (isRecord(rawFamilies)) {
    for (const [key, stack] of Object.entries(rawFamilies)) {
      if (families.size >= LIMITS.families) {
        break;
      }
      const lower = key.trim().toLowerCase();
      if (NAME.test(lower) && typeof stack === "string" && stack.trim() !== "") {
        families.set(lower, stack.trim());
      }
    }
  }
  const familyOf = (raw: unknown): string => {
    const lower = typeof raw === "string" ? raw.trim().toLowerCase() : "";
    return families.has(lower) ? lower : "";
  };

  const fonts: JsonValue[] = [];
  for (const item of items(own(type, "fonts"))) {
    if (fonts.length >= LIMITS.fonts || !isRecord(item)) {
      continue;
    }
    const family = text(own(item, "family"), LIMITS.name).trim();
    const file = typeof own(item, "file") === "string" ? String(own(item, "file")).trim() : "";
    if (family === "" || file === "") {
      continue;
    }
    const style = own(item, "style");
    fonts.push({
      family,
      file: file.includes("/") ? file : `fonts/${file}`,
      weight: weight(own(item, "weight")) ?? "400",
      style: style === "italic" || style === "oblique" ? style : "normal",
    });
  }

  const groups = new Map<string, { readonly family: string; readonly note: string }>();
  const styles = new Map<string, CanonicalStyle>();
  for (const item of items(own(type, "groups"))) {
    if (groups.size >= LIMITS.typeGroups || !isRecord(item)) {
      continue;
    }
    const groupName = text(own(item, "name"), LIMITS.name) || "Type";
    groups.set(groupName, {
      family: familyOf(own(item, "family")),
      note: text(own(item, "note"), LIMITS.note),
    });
    for (const raw of items(own(item, "styles"))) {
      if (styles.size >= LIMITS.typeStyles || !isRecord(raw)) {
        continue;
      }
      const name =
        typeof own(raw, "name") === "string"
          ? String(own(raw, "name")).trim().replace(/^\./, "")
          : "";
      const fontSize = length(own(raw, "fontSize"));
      if (!NAME.test(name) || styles.has(name) || fontSize === undefined) {
        continue;
      }
      styles.set(name, {
        group: groupName,
        fontSize,
        lineHeight: lineHeight(own(raw, "lineHeight")) ?? "1.4",
        fontWeight: weight(own(raw, "fontWeight")) ?? "400",
        letterSpacing: length(own(raw, "letterSpacing")) ?? "0",
        fontStyle: own(raw, "fontStyle") === "italic" ? "italic" : "normal",
        opticalSize: opticalSize(own(raw, "opticalSize")),
        family: familyOf(own(raw, "family")),
        sample: text(own(raw, "sample"), LIMITS.sample),
        usage: text(own(raw, "usage"), LIMITS.usage),
      });
    }
  }
  return { families, fonts, groups, styles };
}

/**
 * tokens.json 의 내용(JSON 으로 푼 값)을 정규 꼴로 읽는다. 어떤 값이든 받는다. 꼴이 어긋난 칸은 페이지처럼 비었거나
 * 없는 것으로 읽는다.
 */
export function readTokens(input: unknown): CanonicalTokens {
  const root = isRecord(input) ? input : {};
  const rawColor = own(root, "color");
  const color = isRecord(rawColor) ? rawColor : {};
  const themes = readThemes(color);

  const colorTokens = new Map<string, CanonicalToken>();
  const rawTokens = own(color, "tokens");
  const listed = Array.isArray(rawTokens)
    ? items(rawTokens)
    : items(own(color, "groups")).flatMap((group) =>
        isRecord(group) ? items(own(group, "tokens")) : [],
      );
  for (const item of listed) {
    if (colorTokens.size >= LIMITS.colors) {
      break;
    }
    if (!isRecord(item)) {
      continue;
    }
    const name = tokenName(own(item, "name"));
    const value = perTheme(own(item, "value"), themes, colorValue);
    if (!NAME.test(name) || colorTokens.has(name) || value === undefined) {
      continue;
    }
    colorTokens.set(name, { value, usage: text(own(item, "usage"), LIMITS.usage) });
  }

  const taken = new Set(colorTokens.keys());
  const families = new Map<string, CanonicalFamily>([["color", { note: "", tokens: colorTokens }]]);
  families.set(
    "spacing",
    readFamily(own(root, "spacing"), taken, (raw) => length(raw)),
  );
  families.set(
    "radius",
    readFamily(own(root, "radius"), taken, (raw) => length(raw, true)),
  );
  const shadow = readFamily(own(root, "shadow"), taken, (raw) => perTheme(raw, themes, plainValue));
  if (shadow.tokens.size > 0) {
    families.set("shadow", shadow);
  }
  let extras = 0;
  for (const key of Object.keys(root)) {
    if (
      BUILT_IN.includes(key) ||
      key === "name" ||
      !EXTRA_FAMILY.test(key) ||
      extras >= LIMITS.extraFamilies
    ) {
      continue;
    }
    const value = own(root, key);
    if (!isRecord(value) || !Array.isArray(own(value, "tokens"))) {
      continue;
    }
    extras += 1;
    const family = readFamily(value, taken, plainValue);
    if (family.tokens.size > 0) {
      families.set(key, family);
    }
  }

  return { themes, families, type: readType(own(root, "type")) };
}

/** 차이의 종류. */
export const DIFF_KINDS = [
  "value",
  "usage",
  "typeField",
  "familyNote",
  "added",
  "removed",
] as const;

export type DiffKind = (typeof DIFF_KINDS)[number];

/**
 * 두 벌의 차이 하나. `family` 는 계열 키(`color`, `type`, `spacing`, `radius`, `shadow`, 다른 계열)이다.
 *
 * - `value`: 토큰의 값(`theme` 은 그 벌), 또는 글자 스타일의 크기·줄 높이·굵기(`field`).
 * - `usage`: 토큰이나 글자 스타일의 설명.
 * - `typeField`: 글자 스타일의 다른 칸(`field`), 글자 묶음의 글꼴(`group`, `field`), 글꼴 묶음(`field` 가
 *   `families.<키>`), 글꼴 목록(`field` 가 `fonts`).
 * - `familyNote`: 계열 설명, 또는 글자 묶음의 설명(`group`).
 * - `added`, `removed`: 토큰(`token`), 글자 묶음(`group`), 벌(`theme`), 계열(셋 다 없다)을 더하거나 지운 것.
 *
 * 없던 쪽은 null 이다.
 */
export interface TokenDiff {
  readonly kind: DiffKind;
  readonly family: string;
  readonly token?: string;
  readonly theme?: string;
  readonly group?: string;
  readonly field?: string;
  readonly before: JsonValue;
  readonly after: JsonValue;
}

function sortedKeys(...maps: readonly ReadonlyMap<string, unknown>[]): string[] {
  return [...new Set(maps.flatMap((map) => [...map.keys()]))].sort(byText);
}

function byText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function valueJson(value: string | ReadonlyMap<string, string>): JsonValue {
  return typeof value === "string"
    ? value
    : Object.fromEntries([...value].sort(([left], [right]) => byText(left, right)));
}

function tokenJson(token: CanonicalToken): JsonValue {
  return { value: valueJson(token.value), usage: token.usage };
}

function familyJson(family: CanonicalFamily): JsonValue {
  return {
    note: family.note,
    tokens: sortedKeys(family.tokens).flatMap((name) => {
      const token = family.tokens.get(name);
      return token === undefined ? [] : [[name, tokenJson(token)]];
    }),
  };
}

function styleJson(style: CanonicalStyle): JsonValue {
  return {
    group: style.group,
    fontSize: style.fontSize,
    lineHeight: style.lineHeight,
    fontWeight: style.fontWeight,
    letterSpacing: style.letterSpacing,
    fontStyle: style.fontStyle,
    opticalSize: style.opticalSize,
    family: style.family,
    sample: style.sample,
    usage: style.usage,
  };
}

function fontsJson(fonts: readonly JsonValue[]): JsonValue {
  return fonts.map((font) => JSON.stringify(font)).sort(byText);
}

const STYLE_VALUES = ["fontSize", "lineHeight", "fontWeight"] as const;
const STYLE_FIELDS = [
  "group",
  "letterSpacing",
  "fontStyle",
  "opticalSize",
  "family",
  "sample",
] as const;

/** 계열의 차례. 색, 글자, 간격, 모서리, 그림자, 다른 계열(이름 차례)이다. */
function familyOrder(names: readonly string[]): string[] {
  const fixed = ["color", "type", "spacing", "radius", "shadow"];
  return [
    ...fixed.filter((name) => names.includes(name)),
    ...names.filter((name) => !fixed.includes(name)).sort(byText),
  ];
}

function diffFamily(
  name: string,
  before: CanonicalFamily,
  after: CanonicalFamily,
  themes: readonly string[],
): TokenDiff[] {
  const diffs: TokenDiff[] = [];
  if (before.note !== after.note) {
    diffs.push({ kind: "familyNote", family: name, before: before.note, after: after.note });
  }
  for (const token of sortedKeys(before.tokens, after.tokens)) {
    const left = before.tokens.get(token);
    const right = after.tokens.get(token);
    if (left === undefined || right === undefined) {
      diffs.push({
        kind: left === undefined ? "added" : "removed",
        family: name,
        token,
        before: left === undefined ? null : tokenJson(left),
        after: right === undefined ? null : tokenJson(right),
      });
      continue;
    }
    if (typeof left.value === "string" || typeof right.value === "string") {
      if (JSON.stringify(valueJson(left.value)) !== JSON.stringify(valueJson(right.value))) {
        diffs.push({
          kind: "value",
          family: name,
          token,
          before: valueJson(left.value),
          after: valueJson(right.value),
        });
      }
    } else {
      for (const theme of themes) {
        const was = left.value.get(theme) ?? null;
        const now = right.value.get(theme) ?? null;
        if (was !== now) {
          diffs.push({ kind: "value", family: name, token, theme, before: was, after: now });
        }
      }
    }
    if (left.usage !== right.usage) {
      diffs.push({ kind: "usage", family: name, token, before: left.usage, after: right.usage });
    }
  }
  return diffs;
}

function diffType(before: CanonicalType, after: CanonicalType): TokenDiff[] {
  const diffs: TokenDiff[] = [];
  for (const key of sortedKeys(before.families, after.families)) {
    const was = before.families.get(key) ?? null;
    const now = after.families.get(key) ?? null;
    if (was !== now) {
      diffs.push({
        kind: "typeField",
        family: "type",
        field: `families.${key}`,
        before: was,
        after: now,
      });
    }
  }
  const fontsBefore = fontsJson(before.fonts);
  const fontsAfter = fontsJson(after.fonts);
  if (JSON.stringify(fontsBefore) !== JSON.stringify(fontsAfter)) {
    diffs.push({
      kind: "typeField",
      family: "type",
      field: "fonts",
      before: fontsBefore,
      after: fontsAfter,
    });
  }
  for (const group of sortedKeys(before.groups, after.groups)) {
    const left = before.groups.get(group);
    const right = after.groups.get(group);
    if (left === undefined || right === undefined) {
      diffs.push({
        kind: left === undefined ? "added" : "removed",
        family: "type",
        group,
        before: left === undefined ? null : { family: left.family, note: left.note },
        after: right === undefined ? null : { family: right.family, note: right.note },
      });
      continue;
    }
    if (left.family !== right.family) {
      diffs.push({
        kind: "typeField",
        family: "type",
        group,
        field: "family",
        before: left.family,
        after: right.family,
      });
    }
    if (left.note !== right.note) {
      diffs.push({
        kind: "familyNote",
        family: "type",
        group,
        before: left.note,
        after: right.note,
      });
    }
  }
  for (const token of sortedKeys(before.styles, after.styles)) {
    const left = before.styles.get(token);
    const right = after.styles.get(token);
    if (left === undefined || right === undefined) {
      diffs.push({
        kind: left === undefined ? "added" : "removed",
        family: "type",
        token,
        before: left === undefined ? null : styleJson(left),
        after: right === undefined ? null : styleJson(right),
      });
      continue;
    }
    for (const field of STYLE_VALUES) {
      if (left[field] !== right[field]) {
        diffs.push({
          kind: "value",
          family: "type",
          token,
          field,
          before: left[field],
          after: right[field],
        });
      }
    }
    for (const field of STYLE_FIELDS) {
      if (left[field] !== right[field]) {
        diffs.push({
          kind: "typeField",
          family: "type",
          token,
          field,
          before: left[field],
          after: right[field],
        });
      }
    }
    if (left.usage !== right.usage) {
      diffs.push({ kind: "usage", family: "type", token, before: left.usage, after: right.usage });
    }
  }
  return diffs;
}

/** 두 벌의 차이 목록. 계열의 차례, 그 안에서 이름 차례다. 차이가 없으면 비어 있다. */
export function diffTokens(before: CanonicalTokens, after: CanonicalTokens): TokenDiff[] {
  const diffs: TokenDiff[] = [];
  const shared = before.themes.filter((theme) => after.themes.includes(theme));
  for (const theme of [...before.themes].sort(byText)) {
    if (!after.themes.includes(theme)) {
      diffs.push({ kind: "removed", family: "color", theme, before: theme, after: null });
    }
  }
  for (const theme of [...after.themes].sort(byText)) {
    if (!before.themes.includes(theme)) {
      diffs.push({ kind: "added", family: "color", theme, before: null, after: theme });
    }
  }
  for (const name of familyOrder([...sortedKeys(before.families, after.families), "type"])) {
    if (name === "type") {
      diffs.push(...diffType(before.type, after.type));
      continue;
    }
    const left = before.families.get(name);
    const right = after.families.get(name);
    if (left === undefined || right === undefined) {
      diffs.push({
        kind: left === undefined ? "added" : "removed",
        family: name,
        before: left === undefined ? null : familyJson(left),
        after: right === undefined ? null : familyJson(right),
      });
      continue;
    }
    diffs.push(...diffFamily(name, left, right, shared));
  }
  return diffs;
}

/** 맞대는 몫을 정규 꼴로 적은 JSON. 키와 목록의 차례가 정해져 있다. */
function comparable(tokens: CanonicalTokens): JsonValue {
  const { type } = tokens;
  return {
    themes: [...tokens.themes].sort(byText),
    families: sortedKeys(tokens.families).flatMap((name) => {
      const family = tokens.families.get(name);
      return family === undefined ? [] : [[name, familyJson(family)]];
    }),
    type: {
      families: sortedKeys(type.families).map((key) => [key, type.families.get(key) ?? ""]),
      fonts: fontsJson(type.fonts),
      groups: sortedKeys(type.groups).flatMap((name) => {
        const group = type.groups.get(name);
        return group === undefined ? [] : [[name, { family: group.family, note: group.note }]];
      }),
      styles: sortedKeys(type.styles).flatMap((name) => {
        const style = type.styles.get(name);
        return style === undefined ? [] : [[name, styleJson(style)]];
      }),
    },
  };
}

/** 맞대는 값. 맞대는 몫을 정규 꼴로 적은 JSON 의 sha256(16 진수)이다. */
export function comparisonHash(tokens: CanonicalTokens): string {
  return createHash("sha256")
    .update(JSON.stringify(comparable(tokens)))
    .digest("hex");
}
