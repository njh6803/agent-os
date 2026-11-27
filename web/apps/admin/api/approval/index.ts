// 결정의 요청 함수(web-admin 티켓 08). 운영자 클라이언트로 채널의 결정 경로를 부른다. 자격은 로그인한 계정의 쿠키다
// (admin-login 티켓 09). 클라이언트는 부를 때 만든다(`api/plugins` 와 같다). 이 함수는 이벤트 처리기에서만 부른다.

import {
  readFrames,
  type components,
  // 계약의 이름 그대로 두면 DOM 전역 `Event` 를 가린다(티켓 03 의 메모).
  type Event as RunEvent,
  type StreamFrame,
} from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";
import { operatorClient } from "../session";

export type { RunEvent, StreamFrame };
export type Decision = components["schemas"]["Decision"];

/**
 * 멈춘 실행에 결정 하나를 낸다(`POST /runs/{run_id}/approval`). 결정은 그것이 답하는 일시정지의 자리를 든다(ADR
 * 0014 의 2026-09-28 이력). 받아들여지면 재개 스트림의 프레임을 받는 대로 내는 반복자를 돌려준다. 받아들여지지 않으면
 * 봉투를 든 RequestFailure 를 던진다. 스트림 경로에서도 에러는 스트림이 시작되기 전에 JSON 봉투로 온다
 * (.claude/rules/http.md).
 *
 * 연결은 `signal` 로 끊는다. 응답 전이면 이 함수가, 응답 뒤면 반복자가 그 에러를 던진다(`readFrames`).
 */
export async function sendDecision(
  runId: string,
  decision: Decision,
  signal: AbortSignal,
): Promise<AsyncGenerator<StreamFrame, void, undefined>> {
  const { data, error, response } = await operatorClient()
    .POST("/runs/{run_id}/approval", {
      params: { path: { run_id: runId } },
      body: decision,
      parseAs: "stream",
      signal,
    })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined || data === null) {
    throw failureOf(response.status, error);
  }
  return readFrames(data);
}
