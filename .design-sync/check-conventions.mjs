// 사용 규약(.design-sync/conventions.md)이 든 이름이 이번 빌드(ds-bundle/)에 실제로 있는지 판정한다.
// /design-sync 스킬은 다시 동기화할 때마다 이 검증을 요구한다. 없는 이름을 적은 규약은 디자인 에이전트가 믿고 스타일이 빠진
// 화면을 그리게 한다. 저장소 뿌리에서 driver(resync.mjs)나 변환기를 돌린 뒤 `node .design-sync/check-conventions.mjs`.
// 종료 코드: 0 모두 맞다, 1 맞지 않는 이름이 있다(목록을 낸다), 2 읽을 파일이 없다.
//
// 읽는 것(규약의 문장 모양에 기댄다. 규약을 고쳐 모양이 바뀌면 여기도 고친다):
// - "이미 있는 유틸리티 클래스: `…`" 의 백틱 묶음: `_ds_bundle.css` 에 `.<클래스>` 가 있어야 한다. 바로 뒤가 이름
//   글자인 것(`.flex-col` 안의 `.flex`)은 세지 않는다.
// - "흔한 Tailwind 이름 가운데 … CSS 가 없어" 사이의 백틱 낱말: 반대로 없어야 한다(있으면 규약이 틀렸다).
// - `--이름` 꼴의 낱말: 앞이 다른 이름 글자가 아닌 `--이름:` 선언이 있어야 한다. "테마의 재료" 문장(원색 토큰)의 것은 쓰지
//   말라는 예시라 뺀다. 여백 줄의 `-2` 꼴은 `--spacing-2` 로 푼다. `<이름>` 이 든 자리 표시는 통째로 뺀다.
// - 예시의 `const { … } = window.AgentOsUi` 와 본문의 `AgentOsUi.<이름>`: 번들에 그 이름이 있어야 하고, 컴포넌트는
//   `components/**/<이름>.d.ts` 도 있어야 한다.
// - "`data-theme`(…)" 의 백틱 낱말: `[data-theme=<키>]` 선택자가 있어야 한다.
import { existsSync, readFileSync, readdirSync } from "node:fs";

const files = {
  md: ".design-sync/conventions.md",
  css: "ds-bundle/_ds_bundle.css",
  js: "ds-bundle/_ds_bundle.js",
  components: "ds-bundle/components",
};
const missing = Object.values(files).filter((path) => !existsSync(path));
if (missing.length > 0) {
  console.error(`읽을 파일이 없다(빌드를 먼저 돌린다): ${missing.join(", ")}`);
  process.exit(2);
}
const md = readFileSync(files.md, "utf8");
const css = readFileSync(files.css, "utf8");
const js = readFileSync(files.js, "utf8");
const problems = [];

const ticks = (text) => [...text.matchAll(/`([^`]+)`/g)].map((match) => match[1]);
const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// 선택자의 클래스 글자(`hover\:bg-tint`, `w-3\/10`)가 있고 바로 뒤가 이름 글자가 아니어야 한다. `.flex` 가 `.flex-col`
// 안에서, `.border` 가 `.border-border` 안에서 맞지 않게 한다.
const hasClass = (name) => {
  const selector = `.${name.replace(/[:/.[\]%]/g, (char) => `\\${char}`)}`;
  return new RegExp(`${escapeRegExp(selector)}(?![\\w\\\\-])`).test(css);
};

const present = /이미 있는 유틸리티 클래스: `([^`]+)`/s.exec(md)?.[1];
if (present === undefined) {
  problems.push("규약에서 '이미 있는 유틸리티 클래스' 묶음을 찾지 못했다");
} else {
  for (const name of present.split(/\s+/).filter(Boolean)) {
    if (!hasClass(name)) problems.push(`클래스가 없다: ${name}`);
  }
}

const absent = /흔한\s+Tailwind 이름 가운데([\s\S]*?)CSS 가 없어/.exec(md)?.[1];
if (absent === undefined) problems.push("규약에서 'CSS 가 없다'고 든 이름의 문장을 찾지 못했다");
for (const name of ticks(absent ?? "")) {
  if (!name.endsWith(":") && hasClass(name)) problems.push(`없다고 적은 클래스가 있다: ${name}`);
  if (name.endsWith(":") && css.includes(`.${name.slice(0, -1)}\\:`)) problems.push(`없다고 적은 변형이 있다: ${name}`);
}

const variables = new Set();
for (const rawLine of md.split("\n")) {
  if (rawLine.includes("테마의 재료")) continue;
  // `--text-<이름>--line-height` 같은 자리 표시는 통째로 걷는다. 남기면 `--line-height` 가 이름으로 뽑힌다.
  const line = rawLine.replace(/--[a-z0-9-]*<[^>]*>[a-z0-9-]*/g, "");
  for (const [name] of line.matchAll(/--[a-z][a-z0-9-]*(?:--[a-z0-9-]+)?/g)) {
    if (!name.endsWith("-")) variables.add(name);
  }
  if (line.includes("--spacing-")) {
    for (const token of ticks(line)) {
      if (/^-\d+$/.test(token)) variables.add(`--spacing${token}`);
    }
  }
}
// 이름의 앞이 다른 이름 글자가 아니어야 한다. `--line-height:` 가 `--text-body--line-height:` 안에서 맞지 않게 한다.
for (const name of variables) {
  if (!new RegExp(`(?<![a-z0-9-])${escapeRegExp(name)}\\s*:`).test(css)) problems.push(`변수가 없다: ${name}`);
}

const exported = new Set(
  [...md.matchAll(/AgentOsUi\.([A-Z_][A-Za-z_]*)/g)].map((match) => match[1]),
);
for (const match of md.matchAll(/const \{([^}]+)\} = window\.AgentOsUi/g)) {
  for (const name of match[1].split(",").map((part) => part.trim()).filter(Boolean)) exported.add(name);
}
const dtsFiles = readdirSync(files.components, { recursive: true }).map(String);
for (const name of exported) {
  if (!new RegExp(`\\b${name}\\b`).test(js)) problems.push(`번들에 없다: ${name}`);
  if (/^[A-Z][a-z]/.test(name) && !dtsFiles.some((path) => path.endsWith(`${name}.d.ts`))) {
    problems.push(`컴포넌트 폴더가 없다: ${name}`);
  }
}

const themes = /`data-theme`\(([^)]*)\)/.exec(md)?.[1] ?? "";
for (const key of ticks(themes).filter((token) => /^[a-z]+$/.test(token))) {
  if (!css.includes(`[data-theme="${key}"]`) && !css.includes(`[data-theme=${key}]`)) {
    problems.push(`테마 선택자가 없다: ${key}`);
  }
}

if (problems.length > 0) {
  console.error(problems.join("\n"));
  process.exit(1);
}
console.log(
  `규약의 이름이 모두 빌드에 있다: 클래스 ${present?.split(/\s+/).filter(Boolean).length ?? 0}, 변수 ${variables.size}, 내보내기 ${exported.size}`,
);
