// 페이지 테스트의 가짜 네트워크. 가짜는 바깥 경계(HTTP) 하나에만 두고 그 안(생성 클라이언트, SWR, 스토어)은
// 진짜다(web-admin 명세 "주 이음매 — 페이지"). 핸들러의 응답 본문은 생성 타입으로 적는다. 계약이 바뀌면 핸들러가
// 컴파일에서 깨진다(스토리 81).

import { setupServer } from "msw/node";
import type { ErrorEnvelope } from "../api/failure";

export type { PluginRow } from "../api/plugins";

export const network = setupServer();

/** 처리하지 않은 요청(메서드와 주소). 테스트가 끝날 때 비어 있어야 한다. setup.ts 가 본다. */
export const unhandled: string[] = [];

/** 페이지가 부르는 주소. 생성 클라이언트처럼 지금 페이지의 출처에서 /api 아래 절대 주소다. */
export function api(path: string): string {
  return new URL(`/api${path}`, location.origin).href;
}

/** 서버가 내는 에러 봉투. */
export function envelope(
  code: ErrorEnvelope["code"],
  message: string,
  requestId = "req-0001",
): ErrorEnvelope {
  return { code, message, request_id: requestId, violations: [] };
}
