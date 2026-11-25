// 위젯 관리 서버의 생성 클라이언트(ADR 0064). 위젯이 widget-login-state 에서, 위젯 관리 화면과 위젯 테스트 페이지가
// portal-admin 에서 이 패키지를 부른다. 지금은 공개 경로용 팩토리 하나뿐이다.
//
// 공개 경로 `/widget-settings/<이름>` 은 토큰이 없고, 위젯 관리 서버는 어느 출처의 페이지든 답을 읽게 한다
// (`Access-Control-Allow-Origin: *`). 브라우저는 `*` 와 자격 증명을 함께 쓰는 답을 읽지 않으므로(명세가 Fetch 표준을
// 기억에 기대어 읽은 어림이다) 요청이 자격 증명을 싣지 않아야 한다. 서버는 preflight(`OPTIONS` 물음)에 답하지 않으므로 요청이 CORS 안전 목록 밖의 머리도 달지 않아야
// 한다. openapi-fetch 0.17.0 은 본문 없는 요청에 `Content-Type` 도 `Accept` 도 붙이지 않는다(`clients.test.ts` 가 잰다).

import createClient, { type Client } from "openapi-fetch";
import type { paths } from "./generated/openapi";

/** 공개 경로 클라이언트가 아는 경로. 토큰 없이 읽히는 위젯 설정 하나뿐이다. */
export type PublicPaths = Pick<paths, "/widget-settings/{site}">;

export type PublicClient = Client<PublicPaths>;

/**
 * 공개 경로를 부르는 클라이언트. 기준 주소는 위젯 관리 서버의 출처(와 있다면 그 접두사)이고 부르는 쪽이 정한다.
 *
 * 기본으로 모든 요청에 `credentials: "omit"` 을 싣고 머리를 더하지 않는다. 호출마다 `credentials` 나 `headers` 를 넘기면
 * 그 값이 기본값을 덮는다(`openapi-fetch` 0.17.0 은 `...baseOptions, ...init` 순서로 요청을 짓는다). 공개 경로를 부르는 쪽은
 * 그 둘을 넘기지 않는다.
 */
export function createPublicClient(baseUrl: URL): PublicClient {
  return createClient<PublicPaths>({ baseUrl: baseUrl.href, credentials: "omit" });
}
