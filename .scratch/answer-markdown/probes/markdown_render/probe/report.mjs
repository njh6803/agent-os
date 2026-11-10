// render.mjs 가 남긴 out/render/summary.json 을 사람이 읽는 글(out/render/report.txt)로 편다. 재지 않고 옮기기만 한다.
// 돌리기: node probe/report.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const data = JSON.parse(readFileSync(join(ROOT, "out", "render", "summary.json"), "utf8"));
const lines = [];
const ids = [...new Set(data.rounds.map((r) => r.id))];
for (const id of ids) {
  const mine = data.rounds.filter((r) => r.id === id);
  lines.push(`## ${id}`, `입력: ${JSON.stringify(mine[0].input)}`);
  for (const r of mine) {
    lines.push(
      `- ${r.candidate} / ${r.mode}`,
      `  html: ${r.html}`,
      `  watch: ${JSON.stringify(r.watch)}`,
      ...(r.violations.length > 0 ? [`  violations: ${JSON.stringify(r.violations)}`] : []),
      ...(r.mustFailures.length > 0 ? [`  must: ${JSON.stringify(r.mustFailures)}`] : []),
      ...(r.reactWarnings.length > 0 ? [`  reactWarnings: ${JSON.stringify(r.reactWarnings)}`] : []),
    );
  }
  lines.push("");
}
writeFileSync(join(ROOT, "out", "render", "report.txt"), lines.join("\n"));
console.log(JSON.stringify({ probe: "report", cases: ids.length, rounds: data.rounds.length }));
