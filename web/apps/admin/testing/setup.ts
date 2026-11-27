// 페이지 테스트의 격리(web-admin 명세 "주 이음매 — 페이지"). 테스트마다 그린 것을 걷고, 핸들러를 되돌리고,
// 화면 이동의 기록과 브라우저 저장소를 비운다. SWR 캐시는 render.tsx 가 그릴 때마다 새로 둔다.
//
// 처리하지 않은 요청은 에러다. "error" 전략은 그 요청을 네트워크 에러로 끝내고 콘솔에 찍기만 해서, 화면이 그것을
// "서버에 닿지 못했다"로 보이면 테스트는 초록일 수 있다(MSW 3.0.0 설치본의 코드를 읽었다). 그래서 사건으로 받아
// 적고 테스트가 끝날 때 비어 있는지 본다. 화면이 부르지 말아야 할 경로를 부르면 그 테스트가 빨갛다.

import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, expect, vi } from "vitest";
import { goTo } from "../api/session";
import { network, unhandled } from "./network";

// 화면 이동은 jsdom 이 지원하지 않는다(`location.assign`). 테스트는 어디로 보냈는지만 본다(`testing/session.ts` 의 `visited`).
vi.mock("../api/session/navigation", () => ({ goTo: vi.fn() }));

beforeAll(() => {
  network.events.on("request:unhandled", ({ request }) => {
    unhandled.push(`${request.method} ${request.url}`);
  });
  network.listen({ onUnhandledFrame: "error" });
});

afterEach(() => {
  cleanup();
  network.resetHandlers();
  vi.mocked(goTo).mockClear();
  history.replaceState(null, "", "/");
  sessionStorage.clear();
  localStorage.clear();
  // 테마가 그려지는 자리. 앞 시험이 단 속성이 남으면 "마운트 때 다시 단다"가 다는 일 없이 초록일 수 있다(admin-style 티켓 09).
  document.documentElement.removeAttribute("data-theme");
  expect(unhandled.splice(0), "처리하지 않은 요청이 있다").toEqual([]);
});

afterAll(() => {
  network.close();
});
