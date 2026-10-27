// iframe 페이지의 첫 화면(web-widget 티켓 03). 사이트가 iframe 의 질의로 준 설정을 읽어 무엇을 그리고, 문서 뿌리에
// 무엇을 달고, 무엇을 console.error 로 남기는지 본다. 질의를 읽는 규칙의 세부는 lib/embed.test.ts 가 잰다.

import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { WidgetPage } from "./WidgetPage";

/** 그 질의로 iframe 페이지를 연다. 위젯이 남긴 console.error 를 돌려준다. */
function openWidget(query: string): string[] {
  window.history.replaceState(null, "", `/widget?${query}`);
  const errors: string[] = [];
  vi.spyOn(console, "error").mockImplementation((...args: unknown[]) => {
    errors.push(args.map(String).join(" "));
  });
  render(<WidgetPage />);
  return errors;
}

function rootAttributes() {
  const { theme, mode, density } = document.documentElement.dataset;
  return { theme, mode, density };
}

test("첫 화면은 위쪽 띠에 이름과 새 대화를, 대화 자리에 할 수 있는 일과 안내를, 아래에 입력창과 보내기를 보인다", () => {
  const errors = openWidget(
    new URLSearchParams({
      agent: "order-helper",
      heading: "주문 도우미",
      intro: "주문, 배송, 환불을 물어볼 수 있습니다.",
    }).toString(),
  );

  expect(screen.getByRole("heading", { name: "주문 도우미" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "새 대화" })).toBeTruthy();
  expect(screen.getByText("주문, 배송, 환불을 물어볼 수 있습니다.")).toBeTruthy();
  expect(screen.getByText("아래에 요청을 적어 보내 주세요.")).toBeTruthy();
  expect(screen.getByRole("textbox", { name: "요청" })).toHaveProperty("disabled", false);
  // 입력이 비어 보내기는 막혀 있다(티켓 05). 글을 넣으면 열리는 것은 WidgetConversation.test.tsx 가 본다.
  expect(screen.getByRole("button", { name: "보내기" })).toHaveProperty("disabled", true);
  expect(screen.queryByRole("alert")).toBeNull();
  expect(errors).toEqual([]);
});

test("할 수 있는 일을 주지 않으면 그 줄 없이 안내만 보이고, 이름을 주지 않으면 에이전트 이름을 보인다", () => {
  openWidget("agent=order-helper");

  expect(screen.getByRole("heading", { name: "order-helper" })).toBeTruthy();
  const conversation = screen.getByRole("main");
  expect(conversation.querySelectorAll("p")).toHaveLength(1);
  expect(conversation.textContent).toBe("아래에 요청을 적어 보내 주세요.");
});

for (const [label, query] of [
  ["에이전트가 없으면", "heading=주문 도우미"],
  ["에이전트가 플러그인 이름의 패턴 밖이면", "agent=Order Helper"],
] as const) {
  test(`${label} 대화 자리에 위험 알림을 보이고 입력을 막으며 agent 를 든 console.error 를 남긴다`, () => {
    const errors = openWidget(query);

    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("위젯 설정이 올바르지 않습니다.");
    expect(alert.textContent).toContain("사이트 관리자에게 알려 주세요.");
    expect(screen.queryByText("아래에 요청을 적어 보내 주세요.")).toBeNull();
    expect(screen.getByRole("textbox", { name: "요청" })).toHaveProperty("disabled", true);
    expect(screen.getByRole("button", { name: "보내기" })).toHaveProperty("disabled", true);
    expect(errors).toEqual([expect.stringContaining("위젯 질의 agent")]);
  });
}

test("에이전트도 이름도 주지 않으면 위쪽 띠에 빈 제목을 두지 않고 새 대화만 선다", () => {
  openWidget("intro=주문을 물어보세요");

  expect(screen.queryByRole("heading")).toBeNull();
  expect(screen.getByRole("button", { name: "새 대화" })).toBeTruthy();
  expect(screen.getByRole("alert")).toBeTruthy();
});

test("테마와 모드를 주면 문서 뿌리에 그 테마와 모드, 보통 밀도를 단다", () => {
  openWidget("agent=order-helper&theme=jacho&mode=dark");

  expect(rootAttributes()).toEqual({ theme: "jacho", mode: "dark", density: "regular" });
});

test("모드를 주지 않으면 문서 뿌리에 모드를 달지 않아 시스템 설정을 따른다", () => {
  openWidget("agent=order-helper");

  expect(rootAttributes()).toEqual({ theme: "nokcheong", mode: undefined, density: "regular" });
});

test("목록 밖의 테마와 모드는 기본값으로 그리고, 위젯은 그대로 쓸 수 있으며 둘을 든 console.error 만 남긴다", () => {
  const errors = openWidget("agent=order-helper&theme=purple&mode=sepia");

  expect(rootAttributes()).toEqual({ theme: "nokcheong", mode: undefined, density: "regular" });
  expect(screen.queryByRole("alert")).toBeNull();
  expect(screen.getByRole("textbox", { name: "요청" })).toHaveProperty("disabled", false);
  expect(errors).toEqual([
    expect.stringContaining("위젯 질의 theme"),
    expect.stringContaining("위젯 질의 mode"),
  ]);
});

test("페이지를 걷으면 문서 뿌리에 단 속성도 걷어 다음 시험에 남지 않는다", () => {
  window.history.replaceState(null, "", "/widget?agent=order-helper&theme=jacho&mode=dark");
  const { unmount } = render(<WidgetPage />);
  expect(rootAttributes()).toEqual({ theme: "jacho", mode: "dark", density: "regular" });

  unmount();

  expect(rootAttributes()).toEqual({ theme: undefined, mode: undefined, density: undefined });
});
