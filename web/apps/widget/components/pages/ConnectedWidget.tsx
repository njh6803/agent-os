// 위젯 한 벌. 두 임베드가 읽은 설정과 길을 받아 대화를 돌리고 화면을 그린다. iframe 방식은 WidgetPage 가 질의를,
// 페이지 안 방식은 element/ 의 커스텀 요소가 속성을 읽어 넘긴다. 테마·모드·밀도를 어디에 다는지도 임베드마다 다르다
// (web-widget 명세 "임베드", "테마·모드·밀도·글꼴"). 대화는 useConversation 이 돌린다.
//
// - 설정이 잘못됐으면 대화 자리에 위험 알림을 보이고 입력 자리를 막는다. 에이전트가 없거나 패턴 밖인 때와, 길이 없는
//   때(페이지 안 방식이 번들의 기준 주소를 읽지 못했다, element/base.ts), 값 파일이 없는 때(404)다. 길이 없으면 토큰도 묻지
//   않는다.
// - 열릴 때 값 파일(허용 출처와 요청 글자 수 상한, lib/runtime.ts)을 받는다. 받는 동안은 틀만 그리고 입력을 막는다. 대화가 쓰는
//   길(`Connection`)은 값을 받은 뒤에 짓는다. 그래서 값을 받기 전에는 토큰을 묻지 않고 저장한 대화를 되돌리는 일도 시작하지
//   않는다. 다시 받으면 풀릴 수 있는 실패는 알림과 "다시 시도"를 보이고 입력을 막는다.
// - 넘겨받은 문제는 하나마다 console.error 로 남긴다. 임베드가 다시 그려도 글이 같으면 다시 남기지 않는다.
import { useEffect, useMemo, useRef, useState } from "react";
import { connect, type EmbedConnection } from "../../lib/connection";
import { phaseOf, waitingApproval } from "../../lib/conversation";
import type { Embed } from "../../lib/embed";
import { useRuntimeValues } from "../../lib/runtime";
import { useConversation } from "./useConversation";
import { WidgetScreen, type Settings } from "./WidgetScreen";

/** 값을 받기 전에 입력창이 쓰는 글자 수 상한. 입력이 막혀 있어 화면에 드러나지 않는다. */
const PENDING_REQUEST_CHARS = Number.MAX_SAFE_INTEGER;

export interface ConnectedWidgetProps {
  readonly embed: Embed;
  /** console.error 로 남길 글. 문제마다 하나이고, 무엇이 틀렸고 위젯이 어떻게 그리는지 든다. */
  readonly problems: readonly string[];
  /** 최종 사용자 경로에 닿는 길. null 이면 요청을 보낼 수 없는 설정이다. */
  readonly connection: EmbedConnection | null;
}

export function ConnectedWidget({ embed, problems, connection: embedded }: ConnectedWidgetProps) {
  const [draft, setDraft] = useState("");
  const { state: runtime, retry } = useRuntimeValues(embedded?.baseUrl ?? null);
  const values = runtime.status === "ready" ? runtime.values : null;
  // 값을 받은 뒤에야 길이 선다. 그 전에는 null 이라 대화가 토큰을 묻지도 저장한 대화를 되돌리지도 않는다.
  const connection = useMemo(
    () => (embedded === null || values === null ? null : connect(embedded, values.allowedOrigins)),
    [embedded, values],
  );
  // 되돌아온 요청(422, 429)은 입력창에 넣는다.
  const { conversation, send, reset, decide, wait, invalid, restore, reconnect } = useConversation(
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

  const settings: Settings =
    runtime.status === "ready"
      ? "ready"
      : runtime.status === "unavailable"
        ? "failed"
        : "receiving";
  const phase = phaseOf(conversation);
  return (
    <WidgetScreen
      heading={embed.heading}
      intro={embed.intro}
      misconfigured={embed.agent === null || embedded === null || runtime.status === "missing"}
      settings={settings}
      onRetrySettings={retry}
      exchanges={conversation.exchanges}
      restarted={conversation.restarted}
      announcements={conversation.announcements}
      sendBlocked={
        settings !== "ready" ||
        restore !== "ready" ||
        phase !== "idle" ||
        (wait !== null && wait.remaining > 0)
      }
      wait={wait}
      invalid={invalid}
      paused={phase === "paused"}
      onDecide={decide}
      // 결정을 보내는 동안은 결정 응답이 결말 전이라 막는다. 결정을 기다리기만 할 때는 열려 있다. 끊겨 다시 잇는 동안도
      // 붙은 응답이 없어 열려 있다. 되돌리는 동안은 고를 대화가 아직 없어 막는다. 값을 받기 전에는 대화가 없다.
      newConversationDisabled={
        settings !== "ready" ||
        restore === "loading" ||
        (phase === "running" && reconnect === null) ||
        (waitingApproval(conversation)?.state.sending ?? null) !== null
      }
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
      requestChars={values === null ? PENDING_REQUEST_CHARS : values.requestChars}
      restore={restore}
      reconnect={reconnect}
    />
  );
}
