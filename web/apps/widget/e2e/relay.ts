// 같은 출처의 중계(ADR 0024 이력 2026-10-24). 운영에서는 운영자의 역방향 프록시가 위젯 페이지와 최종 사용자 경로를 한
// 출처 아래에 모은다. 그 설정은 web-widget 의 범위 밖이라 위젯 e2e 는 이 작은 중계로 같은 출처를 만든다.
//
// - `/end-user/` 아래는 serve 로, `/widget`(질의가 붙은 것 포함)과 `/widget/` 아래는 Next 로 넘기고 나머지는 404 로 답한다.
// - 응답은 모으지 않고 받는 대로 넘긴다. 그래서 도구 줄이 결말 전에 서는지를 이 중계가 가리지 않는다.
// - 받은 요청 줄의 경로를 그대로 넘긴다. nginx 의 경로 정규화, 버퍼링, 대소문자 비교, 본문 상한은 흉내 내지 않는다.
// - 루프백에만 선다. 브라우저는 `widget.localhost` 로 부르고, Playwright 설정이 `*.localhost` 를 127.0.0.1 로 푼다.

import {
  createServer,
  request,
  type IncomingMessage,
  type Server,
  type ServerResponse,
} from "node:http";
import { pipeline } from "node:stream";

export interface Upstreams {
  /** serve 의 주소(`http://127.0.0.1:<포트>`). */
  readonly serve: string;
  /** Next 의 주소. */
  readonly next: string;
}

/** 그 경로를 넘길 상류. 넘기지 않으면 null 이다. */
export function upstreamOf(path: string, upstreams: Upstreams): string | null {
  if (path.startsWith("/end-user/")) {
    return upstreams.serve;
  }
  if (path === "/widget" || path.startsWith("/widget?") || path.startsWith("/widget/")) {
    return upstreams.next;
  }
  return null;
}

function forward(incoming: IncomingMessage, outgoing: ServerResponse, upstreams: Upstreams): void {
  const path = incoming.url ?? "/";
  const target = upstreamOf(path, upstreams);
  if (target === null) {
    outgoing.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    outgoing.end("same-origin relay: blocked\n");
    return;
  }
  // `new URL(path, target)` 은 점 조각을 정규화한다(`/end-user/../runs` 가 `/runs` 가 된다). 원문을 `path` 로 넘긴다.
  const origin = new URL(target);
  const upstream = request(
    {
      hostname: origin.hostname,
      port: origin.port,
      path,
      method: incoming.method,
      headers: incoming.headers,
    },
    (response) => {
      outgoing.writeHead(response.statusCode ?? 502, response.headers);
      // `pipe` 는 상류가 응답 도중 끊겨도 브라우저 쪽을 닫지 않는다. `pipeline` 은 한쪽이 끊기면 양쪽을 destroy 한다.
      pipeline(response, outgoing, () => {
        // 끊김은 destroy 된 응답으로 브라우저에 그대로 보인다. 여기서 더 할 일은 없다.
      });
    },
  );
  upstream.on("error", (error) => {
    if (!outgoing.headersSent) {
      outgoing.writeHead(502, { "Content-Type": "text/plain; charset=utf-8" });
    }
    outgoing.end(`same-origin relay: ${error.message}\n`);
  });
  // 브라우저가 끊으면 상류도 끊는다. 서버가 스트림의 끊김을 보게 하기 위해서다. 정상 종료 뒤에도 불리지만 끝난 요청이라 무해하다.
  outgoing.on("close", () => {
    upstream.destroy();
  });
  incoming.pipe(upstream);
}

/** 그 포트의 루프백에 선 중계. */
export async function startRelay(port: number, upstreams: Upstreams): Promise<Server> {
  const server = createServer((incoming, outgoing) => {
    forward(incoming, outgoing, upstreams);
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", resolve);
  });
  return server;
}
