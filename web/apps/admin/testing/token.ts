// 관리 토큰을 넣는다. 페이지 테스트는 운영자처럼 넣는 자리에 토큰을 넣고 시작한다. 넣으면 화면이 목록 요청 하나로
// 확인하므로 부르는 테스트가 `GET /plugins` 에 답해야 한다.

import { screen } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";

export async function enterAdminToken(user: UserEvent, token: string): Promise<void> {
  await user.type(screen.getByLabelText("관리 토큰"), token);
  await user.click(screen.getByRole("button", { name: "넣기" }));
}
