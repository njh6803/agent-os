// 빌드가 번들에 넣은 두 값(web-widget 티켓 04, next.config.ts 의 env). Next 는 `process.env.이름` 의 자리를 빌드 때
// 글자로 바꿔 넣으므로 점으로 읽고, `process.env` 를 다른 이름에 담거나 구조 분해하지 않는다. 이름은
// tools/site-file.ts 의 WIDGET_ORIGINS_ENV·WIDGET_REQUEST_CHARS_ENV 와 같다(build.test.ts 가 맞댄다). 페이지 시험은
// 빌드를 거치지 않아 testing/setup.ts 가 같은 이름의 환경 변수를 둔다.

/** 모든 사이트의 허용 출처를 합친 목록. 비면 postMessage 를 모두 버린다(ADR 0024 의 fail-closed). */
export function allowedOrigins(): readonly string[] {
  const joined = process.env.AGENT_OS_WIDGET_ORIGINS ?? "";
  return joined === "" ? [] : joined.split(" ");
}

/** 모든 사이트의 요청 글자 수 상한 가운데 가장 작은 값. 세는 단위는 코드 포인트다. */
export function requestCharLimit(): number {
  return Number(process.env.AGENT_OS_WIDGET_REQUEST_CHARS);
}
