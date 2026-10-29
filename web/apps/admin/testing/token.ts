// 토큰을 넣는다. 페이지 테스트는 운영자처럼 넣는 자리에 토큰을 넣고 시작한다. 관리 토큰을 넣으면 화면이 목록 요청
// 하나로 확인하므로 부르는 테스트가 `GET /plugins` 에 답해야 한다. 플러그인 목록을 보지 않는 화면의 테스트는
// `acceptTokens` 로 빈 목록을 답한다. 채널 토큰은 확인하지 않는다. 확인할 채널의 읽기 경로가 없다(ADR 0014).
//
// 채널 토큰을 넣는 자리와 토큰 지우기는 설정 화면에만 있다(admin-style 티켓 04). 그래서 그 둘은 시험이 그린 화면과
// 따로 설정 화면을 그려 거기서 하고 걷는다. 토큰은 탭의 저장소(스토어)에 남으므로 시험의 화면이 그대로 받는다. 앱에서
// 설정으로 옮겼다 돌아와도 토큰이 남는 것과 같다.

import { render, screen, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { createElement } from "react";
import { SettingsPage } from "../components/pages/SettingsPage";
import { api, network } from "./network";

export async function enterAdminToken(user: UserEvent, token: string): Promise<void> {
  await user.type(screen.getByLabelText("관리 토큰"), token);
  await user.click(screen.getByRole("button", { name: "넣기" }));
}

/** 채널 토큰을 설정 화면에서 넣는다. 관리 토큰은 이미 받아들여져 있어야 한다. 넣었다는 표시를 본 뒤 설정 화면을 걷는다. */
export async function enterChannelToken(user: UserEvent, token: string): Promise<void> {
  const settings = render(createElement(SettingsPage));
  const place = within(settings.container);
  await user.type(await place.findByLabelText("채널 토큰"), token);
  await user.click(place.getByRole("button", { name: "채널 토큰 넣기" }));
  await place.findByText("채널 토큰을 넣었다");
  settings.unmount();
}

/** 설정 화면의 토큰 지우기로 이 탭의 두 토큰을 지운다. 관리 토큰은 이미 받아들여져 있어야 한다. */
export async function clearTokens(user: UserEvent): Promise<void> {
  const settings = render(createElement(SettingsPage));
  await user.click(await within(settings.container).findByRole("button", { name: "토큰 지우기" }));
  settings.unmount();
}

/** 넣은 관리 토큰을 확인하는 목록 요청에 빈 목록으로 답한다. 그 화면은 그 밖에는 플러그인 목록을 읽지 않는다. */
export function acceptTokens(): void {
  network.use(http.get(api("/plugins"), () => HttpResponse.json([])));
}
