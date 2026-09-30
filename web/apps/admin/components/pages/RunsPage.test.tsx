// 실행 목록. 운영자가 실행을 최근 것부터 보고, 상태로 거르고, 한 쪽을 넘으면 이어서 더 본다(web-admin 티켓 07).
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 질의(`status`, `after`)는 경계를 지나는 요청에서 본다.

import { fireEvent, screen, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, test, vi } from "vitest";
import {
  api,
  envelope,
  network,
  type RunRow,
  type RunSummary,
  type TracePage,
} from "../../testing/network";
import { renderPage } from "../../testing/render";
import { acceptTokens, enterAdminToken } from "../../testing/token";
import { RunsPage } from "./RunsPage";

const TOKEN = "adm-2Wc8-runs-page-token";

function summary(
  runId: string,
  status: RunSummary["status"],
  startedAt = "2026-09-30T09:00:00+00:00",
): RunSummary {
  return {
    run_id: runId,
    status,
    schema_version: "2",
    started_at: startedAt,
    last_at: startedAt,
    agent: "calc",
    principal: "operator",
  };
}

const PAUSED = summary("r-paused", "paused");
const FINISHED = summary("r-finished", "finished");
const FAILED = summary("r-failed", "failed");
const UNFINISHED = summary("r-unfinished", "unfinished");
const UNREADABLE: RunRow = {
  run_id: "r-broken",
  reason: "헤더를 읽을 수 없다: Invalid JSON",
};

function page(runs: RunRow[], nextCursor: string | null = null): Response {
  const body: TracePage = { runs, next_cursor: nextCursor };
  return HttpResponse.json(body);
}

interface Query {
  readonly status: string | null;
  readonly after: string | null;
}

/**
 * `GET /traces` 에 답한다. `reply` 는 그 요청의 질의와 몇 번째 요청인지(0부터) 받는다. 요청마다의 질의를 쌓아
 * 돌려준다. 화면이 몇 번 읽었는지와 무엇을 실었는지가 여기서 보인다.
 */
function serveRuns(reply: (query: Query, call: number) => Response | Promise<Response>): Query[] {
  const queries: Query[] = [];
  network.use(
    http.get(api("/traces"), ({ request }) => {
      const params = new URL(request.url).searchParams;
      const query = { status: params.get("status"), after: params.get("after") };
      queries.push(query);
      return reply(query, queries.length - 1);
    }),
  );
  return queries;
}

function runList(): HTMLElement {
  return screen.getByRole("region", { name: "실행" });
}

/** 목록의 행 전부. 행마다 첫 링크의 글자가 실행 식별자다. */
function shownRunIds(): (string | null)[] {
  return within(runList())
    .getAllByRole("listitem")
    .map((item) => within(item).getByRole("link").textContent);
}

function row(runId: string): HTMLElement {
  const found = within(runList())
    .getAllByRole("listitem")
    .find((item) => within(item).queryByRole("link", { name: runId }) !== null);
  if (found === undefined) {
    throw new Error(`${runId} 행이 없다`);
  }
  return found;
}

/** 실행 목록을 열고 관리 토큰을 넣어 행이 설 때까지 기다린다. 이어서 누를 사용자를 돌려준다. */
async function showRuns(user: UserEvent = userEvent.setup()): Promise<UserEvent> {
  acceptTokens();
  renderPage(<RunsPage />);
  await enterAdminToken(user, TOKEN);
  await within(await screen.findByRole("region", { name: "실행" })).findAllByRole("listitem");
  return user;
}

afterEach(() => {
  vi.useRealTimers();
});

describe("실행 목록", () => {
  test("행이 서버가 준 순서 그대로 보이고 화면이 다시 정렬하지 않는다", async () => {
    // 시작 시각으로도 이름으로도 정렬되지 않은 차례다.
    const runs = [
      summary("r-b", "finished", "2026-09-30T10:00:00+00:00"),
      summary("r-c", "failed", "2026-09-30T08:00:00+00:00"),
      summary("r-a", "finished", "2026-09-30T11:00:00+00:00"),
    ];
    serveRuns(() => page(runs));

    await showRuns();

    expect(shownRunIds()).toEqual(["r-b", "r-c", "r-a"]);
  });

  test("처음에는 전부를 읽고 질의에 상태도 커서도 싣지 않는다", async () => {
    const queries = serveRuns(() => page([FINISHED]));

    await showRuns();

    expect(screen.getByRole<HTMLInputElement>("radio", { name: "전부" }).checked).toBe(true);
    expect(queries).toEqual([{ status: null, after: null }]);
  });

  test("상태로 거르면 질의에 그 상태가 실리고 그 상태의 행만 보인다", async () => {
    const queries = serveRuns(({ status }) =>
      page(status === "paused" ? [PAUSED] : [PAUSED, FINISHED]),
    );
    const user = await showRuns();

    await user.click(screen.getByRole("radio", { name: "일시정지" }));

    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-paused"]);
    });
    expect(queries).toEqual([
      { status: null, after: null },
      { status: "paused", after: null },
    ]);
  });

  test("상태 넷의 거르기가 저마다의 상태를 싣는다", async () => {
    const queries = serveRuns(() => page([FINISHED]));
    const user = await showRuns();

    for (const name of ["끝남", "실패", "결말 없음", "일시정지"]) {
      await user.click(screen.getByRole("radio", { name }));
    }

    await vi.waitFor(() => {
      expect(queries.map(({ status }) => status)).toEqual([
        null,
        "finished",
        "failed",
        "unfinished",
        "paused",
      ]);
    });
  });

  test("다음 쪽이 있으면 더 보기가 앞 쪽의 커서를 싣고 행을 뒤에 잇는다", async () => {
    const queries = serveRuns(({ after }) =>
      after === null ? page([PAUSED, FINISHED], "cur-2") : page([FAILED]),
    );
    const user = await showRuns();

    await user.click(screen.getByRole("button", { name: "더 보기" }));

    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-paused", "r-finished", "r-failed"]);
    });
    // 더 볼 때 본 쪽도 모두 다시 읽는다(revalidateAll). 커서를 실은 요청은 하나다.
    expect(queries.filter(({ after }) => after !== null)).toEqual([
      { status: null, after: "cur-2" },
    ]);
    // 마지막 쪽이면 더 볼 것이 없다.
    expect(screen.queryByRole("button", { name: "더 보기" })).toBeNull();
  });

  test("거른 채로 더 보면 상태와 커서가 함께 실린다", async () => {
    const queries = serveRuns(({ status, after }) =>
      status === null
        ? page([FINISHED])
        : after === null
          ? page([PAUSED], "cur-paused")
          : page([summary("r-paused-2", "paused")]),
    );
    const user = await showRuns();
    await user.click(screen.getByRole("radio", { name: "일시정지" }));
    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-paused"]);
    });

    await user.click(screen.getByRole("button", { name: "더 보기" }));

    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-paused", "r-paused-2"]);
    });
    expect(queries.at(-1)).toEqual({ status: "paused", after: "cur-paused" });
  });

  test("다음 쪽이 없으면 더 보기가 없다", async () => {
    serveRuns(() => page([FINISHED]));

    await showRuns();

    expect(screen.queryByRole("button", { name: "더 보기" })).toBeNull();
  });

  test("상태의 이름은 용어집의 말이고 실행 중은 어디에도 없다", async () => {
    serveRuns(() => page([PAUSED, FINISHED, FAILED, UNFINISHED]));

    await showRuns();

    expect(within(row("r-paused")).getByText("일시정지")).toBeTruthy();
    expect(within(row("r-finished")).getByText("끝남")).toBeTruthy();
    expect(within(row("r-failed")).getByText("실패")).toBeTruthy();
    expect(within(row("r-unfinished")).getByText("결말 없음")).toBeTruthy();
    expect(document.body.textContent).not.toContain("실행 중");
    const filters = screen
      .getAllByRole("radio")
      .map((radio) => radio.closest("label")?.textContent);
    expect(filters).toEqual(["전부", "일시정지", "끝남", "실패", "결말 없음"]);
  });

  test("멈춘 실행은 상태가 두드러져 목록에서 바로 알아본다", async () => {
    serveRuns(() => page([FINISHED, PAUSED, FAILED, UNFINISHED]));

    await showRuns();

    expect(within(row("r-paused")).getByText("일시정지").tagName).toBe("STRONG");
    for (const [runId, name] of [
      ["r-finished", "끝남"],
      ["r-failed", "실패"],
      ["r-unfinished", "결말 없음"],
    ] as const) {
      expect(within(row(runId)).getByText(name).tagName).not.toBe("STRONG");
    }
  });

  test("요약 행은 에이전트와 주체와 시각을 보인다", async () => {
    serveRuns(() =>
      page([
        {
          ...FINISHED,
          agent: "echo",
          principal: "ops-kim",
          started_at: "2026-09-30T09:00:00+00:00",
          last_at: "2026-09-30T09:05:30+00:00",
        },
      ]),
    );

    await showRuns();

    const text = row("r-finished").textContent;
    expect(text).toContain("echo");
    expect(text).toContain("ops-kim");
    expect(text).toContain("2026-09-30T09:00:00+00:00");
    expect(text).toContain("2026-09-30T09:05:30+00:00");
  });

  test("읽을 수 없는 트레이스의 행은 실행 식별자와 이유를 보인다", async () => {
    serveRuns(() => page([FINISHED, UNREADABLE]));

    await showRuns();

    const broken = row("r-broken");
    expect(broken.textContent).toContain("읽을 수 없는 트레이스");
    expect(broken.textContent).toContain("헤더를 읽을 수 없다: Invalid JSON");
  });

  test("행마다 그 실행을 여는 링크가 있고 읽을 수 없는 트레이스의 행도 그렇다", async () => {
    serveRuns(() => page([PAUSED, UNREADABLE]));

    await showRuns();

    expect(within(row("r-paused")).getByRole("link").getAttribute("href")).toBe("/runs/r-paused");
    expect(within(row("r-broken")).getByRole("link").getAttribute("href")).toBe("/runs/r-broken");
  });

  test("실행이 없으면 없다고 말한다", async () => {
    serveRuns(() => page([]));
    acceptTokens();
    renderPage(<RunsPage />);

    await enterAdminToken(userEvent.setup(), TOKEN);

    expect(await screen.findByText("실행이 없다")).toBeTruthy();
  });

  test("머리에 플러그인 목록과 실행 목록으로 가는 링크가 있다", async () => {
    serveRuns(() => page([FINISHED]));

    await showRuns();

    const nav = screen.getByRole("navigation");
    expect(within(nav).getByRole("link", { name: "플러그인 목록" }).getAttribute("href")).toBe("/");
    expect(within(nav).getByRole("link", { name: "실행 목록" }).getAttribute("href")).toBe("/runs");
  });
});

describe("실행 목록의 새로 고침과 에러", () => {
  test("새로 고침 버튼이 목록을 다시 읽는다", async () => {
    const queries = serveRuns((_, call) => page(call === 0 ? [FINISHED] : [PAUSED, FINISHED]));
    const user = await showRuns();

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-paused", "r-finished"]);
    });
    expect(queries).toHaveLength(2);
  });

  test("더 본 뒤의 새로 고침은 커서가 그대로여도 본 쪽을 모두 다시 읽는다", async () => {
    // 둘째 쪽의 멈춘 실행이 그 사이 끝났다. 새로 고침이 첫 쪽만 읽으면 옛 일시정지가 남는다.
    let decided = false;
    const queries = serveRuns(({ after }) =>
      after === null
        ? page([FINISHED], "cur-2")
        : page([decided ? summary("r-paused", "finished") : PAUSED]),
    );
    const user = await showRuns();
    await user.click(screen.getByRole("button", { name: "더 보기" }));
    await within(runList()).findByRole("link", { name: "r-paused" });
    expect(within(row("r-paused")).getByText("일시정지")).toBeTruthy();
    const before = queries.length;
    decided = true;

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect(await within(row("r-paused")).findByText("끝남")).toBeTruthy();
    expect(queries.slice(before)).toEqual([
      { status: null, after: null },
      { status: null, after: "cur-2" },
    ]);
  });

  test("다음 쪽을 읽는 동안에는 더 보기가 막혀 있다", async () => {
    const second = Promise.withResolvers<Response>();
    serveRuns(({ after }) => (after === null ? page([FINISHED], "cur-2") : second.promise));
    const user = await showRuns();

    await user.click(screen.getByRole("button", { name: "더 보기" }));

    await vi.waitFor(() => {
      expect(screen.getByRole<HTMLButtonElement>("button", { name: "더 보기" }).disabled).toBe(
        true,
      );
    });
    second.resolve(page([FAILED]));
    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-finished", "r-failed"]);
    });
  });

  test("더 본 뒤의 새로 고침은 본 쪽을 모두 다시 읽고 다음 쪽은 새로 읽은 커서로 잇는다", async () => {
    // 새로 고치기 전에 새 실행이 생겨 첫 쪽의 커서가 바뀐다. 옛 커서로 둘째 쪽을 읽으면 행이 겹친다.
    let created = false;
    const queries = serveRuns(({ after }) =>
      after === null
        ? created
          ? page([UNFINISHED, PAUSED], "cur-new")
          : page([PAUSED, FINISHED], "cur-old")
        : after === "cur-new"
          ? page([FINISHED, FAILED])
          : page(created ? [summary("r-stale", "finished")] : [FAILED]),
    );
    const user = await showRuns();
    await user.click(screen.getByRole("button", { name: "더 보기" }));
    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-paused", "r-finished", "r-failed"]);
    });
    const before = queries.length;
    created = true;

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-unfinished", "r-paused", "r-finished", "r-failed"]);
    });
    expect(queries.slice(before)).toEqual([
      { status: null, after: null },
      { status: null, after: "cur-new" },
    ]);
  });

  test("처음 불러오는 중에는 자리표시가 보이고 다시 확인하는 동안에는 이미 보인 행이 남는다", async () => {
    const first = Promise.withResolvers<Response>();
    const again = Promise.withResolvers<Response>();
    serveRuns((_, call) => (call === 0 ? first.promise : again.promise));
    acceptTokens();
    renderPage(<RunsPage />);
    const user = userEvent.setup();
    await enterAdminToken(user, TOKEN);

    expect((await screen.findByRole("status")).textContent).toContain("불러오는 중");
    first.resolve(page([FINISHED]));
    await within(await screen.findByRole("region", { name: "실행" })).findAllByRole("listitem");
    expect(screen.queryByRole("status")).toBeNull();

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("status")).textContent).toContain("다시 확인하는 중");
    expect(shownRunIds()).toEqual(["r-finished"]);
    again.resolve(page([FINISHED]));
    await vi.waitFor(() => {
      expect(screen.queryByRole("status")).toBeNull();
    });
  });

  test("이미 보인 목록도 다시 읽다 실패하면 옛 행을 지우고 봉투의 메시지와 추적 식별자를 보인다", async () => {
    serveRuns((_, call) =>
      call === 0
        ? page([FINISHED])
        : HttpResponse.json(
            envelope("internal_error", "트레이스 디렉터리를 읽지 못했다", "req-7e1d"),
            {
              status: 500,
            },
          ),
    );
    const user = await showRuns();

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("트레이스 디렉터리를 읽지 못했다");
    expect(alert.textContent).toContain("req-7e1d");
    expect(within(runList()).queryAllByRole("listitem")).toEqual([]);
    // 거르기는 실패 중에도 남아 다른 상태로 옮겨 갈 수 있다.
    expect(screen.getByRole("radio", { name: "일시정지" })).toBeTruthy();
  });

  test("목록을 읽다 401 을 받으면 관리 토큰을 지우고 입력 화면으로 돌아가 거부됐다고 말한다", async () => {
    serveRuns(() =>
      HttpResponse.json(envelope("unauthorized", "토큰이 없거나 틀리다"), { status: 401 }),
    );
    acceptTokens();
    renderPage(<RunsPage />);

    await enterAdminToken(userEvent.setup(), TOKEN);

    expect((await screen.findByRole("alert")).textContent).toContain("관리 토큰이 거부됐다");
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
    expect(screen.queryByRole("region", { name: "실행" })).toBeNull();
  });

  test("네트워크 실패는 서버에 닿지 못했다로 보인다", async () => {
    serveRuns(() => Response.error());
    acceptTokens();
    renderPage(<RunsPage />);

    await enterAdminToken(userEvent.setup(), TOKEN);

    expect((await screen.findByRole("alert")).textContent).toContain("서버에 닿지 못했다");
  });

  test("창에 포커스가 돌아오면 목록을 다시 읽는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const queries = serveRuns((_, call) => page(call === 0 ? [FINISHED] : [PAUSED, FINISHED]));
    await showRuns(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }));

    // SWR 은 마운트한 뒤 한동안(focusThrottleInterval) 포커스를 흘려보낸다. 그 너머로 민다.
    await vi.advanceTimersByTimeAsync(10_000);
    fireEvent.focus(window);

    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-paused", "r-finished"]);
    });
    expect(queries).toHaveLength(2);
  });

  test("더 본 뒤 창에 포커스가 돌아오면 본 쪽을 모두 다시 읽는다", async () => {
    // 떠나 있던 사이 둘째 쪽의 멈춘 실행이 끝났다(스토리 33). 포커스가 첫 쪽만 읽으면 옛 일시정지가 남는다.
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let decided = false;
    const queries = serveRuns(({ after }) =>
      after === null
        ? page([FINISHED], "cur-2")
        : page([decided ? summary("r-paused", "finished") : PAUSED]),
    );
    const user = await showRuns(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }));
    await user.click(screen.getByRole("button", { name: "더 보기" }));
    await within(runList()).findByRole("link", { name: "r-paused" });
    const before = queries.length;
    decided = true;

    await vi.advanceTimersByTimeAsync(10_000);
    fireEvent.focus(window);

    expect(await within(row("r-paused")).findByText("끝남")).toBeTruthy();
    expect(queries.slice(before)).toEqual([
      { status: null, after: null },
      { status: null, after: "cur-2" },
    ]);
  });

  test("시간이 흘러도 스스로 다시 읽지 않는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const queries = serveRuns(() => page([FINISHED]));
    await showRuns(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }));

    await vi.advanceTimersByTimeAsync(60 * 60 * 1000);

    expect(queries).toHaveLength(1);
  });

  test("지운 토큰의 늦은 401 은 그 사이 넣은 새 토큰의 목록에 섞이지 않고 새 토큰을 내려놓지 않는다", async () => {
    const old = "adm-old-token-cleared";
    const late = Promise.withResolvers<Response>();
    const authorizations: string[] = [];
    network.use(
      http.get(api("/traces"), ({ request }) => {
        authorizations.push(request.headers.get("Authorization") ?? "(없음)");
        return authorizations.length === 1 ? late.promise : page([FINISHED]);
      }),
    );
    acceptTokens();
    renderPage(<RunsPage />);
    const user = userEvent.setup();
    // 옛 토큰의 요청(0)은 응답을 기다린다.
    await enterAdminToken(user, old);
    await user.click(await screen.findByRole("button", { name: "토큰 지우기" }));
    await enterAdminToken(user, TOKEN);

    // 새 토큰은 옛 요청을 나눠 받지 않고 제 요청을 보낸다.
    await within(await screen.findByRole("region", { name: "실행" })).findAllByRole("listitem");
    expect(authorizations).toEqual([`Bearer ${old}`, `Bearer ${TOKEN}`]);
    late.resolve(
      HttpResponse.json(envelope("unauthorized", "토큰이 없거나 틀리다"), { status: 401 }),
    );
    // 늦은 응답이 처리될 틈을 준다. 옛 요청의 401 이 새 토큰을 내려놓으면 넣는 자리로 돌아간다.
    await new Promise((resolve) => setTimeout(resolve, 200));

    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
