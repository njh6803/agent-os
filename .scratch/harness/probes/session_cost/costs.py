"""모델 단가표와 응답 하나의 API 환산 비용. `collect.py`·`analyze.py`·`judge.py`가 같이 쓴다.

단가($/MTok)의 입력·출력은 claude-api 스킬(Claude Code 2.1.295 번들, 모델 표는 2026-10-06 캐시)을
읽은 것이다. `claude-opus-4-7`은 Skill 도구로 실은 스킬 본문의 모델 표에만, `claude-haiku-4-5`는 그
표와 동봉 문서 `shared/model-migration.md`에 있고, 나머지는 동봉 문서 `shared/models.md`에도 있다.
캐시 읽기는 같은 번들의 `shared/prompt-caching.md` "Economics"가 적은 배수다. `claude-fable-5-1`
0.025배($0.25), `claude-opus-5-5` 0.05배($0.20), 그 밖은 0.1배다. 캐시 쓰기는 5분이 입력의 1.25배,
1시간이 2배다(같은 문단과 `shared/cost-optimization.md`). `claude-haiku-5-5`는 프롬프트 10만 토큰
이하의 단가다. 웹 검색 요금은 표에 없다.

이 표가 Claude Code의 계산과 맞는지는 `collect.py`가 세션의 `cost-state` 기록(Claude Code가 모델마다
남긴 토큰과 `costUSD`)으로 본다. 그 기록은 캐시 쓰기를 5분과 1시간으로 가르지 않아, 표의 단가로 셈한
값이 "모두 5분"과 "모두 1시간" 사이에 드는지를 본다(`price_check`).
"""

from __future__ import annotations

from dataclasses import dataclass

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


@dataclass(frozen=True)
class Price:
    input: float
    output: float
    cache_read: float


PRICES: dict[str, Price] = {
    "claude-opus-5-5": Price(4.0, 20.0, 0.20),
    "claude-fable-5-1": Price(10.0, 50.0, 0.25),
    "claude-sonnet-5-5": Price(2.0, 10.0, 0.20),
    "claude-haiku-5-5": Price(0.10, 0.50, 0.01),
    "claude-opus-5": Price(5.0, 25.0, 0.50),
    "claude-opus-4-8": Price(5.0, 25.0, 0.50),
    "claude-opus-4-7": Price(5.0, 25.0, 0.50),
    "claude-sonnet-5": Price(2.0, 10.0, 0.20),
    "claude-haiku-4-5": Price(1.0, 5.0, 0.10),
}


def price_of(model: str) -> Price | None:
    """날짜가 붙은 이름(`claude-haiku-4-5-20251001`)은 날짜를 떼고 찾는다."""
    if model in PRICES:
        return PRICES[model]
    head, _, tail = model.rpartition("-")
    if tail.isdigit() and len(tail) == 8:
        return PRICES.get(head)
    return None


def _int(v: Json) -> int:
    return v if isinstance(v, int) and not isinstance(v, bool) else 0


@dataclass(frozen=True)
class Usage:
    input: int
    output: int
    thinking: int
    cache_read: int
    write_5m: int
    write_1h: int
    thinking_known: bool

    @staticmethod
    def of(u: dict[str, Json]) -> Usage:
        """캐시 쓰기의 TTL 갈래가 없는 기록은 전부 5분으로 본다(싼 쪽). 생각 토큰의 칸이 없으면
        0이고 `thinking_known`이 거짓이다."""
        total_write = _int(u.get("cache_creation_input_tokens"))
        cc = u.get("cache_creation")
        w5 = w1 = 0
        if isinstance(cc, dict):
            w5 = _int(cc.get("ephemeral_5m_input_tokens"))
            w1 = _int(cc.get("ephemeral_1h_input_tokens"))
        if w5 + w1 != total_write:
            w1 = min(w1, total_write)
            w5 = total_write - w1
        details = u.get("output_tokens_details")
        known = isinstance(details, dict) and "thinking_tokens" in details
        thinking = _int(details.get("thinking_tokens")) if isinstance(details, dict) else 0
        return Usage(
            input=_int(u.get("input_tokens")),
            output=_int(u.get("output_tokens")),
            thinking=thinking,
            cache_read=_int(u.get("cache_read_input_tokens")),
            write_5m=w5,
            write_1h=w1,
            thinking_known=known,
        )


def cost(model: str, u: Usage) -> float | None:
    """달러. 단가표에 없는 모델이면 None 이다."""
    p = price_of(model)
    if p is None:
        return None
    return (
        u.input * p.input
        + u.output * p.output
        + u.cache_read * p.cache_read
        + u.write_5m * p.input * 1.25
        + u.write_1h * p.input * 2.0
    ) / 1e6


def cost_state_bounds(model: str, mu: dict[str, Json]) -> tuple[float, float] | None:
    """`cost-state`의 모델별 토큰으로 셈한 비용의 아래·위 끝(캐시 쓰기가 모두 5분, 모두 1시간)."""
    p = price_of(model)
    if p is None:
        return None
    base = (
        _int(mu.get("inputTokens")) * p.input
        + _int(mu.get("outputTokens")) * p.output
        + _int(mu.get("cacheReadInputTokens")) * p.cache_read
    )
    write = _int(mu.get("cacheCreationInputTokens")) * p.input
    return (base + write * 1.25) / 1e6, (base + write * 2.0) / 1e6
