// 페이지 안 번들의 글꼴. 빌드가 뽑은 face 를 위젯 출처의 `/widget/fonts/` 에서 받도록 위젯만 쓰는 family 이름으로
// 등록하고, 감싼 요소에서 `--sans`·`--mono` 를 그 이름으로 다시 정한다(web-widget 명세 "테마·모드·밀도·글꼴").

import { expect, test } from "vitest";
import { type FontFaceSource, registerFonts, WIDGET_MONO, WIDGET_SANS } from "./fonts";
import { hostRules } from "./styles";

const FACES: readonly FontFaceSource[] = [
  {
    family: "Noto Sans KR",
    weight: "400",
    style: "normal",
    unicodeRange: "U+ac00-d7a3",
    file: "noto-sans-kr-0-400-normal.woff2",
  },
  {
    family: "Noto Sans Mono",
    weight: "500",
    style: "normal",
    unicodeRange: "U+0000-00ff",
    file: "noto-sans-mono-latin-500-normal.woff2",
  },
];

interface Made {
  readonly family: string;
  readonly source: string;
  readonly descriptors: FontFaceDescriptors;
}

test("face 마다 위젯 출처의 글꼴 파일을 위젯만 쓰는 family 이름으로 등록한다", () => {
  const added: Made[] = [];
  registerFonts(
    FACES,
    new URL("https://widget.example:8443"),
    (family, source, descriptors) => ({ family, source, descriptors }),
    (face) => added.push(face),
  );

  expect(added).toEqual([
    {
      family: WIDGET_SANS,
      source:
        'url("https://widget.example:8443/widget/fonts/noto-sans-kr-0-400-normal.woff2") format("woff2")',
      descriptors: { weight: "400", style: "normal", unicodeRange: "U+ac00-d7a3", display: "swap" },
    },
    {
      family: WIDGET_MONO,
      source:
        'url("https://widget.example:8443/widget/fonts/noto-sans-mono-latin-500-normal.woff2") format("woff2")',
      descriptors: { weight: "500", style: "normal", unicodeRange: "U+0000-00ff", display: "swap" },
    },
  ]);
});

test("모르는 family 는 등록하지 않는다. 사이트의 글꼴 이름을 덮지 않는다", () => {
  const added: Made[] = [];
  registerFonts(
    [
      {
        family: "Arial",
        weight: "400",
        style: "normal",
        unicodeRange: "U+0000-00ff",
        file: "arial.woff2",
      },
    ],
    new URL("https://widget.example"),
    (family, source, descriptors) => ({ family, source, descriptors }),
    (face) => added.push(face),
  );
  expect(added).toEqual([]);
});

test("위젯만 쓰는 이름은 사이트가 쓸 글꼴 이름과 겹치지 않고, 감싼 요소에서 두 글꼴 변수를 그 이름으로 다시 정한다", () => {
  expect(WIDGET_SANS).not.toBe(WIDGET_MONO);
  for (const name of [WIDGET_SANS, WIDGET_MONO]) {
    expect(name.startsWith("agent-os-widget-")).toBe(true);
  }
  const rules = hostRules();
  expect(rules).toContain(`--sans: "${WIDGET_SANS}", system-ui, sans-serif;`);
  expect(rules).toContain(`--mono: "${WIDGET_MONO}", ui-monospace, monospace;`);
});
