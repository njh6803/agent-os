// HTTP 요청 처리기. 요청 값(메서드, 경로, 헤더, 쿠키)을 받아 응답 값(상태, 헤더, 본문)을 내는 순수 함수 하나다. 소켓에 거는
// 일은 `serve.ts` 가 하고, 여기는 `node:http` 를 모른다. 그래서 시험이 요청을 값으로 만들어 부른다(pilot-portal 명세 "HTTP
// 요청 처리기와 서버"). 서버 코드와 시험은 전역 `fetch` 를 쓰지 않는다.
//
// 이 티켓의 경로는 `GET /portal/health` 하나다. 시계와 UUID 만들기를 인자로 받는 자리는 그것을 쓰는 끝점(고지 확인, 토큰)을
// 더하는 티켓이 이 함수의 인자로 더한다.

import type { Cookie } from "./cookies.ts";

export interface PortalRequest {
  readonly method: string;
  /** 질의를 뗀 경로. 퍼센트 인코딩은 풀지 않는다. */
  readonly path: string;
  /** 소문자 이름의 요청 헤더. 같은 이름이 여럿이면 `node:http` 가 이은 한 글이다(`cookie` 는 `; ` 로 잇는다). */
  readonly headers: Readonly<Record<string, string>>;
  readonly cookies: readonly Cookie[];
}

export interface PortalResponse {
  readonly status: number;
  readonly headers: Readonly<Record<string, string>>;
  readonly body: string;
}

/** 모든 응답에 단다. 브라우저가 내용을 추측해 다른 형식으로 읽지 못하게 한다. */
const SECURITY_HEADERS = { "X-Content-Type-Options": "nosniff" } as const;

function respond(
  status: number,
  contentType: string,
  body: string,
  extra: Readonly<Record<string, string>> = {},
): PortalResponse {
  return {
    status,
    headers: { ...SECURITY_HEADERS, "Content-Type": contentType, ...extra },
    body,
  };
}

export function handle(request: PortalRequest): PortalResponse {
  if (request.path === "/portal/health") {
    return request.method === "GET"
      ? respond(200, "application/json", JSON.stringify({ status: "ok" }), {
          "Cache-Control": "no-store",
        })
      : respond(405, "text/plain; charset=utf-8", "허용하지 않는 메서드입니다.", { Allow: "GET" });
  }
  return respond(404, "text/plain; charset=utf-8", "찾을 수 없습니다.");
}
