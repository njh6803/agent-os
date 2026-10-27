// 상한의 기다림(web-widget 명세 "상한", ADR 0023 이력 2026-10-23). 시작이나 이어 가기가 429 를 받으면 입력창 위 띠가
// 상한의 종류에 맞는 문구와 다시 보낼 수 있기까지의 시간을 보이고, 그동안 보내기를 막는다. 결정이 429 를 받으면 같은
// 문구를 "다시 고를 수 있습니다"로 끝맺고 그동안 결정 버튼을 막는다. 구독이 429 를 받으면 재접속 띠가 "연결이 많아"로
// 시작해 다시 잇는다고 말하고, 그 시간이 지나면 위젯이 스스로 다시 구독한다.
//
// - 기다릴 시간은 `Retry-After` 의 초이고, 없거나 읽지 못하면 5초다. 서버는 1 이상의 정수 초만 보낸다
//   (`channel/http/limits.py`). HTTP 날짜 꼴은 읽지 않는다. 0 은 읽어 곧바로 다시 보낼 수 있다는 글을 보인다.
// - 60초 이상이면 분으로 올려 적는다. 줄어들다 60초 아래로 내려가면 초로 적는다.
// - 범위를 모르므로 그 사람의 몫으로 단정하지 않는다. `subscriptions` 는 구독에서만 나고 그 문구는 구독의 기다림이
//   정한다. 시작과 이어 가기에서 온 그것은 모르는 값의 문구다.

/**
 * 무엇이 상한에 걸렸는가. 시작이나 이어 가기(`send`)면 문구가 "다시 보낼 수 있습니다"로 끝나고, 결정(`decide`)이면
 * "다시 고를 수 있습니다"로 끝난다. 구독(`subscribe`)이면 상한의 종류와 상관없이 재접속 띠의 문구다.
 */
export type WaitPurpose = "send" | "decide" | "subscribe";

/** 상한에 걸려 기다리는 중. 시간이 다 되어도 다음에 보낼 때까지 남는다. */
export interface LimitWait {
  readonly purpose: WaitPurpose;
  /** 봉투의 `limit`. 계약 밖의 값이나 없는 것도 그대로 든다. */
  readonly limit: string | null;
  /** 처음 받은 기다릴 시간(초). 화면 읽기 프로그램이 읽는 수다. */
  readonly seconds: number;
  /** 다시 보낼 수 있게 되는 시각(`Date.now()` 의 밀리초). */
  readonly until: number;
  /** 남은 초. 0 이면 다시 보낼 수 있다. */
  readonly remaining: number;
}

/** `Retry-After` 가 없거나 읽지 못할 때 기다리는 초. */
const DEFAULT_WAIT_SECONDS = 5;

/** `Retry-After` 의 초. 없거나 0 이상의 정수가 아니면 5다. */
export function retryAfterSeconds(header: string | null): number {
  if (header === null || !/^\d+$/.test(header.trim())) {
    return DEFAULT_WAIT_SECONDS;
  }
  const seconds = Number(header.trim());
  return Number.isSafeInteger(seconds) ? seconds : DEFAULT_WAIT_SECONDS;
}

/** 429 를 받은 시각(`now`)에서 기다림을 세운다. */
export function startWait(
  purpose: WaitPurpose,
  limit: string | null,
  retryAfter: string | null,
  now: number,
): LimitWait {
  const seconds = retryAfterSeconds(retryAfter);
  return { purpose, limit, seconds, until: now + seconds * 1_000, remaining: seconds };
}

/** `now` 에 남은 초. 올려 센다. */
export function remainingAt(wait: LimitWait, now: number): number {
  return Math.max(0, Math.ceil((wait.until - now) / 1_000));
}

/** 남은 초가 다음으로 줄어드는 때까지의 밀리초. */
export function untilNextTick(wait: LimitWait, now: number): number {
  return ((wait.until - now - 1) % 1_000) + 1;
}

/** 기다릴 시간의 글. 60초 이상이면 분으로 올려 적는다. */
export function waitText(seconds: number): string {
  return seconds >= 60 ? `${String(Math.ceil(seconds / 60))}분` : `${String(seconds)}초`;
}

/** 띠의 문구. 기다릴 시간의 앞과 뒤다. 그 사이에 `waitText` 가 들어간다. */
export interface LimitSentence {
  readonly before: string;
  readonly after: string;
}

// 결정의 429 는 상한의 문구를 "다시 고를 수 있습니다"로 끝맺는다(명세 "요청이 거절될 때"의 결정 행). 구독의 429 는 받은
// 것이 그대로라고 덧붙인다(같은 표의 구독 행).
const AFTER = {
  send: " 뒤에 다시 보낼 수 있습니다.",
  decide: " 뒤에 다시 고를 수 있습니다.",
  subscribe: " 뒤에 다시 잇습니다. 받은 내용은 그대로 있습니다.",
} satisfies Record<WaitPurpose, string>;

const BEFORE: ReadonlyMap<string, string> = new Map([
  ["concurrent_runs", "동시에 처리할 수 있는 요청이 가득 찼습니다. "],
  ["hourly_runs", "한 시간 동안 받을 수 있는 요청 수에 닿았습니다. "],
]);

const UNKNOWN_BEFORE = "요청이 많아 ";

// 디자인의 제안("연결이 끊겨 5초 뒤에 다시 잇습니다.")은 기다리는 까닭이 상한이라는 것을 말하지 않아 명세가 바꿨다.
const SUBSCRIBE_BEFORE = "연결이 많아 ";

export function limitSentence(limit: string | null, purpose: WaitPurpose): LimitSentence {
  const before =
    purpose === "subscribe"
      ? SUBSCRIBE_BEFORE
      : ((limit === null ? undefined : BEFORE.get(limit)) ?? UNKNOWN_BEFORE);
  return { before, after: AFTER[purpose] };
}

/** 시간이 다 된 뒤의 띠 문구. */
export const READY = "이제 다시 보낼 수 있습니다.";
