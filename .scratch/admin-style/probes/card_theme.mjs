// admin-style 카드 테마 프로브: 설정 화면의 테마 카드처럼 `data-theme` 만 달고 `data-mode` 를 달지 않은 안쪽 요소가,
// 시스템 라이트와 시스템 다크에서 그 테마의 그 모드 값을 받는지 본다.
//   node .scratch/admin-style/probes/card_theme.mjs [node_modules 가 있는 web 폴더, 기본 web]
//
// 까닭: ADR 0026 의 첫째 2026-10-12 이력은 카드마다 `data-theme` 을 다는 미리보기를 재지 않았다고 적고 명세에 넘겼다.
// 디자인 토큰 CSS 에 `[data-theme]:not([data-mode])` 선택자가 있는 것만 읽었다. 패키지의 미디어 특성 테스트
// (`web/packages/ui/visual/media.visual.ts`)는 문서 뿌리와 shadow 호스트만 보고 안쪽 요소는 보지 않는다.
//
// 자리: 관리 화면처럼 `html` 에 모드는 달지 않는다. 뿌리는 둘이다. 운영자가 기본이 아닌 테마(쪽빛)를 고른 뿌리와, 아무것도
// 고르지 않아 속성이 없는(기본 테마 녹청으로 그려지는) 뿌리다. 그 안에 테마 넷의 카드(테마만), 테마 넷의 기준(그 테마와 그
// 회차의 모드를 명시), 속성 없는 요소 하나를 둔다. 기준이 명시 모드라, 카드가 기준과 같으면 시스템 모드의 선택자가 그 테마의
// 원색과 그 모드의 대응을 함께 풀었다는 뜻이다.
// 결과를 본 뒤 더한 갈래: 첫 실행(2026-10-26)은 쪽빛 뿌리만 쟀다. 셀프 리뷰가 가장 흔한 속성 없는 뿌리를 재지 않았다고 짚어
// 둘째 실행부터 그 뿌리를 더했다. 판정 기준은 그대로다.
//
// 디자인 토큰 CSS 는 패키지의 `theme.css` 를 Tailwind CLI 로 임시 폴더에 컴파일한 것이다. 관리 화면은 Next 의
// `@tailwindcss/postcss` 로 컴파일하므로 같은 엔진의 다른 입구다. Next 빌드에서 그 CSS 가 서는지는 이 프로브가 보지 않는다.
// 쓰임새 토큰의 이름은 그 파일의 `:root, :host, [data-theme], [data-mode]` 블록에서 읽는다.
//
// 측정의 표지(회차는 뿌리 하나와 시스템 모드 하나): `matchMedia("(prefers-color-scheme: dark)")` 가 그 회차의 모드와 맞고,
// 테마 넷의 기준이 `--accent` 에서 서로 다르며(카드와 기준을 맞대는 것이 테마를 가른다), 쓰임새 토큰을 하나 이상 읽은 회차만
// 측정으로 센다.
// 양성 대조: `html`(모드 없음)이 뿌리의 테마(쪽빛, 속성이 없으면 녹청)의 기준과 같다(이미 판정 스토리와 미디어 특성 테스트가
// 보는 뿌리의 갈래).
// 갈래: 속성 없는 안쪽 요소는 뿌리의 테마의 기준과 같고 군청 기준과 다르다. 카드가 테마를 따르는 것이 "모든 안쪽 요소가 같은
// 값을 받는다"는 해석이 아님을 가른다.
// 기대: 카드 넷이 모두 그 테마의 기준과 쓰임새 토큰 전부에서 같다.
// stdout 은 회차마다 JSON 한 줄과 끝의 집계 줄이다. 측정 아닌 회차가 있거나 기대와 다른 것이 있으면 종료 코드가 1 이다.

import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const web = resolve(process.argv[2] ?? "web");
const requireWeb = createRequire(join(web, "package.json"));
const requireUi = createRequire(join(web, "packages", "ui", "package.json"));
const { chromium } = (await import(pathToFileURL(requireWeb.resolve("playwright")).href)).default;

const THEMES = ["guncheong", "nokcheong", "jacho", "jjokbit"];
const DEFAULT_THEME = "nokcheong";
// 뿌리에 단 테마. null 은 속성이 없는 뿌리이고 기본 테마로 그려진다.
const ROOTS = ["jjokbit", null];
const SCHEMES = ["light", "dark"];

const source = join(web, "packages", "ui", "src", "styles", "theme.css");
const block = readFileSync(source, "utf8").match(
  /:root,\s*:host,\s*\[data-theme\],\s*\[data-mode\]\s*\{([^}]*)\}/,
);
const names = block ? [...block[1].matchAll(/(--[a-z0-9-]+)\s*:/g)].map((m) => m[1]) : [];

const work = mkdtempSync(join(tmpdir(), "admin-style-card-theme-"));
const cliPackage = requireUi.resolve("@tailwindcss/cli/package.json");
const cli = join(dirname(cliPackage), JSON.parse(readFileSync(cliPackage, "utf8")).bin.tailwindcss);
const compiled = join(work, "theme.css");
const built = spawnSync(process.execPath, [cli, "-i", source, "-o", compiled], { encoding: "utf8" });
if (built.status !== 0) {
  console.error(built.stderr);
  rmSync(work, { recursive: true, force: true });
  process.exit(1);
}
const css = readFileSync(compiled, "utf8");
rmSync(work, { recursive: true, force: true });

const page = (root, scheme) => `<!doctype html>
<html${root === null ? "" : ` data-theme="${root}"`}><head><style>${css}</style></head><body>
${THEMES.map((t) => `<div id="card-${t}" data-theme="${t}"></div>`).join("\n")}
${THEMES.map((t) => `<div id="ref-${t}" data-theme="${t}" data-mode="${scheme}"></div>`).join("\n")}
<div id="plain"></div>
</body></html>`;

const browser = await chromium.launch();
let measured = 0;
let notMeasured = 0;
let unexpected = 0;
for (const [root, scheme] of ROOTS.flatMap((r) => SCHEMES.map((s) => [r, s]))) {
  const rootTheme = root ?? DEFAULT_THEME;
  const context = await browser.newContext({ colorScheme: scheme });
  const tab = await context.newPage();
  await tab.setContent(page(root, scheme));
  const read = await tab.evaluate((list) => {
    const values = (element) => list.map((name) => getComputedStyle(element).getPropertyValue(name).trim());
    const byId = (id) => values(document.getElementById(id));
    const ids = [...document.querySelectorAll("[id]")].map((element) => element.id);
    return {
      dark: matchMedia("(prefers-color-scheme: dark)").matches,
      root: values(document.documentElement),
      byId: Object.fromEntries(ids.map((id) => [id, byId(id)])),
    };
  }, names);
  await context.close();

  const accentAt = names.indexOf("--accent");
  const refAccents = new Set(THEMES.map((t) => read.byId[`ref-${t}`][accentAt]));
  const marker = read.dark === (scheme === "dark") && refAccents.size === THEMES.length && names.length > 0;
  const same = (a, b) => a.length === b.length && a.every((value, i) => value === b[i]);
  const differing = (a, b) => names.filter((_, i) => a[i] !== b[i]);
  const cards = Object.fromEntries(
    THEMES.map((t) => [t, differing(read.byId[`card-${t}`], read.byId[`ref-${t}`])]),
  );
  const rootControl = same(read.root, read.byId[`ref-${rootTheme}`]);
  const plainFollowsRoot = same(read.byId.plain, read.byId[`ref-${rootTheme}`]);
  const plainDiffersFromGuncheong = !same(read.byId.plain, read.byId["ref-guncheong"]);
  const cardsFollow = Object.values(cards).every((list) => list.length === 0);
  if (marker) {
    measured += 1;
    if (!(cardsFollow && rootControl && plainFollowsRoot && plainDiffersFromGuncheong)) {
      unexpected += 1;
    }
  } else {
    notMeasured += 1;
  }
  console.log(
    JSON.stringify({
      root,
      scheme,
      measurement: marker,
      tokens: names.length,
      cardsDifferingTokens: cards,
      rootControl,
      plainFollowsRoot,
      plainDiffersFromGuncheong,
    }),
  );
}
console.log(`chromium ${browser.version()}`);
await browser.close();
console.log(`측정 ${measured}, 측정 아님 ${notMeasured}, 기대와 다름 ${unexpected}`);
process.exit(notMeasured > 0 || unexpected > 0 ? 1 : 0);
