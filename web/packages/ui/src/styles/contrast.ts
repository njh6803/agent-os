// 판정 스토리 Matrix 가 보는 쓰임새 토큰과 명암비 짝. 패키지 밖으로 내보내지 않는다.
import { contrastRatio } from "../testing";
import type { Mode } from "../themes";

/** 쓰임새 토큰 26개. 컴포넌트는 이것의 유틸리티(`bg-bg`, `text-muted` 등)만 쓴다. */
export const SEMANTIC_TOKENS = [
  "bg",
  "raised",
  "text",
  "muted",
  "border",
  "accent",
  "on-accent",
  "danger",
  "warning",
  "success",
  "info",
  "focus",
  "tint",
  "tint-hover",
  "tint-press",
  "accent-hover",
  "accent-press",
  "border-hover",
  "danger-tint",
  "danger-tint-press",
  "warning-tint",
  "success-tint",
  "info-tint",
  "disabled-surface",
  "disabled-text",
  "divider",
] as const;

export type SemanticToken = (typeof SEMANTIC_TOKENS)[number];

/** 글자 쪽, 바탕 쪽, 기준. */
export type ContrastPair = readonly [SemanticToken, SemanticToken, number];

// 디자인 파일이 재는 짝(대응표에서 기준이 있는 열과 상태용 토큰)에 컴포넌트가 쓰는데 디자인 파일이 재지 않은 짝(알림
// 제목과 그 안 버튼의 포커스 링, 진행 막대와 트랙)을 더했다. 성공 톤의 알림은 없어 `success-tint` 위의 제목 짝은 두지
// 않는다. 쓸 수 없음(`disabled-*`)은 명암비 기준의 대상이 아니다(design-system 명세의 "명암비 짝 43개").
export const CONTRAST_PAIRS: readonly ContrastPair[] = [
  ...(["text", "muted", "accent", "danger", "warning", "success", "info"] as const).flatMap(
    (name): ContrastPair[] => [
      [name, "bg", 4.5],
      [name, "raised", 4.5],
    ],
  ),
  ...(["border", "focus"] as const).flatMap((name): ContrastPair[] => [
    [name, "bg", 3],
    [name, "raised", 3],
  ]),
  ["on-accent", "accent", 4.5],
  ["text", "tint", 4.5],
  ["muted", "tint", 4.5],
  ["text", "tint-hover", 4.5],
  ["text", "tint-press", 4.5],
  ["on-accent", "accent-hover", 4.5],
  ["on-accent", "accent-press", 4.5],
  ["border-hover", "bg", 3],
  ["border-hover", "raised", 3],
  ["danger", "danger-tint", 4.5],
  ["muted", "danger-tint", 4.5],
  ["danger", "danger-tint-press", 4.5],
  ["warning", "warning-tint", 4.5],
  ["muted", "warning-tint", 4.5],
  ["success", "success-tint", 4.5],
  ["info", "info-tint", 4.5],
  ["muted", "info-tint", 4.5],
  ["text", "danger-tint", 4.5],
  ["text", "warning-tint", 4.5],
  ["text", "info-tint", 4.5],
  ["focus", "danger-tint", 3],
  ["focus", "warning-tint", 3],
  ["focus", "info-tint", 3],
  ["accent", "tint", 3],
  ["danger", "tint", 3],
];

/**
 * 한 벌(테마·모드)의 쓰임새 토큰 값으로 기준에 못 미치는 짝마다 메시지 하나. 메시지는 테마, 모드, 짝, 잰 값, 기준을
 * 든다. `value` 는 그 쓰임새 토큰의 계산값(#RRGGBB)을 돌려준다.
 */
export function contrastFailures(
  theme: string,
  mode: Mode,
  value: (name: SemanticToken) => string,
  pairs: readonly ContrastPair[] = CONTRAST_PAIRS,
): string[] {
  return pairs.flatMap(([foreground, background, minimum]) => {
    const ratio = contrastRatio(value(foreground), value(background));
    return ratio < minimum
      ? [`${theme}/${mode} ${foreground}/${background} ${ratio.toFixed(2)} < ${String(minimum)}`]
      : [];
  });
}
