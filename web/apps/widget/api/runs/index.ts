// 최종 사용자 경로의 요청 함수(web-widget 티켓 05). 위젯 클라이언트만 쓴다. 기준 주소는 부르는 쪽이 임베드마다 넘기고
// (lib/connection.ts), 최종 사용자 경로는 그 아래 `/end-user` 다(web-widget 명세 "임베드"의 API 의 기준 주소). iframe
// 방식은 위젯 페이지와 같은 출처라 CORS 를 지나지 않고, 페이지 안 방식은 사이트의 출처에서 CORS 로 부른다. 토큰은
// 클라이언트가 들지 않고 요청마다 `Authorization` 으로 넘긴다.

import {
  createWidgetClient,
  readEndUserFrames,
  type EndUserFrame,
  type EndUserItem,
} from "@agent-os/api-client";

export type { EndUserFrame, EndUserItem };

/** 상한에 걸린 429 가 든 것. 둘 다 없거나 읽지 못하면 null 이다. */
export interface LimitDetail {
  /** 봉투의 `limit`. 계약 밖의 값도 그대로다. */
  readonly limit: string | null;
  /** `Retry-After` 헤더의 원문. */
  readonly retryAfter: string | null;
}

/**
 * 실행이 받아들여지지 않았다. 응답의 상태 코드이고, 응답 전에 네트워크가 실패했으면 null 이다. 429 면 상한의 종류와
 * `Retry-After` 를 함께 든다.
 */
export class RunRejected extends Error {
  readonly status: number | null;
  /** 상한의 종류와 `Retry-After`. 그것을 들지 않은 응답이면 둘 다 null 이다. */
  readonly detail: LimitDetail;

  constructor(
    status: number | null,
    detail: LimitDetail = { limit: null, retryAfter: null },
    options?: ErrorOptions,
  ) {
    super(status === null ? "응답 전에 네트워크가 실패했다" : `상태 ${String(status)}`, options);
    this.name = "RunRejected";
    this.status = status;
    this.detail = detail;
  }
}

/**
 * 에러 본문의 `limit`. openapi-fetch 는 에러 본문을 JSON 으로 풀지 못하면 글자 그대로 넘기므로(프록시가 낸 429 등)
 * 생성 타입을 믿지 않고 실행 중에 모양을 본다.
 */
function limitOf(body: unknown): string | null {
  return typeof body === "object" &&
    body !== null &&
    "limit" in body &&
    typeof body.limit === "string"
    ? body.limit
    : null;
}

/**
 * 실행 하나를 일으킨다. `continueFrom` 이 있으면 그 실행의 이어 가기(`POST /runs/{run_id}/continuation`)이고 없으면
 * 시작(`POST /runs`)이다. 받아들여지면 스트림의 블록을 받는 대로 내는 반복자를 돌려주고, 아니면 RunRejected 를
 * 던진다. 스트림 경로에서도 에러는 스트림이 시작되기 전에 JSON 봉투로 온다(.claude/rules/http.md). 위젯은 상태 코드로
 * 가르고 봉투의 `message` 는 읽지 않는다(web-widget 명세 "요청이 거절될 때"). 429 의 `limit` 과 `Retry-After` 만 읽는다.
 *
 * 연결은 `signal` 로 끊는다. 응답 전이면 이 함수가, 응답 뒤면 반복자가 그 에러를 던진다(`readEndUserFrames`).
 */
export async function sendRun(
  baseUrl: URL,
  token: string,
  agent: string,
  request: string,
  continueFrom: string | null,
  signal: AbortSignal,
): Promise<AsyncGenerator<EndUserFrame, void, undefined>> {
  const client = createWidgetClient(baseUrl);
  const init = {
    headers: { Authorization: `Bearer ${token}` },
    body: { agent, request },
    parseAs: "stream" as const,
    signal,
  };
  const call =
    continueFrom === null
      ? client.POST("/end-user/runs", init)
      : client.POST("/end-user/runs/{run_id}/continuation", {
          ...init,
          params: { path: { run_id: continueFrom } },
        });
  return framesOf(call, signal);
}

/** 결정 하나. 거부에만 사유가 있다. `pause_index` 는 그 승인 묻기의 `paused` 프레임의 `id` 다. */
export type DecisionBody =
  | { readonly decision: "approve"; readonly pause_index: number }
  | { readonly decision: "deny"; readonly reason: string; readonly pause_index: number };

/**
 * 멈춘 실행에 결정 하나를 낸다(`POST /runs/{run_id}/approval`). 받아들여지면 결정 항목부터 실행을 흘리는 반복자를
 * 돌려주고, 아니면 RunRejected 를 던진다. 끊는 것과 에러는 `sendRun` 과 같다.
 */
export async function sendDecision(
  baseUrl: URL,
  token: string,
  runId: string,
  body: DecisionBody,
  signal: AbortSignal,
): Promise<AsyncGenerator<EndUserFrame, void, undefined>> {
  const call = createWidgetClient(baseUrl).POST("/end-user/runs/{run_id}/approval", {
    headers: { Authorization: `Bearer ${token}` },
    params: { path: { run_id: runId } },
    body,
    parseAs: "stream",
    signal,
  });
  return framesOf(call, signal);
}

/**
 * 실행을 다시 구독한다(`GET /runs/{run_id}/subscription`). `lastEventId` 프레임 뒤부터 받는다. 끊는 것과
 * 에러는 `sendRun` 과 같다.
 */
export async function subscribeRun(
  baseUrl: URL,
  token: string,
  runId: string,
  lastEventId: number,
  signal: AbortSignal,
): Promise<AsyncGenerator<EndUserFrame, void, undefined>> {
  const call = createWidgetClient(baseUrl).GET("/end-user/runs/{run_id}/subscription", {
    headers: { Authorization: `Bearer ${token}`, "Last-Event-ID": String(lastEventId) },
    params: { path: { run_id: runId } },
    parseAs: "stream",
    signal,
  });
  return framesOf(call, signal);
}

/** 보낸 요청의 응답이 받아들여졌으면 스트림의 블록을 받는 대로 내는 반복자이고, 아니면 RunRejected 를 던진다. */
async function framesOf(
  call: Promise<{
    readonly data?: ReadableStream<Uint8Array> | null;
    readonly error?: unknown;
    readonly response: Response;
  }>,
  signal: AbortSignal,
): Promise<AsyncGenerator<EndUserFrame, void, undefined>> {
  const { data, error, response } = await call.catch((cause: unknown) => {
    if (signal.aborted) {
      throw cause;
    }
    throw new RunRejected(null, undefined, { cause });
  });
  if (data === undefined || data === null) {
    throw new RunRejected(response.status, {
      limit: limitOf(error),
      retryAfter: response.headers.get("Retry-After"),
    });
  }
  return readEndUserFrames(data);
}
