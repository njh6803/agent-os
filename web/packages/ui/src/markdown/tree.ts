// 변환들이 함께 쓰는 나무 도우미. 런타임 의존성이 없다(타입만 `@types/mdast` 에서 온다).
//
// 나무는 재귀가 아니라 스택으로 돈다. 깊게 겹친 입력(`>` 수천 겹)에서 부품의 처리가 라이브러리보다 먼저 스택을 넘기지
// 않게 하려는 것이다(명세 "변환의 차례").
import type {
  Delete,
  Emphasis,
  Heading,
  Link,
  LinkReference,
  Nodes,
  Paragraph,
  PhrasingContent,
  Strong,
  TableCell,
  Text,
} from "mdast";

/** 자식이 줄 안 내용(phrasing)인 노드. 글자 노드를 쪼개고 감싸는 변환은 이 노드의 `children` 만 바꾼다. */
export type PhrasingParent =
  Delete | Emphasis | Heading | Link | LinkReference | Paragraph | Strong | TableCell;

export function isPhrasingParent(node: Nodes): node is PhrasingParent {
  switch (node.type) {
    case "delete":
    case "emphasis":
    case "heading":
    case "link":
    case "linkReference":
    case "paragraph":
    case "strong":
    case "tableCell":
      return true;
    default:
      return false;
  }
}

/**
 * 나무의 모든 노드를 앞에서부터 한 번씩 찾는다. `visit` 이 노드의 `children` 을 바꾸면 바뀐 자식을 이어서 찾는다. `skip` 이
 * 참인 노드는 그 아래까지 건너뛴다.
 */
export function forEachNode(
  root: Nodes,
  visit: (node: Nodes) => void,
  skip: (node: Nodes) => boolean = () => false,
): void {
  const stack: Nodes[] = [root];
  for (let node = stack.pop(); node !== undefined; node = stack.pop()) {
    if (skip(node)) continue;
    visit(node);
    if ("children" in node) {
      for (let index = node.children.length - 1; index >= 0; index -= 1) {
        const child = node.children[index];
        if (child !== undefined) stack.push(child);
      }
    }
  }
}

/** 줄 안 내용을 든 노드마다 `visit` 을 부른다. `skip` 이 참인 노드는 그 아래까지 건너뛴다. */
export function forEachPhrasingParent(
  root: Nodes,
  visit: (parent: PhrasingParent) => void,
  skip: (node: Nodes) => boolean = () => false,
): void {
  forEachNode(
    root,
    (node) => {
      if (isPhrasingParent(node)) visit(node);
    },
    skip,
  );
}

/** 변환이 노드에 얹는 hast 요소 이름과 속성(`data.hName`, `data.hProperties`). 노드의 `data` 자리에 둔다. */
export function hastData(
  name: string,
  properties: Readonly<Record<string, string>>,
): Record<string, unknown> {
  // `hName`·`hProperties` 는 mdast-util-to-hast 가 `Data` 에 더하는 키인데 이 패키지의 타입에는 들지 않는다.
  return { hName: name, hProperties: properties };
}

/** 변환이 노드에 얹은 hast 요소 이름(`data.hName`). 얹지 않았으면 undefined 다. */
export function hastName(node: Nodes): unknown {
  // `hName` 은 mdast-util-to-hast 가 `Data` 에 더하는 키인데 이 패키지의 타입에는 들지 않는다.
  const data: Record<string, unknown> = { ...node.data };
  return data["hName"];
}

export function isAsciiDigit(char: string | undefined): boolean {
  return char !== undefined && char >= "0" && char <= "9";
}

/** 이웃한 글자 노드를 하나로 합치고 빈 글자 노드를 뺀다. 합친 노드에는 위치가 없다. */
export function mergeText(children: readonly PhrasingContent[]): PhrasingContent[] {
  const merged: PhrasingContent[] = [];
  for (const child of children) {
    if (child.type === "text" && child.value === "") continue;
    const last = merged.at(-1);
    if (child.type === "text" && last?.type === "text") {
      merged[merged.length - 1] = text(last.value + child.value);
    } else {
      merged.push(child);
    }
  }
  return merged;
}

/** 노드 아래의 글자 노드를 이어 붙인다(굵게·기울임 같은 껍데기는 벗긴다). 코드와 줄바꿈 노드는 글자로 세지 않는다. */
export function plainText(root: Nodes): string {
  let value = "";
  forEachNode(root, (node) => {
    if (node.type === "text") value += node.value;
  });
  return value;
}

/**
 * 인용과 목록이 가장 깊이 겹친 자리의 겹 수. `> > 글` 은 2, 목록 안의 목록 안의 인용은 3 이다. 재귀 없이 센다.
 * 깊이 가드가 쓴다(명세 "깊이 가드").
 */
export function containerDepth(root: Nodes): number {
  let deepest = 0;
  const stack: { readonly node: Nodes; readonly depth: number }[] = [{ node: root, depth: 0 }];
  for (let item = stack.pop(); item !== undefined; item = stack.pop()) {
    const depth =
      item.node.type === "blockquote" || item.node.type === "list" ? item.depth + 1 : item.depth;
    if (depth > deepest) deepest = depth;
    if ("children" in item.node) {
      for (const child of item.node.children) stack.push({ node: child, depth });
    }
  }
  return deepest;
}

export function text(value: string): Text {
  return { type: "text", value };
}

/**
 * 변환이 위치(오프셋)로 들여다볼 원문. 파서는 원문 맨 앞의 BOM(U+FEFF)을 건너뛰고 그다음 글자부터 0 으로 센다. BOM 이
 * 있으면 떼어야 위치가 맞는다.
 */
export function sourceOf(file: { readonly value: unknown }): string {
  if (typeof file.value !== "string") return "";
  return file.value.charCodeAt(0) === 0xfeff ? file.value.slice(1) : file.value;
}

/** 노드가 원문에서 차지하는 글자 범위. 변환이 만든 노드처럼 위치가 없으면 null 이다. */
export function sourceRange(node: Nodes): { readonly start: number; readonly end: number } | null {
  const start = node.position?.start.offset;
  const end = node.position?.end.offset;
  return start === undefined || end === undefined ? null : { start, end };
}
