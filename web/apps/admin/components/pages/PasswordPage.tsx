"use client";

// 내 비밀번호 바꾸기 화면(admin-login 명세 "계정 화면과 내 비밀번호"의 `/password`). 계정 메뉴의 "내 비밀번호 바꾸기"로 열고,
// 탐색의 어느 항목에도 들지 않는다. 누구나 자기 비밀번호를 바꿀 수 있다.

import { useChangePassword, useMe } from "../../hooks/queries/session";
import { ChangePasswordForm } from "../organisms/ChangePasswordForm";
import { AdminScreen } from "./AdminScreen";

export function PasswordPage() {
  return (
    <AdminScreen current={null}>
      <ConnectedForm />
    </AdminScreen>
  );
}

function ConnectedForm() {
  const me = useMe();
  const attempt = useChangePassword();
  if (me.data === undefined) {
    return null;
  }
  return (
    <ChangePasswordForm
      name={me.data.name}
      state={attempt}
      tokenMinutes={me.data.token_minutes}
      onSubmit={attempt.submit}
    />
  );
}
