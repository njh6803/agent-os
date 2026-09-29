// 클라이언트 둘이 어디로 요청을 보내는지 잰다. 헤더에 실리는 토큰은 페이지 테스트가 잰다(관리 요청은 05, 결정
// 요청은 08). openapi-fetch 는 클라이언트를 만들 때 전역 fetch 를 쥐므로, 가짜는 만들기 전에 건다.

import { afterEach, expect, test, vi } from "vitest";
import { createAdminClient, createChannelClient } from "./clients";
import type { components } from "./generated/openapi";

const urls: string[] = [];

/** 지금 페이지를 `http://127.0.0.1:3000/plugins` 로 두고, 요청의 주소를 적고 빈 응답을 돌려주는 fetch 를 건다. */
function onPage(): void {
  vi.stubGlobal("location", new URL("http://127.0.0.1:3000/plugins?kind=agent"));
  vi.stubGlobal("fetch", (input: unknown) => {
    urls.push(input instanceof Request ? input.url : `Request 가 아니다: ${String(input)}`);
    return Promise.resolve(Response.json([]));
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  urls.splice(0);
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
