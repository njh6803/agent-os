// 글자 링크(admin-style 명세 "앱 부품"). 화면 안에서 옮기는 링크라 Next 의 `Link` 다. 강조색으로 서고 올리면 글자색이
// 된다(그림의 `a{color:var(--accent)}a:hover{color:var(--text)}`). 포인터 목표가 24px 이상이 되게 줄 높이와 상관없이 최소
// 높이를 둔다(명세 "접근성과 폭"). 고정폭(`mono`)은 실행 식별자의 링크이고, 폭 320 에서도 가로로 밀리지 않게 아무
// 자리에서나 줄을 바꾼다(티켓 06).
import Link from "next/link";

type TextLinkFont = "body" | "mono";

/** 링크의 모양. `inline`은 글줄 안에 서고, `clip`은 열 폭에 맞춰 한 줄로 줄인다(끝을 말줄임표로). */
type TextLinkFit = "inline" | "clip";

const FONT_CLASS = {
  body: "text-body",
  mono: "font-mono text-mono wrap-anywhere",
} satisfies Record<TextLinkFont, string>;

const FIT_CLASS = {
  inline: "inline-flex items-center",
  clip: "block max-w-form truncate",
} satisfies Record<TextLinkFit, string>;

interface TextLinkProps {
  readonly href: string;
  readonly font?: TextLinkFont;
  /** `clip`은 대화 목록의 첫 요청이 쓴다. 줄일 칸의 폭은 `max-w-form` 이고, 그보다 좁은 칸에서는 칸이 정한다. */
  readonly fit?: TextLinkFit;
  readonly children: string;
}

export function TextLink({ href, font = "body", fit = "inline", children }: TextLinkProps) {
  return (
    <Link
      href={href}
      className={`${FIT_CLASS[fit]} min-h-6 rounded-s ${FONT_CLASS[font]} text-accent hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring`}
    >
      {children}
    </Link>
  );
}
