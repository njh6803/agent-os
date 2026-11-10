// 익명 식별자 쿠키. 요청에서 값을 고르는 판정과 `Set-Cookie` 의 속성을 본다.

import { randomUUID } from "node:crypto";
import { expect, test } from "vitest";
import { anonymousCookie, anonymousIdOf } from "./anonymous-cookie.ts";

const ID = "3f2b8c1e-5d4a-4e7b-9a6c-0d1e2f3a4b5c";
const HTTP_ORIGIN = "http://portal.example";
const HTTPS_ORIGIN = "https://portal.example";

test("소문자 UUID v4 값의 portal_anon 쿠키를 식별자로 읽는다", () => {
  expect(anonymousIdOf([{ name: "portal_anon", value: ID }])).toBe(ID);
  expect(anonymousIdOf([{ name: "portal_anon", value: randomUUID() }])).toMatch(/^[0-9a-f-]{36}$/u);
});

test("쿠키가 없으면 식별자가 없다", () => {
  expect(anonymousIdOf([])).toBeUndefined();
  expect(anonymousIdOf([{ name: "other", value: ID }])).toBeUndefined();
});

test("꼴이 틀린 값은 없는 것으로 본다", () => {
  const wrong = [
    "",
    "abc",
    ID.toUpperCase(),
    // v4 가 아닌 버전 자리
    "3f2b8c1e-5d4a-1e7b-9a6c-0d1e2f3a4b5c",
    // 변형 자리가 8, 9, a, b 밖
    "3f2b8c1e-5d4a-4e7b-1a6c-0d1e2f3a4b5c",
    // 36자가 아니다
    `${ID}0`,
    ID.slice(1),
    // 16진수가 아닌 글자
    "3f2b8c1e-5d4a-4e7b-9a6c-0d1e2f3a4b5g",
    // 앞뒤 공백
    ` ${ID}`,
    `${ID} `,
  ];

  for (const value of wrong) {
    expect(anonymousIdOf([{ name: "portal_anon", value }]), JSON.stringify(value)).toBeUndefined();
  }
});

test("같은 이름이 둘 이상 실리면 첫 것을 쓴다", () => {
  const other = randomUUID();

  expect(
    anonymousIdOf([
      { name: "portal_anon", value: ID },
      { name: "portal_anon", value: other },
    ]),
  ).toBe(ID);
});

test("첫 것의 꼴이 틀리면 뒤의 꼴이 맞는 것으로 넘어가지 않고 없는 것으로 본다", () => {
  expect(
    anonymousIdOf([
      { name: "portal_anon", value: "broken" },
      { name: "portal_anon", value: ID },
    ]),
  ).toBeUndefined();
});

test("접두가 붙은 이름은 다른 쿠키다", () => {
  expect(anonymousIdOf([{ name: "__Host-portal_anon", value: ID }])).toBeUndefined();
  expect(anonymousIdOf([{ name: "__Secure-portal_anon", value: ID }])).toBeUndefined();
});

test("Set-Cookie 는 사이트 경로와 30일 수명과 HttpOnly 와 SameSite=Strict 를 단다", () => {
  const header = anonymousCookie({ id: ID, siteName: "demo", publicOrigin: HTTP_ORIGIN });

  expect(header.split("; ")).toEqual([
    `portal_anon=${ID}`,
    "HttpOnly",
    "SameSite=Strict",
    "Path=/portal/sites/demo",
    "Max-Age=2592000",
  ]);
});

test("Secure 는 https 공개 출처일 때만 붙는다", () => {
  const secure = anonymousCookie({ id: ID, siteName: "demo", publicOrigin: HTTPS_ORIGIN });
  const plain = anonymousCookie({ id: ID, siteName: "demo", publicOrigin: HTTP_ORIGIN });

  expect(secure.split("; ")).toContain("Secure");
  expect(plain.split("; ")).not.toContain("Secure");
});

test("사이트마다 쿠키 경로가 다르다", () => {
  expect(anonymousCookie({ id: ID, siteName: "alpha", publicOrigin: HTTP_ORIGIN })).toContain(
    "Path=/portal/sites/alpha",
  );
  expect(anonymousCookie({ id: ID, siteName: "beta", publicOrigin: HTTP_ORIGIN })).toContain(
    "Path=/portal/sites/beta",
  );
});
