// `flow.mjs` 가 남긴 out/flow/summary.json 을 읽어 묶음마다 표로 찍는다. 재지 않고 읽기만 한다.
//
// 돌리기: node probe/report.mjs [--reasons]   (먼저 node probe/flow.mjs 를 돌린다. --reasons 는 고장 회차마다 거부의 까닭도 찍는다)
// 요약 파일이 없거나 측정이 아닌 회차가 적혀 있으면 종료 코드 1.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const summary = JSON.parse(readFileSync(join(ROOT, "out", "flow", "summary.json"), "utf8"));
const rows = summary.rows;
const VARIANTS = ["가-기본", "가-서명", "나-기본", "나-자체서명", "나-jose", "다"];

// 결과를 내지 못한 회차(openssl 이 없을 때의 tls 묶음 등)는 `outcome` 과 `idpLog` 가 null 이다. 그 회차를 거부로 찍거나
// 예외로 죽지 않고 "결과 없음"·"기록 없음"으로 찍어, 끝의 측정이 아닌 회차 목록까지 간다.
const cell = (row) =>
  row === undefined ? "-" : row.outcome === "accepted" ? `통과(sub 일치 ${String(row.subMatches)})` : row.outcome === "rejected" ? "거부" : "결과 없음";
/** 가짜 서버가 받은 설정 문서·공개 키·토큰 요청 수. */
const requests = (row) => (row.idpLog === null ? "기록 없음" : `${String(row.idpLog.discovery)}·${String(row.idpLog.jwks)}·${String(row.idpLog.token)}`);

console.log(`node ${summary.node}, 회차 ${String(summary.rounds)}, 측정 아님 ${String(summary.notMeasured.length)}`);
console.log(`tls: ${JSON.stringify(summary.tls)}`);

console.log("\n[good] 변형 | 결과 | 설정 문서·공개 키·토큰 요청 수 | 전역 fetch | stderr 줄");
for (const row of rows.filter((item) => item.id.startsWith("good/"))) {
  console.log(`${row.id} | ${cell(row)} | ${requests(row)} | ${String(row.globalFetchCalls)} | ${String(row.stderrLineCount)}`);
}

console.log("\n[fault] 고장 | " + VARIANTS.join(" | "));
const faults = [...new Set(rows.filter((item) => item.id.startsWith("fault/")).map((item) => item.id.split("/")[1]))];
for (const fault of faults) {
  console.log(`${fault} | ${VARIANTS.map((variant) => cell(rows.find((item) => item.id === `fault/${fault}/${variant}`))).join(" | ")}`);
}
if (process.argv.includes("--reasons")) {
  console.log("\n[fault] 거부의 까닭(오류와 그 원인 사슬)");
  for (const row of rows.filter((item) => item.id.startsWith("fault/") && item.outcome === "rejected")) {
    console.log(`${row.id} | 공개 키 요청 ${String(row.idpLog?.jwks)} | ${row.error.join(" <- ").slice(0, 260)}`);
  }
}

for (const group of ["callback", "provider", "insecure", "transport", "tls"]) {
  console.log(`\n[${group}] 회차 | 결과 | 단계 | 설정 문서·공개 키·토큰 요청 수 | 전역 fetch | nodeFetch | stderr 줄 | 까닭`);
  for (const row of rows.filter((item) => item.id.startsWith(`${group}/`))) {
    console.log(
      `${row.id} | ${cell(row)} | ${row.stage ?? ""} | ${requests(row)} | ${String(row.globalFetchCalls)} | ${String(row.nodeFetchCalls)} | ${String(row.stderrLineCount)} | ${row.error === null ? "" : row.error.join(" <- ").slice(0, 260)}`,
    );
  }
}
const provider = rows.find((item) => item.id.startsWith("provider/"));
if (provider !== undefined) {
  console.log("\n[provider] 첫 회차의 stderr 머리");
  for (const line of provider.stderrHead) console.log(`  ${line}`);
}
if (summary.notMeasured.length > 0) {
  console.log(`\n측정이 아닌 회차: ${JSON.stringify(summary.notMeasured)}`);
  process.exit(1);
}
