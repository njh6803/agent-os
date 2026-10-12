// design-refresh 명암비 프로브: 재탐색 디자인 파일의 쓰임새 토큰 값으로 짝마다의 명암비를 여덟 벌(테마 넷 × 모드 둘)에서 센다.
//   node .scratch/design-refresh/probes/contrast.mjs
//
// 디자인 파일이 재는 짝(그 파일 스크립트의 PAIRS 를 옮긴 것, 벌마다 35개)에, 컴포넌트의 상태 표가 쓰는데 디자인 파일이 재지
// 않은 짝 8개를 더한 43개가 명세의 짝이다. 그리고 디자인 파일의 상태 표가 적은 위험 버튼 누름(`bg-active`)의 짝 둘을 따로
// 잰다. 그 둘이 다크에서 미달해 명세는 누름 바탕을 `bg-selected` 로 바꿨다. 반투명 바탕(`bg-hover`, `bg-active`,
// `bg-selected`)은 디자인 파일처럼 그 아래 바탕에 겹친 색으로 잰다.
// 값은 `design.mjs` 의 `readRefresh()` 가 돌려주는 디자인 토큰 JSON 에서 읽는다. 브라우저를 쓰지 않는다. 브라우저가 계산한
// 값으로 다시 재는 것은 반영한 뒤의 판정 스토리다.
// stdout 은 짝마다 여덟 벌의 가장 낮은 값과 그 벌, 기준에 못 미친 벌의 수다. 디자인 파일의 표가 든 값과 이 프로브가 셈한
// 값이 어긋나면(소수 둘째 자리) 먼저 그것을 적는다.

import { readRefresh } from "../../design-system/probes/tokens/design.mjs";

const design = readRefresh();
const { tokens } = design;
const THEMES = Object.keys(tokens.theme);
const MODES = ["light", "dark"];

const rgbOf = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const toHex = (rgb) =>
  `#${rgb.map((v) => Math.round(v).toString(16).padStart(2, "0")).join("").toUpperCase()}`;

/** 반투명 색(#RRGGBBAA)을 바탕에 겹친다. 불투명이면 그대로다. 디자인 파일 스크립트의 `over` 와 같은 셈이다. */
function over(hex, base) {
  if (hex.length < 9) {
    return hex.toUpperCase();
  }
  const alpha = parseInt(hex.slice(7, 9), 16) / 255;
  const top = rgbOf(hex);
  const bottom = rgbOf(base);
  return toHex(top.map((v, i) => v * alpha + bottom[i] * (1 - alpha)));
}

function luminance(hex) {
  const [r, g, b] = rgbOf(hex)
    .map((v) => v / 255)
    .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function ratio(a, b) {
  const [x, y] = [luminance(a), luminance(b)];
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

/** 한 벌의 쓰임새 토큰 hex. */
function semanticHex(theme, mode) {
  const t = tokens.theme[theme];
  return Object.fromEntries(
    Object.entries(t.semantic[mode]).map(([name, ref]) => {
      const dot = ref.indexOf(".");
      return [name, t.primitive[ref.slice(0, dot)][ref.slice(dot + 1)]];
    }),
  );
}

// 바탕 쪽은 [바탕] 이거나 [반투명, 그 아래 바탕] 이다.
const SURFACES = [["bg"], ["bg-raised"], ["bg-selected", "bg"], ["bg-hover", "bg-raised"]];
const LINK_SURFACES = [["bg"], ["bg-raised"], ["bg-hover", "bg-raised"]];

/** 디자인 파일 스크립트의 PAIRS 를 짝 목록으로 편 것. [이름, 글자 쪽, 바탕 쪽, 기준, 출처]. */
const DESIGN_PAIRS = [
  ...SURFACES.map((s) => ["text", s, 4.5]),
  ...SURFACES.map((s) => ["text-muted", s, 4.5]),
  ...LINK_SURFACES.map((s) => ["accent", s, 4.5]),
  ["on-accent", ["accent"], 4.5],
  ...["danger", "warning", "success", "info"].flatMap((name) => SURFACES.map((s) => [name, s, 4.5])),
  ...["focus-ring", "border-control"].flatMap((name) => [
    [name, ["bg"], 3],
    [name, ["bg-raised"], 3],
  ]),
  ...["primary", "primary-hover", "primary-active"].map((s) => ["on-primary", [s], 4.5]),
].map(([fg, bg, min]) => [fg, bg, min, "디자인 파일"]);

/**
 * 컴포넌트의 상태 표(디자인 파일 2절, `readRefresh().components` 가 내는 것)를 읽고 손으로 옮긴 짝 가운데 디자인 파일이 재지
 * 않은 것. 출처는 상태 표의 칸이다.
 * - 보조·위험 버튼과 투명 아이콘 버튼은 바탕이 없어 놓인 바탕(bg, bg-raised)이 비치고, 올림·누름에 반투명 바탕을 겹친다.
 * - 위험 버튼의 누름은 명세가 바꾼 `bg-selected` 다. `bg` 위의 그 짝은 디자인 파일의 짝(상태 × `bg-selected`/`bg`)에 이미
 *   있어 여기 두지 않는다.
 * - 진행 막대의 채움(text-muted)은 글자가 아니라 누름 바탕(bg-active) 트랙 위의 3:1 이다(디자인 파일 PAIRS 의 주석).
 * - 꺼진 스위치의 손잡이(bg-raised)는 트랙(border-control) 위에 놓인다.
 */
const COMPONENT_PAIRS = [
  ["text", ["bg-hover", "bg"], 4.5, "보조 버튼 올림, 아이콘 버튼 올림"],
  ["text", ["bg-active", "bg"], 4.5, "보조 버튼 누름, 아이콘 버튼 누름"],
  ["text", ["bg-active", "bg-raised"], 4.5, "보조 버튼 누름(카드 안)"],
  ["danger", ["bg-hover", "bg"], 4.5, "위험 버튼 올림"],
  ["danger", ["bg-selected", "bg-raised"], 4.5, "위험 버튼 누름(카드 안)"],
  ["text-muted", ["bg-active", "bg"], 3, "진행 막대 채움과 트랙"],
  ["text-muted", ["bg-active", "bg-raised"], 3, "진행 막대 채움과 트랙(카드 안)"],
  ["bg-raised", ["border-control"], 3, "꺼진 스위치의 손잡이와 트랙"],
];

/**
 * 디자인 파일의 상태 표가 적은 위험 버튼 누름(`bg-active`). 이 프로브의 첫 실행에서 다크의 여덟 자리 모두 미달해 명세가
 * 누름 바탕을 `bg-selected` 로 바꿨다(사용자가 골랐다). 바꾼 근거로 남겨 둔다.
 */
const DESIGN_DANGER_PRESS = [
  ["danger", ["bg-active", "bg"], 4.5, "디자인 파일의 위험 버튼 누름"],
  ["danger", ["bg-active", "bg-raised"], 4.5, "디자인 파일의 위험 버튼 누름(카드 안)"],
];

function surface(hex, [top, base]) {
  return base === undefined ? hex[top] : over(hex[top], hex[base]);
}

const label = ([top, base]) => (base === undefined ? top : `${top}/${base}`);

// 디자인 파일의 표가 든 값과 이 프로브의 셈을 맞댄다. 표는 행마다 짝들의 가장 낮은 값을 "라이트 · 다크"로 든다.
const mismatches = [];
for (const table of design.themeTables) {
  const values = Object.fromEntries(MODES.map((mode) => [mode, semanticHex(table.key, mode)]));
  for (const row of table.rows) {
    const pairs = DESIGN_PAIRS.filter(([fg]) => fg === row.token);
    if (pairs.length === 0 || !/^\d/.test(row.ratio)) {
      continue;
    }
    const mine = MODES.map((mode) =>
      Math.min(...pairs.map(([fg, bg]) => ratio(values[mode][fg], surface(values[mode], bg)))).toFixed(2),
    ).join(" · ");
    if (mine !== row.ratio) {
      mismatches.push(`${table.key} ${row.token} 표 ${row.ratio} 셈 ${mine}`);
    }
  }
}
console.log(`디자인 파일의 표와 어긋남 ${String(mismatches.length)}${mismatches.length ? `: ${mismatches.join("; ")}` : ""}`);

for (const [group, pairs] of [
  ["디자인 파일", DESIGN_PAIRS],
  ["컴포넌트", COMPONENT_PAIRS],
  ["바꾸기 전", DESIGN_DANGER_PRESS],
]) {
  let failed = 0;
  for (const [fg, bg, min, source] of pairs) {
    const results = THEMES.flatMap((theme) =>
      MODES.map((mode) => {
        const values = semanticHex(theme, mode);
        return { at: `${theme}/${mode}`, value: ratio(values[fg], surface(values, bg)) };
      }),
    );
    const lowest = results.reduce((a, b) => (b.value < a.value ? b : a));
    const below = results.filter((r) => r.value < min);
    failed += below.length;
    const detail = below.length ? ` 미달 ${below.map((r) => `${r.at} ${r.value.toFixed(2)}`).join(", ")}` : "";
    console.log(
      `${group} ${fg} / ${label(bg)} 기준 ${String(min)} 가장 낮음 ${lowest.value.toFixed(2)} (${lowest.at})${detail}${group === "디자인 파일" ? "" : ` — ${source}`}`,
    );
  }
  console.log(`${group} 짝 ${String(pairs.length)}개 × 여덟 벌, 미달 ${String(failed)}`);
}
