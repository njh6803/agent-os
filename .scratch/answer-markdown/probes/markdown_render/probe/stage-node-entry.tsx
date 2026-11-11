// Node 에서 던지는 단계를 가르는 입구. stage-child.mjs 가 esbuild 묶음(CJS, production)으로 부른다.
// `Markdown` 이 요소를 돌려주면 서버 렌더(`renderToStaticMarkup`)까지 해 보고, 그 단계가 던지는지도 적는다.
import { renderToStaticMarkup } from "react-dom/server";
import { describeError, runMarkdown, type Thrown } from "./stage-run";

export interface NodeStages {
  readonly reached: readonly string[];
  readonly filterCalls: number;
  readonly thrown: Thrown | null;
  readonly markdownMs: number;
  /** `Markdown` 이 던졌으면 null 이다(그리지 않았다). */
  readonly render: { readonly thrown: Thrown | null; readonly ms: number; readonly html: string | null } | null;
}

export function stages(text: string): NodeStages {
  const run = runMarkdown(text);
  if (run.thrown !== null) {
    return { reached: run.reached, filterCalls: run.filterCalls, thrown: run.thrown, markdownMs: run.ms, render: null };
  }
  const start = performance.now();
  try {
    const html = renderToStaticMarkup(
      <div className="md" data-answer="markdown">
        {run.element}
      </div>,
    );
    return {
      reached: run.reached,
      filterCalls: run.filterCalls,
      thrown: null,
      markdownMs: run.ms,
      render: { thrown: null, ms: performance.now() - start, html },
    };
  } catch (error) {
    return {
      reached: run.reached,
      filterCalls: run.filterCalls,
      thrown: null,
      markdownMs: run.ms,
      render: { thrown: describeError(error), ms: performance.now() - start, html: null },
    };
  }
}

/** `Markdown` 만 불러 던지는지 본다(그리지 않는다). 던지기 시작하는 깊이를 좁힐 때 쓴다. */
export function markdownThrows(text: string): boolean {
  return runMarkdown(text).thrown !== null;
}
