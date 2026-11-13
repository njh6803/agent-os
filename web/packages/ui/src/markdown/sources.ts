// 출력 끝의 출처 덩이를 `div` 하나로 감싸는 변환(명세 "출처 덩이", 변환의 차례 5).
//
// 출처 덩이는 출력 최상위의 마지막 두 블록인 표지와 목록이다.
// - 표지는 글이 "출처"인 한 줄이다. 콜론이 붙은 `출처:`, 굵게나 기울임으로 두른 `**출처**`, 제목 `## 출처` 도 표지다.
//   앞 문단의 마지막 줄로 붙은 `출처`(사이에 빈 줄이 없어 파서가 한 문단으로 읽었다)는 문단을 갈라 표지로 본다.
// - 목록은 번호 목록이거나, 줄마다 `[숫자]` 로 시작하는 문단이다. 표지와 `[숫자]` 줄들이 한 문단으로 붙은 것도 갈라 본다.
// 번호 없는 글머리 목록, 목록 뒤에 블록이 더 있는 것, 출력 가운데나 인용·목록 안의 "출처"는 알아보지 않는다.
//
// 감싸는 노드는 인용(`blockquote`)에 `hName: "div"` 와 표지를 얹은 것이다. mdast 에 이름 없는 묶음 노드가 없어 블록을 품는
// 노드 하나를 빌린다. 부품은 표지(`data-sources`)가 있는 `div` 만 그리고 표지를 DOM 에 넘기지 않는다. 한 줄 바꿈의 변환
// (차례 7)보다 먼저 돌므로 문단의 줄은 글자 노드의 줄 끝 글자와 줄바꿈 노드(`break`, 줄 끝의 공백 둘이나 역슬래시) 둘 다로
// 가른다.
//
// 문단을 가를 때 표지 앞의 본문은 원래 노드를 그대로 두고, 표지 줄에 걸친 글자 노드 하나만 잘라 원문의 위치를 그 줄 끝까지로
// 옮긴다. 문장 끝 번호의 변환(차례 6)이 그 위치로 역슬래시로 쓴 대괄호를 알아보기 때문이다.
import type {
  Blockquote,
  Heading,
  List,
  Nodes,
  Paragraph,
  PhrasingContent,
  Root,
  Text,
} from "mdast";
import { hastName, mergeText, plainText, sourceRange, text } from "./tree";

/** 원문 위치의 한 점. `unist` 의 `Point` 를 직접 들이지 않고 mdast 노드의 위치에서 꺼낸다. */
type Point = NonNullable<Text["position"]>["start"];

/** 문단 안의 줄 끝 자리. `child` 는 그 줄 끝이 든 자식의 차례이고, `at` 은 글자 노드 안의 줄 끝 글자 자리다(줄바꿈 노드면 null). */
interface Cut {
  readonly child: number;
  readonly at: number | null;
}

/** 문단의 한 줄. `nodes` 는 그 줄의 줄 안 노드이고, `end` 는 그 줄을 끝낸 줄 끝이다(마지막 줄은 null). */
interface Line {
  readonly nodes: PhrasingContent[];
  readonly end: Cut | null;
}

const LINE_END = /\r\n|\n|\r/g;
const BRACKET_LINE = /^\s*\[\d+\]\s/;
const COLON_LABEL = /^출처\s*[:：]$/;

function toLines(children: readonly PhrasingContent[]): Line[] {
  const lines: Line[] = [];
  let current: PhrasingContent[] = [];
  children.forEach((child, index) => {
    if (child.type === "break") {
      lines.push({ nodes: current, end: { child: index, at: null } });
      current = [];
      return;
    }
    if (child.type !== "text") {
      current.push(child);
      return;
    }
    let last = 0;
    for (const match of child.value.matchAll(LINE_END)) {
      if (match.index > last) current.push(text(child.value.slice(last, match.index)));
      lines.push({ nodes: current, end: { child: index, at: match.index } });
      current = [];
      last = match.index + match[0].length;
    }
    if (last === 0) current.push(child);
    else if (last < child.value.length) current.push(text(child.value.slice(last)));
  });
  lines.push({ nodes: current, end: null });
  return lines;
}

/** 줄들을 다시 한 문단의 자식으로 잇는다. 줄 사이에는 줄 끝 글자를 둔다. 출처 덩이 안에서만 쓰므로 위치를 잃어도 된다. */
function fromLines(lines: readonly Line[]): PhrasingContent[] {
  const children: PhrasingContent[] = [];
  lines.forEach((line, index) => {
    if (index > 0) children.push(text("\n"));
    children.push(...line.nodes);
  });
  return mergeText(children);
}

function countLineEnds(value: string): number {
  return [...value.matchAll(LINE_END)].length;
}

/**
 * 글자 노드의 값을 `at` 앞까지로 자른다. `at` 은 값 안의 줄 끝 글자 자리다. 값과 원문 범위의 줄 끝 글자 수가 같으면 같은
 * 차례의 원문 줄 끝 글자까지를 새 위치로 준다. 수가 다르면(문자 참조 `&#10;` 이 값에 줄 끝 글자를 넣었다) 위치를 두지 않는다.
 */
function truncate(node: Text, at: number, source: string): Text {
  const cut = text(node.value.slice(0, at));
  const range = sourceRange(node);
  const start = node.position?.start;
  if (range === null || start === undefined) return cut;
  const slice = source.slice(range.start, range.end);
  if (countLineEnds(slice) !== countLineEnds(node.value)) return cut;
  const kept = countLineEnds(cut.value);
  let lineStart = 0;
  let end = 0;
  let line = 0;
  for (const match of slice.matchAll(LINE_END)) {
    if (line === kept) {
      end = match.index;
      break;
    }
    line += 1;
    lineStart = match.index + match[0].length;
  }
  const endPoint: Point = {
    line: start.line + kept,
    column: kept === 0 ? start.column + end : end - lineStart + 1,
    offset: range.start + end,
  };
  return { ...cut, position: { start, end: endPoint } };
}

/** 문단에서 줄 끝 `cut` 앞의 자식. 그 줄 끝이 글자 노드 안이면 그 노드를 잘라 넣는다. */
function childrenBefore(
  children: readonly PhrasingContent[],
  cut: Cut,
  source: string,
): PhrasingContent[] {
  const kept = children.slice(0, cut.child);
  const node = children[cut.child];
  if (cut.at !== null && cut.at > 0 && node?.type === "text")
    kept.push(truncate(node, cut.at, source));
  return kept;
}

function isLabelText(value: string): boolean {
  const trimmed = value.trim();
  return trimmed === "출처" || COLON_LABEL.test(trimmed);
}

/** 줄 안 노드들이 "출처" 표지 한 줄인가. */
function isLabel(nodes: readonly PhrasingContent[]): boolean {
  const meaningful = nodes.filter((node) => node.type !== "text" || node.value.trim() !== "");
  const only = meaningful.length === 1 ? meaningful[0] : undefined;
  if (only === undefined) return false;
  if (only.type === "text") return isLabelText(only.value);
  if (only.type === "strong" || only.type === "emphasis") return isLabelText(plainText(only));
  return false;
}

function isBracketLine(line: Line | undefined): boolean {
  const first = line?.nodes[0];
  return first?.type === "text" && BRACKET_LINE.test(first.value);
}

function paragraph(children: PhrasingContent[]): Paragraph {
  return { type: "paragraph", children };
}

/** 출처 덩이의 표지. 부품의 허용 목록이 이 속성이 있는 `div` 만 들인다. hast 속성 이름이고 DOM 의 `data-sources` 다. */
export const SOURCES_PROPERTY = "dataSources";

function sourcesBlock(label: Heading | Paragraph, body: List | Paragraph): Blockquote {
  // `hName`·`hProperties` 는 mdast-util-to-hast 가 `Data` 에 더하는 키인데 이 패키지의 타입에는 들지 않는다.
  const data: Record<string, unknown> = {
    hName: "div",
    hProperties: { [SOURCES_PROPERTY]: "true" },
  };
  return { type: "blockquote", data, children: [label, body] };
}

/** 이 변환이 감싼 출처 덩이인가. 문장 끝 번호의 변환이 그 아래를 건너뛸 때 쓴다. */
export function isSourcesBlock(node: Nodes): boolean {
  return node.type === "blockquote" && hastName(node) === "div";
}

/**
 * 목록 블록 `body` 의 바로 앞 블록이 표지이면 둘을 바꿔 넣을 블록들을 낸다. 앞 블록은 표지인 제목이나 문단이거나, 마지막
 * 줄이 표지인 문단이다. 뒤의 것은 문단을 갈라 표지 앞의 본문을 문단으로 남긴다.
 */
function labelBefore(
  previous: Nodes | undefined,
  body: List | Paragraph,
  source: string,
): Root["children"] | null {
  if (previous?.type === "heading")
    return isLabel(previous.children) ? [sourcesBlock(previous, body)] : null;
  if (previous?.type !== "paragraph") return null;
  const lines = toLines(previous.children);
  const labelLine = lines.at(-1);
  if (labelLine === undefined || !isLabel(labelLine.nodes)) return null;
  const cut = lines.at(-2)?.end;
  if (cut === undefined || cut === null) return [sourcesBlock(previous, body)];
  return [
    paragraph(childrenBefore(previous.children, cut, source)),
    sourcesBlock(paragraph(mergeText(labelLine.nodes)), body),
  ];
}

/** 마지막 블록이 문단일 때. `[숫자]` 줄들로 끝나고 그 바로 앞이 표지이면 바꿔 넣을 블록들과 바꿀 블록 수를 낸다. */
function bracketParagraph(
  previous: Nodes | undefined,
  last: Paragraph,
  source: string,
): { readonly replace: 1 | 2; readonly nodes: Root["children"] } | null {
  const lines = toLines(last.children);
  let firstBracket = lines.length;
  while (firstBracket > 0 && isBracketLine(lines[firstBracket - 1])) firstBracket -= 1;
  if (firstBracket === lines.length) return null;
  const sources = paragraph(fromLines(lines.slice(firstBracket)));
  if (firstBracket === 0) {
    // 문단 전체가 `[숫자]` 줄이다. 표지는 앞 블록이다.
    const nodes = labelBefore(previous, sources, source);
    return nodes === null ? null : { replace: 2, nodes };
  }
  const labelLine = lines[firstBracket - 1];
  if (labelLine === undefined || !isLabel(labelLine.nodes)) return null;
  const label = paragraph(mergeText(labelLine.nodes));
  const cut = lines[firstBracket - 2]?.end;
  if (cut === undefined || cut === null)
    return { replace: 1, nodes: [sourcesBlock(label, sources)] };
  return {
    replace: 1,
    nodes: [paragraph(childrenBefore(last.children, cut, source)), sourcesBlock(label, sources)],
  };
}

export function wrapSources(tree: Root, source: string): void {
  const last = tree.children.at(-1);
  const previous = tree.children.at(-2);
  if (last?.type === "list") {
    const nodes = last.ordered === true ? labelBefore(previous, last, source) : null;
    if (nodes !== null) tree.children.splice(-2, 2, ...nodes);
    return;
  }
  if (last?.type === "paragraph") {
    const found = bracketParagraph(previous, last, source);
    if (found !== null) tree.children.splice(-found.replace, found.replace, ...found.nodes);
  }
}
