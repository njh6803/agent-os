// 시작 때 짓는 정적 파일. 벗긴 페이지 스크립트의 글자나 토큰 CSS 의 바이트 수는 단언하지 않고(pilot-portal 명세 "좋은 시험"),
// 스크립트가 JavaScript 로 파싱되는 것과 CSS 가 토큰을 담는 것, 글꼴의 길과 `ETag` 만 본다.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { basename } from "node:path";
import { Script } from "node:vm";
import { fontFiles } from "@agent-os/ui/fonts";
import { expect, test } from "vitest";
import {
  fontFileTable,
  fontsCss,
  pageScript,
  staticText,
  stripPageScript,
  themeCss,
} from "./assets.ts";

test("타입 주석을 벗긴 스크립트가 JavaScript 로 파싱된다", () => {
  const stripped = stripPageScript(
    "(function (): void {\n  const 수: number = 1;\n  void 수;\n})();\n",
  );

  expect(() => new Script(stripped)).not.toThrow();
  expect(stripped).not.toContain(": number");
});

test("타입만 지울 수 없는 문법은 벗기다 거부한다", () => {
  let caught: unknown;
  try {
    stripPageScript("enum 색 {\n  빨강,\n}\n");
  } catch (error: unknown) {
    caught = error;
  }

  expect(caught).toMatchObject({ cause: { code: "ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX" } });
});

test("앱의 페이지 스크립트를 벗긴 결과는 JavaScript 로 파싱되는 고전 스크립트다", () => {
  const script = pageScript();

  expect(() => new Script(script)).not.toThrow();
  expect(script).not.toMatch(/^\s*(import|export)\s/mu);
});

test("글꼴 CSS 의 url 이 글꼴 경로 아래 파일 이름을 가리킨다", () => {
  const css = fontsCss([
    {
      family: "Noto Sans KR",
      weight: "400",
      style: "normal",
      unicodeRange: "U+AC00-D7A3",
      file: "noto-sans-kr-korean-400-normal.woff2",
    },
  ]);

  expect(css).toContain("font-family: 'Noto Sans KR'");
  expect(css).toContain(
    'url("/portal/fonts/noto-sans-kr-korean-400-normal.woff2") format("woff2")',
  );
  expect(css).toContain("unicode-range: U+AC00-D7A3");
});

test("글꼴 파일 표는 목록의 woff2 마다 내용 해시의 ETag 와 크기를 든다", () => {
  const table = fontFileTable();
  const [first] = fontFiles();
  if (first === undefined) {
    throw new Error("글꼴 목록이 비었다");
  }

  expect(table.size).toBe(fontFiles().length);
  const entry = table.get(basename(first));
  expect(entry?.path).toBe(first);
  const hash = createHash("sha256").update(readFileSync(first)).digest("hex");
  expect(entry?.etag).toBe(`"${hash.slice(0, 32)}"`);
  expect(entry?.size).toBe(readFileSync(first).length);
  expect(table.has("not-in-list.woff2")).toBe(false);
});

test("정적 글의 ETag 는 본문이 같으면 같고 다르면 다르다", () => {
  const a = staticText("a{}", "text/css; charset=utf-8");

  expect(staticText("a{}", "text/css; charset=utf-8").etag).toBe(a.etag);
  expect(staticText("b{}", "text/css; charset=utf-8").etag).not.toBe(a.etag);
  expect(a.etag).toMatch(/^"[0-9a-f]{32}"$/u);
});

test("토큰 CSS 를 Tailwind CLI 로 지어 메모리에 읽는다", async () => {
  const css = await themeCss();

  expect(css).toContain("--bg-raised");
  expect(css).toContain("[data-theme");
  expect(css).not.toContain("@import");
});
