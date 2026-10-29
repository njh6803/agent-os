// 빈 줄(admin-style 명세 "화면 머리와 공통 상태"). 무엇이 없는지 한 줄과 아이콘 하나다. 설명 문장과 버튼은 두지 않는다.
// 아이콘은 글자와 함께 놓인 꾸밈이라 화면 읽기 프로그램에서 숨긴다(패키지 `Icon` 은 이름이 없으면 숨긴다).
import { Icon, type IconName, type IconSize } from "@agent-os/ui";

interface EmptyLineProps {
  readonly icon: IconName;
  /** 빈 종류의 줄은 16, 거른 빈 목록은 20 이다(명세). */
  readonly iconSize: Extract<IconSize, "16" | "20">;
  readonly children: string;
}

export function EmptyLine({ icon, iconSize, children }: EmptyLineProps) {
  return (
    <p className="flex items-center gap-2 text-body text-text-muted">
      <Icon name={icon} size={iconSize} />
      {children}
    </p>
  );
}
