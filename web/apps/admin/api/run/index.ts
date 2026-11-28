// 실행을 일으키는 요청 함수(admin-login 티켓 11). 운영자 클라이언트로 채널의 시작 경로와 이어 가기 경로를 부른다. 자격은 로그인한
// 계정의 쿠키다(`api/approval` 과 같다). 클라이언트는 부를 때 만든다. 이 함수는 이벤트 처리기에서만 부른다.

import { readFrames, type StreamFrame } from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";
import { operatorClient } from "../session";

/**
 * 보낼 요청. 에이전트와 요청 문자열은 둘 다 든다. `from` 이 있으면 그 실행(끝난 실행이어야 한다)에서 이어 가고, 없으면 새
 * 대화를 시작한다.
 */
export interface RunRequest {
  readonly agent: string;
  readonly request: string;
  readonly from: string | null;
}

/**
 * 실행 하나를 일으키고(`POST /runs`) 이어 가는(`POST /runs/{run_id}/continuation`) 응답의 이벤트 스트림을 받는 대로 내는
 * 반복자를 돌려준다. 받아들여지지 않으면 봉투를 든 RequestFailure 를 던진다. 스트림 경로에서도 에러는 스트림이 시작되기 전에
 * JSON 봉투로 온다(.claude/rules/http.md). 연결은 `signal` 로 끊는다.
 */
export async function sendRun(
  { agent, request, from }: RunRequest,
  signal: AbortSignal,
): Promise<AsyncGenerator<StreamFrame, void, undefined>> {
  const client = operatorClient();
  const body = { agent, request };
  const { data, error, response } = await (
    from === null
      ? client.POST("/runs", { body, parseAs: "stream", signal })
      : client.POST("/runs/{run_id}/continuation", {
          params: { path: { run_id: from } },
          body,
          parseAs: "stream",
          signal,
        })
  ).catch((cause: unknown) => {
    throw unreachable(cause);
  });
  if (data === undefined || data === null) {
    throw failureOf(response.status, error);
  }
  return readFrames(data);
}
