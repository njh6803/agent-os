// 고지 전문 짓기. 쿠키 문장의 일수는 인자로 받은 쿠키 수명에서 그려진다.

import { expect, test } from "vitest";
import { COOKIE_LIFETIME_DAYS } from "./cookie-policy.ts";
import { noticeText } from "./notice.ts";

const FIRST =
  "이 페이지에서 보낸 질문과 받은 출력은 기록되고, 출력을 만들기 위해 모델 API로 보내집니다.";
const THIRD = "이름, 연락처, 주민등록번호 같은 개인정보를 질문에 넣지 마세요.";

function cookieSentence(days: number): string {
  return `이 브라우저를 알아보기 위해 익명 식별자를 쿠키로 둡니다. 쿠키는 마지막으로 질문한 뒤 ${String(days)}일 동안 남습니다.`;
}

test("사이트가 고지를 적지 않으면 기본 글 세 문단이 차례로 선다", () => {
  expect(noticeText(undefined, COOKIE_LIFETIME_DAYS)).toBe(
    [FIRST, cookieSentence(COOKIE_LIFETIME_DAYS), THIRD].join("\n\n"),
  );
});

test("사이트가 고지를 적으면 그 글 끝에 쿠키 문장이 붙고 기본 글은 들지 않는다", () => {
  const text = noticeText("우리 사이트의 고지입니다.", COOKIE_LIFETIME_DAYS);

  expect(text).toBe(`우리 사이트의 고지입니다.\n\n${cookieSentence(COOKIE_LIFETIME_DAYS)}`);
  expect(text).not.toContain(FIRST);
  expect(text).not.toContain(THIRD);
});

test("쿠키 문장의 일수는 인자로 넘긴 쿠키 수명에서 그려진다", () => {
  // 30 을 글로 박은 구현은 상수만 넘기는 시험으로는 잡히지 않아, 30 이 아닌 값을 넘긴다.
  const basic = noticeText(undefined, 7);
  const written = noticeText("적은 글", 7);

  expect(basic).toContain("7일 동안 남습니다.");
  expect(written).toContain("7일 동안 남습니다.");
  expect(basic).not.toContain("30일");
  expect(written).not.toContain("30일");
});
