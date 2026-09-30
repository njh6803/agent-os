"use client";

// 플러그인 하나를 연 화면(web-admin 티켓 06). 주소의 두 조각(종류와 이름)을 라우트가 그대로 넘긴다.

import Link from "next/link";
import { isPluginKind } from "../../api/plugins";
import { FailureNotice } from "../molecules/FailureNotice";
import { PluginDetail } from "../organisms/PluginDetail";
import { AdminScreen } from "./AdminScreen";

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

/**
 * 주소의 조각을 푼다. Next 16.3.6 은 동적 조각을 퍼센트 인코딩된 채로 넘긴다(e2e 의 패턴 밖 표지 흐름이 쟀다). 요청
 * 함수가 다시 인코딩하므로 풀지 않으면 두 번 인코딩된다. 풀 수 없는 조각이면 null 이다.
 */
function decodeSegment(segment: string): string | null {
  try {
    return decodeURIComponent(segment);
  } catch {
    return null;
  }
}
