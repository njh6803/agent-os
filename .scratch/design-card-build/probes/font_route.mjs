// 티켓 01의 "글꼴 대조를 먼저 본다". 짓기 시험이 카드를 싣는 길(문서의 기준 주소가 산출 폴더의
// `components/<이름>/preview.html`)에서, 묶음 CSS의 글꼴 주소가 `../../fonts/`면 Noto Sans KR이 실리고 `../fonts/`로 바꾸면
// 글꼴 오류가 나는지를 `file://` 문서와 요청 가로채기(`route`)로 산출 폴더를 내준 `http` 문서의 두 길에서 잰다. 실제 페이지에서
// `../fonts/`가 하나도 실리지 않고 `../../fonts/`가 실린 것(README "실제 페이지"의 판 4·5)을 시험의 길이 재현하는지 보는 것이다.
//
// 돌리는 법(저장소 루트에서): node .scratch/design-card-build/probes/font_route.mjs <작업 폴더의 절대 경로>
// 작업 폴더는 아직 없는 절대 경로여야 한다(이 프로브는 아무 폴더도 지우지 않는다). 짓기 명령(`assemble`)을 그 아래 `out/`으로
// 한 번 돌리고, `file://` 길은 진단 문서를 `out/components/Button/` 안에 써서 연다(산출을 고치므로 그 산출은 다른 데 쓰지 않는다).
//
// 회차와 표지: 길(`file`, `route`)과 주소(`positive`는 지은 그대로의 `../../fonts/`, `negative`는 `../fonts/`로 바꾼 것)의 짝 넷.
// 표지는 문서가 카드 자리(`/components/Button/`)에서 열렸고, 문서에 Noto Sans KR의 FontFace가 하나 이상 있으며(묶음 CSS의
// `@font-face`를 읽었다) 한글 글이 문서에 있는 것이다. 이 표지는 양성과 음성 모두에서 나야 하는 "잴 상황이 났다"의
// 표지이고, 두 주소를 가르는 것은 결과(실림과 글꼴 오류)다. 표지가 없는 회차는 측정이 아니라고 세고, 그런 회차가 하나라도
// 있거나 짓기가 실패하면 종료 1이다. 결과: 길마다 갈렸는지(`splits`)를 찍는다. 갈림은 양성이 실림 1 이상·글꼴 오류 0이고
// 음성이 실림 0·글꼴 오류 1 이상인 것이다. 갈리지 않은 길은 티켓의 멈춤 조건이라 종료 코드와 따로 요약에 적는다. 요약에는
// `HEAD`와 짓기 명령·디자인 시스템 패키지 아래 커밋하지 않은 변경의 수도 적는다.
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { pathToFileURL } from "node:url";

const [work] = process.argv.slice(2);
if (work === undefined || !path.isAbsolute(work) || fs.existsSync(work)) {
  console.error("작업 폴더는 아직 없는 절대 경로여야 한다");
  process.exit(2);
}
fs.mkdirSync(work);
const repo = process.cwd();
const out = path.join(work, "out");
const git = (args) => spawnSync("git", args, { cwd: repo, encoding: "utf8", timeout: 30_000 }).stdout.trim();
const head = git(["rev-parse", "--short", "HEAD"]);
const uncommitted = git(["status", "--porcelain", "--", "web/tools/sync-design-system", "web/packages/ui"])
  .split("\n")
  .filter((line) => line !== "").length;

const built = spawnSync(
  process.execPath,
  ["web/tools/sync-design-system/main.ts", "assemble", "--out", out, "--paths", path.join(work, "paths.json")],
  { cwd: repo, encoding: "utf8", timeout: 300_000 },
);
if (built.status !== 0) {
  console.log(JSON.stringify({ head, uncommitted, assemble: built.stdout.trim(), stderr: built.stderr.slice(-2000) }));
  process.exit(1);
}

const { chromium } = await import(pathToFileURL(path.join(repo, "web/node_modules/playwright/index.mjs")).href);
const bundleCss = fs.readFileSync(path.join(out, "components/bundle.css"), "utf8");
const variants = {
  positive: bundleCss,
  negative: bundleCss.replaceAll("url(../../fonts/", "url(../fonts/"),
};
const doc = (css) => `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head>
<body><p id="t" style="font-family:'Noto Sans KR';font-size:20px">한글 글꼴이 실리는지 본다 가나다라마바사</p></body></html>`;
const contentType = (file) => (file.endsWith(".woff2") ? "font/woff2" : file.endsWith(".woff") ? "font/woff" : undefined);

async function measure(page) {
  return page.evaluate(async () => {
    await document.fonts.ready;
    await new Promise((resolve) => setTimeout(resolve, 500));
    await document.fonts.ready;
    const faces = [...document.fonts].filter((face) => face.family.replaceAll('"', "") === "Noto Sans KR");
    return {
      faces: faces.length,
      loaded: faces.filter((face) => face.status === "loaded").length,
      errors: [...document.fonts].filter((face) => face.status === "error").length,
      text: document.getElementById("t")?.textContent?.length ?? 0,
      at: location.pathname,
    };
  });
}

/** 잴 상황이 났다는 표지. 문서가 카드 자리에서 열렸고 묶음 CSS 의 글꼴과 한글 글이 문서에 있다. */
const marked = (seen) => seen.at.includes("/components/Button/") && seen.faces > 0 && seen.text > 0;

const browser = await chromium.launch();
const rounds = [];
try {
  for (const [label, css] of Object.entries(variants)) {
    {
      const file = path.join(out, "components/Button/__font_route.html");
      fs.writeFileSync(file, doc(css));
      const page = await browser.newPage();
      try {
        await page.goto(pathToFileURL(file).href);
        const seen = await measure(page);
        rounds.push({ way: "file", label, marked: marked(seen), ...seen });
      } finally {
        await page.close();
        fs.rmSync(file);
      }
    }
    {
      const page = await browser.newPage();
      const origin = "http://card.test";
      await page.route(`${origin}/**`, async (route) => {
        const { pathname } = new URL(route.request().url());
        if (pathname === "/components/Button/preview.html") {
          return route.fulfill({ status: 200, contentType: "text/html; charset=utf-8", body: doc(css) });
        }
        const file = path.join(out, ...decodeURIComponent(pathname).split("/").filter(Boolean));
        if (!fs.existsSync(file)) return route.fulfill({ status: 404, body: "" });
        return route.fulfill({ status: 200, body: fs.readFileSync(file), contentType: contentType(file) });
      });
      try {
        await page.goto(`${origin}/components/Button/preview.html`);
        const seen = await measure(page);
        rounds.push({ way: "route", label, marked: marked(seen), ...seen });
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}
const notMeasured = rounds.filter((round) => !round.marked).length;
// 측정인 회차만으로 가른다. 한쪽이라도 측정이 아니면 그 길은 `null`이다.
const splits = Object.fromEntries(
  ["file", "route"].map((way) => {
    const of = (label) => rounds.find((round) => round.way === way && round.label === label && round.marked);
    const positive = of("positive");
    const negative = of("negative");
    if (positive === undefined || negative === undefined) return [way, null];
    return [way, positive.loaded > 0 && positive.errors === 0 && negative.loaded === 0 && negative.errors > 0];
  }),
);
console.log(
  JSON.stringify({ head, uncommitted, rounds, measured: rounds.length - notMeasured, notMeasured, splits }, null, 2),
);
process.exit(notMeasured > 0 ? 1 : 0);
