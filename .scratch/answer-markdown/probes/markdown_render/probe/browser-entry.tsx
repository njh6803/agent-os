// 브라우저 프로브의 입구. browser.mjs 와 axe.mjs 가 esbuild 로 묶어(IIFE, 전역 이름 `MdProbe`, React 는 production 으로
// 품는다) Chromium 페이지에 싣는다. 페이지의 `#host` 에 React 뿌리를 세우고 시제품을 그린다.
//
// 그리는 방법(`mode`)
//   direct            `Markdown` 을 직접 불러 try/catch 로 받는다(합친 시제품의 기본).
//   guarded           에러 경계로 받고, 글이 바뀌면 `key` 로 경계를 새로 세운다.
//   guarded-no-reset  에러 경계로 받되 새로 세우지 않는다(실패 상태가 남는 것을 보이는 대조).
//   view              받지 않는다(실패가 실제로 난다는 것을 보이는 대조).
// 뿌리의 오류 처리기(`handlers`)
//   default   React 의 기본 처리기를 그대로 둔다. 콘솔과 페이지 오류에 무엇이 찍히는지는 부르는 쪽(Playwright)이 본다.
//   recorded  `onUncaughtError`·`onCaughtError`·`onRecoverableError` 를 받아 적기만 한다.
import type { ReactNode } from "react";
import { version as reactVersion } from "react";
import { flushSync } from "react-dom";
import { createRoot, type Root, type RootOptions } from "react-dom/client";
import remarkGfm from "remark-gfm";
import {
  ANSWER_PLUGINS,
  type AnswerProps,
  type CODE_BLOCKS,
  createAnswerMarkdown,
  type RemarkPlugins,
  type TABLE_BOXES,
} from "../apps/widget/components/molecules/AnswerMarkdown";
import { remarkAnswer } from "../apps/widget/lib/answer-markdown/index";
import { remarkSoftBreaks } from "../apps/widget/lib/answer-markdown/soft-breaks";
import { describeError, runMarkdown, type Thrown } from "./stage-run";

type Mode = "direct" | "guarded" | "guarded-no-reset" | "view";

interface MountConfig {
  readonly mode: Mode;
  /**
   * combined 는 합친 시제품의 변환, base 는 변환 없이 파서(remark-gfm)만, breaks 는 한 줄 바꿈 변환 하나만,
   * combined-guard 는 합친 시제품에 깊이 가드(인용과 목록이 `GUARD_DEPTH` 겹을 넘으면 던진다)를 켠 것이다.
   */
  readonly plugins: "combined" | "base" | "breaks" | "combined-guard";
  readonly tableBox: keyof typeof TABLE_BOXES;
  readonly codeBlock: keyof typeof CODE_BLOCKS;
  readonly handlers: "default" | "recorded";
}

interface RootError {
  readonly kind: "uncaught" | "caught" | "recoverable";
  readonly thrown: Thrown;
}

interface Snapshot {
  /** `#host` 안에 무엇이 그려졌나. raw 는 원문을 보이는 문단, markdown 은 시제품의 칸, empty 는 아무것도 없다. */
  readonly state: "raw" | "markdown" | "empty";
  /** raw 일 때 그 문단의 글이 받은 글과 글자 그대로 같은가. */
  readonly rawEqualsText: boolean | null;
  /** 부품이 `onFailure` 로 알린 실패. */
  readonly failures: readonly Thrown[];
  /** 뿌리의 처리기가 받은 오류(handlers 가 recorded 일 때만 찬다). */
  readonly rootErrors: readonly RootError[];
}

interface Drawn extends Snapshot {
  readonly ms: number;
  /** `flushSync` 가 던진 것. React 가 오류를 다시 던지지 않으면 null 이다. */
  readonly flushThrown: Thrown | null;
}

/** 프로브가 가드 갈래에 쓰는 한도. 보기로 고른 값이다(화면은 목록 12겹, 인용 20겹에서 글자 하나보다 좁아진다). */
const GUARD_DEPTH = 10;

const PLUGINS: Readonly<Record<MountConfig["plugins"], RemarkPlugins>> = {
  combined: ANSWER_PLUGINS,
  base: [remarkGfm],
  breaks: [remarkGfm, remarkSoftBreaks],
  "combined-guard": [remarkGfm, [remarkAnswer, { recoverEmphasis: true, softBreaks: true, maxContainerDepth: GUARD_DEPTH }]],
};

interface Mounted {
  readonly root: Root;
  readonly Answer: (props: AnswerProps) => ReactNode;
}

let mounted: Mounted | null = null;
const failures: Thrown[] = [];
const rootErrors: RootError[] = [];

function host(): HTMLElement {
  const element = document.getElementById("host");
  if (element === null) throw new Error("#host 가 없다");
  return element;
}

function recorded(): RootOptions {
  return {
    onUncaughtError: (error) => {
      rootErrors.push({ kind: "uncaught", thrown: describeError(error) });
    },
    onCaughtError: (error) => {
      rootErrors.push({ kind: "caught", thrown: describeError(error) });
    },
    onRecoverableError: (error) => {
      rootErrors.push({ kind: "recoverable", thrown: describeError(error) });
    },
  };
}

function snapshot(text: string): Snapshot {
  const raw = host().querySelector('[data-answer="raw"]');
  const markdown = host().querySelector('[data-answer="markdown"]');
  return {
    state: raw !== null ? "raw" : markdown !== null ? "markdown" : "empty",
    rawEqualsText: raw === null ? null : raw.textContent === text,
    failures: [...failures],
    rootErrors: [...rootErrors],
  };
}

function draw(target: Mounted, text: string): Drawn {
  const start = performance.now();
  let flushThrown: Thrown | null = null;
  try {
    flushSync(() => {
      target.root.render(
        <target.Answer
          text={text}
          onFailure={(error) => {
            failures.push(describeError(error));
          }}
        />,
      );
    });
  } catch (error) {
    flushThrown = describeError(error);
  }
  return { ms: performance.now() - start, flushThrown, ...snapshot(text) };
}

/** `#host` 에 뿌리를 세우고 글을 그린다. 한 페이지에서 한 번만 부른다. */
export function mount(config: MountConfig, text: string): Drawn {
  if (mounted !== null) throw new Error("이미 뿌리를 세웠다");
  const set = createAnswerMarkdown({
    remarkPlugins: PLUGINS[config.plugins],
    tableBox: config.tableBox,
    codeBlock: config.codeBlock,
  });
  const answers = {
    direct: set.Direct,
    guarded: set.Guarded,
    "guarded-no-reset": set.GuardedWithoutReset,
    view: ({ text: value }: AnswerProps): ReactNode => <set.View text={value} />,
  } satisfies Record<Mode, (props: AnswerProps) => ReactNode>;
  mounted = { root: createRoot(host(), config.handlers === "recorded" ? recorded() : {}), Answer: answers[config.mode] };
  return draw(mounted, text);
}

/** 세운 뿌리의 같은 자리에 다른 글을 그린다. */
export function update(text: string): Drawn {
  if (mounted === null) throw new Error("뿌리를 세우지 않았다");
  return draw(mounted, text);
}

interface BrowserStages {
  readonly reached: readonly string[];
  readonly filterCalls: number;
  readonly thrown: Thrown | null;
  readonly markdownMs: number;
  /** `Markdown` 이 던졌으면 null 이다(그리지 않았다). */
  readonly render: {
    readonly flushThrown: Thrown | null;
    readonly rootErrors: readonly RootError[];
    readonly ms: number;
    readonly state: Snapshot["state"];
  } | null;
}

/**
 * 던지는 단계를 가른다. 표지를 끼운 `Markdown` 을 부르고, 요소를 돌려주면 `#host` 에 새 뿌리를 세워 그려 본다(React 의
 * 렌더 단계). 뿌리의 처리기는 받아 적는다. 한 페이지에서 `mount` 와 섞어 부르지 않는다.
 */
export function stages(text: string): BrowserStages {
  const run = runMarkdown(text);
  if (run.thrown !== null) {
    return { reached: run.reached, filterCalls: run.filterCalls, thrown: run.thrown, markdownMs: run.ms, render: null };
  }
  const root = createRoot(host(), recorded());
  const start = performance.now();
  let flushThrown: Thrown | null = null;
  try {
    flushSync(() => {
      root.render(
        <div className="md" data-answer="markdown">
          {run.element}
        </div>,
      );
    });
  } catch (error) {
    flushThrown = describeError(error);
  }
  return {
    reached: run.reached,
    filterCalls: run.filterCalls,
    thrown: null,
    markdownMs: run.ms,
    render: { flushThrown, rootErrors: [...rootErrors], ms: performance.now() - start, state: snapshot(text).state },
  };
}

/** `Markdown` 만 불러 던지는지 본다(그리지 않는다). 던지기 시작하는 깊이를 좁힐 때 쓴다. */
export function markdownThrows(text: string): boolean {
  return runMarkdown(text).thrown !== null;
}

export function info(): { readonly react: string; readonly guardDepth: number } {
  return { react: reactVersion, guardDepth: GUARD_DEPTH };
}
