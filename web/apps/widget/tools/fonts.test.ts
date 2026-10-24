// 시작 래퍼가 public/fonts/ 에 복사하는 글꼴 파일. 글꼴 CSS(`@agent-os/ui/fonts.css`)가 들이는 굵기 CSS 의 woff2 를
// 빠짐없이 고르는지와, 복사한 자리에서 이름이 겹치지 않는지, 페이지 안 번들이 등록할 face 가 그 파일과 맞는지를 본다.

import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { basename, join } from "node:path";
import { expect, test } from "vitest";
import { copyFonts, fontFaces, fontFiles } from "./fonts.ts";

/** 굵기 CSS 하나의 @font-face 수. 블록마다 woff2 하나를 가리킨다. */
function faceCount(specifier: string): number {
  const ui = createRequire(import.meta.url).resolve("@agent-os/ui/fonts.css");
  const css = readFileSync(createRequire(ui).resolve(specifier), "utf-8");
  return css.match(/@font-face/g)?.length ?? 0;
}

test("글꼴 CSS 가 들이는 다섯 굵기 CSS 의 woff2 를 모두 고르고, 파일은 모두 있다", () => {
  const files = fontFiles();
  const expected = [
    "@fontsource/noto-sans-kr/400.css",
    "@fontsource/noto-sans-kr/500.css",
    "@fontsource/noto-sans-kr/600.css",
    "@fontsource/noto-sans-mono/400.css",
    "@fontsource/noto-sans-mono/500.css",
  ].reduce((sum, specifier) => sum + faceCount(specifier), 0);

  expect(expected).toBeGreaterThan(0);
  expect(files).toHaveLength(expected);
  expect(files.every((file) => file.endsWith(".woff2") && existsSync(file))).toBe(true);
  expect(files.some((file) => basename(file).startsWith("noto-sans-mono-"))).toBe(true);
});

test("페이지 안 번들이 등록할 face 는 고른 파일마다 하나이고 family·굵기·글자 범위를 든다", () => {
  const faces = fontFaces();

  expect(faces.map((face) => face.file).sort()).toEqual(
    fontFiles()
      .map((file) => basename(file))
      .sort(),
  );
  const weights = (family: string) =>
    [...new Set(faces.filter((face) => face.family === family).map((face) => face.weight))].sort();
  expect(weights("Noto Sans KR")).toEqual(["400", "500", "600"]);
  expect(weights("Noto Sans Mono")).toEqual(["400", "500"]);
  expect(new Set(faces.map((face) => face.family))).toEqual(
    new Set(["Noto Sans KR", "Noto Sans Mono"]),
  );
  expect(faces.every((face) => face.style === "normal")).toBe(true);
  // 한글 음절(가, U+AC00)이 어느 face 의 범위에는 든다. 범위를 빠뜨리면 브라우저는 face 하나가 모든 글자를 맡는다고 본다.
  expect(faces.every((face) => /^U\+[0-9a-f]/i.test(face.unicodeRange))).toBe(true);
  expect(
    faces.some((face) => face.family === "Noto Sans KR" && covers(face.unicodeRange, 0xac00)),
  ).toBe(true);
});

/** CSS unicode-range 글자(`U+0-ff,U+ac00`)가 그 코드 포인트를 덮는지. */
function covers(range: string, codePoint: number): boolean {
  return range.split(",").some((part) => {
    const [start = "", end = start] = part.trim().replace(/^U\+/i, "").split("-");
    return parseInt(start, 16) <= codePoint && codePoint <= parseInt(end, 16);
  });
}

test("복사한 자리에는 고른 파일이 이름 그대로 하나씩 있다. 두 글꼴의 이름이 겹치지 않는다", () => {
  const target = mkdtempSync(join(tmpdir(), "widget-fonts-"));
  try {
    copyFonts(join(target, "fonts"));

    const copied = readdirSync(join(target, "fonts")).sort();
    expect(copied).toEqual(
      fontFiles()
        .map((file) => basename(file))
        .sort(),
    );
  } finally {
    rmSync(target, { recursive: true, force: true });
  }
});
