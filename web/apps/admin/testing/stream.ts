// 재개 스트림의 가짜 응답(web-admin 명세 "주 이음매 — 페이지"). 프레임은 서버처럼 `data:` 한 줄이고
// (.claude/rules/http.md) 줄 끝은 `\n` 이다(서버가 쓰는 FastAPI 의 `fastapi/sse.py`). `\r\n` 을 받는 것은 파서의 단위
// 테스트(`packages/api-client/src/stream.test.ts`)가 잰다. 프레임 사이에 시간 간격을 두고 `ReadableStream` 으로 낸다
// (`.scratch/web-admin/probes/jsdom_sse.sh` 의 모양). 사이에 약속을 두면 그것이 풀릴 때까지 다음 프레임을 내지 않는다.
// 테스트는 그 틈에 스트림이 열려 있는 동안의 화면을 본다.
//
// 못 만드는 것: 도중의 끊김. MSW 3.0.0 은 핸들러 스트림의 에러(`controller.error`)를 읽는 쪽에 에러가 아니라 끝으로
// 넘긴다(`.scratch/web-admin/probes/msw_abort.mjs`). 그래서 결말 없는 끊김은 결말 없이 닫는 것으로 만든다.

import { HttpResponse } from "msw";
import type { RunEvent } from "../api/approval";

const GAP_MS = 10;

/** 프레임 하나. 이벤트는 서버처럼 JSON 으로, 글자는 원문 그대로 `data:` 뒤에 싣는다. */
export function frame(data: RunEvent | string): string {
  return `data: ${typeof data === "string" ? data : JSON.stringify(data)}\n\n`;
}

/** keepalive 주석. 서버의 것과 같은 바이트다. 이벤트가 아니다. */
export const KEEPALIVE = ": ping\n\n";

/** 스트림의 한 걸음. 글자는 내보낼 바이트, 약속은 기다릴 자리다. */
export type Step = string | Promise<unknown>;

/** 걸음을 차례로 낸다. 다 내면 닫는다. */
export function resumeStream(steps: readonly Step[]): Response {
  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    async start(controller) {
      for (const step of steps) {
        if (typeof step !== "string") {
          await step;
          continue;
        }
        await new Promise((resolve) => setTimeout(resolve, GAP_MS));
        controller.enqueue(encoder.encode(step));
      }
      controller.close();
    },
  });
  return new HttpResponse(body, { headers: { "Content-Type": "text/event-stream" } });
}
