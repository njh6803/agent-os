// answer-markdown Tailwind 프로브(2026-11-11): 마크다운 부품의 모양을 요소마다의 유틸리티 클래스로 낼 수 있는지 본다.
//   node .scratch/answer-markdown/probes/tailwind_utilities.mjs [node_modules 가 있는 web 폴더, 기본 web]
//
// 디자인 토큰 CSS(`web/packages/ui/src/styles/theme.css`)는 `--*: initial` 로 Tailwind 의 기본값을 비운다. 그래서 익숙한
// 클래스(`min-w-24`)는 규칙을 만들지 않고, 스토리 테스트의 afterEach 가 규칙 없는 클래스를 실패로 삼는다. 명세는 화면
// 파일의 모양(프로브 `markdown_render/probe/browser-kit.mjs` 의 `MD_CSS`)을 컴포넌트 CSS 없이 요소마다의 클래스로 내고
// 모자란 토큰만 패키지에 더한다고 적으려 한다. 이 프로브는 그 후보 클래스마다 지금 디자인 토큰 CSS 에서 규칙이 생기는지,
// 더하려는 토큰을 넣으면 그 유틸리티가 생기는지를 컴파일해 본다.
//
// 방법: 작업 트리의 theme.css 를 읽어 `@tailwindcss/node`(그 web 폴더의 `packages/ui` 가 깐 `@tailwindcss/vite` 가
// 의존하는 것)의 `compile` 로 컴파일한다. 후보 없이 지은 CSS 를 기준선으로 두고, 후보 하나만 넣어 지은 CSS 에 기준선에
// 없는 줄이 생기면 규칙이 생긴 것이다(선택자를 풀어 읽지 않는다). 더한 줄에서 선언을 뽑아 기대(`expect`)와 견준다.
// 갈래는 둘이다. 1) theme.css 그대로, 2) theme.css 뒤에 더하려는 토큰(`ADDED_TOKENS`)을 붙인 것.
//
// 측정의 표지(.claude/rules/probes.md). 갈래마다 아래가 모두 맞아야 측정으로 센다. 하나라도 어긋나면 종료 코드 1.
// - 기준선의 테마 블록(`@layer theme {`)에 `--text-title:` 과 `--spacing-4: 16px` 가 있다(theme.css 가 실제로 실렸다).
// - 양성 대조: `p-4` 가 `padding: var(--spacing-4)` 를 든 규칙을 만든다.
// - 규칙이 없어야 하는 대조: Tailwind 기본값에 기대는 클래스(`NEGATIVE_CONTROLS`)는 아무 줄도 더하지 않는다. 더하면
//   `--*: initial` 이 걸리지 않은 것이고 "규칙이 생겼다"는 결과를 믿을 수 없다.
// - 갈래 1 에서는 더하려는 토큰의 유틸리티(`TOKEN_UTILITIES`)가 규칙을 만들지 않는다(갈래 2 에서 생긴 까닭이 더한
//   토큰임을 가른다).
// 후보가 규칙을 만들지 않거나 선언이 기대와 다른 것은 측정 결과다(종료 코드 0). stdout 에 적는다.
//
// 못 보는 것: 규칙이 생긴다는 것까지다. 그 클래스들로 그린 화면이 화면 파일과 같은 모양인지는 보지 않는다(사진 비교와
// 스토리의 계산값 단언이 부품을 짓는 티켓에서 본다). 스토리 테스트의 afterEach 판정(`classesWithoutRules`)을 돌린 것도
// 아니다. 그 판정은 브라우저의 CSSOM 에서 규칙을 찾고, 이 프로브는 컴파일한 글에서 찾는다.
import { existsSync, readFileSync, realpathSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const web = resolve(process.argv[2] ?? "web");
const STYLES = join(web, "packages", "ui", "src", "styles");
const vite = realpathSync(join(web, "packages", "ui", "node_modules", "@tailwindcss", "vite"));
const entry = createRequire(join(vite, "package.json")).resolve("@tailwindcss/node");
const tw = await import(pathToFileURL(entry).href);

function versionOf(file) {
  for (let dir = dirname(file); dir !== dirname(dir); dir = dirname(dir)) {
    const manifest = join(dir, "package.json");
    if (existsSync(manifest)) {
      const json = JSON.parse(readFileSync(manifest, "utf8"));
      if (json.name === "@tailwindcss/node") return json.version;
    }
  }
  return "알 수 없음";
}
const version = versionOf(entry.startsWith("file:") ? fileURLToPath(entry) : entry);

const THEME = readFileSync(join(STYLES, "theme.css"), "utf8");
// 패키지에 더하려는 토큰. 표의 칸의 최소·최대 폭, 위첨자 번호의 왼쪽 틈(화면 파일의 2px), 안쪽 목록의 표시(화면 파일의
// 빈 동그라미)다. 뒤의 둘은 사람이 "그림에 맞추고 디자인 시스템을 넓힘"을 고른 뒤 더하기로 했다(2026-11-11).
const ADDED_TOKENS = `
@theme static {
  --spacing-cell-min: 96px;
  --spacing-cell-max: 256px;
  --spacing-cite-start: 2px;
  --list-style-type-circle: circle;
}
`;
const TOKEN_UTILITIES = [
  { name: "min-w-cell-min", expect: "min-width: var(--spacing-cell-min)" },
  { name: "max-w-cell-max", expect: "max-width: var(--spacing-cell-max)" },
  { name: "ml-cite-start", expect: "margin-left: var(--spacing-cite-start)" },
  { name: "list-circle", expect: "list-style-type: var(--list-style-type-circle)" },
];
const NEGATIVE_CONTROLS = ["min-w-24", "max-w-64", "ml-0.5", "text-base", "rounded", "text-gray-500"];

const FOCUS = [
  { name: "focus-visible:outline-2", expect: "outline-width: 2px" },
  { name: "focus-visible:outline-offset-2", expect: "outline-offset: 2px" },
  { name: "focus-visible:outline-focus-ring", expect: "outline-color: var(--focus-ring)" },
];
// 요소마다의 후보. `expect` 는 더한 줄에 있어야 하는 선언의 조각이다.
const ELEMENTS = [
  {
    element: "뿌리(블록 사이 12px, 본문 글자, 긴 낱말 끊기)",
    classes: [
      { name: "flex", expect: "display: flex" },
      { name: "min-w-0", expect: "min-width: var(--spacing-0)" },
      { name: "flex-col", expect: "flex-direction: column" },
      { name: "gap-3", expect: "gap: var(--spacing-3)" },
      { name: "text-body", expect: "font-size: var(--body-size)" },
      { name: "wrap-anywhere", expect: "overflow-wrap: anywhere" },
    ],
  },
  {
    element: "제목(본문 크기 굵게, 위 16px·아래 4px. 제목 바로 뒤의 제목은 위 여백 12px 으로 사이 16px)",
    classes: [
      { name: "font-semibold", expect: "font-weight: var(--font-weight-semibold)" },
      { name: "mt-1", expect: "margin-top: var(--spacing-1)" },
      { name: "mt-3", expect: "margin-top: var(--spacing-3)" },
      { name: "-mb-2", expect: "margin-bottom: calc(var(--spacing-2) * -1)" },
      { name: "first:mt-0", expect: "margin-top: var(--spacing-0)" },
      { name: "last:mb-0", expect: "margin-bottom: var(--spacing-0)" },
    ],
  },
  {
    element: "목록(왼쪽 24px, 항목 사이 4px, 표시)",
    classes: [
      { name: "pl-6", expect: "padding-left: var(--spacing-6)" },
      { name: "list-disc", expect: "list-style-type: disc" },
      { name: "list-decimal", expect: "list-style-type: decimal" },
      { name: "space-y-1", expect: "var(--spacing-1)" },
    ],
  },
  {
    element: "인용(왼쪽 12px, 2px 선, 안의 블록 사이 12px)",
    classes: [
      { name: "border-l-2", expect: "border-left-width: 2px" },
      { name: "border-border-control", expect: "border-color: var(--border-control)" },
      { name: "pl-3", expect: "padding-left: var(--spacing-3)" },
    ],
  },
  {
    element: "줄 안 코드(고정폭, 바탕, 모서리, 좌우 4px)",
    classes: [
      { name: "font-mono", expect: "font-family: var(--mono)" },
      { name: "text-mono", expect: "font-size: var(--mono-size)" },
      { name: "bg-bg", expect: "background-color: var(--bg)" },
      { name: "rounded-s", expect: "border-radius: var(--radius-s)" },
      { name: "px-1", expect: "padding-inline: var(--spacing-1)" },
    ],
  },
  {
    element: "코드 블록(안쪽 12px, 테두리, 가로 스크롤, 포커스 링)",
    classes: [
      { name: "p-3", expect: "padding: var(--spacing-3)" },
      { name: "border", expect: "border-width: 1px" },
      { name: "border-border", expect: "border-color: var(--border)" },
      { name: "overflow-x-auto", expect: "overflow-x: auto" },
      ...FOCUS,
    ],
  },
  {
    element: "링크(강조색, 밑줄)",
    classes: [
      { name: "text-accent", expect: "color: var(--accent)" },
      { name: "underline", expect: "text-decoration-line: underline" },
    ],
  },
  {
    element: "가로줄",
    classes: [{ name: "border-t", expect: "border-top-width: 1px" }],
  },
  {
    element: "표(가로선, 표의 글자, 칸의 여백과 정렬)",
    classes: [
      { name: "border-collapse", expect: "border-collapse: collapse" },
      { name: "text-table", expect: "font-size: var(--table-size)" },
      { name: "border-b", expect: "border-bottom-width: 1px" },
      { name: "last:border-b-0", expect: "border-bottom-width: 0px" },
      { name: "px-3", expect: "padding-inline: var(--spacing-3)" },
      { name: "py-2", expect: "padding-block: var(--spacing-2)" },
      { name: "first:pl-0", expect: "padding-left: var(--spacing-0)" },
      { name: "align-top", expect: "vertical-align: top" },
      { name: "text-left", expect: "text-align: left" },
      { name: "text-center", expect: "text-align: center" },
      { name: "text-right", expect: "text-align: right" },
    ],
  },
  {
    element: "위첨자 번호와 출처(작은 글자, 옅은 색, 번호의 줄 높이 0, 이어진 번호 왼쪽 4px, 위 선과 12px, 줄 사이 4px)",
    classes: [
      { name: "text-small", expect: "font-size: var(--text-small)" },
      { name: "text-text-muted", expect: "color: var(--text-muted)" },
      { name: "leading-0", expect: "line-height: var(--spacing-0)" },
      { name: "ml-1", expect: "margin-left: var(--spacing-1)" },
      { name: "pt-3", expect: "padding-top: var(--spacing-3)" },
      { name: "gap-1", expect: "gap: var(--spacing-1)" },
    ],
  },
  {
    element: "줄 안 글자와 숨긴 글, 원문 문단",
    classes: [
      { name: "italic", expect: "font-style: italic" },
      { name: "line-through", expect: "text-decoration-line: line-through" },
      { name: "sr-only", expect: "position: absolute" },
      { name: "whitespace-pre-wrap", expect: "white-space: pre-wrap" },
    ],
  },
];

const compileWith = async (source, candidates) =>
  (await tw.compile(source, { base: STYLES, onDependency() {} })).build(candidates);

/**
 * 후보 하나가 기준선에 더한 것. 더한 줄이 없으면 빈 배열이다.
 * 기준선에 없는 줄만 모으면, 기준선의 다른 규칙에 글자가 같은 선언(preflight 의 `border-collapse: collapse` 등)이 있을 때
 * 그 선언이 빠진다(첫 실행에서 넷이 그랬다). 그래서 더한 줄 가운데 첫 선택자 줄(`.` 으로 시작하고 `{` 로 끝난다)을
 * 지은 CSS 에서 찾아, 중괄호가 닫힐 때까지의 규칙 전체를 앞에 싣는다.
 */
async function added(source, baseline, candidate) {
  const out = await compileWith(source, [candidate]);
  const all = out.split(/\r?\n/).map((line) => line.trim());
  const fresh = all.filter((line) => line !== "" && !baseline.has(line));
  if (fresh.length === 0) return [];
  const selector = fresh.find((line) => line.startsWith(".") && line.endsWith("{"));
  if (selector === undefined) return fresh;
  const rule = [];
  let depth = 0;
  for (let i = all.indexOf(selector); i < all.length; i += 1) {
    rule.push(all[i]);
    depth += (all[i].match(/\{/g) ?? []).length - (all[i].match(/\}/g) ?? []).length;
    if (depth <= 0) break;
  }
  return [...rule, ...fresh];
}

let unmeasured = 0;
const results = [];
for (const [label, source, withTokens] of [
  ["1) theme.css 그대로", THEME, false],
  ["2) theme.css 에 더하려는 토큰을 붙인 것", `${THEME}\n${ADDED_TOKENS}`, true],
]) {
  console.log(label);
  const baselineCss = await compileWith(source, []);
  const baseline = new Set(baselineCss.split(/\r?\n/).map((line) => line.trim()));
  const start = baselineCss.indexOf("@layer theme {");
  const theme = start < 0 ? "" : baselineCss.slice(start);
  const problems = [];
  if (!theme.includes("--text-title:")) problems.push("테마 블록에 --text-title 이 없다");
  if (!/--spacing-4:\s*16px/.test(theme)) problems.push("테마 블록에 --spacing-4: 16px 가 없다");
  const positive = (await added(source, baseline, "p-4")).join(" ");
  if (!positive.includes("padding: var(--spacing-4)")) problems.push(`양성 대조 p-4 가 규칙을 만들지 않았다: ${positive}`);
  for (const name of NEGATIVE_CONTROLS) {
    const lines = await added(source, baseline, name);
    if (lines.length > 0) problems.push(`규칙이 없어야 하는 대조 ${name} 가 줄을 더했다: ${lines.join(" ")}`);
  }
  const tokenRows = [];
  for (const item of TOKEN_UTILITIES) {
    const lines = (await added(source, baseline, item.name)).join(" ");
    tokenRows.push({ ...item, lines });
    if (!withTokens && lines !== "") problems.push(`토큰을 더하기 전인데 ${item.name} 가 줄을 더했다: ${lines}`);
  }
  if (problems.length > 0) {
    unmeasured += 1;
    console.log(`  측정 아님: ${problems.join(" / ")}`);
    continue;
  }
  console.log("  표지: 테마 블록의 --text-title·--spacing-4, 양성 대조 p-4, 규칙이 없어야 하는 대조 여섯이 모두 맞다");
  let missing = 0;
  let different = 0;
  let total = 0;
  for (const group of ELEMENTS) {
    const lines = [];
    for (const item of group.classes) {
      total += 1;
      const text = (await added(source, baseline, item.name)).join(" ");
      if (text === "") {
        missing += 1;
        lines.push(`    규칙 없음 ${item.name}`);
      } else if (!text.includes(item.expect)) {
        different += 1;
        lines.push(`    선언 다름 ${item.name}: 기대 "${item.expect}", 더한 줄 "${text.slice(0, 200)}"`);
      }
    }
    console.log(`  ${group.element}: 후보 ${String(group.classes.length)}${lines.length === 0 ? ", 모두 기대한 선언" : ""}`);
    for (const line of lines) console.log(line);
  }
  for (const row of tokenRows) {
    if (!withTokens) {
      console.log(`  더하려는 토큰의 유틸리티 ${row.name}: 규칙 없음(토큰을 더하기 전)`);
    } else if (row.lines === "") {
      missing += 1;
      console.log(`  더하려는 토큰의 유틸리티 ${row.name}: 규칙 없음`);
    } else if (!row.lines.includes(row.expect)) {
      different += 1;
      console.log(`  더하려는 토큰의 유틸리티 ${row.name}: 선언 다름. 기대 "${row.expect}", 더한 줄 "${row.lines.slice(0, 200)}"`);
    } else {
      console.log(`  더하려는 토큰의 유틸리티 ${row.name}: ${row.expect}`);
    }
  }
  results.push({ label, total, missing, different });
  console.log(`  합계: 후보 ${String(total)}, 규칙 없음 ${String(missing)}, 선언 다름 ${String(different)}`);
}

console.log(`@tailwindcss/node ${version}`);
console.log(JSON.stringify({ probe: "tailwind_utilities", tailwind: version, results, notMeasured: unmeasured }));
if (unmeasured > 0) process.exitCode = 1;
