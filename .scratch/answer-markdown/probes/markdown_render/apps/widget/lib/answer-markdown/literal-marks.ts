// (다) 후보 ①·②: 파싱 뒤의 mdast 변환. 숫자 사이의 별표와 밑줄(`_`)로 두른 강조를 서식 기호로 읽지 않고 글자로 둔다.
//
// 파서가 낸 `emphasis`·`strong` 노드의 위치(`position` 의 오프셋)로 원문을 들여다보아 구분 기호를 안다. 오프셋은 원문
// 문자열의 UTF-16 자리다(micromark 가 줄 끝과 탭의 가짜 공백을 원문 자리에 맞춰 센다). 구분 기호가 `_` 이면 언제나,
// `*` 이면 규칙에 맞을 때 그 노드를 벗겨 구분 기호 글자와 자식을 그대로 남긴다.
//
// 별표 규칙은 "묶음"으로 본다. 묶음은 이어진 같은 구분 기호 전체다(`2***3***4` 의 `***`). 겹친 `emphasis`·`strong` 이
// 한 묶음을 나눠 가져도 같은 앞뒤 글자를 본다.
// - between-digits(R2): 여는 묶음과 닫는 묶음이 둘 다 바로 앞뒤 글자가 ASCII 숫자다.
// - outer-digits(R1): 여는 묶음의 바로 앞과 닫는 묶음의 바로 뒤가 ASCII 숫자다.
//
// 위치가 없는 노드(다른 변환이 만든 것)와, 위치의 글자가 구분 기호가 아닌 노드는 건드리지 않고 `skipped` 에 센다.
import type { Emphasis, PhrasingContent, Root, Strong } from "mdast";
import { forEachPhrasingParent, mergeText, sourceOf, sourceRange, text } from "./tree";

export type DigitRule = "between-digits" | "outer-digits";

export interface LiteralMarksReport {
  /** 벗긴 노드 수. */
  unwrapped: number;
  /** 규칙에 맞지 않아 둔 노드 수. */
  kept: number;
  /** 위치가 없거나 위치의 글자가 구분 기호가 아니어서 판정하지 못한 노드 수. */
  skipped: number;
}

const DIGIT = /^[0-9]$/;

function isDigit(char: string | undefined): boolean {
  return char !== undefined && DIGIT.test(char);
}

/** `index` 에서 `step` 방향으로 `mark` 가 아닌 첫 글자. */
function beyondRun(source: string, index: number, step: 1 | -1, mark: string): string | undefined {
  let at = index;
  while (source[at] === mark) at += step;
  return source[at];
}

type Verdict = { readonly kind: "unwrap"; readonly mark: string } | { readonly kind: "keep" | "skip" };

function judge(node: Emphasis | Strong, source: string, rule: DigitRule): Verdict {
  const range = sourceRange(node);
  if (range === null) return { kind: "skip" };
  const width = node.type === "strong" ? 2 : 1;
  const mark = source[range.start];
  if (mark !== "*" && mark !== "_") return { kind: "skip" };
  const open = source.slice(range.start, range.start + width);
  const close = source.slice(range.end - width, range.end);
  if (open !== mark.repeat(width) || close !== open) return { kind: "skip" };
  if (mark === "_") return { kind: "unwrap", mark };
  const beforeOpen = beyondRun(source, range.start, -1, mark);
  const afterOpen = beyondRun(source, range.start, 1, mark);
  const beforeClose = beyondRun(source, range.end - 1, -1, mark);
  const afterClose = beyondRun(source, range.end - 1, 1, mark);
  const outer = isDigit(beforeOpen) && isDigit(afterClose);
  const inner = isDigit(afterOpen) && isDigit(beforeClose);
  const literal = rule === "outer-digits" ? outer : outer && inner;
  return literal ? { kind: "unwrap", mark } : { kind: "keep" };
}

export function literalizeMarks(tree: Root, source: string, rule: DigitRule): LiteralMarksReport {
  const report: LiteralMarksReport = { unwrapped: 0, kept: 0, skipped: 0 };
  forEachPhrasingParent(tree, (parent) => {
    // 벗긴 노드의 자식에 또 벗길 노드가 있을 수 있어(`___x___`), 더 벗길 것이 없을 때까지 이 부모에서 되풀이한다.
    for (let changed = true; changed; ) {
      changed = false;
      const next: PhrasingContent[] = [];
      for (const child of parent.children) {
        if (child.type !== "emphasis" && child.type !== "strong") {
          next.push(child);
          continue;
        }
        const verdict = judge(child, source, rule);
        if (verdict.kind === "unwrap") {
          const marks = verdict.mark.repeat(child.type === "strong" ? 2 : 1);
          next.push(text(marks), ...child.children, text(marks));
          report.unwrapped += 1;
          changed = true;
        } else {
          next.push(child);
        }
      }
      if (changed) parent.children = mergeText(next);
    }
  });
  // 남은 노드를 한 번 더 돌며 센다(위의 되풀이는 벗긴 것만 센다).
  forEachPhrasingParent(tree, (parent) => {
    for (const child of parent.children) {
      if (child.type !== "emphasis" && child.type !== "strong") continue;
      if (judge(child, source, rule).kind === "skip") report.skipped += 1;
      else report.kept += 1;
    }
  });
  return report;
}

export function remarkLiteralMarks(rule: DigitRule): (tree: Root, file: { readonly value: unknown }) => undefined {
  return (tree, file) => {
    literalizeMarks(tree, sourceOf(file), rule);
  };
}
