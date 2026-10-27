// 페이지 안 방식의 토큰 손잡이(web-widget 명세 "임베드"의 페이지 안 방식). 사이트는 요소의 속성 `tokenProvider` 에
// `() => Promise<string>` 을 주고, 위젯은 요청을 보낼 때마다 그것을 부른다.
//
// - 함수가 없거나, 던지거나, 거부하거나, 문자열이 아닌 값을 주거나, 10초 안에 답하지 않으면 받지 못한 것(null)이다.
//   위젯은 요청을 보내지 않고 401 과 같은 화면을 보인다(명세 "토큰을 받지 못한 경우"). iframe 방식과 같은 10초다.
// - 사이트는 JS 라 무엇이든 줄 수 있어 값은 unknown 으로 받는다. 약속이 아니라 문자열을 곧바로 돌려줘도 문자열이라
//   받는다.

import { TOKEN_TIMEOUT_MS, type TokenResult } from "../lib/token";

function isProvider(value: unknown): value is () => unknown {
  return typeof value === "function";
}

export function providerToken(provider: unknown): Promise<TokenResult> {
  if (!isProvider(provider)) {
    return Promise.resolve(null);
  }
  let answer: unknown;
  try {
    answer = provider();
  } catch {
    return Promise.resolve(null);
  }
  return new Promise<TokenResult>((resolve) => {
    const timer = setTimeout(() => {
      resolve(null);
    }, TOKEN_TIMEOUT_MS);
    Promise.resolve(answer).then(
      (token: unknown) => {
        clearTimeout(timer);
        resolve(typeof token === "string" ? token : null);
      },
      () => {
        clearTimeout(timer);
        resolve(null);
      },
    );
  });
}
