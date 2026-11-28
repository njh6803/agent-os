// 시험이 관리 화면의 중계로 계정에 로그인해 `Cookie` 머리의 값을 받는 길. `__Host-` 쿠키는 `Secure` 속성이라 http 주소의
// 브라우저에는 저장되지 않으므로 응답의 `Set-Cookie` 값을 읽어 직접 싣는다. 요청 컨텍스트는 `Sec-Fetch-Site` 도 `Origin` 도
// 달지 않아 요청 출처 검사를 지난다.

import type { APIRequestContext } from "@playwright/test";

/** 로그인해 `Cookie` 머리의 값을 준다. 로그인 응답의 `Set-Cookie` 줄마다 `이름=값` 앞 조각만 모은다. */
export async function loginCookie(
  request: APIRequestContext,
  origin: string,
  name: string,
  password: string,
): Promise<string> {
  const response = await request.post(`${origin}/api/auth/login`, { data: { name, password } });
  if (!response.ok()) {
    throw new Error(`로그인이 실패했다(${String(response.status())})`);
  }
  const pairs = response
    .headersArray()
    .filter((header) => header.name.toLowerCase() === "set-cookie")
    .map((header) => header.value.split(";")[0] ?? "")
    .filter((pair) => pair !== "");
  if (pairs.length === 0) {
    throw new Error("로그인 응답에 Set-Cookie 줄이 없다");
  }
  return pairs.join("; ");
}
