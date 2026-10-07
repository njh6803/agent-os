// lucide-react 의 아이콘 하나짜리 서브패스(ADR 0024). 1.51.0 에도 exports 맵과 아이콘별 타입 선언이 없어 손으로 둔다.
// 이 선언은 경로와 타입의 대응을 TypeScript 가 검증하지 않는다. 아이콘 스토리가 모든 이름을 실제로 그려 본다.
// 앰비언트 선언이라 import 로 끌어올 수 없다. 패키지를 소스로 import 하는 앱의 tsc 에도 실리도록 Icon.tsx 가 경로로
// 참조한다.
declare module "lucide-react/dist/esm/icons/*" {
  const icon: import("lucide-react").LucideIcon;
  export default icon;
}
