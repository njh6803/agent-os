// 두 언어가 함께 읽는 사이트 파일 픽스처(`tests/fixtures/site_file/`, web-widget 명세 Testing Decisions 5). 위젯의 두 빌드
// 설정 시험(next.config.test.ts, tools/element.test.ts)이 같은 기대값을 읽는다.

import { readFileSync } from "node:fs";
import { join } from "node:path";

export const SITE_FILE_FIXTURES = join(
  import.meta.dirname,
  "..",
  "..",
  "..",
  "..",
  "tests",
  "fixtures",
  "site_file",
);

export interface ExpectedSiteFile {
  readonly allowedOrigins: readonly string[];
  readonly requestChars: number;
  readonly defaultChars: number;
}

/** 픽스처 `sites.toml` 에서 끌어낼 값(`sites.json`). */
export function expectedSiteFile(): ExpectedSiteFile {
  const parsed: unknown = JSON.parse(readFileSync(join(SITE_FILE_FIXTURES, "sites.json"), "utf-8"));
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
