// 할 일 목록의 표시를 글자로 되돌리는 변환. ADR 0053 은 체크박스를 그리지 않는다고 정했다. remark-gfm 은 항목 머리의
// `[ ]`·`[x]` 를 글에서 떼어 항목 노드의 `checked` 로 옮기고, react-markdown 은 그것을 `input` 과 클래스
// (`task-list-item`, `contains-task-list`)로 그린다. 허용 목록이 `input` 을 그리지 않으므로 그대로 두면 끝난 일과 남은
// 일의 구분이 화면에서 사라진다(프로브 render.mjs 의 `x50-task-list` 와 shape.mjs 의 변환 전 실행이 봤다).
// 이 변환은 `checked` 를 지우고 표시를 원문의 글자 그대로 항목의 첫 문단 앞에 둔다.
//
// 원문의 표시는 첫 문단의 시작 위치에서 찾는다. 표시는 문단 안의 맨 앞에 놓이는 문법이라 문단은 본디 표시의 `[` 에서
// 시작한다. 파서는 표시 뒤의 공백 한 칸을 문단의 첫 글자 노드에서 떼고, 그 노드에 글자가 남으면 문단의 시작 위치를
// 그 공백 다음으로 옮기며, 남지 않으면(표시 바로 뒤가 굵게 같은 다른 노드다) 위치를 옮기지 않는다
// (mdast-util-gfm-task-list-item 2.0.1 의 `exitParagraphWithTaskListItem` 을 읽었다). 그래서 표시는 시작 위치의 네 글자
// 앞이나 시작 위치 바로 그 자리에서 시작한다. 첫 판은 뒤의 것을 "세 글자 앞"으로 어림했고, 사례 g06 이 그 자리가
// 틀렸다는 것을 잡았다(소문자 `[x]` 로 지어졌다). 두 자리 모두 표시의 꼴이 아니거나 위치가 없으면 `checked` 로 짓는다.
//
// 원문에서 표시를 찾지 못했을 때 짓는 표시(`built`)는 부르는 쪽이 `checked` 로 골라 글자로 넘긴다. 첫 판은 `checked` 를
// 불리언 매개변수로 세 함수에 넘겨 저장소의 판정자 규칙(`no-restricted-syntax` 의 불리언 매개변수)에 셋이 걸렸다
// (프로브 lint.mjs 가 잡았다).
import type { ListItem, Paragraph, Root } from "mdast";
import { forEachNode, sourceRange, text } from "./tree";

const MARK = /^\[[ \txX]\]$/u;
const BUILT_DONE = "[x]";
const BUILT_OPEN = "[ ]";

function markOf(paragraph: Paragraph | undefined, built: string, source: string): string {
  const range = paragraph === undefined ? null : sourceRange(paragraph);
  if (range === null) return built;
  for (const back of [4, 0]) {
    const from = range.start - back;
    if (from < 0) continue;
    const written = source.slice(from, from + 3);
    if (MARK.test(written)) return written;
  }
  return built;
}

function restore(item: ListItem, built: string, source: string): void {
  const first = item.children[0];
  const paragraph = first?.type === "paragraph" ? first : undefined;
  const head = text(`${markOf(paragraph, built, source)} `);
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
    if (node.checked === true) restore(node, BUILT_DONE, source);
    else if (node.checked === false) restore(node, BUILT_OPEN, source);
  });
}
