"use client";

// 관리 화면의 첫 화면, 곧 플러그인 목록이다(web-admin 티켓 05). 로그인하지 않았으면 `AdminScreen` 이 로그인 화면으로 보낸다.
// 목록의 행은 접속 확인도 보인다(connection-check 티켓 04).

import { refreshConnections } from "../../hooks/queries/connection";
import { usePlugins, useSetPluginEnabled } from "../../hooks/queries/plugins";
import { PluginList } from "../organisms/PluginList";
import { AdminScreen } from "./AdminScreen";
import { readOf } from "./read";
import { RowConnection } from "./RowConnection";

export function HomePage() {
  return (
    <AdminScreen current="plugins">
      <ConnectedPluginList />
    </AdminScreen>
  );
}

/**
 * 플러그인 목록을 읽어 그린다. 로그인한 계정을 읽은 뒤에만 서므로 읽기도 그때 시작한다. 새로 고침 버튼은 목록과 함께
 * 스스로 하는 접속 확인도 바로 한 번 다시 한다.
 */
function ConnectedPluginList() {
  const plugins = usePlugins();
  const setEnabled = useSetPluginEnabled();
  const read = readOf(plugins);
  return (
    <PluginList
      {...read}
      onRefresh={() => {
        read.onRefresh();
        refreshConnections();
      }}
      onSetEnabled={setEnabled}
      connection={(row) => <RowConnection row={row} />}
    />
  );
}
