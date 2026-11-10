// `Cookie` 요청 헤더 읽기. 같은 이름이 여럿이면 실린 차례를 지킨다(첫 것을 쓰는 것은 쿠키를 읽는 쪽의 몫이다).

import { expect, test } from "vitest";
import { parseCookieHeader } from "./cookies.ts";

test("쿠키 헤더가 없으면 쿠키도 없다", () => {
  expect(parseCookieHeader(undefined)).toEqual([]);
  expect(parseCookieHeader("")).toEqual([]);
});

test("세미콜론으로 가른 쿠키를 실린 차례대로 이름과 값으로 읽는다", () => {
  expect(parseCookieHeader("a=1; b=2;c=3")).toEqual([
    { name: "a", value: "1" },
    { name: "b", value: "2" },
    { name: "c", value: "3" },
  ]);
});

test("같은 이름이 여럿이면 모두 실린 차례로 남긴다", () => {
  expect(parseCookieHeader("portal_anon=first; portal_anon=second")).toEqual([
    { name: "portal_anon", value: "first" },
    { name: "portal_anon", value: "second" },
  ]);
});

test("값에 등호가 들어 있어도 첫 등호에서 이름과 값을 가르고, 등호가 없는 조각은 버린다", () => {
  expect(parseCookieHeader("a=b=c; broken; =novalue")).toEqual([{ name: "a", value: "b=c" }]);
});
