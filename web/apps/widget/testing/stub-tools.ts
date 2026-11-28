// 빌드 도구를 흉내 내는 빈 모듈(testing/spawn-hooks.ts 가 `WIDGET_TEST_TOOLS=stub` 일 때 글꼴 복사와 페이지 안 번들의 빌드 자리에
// 세운다). 빌드가 사이트 파일을 읽지 않는 것을 실제 Vite 를 돌리지 않고 보려는 것이다.

/** 글꼴 복사를 하지 않는다. */
export function copyFonts(): void {}

/** 페이지 안 번들을 짓지 않는다. */
export function buildElement(): Promise<void> {
  return Promise.resolve();
}
