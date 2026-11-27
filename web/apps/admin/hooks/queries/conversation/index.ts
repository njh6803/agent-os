// 대화 하나를 읽는 SWR 훅(admin-login 명세 "대화를 다시 그리는 읽기", "도는 실행을 이어 보기"). 컴포넌트는 useSWR 이나
// 요청 함수를 직접 부르지 않고 이 훅을 쓴다. 401 은 요청 함수 아래의 갱신 규칙(`api/session`)이 받아 SWR 에 닿지 않는다.

import useSWR, { type SWRResponse } from "swr";
import { type Earlier, pollInterval, readEarlierRuns } from "../../../api/conversation";
import { readTrace, type Trace } from "../../../api/traces";
import { READ } from "../admin";
import { traceKeys } from "../traces";

/**
 * 끝 실행의 트레이스. 패널과 같은 열쇠(`traceKeys.one`)로 읽어 SWR 의 같은 값을 쓴다. 결말이 없는 동안 3초마다 다시
 * 읽고, 결말이 오거나 마지막 이벤트 뒤 실행 제한 시간이 지나면 멈춘다.
 *
 * `refreshInterval` 의 함수는 이 훅을 부르는 부품이 그려질 때마다 새로 만든다(인라인 꼴). 한 번 만든 함수를 그대로 쓰는
 * 꼴은 데이터가 오기 전에 0 을 내면 시작하지 않았고 멈춘 뒤 새로 고쳐도 다시 돌지 않았다(`swr_poll` 결과 1a·1b). 그래서
 * 이 훅을 부르는 부품은 입력 칸 같은 자주 바뀌는 상태와 떼어 둔다. 그릴 때마다 타이머를 새로 걸기 때문이다(결과 1c).
 * 창이 가려진 동안 읽지 않고 돌아오면 읽는 앱의 지금 정책(`READ`)은 그대로다.
 *
 * @param timeoutSeconds `GET /auth/me` 의 실행 제한 시간. 멈출 때를 정한다.
 */
export function useEndRun(runId: string, timeoutSeconds: number): SWRResponse<Trace, unknown> {
  return useSWR(traceKeys.one(runId), () => readTrace(runId), {
    ...READ,
    refreshInterval: (latest: Trace | undefined) =>
      pollInterval(latest, timeoutSeconds, Date.now()),
  });
}

/**
 * 끝 실행 앞의 실행들. 앞 실행은 바뀌지 않으므로 창에 돌아올 때 다시 읽지 않고 새로 고침에서만 다시 읽는다. 끝 실행을
 * 아직 읽지 못했으면(`previousRun` 이 undefined) 읽지 않는다.
 */
export function useEarlierRuns(
  previousRun: string | null | undefined,
  endRunId: string,
): SWRResponse<Earlier, unknown> {
  return useSWR(
    previousRun === undefined ? null : (["earlier-runs", endRunId, previousRun] as const),
    ([, end, previous]) => readEarlierRuns(previous, end),
    { ...READ, revalidateOnFocus: false },
  );
}
