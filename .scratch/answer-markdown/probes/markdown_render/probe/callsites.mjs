// 호출 자리 프로브(2026-11-11). 출력을 마크다운 부품으로 그리면 "답의 글자"를 보는 기존 시험의 로케이터가 무엇에 맞게
// 되는지를, 지금의 구조와 바꿀 구조에 같은 로케이터를 걸어 센다. 명세가 "고칠 시험"과 "그대로 서는 시험"을 가르는 근거다.
//
// 돌리기: node probe/callsites.mjs
// 산출물: out/callsites/summary.json, out/callsites/report.txt, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 두 구조(읽기 영역은 대화 영역의 앞 형제다. web/apps/widget/components/pages/WidgetScreen.tsx 150~159줄과
// organisms/Conversation.tsx 81~86, 213~216줄을 읽고 옮겼다)
// - current: 대화 목록의 항목에 `<p><span class="sr-only">출력: </span>글</p>`, 읽기 영역에 `<p>글</p>`.
// - proposed: 대화 목록의 항목에 `<div data-output><span class="sr-only">출력: </span>(마크다운 부품)</div>`, 읽기 영역에
//   `<p>(글자만의 갈래)</p>`. 부품과 글자만의 갈래는 합친 시제품을 Node 의 `renderToStaticMarkup` 으로 그린 것이다
//   (plain-entry.tsx).
//
// 거는 로케이터(실제 Playwright. 괄호는 그 로케이터를 쓰는 자리)
// A. page.getByText(글, { exact: true })                         (widget.e2e.ts 46·49·94·158줄)
// B. 대화.getByText("출력: " + 글, { exact: true })              (widget.e2e.ts 126·164·187줄, element.e2e.ts 33줄)
// C. 대화.getByText("출력: " + 글)                               (widget.e2e.ts 198줄)
// D. page.getByText("출력: " + 글)                               (portal 의 acknowledge.e2e.ts 78줄, sites.e2e.ts 72줄)
// E. 대화.getByRole("paragraph").filter({ hasText: "출력: " })   (widget 과 portal 의 calc.llm.ts)
// F. Testing Library 의 `findByText(글, { selector: "ol p" })`   (web/apps/widget/testing/widget.tsx 의 findOutput)
//    F 는 그 라이브러리를 돌린 것이 아니다. 기본 매처의 규칙(요소 자신의 글자 노드를 이어 붙여 앞뒤 공백을 떼고 공백을
//    하나로 줄인 글이 찾는 글과 같다)을 페이지 안에서 손으로 옮겨 센 것이다. 그래서 F 의 결과는 어림이다.
//
// 글: findOutput 에 넘기는 글 열 가지(위젯의 화면 테스트 다섯 파일에서 글자 그대로 모아 이 파일의 목록과 견준다)와
// e2e 픽스처의 출력 넷(`5/9`, `total:5`, `chars:7`, HTML 조각).
//
// 측정이 아닌 회차(.claude/rules/probes.md). 하나라도 있으면 종료 코드 1.
// - 양성 대조: current 구조에서 A~F 가 모두 하나에 맞아야 한다(지금의 시험이 그 로케이터로 통과하고 있다). 어긋나면
//   이 프로브가 지은 페이지가 지금 화면을 닮지 않은 것이라 proposed 의 수가 뜻이 없다.
// - 표지: 두 구조 모두 대화 영역(`role=region`, 이름 "대화")과 읽기 영역(`role=status`)이 하나씩 있고, proposed 에는 답의
//   칸(`[data-answer="markdown"]`)이 하나 있어야 한다.
// - 화면 테스트 파일에서 모은 글이 이 파일의 목록과 다르거나, HTML 조각이 e2e-stack 의 원문과 다르다.
// Chromium 이 없으면 종료 코드 3(내려받지 않는다).
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { chromium } from "playwright";
import { chromiumPath, PLAYWRIGHT_VERSION } from "./browser-kit.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const REPO = join(ROOT, "..", "..", "..", "..");
const OUT = join(ROOT, "out", "callsites");
const BUNDLE = join(ROOT, "out", "build", "plain-entry.cjs");

const FIND_OUTPUT_TEXTS = [
  "환불했습니다.",
  "환불을 요청하지 않았습니다.",
  "새로 시작",
  "도착 예정입니다.",
  "끝",
  "셋째 끝",
  "둘째 끝",
  "새로 끝",
  "넷째 끝",
  "새 사람의 답",
];
const HTML_OUTPUT = '<img src="x" onerror="window.__widgetE2ePwned = 1"><script>window.__widgetE2ePwned = 2</script>';
const FIXTURE_OUTPUTS = ["5/9", "total:5", "chars:7", HTML_OUTPUT];
const PREFIX = "출력: ";

const TEST_FILES = ["WidgetApproval", "WidgetConversation", "WidgetFailures", "WidgetReconnect", "WidgetStorage"].map((name) =>
  join(REPO, "web", "apps", "widget", "components", "pages", `${name}.test.tsx`),
);

const esc = (value) => value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

/** `<div data-probe="shown">…</div>` 같은 바깥 표지 요소를 벗긴다. 모양이 다르면 null 이다. */
function inner(html, open, close) {
  return html.startsWith(open) && html.endsWith(close) ? html.slice(open.length, html.length - close.length) : null;
}

function documentOf(status, item) {
  return [
    "<!doctype html>",
    '<html lang="ko"><head><meta charset="utf-8"><title>호출 자리 프로브</title>',
    "<style>.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}</style></head>",
    "<body><main>",
    `<div role="status" aria-atomic="false" class="sr-only">${status}</div>`,
    `<div role="region" aria-label="대화" tabindex="0"><ol><li>${item}</li></ol></div>`,
    "</main></body></html>",
  ].join("\n");
}

/** 화면 테스트 파일에서 `findOutput("…")` 의 글을 글자 그대로 모은다. 글자열이 아닌 인자는 따로 센다. */
function collectFindOutputTexts() {
  const texts = new Set();
  let calls = 0;
  let nonLiteral = 0;
  for (const file of TEST_FILES) {
    const source = readFileSync(file, "utf8");
    for (const match of source.matchAll(/findOutput\(([^)]*)\)/g)) {
      calls += 1;
      const literal = /^"((?:[^"\\]|\\.)*)"$/.exec(match[1].trim());
      if (literal === null) nonLiteral += 1;
      else texts.add(JSON.parse(`"${literal[1]}"`));
    }
  }
  return { texts: [...texts], calls, nonLiteral };
}

async function count(locator) {
  return locator.count();
}

async function measure(page, text) {
  const conversation = page.getByRole("region", { name: "대화" });
  const paragraphs = conversation.getByRole("paragraph").filter({ hasText: PREFIX });
  const paragraphCount = await count(paragraphs);
  return {
    signs: {
      regions: await count(conversation),
      statuses: await count(page.getByRole("status")),
      answers: await count(page.locator('[data-answer="markdown"]')),
    },
    A: await count(page.getByText(text, { exact: true })),
    B: await count(conversation.getByText(`${PREFIX}${text}`, { exact: true })),
    C: await count(conversation.getByText(`${PREFIX}${text}`)),
    D: await count(page.getByText(`${PREFIX}${text}`)),
    E: paragraphCount,
    // E 가 하나에 맞으면 실제 모델 e2e 가 읽는 글(머리말을 떼기 전)이다.
    eText: paragraphCount === 1 ? await paragraphs.textContent() : null,
    F: await page.evaluate((wanted) => {
      const ownText = (node) =>
        [...node.childNodes]
          .filter((child) => child.nodeType === Node.TEXT_NODE && Boolean(child.textContent))
          .map((child) => child.textContent)
          .join("");
      return [...document.querySelectorAll("ol p")].filter((node) => ownText(node).trim().replace(/\s+/g, " ") === wanted).length;
    }, text),
    // 바꿀 구조에서 답의 칸에 보이는 글(숨긴 글 포함). 로케이터를 고칠 때의 참고다.
    answerText: await page.evaluate(() => document.querySelector("[data-answer]")?.textContent ?? null),
  };
}

async function main() {
  if (chromiumPath() === null) {
    console.error("Chromium 이 없다. 내려받지 않는다.");
    process.exit(3);
  }
  mkdirSync(dirname(BUNDLE), { recursive: true });
  await build({
    entryPoints: [join(ROOT, "probe", "plain-entry.tsx")],
    outfile: BUNDLE,
    bundle: true,
    platform: "node",
    format: "cjs",
    jsx: "automatic",
    define: { "process.env.NODE_ENV": '"production"' },
    logLevel: "warning",
  });
  const entry = createRequire(import.meta.url)(BUNDLE);
  rmSync(OUT, { recursive: true, force: true });
  mkdirSync(OUT, { recursive: true });

  const notMeasured = [];

  // 전제: 목록이 저장소의 지금 글과 같다.
  const collected = collectFindOutputTexts();
  const missing = collected.texts.filter((text) => !FIND_OUTPUT_TEXTS.includes(text));
  const extra = FIND_OUTPUT_TEXTS.filter((text) => !collected.texts.includes(text));
  if (missing.length > 0 || extra.length > 0 || collected.nonLiteral > 0) {
    notMeasured.push({ reason: "화면 테스트의 findOutput 글이 이 파일의 목록과 다르다", missing, extra, nonLiteral: collected.nonLiteral });
  }
  const stack = readFileSync(join(REPO, "web", "packages", "e2e-stack", "src", "plugins.ts"), "utf8");
  if (!stack.includes(`'${HTML_OUTPUT}'`)) notMeasured.push({ reason: "HTML 조각이 e2e-stack 의 원문과 다르다" });

  const browser = await chromium.launch();
  const version = browser.version();
  const context = await browser.newContext({ viewport: { width: 320, height: 640 } });
  const page = await context.newPage();
  const rows = [];
  const inputs = [
    ...FIND_OUTPUT_TEXTS.map((text) => ({ group: "findOutput", text })),
    ...FIXTURE_OUTPUTS.map((text) => ({ group: "e2e 픽스처", text })),
  ];
  for (const input of inputs) {
    const both = entry.renderBoth(input.text);
    const shown = inner(both.shown, '<div data-probe="shown">', "</div>");
    const plain = inner(both.plain, '<p data-probe="plain">', "</p>");
    if (shown === null || plain === null || both.failed.shown || both.failed.plain) {
      notMeasured.push({ ...input, reason: "표지가 없거나 그리다 물러섰다", failed: both.failed });
      continue;
    }
    const structures = {
      current: documentOf(`<p>${esc(input.text)}</p>`, `<p><span class="sr-only">${PREFIX}</span>${esc(input.text)}</p>`),
      proposed: documentOf(`<p>${plain}</p>`, `<div data-output><span class="sr-only">${PREFIX}</span>${shown}</div>`),
    };
    const row = { ...input, shown, plain };
    for (const [name, html] of Object.entries(structures)) {
      await page.setContent(html);
      row[name] = await measure(page, input.text);
    }
    // 표지
    for (const name of ["current", "proposed"]) {
      const { regions, statuses, answers } = row[name].signs;
      if (regions !== 1 || statuses !== 1 || answers !== (name === "proposed" ? 1 : 0)) {
        notMeasured.push({ ...input, structure: name, reason: "대화 영역·읽기 영역·답의 칸의 수가 기대와 다르다", signs: row[name].signs });
      }
    }
    // 양성 대조: 지금 구조에서는 모든 로케이터가 하나에 맞는다.
    const baseline = ["A", "B", "C", "D", "E", "F"].filter((key) => row.current[key] !== 1);
    if (baseline.length > 0) {
      notMeasured.push({ ...input, reason: "지금 구조에서 하나에 맞지 않는 로케이터가 있다", locators: Object.fromEntries(baseline.map((key) => [key, row.current[key]])) });
    }
    rows.push(row);
  }
  await browser.close();

  const table = rows.map((row) => ({
    group: row.group,
    text: row.text.length > 40 ? `${row.text.slice(0, 40)}…` : row.text,
    current: Object.fromEntries(["A", "B", "C", "D", "E", "F"].map((key) => [key, row.current[key]])),
    proposed: Object.fromEntries(["A", "B", "C", "D", "E", "F"].map((key) => [key, row.proposed[key]])),
  }));
  const changed = {};
  for (const key of ["A", "B", "C", "D", "E", "F"]) {
    changed[key] = [...new Set(rows.map((row) => row.proposed[key]))].sort();
  }
  const summary = {
    probe: "callsites",
    versions: { playwright: PLAYWRIGHT_VERSION, chromium: version, node: process.version },
    findOutput: { calls: collected.calls, distinct: collected.texts.length, nonLiteral: collected.nonLiteral },
    inputs: inputs.length,
    measured: rows.length,
    notMeasured,
    // 바꿀 구조에서 로케이터마다 나온 수(입력 전체에서 서로 다른 값).
    proposedCounts: changed,
    table,
    rows,
  };
  writeFileSync(join(OUT, "summary.json"), `${JSON.stringify(summary, null, 2)}\n`);

  const report = [];
  report.push(`호출 자리 프로브 (Playwright ${PLAYWRIGHT_VERSION}, Chromium ${version}, Node ${process.version})`);
  report.push(`findOutput 호출 ${String(collected.calls)}곳, 서로 다른 글 ${String(collected.texts.length)}가지, 글자열이 아닌 인자 ${String(collected.nonLiteral)}곳`);
  report.push("A page.getByText(글, exact)  B 대화.getByText(출력: 글, exact)  C 대화.getByText(출력: 글)  D page.getByText(출력: 글)");
  report.push("E 대화.getByRole(paragraph).filter(hasText 출력: )  F findByText(글, selector ol p) 의 규칙을 옮긴 것");
  report.push("");
  for (const row of table) {
    report.push(`[${row.group}] ${JSON.stringify(row.text)}`);
    report.push(`    지금: ${JSON.stringify(row.current)}`);
    report.push(`    바꿈: ${JSON.stringify(row.proposed)}`);
  }
  report.push("");
  report.push("== 바꿀 구조에서 답의 칸에 보이는 글과 E 가 읽는 글 ==");
  for (const row of rows) {
    report.push(`  ${JSON.stringify(row.text.slice(0, 40))}: 답의 칸 ${JSON.stringify(row.proposed.answerText)}, 지금 E 의 글 ${JSON.stringify(row.current.eText)}`);
  }
  report.push("");
  report.push("== 측정이 아닌 회차 ==");
  for (const item of notMeasured) report.push(`  ${JSON.stringify(item)}`);
  writeFileSync(join(OUT, "report.txt"), `${report.join("\n")}\n`);

  console.log(
    JSON.stringify({
      probe: "callsites",
      versions: summary.versions,
      findOutput: summary.findOutput,
      inputs: inputs.length,
      measured: rows.length,
      notMeasured: notMeasured.length,
      proposedCounts: changed,
    }),
  );
  process.exit(notMeasured.length > 0 ? 1 : 0);
}

await main();
