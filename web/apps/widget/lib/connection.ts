// 위젯이 최종 사용자 경로에 닿는 길. 두 임베드는 기준 주소와 토큰을 받는 길이 달라(web-widget 명세 "임베드"), 대화를
// 돌리는 쪽(components/pages/useConversation)은 이것을 받아 쓰고 어느 임베드인지 모른다.
//
// - iframe 방식: 기준 주소는 자기 페이지의 출처이고, 토큰은 부모 창에 postMessage 로 묻는다(lib/token.ts).
// - 페이지 안 방식: 기준 주소는 번들 스크립트의 출처이고(element/base.ts), 토큰은 요소의 `tokenProvider` 를
//   부른다(element/token.ts).

import type { TokenResult } from "./token";

export interface Connection {
  /** 최종 사용자 경로의 기준 주소. 출처만 든다. 계약의 경로 키가 `/end-user` 를 이미 든다. */
  readonly baseUrl: URL;
  /** 요청을 보낼 때마다 부른다. 받지 못하면 null 이다. */
  readonly token: () => Promise<TokenResult>;
}
