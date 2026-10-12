// design-refresh Chromium 프로브: 반투명 쓰임새 토큰을 실제 Chromium 이 어떻게 직렬화하고 칠하는지 본다.
//   node .scratch/design-refresh/probes/chromium.mjs [node_modules 가 있는 web 폴더, 기본 web]
//
// 1) 직렬화. 원색 `overlay` 일곱을 사용자 정의 속성에 두고 그것을 `background-color` 로 쓴 요소에서, 계산값과
//    `getPropertyValue` 가 돌려주는 꼴을 낸다. 스토리 테스트의 계산값 단언이 반투명 쓰임새 토큰을 받으려면 이 꼴을 알아야 한다.
// 2) 칠한 픽셀. 명세의 명암비 판정은 반투명을 아래 바탕에 겹친 색을 채널마다 정수로 반올림해 잰다(`contrast.mjs`). 브라우저가
//    실제로 칠한 픽셀이 그 값과 같은지, 그 픽셀과 글자색의 명암비가 판정값과 어떻게 다른지 본다. 대상은 다크 네 테마의 위험
//    버튼 누름(`danger` 글자, `bg-raised`·`bg` 에 겹친 `bg-selected` 바탕)이다. 명세가 남긴 위험(녹청 다크의 카드 안 4.507)의
//    자리다.
// 값은 `design.mjs` 의 `readRefresh()` 가 돌려주는 디자인 토큰 JSON 에서 읽는다. 브라우저는 그 web 폴더의 `playwright` 가
// 깐 chromium 이다(없으면 `pnpm -C web exec playwright install chromium`).
// 측정의 표지: 1) 은 `getPropertyValue` 가 넣은 hex 를 그대로 돌려주고 계산값의 RGB 와 알파(소수 둘째 자리)가 그 hex 와 맞는
// 회차, 2) 는 스크린샷이 1×1·깊이 8·RGB(A)·인터레이스 없음의 PNG 이고 칠한 픽셀이 아래 바탕과 다른 회차(반투명이 실제로
// 칠해졌다)만 측정으로 센다. 표지가 없는 회차가 하나라도 있거나, 측정한 회차가 기대(직렬화 7, 픽셀 16)보다 적으면 종료
// 코드가 1이다.
// stdout 은 1) 의 hex 마다 계산값과 사용자 정의 속성 값, 2) 의 자리마다 칠한 RGB와 명암비, 판정(반올림)과 반올림 없는 값,
// 그리고 chromium 판이다.

import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { inflateSync } from "node:zlib";
import { readRefresh } from "../../design-system/probes/tokens/design.mjs";

const web = resolve(process.argv[2] ?? "web");
const require = createRequire(join(web, "package.json"));
// require.resolve 는 CommonJS 진입점을 준다. 그 import 는 module.exports 를 default 로 낸다.
const { chromium } = (await import(pathToFileURL(require.resolve("playwright")).href)).default;
const { tokens } = readRefresh();

const rgbOf = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
const alphaOf = (hex) => (hex.length < 9 ? 1 : parseInt(hex.slice(7, 9), 16) / 255);
const over = (hex, base, round) =>
  rgbOf(hex).map((v, i) => {
    const mixed = v * alphaOf(hex) + base[i] * (1 - alphaOf(hex));
    return round ? Math.round(mixed) : mixed;
  });
const linear = (v) => (v / 255 <= 0.04045 ? v / 255 / 12.92 : ((v / 255 + 0.055) / 1.055) ** 2.4);
const luminance = ([r, g, b]) => 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
const ratio = (a, b) => {
  const [x, y] = [luminance(a), luminance(b)];
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
};

/** 한 벌의 쓰임새 토큰 hex(`contrast.mjs` 와 같은 풀이). */
function semanticHex(theme, mode) {
  const t = tokens.theme[theme];
  return Object.fromEntries(
    Object.entries(t.semantic[mode]).map(([name, ref]) => {
      const dot = ref.indexOf(".");
      return [name, t.primitive[ref.slice(0, dot)][ref.slice(dot + 1)]];
    }),
  );
}

/**
 * 1×1 PNG 의 첫 화소 RGB. 화소가 하나라 어느 필터든 원래 바이트가 그대로다(왼쪽과 위가 0). 그 읽기는 폭·높이 1, 깊이 8,
 * 색 유형 2(RGB)나 6(RGBA), 인터레이스 없음일 때만 맞아, 머리(IHDR)가 그렇지 않으면 `null` 을 돌려준다(측정 아님).
 */
function firstPixel(png) {
  const idat = [];
  let header = null;
  for (let at = 8; at < png.length; at += 12 + png.readUInt32BE(at)) {
    const size = png.readUInt32BE(at);
    const type = png.toString("ascii", at + 4, at + 8);
    if (type === "IHDR") header = png.subarray(at + 8, at + 8 + size);
    if (type === "IDAT") idat.push(png.subarray(at + 8, at + 8 + size));
  }
  const plain =
    header !== null &&
    header.readUInt32BE(0) === 1 &&
    header.readUInt32BE(4) === 1 &&
    header[8] === 8 &&
    (header[9] === 2 || header[9] === 6) &&
    header[12] === 0;
  if (!plain) return null;
  const raw = inflateSync(Buffer.concat(idat));
  return [raw[1], raw[2], raw[3]];
}

/** `rgba(r, g, b, a)` 계산값을 수 넷으로. 그 꼴이 아니면 `null`. */
function parseRgba(text) {
  const match = /^rgba\((\d+), (\d+), (\d+), ([\d.]+)\)$/.exec(text);
  return match === null ? null : match.slice(1).map(Number);
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 64, height: 64 }, deviceScaleFactor: 1 });
let unmeasured = 0;
// 기대하는 회차의 수. 디자인 토큰 JSON 이 비어 오면 아무것도 재지 않고 0으로 끝나지 않게 센다.
const EXPECTED = { overlays: 7, pixels: 16 };
const done = { overlays: 0, pixels: 0 };

console.log("1) 직렬화");
const overlays = Object.values(tokens.theme.nokcheong.primitive.overlay).map((hex) => hex.toLowerCase());
for (const hex of overlays) {
  const [computed, custom] = await page.evaluate((value) => {
    const el = document.createElement("div");
    el.style.setProperty("--x", value);
    el.style.backgroundColor = "var(--x)";
    document.body.append(el);
    const style = getComputedStyle(el);
    const out = [style.backgroundColor, style.getPropertyValue("--x").trim()];
    el.remove();
    return out;
  }, hex);
  // 계산값의 RGB 와 알파(소수 둘째 자리)가 넣은 hex 와 맞아야 측정이다. 8자리를 읽지 못한 브라우저의 초기값
  // `rgba(0, 0, 0, 0)` 이 `rgba(` 로 시작한다는 것만으로 지나지 않게 한다.
  const parsed = parseRgba(computed);
  const alpha = Math.round((parseInt(hex.slice(7, 9), 16) / 255) * 100) / 100;
  const measured =
    custom.toLowerCase() === hex &&
    parsed !== null &&
    rgbOf(hex).every((v, i) => parsed[i] === v) &&
    parsed[3] === alpha;
  if (measured) done.overlays += 1;
  else unmeasured += 1;
  console.log(`  ${hex} 계산값 ${computed} 사용자 정의 속성 ${custom}${measured ? "" : " (측정 아님)"}`);
}

// 반투명 상자 안에 글자가 있는지로 갈래를 둔다. 손으로 처음 볼 때 글자가 있는 상자의 픽셀이 한 단위 어두웠다. 버튼에는
// 글자가 있으므로 "글자 있음"이 실제에 가깝다. 읽는 화소(40, 40)는 왼쪽 위의 글자에 덮이지 않는다.
console.log("2) 칠한 픽셀 — 다크, danger 글자, bg-selected 를 겹친 바탕");
const box = (color, inner) => `<div style="width:64px;height:64px;background:${color}">${inner}</div>`;
const INNERS = [
  ["글자 없음", ""],
  ["글자 있음", '<span style="font-size:12px">위험</span>'],
];
for (const theme of Object.keys(tokens.theme)) {
  const hex = semanticHex(theme, "dark");
  for (const base of ["bg-raised", "bg"]) {
    const below = rgbOf(hex[base]);
    const text = rgbOf(hex.danger);
    const judged = over(hex["bg-selected"], below, true);
    const exact = over(hex["bg-selected"], below, false);
    console.log(
      `  ${theme} ${base}: 판정 ${judged.join(",")} ${ratio(text, judged).toFixed(3)}` +
        ` / 반올림 없이 ${ratio(text, exact).toFixed(3)}`,
    );
    for (const [label, inner] of INNERS) {
      await page.setContent(`<body style="margin:0">${box(hex[base], box(hex["bg-selected"], inner))}</body>`);
      const painted = firstPixel(await page.screenshot({ clip: { x: 40, y: 40, width: 1, height: 1 } }));
      if (painted === null) {
        unmeasured += 1;
        console.log(`    ${label}: 측정 아님(스크린샷이 1×1·깊이 8·RGB(A)·인터레이스 없음의 PNG 가 아니다)`);
        continue;
      }
      const measured = painted.some((v, i) => v !== below[i]);
      if (measured) done.pixels += 1;
      else unmeasured += 1;
      console.log(
        `    ${label}: 칠한 ${painted.join(",")} ${ratio(text, painted).toFixed(3)}` +
          `${measured ? "" : " (측정 아님: 아래 바탕과 같다)"}`,
      );
    }
  }
}

console.log(`chromium ${browser.version()}`);
await browser.close();
for (const [what, expected] of Object.entries(EXPECTED)) {
  if (done[what] !== expected) {
    console.log(`측정한 ${what} 회차 ${String(done[what])}, 기대 ${String(expected)}`);
    process.exitCode = 1;
  }
}
if (unmeasured > 0) {
  console.log(`측정이 아닌 회차 ${String(unmeasured)}`);
  process.exitCode = 1;
}
