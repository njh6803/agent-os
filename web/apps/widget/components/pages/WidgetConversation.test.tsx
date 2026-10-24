// iframe 위젯의 대화(web-widget 티켓 05). 최종 사용자가 요청을 보내면 위젯이 부모 창에서 토큰을 받아 최종 사용자
// 경로로 실행을 일으키고, 도는 동안 부르는 도구를 보이고, 출력을 받아 이어 가는지를 화면에 보이는 글과 역할로 본다.
// 가짜는 HTTP(MSW)와 부모 창(testing/site.ts)뿐이다.

import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http } from "msw";
import { expect, test, vi } from "vitest";
import {
  api,
  gate,
  items,
  KEEPALIVE,
  frame,
  network,
  rejection,
  stream,
} from "../../testing/network";
import { onTokenRequest, post, serveTokens } from "../../testing/site";
import { WidgetPage } from "./WidgetPage";

const QUERY = new URLSearchParams({ agent: "order-helper", heading: "주문 도우미" }).toString();

function openWidget(query = QUERY): UserEvent {
  window.history.replaceState(null, "", `/widget?${query}`);
  const user = userEvent.setup();
  render(<WidgetPage />);
  return user;
}

function requestBox(): HTMLElement {
  return screen.getByRole("textbox", { name: "요청" });
}

function sendButton(): HTMLElement {
  return screen.getByRole("button", { name: "보내기" });
}

/** 대화 목록에 선 출력. 읽기 영역의 같은 글과 가른다. */
function findOutput(text: string): Promise<HTMLElement> {
  return screen.findByText(text, { selector: "ol p" });
}

async function ask(user: UserEvent, text: string): Promise<void> {
  await user.type(requestBox(), text);
  await user.keyboard("{Enter}");
}

interface Seen {
  readonly url: string;
  readonly authorization: string | null;
  readonly body: unknown;
}

/** 시작 경로에 응답을 걸고, 받은 요청을 차례로 적어 돌려준다. */
function onStart(respond: () => Response): Seen[] {
  const seen: Seen[] = [];
  network.use(
    http.post(api("/runs"), async ({ request }) => {
      seen.push({
        url: request.url,
        authorization: request.headers.get("Authorization"),
        body: await request.json(),
      });
      return respond();
    }),
  );
  return seen;
}

function onContinue(respond: () => Response): Seen[] {
  const seen: Seen[] = [];
  network.use(
    http.post(api("/runs/:runId/continuation"), async ({ request }) => {
      seen.push({
        url: request.url,
        authorization: request.headers.get("Authorization"),
        body: await request.json(),
      });
      return respond();
    }),
  );
  return seen;
}

const FINISHED = () =>
  items({ type: "started", run_id: "run_1" }, { type: "finished", output: "도착 예정입니다." });

// --- 토큰 ---

test("보내면 부모 창에 새 id 의 토큰 요청을 대상 출처 * 로 보내고, 받은 토큰을 Authorization 으로 실어 자기 출처의 /end-user/runs 로 시작한다", async () => {
  const posted = vi.spyOn(window, "postMessage");
  const ids = serveTokens("token-a");
  const seen = onStart(FINISHED);
  const user = openWidget();

  await ask(user, "배송 어디쯤이에요?");

  await findOutput("도착 예정입니다.");
  expect(posted).toHaveBeenCalledWith({ type: "agent-os/token-request", id: ids[0] }, "*");
  expect(seen).toEqual([
    {
      url: `${location.origin}/end-user/runs`,
      authorization: "Bearer token-a",
      body: { agent: "order-helper", request: "배송 어디쯤이에요?" },
    },
  ]);
});

test("요청마다 토큰을 새로 묻고 그때 받은 토큰을 싣는다", async () => {
  const ids: string[] = [];
  onTokenRequest(({ id }) => {
    ids.push(id);
    post({ type: "agent-os/token", id, token: `token-${String(ids.length)}` });
  });
  const started = onStart(FINISHED);
  const continued = onContinue(FINISHED);
  const user = openWidget();

  await ask(user, "첫 요청");
  await findOutput("도착 예정입니다.");
  await ask(user, "둘째 요청");
  await waitFor(() => {
    expect(continued).toHaveLength(1);
  });

  expect(new Set(ids).size).toBe(2);
  expect(started[0]?.authorization).toBe("Bearer token-1");
  expect(continued[0]?.authorization).toBe("Bearer token-2");
});

test("부모가 아닌 창, 허용 밖 출처, 다른 id 의 답은 버리고 맞는 답의 토큰으로 보낸다", async () => {
  // 같은 페이지의 다른 iframe 이 보낸 것처럼 꾸민다.
  const frameElement = document.body.appendChild(document.createElement("iframe"));
  onTokenRequest(({ id }) => {
    post(
      { type: "agent-os/token", id, token: "from-other-window" },
      { source: frameElement.contentWindow },
    );
    post(
      { type: "agent-os/token", id, token: "from-other-origin" },
      { origin: "https://evil.example" },
    );
    post({ type: "agent-os/token", id: `${id}-x`, token: "for-other-request" });
    post({ type: "agent-os/token", id, token: "right" });
  });
  const seen = onStart(FINISHED);
  const user = openWidget();

  await ask(user, "요청");

  await findOutput("도착 예정입니다.");
  expect(seen.map((request) => request.authorization)).toEqual(["Bearer right"]);
});

test("허용 출처가 비면 부모의 답을 모두 버린다", async () => {
  vi.stubEnv("AGENT_OS_WIDGET_ORIGINS", "");
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  const user = openWidget();

  await ask(user, "요청");
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10_000);
  });

  expect((await screen.findByRole("alert")).textContent).toContain(
    "로그인 정보를 받지 못했습니다.",
  );
});

for (const [label, answer] of [
  ["토큰이 null 이면(거부)", null],
  ["토큰이 문자열이 아니면", 42],
] as const) {
  test(`${label} 요청을 보내지 않고 버튼 없는 위험 알림 "로그인 정보를 받지 못했습니다."를 보인다`, async () => {
    onTokenRequest(({ id }) => {
      post({ type: "agent-os/token", id, token: answer });
    });
    const user = openWidget();

    await ask(user, "요청");

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("로그인 정보를 받지 못했습니다.");
    expect(alert.textContent).toContain("페이지를 새로 고쳐 주세요.");
    expect(within(alert).queryByRole("button")).toBeNull();
  });
}

test("10초 안에 답이 없으면 요청을 보내지 않고 같은 알림을 보인다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  onTokenRequest(() => {});
  const user = openWidget();

  await ask(user, "요청");
  await act(async () => {
    await vi.advanceTimersByTimeAsync(9_900);
  });
  expect(screen.queryByRole("alert")).toBeNull();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(100);
  });

  expect((await screen.findByRole("alert")).textContent).toContain(
    "로그인 정보를 받지 못했습니다.",
  );
});

test("요청의 id 를 만들지 못하면(보안 맥락 밖이라 crypto.randomUUID 가 없을 때) 요청을 보내지 않고 같은 알림을 보인다", async () => {
  serveTokens();
  vi.spyOn(crypto, "randomUUID").mockImplementation(() => {
    throw new TypeError("crypto.randomUUID is not a function");
  });
  const user = openWidget();

  await ask(user, "요청");

  expect((await screen.findByRole("alert")).textContent).toContain(
    "로그인 정보를 받지 못했습니다.",
  );
});

test("서버의 401 도 버튼 없는 같은 알림이다", async () => {
  serveTokens();
  onStart(() => rejection(401));
  const user = openWidget();

  await ask(user, "요청");

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("로그인 정보를 받지 못했습니다.");
  expect(within(alert).queryByRole("button")).toBeNull();
});

// --- 보내기 ---

test("Enter 는 보내고 Shift+Enter 는 줄을 바꾸며, 한글을 조합하는 중의 Enter 는 보내지 않는다", async () => {
  serveTokens();
  const seen = onStart(FINISHED);
  const user = openWidget();

  await user.type(requestBox(), "첫 줄{Shift>}{Enter}{/Shift}둘째 줄");
  expect(requestBox()).toHaveProperty("value", "첫 줄\n둘째 줄");
  fireEvent.keyDown(requestBox(), { key: "Enter", isComposing: true });
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(seen).toEqual([]);

  await user.keyboard("{Enter}");

  await findOutput("도착 예정입니다.");
  expect(seen.map((request) => request.body)).toEqual([
    { agent: "order-helper", request: "첫 줄\n둘째 줄" },
  ]);
  expect(requestBox()).toHaveProperty("value", "");
});

test("보내기는 입력이 비었거나 앞뒤 공백만 있을 때 막힌다", async () => {
  const user = openWidget();

  expect(sendButton()).toHaveProperty("disabled", true);
  await user.type(requestBox(), "   ");
  expect(sendButton()).toHaveProperty("disabled", true);
  await user.type(requestBox(), "가");
  expect(sendButton()).toHaveProperty("disabled", false);
});

test("보내기는 설정이 잘못됐을 때 막힌다", () => {
  vi.spyOn(console, "error").mockImplementation(() => {});
  openWidget("heading=주문 도우미");

  expect(sendButton()).toHaveProperty("disabled", true);
});

test("글자 수가 상한의 90% 이상이면 센 수를, 넘으면 넘었다는 글을 입력창에 묶어 보이고 넘으면 보내기가 막힌다", async () => {
  vi.stubEnv("AGENT_OS_WIDGET_REQUEST_CHARS", "20");
  const user = openWidget();

  // 코드 포인트로 센다. 이모지 하나는 UTF-16 으로 둘이지만 하나다.
  await user.click(requestBox());
  await user.paste("가".repeat(17));
  expect(requestBox().getAttribute("aria-describedby")).toBeNull();

  await user.paste("😀");
  const count = document.getElementById(requestBox().getAttribute("aria-describedby") ?? "");
  expect(count?.textContent).toBe("18 / 20");
  expect(sendButton()).toHaveProperty("disabled", false);

  await user.paste("가".repeat(3));
  const over = document.getElementById(requestBox().getAttribute("aria-describedby") ?? "");
  expect(over?.textContent).toBe("20자를 넘었습니다");
  expect(requestBox().getAttribute("aria-invalid")).toBe("true");
  expect(sendButton()).toHaveProperty("disabled", true);
});

test("센 수와 상한은 천 단위로 끊어 적는다", async () => {
  const user = openWidget();

  await user.click(requestBox());
  await user.paste("a".repeat(19_850));

  expect(screen.getByText("19,850 / 20,000")).toBeTruthy();
});

// --- 진행 ---

test("calling 이 오면 줄의 첫 도구를 '부르는 중'으로 보이고, progress 가 같은 이름의 첫 것을 빼며, 줄이 비면 고정 문구다", async () => {
  serveTokens();
  const gates = [gate(), gate(), gate(), gate()];
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      gates[0]?.wait ?? "",
      frame(1, { type: "calling", tools: ["orders.lookup", "shipping.track"] }),
      gates[1]?.wait ?? "",
      frame(2, { type: "progress", tool: "orders.lookup", ok: true }),
      gates[2]?.wait ?? "",
      frame(3, { type: "progress", tool: "shipping.track", ok: false }),
      gates[3]?.wait ?? "",
      frame(4, { type: "finished", output: "끝" }),
    ]),
  );
  const user = openWidget();

  await ask(user, "요청");
  await screen.findByRole("progressbar", { name: "요청을 처리하고 있습니다." });
  gates[0]?.open();
  await screen.findByRole("progressbar", { name: "orders.lookup 부르는 중" });
  gates[1]?.open();
  await screen.findByRole("progressbar", { name: "shipping.track 부르는 중" });
  const tools = screen.getByRole("list", { name: "부른 도구" });
  expect(within(tools).getAllByRole("listitem")[0]?.textContent).toBe("orders.lookup성공");
  gates[2]?.open();
  await screen.findByRole("progressbar", { name: "요청을 처리하고 있습니다." });
  expect(screen.getByText("실패")).toBeTruthy();
  expect(sendButton()).toHaveProperty("disabled", true);
  gates[3]?.open();

  await findOutput("끝");
  expect(screen.queryByRole("progressbar")).toBeNull();
});

test("같은 이름이 줄에 둘이면 progress 는 첫 것 하나만 빼고, 거부의 decided 는 줄을 바꾸지 않으며 그 도구는 progress(실패)로 빠진다", async () => {
  serveTokens();
  const gates = [gate(), gate()];
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      frame(1, { type: "calling", tools: ["refunds.issue", "refunds.issue"] }),
      frame(2, { type: "progress", tool: "refunds.issue", ok: true }),
      frame(3, { type: "decided", decision: "deny", reason: "아니요" }),
      gates[0]?.wait ?? "",
      frame(4, { type: "progress", tool: "refunds.issue", ok: false }),
      gates[1]?.wait ?? "",
      frame(5, { type: "finished", output: "끝" }),
    ]),
  );
  const user = openWidget();

  await ask(user, "요청");
  await waitFor(() => {
    expect(
      screen.getAllByRole("listitem").some((item) => item.textContent === "refunds.issue성공"),
    ).toBe(true);
  });
  expect(screen.getByRole("progressbar", { name: "refunds.issue 부르는 중" })).toBeTruthy();
  gates[0]?.open();
  await screen.findByRole("progressbar", { name: "요청을 처리하고 있습니다." });
  gates[1]?.open();
  await findOutput("끝");
});

test("모델 없이 부른 도구의 progress 는 줄에 없어 그냥 지나가고 이름표는 고정 문구로 남는다", async () => {
  serveTokens();
  const hold = gate();
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      frame(1, { type: "progress", tool: "catalog.search", ok: true }),
      hold.wait,
      frame(2, { type: "finished", output: "끝" }),
    ]),
  );
  const user = openWidget();

  await ask(user, "요청");
  await screen.findByText("catalog.search");

  expect(screen.getByRole("progressbar", { name: "요청을 처리하고 있습니다." })).toBeTruthy();
  hold.open();
  await findOutput("끝");
});

test("keepalive 와 읽지 못한 프레임은 화면을 바꾸지 않는다", async () => {
  serveTokens();
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      KEEPALIVE,
      'data: {"type":"brand_new"}\nid: 1\n\n',
      frame(2, { type: "finished", output: "끝" }),
    ]),
  );
  const user = openWidget();

  await ask(user, "요청");

  await findOutput("끝");
  expect(screen.queryByRole("alert")).toBeNull();
});

test("결말이 오면 도구 줄이 '도구 N개를 불렀습니다' 버튼 한 줄로 접히고 누르면 aria-expanded 와 함께 펴진다", async () => {
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "calling", tools: ["orders.lookup"] },
      { type: "progress", tool: "orders.lookup", ok: true },
      { type: "calling", tools: ["shipping.track"] },
      { type: "progress", tool: "shipping.track", ok: false },
      { type: "finished", output: "끝" },
    ),
  );
  const user = openWidget();

  await ask(user, "요청");
  const summary = await screen.findByRole("button", { name: "도구 2개를 불렀습니다" });
  expect(summary.getAttribute("aria-expanded")).toBe("false");
  expect(screen.queryByRole("list", { name: "부른 도구" })).toBeNull();

  await user.click(summary);

  expect(summary.getAttribute("aria-expanded")).toBe("true");
  const rows = within(screen.getByRole("list", { name: "부른 도구" })).getAllByRole("listitem");
  expect(rows.map((row) => row.textContent)).toEqual(["orders.lookup성공", "shipping.track실패"]);
});

test("실패와 끝내지 못함의 결말에서도 도구 줄이 접히고, 도구 줄이 없는 실행에는 접힌 줄도 없다", async () => {
  serveTokens();
  let call = 0;
  onStart(() => {
    call += 1;
    return call === 1
      ? items(
          { type: "started", run_id: "run_1" },
          { type: "progress", tool: "orders.lookup", ok: true },
          { type: "unfinished" },
        )
      : items({ type: "started", run_id: "run_2" }, { type: "finished", output: "끝" });
  });
  const user = openWidget();

  await ask(user, "요청");
  await screen.findByRole("button", { name: "도구 1개를 불렀습니다" });
  await user.click(screen.getByRole("button", { name: "다시 보내기" }));

  await findOutput("끝");
  expect(screen.getAllByRole("button", { name: /불렀습니다$/ })).toHaveLength(1);
});

test("출력은 글자 그대로 그리고 HTML 조각은 글자로 보인다", async () => {
  serveTokens();
  const output = "첫 줄\n<b>굵게</b> **별표**";
  onStart(() => items({ type: "started", run_id: "run_1" }, { type: "finished", output }));
  const user = openWidget();

  await ask(user, "요청");

  const paragraph = await screen.findByText(
    (_, element) => element?.tagName === "P" && element.textContent === `출력: ${output}`,
  );
  expect(paragraph.querySelector("b")).toBeNull();
});

// --- 이어 가기와 새 대화 ---

test("끝난 실행이 있으면 다음 요청은 그 실행의 이어 가기이고, 실패한 교환은 이어 갈 실행을 바꾸지 않는다", async () => {
  serveTokens();
  const started = onStart(FINISHED);
  let call = 0;
  const continued = onContinue(() => {
    call += 1;
    return call === 1
      ? items(
          { type: "started", run_id: "run_2" },
          { type: "failed", message: "실패", run_id: "run_2", cause: "timeout" },
        )
      : items({ type: "started", run_id: "run_3" }, { type: "finished", output: "셋째 끝" });
  });
  const user = openWidget();

  await ask(user, "첫째");
  await findOutput("도착 예정입니다.");
  await ask(user, "둘째");
  await screen.findByRole("alert");
  await ask(user, "셋째");
  await findOutput("셋째 끝");

  expect(started).toHaveLength(1);
  expect(continued.map((request) => [request.url, request.body])).toEqual([
    [
      `${location.origin}/end-user/runs/run_1/continuation`,
      { agent: "order-helper", request: "둘째" },
    ],
    [
      `${location.origin}/end-user/runs/run_1/continuation`,
      { agent: "order-helper", request: "셋째" },
    ],
  ]);
});

test("'다시 보내기'는 같은 요청 글을 새 교환으로 덧붙이고 실패한 교환은 그대로 남는다", async () => {
  serveTokens();
  let call = 0;
  const seen = onStart(() => {
    call += 1;
    return call === 1 ? rejection(500) : FINISHED();
  });
  const user = openWidget();

  await ask(user, "환불 돼요?");
  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("요청을 처리하지 못했습니다.");
  expect(alert.textContent).toContain("잠시 뒤 다시 보내 주세요.");
  await user.click(within(alert).getByRole("button", { name: "다시 보내기" }));

  await findOutput("도착 예정입니다.");
  expect(seen.map((request) => request.body)).toEqual([
    { agent: "order-helper", request: "환불 돼요?" },
    { agent: "order-helper", request: "환불 돼요?" },
  ]);
  expect(screen.getAllByText("환불 돼요?")).toHaveLength(2);
  expect(screen.getByRole("alert").textContent).toContain("요청을 처리하지 못했습니다.");
});

test("앞 교환의 '다시 보내기'는 뒤 교환이 도는 동안 막히고 결말이 오면 열린다", async () => {
  serveTokens();
  const hold = gate();
  let call = 0;
  onStart(() => {
    call += 1;
    return call === 1
      ? rejection(500)
      : stream([
          frame(0, { type: "started", run_id: "run_1" }),
          hold.wait,
          frame(1, { type: "finished", output: "끝" }),
        ]);
  });
  const user = openWidget();

  await ask(user, "첫째");
  const retry = within(await screen.findByRole("alert")).getByRole("button", {
    name: "다시 보내기",
  });
  await ask(user, "둘째");
  await screen.findByRole("progressbar");
  expect(retry).toHaveProperty("disabled", true);
  hold.open();
  await findOutput("끝");
  expect(retry).toHaveProperty("disabled", false);
});

test("'새 대화'는 응답이 결말 전이면 막히고 끝나면 열리며, 누르면 묻지 않고 화면과 기억을 비워 다음 요청이 시작이 된다", async () => {
  serveTokens();
  const hold = gate();
  let call = 0;
  const started = onStart(() => {
    call += 1;
    return call === 1
      ? stream([
          frame(0, { type: "started", run_id: "run_1" }),
          hold.wait,
          frame(1, { type: "finished", output: "끝" }),
        ])
      : FINISHED();
  });
  const user = openWidget();
  const newConversation = screen.getByRole("button", { name: "새 대화" });

  await ask(user, "첫째");
  await screen.findByRole("progressbar");
  expect(newConversation).toHaveProperty("disabled", true);
  hold.open();
  await findOutput("끝");
  expect(newConversation).toHaveProperty("disabled", false);

  await user.click(newConversation);

  expect(screen.queryByText("첫째")).toBeNull();
  expect(screen.getByText("아래에 요청을 적어 보내 주세요.")).toBeTruthy();
  await ask(user, "둘째");
  await findOutput("도착 예정입니다.");
  expect(started).toHaveLength(2);
});

// MSW 3.0.0 에서 끊김은 읽는 쪽에만 닿아 핸들러에서 볼 수 없다(.scratch/web-admin/probes/msw_abort.mjs). 그래서 위젯이
// 낸 요청의 signal 을 바깥 경계에서 엿본다.
function spyRequests(): () => Request {
  const fetched = vi.spyOn(globalThis, "fetch");
  return () => {
    const request = fetched.mock.calls[0]?.[0];
    if (!(request instanceof Request)) {
      throw new Error("위젯이 Request 로 부르지 않았다");
    }
    return request;
  };
}

test("승인 묻기로 멈추면 진행 표시를 걷고 입력창과 보내기를 막아 두며, '새 대화'는 열려 누르면 열린 스트림을 끊는다", async () => {
  serveTokens();
  const firstRequest = spyRequests();
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      frame(1, { type: "calling", tools: ["refunds.issue"] }),
      frame(2, { type: "paused", tool: "refunds.issue", args: { amount: 1 } }),
      new Promise(() => {}),
    ]),
  );
  const user = openWidget();

  await ask(user, "환불해 주세요");
  await waitFor(() => {
    expect(screen.queryByRole("progressbar")).toBeNull();
  });
  expect(requestBox()).toHaveProperty("disabled", true);
  expect(sendButton()).toHaveProperty("disabled", true);
  const newConversation = screen.getByRole("button", { name: "새 대화" });
  expect(newConversation).toHaveProperty("disabled", false);
  const request = firstRequest();
  expect(request.signal.aborted).toBe(false);

  await user.click(newConversation);

  expect(request.signal.aborted).toBe(true);
  expect(screen.queryByText("환불해 주세요")).toBeNull();
  expect(requestBox()).toHaveProperty("disabled", false);
});

test("페이지를 떠나면 열린 스트림을 끊는다", async () => {
  serveTokens();
  const firstRequest = spyRequests();
  onStart(() => stream([frame(0, { type: "started", run_id: "run_1" }), new Promise(() => {})]));
  const user = openWidget();

  await ask(user, "요청");
  await screen.findByRole("progressbar");
  const request = firstRequest();
  expect(request.signal.aborted).toBe(false);

  cleanup();

  expect(request.signal.aborted).toBe(true);
});

// --- 틈 동안의 실패와 거절 ---

for (const [label, last] of [
  ["실패", { type: "failed", message: "실행이 실패했다", run_id: "run_1", cause: "timeout" }],
  ["끝내지 못함", { type: "unfinished" }],
] as const) {
  test(`${label} 항목은 "실행이 실패로 끝났습니다."와 "다시 보내기"의 위험 알림이다`, async () => {
    serveTokens();
    onStart(() => items({ type: "started", run_id: "run_1" }, last));
    const user = openWidget();

    await ask(user, "요청");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("실행이 실패로 끝났습니다.")).toBeTruthy();
    expect(within(alert).getByRole("button", { name: "다시 보내기" })).toBeTruthy();
    expect(alert.textContent).not.toContain("실행이 실패했다");
  });
}

for (const [label, respond] of [
  ["404", () => rejection(404)],
  ["409", () => rejection(409)],
  ["429", () => rejection(429)],
  ["500", () => rejection(500)],
  ["시작 항목 전에 끝난 스트림", () => stream([])],
  ["시작 항목 뒤에 결말 없이 끝난 스트림", () => items({ type: "started", run_id: "run_1" })],
] as const) {
  test(`${label} 는 "요청을 처리하지 못했습니다."와 "다시 보내기"의 위험 알림이다`, async () => {
    serveTokens();
    onStart(respond);
    const user = openWidget();

    await ask(user, "요청");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("요청을 처리하지 못했습니다.")).toBeTruthy();
    expect(within(alert).getByRole("button", { name: "다시 보내기" })).toBeTruthy();
  });
}

test("응답 전의 네트워크 실패도 같은 알림이다", async () => {
  serveTokens();
  network.use(http.post(api("/runs"), () => Response.error()));
  const user = openWidget();

  await ask(user, "요청");

  expect((await screen.findByRole("alert")).textContent).toContain("요청을 처리하지 못했습니다.");
});

// --- 접근성 ---

test("포커스 차례는 새 대화, 대화 영역, 대화 안의 버튼, 입력창, 보내기다", async () => {
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "progress", tool: "orders.lookup", ok: true },
      { type: "finished", output: "끝" },
    ),
  );
  const user = openWidget();
  await ask(user, "요청");
  await findOutput("끝");
  await user.type(requestBox(), "다음");
  (document.activeElement instanceof HTMLElement ? document.activeElement : document.body).blur();

  const order: (Element | null)[] = [];
  for (let step = 0; step < 5; step += 1) {
    await user.tab();
    order.push(document.activeElement);
  }

  expect(order).toEqual([
    screen.getByRole("button", { name: "새 대화" }),
    screen.getByRole("region", { name: "대화" }),
    screen.getByRole("button", { name: "도구 1개를 불렀습니다" }),
    requestBox(),
    sendButton(),
  ]);
});

test("숨긴 status 영역 하나가 새 도구 줄과 끝난 출력을 차례로 한 번씩 읽고 '부르는 중'은 읽지 않으며, 대화 목록에는 살아 있는 영역 속성이 없다", async () => {
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "calling", tools: ["orders.lookup", "shipping.track"] },
      { type: "progress", tool: "orders.lookup", ok: true },
      { type: "progress", tool: "shipping.track", ok: false },
      { type: "finished", output: "도착 예정입니다." },
    ),
  );
  const user = openWidget();

  await ask(user, "요청");
  await findOutput("도착 예정입니다.");

  const statuses = screen.getAllByRole("status");
  expect(statuses).toHaveLength(1);
  // role="status" 의 aria-atomic 은 기본이 true 라 끄지 않으면 문단이 붙을 때마다 영역 전체를 다시 읽는다.
  expect(statuses[0]?.getAttribute("aria-atomic")).toBe("false");
  const read = [...(statuses[0]?.querySelectorAll("p") ?? [])].map((line) => line.textContent);
  expect(read).toEqual(["orders.lookup 성공", "shipping.track 실패", "도착 예정입니다."]);
  const conversation = screen.getByRole("region", { name: "대화" });
  expect(conversation.closest("[aria-live], [role='log']")).toBeNull();
  expect(conversation.querySelector("[aria-live], [role='log']")).toBeNull();
});

test("새 대화는 읽기 영역도 비운다", async () => {
  serveTokens();
  onStart(FINISHED);
  const user = openWidget();

  await ask(user, "요청");
  await findOutput("도착 예정입니다.");
  await user.click(screen.getByRole("button", { name: "새 대화" }));

  expect(screen.getByRole("status").textContent).toBe("");
});
