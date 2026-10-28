// 관리 화면의 한 화면이 서는 자리. 관리 토큰이 없으면 넣는 자리이고, 있으면 그 화면의 내용과 화면 사이를 오가는
// 링크다. 화면마다 이 문을 지난다. 관리 요청은 모두 관리 토큰을 싣기 때문이다(web-admin 스토리 1). 머리에는 선택인
// 채널 토큰을 넣는 자리와, 두 토큰을 모두 지우는 버튼이 선다(스토리 4, 8). 토큰 스토어를 읽는 것은 여기이고, 넣는
// 자리들은 그 값과 처리기를 props 로 받는다.
//
// 관리 화면의 페이지(app/ 의 page.tsx 넷)가 모두 지나므로 글꼴 CSS 와 앱의 전역 CSS(디자인 토큰 CSS 를 들인 것)를 여기서 싣는다(admin-style 명세
// "디자인 시스템 들이기"). 문서 뿌리에 모드와 밀도를 달지 않아, 모드는 시스템을 따르고 밀도는 폭을 따른다.

import "@agent-os/ui/fonts.css";
import "../../styles/admin.css";
import Link from "next/link";
import type { ReactNode } from "react";
import { useAdminTokenEntry } from "../../hooks/queries/plugins";
import { useHydrated } from "../../hooks/useHydrated";
import { useTokens } from "../../stores/tokens";
import { AdminTokenForm } from "../organisms/AdminTokenForm";
import { ChannelTokenForm } from "../organisms/ChannelTokenForm";
import { AdminFrame } from "../templates/AdminFrame";
import { EntryFrame } from "../templates/EntryFrame";

export function AdminScreen({ children }: { readonly children: ReactNode }) {
  const hydrated = useHydrated();
  const adminToken = useTokens((state) => state.adminToken);
  const adminTokenNotice = useTokens((state) => state.adminTokenNotice);
  const enterAdminToken = useAdminTokenEntry();
  const channelToken = useTokens((state) => state.channelToken);
  const acceptChannelToken = useTokens((state) => state.acceptChannelToken);
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
    // 관리 토큰이 거부돼도 채널 토큰은 남는다. 탭을 닫지 않고 지울 길을 둔다(스토리 8). 틀(탐색)은 서지 않는다.
    return (
      <EntryFrame>
        <AdminTokenForm
          notice={adminTokenNotice}
          onEnter={enterAdminToken}
          onClearTokens={channelToken === null ? null : clearTokens}
        />
      </EntryFrame>
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
          <ChannelTokenForm entered={channelToken !== null} onEnter={acceptChannelToken} />
          {clearButton}
        </>
      }
    >
      {children}
    </AdminFrame>
  );
}
