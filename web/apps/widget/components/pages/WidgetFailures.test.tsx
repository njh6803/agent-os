// 위젯의 실패와 거절(web-widget 티켓 07). 실행이 실패하면 원인마다 정한 위험 알림이 서고, 시작이나 이어 가기가
// 거절되면 상태 코드마다 정한 길을 가며, 상한에 걸리면 입력창 위 띠가 기다릴 시간을 보이는지를 화면에 보이는 글과
// 역할로 본다. 기대하는 문구는 명세(.scratch/web-widget/spec.md)의 "실패 원인의 문구", "요청이 거절될 때", "상한"
// 절의 표에서 그대로 옮겼다. 가짜는 HTTP(MSW)와 부모 창(testing/site.ts)뿐이다.

import { act, cleanup, screen, waitFor, within } from "@testing-library/react";
import type { UserEvent } from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { frame, gate, items, limited, rejection, stream } from "../../testing/network";
import { serveTokens } from "../../testing/site";
import {
  ask,
  FINISHED,
  findOutput,
  onContinue,
  onStart,
  openWidget,
  requestBox,
  sendButton,
} from "../../testing/widget";

// --- 실패 원인의 알림 ---

const FAILURE_ROWS = [
  [
    "conversation_summary",
    "앞선 대화를 정리하지 못해 끝내지 못했습니다.",
    null,
    ["다시 보내기", "새 대화"],
  ],
  ["timeout", "정해진 시간 안에 끝나지 않았습니다.", null, ["다시 보내기", "새 대화"]],
  [
    "tool_connection",
    "에이전트가 쓰는 도구에 연결하지 못했습니다.",
    "잠시 뒤 다시 보내 주세요.",
    ["다시 보내기"],
  ],
  [
    "model_call",
    "에이전트가 모델을 부르지 못했습니다.",
    "잠시 뒤 다시 보내 주세요.",
    ["다시 보내기"],
  ],
  ["tool_failure", "도구가 실패했거나 거부되어 끝내지 못했습니다.", null, ["다시 보내기"]],
  ["loop_limit", "정해진 단계 안에 끝내지 못했습니다.", "요청을 나눠 보내 주세요.", []],
  ["resume_mismatch", "멈춘 실행을 이어서 끝내지 못했습니다.", null, ["다시 보내기"]],
  ["agent_code", "에이전트에 문제가 있어 끝내지 못했습니다.", null, ["다시 보내기"]],
  ["other", "실행이 실패로 끝났습니다.", null, ["다시 보내기"]],
  [null, "실행이 실패로 끝났습니다.", null, ["다시 보내기"]],
  ["brand_new_cause", "실행이 실패로 끝났습니다.", null, ["다시 보내기"]],
] as const;

for (const [cause, title, sentence, buttons] of FAILURE_ROWS) {
  test(`실패 원인 ${String(cause)} 는 message 를 그리지 않고 제목 "${title}", 본문, 실행 식별자 줄, 버튼 [${buttons.join(", ")}]의 위험 알림이다`, async () => {
    serveTokens();
    // 모르는 원인은 생성 타입으로 적을 수 없어 프레임의 바이트로 적는다.
    const failed = JSON.stringify({ type: "failed", message: "고정 문구", run_id: "run_7", cause });
    onStart(() =>
      stream([frame(0, { type: "started", run_id: "run_7" }), `data: ${failed}\nid: 1\n\n`]),
    );
    const user = openWidget();

    await ask(user, "요청");

    const alert = await screen.findByRole("alert");
    // 제목은 알림의 제목 자리에 홀로 선다.
    expect(within(alert).getByText(title)).toBeTruthy();
    expect(alert.textContent).toBe(
      `${title}${sentence ?? ""}실행 식별자: run_7${buttons.join("")}`,
    );
    expect(
      within(alert)
        .queryAllByRole("button")
        .map((button) => button.textContent),
    ).toEqual(buttons);
  });
}

test("loop_limit 의 실패가 오면 포커스가 입력창으로 간다", async () => {
  serveTokens();
  const hold = gate();
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      hold.wait,
      frame(1, { type: "failed", message: "고정 문구", run_id: "run_1", cause: "loop_limit" }),
    ]),
  );
  const user = openWidget();
  await ask(user, "요청");
  await screen.findByRole("progressbar");
  screen.getByRole("region", { name: "대화" }).focus();
  expect(document.activeElement).not.toBe(requestBox());

  hold.open();

  await screen.findByRole("alert");
  await waitFor(() => {
    expect(document.activeElement).toBe(requestBox());
  });
});

test("다른 원인의 실패는 포커스를 옮기지 않는다", async () => {
  serveTokens();
  const hold = gate();
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      hold.wait,
      frame(1, { type: "failed", message: "고정 문구", run_id: "run_1", cause: "timeout" }),
    ]),
  );
  const user = openWidget();
  await ask(user, "요청");
  await screen.findByRole("progressbar");
  const region = screen.getByRole("region", { name: "대화" });
  region.focus();

  hold.open();

  await screen.findByRole("alert");
  expect(document.activeElement).toBe(region);
});

test("알림의 '새 대화'는 화면과 기억을 비워 다음 요청이 시작이 된다", async () => {
  serveTokens();
  const started = onStart(FINISHED);
  onContinue(() =>
    items(
      { type: "started", run_id: "run_2" },
      { type: "failed", message: "고정 문구", run_id: "run_2", cause: "timeout" },
    ),
  );
  const user = openWidget();
  await ask(user, "첫째");
  await findOutput("도착 예정입니다.");
  await ask(user, "둘째");

  await user.click(
    within(await screen.findByRole("alert")).getByRole("button", { name: "새 대화" }),
  );

  expect(screen.queryByText("첫째")).toBeNull();
  expect(screen.getByText("아래에 요청을 적어 보내 주세요.")).toBeTruthy();
  await ask(user, "셋째");
  await findOutput("도착 예정입니다.");
  expect(started).toHaveLength(2);
});

test("포커스 차례에 알림의 버튼이 대화 안의 버튼으로 든다", async () => {
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "failed", message: "고정 문구", run_id: "run_1", cause: "timeout" },
    ),
  );
  const user = openWidget();
  await ask(user, "요청");
  const alert = await screen.findByRole("alert");
  await user.type(requestBox(), "다음");
  (document.activeElement instanceof HTMLElement ? document.activeElement : document.body).blur();

  const order: (Element | null)[] = [];
  for (let step = 0; step < 6; step += 1) {
    await user.tab();
    order.push(document.activeElement);
  }

  // 위쪽 띠의 "새 대화"가 문서의 처음이다.
  const [topBar] = screen.getAllByRole("button", { name: "새 대화" });
  expect(order).toEqual([
    topBar,
    screen.getByRole("region", { name: "대화" }),
    within(alert).getByRole("button", { name: "다시 보내기" }),
    within(alert).getByRole("button", { name: "새 대화" }),
    requestBox(),
    sendButton(),
  ]);
});

// --- 시작과 이어 가기의 거절 ---

/** 응답을 차례로 하나씩 낸다. 시작과 이어 가기가 함께 쓴다. */
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

function lastAlert(): HTMLElement {
  const alert = screen.getAllByRole("alert").at(-1);
  if (alert === undefined) {
    throw new Error("알림이 없다");
  }
  return alert;
}

function buttonsOf(alert: HTMLElement): (string | null)[] {
  return within(alert)
    .queryAllByRole("button")
    .map((button) => button.textContent);
}

test('시작의 404 는 요청을 남긴 채 버튼 없는 위험 알림 "이 에이전트를 찾을 수 없습니다."를 보이고 console.error 를 남긴다', async () => {
  serveTokens();
  const logged = vi.spyOn(console, "error").mockImplementation(() => {});
  const seen = onStart(() => rejection(404));
  const user = openWidget();

  await ask(user, "배송 어디쯤이에요?");

  const alert = await screen.findByRole("alert");
  expect(within(alert).getByText("이 에이전트를 찾을 수 없습니다.")).toBeTruthy();
  expect(alert.textContent).toBe("이 에이전트를 찾을 수 없습니다.사이트 관리자에게 알려 주세요.");
  expect(screen.getByText("배송 어디쯤이에요?")).toBeTruthy();
  expect(logged).toHaveBeenCalledTimes(1);
  expect(String(logged.mock.calls[0]?.[0])).toContain("order-helper");
  expect(seen).toHaveLength(1);
});

for (const path of ["시작", "이어 가기"] as const) {
  test(`${path}의 409 는 위험 알림 "에이전트를 지금 쓸 수 없습니다."와 "다시 보내기"다`, async () => {
    serveTokens();
    if (path === "시작") {
      onStart(() => rejection(409));
    } else {
      onStart(FINISHED);
      onContinue(() => rejection(409));
    }
    const user = openWidget();
    if (path === "이어 가기") {
      await ask(user, "첫째");
      await findOutput("도착 예정입니다.");
    }

    await ask(user, "요청");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("에이전트를 지금 쓸 수 없습니다.")).toBeTruthy();
    expect(alert.textContent).toBe(
      "에이전트를 지금 쓸 수 없습니다.잠시 뒤 다시 보내 주세요.다시 보내기",
    );
  });
}

for (const [label, respond] of [
  ["500", () => rejection(500)],
  ["표 밖의 상태 403", () => rejection(403)],
  ["표 밖의 상태 502", () => rejection(502)],
  ["응답 전의 네트워크 실패", () => Response.error()],
  ["시작 항목 전에 끝난 스트림", () => stream([])],
  // 재접속(티켓 09)이 들어오기 전까지의 틈. 09 가 이 행을 재접속으로 바꾼다.
  ["시작 항목 뒤에 결말 없이 끝난 스트림", () => items({ type: "started", run_id: "run_1" })],
] as const) {
  test(`${label} 는 요청을 남긴 채 위험 알림 "요청을 처리하지 못했습니다."와 "다시 보내기"다`, async () => {
    serveTokens();
    onStart(respond);
    const user = openWidget();

    await ask(user, "환불 돼요?");

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("요청을 처리하지 못했습니다.")).toBeTruthy();
    expect(alert.textContent).toBe(
      "요청을 처리하지 못했습니다.잠시 뒤 다시 보내 주세요.다시 보내기",
    );
    expect(screen.getByText("환불 돼요?")).toBeTruthy();
  });
}

test("처리하지 못한 거절이 같은 대화에서 세 번째로 거듭되면 '새 대화'도 달고, 결말을 받은 요청이 오면 셈이 처음으로 돌아간다", async () => {
  serveTokens();
  const respond = inTurn(
    () => rejection(500),
    () => Response.error(),
    () => stream([]),
    FINISHED,
    () => rejection(502),
    () => rejection(500),
    () => rejection(500),
  );
  onStart(respond);
  onContinue(respond);
  const user = openWidget();
  const seenButtons: (string | null)[][] = [];

  for (const request of ["1", "2", "3"]) {
    await ask(user, request);
    await waitFor(() => {
      expect(screen.getAllByRole("alert")).toHaveLength(seenButtons.length + 1);
    });
    seenButtons.push(buttonsOf(lastAlert()));
  }
  await ask(user, "4");
  await findOutput("도착 예정입니다.");
  for (const request of ["5", "6", "7"]) {
    await ask(user, request);
    await waitFor(() => {
      expect(screen.getAllByRole("alert")).toHaveLength(seenButtons.length + 1);
    });
    seenButtons.push(buttonsOf(lastAlert()));
  }

  expect(seenButtons).toEqual([
    ["다시 보내기"],
    ["다시 보내기"],
    ["다시 보내기", "새 대화"],
    ["다시 보내기"],
    ["다시 보내기"],
    ["다시 보내기", "새 대화"],
  ]);
});

/** 끝난 실행 하나를 두어 다음 요청이 그 실행의 이어 가기가 되게 한다. */
async function afterFinished(user: UserEvent): Promise<void> {
  await ask(user, "첫째");
  await findOutput("도착 예정입니다.");
}

async function advance(ms: number): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

test("이어 가기의 404 면 1초 뒤 같은 이어 가기를 한 번 더 보내고, 받아들여지면 그대로 이어 간다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(FINISHED);
  const continued = onContinue(
    inTurn(
      () => rejection(404),
      () => items({ type: "started", run_id: "run_2" }, { type: "finished", output: "둘째 끝" }),
    ),
  );
  const user = openWidget();
  await afterFinished(user);

  await ask(user, "둘째");
  await waitFor(() => {
    expect(continued).toHaveLength(1);
  });
  await advance(900);
  expect(continued).toHaveLength(1);
  await advance(100);

  await findOutput("둘째 끝");
  expect(continued.map((request) => [request.url, request.body])).toEqual([
    [
      `${location.origin}/end-user/runs/run_1/continuation`,
      { agent: "order-helper", request: "둘째" },
    ],
    [
      `${location.origin}/end-user/runs/run_1/continuation`,
      { agent: "order-helper", request: "둘째" },
    ],
  ]);
  expect(screen.getByText("첫째")).toBeTruthy();
  expect(screen.queryByRole("alert")).toBeNull();
});

test("이어 가기의 404 뒤 1초를 기다리는 동안 페이지를 떠나면 토큰을 다시 청하지 않고 더 보내지 않는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const tokenRequests = serveTokens();
  onStart(FINISHED);
  const continued = onContinue(() => rejection(404));
  const user = openWidget();
  await afterFinished(user);
  await ask(user, "둘째");
  await waitFor(() => {
    expect(continued).toHaveLength(1);
  });
  const asked = tokenRequests.length;

  cleanup();
  await advance(1_000);

  expect(tokenRequests).toHaveLength(asked);
  expect(continued).toHaveLength(1);
});

test("이어 가기가 또 404 면 화면과 기억을 비우고 정보 알림을 남긴 채 같은 요청을 시작으로 보낸다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  const started = onStart(
    inTurn(FINISHED, () =>
      items({ type: "started", run_id: "run_3" }, { type: "finished", output: "새로 끝" }),
    ),
  );
  onContinue(
    inTurn(
      () => rejection(404),
      () => rejection(404),
    ),
  );
  const user = openWidget();
  await afterFinished(user);

  await ask(user, "둘째");
  await advance(1_000);

  await findOutput("새로 끝");
  expect(started.map((request) => request.body)).toEqual([
    { agent: "order-helper", request: "첫째" },
    { agent: "order-helper", request: "둘째" },
  ]);
  expect(screen.queryByText("첫째")).toBeNull();
  expect(screen.queryByText("도착 예정입니다.")).toBeNull();
  // 정보 알림은 대화 안의 하나뿐인 status 다.
  const conversation = screen.getByRole("region", { name: "대화" });
  expect(within(conversation).getByRole("status").textContent).toBe(
    "이전 대화를 이어 갈 수 없어 새 대화로 시작합니다.",
  );
  expect(within(conversation).getByText("둘째")).toBeTruthy();
});

test("새 대화로 보낸 그 시작이 다시 404 면 시작의 404 행대로 하고 더 보내지 않는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  const logged = vi.spyOn(console, "error").mockImplementation(() => {});
  const started = onStart(inTurn(FINISHED, () => rejection(404)));
  const continued = onContinue(
    inTurn(
      () => rejection(404),
      () => rejection(404),
    ),
  );
  const user = openWidget();
  await afterFinished(user);

  await ask(user, "둘째");
  await advance(1_000);

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toBe("이 에이전트를 찾을 수 없습니다.사이트 관리자에게 알려 주세요.");
  await advance(5_000);
  expect(started).toHaveLength(2);
  expect(continued).toHaveLength(2);
  expect(logged).toHaveBeenCalledTimes(1);
});

for (const status of [422, 429] as const) {
  test(`새 대화로 보낸 그 시작이 ${String(status)} 면 정보 알림을 남긴 채 요청을 입력창으로 되돌린다`, async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    serveTokens();
    onStart(
      inTurn(FINISHED, () => (status === 422 ? rejection(422) : limited("concurrent_runs", "5"))),
    );
    onContinue(
      inTurn(
        () => rejection(404),
        () => rejection(404),
      ),
    );
    const user = openWidget();
    await afterFinished(user);

    await ask(user, "둘째");
    await advance(1_000);

    await waitFor(() => {
      expect(requestBox()).toHaveProperty("value", "둘째");
    });
    const conversation = screen.getByRole("region", { name: "대화" });
    expect(within(conversation).getByRole("status").textContent).toBe(
      "이전 대화를 이어 갈 수 없어 새 대화로 시작합니다.",
    );
    expect(screen.queryByText("첫째")).toBeNull();
    expect(screen.queryByText("둘째", { selector: "ol li" })).toBeNull();
  });
}

// --- 요청을 입력창으로 되돌리는 거절(422, 429) ---

const INVALID = "요청을 보낼 수 없습니다. 요청을 고쳐 다시 보내 주세요.";

for (const path of ["시작", "이어 가기"] as const) {
  test(`${path}의 422 는 요청을 대화에서 빼 입력창으로 되돌리고 그 아래 "${INVALID}"를 묶어 보인다`, async () => {
    serveTokens();
    if (path === "시작") {
      onStart(() => rejection(422));
    } else {
      onStart(FINISHED);
      onContinue(() => rejection(422));
    }
    const user = openWidget();
    if (path === "이어 가기") {
      await afterFinished(user);
    }

    await ask(user, "환불 돼요?");

    await waitFor(() => {
      expect(requestBox()).toHaveProperty("value", "환불 돼요?");
    });
    const note = document.getElementById(requestBox().getAttribute("aria-describedby") ?? "");
    expect(note?.textContent).toBe(INVALID);
    expect(screen.queryByText("환불 돼요?", { selector: "ol li" })).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(sendButton()).toHaveProperty("disabled", false);
  });
}

test("422 의 안내는 다음에 보낼 때 걷힌다", async () => {
  serveTokens();
  onStart(inTurn(() => rejection(422), FINISHED));
  const user = openWidget();
  await ask(user, "환불 돼요?");
  await waitFor(() => {
    expect(screen.getByText(INVALID)).toBeTruthy();
  });

  await user.keyboard("{Enter}");

  await findOutput("도착 예정입니다.");
  expect(screen.queryByText(INVALID)).toBeNull();
});

/** 입력창 위 띠의 자리. 대화 뒤, 입력창 앞의 status 다. */
function band(): HTMLElement {
  const statuses = screen.getAllByRole("status");
  const last = statuses.at(-1);
  if (
    last === undefined ||
    last.compareDocumentPosition(requestBox()) !== Node.DOCUMENT_POSITION_FOLLOWING
  ) {
    throw new Error("입력창 앞의 status 가 없다");
  }
  return last;
}

/** 화면 읽기 프로그램이 읽는 글. aria-hidden 인 것을 뺀다. */
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

/** 띠의 줄어드는 숫자. 화면 읽기 프로그램에서 숨는다. 같이 숨는 아이콘은 글이 없어 거른다. */
function countdown(): string | null {
  const hidden = Array.from(
    band().querySelectorAll('[aria-hidden="true"]'),
    (element) => element.textContent,
  );
  return hidden.find((text) => text !== "") ?? null;
}

for (const path of ["시작", "이어 가기"] as const) {
  test(`${path}의 429 는 요청을 대화에서 빼 입력창으로 되돌리고, 띠가 상한의 문구와 기다릴 시간을 보이며 보내기를 막는다`, async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    serveTokens();
    const limitedOnce = inTurn(() => limited("concurrent_runs", "5"));
    if (path === "시작") {
      onStart(limitedOnce);
    } else {
      onStart(FINISHED);
      onContinue(limitedOnce);
    }
    const user = openWidget();
    if (path === "이어 가기") {
      await afterFinished(user);
    }

    await ask(user, "환불 돼요?");

    await waitFor(() => {
      expect(requestBox()).toHaveProperty("value", "환불 돼요?");
    });
    expect(spoken(band())).toBe(
      "동시에 처리할 수 있는 요청이 가득 찼습니다. 5초 뒤에 다시 보낼 수 있습니다.",
    );
    expect(countdown()).toBe("5초");
    expect(screen.queryByText("환불 돼요?", { selector: "ol li" })).toBeNull();
    expect(sendButton()).toHaveProperty("disabled", true);
  });
}

test("띠의 숫자는 매초 줄고 aria-hidden 이며, 화면 읽기 프로그램에는 설 때 한 번과 시간이 다 되어 바뀔 때 한 번 읽힌다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  const started = onStart(inTurn(() => limited("concurrent_runs", "3")));
  const user = openWidget();
  const empty = spoken(band());

  await ask(user, "환불 돼요?");
  await waitFor(() => {
    expect(countdown()).toBe("3초");
  });
  const heard = [empty, spoken(band())];
  const counted = [countdown()];
  for (const step of [1_000, 1_000, 900, 100, 1_000]) {
    await advance(step);
    if (spoken(band()) !== heard.at(-1)) {
      heard.push(spoken(band()));
    }
    counted.push(countdown());
  }

  expect(heard).toEqual([
    "",
    "동시에 처리할 수 있는 요청이 가득 찼습니다. 3초 뒤에 다시 보낼 수 있습니다.",
    "이제 다시 보낼 수 있습니다.",
  ]);
  expect(counted).toEqual(["3초", "2초", "1초", "1초", null, null]);
  expect(started).toHaveLength(1);
});

test("시간이 다 되면 보내기가 열리고 저절로 다시 보내지 않으며, '이제 다시 보낼 수 있습니다.'는 다음에 보낼 때까지 남는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  const started = onStart(inTurn(() => limited("concurrent_runs", "2"), FINISHED));
  const user = openWidget();
  await ask(user, "환불 돼요?");
  await waitFor(() => {
    expect(countdown()).toBe("2초");
  });

  await advance(2_000);
  expect(sendButton()).toHaveProperty("disabled", false);
  await advance(10_000);
  expect(spoken(band())).toBe("이제 다시 보낼 수 있습니다.");
  expect(started).toHaveLength(1);

  await user.click(sendButton());

  await findOutput("도착 예정입니다.");
  expect(spoken(band())).toBe("");
  expect(started).toHaveLength(2);
});

for (const [label, limit, retryAfter, text] of [
  [
    "시간당 실행 수(hourly_runs)에 걸리면",
    "hourly_runs",
    "720",
    "한 시간 동안 받을 수 있는 요청 수에 닿았습니다. 12분 뒤에 다시 보낼 수 있습니다.",
  ],
  ["모르는 상한에 걸리면", "brand_new_limit", "7", "요청이 많아 7초 뒤에 다시 보낼 수 있습니다."],
  [
    "Retry-After 가 없으면",
    "concurrent_runs",
    null,
    "동시에 처리할 수 있는 요청이 가득 찼습니다. 5초 뒤에 다시 보낼 수 있습니다.",
  ],
  [
    "Retry-After 가 날짜라 읽지 못하면",
    "concurrent_runs",
    "Wed, 21 Oct 2026 07:28:00 GMT",
    "동시에 처리할 수 있는 요청이 가득 찼습니다. 5초 뒤에 다시 보낼 수 있습니다.",
  ],
  [
    "Retry-After 가 음수라 읽지 못하면",
    "concurrent_runs",
    "-3",
    "동시에 처리할 수 있는 요청이 가득 찼습니다. 5초 뒤에 다시 보낼 수 있습니다.",
  ],
  [
    "Retry-After 가 소수라 읽지 못하면",
    "concurrent_runs",
    "1.5",
    "동시에 처리할 수 있는 요청이 가득 찼습니다. 5초 뒤에 다시 보낼 수 있습니다.",
  ],
  ["Retry-After 가 0초면", "concurrent_runs", "0", "이제 다시 보낼 수 있습니다."],
  [
    "Retry-After 가 60초면",
    "concurrent_runs",
    "60",
    "동시에 처리할 수 있는 요청이 가득 찼습니다. 1분 뒤에 다시 보낼 수 있습니다.",
  ],
  [
    "Retry-After 가 61초면 분으로 올려",
    "hourly_runs",
    "61",
    "한 시간 동안 받을 수 있는 요청 수에 닿았습니다. 2분 뒤에 다시 보낼 수 있습니다.",
  ],
  [
    "Retry-After 가 59초면",
    "hourly_runs",
    "59",
    "한 시간 동안 받을 수 있는 요청 수에 닿았습니다. 59초 뒤에 다시 보낼 수 있습니다.",
  ],
] as const) {
  test(`${label} 띠가 "${text}"를 보인다`, async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    serveTokens();
    onStart(inTurn(() => limited(limit, retryAfter)));
    const user = openWidget();

    await ask(user, "환불 돼요?");

    await waitFor(() => {
      expect(spoken(band())).toBe(text);
    });
  });
}

test("분으로 적은 기다림이 60초 아래로 내려가면 초로 적는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(inTurn(() => limited("hourly_runs", "90")));
  const user = openWidget();
  await ask(user, "환불 돼요?");
  await waitFor(() => {
    expect(countdown()).toBe("2분");
  });

  await advance(30_000);
  expect(countdown()).toBe("1분");
  await advance(1_000);
  expect(countdown()).toBe("59초");
});

test("상한을 기다리는 동안 앞 교환의 '다시 보내기'도 막힌다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(
    inTurn(
      () => rejection(500),
      () => limited("concurrent_runs", "5"),
    ),
  );
  const user = openWidget();
  await ask(user, "첫째");
  const retry = within(await screen.findByRole("alert")).getByRole("button", {
    name: "다시 보내기",
  });

  await ask(user, "둘째");

  await waitFor(() => {
    expect(countdown()).toBe("5초");
  });
  expect(retry).toHaveProperty("disabled", true);
  await advance(5_000);
  expect(retry).toHaveProperty("disabled", false);
});

test("새 대화를 열어도 상한의 기다림은 남는다", async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  serveTokens();
  onStart(FINISHED);
  onContinue(inTurn(() => limited("concurrent_runs", "5")));
  const user = openWidget();
  await afterFinished(user);
  await ask(user, "둘째");
  await waitFor(() => {
    expect(countdown()).toBe("5초");
  });

  await user.click(screen.getByRole("button", { name: "새 대화" }));

  expect(screen.queryByText("도착 예정입니다.")).toBeNull();
  expect(spoken(band())).toBe(
    "동시에 처리할 수 있는 요청이 가득 찼습니다. 5초 뒤에 다시 보낼 수 있습니다.",
  );
  expect(sendButton()).toHaveProperty("disabled", true);
});

test('끝내지 못함은 제목 "실행을 끝내지 못했습니다.", 본문 "다시 보내 주세요."와 실행 식별자, "다시 보내기"의 위험 알림이다', async () => {
  serveTokens();
  onStart(() => items({ type: "started", run_id: "run_9" }, { type: "unfinished" }));
  const user = openWidget();

  await ask(user, "요청");

  const alert = await screen.findByRole("alert");
  expect(within(alert).getByText("실행을 끝내지 못했습니다.")).toBeTruthy();
  expect(alert.textContent).toBe(
    "실행을 끝내지 못했습니다.다시 보내 주세요.실행 식별자: run_9다시 보내기",
  );
});
