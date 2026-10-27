// 사진 비교 흔들림 프로브(harness 티켓 016): 커밋한 정답 사진 가운데 창(480×320)보다 큰 것을 센다. 전체 페이지 사진이
// 창 밖까지 찍는 사진이다. 위젯의 창은 그 설정을 읽어 따로 준다.
//   node .scratch/harness/probes/visual_flake/sizes.mjs <정답 폴더> <창 폭> <창 높이>
// PNG 머리(IHDR)의 폭과 높이만 읽는다. 측정의 표지: 폴더에 PNG 가 하나 이상 있고 모두 IHDR 를 읽었다.
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const [dir, widthText, heightText] = process.argv.slice(2);
if (dir === undefined || widthText === undefined || heightText === undefined) {
  console.error("사용: node sizes.mjs <정답 폴더> <창 폭> <창 높이>");
  process.exit(2);
}
const viewport = { width: Number(widthText), height: Number(heightText) };
const names = readdirSync(dir).filter((name) => name.endsWith(".png"));
const over = [];
for (const name of names) {
  const png = readFileSync(join(dir, name));
  if (png.toString("ascii", 12, 16) !== "IHDR") {
    console.error(`IHDR 를 읽지 못했다: ${name}`);
    process.exit(1);
  }
  const width = png.readUInt32BE(16);
  const height = png.readUInt32BE(20);
  if (width > viewport.width || height > viewport.height) over.push(`${name} ${width}×${height}`);
}
console.log(`정답 ${names.length}장, 창 ${viewport.width}×${viewport.height} 보다 큰 것 ${over.length}장`);
for (const line of over) console.log(`  ${line}`);
process.exit(names.length > 0 ? 0 : 1);
