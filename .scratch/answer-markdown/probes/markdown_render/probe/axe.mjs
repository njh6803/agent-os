// 접근성 프로브(2026-11-11). 합친 시제품(apps/widget/components/molecules/AnswerMarkdown.tsx)을 브라우저 프로브와 같은
// 묶음으로 Chromium 페이지의 폭 320px 칸 안에 그리고 axe-core 를 돌려, 표를 감싸는 스크롤 칸의 네 모양과 코드 블록의
// 세 모양에서 어떤 규칙이 걸리는지 본다.
//
// 돌리기: node probe/axe.mjs
// 산출물: out/axe/summary.json, out/axe/report.txt, 표준 출력의 마지막 줄(JSON 한 줄)
//
// axe 의 설정은 저장소의 스토리 테스트와 같게 둔다. @storybook/addon-a11y 10.6 은 `region` 규칙만 끄고
// (`axe.configure({ rules: [{ id: "region", enabled: false }] })`) 옵션 없이 `axe.run` 을 부른다(주 체크아웃에 설치된
// dist/_browser-chunks 의 원문에서 읽었다). 패키지의 미리보기는 `a11y: { test: "error" }` 만 준다. axe-core 의 판은
// web/pnpm-lock.yaml 과 같은 4.14.0 이어야 하고, 다르면 아무것도 재지 않는다.
// 바깥 구조는 위젯의 대화 목록과 같다(`div[role=region][aria-label=대화][tabindex=0]` 안의 `ol > li`).
//
// 갈래
//   control  손으로 지은 조각으로 규칙이 이 환경에서 실제로 걸리는지 본다(양성 대조)와, 걸리지 않아야 할 짝(음성 대조).
//   table    표 입력 넷(좁은 표 하나·넓은 표 하나·좁은 표 둘·넓은 표 둘) × 스크롤 칸 넷(region·group·focusable·plain).
//   code     코드 입력 셋(짧은 것·넘치는 것·넘치는 것 둘) × 코드 블록 셋(focusable·plain·group).
//   screens  화면 파일의 입력 다섯을 고른 모양(region·focusable)으로 라이트와 다크에서 그린다.
// 브라우저는 browser.mjs 와 같은 둘이다(chromium, headless-shell).
//
// 측정이 아닌 회차(.claude/rules/probes.md)
// - axe 의 판이 4.14.0 이 아니거나, 묶음에 React 의 production 파일이 없으면 아무것도 재지 않는다.
// - control: 양성 대조는 기대한 규칙이 violations 에 있어야 하고 음성 대조는 없어야 한다. 어긋난 규칙은 그 브라우저에서
//   갈래를 가르지 못한다.
// - 그린 회차: 칸에 시제품이 그려지고(`[data-answer="markdown"]`), 표·코드 블록의 수가 입력과 같고, 넘쳐야 할 입력은
//   스크롤 칸이 실제로 넘치고(scrollWidth > clientWidth) 넘치지 않아야 할 입력은 넘치지 않아야 한다.
// - 보는 규칙(`WATCHED`)마다 axe 가 그 규칙을 violations·passes·incomplete·inapplicable 가운데 하나로 분류해야 한다.
// 하나라도 어긋나면 notMeasured 에 적고 종료 코드 1.
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { chromium } from "playwright";
import { bundle, chromiumPath, openPage, pageHtml, PLAYWRIGHT_VERSION, readJson, ROOT, settle } from "./browser-kit.mjs";
import { SCREEN_INPUTS } from "./shape-cases.mjs";

const OUT = join(ROOT, "out", "axe");
const AXE_WANT = "4.14.0";
const AXE_PATH = join(ROOT, "node_modules", "axe-core", "axe.min.js");
const AXE_VERSION = readJson(join(ROOT, "node_modules", "axe-core", "package.json")).version;
const TARGETS = [
  { name: "chromium", options: { channel: "chromium" } },
  { name: "headless-shell", options: {} },
];
/** 갈래를 가르는 데 쓰는 규칙. 회차마다 axe 가 어느 묶음에 넣었는지 적는다. */
const WATCHED = ["scrollable-region-focusable", "landmark-unique", "aria-allowed-role", "color-contrast"];

const FENCE = "```";
const NARROW_TABLE = ["| 항목 | 값 |", "|---|---|", "| 기간 | 1년 |", "| 급여 | 80% |"].join("\n");
const WIDE_TABLE = [
  "| 구분 | 대상 | 기간 | 급여 | 신청 기한 | 비고 |",
  "|---|---|---|---|---|---|",
  "| 육아휴직 | 만 8세 이하 자녀 | 최대 1년 | 통상임금의 80% | 시작 30일 전 | 두 번 나눠 쓸 수 있음 |",
  "| 출산휴가 | 출산 전후 | 90일 | 통상임금 전액 | 시작 전 | 다태아는 120일 |",
].join("\n");
const LONG_LINE = `curl -X POST https://hr.example.com/api/v1/leave-requests -H "Content-Type: application/json" -d '{"type":"parental"}'`;
const SHORT_CODE = [`${FENCE}bash`, "ls -la", FENCE].join("\n");
const WIDE_CODE = [`${FENCE}bash`, LONG_LINE, FENCE].join("\n");

const TABLE_CASES = [
  { id: "table-narrow", text: `표입니다.\n\n${NARROW_TABLE}`, tables: 1, pres: 0, overflow: false },
  { id: "table-wide", text: `표입니다.\n\n${WIDE_TABLE}`, tables: 1, pres: 0, overflow: true },
  { id: "table-narrow-x2", text: `${NARROW_TABLE}\n\n사이의 글입니다.\n\n${NARROW_TABLE}`, tables: 2, pres: 0, overflow: false },
  { id: "table-wide-x2", text: `${WIDE_TABLE}\n\n사이의 글입니다.\n\n${WIDE_TABLE}`, tables: 2, pres: 0, overflow: true },
];
const CODE_CASES = [
  { id: "code-short", text: `명령입니다.\n\n${SHORT_CODE}`, tables: 0, pres: 1, overflow: false },
  { id: "code-wide", text: `명령입니다.\n\n${WIDE_CODE}`, tables: 0, pres: 1, overflow: true },
  { id: "code-wide-x2", text: `${WIDE_CODE}\n\n사이의 글입니다.\n\n${WIDE_CODE}`, tables: 0, pres: 2, overflow: true },
];
const TABLE_BOXES = ["region", "group", "focusable", "plain"];
const CODE_BLOCKS = ["focusable", "plain", "group"];
const PICKED = { tableBox: "region", codeBlock: "focusable" };

// 손으로 지은 대조. `expect` 의 규칙이 violations 에 있어야 하고 `absent` 의 규칙은 없어야 한다.
const WIDE_CELLS = `<table><tbody><tr>${"<td>넓은 칸의 글입니다</td>".repeat(6)}</tr></tbody></table>`;
const PIXEL = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
const CONTROLS = [
  { id: "plain-text", html: '<div class="md"><p>보통 글입니다.</p></div>', expect: [], absent: ["scrollable-region-focusable", "landmark-unique", "image-alt"] },
  { id: "image-without-alt", html: `<div class="md"><p><img src="${PIXEL}"></p></div>`, expect: ["image-alt"], absent: [] },
  {
    id: "same-name-regions",
    html: '<div class="md"><div role="region" aria-label="표" tabindex="0"><p>하나</p></div><div role="region" aria-label="표" tabindex="0"><p>둘</p></div></div>',
    expect: ["landmark-unique"],
    absent: [],
  },
  {
    id: "different-name-regions",
    html: '<div class="md"><div role="region" aria-label="표 1" tabindex="0"><p>하나</p></div><div role="region" aria-label="표 2" tabindex="0"><p>둘</p></div></div>',
    expect: [],
    absent: ["landmark-unique"],
  },
  {
    id: "same-name-groups",
    html: '<div class="md"><div role="group" aria-label="표" tabindex="0"><p>하나</p></div><div role="group" aria-label="표" tabindex="0"><p>둘</p></div></div>',
    expect: [],
    absent: ["landmark-unique"],
  },
  { id: "scroller-without-focus", html: `<div class="md"><div class="tbl">${WIDE_CELLS}</div></div>`, expect: ["scrollable-region-focusable"], absent: [] },
  { id: "scroller-with-focus", html: `<div class="md"><div class="tbl" tabindex="0">${WIDE_CELLS}</div></div>`, expect: [], absent: ["scrollable-region-focusable"] },
];

const notMeasured = [];

/** 페이지 안에서 도는 함수. 스토리 테스트와 같은 설정으로 axe 를 돌리고 묶음마다 규칙 ID 를 낸다. */
async function axeInPage() {
  await new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  });
  axe.configure({ rules: [{ id: "region", enabled: false }] });
  const result = await axe.run(document, {});
  const ids = (list) => list.map((entry) => entry.id);
  return {
    version: axe.version,
    violations: result.violations.map((entry) => ({
      id: entry.id,
      impact: entry.impact,
      nodes: entry.nodes.map((node) => ({ target: node.target.join(" "), html: node.html.slice(0, 120), summary: (node.failureSummary ?? "").slice(0, 200) })),
    })),
    incomplete: result.incomplete.map((entry) => ({ id: entry.id, nodes: entry.nodes.length })),
    passes: ids(result.passes),
    inapplicable: ids(result.inapplicable),
  };
}

/** 페이지 안에서 도는 함수. 칸에 그려진 것의 수와 스크롤 칸의 넘침을 낸다. */
function shapeInPage() {
  const host = document.getElementById("host");
  const scrollers = [...host.querySelectorAll(".tbl, pre")].map((element) => ({
    tag: element.tagName.toLowerCase(),
    role: element.getAttribute("role"),
    label: element.getAttribute("aria-label"),
    tabindex: element.getAttribute("tabindex"),
    overflows: element.scrollWidth > element.clientWidth,
    scrollWidth: element.scrollWidth,
    clientWidth: element.clientWidth,
  }));
  return {
    markdown: host.querySelector('[data-answer="markdown"]') !== null,
    tables: host.querySelectorAll("table").length,
    pres: host.querySelectorAll("pre").length,
    scrollers,
  };
}

/** 규칙이 어느 묶음에 들었는지. 어디에도 없으면 null 이다(그 회차는 그 규칙을 잰 것이 아니다). */
function bucketOf(result, rule) {
  if (result.violations.some((entry) => entry.id === rule)) return "violations";
  if (result.incomplete.some((entry) => entry.id === rule)) return "incomplete";
  if (result.passes.includes(rule)) return "passes";
  if (result.inapplicable.includes(rule)) return "inapplicable";
  return null;
}

function watched(result, where) {
  const buckets = {};
  for (const rule of WATCHED) {
    buckets[rule] = bucketOf(result, rule);
    if (buckets[rule] === null) notMeasured.push({ ...where, reason: `axe 가 ${rule} 규칙을 분류하지 않았다` });
  }
  return buckets;
}

async function runAxe(page, where) {
  const settled = await settle(page.evaluate(axeInPage), 30_000);
  if (settled.value === undefined) {
    notMeasured.push({ ...where, reason: "axe 가 끝나지 않았다", problem: settled });
    return null;
  }
  if (settled.value.version !== AXE_WANT) {
    notMeasured.push({ ...where, reason: `페이지의 axe 판이 ${settled.value.version} 이다(기대 ${AXE_WANT})` });
    return null;
  }
  return settled.value;
}

async function withPage(browser, made, mode, run) {
  const { context, page, events } = await openPage(browser, pageHtml({ mode, conversation: "region" }), made.outfile);
  try {
    await page.addScriptTag({ path: AXE_PATH });
    return await run(page, events);
  } finally {
    await settle(context.close(), 15_000);
  }
}

async function runControls(browser, target, made) {
  const rows = [];
  for (const control of CONTROLS) {
    const where = { part: "control", browser: target.name, id: control.id };
    const row = await withPage(browser, made, "light", async (page) => {
      await page.evaluate((html) => {
        document.getElementById("host").innerHTML = html;
      }, control.html);
      const result = await runAxe(page, where);
      if (result === null) return null;
      const violated = result.violations.map((entry) => entry.id);
      const missing = control.expect.filter((rule) => !violated.includes(rule));
      const unexpected = control.absent.filter((rule) => violated.includes(rule));
      if (missing.length > 0 || unexpected.length > 0) {
        notMeasured.push({ ...where, reason: "대조가 기대와 다르다", missing, unexpected, violated });
      }
      return { browser: target.name, id: control.id, expect: control.expect, absent: control.absent, violated, ok: missing.length === 0 && unexpected.length === 0 };
    });
    if (row !== null) rows.push(row);
  }
  return rows;
}

async function runCase(browser, target, made, group, item, config, mode) {
  const where = { part: group, browser: target.name, id: item.id, tableBox: config.tableBox, codeBlock: config.codeBlock, mode };
  return withPage(browser, made, mode, async (page, events) => {
    const drawn = await settle(
      page.evaluate(({ mount, text }) => MdProbe.mount(mount, text), { mount: { mode: "direct", plugins: "combined", handlers: "default", ...config }, text: item.text }),
      30_000,
    );
    if (drawn.value?.state !== "markdown") {
      notMeasured.push({ ...where, reason: "시제품이 그려지지 않았다", drawn: drawn.value?.state ?? drawn });
      return null;
    }
    const shape = await page.evaluate(shapeInPage);
    const problems = [];
    if (item.tables !== undefined && shape.tables !== item.tables) problems.push(`표가 ${shape.tables}개다(기대 ${item.tables})`);
    if (item.pres !== undefined && shape.pres !== item.pres) problems.push(`코드 블록이 ${shape.pres}개다(기대 ${item.pres})`);
    if (item.overflow !== undefined) {
      const overflowing = shape.scrollers.filter((scroller) => scroller.overflows).length;
      const want = item.overflow ? shape.scrollers.length : 0;
      if (shape.scrollers.length === 0 || overflowing !== want) problems.push(`넘치는 스크롤 칸이 ${overflowing}/${shape.scrollers.length}개다(기대 ${want})`);
    }
    if (events.pageErrors.length > 0) problems.push(`페이지 오류 ${events.pageErrors.length}건`);
    if (problems.length > 0) {
      notMeasured.push({ ...where, reason: problems.join(", "), scrollers: shape.scrollers });
      return null;
    }
    const result = await runAxe(page, where);
    if (result === null) return null;
    return {
      ...where,
      shape: { tables: shape.tables, pres: shape.pres, scrollers: shape.scrollers.map((s) => `${s.tag}[role=${s.role ?? "-"}][tabindex=${s.tabindex ?? "-"}]${s.overflows ? " 넘침" : ""}`) },
      violations: result.violations,
      incomplete: result.incomplete,
      watched: watched(result, where),
    };
  });
}

function reportText(summary) {
  const lines = [];
  const say = (line = "") => lines.push(line);
  say(`접근성 프로브 (axe-core ${summary.versions.axe}, Playwright ${summary.versions.playwright}, ${JSON.stringify(summary.versions.browsers)})`);
  say();
  say("== 대조 ==");
  for (const row of summary.controls) {
    say(`  ${row.browser} ${row.id}: 위반 [${row.violated.join(", ")}] ${row.ok ? "기대대로" : "기대와 다름"}`);
  }
  for (const group of ["table", "code", "screens"]) {
    say();
    say(`== ${group} ==`);
    for (const row of summary[group]) {
      const variant = group === "code" ? `codeBlock=${row.codeBlock}` : group === "table" ? `tableBox=${row.tableBox}` : `${row.mode}`;
      const violated = row.violations.map((entry) => `${entry.id}(${entry.impact}, ${entry.nodes.length}곳)`).join(", ");
      const incomplete = row.incomplete.map((entry) => `${entry.id}(${entry.nodes}곳)`).join(", ");
      say(`  ${row.browser} ${row.id} ${variant}: 위반 [${violated}] 판정 못 함 [${incomplete}]`);
      say(`      ${WATCHED.map((rule) => `${rule}=${row.watched[rule]}`).join(" ")}`);
      for (const entry of row.violations) {
        for (const node of entry.nodes.slice(0, 2)) say(`      ${entry.id}: ${node.target} | ${node.summary.replaceAll("\n", " / ")}`);
      }
    }
  }
  if (summary.notMeasured.length > 0) {
    say();
    say("== 측정이 아닌 회차 ==");
    for (const entry of summary.notMeasured) say(`  ${JSON.stringify(entry).slice(0, 400)}`);
  }
  return `${lines.join("\n")}\n`;
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  if (chromiumPath() === null) {
    console.log(JSON.stringify({ probe: "axe", chromium: null, reason: `Playwright ${PLAYWRIGHT_VERSION} 이 찾는 Chromium 이 없다(내려받지 않았다)` }));
    process.exit(3);
  }
  if (AXE_VERSION !== AXE_WANT) {
    console.log(JSON.stringify({ probe: "axe", notMeasured: 1, reason: `설치된 axe-core 가 ${AXE_VERSION} 이다(기대 ${AXE_WANT})` }));
    process.exit(1);
  }
  // 브라우저 프로브와 같은 입구를 묶되 산출 자리를 따로 둔다(둘이 함께 돌아도 서로의 묶음을 덮어쓰지 않는다).
  const made = await bundle({
    entry: join(ROOT, "probe", "browser-entry.tsx"),
    outfile: join(OUT, "browser-entry.js"),
    format: "iife",
    platform: "browser",
    globalName: "MdProbe",
    mustBundle: ["react-dom/cjs/react-dom-client.production.js", "react/cjs/react.production.js", "react-markdown/lib/index.js"],
  });
  if (made.problems.length > 0) {
    console.error("묶음이 기대와 다르다", made.problems);
    console.log(JSON.stringify({ probe: "axe", notMeasured: made.problems.length, bundleProblems: made.problems }));
    process.exit(1);
  }

  const summary = { probe: "axe", versions: { axe: AXE_VERSION, playwright: PLAYWRIGHT_VERSION, node: process.version, browsers: {} }, watched: WATCHED, controls: [], table: [], code: [], screens: [], notMeasured };
  for (const target of TARGETS) {
    let browser;
    try {
      browser = await chromium.launch(target.options);
    } catch (error) {
      console.log(JSON.stringify({ probe: "axe", browser: target.name, reason: `띄우지 못했다(내려받지 않았다): ${String(error).slice(0, 300)}` }));
      process.exit(3);
    }
    try {
      summary.versions.browsers[target.name] = browser.version();
      summary.controls.push(...(await runControls(browser, target, made)));
      for (const item of TABLE_CASES) {
        for (const tableBox of TABLE_BOXES) {
          const row = await runCase(browser, target, made, "table", item, { ...PICKED, tableBox }, "light");
          if (row !== null) summary.table.push(row);
        }
      }
      for (const item of CODE_CASES) {
        for (const codeBlock of CODE_BLOCKS) {
          const row = await runCase(browser, target, made, "code", item, { ...PICKED, codeBlock }, "light");
          if (row !== null) summary.code.push(row);
        }
      }
      for (const [id, text] of Object.entries(SCREEN_INPUTS)) {
        for (const mode of ["light", "dark"]) {
          const row = await runCase(browser, target, made, "screens", { id, text }, PICKED, mode);
          if (row !== null) summary.screens.push(row);
        }
      }
    } finally {
      await settle(browser.close(), 15_000);
    }
  }

  writeFileSync(join(OUT, "summary.json"), JSON.stringify(summary, null, 2));
  writeFileSync(join(OUT, "report.txt"), reportText(summary));
  const brief = (rows, key) => rows.map((row) => `${row.browser} ${row.id} ${key(row)}: [${row.violations.map((entry) => entry.id).join(",")}]`);
  console.log(
    JSON.stringify({
      probe: "axe",
      versions: summary.versions,
      notMeasured: notMeasured.length,
      controls: summary.controls.map((row) => `${row.browser} ${row.id}: [${row.violated.join(",")}]${row.ok ? "" : " 기대와 다름"}`),
      table: brief(summary.table, (row) => row.tableBox),
      code: brief(summary.code, (row) => row.codeBlock),
      screens: brief(summary.screens, (row) => row.mode),
    }),
  );
  if (notMeasured.length > 0) {
    console.error("측정이 아닌 회차", JSON.stringify(notMeasured, null, 2).slice(0, 4000));
    process.exit(1);
  }
}

await main();
