// 위젯의 저장(web-widget 티켓 09). 같은 탭에서 새로 고쳐도 대화가 남고, 새 탭은 새 대화로 시작하며, 같은 탭에서 사이트
// 계정이 바뀌면 앞 사람의 대화가 보이지 않는지를 화면에 보이는 글과 역할로 본다(스토리 12·14·15). 새로 고침은 그린 것을
// 걷고 같은 질의로 다시 그리는 것이고(testing/widget 의 `reload`), sessionStorage 는 한 테스트 안에서 남는다. 새 탭은 빈
// sessionStorage 다. 기대하는 규칙은 명세(.scratch/web-widget/spec.md)의 "저장" 절에서 옮겼다.
//
// 저장한 값의 글자는 두 자리에서만 본다. 명세가 이름을 정한 판 번호 필드(`version`)를 바꾸는 사례와, 모양 검사를 깨려고
// 고친 값을 다시 넣는 사례다. 용량은 sessionStorage 의 쓰기를 글자 수로 막는 흉내(`limitStorage`)로 만든다.

import { screen, waitFor, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { gate, items, rejection, stream, frame } from "../../testing/network";
import {
  answerTokens,
  ISSUER,
  onTokenRequest,
  post,
  removeTokenListeners,
  serveTokens,
  siteToken,
  SUBJECT,
} from "../../testing/site";
import {
  advance,
  ask,
  FINISHED,
  findOutput,
  inTurn,
  onContinue,
  onDecide,
  onStart,
  onSubscribe,
  openWidget,
  reload,
  requestBox,
  sendButton,
  STORAGE_KEY,
} from "../../testing/widget";

const WELCOME = "아래에 요청을 적어 보내 주세요.";

function finished(runId: string, output: string): () => Response {
  return () => items({ type: "started", run_id: runId }, { type: "finished", output });
}

/** 끝난 실행 하나(run_1)를 두고 그 출력이 선 것까지 기다린다. */
async function afterFinished(user: UserEvent, request = "첫째"): Promise<void> {
  await ask(user, request);
  await findOutput("도착 예정입니다.");
}

/** 긴 요청을 붙여 넣어 보낸다. 글자를 하나씩 치면 느리다. */
async function askLong(user: UserEvent, text: string): Promise<void> {
  await user.click(requestBox());
  await user.paste(text);
  await user.keyboard("{Enter}");
}

// --- 상태의 옮김과 다음 요청 ---

test("같은 탭에서 새로 고치면 끝난 교환이 도구 줄째 남고, 다음 요청은 마지막으로 끝난 실행의 이어 가기다", async () => {
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "progress", tool: "orders.lookup", ok: true },
      { type: "finished", output: "도착 예정입니다." },
    ),
  );
  const continued = onContinue(finished("run_2", "둘째 끝"));
  await afterFinished(openWidget());

  const user = reload();

  await findOutput("도착 예정입니다.");
  expect(screen.getByText("첫째")).toBeTruthy();
  await user.click(screen.getByRole("button", { name: "도구 1개를 불렀습니다" }));
  expect(screen.getByText("orders.lookup")).toBeTruthy();
  await ask(user, "둘째");
  await findOutput("둘째 끝");
  expect(continued.map((request) => request.url)).toEqual([
    `${location.origin}/end-user/runs/run_1/continuation`,
  ]);
});

test("실패와 끝내지 못함의 교환은 원인과 실행 식별자째 남고, 새로 고친 뒤 다시 붙지 않으며, 이어 갈 실행은 그대로다", async () => {
  serveTokens();
  onStart(FINISHED);
  const continued = onContinue(
    inTurn(
      () =>
        items(
          { type: "started", run_id: "run_2" },
          { type: "failed", message: "고정 문구", run_id: "run_2", cause: "timeout" },
        ),
      () => items({ type: "started", run_id: "run_3" }, { type: "unfinished" }),
      finished("run_4", "넷째 끝"),
    ),
  );
  let user = openWidget();
  await afterFinished(user);
  await ask(user, "둘째");
  await screen.findByText("정해진 시간 안에 끝나지 않았습니다.");
  await ask(user, "셋째");
  await screen.findByText("실행을 끝내지 못했습니다.");

  // 다시 붙을 실행이 비어 구독을 보내지 않는다. 보내면 처리하지 않은 요청으로 실패한다.
  user = reload();

  await screen.findByText("정해진 시간 안에 끝나지 않았습니다.");
  expect(screen.getByText("실행을 끝내지 못했습니다.")).toBeTruthy();
  expect(screen.getByText("run_2")).toBeTruthy();
  expect(screen.getByText("run_3")).toBeTruthy();
  await ask(user, "넷째");
  await findOutput("넷째 끝");
  expect(continued.map((request) => request.url)).toEqual(
    Array.from({ length: 3 }, () => `${location.origin}/end-user/runs/run_1/continuation`),
  );
});

// --- 새 탭과 묶음 견주기 ---

test("저장이 없으면(새 탭) 토큰을 묻지 않고 첫 화면을 그린다", async () => {
  const asked = serveTokens();
  openWidget();

  expect(await screen.findByText(WELCOME)).toBeTruthy();
  expect(asked).toEqual([]);
});

test("저장한 것이 있으면 토큰을 받아 견주기 전에는 진행 표시만 보이고, 같은 발급자와 sub 의 토큰이 오면 그린다", async () => {
  serveTokens();
  onStart(FINISHED);
  await afterFinished(openWidget());
  removeTokenListeners();
  const pending: string[] = [];
  onTokenRequest(({ id }) => {
    pending.push(id);
  });

  reload();

  await waitFor(() => {
    expect(pending).toHaveLength(1);
  });
  expect(screen.getByRole("progressbar", { name: "이전 대화를 불러오고 있습니다." })).toBeTruthy();
  expect(screen.queryByText("첫째")).toBeNull();
  expect(screen.queryByText(WELCOME)).toBeNull();
  expect(sendButton()).toHaveProperty("disabled", true);
  expect(screen.getByRole("button", { name: "새 대화" })).toHaveProperty("disabled", true);

  post({ type: "agent-os/token", id: pending[0], token: siteToken("again") });

  await findOutput("도착 예정입니다.");
  expect(screen.queryByRole("progressbar", { name: "이전 대화를 불러오고 있습니다." })).toBeNull();
});

for (const [label, claims] of [
  ["발급자", { iss: "https://other-shop.example", sub: SUBJECT }],
  ["sub", { iss: ISSUER, sub: "user-2" }],
] as const) {
  test(`새로 고친 뒤 받은 토큰의 ${label}가 저장한 것과 다르면 저장을 지우고 빈 화면으로 시작한다`, async () => {
    serveTokens();
    onStart(FINISHED);
    await afterFinished(openWidget());
    answerTokens(siteToken("other", claims));

    reload();

    expect(await screen.findByText(WELCOME)).toBeTruthy();
    expect(screen.queryByText("첫째")).toBeNull();
    expect(sessionStorage.getItem(STORAGE_KEY)).toBeNull();
  });
}

for (const [label, token] of [
  ["받지 못한 토큰", null],
  ["점이 없는 토큰", "not-a-jwt"],
  ["페이로드가 base64url 이 아닌 토큰", "eyJ.%%%.sig"],
  ["페이로드가 JSON 이 아닌 토큰", `x.${btoa("not json")}.sig`],
  ["sub 가 없는 토큰", siteToken("no-sub", { iss: ISSUER })],
  ["sub 가 글자가 아닌 토큰", siteToken("number-sub", { iss: ISSUER, sub: 7 })],
] as const) {
  test(`새로 고친 뒤 ${label}이면 저장을 지우지도 그리지도 않고 '로그인 정보를 받지 못했습니다.'를 보인다`, async () => {
    serveTokens();
    onStart(FINISHED);
    await afterFinished(openWidget());
    answerTokens(token);

    reload();

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe("로그인 정보를 받지 못했습니다.페이지를 새로 고쳐 주세요.");
    expect(within(alert).queryAllByRole("button")).toEqual([]);
    expect(screen.queryByText("첫째")).toBeNull();
    expect(screen.queryByText(WELCOME)).toBeNull();
    expect(sendButton()).toHaveProperty("disabled", true);
    expect(sessionStorage.getItem(STORAGE_KEY)).not.toBeNull();

    // 맞는 토큰을 받으면 그대로 그린다.
    answerTokens(siteToken());
    reload();
    await findOutput("도착 예정입니다.");
  });
}

test("토큰을 받지 못해 그리지 못한 화면에서 '새 대화'를 누르면 저장을 지우고 첫 화면으로 간다", async () => {
  serveTokens();
  onStart(FINISHED);
  await afterFinished(openWidget());
  answerTokens(null);
  const user = reload();
  await screen.findByRole("alert");

  await user.click(screen.getByRole("button", { name: "새 대화" }));

  expect(await screen.findByText(WELCOME)).toBeTruthy();
  expect(sessionStorage.getItem(STORAGE_KEY)).toBeNull();
});

test("요청을 보낼 때 받은 토큰의 sub 가 바뀌었으면 앞 대화를 지우고 그 요청을 새 대화의 시작으로 보낸다", async () => {
  serveTokens();
  const started = onStart(inTurn(FINISHED, finished("run_9", "새 사람의 답")));
  const user = openWidget();
  await afterFinished(user);
  answerTokens(siteToken("next", { iss: ISSUER, sub: "user-2" }));

  await ask(user, "둘째");

  await findOutput("새 사람의 답");
  expect(screen.queryByText("첫째")).toBeNull();
  expect(screen.queryByText("도착 예정입니다.")).toBeNull();
  expect(started.map((request) => request.body)).toEqual([
    { agent: "order-helper", request: "첫째" },
    { agent: "order-helper", request: "둘째" },
  ]);

  // 새로 고쳐도 새 사람의 대화만 남는다.
  reload();
  await findOutput("새 사람의 답");
  expect(screen.queryByText("첫째")).toBeNull();
});

test("결정을 보낼 때 받은 토큰의 sub 가 바뀌었으면 결정을 보내지 않고 저장과 화면을 비운다", async () => {
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "paused", tool: "payments.refund", args: { amount: 18900 } },
    ),
  );
  const decided = onDecide(() => rejection(500));
  const user = openWidget();
  await ask(user, "환불해 주세요");
  await screen.findByRole("group", { name: "승인 묻기" });
  answerTokens(siteToken("next", { iss: ISSUER, sub: "user-2" }));

  await user.click(screen.getByRole("button", { name: "승인" }));

  expect(await screen.findByText(WELCOME)).toBeTruthy();
  expect(decided).toEqual([]);
  expect(sessionStorage.getItem(STORAGE_KEY)).toBeNull();
});

// --- 용량 ---

/**
 * sessionStorage 의 쓰기를 키와 값의 글자 수 합으로 막는다. 넘으면 브라우저처럼 QuotaExceededError 를 던진다. 읽기와
 * 지우기는 같은 자리에 닿는다. 돌려준 함수로 한도를 바꾼다.
 */
function limitStorage(maxChars: number): (next: number) => void {
  let quota = maxChars;
  const kept = new Map<string, string>();
  vi.spyOn(Storage.prototype, "getItem").mockImplementation((key) => kept.get(key) ?? null);
  vi.spyOn(Storage.prototype, "setItem").mockImplementation((key, value) => {
    if (key.length + value.length > quota) {
      throw new DOMException("용량을 넘었다", "QuotaExceededError");
    }
    kept.set(key, value);
  });
  vi.spyOn(Storage.prototype, "removeItem").mockImplementation((key) => {
    kept.delete(key);
  });
  return (next) => {
    quota = next;
  };
}

const LONG_FIRST = "가".repeat(2_000);
const LONG_SECOND = "나".repeat(2_000);

test("저장이 용량을 넘으면 오래된 교환부터 빼고 남은 것을 저장한다", async () => {
  limitStorage(1_000);
  serveTokens();
  onStart(FINISHED);
  const continued = onContinue(inTurn(finished("run_2", "둘째 끝"), finished("run_3", "셋째 끝")));
  let user = openWidget();
  await askLong(user, LONG_FIRST);
  await findOutput("도착 예정입니다.");
  await ask(user, "둘째");
  await findOutput("둘째 끝");

  user = reload();

  await findOutput("둘째 끝");
  expect(screen.getByText("둘째")).toBeTruthy();
  expect(screen.queryByText(LONG_FIRST)).toBeNull();
  expect(screen.queryByText("도착 예정입니다.")).toBeNull();
  await ask(user, "셋째");
  await findOutput("셋째 끝");
  expect(continued.map((request) => request.url).at(-1)).toBe(
    `${location.origin}/end-user/runs/run_2/continuation`,
  );
});

test("교환을 다 빼도 넘으면 묶음과 run_id 만 두어, 새로 고친 뒤 빈 화면에서 보낸 요청이 마지막으로 끝난 실행의 이어 가기다", async () => {
  limitStorage(1_000);
  serveTokens();
  onStart(FINISHED);
  const continued = onContinue(inTurn(finished("run_2", "둘째 끝"), finished("run_3", "셋째 끝")));
  let user = openWidget();
  await askLong(user, LONG_FIRST);
  await findOutput("도착 예정입니다.");
  await askLong(user, LONG_SECOND);
  await findOutput("둘째 끝");

  user = reload();

  expect(await screen.findByText(WELCOME)).toBeTruthy();
  await ask(user, "셋째");
  await findOutput("셋째 끝");
  expect(continued.map((request) => request.url).at(-1)).toBe(
    `${location.origin}/end-user/runs/run_2/continuation`,
  );
});

test("다시 붙을 교환의 요청 글까지 빼면, 새로 고친 뒤 요청 글 없이 그 실행에 처음부터 다시 붙는다", async () => {
  limitStorage(1_000);
  serveTokens();
  const running = gate();
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      frame(1, { type: "progress", tool: "orders.lookup", ok: true }),
      running.wait,
    ]),
  );
  const subscribed = onSubscribe(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "progress", tool: "orders.lookup", ok: true },
      { type: "finished", output: "도착 예정입니다." },
    ),
  );
  await askLong(openWidget(), LONG_FIRST);
  await screen.findByText("orders.lookup");

  reload();

  await findOutput("도착 예정입니다.");
  expect(screen.queryByText(LONG_FIRST)).toBeNull();
  // 요청 상자는 화면 읽기 프로그램에 "요청: " 으로 시작한다. 빈 요청의 상자를 그리지 않는다.
  expect(screen.queryByText("요청:")).toBeNull();
  expect(subscribed.map((request) => request.lastEventId)).toEqual([null]);
});

test("묶음과 run_id 도 넘으면 앞서 저장한 것을 지우고 메모리로만 이어 간다", async () => {
  const setQuota = limitStorage(100_000);
  serveTokens();
  const started = onStart(inTurn(FINISHED, finished("run_5", "새로 끝")));
  const continued = onContinue(finished("run_2", "둘째 끝"));
  let user = openWidget();
  await afterFinished(user);
  expect(sessionStorage.getItem(STORAGE_KEY)).not.toBeNull();
  setQuota(10);

  // 메모리로는 이어 간다.
  await ask(user, "둘째");
  await findOutput("둘째 끝");
  expect(continued.map((request) => request.url)).toEqual([
    `${location.origin}/end-user/runs/run_1/continuation`,
  ]);
  expect(sessionStorage.getItem(STORAGE_KEY)).toBeNull();

  user = reload();

  expect(await screen.findByText(WELCOME)).toBeTruthy();
  await ask(user, "셋째");
  await findOutput("새로 끝");
  expect(started).toHaveLength(2);
});

// --- 판과 모양 ---

for (const [label, edit] of [
  ["판이 2 인", (value: string) => value.replace('"version":1', '"version":2')],
  ["판이 없는", (value: string) => value.replace('"version":1,', "")],
  ["JSON 이 아닌", (value: string) => value.slice(1)],
  ["sub 가 글자가 아닌", (value: string) => value.replace(`"sub":"${SUBJECT}"`, '"sub":7')],
  ["도구 줄의 성패가 참거짓이 아닌", (value: string) => value.replace('"ok":true', '"ok":"yes"')],
  ["교환이 배열이 아닌", (value: string) => value.replace(/"exchanges":\[.*\]/, '"exchanges":{}')],
] as const) {
  test(`${label} 저장은 토큰을 묻지 않고 지운 뒤 빈 화면으로 시작한다`, async () => {
    const asked = serveTokens();
    onStart(() =>
      items(
        { type: "started", run_id: "run_1" },
        { type: "progress", tool: "orders.lookup", ok: true },
        { type: "finished", output: "도착 예정입니다." },
      ),
    );
    await afterFinished(openWidget());
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved === null) {
      throw new Error("저장이 없다");
    }
    const broken = edit(saved);
    expect(broken).not.toBe(saved);
    sessionStorage.setItem(STORAGE_KEY, broken);
    const before = asked.length;

    reload();

    expect(await screen.findByText(WELCOME)).toBeTruthy();
    expect(screen.queryByText("첫째")).toBeNull();
    expect(sessionStorage.getItem(STORAGE_KEY)).toBeNull();
    expect(asked).toHaveLength(before);
  });
}

// --- 저장하지 않는 것 ---

test("시작 항목 전에 거절된 요청과 그 알림, 입력창의 글은 저장하지 않는다", async () => {
  serveTokens();
  onStart(FINISHED);
  onContinue(() => rejection(409));
  const user = openWidget();
  await afterFinished(user);
  await ask(user, "둘째");
  await screen.findByText("에이전트를 지금 쓸 수 없습니다.");
  await user.type(requestBox(), "쓰던 글");

  reload();

  await findOutput("도착 예정입니다.");
  expect(screen.queryByText("둘째")).toBeNull();
  expect(screen.queryByText("에이전트를 지금 쓸 수 없습니다.")).toBeNull();
  expect(requestBox()).toHaveProperty("value", "");
});

test("이어 가기의 마지막 404 는 그 순간 저장도 비우고, 그 뒤에 남긴 정보 알림은 저장하지 않는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  const restart = gate();
  onStart(
    inTurn(FINISHED, () =>
      stream([
        restart.wait,
        frame(0, { type: "started", run_id: "run_3" }),
        frame(1, { type: "finished", output: "새로 끝" }),
      ]),
    ),
  );
  onContinue(() => rejection(404));
  let user = openWidget();
  await afterFinished(user);
  await ask(user, "둘째");
  await advance(1_000);
  await screen.findByText("이전 대화를 이어 갈 수 없어 새 대화로 시작합니다.");
  expect(sessionStorage.getItem(STORAGE_KEY)).toBeNull();
  restart.open();
  await findOutput("새로 끝");

  user = reload();

  await findOutput("새로 끝");
  expect(screen.getByText("둘째")).toBeTruthy();
  expect(screen.queryByText("첫째")).toBeNull();
  expect(screen.queryByText("이전 대화를 이어 갈 수 없어 새 대화로 시작합니다.")).toBeNull();
  expect(user).toBeTruthy();
});

test("'새 대화'는 저장도 비워, 새로 고치면 첫 화면이고 다음 요청은 시작이다", async () => {
  serveTokens();
  const started = onStart(inTurn(FINISHED, finished("run_2", "새로 끝")));
  let user = openWidget();
  await afterFinished(user);

  await user.click(screen.getByRole("button", { name: "새 대화" }));
  expect(sessionStorage.getItem(STORAGE_KEY)).toBeNull();
  user = reload();

  expect(await screen.findByText(WELCOME)).toBeTruthy();
  await ask(user, "둘째");
  await findOutput("새로 끝");
  expect(started).toHaveLength(2);
});
