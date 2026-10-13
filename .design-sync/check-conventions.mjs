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
// - 예시의 `const { … } = window.AgentOsUi` 와 본문의 `AgentOsUi.<이름>`: 번들의 내보내기 블록에 그 이름이 있어야 하고,
//   컴포넌트는 파일 이름이 정확히 `<이름>.d.ts` 인 파일이 `components/` 아래에 있어야 한다(`IconButton.d.ts` 로 `Button`
//   이 통과하지 않게).
// - "`data-theme`(…)" 와 "`data-density`(…)" 의 백틱 낱말: `[data-theme=<키>]`·`[data-density=<키>]` 선택자가 있어야 한다.
//
// 규약 밖에서 함께 보는 것 둘(design-refresh 티켓 05. 규칙은 NOTES 의 "카드에 올리는 스토리"와 "기초 카드"):
// - 빼는 목록. 참조 Storybook 의 색인(`cfg.storybookStatic` 의 `index.json`)에서 컴포넌트 스토리(제목의 마지막 토막이
//   `cfg.titleMap` 에서 null 이 아닌 것)를 모아, 태그 `showcase` 가 없는 스토리는 모두 그 컴포넌트의
//   `cfg.overrides.<Name>.skip` 에 있어야 하고, 빼는 목록의 id 는 모두 그 컴포넌트의 지금 있는 변형 스토리여야 하며,
//   컴포넌트마다 `showcase` 스토리가 하나 이상 있어야 한다. 빼는 목록은 스토리 id 라 스토리를 더하거나 이름을 바꾸면
//   조용히 어긋난다.
// - 기초 카드와 목록 타일. 폴더 넷(`FOUNDATIONS`)이 모두 있고, `.design-sync/foundations/<폴더>/` 마다 HTML 이 하나이고 첫 줄이 `<!-- @dsCard group="…" -->`
//   이어야 한다. 카드와 `thumbnail.html` 이 읽는 `var(--이름)`·`data-value="--이름"` 은 빌드 CSS 에 선언이 있어야 하고
//   (이름이 바뀌면 풀리지 않아 조용히 빈 칸이 된다), `data-theme`·`data-density` 의 값은 선택자가 있어야 한다. 그리고
//   `ds-bundle/` 에 같은 내용으로 복사되어 있어야 한다.
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const files = {
  md: ".design-sync/conventions.md",
  config: ".design-sync/config.json",
  foundations: ".design-sync/foundations",
  thumbnail: ".design-sync/thumbnail.html",
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
// 선택자의 클래스 글자(`hover\:bg-bg-hover`, `w-3\/10`)가 있고 바로 뒤가 이름 글자가 아니어야 한다. `.flex` 가 `.flex-col`
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
  [...md.matchAll(/AgentOsUi\.([A-Z_][A-Za-z0-9_]*)/g)].map((match) => match[1]),
);
for (const match of md.matchAll(/const \{([^}]+)\} = window\.AgentOsUi/g)) {
  for (const name of match[1].split(",").map((part) => part.trim()).filter(Boolean)) exported.add(name);
}
// 번들의 내보내기 블록(`__export(bundle_entry_exports, { 이름: () => … })`)에 든 이름만 `window.AgentOsUi` 에 오른다. 번들은
// 압축하지 않아 내부 식별자(`var GLYPHS`)도 글자로 남으므로 번들 전체의 낱말로 보면 내보내지 않은 이름이 통과한다.
const exportBlock = /__export\(bundle_entry_exports, \{([\s\S]*?)\n\s*\}\);/.exec(js)?.[1];
if (exportBlock === undefined) problems.push("번들에서 내보내기 블록을 찾지 못했다");
const bundleExports = new Set([...(exportBlock ?? "").matchAll(/^\s*([A-Za-z_$][\w$]*): \(\) =>/gm)].map((match) => match[1]));
const dtsNames = new Set(readdirSync(files.components, { recursive: true }).map((path) => String(path).split(/[\\/]/).at(-1)));
for (const name of exported) {
  if (!bundleExports.has(name)) problems.push(`번들이 내보내지 않는다: ${name}`);
  if (/^[A-Z][a-z]/.test(name) && !dtsNames.has(`${name}.d.ts`)) problems.push(`컴포넌트 폴더가 없다: ${name}`);
}

const hasSelector = (attribute, key) =>
  css.includes(`[${attribute}="${key}"]`) || css.includes(`[${attribute}=${key}]`);
for (const attribute of ["data-theme", "data-density"]) {
  const keys = new RegExp(`\`${attribute}\`\\(([^)]*)\\)`).exec(md)?.[1] ?? "";
  for (const key of ticks(keys).filter((token) => /^[a-z]+$/.test(token))) {
    if (!hasSelector(attribute, key)) problems.push(`${attribute} 선택자가 없다: ${key}`);
  }
}

// 빼는 목록. 변환기는 제목의 마지막 토막을 공백 없이 컴포넌트 이름으로 본다(`titleMap` 의 키도 그 꼴이다).
const SHOWCASE_TAG = "showcase";
const config = JSON.parse(readFileSync(files.config, "utf8"));
const indexPath = join(config.storybookStatic ?? "", "index.json");
if (!existsSync(indexPath)) {
  console.error(`읽을 파일이 없다(참조 Storybook 을 먼저 짓는다): ${indexPath}`);
  process.exit(2);
}
const index = JSON.parse(readFileSync(indexPath, "utf8"));
const titleMap = config.titleMap ?? {};
const overrides = config.overrides ?? {};
const storiesByComponent = new Map();
for (const entry of Object.values(index.entries ?? {})) {
  if (entry.type !== "story") continue;
  const name = String(entry.title).split("/").at(-1).replace(/\s+/g, "");
  if (titleMap[name] === null) continue;
  if (!storiesByComponent.has(name)) storiesByComponent.set(name, []);
  storiesByComponent.get(name).push(entry);
}
let skipped = 0;
for (const [name, stories] of storiesByComponent) {
  const skip = new Set(overrides[name]?.skip ?? []);
  skipped += skip.size;
  const showcase = stories.filter((story) => story.tags.includes(SHOWCASE_TAG));
  if (showcase.length === 0) problems.push(`보여 주기용 스토리가 없다: ${name}`);
  for (const story of stories) {
    if (!story.tags.includes(SHOWCASE_TAG) && !skip.has(story.id)) {
      problems.push(`변형 스토리가 빼는 목록에 없다: ${name} ${story.id}`);
    }
  }
  const ids = new Map(stories.map((story) => [story.id, story]));
  for (const id of skip) {
    const story = ids.get(id);
    if (story === undefined) problems.push(`빼는 목록의 스토리가 없다: ${name} ${id}`);
    else if (story.tags.includes(SHOWCASE_TAG)) problems.push(`보여 주기용 스토리를 뺀다: ${name} ${id}`);
  }
}
for (const name of Object.keys(overrides)) {
  if (!storiesByComponent.has(name)) problems.push(`빼는 목록의 컴포넌트가 색인에 없다: ${name}`);
}

// 기초 카드와 목록 타일.
const DSCARD = /^<!--\s*@dsCard\s+group="[^"]*"[^>]*-->/;
// 기초 카드 넷(NOTES 의 "기초 카드"). 폴더가 빠지거나 이름이 바뀌면 그 카드가 조용히 빠진 채 올라간다.
const FOUNDATIONS = ["colors", "density", "spacing", "type"];
const folders = readdirSync(files.foundations, { withFileTypes: true }).filter((entry) => entry.isDirectory());
for (const name of FOUNDATIONS) {
  if (!folders.some((folder) => folder.name === name)) problems.push(`기초 카드 폴더가 없다: ${name}`);
}
const cards = [];
for (const folder of folders) {
  const htmls = readdirSync(join(files.foundations, folder.name)).filter((file) => file.endsWith(".html"));
  if (htmls.length !== 1) problems.push(`기초 카드 폴더의 HTML 이 하나가 아니다: ${folder.name} (${htmls.length})`);
  for (const file of htmls) {
    const path = join(files.foundations, folder.name, file);
    const text = readFileSync(path, "utf8");
    if (!DSCARD.test(text.split("\n", 1)[0])) problems.push(`첫 줄이 @dsCard 가 아니다: ${path}`);
    cards.push({ path, text, copy: join("ds-bundle", "foundations", folder.name, file) });
  }
}
cards.push({ path: files.thumbnail, text: readFileSync(files.thumbnail, "utf8"), copy: join("ds-bundle", "thumbnail.html") });
const cardVariables = new Set();
for (const { path, text, copy } of cards) {
  for (const [, name] of text.matchAll(/var\(\s*(--[a-z][a-z0-9-]*)/g)) cardVariables.add(name);
  for (const [, name] of text.matchAll(/data-value="(--[a-z][a-z0-9-]*)"/g)) cardVariables.add(name);
  for (const [, attribute, key] of text.matchAll(/(data-theme|data-density)="([a-z]+)"/g)) {
    if (!hasSelector(attribute, key)) problems.push(`${attribute} 선택자가 없다: ${key} (${path})`);
  }
  if (!existsSync(copy) || readFileSync(copy, "utf8") !== text) problems.push(`ds-bundle 에 복사되지 않았다: ${path} → ${copy}`);
}
for (const name of cardVariables) {
  if (!new RegExp(`(?<![a-z0-9-])${escapeRegExp(name)}\\s*:`).test(css)) problems.push(`카드의 변수가 없다: ${name}`);
}

if (problems.length > 0) {
  console.error(problems.join("\n"));
  process.exit(1);
}
console.log(
  `규약의 이름이 모두 빌드에 있다: 클래스 ${present?.split(/\s+/).filter(Boolean).length ?? 0}, 변수 ${variables.size}, 내보내기 ${exported.size}. ` +
    `빼는 목록이 맞다: 컴포넌트 ${storiesByComponent.size}, 뺀 스토리 ${skipped}. 카드 ${cards.length}개의 변수 ${cardVariables.size}이 빌드에 있다`,
);
