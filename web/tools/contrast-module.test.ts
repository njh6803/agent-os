// 디자인 시스템 패키지의 명암비 모듈(`@agent-os/ui/contrast`)을 `web/tools` 의 스크립트처럼 패키지 이름으로 부른다.
// 판정 스토리 Matrix 와 같은 짝 표와 같은 공식이 루트 설정(`nodenext`, `lib` es2024)의 타입 검사와 실행을 지나는지 본다
// (design-reverse-sync 명세의 "명암비 계산을 부르는 길"). 실행은 둘이다. vitest 는 Vite 의 해석으로 모듈을 풀어 `.js` 를
// 붙인 상대 import 도 이웃 `.ts` 로 풀므로, `web/tools` 의 스크립트처럼 Node 를 띄워 패키지 이름으로 부르는 사례를 따로
// 둔다. 값은 합성한다. 이 시험은 디자인 토큰 CSS 를 풀지 않는다.
import { spawnSync } from "node:child_process";
import { dirname } from "node:path";
import {
  CONTRAST_PAIRS,
  contrastFailures,
  contrastRatio,
  measureContrast,
  type SemanticToken,
} from "@agent-os/ui/contrast";
import { describe, expect, test } from "vitest";

const WEB = dirname(import.meta.dirname);
const BLACK = "#000000";
const WHITE = "#ffffff";
// 글자 쪽으로만 쓰이는 토큰. 바탕으로도 쓰이는 토큰(`accent` 는 `on-accent` 짝의 바탕이다)을 바꾸면 다른 짝도 함께 바뀐다.
const MUTED: SemanticToken = "text-muted";

// Node 가 `web/` 에서 패키지 이름으로 모듈을 들여 모두 검은 값의 짝을 판정하고 수 둘을 찍는다.
const NODE_SCRIPT = [
  'const { CONTRAST_PAIRS, contrastFailures } = await import("@agent-os/ui/contrast");',
  `const failures = contrastFailures("nokcheong", "light", () => "${BLACK}");`,
  "console.log(JSON.stringify({ pairs: CONTRAST_PAIRS.length, failures: failures.length }));",
].join("\n");

describe("패키지 이름으로 부른 명암비 모듈", () => {
  test("쓰임새 토큰을 모두 검은 값으로 주면 짝 43개가 모두 걸린다", () => {
    const failures = contrastFailures("nokcheong", "light", () => BLACK);

    expect([CONTRAST_PAIRS.length, failures.length]).toEqual([43, 43]);
  });

  test("글자로만 쓰이는 토큰 하나를 흰 값으로 바꾸면 그 토큰을 글자로 드는 짝만 걸린 목록에서 빠진다", () => {
    const allBlack = contrastFailures("nokcheong", "light", () => BLACK);
    const mutedWhite = contrastFailures("nokcheong", "light", (name) =>
      name === MUTED ? WHITE : BLACK,
    );

    expect(allBlack.filter((message) => !mutedWhite.includes(message))).toEqual([
      "nokcheong/light text-muted/bg 1.00 < 4.5",
      "nokcheong/light text-muted/bg-raised 1.00 < 4.5",
      "nokcheong/light text-muted/bg-selected+bg 1.00 < 4.5",
      "nokcheong/light text-muted/bg-hover+bg-raised 1.00 < 4.5",
      "nokcheong/light text-muted/bg-active+bg 1.00 < 3",
      "nokcheong/light text-muted/bg-active+bg-raised 1.00 < 3",
    ]);
    expect(mutedWhite).toEqual(allBlack.filter((message) => mutedWhite.includes(message)));
    expect(mutedWhite).toHaveLength(37);
  });

  test("짝마다 잰 값은 짝, 바탕 쪽의 이름, 겹친 두 색, 명암비를 들고 걸린 목록과 같은 짝을 기준 밑으로 낸다", () => {
    const value = (name: SemanticToken): string =>
      name === MUTED ? WHITE : name === "bg-selected" ? "#ffffff80" : BLACK;
    const measured = measureContrast(value, CONTRAST_PAIRS);
    const selected = measured.find(
      ({ pair, surface }) => pair[0] === MUTED && surface === "bg-selected+bg",
    );

    expect(measured).toHaveLength(43);
    expect(selected).toEqual({
      pair: [MUTED, ["bg-selected", "bg"], 4.5],
      surface: "bg-selected+bg",
      foregroundColor: WHITE,
      backgroundColor: "#808080",
      ratio: contrastRatio(WHITE, "#808080"),
    });
    expect(
      measured
        .filter(({ pair, ratio }) => ratio < pair[2])
        .map(
          ({ pair, surface, ratio }) =>
            `nokcheong/light ${pair[0]}/${surface} ${(Math.floor(ratio * 100) / 100).toFixed(2)} < ${String(pair[2])}`,
        ),
    ).toEqual(contrastFailures("nokcheong", "light", value));
  });

  test("Node 가 패키지 이름으로 모듈을 바로 불러 짝 43개를 모두 판정한다", () => {
    const run = spawnSync(process.execPath, ["--input-type=module", "--eval", NODE_SCRIPT], {
      cwd: WEB,
      encoding: "utf-8",
    });

    expect(run.status, run.stderr).toBe(0);
    expect(run.stdout.trim()).toBe('{"pairs":43,"failures":43}');
  });
});
