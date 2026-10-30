// 관리 화면의 틀(admin-style 명세 "틀과 탐색", 그림의 옆 탐색과 위 막대). 슬롯만 받는다. 채우는 것은 pages 다.
//
// 넓은 폭(`wide` 이상)에서는 왼쪽 옆 탐색(폭 `nav`)과 본문을 바탕 한 단계(`bg-raised`와 `bg`)와 테두리로 가르고, 옆
// 탐색 맨 위에 "Agent OS", 그 아래 탐색 항목이 선다. 좁은 폭에서는 같은 탐색이 위 막대(높이 `top-bar`)가 되어 "Agent OS"
// 와 글자 탐색이 한 줄에 선다. 서랍이나 메뉴 단추는 두지 않는다. 옆 탐색과 위 막대는 따로 그린 두 벌이 아니라 배치만
// 바뀌는 `nav` 하나다. 두 벌을 그리고 CSS 로 하나를 숨기면 CSS 를 싣지 않는 페이지 시험(jsdom)에 이름이 같은 탐색이
// 둘 보인다(티켓 04 "이 티켓이 정한 것"). "Agent OS" 는 제목 요소가 아닌 글자다.
//
// 본문 칸은 이름 없는 컨테이너(`@container`)다. 화면의 갈래(`@split:`)가 뷰포트가 아니라 이 칸의 폭으로 갈린다(ADR
// 0026 의 2026-10-26 이력). 틀 없이 그리는 organisms 의 스토리는 미리보기의 데코레이터가 같은 컨테이너를 두른다.
import type { ReactNode } from "react";

interface AdminFrameProps {
  /** 탐색 항목들. */
  readonly nav: ReactNode;
  /** 본문. 하이드레이션 전에는 없다(틀만 선다). */
  readonly children?: ReactNode;
}

export function AdminFrame({ nav, children }: AdminFrameProps) {
  return (
    <div className="flex min-h-dvh flex-col bg-bg text-text wide:flex-row">
      <nav
        aria-label="관리 화면"
        className="flex h-top-bar shrink-0 items-center gap-1 border-b border-border bg-bg-raised px-4 wide:h-auto wide:w-nav wide:flex-col wide:items-stretch wide:border-r wide:border-b-0 wide:px-3 wide:py-4"
      >
        <span className="flex-1 text-body font-semibold wide:mb-3 wide:flex wide:h-nav-item wide:flex-none wide:items-center wide:px-3">
          Agent OS
        </span>
        {nav}
      </nav>
      <main className="@container min-w-0 flex-1 px-4 pt-6 pb-8 wide:p-8">{children}</main>
    </div>
  );
}
