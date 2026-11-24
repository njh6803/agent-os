"use client";

// 관리 화면의 첫 화면. 관리 토큰이 없으면 넣는 자리이고, 있으면 플러그인 목록이다(web-admin 티켓 05). 목록의 행은 접속
// 확인도 보인다(connection-check 티켓 04).

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
 * 플러그인 목록을 읽어 그린다. 관리 토큰이 받아들여진 뒤에만 서므로 읽기도 그때 시작한다. 새로 고침 버튼은 목록과 함께
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
