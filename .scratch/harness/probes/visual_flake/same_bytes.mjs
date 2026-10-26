// 사진 비교 흔들림 프로브(harness 티켓 016): CI 가 실패하며 올린 실제 그림(-actual)이 run.mjs 의 어느 실행이 남긴
// B 사진과 바이트까지 같은지 찾는다. 원인의 양성 대조다. 부분 래스터를 끈 실행(summary.json 의 partialOff 가 true)의
// B 사진과 같으면, CI 의 흔들린 그림은 부분 래스터를 끈 그림이다.
//   node .scratch/harness/probes/visual_flake/same_bytes.mjs <CI 아티팩트를 푼 폴더> [--baseline <판>] [<run.mjs 의 --out 폴더> ...]
// --baseline 을 주면 CI 의 실제 그림마다 그 판에 커밋한 같은 이름의 정답 사진(`-actual` 을 뗀 이름)과도 바이트를
// 맞댄다. 고친 뒤의 정답이 CI 의 흔들린 그림 그대로인지 본다. 정답은 작업 트리가 아니라 판에서 꺼낸다(probes 규칙).
// 측정의 표지: 넘긴 --out 폴더마다 summary.json 과 shots/ 가 있고, --baseline 이면 그 판에 같은 이름의 정답이 있다.
// 없는 것이 하나라도 있거나 CI 의 실제 그림이 하나도 없으면 종료 코드가 1 이다. CI 의 실제 그림마다, 같은 바이트의
// 사진을 찾은 실행과 그 실행의 partialOff 를 찍는다.
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(path);
    else yield path;
  }
}
const digestOf = (bytes) => createHash("sha256").update(bytes).digest("hex");
const sha = (path) => digestOf(readFileSync(path));

const [ciRoot, ...rest] = process.argv.slice(2);
const at = rest.indexOf("--baseline");
const baselineRev = at === -1 ? null : rest[at + 1];
const outs = at === -1 ? rest : rest.filter((_, index) => index !== at && index !== at + 1);
if (ciRoot === undefined || baselineRev === undefined || (outs.length === 0 && baselineRev === null)) {
  console.error("사용: node same_bytes.mjs <CI 아티팩트 폴더> [--baseline <판>] [<run.mjs --out 폴더> ...]");
  process.exit(2);
}

const REPO = resolve(import.meta.dirname, "..", "..", "..", "..");
const SNAPSHOTS = "web/packages/ui/visual/snapshots";
const git = (gitArgs) => spawnSync("git", ["-C", REPO, ...gitArgs], { timeout: 60_000, maxBuffer: 64 * 1024 * 1024 });
let baselineCommit = null;
if (baselineRev !== null) {
  const found = git(["rev-parse", "--verify", `${baselineRev}^{commit}`]);
  if (found.status !== 0) {
    console.error(`--baseline 을 커밋으로 풀지 못했다: ${baselineRev}`);
    process.exit(2);
  }
  baselineCommit = found.stdout.toString().trim();
}

let notMeasured = 0;
const shots = new Map();
for (const out of outs) {
  const summaryPath = join(out, "summary.json");
  if (!existsSync(summaryPath) || !existsSync(join(out, "shots"))) {
    console.log(`측정 아님: ${out} 에 summary.json 이나 shots/ 가 없다`);
    notMeasured += 1;
    continue;
  }
  const { partialOff } = JSON.parse(readFileSync(summaryPath, "utf-8"));
  for (const path of walk(join(out, "shots"))) {
    const digest = sha(path);
    const found = shots.get(digest) ?? [];
    found.push(`${basename(out)}/${basename(path)} (부분 래스터 끔 ${String(partialOff)})`);
    shots.set(digest, found);
  }
}
let actuals = 0;
for (const path of walk(ciRoot)) {
  if (!path.endsWith("-actual.png")) continue;
  actuals += 1;
  const digest = sha(path);
  const found = shots.get(digest) ?? [];
  console.log(`${basename(path)} ${digest.slice(0, 12)}: 같은 바이트 ${found.length}장`);
  for (const line of found.slice(0, 4)) console.log(`  ${line}`);
  if (found.length > 4) console.log(`  … ${found.length - 4}장 더`);
  if (baselineCommit !== null) {
    const name = basename(path).replace(/-actual\.png$/, ".png");
    const blob = git(["show", `${baselineCommit}:${SNAPSHOTS}/${name}`]);
    if (blob.status !== 0) {
      console.log(`  측정 아님: ${baselineCommit.slice(0, 12)} 에 정답 ${name} 이 없다`);
      notMeasured += 1;
    } else {
      const same = digestOf(blob.stdout) === digest;
      console.log(`  정답(${baselineCommit.slice(0, 12)}) ${name}: ${same ? "같은 바이트" : "다른 바이트"}`);
    }
  }
}
if (actuals === 0) console.log(`측정 아님: ${ciRoot} 에 -actual.png 가 없다`);
process.exit(notMeasured === 0 && actuals > 0 ? 0 : 1);
