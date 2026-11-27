// 대화 화면(admin-login 티켓 10). 끝 실행의 트레이스를 읽고 앞 실행을 거슬러 읽어 첫 실행부터 한 번에 그린다. 끝 실행이 결말
// 없이 도는 동안은 그 실행 하나만 3초마다 다시 읽고, 결말이 오거나 멈출 때가 지나면 멈춘다. 실행마다의 "자세히"가 오른쪽에
// 실행 패널을 연다. 보내기와 이어 가기와 승인과 옛 주소의 이동은 `ConversationPage.write.test.tsx` 가 본다.
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 시간은 가짜 시계가 흘린다. 시간대는 `pages` 프로젝트가
// America/New_York 으로 고정한다(web/vitest.config.ts). 로그인은 쿠키라 테스트에서 보이지 않고, 화면은 `GET /auth/me` 에
// 계정이 답해야 그려진다(`signedIn`). 멈출 때를 정하는 실행 제한 시간은 그 답의 `run_timeout_seconds` 다.

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, test, vi } from "vitest";
import {
  denied,
  failed,
  finished,
  granted,
  llm,
  paused,
  resumed,
  started,
  summarized,
  T0,
  toolCalled,
  trace,
} from "../../testing/events";
import { api, envelope, network, type Trace } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { signedIn } from "../../testing/session";
import { ConversationPage } from "./ConversationPage";

/** 실행 백 개를 차례로 읽는 시험이 기다리는 시간(밀리초). 시험 하나의 제한도 이 값에 맞춘다. */
const LONG_CHAIN_MS = 20_000;

type Reply = Trace | Response | ((call: number) => Trace | Response | Promise<Response>);

/** 실행마다의 응답. 읽은 차례(실행 식별자)와 그 실행을 읽은 횟수를 돌려준다. */
interface Served {
  readonly reads: string[];
  count(runId: string): number;
}

/**
 * `GET /traces/{run_id}` 에 답한다. 없는 실행은 404 봉투다. `replies` 의 값은 트레이스, 응답, 또는 그 실행을 몇 번째
 * 읽는지(0부터) 받아 답하는 함수다.
 */
function serveTraces(replies: Record<string, Reply>): Served {
  const reads: string[] = [];
  network.use(
    http.get(api("/traces/:runId"), ({ params }) => {
      const runId = String(params["runId"]);
      const call = reads.filter((read) => read === runId).length;
      reads.push(runId);
      const reply = replies[runId];
      if (reply === undefined) {
        return HttpResponse.json(envelope("not_found", `${runId} 의 트레이스가 없다`), {
          status: 404,
        });
      }
      const answer = typeof reply === "function" ? reply(call) : reply;
      return answer instanceof Response || answer instanceof Promise
        ? answer
        : HttpResponse.json(answer);
    }),
  );
  return { reads, count: (runId) => reads.filter((read) => read === runId).length };
}

/** 끝난 실행 하나. 요청 글은 `<식별자>의 요청`, 출력 글은 `<식별자>의 출력`이다. */
function done(runId: string, previous: string | null = null, ts?: string): Trace {
  return trace(runId, [
    started(runId, previous, ts),
    llm(runId, ts),
    finished(runId, `${runId}의 출력`, ts),
  ]);
}

/** 이어 간 두 실행의 대화. 끝 실행은 둘째다. */
const TWO = { first: done("r1"), second: done("r2", "r1") };

async function showChat(runId: string, me: Parameters<typeof signedIn>[0] = {}): Promise<void> {
  signedIn(me);
  renderPage(<ConversationPage runId={runId} />);
  await screen.findByRole("heading", { level: 1, name: "대화" });
}

/** 보이는 실행의 구역. 첫 실행이 첫째다. */
function turnSections(): HTMLElement[] {
  return screen.getAllByRole("region", { name: /^실행 \d+$/ });
}

function panel(): HTMLElement | null {
  return screen.queryByRole("complementary", { name: "실행 패널" });
}

function clock(): UserEvent {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

function setVisibility(state: "visible" | "hidden"): void {
  Object.defineProperty(document, "visibilityState", { configurable: true, get: () => state });
}

afterEach(() => {
  vi.useRealTimers();
  history.replaceState(null, "", "/");
  Reflect.deleteProperty(document, "visibilityState");
});

describe("대화를 다시 그리는 읽기", () => {
  test("끝 실행에서 앞 실행을 거슬러 읽고 첫 실행부터 차례로 그린다", async () => {
    const served = serveTraces({ r2: TWO.second, r1: TWO.first });

    await showChat("r2");
    await screen.findByText("r2의 출력");

    expect(served.reads).toEqual(["r2", "r1"]);
    const [firstTurn, secondTurn] = turnSections();
    expect(within(firstTurn ?? document.body).getByText("r1의 요청")).toBeTruthy();
    expect(within(firstTurn ?? document.body).getByText("r1의 출력")).toBeTruthy();
    expect(within(secondTurn ?? document.body).getByText("r2의 요청")).toBeTruthy();
    expect(within(secondTurn ?? document.body).getByText("r2의 출력")).toBeTruthy();
    expect(turnSections()).toHaveLength(2);
  });

  test("거슬러 읽는 동안은 대화를 불러오는 중이고 다 읽은 뒤 한 번에 그린다", async () => {
    const first = Promise.withResolvers<Response>();
    serveTraces({ r2: TWO.second, r1: () => first.promise });
    signedIn();
    renderPage(<ConversationPage runId="r2" />);

    expect(await screen.findByRole("progressbar", { name: "대화를 불러오는 중" })).toBeTruthy();
    // 끝 실행은 이미 왔지만 앞 실행을 기다리는 동안은 아무것도 그리지 않는다.
    expect(screen.queryByText("r2의 출력")).toBeNull();
    first.resolve(HttpResponse.json(TWO.first));
    expect(await screen.findByText("r1의 출력")).toBeTruthy();
    expect(screen.getByText("r2의 출력")).toBeTruthy();
    expect(screen.queryByRole("progressbar", { name: "대화를 불러오는 중" })).toBeNull();
  });

  test("앞 실행이 없는 대화는 끝 실행 하나만 읽는다", async () => {
    const served = serveTraces({ r1: TWO.first });

    await showChat("r1");
    await screen.findByText("r1의 출력");

    expect(served.reads).toEqual(["r1"]);
    expect(screen.queryByText("앞부분을 읽지 못했다")).toBeNull();
    expect(screen.queryByText("더 앞의 대화는 이 화면에 보이지 않는다")).toBeNull();
  });

  test(
    "끝 실행을 뺀 100개까지만 거슬러 읽고 맨 위에 더 앞이 보이지 않는다고 알린다",
    async () => {
      // r1 이 가장 오래된 실행이고 r102 가 끝 실행이다. 거슬러 읽을 수 있는 것은 r101 부터 r2 까지 100개다.
      const replies: Record<string, Trace> = {};
      for (let index = 1; index <= 102; index += 1) {
        const id = `r${String(index)}`;
        replies[id] = done(id, index === 1 ? null : `r${String(index - 1)}`);
      }
      const served = serveTraces(replies);

      await showChat("r102");
      // 100번을 차례로 읽어 기본 대기(1초)로는 모자란다.
      await screen.findByText("r102의 출력", {}, { timeout: LONG_CHAIN_MS });

      expect(served.reads).toHaveLength(101);
      expect(served.count("r1")).toBe(0);
      expect(turnSections()).toHaveLength(101);
      expect(screen.getByText("더 앞의 대화는 이 화면에 보이지 않는다")).toBeTruthy();
      expect(screen.queryByText("앞부분을 읽지 못했다")).toBeNull();
      // 가장 오래 읽은 실행이 맨 위에 선다.
      expect(within(turnSections()[0] ?? document.body).getByText("r2의 요청")).toBeTruthy();
    },
    LONG_CHAIN_MS + 10_000,
  );

  test(
    "거슬러 읽은 실행이 정확히 100개로 처음에 닿으면 더 앞이 있다고 알리지 않는다",
    async () => {
      // r101 이 끝 실행이고 r1 이 처음이다. 거슬러 읽는 것은 r100 부터 r1 까지 정확히 100개다.
      const replies: Record<string, Trace> = {};
      for (let index = 1; index <= 101; index += 1) {
        const id = `r${String(index)}`;
        replies[id] = done(id, index === 1 ? null : `r${String(index - 1)}`);
      }
      serveTraces(replies);

      await showChat("r101");
      await screen.findByText("r101의 출력", {}, { timeout: LONG_CHAIN_MS });

      expect(turnSections()).toHaveLength(101);
      expect(screen.queryByText("더 앞의 대화는 이 화면에 보이지 않는다")).toBeNull();
    },
    LONG_CHAIN_MS + 10_000,
  );

  test("앞 실행이 404면 읽은 데까지 그리고 맨 위에 앞부분을 읽지 못했다고 알린다", async () => {
    serveTraces({ r3: done("r3", "r2"), r2: done("r2", "r1") });

    await showChat("r3");
    await screen.findByText("r3의 출력");

    expect(turnSections()).toHaveLength(2);
    expect(screen.getByText("앞부분을 읽지 못했다")).toBeTruthy();
    expect(screen.queryByText("r1의 요청")).toBeNull();
  });

  test("앞 실행이 읽히지 않아 500이어도 읽은 데까지 그리고 같은 알림이다", async () => {
    serveTraces({
      r2: done("r2", "r1"),
      r1: HttpResponse.json(envelope("internal_error", "읽을 수 없다"), { status: 500 }),
    });

    await showChat("r2");
    await screen.findByText("r2의 출력");

    expect(turnSections()).toHaveLength(1);
    expect(screen.getByText("앞부분을 읽지 못했다")).toBeTruthy();
  });

  test("지난 실행으로 돌아오는 순환은 거기서 끊고 알린다", async () => {
    serveTraces({ b: done("b", "a"), a: done("a", "b") });

    await showChat("b");
    await screen.findByText("b의 출력");

    expect(turnSections()).toHaveLength(2);
    expect(screen.getByText("앞부분을 읽지 못했다")).toBeTruthy();
  });

  test("끝 실행 자체를 읽지 못하면 실패만 보이고 추적 식별자가 든다", async () => {
    serveTraces({
      r1: HttpResponse.json(envelope("not_found", "그 실행은 없다", "req-404"), { status: 404 }),
    });

    await showChat("r1");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("대화를 읽지 못했다")).toBeTruthy();
    expect(within(alert).getByText("그 실행은 없다")).toBeTruthy();
    expect(within(alert).getByText("req-404")).toBeTruthy();
    expect(screen.queryByRole("region", { name: /^실행 \d+$/ })).toBeNull();
  });

  test("서버에 닿지 못해 앞 실행을 읽지 못하면 끊김이 아니라 읽기의 실패다", async () => {
    serveTraces({ r2: done("r2", "r1"), r1: () => HttpResponse.error() });

    await showChat("r2");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("서버에 닿지 못했다")).toBeTruthy();
    expect(screen.queryByText("r2의 출력")).toBeNull();
  });

  test("주소를 풀 수 없으면 읽지 않고 받은 조각 그대로를 제목으로 실패를 보인다", async () => {
    const served = serveTraces({});
    signedIn();
    renderPage(<ConversationPage runId="%E0%A4%A" />);

    expect(await screen.findByText("주소를 풀 수 없다: %E0%A4%A")).toBeTruthy();
    expect(served.reads).toEqual([]);
  });

  test("퍼센트 인코딩된 조각은 풀어서 읽는다", async () => {
    const served = serveTraces({ "run/odd id": done("run/odd id") });

    await showChat("run%2Fodd%20id");
    await screen.findByText("run/odd id의 출력");

    expect(served.reads).toEqual(["run/odd id"]);
  });

  test("새로 고침은 끝 실행과 앞 실행을 다시 읽고 그동안 다시 확인하는 중이 보인다", async () => {
    const user = userEvent.setup();
    const second = Promise.withResolvers<Response>();
    const served = serveTraces({
      r2: (call) => (call === 0 ? TWO.second : second.promise),
      r1: TWO.first,
    });
    await showChat("r2");
    await screen.findByText("r2의 출력");

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect(await screen.findByRole("progressbar", { name: "다시 확인하는 중" })).toBeTruthy();
    // 다시 확인하는 동안 보인 대화는 지우지 않는다.
    expect(screen.getByText("r2의 출력")).toBeTruthy();
    second.resolve(HttpResponse.json(TWO.second));
    await waitFor(() => {
      expect(screen.queryByRole("progressbar", { name: "다시 확인하는 중" })).toBeNull();
    });
    expect(served.count("r2")).toBe(2);
    expect(served.count("r1")).toBe(2);
  });

  test("다시 읽다 실패하면 보인 대화를 지우고 실패만 보인다", async () => {
    const user = userEvent.setup();
    serveTraces({
      r1: (call) =>
        call === 0
          ? TWO.first
          : HttpResponse.json(envelope("internal_error", "다시 읽지 못했다"), { status: 500 }),
    });
    await showChat("r1");
    await screen.findByText("r1의 출력");

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect(await screen.findByText("다시 읽지 못했다")).toBeTruthy();
    expect(screen.queryByText("r1의 출력")).toBeNull();
  });
});

describe("대화 화면", () => {
  test("머리의 제목은 대화이고 끝 실행의 에이전트를 보이고 대화 목록으로 가는 링크가 있다", async () => {
    serveTraces({ r1: done("r1") });

    await showChat("r1");

    // 제목은 데이터와 무관하게 먼저 그려지므로, 에이전트 이름은 트레이스가 도착할 때까지 기다려 찾는다.
    expect(await screen.findByText("support-bot")).toBeTruthy();
    expect(screen.getByRole("link", { name: "대화 목록" }).getAttribute("href")).toBe("/chat");
    const nav = screen.getByRole("navigation", { name: "관리 화면" });
    expect(within(nav).getByRole("link", { name: "대화" }).getAttribute("aria-current")).toBe(
      "page",
    );
  });

  test("시작 이벤트가 없는 트레이스도 시각 없이 그려지고 화면이 무너지지 않는다", async () => {
    serveTraces({ r1: trace("r1", [llm("r1")]) });

    await showChat("r1");

    expect(await screen.findByRole("region", { name: "실행 1" })).toBeTruthy();
    expect(screen.queryByText(/Invalid Date/)).toBeNull();
  });

  test("요청과 도구 호출 묶음과 출력이 한 실행의 구역에 차례로 선다", async () => {
    serveTraces({
      r1: trace("r1", [
        started("r1"),
        llm("r1"),
        toolCalled("r1", "orders.lookup", "ok"),
        toolCalled("r1", "mail.send", "error"),
        finished("r1", "끝냈다"),
      ]),
    });

    await showChat("r1");
    await screen.findByText("끝냈다");

    const section = turnSections()[0] ?? document.body;
    expect(section.textContent).toMatch(/r1의 요청.*도구 2개를 불렀다.*끝냈다/);
  });

  test("도구 호출은 접혀 있고 펼치면 이름과 성공·실패가 보이며 인자와 결과는 보이지 않는다", async () => {
    const user = userEvent.setup();
    serveTraces({
      r1: trace("r1", [
        started("r1"),
        toolCalled("r1", "orders.lookup", "ok", T0, { content: "비밀 결과", args: { id: "A-1" } }),
        toolCalled("r1", "mail.send", "error"),
        finished("r1", "끝냈다"),
      ]),
    });
    await showChat("r1");
    await screen.findByText("끝냈다");

    const fold = screen.getByText("도구 2개를 불렀다").closest("details");
    expect(fold?.open).toBe(false);
    await user.click(screen.getByText("도구 2개를 불렀다"));

    expect(fold?.open).toBe(true);
    const items = within(fold ?? document.body).getAllByRole("listitem");
    expect(items.map((item) => item.textContent)).toEqual(["orders.lookup성공", "mail.send실패"]);
    expect(screen.queryByText("비밀 결과")).toBeNull();
    expect(screen.queryByText(/A-1/)).toBeNull();
  });

  test("도구를 부르지 않은 실행에는 도구 호출 묶음이 없다", async () => {
    serveTraces({ r1: done("r1") });

    await showChat("r1");
    await screen.findByText("r1의 출력");

    expect(screen.queryByText(/도구 \d+개를 불렀다/)).toBeNull();
  });

  test("출력은 마크다운으로 그리고 원시 HTML 은 글자로 보인다", async () => {
    serveTraces({
      r1: trace("r1", [started("r1"), finished("r1", "**굵은 글** 과 <b>태그</b>")]),
    });

    await showChat("r1");

    const bold = await screen.findByText("굵은 글");
    expect(bold.tagName).toBe("STRONG");
    expect(screen.getByText(/<b>태그<\/b>/)).toBeTruthy();
  });

  test("실패한 실행은 실패 알림에 실패 이벤트의 글을 보인다", async () => {
    serveTraces({ r1: trace("r1", [started("r1"), failed("r1", "모델이 답하지 않았다")]) });

    await showChat("r1");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("실행이 실패했다")).toBeTruthy();
    expect(within(alert).getByText("모델이 답하지 않았다")).toBeTruthy();
  });

  test("대화 요약 이벤트는 대화에 보이지 않는다", async () => {
    serveTraces({
      r1: trace("r1", [started("r1"), summarized("r1"), llm("r1"), finished("r1", "답")]),
    });

    await showChat("r1");
    await screen.findByText("답");

    expect(screen.queryByText("요약")).toBeNull();
  });

  test("승인은 결정한 계정과 시각과 도구를 말하고 거부는 거부했다고 말한다", async () => {
    serveTraces({
      r1: trace("r1", [
        started("r1"),
        paused("r1", "mail.send"),
        granted("r1", "lee.ops", "2026-11-27T03:30:00+00:00"),
        resumed("r1"),
        paused("r1", "pay.refund"),
        denied("r1", "park.ops", "금액이 크다", "2026-11-27T03:40:00+00:00"),
        finished("r1", "접었다"),
      ]),
    });

    await showChat("r1");
    await screen.findByText("접었다");

    const section = turnSections()[0] ?? document.body;
    expect(section.textContent).toContain("lee.ops가 2026-11-26 22:30:00에 승인했다: mail.send");
    expect(section.textContent).toContain(
      "park.ops가 2026-11-26 22:40:00에 거부했다: pay.refund (금액이 크다)",
    );
  });

  test("결정한 계정이 비면 요청한 주체가 아니라 결정한 주체의 이름을 쓴다", async () => {
    serveTraces({
      r1: trace("r1", [
        started("r1", null, undefined, { principal: "hong" }),
        paused("r1", "mail.send"),
        granted("r1", null, undefined, "ops-cli"),
        finished("r1", "보냈다"),
      ]),
    });

    await showChat("r1");
    await screen.findByText("보냈다");

    expect(screen.getByText(/ops-cli가 .*에 승인했다/)).toBeTruthy();
    expect(screen.queryByText(/hong가 .*에 승인했다/)).toBeNull();
  });

  test("결정을 기다리는 실행은 그 도구 호출 자리에 승인 묻기가 서고 거부가 승인보다 먼저다", async () => {
    serveTraces({ r1: trace("r1", [started("r1"), paused("r1", "mail.send")]) });
    network.use(http.get(api("/plugins"), () => HttpResponse.json([])));

    await showChat("r1");

    const ask = await screen.findByRole("region", { name: "승인 묻기" });
    expect(within(ask).getByText("mail.send")).toBeTruthy();
    expect(
      within(ask)
        .getAllByRole("button")
        .map((button) => button.textContent),
    ).toEqual(["거부", "승인"]);
  });

  test("시각은 브라우저의 시간대로 보인다", async () => {
    serveTraces({ r1: done("r1", null, "2026-11-27T01:00:00+00:00") });

    await showChat("r1");

    expect(await screen.findByText("2026-11-26 20:00:00")).toBeTruthy();
  });

  test("상태 배지는 실행마다 그 실행의 결말이다", async () => {
    serveTraces({
      r2: trace("r2", [started("r2", "r1"), failed("r2", "망했다")]),
      r1: done("r1"),
    });

    await showChat("r2");
    await screen.findByText("망했다");

    const [firstTurn, secondTurn] = turnSections();
    expect(within(firstTurn ?? document.body).getByText("끝남")).toBeTruthy();
    expect(within(secondTurn ?? document.body).getByText("실패")).toBeTruthy();
  });
});

describe("도는 실행 이어 보기", () => {
  /** 마지막 이벤트가 모델 호출인, 결말 없는 실행. */
  function running(ts: string): Trace {
    return trace("r1", [started("r1", null, ts), llm("r1", ts)]);
  }

  test("결말 없는 끝 실행은 진행 표시로 다음 일을 보인다", async () => {
    // 마지막 이벤트가 지금이라 멈출 때가 지나지 않았다.
    const now = new Date().toISOString();
    serveTraces({ r1: trace("r1", [started("r1", null, now)]) });

    await showChat("r1");

    expect(await screen.findByRole("progressbar", { name: "모델을 부르는 중" })).toBeTruthy();
  });

  test("모델 호출 다음이면 도구를 부르는 중이다", async () => {
    const now = new Date().toISOString();
    serveTraces({ r1: trace("r1", [started("r1", null, now), llm("r1", now)]) });

    await showChat("r1");

    expect(await screen.findByRole("progressbar", { name: "도구를 부르는 중" })).toBeTruthy();
  });

  test("3초마다 끝 실행 하나만 다시 읽고 새 이벤트를 그린다", async () => {
    clock();
    const now = Date.now();
    const served = serveTraces({
      r2: (call) =>
        call < 2
          ? trace("r2", [started("r2", "r1", new Date(now).toISOString())])
          : trace("r2", [
              started("r2", "r1", new Date(now).toISOString()),
              toolCalled("r2", "orders.lookup", "ok", new Date(now).toISOString()),
              llm("r2", new Date(now).toISOString()),
              finished("r2", "새 출력", new Date(now).toISOString()),
            ]),
      r1: TWO.first,
    });
    await showChat("r2");
    await screen.findByText("r1의 출력");
    expect(served.count("r2")).toBe(1);

    // 3초가 되기 전에는 다시 읽지 않는다(더 이른 간격으로 나가면 여기서 빨개진다).
    await vi.advanceTimersByTimeAsync(2_900);
    expect(served.count("r2")).toBe(1);
    await vi.advanceTimersByTimeAsync(200);
    await waitFor(() => {
      expect(served.count("r2")).toBe(2);
    });

    await vi.advanceTimersByTimeAsync(3_000);
    expect(await screen.findByText("새 출력")).toBeTruthy();
    expect(screen.getByText("도구 1개를 불렀다")).toBeTruthy();
    // 앞 실행은 다시 읽지 않는다.
    expect(served.count("r1")).toBe(1);
  });

  test("결말이 오면 더는 읽지 않는다", async () => {
    clock();
    const now = new Date(Date.now()).toISOString();
    const served = serveTraces({
      r1: (call) =>
        call === 0
          ? trace("r1", [started("r1", null, now)])
          : trace("r1", [started("r1", null, now), finished("r1", "끝", now)]),
    });
    await showChat("r1");
    await screen.findByRole("progressbar", { name: "모델을 부르는 중" });

    await vi.advanceTimersByTimeAsync(3_100);
    expect(await screen.findByText("끝")).toBeTruthy();
    const afterOutcome = served.count("r1");
    await vi.advanceTimersByTimeAsync(60_000);

    expect(served.count("r1")).toBe(afterOutcome);
  });

  test("승인으로 다시 도는 실행은 앞의 일시정지가 남아 있어도 계속 읽는다", async () => {
    clock();
    const now = new Date(Date.now()).toISOString();
    const served = serveTraces({
      r1: trace("r1", [
        started("r1", null, now),
        paused("r1", "mail.send", now),
        granted("r1", "lee.ops", now),
        resumed("r1", now),
      ]),
    });
    await showChat("r1");
    await screen.findByText(/lee.ops가 .*에 승인했다/);

    await vi.advanceTimersByTimeAsync(3_100);
    await vi.advanceTimersByTimeAsync(3_000);

    await waitFor(() => {
      expect(served.count("r1")).toBeGreaterThanOrEqual(3);
    });
  });

  test("일시정지로 멈춘 실행은 다시 읽지 않는다", async () => {
    clock();
    const now = new Date(Date.now()).toISOString();
    const served = serveTraces({
      r1: trace("r1", [started("r1", null, now), paused("r1", "mail.send", now)]),
    });
    network.use(http.get(api("/plugins"), () => HttpResponse.json([])));
    await showChat("r1");
    await screen.findByRole("region", { name: "승인 묻기" });

    await vi.advanceTimersByTimeAsync(30_000);

    expect(served.count("r1")).toBe(1);
  });

  test("마지막 이벤트 뒤 실행 제한 시간이 지나면 끝맺지 못한 것으로 보인다고 알리고 멈춘다", async () => {
    clock();
    const last = Date.now();
    // 마지막 이벤트는 이미 60초 전이고 제한 시간은 120초다. 같은 트레이스가 계속 온다.
    const served = serveTraces({ r1: running(new Date(last - 60_000).toISOString()) });
    await showChat("r1", { run_timeout_seconds: 120 });
    await screen.findByRole("progressbar", { name: "도구를 부르는 중" });
    expect(screen.queryByText("끝맺지 못한 것으로 보입니다")).toBeNull();

    await vi.advanceTimersByTimeAsync(60_000);

    // 같은 트레이스가 다시 왔을 뿐인데도 알림이 선다. 알림을 그리는 부품이 다시 확인하는 중인지를 함께 읽는다.
    expect(await screen.findByText("끝맺지 못한 것으로 보입니다")).toBeTruthy();
    expect(screen.queryByRole("progressbar", { name: "도구를 부르는 중" })).toBeNull();
    const stopped = served.count("r1");
    await vi.advanceTimersByTimeAsync(60_000);
    expect(served.count("r1")).toBe(stopped);
  });

  test("멈출 때는 서버가 알려 준 실행 제한 시간으로 정한다", async () => {
    clock();
    const last = Date.now();
    // 같은 트레이스인데 제한 시간이 600초면 90초 뒤에도 알림이 서지 않고 계속 읽는다.
    const served = serveTraces({ r1: running(new Date(last).toISOString()) });
    await showChat("r1", { run_timeout_seconds: 600 });
    await screen.findByRole("progressbar", { name: "도구를 부르는 중" });

    await vi.advanceTimersByTimeAsync(90_000);

    expect(screen.queryByText("끝맺지 못한 것으로 보입니다")).toBeNull();
    expect(served.count("r1")).toBeGreaterThan(20);
  });

  test("열자마자 멈출 때가 지난 대화는 읽기 한 번 뒤에 알림이 서고 새로 고침으로 다시 읽는다", async () => {
    clock();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const served = serveTraces({
      r1: (call) =>
        call === 0
          ? running(new Date(Date.now() - 1_000_000).toISOString())
          : trace("r1", [started("r1"), finished("r1", "뒤늦게 끝")]),
    });
    await showChat("r1", { run_timeout_seconds: 300 });
    expect(await screen.findByText("끝맺지 못한 것으로 보입니다")).toBeTruthy();
    await vi.advanceTimersByTimeAsync(30_000);
    expect(served.count("r1")).toBe(1);

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect(await screen.findByText("뒤늦게 끝")).toBeTruthy();
    expect(screen.queryByText("끝맺지 못한 것으로 보입니다")).toBeNull();
  });

  test("주기 읽기가 실패하면 실패를 보이고 읽기를 쉬며 새로 고침이 다시 돌게 한다", async () => {
    clock();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const now = new Date(Date.now()).toISOString();
    const served = serveTraces({
      r1: (call) =>
        call === 1
          ? HttpResponse.json(envelope("internal_error", "서버가 쉰다"), { status: 500 })
          : trace("r1", [started("r1", null, now)]),
    });
    await showChat("r1");
    await screen.findByRole("progressbar", { name: "모델을 부르는 중" });

    await vi.advanceTimersByTimeAsync(3_100);
    expect(await screen.findByText("서버가 쉰다")).toBeTruthy();
    const afterFailure = served.count("r1");
    await vi.advanceTimersByTimeAsync(30_000);
    expect(served.count("r1")).toBe(afterFailure);

    await user.click(screen.getByRole("button", { name: "새로 고침" }));
    await screen.findByRole("progressbar", { name: "모델을 부르는 중" });
    await vi.advanceTimersByTimeAsync(3_100);

    await waitFor(() => {
      expect(served.count("r1")).toBeGreaterThan(afterFailure + 1);
    });
  });

  test("창이 가려진 동안은 읽지 않고 돌아오면 읽는다", async () => {
    clock();
    const now = new Date(Date.now()).toISOString();
    const served = serveTraces({ r1: trace("r1", [started("r1", null, now)]) });
    await showChat("r1");
    await screen.findByRole("progressbar", { name: "모델을 부르는 중" });
    setVisibility("hidden");
    fireEvent(document, new Event("visibilitychange"));
    const before = served.count("r1");

    await vi.advanceTimersByTimeAsync(30_000);
    expect(served.count("r1")).toBe(before);

    setVisibility("visible");
    await act(async () => {
      fireEvent(document, new Event("visibilitychange"));
      await vi.advanceTimersByTimeAsync(100);
    });

    await waitFor(() => {
      expect(served.count("r1")).toBeGreaterThan(before);
    });
  });
});

describe("실행 패널", () => {
  test("자세히를 누르면 오른쪽 패널이 열리고 주소에 질의가 붙고 그 실행의 이벤트가 UTC 값 그대로 선다", async () => {
    const user = userEvent.setup();
    serveTraces({ r2: TWO.second, r1: TWO.first });
    await showChat("r2");
    await screen.findByText("r2의 출력");
    expect(panel()).toBeNull();

    await user.click(
      within(turnSections()[1] ?? document.body).getByRole("button", { name: "자세히" }),
    );

    const opened = await screen.findByRole("complementary", { name: "실행 패널" });
    expect(location.search).toBe("?run=r2");
    expect(within(opened).getByRole("heading", { level: 2, name: "실행" })).toBeTruthy();
    expect(within(opened).getByText("r2")).toBeTruthy();
    expect(await within(opened).findByText("run_started")).toBeTruthy();
    // 패널의 시각은 트레이스의 글자 그대로다. 대화의 시각과 달리 시간대로 바꾸지 않는다.
    expect(within(opened).getAllByText("2026-11-27T01:00:00+00:00").length).toBeGreaterThan(0);
    expect(within(opened).getByText("kim.dev")).toBeTruthy();
    // 결정 자리는 두지 않는다.
    expect(within(opened).queryByRole("button", { name: /승인|거부/ })).toBeNull();
    expect(
      within(turnSections()[1] ?? document.body)
        .getByRole("button", { name: "자세히" })
        .getAttribute("aria-expanded"),
    ).toBe("true");
    expect(
      within(turnSections()[0] ?? document.body)
        .getByRole("button", { name: "자세히" })
        .getAttribute("aria-expanded"),
    ).toBe("false");
  });

  test("주소의 질의로 열린 채 화면이 서고 열린 패널이 대화를 가리는 덮개는 없다", async () => {
    history.replaceState(null, "", "/chat/r2?run=r1");
    serveTraces({ r2: TWO.second, r1: TWO.first });

    await showChat("r2");

    expect(await screen.findByRole("complementary", { name: "실행 패널" })).toBeTruthy();
    expect(screen.queryByRole("dialog")).toBeNull();
    // 대화는 패널이 열린 채로도 그대로 읽힌다.
    expect(await screen.findByText("r2의 출력")).toBeTruthy();
  });

  test("닫기 버튼은 패널을 닫고 질의를 뺀다", async () => {
    const user = userEvent.setup();
    history.replaceState(null, "", "/chat/r1?run=r1&keep=1");
    serveTraces({ r1: TWO.first });
    await showChat("r1");
    const opened = await screen.findByRole("complementary", { name: "실행 패널" });

    await user.click(within(opened).getByRole("button", { name: "닫기" }));

    expect(panel()).toBeNull();
    expect(location.search).toBe("?keep=1");
  });

  test("Esc 도 패널을 닫고 질의를 뺀다", async () => {
    const user = userEvent.setup();
    history.replaceState(null, "", "/chat/r1?run=r1");
    serveTraces({ r1: TWO.first });
    await showChat("r1");
    await screen.findByRole("complementary", { name: "실행 패널" });

    await user.keyboard("{Escape}");

    expect(panel()).toBeNull();
    expect(location.search).toBe("");
  });

  test("패널이 열릴 때 포커스가 닫기 버튼으로 간다", async () => {
    history.replaceState(null, "", "/chat/r1?run=r1");
    serveTraces({ r1: TWO.first });
    await showChat("r1");

    const opened = await screen.findByRole("complementary", { name: "실행 패널" });

    expect(document.activeElement).toBe(within(opened).getByRole("button", { name: "닫기" }));
  });

  test("자세히로 연 패널을 닫으면 포커스가 그 자세히 버튼으로 돌아온다", async () => {
    const user = userEvent.setup();
    serveTraces({ r2: TWO.second, r1: TWO.first });
    await showChat("r2");
    await screen.findByText("r2의 출력");
    const detail = within(turnSections()[1] ?? document.body).getByRole("button", {
      name: "자세히",
    });
    await user.click(detail);
    const opened = await screen.findByRole("complementary", { name: "실행 패널" });

    await user.click(within(opened).getByRole("button", { name: "닫기" }));

    expect(panel()).toBeNull();
    expect(document.activeElement).toBe(
      within(turnSections()[1] ?? document.body).getByRole("button", { name: "자세히" }),
    );
  });

  test("열린 채 다른 실행의 자세히를 누르면 패널이 닫히지 않고 내용만 바뀐다", async () => {
    const user = userEvent.setup();
    serveTraces({
      r2: TWO.second,
      r1: trace("r1", [
        started("r1", null, undefined, { request: "첫 요청의 글" }),
        finished("r1", "첫 출력"),
      ]),
    });
    await showChat("r2");
    await screen.findByText("r2의 출력");
    await user.click(
      within(turnSections()[1] ?? document.body).getByRole("button", { name: "자세히" }),
    );
    const opened = await screen.findByRole("complementary", { name: "실행 패널" });
    await within(opened).findByText("run_started");

    await user.click(
      within(turnSections()[0] ?? document.body).getByRole("button", { name: "자세히" }),
    );

    await waitFor(() => {
      expect(location.search).toBe("?run=r1");
    });
    expect(panel()).toBe(opened);
    expect(await within(opened).findByText("첫 요청의 글")).toBeTruthy();
    expect(within(opened).queryByText("r2의 요청")).toBeNull();
  });

  test("패널은 방문 기록을 늘리지 않는다", async () => {
    const user = userEvent.setup();
    serveTraces({ r1: TWO.first });
    await showChat("r1");
    await screen.findByText("r1의 출력");
    const length = history.length;

    await user.click(screen.getByRole("button", { name: "자세히" }));
    await screen.findByRole("complementary", { name: "실행 패널" });

    expect(history.length).toBe(length);
  });

  test("끝 실행의 패널은 대화와 같은 값을 써서 같은 트레이스를 두 번 받지 않는다", async () => {
    const user = userEvent.setup();
    const served = serveTraces({ r1: TWO.first });
    await showChat("r1");
    await screen.findByText("r1의 출력");
    expect(served.count("r1")).toBe(1);

    await user.click(screen.getByRole("button", { name: "자세히" }));
    await within(await screen.findByRole("complementary", { name: "실행 패널" })).findByText(
      "run_started",
    );

    expect(served.count("r1")).toBe(1);
  });

  test("패널의 새로 고침은 그 실행의 트레이스를 다시 읽는다", async () => {
    const user = userEvent.setup();
    history.replaceState(null, "", "/chat/r2?run=r1");
    const served = serveTraces({ r2: TWO.second, r1: TWO.first });
    await showChat("r2");
    const opened = await screen.findByRole("complementary", { name: "실행 패널" });
    await within(opened).findByText("run_started");
    const before = served.count("r1");

    await user.click(within(opened).getByRole("button", { name: "새로 고침" }));

    await waitFor(() => {
      expect(served.count("r1")).toBe(before + 1);
    });
    // 대화 쪽 읽기는 건드리지 않는다.
    expect(served.count("r2")).toBe(1);
  });

  test("패널은 주기 읽기를 따로 걸지 않는다", async () => {
    clock();
    history.replaceState(null, "", "/chat/r2?run=r1");
    const served = serveTraces({ r2: TWO.second, r1: TWO.first });
    await showChat("r2");
    await within(await screen.findByRole("complementary", { name: "실행 패널" })).findByText(
      "run_started",
    );
    const before = served.count("r1");

    await vi.advanceTimersByTimeAsync(60_000);

    expect(served.count("r1")).toBe(before);
  });

  test("패널의 실행을 읽지 못하면 패널 안에서 실패만 보이고 대화는 그대로다", async () => {
    history.replaceState(null, "", "/chat/r1?run=gone");
    serveTraces({ r1: TWO.first });

    await showChat("r1");

    const opened = await screen.findByRole("complementary", { name: "실행 패널" });
    expect(await within(opened).findByText("실행을 읽지 못했다")).toBeTruthy();
    expect(await screen.findByText("r1의 출력")).toBeTruthy();
  });
});
