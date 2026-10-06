// design-system 디자인 토큰 프로브의 측정. tokens/setup.mjs 를 마친 작업 루트에서 돈다(저장소 루트에서 부른다).
//   node .scratch/design-system/probes/tokens/measure.mjs <작업 루트>/storybook
//
// 재는 것(결과는 <작업 루트>/storybook/tokens.json, stdout 은 요약)
//   stories  스토리 테스트(vitest --project storybook, 실제 chromium, Vite 개발 서버). 판정 함수와 기대값은
//            Tokens.stories.tsx 에 있다: 안쪽 요소의 열 벌 계산값·명암비, 표본 컴포넌트의 클래스, 심은 클래스를 잡는
//            것, 글꼴 일곱 벌의 FontFace 적재
//   vite     storybook build(Vite 빌드)가 낸 글꼴 파일의 수·바이트, 빌드 CSS 의 url() 이 가리키는 파일이 있는지
//   switch   정적 빌드를 Playwright chromium 으로 열어(http://sb.probe/ 로 route, 밖의 요청은 abort 하고 센다) 쓰임새
//            토큰 26개의 계산값을 디자인 파일 값과 맞춘다. 자리는 셋: 문서 뿌리(html 의 data-theme·data-mode), 모드가
//            없을 때 prefers-color-scheme(emulateMedia), shadow 호스트(문서의 시트를 모두 끈 뒤 shadow 안의 표본)
//   fonts    정적 빌드에서 테마마다 KoreanSample 을 그릴 때 받는 글꼴 파일과 바이트
//   states   정적 빌드에서 열 벌마다 주 버튼을 Playwright 의 실제 마우스로 올리고 누르고, 키보드 Tab 으로 포커스했을 때의
//            배경과 outline 이 쓰임새 토큰(accent, accent-hover, accent-press, focus)의 값인지
//   motion   정적 빌드의 Motion 스토리에서 움직임 줄이기가 없을 때와 있을 때(reducedMotion) 도는 표시와 값 모름 진행
//            막대의 계산된 animation-name
//   switch 의 속성 없는 사례 넷: 데코레이터가 단 data-theme·data-mode 를 문서 뿌리나 shadow 호스트에서 지운 뒤 시스템
//            모드 둘에서 먹의 값인지
//   fontFaces  Fontsource 굵기 CSS 의 @font-face 수
//   next     apps/admin 을 next build 하고 빌드 CSS 의 @font-face url() 이 .next/static/media 의 파일을 가리키는지,
//            next start 로 띄운 / 에서 html 의 쓰임새 토큰과 글꼴 적재
// 아무것도 설치하지 않는다. 사본의 Playwright 1.63.0 chromium 이 %LOCALAPPDATA%\ms-playwright 에 있어야 한다.
// 8796~8799 에서 빈 포트 하나를 쓴다(next start).

import { spawn, spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { createServer } from "node:net";
import { extname, join, resolve } from "node:path";
import { expectedSemantic, readDesign, semanticNames } from "./design.mjs";

const [wsArg] = process.argv.slice(2);
if (wsArg === undefined) {
  console.error("사용: node measure.mjs <작업 루트>/storybook");
  process.exit(2);
}
const ws = resolve(wsArg);
const web = join(ws, "web");
const ui = join(web, "packages", "ui");
const admin = join(web, "apps", "admin");
const { chromium } = createRequire(join(web, "package.json"))("playwright");

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
};

const design = readDesign();
const THEMES = Object.keys(design.tokens.themes);
const SEMANTIC = semanticNames(design.tokens);
const expected = (theme, mode) => expectedSemantic(design.tokens, theme, mode);
const result = { measuredAt: new Date().toISOString() };

// 글꼴 패키지 CSS 의 @font-face 수(굵기 하나의 동적 서브셋 조각 수)
{
  const count = (path) => (readFileSync(path, "utf-8").match(/@font-face/g) ?? []).length;
  const fontsource = join(ui, "node_modules", "@fontsource");
  result.fontFaces = Object.fromEntries(
    [
      ["noto-sans-kr/400.css", join(fontsource, "noto-sans-kr", "400.css")],
      ["noto-sans-kr/500.css", join(fontsource, "noto-sans-kr", "500.css")],
      ["noto-sans-kr/600.css", join(fontsource, "noto-sans-kr", "600.css")],
      ["jetbrains-mono/400.css", join(fontsource, "jetbrains-mono", "400.css")],
    ].map(([label, path]) => [label, count(path)]),
  );
  console.log("[font-faces]", JSON.stringify(result.fontFaces));
}

// stories -------------------------------------------------------------------------------------------------------
{
  const out = join(ws, "tokens-stories.json");
  const run = sh("pnpm", ["exec", "vitest", "run", "--project", "storybook", "--reporter=json", `--outputFile=${out}`], web);
  const report = JSON.parse(readFileSync(out, "utf-8"));
  result.stories = {
    exit: run.status,
    ms: run.ms,
    tests: report.testResults.flatMap((file) =>
      file.assertionResults.map((test) => ({ name: test.fullName, status: test.status })),
    ),
  };
  console.log(`[stories] exit ${String(run.status)} ${String(run.ms)}ms`, result.stories.tests.map((t) => `${t.name}:${t.status}`).join(" | "));
}

// vite ----------------------------------------------------------------------------------------------------------
const staticDir = join(ui, "storybook-static");
{
  const run = sh("pnpm", ["exec", "storybook", "build", "--quiet"], ui);
  const files = filesUnder(staticDir);
  const fonts = files.filter((path) => [".woff2", ".woff"].includes(extname(path)));
  const css = files.filter((path) => extname(path) === ".css");
  const urls = css.flatMap((path) =>
    [...readFileSync(path, "utf-8").matchAll(/url\(\s*["']?([^"')]+\.(?:woff2|woff))["']?\s*\)/g)].map((m) => ({ css: path, url: m[1] })),
  );
  const missing = urls.filter(({ css: from, url }) => !existsSync(resolve(join(from, ".."), url.split("?")[0])));
  result.vite = {
    exit: run.status,
    ms: run.ms,
    fontFiles: { woff2: fonts.filter((p) => p.endsWith(".woff2")).length, woff: fonts.filter((p) => p.endsWith(".woff")).length },
    fontBytes: fonts.reduce((sum, path) => sum + statSync(path).size, 0),
    cssFiles: css.map((path) => ({ path: path.slice(staticDir.length + 1), bytes: statSync(path).size })),
    fontUrls: urls.length,
    missingFontUrls: missing.slice(0, 10),
  };
  console.log(`[vite] exit ${String(run.status)} ${String(run.ms)}ms`, JSON.stringify({ ...result.vite, cssFiles: result.vite.cssFiles.length }));
}

// switch & fonts --------------------------------------------------------------------------------------------------
{
  const browser = await chromium.launch();
  const outside = [];
  const open = async ({ story, globals, colorScheme = "light", reducedMotion = "no-preference" }) => {
    const context = await browser.newContext({ colorScheme, reducedMotion });
    const page = await context.newPage();
    const served = [];
    await page.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.host !== "sb.probe") {
        outside.push(url.href);
        await route.abort();
        return;
      }
      const path = join(staticDir, decodeURIComponent(url.pathname));
      if (!existsSync(path) || statSync(path).isDirectory()) {
        await route.fulfill({ status: 404, body: "" });
        return;
      }
      const body = readFileSync(path);
      served.push({ path: url.pathname, bytes: body.length });
      await route.fulfill({ status: 200, body, contentType: TYPES[extname(path)] ?? "application/octet-stream" });
    });
    const query = Object.entries(globals)
      .map(([key, value]) => `${key}:${value}`)
      .join(";");
    const id = story.includes("--") ? story : `probe-tokens--${story}`;
    await page.goto(`http://sb.probe/iframe.html?id=${id}&viewMode=story&globals=${query}`);
    return { context, page, served };
  };
  const readValues = (page, where) =>
    page.evaluate(
      ({ names, where: place }) => {
        let element = document.documentElement;
        if (place === "sample") {
          element = document.querySelector("[data-probe=sample]");
        }
        if (place === "root-bare") {
          // 데코레이터가 단 속성을 지운다. 속성이 없는 문서는 먹이고 모드는 시스템이어야 한다.
          delete document.documentElement.dataset.theme;
          delete document.documentElement.dataset.mode;
        }
        if (place === "shadow" || place === "shadow-bare") {
          for (const sheet of document.styleSheets) {
            sheet.disabled = true;
          }
          const host = document.querySelector("[data-shadow-frame]");
          if (place === "shadow-bare" && host) {
            delete host.dataset.theme;
            delete host.dataset.mode;
          }
          element = host?.shadowRoot?.querySelector("[data-probe=sample]");
        }
        if (!element) {
          return null;
        }
        const style = getComputedStyle(element);
        return Object.fromEntries(names.map((name) => [name, style.getPropertyValue(`--${name}`).trim().toUpperCase()]));
      },
      { names: SEMANTIC, where },
    );
  const compare = (got, want) =>
    got === null ? ["표본 없음"] : SEMANTIC.filter((name) => got[name] !== want[name]).map((name) => `${name} ${got[name]}!=${want[name]}`);

  const cases = [];
  for (const theme of THEMES) {
    for (const mode of ["light", "dark"]) {
      cases.push({ label: `root ${theme}/${mode}`, story: "sample", globals: { theme, mode, shadow: "off" }, where: "root", want: mode });
      cases.push({ label: `sample ${theme}/${mode}`, story: "sample", globals: { theme, mode, shadow: "off" }, where: "sample", want: mode });
      cases.push({ label: `system ${theme}/${mode}`, story: "sample", globals: { theme, mode: "system", shadow: "off" }, where: "root", want: mode, colorScheme: mode });
      cases.push({ label: `shadow ${theme}/${mode}`, story: "sample", globals: { theme, mode, shadow: "on" }, where: "shadow", want: mode });
      cases.push({ label: `shadow-system ${theme}/${mode}`, story: "sample", globals: { theme, mode: "system", shadow: "on" }, where: "shadow", want: mode, colorScheme: mode });
    }
  }
  // 속성 없는 뿌리와 호스트: 데코레이터가 청록·다크를 단 뒤 지우고, 시스템 모드 둘에서 먹의 값인지 본다.
  for (const scheme of ["light", "dark"]) {
    cases.push({ label: `root-bare ${scheme}`, story: "sample", globals: { theme: "cheongnok", mode: "dark", shadow: "off" }, where: "root-bare", want: scheme, wantTheme: "muk", colorScheme: scheme });
    cases.push({ label: `shadow-bare ${scheme}`, story: "sample", globals: { theme: "cheongnok", mode: "dark", shadow: "on" }, where: "shadow-bare", want: scheme, wantTheme: "muk", colorScheme: scheme });
  }
  result.switch = [];
  for (const c of cases) {
    const { context, page } = await open(c);
    if (c.where.startsWith("shadow")) {
      await page.waitForFunction(() => document.querySelector("[data-shadow-frame]")?.shadowRoot?.querySelector("[data-probe=sample]") != null);
    } else {
      await page.waitForSelector("[data-probe=sample]");
    }
    const theme = c.wantTheme ?? c.globals.theme;
    const diffs = compare(await readValues(page, c.where), expected(theme, c.want));
    result.switch.push({ label: c.label, diffs });
    await context.close();
  }
  const bad = result.switch.filter((c) => c.diffs.length > 0);
  console.log(`[switch] ${String(result.switch.length)} 사례, 어긋난 사례 ${String(bad.length)}`, bad.slice(0, 5).map((c) => `${c.label}: ${c.diffs.slice(0, 3).join(", ")}`).join(" | "));

  result.fonts = [];
  for (const theme of THEMES) {
    const { context, page, served } = await open({ story: "korean-sample", globals: { theme, mode: "light", shadow: "off" } });
    await page.waitForSelector("text=실행이 실패했습니다.");
    await page.evaluate(async () => {
      await document.fonts.ready;
    });
    await page.waitForTimeout(300);
    const faces = await page.evaluate(() =>
      [...document.fonts].filter((f) => f.status === "loaded").map((f) => `${f.family.replaceAll('"', "")} ${f.weight}`),
    );
    const fontFiles = served.filter((s) => /\.(woff2|woff)$/.test(s.path));
    result.fonts.push({
      theme,
      files: fontFiles.length,
      bytes: fontFiles.reduce((sum, s) => sum + s.bytes, 0),
      faces: [...new Set(faces)].sort(),
      woff: fontFiles.filter((s) => s.path.endsWith(".woff")).length,
    });
    await context.close();
  }
  console.log("[fonts]", result.fonts.map((f) => `${f.theme} ${String(f.files)}파일 ${String(f.bytes)}B woff${String(f.woff)} [${f.faces.join(", ")}]`).join(" | "));
  // 실제 입력(Playwright 의 마우스와 키보드)의 상태 색. 스토리 테스트의 userEvent 는 합성 이벤트라 :hover·:active 가
  // 걸리지 않았다(Button.stories.tsx 의 States). 테마마다 라이트·다크로 주 버튼을 올리고, 누르고, Tab 으로 포커스한다.
  result.states = [];
  for (const theme of THEMES) {
    for (const mode of ["light", "dark"]) {
      const { context, page } = await open({ story: "atoms-button--primary", globals: { theme, mode, shadow: "off" } });
      const button = page.getByRole("button", { name: "승인" });
      await button.waitFor();
      const read = () =>
        button.evaluate((element) => {
          const style = getComputedStyle(element);
          const root = getComputedStyle(document.documentElement);
          const hex = (name) => root.getPropertyValue(`--${name}`).trim();
          const rgb = (value) => {
            const probe = document.createElement("div");
            probe.style.color = value;
            document.body.append(probe);
            const out = getComputedStyle(probe).color;
            probe.remove();
            return out;
          };
          return {
            background: style.backgroundColor,
            outline: `${style.outlineStyle} ${style.outlineColor}`,
            tokens: { accent: rgb(hex("accent")), hover: rgb(hex("accent-hover")), press: rgb(hex("accent-press")), focus: rgb(hex("focus")) },
          };
        });
      const initial = await read();
      await button.hover();
      const hovered = await read();
      await page.mouse.down();
      const pressed = await read();
      await page.mouse.up();
      // 누르면 버튼이 포커스를 받는다. 그대로 Tab 을 누르거나 blur() 뒤에 누르면 순차 탐색이 버튼 다음 자리에서
      // 시작해 버튼에 오지 않았다(2026-10-06 첫 실행, 열 벌 모두 outline none). 빈 자리(1, 1)를 눌러 출발점을 문서
      // 처음으로 돌린 뒤 Tab 을 누른다.
      await page.mouse.click(1, 1);
      await page.keyboard.press("Tab");
      const focused = await read();
      const t = initial.tokens;
      result.states.push({
        label: `${theme}/${mode}`,
        default: initial.background === t.accent,
        hover: hovered.background === t.hover,
        press: pressed.background === t.press,
        focus: focused.outline === `solid ${t.focus}`,
        raw: { initial: initial.background, hovered: hovered.background, pressed: pressed.background, focused: focused.outline, tokens: t },
      });
      await context.close();
    }
  }
  const stateBad = result.states.filter((s) => !(s.default && s.hover && s.press && s.focus));
  console.log(`[states] ${String(result.states.length)} 벌, 어긋난 벌 ${String(stateBad.length)}`, stateBad.slice(0, 3).map((s) => JSON.stringify(s)).join(" | "));

  // 움직임: 우리 `--animate-spin`·`--animate-progress` 가 도는지, 움직임 줄이기에서 `motion-reduce:animate-none` 이
  // 멈추는지(계산된 animation-name).
  result.motion = [];
  for (const reducedMotion of ["no-preference", "reduce"]) {
    const { context, page } = await open({ story: "motion", globals: { theme: "muk", mode: "light", shadow: "off" }, reducedMotion });
    await page.waitForSelector("[data-probe=spinner]");
    const names = await page.evaluate(() =>
      ["spinner", "bar"].map((probe) => {
        const element = document.querySelector(`[data-probe=${probe}]`);
        return `${probe} ${element ? getComputedStyle(element).animationName : "없음"}`;
      }),
    );
    result.motion.push({ reducedMotion, names });
    await context.close();
  }
  console.log("[motion]", JSON.stringify(result.motion));

  result.outsideRequests = [...new Set(outside)];
  console.log(`[outside] ${String(result.outsideRequests.length)}`, result.outsideRequests.slice(0, 5).join(" "));
  await browser.close();
}

// next ----------------------------------------------------------------------------------------------------------
{
  const build = sh("pnpm", ["--filter", "@agent-os/admin", "build"], web);
  const nextStatic = join(admin, ".next", "static");
  const css = existsSync(nextStatic) ? filesUnder(nextStatic).filter((path) => extname(path) === ".css") : [];
  // Next 16 은 CSS 를 .next/static/chunks/ 에 두고 글꼴을 그 CSS 에서 상대 경로(../media/…)로 가리킨다. 2026-10-06 첫
  // 실행은 이것을 static 기준으로 풀어 778개 모두를 없다고 잘못 셌다(next start 의 글꼴 응답은 모두 200 이었다).
  const urls = css.flatMap((path) =>
    [...readFileSync(path, "utf-8").matchAll(/url\(\s*["']?([^"')]+\.(?:woff2|woff))["']?\s*\)/g)].map((m) => ({ css: path, url: m[1] })),
  );
  const missing = urls
    .filter(({ css: from, url }) => {
      const local = url.startsWith("/_next/static/") ? join(nextStatic, url.slice("/_next/static/".length)) : resolve(join(from, ".."), url);
      return !existsSync(local);
    })
    .map(({ url }) => url);
  const media = existsSync(join(nextStatic, "media")) ? filesUnder(join(nextStatic, "media")) : [];
  result.next = {
    buildExit: build.status,
    buildMs: build.ms,
    buildTail: build.output.split("\n").slice(-25).join("\n"),
    cssFiles: css.map((path) => ({ path: path.slice(nextStatic.length + 1), bytes: statSync(path).size })),
    fontFaces: css.reduce((sum, path) => sum + (readFileSync(path, "utf-8").match(/@font-face/g) ?? []).length, 0),
    fontUrls: urls.length,
    sampleUrls: urls.slice(0, 3).map(({ url }) => url),
    missingFontUrls: missing.slice(0, 10),
    mediaFiles: media.length,
    mediaBytes: media.reduce((sum, path) => sum + statSync(path).size, 0),
  };
  console.log(`[next build] exit ${String(build.status)} ${String(build.ms)}ms`, JSON.stringify({ ...result.next, buildTail: undefined, cssFiles: result.next.cssFiles.length }));

  if (build.status === 0) {
    const port = await freePort([8796, 8797, 8798, 8799]);
    const server = spawn(process.execPath, [join(admin, "node_modules", "next", "dist", "bin", "next"), "start", "-p", String(port)], {
      cwd: admin,
      stdio: "ignore",
    });
    try {
      await waitForPort(port, 30_000);
      const browser = await chromium.launch();
      const page = await browser.newPage();
      const fontResponses = [];
      page.on("response", (response) => {
        if (/\.(woff2|woff)(\?|$)/.test(response.url())) {
          fontResponses.push(response.status());
        }
      });
      await page.goto(`http://127.0.0.1:${String(port)}/`);
      await page.evaluate(async () => {
        await document.fonts.ready;
      });
      const probe = await page.evaluate(async () => {
        const faces = await document.fonts.load('400 16px "Noto Sans KR"', "가");
        const style = getComputedStyle(document.documentElement);
        return {
          bg: style.getPropertyValue("--bg").trim(),
          text: style.getPropertyValue("--text").trim(),
          fontFamily: getComputedStyle(document.body).fontFamily,
          notoLoaded: faces.map((face) => face.status),
        };
      });
      result.next.start = { port, ...probe, fontResponses };
      console.log("[next start]", JSON.stringify(result.next.start));
      await browser.close();
    } finally {
      server.kill();
    }
  }
}

writeFileSync(join(ws, "tokens.json"), `${JSON.stringify(result, null, 2)}\n`);
console.log(`결과: ${join(ws, "tokens.json")}`);

// ---------------------------------------------------------------------------------------------------------------

function sh(command, args, cwd) {
  const started = Date.now();
  // 윈도우의 pnpm 은 .cmd 라 셸로 부른다. 인자는 이 파일의 상수와 작업 루트 안의 경로뿐이다.
  const viaShell = process.platform === "win32" && command === "pnpm";
  const run = viaShell
    ? spawnSync([command, ...args.map((a) => (a.includes(" ") ? `"${a}"` : a))].join(" "), { cwd, encoding: "utf-8", shell: true, maxBuffer: 64 * 1024 * 1024 })
    : spawnSync(command, args, { cwd, encoding: "utf-8", maxBuffer: 64 * 1024 * 1024 });
  return { status: run.status, ms: Date.now() - started, output: `${run.stdout ?? ""}${run.stderr ?? ""}` };
}

function filesUnder(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory() ? filesUnder(join(dir, entry.name)) : [join(dir, entry.name)],
  );
}

function freePort(candidates) {
  return candidates.reduce(
    (found, port) =>
      found.then(
        (value) =>
          value ??
          new Promise((done) => {
            const server = createServer();
            server.once("error", () => done(null));
            server.listen(port, "127.0.0.1", () => server.close(() => done(port)));
          }),
      ),
    Promise.resolve(null),
  ).then((port) => {
    if (port === null) {
      throw new Error(`빈 포트가 없다: ${candidates.join(", ")}`);
    }
    return port;
  });
}

async function waitForPort(port, timeoutMs) {
  const until = Date.now() + timeoutMs;
  while (Date.now() < until) {
    try {
      const response = await fetch(`http://127.0.0.1:${String(port)}/`);
      if (response.status > 0) {
        return;
      }
    } catch {
      await new Promise((done) => setTimeout(done, 300));
    }
  }
  throw new Error(`next start 가 ${String(timeoutMs)}ms 안에 뜨지 않았다`);
}
