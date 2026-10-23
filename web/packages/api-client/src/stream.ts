// SSE 스트림을 손으로 읽는다(ADR 0021). 잰 생성기 넷 중 스트림 항목의 스키마(`itemSchema`)를 쓰는 것이 없어
// 생성물의 SSE 응답은 `unknown` 이다(ADR 0010 의 2026-09-28 이력). openapi-fetch 의 `parseAs: "stream"` 으로 받은
// 본문을 여기서 빈 줄로 끝나는 블록으로 가르고, 판별자만 보는 술어로 생성 타입에 좁힌다. 읽기는 둘이고 블록을
// 가르는 것까지 같다.
//
// - `readFrames`: 운영자 채널(`/runs`)의 재개 스트림. 프레임은 `data:` 한 줄이고 `event:`·`id:` 가 없다
//   (`.claude/rules/http.md`). 항목은 생성 타입 `Event` 다.
// - `readEndUserFrames`: 최종 사용자 경로의 스트림(위젯의 것). 프레임은 `data:` 한 줄과 `id:` 한 줄이다. 항목은
//   생성 타입 `EndUserItem` 이고, 프레임의 `id` 가 결정의 `pause_index` 와 구독의 `Last-Event-ID` 가 된다.
//
// 둘 다 SSE 의 규칙대로 읽는다. 줄 끝은 `\r\n` 과 `\n` 이고, 홀로 선 `\r` 은 줄 끝으로 받지 않는다(서버가 보내지
// 않는다). 술어를 지나지 못한 프레임은 버리지 않고 `data` 의 원문 그대로 넘긴다. `JSON.parse` 에 실패한 것도 같다.
// 스트림이 프레임 한가운데서 끝나면 남은 것을 버리지 않고 넘긴다. "읽는 쪽이 모르는 것을 지우지 않고 들고 있게
// 한다"(ADR 0010·0012 이력)를 스트림에도 건다. 트레이스 상세의 `UnknownEvent` 를 빌려 쓰지 않는 이유는, 그것이
// 판별자만 모르는 줄이고 원문이 유효한 JSON 이기 때문이다(`adapters/jsonl.py` 의 `_require_raw_run`). 여기 원문은
// JSON 이 아닐 수도 있다.
//
// 두 읽기는 같은 블록을 받아 다르게 넘긴다. 운영자 쪽은 블록의 `data` 만 보고, 최종 사용자 쪽은 `id` 와 주석과 블록이
// 빈 줄로 닫혔는지도 본다. 그래서 갈리는 블록은 이렇다.
//
// - `data` 가 없는 블록. 운영자 쪽은 SSE 명세대로 그것을 프레임으로 보지 않아 주석(keepalive)과 `retry:`·`id:` 만 든
//   제어 블록, 모르는 필드 이름의 줄만 든 블록이 조용히 사라진다. 서버는 앞의 것만 보낸다. 최종 사용자 쪽은 주석만
//   든 블록을 keepalive 값으로 낸다. 위젯의 무응답 판정이 그것을 세어, 도구가 오래 도는 동안에도 스트림이 살아
//   있는지 안다(web-widget 명세 "api-client"). 나머지는 그 줄들을 원문으로 낸다.
// - `id` 가 없거나, 십진 정수가 아니거나, 안전한 정수(`Number.isSafeInteger`)의 범위를 넘는 블록. 운영자 쪽은 술어를
//   지나면 이벤트이고, 최종 사용자 쪽은 원문이다.
// - 스트림이 끝날 때 남은 닫히지 않은 블록. 운영자 쪽은 닫힌 블록과 같은 길로 넘기고, 최종 사용자 쪽은 늘 `id` 없는
//   원문으로 낸다(`unclosedFrame`).

import type { components } from "./generated/openapi";

/** 계약의 이벤트. 재개 스트림의 항목이 좁혀지는 타입이다. */
export type Event = components["schemas"]["Event"];

/** 계약의 최종 사용자 항목. 최종 사용자 스트림의 항목이 좁혀지는 타입이다. */
export type EndUserItem = components["schemas"]["EndUserItem"];

/** 재개 스트림의 프레임 하나. 술어를 지난 것은 이벤트이고, 지나지 못한 것은 `data` 의 원문 그대로다. */
export type StreamFrame =
  | { readonly kind: "event"; readonly event: Event }
  | { readonly kind: "raw"; readonly raw: string };

/**
 * 최종 사용자 스트림에서 온 블록 하나. 항목은 늘 십진 정수 `id` 를 든다. 술어나 `id` 를 지나지 못한 프레임은
 * `data` 의 원문(그것이 없으면 블록의 줄들)과 읽은 `id`(없거나 안전한 정수 범위의 십진 정수가 아니면 null)다. 스트림이 빈 줄로 닫기
 * 전에 끝나 남은 블록은 `id` 가 잘렸을 수 있어 늘 원문이고 `id` 가 null 이다. 주석만 든 블록은 서버의 keepalive 가
 * 왔다는 값이다.
 */
export type EndUserFrame =
  | { readonly kind: "item"; readonly id: number; readonly item: EndUserItem }
  | { readonly kind: "raw"; readonly id: number | null; readonly raw: string }
  | { readonly kind: "keepalive" };

/** 계약의 이벤트 종류 전부. 빠지거나 넘치면 컴파일이 실패한다. */
export type EventTypes = Record<Event["type"], true>;

/** 계약의 최종 사용자 항목 종류 전부. 빠지거나 넘치면 컴파일이 실패한다. */
export type EndUserItemTypes = Record<EndUserItem["type"], true>;

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

export const END_USER_ITEM_TYPES = {
  started: true,
  calling: true,
  progress: true,
  paused: true,
  decided: true,
  finished: true,
  failed: true,
  unfinished: true,
} satisfies EndUserItemTypes;

/** 판별자만 본다. 객체이고 `type` 이 계약의 종류 가운데 하나면 참이다. 다른 필드는 서버를 믿는다. */
export function isEvent(value: unknown): value is Event {
  return hasKnownType(value, EVENT_TYPES);
}

/** 판별자만 본다. 객체이고 `type` 이 계약의 항목 종류 가운데 하나면 참이다. 다른 필드는 서버를 믿는다. */
export function isEndUserItem(value: unknown): value is EndUserItem {
  return hasKnownType(value, END_USER_ITEM_TYPES);
}

function hasKnownType(value: unknown, types: Readonly<Record<string, true>>): boolean {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    typeof value.type === "string" &&
    Object.hasOwn(types, value.type)
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
  const { blocks, rest } = splitBlocks(buffer);
  return { data: blocks.flatMap((lines) => dataOf(lines) ?? []), rest };
}

/** 빈 줄로 끝난 블록들의 줄과 아직 끝나지 않은 블록의 원문. 줄이 하나도 없는 블록(빈 줄이 겹친 것)은 없다. */
interface Blocks {
  readonly blocks: readonly (readonly string[])[];
  readonly rest: string;
}

function splitBlocks(buffer: string): Blocks {
  const blocks: string[][] = [];
  let lines: string[] = [];
  let blockStart = 0;
  let lineStart = 0;
  for (let end = buffer.indexOf("\n"); end !== -1; end = buffer.indexOf("\n", lineStart)) {
    const line = buffer.slice(lineStart, buffer[end - 1] === "\r" ? end - 1 : end);
    lineStart = end + 1;
    if (line !== "") {
      lines.push(line);
      continue;
    }
    if (lines.length > 0) {
      blocks.push(lines);
    }
    lines = [];
    blockStart = lineStart;
  }
  return { blocks, rest: buffer.slice(blockStart) };
}

/** 줄 하나의 필드 이름과 값. 콜론이 없는 줄은 이름이 줄 전체이고 값이 비어 있다. 주석 줄은 이름이 빈 문자열이다. */
interface Field {
  readonly name: string;
  readonly value: string;
}

function fieldOf(line: string): Field {
  const colon = line.indexOf(":");
  if (colon === -1) {
    return { name: line, value: "" };
  }
  const value = line.slice(colon + 1);
  return { name: line.slice(0, colon), value: value.startsWith(" ") ? value.slice(1) : value };
}

/** 블록의 `data` 값. 줄이 여럿이면 줄바꿈으로 잇고, 하나도 없으면 없음이다. */
function dataOf(lines: readonly string[]): string | null {
  const values = lines
    .map(fieldOf)
    .flatMap((field) => (field.name === "data" ? [field.value] : []));
  return values.length > 0 ? values.join("\n") : null;
}

// 블록의 마지막 `id` 줄이 십진 정수면 그 값이다. SSE 명세는 `id` 없는 이벤트에 앞 이벤트의 것을 이어 주지만 서버는
// 프레임마다 싣는다. 이어 주면 `id` 를 빠뜨린 프레임이 앞 프레임의 자리를 결정의 `pause_index` 로 들게 되므로 블록의
// 것만 본다.
function idOf(lines: readonly string[]): number | null {
  const ids = lines.map(fieldOf).filter((field) => field.name === "id");
  const last = ids.at(-1)?.value;
  if (last === undefined || !/^[0-9]+$/.test(last)) {
    return null;
  }
  const id = Number(last);
  return Number.isSafeInteger(id) ? id : null;
}

function classify(data: string): StreamFrame {
  const parsed = parseJson(data);
  return parsed.ok && isEvent(parsed.value)
    ? { kind: "event", event: parsed.value }
    : { kind: "raw", raw: data };
}

function endUserFrame(lines: readonly string[]): EndUserFrame {
  if (lines.every((line) => line.startsWith(":"))) {
    return { kind: "keepalive" };
  }
  const id = idOf(lines);
  const data = dataOf(lines);
  if (data === null) {
    return { kind: "raw", id, raw: lines.join("\n") };
  }
  const parsed = parseJson(data);
  return id !== null && parsed.ok && isEndUserItem(parsed.value)
    ? { kind: "item", id, item: parsed.value }
    : { kind: "raw", id, raw: data };
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
 * `parseAs: "stream"` 으로 받은 재개 스트림의 본문을 프레임으로 읽는다. 조각이 오는 대로 끝난 프레임을 넘긴다.
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
    for await (const { lines } of blocksFrom(reader)) {
      const data = dataOf(lines);
      if (data !== null) {
        yield classify(data);
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * `parseAs: "stream"` 으로 받은 최종 사용자 스트림의 본문을 읽는다. 조각이 오는 대로 끝난 블록을 하나씩 넘긴다.
 * 수명과 끊는 길은 `readFrames` 와 같다.
 */
export async function* readEndUserFrames(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<EndUserFrame, void, undefined> {
  const reader = stream.getReader();
  try {
    for await (const { lines, closed } of blocksFrom(reader)) {
      yield closed ? endUserFrame(lines) : unclosedFrame(lines);
    }
  } finally {
    reader.releaseLock();
  }
}

// 스트림이 빈 줄로 닫기 전에 끝난 블록. 서버는 `data` 다음에 `id` 를 실어(fastapi 0.141.1 의 `sse.py`) `id` 가
// 잘렸을 수 있다. 그 값이 결정의 `pause_index` 나 구독의 `Last-Event-ID` 가 되면 엉뚱한 자리를 가리키므로 읽지
// 않는다.
function unclosedFrame(lines: readonly string[]): EndUserFrame {
  return { kind: "raw", id: null, raw: dataOf(lines) ?? lines.join("\n") };
}

/** 블록 하나의 줄과 그 블록이 빈 줄로 닫혔는지. 닫히지 않은 블록은 스트림이 끝날 때 남은 것뿐이다. */
interface Block {
  readonly lines: readonly string[];
  readonly closed: boolean;
}

async function* blocksFrom(
  reader: ReadableStreamDefaultReader<Uint8Array>,
): AsyncGenerator<Block, void, undefined> {
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) {
      // 남은 것을 빈 줄로 닫아 닫히지 않은 블록 하나로 넘긴다. SSE 명세는 끝나지 않은 프레임을 버리지만 여기서는
      // 버리지 않는다. 운영자 쪽은 재접속이 없고 기록의 원천이 스트림이 끝난 뒤 다시 읽는 트레이스다. 최종 사용자
      // 쪽은 그것을 원문으로 내고, 위젯이 원문을 건너뛰고 마지막으로 받은 `id` 부터 다시 구독한다.
      const { blocks } = splitBlocks(`${buffer}${decoder.decode()}\n\n`);
      yield* blocks.map((lines) => ({ lines, closed: false }));
      return;
    }
    const { blocks, rest } = splitBlocks(buffer + decoder.decode(value, { stream: true }));
    yield* blocks.map((lines) => ({ lines, closed: true }));
    buffer = rest;
  }
}
