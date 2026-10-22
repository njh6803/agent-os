/**
 * 짓기 명령. 디자인 토큰 CSS 에서 Design System 형식의 `tokens.json` 을 짓는다(design-reverse-sync 명세 "tokens.json",
 * ADR 0025 의 2026-10-21 이력). 같은 입력에는 바이트까지 같은 결과를 낸다.
 *
 * - 페이지 테마는 디자인 토큰 CSS 의 테마 × 모드 둘의 벌이고 id 는 `<테마>-<모드>` 다. 테마는 CSS 에 처음 나온
 *   차례이고(기본 테마의 블록이 앞이다), 한 테마의 라이트가 다크보다 앞이다.
 * - 색은 벌마다 문서 뿌리에서 이기는 선언(`theme-css.ts`)의 값이다. hex 나 색 함수인 속성이 원색과 반투명이고, 다른
 *   색 토큰을 `var()` 로 가리키는 속성이 쓰임새 토큰이다. 길이와 글꼴 같은 다른 값의 속성(밀도, 글꼴 변수)은 내지 않는다.
 *   여덟 벌이 한 선언을 나누면 값은 문자열 하나이고(반투명), 아니면 벌마다 적는다(원색, 쓰임새 토큰). 차례는 원색,
 *   반투명, 쓰임새 토큰이고 그 안에서 CSS 의 차례다.
 * - 설명은 첫 벌(기본 테마의 라이트)에서 이기는 선언의 줄 끝 주석이다. 원색은 기본 테마 블록, 쓰임새 토큰은 라이트
 *   대응 블록, 반투명은 뿌리 블록의 줄이 된다(명세 "토큰 설명의 자리").
 * - 글자 크기는 `@theme` 의 `--text-<이름>` 과 그 `--line-height`·`--font-weight` 이고 설명은 크기 줄의 주석이다.
 *   묶음 하나가 글꼴 묶음 `sans`(첫 벌의 `--sans` 값)를 가리킨다. 글꼴 파일 목록은 내지 않는다.
 * - 간격은 `@theme` 의 `--spacing-<숫자>`(Tailwind 의 숫자 단계), 모서리는 `--radius-*` 다. 이름 있는 치수와 밀도는
 *   내지 않는다.
 * - 형식의 한도(테마 8, 색 600, 다른 계열 60)를 넘으면 `limit` 오류다.
 *
 * 명령: `build [--css <디자인 토큰 CSS>] --out <tokens.json>`. CSS 를 주지 않으면 패키지의 디자인 토큰 CSS 를 읽는다.
 * 보고는 쓴 파일의 절대 경로(`out`), 벌의 수(`themes`), 토큰의 수(`tokens`, 글자 스타일 포함), 맞대는 값(`hash`)이다.
 */

import { dirname, join } from "node:path";
import { parseArgs } from "node:util";
import { CommandError, parsedArgs, readInput, writeOutput, type ReportFields } from "./command.ts";
import { MODES, parseThemeCss, type Declaration, type Mode } from "./theme-css.ts";
import {
  comparisonHash,
  LIMITS,
  readTokens,
  serializeTokensFile,
  type ColorToken,
  type Theme,
  type Token,
  type TokenFamily,
  type TokensFile,
  type TypeStyle,
} from "./tokens-json.ts";

/**
 * 테마 키의 한국어 이름. 패키지의 테마 목록(`web/packages/ui/src/themes.ts`)과 같은 이름이고, `web/tools` 가 그 패키지에
 * 의존하지 않아 여기 적는다. 없는 키는 키를 이름으로 쓴다.
 */
const THEME_NAMES: ReadonlyMap<string, string> = new Map([
  ["nokcheong", "녹청"],
  ["guncheong", "군청"],
  ["jacho", "자초"],
  ["jjokbit", "쪽빛"],
]);

const MODE_NAMES: Readonly<Record<Mode, string>> = { light: "라이트", dark: "다크" };

const LITERAL =
  /^(?:#[0-9a-f]{3,4}|#[0-9a-f]{6}|#[0-9a-f]{8}|(?:rgb|rgba|hsl|hsla|oklch|oklab|lab|lch|color)\(.*\))$/i;
const REFERENCE = /^var\(\s*--([A-Za-z0-9][A-Za-z0-9_.-]*)\s*\)$/;
const TEXT_SIZE = /^--(text-[A-Za-z0-9_.]+(?:-[A-Za-z0-9_.]+)*)$/;
const SPACING = /^--(spacing-\d+)$/;
const RADIUS = /^--(radius-[A-Za-z0-9_.-]+)$/;

interface Bench {
  readonly theme: Theme;
  readonly winners: ReadonlyMap<string, Declaration>;
}

/** 한 벌의 색 값. 가리키는 값이면 가리키는 토큰의 이름이다. */
type ColorValue = { readonly literal: string } | { readonly reference: string };

/** 색 토큰 후보. 벌마다의 선언과 값이다. */
interface ColorCandidate {
  readonly name: string;
  readonly declarations: readonly Declaration[];
  readonly values: readonly ColorValue[];
}

function limit(what: string, count: number, cap: number): void {
  if (count > cap) {
    throw new CommandError(
      "limit",
      `${what} 수가 ${String(count)} 개로 형식의 한도 ${String(cap)} 개를 넘는다`,
    );
  }
}

function benches(css: string): {
  readonly benches: readonly Bench[];
  readonly css: ReturnType<typeof parseThemeCss>;
} {
  const parsed = parseThemeCss(css);
  if (parsed.themes.length === 0) {
    throw new CommandError("input", "디자인 토큰 CSS 에 [data-theme] 테마가 없다");
  }
  const found = parsed.themes.flatMap((key) =>
    MODES.map((mode) => ({
      theme: { id: `${key}-${mode}`, name: `${THEME_NAMES.get(key) ?? key} ${MODE_NAMES[mode]}` },
      winners: parsed.winners(key, mode),
    })),
  );
  limit("페이지 테마(테마 × 모드)", found.length, LIMITS.themes);
  return { benches: found, css: parsed };
}

/** 모든 벌에서 색이거나 다른 색 토큰을 가리키는 속성을 색 토큰 후보로 고른다. */
function colorCandidates(found: readonly Bench[]): ColorCandidate[] {
  const properties = new Set(found.flatMap((bench) => [...bench.winners.keys()]));
  const raw = [...properties].flatMap((property) => {
    const declarations = found.map((bench) => bench.winners.get(property));
    const values = declarations.map((declaration): ColorValue | undefined => {
      const value = declaration?.value ?? "";
      if (LITERAL.test(value)) {
        return { literal: value.toLowerCase() };
      }
      const reference = REFERENCE.exec(value);
      return reference === null ? undefined : { reference: reference[1] ?? "" };
    });
    if (values.every((value) => value === undefined)) {
      return [];
    }
    if (values.some((value) => value === undefined)) {
      throw new CommandError(
        "input",
        `${property} 가 어떤 벌에서는 색이고 어떤 벌에서는 선언이 없거나 색이 아니다`,
      );
    }
    return [
      {
        name: property.slice(2),
        declarations: declarations.flatMap((declaration) =>
          declaration === undefined ? [] : [declaration],
        ),
        values: values.flatMap((value) => (value === undefined ? [] : [value])),
      },
    ];
  });
  // 색 토큰을 가리키는 것만 남을 때까지 거른다(가리키는 토큰이 색이 아니면 그 후보도 색이 아니다).
  let kept = raw;
  for (;;) {
    const names = new Set(kept.map((candidate) => candidate.name));
    const next = kept.filter((candidate) =>
      candidate.values.every((value) => !("reference" in value) || names.has(value.reference)),
    );
    if (next.length === kept.length) {
      return next;
    }
    kept = next;
  }
}

function colorTokens(found: readonly Bench[]): ColorToken[] {
  const ranked = colorCandidates(found).map((candidate) => {
    const first = candidate.declarations[0];
    const shared = candidate.declarations.every((declaration) => declaration === first);
    const referencing = candidate.values.some((value) => "reference" in value);
    const rank = referencing ? 2 : shared ? 1 : 0;
    const texts = candidate.values.map((value) =>
      "reference" in value ? `{${value.reference}}` : value.literal,
    );
    const token: ColorToken = {
      name: candidate.name,
      value: shared
        ? (texts[0] ?? "")
        : Object.fromEntries(found.map((bench, index) => [bench.theme.id, texts[index] ?? ""])),
      usage: first?.comment ?? "",
    };
    return { token, rank, line: first?.line ?? 0 };
  });
  ranked.sort((left, right) => left.rank - right.rank || left.line - right.line);
  return ranked.map((entry) => entry.token);
}

function weightOf(value: string): number | string {
  return /^\d+$/.test(value) ? Number(value) : value;
}

function typeStyles(themeStatic: ReadonlyMap<string, Declaration>): TypeStyle[] {
  return [...themeStatic.values()].flatMap((declaration) => {
    const found = TEXT_SIZE.exec(declaration.property);
    if (found === null) {
      return [];
    }
    const lineHeight = themeStatic.get(`${declaration.property}--line-height`)?.value;
    const fontWeight = themeStatic.get(`${declaration.property}--font-weight`)?.value;
    return [
      {
        name: found[1] ?? "",
        fontSize: declaration.value,
        ...(lineHeight === undefined ? {} : { lineHeight }),
        ...(fontWeight === undefined ? {} : { fontWeight: weightOf(fontWeight) }),
        usage: declaration.comment,
      },
    ];
  });
}

function family(
  themeStatic: ReadonlyMap<string, Declaration>,
  pattern: RegExp,
  what: string,
): TokenFamily {
  const tokens: Token[] = [...themeStatic.values()].flatMap((declaration) => {
    const found = pattern.exec(declaration.property);
    return found === null
      ? []
      : [{ name: found[1] ?? "", value: declaration.value, usage: declaration.comment }];
  });
  limit(what, tokens.length, LIMITS.familyTokens);
  return { note: "", tokens };
}

/** 디자인 토큰 CSS 에서 tokens.json 을 짓는다. 풀 수 없으면 `input`, 한도를 넘으면 `limit` 오류다. */
export function buildTokensFile(css: string): TokensFile {
  const { benches: found, css: parsed } = benches(css);
  const color = colorTokens(found);
  limit("색 토큰", color.length, LIMITS.colors);
  const sans = found[0]?.winners.get("--sans")?.value;
  if (sans === undefined) {
    throw new CommandError("input", "디자인 토큰 CSS 의 기본 테마에 --sans 가 없다");
  }
  return {
    version: 1,
    color: { themes: found.map((bench) => bench.theme), tokens: color },
    type: {
      families: { sans },
      groups: [{ name: "글자", family: "sans", styles: typeStyles(parsed.themeStatic) }],
    },
    spacing: family(parsed.themeStatic, SPACING, "간격 토큰"),
    radius: family(parsed.themeStatic, RADIUS, "모서리 토큰"),
  };
}

/** 지은 tokens.json 의 바이트. */
export function buildTokensJson(css: string): string {
  return serializeTokensFile(buildTokensFile(css));
}

/** 패키지의 디자인 토큰 CSS. */
const DEFAULT_CSS = join(
  dirname(dirname(import.meta.dirname)),
  "packages",
  "ui",
  "src",
  "styles",
  "theme.css",
);

/** 짓기 명령. */
export function build(args: readonly string[]): ReportFields {
  const { css = DEFAULT_CSS, out } = parsedArgs(
    () =>
      parseArgs({
        args: [...args],
        options: { css: { type: "string" }, out: { type: "string" } },
        strict: true,
        allowPositionals: false,
      }).values,
  );
  if (out === undefined) {
    throw new CommandError("usage", "build 에는 --out <tokens.json> 이 있어야 한다");
  }
  const file = buildTokensFile(readInput(css));
  const tokens =
    file.color.tokens.length +
    file.type.groups.reduce((count, group) => count + group.styles.length, 0) +
    file.spacing.tokens.length +
    file.radius.tokens.length;
  return {
    out: writeOutput(out, serializeTokensFile(file)),
    themes: file.color.themes.length,
    tokens,
    hash: comparisonHash(readTokens(file)),
  };
}
