// 마크다운 부품(ADR 0053, answer-markdown 명세). 모델이 지은 출력을 마크다운으로 그리는 `Markdown` 과, 같은 변환과 같은 허용
// 목록을 지난 뒤 요소 없이 글자만 내는 `MarkdownText` 를 내보낸다(화면 읽기 프로그램에 새 출력을 알리는 영역이 읽을 글).
// props 는 둘 다 `text` 하나다. `className`·`style` 과 허용 요소나 링크 규칙을 바꾸는 prop 은 없다. 위젯과 관리 화면이 같은
// 제한으로 쓰게 하려는 것이다. 상태와 효과가 없다.
//
// 위험한 것은 그리지 않는다. 원시 HTML 과 스크립트는 글자로 보이고, 이미지는 "이미지: 대체 글"만 보이며, `http`·`https` 밖의
// 주소와 사용자 정보가 든 주소는 링크가 아니다(`../../markdown/link-url.ts`). 인용과 목록이 10겹을 넘게 겹치거나 파서와
// 변환 단계에서 던지는 출력은 원문이 글자 그대로 보인다. 아래 try/catch 가 받는 범위는 그 단계의 동기 예외까지다. 반환된
// 요소 안의 컴포넌트는 React 가 나중에 그리므로 거기서 던지는 예외는 받지 못한다.
//
// 모양은 요소마다의 클래스로 낸다. 디자인 시스템에는 컴포넌트 CSS 가 없고 화면 파일은 자손·형제 선택자로 그렸으므로, 놓인
// 자리(뿌리·인용 안의 흐름, 목록 항목 안, 출처 덩이 안)는 React 컨텍스트로 알고, 바로 앞 형제가 무엇인지는 변환이 단 표지로
// 안다. 제목 바로 뒤의 제목은 `data-after-heading`, 이어진 번호는 `data-cite` 의 값이다. 출처 덩이(`data-sources`)와 문장 끝
// 번호(`data-cite`)도 표지로 알아본다. 표지와 라이브러리가 붙이는 속성(`node`, `style`, 클래스)은 DOM 에 넘기지 않는다.
//
// 실패는 라이브러리의 컴포넌트를 요소로 두지 않고 함수로 직접 불러 try/catch 로 받는다. 그 함수는 훅을 쓰지 않는 동기
// 함수다(react-markdown 10.1.0 의 `Markdown`). 라이브러리가 훅을 쓰는 판으로 바뀌면 다시 그릴 때 깨질 수 있어 단위 시험이
// 같은 부품 하나를 보통 글, 물러서는 글, 보통 글로 다시 그려 본다.
import {
  Children,
  type ComponentProps,
  createContext,
  isValidElement,
  type ReactNode,
  useContext,
} from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import { CITE_ADJACENT, CITE_MARK } from "../../markdown/citations";
import { AFTER_HEADING } from "../../markdown/heading-marks";
import { linkHref } from "../../markdown/link-url";
import { BASE_OPTIONS, normalizeLineEnds } from "../../markdown/options";

export interface MarkdownProps {
  /** 마크다운으로 읽을 출력의 원문. */
  text: string;
}

// ---- 놓인 자리 ----

/** 블록 사이가 12px 인 자리(뿌리, 인용)는 `flow`, 목록 항목 안은 `item`, 출처 덩이 안은 `sources`(둘 다 블록 사이 4px). */
type Place = "flow" | "item" | "sources";
const PlaceContext = createContext<Place>("flow");
/** 코드 블록(`pre`) 안의 `code` 는 줄 안 코드의 바탕과 여백을 갖지 않는다. */
const InPreContext = createContext(false);
/** 표의 머리(`thead`)와 본문(`tbody`). 본문의 줄만 가로선을 긋는다. */
const TableSectionContext = createContext<"head" | "body">("body");

// ---- 화면 ----

const FOCUS_RING =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring";

const ROOT = "flex flex-col gap-3 text-body text-text wrap-anywhere";
const RAW = "whitespace-pre-wrap text-body text-text wrap-anywhere";

// 제목은 본문 크기에 굵기 600 이다. 흐름 안에서는 위 16px, 아래 4px 이고(틈 12px 에 위 여백 4px, 아래 여백 -8px) 그 자리의
// 첫 요소일 때 위 여백을, 마지막 요소일 때 아래 여백을 0 으로 둔다. 제목 바로 뒤의 제목은 위 여백을 12px 로 두어 사이가
// 16px 이 되게 한다. 목록 항목과 출처 덩이 안의 제목은 그 자리의 블록 사이를 따르고 따로 여백을 두지 않는다.
const HEADING_CLASS = {
  flow: "mt-1 -mb-2 first:mt-0 last:mb-0",
  flowAfterHeading: "mt-3 -mb-2 first:mt-0 last:mb-0",
  tight: "",
} satisfies Record<"flow" | "flowAfterHeading" | "tight", string>;

type HeadingProps = ComponentProps<"h1"> & { readonly [AFTER_HEADING]?: string };

function heading(Tag: "h2" | "h3" | "h4" | "h5" | "h6") {
  return function Heading(props: HeadingProps) {
    const place = useContext(PlaceContext);
    const key =
      place !== "flow" ? "tight" : props[AFTER_HEADING] === undefined ? "flow" : "flowAfterHeading";
    return <Tag className={`font-semibold ${HEADING_CLASS[key]}`}>{props.children}</Tag>;
  };
}

// 제목은 한 단계 낮춘다. 위젯 제목이 `h1` 이라 출력의 제목과 갈리게 하려는 것이다. 보이는 모양은 여섯 단계가 같다.
// `h5` 와 `h6` 이 둘 다 `h6` 을 가리키는 것은 의도다. `h6` 은 더 내릴 수 없어 `h6` 으로 둔다.
const HEADINGS = {
  h1: heading("h2"),
  h2: heading("h3"),
  h3: heading("h4"),
  h4: heading("h5"),
  h5: heading("h6"),
  h6: heading("h6"),
} satisfies Components;

function Link({ href, children }: ComponentProps<"a">) {
  const safe = href === undefined ? null : linkHref(href);
  if (safe === null) return <>{children}</>;
  return (
    <a
      href={safe}
      target="_blank"
      rel="noopener noreferrer"
      className={`text-accent underline ${FOCUS_RING}`}
    >
      {children}
      <span className="sr-only">(새 탭에서 열림)</span>
    </a>
  );
}

function ImagePlace({ alt }: ComponentProps<"img">) {
  return <span className="text-text-muted">{imageText(alt)}</span>;
}

function imageText(alt: string | undefined): string {
  return alt === undefined || alt === "" ? "이미지" : `이미지: ${alt}`;
}

function Blockquote({ children }: ComponentProps<"blockquote">) {
  return (
    <blockquote className="flex flex-col gap-3 border-l-2 border-border-control pl-3">
      <PlaceContext.Provider value="flow">{children}</PlaceContext.Provider>
    </blockquote>
  );
}

// 글머리는 어디에 놓여도 검은 점이고 안쪽 목록은 들여쓰기 24px 로 단계가 갈린다. 목록과 항목은 flex 로 만들지 않는다
// (글머리 표시가 사라진다). 항목 사이와 항목 안의 블록 사이 4px 은 자식 사이 여백으로 낸다. 출처 덩이 안의 목록은 항목 사이가
// 0 이다.
function List({
  children,
  ordered,
  start,
}: {
  children?: ReactNode;
  ordered: boolean;
  start?: number;
}) {
  const place = useContext(PlaceContext);
  const nested = place === "item" ? "mt-1 " : "";
  const between = place === "sources" ? "" : "space-y-1 ";
  const className = `${nested}${between}pl-6 ${ordered ? "list-decimal" : "list-disc"}`;
  return ordered ? (
    <ol className={className} start={start}>
      {children}
    </ol>
  ) : (
    <ul className={className}>{children}</ul>
  );
}

function UnorderedList({ children }: ComponentProps<"ul">) {
  return <List ordered={false}>{children}</List>;
}

function OrderedList({ children, start }: ComponentProps<"ol">) {
  return (
    <List ordered start={start}>
      {children}
    </List>
  );
}

function Item({ children }: ComponentProps<"li">) {
  return (
    <li className="space-y-1">
      <PlaceContext.Provider value="item">{children}</PlaceContext.Provider>
    </li>
  );
}

function InlineOrBlockCode({ children }: ComponentProps<"code">) {
  const inPre = useContext(InPreContext);
  return (
    <code className={inPre ? "font-mono text-mono" : "rounded-s bg-bg px-1 font-mono text-mono"}>
      {children}
    </code>
  );
}

// 코드 블록은 줄을 꺾지 않고 칸 안에서 가로로 스크롤하며 포커스를 받는다. 넘치지 않을 때도 같은 속성이다(넘치는지를 재려면
// 그린 뒤의 폭을 봐야 하고 부품은 효과를 쓰지 않는다).
function CodeBlock({ children }: ComponentProps<"pre">) {
  return (
    <pre
      tabIndex={0}
      className={`overflow-x-auto rounded-s border border-border bg-bg p-3 ${FOCUS_RING}`}
    >
      <InPreContext.Provider value>{children}</InPreContext.Provider>
    </pre>
  );
}

// 표는 `div` 로 감싸고 그 `div` 가 가로로 스크롤한다. 이름 "표"의 묶음이고 포커스를 받는다. 이름 있는 영역(`region`)으로
// 두면 표가 둘인 출력에서 같은 이름의 랜드마크가 둘이 되어 axe 가 위반으로 본다(명세 "표와 코드 블록의 스크롤 칸").
function Table({ children }: ComponentProps<"table">) {
  return (
    <div role="group" aria-label="표" tabIndex={0} className={`overflow-x-auto ${FOCUS_RING}`}>
      <table className="border-collapse text-table">{children}</table>
    </div>
  );
}

function TableHead({ children }: ComponentProps<"thead">) {
  return (
    <thead className="border-b border-border">
      <TableSectionContext.Provider value="head">{children}</TableSectionContext.Provider>
    </thead>
  );
}

function TableBody({ children }: ComponentProps<"tbody">) {
  return (
    <tbody>
      <TableSectionContext.Provider value="body">{children}</TableSectionContext.Provider>
    </tbody>
  );
}

function TableRow({ children }: ComponentProps<"tr">) {
  const section = useContext(TableSectionContext);
  return (
    <tr className={section === "body" ? "border-b border-border last:border-b-0" : ""}>
      {children}
    </tr>
  );
}

// 표 칸의 정렬은 라이브러리가 인라인 `style` 로 주는 값을 읽어 정렬 유틸리티로 바꾼다. 모양을 내는 길을 클래스 하나로만
// 두어 클래스 판정과 사진 비교가 모든 모양을 보게 하려는 것이다.
const ALIGN_CLASS = {
  left: "text-left",
  center: "text-center",
  right: "text-right",
} satisfies Record<string, string>;

function alignClass(style: ComponentProps<"td">["style"]): string {
  const align = style?.textAlign;
  if (align === "left" || align === "center" || align === "right") return ALIGN_CLASS[align];
  return "";
}

const CELL = "min-w-cell-min max-w-cell-max px-3 py-2 align-top first:pl-0";

// 문장 끝 번호는 작은 흐린 위첨자이고 줄 높이를 0 으로 두어 번호가 든 줄이 높아지지 않게 한다. 앞 글자와의 틈은 2px 이고,
// 바로 앞이 번호인 번호(이어진 번호)는 두 번호가 한 수로 읽히지 않게 4px 이다. 누를 수 없고 포커스를 받지 않는다.
type CiteProps = ComponentProps<"sup"> & { readonly [CITE_MARK]?: string };

function Cite(props: CiteProps) {
  const gap = props[CITE_MARK] === CITE_ADJACENT ? "ml-1" : "ml-cite-start";
  return <sup className={`${gap} text-small leading-0 text-text-muted`}>{props.children}</sup>;
}

// 출처 덩이는 위 선 아래 12px 에 작은 흐린 글자로 그리고, 안의 블록 사이는 4px 이다. 안의 요소는 글자 크기와 색을 물려받는다.
function SourcesBlock({ children }: ComponentProps<"div">) {
  return (
    <div className="flex flex-col gap-1 border-t border-border pt-3 text-small text-text-muted">
      <PlaceContext.Provider value="sources">{children}</PlaceContext.Provider>
    </div>
  );
}

function HeaderCell({ children, style }: ComponentProps<"th">) {
  return (
    <th className={`${CELL} font-semibold ${alignClass(style) || ALIGN_CLASS.left}`}>{children}</th>
  );
}

function DataCell({ children, style }: ComponentProps<"td">) {
  return <td className={`${CELL} ${alignClass(style)}`.trim()}>{children}</td>;
}

const SCREEN_COMPONENTS = {
  ...HEADINGS,
  a: Link,
  blockquote: Blockquote,
  code: InlineOrBlockCode,
  del: ({ children }: ComponentProps<"del">) => <del className="line-through">{children}</del>,
  div: SourcesBlock,
  em: ({ children }: ComponentProps<"em">) => <em className="italic">{children}</em>,
  hr: () => <hr className="border-t border-border" />,
  img: ImagePlace,
  li: Item,
  ol: OrderedList,
  pre: CodeBlock,
  strong: ({ children }: ComponentProps<"strong">) => (
    <strong className="font-semibold">{children}</strong>
  ),
  sup: Cite,
  table: Table,
  tbody: TableBody,
  td: DataCell,
  th: HeaderCell,
  thead: TableHead,
  tr: TableRow,
  ul: UnorderedList,
} satisfies Components;

/** 출력을 마크다운으로 그린다. 파서와 변환 단계에서 던지거나 인용·목록이 10겹을 넘으면 원문을 글자 그대로 보인다. */
export function Markdown({ text }: MarkdownProps) {
  let drawn: ReactNode;
  try {
    drawn = ReactMarkdown({
      ...BASE_OPTIONS,
      components: SCREEN_COMPONENTS,
      children: normalizeLineEnds(text),
    });
  } catch {
    return <p className={RAW}>{text}</p>;
  }
  return <div className={ROOT}>{drawn}</div>;
}

// ---- 글자만 ----

// 글자만 내는 갈래는 화면 읽기 프로그램에 새 출력을 알리는 숨긴 영역이 읽을 글이다. 같은 변환과 허용 목록을 지난 나무에서
// 요소를 그리지 않고 글자만 남긴다. 블록과 목록 항목 사이는 라이브러리가 끼운 줄 끝 글자가 띄운다. 표는 그렇지 않다. JSX 로
// 바꾸는 단계가 표 요소 바로 아래의 공백 글자를 걸러 내므로 칸 뒤에 공백을, 줄 뒤에 줄 끝 글자를 손수 둔다. 번호 목록의
// 번호는 화면에서 CSS 가 그리므로 글자로 되살리고, 링크의 "(새 탭에서 열림)" 은 내지 않는다(누를 수 없는 글이다). 문장 끝
// 번호는 앞 글자에 붙어 그려지므로 앞에 공백을 두어 앞말과 한 낱말로 읽히지 않게 한다.
function Bare({ children }: { readonly children?: ReactNode }) {
  return <>{children}</>;
}

function CiteText({ children }: { readonly children?: ReactNode }) {
  return <> {children}</>;
}

function CellText({ children }: { readonly children?: ReactNode }) {
  return <>{children} </>;
}

function RowText({ children }: { readonly children?: ReactNode }) {
  return (
    <>
      {children}
      {"\n"}
    </>
  );
}

function ImageText({ alt }: ComponentProps<"img">) {
  return <>{imageText(alt)}</>;
}

function OrderedText({ start, children }: ComponentProps<"ol">) {
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

const TEXT_COMPONENTS = {
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
  img: ImageText,
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

/** 출력을 요소 없이 글자만으로 낸다. 파서와 변환 단계에서 던지거나 10겹을 넘으면 원문을 낸다. */
export function MarkdownText({ text }: MarkdownProps) {
  try {
    return ReactMarkdown({
      ...BASE_OPTIONS,
      components: TEXT_COMPONENTS,
      children: normalizeLineEnds(text),
    });
  } catch {
    return text;
  }
}
