// 상한의 기다림(web-widget 명세 "상한", ADR 0023 이력 2026-10-23). 시작이나 이어 가기가 429 를 받으면 입력창 위 띠가
// 상한의 종류에 맞는 문구와 다시 보낼 수 있기까지의 시간을 보이고, 그동안 보내기를 막는다.
//
// - 기다릴 시간은 `Retry-After` 의 초이고, 없거나 읽지 못하면 5초다. 서버는 1 이상의 정수 초만 보낸다
//   (`channel/http/limits.py`). HTTP 날짜 꼴은 읽지 않는다. 0 은 읽어 곧바로 다시 보낼 수 있다는 글을 보인다.
// - 60초 이상이면 분으로 올려 적는다. 줄어들다 60초 아래로 내려가면 초로 적는다.
// - 범위를 모르므로 그 사람의 몫으로 단정하지 않는다. `subscriptions` 는 구독에서만 나서 티켓 09 가 문구를 더한다.
//   그때까지 시작과 이어 가기에서 온 그것은 모르는 값의 문구다.

/** 상한에 걸려 기다리는 중. 시간이 다 되어도 다음에 보낼 때까지 남는다. */
export interface LimitWait {
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
export function startWait(limit: string | null, retryAfter: string | null, now: number): LimitWait {
  const seconds = retryAfterSeconds(retryAfter);
  return { limit, seconds, until: now + seconds * 1_000, remaining: seconds };
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

const AFTER = " 뒤에 다시 보낼 수 있습니다.";

const SENTENCES: ReadonlyMap<string, LimitSentence> = new Map([
  ["concurrent_runs", { before: "동시에 처리할 수 있는 요청이 가득 찼습니다. ", after: AFTER }],
  ["hourly_runs", { before: "한 시간 동안 받을 수 있는 요청 수에 닿았습니다. ", after: AFTER }],
]);

const UNKNOWN: LimitSentence = { before: "요청이 많아 ", after: AFTER };

export function limitSentence(limit: string | null): LimitSentence {
  return (limit === null ? undefined : SENTENCES.get(limit)) ?? UNKNOWN;
}

/** 시간이 다 된 뒤의 띠 문구. */
export const READY = "이제 다시 보낼 수 있습니다.";
