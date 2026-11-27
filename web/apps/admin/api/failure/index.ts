// 요청이 데이터 대신 돌려준 것(web-admin 명세 "새로 고침과 상태"). 화면은 봉투의 message 와 request_id 를 보인다.
// 봉투가 아니면(네트워크 실패, 중계가 상류에 닿지 못함) "서버에 닿지 못했다"를 보인다. 에러 봉투는 토큰을 싣지
// 않는다(.claude/rules/http.md). 그래서 여기 든 글자를 그대로 화면에 올려도 토큰이 드러나지 않는다.

import type { components } from "@agent-os/api-client";

export type ErrorEnvelope = components["schemas"]["ErrorEnvelope"];

/** 봉투가 없는 실패의 문구. 네트워크 실패와 중계가 상류에 닿지 못한 것이 여기 든다. */
export const UNREACHABLE = "서버에 닿지 못했다";

export class RequestFailure extends Error {
  /** 응답의 상태 코드. 응답이 없었으면 null 이다. */
  readonly status: number | null;
  /** 서버의 에러 봉투. 응답이 봉투의 모양이 아니었으면 null 이다. */
  readonly envelope: ErrorEnvelope | null;

  constructor(status: number | null, envelope: ErrorEnvelope | null, options?: ErrorOptions) {
    super(envelope === null ? UNREACHABLE : envelope.message, options);
    this.name = "RequestFailure";
    this.status = status;
    this.envelope = envelope;
  }
}

/** 데이터가 아닌 응답. openapi-fetch 는 JSON 이 아닌 에러 본문을 글자로 주므로 모양을 보고 봉투로 좁힌다. */
export function failureOf(status: number, body: unknown): RequestFailure {
  return new RequestFailure(status, isEnvelope(body) ? body : null);
}

/** 응답을 받지 못한 요청. */
export function unreachable(cause: unknown): RequestFailure {
  return new RequestFailure(null, null, { cause });
}

/** 화면에 보일 것. 봉투가 없으면 서버에 닿지 못한 것이다. */
export function describeFailure(error: unknown): {
  readonly message: string;
  readonly requestId: string | null;
} {
  if (error instanceof RequestFailure && error.envelope !== null) {
    return { message: error.envelope.message, requestId: error.envelope.request_id };
  }
  return { message: UNREACHABLE, requestId: null };
}

function isEnvelope(value: unknown): value is ErrorEnvelope {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    typeof value.code === "string" &&
    "message" in value &&
    typeof value.message === "string" &&
    "request_id" in value &&
    typeof value.request_id === "string" &&
    "violations" in value &&
    Array.isArray(value.violations)
  );
}
