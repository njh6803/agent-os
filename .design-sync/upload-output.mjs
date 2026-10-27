// 빌드 산출(ds-bundle/)에서 디자인 시스템 아티팩트에 올릴 것만 산출 폴더로 옮기고, 그 경로 목록을 쓴다. 산출 폴더는
// `/sync-design-system` 올리기의 `record plan --local` 과 `record write --local` 이 읽는다. 그 명령은 폴더의 파일을 모두
// 보낼 후보로 세므로, ds-bundle/ 을 그대로 주면 채점 사진과 판정 파일까지 아티팩트에 보낸다(design-reverse-sync 티켓 08).
// 저장소 뿌리에서 driver 와 복사, 사용 규약 검사, `build --out ds-bundle/tokens.json` 을 마친 뒤
// `node .design-sync/upload-output.mjs <산출 폴더> <목록 JSON>`.
// 종료 코드: 0 옮겼다, 1 ds-bundle/ 에 모르는 항목이 있거나 올릴 항목 가운데 없는 것이 있다, 2 인자가 틀렸거나 저장소
// 뿌리에서 부르지 않아 ds-bundle/ 이 없거나 산출 폴더가 비지 않았거나 목록을 쓸 폴더가 없다, 3 그 밖의 오류로 읽기·복사·
// 쓰기가 멈췄다(산출 폴더가 반쯤 찼을 수 있다).
//
// 올리는 것(OUTPUT)은 번들 스킬의 업로드 허용 목록(storybook/SKILL.md 의 Upload 의 writes)에서 단독 앱의 표지
// `_ds_needs_recompile` 을 뺀 것과, 이 저장소가 더하는 기초 카드 `foundations/` 와 `tokens.json` 이다. 빼는 것(LOCAL)은
// 번들 스킬이 로컬에 남긴다고 적은 것(점으로 시작하는 항목, `_screenshots/`, `_sb/`)과 단독 Claude Design 앱의 장치
// (`_ds_needs_recompile`, 목록 타일 `thumbnail.html`)다. 둘 어디에도 없는 맨 위 항목은 번들 스킬의 판이 바뀌며 새로 생긴
// 것이라 올릴지 정하기 전에는 멈춘다. 올릴 항목이 하나라도 없어도 멈춘다. 번들 스킬은 산출 전체를 늘 보내라고 한다.
// 그 항목이 빠진 산출 폴더로 계획을 지으면 지난 산출 목록에 든 그 항목의 경로를 모두 지울 경로로 내고, 빠진 채 지은
// 목록을 커밋하면 그 경로가 지난 산출 목록에서 빠져 뒤에 코드가 그 파일을 빼도 지우지 못한다. 목록은 산출 폴더의 파일을
// 아티팩트 경로(`project/…`)로 적은 JSON 배열이고, 다음 올리기가 `record plan --previous-output` 으로 받는 지난 산출
// 목록이다(NOTES 의 "아티팩트에 올리기").
import { cpSync, existsSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";

const BUNDLE = "ds-bundle";
const OUTPUT = [
  "README.md",
  "_ds_bundle.css",
  "_ds_bundle.js",
  "_ds_sync.json",
  "_preview",
  "_vendor",
  "components",
  "fonts",
  "foundations",
  "guidelines",
  "styles.css",
  "tokens",
  "tokens.json",
];
const LOCAL = ["_screenshots", "_sb", "_ds_needs_recompile", "thumbnail.html"];

process.on("uncaughtException", (error) => {
  console.error(`읽기·복사·쓰기가 멈췄다: ${String(error)}. 산출 폴더를 지우고 한 번 다시 친다`);
  process.exit(3);
});

const [folder, list] = process.argv.slice(2);
if (folder === undefined || list === undefined) {
  console.error("사용: node .design-sync/upload-output.mjs <산출 폴더> <목록 JSON>");
  process.exit(2);
}
const out = resolve(folder);
if (existsSync(out) && readdirSync(out).length > 0) {
  console.error(`${out} 가 비지 않았다. 앞 올리기의 파일이 남으면 지금 빌드에 없는 파일을 보낸다`);
  process.exit(2);
}
if (!existsSync(dirname(resolve(list)))) {
  console.error(`${dirname(resolve(list))} 이 없다. 목록을 쓸 폴더를 먼저 만든다`);
  process.exit(2);
}
if (!existsSync(BUNDLE)) {
  console.error(`${BUNDLE}/ 이 없다. 저장소 뿌리에서 driver 를 돌린 뒤 부른다`);
  process.exit(2);
}

const entries = readdirSync(BUNDLE);
const unknown = entries.filter((name) => !name.startsWith(".") && !OUTPUT.includes(name) && !LOCAL.includes(name));
const absent = OUTPUT.filter((name) => !entries.includes(name));
if (unknown.length > 0 || absent.length > 0) {
  for (const name of unknown) console.error(`모르는 항목: ${BUNDLE}/${name} (OUTPUT 이나 LOCAL 에 넣고 까닭을 NOTES 에 적는다)`);
  for (const name of absent) console.error(`없는 항목: ${BUNDLE}/${name}`);
  process.exit(1);
}

for (const name of OUTPUT) {
  cpSync(join(BUNDLE, name), join(out, name), { recursive: true });
}
const paths = readdirSync(out, { withFileTypes: true, recursive: true })
  .filter((entry) => entry.isFile())
  .map((entry) => `project/${relative(out, join(entry.parentPath, entry.name)).split(sep).join("/")}`)
  .sort();
writeFileSync(list, `${JSON.stringify(paths, null, 2)}\n`);
console.log(JSON.stringify({ out, list: resolve(list), files: paths.length }));
