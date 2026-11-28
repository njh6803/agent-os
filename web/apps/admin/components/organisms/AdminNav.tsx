// 관리 화면의 탐색 항목(admin-style 명세 "틀과 탐색", admin-login 명세 "탐색"). 틀(AdminFrame)의 `nav` 슬롯에 들고, 넓은 폭에서는
// 옆 탐색, 좁은 폭에서는 위 막대에 선다. 첫 화면이 플러그인 목록이라 그 차례다. "계정"은 시스템 관리자에게만 보인다. 계정을 다루는
// 일은 권한 `manage_accounts` 라서 관리자에게는 항목이 없다(관리자가 주소로 열면 계정 화면이 한 줄로 막는다).
import type { IconName } from "@agent-os/ui";
import { NavItem } from "../molecules/NavItem";

/** 탐색이 가리키는 화면. 플러그인 하나는 플러그인, 대화 하나는 대화 항목 아래에 든다. */
export type Section = "plugins" | "chat" | "accounts" | "settings";

const SECTIONS = [
  { section: "plugins", href: "/", icon: "plug", label: "플러그인" },
  { section: "chat", href: "/chat", icon: "message-square", label: "대화" },
  { section: "accounts", href: "/accounts", icon: "users", label: "계정" },
  { section: "settings", href: "/settings", icon: "settings", label: "설정" },
] as const satisfies readonly { section: Section; href: string; icon: IconName; label: string }[];

interface AdminNavProps {
  /** 지금 화면이 든 탐색 항목. 어느 항목에도 들지 않는 화면(내 비밀번호 바꾸기)이면 null 이다. */
  readonly current: Section | null;
  /** "계정" 항목을 보인다. 시스템 관리자일 때만 참이다. */
  readonly showAccounts?: boolean;
}

export function AdminNav({ current, showAccounts = false }: AdminNavProps) {
  return SECTIONS.filter(({ section }) => section !== "accounts" || showAccounts).map(
    ({ section, href, icon, label }) => (
      <NavItem key={section} href={href} icon={icon} current={section === current}>
        {label}
      </NavItem>
    ),
  );
}
