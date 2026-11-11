// 시제품: 모델이 지은 출력을 마크다운으로 그리는 부품(react-markdown + remark-gfm). 기존 `MarkdownReact.tsx` 의 제한에
// 화면 파일(`.scratch/answer-markdown/design/`)의 목표 모양을 더했다. 프로브가 후보를 견주려고 플러그인 목록과 표·코드
// 칸의 모양을 바깥에서 받는다(`createAnswerMarkdown`).
//
// 기존 제한(그대로)
// - 원시 HTML 은 글자로 보인다(rehype 플러그인을 더하지 않는다).
// - 허용 목록(`allowedElements`)에 든 요소만 그리고 나머지는 껍데기를 벗긴다(`unwrapDisallowed`).
// 목표 모양(더한 것)
// - 제목은 한 단계 낮춘다(`#` 은 `h2`, …, `#####` 와 `######` 은 `h6`).
// - 링크는 `http`·`https` 이고 사용자 정보가 없는 주소만 `a` 로 그린다(`lib/link-url.ts`). 링크 글 뒤에 화면 읽기
//   프로그램만 읽는 "(새 탭에서 열림)" 을 둔다.
// - 이미지는 그리지 않고 `이미지: 대체 글` 을 보인다. 대체 글이 비면 `이미지` 만 보인다.
// - 표는 스크롤 칸으로 감싸고 코드 블록은 포커스를 받는다(모양은 `TABLE_BOXES`, `CODE_BLOCKS` 에서 고른다).
// - 변환이 낸 `sup`(문장 끝 번호)과 `div`(출처 덩이)를 허용한다. 표지가 없는 `sup`·`div` 는 벗긴다. GFM 각주가 내는
//   `sup` 이 그렇게 벗겨진다.
//
// 그리다 실패하면 원문을 보이는 방법은 둘을 함께 둔다(프로브가 견준다).
// - `Direct`: react-markdown 의 `Markdown` 함수를 그리는 중에 직접 불러 `try/catch` 로 받는다. `Markdown` 은 훅을 쓰지
//   않는 함수다(react-markdown 10.1.0 의 `lib/index.js` 175~179줄을 읽었다). 파싱부터 React 요소를 만드는 데까지를 받는다.
// - `Guarded`: 에러 경계(클래스 컴포넌트)로 받는다. 글이 바뀌면 `key` 로 경계를 새로 세워 실패 상태를 푼다.
import { Children, Component, type ComponentProps, isValidElement, type ReactNode } from "react";
import Markdown, { type AllowElement, type Components, type Options } from "react-markdown";
import remarkGfm from "remark-gfm";
import { remarkAnswer } from "../../lib/answer-markdown/index";
import { linkUrl } from "../../lib/link-url";

export type RemarkPlugins = NonNullable<Options["remarkPlugins"]>;

const ALLOWED_ELEMENTS = [
  "a",
  "blockquote",
  "br",
  "code",
  "del",
  "div",
  "em",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "hr",
  "img",
  "li",
  "ol",
  "p",
  "pre",
  "strong",
  "sup",
  "table",
  "tbody",
  "td",
  "th",
  "thead",
  "tr",
  "ul",
] as const;

const allowElement: AllowElement = (element) => {
  if (element.tagName === "sup") return "dataCite" in element.properties;
  if (element.tagName === "div") {
    const classes = element.properties.className;
    return Array.isArray(classes) && classes.includes("sources");
  }
  return true;
};

function Link({ href, children }: ComponentProps<"a">): ReactNode {
  const safe = href === undefined ? null : linkUrl(href);
  if (safe === null) {
    return <>{children}</>;
  }
  return (
    <a href={safe} target="_blank" rel="noopener noreferrer">
      {children}
      <span className="sr-only">(새 탭에서 열림)</span>
    </a>
  );
}

function ImageAlt({ alt }: ComponentProps<"img">): ReactNode {
  return <span className="img-alt">{alt === undefined || alt === "" ? "이미지" : `이미지: ${alt}`}</span>;
}

/** 표의 스크롤 칸. 접근성 검사(axe) 프로브가 넷을 견준다. */
export const TABLE_BOXES = {
  region: ({ children }: ComponentProps<"table">): ReactNode => (
    <div className="tbl" role="region" aria-label="표" tabIndex={0}>
      <table>{children}</table>
    </div>
  ),
  group: ({ children }: ComponentProps<"table">): ReactNode => (
    <div className="tbl" role="group" aria-label="표" tabIndex={0}>
      <table>{children}</table>
    </div>
  ),
  focusable: ({ children }: ComponentProps<"table">): ReactNode => (
    <div className="tbl" tabIndex={0}>
      <table>{children}</table>
    </div>
  ),
  plain: ({ children }: ComponentProps<"table">): ReactNode => (
    <div className="tbl">
      <table>{children}</table>
    </div>
  ),
} satisfies Record<string, (props: ComponentProps<"table">) => ReactNode>;

/** 코드 블록. 접근성 검사(axe) 프로브가 셋을 견준다. */
export const CODE_BLOCKS = {
  focusable: ({ children }: ComponentProps<"pre">): ReactNode => <pre tabIndex={0}>{children}</pre>,
  plain: ({ children }: ComponentProps<"pre">): ReactNode => <pre>{children}</pre>,
  group: ({ children }: ComponentProps<"pre">): ReactNode => (
    <pre role="group" aria-label="코드" tabIndex={0}>
      {children}
    </pre>
  ),
} satisfies Record<string, (props: ComponentProps<"pre">) => ReactNode>;

function urlTransform(url: string): string {
  return linkUrl(url) ?? "";
}

// 글자만 내는 갈래(화면 읽기 영역에 넘길 글). 같은 변환과 허용 목록을 지난 나무에서 요소를 그리지 않고 글자만 남긴다.
// 블록과 목록 항목 사이는 mdast-util-to-hast 가 끼운 줄 끝 글자가 남아 띄어진다. 표는 그렇지 않다. JSX 로 바꾸는 단계
// (hast-util-to-jsx-runtime)가 표 요소(`table`, `thead`, `tbody`, `tr`) 바로 아래의 공백 글자 노드를 걸러 내, 첫 판은
// 칸과 줄이 모두 붙었다(plaintext.mjs 가 잡았다). 그래서 칸 뒤에 공백을, 줄 뒤에 줄 끝 글자를 손수 둔다.
// 링크의 "(새 탭에서 열림)" 은 넣지 않는다. 번호 목록의 번호는 화면에서 CSS 가 그리므로 글자로 되살린다.
function Bare({ children }: { readonly children?: ReactNode }): ReactNode {
  return <>{children}</>;
}

function CellText({ children }: { readonly children?: ReactNode }): ReactNode {
  return <>{children} </>;
}

function RowText({ children }: { readonly children?: ReactNode }): ReactNode {
  return (
    <>
      {children}
      {"\n"}
    </>
  );
}

function ImageAltText({ alt }: ComponentProps<"img">): ReactNode {
  return alt === undefined || alt === "" ? "이미지" : `이미지: ${alt}`;
}

function CiteText({ children }: ComponentProps<"sup">): ReactNode {
  return <> {children}</>;
}

function OrderedText({ start, children }: ComponentProps<"ol">): ReactNode {
  let number = start ?? 1;
  return Children.map(children, (child) => {
    if (!isValidElement(child)) return child;
    const numbered = (
      <>
        {String(number)}. {child}
      </>
    );
    number += 1;
    return numbered;
  });
}

const PLAIN_COMPONENTS = {
  a: Bare,
  blockquote: Bare,
  br: Bare,
  code: Bare,
  del: Bare,
  div: Bare,
  em: Bare,
  h1: Bare,
  h2: Bare,
  h3: Bare,
  h4: Bare,
  h5: Bare,
  h6: Bare,
  hr: Bare,
  img: ImageAltText,
  li: Bare,
  ol: OrderedText,
  p: Bare,
  pre: Bare,
  strong: Bare,
  sup: CiteText,
  table: Bare,
  tbody: Bare,
  td: CellText,
  th: CellText,
  thead: Bare,
  tr: RowText,
  ul: Bare,
} satisfies Components;

/** 번호 목록의 번호를 되살리지 않는 것. 프로브가 화면의 글과 글자를 견줄 때만 쓴다. */
const PLAIN_COMPONENTS_WITHOUT_ORDINALS = { ...PLAIN_COMPONENTS, ol: Bare } satisfies Components;

/** 그리다 실패했을 때의 모양. 지금 위젯이 출력을 그리는 문단과 같다(줄바꿈을 지키고 긴 낱말은 줄 끝에서 꺾는다). */
function RawAnswer({ text }: { readonly text: string }): ReactNode {
  return (
    <p className="raw" data-answer="raw">
      {text}
    </p>
  );
}

interface BoundaryProps {
  readonly text: string;
  readonly onFailure: ((error: unknown) => void) | undefined;
  readonly children: ReactNode;
}

interface BoundaryState {
  readonly failed: boolean;
}

class FailureBoundary extends Component<BoundaryProps, BoundaryState> {
  static getDerivedStateFromError(): BoundaryState {
    return { failed: true };
  }

  override state: BoundaryState = { failed: false };

  override componentDidCatch(error: unknown): void {
    this.props.onFailure?.(error);
  }

  override render(): ReactNode {
    return this.state.failed ? <RawAnswer text={this.props.text} /> : this.props.children;
  }
}

export interface AnswerProps {
  readonly text: string;
  /** 그리다 실패했을 때 불린다. 프로브가 "실패가 실제로 났다"는 표지로 쓴다. */
  readonly onFailure?: (error: unknown) => void;
}

export interface AnswerConfig {
  readonly remarkPlugins: RemarkPlugins;
  readonly tableBox: keyof typeof TABLE_BOXES;
  readonly codeBlock: keyof typeof CODE_BLOCKS;
}

export interface AnswerMarkdownSet {
  /** 실패를 받지 않고 그린다. 던지면 그대로 던진다. */
  readonly View: (props: { readonly text: string }) => ReactNode;
  /** `Markdown` 을 직접 불러 `try/catch` 로 받는다. */
  readonly Direct: (props: AnswerProps) => ReactNode;
  /** 에러 경계로 받고, 글이 바뀌면 경계를 새로 세운다. */
  readonly Guarded: (props: AnswerProps) => ReactNode;
  /** 에러 경계로 받되 경계를 새로 세우지 않는다(실패 상태가 남는 것을 보이는 대조). */
  readonly GuardedWithoutReset: (props: AnswerProps) => ReactNode;
  /** 요소 없이 글자만 낸다(화면 읽기 영역에 넘길 글). 실패하면 원문을 낸다. 번호 목록의 번호를 글자로 되살린다. */
  readonly Plain: (props: AnswerProps) => ReactNode;
  /** `Plain` 에서 번호 목록의 번호를 되살리지 않은 것. 프로브가 화면의 글과 글자를 견줄 때만 쓴다. */
  readonly PlainWithoutOrdinals: (props: AnswerProps) => ReactNode;
}

/** react-markdown 에 넘기는 옵션. 프로브가 던지는 단계를 가르려고 같은 옵션으로 `Markdown` 을 직접 부른다. */
export function answerOptions(config: AnswerConfig): Options {
  const components = {
    a: Link,
    img: ImageAlt,
    table: TABLE_BOXES[config.tableBox],
    pre: CODE_BLOCKS[config.codeBlock],
    h1: "h2",
    h2: "h3",
    h3: "h4",
    h4: "h5",
    h5: "h6",
  } satisfies Components;
  return {
    allowedElements: ALLOWED_ELEMENTS,
    allowElement,
    unwrapDisallowed: true,
    remarkPlugins: config.remarkPlugins,
    components,
    urlTransform,
  };
}

export function createAnswerMarkdown(config: AnswerConfig): AnswerMarkdownSet {
  const options = answerOptions(config);

  function View({ text }: { readonly text: string }): ReactNode {
    return (
      <div className="md" data-answer="markdown">
        <Markdown {...options}>{text}</Markdown>
      </div>
    );
  }

  function Direct({ text, onFailure }: AnswerProps): ReactNode {
    let drawn: ReactNode;
    try {
      drawn = Markdown({ ...options, children: text });
    } catch (error) {
      onFailure?.(error);
      return <RawAnswer text={text} />;
    }
    return (
      <div className="md" data-answer="markdown">
        {drawn}
      </div>
    );
  }

  function Guarded({ text, onFailure }: AnswerProps): ReactNode {
    return (
      <FailureBoundary key={text} text={text} onFailure={onFailure}>
        <View text={text} />
      </FailureBoundary>
    );
  }

  function GuardedWithoutReset({ text, onFailure }: AnswerProps): ReactNode {
    return (
      <FailureBoundary text={text} onFailure={onFailure}>
        <View text={text} />
      </FailureBoundary>
    );
  }

  function plain(components: Components): (props: AnswerProps) => ReactNode {
    return ({ text, onFailure }) => {
      try {
        return Markdown({ ...options, components, children: text });
      } catch (error) {
        onFailure?.(error);
        return text;
      }
    };
  }

  return {
    View,
    Direct,
    Guarded,
    GuardedWithoutReset,
    Plain: plain(PLAIN_COMPONENTS),
    PlainWithoutOrdinals: plain(PLAIN_COMPONENTS_WITHOUT_ORDINALS),
  };
}

/** 합친 시제품의 플러그인 목록. 직접 짠 변환만 쓴다. */
export const ANSWER_PLUGINS: RemarkPlugins = [remarkGfm, remarkAnswer];

const ANSWER = createAnswerMarkdown({ remarkPlugins: ANSWER_PLUGINS, tableBox: "region", codeBlock: "focusable" });

/** 합친 시제품. 실패를 `try/catch` 로 받는다. */
export const AnswerMarkdown = ANSWER.Direct;
/** 합친 시제품에서 실패를 받지 않는 것. 프로브의 모양 판정이 쓴다. */
export const AnswerMarkdownView = ANSWER.View;
/** 합친 시제품에서 실패를 에러 경계로 받는 것. */
export const AnswerMarkdownGuarded = ANSWER.Guarded;
/** 합친 시제품과 같은 변환을 지나 글자만 내는 것(화면 읽기 영역에 넘길 글). */
export const AnswerPlain = ANSWER.Plain;
export const AnswerPlainWithoutOrdinals = ANSWER.PlainWithoutOrdinals;
