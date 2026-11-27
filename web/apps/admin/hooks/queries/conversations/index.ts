// 대화 목록의 SWR 훅. 컴포넌트는 useSWR 이나 요청 함수를 직접 부르지 않고 이 훅을 쓴다. 읽기 정책은 `READ` 다. 목록은
// 저절로 다시 읽지 않는다(대화 쪽의 주기 읽기는 대화 화면의 끝 실행뿐이다, ADR 0063).

import useSWRInfinite, { type SWRInfiniteResponse } from "swr/infinite";
import { type ConversationPage, listConversations } from "../../../api/conversations";
import type { RunStatus } from "../../../api/traces";
import { READ } from "../admin";

/** SWR 키. 쪽은 상태와 커서로 갈린다. 계정이 바뀌면 화면을 새로 불러와 캐시가 남지 않으므로 계정은 싣지 않는다. */
export const conversationKeys = {
  page: (status: RunStatus | null, after: string | null) =>
    ["conversations", status, after] as const,
};

/**
 * 대화 목록. 상태가 null 이면 전부다. 쪽을 잇고 다시 읽는 방식은 옛 실행 목록 훅과 같았다. 새로 고침과 포커스와
 * 더 보기는 본 쪽을 모두 차례로 다시 읽어, 그 사이 끝 실행이 바뀐 대화가 옛 커서로 겹쳐 보이지 않는다.
 */
export function useConversationList(
  status: RunStatus | null,
): SWRInfiniteResponse<ConversationPage, unknown> {
  return useSWRInfinite(
    (index: number, previous: ConversationPage | null) => {
      if (index === 0) {
        return conversationKeys.page(status, null);
      }
      return previous === null || previous.next_cursor === null
        ? null
        : conversationKeys.page(status, previous.next_cursor);
    },
    ([, pageStatus, after]) => listConversations(pageStatus, after),
    { ...READ, revalidateAll: true },
  );
}
