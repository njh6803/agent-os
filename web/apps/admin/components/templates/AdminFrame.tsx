import type { ReactNode } from "react";

interface AdminFrameProps {
  /** 머리의 동작 자리. 토큰 지우기 같은 것이 선다. */
  readonly actions?: ReactNode;
  readonly children?: ReactNode;
}

/** 관리 화면의 틀. 슬롯만 받는다. 채우는 것은 pages 다. */
export function AdminFrame({ actions, children }: AdminFrameProps) {
  return (
    <>
      <header>
        <h1>관리 화면</h1>
        {actions}
      </header>
      <main>{children}</main>
    </>
  );
}
