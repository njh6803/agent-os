/**
 * 위젯 빌드의 앞 단계(글꼴 복사, 페이지 안 번들의 Vite 빌드)만 프로세스 안에서 따로 잰다. `measure.mjs phases` 가 띄운다.
 * 위젯의 시작 래퍼(`web/apps/widget/tools/start.ts`)의 `prepare` 가 하는 일을 같은 함수로 같은 차례로 부른다.
 * `next build` 는 부르지 않는다.
 *
 * 마지막 stdout 줄이 결과 JSON 이다. `startupMs` 는 부모가 프로세스를 띄운 때(`AGENT_OS_PROBE_SPAWNED_AT`, epoch ms)부터
 * 이 모듈의 몸통에 닿기까지, `importMs` 는 번들 빌드 모듈(vite, @tailwindcss/vite 포함)과 글꼴 도우미를 적재한 시간이다.
 *
 * 사용: node phases.mjs <위젯 앱 폴더>   (환경: AGENT_OS_SITE_FILE, AGENT_OS_PROBE_SPAWNED_AT)
 */

import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const reachedAt = Date.now();
const spawnedAt = Number(process.env.AGENT_OS_PROBE_SPAWNED_AT);
const widget = process.argv[2];
if (widget === undefined || !path.isAbsolute(widget)) {
  console.error("사용: node phases.mjs <위젯 앱 폴더의 절대 경로>");
  process.exit(2);
}
const fromWidget = createRequire(path.join(widget, "package.json"));
const fontsTarget = path.join(widget, "public", "fonts");

const importStarted = performance.now();
const element = await import(pathToFileURL(path.join(widget, "tools", "element.ts")).href);
const fonts = await import(pathToFileURL(fromWidget.resolve("@agent-os/ui/fonts")).href);
const imported = performance.now();
fonts.copyFonts(fontsTarget);
const copied = performance.now();
await element.buildElement(process.env);
const built = performance.now();

console.log(
  JSON.stringify({
    startupMs: Number.isFinite(spawnedAt) ? reachedAt - spawnedAt : null,
    importMs: imported - importStarted,
    copyFontsMs: copied - imported,
    buildElementMs: built - copied,
    fontFiles: fs.readdirSync(fontsTarget).length,
    elementBytes: fs.statSync(path.join(widget, "public", element.ELEMENT_FILE)).size,
  }),
);
