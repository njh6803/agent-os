// 후보 1: react-markdown + remark-gfm. 마크다운을 React 요소로 그리고 innerHTML 을 쓰지 않는다.
//
// 건 제한
// - 원시 HTML: react-markdown 은 rehype-raw 를 더하지 않으면 원시 HTML 을 글자로 바꾼다(lib/index.js 의 `raw` 갈래).
//   여기서는 아무 rehype 플러그인도 더하지 않는다.
// - 요소: 허용 목록(`allowedElements`)에 든 태그만 그리고, 목록 밖의 요소는 껍데기를 벗겨 안의 글만 남긴다
//   (`unwrapDisallowed`). 각주의 `sup`·`section`, 할 일 목록의 `input` 이 그렇게 벗겨진다.
// - 이미지: `img` 는 대체 글만 그린다. 주소는 어느 속성에도 싣지 않는다.
// - 링크: `http:`·`https:` 만 `a` 로 그리고 `target="_blank"` 와 `rel="noopener noreferrer"` 를 단다. 나머지는 링크의
//   글만 그린다. `urlTransform` 도 같은 정책이라 다른 주소 속성(`cite` 등)에도 같은 판정이 걸린다.
import type { ComponentProps, ReactNode } from "react";
import Markdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { httpUrl } from "../../lib/safe-url";

const ALLOWED_ELEMENTS = [
  "a",
  "blockquote",
  "br",
  "code",
  "del",
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
  "table",
  "tbody",
  "td",
  "th",
  "thead",
  "tr",
  "ul",
] as const;

function Link({ href, children }: ComponentProps<"a">): ReactNode {
  const safe = href === undefined ? null : httpUrl(href);
  if (safe === null) {
    return <>{children}</>;
  }
  return (
    <a href={safe} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  );
}

function ImageAlt({ alt }: ComponentProps<"img">): ReactNode {
  return alt === undefined || alt === "" ? null : <span>{alt}</span>;
}

const COMPONENTS = { a: Link, img: ImageAlt } satisfies Components;
const REMARK_PLUGINS = [remarkGfm];

function urlTransform(url: string): string {
  return httpUrl(url) ?? "";
}

export function MarkdownReact({ text }: { readonly text: string }) {
  return (
    <Markdown
      allowedElements={ALLOWED_ELEMENTS}
      unwrapDisallowed
      remarkPlugins={REMARK_PLUGINS}
      components={COMPONENTS}
      urlTransform={urlTransform}
    >
      {text}
    </Markdown>
  );
}

/** 대조군. 라이브러리의 기본 설정에 GFM 만 더한 것이다. 제한을 걸지 않았을 때 같은 입력이 무엇이 되는지 본다. */
export function MarkdownReactDefault({ text }: { readonly text: string }) {
  return <Markdown remarkPlugins={REMARK_PLUGINS}>{text}</Markdown>;
}
