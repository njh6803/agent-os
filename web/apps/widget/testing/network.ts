// 위젯 페이지 시험의 가짜 네트워크. 가짜는 바깥 경계(HTTP) 하나에만 두고 그 안(위젯 클라이언트, 스트림 읽기, 대화의
// 규칙)은 진짜다(web-widget 명세 Testing Decisions 1, 선례는 관리 화면의 apps/admin/testing/). 스트림 프레임은 생성
// 타입으로 적어 계약이 바뀌면 핸들러가 컴파일에서 깨진다.
//
// 프레임은 서버처럼 `data:` 한 줄 다음에 `id:` 한 줄이고 줄 끝은 `\n` 이다(fastapi 0.141.1 의 `sse.py`). 프레임 사이에
// 시간 간격을 두고 `ReadableStream` 으로 낸다. 사이에 약속을 두면 그것이 풀릴 때까지 다음 프레임을 내지 않는다. 시험은
// 그 틈에 스트림이 열려 있는 동안의 화면을 본다.
//
// 못 만드는 것: 도중의 끊김. MSW 3.0.0 은 핸들러 스트림의 에러를 읽는 쪽에 끝으로 넘긴다(apps/admin/testing/stream.ts).
// 그래서 결말 없는 끊김은 결말 없이 닫는 것으로 만든다.

import type { EndUserItem } from "@agent-os/api-client";
import { HttpResponse } from "msw";
import { setupServer } from "msw/node";

export const network = setupServer();

/** 처리하지 않은 요청(메서드와 주소). 시험이 끝날 때 비어 있어야 한다. setup.ts 가 본다. */
export const unhandled: string[] = [];

/** 위젯이 부르는 주소. iframe 페이지의 출처 아래 최종 사용자 경로다. */
export function api(path: string): string {
  return new URL(`/end-user${path}`, location.origin).href;
}

const GAP_MS = 10;

/** 항목 하나의 프레임. `id` 는 그 이벤트의 인덱스다. */
export function frame(id: number, item: EndUserItem): string {
  return `data: ${JSON.stringify(item)}\nid: ${String(id)}\n\n`;
}

/** keepalive 주석. 서버의 것과 같은 바이트다. */
export const KEEPALIVE = ": ping\n\n";

/** 스트림의 한 걸음. 글자는 내보낼 바이트, 약속은 기다릴 자리다. */
export type Step = string | Promise<unknown>;

/** 걸음을 차례로 낸다. 다 내면 닫는다. */
export function stream(steps: readonly Step[]): Response {
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

/** 항목들을 0 부터 센 `id` 로 차례로 내고 닫는다. */
export function items(...list: readonly EndUserItem[]): Response {
  return stream(list.map((item, index) => frame(index, item)));
}

/** 풀어 줄 때까지 기다리는 자리. 스트림의 걸음에 넣어 그 틈의 화면을 본다. */
export function gate(): { readonly wait: Promise<void>; readonly open: () => void } {
  let open = () => {};
  const wait = new Promise<void>((resolve) => {
    open = resolve;
  });
  return { wait, open };
}

/** 서버가 내는 에러 봉투. 위젯은 상태 코드로만 가른다. */
export function rejection(status: number): Response {
  const codes: Record<number, string> = {
    401: "unauthorized",
    404: "not_found",
    409: "conflict",
    422: "invalid_request",
    429: "too_many_requests",
  };
  return HttpResponse.json(
    {
      code: codes[status] ?? "internal_error",
      message: "봉투의 문구",
      request_id: "req-0001",
      violations: [],
    },
    { status },
  );
}
