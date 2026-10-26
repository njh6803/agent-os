// 대화를 돌린다. 요청마다 임베드가 준 길(lib/connection)로 새 토큰을 받아 최종 사용자 경로로 실행을 일으키고, 스트림의
// 항목을 대화의 규칙(lib/conversation)에 넘긴다. 비동기 일(시작·이어 가기, 결정, 다시 잇기, 되돌리기)은 drivers 가 하고,
// 이 훅은 그 일의 자리와 화면의 상태를 든다. 열린 일은 하나이고, 새 요청이나 결정이 앞의 것을 끊고 자리를 잇는다. 새
// 대화와 위젯이 걷히는 것(iframe 페이지를 떠나거나 사이트가 요소를 뗀다)도 그것을 끊는다. 에이전트나 길이 없으면(설정이
// 잘못됐다) 토큰도 묻지 않고 요청도 결정도 보내지 않으며 저장도 보지 않는다.
//
// 요청을 입력창으로 되돌리는 거절(422, 429)은 대화 밖의 상태다. 되돌린 요청은 부르는 쪽(`onReturn`)이 입력창에 넣고,
// 422 는 입력창 아래 안내를, 429 는 상한의 기다림(lib/limit)을 세운다. 둘 다 다음에 보낼 때 걷힌다. 기다림은 새
// 대화로는 걷히지 않는다. 서버는 상한을 대화와 상관없이 센다. 결정의 429 는 결정의 기다림을 세우고, 그 기다림은 새 대화가
// 걷는다. 걷힌 대화에는 고를 카드가 없다.
//
// 저장(lib/storage). 처음 그릴 때 저장한 대화가 있으면 토큰을 받아 묶음을 견주기 전에는 진행 표시만 보인다(`restore`).
// 그 뒤로는 대화가 바뀔 때마다 저장한다. 토큰을 받지 못해 그리지 못한 동안에는 저장을 건드리지 않는다.

import { useCallback, useEffect, useLayoutEffect, useReducer, useRef, useState } from "react";
import type { DecisionBody } from "../../api/runs";
import type { Connection } from "../../lib/connection";
import {
  INITIAL,
  reduce,
  waitingApproval,
  type Conversation,
  type Decision,
} from "../../lib/conversation";
import { remainingAt, startWait, untilNextTick, type LimitWait } from "../../lib/limit";
import type { Reconnect } from "../../lib/reconnect";
import {
  load,
  remove,
  sameBundle,
  save,
  sessionStore,
  snapshotOf,
  storageKey,
  type Bundle,
} from "../../lib/storage";
import {
  decide as runDecision,
  restore as restoreSaved,
  run,
  type Restored,
  type Session,
} from "./drivers";

/**
 * 저장한 대화를 되돌린 자리. `loading` 은 토큰을 받아 묶음을 견주는 중이라 진행 표시만 보인다. 되돌린 뒤의 자리는
 * drivers 의 `Restored` 다.
 */
export type Restore = "loading" | Restored;

export interface ConversationControls {
  readonly conversation: Conversation;
  /** 요청 하나를 보낸다. 이어 갈 실행이 있으면 이어 가기이고 없으면 시작이다. */
  readonly send: (request: string) => void;
  /** 저장과 화면과 기억을 비우고 열린 스트림을 끊는다. */
  readonly reset: () => void;
  /** 결정을 기다리는 승인 묻기에 결정을 보낸다. 기다리는 것이 없거나 보내는 중이면 아무것도 하지 않는다. */
  readonly decide: (decision: Decision) => void;
  /** 상한(429)에 걸려 기다리는 중. 시간이 다 되어도 다음에 보낼 때까지 남는다. */
  readonly wait: LimitWait | null;
  /** 앞 요청이 422 로 되돌아왔다. */
  readonly invalid: boolean;
  readonly restore: Restore;
  /** 끊긴 실행에 다시 잇는 중. */
  readonly reconnect: Reconnect | null;
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
  // 저장이 있는지는 그리기 전(useLayoutEffect)에 안다. 없으면 진행 표시는 칠해지지 않는다.
  const [restore, setRestore] = useState<Restore>("loading");
  const [reconnect, setReconnect] = useState<Reconnect | null>(null);
  const open = useRef<AbortController | null>(null);
  // 지금 대화의 토큰 묶음. 처음 받은 토큰이나 되돌린 저장의 것이고, 다른 묶음의 토큰이 오면 그것으로 바뀐다.
  const bundle = useRef<Bundle | null>(null);

  useEffect(
    () => () => {
      open.current?.abort();
    },
    [],
  );

  // 남은 초는 갱신이 적용될 때의 시각으로 센다. 다음 타이머는 다시 그린 뒤에야 서므로, 그리기가 늦으면(화면 동작
  // 시험의 act 는 시계를 돌리는 동안 그리기를 끝까지 미룬다) 타이머가 울린 때 센 값은 적용될 때 이미 지난 값이다.
  useCountdown(
    wait,
    useCallback(() => {
      setWait((current) =>
        current === null ? null : { ...current, remaining: remainingAt(current, Date.now()) },
      );
    }, []),
  );
  useCountdown(
    reconnect?.kind === "limited" ? reconnect.wait : null,
    useCallback(() => {
      setReconnect((current) =>
        current?.kind === "limited"
          ? {
              ...current,
              wait: { ...current.wait, remaining: remainingAt(current.wait, Date.now()) },
            }
          : current,
      );
    }, []),
  );

  const reset = useCallback(() => {
    open.current?.abort();
    open.current = null;
    setInvalid(false);
    setReconnect(null);
    setWait((current) => (current?.purpose === "decide" ? null : current));
    setRestore("ready");
    dispatch({ type: "reset" });
  }, []);

  /** 열린 일을 끊고 새 일의 자리를 연다. 끊긴 뒤에 온 것은 버린다. */
  const begin = useCallback(
    (through: Connection): Session => {
      open.current?.abort();
      const abort = new AbortController();
      open.current = abort;
      setReconnect(null);
      return {
        connection: through,
        signal: abort.signal,
        dispatch: (action) => {
          if (!abort.signal.aborted) {
            dispatch(action);
          }
        },
        matches: (next) => bundle.current === null || sameBundle(bundle.current, next),
        hold: (next) => {
          bundle.current = next;
        },
        reconnecting: (next) => {
          if (!abort.signal.aborted) {
            setReconnect(next);
          }
        },
        forget: reset,
      };
    },
    [reset],
  );

  // 저장한 대화를 되돌린다. 에이전트가 바뀌면 그 에이전트의 저장을 본다. 길은 임베드가 한 번 짓는다.
  useLayoutEffect(() => {
    if (agent === null || connection === null) {
      setRestore("ready");
      return;
    }
    const storage = sessionStore();
    const key = storageKey(agent);
    const loaded = load(storage, key);
    if (loaded.kind !== "saved") {
      if (loaded.kind === "invalid") {
        remove(storage, key);
      }
      setRestore("ready");
      return;
    }
    setRestore("loading");
    const session = begin(connection);
    void restoreSaved(session, loaded.saved, (restored) => {
      if (!session.signal.aborted) {
        setRestore(restored);
      }
    });
  }, [agent, connection, begin]);

  // 대화가 바뀔 때마다 저장한다. 되돌리기 전과 토큰을 받지 못한 동안에는 저장을 건드리지 않는다.
  useEffect(() => {
    const known = bundle.current;
    if (agent === null || restore !== "ready" || known === null) {
      return;
    }
    save(sessionStore(), storageKey(agent), known, snapshotOf(conversation));
  }, [agent, restore, conversation]);

  const { continueFrom } = conversation;
  const send = useCallback(
    (request: string) => {
      if (agent === null || connection === null) {
        return;
      }
      const session = begin(connection);
      setWait(null);
      setInvalid(false);
      dispatch({ type: "sent", request });
      void run(session, agent, request, continueFrom, (rejected) => {
        if (session.signal.aborted) {
          return;
        }
        onReturn(request);
        if (rejected.status === 422) {
          setInvalid(true);
        } else if (rejected.status === 429) {
          setWait(startWait("send", rejected.detail.limit, rejected.detail.retryAfter, Date.now()));
        }
      });
    },
    [agent, connection, begin, continueFrom, onReturn],
  );

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
      const session = begin(connection);
      setWait(null);
      dispatch({ type: "deciding", decision: decision.decision });
      const body: DecisionBody =
        decision.decision === "approve"
          ? { decision: "approve", pause_index: pauseId }
          : { decision: "deny", reason: decision.reason, pause_index: pauseId };
      void runDecision(session, runId, pauseId, body, (rejected) => {
        if (!session.signal.aborted) {
          setWait(
            startWait("decide", rejected.detail.limit, rejected.detail.retryAfter, Date.now()),
          );
        }
      });
    },
    [connection, begin, pauseId, runId],
  );

  return { conversation, send, reset, decide, wait, invalid, restore, reconnect };
}

/** 기다림의 남은 초가 줄어드는 때마다 `tick` 으로 다시 센다. 0 이 되면 멈추고 기다림은 남는다. `tick` 은 바뀌지 않아야 한다. */
function useCountdown(wait: LimitWait | null, tick: () => void): void {
  useEffect(() => {
    if (wait === null || wait.remaining === 0) {
      return;
    }
    const timer = setTimeout(tick, untilNextTick(wait, Date.now()));
    return () => {
      clearTimeout(timer);
    };
  }, [wait, tick]);
}
