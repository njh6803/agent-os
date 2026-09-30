"use client";

// 실행 하나를 연 화면(web-admin 티켓 07). 주소의 조각(실행 식별자)을 라우트가 그대로 넘긴다.

import Link from "next/link";
import { FailureNotice } from "../molecules/FailureNotice";
import { RunDetail } from "../organisms/RunDetail";
import { AdminScreen } from "./AdminScreen";
import { decodeSegment } from "./segment";

interface RunPageProps {
  /** 주소의 조각 그대로다. 퍼센트 인코딩이 풀리지 않았을 수 있다. */
  readonly runId: string;
}

export function RunPage({ runId }: RunPageProps) {
  const decoded = decodeSegment(runId);
  return (
    <AdminScreen>
      <Link href="/runs">실행 목록으로</Link>
      {decoded === null ? (
        <FailureNotice message={`주소를 풀 수 없다: ${runId}`} requestId={null} />
      ) : (
        <RunDetail runId={decoded} />
      )}
    </AdminScreen>
  );
}
