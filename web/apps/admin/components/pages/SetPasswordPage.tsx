"use client";

// 링크로 비밀번호 정하기 화면(admin-login 명세 "비밀번호 링크"의 `/set-password#<토큰>`). 로그인 없이 열리는 화면이라 `AdminScreen` 을
// 지나지 않고, 글꼴과 앱의 CSS, 테마 지키기를 여기서 직접 한다(`LoginPage` 와 같은 까닭). 요청 함수 아래의 갱신 규칙도 이 경로를
// 지나지 않는다(`api/session` 의 `OUTSIDE_RULE`).
//
// 주소의 `#` 뒤가 토큰이다. 화면은 그것을 읽은 즉시 방문 기록의 주소를 바꿔 주소창에서 지운다. 화면 공유나 방문 기록에 토큰이
// 남지 않게 하려는 것이다. 토큰은 화면이 선 첫 순간에 한 번 읽어 상태로 쥐고(`useState`), 주소가 바뀌어도 잃지 않는다. 토큰으로
// 서버에서 읽어 오는 것은 없고 계정 이름도 보이지 않는다.

import "@agent-os/ui/fonts.css";
import "../../styles/admin.css";
import { useEffect, useState } from "react";
import { useSetPassword } from "../../hooks/queries/session";
import { useCurrentUrl } from "../../hooks/useCurrentUrl";
import { useForgetOldTokens } from "../../hooks/useForgetOldTokens";
import { useStoredTheme } from "../../stores/theme";
import { SetPasswordForm } from "../organisms/SetPasswordForm";
import { EntryFrame } from "../templates/EntryFrame";

/** 주소의 `#` 뒤. 없거나 비었으면 null 이다. */
function tokenOf(hash: string): string | null {
  const token = hash.startsWith("#") ? hash.slice(1) : hash;
  return token === "" ? null : token;
}

function SetPasswordScreen() {
  const [token] = useState(() => tokenOf(location.hash));
  const attempt = useSetPassword(token);

  useEffect(() => {
    // 방문 기록의 항목은 그대로 두고 주소만 바꾼다. 질의는 남기고 `#` 뒤만 지운다.
    history.replaceState(history.state, "", `${location.pathname}${location.search}`);
  }, []);

  return (
    <EntryFrame>
      <SetPasswordForm state={attempt} onSubmit={attempt.submit} />
    </EntryFrame>
  );
}

export function SetPasswordPage() {
  useStoredTheme();
  useForgetOldTokens();
  const url = useCurrentUrl();
  if (url === null) {
    return <EntryFrame>{null}</EntryFrame>;
  }
  return <SetPasswordScreen />;
}
