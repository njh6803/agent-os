// 브라우저 프로브(2026-11-11). 합친 시제품(apps/widget/components/molecules/AnswerMarkdown.tsx)을 esbuild 로 묶어(React 는
// production 으로 품는다) Playwright 의 Chromium 페이지에서 폭 320px 칸 안에 그리고, 여덟 가지를 잰다.
//
// 돌리기: node probe/browser.mjs                 (여덟 부분 모두. out/browser/summary.json 을 쓴다. 10분 넘게 걸린다)
//         node probe/browser.mjs capture fine    (고른 부분만. 요약은 out/browser/partial.json 에 쓴다)
//         node probe/browser.mjs sweep --only=quote:   (이름에 그 조각이 든 입력만. 손으로 볼 때 쓴다)
// 산출물: out/browser/summary.json, out/browser/report.txt, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 브라우저는 둘이고 둘 다 설치된 Playwright 의 판이 이미 내려받아 둔 것이다(내려받지 않는다. 없으면 종료 코드 3).
//   chromium        온전한 Chromium 을 새 헤드리스 모드로 띄운 것(`channel: "chromium"`). 사람이 쓰는 Chrome 에 가깝다.
//   headless-shell  Playwright 가 헤드리스에서 기본으로 띄우는 것(chromium_headless_shell). 저장소의 e2e 가 도는 브라우저다.
// 둘을 가른 까닭: 첫 판은 기본(headless-shell)만 썼는데, 깊이 200 의 겹친 인용에서 렌더러가 죽었다. 손으로 갈라 보니
// CSS 없이 손으로 지은 div 200겹도 headless-shell 에서는 죽고 온전한 Chromium 에서는 죽지 않았다.
//
// 부분
//   capture    실패를 받는 두 방법(`Markdown` 을 직접 불러 try/catch, 에러 경계)을 `>` 3,000개 입력으로 견준다.
//   stages     입력마다 어느 단계에서 던지는지 Node 와 두 브라우저에서 가른다(표지와 스택. stage-run.tsx 머리 주석).
//   threshold  `Markdown` 이 던지기 시작하는 깊이를 좁히고, 던지지 않는 가장 깊은 깊이 언저리에서 시제품을 그려 본다.
//   sweep      깊이 50~3,000 의 겹친 인용·목록과 병적인 입력 열넷을 시제품으로 그리고 화면을 잰다.
//   crash      렌더러가 죽기 시작하는 깊이를 좁힌다. 시제품과, CSS 없이 손으로 지은 div 를 견준다.
//   guard      깊이 가드를 켠 갈래로 한도 바로 아래·위와 sweep 의 깊이 입력을 그려, 한도 이하는 그리고 넘으면 원문을
//              보이는지 본다(runGuard 의 주석).
//   fine       깊이 1~40 을 한 겹씩 그려 화면이 가로로 넘치기 시작하는 깊이를 찾는다.
//   heights    (가)③: 한 줄 바꿈을 CSS `white-space` 로 보일 때 블록 사이의 줄 끝 글자가 빈 줄이 되는지 높이로 본다.
//
// 측정이 아닌 회차(.claude/rules/probes.md)
// - 묶음: React 의 production 파일이 묶이고 development 파일이 없어야 한다. 어긋나면 아무것도 재지 않는다.
// - capture: 받지 않는 대조(view)에서 `>` 3,000개가 실제로 실패해야 한다(페이지 오류가 찍히고 칸이 빈다). 그렇지 않으면
//   견준 것이 아니다. 갈래마다 첫 단계(보통 글)가 마크다운으로 그려져야 한다.
// - stages: 던진 회차는 표지가 가리키는 단계와 스택이 가리키는 단계가 맞아야 한다. 던지지 않은 깊이 입력은 거르기가
//   요소마다 부르는 `allowElement` 의 횟수가 깊이와 맞아야 한다(입력이 정말 그만큼 겹쳤다는 표지).
// - sweep: 그린 뒤의 상태가 raw(원문), markdown(시제품) 가운데 하나이거나, 제한 시간·크래시·페이지 오류 가운데 하나가
//   있어야 한다. markdown 이고 페이지가 살아 있는 깊이 입력은 DOM 의 요소 수가 깊이와 같아야 한다.
// - crash: 좁히기의 두 끝(죽지 않는 깊이, 죽는 깊이)을 먼저 확인한다. 죽은 회차는 Playwright 의 crash 이벤트가 있어야 한다.
// - guard: 한도 이하의 입력은 마크다운으로 그려지고, 넘는 입력은 원문이 보이며 받은 오류의 이름이 가드의 것
//   (`AnswerTooDeepError`)이거나 그보다 먼저 난 `RangeError` 여야 한다.
// - fine: 깊이 1 은 넘치지 않고 깊이 40 은 넘쳐야 한다. 깊이마다 DOM 의 요소 수가 깊이와 같아야 한다.
// - heights: `<br>` 갈래의 높이가 변환 없는 갈래보다 한 줄 바꿈 수만큼 커야 한다(줄바꿈이 실제로 그려졌다는 표지).
// 하나라도 어긋나면 notMeasured 에 적고 종료 코드 1.
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { chromium } from "playwright";
import {
  bundle,
  chromiumPath,
  framesOf,
  openPage,
  pageHtml,
  PLAYWRIGHT_VERSION,
  ROOT,
  settle,
  stageOfPackage,
  stageOfThrow,
} from "./browser-kit.mjs";
import { DEPTH_ELEMENT, DEPTH_KINDS, DEPTHS, inputOf, STRESS_NAMES } from "./inputs.mjs";

const OUT = join(ROOT, "out", "browser");
const PARTS = ["capture", "stages", "threshold", "sweep", "crash", "guard", "fine", "heights"];
const only = process.argv.slice(2).find((arg) => arg.startsWith("--only="))?.slice("--only=".length) ?? null;
const asked = process.argv.slice(2).filter((arg) => !arg.startsWith("--only="));
const unknown = asked.filter((part) => !PARTS.includes(part));
if (unknown.length > 0) {
  console.error(`없는 부분이다: ${unknown.join(", ")}. 고를 수 있는 것: ${PARTS.join(", ")}`);
  process.exit(2);
}
const parts = asked.length === 0 ? PARTS : asked;

const TARGETS = [
  { name: "chromium", options: { channel: "chromium" } },
  { name: "headless-shell", options: {} },
];
const PRIMARY = TARGETS[0];
const launch = (target) => chromium.launch(target.options);

const DEPTH_NAMES = [
  ...DEPTHS.map((depth) => `quote:${depth}`),
  ...DEPTHS.map((depth) => `list-inline:${depth}`),
  // 들여 쓴 목록은 글의 크기가 깊이의 제곱으로 는다(깊이 2,000 은 4MB, 3,000 은 9MB). 1,000 까지만 잰다.
  ...DEPTHS.filter((depth) => depth <= 1_000).map((depth) => `list-indent:${depth}`),
];
const ALL_NAMES = [...DEPTH_NAMES, ...STRESS_NAMES.map((name) => `stress:${name}`)].filter(
  (name) => only === null || name.includes(only),
);
const COMBINED = { plugins: "combined", tableBox: "region", codeBlock: "focusable" };

const notMeasured = [];
const round1 = (value) => Math.round(value * 10) / 10;

/** `quote:3000` 꼴 이름에서 깊이 입력이면 { kind, element, depth } 를 낸다. */
function depthOf(name) {
  const [kind, rest] = name.split(":");
  const element = DEPTH_ELEMENT[kind];
  return element === undefined ? null : { kind, element, depth: Number(rest) };
}

/** 페이지 안에서 도는 함수. 프레임 둘을 기다린 뒤(그려졌다는 표지) 칸과 문서의 치수를 잰다. */
async function measureInPage() {
  await new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  });
  const host = document.getElementById("host");
  const all = host.querySelectorAll("*");
  let deepest = null;
  let maxDepth = 0;
  let maxRight = 0;
  for (const element of all) {
    let depth = 0;
    for (let up = element; up !== host && up !== null; up = up.parentElement) depth += 1;
    if (depth > maxDepth) {
      maxDepth = depth;
      deepest = element;
    }
    if (!element.classList.contains("sr-only")) maxRight = Math.max(maxRight, element.getBoundingClientRect().right);
  }
  const rect = deepest === null ? null : deepest.getBoundingClientRect();
  return {
    innerWidth: window.innerWidth,
    docScrollWidth: document.documentElement.scrollWidth,
    docScrollHeight: document.documentElement.scrollHeight,
    hostWidth: host.clientWidth,
    elements: all.length,
    maxDepth,
    maxRight: Math.round(maxRight),
    deepest:
      deepest === null
        ? null
        : { tag: deepest.tagName.toLowerCase(), left: Math.round(rect.left), width: Math.round(rect.width), height: Math.round(rect.height) },
    counts: {
      blockquote: host.querySelectorAll("blockquote").length,
      ul: host.querySelectorAll("ul").length,
    },
  };
}

/** 페이지 안에서 도는 함수. 콘솔과 페이지 오류가 올 틈을 주고 칸에 보이는 글의 앞머리를 낸다. */
async function shownInPage() {
  await new Promise((resolve) => {
    setTimeout(resolve, 150);
  });
  return document.getElementById("host").textContent.slice(0, 24);
}

function thrownSummary(thrown, made) {
  if (thrown === null || thrown === undefined) return null;
  const frames = framesOf(thrown.stack, made);
  return { name: thrown.name, message: thrown.message, frames: frames.slice(0, 5) };
}

function drawnSummary(settled, made) {
  if (settled.value === undefined) return settled;
  const drawn = settled.value;
  return {
    state: drawn.state,
    rawEqualsText: drawn.rawEqualsText,
    ms: round1(drawn.ms),
    flushThrown: thrownSummary(drawn.flushThrown, made),
    failures: drawn.failures.map((thrown) => thrownSummary(thrown, made)),
    rootErrors: drawn.rootErrors.map((entry) => ({ kind: entry.kind, ...thrownSummary(entry.thrown, made) })),
  };
}

const copyEvents = (events) => ({
  console: events.console.map((entry) => ({ type: entry.type, text: entry.text.split("\n")[0] })),
  pageErrors: [...events.pageErrors],
  crashed: events.crashed,
});

// ───────────────────────── capture ─────────────────────────

const NORMAL_1 = "첫 **답**입니다.\n\n- 하나\n- 둘";
const NORMAL_2 = "둘째 *답*입니다.";
const BAD_1 = `${">".repeat(3_000)} a`;
const BAD_2 = `${">".repeat(3_001)} b`;
const CAPTURE_STEPS = [
  { step: "보통 글 1", text: NORMAL_1, bad: false },
  { step: "`>` 3,000개", text: BAD_1, bad: true },
  { step: "보통 글 2", text: NORMAL_2, bad: false },
  { step: "`>` 3,000개 다시", text: BAD_1, bad: true },
  { step: "`>` 3,001개", text: BAD_2, bad: true },
  { step: "보통 글 1 다시", text: NORMAL_1, bad: false },
];
const CAPTURE_BRANCHES = [
  { mode: "view", handlers: "default" },
  { mode: "view", handlers: "recorded" },
  { mode: "direct", handlers: "default" },
  { mode: "guarded", handlers: "default" },
  { mode: "guarded", handlers: "recorded" },
  { mode: "guarded-no-reset", handlers: "default" },
];

async function captureBranch(target, branch, made) {
  const browser = await launch(target);
  const row = { browser: target.name, ...branch, steps: [] };
  try {
    const { page, events } = await openPage(browser, pageHtml(), made.outfile);
    let seenConsole = 0;
    let seenPageErrors = 0;
    let seenFailures = 0;
    let seenRootErrors = 0;
    for (const [index, step] of CAPTURE_STEPS.entries()) {
      const call =
        index === 0
          ? page.evaluate(([config, text]) => MdProbe.mount(config, text), [{ ...COMBINED, ...branch }, step.text])
          : page.evaluate((text) => MdProbe.update(text), step.text);
      const settled = await settle(call, 60_000);
      // 콘솔과 페이지 오류는 늦게 온다. 뒤따르는 호출 하나를 기다린 뒤에 센다.
      const shown = await settle(page.evaluate(shownInPage), 30_000);
      const drawn = drawnSummary(settled, made);
      row.steps.push({
        step: step.step,
        bad: step.bad,
        state: drawn.state ?? null,
        rawEqualsText: drawn.rawEqualsText ?? null,
        problem: settled.value === undefined ? settled : null,
        flushThrown: drawn.flushThrown ?? null,
        newFailures: (drawn.failures ?? []).slice(seenFailures),
        newRootErrors: (drawn.rootErrors ?? []).slice(seenRootErrors),
        newConsole: events.console.slice(seenConsole).map((entry) => ({ type: entry.type, text: entry.text.split("\n")[0] })),
        newPageErrors: events.pageErrors.slice(seenPageErrors),
        shownText: shown.value ?? null,
        responsive: shown.value !== undefined,
      });
      seenFailures = (drawn.failures ?? []).length;
      seenRootErrors = (drawn.rootErrors ?? []).length;
      seenConsole = events.console.length;
      seenPageErrors = events.pageErrors.length;
    }
    row.crashed = events.crashed;
  } finally {
    await settle(browser.close(), 15_000);
  }
  return row;
}

async function runCapture(made) {
  const rows = [];
  for (const target of TARGETS) {
    for (const branch of CAPTURE_BRANCHES) rows.push(await captureBranch(target, branch, made));
    // 받지 않는 대조에서 실패가 실제로 났나. 났어야 받는 갈래를 견준 것이다.
    const control = rows.find((row) => row.browser === target.name && row.mode === "view" && row.handlers === "default");
    const controlBad = control.steps[1];
    const failed = controlBad.state !== "markdown" && (controlBad.newPageErrors.length > 0 || controlBad.flushThrown !== null);
    if (!failed) {
      notMeasured.push({ part: "capture", browser: target.name, reason: "받지 않는 대조에서 `>` 3,000개가 실패하지 않았다", step: controlBad });
    }
  }
  for (const row of rows) {
    const branch = `${row.browser}/${row.mode}/${row.handlers}`;
    if (row.steps[0].state !== "markdown") {
      notMeasured.push({ part: "capture", branch, reason: "보통 글이 마크다운으로 그려지지 않았다" });
    }
    // 단계마다 호출이 끝나 상태를 돌려줬나. 못 돌려줬는데 크래시 이벤트도 없으면 그 단계는 본 것이 아니다.
    for (const step of row.steps) {
      if (step.problem !== null && !row.crashed) {
        notMeasured.push({ part: "capture", branch, step: step.step, reason: "단계의 호출이 상태를 돌려주지 않았고 크래시 이벤트도 없다", problem: step.problem });
      }
    }
  }
  return rows;
}

// ───────────────────────── stages ─────────────────────────

function parseLastLine(run) {
  try {
    return JSON.parse((run.stdout ?? "").trim().split(/\r?\n/).pop() ?? "");
  } catch {
    return null;
  }
}

function nodeStages(name, nodeBundle) {
  const run = spawnSync(process.execPath, [join(ROOT, "probe", "stage-child.mjs"), nodeBundle.outfile, "stages", name], {
    encoding: "utf8",
    timeout: 120_000,
    maxBuffer: 256 * 1024 * 1024,
  });
  if (run.error !== undefined && run.error.code === "ETIMEDOUT") {
    // 제한 시간은 어느 단계에서 멈췄는지 알리는 표지가 없다. 결과 줄에는 "제한 시간"으로 적고 측정으로는 세지 않는다.
    notMeasured.push({ part: "stages", env: "node", name, reason: "제한 시간 안에 끝나지 않았다", timeoutMs: 120_000 });
    return { env: "node", name, timedOut: true };
  }
  const parsed = parseLastLine(run);
  if (parsed === null || parsed.ok !== true) {
    notMeasured.push({ part: "stages", env: "node", name, status: run.status, stderr: (run.stderr ?? "").slice(0, 300) });
    return { env: "node", name, broken: true };
  }
  return stageRow("node", name, parsed, parsed.render, parsed.render?.counts ?? null, nodeBundle);
}

function stageRow(env, name, result, render, counts, made) {
  const row = { env, name, reached: result.reached, filterCalls: result.filterCalls, markdownMs: round1(result.markdownMs) };
  if (result.thrown !== null) {
    const frames = framesOf(result.thrown.stack, made);
    const verdict = stageOfThrow(result.reached, frames);
    row.threw = { name: result.thrown.name, stage: verdict.stage, byMarker: verdict.byMarker, helperOnly: verdict.helperOnly, frames: frames.slice(0, 4) };
    if (!verdict.agree) notMeasured.push({ part: "stages", env, name, reason: "표지와 스택이 가리키는 단계가 다르다", verdict, frames: frames.slice(0, 6) });
    return row;
  }
  // `Markdown` 은 지났다. React 의 렌더가 던졌나.
  const renderThrown = render?.thrown ?? render?.flushThrown ?? render?.rootErrors?.[0]?.thrown ?? null;
  if (renderThrown !== null) {
    const frames = framesOf(renderThrown.stack, made);
    const stage = frames[0] === undefined ? null : stageOfPackage(frames[0].pkg);
    row.threw = { name: renderThrown.name, stage, byMarker: ["React의 렌더"], frames: frames.slice(0, 4) };
    row.renderErrorKinds = render?.rootErrors?.map((entry) => entry.kind) ?? null;
    if (stage !== "React의 렌더") notMeasured.push({ part: "stages", env, name, reason: "렌더가 던졌는데 스택이 React 의 것이 아니다", frames: frames.slice(0, 6) });
    return row;
  }
  row.threw = null;
  row.renderMs = render === null || render === undefined ? null : round1(render.ms);
  const expected = depthOf(name);
  if (expected !== null) {
    // 입력이 정말 그 깊이까지 겹쳤다는 표지는 거르기가 요소마다 부르는 `allowElement` 의 횟수다(인용은 겹마다 하나와
    // 문단 하나, 목록은 겹마다 목록과 항목 둘). 그린 결과의 요소 수는 표지로 쓰지 않고 결과로 적는다. 첫 판은 그린
    // 결과로 셌는데, Node 의 서버 렌더가 깊이 500 에서 겹 열넷을 말없이 빠뜨려 표지가 될 수 없었다.
    const wantCalls = expected.kind === "quote" ? expected.depth + 1 : 2 * expected.depth;
    if (result.filterCalls !== wantCalls) {
      notMeasured.push({ part: "stages", env, name, reason: `거르기 호출 수가 깊이와 맞지 않는다(기대 ${wantCalls})`, filterCalls: result.filterCalls });
    }
    row.renderedDepth = counts === null ? null : counts[expected.element];
    row.renderedAll = counts === null ? null : counts[expected.element] === expected.depth;
  }
  return row;
}

async function browserStages(target, name, made) {
  const text = inputOf(name);
  const browser = await launch(target);
  try {
    const { page, events } = await openPage(browser, pageHtml(), made.outfile);
    const settled = await settle(page.evaluate((value) => MdProbe.stages(value), text), 120_000);
    if (settled.value === undefined) {
      // 크래시 이벤트가 있으면 죽은 것이 결과다. 이벤트 없이 제한 시간만 지났으면 무엇이 일어났는지 모르는 회차다.
      if (settled.timedOut === true && !events.crashed) {
        notMeasured.push({ part: "stages", env: target.name, name, reason: "제한 시간이 지났는데 크래시 이벤트가 없다", problem: settled });
      }
      if (settled.timedOut === true || events.crashed) return { env: target.name, name, ...settled, crashed: events.crashed };
      notMeasured.push({ part: "stages", env: target.name, name, problem: settled });
      return { env: target.name, name, broken: true };
    }
    // 그린 뒤에 치수를 잰다. 여기서 렌더러가 죽으면 그것도 결과다(crashedAfterRender).
    const after = settled.value.thrown === null ? await settle(page.evaluate(measureInPage), 60_000) : { value: null };
    const row = stageRow(target.name, name, settled.value, settled.value.render, after.value?.counts ?? null, made);
    row.crashedAfterRender = events.crashed;
    if (after.value === undefined && !events.crashed) row.measureProblem = after;
    row.pageErrors = [...events.pageErrors];
    return row;
  } finally {
    await settle(browser.close(), 15_000);
  }
}

// 과제의 입력(`>` 3,000개)은 던지는 단계가 회차마다 갈릴 수 있어(스택이 넘치는 자리는 JIT 상태를 탄다) 여러 번 본다.
const REPEAT_NAME = "quote:3000";
const REPEATS = 10;

async function runStages(made, nodeBundle) {
  const rows = [];
  for (const name of ALL_NAMES) {
    rows.push(nodeStages(name, nodeBundle));
    for (const target of TARGETS) rows.push(await browserStages(target, name, made));
  }
  const repeats = {};
  if (only === null) {
    const tally = (list) => {
      const counts = {};
      for (const row of list) {
        const key = row.threw === undefined ? "측정 아님" : row.threw === null ? "던지지 않는다" : row.threw.stage;
        counts[key] = (counts[key] ?? 0) + 1;
      }
      return counts;
    };
    const node = [];
    for (let i = 0; i < REPEATS; i += 1) node.push(nodeStages(REPEAT_NAME, nodeBundle));
    repeats.node = tally(node);
    for (const target of TARGETS) {
      const list = [];
      for (let i = 0; i < REPEATS; i += 1) list.push(await browserStages(target, REPEAT_NAME, made));
      repeats[target.name] = tally(list);
    }
  }
  return { rows, repeats: { name: REPEAT_NAME, rounds: REPEATS, byEnv: repeats } };
}

// ───────────────────────── threshold ─────────────────────────

const THRESHOLD_KINDS = ["quote", "list-inline"];
const THRESHOLD_LO = 50;
const THRESHOLD_HI = 3_000;
const THRESHOLD_REPEATS = 3;

function nodeThreshold(kind, nodeBundle) {
  const run = spawnSync(
    process.execPath,
    [join(ROOT, "probe", "stage-child.mjs"), nodeBundle.outfile, "threshold", kind, String(THRESHOLD_LO), String(THRESHOLD_HI)],
    { encoding: "utf8", timeout: 300_000, maxBuffer: 64 * 1024 * 1024 },
  );
  const parsed = parseLastLine(run);
  if (parsed === null || parsed.ok !== true) {
    notMeasured.push({ part: "threshold", env: "node", kind, status: run.status, stderr: (run.stderr ?? "").slice(0, 300) });
    return null;
  }
  return parsed;
}

async function browserThreshold(target, kind, made) {
  const make = DEPTH_KINDS[kind];
  const browser = await launch(target);
  try {
    const { page } = await openPage(browser, pageHtml(), made.outfile);
    const throws = async (depth) => {
      const settled = await settle(page.evaluate((value) => MdProbe.markdownThrows(value), make(depth)), 120_000);
      if (settled.value === undefined) throw new Error(`깊이 ${depth} 에서 답이 없다: ${JSON.stringify(settled)}`);
      return settled.value;
    };
    const loThrows = await throws(THRESHOLD_LO);
    const hiThrows = await throws(THRESHOLD_HI);
    if (loThrows || !hiThrows) return { ok: true, kind, bracketed: false, lo: THRESHOLD_LO, hi: THRESHOLD_HI, loThrows, hiThrows };
    let pass = THRESHOLD_LO;
    let fail = THRESHOLD_HI;
    let checks = 2;
    while (fail - pass > 1) {
      const mid = Math.floor((pass + fail) / 2);
      if (await throws(mid)) fail = mid;
      else pass = mid;
      checks += 1;
    }
    const again = { lastPassThrows: await throws(pass), firstThrowThrows: await throws(fail) };
    return { ok: true, kind, bracketed: true, lastPass: pass, firstThrow: fail, checks, again };
  } catch (error) {
    notMeasured.push({ part: "threshold", env: target.name, kind, reason: String(error).slice(0, 300) });
    return null;
  } finally {
    await settle(browser.close(), 15_000);
  }
}

async function runThreshold(made, nodeBundle) {
  const result = { kinds: {}, edge: [] };
  for (const kind of THRESHOLD_KINDS) {
    const entry = { node: [] };
    for (let i = 0; i < THRESHOLD_REPEATS; i += 1) entry.node.push(nodeThreshold(kind, nodeBundle));
    for (const target of TARGETS) {
      entry[target.name] = [];
      for (let i = 0; i < THRESHOLD_REPEATS; i += 1) entry[target.name].push(await browserThreshold(target, kind, made));
    }
    result.kinds[kind] = entry;
    // 던지지 않는 가장 깊은 깊이 언저리에서 시제품을 실제로 그려 본다. `Markdown` 은 지나는데 React 의 렌더나 브라우저의
    // 배치가 못 버티는 깊이가 있는지 보려는 것이다. 좁힌 값은 회차마다 조금 움직여, 세 깊이를 본다.
    for (const target of TARGETS) {
      const passes = entry[target.name].filter((item) => item !== null && item.bracketed).map((item) => item.lastPass);
      if (passes.length === 0) continue;
      const edge = Math.min(...passes);
      for (const depth of [edge, edge - 20, edge - 100]) {
        if (depth <= 0) continue;
        for (const mode of ["direct", "guarded"]) {
          result.edge.push(await sweepRound(target, `${kind}:${depth}`, mode, made, { thenNormal: true }));
        }
      }
    }
  }
  return result;
}

// ───────────────────────── sweep ─────────────────────────

async function sweepRound(target, name, mode, made, { thenNormal = false, plugins = "combined" } = {}) {
  const text = inputOf(name);
  const browser = await launch(target);
  const row = { browser: target.name, name, mode, inputChars: text.length };
  let live = null;
  try {
    const { page, events } = await openPage(browser, pageHtml(), made.outfile);
    live = events;
    const mounted = await settle(
      page.evaluate(([config, value]) => MdProbe.mount(config, value), [{ ...COMBINED, plugins, mode, handlers: "default" }, text]),
      60_000,
    );
    row.mount = drawnSummary(mounted, made);
    const started = Date.now();
    const after = await settle(page.evaluate(measureInPage), 30_000);
    row.afterMs = Date.now() - started;
    row.after = after.value ?? after;
    row.responsive = after.value !== undefined;
    const shot = await settle(page.screenshot({ type: "png" }), 30_000);
    row.screenshotBytes = shot.value === undefined ? shot : shot.value.length;
    if (thenNormal) {
      // 깊게 그린 자리에 보통 글을 다시 그린다(깊은 나무를 지우는 길).
      const next = await settle(page.evaluate((value) => MdProbe.update(value), NORMAL_2), 60_000);
      const shown = await settle(page.evaluate(shownInPage), 30_000);
      row.thenNormal = { ...drawnSummary(next, made), shownText: shown.value ?? shown };
    }
  } finally {
    await settle(browser.close(), 15_000);
    row.events = live === null ? null : copyEvents(live);
  }
  const state = row.mount.state ?? null;
  const explained =
    state === "raw" || state === "markdown" || row.mount.timedOut === true || row.events?.crashed === true || (row.events?.pageErrors.length ?? 0) > 0;
  if (!explained) notMeasured.push({ part: "sweep", browser: target.name, name, mode, reason: "그린 뒤의 상태를 알 수 없다", mount: row.mount });
  const expected = depthOf(name);
  if (state === "markdown" && expected !== null && row.responsive && row.after.counts[expected.element] !== expected.depth) {
    notMeasured.push({ part: "sweep", browser: target.name, name, mode, reason: `DOM 의 ${expected.element} 수가 깊이와 다르다`, counts: row.after.counts });
  }
  row.verdict = {
    threw: (row.mount.failures?.length ?? 0) > 0 || (row.events?.pageErrors.length ?? 0) > 0 || (row.mount.flushThrown ?? null) !== null,
    fellBackToRaw: state === "raw" && row.mount.rawEqualsText === true,
    ms: row.mount.ms ?? null,
    responsive: row.responsive,
    overflow: row.responsive ? row.after.docScrollWidth > row.after.innerWidth : null,
    crashed: row.events?.crashed ?? null,
  };
  return row;
}

async function runSweep(made) {
  const rows = [];
  for (const target of TARGETS) {
    for (const name of ALL_NAMES) {
      for (const mode of ["direct", "guarded"]) rows.push(await sweepRound(target, name, mode, made));
    }
  }
  return rows;
}

// ───────────────────────── crash ─────────────────────────

// 짓는 법. prototype 은 시제품(직접 부르기)으로 겹친 인용을 그린다. dom-div 는 CSS 가 없는 빈 페이지에 div 를 손으로
// 겹쳐 짓는다(시제품도 React 도 디자인의 CSS 도 없다). 둘이 비슷한 깊이에서 죽으면 죽는 까닭은 브라우저의 배치다.
const CRASH_BUILDS = ["prototype", "dom-div"];
const CRASH_LADDER = [50, 100, 200, 500, 1_000, 1_500, 2_000, 3_000, 5_000, 10_000, 20_000];
const BARE_PAGE = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>빈 페이지</title></head><body><div id="host"></div></body></html>';

/** 깊이 하나를 짓고 배치와 프레임을 일으킨 뒤 렌더러가 살아 있는지 본다. */
async function crashCheck(target, build, depth, made) {
  const browser = await launch(target);
  try {
    const { page, events } = await openPage(browser, build === "prototype" ? pageHtml() : BARE_PAGE, made.outfile);
    const built =
      build === "prototype"
        ? await settle(
            page.evaluate(([config, value]) => MdProbe.mount(config, value).state, [
              { ...COMBINED, mode: "direct", handlers: "default" },
              DEPTH_KINDS.quote(depth),
            ]),
            60_000,
          )
        : await settle(
            page.evaluate((levels) => {
              let inner = document.createElement("p");
              inner.textContent = "a";
              for (let i = 0; i < levels; i += 1) {
                const box = document.createElement("div");
                box.append(inner);
                inner = box;
              }
              document.getElementById("host").append(inner);
              return "dom";
            }, depth),
            60_000,
          );
    const layout = await settle(page.evaluate(() => document.documentElement.scrollWidth), 30_000);
    const frame = await settle(
      page.evaluate(
        () =>
          new Promise((resolve) => {
            requestAnimationFrame(() => requestAnimationFrame(() => resolve("frame")));
          }),
      ),
      30_000,
    );
    const alive = await settle(
      page.evaluate(() => 1 + 1),
      10_000,
    );
    const diedAt = built.value === undefined ? "짓기" : layout.value === undefined ? "배치" : frame.value === undefined ? "프레임" : alive.value === undefined ? "그 뒤" : null;
    return { depth, built: built.value ?? built, crashed: events.crashed, diedAt, timedOut: [built, layout, frame, alive].some((step) => step.timedOut === true) };
  } finally {
    await settle(browser.close(), 15_000);
  }
}

async function findCrashDepth(target, build, made) {
  const checks = [];
  let lastAlive = null;
  let firstDead = null;
  for (const depth of CRASH_LADDER) {
    const check = await crashCheck(target, build, depth, made);
    checks.push(check);
    // 시제품은 `Markdown` 이 던지는 깊이부터 원문만 보인다. 거기서부터는 겹친 DOM 이 없어 사다리를 멈춘다.
    if (build === "prototype" && check.built === "raw") break;
    if (check.diedAt === null) {
      lastAlive = depth;
      continue;
    }
    if (!check.crashed) {
      notMeasured.push({ part: "crash", browser: target.name, build, depth, reason: "답이 없는데 crash 이벤트가 없다", check });
      return { build, checks, lastAlive, firstDead: null };
    }
    firstDead = depth;
    break;
  }
  if (firstDead === null) return { build, checks, lastAlive, firstDead: null };
  if (lastAlive === null) {
    notMeasured.push({ part: "crash", browser: target.name, build, reason: "사다리의 첫 깊이에서 이미 죽었다" });
    return { build, checks, lastAlive, firstDead };
  }
  while (firstDead - lastAlive > 1) {
    const mid = Math.floor((lastAlive + firstDead) / 2);
    const check = await crashCheck(target, build, mid, made);
    checks.push(check);
    if (check.diedAt === null) lastAlive = mid;
    else if (check.crashed) firstDead = mid;
    else {
      notMeasured.push({ part: "crash", browser: target.name, build, depth: mid, reason: "답이 없는데 crash 이벤트가 없다", check });
      break;
    }
  }
  // 두 끝을 한 번씩 더 본다(죽는 깊이가 회차마다 움직이는지).
  const again = { lastAlive: await crashCheck(target, build, lastAlive, made), firstDead: await crashCheck(target, build, firstDead, made) };
  // 다시 본 회차도 처음과 같은 판정이다. 답이 없는데 크래시 이벤트가 없으면 죽은 것으로 적지 않고 측정 아님으로 센다.
  for (const [end, depth] of [["lastAlive", lastAlive], ["firstDead", firstDead]]) {
    const check = again[end];
    if (check.diedAt !== null && !check.crashed) {
      notMeasured.push({ part: "crash", browser: target.name, build, depth, reason: "다시 본 회차에서 답이 없는데 crash 이벤트가 없다", end, check });
    }
  }
  return {
    build,
    checks,
    lastAlive,
    firstDead,
    again: { lastAliveDied: again.lastAlive.diedAt, firstDeadDied: again.firstDead.diedAt, lastAliveCrashed: again.lastAlive.crashed, firstDeadCrashed: again.firstDead.crashed },
  };
}

async function runCrash(made) {
  const result = {};
  for (const target of TARGETS) {
    result[target.name] = [];
    for (const build of CRASH_BUILDS) result[target.name].push(await findCrashDepth(target, build, made));
  }
  return result;
}

// ───────────────────────── guard ─────────────────────────

/**
 * 깊이 가드를 켠 갈래(인용과 목록이 한도를 넘게 겹치면 그리지 않고 던진다)로 같은 깊이 입력을 그린다. 한도 바로 아래와
 * 바로 위도 본다. 표지: 한도 이하는 마크다운으로 그려지고, 넘는 것은 원문이 보이며 그 까닭이 가드의 오류
 * (`AnswerTooDeepError`)거나 그보다 먼저 파싱에서 난 `RangeError` 다. 넘는데 마크다운으로 그려지면 가드가 돌지 않은 것이다.
 */
async function runGuard(made, guardDepth) {
  const names = [
    `quote:${guardDepth}`,
    `quote:${guardDepth + 1}`,
    `list-inline:${guardDepth}`,
    `list-inline:${guardDepth + 1}`,
    ...DEPTH_NAMES,
  ].filter((name) => only === null || name.includes(only));
  const rows = [];
  for (const target of TARGETS) {
    for (const name of names) {
      const row = await sweepRound(target, name, "direct", made, { plugins: "combined-guard" });
      const depth = depthOf(name).depth;
      const failure = row.mount.failures?.[0]?.name ?? null;
      row.guard = { limit: guardDepth, depth, shouldDraw: depth <= guardDepth, failure };
      const state = row.mount.state ?? null;
      const asExpected = depth <= guardDepth ? state === "markdown" : state === "raw" && (failure === "AnswerTooDeepError" || failure === "RangeError");
      if (!asExpected) notMeasured.push({ part: "guard", browser: target.name, name, reason: "가드의 기대와 다르다", state, failure });
      rows.push(row);
    }
  }
  return rows;
}

// ───────────────────────── fine ─────────────────────────

const FINE_MAX = 40;

async function runFine(made) {
  const result = {};
  const browser = await launch(PRIMARY);
  try {
    for (const kind of Object.keys(DEPTH_KINDS)) {
      const { page, context } = await openPage(browser, pageHtml(), made.outfile);
      const rows = [];
      for (let depth = 1; depth <= FINE_MAX; depth += 1) {
        const text = DEPTH_KINDS[kind](depth);
        const call =
          depth === 1
            ? page.evaluate(([config, value]) => MdProbe.mount(config, value), [{ ...COMBINED, mode: "direct", handlers: "default" }, text])
            : page.evaluate((value) => MdProbe.update(value), text);
        const drawn = await settle(call, 30_000);
        const after = await settle(page.evaluate(measureInPage), 30_000);
        if (drawn.value === undefined || after.value === undefined || drawn.value.state !== "markdown") {
          notMeasured.push({ part: "fine", kind, depth, drawn: drawn.value?.state ?? drawn, after: after.value === undefined ? after : "ok" });
          continue;
        }
        if (after.value.counts[DEPTH_ELEMENT[kind]] !== depth) {
          notMeasured.push({ part: "fine", kind, depth, reason: "요소 수가 깊이와 다르다", counts: after.value.counts });
          continue;
        }
        rows.push({
          depth,
          docScrollWidth: after.value.docScrollWidth,
          innerWidth: after.value.innerWidth,
          maxRight: after.value.maxRight,
          deepest: after.value.deepest,
          height: after.value.docScrollHeight,
        });
      }
      await context.close();
      const overflow = rows.find((row) => row.docScrollWidth > row.innerWidth);
      // 가장 안쪽 요소의 폭이 본문 글자 하나(15px)보다 좁아지는 첫 깊이. 그 뒤로는 글자가 한 자씩 꺾이거나 칸 밖으로 나간다.
      const narrow = rows.find((row) => row.deepest !== null && row.deepest.width < 15);
      const offscreen = rows.find((row) => row.deepest !== null && row.deepest.left >= row.innerWidth);
      result[kind] = {
        browser: PRIMARY.name,
        measuredDepths: rows.length,
        widthAtDepth1: rows[0]?.deepest?.width ?? null,
        firstNarrowerThanOneChar: narrow?.depth ?? null,
        firstDocumentOverflow: overflow?.depth ?? null,
        firstOffscreen: offscreen?.depth ?? null,
        rows,
      };
      // 대조: 깊이 1 은 넘치지 않고 깊이 40 은 넘쳐야 "넘치기 시작하는 깊이"가 그 사이에 있다.
      if (rows.length > 0 && (rows[0].docScrollWidth > rows[0].innerWidth || overflow === undefined)) {
        notMeasured.push({ part: "fine", kind, reason: "깊이 1 이 이미 넘치거나 깊이 40 까지 넘치지 않았다" });
      }
    }
  } finally {
    await settle(browser.close(), 15_000);
  }
  return result;
}

// ───────────────────────── heights ─────────────────────────

// 갈래. `none` 은 변환도 CSS 도 없는 지금의 파서 그대로, `br` 은 직접 짠 변환(한 줄 바꿈을 <br> 로)이고 나머지는 변환 없이
// CSS 만 더한 것이다.
const LEAVES = "p,h1,h2,h3,h4,h5,h6,th,td";
const HEIGHT_VARIANTS = [
  { name: "none", plugins: "base", css: "" },
  { name: "br", plugins: "breaks", css: "" },
  { name: "css-container-pre-line", plugins: "base", css: ".md{white-space:pre-line}" },
  { name: "css-container-pre-wrap", plugins: "base", css: ".md{white-space:pre-wrap}" },
  { name: "css-leaf-pre-line", plugins: "base", css: `.md :is(${LEAVES}){white-space:pre-line}` },
  { name: "css-leaf-li-pre-line", plugins: "base", css: `.md :is(${LEAVES},li){white-space:pre-line}` },
];
// 기대는 결과를 보기 전에 적었다(2026-11-11). `br` 갈래의 높이와 견준 것이다: same 같다, more 더 높다(빈 줄이 생긴다),
// less 더 낮다(줄바꿈이 보이지 않는다). 순서는 css-container-pre-line, css-container-pre-wrap, css-leaf-pre-line,
// css-leaf-li-pre-line 이다. 근거는 mdast-util-to-hast 가 블록 사이에 "\n" 글자 노드를 두고(목록·인용·항목 안쪽 포함)
// hast-util-to-jsx-runtime 이 표 안의 것만 지운다는 것, 그리고 줄 끝 글자를 지키는 white-space 아래에서는 그 글자 노드가
// 빈 줄 하나가 된다는 추론이다. `softBreaks` 는 코드 밖의 한 줄 바꿈 수다.
const HEIGHT_CASES = [
  { id: "h01-two-paragraphs", text: "가\n\n나", softBreaks: 0, expect: ["more", "more", "same", "same"] },
  { id: "h02-soft-break", text: "가\n나", softBreaks: 1, expect: ["same", "same", "same", "same"] },
  { id: "h03-two-soft-breaks", text: "가\n나\n다", softBreaks: 2, expect: ["same", "same", "same", "same"] },
  { id: "h04-tight-list", text: "- 가\n- 나", softBreaks: 0, expect: ["more", "more", "same", "same"] },
  { id: "h05-tight-list-soft-break", text: "- 가\n  나\n- 다", softBreaks: 1, expect: ["more", "more", "less", "same"] },
  { id: "h06-nested-list", text: "- 가\n  - 나\n  - 다\n- 라", softBreaks: 0, expect: ["more", "more", "same", "more"] },
  { id: "h07-loose-list", text: "- 가\n\n- 나", softBreaks: 0, expect: ["more", "more", "same", "more"] },
  { id: "h08-quote-soft-break", text: "> 가\n> 나", softBreaks: 1, expect: ["more", "more", "same", "same"] },
  { id: "h09-heading-paragraph", text: "## 가\n\n나", softBreaks: 0, expect: ["more", "more", "same", "same"] },
  { id: "h10-table", text: "| 가 | 나 |\n|---|---|\n| 다 | 라 |", softBreaks: 0, expect: ["same", "same", "same", "same"] },
  { id: "h11-table-paragraph", text: "| 가 | 나 |\n|---|---|\n| 다 | 라 |\n\n마", softBreaks: 0, expect: ["more", "more", "same", "same"] },
  { id: "h12-code-block", text: "```\n가\n나\n```", softBreaks: 0, expect: ["same", "same", "same", "same"] },
  { id: "h13-paragraph-list-paragraph", text: "가\n\n- 나\n- 다\n\n라", softBreaks: 0, expect: ["more", "more", "same", "same"] },
  { id: "h14-hard-break", text: "가  \n나", softBreaks: 0, expect: ["more", "more", "more", "more"] },
  { id: "h15-ordered-soft-break-nested", text: "1. 가\n   나\n   - 다", softBreaks: 1, expect: ["more", "more", "less", "more"] },
];

async function runHeights(made) {
  const rows = [];
  const browser = await launch(PRIMARY);
  try {
    for (const item of HEIGHT_CASES) {
      const heights = {};
      for (const variant of HEIGHT_VARIANTS) {
        const { page, context } = await openPage(browser, pageHtml({ extraCss: variant.css }), made.outfile);
        const drawn = await settle(
          page.evaluate(([config, value]) => MdProbe.mount(config, value), [
            { mode: "view", plugins: variant.plugins, tableBox: "region", codeBlock: "focusable", handlers: "default" },
            item.text,
          ]),
          30_000,
        );
        const measured = await settle(
          page.evaluate(() => {
            const md = document.querySelector('#host [data-answer="markdown"]');
            if (md === null) return null;
            return { height: md.getBoundingClientRect().height, br: md.querySelectorAll("br").length };
          }),
          30_000,
        );
        await context.close();
        if (drawn.value?.state !== "markdown" || measured.value === undefined || measured.value === null) {
          notMeasured.push({ part: "heights", id: item.id, variant: variant.name, drawn: drawn.value?.state ?? drawn });
          continue;
        }
        heights[variant.name] = measured.value;
      }
      if (Object.keys(heights).length !== HEIGHT_VARIANTS.length) continue;
      const base = heights.none.height;
      const br = heights.br.height;
      // 표지: `<br>` 갈래가 한 줄 바꿈 수만큼(본문 줄 높이 22px 씩) 높아야 줄바꿈이 실제로 그려진 것이다.
      if (br - base !== 22 * item.softBreaks || heights.br.br < item.softBreaks) {
        notMeasured.push({ part: "heights", id: item.id, reason: "<br> 갈래의 높이가 한 줄 바꿈 수와 맞지 않는다", base, br });
        continue;
      }
      const cssVariants = HEIGHT_VARIANTS.slice(2);
      const compared = cssVariants.map((variant, index) => {
        const height = heights[variant.name].height;
        const got = height === br ? "same" : height > br ? "more" : "less";
        return { variant: variant.name, height, overBr: height - br, got, expected: item.expect[index], asExpected: got === item.expect[index] };
      });
      rows.push({ id: item.id, text: item.text, softBreaks: item.softBreaks, none: base, br, compared });
    }
  } finally {
    await settle(browser.close(), 15_000);
  }
  return rows;
}

// ───────────────────────── 보고 ─────────────────────────

function sweepLine(row) {
  const after = row.responsive ? row.after : null;
  const failure = row.mount.failures?.[0] ?? null;
  return (
    `${row.browser.padEnd(14)} ${row.name.padEnd(26)} ${row.mode.padEnd(8)} 상태=${String(row.mount.state ?? (row.mount.timedOut ? "제한 시간" : "?")).padEnd(8)}` +
    ` 던짐=${row.verdict.threw}${failure === null ? "" : `(${failure.name} @ ${failure.frames[0]?.pkg ?? "?"})`} 원문=${row.verdict.fellBackToRaw}` +
    ` ${row.verdict.ms}ms 응답=${row.verdict.responsive} 가로 넘침=${row.verdict.overflow}` +
    `${after === null ? "" : `(문서 ${after.docScrollWidth}px, 가장 깊은 ${after.deepest?.tag}@${after.deepest?.left}px 폭 ${after.deepest?.width}px, 깊이 ${after.maxDepth})`}` +
    ` 크래시=${row.verdict.crashed} 콘솔=${row.events?.console.length ?? "?"} 페이지오류=${row.events?.pageErrors.length ?? "?"}`
  );
}

function reportText(summary) {
  const lines = [];
  const say = (line = "") => lines.push(line);
  say(`브라우저 프로브 · Playwright ${summary.versions.playwright} · ${Object.entries(summary.versions.browsers).map(([name, version]) => `${name} ${version}`).join(" · ")} · React ${summary.versions.react} · Node ${summary.versions.node}`);
  say(`측정이 아닌 회차: ${summary.notMeasured.length}`);
  if (summary.capture !== undefined) {
    say();
    say("== capture: 실패를 받는 두 방법 ==");
    for (const row of summary.capture) {
      say(`[${row.browser} · ${row.mode} / 처리기 ${row.handlers}]`);
      for (const step of row.steps) {
        const failure = step.newFailures[0];
        say(
          `  ${step.step.padEnd(14)} 상태=${String(step.state).padEnd(8)} 원문과 같다=${step.rawEqualsText} onFailure=${step.newFailures.length}` +
            `${failure === undefined || failure === null ? "" : `(${failure.name} @ ${failure.frames[0]?.pkg ?? "?"})`}` +
            ` 콘솔=${step.newConsole.length} 페이지오류=${step.newPageErrors.length} 뿌리=${step.newRootErrors.map((e) => e.kind).join(",") || "-"} 보이는 글=${JSON.stringify(step.shownText)}`,
        );
        for (const entry of step.newConsole) say(`      콘솔 ${entry.type}: ${entry.text.slice(0, 120)}`);
        for (const entry of step.newPageErrors) say(`      페이지 오류: ${entry.name}: ${entry.message.slice(0, 100)}`);
      }
    }
  }
  if (summary.stages !== undefined) {
    say();
    say("== stages: 어느 단계에서 던지나 ==");
    for (const row of summary.stages.rows) {
      if (row.reached === undefined) {
        say(`  ${row.env.padEnd(14)} ${row.name.padEnd(26)} ${row.timedOut ? "제한 시간" : row.crashed ? "크래시" : "측정 아님"}`);
        continue;
      }
      const threw =
        row.threw === null
          ? `던지지 않는다${row.renderedAll === undefined ? "" : ` · 그린 겹 ${row.renderedDepth}${row.renderedAll === false ? "(모자란다)" : ""}`}` +
            `${row.crashedAfterRender === true ? " · 그린 뒤 렌더러가 죽었다" : ""}${row.measureProblem === undefined ? "" : ` · 치수 재기 실패 ${JSON.stringify(row.measureProblem).slice(0, 120)}`}`
          : `${row.threw.name} @ ${row.threw.stage} (${row.threw.frames.map((f) => `${f.fn}·${f.pkg}`).join(" < ")})`;
      say(`  ${row.env.padEnd(14)} ${row.name.padEnd(26)} 표지=${row.reached.join(">") || "-"} 거르기 호출=${row.filterCalls} ${row.markdownMs}ms ${threw}`);
    }
    say(`  ${summary.stages.repeats.name} 을 ${summary.stages.repeats.rounds}번: ${JSON.stringify(summary.stages.repeats.byEnv)}`);
  }
  if (summary.threshold !== undefined) {
    say();
    say("== threshold: `Markdown` 이 던지기 시작하는 깊이(마지막 통과/첫 던짐) ==");
    const show = (list) => list.map((e) => (e === null ? "측정 아님" : e.bracketed ? `${e.lastPass}/${e.firstThrow}` : `좁히지 못함(lo 던짐=${e.loThrows}, hi 던짐=${e.hiThrows})`)).join(", ");
    for (const [kind, entry] of Object.entries(summary.threshold.kinds)) {
      say(`  ${kind}: ${Object.entries(entry).map(([env, list]) => `${env} ${show(list)}`).join(" · ")}`);
    }
    for (const row of summary.threshold.edge) say(`  경계 ${sweepLine(row)}${row.thenNormal === undefined ? "" : ` → 보통 글: ${row.thenNormal.state ?? JSON.stringify(row.thenNormal).slice(0, 80)} ${JSON.stringify(row.thenNormal.shownText)}`}`);
  }
  if (summary.sweep !== undefined) {
    say();
    say("== sweep: 시제품으로 그린 결과 ==");
    for (const row of summary.sweep) say(`  ${sweepLine(row)}`);
  }
  if (summary.crash !== undefined) {
    say();
    say("== crash: 렌더러가 죽기 시작하는 깊이 ==");
    for (const [browser, list] of Object.entries(summary.crash)) {
      for (const entry of list) {
        say(
          `  ${browser.padEnd(14)} ${entry.build.padEnd(10)} 죽지 않는 가장 깊은 깊이 ${entry.lastAlive} · 죽는 첫 깊이 ${entry.firstDead}` +
            `${entry.again === undefined ? "" : ` · 다시 보기 ${JSON.stringify(entry.again)}`} · 본 깊이 ${entry.checks.map((c) => `${c.depth}${c.diedAt === null ? (c.built === "raw" ? "(원문)" : "") : `(${c.diedAt}에서 죽음)`}`).join(", ")}`,
        );
      }
    }
  }
  if (summary.guard !== undefined) {
    say();
    say(`== guard: 깊이 가드(한도 ${summary.versions.guardDepth}겹)를 켠 갈래 ==`);
    for (const row of summary.guard) say(`  ${sweepLine(row)} 가드=${row.guard.failure ?? "-"}`);
  }
  if (summary.fine !== undefined) {
    say();
    say("== fine: 화면이 넘치기 시작하는 깊이 ==");
    for (const [kind, entry] of Object.entries(summary.fine)) {
      say(
        `  ${kind}: 깊이 1 의 안쪽 폭 ${entry.widthAtDepth1}px · 안쪽 폭이 글자 하나(15px)보다 좁아지는 첫 깊이 ${entry.firstNarrowerThanOneChar}` +
          ` · 문서가 가로로 넘치는 첫 깊이 ${entry.firstDocumentOverflow} · 가장 안쪽이 창 밖으로 나가는 첫 깊이 ${entry.firstOffscreen}`,
      );
    }
  }
  if (summary.heights !== undefined) {
    say();
    say("== heights: 한 줄 바꿈을 CSS 로 보일 때의 높이(px). <br> 갈래와 견준다 ==");
    for (const row of summary.heights) {
      say(
        `  ${row.id.padEnd(30)} none=${row.none} br=${row.br} ` +
          row.compared.map((c) => `${c.variant.replace("css-", "")}=${c.height}(${c.overBr >= 0 ? "+" : ""}${c.overBr}${c.asExpected ? "" : ` 기대 ${c.expected}`})`).join(" "),
      );
    }
  }
  if (summary.notMeasured.length > 0) {
    say();
    say("== 측정이 아닌 회차 ==");
    for (const entry of summary.notMeasured) say(`  ${JSON.stringify(entry).slice(0, 400)}`);
  }
  return `${lines.join("\n")}\n`;
}

// ───────────────────────── main ─────────────────────────

async function main() {
  mkdirSync(OUT, { recursive: true });
  if (chromiumPath() === null) {
    console.log(JSON.stringify({ probe: "browser", chromium: null, reason: `Playwright ${PLAYWRIGHT_VERSION} 이 찾는 Chromium 이 없다(${chromium.executablePath()}). 내려받지 않았다.` }));
    process.exit(3);
  }
  const made = await bundle({
    entry: join(ROOT, "probe", "browser-entry.tsx"),
    outfile: join(OUT, "browser-entry.js"),
    format: "iife",
    platform: "browser",
    globalName: "MdProbe",
    mustBundle: ["react-dom/cjs/react-dom-client.production.js", "react/cjs/react.production.js", "react-markdown/lib/index.js"],
  });
  const nodeBundle = await bundle({
    entry: join(ROOT, "probe", "stage-node-entry.tsx"),
    outfile: join(ROOT, "out", "build", "stage-node-entry.cjs"),
    format: "cjs",
    platform: "node",
    mustBundle: ["react-dom/cjs/react-dom-server", "react/cjs/react.production.js", "react-markdown/lib/index.js"],
  });
  const bundleProblems = [...made.problems, ...nodeBundle.problems];
  if (bundleProblems.length > 0) {
    console.error("묶음이 기대와 다르다", bundleProblems);
    console.log(JSON.stringify({ probe: "browser", notMeasured: bundleProblems.length, bundleProblems }));
    process.exit(1);
  }

  const versions = { playwright: PLAYWRIGHT_VERSION, node: process.version, browsers: {} };
  for (const target of TARGETS) {
    let browser;
    try {
      browser = await launch(target);
    } catch (error) {
      console.log(JSON.stringify({ probe: "browser", browser: target.name, reason: `띄우지 못했다(내려받지 않았다): ${String(error).slice(0, 300)}` }));
      process.exit(3);
    }
    try {
      versions.browsers[target.name] = browser.version();
      const { page } = await openPage(browser, pageHtml(), made.outfile);
      const info = await page.evaluate(() => MdProbe.info());
      versions.react = info.react;
      versions.guardDepth = info.guardDepth;
      versions.hostWidth = await page.evaluate(() => document.getElementById("host").clientWidth);
    } finally {
      await settle(browser.close(), 15_000);
    }
  }

  const summary = { probe: "browser", parts, only, versions, notMeasured };
  if (parts.includes("capture")) summary.capture = await runCapture(made);
  if (parts.includes("stages")) summary.stages = await runStages(made, nodeBundle);
  if (parts.includes("threshold")) summary.threshold = await runThreshold(made, nodeBundle);
  if (parts.includes("sweep")) summary.sweep = await runSweep(made);
  if (parts.includes("crash")) summary.crash = await runCrash(made);
  if (parts.includes("guard")) summary.guard = await runGuard(made, versions.guardDepth);
  if (parts.includes("fine")) summary.fine = await runFine(made);
  if (parts.includes("heights")) summary.heights = await runHeights(made);

  const whole = parts.length === PARTS.length && only === null;
  writeFileSync(join(OUT, whole ? "summary.json" : "partial.json"), JSON.stringify(summary, null, 2));
  writeFileSync(join(OUT, whole ? "report.txt" : "partial-report.txt"), reportText(summary));
  const firstThrows = (list) => list.map((e) => (e === null ? null : (e.firstThrow ?? "좁히지 못함")));
  console.log(
    JSON.stringify({
      probe: "browser",
      parts,
      only,
      versions,
      notMeasured: notMeasured.length,
      capture: summary.capture?.map((row) => ({
        branch: `${row.browser}/${row.mode}/${row.handlers}`,
        states: row.steps.map((step) => step.state),
        console: row.steps.map((step) => step.newConsole.length),
        pageErrors: row.steps.map((step) => step.newPageErrors.length),
      })),
      stagesThrown: summary.stages?.rows
        .filter((row) => row.threw !== null && row.threw !== undefined)
        .map((row) => `${row.env} ${row.name}: ${row.threw.stage}`),
      stageRepeats: summary.stages?.repeats.byEnv,
      threshold:
        summary.threshold === undefined
          ? undefined
          : Object.fromEntries(
              Object.entries(summary.threshold.kinds).map(([kind, entry]) => [
                kind,
                Object.fromEntries(Object.entries(entry).map(([env, list]) => [env, firstThrows(list)])),
              ]),
            ),
      sweep: summary.sweep?.map(
        (row) =>
          `${row.browser} ${row.name} ${row.mode}: ${row.mount.state ?? "?"}${row.verdict.overflow ? " 넘침" : ""}${row.verdict.crashed ? " 크래시" : ""}${row.verdict.responsive ? "" : " 무응답"}`,
      ),
      crash:
        summary.crash === undefined
          ? undefined
          : Object.fromEntries(
              Object.entries(summary.crash).map(([browser, list]) => [browser, list.map((entry) => `${entry.build}: ${entry.lastAlive}/${entry.firstDead}`)]),
            ),
      guard: summary.guard?.map(
        (row) => `${row.browser} ${row.name}: ${row.mount.state ?? "?"}${row.guard.failure === null ? "" : ` ${row.guard.failure}`}${row.verdict.crashed ? " 크래시" : ""}${row.verdict.overflow ? " 넘침" : ""}`,
      ),
      fine:
        summary.fine === undefined
          ? undefined
          : Object.fromEntries(
              Object.entries(summary.fine).map(([kind, entry]) => [kind, { narrow: entry.firstNarrowerThanOneChar, overflow: entry.firstDocumentOverflow }]),
            ),
      heightsUnexpected: summary.heights?.flatMap((row) => row.compared.filter((c) => !c.asExpected).map((c) => `${row.id} ${c.variant}: ${c.got}(기대 ${c.expected})`)),
    }),
  );
  if (notMeasured.length > 0) {
    console.error("측정이 아닌 회차", JSON.stringify(notMeasured, null, 2).slice(0, 4000));
    process.exit(1);
  }
}

await main();
