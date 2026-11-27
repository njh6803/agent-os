// 대화 화면의 쓰기(admin-login 티켓 11). 새 대화에서 에이전트를 골라 보내고, 끝난 대화를 끝 실행에서 이어 가고, 실패한 실행을
// 다시 보내고, 일시정지의 승인 묻기에 결정하는 일을 본다. 읽기와 도는 실행 이어 보기와 실행 패널은 `ConversationPage.test.tsx` 가
// 본다. 최종 사용자의 대화는 읽기만 된다.
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 응답 스트림은 `ReadableStream` 으로 프레임을 시간 간격을 두고
// 낸다(testing/stream.ts). 사이에 약속을 두면 그것이 풀릴 때까지 다음 프레임을 내지 않아, 스트림이 열려 있는 동안의 화면을 본다.
// 로그인은 쿠키라 테스트에서 보이지 않고, 화면은 `GET /auth/me` 에 계정이 답해야 그려진다(`signedIn`).

import { screen, waitFor, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, test, vi } from "vitest";
import {
  failed,
  finished,
  granted,
  llm,
  paused,
  resumed,
  started,
  T0,
  toolCalled,
  trace,
} from "../../testing/events";
import {
  api,
  envelope,
  network,
  type Plugin,
  type PluginRow,
  type RunEvent,
  type Trace,
} from "../../testing/network";
import { renderPage } from "../../testing/render";
import { frame, KEEPALIVE, resumeStream, type Step } from "../../testing/stream";
import { signedIn, visited } from "../../testing/session";
import { ConversationPage } from "./ConversationPage";

type TraceEvent = Trace["events"][number];

/** 최종 사용자의 주체. 사이트의 발급자와 `sub` 를 구분자 `|` 로 묶은 이름이다(end-user-channel 명세 "주체"). */
const END_USER = "https://shop.example|user-42";
const END_USER_LINE = "최종 사용자의 대화라 이어 가거나 결정할 수 없다";

type PluginKind = "agent" | "mcp" | "model" | "skill";

interface PluginOptions {
  readonly enabled?: boolean;
  readonly mcp?: readonly string[];
  readonly requires?: readonly string[];
}

/** 플러그인 하나. 매니페스트를 읽은 보통 행이다. */
function plugin(kind: PluginKind, name: string, options: PluginOptions = {}): Plugin {
  const { enabled = true, mcp = [], requires = [] } = options;
  return {
    kind,
    name,
    enabled,
    manifest: {
      schema_version: "1",
      kind,
      name,
      version: "0.1.0",
      entrypoint: null,
      mcp: [...mcp],
      requires_approval: [...requires],
      conversation_limit: null,
      max_turns: null,
      max_tool_calls: null,
      model: null,
      skills: [],
      provider: null,
      model_id: null,
      max_tokens: null,
      temperature: null,
      base_url: null,
      api_key_env: null,
      server: null,
    },
  };
}

/** `GET /plugins` 에 그 행들이나 그 응답으로 답한다. 요청마다의 주소를 쌓아 호출 횟수를 센다. */
function servePlugins(rows: readonly PluginRow[] | Response): string[] {
  const reads: string[] = [];
  network.use(
    http.get(api("/plugins"), ({ request }) => {
      reads.push(request.url);
      return rows instanceof Response ? rows.clone() : HttpResponse.json([...rows]);
    }),
  );
  return reads;
}

/** 켜진 에이전트 둘. 고르는 칸이 이 이름들을 보인다. */
const AGENTS: PluginRow[] = [plugin("agent", "support-bot"), plugin("agent", "echo")];

/** `GET /traces/{run_id}` 에 답한다. 값은 트레이스이거나 몇 번째 읽기인지(0부터) 받아 답하는 함수다. */
function serveTraces(replies: Record<string, Trace | ((call: number) => Trace | Response)>): {
  count: (runId: string) => number;
} {
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
      return answer instanceof Response ? answer : HttpResponse.json(answer);
    }),
  );
  return { count: (runId) => reads.filter((read) => read === runId).length };
}

/** 쓰기 경로 하나에 답한다. 요청마다의 본문을 쌓는다. `reply` 는 몇 번째 요청인지(0부터) 받는다. */
function servePost(path: string, reply: (call: number) => Response | Promise<Response>): unknown[] {
  const sent: unknown[] = [];
  network.use(
    http.post(api(path), async ({ request }) => {
      const body: unknown = await request.clone().json();
      sent.push(body);
      return reply(sent.length - 1);
    }),
  );
  return sent;
}

/** 응답 스트림이 싣는 이벤트. 트레이스에만 있는 읽지 못한 이벤트(`unknown`)는 스트림에 실리지 않는다. */
function onStream(event: TraceEvent): RunEvent {
  if (event.type === "unknown") {
    throw new Error("읽지 못한 이벤트는 응답 스트림에 싣지 못한다");
  }
  return event;
}

/** 이벤트와 걸음으로 응답 스트림을 만든다. 글자는 걸음 그대로 낸다. */
function stream(steps: readonly (TraceEvent | Step)[]): Response {
  return resumeStream(
    steps.map((step) =>
      typeof step === "object" && !(step instanceof Promise) ? frame(onStream(step)) : step,
    ),
  );
}

function clock(): UserEvent {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

function button(name: string): HTMLButtonElement {
  return screen.getByRole<HTMLButtonElement>("button", { name });
}

function box(name: string): HTMLTextAreaElement {
  return screen.getByRole<HTMLTextAreaElement>("textbox", { name });
}

/** 입력 칸에 글을 쓰고 보내기를 누른다. */
async function sendText(user: UserEvent, text: string): Promise<void> {
  await user.type(box("요청"), text);
  await user.click(button("보내기"));
}

/** 새 대화 화면을 열고 에이전트 목록이 설 때까지 기다린다. */
async function openNew(): Promise<UserEvent> {
  const user = userEvent.setup();
  signedIn();
  renderPage(<ConversationPage runId={null} />);
  await screen.findByRole("combobox", { name: "에이전트" });
  return user;
}

/** 대화 화면을 열고 끝 실행의 구역이 설 때까지 기다린다. */
async function openChat(
  runId: string,
  me: Parameters<typeof signedIn>[0] = {},
): Promise<UserEvent> {
  const user = userEvent.setup();
  signedIn(me);
  renderPage(<ConversationPage runId={runId} />);
  await screen.findByRole("region", { name: "실행 1" });
  return user;
}

/** 끝난 실행 하나. 요청 글은 `<식별자>의 요청`, 출력 글은 `<식별자>의 출력`이다. */
function done(runId: string, previous: string | null = null, agent = "support-bot"): Trace {
  return trace(runId, [
    started(runId, previous, T0, { agent }),
    llm(runId),
    finished(runId, `${runId}의 출력`),
  ]);
}

/** 스트림이 시작되는 이벤트. 새 실행이고 시각은 지금이라 멈출 때가 지나지 않았다. */
function startedNow(
  runId: string,
  previous: string | null,
  request: string,
  agent: string,
): TraceEvent {
  return started(runId, previous, new Date().toISOString(), { agent, request });
}

/** 스트림이 끝난 뒤 다시 읽는 트레이스. */
function readBack(runId: string, previous: string | null, request: string, output: string): Trace {
  return trace(runId, [started(runId, previous, T0, { request }), finished(runId, output)]);
}

afterEach(async () => {
  vi.useRealTimers();
  // 보내기가 끝나 끝 실행이 바뀌면 SWR 이 마운트 때 한 번 더 확인한다. 그 읽기가 시험이 끝난 뒤 다음 시험에 새지 않게 기다린다.
  await new Promise((resolve) => setTimeout(resolve, 50));
  history.replaceState(null, "", "/");
});

describe("새 대화", () => {
  test("머리의 제목은 새 대화이고 새로 고침이 없고 켜진 에이전트를 고르는 칸이 있다", async () => {
    servePlugins([
      ...AGENTS,
      plugin("agent", "off-bot", { enabled: false }),
      plugin("mcp", "fixture"),
    ]);

    await openNew();

    expect(screen.getByRole("heading", { level: 1, name: "새 대화" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "새로 고침" })).toBeNull();
    const options = within(screen.getByRole("combobox", { name: "에이전트" })).getAllByRole(
      "option",
    );
    // 꺼진 에이전트와 에이전트가 아닌 플러그인은 고르지 못한다.
    expect(options.map((option) => option.textContent)).toEqual(["support-bot", "echo"]);
    expect(screen.getByRole("link", { name: "대화 목록" }).getAttribute("href")).toBe("/chat");
  });

  test("에이전트를 고르고 보내면 시작 요청이 가고 주소가 그 실행으로 바뀌고 응답이 대화에 붙는다", async () => {
    servePlugins(AGENTS);
    const sent = servePost("/runs", () =>
      stream([startedNow("r9", null, "안녕", "echo"), llm("r9"), finished("r9", "반가워")]),
    );
    const read = serveTraces({ r9: readBack("r9", null, "안녕", "반가워") });
    const user = await openNew();
    const length = history.length;

    await user.selectOptions(screen.getByRole("combobox", { name: "에이전트" }), "echo");
    await sendText(user, "안녕");

    expect(await screen.findByText("반가워")).toBeTruthy();
    expect(sent).toEqual([{ agent: "echo", request: "안녕" }]);
    expect(location.pathname).toBe("/chat/r9");
    // 주소는 방문 기록을 늘리지 않고 바뀐다. 뒤로 가기가 빈 새 대화가 아니라 목록으로 가게 하려는 것이다.
    expect(history.length).toBe(length);
    // 끝난 뒤에는 읽은 대화다. 머리가 대화로 바뀌고 입력 칸이 이어 보내기를 연다.
    expect(await screen.findByRole("heading", { level: 1, name: "대화" })).toBeTruthy();
    expect(read.count("r9")).toBeGreaterThanOrEqual(1);
    expect(box("요청").value).toBe("");
  });

  test("보내는 동안 요청이 말풍선으로 서고 진행 표시가 단계를 따라 바뀌고 글은 쓰되 보내기는 막힌다", async () => {
    servePlugins(AGENTS);
    const beforeStart = Promise.withResolvers<undefined>();
    const afterStart = Promise.withResolvers<undefined>();
    const afterModel = Promise.withResolvers<undefined>();
    servePost("/runs", () =>
      stream([
        beforeStart.promise,
        startedNow("r9", null, "안녕", "echo"),
        afterStart.promise,
        llm("r9"),
        afterModel.promise,
        finished("r9", "반가워"),
      ]),
    );
    serveTraces({ r9: readBack("r9", null, "안녕", "반가워") });
    const user = await openNew();

    await sendText(user, "안녕");

    // 시작 이벤트가 오기 전에도 보낸 요청이 보이고 주소는 아직 새 대화다.
    expect(await screen.findByText("안녕")).toBeTruthy();
    expect(screen.getByRole("progressbar", { name: "모델을 부르는 중" })).toBeTruthy();
    expect(location.pathname).not.toBe("/chat/r9");
    beforeStart.resolve(undefined);
    await waitFor(() => {
      expect(location.pathname).toBe("/chat/r9");
    });
    expect(screen.getByRole("progressbar", { name: "모델을 부르는 중" })).toBeTruthy();
    // 도는 동안 글은 쓸 수 있고(초안) 보내기만 막는다.
    await user.type(box("요청"), "다음 질문");
    expect(box("요청").value).toBe("다음 질문");
    expect(button("보내기").disabled).toBe(true);
    expect(screen.getByText("실행이 끝나면 보낼 수 있다.")).toBeTruthy();
    afterStart.resolve(undefined);
    expect(await screen.findByRole("progressbar", { name: "도구를 부르는 중" })).toBeTruthy();
    afterModel.resolve(undefined);

    expect(await screen.findByText("반가워")).toBeTruthy();
    await waitFor(() => {
      expect(button("보내기").disabled).toBe(false);
    });
    // 쓰던 초안은 지워지지 않는다.
    expect(box("요청").value).toBe("다음 질문");
  });

  test("요청이 공백뿐이면 보낼 수 없다", async () => {
    servePlugins(AGENTS);
    const user = await openNew();

    expect(button("보내기").disabled).toBe(true);
    await user.type(box("요청"), "   ");

    expect(button("보내기").disabled).toBe(true);
  });

  test("켜진 에이전트가 없으면 고르는 칸 대신 안내가 서고 보낼 수 없다", async () => {
    servePlugins([plugin("agent", "off-bot", { enabled: false })]);
    const user = userEvent.setup();
    signedIn();
    renderPage(<ConversationPage runId={null} />);

    expect(await screen.findByText(/켜진 에이전트가 없다/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "플러그인 목록" }).getAttribute("href")).toBe("/");
    await user.type(box("요청"), "안녕");
    expect(button("보내기").disabled).toBe(true);
  });

  test("플러그인 목록을 읽지 못하면 에이전트를 고르지 못한다고 알린다", async () => {
    servePlugins(HttpResponse.json(envelope("internal_error", "서버가 쉰다"), { status: 500 }));
    signedIn();
    renderPage(<ConversationPage runId={null} />);

    expect(
      await screen.findByText("플러그인 목록을 읽지 못해 에이전트를 고르지 못한다"),
    ).toBeTruthy();
    expect(button("보내기").disabled).toBe(true);
  });

  test("목록을 불러오는 동안은 불러오는 중이라고 말한다", async () => {
    const hold = Promise.withResolvers<Response>();
    network.use(http.get(api("/plugins"), () => hold.promise));
    signedIn();
    renderPage(<ConversationPage runId={null} />);

    expect(await screen.findByText("켜진 에이전트를 불러오는 중")).toBeTruthy();
    hold.resolve(HttpResponse.json([...AGENTS]));
    expect(await screen.findByRole("combobox", { name: "에이전트" })).toBeTruthy();
  });

  test("요청이 받아들여지지 않으면 제목과 서버의 메시지와 추적 식별자를 보이고 대화는 서지 않는다", async () => {
    servePlugins(AGENTS);
    servePost("/runs", () =>
      HttpResponse.json(envelope("not_found", "그 에이전트는 없다", "req-404"), { status: 404 }),
    );
    const user = await openNew();

    await sendText(user, "안녕");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("요청을 보내지 못했다")).toBeTruthy();
    expect(within(alert).getByText("그 에이전트는 없다")).toBeTruthy();
    expect(within(alert).getByText("req-404")).toBeTruthy();
    expect(location.pathname).not.toMatch(/^\/chat\/r/);
  });

  test("서버에 닿지 못하면 서버에 닿지 못했다고 알린다", async () => {
    servePlugins(AGENTS);
    network.use(http.post(api("/runs"), () => HttpResponse.error()));
    const user = await openNew();

    await sendText(user, "안녕");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("요청을 보내지 못했다")).toBeTruthy();
    expect(within(alert).getByText("서버에 닿지 못했다")).toBeTruthy();
  });

  test("응답 스트림이 결말 없이 끊겨도 보내기를 다시 하지 않고 트레이스를 다시 읽어 이어 본다", async () => {
    const user = clock();
    servePlugins(AGENTS);
    const now = new Date().toISOString();
    const begin = started("r9", null, now, { agent: "echo", request: "안녕" });
    // 결말 없이 닫는다. MSW 에서는 도중의 끊김도 이 모양으로 온다(testing/stream.ts).
    const sent = servePost("/runs", () => stream([begin, KEEPALIVE]));
    const read = serveTraces({
      r9: (call) =>
        call < 2 ? trace("r9", [begin]) : trace("r9", [begin, finished("r9", "뒤늦게 끝", now)]),
    });
    signedIn();
    renderPage(<ConversationPage runId={null} />);
    await screen.findByRole("combobox", { name: "에이전트" });

    await sendText(user, "안녕");

    expect(await screen.findByText("응답 스트림이 끊겼다. 실행은 서버에서 계속된다")).toBeTruthy();
    expect(screen.getByText(/돌아오면 트레이스로 이어 본다/)).toBeTruthy();
    expect(location.pathname).toBe("/chat/r9");
    await waitFor(() => {
      expect(read.count("r9")).toBeGreaterThanOrEqual(1);
    });
    // 도는 실행이라 3초마다 이어 읽고, 결말이 오면 그린다.
    await vi.advanceTimersByTimeAsync(3_100);
    await vi.advanceTimersByTimeAsync(3_100);
    expect(await screen.findByText("뒤늦게 끝")).toBeTruthy();
    expect(sent).toHaveLength(1);
  });

  test("스트림이 열린 채 화면을 떠나면 그 실행을 다시 읽지 않는다", async () => {
    servePlugins(AGENTS);
    const hold = Promise.withResolvers<undefined>();
    servePost("/runs", () =>
      stream([startedNow("r9", null, "안녕", "echo"), hold.promise, finished("r9", "끝")]),
    );
    const read = serveTraces({ r9: done("r9") });
    const user = userEvent.setup();
    signedIn();
    const view = renderPage(<ConversationPage runId={null} />);
    await screen.findByRole("combobox", { name: "에이전트" });
    await sendText(user, "안녕");
    await waitFor(() => {
      expect(location.pathname).toBe("/chat/r9");
    });

    view.unmount();
    hold.resolve(undefined);
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(read.count("r9")).toBe(0);
  });

  test("읽지 못한 프레임이 와도 뒤의 이벤트가 계속 붙는다", async () => {
    servePlugins(AGENTS);
    servePost("/runs", () =>
      stream([
        startedNow("r9", null, "안녕", "echo"),
        frame("이건 JSON 이 아니다"),
        finished("r9", "끝"),
      ]),
    );
    serveTraces({ r9: readBack("r9", null, "안녕", "끝") });
    const user = await openNew();

    await sendText(user, "안녕");

    expect(await screen.findByText("끝")).toBeTruthy();
    expect(location.pathname).toBe("/chat/r9");
  });
});

describe("이어 가기", () => {
  test("끝난 대화는 끝 실행에서 이어 가고 앞 실행을 다시 읽지 않는다", async () => {
    const sent = servePost("/runs/r2/continuation", () =>
      stream([
        startedNow("r3", "r2", "더 알려 줘", "support-bot"),
        llm("r3"),
        finished("r3", "r3의 출력"),
      ]),
    );
    const read = serveTraces({
      r3: readBack("r3", "r2", "더 알려 줘", "r3의 출력"),
      r2: done("r2", "r1"),
      r1: done("r1"),
    });
    const user = await openChat("r2");
    await screen.findByText("r2의 출력");
    expect(screen.getAllByRole("region", { name: /^실행 \d+$/ })).toHaveLength(2);

    await sendText(user, "더 알려 줘");

    await waitFor(() => {
      expect(screen.getAllByRole("region", { name: /^실행 \d+$/ })).toHaveLength(3);
    });
    expect(await screen.findByText("r3의 출력")).toBeTruthy();
    // 에이전트는 끝 실행의 것이고 요청은 이어 가는 실행의 것이다.
    expect(sent).toEqual([{ agent: "support-bot", request: "더 알려 줘" }]);
    expect(location.pathname).toBe("/chat/r3");
    // 이미 읽은 앞 실행은 새 끝 실행의 몫으로 채워져 다시 읽지 않는다.
    expect(read.count("r1")).toBe(1);
    expect(read.count("r2")).toBe(1);
  });

  test("이어 가는 동안 끝 실행의 구역 아래에 새 구역이 서고 도는 동안은 보내기가 막힌다", async () => {
    const hold = Promise.withResolvers<undefined>();
    servePost("/runs/r1/continuation", () =>
      stream([
        startedNow("r2", "r1", "또", "support-bot"),
        hold.promise,
        finished("r2", "r2의 출력"),
      ]),
    );
    serveTraces({ r2: readBack("r2", "r1", "또", "r2의 출력"), r1: done("r1") });
    const user = await openChat("r1");

    await sendText(user, "또");

    await waitFor(() => {
      expect(screen.getAllByRole("region", { name: /^실행 \d+$/ })).toHaveLength(2);
    });
    await user.type(box("요청"), "다음");
    expect(button("보내기").disabled).toBe(true);
    hold.resolve(undefined);
    expect(await screen.findByText("r2의 출력")).toBeTruthy();
  });

  test("도는 실행은 읽기 3초 간격 그대로 두고 쓰는 글이 그 간격을 흔들지 않는다", async () => {
    const user = clock();
    const now = new Date().toISOString();
    const read = serveTraces({ r1: trace("r1", [started("r1", null, now)]) });
    signedIn();
    renderPage(<ConversationPage runId="r1" />);
    await screen.findByRole("progressbar", { name: "모델을 부르는 중" });

    // 한 글자씩 1초 간격으로 7초 동안 친다. 글을 칠 때마다 이 부품이 다시 그려져 타이머가 새로 걸리면 3초가 차지 않아 읽기가
    // 밀린다.
    for (const letter of "쓰는 중인 글") {
      await user.type(box("요청"), letter);
      await vi.advanceTimersByTimeAsync(1_000);
    }
    expect(button("보내기").disabled).toBe(true);

    await waitFor(() => {
      expect(read.count("r1")).toBeGreaterThanOrEqual(3);
    });
    // 글은 읽기로 지워지지 않았고 읽기도 3초마다 갔다.
    expect(read.count("r1")).toBeLessThanOrEqual(4);
    expect(box("요청").value).toBe("쓰는 중인 글");
  });

  test("일시정지한 대화는 입력 칸이 승인을 기다린다고 알리고 승인 묻기로 가는 링크가 선다", async () => {
    servePlugins([plugin("agent", "support-bot")]);
    serveTraces({ r1: trace("r1", [started("r1"), paused("r1", "mail.send")]) });
    const user = await openChat("r1");

    expect(await screen.findByText("승인을 기다린다:")).toBeTruthy();
    expect(screen.getByRole("link", { name: "승인 묻기로 가기" }).getAttribute("href")).toBe(
      "#approval",
    );
    await user.type(box("요청"), "먼저 보내 본다");
    expect(button("보내기").disabled).toBe(true);
    expect(screen.getByText("승인이나 거부를 먼저 고른다.")).toBeTruthy();
  });

  test("끝난 대화는 에이전트를 고르지도 꺼짐을 미리 알리지도 않아 플러그인 목록을 읽지 않는다", async () => {
    const reads = servePlugins(AGENTS);
    serveTraces({ r1: done("r1") });
    await openChat("r1");

    // 읽기가 있었다면 첫 그림이 서고 곧 요청이 나간다. 잠시 기다려도 나가지 않는다.
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(reads).toHaveLength(0);
  });

  test("승인을 기다리는 대화는 꺼짐을 미리 알리려고 플러그인 목록을 읽는다", async () => {
    const reads = servePlugins([plugin("agent", "support-bot")]);
    serveTraces({ r1: trace("r1", [started("r1"), paused("r1", "mail.send")]) });
    await openChat("r1");

    await waitFor(() => {
      expect(reads.length).toBeGreaterThan(0);
    });
  });

  test("멈출 때가 지난 결말 없는 대화는 이어 가지 못한다고 알린다", async () => {
    serveTraces({ r1: trace("r1", [started("r1"), llm("r1")]) });
    const user = await openChat("r1", { run_timeout_seconds: 120 });

    await user.type(box("요청"), "이어서");

    expect(button("보내기").disabled).toBe(true);
    expect(screen.getByText("결말 없는 실행은 이어 갈 수 없다.")).toBeTruthy();
  });

  test("이어 가기가 받아들여지지 않으면 제목과 메시지를 보이고 대화는 그대로다", async () => {
    servePost("/runs/r1/continuation", () =>
      HttpResponse.json(envelope("conflict", "끝난 실행에서만 이어 간다", "req-409"), {
        status: 409,
      }),
    );
    serveTraces({ r1: done("r1") });
    const user = await openChat("r1");

    await sendText(user, "이어서");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("요청을 보내지 못했다")).toBeTruthy();
    expect(within(alert).getByText("끝난 실행에서만 이어 간다")).toBeTruthy();
    expect(screen.getAllByRole("region", { name: /^실행 \d+$/ })).toHaveLength(1);
  });
});

describe("실패한 실행 다시 보내기", () => {
  test("앞 실행이 있으면 실패한 끝 실행의 요청을 그 앞 실행에서 다시 보낸다", async () => {
    const sent = servePost("/runs/r1/continuation", () =>
      stream([startedNow("r3", "r1", "r2의 요청", "support-bot"), finished("r3", "r3의 출력")]),
    );
    serveTraces({
      r3: readBack("r3", "r1", "r2의 요청", "r3의 출력"),
      r2: trace("r2", [started("r2", "r1"), failed("r2", "모델이 답하지 않았다")]),
      r1: done("r1"),
    });
    const user = await openChat("r2");
    await screen.findByText("모델이 답하지 않았다");
    expect(
      screen.getByText("실패한 실행은 이어 가지 못해, 보내면 그 앞의 실행에서 이어 간다."),
    ).toBeTruthy();

    await user.click(button("다시 보내기"));

    expect(await screen.findByText("r3의 출력")).toBeTruthy();
    expect(sent).toEqual([{ agent: "support-bot", request: "r2의 요청" }]);
    expect(location.pathname).toBe("/chat/r3");
  });

  test("앞 실행이 없으면 같은 에이전트로 새 대화를 시작한다", async () => {
    const sent = servePost("/runs", () =>
      stream([startedNow("r2", null, "r1의 요청", "support-bot"), finished("r2", "r2의 출력")]),
    );
    serveTraces({
      r2: readBack("r2", null, "r1의 요청", "r2의 출력"),
      r1: trace("r1", [started("r1"), failed("r1", "망했다")]),
    });
    const user = await openChat("r1");
    await screen.findByText("망했다");
    expect(
      screen.getByText("실패한 실행은 이어 가지 못해, 보내면 같은 에이전트로 새 대화를 시작한다."),
    ).toBeTruthy();

    await user.click(button("다시 보내기"));

    expect(await screen.findByText("r2의 출력")).toBeTruthy();
    expect(sent).toEqual([{ agent: "support-bot", request: "r1의 요청" }]);
  });

  test("실패한 대화에 새 요청을 쓰면 그 앞 실행에서 이어 간다", async () => {
    const sent = servePost("/runs/r1/continuation", () =>
      stream([startedNow("r3", "r1", "다른 요청", "support-bot"), finished("r3", "r3의 출력")]),
    );
    serveTraces({
      r3: readBack("r3", "r1", "다른 요청", "r3의 출력"),
      r2: trace("r2", [started("r2", "r1"), failed("r2", "망했다")]),
      r1: done("r1"),
    });
    const user = await openChat("r2");
    await screen.findByText("망했다");

    await sendText(user, "다른 요청");

    expect(await screen.findByText("r3의 출력")).toBeTruthy();
    expect(sent).toEqual([{ agent: "support-bot", request: "다른 요청" }]);
  });

  test("끝 실행이 아닌 앞 실행의 실패에는 다시 보내기가 없다", async () => {
    serveTraces({
      r2: done("r2", "r1"),
      r1: trace("r1", [started("r1"), failed("r1", "앞에서 망했다")]),
    });
    await openChat("r2");
    await screen.findByText("앞에서 망했다");

    expect(screen.queryByRole("button", { name: "다시 보내기" })).toBeNull();
  });
});

describe("최종 사용자의 대화", () => {
  test("끝난 대화는 읽기만 되고 입력 칸 대신 한 줄이 선다", async () => {
    serveTraces({
      r1: trace("r1", [
        started("r1", null, T0, { principal: END_USER }),
        finished("r1", "r1의 출력"),
      ]),
    });
    await openChat("r1");

    expect(screen.getByText(END_USER_LINE)).toBeTruthy();
    expect(screen.queryByRole("textbox", { name: "요청" })).toBeNull();
    expect(screen.queryByRole("button", { name: "보내기" })).toBeNull();
  });

  test("일시정지한 대화는 승인을 기다리는 중이라는 한 줄만 있고 결정 버튼이 없다", async () => {
    serveTraces({
      r1: trace("r1", [
        started("r1", null, T0, { principal: END_USER }),
        paused("r1", "mail.send"),
      ]),
    });
    await openChat("r1");

    expect(screen.getByText(/승인을 기다리는 중/)).toBeTruthy();
    expect(screen.getByText(END_USER_LINE)).toBeTruthy();
    expect(screen.queryByRole("region", { name: "승인 묻기" })).toBeNull();
    expect(screen.queryByRole("button", { name: /^(승인|거부)$/ })).toBeNull();
  });

  test("실패한 대화에도 다시 보내기가 없다", async () => {
    serveTraces({
      r1: trace("r1", [started("r1", null, T0, { principal: END_USER }), failed("r1", "망했다")]),
    });
    await openChat("r1");
    await screen.findByText("망했다");

    expect(screen.queryByRole("button", { name: "다시 보내기" })).toBeNull();
    expect(screen.getByText(END_USER_LINE)).toBeTruthy();
  });

  test("운영자의 대화에는 그 한 줄이 없다", async () => {
    serveTraces({ r1: done("r1") });
    await openChat("r1");

    expect(screen.queryByText(END_USER_LINE)).toBeNull();
  });

  test("주체는 첫 실행으로 가려서 끝 실행이 운영자의 것이어도 최종 사용자의 대화는 읽기만 된다", async () => {
    serveTraces({
      r2: done("r2", "r1"),
      r1: trace("r1", [
        started("r1", null, T0, { principal: END_USER }),
        finished("r1", "r1의 출력"),
      ]),
    });
    await openChat("r2");

    expect(screen.getByText(END_USER_LINE)).toBeTruthy();
    expect(screen.queryByRole("textbox", { name: "요청" })).toBeNull();
  });
});

describe("승인 묻기", () => {
  const FIRST = { a: 2, b: 3 };
  const SECOND = { a: 4, b: 5 };

  /** 일시정지. 결정의 자리는 그 이벤트가 트레이스에서 선 차례다. */
  const pausedWith = (args: Record<string, number>): TraceEvent => ({
    type: "run_paused",
    run_id: "r1",
    ts: T0,
    tool: "add",
    args,
    rule: null,
    server: null,
  });
  const added = (args: Record<string, number>, content: string): TraceEvent =>
    toolCalled("r1", "add", "ok", T0, { args, content });
  const BEGIN = [started("r1", null, T0, { agent: "calc" }), llm("r1")];
  /** 시작(0), 모델(1), 첫 일시정지(2). */
  const PAUSED = trace("r1", [...BEGIN, pausedWith(FIRST)]);
  /** 첫 결정(3), 재개(4), 도구(5), 끝(6). */
  const FINISH_TAIL = [
    granted("r1", null),
    resumed("r1"),
    added(FIRST, "5"),
    finished("r1", "5/9"),
  ];
  const DONE = trace("r1", [...PAUSED.events, ...FINISH_TAIL]);
  /** 첫 결정(3), 재개(4), 도구(5), 둘째 일시정지(6). */
  const REPAUSE_TAIL = [granted("r1", null), resumed("r1"), added(FIRST, "5"), pausedWith(SECOND)];
  const REPAUSED = trace("r1", [...PAUSED.events, ...REPAUSE_TAIL]);

  const CALC_ROWS: PluginRow[] = [
    plugin("agent", "calc", { mcp: ["fixture"], requires: ["add"] }),
    plugin("mcp", "fixture"),
  ];

  function region(): HTMLElement {
    return screen.getByRole("region", { name: "승인 묻기" });
  }

  async function openAsk(): Promise<UserEvent> {
    const user = userEvent.setup();
    signedIn();
    renderPage(<ConversationPage runId="r1" />);
    await screen.findByRole("region", { name: "승인 묻기" });
    return user;
  }

  test("멈춘 대화에는 승인 묻기가 서고 무엇을 승인하는지 도구와 인자가 글자 그대로 보인다", async () => {
    serveTraces({ r1: PAUSED });
    servePlugins(CALC_ROWS);

    await openAsk();

    expect(within(region()).getByText("add")).toBeTruthy();
    expect(region().textContent).toContain(JSON.stringify(FIRST, null, 2));
    expect(
      within(region())
        .getAllByRole("button")
        .map((control) => control.textContent),
    ).toEqual(["거부", "승인"]);
  });

  test("승인은 판별자와 트레이스에서 읽은 일시정지의 자리를 보낸다", async () => {
    serveTraces({ r1: (call) => (call === 0 ? PAUSED : DONE) });
    servePlugins(CALC_ROWS);
    const sent = servePost("/runs/r1/approval", () => stream(FINISH_TAIL));
    const user = await openAsk();

    await user.click(button("승인"));

    expect(await screen.findByText("5/9")).toBeTruthy();
    expect(sent).toEqual([{ decision: "approve", pause_index: 2 }]);
    expect(screen.getByText(/operator가 .*에 승인했다/)).toBeTruthy();
    expect(screen.queryByRole("region", { name: "승인 묻기" })).toBeNull();
  });

  test("거부는 사유가 비어 있거나 공백뿐이면 보낼 수 없다", async () => {
    serveTraces({ r1: PAUSED });
    servePlugins(CALC_ROWS);
    const sent = servePost("/runs/r1/approval", () => stream(FINISH_TAIL));
    const user = await openAsk();

    expect(button("거부").disabled).toBe(true);
    await user.type(box("거부 사유"), "   ");
    await user.click(button("거부"));

    expect(button("거부").disabled).toBe(true);
    expect(sent).toEqual([]);
  });

  test("거부는 적은 사유를 다듬어 판별자와 자리와 함께 보낸다", async () => {
    serveTraces({ r1: (call) => (call === 0 ? PAUSED : DONE) });
    servePlugins(CALC_ROWS);
    const sent = servePost("/runs/r1/approval", () => stream(FINISH_TAIL));
    const user = await openAsk();

    await user.type(box("거부 사유"), "  인자가 틀렸다 ");
    await user.click(button("거부"));

    await waitFor(() => {
      expect(sent).toHaveLength(1);
    });
    expect(sent[0]).toEqual({ decision: "deny", pause_index: 2, reason: "인자가 틀렸다" });
  });

  test("거부가 422 를 받으면 승인 묻기 안의 알림에 메시지와 추적 식별자와 위반을 모두 보이고 사유 칸이 사유의 위반을 받는다", async () => {
    serveTraces({ r1: PAUSED });
    servePlugins(CALC_ROWS);
    servePost("/runs/r1/approval", () =>
      HttpResponse.json(
        {
          ...envelope("invalid_request", "요청의 형식이 올바르지 않다", "req-4220"),
          violations: [
            { field: "body.deny.reason", message: "사유는 비어 있을 수 없다" },
            { field: "body.pause_index", message: "음수일 수 없다" },
          ],
        },
        { status: 422 },
      ),
    );
    const user = await openAsk();

    await user.type(box("거부 사유"), "틀렸다");
    await user.click(button("거부"));

    const alert = await within(region()).findByRole("alert");
    expect(within(alert).getByText("결정을 보내지 못했다")).toBeTruthy();
    expect(within(alert).getByText("요청의 형식이 올바르지 않다")).toBeTruthy();
    expect(within(alert).getByText("req-4220")).toBeTruthy();
    expect(within(alert).getByText("body.pause_index")).toBeTruthy();
    expect(box("거부 사유").getAttribute("aria-invalid")).toBe("true");
    // 422 는 승인 묻기 안에만 서고 대화 아래의 알림에는 서지 않는다.
    expect(screen.getAllByText("결정을 보내지 못했다")).toHaveLength(1);
  });

  test("422 의 위반이 사유에 걸리지 않으면 사유 칸은 오류 상태가 아니다", async () => {
    serveTraces({ r1: PAUSED });
    servePlugins(CALC_ROWS);
    servePost("/runs/r1/approval", () =>
      HttpResponse.json(
        {
          ...envelope("invalid_request", "형식 오류", "req-4221"),
          violations: [{ field: "body.pause_index", message: "음수일 수 없다" }],
        },
        { status: 422 },
      ),
    );
    const user = await openAsk();

    await user.click(button("승인"));

    expect(await within(region()).findByText("body.pause_index")).toBeTruthy();
    expect(box("거부 사유").getAttribute("aria-invalid")).not.toBe("true");
  });

  test("결정을 보내는 동안 버튼이 막히고 재개된 이벤트가 받는 대로 대화에 붙는다", async () => {
    const hold = Promise.withResolvers<undefined>();
    const afterGrant = Promise.withResolvers<undefined>();
    const read = serveTraces({ r1: (call) => (call === 0 ? PAUSED : DONE) });
    servePlugins(CALC_ROWS);
    servePost("/runs/r1/approval", () =>
      stream([
        hold.promise,
        granted("r1", null),
        KEEPALIVE,
        resumed("r1"),
        afterGrant.promise,
        added(FIRST, "5"),
        finished("r1", "5/9"),
      ]),
    );
    const user = await openAsk();

    await user.click(button("승인"));

    expect(button("승인").disabled).toBe(true);
    expect(button("거부").disabled).toBe(true);
    hold.resolve(undefined);
    // 스트림이 닫히기 전에 받은 이벤트가 먼저 보이고, 트레이스는 아직 다시 읽지 않았다.
    expect(await screen.findByText(/operator가 .*에 승인했다/)).toBeTruthy();
    expect(read.count("r1")).toBe(1);
    expect(screen.queryByText("5/9")).toBeNull();
    afterGrant.resolve(undefined);

    expect(await screen.findByText("5/9")).toBeTruthy();
    expect(read.count("r1")).toBe(2);
    expect(screen.queryByText(/응답 스트림이 끊겼다/)).toBeNull();
  });

  test("응답 스트림이 결말 없이 끊겨도 결정을 다시 보내지 않고 트레이스를 다시 읽으며 끊겼다고 말한다", async () => {
    const partial = trace("r1", [...PAUSED.events, granted("r1", null), resumed("r1")]);
    const read = serveTraces({ r1: (call) => (call === 0 ? PAUSED : partial) });
    servePlugins(CALC_ROWS);
    const sent = servePost("/runs/r1/approval", () =>
      stream([granted("r1", null), resumed("r1"), KEEPALIVE]),
    );
    const user = await openAsk();

    await user.click(button("승인"));

    expect(await screen.findByText("응답 스트림이 끊겼다. 실행은 서버에서 계속된다")).toBeTruthy();
    expect(screen.getByText(/창을 닫거나 떠나도 실행은 끝까지 간다/)).toBeTruthy();
    await waitFor(() => {
      expect(read.count("r1")).toBe(2);
    });
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(sent).toHaveLength(1);
  });

  test("끊긴 뒤 다시 읽은 실행이 아직 도는 중이면 3초마다 이어 읽어 결말을 그린다", async () => {
    const user = clock();
    const now = new Date().toISOString();
    const live = (events: readonly TraceEvent[]): Trace =>
      trace(
        "r1",
        events.map((event) => ({ ...event, ts: now })),
      );
    const partial = live([...PAUSED.events, granted("r1", null), resumed("r1")]);
    const complete = live(DONE.events);
    const read = serveTraces({
      r1: (call) => (call === 0 ? live(PAUSED.events) : call === 1 ? partial : complete),
    });
    servePlugins(CALC_ROWS);
    servePost("/runs/r1/approval", () => stream([granted("r1", null), resumed("r1")]));
    signedIn();
    renderPage(<ConversationPage runId="r1" />);
    await screen.findByRole("region", { name: "승인 묻기" });

    await user.click(button("승인"));
    await screen.findByText("응답 스트림이 끊겼다. 실행은 서버에서 계속된다");
    await vi.advanceTimersByTimeAsync(3_100);

    expect(await screen.findByText("5/9")).toBeTruthy();
    expect(read.count("r1")).toBeGreaterThanOrEqual(3);
  });

  test("다시 읽은 트레이스가 새 일시정지에서 끝나면 새 자리로 승인 묻기가 다시 서고 앞 사유는 남지 않는다", async () => {
    const second = trace("r1", [
      ...REPAUSED.events,
      granted("r1", null),
      resumed("r1"),
      added(SECOND, "9"),
      finished("r1", "5/9"),
    ]);
    serveTraces({ r1: (call) => [PAUSED, REPAUSED][call] ?? second });
    servePlugins(CALC_ROWS);
    const sent = servePost("/runs/r1/approval", (call) =>
      call === 0
        ? stream(REPAUSE_TAIL)
        : stream([granted("r1", null), resumed("r1"), added(SECOND, "9"), finished("r1", "5/9")]),
    );
    const user = await openAsk();
    await user.type(box("거부 사유"), "앞 일시정지의 사유");

    await user.click(button("승인"));

    await waitFor(() => {
      expect(region().textContent).toContain(JSON.stringify(SECOND, null, 2));
    });
    await waitFor(() => {
      expect(button("승인").disabled).toBe(false);
    });
    // 다시 멈춘 것은 결말이다. 끊긴 것이 아니다.
    expect(screen.queryByText(/응답 스트림이 끊겼다/)).toBeNull();
    expect(box("거부 사유").value).toBe("");
    await user.click(button("승인"));
    expect(await screen.findByText("5/9")).toBeTruthy();
    expect(sent).toEqual([
      { decision: "approve", pause_index: 2 },
      { decision: "approve", pause_index: 6 },
    ]);
  });

  test("떠난 화면의 결정은 스트림이 끝나도 트레이스를 다시 읽지 않는다", async () => {
    const hold = Promise.withResolvers<undefined>();
    const read = serveTraces({ r1: PAUSED });
    servePlugins(CALC_ROWS);
    servePost("/runs/r1/approval", () =>
      stream([granted("r1", null), hold.promise, resumed("r1")]),
    );
    const user = userEvent.setup();
    signedIn();
    const view = renderPage(<ConversationPage runId="r1" />);
    await screen.findByRole("region", { name: "승인 묻기" });
    await user.click(button("승인"));
    await screen.findByText(/operator가 .*에 승인했다/);

    view.unmount();
    hold.resolve(undefined);
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(read.count("r1")).toBe(1);
  });

  test("409 면 봉투의 메시지를 보이고 트레이스와 플러그인 목록을 다시 읽어 지금의 일시정지를 보인다", async () => {
    const read = serveTraces({ r1: (call) => (call === 0 ? PAUSED : REPAUSED) });
    const plugins = servePlugins(CALC_ROWS);
    servePost("/runs/r1/approval", () =>
      HttpResponse.json(envelope("conflict", "그 일시정지는 이미 결정됐다", "req-409"), {
        status: 409,
      }),
    );
    const user = await openAsk();

    await user.click(button("승인"));

    expect(await screen.findByText("그 일시정지는 이미 결정됐다")).toBeTruthy();
    expect(screen.getByText("req-409")).toBeTruthy();
    await waitFor(() => {
      expect(read.count("r1")).toBe(2);
    });
    expect(plugins.length).toBeGreaterThanOrEqual(2);
    expect(region().textContent).toContain(JSON.stringify(SECOND, null, 2));
  });

  test("409 뒤 다시 읽은 대화가 일시정지가 아니어서 승인 묻기가 걷혀도 알림은 남는다", async () => {
    serveTraces({ r1: (call) => (call === 0 ? PAUSED : DONE) });
    servePlugins(CALC_ROWS);
    servePost("/runs/r1/approval", () =>
      HttpResponse.json(envelope("conflict", "일시정지가 아니다", "req-409"), { status: 409 }),
    );
    const user = await openAsk();

    await user.click(button("승인"));

    expect(await screen.findByText("일시정지가 아니다")).toBeTruthy();
    await waitFor(() => {
      expect(screen.queryByRole("region", { name: "승인 묻기" })).toBeNull();
    });
    expect(screen.getByText("일시정지가 아니다")).toBeTruthy();
  });

  test("결정이 401 을 받고 갱신이 서버 오류로 실패하면 로그인 화면으로 가지 않고 결정을 보내지 못했다고 말한다", async () => {
    serveTraces({ r1: PAUSED });
    servePlugins(CALC_ROWS);
    servePost("/runs/r1/approval", () =>
      HttpResponse.json(envelope("unauthorized", "로그인이 필요하다", "req-401"), { status: 401 }),
    );
    network.use(
      http.post(api("/auth/refresh"), () =>
        HttpResponse.json(envelope("internal_error", "갱신 실패"), { status: 500 }),
      ),
    );
    const user = await openAsk();

    await user.click(button("승인"));

    expect(await screen.findByText("결정을 보내지 못했다")).toBeTruthy();
    expect(screen.getByText("로그인이 필요하다")).toBeTruthy();
    expect(visited()).toEqual([]);
  });

  describe("꺼진 플러그인", () => {
    test("에이전트가 꺼졌으면 버튼이 막히고 꺼진 에이전트가 보인다", async () => {
      serveTraces({ r1: PAUSED });
      servePlugins([
        plugin("agent", "calc", { enabled: false, mcp: ["fixture"] }),
        plugin("mcp", "fixture"),
      ]);

      await openAsk();

      expect(screen.getByText("꺼진 플러그인이 있어 재개할 수 없다: 에이전트 calc")).toBeTruthy();
      expect(button("승인").disabled).toBe(true);
      expect(button("거부").disabled).toBe(true);
      expect(box("거부 사유").disabled).toBe(true);
    });

    test("에이전트가 쓰는 MCP 가 꺼졌으면 꺼진 MCP 가 보인다", async () => {
      serveTraces({ r1: PAUSED });
      servePlugins([
        plugin("agent", "calc", { mcp: ["fixture"] }),
        plugin("mcp", "fixture", { enabled: false }),
      ]);

      await openAsk();

      expect(screen.getByText("꺼진 플러그인이 있어 재개할 수 없다: MCP fixture")).toBeTruthy();
      expect(button("승인").disabled).toBe(true);
    });

    test("켜진 것만 있으면 알림이 없고 버튼이 열려 있다", async () => {
      serveTraces({ r1: PAUSED });
      servePlugins(CALC_ROWS);

      await openAsk();

      expect(screen.queryByText(/꺼진 플러그인이 있어/)).toBeNull();
      expect(button("승인").disabled).toBe(false);
    });

    test("플러그인 목록을 읽지 못하면 미리 알 수 없다고 말하고 버튼을 막지 않는다", async () => {
      serveTraces({ r1: PAUSED });
      servePlugins(HttpResponse.json(envelope("internal_error", "서버가 쉰다"), { status: 500 }));

      await openAsk();

      expect(
        await screen.findByText("플러그인 목록을 읽지 못해 꺼진 플러그인을 미리 알 수 없다"),
      ).toBeTruthy();
      expect(button("승인").disabled).toBe(false);
    });
  });
});

describe("스트림이 열린 동안의 로그인 갱신", () => {
  /** 보내기를 걸고 스트림을 잡아 둔다. 시작 이벤트가 온 뒤라 주소는 `/chat/r9` 다. */
  async function openStream(): Promise<{ release: () => void }> {
    const user = clock();
    const hold = Promise.withResolvers<undefined>();
    servePlugins(AGENTS);
    servePost("/runs", () =>
      stream([startedNow("r9", null, "안녕", "echo"), hold.promise, finished("r9", "끝")]),
    );
    serveTraces({ r9: readBack("r9", null, "안녕", "끝") });
    signedIn({ token_minutes: 5 });
    renderPage(<ConversationPage runId={null} />);
    await screen.findByRole("combobox", { name: "에이전트" });
    await sendText(user, "안녕");
    await waitFor(() => {
      expect(location.pathname).toBe("/chat/r9");
    });
    return {
      release: () => {
        hold.resolve(undefined);
      },
    };
  }

  function serveRefresh(status: 204 | 401): { count: () => number } {
    let count = 0;
    network.use(
      http.post(api("/auth/refresh"), () => {
        count += 1;
        return status === 204
          ? new HttpResponse(null, { status })
          : HttpResponse.json(envelope("unauthorized", "로그인이 끝났다"), { status });
      }),
    );
    return { count: () => count };
  }

  test("짧은 JWT 수명의 80% 가 지나면 갱신을 부르고 스트림이 닫히면 더 부르지 않는다", async () => {
    const refreshes = serveRefresh(204);
    const { release } = await openStream();

    await vi.advanceTimersByTimeAsync(230_000);
    expect(refreshes.count()).toBe(0);
    await vi.advanceTimersByTimeAsync(20_000);
    expect(refreshes.count()).toBe(1);

    release();
    expect(await screen.findByText("끝")).toBeTruthy();
    await vi.advanceTimersByTimeAsync(20 * 60_000);

    expect(refreshes.count()).toBe(1);
    expect(visited()).toEqual([]);
  });

  test("갱신이 401 이면 지금 대화의 주소를 싣고 만료 알림과 함께 로그인 화면으로 간다", async () => {
    serveRefresh(401);
    const { release } = await openStream();

    await vi.advanceTimersByTimeAsync(250_000);

    await waitFor(() => {
      expect(visited()).toHaveLength(1);
    });
    const target = visited()[0] ?? "";
    expect(target).toMatch(/^\/login\?/);
    expect(target).toContain("notice=expired");
    expect(decodeURIComponent(target)).toContain("next=/chat/r9");
    release();
  });

  test("갱신이 서버 오류로 실패하면 로그인이 끝났는지 모르므로 로그인 화면으로 가지 않는다", async () => {
    network.use(
      http.post(api("/auth/refresh"), () =>
        HttpResponse.json(envelope("internal_error", "갱신 실패"), { status: 500 }),
      ),
    );
    const { release } = await openStream();

    await vi.advanceTimersByTimeAsync(250_000);

    expect(visited()).toEqual([]);
    release();
  });

  test("스트림이 열려 있지 않으면 시간이 지나도 갱신을 부르지 않는다", async () => {
    const refreshes = serveRefresh(204);
    serveTraces({ r1: done("r1") });
    clock();
    signedIn({ token_minutes: 5 });
    renderPage(<ConversationPage runId="r1" />);
    await screen.findByText("r1의 출력");

    await vi.advanceTimersByTimeAsync(20 * 60_000);

    expect(refreshes.count()).toBe(0);
  });
});
