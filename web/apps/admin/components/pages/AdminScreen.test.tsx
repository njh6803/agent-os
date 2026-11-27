// 로그인한 화면의 문과 계정 메뉴(admin-login 티켓 09). 화면은 "지금 누구인지"(`GET /auth/me`)를 읽은 뒤에야 틀과 본문을 그린다.
// 읽지 못하면 로그인 화면으로 보내고, 계정 메뉴의 로그아웃은 세 갈래(204, 갱신의 401, 쿠키를 지우는 응답 없음)로 끝난다.
//
// 주 이음매다. 설정 화면을 그려 보고 HTTP 만 MSW 가 받는다. 화면 이동은 가짜(`goTo`)가 받는다.

import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";
import { api, envelope, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { ME, signedIn, signedOut, visited } from "../../testing/session";
import { SettingsPage } from "./SettingsPage";

const LOGGED_OUT = "/login?notice=logged-out";

/** 로그인한 채 설정 화면을 열고 본문이 설 때까지 기다린다. */
async function openSettings(me: Partial<typeof ME> = {}): Promise<void> {
  signedIn(me);
  renderPage(<SettingsPage />);
  await screen.findByRole("heading", { level: 1, name: "설정" });
}

/** 계정 자리를 눌러 메뉴를 열고 "로그아웃" 항목을 돌려준다. */
async function openMenu(): Promise<HTMLElement> {
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: /kim\.dev/ }));
  return screen.getByRole("menuitem", { name: "로그아웃" });
}

describe("지금 누구인지 읽기", () => {
  test("읽는 동안은 틀만 서고 본문과 계정 자리는 비어 있다", async () => {
    let answer: () => void = () => undefined;
    const waiting = new Promise<void>((resolve) => {
      answer = resolve;
    });
    network.use(
      http.get(api("/auth/me"), async () => {
        await waiting;
        return HttpResponse.json(ME);
      }),
    );

    renderPage(<SettingsPage />);

    expect(screen.getByRole("navigation", { name: "관리 화면" })).toBeTruthy();
    expect(screen.queryByRole("heading", { level: 1, name: "설정" })).toBeNull();
    expect(screen.queryByRole("button", { name: /kim\.dev/ })).toBeNull();

    answer();
    expect(await screen.findByRole("heading", { level: 1, name: "설정" })).toBeTruthy();
    expect(screen.getByRole("button", { name: /kim\.dev/ })).toBeTruthy();
  });

  test("계정의 이름과 단계를 계정 자리에 보인다", async () => {
    await openSettings({ name: "lee.ops", tier: "system_admin" });

    const spot = screen.getByRole("button", { name: /lee\.ops/ });
    expect(spot.textContent).toContain("lee.ops");
    expect(spot.textContent).toContain("시스템 관리자");
  });

  test("관리자 단계는 관리자라고 보인다", async () => {
    await openSettings({ tier: "admin" });

    expect(screen.getByRole("button", { name: /kim\.dev/ }).textContent).toContain("관리자");
  });

  test("로그인하지 않았으면 지금 주소를 돌아올 곳으로 달아 로그인 화면으로 보낸다", async () => {
    history.replaceState(null, "", "/settings?tab=theme");
    signedOut();

    renderPage(<SettingsPage />);

    await waitFor(() => {
      expect(visited()).toEqual(["/login?next=%2Fsettings%3Ftab%3Dtheme"]);
    });
    expect(screen.queryByRole("heading", { level: 1, name: "설정" })).toBeNull();
  });

  test("서버에 닿지 못하면 로그인 화면으로 보내지 않고 실패를 알린다", async () => {
    network.use(http.get(api("/auth/me"), () => HttpResponse.error()));

    renderPage(<SettingsPage />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("로그인한 계정을 읽지 못했다");
    expect(alert.textContent).toContain("서버에 닿지 못했다");
    expect(visited()).toEqual([]);
  });

  test("서버가 오류를 내면 봉투의 메시지를 알리고 로그인 화면으로 보내지 않는다", async () => {
    network.use(
      http.get(api("/auth/me"), () =>
        HttpResponse.json(envelope("internal_error", "서버가 멈췄다", "req-9c02"), { status: 500 }),
      ),
    );

    renderPage(<SettingsPage />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("서버가 멈췄다");
    expect(alert.textContent).toContain("req-9c02");
    expect(visited()).toEqual([]);
  });

  test("읽은 적이 있는 화면에서 다시 읽다 서버가 오류를 내면 보인 계정과 본문을 지우고 실패만 보인다", async () => {
    const cache = new Map();
    signedIn();
    const first = renderPage(<SettingsPage />, cache);
    await screen.findByRole("heading", { level: 1, name: "설정" });
    first.unmount();

    network.use(
      http.get(api("/auth/me"), () =>
        HttpResponse.json(envelope("internal_error", "서버가 멈췄다", "req-4d17"), { status: 500 }),
      ),
    );
    renderPage(<SettingsPage />, cache);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("서버가 멈췄다");
    expect(screen.queryByRole("heading", { level: 1, name: "설정" })).toBeNull();
    expect(screen.queryByRole("button", { name: /kim\.dev/ })).toBeNull();
    expect(visited()).toEqual([]);
  });
});

describe("계정 메뉴", () => {
  test("계정 자리를 누르면 로그아웃 하나가 든 메뉴가 열리고 Esc 로 닫힌다", async () => {
    await openSettings();
    const user = userEvent.setup();
    const spot = screen.getByRole("button", { name: /kim\.dev/ });
    expect(spot.getAttribute("aria-expanded")).toBe("false");

    await user.click(spot);

    expect(spot.getAttribute("aria-expanded")).toBe("true");
    const menu = screen.getByRole("menu", { name: "kim.dev 계정" });
    expect(
      Array.from(menu.querySelectorAll('[role="menuitem"]')).map((item) => item.textContent),
    ).toEqual(["로그아웃"]);

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("menu")).toBeNull();
    expect(spot.getAttribute("aria-expanded")).toBe("false");
  });

  test("메뉴 밖을 누르면 닫힌다", async () => {
    await openSettings();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /kim\.dev/ }));

    await user.click(screen.getByRole("heading", { level: 1, name: "설정" }));

    expect(screen.queryByRole("menu")).toBeNull();
  });
});

describe("로그아웃", () => {
  test("서버가 204 로 답하면 로그아웃했다는 알림과 함께 로그인 화면으로 보낸다", async () => {
    await openSettings();
    let calls = 0;
    network.use(
      http.post(api("/auth/logout"), () => {
        calls += 1;
        return new Response(null, { status: 204 });
      }),
    );

    const user = userEvent.setup();
    await user.click(await openMenu());

    await waitFor(() => {
      expect(visited()).toEqual([LOGGED_OUT]);
    });
    expect(calls).toBe(1);
  });

  test("짧은 로그인이 끝나 401 이고 갱신도 401 이면 쿠키를 지우는 응답을 받은 것이라 같은 곳으로 보낸다", async () => {
    await openSettings();
    network.use(
      http.post(api("/auth/logout"), () =>
        HttpResponse.json(envelope("unauthorized", "로그인이 끝났다"), { status: 401 }),
      ),
      http.post(api("/auth/refresh"), () =>
        HttpResponse.json(envelope("unauthorized", "로그인이 끝났다"), { status: 401 }),
      ),
    );

    const user = userEvent.setup();
    await user.click(await openMenu());

    await waitFor(() => {
      expect(visited()).toEqual([LOGGED_OUT]);
    });
  });

  test("로그아웃이 401 이어도 갱신이 되면 다시 보낸 로그아웃의 204 로 로그인 화면에 보낸다", async () => {
    await openSettings();
    let logouts = 0;
    let refreshes = 0;
    network.use(
      http.post(api("/auth/logout"), () => {
        logouts += 1;
        return logouts === 1
          ? HttpResponse.json(envelope("unauthorized", "만료됐다"), { status: 401 })
          : new Response(null, { status: 204 });
      }),
      http.post(api("/auth/refresh"), () => {
        refreshes += 1;
        return new Response(null, { status: 204 });
      }),
    );

    const user = userEvent.setup();
    await user.click(await openMenu());

    await waitFor(() => {
      expect(visited()).toEqual([LOGGED_OUT]);
    });
    expect(logouts).toBe(2);
    expect(refreshes).toBe(1);
  });

  test("쿠키를 지우는 응답을 받지 못하면 로그인 화면으로 보내지 않고 메뉴에서 알린다", async () => {
    await openSettings();
    network.use(http.post(api("/auth/logout"), () => HttpResponse.error()));

    const user = userEvent.setup();
    await user.click(await openMenu());

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe("로그아웃하지 못했다. 다시 누른다");
    expect(screen.getByRole("menu", { name: "kim.dev 계정" })).toBeTruthy();
    expect(visited()).toEqual([]);
  });

  test("서버가 500 을 내도 로그인 화면으로 보내지 않고 같은 알림을 보인다", async () => {
    await openSettings();
    network.use(
      http.post(api("/auth/logout"), () =>
        HttpResponse.json(envelope("internal_error", "서버가 멈췄다"), { status: 500 }),
      ),
    );

    const user = userEvent.setup();
    await user.click(await openMenu());

    expect((await screen.findByRole("alert")).textContent).toBe("로그아웃하지 못했다. 다시 누른다");
    expect(visited()).toEqual([]);
  });

  test("요청이 가는 동안에는 Esc 와 메뉴 밖 누르기와 계정 단추로 메뉴가 닫히지 않아 실패 알림이 그 자리에 선다", async () => {
    await openSettings();
    let answer: () => void = () => undefined;
    const waiting = new Promise<void>((resolve) => {
      answer = resolve;
    });
    network.use(
      http.post(api("/auth/logout"), async () => {
        await waiting;
        return HttpResponse.json(envelope("internal_error", "서버가 멈췄다"), { status: 500 });
      }),
    );
    const user = userEvent.setup();
    await user.click(await openMenu());

    await user.keyboard("{Escape}");
    await user.click(screen.getByRole("heading", { level: 1, name: "설정" }));
    await user.click(screen.getByRole("button", { name: /kim\.dev/ }));

    expect(screen.getByRole("menu", { name: "kim.dev 계정" })).toBeTruthy();
    answer();
    expect((await screen.findByRole("alert")).textContent).toBe("로그아웃하지 못했다. 다시 누른다");
    expect(visited()).toEqual([]);
  });

  test("실패한 뒤 다시 누르면 알림이 걷히고 이번에 성공하면 로그인 화면으로 보낸다", async () => {
    await openSettings();
    let calls = 0;
    network.use(
      http.post(api("/auth/logout"), () => {
        calls += 1;
        return calls === 1 ? HttpResponse.error() : new Response(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    await user.click(await openMenu());
    await screen.findByRole("alert");

    await user.click(screen.getByRole("menuitem", { name: "로그아웃" }));

    await waitFor(() => {
      expect(visited()).toEqual([LOGGED_OUT]);
    });
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("저장소", () => {
  test("화면이 뜨면 옛 판이 이 탭에 남긴 토큰 저장 키를 지운다", async () => {
    sessionStorage.setItem("agent-os-admin-tokens", '{"state":{"adminToken":"adm-old"}}');

    await openSettings();

    expect(sessionStorage.getItem("agent-os-admin-tokens")).toBeNull();
  });
});
