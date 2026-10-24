"use client";

// iframe 페이지. 사이트가 iframe 의 질의로 준 임베드 설정을 읽어 화면을 그리고, 문서 뿌리(html)에 테마·모드·
// 보통 밀도를 단다(web-widget 명세 "임베드"와 "테마·모드·밀도·글꼴"). 잘못 준 질의는 하나마다 그 이름을 든
// console.error 를 남긴다. 대화는 useConversation 이 돌린다.
//
// 질의는 브라우저의 주소에서 읽는다. 페이지는 빌드 때 미리 그려지고 그때는 주소가 없어(서버 스냅숏 null) 빈 몸으로
// 나가며, 하이드레이션 뒤 그린다. 속성은 그림을 칠하기 전(useLayoutEffect)에 달아 기본 테마로 한 번 칠해지지 않게 한다.
//
// 위젯의 CSS 와 글꼴 CSS 는 여기서 전역으로 싣는다. app/layout.tsx 에서 import 하면 층 경계가 막는다(ADR 0024).
import "@agent-os/ui/fonts.css";
import "../../styles/widget.css";
import { useEffect, useLayoutEffect, useMemo, useState, useSyncExternalStore } from "react";
import { requestCharLimit } from "../../lib/build";
import { phaseOf } from "../../lib/conversation";
import { readEmbed } from "../../lib/embed";
import { useConversation } from "./useConversation";
import { WidgetScreen } from "./WidgetScreen";

function subscribe(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  return () => {
    window.removeEventListener("popstate", onChange);
  };
}

export function WidgetPage() {
  const search = useSyncExternalStore(
    subscribe,
    () => window.location.search,
    () => null,
  );
  const read = useMemo(() => {
    if (search === null) {
      return null;
    }
    const params = new URLSearchParams(search);
    return readEmbed((name) => params.get(name));
  }, [search]);
  const { conversation, send, reset } = useConversation(read?.embed.agent ?? null);
  const [draft, setDraft] = useState("");

  useLayoutEffect(() => {
    if (read === null) {
      return;
    }
    const root = document.documentElement;
    root.dataset["theme"] = read.embed.theme;
    if (read.embed.mode === null) {
      delete root.dataset["mode"];
    } else {
      root.dataset["mode"] = read.embed.mode;
    }
    root.dataset["density"] = "regular";
    return () => {
      delete root.dataset["theme"];
      delete root.dataset["mode"];
      delete root.dataset["density"];
    };
  }, [read]);

  useEffect(() => {
    for (const problem of read?.problems ?? []) {
      console.error(`위젯 질의 ${problem.name}: ${problem.reason}`);
    }
  }, [read]);

  if (read === null) {
    return null;
  }
  const phase = phaseOf(conversation);
  return (
    <WidgetScreen
      heading={read.embed.heading}
      intro={read.embed.intro}
      misconfigured={read.embed.agent === null}
      exchanges={conversation.exchanges}
      announcements={conversation.announcements}
      sendBlocked={phase !== "idle"}
      paused={phase === "paused"}
      newConversationDisabled={phase === "running"}
      draft={draft}
      onDraftChange={setDraft}
      onSend={(request) => {
        setDraft("");
        send(request);
      }}
      // "다시 보내기"는 그 교환의 요청을 다시 보낼 뿐이라, 사용자가 입력창에 쓰던 글은 그대로 둔다.
      onRetry={send}
      onNewConversation={reset}
      requestChars={requestCharLimit()}
    />
  );
}
