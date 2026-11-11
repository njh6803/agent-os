// 각주 문법을 글자로 되돌리는 변환. ADR 0053 은 각주를 그리지 않는다고 정했는데, remark-gfm 에는 각주만 끄는 옵션이
// 없다. 그대로 두면 본문의 `[^1]` 은 표지 없는 `1` 이 되고, 출력 끝에 숨긴 영어 제목(`Footnotes`)과 각주의 글과 돌아가기
// 표시(`↩`)가 생긴다(프로브 plaintext.mjs 와 textcompare.mjs 가 봤다). 이 변환은 파서가 낸 각주 노드 둘을 원문의 글자로
// 바꾼다.
// - `footnoteReference`(본문의 `[^1]`)는 원문에서 그 자리의 글자를 든 글자 노드가 된다.
// - `footnoteDefinition`(`[^1]: 글`)은 껍데기를 벗기고, 첫 문단 앞에 `[^1]: ` 을 글자로 둔다. 정의가 놓인 자리에 그대로
//   남는다(끝으로 옮기지 않는다).
// 정의가 없는 `[^1]` 은 파서가 처음부터 글자로 두므로 손댈 것이 없다.
import type { FootnoteDefinition, FootnoteReference, Paragraph, Root, RootContent } from "mdast";
import { forEachNode, isPhrasingParent, sourceRange, text } from "./tree";

function marker(node: FootnoteReference | FootnoteDefinition): string {
  return `[^${node.label ?? node.identifier}]`;
}

function referenceText(node: FootnoteReference, source: string): string {
  const range = sourceRange(node);
  return range === null ? marker(node) : source.slice(range.start, range.end);
}

function unwrapDefinition(node: FootnoteDefinition): FootnoteDefinition["children"] {
  const head = text(`${marker(node)}: `);
  const [first, ...rest] = node.children;
  if (first?.type === "paragraph") {
    const paragraph: Paragraph = { type: "paragraph", children: [head, ...first.children] };
    return [paragraph, ...rest];
  }
  const paragraph: Paragraph = { type: "paragraph", children: [head] };
  return [paragraph, ...node.children];
}

export function footnotesToText(tree: Root, source: string): void {
  forEachNode(tree, (node) => {
    if (isPhrasingParent(node)) {
      if (node.children.some((child) => child.type === "footnoteReference")) {
        node.children = node.children.map((child) =>
          child.type === "footnoteReference" ? text(referenceText(child, source)) : child,
        );
      }
      return;
    }
    if (node.type === "root") {
      if (node.children.some((child) => child.type === "footnoteDefinition")) {
        const next: RootContent[] = [];
        for (const child of node.children) {
          if (child.type === "footnoteDefinition") next.push(...unwrapDefinition(child));
          else next.push(child);
        }
        node.children = next;
      }
      return;
    }
    if (node.type === "blockquote" || node.type === "listItem") {
      if (node.children.some((child) => child.type === "footnoteDefinition")) {
        const next: FootnoteDefinition["children"] = [];
        for (const child of node.children) {
          if (child.type === "footnoteDefinition") next.push(...unwrapDefinition(child));
          else next.push(child);
        }
        node.children = next;
      }
    }
  });
}
