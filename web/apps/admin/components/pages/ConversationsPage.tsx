"use client";

// 대화 목록 화면(admin-login 티켓 10). 상태로 거르고 이어서 더 본다. 저절로 다시 읽지 않는다.

import { useState } from "react";
import type { RunStatus } from "../../api/traces";
import { useConversationList } from "../../hooks/queries/conversations";
import { ConversationList } from "../organisms/ConversationList";
import { AdminScreen } from "./AdminScreen";
import { readOf } from "./read";

export function ConversationsPage() {
  return (
    <AdminScreen current="chat">
      <ConnectedConversationList />
    </AdminScreen>
  );
}

/**
 * 대화 목록을 읽어 그린다. 로그인한 계정을 읽은 뒤에만 서므로 읽기도 그때 시작한다. 고른 거르기는 읽기의 키라 여기 든다.
 */
function ConnectedConversationList() {
  const [status, setStatus] = useState<RunStatus | null>(null);
  const conversations = useConversationList(status);
  return (
    <ConversationList
      {...readOf(conversations)}
      status={status}
      onStatusChange={setStatus}
      onMore={() => {
        void conversations.setSize((size) => size + 1);
      }}
    />
  );
}
