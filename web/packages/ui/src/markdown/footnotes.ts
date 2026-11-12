// 각주 문법을 원문의 글자로 되돌리는 변환(명세 "각주와 할 일 목록", 변환의 차례 4). ADR 0053 은 각주를 그리지 않는다고
// 정했는데 remark-gfm 에는 각주만 끄는 옵션이 없다. 그대로 두면 본문의 `[^1]` 은 표지 없는 `1` 이 되고, 출력 끝에 숨긴 영어
// 제목과 돌아가기 표시가 생긴다.
// - `footnoteReference`(본문의 `[^1]`)는 원문에서 그 자리의 글자를 든 글자 노드가 된다.
// - `footnoteDefinition`(`[^1]: 글`)은 껍데기를 벗기고 첫 문단 앞에 `[^1]: ` 을 글자로 둔다. 정의는 놓인 자리에 남고
//   끝으로 옮기지 않는다. 정의 안의 서식은 그리고, 정의 안에 든 정의도 같은 방식으로 글자가 된다.
// 정의가 없는 `[^1]` 은 파서가 처음부터 글자로 두므로 손댈 것이 없다.
import type { FootnoteDefinition, FootnoteReference, Paragraph, Root, RootContent } from "mdast";
import { forEachNode, isPhrasingParent, sourceRange, text } from "./tree";

type Blocks = FootnoteDefinition["children"];

function marker(node: FootnoteReference | FootnoteDefinition): string {
  return `[^${node.label ?? node.identifier}]`;
}

function referenceText(node: FootnoteReference, source: string): string {
  const range = sourceRange(node);
  return range === null ? marker(node) : source.slice(range.start, range.end);
}

function isFootnoteDefinition(node: RootContent): boolean {
  return node.type === "footnoteDefinition";
}

function unwrapDefinition(node: FootnoteDefinition): Blocks {
  const head = text(`${marker(node)}: `);
  const [first, ...rest] = node.children;
  if (first?.type === "paragraph") {
    const paragraph: Paragraph = { type: "paragraph", children: [head, ...first.children] };
    return [paragraph, ...rest];
  }
  const paragraph: Paragraph = { type: "paragraph", children: [head] };
  return [paragraph, ...node.children];
}

function unwrapBlocks(children: Blocks): Blocks {
  const next: Blocks = [];
  for (const child of children) {
    if (child.type === "footnoteDefinition") next.push(...unwrapDefinition(child));
    else next.push(child);
  }
  return next;
}

function unwrapRoot(children: RootContent[]): RootContent[] {
  const next: RootContent[] = [];
  for (const child of children) {
    if (child.type === "footnoteDefinition") next.push(...unwrapDefinition(child));
    else next.push(child);
  }
  return next;
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
    // 한 번에 한 겹씩 벗긴다. 정의 안에 든 정의는 벗긴 뒤에야 같은 자리의 형제가 되므로, 정의가 남지 않을 때까지 되풀이한다.
    // 재귀가 아니라 반복이어서 겹이 깊어도 스택이 넘치지 않는다.
    if (node.type === "root") {
      while (node.children.some(isFootnoteDefinition)) node.children = unwrapRoot(node.children);
    } else if (node.type === "blockquote" || node.type === "listItem") {
      while (node.children.some(isFootnoteDefinition)) node.children = unwrapBlocks(node.children);
    }
  });
}
