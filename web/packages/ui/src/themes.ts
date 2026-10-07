// 테마 목록. 테마는 색과 글꼴의 한 벌이고 키가 `data-theme` 의 값이다(ADR 0026 의 2026-10-06 이력). Storybook 의
// globals, 판정 스토리, 앱의 고르기 화면과 값 검사가 이 목록을 읽는다. 테마를 하나 더하면 이 목록의 한 줄과 디자인 토큰
// CSS(`styles/theme.css`)의 원색 66개·고정폭 글꼴·테마 선택자를 함께 적는다.

export interface ThemeEntry {
  /** `data-theme` 의 값. 로마자다. */
  readonly key: string;
  /** 화면에 보이는 이름. */
  readonly name: string;
}

export const THEMES = [
  { key: "muk", name: "먹" },
  { key: "cheongnok", name: "청록" },
  { key: "gongmun", name: "공문" },
  { key: "hwangto", name: "황토" },
  { key: "jadu", name: "자두" },
] as const satisfies readonly ThemeEntry[];

export type ThemeKey = (typeof THEMES)[number]["key"];

/** 사이트나 운영자가 고르지 않았을 때의 테마. 속성이 없는 문서와 호스트도 이 값으로 그린다. */
export const DEFAULT_THEME: ThemeKey = "muk";

/** `data-mode` 의 값. 속성이 없으면 시스템 설정(`prefers-color-scheme`)을 따른다. */
export const MODES = ["light", "dark"] as const;

export type Mode = (typeof MODES)[number];
