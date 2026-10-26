// 사진 비교 흔들림 프로브(harness 티켓 016)의 첫 갈래: CI 의 visual 잡이 실패하며 올린 아티팩트(visual-test-results)에서
// 실제(-actual)와 정답(-expected)을 맞대어 갈린 픽셀의 자리와 값을 낸다.
//   node .scratch/harness/probes/visual_flake/ci_diff.mjs <아티팩트를 푼 폴더> [...]
// 폴더 아래를 훑어 `<이름>-actual.png` 와 `<이름>-expected.png` 짝마다 한 덩이를 찍는다.
//
// 측정의 표지는 둘이고 둘 다 맞아야 그 짝을 측정으로 센다. 하나라도 어긋나면 측정 아님으로 세고 종료 코드가 1 이다.
// - 같은 폴더의 `<이름>-diff.png` 에서 빨강(255,0,0)인 픽셀의 수가 error-context.md 의 "N pixels ... are different" 의
//   N 과 같다. Playwright 의 비교(pixelmatch)는 안티에일리어싱으로 본 픽셀을 노랑(255,255,0)으로 칠하고 N 에서 뺀다.
// - 이 디코더가 실제·정답에서 RGBA 가 다르다고 센 픽셀의 자리가 차이 그림의 빨강과 노랑을 합친 자리와 같다.
// 첫 판은 N 과 디코더의 수를 바로 맞댔는데 세 짝 모두 디코더 쪽이 많았다(1·2, 3·29, 6·17). 차이 그림의 노랑을 보고
// 위 두 표지로 바꿨다. 짝을 하나도 찾지 못한 폴더(내려받기가 비었다)와 읽거나 맞대지 못한 짝(크기가 다르다)도
// 측정 아님이다.
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { differingPixels, readPng } from "./png.mjs";

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(path);
    else yield path;
  }
}

const roots = process.argv.slice(2);
if (roots.length === 0) {
  console.error("사용: node ci_diff.mjs <아티팩트를 푼 폴더> [...]");
  process.exit(2);
}

let notMeasured = 0;
for (const root of roots) {
  let pairs = 0;
  for (const actualPath of walk(root)) {
    if (!actualPath.endsWith("-actual.png")) continue;
    pairs += 1;
    const name = basename(actualPath).slice(0, -"-actual.png".length);
    const expectedPath = join(dirname(actualPath), `${name}-expected.png`);
    if (!existsSync(expectedPath)) {
      console.log(`측정 아님: ${name} 의 정답 그림이 없다`);
      notMeasured += 1;
      continue;
    }
    // 읽기나 맞대기가 던지면(크기가 다르다, 모르는 PNG) 그 짝만 측정 아님으로 세고 뒤의 짝을 잇는다.
    let actual;
    let found;
    const marks = new Map();
    try {
      actual = readPng(actualPath);
      found = differingPixels(readPng(expectedPath), actual);
      const diffPath = join(dirname(actualPath), `${name}-diff.png`);
      if (existsSync(diffPath)) {
        const diff = readPng(diffPath);
        for (let i = 0; i < diff.width * diff.height; i += 1) {
          const [r, g, b] = diff.rgba.subarray(i * 4, i * 4 + 3);
          if (r === 255 && g === 0 && b === 0) marks.set(i, "빨강");
          else if (r === 255 && g === 255 && b === 0) marks.set(i, "노랑");
        }
      }
    } catch (error) {
      console.log(
        `측정 아님: ${name} 을 읽거나 맞대지 못했다(${error instanceof Error ? error.message : String(error)})`,
      );
      notMeasured += 1;
      continue;
    }
    const contextPath = join(dirname(actualPath), "error-context.md");
    const reported = existsSync(contextPath)
      ? /(\d+) pixels \(ratio [\d.]+ of all image pixels\) are different/.exec(
          readFileSync(contextPath, "utf-8"),
        )
      : null;
    const red = [...marks.values()].filter((mark) => mark === "빨강").length;
    const sameSpots =
      marks.size === found.length && found.every(({ x, y }) => marks.has(y * actual.width + x));
    const marker = reported !== null && Number(reported[1]) === red && sameSpots;
    console.log(
      `${name}: ${actual.width}×${actual.height}, 갈린 픽셀 ${found.length}(빨강 ${red}, 노랑 ${marks.size - red}), Playwright 보고 ${reported?.[1] ?? "없음"}${marker ? "" : " (측정 아님)"}`,
    );
    if (!marker) notMeasured += 1;
    for (const { x, y, a, b } of found) {
      const delta = a.map((value, c) => b[c] - value);
      const mark = marks.get(y * actual.width + x) ?? "표시 없음";
      console.log(
        `  (${x}, ${y}) ${mark} 정답 rgba(${a.join(",")}) 실제 rgba(${b.join(",")}) 차 [${delta.join(",")}]`,
      );
    }
  }
  if (pairs === 0) {
    console.log(`측정 아님: ${root} 에 실제 그림(-actual.png)이 없다`);
    notMeasured += 1;
  }
}
process.exit(notMeasured === 0 ? 0 : 1);
