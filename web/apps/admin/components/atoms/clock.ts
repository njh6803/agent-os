// 서버의 시각(ISO 8601)을 이 브라우저의 시간대로 적는 함수들. 실행 목록, 대화 목록, 대화 화면, 계정 목록이 함께 쓴다.
// 실행 패널은 트레이스의 UTC 값을 그대로 보이므로 쓰지 않는다. 하이드레이션 뒤에만 그려지는 본문이라 서버의 시간대와
// 갈릴 일이 없다(`AdminScreen`).

/**
 * 이 브라우저의 시간대로 시각을 적는 형식. 시간대를 주지 않아 `Intl` 이 고른 시간대이고, 그 이름도 이것이 든다. 숫자는
 * 늘 라틴 숫자이고 시는 0~23 이다. `hour12: false` 대신 시 주기를 바로 준다. 옛 사양을 따르는 엔진은 `hour12: false` 에
 * en-US 의 자정을 24 로 적을 수 있다(그런 엔진에서 재지는 않았다. Node 24.19·ICU 78.3 에서 `node -e` 로 손으로 보니
 * 둘 다 00 이었다).
 */
export function localClock(): Intl.DateTimeFormat {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
    numberingSystem: "latn",
  });
}

function partsOf(
  clock: Intl.DateTimeFormat,
  at: string,
): (type: Intl.DateTimeFormatPartTypes) => string {
  const parts = clock.formatToParts(new Date(at));
  return (type) => parts.find((found) => found.type === type)?.value ?? "";
}

/** "YYYY-MM-DD HH:mm:ss". 초 아래는 버린다. */
export function formatTime(clock: Intl.DateTimeFormat, at: string): string {
  const part = partsOf(clock, at);
  return `${part("year")}-${part("month")}-${part("day")} ${part("hour")}:${part("minute")}:${part("second")}`;
}

/** "YYYY-MM-DD HH:mm". 초는 적지 않는다. */
export function formatMinute(clock: Intl.DateTimeFormat, at: string): string {
  const part = partsOf(clock, at);
  return `${part("year")}-${part("month")}-${part("day")} ${part("hour")}:${part("minute")}`;
}

/** "HH:mm". 잠김이 풀리는 시각처럼 곧 닥칠 때에 쓴다. */
export function formatClockTime(clock: Intl.DateTimeFormat, at: string): string {
  const part = partsOf(clock, at);
  return `${part("hour")}:${part("minute")}`;
}
