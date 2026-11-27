// 링크로 비밀번호 정하기 화면(admin-login 티켓 12). 로그인 없이 열리고 갱신 규칙을 지나지 않는다. 주소의 `#` 뒤를 읽은 즉시
// 주소창에서 지우고, 토큰으로 서버에서 읽어 오는 것이 없다. 주 이음매다. 화면을 그려 보고 HTTP 만 MSW 가 받는다.

import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";
import { api, envelope, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { visited } from "../../testing/session";
import { SetPasswordPage } from "./SetPasswordPage";

type User = ReturnType<typeof userEvent.setup>;

/** 주소를 `hash` 로 연 채 그린다. 토큰을 읽어 가는 일은 첫 그림에서 끝난다. */
async function openAt(hash: string): Promise<void> {
  history.replaceState(null, "", `/set-password${hash}`);
  renderPage(<SetPasswordPage />);
  await screen.findByRole("heading", { level: 1, name: "비밀번호 정하기" });
}

async function fill(user: User, label: string, text: string): Promise<void> {
  await user.click(screen.getByLabelText(label));
  await user.paste(text);
}

/** 서버가 받은 요청을 적는다. 로그인 여부를 묻거나 갱신을 부르면 이 수가 는다. */
function watchSession(): { me: () => number; refresh: () => number } {
  let me = 0;
  let refresh = 0;
  network.use(
    http.get(api("/auth/me"), () => {
      me += 1;
      return HttpResponse.json(envelope("unauthorized", "로그인이 필요하다"), { status: 401 });
    }),
    http.post(api("/auth/refresh"), () => {
      refresh += 1;
      return HttpResponse.json(envelope("unauthorized", "로그인이 끝났다"), { status: 401 });
    }),
  );
  return { me: () => me, refresh: () => refresh };
}

describe("주소의 토큰", () => {
  test("읽은 즉시 주소창에서 # 뒤를 지우고 방문 기록의 항목은 그대로 둔다", async () => {
    const before = history.length;

    await openAt("#tok-secret_1");

    await waitFor(() => {
      expect(location.hash).toBe("");
    });
    expect(location.pathname).toBe("/set-password");
    expect(history.length).toBe(before);
  });

  test("지운 뒤에도 그 토큰으로 보낸다", async () => {
    let sent: unknown = null;
    network.use(
      http.post(api("/auth/set-password"), async ({ request }) => {
        sent = await request.json();
        return new Response(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    await openAt("#tok-secret_1");
    await waitFor(() => {
      expect(location.hash).toBe("");
    });
    await fill(user, "새 비밀번호", "New-Pass1!x");
    await fill(user, "새 비밀번호 다시", "New-Pass1!x");

    await user.click(screen.getByRole("button", { name: "비밀번호 정하기" }));

    await waitFor(() => {
      expect(visited()).toEqual(["/login?notice=password-set"]);
    });
    expect(sent).toEqual({ token: "tok-secret_1", password: "New-Pass1!x" });
  });

  test("로그인 여부를 묻지 않고 계정 이름도 보이지 않으며 갱신 규칙을 지나지 않는다", async () => {
    const calls = watchSession();
    network.use(
      http.post(api("/auth/set-password"), () =>
        HttpResponse.json(envelope("unauthorized", "로그인이 필요하다"), { status: 401 }),
      ),
    );
    const user = userEvent.setup();
    await openAt("#tok-secret_1");
    await fill(user, "새 비밀번호", "New-Pass1!x");
    await fill(user, "새 비밀번호 다시", "New-Pass1!x");

    await user.click(screen.getByRole("button", { name: "비밀번호 정하기" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("비밀번호를 정하지 못했다");
    expect(calls.me()).toBe(0);
    expect(calls.refresh()).toBe(0);
    expect(visited()).toEqual([]);
  });
});

describe("정하기", () => {
  test("두 칸이 다르면 보내지 않고 둘째 칸 아래에 알린다", async () => {
    const user = userEvent.setup();
    await openAt("#tok-1");
    await fill(user, "새 비밀번호", "New-Pass1!x");
    await fill(user, "새 비밀번호 다시", "New-Pass1!y");

    await user.click(screen.getByRole("button", { name: "비밀번호 정하기" }));

    expect(screen.getByText("위 칸과 같지 않다")).toBeTruthy();
    expect(screen.getByLabelText("새 비밀번호 다시").getAttribute("aria-invalid")).toBe("true");
    expect(visited()).toEqual([]);
  });

  test("규칙을 다 맞추지 않으면 보내지 않고 규칙 목록이 알린다", async () => {
    const user = userEvent.setup();
    await openAt("#tok-1");
    await fill(user, "새 비밀번호", "short");
    await fill(user, "새 비밀번호 다시", "short");

    await user.click(screen.getByRole("button", { name: "비밀번호 정하기" }));

    const list = screen.getByRole("list", { name: "비밀번호 규칙" });
    expect(list.textContent).toContain("맞지 않음");
    expect(visited()).toEqual([]);
  });

  test("128자를 넘으면 첫째 칸 아래에 줄이라고 알린다", async () => {
    const user = userEvent.setup();
    await openAt("#tok-1");

    await fill(user, "새 비밀번호", "😀".repeat(129));

    expect(screen.getByText("128자 이하로 줄인다")).toBeTruthy();
  });

  test("서버가 비밀번호 규칙 위반으로 보면 그 문구를 첫째 칸 아래에 보인다", async () => {
    network.use(
      http.post(api("/auth/set-password"), () =>
        HttpResponse.json(
          {
            ...envelope("invalid_request", "요청의 형식이 올바르지 않다", "req-sp1"),
            violations: [{ field: "body.password", message: "제어 문자는 쓸 수 없다" }],
          },
          { status: 422 },
        ),
      ),
    );
    const user = userEvent.setup();
    await openAt("#tok-1");
    await fill(user, "새 비밀번호", "New-Pass1!x");
    await fill(user, "새 비밀번호 다시", "New-Pass1!x");

    await user.click(screen.getByRole("button", { name: "비밀번호 정하기" }));

    expect(await screen.findByText("제어 문자는 쓸 수 없다")).toBeTruthy();
    expect(visited()).toEqual([]);
  });
});

describe("쓸 수 없는 링크", () => {
  test("404 면 더 쓸 수 없다고 알리고 입력 칸을 걷고 로그인 화면으로 가는 링크를 둔다", async () => {
    network.use(
      http.post(api("/auth/set-password"), () =>
        HttpResponse.json(envelope("not_found", "이 링크는 더 쓸 수 없다"), { status: 404 }),
      ),
    );
    const user = userEvent.setup();
    await openAt("#tok-old");
    await fill(user, "새 비밀번호", "New-Pass1!x");
    await fill(user, "새 비밀번호 다시", "New-Pass1!x");

    await user.click(screen.getByRole("button", { name: "비밀번호 정하기" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("이 링크는 더 쓸 수 없다");
    expect(alert.textContent).toContain("관리하는 사람에게 새 링크를 받는다");
    expect(screen.queryByLabelText("새 비밀번호")).toBeNull();
    expect(screen.queryByRole("button", { name: "비밀번호 정하기" })).toBeNull();
    expect(screen.getByRole("link", { name: "로그인 화면으로" }).getAttribute("href")).toBe(
      "/login",
    );
  });

  test("주소에 # 뒤가 없으면 서버에 묻지 않고 처음부터 쓸 수 없는 링크로 보인다", async () => {
    await openAt("");

    expect((await screen.findByRole("alert")).textContent).toContain("이 링크는 더 쓸 수 없다");
    expect(screen.queryByLabelText("새 비밀번호")).toBeNull();
  });
});
