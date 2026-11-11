// (가) 후보 ②: 직접 짠 변환. 줄 안 글자 노드에 남은 줄 끝(`\n`, `\r\n`, `\r`)을 `break` 노드로 나눈다.
//
// 파서는 문단 안의 한 줄 바꿈을 글자 노드의 값에 줄 끝 글자로 남긴다. 코드(`code`, `inlineCode`)와 원시 HTML(`html`)은
// 글자 노드가 아니라 손대지 않는다. 줄 끝 공백 둘이나 역슬래시로 쓴 강제 줄바꿈은 파서가 이미 `break` 노드로 냈고
// 그 줄 끝은 글자 노드에 남지 않는다.
import type { PhrasingContent, Root, Text } from "mdast";
import { forEachPhrasingParent, text } from "./tree";

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
  forEachPhrasingParent(tree, (parent) => {
    if (!parent.children.some((child) => child.type === "text" && LINE_END.test(child.value))) return;
    parent.children = parent.children.flatMap((child) => (child.type === "text" ? splitLines(child) : [child]));
  });
}

export function remarkSoftBreaks(): (tree: Root) => undefined {
  return (tree) => {
    softBreaksToBreaks(tree);
  };
}
