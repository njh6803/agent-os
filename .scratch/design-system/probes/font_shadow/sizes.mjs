// design-system 글꼴 프로브: Pretendard 패키지의 판, 라이선스, woff2 파일 크기를 파일에서 직접 잰다.
//   node .scratch/design-system/probes/font_shadow/sizes.mjs <pretendard 패키지 폴더> [--out <결과 json>]
// <pretendard 패키지 폴더>는 `npm pack pretendard@<판>` 으로 받은 tgz 를 저장소 밖에서 푼 `package/` 다(package.json 이
// 있는 자리). 받은 글꼴은 저장소에 두지 않는다.
//
// 재는 것
//   package   package.json 의 name·version·license 와 LICENSE.txt 의 저작권 줄(예약 글꼴 이름)
//   full      굵기 하나 전체 글자 파일(static/woff2), 9 굵기 전부, 가변 글꼴 하나(variable/woff2), 저자가 낸 고정
//             서브셋(static/woff2-subset)의 바이트
//   dynamic   동적 서브셋 CSS(static 의 400 굵기, variable)를 읽어 @font-face 조각마다 unicode-range 와 파일 크기를
//             짝짓는다. 조각 수, 합, 최소·최대, 범위가 덮는 코드 포인트 수와 한글 음절(U+AC00–D7A3, 11,172자) 수,
//             그리고 SENTENCE 의 코드 포인트를 하나라도 덮는 조각(브라우저가 받아야 할 조각)의 번호와 바이트.
//             브라우저가 실제로 받은 조각은 measure.mjs 의 q4 사례가 잰다. 둘을 견주는 자리다.
//   css       동적 서브셋 CSS 파일 자체의 바이트와, 400 굵기 규칙만 남겼을 때의 바이트(각각 gzip 9단계도)
//   glyphs    subset_glyphs.txt(고정 서브셋의 글자 목록)의 글자 수, 한글 음절 수, SENTENCE 를 다 덮는지
// 결과는 JSON 으로 stdout 에 내고 --out 이 있으면 그 파일에도 쓴다.

import { readFileSync, statSync, writeFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { gzipSync } from "node:zlib";

// measure.mjs 의 SENTENCE 와 같은 글자열이다(모듈을 import 하면 이 파일의 최상위가 돌아서 따로 둔다).
const SENTENCE ="승인을 기다리고 있습니다. 허가하거나 거부해 주세요.";

const args = process.argv.slice(2);
const outIndex = args.indexOf("--out");
const out = outIndex === -1 ? null : resolve(args[outIndex + 1]);
const pkg = resolve(args.find((arg, i) => !arg.startsWith("--") && args[i - 1] !== "--out") ?? ".");
const web = join(pkg, "dist", "web");

const size = (path) => statSync(path).size;
// 서버가 압축해 낼 때의 크기 어림으로 gzip 9단계를 쓴다(widget_stack 프로브와 같은 단계). woff2 는 안에서 이미 Brotli 로
// 압축되어 있어 재지 않는다.
const gzip = (text) => gzipSync(Buffer.from(text), { level: 9 }).length;
const isHangulSyllable = (cp) => cp >= 0xac00 && cp <= 0xd7a3;

function woff2Magic(path) {
  return readFileSync(path).subarray(0, 4).toString("latin1");
}

// @font-face 블록을 하나씩 읽는다. 패키지 CSS 는 블록마다 src 의 첫 url 이 woff2 다.
function parseFaces(cssText) {
  const faces = [];
  for (const match of cssText.matchAll(/@font-face\s*\{([^}]*)\}/g)) {
    const block = match[0];
    const body = match[1];
    const prop = (name) => new RegExp(`${name}\\s*:\\s*([^;]+);`).exec(body)?.[1].trim() ?? null;
    const url = /url\(\s*['"]?([^'")]+)['"]?\s*\)/.exec(body)?.[1] ?? null;
    const ranges = (prop("unicode-range") ?? "")
      .split(",")
      .map((part) => part.trim().replace(/^U\+/i, ""))
      .filter(Boolean)
      .map((part) => {
        const [lo, hi] = part.split("-");
        return [Number.parseInt(lo, 16), Number.parseInt(hi ?? lo, 16)];
      });
    faces.push({ block, family: prop("font-family"), weight: prop("font-weight"), url, ranges });
  }
  return faces;
}

function covered(faces) {
  let codePoints = 0;
  let hangul = 0;
  const seen = new Set();
  for (const face of faces) {
    for (const [lo, hi] of face.ranges) {
      for (let cp = lo; cp <= hi; cp += 1) {
        if (!seen.has(cp)) {
          seen.add(cp);
          codePoints += 1;
          hangul += isHangulSyllable(cp) ? 1 : 0;
        }
      }
    }
  }
  return { codePoints, hangulSyllables: hangul };
}

function dynamic(cssRel, weight) {
  const cssPath = join(web, cssRel);
  const cssText = readFileSync(cssPath, "utf-8");
  const all = parseFaces(cssText);
  const faces = weight === null ? all : all.filter((face) => face.weight === weight);
  const slices = faces.map((face) => {
    const file = join(dirname(cssPath), face.url);
    return { index: Number(/\.subset\.(\d+)\.woff2$/.exec(face.url)?.[1]), file: basename(file), bytes: size(file), ranges: face.ranges };
  });
  const bytes = slices.map((slice) => slice.bytes);
  const codePoints = [...new Set([...SENTENCE].map((ch) => ch.codePointAt(0)))];
  const needed = slices.filter((slice) =>
    codePoints.some((cp) => slice.ranges.some(([lo, hi]) => cp >= lo && cp <= hi)),
  );
  const uncovered = codePoints.filter(
    (cp) => !slices.some((slice) => slice.ranges.some(([lo, hi]) => cp >= lo && cp <= hi)),
  );
  const weightOnly = faces.map((face) => face.block).join("\n");
  return {
    css: cssRel,
    cssBytes: Buffer.byteLength(cssText),
    cssGzip: gzip(cssText),
    // 이 굵기의 규칙만 남겼을 때(위젯 번들이 한 굵기만 싣는다면)의 CSS 바이트. 주석은 뺀다.
    cssBytesThisWeightOnly: Buffer.byteLength(weightOnly),
    cssGzipThisWeightOnly: gzip(weightOnly),
    family: faces[0]?.family ?? null,
    weight,
    slices: slices.length,
    totalBytes: bytes.reduce((a, b) => a + b, 0),
    minBytes: Math.min(...bytes),
    maxBytes: Math.max(...bytes),
    coverage: covered(faces),
    sentence: {
      text: SENTENCE,
      distinctCodePoints: codePoints.length,
      neededSlices: needed.map((slice) => slice.index).sort((a, b) => a - b),
      neededBytes: needed.reduce((acc, slice) => acc + slice.bytes, 0),
      uncoveredCodePoints: uncovered.map((cp) => `U+${cp.toString(16).toUpperCase()}`),
    },
  };
}

const manifest = JSON.parse(readFileSync(join(pkg, "package.json"), "utf-8"));
const license = readFileSync(join(pkg, "dist", "LICENSE.txt"), "utf-8").split(/\r?\n/);
const weights = ["Thin", "ExtraLight", "Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold", "Black"];
const staticWoff2 = Object.fromEntries(
  weights.map((name) => [name, size(join(web, "static", "woff2", `Pretendard-${name}.woff2`))]),
);
const glyphs = [...readFileSync(join(pkg, "subset_glyphs.txt"), "utf-8").replace(/\s/g, "")];
const glyphSet = new Set(glyphs);

const result = {
  measuredAt: new Date().toISOString(),
  node: process.version,
  package: {
    name: manifest.name,
    version: manifest.version,
    license: manifest.license,
    copyright: license.slice(0, 2).join(" "),
    licenseTitle: license.find((line) => line.includes("SIL OPEN FONT LICENSE")) ?? null,
  },
  full: {
    regular: {
      file: "static/woff2/Pretendard-Regular.woff2",
      bytes: staticWoff2.Regular,
      magic: woff2Magic(join(web, "static", "woff2", "Pretendard-Regular.woff2")),
    },
    staticAllWeights: staticWoff2,
    staticAllWeightsTotal: Object.values(staticWoff2).reduce((a, b) => a + b, 0),
    variable: {
      file: "variable/woff2/PretendardVariable.woff2",
      bytes: size(join(web, "variable", "woff2", "PretendardVariable.woff2")),
      magic: woff2Magic(join(web, "variable", "woff2", "PretendardVariable.woff2")),
    },
    fixedSubsetRegular: {
      file: "static/woff2-subset/Pretendard-Regular.subset.woff2",
      bytes: size(join(web, "static", "woff2-subset", "Pretendard-Regular.subset.woff2")),
    },
  },
  dynamic: {
    staticRegular: dynamic("static/pretendard-dynamic-subset.css", "400"),
    variable: dynamic("variable/pretendardvariable-dynamic-subset.css", null),
  },
  glyphs: {
    file: "subset_glyphs.txt",
    characters: glyphSet.size,
    hangulSyllables: [...glyphSet].filter((ch) => isHangulSyllable(ch.codePointAt(0))).length,
    coversSentence: [...SENTENCE].filter((ch) => ch.trim() !== "").every((ch) => glyphSet.has(ch)),
  },
};

const text = `${JSON.stringify(result, null, 2)}\n`;
if (out !== null) {
  writeFileSync(out, text);
}
console.log(text);
