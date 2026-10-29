import { type ReactNode, useEffect, useState } from "react";

/** 처음 불러오는 중의 표시가 서기까지 기다리는 시간. 그보다 빨리 오면 아무것도 깜빡이지 않는다. */
const LOADING_DELAY_MS = 300;

/**
 * 마운트되고 `LOADING_DELAY_MS` 가 지난 뒤에야 `children` 을 그린다. 처음 불러오는 중의 표시는 0.3초를 넘길 때만
 * 보인다(`.claude/rules/web-design.md` 의 뼈대 줄, admin-style 명세 "화면 머리와 공통 상태"). 불러오기가 끝나 걷히면
 * 다음에 다시 설 때 처음부터 기다린다.
 */
export function AfterDelay({ children }: { readonly children: ReactNode }) {
  const [elapsed, setElapsed] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => {
      setElapsed(true);
    }, LOADING_DELAY_MS);
    return () => {
      clearTimeout(timer);
    };
  }, []);
  return elapsed ? children : null;
}
