// Vite 의 `?inline` import 는 빌드한 CSS 를 글자로 준다(shadow 틀과 판정 스토리). TypeScript 에 그 모양을 알린다.
declare module "*.css?inline" {
  const css: string;
  export default css;
}
