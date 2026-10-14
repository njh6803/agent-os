// 사용 규약 검사기(.design-sync/check-conventions.mjs)의 티켓 05 판정 가운데, 파일을 만들거나 지우는 변이 둘을 본다.
// 나머지 아홉은 원문 치환이라 tools/mutate.py 의 표 checker_mutations.toml 로 옮겼다(대기열 253). 이 둘은 원문
// 치환으로 표현하지 못해 여기 남는다. 저장소의 파일은 고치지 않는다. 검사기가 읽는 입력을 임시 폴더에 복사하고,
// 변이마다 새 사본을 고쳐 그 폴더를 작업 디렉터리로 검사기를 돌린다.
//
// 사용(저장소 뿌리에서, 변환기와 참조 Storybook 을 돌리고 카드를 ds-bundle/ 에 복사한 뒤):
//   node .scratch/design-refresh/probes/checker_mutations.mjs
// 기준선(변이 없음)은 0 과 검사기의 집계 줄이, 변이마다 1 과 기대한 메시지가 나와야 한다. 원문을 찾지 못하면 던진다.
// 하나라도 어긋나면 1 로 끝난다.
import { spawnSync } from "node:child_process";
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const INPUTS = [
  ".design-sync/conventions.md",
  ".design-sync/config.json",
  ".design-sync/check-conventions.mjs",
  ".design-sync/foundations",
  ".design-sync/thumbnail.html",
  ".design-sync/sb-reference/index.json",
  "ds-bundle/_ds_bundle.css",
  "ds-bundle/_ds_bundle.js",
  "ds-bundle/components",
  "ds-bundle/foundations",
  "ds-bundle/thumbnail.html",
];

/** 변이: 이름, 고칠 파일과 원문·새 글, 기대한 메시지의 조각. edits 가 비면 기준선이다. */
const MUTATIONS = [
  { name: "기준선", edits: [], expect: null, marker: "빼는 목록이 맞다: 컴포넌트 9" },
  {
    name: "기초 카드 폴더에 HTML 이 둘이다",
    extraFile: [".design-sync/foundations/colors/extra.html", "<!-- @dsCard group=\"Colors\" -->\n"],
    edits: [],
    expect: "기초 카드 폴더의 HTML 이 하나가 아니다: colors (2)",
  },
  {
    name: "기초 카드 폴더 하나를 원본과 사본에서 함께 지운다",
    removeDirs: [".design-sync/foundations/density", "ds-bundle/foundations/density"],
    edits: [],
    expect: "기초 카드 폴더가 없다: density",
  },
];

let failed = 0;
for (const mutation of MUTATIONS) {
  const dir = mkdtempSync(join(tmpdir(), "checker-mut-"));
  try {
    for (const input of INPUTS) cpSync(input, join(dir, input), { recursive: true });
    if (mutation.extraFile !== undefined) writeFileSync(join(dir, mutation.extraFile[0]), mutation.extraFile[1]);
    for (const removed of mutation.removeDirs ?? []) rmSync(join(dir, removed), { recursive: true });
    for (const [file, oldText, newText, mode] of mutation.edits) {
      const path = join(dir, file);
      const text = readFileSync(path, "utf8");
      if (!text.includes(oldText)) throw new Error(`${mutation.name}: 원문이 없다 ${file}: ${oldText}`);
      writeFileSync(path, mode === "all" ? text.replaceAll(oldText, newText) : text.replace(oldText, newText));
    }
    // 카드 변수·첫 줄·선택자 변이는 복사 판정에 먼저 걸리지 않게 ds-bundle 사본도 같이 고친다.
    if (mutation.copyCard !== undefined) {
      const card = `foundations/${mutation.copyCard}/index.html`;
      cpSync(join(dir, ".design-sync", card), join(dir, "ds-bundle", card));
    }
    if (mutation.copyThumb === true) cpSync(join(dir, ".design-sync/thumbnail.html"), join(dir, "ds-bundle/thumbnail.html"));
    const result = spawnSync(process.execPath, [".design-sync/check-conventions.mjs"], { cwd: dir, encoding: "utf8" });
    const output = `${result.stdout}${result.stderr}`;
    // 기준선도 종료 코드만 보지 않고 검사기의 집계 줄(빼는 목록을 센 표지)을 본다. 변이는 기대한 메시지가 표지다.
    const ok =
      mutation.expect === null
        ? result.status === 0 && output.includes(mutation.marker)
        : result.status === 1 && output.includes(mutation.expect);
    if (!ok) failed += 1;
    console.log(`${ok ? "맞다" : "어긋난다"}  ${mutation.name}  (종료 ${result.status})`);
    if (!ok) console.log(output.trim().split("\n").map((line) => `    ${line}`).join("\n"));
  } finally {
    // 윈도에서 백신·색인기가 파일을 잡으면 EBUSY 로 던질 수 있어 몇 번 다시 시도한다(force 는 그것을 막지 않는다).
    rmSync(dir, { recursive: true, force: true, maxRetries: 3 });
  }
}
console.log(failed === 0 ? `변이 ${MUTATIONS.length - 1}개가 모두 기대대로다` : `어긋난 것 ${failed}`);
process.exit(failed === 0 ? 0 : 1);
