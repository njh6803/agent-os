// design-system 디자인 토큰 CSS 를 Vite 라이브러리 모드(페이지 안 위젯 번들의 빌드, ADR 0024)와 Tailwind CLI(패키지의
// build, ADR 0026)가 어떻게 내는지 잰다. tokens/setup.mjs 를 마친 작업 루트에서 돈다(저장소 루트에서 부른다).
//   node .scratch/design-system/probes/tokens/libmode.mjs <작업 루트>/storybook
//
// 재는 것(결과는 <작업 루트>/storybook/libmode.json, 빌드 산출물은 <작업 루트>/storybook/libmode/, stdout 은 요약)
//   fonts-import  진입점이 글꼴 CSS 를 그냥 import 한다. 산출 CSS 의 data:font URL 수와 바이트
//   fonts-inline  진입점이 글꼴 CSS 를 ?inline 으로 받는다(ADR 0024 의 shadow root 길). 산출 JS 의 data:font URL 수와 바이트
//   tokens-inline 디자인 토큰 CSS 에서 글꼴 CSS 의 @import 한 줄만 뺀 사본을 @tailwindcss/vite 를 거쳐 ?inline 으로 받는다.
//                 data:font URL 수, @font-face 수, rem 수, 바이트
//   cli           Tailwind CLI 로 디자인 토큰 CSS 전체를 빌드한 파일의 url() 이 그 파일 자리에서 실제 파일로 풀리는지
// 아무것도 설치하지 않는다. 사본의 packages/ui 에 깔린 vite, @tailwindcss/vite, @tailwindcss/cli 를 쓴다. 글꼴을 뺀 사본은
// 디자인 토큰 CSS 옆에 잠깐 쓰고(@source 의 상대 경로를 지키려고) 끝나면 지운다.

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [wsArg] = process.argv.slice(2);
if (wsArg === undefined) {
  console.error("사용: node libmode.mjs <작업 루트>/storybook");
  process.exit(2);
}
const ws = resolve(wsArg);
const ui = join(ws, "web", "packages", "ui");
const styles = join(ui, "src", "styles");
const out = join(ws, "libmode");
const requireUi = createRequire(join(ui, "package.json"));
// 몇 패키지는 exports 에 package.json 을 두지 않아 resolve 하지 못한다. pnpm 이 패키지의 node_modules 에 둔 링크를 읽는다.
const versionOf = (name) =>
  JSON.parse(readFileSync(join(ui, "node_modules", name, "package.json"), "utf8")).version;
const importUi = async (name) => import(pathToFileURL(requireUi.resolve(name)).href);

const { build } = await importUi("vite");
const tailwind = (await importUi("@tailwindcss/vite")).default;

const result = {
  measuredAt: new Date().toISOString(),
  versions: {
    vite: versionOf("vite"),
    tailwindcss: versionOf("tailwindcss"),
    "@tailwindcss/vite": versionOf("@tailwindcss/vite"),
    "@tailwindcss/cli": versionOf("@tailwindcss/cli"),
    "@fontsource/noto-sans-kr": versionOf("@fontsource/noto-sans-kr"),
    "@fontsource/jetbrains-mono": versionOf("@fontsource/jetbrains-mono"),
    "@ibm/plex-mono": versionOf("@ibm/plex-mono"),
  },
  cases: {},
};

const count = (text, pattern) => (text.match(pattern) ?? []).length;
const tally = (text) => ({
  bytes: Buffer.byteLength(text),
  dataWoff2: count(text, /data:font\/woff2/g),
  dataWoff: count(text, /data:font\/woff[;,]/g),
  fontFace: count(text, /@font-face/g),
  rem: count(text, /\d(?:\.\d+)?rem\b/g),
});

// 진입점 하나를 라이브러리 모드로 빌드하고 산출 파일마다 위의 수를 센다.
async function libBuild(name, entrySource, plugins) {
  const dir = join(out, name);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  const entry = join(dir, "entry.js");
  writeFileSync(entry, entrySource);
  await build({
    configFile: false,
    root: dir,
    logLevel: "warn",
    plugins,
    resolve: { alias: { "ui-probe": ui } },
    build: {
      outDir: join(dir, "dist"),
      emptyOutDir: true,
      lib: { entry, formats: ["es"], fileName: "widget" },
    },
  });
  const files = {};
  for (const file of readdirSync(join(dir, "dist"))) {
    files[file] = tally(readFileSync(join(dir, "dist", file), "utf8"));
  }
  return { entry: entrySource.trim(), files };
}

mkdirSync(out, { recursive: true });

result.cases["fonts-import"] = await libBuild(
  "fonts-import",
  'import "ui-probe/src/styles/fonts.css";\nexport const loaded = true;\n',
  [],
);
result.cases["fonts-inline"] = await libBuild(
  "fonts-inline",
  'import css from "ui-probe/src/styles/fonts.css?inline";\nexport { css };\n',
  [],
);

// 글꼴 CSS 의 @import 한 줄만 뺀 디자인 토큰 CSS. 원본 옆에 두어야 @source ".." 가 같은 자리를 훑는다.
const themeSource = readFileSync(join(styles, "theme.css"), "utf8");
const fontsImport = '@import "./fonts.css";\n';
if (!themeSource.includes(fontsImport)) {
  console.error("디자인 토큰 CSS 에 글꼴 CSS 의 @import 줄이 없다. tokens/setup.mjs 의 생성물인지 본다");
  process.exit(1);
}
const tokensOnly = join(styles, "theme.tokens-only.css");
writeFileSync(tokensOnly, themeSource.replace(fontsImport, ""));
try {
  result.cases["tokens-inline"] = await libBuild(
    "tokens-inline",
    'import css from "ui-probe/src/styles/theme.tokens-only.css?inline";\nexport { css };\n',
    [tailwind()],
  );
} finally {
  rmSync(tokensOnly, { force: true });
}

// 패키지 build 의 CSS 단계. 산출 파일의 url() 이 그 파일 자리에서 풀리는지 본다.
const cliDir = join(out, "cli");
rmSync(cliDir, { recursive: true, force: true });
mkdirSync(cliDir, { recursive: true });
const cliOut = join(cliDir, "ui.css");
const cli = spawnSync(
  process.execPath,
  [join(ui, "node_modules", "@tailwindcss", "cli", "dist", "index.mjs"), "-i", join(styles, "theme.css"), "-o", cliOut],
  { cwd: ui, encoding: "utf8" },
);
if (cli.status !== 0) {
  console.error(cli.stderr);
  process.exit(1);
}
const cliCss = readFileSync(cliOut, "utf8");
const urls = [...cliCss.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)].map((m) => m[1]);
const relative = urls.filter((u) => !u.startsWith("data:"));
const resolved = relative.filter((u) => existsSync(resolve(dirname(cliOut), u)));
// 풀리지 않은 url() 을 출처로 묶는다. Fontsource 는 `./files/<파일>` 이라 앞 두 토막(`./files`)이,
// IBM 은 `../../node_modules/@ibm/plex-mono/…` 라 앞 네 토막(`../../node_modules/@ibm`)이 출처를 가른다.
const prefixes = {};
for (const u of relative) {
  const prefix = u.split("/").slice(0, u.startsWith("..") ? 4 : 2).join("/");
  prefixes[prefix] = (prefixes[prefix] ?? 0) + 1;
}
result.cases.cli = { ...tally(cliCss), urls: relative.length, resolved: resolved.length, prefixes };

writeFileSync(join(ws, "libmode.json"), `${JSON.stringify(result, null, 2)}\n`);

console.log("판", JSON.stringify(result.versions));
for (const [name, c] of Object.entries(result.cases)) {
  if (c.files === undefined) {
    console.log(name, JSON.stringify(c));
    continue;
  }
  for (const [file, s] of Object.entries(c.files)) console.log(name, file, JSON.stringify(s));
}
