// 바로 앞 형제가 제목인 제목에 표지를 다는 변환(명세 "모양은 요소마다의 클래스로 낸다"의 "표지의 길", 변환의 차례 8).
// 화면 그림은 제목 바로 뒤의 제목 사이를 16px 로 그렸는데, 요소에 클래스를 주는 부품은 형제를 가리킬 수 없다. 그래서 변환이
// 노드에 표지를 달고 부품이 요소의 속성으로 읽어 클래스를 고른다. 표지는 DOM 에 넘기지 않는다.
// 표지는 mdast 노드의 `data.hProperties` 로 달아 react-markdown 이 요소의 `data-after-heading` 속성으로 넘긴다.
import type { Root } from "mdast";
import { forEachNode } from "./tree";

/** 변환이 단 표지의 속성 이름. 부품이 읽고 지운다. */
export const AFTER_HEADING = "data-after-heading";

export function markHeadingsAfterHeading(tree: Root): void {
  forEachNode(tree, (node) => {
    if (!("children" in node)) return;
    let previousIsHeading = false;
    for (const child of node.children) {
      if (child.type === "heading" && previousIsHeading) {
        // `hProperties` 는 mdast-util-to-hast 가 `Data` 에 더하는 키인데 이 패키지의 타입에는 들지 않는다.
        const data: Record<string, unknown> = {
          ...child.data,
          hProperties: { dataAfterHeading: "true" },
        };
        child.data = data;
      }
      previousIsHeading = child.type === "heading";
    }
  });
}
