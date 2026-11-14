// 숫자 사이 기호를 글자로 두는 변환(명세 "숫자 사이의 별표와 밑줄", 변환의 차례 3).
//
// 파서가 낸 기울임·굵게 노드의 위치로 원문을 들여다보아 구분 기호를 안다. 구분 기호가 밑줄이면 언제나, 별표이면 여는
// 묶음의 바로 앞과 닫는 묶음의 바로 뒤가 둘 다 ASCII 숫자일 때(`2*3*4`) 그 노드를 벗긴다. 벗긴 자리에는 구분 기호 글자와
// 자식이 그대로 남는다. 묶음은 이어진 같은 구분 기호 전체다(`2***3***4` 의 `***`). 겹친 기울임과 굵게가 한 묶음을 나눠
// 가져도 같은 앞뒤 글자를 본다.
//
// 위치가 없는 노드(닫히지 않는 굵게의 변환이 만든 것)와, 위치의 글자가 구분 기호가 아닌 노드는 건드리지 않는다.
import type { Emphasis, PhrasingContent, Root, Strong } from "mdast";
import { forEachPhrasingParent, isAsciiDigit, mergeText, sourceRange, text } from "./tree";

/**
 * 원문의 별표 묶음마다 그 묶음의 바로 앞과 바로 뒤 글자를 찾는다. 겹친 강조(`2****x****3`)는 한 묶음을 여러 노드가 나눠
 * 가지므로, 노드마다 묶음을 걸어 끝을 찾으면 별표 수의 제곱만큼 걷는다. 그래서 원문을 처음 물을 때 한 번 훑어 자리마다 묶음의
 * 시작과 끝을 적어 두고, 그 뒤로는 적은 값을 읽는다.
 */
class StarRuns {
  private readonly source: string;
  private starts: Int32Array | null = null;
  private ends: Int32Array | null = null;

  constructor(source: string) {
    this.source = source;
  }

  /** `index` 의 별표가 든 묶음의 바로 앞 글자. */
  charBefore(index: number): string | undefined {
    return this.source[this.table().starts[index] ?? index - 1];
  }

  /** `index` 의 별표가 든 묶음의 바로 뒤 글자. */
  charAfter(index: number): string | undefined {
    return this.source[this.table().ends[index] ?? index + 1];
  }

  /** 자리마다 묶음의 바로 앞 자리(`starts`)와 바로 뒤 자리(`ends`). 별표가 아닌 자리의 값은 쓰지 않는다. */
  private table(): { readonly starts: Int32Array; readonly ends: Int32Array } {
    if (this.starts === null || this.ends === null) {
      const length = this.source.length;
      const starts = new Int32Array(length);
      const ends = new Int32Array(length);
      for (let at = 0; at < length; at += 1)
        starts[at] = this.source[at - 1] === "*" ? (starts[at - 1] ?? at - 1) : at - 1;
      for (let at = length - 1; at >= 0; at -= 1)
        ends[at] = this.source[at + 1] === "*" ? (ends[at + 1] ?? at + 1) : at + 1;
      this.starts = starts;
      this.ends = ends;
    }
    return { starts: this.starts, ends: this.ends };
  }
}

/** 벗길 노드면 그 구분 기호 글자를, 둘 노드면 null 을 낸다. */
function literalMark(node: Emphasis | Strong, source: string, runs: StarRuns): string | null {
  const range = sourceRange(node);
  if (range === null) return null;
  const width = node.type === "strong" ? 2 : 1;
  const mark = source[range.start];
  if (mark !== "*" && mark !== "_") return null;
  const open = source.slice(range.start, range.start + width);
  const close = source.slice(range.end - width, range.end);
  if (open !== mark.repeat(width) || close !== open) return null;
  if (mark === "_") return open;
  const beforeOpen = runs.charBefore(range.start);
  const afterClose = runs.charAfter(range.end - 1);
  return isAsciiDigit(beforeOpen) && isAsciiDigit(afterClose) ? open : null;
}

export function literalizeMarks(tree: Root, source: string): void {
  const runs = new StarRuns(source);
  forEachPhrasingParent(tree, (parent) => {
    // 벗긴 노드의 자식에 또 벗길 노드가 있을 수 있어(`___x___`), 더 벗길 것이 없을 때까지 이 부모에서 되풀이한다.
    for (let changed = true; changed;) {
      changed = false;
      const next: PhrasingContent[] = [];
      for (const child of parent.children) {
        if (child.type === "emphasis" || child.type === "strong") {
          const marks = literalMark(child, source, runs);
          if (marks !== null) {
            next.push(text(marks), ...child.children, text(marks));
            changed = true;
            continue;
          }
        }
        next.push(child);
      }
      if (changed) parent.children = mergeText(next);
    }
  });
}
