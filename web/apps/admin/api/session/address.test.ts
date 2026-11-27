// 로그인 화면의 주소 규칙(admin-login 명세 "관리 화면의 페이지와 주소"의 `next`, "https가 아닌 주소"). 순수한 함수라 화면 없이
// 본다. 같은 출처가 아닌 주소와 경로만 떼면 다른 사이트로 읽히는 주소를 `next` 로 받지 않는지가 이 시험의 일이다.

import { describe, expect, test } from "vitest";
import { canSignInAt, loginAddress, nextTarget, noticeOf } from "./address";

const ORIGIN = "https://admin.example:8443";

describe("로그인 뒤에 돌아갈 곳(next)", () => {
  test.each([
    ["경로와 질의가 든 같은 출처의 주소를 받는다", "/chat?x=1", `${ORIGIN}/chat?x=1`],
    ["절대 주소도 출처가 같으면 받는다", `${ORIGIN}/runs`, `${ORIGIN}/runs`],
    [
      "출처가 같고 경로가 겹빗금으로 시작하면 절대 주소로 돌려준다",
      `${ORIGIN}//evil.test/x`,
      `${ORIGIN}//evil.test/x`,
    ],
  ])("%s", (_name, raw, expected) => {
    expect(nextTarget(raw, ORIGIN)).toBe(expected);
  });

  test.each([
    ["값이 없으면 받지 않는다", null],
    ["빈 값은 받지 않는다", ""],
    ["빗금 둘로 시작하면 다른 사이트다", "//evil.test"],
    ["빗금 사이의 탭은 지워져 다른 사이트가 된다", "/\t/evil.test"],
    ["빗금 사이의 줄바꿈은 지워져 다른 사이트가 된다", "/\n/evil.test"],
    ["역빗금도 빗금으로 읽혀 다른 사이트가 된다", "/\\evil.test"],
    ["퍼센트로 쓴 글자로 가린 로그인 화면도 받지 않는다", "/%6cogin"],
    ["다른 출처의 절대 주소는 받지 않는다", "https://evil.test/"],
    ["같은 호스트라도 포트가 다르면 다른 출처다", "https://admin.example/runs"],
    ["http 로 바꾼 주소는 다른 출처다", "http://admin.example:8443/runs"],
    ["로그인 화면으로 돌아가지 않는다", "/login"],
    ["질의가 붙은 로그인 화면도 받지 않는다", "/login?next=%2Fruns"],
    ["끝 빗금이 붙은 로그인 화면도 받지 않는다", "/login/"],
    ["비밀번호 정하기 화면으로 돌아가지 않는다", "/set-password"],
    ["javascript 주소는 받지 않는다", "javascript:alert(1)"],
  ])("%s", (_name, raw) => {
    expect(nextTarget(raw, ORIGIN)).toBeNull();
  });
});

describe("로그인 화면의 알림 값", () => {
  test.each(["logged-out", "expired", "password-set"])("%s 는 받는다", (value) => {
    expect(noticeOf(value)).toBe(value);
  });

  test.each([null, "", "unknown", "toString", "__proto__"])("%s 는 무시한다", (value) => {
    expect(noticeOf(value)).toBeNull();
  });
});

describe("로그인 화면의 주소를 짓는다", () => {
  test("아무것도 없으면 경로만이다", () => {
    expect(loginAddress({})).toBe("/login");
  });

  test("돌아갈 곳은 질의 글자로 감싸 싣는다", () => {
    expect(loginAddress({ next: "/runs?status=failed" })).toBe(
      "/login?next=%2Fruns%3Fstatus%3Dfailed",
    );
  });

  test("알림을 함께 싣는다", () => {
    expect(loginAddress({ next: "/", notice: "expired" })).toBe("/login?next=%2F&notice=expired");
  });
});

describe("이 주소에서 로그인할 수 있는가", () => {
  test.each([
    "https://admin.example/",
    "http://localhost:3000/",
    "http://127.0.0.1:3000/",
    "http://[::1]:3000/",
  ])("%s 는 된다", (address) => {
    expect(canSignInAt(new URL(address))).toBe(true);
  });

  test.each(["http://admin.example/", "http://192.168.0.10:3000/", "http://localhost.evil.test/"])(
    "%s 는 https 가 아니라 안 된다",
    (address) => {
      expect(canSignInAt(new URL(address))).toBe(false);
    },
  );
});
