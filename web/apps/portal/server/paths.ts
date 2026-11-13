// 위젯 미리보기 페이지가 내는 경로의 모양을 한 곳에 모은다(pilot-portal 명세 "경로와 끝점"). 처리기가 길을 가르는 데, 쿠키가 경로를
// 사이트마다 가르는 데, 페이지 HTML 이 정적 파일을 가리키는 데 같은 글자를 쓴다. 페이지 스크립트(`browser/portal.ts`)는
// 번들 없이 브라우저가 읽는 고전 스크립트라 이 모듈을 import 하지 못하고 사이트 끝점의 모양을 제 안에 적는다. 둘이 어긋나면
// 위젯 미리보기 페이지 e2e(`e2e/acknowledge.e2e.ts`)가 빨개진다(상태·확인·토큰 끝점을 실제로 부르는 사례다. 토큰 끝점이 어긋나면
// 질문에 답이 서지 않는다). 그 경로를 바꿀 때는 `browser/portal.ts` 도 같이 고친다.

export const ROOT = "/";
export const PAGE = "/portal/";
export const HEALTH = "/portal/health";
export const SITES_PREFIX = "/portal/sites/";
export const FONTS_PREFIX = "/portal/fonts/";

/** 메모리의 글로 내는 정적 파일 넷. 페이지가 링크로 든다. */
export const PAGE_SCRIPT = "/portal/portal.js";
export const PAGE_CSS = "/portal/portal.css";
export const THEME_CSS = "/portal/theme.css";
export const FONTS_CSS = "/portal/fonts.css";

/** 위젯 번들. 운영의 프록시가 같은 출처에서 낸다(위젯 앱의 `/widget/` 아래). */
export const WIDGET_BUNDLE = "/widget/element.js";

/** `/portal/sites/<이름>/<끝점>`. 이름은 첫 묶음, 끝점은 둘째 묶음이다. */
export const SITE_ENDPOINT = /^\/portal\/sites\/([^/]+)\/(acknowledgement|token)$/u;

/** 그 사이트의 쿠키가 걸리는 경로. 사이트마다 달라 같은 쿠키 이름으로도 사이트마다 다른 쿠키가 선다. */
export function siteCookiePath(siteName: string): string {
  return `${SITES_PREFIX}${siteName}`;
}

/** 글꼴 파일의 주소. `fontsCss` 의 `url()` 과 처리기의 길이 같은 모양을 쓴다. */
export function fontPath(file: string): string {
  return `${FONTS_PREFIX}${file}`;
}
