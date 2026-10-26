// 페이지 안 번들의 글꼴(web-widget 명세 "테마·모드·밀도·글꼴"). Chromium·Firefox 는 shadow root 안의 @font-face 를
// 쓰지 않아(글꼴 CSS `fonts.css` 의 머리 주석) 글꼴을 사이트 문서에 등록한다. 글꼴 파일은 번들에 박지 않고 위젯 출처의
// `/widget/fonts/` 에서 받는다(시작 래퍼가 복사한 자리, tools/fonts.ts). 그 응답에는 Next 가
// `Access-Control-Allow-Origin: *` 를 단다(next.config.ts).
//
// - family 이름은 위젯만 쓰는 고유한 이름이다. 글꼴 CSS 의 이름("Noto Sans KR")으로 등록하면 같은 이름을 쓰는 사이트의
//   글자까지 위젯 출처의 파일로 그려진다. 감싼 요소가 `--sans`·`--mono` 를 이 이름으로 다시 정한다(styles.ts).
// - face 는 빌드가 글꼴 CSS 에서 뽑은 것(굵기, 모양, 글자 범위, 파일)이다. 한글 글꼴은 글자 범위로 나뉜 파일 백여 개라
//   범위를 빠뜨리면 브라우저는 face 하나가 모든 글자를 맡는다고 본다.
// - 사이트의 CSP 가 위젯 출처의 글꼴을 막으면 시스템 글꼴로 그려진다(두 글꼴 변수의 대체 목록, 임베드 안내).
// - FontFace 를 짓고 문서에 더하는 것은 부르는 쪽이 넘긴다. 번들 입구는 브라우저의 것을 넘긴다.

export const WIDGET_SANS = "agent-os-widget-sans";
export const WIDGET_MONO = "agent-os-widget-mono";

/** 글꼴 CSS 의 family 를 위젯만 쓰는 이름으로 옮긴다. 두 글꼴은 디자인 토큰 CSS 의 `--sans`·`--mono` 다. */
const FAMILIES: ReadonlyMap<string, string> = new Map([
  ["Noto Sans KR", WIDGET_SANS],
  ["Noto Sans Mono", WIDGET_MONO],
]);

/** 글꼴 CSS 의 @font-face 하나. 빌드가 뽑는다(tools/fonts.ts 의 fontFaces). */
export interface FontFaceSource {
  readonly family: string;
  readonly weight: string;
  readonly style: string;
  readonly unicodeRange: string;
  /** woff2 의 파일 이름. `/widget/fonts/` 아래에 있다. */
  readonly file: string;
}

/**
 * face 마다 `make` 로 짓고 `add` 로 더한다. `make` 가 앞에 있어야 TypeScript 가 그 반환에서 `Face` 를 추론한다. 문맥으로
 * 타입을 받는 인자는 왼쪽부터 보아, `add` 가 앞이면 `Face` 가 `unknown` 으로 정해진다.
 */
export function registerFonts<Face>(
  faces: readonly FontFaceSource[],
  baseUrl: URL,
  make: (family: string, source: string, descriptors: FontFaceDescriptors) => Face,
  add: (face: Face) => void,
): void {
  for (const face of faces) {
    const family = FAMILIES.get(face.family);
    if (family === undefined) {
      continue;
    }
    const url = new URL(`/widget/fonts/${face.file}`, baseUrl);
    add(
      make(family, `url(${JSON.stringify(url.href)}) format("woff2")`, {
        weight: face.weight,
        style: face.style,
        unicodeRange: face.unicodeRange,
        display: "swap",
      }),
    );
  }
}
