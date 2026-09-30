// 페이지 테스트의 격리(web-admin 명세 "주 이음매 — 페이지"). 테스트마다 그린 것을 걷고, 핸들러를 되돌리고,
// 스토어와 브라우저 저장소를 비운다. SWR 캐시는 render.tsx 가 그릴 때마다 새로 둔다.
//
// 처리하지 않은 요청은 에러다. "error" 전략은 그 요청을 네트워크 에러로 끝내고 콘솔에 찍기만 해서, 화면이 그것을
// "서버에 닿지 못했다"로 보이면 테스트는 초록일 수 있다(MSW 3.0.0 설치본의 코드를 읽었다). 그래서 사건으로 받아
// 적고 테스트가 끝날 때 비어 있는지 본다. 화면이 부르지 말아야 할 경로를 부르면 그 테스트가 빨갛다.

import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, expect } from "vitest";
import { useTokens } from "../stores/tokens";
import { network, unhandled } from "./network";

beforeAll(() => {
  network.events.on("request:unhandled", ({ request }) => {
    unhandled.push(`${request.method} ${request.url}`);
  });
  network.listen({ onUnhandledFrame: "error" });
});

afterEach(() => {
  cleanup();
  network.resetHandlers();
  useTokens.setState(useTokens.getInitialState(), true);
  sessionStorage.clear();
  localStorage.clear();
  expect(unhandled.splice(0), "처리하지 않은 요청이 있다").toEqual([]);
});

afterAll(() => {
  network.close();
});
