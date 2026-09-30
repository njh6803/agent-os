// 흐름이 채널 토큰으로 보내는 화면 밖의 요청(web-admin 명세 "e2e"). 멈춘 실행을 만드는 `POST /runs` 와, 오래된 화면의
// "다른 곳"인 결정이다. 화면과 같은 중계(`/api/*`)를 지나되 브라우저의 포커스를 건드리지 않는다. 탭을 바꾸면 포커스
// 재검증이 먼저 새 일시정지를 읽어, 옛 자리를 보낼 기회가 사라질 수 있다.
//
// 스트림은 제품과 같은 파서(`readFrames`)로 읽는다. 술어를 지나지 못한 프레임이 오면 준비가 실패한다.

import {
  readFrames,
  type components,
  // 계약의 이름 그대로 두면 DOM 전역 `Event` 를 가린다.
  type Event as RunEvent,
} from "@agent-os/api-client";
import type { APIRequestContext, APIResponse } from "@playwright/test";
import { stack } from "./env";

type Decision = components["schemas"]["Decision"];

/** 멈춘 실행과, 지금 그 실행이 멈춘 일시정지의 자리(트레이스 상세 `events` 의 인덱스). */
export interface Paused {
  readonly runId: string;
  readonly pauseIndex: number;
}

/** 채널 토큰으로 그 에이전트의 실행 하나를 일으킨다. 승인 대상에서 멈춰야 한다. */
export async function startPausedRun(request: APIRequestContext, agent: string): Promise<Paused> {
  const { adminUrl, channelToken } = stack();
  const response = await request.post(`${adminUrl}/api/runs`, {
    headers: { Authorization: `Bearer ${channelToken}` },
    data: { agent, request: `${agent} 의 e2e 요청` },
  });
  return pausedOf(await eventsOf(response), 0);
}

/**
 * 채널 토큰으로 그 일시정지를 허가한다. 재개가 다음 승인 대상에서 다시 멈춰야 한다. 재개 스트림의 프레임은 트레이스에
 * 새로 붙은 줄과 같아서(스토리 61) 새 일시정지의 자리는 결정의 다음 자리부터 센다.
 */
export async function approve(request: APIRequestContext, paused: Paused): Promise<Paused> {
  const { adminUrl, channelToken } = stack();
  const decision: Decision = { decision: "approve", pause_index: paused.pauseIndex };
  const response = await request.post(
    `${adminUrl}/api/runs/${encodeURIComponent(paused.runId)}/approval`,
    { headers: { Authorization: `Bearer ${channelToken}` }, data: decision },
  );
  return pausedOf(await eventsOf(response), paused.pauseIndex + 1);
}

async function eventsOf(response: APIResponse): Promise<RunEvent[]> {
  const text = await response.text();
  if (!response.ok()) {
    throw new Error(`채널 요청이 실패했다(${String(response.status())}): ${text}`);
  }
  const body = new Response(text).body;
  if (body === null) {
    throw new Error("채널 응답에 본문이 없다");
  }
  const events: RunEvent[] = [];
  for await (const frame of readFrames(body)) {
    if (frame.kind === "raw") {
      throw new Error(`읽지 못한 프레임: ${frame.raw}`);
    }
    events.push(frame.event);
  }
  return events;
}

/** 스트림이 일시정지로 끝났으면 그 자리. `first` 는 스트림의 첫 이벤트가 트레이스에서 서는 자리다. */
function pausedOf(events: readonly RunEvent[], first: number): Paused {
  const last = events.at(-1);
  if (last?.type !== "run_paused") {
    throw new Error(`실행이 멈추지 않았다: ${JSON.stringify(events)}`);
  }
  return { runId: last.run_id, pauseIndex: first + events.length - 1 };
}
