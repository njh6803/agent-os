// 대화를 돌린다. 요청마다 임베드가 준 길(lib/connection)로 새 토큰을 받아 최종 사용자 경로로 실행을 일으키고, 스트림의
// 항목을 대화의 규칙(lib/conversation)에 넘긴다. 열린 스트림은 하나이고, 새 요청이나 결정이 앞의 것을 끊고 자리를 잇는다.
// 새 대화와 위젯이 걷히는 것(iframe 페이지를 떠나거나 사이트가 요소를 뗀다)도 그것을 끊는다. 에이전트나 길이 없으면(설정이
// 잘못됐다) 토큰도 묻지 않고 요청도 결정도 보내지 않는다.
//
// 요청을 입력창으로 되돌리는 거절(422, 429)은 대화 밖의 상태다. 되돌린 요청은 부르는 쪽(`onReturn`)이 입력창에 넣고,
// 422 는 입력창 아래 안내를, 429 는 상한의 기다림(lib/limit)을 세운다. 둘 다 다음에 보낼 때 걷힌다. 기다림은 새
// 대화로는 걷히지 않는다. 서버는 상한을 대화와 상관없이 센다.
//
// 승인 묻기의 결정도 같은 열린 스트림 자리를 쓴다. 결정의 거절은 명세 "요청이 거절될 때"의 결정 행대로 가른다. 결정의
// 429 는 결정의 기다림을 세우고, 그 기다림은 새 대화가 걷는다. 걷힌 대화에는 고를 카드가 없다.

import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import {
  RunRejected,
  sendDecision,
  sendRun,
  subscribeRun,
  type DecisionBody,
  type EndUserFrame,
} from "../../api/runs";
import type { Connection } from "../../lib/connection";
import {
  INITIAL,
  reduce,
  waitingApproval,
  type Action,
  type Conversation,
  type Decision,
} from "../../lib/conversation";
import { remainingAt, startWait, untilNextTick, type LimitWait } from "../../lib/limit";

export interface ConversationControls {
  readonly conversation: Conversation;
  /** 요청 하나를 보낸다. 이어 갈 실행이 있으면 이어 가기이고 없으면 시작이다. */
  readonly send: (request: string) => void;
  /** 화면과 기억을 비우고 열린 스트림을 끊는다. */
  readonly reset: () => void;
  /** 결정을 기다리는 승인 묻기에 결정을 보낸다. 기다리는 것이 없거나 보내는 중이면 아무것도 하지 않는다. */
  readonly decide: (decision: Decision) => void;
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
            setWait(
              startWait("send", rejected.detail.limit, rejected.detail.retryAfter, Date.now()),
            );
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
    setWait((current) => (current?.purpose === "decide" ? null : current));
    dispatch({ type: "reset" });
  }, []);

  // `waitingApproval` 은 렌더마다 새 객체를 돌려주므로, 콜백은 원시값인 멈춘 자리에만 기댄다.
  // 결정을 받을 수 없으면(기다리는 승인 묻기가 없거나 이미 보내는 중) `null` 이다.
  const waiting = waitingApproval(conversation);
  const pauseId = waiting === null || waiting.state.sending !== null ? null : waiting.pauseId;
  const runId = conversation.exchanges.at(-1)?.runId ?? null;
  const decide = useCallback(
    (decision: Decision) => {
      if (pauseId === null || runId === null || connection === null) {
        return;
      }
      open.current?.abort();
      const abort = new AbortController();
      open.current = abort;
      setWait(null);
      dispatch({ type: "deciding", decision: decision.decision });
      const body: DecisionBody =
        decision.decision === "approve"
          ? { decision: "approve", pause_index: pauseId }
          : { decision: "deny", reason: decision.reason, pause_index: pauseId };
      void runDecision(connection, runId, pauseId, body, abort.signal, {
        dispatch: (action) => {
          if (!abort.signal.aborted) {
            dispatch(action);
          }
        },
        limited: (rejected) => {
          if (!abort.signal.aborted) {
            setWait(
              startWait("decide", rejected.detail.limit, rejected.detail.retryAfter, Date.now()),
            );
          }
        },
      });
    },
    [connection, pauseId, runId],
  );

  return { conversation, send, reset, decide, wait, invalid };
}

interface Report {
  readonly dispatch: (action: Action) => void;
  /** 요청을 입력창으로 되돌리는 거절(422, 429)을 받았다. */
  readonly refuse: (rejected: RunRejected) => void;
}

/** 이어 가기나 결정의 404 뒤 한 번 더 보내기까지 기다리는 시간. */
const NOT_FOUND_RETRY_MS = 1_000;

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
        if (!(await sleep(NOT_FOUND_RETRY_MS, signal))) {
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
  await readItems(frames, dispatch);
  dispatch({ type: "ended" });
  return null;
}

/**
 * 스트림의 항목을 끝까지 넘긴다. 끊긴 것도 결말 없이 끝난 것과 같아 에러를 삼킨다. 받은 항목이 있었는지와 결정
 * 항목이 있었는지를 돌려준다.
 */
async function readItems(
  frames: AsyncGenerator<EndUserFrame, void, undefined>,
  dispatch: Report["dispatch"],
): Promise<{ readonly any: boolean; readonly decided: boolean }> {
  let any = false;
  let decided = false;
  try {
    for await (const frame of frames) {
      if (frame.kind === "item") {
        any = true;
        decided ||= frame.item.type === "decided";
        dispatch({ type: "item", id: frame.id, item: frame.item });
      }
    }
  } catch {
    // 끊긴 것도 결말 없이 끝난 것과 같다.
  }
  return { any, decided };
}

interface DecisionReport {
  readonly dispatch: (action: Action) => void;
  /** 결정이 429 를 받았다. */
  readonly limited: (rejected: RunRejected) => void;
}

/**
 * 결정 하나를 보낸다(명세 "요청이 거절될 때"의 결정 행). 보낼 때마다 토큰을 새로 받는다.
 *
 * - 받아들여지면 결정 항목부터 실행을 이어 받는다. 결정 항목 전에 끝나면 처리하지 못한 것이다.
 * - 404 면 1초 뒤 한 번 더 보내고, 또 404 면 그 승인 묻기를 더 받을 수 없다.
 * - 409 면 일시정지 프레임 뒤부터 다시 구독해 다른 탭이 낸 결정을 따라간다. 아무것도 없이 닫히면 보내지 못한 것이다.
 * - 401 이나 토큰을 받지 못한 것, 429, 그 밖(422, 500, 표 밖, 응답 전의 네트워크 실패)은 다시 결정을 받는다.
 */
async function runDecision(
  connection: Connection,
  runId: string,
  pauseId: number,
  body: DecisionBody,
  signal: AbortSignal,
  { dispatch, limited }: DecisionReport,
): Promise<void> {
  let retried = false;
  for (;;) {
    const token = await connection.token();
    if (signal.aborted) {
      return;
    }
    if (token === null) {
      dispatch({ type: "decision-refused", notice: "unauthorized" });
      return;
    }
    let frames;
    try {
      frames = await sendDecision(connection.baseUrl, token, runId, body, signal);
    } catch (error) {
      const status = error instanceof RunRejected ? error.status : null;
      if (status === 404 && !retried) {
        retried = true;
        if (!(await sleep(NOT_FOUND_RETRY_MS, signal))) {
          return;
        }
        continue;
      }
      if (status === 404) {
        dispatch({ type: "expired" });
      } else if (status === 409) {
        await follow(connection, runId, pauseId, signal, dispatch);
      } else if (status === 429 && error instanceof RunRejected) {
        limited(error);
        dispatch({ type: "decision-refused", notice: null });
      } else {
        dispatch({ type: "decision-refused", notice: status === 401 ? "unauthorized" : "error" });
      }
      return;
    }
    const read = await readItems(frames, dispatch);
    dispatch(read.decided ? { type: "ended" } : { type: "decision-refused", notice: "error" });
    return;
  }
}

/**
 * 결정이 409 였다. 일시정지 프레임 뒤부터 그 실행을 다시 구독해, 새 항목이 오면 따라간다(다른 탭이 결정했다). 아무것도
 * 없이 닫히면 일시정지가 그대로라 보내지 못한 것이다. 토큰을 받지 못하거나 구독이 401 이면 로그인 정보를 받지 못한 것이고,
 * 그 밖의 거절은 처리하지 못한 것이다.
 */
async function follow(
  connection: Connection,
  runId: string,
  pauseId: number,
  signal: AbortSignal,
  dispatch: Report["dispatch"],
): Promise<void> {
  const token = await connection.token();
  if (signal.aborted) {
    return;
  }
  if (token === null) {
    dispatch({ type: "decision-refused", notice: "unauthorized" });
    return;
  }
  let frames;
  try {
    frames = await subscribeRun(connection.baseUrl, token, runId, pauseId, signal);
  } catch (error) {
    const status = error instanceof RunRejected ? error.status : null;
    dispatch({ type: "decision-refused", notice: status === 401 ? "unauthorized" : "error" });
    return;
  }
  const read = await readItems(frames, dispatch);
  if (!read.any) {
    dispatch({ type: "decision-refused", notice: "conflict" });
  } else if (read.decided) {
    dispatch({ type: "ended" });
  } else {
    dispatch({ type: "decision-refused", notice: "error" });
  }
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
