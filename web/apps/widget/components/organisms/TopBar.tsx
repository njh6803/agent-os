// 위쪽 띠(화면 디자인의 고른 A). 이름과 "새 대화" 글자 버튼이다. 새 대화의 동작은 web-widget 티켓 05 가 잇는다.
import { Button } from "@agent-os/ui";

export interface TopBarProps {
  /** 사이트가 준 이름. 길면 줄 끝에서 줄인다. 비면(설정이 잘못돼 이름이 없을 때) 제목을 그리지 않는다. 빈 제목은 axe 위반이다. */
  readonly heading: string;
}

export function TopBar({ heading }: TopBarProps) {
  return (
    <header className="flex shrink-0 items-center justify-end gap-2 border-b border-border py-2 pr-2 pl-4">
      {heading === "" ? null : (
        <h1 className="min-w-0 flex-1 truncate text-body font-semibold">{heading}</h1>
      )}
      <Button variant="secondary">새 대화</Button>
    </header>
  );
}
