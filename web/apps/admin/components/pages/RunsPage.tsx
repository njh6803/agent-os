"use client";

// 실행 목록 화면(web-admin 티켓 07). 상태로 거르고 이어서 더 본다.

import { useState } from "react";
import type { RunStatus } from "../../api/traces";
import { useRunList } from "../../hooks/queries/traces";
import { RunList } from "../organisms/RunList";
import { AdminScreen } from "./AdminScreen";
import { readOf } from "./read";

export function RunsPage() {
  return (
    <AdminScreen>
      <ConnectedRunList />
    </AdminScreen>
  );
}

/**
 * 실행 목록을 읽어 그린다. 관리 토큰이 받아들여진 뒤에만 서므로 읽기도 그때 시작한다. 고른 거르기는 읽기의 키라
 * 여기 든다.
 */
function ConnectedRunList() {
  const [status, setStatus] = useState<RunStatus | null>(null);
  const runs = useRunList(status);
  return (
    <RunList
      {...readOf(runs)}
      status={status}
      onStatusChange={setStatus}
      onMore={() => {
        void runs.setSize((size) => size + 1);
      }}
    />
  );
}
