// 사진 비교 흔들림 프로브(harness 티켓 016): 두 판 사이에 바뀐 정답 사진마다 갈린 픽셀 수와 채널 차의 최댓값을 센다.
// 정답을 다시 만든 뒤 무엇이 얼마나 바뀌었는지(PR 본문)와, 픽셀은 같은데 바이트만 바뀐 사진(다시 쓸 까닭이 없는
// 사진)을 가른다.
//   node .scratch/harness/probes/visual_flake/changed_baselines.mjs <판> [<판2>]
// 판2 가 없으면 작업 트리와 맞대고, 그때는 추적하지 않는 새 사진도 적는다. 판은 `git rev-parse` 가 푸는 이름이다.
// 대는 폴더는 패키지와 위젯의 정답 폴더 둘이다. 측정의 표지: 바뀐 사진이 하나 이상이고 모두 양쪽에서 PNG 로 읽었다.
// 읽지 못한 사진이나 크기가 다른 사진이 있으면 종료 1, 바뀐 사진이 없어도 종료 1(잰 것이 없다)이다.
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { differingPixels, readPng } from "./png.mjs";

const REPO = resolve(import.meta.dirname, "..", "..", "..", "..");
const DIRS = ["web/packages/ui/visual/snapshots", "web/apps/widget/visual/snapshots"];

const [fromRev, toRev] = process.argv.slice(2);
if (fromRev === undefined) {
  console.error("사용: node changed_baselines.mjs <판> [<판2>]");
  process.exit(2);
}

const git = (gitArgs) => spawnSync("git", ["-C", REPO, ...gitArgs], { timeout: 60_000, maxBuffer: 64 * 1024 * 1024 });
const resolveRev = (rev) => {
  const found = git(["rev-parse", "--verify", `${rev}^{commit}`]);
  if (found.status !== 0) {
    console.error(`판을 커밋으로 풀지 못했다: ${rev}`);
    process.exit(2);
  }
  return found.stdout.toString().trim();
};
const from = resolveRev(fromRev);
const to = toRev === undefined ? null : resolveRev(toRev);

const lines = (result, what) => {
  if (result.status !== 0) {
    console.error(`${what} 가 실패했다: ${result.stderr.toString()}`);
    process.exit(2);
  }
  return result.stdout
    .toString()
    .split("\n")
    .filter((line) => line.endsWith(".png"));
};
const changed = lines(git(["diff", "--name-only", from, ...(to === null ? [] : [to]), "--", ...DIRS]), "git diff");
const untracked =
  to === null ? lines(git(["ls-files", "--others", "--exclude-standard", "--", ...DIRS]), "git ls-files") : [];

const blob = (rev, path) => {
  const shown = git(["show", `${rev}:${path}`]);
  return shown.status === 0 ? shown.stdout : null;
};
const side = (path) => {
  if (to !== null) return blob(to, path);
  try {
    return readFileSync(join(REPO, path));
  } catch {
    return null;
  }
};

let problems = 0;
let pixelChanged = 0;
let bytesOnly = 0;
console.log(`판 ${from.slice(0, 12)} → ${to === null ? "작업 트리" : to.slice(0, 12)}, 바뀐 사진 ${changed.length}장`);
for (const path of changed) {
  const before = blob(from, path);
  const after = side(path);
  const name = path.split("/").slice(-1)[0];
  if (before === null || after === null) {
    console.log(`  ${name}: ${before === null ? "새 사진" : "지운 사진"}`);
    continue;
  }
  let diff;
  try {
    diff = differingPixels(readPng(before, `${from}:${path}`), readPng(after, path));
  } catch (error) {
    console.log(`  ${name}: 읽지 못했다(${error instanceof Error ? error.message : String(error)})`);
    problems += 1;
    continue;
  }
  if (diff.length === 0) {
    console.log(`  ${name}: 픽셀이 같다(바이트만 다르다)`);
    bytesOnly += 1;
    continue;
  }
  // 인자 펼치기는 갈린 픽셀이 많으면 인자 수 한도에 걸린다
  const delta = diff.reduce(
    (most, { a, b }) => a.reduce((inner, value, c) => Math.max(inner, Math.abs(value - b[c])), most),
    0,
  );
  console.log(`  ${name}: ${diff.length}픽셀, 채널 차 최대 ${delta}`);
  pixelChanged += 1;
}
for (const path of untracked) console.log(`  ${path.split("/").slice(-1)[0]}: 추적하지 않는 새 사진`);
console.log(`픽셀이 바뀐 사진 ${pixelChanged}장, 바이트만 바뀐 사진 ${bytesOnly}장, 읽지 못한 사진 ${problems}장`);
process.exit(problems === 0 && changed.length + untracked.length > 0 ? 0 : 1);
