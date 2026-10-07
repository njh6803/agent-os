// 정적 빌드를 내는 route(storybook.ts)의 경계. 인코딩한 `/`(`%2F`)는 URL 파서가 dot segment 로 접지 않아, 디코딩한 뒤
// 이어 붙이면 정적 빌드 밖을 가리킬 수 있다.
import { ORIGIN, expect, muk, test } from "./storybook.ts";

test("정적 빌드 밖을 가리키는 인코딩한 경로는 내지 않는다", async ({ page, storybook }) => {
  await storybook.open("atoms-button--primary", muk("light"));
  // 정적 빌드의 바로 위는 패키지 폴더이고 거기 package.json 이 있다.
  const response = await page.goto(`${ORIGIN}/..%2Fpackage.json`);
  expect(response?.status()).toBe(404);
});
