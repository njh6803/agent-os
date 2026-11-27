// 값 파일을 쓰는 코드(widget-runtime-values 티켓 01). 사이트 파일에서 두 값이 어떻게 나오는지, 쓴 파일이 두 키만 든 객체와 글자
// 그대로 같은지, 상한이 무한대가 될 때 쓴 값, 읽지 못할 때 아무것도 쓰지 않는 것을 본다. 두 언어가 함께 읽는 사이트 파일의
// 표기와 모양은 `@agent-os/site-file` 의 시험이 본다.

import { mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { SITE_FILE_ENV } from "@agent-os/site-file";
import { afterEach, beforeEach, describe, expect, test } from "vitest";
import { expectedSiteFile, SITE_FILE_FIXTURES } from "../testing/site-file.ts";
import { canSymlink } from "../testing/symlink.ts";
import { describeValues, RUNTIME_FILE, runtimeValues, writeRuntimeValues } from "./runtime.ts";

const FIXTURE = join(SITE_FILE_FIXTURES, "sites.toml");

let app: string;

beforeEach(() => {
  app = mkdtempSync(join(tmpdir(), "widget-runtime-"));
});

afterEach(() => {
  rmSync(app, { recursive: true, force: true, maxRetries: 5 });
});

/** 앱 폴더에 쓴 값 파일의 글자 그대로. */
function written(): string {
  return readFileSync(join(app, "public", RUNTIME_FILE), "utf-8");
}

/** 쓴 값 파일을 읽은 값. */
function parsed(): unknown {
  return JSON.parse(written());
}

/**
 * 사이트 하나만 든 사이트 파일을 쓰고 그 경로를 돌려준다. 요청 글자 수 상한(`request_chars`)은 사이트의 `limits` 표에 놓이고,
 * 적지 않으면 그 표를 쓰지 않는다. 숫자는 글자 그대로 받아 `Number` 로 담기지 않는 큰 값도 적을 수 있다.
 */
function siteFileWith(requestChars: string | undefined, origins: readonly string[] = []): string {
  const path = join(app, "sites.toml");
  const quoted = origins.map((origin) => JSON.stringify(origin)).join(", ");
  writeFileSync(
    path,
    [
      'schema_version = "1"',
      "[[sites]]",
      'issuer = "https://issuer.example"',
      'audience = "agent-os"',
      'agents = ["order-helper"]',
      `allowed_origins = [${quoted}]`,
      "[[sites.public_keys]]",
      'pem = "-----BEGIN PUBLIC KEY-----\\nAAAA\\n-----END PUBLIC KEY-----"',
      ...(requestChars === undefined ? [] : ["[sites.limits]", `request_chars = ${requestChars}`]),
    ].join("\n"),
    "utf-8",
  );
  return path;
}

describe("값 파일의 내용", () => {
  test("사이트 파일의 환경 변수가 없으면 빈 허용 출처와 서버의 기본 상한 20000 이다", () => {
    expect(runtimeValues({})).toEqual({ allowedOrigins: [], requestChars: 20_000 });
  });

  test("여러 사이트의 허용 출처는 합친 목록이고 상한은 가장 작은 값이다", () => {
    const expected = expectedSiteFile();

    expect(runtimeValues({ [SITE_FILE_ENV]: FIXTURE })).toEqual({
      allowedOrigins: expected.allowedOrigins,
      requestChars: expected.requestChars,
    });
  });

  test("허용 출처를 적지 않은 사이트 파일은 빈 목록이다", () => {
    const path = siteFileWith(undefined);

    expect(runtimeValues({ [SITE_FILE_ENV]: path })).toEqual({
      allowedOrigins: [],
      requestChars: 20_000,
    });
  });

  test("읽지 못하는 사이트 파일은 진단을 든 오류를 던진다", () => {
    const missing = join(app, "none.toml");

    expect(() => runtimeValues({ [SITE_FILE_ENV]: missing })).toThrow(
      `사이트 파일 ${missing} 을 받아들일 수 없다`,
    );
    expect(() => runtimeValues({ [SITE_FILE_ENV]: "" })).toThrow(`${SITE_FILE_ENV} 가 비었다`);
  });

  test("상한이 Number 로 바뀔 때 무한대가 되면 가장 큰 유한한 수로 쓴다", () => {
    const path = siteFileWith(`1${"0".repeat(400)}`);

    const values = runtimeValues({ [SITE_FILE_ENV]: path });

    expect(values.requestChars).toBe(Number.MAX_VALUE);
  });
});

describe("값 파일 쓰기", () => {
  test("쓴 파일은 허용 출처와 상한 두 키만 든 객체와 글자 그대로 같다", () => {
    const expected = expectedSiteFile();

    writeRuntimeValues({ [SITE_FILE_ENV]: FIXTURE }, app, () => {});

    expect(written()).toBe(
      JSON.stringify({
        allowedOrigins: expected.allowedOrigins,
        requestChars: expected.requestChars,
      }),
    );
    expect(parsed()).toEqual({
      allowedOrigins: expected.allowedOrigins,
      requestChars: expected.requestChars,
    });
  });

  test("사이트 파일의 다른 값(공개 키, 발급자, 열 에이전트)은 싣지 않는다", () => {
    writeRuntimeValues({ [SITE_FILE_ENV]: FIXTURE }, app, () => {});

    expect(written()).not.toMatch(/BEGIN PUBLIC KEY|issuer|audience|agents/);
  });

  test("2^53 을 넘는 상한은 가까운 정수 그대로, 무한대가 되는 상한은 가장 큰 유한한 수로 쓴다", () => {
    const large = siteFileWith("9007199254740993");
    writeRuntimeValues({ [SITE_FILE_ENV]: large }, app, () => {});
    expect(parsed()).toEqual({ allowedOrigins: [], requestChars: 9_007_199_254_740_992 });

    const infinite = siteFileWith(`1${"0".repeat(400)}`);
    writeRuntimeValues({ [SITE_FILE_ENV]: infinite }, app, () => {});
    expect(parsed()).toEqual({ allowedOrigins: [], requestChars: Number.MAX_VALUE });
  });

  test("받은 값을 한 줄로 알린다. 합친 허용 출처와 상한만 싣는다", () => {
    const lines: string[] = [];
    const expected = expectedSiteFile();

    writeRuntimeValues({ [SITE_FILE_ENV]: FIXTURE }, app, (line) => lines.push(line));

    expect(lines).toEqual([
      describeValues({
        allowedOrigins: expected.allowedOrigins,
        requestChars: expected.requestChars,
      }),
    ]);
    expect(lines[0]).toContain(String(expected.requestChars));
    for (const origin of expected.allowedOrigins) {
      expect(lines[0]).toContain(origin);
    }
    expect(lines[0]).not.toMatch(/BEGIN PUBLIC KEY|issuer|audience/);
  });

  test("허용 출처가 없으면 '없음'으로 알린다", () => {
    expect(describeValues({ allowedOrigins: [], requestChars: 20_000 })).toBe(
      "위젯이 받은 값: 허용 출처 없음, 요청 글자 수 상한 20000",
    );
  });

  test("읽지 못하면 아무것도 쓰지 않고 오류를 던지며 알리지도 않는다", () => {
    const lines: string[] = [];

    expect(() =>
      writeRuntimeValues({ [SITE_FILE_ENV]: join(app, "none.toml") }, app, (line) =>
        lines.push(line),
      ),
    ).toThrow("받아들일 수 없다");

    expect(lines).toEqual([]);
    expect(() => written()).toThrow();
  });

  test("다시 띄우면 앞 값 위에 새 값을 덮어쓴다", () => {
    writeRuntimeValues({}, app, () => {});
    writeRuntimeValues({ [SITE_FILE_ENV]: FIXTURE }, app, () => {});

    expect(written()).toBe(JSON.stringify(runtimeValues({ [SITE_FILE_ENV]: FIXTURE })));
  });

  // 윈도에서 링크를 만들 권한이 없으면 건너뛴 것으로 보인다(초록으로 지나가지 않는다). 리눅스의 CI 가 본다.
  test.skipIf(!canSymlink())(
    "그 자리가 다른 폴더 안을 가리키는 링크여도 링크를 따라가 그 폴더에 쓴다",
    () => {
      // 이미지가 읽기 전용 루트에서 쓸 자리를 `/run/agent-os-widget` 안으로 둔다(티켓 03). 이름 바꾸기로 덮으면 링크가 보통
      // 파일로 바뀌어 거기서 실패하므로, 쓰는 코드는 그 자리를 열어 바로 써야 한다.
      const target = join(app, "run");
      mkdirSync(target);
      mkdirSync(join(app, "public"));
      writeFileSync(join(target, RUNTIME_FILE), "{}");
      symlinkSync(join(target, RUNTIME_FILE), join(app, "public", RUNTIME_FILE), "file");

      writeRuntimeValues({}, app, () => {});

      expect(readFileSync(join(target, RUNTIME_FILE), "utf-8")).toBe(
        JSON.stringify({ allowedOrigins: [], requestChars: 20_000 }),
      );
    },
  );
});
