// 생성 클라이언트 셋(ADR 0021·0024). 요청의 경로를 보고 자격을 고르지 않는다. 고르는 것은 클라이언트다. 운영자
// 클라이언트는 토큰을 들지 않고, 쿠키는 브라우저가 같은 출처의 중계(`/api/*`)에 스스로 싣는다. 위젯 클라이언트도 토큰을
// 들지 않고 부르는 쪽이 요청마다 사이트가 서명한 토큰을 넘긴다. 한 자격이 맡지 않은 경로에 실리는 실수는 타입이
// 막는다. 각 클라이언트가 아는 경로가 그 자격이 여는 경로뿐이라서다.
//
// 서버의 접두사→자격 표(`/end-user` 아래는 사이트가 서명한 토큰, 그 밖은 운영자 로그인. `.claude/rules/http.md`)를 여기서
// 다시 판정하지 않는다. TS 가 아는 것은 생성된 경로 키 가운데 어느 것이 최종 사용자의 것인가뿐이다. 계약에 경로가 늘면
// 경로 목록을 고정한 타입 테스트(`clients.test-d.ts`)가 빨개진다. 관리 화면은 최종 사용자 경로를 부르지 않고, 위젯은 그
// 경로만 부른다.

import createClient, { type Client, type Middleware } from "openapi-fetch";
import type { paths } from "./generated/openapi";

/** 사이트가 서명한 토큰이 여는 경로. 최종 사용자가 자기 실행을 시작하고 결정하고 구독하고 이어 간다. */
type EndUserPath =
  | "/end-user/runs"
  | "/end-user/runs/{run_id}/approval"
  | "/end-user/runs/{run_id}/subscription"
  | "/end-user/runs/{run_id}/continuation";

/** 위젯 클라이언트가 아는 경로. 최종 사용자 경로 넷뿐이다. */
export type WidgetPaths = Pick<paths, EndUserPath>;

/**
 * 운영자 클라이언트가 아는 경로. 최종 사용자 경로를 뺀 운영자 경로 전부다. 계정으로 로그인한 관리 화면이 쓴다. 자격은
 * 쿠키라서 부르는 쪽이 토큰을 넘기지 않는다(admin-login 명세 "계약과 생성물").
 */
export type OperatorPaths = Omit<paths, EndUserPath>;

export type WidgetClient = Client<WidgetPaths>;
export type OperatorClient = Client<OperatorPaths>;
/** 요청 앞뒤에 끼는 함수 묶음. 화면이 갱신 규칙을 꽂는 자리(`OperatorClient.use`)의 타입이다. */
export type OperatorMiddleware = Middleware;

/**
 * 토큰을 받지 않는 운영자 클라이언트. 쿠키는 브라우저가 같은 출처의 중계(`/api/*`)에 스스로 싣는다. 관리 화면이 부르는
 * 운영자 경로 전부(관리, 채널의 시작과 이어 가기와 결정, 로그인)를 안다.
 */
export function createOperatorClient(): OperatorClient {
  return createClient<OperatorPaths>({ baseUrl: apiBaseUrl() });
}

/**
 * 최종 사용자 경로를 부르는 클라이언트. 기준 주소는 위젯이 사이트 설정에서 받은 런타임의 주소다.
 *
 * 서명 토큰을 들지 않는다. 부르는 쪽이 요청마다 `Authorization` 헤더로 넘긴다. 위젯은 토큰 손잡이가 실패한 것을
 * 요청을 보내기 전에 가려 401 과 같은 화면으로 보이기 때문이다(web-widget 명세 "api-client"). 스트림은
 * `EventSource` 가 아니라 이 클라이언트의 `parseAs: "stream"` 으로 받아 `readEndUserFrames` 로 읽고, 구독의
 * `Last-Event-ID` 는 계약의 헤더 파라미터(`params.header`)로 보낸다. 프레임 크기 상한은 두지 않는다(ADR 0024).
 */
export function createWidgetClient(baseUrl: URL): WidgetClient {
  return createClient<WidgetPaths>({ baseUrl: baseUrl.href });
}

// 같은 출처의 중계(`/api/*`)를 가리키는 절대 주소. 상대 경로 `/api` 는 브라우저에서는 되지만 jsdom 에서
// `Failed to parse URL` 로 섰다(`.scratch/web-admin/probes/jsdom_sse.sh`). 한 모양이어야 테스트가 제품 코드를 본다.
function apiBaseUrl(): string {
  return new URL("/api", location.origin).href;
}
