// 관리 요청의 훅들이 함께 쓰는 것. 플러그인과 실행 두 도메인이 쓴다. 읽기 정책과, 관리 요청의 401 로 관리 토큰을
// 내려놓는 것이 여기 있다. 넣는 자리의 확인 요청이 거부를 스토어에 남기는 것은 `hooks/queries/plugins` 의
// `useAdminTokenEntry` 이고, 401 을 거부로 읽는 규칙(`isRejection`)은 둘이 함께 쓴다.

import { RequestFailure } from "../../../api/failure";
import { useTokens } from "../../../stores/tokens";

/**
 * 서버 데이터를 읽는 정책. 다시 읽는 때는 창 포커스, 새로 고침 버튼, 쓰기 직후뿐이다(web-admin 명세 "새로 고침과
 * 상태"). 주기 재검증을 두지 않고, 재연결과 실패 뒤의 재시도도 끈다. 둘 다 시간이 흐르는 것만으로 서버를 다시
 * 부른다(스토리 35).
 */
export const READ = {
  revalidateOnFocus: true,
  revalidateOnReconnect: false,
  refreshInterval: 0,
  shouldRetryOnError: false,
} as const;

/** 관리 토큰이 거부됐다는 실패인가. 401 이 거부라는 규칙은 확인 요청과 관리 요청이 이것 하나를 쓴다. */
export function isRejection(error: unknown): boolean {
  return error instanceof RequestFailure && error.status === 401;
}

/** 관리 요청 하나를 보낸다. 401 이면 그 요청이 실은 관리 토큰을 내려놓고 실패를 그대로 던진다. */
export async function orRejectAdminToken<T>(
  adminToken: string,
  request: (adminToken: string) => Promise<T>,
): Promise<T> {
  try {
    return await request(adminToken);
  } catch (error: unknown) {
    rejectAdminTokenIfStillHeld(error, adminToken);
    throw error;
  }
}

/** 그 사이 운영자가 다른 토큰을 넣었으면 그것은 둔다. 거부된 것은 옛 요청이 실은 토큰이다. */
function rejectAdminTokenIfStillHeld(error: unknown, adminToken: string): void {
  const tokens = useTokens.getState();
  if (isRejection(error) && tokens.adminToken === adminToken) {
    tokens.rejectAdminToken();
  }
}
