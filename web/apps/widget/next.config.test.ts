// 위젯의 설정 파일. next dev·build·start 가 읽는 그 파일을 사이트 파일 변수마다 새로 읽어, iframe 페이지가 어디에 서고
// 어떤 응답 헤더를 다는지, 사이트 파일에서 무엇을 빌드에 싣는지 본다(web-widget 티켓 04). 헤더가 basePath 아래의 실제
// 경로에 붙는지는 빌드한 앱의 응답을 보는 e2e 가 판정한다. `frame-ancestors` 는 06 이, 글꼴 응답의
// `Access-Control-Allow-Origin` 은 10 이 본다. 표기와 모양의 판정 하나하나는 tools/site-file.test.ts 가 본다.

import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { NextConfig } from "next";
import { afterEach, describe, expect, test, vi } from "vitest";
import {
  DEFAULT_REQUEST_CHARS,
  SITE_FILE_ENV,
  WIDGET_ORIGINS_ENV,
  WIDGET_REQUEST_CHARS_ENV,
} from "./tools/site-file.ts";

const FIXTURES = join(import.meta.dirname, "..", "..", "..", "tests", "fixtures", "site_file");

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

async function loadConfig(siteFile: string | undefined): Promise<NextConfig> {
  vi.stubEnv(SITE_FILE_ENV, siteFile);
  vi.resetModules();
  const module = await import("./next.config.ts");
  return module.default;
}

async function headersOf(config: NextConfig, source: string): Promise<Record<string, string>> {
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

/** 임시 폴더에 쓴 사이트 파일의 경로. 글은 UTF-8 로 쓴다. */
function siteFile(content: string | Uint8Array): string {
  const path = join(mkdtempSync(join(tmpdir(), "widget-site-file-")), "sites.toml");
  writeFileSync(path, content);
  return path;
}

/** 사이트 하나의 TOML. 공개 키의 PEM 은 서버만 읽는 값이라 빌드는 뜻을 보지 않는다. */
function site({
  origins = '["https://shop.example"]',
  agents = 'agents = ["echo"]',
  extra = "",
}: { origins?: string; agents?: string; extra?: string } = {}): string {
  return [
    'schema_version = "1"',
    "[[sites]]",
    'issuer = "https://shop.example"',
    'audience = "agent-os"',
    origins === "" ? "" : `allowed_origins = ${origins}`,
    agents,
    extra,
    "[[sites.public_keys]]",
    'pem = "서버만 읽는다"',
    "",
  ].join("\n");
}

interface Expected {
  readonly allowedOrigins: readonly string[];
  readonly requestChars: number;
  readonly defaultChars: number;
}

/** 두 언어가 함께 읽는 기대값(sites.json). */
function expectedValues(): Expected {
  const parsed: unknown = JSON.parse(readFileSync(join(FIXTURES, "sites.json"), "utf-8"));
  if (typeof parsed !== "object" || parsed === null) {
    throw new Error("sites.json 이 객체가 아니다");
  }
  const origins: unknown = "allowed_origins" in parsed ? parsed.allowed_origins : undefined;
  const chars = "request_chars" in parsed ? parsed.request_chars : undefined;
  const defaultChars = "default_request_chars" in parsed ? parsed.default_request_chars : undefined;
  const allowedOrigins = Array.isArray(origins)
    ? origins.filter((origin: unknown): origin is string => typeof origin === "string")
    : [];
  if (
    !Array.isArray(origins) ||
    allowedOrigins.length !== origins.length ||
    typeof chars !== "number" ||
    typeof defaultChars !== "number"
  ) {
    throw new Error("sites.json 의 모양이 다르다");
  }
  return { allowedOrigins, requestChars: chars, defaultChars };
}

test("iframe 페이지는 basePath /widget 아래에 선다", async () => {
  expect((await loadConfig(undefined)).basePath).toBe("/widget");
});

test("사이트 파일을 주지 않으면 어떤 사이트도 iframe 페이지를 품지 못하고 상한은 서버의 기본값이다", async () => {
  const config = await loadConfig(undefined);

  expect(await headersOf(config, "/:path*")).toEqual({
    "Content-Security-Policy": "frame-ancestors 'none'",
  });
  expect(config.env).toEqual({
    [WIDGET_ORIGINS_ENV]: "",
    [WIDGET_REQUEST_CHARS_ENV]: "20000",
  });
});

test("두 언어가 함께 읽는 사이트 파일의 합친 허용 출처가 frame-ancestors 에, 가장 작은 상한이 빌드에 든다", async () => {
  const expected = expectedValues();

  const config = await loadConfig(join(FIXTURES, "sites.toml"));

  expect(await headersOf(config, "/:path*")).toEqual({
    "Content-Security-Policy": `frame-ancestors ${expected.allowedOrigins.join(" ")}`,
  });
  expect(config.env).toEqual({
    [WIDGET_ORIGINS_ENV]: expected.allowedOrigins.join(" "),
    [WIDGET_REQUEST_CHARS_ENV]: String(expected.requestChars),
  });
  expect(DEFAULT_REQUEST_CHARS).toBe(expected.defaultChars);
});

test("사이트가 있어도 합친 허용 출처가 비면 어떤 사이트도 iframe 페이지를 품지 못한다", async () => {
  const config = await loadConfig(siteFile(site({ origins: "[]" })));

  expect(await headersOf(config, "/:path*")).toEqual({
    "Content-Security-Policy": "frame-ancestors 'none'",
  });
  expect(config.env).toEqual({ [WIDGET_ORIGINS_ENV]: "", [WIDGET_REQUEST_CHARS_ENV]: "20000" });
});

describe("변수가 준 사이트 파일을 읽지 못하면 빌드가 실패한다", () => {
  test("변수가 비었다", async () => {
    await expect(loadConfig("")).rejects.toThrow(`${SITE_FILE_ENV} 가 비었다`);
  });

  test("파일이 없다", async () => {
    const missing = join(mkdtempSync(join(tmpdir(), "widget-site-file-")), "none.toml");

    await expect(loadConfig(missing)).rejects.toThrow(`사이트 파일 ${missing} 을 받아들일 수 없다`);
    await expect(loadConfig(missing)).rejects.toThrow("파일이 없다");
  });

  test.each<[string, string | Uint8Array, string]>([
    ["TOML 이 깨졌다", 'schema_version = "1"\n[[sites]\n', "TOML 이 아니다"],
    ["파일 머리에 BOM 이 있다", `\uFEFF${site()}`, "TOML 이 아니다: 파일 머리에 BOM 이 있다"],
    ["UTF-8 이 아니다", Uint8Array.of(0x73, 0x3d, 0xff), "읽을 수 없다(UTF-8 이 아니다)"],
    [
      "판이 1 이 아니다",
      site().replace('schema_version = "1"', 'schema_version = "2"'),
      "schema_version:",
    ],
    ["모르는 키가 있다", site({ extra: "quota = 3" }), "sites[0].quota: 모르는 키다"],
    ["허용 출처가 빠졌다", site({ origins: "" }), "sites[0].allowed_origins: 빠졌다"],
    ["열 에이전트가 빠졌다", site({ agents: "" }), "sites[0].agents: 빠졌다"],
    [
      "수를 글자로 적었다",
      site({ extra: '[sites.limits]\nrequest_chars = "4000"' }),
      "sites[0].limits.request_chars: 정수여야 한다",
    ],
    [
      "허용 출처가 브라우저가 싣는 표기가 아니다",
      site({ origins: '["https://shop.example", "https://Shop.example"]' }),
      "sites[0].allowed_origins[1]: 브라우저가 Origin 헤더에 싣는 표기가 아니다(규칙 case)",
    ],
    [
      "요청 글자 수 상한이 0 이다",
      site({ extra: "[sites.limits]\nrequest_chars = 0" }),
      "sites[0].limits.request_chars: 1 이상이어야 한다",
    ],
  ])("%s", async (_, content, problem) => {
    const path = siteFile(content);

    await expect(loadConfig(path)).rejects.toThrow(`사이트 파일 ${path} 을 받아들일 수 없다`);
    await expect(loadConfig(path)).rejects.toThrow(problem);
  });
});

test("글꼴 응답은 자격 증명 없이 어느 출처에서나 읽힌다", async () => {
  expect(await headersOf(await loadConfig(undefined), "/fonts/:path*")).toEqual({
    "Access-Control-Allow-Origin": "*",
  });
});

test("API 를 넘기는 중계를 두지 않는다. 최종 사용자 경로는 nginx 가 파이썬에 바로 넘긴다", async () => {
  expect((await loadConfig(undefined)).rewrites).toBeUndefined();
});
