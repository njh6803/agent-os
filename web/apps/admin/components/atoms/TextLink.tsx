// 글자 링크(admin-style 명세 "앱 부품"). 화면 안에서 옮기는 링크라 Next 의 `Link` 다. 강조색으로 서고 올리면 글자색이
// 된다(그림의 `a{color:var(--accent)}a:hover{color:var(--text)}`). 포인터 목표가 24px 이상이 되게 줄 높이와 상관없이 최소
// 높이를 둔다(명세 "접근성과 폭").
import Link from "next/link";

interface TextLinkProps {
  readonly href: string;
  readonly children: string;
}

export function TextLink({ href, children }: TextLinkProps) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-6 items-center rounded-s text-body text-accent hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
    >
      {children}
    </Link>
  );
}
