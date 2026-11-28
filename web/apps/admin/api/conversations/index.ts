// 대화 목록의 요청 함수. 공용 생성 클라이언트만 쓰고 데이터만 돌려준다. 데이터가 아니면 RequestFailure 를 던진다. 클라이언트는
// 부를 때 만든다(`api/traces` 와 같다). 이 함수는 SWR 의 fetcher 에서만 부른다.

import type { components } from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";
import { operatorClient } from "../session";
import type { RunStatus } from "../traces";

export type ConversationPage = components["schemas"]["ConversationPage"];
export type ConversationRow = components["schemas"]["ConversationRow"];
export type Conversation = components["schemas"]["Conversation"];
export type UnreadableTrace = components["schemas"]["UnreadableTrace"];

/**
 * 대화 목록의 한 쪽(`GET /conversations`). 끝 실행이 최근인 대화가 먼저다. 상태는 끝 실행의 실행 상태다. 상태가 null 이면
 * 전부이고, 커서가 null 이면 첫 쪽이다. null 인 질의는 싣지 않는다(openapi-fetch 가 뺀다).
 */
export async function listConversations(
  status: RunStatus | null,
  after: string | null,
): Promise<ConversationPage> {
  const { data, error, response } = await operatorClient()
    .GET("/conversations", { params: { query: { status, after } } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data;
}
