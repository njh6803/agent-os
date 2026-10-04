// 프로브 전용(web-widget 위젯 스택 측정). 저장소의 api-client 에는 없다. setup.mjs 가 임시 트리의 패키지에만 넣는다.
// 지금의 채널 클라이언트는 기준 주소가 `new URL("/api", location.origin)` 로 고정이고 `/runs` 를 모른다
// (`clients.ts`, `clients.test-d.ts`). 다른 출처의 채널을 부르는 위젯을 재려면 그 둘이 풀린 클라이언트가 있어야 해서,
// 측정하는 동안만 이것을 둔다. 실제로 어디를 바꿀지는 설계가 정한다.

import createClient, { type Client } from "openapi-fetch";
import type { paths } from "./generated/openapi";

/** 위젯이 아는 경로. 실행 하나를 일으키는 것뿐이다. */
export type WidgetPaths = Pick<paths, "/runs">;

export type WidgetClient = Client<WidgetPaths>;

/** 기준 주소(다른 출처일 수 있다)를 받아 토큰을 싣는 클라이언트. */
export function createWidgetClient(baseUrl: string, token: string): WidgetClient {
  return createClient<WidgetPaths>({ baseUrl, headers: { Authorization: `Bearer ${token}` } });
}
