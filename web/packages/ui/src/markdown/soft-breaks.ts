// 한 줄 바꿈을 줄바꿈 노드로 바꾸는 변환(명세 "한 줄 바꿈", 변환의 차례 7). 파서는 문단 안의 한 줄 바꿈을 글자 노드의 값에
// 줄 끝 글자(`\n`, `\r\n`, `\r`)로 남긴다. 그 글자 노드를 `break` 노드로 나누어 `br` 로 그린다. 코드(줄 안과 블록)와 원시
// HTML 은 글자 노드가 아니라 손대지 않는다. 줄 끝 공백 둘이나 역슬래시로 쓴 강제 줄바꿈은 파서가 이미 `break` 로 냈다.
import type { PhrasingContent, Root, Text } from "mdast";
import { forEachNode, isPhrasingParent, text } from "./tree";

const LINE_END = /\r\n|\n|\r/;

function splitLines(node: Text): PhrasingContent[] {
  const lines = node.value.split(LINE_END);
  if (lines.length === 1) return [node];
  const pieces: PhrasingContent[] = [];
  lines.forEach((line, index) => {
    if (index > 0) pieces.push({ type: "break" });
    if (line !== "") pieces.push(text(line));
  });
  return pieces;
}

export function softBreaksToBreaks(tree: Root): void {
  forEachNode(tree, (node) => {
    if (!isPhrasingParent(node)) return;
    if (!node.children.some((child) => child.type === "text" && LINE_END.test(child.value))) return;
    node.children = node.children.flatMap((child) =>
      child.type === "text" ? splitLines(child) : [child],
    );
  });
}
