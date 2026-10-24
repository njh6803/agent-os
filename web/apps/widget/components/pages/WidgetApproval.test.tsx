// 위젯의 승인 묻기(web-widget 티켓 08). 에이전트가 승인 대상 도구에서 멈추면 대화 안에 카드가 서서 도구와 인자의
// 원문을 보이고, 최종 사용자가 승인하거나 사유를 적어 거부하며, 결정의 거절마다 정한 길을 가는지를 화면에 보이는
// 글과 역할로 본다. 기대하는 문구는 명세(.scratch/web-widget/spec.md)의 "승인 묻기", "요청이 거절될 때"(경로가 "결정"인
// 행), "상한", "접근성" 절에서 그대로 옮겼다. 가짜는 HTTP(MSW)와 부모 창(testing/site.ts)뿐이다.

import { act, screen, waitFor, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { frame, gate, items, limited, rejection, stream, type Step } from "../../testing/network";
import { onTokenRequest, post, serveTokens } from "../../testing/site";
import {
  ask,
  findOutput,
  onDecide,
  onStart,
  onSubscribe,
  openWidget,
  requestBox,
  sendButton,
} from "../../testing/widget";

/** 받은 키 차례가 사전 차례와 다르고, 한글과 겹친 객체가 든 인자. */
const ARGS = {
  order_id: "ORD-2026-10-22-000184",
  amount: 18900,
  reason: "배송 지연",
  notify: { template: "refund-completed-v2", channel: "email" },
};

/** 멈춘 프레임의 `id`. 0 부터 센 항목의 수와 갈라, 결정의 `pause_index` 가 이 값에서 온 것을 가른다. */
const PAUSE_ID = 7;

/** 도구 하나를 부른 뒤 승인 대상 도구에서 멈추고 닫는 시작의 스트림. */
function pausedStart(...after: readonly Step[]): () => Response {
  return () =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      frame(1, { type: "calling", tools: ["orders.lookup"] }),
      frame(2, { type: "progress", tool: "orders.lookup", ok: true }),
      frame(3, { type: "calling", tools: ["payments.refund"] }),
      frame(PAUSE_ID, { type: "paused", tool: "payments.refund", args: ARGS }),
      ...after,
    ]);
}

/** 승인한 뒤 결정 항목부터 실행이 이어져 끝나는 결정 응답. */
function approvedThenFinished(...before: readonly Step[]): () => Response {
  return () =>
    stream([
      ...before,
      frame(8, { type: "decided", decision: "approve", reason: null }),
      frame(9, { type: "progress", tool: "payments.refund", ok: true }),
      frame(10, { type: "finished", output: "환불했습니다." }),
    ]);
}

function card(): HTMLElement {
  return screen.getByRole("group", { name: "승인 묻기" });
}

function approveButton(): HTMLElement {
  return within(card()).getByRole("button", { name: "승인" });
}

function denyButton(): HTMLElement {
  return within(card()).getByRole("button", { name: "거부" });
}

function reasonBox(): HTMLElement {
  return within(card()).getByRole("textbox", { name: "거부 사유" });
}

/** 입력창 위 띠. 숨긴 읽기 영역과 가르려고 입력 자리(form) 바로 앞의 것을 고른다. */
function band(): HTMLElement {
  const form = requestBox().closest("form");
  const element = form?.previousElementSibling;
  if (!(element instanceof HTMLElement) || element.getAttribute("role") !== "status") {
    throw new Error("입력창 위 띠가 없다");
  }
  return element;
}

/** 화면 읽기 프로그램이 듣는 띠의 글. 숨긴 숫자를 뺀다. */
function spoken(element: Element): string {
  const copy = element.cloneNode(true);
  if (!(copy instanceof Element)) {
    throw new Error("요소가 아니다");
  }
  for (const hidden of copy.querySelectorAll('[aria-hidden="true"]')) {
    hidden.remove();
  }
  return copy.textContent;
}

/** 카드가 설 때까지 요청을 보낸다. */
async function untilPaused(user: UserEvent): Promise<void> {
  await ask(user, "우산 값 환불해 주세요");
  await screen.findByRole("group", { name: "승인 묻기" });
}

async function advance(ms: number): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

/** 응답을 차례로 하나씩 낸다. */
function inTurn(...responses: readonly (() => Response)[]): () => Response {
  let next = 0;
  return () => {
    const respond = responses[next];
    next += 1;
    if (respond === undefined) {
      throw new Error("준비한 응답보다 요청이 많다");
    }
    return respond();
  };
}

// --- 카드 ---

test("paused 가 오면 진행 표시를 걷고 카드를 세워, 도구 이름을 고정폭 font-medium 으로 보인다", async () => {
  serveTokens();
  onStart(pausedStart());
  const user = openWidget();

  await untilPaused(user);

  expect(screen.queryByRole("progressbar")).toBeNull();
  expect(within(card()).getByText("승인이 필요합니다")).toBeTruthy();
  const tool = within(card()).getByText("payments.refund");
  expect(tool.className).toContain("font-mono");
  expect(tool.className).toContain("font-medium");
});

test("인자는 받은 키 차례, 두 칸 들여쓰기, 이스케이프하지 않은 한글의 JSON 글을 고치거나 줄이지 않고 보인다", async () => {
  serveTokens();
  onStart(pausedStart());
  const user = openWidget();

  await untilPaused(user);

  const args = within(card()).getByText((_, element) => element?.tagName === "PRE");
  expect(args.textContent).toBe(JSON.stringify(ARGS, null, 2));
  expect(args.textContent).toContain('"reason": "배송 지연"');
  expect(args.textContent.indexOf('"template"')).toBeLessThan(
    args.textContent.indexOf('"channel"'),
  );
  expect(args.className).toContain("font-mono");
});

test("승인하면 결정의 pause_index 는 paused 프레임의 id 이고, 그 실행에 토큰과 함께 보낸다", async () => {
  serveTokens("token-a");
  onStart(pausedStart());
  const decided = onDecide(approvedThenFinished());
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await findOutput("환불했습니다.");
  expect(decided).toHaveLength(1);
  expect(decided[0]?.url).toContain("/end-user/runs/run_1/approval");
  expect(decided[0]?.authorization).toBe("Bearer token-a");
  expect(decided[0]?.body).toEqual({ decision: "approve", pause_index: PAUSE_ID });
});

test("사유가 비면 '거부'가 막히고, 사유를 적으면 열려 그 사유를 적은 그대로 보낸다", async () => {
  serveTokens();
  onStart(pausedStart());
  const decided = onDecide(() =>
    stream([
      frame(8, { type: "decided", decision: "deny", reason: " 고객센터에 먼저 물어보겠습니다 " }),
      frame(9, { type: "progress", tool: "payments.refund", ok: false }),
      frame(10, { type: "finished", output: "환불을 요청하지 않았습니다." }),
    ]),
  );
  const user = openWidget();
  await untilPaused(user);
  expect(denyButton()).toHaveProperty("disabled", true);

  await user.type(reasonBox(), " 고객센터에 먼저 물어보겠습니다 ");
  expect(denyButton()).toHaveProperty("disabled", false);
  await user.click(denyButton());

  await findOutput("환불을 요청하지 않았습니다.");
  expect(decided[0]?.body).toEqual({
    decision: "deny",
    reason: " 고객센터에 먼저 물어보겠습니다 ",
    pause_index: PAUSE_ID,
  });
});

// 파이썬 str.strip() 이 지우는 글자. JS 의 trim() 은 U+001C~U+001F 와 U+0085 를 지우지 않고 U+FEFF 를 지운다.
for (const [label, reason, blocked] of [
  ["U+001C~U+001F 만 든 사유", "\u001c\u001d\u001e\u001f", true],
  ["U+0085 만 든 사유", "\u0085", true],
  ["U+3000 과 U+2028 만 든 사유", String.fromCodePoint(0x3000, 0x2028), true],
  ["U+FEFF 만 든 사유", String.fromCodePoint(0xfeff), false],
] as const) {
  test(`${label}는 '거부'가 ${blocked ? "막힌다" : "막히지 않는다"}`, async () => {
    serveTokens();
    onStart(pausedStart());
    const user = openWidget();
    await untilPaused(user);

    reasonBox().focus();
    await user.paste(reason);

    expect(reasonBox()).toHaveProperty("value", reason);
    expect(denyButton()).toHaveProperty("disabled", blocked);
  });
}

test("사유가 상한의 90% 이상이면 칸 아래에 센 수를, 넘으면 '20,000자를 넘었습니다'를 보이고 '거부'가 막힌다", async () => {
  serveTokens();
  onStart(pausedStart());
  const user = openWidget();
  await untilPaused(user);
  expect(within(card()).getByText("거부하려면 사유를 적어 주세요.")).toBeTruthy();

  reasonBox().focus();
  // 이모지 하나는 UTF-16 으로 둘이지만 코드 포인트로 하나다.
  await user.paste("😀".repeat(17_999));
  expect(within(card()).queryByText("17,999 / 20,000")).toBeNull();
  await user.paste("😀");
  expect(within(card()).getByText("18,000 / 20,000")).toBeTruthy();
  expect(denyButton()).toHaveProperty("disabled", false);

  await user.paste("😀".repeat(2_001));

  expect(within(card()).getByText("20,000자를 넘었습니다")).toBeTruthy();
  expect(denyButton()).toHaveProperty("disabled", true);
});

test("보내는 동안 두 버튼과 사유 칸이 막히고, decided 가 오면 걷혀 '승인했습니다' 한 줄이 남으며 실행이 이어진다", async () => {
  serveTokens();
  onStart(pausedStart());
  const hold = gate();
  onDecide(approvedThenFinished(hold.wait));
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await waitFor(() => {
    expect(approveButton().getAttribute("aria-busy")).toBe("true");
  });
  expect(denyButton()).toHaveProperty("disabled", true);
  expect(reasonBox()).toHaveProperty("disabled", true);

  hold.open();

  await findOutput("환불했습니다.");
  expect(within(card()).getByText("승인했습니다")).toBeTruthy();
  expect(within(card()).queryByRole("button")).toBeNull();
  expect(within(card()).queryByRole("textbox")).toBeNull();
});

test("승인이 닿으면 진행 표시의 이름표가 멈췄던 도구의 이름이다", async () => {
  serveTokens();
  onStart(pausedStart());
  const hold = gate();
  onDecide(() =>
    stream([
      frame(8, { type: "decided", decision: "approve", reason: null }),
      hold.wait,
      frame(9, { type: "progress", tool: "payments.refund", ok: true }),
      frame(10, { type: "finished", output: "환불했습니다." }),
    ]),
  );
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await screen.findByRole("progressbar", { name: "payments.refund 부르는 중" });
  hold.open();
  await findOutput("환불했습니다.");
});

function approvedFrames(): Step[] {
  return [
    frame(8, { type: "decided", decision: "approve", reason: null }),
    frame(9, { type: "progress", tool: "payments.refund", ok: true }),
    frame(10, { type: "finished", output: "환불했습니다." }),
  ];
}

test("거부하면 '거부했습니다: <사유>' 한 줄이 남는다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(() =>
    stream([
      frame(8, { type: "decided", decision: "deny", reason: "고객센터에 먼저 물어보겠습니다" }),
      frame(9, { type: "finished", output: "환불을 요청하지 않았습니다." }),
    ]),
  );
  const user = openWidget();
  await untilPaused(user);

  await user.type(reasonBox(), "고객센터에 먼저 물어보겠습니다");
  await user.click(denyButton());

  await findOutput("환불을 요청하지 않았습니다.");
  expect(within(card()).getByText("거부했습니다: 고객센터에 먼저 물어보겠습니다")).toBeTruthy();
  expect(within(card()).queryByRole("button")).toBeNull();
});

test("결정 응답이 다시 멈추면 그 뒤에 새 카드가 선다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(() =>
    stream([
      frame(8, { type: "decided", decision: "approve", reason: null }),
      frame(9, { type: "progress", tool: "payments.refund", ok: true }),
      frame(10, { type: "calling", tools: ["mail.send"] }),
      frame(11, { type: "paused", tool: "mail.send", args: { to: "고객" } }),
    ]),
  );
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await waitFor(() => {
    expect(screen.getAllByRole("group", { name: "승인 묻기" })).toHaveLength(2);
  });
  const [first, second] = screen.getAllByRole("group", { name: "승인 묻기" });
  expect(within(first ?? document.body).getByText("승인했습니다")).toBeTruthy();
  expect(within(second ?? document.body).getByText("mail.send")).toBeTruthy();
  expect(within(second ?? document.body).getByRole("button", { name: "승인" })).toBeTruthy();
});

// --- 입력창과 새 대화 ---

test("결정을 기다리는 동안 입력창과 보내기가 막히고 띠가 '승인이나 거부를 먼저 골라 주세요.'를 보인다", async () => {
  serveTokens();
  onStart(pausedStart());
  const user = openWidget();

  await untilPaused(user);

  expect(requestBox()).toHaveProperty("disabled", true);
  expect(sendButton()).toHaveProperty("disabled", true);
  expect(spoken(band())).toBe("승인이나 거부를 먼저 골라 주세요.");
});

test("결정한 뒤에는 띠가 걷힌다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(approvedThenFinished());
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await findOutput("환불했습니다.");
  expect(spoken(band())).toBe("");
  expect(requestBox()).toHaveProperty("disabled", false);
});

test("멈춘 실행을 기다릴 때 '새 대화'는 열려 있고, 누르면 묻지 않고 화면을 비워 다음 요청이 시작이 된다", async () => {
  serveTokens();
  const started = onStart(
    inTurn(pausedStart(), () =>
      items({ type: "started", run_id: "run_2" }, { type: "finished", output: "새로 시작" }),
    ),
  );
  const user = openWidget();
  await untilPaused(user);
  const newConversation = screen.getByRole("button", { name: "새 대화" });
  expect(newConversation).toHaveProperty("disabled", false);

  await user.click(newConversation);

  expect(screen.queryByRole("group", { name: "승인 묻기" })).toBeNull();
  expect(screen.queryByText("우산 값 환불해 주세요")).toBeNull();
  expect(spoken(band())).toBe("");
  await ask(user, "다시");
  await findOutput("새로 시작");
  expect(started).toHaveLength(2);
});

test("결정을 보내는 동안에는 '새 대화'가 막힌다", async () => {
  serveTokens();
  onStart(pausedStart());
  const hold = gate();
  onDecide(() => stream([hold.wait, ...approvedFrames()]));
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await waitFor(() => {
    expect(screen.getByRole("button", { name: "새 대화" })).toHaveProperty("disabled", true);
  });
  hold.open();
  await findOutput("환불했습니다.");
});

// --- 결정의 거절 ---

/** 카드 아래의 알림. 카드와 같은 항목 안에서 카드 뒤에 선다. */
function noticeBelowCard(role: "alert" | "status"): HTMLElement {
  const item = card().parentElement;
  if (item === null) {
    throw new Error("카드의 항목이 없다");
  }
  const notice = within(item).getByRole(role);
  expect(card().compareDocumentPosition(notice) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  return notice;
}

test("결정이 401 이면 카드 아래에 위험 알림 '로그인 정보를 받지 못했습니다.'가 서고 버튼이 다시 열린다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(() => rejection(401));
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await waitFor(() => {
    expect(noticeBelowCard("alert").textContent).toBe(
      "로그인 정보를 받지 못했습니다.페이지를 새로 고쳐 주세요.",
    );
  });
  expect(approveButton()).toHaveProperty("disabled", false);
  expect(approveButton().getAttribute("aria-busy")).toBeNull();
});

test("결정에 쓸 토큰을 받지 못하면 보내지 않고 401 과 같은 알림을 보이며 버튼이 다시 열린다", async () => {
  let asked = 0;
  onTokenRequest(({ id }) => {
    asked += 1;
    post({ type: "agent-os/token", id, token: asked === 1 ? "signed-token" : null });
  });
  onStart(pausedStart());
  const decided = onDecide(approvedThenFinished());
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await waitFor(() => {
    expect(noticeBelowCard("alert").textContent).toBe(
      "로그인 정보를 받지 못했습니다.페이지를 새로 고쳐 주세요.",
    );
  });
  expect(decided).toHaveLength(0);
  expect(approveButton()).toHaveProperty("disabled", false);
});

test("다시 고르면 앞의 알림이 걷힌다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(inTurn(() => rejection(500), approvedThenFinished()));
  const user = openWidget();
  await untilPaused(user);
  await user.click(approveButton());
  await waitFor(() => {
    expect(noticeBelowCard("alert")).toBeTruthy();
  });

  await user.click(approveButton());

  await findOutput("환불했습니다.");
  expect(screen.queryByRole("alert")).toBeNull();
});

test("결정이 404 면 1초 뒤 한 번 더 보내고, 받아들여지면 그대로 이어 간다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(pausedStart());
  const decided = onDecide(inTurn(() => rejection(404), approvedThenFinished()));
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());
  await waitFor(() => {
    expect(decided).toHaveLength(1);
  });
  // 가짜 시계와 함께 실제 시간도 흘러(shouldAdvanceTime) 1초에 꼭 맞춰 재지 않는다.
  await advance(900);
  expect(decided).toHaveLength(1);
  await advance(100);

  await findOutput("환불했습니다.");
  expect(decided).toHaveLength(2);
  expect(decided[1]?.body).toEqual(decided[0]?.body);
});

test("결정이 또 404 면 카드의 버튼과 사유 칸을 걷고 그 아래 정보 알림을 남기며 입력창을 연다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(pausedStart());
  const decided = onDecide(() => rejection(404));
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());
  await waitFor(() => {
    expect(decided).toHaveLength(1);
  });
  await advance(1_000);

  await waitFor(() => {
    expect(noticeBelowCard("status").textContent).toBe("이 승인 묻기는 더 이상 받을 수 없습니다.");
  });
  expect(decided).toHaveLength(2);
  expect(within(card()).queryByRole("button")).toBeNull();
  expect(within(card()).queryByRole("textbox")).toBeNull();
  expect(requestBox()).toHaveProperty("disabled", false);
  expect(spoken(band())).toBe("");
});

test("결정이 409 면 Last-Event-ID 를 일시정지 프레임의 id 로 두고 다시 구독해, 다른 탭의 결정을 따라간다", async () => {
  serveTokens();
  onStart(pausedStart());
  const decided = onDecide(() => rejection(409));
  const subscribed = onSubscribe(() => stream(approvedFrames()));
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await findOutput("환불했습니다.");
  expect(decided).toHaveLength(1);
  expect(subscribed).toHaveLength(1);
  expect(subscribed[0]?.url).toContain("/end-user/runs/run_1/subscription");
  expect(subscribed[0]?.lastEventId).toBe(String(PAUSE_ID));
  expect(within(card()).getByText("승인했습니다")).toBeTruthy();
  expect(screen.queryByRole("alert")).toBeNull();
});

test("결정이 409 이고 다시 구독한 스트림이 아무것도 없이 닫히면 카드 아래에 위험 알림을 보이고 버튼을 다시 연다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(() => rejection(409));
  onSubscribe(() => stream([]));
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await waitFor(() => {
    expect(noticeBelowCard("alert").textContent).toBe(
      "결정을 보내지 못했습니다.잠시 뒤 다시 골라 주세요.",
    );
  });
  expect(approveButton()).toHaveProperty("disabled", false);
  expect(within(card()).queryByText("승인했습니다")).toBeNull();
});

test("결정이 409 이고 다시 구독이 401 이면 카드 아래에 위험 알림 '로그인 정보를 받지 못했습니다.'가 서고 버튼이 다시 열린다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(() => rejection(409));
  onSubscribe(() => rejection(401));
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await waitFor(() => {
    expect(noticeBelowCard("alert").textContent).toBe(
      "로그인 정보를 받지 못했습니다.페이지를 새로 고쳐 주세요.",
    );
  });
  expect(approveButton()).toHaveProperty("disabled", false);
});

for (const [label, respond] of [
  ["422", () => rejection(422)],
  ["500", () => rejection(500)],
  ["표 밖의 상태 403", () => rejection(403)],
  ["응답 전의 네트워크 실패", () => Response.error()],
  ["decided 항목 전에 끝난 스트림", () => stream([])],
] as const) {
  test(`결정의 ${label} 는 카드 아래에 위험 알림 "요청을 처리하지 못했습니다."를 보이고 버튼을 다시 연다`, async () => {
    serveTokens();
    onStart(pausedStart());
    onDecide(respond);
    const user = openWidget();
    await untilPaused(user);

    await user.click(approveButton());

    await waitFor(() => {
      expect(noticeBelowCard("alert").textContent).toBe(
        "요청을 처리하지 못했습니다.잠시 뒤 다시 보내 주세요.",
      );
    });
    expect(approveButton()).toHaveProperty("disabled", false);
    expect(reasonBox()).toHaveProperty("disabled", false);
  });
}

test("결정이 이미 서버에 닿아 다시 고른 결정이 409 를 받으면 다시 구독해 그 결정을 따라간다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(
    inTurn(
      () => stream([]),
      () => rejection(409),
    ),
  );
  const subscribed = onSubscribe(() => stream(approvedFrames()));
  const user = openWidget();
  await untilPaused(user);
  await user.click(approveButton());
  await waitFor(() => {
    expect(noticeBelowCard("alert")).toBeTruthy();
  });

  await user.click(approveButton());

  await findOutput("환불했습니다.");
  expect(subscribed[0]?.lastEventId).toBe(String(PAUSE_ID));
});

test("결정이 429 면 띠가 상한의 문구를 '다시 고를 수 있습니다'로 끝맺고 그동안 결정 버튼을 막으며, 시간이 다 되면 저절로 보내지 않고 버튼을 다시 연다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(pausedStart());
  const decided = onDecide(() => limited("concurrent_runs", "2"));
  const user = openWidget();
  await untilPaused(user);
  await user.type(reasonBox(), "사유");

  await user.click(approveButton());

  await waitFor(() => {
    expect(spoken(band())).toBe(
      "동시에 처리할 수 있는 요청이 가득 찼습니다. 2초 뒤에 다시 고를 수 있습니다.",
    );
  });
  expect(approveButton()).toHaveProperty("disabled", true);
  expect(denyButton()).toHaveProperty("disabled", true);
  expect(screen.queryByRole("alert")).toBeNull();

  await advance(2_000);

  await waitFor(() => {
    expect(approveButton()).toHaveProperty("disabled", false);
  });
  expect(denyButton()).toHaveProperty("disabled", false);
  expect(spoken(band())).toBe("승인이나 거부를 먼저 골라 주세요.");
  expect(decided).toHaveLength(1);
});

test("시간당 상한의 429 도 분으로 적고 '다시 고를 수 있습니다'로 끝맺는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(pausedStart());
  onDecide(() => limited("hourly_runs", "720"));
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());

  await waitFor(() => {
    expect(spoken(band())).toBe(
      "한 시간 동안 받을 수 있는 요청 수에 닿았습니다. 12분 뒤에 다시 고를 수 있습니다.",
    );
  });
});

test("결정의 429 를 기다리는 동안 '새 대화'를 누르면 그 기다림이 걷혀 바로 요청을 보낼 수 있다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(pausedStart());
  onDecide(() => limited("hourly_runs", "720"));
  const user = openWidget();
  await untilPaused(user);
  await user.click(approveButton());
  await waitFor(() => {
    expect(spoken(band())).toContain("다시 고를 수 있습니다");
  });

  await user.click(screen.getByRole("button", { name: "새 대화" }));

  expect(spoken(band())).toBe("");
  expect(requestBox()).toHaveProperty("disabled", false);
});

// --- 접근성 ---

test("승인 묻기가 서면 포커스가 카드의 제목으로 가고, 결정한 뒤에는 결과 줄로 간다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(approvedThenFinished());
  const user = openWidget();

  await untilPaused(user);

  await waitFor(() => {
    expect(document.activeElement?.textContent).toBe("승인이 필요합니다");
  });

  await user.click(approveButton());

  await findOutput("환불했습니다.");
  expect(document.activeElement?.textContent).toBe("승인했습니다");
  // 입력창이 다시 열려도 포커스를 옮기지 않는다.
  expect(requestBox()).toHaveProperty("disabled", false);
  expect(document.activeElement).not.toBe(requestBox());
});

test("숨긴 읽기 영역이 새 도구 줄, 승인 묻기, 끝난 출력을 차례로 한 번씩 읽는다", async () => {
  serveTokens();
  onStart(pausedStart());
  onDecide(approvedThenFinished());
  const user = openWidget();
  await untilPaused(user);

  await user.click(approveButton());
  await findOutput("환불했습니다.");

  const region = screen
    .getAllByRole("status")
    .find((element) => element.getAttribute("aria-atomic") === "false");
  expect(
    Array.from(region?.querySelectorAll("p") ?? [], (paragraph) => paragraph.textContent),
  ).toEqual([
    "orders.lookup 성공",
    "승인이 필요합니다: payments.refund",
    "payments.refund 성공",
    "환불했습니다.",
  ]);
});

test("포커스 차례에 승인 카드가 대화 안의 버튼으로 들어 입력창보다 앞선다", async () => {
  serveTokens();
  onStart(pausedStart());
  const user = openWidget();
  await untilPaused(user);
  await user.type(reasonBox(), "사유");
  screen.getByRole("button", { name: "새 대화" }).focus();

  const order: string[] = [];
  for (let step = 0; step < 4; step += 1) {
    await user.tab();
    // 칸은 넣은 글로, 나머지는 이름(aria-label)이나 글로 가른다.
    const active = document.activeElement;
    order.push(
      active instanceof HTMLInputElement
        ? active.value
        : (active?.getAttribute("aria-label") ?? active?.textContent ?? ""),
    );
  }

  expect(order).toEqual(["대화", "사유", "거부", "승인"]);
});
