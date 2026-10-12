// design-refresh Tailwind 프로브: 밀도 별칭(`@theme inline`)이 CSS 변수로 나오는 조건과, 빌드의 최적화가 hex 를 줄이는지 본다.
//   node .scratch/design-refresh/probes/tailwind.mjs [node_modules 가 있는 web 폴더, 기본 web]
//
// 입력은 같은 폴더의 `tailwind-input.css` 다. 명세의 밀도 절은 `--text-body: var(--body-size)` 같은 별칭을 `@theme inline`
// 에 두고 "inline 이라 CSS 변수로 나오지 않는다"고 적었다. 그런데 지금 디자인 토큰 CSS 의 `[data-ui-root]` 규칙은 손으로 쓴
// `var(--text-body)` 로 그 이름을 읽는다. 그 모양을 컴파일해 별칭이 `:root, :host` 에 선언으로 나오는지, 손으로 읽지 않는
// `--spacing-control` 은 나오지 않는지 본다. 그 규칙을 뺀 입력도 컴파일해, 별칭이 나오는 까닭이 손으로 쓴 `var()` 인지 가른다. 그리고 `optimize`(Lightning CSS. `@tailwindcss/vite` 가 빌드 때 부른다)가
// 사용자 정의 속성의 hex 를 짧은 꼴로 바꾸는지 `minify` 둘에서 본다.
// Tailwind 는 그 web 폴더의 `packages/ui` 가 깐 `@tailwindcss/vite` 가 의존하는 `@tailwindcss/node` 다.
// 측정의 표지: 컴파일 결과에 `@layer theme` 과 `.h-control` 규칙이 있어야(입력이 실제로 컴파일됐다) 1) 을, optimize 결과에
// `--gray-0:` 이 있어야 2) 를 측정으로 센다. 표지가 없으면 종료 코드가 1이다.
// stdout 은 1) 별칭 둘이 선언으로 나왔는지, 2) minify 마다 hex 셋의 꼴, 그리고 Tailwind 판이다.

import { readFileSync, realpathSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const web = resolve(process.argv[2] ?? "web");
// 두 패키지 모두 `exports` 가 `./package.json` 을 내지 않아, 링크를 푼 폴더에서 이웃 패키지를 찾는다(pnpm 은 의존성을
// 같은 `node_modules` 아래 이웃으로 둔다).
const vite = realpathSync(join(web, "packages", "ui", "node_modules", "@tailwindcss", "vite"));
const node = join(dirname(vite), "node");
const tw = await import(pathToFileURL(createRequire(join(vite, "package.json")).resolve("@tailwindcss/node")).href);
const { version } = JSON.parse(readFileSync(join(node, "package.json"), "utf8"));

const css = readFileSync(new URL("tailwind-input.css", import.meta.url), "utf8");
const CANDIDATES = ["text-body", "h-control"];
const compile = async (source) =>
  (await tw.compile(source, { base: join(web, "packages", "ui"), onDependency() {} })).build(CANDIDATES);
const out = await compile(css);
let unmeasured = 0;

// 갈래 둘: 입력 그대로(`[data-ui-root]` 가 `var(--text-body)` 를 읽는다)와, 그 `@layer base` 규칙을 뺀 입력. 별칭이
// 선언으로 나오는 까닭이 손으로 쓴 `var()` 라면 앞에서만 나오고 뒤에서는 나오지 않아야 한다.
const withoutRule = css.slice(0, css.indexOf("@layer base"));
console.log("1) inline 별칭이 선언으로 나오는가");
for (const [label, compiled] of [
  ["[data-ui-root] 가 var(--text-body) 를 읽는 입력", out],
  ["그 규칙을 뺀 입력", await compile(withoutRule)],
]) {
  if (compiled.includes("@layer theme") && compiled.includes(".h-control")) {
    const end = compiled.indexOf("@layer base");
    const theme = compiled.slice(compiled.indexOf("@layer theme"), end < 0 ? undefined : end);
    console.log(`  ${label}`);
    console.log(`    --text-body: ${theme.includes("--text-body:") ? "나왔다" : "나오지 않았다"}`);
    console.log(`    --spacing-control(유틸리티만 쓴다): ${theme.includes("--spacing-control:") ? "나왔다" : "나오지 않았다"}`);
  } else {
    unmeasured += 1;
    console.log(`  ${label}: 측정 아님(컴파일 결과에 @layer theme 이나 .h-control 이 없다)`);
  }
}

console.log("2) optimize 뒤의 hex");
for (const minify of [false, true]) {
  const optimized = tw.optimize(out, { minify });
  const code = String(optimized.code ?? optimized);
  // 줄인 CSS 에서는 블록의 마지막 선언 뒤에 `;` 없이 `}` 가 온다.
  const found = code.match(/--gray-0:[^;}]*|--overlay-black-40:[^;}]*|--overlay-white-10:[^;}]*/g) ?? [];
  if (!found.some((line) => line.startsWith("--gray-0:"))) unmeasured += 1;
  console.log(`  minify ${String(minify)}: ${found.map((line) => line.replace(/\s+/g, "")).join("  ")}`);
}

console.log(`@tailwindcss/node ${version}`);
if (unmeasured > 0) {
  console.log(`측정이 아닌 회차 ${String(unmeasured)}`);
  process.exitCode = 1;
}
