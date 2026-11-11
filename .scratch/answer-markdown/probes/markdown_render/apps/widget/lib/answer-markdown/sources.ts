// (마) 출력 끝의 "출처" 덩이를 알아보아 한 요소(`div.sources`)로 감싸는 변환. 어떤 글을 출처 덩이로 볼지는 규칙
// (`SourcesRule`)이 정하고, 프로브가 규칙을 바꿔 가며 같은 입력을 견준다.
//
// 기본 꼴은 문서의 마지막 최상위 노드 둘이 "글이 `출처` 인 한 줄짜리 문단"과 "번호 목록"인 것이다. 규칙의 칸마다 그
// 꼴을 하나씩 넓힌다. 감싸는 노드는 `blockquote` 에 `hName: "div"` 를 얹은 것이다(mdast 에 이름 없는 묶음 노드가 없어
// 블록을 품는 노드 하나를 빌린다).
//
// 줄바꿈 변환(soft-breaks.ts)보다 먼저 돌아도 뒤에 돌아도 된다. 문단의 줄은 글자 노드의 줄 끝 글자와 `break` 노드
// 둘 다로 가른다.
import type { Blockquote, Heading, List, Nodes, Paragraph, PhrasingContent, Root } from "mdast";
import { mergeText, plainText, text } from "./tree";

export interface SourcesRule {
  /** "출처" 줄이 제목(`## 출처`)이어도 알아본다. */
  readonly heading: boolean;
  /** "출처" 가 굵게나 기울임으로 싸여 있어도(`**출처**`) 알아본다. */
  readonly emphasized: boolean;
  /** 콜론이 붙어도(`출처:`) 알아본다. */
  readonly colon: boolean;
  /** 번호 없는 목록도 알아본다. */
  readonly unorderedList: boolean;
  /** "출처" 가 앞 문단의 마지막 줄이면 문단을 갈라 알아본다. */
  readonly splitTrailingLine: boolean;
  /** 목록이 아니라 `[1] …` 꼴의 줄들이어도 알아본다. */
  readonly bracketLines: boolean;
}

/** 문단의 한 줄. `end` 는 그 줄을 끝낸 것(줄 끝 글자를 든 글자 노드나 `break` 노드)이고 마지막 줄은 null 이다. */
interface Line {
  readonly nodes: PhrasingContent[];
  readonly end: PhrasingContent | null;
}

const LINE_END = /\r\n|\n|\r/g;
const BRACKET_LINE = /^\s*\[\d+\]\s/;

function toLines(children: readonly PhrasingContent[]): Line[] {
  const lines: Line[] = [];
  let current: PhrasingContent[] = [];
  for (const child of children) {
    if (child.type === "break") {
      lines.push({ nodes: current, end: child });
      current = [];
    } else if (child.type === "text") {
      let last = 0;
      for (const match of child.value.matchAll(LINE_END)) {
        if (match.index > last) current.push(text(child.value.slice(last, match.index)));
        lines.push({ nodes: current, end: text(match[0]) });
        current = [];
        last = match.index + match[0].length;
      }
      if (last === 0) current.push(child);
      else if (last < child.value.length) current.push(text(child.value.slice(last)));
    } else {
      current.push(child);
    }
  }
  lines.push({ nodes: current, end: null });
  return lines;
}

function fromLines(lines: readonly Line[]): PhrasingContent[] {
  const children: PhrasingContent[] = [];
  lines.forEach((line, index) => {
    children.push(...line.nodes);
    if (line.end !== null && index < lines.length - 1) children.push(line.end);
  });
  return mergeText(children);
}

function isLabelText(value: string, rule: SourcesRule): boolean {
  const trimmed = value.trim();
  return trimmed === "출처" || (rule.colon && /^출처\s*[:：]$/.test(trimmed));
}

/** 줄 안 노드들이 "출처" 표지 한 줄인가. */
function isLabel(nodes: readonly PhrasingContent[], rule: SourcesRule): boolean {
  const meaningful = nodes.filter((node) => node.type !== "text" || node.value.trim() !== "");
  const only = meaningful.length === 1 ? meaningful[0] : undefined;
  if (only === undefined) return false;
  if (only.type === "text") return isLabelText(only.value, rule);
  if (rule.emphasized && (only.type === "strong" || only.type === "emphasis")) return isLabelText(plainText(only), rule);
  return false;
}

function isBracketLine(line: Line): boolean {
  const first = line.nodes[0];
  return first?.type === "text" && BRACKET_LINE.test(first.value);
}

function paragraph(children: PhrasingContent[]): Paragraph {
  return { type: "paragraph", children };
}

function wrap(label: Heading | Paragraph, body: List | Paragraph): Blockquote {
  return { type: "blockquote", data: { hName: "div", hProperties: { className: ["sources"] } }, children: [label, body] };
}

/** 이 변환이 감싼 출처 덩이인가. 다른 변환(번호 위첨자)이 그 아래를 건너뛸 때 쓴다. */
export function isSourcesBlock(node: Nodes): boolean {
  return node.type === "blockquote" && node.data?.hName === "div";
}

/** 마지막 노드가 목록일 때. 앞 노드가 표지이거나, 표지로 끝나는 문단이면 감싼 노드들을 돌려준다. */
function beforeList(previous: Nodes | undefined, list: List, rule: SourcesRule): Root["children"] | null {
  if (!(list.ordered === true || rule.unorderedList)) return null;
  if (previous?.type === "heading") {
    return rule.heading && isLabel(previous.children, rule) ? [wrap(previous, list)] : null;
  }
  if (previous?.type !== "paragraph") return null;
  const lines = toLines(previous.children);
  const lastLine = lines.at(-1);
  if (lastLine === undefined || !isLabel(lastLine.nodes, rule)) return null;
  if (lines.length === 1) return [wrap(previous, list)];
  if (!rule.splitTrailingLine) return null;
  return [paragraph(fromLines(lines.slice(0, -1))), wrap(paragraph(lastLine.nodes), list)];
}

/** 마지막 노드가 문단일 때. `[1] …` 줄들로 끝나고 그 바로 앞이 표지이면 감싼 노드들을 돌려준다. */
function bracketParagraph(previous: Nodes | undefined, last: Paragraph, rule: SourcesRule): { readonly replace: 1 | 2; readonly nodes: Root["children"] } | null {
  if (!rule.bracketLines) return null;
  const lines = toLines(last.children);
  let firstBracket = lines.length;
  while (firstBracket > 0) {
    const line = lines[firstBracket - 1];
    if (line === undefined || !isBracketLine(line)) break;
    firstBracket -= 1;
  }
  if (firstBracket === lines.length) return null;
  const sources = paragraph(fromLines(lines.slice(firstBracket)));
  if (firstBracket === 0) {
    // 문단 전체가 `[1] …` 줄이다. 표지는 앞 노드여야 한다.
    if (previous?.type === "heading" && rule.heading && isLabel(previous.children, rule)) {
      return { replace: 2, nodes: [wrap(previous, sources)] };
    }
    if (previous?.type === "paragraph" && isLabel(previous.children, rule)) {
      return { replace: 2, nodes: [wrap(previous, sources)] };
    }
    return null;
  }
  const labelLine = lines[firstBracket - 1];
  if (labelLine === undefined || !isLabel(labelLine.nodes, rule)) return null;
  const label = paragraph(labelLine.nodes);
  if (firstBracket === 1) return { replace: 1, nodes: [wrap(label, sources)] };
  if (!rule.splitTrailingLine) return null;
  return { replace: 1, nodes: [paragraph(fromLines(lines.slice(0, firstBracket - 1))), wrap(label, sources)] };
}

/** 출처 덩이를 감쌌으면 true 다. */
export function wrapSources(tree: Root, rule: SourcesRule): boolean {
  const last = tree.children.at(-1);
  const previous = tree.children.at(-2);
  if (last?.type === "list") {
    const nodes = beforeList(previous, last, rule);
    if (nodes === null) return false;
    tree.children.splice(-2, 2, ...nodes);
    return true;
  }
  if (last?.type === "paragraph") {
    const found = bracketParagraph(previous, last, rule);
    if (found === null) return false;
    tree.children.splice(-found.replace, found.replace, ...found.nodes);
    return true;
  }
  return false;
}

export function remarkSources(rule: SourcesRule): (tree: Root) => undefined {
  return (tree) => {
    wrapSources(tree, rule);
  };
}
