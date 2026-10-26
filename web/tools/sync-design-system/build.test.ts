// 짓기 명령의 테스트(design-reverse-sync 명세 Testing Decisions "짓기"). 입력은 실제 디자인 토큰 CSS 를 읽은 사본이고,
// 사례는 그 사본을 고쳐 만든다.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, expect, test } from "vitest";
import { THEMES } from "../../packages/ui/src/themes.ts";
import { buildTokensFile, buildTokensJson, THEME_NAMES } from "./build.ts";
import { CommandError } from "./command.ts";
import { readTokens, type ColorToken, type TokensFile } from "./tokens-json.ts";

const WEB = dirname(dirname(import.meta.dirname));
const CSS = readFileSync(join(WEB, "packages", "ui", "src", "styles", "theme.css"), "utf-8");

const THEME_IDS = [
  "nokcheong-light",
  "nokcheong-dark",
  "guncheong-light",
  "guncheong-dark",
  "jacho-light",
  "jacho-dark",
  "jjokbit-light",
  "jjokbit-dark",
];

/** 사본에서 `line` 으로 시작하는 `nth` 번째(0부터) 줄의 끝에 주석을 단다. 없으면 던진다. */
function commentLine(css: string, line: string, comment: string, nth = 0): string {
  const lines = css.split("\n");
  const found = lines.flatMap((text, index) => (text.trimStart().startsWith(line) ? [index] : []));
  const at = found[nth];
  if (at === undefined) {
    throw new Error(`사본에 ${line} 로 시작하는 ${String(nth)} 번째 줄이 없다`);
  }
  lines[at] = `${lines[at] ?? ""} /* ${comment} */`;
  return lines.join("\n");
}

/** 사본의 `anchor` 줄 바로 앞에 줄들을 끼운다. */
function insertBefore(css: string, anchor: string, added: readonly string[]): string {
  const at = css.indexOf(anchor);
  if (at < 0) {
    throw new Error(`사본에 ${anchor} 가 없다`);
  }
  return css.slice(0, at) + added.map((line) => `${line}\n`).join("") + css.slice(at);
}

function colorToken(file: TokensFile, name: string): ColorToken {
  const token = file.color.tokens.find((candidate) => candidate.name === name);
  if (token === undefined) {
    throw new Error(`색 토큰 ${name} 이 없다`);
  }
  return token;
}

function perTheme(token: ColorToken): Readonly<Record<string, string>> {
  if (typeof token.value === "string") {
    throw new Error(`${token.name} 의 값이 벌마다가 아니라 문자열이다`);
  }
  return token.value;
}

function buildError(css: string): CommandError {
  try {
    buildTokensJson(css);
  } catch (error) {
    if (error instanceof CommandError) {
      return error;
    }
    throw error;
  }
  throw new Error("짓기가 오류 없이 끝났다");
}

describe("짓기", () => {
  test("같은 입력에는 바이트까지 같은 결과를 낸다", () => {
    expect(buildTokensJson(CSS)).toBe(buildTokensJson(CSS));
  });

  test("결과는 지은 tokens.json 을 두 칸 들여 쓴 JSON 과 끝 줄바꿈이다", () => {
    expect(buildTokensJson(CSS)).toBe(`${JSON.stringify(buildTokensFile(CSS), null, 2)}\n`);
  });

  test("토큰은 색 98, 글자 스타일 3, 간격 7, 모서리 4 의 112 개다", () => {
    const file = buildTokensFile(CSS);
    const styles = file.type.groups.flatMap((group) => group.styles);

    expect([
      file.color.tokens.length,
      styles.length,
      file.spacing.tokens.length,
      file.radius.tokens.length,
    ]).toEqual([98, 3, 7, 4]);
  });

  test("색 토큰은 원색, 반투명, 쓰임새 토큰의 차례이고 그 안에서는 디자인 토큰 CSS 의 차례다", () => {
    const names = buildTokensFile(CSS).color.tokens.map((token) => token.name);

    expect([0, 67, 68, 74, 75, 97].map((index) => names[index])).toEqual([
      "gray-0",
      "info-950",
      "overlay-black-4",
      "overlay-white-16",
      "bg",
      "shadow-color",
    ]);
  });

  test("테마는 여덟 벌이고 첫째가 녹청 라이트, 그다음 녹청 다크와 군청·자초·쪽빛의 라이트·다크 순이다", () => {
    const { themes } = buildTokensFile(CSS).color;

    expect(themes.map((theme) => theme.id)).toEqual(THEME_IDS);
    expect(themes.slice(0, 3).map((theme) => theme.name)).toEqual([
      "녹청 라이트",
      "녹청 다크",
      "군청 라이트",
    ]);
  });

  test("테마의 한국어 이름은 패키지의 테마 목록과 키와 이름이 같다", () => {
    expect(THEME_NAMES).toEqual(new Map(THEMES.map((theme) => [theme.key, theme.name])));
  });

  test("원색 68 개는 여덟 벌의 값을 모두 적고, 같은 테마의 라이트·다크는 그 테마 블록의 값을 나눈다", () => {
    const file = buildTokensFile(CSS);
    const primitives = file.color.tokens.filter(
      (token) =>
        typeof token.value !== "string" && !String(token.value[THEME_IDS[0] ?? ""]).startsWith("{"),
    );
    const gray50 = perTheme(colorToken(file, "gray-50"));

    expect(primitives).toHaveLength(68);
    expect(
      primitives.every((token) => Object.keys(perTheme(token)).join() === THEME_IDS.join()),
    ).toBe(true);
    expect(gray50).toMatchObject({
      "nokcheong-light": "#f4f8fb",
      "nokcheong-dark": "#f4f8fb",
      "guncheong-light": "#f7f7f7",
      "jjokbit-dark": "#faf7f3",
    });
  });

  test("반투명 7 개는 문자열 하나다", () => {
    const overlays = buildTokensFile(CSS).color.tokens.filter((token) =>
      token.name.startsWith("overlay-"),
    );

    expect(overlays.map((token) => [token.name, token.value])).toEqual([
      ["overlay-black-4", "#0000000a"],
      ["overlay-black-7", "#00000012"],
      ["overlay-black-12", "#0000001f"],
      ["overlay-black-40", "#00000066"],
      ["overlay-white-6", "#ffffff0f"],
      ["overlay-white-10", "#ffffff1a"],
      ["overlay-white-16", "#ffffff29"],
    ]);
  });

  test("쓰임새 토큰 23 개는 벌마다 그 벌의 대응이 가리키는 원색이나 반투명을 {이름} 으로 적는다", () => {
    const file = buildTokensFile(CSS);
    const semantic = file.color.tokens.filter(
      (token) =>
        typeof token.value !== "string" && String(token.value[THEME_IDS[0] ?? ""]).startsWith("{"),
    );

    expect(semantic).toHaveLength(23);
    expect(perTheme(colorToken(file, "bg"))).toMatchObject({
      "nokcheong-light": "{gray-50}",
      "nokcheong-dark": "{gray-950}",
      "jjokbit-light": "{gray-50}",
    });
    expect(perTheme(colorToken(file, "bg-hover"))).toMatchObject({
      "guncheong-light": "{overlay-black-4}",
      "guncheong-dark": "{overlay-white-6}",
    });
  });

  test("군청·자초의 주 버튼은 그 테마의 덮기를, 녹청·쪽빛은 먹색 갈래를 가리킨다", () => {
    const file = buildTokensFile(CSS);

    expect(perTheme(colorToken(file, "primary"))).toEqual({
      "nokcheong-light": "{gray-900}",
      "nokcheong-dark": "{gray-100}",
      "guncheong-light": "{accent-600}",
      "guncheong-dark": "{accent-400}",
      "jacho-light": "{accent-600}",
      "jacho-dark": "{accent-400}",
      "jjokbit-light": "{gray-900}",
      "jjokbit-dark": "{gray-100}",
    });
    expect(perTheme(colorToken(file, "on-primary"))).toMatchObject({
      "guncheong-light": "{gray-0}",
      "guncheong-dark": "{accent-950}",
      "nokcheong-dark": "{gray-950}",
    });
  });

  test("hex 는 소문자로 낸다", () => {
    const file = buildTokensFile(CSS.replace("--gray-50: #f4f8fb;", "--gray-50: #F4F8FB;"));

    expect(perTheme(colorToken(file, "gray-50"))["nokcheong-light"]).toBe("#f4f8fb");
  });

  test("페이지가 색으로 읽지 않는 색 함수의 속성은 색 토큰으로 내지 않아, 낸 색 토큰을 페이지가 모두 읽는다", () => {
    const css = insertBefore(CSS, "    --gray-0: #ffffff;", ["    --tinted: rgb(var(--x) 0 0);"]);
    const file = buildTokensFile(css);

    expect(file.color.tokens.map((token) => token.name)).not.toContain("tinted");
    expect(readTokens(file).families.get("color")?.tokens.size).toBe(file.color.tokens.length);
  });

  test("지금 디자인 토큰 CSS 에는 줄 끝 주석이 없어 설명이 모두 빈 칸이다", () => {
    const file = buildTokensFile(CSS);
    const usages = [
      ...file.color.tokens,
      ...file.type.groups.flatMap((group) => group.styles),
      ...file.spacing.tokens,
      ...file.radius.tokens,
    ].map((token) => token.usage);

    expect(new Set(usages)).toEqual(new Set([""]));
  });

  test("설명은 그 토큰을 선언한 줄 끝의 주석이다", () => {
    let css = CSS;
    css = commentLine(css, "--gray-500: #606466;", "흐린 글자의 원색");
    css = commentLine(css, "--overlay-black-4:", "올림의 반투명");
    css = commentLine(css, "--bg: var(--gray-50);", "화면 바탕");
    css = commentLine(css, "--spacing-4:", "카드 안쪽 여백");
    css = commentLine(css, "--radius-m:", "버튼과 카드의 모서리");
    css = commentLine(css, "--text-title:", "화면 제목");
    const file = buildTokensFile(css);

    expect(colorToken(file, "gray-500").usage).toBe("흐린 글자의 원색");
    expect(colorToken(file, "overlay-black-4").usage).toBe("올림의 반투명");
    expect(colorToken(file, "bg").usage).toBe("화면 바탕");
    expect(file.spacing.tokens.find((token) => token.name === "spacing-4")?.usage).toBe(
      "카드 안쪽 여백",
    );
    expect(file.radius.tokens.find((token) => token.name === "radius-m")?.usage).toBe(
      "버튼과 카드의 모서리",
    );
    expect(file.type.groups[0]?.styles.find((style) => style.name === "text-title")?.usage).toBe(
      "화면 제목",
    );
  });

  test("설명은 녹청 블록과 라이트 대응 블록의 줄에서만 읽고, 다른 테마 블록·다크 대응·앞 줄의 주석은 읽지 않는다", () => {
    let css = CSS;
    css = commentLine(css, "--gray-500: #636363;", "군청 블록의 주석");
    css = commentLine(css, "--bg: var(--gray-950);", "다크 대응의 주석");
    // 줄 하나를 차지한 주석은 앞 선언(radius-s)의 것도 뒤 선언(radius-m)의 것도 아니다.
    css = insertBefore(css, "--radius-m:", ["  /* 앞 줄의 주석 */"]);
    const file = buildTokensFile(css);

    expect(colorToken(file, "gray-500").usage).toBe("");
    expect(colorToken(file, "bg").usage).toBe("");
    expect(file.radius.tokens.slice(0, 2).map((token) => [token.name, token.usage])).toEqual([
      ["radius-s", ""],
      ["radius-m", ""],
    ]);
  });

  test("글자 크기는 type 묶음 하나에 스타일 셋이고 크기·줄 높이·굵기가 디자인 토큰 CSS 의 값 그대로다", () => {
    const { type } = buildTokensFile(CSS);

    expect(type.groups).toHaveLength(1);
    expect(type.groups[0]?.styles).toEqual([
      { name: "text-title", fontSize: "24px", lineHeight: "32px", fontWeight: 600, usage: "" },
      { name: "text-small", fontSize: "12px", lineHeight: "16px", fontWeight: 400, usage: "" },
      { name: "text-badge", fontSize: "12px", lineHeight: "16px", fontWeight: 500, usage: "" },
    ]);
  });

  test("글자 묶음은 --sans 값 하나를 든 글꼴 묶음 sans 를 가리키고 글꼴 파일 목록은 내지 않는다", () => {
    const { type } = buildTokensFile(CSS);

    expect(type.families).toEqual({ sans: '"Noto Sans KR", system-ui, sans-serif' });
    expect(type.groups[0]?.family).toBe("sans");
    expect(Object.keys(type)).not.toContain("fonts");
  });

  test("간격 7 개와 모서리 4 개를 이름과 px 값 그대로 내고 계열 설명은 비운다", () => {
    const file = buildTokensFile(CSS);

    expect(file.spacing.tokens.map((token) => [token.name, token.value])).toEqual([
      ["spacing-0", "0px"],
      ["spacing-1", "4px"],
      ["spacing-2", "8px"],
      ["spacing-3", "12px"],
      ["spacing-4", "16px"],
      ["spacing-6", "24px"],
      ["spacing-8", "32px"],
    ]);
    expect(file.radius.tokens.map((token) => [token.name, token.value])).toEqual([
      ["radius-s", "4px"],
      ["radius-m", "8px"],
      ["radius-l", "12px"],
      ["radius-full", "999px"],
    ]);
    expect([file.spacing.note, file.radius.note]).toEqual(["", ""]);
  });

  test("밀도와 이름 있는 치수는 내지 않는다", () => {
    const names = JSON.stringify(buildTokensFile(CSS));

    for (const left of [
      "body-size",
      "control-h",
      "spacing-control-s",
      "spacing-nav",
      "icon-s",
      "font-weight",
    ]) {
      expect(names).not.toContain(`"${left}`);
    }
  });

  test("테마가 여덟 벌을 넘는 입력은 한도 오류다", () => {
    const extra = CSS.replace(
      '[data-theme="jjokbit"],\n  :host([data-theme="jjokbit"]) {',
      [
        '[data-theme="jjokbit"],',
        '  :host([data-theme="jjokbit"]),',
        '  [data-theme="extra"] {',
      ].join("\n"),
    );

    const error = buildError(extra);

    expect(extra).not.toBe(CSS);
    expect(error.kind).toBe("limit");
    expect(error.message).toContain("페이지 테마(테마 × 모드) 수가 10 개로");
  });

  test("색이 600 개를 넘는 입력은 한도 오류다", () => {
    const filler = Array.from(
      { length: 503 },
      (_, index) => `    --filler-${String(index)}: #000000;`,
    );
    const css = insertBefore(CSS, "    --gray-0: #ffffff;", filler);

    const error = buildError(css);

    expect(error.kind).toBe("limit");
    expect(error.message).toContain("색 토큰 수가 601 개로");
  });

  test("600 개 그대로의 색은 한도 안이다", () => {
    const filler = Array.from(
      { length: 502 },
      (_, index) => `    --filler-${String(index)}: #000000;`,
    );

    expect(
      buildTokensFile(insertBefore(CSS, "    --gray-0: #ffffff;", filler)).color.tokens,
    ).toHaveLength(600);
  });

  test("간격이 60 개를 넘는 입력은 한도 오류다", () => {
    const filler = Array.from(
      { length: 54 },
      (_, index) => `  --spacing-${String(100 + index)}: 1px;`,
    );

    const error = buildError(insertBefore(CSS, "  --spacing-0: 0px;", filler));

    expect(error.kind).toBe("limit");
    expect(error.message).toContain("간격 토큰 수가 61 개로");
  });
});
