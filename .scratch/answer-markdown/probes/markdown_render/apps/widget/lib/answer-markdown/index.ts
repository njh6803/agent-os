// 합친 시제품의 mdast 변환. 다섯 처리를 정한 차례로 한 번에 돈다. 프로브가 고른 후보와 규칙이 여기 모인다.
//
// 차례와 그 까닭
// 1. 닫히지 않은 강조 되살리기(cjk-emphasis.ts). 파서가 낸 글자 노드의 위치를 본다. 뒤의 변환이 글자 노드를 합치면
//    위치가 사라지므로 맨 먼저 돈다. 이 변환이 만든 `strong`·`emphasis` 에는 위치가 없다.
// 2. 숫자 사이 별표와 밑줄 강조를 글자로(literal-marks.ts). 파서가 낸 `strong`·`emphasis` 의 위치만 본다. 1이 만든
//    노드는 위치가 없어 건너뛰고, 2가 글자로 되돌린 별표는 1이 이미 지나간 뒤라 다시 굵게 되지 않는다.
// 2-1. 각주 문법을 글자로(footnotes.ts). 원문의 위치를 보는 1과 2 뒤에 돈다. 되돌린 `[^1]` 은 번호 변환이 보지 않는다
//    (`[숫자]` 꼴이 아니다).
// 2-2. 할 일 목록의 표시를 글자로(task-marks.ts). 같은 까닭으로 1과 2 뒤에 돈다. 되돌린 `[x]`·`[ ]` 도 `[숫자]` 꼴이
//    아니라 번호 변환이 보지 않는다.
// 3. 출처 덩이 감싸기(sources.ts). 번호 변환보다 먼저 돌아야 출처 덩이 안의 `[1]` 을 번호로 바꾸지 않는다.
// 4. 문장 끝 번호를 위첨자로(citations.ts). 줄 머리와 줄 끝을 글자 노드의 줄 끝 글자로도 보므로 줄바꿈 변환보다 먼저 돈다.
//    역슬래시로 쓴 대괄호(`\[1\]`)는 글자 노드의 원문 위치로 알아본다. 1과 2가 새로 지은 글자 노드에는 위치가 없어,
//    그 노드의 `\[1\]` 은 번호가 된다. 알고 받아들인 한계다(명세 "문장 끝 번호"의 받아들이는 한계).
// 5. 한 줄 바꿈을 `break` 로(soft-breaks.ts).
// 깊이 가드(`maxContainerDepth`)를 켜면 다섯보다 먼저 겹 수를 세고, 넘으면 던진다.
//
// 강조 되살리기나 줄바꿈을 라이브러리 플러그인에 맡기는 조합(remark-cjk-friendly, remark-breaks)은 그 단계를 끄고
// 플러그인 목록에서 자리를 잡는다(remark-cjk-friendly 는 이 변환 앞, remark-breaks 는 뒤).
import type { Root } from "mdast";
import { type CitationRule, citationsToSuperscript } from "./citations";
import { recoverUnclosedEmphasis } from "./cjk-emphasis";
import { footnotesToText } from "./footnotes";
import { type DigitRule, literalizeMarks } from "./literal-marks";
import { softBreaksToBreaks } from "./soft-breaks";
import { isSourcesBlock, type SourcesRule, wrapSources } from "./sources";
import { taskMarksToText } from "./task-marks";
import { containerDepth, sourceOf } from "./tree";

// 사람이 고른 규칙이다(2026-11-11 "글자가 낀 식까지 넓힘"). 여는 묶음의 앞과 닫는 묶음의 뒤가 숫자이면 글자로 둔다.
export const ANSWER_DIGIT_RULE: DigitRule = "outer-digits";

export const ANSWER_CITATION_RULE: CitationRule = {
  skipAfterWordChar: true,
  onlyAtLineEnd: false,
  skipAtLineStart: true,
  skipInLink: true,
  maxDigits: 3,
};

export const ANSWER_SOURCES_RULE: SourcesRule = {
  heading: true,
  emphasized: true,
  colon: true,
  unorderedList: false,
  splitTrailingLine: true,
  bracketLines: true,
};

export interface AnswerSteps {
  /** 닫히지 않은 강조를 직접 짠 변환으로 되살린다. remark-cjk-friendly 를 쓰는 조합은 끈다. */
  readonly recoverEmphasis: boolean;
  /** 한 줄 바꿈을 직접 짠 변환으로 `break` 로 바꾼다. remark-breaks 를 쓰는 조합은 끈다. */
  readonly softBreaks: boolean;
  /**
   * 각주 문법을 글자로 되돌린다(footnotes.ts). 기본은 켠 것이고, 프로브가 끈 갈래(`false`)를 대조로 잰다.
   * 위치를 보는 앞의 두 변환 뒤에, 출처 덩이와 번호 변환 앞에 돈다.
   */
  readonly footnotesAsText?: boolean;
  /**
   * 깊이 가드. 인용과 목록이 이 겹 수를 넘게 겹치면 그리지 않고 던진다(부품이 받아 원문을 보인다). 없으면 세지 않는다.
   * 합친 시제품의 기본은 가드가 없는 것이고, 프로브가 가드를 켠 갈래를 따로 잰다.
   */
  readonly maxContainerDepth?: number;
}

/** 깊이 가드가 던지는 오류. 스택이 넘쳐 난 `RangeError` 와 이름으로 가른다. */
export class AnswerTooDeepError extends Error {
  override readonly name = "AnswerTooDeepError";

  constructor(depth: number, limit: number) {
    super(`인용과 목록이 ${String(depth)}겹 겹쳤다(한도 ${String(limit)}겹)`);
  }
}

const ALL_STEPS: AnswerSteps = { recoverEmphasis: true, softBreaks: true };

export function remarkAnswer(steps: AnswerSteps = ALL_STEPS): (tree: Root, file: { readonly value: unknown }) => undefined {
  return (tree, file) => {
    if (steps.maxContainerDepth !== undefined) {
      const depth = containerDepth(tree);
      if (depth > steps.maxContainerDepth) throw new AnswerTooDeepError(depth, steps.maxContainerDepth);
    }
    const source = sourceOf(file);
    if (steps.recoverEmphasis) recoverUnclosedEmphasis(tree, source);
    literalizeMarks(tree, source, ANSWER_DIGIT_RULE);
    if (steps.footnotesAsText !== false) footnotesToText(tree, source);
    taskMarksToText(tree, source);
    wrapSources(tree, ANSWER_SOURCES_RULE);
    citationsToSuperscript(tree, source, ANSWER_CITATION_RULE, isSourcesBlock);
    if (steps.softBreaks) softBreaksToBreaks(tree);
  };
}
