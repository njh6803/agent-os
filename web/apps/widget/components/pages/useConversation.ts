// 대화를 돌린다. 요청마다 부모 창에서 새 토큰을 받아 최종 사용자 경로로 실행을 일으키고, 스트림의 항목을 대화의
// 규칙(lib/conversation)에 넘긴다. 열린 스트림은 하나이고, 새 대화와 페이지를 떠나는 것이 그것을 끊는다.

import { useCallback, useEffect, useReducer, useRef } from "react";
import { RunRejected, sendRun } from "../../api/runs";
import { allowedOrigins } from "../../lib/build";
import { INITIAL, reduce, type Action, type Conversation } from "../../lib/conversation";
import { requestToken } from "../../lib/token";

export interface ConversationControls {
  readonly conversation: Conversation;
  /** 요청 하나를 보낸다. 이어 갈 실행이 있으면 이어 가기이고 없으면 시작이다. */
  readonly send: (request: string) => void;
  /** 화면과 기억을 비우고 열린 스트림을 끊는다. */
  readonly reset: () => void;
}

export function useConversation(agent: string | null): ConversationControls {
  const [conversation, dispatch] = useReducer(reduce, INITIAL);
  const open = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      open.current?.abort();
    },
    [],
  );

  const { continueFrom } = conversation;
  const send = useCallback(
    (request: string) => {
      if (agent === null) {
        return;
      }
      open.current?.abort();
      const abort = new AbortController();
      open.current = abort;
      dispatch({ type: "sent", request });
      void run(agent, request, continueFrom, abort.signal, (action) => {
        if (!abort.signal.aborted) {
          dispatch(action);
        }
      });
    },
    [agent, continueFrom],
  );

  const reset = useCallback(() => {
    open.current?.abort();
    open.current = null;
    dispatch({ type: "reset" });
  }, []);

  return { conversation, send, reset };
}

type Dispatch = (action: Action) => void;

async function run(
  agent: string,
  request: string,
  continueFrom: string | null,
  signal: AbortSignal,
  dispatch: Dispatch,
): Promise<void> {
  const token = await requestToken(allowedOrigins());
  if (signal.aborted) {
    return;
  }
  if (token === null) {
    dispatch({ type: "no-token" });
    return;
  }
  try {
    const frames = await sendRun(token, agent, request, continueFrom, signal);
    for await (const frame of frames) {
      if (frame.kind === "item") {
        dispatch({ type: "item", item: frame.item });
      }
    }
    dispatch({ type: "ended" });
  } catch (error) {
    dispatch({ type: "rejected", status: error instanceof RunRejected ? error.status : null });
  }
}
