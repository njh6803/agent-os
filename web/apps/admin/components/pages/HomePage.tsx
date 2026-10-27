"use client";

// 관리 화면의 첫 화면. 관리 토큰이 없으면 넣는 자리이고, 있으면 플러그인 목록이다(web-admin 티켓 05).

import { usePlugins, useSetPluginEnabled } from "../../hooks/queries/plugins";
import { PluginList } from "../organisms/PluginList";
import { AdminScreen } from "./AdminScreen";
import { readOf } from "./read";

export function HomePage() {
  return (
    <AdminScreen>
      <ConnectedPluginList />
    </AdminScreen>
  );
}

/** 플러그인 목록을 읽어 그린다. 관리 토큰이 받아들여진 뒤에만 서므로 읽기도 그때 시작한다. */
function ConnectedPluginList() {
  const plugins = usePlugins();
  const setEnabled = useSetPluginEnabled();
  return <PluginList {...readOf(plugins)} onSetEnabled={setEnabled} />;
}
