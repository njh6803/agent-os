// 내려받은 HTML 원문에서 스크립트와 태그를 빼고, 주어진 구절마다 처음 나오는 자리를 앞뒤 160자와 함께 보인다.
//
// 공식 안내 문서의 문장을 웹 요약이 아니라 원문으로 대 볼 때 쓴다. 구절이 하나라도 없으면 1로 끝난다.
//
// 원문은 저장소 밖 작업 폴더에 먼저 받는다: curl -sL <주소> -o <작업 폴더>/page.html
// 저장소 루트에서: node .scratch/design-artifacts/probes/find_sentences.mjs <작업 폴더>/page.html "구절" ["구절" ...]
import { readFileSync } from "node:fs";

const [file, ...needles] = process.argv.slice(2);
const text = readFileSync(file, "utf8")
  .replace(/<script[\s\S]*?<\/script>/g, " ")
  .replace(/<[^>]+>/g, " ")
  .replace(/&#x27;/g, "'")
  .replace(/&quot;/g, '"')
  .replace(/&amp;/g, "&")
  .replace(/\s+/g, " ");

let missing = 0;
for (const n of needles) {
  const i = text.indexOf(n);
  if (i < 0) missing += 1;
  console.log(`[${n}] ${i < 0 ? "없음" : "… " + text.slice(Math.max(0, i - 160), i + n.length + 160) + " …"}`);
}
console.log(`집계: 구절 ${needles.length}, 없음 ${missing}`);
process.exit(needles.length > 0 && missing === 0 ? 0 : 1);
