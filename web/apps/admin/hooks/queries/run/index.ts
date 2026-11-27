// 대화 화면이 실행을 일으키고 결정을 내리는 훅(admin-login 티켓 11, 앞 이름은 web-admin 티켓 08의 `useDecision`). 컴포넌트는 요청
// 함수를 직접 부르지 않고 이것을 쓴다. 요청 하나를 보내고, 응답 스트림의 프레임을 받는 대로 들고, 스트림이 끝나면 그 실행의
// 트레이스를 다시 읽는다. 기록의 원천은 다시 읽은 트레이스다.
//
// **요청은 정확히 한 번이다**(스토리 46, ADR 0019). 스트림이 결말 없이 끊겨도 다시 보내지 않는다. 다시 보낸 결정은 다른
// 일시정지에 닿을 수 있고, 다시 보낸 시작은 실행을 하나 더 만든다. 끊긴 스트림은 트레이스를 다시 읽어 이어 본다. 실행은
// 서버에서 끝까지 간다(ADR 0014). 화면이 떠나면 연결을 끊고(요청의 `signal`) 그 요청은 더 아무것도 하지 않는다. SWR 의
// 캐시는 화면 사이에 하나라서, 떠난 요청이 다시 읽으면 그 사이 돌아온 화면이 읽는다.

import { useCallback, useEffect, useRef, useState } from "react";
import { useSWRConfig } from "swr";
import {
  sendDecision,
  type Decision,
  type RunEvent,
  type StreamFrame,
} from "../../../api/approval";
import { RequestFailure } from "../../../api/failure";
import { sendRun, type RunRequest } from "../../../api/run";
import { readTrace } from "../../../api/traces";
import { pluginKeys } from "../plugins";
import { traceKeys } from "../traces";

/**
 * 이벤트 종류마다 스트림을 끝맺는가. 스트림은 실행이 멈추거나 끝나거나 실패한 이벤트로 끝난다(ADR 0014). 이것으로 끝나지 않은
 * 스트림은 결말 없이 끊긴 것이다. 참인 셋은 core `run_status()` 가 결말 없음이 아닌 상태를 주는 갈래와 같다(web-admin 명세
 * "실행 하나"의 2026-09-30 이력). `Record` 라서 계약에 종류가 늘면 여기가 컴파일에서 깨져, 그 종류가 스트림을 끝맺는지
 * 정하게 된다. 대화 요약은 결말이 아니다. `run_status()` 의 갈래 밖이고 실행은 그 뒤에도 계속된다(ADR 0022).
 */
const ENDS_STREAM = {
  run_started: false,
  llm_called: false,
  tool_called: false,
  run_paused: true,
  approval_granted: false,
  approval_denied: false,
  run_resumed: false,
  run_finished: true,
  run_failed: true,
  conversation_summarized: false,
} as const satisfies Record<RunEvent["type"], boolean>;

/** 스트림의 마지막 프레임이 결말인가. 프레임이 없거나 읽지 못한 프레임이면 아니다. */
function endsStream(last: StreamFrame | null): boolean {
  return last?.kind === "event" && ENDS_STREAM[last.event.type];
}

/** 마지막 요청이 받아들여지지 않은 실패와 그 요청의 갈래. 다음 요청을 보내면 걷힌다. */
export interface RunFailure {
  readonly kind: "decide" | "send";
  readonly error: RequestFailure;
}

export interface RunStream {
  /**
   * 요청 하나가 끝날 때까지 참이다. 그동안 보내기와 결정 버튼을 막는다. 끝은 받아들여지지 않은 요청의 처리(409 면 다시 읽기까지)이거나
   * 응답 스트림 뒤의 다시 읽기와 화면 바꾸기다.
   */
  readonly busy: boolean;
  /** 받는 대로 쌓은 응답 스트림의 프레임. 다시 읽은 트레이스가 서면 걷힌다. */
  readonly frames: readonly StreamFrame[];
  /** 보낸 요청의 글. 시작 이벤트가 오기 전에도 화면이 그 요청을 말풍선에 둔다. 요청이 끝나면 걷힌다. */
  readonly pending: string | null;
  /** 마지막 응답 스트림이 결말 없이 끊겼다. */
  readonly cut: boolean;
  readonly failure: RunFailure | null;
  /** 실행을 일으키거나 이어 간다. 시작 이벤트가 오면 그 실행을 `onStarted` 로 알린다. */
  readonly send: (request: RunRequest) => void;
  /** 멈춘 실행 하나에 결정을 낸다. 결정의 자리는 부르는 쪽이 트레이스에서 읽어 결정에 싣는다. */
  readonly decide: (runId: string, decision: Decision) => void;
}

interface RunStreamOptions {
  /** 시작 이벤트가 온 순간. 주소를 그 실행으로 바꾸는 자리다. 한 번의 보내기에 한 번 부른다. */
  readonly onStarted: (runId: string) => void;
  /**
   * 스트림이 끝나고 그 실행의 트레이스를 다시 읽은 직후, 받은 프레임을 걷기 전에 부른다. 보내기가 만든 새 실행으로 화면을
   * 옮기는 자리다. 이 사이에 화면이 비지 않게 하려는 것이다.
   */
  readonly onSettled: (runId: string, kind: "decide" | "send") => Promise<void>;
}

export function useRunStream({ onStarted, onSettled }: RunStreamOptions): RunStream {
  const { mutate } = useSWRConfig();
  const [busy, setBusy] = useState(false);
  const [frames, setFrames] = useState<readonly StreamFrame[]>([]);
  const [pending, setPending] = useState<string | null>(null);
  const [cut, setCut] = useState(false);
  const [failure, setFailure] = useState<RunFailure | null>(null);
  // 보낸 요청의 연결. 화면이 떠나면 끊는다. 끝나기 전의 두 번째 요청은 막힌 버튼이 막는다(`busy`).
  const inFlight = useRef<AbortController | null>(null);
  // 처리기는 그릴 때마다 새로 만들어진다. 오래 걸리는 요청은 부를 때의 것이 아니라 마지막 것을 불러야 한다.
  const handlers = useRef({ onStarted, onSettled });
  handlers.current = { onStarted, onSettled };

  useEffect(
    () => () => {
      inFlight.current?.abort();
    },
    [],
  );

  /** 요청 하나의 공통 흐름. `open` 이 스트림을 열고, `target` 은 트레이스를 다시 읽을 실행을 알려 준다. */
  const run = useCallback(
    (
      kind: RunFailure["kind"],
      open: (signal: AbortSignal) => Promise<AsyncGenerator<StreamFrame, void, undefined>>,
      known: string | null,
      shown: string | null,
    ) => {
      const controller = new AbortController();
      inFlight.current = controller;
      setBusy(true);
      setFrames([]);
      setPending(shown);
      setCut(false);
      setFailure(null);
      // 다시 읽을 실행. 결정은 처음부터 알고, 보내기는 시작 이벤트가 와야 안다.
      let target = known;

      /** 받아들여지지 않은 요청. 요청 함수는 응답이 없거나(응답 전에 떠나 끊은 것도) 봉투인 것을 모두 RequestFailure 로
       * 던진다. 그 밖의 예외는 이 코드의 결함이라 덮지 않고 다시 던진다. */
      async function refused(error: unknown): Promise<void> {
        if (!(error instanceof RequestFailure)) {
          throw error;
        }
        setFailure({ kind, error });
        setPending(null);
        // 401 은 갱신 규칙이 이미 받았다(`api/session`). 갱신까지 401 이면 로그인 화면으로 가고, 그 밖의 실패면 그대로 남아
        // 화면이 "보내지 못했다"로 알린다.
        if (error.status === 409 && known !== null) {
          // 뜻 넷(자리 어긋남, 일시정지 아님, 형식 1, 꺼짐)이 같은 처리다. 가르는 것은 메시지다(ADR 0014 이력).
          // 꺼짐의 미리 알림이 목록에 기대므로 목록도 다시 읽는다.
          await Promise.all([mutate(traceKeys.one(known)), mutate(pluginKeys.list())]);
        }
      }

      /** 응답 스트림을 받는 대로 쌓고 마지막 프레임을 돌려준다. 끊겨도 던지지 않는다. */
      async function follow(
        received: AsyncGenerator<StreamFrame, void, undefined>,
      ): Promise<StreamFrame | null> {
        let last: StreamFrame | null = null;
        try {
          for await (const frame of received) {
            last = frame;
            setFrames((shown) => [...shown, frame]);
            if (target === null && frame.kind === "event" && frame.event.type === "run_started") {
              target = frame.event.run_id;
              handlers.current.onStarted(target);
            }
          }
        } catch {
          // 끊겼다. 결말을 받았는지는 마지막 프레임이 말한다. 결말 뒤의 끊김은 끊김이 아니다.
        }
        return last;
      }

      async function deliver(): Promise<void> {
        let received: AsyncGenerator<StreamFrame, void, undefined>;
        try {
          received = await open(controller.signal);
        } catch (error: unknown) {
          await refused(error);
          return;
        }
        const last = await follow(received);
        // 떠난 화면의 요청은 여기서 끝난다. 다시 읽을 화면이 없고, SWR 의 캐시가 화면과 함께 걷혔으면(`provider` 를 화면마다
        // 두는 설정. 페이지 테스트가 그렇다) 그 캐시에 부르는 mutate 가 처리하지 않은 에러로 남는다.
        if (controller.signal.aborted) {
          return;
        }
        setCut(!endsStream(last));
        if (target !== null) {
          // 읽은 값을 캐시에 넣는다. 보내기가 만든 실행은 아직 읽는 화면이 없어 `mutate(key)` 만으로는 읽지 않기 때문이다.
          // 읽지 못해도 화면이 그 실행을 열 때 스스로 읽고 실패를 보인다.
          await mutate(traceKeys.one(target), readTrace(target), { revalidate: false }).catch(
            () => undefined,
          );
          await handlers.current.onSettled(target, kind);
        }
        setFrames([]);
        setPending(null);
      }

      void deliver().finally(() => {
        inFlight.current = null;
        setBusy(false);
      });
    },
    [mutate],
  );

  const send = useCallback(
    (request: RunRequest) => {
      run("send", (signal) => sendRun(request, signal), null, request.request);
    },
    [run],
  );

  const decide = useCallback(
    (runId: string, decision: Decision) => {
      run("decide", (signal) => sendDecision(runId, decision, signal), runId, null);
    },
    [run],
  );

  return { busy, frames, pending, cut, failure, send, decide };
}
