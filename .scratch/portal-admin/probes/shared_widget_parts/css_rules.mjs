// 지은 앱(`next build` 의 .next/static)의 CSS 에 주어진 클래스의 규칙이 있는지 본다(README "다시 돌리는 법" 6).
//
// 소비자 확인의 갈래 둘을 가른다. 앱의 전역 CSS 가 `@agent-os/widget-ui/source.css` 를 들이면 위젯 화면 부품의 소스에만
// 있는 클래스의 규칙이 지은 CSS 에 있고(`present`), 들이지 않으면 없다(`absent`). `next build` 는 두 갈래 모두 0 으로
// 끝나므로 종료 코드로는 가르지 못한다.
//
// 대조 클래스는 두 갈래 모두에 있어야 하는 것(앱이나 디자인 시스템의 소스에 이미 있는 클래스)이다. 대조 클래스를 찾지
// 못하면 CSS 를 읽지 못했거나 선택자 찾기가 틀린 것이라 측정이 아니라고 보고 2 로 끝난다. 준 경로를 읽지 못했을 때도 2 다.
// 기대와 다른 클래스가 있으면 1 이다.
//
// 쓰기: node css_rules.mjs <.next/static 경로> <present|absent> <대조 클래스> <클래스>...
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const [root, expectation, control, ...classes] = process.argv.slice(2);
if (
  root === undefined ||
  (expectation !== "present" && expectation !== "absent") ||
  control === undefined ||
  classes.length === 0
) {
  console.error(
    "쓰기: node css_rules.mjs <.next/static 경로> <present|absent> <대조 클래스> <클래스>...",
  );
  process.exit(2);
}

function cssFiles(dir) {
  const found = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) {
      found.push(...cssFiles(path));
    } else if (name.endsWith(".css")) {
      found.push(path);
    }
  }
  return found;
}

/** Tailwind 가 선택자에 쓰는 이스케이프(`\:`, `\/`)를 붙인다. */
function selector(name) {
  return "." + name.replace(/[:/]/g, (char) => "\\" + char);
}

let files;
let text;
try {
  files = cssFiles(root);
  text = files.map((path) => readFileSync(path, "utf-8")).join("\n");
} catch (error) {
  console.error(`측정이 아니다: ${root} 아래의 CSS 를 읽지 못했다(${error.message})`);
  process.exit(2);
}
// 선택자 뒤에는 `{` 나 의사 클래스의 `:` 가 온다.
const has = (name) => text.includes(selector(name) + "{") || text.includes(selector(name) + ":");

console.log(`CSS 파일 ${files.length}개, ${text.length}자`);
if (files.length === 0 || !has(control)) {
  console.error(`측정이 아니다: CSS 파일이 없거나 대조 클래스 ${control} 의 규칙을 찾지 못했다`);
  process.exit(2);
}
console.log(`대조 ${control}: 있다`);

let mismatched = 0;
for (const name of classes) {
  const present = has(name);
  console.log(`${name}: ${present ? "있다" : "없다"}`);
  if (present !== (expectation === "present")) {
    mismatched += 1;
  }
}
console.log(`기대(${expectation})와 다른 클래스 ${mismatched}개`);
process.exit(mismatched === 0 ? 0 : 1);
