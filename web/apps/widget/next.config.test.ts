// 위젯의 설정 파일. next dev·build·start 가 단계(phase)를 주어 부르는 그 함수를 사이트 파일 변수마다 새로 불러, iframe 페이지가
// 어디에 서고 어떤 응답 헤더를 다는지 본다. 사이트 파일을 읽는 것은 개발 서버 단계뿐이고, 빌드와 서비스 시작 단계는 사이트
// 파일과 무관하게 `frame-ancestors 'none'` 을 낸다(widget-runtime-values 티켓 02). 서비스 시작이 뜰 때 그 값을 사이트 파일의
// 허용 출처로 바꿔 넣는 것은 `tools/manifest.test.ts` 가 본다. 요청 글자 수 상한과 허용 출처는 번들에 싣지 않고 값 파일로
// 받는다(티켓 01. 값 파일을 쓰는 코드는 `tools/runtime.test.ts` 가 본다). 헤더가 basePath 아래의 실제 경로에 붙는지는 빌드한
// 앱의 응답을 보는 e2e 가 판정한다. 표기와 모양의 판정 하나하나는 `@agent-os/site-file` 의 시험
// (`web/packages/site-file/src/site-file.test.ts`)이 본다.

import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DEFAULT_REQUEST_CHARS, SITE_FILE_ENV } from "@agent-os/site-file";
import type { NextConfig } from "next";
import {
  PHASE_DEVELOPMENT_SERVER,
  PHASE_PRODUCTION_BUILD,
  PHASE_PRODUCTION_SERVER,
} from "next/constants";
import { afterEach, describe, expect, test, vi } from "vitest";
import { expectedSiteFile, SITE_FILE_FIXTURES } from "./testing/site-file.ts";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

/** 사이트 파일을 읽는 것은 개발 서버 단계뿐이다. 다른 단계는 `PHASE_*` 로 따로 부른다. */
async function loadConfig(
  siteFile: string | undefined,
  phase: string = PHASE_DEVELOPMENT_SERVER,
): Promise<NextConfig> {
  vi.stubEnv(SITE_FILE_ENV, siteFile);
  vi.resetModules();
  const module = await import("./next.config.ts");
  return module.default(phase);
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

test("iframe 페이지는 basePath /widget 아래에 선다", async () => {
  expect((await loadConfig(undefined)).basePath).toBe("/widget");
});

describe("빌드와 서비스 시작 단계는 사이트 파일을 읽지 않고 아무도 품지 못하는 값을 낸다", () => {
  // 서비스 시작이 뜰 때 이 값을 사이트 파일의 허용 출처로 바꿔 넣는다(tools/manifest.ts). 빌드가 사이트 파일을 읽어 값을
  // 굳히면 그 자리가 `'none'` 이 아니라서 서비스 시작이 멈춘다.
  const NONE = { "Content-Security-Policy": "frame-ancestors 'none'" };

  for (const [name, phase] of [
    ["빌드", PHASE_PRODUCTION_BUILD],
    ["서비스 시작", PHASE_PRODUCTION_SERVER],
  ] as const) {
    test(`${name} 단계는 허용 출처가 든 사이트 파일을 주어도 'none' 이다`, async () => {
      const config = await loadConfig(join(SITE_FILE_FIXTURES, "sites.toml"), phase);

      expect(await headersOf(config, "/:path*")).toEqual(NONE);
    });

    test(`${name} 단계는 읽지 못하는 사이트 파일을 주어도 멈추지 않는다`, async () => {
      const missing = join(mkdtempSync(join(tmpdir(), "widget-site-file-")), "none.toml");

      for (const value of [missing, "", siteFile('schema_version = "1"\n[[sites]\n')]) {
        const config = await loadConfig(value, phase);

        expect(await headersOf(config, "/:path*")).toEqual(NONE);
      }
    });

    test(`${name} 단계도 basePath 와 나머지 머리 규칙은 개발 서버와 같다`, async () => {
      const config = await loadConfig(undefined, phase);
      const dev = await loadConfig(undefined);

      expect(config.basePath).toBe("/widget");
      for (const source of ["/fonts/:path*", "/element.js", "/runtime.json"]) {
        expect(await headersOf(config, source)).toEqual(await headersOf(dev, source));
      }
    });
  }
});

describe("개발 서버 단계는 뜰 때 사이트 파일을 읽어 응답 머리를 낸다", () => {
  test("사이트 파일을 주지 않으면 어떤 사이트도 iframe 페이지를 품지 못한다", async () => {
    const config = await loadConfig(undefined);

    expect(await headersOf(config, "/:path*")).toEqual({
      "Content-Security-Policy": "frame-ancestors 'none'",
    });
  });

  test("두 언어가 함께 읽는 사이트 파일의 합친 허용 출처가 frame-ancestors 에 든다", async () => {
    const expected = expectedSiteFile();

    const config = await loadConfig(join(SITE_FILE_FIXTURES, "sites.toml"));

    expect(await headersOf(config, "/:path*")).toEqual({
      "Content-Security-Policy": `frame-ancestors ${expected.allowedOrigins.join(" ")}`,
    });
    expect(DEFAULT_REQUEST_CHARS).toBe(expected.defaultChars);
  });

  test("사이트가 있어도 합친 허용 출처가 비면 어떤 사이트도 iframe 페이지를 품지 못한다", async () => {
    const config = await loadConfig(siteFile(site({ origins: "[]" })));

    expect(await headersOf(config, "/:path*")).toEqual({
      "Content-Security-Policy": "frame-ancestors 'none'",
    });
  });

  test("줄 끝을 CR 하나로 적은 사이트 파일도 서버처럼 읽는다", async () => {
    const config = await loadConfig(siteFile(site().replaceAll("\n", "\r")));

    expect(await headersOf(config, "/:path*")).toEqual({
      "Content-Security-Policy": "frame-ancestors https://shop.example",
    });
  });
});

test("사이트 파일의 두 값(허용 출처와 요청 글자 수 상한)을 번들에 싣지 않는다", async () => {
  // 값은 열릴 때 값 파일로 받는다. 설정이 env 로 싣지 않아야 번들의 내용이 사이트 파일과 무관하다(사용자 이야기 26).
  for (const phase of [PHASE_DEVELOPMENT_SERVER, PHASE_PRODUCTION_BUILD, PHASE_PRODUCTION_SERVER]) {
    for (const path of [undefined, join(SITE_FILE_FIXTURES, "sites.toml")]) {
      expect((await loadConfig(path, phase)).env).toBeUndefined();
    }
  }
});

describe("변수가 준 사이트 파일을 읽지 못하면 개발 서버가 설정을 읽다 멈춘다", () => {
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

test("페이지 안 번들 응답도 어느 출처에서나 읽힌다. crossorigin 을 붙인 script 는 CORS 로 받는다", async () => {
  expect(await headersOf(await loadConfig(undefined), "/element.js")).toEqual({
    "Access-Control-Allow-Origin": "*",
  });
});

test("값 파일 응답도 어느 출처에서나 읽힌다. 사이트 페이지 안에서 도는 번들이 받는다", async () => {
  const headers = await headersOf(await loadConfig(undefined), "/runtime.json");

  // 캐시 머리는 달지 않는다. 값은 비밀이 아니고 위젯이 뜰 때마다 사이트 파일을 새로 읽어 쓴다.
  expect(headers).toEqual({ "Access-Control-Allow-Origin": "*" });
});

test("API 를 넘기는 중계를 두지 않는다. 최종 사용자 경로는 nginx 가 파이썬에 바로 넘긴다", async () => {
  expect((await loadConfig(undefined)).rewrites).toBeUndefined();
});
