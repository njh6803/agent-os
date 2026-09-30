"use client";

// 실행 목록 화면(web-admin 티켓 07). 상태로 거르고 이어서 더 본다.

import { RunList } from "../organisms/RunList";
import { AdminScreen } from "./AdminScreen";

export function RunsPage() {
  return (
    <AdminScreen>
      <RunList />
    </AdminScreen>
  );
}
