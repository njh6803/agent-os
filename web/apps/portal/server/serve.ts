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
import { type PortalRequest, type PortalResponse, SERVER_ERROR } from "./handler.ts";

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

/**
 * 처리기가 던져도 그 요청만 500 으로 답한다. 던진 예외를 그대로 두면 프로세스가 죽어 요청 하나가 모든 사이트의 서비스를
 * 멈춘다. 오류의 이름만 stderr 에 남기고 메시지는 싣지 않는다(메시지에 쿠키 값이나 토큰이 섞일 수 있다).
 */
function answer(handler: Handler, incoming: IncomingMessage): PortalResponse {
  try {
    return handler(toRequest(incoming));
  } catch (error: unknown) {
    console.error(
      `요청을 처리하지 못했다(${error instanceof Error ? error.name : "알 수 없는 오류"})`,
    );
    return SERVER_ERROR;
  }
}

/**
 * `host` 와 `port` 에서 듣기 시작한다. 서지 못하면(포트가 쓰이는 중 등) 그 오류로 거부한다. 선 뒤의 서버 `error` 는 처리기를
 * 두지 않아 프로세스가 죽는다. 듣던 소켓이 깨진 서버는 요청을 받지 못하니 프로세스 관리자가 다시 띄우는 편이 낫다.
 */
export function listen(handler: Handler, host: string, port: number): Promise<Server> {
  const server = createServer((incoming, outgoing) => {
    const response = answer(handler, incoming);
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
