/**
 * 위젯이 내주는 글꼴 파일. 시작 래퍼(`start.ts`)가 `dev` 와 `build` 전에 `public/fonts/` 로 복사하고, Next 가 그것을
 * `/widget/fonts/` 아래에서 낸다(web-widget 명세 "위젯 앱의 배치와 빌드"). 페이지 안 번들(티켓 10)이 사이트 문서에서
 * `FontFace` 로 받는 파일이다. iframe 페이지는 이 자리를 쓰지 않고 글꼴 CSS 를 Next 의 번들로 싣는다.
 *
 * 고르는 것은 글꼴 CSS(`@agent-os/ui/fonts.css`)가 `@import` 하는 굵기 CSS 들이 `url()` 로 가리키는 woff2 이고, 이름을
 * 바꾸지 않는다. woff 는 고르지 않는다. 굵기 CSS 는 woff2 를 먼저 적고, 위젯이 지원하는 브라우저는 모두 woff2 를 읽는다.
 * 복사한 자리는 저장소가 무시한다(뿌리 `.gitignore`). 이미 있는 파일은 덮어쓰고, 굵기 CSS 에서 빠진 옛 파일은 지우지
 * 않는다.
 *
 * 페이지 안 번들은 같은 굵기 CSS 의 @font-face 마다 family·굵기·모양·글자 범위·woff2 이름을 받아(`fontFaces`) 사이트
 * 문서에 등록한다(element/fonts.ts). 빌드 설정(element.ts)이 그 목록을 번들에 싣는다. 블록에서 하나라도 읽지 못하면
 * 던져 빌드를 멈춘다. 글자 범위를 빠뜨린 face 는 모든 글자를 맡는다고 읽힌다.
 */

import { copyFileSync, mkdirSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { basename, dirname, join } from "node:path";
import type { FontFaceSource } from "../element/fonts.ts";

const IMPORT = /@import\s+"([^"]+)"\s*;/g;
const WOFF2 = /url\(\s*["']?(\.\/files\/[^"')]+\.woff2)["']?\s*\)/g;
const FACE = /@font-face\s*\{([^}]*)\}/g;

/** 글꼴 CSS 가 들이는 굵기 CSS 들의 절대 경로. 글꼴 CSS 의 차례다. */
function weightCss(): string[] {
  const fontsCss = createRequire(import.meta.url).resolve("@agent-os/ui/fonts.css");
  const fromUi = createRequire(fontsCss);
  const found: string[] = [];
  for (const [, specifier] of readFileSync(fontsCss, "utf-8").matchAll(IMPORT)) {
    if (specifier !== undefined) {
      found.push(fromUi.resolve(specifier));
    }
  }
  return found;
}

/** 글꼴 CSS 가 들이는 굵기 CSS 들의 woff2 파일. 절대 경로이고 정렬했다. */
export function fontFiles(): string[] {
  const files = new Set<string>();
  for (const css of weightCss()) {
    for (const [, url] of readFileSync(css, "utf-8").matchAll(WOFF2)) {
      if (url !== undefined) {
        files.add(join(dirname(css), url));
      }
    }
  }
  return [...files].sort();
}

/** 굵기 CSS 들의 @font-face. 글꼴 CSS 와 굵기 CSS 의 차례다. */
export function fontFaces(): FontFaceSource[] {
  const faces: FontFaceSource[] = [];
  for (const css of weightCss()) {
    for (const [, block = ""] of readFileSync(css, "utf-8").matchAll(FACE)) {
      faces.push(faceOf(block, css));
    }
  }
  return faces;
}

function faceOf(block: string, css: string): FontFaceSource {
  const read = (pattern: RegExp, what: string): string => {
    const value = pattern.exec(block)?.[1]?.trim();
    if (value === undefined || value === "") {
      throw new Error(`글꼴 CSS ${css} 의 @font-face 에서 ${what} 을 읽지 못했다`);
    }
    return value;
  };
  return {
    family: read(/font-family:\s*['"]([^'"]+)['"]/, "font-family"),
    weight: read(/font-weight:\s*([^;]+);/, "font-weight"),
    style: read(/font-style:\s*([^;]+);/, "font-style"),
    unicodeRange: read(/unicode-range:\s*([^;]+);/, "unicode-range"),
    file: basename(read(/url\(\s*["']?\.\/files\/([^"')]+\.woff2)["']?\s*\)/, "woff2")),
  };
}

/** 글꼴 파일을 `target` 에 이름 그대로 복사한다. */
export function copyFonts(target: string): void {
  mkdirSync(target, { recursive: true });
  for (const file of fontFiles()) {
    copyFileSync(file, join(target, basename(file)));
  }
}
