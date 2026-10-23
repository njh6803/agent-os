// 위젯 창. 위쪽 띠, 대화 자리, 입력 자리를 위에서 아래로 쌓고 자기 자리(iframe 의 크기)를 채운다. 슬롯만 받는다.
// 창이 컨테이너다. 안쪽 부품이 폭으로 모양을 가를 때는 `@wide:`(360px)를 쓴다(web-widget 명세 "테마·모드·밀도·글꼴").
// 첫 화면의 부품은 아직 폭으로 가르지 않는다.
import type { ReactNode } from "react";

export interface WidgetFrameProps {
  readonly topBar: ReactNode;
  /** 남는 높이를 채우고, 넘치면 이 자리 안에서 스크롤한다. */
  readonly conversation: ReactNode;
  readonly composer: ReactNode;
}

export function WidgetFrame({ topBar, conversation, composer }: WidgetFrameProps) {
  return (
    <div className="@container flex h-full flex-col overflow-hidden rounded-l border border-border bg-bg-raised text-text shadow-float">
      {topBar}
      <main className="flex min-h-0 flex-1 flex-col overflow-y-auto">{conversation}</main>
      {composer}
    </div>
  );
}
