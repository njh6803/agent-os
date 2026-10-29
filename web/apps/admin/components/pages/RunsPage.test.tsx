// 실행 목록. 운영자가 실행을 최근 것부터 보고, 상태로 거르고, 한 쪽을 넘으면 이어서 더 본다(web-admin 티켓 07). 본문
// 칸이 넓으면 표, 좁으면 카드이고 시각은 이 브라우저의 시간대로 적는다(admin-style 티켓 06).
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 질의(`status`, `after`)는 경계를 지나는 요청에서 본다.
//
// jsdom 은 Tailwind 의 CSS 를 싣지 않아 컨테이너 질의를 풀지 않는다. 그래서 표와 카드가 함께 보인다. 시험은 갈래마다
// 찾는다(표는 `table` 안의 행, 카드는 목록의 항목). 행의 글자를 보는 단언은 두 갈래에 함께 걸고, 행의 차례는 두 갈래가
// 같은지 본다. 어느 갈래가 어느 폭에서 서는지는 스토리가 본다(티켓 06 "이 티켓이 정한 것").
//
// 시간대는 `pages` 프로젝트가 America/New_York 으로 고정한다(web/vitest.config.ts). 이 PC 의 시간대(Asia/Seoul)로는 머리
// 설명에 그 이름이 나오지 않아, 머리의 단언이 고정이 들었다는 단언을 겸한다.

import { act, fireEvent, screen, within } from "@testing-library/react";
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
import { acceptTokens, clearTokens, enterAdminToken } from "../../testing/token";
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

/** 표의 열 머리. 차례가 열의 차례다. */
const COLUMNS = ["상태", "실행", "에이전트", "주체", "시작", "마지막"];

function runList(): HTMLElement {
  return screen.getByRole("region", { name: "실행" });
}

/** 넓은 갈래(표)의 본문 행. 머리 행은 뺀다. */
function tableRows(): HTMLElement[] {
  return within(within(runList()).getByRole("table")).getAllByRole("row").slice(1);
}

/** 좁은 갈래(카드)의 항목. */
function cards(): HTMLElement[] {
  return within(runList()).getAllByRole("listitem");
}

function linkText(place: HTMLElement): string | null {
  return within(place).getByRole("link").textContent;
}

/** 보이는 실행 식별자의 차례. 행마다 하나뿐인 링크의 글자다. 두 갈래가 같은 차례로 같은 실행을 보이는지 함께 본다. */
function shownRunIds(): (string | null)[] {
  const fromTable = tableRows().map(linkText);
  expect(cards().map(linkText), "카드가 표와 다른 실행을 보인다").toEqual(fromTable);
  return fromTable;
}

function placeOf(places: readonly HTMLElement[], runId: string, what: string): HTMLElement {
  const found = places.find((place) => within(place).queryByRole("link", { name: runId }) !== null);
  if (found === undefined) {
    throw new Error(`${runId} 의 ${what}이 없다`);
  }
  return found;
}

/** 실행 하나를 보이는 두 자리. 표의 행과 카드다. */
function placesOf(runId: string): readonly [HTMLElement, HTMLElement] {
  return [placeOf(tableRows(), runId, "표의 행"), placeOf(cards(), runId, "카드")];
}

/** 그 실행을 보이는 두 자리가 모두 그 글자를 보이는가. */
function showsInBoth(runId: string, text: string): boolean {
  return placesOf(runId).every((place) => within(place).queryByText(text) !== null);
}

/**
 * 처음 불러오는 동안 넓은 갈래에 서는 뼈대. 화면 읽기 프로그램에서 숨어 있어 숨은 것까지 찾는다. 다 읽은 표는 숨지
 * 않아 섞이지 않는다.
 */
function skeleton(): HTMLElement | undefined {
  return within(runList())
    .queryAllByRole("table", { hidden: true })
    .find((table) => table.closest("[aria-hidden='true']") !== null);
}

/** 실행 목록을 열고 관리 토큰을 넣어 행이 설 때까지 기다린다. 이어서 누를 사용자를 돌려준다. */
async function showRuns(user: UserEvent = userEvent.setup()): Promise<UserEvent> {
  acceptTokens();
  renderPage(<RunsPage />);
  await enterAdminToken(user, TOKEN);
  await within(await screen.findByRole("region", { name: "실행" })).findByRole("table");
  return user;
}

afterEach(() => {
  vi.useRealTimers();
});

describe("실행 목록", () => {
  test("머리의 제목은 개수 없이 실행이고 설명이 이 브라우저의 시간대 이름을 든다", async () => {
    serveRuns(() => page([PAUSED, FINISHED]));

    await showRuns();

    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("실행");
    expect(
      within(runList()).getByText(
        "트레이스로 남은 실행이다. 새로 시작한 것이 위에 온다. 시각은 이 브라우저의 시간대(America/New_York)로 적었다.",
      ),
    ).toBeTruthy();
  });

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

  test("상태는 배지의 글자로 용어집의 말이고 실행 중은 어디에도 없다", async () => {
    serveRuns(() => page([PAUSED, FINISHED, FAILED, UNFINISHED]));

    await showRuns();

    for (const [runId, name] of [
      ["r-paused", "일시정지"],
      ["r-finished", "끝남"],
      ["r-failed", "실패"],
      ["r-unfinished", "결말 없음"],
    ] as const) {
      for (const place of placesOf(runId)) {
        expect(within(place).getByText(name)).toBeTruthy();
      }
    }
    expect(document.body.textContent).not.toContain("실행 중");
    const filters = screen
      .getAllByRole("radio")
      .map((radio) => radio.closest("label")?.textContent);
    expect(filters).toEqual(["전부", "일시정지", "끝남", "실패", "결말 없음"]);
  });

  test("표는 상태·실행·에이전트·주체·시작·마지막 열이고 카드는 첫 줄이 상태와 시작, 그 아래가 실행·에이전트·주체·마지막이다", async () => {
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

    const headers = within(within(runList()).getByRole("table")).getAllByRole("columnheader");
    expect(headers.map((header) => header.textContent)).toEqual(COLUMNS);
    expect(headers.map((header) => header.getAttribute("scope"))).toEqual(COLUMNS.map(() => "col"));
    const [tableRow, card] = placesOf("r-finished");
    expect(
      within(tableRow)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    ).toEqual([
      "끝남",
      "r-finished",
      "echo",
      "ops-kim",
      "2026-09-30 05:00:00",
      "2026-09-30 05:05:30",
    ]);
    expect(card.textContent).toBe(
      "끝남2026-09-30 05:00:00r-finished에이전트echo주체ops-kim마지막2026-09-30 05:05:30",
    );
  });

  test("시작과 마지막은 이 브라우저의 시간대로 바꾼 24시간 시각이고 초 아래는 버린다", async () => {
    serveRuns(() =>
      page([
        {
          ...FINISHED,
          started_at: "2026-09-30T09:00:00+00:00",
          last_at: "2026-10-01T03:04:05+00:00",
        },
        {
          ...FAILED,
          started_at: "2026-10-01T04:00:30+00:00",
          last_at: "2026-10-01T16:59:59.987654Z",
        },
      ]),
    );

    await showRuns();

    // America/New_York 은 이때 서머타임(UTC-4)이다. 날짜가 앞으로 넘어가고, 자정은 24 가 아니라 00 이며, 오후는
    // 12시간제가 아니다. 서버가 싣는 마이크로초와 `Z` 도 읽고, 올리지 않고 버린다.
    for (const [runId, times] of [
      ["r-finished", ["2026-09-30 05:00:00", "2026-09-30 23:04:05"]],
      ["r-failed", ["2026-10-01 00:00:30", "2026-10-01 12:59:59"]],
    ] as const) {
      for (const place of placesOf(runId)) {
        for (const time of times) {
          expect(within(place).getByText(time)).toBeTruthy();
        }
      }
    }
  });

  test("읽을 수 없는 트레이스의 행은 실행 칸에 링크를 두고 나머지 칸을 합쳐 이유를 보인다", async () => {
    serveRuns(() => page([FINISHED, UNREADABLE]));

    await showRuns();

    const reason = "읽을 수 없는 트레이스: 헤더를 읽을 수 없다: Invalid JSON";
    const [tableRow, card] = placesOf("r-broken");
    const cells = within(tableRow).getAllByRole("cell");
    // 상태 칸에는 꾸밈 아이콘 하나뿐이다. 에이전트부터 마지막까지 넷을 한 칸으로 합친다.
    expect(cells.map((cell) => cell.textContent)).toEqual(["", "r-broken", reason]);
    expect(cells.at(-1)?.getAttribute("colspan")).toBe("4");
    // 카드는 첫 줄이 이유이고 그 아래가 링크다.
    expect(card.textContent).toBe(`${reason}r-broken`);
  });

  test("행마다 그 실행을 여는 링크가 있고 읽을 수 없는 트레이스의 행도 그렇다", async () => {
    serveRuns(() => page([PAUSED, UNREADABLE]));

    await showRuns();

    for (const runId of ["r-paused", "r-broken"]) {
      for (const place of placesOf(runId)) {
        expect(within(place).getByRole("link").getAttribute("href")).toBe(`/runs/${runId}`);
      }
    }
  });

  test("실행이 없으면 없다고 말한다", async () => {
    serveRuns(() => page([]));
    acceptTokens();
    renderPage(<RunsPage />);

    await enterAdminToken(userEvent.setup(), TOKEN);

    expect(await within(runList()).findByText("실행이 없다")).toBeTruthy();
    expect(within(runList()).queryByRole("table")).toBeNull();
    expect(within(runList()).queryByRole("listitem")).toBeNull();
  });

  test("거른 상태에 실행이 없으면 그 상태의 한 줄이 서고 전부 보기는 없으며 거르기는 남는다", async () => {
    serveRuns(({ status }) => page(status === null ? [FINISHED] : []));
    const user = await showRuns();

    for (const [name, line] of [
      ["일시정지", "일시정지한 실행이 없다"],
      ["끝남", "끝난 실행이 없다"],
      ["실패", "실패한 실행이 없다"],
      ["결말 없음", "결말 없는 실행이 없다"],
    ] as const) {
      await user.click(screen.getByRole("radio", { name }));

      expect(await within(runList()).findByText(line)).toBeTruthy();
      expect(within(runList()).queryByRole("table")).toBeNull();
      expect(screen.queryByRole("button", { name: "전부 보기" })).toBeNull();
      expect(screen.getByRole<HTMLInputElement>("radio", { name }).checked).toBe(true);
    }
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
    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-finished", "r-paused"]);
    });
    expect(showsInBoth("r-paused", "일시정지")).toBe(true);
    const before = queries.length;
    decided = true;

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    await vi.waitFor(() => {
      expect(showsInBoth("r-paused", "끝남")).toBe(true);
    });
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

    expect(
      await screen.findByRole("progressbar", { name: "실행 목록을 불러오는 중" }),
    ).toBeTruthy();
    first.resolve(page([FINISHED]));
    await within(await screen.findByRole("region", { name: "실행" })).findByRole("table");
    expect(screen.queryByRole("progressbar")).toBeNull();

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect(await screen.findByRole("progressbar", { name: "다시 확인하는 중" })).toBeTruthy();
    expect(shownRunIds()).toEqual(["r-finished"]);
    // 다시 확인하는 중에는 보인 행이 남아 뼈대가 서지 않는다.
    expect(skeleton()).toBeUndefined();
    again.resolve(page([FINISHED]));
    await vi.waitFor(() => {
      expect(screen.queryByRole("progressbar")).toBeNull();
    });
  });

  test("처음 불러오는 동안 표의 뼈대 행 넷은 0.3초가 지나야 서고 표 머리를 둔다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const first = Promise.withResolvers<Response>();
    serveRuns(() => first.promise);
    acceptTokens();
    renderPage(<RunsPage />);
    await enterAdminToken(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }), TOKEN);
    await screen.findByRole("heading", { level: 1, name: "실행" });

    // 진행 표시의 같은 시험(HomePage.test.tsx 의 "0.3초가 지나야 선다")과 같은 꼴이다. 앞의 단언은 0.1초만 밀어,
    // 지연이 없으면 빨개지고 머리가 선 뒤 흐른 실제 시간이 0.2초를 넘지 않는 한 초록이다.
    await act(() => vi.advanceTimersByTimeAsync(100));
    expect(skeleton()).toBeUndefined();
    await act(() => vi.advanceTimersByTimeAsync(200));
    const bones = skeleton();
    if (bones === undefined) {
      throw new Error("0.3초가 지나도 뼈대가 서지 않았다");
    }
    const headers = within(bones).getAllByRole("columnheader", { hidden: true });
    expect(headers.map((header) => header.textContent)).toEqual(COLUMNS);
    const rows = within(bones).getAllByRole("row", { hidden: true }).slice(1);
    expect(rows).toHaveLength(4);
    // 뼈대 행은 막대뿐이라 글자가 없다.
    expect(rows.map((bone) => bone.textContent)).toEqual(["", "", "", ""]);

    first.resolve(page([FINISHED]));

    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-finished"]);
    });
    expect(skeleton()).toBeUndefined();
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
    expect(alert.textContent).toContain("실행 목록을 읽지 못했다");
    expect(alert.textContent).toContain("트레이스 디렉터리를 읽지 못했다");
    expect(alert.textContent).toContain("추적 식별자: req-7e1d");
    expect(within(runList()).queryByRole("table")).toBeNull();
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
    await vi.waitFor(() => {
      expect(shownRunIds()).toEqual(["r-finished", "r-paused"]);
    });
    const before = queries.length;
    decided = true;

    await vi.advanceTimersByTimeAsync(10_000);
    fireEvent.focus(window);

    await vi.waitFor(() => {
      expect(showsInBoth("r-paused", "끝남")).toBe(true);
    });
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
    await clearTokens(user);
    await enterAdminToken(user, TOKEN);

    // 새 토큰은 옛 요청을 나눠 받지 않고 제 요청을 보낸다.
    await within(await screen.findByRole("region", { name: "실행" })).findByRole("table");
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
