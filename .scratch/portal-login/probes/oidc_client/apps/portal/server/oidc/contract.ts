// 세 후보(가 openid-client, 나 oauth4webapi+jose, 다 직접 구현)가 함께 지키는 모양. 프로브의 것이고 제품 코드가 아니다.
//
// 질문 페이지 서버는 상태를 두지 않으므로 로그인 한 번을 두 걸음으로 가른다. `begin` 이 인가 요청 주소와 브라우저 왕복을
// 건너 들고 있을 값(`Pending`)을 내고, `finish` 가 돌아온 요청의 주소와 그 값을 받아 `sub` 를 낸다. `Pending` 은 글 셋이라
// 쿠키에 실을 수 있다. 두 걸음 모두 Promise 를 돌려준다(설정 문서 조회와 토큰 교환이 HTTP 호출이다).

export interface Pending {
  readonly state: string;
  readonly nonce: string;
  readonly codeVerifier: string;
}

export interface LoginConfig {
  readonly issuer: string;
  readonly clientId: string;
  readonly clientSecret: string;
  readonly redirectUri: string;
  /** `http` 발급자를 받을지. `deny` 는 후보의 기본 동작 그대로 둔다. */
  readonly insecure: "allow" | "deny";
  /** ID 토큰 서명을 어떻게 볼지. 후보마다 받는 값이 다르고 모르는 값은 던진다. */
  readonly signature: string;
  /** HTTP 를 무엇으로 내는지. `default` 는 후보의 기본, `node-http` 는 `node:http`·`node:https` 의 `request` 다. */
  readonly transport: "default" | "node-http";
}

export interface Begun {
  readonly authorizationUrl: string;
  readonly pending: Pending;
}

export interface OidcClient {
  begin(config: LoginConfig): Promise<Begun>;
  /** 돌아온 요청을 검증하고 인가 코드를 토큰으로 바꿔 ID 토큰의 `sub` 를 낸다. 어긋나면 던진다. */
  finish(config: LoginConfig, callbackUrl: string, pending: Pending): Promise<string>;
}
