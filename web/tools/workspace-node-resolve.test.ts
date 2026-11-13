// 위젯 미리보기 페이지 서버가 패키지 이름으로 import 할 셋을 `web/tools` 의 스크립트처럼 Node 로 바로 띄워 푼다
// (pilot-portal 명세 "띄우기와 타입 검사"). `@agent-os/ui/themes`, `@agent-os/ui/fonts`, `@agent-os/site-file` 이 빌드 없이,
// `--preserve-symlinks` 없이 읽히는지 본다. vitest 는 Vite 의 해석으로 모듈을 풀어 확장자 없는 상대 import 와 링크 풀이의
// 차이를 가리므로 Node 를 따로 띄우는 사례만 둔다. `@agent-os/site-file` 이 읽는 `smol-toml` 이 그 패키지 폴더의
// `node_modules` 링크로 풀리는 것(명세의 어림)도 이 사례가 본다. `contrast-module.test.ts` 가 같은 길로 명암비 모듈을 본다.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, expect, test } from "vitest";

const WEB = dirname(import.meta.dirname);
// `@agent-os/site-file` 은 그것을 의존성으로 드는 앱(위젯, 뒤에 위젯 미리보기 페이지)에서만 풀린다. `web/` 뿌리는 들지 않는다.
const WIDGET = join(WEB, "apps", "widget");

/** `cwd` 에서 Node 가 ESM 스크립트를 띄워 찍은 JSON. 실패하면 stderr 를 알린다. */
function run(script: string, cwd = WEB): unknown {
  const result = spawnSync(process.execPath, ["--input-type=module", "--eval", script], {
    cwd,
    encoding: "utf-8",
  });
  expect(result.status, result.stderr).toBe(0);
  return JSON.parse(result.stdout);
}

describe("패키지 이름으로 Node 가 바로 읽는 위젯 미리보기 페이지의 의존", () => {
  test("@agent-os/ui/themes 가 테마·기본 테마·모드·밀도를 낸다", () => {
    const loaded = run(
      [
        'const { THEMES, DEFAULT_THEME, MODES, DENSITIES } = await import("@agent-os/ui/themes");',
        "console.log(JSON.stringify({ themes: THEMES.map(({ key }) => key), DEFAULT_THEME, MODES, DENSITIES }));",
      ].join("\n"),
    );

    expect(loaded).toEqual({
      themes: ["guncheong", "nokcheong", "jacho", "jjokbit"],
      DEFAULT_THEME: "nokcheong",
      MODES: ["light", "dark"],
      DENSITIES: ["compact", "regular"],
    });
  });

  test("@agent-os/ui/fonts 가 글꼴 파일 목록과 @font-face 목록을 같은 수로 낸다", () => {
    const loaded = run(
      [
        'const { fontFiles, fontFaces } = await import("@agent-os/ui/fonts");',
        "const files = fontFiles();",
        "const faces = fontFaces();",
        "console.log(JSON.stringify({ filled: files.length > 0, sameCount: files.length === faces.length, family: faces[0]?.family }));",
      ].join("\n"),
    );

    expect(loaded).toEqual({ filled: true, sameCount: true, family: "Noto Sans KR" });
  });

  test("@agent-os/site-file 이 smol-toml 을 제 패키지 폴더에서 풀어 사이트 파일을 읽는다", () => {
    const text = [
      'schema_version = "1"',
      "[[sites]]",
      'issuer = "https://shop.example"',
      'audience = "agent-os"',
      'allowed_origins = ["https://shop.example"]',
      'agents = ["echo"]',
      "[[sites.public_keys]]",
      'kid = "shop-1"',
      'pem = "pem"',
    ].join("\n");
    const loaded = run(
      [
        'const { parseSiteFile } = await import("@agent-os/site-file");',
        `console.log(JSON.stringify(parseSiteFile(${JSON.stringify(text)})));`,
      ].join("\n"),
      WIDGET,
    );

    expect(loaded).toEqual({
      sites: [
        {
          issuer: "https://shop.example",
          audience: "agent-os",
          agents: ["echo"],
          allowedOrigins: ["https://shop.example"],
          publicKeys: [{ kid: "shop-1", pem: "pem" }],
          requestChars: 20_000,
        },
      ],
    });
  });

  test("smol-toml 은 위젯 폴더에서 풀리지 않고 site-file 패키지 폴더의 node_modules 링크로만 풀린다", () => {
    const loaded = run(
      [
        'const seen = await import("smol-toml").then(() => true, () => false);',
        "console.log(JSON.stringify({ seen }));",
      ].join("\n"),
      WIDGET,
    );

    expect(loaded).toEqual({ seen: false });
    expect(existsSync(join(WEB, "packages", "site-file", "node_modules", "smol-toml"))).toBe(true);
  });
});
