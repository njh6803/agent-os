"use client";

// 플러그인 하나를 연 화면(web-admin 티켓 06). 주소의 두 조각(종류와 이름)을 라우트가 그대로 넘긴다.

import Link from "next/link";
import { isPluginKind } from "../../api/plugins";
import { FailureNotice } from "../molecules/FailureNotice";
import { PluginDetail } from "../organisms/PluginDetail";
import { AdminScreen } from "./AdminScreen";

interface PluginPageProps {
  readonly kind: string;
  readonly name: string;
}

export function PluginPage({ kind, name }: PluginPageProps) {
  return (
    <AdminScreen>
      <Link href="/">플러그인 목록으로</Link>
      {isPluginKind(kind) ? (
        <PluginDetail kind={kind} name={name} />
      ) : (
        <FailureNotice message={`플러그인의 종류가 아니다: ${kind}`} requestId={null} />
      )}
    </AdminScreen>
  );
}
