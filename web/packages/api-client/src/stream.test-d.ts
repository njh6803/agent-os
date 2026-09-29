// 판별자 술어가 쓰는 종류 목록의 타입 테스트. tsc 가 판정한다. 손으로 쓴 목록이 생성 타입 `Event` 의 종류와
// 어긋나면 컴파일이 실패한다는 것을 고정한다(ADR 0021).

import { expectTypeOf } from "vitest";
import { EVENT_TYPES, type Event, type EventTypes } from "./stream";

// 지금의 목록은 계약의 종류와 같다. 계약에 종류가 늘면 `stream.ts` 의 목록에서 컴파일이 먼저 실패한다.
expectTypeOf<keyof typeof EVENT_TYPES>().toEqualTypeOf<Event["type"]>();

declare const 하나_빠진_목록: Omit<typeof EVENT_TYPES, "run_started">;

// @ts-expect-error: 계약의 종류가 목록에서 빠지면 컴파일이 실패한다
export const 빠진_목록 = 하나_빠진_목록 satisfies EventTypes;

// @ts-expect-error: 계약에 없는 종류가 목록에 들면 컴파일이 실패한다
export const 넘친_목록 = { ...EVENT_TYPES, run_exploded: true } satisfies EventTypes;
