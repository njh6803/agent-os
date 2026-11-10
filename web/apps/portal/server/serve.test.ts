// `node:http` 겉. 요청을 값으로 옮기는 일과 응답 값을 쓰는 일, 처리기가 던졌을 때의 500 을 실제 소켓으로 본다. 전역 `fetch` 는
// 쓰지 않고 `node:http` 의 `request` 로 부른다.

import { request, type Server } from "node:http";
import { afterEach, expect, test, vi } from "vitest";
import type { PortalRequest, PortalResponse } from "./handler.ts";
import { listen } from "./serve.ts";

const servers: Server[] = [];

afterEach(() => {
  vi.restoreAllMocks();
  for (const server of servers.splice(0)) {
    server.closeAllConnections();
    server.close();
  }
});

async function start(handler: (request: PortalRequest) => PortalResponse): Promise<number> {
  const server = await listen(handler, "127.0.0.1", 0);
  servers.push(server);
  const address = server.address();
  if (address === null || typeof address === "string") {
    throw new Error("포트를 알 수 없다");
  }
  return address.port;
}

interface Answer {
  readonly status: number;
  readonly headers: Record<string, string | string[] | undefined>;
  readonly body: string;
}

function send(
  port: number,
  method: string,
  path: string,
  headers: Record<string, string> = {},
): Promise<Answer> {
  return new Promise((resolve, reject) => {
    const outgoing = request({ host: "127.0.0.1", port, method, path, headers }, (incoming) => {
      const chunks: Buffer[] = [];
      incoming.on("data", (chunk: Buffer) => chunks.push(chunk));
      incoming.on("end", () => {
        resolve({
          status: incoming.statusCode ?? 0,
          headers: incoming.headers,
          body: Buffer.concat(chunks).toString("utf-8"),
        });
      });
    });
    outgoing.on("error", reject);
    // 응답이 오지 않으면(처리기의 예외가 소켓을 그냥 둔 경우) 시험의 시간 제한까지 기다리지 않고 바로 실패한다.
    outgoing.setTimeout(5000, () => {
      outgoing.destroy(new Error("응답이 없다"));
    });
    outgoing.end();
  });
}

test("처리기가 낸 상태와 헤더와 본문을 그대로 쓴다", async () => {
  const port = await start(() => ({
    status: 418,
    headers: { "Content-Type": "text/plain; charset=utf-8", "X-Test": "yes" },
    body: "찻주전자",
  }));

  const answer = await send(port, "GET", "/anything");

  expect(answer.status).toBe(418);
  expect(answer.headers["x-test"]).toBe("yes");
  expect(answer.body).toBe("찻주전자");
});

test("요청을 메서드와 질의를 뗀 경로와 소문자 헤더와 쿠키로 옮긴다", async () => {
  const seen: PortalRequest[] = [];
  const port = await start((incoming) => {
    seen.push(incoming);
    return { status: 204, headers: {}, body: "" };
  });

  await send(port, "POST", "/portal/sites/demo/token?x=1", {
    Origin: "http://portal.localhost:8080",
    Cookie: "portal_anon=abc; other=1",
  });

  expect(seen).toHaveLength(1);
  expect(seen[0]?.method).toBe("POST");
  expect(seen[0]?.path).toBe("/portal/sites/demo/token");
  expect(seen[0]?.headers["origin"]).toBe("http://portal.localhost:8080");
  expect(seen[0]?.cookies).toEqual([
    { name: "portal_anon", value: "abc" },
    { name: "other", value: "1" },
  ]);
});

test("204 응답은 본문 없이 나간다", async () => {
  const port = await start(() => ({ status: 204, headers: { "Set-Cookie": "a=b" }, body: "" }));

  const answer = await send(port, "POST", "/x");

  expect(answer.status).toBe(204);
  expect(answer.body).toBe("");
  expect(answer.headers["set-cookie"]).toEqual(["a=b"]);
});

test("처리기가 던지면 500 으로 답하고 서버는 다음 요청을 받는다", async () => {
  const log = vi.spyOn(console, "error").mockImplementation(() => undefined);
  let calls = 0;
  const port = await start(() => {
    calls += 1;
    if (calls === 1) {
      throw new Error("비밀이 든 메시지 portal_anon=SECRET");
    }
    return { status: 200, headers: {}, body: "살아 있다" };
  });

  const failed = await send(port, "GET", "/x");
  const next = await send(port, "GET", "/x");

  expect(failed.status).toBe(500);
  expect(failed.headers["content-type"]).toBe("text/plain; charset=utf-8");
  expect(failed.headers["x-content-type-options"]).toBe("nosniff");
  expect(failed.body).not.toContain("SECRET");
  expect(next.status).toBe(200);
  expect(next.body).toBe("살아 있다");
  // 오류의 이름만 남기고 메시지는 싣지 않는다. 메시지에 쿠키 값이나 토큰이 섞일 수 있다.
  expect(log).toHaveBeenCalledTimes(1);
  expect(String(log.mock.calls[0]?.[0])).not.toContain("SECRET");
});
