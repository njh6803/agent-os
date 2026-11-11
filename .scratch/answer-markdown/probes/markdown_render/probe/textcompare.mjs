// 글자 비교 프로브(2026-11-11). 위젯의 실제 모델 e2e(tests/test_widget_llm.py 183~188줄)는 화면의 글과 트레이스의 출력을
// 글자 그대로 견준다. 답을 마크다운으로 그리면 둘이 같지 않게 되므로, 대신 쓸 규칙 하나를 모든 입력에 대 본다.
//
// 규칙(후보): 화면의 글(`.sr-only` 를 뺀 textContent)과 원문에서 유니코드 글자(L)와 숫자(N)만 남긴 뒤, 화면 쪽이 원문
// 쪽의 부분열(차례를 지킨 일부)이어야 한다.
//
// 돌리기: node probe/textcompare.mjs
// 산출물: out/textcompare/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 입력: 기존 52가지(cases.mjs), 모양 프로브의 사례 전부(shape-cases.mjs 의 GROUPS)와 화면 파일의 입력 다섯(SCREEN_INPUTS),
// 병적인 입력 열넷(inputs.mjs). 합친 시제품(shape-entry.tsx 의 `combined` 갈래)으로 그린다. 그리다 스택이 넘쳐
// (`RangeError`) 던진 입력은 시제품이 원문을 그대로 보이는 것(실패 때의 모양)으로 치고 `fallback` 으로 적는다.
//
// 내는 것: 입력마다 부분열인지, 길이 비율(화면 ÷ 원문, 걸러 낸 글자 수), 부분열이 아닌 입력과 그 까닭, 비율이 가장 낮은
// 다섯. 그리고 다른 입력의 화면 글을 바꿔 넣었을 때 규칙이 거르는지(모든 짝).
//
// 측정이 아닌 회차(.claude/rules/probes.md). 하나라도 있으면 종료 코드 1.
// - 그렸는데 답의 칸(`div[data-answer="markdown"]`)이 없는 입력.
// - 그리다 `RangeError` 가 아닌 예외를 던진 입력. 깊은 겹침의 스택 넘침이 아니면 변환의 버그일 수 있어, 원문으로
//   물러선 것(부분열)으로 세지 않는다(2026-11-11 PR 직전 리뷰가 짚어 더했다. 그 전 판은 예외의 종류를 가리지 않았다).
// - 양성 대조: 화면 파일의 입력 다섯은 글이 길고 서로 다르다. 그 스무 짝(다른 입력의 화면 글을 넣은 것)이 모두
//   "부분열이 아니다"여야 한다. 하나라도 부분열이면 규칙이 바꿔치기를 거르지 못한 것이라 위의 "부분열이다"가 뜻이 없다.
// - 걸러 내기 자가 시험이 틀리면 종료 코드 2.
import { mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { parseFragment } from "parse5";
import { CASES } from "./cases.mjs";
import { STRESS_INPUTS } from "./inputs.mjs";
import { GROUPS, SCREEN_INPUTS } from "./shape-cases.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "textcompare");
const BUNDLE = join(ROOT, "out", "build", "textcompare-entry.cjs");

/** 유니코드 글자(L)와 숫자(N)만 남긴 코드 포인트의 배열. */
export function lettersAndDigits(value) {
  return [...value].filter((char) => /[\p{L}\p{N}]/u.test(char));
}

/** `needle` 이 `hay` 의 부분열인가. 아니면 맞추지 못한 첫 자리를 낸다. */
export function subsequence(needle, hay) {
  let at = 0;
  for (let i = 0; i < needle.length; i += 1) {
    while (at < hay.length && hay[at] !== needle[i]) at += 1;
    if (at === hay.length) return { ok: false, failedAt: i };
    at += 1;
  }
  return { ok: true, failedAt: null };
}

// 이 프로브만의 입력. 부분열이 아니게 되는 까닭 가운데 다른 입력들에 없는 것(문자 참조, 본문 앞에 온 각주)을 일부러
// 넣었다. 기대(`expect`: 부분열인가, `why`: 아니라면 까닭의 앞머리)는 결과를 보기 전에 적었다(2026-11-11).
const OWN_CASES = [
  { id: "t01-numeric-reference-letter", text: "&#44032;격은 100원입니다", expect: false, why: "문자 참조" },
  { id: "t02-named-reference-letter", text: "caf&eacute;에서 만납니다", expect: false, why: "문자 참조" },
  // t03 의 기대는 한 번 바꿨다. 첫 실행(각주를 remark-gfm 그대로 둔 시제품)에서는 미리 적은 대로 부분열이 아니었다
  // (까닭: 각주가 `Footnotes` 제목을 더하고 각주의 글을 끝으로 옮긴다). 그 뒤 시제품에 각주 문법을 글자로 되돌리는 변환
  // (footnotes.ts)을 넣었고, 그 변환은 정의를 놓인 자리에 두므로 다시 돌리기 전에 기대를 부분열로 고쳤다.
  { id: "t03-footnote-before-body", text: "첫 문장입니다[^1].\n\n[^1]: 각주의 글\n\n둘째 문단입니다.", expect: true },
  { id: "t04-footnote-at-end", text: "첫 문장입니다[^1].\n\n둘째 문단입니다.\n\n[^1]: 각주의 글", expect: true },
  { id: "t05-reference-symbols", text: "A &amp; B &lt; C &#42; D", expect: true },
  { id: "t06-task-list", text: "- [x] 한 일\n- [ ] 할 일", expect: true },
  { id: "t07-reference-link", text: "[법령][a]을 봅니다.\n\n[a]: https://www.law.go.kr/", expect: true },
];

const hasClass = (node, name) => (node.attrs ?? []).some((a) => a.name === "class" && a.value.split(/\s+/).includes(name));

/** 요소 아래의 글자를 이어 붙인다. `skip` 이 참인 요소는 그 아래까지 뺀다. */
function textOf(node, skip) {
  let out = "";
  const stack = [node];
  while (stack.length > 0) {
    const current = stack.pop();
    if (current.nodeName === "#text") {
      out += current.value;
      continue;
    }
    if (current !== node && skip(current)) continue;
    const children = current.childNodes ?? [];
    for (let i = children.length - 1; i >= 0; i -= 1) stack.push(children[i]);
  }
  return out;
}

function findBox(html) {
  const stack = [parseFragment(html)];
  while (stack.length > 0) {
    const node = stack.pop();
    if (node.tagName === "div" && (node.attrs ?? []).some((a) => a.name === "data-answer" && a.value === "markdown")) return node;
    const children = node.childNodes ?? [];
    for (let i = children.length - 1; i >= 0; i -= 1) stack.push(children[i]);
  }
  return null;
}

function selfTest() {
  const wrong = [];
  const same = (got, want, label) => {
    if (JSON.stringify(got) !== JSON.stringify(want)) wrong.push({ label, got, want });
  };
  same(lettersAndDigits("가-1 a!\n２[3]"), ["가", "1", "a", "２", "3"], "글자와 숫자만 남긴다");
  same(subsequence([..."ac"], [..."abc"]).ok, true, "차례를 지킨 일부는 부분열이다");
  same(subsequence([..."ca"], [..."abc"]).ok, false, "차례가 바뀌면 부분열이 아니다");
  same(subsequence([..."abd"], [..."abc"]), { ok: false, failedAt: 2 }, "없는 글자의 자리를 낸다");
  same(subsequence([], [..."abc"]).ok, true, "빈 글은 부분열이다");
  const box = findBox('<div data-probe="x"><div data-answer="markdown"><p>가<a>나<span class="sr-only">(새 탭에서 열림)</span></a></p></div></div>');
  same(textOf(box, (node) => hasClass(node, "sr-only")), "가나", "sr-only 아래의 글을 뺀다");
  return wrong;
}

/** 부분열이 아닌 까닭을 가른다. 순서대로 대 보고 처음 맞는 것을 낸다. */
function reasonOf({ source, html, box, screenChars, sourceChars }) {
  // 1. 이미지 자리의 표지("이미지: ", "이미지")가 원문에 없는 글자다. 그 표지를 빼면 부분열이 되는지 본다.
  const withoutImages = lettersAndDigits(textOf(box, (node) => hasClass(node, "sr-only") || hasClass(node, "img-alt")));
  const imageAlts = [];
  const stack = [box];
  while (stack.length > 0) {
    const node = stack.pop();
    if (hasClass(node, "img-alt")) imageAlts.push(textOf(node, () => false));
    for (const child of node.childNodes ?? []) stack.push(child);
  }
  if (imageAlts.length > 0) {
    // 표지를 뗀 대체 글은 원문에 있어야 한다. 이미지 칸을 통째로 뺀 글이 부분열이면 까닭은 표지다.
    if (subsequence(withoutImages, sourceChars).ok) return "이미지 자리의 표지(`이미지: `)가 원문에 없는 글자다";
  }
  // 2. GFM 각주가 영어 제목(Footnotes)을 더한다.
  if (html.includes('id="footnote-label"')) return "각주가 `Footnotes` 제목과 돌아가기 표시를 더하고 각주 글을 끝으로 옮긴다";
  // 3. 문자 참조(`&#44032;`, `&eacute;`)가 풀려 원문에 없는 글자가 선다.
  if (/&(#\d+|#x[0-9a-f]+|[a-z][a-z0-9]*);/i.test(source)) return "문자 참조가 풀려 원문에 없는 글자가 선다";
  return "가르지 못했다";
}

async function main() {
  const wrong = selfTest();
  if (wrong.length > 0) {
    console.error("걸러 내기 자가 시험이 틀렸다", JSON.stringify(wrong, null, 2));
    process.exit(2);
  }
  mkdirSync(dirname(BUNDLE), { recursive: true });
  mkdirSync(OUT, { recursive: true });
  await build({
    entryPoints: [join(ROOT, "probe", "shape-entry.tsx")],
    outfile: BUNDLE,
    bundle: true,
    platform: "node",
    format: "cjs",
    jsx: "automatic",
    define: { "process.env.NODE_ENV": '"production"' },
    logLevel: "warning",
  });
  const entry = createRequire(import.meta.url)(BUNDLE);

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
  for (const item of OWN_CASES) add("글자 비교만", item.id, item.text);

  const notMeasured = [];
  const rows = [];
  const fallbackRows = [];
  for (const input of inputs) {
    const sourceChars = lettersAndDigits(input.text);
    let html = null;
    let threw = null;
    let stackOverflow = false;
    try {
      html = entry.render("combined", input.id, input.text).html;
    } catch (error) {
      threw = String(error).slice(0, 80);
      stackOverflow = error instanceof Error && error.name === "RangeError";
    }
    if (html === null && !stackOverflow) {
      notMeasured.push({ group: input.group, id: input.id, reason: "그리다 스택 넘침(RangeError)이 아닌 예외를 던졌다", threw });
      continue;
    }
    if (html === null) {
      // 스택이 넘쳐 던졌다. 이 갈래(`View`)는 실패를 받지 않아 화면에 무엇이 그려지는지 이 프로브는 보지 못했다.
      // 원문이 보인다고 가정해 부분열로 세지 않고, 던졌다는 것만 적어 집계(부분열의 수, 바꿔치기 짝)에서 뺀다.
      fallbackRows.push({ group: input.group, id: input.id, threw });
      continue;
    }
    const box = findBox(html);
    if (box === null) {
      notMeasured.push({ group: input.group, id: input.id, reason: "답의 칸이 없다" });
      continue;
    }
    const screenChars = lettersAndDigits(textOf(box, (node) => hasClass(node, "sr-only")));
    const verdict = subsequence(screenChars, sourceChars);
    const row = {
      ...input,
      fallback: false,
      threw: null,
      sourceLength: sourceChars.length,
      screenLength: screenChars.length,
      ratio: sourceChars.length === 0 ? null : Math.round((screenChars.length / sourceChars.length) * 1000) / 1000,
      subsequence: verdict.ok,
      reason: null,
      screenChars,
    };
    if (!verdict.ok) {
      row.reason = reasonOf({ source: input.text, html, box, screenChars, sourceChars });
      row.failedAt = { index: verdict.failedAt, around: screenChars.slice(Math.max(0, verdict.failedAt - 8), verdict.failedAt + 8).join("") };
    }
    // 규칙의 변형: 이미지 자리(`.img-alt`)도 화면의 글에서 뺀다.
    row.subsequenceWithoutImages = subsequence(
      lettersAndDigits(textOf(box, (node) => hasClass(node, "sr-only") || hasClass(node, "img-alt"))),
      sourceChars,
    ).ok;
    rows.push(row);
  }
  // 이 프로브만의 입력은 미리 적은 기대와 견준다. 부분열이 아니라고 기대한 것은 까닭도 맞아야 한다.
  for (const item of OWN_CASES) {
    const row = rows.find((candidate) => candidate.group === "글자 비교만" && candidate.id === item.id);
    if (row === undefined) continue;
    const sameVerdict = row.subsequence === item.expect;
    const sameWhy = item.expect || (row.reason ?? "").startsWith(item.why);
    if (!sameVerdict || !sameWhy) {
      notMeasured.push({ group: "글자 비교만", id: item.id, reason: "미리 적은 기대와 다르다", expect: item.expect, why: item.why ?? null, got: row.subsequence, gotReason: row.reason });
    }
  }

  // 양성 대조: 화면 파일의 입력 다섯끼리 화면 글을 바꿔 넣는다. 스무 짝이 모두 걸려야 한다.
  const screens = rows.filter((row) => row.group === "화면 파일");
  const control = [];
  for (const target of screens) {
    for (const other of screens) {
      if (target === other) continue;
      const caught = !subsequence(other.screenChars, lettersAndDigits(target.text)).ok;
      control.push({ source: target.id, screenFrom: other.id, caught });
    }
  }
  if (screens.length !== 5 || control.some((pair) => !pair.caught)) {
    notMeasured.push({ reason: "양성 대조가 걸리지 않았다(화면 파일의 입력끼리 바꿔 넣은 글이 부분열이다)", control: control.filter((pair) => !pair.caught), screens: screens.length });
  }

  // 모든 짝: 다른 입력의 화면 글을 넣었을 때 규칙이 거르는 비율과, 거르지 못하는 짝의 모양.
  let pairs = 0;
  let caught = 0;
  const slipped = [];
  const slippedByScreenLength = {};
  const screenKey = new Map(rows.map((row) => [row, row.screenChars.join("")]));
  for (const target of rows) {
    const sourceChars = lettersAndDigits(target.text);
    for (const other of rows) {
      // 화면 글이 같은 입력끼리는 바꿔치기가 아니다.
      if (target === other || screenKey.get(other) === screenKey.get(target)) continue;
      pairs += 1;
      if (!subsequence(other.screenChars, sourceChars).ok) {
        caught += 1;
        continue;
      }
      const bucket = other.screenLength === 0 ? "0" : other.screenLength <= 5 ? "1~5" : other.screenLength <= 20 ? "6~20" : "21 이상";
      slippedByScreenLength[bucket] = (slippedByScreenLength[bucket] ?? 0) + 1;
      if (other.screenLength > 20 && slipped.length < 20) {
        slipped.push({ source: `${target.group}/${target.id}`, screenFrom: `${other.group}/${other.id}`, screenLength: other.screenLength, sourceLength: sourceChars.length });
      }
    }
  }

  const failing = rows.filter((row) => !row.subsequence);
  const byReason = {};
  for (const row of failing) byReason[row.reason] = (byReason[row.reason] ?? 0) + 1;
  const withRatio = rows.filter((row) => row.ratio !== null && !row.fallback);
  const lowest = [...withRatio].sort((a, b) => a.ratio - b.ratio).slice(0, 5);
  const ratios = withRatio.map((row) => row.ratio).sort((a, b) => a - b);
  const strip = ({ screenChars, text, ...rest }) => ({ ...rest, input: text.length > 200 ? `${text.slice(0, 200)}…` : text, screen: screenChars.join("").slice(0, 200) });
  const summary = {
    probe: "textcompare",
    rule: "화면의 글(.sr-only 제외)과 원문에서 유니코드 L·N 만 남긴 뒤 화면이 원문의 부분열",
    inputs: rows.length,
    byGroup: Object.fromEntries([...new Set(rows.map((row) => row.group))].map((group) => [group, rows.filter((row) => row.group === group).length])),
    subsequence: rows.length - failing.length,
    notSubsequence: failing.length,
    byReason,
    // 이미지 자리도 뺀 변형 규칙에서 부분열이 아닌 입력(던져서 원문을 보인 입력은 세지 않는다).
    notSubsequenceWithoutImages: rows.filter((row) => !row.fallback && row.subsequenceWithoutImages === false).map((row) => `${row.group}/${row.id}`),
    // 스택이 넘쳐 던진 입력. 화면을 보지 못해 위의 모든 집계(inputs, subsequence, 짝)에서 빠진다.
    fallbacks: fallbackRows.map((row) => `${row.group}/${row.id}`),
    inputsTotal: rows.length + fallbackRows.length,
    ratio: { counted: ratios.length, min: ratios[0], median: ratios[Math.floor(ratios.length / 2)], max: ratios.at(-1), equalOne: ratios.filter((r) => r === 1).length, emptyScreen: withRatio.filter((row) => row.screenLength === 0).length },
    lowestFive: lowest.map(strip),
    failing: failing.map(strip),
    control: { designated: control.length, designatedCaught: control.filter((pair) => pair.caught).length, allPairs: pairs, allCaught: caught, slippedByScreenLength, slippedLongExamples: slipped },
    notMeasured,
    rows: rows.map(strip),
  };
  writeFileSync(join(OUT, "summary.json"), JSON.stringify(summary, null, 2));
  const { rows: _rows, ...short } = summary;
  console.log(
    JSON.stringify({
      ...short,
      lowestFive: summary.lowestFive.map((row) => ({ id: `${row.group}/${row.id}`, ratio: row.ratio, input: row.input.slice(0, 60), screen: row.screen.slice(0, 40) })),
      failing: summary.failing.map((row) => ({ id: `${row.group}/${row.id}`, reason: row.reason, around: row.failedAt?.around, input: row.input.slice(0, 60) })),
      notMeasured: notMeasured.length,
    }),
  );
  if (notMeasured.length > 0) {
    console.error("측정이 아닌 회차", JSON.stringify(notMeasured, null, 2));
    process.exit(1);
  }
}

await main();
