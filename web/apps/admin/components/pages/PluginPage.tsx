"use client";

// 플러그인 하나를 연 화면(web-admin 티켓 06). 주소의 두 조각(종류와 이름)을 라우트가 그대로 넘긴다.

import Link from "next/link";
import { useId } from "react";
import { isPluginKind, type PluginKind } from "../../api/plugins";
import { usePlugin } from "../../hooks/queries/plugins";
import { FailureNotice } from "../molecules/FailureNotice";
import { ScreenHeader } from "../molecules/ScreenHeader";
import { PluginDetail } from "../organisms/PluginDetail";
import { AdminScreen } from "./AdminScreen";
import { readOf } from "./read";
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
    <AdminScreen current="plugins">
      <Link href="/">플러그인 목록으로</Link>
      {decodedKind === null || decodedName === null ? (
        <AddressFailure title={name} message={`주소를 풀 수 없다: ${kind}/${name}`} />
      ) : isPluginKind(decodedKind) ? (
        <ConnectedPluginDetail kind={decodedKind} name={decodedName} />
      ) : (
        <AddressFailure title={decodedName} message={`플러그인의 종류가 아니다: ${decodedKind}`} />
      )}
    </AdminScreen>
  );
}

/**
 * 주소로 플러그인을 고르지 못한 화면. 읽기 골격(`ReadSection`)을 지나지 않아도 화면 머리의 제목은 주소의 이름 조각이다
 * (풀지 못했으면 받은 그대로).
 */
function AddressFailure({ title, message }: { readonly title: string; readonly message: string }) {
  const titleId = useId();
  return (
    <section aria-labelledby={titleId} className="flex flex-col gap-6">
      <ScreenHeader titleId={titleId} title={title} />
      <FailureNotice message={message} requestId={null} />
    </section>
  );
}

/** 플러그인 하나를 읽어 그린다. 주소를 푼 뒤, 관리 토큰이 받아들여진 뒤에만 서므로 읽기도 그때 시작한다. */
function ConnectedPluginDetail({
  kind,
  name,
}: {
  readonly kind: PluginKind;
  readonly name: string;
}) {
  const plugin = usePlugin(kind, name);
  return <PluginDetail name={name} {...readOf(plugin)} />;
}
