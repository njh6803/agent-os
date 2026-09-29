// 생성 클라이언트 둘(ADR 0021). 요청의 경로를 보고 토큰을 고르지 않는다. 고르는 것은 클라이언트다. 관리
// 클라이언트는 관리 토큰만, 채널 클라이언트는 채널 토큰만 싣는다. 한 토큰이 맡지 않은 경로에 실리는 실수는 타입이
// 막는다. 각 클라이언트가 아는 경로가 그 토큰이 여는 경로뿐이라서다.
//
// 서버의 접두사→토큰 표(`/runs` 아래는 채널, 그 밖은 관리. `.claude/rules/http.md`)를 여기서 다시 판정하지 않는다.
// TS 가 아는 것은 생성된 경로 키 가운데 어느 것이 채널의 것인가뿐이다. 계약에 경로가 늘면 관리 클라이언트의 타입에
// 새 경로가 보이고, 경로 목록을 고정한 타입 테스트(`clients.test-d.ts`)가 빨개진다.

import createClient, { type Client } from "openapi-fetch";
import type { paths } from "./generated/openapi";

/** 채널 토큰이 여는 경로. 실행을 일으키는 것과 결정을 내는 것이다. */
type ChannelPath = "/runs" | "/runs/{run_id}/approval";

/** 관리 클라이언트가 아는 경로. 생성된 경로에서 채널의 경로 둘을 뺀 것이다. */
export type AdminPaths = Omit<paths, ChannelPath>;

/** 채널 클라이언트가 아는 경로. 관리 화면이 채널에 내는 요청은 결정 하나뿐이다. */
export type ChannelPaths = Pick<paths, "/runs/{run_id}/approval">;

export type AdminClient = Client<AdminPaths>;
export type ChannelClient = Client<ChannelPaths>;

/** 관리 토큰을 싣는 클라이언트. */
export function createAdminClient(adminToken: string): AdminClient {
  return createClient<AdminPaths>({ baseUrl: apiBaseUrl(), headers: bearer(adminToken) });
}

/** 채널 토큰을 싣는 클라이언트. */
export function createChannelClient(channelToken: string): ChannelClient {
  return createClient<ChannelPaths>({ baseUrl: apiBaseUrl(), headers: bearer(channelToken) });
}

// 같은 출처의 중계(`/api/*`)를 가리키는 절대 주소. 상대 경로 `/api` 는 브라우저에서는 되지만 jsdom 에서
// `Failed to parse URL` 로 섰다(`.scratch/web-admin/probes/jsdom_sse.sh`). 한 모양이어야 테스트가 제품 코드를 본다.
function apiBaseUrl(): string {
  return new URL("/api", location.origin).href;
}

function bearer(token: string): { readonly Authorization: string } {
  return { Authorization: `Bearer ${token}` };
}
