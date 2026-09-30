// 데스크톱 앱의 app.asar 를 풀지 않고 헤더를 읽어 .js 파일에서 패턴 주변의 글자를 찍는다. 읽기만 한다(일지 2026-09-30-06).
// 쓰는 법: node .scratch/harness/probes/asar_grep.mjs <app.asar> <정규식> [앞뒤 글자 수] [파일 경로의 일부]
// 2026-09-30(앱 2.9939.2): `"second-instance"` 의 처리기가 첫 줄 `if(ej())return;` 에서 돌아가고, `ej` 는 끝내기 깃발 셋
// (`JA||YA||XA`)이었다. 축약 이름은 청크마다 겹쳐 네 번째 인자로 그 청크(예: `6aZ703Pj`)를 좁힌다. 판이 바뀌면 이름도 바뀐다.
import { openSync, readSync } from "node:fs";

const [asarPath, pattern, spanArg, only] = process.argv.slice(2);
const span = Number(spanArg ?? 300);
const fd = openSync(asarPath, "r");
const read = (offset, length) => {
  const buf = Buffer.alloc(length);
  readSync(fd, buf, 0, length, offset);
  return buf;
};
const sizeBuf = read(0, 8);
const headerSize = sizeBuf.readUInt32LE(4);
const headerBuf = read(8, headerSize);
const jsonLen = headerBuf.readUInt32LE(4);
const header = JSON.parse(headerBuf.subarray(8, 8 + jsonLen).toString("utf8"));
const base = 8 + headerSize;
const regex = new RegExp(pattern, "g");

function* walk(node, prefix) {
  for (const [name, entry] of Object.entries(node.files ?? {})) {
    const path = `${prefix}/${name}`;
    if (entry.files) yield* walk(entry, path);
    else yield [path, entry];
  }
}

for (const [path, entry] of walk(header, "")) {
  if (!/\.(c|m)?js$/.test(path) || entry.unpacked || path.includes("node_modules")) continue;
  if (only && !path.includes(only)) continue;
  const text = read(base + Number(entry.offset), entry.size).toString("utf8");
  for (const match of text.matchAll(regex)) {
    const start = Math.max(0, match.index - span);
    console.log(`== ${path} @${match.index}`);
    console.log(text.slice(start, match.index + span).replace(/\s+/g, " "));
  }
}
