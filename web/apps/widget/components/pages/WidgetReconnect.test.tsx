// 위젯의 재접속(web-widget 티켓 09). 실행 도중 연결이 끊기면 받은 것을 둔 채 입력창 위 띠가 다시 잇는다고 말하고 같은
// 실행에 다시 붙는지, 새로 고친 뒤 돌거나 멈춘 실행에 처음부터 다시 붙는지, 구독이 거절되면 상태 코드마다 정한 길을
// 가는지를 화면에 보이는 글과 역할로 본다. 기대하는 규칙과 문구는 명세(.scratch/web-widget/spec.md)의 "재접속"과
// "요청이 거절될 때"의 구독 행에서 옮겼다.
//
// MSW 는 도중의 끊김을 만들지 못해(testing/network 의 머리 주석) 끊김은 결말 없이 닫는 것으로 만든다. 간격과 45초는
// 가짜 시계로 잰다. 시계를 돌리는 동안 실제 시간도 조금 흐르므로 간격은 초로 반올림해 견준다.

import { screen, waitFor, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { HttpResponse } from "msw";
import { expect, test, vi } from "vitest";
import { frame, gate, items, KEEPALIVE, limited, rejection, stream } from "../../testing/network";
import { answerTokens, serveTokens, siteToken } from "../../testing/site";
import {
  advance,
  ask,
  band,
  countdown,
  findOutput,
  inTurn,
  onDecide,
  onStart,
  onSubscribe,
  openWidget,
  reload,
  spoken,
  STORAGE_KEY,
  type Subscribed,
  untilSaved,
} from "../../testing/widget";

const CUT = "연결이 끊겨 다시 잇고 있습니다. 받은 내용은 그대로 있습니다.";
const WELCOME = "아래에 요청을 적어 보내 주세요.";
const EXPIRED = "이 승인 묻기는 더 이상 받을 수 없습니다.";
const SUBSCRIPTION = `${location.origin}/end-user/runs/run_1/subscription`;

function cutBand(): HTMLElement | null {
  return screen.queryByRole("progressbar", { name: CUT });
}

/** 시작 항목과 도구 줄 하나를 받고 결말 없이 닫힌다. 마지막 프레임의 `id` 는 1 이다. */
const CUT_AFTER_TOOL = () =>
  items(
    { type: "started", run_id: "run_1" },
    { type: "progress", tool: "orders.lookup", ok: true },
  );

/** 구독의 응답. 결말 하나를 `id` 로 내고 닫는다. */
function finishedAt(id: number, output = "도착 예정입니다."): () => Response {
  return () => stream([frame(id, { type: "finished", output })]);
}

/** 기다리는 시각부터 첫 구독과 그 뒤 구독들의 간격(초, 반올림). */
function gaps(from: number, subscribed: readonly { readonly at: number }[]): number[] {
  const times = [from, ...subscribed.map((request) => request.at)];
  return times.slice(1).map((at, index) => Math.round((at - (times[index] ?? at)) / 1_000));
}

// --- 끊김과 다시 잇기 ---

test("시작 항목 뒤에 결말 없이 닫히면 받은 도구 줄을 둔 채 띠가 다시 잇는다고 말하고, 1초 뒤 마지막 프레임의 id 로 구독해 이어 받는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens(siteToken("token-a"));
  onStart(CUT_AFTER_TOOL);
  const subscribed = onSubscribe(finishedAt(2));
  const user = openWidget();

  await ask(user, "주문 어디쯤?");

  expect(await screen.findByRole("progressbar", { name: CUT })).toBeTruthy();
  expect(within(band()).getByRole("progressbar", { name: CUT })).toBeTruthy();
  expect(screen.getByText("주문 어디쯤?")).toBeTruthy();
  expect(screen.getByText("orders.lookup")).toBeTruthy();
  // 끊긴 동안 목록에는 도구 줄만 남고 진행 표시는 띠가 맡는다(화면 디자인 mk-reconnect).
  expect(screen.queryByRole("progressbar", { name: "요청을 처리하고 있습니다." })).toBeNull();
  expect(screen.queryByText(/처리하지 못했습니다/)).toBeNull();
  expect(subscribed).toEqual([]);

  await advance(1_000);

  await findOutput("도착 예정입니다.");
  expect(
    subscribed.map(({ url, authorization, lastEventId }) => ({ url, authorization, lastEventId })),
  ).toEqual([
    { url: SUBSCRIPTION, authorization: `Bearer ${siteToken("token-a")}`, lastEventId: "1" },
  ]);
  expect(cutBand()).toBeNull();
});

test("다시 붙은 구독이 또 결말 없이 닫히면 그 구독의 마지막 프레임 id 로 다시 잇는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(CUT_AFTER_TOOL);
  const subscribed = onSubscribe(
    inTurn(
      () => stream([frame(2, { type: "progress", tool: "orders.track", ok: true })]),
      finishedAt(3),
    ),
  );
  const user = openWidget();
  await ask(user, "주문 어디쯤?");
  await screen.findByRole("progressbar", { name: CUT });

  await advance(1_000);
  await waitFor(() => {
    expect(screen.getByText("orders.track")).toBeTruthy();
  });
  await screen.findByRole("progressbar", { name: CUT });
  await advance(1_000);

  await findOutput("도착 예정입니다.");
  expect(subscribed.map((request) => request.lastEventId)).toEqual(["1", "2"]);
});

test("다시 잇는 간격은 1, 2, 4, 8, 16초이고 그 뒤로는 30초마다다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(CUT_AFTER_TOOL);
  // 받아들였지만 새 프레임 없이 닫히는 구독. 붙자마자 다시 끊긴다.
  const subscribed = onSubscribe(() => stream([]));
  const user = openWidget();
  await ask(user, "주문 어디쯤?");
  await screen.findByRole("progressbar", { name: CUT });
  const cutAt = Date.now();

  for (const [count, seconds] of [
    [1, 1],
    [2, 2],
    [3, 4],
    [4, 8],
    [5, 16],
    [6, 30],
    [7, 30],
  ] as const) {
    await advance(seconds * 1_000);
    await waitFor(() => {
      expect(subscribed).toHaveLength(count);
    });
  }

  expect(gaps(cutAt, subscribed)).toEqual([1, 2, 4, 8, 16, 30, 30]);
  expect(new Set(subscribed.map((request) => request.lastEventId))).toEqual(new Set(["1"]));
  expect(cutBand()).toBeTruthy();
});

test("45초 동안 프레임도 keepalive 도 오지 않으면 끊긴 것으로 보고, keepalive 가 오는 동안은 끊김으로 세지 않는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  const ping = gate();
  const never = gate();
  onStart(() =>
    stream([frame(0, { type: "started", run_id: "run_1" }), ping.wait, KEEPALIVE, never.wait]),
  );
  const subscribed = onSubscribe(finishedAt(1));
  const user = openWidget();
  await ask(user, "주문 어디쯤?");
  await screen.findByRole("progressbar", { name: "요청을 처리하고 있습니다." });

  await advance(40_000);
  ping.open();
  await advance(100);
  await advance(40_000);
  // 시작 항목에서 80초가 지났지만 keepalive 에서는 40초다.
  expect(cutBand()).toBeNull();

  await advance(5_000);

  expect(await screen.findByRole("progressbar", { name: CUT })).toBeTruthy();
  await advance(1_000);
  await findOutput("도착 예정입니다.");
  expect(subscribed.map((request) => request.lastEventId)).toEqual(["0"]);
});

test("승인 묻기 뒤에 닫힌 스트림은 끊김이 아니어서 띠도 구독도 없다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "paused", tool: "payments.refund", args: { amount: 18900 } },
    ),
  );
  const subscribed = onSubscribe(finishedAt(2));
  const user = openWidget();
  await ask(user, "환불해 주세요");
  await screen.findByRole("group", { name: "승인 묻기" });

  await advance(60_000);

  expect(cutBand()).toBeNull();
  expect(subscribed).toEqual([]);
});

test("결정 응답이 결정 항목 뒤에 결말 없이 닫히면 끊김이고, 그 응답의 마지막 프레임 id 로 다시 잇는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "paused", tool: "payments.refund", args: { amount: 18900 } },
    ),
  );
  onDecide(() =>
    stream([
      frame(2, { type: "decided", decision: "approve", reason: null }),
      frame(3, { type: "progress", tool: "payments.refund", ok: true }),
    ]),
  );
  const subscribed = onSubscribe(finishedAt(4, "환불했습니다."));
  const user = openWidget();
  await ask(user, "환불해 주세요");
  await screen.findByRole("group", { name: "승인 묻기" });

  await user.click(screen.getByRole("button", { name: "승인" }));

  expect(await screen.findByRole("progressbar", { name: CUT })).toBeTruthy();
  expect(screen.queryByText("결정을 보내지 못했습니다.")).toBeNull();
  await advance(1_000);
  await findOutput("환불했습니다.");
  expect(subscribed.map((request) => request.lastEventId)).toEqual(["3"]);
});

test("끊긴 동안 '새 대화'는 열려 있고, 누르면 화면을 비우고 다시 잇지 않는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(CUT_AFTER_TOOL);
  const subscribed = onSubscribe(finishedAt(2));
  const user = openWidget();
  await ask(user, "주문 어디쯤?");
  await screen.findByRole("progressbar", { name: CUT });

  const newConversation = screen.getByRole("button", { name: "새 대화" });
  expect(newConversation).toHaveProperty("disabled", false);
  await user.click(newConversation);
  await advance(60_000);

  expect(screen.getByText(WELCOME)).toBeTruthy();
  expect(cutBand()).toBeNull();
  expect(subscribed).toEqual([]);
  expect(sessionStorage.getItem(STORAGE_KEY)).toBeNull();
});

// --- 새로 고친 뒤 다시 붙기 ---

test("새로 고친 뒤 도는 실행에는 Last-Event-ID 없이 붙어 처음부터 받고, 도구 줄과 진행 표시의 이름표를 다시 짓는다", async () => {
  serveTokens(siteToken("token-a"));
  const first = gate();
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      frame(1, { type: "calling", tools: ["orders.lookup", "payments.refund"] }),
      frame(2, { type: "progress", tool: "orders.lookup", ok: true }),
      first.wait,
    ]),
  );
  const again = gate();
  const subscribed = onSubscribe(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      frame(1, { type: "calling", tools: ["orders.lookup", "payments.refund"] }),
      frame(2, { type: "progress", tool: "orders.lookup", ok: true }),
      again.wait,
      frame(3, { type: "progress", tool: "payments.refund", ok: true }),
      frame(4, { type: "finished", output: "환불했습니다." }),
    ]),
  );
  await ask(openWidget(), "환불해 주세요");
  await screen.findByRole("progressbar", { name: "payments.refund 부르는 중" });
  answerTokens(siteToken("token-b"));

  reload();

  expect(
    await screen.findByRole("progressbar", { name: "payments.refund 부르는 중" }),
  ).toBeTruthy();
  expect(screen.getByText("환불해 주세요")).toBeTruthy();
  expect(screen.getAllByText("orders.lookup")).toHaveLength(1);
  expect(cutBand()).toBeNull();
  expect(
    subscribed.map(({ url, authorization, lastEventId }) => ({ url, authorization, lastEventId })),
  ).toEqual([
    { url: SUBSCRIPTION, authorization: `Bearer ${siteToken("token-b")}`, lastEventId: null },
  ]);

  again.open();
  await findOutput("환불했습니다.");
});

test("새로 고친 뒤 멈춘 실행에 붙으면 승인 카드가 다시 서고, 그 카드로 결정을 보낸다", async () => {
  serveTokens();
  const paused = () =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "paused", tool: "payments.refund", args: { amount: 18900 } },
    );
  onStart(paused);
  const subscribed = onSubscribe(paused);
  const decided = onDecide(() =>
    stream([
      frame(2, { type: "decided", decision: "approve", reason: null }),
      frame(3, { type: "finished", output: "환불했습니다." }),
    ]),
  );
  await ask(openWidget(), "환불해 주세요");
  await screen.findByRole("group", { name: "승인 묻기" });

  const user = reload();

  const card = await screen.findByRole("group", { name: "승인 묻기" });
  expect(within(card).getByText("payments.refund")).toBeTruthy();
  expect(subscribed.map((request) => request.lastEventId)).toEqual([null]);
  expect(cutBand()).toBeNull();

  await user.click(within(card).getByRole("button", { name: "승인" }));

  await findOutput("환불했습니다.");
  expect(decided.map((request) => request.body)).toEqual([{ decision: "approve", pause_index: 1 }]);
});

test("새로 고친 뒤 끝난 실행만 있으면 구독하지 않는다", async () => {
  serveTokens();
  onStart(() =>
    items({ type: "started", run_id: "run_1" }, { type: "finished", output: "도착 예정입니다." }),
  );
  const subscribed = onSubscribe(finishedAt(2));
  await ask(openWidget(), "주문 어디쯤?");
  await findOutput("도착 예정입니다.");

  reload();

  await findOutput("도착 예정입니다.");
  expect(subscribed).toEqual([]);
});

test("결정이 두 번 404 여서 승인 묻기를 더 받을 수 없게 된 뒤 새로 고치면, 그 알림이 남고 구독하지 않는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "paused", tool: "payments.refund", args: { amount: 18900 } },
    ),
  );
  const decided = onDecide(() => rejection(404));
  const subscribed = onSubscribe(finishedAt(2));
  const user = openWidget();
  await ask(user, "환불해 주세요");
  const card = await screen.findByRole("group", { name: "승인 묻기" });
  await user.click(within(card).getByRole("button", { name: "승인" }));
  await waitFor(() => {
    expect(decided).toHaveLength(1);
  });
  await advance(1_000);
  await screen.findByText(EXPIRED);

  reload();

  expect(await screen.findByText(EXPIRED)).toBeTruthy();
  await advance(60_000);
  expect(subscribed).toEqual([]);
});

// --- 구독의 거절 ---

/** 끊긴 대화를 하나 세운다. 구독의 응답은 `respond` 다. 받은 구독 요청을 차례로 적어 돌려준다. */
async function afterCut(
  respond: () => Response,
): Promise<{ readonly subscribed: Subscribed[]; readonly user: UserEvent }> {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(CUT_AFTER_TOOL);
  const subscribed = onSubscribe(respond);
  const user = openWidget();
  await ask(user, "주문 어디쯤?");
  await screen.findByRole("progressbar", { name: CUT });
  return { subscribed, user };
}

test("구독이 401 이면 다시 잇기를 멈추고 버튼 없는 '로그인 정보를 받지 못했습니다.'를 보인다", async () => {
  const { subscribed } = await afterCut(() => rejection(401));

  await advance(1_000);

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toBe("로그인 정보를 받지 못했습니다.페이지를 새로 고쳐 주세요.");
  expect(within(alert).queryAllByRole("button")).toEqual([]);
  expect(cutBand()).toBeNull();
  await advance(60_000);
  expect(subscribed).toHaveLength(1);
});

test("다시 이을 때 토큰을 받지 못하면 구독을 보내지 않고 다시 잇기를 멈춘다", async () => {
  const { subscribed } = await afterCut(finishedAt(2));
  answerTokens(null);

  await advance(1_000);

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toBe("로그인 정보를 받지 못했습니다.페이지를 새로 고쳐 주세요.");
  expect(cutBand()).toBeNull();
  await advance(60_000);
  expect(subscribed).toEqual([]);
});

test("구독이 404 면 1초 뒤 한 번 더 보내고, 그것이 붙으면 이어 받는다", async () => {
  const { subscribed } = await afterCut(inTurn(() => rejection(404), finishedAt(2)));

  await advance(1_000);
  await waitFor(() => {
    expect(subscribed).toHaveLength(1);
  });
  await advance(1_000);

  await findOutput("도착 예정입니다.");
  expect(gaps(subscribed[0]?.at ?? 0, subscribed.slice(1))).toEqual([1]);
});

test("구독이 두 번 404 면 저장과 화면을 비우고 정보 알림을 남기며, 더 잇지 않는다", async () => {
  const { subscribed } = await afterCut(() => rejection(404));

  await advance(1_000);
  await waitFor(() => {
    expect(subscribed).toHaveLength(1);
  });
  await advance(1_000);

  expect(await screen.findByText("이전 대화를 이어 갈 수 없어 새 대화로 시작합니다.")).toBeTruthy();
  expect(screen.queryByText("주문 어디쯤?")).toBeNull();
  expect(screen.queryByText("orders.lookup")).toBeNull();
  expect(cutBand()).toBeNull();
  await untilSaved((value) => {
    expect(value).toBeNull();
  });
  await advance(60_000);
  expect(subscribed).toHaveLength(2);
});

test("구독의 404 사이에 다른 거절이 끼면 뒤의 404 는 다시 첫 404 라, 1초 뒤 한 번 더 보낸다", async () => {
  const { subscribed } = await afterCut(
    inTurn(
      () => rejection(404),
      () => rejection(500),
      () => rejection(404),
      finishedAt(2),
    ),
  );
  const cutAt = Date.now();

  await advance(1_000);
  await waitFor(() => {
    expect(subscribed).toHaveLength(1);
  });
  await advance(1_000);
  await waitFor(() => {
    expect(subscribed).toHaveLength(2);
  });
  await advance(2_000);
  await waitFor(() => {
    expect(subscribed).toHaveLength(3);
  });
  await advance(1_000);

  await findOutput("도착 예정입니다.");
  expect(screen.queryByText("이전 대화를 이어 갈 수 없어 새 대화로 시작합니다.")).toBeNull();
  expect(gaps(cutAt, subscribed)).toEqual([1, 1, 2, 1]);
});

test("구독이 409 면 곧바로 Last-Event-ID 없이 처음부터 구독하고, 이미 받은 프레임은 건너뛴다", async () => {
  const { subscribed } = await afterCut(
    inTurn(
      () => rejection(409),
      () =>
        items(
          { type: "started", run_id: "run_1" },
          { type: "progress", tool: "orders.lookup", ok: true },
          { type: "finished", output: "도착 예정입니다." },
        ),
    ),
  );

  await advance(1_000);

  await findOutput("도착 예정입니다.");
  expect(subscribed.map((request) => request.lastEventId)).toEqual(["1", null]);
  expect(gaps(subscribed[0]?.at ?? 0, subscribed.slice(1))).toEqual([0]);
  expect(screen.getByRole("button", { name: "도구 1개를 불렀습니다" })).toBeTruthy();
});

test("409 가 거듭되면 그 뒤의 것은 500 과 같아, 세 번째에 다시 잇기를 멈춘다", async () => {
  const { subscribed } = await afterCut(() => rejection(409));

  await advance(60_000);

  const alert = await screen.findByRole("alert");
  expect(within(alert).getByText("요청을 처리하지 못했습니다.")).toBeTruthy();
  expect(subscribed.map((request) => request.lastEventId)).toEqual(["1", null, null, null]);
  await advance(60_000);
  expect(subscribed).toHaveLength(4);
});

test("구독이 429 면 재접속 띠가 상한의 기다릴 시간을 보이고, 그 시간이 지나면 다시 구독한다", async () => {
  const { subscribed } = await afterCut(inTurn(() => limited("subscriptions", "7"), finishedAt(2)));

  await advance(1_000);

  await waitFor(() => {
    expect(spoken(band())).toBe("연결이 많아 7초 뒤에 다시 잇습니다. 받은 내용은 그대로 있습니다.");
  });
  expect(countdown()).toBe("7초");
  expect(cutBand()).toBeNull();
  await advance(3_000);
  expect(countdown()).toBe("4초");
  expect(subscribed).toHaveLength(1);

  await advance(4_000);

  await findOutput("도착 예정입니다.");
  expect(gaps(subscribed[0]?.at ?? 0, subscribed.slice(1))).toEqual([7]);
});

test("구독의 429 가 Retry-After 0 이어도 곧바로 되풀이하지 않고 재접속의 첫 간격인 1초 뒤에 다시 구독한다", async () => {
  // 서버는 1 이상만 보내지만 사이의 프록시가 0 을 보낼 수 있다.
  const { subscribed } = await afterCut(inTurn(() => limited("subscriptions", "0"), finishedAt(2)));

  await advance(1_000 + 1_000);

  await findOutput("도착 예정입니다.");
  expect(gaps(subscribed[0]?.at ?? 0, subscribed.slice(1))).toEqual([1]);
});

test("구독의 429 가 Retry-After 를 타이머가 받는 가장 긴 시간보다 길게 주어도 곧바로 되풀이하지 않는다", async () => {
  // 시험의 가짜 타이머는 2^31-1ms(약 24.8일)를 넘는 지연을 1ms 로 바꾼다. 3,000,000초는 그보다 길다.
  const { subscribed } = await afterCut(
    inTurn(() => limited("subscriptions", "3000000"), finishedAt(2)),
  );

  await advance(1_000 + 60_000);

  expect(subscribed).toHaveLength(1);
});

for (const [label, status] of [
  ["500", 500],
  ["422", 422],
  ["표 밖의 상태(503)", 503],
] as const) {
  test(`구독이 ${label}이면 재접속의 간격으로 다시 보내고, 세 번 거듭되면 멈춰 '새 대화'만 있는 위험 알림을 보인다`, async () => {
    const { subscribed, user } = await afterCut(() => rejection(status));
    const cutAt = Date.now();

    await advance(1_000 + 2_000 + 4_000);

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("요청을 처리하지 못했습니다.")).toBeTruthy();
    expect(within(alert).getByText("잠시 뒤 다시 보내 주세요.")).toBeTruthy();
    expect(
      within(alert)
        .getAllByRole("button")
        .map((button) => button.textContent),
    ).toEqual(["새 대화"]);
    expect(gaps(cutAt, subscribed)).toEqual([1, 2, 4]);
    expect(cutBand()).toBeNull();
    await advance(60_000);
    expect(subscribed).toHaveLength(3);

    await user.click(within(alert).getByRole("button", { name: "새 대화" }));

    expect(await screen.findByText(WELCOME)).toBeTruthy();
  });
}

/** 처음부터 받은 구독. 이미 받은 시작 항목과 도구 줄 뒤에 결말이 온다. */
const FROM_START = () =>
  items(
    { type: "started", run_id: "run_1" },
    { type: "progress", tool: "orders.lookup", ok: true },
    { type: "finished", output: "도착 예정입니다." },
  );

for (const [label, refusals, stopsAfter] of [
  ["500 이 세 번 거듭되어", [500, 500, 500], 1_000 + 2_000 + 4_000],
  ["401 이어서", [401], 1_000],
] as const) {
  test(`구독이 ${label} 다시 잇기를 멈춘 뒤 새로 고치면, 그 실행에 Last-Event-ID 없이 다시 붙는다`, async () => {
    const { subscribed } = await afterCut(
      inTurn(...refusals.map((status) => () => rejection(status)), FROM_START),
    );
    await advance(stopsAfter);
    await screen.findByRole("alert");

    reload();

    await findOutput("도착 예정입니다.");
    expect(screen.getByText("주문 어디쯤?")).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(subscribed.map((request) => request.lastEventId)).toEqual([
      ...refusals.map(() => "1"),
      null,
    ]);
  });
}

test("구독의 500 은 붙은 구독이 하나 오면 셈이 처음으로 돌아간다", async () => {
  const { subscribed } = await afterCut(
    inTurn(
      () => rejection(500),
      () => rejection(500),
      () => stream([frame(2, { type: "progress", tool: "orders.track", ok: true })]),
      () => rejection(500),
      () => rejection(500),
      finishedAt(3),
    ),
  );

  await advance(120_000);

  await findOutput("도착 예정입니다.");
  expect(subscribed).toHaveLength(6);
  expect(screen.queryByRole("alert")).toBeNull();
});

test("응답 전의 네트워크 실패는 끊긴 것과 같아 세지 않고 끝없이 다시 잇는다", async () => {
  const { subscribed } = await afterCut(
    inTurn(
      () => HttpResponse.error(),
      () => HttpResponse.error(),
      () => HttpResponse.error(),
      () => HttpResponse.error(),
      finishedAt(2),
    ),
  );
  const cutAt = Date.now();

  await advance(1_000 + 2_000 + 4_000 + 8_000);
  await waitFor(() => {
    expect(subscribed).toHaveLength(4);
  });
  expect(screen.queryByRole("alert")).toBeNull();
  expect(cutBand()).toBeTruthy();
  await advance(16_000);

  await findOutput("도착 예정입니다.");
  expect(gaps(cutAt, subscribed)).toEqual([1, 2, 4, 8, 16]);
});
