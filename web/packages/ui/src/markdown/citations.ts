// 문장 끝 번호 `[숫자]` 를 위첨자로 바꾸는 변환(명세 "문장 끝 번호", 변환의 차례 6).
//
// 번호로 보는 것은 글자 노드 안의 `[`, ASCII 숫자 한 자리에서 세 자리, `]` 다. 문장 끝이 아니어도 본다. 번호로 보지 않는 것은
// 이렇다.
// - 바로 앞 글자가 ASCII 영문자·숫자·밑줄인 것(`a[1]`). 그렇게 건너뛴 번호에 바로 붙은 번호도 건너뛴다(`A[1][2]`).
// - 줄 머리의 것. 블록이나 칸의 첫 글자, 줄 끝 글자 바로 뒤, 굵게나 기울임의 첫 글자에서 시작하는 번호다(앞이 공백뿐인 것도).
// - 링크 글 안의 것과 출처 덩이 안의 것. 그 아래를 통째로 건너뛴다.
// - 네 자리 이상인 것. 숫자 밖의 글자가 든 것은 처음부터 번호의 꼴이 아니다.
// - 원문의 그 범위에 역슬래시로 쓴 여는 대괄호(`\[`)가 있는 글자 노드의 것. 노드를 통째로 건너뛴다. 위치가 없는 노드(닫히지
//   않는 굵게와 숫자 사이 기호의 변환이 지은 것)는 알아보지 못하고 번호로 본다(명세의 받아들이는 한계).
// 코드, 이미지의 대체 글, 링크 주소는 글자 노드가 아니라 대상이 아니다.
//
// 번호로 본 것은 대괄호와 바로 앞의 빈칸·탭을 떼고 숫자만 위첨자 노드에 둔다. 위첨자 노드는 기울임(`emphasis`)에 `hName:
// "sup"` 과 표지를 얹은 것이다(mdast 에 위첨자 노드가 없어 줄 안 노드 하나를 빌린다). 공백을 뗀 뒤 바로 앞 형제가 위첨자
// 번호인 번호(`[1][2]`, `[1] [2]` 의 둘째)에는 이어진 번호의 표지를 단다. 부품이 표지로 왼쪽 틈을 고르고 표지를 DOM 에
// 넘기지 않는다.
//
// 번호의 수에 비례하는 시간에 돈다. 글자 노드마다 번호를 앞에서부터 한 번 찾고, 줄 머리인지는 지나온 글자로 이어서 안다.
// 번호마다 줄의 앞이나 나머지를 다시 훑지 않는다(명세 "구현에 넘기는 것").
import type { Emphasis, Nodes, PhrasingContent, Root, Text } from "mdast";
import { isSourcesBlock } from "./sources";
import { forEachPhrasingParent, hastName, sourceRange, text } from "./tree";

/** 변환이 위첨자 번호에 단 표지의 속성 이름. 부품이 읽고 지운다. */
export const CITE_MARK = "data-cite";
/** 같은 표지의 hast 속성 이름. 부품의 허용 목록이 이 속성이 있는 `sup` 만 들인다. */
export const CITE_PROPERTY = "dataCite";
/** 표지의 값. 바로 앞 형제가 위첨자 번호인 번호(이어진 번호)면 이 값이고, 아니면 `CITE_FIRST` 다. */
export const CITE_ADJACENT = "adjacent";
export const CITE_FIRST = "first";

const MARKER = /\[(\d+)\]/g;
const MAX_DIGITS = 3;

function isWordChar(char: string | undefined): boolean {
  if (char === undefined) return false;
  return (
    (char >= "a" && char <= "z") ||
    (char >= "A" && char <= "Z") ||
    (char >= "0" && char <= "9") ||
    char === "_"
  );
}

function isLineEnd(char: string | undefined): boolean {
  return char === "\n" || char === "\r";
}

function citation(digits: string, mark: typeof CITE_FIRST | typeof CITE_ADJACENT): Emphasis {
  // `hName`·`hProperties` 는 mdast-util-to-hast 가 `Data` 에 더하는 키인데 이 패키지의 타입에는 들지 않는다.
  const data: Record<string, unknown> = {
    hName: "sup",
    hProperties: { [CITE_PROPERTY]: mark },
  };
  return { type: "emphasis", data, children: [text(digits)] };
}

function isCitation(node: PhrasingContent | undefined): boolean {
  return node?.type === "emphasis" && hastName(node) === "sup";
}

/**
 * 글자 노드 하나를 글자와 위첨자 번호로 갈라 `out` 에 잇는다. `startsLine` 은 이 노드가 줄 머리에서 시작하는가(부모의 첫
 * 자식이거나 앞이 줄바꿈 노드다)이다.
 */
function rewrite(
  node: Text,
  out: PhrasingContent[],
  { startsLine }: { readonly startsLine: boolean },
): void {
  const value = node.value;
  // `scanned` 앞까지의 글자로 지금 줄에 공백 밖의 글자가 있었는지(`lineHasContent`), 노드의 첫 줄을 지났는지를 이어서 안다.
  let scanned = 0;
  let lineHasContent = false;
  let pastFirstLine = false;
  let last = 0;
  let refusedEnd = -1;
  for (const match of value.matchAll(MARKER)) {
    const start = match.index;
    const end = start + match[0].length;
    for (; scanned < start; scanned += 1) {
      const char = value.charAt(scanned);
      if (isLineEnd(char)) {
        lineHasContent = false;
        pastFirstLine = true;
      } else if (char.trim() !== "") {
        lineHasContent = true;
      }
    }
    const atLineStart = !lineHasContent && (pastFirstLine || startsLine);
    const digits = match[1] ?? "";
    const refused =
      digits.length > MAX_DIGITS ||
      isWordChar(value[start - 1]) ||
      refusedEnd === start ||
      atLineStart;
    // 번호의 글자(`[1]`)는 공백이 아니므로 이 줄은 이제 줄 머리가 아니다.
    scanned = end;
    lineHasContent = true;
    if (refused) {
      refusedEnd = end;
      continue;
    }
    let cut = start;
    while (cut > last && (value[cut - 1] === " " || value[cut - 1] === "\t")) cut -= 1;
    if (cut > last) out.push(text(value.slice(last, cut)));
    out.push(citation(digits, isCitation(out.at(-1)) ? CITE_ADJACENT : CITE_FIRST));
    last = end;
  }
  if (last === 0) out.push(node);
  else if (last < value.length) out.push(text(value.slice(last)));
}

function escapedBracket(node: Text, source: string): boolean {
  const range = sourceRange(node);
  return range !== null && source.slice(range.start, range.end).includes("\\[");
}

function skipped(node: Nodes): boolean {
  return node.type === "link" || node.type === "linkReference" || isSourcesBlock(node);
}

export function citationsToSuperscript(tree: Root, source: string): void {
  forEachPhrasingParent(
    tree,
    (parent) => {
      const { children } = parent;
      if (!children.some((child) => child.type === "text" && child.value.includes("["))) return;
      const next: PhrasingContent[] = [];
      children.forEach((child, index) => {
        if (child.type !== "text" || escapedBracket(child, source)) {
          next.push(child);
          return;
        }
        const previous = children[index - 1];
        rewrite(child, next, { startsLine: previous === undefined || previous.type === "break" });
      });
      parent.children = next;
    },
    skipped,
  );
}
