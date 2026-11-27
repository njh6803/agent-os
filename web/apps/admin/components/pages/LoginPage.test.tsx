// 로그인 화면(admin-login 티켓 09). 운영자가 이름과 비밀번호를 넣어 로그인하고 보던 화면으로 돌아간다.
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 화면 이동은 가짜(`goTo`)가 받아 어디로 보냈는지만 본다. 주소의
// 질의(`next`, `notice`)는 그리기 전에 jsdom 의 주소에 심는다. 로그인, 갱신, 첫 계정 확인은 401 을 받아도 갱신하지 않는다.
// 갱신 경로에 핸들러를 두지 않았으므로, 그 경로를 부르면 처리하지 않은 요청으로 시험이 빨개진다(`testing/setup.ts`).

import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";
import { api, envelope, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { signedIn, signedOut, visited } from "../../testing/session";
import { LoginPage } from "./LoginPage";

/** 이 서버에 계정이 있는가를 답한다. */
function serveSetup({ needsFirstAccount }: { readonly needsFirstAccount: boolean }): void {
  network.use(
    http.get(api("/auth/setup"), () =>
      HttpResponse.json({ needs_first_account: needsFirstAccount }),
    ),
  );
}

/** 로그인 요청에 답하고, 받은 본문을 쌓아 돌려준다. */
function serveLogin(reply: () => Response): unknown[] {
  const bodies: unknown[] = [];
  network.use(
    http.post(api("/auth/login"), async ({ request }) => {
      bodies.push(await request.json());
      return reply();
    }),
  );
  return bodies;
}

/** 로그인하지 않은 운영자가 주소 `place` 로 로그인 화면을 연다. */
async function openLogin(place = "/login"): Promise<void> {
  history.replaceState(null, "", place);
  signedOut();
  serveSetup({ needsFirstAccount: false });
  renderPage(<LoginPage />);
  await screen.findByRole("heading", { level: 1, name: "로그인" });
}

async function signInAs(name: string, password: string): Promise<void> {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("계정 이름"), name);
  await user.type(screen.getByLabelText("비밀번호"), password);
  await user.click(screen.getByRole("button", { name: "로그인" }));
}

/** 이 주소 기준으로 푼 절대 주소. */
function absolute(path: string): string {
  return new URL(path, location.origin).href;
}

describe("로그인", () => {
  test("이름과 비밀번호를 서버에 보내고 돌아갈 곳이 없으면 첫 화면으로 보낸다", async () => {
    await openLogin();
    const bodies = serveLogin(() => new Response(null, { status: 204 }));

    await signInAs("kim.dev", "test-password-1");

    await expect.poll(visited).toEqual([absolute("/")]);
    expect(bodies).toEqual([{ name: "kim.dev", password: "test-password-1" }]);
  });

  test("쫓겨난 화면(next)으로 돌아간다", async () => {
    await openLogin("/login?next=%2Fruns%3Fstatus%3Dfailed");
    serveLogin(() => new Response(null, { status: 204 }));

    await signInAs("kim.dev", "test-password-1");

    await expect.poll(visited).toEqual([absolute("/runs?status=failed")]);
  });

  test.each([
    ["다른 사이트의 주소", "https://evil.test/"],
    ["빗금 둘로 시작해 다른 사이트로 읽히는 주소", "//evil.test"],
    ["탭이 끼어 다른 사이트로 읽히는 주소", "/\t/evil.test"],
    ["줄바꿈이 끼어 다른 사이트로 읽히는 주소", "/\n/evil.test"],
    ["로그인 화면 자신", "/login"],
  ])("돌아갈 곳이 %s 면 받지 않고 첫 화면으로 보낸다", async (_name, next) => {
    await openLogin(`/login?next=${encodeURIComponent(next)}`);
    serveLogin(() => new Response(null, { status: 204 }));

    await signInAs("kim.dev", "test-password-1");

    await expect.poll(visited).toEqual([absolute("/")]);
  });

  test("같은 출처의 절대 주소가 빗금 둘로 시작하는 경로를 들면 이동은 그 절대 주소 그대로라 다른 사이트로 나가지 않는다", async () => {
    const target = `${location.origin}//evil.test/x`;
    await openLogin(`/login?next=${encodeURIComponent(target)}`);
    serveLogin(() => new Response(null, { status: 204 }));

    await signInAs("kim.dev", "test-password-1");

    await expect.poll(visited).toEqual([target]);
  });

  test("이름이나 비밀번호가 맞지 않으면 입력 칸 위에 알림을 남기고 비밀번호 칸만 비운다", async () => {
    await openLogin();
    serveLogin(() =>
      HttpResponse.json(envelope("unauthorized", "이름이나 비밀번호가 맞지 않다"), { status: 401 }),
    );

    await signInAs("kim.dev", "wrong-password");

    expect((await screen.findByRole("alert")).textContent).toContain("로그인하지 못했다");
    expect(screen.getByLabelText("비밀번호")).toHaveProperty("value", "");
    expect(screen.getByLabelText("계정 이름")).toHaveProperty("value", "kim.dev");
    expect(visited()).toEqual([]);
  });

  test("다시 시도하면 앞의 거절 알림이 걷힌다", async () => {
    await openLogin();
    serveLogin(() =>
      HttpResponse.json(envelope("unauthorized", "이름이나 비밀번호가 맞지 않다"), { status: 401 }),
    );
    await signInAs("kim.dev", "wrong-password");
    await screen.findByRole("alert");
    serveLogin(() => new Response(null, { status: 204 }));

    const user = userEvent.setup();
    await user.type(screen.getByLabelText("비밀번호"), "test-password-1");
    await user.click(screen.getByRole("button", { name: "로그인" }));

    await expect.poll(visited).toEqual([absolute("/")]);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("서버가 오류를 내면 거절과 다른 실패 알림을 보이고 화면을 옮기지 않는다", async () => {
    await openLogin();
    serveLogin(() =>
      HttpResponse.json(envelope("internal_error", "서버가 멈췄다", "req-7a31"), { status: 500 }),
    );

    await signInAs("kim.dev", "test-password-1");

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("로그인을 보내지 못했다");
    expect(alert.textContent).toContain("서버가 멈췄다");
    expect(alert.textContent).toContain("req-7a31");
    expect(visited()).toEqual([]);
  });

  test("서버에 닿지 못하면 서버에 닿지 못했다고 알린다", async () => {
    await openLogin();
    network.use(http.post(api("/auth/login"), () => HttpResponse.error()));

    await signInAs("kim.dev", "test-password-1");

    expect((await screen.findByRole("alert")).textContent).toContain("서버에 닿지 못했다");
    expect(visited()).toEqual([]);
  });
});

describe("이미 로그인한 채 연 로그인 화면", () => {
  test("쫓겨난 화면으로 보내고 입력 칸을 세우지 않는다", async () => {
    history.replaceState(null, "", "/login?next=%2Fruns");
    signedIn();
    serveSetup({ needsFirstAccount: false });

    renderPage(<LoginPage />);

    await expect.poll(visited).toEqual([absolute("/runs")]);
    expect(screen.queryByLabelText("계정 이름")).toBeNull();
  });

  test("돌아갈 곳이 없으면 첫 화면으로 보낸다", async () => {
    history.replaceState(null, "", "/login");
    signedIn();
    serveSetup({ needsFirstAccount: false });

    renderPage(<LoginPage />);

    await expect.poll(visited).toEqual([absolute("/")]);
  });

  test("비밀번호를 정한 뒤(notice=password-set)에는 보내지 않고 로그인 화면을 그대로 둔다", async () => {
    history.replaceState(null, "", "/login?notice=password-set");
    signedIn();
    serveSetup({ needsFirstAccount: false });

    renderPage(<LoginPage />);

    expect(await screen.findByLabelText("계정 이름")).toBeTruthy();
    expect(screen.getByText("비밀번호를 정했다")).toBeTruthy();
    expect(visited()).toEqual([]);
  });
});

describe("이전 화면이 남긴 알림", () => {
  test.each([
    ["logged-out", "로그아웃했다"],
    ["expired", "로그인이 끝났다"],
    ["password-set", "비밀번호를 정했다"],
  ])('notice=%s 면 "%s" 를 보인다', async (notice, title) => {
    await openLogin(`/login?notice=${notice}`);

    expect(screen.getByRole("status").textContent).toContain(title);
  });

  test("모르는 값은 알림 없이 로그인 화면만 보인다", async () => {
    await openLogin("/login?notice=hacked");

    expect(screen.queryByRole("status")).toBeNull();
    expect(screen.getByLabelText("계정 이름")).toBeTruthy();
  });
});

describe("계정이 하나도 없는 서버", () => {
  test("입력 칸 대신 첫 계정을 만드는 명령 두 꼴을 보인다", async () => {
    history.replaceState(null, "", "/login");
    signedOut();
    serveSetup({ needsFirstAccount: true });

    renderPage(<LoginPage />);

    expect(await screen.findByRole("heading", { level: 1, name: "첫 계정을 만든다" })).toBeTruthy();
    expect(screen.getByText("agent-os operator system-admin <계정 이름>")).toBeTruthy();
    expect(
      screen.getByText("docker compose exec serve agent-os operator system-admin <계정 이름>"),
    ).toBeTruthy();
    expect(screen.queryByLabelText("계정 이름")).toBeNull();
    expect(screen.queryByLabelText("비밀번호")).toBeNull();
  });

  test("첫 계정 확인이 401 이어도 갱신하지 않고 입력 칸을 보인다", async () => {
    // 지금 누구인지는 읽히게 둔다(비밀번호를 정한 뒤의 화면이라 로그인 화면에 머문다). 그래서 갱신을 부를 수 있는 요청은
    // 첫 계정 확인 하나다.
    history.replaceState(null, "", "/login?notice=password-set");
    signedIn();
    let refreshCalls = 0;
    network.use(
      http.get(api("/auth/setup"), () =>
        HttpResponse.json(envelope("unauthorized", "로그인이 필요하다"), { status: 401 }),
      ),
      http.post(api("/auth/refresh"), () => {
        refreshCalls += 1;
        return new Response(null, { status: 204 });
      }),
    );

    renderPage(<LoginPage />);

    expect(await screen.findByLabelText("계정 이름")).toBeTruthy();
    expect(refreshCalls).toBe(0);
  });
});

describe("저장소", () => {
  test("옛 판이 이 탭에 남긴 토큰 저장 키를 지운다", async () => {
    sessionStorage.setItem("agent-os-admin-tokens", '{"state":{"adminToken":"adm-old"}}');

    await openLogin();

    expect(sessionStorage.getItem("agent-os-admin-tokens")).toBeNull();
  });
});
