// 판별자 술어가 쓰는 종류 목록의 타입 테스트. tsc 가 판정한다. 손으로 쓴 목록이 생성 타입 `Event`·`EndUserItem` 의
// 종류와 어긋나면 컴파일이 실패한다는 것을 고정한다(ADR 0021).

import { expectTypeOf } from "vitest";
import {
  END_USER_ITEM_TYPES,
  EVENT_TYPES,
  readEndUserFrames,
  type EndUserItem,
  type EndUserItemTypes,
  type Event,
  type EventTypes,
} from "./stream";

// 지금의 목록은 계약의 종류와 같다. 계약에 종류가 늘면 `stream.ts` 의 목록에서 컴파일이 먼저 실패한다.
expectTypeOf<keyof typeof EVENT_TYPES>().toEqualTypeOf<Event["type"]>();
expectTypeOf<keyof typeof END_USER_ITEM_TYPES>().toEqualTypeOf<EndUserItem["type"]>();

declare const 하나_빠진_목록: Omit<typeof EVENT_TYPES, "run_started">;
declare const 하나_빠진_항목_목록: Omit<typeof END_USER_ITEM_TYPES, "calling">;

// @ts-expect-error: 계약의 종류가 목록에서 빠지면 컴파일이 실패한다
export const 빠진_목록 = 하나_빠진_목록 satisfies EventTypes;

// @ts-expect-error: 계약에 없는 종류가 목록에 들면 컴파일이 실패한다
export const 넘친_목록 = { ...EVENT_TYPES, run_exploded: true } satisfies EventTypes;

// @ts-expect-error: 계약의 항목 종류(calling)가 목록에서 빠지면 컴파일이 실패한다
export const 빠진_항목_목록 = 하나_빠진_항목_목록 satisfies EndUserItemTypes;

declare const 스트림: ReadableStream<Uint8Array>;

export async function 항목은_판별자로_좁혀지고_부르기_시작함은_도구_이름의_목록을_든다(): Promise<void> {
  for await (const frame of readEndUserFrames(스트림)) {
    if (frame.kind === "item") {
      expectTypeOf(frame.id).toEqualTypeOf<number>();
      if (frame.item.type === "calling") {
        expectTypeOf(frame.item.tools).toEqualTypeOf<string[]>();
      }
    } else if (frame.kind === "raw") {
      expectTypeOf(frame.id).toEqualTypeOf<number | null>();
      expectTypeOf(frame.raw).toEqualTypeOf<string>();
    }
  }
}
