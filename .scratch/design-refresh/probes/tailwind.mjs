// design-refresh Tailwind 프로브: 밀도 별칭(`@theme inline`)이 CSS 변수로 나오는 조건과, 빌드의 최적화가 hex 를 줄이는지 본다.
//   node .scratch/design-refresh/probes/tailwind.mjs [node_modules 가 있는 web 폴더, 기본 web]
//
// 입력은 같은 폴더의 `tailwind-input.css` 다. 명세의 밀도 절은 `--text-body: var(--body-size)` 같은 별칭을 `@theme inline`
// 에 두고 "inline 이라 CSS 변수로 나오지 않는다"고 적었다. 그런데 지금 디자인 토큰 CSS 의 `[data-ui-root]` 규칙은 손으로 쓴
// `var(--text-body)` 로 그 이름을 읽는다. 그 모양을 컴파일해 별칭이 `:root, :host` 에 선언으로 나오는지, 손으로 읽지 않는
// `--spacing-control` 은 나오지 않는지 본다. 그 규칙을 뺀 입력도 컴파일해, 별칭이 나오는 까닭이 손으로 쓴 `var()` 인지
// 가른다. 그리고 `optimize`(Lightning CSS. `@tailwindcss/vite` 가 빌드 때 부른다)가 사용자 정의 속성의 hex 를 짧은 꼴로
// 바꾸는지 `minify` 둘에서 본다.
// Tailwind 는 그 web 폴더의 `packages/ui` 가 깐 `@tailwindcss/vite` 가 의존하는 `@tailwindcss/node` 다.
// 측정의 표지: 1) 은 테마 블록(`@layer theme {`)이 있고 그 안에 `@theme static` 의 `--text-title:` 이 나오며(양성 대조)
// `.h-control` 규칙이 있는 회차, 2) 는 optimize 결과에 입력의 사용자 정의 속성 셋이 모두 나오는 회차만 측정으로 센다.
// 표지가 없는 회차가 하나라도 있으면 종료 코드가 1이다.
// stdout 은 1) 갈래마다 별칭 둘이 선언으로 나왔는지, 2) minify 마다 hex 셋의 꼴, 그리고 import 한 Tailwind 의 판이다.

import { existsSync, readFileSync, realpathSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const web = resolve(process.argv[2] ?? "web");
// `@tailwindcss/vite` 는 `exports` 가 `./package.json` 을 내지 않아, 링크를 푼 폴더에서 그 패키지의 require 로
// `@tailwindcss/node` 를 푼다.
const vite = realpathSync(join(web, "packages", "ui", "node_modules", "@tailwindcss", "vite"));
const entry = createRequire(join(vite, "package.json")).resolve("@tailwindcss/node");
const tw = await import(pathToFileURL(entry).href);

/** import 한 모듈의 파일에서 위로 올라가 이름이 `@tailwindcss/node` 인 package.json 의 판을 읽는다. */
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

const css = readFileSync(new URL("tailwind-input.css", import.meta.url), "utf8");
const CANDIDATES = ["text-body", "h-control"];
const compile = async (source) =>
  (await tw.compile(source, { base: join(web, "packages", "ui"), onDependency() {} })).build(CANDIDATES);
const out = await compile(css);
let unmeasured = 0;

// 갈래 둘: 입력 그대로(`[data-ui-root]` 가 `var(--text-body)` 를 읽는다)와, 그 `@layer base` 규칙을 뺀 입력. 별칭이
// 선언으로 나오는 까닭이 손으로 쓴 `var()` 라면 앞에서만 나오고 뒤에서는 나오지 않아야 한다. 테마 블록은 머리의 층 순서
// 선언(`@layer theme, base, …;`)이 아니라 `@layer theme {` 로 찾는다.
const withoutRule = css.slice(0, css.indexOf("@layer base"));
console.log("1) inline 별칭이 선언으로 나오는가");
for (const [label, compiled] of [
  ["[data-ui-root] 가 var(--text-body) 를 읽는 입력", out],
  ["그 규칙을 뺀 입력", await compile(withoutRule)],
]) {
  const start = compiled.indexOf("@layer theme {");
  const end = compiled.indexOf("@layer base {");
  const theme = start < 0 ? "" : compiled.slice(start, end < 0 ? undefined : end);
  if (theme.includes("--text-title:") && compiled.includes(".h-control")) {
    console.log(`  ${label}`);
    console.log(`    --text-body: ${theme.includes("--text-body:") ? "나왔다" : "나오지 않았다"}`);
    console.log(`    --spacing-control(유틸리티만 쓴다): ${theme.includes("--spacing-control:") ? "나왔다" : "나오지 않았다"}`);
  } else {
    unmeasured += 1;
    console.log(`  ${label}: 측정 아님(테마 블록에 --text-title 이 없거나 .h-control 규칙이 없다)`);
  }
}

console.log("2) optimize 뒤의 hex");
const NAMES = ["--gray-0", "--overlay-black-40", "--overlay-white-10"];
for (const minify of [false, true]) {
  const optimized = tw.optimize(out, { minify });
  const code = String(optimized.code ?? optimized);
  // 줄인 CSS 에서는 블록의 마지막 선언 뒤에 `;` 없이 `}` 가 온다.
  const found = NAMES.map((name) => new RegExp(`${name}:[^;}]*`).exec(code)?.[0] ?? null);
  if (found.includes(null)) unmeasured += 1;
  console.log(
    `  minify ${String(minify)}: ${found.map((line, i) => (line === null ? `${NAMES[i]} 없음` : line.replace(/\s+/g, ""))).join("  ")}`,
  );
}

console.log(`@tailwindcss/node ${version}`);
if (unmeasured > 0) {
  console.log(`측정이 아닌 회차 ${String(unmeasured)}`);
  process.exitCode = 1;
}
