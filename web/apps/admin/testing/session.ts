// 페이지 테스트의 로그인 도우미. 관리 화면은 토큰이 아니라 쿠키로 로그인하고, 화면은 "지금 누구인지"(`GET /auth/me`)를 읽어서만
// 로그인했는지 안다(admin-login 티켓 09). 그래서 로그인한 화면을 그리는 테스트는 그 읽기에 답한다. 쿠키는 HttpOnly 라
// 테스트가 만지지 않는다. 가짜는 HTTP 하나에만 둔다.
//
// 화면 이동(`goTo`)은 `setup.ts` 가 가짜로 바꿔 두었다. 테스트는 `visited()` 로 어디로 보냈는지 본다.

import { http, HttpResponse } from "msw";
import { vi } from "vitest";
import { goTo, type Me } from "../api/session";
import { api, envelope, network } from "./network";

/** 기본 계정. 관리자다. */
export const ME: Me = {
  name: "kim.dev",
  tier: "admin",
  token_minutes: 5,
  run_timeout_seconds: 300,
};

/** 로그인한 채로 둔다. `GET /auth/me` 가 계정을 돌려준다. 갱신 경로는 쓰지 않는다. */
export function signedIn(me: Partial<Me> = {}): void {
  network.use(http.get(api("/auth/me"), () => HttpResponse.json({ ...ME, ...me })));
}

/** 로그인하지 않은 채로 둔다. 지금 누구인지도 갱신도 401 이다. */
export function signedOut(): void {
  network.use(
    http.get(api("/auth/me"), () =>
      HttpResponse.json(envelope("unauthorized", "로그인이 필요하다"), { status: 401 }),
    ),
    http.post(api("/auth/refresh"), () =>
      HttpResponse.json(envelope("unauthorized", "로그인이 끝났다"), { status: 401 }),
    ),
  );
}

/** 화면이 `goTo` 로 보낸 주소들. 보낸 차례다. */
export function visited(): string[] {
  return vi.mocked(goTo).mock.calls.map(([href]) => href);
}
