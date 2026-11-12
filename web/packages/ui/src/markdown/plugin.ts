// 마크다운 부품의 remark 플러그인 하나(명세 "변환의 차례"). 파서(remark-gfm 포함)가 낸 나무를 요소로 바꾸기 전에 한 번
// 고친다. 이 티켓이 짓는 처리와 그 차례는 아래 넷이고, answer-markdown 티켓 02 가 2·3·5·6 을 그 사이에 끼운다.
// 1. 깊이 가드. 인용과 목록의 겹 수가 한도를 넘으면 던진다. 부품이 받아 원문으로 물러선다.
// 4. 각주 문법과 할 일 목록의 표시를 글자로. 원문의 위치를 보는 처리는 BOM 을 뗀 원문과 맞댄다.
// 7. 한 줄 바꿈을 줄바꿈으로.
// 8. 바로 앞 형제가 제목인 제목에 표지 달기. 맨 뒤에 돈다.
// 깊이를 세는 일과 나무를 고치는 일은 재귀 없이 돈다.
import type { Root } from "mdast";
import { footnotesToText } from "./footnotes";
import { markHeadingsAfterHeading } from "./heading-marks";
import { softBreaksToBreaks } from "./soft-breaks";
import { taskMarksToText } from "./task-marks";
import { containerDepth, sourceOf } from "./tree";

/** 인용과 목록이 이 겹 수를 넘으면 그리지 않고 원문으로 물러선다(명세 "깊이 가드"). 10겹까지는 그린다. */
const MAX_CONTAINER_DEPTH = 10;

/** 깊이 가드가 던지는 오류. 부품은 던지는 모든 것을 같은 길로 받아 원문으로 물러서므로 오류의 종류를 가르지 않는다. */
export class TooDeepError extends Error {
  override readonly name = "TooDeepError";

  constructor(depth: number) {
    super(`인용과 목록이 ${String(depth)}겹 겹쳤다(한도 ${String(MAX_CONTAINER_DEPTH)}겹)`);
  }
}

export function remarkAnswer(): (tree: Root, file: { readonly value: unknown }) => undefined {
  return (tree, file) => {
    const depth = containerDepth(tree);
    if (depth > MAX_CONTAINER_DEPTH) throw new TooDeepError(depth);
    const source = sourceOf(file);
    footnotesToText(tree, source);
    taskMarksToText(tree, source);
    softBreaksToBreaks(tree);
    markHeadingsAfterHeading(tree);
  };
}
