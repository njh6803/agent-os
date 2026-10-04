// 결정. 운영자가 채널 토큰을 넣으면 멈춘 실행에 결정 자리가 서고, 허가나 거부를 보내면 재개된 실행의 이벤트가 받는
// 대로 붙는다(web-admin 티켓 08). 결정의 자리는 화면이 트레이스 상세에서 읽은 인덱스다(ADR 0019 이력).
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 재개 스트림은 `ReadableStream` 으로 프레임을 시간
// 간격을 두고 낸다(testing/stream.ts). 결정 요청에는 채널 토큰만, 관리 요청에는 관리 토큰만 실리는 것을 핸들러가
// 헤더로 본다(스토리 10).

import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, test, vi } from "vitest";
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
import { enterAdminToken, enterChannelToken } from "../../testing/token";
import { RunPage } from "./RunPage";

const ADMIN = "adm-4Kd8-decision-page-token";
const CHANNEL = "chn-2Pw6-decision-page-token";
const RUN = "r-gated";
const TS = "2026-09-30T10:00:00+00:00";

const STARTED: RunEvent = {
  type: "run_started",
  run_id: RUN,
  ts: TS,
  agent: "calc",
  request: "2 더하기 3 하고 4 더하기 5",
  principal: "operator",
  previous_run: null,
};
const CALLED: RunEvent = {
  type: "llm_called",
  run_id: RUN,
  ts: TS,
  model: "claude-sonnet-5",
  input_tokens: 10,
  output_tokens: 4,
  prompt: "계산한다",
  text: "",
  tool_calls: [{ id: "call-1", name: "add", args: { a: 2, b: 3 } }],
};
const FIRST_ARGS = { a: 2, b: 3 };
const SECOND_ARGS = { a: 4, b: 5 };
const paused = (args: Record<string, number>): RunEvent => ({
  type: "run_paused",
  run_id: RUN,
  ts: TS,
  tool: "add",
  args,
});
const GRANTED: RunEvent = { type: "approval_granted", run_id: RUN, ts: TS, approver: "operator" };
const RESUMED: RunEvent = { type: "run_resumed", run_id: RUN, ts: TS };
const tool = (args: Record<string, number>, content: string): RunEvent => ({
  type: "tool_called",
  run_id: RUN,
  ts: TS,
  tool: "add",
  ok: true,
  args,
  content,
});
const FINISHED: RunEvent = { type: "run_finished", run_id: RUN, ts: TS, output: "5/9" };

const trace = (events: readonly Trace["events"][number][]): Trace => ({
  run_id: RUN,
  schema_version: "2",
  events: [...events],
});

/** 시작(0), 모델 호출(1), 첫 일시정지(2). 결정의 자리는 2 다. */
const PAUSED = trace([STARTED, CALLED, paused(FIRST_ARGS)]);
/** 첫 결정(3), 재개(4), 도구(5), 둘째 일시정지(6). */
const REPAUSED_TAIL = [GRANTED, RESUMED, tool(FIRST_ARGS, "5"), paused(SECOND_ARGS)] as const;
const REPAUSED = trace([...PAUSED.events, ...REPAUSED_TAIL]);
const FINISHED_TAIL = [GRANTED, RESUMED, tool(FIRST_ARGS, "5"), FINISHED] as const;
const DONE = trace([...PAUSED.events, ...FINISHED_TAIL]);

const CALC: Plugin = {
  kind: "agent",
  name: "calc",
  enabled: true,
  manifest: {
    schema_version: "1",
    kind: "agent",
    name: "calc",
    version: "0.1.0",
    entrypoint: "agent:Calc",
    mcp: ["fixture"],
    requires_approval: ["add"],
    conversation_limit: null,
    server: null,
  },
};
const FIXTURE: Plugin = {
  kind: "mcp",
  name: "fixture",
  enabled: true,
  manifest: {
    schema_version: "1",
    kind: "mcp",
    name: "fixture",
    version: "0.1.0",
    entrypoint: null,
    mcp: [],
    requires_approval: [],
    conversation_limit: null,
    server: { command: "python", args: ["fixture.py"], secret_args: {} },
  },
};
const ROWS: PluginRow[] = [CALC, FIXTURE];

/** 요청 하나가 실은 것. */
interface Sent {
  readonly authorization: string;
  readonly body: unknown;
}

/** `GET /traces/{run_id}` 에 답한다. `reply` 는 몇 번째 요청인지(0부터) 받는다. 요청마다의 `Authorization` 을 쌓는다. */
function serveTrace(reply: (call: number) => Trace): string[] {
  const authorizations: string[] = [];
  network.use(
    http.get(api(`/traces/${RUN}`), ({ request }) => {
      authorizations.push(request.headers.get("Authorization") ?? "(없음)");
      return HttpResponse.json(reply(authorizations.length - 1));
    }),
  );
  return authorizations;
}

/** `GET /plugins` 에 그 행들로 답한다. 관리 토큰의 확인 요청도 여기 든다. 요청마다의 `Authorization` 을 쌓는다. */
function servePlugins(rows: readonly PluginRow[]): string[] {
  const authorizations: string[] = [];
  network.use(
    http.get(api("/plugins"), ({ request }) => {
      authorizations.push(request.headers.get("Authorization") ?? "(없음)");
      return HttpResponse.json([...rows]);
    }),
  );
  return authorizations;
}

/** `POST /runs/{run_id}/approval` 에 답한다. 요청마다의 `Authorization` 과 본문을 쌓는다. */
function serveDecision(
  reply: (call: number, request: Request) => Response | Promise<Response>,
): Sent[] {
  const sent: Sent[] = [];
  network.use(
    http.post(api(`/runs/${RUN}/approval`), async ({ request }) => {
      const body: unknown = await request.clone().json();
      sent.push({ authorization: request.headers.get("Authorization") ?? "(없음)", body });
      return reply(sent.length - 1, request);
    }),
  );
  return sent;
}

/** 재개 스트림으로 답한다. 프레임은 이벤트이거나 걸음이다. */
function stream(steps: readonly (RunEvent | Step)[]): Response {
  return resumeStream(
    steps.map((step) =>
      typeof step === "object" && !(step instanceof Promise) ? frame(step) : step,
    ),
  );
}

/** 실행 하나를 열고 관리 토큰을 넣는다. 트레이스가 설 때까지 기다린다. */
async function openRun(): Promise<UserEvent> {
  const user = userEvent.setup();
  renderPage(<RunPage runId={RUN} />);
  await enterAdminToken(user, ADMIN);
  await screen.findByRole("region", { name: "이벤트" });
  return user;
}

/** 실행 하나를 열고 두 토큰을 넣는다. 결정 자리가 설 때까지 기다린다. */
async function openDecision(): Promise<UserEvent> {
  const user = await openRun();
  await enterChannelToken(user, CHANNEL);
  await screen.findByRole("region", { name: "결정" });
  return user;
}

function place(): HTMLElement {
  return screen.getByRole("region", { name: "결정" });
}

function events(): HTMLElement {
  return screen.getByRole("region", { name: "이벤트" });
}

function button(name: string): HTMLButtonElement {
  return screen.getByRole<HTMLButtonElement>("button", { name });
}

/**
 * 결정 자리가 그 인자의 일시정지를 보일 때까지 기다린다. 인자는 들여 적은 여러 줄이라 글자 matcher 가 아니라 자리의
 * 글자에 든 것으로 본다(Testing Library 는 요소의 글자만 공백을 접는다).
 */
async function showsArgs(args: Record<string, number>): Promise<void> {
  await waitFor(() => {
    expect(place().textContent).toContain(JSON.stringify(args, null, 2));
  });
}

function reason(): HTMLElement {
  return screen.getByRole("textbox", { name: "거부 사유" });
}

/** 그 자리의 이벤트 제목(종류) 전부. 쓴 순서대로다. */
function kinds(region: HTMLElement): (string | null)[] {
  return within(region)
    .getAllByRole("heading", { level: 4 })
    .map((heading) => heading.textContent);
}

/** 브라우저 저장소 하나의 값 전부. */
function storedValues(storage: Storage): string[] {
  const found: string[] = [];
  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    found.push(key === null ? "" : (storage.getItem(key) ?? ""));
  }
  return found;
}

afterEach(() => {
  vi.useRealTimers();
});

describe("결정 자리", () => {
  test("채널 토큰이 없으면 멈춘 실행에도 결정 자리가 없고 채널 토큰을 넣는 자리가 있다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);

    await openRun();

    expect(screen.queryByRole("region", { name: "결정" })).toBeNull();
    expect(screen.queryByRole("button", { name: "허가" })).toBeNull();
    expect(screen.getByLabelText("채널 토큰")).toBeTruthy();
  });

  test("채널 토큰을 넣으면 멈춘 실행에 결정 자리가 서고 무엇을 승인하는지 도구와 인자가 보인다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);

    await openDecision();

    const shown = place().textContent;
    expect(shown).toContain("add");
    expect(shown).toContain(JSON.stringify(FIRST_ARGS, null, 2));
    expect(button("허가").disabled).toBe(false);
  });

  test("결정 자리는 승인자가 serve 를 띄운 OS 사용자로 기록된다고 말한다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);

    await openDecision();

    expect(place().textContent).toMatch(/승인자는 .*serve.* 를 띄운 OS 사용자로 기록된다/);
  });

  test("끝난 실행에는 채널 토큰이 있어도 결정 자리가 없다", async () => {
    serveTrace(() => DONE);
    servePlugins(ROWS);
    const user = await openRun();

    await enterChannelToken(user, CHANNEL);

    expect(await screen.findByText("채널 토큰을 넣었다")).toBeTruthy();
    expect(screen.queryByRole("region", { name: "결정" })).toBeNull();
  });

  test("형식 1 트레이스는 멈춰 있어도 결정 자리가 없고 재개할 수 없다는 말 하나만 있다", async () => {
    serveTrace(() => ({ ...PAUSED, schema_version: "1" }));
    servePlugins(ROWS);
    const user = await openRun();

    await enterChannelToken(user, CHANNEL);

    expect(await screen.findByText("채널 토큰을 넣었다")).toBeTruthy();
    expect(screen.queryByRole("region", { name: "결정" })).toBeNull();
    expect(screen.getAllByText(/재개할 수 없다/)).toHaveLength(1);
  });

  test("형식 3 트레이스의 멈춘 실행에도 결정 자리가 선다", async () => {
    // 형식 조건은 "형식 1 이 아니다"다. 형식이 늘 때마다 결정 자리가 조용히 사라지지 않는다(스토리 56).
    serveTrace(() => ({ ...PAUSED, schema_version: "3" }));
    servePlugins(ROWS);

    await openDecision();

    expect(place().textContent).toContain("add");
  });
});

describe("허가와 거부", () => {
  test("허가는 채널 토큰만 싣고 판별자와 트레이스 상세에서 읽은 자리를 보낸다", async () => {
    const traceAuthorizations = serveTrace((call) => (call === 0 ? PAUSED : DONE));
    const pluginAuthorizations = servePlugins(ROWS);
    const sent = serveDecision(() => stream(FINISHED_TAIL));
    const user = await openDecision();

    await user.click(button("허가"));

    await waitFor(() => {
      expect(sent).toHaveLength(1);
    });
    expect(sent).toEqual([
      { authorization: `Bearer ${CHANNEL}`, body: { decision: "approve", pause_index: 2 } },
    ]);
    await within(events()).findByText("run_finished");
    // 관리 요청에는 채널 토큰이 실리지 않는다.
    expect(new Set([...traceAuthorizations, ...pluginAuthorizations])).toEqual(
      new Set([`Bearer ${ADMIN}`]),
    );
  });

  test("거부는 사유가 비어 있거나 공백뿐이면 보낼 수 없다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);
    const sent = serveDecision(() => stream(FINISHED_TAIL));
    const user = await openDecision();

    expect(button("거부").disabled).toBe(true);
    await user.type(reason(), "   ");
    await user.click(button("거부"));

    expect(button("거부").disabled).toBe(true);
    expect(sent).toEqual([]);
  });

  test("거부는 적은 사유를 다듬어 판별자와 자리와 함께 보낸다", async () => {
    serveTrace((call) => (call === 0 ? PAUSED : DONE));
    servePlugins(ROWS);
    const sent = serveDecision(() => stream(FINISHED_TAIL));
    const user = await openDecision();

    await user.type(reason(), "  인자가 틀렸다 ");
    await user.click(button("거부"));

    await waitFor(() => {
      expect(sent).toHaveLength(1);
    });
    expect(sent[0]?.body).toEqual({ decision: "deny", pause_index: 2, reason: "인자가 틀렸다" });
  });

  test("거부가 422 를 받으면 violations 를 사유 옆에 보인다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);
    serveDecision(() =>
      HttpResponse.json(
        {
          ...envelope("invalid_request", "요청의 형식이 올바르지 않다", "req-4220"),
          violations: [{ field: "body.deny.reason", message: "사유는 비어 있을 수 없다" }],
        },
        { status: 422 },
      ),
    );
    const user = await openDecision();

    await user.type(reason(), "사유");
    await user.click(button("거부"));

    expect(
      await screen.findByRole("textbox", {
        name: "거부 사유",
        description: /body\.deny\.reason.*사유는 비어 있을 수 없다/,
      }),
    ).toBeTruthy();
    expect(place().textContent).toContain("req-4220");
  });
});

describe("재개 스트림", () => {
  test("재개된 실행의 이벤트가 스트림이 닫히기 전에 받는 대로 트레이스 아래에 붙고 그동안 결정 버튼이 막힌다", async () => {
    const hold = Promise.withResolvers<undefined>();
    const traceAuthorizations = serveTrace((call) => (call === 0 ? PAUSED : DONE));
    servePlugins(ROWS);
    serveDecision(() =>
      stream([GRANTED, KEEPALIVE, RESUMED, hold.promise, tool(FIRST_ARGS, "5"), FINISHED]),
    );
    const user = await openDecision();

    await user.click(button("허가"));

    const resumed = await screen.findByRole("region", { name: "재개 스트림" });
    await within(resumed).findByText("run_resumed");
    expect(kinds(resumed)).toEqual(["approval_granted", "run_resumed"]);
    expect(events().compareDocumentPosition(resumed) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(
      0,
    );
    expect(traceAuthorizations).toHaveLength(1);
    expect(button("허가").disabled).toBe(true);
    expect(button("거부").disabled).toBe(true);
    hold.resolve(undefined);
  });

  test("재개 스트림이 결말로 끝나면 트레이스를 다시 읽고 그 기록으로 보인다", async () => {
    const traceAuthorizations = serveTrace((call) => (call === 0 ? PAUSED : DONE));
    servePlugins(ROWS);
    serveDecision(() => stream(FINISHED_TAIL));
    const user = await openDecision();

    await user.click(button("허가"));

    await within(events()).findByText("run_finished");
    expect(traceAuthorizations).toHaveLength(2);
    expect(kinds(events())).toHaveLength(DONE.events.length);
    // 기록의 원천은 다시 읽은 트레이스다. 스트림으로 받은 것은 걷힌다.
    expect(screen.queryByRole("region", { name: "재개 스트림" })).toBeNull();
    expect(screen.queryByRole("region", { name: "결정" })).toBeNull();
    expect(screen.queryByText(/끊겼다/)).toBeNull();
  });

  test("재개 스트림이 결말 없이 끊겨도 결정을 다시 보내지 않고 트레이스를 다시 읽으며 끊겼다고 말한다", async () => {
    // 결말 없이 닫는다. MSW 에서는 도중의 끊김도 이 모양으로 온다(testing/stream.ts).
    const partial = trace([...PAUSED.events, GRANTED, RESUMED]);
    const traceAuthorizations = serveTrace((call) => (call === 0 ? PAUSED : partial));
    servePlugins(ROWS);
    const sent = serveDecision(() => stream([GRANTED, RESUMED, KEEPALIVE]));
    const user = await openDecision();

    await user.click(button("허가"));

    expect(await screen.findByText(/재개 스트림이 끊겼다. 실행은 서버에서 계속된다/)).toBeTruthy();
    expect(screen.getByText(/창을 닫거나 떠나도 실행은 끝까지 간다/)).toBeTruthy();
    expect(screen.getByText(/돌아오면 트레이스로 이어 본다/)).toBeTruthy();
    await waitFor(() => {
      expect(kinds(events())).toHaveLength(partial.events.length);
    });
    expect(traceAuthorizations).toHaveLength(2);
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(sent).toHaveLength(1);
  });

  test("다시 읽은 트레이스가 새 일시정지에서 끝나면 새 자리로 결정 자리가 다시 서고 그 자리로 결정한다", async () => {
    const second = trace([...REPAUSED.events, GRANTED, RESUMED, tool(SECOND_ARGS, "9"), FINISHED]);
    serveTrace((call) => [PAUSED, REPAUSED][call] ?? second);
    servePlugins(ROWS);
    const sent = serveDecision((call) =>
      call === 0
        ? stream(REPAUSED_TAIL)
        : stream([GRANTED, RESUMED, tool(SECOND_ARGS, "9"), FINISHED]),
    );
    const user = await openDecision();
    // 앞 일시정지에 거부 사유를 적다가 허가한다. 새 일시정지는 새로 판단할 호출이라 그 사유를 들지 않는다.
    await user.type(reason(), "앞 일시정지의 사유");

    await user.click(button("허가"));

    await showsArgs(SECOND_ARGS);
    await waitFor(() => {
      expect(button("허가").disabled).toBe(false);
    });
    // 다시 멈춘 것은 결말이다. 끊긴 것이 아니다.
    expect(screen.queryByText(/끊겼다/)).toBeNull();
    expect(screen.getByRole<HTMLTextAreaElement>("textbox", { name: "거부 사유" }).value).toBe("");
    await user.click(button("허가"));
    await within(events()).findByText("run_finished");
    expect(sent.map(({ body }) => body)).toEqual([
      { decision: "approve", pause_index: 2 },
      { decision: "approve", pause_index: 6 },
    ]);
  });

  test("술어를 지나지 못한 프레임은 원문 그대로 보이고 뒤의 프레임도 계속 붙는다", async () => {
    const hold = Promise.withResolvers<undefined>();
    const notJson = "이것은 JSON 이 아니다 <b>굵게</b>";
    const unknownKind = '{"type":"run_exploded","run_id":"r-gated"}';
    serveTrace((call) => (call === 0 ? PAUSED : DONE));
    servePlugins(ROWS);
    serveDecision(() =>
      stream([GRANTED, frame(notJson), frame(unknownKind), RESUMED, hold.promise, FINISHED]),
    );
    const user = await openDecision();

    await user.click(button("허가"));

    const resumed = await screen.findByRole("region", { name: "재개 스트림" });
    await within(resumed).findByText("run_resumed");
    expect(resumed.textContent).toContain(notJson);
    expect(resumed.textContent).toContain(unknownKind);
    expect(document.querySelector("b")).toBeNull();
    expect(within(resumed).getAllByRole("listitem")).toHaveLength(4);
    hold.resolve(undefined);
  });

  test("재개 스트림 도중에 떠났다가 돌아오면 떠난 결정은 스트림이 끝나도 트레이스를 다시 읽지 않는다", async () => {
    // 떠나면 요청의 signal 로 연결을 끊고 그 결정은 끝난다. MSW 3.0.0 에서 끊김은 읽는 쪽에만 닿아 핸들러에서 볼 수 없다
    // (`.scratch/web-admin/probes/msw_abort.mjs`). 그래서 돌아온 화면을 본다. SWR 의 캐시는 화면 사이에 하나라서(앱은
    // 전역 캐시를 쓴다) 떠난 결정이 스트림의 끝에서 다시 읽으면 돌아온 화면의 트레이스를 부른다.
    const hold = Promise.withResolvers<undefined>();
    const traceAuthorizations = serveTrace(() => PAUSED);
    servePlugins(ROWS);
    serveDecision(() => stream([GRANTED, hold.promise, RESUMED, FINISHED]));
    const cache = new Map();
    const user = userEvent.setup();
    const left = renderPage(<RunPage runId={RUN} />, cache);
    await enterAdminToken(user, ADMIN);
    await enterChannelToken(user, CHANNEL);
    await user.click(await screen.findByRole("button", { name: "허가" }));
    await screen.findByText("approval_granted");
    left.unmount();

    renderPage(<RunPage runId={RUN} />, cache);
    await screen.findByRole("region", { name: "결정" });
    await new Promise((resolve) => setTimeout(resolve, 100));
    const readBefore = traceAuthorizations.length;
    hold.resolve(undefined);

    await new Promise((resolve) => setTimeout(resolve, 200));
    expect(traceAuthorizations).toHaveLength(readBefore);
    expect(screen.queryByRole("region", { name: "재개 스트림" })).toBeNull();
  });
});

describe("409 와 꺼짐", () => {
  test("409 면 봉투의 메시지를 보이고 트레이스와 플러그인 목록을 다시 읽어 지금의 일시정지를 보인다", async () => {
    const message = "결정이 가리킨 자리 2 는 지금의 일시정지(자리 6)가 아니다";
    const traceAuthorizations = serveTrace((call) => (call === 0 ? PAUSED : REPAUSED));
    const pluginAuthorizations = servePlugins(ROWS);
    serveDecision(() =>
      HttpResponse.json(envelope("conflict", message, "req-4090"), { status: 409 }),
    );
    const user = await openDecision();
    const readBefore = pluginAuthorizations.length;

    await user.click(button("허가"));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain(message);
    expect(alert.textContent).toContain("req-4090");
    await showsArgs(SECOND_ARGS);
    expect(traceAuthorizations).toHaveLength(2);
    expect(pluginAuthorizations.length).toBeGreaterThan(readBefore);
    // 새 일시정지가 보이는 동안에도 메시지가 남는다.
    expect(screen.getByRole("alert").textContent).toContain(message);
  });

  test("에이전트가 꺼졌으면 결정 버튼이 막히고 꺼진 에이전트가 보인다", async () => {
    serveTrace(() => PAUSED);
    servePlugins([{ ...CALC, enabled: false }, FIXTURE]);
    const user = await openDecision();

    expect(await within(place()).findByText(/꺼진 플러그인이 있어 재개할 수 없다/)).toBeTruthy();
    expect(place().textContent).toContain("에이전트 calc");
    await user.type(reason(), "사유");
    expect(button("허가").disabled).toBe(true);
    expect(button("거부").disabled).toBe(true);
  });

  test("에이전트가 쓰는 MCP 가 꺼졌으면 결정 버튼이 막히고 꺼진 MCP 가 보인다", async () => {
    serveTrace(() => PAUSED);
    servePlugins([CALC, { ...FIXTURE, enabled: false }]);
    await openDecision();

    expect(await within(place()).findByText(/꺼진 플러그인이 있어 재개할 수 없다/)).toBeTruthy();
    expect(place().textContent).toContain("MCP fixture");
    expect(place().textContent).not.toContain("에이전트 calc");
    expect(button("허가").disabled).toBe(true);
  });

  test("플러그인 목록을 다시 읽다 실패하면 옛 꺼짐을 믿지 않고 미리 알 수 없다고 말하며 결정 버튼을 막지 않는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    serveTrace(() => PAUSED);
    // 관리 토큰의 확인(0)과 결정 자리의 목록(1)은 에이전트가 꺼진 목록이고, 그 뒤는 운영자 파일이 깨진 500 이다.
    let listed = 0;
    network.use(
      http.get(api("/plugins"), () => {
        listed += 1;
        return listed <= 2
          ? HttpResponse.json([{ ...CALC, enabled: false }, FIXTURE])
          : HttpResponse.json(envelope("internal_error", "운영자 파일을 읽을 수 없다"), {
              status: 500,
            });
      }),
    );
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    renderPage(<RunPage runId={RUN} />);
    await enterAdminToken(user, ADMIN);
    await enterChannelToken(user, CHANNEL);
    expect(
      await within(await screen.findByRole("region", { name: "결정" })).findByText(
        /꺼진 플러그인이 있어 재개할 수 없다/,
      ),
    ).toBeTruthy();
    expect(button("허가").disabled).toBe(true);

    // SWR 은 마운트한 뒤 한동안(focusThrottleInterval) 포커스를 흘려보낸다. 그 너머로 민다.
    await vi.advanceTimersByTimeAsync(10_000);
    fireEvent.focus(window);

    await waitFor(() => {
      expect(button("허가").disabled).toBe(false);
    });
    expect(listed).toBe(3);
    expect(place().textContent).not.toContain("꺼진 플러그인이 있어");
    expect(place().textContent).toContain(
      "플러그인 목록을 읽지 못해 꺼진 플러그인을 미리 알 수 없다",
    );
  });

  test("에이전트 행이 표지면 미리 알 수 없어 결정 버튼을 막지 않는다", async () => {
    serveTrace(() => PAUSED);
    servePlugins([
      { kind: "agent", name: "calc", enabled: false, reason: "매니페스트를 읽을 수 없다" },
      { ...FIXTURE, enabled: false },
    ]);
    await openDecision();

    // 목록을 읽은 뒤에도 막지 않는다.
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(place().textContent).not.toContain("꺼진 플러그인");
    expect(button("허가").disabled).toBe(false);
  });
});

describe("채널 토큰의 거부", () => {
  test("결정이 401 을 받으면 채널 토큰만 지우고 채널 토큰이 거부됐다고 말하며 관리 화면은 그대로 쓴다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);
    serveDecision(() =>
      HttpResponse.json(envelope("unauthorized", "토큰이 없거나 틀리다"), { status: 401 }),
    );
    const user = await openDecision();

    await user.click(button("허가"));

    expect((await screen.findByRole("alert")).textContent).toContain("채널 토큰이 거부됐다");
    expect(screen.getByRole("region", { name: "이벤트" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "허가" })).toBeNull();
    expect(screen.getByLabelText("채널 토큰")).toBeTruthy();
    const stored = storedValues(sessionStorage).join("\n");
    expect(stored).toContain(ADMIN);
    expect(stored).not.toContain(CHANNEL);
  });
});
