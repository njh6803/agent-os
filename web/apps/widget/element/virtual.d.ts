// 페이지 안 번들의 빌드가 내는 가상 모듈(tools/element.ts 의 fontsModule). 글꼴 CSS 의 @font-face 마다 하나이고, 모양은
// element/fonts.ts 의 FontFaceSource 와 같다. 번들 입구가 이 값을 registerFonts 에 넘겨 두 모양이 어긋나면 tsc 가 잡는다.
// 앰비언트 모듈 선언 안에서는 상대 경로로 import 하지 못해 모양을 다시 적는다.
declare module "virtual:agent-os-widget/fonts" {
  export const FONT_FACES: readonly {
    readonly family: string;
    readonly weight: string;
    readonly style: string;
    readonly unicodeRange: string;
    readonly file: string;
  }[];
}
