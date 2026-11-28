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

/**
 * 방문 기록을 늘리지 않고 주소만 `path` 로 바꾼다(`replaceState`). 새 대화나 이어 가기의 시작 이벤트가 오면 주소가 그 실행의
 * 대화(`/chat/<실행>`)가 된다. 뒤로 가기가 빈 새 대화가 아니라 대화 목록으로 가게 하려는 것이다. 질의는 비워지므로 열린
 * 패널은 닫힌다. 상태를 null 로 넘겨야 라우터가 바뀐 주소를 알아 `usePathname` 이 따라온다(라우터의 상태가 든 `history.state`
 * 를 그대로 넘기면 라우터는 자기 것이라 보고 건너뛴다). 화면은 그대로 두고 주소만 따라온다.
 */
export function replaceAddress(path: string): void {
  history.replaceState(null, "", path);
  window.dispatchEvent(new Event(CHANGED));
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
