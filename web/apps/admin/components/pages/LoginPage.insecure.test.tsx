// 로그인 화면이 https 가 아닌 주소에서 로그인을 막고 알린다(admin-login 티켓 09). 쿠키(`__Host-` 이름, `Secure`)는 https 나
// 루프백 주소에서만 받아지므로(`.scratch/admin-login/probes/cookie_relay`), 그 밖의 http 주소에서 넣은 비밀번호는 로그인이
// 되지 않는다. 주소가 갈리는 곳은 `canSignInAt` 이고(`api/session/address.test.ts` 가 값마다 본다), 여기서는 그 판정이 화면의
// 알림과 입력 칸 막기에 이어졌는지를 본다.
//
// jsdom 의 주소는 출처를 바꿀 수 없어 지금 주소를 읽는 훅(`useCurrentUrl`)만 가짜로 바꾼다. 요청이 가는 곳(`api()`)은
// jsdom 의 출처 그대로다.

import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, test, vi } from "vitest";
import { api, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { signedOut } from "../../testing/session";
import { LoginPage } from "./LoginPage";

const opened = vi.hoisted(() => ({ href: "http://localhost:3000/login" }));

vi.mock("../../hooks/useCurrentUrl", () => ({ useCurrentUrl: () => new URL(opened.href) }));

/** 로그인하지 않은 운영자가 주소 `href` 로 로그인 화면을 열고 입력 칸이 설 때까지 기다린다. */
async function openAt(href: string): Promise<void> {
  opened.href = href;
  signedOut();
  network.use(
    http.get(api("/auth/setup"), () => HttpResponse.json({ needs_first_account: false })),
  );
  renderPage(<LoginPage />);
  await screen.findByRole("heading", { level: 1, name: "로그인" });
}

const WARNING = "이 주소에서는 로그인할 수 없다";

describe("https 가 아닌 주소", () => {
  test.each([
    ["이름이 있는 호스트", "http://admin.example:3000/login"],
    ["루프백처럼 보이는 이름의 다른 호스트", "http://localhost.evil.test:3000/login"],
    ["사설 주소", "http://192.168.0.7:3000/login"],
  ])(
    "%s 의 http 주소는 https 가 아니라 로그인할 수 없다고 알리고 입력 칸과 단추를 막는다",
    async (_name, href) => {
      await openAt(href);

      expect(screen.getByText(WARNING)).toBeTruthy();
      expect(screen.getByLabelText("계정 이름")).toHaveProperty("disabled", true);
      expect(screen.getByLabelText("비밀번호")).toHaveProperty("disabled", true);
      expect(screen.getByRole("button", { name: "로그인" })).toHaveProperty("disabled", true);
    },
  );

  test.each([
    ["https 주소", "https://admin.example/login"],
    ["localhost", "http://localhost:3000/login"],
    ["127.0.0.1", "http://127.0.0.1:3000/login"],
    ["[::1]", "http://[::1]:3000/login"],
  ])("%s 에서는 알림 없이 입력 칸과 단추가 열려 있다", async (_name, href) => {
    await openAt(href);

    expect(screen.queryByText(WARNING)).toBeNull();
    expect(screen.getByLabelText("계정 이름")).toHaveProperty("disabled", false);
    expect(screen.getByLabelText("비밀번호")).toHaveProperty("disabled", false);
    expect(screen.getByRole("button", { name: "로그인" })).toHaveProperty("disabled", false);
  });
});
