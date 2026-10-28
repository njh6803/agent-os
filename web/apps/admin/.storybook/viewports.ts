// 관리 화면을 그리는 창 두 벌(admin-style 명세 "Storybook과 사진 비교"). 넓은 것은 옆 탐색이 서는 폭, 좁은 것은 휴대폰
// 폭이다. 미리보기가 viewport 항목으로 싣고(preview.tsx), 스토리 테스트 프로젝트 둘(뿌리 vitest.config.ts)이 그 키로 고르며,
// 사진 비교의 프로젝트 둘(visual/playwright.config.ts)이 같은 크기로 찍는다.
export const VIEWPORTS = {
  wide: { width: 1280, height: 900 },
  narrow: { width: 320, height: 640 },
} as const;

export type ViewportKey = keyof typeof VIEWPORTS;
