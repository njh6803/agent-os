// 옛 실행 화면의 주소가 대화 화면으로 옮겨 가는 설정(admin-login 티켓 11). 설정을 읽는 때는 `next.config.ts` 가 상류 주소를
// 판정하지만 기본 주소는 판정을 지나므로 환경 변수 없이 읽힌다. 실제 브라우저에서 따라가는 것은 e2e(reading.e2e.ts)가 본다.

import { expect, test } from "vitest";
import config from "../next.config.ts";

async function redirectsOf() {
  const redirects = await config.redirects?.();
  if (redirects === undefined) {
    throw new Error("설정에 옮기는 주소가 없다");
  }
  return redirects;
}

test("옛 실행 목록 주소는 대화 목록으로 옮겨 가고 브라우저가 기억하지 않는다", async () => {
  expect(await redirectsOf()).toContainEqual({
    source: "/runs",
    destination: "/chat",
    permanent: false,
  });
});

test("옛 실행 하나의 주소는 그 실행까지의 대화와 열린 패널로 옮겨 간다", async () => {
  expect(await redirectsOf()).toContainEqual({
    source: "/runs/:runId",
    destination: "/chat/:runId?run=:runId",
    permanent: false,
  });
});
