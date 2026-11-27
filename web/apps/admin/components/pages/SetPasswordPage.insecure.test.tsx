// 링크로 비밀번호 정하기 화면이 https 가 아닌 주소에서 정하기를 막고 알린다(admin-login 티켓 12, PR 리뷰의 지적). 이 화면은 쿠키를
// 쓰지 않지만 새 비밀번호를 본문에 담아 보내므로, 평문 http 로 오가지 않게 로그인 화면과 같은 판정(`canSignInAt`)으로 막는다. 주소가
// 갈리는 곳은 그 함수이고(`api/session/address.test.ts` 가 값마다 본다), 여기서는 그 판정이 알림과 단추 막기에 이어졌는지를 본다.
// 입력 칸은 열려 있고 막히는 것은 정하기 단추뿐이다.
//
// jsdom 의 주소는 출처를 바꿀 수 없어 지금 주소를 읽는 훅(`useCurrentUrl`)만 가짜로 바꾼다(`LoginPage.insecure.test` 와 같은 길).

import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http } from "msw";
import { describe, expect, test, vi } from "vitest";
import { api, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { SetPasswordPage } from "./SetPasswordPage";

const opened = vi.hoisted(() => ({ href: "http://localhost:3000/set-password" }));

vi.mock("../../hooks/useCurrentUrl", () => ({ useCurrentUrl: () => new URL(opened.href) }));

/** 주소 `href` 로 연 것으로 보고 화면이 설 때까지 기다린다. */
async function openAt(href: string): Promise<void> {
  opened.href = href;
  history.replaceState(null, "", "/set-password#tok-secret_1");
  renderPage(<SetPasswordPage />);
  await screen.findByRole("heading", { level: 1, name: "비밀번호 정하기" });
}

const WARNING = "이 주소에서는 비밀번호를 정할 수 없다";

describe("https 가 아닌 주소", () => {
  test.each([
    ["이름이 있는 호스트", "http://admin.example:3000/set-password"],
    ["루프백처럼 보이는 이름의 다른 호스트", "http://localhost.evil.test:3000/set-password"],
    ["사설 주소", "http://192.168.0.7:3000/set-password"],
  ])("%s 의 http 주소는 알리고 정하기 단추만 막으며 서버로 보내지 않는다", async (_name, href) => {
    let sent = 0;
    network.use(
      http.post(api("/auth/set-password"), () => {
        sent += 1;
        return new Response(null, { status: 204 });
      }),
    );
    await openAt(href);

    expect(screen.getByText(WARNING)).toBeTruthy();
    expect(screen.getByLabelText("새 비밀번호")).toHaveProperty("disabled", false);
    expect(screen.getByLabelText("새 비밀번호 다시")).toHaveProperty("disabled", false);
    const button = screen.getByRole("button", { name: "비밀번호 정하기" });
    expect(button).toHaveProperty("disabled", true);
    await userEvent.setup().click(button);
    expect(sent).toBe(0);
  });

  test.each([
    ["https 주소", "https://admin.example/set-password"],
    ["localhost", "http://localhost:3000/set-password"],
    ["127.0.0.1", "http://127.0.0.1:3000/set-password"],
    ["[::1]", "http://[::1]:3000/set-password"],
  ])("%s 에서는 알림 없이 입력 칸과 단추가 열려 있다", async (_name, href) => {
    await openAt(href);

    expect(screen.queryByText(WARNING)).toBeNull();
    expect(screen.getByLabelText("새 비밀번호")).toHaveProperty("disabled", false);
    expect(screen.getByRole("button", { name: "비밀번호 정하기" })).toHaveProperty(
      "disabled",
      false,
    );
  });
});
