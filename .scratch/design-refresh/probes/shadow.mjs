// design-refresh 그림자 프로브: 떠 있는 것의 그림자 `--shadow-float` 를 `@theme static` 과 `@theme inline` 에 둘 때
// `.shadow-float` 유틸리티와 뿌리의 선언이 어떻게 나오는지 본다.
//   node .scratch/design-refresh/probes/shadow.mjs [node_modules 가 있는 web 폴더, 기본 web]
//
// 그림자 색(`--shadow-color`)은 모드마다 달라, 유틸리티가 그 색을 놓인 요소에서 읽어야 한다. 티켓 04 는 처음에 static
// 이면 변수가 뿌리에 선언으로 나와 유틸리티가 뿌리의 모드로 풀린 색을 받는다고 어림했는데, 그렇게 옮긴 변이에서도 판정
// 스토리 FloatShadow 가 초록이었다(`density_sizes_mutations.toml`). 그 까닭을 컴파일 결과로 가른다. 두 블록이 같은
// 유틸리티를 내면 까닭은 Tailwind 가 그림자 값을 유틸리티에 풀어 쓰는 것이고, 남는 차이는 뿌리의 선언이다.
// Tailwind 는 그 web 폴더의 `packages/ui` 가 깐 `@tailwindcss/vite` 가 의존하는 `@tailwindcss/node` 다(`tailwind.mjs` 와
// 같은 길).
// 측정의 표지: 갈래마다 `.shadow-float` 규칙이 있고 그 안에 `box-shadow` 가 있는 회차만 측정으로 센다. 표지가 없는 회차가
// 하나라도 있으면 종료 코드가 1이다.
// stdout 은 갈래마다 뿌리에 `--shadow-float` 선언이 있는지와 `.shadow-float` 규칙, 두 규칙이 같은지, Tailwind 의 판이다.

import { existsSync, readFileSync, realpathSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const web = resolve(process.argv[2] ?? "web");
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

// 디자인 토큰 CSS 의 그 줄과 같은 값이다.
const SHADOW = "--shadow-float: 0 8px 24px var(--shadow-color), 0 1px 2px var(--shadow-color);";
const source = (block) => `@import "tailwindcss/theme.css" layer(theme);
@import "tailwindcss/utilities.css" layer(utilities);
@theme ${block} {
  --*: initial;
  ${SHADOW}
}
`;

let unmeasured = 0;
const rules = [];
for (const block of ["static", "inline"]) {
  const compiled = await (
    await tw.compile(source(block), { base: join(web, "packages", "ui"), onDependency() {} })
  ).build(["shadow-float"]);
  const start = compiled.indexOf(".shadow-float");
  const rule = start < 0 ? "" : compiled.slice(start, compiled.indexOf("}", start) + 1).replace(/\s+/g, " ");
  if (!rule.includes("box-shadow")) {
    unmeasured += 1;
    console.log(`== ${block}: 측정 아님(.shadow-float 규칙이나 box-shadow 가 없다)`);
    continue;
  }
  const rootDeclared = /:root[^{]*\{[^}]*--shadow-float:/.test(compiled);
  rules.push(rule);
  console.log(`== ${block}: 뿌리에 --shadow-float 선언 ${rootDeclared ? "있음" : "없음"}`);
  console.log(`   ${rule}`);
}
if (rules.length === 2) {
  console.log(`두 블록의 .shadow-float 규칙이 ${rules[0] === rules[1] ? "같다" : "다르다"}`);
}
console.log(`@tailwindcss/node ${version}`);
process.exit(unmeasured === 0 ? 0 : 1);
