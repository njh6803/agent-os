"use client";

// 설정 화면(admin-style 티켓 04, 09, admin-login 티켓 09). 테마를 고른다. 다른 화면처럼 로그인한 뒤에 열린다. 본문은
// `organisms/Settings` 이고 여기는 지금 테마(`stores/theme`)를 읽어 넘긴다.

import { chooseTheme, useTheme } from "../../stores/theme";
import { Settings } from "../organisms/Settings";
import { AdminScreen } from "./AdminScreen";

export function SettingsPage() {
  return (
    <AdminScreen current="settings">
      <ConnectedSettings />
    </AdminScreen>
  );
}

/** 로그인한 계정을 읽은 뒤에만 선다. */
function ConnectedSettings() {
  const theme = useTheme();
  return <Settings theme={theme} onChooseTheme={chooseTheme} />;
}
