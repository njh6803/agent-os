// 재개 스트림의 가짜 응답. 관리 화면의 `apps/admin/testing/stream.ts` 와 같은 모양이다. 프레임은 `data:` 한 줄이고
// 걸음 사이에 약속을 두면 그것이 풀릴 때까지 다음 프레임을 내지 않는다. 테스트는 그 틈에 스트림이 열려 있는 동안의
// 화면을 본다.

import type { Event as RunEvent } from "@agent-os/api-client";
import { HttpResponse } from "msw";

const GAP_MS = 10;

export function frame(event: RunEvent): string {
  return `data: ${JSON.stringify(event)}\n\n`;
}

export type Step = string | Promise<unknown>;

export function sseResponse(steps: readonly Step[]): Response {
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
