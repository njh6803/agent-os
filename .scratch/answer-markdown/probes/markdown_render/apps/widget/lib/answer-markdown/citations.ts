// (라) 문장 끝 번호 `[숫자]` 를 위첨자로 바꾸는 변환. 어떤 글을 번호로 볼지는 규칙(`CitationRule`)이 정하고, 프로브가
// 규칙을 바꿔 가며 같은 입력을 견준다.
//
// 번호로 본 `[숫자]` 는 대괄호를 떼고, 바로 앞의 공백(빈칸·탭)을 떼어 앞 글자에 붙인다. 내는 노드는 `emphasis` 에
// `hName: "sup"` 을 얹은 것이다(mdast 에 위첨자 노드가 없어 줄 안 노드 하나를 빌린다). `data-cite` 속성은 부품이 GFM
// 각주가 내는 `sup` 과 가르는 표지다.
//
// 보는 것은 글자 노드뿐이다. 줄 안 코드와 코드 블록, 이미지의 대체 글, 링크 주소는 글자 노드가 아니다. 파서가 이미
// 다른 것으로 읽은 `[1]`(정의가 있는 링크 참조, `[1](주소)`, 각주)은 글자 노드에 없다. 역슬래시로 쓴 `\[1\]` 은 글자
// 노드의 값에서 구별되지 않아, 원문의 그 범위에 `\[` 가 있는 글자 노드는 통째로 건너뛴다.
import type { Emphasis, Nodes, PhrasingContent, Root, Text } from "mdast";
import { forEachPhrasingParent, sourceOf, sourceRange, text } from "./tree";

export interface CitationRule {
  /** 바로 앞 글자가 ASCII 영문자·숫자·밑줄이면 번호로 보지 않는다(`a[1]`, `arr[0]`). 그렇게 건너뛴 것에 바로 붙은 `[숫자]` 도 건너뛴다(`A[1][2]`). */
  readonly skipAfterWordChar: boolean;
  /** 그 줄의 끝까지 공백·문장부호·다른 `[숫자]` 뿐일 때만 번호로 본다. */
  readonly onlyAtLineEnd: boolean;
  /** 줄 머리(블록의 처음, 줄바꿈 바로 뒤)의 `[숫자]` 는 번호로 보지 않는다(`[1] 문서 이름`). */
  readonly skipAtLineStart: boolean;
  /** 링크 글 안은 건너뛴다. */
  readonly skipInLink: boolean;
  /** 이 자릿수를 넘는 숫자는 번호로 보지 않는다(`[2026]`). */
  readonly maxDigits: number;
}

const MARKER = /\[(\d+)\]/g;
const WORD_CHAR = /[A-Za-z0-9_]/;
const LINE_END = /[\r\n]/;
const TRAILING_ONLY = /^(?:[\s.,;:!?…。、)\]」』"'”’]|\[\d+\])*$/;

/** 글자 노드 앞뒤의 형편. 줄 머리인지와 줄 끝인지를 이웃 노드로 안다. */
interface Surroundings {
  /** 이 글자 노드가 줄 머리에서 시작하는가(블록의 처음이거나 앞이 줄바꿈 노드다). */
  readonly startsLine: boolean;
  /** 이 글자 노드가 줄 끝에서 끝나는가(블록의 끝이거나 뒤가 줄바꿈 노드다). */
  readonly endsLine: boolean;
}

function superscript(digits: string): Emphasis {
  return { type: "emphasis", data: { hName: "sup", hProperties: { dataCite: "" } }, children: [text(digits)] };
}

function rewrite(node: Text, around: Surroundings, rule: CitationRule): PhrasingContent[] {
  const value = node.value;
  const pieces: PhrasingContent[] = [];
  let last = 0;
  let skippedEnd = -1;
  for (const match of value.matchAll(MARKER)) {
    const digits = match[1] ?? "";
    const start = match.index;
    const end = start + match[0].length;
    const lineStart = Math.max(value.lastIndexOf("\n", start - 1), value.lastIndexOf("\r", start - 1)) + 1;
    const beforeOnLine = value.slice(lineStart, start);
    const atLineStart = beforeOnLine.trim() === "" && (lineStart > 0 || around.startsLine);
    const restOfLine = value.slice(end).split(LINE_END, 1)[0] ?? "";
    const lineContinuesPastNode = !LINE_END.test(value.slice(end)) && !around.endsLine;
    const previous = start > 0 ? value[start - 1] : undefined;
    const refused =
      digits.length > rule.maxDigits ||
      (rule.skipAfterWordChar && ((previous !== undefined && WORD_CHAR.test(previous)) || skippedEnd === start)) ||
      (rule.skipAtLineStart && atLineStart) ||
      (rule.onlyAtLineEnd && (lineContinuesPastNode || !TRAILING_ONLY.test(restOfLine)));
    if (refused) {
      skippedEnd = end;
      continue;
    }
    const before = value.slice(last, start).replace(/[ \t]+$/, "");
    if (before !== "") pieces.push(text(before));
    pieces.push(superscript(digits));
    last = end;
  }
  if (last === 0) return [node];
  if (last < value.length) pieces.push(text(value.slice(last)));
  return pieces;
}

function escapedBracket(node: Text, source: string): boolean {
  const range = sourceRange(node);
  return range !== null && source.slice(range.start, range.end).includes("\\[");
}

/** 위첨자로 바꾼 번호의 수를 돌려준다. `skip` 이 참인 노드는 그 아래까지 건너뛴다(출처 덩이 등). */
export function citationsToSuperscript(
  tree: Root,
  source: string,
  rule: CitationRule,
  skip: (node: Nodes) => boolean = () => false,
): number {
  let count = 0;
  const skipNode = (node: Nodes): boolean =>
    skip(node) || (rule.skipInLink && (node.type === "link" || node.type === "linkReference"));
  forEachPhrasingParent(
    tree,
    (parent) => {
      if (!parent.children.some((child) => child.type === "text" && child.value.includes("["))) return;
      const next: PhrasingContent[] = [];
      parent.children.forEach((child, index) => {
        if (child.type !== "text" || escapedBracket(child, source)) {
          next.push(child);
          return;
        }
        const before = parent.children[index - 1];
        const after = parent.children[index + 1];
        const pieces = rewrite(
          child,
          {
            startsLine: before === undefined || before.type === "break",
            endsLine: after === undefined || after.type === "break",
          },
          rule,
        );
        count += pieces.filter((piece) => piece.type === "emphasis").length;
        next.push(...pieces);
      });
      parent.children = next;
    },
    skipNode,
  );
  return count;
}

export function remarkCitations(rule: CitationRule): (tree: Root, file: { readonly value: unknown }) => undefined {
  return (tree, file) => {
    citationsToSuperscript(tree, sourceOf(file), rule);
  };
}
