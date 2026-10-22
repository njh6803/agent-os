// 명암비 모듈(`@agent-os/ui/contrast`). 판정 스토리 Matrix 가 이 짝 표와 공식으로 판정하고, `web/tools` 쪽은 패키지
// 이름으로 들인다(design-reverse-sync 명세의 "명암비 계산을 부르는 길". 지금 부르는 것은 `web/tools/contrast-module.test.ts`
// 다). 상대 import 가 없는 한 파일이다. `web/tools` 의 루트 설정(`nodenext`)은 확장자 없는 상대 import 를 타입 검사에서
// 거부하고(TS2834·TS2835), Node 는 `"../testing"` 을 폴더 import 로 읽어 멈춘다
// (`.scratch/design-reverse-sync/probes/tools_import.mjs`). `.js` 를 붙인 상대 import 는 타입 검사를 지나도 이웃 `.ts`
// 를 찾지 못한 Node 가 멈춘다. 그래서 계산 함수와 모드 목록을 여기 정의하고 `testing`·`themes` 가 여기서 들인다. DOM
// 타입을 쓰는 판정 함수(`testing` 의 나머지)는 두지 않는다. 루트 설정의 `lib` 은 es2024 뿐이다.
// - contrastRatio: WCAG 2.2 의 대비. 불투명한 쓰임새 토큰의 계산값(#RRGGBB)을 받는다.
// - composite: 반투명 쓰임새 토큰(#RRGGBBAA)을 그 아래 바탕에 겹친 색. 채널마다 0~255 의 정수로 반올림한 #rrggbb 를
//   돌려준다. 반올림은 판정의 일부다. 디자인 파일 스크립트의 `over` 와 같은 셈이고(design-refresh 명세의 "반투명 바탕의
//   명암비"), 녹청 다크의 카드 안 위험 버튼 누름은 반올림하면 4.507, 하지 않으면 4.494 다.

/** `data-mode` 의 값. 속성이 없으면 시스템 설정(`prefers-color-scheme`)을 따른다. */
export const MODES = ["light", "dark"] as const;

export type Mode = (typeof MODES)[number];

type Channels = readonly [number, number, number];

/** WCAG 2.2 의 대비. 인자는 `#RRGGBB` 이고 대소문자를 가리지 않는다. */
export function contrastRatio(a: string, b: string): number {
  const first = luminance(opaqueChannels(a));
  const second = luminance(opaqueChannels(b));
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

/**
 * `top` 을 불투명한 `bottom`(`#RRGGBB`)에 알파로 겹친 색. `top` 은 `#RRGGBB` 이거나 `#RRGGBBAA` 이고, 불투명이면 그
 * 색이다. 채널마다 0~255 의 정수로 반올림한 소문자 `#rrggbb` 를 돌려준다.
 */
export function composite(top: string, bottom: string): string {
  const match = /^#([0-9a-f]{6})([0-9a-f]{2})?$/i.exec(top.trim());
  if (match === null) {
    throw new Error(`#RRGGBB 나 #RRGGBBAA 가 아니다: "${top}"`);
  }
  const [, color = "", alphaHex = "ff"] = match;
  const alpha = Number.parseInt(alphaHex, 16) / 255;
  const above = opaqueChannels(`#${color}`);
  const below = opaqueChannels(bottom);
  return `#${above
    .map((channel, index) => {
      const mixed = Math.round(channel * alpha + (below[index] ?? 0) * (1 - alpha));
      return mixed.toString(16).padStart(2, "0");
    })
    .join("")}`;
}

function opaqueChannels(hex: string): Channels {
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

/**
 * 쓰임새 토큰 23개. 이름은 디자인 파일 그대로이고, 그림자 하나만 코드에서 `shadow-color` 다(design-refresh 명세의 "색 —
 * 쓰임새 토큰"). 컴포넌트는 앞의 22개의 유틸리티(`bg-bg-raised`, `text-text-muted` 등)만 쓴다.
 */
export const SEMANTIC_TOKENS = [
  "bg",
  "bg-raised",
  "text",
  "text-muted",
  "border",
  "accent",
  "on-accent",
  "danger",
  "warning",
  "success",
  "info",
  "focus-ring",
  "border-control",
  "primary",
  "on-primary",
  "primary-hover",
  "primary-active",
  "bg-hover",
  "bg-active",
  "bg-selected",
  "text-disabled",
  "bg-disabled",
  "shadow-color",
] as const;

export type SemanticToken = (typeof SEMANTIC_TOKENS)[number];

/** 반투명 쓰임새 토큰. 값은 `#RRGGBBAA` 이고 명암비는 그 아래 바탕에 겹쳐 잰다. */
export const TRANSLUCENT_TOKENS = [
  "bg-hover",
  "bg-active",
  "bg-selected",
  "shadow-color",
] as const satisfies readonly SemanticToken[];

/** 짝의 바탕 쪽. 쓰임새 토큰 하나이거나 [반투명 쓰임새 토큰, 그 아래 불투명한 바탕]이다. */
export type Surface = SemanticToken | readonly [SemanticToken, SemanticToken];

/** 글자 쪽, 바탕 쪽, 기준. */
export type ContrastPair = readonly [SemanticToken, Surface, number];

// 바탕 넷. 놓인 바탕 둘과, 그 위에 반투명을 한 겹 겹친 것 둘이다. 판정은 놓인 바탕 위의 한 겹까지다(명세의 "판정은 놓인
// 바탕 위의 한 겹까지다").
const SURFACES: readonly Surface[] = [
  "bg",
  "bg-raised",
  ["bg-selected", "bg"],
  ["bg-hover", "bg-raised"],
];

// 짝 43개(design-refresh 명세의 "명암비 짝 43개"). 앞의 35개는 디자인 파일 스크립트가 재는 짝을 편 것이고, 뒤의 8개는
// 컴포넌트가 쓰는데 디자인 파일이 재지 않은 짝이다. `border`(장식)와 쓸 수 없음(`text-disabled`, `bg-disabled`)은 명암비
// 기준의 대상이 아니다.
export const CONTRAST_PAIRS: readonly ContrastPair[] = [
  ...(["text", "text-muted"] as const).flatMap((name) =>
    SURFACES.map((surface): ContrastPair => [name, surface, 4.5]),
  ),
  ...(["bg", "bg-raised", ["bg-hover", "bg-raised"]] as const).map((surface): ContrastPair => [
    "accent",
    surface,
    4.5,
  ]),
  ["on-accent", "accent", 4.5],
  ...(["danger", "warning", "success", "info"] as const).flatMap((name) =>
    SURFACES.map((surface): ContrastPair => [name, surface, 4.5]),
  ),
  ...(["focus-ring", "border-control"] as const).flatMap((name): ContrastPair[] => [
    [name, "bg", 3],
    [name, "bg-raised", 3],
  ]),
  ...(["primary", "primary-hover", "primary-active"] as const).map((surface): ContrastPair => [
    "on-primary",
    surface,
    4.5,
  ]),
  // 보조 버튼과 투명 아이콘 버튼의 올림·누름. 바탕이 없어 놓인 바탕이 비친다.
  ["text", ["bg-hover", "bg"], 4.5],
  ["text", ["bg-active", "bg"], 4.5],
  ["text", ["bg-active", "bg-raised"], 4.5],
  // 위험 버튼의 올림과 카드 안의 누름. `bg` 위의 누름은 위 디자인 파일의 짝에 있다.
  ["danger", ["bg-hover", "bg"], 4.5],
  ["danger", ["bg-selected", "bg-raised"], 4.5],
  // 진행 막대의 채움과 트랙. 글자가 아니라 3 이다.
  ["text-muted", ["bg-active", "bg"], 3],
  ["text-muted", ["bg-active", "bg-raised"], 3],
  // 꺼진 스위치의 손잡이와 트랙. 명암비는 대칭이라 위 `border-control`/`bg-raised` 와 같은 측정이지만 스위치의 뜻으로 둔다.
  ["bg-raised", "border-control", 3],
];

/** 바탕 쪽의 이름. 겹친 바탕은 위에서 아래로 `+` 로 잇는다. */
function surfaceName(surface: Surface): string {
  return typeof surface === "string" ? surface : surface.join("+");
}

/**
 * 한 벌(테마·모드)의 쓰임새 토큰 값으로 기준에 못 미치는 짝마다 메시지 하나. 메시지는 테마, 모드, 짝, 잰 값, 기준을
 * 든다. `value` 는 그 쓰임새 토큰의 계산값(`#RRGGBB`, 반투명은 `#RRGGBBAA`)을 돌려준다. 반투명은 아래 바탕에 겹쳐 채널마다
 * 반올림한 색으로 잰다(`composite`).
 */
export function contrastFailures(
  theme: string,
  mode: Mode,
  value: (name: SemanticToken) => string,
  pairs: readonly ContrastPair[] = CONTRAST_PAIRS,
): string[] {
  const surfaceColor = (surface: Surface): string =>
    typeof surface === "string" ? value(surface) : composite(value(surface[0]), value(surface[1]));
  return pairs.flatMap(([foreground, background, minimum]) => {
    const behind = surfaceColor(background);
    const ratio = contrastRatio(composite(value(foreground), behind), behind);
    // 잰 값은 두 자리로 내려 적는다. 반올림하면 4.497 이 "4.50 < 4.5" 로 찍혀 메시지가 기준을 넘은 것처럼 읽힌다.
    const shown = (Math.floor(ratio * 100) / 100).toFixed(2);
    return ratio < minimum
      ? [`${theme}/${mode} ${foreground}/${surfaceName(background)} ${shown} < ${String(minimum)}`]
      : [];
  });
}
