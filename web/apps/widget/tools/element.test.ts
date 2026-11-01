// 페이지 안 번들의 빌드 설정(web-widget 티켓 10). 사이트 파일에서 무엇을 번들에 싣고 무엇을 싣지 않는지, 읽지 못하면
// 빌드가 멈추는지, 산출물이 청크로 나뉘지 않는 classic 스크립트 하나인지를 본다. 번들이 사이트 페이지에서 실려 도는지는
// 위젯 e2e 가 본다. 표기와 모양의 판정 하나하나는 tools/site-file.test.ts 가 본다.

import { mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Script } from "node:vm";
import { describe, expect, test } from "vitest";
import { expectedSiteFile, SITE_FILE_FIXTURES } from "../testing/site-file.ts";
import { buildElement, ELEMENT_FILE, elementBuildConfig } from "./element.ts";
import { fontFaces } from "./fonts.ts";
import { SITE_FILE_ENV, WIDGET_ORIGINS_ENV, WIDGET_REQUEST_CHARS_ENV } from "./site-file.ts";

const CHARS = `process.env.${WIDGET_REQUEST_CHARS_ENV}`;
const FIXTURE = join(SITE_FILE_FIXTURES, "sites.toml");

test("번들은 청크로 나뉘지 않는 classic 스크립트 하나로 Next 의 public/element.js 에 나간다", () => {
  const config = elementBuildConfig({}, "out");

  expect(ELEMENT_FILE).toBe("element.js");
  expect(config.build?.outDir).toBe("out");
  expect(config.build?.lib).toMatchObject({ formats: ["iife"] });
  // 같은 자리의 글꼴 파일을 지우지 않는다. Vite 의 public 복사도 끈다.
  expect(config.build?.emptyOutDir).toBe(false);
  expect(config.build?.copyPublicDir).toBe(false);
  expect(config.configFile).toBe(false);
  expect(elementBuildConfig({}).build?.outDir).toBe(join(import.meta.dirname, "..", "public"));
});

test("사이트 파일을 주지 않으면 서버의 기본 상한을 싣는다", () => {
  expect(elementBuildConfig({}).define?.[CHARS]).toBe(JSON.stringify("20000"));
});

test("두 언어가 함께 읽는 사이트 파일의 가장 작은 상한을 싣고, 허용 출처는 싣지 않는다", () => {
  const expected = expectedSiteFile();

  const config = elementBuildConfig({ [SITE_FILE_ENV]: FIXTURE });

  expect(config.define?.[CHARS]).toBe(JSON.stringify(String(expected.requestChars)));
  expect(
    Object.keys(config.define ?? {}).filter((key) => key.includes(WIDGET_ORIGINS_ENV)),
  ).toEqual([]);
  const written = JSON.stringify(config.define);
  expect(expected.allowedOrigins.filter((origin) => written.includes(origin))).toEqual([]);
});

describe("변수가 준 사이트 파일을 읽지 못하면 빌드가 실패한다", () => {
  test("파일이 없다", () => {
    const missing = join(mkdtempSync(join(tmpdir(), "widget-element-")), "none.toml");
    expect(() => elementBuildConfig({ [SITE_FILE_ENV]: missing })).toThrow(
      `사이트 파일 ${missing} 을 받아들일 수 없다`,
    );
  });

  test("변수가 비었다", () => {
    expect(() => elementBuildConfig({ [SITE_FILE_ENV]: "" })).toThrow(`${SITE_FILE_ENV} 가 비었다`);
  });
});

test("빌드한 번들은 모듈이 아닌 스크립트 하나이고, 빌드 때의 환경 변수 자리와 허용 출처와 글꼴 파일을 싣지 않는다", async () => {
  const out = mkdtempSync(join(tmpdir(), "widget-element-"));
  try {
    await buildElement({ [SITE_FILE_ENV]: FIXTURE }, out);

    expect(readdirSync(out)).toEqual([ELEMENT_FILE]);
    const bundle = readFileSync(join(out, ELEMENT_FILE), "utf-8");
    // import·export 가 남은 모듈이면 classic 스크립트로 읽지 못한다.
    expect(() => new Script(bundle)).not.toThrow();
    // 브라우저에는 process 가 없다. React 와 openapi-fetch 가 `typeof process` 로 먼저 보는 자리는 남는다.
    expect(bundle).not.toMatch(/\bprocess\.env\b/);
    expect(bundle).toContain("agent-os-widget");
    const { allowedOrigins } = expectedSiteFile();
    expect(allowedOrigins.filter((origin) => bundle.includes(origin))).toEqual([]);
    // 위젯의 CSS 가 글꼴 CSS 를 들이면 글꼴 파일이 모두 data URL 로 박힌다(styles/widget.css 의 머리 주석).
    expect(bundle).not.toContain("data:font/");
    // 한글 글꼴의 세 굵기는 같은 글자 범위를 쓴다. 범위를 굵기마다 실으면 목록이 gzip 으로 약 46KB 늘었다
    // (.scratch/web-widget/probes/font_list_size.mjs).
    const korean = fontFaces().filter((face) => face.family === "Noto Sans KR");
    const range = korean[0]?.unicodeRange ?? "";
    expect(korean.filter((face) => face.unicodeRange === range).length).toBeGreaterThan(1);
    expect(bundle.split(range).length - 1).toBe(1);
  } finally {
    rmSync(out, { recursive: true, force: true, maxRetries: 5 });
  }
});

test("빌드는 비어 있던 NODE_ENV 를 비운 채로 둔다", async () => {
  // 시작 래퍼는 빌드한 프로세스에서 이어 `next dev` 를 부른다. NODE_ENV 가 production 으로 남으면 next 가 경고를 내고
  // 그 값으로 개발 서버를 띄운다. vitest 가 NODE_ENV 를 채워 두므로 지운 뒤 빌드한다.
  const out = mkdtempSync(join(tmpdir(), "widget-element-"));
  // Next 의 타입은 NODE_ENV 를 늘 있는 값으로 적는다. 비운 자리를 보려고 넓은 타입으로 받는다.
  const processEnv: Record<string, string | undefined> = process.env;
  const before = processEnv["NODE_ENV"];
  delete processEnv["NODE_ENV"];
  try {
    await buildElement({}, out);

    expect(processEnv["NODE_ENV"]).toBeUndefined();
  } finally {
    if (before !== undefined) {
      processEnv["NODE_ENV"] = before;
    }
    rmSync(out, { recursive: true, force: true, maxRetries: 5 });
  }
});
