// 정적 빌드를 내는 route(index.ts)의 성질.
// - 경계. 인코딩한 `/`(`%2F`)는 URL 파서가 dot segment 로 접지 않아, 디코딩한 뒤 이어 붙이면 정적 빌드 밖을 가리킬 수 있다.
// - play 맥락의 `userEvent` 가 비어 있는 것. 이 출처는 보안 맥락이 아니라 `navigator.clipboard` 가 없고, Storybook 10.6.1 은
//   그것이 있을 때만 play 맥락의 `userEvent` 를 채운다(index.ts 머리 주석). 그래서 사진은 play 가 그 `userEvent` 로 바꾼
//   상태를 담지 않는다. 출처가 보안 맥락이 되거나 Storybook 이 clipboard 없이도 채우게 바뀌면 play 가 그 호출을 지나 이어
//   돌고, 기존 사진이 그 뒤 상태가 든 그림으로 한꺼번에 바뀌어 사진 비교가 빨개진다. 사진만으로는 까닭이 보이지 않아 이
//   테스트가 그 까닭을 이름으로 알린다.
import { ORIGIN, expect, inDefaultTheme, test } from "./storybook.ts";

test("정적 빌드 밖을 가리키는 인코딩한 경로는 내지 않는다", async ({ page, storybook }) => {
  await storybook.open("atoms-button--primary", inDefaultTheme("light", "regular"));
  // 정적 빌드의 바로 위는 패키지 폴더이고 거기 package.json 이 있다.
  const response = await page.goto(`${ORIGIN}/..%2Fpackage.json`);
  expect(response?.status()).toBe(404);
});

test("정적 빌드의 play 맥락은 userEvent 가 비어 Typing 의 play 가 첫 입력에서 멈추고 넣으려던 글이 그림에 없다", async ({
  page,
  storybook,
}) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });
  // Typing 의 play 는 칸을 찾은 뒤 처음 하는 일이 `userEvent.type` 이다.
  await storybook.open("molecules-textfield--typing", inDefaultTheme("light", "regular"));
  // 까닭: Storybook 10.6.1 은 `navigator.clipboard` 가 있을 때만 play 맥락의 `userEvent` 를 채우는데 이 출처에는 그것이 없다.
  expect(
    await page.evaluate(() => ({
      secure: window.isSecureContext,
      clipboard: typeof navigator.clipboard,
    })),
  ).toEqual({ secure: false, clipboard: "undefined" });
  // 표지: play 가 실제로 돌다 빈 `userEvent` 의 `type` 에서 멈췄다. 이것이 없으면 play 가 아예 돌지 않아 칸이 빈 것과
  // 가르지 못한다.
  expect(errors, "콘솔의 오류").toContainEqual(expect.stringMatching(/\.type is not a function/));
  // 그림: play 가 넣으려던 글이 두 칸 모두 없다.
  await expect(page.getByRole("textbox", { name: "플러그인 이름" })).toHaveValue("");
  await expect(page.getByRole("textbox", { name: "거부 사유" })).toHaveValue("");
});
