// 화면이 갱신을 부르는 규칙(admin-login 티켓 09, 명세 "화면이 갱신을 부르는 규칙"). 짧은 로그인(JWT)이 만료돼 401 을 받으면
// 갱신을 한 번 부르고 처음 요청을 한 번 다시 보낸다. 운영자는 알아채지 못한다. 규칙은 요청 함수 아래의 한 층이라, 어느 화면의
// 요청으로든 같다. 여기서는 플러그인 목록을 읽는 첫 화면으로 본다.
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 화면 이동은 가짜(`goTo`)가 받는다.

import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";
import { api, envelope, network, type PluginRow } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { signedIn, visited } from "../../testing/session";
import { listPlugins, setPluginEnabled } from "../../api/plugins";
import { HomePage } from "./HomePage";

const ROWS: PluginRow[] = [
  { kind: "agent", name: "broken", enabled: true, reason: "매니페스트를 읽을 수 없다" },
];

const EXPIRED = "/login?next=%2F&notice=expired";

function unauthorized(): Response {
  return HttpResponse.json(envelope("unauthorized", "로그인이 끝났다"), { status: 401 });
}

/** 플러그인 목록이 `replies` 의 차례대로 답하게 하고, 받은 횟수를 세는 함수를 돌려준다. 끝을 넘으면 마지막 답을 되풀이한다. */
function serveList(...replies: (() => Response)[]): () => number {
  let calls = 0;
  network.use(
    http.get(api("/plugins"), () => {
      const reply = replies[Math.min(calls, replies.length - 1)];
      calls += 1;
      return reply?.() ?? HttpResponse.json(ROWS);
    }),
  );
  return () => calls;
}

/** 갱신 요청에 답하고, 받은 횟수를 세는 함수를 돌려준다. */
function serveRefresh(reply: () => Response | Promise<Response>): () => number {
  let calls = 0;
  network.use(
    http.post(api("/auth/refresh"), () => {
      calls += 1;
      return reply();
    }),
  );
  return () => calls;
}

const ok = (): Response => HttpResponse.json(ROWS);
const renewed = (): Response => new Response(null, { status: 204 });

describe("401 을 받으면", () => {
  test("갱신을 한 번 부르고 처음 요청을 한 번 다시 보내 목록을 보인다", async () => {
    signedIn();
    const listCalls = serveList(unauthorized, ok);
    const refreshCalls = serveRefresh(renewed);

    renderPage(<HomePage />);

    expect(await screen.findByText("broken")).toBeTruthy();
    expect(listCalls()).toBe(2);
    expect(refreshCalls()).toBe(1);
    expect(visited()).toEqual([]);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("겹쳐 온 401 들은 갱신 하나를 함께 기다리고 각자 한 번씩 다시 보낸다", async () => {
    // 같은 때에 읽기 둘이 401 을 받는다. 갱신이 끝나기 전에는 어느 쪽도 답을 받지 못한다. 화면의 읽기는 앞의 읽기가 끝나야
    // 다음 읽기를 시작하는 줄이 많아 요청 함수를 바로 겹쳐 부른다(규칙은 요청 함수 아래의 한 층이다).
    let release: () => void = () => undefined;
    const held = new Promise<void>((resolve) => {
      release = resolve;
    });
    const refreshCalls = serveRefresh(async () => {
      await held;
      return renewed();
    });
    const listCalls = serveList(unauthorized, unauthorized, ok);

    const reads = Promise.all([listPlugins(), listPlugins()]);
    await waitFor(() => {
      expect(listCalls()).toBe(2);
    });
    release();

    expect(await reads).toEqual([ROWS, ROWS]);
    expect(refreshCalls()).toBe(1);
    expect(listCalls()).toBe(4);
  });

  test("본문이 있는 요청도 같은 본문 그대로 한 번 다시 보낸다", async () => {
    // 처음 요청은 보내면서 본문을 다 읽히므로, 규칙이 보내기 전에 복사해 둔 요청을 다시 보내야 본문이 남는다.
    const bodies: unknown[] = [];
    let calls = 0;
    network.use(
      http.put(api("/plugins/agent/broken/enabled"), async ({ request }) => {
        bodies.push(await request.json());
        calls += 1;
        return calls === 1 ? unauthorized() : new Response(null, { status: 204 });
      }),
    );
    const refreshCalls = serveRefresh(renewed);

    await setPluginEnabled("agent", "broken", { enabled: false });

    expect(bodies).toEqual([{ enabled: false }, { enabled: false }]);
    expect(refreshCalls()).toBe(1);
  });

  test("갱신이 끝난 뒤에 받은 새 401 은 새 갱신을 부른다", async () => {
    signedIn();
    const listCalls = serveList(unauthorized, ok);
    const refreshCalls = serveRefresh(renewed);
    renderPage(<HomePage />);
    await screen.findByText("broken");
    serveList(unauthorized, ok);

    // "새로 고침" 으로 다시 읽는다. 다시 401 이 오면 갱신을 또 한 번 부른다.
    screen.getByRole("button", { name: "새로 고침" }).click();

    await waitFor(() => {
      expect(refreshCalls()).toBe(2);
    });
    expect(listCalls()).toBe(2);
  });
});

describe("갱신이 거절되면", () => {
  test("로그인이 끝났다는 알림과 지금 주소를 달아 로그인 화면으로 보낸다", async () => {
    signedIn();
    serveList(unauthorized);
    const refreshCalls = serveRefresh(unauthorized);

    renderPage(<HomePage />);

    await waitFor(() => {
      expect(visited()).toEqual([EXPIRED]);
    });
    expect(refreshCalls()).toBe(1);
  });
});

describe("다시 보낸 요청이 또 401 이면", () => {
  test("갱신을 다시 부르지 않고 로그인 화면으로 보낸다", async () => {
    signedIn();
    const listCalls = serveList(unauthorized);
    const refreshCalls = serveRefresh(renewed);

    renderPage(<HomePage />);

    await waitFor(() => {
      expect(visited()).toEqual([EXPIRED]);
    });
    expect(listCalls()).toBe(2);
    expect(refreshCalls()).toBe(1);
  });
});

describe("갱신이 거절이 아닌 이유로 실패하면", () => {
  test("로그인이 끝났는지 모르므로 로그인 화면으로 보내지 않고 처음 요청의 실패를 보인다", async () => {
    signedIn();
    serveList(unauthorized);
    serveRefresh(() =>
      HttpResponse.json(envelope("internal_error", "서버가 멈췄다"), { status: 500 }),
    );

    renderPage(<HomePage />);

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(visited()).toEqual([]);
  });

  test("갱신 요청이 서버에 닿지 못해도 로그인 화면으로 보내지 않는다", async () => {
    signedIn();
    serveList(unauthorized);
    serveRefresh(() => HttpResponse.error());

    renderPage(<HomePage />);

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(visited()).toEqual([]);
  });
});

describe("401 이 아닌 실패는", () => {
  test("갱신을 부르지 않는다", async () => {
    signedIn();
    serveList(() =>
      HttpResponse.json(envelope("internal_error", "서버가 멈췄다"), { status: 500 }),
    );
    const refreshCalls = serveRefresh(renewed);

    renderPage(<HomePage />);

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(refreshCalls()).toBe(0);
  });
});
