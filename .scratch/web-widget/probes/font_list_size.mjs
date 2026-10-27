// 페이지 안 번들이 싣는 글꼴 face 목록의 크기를 두 꼴로 견준다(web-widget 티켓 10). 목록을 그대로 싣는 꼴과, 글자
// 범위를 한 번씩만 싣고 face 가 그것을 가리키는 꼴(tools/element.ts 의 가상 모듈과 같은 모양)이다. 모듈의 글을 지어
// Node 의 zlib(기본 수준)로 gzip·brotli 크기를 잰다. 번들 전체가 아니라 목록 모듈의 글만 잰다.
//
// 표지: face 가 하나 이상이고 범위가 face 보다 적다(겹치는 범위가 실제로 있다). 아니면 재려는 상황이 아니라 1로 끝난다.
//
// 사용: node .scratch/web-widget/probes/font_list_size.mjs web/apps/widget
import { brotliCompressSync, gzipSync } from "node:zlib";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const app = resolve(process.argv[2] ?? "web/apps/widget");
const { fontFaces } = await import(pathToFileURL(join(app, "tools", "fonts.ts")).href);
const faces = fontFaces();
const ranges = [...new Set(faces.map((face) => face.unicodeRange))];
if (faces.length === 0 || ranges.length >= faces.length) {
  console.error(`측정 아님: face ${faces.length}개, 범위 ${ranges.length}개`);
  process.exit(1);
}

const plain = `export const FONT_FACES = ${JSON.stringify(faces)};`;
const shared = `const r=${JSON.stringify(ranges)};export const FONT_FACES=[${faces
  .map(
    (face) =>
      `{family:${JSON.stringify(face.family)},weight:${JSON.stringify(face.weight)},style:${JSON.stringify(face.style)},unicodeRange:r[${ranges.indexOf(face.unicodeRange)}],file:${JSON.stringify(face.file)}}`,
  )
  .join(",")}];`;
console.log(`face ${faces.length}개, 서로 다른 범위 ${ranges.length}개`);
for (const [name, text] of [
  ["그대로", plain],
  ["범위 한 번씩", shared],
]) {
  console.log(
    `${name}: 글 ${text.length}바이트, gzip ${gzipSync(text).length}바이트, brotli ${brotliCompressSync(text).length}바이트`,
  );
}
