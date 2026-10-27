// 클라이언트 셋이 어디로 요청을 보내는지 잰다. 관리·채널 클라이언트의 헤더에 실리는 토큰은 페이지 테스트가 잰다(관리
// 요청은 05, 결정 요청은 08). 위젯 클라이언트는 토큰을 들지 않아 부르는 쪽이 준 헤더가 그대로 실리는지 여기서 잰다.
// openapi-fetch 는 클라이언트를 만들 때 전역 fetch 를 쥐므로, 가짜는 만들기 전에 건다.

import { afterEach, expect, test, vi } from "vitest";
import { createAdminClient, createChannelClient, createWidgetClient } from "./clients";
import type { components } from "./generated/openapi";

const urls: string[] = [];
const requests: Request[] = [];

/** 지금 페이지를 `http://127.0.0.1:3000/plugins` 로 두고, 요청을 적고 빈 응답을 돌려주는 fetch 를 건다. */
function onPage(): void {
  vi.stubGlobal("location", new URL("http://127.0.0.1:3000/plugins?kind=agent"));
  vi.stubGlobal("fetch", (input: unknown) => {
    if (input instanceof Request) {
      requests.push(input);
    }
    urls.push(input instanceof Request ? input.url : `Request 가 아니다: ${String(input)}`);
    return Promise.resolve(Response.json([]));
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  urls.splice(0);
  requests.splice(0);
});

test("관리 클라이언트는 지금 페이지의 출처에서 /api 아래 절대 주소로 부른다", async () => {
  onPage();

  await createAdminClient("admin-token").GET("/plugins");

  expect(urls).toEqual(["http://127.0.0.1:3000/api/plugins"]);
});

test("채널 클라이언트도 지금 페이지의 출처에서 /api 아래 절대 주소로 부른다", async () => {
  onPage();
  const decision: components["schemas"]["Decision"] = { decision: "approve", pause_index: 2 };

  await createChannelClient("channel-token").POST("/runs/{run_id}/approval", {
    params: { path: { run_id: "r1" } },
    body: decision,
    parseAs: "stream",
  });

  expect(urls).toEqual(["http://127.0.0.1:3000/api/runs/r1/approval"]);
});

const AGENT_OS = new URL("https://agent.example/os/");

test("위젯 클라이언트는 지금 페이지의 출처가 아니라 받은 기준 주소 아래로 부른다", async () => {
  onPage();

  await createWidgetClient(AGENT_OS).POST("/end-user/runs", {
    body: { agent: "echo", request: "안녕" },
    headers: { Authorization: "Bearer signed" },
    parseAs: "stream",
  });

  expect(urls).toEqual(["https://agent.example/os/end-user/runs"]);
  expect(requests[0]?.headers.get("Authorization")).toBe("Bearer signed");
});

test("위젯 클라이언트는 토큰을 들지 않아 부르는 쪽이 넘기지 않으면 Authorization 이 없다", async () => {
  onPage();

  await createWidgetClient(AGENT_OS).POST("/end-user/runs", {
    body: { agent: "echo", request: "안녕" },
    parseAs: "stream",
  });

  expect(requests[0]?.headers.has("Authorization")).toBe(false);
});

test("구독은 마지막으로 받은 id 를 계약의 헤더 파라미터 Last-Event-ID 로 보낸다", async () => {
  onPage();

  await createWidgetClient(AGENT_OS).GET("/end-user/runs/{run_id}/subscription", {
    params: { path: { run_id: "r1" }, header: { "last-event-id": "7" } },
    headers: { Authorization: "Bearer signed" },
    parseAs: "stream",
  });

  expect(urls).toEqual(["https://agent.example/os/end-user/runs/r1/subscription"]);
  expect(requests[0]?.headers.get("Last-Event-ID")).toBe("7");
});
