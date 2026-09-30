"use client";

// 플러그인 하나를 연 화면(web-admin 티켓 06). 주소의 두 조각(종류와 이름)을 라우트가 그대로 넘긴다.

import Link from "next/link";
import { isPluginKind } from "../../api/plugins";
import { FailureNotice } from "../molecules/FailureNotice";
import { PluginDetail } from "../organisms/PluginDetail";
import { AdminScreen } from "./AdminScreen";
import { decodeSegment } from "./segment";

interface PluginPageProps {
  /** 주소의 조각 그대로다. 퍼센트 인코딩이 풀리지 않았을 수 있다. */
  readonly kind: string;
  readonly name: string;
}

export function PluginPage({ kind, name }: PluginPageProps) {
  const decodedKind = decodeSegment(kind);
  const decodedName = decodeSegment(name);
  return (
    <AdminScreen>
      <Link href="/">플러그인 목록으로</Link>
      {decodedKind === null || decodedName === null ? (
        <FailureNotice message={`주소를 풀 수 없다: ${kind}/${name}`} requestId={null} />
      ) : isPluginKind(decodedKind) ? (
        <PluginDetail kind={decodedKind} name={decodedName} />
      ) : (
        <FailureNotice message={`플러그인의 종류가 아니다: ${decodedKind}`} requestId={null} />
      )}
    </AdminScreen>
  );
}
