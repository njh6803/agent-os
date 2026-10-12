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
// 측정의 표지: 1) 은 `getPropertyValue` 가 넣은 hex 를 그대로 돌려주고 계산값이 `rgba(` 로 시작한 회차, 2) 는 칠한 픽셀이 아래
// 바탕과 다른 회차(반투명이 실제로 칠해졌다)만 측정으로 센다. 표지가 없는 회차가 하나라도 있으면 종료 코드가 1이다.
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

/** 1×1 PNG 의 첫 화소 RGB. 화소가 하나라 어느 필터든 원래 바이트가 그대로다(왼쪽과 위가 0). */
function firstPixel(png) {
  const idat = [];
  for (let at = 8; at < png.length; at += 12 + png.readUInt32BE(at)) {
    const size = png.readUInt32BE(at);
    if (png.toString("ascii", at + 4, at + 8) === "IDAT") idat.push(png.subarray(at + 8, at + 8 + size));
  }
  const raw = inflateSync(Buffer.concat(idat));
  return [raw[1], raw[2], raw[3]];
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 64, height: 64 }, deviceScaleFactor: 1 });
let unmeasured = 0;

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
  const measured = custom.toLowerCase() === hex && computed.startsWith("rgba(");
  if (!measured) unmeasured += 1;
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
      const measured = painted.some((v, i) => v !== below[i]);
      if (!measured) unmeasured += 1;
      console.log(
        `    ${label}: 칠한 ${painted.join(",")} ${ratio(text, painted).toFixed(3)}` +
          `${measured ? "" : " (측정 아님: 아래 바탕과 같다)"}`,
      );
    }
  }
}

console.log(`chromium ${browser.version()}`);
await browser.close();
if (unmeasured > 0) {
  console.log(`측정이 아닌 회차 ${String(unmeasured)}`);
  process.exitCode = 1;
}
