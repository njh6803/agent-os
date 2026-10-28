// 관리 토큰을 넣기 전의 틀. 옆 탐색도 위 막대도 없이 "Agent OS"(제목 요소가 아닌 글자)와 그 아래 한 칸이 최대 폭
// `form` 으로 가운데에 선다(그림 mk-token, mk-token-m). 슬롯만 받는다.
//
// 그림은 위 여백을 넓은 폭 96px, 좁은 폭 48px 로 그렸지만 간격 토큰은 32px(`8`)까지라 두 폭 모두 그것으로 둔다(어림).
// 인라인 px 는 옮기지 않는다(admin-style 명세 "기준 폭 `form`과 `content`").
import type { ReactNode } from "react";

export function EntryFrame({ children }: { readonly children: ReactNode }) {
  return (
    <div className="flex justify-center px-4 py-8">
      <main className="flex w-full max-w-form flex-col gap-6">
        <div className="text-body font-semibold">Agent OS</div>
        {children}
      </main>
    </div>
  );
}
