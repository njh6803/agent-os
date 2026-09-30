// 결정의 훅(web-admin 티켓 08). 컴포넌트는 요청 함수를 직접 부르지 않고 이것을 쓴다. 결정 하나를 보내고, 재개
// 스트림의 프레임을 받는 대로 들고, 스트림이 끝나면 트레이스를 다시 읽는다. 기록의 원천은 다시 읽은 트레이스다.
//
// **결정 요청은 정확히 한 번이다**(스토리 46, ADR 0019). 스트림이 결말 없이 끊겨도 다시 보내지 않는다. 다시 보낸 결정은
// 다른 일시정지에 닿을 수 있다. 끊긴 스트림은 트레이스를 다시 읽어 이어 본다. 실행은 서버에서 끝까지 간다(ADR 0014).
// 화면이 떠나면 연결을 끊고(요청의 `signal`) 그 결정은 더 아무것도 하지 않는다. SWR 의 캐시는 화면 사이에 하나라서, 떠난
// 결정이 다시 읽으면 그 사이 돌아온 화면이 읽는다.

import { useCallback, useEffect, useRef, useState } from "react";
import { useSWRConfig } from "swr";
import {
  sendDecision,
  type Decision,
  type RunEvent,
  type StreamFrame,
} from "../../../api/approval";
import { RequestFailure } from "../../../api/failure";
import { useTokens } from "../../../stores/tokens";
import { isRejection } from "../admin";
import { pluginKeys } from "../plugins";
import { traceKeys } from "../traces";

/**
 * 이벤트 종류마다 재개 스트림을 끝맺는가. 스트림은 실행이 멈추거나 끝나거나 실패한 이벤트로 끝난다(ADR 0014). 이것으로
 * 끝나지 않은 스트림은 결말 없이 끊긴 것이다. 참인 셋은 core `run_status()` 가 결말 없음이 아닌 상태를 주는 갈래와
 * 같다(web-admin 명세 "실행 하나"의 2026-09-30 이력). 상태의 이름은 보이지 않는다. `Record` 라서 계약에 종류가 늘면
 * 여기가 컴파일에서 깨져, 그 종류가 스트림을 끝맺는지 정하게 된다.
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
} as const satisfies Record<RunEvent["type"], boolean>;

/** 스트림의 마지막 프레임이 결말인가. 프레임이 없거나 읽지 못한 프레임이면 아니다. */
function endsStream(last: StreamFrame | null): boolean {
  return last?.kind === "event" && ENDS_STREAM[last.event.type];
}

export interface DecisionAttempt {
  /**
   * 결정 하나가 끝날 때까지 참이다. 그동안 결정 버튼을 막는다. 끝은 받아들여지지 않은 결정의 처리(409 면 다시 읽기까지)이거나
   * 재개 스트림 뒤의 다시 읽기다.
   */
  readonly busy: boolean;
  /** 받는 대로 쌓은 재개 스트림의 프레임. 다시 읽은 트레이스가 서면 걷힌다. */
  readonly frames: readonly StreamFrame[];
  /** 마지막 재개 스트림이 결말 없이 끊겼다. */
  readonly cut: boolean;
  /** 마지막 결정이 받아들여지지 않은 실패. 없으면 null 이다. 다음 결정을 보내면 걷힌다. */
  readonly failure: RequestFailure | null;
  /** 결정 하나를 보낸다. 채널 토큰이 없으면 보내지 않는다. */
  readonly decide: (decision: Decision) => void;
}

/** 한 실행에 결정을 낸다. 결정의 자리는 부르는 쪽이 트레이스 상세에서 읽어 결정에 싣는다. */
export function useDecision(runId: string): DecisionAttempt {
  const channelToken = useTokens((state) => state.channelToken);
  const generation = useTokens((state) => state.adminTokenGeneration);
  const { mutate } = useSWRConfig();
  const [busy, setBusy] = useState(false);
  const [frames, setFrames] = useState<readonly StreamFrame[]>([]);
  const [cut, setCut] = useState(false);
  const [failure, setFailure] = useState<RequestFailure | null>(null);
  // 보낸 결정의 연결. 화면이 떠나면 끊는다. 결정이 끝나기 전의 두 번째 결정은 막힌 버튼이 막는다(`busy`).
  const inFlight = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      inFlight.current?.abort();
    },
    [],
  );

  const decide = useCallback(
    (decision: Decision) => {
      if (channelToken === null) {
        return;
      }
      const controller = new AbortController();
      inFlight.current = controller;
      setBusy(true);
      setFrames([]);
      setCut(false);
      setFailure(null);
      const rereadTrace = () => mutate(traceKeys.one(generation, runId));

      /** 받아들여지지 않은 결정. 요청 함수는 응답이 없거나(응답 전에 떠나 끊은 것도) 봉투인 것을 모두 RequestFailure 로
       * 던진다. 그 밖의 예외는 이 코드의 결함이라 덮지 않고 다시 던진다. */
      async function refused(error: unknown, token: string): Promise<void> {
        if (!(error instanceof RequestFailure)) {
          throw error;
        }
        setFailure(error);
        if (isRejection(error)) {
          rejectChannelTokenIfStillHeld(token);
        } else if (error.status === 409) {
          // 뜻 넷(자리 어긋남, 일시정지 아님, 형식 1, 꺼짐)이 같은 처리다. 가르는 것은 메시지다(ADR 0014 이력).
          // 꺼짐의 미리 알림이 목록에 기대므로 목록도 다시 읽는다.
          await Promise.all([rereadTrace(), mutate(pluginKeys.list(generation))]);
        }
      }

      /** 재개 스트림을 받는 대로 쌓고 마지막 프레임을 돌려준다. 끊겨도 던지지 않는다. */
      async function follow(
        received: AsyncGenerator<StreamFrame, void, undefined>,
      ): Promise<StreamFrame | null> {
        let last: StreamFrame | null = null;
        try {
          for await (const frame of received) {
            last = frame;
            setFrames((shown) => [...shown, frame]);
          }
        } catch {
          // 끊겼다. 결말을 받았는지는 마지막 프레임이 말한다. 결말 뒤의 끊김은 끊김이 아니다.
        }
        return last;
      }

      async function deliver(token: string): Promise<void> {
        let received: AsyncGenerator<StreamFrame, void, undefined>;
        try {
          received = await sendDecision(token, runId, decision, controller.signal);
        } catch (error: unknown) {
          await refused(error, token);
          return;
        }
        const last = await follow(received);
        // 떠난 화면의 결정은 여기서 끝난다. 다시 읽을 화면이 없고, SWR 의 캐시가 화면과 함께 걷혔으면(`provider` 를
        // 화면마다 두는 설정. 페이지 테스트가 그렇다) 그 캐시에 부르는 mutate 가 처리하지 않은 에러로 남는다.
        if (controller.signal.aborted) {
          return;
        }
        setCut(!endsStream(last));
        await rereadTrace();
        setFrames([]);
      }

      void deliver(channelToken).finally(() => {
        inFlight.current = null;
        setBusy(false);
      });
    },
    [channelToken, generation, mutate, runId],
  );

  return { busy, frames, cut, failure, decide };
}

/**
 * 거부된 채널 토큰만 내려놓는다. 그 사이 운영자가 다른 토큰을 넣었으면 그것은 둔다. 거부된 것은 결정이 실은 토큰이다.
 * 관리 토큰의 늦은 401 과 같은 조건이다(`hooks/queries/admin`).
 */
function rejectChannelTokenIfStillHeld(channelToken: string): void {
  const tokens = useTokens.getState();
  if (tokens.channelToken === channelToken) {
    tokens.rejectChannelToken();
  }
}
