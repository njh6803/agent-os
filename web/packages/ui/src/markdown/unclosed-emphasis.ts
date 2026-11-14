// 닫히지 않은 굵게와 기울임을 되살리는 변환(명세 "한국어에서 닫히지 않는 굵게", 변환의 차례 2).
//
// 표준 마크다운은 닫는 별표 앞이 문장부호이고 뒤가 글자이면(`**민법 제750조(불법행위)**는`) 그 별표를 닫는 기호로 읽지
// 않는다. 그 별표와 짝이 될 여는 별표는 글자 노드에 그대로 남는다. 이 변환은 파서가 이미 짝지은 강조는 건드리지 않고, 글자로
// 남은 별표 묶음만 느슨한 조건으로 다시 짝짓는다.
// - 묶음은 이어진 별표 전체이고, 길이가 1(기울임)이나 2(굵게)인 것만 본다.
// - 여는 묶음은 바로 뒤가 공백이 아니어야 하고, 닫는 묶음은 바로 앞이 공백이 아니어야 한다. 둘 사이는 비지 않아야 한다.
//   두 묶음의 길이가 같아야 한다.
// - 같은 부모의 자식 안에서만 짝짓는다(링크 글 안의 별표는 링크 밖의 별표와 짝이 되지 않는다).
// - 닫는 묶음은 그 앞의 같은 길이 여는 묶음 가운데 가장 가까운 것과 짝짓고, 짝끼리 엇갈리지 않는다.
// - 여는 묶음의 바로 앞과 닫는 묶음의 바로 뒤가 둘 다 ASCII 숫자인 짝은 짓지 않는다(`2*(3+4)*5`). 숫자 사이 기호의 변환
//   (차례 3)이 글자로 둘 모양인데, 이 변환이 지은 강조에는 위치가 없어 차례 3이 판정하지 못하기 때문이다.
// 역슬래시나 문자 참조로 쓴 별표(`\*`, `&#42;`)는 글자 노드의 값에서 보통 별표와 구별되지 않는다. 그래서 원문의 그 범위에
// 그런 표기가 있는 글자 노드와, 위치가 없는 글자 노드(다른 변환이 만든 것)는 통째로 건너뛴다. 밑줄은 다시 짝짓지 않는다
// (숫자 사이 기호의 변환이 밑줄 강조를 늘 글자로 둔다).
//
// 받아들이는 한계: 파서가 이미 엉뚱하게 짝지은 것은 고치지 못한다(`**가(1)**는 나**다** 끝` 의 가운데 둘). 글자로 쓴 별표
// 둘이 굵게로 짝지어지기도 한다(`src/**(전부)와 test/**`).
import type { PhrasingContent, Root, Text } from "mdast";
import { forEachPhrasingParent, isAsciiDigit, mergeText, sourceRange, text } from "./tree";

type Width = 1 | 2;
type Piece =
  | { readonly kind: "node"; readonly node: PhrasingContent }
  | { readonly kind: "run"; readonly width: Width };

const ESCAPED_ASTERISK = /\\\*|&(?:#0*42|#[xX]0*2[aA]|ast|midast);/;
const ASTERISKS = /\*+/g;

function eligible(node: Text, source: string): boolean {
  const range = sourceRange(node);
  return range !== null && !ESCAPED_ASTERISK.test(source.slice(range.start, range.end));
}

/** 자식을 노드 조각과 별표 묶음 조각으로 나눈다. 다시 짝지을 수 없는 글자 노드는 통째로 노드 조각이다. */
function split(children: readonly PhrasingContent[], source: string): Piece[] {
  const pieces: Piece[] = [];
  for (const child of children) {
    if (child.type !== "text" || !eligible(child, source)) {
      pieces.push({ kind: "node", node: child });
      continue;
    }
    let last = 0;
    for (const match of child.value.matchAll(ASTERISKS)) {
      const width = match[0].length;
      if (width !== 1 && width !== 2) continue;
      if (match.index > last) {
        pieces.push({ kind: "node", node: text(child.value.slice(last, match.index)) });
      }
      pieces.push({ kind: "run", width });
      last = match.index + width;
    }
    if (last === 0) pieces.push({ kind: "node", node: child });
    else if (last < child.value.length) {
      pieces.push({ kind: "node", node: text(child.value.slice(last)) });
    }
  }
  return pieces;
}

/** 묶음 바로 옆의 조각이 묶음에 붙은 글(공백이 아닌 것)인가. `edge` 는 그 조각에서 묶음 쪽 끝이다. */
function hugs(piece: Piece | undefined, edge: "start" | "end"): boolean {
  if (piece?.kind !== "node" || piece.node.type === "break") return false;
  if (piece.node.type !== "text") return true;
  return edge === "start" ? !/^\s/.test(piece.node.value) : !/\s$/.test(piece.node.value);
}

/** 조각에서 묶음 쪽 끝의 글자. 글자 노드가 아니면 undefined 다. */
function edgeChar(piece: Piece | undefined, edge: "start" | "end"): string | undefined {
  if (piece?.kind !== "node" || piece.node.type !== "text") return undefined;
  const value = piece.node.value;
  return edge === "start" ? value.at(0) : value.at(-1);
}

/** 여는 묶음의 바로 앞과 닫는 묶음의 바로 뒤가 둘 다 ASCII 숫자인가. */
function betweenDigits(pieces: readonly Piece[], opener: number, closer: number): boolean {
  return (
    isAsciiDigit(edgeChar(pieces[opener - 1], "end")) &&
    isAsciiDigit(edgeChar(pieces[closer + 1], "start"))
  );
}

/** 여는 묶음의 자리에서 닫는 묶음의 자리로 가는 짝. 짝끼리 엇갈리지 않는다. */
function pair(pieces: readonly Piece[]): Map<number, number> {
  const pairs = new Map<number, number>();
  const open: Record<Width, number | null> = { 1: null, 2: null };
  pieces.forEach((piece, index) => {
    if (piece.kind !== "run") return;
    const opener = open[piece.width];
    if (
      opener !== null &&
      index - opener > 1 &&
      hugs(pieces[index - 1], "end") &&
      !betweenDigits(pieces, opener, index)
    ) {
      pairs.set(opener, index);
      open[piece.width] = null;
      // 이 짝 안에서 열리고 닫히지 않은 다른 길이의 묶음은 글자로 남긴다(짝이 엇갈리지 않게).
      const other: Width = piece.width === 1 ? 2 : 1;
      const otherOpener = open[other];
      if (otherOpener !== null && otherOpener > opener) open[other] = null;
    } else if (hugs(pieces[index + 1], "start")) {
      open[piece.width] = index;
    }
  });
  return pairs;
}

interface Frame {
  readonly width: Width;
  readonly close: number;
  readonly children: PhrasingContent[];
}

/** 조각을 다시 자식 노드로 짓는다. 짝지은 묶음은 굵게나 기울임으로 감싸고, 짝이 없는 묶음은 별표 글자로 남긴다. */
function build(pieces: readonly Piece[], pairs: ReadonlyMap<number, number>): PhrasingContent[] {
  const top: PhrasingContent[] = [];
  const frames: Frame[] = [];
  const into = (): PhrasingContent[] => frames.at(-1)?.children ?? top;
  pieces.forEach((piece, index) => {
    const frame = frames.at(-1);
    if (frame !== undefined && frame.close === index) {
      frames.pop();
      const children = mergeText(frame.children);
      into().push(
        frame.width === 2 ? { type: "strong", children } : { type: "emphasis", children },
      );
      return;
    }
    if (piece.kind === "node") {
      into().push(piece.node);
      return;
    }
    const close = pairs.get(index);
    if (close === undefined) into().push(text("*".repeat(piece.width)));
    else frames.push({ width: piece.width, close, children: [] });
  });
  return mergeText(top);
}

export function recoverUnclosedEmphasis(tree: Root, source: string): void {
  forEachPhrasingParent(tree, (parent) => {
    if (!parent.children.some((child) => child.type === "text" && child.value.includes("*"))) {
      return;
    }
    const pieces = split(parent.children, source);
    const pairs = pair(pieces);
    if (pairs.size === 0) return;
    parent.children = build(pieces, pairs);
  });
}
