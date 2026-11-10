// 참고: remark-gfm 을 뺀 react-markdown(표·취소선·자동 링크·각주·할 일 목록이 없다). remark-gfm 의 몫을 보려는 것이다.
import type { ComponentProps, ReactNode } from "react";
import Markdown, { type Components } from "react-markdown";
import { httpUrl } from "../../apps/widget/lib/safe-url";

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

function urlTransform(url: string): string {
  return httpUrl(url) ?? "";
}

export function Answer({ text }: { readonly text: string }) {
  return (
    <Markdown components={COMPONENTS} urlTransform={urlTransform}>
      {text}
    </Markdown>
  );
}
