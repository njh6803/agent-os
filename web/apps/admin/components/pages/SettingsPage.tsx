"use client";

// 설정 화면(admin-style 티켓 04). 채널 토큰을 넣고 이 탭의 두 토큰을 지운다. 다른 화면처럼 관리 토큰을 넣은 뒤에
// 열린다. 본문은 `organisms/Settings` 이고 여기는 토큰 스토어를 읽어 넘긴다.

import { useTokens } from "../../stores/tokens";
import { Settings } from "../organisms/Settings";
import { AdminScreen } from "./AdminScreen";

export function SettingsPage() {
  return (
    <AdminScreen current="settings">
      <TokenSettings />
    </AdminScreen>
  );
}

/** 관리 토큰이 받아들여진 뒤에만 선다. */
function TokenSettings() {
  const channelToken = useTokens((state) => state.channelToken);
  const acceptChannelToken = useTokens((state) => state.acceptChannelToken);
  const clearTokens = useTokens((state) => state.clearTokens);
  return (
    <Settings
      channelTokenEntered={channelToken !== null}
      onEnterChannelToken={acceptChannelToken}
      onClearTokens={clearTokens}
    />
  );
}
