// 이벤트 하나를 글자로 그리는 것(web-admin 티켓 07, end-user-continuation 티켓 10, admin-login 티켓 11). 옛 실행 화면의
// 페이지 테스트가 이 부품을 거쳐 재던 것을 화면이 없어진 뒤에도 이 부품 하나에서 잰다. 이벤트 하나를 jsdom 에 그리고
// 네트워크는 쓰지 않는다. 트레이스는 바깥에서 온 텍스트를 싣는다. 그것이 요소로 그려지지 않는 것을 문서에서 본다(ADR 0019).

import { render, within } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import type { TraceEvent } from "../../api/traces";
import { EventItem } from "./EventItem";

const RUN = "r-calc";
const TS = "2026-09-30T09:00:00+00:00";

/** 시작 이벤트. `fields` 로 바꾼 값은 계약 밖의 모양(지도가 아닌 바로가기 따위)도 받는다. 바깥에서 온 텍스트라서다. */
function started(fields: Readonly<Record<string, unknown>> = {}): TraceEvent {
  return Object.assign(
    {
      type: "run_started" as const,
      run_id: RUN,
      ts: TS,
      agent: "calc",
      request: "1 더하기 2",
      principal: "operator",
      previous_run: null,
      shortcuts: null,
      requesting_account: null,
    },
    fields,
  );
}

function show(event: TraceEvent): HTMLElement {
  const { container } = render(
    <ul>
      <EventItem event={event} />
    </ul>,
  );
  return within(container).getByRole("listitem");
}

function names(item: HTMLElement): (string | null)[] {
  return within(item)
    .getAllByRole("term")
    .map((term) => term.textContent);
}

/** 이벤트 항목에서 계약의 이름이 `name` 인 필드의 값 칸. */
function fieldValue(item: HTMLElement, name: string): HTMLElement {
  const term = within(item)
    .getAllByRole("term")
    .find((found) => found.querySelector("code")?.textContent === name);
  const value = term?.nextElementSibling;
  if (!(value instanceof HTMLElement)) {
    throw new Error(`${name} 필드가 없다`);
  }
  return value;
}

describe("이벤트 하나", () => {
  test("카드 머리는 종류와 트레이스의 시각 글자 그대로이고 모르는 종류는 시각이 없다", () => {
    const first = show(started());
    expect(within(first).getByRole("heading", { level: 3 }).textContent).toBe(`run_started ${TS}`);

    const unknown = show({ type: "unknown", raw: "{}" });
    expect(within(unknown).getByRole("heading", { level: 3 }).textContent).toBe("모르는 종류");
  });

  test("필드의 이름은 용어집의 말과 계약의 이름을 함께 보인다", () => {
    expect(names(show(started()))).toEqual([
      "시각 ts",
      "에이전트 agent",
      "요청 request",
      "주체 principal",
      "앞 실행 previous_run",
      "바로가기 shortcuts",
      "요청한 계정 requesting_account",
    ]);
  });

  test("모르는 종류의 이벤트는 원문 문자열을 그대로 보인다", () => {
    const raw = '{"type":"future_kind","run_id":"r-calc","ts":"2026-09-30T09:00:04+00:00"}';
    const item = show({ type: "unknown", raw });

    expect(names(item)).toEqual(["원문 raw"]);
    expect(item.textContent).toContain(raw);
  });

  test("인자와 도구 호출 같은 JSON 값은 들여 적고 마스킹된 인자는 *** 로 보인다", () => {
    const calls = [{ id: "call-1", name: "add", args: { a: 1, b: 2 } }];
    const call = show({
      type: "llm_called",
      run_id: RUN,
      ts: TS,
      model: "claude-sonnet-5",
      input_tokens: 12,
      output_tokens: 7,
      prompt: "첫 줄\n  둘째 줄은 들여 썼다",
      text: "",
      tool_calls: calls,
    });
    expect(call.textContent).toContain(JSON.stringify(calls, null, 2));
    expect(call.textContent).toContain("첫 줄\n  둘째 줄은 들여 썼다");

    const masked = show({
      type: "tool_called",
      run_id: RUN,
      ts: TS,
      tool: "login",
      ok: false,
      args: { user: "ops", password: "***" },
      content: "인증에 실패했다",
      rule: null,
    });
    expect(masked.textContent).toContain('"password": "***"');
    expect(masked.textContent).toContain("false");
  });

  test("실패 원인은 용어집의 말과 계약의 이름을 함께 보이고 값은 계약의 값 그대로 글자다", () => {
    const item = show({
      type: "run_failed",
      run_id: RUN,
      ts: TS,
      error: "모델 호출이 실행 기한 300초를 넘겼다",
      cause: "timeout",
    });

    expect(names(item)).toEqual(["시각 ts", "에러 error", "실패 원인 cause"]);
    // 원인마다 문구를 짓는 것은 위젯의 몫이다. 관리 화면은 운영자에게 계약의 값을 보인다.
    expect(fieldValue(item, "cause").textContent).toBe("timeout");
  });

  test("요청한 계정과 결정한 계정은 용어집의 말과 계약의 이름을 함께 보이고 값은 글자 그대로다", () => {
    const requested = show(started({ requesting_account: "alice" }));
    expect(names(requested)).toContain("요청한 계정 requesting_account");
    expect(fieldValue(requested, "requesting_account").textContent).toBe("alice");

    const decided = show({
      type: "approval_granted",
      run_id: RUN,
      ts: TS,
      approver: "operator",
      deciding_account: "bob",
    });
    expect(names(decided)).toEqual(["시각 ts", "승인자 approver", "결정한 계정 deciding_account"]);
    expect(fieldValue(decided, "deciding_account").textContent).toBe("bob");
  });

  test("적용 규칙과 서버는 용어집의 말과 계약의 이름을 함께 보이고 옛 줄의 null 은 칸이 글자로 남는다", () => {
    const paused = show({
      type: "run_paused",
      run_id: RUN,
      ts: TS,
      tool: "send",
      args: { to: "bob" },
      rule: "requires_approval",
      server: "everything",
    });
    expect(names(paused)).toEqual([
      "시각 ts",
      "도구 tool",
      "인자 args",
      "적용 규칙 rule",
      "서버 server",
    ]);
    expect(fieldValue(paused, "rule").textContent).toBe("requires_approval");
    expect(fieldValue(paused, "server").textContent).toBe("everything");

    const old = show({
      type: "run_paused",
      run_id: RUN,
      ts: TS,
      tool: "send",
      args: {},
      rule: null,
      server: null,
    });
    expect(fieldValue(old, "rule").textContent).toBe("null");
    expect(fieldValue(old, "server").textContent).toBe("null");
  });

  test("요약 이벤트의 필드는 용어집의 말과 계약의 이름을 함께 보이고 글과 토큰 수는 글자다", () => {
    const summary = "2+3 묻자 5 답함(실행 r calc/하나).";
    const item = show({
      type: "conversation_summarized",
      run_id: RUN,
      ts: TS,
      summary,
      last_covered_run: "r calc/하나",
      model: "claude-sonnet-5",
      input_tokens: 543,
      output_tokens: 38,
    });

    expect(names(item)).toEqual([
      "시각 ts",
      "요약 글 summary",
      "요약에 든 마지막 실행 last_covered_run",
      "모델 model",
      "입력 토큰 수 input_tokens",
      "응답 토큰 수 output_tokens",
    ]);
    expect(item.textContent).toContain(summary);
    expect(item.textContent).toContain("543");
    // 링크는 실행 식별자 필드 하나뿐이다. 요약 글에 든 식별자는 글자다.
    expect(within(item).getAllByRole("link")).toHaveLength(1);
  });

  test("앞 실행과 요약에 든 마지막 실행은 그 실행의 상세로 가는 링크이고 주소는 인코딩한 식별자다", () => {
    const previous = within(show(started({ previous_run: "r calc/둘" }))).getByRole("link", {
      name: "r calc/둘",
    });
    expect(previous.getAttribute("href")).toBe("/runs/r%20calc%2F%EB%91%98");
  });

  test("이어 가지 않은 실행의 앞 실행은 링크가 아니라 글자다", () => {
    const item = show(started());

    expect(within(item).queryByRole("link")).toBeNull();
    expect(fieldValue(item, "previous_run").textContent).toBe("null");
  });

  test.each([".", ".."])(
    "앞 실행이 %s 이면 주소가 /runs/ 밖으로 풀리므로 링크가 아니라 글자다",
    (dot) => {
      const item = show(started({ previous_run: dot }));

      expect(within(item).queryByRole("link")).toBeNull();
      expect(fieldValue(item, "previous_run").textContent).toBe(dot);
    },
  );

  test("최종 사용자의 주체는 발급자와 sub 를 가르는 구분자까지 글자 그대로 보인다", () => {
    const item = show(started({ principal: "https://shop.example|user-17" }));

    expect(fieldValue(item, "principal").textContent).toBe("https://shop.example|user-17");
  });

  test("바로가기는 에이전트마다 이름이 글자이고 그 실행의 상세로 가는 링크 하나다", () => {
    const item = show(started({ shortcuts: { calc: "r calc/셋", weather: "r-weather-1" } }));

    const shortcuts = fieldValue(item, "shortcuts");
    const rows = within(shortcuts)
      .getAllByRole("term")
      .map((agent) => ({
        agent: agent.textContent,
        links:
          agent.nextElementSibling instanceof HTMLElement
            ? within(agent.nextElementSibling)
                .queryAllByRole("link")
                .map((link) => [link.textContent, link.getAttribute("href")])
            : [],
      }));
    expect(rows).toEqual([
      { agent: "calc", links: [["r calc/셋", `/runs/${encodeURIComponent("r calc/셋")}`]] },
      { agent: "weather", links: [["r-weather-1", "/runs/r-weather-1"]] },
    ]);
    expect(within(shortcuts).getByRole("link", { name: "r calc/셋" }).getAttribute("href")).toBe(
      "/runs/r%20calc%2F%EC%85%8B",
    );
    // 링크는 바로가기의 칸 둘뿐이다. 이어 가지 않은 실행의 앞 실행은 글자다.
    expect(within(item).getAllByRole("link")).toHaveLength(2);
  });

  test("바로가기가 없는 옛 실행은 링크 없이 글자 null 이다", () => {
    const item = show(started());

    expect(fieldValue(item, "shortcuts").textContent).toBe("null");
    expect(within(item).queryByRole("link")).toBeNull();
  });

  test("새 대화의 첫 실행인 빈 바로가기는 링크 없이 글자 {} 라 옛 실행의 null 과 갈린다", () => {
    const item = show(started({ shortcuts: {} }));

    expect(fieldValue(item, "shortcuts").textContent).toBe("{}");
    expect(within(item).queryByRole("link")).toBeNull();
  });

  test.each([".", ".."])(
    "바로가기의 실행이 %s 이면 그 칸만 링크가 아니라 글자이고 다른 칸은 링크다",
    (dot) => {
      const item = show(started({ shortcuts: { calc: dot, weather: "r-weather-1" } }));

      const shortcuts = fieldValue(item, "shortcuts");
      expect(
        within(shortcuts)
          .getAllByRole("link")
          .map((link) => link.textContent),
      ).toEqual(["r-weather-1"]);
      expect(shortcuts.textContent).toContain(`calc${dot}`);
    },
  );

  test.each<[string, unknown, string]>([
    ["문자열", "r-calc", "r-calc"],
    ["배열", ["r-calc"], '[\n  "r-calc"\n]'],
    [
      "문자열이 아닌 값을 든 객체",
      { calc: "r-calc", weather: 3 },
      '{\n  "calc": "r-calc",\n  "weather": 3\n}',
    ],
    [
      "null 을 든 객체",
      { calc: "r-calc", weather: null },
      '{\n  "calc": "r-calc",\n  "weather": null\n}',
    ],
  ])("바로가기가 지도가 아닌 %s 이면 링크 없이 글자 그리기로 보인다", (_, shortcuts, shown) => {
    const item = show(started({ shortcuts }));

    expect(within(item).queryByRole("link")).toBeNull();
    expect(fieldValue(item, "shortcuts").textContent).toBe(shown);
  });

  test("이벤트에 든 HTML 은 글자 그대로 보이고 요소로 그려지지 않는다", () => {
    const image = '<img src=x onerror="window.__agentOsXss = true">';
    const script = "<script>window.__agentOsXss = true</script>";
    const link = '<a href="javascript:window.__agentOsXss = true">눌러</a>';
    // 앞 실행의 값은 링크의 href 에 든다. 인코딩되어 `/runs/` 아래의 조각으로만 남아야 한다.
    const previous = "javascript:window.__agentOsXss = true/../../plugins?x#y";
    // 바로가기의 에이전트 이름은 글자이고, 실행 식별자는 앞 실행처럼 인코딩된 조각으로만 href 에 든다.
    const agent = '<iframe src="javascript:window.__agentOsXss = true"></iframe>';
    const shortcut = "javascript:window.__agentOsXss = 1#../..";

    const item = show(
      started({
        request: script,
        previous_run: previous,
        shortcuts: { [agent]: shortcut },
      }),
    );
    const called = show({
      type: "tool_called",
      run_id: RUN,
      ts: TS,
      tool: "fetch",
      ok: true,
      args: {},
      content: image + link,
      rule: null,
    });

    for (const text of [script, previous, agent, shortcut]) {
      expect(item.textContent).toContain(text);
    }
    expect(called.textContent).toContain(image + link);
    expect(document.querySelector("img")).toBeNull();
    expect(document.querySelector("iframe")).toBeNull();
    expect(document.body.querySelector("script")).toBeNull();
    expect(document.querySelector('a[href^="javascript"]')).toBeNull();
    expect(within(item).getByRole("link", { name: previous }).getAttribute("href")).toBe(
      "/runs/javascript%3Awindow.__agentOsXss%20%3D%20true%2F..%2F..%2Fplugins%3Fx%23y",
    );
    expect(within(item).getByRole("link", { name: shortcut }).getAttribute("href")).toBe(
      "/runs/javascript%3Awindow.__agentOsXss%20%3D%201%23..%2F..",
    );
    expect(Reflect.has(window, "__agentOsXss")).toBe(false);
  });
});
