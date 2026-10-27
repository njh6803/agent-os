// 들이기 명령의 테스트(design-reverse-sync 명세 Testing Decisions "왕복"·"옮기기와 묻기"·"판정과 제안"). 입력은 실제
// 디자인 토큰 CSS 에서 줄 끝의 쓰임 설명(티켓 03)을 벗긴 사본과 그것으로 지은 tokens.json 이고, 사례는 그 사본을 고쳐
// 만든다. 설명 글이 바뀌어도 사례의 기대가 그대로이게 벗긴다. 설명이 달린 실제 판은 한 사례가 쓴다. 보고와 고친 디자인 토큰
// CSS 를 본다.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { check, format, resolveConfig, util } from "prettier";
import { describe, expect, test } from "vitest";
import { buildTokensFile } from "./build.ts";
import { CommandError } from "./command.ts";
import { importTokens, PRINT_WIDTH, type ImportReport } from "./import.ts";
import { diffTokens, readTokens } from "./tokens-json.ts";

const WEB = dirname(dirname(import.meta.dirname));
const CSS_PATH = join(WEB, "packages", "ui", "src", "styles", "theme.css");
const THEME_CSS = readFileSync(CSS_PATH, "utf-8");
const CSS = withoutLineComments(THEME_CSS);

const NOK = ["nokcheong-light", "nokcheong-dark"];
const ALL = [
  "nokcheong-light",
  "nokcheong-dark",
  "guncheong-light",
  "guncheong-dark",
  "jacho-light",
  "jacho-dark",
  "jjokbit-light",
  "jjokbit-dark",
];
const LIGHTS = ALL.filter((theme) => theme.endsWith("-light"));
const DARKS = ALL.filter((theme) => theme.endsWith("-dark"));
const RENAME = "이름을 바꾼 것일 수 있다";

/** 선언을 끝낸 `;` 뒤의 줄 끝 주석을 벗긴 사본(`build.test.ts` 의 같은 이름과 같다). */
function withoutLineComments(css: string): string {
  return css.replace(/;[ \t]*\/\*[^\n]*?\*\/[ \t]*$/gm, ";");
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

/** `css` 로 지은 tokens.json 의 고칠 수 있는 사본. */
function built(css = CSS): Record<string, unknown> {
  const parsed: unknown = JSON.parse(JSON.stringify(buildTokensFile(css)));
  return record(parsed);
}

/** `css` 로 지은 tokens.json 을 `edit` 이 그 자리에서 고친 것. 웹의 tokens.json 이다. */
function edited(edit: (file: Record<string, unknown>) => void, css = CSS): Record<string, unknown> {
  const file = built(css);
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
    .flatMap((group) => list(record(group).styles).map(record))
    .find((style) => style.name === name);
  if (found === undefined) {
    throw new Error(`글자 스타일 ${name} 이 없다`);
  }
  return found;
}

/** 색 토큰의 벌마다의 값을 바꾼다. 문자열 값(반투명)은 페이지처럼 첫 테마의 객체로 바꾼 뒤 고친다. */
function setColor(
  file: Record<string, unknown>,
  name: string,
  values: Record<string, string>,
): void {
  const token = tokenIn(file, "color", name);
  const current = token.value;
  const benches = typeof current === "string" ? { [ALL[0] ?? ""]: current } : record(current);
  token.value = { ...benches, ...values };
}

function both(value: string): Record<string, string> {
  return Object.fromEntries(NOK.map((theme) => [theme, value]));
}

interface Run {
  readonly css?: string;
  readonly base?: unknown;
  readonly answers?: Readonly<Record<string, string>>;
}

/** 들인다. 기준본은 주지 않으면 지금 디자인 토큰 CSS 로 지은 것(마지막으로 올린 것)이다. */
function run(web: unknown, options: Run = {}): { css: string; report: ImportReport } {
  return importTokens({
    css: options.css ?? CSS,
    base: options.base ?? built(),
    web,
    answers: options.answers ?? {},
  });
}

/** 두 CSS 에서 바뀐 줄의 [전, 후] 다. 앞뒤 공백은 뗀다. */
function changedLines(before: string, after: string): string[][] {
  const left = before.split("\n");
  const right = after.split("\n");
  if (left.length !== right.length) {
    throw new Error(`줄 수가 ${String(left.length)} 에서 ${String(right.length)} 로 바뀌었다`);
  }
  return left.flatMap((line, index) => {
    const next = right[index] ?? "";
    return line === next ? [] : [[line.trim(), next.trim()]];
  });
}

/** 설명을 벗긴 사본에서 앞뒤 공백을 뗀 것이 `line` 인 첫 줄(들여쓰기까지). */
function lineText(line: string): string {
  return CSS.split("\n")[lineOf(line) - 1] ?? "";
}

/** `line` 끝의 주석으로 붙이면 그 줄의 글자 폭(Prettier 가 재는 폭, 한글은 두 칸)이 `width` 가 되는 설명. */
function usageOfWidth(line: string, width: number): string {
  const rest = width - util.getStringWidth(`${line} /*  */`);
  return "가".repeat(Math.floor(rest / 2)) + (rest % 2 === 1 ? "a" : "");
}

/** `text` 의 줄 가운데 앞뒤 공백을 뗀 것이 `line` 인 `nth` 번째(0 부터)의 줄 번호(1 부터). */
function lineOf(line: string, nth = 0, text = CSS): number {
  const found = text
    .split("\n")
    .flatMap((candidate, index) => (candidate.trim() === line ? [index + 1] : []));
  const at = found[nth];
  if (at === undefined) {
    throw new Error(`${line} 인 ${String(nth)} 번째 줄이 없다`);
  }
  return at;
}

function ids(items: readonly { readonly id: string }[]): string[] {
  return items.map((item) => item.id);
}

function only<T>(items: readonly T[]): T {
  const [first, ...rest] = items;
  if (first === undefined || rest.length > 0) {
    throw new Error(`하나가 아니라 ${String(items.length)} 개다`);
  }
  return first;
}

function slot(token: string, themes: readonly string[]): string {
  return `color/${token}@${themes.join("+")}`;
}

function importError(web: unknown, options: Run): CommandError {
  try {
    run(web, options);
  } catch (error) {
    if (error instanceof CommandError) {
      return error;
    }
    throw error;
  }
  throw new Error(`들이기가 오류 없이 끝났다(답 ${JSON.stringify(options.answers ?? {})})`);
}

describe("셋 맞대기와 옮기기", () => {
  test("지은 tokens.json 을 그대로 들이면 옮기는 것도 묻는 것도 없고 디자인 토큰 CSS 가 바이트까지 같다", () => {
    const { css, report } = run(built());

    expect(css).toBe(CSS);
    expect(report).toEqual({
      changed: false,
      moved: [],
      asked: [],
      alreadyImported: [],
      codeOnly: [],
      contrast: { measured: 344, failures: [], suggestions: [] },
      answered: [],
    });
  });

  test("원색의 라이트·다크를 같은 값으로 바꾸면 그 테마 블록의 줄 하나로 옮기고, 다시 지으면 웹 값과 같다", () => {
    const web = edited((file) => {
      setColor(file, "accent-600", both("#04605f"));
    });
    const { css, report } = run(web);

    expect(report.moved).toEqual([
      {
        id: slot("accent-600", NOK),
        family: "color",
        token: "accent-600",
        field: "value",
        themes: NOK,
        line: lineOf("--accent-600: #056868;"),
        before: "#056868",
        after: "#04605f",
        web: "#04605f",
      },
    ]);
    expect(report.asked).toEqual([]);
    expect(report.changed).toBe(true);
    expect(changedLines(CSS, css)).toEqual([["--accent-600: #056868;", "--accent-600: #04605f;"]]);
    expect(diffTokens(readTokens(web), readTokens(buildTokensFile(css)))).toEqual([]);
  });

  test("원색 한 벌만 바꾸면 옮기지 않고 한 값을 나누는 벌 가운데 일부만 바꾼 것으로 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        setColor(file, "accent-600", { "nokcheong-light": "#04605f" });
      }),
    );

    expect(css).toBe(CSS);
    expect(report.moved).toEqual([]);
    expect(report.asked).toEqual([
      {
        id: slot("accent-600", NOK),
        reason: "partial",
        family: "color",
        token: "accent-600",
        group: null,
        field: "value",
        themes: NOK,
        changes: [{ theme: "nokcheong-light", base: "#056868", web: "#04605f", code: "#056868" }],
        choices: [],
        webReason: null,
        note: "",
      },
    ]);
  });

  test("원색의 라이트와 다크를 서로 다른 값으로 바꾸면 옮기지 않고 벌마다 다르게 바꾼 것으로 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        setColor(file, "accent-600", { "nokcheong-light": "#04605f", "nokcheong-dark": "#03504f" });
      }),
    );

    expect(css).toBe(CSS);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      [slot("accent-600", NOK), "partial"],
    ]);
  });

  // 기준본의 녹청 라이트는 이미 웹의 값이고 코드의 라이트는 기준본에서 바뀌었다. 웹이 다크만 라이트에 맞췄는데 줄로 옮기면
  // 코드가 바꾼 라이트의 몫을 되돌린다.
  test("기준본이 벌마다 다르던 자리에서 웹이 한 벌만 바꿔 두 벌을 맞추면 옮기지 않고 일부만 바꾼 것으로 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        setColor(file, "accent-600", both("#04605f"));
      }),
      {
        base: edited((file) => {
          setColor(file, "accent-600", { "nokcheong-light": "#04605f" });
        }),
      },
    );

    expect(css).toBe(CSS);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      [slot("accent-600", NOK), "partial"],
    ]);
  });

  test("반투명의 첫 테마만 바꾸면 여덟 벌이 함께 바뀌어 뿌리 블록의 줄로 옮긴다", () => {
    const web = edited((file) => {
      setColor(file, "overlay-black-4", { "nokcheong-light": "#00000008" });
    });
    const { css, report } = run(web);

    expect(report.moved).toMatchObject([
      { id: slot("overlay-black-4", ALL), themes: ALL, before: "#0000000a", after: "#00000008" },
    ]);
    expect(changedLines(CSS, css)).toEqual([
      ["--overlay-black-4: #0000000a;", "--overlay-black-4: #00000008;"],
    ]);
    expect(diffTokens(readTokens(web), readTokens(buildTokensFile(css)))).toEqual([]);
  });

  test("반투명의 일부 벌만 바꾸면 옮기지 않고 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        setColor(file, "overlay-black-4", { "jacho-dark": "#00000008" });
      }),
    );

    expect(css).toBe(CSS);
    expect(report.asked).toMatchObject([
      {
        id: slot("overlay-black-4", ALL),
        reason: "partial",
        changes: [{ theme: "jacho-dark", base: "#0000000a", web: "#00000008", code: "#0000000a" }],
      },
    ]);
  });

  test("간격과 모서리는 px 와 단위 없는 수(px 로 읽는다)와 0 을 옮기고 rem·% 는 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        tokenIn(file, "spacing", "spacing-0").value = 0;
        tokenIn(file, "spacing", "spacing-4").value = "20px";
        tokenIn(file, "radius", "radius-s").value = 6;
        tokenIn(file, "radius", "radius-m").value = "0.5rem";
        tokenIn(file, "radius", "radius-l").value = "50%";
      }),
    );

    expect(report.moved.map(({ id, before, after }) => [id, before, after])).toEqual([
      ["spacing/spacing-0", "0px", "0"],
      ["spacing/spacing-4", "16px", "20px"],
      ["radius/radius-s", "4px", "6px"],
    ]);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      ["radius/radius-l", "unit"],
      ["radius/radius-m", "unit"],
    ]);
    expect(changedLines(CSS, css)).toEqual([
      ["--spacing-0: 0px;", "--spacing-0: 0;"],
      ["--spacing-4: 16px;", "--spacing-4: 20px;"],
      ["--radius-s: 4px;", "--radius-s: 6px;"],
    ]);
  });

  test("소수 끝에 0 이 붙은 px 는 Prettier 가 고쳐 쓰므로 옮기지 않고 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        tokenIn(file, "spacing", "spacing-2").value = "20.50px";
        tokenIn(file, "spacing", "spacing-3").value = "20.0px";
        tokenIn(file, "radius", "radius-s").value = "4.5px";
      }),
    );

    expect(report.moved.map(({ id, after }) => [id, after])).toEqual([
      ["radius/radius-s", "4.5px"],
    ]);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      ["spacing/spacing-2", "unit"],
      ["spacing/spacing-3", "unit"],
    ]);
    expect(changedLines(CSS, css)).toEqual([["--radius-s: 4px;", "--radius-s: 4.5px;"]]);
  });

  test("글자 스타일의 크기·줄 높이·굵기는 그 줄로 옮기고, 단위 없는 줄 높이와 굵기 범위는 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        styleIn(file, "text-title").fontSize = "26px";
        styleIn(file, "text-title").lineHeight = 1.5;
        styleIn(file, "text-small").fontWeight = 500;
        styleIn(file, "text-badge").lineHeight = "18px";
        styleIn(file, "text-badge").fontWeight = "300 800";
      }),
    );

    expect(report.moved.map(({ id, before, after }) => [id, before, after])).toEqual([
      ["type/text-badge#lineHeight", "16px", "18px"],
      ["type/text-small#fontWeight", "400", "500"],
      ["type/text-title#fontSize", "24px", "26px"],
    ]);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      ["type/text-badge#fontWeight", "weightRange"],
      ["type/text-title#lineHeight", "unit"],
    ]);
    expect(changedLines(CSS, css)).toEqual([
      ["--text-title: 24px;", "--text-title: 26px;"],
      ["--text-small--font-weight: 400;", "--text-small--font-weight: 500;"],
      ["--text-badge--line-height: 16px;", "--text-badge--line-height: 18px;"],
    ]);
  });

  test("oklch()·hsl()·rgb()·3 자리 hex 는 hex 로 바꿔 옮기고 웹의 값과 바꾼 값을 보고에 함께 적는다", () => {
    const web = edited((file) => {
      setColor(file, "danger-500", both("oklch(0.627955 0.257683 29.2339)"));
      setColor(file, "accent-500", both("hsl(180 100% 20%)"));
      setColor(file, "info-500", both("rgb(255 128 0)"));
      setColor(file, "gray-300", both("#ABC"));
    });
    const { css, report } = run(web);

    expect(report.moved.map(({ token, web: value, after }) => [token, value, after])).toEqual([
      ["accent-500", "hsl(180 100% 20%)", "#006666"],
      ["danger-500", "oklch(0.627955 0.257683 29.2339)", "#ff0000"],
      ["gray-300", "#abc", "#aabbcc"],
      ["info-500", "rgb(255 128 0)", "#ff8000"],
    ]);
    expect(report.asked).toEqual([]);
    expect(changedLines(CSS, css)).toEqual([
      ["--gray-300: #9b9fa1;", "--gray-300: #aabbcc;"],
      ["--accent-500: #2d8a8a;", "--accent-500: #006666;"],
      ["--danger-500: #d33b36;", "--danger-500: #ff0000;"],
      ["--info-500: #337bd0;", "--info-500: #ff8000;"],
    ]);
  });

  test("sRGB 밖의 값, lab()·color(), 읽지 못하는 색 함수는 옮기지 않고 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        setColor(file, "accent-500", both("oklch(0.7 0.4 30)"));
        setColor(file, "danger-500", both("lab(50% 40 59)"));
        setColor(file, "info-500", both("color(display-p3 1 0 0)"));
        setColor(file, "warning-500", both("rgb(1 2)"));
      }),
    );

    expect(css).toBe(CSS);
    expect(report.asked.map(({ token, reason }) => [token, reason])).toEqual([
      ["accent-500", "outOfGamut"],
      ["danger-500", "colorSpace"],
      ["info-500", "colorSpace"],
      ["warning-500", "unreadableColor"],
    ]);
  });

  test("불투명한 쓰임새 토큰이 가리키는 원색에 투명도를 주면 묻고, 반투명 쓰임새 토큰만 가리키는 원색은 옮긴다", () => {
    const { report } = run(
      edited((file) => {
        setColor(file, "gray-100", both("#ecf1f380"));
        setColor(file, "overlay-black-7", { "nokcheong-light": "#00000014" });
      }),
    );

    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      [slot("gray-100", NOK), "alpha"],
    ]);
    expect(ids(report.moved)).toEqual([slot("overlay-black-7", ALL)]);
  });

  test("원색과 반투명을 다른 토큰을 가리키는 별칭으로 바꾸면 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        setColor(file, "accent-500", both("{accent-600}"));
        setColor(file, "overlay-black-4", { "nokcheong-light": "{overlay-black-7}" });
      }),
    );

    expect(css).toBe(CSS);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      [slot("accent-500", NOK), "alias"],
      [slot("overlay-black-4", ALL), "alias"],
    ]);
  });

  test("쓰임새 토큰이 가리키는 원색을 바꾸면 별칭이든 별칭이 아닌 값이든 대응 바꾸기로 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        setColor(file, "text", { "nokcheong-light": "{gray-800}" });
        setColor(file, "bg", { "guncheong-dark": "#000000" });
      }),
    );

    expect(css).toBe(CSS);
    expect(report.asked).toMatchObject([
      {
        id: slot("bg", DARKS),
        reason: "mapping",
        changes: [{ theme: "guncheong-dark", base: "{gray-950}", web: "#000000" }],
      },
      {
        id: slot("text", LIGHTS),
        reason: "mapping",
        changes: [{ theme: "nokcheong-light", base: "{gray-900}", web: "{gray-800}" }],
      },
    ]);
  });

  test("토큰을 더하거나 지우면 묻고, 한 계열에서 함께 나오면 이름을 바꾼 것일 수 있다고 적는다", () => {
    const { css, report } = run(
      edited((file) => {
        const color = record(file.color);
        color.tokens = [...list(color.tokens), { name: "new-1", value: "#123456", usage: "" }];
        const spacing = record(file.spacing);
        spacing.tokens = list(spacing.tokens).filter((token) => record(token).name !== "spacing-8");
        const radius = record(file.radius);
        radius.tokens = list(radius.tokens).map((token) =>
          record(token).name === "radius-l" ? { ...record(token), name: "radius-xl" } : token,
        );
      }),
    );

    expect(css).toBe(CSS);
    expect(report.asked.map(({ id, reason, note }) => [id, reason, note])).toEqual([
      ["color/new-1", "added", ""],
      ["spacing/spacing-8", "removed", ""],
      ["radius/radius-l", "removed", RENAME],
      ["radius/radius-xl", "added", RENAME],
    ]);
  });

  test("글자 스타일의 다른 칸(자간), 계열 설명, 새 계열은 옮기지 않고 그 종류로 묻는다", () => {
    const { css, report } = run(
      edited((file) => {
        styleIn(file, "text-title").letterSpacing = "1px";
        record(file.spacing).note = "간격";
        file.shadow = { note: "", tokens: [{ name: "shadow-1", value: "0 1px 2px #000" }] };
      }),
    );

    expect(css).toBe(CSS);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      ["type/text-title#letterSpacing", "typeField"],
      ["spacing#note", "familyNote"],
      ["shadow", "added"],
    ]);
  });

  test("셋 맞대기는 웹만, 코드만, 둘 다 같게, 둘 다 다르게 바뀐 것을 네 갈래로 가른다", () => {
    const code = CSS.replace("--gray-50: #f4f8fb;", "--gray-50: #f0f0f0;")
      .replace("--gray-200: #e1e5e8;", "--gray-200: #dddddd;")
      .replace("--gray-300: #9b9fa1;", "--gray-300: #999999;");
    const web = edited((file) => {
      setColor(file, "gray-400", both("#888888"));
      setColor(file, "gray-200", both("#dddddd"));
      setColor(file, "gray-300", both("#aaaaaa"));
    });
    const { css, report } = run(web, { css: code });

    expect(ids(report.moved)).toEqual([slot("gray-400", NOK)]);
    expect(report.asked).toEqual([
      {
        id: slot("gray-300", NOK),
        reason: "conflict",
        family: "color",
        token: "gray-300",
        group: null,
        field: "value",
        themes: NOK,
        changes: NOK.map((theme) => ({ theme, base: "#9b9fa1", web: "#aaaaaa", code: "#999999" })),
        choices: ["web", "code"],
        webReason: null,
        note: "",
      },
    ]);
    expect(report.alreadyImported.map(({ token, theme }) => [token, theme])).toEqual(
      NOK.map((theme) => ["gray-200", theme]),
    );
    expect(report.codeOnly.map(({ token, theme }) => [token, theme])).toEqual(
      NOK.map((theme) => ["gray-50", theme]),
    );
    expect(changedLines(code, css)).toEqual([["--gray-400: #898d8f;", "--gray-400: #888888;"]]);
  });

  test("둘 다 다르게 바뀌었는데 웹 값을 옮길 수 없으면 코드 값만 고를 수 있고 옮기지 못하는 까닭을 함께 낸다", () => {
    const code = CSS.replace("--gray-300: #9b9fa1;", "--gray-300: #999999;");
    const web = edited((file) => {
      setColor(file, "gray-300", both("oklch(0.7 0.4 30)"));
    });
    const { report } = run(web, { css: code });
    const answered = run(web, { css: code, answers: { [slot("gray-300", NOK)]: "code" } });

    expect(report.asked).toMatchObject([
      {
        id: slot("gray-300", NOK),
        reason: "conflict",
        choices: ["code"],
        webReason: "outOfGamut",
      },
    ]);
    expect(answered.report.asked).toEqual([]);
    expect(answered.css).toBe(code);
    expect(
      importError(web, { css: code, answers: { [slot("gray-300", NOK)]: "web" } }).message,
    ).toContain("web 는 고를 수 없다");
  });

  test("대응 바꾸기를 코드와 웹이 다르게 바꾸면 대응 바꾸기를 옮기지 못하는 까닭으로 낸다", () => {
    const code = CSS.replace("--text: var(--gray-900);", "--text: var(--gray-800);");
    const { css, report } = run(
      edited((file) => {
        setColor(file, "text", Object.fromEntries(LIGHTS.map((theme) => [theme, "{gray-700}"])));
      }),
      { css: code },
    );

    expect(css).toBe(code);
    expect(report.asked).toMatchObject([
      { id: slot("text", LIGHTS), reason: "conflict", choices: ["code"], webReason: "mapping" },
    ]);
  });

  test("설명 고침은 그 토큰을 선언한 줄 끝의 주석으로 옮기고 보고에 전과 후를 낸다", () => {
    const web = edited((file) => {
      tokenIn(file, "color", "gray-900").usage = "본문 글자의 원색";
      tokenIn(file, "color", "bg").usage = "화면 바탕";
      tokenIn(file, "spacing", "spacing-4").usage = "기본 간격";
      styleIn(file, "text-title").usage = "제목 글자";
    });
    const { css, report } = run(web);

    expect(report.moved.map(({ id, field, before, after }) => [id, field, before, after])).toEqual([
      ["color/bg#usage", "usage", "", "화면 바탕"],
      ["color/gray-900#usage", "usage", "", "본문 글자의 원색"],
      ["type/text-title#usage", "usage", "", "제목 글자"],
      ["spacing/spacing-4#usage", "usage", "", "기본 간격"],
    ]);
    expect(changedLines(CSS, css)).toEqual([
      ["--text-title: 24px;", "--text-title: 24px; /* 제목 글자 */"],
      ["--spacing-4: 16px;", "--spacing-4: 16px; /* 기본 간격 */"],
      ["--gray-900: #171a1c;", "--gray-900: #171a1c; /* 본문 글자의 원색 */"],
      ["--bg: var(--gray-50);", "--bg: var(--gray-50); /* 화면 바탕 */"],
    ]);
    expect(diffTokens(readTokens(web), readTokens(buildTokensFile(css)))).toEqual([]);
  });

  test("웹에서 설명을 비우면 그 줄 끝의 주석을 지운다", () => {
    const code = CSS.replace("--radius-m: 8px;", "--radius-m: 8px; /* 옛 설명 */");
    const web = edited((file) => {
      tokenIn(file, "radius", "radius-m").usage = "";
    }, code);
    const { css, report } = run(web, { css: code, base: built(code) });

    expect(report.moved.map(({ id, before, after }) => [id, before, after])).toEqual([
      ["radius/radius-m#usage", "옛 설명", ""],
    ]);
    expect(changedLines(code, css)).toEqual([
      ["--radius-m: 8px; /* 옛 설명 */", "--radius-m: 8px;"],
    ]);
  });

  test("주석을 끝내는 글자나 줄바꿈이나 앞뒤 공백이 든 설명은 그 토큰만 묻고 다른 설명은 옮긴다", () => {
    const { report } = run(
      edited((file) => {
        tokenIn(file, "color", "gray-900").usage = "끝 */ 표지";
        tokenIn(file, "color", "gray-800").usage = "줄\n바꿈";
        tokenIn(file, "color", "gray-700").usage = " 앞 공백";
        tokenIn(file, "color", "gray-600").usage = "괜찮은 설명";
      }),
    );

    expect(ids(report.moved)).toEqual(["color/gray-600#usage"]);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      ["color/gray-700#usage", "usageText"],
      ["color/gray-800#usage", "usageText"],
      ["color/gray-900#usage", "usageText"],
    ]);
  });

  test("여러 줄에 걸친 선언과 한 줄의 여러 선언은 옮기지 않고 옮길 줄이 없다고 묻는다", () => {
    const code = CSS.replace("    --gray-0: #ffffff;", "    --gray-0:\n      #ffffff;")
      .replace(
        "    --gray-50: #f4f8fb;\n    --gray-100: #ecf1f3;",
        "    --gray-50: #f4f8fb; --gray-100: #ecf1f3;",
      )
      .replace("--gray-200: #e1e5e8;", "--gray-200: #e1e5e8; /* 하나 */ /* 둘 */");
    const { css, report } = run(
      edited((file) => {
        setColor(file, "gray-0", both("#fefefe"));
        setColor(file, "gray-50", both("#f0f4f7"));
        setColor(file, "gray-200", both("#dddddd"));
      }),
      { css: code },
    );

    expect(css).toBe(code);
    expect(report.asked.map(({ token, reason }) => [token, reason])).toEqual([
      ["gray-0", "noLine"],
      ["gray-200", "noLine"],
      ["gray-50", "noLine"],
    ]);
  });

  test("줄 끝이 CRLF 인 디자인 토큰 CSS 는 고친 줄도 CRLF 로 끝난다", () => {
    const code = CSS.replaceAll("\n", "\r\n");
    const { css, report } = run(
      edited((file) => {
        setColor(file, "accent-600", both("#04605f"));
        tokenIn(file, "spacing", "spacing-4").usage = "기본 간격";
      }),
      { css: code },
    );

    expect(ids(report.moved)).toEqual([slot("accent-600", NOK), "spacing/spacing-4#usage"]);
    expect(css).toBe(
      code
        .replace("--accent-600: #056868;\r", "--accent-600: #04605f;\r")
        .replace("--spacing-4: 16px;\r", "--spacing-4: 16px; /* 기본 간격 */\r"),
    );
  });

  test("설명이 달린 실제 디자인 토큰 CSS 에서 값만 옮기면 그 줄 끝의 설명은 그대로 남는다", () => {
    const usage =
      buildTokensFile(THEME_CSS).color.tokens.find((token) => token.name === "accent-600")?.usage ??
      "";
    const { css } = run(
      edited((file) => {
        setColor(file, "accent-600", both("#04605f"));
      }, THEME_CSS),
      { css: THEME_CSS, base: built(THEME_CSS) },
    );

    expect(usage).not.toBe("");
    expect(changedLines(THEME_CSS, css)).toEqual([
      [`--accent-600: #056868; /* ${usage} */`, `--accent-600: #04605f; /* ${usage} */`],
    ]);
  });

  test("고친 디자인 토큰 CSS 가 Prettier 의 포맷 검사를 지난다", async () => {
    const options = { ...(await resolveConfig(CSS_PATH)), filepath: CSS_PATH };
    const { css, report } = run(
      edited((file) => {
        setColor(file, "accent-600", both("oklch(0.45 0.04 195)"));
        tokenIn(file, "color", "accent-600").usage =
          "강조 글자와 포커스 링이 가리키는 녹청 라이트의 원색".repeat(3);
        tokenIn(file, "color", "overlay-black-4").usage = "올림";
        tokenIn(file, "spacing", "spacing-2").value = "10px";
        styleIn(file, "text-small").usage = "작은 글자";
      }),
    );

    expect(report.asked).toEqual([]);
    expect(report.moved).toHaveLength(5);
    expect(await check(CSS, options)).toBe(true);
    expect(await check(css.replace("--gray-0: #ffffff;", "--gray-0:#ffffff;"), options)).toBe(
      false,
    );
    expect(await check(css, options)).toBe(true);
  });

  test("쓰임새 토큰의 줄을 Prettier 의 폭보다 넓게 만드는 설명은 그 토큰만 묻고, 폭에 맞는 설명과 원색 줄의 긴 설명은 옮긴다", async () => {
    const options = { ...(await resolveConfig(CSS_PATH)), filepath: CSS_PATH };
    const bg = lineText("--bg: var(--gray-50);");
    const raised = lineText("--bg-raised: var(--gray-0);");
    const fits = usageOfWidth(bg, PRINT_WIDTH);
    const over = usageOfWidth(raised, PRINT_WIDTH + 1);
    const { css, report } = run(
      edited((file) => {
        tokenIn(file, "color", "bg").usage = fits;
        tokenIn(file, "color", "bg-raised").usage = over;
        tokenIn(file, "color", "gray-900").usage = "본문 글자의 원색".repeat(10);
      }),
    );

    expect(options.printWidth).toBe(PRINT_WIDTH);
    expect(util.getStringWidth(`${bg} /* ${fits} */`)).toBe(PRINT_WIDTH);
    expect(ids(report.moved)).toEqual(["color/bg#usage", "color/gray-900#usage"]);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      ["color/bg-raised#usage", "lineWidth"],
    ]);
    expect(await check(css, options)).toBe(true);
    expect(await check(css.replace(raised, `${raised} /* ${over} */`), options)).toBe(false);
  });

  test("설명이 달린 실제 디자인 토큰 CSS 에서 설명을 다른 설명으로 바꾸면 옛 설명을 갈아 쓴다", async () => {
    const options = { ...(await resolveConfig(CSS_PATH)), filepath: CSS_PATH };
    const tokens = buildTokensFile(THEME_CSS).color.tokens;
    const old = (name: string): string => tokens.find((token) => token.name === name)?.usage ?? "";
    const web = edited((file) => {
      tokenIn(file, "color", "accent-600").usage = "강조 글자의 원색";
      tokenIn(file, "color", "bg").usage = "문서의 바탕";
      tokenIn(file, "color", "bg-raised").usage = "올라온 면의 바탕".repeat(8);
    }, THEME_CSS);
    const { css, report } = run(web, { css: THEME_CSS, base: built(THEME_CSS) });

    expect([old("accent-600"), old("bg")]).not.toContain("");
    expect(report.moved.map(({ id, before, after }) => [id, before, after])).toEqual([
      ["color/accent-600#usage", old("accent-600"), "강조 글자의 원색"],
      ["color/bg#usage", old("bg"), "문서의 바탕"],
    ]);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      ["color/bg-raised#usage", "lineWidth"],
    ]);
    expect(changedLines(THEME_CSS, css)).toEqual([
      [
        `--accent-600: #056868; /* ${old("accent-600")} */`,
        "--accent-600: #056868; /* 강조 글자의 원색 */",
      ],
      [`--bg: var(--gray-50); /* ${old("bg")} */`, "--bg: var(--gray-50); /* 문서의 바탕 */"],
    ]);
    expect(
      diffTokens(readTokens(web), readTokens(buildTokensFile(css))).map(({ kind, token }) => [
        kind,
        token,
      ]),
    ).toEqual([["usage", "bg-raised"]]);
    expect(await check(css, options)).toBe(true);
  });

  test("Prettier 가 세 줄로 쪼갠 쓰임새 토큰의 선언은 설명을 고쳐도 옮기지 않고 옮길 줄이 없다고 묻는다", async () => {
    const options = { ...(await resolveConfig(CSS_PATH)), filepath: CSS_PATH };
    const bg = lineText("--bg: var(--gray-50);");
    const code = await format(
      CSS.replace(bg, `${bg} /* ${usageOfWidth(bg, PRINT_WIDTH + 1)} */`),
      options,
    );
    const { css, report } = run(
      edited((file) => {
        tokenIn(file, "color", "bg").usage = "문서의 바탕";
      }, code),
      { css: code, base: built(code) },
    );

    expect(code).toContain("--bg: var(\n");
    expect(css).toBe(code);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      ["color/bg#usage", "noLine"],
    ]);
  });
});

describe("판정과 제안", () => {
  const START = "oklch(0.3 0.01 220)";
  const GRAY_100 = slot("gray-100", NOK);

  function darkText(value: string): ImportReport {
    return run(
      edited((file) => {
        setColor(file, "gray-100", both(value));
      }),
    ).report;
  }

  test("녹청 다크의 글자 원색을 바탕에 가깝게 바꾸면 걸린 짝과 그 원색의 가장 가까운 통과 값을 낸다", () => {
    const report = darkText(START);
    const moved = only(report.moved);

    expect(moved.id).toBe(GRAY_100);
    expect(
      report.contrast.failures.map(
        ({ theme, foreground, surface }) => `${theme} ${foreground}/${surface}`,
      ),
    ).toContain("nokcheong-dark text/bg");
    expect(
      report.contrast.failures.filter(
        ({ theme, ratio, minimum, tokens }) =>
          theme !== "nokcheong-dark" || ratio >= minimum || !tokens.includes(GRAY_100),
      ),
    ).toEqual([]);
    const suggestion = only(report.contrast.suggestions);
    expect(suggestion).toMatchObject({
      id: GRAY_100,
      token: "gray-100",
      themes: NOK,
      from: moved.after,
      by: "lightness",
    });
    expect(suggestion.steps).toBeGreaterThan(0);
    expect(suggestion.value).toMatch(/^#[0-9a-f]{6}$/);
  });

  test("제안 값으로 다시 들이면 걸린 짝이 없고, 제안 값에서 밝기를 0.001 덜 옮긴 값은 걸린다", () => {
    const suggestion = only(darkText(START).contrast.suggestions);
    const steps = suggestion.steps ?? 0;
    const less = 0.3 + (steps - 1) * 0.001;

    expect(darkText(suggestion.value ?? "").contrast.failures).toEqual([]);
    expect(darkText(`oklch(${String(less)} 0.01 220)`).contrast.failures).not.toEqual([]);
  });

  test("투명도가 있는 원색은 색을 두고 투명도를 1/255 씩 옮긴 값을 낸다", () => {
    const overlay = (value: string): ImportReport =>
      run(
        edited((file) => {
          setColor(file, "overlay-white-16", { "nokcheong-light": value });
        }),
      ).report;
    const report = overlay("#ffffffcc");
    const suggestion = only(report.contrast.suggestions);
    const steps = suggestion.steps ?? 0;
    const alpha = (step: number): string => `#ffffff${(0xcc + step).toString(16).padStart(2, "0")}`;

    expect(report.contrast.failures.map(({ theme }) => theme)).toContain("nokcheong-dark");
    expect(suggestion).toMatchObject({ id: slot("overlay-white-16", ALL), by: "alpha" });
    expect(steps).toBeLessThan(0);
    expect(suggestion.value).toBe(alpha(steps));
    expect(overlay(alpha(steps)).contrast.failures).toEqual([]);
    expect(overlay(alpha(steps + 1)).contrast.failures).not.toEqual([]);
  });

  // 다크의 글자(gray-100)와 바탕(gray-950)을 함께 #808080 으로 두면, 글자는 밝히면 바탕에, 어둡히면 올린 바탕(gray-900)에
  // 걸린다. 바탕도 밝히면 글자에, 어둡히면 위에 겹친 선택 바탕(흰색 10%)이 글자와 4.41 에 머문다.
  test("밝기를 0 에서 1 까지 옮겨도 통과하는 값이 없으면 제안 값이 없다고 낸다", () => {
    const { report } = run(
      edited((file) => {
        setColor(file, "gray-100", both("#808080"));
        setColor(file, "gray-950", both("#808080"));
      }),
    );

    expect(report.contrast.failures).not.toEqual([]);
    expect(report.contrast.suggestions).toEqual([
      {
        id: GRAY_100,
        token: "gray-100",
        themes: NOK,
        from: "#808080",
        by: "lightness",
        steps: null,
        value: null,
      },
      {
        id: slot("gray-950", NOK),
        token: "gray-950",
        themes: NOK,
        from: "#808080",
        by: "lightness",
        steps: null,
        value: null,
      },
    ]);
  });
});

describe("사람이 고른 답", () => {
  const code = CSS.replace("--gray-300: #9b9fa1;", "--gray-300: #999999;").replace(
    "--gray-200: #e1e5e8;",
    "--gray-200: #dddddd;",
  );
  const web = edited((file) => {
    setColor(file, "gray-300", both("#aaaaaa"));
    setColor(file, "gray-200", both("#cccccc"));
    setColor(file, "gray-100", both("oklch(0.3 0.01 220)"));
  });

  test("답을 주면 웹 값과 제안 값으로 옮기고 코드 값을 고른 토큰은 그대로 두며, 같은 입력과 답에는 같은 결과다", () => {
    const first = run(web, { css: code });
    const suggestion = only(first.report.contrast.suggestions);
    const answers = {
      [slot("gray-300", NOK)]: "web",
      [slot("gray-200", NOK)]: "code",
      [slot("gray-100", NOK)]: "suggested",
    };
    const answered = run(web, { css: code, answers });

    expect(first.report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      [slot("gray-200", NOK), "conflict"],
      [slot("gray-300", NOK), "conflict"],
    ]);
    expect(answered.report.moved.map(({ token, after }) => [token, after])).toEqual([
      ["gray-100", suggestion.value],
      ["gray-300", "#aaaaaa"],
    ]);
    expect(answered.report.asked).toEqual([]);
    expect(answered.report.contrast.failures).toEqual([]);
    expect(answered.report.answered).toEqual([
      { id: slot("gray-100", NOK), choice: "suggested", value: suggestion.value },
      { id: slot("gray-200", NOK), choice: "code", value: "#dddddd" },
      { id: slot("gray-300", NOK), choice: "web", value: "#aaaaaa" },
    ]);
    expect(changedLines(code, answered.css)).toEqual([
      ["--gray-100: #ecf1f3;", `--gray-100: ${suggestion.value ?? ""};`],
      ["--gray-300: #999999;", "--gray-300: #aaaaaa;"],
    ]);
    expect(run(web, { css: code, answers })).toEqual(answered);
  });

  test("제안이 난 자리에서 코드 값을 고르면 옮기지 않고, 걸린 웹 값은 고를 수 없다", () => {
    const gray100 = slot("gray-100", NOK);
    const conflicts = { [slot("gray-300", NOK)]: "code", [slot("gray-200", NOK)]: "code" };
    const kept = run(web, { css: code, answers: { ...conflicts, [gray100]: "code" } });
    const forced = importError(web, { css: code, answers: { ...conflicts, [gray100]: "web" } });

    expect(kept.report.moved).toEqual([]);
    expect(kept.css).toBe(code);
    expect(kept.report.contrast).toEqual({ measured: 344, failures: [], suggestions: [] });
    expect(kept.report.answered.find(({ id }) => id === gray100)).toEqual({
      id: gray100,
      choice: "code",
      value: "#ecf1f3",
    });
    expect(forced.kind).toBe("input");
    expect(forced.message).toContain(`${gray100} 에서 web 는 고를 수 없다`);
  });

  test("둘 다 다르게 바뀐 자리도 웹 값을 골라 명암비에 걸리면 제안 값을 고를 수 있다", () => {
    const gray100 = slot("gray-100", NOK);
    const both100 = code.replace("--gray-100: #ecf1f3;", "--gray-100: #eeeeee;");
    const conflicts = { [slot("gray-300", NOK)]: "code", [slot("gray-200", NOK)]: "code" };
    const first = run(web, { css: both100, answers: conflicts });
    const picked = run(web, { css: both100, answers: { ...conflicts, [gray100]: "web" } });
    const suggestion = only(picked.report.contrast.suggestions);
    const answered = run(web, {
      css: both100,
      answers: { ...conflicts, [gray100]: "suggested" },
    });

    expect(first.report.asked).toMatchObject([
      { id: gray100, reason: "conflict", choices: ["web", "code"] },
    ]);
    expect(picked.report.contrast.failures).not.toEqual([]);
    expect(suggestion).toMatchObject({ id: gray100, by: "lightness" });
    expect(answered.report.moved.map(({ token, after }) => [token, after])).toEqual([
      ["gray-100", suggestion.value],
    ]);
    expect(answered.report.contrast.failures).toEqual([]);
    expect(answered.report.answered.find(({ id }) => id === gray100)).toEqual({
      id: gray100,
      choice: "suggested",
      value: suggestion.value,
    });
  });

  test("답이 이번 들이기에 없는 자리를 가리키거나 그 자리에서 고를 수 없는 답이면 입력 오류다", () => {
    const unknown = importError(web, { css: code, answers: { "color/none@x": "web" } });
    const unchoosable = importError(web, {
      css: code,
      answers: { [slot("gray-300", NOK)]: "suggested" },
    });

    expect(unknown.kind).toBe("input");
    expect(unknown.message).toContain("color/none@x");
    expect(unchoosable.kind).toBe("input");
    expect(unchoosable.message).toContain("suggested 는 고를 수 없다");
    expect(
      importError(web, { css: code, answers: { [slot("gray-300", NOK)]: "maybe" } }).message,
    ).toContain("maybe 는 고를 수 없다");
  });
});

describe("이어받는 기준본", () => {
  // 앞 들이기의 claim 사본(그때의 웹)은 gray-500·gray-600·gray-700·gray-800 을 바꿨다. 사람은 gray-500 에 "코드 값"을
  // 골랐고 나머지 셋을 들여 병합했다(code). 열린 PR 동안 "덮어쓴다"가 웹의 gray-800 을 옛 코드 값으로 되돌렸고, 그 뒤 웹은
  // gray-600 을 더 고쳤다. 이어받는 기준본은 지금 웹에서 더 고친 몫(gray-600)만 claim 사본의 값으로 바꾼 것이다(명세
  // "병합됐으면"의 2026-10-22 주석의 셋째).
  const claim = edited((file) => {
    setColor(file, "gray-500", both("#555555"));
    setColor(file, "gray-600", both("#444444"));
    setColor(file, "gray-700", both("#333333"));
    setColor(file, "gray-800", both("#222222"));
  });
  const code = CSS.replace("--gray-600: #4f5355;", "--gray-600: #444444;")
    .replace("--gray-700: #3d4042;", "--gray-700: #333333;")
    .replace("--gray-800: #2b2e30;", "--gray-800: #222222;");
  const web = edited((file) => {
    setColor(file, "gray-500", both("#555555"));
    setColor(file, "gray-600", both("#4a4a4a"));
    setColor(file, "gray-700", both("#333333"));
  });
  const inherited = edited((file) => {
    setColor(file, "gray-500", both("#555555"));
    setColor(file, "gray-600", both("#444444"));
    setColor(file, "gray-700", both("#333333"));
  });

  test("코드 값을 고른 토큰과 되돌린 토큰은 코드만 바뀐 것이라 들어오지 않고 더 고친 몫만 들어온다", () => {
    const { css, report } = run(web, { css: code, base: inherited });

    expect(ids(report.moved)).toEqual([slot("gray-600", NOK)]);
    expect(report.asked).toEqual([]);
    expect(report.alreadyImported).toEqual([]);
    expect(report.codeOnly.map(({ token, theme }) => [token, theme])).toEqual([
      ...NOK.map((theme) => ["gray-500", theme]),
      ...NOK.map((theme) => ["gray-800", theme]),
    ]);
    expect(changedLines(code, css)).toEqual([["--gray-600: #444444;", "--gray-600: #4a4a4a;"]]);
  });

  test("기록의 기준본을 주면 코드 값을 고른 토큰이 다시 웹 편집으로 들어온다", () => {
    const { report } = run(web, { css: code });

    expect(ids(report.moved)).toEqual([slot("gray-500", NOK)]);
    expect(report.asked.map(({ id, reason }) => [id, reason])).toEqual([
      [slot("gray-600", NOK), "conflict"],
    ]);
  });

  test("claim 사본을 기준본으로 주면 덮어써 되돌린 토큰이 웹 편집으로 들어와 병합한 값을 되돌린다", () => {
    const { report } = run(web, { css: code, base: claim });

    expect(report.moved.map(({ token, after }) => [token, after])).toEqual([
      ["gray-600", "#4a4a4a"],
      ["gray-800", "#2b2e30"],
    ]);
  });
});

describe("판정하지 못하는 코드", () => {
  test.each([
    [
      "불투명해야 할 바탕에 반투명이 온다",
      CSS.replace("--gray-100: #ecf1f3;", "--gray-100: #ecf1f380;"),
      "nokcheong-dark 의 명암비를 잴 수 없다",
    ],
    [
      "쓰임새 토큰이 없다",
      CSS.replace(/^\s*--bg-raised: var\(--gray-\d+\);\n/gm, ""),
      "bg-raised 를 풀 수 없다: bg-raised 가 없다",
    ],
    [
      "별칭이 돈다",
      CSS.replace("--text: var(--gray-900);", "--text: var(--text-muted);").replace(
        "--text-muted: var(--gray-500);",
        "--text-muted: var(--text);",
      ),
      "text 를 푸는 별칭이 32 번을 넘게 이어진다",
    ],
    [
      "원색을 sRGB 의 hex 로 읽지 못한다",
      CSS.replace("--gray-0: #ffffff;", "--gray-0: lab(100% 0 0);"),
      "gray-0 값 lab(100% 0 0) 를 sRGB 의 hex 로 읽을 수 없어",
    ],
  ])("%s 면 판정하지 못해 입력 오류다", (_, code, message) => {
    const error = importError(built(), { css: code });

    expect(error.kind).toBe("input");
    expect(error.message).toContain(message);
  });
});
