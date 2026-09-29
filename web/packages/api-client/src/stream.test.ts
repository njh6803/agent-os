// 재개 스트림(SSE)을 읽는 층의 테스트. 프레임 파서와 판별자 술어는 순수 함수로, 스트림 읽기는 조각을 손으로
// 나눠 넣은 ReadableStream 으로 잰다. 네트워크를 타지 않는다. openapi-fetch 가 jsdom 의 MSW 스트림을 조각마다
// 넘기는 것은 설계 프로브(jsdom_sse.sh)가 쟀고, 화면을 지나는 것은 결정 화면 티켓(08)의 페이지 테스트가 잰다.

import { describe, expect, test } from "vitest";
import { EVENT_TYPES, isEvent, readFrames, splitFrames, type StreamFrame } from "./stream";

describe("SSE 프레임 파서", () => {
  test("빈 줄로 끝난 프레임의 data 를 떼어 내고 끝나지 않은 프레임은 남긴다", () => {
    expect(splitFrames('data: {"type":"run_started"}\n\ndata: {"type":')).toEqual({
      data: ['{"type":"run_started"}'],
      rest: 'data: {"type":',
    });
  });

  test("조각 경계가 프레임 한가운데서 갈려도 남은 것에 이어 붙이면 프레임 하나다", () => {
    const first = splitFrames('data: {"type":"run_');

    expect(first.data).toEqual([]);
    expect(splitFrames(`${first.rest}started"}\n\n`)).toEqual({
      data: ['{"type":"run_started"}'],
      rest: "",
    });
  });

  test("조각 경계가 data 줄 뒤, 프레임을 닫는 빈 줄 앞에서 갈려도 프레임 하나다", () => {
    const first = splitFrames("data: 1\n");

    expect(first.data).toEqual([]);
    expect(splitFrames(`${first.rest}\n`).data).toEqual(["1"]);
  });

  test("한 버퍼에 프레임이 여럿이면 차례대로 모두 떼어 낸다", () => {
    expect(splitFrames("data: 1\n\ndata: 2\n\ndata: 3\n\n").data).toEqual(["1", "2", "3"]);
  });

  test("keepalive 주석 줄은 프레임이 아니다", () => {
    expect(splitFrames(": ping\n\ndata: 1\n\n: ping\n\n").data).toEqual(["1"]);
  });

  test("줄 끝이 \\r\\n 이든 \\n 이든 같은 프레임이다", () => {
    expect(splitFrames("data: 1\r\n\r\ndata: 2\n\n: ping\r\n\r\n").data).toEqual(["1", "2"]);
  });

  test("\\r\\n 이 조각 사이에서 갈려도 줄 끝 하나다", () => {
    const first = splitFrames("data: 1\r");

    expect(splitFrames(`${first.rest}\n\r\n`).data).toEqual(["1"]);
  });

  test("data: 뒤의 공백 하나는 값이 아니고 둘째 공백부터는 값이다", () => {
    expect(splitFrames("data:1\n\ndata: 2\n\ndata:  3\n\n").data).toEqual(["1", "2", " 3"]);
  });

  test("한 프레임의 data 줄이 여럿이면 줄바꿈으로 이어 값 하나가 된다", () => {
    expect(splitFrames("data: 첫 줄\ndata: 둘째 줄\n\n").data).toEqual(["첫 줄\n둘째 줄"]);
  });

  test("data 가 아닌 필드는 값에 들지 않는다", () => {
    expect(splitFrames("event: run\nid: 7\nretry: 10\ndata: 1\n\n").data).toEqual(["1"]);
  });
});

describe("판별자 술어", () => {
  test("계약의 종류마다 참이다", () => {
    // 목록이 계약과 같은지는 컴파일러가 본다(stream.test-d.ts). 여기서는 술어가 그 목록을 쓰는지 본다.
    for (const type of Object.keys(EVENT_TYPES)) {
      expect(isEvent({ type }), type).toBe(true);
    }
  });

  test("판별자만 보고 다른 필드는 보지 않는다", () => {
    expect(isEvent({ type: "run_paused" })).toBe(true);
  });

  test("모르는 type 은 거짓이다", () => {
    expect(isEvent({ type: "run_exploded" })).toBe(false);
    // 트레이스 상세에만 있는 표지다. 스트림의 이벤트가 아니다.
    expect(isEvent({ type: "unknown", raw: "{}" })).toBe(false);
  });

  test("객체의 기본 속성 이름은 종류가 아니다", () => {
    for (const type of ["toString", "constructor", "__proto__", "hasOwnProperty"]) {
      expect(isEvent({ type }), type).toBe(false);
    }
  });

  test("객체가 아닌 것은 거짓이다", () => {
    for (const value of [null, undefined, "run_started", 1, true, [], ["run_started"]]) {
      expect(isEvent(value), JSON.stringify(value)).toBe(false);
    }
  });

  test("type 이 없거나 문자열이 아니면 거짓이다", () => {
    for (const value of [{}, { kind: "run_started" }, { type: 1 }, { type: null }]) {
      expect(isEvent(value), JSON.stringify(value)).toBe(false);
    }
  });
});

const encoder = new TextEncoder();

/** 준 조각을 차례로 흘리고 닫는 스트림. 문자열은 UTF-8 로 바꾼다. */
function streamOf(...chunks: readonly (string | Uint8Array)[]): ReadableStream<Uint8Array> {
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(typeof chunk === "string" ? encoder.encode(chunk) : chunk);
      }
      controller.close();
    },
  });
}

async function collect(stream: ReadableStream<Uint8Array>): Promise<StreamFrame[]> {
  const frames: StreamFrame[] = [];
  for await (const frame of readFrames(stream)) {
    frames.push(frame);
  }
  return frames;
}

const STARTED = { type: "run_started", run_id: "r1", ts: "2026-09-29T00:00:00Z" };

describe("재개 스트림 읽기", () => {
  test("조각이 프레임 한가운데서 갈려도 이벤트 하나로 온다", async () => {
    const frame = `data: ${JSON.stringify(STARTED)}\n\n`;

    expect(await collect(streamOf(frame.slice(0, 20), frame.slice(20)))).toEqual([
      { kind: "event", event: STARTED },
    ]);
  });

  test("여러 바이트 글자가 조각 사이에서 갈려도 깨지지 않는다", async () => {
    const paused = {
      type: "run_paused",
      run_id: "r1",
      ts: "2026-09-29T00:00:00Z",
      tool: "쓰기",
      args: {},
    };
    const text = `data: ${JSON.stringify(paused)}\n\n`;
    const bytes = encoder.encode(text);
    // "쓰" 는 UTF-8 로 세 바이트다. 그 첫 바이트 뒤에서 가른다.
    const inside = encoder.encode(text.slice(0, text.indexOf("쓰"))).length + 1;

    expect(await collect(streamOf(bytes.slice(0, inside), bytes.slice(inside)))).toEqual([
      { kind: "event", event: paused },
    ]);
  });

  test("keepalive 주석은 프레임으로 넘기지 않는다", async () => {
    expect(
      await collect(streamOf(": ping\n\n", `data: ${JSON.stringify(STARTED)}\n\n`, ": ping\n\n")),
    ).toEqual([{ kind: "event", event: STARTED }]);
  });

  test("술어를 지나지 못한 프레임은 버리지 않고 원문으로 넘기며 다음 프레임을 계속 읽는다", async () => {
    const stranger = '{"type":"run_exploded","run_id":"r1"}';

    expect(
      await collect(streamOf(`data: ${stranger}\n\ndata: ${JSON.stringify(STARTED)}\n\n`)),
    ).toEqual([
      { kind: "raw", raw: stranger },
      { kind: "event", event: STARTED },
    ]);
  });

  test("JSON 이 아닌 프레임도 원문으로 넘기며 다음 프레임을 계속 읽는다", async () => {
    expect(await collect(streamOf(`data: {깨진\n\ndata: ${JSON.stringify(STARTED)}\n\n`))).toEqual([
      { kind: "raw", raw: "{깨진" },
      { kind: "event", event: STARTED },
    ]);
  });

  test("스트림이 JSON 한가운데서 끝나면 남은 data 를 버리지 않고 원문으로 넘긴다", async () => {
    expect(await collect(streamOf('data: {"type":"run_fin'))).toEqual([
      { kind: "raw", raw: '{"type":"run_fin' },
    ]);
  });

  test("스트림이 프레임을 닫는 빈 줄 없이 끝나도 남은 프레임을 이벤트로 넘긴다", async () => {
    expect(await collect(streamOf(`data: ${JSON.stringify(STARTED)}\n`))).toEqual([
      { kind: "event", event: STARTED },
    ]);
  });

  test("다 읽으면 스트림의 잠금을 푼다", async () => {
    const stream = streamOf(`data: ${JSON.stringify(STARTED)}\n\n`);

    await collect(stream);

    expect(stream.locked).toBe(false);
  });

  test("요청을 끊어 다음 조각을 기다리던 스트림이 에러로 끝나면 그 에러를 던지고 잠금을 푼다", async () => {
    // 브라우저의 fetch 는 요청의 signal 이 끊기면 본문 스트림을 그 에러로 끝낸다. 여기서는 스트림을 손으로 끝낸다.
    let abort: (reason: unknown) => void = () => undefined;
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(STARTED)}\n\n`));
        abort = (reason) => {
          controller.error(reason);
        };
      },
    });
    const frames = readFrames(stream);
    expect((await frames.next()).value).toEqual({ kind: "event", event: STARTED });

    const waiting = frames.next();
    abort(new DOMException("요청을 끊었다", "AbortError"));

    await expect(waiting).rejects.toThrow("요청을 끊었다");
    expect(stream.locked).toBe(false);
  });

  test("읽는 쪽이 도중에 멈추면 잠금을 풀어 부른 쪽이 스트림을 닫을 수 있다", async () => {
    const stream = streamOf(
      `data: ${JSON.stringify(STARTED)}\n\n`,
      `data: ${JSON.stringify(STARTED)}\n\n`,
    );

    for await (const frame of readFrames(stream)) {
      expect(frame.kind).toBe("event");
      break;
    }

    expect(stream.locked).toBe(false);
    await expect(stream.cancel()).resolves.toBeUndefined();
  });
});
