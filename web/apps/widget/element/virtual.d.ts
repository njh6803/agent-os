// 페이지 안 번들의 빌드가 내는 가상 모듈(tools/element.ts 의 fontsModule). 글꼴 CSS 의 @font-face 마다 하나이고, 모양은
// `@agent-os/ui/fonts` 의 FontFaceSource 다. 앰비언트 모듈 선언 안에서는 import 문을 쓸 수 없어 타입 import 로 읽는다.
declare module "virtual:agent-os-widget/fonts" {
  export const FONT_FACES: readonly import("@agent-os/ui/fonts").FontFaceSource[];
}
