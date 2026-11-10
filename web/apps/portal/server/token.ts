// 사이트 토큰(pilot-portal 명세 "토큰", ADR 0023). RS256 JWT 이고 클레임은 서버가 요구하는 다섯(`iss`, `sub`, `aud`, `iat`,
// `exp`)이다. `nbf` 는 넣지 않는다. 키 하나로 모든 사이트에 서명한다. 선례는 위젯 e2e 의 `token.ts` 이고, 서버는 앱 사이
// import 를 하지 않아 같은 일을 여기서 따로 한다.

import { createHash, type KeyObject, sign } from "node:crypto";

/** 서버의 상한 600초 안에서 정한 수명. 페이지가 질문마다 새로 받아 간다. */
export const TOKEN_LIFETIME_SECONDS = 120;

export interface TokenInput {
  readonly privateKey: KeyObject;
  readonly kid: string;
  readonly issuer: string;
  readonly audience: string;
  readonly subject: string;
  /** 발급 시각. 에포크 초다. */
  readonly nowSeconds: number;
}

/**
 * 익명 주체의 이름. 쿠키 값 글자 36자의 SHA-256 을 소문자 16진으로 쓴 앞 32자에 `anon-` 을 붙인다. 소금은 없다. 같은
 * 쿠키가 같은 주체로 이어져야 해서다. 쿠키 값 원문이 트레이스에 남지 않게 하는 길이다(ADR 0050).
 */
export function anonymousSubject(cookieValue: string): string {
  return `anon-${createHash("sha256").update(cookieValue, "utf8").digest("hex").slice(0, 32)}`;
}

function encode(value: object): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

export function signSiteToken(input: TokenInput): string {
  const head = encode({ alg: "RS256", typ: "JWT", kid: input.kid });
  const body = encode({
    iss: input.issuer,
    sub: input.subject,
    aud: input.audience,
    iat: input.nowSeconds,
    exp: input.nowSeconds + TOKEN_LIFETIME_SECONDS,
  });
  const signature = sign("RSA-SHA256", Buffer.from(`${head}.${body}`), input.privateKey);
  return `${head}.${body}.${signature.toString("base64url")}`;
}
