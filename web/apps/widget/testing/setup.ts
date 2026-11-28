// 위젯 페이지 시험(widget-pages)의 격리. 테스트마다 그린 것을 걷고(페이지가 문서 뿌리에 단 속성도 그때 걷힌다),
// 엿본 함수와 가짜 시계와 환경 변수를 되돌리고, 핸들러와 사이트의 흉내를 걷고, 주소를 처음으로 돌리고, 위젯이 쓴
// sessionStorage 를 비운다. 한 테스트 안에서는 저장이 남아, 그린 것을 걷고 다시 그리면 같은 탭의 새로 고침이다.
//
// 열릴 때 받는 두 값(값 파일, lib/runtime.ts)은 사례마다 받은 상태로 미리 둔다(testing/runtime.ts). 그래서 사례는 값을 받는
// 동안의 화면을 거치지 않고 시작한다. 허용 출처는 사이트의 흉내 하나이고 글자 수 상한은 서버의 기본값 20,000 이다. 값 파일을
// 받는 길은 components/pages/WidgetSettings.test.tsx 가 따로 본다.
//
// 처리하지 않은 요청은 에러다. MSW 의 "error" 전략은 그 요청을 네트워크 에러로 끝내고 콘솔에 찍기만 해서 화면이
// 그것을 거절로 보이면 테스트는 초록일 수 있다(apps/admin/testing/setup.ts). 그래서 사건으로 받아 적고 테스트가 끝날
// 때 비어 있는지 본다.

import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, beforeEach, expect, vi } from "vitest";
import { clearRuntimeValues } from "../lib/runtime";
import { network, unhandled } from "./network";
import { seedValues } from "./runtime";
import { removeTokenListeners } from "./site";

beforeAll(() => {
  network.events.on("request:unhandled", ({ request }) => {
    unhandled.push(`${request.method} ${request.url}`);
  });
  network.listen({ onUnhandledFrame: "error" });
});

beforeEach(() => {
  seedValues(new URL(window.location.origin));
});

afterEach(() => {
  cleanup();
  clearRuntimeValues();
  vi.restoreAllMocks();
  vi.useRealTimers();
  vi.unstubAllEnvs();
  network.resetHandlers();
  removeTokenListeners();
  window.history.replaceState(null, "", "/");
  sessionStorage.clear();
  expect(unhandled.splice(0), "처리하지 않은 요청이 있다").toEqual([]);
});

afterAll(() => {
  network.close();
});
