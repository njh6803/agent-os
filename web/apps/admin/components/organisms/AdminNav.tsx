// 관리 화면의 탐색 항목 셋(admin-style 명세 "틀과 탐색"). 틀(AdminFrame)의 `nav` 슬롯에 들고, 넓은 폭에서는 옆 탐색,
// 좁은 폭에서는 위 막대에 선다. 첫 화면이 플러그인 목록이라 그 차례다.
import type { IconName } from "@agent-os/ui";
import { NavItem } from "../molecules/NavItem";

/** 탐색이 가리키는 화면. 플러그인 하나는 플러그인, 실행 하나는 실행 항목 아래에 든다. */
export type Section = "plugins" | "runs" | "settings";

const SECTIONS = [
  { section: "plugins", href: "/", icon: "plug", label: "플러그인" },
  { section: "runs", href: "/runs", icon: "list", label: "실행" },
  { section: "settings", href: "/settings", icon: "settings", label: "설정" },
] as const satisfies readonly { section: Section; href: string; icon: IconName; label: string }[];

export function AdminNav({ current }: { readonly current: Section }) {
  return SECTIONS.map(({ section, href, icon, label }) => (
    <NavItem key={section} href={href} icon={icon} current={section === current}>
      {label}
    </NavItem>
  ));
}
