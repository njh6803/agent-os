// 사진 비교 흔들림 프로브(harness 티켓 016): 정답을 다시 쓴 두 판 사이에 바뀐 사진마다, 부분 래스터를 켠 채(인자 없이)
// 찍은 그림이 옛 정답과 새 정답 가운데 어느 쪽과 바이트까지 같은지 가른다. 바뀐 정답의 까닭(PR 본문)을 잰다.
//   node .scratch/harness/probes/visual_flake/attribution.mjs <옛 판> <새 판> <그림 폴더> <실행 기록> [<실행 기록> ...]
// <그림 폴더> 는 인자 없이 정답을 전부 다시 쓴(`--update-snapshots=all`) 뒤, 두 정답 폴더를 저장소와 같은 상대 경로로
// 복사한 폴더다(<그림 폴더>/web/packages/ui/visual/snapshots, <그림 폴더>/web/apps/widget/visual/snapshots). 인자 없이
// 찍으려면 두 설정의 `launchOptions` 를 `{ args: [] }` 로 바꾸고 `pnpm -C web visual --update-snapshots=all` 과
// `pnpm -C web visual:widget --update-snapshots=all` 을 친다(변이 표의 설정 변이와 같은 편집). <실행 기록> 은 그 두 실행의
// 출력이다. 정답은 작업 트리가 아니라 두 판에서 읽는다(probes 규칙).
//
// 갈래는 셋이다. 옛 정답과 같으면 인자가 그 그림을 바꾼 것이다. 새 정답과 같으면 이 PC 에서는 인자 없이도 새 그림이
// 찍혔고, 옛 정답은 다른 때(다른 기계나 다른 회차)의 그림이다. 둘 다 아니면 인자로 설명되지 않는다. 바뀌지 않은 정답과
// 인자 없는 그림이 다른 사진도 따로 센다.
//
// 측정의 표지: 실행 기록마다 실행 인자 시험이 받지 못한 인자를 Received 차이 줄로 찍었고(그 실행의 브라우저가 인자 없이
// 떴다), 실패는 그 시험 하나뿐이며 통과 줄이 있다. 다른 시험이 실패하면 그 사진은 다시 쓰이지 않아 새 정답 그대로 남으므로
// 측정이 아니다. 표지가 어긋난 기록이 있거나, 두 판의 정답이 그림 폴더에 없으면 종료 코드가 1 이다.
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const REPO = resolve(import.meta.dirname, "..", "..", "..", "..");
const DIRS = ["web/packages/ui/visual/snapshots", "web/apps/widget/visual/snapshots"];
const ARGS_MARKER = '+   "--disable-partial-raster",';
const ARGS_TEST = "실행 인자를 모두";

const [oldRev, newRev, rendersDir, ...logs] = process.argv.slice(2);
if (rendersDir === undefined || logs.length === 0) {
  console.error("사용: node attribution.mjs <옛 판> <새 판> <그림 폴더> <실행 기록> [<실행 기록> ...]");
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
// 판의 정답 사진마다 git 의 blob id. 그림의 바이트도 같은 방식으로 셈해 바이트가 같은지 본다.
const blobIds = (commit) => {
  const listed = git(["ls-tree", "-r", commit, "--", ...DIRS]);
  const ids = new Map();
  for (const line of listed.stdout.toString().split("\n")) {
    const match = /^\d+ blob ([0-9a-f]+)\t(.+\.png)$/.exec(line);
    if (match !== null) ids.set(match[2], match[1]);
  }
  return ids;
};
const blobIdOf = (bytes) =>
  createHash("sha1").update(`blob ${bytes.length}\0`).update(bytes).digest("hex");

let notMeasured = 0;
for (const log of logs) {
  const text = existsSync(log) ? readFileSync(log, "utf-8") : "";
  const lines = text.split(/\r?\n/);
  const failedAt = lines.findIndex((line) => /^\s+\d+ failed$/.test(line));
  const failedCount = failedAt === -1 ? 0 : Number(/(\d+)/.exec(lines[failedAt])?.[1]);
  const failedTitles = failedAt === -1 ? [] : lines.slice(failedAt + 1, failedAt + 1 + failedCount);
  const others = lines.filter((line) => /^\s+\d+ (flaky|interrupted|skipped|did not run)/.test(line));
  const passed = lines.some((line) => /^\s+\d+ passed/.test(line));
  const ok =
    text.includes(ARGS_MARKER) &&
    failedCount === 1 &&
    failedTitles.every((title) => title.includes(ARGS_TEST)) &&
    others.length === 0 &&
    passed;
  if (!ok) {
    notMeasured += 1;
    console.log(
      `측정 아님: ${log} (인자 표지 ${String(text.includes(ARGS_MARKER))}, 실패 ${failedCount}, 그 밖 ${others.length}, 통과 줄 ${String(passed)})`,
    );
  }
}

const oldCommit = resolveRev(oldRev);
const newCommit = resolveRev(newRev);
const oldIds = blobIds(oldCommit);
const newIds = blobIds(newCommit);
const groups = { "옛 정답과 같다": [], "새 정답과 같다": [], "둘 다 아니다": [] };
const unchangedDiffer = [];
const onlyOneSide = [];
for (const [path, newId] of newIds) {
  const oldId = oldIds.get(path);
  if (oldId === undefined) {
    onlyOneSide.push(path);
    continue;
  }
  const renderPath = join(rendersDir, path);
  if (!existsSync(renderPath)) {
    notMeasured += 1;
    console.log(`측정 아님: 그림 폴더에 없다: ${path}`);
    continue;
  }
  const renderId = blobIdOf(readFileSync(renderPath));
  if (oldId === newId) {
    if (renderId !== oldId) unchangedDiffer.push(path);
    continue;
  }
  const group = renderId === oldId ? "옛 정답과 같다" : renderId === newId ? "새 정답과 같다" : "둘 다 아니다";
  groups[group].push(path);
}
for (const path of oldIds.keys()) {
  if (!newIds.has(path)) onlyOneSide.push(path);
}

const name = (path) => path.slice(path.lastIndexOf("/") + 1);
console.log(`옛 판 ${oldCommit.slice(0, 8)}, 새 판 ${newCommit.slice(0, 8)}`);
for (const [group, paths] of Object.entries(groups)) {
  console.log(`${group}: ${paths.length}`);
  for (const path of paths) console.log(`  ${name(path)}`);
}
console.log(`바뀌지 않은 정답과 인자 없는 그림이 다르다: ${unchangedDiffer.length}`);
for (const path of unchangedDiffer) console.log(`  ${name(path)}`);
if (onlyOneSide.length > 0) console.log(`한쪽 판에만 있는 사진(셈에서 뺐다): ${onlyOneSide.length}`);
console.log(
  JSON.stringify({
    oldCommit,
    newCommit,
    counts: Object.fromEntries(Object.entries(groups).map(([group, paths]) => [group, paths.length])),
    unchangedDiffer: unchangedDiffer.length,
    notMeasured,
  }),
);
process.exit(notMeasured === 0 ? 0 : 1);
