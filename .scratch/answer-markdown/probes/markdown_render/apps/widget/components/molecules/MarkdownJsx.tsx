// 후보 2: markdown-to-jsx(React 입구 `markdown-to-jsx/react`). 의존성이 없는 패키지 하나다.
//
// 건 제한
// - 원시 HTML: `disableParsingRawHTML` 로 HTML 을 요소로 옮기는 일을 끈다.
// - 규칙 단위 렌더(`renderRule`)를 허용 목록으로 쓴다. 이 라이브러리에는 요소 허용 목록 옵션이 없어, 규칙 종류
//   (`RuleType`)를 `switch` 로 모두 적고 그릴 것만 `next()` 로 넘긴다. 끝의 `default` 가 남은 타입을 never 에 대입해,
//   새 판이 규칙 종류를 더하면 타입 검사가 멈춘다.
//   - 이미지: 대체 글만 그린다.
//   - 링크: `http:`·`https:` 만 `a` 로 그리고 `target="_blank"` 와 `rel="noopener noreferrer"` 를 단다. 나머지는 글만.
//   - 할 일 목록의 체크박스(`input`): `[ ]`·`[x]` 글자로 그린다.
//   - 각주 참조(`[^1]`): `[1]` 글자로 그린다. 각주 본문은 라이브러리가 `footer` 로 그리고 `overrides` 로 벗긴다.
//   - HTML 노드·앞머리(frontmatter)·참조 모음: 그리지 않는다(옵션으로 이미 꺼 두었고, 여기는 두 번째 그물이다).
// - 주소 거르개(`sanitizer`)도 같은 정책으로 바꿔 파서가 먼저 거른다.
// - `forceBlock`: 한 줄짜리 글도 문단(`p`)으로 감싼다. 끄면 한 줄 글은 감싼 요소 없이 글자만 나온다.
// - `disableFrontmatter`: 답이 `---` 로 시작해도 앞머리로 읽어 삼키지 않는다.
// - `slugify`: 제목의 `id` 를 빈 글로 만든다. 페이지 안 방식에서 사이트 문서의 `id` 와 겹치지 않게 한다.
import { Fragment, type ReactNode } from "react";
import { Markdown, RuleType, type MarkdownToJSX } from "markdown-to-jsx/react";
import { httpUrl } from "../../lib/safe-url";

function renderRule(
  next: () => ReactNode,
  node: MarkdownToJSX.ASTNode,
  renderChildren: MarkdownToJSX.ASTRender,
  state: MarkdownToJSX.State,
): ReactNode {
  switch (node.type) {
    case RuleType.blockQuote:
    case RuleType.breakLine:
    case RuleType.breakThematic:
    case RuleType.codeBlock:
    case RuleType.codeInline:
    case RuleType.heading:
    case RuleType.orderedList:
    case RuleType.paragraph:
    case RuleType.table:
    case RuleType.text:
    case RuleType.textFormatted:
    case RuleType.unorderedList:
      return next();
    case RuleType.image:
      return node.alt === undefined || node.alt === "" ? null : (
        <span key={state.key}>{node.alt}</span>
      );
    case RuleType.link: {
      const href = node.target === null ? null : httpUrl(node.target);
      const children = renderChildren(node.children, state);
      if (href === null) {
        return <Fragment key={state.key}>{children}</Fragment>;
      }
      return (
        <a key={state.key} href={href} target="_blank" rel="noopener noreferrer">
          {children}
        </a>
      );
    }
    case RuleType.gfmTask:
      return <Fragment key={state.key}>{node.completed ? "[x]" : "[ ]"}</Fragment>;
    case RuleType.footnoteReference:
      return <Fragment key={state.key}>[{node.text}]</Fragment>;
    case RuleType.footnote:
    case RuleType.frontmatter:
    case RuleType.htmlBlock:
    case RuleType.htmlComment:
    case RuleType.htmlSelfClosing:
    case RuleType.ref:
    case RuleType.refCollection:
      return null;
    default: {
      // 허용 목록에 없는 규칙 종류다. 위에서 모두 적었으므로 여기서 node 의 타입은 never 다. 라이브러리의 새 판이
      // 규칙 종류를 더하면 이 대입이 타입 오류(TS2322)가 되어 타입 검사가 멈춘다(probe/typecheck.mjs 가 갈래 하나를
      // 지운 사본으로 잰다). `default` 와 이 대입이 없으면 멈추지 않는다. 반환 타입 ReactNode 가 undefined 를 품어
      // "끝에 return 이 없다"(TS2366)가 나지 않기 때문이다(첫 시도에서 대조가 걸리지 않아 알았다).
      const unknownRule: never = node;
      return unknownRule;
    }
  }
}

function Unwrapped({ children }: { readonly children?: ReactNode }): ReactNode {
  return <div>{children}</div>;
}

const OPTIONS: MarkdownToJSX.Options = {
  disableParsingRawHTML: true,
  disableFrontmatter: true,
  forceBlock: true,
  sanitizer: (value) => httpUrl(value),
  slugify: () => "",
  overrides: { footer: Unwrapped },
  renderRule,
};

export function MarkdownJsx({ text }: { readonly text: string }) {
  return <Markdown options={OPTIONS}>{text}</Markdown>;
}

/** 대조군. 라이브러리의 기본 설정이다. 제한을 걸지 않았을 때 같은 입력이 무엇이 되는지 본다. */
export function MarkdownJsxDefault({ text }: { readonly text: string }) {
  return <Markdown>{text}</Markdown>;
}
