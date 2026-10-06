"""최종 사용자 경로의 상한. 기본값 일곱과 셈이 여기 한 곳에 있다(ADR 0023).

상한은 원격에 열린 최종 사용자 경로에만 건다. 운영자 채널(`/runs`)과 관리에는 없다. 요청 글자 수를
넘으면 422 이고(`body.request`), 동시 실행·시간당 실행·구독 수를 넘으면 429 와 `Retry-After` 다.
429 의 예외 타입(`LimitExceeded`)은 공용 층이 소유하고 여기서 던진다 — 표는 채널의 타입을 import 할
수 없고 라우트는 상태 코드를 스스로 정하지 않는다.

**기본값은 여기 한 곳이다**(루프 상한이 core 의 한 곳에 있는 것과 같은 모양). 사이트 파일의 상한
표는 값마다 선택이고(`SiteLimits`) 없음이 이 기본값이다. 전역 동시 실행만 사이트의 것이 아니라
`serve` 의 인자이고 그 없음도 이 기본값이다 — `serve` 도 `create_app` 도 값을 짓지 않는다. 기본값은
사용자가 고른 중간 묶음이고 재지 않은 어림이다(end-user-channel 명세 "상한").

**검사의 자리는 인증과 본문 검증 뒤, core 앞이다.** 422(형식, 글자 수)가 먼저이고 429 가 그다음이며
core 의 404·409 는 그 뒤다. 걸린 요청은 core 에 닿지 않아 트레이스도 셈도 늘지 않는다. 그래서 남의
실행에 낸 결정이나 목록 밖 에이전트로 보낸 시작도 404 보다 429 가 먼저다 — 드러나는 것은 요청하는
쪽 자신의 셈뿐이다.

**동시 실행은 칸으로 센다.** 최종 사용자 경로가 일으켜(결정도 든다) 지금 도는 실행 하나가 칸
하나다. 칸의 입장과 반환은 등록부(`Runs`)가 소유한다 — 상한 검사와 칸 차지가 await 없이 한
걸음이라 동시 요청 둘이 마지막 칸을 함께 차지하지 못하고, 반환은 실행의 태스크가 끝나는 한
자리에서 꼭 한 번이다(`runs` 모듈 독스트링). 이 모듈은 칸이 몇인지와 상한을 넘는지를 안다.

**시간당 실행은 미끄러지는 창이다.** 주체와 사이트마다 최근 3,600초 안의 시작 시각을 든다. 시작과
결정 모두 센다 — 둘 다 모델을 돌리는 요청이다. 요청이 오면 먼저 창 밖의 시각과 비어 버린 키를
지우고(명령), 그다음 수를 본다(질의). 그래서 셀 때의 셈 표는 창이 지난 키를 들고 있지 않고 키마다
많아야 상한 개의 시각이다. 지우는 것은 실행을 일으키는 요청이 올 때뿐이라 그 사이에는 창이 지난
키가 남는다. 시간당 셈은 칸이 아니라 시각이라 반환이 없다. 시계는 `Clock` 포트다.

**구독 수는 주체마다 열린 구독 연결(`GET`)의 수다.** 시작·결정 응답의 연결은 세지 않는다 — 그것은
동시 실행이 센다.

**동사.** 상한을 보고 칸 하나를 차지하는 것이 `take`, 돌려주는 것이 `give_back` 이다. 동시 실행의
칸과 구독 수가 같은 동사를 쓴다(`CONTEXT.md` 의 동사 표).

**`Retry-After`.** 시간당에 걸리면 창이 한 칸 비기까지의 초(올림, 1 이상)다. 동시 실행이나 구독
수에 걸리면 5초다 — 실행이 언제 끝날지 알 수 없어 짐작하지 않는다. 봉투의 문구는 어느 상한인지만
들고, 서버 기록은 사이트의 발급자와 상한의 범위(주체별·사이트별·전역)와 값을 든다. 주체(`sub`)는
어디에도 적지 않는다.

**셈은 프로세스 메모리다.** 워커가 하나라 충분하고(ADR 0014) 다시 시작하면 비워진다. 포트가 아니다.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi.exceptions import RequestValidationError

from agent_os.core.ports import Clock
from agent_os.http.errors import Limit, LimitExceeded
from agent_os.http.sites import EndUser, Site
from agent_os.sdk import Principal

# 기본값 일곱. 사이트 파일의 상한 표에 적지 않은 값과, `serve` 의 전역 인자를 주지 않았을 때의
# 값이다.
DEFAULT_REQUEST_CHARS = 20_000
DEFAULT_CONCURRENT_RUNS_PER_PRINCIPAL = 2
DEFAULT_HOURLY_RUNS_PER_PRINCIPAL = 60
DEFAULT_CONCURRENT_RUNS_PER_SITE = 20
DEFAULT_HOURLY_RUNS_PER_SITE = 1_000
DEFAULT_SUBSCRIPTIONS_PER_PRINCIPAL = 4
DEFAULT_CONCURRENT_RUNS = 50

# 시간당 실행의 창.
WINDOW = timedelta(seconds=3_600)
# 동시 실행이나 구독 수에 걸렸을 때의 `Retry-After`(초).
BUSY_RETRY_AFTER_SECONDS = 5


def check_request_chars(request: str, site: Site) -> None:
    """요청 글자 수가 그 사이트의 상한 안인지 본다. 넘으면 `body.request` 를 가리키는 422 다.

    글자는 코드 포인트(파이썬 `len`)다. 바이트가 아닌 이유는 사람이 쓴 글의 길이라서다. 본문의 형식
    오류와 같은 422 로 답하려고 FastAPI 의 검증 오류를 그대로 던진다 — 표의 같은 갈래를 지난다.
    받은 값은 오류에 싣지 않는다. 표의 기록이 형식 오류에서 받은 값을 싣지 않는 것과 같은 이유다
    (`http/errors.py` 의 `_detail_of`).
    """
    limit = _or_default(site.limits.request_chars, DEFAULT_REQUEST_CHARS)
    if len(request) <= limit:
        return
    raise RequestValidationError(
        [
            {
                "type": "string_too_long",
                "loc": ("body", "request"),
                "msg": f"String should have at most {limit} characters",
            }
        ]
    )


@dataclass(frozen=True, eq=False)
class Seat:
    """상한 아래의 칸 하나. 동시 실행의 칸은 등록부가 실행 하나에 하나를 들고 그 실행의 태스크가
    끝날 때 돌려주고, 구독의 칸은 구독의 의존성이 들고 응답이 끝나면 돌려준다. `take` 가 돌려준 칸은
    꼭 `give_back` 한다 — 버리면 칸이 샌다.

    같음을 값이 아니라 정체로 본다 — 같은 주체의 칸 둘은 값이 같아도 다른 칸이고, 돌려준 칸이 남의
    칸을 지우면 안 된다.
    """

    principal: Principal
    issuer: str


class RunQuota:
    """최종 사용자 경로가 일으키는 실행의 셈. 동시 실행의 칸과 시간당 실행의 시각을 든다.

    등록부(`Runs`)만 이것을 쓴다. 전역 동시 실행 상한은 조립이 넘긴 값이고 없음은 기본값이다.
    """

    def __init__(self, *, clock: Clock, concurrent_runs: int | None) -> None:
        self._clock = clock
        self._concurrent_runs = _or_default(concurrent_runs, DEFAULT_CONCURRENT_RUNS)
        self._seats: list[Seat] = []
        self._by_principal = _Window[Principal]()
        self._by_site = _Window[str]()

    def take(self, user: EndUser) -> Seat:
        """상한을 보고 칸 하나를 차지하고 시작 시각을 남긴다(명령). 걸리면 `LimitExceeded` 다.

        await 가 없다. 검사와 차지 사이에 다른 요청이 끼지 않는다.
        """
        now = self._clock.now()
        self._by_principal.forget_before(now - WINDOW)
        self._by_site.forget_before(now - WINDOW)
        refusal = self._refusal(user, now)
        if refusal is not None:
            raise refusal
        seat = Seat(principal=user.principal, issuer=user.site.issuer)
        self._seats.append(seat)
        self._by_principal.record(user.principal, now)
        self._by_site.record(user.site.issuer, now)
        return seat

    def give_back(self, seat: Seat) -> None:
        """칸 하나를 돌려준다(명령). 부르는 자리는 등록부의 한 곳이다."""
        self._seats.remove(seat)

    def _refusal(self, user: EndUser, now: datetime) -> LimitExceeded | None:
        """걸린 상한이 있으면 그 거절(질의). 동시 실행(주체별 → 사이트별 → 전역)을 먼저 보고 시간당
        실행(주체별 → 사이트별)을 본다. 앞의 것에 걸리면 뒤의 것은 보지 않는다."""
        limits = user.site.limits
        issuer = user.site.issuer
        concurrent = (
            (
                "주체별",
                sum(1 for seat in self._seats if seat.principal == user.principal),
                _or_default(
                    limits.concurrent_runs_per_principal, DEFAULT_CONCURRENT_RUNS_PER_PRINCIPAL
                ),
            ),
            (
                "사이트별",
                sum(1 for seat in self._seats if seat.issuer == issuer),
                _or_default(limits.concurrent_runs_per_site, DEFAULT_CONCURRENT_RUNS_PER_SITE),
            ),
            ("전역", len(self._seats), self._concurrent_runs),
        )
        for scope, count, limit in concurrent:
            if count >= limit:
                return _exceeded(
                    Limit.CONCURRENT_RUNS, scope, limit, issuer, BUSY_RETRY_AFTER_SECONDS
                )
        hourly = (
            (
                "주체별",
                self._by_principal.times(user.principal),
                _or_default(limits.hourly_runs_per_principal, DEFAULT_HOURLY_RUNS_PER_PRINCIPAL),
            ),
            (
                "사이트별",
                self._by_site.times(issuer),
                _or_default(limits.hourly_runs_per_site, DEFAULT_HOURLY_RUNS_PER_SITE),
            ),
        )
        for scope, times, limit in hourly:
            if len(times) >= limit:
                wait = _seconds_until_room(times, limit, now)
                return _exceeded(Limit.HOURLY_RUNS, scope, limit, issuer, wait)
        return None


class SubscriptionQuota:
    """주체마다 열린 구독 연결의 수. 구독 경로의 의존성이 들어올 때 차지하고 응답이 끝나면 돌려준다.

    동시 실행의 칸과 같은 모양이다 — 구독 연결 하나가 칸 하나다.
    """

    def __init__(self) -> None:
        self._open: dict[Principal, int] = {}

    def take(self, user: EndUser) -> Seat:
        """상한을 보고 칸 하나를 차지한다(명령). 걸리면 `LimitExceeded` 다. await 가 없다."""
        limit = _or_default(
            user.site.limits.subscriptions_per_principal, DEFAULT_SUBSCRIPTIONS_PER_PRINCIPAL
        )
        count = self._open.get(user.principal, 0)
        if count >= limit:
            raise _exceeded(
                Limit.SUBSCRIPTIONS, "주체별", limit, user.site.issuer, BUSY_RETRY_AFTER_SECONDS
            )
        self._open[user.principal] = count + 1
        return Seat(principal=user.principal, issuer=user.site.issuer)

    def give_back(self, seat: Seat) -> None:
        """칸 하나를 돌려준다(명령). 0 이 된 주체는 표에서 지운다."""
        remaining = self._open[seat.principal] - 1
        if remaining:
            self._open[seat.principal] = remaining
        else:
            del self._open[seat.principal]


class _Window[Key: Hashable]:
    """키마다 창 안의 시각들. 시각은 들어온 순서이고 그 순서가 곧 오래된 순서다."""

    def __init__(self) -> None:
        self._times: dict[Key, deque[datetime]] = {}

    def forget_before(self, cutoff: datetime) -> None:
        """`cutoff` 이하의 시각과 비어 버린 키를 지운다(명령). 창 밖이다."""
        for key in tuple(self._times):
            times = self._times[key]
            while times and times[0] <= cutoff:
                times.popleft()
            if not times:
                del self._times[key]

    def times(self, key: Key) -> Sequence[datetime]:
        """키의 시각들(질의). 없으면 비어 있다."""
        return tuple(self._times.get(key, ()))

    def record(self, key: Key, at: datetime) -> None:
        """시각 하나를 남긴다(명령)."""
        self._times.setdefault(key, deque()).append(at)


def _seconds_until_room(times: Sequence[datetime], limit: int, now: datetime) -> int:
    """창에 자리가 하나 날 때까지의 초(질의). 올림이고 1 이상이다.

    창 안의 시각이 `limit` 개 아래로 내려가려면 오래된 쪽부터 `len(times) - limit + 1` 개가 창을
    나가야 한다. 그 마지막 것이 나가는 때다. 보통은 꼭 `limit` 개라 가장 오래된 시각이다.
    """
    leaving = times[len(times) - limit]
    seconds = (leaving + WINDOW - now).total_seconds()
    return max(1, math.ceil(seconds))


def _exceeded(limit: Limit, scope: str, value: int, issuer: str, retry_after: int) -> LimitExceeded:
    """거절 하나(질의). 문구는 서버 기록에만 가고 사이트의 발급자와 범위와 값을 든다."""
    return LimitExceeded(
        f"사이트 {issuer} — {scope} {limit.value} 상한 {value}",
        limit=limit,
        retry_after_seconds=retry_after,
    )


def _or_default(value: int | None, default: int) -> int:
    return default if value is None else value
