// 플러그인의 요청 함수. 공용 생성 클라이언트만 쓰고 데이터만 돌려준다. 데이터가 아니면 RequestFailure 를 던진다.
// 클라이언트는 부를 때 만든다. 만들 때 location 을 읽어 브라우저에서만 설 수 있다. 그래서 이 함수는 SWR 의 fetcher 나
// 이벤트 처리기에서만 부른다(티켓 03 의 메모).

import { createAdminClient, type components } from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";

export type PluginRow = components["schemas"]["PluginRow"];

/** 등록된 플러그인 전부(`GET /plugins`). 관리 토큰을 싣는다. */
export async function listPlugins(adminToken: string): Promise<PluginRow[]> {
  const { data, error, response } = await createAdminClient(adminToken)
    .GET("/plugins")
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data;
}
