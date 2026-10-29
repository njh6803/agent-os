// 탐색 항목(admin-style 명세 "앱 부품", 그림의 옆 탐색과 위 막대). 넓은 폭(`wide` 이상)에서는 아이콘 16과 글자, 높이
// `nav-item` 이고, 좁은 폭에서는 위 막대의 글자만, 조작 높이다. 지금 화면의 항목은 `aria-current="page"` 와 반투명 칠
// (`bg-selected`)이다. 아이콘은 글자와 함께 놓인 꾸밈이라 화면 읽기 프로그램에서 숨긴다.
import { Icon, type IconName } from "@agent-os/ui";
import Link from "next/link";

const STATE = {
  current: "bg-bg-selected font-medium text-text",
  other: "text-text-muted hover:bg-bg-hover hover:text-text",
} as const satisfies Record<"current" | "other", string>;

interface NavItemProps {
  readonly href: string;
  readonly icon: IconName;
  readonly children: string;
  /** 지금 보는 화면의 항목인가. */
  readonly current: boolean;
}

export function NavItem({ href, icon, children, current }: NavItemProps) {
  return (
    <Link
      href={href}
      aria-current={current ? "page" : undefined}
      className={`flex h-control items-center gap-2 rounded-m px-2 text-body focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring wide:h-nav-item wide:px-3 ${STATE[current ? "current" : "other"]}`}
    >
      <span className="hidden wide:flex">
        <Icon name={icon} size="16" />
      </span>
      {children}
    </Link>
  );
}
