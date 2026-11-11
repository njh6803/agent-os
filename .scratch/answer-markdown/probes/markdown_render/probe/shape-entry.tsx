// 모양 프로브의 입구. shape.mjs 와 textcompare.mjs 가 esbuild 로 묶어 Node 에서 부른다.
//
// 갈래(variant)마다 시제품 부품(`AnswerMarkdown.tsx` 의 `createAnswerMarkdown`)에 다른 플러그인 목록을 준다. 부품의
// 나머지(제목 낮추기, 링크, 이미지, 표 칸, 허용 목록)는 모든 갈래가 같다. 목록의 맨 앞과 맨 뒤에 나무를 베껴 두는
// 플러그인을 끼워, 파서가 낸 mdast 와 변환을 모두 지난 mdast 를 함께 돌려준다.
// 바깥의 `div[data-probe]` 는 "이 회차가 실제로 그려졌다"는 표지이고 shape.mjs 가 단언한다.
import type { Root } from "mdast";
import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import remarkBreaks from "remark-breaks";
import remarkCjkFriendly from "remark-cjk-friendly";
import remarkGfm from "remark-gfm";
import remarkParse from "remark-parse";
import { unified } from "unified";
import { createAnswerMarkdown, type RemarkPlugins } from "../apps/widget/components/molecules/AnswerMarkdown";
import { type CitationRule, remarkCitations } from "../apps/widget/lib/answer-markdown/citations";
import { remarkRecoverEmphasis } from "../apps/widget/lib/answer-markdown/cjk-emphasis";
import { ANSWER_CITATION_RULE, ANSWER_SOURCES_RULE, remarkAnswer } from "../apps/widget/lib/answer-markdown/index";
import {
  type DigitRule,
  type LiteralMarksReport,
  literalizeMarks,
  remarkLiteralMarks,
} from "../apps/widget/lib/answer-markdown/literal-marks";
import { remarkLiteralMarksSyntax } from "../apps/widget/lib/answer-markdown/literal-marks-syntax";
import { remarkSoftBreaks } from "../apps/widget/lib/answer-markdown/soft-breaks";
import { remarkSources, type SourcesRule } from "../apps/widget/lib/answer-markdown/sources";
import { sourceOf } from "../apps/widget/lib/answer-markdown/tree";
import { linkUrl } from "../apps/widget/lib/link-url";

interface Captured {
  parsed: Root | null;
  final: Root | null;
}

const captured: Captured = { parsed: null, final: null };

function spyParsed(): (tree: Root) => undefined {
  return (tree) => {
    captured.parsed = structuredClone(tree);
  };
}

function spyFinal(): (tree: Root) => undefined {
  return (tree) => {
    captured.final = structuredClone(tree);
  };
}

// (라) 후보 규칙. A 는 코드가 아닌 글자 노드의 모든 `[숫자]`, B 는 A 에서 바로 앞이 ASCII 영문자·숫자·밑줄인 것을
// 뺀 것, C 는 줄이나 블록의 끝에 오는 것만이다. D 는 합친 시제품이 쓰는 규칙(B 에 줄 머리·링크 글·자릿수 제한)이다.
const CITE_A: CitationRule = {
  skipAfterWordChar: false,
  onlyAtLineEnd: false,
  skipAtLineStart: false,
  skipInLink: false,
  maxDigits: 99,
};
const CITE_B: CitationRule = { ...CITE_A, skipAfterWordChar: true };
const CITE_C: CitationRule = { ...CITE_A, onlyAtLineEnd: true };

// (마) 후보 규칙. narrow 는 "글이 `출처` 인 문단 + 번호 목록"만, base 는 과제의 기본 규칙(문단 또는 제목 + 번호 목록),
// wide 는 갈래를 모두 켠 것, pick 은 합친 시제품이 쓰는 규칙이다.
const SOURCES_NARROW: SourcesRule = {
  heading: false,
  emphasized: false,
  colon: false,
  unorderedList: false,
  splitTrailingLine: false,
  bracketLines: false,
};
const SOURCES_BASE: SourcesRule = { ...SOURCES_NARROW, heading: true };
const SOURCES_WIDE: SourcesRule = {
  heading: true,
  emphasized: true,
  colon: true,
  unorderedList: true,
  splitTrailingLine: true,
  bracketLines: true,
};

const R2: DigitRule = "between-digits";
const R1: DigitRule = "outer-digits";

const PLUGINS: Readonly<Record<string, RemarkPlugins>> = {
  // 대조: 변환 없이 파서(remark-gfm)만.
  base: [remarkGfm],
  // (가)
  "breaks-plugin": [remarkGfm, remarkBreaks],
  "breaks-own": [remarkGfm, remarkSoftBreaks],
  // (나)
  "cjk-plugin": [remarkGfm, remarkCjkFriendly],
  "cjk-plugin-first": [remarkCjkFriendly, remarkGfm],
  "cjk-own": [remarkGfm, remarkRecoverEmphasis],
  // (다)
  "literal-r2": [remarkGfm, [remarkLiteralMarks, R2]],
  "literal-r1": [remarkGfm, [remarkLiteralMarks, R1]],
  "literal-syntax": [remarkGfm, remarkLiteralMarksSyntax],
  // (나)와 (다)를 함께 켠 것. 이름은 도는 차례다.
  "own-cjk>r2": [remarkGfm, remarkRecoverEmphasis, [remarkLiteralMarks, R2]],
  "r2>own-cjk": [remarkGfm, [remarkLiteralMarks, R2], remarkRecoverEmphasis],
  "cjk-plugin+r2": [remarkGfm, remarkCjkFriendly, [remarkLiteralMarks, R2]],
  "cjk-plugin>syntax": [remarkGfm, remarkCjkFriendly, remarkLiteralMarksSyntax],
  "syntax>cjk-plugin": [remarkGfm, remarkLiteralMarksSyntax, remarkCjkFriendly],
  // 첫 결과를 본 뒤 더한 갈래다(2026-11-11). 토큰 단계에서 글자로 둔 별표를 파싱 뒤의 (나) 변환이 다시 묶는지 본다.
  "syntax+own-cjk": [remarkGfm, remarkLiteralMarksSyntax, remarkRecoverEmphasis],
  // 사람이 별표 규칙을 넓힌 규칙(R1)으로 고른 뒤 더한 갈래다(2026-11-11). 합친 시제품의 차례와 그 거꾸로다.
  "own-cjk>r1": [remarkGfm, remarkRecoverEmphasis, [remarkLiteralMarks, R1]],
  "r1>own-cjk": [remarkGfm, [remarkLiteralMarks, R1], remarkRecoverEmphasis],
  // (라)
  "cite-a": [remarkGfm, [remarkCitations, CITE_A]],
  "cite-b": [remarkGfm, [remarkCitations, CITE_B]],
  "cite-c": [remarkGfm, [remarkCitations, CITE_C]],
  "cite-d": [remarkGfm, [remarkCitations, ANSWER_CITATION_RULE]],
  // (마)
  "sources-narrow": [remarkGfm, [remarkSources, SOURCES_NARROW]],
  "sources-base": [remarkGfm, [remarkSources, SOURCES_BASE]],
  "sources-wide": [remarkGfm, [remarkSources, SOURCES_WIDE]],
  "sources-pick": [remarkGfm, [remarkSources, ANSWER_SOURCES_RULE]],
  "breaks>sources-pick": [remarkGfm, remarkSoftBreaks, [remarkSources, ANSWER_SOURCES_RULE]],
  "sources-pick>breaks": [remarkGfm, [remarkSources, ANSWER_SOURCES_RULE], remarkSoftBreaks],
  // 합친 시제품과, 한 단계를 라이브러리 플러그인으로 바꾼 것.
  combined: [remarkGfm, remarkAnswer],
  "combined-breaks-plugin": [remarkGfm, [remarkAnswer, { recoverEmphasis: true, softBreaks: false }], remarkBreaks],
  "combined-cjk-plugin": [remarkGfm, remarkCjkFriendly, [remarkAnswer, { recoverEmphasis: false, softBreaks: true }]],
};

type View = (props: { readonly text: string }) => ReactNode;

const VIEWS: Readonly<Record<string, View>> = Object.fromEntries(
  Object.entries(PLUGINS).map(([name, plugins]) => [
    name,
    createAnswerMarkdown({
      remarkPlugins: [spyParsed, ...plugins, spyFinal],
      tableBox: "region",
      codeBlock: "focusable",
    }).View,
  ]),
);

export const VARIANTS = Object.keys(PLUGINS);

export interface Rendered {
  readonly html: string;
  /** 파서가 낸 mdast(변환 전). */
  readonly parsed: Root | null;
  /** 변환을 모두 지난 mdast. */
  readonly final: Root | null;
}

export function render(variant: string, id: string, text: string): Rendered {
  const Renderer = VIEWS[variant];
  if (Renderer === undefined) {
    throw new Error(`없는 갈래다: ${variant}`);
  }
  captured.parsed = null;
  captured.final = null;
  const html = renderToStaticMarkup(
    <div data-probe={id}>
      <Renderer text={text} />
    </div>,
  );
  return { html, parsed: captured.parsed, final: captured.final };
}

/**
 * (다)의 변환이 노드를 몇 개 벗기고, 두고, 판정하지 못했는지. `skipped` 가 0 이 아니면 위치가 원문과 어긋난 것이다.
 * `source` 가 "as-transform" 이면 변환이 실제로 쓰는 원문(`sourceOf`, 맨 앞의 BOM 을 뗀다)이고, "raw" 면 받은 글
 * 그대로다. BOM 으로 시작하는 입력에서 둘이 갈려야 그 사례가 BOM 을 떼는 길을 실제로 지난 것이다.
 */
export function literalReport(text: string, rule: DigitRule, source: "as-transform" | "raw"): LiteralMarksReport {
  const tree = unified().use(remarkParse).use(remarkGfm).parse(text);
  return literalizeMarks(tree, source === "raw" ? text : sourceOf({ value: text }), rule);
}

/** 링크 주소 판정 함수를 그대로 부른다. */
export function judgeUrl(value: string): string | null {
  return linkUrl(value);
}
