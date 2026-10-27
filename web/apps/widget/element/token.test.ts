// 페이지 안 방식의 토큰 손잡이. 사이트가 요소의 `tokenProvider` 에 준 값을 요청마다 부르고, 받지 못한 갈래(함수가
// 없음, 던짐, 거부, 문자열이 아닌 값, 10초 안에 답 없음)를 모두 null 로 낸다(web-widget 명세 "토큰을 받지 못한 경우").

import { afterEach, describe, expect, test, vi } from "vitest";
import { TOKEN_TIMEOUT_MS } from "../lib/token";
import { providerToken } from "./token";

afterEach(() => {
  vi.useRealTimers();
});

test("함수가 문자열로 답하면 그 토큰을 받는다", async () => {
  await expect(providerToken(() => Promise.resolve("signed.token.value"))).resolves.toBe(
    "signed.token.value",
  );
});

test("함수를 요청마다 새로 부른다", async () => {
  let calls = 0;
  const provider = () => Promise.resolve(`token-${String(++calls)}`);
  await expect(providerToken(provider)).resolves.toBe("token-1");
  await expect(providerToken(provider)).resolves.toBe("token-2");
});

describe("받지 못한 것은 null 이다", () => {
  for (const [name, provider] of [
    ["함수가 없다", undefined],
    ["함수가 아닌 값이다", "signed.token.value"],
    ["거부한다", () => Promise.reject(new Error("로그인이 풀렸다"))],
    [
      "던진다",
      () => {
        throw new Error("사이트의 버그");
      },
    ],
    ["숫자로 답한다", () => Promise.resolve(42)],
    ["null 로 답한다", () => Promise.resolve(null)],
    ["객체로 답한다", () => Promise.resolve({ token: "signed.token.value" })],
  ] as const) {
    test(name, async () => {
      await expect(providerToken(provider)).resolves.toBeNull();
    });
  }
});

test("10초 안에 답하지 않으면 받지 못한 것이고, 늦게 온 답은 버린다", async () => {
  vi.useFakeTimers();
  let answer: (token: string) => void = () => undefined;
  const result = providerToken(
    () =>
      new Promise<string>((resolve) => {
        answer = resolve;
      }),
  );

  await vi.advanceTimersByTimeAsync(TOKEN_TIMEOUT_MS - 1);
  let settled = false;
  void result.then(() => {
    settled = true;
  });
  await Promise.resolve();
  expect(settled).toBe(false);

  await vi.advanceTimersByTimeAsync(1);
  answer("late.token.value");
  await expect(result).resolves.toBeNull();
});

test("답을 받으면 기다리던 시계를 걷는다", async () => {
  vi.useFakeTimers();
  await providerToken(() => Promise.resolve("signed.token.value"));
  expect(vi.getTimerCount()).toBe(0);
});
