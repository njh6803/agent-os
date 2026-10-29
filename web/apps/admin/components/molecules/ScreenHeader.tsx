// 화면 머리(admin-style 명세 "화면 머리와 공통 상태"). 그 화면의 제목 `h1`, 그 아래 흐린 설명 한 줄, 읽는 화면이면 오른쪽에
// 동작(보조 버튼 "새로 고침")이다. 좁은 폭(`wide` 미만)에서는 동작이 제목 아래로 내려간다(명세가 정했다. 그림 mk-plugins-m
// 은 오른쪽에 두었다).
import type { ReactNode } from "react";

interface ScreenHeaderProps {
  /** 제목 요소의 id. 화면의 구역이 이 제목으로 이름을 얻는다. */
  readonly titleId?: string;
  readonly title: ReactNode;
  readonly description?: ReactNode;
  readonly action?: ReactNode;
}

export function ScreenHeader({ titleId, title, description, action }: ScreenHeaderProps) {
  return (
    <header className="flex flex-col items-start gap-3 wide:flex-row wide:justify-between wide:gap-4">
      <div className="flex min-w-0 flex-col gap-2">
        <h1 id={titleId} className="text-title wrap-anywhere">
          {title}
        </h1>
        {description === undefined ? null : (
          <p className="text-body text-text-muted">{description}</p>
        )}
      </div>
      {action}
    </header>
  );
}
