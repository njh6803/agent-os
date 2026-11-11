// 모양 프로브. 명세가 정할 다섯 가지(한 줄 바꿈, 닫히지 않는 굵게, 숫자 사이 별표와 밑줄, 문장 끝 번호, 출처 덩이)의
// 후보를 같은 입력으로 그려 견주고, 합친 시제품이 목표 모양(화면 파일)을 내는지 본다.
//
// 돌리기: node probe/shape.mjs
// 산출물: out/shape/summary.json(회차 전부. 입력, 파서의 mdast, 변환 뒤 mdast, HTML, 판정),
//         out/shape/report.txt(사람이 읽는 표), 표준 출력의 마지막 줄(JSON 한 줄)
//
// 방식은 render.mjs 와 같다. 시제품 부품을 esbuild 로 묶어 `renderToStaticMarkup` 의 HTML 을 parse5 로 읽는다.
// 기대는 shape-cases.mjs 에 결과를 보기 전에 적었고, 견줄 글을 만드는 방식은 shape-html.mjs 에 있다.
//
// 재는 것
// 1. 갈래별 사례: 후보마다 목표 모양(want)과 같은지, 그 후보의 규칙대로(wantBy)인지. 어긋난 것은 측정 결과다(종료 코드 0).
// 2. 모든 회차에 제한 규칙(R1~R5, judge.mjs)을 건다. 시제품이 금지 요소나 위험한 주소를 내면 그 회차를 적는다.
// 3. (다)의 변환이 판정하지 못한 노드(`skipped`). 위치(오프셋)가 원문과 어긋나면 0 이 아니다.
// 4. 기존 입력 52가지(cases.mjs)를 합친 시제품으로 그린 결과. 기존 기대가 어긋나는 자리는 미리 적은 목록
//    (EXPECTED_MUST_FAILURES)과 견준다.
// 5. 화면 파일의 `div.md` 와 합친 시제품의 출력이 요소의 종류와 차례에서 같은지.
//
// 측정이 아닌 회차(.claude/rules/probes.md). 하나라도 있으면 종료 코드 1.
// - 그리다 던진 회차, 표지(`div[data-probe]`)나 답의 칸(`div[data-answer="markdown"]`)이 없는 회차.
// - 대조 갈래(변환 없는 base)가 기대와 다르게 나온 사례. `problem: true` 인데 base 가 이미 목표와 같으면 고칠 문제가
//   그 입력에서 나지 않은 것이고, `problem` 이 아닌데 base 가 목표와 다르면 파서에 대한 기대가 틀린 것이다. 어느 쪽이든
//   후보의 통과·실패가 재려던 것을 재지 못한다.
// - 화면 파일을 읽지 못했거나 그 안에서 `div.md` 를 찾지 못한 견줌.
// 판정기 자가 시험(judge.mjs 의 selfTest, 아래 normalizeSelfTest)이 틀리면 종료 코드 2.
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { parse } from "parse5";
import { CASES } from "./cases.mjs";
import { analyze, selfTest, violations } from "./judge.mjs";
import { EXPECTED_MUST_FAILURES, GROUPS, SCREEN_INPUTS, SCREENS } from "./shape-cases.mjs";
import { find, normalize, plainText, skeleton } from "./shape-html.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "shape");
const BUNDLE = join(ROOT, "out", "build", "shape-entry.cjs");
const DESIGN = join(ROOT, "..", "..", "design");

function normalizeSelfTest() {
  const samples = [
    // 블록 사이의 줄 끝 글자는 빠지고 센다.
    ['<div data-answer="markdown"><p>a</p>\n<p>b</p></div>', "<p>a</p><p>b</p>", 1],
    // 문단 안의 줄 끝 글자와 `<br>` 뒤의 줄 끝 글자는 남는다.
    ['<div data-answer="markdown"><p>a\nb<br/>\nc</p></div>', "<p>a\nb<br>\nc</p>", 0],
    // 빽빽한 목록의 항목 글 뒤, 겹친 목록 앞뒤의 줄 끝 글자는 빠진다.
    ['<div data-answer="markdown"><ul>\n<li>a\n<ul>\n<li>b</li>\n</ul>\n</li>\n</ul></div>', "<ul><li>a<ul><li>b</li></ul></li></ul>", 6],
    // 항목 안에서 줄 안 요소 사이의 줄 끝 글자는 남는다.
    ['<div data-answer="markdown"><ul>\n<li><strong>a</strong>\n<strong>b</strong></li>\n</ul></div>', "<ul><li><strong>a</strong>\n<strong>b</strong></li></ul>", 2],
    // 속성은 이름 차례로 쓴다.
    ['<div data-answer="markdown"><a target="_blank" href="https://a.example/?x=1&amp;y=2" rel="noopener noreferrer">x</a></div>', '<a href="https://a.example/?x=1&amp;y=2" rel="noopener noreferrer" target="_blank">x</a>', 0],
    // 코드 블록 안의 줄 끝 글자는 남는다.
    ['<div data-answer="markdown"><pre tabindex="0"><code>a\nb\n</code></pre></div>', '<pre tabindex="0"><code>a\nb\n</code></pre>', 0],
  ];
  const wrong = [];
  for (const [html, expected, newlines] of samples) {
    const got = normalize(html);
    if (got === null || got.html !== expected || got.structuralNewlines !== newlines) wrong.push({ html, expected, newlines, got });
  }
  if (normalize("<p>칸이 없다</p>") !== null) wrong.push({ html: "<p>칸이 없다</p>", expected: null });
  return wrong;
}

/** mdast 를 한 줄 글로 쓴다. 사례마다 파서가 무엇을 냈는지 보려는 것이다. */
function dump(node) {
  if (node === null || node === undefined) return "(없음)";
  if (node.type === "text") return JSON.stringify(node.value);
  let label = node.type;
  if (node.type === "heading") label += node.depth;
  if (node.type === "list") label += node.ordered ? `(ol${node.start !== null && node.start !== undefined && node.start !== 1 ? ` start=${node.start}` : ""}${node.spread ? " loose" : ""})` : `(ul${node.spread ? " loose" : ""})`;
  if (node.type === "link" || node.type === "image" || node.type === "definition") label += `<${node.url}>`;
  if (node.type === "linkReference" || node.type === "imageReference" || node.type === "footnoteReference" || node.type === "footnoteDefinition" || node.type === "definition") {
    label += `#${node.identifier}${node.referenceType === undefined ? "" : `:${node.referenceType}`}`;
  }
  if (node.type === "image") label += `alt=${JSON.stringify(node.alt)}`;
  if (node.data?.hName !== undefined) label += `→${node.data.hName}`;
  if (Array.isArray(node.children)) return `${label}[${node.children.map(dump).join(", ")}]`;
  if (typeof node.value === "string") return `${label}(${JSON.stringify(node.value)})`;
  return label;
}

async function main() {
  const wrongJudge = selfTest();
  const wrongNormalize = normalizeSelfTest();
  if (wrongJudge.length > 0 || wrongNormalize.length > 0) {
    console.error("판정기 자가 시험이 틀렸다", JSON.stringify({ wrongJudge, wrongNormalize }, null, 2));
    process.exit(2);
  }

  mkdirSync(dirname(BUNDLE), { recursive: true });
  await build({
    entryPoints: [join(ROOT, "probe", "shape-entry.tsx")],
    outfile: BUNDLE,
    bundle: true,
    platform: "node",
    format: "cjs",
    jsx: "automatic",
    define: { "process.env.NODE_ENV": '"development"' },
    logLevel: "warning",
  });
  const entry = createRequire(import.meta.url)(BUNDLE);

  rmSync(OUT, { recursive: true, force: true });
  mkdirSync(OUT, { recursive: true });

  const notMeasured = [];
  const originalError = console.error;

  /** 한 회차를 그린다. 측정이 아니면 null 을 돌려주고 까닭을 적는다. */
  function draw(where, variant, id, input) {
    if (!entry.VARIANTS.includes(variant)) {
      notMeasured.push({ ...where, variant, id, reason: "없는 갈래다" });
      return null;
    }
    const warnings = [];
    console.error = (...args) => warnings.push(args.map(String).join(" ").slice(0, 300));
    let rendered;
    try {
      rendered = entry.render(variant, id, input);
    } catch (error) {
      notMeasured.push({ ...where, variant, id, reason: `던졌다: ${String(error)}` });
      return null;
    } finally {
      console.error = originalError;
    }
    const marker = `<div data-probe="${id}">`;
    const normalized = rendered.html.includes(marker) ? normalize(rendered.html) : null;
    if (normalized === null) {
      notMeasured.push({ ...where, variant, id, reason: "표지나 답의 칸이 없다" });
      return null;
    }
    const analysis = analyze(rendered.html);
    return {
      raw: rendered.html,
      html: normalized.html,
      structuralNewlines: normalized.structuralNewlines,
      softNewlines: normalized.softNewlines,
      br: normalized.br,
      parsed: dump(rendered.parsed),
      final: dump(rendered.final),
      violations: violations(analysis),
      analysis,
      reactWarnings: warnings,
    };
  }

  // ── 1~3. 갈래별 사례 ──────────────────────────────────────────────────────────────────────────────────────────
  const groups = [];
  for (const group of GROUPS) {
    const variants = [...new Set([...(group.control === null ? [] : [group.control]), ...group.candidates])];
    const undo = new Set(group.undoBreaks ?? []);
    const rows = [];
    for (const item of group.cases) {
      const where = { group: group.name };
      const drawn = {};
      for (const variant of variants) drawn[variant] = draw(where, variant, item.id, item.input);
      const seen = (variant) => {
        const round = drawn[variant];
        if (round === null || round === undefined) return null;
        return undo.has(variant) ? round.html.replaceAll("<br>\n", "\n") : round.html;
      };
      const control = group.control === null ? null : seen(group.control);
      if (group.control !== null && control !== null && item.want !== null) {
        const controlMeets = control === item.want;
        if (item.problem === true && controlMeets) {
          notMeasured.push({ ...where, id: item.id, reason: "problem 사례인데 대조 갈래가 이미 목표와 같다(문제가 나지 않았다)" });
        }
        if (item.problem !== true && !controlMeets) {
          notMeasured.push({ ...where, id: item.id, reason: "대조 갈래가 목표와 다르다(파서에 대한 기대가 틀렸다)", control, want: item.want });
        }
      }
      const verdicts = {};
      for (const candidate of group.candidates) {
        const html = seen(candidate);
        if (html === null) continue;
        const byRule = item.wantBy?.[candidate];
        const twin = group.sameAs?.[candidate];
        verdicts[candidate] = {
          html,
          target: item.want === null ? null : html === item.want,
          rule: byRule === undefined ? null : html === byRule,
          sameAsControl: control === null ? null : html === control,
          sameAsTwin: twin === undefined ? null : html === seen(twin),
          violations: drawn[candidate].violations,
          final: drawn[candidate].final,
          structuralNewlines: drawn[candidate].structuralNewlines,
          softNewlines: drawn[candidate].softNewlines,
          br: drawn[candidate].br,
        };
      }
      const row = {
        id: item.id,
        note: item.note ?? null,
        revised: item.revised ?? null,
        input: item.input,
        want: item.want,
        wantBy: item.wantBy ?? null,
        problem: item.problem === true,
        control:
          group.control === null || drawn[group.control] === null
            ? null
            : {
                html: control,
                parsed: drawn[group.control].parsed,
                structuralNewlines: drawn[group.control].structuralNewlines,
                softNewlines: drawn[group.control].softNewlines,
                br: drawn[group.control].br,
              },
        verdicts,
      };
      if (group.name === "literal" || group.name === "interplay") {
        row.literal = {
          r2: entry.literalReport(item.input, "between-digits", "as-transform"),
          r1: entry.literalReport(item.input, "outer-digits", "as-transform"),
          // 원문에서 BOM 을 떼지 않고 넘긴 것. BOM 으로 시작하는 사례(d32)에서만 위와 갈려야 한다.
          r2RawSource: entry.literalReport(item.input, "between-digits", "raw"),
        };
      }
      rows.push(row);
    }
    groups.push({ name: group.name, title: group.title, control: group.control, candidates: group.candidates, rows });
  }

  // ── 4. 기존 입력 52가지를 합친 시제품으로 ─────────────────────────────────────────────────────────────────────
  const legacy = [];
  for (const item of CASES) {
    const round = draw({ group: "legacy-52" }, "combined", item.id, item.input);
    if (round === null) continue;
    legacy.push({
      id: item.id,
      input: item.input,
      html: round.html,
      violations: round.violations,
      mustFailures: item.must(round.analysis),
      watch: item.watch(round.analysis),
      reactWarnings: round.reactWarnings,
    });
  }
  const legacyFailed = legacy.filter((x) => x.mustFailures.length > 0).map((x) => x.id);
  const legacySummary = {
    rounds: legacy.length,
    withViolations: legacy.filter((x) => x.violations.length > 0).map((x) => x.id),
    withMustFailures: legacyFailed,
    unexpectedMustFailures: legacyFailed.filter((id) => !(id in EXPECTED_MUST_FAILURES)),
    expectedButPassed: Object.keys(EXPECTED_MUST_FAILURES).filter((id) => !legacyFailed.includes(id)),
    withReactWarnings: legacy.filter((x) => x.reactWarnings.length > 0).map((x) => x.id),
  };

  // ── 5. 화면 파일과 견주기 ─────────────────────────────────────────────────────────────────────────────────────
  const screens = [];
  for (const screen of SCREENS) {
    const where = { group: "screens", id: `${screen.file}#${screen.index}` };
    let boxes;
    try {
      const document = parse(readFileSync(join(DESIGN, screen.file), "utf8"));
      boxes = [];
      const collect = (node) => {
        if (node.tagName === "div" && (node.attrs ?? []).some((a) => a.name === "class" && a.value.split(/\s+/).includes("md"))) {
          boxes.push(node);
          return;
        }
        for (const child of node.childNodes ?? []) collect(child);
        if (node.content !== undefined) collect(node.content);
      };
      collect(document);
    } catch (error) {
      notMeasured.push({ ...where, reason: `화면 파일을 읽지 못했다: ${String(error)}` });
      continue;
    }
    const target = boxes[screen.index];
    if (target === undefined) {
      notMeasured.push({ ...where, reason: `화면 파일에서 div.md 를 찾지 못했다(찾은 수 ${boxes.length})` });
      continue;
    }
    const round = draw(where, "combined", screen.input, SCREEN_INPUTS[screen.input]);
    if (round === null) continue;
    const mine = find(parse(round.raw), (node) => (node.attrs ?? []).some((a) => a.name === "data-answer" && a.value === "markdown"));
    const wanted = { skeleton: skeleton(target), text: plainText(target) };
    const got = { skeleton: skeleton(mine), text: plainText(mine) };
    const spaceless = (value) => value.replace(/\s+/g, "");
    screens.push({
      screen: `${screen.file}#${screen.index}`,
      input: screen.input,
      sameSkeleton: wanted.skeleton === got.skeleton,
      // 첫 판은 공백을 하나로 줄인 글자를 견줬다(sameText). 첫 결과에서 그것이 세 화면에서 달랐고, 차이는 공백뿐이었다
      // (시제품은 `<br>` 뒤에 줄 끝 글자를 하나 두고 화면 파일은 두지 않는다. 화면 파일은 표의 행 사이에 줄 끝 글자를
      // 둔다). 그래서 공백을 모두 뺀 글자를 견주는 칸(sameTextIgnoringSpace)을 더했다. 두 칸을 다 낸다.
      sameText: wanted.text === got.text,
      sameTextIgnoringSpace: spaceless(wanted.text) === spaceless(got.text),
      wanted,
      got,
    });
  }

  // BOM 을 떼는 길이 실제로 지났다는 표지: BOM 으로 시작하는 사례에서, 원문을 그대로 넘긴 변환은 노드를 판정하지
  // 못하고(skipped) BOM 을 뗀 변환은 판정해야 한다. 그런 사례가 하나도 없으면 "위치가 맞다"는 BOM 을 재지 못한 것이다.
  const literalRows = groups.flatMap((group) => group.rows).filter((row) => row.literal !== undefined);
  const bomRows = literalRows.filter((row) => row.input.startsWith("﻿"));
  const bomExercised = bomRows.filter((row) => row.literal.r2RawSource.skipped > 0 && row.literal.r2.skipped === 0).map((row) => row.id);
  if (bomExercised.length === 0) {
    notMeasured.push({ group: "literal", reason: "BOM 으로 시작하는 사례에서 원문을 그대로 넘긴 변환과 BOM 을 뗀 변환이 갈리지 않았다", bomRows: bomRows.map((row) => ({ id: row.id, ...row.literal })) });
  }
  const rawDiffersElsewhere = literalRows
    .filter((row) => !row.input.startsWith("﻿") && JSON.stringify(row.literal.r2RawSource) !== JSON.stringify(row.literal.r2))
    .map((row) => row.id);
  if (rawDiffersElsewhere.length > 0) {
    notMeasured.push({ group: "literal", reason: "BOM 이 없는 사례에서 두 원문의 결과가 갈렸다", ids: rawDiffersElsewhere });
  }

  // ── 요약 ──────────────────────────────────────────────────────────────────────────────────────────────────────
  const summary = {};
  for (const group of groups) {
    summary[group.name] = {};
    for (const candidate of group.candidates) {
      const mine = group.rows.filter((row) => row.verdicts[candidate] !== undefined);
      const ids = (pick) => mine.filter((row) => pick(row.verdicts[candidate], row)).map((row) => row.id);
      summary[group.name][candidate] = {
        rounds: mine.length,
        targetPass: ids((v) => v.target === true).length,
        targetFail: ids((v) => v.target === false),
        fixed: ids((v, row) => row.problem && v.target === true).length,
        notFixed: ids((v, row) => row.problem && v.target === false),
        regressed: ids((v, row) => !row.problem && v.target === false),
        ruleFail: ids((v) => v.rule === false),
        differsFromTwin: ids((v) => v.sameAsTwin === false),
        withViolations: ids((v) => v.violations.length > 0),
      };
    }
  }
  const literalSkipped = groups
    .flatMap((group) => group.rows)
    .filter((row) => row.literal !== undefined && (row.literal.r2.skipped > 0 || row.literal.r1.skipped > 0))
    .map((row) => ({ id: row.id, ...row.literal }));

  writeFileSync(join(OUT, "summary.json"), JSON.stringify({ notMeasured, summary, literalSkipped, legacy: legacySummary, screens, groups, legacyRounds: legacy }, null, 2));
  writeFileSync(join(OUT, "report.txt"), report(groups, legacy, legacySummary, screens, notMeasured));

  console.log(
    JSON.stringify({
      probe: "shape",
      cases: Object.fromEntries(groups.map((group) => [group.name, group.rows.length])),
      notMeasured: notMeasured.length,
      summary,
      literalSkipped,
      legacy: legacySummary,
      bomExercised,
      screens: screens.map((s) => ({
        screen: s.screen,
        sameSkeleton: s.sameSkeleton,
        sameText: s.sameText,
        sameTextIgnoringSpace: s.sameTextIgnoringSpace,
      })),
    }),
  );
  if (notMeasured.length > 0) {
    console.error("측정이 아닌 회차", JSON.stringify(notMeasured, null, 2));
    process.exit(1);
  }
}

const mark = (value) => (value === null ? "·" : value ? "O" : "X");

function report(groups, legacy, legacySummary, screens, notMeasured) {
  const lines = [];
  lines.push("모양 프로브의 결과(shape.mjs 가 썼다). O 는 기대와 같다, X 는 다르다, · 는 기대를 걸지 않았다.");
  lines.push("목표 = 목표 모양(want), 규칙 = 그 후보의 규칙대로(wantBy).");
  lines.push("");
  for (const group of groups) {
    lines.push(`${"=".repeat(100)}\n${group.title} [${group.name}]  대조: ${group.control ?? "(없음)"}  후보: ${group.candidates.join(", ")}`);
    lines.push("=".repeat(100));
    for (const row of group.rows) {
      lines.push("");
      lines.push(`--- ${row.id}${row.problem ? "  (problem)" : ""}${row.note === null ? "" : `  ${row.note}`}`);
      if (row.revised !== null) lines.push(`    기대를 고쳤다: ${row.revised}`);
      lines.push(`    입력:   ${JSON.stringify(row.input)}`);
      lines.push(`    목표:   ${row.want === null ? "(정하지 않았다)" : JSON.stringify(row.want)}`);
      if (row.control !== null) {
        lines.push(`    파서:   ${row.control.parsed}`);
        lines.push(`    대조:   ${JSON.stringify(row.control.html)}   [블록 사이 줄 끝 ${row.control.structuralNewlines}, 문단 안 줄 끝 ${row.control.softNewlines}, br ${row.control.br}]`);
      }
      for (const candidate of group.candidates) {
        const v = row.verdicts[candidate];
        if (v === undefined) {
          lines.push(`    ${candidate}: (측정이 아니다)`);
          continue;
        }
        const flags = [`목표 ${mark(v.target)}`, `규칙 ${mark(v.rule)}`];
        if (v.sameAsTwin !== null) flags.push(`짝과 같다 ${mark(v.sameAsTwin)}`);
        if (v.violations.length > 0) flags.push(`위반 ${JSON.stringify(v.violations)}`);
        lines.push(`    ${candidate}: ${flags.join(", ")}   ${JSON.stringify(v.html)}`);
        if (["sources", "cite", "combined", "links"].includes(group.name)) lines.push(`        mdast: ${v.final}`);
      }
      if (row.literal !== undefined) {
        lines.push(
          `    변환 보고: R2 ${JSON.stringify(row.literal.r2)}  R1 ${JSON.stringify(row.literal.r1)}  R2(BOM 을 떼지 않은 원문) ${JSON.stringify(row.literal.r2RawSource)}`,
        );
      }
    }
    lines.push("");
  }
  lines.push(`${"=".repeat(100)}\n기존 입력 52가지를 합친 시제품으로 [legacy-52]\n${"=".repeat(100)}`);
  lines.push(JSON.stringify(legacySummary, null, 2));
  for (const row of legacy) {
    lines.push("");
    lines.push(`--- ${row.id}`);
    lines.push(`    입력:   ${JSON.stringify(row.input)}`);
    lines.push(`    HTML:   ${JSON.stringify(row.html)}`);
    if (row.violations.length > 0) lines.push(`    위반:   ${JSON.stringify(row.violations)}`);
    if (row.mustFailures.length > 0) lines.push(`    기존 기대 어김: ${JSON.stringify(row.mustFailures)}`);
  }
  lines.push("");
  lines.push(`${"=".repeat(100)}\n화면 파일과 견주기 [screens]\n${"=".repeat(100)}`);
  for (const s of screens) {
    lines.push("");
    lines.push(
      `--- ${s.screen} ← ${s.input}: 요소의 종류와 차례 ${mark(s.sameSkeleton)}, 글자(공백을 하나로) ${mark(s.sameText)}, 글자(공백을 빼고) ${mark(s.sameTextIgnoringSpace)}`,
    );
    lines.push(`    화면:   ${s.wanted.skeleton}`);
    lines.push(`    시제품: ${s.got.skeleton}`);
    if (!s.sameText) {
      lines.push(`    화면 글:   ${JSON.stringify(s.wanted.text)}`);
      lines.push(`    시제품 글: ${JSON.stringify(s.got.text)}`);
    }
  }
  lines.push("");
  lines.push(`측정이 아닌 회차: ${notMeasured.length}`);
  for (const item of notMeasured) lines.push(`    ${JSON.stringify(item)}`);
  return `${lines.join("\n")}\n`;
}

await main();
