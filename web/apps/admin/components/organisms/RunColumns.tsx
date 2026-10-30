import type { ReactNode } from "react";

interface RunColumnsProps {
  readonly events: ReactNode;
  /** 결정 칸의 내용. 없으면 결정 칸이 서지 않는다. */
  readonly panel: ReactNode;
  readonly stream: ReactNode;
}

/**
 * 이벤트 칸, 결정 칸, 재개 스트림의 배치(admin-style 명세 "실행 하나와 결정 자리"). 상태를 쓰지 않는 배치라 실행
 * 하나의 본문(`RunDecision`)에서 떼어 냈다(admin-style 티켓 08). 본문 칸(틀의 `@container`)이 `split` 이상이면 왼쪽
 * 칸에 이벤트와 재개 스트림이 서고 결정 칸이 오른쪽 옆 칸(`wide`, 360px)으로 붙어 스크롤해도 머문다(`sticky`). 그
 * 미만이면 한 열이고 결정 칸이 이벤트 칸 아래, 재개 스트림 위다. 왼쪽 칸은 결정 칸이 있든 없든 최대 폭 `content` 를
 * 넘지 않는다.
 *
 * 결정 칸은 이름 없는 컨테이너(`@container`)다. 그 안의 버튼 줄이 칸의 폭으로 갈린다(명세 "결정 자리"). 칸 자신의
 * `@split:` 은 조상인 본문 칸의 폭을 본다. 컨테이너 질의는 자기가 아니라 가장 가까운 조상 컨테이너를 보기 때문이다.
 *
 * 한 열일 때 왼쪽 칸을 `contents` 로 풀어 세 칸을 한 flex 열의 형제로 두고 `order` 로 결정 칸을 이벤트 칸과 재개
 * 스트림 사이에 놓는다. 그래서 좁은 폭에서는 보이는 차례(이벤트, 결정, 재개 스트림)와 문서의 차례(이벤트, 재개 스트림,
 * 결정)가 다르다. 문서의 차례를 보이는 차례와 맞추려면 결정 칸을 이벤트 칸과 재개 스트림 사이에 두고, 넓은 폭에서
 * 그 셋을 두 열 격자(`minmax(0, 1fr) 360px`, 결정 칸이 두 행에 걸친다)로 놓아야 한다. 그 열 정의는 디자인 토큰에 없는
 * 임의값이라 쓰지 않았다(티켓 08 이 07 의 리뷰를 받아 봤다). 화면 읽기 프로그램은 늘 문서의 차례로 읽는다. 재개 스트림에
 * 포커스를 받는 것은 받은 이벤트의 실행 링크뿐이라, 탭 차례가 보이는 차례와 어긋나는 것은 그 링크가 있을 때뿐이다.
 */
export function RunColumns({ events, panel, stream }: RunColumnsProps) {
  return (
    <div className="flex flex-col gap-6 @split:flex-row @split:items-start">
      <div className="contents @split:flex @split:max-w-content @split:min-w-0 @split:flex-1 @split:flex-col @split:gap-6">
        {events}
        {stream === null ? null : <div className="order-2 @split:order-none">{stream}</div>}
      </div>
      {panel === null ? null : (
        <div className="@container order-1 @split:sticky @split:top-8 @split:order-none @split:w-wide @split:shrink-0">
          {panel}
        </div>
      )}
    </div>
  );
}
