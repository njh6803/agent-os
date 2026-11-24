// 접속 확인의 요청 함수(ADR 0067). 공용 생성 클라이언트만 쓰고 데이터만 돌려준다. 데이터가 아니면 RequestFailure 를
// 던진다. 붙지 못함(`unreached`)도 200 의 데이터라서 던지지 않는다. 401 은 관리 토큰의 문제이고 실패다.
// 클라이언트는 부를 때 만든다(`api/plugins` 의 머리 설명과 같다).

import { createAdminClient, type components } from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";

export type ConnectionCheck = components["schemas"]["ConnectionCheck"];
export type CheckableKind = components["schemas"]["CheckableKind"];

/**
 * 켜 둔 원격 MCP 서버나 켜 둔 모델이 붙는지 스스로 확인한다(`GET /plugins/{kind}/{name}/connection-check`). 응답은
 * `status` 로 가르는 넷 가운데 하나다.
 */
export async function checkConnection(
  adminToken: string,
  kind: CheckableKind,
  name: string,
): Promise<ConnectionCheck> {
  const { data, error, response } = await createAdminClient(adminToken)
    .GET("/plugins/{kind}/{name}/connection-check", { params: { path: { kind, name } } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data;
}

/**
 * 켜 둔 stdio MCP 서버를 한 번 띄워 붙는지 확인한다(`POST` 같은 경로). 운영자가 버튼을 눌러야만 부른다.
 */
export async function checkConnectionByLaunching(
  adminToken: string,
  kind: CheckableKind,
  name: string,
): Promise<ConnectionCheck> {
  const { data, error, response } = await createAdminClient(adminToken)
    .POST("/plugins/{kind}/{name}/connection-check", { params: { path: { kind, name } } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data;
}
