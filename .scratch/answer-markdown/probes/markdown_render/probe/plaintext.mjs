// 글자만 내는 갈래의 프로브(2026-11-11). 화면 읽기 영역(role="status")에 "기호를 뗀 글"을 넘기려고, 화면에 그리는 것과
// 같은 변환과 허용 목록을 지난 나무에서 요소를 그리지 않고 글자만 남기는 갈래(시제품의 `Plain`)를 본다.
//
// 돌리기: node probe/plaintext.mjs
// 산출물: out/plaintext/summary.json(입력마다의 판정), out/plaintext/report.txt(사람이 읽는 글. 화면 파일의 입력 다섯은
//         글자만의 글을 그대로 싣는다), 표준 출력의 마지막 줄(JSON 한 줄)
//
// 입력: textcompare.mjs 와 같은 모음(기존 52가지, 모양 프로브의 사례, 화면 파일의 입력 다섯, 병적인 입력 열넷)에 이
// 프로브만의 입력(OWN_CASES)을 더한다. 입구는 plain-entry.tsx 이고 합친 시제품(`AnswerMarkdown`)과 글자만의 갈래 둘
// (`AnswerPlain`, 번호를 되살리지 않는 `AnswerPlainWithoutOrdinals`)을 Node 의 `renderToStaticMarkup` 으로 그린다.
//
// 재는 것(입력마다)
// 1. 요소 없음: 글자만의 갈래 둘 다 `p[data-probe="plain"]` 아래가 글자 노드뿐이다.
// 2. 낱말 견줌: 화면의 글과 글자만의 글(번호를 되살리지 않은 것)을 공백으로 끊은 낱말의 열이 같다. 화면 쪽은 `.sr-only`
//    를 빼고, 블록 요소의 처음과 끝, `<br>`, 위첨자 번호(`sup`)의 앞을 공백으로 친다. 열이 같으면 글자가 같고, 화면에서
//    따로 서는 블록·목록 항목·표의 칸이 글자만의 글에서도 서로 붙지 않는다.
// 3. 번호: 번호를 되살린 글은 2 의 열에 번호 낱말(`3.`)만 더한 것이고, 더한 낱말의 열이 화면의 번호 목록(`ol` 의 `start`
//    와 항목의 차례)과 같다.
// 4. 실패: 세 갈래(화면, 글자만, 번호 없는 글자만)가 함께 원문으로 물러선 입력은 세 글이 모두 원문과 글자 그대로 같다.
// 5. 갈린 입력(`diverged`): 세 갈래 가운데 일부만 물러선 입력. 깊이 가드가 없는 합친 시제품에서는 스택 문턱 근처의
//    입력(`>` 3,000겹)이 실행마다, 갈래마다 던지기도 하고 그리기도 한다(2026-11-11 의 세 실행 가운데 둘은 세 갈래가
//    함께 물러섰고 하나는 글자만의 갈래만 물러섰다). 어긋남과 따로 세고, 어느 갈래가 어떤 오류로 물러섰는지 적는다.
// 6. 깊이 가드(`renderBothGuarded`, 한도 GUARD_DEPTH 겹): 모든 입력을 가드를 켠 묶음으로 한 번 더 그려, 세 갈래가
//    함께 물러서거나 함께 그리는지 본다. 가드의 사례(GUARD_CASES)는 한도까지는 세 갈래 모두 그리고, 한도를 넘으면
//    세 갈래 모두 `AnswerTooDeepError` 로 물러서는지 본다.
// 어긋난 입력과 갈린 입력은 측정 결과다(종료 코드 0). 마지막 줄의 `mismatched`, `diverged`, `guard` 에 적는다.
//
// 측정이 아닌 회차(.claude/rules/probes.md). 하나라도 있으면 종료 코드 1.
// - 그렸는데 표지(`div[data-probe="shown"]`, `p[data-probe="plain"]`)가 없는 입력.
// - 화면의 갈래가 물러서지 않았는데 답의 칸(`div[data-answer="markdown"]`)이 없는 입력.
// - 재려는 상황이 한 번도 나지 않은 것. 표의 칸(한 줄에 둘 이상), 번호 목록, 1 이 아닌 수로 시작하는 번호 목록, 겹친
//   목록, 위첨자 번호, 이미지 자리, `<br>`, 코드 블록, 세 갈래가 함께 원문으로 물러선 입력이 각각 하나 이상 있어야 그
//   상황의 결론을 낸다. 함께 물러서는 입력은 문턱에서 먼 `>` 20,000겹(p15)으로 확실히 낸다.
// - 가드의 절에서 `AnswerTooDeepError` 가 한 번도 나지 않은 것(가드가 걸려 있지 않다)과, 가드를 켜고도 한도 이하의
//   사례가 하나도 그려지지 않은 것(가드가 모든 입력을 막고 있다).
// 판정 함수의 자가 시험이 틀리면 종료 코드 2. 자가 시험에는 판정이 "붙었다"와 "번호가 틀렸다"를 실제로 가려내는 양성
// 대조(손으로 지은 HTML 과 글)가 든다.
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { parseFragment } from "parse5";
import { CASES } from "./cases.mjs";
import { DEPTH_KINDS, STRESS_INPUTS } from "./inputs.mjs";
import { GROUPS, SCREEN_INPUTS } from "./shape-cases.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "plaintext");
const BUNDLE = join(ROOT, "out", "build", "plain-entry.cjs");

// 이 프로브만의 입력. 다른 모음에 드물거나 없는 모양(1 이 아닌 시작 번호, 겹친 번호 목록, 빈 칸, 느슨한 목록 등)이다.
const OWN_CASES = [
  { id: "p01-ordered-from-3", text: "3. 셋\n4. 넷\n5. 다섯" },
  { id: "p02-ordered-in-bullets", text: "- 가\n  1. 하나\n  2. 둘\n- 나" },
  { id: "p03-ordered-in-ordered", text: "1. 가\n   1. 안\n   2. 쪽\n2. 나" },
  { id: "p04-empty-cell", text: "| 가 | 나 |\n|---|---|\n|  | 다 |\n| 라 |  |" },
  { id: "p05-loose-list", text: "1. 가\n\n   둘째 문단\n\n2. 나" },
  { id: "p06-image-in-link", text: "[![그림](https://a.example/a.png)](https://a.example/) 뒤의 글" },
  { id: "p07-code-block-html", text: "앞\n\n```html\n<b>x</b>\n<i>y</i>\n```\n\n뒤" },
  { id: "p08-inline-marks", text: "~~지움~~ **굵게** *기울임* `코드` [링크](https://a.example/)" },
  { id: "p09-raw-html", text: "<b>굵게</b> 글 <script>x()</script>" },
  { id: "p10-task-list", text: "- [x] 한 일\n- [ ] 할 일" },
  { id: "p11-cells-with-marks", text: "| **서류** | `발급처` |\n|---|---|\n| [등본](https://a.example/) | 정부24 |" },
  { id: "p12-quote-with-list", text: "> 인용 첫 줄\n> - 항목 하나\n> - 항목 둘\n\n끝" },
  { id: "p13-soft-breaks", text: "첫 줄\n둘째 줄\n셋째 줄" },
  { id: "p14-heading-then-text", text: "# 제목\n본문\n\n## 작은 제목\n- 항목" },
  // 세 갈래가 함께 물러서는 입력. `>` 3,000겹은 스택 문턱 근처라 실행마다 갈리므로 문턱에서 먼 깊이를 따로 둔다.
  { id: "p15-quote-20000", text: `${">".repeat(20_000)} a` },
];

// 깊이 가드의 사례. `expect` 는 가드를 켠 묶음에서 세 갈래가 낼 결과다. 겹 수는 인용과 목록을 합쳐 센다.
const GUARD_CASES = [
  { id: "quote:10", text: DEPTH_KINDS.quote(10), expect: "drawn" },
  { id: "quote:11", text: DEPTH_KINDS.quote(11), expect: "too-deep" },
  { id: "list-inline:10", text: DEPTH_KINDS["list-inline"](10), expect: "drawn" },
  { id: "list-inline:11", text: DEPTH_KINDS["list-inline"](11), expect: "too-deep" },
  { id: "list-indent:10", text: DEPTH_KINDS["list-indent"](10), expect: "drawn" },
  { id: "list-indent:11", text: DEPTH_KINDS["list-indent"](11), expect: "too-deep" },
  { id: "mixed:5+5", text: `${"> - ".repeat(5)}a`, expect: "drawn" },
  { id: "mixed:6+5", text: `${"> - ".repeat(5)}> a`, expect: "too-deep" },
  { id: "quote:2500", text: DEPTH_KINDS.quote(2_500), expect: "too-deep" },
  { id: "quote:3000", text: DEPTH_KINDS.quote(3_000), expect: "too-deep" },
  { id: "list-indent:200", text: DEPTH_KINDS["list-indent"](200), expect: "too-deep" },
];
const TOO_DEEP = "AnswerTooDeepError";

const BLOCKS = new Set([
  "p", "div", "blockquote", "ul", "ol", "li", "table", "thead", "tbody", "tr", "th", "td", "pre", "hr", "br",
  "h1", "h2", "h3", "h4", "h5", "h6",
]);

const attr = (node, name) => (node.attrs ?? []).find((a) => a.name === name)?.value;
const hasClass = (node, name) => (attr(node, "class") ?? "").split(/\s+/).includes(name);
const words = (text) => text.split(/\s+/u).filter((word) => word !== "");

function findOne(node, test) {
  const stack = [node];
  while (stack.length > 0) {
    const current = stack.pop();
    if (test(current)) return current;
    const children = current.childNodes ?? [];
    for (let i = children.length - 1; i >= 0; i -= 1) stack.push(children[i]);
  }
  return null;
}

function countAll(node, test) {
  let count = 0;
  const stack = [node];
  while (stack.length > 0) {
    const current = stack.pop();
    if (test(current)) count += 1;
    for (const child of current.childNodes ?? []) stack.push(child);
  }
  return count;
}

/** 요소 아래의 글자를 그대로 이어 붙인다. */
function rawText(node) {
  let out = "";
  const stack = [node];
  while (stack.length > 0) {
    const current = stack.pop();
    if (current.nodeName === "#text") {
      out += current.value;
      continue;
    }
    const children = current.childNodes ?? [];
    for (let i = children.length - 1; i >= 0; i -= 1) stack.push(children[i]);
  }
  return out;
}

/** 화면의 글. `.sr-only` 를 빼고, 블록 요소의 처음과 끝·`<br>`·`sup` 의 앞을 공백으로 친다. */
export function shownText(box) {
  let out = "";
  // 차례를 지키려고 "열기"와 "닫기"를 스택에 함께 넣는다.
  const stack = [{ node: box, close: false }];
  while (stack.length > 0) {
    const { node, close } = stack.pop();
    if (close) {
      out += " ";
      continue;
    }
    if (node.nodeName === "#text") {
      out += node.value;
      continue;
    }
    if (node !== box && hasClass(node, "sr-only")) continue;
    const block = BLOCKS.has(node.tagName);
    if (block || node.tagName === "sup") out += " ";
    if (block) stack.push({ node, close: true });
    const children = node.childNodes ?? [];
    for (let i = children.length - 1; i >= 0; i -= 1) stack.push({ node: children[i], close: false });
  }
  return out;
}

/** 화면의 번호 목록이 내야 할 번호 낱말의 열. 항목의 번호는 그 항목의 글(안쪽 목록 포함)보다 먼저 온다. */
export function expectedOrdinals(box) {
  const out = [];
  const walk = (node) => {
    if (node.tagName === "ol") {
      let number = Number(attr(node, "start") ?? "1");
      for (const child of node.childNodes ?? []) {
        if (child.tagName === "li") {
          out.push(`${String(number)}.`);
          number += 1;
        }
        walk(child);
      }
      return;
    }
    for (const child of node.childNodes ?? []) walk(child);
  };
  walk(box);
  return out;
}

/**
 * `withOrdinals` 가 `without` 에 `ordinals` 의 낱말만 차례대로 끼운 열인가.
 * 아니면 어긋난 첫 자리를 낸다.
 */
export function onlyOrdinalsAdded(withOrdinals, without, ordinals) {
  let j = 0;
  let k = 0;
  for (let i = 0; i < withOrdinals.length; i += 1) {
    const word = withOrdinals[i];
    // 번호를 먼저 본다. 항목의 글이 번호와 같은 낱말로 시작해도 번호가 앞에 온다.
    if (k < ordinals.length && word === ordinals[k] && (j >= without.length || withOrdinals[i + 1] === without[j] || word !== without[j])) {
      k += 1;
      continue;
    }
    if (j < without.length && word === without[j]) {
      j += 1;
      continue;
    }
    return { ok: false, at: i, word, expectedOrdinal: ordinals[k] ?? null, expectedWord: without[j] ?? null };
  }
  if (j !== without.length || k !== ordinals.length) {
    return { ok: false, at: withOrdinals.length, word: null, expectedOrdinal: ordinals[k] ?? null, expectedWord: without[j] ?? null };
  }
  return { ok: true };
}

const sameList = (a, b) => a.length === b.length && a.every((value, index) => value === b[index]);

function firstDifference(a, b) {
  const length = Math.min(a.length, b.length);
  for (let i = 0; i < length; i += 1) {
    if (a[i] !== b[i]) return { at: i, shown: a.slice(Math.max(0, i - 2), i + 3), plain: b.slice(Math.max(0, i - 2), i + 3) };
  }
  return { at: length, shown: a.slice(Math.max(0, length - 2), length + 3), plain: b.slice(Math.max(0, length - 2), length + 3) };
}

function selfTest() {
  const wrong = [];
  const same = (got, want, label) => {
    if (JSON.stringify(got) !== JSON.stringify(want)) wrong.push({ label, got, want });
  };
  const boxOf = (html) =>
    findOne(parseFragment(html), (node) => node.tagName === "div" && attr(node, "data-answer") === "markdown");

  // 양성 대조 1: 표의 칸이 붙은 글은 화면의 낱말 열과 다르고, 띄운 글은 같다.
  const table = boxOf('<div data-answer="markdown"><div class="tbl"><table><thead><tr><th>가</th><th>나</th></tr></thead><tbody><tr><td>다</td><td>라</td></tr></tbody></table></div></div>');
  same(words(shownText(table)), ["가", "나", "다", "라"], "표의 칸마다 낱말이 끊긴다");
  same(sameList(words(shownText(table)), words("가나다라")), false, "칸이 붙은 글은 화면과 다르다");
  same(sameList(words(shownText(table)), words("가\n나\n다\n라")), true, "칸을 띄운 글은 화면과 같다");
  // 양성 대조 2: 목록 항목이 붙은 글도 가려낸다.
  const list = boxOf('<div data-answer="markdown"><ul><li>가</li><li>나</li></ul><p>다</p></div>');
  same(sameList(words(shownText(list)), words("가나 다")), false, "항목이 붙은 글은 화면과 다르다");
  same(sameList(words(shownText(list)), words("가 나 다")), true, "항목을 띄운 글은 화면과 같다");
  // 위첨자 번호는 앞만 띄우고, `.sr-only` 는 뺀다.
  const cite = boxOf('<div data-answer="markdown"><p>있습니다<sup data-cite="">1</sup>. <a href="https://a.example/">링크<span class="sr-only">(새 탭에서 열림)</span></a></p></div>');
  same(words(shownText(cite)), ["있습니다", "1.", "링크"], "위첨자 번호의 앞을 띄우고 숨긴 글을 뺀다");
  // 줄 안 요소는 낱말을 끊지 않는다.
  const inline = boxOf('<div data-answer="markdown"><p>가<strong>나</strong>다<br>\n라</p></div>');
  same(words(shownText(inline)), ["가나다", "라"], "줄 안 요소는 끊지 않고 br 은 끊는다");
  // 번호의 열: 시작 번호와 겹친 목록.
  const ordered = boxOf('<div data-answer="markdown"><ol start="3"><li>가<ol><li>안</li><li>쪽</li></ol></li><li>나</li></ol></div>');
  same(expectedOrdinals(ordered), ["3.", "1.", "2.", "4."], "번호는 항목의 글보다 먼저 오고 안쪽 목록은 1 부터다");
  // 양성 대조 3: 번호가 빠지거나 틀리면 가려낸다.
  same(onlyOrdinalsAdded(["3.", "가", "1.", "안", "2.", "쪽", "4.", "나"], ["가", "안", "쪽", "나"], ["3.", "1.", "2.", "4."]).ok, true, "번호만 더한 열이다");
  same(onlyOrdinalsAdded(["가", "안", "쪽", "나"], ["가", "안", "쪽", "나"], ["3.", "1.", "2.", "4."]).ok, false, "번호가 빠진 열을 가려낸다");
  same(onlyOrdinalsAdded(["1.", "가", "2.", "나"], ["가", "나"], ["3.", "4."]).ok, false, "시작 번호가 틀린 열을 가려낸다");
  same(onlyOrdinalsAdded(["1.", "가", "덤", "2.", "나"], ["가", "나"], ["1.", "2."]).ok, false, "번호가 아닌 낱말이 더해진 열을 가려낸다");
  same(onlyOrdinalsAdded(["1.", "1.", "가"], ["1.", "가"], ["1."]).ok, true, "항목의 글이 번호와 같은 낱말로 시작해도 맞춘다");
  return wrong;
}

async function main() {
  const wrong = selfTest();
  if (wrong.length > 0) {
    console.error("판정 함수의 자가 시험이 틀렸다", JSON.stringify(wrong, null, 2));
    process.exit(2);
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

  const inputs = [];
  const seen = new Set();
  const add = (group, id, text) => {
    const key = `${group}/${id}`;
    if (seen.has(key)) return;
    seen.add(key);
    inputs.push({ group, id, text });
  };
  for (const item of CASES) add("기존 52", item.id, item.input);
  for (const group of GROUPS) for (const item of group.cases) add(group.name, item.id, item.input);
  for (const [name, text] of Object.entries(SCREEN_INPUTS)) add("화면 파일", name, text);
  for (const [name, make] of Object.entries(STRESS_INPUTS)) add("병적인 입력", name, make());
  for (const item of OWN_CASES) add("글자만의 갈래", item.id, item.text);

  const notMeasured = [];
  const rows = [];
  const diverged = [];
  const situations = { cells: 0, ordered: 0, orderedFromOther: 0, nestedList: 0, cite: 0, image: 0, br: 0, pre: 0, fallback: 0 };
  const screens = [];
  const allFailed = (failed) => failed.shown && failed.plain && failed.plainWithoutOrdinals;
  const noneFailed = (failed) => !failed.shown && !failed.plain && !failed.plainWithoutOrdinals;

  for (const input of inputs) {
    const where = { group: input.group, id: input.id };
    let both;
    try {
      both = entry.renderBoth(input.text);
    } catch (error) {
      notMeasured.push({ ...where, reason: `그리다 던졌다: ${String(error).slice(0, 120)}` });
      continue;
    }
    const shownRoot = findOne(parseFragment(both.shown), (node) => node.tagName === "div" && attr(node, "data-probe") === "shown");
    const plainRoot = findOne(parseFragment(both.plain), (node) => node.tagName === "p" && attr(node, "data-probe") === "plain");
    const bareRoot = findOne(parseFragment(both.plainWithoutOrdinals), (node) => node.tagName === "p" && attr(node, "data-probe") === "plain");
    if (shownRoot === null || plainRoot === null || bareRoot === null) {
      notMeasured.push({ ...where, reason: "표지(data-probe)가 없다" });
      continue;
    }
    const elementsInPlain = countAll(plainRoot, (node) => node !== plainRoot && node.tagName !== undefined);
    const elementsInBare = countAll(bareRoot, (node) => node !== bareRoot && node.tagName !== undefined);
    const plainTextValue = rawText(plainRoot);
    const bareTextValue = rawText(bareRoot);
    const row = { ...where, bytes: Buffer.byteLength(input.text), noElements: elementsInPlain === 0 && elementsInBare === 0 };

    if (!allFailed(both.failed) && !noneFailed(both.failed)) {
      // 세 갈래 가운데 일부만 물러섰다. 가드가 없는 시제품의 측정 결과이고 어긋남과 따로 센다.
      diverged.push({
        ...where,
        bytes: row.bytes,
        failed: both.failed,
        errors: both.errors,
        // 물러선 글자만의 갈래는 원문을 그대로 낸다(화면의 갈래가 그린 글과 달라진다).
        plainIsSource: both.failed.plain ? plainTextValue === input.text : null,
        bareIsSource: both.failed.plainWithoutOrdinals ? bareTextValue === input.text : null,
      });
      continue;
    }

    if (allFailed(both.failed)) {
      // 세 갈래가 함께 원문으로 물러섰다. 세 글이 모두 원문과 글자 그대로 같아야 한다.
      const raw = findOne(shownRoot, (node) => node.tagName === "p" && attr(node, "data-answer") === "raw");
      if (raw === null) {
        notMeasured.push({ ...where, reason: "물러섰다는데 원문의 문단(data-answer=raw)이 없다" });
        continue;
      }
      situations.fallback += 1;
      row.fallback = true;
      row.errors = both.errors;
      row.shownIsSource = rawText(raw) === input.text;
      row.plainIsSource = plainTextValue === input.text && bareTextValue === input.text;
      row.ok = row.noElements && row.shownIsSource && row.plainIsSource;
      rows.push(row);
      continue;
    }

    const box = findOne(shownRoot, (node) => node.tagName === "div" && attr(node, "data-answer") === "markdown");
    if (box === null) {
      notMeasured.push({ ...where, reason: "답의 칸이 없다" });
      continue;
    }
    const has = (test) => countAll(box, test) > 0;
    if (has((node) => node.tagName === "tr" && (node.childNodes ?? []).filter((c) => c.tagName === "th" || c.tagName === "td").length >= 2)) situations.cells += 1;
    if (has((node) => node.tagName === "ol")) situations.ordered += 1;
    if (has((node) => node.tagName === "ol" && attr(node, "start") !== undefined && attr(node, "start") !== "1")) situations.orderedFromOther += 1;
    if (has((node) => node.tagName === "li" && (node.childNodes ?? []).some((c) => c.tagName === "ul" || c.tagName === "ol"))) situations.nestedList += 1;
    if (has((node) => node.tagName === "sup")) situations.cite += 1;
    if (has((node) => hasClass(node, "img-alt"))) situations.image += 1;
    if (has((node) => node.tagName === "br")) situations.br += 1;
    if (has((node) => node.tagName === "pre")) situations.pre += 1;

    const shownWords = words(shownText(box));
    const bareWords = words(bareTextValue);
    const plainWords = words(plainTextValue);
    const ordinals = expectedOrdinals(box);
    row.fallback = false;
    row.words = shownWords.length;
    row.ordinals = ordinals.length;
    row.sameWords = sameList(shownWords, bareWords);
    if (!row.sameWords) row.difference = firstDifference(shownWords, bareWords);
    const added = onlyOrdinalsAdded(plainWords, bareWords, ordinals);
    row.ordinalsOk = added.ok;
    if (!added.ok) row.ordinalDifference = added;
    row.ok = row.noElements && row.sameWords && row.ordinalsOk;
    rows.push(row);
    if (input.group === "화면 파일" || input.group === "글자만의 갈래") screens.push({ ...where, plain: plainTextValue });
  }

  for (const [name, count] of Object.entries(situations)) {
    if (count === 0) notMeasured.push({ group: "(상황)", id: name, reason: "이 상황이 든 입력이 하나도 없다" });
  }

  // 깊이 가드를 켠 묶음. 모든 입력과 가드의 사례를 그려, 세 갈래가 함께 물러서거나 함께 그리는지 본다.
  const guard = { limit: entry.GUARD_DEPTH, inputs: 0, drawn: 0, tooDeep: 0, otherError: 0, diverged: [], unexpected: [], changed: [], cases: [] };
  const guardInputs = [...inputs.map((input) => ({ ...input, expect: null })), ...GUARD_CASES.map((item) => ({ group: "가드의 사례", id: item.id, text: item.text, expect: item.expect }))];
  for (const input of guardInputs) {
    const where = { group: input.group, id: input.id };
    let guarded;
    try {
      guarded = entry.renderBothGuarded(input.text);
    } catch (error) {
      notMeasured.push({ ...where, reason: `가드를 켠 묶음이 그리다 던졌다: ${String(error).slice(0, 120)}` });
      continue;
    }
    const shownRoot = findOne(parseFragment(guarded.shown), (node) => node.tagName === "div" && attr(node, "data-probe") === "shown");
    const plainRoot = findOne(parseFragment(guarded.plain), (node) => node.tagName === "p" && attr(node, "data-probe") === "plain");
    if (shownRoot === null || plainRoot === null) {
      notMeasured.push({ ...where, reason: "가드를 켠 묶음에 표지(data-probe)가 없다" });
      continue;
    }
    guard.inputs += 1;
    const names = [guarded.errors.shown, guarded.errors.plain, guarded.errors.plainWithoutOrdinals];
    let outcome;
    if (noneFailed(guarded.failed)) {
      if (findOne(shownRoot, (node) => node.tagName === "div" && attr(node, "data-answer") === "markdown") === null) {
        notMeasured.push({ ...where, reason: "가드를 켠 묶음이 그렸다는데 답의 칸이 없다" });
        continue;
      }
      outcome = "drawn";
      guard.drawn += 1;
    } else if (allFailed(guarded.failed)) {
      const sourceShown = rawText(findOne(shownRoot, (node) => node.tagName === "p" && attr(node, "data-answer") === "raw") ?? { childNodes: [] }) === input.text;
      const sourcePlain = rawText(plainRoot) === input.text;
      if (names.every((name) => name === TOO_DEEP)) {
        outcome = "too-deep";
        guard.tooDeep += 1;
      } else {
        // 가드보다 먼저 파서가 던진 입력(`>` 20,000겹) 등. 오류의 이름을 적는다.
        outcome = `other:${names.join(",")}`;
        guard.otherError += 1;
      }
      if (!sourceShown || !sourcePlain) guard.unexpected.push({ ...where, outcome, why: "물러선 글이 원문과 다르다", sourceShown, sourcePlain });
    } else {
      outcome = "diverged";
      guard.diverged.push({ ...where, failed: guarded.failed, errors: guarded.errors });
    }
    if (input.expect !== null) {
      guard.cases.push({ id: input.id, expect: input.expect, outcome, ok: outcome === input.expect });
      if (outcome !== input.expect) guard.unexpected.push({ ...where, outcome, why: `기대는 ${input.expect}` });
      continue;
    }
    // 가드를 켜도 한도 이하의 입력은 가드 없는 묶음과 같은 글을 내야 한다(가드가 그리는 모양을 바꾸지 않는다).
    if (outcome === "drawn") {
      const plain = entry.renderBoth(input.text);
      if (noneFailed(plain.failed) && (plain.shown !== guarded.shown || plain.plain !== guarded.plain)) guard.changed.push(where);
    }
  }
  if (guard.tooDeep === 0) notMeasured.push({ group: "(가드)", id: "too-deep", reason: `${TOO_DEEP} 가 한 번도 나지 않았다` });
  if (guard.cases.filter((item) => item.expect === "drawn" && item.outcome === "drawn").length === 0) {
    notMeasured.push({ group: "(가드)", id: "drawn", reason: "한도 이하의 사례가 하나도 그려지지 않았다" });
  }

  const mismatched = rows.filter((row) => !row.ok);
  const summary = {
    probe: "plaintext",
    node: process.version,
    inputs: inputs.length,
    measured: rows.length + diverged.length,
    notMeasured,
    situations,
    ok: rows.length - mismatched.length,
    mismatched,
    diverged,
    guard,
    rows,
    screens,
  };
  writeFileSync(join(OUT, "summary.json"), `${JSON.stringify(summary, null, 2)}\n`);

  const report = [];
  report.push(`글자만 내는 갈래 (Node ${process.version})`);
  report.push(`입력 ${String(inputs.length)}, 측정 ${String(summary.measured)}, 측정 아님 ${String(notMeasured.length)}, 맞음 ${String(summary.ok)}, 어긋남 ${String(mismatched.length)}, 갈린 입력 ${String(diverged.length)}`);
  report.push(`상황이 든 입력의 수: ${JSON.stringify(situations)}`);
  report.push("");
  report.push("== 어긋난 입력 ==");
  for (const row of mismatched) report.push(`  ${JSON.stringify(row)}`);
  report.push("");
  report.push("== 갈린 입력(가드 없음. 세 갈래 가운데 일부만 물러섰다) ==");
  for (const row of diverged) report.push(`  ${JSON.stringify(row)}`);
  report.push("");
  report.push(`== 깊이 가드(한도 ${String(guard.limit)}겹) ==`);
  report.push(`  입력 ${String(guard.inputs)}, 세 갈래 모두 그림 ${String(guard.drawn)}, 세 갈래 모두 ${TOO_DEEP} ${String(guard.tooDeep)}, 다른 오류로 함께 물러섬 ${String(guard.otherError)}, 갈린 입력 ${String(guard.diverged.length)}, 기대와 다름 ${String(guard.unexpected.length)}, 가드 없는 묶음과 글이 다름 ${String(guard.changed.length)}`);
  for (const item of guard.cases) report.push(`  ${item.ok ? "맞음" : "다름"} ${item.id}: 기대 ${item.expect}, 결과 ${item.outcome}`);
  for (const item of guard.diverged) report.push(`  갈림 ${JSON.stringify(item)}`);
  for (const item of guard.unexpected) report.push(`  기대와 다름 ${JSON.stringify(item)}`);
  for (const item of guard.changed) report.push(`  글이 다름 ${JSON.stringify(item)}`);
  report.push("");
  report.push("== 측정이 아닌 회차 ==");
  for (const item of notMeasured) report.push(`  ${JSON.stringify(item)}`);
  report.push("");
  report.push("== 글자만의 글 (화면 파일의 입력과 이 프로브만의 입력) ==");
  for (const item of screens) {
    report.push(`-- ${item.group}/${item.id} --`);
    report.push(item.plain);
    report.push("");
  }
  writeFileSync(join(OUT, "report.txt"), `${report.join("\n")}\n`);

  console.log(
    JSON.stringify({
      probe: "plaintext",
      inputs: inputs.length,
      measured: summary.measured,
      notMeasured: notMeasured.length,
      situations,
      ok: summary.ok,
      mismatched: mismatched.map((row) => `${row.group}/${row.id}`),
      diverged: diverged.map((row) => `${row.group}/${row.id}`),
      guard: {
        limit: guard.limit,
        inputs: guard.inputs,
        drawn: guard.drawn,
        tooDeep: guard.tooDeep,
        otherError: guard.otherError,
        diverged: guard.diverged.map((row) => `${row.group}/${row.id}`),
        unexpected: guard.unexpected.map((row) => `${row.group}/${row.id}`),
        changed: guard.changed.map((row) => `${row.group}/${row.id}`),
        cases: guard.cases.filter((item) => !item.ok).map((item) => item.id),
      },
    }),
  );
  process.exit(notMeasured.length > 0 ? 1 : 0);
}

await main();
