// 실행 하나를 일으키는 요청 함수. 후보 넷이 같은 것을 쓴다. 받아들여지면 재개 스트림의 프레임을 받는 대로 내는
// 반복자를 돌려준다. 받아들여지지 않으면 상태 코드를 든 에러를 던진다.

import { createWidgetClient, readFrames, type StreamFrame } from "@agent-os/api-client";

export type { StreamFrame };

/** 위젯이 부를 곳. 기준 주소는 채널의 출처(다른 출처일 수 있다)다. */
export interface RunTarget {
  readonly baseUrl: string;
  readonly token: string;
  readonly agent: string;
}

export async function startRun(
  target: RunTarget,
  request: string,
  signal: AbortSignal,
): Promise<AsyncGenerator<StreamFrame, void, undefined>> {
  const { data, response } = await createWidgetClient(target.baseUrl, target.token).POST("/runs", {
    body: { agent: target.agent, request },
    parseAs: "stream",
    signal,
  });
  if (data === undefined || data === null) {
    throw new Error(`실행을 일으키지 못했다: ${String(response.status)}`);
  }
  return readFrames(data);
}
