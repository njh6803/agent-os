import { useMemo, useSyncExternalStore } from "react";

const subscribe = (): (() => void) => () => undefined;

/**
 * 지금 화면의 주소. 서버가 그린 그림과 hydration 의 첫 그림에서는 null 이다.
 *
 * 로그인 화면은 주소의 질의(`next`, `notice`)와 출처(`https` 인지)로 갈린다. 서버는 그 주소를 모르고, Next 의
 * `useSearchParams` 는 정적으로 미리 그리는 페이지를 경계(`Suspense`)로 갈라 다른 값을 주는 길이 하나 더 생긴다. 브라우저의
 * 주소를 직접 읽으면 갈래가 하나다. 주소는 이 화면이 떠 있는 동안 바뀌지 않는다(화면 이동은 전체를 새로 불러온다).
 */
export function useCurrentUrl(): URL | null {
  const href = useSyncExternalStore(
    subscribe,
    () => location.href,
    () => null,
  );
  return useMemo(() => (href === null ? null : new URL(href)), [href]);
}
