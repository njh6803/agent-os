// 커스텀 요소를 jsdom 에 그리고 shadow root 안의 요소를 찾아 쓴다. 후보 넷이 같은 테스트를 돈다. 다른 것은
// `./element` 가 무엇으로 그리느냐뿐이다. HTTP 만 MSW 가 받는다. jsdom 의 fetch 는 노드의 것이라 CORS 는 여기서 재지
// 않는다(실제 브라우저는 shadow.mjs).

import type { Event as RunEvent } from "@agent-os/api-client";
import { fireEvent, screen, waitFor, within } from "@testing-library/dom";
import userEvent from "@testing-library/user-event";
import { http } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, test } from "vitest";
import "./element";
import { frame, sseResponse } from "./testing/stream";

const BASE = "https://agent.example";
const TOKEN = "probe-token-not-a-secret";
const RUN = "r-widget";
const TS = "2026-10-03T10:00:00+00:00";

const STARTED: RunEvent = {
  type: "run_started",
  run_id: RUN,
  ts: TS,
  agent: "echo",
  request: "안녕",
  principal: "widget",
};
const FINISHED: RunEvent = { type: "run_finished", run_id: RUN, ts: TS, output: "안녕하세요" };

const network = setupServer();
const unhandled: string[] = [];

beforeAll(() => {
  network.events.on("request:unhandled", ({ request }) => {
    unhandled.push(`${request.method} ${request.url}`);
  });
  network.listen({ onUnhandledFrame: "error" });
});

afterEach(() => {
  document.body.replaceChildren();
  network.resetHandlers();
  expect(unhandled.splice(0), "처리하지 않은 요청이 있다").toEqual([]);
});

afterAll(() => {
  network.close();
});

function mount(): HTMLElement {
  const host = document.createElement("agent-os-widget");
  host.setAttribute("api-base", BASE);
  host.setAttribute("agent", "echo");
  host.setAttribute("token", TOKEN);
  document.body.append(host);
  return host;
}

/** shadow root 안의 위젯 뿌리. 그려질 때까지 기다린다. */
async function widgetOf(host: HTMLElement): Promise<HTMLElement> {
  return waitFor(() => {
    const section = host.shadowRoot?.querySelector("section");
    if (!(section instanceof HTMLElement)) {
      throw new Error("shadow root 안에 위젯이 아직 없다");
    }
    return section;
  });
}

describe("커스텀 요소", () => {
  test("위젯은 shadow root 안에 그려지고 문서에서 찾는 쿼리에는 보이지 않는다", async () => {
    const widget = await widgetOf(mount());

    expect(within(widget).getByRole("textbox", { name: "메시지 입력" })).toBeDefined();
    expect(within(widget).getByRole("button", { name: "보내기" })).toBeDefined();
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(document.querySelector("section")).toBeNull();
  });

  // 글자는 fireEvent 로 넣는다. user-event 14.6.7 의 type 은 shadow root 안의 입력창 값을 바꾸지만 React 19 의
  // onChange 에 닿지 않았다(light DOM 에서는 닿았다. 그쪽은 손으로 돌려 봤다). 그 차이는 아래 사례가 후보마다 잰다.
  test("입력하고 보내면 기준 주소로 실행을 일으키고 SSE 프레임을 받는 대로 목록에 붙인다", async () => {
    const hold = Promise.withResolvers<undefined>();
    const seen: { url: string; authorization: string | null; body: unknown }[] = [];
    network.use(
      http.post(`${BASE}/runs`, async ({ request }) => {
        const body: unknown = await request.json();
        seen.push({ url: request.url, authorization: request.headers.get("authorization"), body });
        return sseResponse([frame(STARTED), hold.promise, frame(FINISHED)]);
      }),
    );
    const user = userEvent.setup();
    const widget = await widgetOf(mount());
    const list = within(widget).getByRole("list", { name: "메시지" });

    fireEvent.input(within(widget).getByRole("textbox", { name: "메시지 입력" }), {
      target: { value: "안녕" },
    });
    await user.click(within(widget).getByRole("button", { name: "보내기" }));

    await waitFor(() => {
      expect(within(list).getByText("run_started")).toBeDefined();
    });
    expect(within(list).getByText("안녕")).toBeDefined();
    expect(within(list).queryByText("안녕하세요")).toBeNull();

    hold.resolve(undefined);

    await waitFor(() => {
      expect(within(list).getByText("안녕하세요")).toBeDefined();
    });
    expect(seen).toEqual([
      {
        url: `${BASE}/runs`,
        authorization: `Bearer ${TOKEN}`,
        body: { agent: "echo", request: "안녕" },
      },
    ]);
  });

  test("user-event 로 친 글자가 위젯의 입력 처리에 닿아 보내진다", async () => {
    network.use(http.post(`${BASE}/runs`, () => sseResponse([frame(STARTED), frame(FINISHED)])));
    const user = userEvent.setup();
    const widget = await widgetOf(mount());
    const list = within(widget).getByRole("list", { name: "메시지" });

    await user.type(within(widget).getByRole("textbox", { name: "메시지 입력" }), "타자");
    await user.click(within(widget).getByRole("button", { name: "보내기" }));

    await waitFor(() => {
      expect(within(list).getByText("안녕하세요")).toBeDefined();
    });
    expect(within(list).getByText("타자")).toBeDefined();
  });
});
