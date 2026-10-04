// 클라이언트 둘의 타입 테스트. tsc 가 판정한다(`pnpm run typecheck`). `@ts-expect-error` 는 억제가 아니라
// "이 코드는 컴파일되면 안 된다"는 단언이다. 그 줄에 에러가 없으면 컴파일이 실패한다(ADR 0020).
//
// 토큰이 맡지 않은 경로에 실리는 실수를 타입이 막는지 본다. 헤더에 무엇이 실리는지는 페이지 테스트가 잰다
// (관리 요청은 05, 결정 요청은 08).

import { expectTypeOf } from "vitest";
import type { AdminClient, AdminPaths, ChannelClient, ChannelPaths } from "./clients";
import type { components, paths } from "./generated/openapi";
import { readFrames, type StreamFrame } from "./stream";

type Schemas = components["schemas"];

declare const 관리: AdminClient;
declare const 채널: ChannelClient;

// 결정은 `Decision` 타입의 값으로 넘긴다. 판별 유니온 본문을 인라인 리터럴로 주면 openapi-fetch 0.17.0 의 옵션 추론이
// 제약으로 떨어져 `parseAs: "stream"` 의 `data` 가 `unknown` 이 된다(`.scratch/web-admin/probes/immutable_readable.sh`).
const 결정: Schemas["Decision"] = { decision: "approve", pause_index: 0 };

export async function 관리_클라이언트는_관리_경로를_부른다(): Promise<void> {
  await 관리.GET("/plugins");
  await 관리.GET("/traces/{run_id}", { params: { path: { run_id: "r1" } } });
  await 관리.PUT("/plugins/{kind}/{name}/enabled", {
    params: { path: { kind: "agent", name: "echo" } },
    body: { enabled: false },
  });
}

export async function 관리_클라이언트의_목록_응답은_순회할_수_있는_배열이다(): Promise<void> {
  // 생성기의 `--immutable` 을 다시 켜는 조건을 판정하는 자리다(ADR 0021 의 2026-09-29 이력). 지금의 openapi-fetch 는
  // readonly 배열의 배열성을 지워 순회에서 컴파일이 실패한다(TS2488). 가변 배열과 같은지 보지 않고 순회할 수 있는지와
  // 원소가 생성 스키마에 들어가는지만 본다. 고쳐진 뒤 다시 켜면 readonly 배열이어도 여기가 초록이다.
  const plugins = await 관리.GET("/plugins");
  for (const row of plugins.data ?? []) {
    expectTypeOf(row).toExtend<Schemas["PluginRow"]>();
  }
  const trace = await 관리.GET("/traces/{run_id}", { params: { path: { run_id: "r1" } } });
  for (const event of trace.data?.events ?? []) {
    expectTypeOf(event).toExtend<Schemas["TraceEvent"]>();
  }
  for (const violation of trace.error?.violations ?? []) {
    expectTypeOf(violation).toExtend<Schemas["Violation"]>();
  }
}

export async function 관리_클라이언트로_채널_경로를_부르면_컴파일이_실패한다(): Promise<void> {
  // @ts-expect-error: 관리 클라이언트는 채널의 결정 경로를 모른다. 관리 토큰이 채널 경로에 실리지 않는다
  await 관리.POST("/runs/{run_id}/approval", { params: { path: { run_id: "r1" } }, body: 결정 });
  // @ts-expect-error: 관리 클라이언트는 실행을 일으키는 채널 경로도 모른다
  await 관리.POST("/runs", { body: { agent: "echo", request: "안녕" } });
  // @ts-expect-error: 관리 클라이언트는 끝난 실행을 이어 가는 채널 경로도 모른다. 관리는 실행을 일으키지 않는다
  await 관리.POST("/runs/{run_id}/continuation", {
    params: { path: { run_id: "r1" } },
    body: { agent: "echo", request: "그럼?" },
  });
}

export async function 채널_클라이언트로_관리_경로를_부르면_컴파일이_실패한다(): Promise<void> {
  // @ts-expect-error: 채널 클라이언트는 관리 경로를 모른다. 채널 토큰이 관리 경로에 실리지 않는다
  await 채널.GET("/plugins");
  // @ts-expect-error: 채널 클라이언트는 결정 경로 하나만 안다. 실행을 일으키는 경로도 모른다
  await 채널.POST("/runs", { body: { agent: "echo", request: "안녕" } });
}

export async function 결정_스트림은_본문을_스트림으로_에러를_봉투로_받는다(): Promise<void> {
  const { data, error } = await 채널.POST("/runs/{run_id}/approval", {
    params: { path: { run_id: "r1" } },
    body: 결정,
    parseAs: "stream",
  });
  // 스트림 경로에서도 에러는 스트림이 시작되기 전에 JSON 봉투로 나간다(`.claude/rules/http.md`).
  expectTypeOf(error).toEqualTypeOf<Schemas["ErrorEnvelope"] | undefined>();
  expectTypeOf(data).toEqualTypeOf<ReadableStream<Uint8Array<ArrayBuffer>> | null | undefined>();
  if (data) {
    for await (const frame of readFrames(data)) {
      expectTypeOf(frame).toEqualTypeOf<StreamFrame>();
    }
  }
}

// 경로 목록을 고정한다. 계약에 경로가 늘면 관리 클라이언트의 타입에 새 경로가 보여 여기서 컴파일이 실패한다.
// 채널의 경로면 `clients.ts` 의 채널 경로 목록에, 관리의 경로면 아래 목록에 더한다. 고칠 자리가 컴파일러 앞에 선다.
expectTypeOf<keyof AdminPaths>().toEqualTypeOf<
  | "/health"
  | "/plugins"
  | "/plugins/{kind}/{name}"
  | "/plugins/{kind}/{name}/enabled"
  | "/traces"
  | "/traces/{run_id}"
>();
expectTypeOf<keyof ChannelPaths>().toEqualTypeOf<"/runs/{run_id}/approval">();
expectTypeOf<Exclude<keyof paths, keyof AdminPaths>>().toEqualTypeOf<
  "/runs" | "/runs/{run_id}/approval" | "/runs/{run_id}/continuation"
>();
