// 위젯이 에이전트의 출력을 디자인 시스템의 마크다운 부품으로 그리는지를 화면에 보이는 글과 역할로 본다(answer-markdown
// 티켓 03, ADR 0053). 입력마다 무엇이 그려지는지는 부품의 단위 시험(`packages/ui`)이 보므로, 여기서는 부품이 불렸다는 것과
// 위젯이 정한 자리(숨긴 "출력: ", 읽기 영역, 그리지 않는 글)만 둔다. 가짜는 HTTP(MSW)와 부모 창(testing/site.ts)뿐이다.

import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import { frame, items, stream } from "../../testing/network";
import { serveTokens } from "../../testing/site";
import { ask, onDecide, onStart, openWidget, reload, untilSaved } from "../../testing/widget";

/** 대화 영역. 읽기 영역과 입력창 위 띠를 뺀 화면이다. */
function conversation(): HTMLElement {
  return screen.getByRole("region", { name: "대화" });
}

/** 숨긴 읽기 영역. 대화 앞의 첫 status 다. */
function reader(): HTMLElement {
  const first = screen.getAllByRole("status")[0];
  if (first === undefined) {
    throw new Error("읽기 영역이 없다");
  }
  return first;
}

function finishedWith(output: string): () => Response {
  return () => items({ type: "started", run_id: "run_1" }, { type: "finished", output });
}

const RICH = [
  "## 배송 안내",
  "",
  "**도착** 예정은 [조회 페이지](https://example.com/track)에서 봅니다.",
  "",
  "| 칸 | 값 |",
  "| --- | --- |",
  "| 가 | 1 |",
].join("\n");

test("출력의 굵게가 strong 으로 그려지고 숨긴 '출력: ' 이 그 앞에 문단이 아닌 요소 안에 있다", async () => {
  serveTokens();
  onStart(finishedWith("**굵게** 로 쓴 답"));
  const user = openWidget();

  await ask(user, "요청");

  const strong = await within(conversation()).findByText("굵게", { selector: "strong" });
  const wrapper = strong.closest("p")?.parentElement?.parentElement;
  expect(wrapper?.tagName).toBe("DIV");
  expect(wrapper?.textContent).toBe("출력: 굵게 로 쓴 답");
  expect(wrapper?.firstElementChild?.className).toContain("sr-only");
});

test("읽기 영역에는 기호를 뗀 글이 문단 하나로 놓이고 제목과 표와 링크 요소가 없다", async () => {
  serveTokens();
  onStart(finishedWith(RICH));
  const user = openWidget();

  await ask(user, "요청");

  // 대화 영역에는 요소로 한 번씩 그려진다. 출력의 `##` 은 위젯 제목(h1)보다 낮은 h3 다.
  await within(conversation()).findByRole("heading", { level: 3, name: "배송 안내" });
  expect(within(conversation()).getByRole("table")).toBeTruthy();
  expect(within(conversation()).getAllByRole("link")).toHaveLength(1);
  // 읽기 영역은 글자만 낸다. 같은 제목, 표, 링크가 두 벌로 잡히지 않는다.
  const area = reader();
  expect(within(area).queryByRole("heading")).toBeNull();
  expect(within(area).queryByRole("table")).toBeNull();
  expect(within(area).queryByRole("link")).toBeNull();
  expect([...area.querySelectorAll("*")].map((element) => element.tagName)).toEqual(["P"]);
  const spoken = area.textContent;
  expect(spoken).toContain("배송 안내");
  expect(spoken).toContain("도착");
  expect(spoken).toContain("조회 페이지");
  expect(spoken).not.toMatch(/[*#|]/);
  expect(spoken).not.toContain("](");
});

test("도구 줄의 결과를 알리는 읽기 영역의 글은 글자 그대로 남는다", async () => {
  serveTokens();
  onStart(() =>
    items(
      { type: "started", run_id: "run_1" },
      { type: "progress", tool: "orders__lookup", ok: true },
      { type: "finished", output: "끝" },
    ),
  );
  const user = openWidget();

  await ask(user, "요청");

  await within(conversation()).findByText("끝", { selector: "p" });
  expect([...reader().querySelectorAll("p")].map((line) => line.textContent)).toEqual([
    "orders__lookup 성공",
    "끝",
  ]);
});

test("새로 고쳐 되돌린 이전 대화의 출력도 같은 부품으로 그린다", async () => {
  serveTokens();
  onStart(finishedWith("**굵게** 로 쓴 답"));
  const user = openWidget();
  await ask(user, "요청");
  await within(conversation()).findByText("굵게", { selector: "strong" });
  await untilSaved((saved) => {
    expect(saved).toContain("굵게");
  });

  reload();

  // 되돌리는 동안은 대화 자리에 진행 표시만 있어 영역이 서기를 기다린다.
  const strong = await screen.findByText("굵게", { selector: "strong" });
  expect(strong.closest("p")?.parentElement?.parentElement?.textContent).toBe(
    "출력: 굵게 로 쓴 답",
  );
  // 알림은 저장하지 않으므로 되돌린 화면의 읽기 영역은 비어 있다.
  expect(reader().textContent).toBe("");
});

test("내가 보낸 질문과 인사말은 별표와 밑줄이 든 글을 넣어도 글자 그대로 보인다", async () => {
  serveTokens();
  onStart(finishedWith("끝"));
  const user = openWidget("agent=order-helper&heading=주문 도우미&intro=**인사** 와 __밑줄__");
  expect(screen.getByText("**인사** 와 __밑줄__")).toBeTruthy();

  await ask(user, "**질문** 과 __밑줄__ 과 2*3*4");

  const request = await within(conversation()).findByText("**질문** 과 __밑줄__ 과 2*3*4");
  expect(request.querySelector("strong, em")).toBeNull();
});

test("승인 카드의 도구 인자는 별표와 밑줄이 들어 있어도 글자 그대로 보인다", async () => {
  serveTokens();
  onStart(() =>
    stream([
      frame(0, { type: "started", run_id: "run_1" }),
      frame(1, { type: "calling", tools: ["payments.refund"] }),
      frame(2, {
        type: "paused",
        tool: "payments.refund",
        args: { reason: "**배송** 지연 __init__" },
      }),
    ]),
  );
  onDecide(finishedWith("끝"));
  const user = openWidget();

  await ask(user, "요청");

  const card = await screen.findByRole("group", { name: "승인 묻기" });
  expect(card.textContent).toContain("**배송** 지연 __init__");
  expect(card.querySelector("strong, em")).toBeNull();
});
