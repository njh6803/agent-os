// 트레이스의 요청 함수. 공용 생성 클라이언트만 쓰고 데이터만 돌려준다. 데이터가 아니면 RequestFailure 를 던진다. 클라이언트는
// 부를 때 만든다(`api/plugins` 와 같다). 이 함수는 SWR 의 fetcher 와 이벤트 처리기에서만 부른다.

import type { components } from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";
import { operatorClient } from "../session";

export type RunStatus = components["schemas"]["RunStatus"];
export type Trace = components["schemas"]["Trace"];
export type TraceEvent = components["schemas"]["TraceEvent"];

/**
 * 한 실행의 트레이스(`GET /traces/{run_id}`). 이벤트는 쓴 순서 그대로다. 요약은 싣지 않는다. 없는 실행은 404, 읽을
 * 수 없는 파일은 500 봉투다.
 */
export async function readTrace(runId: string): Promise<Trace> {
  const { data, error, response } = await operatorClient()
    .GET("/traces/{run_id}", { params: { path: { run_id: runId } } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data;
}
