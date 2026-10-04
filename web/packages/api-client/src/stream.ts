// 재개 스트림(SSE)을 손으로 읽는다(ADR 0021). 잰 생성기 넷 중 스트림 항목의 스키마(`itemSchema`)를 쓰는 것이
// 없어 생성물의 SSE 응답은 `unknown` 이다(ADR 0010 의 2026-09-28 이력). openapi-fetch 의 `parseAs: "stream"` 으로
// 받은 본문을 여기서 프레임으로 가르고, 판별자만 보는 술어로 생성 타입 `Event` 로 좁힌다.
//
// 서버의 프레임은 `data:` 한 줄이고 `event:`·`id:` 를 싣지 않는다(`.claude/rules/http.md`). 그래도 파서는 SSE 의
// 규칙대로 읽는다. 줄 끝은 `\r\n` 과 `\n` 이고, 홀로 선 `\r` 은 줄 끝으로 받지 않는다(서버가 보내지 않는다).
//
// 술어를 지나지 못한 프레임은 버리지 않고 `data` 의 원문 그대로 넘긴다. `JSON.parse` 에 실패한 것도 같다. 스트림이
// 프레임 한가운데서 끝나면 남은 것을 프레임 하나로 닫아 같은 길로 넘긴다. "읽는 쪽이 모르는 것을 지우지 않고 들고
// 있게 한다"(ADR 0010·0012 이력)를 스트림에도 건다. 트레이스 상세의 `UnknownEvent` 를 빌려 쓰지 않는 이유는, 그것이
// 판별자만 모르는 줄이고 원문이 유효한 JSON 이기 때문이다(`adapters/jsonl.py` 의 `_require_raw_run`). 여기 원문은 JSON
// 이 아닐 수도 있다.
//
// 못 보는 것: `data` 줄이 없는 블록은 SSE 명세대로 프레임이 아니다. 주석(keepalive)과 `retry:`·`id:` 만 든 제어 블록이
// 그렇고, 모르는 필드 이름의 줄(`data:` 접두사가 빠진 JSON 한 줄 같은 것)만 든 블록도 조용히 사라진다. 서버는 그런
// 블록을 보내지 않는다.

import type { components } from "./generated/openapi";

/** 계약의 이벤트. 재개 스트림의 항목이 좁혀지는 타입이다. */
export type Event = components["schemas"]["Event"];

/** 재개 스트림의 프레임 하나. 술어를 지난 것은 이벤트이고, 지나지 못한 것은 `data` 의 원문 그대로다. */
export type StreamFrame =
  | { readonly kind: "event"; readonly event: Event }
  | { readonly kind: "raw"; readonly raw: string };

/** 계약의 이벤트 종류 전부. 빠지거나 넘치면 컴파일이 실패한다. */
export type EventTypes = Record<Event["type"], true>;

// 손으로 쓴 목록이지만 `satisfies` 가 생성 타입과 대조하므로 어긋날 수 없다(ADR 0021).
export const EVENT_TYPES = {
  run_started: true,
  llm_called: true,
  tool_called: true,
  run_paused: true,
  approval_granted: true,
  approval_denied: true,
  run_resumed: true,
  run_finished: true,
  run_failed: true,
  conversation_summarized: true,
} satisfies EventTypes;

/** 판별자만 본다. 객체이고 `type` 이 계약의 종류 가운데 하나면 참이다. 다른 필드는 서버를 믿는다. */
export function isEvent(value: unknown): value is Event {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof value.type === "string" &&
    Object.hasOwn(EVENT_TYPES, value.type)
  );
}

/** 끝난 프레임들의 `data` 값과, 아직 끝나지 않은 프레임의 원문. */
export interface Split {
  readonly data: readonly string[];
  readonly rest: string;
}

/**
 * 버퍼에서 빈 줄로 끝난 프레임들의 `data` 값을 떼어 낸다. 끝나지 않은 프레임은 `rest` 로 남기므로, 다음 조각을
 * `rest` 에 이어 붙여 다시 부르면 조각 경계가 프레임 한가운데서 갈려도 프레임 하나다.
 *
 * `data` 가 없는 프레임(keepalive 주석 `:` 뿐인 것)은 값을 내지 않는다. `data:` 뒤의 공백 하나는 값이 아니다.
 * 한 프레임의 `data` 줄이 여럿이면 줄바꿈으로 잇는다. 다른 필드(`event`, `id`, `retry`)는 값에 들지 않는다.
 */
export function splitFrames(buffer: string): Split {
  const data: string[] = [];
  let lines: string[] = [];
  let frameStart = 0;
  let lineStart = 0;
  for (let end = buffer.indexOf("\n"); end !== -1; end = buffer.indexOf("\n", lineStart)) {
    const line = buffer.slice(lineStart, buffer[end - 1] === "\r" ? end - 1 : end);
    lineStart = end + 1;
    if (line !== "") {
      lines.push(line);
      continue;
    }
    const values = lines.flatMap(dataValue);
    if (values.length > 0) {
      data.push(values.join("\n"));
    }
    lines = [];
    frameStart = lineStart;
  }
  return { data, rest: buffer.slice(frameStart) };
}

/** 줄 하나가 `data` 필드면 그 값 하나, 아니면 없음. 콜론이 없는 줄은 이름이 줄 전체이고 값이 비어 있다. */
function dataValue(line: string): string[] {
  const colon = line.indexOf(":");
  const name = colon === -1 ? line : line.slice(0, colon);
  if (name !== "data") {
    return [];
  }
  const value = colon === -1 ? "" : line.slice(colon + 1);
  return [value.startsWith(" ") ? value.slice(1) : value];
}

function classify(data: string): StreamFrame {
  const parsed = parseJson(data);
  return parsed.ok && isEvent(parsed.value)
    ? { kind: "event", event: parsed.value }
    : { kind: "raw", raw: data };
}

function parseJson(
  text: string,
): { readonly ok: true; readonly value: unknown } | { readonly ok: false } {
  try {
    const value: unknown = JSON.parse(text);
    return { ok: true, value };
  } catch {
    return { ok: false };
  }
}

/**
 * `parseAs: "stream"` 으로 받은 본문을 프레임으로 읽는다. 조각이 오는 대로 끝난 프레임을 넘긴다.
 *
 * 스트림의 수명은 부른 쪽의 것이다. 연결을 끊는 길은 요청에 준 `signal`(AbortController)이다. 끊으면 다음 조각을
 * 기다리던 읽기가 그 에러로 끝나고, 이 반복자가 그 에러를 던지며 잠금을 푼다. 응답이 오기 전에도 같은 길이다.
 * 반복자의 `return()` 으로는 끊지 못한다. 기다리던 읽기가 풀린 뒤(다음 조각이나 keepalive)에야 닿고, 그동안 스트림이
 * 잠겨 `stream.cancel()` 도 거부된다. 다 읽거나 루프에서 멈추면 잠금만 풀고 닫지 않는다.
 */
export async function* readFrames(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<StreamFrame, void, undefined> {
  const reader = stream.getReader();
  try {
    yield* framesFrom(reader);
  } finally {
    reader.releaseLock();
  }
}

async function* framesFrom(
  reader: ReadableStreamDefaultReader<Uint8Array>,
): AsyncGenerator<StreamFrame, void, undefined> {
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    // 끝나면 남은 것을 빈 줄로 닫아 프레임 하나로 넘긴다. SSE 명세는 끝나지 않은 프레임을 버리지만 여기서는
    // 버리지 않는다. 재접속이 없고, 기록의 원천은 스트림이 끝난 뒤 다시 읽는 트레이스다.
    buffer += done ? `${decoder.decode()}\n\n` : decoder.decode(value, { stream: true });
    const { data, rest } = splitFrames(buffer);
    for (const item of data) {
      yield classify(item);
    }
    if (done) {
      return;
    }
    buffer = rest;
  }
}
