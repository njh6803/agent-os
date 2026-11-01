// 결정. 운영자가 채널 토큰을 넣으면 멈춘 실행에 결정 자리가 서고, 승인이나 거부를 보내면 재개된 실행의 이벤트가 받는
// 대로 붙는다(web-admin 티켓 08). 결정의 자리는 화면이 트레이스 상세에서 읽은 인덱스다(ADR 0019 이력). 결정 칸에는
// 셋 가운데 하나가 선다(admin-style 티켓 08). 최종 사용자의 실행이면 채널 토큰과 상관없이 결정은 그 사람만 낸다는 한
// 줄(end-user-channel 티켓 05), 채널 토큰이 없으면 설정에서 넣으라는 한 줄과 "설정 열기", 그 밖에는 결정 자리다.
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
/** 이벤트 칸의 이름. 제목이 "이벤트 <개수>"다. */
const EVENTS = /^이벤트 \d+$/;

const STARTED: RunEvent = {
  type: "run_started",
  run_id: RUN,
  ts: TS,
  agent: "calc",
  request: "2 더하기 3 하고 4 더하기 5",
  principal: "operator",
  previous_run: null,
  shortcuts: null,
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

/** 최종 사용자의 주체. 사이트의 발급자와 `sub` 를 구분자 `|` 로 묶은 이름이다(end-user-channel 명세 "주체"). */
const END_USER = "https://shop.example|user-42";
/** `PAUSED` 와 같되 주체가 최종 사용자이고 형식 3 이다. */
const END_USER_PAUSED: Trace = {
  ...trace([{ ...STARTED, principal: END_USER }, ...PAUSED.events.slice(1)]),
  schema_version: "3",
};

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
    model: null,
    provider: null,
    model_id: null,
    max_tokens: null,
    temperature: null,
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
    model: null,
    provider: null,
    model_id: null,
    max_tokens: null,
    temperature: null,
    server: { command: "python", args: ["fixture.py"], secret_args: {} },
  },
};
const ROWS: PluginRow[] = [CALC, FIXTURE];

/** 모델 플러그인 하나. 에이전트가 `model` 로 이름을 골라 쓴다. */
function modelPlugin(name: string, { enabled }: { readonly enabled: boolean }): Plugin {
  return {
    kind: "model",
    name,
    enabled,
    manifest: {
      schema_version: "1",
      kind: "model",
      name,
      version: "0.1.0",
      entrypoint: null,
      mcp: [],
      requires_approval: [],
      conversation_limit: null,
      model: null,
      provider: "anthropic",
      model_id: "claude-sonnet-5",
      max_tokens: 4096,
      temperature: null,
      server: null,
    },
  };
}

/** `model` 로 그 모델을 고른 `calc`. */
function calcUsing(model: string | null): Plugin {
  return CALC.kind === "agent" && "manifest" in CALC
    ? { ...CALC, manifest: { ...CALC.manifest, model } }
    : CALC;
}

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
  await screen.findByRole("region", { name: EVENTS });
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
  return screen.getByRole("region", { name: EVENTS });
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

/** 채널 토큰이 없을 때의 안내 줄. */
const NO_CHANNEL_TOKEN = "결정을 내리려면 설정에서 채널 토큰을 넣는다";
/** 최종 사용자의 실행의 한 줄. */
const END_USER_LINE = "최종 사용자의 실행이라 결정은 그 사람만 낸다";

/** `a` 가 문서에서 `b` 보다 앞에 서는가. */
function precedes(a: Node, b: Node): boolean {
  return (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
}

/** 제목 글자로 알림 하나를 찾는다. 패키지 `Alert` 는 제목을 첫 문단으로 둔다. */
async function alertTitled(title: string): Promise<HTMLElement> {
  const alert = (await screen.findByText(title)).closest('[role="alert"], [role="status"]');
  if (!(alert instanceof HTMLElement)) {
    throw new Error(`알림이 아니다: ${title}`);
  }
  return alert;
}

/** 그 자리의 이벤트 종류 전부. 쓴 순서대로다. 카드 머리("<종류> <시각>")의 첫 낱말이다. */
function kinds(region: HTMLElement): (string | undefined)[] {
  return within(region)
    .getAllByRole("heading", { level: 3 })
    .map((heading) => heading.textContent.split(" ")[0]);
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
  test("채널 토큰이 없으면 멈춘 실행에 결정 자리 대신 설정에서 넣으라는 한 줄과 설정 열기가 서고 실행 화면에 채널 토큰을 넣는 자리는 없다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);

    await openRun();

    expect(screen.queryByRole("region", { name: "결정" })).toBeNull();
    expect(screen.queryByRole("button", { name: "승인" })).toBeNull();
    expect(screen.getAllByText(NO_CHANNEL_TOKEN)).toHaveLength(1);
    expect(screen.getByRole("link", { name: "설정 열기" }).getAttribute("href")).toBe("/settings");
    expect(screen.queryByLabelText("채널 토큰")).toBeNull();
    // 안내 줄의 아이콘은 꾸밈이라 화면 읽기 프로그램에서 숨는다.
    const line = screen.getByText(NO_CHANNEL_TOKEN).closest("p");
    expect(line?.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });

  test("채널 토큰을 넣으면 안내 줄이 걷히고 멈춘 실행에 결정 자리가 서며 무엇을 승인하는지 도구와 인자가 보인다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);

    await openDecision();

    const shown = place().textContent;
    expect(shown).toContain("add");
    expect(shown).toContain(JSON.stringify(FIRST_ARGS, null, 2));
    expect(button("승인").disabled).toBe(false);
    expect(screen.queryByText(NO_CHANNEL_TOKEN)).toBeNull();
    expect(screen.queryByRole("link", { name: "설정 열기" })).toBeNull();
  });

  test("결정 자리의 버튼은 거부 다음 승인이고 허가는 없으며 사유 칸이 버튼 위에 선다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);

    await openDecision();

    expect(
      within(place())
        .getAllByRole("button")
        .map((found) => found.textContent),
    ).toEqual(["거부", "승인"]);
    expect(screen.queryByText("허가")).toBeNull();
    expect(precedes(reason(), button("거부"))).toBe(true);
    expect(
      screen.getByRole("textbox", {
        name: "거부 사유",
        description: "거부하려면 적는다. 비어 있으면 거부를 보낼 수 없다.",
      }),
    ).toBeTruthy();
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

    expect(screen.queryByRole("region", { name: "결정" })).toBeNull();
  });

  test("형식 1 트레이스는 멈춰 있어도 결정 자리가 없고 재개할 수 없다는 말 하나만 있다", async () => {
    serveTrace(() => ({ ...PAUSED, schema_version: "1" }));
    servePlugins(ROWS);
    const user = await openRun();

    await enterChannelToken(user, CHANNEL);

    expect(screen.queryByRole("region", { name: "결정" })).toBeNull();
    expect(screen.getAllByText(/재개할 수 없다/)).toHaveLength(1);
    expect(screen.queryByText(NO_CHANNEL_TOKEN)).toBeNull();
  });

  test("형식 1 트레이스는 채널 토큰이 없어도 결정 칸이 서지 않는다", async () => {
    serveTrace(() => ({ ...PAUSED, schema_version: "1" }));
    servePlugins(ROWS);

    await openRun();

    expect(screen.queryByText(NO_CHANNEL_TOKEN)).toBeNull();
    expect(screen.queryByRole("link", { name: "설정 열기" })).toBeNull();
  });

  test("형식 3 트레이스의 멈춘 실행에도 결정 자리가 선다", async () => {
    // 형식 조건은 "형식 1 이 아니다"다. 형식이 늘 때마다 결정 자리가 조용히 사라지지 않는다(스토리 56).
    serveTrace(() => ({ ...PAUSED, schema_version: "3" }));
    servePlugins(ROWS);

    await openDecision();

    expect(place().textContent).toContain("add");
  });

  test("최종 사용자의 멈춘 실행에는 채널 토큰이 있어도 결정 자리가 없고 결정은 그 사람만 낸다는 말 하나가 있다", async () => {
    // 주체 이름 `<발급자>|<sub>` 의 구분자로 최종 사용자를 알아본다(end-user-channel 명세 "관리 화면"). 서버에 묻지
    // 않는다. 같은 트레이스에 `|` 가 없으면 자리가 선다(위 형식 3 의 사례).
    serveTrace(() => END_USER_PAUSED);
    servePlugins(ROWS);
    const user = await openRun();

    await enterChannelToken(user, CHANNEL);

    expect(screen.queryByRole("region", { name: "결정" })).toBeNull();
    expect(screen.queryByRole("button", { name: "승인" })).toBeNull();
    expect(screen.getAllByText(END_USER_LINE)).toHaveLength(1);
    // 그 한 줄만 선 결정 칸에는 재개 스트림이 서지 않는다(admin-style 티켓 07 "재개 스트림이 서는 조건").
    expect(screen.queryByRole("region", { name: "재개 스트림" })?.textContent ?? null).toBeNull();
  });

  test("최종 사용자의 멈춘 실행은 채널 토큰이 없어도 결정은 그 사람만 낸다는 한 줄이고 채널 토큰 안내는 없다", async () => {
    serveTrace(() => END_USER_PAUSED);
    servePlugins(ROWS);

    await openRun();

    expect(screen.getAllByText(END_USER_LINE)).toHaveLength(1);
    expect(screen.queryByText(NO_CHANNEL_TOKEN)).toBeNull();
    expect(screen.queryByRole("link", { name: "설정 열기" })).toBeNull();
    expect(screen.queryByRole("region", { name: "재개 스트림" })).toBeNull();
    const line = screen.getByText(END_USER_LINE).closest("p");
    expect(line?.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });

  test("최종 사용자의 실행에서도 주체는 구분자 `|` 를 든 글자 그대로 이벤트에 보인다", async () => {
    // 목록과 상세는 바뀌지 않는다. 주체는 글자로 그려지고 `|` 는 글자다(web-admin 스토리 32).
    serveTrace(() => END_USER_PAUSED);
    servePlugins(ROWS);

    await openRun();

    expect(within(events()).getByText(END_USER)).toBeTruthy();
  });
});

describe("승인과 거부", () => {
  test("승인은 채널 토큰만 싣고 판별자와 트레이스 상세에서 읽은 자리를 보낸다", async () => {
    const traceAuthorizations = serveTrace((call) => (call === 0 ? PAUSED : DONE));
    const pluginAuthorizations = servePlugins(ROWS);
    const sent = serveDecision(() => stream(FINISHED_TAIL));
    const user = await openDecision();

    await user.click(button("승인"));

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

  test("거부가 422 를 받으면 결정 자리 안의 알림에 메시지와 추적 식별자와 위반을 모두 보이고 사유 칸이 사유의 위반을 받는다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);
    serveDecision(() =>
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
    const user = await openDecision();

    await user.type(reason(), "사유");
    await user.click(button("거부"));

    const field = await screen.findByRole("textbox", {
      name: "거부 사유",
      description: "사유는 비어 있을 수 없다",
    });
    expect(field.getAttribute("aria-invalid")).toBe("true");
    const alert = await alertTitled("결정을 보내지 못했다");
    expect(alert.getAttribute("role")).toBe("alert");
    expect(place().contains(alert)).toBe(true);
    // 알림은 사유 칸 바로 아래, 버튼 위다.
    expect(precedes(field, alert)).toBe(true);
    expect(precedes(alert, button("거부"))).toBe(true);
    const shown = alert.textContent;
    expect(shown).toContain("요청의 형식이 올바르지 않다");
    expect(shown).toContain("req-4220");
    expect(within(alert).getByText("body.deny.reason").tagName).toBe("CODE");
    expect(shown).toContain("사유는 비어 있을 수 없다");
    expect(within(alert).getByText("body.pause_index").tagName).toBe("CODE");
    expect(shown).toContain("음수일 수 없다");
  });

  test("422 의 위반이 사유에 걸리지 않으면 사유 칸은 오류 상태가 아니고 위반은 알림에 선다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);
    serveDecision(() =>
      HttpResponse.json(
        {
          ...envelope("invalid_request", "요청의 형식이 올바르지 않다", "req-4221"),
          violations: [{ field: "body.pause_index", message: "음수일 수 없다" }],
        },
        { status: 422 },
      ),
    );
    const user = await openDecision();

    await user.type(reason(), "사유");
    await user.click(button("거부"));

    const alert = await alertTitled("결정을 보내지 못했다");
    expect(alert.textContent).toContain("음수일 수 없다");
    expect(reason().getAttribute("aria-invalid")).toBeNull();
    expect(
      screen.getByRole("textbox", {
        name: "거부 사유",
        description: "거부하려면 적는다. 비어 있으면 거부를 보낼 수 없다.",
      }),
    ).toBeTruthy();
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

    await user.click(button("승인"));

    const resumed = await screen.findByRole("region", { name: "재개 스트림" });
    await within(resumed).findByText("run_resumed");
    expect(kinds(resumed)).toEqual(["approval_granted", "run_resumed"]);
    expect(events().compareDocumentPosition(resumed) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(
      0,
    );
    expect(traceAuthorizations).toHaveLength(1);
    expect(button("승인").disabled).toBe(true);
    expect(button("거부").disabled).toBe(true);
    hold.resolve(undefined);
  });

  test("재개 스트림이 결말로 끝나면 트레이스를 다시 읽고 그 기록으로 보인다", async () => {
    const traceAuthorizations = serveTrace((call) => (call === 0 ? PAUSED : DONE));
    servePlugins(ROWS);
    serveDecision(() => stream(FINISHED_TAIL));
    const user = await openDecision();

    await user.click(button("승인"));

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

    await user.click(button("승인"));

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
    // 앞 일시정지에 거부 사유를 적다가 승인한다. 새 일시정지는 새로 판단할 호출이라 그 사유를 들지 않는다.
    await user.type(reason(), "앞 일시정지의 사유");

    await user.click(button("승인"));

    await showsArgs(SECOND_ARGS);
    await waitFor(() => {
      expect(button("승인").disabled).toBe(false);
    });
    // 다시 멈춘 것은 결말이다. 끊긴 것이 아니다.
    expect(screen.queryByText(/끊겼다/)).toBeNull();
    expect(screen.getByRole<HTMLTextAreaElement>("textbox", { name: "거부 사유" }).value).toBe("");
    await user.click(button("승인"));
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

    await user.click(button("승인"));

    const resumed = await screen.findByRole("region", { name: "재개 스트림" });
    await within(resumed).findByText("run_resumed");
    expect(resumed.textContent).toContain(notJson);
    expect(resumed.textContent).toContain(unknownKind);
    expect(document.querySelector("b")).toBeNull();
    expect(within(resumed).getAllByRole("listitem")).toHaveLength(4);
    expect(
      within(resumed).getAllByRole("heading", { level: 3, name: "읽지 못한 프레임" }),
    ).toHaveLength(2);
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
    await user.click(await screen.findByRole("button", { name: "승인" }));
    await screen.findByText("approval_granted");
    left.unmount();

    renderPage(<RunPage runId={RUN} />, cache);
    await screen.findByRole("region", { name: "결정" });
    await new Promise((resolve) => setTimeout(resolve, 100));
    const readBefore = traceAuthorizations.length;
    hold.resolve(undefined);

    await new Promise((resolve) => setTimeout(resolve, 200));
    expect(traceAuthorizations).toHaveLength(readBefore);
    // 돌아온 화면의 재개 스트림은 결정 자리가 섰으니 서지만, 떠난 결정의 조각은 붙지 않아 빈 줄이다.
    const resumed = screen.getByRole("region", { name: "재개 스트림" });
    expect(within(resumed).queryAllByRole("listitem")).toHaveLength(0);
    expect(resumed.textContent).toContain("결정을 내면 재개한 이벤트가 여기에 차례로 붙는다.");
  });

  test("결정 자리가 서면 조각이 오기 전에도 재개 스트림이 빈 줄로 선다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);

    await openDecision();

    const resumed = screen.getByRole("region", { name: "재개 스트림" });
    expect(resumed.textContent).toContain("결정을 내면 재개한 이벤트가 여기에 차례로 붙는다.");
    expect(within(resumed).queryAllByRole("listitem")).toHaveLength(0);
  });

  test("채널 토큰이 없어 결정 자리가 서지 않으면 재개 스트림도 서지 않는다", async () => {
    serveTrace(() => PAUSED);
    servePlugins(ROWS);

    await openRun();

    expect(screen.queryByRole("region", { name: "재개 스트림" })).toBeNull();
  });

  test("끊긴 재개 스트림의 정보 알림은 이벤트 칸 위에 제목과 본문으로 선다", async () => {
    const partial = trace([...PAUSED.events, GRANTED, RESUMED]);
    serveTrace((call) => (call === 0 ? PAUSED : partial));
    servePlugins(ROWS);
    serveDecision(() => stream([GRANTED, RESUMED]));
    const user = await openDecision();

    await user.click(button("승인"));

    const title = await screen.findByText("재개 스트림이 끊겼다. 실행은 서버에서 계속된다");
    const alert = title.closest('[role="status"]');
    if (!(alert instanceof HTMLElement)) {
      throw new Error("끊긴 알림이 상태 영역이 아니다");
    }
    expect(
      within(alert).getByText(
        "창을 닫거나 떠나도 실행은 끝까지 간다. 돌아오면 트레이스로 이어 본다.",
      ),
    ).toBeTruthy();
    expect(alert.compareDocumentPosition(events()) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
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

    await user.click(button("승인"));

    const alert = await alertTitled("결정을 보내지 못했다");
    expect(alert.textContent).toContain(message);
    expect(within(alert).getByText("req-4090").tagName).toBe("CODE");
    // 화면 머리 아래, 이벤트 칸 위이고 결정 자리 밖이다.
    expect(precedes(alert, events())).toBe(true);
    await showsArgs(SECOND_ARGS);
    expect(place().contains(alert)).toBe(false);
    expect(traceAuthorizations).toHaveLength(2);
    expect(pluginAuthorizations.length).toBeGreaterThan(readBefore);
    // 새 일시정지가 보이는 동안에도 메시지가 남는다.
    expect(screen.getByRole("alert").textContent).toContain(message);
  });

  test("409 뒤 다시 읽은 실행이 일시정지가 아니어서 결정 칸이 걷혀도 알림은 남는다", async () => {
    const message = "실행이 이미 끝났다";
    serveTrace((call) => (call === 0 ? PAUSED : DONE));
    servePlugins(ROWS);
    serveDecision(() =>
      HttpResponse.json(envelope("conflict", message, "req-4091"), { status: 409 }),
    );
    const user = await openDecision();

    await user.click(button("승인"));

    await within(events()).findByText("run_finished");
    expect(screen.queryByRole("region", { name: "결정" })).toBeNull();
    const alert = await alertTitled("결정을 보내지 못했다");
    expect(alert.textContent).toContain(message);
    expect(precedes(alert, events())).toBe(true);
  });

  test("에이전트가 꺼졌으면 결정 버튼이 막히고 꺼진 에이전트가 보인다", async () => {
    serveTrace(() => PAUSED);
    servePlugins([{ ...CALC, enabled: false }, FIXTURE]);
    const user = await openDecision();

    const warning = (
      await within(place()).findByText("꺼진 플러그인이 있어 재개할 수 없다: 에이전트 calc")
    ).closest('[role="status"]');
    if (!(warning instanceof HTMLElement)) {
      throw new Error("꺼짐 경고가 상태 영역이 아니다");
    }
    expect(warning.textContent).toContain("다시 켜면 결정을 낼 수 있다.");
    expect(within(warning).getByRole("link", { name: "플러그인 목록" }).getAttribute("href")).toBe(
      "/",
    );
    // 사유 칸과 버튼 둘이 막힌다.
    expect(reason()).toHaveProperty("disabled", true);
    await user.type(reason(), "사유");
    expect(button("승인").disabled).toBe(true);
    expect(button("거부").disabled).toBe(true);
  });

  test("에이전트가 쓰는 MCP 가 꺼졌으면 결정 버튼이 막히고 꺼진 MCP 가 보인다", async () => {
    serveTrace(() => PAUSED);
    servePlugins([CALC, { ...FIXTURE, enabled: false }]);
    await openDecision();

    expect(await within(place()).findByText(/꺼진 플러그인이 있어 재개할 수 없다/)).toBeTruthy();
    expect(place().textContent).toContain("MCP fixture");
    expect(place().textContent).not.toContain("에이전트 calc");
    expect(button("승인").disabled).toBe(true);
  });

  test("에이전트가 고른 모델이 꺼졌으면 결정 버튼이 막히고 꺼진 모델이 보인다", async () => {
    serveTrace(() => PAUSED);
    servePlugins([calcUsing("sonnet"), FIXTURE, modelPlugin("sonnet", { enabled: false })]);
    await openDecision();

    expect(await within(place()).findByText(/꺼진 플러그인이 있어 재개할 수 없다/)).toBeTruthy();
    expect(place().textContent).toContain("모델 sonnet");
    expect(place().textContent).not.toContain("에이전트 calc");
    expect(button("승인").disabled).toBe(true);
    expect(button("거부").disabled).toBe(true);
  });

  test("에이전트가 고르지 않은 모델이 꺼진 것은 결정 버튼을 막지 않는다", async () => {
    serveTrace(() => PAUSED);
    servePlugins([
      calcUsing("sonnet"),
      FIXTURE,
      modelPlugin("sonnet", { enabled: true }),
      modelPlugin("opus", { enabled: false }),
    ]);
    await openDecision();

    // 목록을 읽은 뒤에도 막지 않는다.
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(place().textContent).not.toContain("꺼진 플러그인");
    expect(button("승인").disabled).toBe(false);
  });

  test("model 을 적지 않은 에이전트는 꺼진 모델이 있어도 미리 막지 않는다", async () => {
    serveTrace(() => PAUSED);
    servePlugins([calcUsing(null), FIXTURE, modelPlugin("sonnet", { enabled: false })]);
    await openDecision();

    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(place().textContent).not.toContain("꺼진 플러그인");
    expect(button("승인").disabled).toBe(false);
  });

  test("에이전트가 고른 모델의 행이 표지면 꺼짐으로 세지 않고 결정 버튼을 막지 않는다", async () => {
    serveTrace(() => PAUSED);
    servePlugins([
      calcUsing("sonnet"),
      FIXTURE,
      { kind: "model", name: "sonnet", enabled: false, reason: "매니페스트를 읽을 수 없다" },
    ]);
    await openDecision();

    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(place().textContent).not.toContain("꺼진 플러그인");
    expect(place().textContent).not.toContain("모델 sonnet");
    expect(button("승인").disabled).toBe(false);
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
    expect(button("승인").disabled).toBe(true);

    // SWR 은 마운트한 뒤 한동안(focusThrottleInterval) 포커스를 흘려보낸다. 그 너머로 민다.
    await vi.advanceTimersByTimeAsync(10_000);
    fireEvent.focus(window);

    await waitFor(() => {
      expect(button("승인").disabled).toBe(false);
    });
    expect(listed).toBe(3);
    expect(place().textContent).not.toContain("꺼진 플러그인이 있어");
    const notice = within(place())
      .getByText("플러그인 목록을 읽지 못해 꺼진 플러그인을 미리 알 수 없다")
      .closest('[role="status"]');
    expect(notice).not.toBeNull();
    expect(reason()).toHaveProperty("disabled", false);
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
    expect(button("승인").disabled).toBe(false);
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

    await user.click(button("승인"));

    const alert = await alertTitled("채널 토큰이 거부됐다");
    expect(alert.textContent).toContain("설정에서 다시 넣는다.");
    expect(precedes(alert, events())).toBe(true);
    // 알림에는 링크가 없고, 설정으로 가는 링크는 결정 칸이 바뀐 채널 토큰 안내 줄의 하나다.
    expect(within(alert).queryByRole("link")).toBeNull();
    expect(screen.getAllByText(NO_CHANNEL_TOKEN)).toHaveLength(1);
    expect(screen.getAllByRole("link", { name: "설정 열기" })).toHaveLength(1);
    expect(screen.getByRole("region", { name: EVENTS })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "승인" })).toBeNull();
    const stored = storedValues(sessionStorage).join("\n");
    expect(stored).toContain(ADMIN);
    expect(stored).not.toContain(CHANNEL);
  });
});
