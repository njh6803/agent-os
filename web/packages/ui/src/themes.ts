// 테마 목록. 키가 `data-theme` 의 값이다(ADR 0026 의 둘째 2026-10-06 이력과 셋째 2026-10-12 이력). 테마는 색만 고르고
// 글꼴·굵기·크기·모서리는 고르지 않는다. 순서는 디자인 파일의 것이다. Storybook 의 globals, 판정 스토리, 앱의 고르기
// 화면과 값 검사가 이 목록을 읽는다. 테마를 하나 더하면 이 목록의 한 줄과 디자인 토큰 CSS(`styles/theme.css`)의 원색
// 블록 하나(회색 13단계와 다섯 계열의 11단계)를 함께 적고, 주 버튼이 강조색이면 그 CSS 의 `primary` 묶음을 덮는 선택자와
// 판정 스토리 Matrix 의 강조색 테마 목록(`ACCENT_PRIMARY`)에 그 키를 더한다. Matrix 는 이 목록의 키와 순서도 글자로 본다.

export interface ThemeEntry {
  /** `data-theme` 의 값. 로마자다. */
  readonly key: string;
  /** 화면에 보이는 이름. */
  readonly name: string;
}

export const THEMES = [
  { key: "guncheong", name: "군청" },
  { key: "nokcheong", name: "녹청" },
  { key: "jacho", name: "자초" },
  { key: "jjokbit", name: "쪽빛" },
] as const satisfies readonly ThemeEntry[];

export type ThemeKey = (typeof THEMES)[number]["key"];

/** 사이트나 운영자가 고르지 않았을 때의 테마. 속성이 없는 문서와 호스트도 이 값으로 그린다. */
export const DEFAULT_THEME: ThemeKey = "nokcheong";

/** `data-mode` 의 값. 속성이 없으면 시스템 설정(`prefers-color-scheme`)을 따른다. */
export const MODES = ["light", "dark"] as const;

export type Mode = (typeof MODES)[number];

/**
 * `data-density` 의 값. 촘촘(compact)과 보통(regular)이고 테마·모드와 같은 요소에 단다. 속성이 없으면 화면 폭 768px
 * 이상에서 촘촘, 미만에서 보통이다(ADR 0026 의 2026-10-12 이력). 관리 화면은 달지 않고 위젯은 보통을 단다.
 */
export const DENSITIES = ["compact", "regular"] as const;

export type Density = (typeof DENSITIES)[number];
