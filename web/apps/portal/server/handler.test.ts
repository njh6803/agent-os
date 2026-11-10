// HTTP 요청 처리기. 순수 함수라 요청을 값으로 만들어 부른다. 실제 소켓은 e2e 가 지난다.

import { expect, test } from "vitest";
import { handle, type PortalRequest } from "./handler.ts";

function request(method: string, path: string): PortalRequest {
  return { method, path, headers: {}, cookies: [] };
}

test("health 는 살아 있다고 JSON 으로 답하고 캐시하지 않는다", () => {
  const response = handle(request("GET", "/portal/health"));

  expect(response.status).toBe(200);
  expect(response.headers["Content-Type"]).toBe("application/json");
  expect(response.headers["Cache-Control"]).toBe("no-store");
  expect(JSON.parse(response.body)).toEqual({ status: "ok" });
});

test("모르는 경로는 404 다", () => {
  expect(handle(request("GET", "/nothing")).status).toBe(404);
  // 이 티켓에는 페이지가 없다. 끝 슬래시가 없는 /portal 도 모르는 경로다.
  expect(handle(request("GET", "/portal/")).status).toBe(404);
  expect(handle(request("GET", "/portal")).status).toBe(404);
  expect(handle(request("GET", "/")).status).toBe(404);
});

test("아는 경로의 다른 메서드는 405 와 Allow 로 답한다", () => {
  for (const method of ["POST", "PUT", "DELETE", "HEAD"]) {
    const response = handle(request(method, "/portal/health"));

    expect(response.status, method).toBe(405);
    expect(response.headers["Allow"], method).toBe("GET");
  }
});

test("모든 응답에 nosniff 를 단다", () => {
  const responses = [
    handle(request("GET", "/portal/health")),
    handle(request("GET", "/nothing")),
    handle(request("POST", "/portal/health")),
  ];

  for (const response of responses) {
    expect(response.headers["X-Content-Type-Options"]).toBe("nosniff");
  }
});
