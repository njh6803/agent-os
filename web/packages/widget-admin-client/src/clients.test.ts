// 공개 경로용 팩토리가 보내는 요청의 모양을 가짜 fetch 로 잰다. 위젯은 다른 출처에서 이 경로를 읽는다. 위젯 관리 서버는
// 허용 출처를 `*` 하나로 두고 preflight(`OPTIONS` 물음)에 답하지 않는다. 그래서 요청이 자격 증명을 싣지 않고 CORS 안전 목록
// 밖의 머리를 달지 않아야 브라우저가 답을 읽는다(widget-admin-server 명세 "응답 머리").
// openapi-fetch 는 클라이언트를 만들 때 전역 fetch 를 쥐므로, 가짜는 만들기 전에 건다.

import { afterEach, expect, test, vi } from "vitest";
import { createPublicClient } from "./clients";

const requests: Request[] = [];

/** 요청을 적고 404 봉투를 돌려주는 fetch 를 전역에 건다. */
function stubFetch(): void {
  vi.stubGlobal("fetch", (input: unknown) => {
    if (input instanceof Request) {
      requests.push(input);
    }
    return Promise.resolve(
      Response.json(
        { code: "not_found", message: "없는 사이트다", violations: [], request_id: "r-1" },
        { status: 404 },
      ),
    );
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  requests.splice(0);
});

const WIDGET_ADMIN = new URL("https://admin.example/");

async function 읽는다(base: URL = WIDGET_ADMIN): Promise<Request> {
  stubFetch();
  await createPublicClient(base).GET("/widget-settings/{site}", {
    params: { path: { site: "demo" } },
  });
  const request = requests[0];
  if (request === undefined) {
    throw new Error("가짜 fetch 가 요청을 받지 못했다");
  }
  return request;
}

test("공개 경로는 GET 으로 기준 주소 아래 /widget-settings/<이름> 을 부른다", async () => {
  const request = await 읽는다();

  expect(request.method).toBe("GET");
  expect(request.url).toBe("https://admin.example/widget-settings/demo");
});

test("기준 주소에 경로가 있으면 그 아래로 부른다", async () => {
  const request = await 읽는다(new URL("https://example.com/widget-admin/"));

  expect(request.url).toBe("https://example.com/widget-admin/widget-settings/demo");
});

test("모든 요청이 자격 증명을 싣지 않는다", async () => {
  const request = await 읽는다();

  expect(request.credentials).toBe("omit");
});

test("요청에 Content-Type 도 Accept 도 없다", async () => {
  const request = await 읽는다();

  expect(request.headers.has("Content-Type")).toBe(false);
  expect(request.headers.has("Accept")).toBe(false);
});

test("요청에 머리가 하나도 더해지지 않는다", async () => {
  const request = await 읽는다();
  const names: string[] = [];
  request.headers.forEach((_value, name) => names.push(name));

  expect(names).toEqual([]);
});

test("404 봉투는 error 로 돌아오고 data 는 없다", async () => {
  stubFetch();

  const { data, error } = await createPublicClient(WIDGET_ADMIN).GET("/widget-settings/{site}", {
    params: { path: { site: "demo" } },
  });

  expect(data).toBeUndefined();
  expect(error).toEqual({
    code: "not_found",
    message: "없는 사이트다",
    violations: [],
    request_id: "r-1",
  });
});
