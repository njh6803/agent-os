// 중계가 경로를 어느 상류로 넘기는지. 실제 소켓은 위젯 e2e 와 질문 페이지 e2e 가 지나고, 여기서는 경로를 상류로 가르는 순수
// 함수만 본다.

import { expect, test } from "vitest";
import { upstreamOf } from "./relay.ts";

const SERVE = "http://127.0.0.1:1001";
const NEXT = "http://127.0.0.1:1002";
const PORTAL = "http://127.0.0.1:1003";

const WITH_PORTAL = { serve: SERVE, next: NEXT, portal: PORTAL };
const WITHOUT_PORTAL = { serve: SERVE, next: NEXT };

test("최종 사용자 경로는 serve 로, 위젯 경로는 Next 로 넘긴다", () => {
  expect(upstreamOf("/end-user/runs", WITH_PORTAL)).toBe(SERVE);
  expect(upstreamOf("/widget", WITH_PORTAL)).toBe(NEXT);
  expect(upstreamOf("/widget?agent=calc", WITH_PORTAL)).toBe(NEXT);
  expect(upstreamOf("/widget/element.js", WITH_PORTAL)).toBe(NEXT);
});

test("질문 페이지 상류가 있으면 루트와 /portal/ 아래를 그 상류로 넘긴다", () => {
  expect(upstreamOf("/", WITH_PORTAL)).toBe(PORTAL);
  expect(upstreamOf("/?site=demo", WITH_PORTAL)).toBe(PORTAL);
  expect(upstreamOf("/portal/", WITH_PORTAL)).toBe(PORTAL);
  expect(upstreamOf("/portal/sites/demo/token", WITH_PORTAL)).toBe(PORTAL);
  expect(upstreamOf("/portal/fonts/a.woff2", WITH_PORTAL)).toBe(PORTAL);
});

test("루트는 정확히 루트만 넘기고 /portal 은 끝 슬래시가 없으면 넘기지 않는다", () => {
  expect(upstreamOf("/portal", WITH_PORTAL)).toBeNull();
  expect(upstreamOf("/portalx/", WITH_PORTAL)).toBeNull();
  expect(upstreamOf("/other", WITH_PORTAL)).toBeNull();
});

test("질문 페이지 상류를 주지 않으면 루트와 /portal/ 아래도 넘기지 않는다(위젯 e2e 의 동작이 그대로다)", () => {
  expect(upstreamOf("/", WITHOUT_PORTAL)).toBeNull();
  expect(upstreamOf("/?site=demo", WITHOUT_PORTAL)).toBeNull();
  expect(upstreamOf("/portal/", WITHOUT_PORTAL)).toBeNull();
  expect(upstreamOf("/portal/sites/demo/token", WITHOUT_PORTAL)).toBeNull();
  expect(upstreamOf("/end-user/runs", WITHOUT_PORTAL)).toBe(SERVE);
  expect(upstreamOf("/widget", WITHOUT_PORTAL)).toBe(NEXT);
});
