// 요금제 페이지(claude.com/pricing) 원문에서 표마다 머리 칸과, 이름으로 고른 행의 칸 값(yes/no 아이콘이나 글자)을 뽑는다.
//
// 아이콘은 칸 안 span의 CSS 모듈 클래스 이름 끝(`__yes`, `__no`)으로 가른다. 2026-10-16에 내려받은 원문에서 그
// 모양을 보고 적었다. 고른 행을 못 찾거나, 찾은 행에 아이콘도 글자도 아닌 칸(`?`)이 있으면 측정이 아니므로 1로 끝난다.
//
// 원문은 저장소 밖 작업 폴더에 먼저 받는다: curl -sL https://claude.com/pricing -o <작업 폴더>/pricing.html
// 저장소 루트에서: node .scratch/design-artifacts/probes/pricing_rows.mjs <작업 폴더>/pricing.html "Project sharing and collaboration" "Claude Design"
import { readFileSync } from "node:fs";

const html = readFileSync(process.argv[2], "utf8");
const rowNames = process.argv.slice(3);
const tables = html
  .split("<table")
  .slice(1)
  .map((t) => t.split("</table>")[0]);

const text = (s) =>
  s
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();

const found = new Set();
let unreadable = 0;
tables.forEach((t, i) => {
  const head = (t.split("</thead>")[0].match(/<th[\s\S]*?<\/th>/g) ?? []).map(text);
  const rows = t.match(/<tr[\s\S]*?<\/tr>/g) ?? [];
  for (const row of rows) {
    const name = text((row.match(/<th[\s\S]*?<\/th>/) ?? [""])[0]);
    const wanted = rowNames.find((n) => name.startsWith(n));
    if (wanted === undefined) continue;
    found.add(wanted);
    const cells = (row.match(/<td[\s\S]*?<\/td>/g) ?? []).map((c) => {
      if (/__yes/.test(c)) return "yes";
      if (/__no/.test(c)) return "no";
      return text(c) || "?";
    });
    unreadable += cells.filter((c) => c === "?").length;
    console.log(`표 ${i}: 머리=${JSON.stringify(head)} | ${name} = ${JSON.stringify(cells)}`);
  }
});

const missing = rowNames.filter((n) => !found.has(n));
console.log(
  `집계: 고른 행 ${rowNames.length}, 찾은 행 ${found.size}, 못 찾은 행 ${JSON.stringify(missing)}, 읽지 못한 칸 ${unreadable}`,
);
process.exit(rowNames.length > 0 && missing.length === 0 && unreadable === 0 ? 0 : 1);
