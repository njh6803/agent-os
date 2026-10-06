// visual_docker 프로브의 촬영 테스트. run.mjs 가 작업 폴더의 probe/ 로 옮겨 Playwright 컨테이너와 Windows 호스트에서 같은
// 파일로 돌린다. 직접 부르지 않는다(환경 변수는 playwright.config.mjs 머리 주석, VISUAL_SITE 는 표본 폴더).
//
// 색 구성표(light, dark)마다 테스트 하나:
//   1. 표본(site/index.html)을 http://visual.probe/ 아래로 route 해 낸다. 그 출처 밖 요청은 abort 하고 기록한다
//   2. document.fonts.ready 뒤 Pretendard 두 굵기가 loaded 인지 보고, Tab 으로 #btn-focus 에 포커스를 준다
//   3. 원본 스크린샷: 페이지 전체(fullPage)와 영역(REGIONS)마다 요소 스크린샷을 VISUAL_OUT/<구성표>/ 에 쓴다
//   4. toHaveScreenshot: baseline 모드는 정답을 쓰고, compare 모드는 같은 이름을 세 설정(default, maxDiffPixels 0,
//      maxDiffPixels 0 + threshold 0)으로 비교해 통과 여부와 오류 첫 줄들을 기록한다(실패를 잡아 테스트는 이어 간다)
//   5. 재료: 영역 상자, 글자 사각형(Range.getClientRects, 다른 픽셀이 글자 자리인지 가르는 데 쓴다), 제목·버튼의 글자열
//      폭과 요소 폭(WIDTH_TARGETS), CDP 로 영역 글자를
//      그린 플랫폼 글꼴, 브라우저 판과 이 워커가 실제로 띄운 실행 파일, 리눅스면 fc-match 결과와 /etc/os-release,
//      PLAYWRIGHT_BROWSERS_PATH 의 목록
// 결과는 VISUAL_OUT/run-<구성표>.json 이다.
import { execSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, readdirSync, readlinkSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { arch, platform, release } from "node:os";
import { extname, join, normalize, relative } from "node:path";
import { chromium, expect, test } from "@playwright/test";

const SITE = process.env.VISUAL_SITE;
const OUT = process.env.VISUAL_OUT;
const MODE = process.env.VISUAL_MODE;
const ORIGIN = "http://visual.probe";
const REGIONS = ["text-web", "text-system", "box-border", "box-shadow", "box-ring", "box-gradient", "buttons"];
// 폭을 재는 요소. 글자열 폭(Range)과 요소 폭. 같은 글꼴 파일의 글자열이 운영체제마다 폭이 다른지 본다.
const WIDTH_TARGETS = [
  "#text-web h2",
  "#text-system h2",
  "#btn-focus",
  "#buttons .secondary",
  "#buttons .ghost",
  "#buttons .primary:disabled",
  "#btn-native",
];
const SCHEMES = ["light", "dark"];
const VARIANTS = {
  default: {},
  maxDiffPixels0: { maxDiffPixels: 0 },
  strict: { maxDiffPixels: 0, threshold: 0 },
};
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".woff2": "font/woff2",
};

const require = createRequire(import.meta.url);
const version = (name) => require(`${name}/package.json`).version;
const stripAnsi = (text) => text.replace(/\u001b\[[0-9;]*m/g, "");
const tryRun = (command) => {
  try {
    return execSync(command, { encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] }).trim();
  } catch (error) {
    return `error: ${String(error).split("\n")[0]}`;
  }
};

function linuxFacts() {
  if (platform() !== "linux") {
    return null;
  }
  const osRelease = existsSync("/etc/os-release")
    ? (/^PRETTY_NAME="?([^"\n]*)"?$/m.exec(readFileSync("/etc/os-release", "utf-8"))?.[1] ?? null)
    : null;
  return {
    osRelease,
    fcMatch: {
      "system-ui": tryRun("fc-match system-ui"),
      "sans-serif": tryRun("fc-match sans-serif"),
      "sans-serif:lang=ko": tryRun("fc-match sans-serif:lang=ko"),
      monospace: tryRun("fc-match monospace"),
    },
    fcListCount: tryRun("fc-list | wc -l"),
  };
}

function browsersPathListing() {
  const dir = process.env.PLAYWRIGHT_BROWSERS_PATH ?? null;
  if (dir === null || !existsSync(dir)) {
    return { dir, entries: null };
  }
  return { dir, entries: readdirSync(dir).sort() };
}

// 페이지 안에서 돈다. 영역 상자와 글자 사각형(문서 좌표, 소수 둘째 자리), 요소마다 글자열 폭과 요소 폭
function geometry({ regionIds, widthTargets }) {
  const round = (value) => Math.round(value * 100) / 100;
  const rect = (r) => ({
    x: round(r.left + window.scrollX),
    y: round(r.top + window.scrollY),
    width: round(r.width),
    height: round(r.height),
  });
  const regions = Object.fromEntries(
    regionIds.map((id) => [id, rect(document.getElementById(id).getBoundingClientRect())]),
  );
  const textRects = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node !== null; node = walker.nextNode()) {
    if (node.textContent.trim() === "") {
      continue;
    }
    const range = document.createRange();
    range.selectNodeContents(node);
    for (const r of range.getClientRects()) {
      if (r.width > 0 && r.height > 0) {
        textRects.push(rect(r));
      }
    }
  }
  const widths = Object.fromEntries(
    widthTargets.map((selector) => {
      const element = document.querySelector(selector);
      const range = document.createRange();
      range.selectNodeContents(element);
      return [
        selector,
        { text: round(range.getBoundingClientRect().width), box: round(element.getBoundingClientRect().width) },
      ];
    }),
  );
  return {
    regions,
    textRects,
    widths,
    documentSize: { width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight },
    devicePixelRatio: window.devicePixelRatio,
  };
}

async function platformFonts(page, selectors) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("DOM.enable");
  await cdp.send("CSS.enable");
  const { root } = await cdp.send("DOM.getDocument", { depth: -1 });
  const found = {};
  for (const selector of selectors) {
    const { nodeIds } = await cdp.send("DOM.querySelectorAll", { nodeId: root.nodeId, selector });
    const counts = {};
    for (const nodeId of nodeIds) {
      const { fonts } = await cdp.send("CSS.getPlatformFontsForNode", { nodeId });
      for (const font of fonts) {
        const key = `${font.familyName}${font.isCustomFont ? " (custom)" : ""}`;
        counts[key] = (counts[key] ?? 0) + font.glyphCount;
      }
    }
    found[selector] = counts;
  }
  await cdp.detach();
  return found;
}

async function browserFacts(browser) {
  const cdp = await browser.newBrowserCDPSession();
  const info = await cdp.send("Browser.getVersion");
  await cdp.detach();
  return {
    version: browser.version(),
    product: info.product,
    revision: info.revision,
    userAgent: info.userAgent,
    launchedExecutables: launchedExecutables(),
  };
}

// 이 워커가 띄운 자식 프로세스의 실행 파일. chromium.executablePath() 는 설치 위치만 알려 주고 실제로 뜬 것(전체 chromium 인지
// headless shell 인지)은 알려 주지 않는다. CDP Browser.getBrowserCommandLine 은 --enable-automation 이 없어 거절된다.
function launchedExecutables() {
  if (platform() === "linux") {
    const found = new Set();
    for (const pid of readdirSync("/proc").filter((name) => /^\d+$/.test(name))) {
      try {
        const stat = readFileSync(`/proc/${pid}/stat`, "utf-8");
        const parent = Number(stat.slice(stat.lastIndexOf(")") + 2).split(" ")[1]);
        if (parent === process.pid) {
          found.add(readlinkSync(`/proc/${pid}/exe`));
        }
      } catch {
        // 그 사이 끝난 프로세스
      }
    }
    return [...found].sort();
  }
  if (platform() === "win32") {
    const listed = tryRun(
      `powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter 'ParentProcessId=${String(process.pid)}' | Select-Object -ExpandProperty ExecutablePath | Sort-Object -Unique"`,
    );
    // 이 조회를 돌린 셸(cmd.exe, powershell.exe)은 뺀다.
    return listed
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line !== "" && !/\\(cmd|powershell)\.exe$/i.test(line));
  }
  return null;
}

for (const scheme of SCHEMES) {
  test(scheme, async ({ page, browser }) => {
    test.setTimeout(120_000);
    const started = Date.now();
    const external = [];
    await page.emulateMedia({ colorScheme: scheme });
    await page.context().route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.origin !== ORIGIN) {
        external.push(url.href);
        await route.abort();
        return;
      }
      const file = normalize(join(SITE, decodeURIComponent(url.pathname)));
      if (relative(SITE, file).startsWith("..") || !existsSync(file)) {
        await route.fulfill({ status: 404, body: "" });
        return;
      }
      await route.fulfill({
        status: 200,
        body: readFileSync(file),
        contentType: TYPES[extname(file)] ?? "application/octet-stream",
      });
    });

    await page.goto(`${ORIGIN}/index.html`, { waitUntil: "load" });
    const fonts = await page.evaluate(async () => {
      await document.fonts.ready;
      return [...document.fonts].map((font) => ({ family: font.family, weight: font.weight, status: font.status }));
    });
    const probeFonts = fonts.filter((font) => font.family.includes("Pretendard Probe"));
    expect(probeFonts.map((font) => font.status)).toEqual(["loaded", "loaded"]);
    await page.keyboard.press("Tab");
    const focus = await page.evaluate(() => ({
      id: document.activeElement?.id ?? null,
      focusVisible: document.activeElement?.matches(":focus-visible") ?? false,
    }));

    // 3. 원본 스크린샷
    const dir = join(OUT, scheme);
    mkdirSync(dir, { recursive: true });
    const rawStarted = Date.now();
    await page.screenshot({ path: join(dir, "page.png"), fullPage: true, animations: "disabled" });
    for (const id of REGIONS) {
      await page.locator(`#${id}`).screenshot({ path: join(dir, `${id}.png`), animations: "disabled" });
    }
    const rawMs = Date.now() - rawStarted;

    // 4. toHaveScreenshot
    const shots = [
      { name: `page-${scheme}.png`, target: page, options: { fullPage: true } },
      ...REGIONS.map((id) => ({ name: `${id}-${scheme}.png`, target: page.locator(`#${id}`), options: {} })),
    ];
    const checks = [];
    const assertStarted = Date.now();
    for (const shot of shots) {
      const variants = MODE === "baseline" ? { write: {} } : VARIANTS;
      for (const [variant, extra] of Object.entries(variants)) {
        try {
          await expect(shot.target).toHaveScreenshot(shot.name, { ...shot.options, ...extra });
          checks.push({ name: shot.name, variant, pass: true });
        } catch (error) {
          const lines = stripAnsi(String(error.message ?? error))
            .split("\n")
            .map((line) => line.trim())
            .filter((line) => line !== "");
          checks.push({ name: shot.name, variant, pass: false, message: lines.slice(0, 4).join(" | ") });
        }
      }
    }
    const assertMs = Date.now() - assertStarted;

    // 5. 재료
    const geo = await page.evaluate(geometry, { regionIds: REGIONS, widthTargets: WIDTH_TARGETS });
    // CSS.getPlatformFontsForNode 는 그 노드의 자식 텍스트 노드만 본다. 글자를 직접 가진 요소를 고른다.
    const usedFonts = await platformFonts(page, [
      "#text-web h2",
      "#text-web p",
      "#text-web code",
      "#text-system h2",
      "#text-system p",
      "#text-system code",
      "#buttons .btn",
      "#btn-native",
    ]);
    const facts = {
      scheme,
      mode: MODE,
      platform: `${platform()} ${release()} ${arch()}`,
      node: process.version,
      packages: {
        "@playwright/test": version("@playwright/test"),
        playwright: version("playwright"),
        "playwright-core": version("playwright-core"),
      },
      browser: await browserFacts(browser),
      executablePath: chromium.executablePath(),
      browsersPath: browsersPathListing(),
      linux: linuxFacts(),
      fonts,
      focus,
      external,
      geometry: geo,
      platformFonts: usedFonts,
      checks,
      timing: { testMs: Date.now() - started, rawScreenshotsMs: rawMs, toHaveScreenshotMs: assertMs },
    };
    writeFileSync(join(OUT, `run-${scheme}.json`), `${JSON.stringify(facts, null, 2)}\n`);
    expect(external).toEqual([]);
  });
}
