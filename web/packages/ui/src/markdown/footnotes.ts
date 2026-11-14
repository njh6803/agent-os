// 각주 문법을 원문의 글자로 되돌리는 변환(명세 "각주와 할 일 목록", 변환의 차례 4). ADR 0053 은 각주를 그리지 않는다고
// 정했는데 remark-gfm 에는 각주만 끄는 옵션이 없다. 그대로 두면 본문의 `[^1]` 은 표지 없는 `1` 이 되고, 출력 끝에 숨긴 영어
// 제목과 돌아가기 표시가 생긴다.
// - `footnoteReference`(본문의 `[^1]`)는 원문에서 그 자리의 글자를 든 글자 노드가 된다.
// - `footnoteDefinition`(`[^1]: 글`)은 껍데기를 벗기고 첫 문단 앞에 원문의 표지 `[^1]` 과 `: ` 을 글자로 둔다. 표지는 파서가
//   푼 `label` 이 아니라 원문에서 자른다(`[^a\*b]` 의 역슬래시가 본문의 참조처럼 남는다). 정의는 놓인 자리에 남고 끝으로
//   옮기지 않는다. 정의 안의 서식은 그리고, 정의 안에 든 정의도 같은 방식으로 글자가 된다.
// 정의가 없는 `[^1]` 은 파서가 처음부터 글자로 두므로 손댈 것이 없다.
import type { FootnoteDefinition, FootnoteReference, Paragraph, Root, RootContent } from "mdast";
import { forEachNode, isPhrasingParent, sourceRange, text } from "./tree";

type Block = FootnoteDefinition["children"][number];

function marker(node: FootnoteReference | FootnoteDefinition): string {
  return `[^${node.label ?? node.identifier}]`;
}

function referenceText(node: FootnoteReference, source: string): string {
  const range = sourceRange(node);
  return range === null ? marker(node) : source.slice(range.start, range.end);
}

/** 정의의 표지(`[^라벨]`)를 원문에서 자른다. 역슬래시로 쓴 글자는 건너뛰고 첫 `]` 까지다. 자르지 못하면 `label` 로 짓는다. */
function definitionMarker(node: FootnoteDefinition, source: string): string {
  const range = sourceRange(node);
  if (range === null || !source.startsWith("[^", range.start)) return marker(node);
  for (let at = range.start + 2; at < range.end; at += 1) {
    const char = source[at];
    if (char === "\\") at += 1;
    else if (char === "]") return source.slice(range.start, at + 1);
  }
  return marker(node);
}

function isFootnoteDefinition(node: RootContent): node is FootnoteDefinition {
  return node.type === "footnoteDefinition";
}

function unwrapDefinition(node: FootnoteDefinition, source: string): Block[] {
  const head = text(`${definitionMarker(node, source)}: `);
  const [first, ...rest] = node.children;
  if (first?.type === "paragraph") {
    const paragraph: Paragraph = { type: "paragraph", children: [head, ...first.children] };
    return [paragraph, ...rest];
  }
  const paragraph: Paragraph = { type: "paragraph", children: [head] };
  return [paragraph, ...node.children];
}

/** 자식 가운데 정의를 한 겹 벗긴다. 뿌리와 인용·목록 항목이 함께 쓴다. */
function unwrapDefinitions<C extends RootContent>(
  children: readonly C[],
  source: string,
): (C | Block)[] {
  const next: (C | Block)[] = [];
  for (const child of children) {
    if (isFootnoteDefinition(child)) next.push(...unwrapDefinition(child, source));
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
    // 재귀가 아니라 반복이어서 겹이 깊어도 스택이 넘치지 않는다. 뿌리와 인용·목록 항목은 자식의 타입이 달라 갈래를 나눈다.
    if (node.type === "root") {
      while (node.children.some(isFootnoteDefinition)) {
        node.children = unwrapDefinitions(node.children, source);
      }
    } else if (node.type === "blockquote" || node.type === "listItem") {
      while (node.children.some(isFootnoteDefinition)) {
        node.children = unwrapDefinitions(node.children, source);
      }
    }
  });
}
