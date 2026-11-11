// 던지는 단계 가르기. Node 의 자식(stage-node-entry.tsx)과 Chromium 의 묶음(browser-entry.tsx)이 함께 쓴다.
//
// 합친 시제품과 같은 옵션(`answerOptions`)으로 react-markdown 의 `Markdown` 을 직접 부르되, 플러그인 목록에 표지를
// 끼운다. 표지는 나무를 건드리지 않고 "여기까지 왔다"만 적는다.
//   parsed     첫 remark 변환기가 불렸다. 곧 파싱(micromark, mdast-util-from-markdown)이 끝났다.
//   own-done   직접 짠 변환(`remarkAnswer`)이 끝났다.
//   hast-done  첫 rehype 변환기가 불렸다. 곧 mdast→hast 변환(remark-rehype)이 끝났다.
//   returned   `Markdown` 이 React 요소를 돌려줬다. 곧 허용 목록 거르기와 JSX 로 바꾸기가 끝났다.
// 허용 목록 거르기와 JSX 로 바꾸기는 react-markdown 의 한 함수(`post`) 안이라 표지를 끼울 자리가 없다. 그 둘은 던진
// 오류의 스택 맨 위 프레임이 어느 패키지의 것인지로 가른다(부르는 쪽이 묶음의 줄 번호를 모듈로 옮긴다).
// `filterCalls` 는 거르기가 요소마다 부르는 `allowElement` 가 불린 횟수다.
import type { ReactNode } from "react";
import Markdown, { type Options } from "react-markdown";
import { ANSWER_PLUGINS, answerOptions } from "../apps/widget/components/molecules/AnswerMarkdown";

// 스택이 넘친 자리의 프레임을 넉넉히 받는다(V8 의 기본은 10이다).
Error.stackTraceLimit = 30;

export interface Thrown {
  readonly name: string;
  readonly message: string;
  readonly stack: string;
}

export function describeError(error: unknown): Thrown {
  if (error instanceof Error) {
    return { name: error.name, message: error.message.slice(0, 200), stack: error.stack ?? "" };
  }
  return { name: typeof error, message: String(error).slice(0, 200), stack: "" };
}

export interface MarkdownRun {
  readonly reached: readonly string[];
  readonly filterCalls: number;
  readonly thrown: Thrown | null;
  readonly element: ReactNode;
  readonly ms: number;
}

export function runMarkdown(text: string): MarkdownRun {
  const reached: string[] = [];
  let filterCalls = 0;
  const marker = (name: string) => (): (() => undefined) => () => {
    reached.push(name);
    return undefined;
  };
  const base = answerOptions({
    remarkPlugins: [marker("parsed"), ...ANSWER_PLUGINS, marker("own-done")],
    tableBox: "region",
    codeBlock: "focusable",
  });
  const allow = base.allowElement;
  const options: Options = {
    ...base,
    rehypePlugins: [marker("hast-done")],
    allowElement: (element, index, parent) => {
      filterCalls += 1;
      return allow?.(element, index, parent) ?? true;
    },
    children: text,
  };
  const start = performance.now();
  try {
    const element = Markdown(options);
    reached.push("returned");
    return { reached, filterCalls, thrown: null, element, ms: performance.now() - start };
  } catch (error) {
    return { reached, filterCalls, thrown: describeError(error), element: null, ms: performance.now() - start };
  }
}
