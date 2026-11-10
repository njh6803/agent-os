// 렌더 프로브의 입구. render.mjs 가 esbuild 로 묶어 Node 에서 부른다(Node 는 JSX 를 스스로 읽지 못한다).
// 후보 × 방식(제한/기본)마다 같은 입력을 `renderToStaticMarkup` 으로 HTML 글로 바꾼다.
// 바깥의 `div[data-probe]` 는 "이 회차가 실제로 그려졌다"는 표지이고 render.mjs 가 단언한다.
import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MarkdownJsx, MarkdownJsxDefault } from "../apps/widget/components/molecules/MarkdownJsx";
import {
  MarkdownReact,
  MarkdownReactDefault,
} from "../apps/widget/components/molecules/MarkdownReact";

type Renderer = (props: { readonly text: string }) => ReactNode;

const RENDERERS: Readonly<Record<string, Readonly<Record<string, Renderer>>>> = {
  "react-markdown": { restricted: MarkdownReact, default: MarkdownReactDefault },
  "markdown-to-jsx": { restricted: MarkdownJsx, default: MarkdownJsxDefault },
};

export const CANDIDATES = Object.keys(RENDERERS);
export const MODES = ["restricted", "default"] as const;

export function render(candidate: string, mode: string, id: string, text: string): string {
  const Renderer = RENDERERS[candidate]?.[mode];
  if (Renderer === undefined) {
    throw new Error(`없는 후보나 방식이다: ${candidate}/${mode}`);
  }
  return renderToStaticMarkup(
    <div data-probe={id}>
      <Renderer text={text} />
    </div>,
  );
}
