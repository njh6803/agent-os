// 글자만 내는 갈래의 입구. plaintext.mjs 와 callsites.mjs 가 esbuild 로 묶어 Node 에서 부른다.
// 합친 시제품으로 같은 글을 두 번 그린다. 하나는 화면에 보이는 모양(`shown`), 하나는 화면 읽기 영역에 넘길 글자만의
// 모양(`plain`, 번호 목록의 번호를 되살린 것과 되살리지 않은 것)이다. 바깥의 `data-probe` 는 "이 회차가 실제로
// 그려졌다"는 표지이고 부르는 쪽이 단언한다. 읽기 영역은 위젯처럼 문단 하나(`p`)로 감싼다.
//
// `renderBoth` 는 합친 시제품 그대로(깊이 가드 없음)이고, `renderBothGuarded` 는 깊이 가드를 켠 것이다(인용과 목록이
// `GUARD_DEPTH` 겹을 넘으면 그리기 전에 던진다). `errors` 는 갈래마다 `onFailure` 가 받은 오류의 이름이다.
import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import remarkGfm from "remark-gfm";
import { ANSWER_PLUGINS, type AnswerMarkdownSet, createAnswerMarkdown, type RemarkPlugins } from "../apps/widget/components/molecules/AnswerMarkdown";
import { remarkAnswer } from "../apps/widget/lib/answer-markdown/index";

/** 프로브가 가드 갈래에 쓰는 한도. browser-entry.tsx 의 값과 같다. */
export const GUARD_DEPTH = 10;

const GUARDED_PLUGINS: RemarkPlugins = [
  remarkGfm,
  [remarkAnswer, { recoverEmphasis: true, softBreaks: true, maxContainerDepth: GUARD_DEPTH }],
];

const PLAIN = createAnswerMarkdown({ remarkPlugins: ANSWER_PLUGINS, tableBox: "region", codeBlock: "focusable" });
const GUARDED = createAnswerMarkdown({ remarkPlugins: GUARDED_PLUGINS, tableBox: "region", codeBlock: "focusable" });

export interface Both {
  readonly shown: string;
  readonly plain: string;
  readonly plainWithoutOrdinals: string;
  /** 갈래마다 그리다 실패해 원문으로 물러섰는가(부품이 `onFailure` 로 알린 것). */
  readonly failed: { readonly shown: boolean; readonly plain: boolean; readonly plainWithoutOrdinals: boolean };
  /** 갈래마다 `onFailure` 가 받은 오류의 이름. 물러서지 않았으면 null 이다. */
  readonly errors: { readonly shown: string | null; readonly plain: string | null; readonly plainWithoutOrdinals: string | null };
}

const nameOf = (error: unknown): string => (error instanceof Error ? error.name : typeof error);

function draw(text: string, Answer: (props: { readonly text: string; readonly onFailure: (error: unknown) => void }) => ReactNode, tag: "div" | "p", probe: string): { readonly html: string; readonly error: string | null } {
  let error: string | null = null;
  const inner = (
    <Answer
      text={text}
      onFailure={(thrown) => {
        error = nameOf(thrown);
      }}
    />
  );
  const html = renderToStaticMarkup(tag === "div" ? <div data-probe={probe}>{inner}</div> : <p data-probe={probe}>{inner}</p>);
  return { html, error };
}

function both(text: string, set: AnswerMarkdownSet): Both {
  const shown = draw(text, set.Direct, "div", "shown");
  const plain = draw(text, set.Plain, "p", "plain");
  const bare = draw(text, set.PlainWithoutOrdinals, "p", "plain");
  return {
    shown: shown.html,
    plain: plain.html,
    plainWithoutOrdinals: bare.html,
    failed: { shown: shown.error !== null, plain: plain.error !== null, plainWithoutOrdinals: bare.error !== null },
    errors: { shown: shown.error, plain: plain.error, plainWithoutOrdinals: bare.error },
  };
}

export function renderBoth(text: string): Both {
  return both(text, PLAIN);
}

export function renderBothGuarded(text: string): Both {
  return both(text, GUARDED);
}
