// 번들이 빌드 값을 읽는 자리(lib/build.ts). Next 는 `process.env.이름` 을 글자 그대로 찾아 바꿔 넣으므로, 그 글자가
// 빌드가 env 에 싣는 이름(tools/site-file.ts 의 상수)과 같아야 한다. 이름이 어긋나면 번들의 값이 늘 없음이 되고 화면
// 시험은 환경 변수로 값을 두어 그것을 보지 못한다.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, expect, test, vi } from "vitest";
import { WIDGET_ORIGINS_ENV, WIDGET_REQUEST_CHARS_ENV } from "../tools/site-file.ts";
import { allowedOrigins, requestCharLimit } from "./build";

const SOURCE = readFileSync(join(import.meta.dirname, "build.ts"), "utf8");

afterEach(() => {
  vi.unstubAllEnvs();
});

test("빌드 값은 빌드가 싣는 이름 그대로 process.env 의 점 표기로 읽는다", () => {
  expect(SOURCE).toContain(`process.env.${WIDGET_ORIGINS_ENV}`);
  expect(SOURCE).toContain(`process.env.${WIDGET_REQUEST_CHARS_ENV}`);
});

test("합친 허용 출처는 공백 하나로 이은 글을 나눈 목록이고 빈 글이면 빈 목록이다", () => {
  vi.stubEnv(WIDGET_ORIGINS_ENV, "https://a.example https://b.example:8443");
  expect(allowedOrigins()).toEqual(["https://a.example", "https://b.example:8443"]);

  vi.stubEnv(WIDGET_ORIGINS_ENV, "");
  expect(allowedOrigins()).toEqual([]);
});

test("요청 글자 수 상한은 십진수 글을 읽은 수다", () => {
  vi.stubEnv(WIDGET_REQUEST_CHARS_ENV, "1500");
  expect(requestCharLimit()).toBe(1500);
});
