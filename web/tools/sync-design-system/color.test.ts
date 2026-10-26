// 색 변환의 테스트(design-reverse-sync 명세 "가장 가까운 값"의 2026-10-22 주석). 알려진 값의 변환과 hex 왕복을 본다.
// 알려진 값은 hsl()·rgb() 의 정의에서 바로 나오는 값과, CSS Color 4(https://www.w3.org/TR/css-color-4/) §7.3 이 적은
// sRGB 파랑·노랑의 OKLCH(소수 셋째 자리)다. 빨강·파랑의 소수 여섯째 자리 값은 CSS Color 4 표본 코드의 행렬(XYZ 를
// 거친다)로 셈해 이 모듈의 값과 그 자리까지 같았다(2026-10-27 손으로 봤다, 일지 2026-10-26-19).

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, expect, test } from "vitest";
import {
  expandHex,
  fromOklch,
  nearestByAlpha,
  nearestByLightness,
  readColor,
  readOklch,
  toHex,
  toOklch,
  type Srgb,
} from "./color.ts";

const WEB = dirname(dirname(import.meta.dirname));
const CSS = readFileSync(join(WEB, "packages", "ui", "src", "styles", "theme.css"), "utf-8");

/** 읽은 색의 hex. 읽지 못하거나 sRGB 밖이면 undefined. */
function hexOf(text: string): string | undefined {
  const color = readColor(text);
  return color === undefined ? undefined : toHex(color);
}

function read(text: string): Srgb {
  const color = readColor(text);
  if (color === undefined) {
    throw new Error(`${text} 를 읽지 못했다`);
  }
  return color;
}

describe("색 읽기와 hex", () => {
  test.each([
    ["#abc", "#aabbcc"],
    ["#ABCD", "#aabbccdd"],
    ["#ffffffff", "#ffffffff"],
    ["rgb(0 0 0)", undefined],
    ["#abcde", undefined],
  ])("hex 펴기는 %s 를 %s 로 낸다", (text, hex) => {
    expect(expandHex(text)).toBe(hex);
  });

  test.each([
    ["#abc", "#aabbcc"],
    ["#ABCD", "#aabbccdd"],
    ["#F4F8FB", "#f4f8fb"],
    ["#0000000a", "#0000000a"],
    ["#ffffffff", "#ffffff"],
  ])("hex %s 는 %s 다", (text, hex) => {
    expect(hexOf(text)).toBe(hex);
  });

  test.each([
    ["rgb(255 0 0)", "#ff0000"],
    ["rgb(255, 128, 0)", "#ff8000"],
    ["rgb(100% 50% 0%)", "#ff8000"],
    ["rgb(255 0 0 / 50%)", "#ff000080"],
    ["rgba(0, 0, 255, 0.25)", "#0000ff40"],
    ["rgb(none 0 0)", "#000000"],
    ["hsl(120 100% 50%)", "#00ff00"],
    ["hsl(120deg, 100%, 50%)", "#00ff00"],
    ["hsl(0.5turn 100% 50%)", "#00ffff"],
    ["hsla(0, 0%, 50%, 0.5)", "#80808080"],
    ["hsl(0 -50% 50%)", "#808080"],
    ["oklab(0.627955 0.224863 0.125846)", "#ff0000"],
    ["oklch(0.627955 0.257683 29.2339)", "#ff0000"],
    ["oklch(62.7955% 0.257683 29.2339deg)", "#ff0000"],
    ["oklch(0.452014 0.313214 264.052)", "#0000ff"],
    ["oklch(1 0 0)", "#ffffff"],
    ["oklch(0 0 0)", "#000000"],
    ["oklch(0.627955 0.257683 29.2339 / 0.5)", "#ff000080"],
  ])("%s 는 %s 다", (text, hex) => {
    expect(hexOf(text)).toBe(hex);
  });

  test.each(["oklch(0.7 0.4 30)", "oklab(0.5 0.4 0.4)", "rgb(300 0 0)", "hsl(0 100% 120%)"])(
    "sRGB 밖의 %s 는 hex 가 없다",
    (text) => {
      expect(readColor(text)).toBeDefined();
      expect(hexOf(text)).toBeUndefined();
    },
  );

  test.each([
    "lab(50% 40 59)",
    "lch(50% 72 56)",
    "color(display-p3 1 0 0)",
    "rgb(1 2)",
    "rgb(1 2 3 4)",
    "rgb(none, 0, 0)",
    "oklch(0.5, 0.1, 30)",
    "oklab(0.5, 0.1, 0.1)",
    "oklch(a b c)",
    "{gray-0}",
    "red",
  ])("다른 색 공간이나 읽지 못하는 값 %s 는 읽지 않는다", (text) => {
    expect(readColor(text)).toBeUndefined();
  });

  // 못 보는 것(모듈 독스트링): 쉼표 꼴에서 CSS 가 받지 않는 값의 꼴도 읽는다.
  test.each([
    ["rgb(100%, 0, 0)", "#ff0000"],
    ["hsl(120, 100, 50)", "#00ff00"],
  ])("쉼표 꼴에서 CSS 가 받지 않는 %s 도 %s 로 읽는다", (text, hex) => {
    expect(hexOf(text)).toBe(hex);
  });

  test("반 단계 안쪽은 sRGB 안으로, 그 밖은 밖으로 본다", () => {
    expect(toHex({ red: 1 + 0.4 / 255, green: -0.4 / 255, blue: 0.5, alpha: 1 })).toBe("#ff0080");
    expect(toHex({ red: 1 + 0.6 / 255, green: 0, blue: 0, alpha: 1 })).toBeUndefined();
    expect(toHex({ red: 0, green: -0.6 / 255, blue: 0, alpha: 1 })).toBeUndefined();
  });
});

describe("OKLCH 왕복", () => {
  test.each([
    ["#0000ff", 0.452, 0.313, 264.1],
    ["#ffff00", 0.968, 0.211, 109.8],
  ])("%s 의 OKLCH 는 CSS Color 4 §7.3 이 적은 값이다", (hex, lightness, chroma, hue) => {
    const color = toOklch(read(hex));

    expect(color.lightness).toBeCloseTo(lightness, 3);
    expect(color.chroma).toBeCloseTo(chroma, 3);
    expect(color.hue).toBeCloseTo(hue, 1);
  });

  test("빨강의 OKLCH 는 CSS Color 4 표본 코드로 셈한 값이다", () => {
    const red = toOklch(read("#ff0000"));

    expect(red.lightness).toBeCloseTo(0.627955, 5);
    expect(red.chroma).toBeCloseTo(0.257683, 5);
    expect(red.hue).toBeCloseTo(29.2339, 3);
    expect(red.alpha).toBe(1);
  });

  test("파랑처럼 OKLab 의 b 가 음수인 색도 색상을 0 이상 360 미만의 도로 낸다", () => {
    expect(toOklch(read("#0000ff")).hue).toBeCloseTo(264.052, 3);
  });

  test("디자인 토큰 CSS 의 hex 는 모두 OKLCH 로 갔다 와도 같은 hex 다", () => {
    const hexes = [...new Set(CSS.match(/#[0-9a-f]{6}(?:[0-9a-f]{2})?\b/gi) ?? [])];

    expect(hexes.length).toBeGreaterThan(100);
    expect(
      hexes.filter((hex) => toHex(fromOklch(toOklch(read(hex)))) !== hex.toLowerCase()),
    ).toEqual([]);
  });

  test("oklch() 는 적힌 값 그대로 OKLCH 로 읽고, 다른 꼴은 sRGB 를 거쳐 읽는다", () => {
    expect(readOklch("oklch(0.3 0.01 220 / 50%)")).toEqual({
      lightness: 0.3,
      chroma: 0.01,
      hue: 220,
      alpha: 0.5,
    });
    expect(readOklch("oklch(120% -1 1turn)")).toEqual({
      lightness: 1,
      chroma: 0,
      hue: 360,
      alpha: 1,
    });
    expect(readOklch("#ff0000")).toEqual(toOklch(read("#ff0000")));
    expect(readOklch("lab(50% 40 59)")).toBeUndefined();
  });

  // 두 행렬은 소수 열 자리로 끊긴 값이라 서로의 역이 1e-9 쯤 어긋난다. hex 한 단계(1/255)보다 훨씬 작다.
  test("밝기만 옮긴 OKLCH 는 색상과 채도를 지킨다", () => {
    const start = toOklch(read("#2d8a8a"));
    const moved = toOklch(fromOklch({ ...start, lightness: start.lightness + 0.05 }));

    expect(moved.lightness).toBeCloseTo(start.lightness + 0.05, 6);
    expect(moved.chroma).toBeCloseTo(start.chroma, 6);
    expect(moved.hue).toBeCloseTo(start.hue, 4);
  });
});

describe("가장 가까운 통과 값", () => {
  test("밝기는 0.001 씩 옮기고, 양쪽이 같은 걸음에서 지나면 밝은 쪽을 낸다", () => {
    const origin = toOklch(read("#808080"));

    expect(nearestByLightness(origin, () => true)).toEqual({
      steps: 1,
      value: toHex(fromOklch({ ...origin, lightness: origin.lightness + 0.001 })),
    });
  });

  test("투명도는 1/255 씩 옮기고, 양쪽이 같은 걸음에서 지나면 투명한 쪽을 낸다", () => {
    expect(nearestByAlpha("#ffffffcc", () => true)).toEqual({ steps: -1, value: "#ffffffcb" });
  });

  test("불투명에 닿은 투명도는 6 자리로 낸다", () => {
    expect(nearestByAlpha("#000000fe", (hex) => hex.length === 7)).toEqual({
      steps: 1,
      value: "#000000",
    });
  });

  test("지나는 값이 없으면 없다고 낸다", () => {
    expect(nearestByLightness(toOklch(read("#808080")), () => false)).toBeUndefined();
    expect(nearestByAlpha("#ffffffcc", () => false)).toBeUndefined();
  });
});
