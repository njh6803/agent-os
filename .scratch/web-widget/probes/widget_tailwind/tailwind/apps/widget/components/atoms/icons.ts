// 위젯이 쓰는 아이콘. lucide-react 는 아이콘 하나의 서브패스로 import 한다(ADR 0021, 루트 import 는 ESLint 가 막는다).
// 경로는 배포 폴더의 ESM 파일이다(`exports` 맵이 없다). 타입은 lucide-icons.d.ts 가 준다.

export { default as CloseIcon } from "lucide-react/dist/esm/icons/x";
export { default as SendIcon } from "lucide-react/dist/esm/icons/send";
