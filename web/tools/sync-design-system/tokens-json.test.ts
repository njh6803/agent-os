// 두 벌의 tokens.json 을 값으로 맞대는 공용 함수의 테스트(design-reverse-sync 명세 "맞대는 것"의 2026-10-22 주석,
// Testing Decisions "왕복"의 셋째 문장). 입력은 실제 디자인 토큰 CSS 로 지은 tokens.json 을 고친 것과, 임시
// 아티팩트에서 받은 시험 자료(`fixtures/`)다.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, expect, test } from "vitest";
import { buildTokensFile } from "./build.ts";
import {
  colorLiteral,
  comparisonHash,
  DIFF_KINDS,
  diffTokens,
  readTokens,
  valueAt,
  type TokensFile,
  type TokenDiff,
} from "./tokens-json.ts";

const WEB = dirname(dirname(import.meta.dirname));
const CSS = readFileSync(join(WEB, "packages", "ui", "src", "styles", "theme.css"), "utf-8");
const BUILT = buildTokensFile(CSS);

/** 고칠 수 있는 깊은 사본. 지은 파일은 JSON 이라 JSON 왕복이 사본이다. */
function copy(file: TokensFile): unknown {
  const text = JSON.stringify(file);
  const parsed: unknown = JSON.parse(text);
  return parsed;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isList(value: unknown): value is unknown[] {
  return Array.isArray(value);
}

/** 같은 객체를 객체로 본다. 사본이 아니라 그 자리에서 고친다. */
function record(value: unknown): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new Error("객체가 아니다");
  }
  return value;
}

/** 같은 배열을 배열로 본다. */
function list(value: unknown): unknown[] {
  if (!isList(value)) {
    throw new Error("배열이 아니다");
  }
  return value;
}

/** 사본을 고친다. `edit` 이 받은 객체를 그 자리에서 바꾼다. */
function edited(edit: (file: Record<string, unknown>) => void): Record<string, unknown> {
  const file = record(copy(BUILT));
  edit(file);
  return file;
}

/** `family` 계열에서 이름이 `name` 인 토큰 객체. 그 자리에서 고칠 수 있다. */
function tokenIn(
  file: Record<string, unknown>,
  family: string,
  name: string,
): Record<string, unknown> {
  const tokens = list(record(file[family]).tokens);
  const found = tokens.map(record).find((token) => token.name === name);
  if (found === undefined) {
    throw new Error(`${family} 에 ${name} 이 없다`);
  }
  return found;
}

function styleIn(file: Record<string, unknown>, name: string): Record<string, unknown> {
  const groups = list(record(file.type).groups).map(record);
  const found = groups
    .flatMap((group) => list(group.styles).map(record))
    .find((style) => style.name === name);
  if (found === undefined) {
    throw new Error(`글자 스타일 ${name} 이 없다`);
  }
  return found;
}

/**
 * 페이지가 저장하며 꼴만 다시 쓴 tokens.json. Design System 형식 판 1792564314-af13 의 `app.js` 가 저장할 때 내는
 * 꼴(`version` 이 앞, 문자열 색 값을 첫 테마의 객체로, 빈 설명 칸, 글자 스타일의 모든 칸과 문자열 굵기, 빈 글꼴 목록)을
 * 손으로 옮겼다. 실제 저장본은 임시 아티팩트에서 받은 시험 자료가 본다.
 */
function pageRewrite(file: TokensFile): unknown {
  const first = file.color.themes[0]?.id ?? "";
  return {
    version: 1,
    color: {
      themes: file.color.themes.map((theme) => ({ id: theme.id, name: theme.name })),
      tokens: file.color.tokens.map((token) => ({
        name: token.name,
        value: typeof token.value === "string" ? { [first]: token.value } : token.value,
        usage: token.usage,
      })),
    },
    type: {
      fonts: [],
      families: file.type.families,
      groups: file.type.groups.map((group) => ({
        name: group.name,
        family: group.family,
        note: "",
        styles: group.styles.map((style) => ({
          name: style.name,
          fontSize: style.fontSize,
          lineHeight: style.lineHeight,
          fontWeight: String(style.fontWeight),
          letterSpacing: "0",
          fontStyle: "normal",
          opticalSize: null,
          family: "",
          sample: "",
          usage: style.usage,
        })),
      })),
    },
    spacing: { note: "", tokens: file.spacing.tokens.map((token) => ({ ...token })) },
    radius: { note: "", tokens: file.radius.tokens.map((token) => ({ ...token })) },
  };
}

function compare(after: unknown): { diffs: TokenDiff[]; sameHash: boolean } {
  const before = readTokens(BUILT);
  const read = readTokens(after);
  return {
    diffs: diffTokens(before, read),
    sameHash: comparisonHash(before) === comparisonHash(read),
  };
}

describe("값으로 맞대기", () => {
  test("같은 파일은 차이가 없고 맞대는 값도 같다", () => {
    expect(compare(copy(BUILT))).toEqual({ diffs: [], sameHash: true });
  });

  test("페이지가 꼴만 다시 쓴 같은 내용은 차이가 없고 맞대는 값도 같다", () => {
    expect(compare(pageRewrite(BUILT))).toEqual({ diffs: [], sameHash: true });
  });

  test("대문자 hex 와 페이지가 소문자로 다시 쓴 것은 차이가 없다", () => {
    const upper = edited((file) => {
      const gray = tokenIn(file, "color", "gray-50");
      gray.value = { ...record(gray.value), "guncheong-dark": "#F7F7F7" };
    });

    expect(diffTokens(readTokens(upper), readTokens(pageRewrite(BUILT)))).toEqual([]);
    expect(comparisonHash(readTokens(upper))).toBe(comparisonHash(readTokens(BUILT)));
  });

  test("맞대는 값은 sha256 의 16 진수 64 자다", () => {
    expect(comparisonHash(readTokens(BUILT))).toMatch(/^[0-9a-f]{64}$/);
  });

  test("원색 한 벌의 값 하나는 그 토큰·벌의 값 차이다", () => {
    const after = edited((file) => {
      const gray = tokenIn(file, "color", "gray-50");
      gray.value = { ...record(gray.value), "nokcheong-light": "#000000" };
    });

    expect(compare(after)).toEqual({
      diffs: [
        {
          kind: "value",
          family: "color",
          token: "gray-50",
          theme: "nokcheong-light",
          before: "#f4f8fb",
          after: "#000000",
        },
      ],
      sameHash: false,
    });
  });

  test("반투명의 첫 테마만 고치면 여덟 벌이 함께 바뀐 값 차이다", () => {
    const after = edited((file) => {
      tokenIn(file, "color", "overlay-black-4").value = { "nokcheong-light": "#0000000b" };
    });
    const { diffs } = compare(after);

    expect(diffs).toHaveLength(8);
    expect(diffs.every((diff) => diff.kind === "value" && diff.token === "overlay-black-4")).toBe(
      true,
    );
    expect(diffs.map((diff) => diff.after)).toEqual(Array.from({ length: 8 }, () => "#0000000b"));
  });

  test("설명 하나는 그 토큰의 설명 차이다", () => {
    const after = edited((file) => {
      tokenIn(file, "radius", "radius-m").usage = "버튼과 카드";
    });

    expect(compare(after)).toEqual({
      diffs: [
        { kind: "usage", family: "radius", token: "radius-m", before: "", after: "버튼과 카드" },
      ],
      sameHash: false,
    });
  });

  test("토큰을 더하면 더한 것이다", () => {
    const after = edited((file) => {
      list(record(file.spacing).tokens).push({ name: "spacing-5", value: "20px", usage: "" });
    });

    expect(compare(after)).toEqual({
      diffs: [
        {
          kind: "added",
          family: "spacing",
          token: "spacing-5",
          before: null,
          after: { value: "20px", usage: "" },
        },
      ],
      sameHash: false,
    });
  });

  test("토큰을 지우면 지운 것이다", () => {
    const after = edited((file) => {
      const color = record(file.color);
      color.tokens = list(color.tokens).filter((token) => record(token).name !== "info-950");
    });
    const { diffs, sameHash } = compare(after);

    expect(diffs.map((diff) => [diff.kind, diff.family, diff.token, diff.after])).toEqual([
      ["removed", "color", "info-950", null],
    ]);
    expect(sameHash).toBe(false);
  });

  test("글자 스타일의 크기는 값 차이, 자간은 글자 스타일의 다른 칸 차이다", () => {
    const after = edited((file) => {
      styleIn(file, "text-title").fontSize = "26px";
      styleIn(file, "text-small").letterSpacing = "0.5px";
    });

    expect(compare(after)).toEqual({
      diffs: [
        {
          kind: "typeField",
          family: "type",
          token: "text-small",
          field: "letterSpacing",
          before: "0",
          after: "0.5px",
        },
        {
          kind: "value",
          family: "type",
          token: "text-title",
          field: "fontSize",
          before: "24px",
          after: "26px",
        },
      ],
      sameHash: false,
    });
  });

  test("계열 설명은 계열 설명 차이다", () => {
    const after = edited((file) => {
      record(file.spacing).note = "Tailwind 의 숫자 단계";
    });

    expect(compare(after)).toEqual({
      diffs: [
        { kind: "familyNote", family: "spacing", before: "", after: "Tailwind 의 숫자 단계" },
      ],
      sameHash: false,
    });
  });

  test("새 계열은 그 계열을 더한 것이다", () => {
    const after = edited((file) => {
      file.shadow = {
        tokens: [{ name: "shadow-float", value: "0 8px 24px #0000001f", usage: "" }],
      };
    });
    const { diffs, sameHash } = compare(after);

    expect(diffs.map((diff) => [diff.kind, diff.family, diff.token])).toEqual([
      ["added", "shadow", undefined],
    ]);
    expect(sameHash).toBe(false);
  });

  test("페이지가 버리는 테마 id(객체의 기본 속성 이름)는 벌로 세지 않는다", () => {
    // id 는 소문자로 바꾼 뒤 거르므로 `toString` 같은 낙타 꼴 이름은 걸리지 않는다(페이지도 같다).
    const themes = ["prototype", "constructor", "nokcheong-light"].map((id) => ({
      id,
      name: id,
    }));

    expect(readTokens({ color: { themes, tokens: [] } }).themes).toEqual(["nokcheong-light"]);
  });

  test("같은 이름의 둘째 토큰은 한 계열 안에 있든 앞 계열이 쓴 이름이든 버린다", () => {
    const read = readTokens({
      color: { themes: [{ id: "a" }], tokens: [{ name: "x", value: "#111111" }] },
      spacing: {
        tokens: [
          { name: "x", value: "4px" },
          { name: "s", value: "4px" },
          { name: "s", value: "8px" },
        ],
      },
      radius: {
        tokens: [
          { name: "s", value: "2px" },
          { name: "r", value: "2px" },
        ],
      },
    });
    const spacing = [...(read.families.get("spacing")?.tokens ?? [])];

    expect(spacing.map(([name, token]) => [name, token.value])).toEqual([["s", "4px"]]);
    expect([...(read.families.get("radius")?.tokens.keys() ?? [])]).toEqual(["r"]);
  });

  test("맞대는 몫 밖의 칸(이름, 판, 테마의 표시 이름)은 맞대지 않는다", () => {
    const after = edited((file) => {
      file.name = "다른 이름";
      file.version = 2;
      const themes = list(record(file.color).themes).map(record);
      const firstTheme = themes[0];
      if (firstTheme !== undefined) {
        firstTheme.name = "Nokcheong Light";
      }
    });

    expect(compare(after)).toEqual({ diffs: [], sameHash: true });
  });
});

describe("차이 자리의 값", () => {
  // 들이기가 웹의 차이마다 같은 자리를 코드에서 읽어 셋을 맞댄다(명세 "거꾸로 동기화"의 "셋으로 맞댄다").
  const after = edited((file) => {
    record(tokenIn(file, "color", "gray-900").value)["nokcheong-light"] = "#000000";
    tokenIn(file, "color", "accent-600").usage = "강조";
    list(record(file.color).tokens).push({ name: "new-1", value: "#123456", usage: "" });
    list(record(file.color).themes).pop();
    tokenIn(file, "radius", "radius-s").value = "5px";
    const spacing = record(file.spacing);
    spacing.note = "간격";
    spacing.tokens = list(spacing.tokens).filter((token) => record(token).name !== "spacing-8");
    const title = styleIn(file, "text-title");
    title.fontSize = "25px";
    title.letterSpacing = "1px";
    title.usage = "제목";
    const type = record(file.type);
    record(type.families).mono = "monospace";
    type.fonts = [{ family: "X", file: "x.woff2" }];
    const groups = list(type.groups);
    record(groups[0]).note = "묶음";
    groups.push({ name: "둘째", family: "sans", styles: [] });
    file.shadow = { note: "", tokens: [{ name: "shadow-1", value: "0 1px 2px #000" }] };
  });
  const before = readTokens(BUILT);
  const read = readTokens(after);
  const diffs = diffTokens(before, read);

  test("차이마다 그 자리를 두 벌에서 읽은 값은 그 차이의 전과 후다", () => {
    expect(new Set(diffs.map((diff) => diff.kind))).toEqual(new Set(DIFF_KINDS));
    expect(diffs.length).toBeGreaterThan(12);
    expect(diffs.map((diff) => [valueAt(before, diff), valueAt(read, diff)])).toEqual(
      diffs.map((diff) => [diff.before, diff.after]),
    );
  });

  test("다른 벌에 그 자리가 없으면 null 이다", () => {
    const empty = readTokens({});

    expect(
      diffs
        .filter((diff) => diff.kind !== "familyNote" && diff.family !== "type")
        .filter((diff) => diff.theme === undefined || diff.kind === "value")
        .map((diff) => valueAt(empty, diff)),
    ).toEqual(
      diffs
        .filter((diff) => diff.kind !== "familyNote" && diff.family !== "type")
        .filter((diff) => diff.theme === undefined || diff.kind === "value")
        .map(() => null),
    );
  });
});

describe("색 리터럴", () => {
  test.each([
    ["#F4F8FB", "#f4f8fb"],
    [" oklch(0.5 0.1 200) ", "oklch(0.5 0.1 200)"],
    ["RGB(255 0 0 / 50%)", "rgb(255 0 0 / 50%)"],
  ])("페이지가 색으로 읽는 %s 는 소문자 %s 다", (value, literal) => {
    expect(colorLiteral(value)).toBe(literal);
  });

  test.each([
    "rgb(var(--x) 0 0)",
    "oklch(from #fff l c h)",
    `oklch(${"0".repeat(61)})`,
    "{gray-0}",
    "var(--gray-0)",
    "red",
  ])("페이지가 색으로 읽지 않는 %s 는 리터럴이 아니다", (value) => {
    expect(colorLiteral(value)).toBeUndefined();
  });
});

describe("임시 아티팩트에서 받은 저장본", () => {
  // 비공개 임시 디자인 시스템 아티팩트(2026-10-22, 지금은 지웠다)에서 Artifact 도구가 파일마다 낸 sha256 이다. 올린
  // tokens.json 은 판 1792670467-a367 의 것이고, 사람이 페이지에서 gray-50 의 녹청 라이트 값과 radius-m 설명을
  // 고쳐 저장한 뒤의 두 파일은 판 1792671359-792c 의 것이다(.scratch/design-reverse-sync/probes/README.md).
  // 올린 파일을 따로 두는 것은, 디자인 토큰 CSS 가 바뀌어도(03 의 설명 주석) 이 사례가 그대로이게 하려는 것이다.
  const RECEIVED = [
    ["uploaded-tokens.json", "191da4dc98d92e537243767fc8c3f0b22a5b9e75b0b83b5e7751590e51f90251"],
    ["page-saved-tokens.json", "8ec4aab6d2dcd42353561439aea3a49910ab787efbcbbcd5601a1cced26020bb"],
    ["page-saved-README.md", "fa615f747a3d82916b44d4f18f1c84cadaa5a12c89db05ebdef0dcb37338406c"],
  ] as const;

  function fixture(name: string): Buffer {
    return readFileSync(join(import.meta.dirname, "fixtures", name));
  }

  function parsedFixture(name: string): unknown {
    const parsed: unknown = JSON.parse(fixture(name).toString("utf-8"));
    return parsed;
  }

  test.each(RECEIVED)("%s 는 Artifact 도구가 낸 바이트 그대로다", (name, sha256) => {
    expect(createHash("sha256").update(fixture(name)).digest("hex")).toBe(sha256);
  });

  test("올린 파일과 페이지가 저장한 파일을 맞대면 사람이 고친 둘만 나온다", () => {
    const uploaded = readTokens(parsedFixture("uploaded-tokens.json"));
    const saved = readTokens(parsedFixture("page-saved-tokens.json"));

    expect(diffTokens(uploaded, saved)).toEqual([
      {
        kind: "value",
        family: "color",
        token: "gray-50",
        theme: "nokcheong-light",
        before: "#f4f8fb",
        after: "#f0f4f8",
      },
      {
        kind: "usage",
        family: "radius",
        token: "radius-m",
        before: "",
        after: "버튼과 카드의 모서리",
      },
    ]);
  });

  test("페이지가 꼴을 다시 쓴 저장본도 고친 둘을 되돌리면 올린 파일과 맞대는 값이 같다", () => {
    const uploaded = record(parsedFixture("uploaded-tokens.json"));
    const saved = record(parsedFixture("page-saved-tokens.json"));
    // 페이지가 꼴을 다시 썼다는 표지. 올린 파일에 없던 빈 글꼴 목록이 저장본에 있다.
    expect(Object.hasOwn(record(uploaded.type), "fonts")).toBe(false);
    expect(record(saved.type).fonts).toEqual([]);

    const gray = tokenIn(saved, "color", "gray-50");
    gray.value = { ...record(gray.value), "nokcheong-light": "#f4f8fb" };
    tokenIn(saved, "radius", "radius-m").usage = "";

    expect(comparisonHash(readTokens(saved))).toBe(comparisonHash(readTokens(uploaded)));
  });
});
