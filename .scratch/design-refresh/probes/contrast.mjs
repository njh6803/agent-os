// design-refresh 명암비 프로브: 재탐색 디자인 파일의 쓰임새 토큰 값으로 짝마다의 명암비를 여덟 벌(테마 넷 × 모드 둘)에서 센다.
//   node .scratch/design-refresh/probes/contrast.mjs
//
// 디자인 파일이 재는 짝(그 파일 스크립트의 PAIRS 를 옮긴 것, 벌마다 35개)에, 컴포넌트의 상태 표가 쓰는데 디자인 파일이 재지
// 않은 짝 8개를 더한 43개가 명세의 짝이다. 그리고 디자인 파일의 상태 표가 적은 위험 버튼 누름(`bg-active`)의 짝 둘을 따로
// 잰다. 그 둘이 다크에서 미달해 명세는 누름 바탕을 `bg-selected` 로 바꿨다. 반투명 바탕(`bg-hover`, `bg-active`,
// `bg-selected`)은 디자인 파일처럼 그 아래 바탕에 겹친 색으로 잰다. 겹친 색은 채널마다 0~255 의 정수로 반올림한다(디자인
// 파일 스크립트의 `over` 와 같다). 반올림 없이 겹치면 판정이 뒤집히는 짝과, 반투명이 두 겹 겹치는 자리(명세의 판정 밖)도
// 함께 낸다.
// 값은 `design.mjs` 의 `readRefresh()` 가 돌려주는 디자인 토큰 JSON 에서 읽는다. 브라우저를 쓰지 않는다. 브라우저가 계산한
// 값으로 다시 재는 것은 반영한 뒤의 판정 스토리다.
// stdout 은 디자인 파일의 표와 대조한 행 수와 어긋남, 짝마다 여덟 벌의 가장 낮은 값과 그 벌, 기준에 못 미친 벌의 수다.

import { readRefresh } from "../../design-system/probes/tokens/design.mjs";

const design = readRefresh();
const { tokens } = design;
const THEMES = Object.keys(tokens.theme);
const MODES = ["light", "dark"];

const rgbOf = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const alphaOf = (hex) => (hex.length < 9 ? 1 : parseInt(hex.slice(7, 9), 16) / 255);

/**
 * 색을 바탕(RGB)에 겹친 RGB. 불투명이면 그 색이다. `round` 면 채널마다 정수로 반올림한다(디자인 파일 스크립트의 `over` 는
 * hex 로 돌려주므로 반올림한다).
 */
function over(hex, base, round) {
  const alpha = alphaOf(hex);
  const mixed = rgbOf(hex).map((v, i) => v * alpha + base[i] * (1 - alpha));
  return round ? mixed.map(Math.round) : mixed;
}

function luminance(rgb) {
  const [r, g, b] = rgb
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

/**
 * 바탕 쪽 RGB. `layers` 는 위에서 아래로의 토큰 이름이고 마지막이 불투명한 바탕이다. [바탕] 이거나 [반투명, 바탕] 이거나
 * [반투명, 반투명, 바탕] 이다.
 */
function surface(hex, layers, round) {
  const bottom = layers.at(-1);
  return layers
    .slice(0, -1)
    .reduceRight((base, name) => over(hex[name], base, round), rgbOf(hex[bottom]));
}

/** 글자 쪽과 바탕 쪽의 명암비. 글자 쪽도 반투명일 수 있어 바탕에 겹친다(지금 짝에는 없다). */
function pairRatio(hex, fg, layers, round) {
  const back = surface(hex, layers, round);
  return ratio(over(hex[fg], back, round), back);
}

// 바탕 쪽은 위에서 아래로의 토큰 이름이다.
const SURFACES = [["bg"], ["bg-raised"], ["bg-selected", "bg"], ["bg-hover", "bg-raised"]];
const LINK_SURFACES = [["bg"], ["bg-raised"], ["bg-hover", "bg-raised"]];

/** 디자인 파일 스크립트의 PAIRS 를 짝 목록으로 편 것. [글자 쪽, 바탕 쪽, 기준, 출처]. */
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

/**
 * 반투명이 두 겹 겹치는 자리. 명세의 판정(놓인 바탕 위의 한 겹)은 이것을 보지 않는다. 표의 행 올림(`bg-hover`, 행은
 * `bg-raised`) 안에 놓인 위험 버튼을 올리거나 누르는 경우다. 그 배치를 쓰는 앱이 본다.
 */
const TWO_LAYERS = [
  ["danger", ["bg-hover", "bg-hover", "bg-raised"], 4.5, "행 올림 안의 위험 버튼 올림"],
  ["danger", ["bg-selected", "bg-hover", "bg-raised"], 4.5, "행 올림 안의 위험 버튼 누름"],
];

const label = (layers) => layers.join("/");

// 디자인 파일의 표가 든 값과 이 프로브의 셈을 맞댄다. 표는 행마다 짝들의 가장 낮은 값을 "라이트 · 다크"로 든다.
const mismatches = [];
let compared = 0;
for (const table of design.themeTables) {
  const values = Object.fromEntries(MODES.map((mode) => [mode, semanticHex(table.key, mode)]));
  for (const row of table.rows) {
    const pairs = DESIGN_PAIRS.filter(([fg]) => fg === row.token);
    if (pairs.length === 0 || !/^\d/.test(row.ratio)) {
      continue;
    }
    compared += 1;
    const mine = MODES.map((mode) =>
      Math.min(...pairs.map(([fg, bg]) => pairRatio(values[mode], fg, bg, true))).toFixed(2),
    ).join(" · ");
    if (mine !== row.ratio) {
      mismatches.push(`${table.key} ${row.token} 표 ${row.ratio} 셈 ${mine}`);
    }
  }
}
console.log(
  `디자인 파일의 표와 대조한 행 ${String(compared)}, 어긋남 ${String(mismatches.length)}${mismatches.length ? `: ${mismatches.join("; ")}` : ""}`,
);

function report(group, pairs, round) {
  let failed = 0;
  for (const [fg, bg, min, source] of pairs) {
    const results = THEMES.flatMap((theme) =>
      MODES.map((mode) => ({
        at: `${theme}/${mode}`,
        value: pairRatio(semanticHex(theme, mode), fg, bg, round),
      })),
    );
    const lowest = results.reduce((a, b) => (b.value < a.value ? b : a));
    const below = results.filter((r) => r.value < min);
    failed += below.length;
    const detail = below.length ? ` 미달 ${below.map((r) => `${r.at} ${r.value.toFixed(3)}`).join(", ")}` : "";
    console.log(
      `${group} ${fg} / ${label(bg)} 기준 ${String(min)} 가장 낮음 ${lowest.value.toFixed(3)} (${lowest.at})${detail}${group === "디자인 파일" ? "" : ` — ${source}`}`,
    );
  }
  console.log(`${group} 짝 ${String(pairs.length)}개 × 여덟 벌, 미달 ${String(failed)}`);
}

report("디자인 파일", DESIGN_PAIRS, true);
report("컴포넌트", COMPONENT_PAIRS, true);
report("바꾸기 전", DESIGN_DANGER_PRESS, true);
report("두 겹(판정 밖)", TWO_LAYERS, true);

// 반올림 없이 겹치면 판정이 뒤집히는 짝. 명세의 짝 43개 가운데 반올림에 기대어 지나는 것을 찾는다.
const flipped = [];
for (const [fg, bg, min] of [...DESIGN_PAIRS, ...COMPONENT_PAIRS]) {
  for (const theme of THEMES) {
    for (const mode of MODES) {
      const hex = semanticHex(theme, mode);
      const rounded = pairRatio(hex, fg, bg, true);
      const exact = pairRatio(hex, fg, bg, false);
      if (rounded >= min !== exact >= min) {
        flipped.push(
          `${theme}/${mode} ${fg} / ${label(bg)} 반올림 ${rounded.toFixed(3)} 반올림 없이 ${exact.toFixed(3)} 기준 ${String(min)}`,
        );
      }
    }
  }
}
console.log(`반올림 없이 겹치면 판정이 뒤집히는 자리 ${String(flipped.length)}${flipped.length ? `: ${flipped.join("; ")}` : ""}`);
