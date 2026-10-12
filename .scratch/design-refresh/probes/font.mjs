// design-refresh 글꼴 프로브: 고정폭 글꼴의 npm 패키지 `@fontsource/noto-sans-mono` 가 ADR 0026 의 글꼴 조건(OFL, 자가 호스팅,
// 예약 글꼴 이름을 지키는 판)과 패키지의 글꼴 CSS 모양(굵기 CSS 를 `@import`, `local()` 없음)에 맞는지 본다.
//   node .scratch/design-refresh/probes/font.mjs <작업 폴더> [--version 5.3.0]
//
// 작업 폴더에 `npm pack` 으로 받아 풀고(레지스트리에 닿는다) 그 `package/` 를 읽는다. 저장소에는 아무것도 쓰지 않는다.
// 지금 패키지의 한글 글꼴 `@fontsource/noto-sans-kr` 5.3.0 의 같은 자리(굵기 CSS 의 상대 `url()`, 파일 이름 모양)를 함께
// 받아 견준다. 그 패키지의 CSS 는 Vite(Storybook 빌드)와 Next 16 이 실제 파일로 냈다(.scratch/design-system/probes/tokens/
// measure.mjs, 2026-10-06).
// stdout 은 패키지마다 판, 라이선스, LICENSE 의 예약 글꼴 이름 줄, 설치 때 도는 스크립트, 굵기 400·500 CSS 의 `@font-face` 수와 서브셋 이름,
// `local(` 수, `url()` 의 모양과 가리키는 파일이 있는지, 한글(U+AC00)을 덮는 범위가 있는지, 굵기 하나의 woff2 바이트 합이다.

import { execFileSync, execSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const work = args[0];
if (work === undefined || work.startsWith("--")) {
  console.error("사용: node .scratch/design-refresh/probes/font.mjs <작업 폴더> [--version 5.3.0]");
  process.exit(2);
}
const versionIndex = args.indexOf("--version");
const version = versionIndex === -1 ? "5.3.0" : args[versionIndex + 1];

const PACKAGES = [
  { name: "@fontsource/noto-sans-mono", version, weights: ["400", "500"] },
  { name: "@fontsource/noto-sans-kr", version: "5.3.0", weights: ["400", "500", "600"] },
];

function fetchPackage({ name, version: v }) {
  const dir = resolve(work, name.replace("/", "__"));
  mkdirSync(dir, { recursive: true });
  // Windows 의 npm 은 .cmd 라 셸로 부른다. 넘기는 값은 이 파일의 상수와 인자의 경로뿐이다. npm 의 notice 는 stderr 라 버린다.
  const out = execSync(`npm pack ${name}@${v} --pack-destination "${dir}"`, {
    encoding: "utf-8",
    stdio: ["ignore", "pipe", "ignore"],
  });
  const tarball = out.trim().split(/\r?\n/).pop();
  execFileSync("tar", ["-xzf", tarball], { cwd: dir });
  return join(dir, "package");
}

/** unicode-range 의 범위가 코드 포인트를 덮는지. */
function covers(range, codePoint) {
  return range.split(",").some((part) => {
    const text = part.trim().replace(/^U\+/i, "");
    if (text.includes("?")) {
      const low = parseInt(text.replace(/\?/g, "0"), 16);
      const high = parseInt(text.replace(/\?/g, "F"), 16);
      return codePoint >= low && codePoint <= high;
    }
    const [low, high = low] = text.split("-").map((value) => parseInt(value.replace(/^U\+/i, ""), 16));
    return codePoint >= low && codePoint <= high;
  });
}

for (const pkg of PACKAGES) {
  const root = fetchPackage(pkg);
  const manifest = JSON.parse(readFileSync(join(root, "package.json"), "utf-8"));
  const licenseFile = readdirSync(root).find((file) => /^licen[cs]e/i.test(file));
  const licenseText = licenseFile === undefined ? "" : readFileSync(join(root, licenseFile), "utf-8");
  // 예약 글꼴 이름은 저작권 줄에 "with Reserved Font Name ..." 으로 붙는다. 그 아래 OFL 본문의 정의 문장은 세지 않는다.
  const header = licenseText.split(/This Font Software is licensed/i)[0] ?? "";
  const copyright = header
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line !== "");
  const reserved = copyright.filter((line) => /reserved font name/i.test(line));
  const ofl = /SIL OPEN FONT LICENSE/i.test(licenseText);
  // pnpm 11 은 `allowBuilds` 에 적지 않은 설치 스크립트에서 설치를 멈춘다(ADR 0026 본문). 그래서 설치 때 도는 스크립트가 있는지 본다.
  const lifecycle = Object.keys(manifest.scripts ?? {}).filter((name) =>
    ["preinstall", "install", "postinstall", "prepare"].includes(name),
  );
  console.log(
    `${pkg.name} ${manifest.version} license ${manifest.license} OFL 본문 ${String(ofl)} 저작권 줄 "${copyright.join(" / ")}" 예약 이름 ${reserved.length ? reserved.join(" / ") : "없음"} 설치 스크립트 ${lifecycle.length ? lifecycle.join(", ") : "없음"}`,
  );
  for (const weight of pkg.weights) {
    const cssPath = join(root, `${weight}.css`);
    if (!existsSync(cssPath)) {
      console.log(`  ${weight}.css 없음`);
      continue;
    }
    const css = readFileSync(cssPath, "utf-8");
    const faces = [...css.matchAll(/(?:\/\*\s*([^*]+?)\s*\*\/\s*)?@font-face\s*\{([^}]*)\}/g)];
    const subsets = faces.map(([, comment]) => (comment ?? "").replace(new RegExp(`-${weight}-normal$`), ""));
    const urls = [...css.matchAll(/url\(([^)]+)\)/g)].map(([, url]) => url.replace(/["']/g, ""));
    const missing = urls.filter((url) => !existsSync(resolve(root, url)));
    const prefixes = [...new Set(urls.map((url) => url.replace(/[^/]+$/, "")))];
    const ranges = faces.map(([, , body]) => /unicode-range:\s*([^;]+);/.exec(body)?.[1] ?? "");
    const hangul = ranges.some((range) => range !== "" && covers(range, 0xac00));
    const woff2 = urls
      .filter((url) => url.endsWith(".woff2"))
      .reduce((sum, url) => sum + (existsSync(resolve(root, url)) ? statSync(resolve(root, url)).size : 0), 0);
    console.log(
      `  ${weight}.css @font-face ${String(faces.length)} local( ${String((css.match(/local\(/g) ?? []).length)} url ${String(urls.length)} 없는 파일 ${String(missing.length)} 앞머리 ${prefixes.join(" ")} 한글 U+AC00 ${hangul ? "덮음" : "안 덮음"} woff2 합 ${String(woff2)}B`,
    );
    if (pkg.name.endsWith("mono")) {
      console.log(`    서브셋 ${subsets.join(", ")}`);
    }
  }
}
