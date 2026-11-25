// 공개 경로용 클라이언트와 생성 타입의 타입 테스트. tsc 가 판정한다(`pnpm run typecheck`). `@ts-expect-error` 는 억제가
// 아니라 "이 코드는 컴파일되면 안 된다"는 단언이다(ADR 0020). 요청이 실제로 보내는 모양은 `clients.test.ts` 가 잰다.

import { expectTypeOf } from "vitest";
import type { PublicClient, PublicPaths } from "./clients";
import type { components } from "./generated/openapi";

type Schemas = components["schemas"];
type Settings = Schemas["WidgetSettings"];

declare const 공개: PublicClient;

// 판 표시는 좁히지 않은 수다. 리터럴 `1` 로 좁혀지면 받은 판을 `1` 과 견주는 조건이 typescript-eslint 의
// `no-unnecessary-condition` 에 늘 같은 결과인 조건으로 걸린다(widget-admin-server 명세 "판 표시").
expectTypeOf<Settings["schema_version"]>().toEqualTypeOf<number>();

export function 받은_판을_견주는_조건은_늘_같은_결과로_막히지_않는다(설정: Settings): boolean {
  return 설정.schema_version === 1;
}

// 모든 칸이 늘 있다. 값이 없으면 `null` 이고 예시 질문은 빈 목록, 밝기 스위치 숨기기는 거짓이다(명세 "답의 모양").
// 빠질 수 있는 칸이 하나라도 있으면 `Required` 로 바꾼 것과 달라진다.
expectTypeOf<Settings>().toEqualTypeOf<Required<Settings>>();

expectTypeOf<Settings["agent"]>().toEqualTypeOf<string | null>();
expectTypeOf<Settings["example_questions"]>().toEqualTypeOf<string[]>();
expectTypeOf<Settings["hide_mode_switch"]>().toEqualTypeOf<boolean>();
expectTypeOf<NonNullable<Settings["mode"]>>().toEqualTypeOf<"light" | "dark">();
expectTypeOf<Settings["mode"]>().toEqualTypeOf<Schemas["Mode"] | null>();

export async function 공개_클라이언트는_위젯_설정을_이름으로_읽는다(): Promise<void> {
  const { data, error } = await 공개.GET("/widget-settings/{site}", {
    params: { path: { site: "demo" } },
  });
  expectTypeOf(data).toEqualTypeOf<Settings | undefined>();
  expectTypeOf(error).toEqualTypeOf<Schemas["ErrorEnvelope"] | undefined>();
}

export async function 공개_클라이언트로_경로_밖을_부르면_컴파일이_실패한다(): Promise<void> {
  // @ts-expect-error: 공개 클라이언트는 위젯 설정 경로 하나만 안다. 서버의 상태 경로도 부르지 않는다
  await 공개.GET("/health");
}

// 경로 목록을 고정한다. 공개 경로가 늘면 이 목록과 `clients.ts` 의 경로 목록이 함께 컴파일에서 걸린다.
expectTypeOf<keyof PublicPaths>().toEqualTypeOf<"/widget-settings/{site}">();
