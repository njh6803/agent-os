import { useSyncExternalStore } from "react";

const subscribe = (): (() => void) => () => undefined;

/**
 * 브라우저가 그리는 중인가. 서버가 그린 그림과 hydration 의 첫 그림에서는 거짓이다.
 *
 * Next 는 클라이언트 컴포넌트도 서버에서 한 번 그리고, 이 화면은 정적으로 미리 그려진다. 서버에는 sessionStorage 가
 * 없어 토큰이 늘 없다. 토큰으로 갈리는 화면을 서버에서 그리면 미리 그린 HTML 에 넣는 칸이 박혀, 토큰을 가진 운영자가
 * 새로 고칠 때마다 그 칸이 잠깐 보였다 사라진다. 그래서 거짓인 동안은 어느 쪽도 그리지 않는다.
 *
 * 두 그림의 어긋남(hydration mismatch)을 막는 것은 이것이 아니다. zustand 의 훅이 hydration 에서 서버 스냅숏으로 초기
 * 상태(토큰 없음)를 준다(zustand 5.0.15 의 `useStore`). 이 가드를 빼도 어긋나지 않았다(티켓 05 의 변이).
 */
export function useHydrated(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => true,
    () => false,
  );
}
