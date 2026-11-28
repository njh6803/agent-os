// 화면 머리(admin-style 명세 "화면 머리와 공통 상태"). 그 화면의 제목 `h1`, 그 아래 흐린 설명 한 줄, 읽는 화면이면 오른쪽에
// 동작(보조 버튼 "새로 고침")이다. 좁은 폭(`wide` 미만)에서는 동작이 제목 아래로 내려간다(명세가 정했다. 그림 mk-plugins-m
// 은 오른쪽에 두었다).
import type { ReactNode } from "react";

interface ScreenHeaderProps {
  /** 제목 요소의 id. 화면의 구역이 이 제목으로 이름을 얻는다. */
  readonly titleId?: string;
  readonly title: ReactNode;
  /** 제목 옆에 서되 제목의 이름에 들지 않는 것(플러그인 하나의 켜짐·꺼짐). */
  readonly beside?: ReactNode;
  readonly description?: ReactNode;
  readonly action?: ReactNode;
  /**
   * 제목의 단계. 기본은 화면의 제목 `h1` 이다. 대화 화면 위에 뜨는 실행 패널은 화면 안의 구역이라 `h2` 이고, 글자도 본문
   * 크기의 굵은 글자다(그림 ch-run).
   */
  readonly level?: "h1" | "h2";
}

export function ScreenHeader({
  titleId,
  title,
  beside,
  description,
  action,
  level = "h1",
}: ScreenHeaderProps) {
  const Heading = level;
  const heading = (
    <Heading
      id={titleId}
      className={
        level === "h1" ? "text-title wrap-anywhere" : "text-body font-semibold wrap-anywhere"
      }
    >
      {title}
    </Heading>
  );
  return (
    <header className="flex flex-col items-start gap-3 wide:flex-row wide:justify-between wide:gap-4">
      <div className="flex min-w-0 flex-col gap-2">
        {beside === undefined ? (
          heading
        ) : (
          <div className="flex min-w-0 flex-wrap items-center gap-3">
            {heading}
            {beside}
          </div>
        )}
        {description === undefined ? null : (
          <p className="text-body text-text-muted">{description}</p>
        )}
      </div>
      {action}
    </header>
  );
}
