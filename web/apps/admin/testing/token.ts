// 관리 토큰을 넣는다. 페이지 테스트는 운영자처럼 넣는 자리에 토큰을 넣고 시작한다. 넣으면 화면이 목록 요청 하나로
// 확인하므로 부르는 테스트가 `GET /plugins` 에 답해야 한다. 플러그인 목록을 보지 않는 화면의 테스트는 `acceptTokens` 로
// 빈 목록을 답한다.

import { screen } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { api, network } from "./network";

export async function enterAdminToken(user: UserEvent, token: string): Promise<void> {
  await user.type(screen.getByLabelText("관리 토큰"), token);
  await user.click(screen.getByRole("button", { name: "넣기" }));
}

/** 넣은 관리 토큰을 확인하는 목록 요청에 빈 목록으로 답한다. 그 화면은 그 밖에는 플러그인 목록을 읽지 않는다. */
export function acceptTokens(): void {
  network.use(http.get(api("/plugins"), () => HttpResponse.json([])));
}
