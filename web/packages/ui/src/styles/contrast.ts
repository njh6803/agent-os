// 판정 스토리 Matrix 가 보는 쓰임새 토큰과 명암비 짝. 패키지 밖으로 내보내지 않는다.
import { composite, contrastRatio } from "../testing";
import type { Mode } from "../themes";

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
