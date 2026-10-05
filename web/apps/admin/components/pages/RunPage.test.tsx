// 실행 하나. 운영자가 실행 하나를 열어 이벤트를 쓴 순서대로 전부, 들어온 모양 그대로 글자로 본다(web-admin 티켓 07).
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 실행 식별자는 라우트가 페이지에 넘기는 주소의 조각
// 그대로 준다. 트레이스는 바깥에서 온 텍스트를 싣는다. 그것이 요소로 그려지지 않는 것을 문서에서 본다(ADR 0019).

import { screen, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";
import { api, envelope, network, type Trace } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { acceptTokens, enterAdminToken } from "../../testing/token";
import { RunPage } from "./RunPage";

const TOKEN = "adm-9Jm3-run-page-token";
const RUN = "r-calc";
const TS = "2026-09-30T09:00:00+00:00";

const TOOL_CALLS = [{ id: "call-1", name: "add", args: { a: 1, b: 2 } }];
const UNKNOWN_RAW = '{"type":"future_kind","run_id":"r-calc","ts":"2026-09-30T09:00:04+00:00"}';

const TRACE: Trace = {
  run_id: RUN,
  schema_version: "2",
  events: [
    {
      type: "run_started",
      run_id: RUN,
      ts: TS,
      agent: "calc",
      request: "1 더하기 2",
      principal: "operator",
      previous_run: null,
    },
    {
      type: "llm_called",
      run_id: RUN,
      ts: TS,
      model: "claude-sonnet-5",
      input_tokens: 12,
      output_tokens: 7,
      prompt: "첫 줄\n  둘째 줄은 들여 썼다",
      text: "",
      tool_calls: TOOL_CALLS,
    },
    {
      type: "tool_called",
      run_id: RUN,
      ts: TS,
      tool: "add",
      ok: true,
      args: { a: 1, b: 2 },
      content: "3",
    },
    {
      type: "tool_called",
      run_id: RUN,
      ts: TS,
      tool: "login",
      ok: false,
      args: { user: "ops", password: "***" },
      content: "인증에 실패했다",
    },
    { type: "unknown", raw: UNKNOWN_RAW },
    { type: "run_finished", run_id: RUN, ts: TS, output: "3" },
  ],
};

// 이어 간 실행. 앞 실행과 요약이 덮는 끝의 식별자에 띄어쓰기·빗금·한글을 두어 링크의 주소가 인코딩되는 것을 잰다.
const CONTINUED = "r-calc-3";
const PREVIOUS = "r calc/둘";
const COVERED = "r calc/하나";
const SUMMARY = "2+3 묻자 5 답함(실행 r calc/하나).";
const CONTINUED_TRACE: Trace = {
  run_id: CONTINUED,
  schema_version: "3",
  events: [
    {
      type: "run_started",
      run_id: CONTINUED,
      ts: TS,
      agent: "calc",
      request: "거기에 4를 더하면",
      principal: "operator",
      previous_run: PREVIOUS,
    },
    {
      type: "conversation_summarized",
      run_id: CONTINUED,
      ts: TS,
      summary: SUMMARY,
      last_covered_run: COVERED,
      model: "claude-sonnet-5",
      input_tokens: 543,
      output_tokens: 38,
    },
    { type: "run_finished", run_id: CONTINUED, ts: TS, output: "9" },
  ],
};

/**
 * `GET /traces/{run_id}` 하나에 답한다. `reply` 는 몇 번째 요청인지(0부터) 받는다. 요청마다의 `Authorization` 을
 * 쌓아 돌려준다.
 */
function serveTrace(path: string, reply: (call: number) => Response | Promise<Response>): string[] {
  const authorizations: string[] = [];
  network.use(
    http.get(api(path), ({ request }) => {
      authorizations.push(request.headers.get("Authorization") ?? "(없음)");
      return reply(authorizations.length - 1);
    }),
  );
  return authorizations;
}

/** 실행 하나를 열고 관리 토큰을 넣는다. 이어서 누를 사용자를 돌려준다. */
async function openRun(runId: string): Promise<UserEvent> {
  const user = userEvent.setup();
  acceptTokens();
  renderPage(<RunPage runId={runId} />);
  await enterAdminToken(user, TOKEN);
  return user;
}

function events(): HTMLElement {
  return screen.getByRole("region", { name: "이벤트" });
}

/** 이벤트 항목 전부. 쓴 순서대로다. */
function eventItems(): HTMLElement[] {
  return within(events()).getAllByRole("listitem");
}

function eventItem(index: number): HTMLElement {
  const found = eventItems()[index];
  if (found === undefined) {
    throw new Error(`${String(index)}번째 이벤트가 없다`);
  }
  return found;
}

describe("실행 하나", () => {
  test("목록을 거치지 않고 곧장 열어도 그 실행의 트레이스 하나만 읽어 선다", async () => {
    // 처리하지 않은 요청(목록 GET /traces 같은)은 setup.ts 가 테스트를 빨갛게 한다.
    const authorizations = serveTrace(`/traces/${RUN}`, () => HttpResponse.json(TRACE));

    await openRun(RUN);

    expect(await screen.findByRole("region", { name: "이벤트" })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 2, name: RUN })).toBeTruthy();
    expect(authorizations).toEqual([`Bearer ${TOKEN}`]);
  });

  test("이벤트가 쓴 순서대로 전부 보인다", async () => {
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json(TRACE));

    await openRun(RUN);

    await screen.findByRole("region", { name: "이벤트" });
    expect(
      within(events())
        .getAllByRole("heading", { level: 4 })
        .map((heading) => heading.textContent),
    ).toEqual([
      "run_started",
      "llm_called",
      "tool_called",
      "tool_called",
      "모르는 종류",
      "run_finished",
    ]);
  });

  test("종류별 필드가 들어온 모양 그대로 글자로 보인다", async () => {
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json(TRACE));

    await openRun(RUN);

    await screen.findByRole("region", { name: "이벤트" });
    const started = eventItem(0).textContent;
    expect(started).toContain("request");
    expect(started).toContain("1 더하기 2");
    expect(started).toContain("principal");
    expect(started).toContain("operator");
    // 여러 줄의 프롬프트는 줄바꿈과 들여쓰기가 그대로다.
    expect(eventItem(1).textContent).toContain("첫 줄\n  둘째 줄은 들여 썼다");
    expect(eventItem(1).textContent).toContain("claude-sonnet-5");
    expect(eventItem(3).textContent).toContain("인증에 실패했다");
    expect(eventItem(3).textContent).toContain("false");
    expect(eventItem(5).textContent).toContain("output");
  });

  test("필드의 이름은 용어집의 말과 계약의 이름을 함께 보인다", async () => {
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json(TRACE));

    await openRun(RUN);

    await screen.findByRole("region", { name: "이벤트" });
    const names = (index: number): (string | null)[] =>
      within(eventItem(index))
        .getAllByRole("term")
        .map((term) => term.textContent);
    expect(names(0)).toEqual([
      "시각 ts",
      "에이전트 agent",
      "요청 request",
      "주체 principal",
      "앞 실행 previous_run",
    ]);
    expect(names(3)).toEqual(["시각 ts", "도구 tool", "성공 ok", "인자 args", "결과 내용 content"]);
    expect(names(4)).toEqual(["원문 raw"]);
  });

  test("앞 실행과 요약이 덮는 끝은 그 실행의 상세로 가는 링크이고 주소는 인코딩한 식별자다", async () => {
    serveTrace(`/traces/${CONTINUED}`, () => HttpResponse.json(CONTINUED_TRACE));

    await openRun(CONTINUED);

    await screen.findByRole("region", { name: "이벤트" });
    const previous = within(eventItem(0)).getByRole("link", { name: PREVIOUS });
    expect(previous.getAttribute("href")).toBe(`/runs/${encodeURIComponent(PREVIOUS)}`);
    expect(previous.getAttribute("href")).toBe("/runs/r%20calc%2F%EB%91%98");
    const covered = within(eventItem(1)).getByRole("link", { name: COVERED });
    expect(covered.getAttribute("href")).toBe("/runs/r%20calc%2F%ED%95%98%EB%82%98");
    // 링크는 실행 식별자 필드 둘뿐이다. 요약 글에 든 식별자는 글자다.
    expect(within(events()).getAllByRole("link")).toHaveLength(2);
  });

  test("이어 가지 않은 실행의 앞 실행은 링크가 아니라 글자다", async () => {
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json(TRACE));

    await openRun(RUN);

    await screen.findByRole("region", { name: "이벤트" });
    expect(within(events()).queryByRole("link")).toBeNull();
    expect(eventItem(0).textContent).toContain("null");
  });

  test.each([".", ".."])(
    "앞 실행이 %s 이면 주소가 /runs/ 밖으로 풀리므로 링크가 아니라 글자다",
    async (dot) => {
      const [started, ...rest] = TRACE.events;
      if (started?.type !== "run_started") {
        throw new Error("첫 이벤트가 시작 이벤트가 아니다");
      }
      serveTrace(`/traces/${RUN}`, () =>
        HttpResponse.json({ ...TRACE, events: [{ ...started, previous_run: dot }, ...rest] }),
      );

      await openRun(RUN);

      await screen.findByRole("region", { name: "이벤트" });
      expect(within(events()).queryByRole("link")).toBeNull();
      expect(eventItem(0).textContent).toContain(`previous_run${dot}`);
    },
  );

  test("요약 이벤트의 필드는 용어집의 말과 계약의 이름을 함께 보이고 글과 토큰 수는 글자다", async () => {
    serveTrace(`/traces/${CONTINUED}`, () => HttpResponse.json(CONTINUED_TRACE));

    await openRun(CONTINUED);

    await screen.findByRole("region", { name: "이벤트" });
    expect(
      within(eventItem(1))
        .getAllByRole("term")
        .map((term) => term.textContent),
    ).toEqual([
      "시각 ts",
      "요약 글 summary",
      "덮는 끝 last_covered_run",
      "모델 model",
      "입력 토큰 수 input_tokens",
      "응답 토큰 수 output_tokens",
    ]);
    const shown = eventItem(1).textContent;
    expect(shown).toContain(SUMMARY);
    expect(shown).toContain("543");
    expect(shown).toContain("38");
  });

  test("인자와 도구 호출 같은 JSON 값은 들여 적은 글자로 보인다", async () => {
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json(TRACE));

    await openRun(RUN);

    await screen.findByRole("region", { name: "이벤트" });
    expect(eventItem(1).textContent).toContain(JSON.stringify(TOOL_CALLS, null, 2));
    expect(eventItem(2).textContent).toContain(JSON.stringify({ a: 1, b: 2 }, null, 2));
  });

  test("마스킹된 인자는 *** 로 보인다", async () => {
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json(TRACE));

    await openRun(RUN);

    await screen.findByRole("region", { name: "이벤트" });
    expect(eventItem(3).textContent).toContain('"password": "***"');
  });

  test("모르는 종류의 이벤트는 원문 문자열을 그대로 보인다", async () => {
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json(TRACE));

    await openRun(RUN);

    await screen.findByRole("region", { name: "이벤트" });
    expect(eventItem(4).textContent).toContain(UNKNOWN_RAW);
  });

  test("형식 1 트레이스는 읽을 수 있지만 재개할 수 없다고 말한다", async () => {
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json({ ...TRACE, schema_version: "1" }));

    await openRun(RUN);

    await screen.findByRole("region", { name: "이벤트" });
    expect(screen.getByText(/읽을 수 있지만 재개할 수 없다/)).toBeTruthy();
  });

  test.each(["2", "3"] as const)(
    "형식 %s 트레이스에는 재개할 수 없다는 말이 없다",
    async (version) => {
      serveTrace(`/traces/${RUN}`, () => HttpResponse.json({ ...TRACE, schema_version: version }));

      await openRun(RUN);

      await screen.findByRole("region", { name: "이벤트" });
      expect(screen.queryByText(/재개할 수 없다/)).toBeNull();
    },
  );

  test("트레이스에 든 HTML 은 글자 그대로 보이고 요소로 그려지지 않는다", async () => {
    const image = '<img src=x onerror="window.__agentOsXss = true">';
    const script = "<script>window.__agentOsXss = true</script>";
    const link = '<a href="javascript:window.__agentOsXss = true">눌러</a>';
    const bold = '{"type":"<b>굵게</b>"}';
    // 앞 실행의 값은 링크의 href 에 든다. 인코딩되어 `/runs/` 아래의 조각으로만 남아야 한다.
    const previous = "javascript:window.__agentOsXss = true/../../plugins?x#y";
    const hostile: Trace = {
      run_id: RUN,
      schema_version: "3",
      events: [
        {
          type: "run_started",
          run_id: RUN,
          ts: TS,
          agent: "calc",
          request: script,
          principal: "operator",
          previous_run: previous,
        },
        {
          type: "llm_called",
          run_id: RUN,
          ts: TS,
          model: "claude-sonnet-5",
          input_tokens: 1,
          output_tokens: 1,
          prompt: link,
          text: "",
          tool_calls: [],
        },
        {
          type: "tool_called",
          run_id: RUN,
          ts: TS,
          tool: "fetch",
          ok: true,
          args: {},
          content: image,
        },
        { type: "unknown", raw: bold },
      ],
    };
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json(hostile));

    await openRun(RUN);

    await screen.findByRole("region", { name: "이벤트" });
    const shown = events().textContent;
    for (const text of [image, script, link, bold, previous]) {
      expect(shown).toContain(text);
    }
    expect(document.querySelector("img")).toBeNull();
    expect(document.body.querySelector("script")).toBeNull();
    expect(document.querySelector("b")).toBeNull();
    expect(document.querySelector('a[href^="javascript"]')).toBeNull();
    expect(within(events()).getByRole("link", { name: previous }).getAttribute("href")).toBe(
      "/runs/javascript%3Awindow.__agentOsXss%20%3D%20true%2F..%2F..%2Fplugins%3Fx%23y",
    );
    expect(Reflect.has(window, "__agentOsXss")).toBe(false);
  });

  test("없는 실행을 열면 404 봉투의 메시지와 추적 식별자가 보인다", async () => {
    serveTrace("/traces/r-ghost", () =>
      HttpResponse.json(envelope("not_found", "r-ghost 실행의 트레이스가 없다", "req-40a1"), {
        status: 404,
      }),
    );

    await openRun("r-ghost");

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("r-ghost 실행의 트레이스가 없다");
    expect(alert.textContent).toContain("req-40a1");
  });

  test("읽을 수 없는 트레이스를 열면 500 봉투의 메시지와 추적 식별자가 보인다", async () => {
    const message = "트레이스를 읽을 수 없다: C:/root/traces/r-broken.jsonl 1번째 줄";
    serveTrace("/traces/r-broken", () =>
      HttpResponse.json(envelope("internal_error", message, "req-5c02"), { status: 500 }),
    );

    await openRun("r-broken");

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain(message);
    expect(alert.textContent).toContain("req-5c02");
    expect(screen.queryByRole("region", { name: "이벤트" })).toBeNull();
  });

  test("트레이스를 읽다 401 을 받으면 관리 토큰을 지우고 입력 화면으로 돌아가 거부됐다고 말한다", async () => {
    serveTrace(`/traces/${RUN}`, () =>
      HttpResponse.json(envelope("unauthorized", "토큰이 없거나 틀리다"), { status: 401 }),
    );

    await openRun(RUN);

    expect((await screen.findByRole("alert")).textContent).toContain("관리 토큰이 거부됐다");
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
  });

  test("지운 토큰의 늦은 401 은 그 사이 넣은 새 토큰의 트레이스에 섞이지 않고 새 토큰을 내려놓지 않는다", async () => {
    const old = "adm-old-token-cleared";
    const late = Promise.withResolvers<Response>();
    acceptTokens();
    const authorizations = serveTrace(`/traces/${RUN}`, (call) =>
      call === 0 ? late.promise : HttpResponse.json(TRACE),
    );
    const user = userEvent.setup();
    renderPage(<RunPage runId={RUN} />);
    // 옛 토큰의 요청(0)은 응답을 기다린다.
    await enterAdminToken(user, old);
    await user.click(await screen.findByRole("button", { name: "토큰 지우기" }));
    await enterAdminToken(user, TOKEN);

    // 새 토큰은 옛 요청을 나눠 받지 않고 제 요청을 보낸다.
    expect(await screen.findByRole("region", { name: "이벤트" })).toBeTruthy();
    expect(authorizations).toEqual([`Bearer ${old}`, `Bearer ${TOKEN}`]);
    late.resolve(
      HttpResponse.json(envelope("unauthorized", "토큰이 없거나 틀리다"), { status: 401 }),
    );
    // 늦은 응답이 처리될 틈을 준다. 옛 요청의 401 이 새 토큰을 내려놓으면 넣는 자리로 돌아간다.
    await new Promise((resolve) => setTimeout(resolve, 200));

    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("새로 고침 버튼이 그 트레이스를 다시 읽는다", async () => {
    const authorizations = serveTrace(`/traces/${RUN}`, (call) =>
      HttpResponse.json(call === 0 ? { ...TRACE, events: TRACE.events.slice(0, 1) } : TRACE),
    );
    const user = await openRun(RUN);
    await screen.findByRole("region", { name: "이벤트" });
    expect(eventItems()).toHaveLength(1);

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    await within(events()).findByText("run_finished");
    expect(eventItems()).toHaveLength(TRACE.events.length);
    expect(authorizations).toHaveLength(2);
  });

  test("이미 보인 트레이스도 다시 읽다 실패하면 이벤트를 지우고 실패를 보인다", async () => {
    serveTrace(`/traces/${RUN}`, (call) =>
      call === 0
        ? HttpResponse.json(TRACE)
        : HttpResponse.json(envelope("internal_error", "트레이스를 읽을 수 없다"), { status: 500 }),
    );
    const user = await openRun(RUN);
    await screen.findByRole("region", { name: "이벤트" });

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("alert")).textContent).toContain("트레이스를 읽을 수 없다");
    expect(screen.queryByRole("region", { name: "이벤트" })).toBeNull();
  });

  test("주소의 조각이 인코딩된 채로 와도 풀어서 보이고 요청은 한 번만 인코딩한다", async () => {
    // Next 16.3.6 은 동적 조각을 퍼센트 인코딩된 채로 넘긴다. 패턴 안의 식별자로는 드러나지 않아 띄어쓰기로 잰다.
    const authorizations = serveTrace("/traces/run%20one", () =>
      HttpResponse.json(envelope("invalid_request", "요청의 형식이 올바르지 않다"), {
        status: 422,
      }),
    );

    // 두 번 인코딩한 요청(run%2520one)은 처리하지 않은 요청이라 setup.ts 가 테스트를 빨갛게 한다.
    await openRun("run%20one");

    expect(await screen.findByRole("heading", { level: 2, name: "run one" })).toBeTruthy();
    expect((await screen.findByRole("alert")).textContent).toContain("요청의 형식이 올바르지 않다");
    expect(authorizations).toHaveLength(1);
  });

  test("풀 수 없는 주소의 조각이면 요청을 보내지 않고 그렇다고 말한다", async () => {
    await openRun("%E0%A4%A");

    expect((await screen.findByRole("alert")).textContent).toContain("주소를 풀 수 없다: %E0%A4%A");
  });

  test("실행 목록으로 돌아가는 링크가 있다", async () => {
    serveTrace(`/traces/${RUN}`, () => HttpResponse.json(TRACE));

    await openRun(RUN);

    const back = await screen.findByRole("link", { name: "실행 목록으로" });
    expect(back.getAttribute("href")).toBe("/runs");
    await screen.findByRole("region", { name: "이벤트" });
  });
});
