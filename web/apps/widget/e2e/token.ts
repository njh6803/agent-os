// 사이트의 서명 키와 토큰(ADR 0023). 키 쌍과 토큰은 `node:crypto` 가 짓는다. 개인 키는 준비(러너 프로세스)의 사이트
// 서버만 들고, 공개 키는 사이트 파일에 실린다. 어느 것도 커밋하지 않는다.
//
// 토큰은 RS256 JWT 이고 클레임은 서버가 요구하는 다섯(`iss`, `sub`, `aud`, `exp`, `iat`)이다. 수명은 서버의 상한
// 600초 안의 300초다(`src/agent_os/http/sites.py`).

import { generateKeyPairSync, type KeyObject, randomUUID, sign } from "node:crypto";

export const ISSUER = "https://site.e2e.example";
export const AUDIENCE = "agent-os";
export const KEY_ID = "e2e-1";
const LIFETIME_SECONDS = 300;

export interface SiteKey {
  readonly privateKey: KeyObject;
  /** 사이트 파일의 `pem` 에 싣는 SPKI PEM. */
  readonly publicPem: string;
}

export function siteKey(): SiteKey {
  const { privateKey, publicKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
  return {
    privateKey,
    publicPem: publicKey.export({ type: "spki", format: "pem" }).toString(),
  };
}

function encode(value: object): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

/** 그 키로 서명한 토큰. `sub` 를 주지 않으면 토큰마다 새 주체라 주체별 시간당 상한에 걸리지 않는다. */
export function signToken(key: SiteKey, sub: string = randomUUID()): string {
  const now = Math.floor(Date.now() / 1000);
  const head = encode({ alg: "RS256", typ: "JWT", kid: KEY_ID });
  const body = encode({
    iss: ISSUER,
    sub,
    aud: AUDIENCE,
    iat: now,
    exp: now + LIFETIME_SECONDS,
  });
  const signature = sign("RSA-SHA256", Buffer.from(`${head}.${body}`), key.privateKey);
  return `${head}.${body}.${signature.toString("base64url")}`;
}
