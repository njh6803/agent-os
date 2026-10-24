// 페이지 안 방식의 API 기준 주소(web-widget 명세 "API의 기준 주소"). 번들 스크립트의 출처이고, 최종 사용자 경로는 그
// 아래 `/end-user` 다(계약의 경로 키가 이미 든다).
//
// 번들 입구(index.ts)가 최상위를 실행하는 동안의 `document.currentScript` 를 넘긴다. 그 값은 classic 스크립트가 최상위를
// 실행하는 동안에만 있다. 인스턴스인지 먼저 보는 것은 DOM clobbering 때문이다. `document` 의 이름 있는 속성이 내장
// 속성을 가려, 사이트 페이지의 `<img name="currentScript" src="https://<다른 출처>/">` 가 그 자리에 선다. 그 `src` 를
// 기준 주소로 쓰면 요청마다 서명 토큰이 그 출처로 간다. 그래서 `getAttribute("src")` 나 `"src" in` 으로 좁히지 않는다.
// 인스턴스가 아니면(없음, 다른 요소, 컬렉션) 기준 주소가 없고, 위젯은 요청도 토큰 함수도 부르지 않는다.
//
// `src` 는 속성(property)이라 문서 기준으로 푼 절대 주소다. 비었거나(인라인 스크립트) 출처가 불투명하면(`data:`) 기준
// 주소가 없다.

export function scriptBaseUrl(current: unknown): URL | null {
  if (!(current instanceof HTMLScriptElement)) {
    return null;
  }
  try {
    return new URL(new URL(current.src).origin);
  } catch {
    return null;
  }
}
