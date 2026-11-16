// 옮기기 전과 뒤의 위젯 Storybook 정적 빌드의 index.json 을 견준다(README "다시 돌리는 법" 4).
//
// 사진 비교의 정답 사진 이름은 `<스토리 id>-<모드>.png` 다(web/apps/widget/visual/stories.visual.ts). 스토리 id 가 옮긴
// 뒤에도 같으면 정답 사진의 이름이 바뀌지 않는다. 이 스크립트는 스토리 id 의 집합이 같은지와, 뒤의 빌드가 스토리를
// 실제로 새 패키지에서 실었는지(importPath)를 함께 본다. 뒤의 것이 옮기기 전 빌드를 다시 읽은 것이면 importPath 가
// 패키지를 가리키지 않아 측정이 아니라고 보고 2 로 끝난다.
//
// 종료 코드: 0 은 스토리 id 와 judgment 태그가 같다, 1 은 측정했는데 다르다, 2 는 측정이 아니다(쓰기가 틀렸다, 파일을
// index.json 으로 읽지 못했다, 위의 표지가 없다). 같은 폴더의 css_rules.mjs 와 preview_shield.mjs 가 같은 가름을 쓴다.
//
// 쓰기: node compare_index.mjs <옮기기 전 index.json> <옮긴 뒤 index.json>
import { readFileSync } from "node:fs";

const PACKAGE = "packages/widget-ui/src/";

const [beforePath, afterPath] = process.argv.slice(2);
if (beforePath === undefined || afterPath === undefined) {
  console.error("쓰기: node compare_index.mjs <옮기기 전 index.json> <옮긴 뒤 index.json>");
  process.exit(2);
}

function stories(path) {
  try {
    const { entries } = JSON.parse(readFileSync(path, "utf-8"));
    return Object.values(entries).filter((entry) => entry.type === "story");
  } catch (error) {
    console.error(`측정이 아니다: ${path} 를 index.json 으로 읽지 못했다(${error.message})`);
    process.exit(2);
  }
}

const before = stories(beforePath);
const after = stories(afterPath);
const ids = (list) => list.map((entry) => entry.id).sort();
const sameIds = JSON.stringify(ids(before)) === JSON.stringify(ids(after));
const fromPackage = (list) => list.filter((entry) => entry.importPath.includes(PACKAGE)).length;
const judgment = (list) =>
  list
    .filter((entry) => entry.tags.includes("judgment"))
    .map((entry) => entry.id)
    .sort()
    .join(",");

console.log(`옮기기 전: 스토리 ${before.length}, 패키지에서 실은 것 ${fromPackage(before)}`);
console.log(`옮긴 뒤: 스토리 ${after.length}, 패키지에서 실은 것 ${fromPackage(after)}`);
console.log(`스토리 id 가 같다: ${sameIds}`);
console.log(`judgment 태그(사진을 찍지 않는다): 전 [${judgment(before)}] 뒤 [${judgment(after)}]`);

// 표지: 두 빌드에 스토리가 있고, 앞의 것은 패키지에서 하나도 싣지 않았으며, 뒤의 것은 모두 패키지에서 실었다.
const measured =
  before.length > 0 &&
  after.length > 0 &&
  fromPackage(before) === 0 &&
  fromPackage(after) === after.length;
if (!measured) {
  console.error("측정이 아니다: 앞의 것이 옮기기 전 빌드가 아니거나 뒤의 것이 옮긴 뒤 빌드가 아니다");
  process.exit(2);
}
process.exit(sameIds && judgment(before) === judgment(after) ? 0 : 1);
