// 글자 링크(admin-style 명세 "앱 부품"). 화면 안에서 옮기는 링크라 Next 의 `Link` 다. 강조색으로 서고 올리면 글자색이
// 된다(그림의 `a{color:var(--accent)}a:hover{color:var(--text)}`). 포인터 목표가 24px 이상이 되게 줄 높이와 상관없이 최소
// 높이를 둔다(명세 "접근성과 폭"). 고정폭(`mono`)은 실행 식별자의 링크이고, 폭 320 에서도 가로로 밀리지 않게 아무
// 자리에서나 줄을 바꾼다(티켓 06).
import Link from "next/link";

type TextLinkFont = "body" | "mono";

const FONT_CLASS = {
  body: "text-body",
  mono: "font-mono text-mono wrap-anywhere",
} satisfies Record<TextLinkFont, string>;

interface TextLinkProps {
  readonly href: string;
  readonly font?: TextLinkFont;
  readonly children: string;
}

export function TextLink({ href, font = "body", children }: TextLinkProps) {
  return (
    <Link
      href={href}
      className={`inline-flex min-h-6 items-center rounded-s ${FONT_CLASS[font]} text-accent hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring`}
    >
      {children}
    </Link>
  );
}
