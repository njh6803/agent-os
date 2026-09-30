// 관리 화면의 한 화면이 서는 자리. 관리 토큰이 없으면 넣는 자리이고, 있으면 그 화면의 내용과 화면 사이를 오가는
// 링크다. 화면마다 이 문을 지난다. 관리 요청은 모두 관리 토큰을 싣기 때문이다(web-admin 스토리 1). 머리에는 선택인
// 채널 토큰을 넣는 자리와, 두 토큰을 모두 지우는 버튼이 선다(스토리 4, 8).

import Link from "next/link";
import type { ReactNode } from "react";
import { useHydrated } from "../../hooks/useHydrated";
import { useTokens } from "../../stores/tokens";
import { AdminTokenForm } from "../organisms/AdminTokenForm";
import { ChannelTokenForm } from "../organisms/ChannelTokenForm";
import { AdminFrame } from "../templates/AdminFrame";

export function AdminScreen({ children }: { readonly children: ReactNode }) {
  const hydrated = useHydrated();
  const adminToken = useTokens((state) => state.adminToken);
  const channelToken = useTokens((state) => state.channelToken);
  const clearTokens = useTokens((state) => state.clearTokens);
  const clearButton = (
    <button type="button" onClick={clearTokens}>
      토큰 지우기
    </button>
  );

  if (!hydrated) {
    return <AdminFrame />;
  }
  if (adminToken === null) {
    // 관리 토큰이 거부돼도 채널 토큰은 남는다. 탭을 닫지 않고 지울 길을 둔다(스토리 8).
    return (
      <AdminFrame actions={channelToken === null ? undefined : clearButton}>
        <AdminTokenForm />
      </AdminFrame>
    );
  }
  return (
    <AdminFrame
      nav={
        <>
          <Link href="/">플러그인 목록</Link> <Link href="/runs">실행 목록</Link>
        </>
      }
      actions={
        <>
          <ChannelTokenForm />
          {clearButton}
        </>
      }
    >
      {children}
    </AdminFrame>
  );
}
