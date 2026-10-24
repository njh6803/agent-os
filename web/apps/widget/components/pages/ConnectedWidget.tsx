// 위젯 한 벌. 두 임베드가 읽은 설정과 길을 받아 대화를 돌리고 화면을 그린다. iframe 방식은 WidgetPage 가 질의를,
// 페이지 안 방식은 element/ 의 커스텀 요소가 속성을 읽어 넘긴다. 테마·모드·밀도를 어디에 다는지도 임베드마다 다르다
// (web-widget 명세 "임베드", "테마·모드·밀도·글꼴"). 대화는 useConversation 이 돌린다.
//
// - 설정이 잘못됐으면 대화 자리에 위험 알림을 보이고 입력 자리를 막는다. 에이전트가 없거나 패턴 밖인 때와, 길이 없는
//   때(페이지 안 방식이 번들의 기준 주소를 읽지 못했다, element/base.ts)다. 길이 없으면 토큰도 묻지 않는다.
// - 넘겨받은 문제는 하나마다 console.error 로 남긴다. 임베드가 다시 그려도 글이 같으면 다시 남기지 않는다.
import { useEffect, useRef, useState } from "react";
import { requestCharLimit } from "../../lib/build";
import type { Connection } from "../../lib/connection";
import { phaseOf } from "../../lib/conversation";
import type { Embed } from "../../lib/embed";
import { useConversation } from "./useConversation";
import { WidgetScreen } from "./WidgetScreen";

export interface ConnectedWidgetProps {
  readonly embed: Embed;
  /** console.error 로 남길 글. 문제마다 하나이고, 무엇이 틀렸고 위젯이 어떻게 그리는지 든다. */
  readonly problems: readonly string[];
  /** 최종 사용자 경로에 닿는 길. null 이면 요청을 보낼 수 없는 설정이다. */
  readonly connection: Connection | null;
}

export function ConnectedWidget({ embed, problems, connection }: ConnectedWidgetProps) {
  const [draft, setDraft] = useState("");
  // 되돌아온 요청(422, 429)은 입력창에 넣는다.
  const { conversation, send, reset, wait, invalid } = useConversation(
    embed.agent,
    connection,
    setDraft,
  );

  // 배열은 그릴 때마다 새로 올 수 있어 앞서 남긴 글과 견준다.
  const logged = useRef<string | null>(null);
  useEffect(() => {
    const key = JSON.stringify(problems);
    if (key === logged.current) {
      return;
    }
    logged.current = key;
    for (const problem of problems) {
      console.error(problem);
    }
  }, [problems]);

  const phase = phaseOf(conversation);
  return (
    <WidgetScreen
      heading={embed.heading}
      intro={embed.intro}
      misconfigured={embed.agent === null || connection === null}
      exchanges={conversation.exchanges}
      restarted={conversation.restarted}
      announcements={conversation.announcements}
      sendBlocked={phase !== "idle" || (wait !== null && wait.remaining > 0)}
      wait={wait}
      invalid={invalid}
      paused={phase === "paused"}
      newConversationDisabled={phase === "running"}
      draft={draft}
      onDraftChange={setDraft}
      onSend={(request) => {
        setDraft("");
        send(request);
      }}
      // "다시 보내기"는 그 교환의 요청을 다시 보낼 뿐이라 입력창을 비우지 않는다. 그 요청이 422·429 로 돌아오면
      // 명세대로 입력창에 넣어, 쓰던 글을 덮는다(위 useConversation 의 onReturn).
      onRetry={send}
      onNewConversation={reset}
      requestChars={requestCharLimit()}
    />
  );
}
