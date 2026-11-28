"use client";

// 계정 화면(admin-login 명세 "계정 화면과 내 비밀번호"). 시스템 관리자만 연다(권한 `manage_accounts`). 관리자가 주소로 열면 서버에
// 묻지 않고 "이 계정으로는 볼 수 없다" 한 줄만 보인다. 계정 목록과 쓰기는 이 화면을 연 계정이 시스템 관리자일 때만 읽는다.

import { setPasswordAddress } from "../../api/session";
import { useAccountActions, useAccounts } from "../../hooks/queries/accounts";
import { useMe } from "../../hooks/queries/session";
import { EmptyLine } from "../molecules/EmptyLine";
import { AccountList } from "../organisms/AccountList";
import { AdminScreen } from "./AdminScreen";
import { readOf } from "./read";

export function AccountsPage() {
  return (
    <AdminScreen current="accounts">
      <ConnectedAccounts />
    </AdminScreen>
  );
}

/** 지금 계정의 단계로 갈린다. 계정을 읽은 뒤에만 서므로(`AdminScreen`) 단계를 알고 있다. */
function ConnectedAccounts() {
  const me = useMe();
  const allowed = me.data?.tier === "system_admin";
  const accounts = useAccounts({ active: allowed });
  const actions = useAccountActions();
  if (me.data === undefined) {
    return null;
  }
  if (!allowed) {
    return (
      <EmptyLine icon="lock" iconSize="20">
        이 계정으로는 볼 수 없다
      </EmptyLine>
    );
  }
  return (
    <AccountList
      {...readOf(accounts)}
      currentName={me.data.name}
      tokenMinutes={me.data.token_minutes}
      actions={actions}
      addressOf={setPasswordAddress}
    />
  );
}
