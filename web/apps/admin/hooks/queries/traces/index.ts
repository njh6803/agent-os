// 실행과 트레이스의 SWR 훅. 컴포넌트는 useSWR 이나 요청 함수를 직접 부르지 않고 이 훅을 쓴다. 읽기 정책은 플러그인의 훅과
// 함께 쓴다(`hooks/queries/admin`). 401 은 요청 함수 아래의 갱신 규칙이 받는다(`api/session`).

import useSWR, { type SWRResponse } from "swr";
import useSWRInfinite, { type SWRInfiniteResponse } from "swr/infinite";
import {
  listTraces,
  readTrace,
  type RunStatus,
  type Trace,
  type TracePage,
} from "../../../api/traces";
import { READ } from "../admin";

/** SWR 키. 목록의 쪽은 상태와 커서로 갈린다. 계정이 바뀌면 화면을 새로 불러와 캐시가 남지 않으므로 계정은 키에 싣지 않는다. */
export const traceKeys = {
  page: (status: RunStatus | null, after: string | null) => ["traces", status, after] as const,
  one: (runId: string) => ["trace", runId] as const,
};

/**
 * 실행 목록. 상태가 null 이면 전부다. 로그인한 화면 안에서만 부른다(`AdminScreen` 이 "지금 누구인지"를 읽은 뒤에 그린다).
 *
 * 쪽은 SWR 의 무한 목록이다. 둘째 쪽부터의 키는 앞 쪽의 `next_cursor` 이고, 그것이 null 이면 더 없다. 다시 읽을
 * 때는 본 쪽을 모두 차례로 다시 읽으며 다음 쪽의 키를 새로 읽은 앞 쪽의 커서로 다시 짓는다. 그 사이 새 실행이 생겨
 * 커서가 바뀌어도 옛 커서로 읽어 행이 겹치지 않는다. 새로 고침(`mutate()`)만이 아니라 포커스와 더 보기도 본 쪽을 모두
 * 읽는다(`revalidateAll`). 기본값이면 포커스가 첫 쪽과 커서가 바뀐 쪽만 읽어, 떠나 있던 사이 둘째 쪽의 실행이 끝나도 옛
 * 상태가 남는다(스토리 33). 처음 고르는 상태는 첫 쪽부터이고, 전에 본 상태로 돌아오면 그때 본 쪽 수를 되살린다
 * (`persistSize` 기본값).
 */
export function useRunList(status: RunStatus | null): SWRInfiniteResponse<TracePage, unknown> {
  return useSWRInfinite(
    (index: number, previous: TracePage | null) => {
      if (index === 0) {
        return traceKeys.page(status, null);
      }
      return previous === null || previous.next_cursor === null
        ? null
        : traceKeys.page(status, previous.next_cursor);
    },
    ([, pageStatus, after]) => listTraces(pageStatus, after),
    { ...READ, revalidateAll: true },
  );
}

/** 실행 하나의 트레이스. */
export function useTrace(runId: string): SWRResponse<Trace, unknown> {
  return useSWR(traceKeys.one(runId), () => readTrace(runId), READ);
}
