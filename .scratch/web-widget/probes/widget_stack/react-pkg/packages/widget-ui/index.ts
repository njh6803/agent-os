// 위젯의 공유 컴포넌트 패키지(측정의 모양 B). iframe 의 Next 페이지와 커스텀 요소 번들이 이것을 같이 쓴다.
// api/, lib/, components/organisms/ 는 setup.mjs 가 react/ 의 위젯 앱에서 옮겨 온다.

export type { RunTarget } from "./api/runs";
export { ChatWidget } from "./components/organisms/ChatWidget";
export { STYLES } from "./lib/styles";
export { targetFromElement, targetFromLocation } from "./lib/target";
