/**
 * 정규 꼴의 두 벌에서 차이가 가리키는 자리만 옮기기와, 정규 꼴을 `tokens.json` 으로 적기. 확인이 이어받을 기준본을
 * 짓는 데 쓴다(design-reverse-sync 명세 "겹침"의 "병합됐으면"의 2026-10-22 주석의 셋째). 이어받을 기준본은 지금 웹의
 * `tokens.json` 에서 더 고친 몫의 토큰·벌만 앞 `claim` 의 사본 값으로 바꾼 것이고, 들이기 명령(`import.ts`)이
 * 기준본으로 받는다.
 *
 * 자리는 `tokens-json.ts` 의 `valueAt` 이 읽는 자리와 같다. 그래서 `withSpots(target, source, diffs)` 의 결과에서
 * 차이마다 `valueAt` 은 `source` 의 그것과 같고, 차이가 가리키지 않는 자리는 `target` 그대로다. 한쪽에 토큰·묶음·
 * 계열이 없는 자리는 그것을 통째로 옮기거나 지운다.
 *
 * `tokensFileOf` 는 `readTokens` 가 같은 정규 꼴로 다시 읽는 `tokens.json` 을 낸다. 맞대지 않는 칸(이름, 판, 테마의
 * 표시 이름)은 적지 않거나 테마 id 로 적는다.
 *
 * 못 보는 것: 벌을 더하는 자리를 옮기면 벌 목록만 바뀌고 토큰의 그 벌 값은 따로 옮기지 않는다. 다시 읽을 때 첫 테마의
 * 값을 물려받는다. 그 벌의 값이 다르면 값의 차이로 따로 든다. 글자 스타일을 옮겼는데 그 묶음이 결과에 없으면 빈
 * 묶음을 더해 적는다.
 */

import {
  readTokens,
  valueAt,
  type CanonicalFamily,
  type CanonicalStyle,
  type CanonicalToken,
  type CanonicalTokens,
  type CanonicalType,
  type JsonValue,
  type TokenDiff,
} from "./tokens-json.ts";

/** 바꿀 수 있는 정규 꼴. */
interface Draft {
  themes: string[];
  families: Map<string, { note: string; tokens: Map<string, CanonicalToken> }>;
  typeFamilies: Map<string, string>;
  fonts: JsonValue[];
  groups: Map<string, { readonly family: string; readonly note: string }>;
  styles: Map<string, CanonicalStyle>;
}

function draftOf(tokens: CanonicalTokens): Draft {
  return {
    themes: [...tokens.themes],
    families: new Map(
      [...tokens.families].map(([name, family]) => [
        name,
        { note: family.note, tokens: new Map(family.tokens) },
      ]),
    ),
    typeFamilies: new Map(tokens.type.families),
    fonts: [...tokens.type.fonts],
    groups: new Map(tokens.type.groups),
    styles: new Map(tokens.type.styles),
  };
}

function frozen(draft: Draft): CanonicalTokens {
  const families = new Map<string, CanonicalFamily>(
    [...draft.families].map(([name, family]) => [
      name,
      { note: family.note, tokens: family.tokens },
    ]),
  );
  const type: CanonicalType = {
    families: draft.typeFamilies,
    fonts: draft.fonts,
    groups: draft.groups,
    styles: draft.styles,
  };
  return { themes: draft.themes, families, type };
}

/** `map` 의 `key` 를 `value` 로 두거나, `value` 가 없으면 지운다. */
function put<T>(map: Map<string, T>, key: string, value: T | undefined): void {
  if (value === undefined) {
    map.delete(key);
  } else {
    map.set(key, value);
  }
}

function moveTheme(draft: Draft, source: CanonicalTokens, theme: string): void {
  const kept = draft.themes.filter((item) => item !== theme);
  draft.themes = source.themes.includes(theme) ? [...kept, theme] : kept;
}

function moveFamilySpot(draft: Draft, source: CanonicalTokens, diff: TokenDiff): void {
  const from = source.families.get(diff.family);
  const { token, theme } = diff;
  if (token === undefined) {
    const into = draft.families.get(diff.family);
    if (diff.kind === "familyNote" && from !== undefined && into !== undefined) {
      into.note = from.note;
    } else {
      put(
        draft.families,
        diff.family,
        from === undefined ? undefined : { note: from.note, tokens: new Map(from.tokens) },
      );
    }
    return;
  }
  let into = draft.families.get(diff.family);
  if (into === undefined) {
    if (from === undefined) {
      return;
    }
    into = { note: from.note, tokens: new Map() };
    draft.families.set(diff.family, into);
  }
  const incoming = from?.tokens.get(token);
  const current = into.tokens.get(token);
  if (
    incoming === undefined ||
    current === undefined ||
    diff.kind === "added" ||
    diff.kind === "removed"
  ) {
    put(into.tokens, token, incoming);
    return;
  }
  if (diff.kind === "usage") {
    into.tokens.set(token, { ...current, usage: incoming.usage });
    return;
  }
  if (
    theme !== undefined &&
    typeof current.value !== "string" &&
    typeof incoming.value !== "string"
  ) {
    const values = new Map(current.value);
    put(values, theme, incoming.value.get(theme));
    into.tokens.set(token, { ...current, value: values });
    return;
  }
  into.tokens.set(token, { ...current, value: incoming.value });
}

const STYLE_FIELDS = [
  "group",
  "fontSize",
  "lineHeight",
  "fontWeight",
  "letterSpacing",
  "fontStyle",
  "opticalSize",
  "family",
  "sample",
] as const;

type StyleField = (typeof STYLE_FIELDS)[number];

function withField(style: CanonicalStyle, from: CanonicalStyle, field: StyleField): CanonicalStyle {
  switch (field) {
    case "group":
      return { ...style, group: from.group };
    case "fontSize":
      return { ...style, fontSize: from.fontSize };
    case "lineHeight":
      return { ...style, lineHeight: from.lineHeight };
    case "fontWeight":
      return { ...style, fontWeight: from.fontWeight };
    case "letterSpacing":
      return { ...style, letterSpacing: from.letterSpacing };
    case "fontStyle":
      return { ...style, fontStyle: from.fontStyle };
    case "opticalSize":
      return { ...style, opticalSize: from.opticalSize };
    case "family":
      return { ...style, family: from.family };
    case "sample":
      return { ...style, sample: from.sample };
  }
}

function moveTypeSpot(draft: Draft, source: CanonicalTokens, diff: TokenDiff): void {
  const { kind, token, group, field = "" } = diff;
  if (token !== undefined) {
    const from = source.type.styles.get(token);
    const current = draft.styles.get(token);
    const known = STYLE_FIELDS.find((name) => name === field);
    if (from === undefined || current === undefined || kind === "added" || kind === "removed") {
      put(draft.styles, token, from);
    } else if (kind === "usage") {
      draft.styles.set(token, { ...current, usage: from.usage });
    } else if (known !== undefined) {
      draft.styles.set(token, withField(current, from, known));
    }
    return;
  }
  if (group !== undefined) {
    const from = source.type.groups.get(group);
    const current = draft.groups.get(group);
    if (from === undefined || current === undefined || kind === "added" || kind === "removed") {
      put(draft.groups, group, from);
    } else if (kind === "familyNote") {
      draft.groups.set(group, { ...current, note: from.note });
    } else {
      draft.groups.set(group, { ...current, family: from.family });
    }
    return;
  }
  if (field === "fonts") {
    draft.fonts = [...source.type.fonts];
    return;
  }
  const key = field.replace(/^families\./, "");
  put(draft.typeFamilies, key, source.type.families.get(key));
}

/** `target` 에서 `diffs` 가 가리키는 자리만 `source` 의 값으로 바꾼 벌. */
export function withSpots(
  target: CanonicalTokens,
  source: CanonicalTokens,
  diffs: readonly TokenDiff[],
): CanonicalTokens {
  const draft = draftOf(target);
  for (const diff of diffs) {
    if (diff.family === "type") {
      moveTypeSpot(draft, source, diff);
    } else if (diff.token === undefined && diff.theme !== undefined) {
      moveTheme(draft, source, diff.theme);
    } else {
      moveFamilySpot(draft, source, diff);
    }
  }
  return frozen(draft);
}

function valueOut(value: string | ReadonlyMap<string, string>): JsonValue {
  return typeof value === "string" ? value : Object.fromEntries(value);
}

function familyOut(family: CanonicalFamily): JsonValue {
  return {
    note: family.note,
    tokens: [...family.tokens].map(([name, token]) => ({
      name,
      value: valueOut(token.value),
      usage: token.usage,
    })),
  };
}

function styleOut(name: string, style: CanonicalStyle): JsonValue {
  return {
    name,
    fontSize: style.fontSize,
    lineHeight: style.lineHeight,
    fontWeight: style.fontWeight,
    letterSpacing: style.letterSpacing,
    fontStyle: style.fontStyle,
    ...(style.opticalSize === null ? {} : { opticalSize: style.opticalSize }),
    family: style.family,
    sample: style.sample,
    usage: style.usage,
  };
}

function typeOut(type: CanonicalType): JsonValue {
  const groups = new Map(type.groups);
  for (const style of type.styles.values()) {
    if (!groups.has(style.group)) {
      groups.set(style.group, { family: "", note: "" });
    }
  }
  return {
    families: Object.fromEntries(type.families),
    fonts: [...type.fonts],
    groups: [...groups].map(([name, group]) => ({
      name,
      family: group.family,
      note: group.note,
      styles: [...type.styles]
        .filter(([, style]) => style.group === name)
        .map(([styleName, style]) => styleOut(styleName, style)),
    })),
  };
}

/** `readTokens` 가 `tokens` 로 다시 읽는 `tokens.json` 의 내용. */
export function tokensFileOf(tokens: CanonicalTokens): JsonValue {
  const fields: Record<string, JsonValue> = {
    version: 1,
    color: {
      themes: tokens.themes.map((id) => ({ id, name: id })),
      tokens: [...(tokens.families.get("color")?.tokens ?? [])].map(([name, token]) => ({
        name,
        value: valueOut(token.value),
        usage: token.usage,
      })),
    },
    type: typeOut(tokens.type),
  };
  for (const [name, family] of tokens.families) {
    if (name !== "color") {
      fields[name] = familyOut(family);
    }
  }
  return fields;
}

/** 이어받을 기준본. 웹의 `tokens.json` 에서 `diffs` 가 가리키는 자리만 `claim` 사본의 값으로 바꾼 것이다. */
export function inheritedBaseline(
  web: unknown,
  copy: unknown,
  diffs: readonly TokenDiff[],
): JsonValue {
  return tokensFileOf(withSpots(readTokens(web), readTokens(copy), diffs));
}

/** 차이가 가리키는 자리의 값이 두 벌에서 같은가. */
export function sameAt(left: CanonicalTokens, right: CanonicalTokens, diff: TokenDiff): boolean {
  return JSON.stringify(valueAt(left, diff)) === JSON.stringify(valueAt(right, diff));
}
