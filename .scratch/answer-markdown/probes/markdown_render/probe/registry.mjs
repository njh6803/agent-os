// 레지스트리 프로브(B1 의 보탬). 설치한 판이 언제 나왔고 그 뒤로 얼마나 자주 새 판이 나오는지 본다. 공급망 유예
// (pnpm 의 minimumReleaseAge, 예외를 두지 않는다는 ADR 0024)와 잠금 파일이 얼마나 자주 흔들릴지의 근거다.
//
// 돌리기: node probe/registry.mjs      (레지스트리 https://registry.npmjs.org/ 에 읽기 요청 넷을 보낸다)
// 산출물: out/registry/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
// 측정이 아닌 회차: 응답에 설치한 판의 시각이 없으면 그 패키지는 잰 것이 아니다. 종료 코드 1.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "registry");
const PACKAGES = ["react-markdown", "remark-gfm", "markdown-to-jsx", "marked"];
const DAY = 24 * 60 * 60 * 1000;

mkdirSync(OUT, { recursive: true });
const now = Date.now();
const rows = [];
const notMeasured = [];
for (const name of PACKAGES) {
  const installed = JSON.parse(readFileSync(join(ROOT, "node_modules", name, "package.json"), "utf8")).version;
  const response = await fetch(`https://registry.npmjs.org/${name}`);
  if (!response.ok) {
    notMeasured.push({ name, status: response.status });
    continue;
  }
  const doc = await response.json();
  const releasedAt = doc.time?.[installed];
  if (typeof releasedAt !== "string") {
    notMeasured.push({ name, reason: "설치한 판의 시각이 없다" });
    continue;
  }
  const stable = Object.entries(doc.time)
    .filter(([version]) => /^\d+\.\d+\.\d+$/.test(version))
    .map(([version, at]) => ({ version, at }))
    .sort((a, b) => a.at.localeCompare(b.at));
  const within = (days) => stable.filter((r) => now - Date.parse(r.at) <= days * DAY).length;
  rows.push({
    name,
    installed,
    installedReleasedAt: releasedAt,
    installedAgeDays: Math.floor((now - Date.parse(releasedAt)) / DAY),
    latest: doc["dist-tags"]?.latest,
    latestReleasedAt: doc.time?.[doc["dist-tags"]?.latest],
    stableReleasesLast90Days: within(90),
    stableReleasesLast365Days: within(365),
    lastFive: stable.slice(-5),
  });
}
writeFileSync(join(OUT, "summary.json"), JSON.stringify({ at: new Date(now).toISOString(), notMeasured, rows }, null, 2));
console.log(JSON.stringify({ probe: "registry", at: new Date(now).toISOString(), notMeasured, rows: rows.map(({ lastFive, ...row }) => row) }));
if (notMeasured.length > 0) process.exit(1);
