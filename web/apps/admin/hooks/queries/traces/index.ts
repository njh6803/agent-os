// 실행 하나의 트레이스를 읽는 SWR 훅. 컴포넌트는 useSWR 이나 요청 함수를 직접 부르지 않고 이 훅을 쓴다. 읽기 정책은 플러그인의
// 훅과 함께 쓴다(`hooks/queries/admin`). 401 은 요청 함수 아래의 갱신 규칙이 받는다(`api/session`).

import useSWR, { type SWRResponse } from "swr";
import { readTrace, type Trace } from "../../../api/traces";
import { READ } from "../admin";

/** SWR 키. 계정이 바뀌면 화면을 새로 불러와 캐시가 남지 않으므로 계정은 키에 싣지 않는다. */
export const traceKeys = {
  one: (runId: string) => ["trace", runId] as const,
};

/** 실행 하나의 트레이스. */
export function useTrace(runId: string): SWRResponse<Trace, unknown> {
  return useSWR(traceKeys.one(runId), () => readTrace(runId), READ);
}
