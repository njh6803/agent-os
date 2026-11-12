// 할 일 목록의 표시를 원문의 글자로 되돌리는 변환(명세 "각주와 할 일 목록", 변환의 차례 4). ADR 0053 은 체크박스를 그리지
// 않는다고 정했다. remark-gfm 은 항목 머리의 `[ ]`·`[x]` 를 글에서 떼어 항목 노드의 `checked` 로 옮기고, 허용 목록은 그것을
// 그리는 `input` 을 내지 않는다. 그대로 두면 끝난 일과 남은 일의 구분이 화면에서 사라진다.
// 이 변환은 `checked` 를 지우고 표시(`[ ]`, `[x]`, `[X]`)를 원문 글자 그대로 항목의 첫 문단 앞에 둔다.
//
// 원문의 표시는 첫 문단의 시작 위치에서 찾는다. 파서는 표시 뒤의 공백 한 칸을 문단의 첫 글자 노드에서 떼고, 그 노드에 글자가
// 남으면 문단의 시작 위치를 그 공백 다음으로 옮기며, 남지 않으면(표시 바로 뒤가 굵게 같은 다른 노드다) 옮기지 않는다
// (mdast-util-gfm-task-list-item 의 `exitParagraphWithTaskListItem`). 그래서 표시는 시작 위치의 네 글자 앞이나 시작 위치
// 바로 그 자리에서 시작한다. 두 자리 모두 표시의 꼴이 아니거나 위치가 없으면 `checked` 값으로 지은 표시를 쓴다.
import type { ListItem, Paragraph, Root } from "mdast";
import { forEachNode, sourceRange, text } from "./tree";

const MARK = /^\[[ \txX]\]$/u;
const DONE = "[x]";
const OPEN = "[ ]";

function writtenMark(paragraph: Paragraph | undefined, fallback: string, source: string): string {
  const range = paragraph === undefined ? null : sourceRange(paragraph);
  if (range === null) return fallback;
  for (const back of [4, 0]) {
    const from = range.start - back;
    if (from < 0) continue;
    const written = source.slice(from, from + 3);
    if (MARK.test(written)) return written;
  }
  return fallback;
}

function restore(item: ListItem, fallback: string, source: string): void {
  const first = item.children[0];
  const paragraph = first?.type === "paragraph" ? first : undefined;
  const head = text(`${writtenMark(paragraph, fallback, source)} `);
  if (paragraph === undefined) {
    item.children = [{ type: "paragraph", children: [head] }, ...item.children];
  } else {
    paragraph.children = [head, ...paragraph.children];
  }
  item.checked = null;
}

export function taskMarksToText(tree: Root, source: string): void {
  forEachNode(tree, (node) => {
    if (node.type !== "listItem") return;
    if (node.checked === true) restore(node, DONE, source);
    else if (node.checked === false) restore(node, OPEN, source);
  });
}
