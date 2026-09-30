"use client";

// 관리 화면의 첫 화면. 관리 토큰이 없으면 넣는 자리이고, 있으면 플러그인 목록이다(web-admin 티켓 05).

import { useHydrated } from "../../hooks/useHydrated";
import { useTokens } from "../../stores/tokens";
import { AdminTokenForm } from "../organisms/AdminTokenForm";
import { PluginList } from "../organisms/PluginList";
import { AdminFrame } from "../templates/AdminFrame";

export function HomePage() {
  const hydrated = useHydrated();
  const adminToken = useTokens((state) => state.adminToken);
  const clearTokens = useTokens((state) => state.clearTokens);

  if (!hydrated) {
    return <AdminFrame />;
  }
  if (adminToken === null) {
    return (
      <AdminFrame>
        <AdminTokenForm />
      </AdminFrame>
    );
  }
  return (
    <AdminFrame
      actions={
        <button type="button" onClick={clearTokens}>
          토큰 지우기
        </button>
      }
    >
      <PluginList />
    </AdminFrame>
  );
}
