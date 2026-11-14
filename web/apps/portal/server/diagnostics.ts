// 시작할 때 사람이 읽는 두 글. 구성 오류(stderr)와 시작 로그(stdout)다. 어느 쪽에도 쿠키 값과 토큰, 키와 파일의 내용을
// 싣지 않는다(ADR 0050 결정 "기록").

/** 구성 오류. 첫 줄 뒤에 어긋난 자리마다 `<자리>: <까닭>` 한 줄이다. */
export function configErrorText(problems: readonly string[]): string {
  return ["구성 오류:", ...problems].join("\n");
}

/** 시작 로그 한 줄. IPv6 주소는 대괄호 없이는 URL 의 호스트가 되지 않아 `::1` 은 `[::1]` 로 감싼다. */
export function listenLine(host: string, port: number, siteCount: number): string {
  const authority = host.includes(":") ? `[${host}]` : host;
  return `위젯 미리보기 페이지가 http://${authority}:${String(port)}/portal/ 에 섰다. 사이트 ${String(siteCount)}개.`;
}
