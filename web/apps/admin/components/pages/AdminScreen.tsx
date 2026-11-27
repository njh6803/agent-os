// 관리 화면의 한 화면이 서는 자리. 로그인한 계정을 읽은 뒤에야 틀(탐색과 계정 자리)과 그 화면의 내용이 선다. 화면마다 이
// 문을 지난다. 로그인 여부는 쿠키가 HttpOnly 라 화면이 직접 알 수 없고, "지금 누구인지"(`GET /auth/me`)를 읽어서만 안다
// (admin-login 명세 "관리 화면의 페이지와 주소"). 쿠키가 없거나 끝났으면 요청 함수 아래의 갱신 규칙(`api/session`)이 갱신하고,
// 갱신까지 실패하면 로그인 화면으로 보낸다. 그래서 이 문은 읽는 동안 틀만 세우고 본문을 비워 둔다.
//
// pages 가 계정의 값(이름, 단계)을 읽어 organisms 에 props 로 넘긴다. organisms 는 훅도 스토어도 요청 함수도 가져오지 않는다.
//
// 관리 화면의 페이지(app/ 의 page.tsx)가 모두 지나므로 글꼴 CSS 와 앱의 전역 CSS(디자인 토큰 CSS 를 들인 것)를 여기서 싣는다(admin-style 명세
// "디자인 시스템 들이기"). 문서 뿌리에 모드와 밀도를 달지 않아, 모드는 시스템을 따르고 밀도는 폭을 따른다.
//
// 같은 까닭으로 테마도 여기서 지킨다(admin-style 티켓 09). 마운트될 때 하이드레이션이 지운 테마를 저장 값으로 되살리고,
// 마운트된 동안 다른 탭이 바꾼 테마를 따른다.

import "@agent-os/ui/fonts.css";
import "../../styles/admin.css";
import type { ReactNode } from "react";
import { describeFailure } from "../../api/failure";
import { useLogOut, useMe } from "../../hooks/queries/session";
import { useForgetOldTokens } from "../../hooks/useForgetOldTokens";
import { useStoredTheme } from "../../stores/theme";
import { FailureAlert } from "../molecules/FailureAlert";
import { AccountMenu } from "../organisms/AccountMenu";
import { AdminNav, type Section } from "../organisms/AdminNav";
import { AdminFrame } from "../templates/AdminFrame";

interface AdminScreenProps {
  /** 지금 화면이 든 탐색 항목. 어느 항목에도 들지 않는 화면(내 비밀번호 바꾸기)이면 null 이다. */
  readonly current: Section | null;
  readonly children: ReactNode;
}

export function AdminScreen({ current, children }: AdminScreenProps) {
  useStoredTheme();
  useForgetOldTokens();
  const me = useMe();
  const logOut = useLogOut();
  // "계정" 항목은 시스템 관리자에게만 보인다. 계정을 읽기 전에는 보이지 않는다.
  const nav = (
    <AdminNav
      current={current}
      showAccounts={me.error === undefined && me.data?.tier === "system_admin"}
    />
  );

  if (me.error !== undefined) {
    // 서버에 닿지 못했거나 서버가 오류를 냈다. 로그인하지 않은 것(401)이면 규칙이 로그인 화면으로 보내고, 옮겨 가는 동안과
    // 갱신이 네트워크로 실패해 끝났는지 모르는 때(규칙이 보내지 않는다)에는 이 알림이 보인다. 이미 읽은 계정이 캐시에 있어도
    // (화면을 옮겨 다시 읽다 실패한 때) 옛 이름과 본문을 지우고 실패만 보인다(`web-admin.md`의 다시 읽다 실패하면).
    const { message, requestId } = describeFailure(me.error);
    return (
      <AdminFrame nav={nav}>
        <FailureAlert title="로그인한 계정을 읽지 못했다" message={message} requestId={requestId} />
      </AdminFrame>
    );
  }
  if (me.data === undefined) {
    // 읽는 중이거나 갱신하는 중이다. 틀만 서고 본문은 비운다.
    return <AdminFrame nav={nav} />;
  }
  return (
    <AdminFrame
      nav={nav}
      account={
        <AccountMenu
          name={me.data.name}
          tier={me.data.tier}
          pending={logOut.pending}
          failed={logOut.failed}
          onLogOut={logOut.submit}
        />
      }
    >
      {children}
    </AdminFrame>
  );
}
