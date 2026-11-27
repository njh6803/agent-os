"use client";

// 로그인 화면(admin-login 명세 "관리 화면의 페이지와 주소"의 `/login`). 로그인 없이 열리는 화면이라 `AdminScreen` 을 지나지 않고,
// 글꼴과 앱의 CSS, 테마 지키기를 여기서 직접 한다(AdminScreen 의 머리 주석과 같은 까닭).
//
// 뜰 때 두 가지를 읽는다. 첫 계정 확인(`GET /auth/setup`)이 참이면 입력 칸 대신 첫 계정을 만드는 명령을 보인다. 지금 누구인지
// (`GET /auth/me`)가 읽히면 이미 로그인한 것이라 `next` 나 `/` 로 보낸다. 다만 `notice=password-set` 이면 보내지 않는다.
// 링크로 비밀번호를 정한 사람이 다른 계정으로 로그인한 채 그 링크를 열었을 수 있어, 방금 정한 계정으로 로그인할 길을 남긴다.
//
// `next` 는 같은 출처의 주소일 때만 받는다(`api/session` 의 `nextTarget`). 받지 못하면 `/` 다.
// 두 읽기가 끝나기 전에는 입력 칸을 세우지 않는다. 칸이 섰다가 명령 안내로 바뀌거나, 이미 로그인한 사람에게 칸이 잠깐 보이는 일을 막는다.

import "@agent-os/ui/fonts.css";
import "../../styles/admin.css";
import { useEffect } from "react";
import { canSignInAt, goTo, nextTarget, noticeOf } from "../../api/session";
import { useLogIn, useMe, useNeedsFirstAccount } from "../../hooks/queries/session";
import { useCurrentUrl } from "../../hooks/useCurrentUrl";
import { useForgetOldTokens } from "../../hooks/useForgetOldTokens";
import { useStoredTheme } from "../../stores/theme";
import { FirstAccountGuide } from "../organisms/FirstAccountGuide";
import { LoginForm } from "../organisms/LoginForm";
import { EntryFrame } from "../templates/EntryFrame";

function LoginScreen({ url }: { readonly url: URL }) {
  const notice = noticeOf(url.searchParams.get("notice"));
  const destination =
    nextTarget(url.searchParams.get("next"), url.origin) ?? new URL("/", url.origin).href;
  const me = useMe();
  const setup = useNeedsFirstAccount();
  const attempt = useLogIn(destination);
  const signedIn = me.data !== undefined;
  const leaving = signedIn && notice !== "password-set";

  useEffect(() => {
    if (leaving) {
      goTo(destination);
    }
  }, [leaving, destination]);

  const asked =
    (me.data !== undefined || me.error !== undefined) &&
    (setup.data !== undefined || setup.error !== undefined);
  if (!asked || leaving) {
    return <EntryFrame>{null}</EntryFrame>;
  }
  return (
    <EntryFrame>
      {setup.data === true ? (
        <FirstAccountGuide />
      ) : (
        <LoginForm
          notice={notice}
          insecure={!canSignInAt(url)}
          rejected={attempt.rejected}
          rejections={attempt.rejections}
          failure={attempt.failure}
          pending={attempt.pending}
          onSubmit={attempt.submit}
        />
      )}
    </EntryFrame>
  );
}

export function LoginPage() {
  useStoredTheme();
  useForgetOldTokens();
  const url = useCurrentUrl();
  if (url === null) {
    return <EntryFrame>{null}</EntryFrame>;
  }
  return <LoginScreen url={url} />;
}
