// 위젯이 부를 곳을 읽는다. (1) 사이트 페이지의 커스텀 요소는 속성에서, (2) iframe 페이지는 자기 주소에서 읽는다.
// iframe 페이지는 채널과 같은 출처에서 서고 관리 화면처럼 /api 아래를 채널로 넘기므로(Next 의 rewrites, 또는 측정의
// 가짜 서버), 기준 주소가 지금의 `apiBaseUrl()`(`packages/api-client/src/clients.ts`)과 같은 모양이다. 토큰을 무엇으로
// 어떻게 넘길지(최종 사용자 인증)는 이 측정의 범위 밖이라, 측정에서는 가짜 토큰을 그대로 넘긴다.

import type { RunTarget } from "../api/runs";

export function targetFromElement(host: Element): RunTarget {
  return {
    baseUrl: host.getAttribute("api-base") ?? "",
    token: host.getAttribute("token") ?? "",
    agent: host.getAttribute("agent") ?? "",
  };
}

export function targetFromLocation(where: Location): RunTarget {
  const query = new URLSearchParams(where.search);
  return {
    baseUrl: new URL("/api", where.origin).href,
    token: query.get("token") ?? "",
    agent: query.get("agent") ?? "",
  };
}
