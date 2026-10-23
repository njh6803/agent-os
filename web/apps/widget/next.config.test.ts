// 위젯의 설정 파일. next dev·build·start 가 읽는 그 파일을 새로 읽어, iframe 페이지가 어디에 서고 어떤 응답 헤더를
// 다는지 본다. 헤더가 basePath 아래의 실제 경로에 붙는지는 빌드한 앱의 응답을 보는 e2e 가 판정한다. `frame-ancestors`
// 는 06 이, 글꼴 응답의 `Access-Control-Allow-Origin` 은 10 이 본다.

import { expect, test } from "vitest";
import config from "./next.config.ts";

async function headersOf(source: string): Promise<Record<string, string>> {
  if (config.headers === undefined) {
    throw new Error("설정에 headers 가 없다");
  }
  const rules = await config.headers();
  const found = rules.filter((rule) => rule.source === source);
  if (found.length === 0) {
    throw new Error(`${source} 에 헤더 규칙이 없다`);
  }
  return Object.fromEntries(found.flatMap((rule) => rule.headers.map((h) => [h.key, h.value])));
}

test("iframe 페이지는 basePath /widget 아래에 선다", () => {
  expect(config.basePath).toBe("/widget");
});

test("사이트 파일을 읽기 전에는 어떤 사이트도 iframe 페이지를 품지 못한다", async () => {
  expect(await headersOf("/:path*")).toEqual({
    "Content-Security-Policy": "frame-ancestors 'none'",
  });
});

test("글꼴 응답은 자격 증명 없이 어느 출처에서나 읽힌다", async () => {
  expect(await headersOf("/fonts/:path*")).toEqual({ "Access-Control-Allow-Origin": "*" });
});

test("API 를 넘기는 중계를 두지 않는다. 최종 사용자 경로는 nginx 가 파이썬에 바로 넘긴다", () => {
  expect(config.rewrites).toBeUndefined();
});
