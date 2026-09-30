"use client";

// 관리 화면의 첫 화면. 관리 토큰이 없으면 넣는 자리이고, 있으면 플러그인 목록이다(web-admin 티켓 05).

import { PluginList } from "../organisms/PluginList";
import { AdminScreen } from "./AdminScreen";

export function HomePage() {
  return (
    <AdminScreen>
      <PluginList />
    </AdminScreen>
  );
}
