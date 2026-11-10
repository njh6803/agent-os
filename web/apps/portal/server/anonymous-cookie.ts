// 익명 식별자 쿠키(pilot-portal 명세 "익명 식별자 쿠키"). 이름은 사이트와 상관없이 `portal_anon` 하나이고 경로가 사이트마다
// 쿠키를 가른다. 값이 소문자 UUID v4 가 아니면 없는 것으로 본다. 서명은 두지 않는다(ADR 0050 Consequences). `__Host-`·
// `__Secure-` 접두는 쓰지 않는다.

import { COOKIE_LIFETIME_DAYS } from "./cookie-policy.ts";
import type { Cookie } from "./cookies.ts";

export const ANONYMOUS_COOKIE = "portal_anon";

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/u;
const SECONDS_PER_DAY = 86_400;

/**
 * 요청의 쿠키에서 익명 식별자를 읽는다. 같은 이름이 둘 이상 실리면 첫 것을 쓰고, 그 값의 꼴이 틀리면 뒤의 것으로 넘어가지
 * 않고 없는 것으로 본다.
 */
export function anonymousIdOf(cookies: readonly Cookie[]): string | undefined {
  const first = cookies.find((cookie) => cookie.name === ANONYMOUS_COOKIE);
  return first !== undefined && UUID_V4.test(first.value) ? first.value : undefined;
}

export interface CookieSpec {
  readonly id: string;
  readonly siteName: string;
  /** 설정의 `public_origin`. `Secure` 를 붙일지는 이 값의 스킴이 정한다. */
  readonly publicOrigin: string;
}

/** 식별자를 그 사이트 경로에 30일 동안 두는 `Set-Cookie` 값. `Secure` 는 공개 출처가 https 일 때만 붙는다. */
export function anonymousCookie({ id, siteName, publicOrigin }: CookieSpec): string {
  return [
    `${ANONYMOUS_COOKIE}=${id}`,
    "HttpOnly",
    "SameSite=Strict",
    `Path=/portal/sites/${siteName}`,
    `Max-Age=${String(COOKIE_LIFETIME_DAYS * SECONDS_PER_DAY)}`,
    ...(publicOrigin.startsWith("https://") ? ["Secure"] : []),
  ].join("; ");
}
