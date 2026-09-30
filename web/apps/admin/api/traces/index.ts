// 실행과 트레이스의 요청 함수. 공용 생성 클라이언트만 쓰고 데이터만 돌려준다. 데이터가 아니면 RequestFailure 를
// 던진다. 클라이언트는 부를 때 만든다(`api/plugins` 와 같다). 이 함수는 SWR 의 fetcher 에서만 부른다.

import { createAdminClient, type components } from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";

export type TracePage = components["schemas"]["TracePage"];
export type RunRow = components["schemas"]["RunRow"];
export type RunSummary = components["schemas"]["RunSummary"];
export type RunStatus = components["schemas"]["RunStatus"];
export type Trace = components["schemas"]["Trace"];
export type TraceEvent = components["schemas"]["TraceEvent"];

/**
 * 실행 목록의 한 쪽(`GET /traces`). 최근 실행이 먼저다. 상태가 null 이면 전부이고, 커서가 null 이면 첫 쪽이다.
 * null 인 질의는 싣지 않는다(openapi-fetch 가 뺀다).
 */
export async function listTraces(
  adminToken: string,
  status: RunStatus | null,
  after: string | null,
): Promise<TracePage> {
  const { data, error, response } = await createAdminClient(adminToken)
    .GET("/traces", { params: { query: { status, after } } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data;
}

/**
 * 한 실행의 트레이스(`GET /traces/{run_id}`). 이벤트는 쓴 순서 그대로다. 요약은 싣지 않는다. 없는 실행은 404, 읽을 수
 * 없는 파일은 500 봉투다.
 */
export async function readTrace(adminToken: string, runId: string): Promise<Trace> {
  const { data, error, response } = await createAdminClient(adminToken)
    .GET("/traces/{run_id}", { params: { path: { run_id: runId } } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data;
}
