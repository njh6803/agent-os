// 요청 처리기(`handler.ts`)를 `node:http` 에 거는 얇은 겉. 요청을 값으로 옮기고 응답 값을 쓰는 일만 한다. 판단은 처리기에
// 있고, 실제 소켓은 e2e 가 지난다. 접근 로그를 남기지 않는다(접근 기록은 프록시의 몫이고, 쿠키와 토큰이 섞일 길을 열지
// 않는다. ADR 0050 결정 "기록"). 설정의 `host` 와 `port` 에서만 듣는다.

import {
  createServer,
  type IncomingHttpHeaders,
  type IncomingMessage,
  type Server,
} from "node:http";
import { parseCookieHeader } from "./cookies.ts";
import type { PortalRequest, PortalResponse } from "./handler.ts";

export type Handler = (request: PortalRequest) => PortalResponse;

/** 요청 대상에서 질의를 뗀 경로. 퍼센트 인코딩은 풀지 않는다. */
function pathOf(target: string | undefined): string {
  const raw = target ?? "/";
  const query = raw.indexOf("?");
  return query < 0 ? raw : raw.slice(0, query);
}

function flatten(headers: IncomingHttpHeaders): Record<string, string> {
  const flat: Record<string, string> = {};
  for (const [name, value] of Object.entries(headers)) {
    if (value !== undefined) {
      flat[name] = Array.isArray(value) ? value.join(", ") : value;
    }
  }
  return flat;
}

function toRequest(incoming: IncomingMessage): PortalRequest {
  return {
    method: incoming.method ?? "GET",
    path: pathOf(incoming.url),
    headers: flatten(incoming.headers),
    cookies: parseCookieHeader(incoming.headers.cookie),
  };
}

/** `host` 와 `port` 에서 듣기 시작한다. 서지 못하면(포트가 쓰이는 중 등) 그 오류로 거부한다. */
export function listen(handler: Handler, host: string, port: number): Promise<Server> {
  const server = createServer((incoming, outgoing) => {
    const response = handler(toRequest(incoming));
    outgoing.writeHead(response.status, response.headers);
    outgoing.end(response.body);
  });
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen({ host, port }, () => {
      server.off("error", reject);
      resolve(server);
    });
  });
}
