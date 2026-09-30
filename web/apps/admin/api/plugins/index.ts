// 플러그인의 요청 함수. 공용 생성 클라이언트만 쓰고 데이터만 돌려준다. 데이터가 아니면 RequestFailure 를 던진다.
// 클라이언트는 부를 때 만든다. 만들 때 location 을 읽어 브라우저에서만 설 수 있다. 그래서 이 함수는 SWR 의 fetcher 나
// 이벤트 처리기에서만 부른다(티켓 03 의 메모).

import { createAdminClient, type components } from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";

export type PluginRow = components["schemas"]["PluginRow"];
export type Plugin = components["schemas"]["Plugin"];
export type PluginKind = components["schemas"]["PluginKind"];

// 계약의 종류 넷. `Record` 라서 계약에 종류가 늘거나 줄면 여기가 컴파일에서 깨진다.
const KINDS = { agent: true, mcp: true, skill: true, model: true } as const satisfies Record<
  PluginKind,
  true
>;

/** 주소처럼 바깥에서 온 글자가 플러그인의 종류인가. */
export function isPluginKind(value: string): value is PluginKind {
  return Object.hasOwn(KINDS, value);
}

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

/**
 * 플러그인 하나(`GET /plugins/{kind}/{name}`). 매니페스트가 읽히는 것만 행이 온다. 읽을 수 없는 매니페스트는 500
 * 봉투이고 메시지가 경로와 이유를 든다.
 */
export async function readPlugin(
  adminToken: string,
  kind: PluginKind,
  name: string,
): Promise<Plugin> {
  const { data, error, response } = await createAdminClient(adminToken)
    .GET("/plugins/{kind}/{name}", { params: { path: { kind, name } } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data;
}

/**
 * 플러그인 하나를 켜거나 끈다(`PUT /plugins/{kind}/{name}/enabled`). 멱등이고 답은 본문 없는 204 다. 본문이 없는
 * 성공에도 openapi-fetch 의 data 는 비어 있어 응답의 상태로 가른다.
 */
export async function setPluginEnabled(
  adminToken: string,
  kind: PluginKind,
  name: string,
  enabled: boolean,
): Promise<void> {
  const { error, response } = await createAdminClient(adminToken)
    .PUT("/plugins/{kind}/{name}/enabled", {
      params: { path: { kind, name } },
      body: { enabled },
    })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (!response.ok) {
    throw failureOf(response.status, error);
  }
}
