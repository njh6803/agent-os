// 아티팩트에서 읽은 파일의 sha256(Artifact 도구가 낸 값)과 저장소 사본의 sha256을 맞대 같은 판인지 본다.
//
// 기록 파일(기본은 이 폴더의 `artifact_reads.json`)의 줄마다 저장소 쪽 바이트를 구해 sha256을 새로 세고, 기록의
// 값과 같으면 "같다"다. 저장소 쪽은 줄의 `commit`이 있으면 `git show <commit>:<repo>`로 그 커밋의 바이트를 꺼내고,
// `commit`이 null이면 작업 트리의 파일을 읽는다. 아티팩트에서 읽은 그때의 저장소와 맞대야 하므로, 나중에 저장소
// 파일이 바뀌어도 결과가 바뀌지 않게 커밋을 적는다. 줄의 `expect`가 기대다. "same"은 같은 판이어야 하는 짝(양성),
// "differ"는 달라야 하는 짝(음성 대조: 대조기가 다른 것을 다르다고 내는지)이다. 저장소 쪽을 구하지 못하거나 기록에
// 판 id·64자리 sha256이 없는 줄은 측정이 아니라고 따로 센다.
//
// `--saved <폴더>`로 아티팩트에서 받은 파일의 폴더(Artifact 도구 read의 out_dir, 그 아래 `project/...`)를 주면, 받은
// 바이트의 sha256도 세어 도구가 낸 값과 같은지 본다(도구의 해시가 실제 바이트의 해시라는 대조). 판이 둘 이상인
// 경로는 기록에서 마지막 판만 대조하므로 그 폴더는 그 판에서 받은 것이어야 한다.
//
// 다른 기능이 쓸 때는 자기 probes 폴더에 기록 파일을 새로 두고 `--record`로 준다. 이 기능의 기록을 덮어쓰지 않는다.
//
// 저장소 루트에서 돈다:
//   node .scratch/design-artifacts/probes/hash_match.mjs [--record <기록 파일>] [--saved <받은 파일 폴더>]
// 종료 코드: 모든 줄이 측정이고 기대대로면 0, 아니면 1.

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
const option = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};
const recordPath = option("--record") ?? ".scratch/design-artifacts/probes/artifact_reads.json";
const savedDir = option("--saved");

const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex");
const isHex64 = (s) => typeof s === "string" && /^[0-9a-f]{64}$/.test(s);

/** 저장소 쪽 바이트. 구하지 못하면 null. */
function repoBytes(row) {
  if (row.commit) {
    try {
      return execFileSync("git", ["show", `${row.commit}:${row.repo}`], { maxBuffer: 64 * 1024 * 1024 });
    } catch {
      return null;
    }
  }
  return existsSync(row.repo) ? readFileSync(row.repo) : null;
}

const record = JSON.parse(readFileSync(recordPath, "utf8"));
let notMeasured = 0;
let unexpected = 0;
let measured = 0;

console.log(`기록: ${recordPath} (${record.artifact})`);
for (const row of record.reads) {
  const where = row.commit ? `${row.commit}:${row.repo}` : `작업 트리 ${row.repo}`;
  const label = `${row.version} ${row.path} ↔ ${where}`;
  const bytes = repoBytes(row);
  if (!row.version || !isHex64(row.sha256) || bytes === null || !["same", "differ"].includes(row.expect)) {
    notMeasured += 1;
    console.log(`측정 아님  ${label} (판 id·sha256·저장소 쪽 바이트·기대(same, differ) 가운데 빠지거나 틀린 것이 있다)`);
    continue;
  }
  measured += 1;
  const same = sha256(bytes) === row.sha256;
  const ok = (row.expect === "same") === same;
  if (!ok) unexpected += 1;
  console.log(`${ok ? "기대대로" : "기대와 다름"}  ${same ? "같다" : "다르다"} (기대 ${row.expect})  ${label}`);
}

if (savedDir) {
  const latest = new Map();
  for (const row of record.reads) latest.set(row.path, row);
  for (const row of latest.values()) {
    const saved = join(savedDir, row.path);
    if (!existsSync(saved)) {
      notMeasured += 1;
      console.log(`측정 아님  받은 파일 없음 ${saved}`);
      continue;
    }
    measured += 1;
    const ok = sha256(readFileSync(saved)) === row.sha256;
    if (!ok) unexpected += 1;
    console.log(`${ok ? "기대대로" : "기대와 다름"}  받은 바이트의 sha256 ${ok ? "=" : "≠"} 도구가 낸 값  ${row.path} (${row.version})`);
  }
}

console.log(`집계: 측정 ${measured}, 측정 아님 ${notMeasured}, 기대와 다름 ${unexpected}`);
process.exit(notMeasured === 0 && unexpected === 0 && measured > 0 ? 0 : 1);
