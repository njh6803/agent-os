// 위젯이 열릴 때 받는 값 파일(`/widget/runtime.json`, widget-runtime-values 티켓 01). 시작 래퍼가 뜰 때 사이트 파일에서 합친
// 허용 출처와 가장 작은 요청 글자 수 상한을 이 파일로 쓰고(tools/runtime.ts), 두 임베드가 열릴 때 받아 화면에 쓴다. 브라우저
// 쪽에서 두 값을 읽는 자리는 이 파일 하나다. 다른 코드는 `useRuntimeValues` 를 거쳐서만 읽는다.
//
// - 받는 자리는 임베드의 기준 주소 아래 `/widget/runtime.json` 이다. iframe 방식은 자기 페이지의 출처, 페이지 안 방식은 번들
//   스크립트가 실려 온 출처다(lib/connection.ts, element/base.ts). 쿠키와 자격 증명은 싣지 않는다. 응답의 CORS 머리는 설정
//   파일(next.config.ts)이 달아 어느 사이트 페이지에서도 읽힌다.
// - 받은 답은 두 키만 본다. 모르는 키는 무시한다. 허용 출처는 글자의 목록이고 상한은 1 이상의 정수다. 상한을 안전한 정수로
//   좁히지 않는다. 사이트 파일이 위로 막지 않고 받은 큰 상한에서 위젯이 닫히지 않게 하려는 것이다.
// - 실패는 둘로 가른다. 값 파일이 없는 404 는 설정이 틀린 것이라 다시 받아도 풀리지 않는다(`missing`). 요청 실패, 5xx, 10초
//   안에 답 없음, 읽지 못하는 답, 404 가 아닌 200 밖의 답은 다시 받으면 풀릴 수 있다(`unavailable`). 스스로 다시 받지 않고
//   `retry` 가 불릴 때만 다시 받는다.
// - 같은 주소는 문서 안에서 한 번만 받는다. 요소가 여럿 서거나 떼었다 붙여도 다시 받지 않는다. 값이 바뀐 것은 문서를 새로
//   열 때 반영된다. 실패한 답은 `retry` 가 지운다.
// - 전역 `fetch` 를 직접 쓰는 파일이다. 부르는 것이 Agent OS 의 API 가 아니라 위젯 자신의 정적 파일이라 생성 클라이언트를
//   거치지 않는다(web/eslint.config.mjs 의 예외가 이 파일 하나만 푼다).

import { useCallback, useEffect, useSyncExternalStore } from "react";

/** 값 파일의 경로. 위젯의 basePath(next.config.ts) 아래 공개 파일이다. */
export const RUNTIME_PATH = "/widget/runtime.json";

/** 받는 데 주는 시간. 넘기면 받지 못한 것이다. */
export const RUNTIME_TIMEOUT_MS = 10_000;

/** 값 파일의 내용. */
export interface RuntimeValues {
  /** 모든 사이트의 허용 출처를 합친 목록. 비면 postMessage 를 모두 버린다(ADR 0024 의 fail-closed). */
  readonly allowedOrigins: readonly string[];
  /** 모든 사이트의 요청 글자 수 상한 가운데 가장 작은 값. 세는 단위는 코드 포인트다. */
  readonly requestChars: number;
}

export type RuntimeState =
  | { readonly status: "loading" }
  | { readonly status: "ready"; readonly values: RuntimeValues }
  /** 다시 받으면 풀릴 수 있는 실패. */
  | { readonly status: "unavailable" }
  /** 값 파일이 없다(404). 다시 받아도 풀리지 않는다. */
  | { readonly status: "missing" };

const LOADING: RuntimeState = { status: "loading" };
const UNAVAILABLE: RuntimeState = { status: "unavailable" };
const MISSING: RuntimeState = { status: "missing" };

interface Entry {
  readonly state: RuntimeState;
  /** 받는 중일 때만 있다. */
  readonly controller: AbortController | null;
}

const entries = new Map<string, Entry>();
const listeners = new Set<() => void>();
// 시험이 걷은 뒤에 늦게 온 답을 버리려는 세대. 걷을 때마다 오른다.
let generation = 0;

function emit(): void {
  for (const listener of listeners) {
    listener();
  }
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function isTexts(value: unknown): value is readonly string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

/** 받은 JSON 을 값으로 읽는다. 읽지 못하면 null. */
function readValues(body: unknown): RuntimeValues | null {
  if (typeof body !== "object" || body === null) {
    return null;
  }
  const allowedOrigins = "allowedOrigins" in body ? body.allowedOrigins : undefined;
  const requestChars = "requestChars" in body ? body.requestChars : undefined;
  if (
    !isTexts(allowedOrigins) ||
    typeof requestChars !== "number" ||
    !Number.isInteger(requestChars) ||
    requestChars < 1
  ) {
    return null;
  }
  return { allowedOrigins, requestChars };
}

async function receive(url: string, signal: AbortSignal): Promise<RuntimeState> {
  try {
    const response = await fetch(url, { credentials: "omit", signal });
    if (response.status === 404) {
      return MISSING;
    }
    if (!response.ok) {
      return UNAVAILABLE;
    }
    const values = readValues(await response.json());
    return values === null ? UNAVAILABLE : { status: "ready", values };
  } catch {
    // 요청 실패, 시간 초과(중단), JSON 이 아닌 답.
    return UNAVAILABLE;
  }
}

/** 받기를 시작한다. 받는 동안은 `loading` 이고 끝나면 답의 상태로 바뀐다. */
function load(url: string): void {
  const controller = new AbortController();
  const mine = generation;
  entries.set(url, { state: LOADING, controller });
  emit();
  const timer = setTimeout(() => {
    controller.abort();
  }, RUNTIME_TIMEOUT_MS);
  void receive(url, controller.signal).then((state) => {
    clearTimeout(timer);
    if (mine !== generation) {
      return;
    }
    entries.set(url, { state, controller: null });
    emit();
  });
}

function valuesUrl(baseUrl: URL): string {
  return new URL(RUNTIME_PATH, baseUrl).href;
}

export interface RuntimeValuesControls {
  readonly state: RuntimeState;
  /** 다시 받으면 풀릴 수 있는 실패일 때만 다시 받는다. */
  readonly retry: () => void;
}

/**
 * 임베드의 기준 주소 아래 값 파일을 받아 상태를 준다. `baseUrl` 이 null 이면(요청을 보낼 수 없는 설정) 받지 않고 받는 중으로
 * 남는다. 받기는 그리고 난 뒤의 효과가 시작한다. 서버에서 미리 그릴 때는 늘 받는 중이다.
 */
export function useRuntimeValues(baseUrl: URL | null): RuntimeValuesControls {
  const url = baseUrl === null ? null : valuesUrl(baseUrl);
  const state = useSyncExternalStore(
    subscribe,
    () => (url === null ? LOADING : (entries.get(url)?.state ?? LOADING)),
    () => LOADING,
  );
  useEffect(() => {
    if (url !== null && !entries.has(url)) {
      load(url);
    }
  }, [url]);
  const retry = useCallback(() => {
    if (url !== null && entries.get(url)?.state.status === "unavailable") {
      load(url);
    }
  }, [url]);
  return { state, retry };
}

/**
 * 시험이 쓰는 이음매. 받은 값을 미리 둬 첫 그림부터 받은 상태로 선다. 실제로 받는 길은 components/pages/WidgetSettings.test.tsx 가 값 파일의
 * 응답을 흉내 내어 본다. 위젯 시험은 사례마다 이 값을 두고 시작한다(testing/setup.ts).
 */
export function seedRuntimeValues(baseUrl: URL, values: RuntimeValues): void {
  entries.set(valuesUrl(baseUrl), { state: { status: "ready", values }, controller: null });
  emit();
}

/** 시험이 쓰는 이음매. 받은 값과 받는 중인 요청을 모두 걷는다. 걷은 뒤에 늦게 온 답은 버린다. */
export function clearRuntimeValues(): void {
  generation += 1;
  for (const { controller } of entries.values()) {
    controller?.abort();
  }
  entries.clear();
  emit();
}
