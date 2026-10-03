// lucide-react 1.51.0 에는 `exports` 맵이 없고 아이콘 하나의 모듈(`dist/esm/icons/<이름>.mjs`)에는 타입 선언이 없다.
// 패키지 루트의 선언이 아이콘마다 `LucideIcon` 을 내므로 같은 타입을 기본 내보내기로 준다. 루트를 타입으로만 읽는
// `import("lucide-react")` 는 ESLint 의 루트 import 금지에 걸리지 않는다(`import type` 문은 걸린다, cases.mjs).
declare module "lucide-react/dist/esm/icons/*" {
  const icon: import("lucide-react").LucideIcon;
  export default icon;
}
