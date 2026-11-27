// 관리 요청의 훅들이 함께 쓰는 것. 플러그인, 실행, 대화 도메인이 쓴다. 읽기 정책이 여기 있다. 401 은 요청 함수 아래의 갱신
// 규칙(`api/session`)이 먼저 받아 갱신하고 다시 보낸다. 갱신까지 실패하면 그 규칙이 로그인 화면으로 보내므로 훅은 401 을
// 따로 다루지 않는다(admin-login 티켓 09).

/**
 * 서버 데이터를 읽는 정책. 다시 읽는 때는 창 포커스, 새로 고침 버튼, 쓰기 직후뿐이다(web-admin 명세 "새로 고침과
 * 상태"). 주기 재검증을 두지 않고, 재연결과 실패 뒤의 재시도도 끈다. 둘 다 시간이 흐르는 것만으로 서버를 다시
 * 부른다(스토리 35). 이 정책에서 빠지는 주기 읽기는 `.claude/rules/web-admin.md` 가 적는다. 지금 코드에 있는 것은
 * 플러그인 목록의 접속 확인(정책은 `hooks/queries/connection`의 `AUTO`)과 대화 화면의 끝 실행(정책은
 * `hooks/queries/conversation`의 `useEndRun`) 둘이다. 대화 목록은 여기에 `revalidateAll` 을 더해 포커스와 더 보기에 본 쪽을 모두 다시 읽는다
 * (`hooks/queries/conversations`). 더 보기는 운영자가 누른 때라 버튼의 몫으로 본다.
 */
export const READ = {
  revalidateOnFocus: true,
  revalidateOnReconnect: false,
  refreshInterval: 0,
  shouldRetryOnError: false,
} as const;
