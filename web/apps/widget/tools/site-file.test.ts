// 위젯 빌드가 사이트 파일에서 읽는 것. 허용 출처의 표기 판정과 사이트 파일의 모양 판정을 글에서 바로 본다. 두 언어가
// 함께 읽는 픽스처는 tests/fixtures/site_file/ 이고(규칙의 이름과 차례는 그 README), 파이썬은 tests/test_main.py 가
// 같은 파일을 읽는다. 변수와 파일을 거쳐 설정에 드는 것은 next.config.test.ts 가 본다.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, test } from "vitest";
import { DEFAULT_REQUEST_CHARS, originRule, siteFileInput } from "./site-file.ts";

const FIXTURES = join(
  import.meta.dirname,
  "..",
  "..",
  "..",
  "..",
  "tests",
  "fixtures",
  "site_file",
);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function casesOf(document: unknown, key: string): readonly Record<string, unknown>[] {
  const list = isRecord(document) ? document[key] : undefined;
  if (!Array.isArray(list)) {
    throw new Error(`origins.json 에 ${key} 배열이 없다`);
  }
  return list.map((item: unknown) => {
    if (!isRecord(item)) {
      throw new Error(`origins.json 의 ${key} 에 객체가 아닌 항목이 있다`);
    }
    return item;
  });
}

function textOf(item: Record<string, unknown>, key: string): string {
  const value = item[key];
  if (typeof value !== "string") {
    throw new Error(`origins.json 의 항목에 글자 ${key} 가 없다`);
  }
  return value;
}

const ORIGINS: unknown = JSON.parse(readFileSync(join(FIXTURES, "origins.json"), "utf-8"));
const PASSING = casesOf(ORIGINS, "pass").map((item) => textOf(item, "origin"));
const BLOCKED = casesOf(ORIGINS, "block").map((item) => ({
  origin: textOf(item, "origin"),
  rule: textOf(item, "rule"),
}));
// 브라우저가 다른 값으로 바꾸거나 거절하는 표기의 규칙. 나머지 셋(wildcard, null, scheme)은 정한 금지라 브라우저가
// 그대로 싣는 값도 막는다.
const NOTATION_RULES: readonly string[] = [
  "shape",
  "case",
  "path",
  "userinfo",
  "port",
  "default-port",
  "idn",
  "ipv6",
  "host",
  "ipv4",
];

/** Node 의 URL 파서가 그 값에서 읽은 출처. 던지면 null. */
function parsedOrigin(value: string): string | null {
  try {
    return new URL(value).origin;
  } catch {
    return null;
  }
}

/** 사이트 하나의 TOML. 공개 키의 PEM 은 서버만 읽는 값이라 빌드는 뜻을 보지 않는다. */
function site(origins: string, extra = ""): string {
  return [
    "",
    "[[sites]]",
    'issuer = "https://shop.example"',
    'audience = "agent-os"',
    `allowed_origins = ${origins}`,
    'agents = ["echo"]',
    extra,
    "[[sites.public_keys]]",
    'pem = "서버만 읽는다"',
    "",
  ].join("\n");
}

function problemsOf(text: string): readonly string[] {
  const input = siteFileInput(text);
  if (!("problems" in input)) {
    throw new Error("받아들일 수 없는 사이트 파일을 받아들였다");
  }
  return input.problems;
}

describe("허용 출처의 표기", () => {
  test("픽스처에 지나는 사례와 막히는 사례가 있다", () => {
    expect(PASSING.length).toBeGreaterThan(0);
    expect(BLOCKED.length).toBeGreaterThan(0);
  });

  test.each(PASSING)("%s 는 브라우저가 싣는 표기라 지난다", (origin) => {
    expect(originRule(origin)).toBeNull();
  });

  test.each(BLOCKED)("$origin 은 규칙 $rule 에 막힌다", ({ origin, rule }) => {
    expect(originRule(origin)).toBe(rule);
  });

  test.each(PASSING)("%s 는 Node 의 URL 파서가 바꾸지 않는다", (origin) => {
    expect(parsedOrigin(origin)).toBe(origin);
  });

  test.each(BLOCKED.filter(({ rule }) => NOTATION_RULES.includes(rule)))(
    "$origin 은 Node 의 URL 파서가 다른 값으로 바꾸거나 거절한다",
    ({ origin }) => {
      expect(parsedOrigin(origin)).not.toBe(origin);
    },
  );
});

describe("사이트 파일의 모양", () => {
  test("사이트가 없는 파일은 빈 허용 출처와 서버의 기본 상한이다", () => {
    expect(siteFileInput('schema_version = "1"\n')).toEqual({
      allowedOrigins: [],
      requestChars: DEFAULT_REQUEST_CHARS,
    });
  });

  test("모든 사이트가 기본값보다 큰 상한을 적으면 그 가운데 가장 작은 값이다", () => {
    const text = [
      'schema_version = "1"',
      site('["https://a.example"]', "[sites.limits]\nrequest_chars = 50000"),
      site('["https://b.example"]', "[sites.limits]\nrequest_chars = 30000"),
    ].join("\n");

    expect(siteFileInput(text)).toEqual({
      allowedOrigins: ["https://a.example", "https://b.example"],
      requestChars: 30_000,
    });
  });

  test("표기 밖의 출처는 그 자리와 어긴 규칙을 말하고 값을 싣지 않는다", () => {
    const text = `schema_version = "1"\n${site('["https://ok.example", "https://user:pw@shop.example"]')}`;

    const problems = problemsOf(text);

    expect(problems).toHaveLength(1);
    expect(problems[0]).toContain(
      "sites[0].allowed_origins[1]: 브라우저가 Origin 헤더에 싣는 표기가 아니다(규칙 userinfo)",
    );
    expect(problems[0]).not.toContain("pw@");
  });

  test.each([
    ["issuer", 'issuer = "https://shop.example"'],
    ["audience", 'audience = "agent-os"'],
    ["allowed_origins", 'allowed_origins = ["https://a.example"]'],
    ["agents", 'agents = ["echo"]'],
    ["public_keys", '[[sites.public_keys]]\npem = "서버만 읽는다"'],
  ])("사이트 항목의 필수 키 %s 가 빠지면 그 자리를 말하고 받아들이지 않는다", (key, line) => {
    const text = `schema_version = "1"\n${site('["https://a.example"]').replace(line, "")}`;

    expect(problemsOf(text)).toEqual([`sites[0].${key}: 빠졌다`]);
  });

  test("판 schema_version 이 빠지면 그 자리를 말하고 받아들이지 않는다", () => {
    expect(problemsOf(site('["https://a.example"]'))).toEqual(["schema_version: 빠졌다"]);
  });

  test("파일 머리의 BOM 은 서버의 TOML 파서처럼 거절한다", () => {
    expect(problemsOf(`\uFEFFschema_version = "1"\n`)).toEqual([
      expect.stringContaining("TOML 이 아니다"),
    ]);
  });

  test.each([
    ["사이트가 표의 배열이 아니다", 'schema_version = "1"\nsites = "shop"\n', "sites:"],
    ["사이트가 표가 아니다", 'schema_version = "1"\nsites = ["shop"]\n', "sites[0]:"],
    [
      "발급자를 수로 적었다",
      `schema_version = "1"\n${site('["https://a.example"]').replace('"https://shop.example"', "3")}`,
      "sites[0].issuer:",
    ],
    [
      "공개 키에 모르는 키가 있다",
      `schema_version = "1"\n${site('["https://a.example"]')}kind = "rsa"\n`,
      "sites[0].public_keys[0].kind:",
    ],
    [
      "공개 키의 pem 이 빠졌다",
      `schema_version = "1"\n${site('["https://a.example"]').replace('pem = "서버만 읽는다"', 'kid = "k1"')}`,
      "sites[0].public_keys[0].pem:",
    ],
    [
      "열 에이전트에 글자가 아닌 것이 있다",
      `schema_version = "1"\n${site('["https://a.example"]').replace('["echo"]', '["echo", 1]')}`,
      "sites[0].agents[1]:",
    ],
    [
      "상한 표가 표가 아니다",
      `schema_version = "1"\n${site('["https://a.example"]', "limits = 3")}`,
      "sites[0].limits:",
    ],
    [
      "다른 상한을 실수로 적었다",
      `schema_version = "1"\n${site('["https://a.example"]', "[sites.limits]\nhourly_runs_per_site = 2.0")}`,
      "sites[0].limits.hourly_runs_per_site:",
    ],
  ])("%s. 그 자리를 말하고 받아들이지 않는다", (_, text, place) => {
    expect(problemsOf(text)).toEqual([expect.stringContaining(place)]);
  });
});
