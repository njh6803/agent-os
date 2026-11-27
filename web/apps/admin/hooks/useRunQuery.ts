import { useSyncExternalStore } from "react";

/** 질의가 바뀌었음을 같은 탭의 구독자에게 알리는 이벤트. `replaceState` 는 `popstate` 를 내지 않는다. */
const CHANGED = "agent-os:run-query";

const QUERY = "run";

function subscribe(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  window.addEventListener(CHANGED, onChange);
  return () => {
    window.removeEventListener("popstate", onChange);
    window.removeEventListener(CHANGED, onChange);
  };
}

function read(): string | null {
  return new URLSearchParams(location.search).get(QUERY);
}

/** 서버가 그린 그림과 hydration 의 첫 그림에서는 패널이 닫혀 있다. 서버는 주소의 질의를 모른다. */
function readOnServer(): null {
  return null;
}

/**
 * 주소의 `?run=<실행>` 질의. 대화 화면이 실행 패널을 열고 닫는 상태다. 패널의 여닫기는 방문 기록을 늘리지 않는다
 * (`replaceState`). 뒤로 가기가 패널이 열리기 전의 화면이 아니라 대화 목록으로 가게 하려는 것이다. 다른 질의와 조각은
 * 그대로 둔다. 서버가 그린 그림과 hydration 의 첫 그림은 늘 닫힘이고, 그 뒤 브라우저의 주소를 읽는다(`useCurrentUrl` 과 같은
 * 까닭이다).
 */
export function useRunQuery(): readonly [string | null, (run: string | null) => void] {
  const run = useSyncExternalStore(subscribe, read, readOnServer);
  return [run, setRunQuery];
}

function setRunQuery(run: string | null): void {
  const url = new URL(location.href);
  if (run === null) {
    url.searchParams.delete(QUERY);
  } else {
    url.searchParams.set(QUERY, run);
  }
  history.replaceState(history.state, "", url);
  window.dispatchEvent(new Event(CHANGED));
}
