// 접속 확인의 훅(ADR 0067 결정 "화면이 스스로 하는 확인"). 플러그인 화면의 행이 쓴다. 스스로 하는 확인은 켜 둔 원격
// MCP 서버와 켜 둔 모델의 행마다 30초마다 돌고, 켜 둔 stdio MCP 서버는 운영자가 버튼을 눌러야만 확인한다.
//
// 읽기 정책(`hooks/queries/admin` 의 `READ`)에는 주기 재확인이 없다. 이 파일의 `AUTO` 가 그 예외이고, 플러그인 화면에서만,
// 창이 보이는 동안에만, 켜 둔 원격 MCP 서버와 모델의 행 수만큼 요청을 보낸다. SWR(2.5.1)의 기본 동작으로는 되지 않는
// 셋을 아래처럼 푼다.
//
// - 오류 상태인 키는 주기 재확인을 건너뛴다. 그래서 요청의 실패를 던지지 않고 값(`failed`)으로 돌려준다.
// - 묶인 `mutate()` 는 날아가는 요청과 겹쳐 새 요청을 보낸다. 그래서 요청을 모듈의 `flights` 에 두고 같은 행의 요청이
//   날아가는 동안에는 그 요청을 함께 기다린다.
// - 키를 껐다 켜면 옛 캐시가 남는다. 그래서 키가 사라질 때(꺼짐, 페이지를 떠남) 그 키의 캐시와 날아가는 요청을 비운다.

import { useCallback, useEffect, useRef, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { describeFailure, RequestFailure } from "../../../api/failure";
import {
  checkConnection,
  checkConnectionByLaunching,
  type CheckableKind,
  type ConnectionCheck,
} from "../../../api/connection";
import type { ConnectionResult, PressedResult } from "../../../types/connection";
import { pluginKeys } from "../plugins";

/** 스스로 하는 확인의 읽기 정책. 간격은 30초이고 보이지 않는 동안은 SWR 이 쉰다(`refreshWhenHidden` 이 꺼짐). */
const AUTO = {
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  refreshInterval: 30_000,
  refreshWhenHidden: false,
  shouldRetryOnError: false,
  // 날아가는 요청과의 겹침은 `flights` 가 막는다. 끝난 뒤 2초 동안 새 요청을 막는 기본값은 껐다 켠 행의 확인을 늦춘다.
  dedupingInterval: 0,
} as const;

const AUTO_ROOT = "connection-check";

const connectionKeys = {
  auto: (kind: CheckableKind, name: string) => [AUTO_ROOT, kind, name] as const,
};

/** 날아가는 확인. 그 행(종류, 이름)이 화면에 서 있는 동안 같은 행의 요청은 하나만 보낸다. 행이 걷히면 비운다. */
const flights = new Map<string, Promise<ConnectionResult | null>>();

/** 지금 화면에 서 있는 행의 다시 확인. 행마다 하나다. */
const mounted = new Map<string, () => void>();

function flightKey(kind: CheckableKind, name: string): string {
  return JSON.stringify([kind, name]);
}

function sharedFlight(
  key: string,
  start: () => Promise<ConnectionResult | null>,
): Promise<ConnectionResult | null> {
  const existing = flights.get(key);
  if (existing !== undefined) {
    return existing;
  }
  const flight: Promise<ConnectionResult | null> = start().finally(() => {
    if (flights.get(key) === flight) {
      flights.delete(key);
    }
  });
  flights.set(key, flight);
  return flight;
}

/**
 * 확인 요청 하나를 보내 행에 보일 결과로 옮긴다. 요청의 실패는 `failed` 값이다. `null` 은 응답이 `disabled` 나
 * `not_applicable` 이라 보일 결과가 없다는 것이고, 목록이 그 사이 바뀐 것이다.
 */
async function resultOf(request: () => Promise<ConnectionCheck>): Promise<ConnectionResult | null> {
  try {
    const check = await request();
    switch (check.status) {
      case "reached":
        return { state: "reached" };
      case "unreached":
        return { state: "unreached", reason: check.reason };
      case "disabled":
      case "not_applicable":
        return null;
    }
  } catch (error: unknown) {
    // 요청 함수는 실패를 모두 RequestFailure 로 던진다. 그 밖의 예외는 이 코드의 결함이라 덮지 않고 다시 던진다.
    if (!(error instanceof RequestFailure)) {
      throw error;
    }
    return { state: "failed", message: describeFailure(error).message };
  }
}

/** 확인할 플러그인 하나. `enabled` 는 그 행이 켜져 있는지다. */
export interface ConnectionTarget {
  readonly kind: CheckableKind;
  readonly name: string;
  readonly enabled: boolean;
}

/**
 * 켜 둔 원격 MCP 서버나 켜 둔 모델의 행이 스스로 하는 확인. 꺼 둔 행이면 부르지 않는다. 처음 응답이
 * 오기 전과 응답이 `disabled` 나 `not_applicable` 일 때는 `undefined` 다.
 *
 * 다시 확인하는 동안에는 앞선 결과가 그대로 남는다. 보이지 않던 탭이 보이면 바로 한 번 확인한다.
 */
export function useAutoConnection({
  kind,
  name,
  enabled,
}: ConnectionTarget): ConnectionResult | undefined {
  const { mutate } = useSWRConfig();
  const run = enabled;
  const key = run ? connectionKeys.auto(kind, name) : null;
  const flight = flightKey(kind, name);

  const { data } = useSWR(
    key,
    run
      ? () =>
          // 보이지 않는 탭에서 행이 서면 첫 확인도 보내지 않는다(`refreshWhenHidden` 은 주기 확인만 쉬게 한다). 탭이 보이면
          // 아래 효과의 처리기가 바로 한 번 확인한다.
          document.visibilityState === "hidden"
            ? Promise.resolve(null)
            : sharedFlight(flight, async () => {
                const result = await resultOf(() => checkConnection(kind, name));
                if (result === null) {
                  void mutate(pluginKeys.list());
                }
                return result;
              })
      : null,
    AUTO,
  );

  // 키가 사라질 때(꺼짐, 페이지를 떠남) 그 행의 캐시와 날아가는 요청을 비운다. 그래야 다시 켰을 때 옛
  // 결과가 보이지 않고, 날아가던 옛 요청의 응답이 새 확인으로 쓰이지 않는다. SWR 의 효과가 먼저 걷히고 나서 이 정리가
  // 돌므로 `revalidate` 를 켜도 요청은 가지 않고, 날아가는 요청의 표지(중복을 막는 표)만 지워 다시 켰을 때 확인이 바로
  // 나간다. 키는 값이 같아도 렌더마다 새 배열이라, 효과 안에서 그 조각(kind, name)으로 다시 짓는다.
  useEffect(() => {
    if (!run) {
      return undefined;
    }
    const ownKey = connectionKeys.auto(kind, name);
    const refresh = (): void => {
      void mutate(ownKey);
    };
    const onVisibility = (): void => {
      if (document.visibilityState === "visible") {
        refresh();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    mounted.set(flight, refresh);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      if (mounted.get(flight) === refresh) {
        mounted.delete(flight);
      }
      flights.delete(flight);
      // 화면 전체가 걷힐 때는 SWR 의 상태가 먼저 사라져 mutate 가 던진다. 그때는 비울 캐시도 없다.
      mutate(ownKey, undefined, { revalidate: true }).catch(() => undefined);
    };
  }, [run, kind, name, flight, mutate]);

  return data ?? undefined;
}

/**
 * 목록의 새로 고침을 누를 때 스스로 하는 확인도 바로 한 번 다시 한다. 날아가는 확인이 있으면 그것을 함께 기다리므로 그
 * 행의 요청은 늘 하나다. 화면에 서 있지 않은 행은 보내지 않는다.
 */
export function refreshConnections(): void {
  for (const refresh of [...mounted.values()]) {
    refresh();
  }
}

export interface ManualConnection {
  /** 응답을 기다리는 중이다. 이 동안 다시 누를 수 없다. */
  readonly pending: boolean;
  readonly latest: PressedResult | undefined;
  /** 확인을 시작한다. 응답을 기다리는 중이거나 켜져 있지 않으면 아무것도 하지 않는다. */
  readonly run: () => void;
}

/**
 * 켜 둔 stdio MCP 서버의 접속 확인. 운영자가 누를 때만 서버를 한 번 띄운다. 결과는 이 부품의 상태에만 있다. 목록을
 * 다시 읽어도 남고, 플러그인을 끄거나 화면을 떠나면 사라진다. 끈 뒤에 도착하는 응답은 버린다.
 */
export function useManualConnection({ kind, name, enabled }: ConnectionTarget): ManualConnection {
  const { mutate } = useSWRConfig();
  const [pending, setPending] = useState(false);
  const [latest, setLatest] = useState<PressedResult | undefined>(undefined);
  const [wasEnabled, setWasEnabled] = useState(enabled);
  // 요청마다 번호를 매겨, 끄거나 새 요청이 시작된 뒤에 도착한 옛 응답을 버린다.
  const ticket = useRef(0);

  // 꺼지는 순간 결과를 지운다. 렌더 중에 상태를 맞추면 꺼진 행이 한 번도 옛 결과를 그리지 않는다.
  if (wasEnabled !== enabled) {
    setWasEnabled(enabled);
    if (!enabled) {
      setLatest(undefined);
      setPending(false);
    }
  }
  useEffect(() => {
    if (!enabled) {
      ticket.current += 1;
    }
  }, [enabled]);

  const run = useCallback(() => {
    if (!enabled || pending) {
      return;
    }
    ticket.current += 1;
    const mine = ticket.current;
    const pressedAt = new Date();
    setPending(true);
    void resultOf(() => checkConnectionByLaunching(kind, name)).then((result) => {
      if (ticket.current !== mine) {
        return;
      }
      setPending(false);
      if (result === null) {
        setLatest(undefined);
        void mutate(pluginKeys.list());
        return;
      }
      setLatest({ result, at: result.state === "failed" ? pressedAt : new Date() });
    });
  }, [enabled, kind, mutate, name, pending]);

  return { pending, latest, run };
}
