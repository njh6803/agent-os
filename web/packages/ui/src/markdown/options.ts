// `Markdown`(화면)과 `MarkdownText`(글자만)가 함께 쓰는 react-markdown 옵션. 둘은 파서, 변환, 허용 목록, 주소 판정을 함께
// 쓰고 나무의 요소를 무엇으로 바꾸는지(`components`)만 다르다(명세 "부품의 자리와 내보내는 것"). 화면을 그리지 않는 모듈이라
// 컴포넌트 폴더 밖에 두고 패키지 밖으로 내보내지 않는다.
//
// - 원시 HTML 을 그리는 플러그인(rehype-raw)을 두지 않으므로 HTML 은 글자로 보인다.
// - 그리는 요소는 닫힌 목록이다(명세 "그리는 요소와 모양"). 목록 밖의 요소는 껍데기를 벗겨 안의 글만 남긴다.
// - 이미지(`img`)는 목록에 들지만 부품이 요소가 아니라 "이미지: 대체 글" 글자로 바꾼다. 어느 쪽도 `img` 를 내지 않는다.
// - 주소는 링크 정책(`link-url.ts`)을 지난 것만 남기고, 지나지 못하면 빈 글자로 바꾼다.
import type { Options } from "react-markdown";
import remarkGfm from "remark-gfm";
import { linkHref } from "./link-url";
import { remarkAnswer } from "./plugin";

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

/**
 * 파싱 전에 줄 끝(`\r\n`, `\r`)을 `\n` 으로 맞춘다. HTML 파서는 입력의 CR 을 LF 로 맞추지만 React 가 만드는 글자 노드는
 * 맞추지 않아서, 코드 블록 안의 `\r\n` 이 그대로 DOM 에 남는다. 물러서는 원문은 넣은 글자 그대로 보이므로 이 함수를 거치지 않는다.
 */
export function normalizeLineEnds(text: string): string {
  return text.replace(/\r\n?/g, "\n");
}

export const BASE_OPTIONS = {
  allowedElements: ALLOWED_ELEMENTS,
  unwrapDisallowed: true,
  remarkPlugins: [remarkGfm, remarkAnswer],
  urlTransform: (url: string): string => linkHref(url) ?? "",
} satisfies Options;
