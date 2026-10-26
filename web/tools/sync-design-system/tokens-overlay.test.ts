// 정규 꼴의 자리 옮기기와 tokens.json 으로 적기의 테스트(design-reverse-sync 명세 "겹침"의 "병합됐으면"의 2026-10-22
// 주석의 셋째, 티켓 06 "확인이 claim 과 맞대기"의 이어받을 기준본). 입력은 실제 디자인 토큰 CSS 로 지은 tokens.json 을
// 고친 것과 임시 아티팩트에서 받은 시험 자료(`fixtures/`)다.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, expect, test } from "vitest";
import { buildTokensFile } from "./build.ts";
import { comparisonHash, DIFF_KINDS, diffTokens, readTokens, valueAt } from "./tokens-json.ts";
import { inheritedBaseline, sameAt, tokensFileOf, withSpots } from "./tokens-overlay.ts";

const WEB = dirname(dirname(import.meta.dirname));
const CSS = readFileSync(join(WEB, "packages", "ui", "src", "styles", "theme.css"), "utf-8");
const BUILT = buildTokensFile(CSS);

function fixture(name: string): unknown {
  const parsed: unknown = JSON.parse(
    readFileSync(join(import.meta.dirname, "fixtures", name), "utf-8"),
  );
  return parsed;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function record(value: unknown): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new Error("객체가 아니다");
  }
  return value;
}

function list(value: unknown): unknown[] {
  if (!Array.isArray(value)) {
    throw new Error("배열이 아니다");
  }
  return value.map((item: unknown) => item);
}

/** 지은 파일의 사본을 `edit` 이 그 자리에서 고친 것. */
function edited(edit: (file: Record<string, unknown>) => void): Record<string, unknown> {
  const parsed: unknown = JSON.parse(JSON.stringify(BUILT));
  const file = record(parsed);
  edit(file);
  return file;
}

function tokenIn(
  file: Record<string, unknown>,
  family: string,
  name: string,
): Record<string, unknown> {
  const found = list(record(file[family]).tokens)
    .map(record)
    .find((token) => token.name === name);
  if (found === undefined) {
    throw new Error(`${family} 에 ${name} 이 없다`);
  }
  return found;
}

function styleIn(file: Record<string, unknown>, name: string): Record<string, unknown> {
  const found = list(record(file.type).groups)
    .map(record)
    .flatMap((group) => list(group.styles).map(record))
    .find((style) => style.name === name);
  if (found === undefined) {
    throw new Error(`글자 스타일 ${name} 이 없다`);
  }
  return found;
}

/** 모든 차이 종류가 나는 고침. */
function everyKind(file: Record<string, unknown>): void {
  record(tokenIn(file, "color", "gray-900").value)["nokcheong-light"] = "#000000";
  tokenIn(file, "color", "accent-600").usage = "강조";
  const color = record(file.color);
  color.tokens = [...list(color.tokens), { name: "new-1", value: "#123456", usage: "" }];
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
  type.groups = [...groups, { name: "둘째", family: "sans", styles: [] }];
  file.shadow = { note: "", tokens: [{ name: "shadow-1", value: "0 1px 2px #000" }] };
}

describe("tokens.json 으로 적기", () => {
  test.each([
    ["지은 파일", BUILT],
    ["올린 시험 자료", fixture("uploaded-tokens.json")],
    ["페이지가 저장한 시험 자료", fixture("page-saved-tokens.json")],
    ["모든 종류를 고친 파일", edited(everyKind)],
  ])("%s 의 정규 꼴을 적어 다시 읽으면 같은 정규 꼴이다", (_name, file) => {
    const tokens = readTokens(file);
    const again = readTokens(tokensFileOf(tokens));

    expect(diffTokens(tokens, again)).toEqual([]);
    expect(comparisonHash(again)).toBe(comparisonHash(tokens));
  });

  test("묶음이 없는 글자 스타일은 빈 묶음을 더해 적는다", () => {
    const tokens = readTokens(BUILT);
    const style = tokens.type.styles.get("text-title");
    if (style === undefined) {
      throw new Error("text-title 이 없다");
    }
    const moved = {
      ...tokens,
      type: {
        ...tokens.type,
        styles: new Map([...tokens.type.styles, ["text-title", { ...style, group: "없는 묶음" }]]),
      },
    };
    const again = readTokens(tokensFileOf(moved));

    expect(again.type.styles.get("text-title")?.group).toBe("없는 묶음");
    expect(again.type.groups.get("없는 묶음")).toEqual({ family: "", note: "" });
  });
});

describe("자리 옮기기", () => {
  const target = readTokens(BUILT);
  const source = readTokens(edited(everyKind));
  const diffs = diffTokens(target, source);

  test("모든 차이를 옮기면 source 와 같다", () => {
    expect(new Set(diffs.map((diff) => diff.kind))).toEqual(new Set(DIFF_KINDS));
    const moved = withSpots(target, source, diffs);

    expect(diffTokens(moved, source)).toEqual([]);
  });

  test("옮긴 차이의 자리는 source 의 값이고 나머지 자리는 target 그대로다", () => {
    for (let index = 0; index < diffs.length; index += 1) {
      const chosen = diffs.filter((_diff, at) => at % 2 === index % 2);
      const moved = withSpots(target, source, chosen);
      for (const diff of diffs) {
        const expected = chosen.includes(diff) ? source : target;
        expect(sameAt(moved, expected, diff), JSON.stringify(diff)).toBe(true);
      }
    }
  });

  test("벌을 지운 차이를 옮기면 벌 목록에서 빠지고, 되돌려 옮기면 다시 든다", () => {
    const fewer = readTokens(
      edited((file) => {
        const color = record(file.color);
        color.themes = list(color.themes).slice(0, -1);
      }),
    );
    const removed = diffTokens(target, fewer).filter((diff) => diff.token === undefined);
    expect(removed.map((diff) => diff.kind)).toEqual(["removed"]);

    const moved = withSpots(target, fewer, removed);
    expect(moved.themes).toEqual(fewer.themes);
    expect(withSpots(moved, target, removed).themes).toEqual(target.themes);
  });
});

describe("이어받을 기준본", () => {
  // 앞 들이기의 claim 사본은 gray-500 과 gray-600 을 바꿨다. 그 들이기가 병합된 뒤 사람이 웹에서 gray-600 을 더
  // 고치고 spacing-4 의 설명도 고쳤다. 확인이 더 고친 몫으로 낸 자리만 사본의 값으로 바꾼다.
  const claim = edited((file) => {
    record(tokenIn(file, "color", "gray-500").value)["nokcheong-light"] = "#777777";
    record(tokenIn(file, "color", "gray-600").value)["nokcheong-light"] = "#666666";
  });
  const web = edited((file) => {
    record(tokenIn(file, "color", "gray-500").value)["nokcheong-light"] = "#777777";
    record(tokenIn(file, "color", "gray-600").value)["nokcheong-light"] = "#606060";
    tokenIn(file, "spacing", "spacing-4").usage = "웹에서 더 고친 설명";
  });

  test("더 고친 몫의 자리만 claim 사본의 값이고 나머지는 지금 웹이다", () => {
    const further = diffTokens(readTokens(claim), readTokens(web));
    expect(further.map((diff) => diff.token)).toEqual(["gray-600", "spacing-4"]);

    const inherited = readTokens(inheritedBaseline(web, claim, further));

    expect(diffTokens(inherited, readTokens(claim))).toEqual([]);
    expect(diffTokens(inherited, readTokens(web))).toEqual(further);
    for (const diff of further) {
      expect(valueAt(inherited, diff)).toEqual(diff.before);
    }
  });
});
