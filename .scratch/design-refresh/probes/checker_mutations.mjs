// 사용 규약 검사기(.design-sync/check-conventions.mjs)의 티켓 05 판정(빼는 목록, 기초 카드와 목록 타일, data-density)이
// 빨개지는 것을 변이로 본다. tools/mutate.py 의 판정(pytest, vitest, playwright, tsc)에는 종료 코드로 말하는 node 검사기가
// 없어 여기 따로 둔다. 저장소의 파일은 고치지 않는다. 검사기가 읽는 입력을 임시 폴더에 복사하고, 변이마다 새 사본을 고쳐
// 그 폴더를 작업 디렉터리로 검사기를 돌린다.
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
    name: "변형 스토리 하나를 빼는 목록에서 걷는다",
    edits: [[".design-sync/config.json", '        "atoms-button--narrow-row"\n', ""], [".design-sync/config.json", '"atoms-button--focus",', '"atoms-button--focus"']],
    expect: "변형 스토리가 빼는 목록에 없다: Button atoms-button--narrow-row",
  },
  {
    name: "빼는 목록에 없는 스토리 id 를 든다",
    edits: [[".design-sync/config.json", '"atoms-card--default",', '"atoms-card--default",\n        "atoms-card--gone",']],
    expect: "빼는 목록의 스토리가 없다: Card atoms-card--gone",
  },
  {
    name: "보여 주기용 스토리를 빼는 목록에 든다",
    edits: [[".design-sync/config.json", '"atoms-icon--decorative",', '"atoms-icon--decorative",\n        "atoms-icon--showcase-nav-items",']],
    expect: "보여 주기용 스토리를 뺀다: Icon atoms-icon--showcase-nav-items",
  },
  {
    name: "컴포넌트의 보여 주기용 태그를 모두 걷는다",
    edits: [[".design-sync/sb-reference/index.json", '"showcase"]', '"other"]', "all"]],
    expect: "보여 주기용 스토리가 없다: Button",
  },
  {
    name: "기초 카드가 없는 변수를 읽는다",
    edits: [[".design-sync/foundations/spacing/index.html", "var(--radius-s)", "var(--radius-xs)"]],
    copyCard: "spacing",
    expect: "카드의 변수가 없다: --radius-xs",
  },
  {
    name: "기초 카드의 첫 줄이 @dsCard 가 아니다",
    edits: [[".design-sync/foundations/type/index.html", '<!-- @dsCard group="Type" -->\n', ""]],
    copyCard: "type",
    expect: "첫 줄이 @dsCard 가 아니다",
  },
  {
    name: "기초 카드 폴더에 HTML 이 둘이다",
    extraFile: [".design-sync/foundations/colors/extra.html", "<!-- @dsCard group=\"Colors\" -->\n"],
    edits: [],
    expect: "기초 카드 폴더의 HTML 이 하나가 아니다: colors (2)",
  },
  {
    name: "목록 타일이 없는 테마를 단다",
    edits: [[".design-sync/thumbnail.html", 'data-theme="jacho"', 'data-theme="jadu"']],
    copyThumb: true,
    expect: "data-theme 선택자가 없다: jadu",
  },
  {
    name: "카드를 ds-bundle 에 복사하지 않았다",
    edits: [[".design-sync/foundations/density/index.html", "<h1>", "<h1 data-x>"]],
    expect: "ds-bundle 에 복사되지 않았다",
  },
  {
    name: "규약이 없는 밀도 키를 든다",
    edits: [[".design-sync/conventions.md", "`data-density`(`compact` 촘촘", "`data-density`(`dense` 촘촘"]],
    expect: "data-density 선택자가 없다: dense",
  },
];

let failed = 0;
for (const mutation of MUTATIONS) {
  const dir = mkdtempSync(join(tmpdir(), "checker-mut-"));
  try {
    for (const input of INPUTS) cpSync(input, join(dir, input), { recursive: true });
    if (mutation.extraFile !== undefined) writeFileSync(join(dir, mutation.extraFile[0]), mutation.extraFile[1]);
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
    rmSync(dir, { recursive: true, force: true });
  }
}
console.log(failed === 0 ? `변이 ${MUTATIONS.length - 1}개가 모두 기대대로다` : `어긋난 것 ${failed}`);
process.exit(failed === 0 ? 0 : 1);
