/**
 * 페이지 안 번들(`element.js`)을 주어진 사이트 파일로 주어진 폴더에 한 번 짓고, 걸린 시간과 산출물의 해시를 JSON 한 줄로
 * 찍는다. `measure.mjs` 가 띄운다. 위젯의 빌드 함수(`web/apps/widget/tools/element.ts` 의 `buildElement`)를 그대로 부른다.
 * Vite 가 경고를 stdout 에 찍으므로 결과는 마지막 줄이다.
 *
 * 사용: node element_build.mjs <위젯 앱 폴더> <사이트 파일의 절대 경로 | -> <내는 폴더의 절대 경로>
 *       사이트 파일 자리에 `-` 를 주면 변수를 빼고 짓는다(사이트 없음).
 */

import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [widget, siteFile, outDir] = process.argv.slice(2);
if (
  widget === undefined ||
  siteFile === undefined ||
  outDir === undefined ||
  !path.isAbsolute(widget) ||
  !path.isAbsolute(outDir) ||
  (siteFile !== "-" && !path.isAbsolute(siteFile))
) {
  console.error("사용: node element_build.mjs <위젯 앱 폴더> <사이트 파일 | -> <내는 폴더>. 경로는 모두 절대 경로다.");
  process.exit(2);
}

const importStarted = performance.now();
const { buildElement, ELEMENT_FILE } = await import(pathToFileURL(path.join(widget, "tools", "element.ts")).href);
const importMs = performance.now() - importStarted;

const env = { ...process.env };
if (siteFile === "-") {
  delete env.AGENT_OS_SITE_FILE;
} else {
  env.AGENT_OS_SITE_FILE = siteFile;
}
const buildStarted = performance.now();
await buildElement(env, outDir);
const buildMs = performance.now() - buildStarted;

const bytes = fs.readFileSync(path.join(outDir, ELEMENT_FILE));
console.log(
  JSON.stringify({
    importMs: Math.round(importMs),
    buildMs: Math.round(buildMs),
    bytes: bytes.length,
    sha256: createHash("sha256").update(bytes).digest("hex"),
  }),
);
