import { afterEach, expect, test } from "vitest";
import { publish, received } from "./env.ts";

const NAME = "AGENT_OS_E2E_STACK_TEST_VALUE";

afterEach(() => {
  Reflect.deleteProperty(process.env, NAME);
});

test("준비가 적은 값을 시험이 같은 이름으로 읽는다", () => {
  publish(NAME, "/tmp/traces");

  expect(received(NAME)).toBe("/tmp/traces");
});

test("준비가 적지 않은 이름을 읽으면 이름을 알리며 던진다", () => {
  expect(() => received(NAME)).toThrow(NAME);
});
