// 관리 화면의 한 화면이 서는 자리. 관리 토큰이 없으면 넣는 자리이고, 있으면 틀(탐색)과 그 화면의 내용이다. 화면마다 이
// 문을 지난다. 관리 요청은 모두 관리 토큰을 싣기 때문이다(web-admin 스토리 1). 채널 토큰을 넣는 자리와 두 토큰을 지우는
// 버튼은 설정 화면에 있다(admin-style 티켓 04). 화면 부품 가운데 토큰 스토어를 읽는 것은 pages(여기, 설정 화면, 실행
// 화면)이고, 넣는 자리들은 그 값과 처리기를 props 로 받는다.
//
// 관리 화면의 페이지(app/ 의 page.tsx)가 모두 지나므로 글꼴 CSS 와 앱의 전역 CSS(디자인 토큰 CSS 를 들인 것)를 여기서 싣는다(admin-style 명세
// "디자인 시스템 들이기"). 문서 뿌리에 모드와 밀도를 달지 않아, 모드는 시스템을 따르고 밀도는 폭을 따른다.
//
// 같은 까닭으로 테마도 여기서 지킨다(admin-style 티켓 09). 마운트될 때 하이드레이션이 지운 테마를 저장 값으로 되살리고,
// 마운트된 동안 다른 탭이 바꾼 테마를 따른다. 관리 토큰을 넣기 전의 화면도 그렇다.

import "@agent-os/ui/fonts.css";
import "../../styles/admin.css";
import type { ReactNode } from "react";
import { useAdminTokenEntry } from "../../hooks/queries/plugins";
import { useHydrated } from "../../hooks/useHydrated";
import { useStoredTheme } from "../../stores/theme";
import { useTokens } from "../../stores/tokens";
import { AdminNav, type Section } from "../organisms/AdminNav";
import { AdminTokenForm } from "../organisms/AdminTokenForm";
import { AdminFrame } from "../templates/AdminFrame";
import { EntryFrame } from "../templates/EntryFrame";

interface AdminScreenProps {
  /** 지금 화면이 든 탐색 항목. */
  readonly current: Section;
  readonly children: ReactNode;
}

export function AdminScreen({ current, children }: AdminScreenProps) {
  useStoredTheme();
  const hydrated = useHydrated();
  const adminToken = useTokens((state) => state.adminToken);
  const adminTokenNotice = useTokens((state) => state.adminTokenNotice);
  const enterAdminToken = useAdminTokenEntry();
  const channelToken = useTokens((state) => state.channelToken);
  const clearTokens = useTokens((state) => state.clearTokens);
  const nav = <AdminNav current={current} />;

  if (!hydrated) {
    // 이 탭에 관리 토큰이 있는지 아직 모르는 동안은 틀만 서고 본문은 비운다(admin-style 명세 2026-10-27 주석).
    return <AdminFrame nav={nav} />;
  }
  if (adminToken === null) {
    // 관리 토큰이 거부돼도 채널 토큰은 남는다. 관리 토큰이 없으면 설정 화면에 닿지 못하므로, 탭을 닫지 않고 지울 길을
    // 여기 둔다(스토리 8). 틀(탐색)은 서지 않는다.
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
  return <AdminFrame nav={nav}>{children}</AdminFrame>;
}
