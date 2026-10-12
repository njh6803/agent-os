// Vite 의 `?inline` import 는 빌드한 CSS 를 글자로 준다(shadow 틀과 판정 스토리). `?raw` 는 빌드하지 않은 소스를 준다
// (판정 스토리가 `@theme` 블록의 토큰 이름을 읽는다). TypeScript 에 그 모양을 알린다.
declare module "*.css?inline" {
  const css: string;
  export default css;
}
declare module "*.css?raw" {
  const source: string;
  export default source;
}
