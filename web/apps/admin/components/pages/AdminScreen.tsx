// 관리 화면의 한 화면이 서는 자리. 관리 토큰이 없으면 넣는 자리이고, 있으면 그 화면의 내용과 화면 사이를 오가는
// 링크다. 화면마다 이 문을 지난다. 관리 요청은 모두 관리 토큰을 싣기 때문이다(web-admin 스토리 1).

import Link from "next/link";
import type { ReactNode } from "react";
import { useHydrated } from "../../hooks/useHydrated";
import { useTokens } from "../../stores/tokens";
import { AdminTokenForm } from "../organisms/AdminTokenForm";
import { AdminFrame } from "../templates/AdminFrame";

export function AdminScreen({ children }: { readonly children: ReactNode }) {
  const hydrated = useHydrated();
  const adminToken = useTokens((state) => state.adminToken);
  const clearTokens = useTokens((state) => state.clearTokens);

  if (!hydrated) {
    return <AdminFrame />;
  }
  if (adminToken === null) {
    return (
      <AdminFrame>
        <AdminTokenForm />
      </AdminFrame>
    );
  }
  return (
    <AdminFrame
      nav={
        <>
          <Link href="/">플러그인 목록</Link> <Link href="/runs">실행 목록</Link>
        </>
      }
      actions={
        <button type="button" onClick={clearTokens}>
          토큰 지우기
        </button>
      }
    >
      {children}
    </AdminFrame>
  );
}
