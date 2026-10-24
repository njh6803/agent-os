// 대화를 돌린다. 요청마다 임베드가 준 길(lib/connection)로 새 토큰을 받아 최종 사용자 경로로 실행을 일으키고, 스트림의
// 항목을 대화의 규칙(lib/conversation)에 넘긴다. 열린 스트림은 하나이고, 새 대화와 페이지를 떠나는 것이 그것을 끊는다.
// 에이전트나 길이 없으면(설정이 잘못됐다) 토큰도 묻지 않고 요청도 보내지 않는다.
//
// 요청을 입력창으로 되돌리는 거절(422, 429)은 대화 밖의 상태다. 되돌린 요청은 부르는 쪽(`onReturn`)이 입력창에 넣고,
// 422 는 입력창 아래 안내를, 429 는 상한의 기다림(lib/limit)을 세운다. 둘 다 다음에 보낼 때 걷힌다. 기다림은 새
// 대화로는 걷히지 않는다. 서버는 상한을 대화와 상관없이 센다.

import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { RunRejected, sendRun } from "../../api/runs";
import type { Connection } from "../../lib/connection";
import { INITIAL, reduce, type Action, type Conversation } from "../../lib/conversation";
import { remainingAt, startWait, untilNextTick, type LimitWait } from "../../lib/limit";

export interface ConversationControls {
  readonly conversation: Conversation;
  /** 요청 하나를 보낸다. 이어 갈 실행이 있으면 이어 가기이고 없으면 시작이다. */
  readonly send: (request: string) => void;
  /** 화면과 기억을 비우고 열린 스트림을 끊는다. */
  readonly reset: () => void;
  /** 상한(429)에 걸려 기다리는 중. 시간이 다 되어도 다음에 보낼 때까지 남는다. */
  readonly wait: LimitWait | null;
  /** 앞 요청이 422 로 되돌아왔다. */
  readonly invalid: boolean;
}

/** `onReturn` 은 입력창으로 되돌릴 요청을 받는다(422, 429). */
export function useConversation(
  agent: string | null,
  connection: Connection | null,
  onReturn: (request: string) => void,
): ConversationControls {
  const [conversation, dispatch] = useReducer(reduce, INITIAL);
  const [wait, setWait] = useState<LimitWait | null>(null);
  const [invalid, setInvalid] = useState(false);
  const open = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      open.current?.abort();
    },
    [],
  );

  // 남은 초가 줄어드는 때마다 다시 센다. 0 이 되면 멈추고 기다림은 남는다.
  useEffect(() => {
    if (wait === null || wait.remaining === 0) {
      return;
    }
    const timer = setTimeout(
      () => {
        setWait((current) =>
          current === null ? null : { ...current, remaining: remainingAt(current, Date.now()) },
        );
      },
      untilNextTick(wait, Date.now()),
    );
    return () => {
      clearTimeout(timer);
    };
  }, [wait]);

  const { continueFrom } = conversation;
  const send = useCallback(
    (request: string) => {
      if (agent === null || connection === null) {
        return;
      }
      open.current?.abort();
      const abort = new AbortController();
      open.current = abort;
      setWait(null);
      setInvalid(false);
      dispatch({ type: "sent", request });
      void run(connection, agent, request, continueFrom, abort.signal, {
        dispatch: (action) => {
          if (!abort.signal.aborted) {
            dispatch(action);
          }
        },
        refuse: (rejected) => {
          if (abort.signal.aborted) {
            return;
          }
          onReturn(request);
          if (rejected.status === 422) {
            setInvalid(true);
          } else if (rejected.status === 429) {
            setWait(startWait(rejected.detail.limit, rejected.detail.retryAfter, Date.now()));
          }
        },
      });
    },
    [agent, connection, continueFrom, onReturn],
  );

  const reset = useCallback(() => {
    open.current?.abort();
    open.current = null;
    setInvalid(false);
    dispatch({ type: "reset" });
  }, []);

  return { conversation, send, reset, wait, invalid };
}

interface Report {
  readonly dispatch: (action: Action) => void;
  /** 요청을 입력창으로 되돌리는 거절(422, 429)을 받았다. */
  readonly refuse: (rejected: RunRejected) => void;
}

/** 이어 가기의 404 뒤 한 번 더 보내기까지 기다리는 시간. */
const CONTINUATION_RETRY_MS = 1_000;

/**
 * 요청 하나를 보낸다. 보낼 때마다 토큰을 새로 받는다. 이어 가기가 404 면 1초 뒤 한 번 더 보내고, 또 404 면 화면과
 * 기억을 비운 뒤 같은 요청을 시작으로 보낸다. 그 시작의 404 는 시작의 404 이고 더 보내지 않는다.
 */
async function run(
  connection: Connection,
  agent: string,
  request: string,
  continueFrom: string | null,
  signal: AbortSignal,
  { dispatch, refuse }: Report,
): Promise<void> {
  let target = continueFrom;
  let retried = false;
  for (;;) {
    const token = await connection.token();
    if (signal.aborted) {
      return;
    }
    if (token === null) {
      dispatch({ type: "no-token" });
      return;
    }
    // 끊은 뒤에 온 결과는 부르는 쪽의 dispatch 가 버린다.
    const rejected = await attempt(
      connection.baseUrl,
      token,
      agent,
      request,
      target,
      signal,
      dispatch,
    );
    if (rejected === null) {
      return;
    }
    const { status } = rejected;
    if (status === 404 && target !== null) {
      if (!retried) {
        retried = true;
        // 기다리는 동안 끊겼으면 토큰을 다시 청하지 않는다.
        if (!(await sleep(CONTINUATION_RETRY_MS, signal))) {
          return;
        }
        continue;
      }
      dispatch({ type: "restarted" });
      target = null;
      continue;
    }
    if (status === 404) {
      console.error(`위젯 에이전트 ${agent}: 서버가 찾지 못했다(404)`);
    }
    if (status === 422 || status === 429) {
      refuse(rejected);
    }
    dispatch({ type: "rejected", status });
    return;
  }
}

/**
 * 한 번 보내고 스트림을 끝까지 읽는다. 받아들여져 스트림을 읽었으면 null, 거절됐으면 그 거절이다. 읽는 도중의 끊김은
 * 처리하지 못한 것으로 끝낸다(재접속은 티켓 09).
 */
async function attempt(
  baseUrl: URL,
  token: string,
  agent: string,
  request: string,
  continueFrom: string | null,
  signal: AbortSignal,
  dispatch: Report["dispatch"],
): Promise<RunRejected | null> {
  let frames;
  try {
    frames = await sendRun(baseUrl, token, agent, request, continueFrom, signal);
  } catch (error) {
    // 끊어서 난 에러도 여기로 온다. 그 뒤의 결과는 부르는 쪽이 버린다.
    return error instanceof RunRejected
      ? error
      : new RunRejected(null, undefined, { cause: error });
  }
  try {
    for await (const frame of frames) {
      if (frame.kind === "item") {
        dispatch({ type: "item", item: frame.item });
      }
    }
  } catch {
    // 끊긴 것도 결말 없이 끝난 것과 같다.
  }
  dispatch({ type: "ended" });
  return null;
}

/** 기다린다. 끝까지 기다렸으면 참이고, 끊으면 곧바로 거짓으로 돌아온다. */
function sleep(ms: number, signal: AbortSignal): Promise<boolean> {
  return new Promise((resolve) => {
    // 이미 끊긴 신호에는 abort 가 다시 오지 않는다.
    if (signal.aborted) {
      resolve(false);
      return;
    }
    const timer = setTimeout(() => {
      resolve(true);
    }, ms);
    signal.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        resolve(false);
      },
      { once: true },
    );
  });
}
