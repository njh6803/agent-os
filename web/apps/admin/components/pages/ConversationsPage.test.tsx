// 대화 목록(admin-login 티켓 10). 운영자가 대화를 끝 실행이 최근인 것부터 보고, 상태로 거르고, 한 쪽을 넘으면 이어서 더 본다.
// 줄을 누르면 `/chat/<끝 실행>` 으로 간다. 저절로 다시 읽지 않는다.
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. jsdom 은 Tailwind 의 CSS 를 싣지 않아 컨테이너 질의를 풀지
// 않는다. 그래서 표와 카드가 함께 보인다. 줄의 글자를 보는 단언은 두 갈래에 함께 건다. 어느 갈래가 어느 폭에서 서는지는
// 스토리가 본다. 시간대는 `pages` 프로젝트가 America/New_York 으로 고정한다(web/vitest.config.ts).

import { screen, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, test, vi } from "vitest";
import {
  api,
  envelope,
  network,
  type Conversation,
  type ConversationPage,
  type ConversationRow,
} from "../../testing/network";
import { renderPage } from "../../testing/render";
import { signedIn } from "../../testing/session";
import { ConversationsPage } from "./ConversationsPage";

function conversation(lastRun: string, extra: Partial<Conversation> = {}): Conversation {
  return {
    agent: "support-bot",
    complete: true,
    first_request: `${lastRun}의 첫 요청`,
    last_at: "2026-11-27T01:05:30+00:00",
    last_run: lastRun,
    last_started_at: "2026-11-27T01:00:00+00:00",
    principal: "operator",
    requesting_account: "kim.dev",
    run_count: 2,
    status: "finished",
    ...extra,
  };
}

const FIRST = conversation("c-first");
const SECOND = conversation("c-second", { status: "paused", run_count: 1 });
const THIRD = conversation("c-third", { status: "failed" });

interface Query {
  readonly status: string | null;
  readonly after: string | null;
}

function page(conversations: ConversationRow[], nextCursor: string | null = null): Response {
  const body: ConversationPage = { conversations, next_cursor: nextCursor };
  return HttpResponse.json(body);
}

/** `GET /conversations` 에 답한다. 요청마다의 질의를 쌓아 돌려준다. */
function serve(reply: (query: Query, call: number) => Response | Promise<Response>): Query[] {
  const queries: Query[] = [];
  network.use(
    http.get(api("/conversations"), ({ request }) => {
      const params = new URL(request.url).searchParams;
      const query = { status: params.get("status"), after: params.get("after") };
      queries.push(query);
      return reply(query, queries.length - 1);
    }),
  );
  return queries;
}

function list(): HTMLElement {
  return screen.getByRole("region", { name: "대화" });
}

/** 넓은 갈래(표)의 본문 행. 머리 행은 뺀다. */
function tableRows(): HTMLElement[] {
  return within(within(list()).getByRole("table")).getAllByRole("row").slice(1);
}

/** 좁은 갈래(카드)의 항목. */
function cards(): HTMLElement[] {
  return within(list()).getAllByRole("listitem");
}

/** 두 갈래에서 줄 하나를 찾는다. 표의 행과 카드다. */
function placesOf(text: string): readonly [HTMLElement, HTMLElement] {
  const find = (places: readonly HTMLElement[]): HTMLElement => {
    const found = places.find((place) => within(place).queryByText(text) !== null);
    if (found === undefined) {
      throw new Error(`${text} 가 든 줄이 없다`);
    }
    return found;
  };
  return [find(tableRows()), find(cards())];
}

/** 줄의 링크가 가리키는 주소. 줄마다 첫 요청 링크 하나다. */
function hrefOf(place: HTMLElement): string | null {
  return within(place).getByRole("link").getAttribute("href");
}

async function showList(user: UserEvent = userEvent.setup()): Promise<UserEvent> {
  signedIn();
  renderPage(<ConversationsPage />);
  await within(await screen.findByRole("region", { name: "대화" })).findByRole("table");
  return user;
}

afterEach(() => {
  vi.useRealTimers();
});

describe("대화 목록", () => {
  test("머리의 제목은 대화이고 설명이 이 브라우저의 시간대 이름을 든다", async () => {
    serve(() => page([FIRST]));

    await showList();

    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("대화");
    expect(
      within(list()).getByText(
        "이어 가기로 이어진 실행들이다. 끝 실행이 최근인 대화가 위에 온다. 시각은 이 브라우저의 시간대(America/New_York)로 적었다.",
      ),
    ).toBeTruthy();
  });

  test("탐색에 대화 항목이 있고 지금 화면으로 표시된다", async () => {
    serve(() => page([FIRST]));

    await showList();

    const nav = screen.getByRole("navigation", { name: "관리 화면" });
    const item = within(nav).getByRole("link", { name: "대화" });
    expect(item.getAttribute("href")).toBe("/chat");
    expect(item.getAttribute("aria-current")).toBe("page");
  });

  test("줄이 서버가 준 순서 그대로 보이고 화면이 다시 정렬하지 않는다", async () => {
    serve(() => page([THIRD, FIRST, SECOND]));

    await showList();

    const fromTable = tableRows().map((row) => hrefOf(row));
    expect(fromTable).toEqual(["/chat/c-third", "/chat/c-first", "/chat/c-second"]);
    expect(cards().map((card) => hrefOf(card))).toEqual(fromTable);
  });

  test("처음에는 전부를 읽고 질의에 상태도 커서도 싣지 않는다", async () => {
    const queries = serve(() => page([FIRST]));

    await showList();

    expect(screen.getByRole<HTMLInputElement>("radio", { name: "전부" }).checked).toBe(true);
    expect(queries).toEqual([{ status: null, after: null }]);
  });

  test("표는 첫 요청·요청한 계정·에이전트·상태·실행·마지막 열이다", async () => {
    serve(() => page([conversation("c-1", { first_request: "환불해 줘", run_count: 3 })]));

    await showList();

    const headers = within(within(list()).getByRole("table")).getAllByRole("columnheader");
    expect(headers.map((header) => header.textContent)).toEqual([
      "첫 요청",
      "요청한 계정",
      "에이전트",
      "상태",
      "실행",
      "마지막",
    ]);
    expect(
      within(tableRows()[0] ?? document.body)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    ).toEqual(["환불해 줘", "kim.dev", "support-bot", "끝남", "3", "2026-11-26 20:05:30"]);
  });

  test("줄의 링크는 끝 실행의 대화 주소로 가고 식별자는 인코딩된다", async () => {
    serve(() => page([conversation("run/odd id")]));

    await showList();

    for (const place of [tableRows()[0], cards()[0]]) {
      expect(hrefOf(place ?? document.body)).toBe("/chat/run%2Fodd%20id");
    }
  });

  test("상태는 배지의 글자로 용어집의 말이다", async () => {
    serve(() => page([FIRST, SECOND, THIRD, conversation("c-4", { status: "unfinished" })]));

    await showList();

    for (const [runId, name] of [
      ["c-first", "끝남"],
      ["c-second", "일시정지"],
      ["c-third", "실패"],
      ["c-4", "결말 없음"],
    ] as const) {
      for (const place of placesOf(`${runId}의 첫 요청`)) {
        expect(within(place).getByText(name)).toBeTruthy();
      }
    }
  });

  test("앞부분을 읽지 못한 대화는 첫 요청 옆에 그 말이 서고 읽은 대화에는 없다", async () => {
    serve(() => page([conversation("c-cut", { complete: false }), FIRST]));

    await showList();

    for (const place of placesOf("c-cut의 첫 요청")) {
      expect(within(place).getByText("앞부분을 읽지 못함")).toBeTruthy();
    }
    for (const place of placesOf("c-first의 첫 요청")) {
      expect(within(place).queryByText("앞부분을 읽지 못함")).toBeNull();
    }
  });

  test("요청한 계정이 있으면 그 이름을 보이고 없으면 주체를 흐린 글자로 보인다", async () => {
    serve(() =>
      page([
        conversation("c-account", { requesting_account: "lee.ops", principal: "operator" }),
        conversation("c-os", { requesting_account: null, principal: "deploy-user" }),
      ]),
    );

    await showList();

    for (const place of placesOf("c-account의 첫 요청")) {
      const name = within(place).getByText("lee.ops");
      expect(name.className).not.toContain("text-text-muted");
    }
    for (const place of placesOf("c-os의 첫 요청")) {
      const principal = within(place).getByText("deploy-user");
      expect(principal.className).toContain("text-text-muted");
    }
  });

  test("요청한 계정이 빈 최종 사용자의 대화는 주체 앞에 최종 사용자를 붙이고 명령줄은 붙이지 않는다", async () => {
    serve(() =>
      page([
        conversation("c-end", {
          requesting_account: null,
          principal: "https://shop.example|user-17",
        }),
        conversation("c-cli", { requesting_account: null, principal: "hong" }),
      ]),
    );

    await showList();

    for (const place of placesOf("c-end의 첫 요청")) {
      expect(within(place).getByText("최종 사용자 https://shop.example|user-17")).toBeTruthy();
    }
    for (const place of placesOf("c-cli의 첫 요청")) {
      expect(within(place).getByText("hong")).toBeTruthy();
      expect(within(place).queryByText(/명령줄|최종 사용자/)).toBeNull();
    }
  });

  test("표지 줄은 이유를 보이고 누르면 그 실행의 대화 주소로 간다", async () => {
    serve(() => page([FIRST, { run_id: "r-broken", reason: "헤더를 읽을 수 없다: Invalid JSON" }]));

    await showList();

    const [row, card] = placesOf("r-broken");
    for (const place of [row, card]) {
      expect(
        within(place).getByText(/읽을 수 없는 트레이스: 헤더를 읽을 수 없다: Invalid JSON/),
      ).toBeTruthy();
      expect(within(place).getByRole("link", { name: "r-broken" }).getAttribute("href")).toBe(
        "/chat/r-broken",
      );
    }
  });

  test("상태로 거르면 질의에 그 상태가 실리고 그 상태의 줄만 보인다", async () => {
    const queries = serve(({ status }) => page(status === "paused" ? [SECOND] : [FIRST, SECOND]));
    const user = await showList();

    await user.click(screen.getByRole("radio", { name: "일시정지" }));

    await vi.waitFor(() => {
      expect(tableRows().map((row) => hrefOf(row))).toEqual(["/chat/c-second"]);
    });
    expect(queries).toEqual([
      { status: null, after: null },
      { status: "paused", after: null },
    ]);
  });

  test("다음 쪽이 있으면 더 보기가 앞 쪽의 커서를 싣고 줄을 뒤에 잇는다", async () => {
    const queries = serve(({ after }) =>
      after === null ? page([FIRST, SECOND], "cur-2") : page([THIRD]),
    );
    const user = await showList();

    await user.click(screen.getByRole("button", { name: "더 보기" }));

    await vi.waitFor(() => {
      expect(tableRows().map((row) => hrefOf(row))).toEqual([
        "/chat/c-first",
        "/chat/c-second",
        "/chat/c-third",
      ]);
    });
    expect(queries.filter(({ after }) => after !== null)).toEqual([
      { status: null, after: "cur-2" },
    ]);
    expect(screen.queryByRole("button", { name: "더 보기" })).toBeNull();
  });

  test("대화가 없으면 빈 줄 한 줄이고 거른 상태마다 그 상태의 말이다", async () => {
    serve(({ status }) => page(status === null ? [] : []));
    const user = userEvent.setup();
    signedIn();
    renderPage(<ConversationsPage />);

    expect(await screen.findByText("대화가 없다")).toBeTruthy();
    await user.click(screen.getByRole("radio", { name: "실패" }));
    expect(await screen.findByText("실패한 대화가 없다")).toBeTruthy();
  });

  test("저절로 다시 읽지 않는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const queries = serve(() => page([FIRST]));
    await showList(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }));

    await vi.advanceTimersByTimeAsync(10 * 60_000);

    expect(queries).toHaveLength(1);
  });
});

describe("읽기 골격", () => {
  test("읽는 동안 대화를 불러오는 중이 보이고 오면 사라진다", async () => {
    const first = Promise.withResolvers<Response>();
    serve(() => first.promise);
    signedIn();
    renderPage(<ConversationsPage />);

    expect(
      await screen.findByRole("progressbar", { name: "대화 목록을 불러오는 중" }),
    ).toBeTruthy();
    first.resolve(page([FIRST]));
    await within(await screen.findByRole("region", { name: "대화" })).findByRole("table");
    expect(screen.queryByRole("progressbar", { name: "대화 목록을 불러오는 중" })).toBeNull();
  });

  test("읽다 실패하면 실패 알림과 추적 식별자를 보이고 거르기는 남는다", async () => {
    serve(() =>
      HttpResponse.json(envelope("internal_error", "대화를 묶지 못했다", "req-9"), { status: 500 }),
    );
    signedIn();
    renderPage(<ConversationsPage />);

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("대화 목록을 읽지 못했다")).toBeTruthy();
    expect(within(alert).getByText("대화를 묶지 못했다")).toBeTruthy();
    expect(within(alert).getByText("req-9")).toBeTruthy();
    expect(screen.getByRole("radio", { name: "전부" })).toBeTruthy();
  });

  test("다시 읽다 실패하면 보인 줄을 지우고 실패만 보인다", async () => {
    serve((_query, call) =>
      call === 0
        ? page([FIRST])
        : HttpResponse.json(envelope("internal_error", "다시 읽지 못했다"), { status: 500 }),
    );
    const user = await showList();

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect(await screen.findByText("다시 읽지 못했다")).toBeTruthy();
    expect(screen.queryByText("c-first의 첫 요청")).toBeNull();
  });
});
