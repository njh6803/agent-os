"""다시 풀기 회차의 공식 단가 셈. 세션 기록 파일의 assistant 응답마다 공식 단가로 비용을 셈한다.

명세는 `.scratch/model-rerun/spec.md`의 "회차 기록"(공식 단가 셈 문단과 그 2026-10-22 주석)과
"상한과 끄기"의 2026-10-22 주석(끈 호출이 든 세션의 비용 칸에 이 셈을 대신 넣는다)이고, 티켓은
`.scratch/model-rerun/issues/07-gates-and-official-cost.md`의 "공식 단가"다. 회차 기록의 비용 칸에
이 셈을 넣는 것은 회차를 돌고 기록을 짓는 쪽(06·10)이다.

두 층이다.
- 값만 받는 셈(`cost_of`, `round_cost`)은 파일을 열지 않는다. `cost_of`는 세션 하나의 기록 줄(본
  세션과 서브에이전트 기록을 이어 붙인 것)과 그 세션의 마지막 `modelUsage`를 받는다.
  - 응답은 `type`이 `assistant`이고 `message.usage`가 든 줄이다. 모델이 `<synthetic>`인 줄, JSON으로
    풀리지 않는 줄은 세지 않는다. 모델이 없는 응답은 `PriceError`다. 빼면 그 응답의 비용이 셈에서
    빠져 낮게 나온다.
  - 응답은 `message.id`로 한 번만 센다. 같은 id의 줄이 여럿이면 출력 토큰이 가장 큰 usage를 쓰고,
    모델은 첫 줄의 것이다. id가 없으면 줄의 `uuid`로, 그것도 없으면 줄마다 따로 센다. 여기까지는
    사용량 장부(`tools/token_report.py`의 `read_stream`)와 같다. 장부와 달리 세션의 기록 파일을 모두
    이어 붙여 한 번에 세고, 시각이 없는 응답도 세며, 모델이 없는 응답을 `(모름)`으로 세지 않는다.
  - 캐시 쓰기는 `cache_creation`의 5분 몫(입력 단가의 `WRITE_5M`배)과 1시간 몫(`WRITE_1H`배)으로
    나눈다. 나눈 합이 `cache_creation_input_tokens`와 맞지 않으면 1시간 몫을 합으로 자르고 남는
    몫을 5분으로 본다(장부의 `_cache_writes`와 같다).
  - Haiku 5.5는 응답마다 프롬프트(입력, 캐시 읽기, 캐시 쓰기의 합)가 `HAIKU_LONG_PROMPT`를 넘으면
    그 응답의 모든 토큰을 `HAIKU_LONG_PRICE`로 셈한다.
  - 기록 줄에 응답이 있는 모델은 `modelUsage`의 그 모델(꼬리만 다른 이름은 더한다)과 칸마다(입력,
    출력, 캐시 읽기, 캐시 쓰기) 견주어, 응답 셈이 모자란 몫을 같은 단가로 더한다. 캐시 쓰기 몫은 5분
    배수, Haiku는 10만 토큰 이하의 단가다. 응답 셈이 많은 칸은 빼지 않는다. 조건 판 2의 파일럿에서
    세션 기록 파일은 출력 토큰이 모자랐고(Opus는 입력, 캐시 읽기, 캐시 쓰기도), 이렇게 채우면
    모델마다 `costUSD`와 맞았다(`.scratch/model-rerun/probes/official_cost/`).
  - 기록 줄에 응답이 없는 모델이 `modelUsage`에 있으면 그 모델의 토큰을 캐시 쓰기 5분 배수로 셈해
    더하고(어림), 그 모델(아래 꼬리를 뗀 이름)과 토큰을 `substitutes`에 따로 든다. 꼬리만 다른
    이름(`X`와 `X[1m]`)은 한 항목으로 더한다.
  - 토큰 합은 응답 셈과 채운 몫에서 낸다. 대신 셈한 모델의 토큰은 `substitutes`에만 들고 합에는
    없다.
  - 모델 이름은 끝의 `[1m]`과 날짜(`-YYYYMMDD`)를 떼고 단가를 찾고, 응답과 `modelUsage`의 같은
    모델을 가른다. 단가가 없는 모델도 `PriceError`다.
  - `round_cost`는 세션마다의 셈을 더한다. 회차의 합은 세션마다의 합이고, 대신 셈한 같은 모델은 한
    항목으로 더한다.
- 파일 층(`session_cost`)은 본 세션 기록 파일 `<세션 id>.jsonl`과 그 옆 `<세션 id>/subagents/`의
  `*.jsonl`을 읽어 `cost_of`에 넘긴다. 기록 파일을 세션 id로 찾는 것은 부르는 쪽이다(명세 "러너가
  기대는 `claude -p`의 동작"의 2026-10-22 주석). 본 세션 기록 파일이 없으면 `FileNotFoundError`다.
  줄은 `\\n`으로만 가른다. 글 안의 U+2028에서 가르면 그 응답이 셈에서 빠진다(장부의 `read_records`와
  `tools/rerun_session.py`의 기록 줄 읽기와 같다).

단가 상수는 `docs/model-selection.md` 2절의 표에서 옮겼고 그 문서와 묶지 않는다. 본 측정의 단가는
사전 등록 절(11)이 고정하고 그 뒤 바꾸지 않는데, 그 문서는 단가가 바뀌면 고쳐지는 살아 있는 문서다.
사용량 장부의 단가표(`tools/token_report.py`의 `PRICES`)도 쓰지 않는다. 그 표는 Sonnet 5.5의 캐시
읽기를 Claude Code가 셈한 0.1배로 두어 공식 단가(0.05배)와 다르다.

못 보는 것.
- 생각 토큰. 커밋한 프로브
  원본(`.scratch/model-rerun/probes/headless_flags/2026-10-22/서브-2.jsonl`)의 assistant 응답
  usage에는 생각 토큰 칸이 없다(결과 이벤트의 usage에는 `output_tokens_details`가, `modelUsage`에는
  `thinkingTokens`가 있다). 그래서 응답 셈의 생각 합은 늘 빈 값이고, 대신 셈한 모델만 `modelUsage`의
  `thinkingTokens`를 옮긴다. 생각 토큰은 출력 토큰으로 셈한다는 공식 단가를 따라 비용에는 출력 칸만
  쓴다.
- 기록 파일이 모자란 까닭. 출력이 모자란 것이 assistant 줄의 출력 토큰이 끝까지 쌓이기 전의
  값이어서인지, Opus의 다른 칸이 모자란 것이 기록 파일에 남지 않는 요청이 있어서인지는 재지 않았다.
  채운 몫의 캐시 쓰기가 5분인지 1시간인지도 모른다. 파일럿에서 Opus의 채운 캐시 쓰기를 1시간으로
  셈하면 `costUSD`보다 0.0011~0.0287달러 많았고 5분으로 셈하면 맞았다.
- `modelUsage`가 없는 세션(러너가 끈 호출만 있는 세션)은 채우지 못해 응답 셈만 남고, 그만큼 낮다.
- 그 프로브 원본(stream-json)에 이 셈을 대면 결과 이벤트의 `total_cost_usd`와 맞지 않았다(셀프
  리뷰의 두 서브에이전트가 손으로 대 0.03766과 0.03946을 봤다). 그때는 `modelUsage`를 넘기지 않았다.
- Haiku의 대신 셈은 응답마다의 프롬프트 크기를 몰라 10만 토큰 이하의 단가로 셈한다. 긴 세션이면
  실제보다 싸다(명세 2026-10-22 주석). 응답이 있는 Haiku의 채운 몫도 같은 까닭으로 10만 토큰 이하의
  단가이고, 채운 몫은 `substitutes`에 들지 않아 판정 출력의 대신 셈 수에도 들지 않는다. 프롬프트
  크기로 단가가 갈리는 모델은 Haiku뿐이라 Opus·Sonnet의 채운 몫은 단가가 갈리지 않는다.
- 웹 검색 요금과 그 밖의 서버 도구 요금은 셈하지 않는다.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from tools.rerun_files import ModelUsage, Substitute, Tokens

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


@dataclass(frozen=True)
class Price:
    """달러/백만 토큰."""

    input: float
    output: float
    cache_read: float


# `docs/model-selection.md` 2절 "모델" 표(2026-10-13 원문 대조)를 2026-10-23에 옮겼다. Haiku 5.5는
# 프롬프트 10만 토큰 이하의 값이고, 넘으면 `HAIKU_LONG_PRICE`다.
PRICES: dict[str, Price] = {
    "claude-fable-5-1": Price(10.0, 50.0, 0.25),
    "claude-opus-5-5": Price(4.0, 20.0, 0.20),
    "claude-sonnet-5-5": Price(2.0, 10.0, 0.10),
    "claude-haiku-5-5": Price(0.10, 0.50, 0.01),
}
HAIKU = "claude-haiku-5-5"
HAIKU_LONG_PRICE = Price(0.50, 2.50, 0.05)
HAIKU_LONG_PROMPT = 100_000  # 이 토큰 수를 넘는 프롬프트가 높은 단가다
# 캐시 쓰기의 배수(입력 단가에 곱한다). 명세 "회차 기록"의 공식 단가 셈 문단이다.
WRITE_5M = 1.25
WRITE_1H = 2.0

_DATE_TAIL = re.compile(r"-[0-9]{8}$")
_WIDE_TAIL = "[1m]"
_SYNTHETIC = "<synthetic>"


class PriceError(ValueError):
    """단가가 없는 모델."""


@dataclass(frozen=True)
class Cost:
    """세션 하나나 회차의 공식 단가 셈."""

    official_usd: float
    tokens: Tokens  # 응답 셈과 채운 몫의 합. 생각은 늘 빈 값이다(모듈 독스트링 못 보는 것)
    substitutes: tuple[Substitute, ...]  # `modelUsage`로 대신 셈한 모델과 그 토큰


def _canonical(model: str) -> str:
    """끝의 `[1m]`과 날짜를 뗀 이름."""
    return _DATE_TAIL.sub("", model.removesuffix(_WIDE_TAIL))


def _price(model: str) -> Price:
    price = PRICES.get(model)
    if price is None:
        raise PriceError(f"공식 단가가 없는 모델이다: {model}")
    return price


def _obj(v: Json) -> dict[str, Json]:
    return v if isinstance(v, dict) else {}


def _int(v: Json) -> int:
    return v if isinstance(v, int) and not isinstance(v, bool) else 0


def _str(v: Json) -> str | None:
    return v if isinstance(v, str) else None


def _parse(line: str) -> Json:
    # `json.loads`의 반환형은 Any라 여기서 `Json`으로 받는다(`tools/token_report.py`와 같다).
    return json.loads(line)


@dataclass
class _Response:
    model: str
    usage: dict[str, Json]


def _responses(lines: Iterable[str]) -> list[_Response]:
    """응답마다 첫 줄의 모델과 출력 토큰이 가장 큰 usage. 처음 나온 차례다."""
    found: dict[str, _Response] = {}
    for index, line in enumerate(lines):
        try:
            d = _parse(line)
        except ValueError:
            continue
        if not isinstance(d, dict) or d.get("type") != "assistant":
            continue
        m = _obj(d.get("message"))
        usage = m.get("usage")
        model = _str(m.get("model"))
        if not isinstance(usage, dict) or model == _SYNTHETIC:
            continue
        if model is None:
            raise PriceError(f"모델이 없는 응답이다(기록 줄 {index + 1})")
        key = _str(m.get("id")) or _str(d.get("uuid")) or f"#{index}"
        seen = found.get(key)
        if seen is None:
            found[key] = _Response(model, usage)
        elif _int(usage.get("output_tokens")) > _int(seen.usage.get("output_tokens")):
            seen.usage = usage
    return list(found.values())


def _cache_writes(usage: dict[str, Json]) -> tuple[int, int]:
    """(5분 몫, 1시간 몫). 나눈 합이 캐시 쓰기 합과 맞지 않으면 남는 몫을 5분으로 본다."""
    total = _int(usage.get("cache_creation_input_tokens"))
    split = _obj(usage.get("cache_creation"))
    w5 = _int(split.get("ephemeral_5m_input_tokens"))
    w1 = _int(split.get("ephemeral_1h_input_tokens"))
    if w5 + w1 != total:
        w1 = min(w1, total)
        w5 = total - w1
    return w5, w1


def _usd(price: Price, input: int, output: int, read: int, w5: int, w1: int) -> float:
    return (
        input * price.input
        + output * price.output
        + read * price.cache_read
        + w5 * price.input * WRITE_5M
        + w1 * price.input * WRITE_1H
    ) / 1e6


def _add(a: int | None, b: int | None) -> int | None:
    return None if a is None or b is None else a + b


def _add_tokens(a: Tokens, b: Tokens) -> Tokens:
    return Tokens(
        input=_add(a.input, b.input),
        output=_add(a.output, b.output),
        cache_read=_add(a.cache_read, b.cache_read),
        cache_write=_add(a.cache_write, b.cache_write),
        thinking=_add(a.thinking, b.thinking),
    )


def cost_of(lines: Iterable[str], model_usage: Sequence[ModelUsage]) -> Cost:
    """세션 하나의 기록 줄과 그 세션의 마지막 `modelUsage`의 공식 단가 셈."""
    usd = 0.0
    input = output = read = write = 0
    seen: dict[str, list[int]] = {}  # 모델마다 응답 셈의 입력, 출력, 캐시 읽기, 캐시 쓰기
    for r in _responses(lines):
        model = _canonical(r.model)
        price = _price(model)
        w5, w1 = _cache_writes(r.usage)
        i = _int(r.usage.get("input_tokens"))
        o = _int(r.usage.get("output_tokens"))
        c = _int(r.usage.get("cache_read_input_tokens"))
        if model == HAIKU and i + c + w5 + w1 > HAIKU_LONG_PROMPT:
            price = HAIKU_LONG_PRICE
        usd += _usd(price, i, o, c, w5, w1)
        input, output, read, write = input + i, output + o, read + c, write + w5 + w1
        got = seen.setdefault(model, [0, 0, 0, 0])
        got[0], got[1], got[2], got[3] = got[0] + i, got[1] + o, got[2] + c, got[3] + w5 + w1
    # 응답이 있는 모델은 `modelUsage`(꼬리만 다른 이름은 더한다)보다 모자란 칸을 채운다
    for model, gap in _gaps(seen, model_usage):
        usd += _usd(_price(model), *gap, 0)
        input, output, read, write = (
            input + gap[0],
            output + gap[1],
            read + gap[2],
            write + gap[3],
        )
    # 기록에 응답이 없는 모델만 `modelUsage`로 대신 셈하고, 응답 셈과 같은 누산기에 차례로 더한다.
    # 대신 셈의 합을 따로 구해 더하면 부동소수점 더하기의 차례가 바뀌어 값이 달라질 수 있다
    absent = [u for u in model_usage if _canonical(u.model) not in seen]
    for u in absent:
        usd += _substitute_usd(u)
    tokens = Tokens(input=input, output=output, cache_read=read, cache_write=write, thinking=None)
    substitutes = _merge_substitutes(_substitute(u) for u in absent)
    return Cost(official_usd=usd, tokens=tokens, substitutes=substitutes)


def _gaps(
    seen: dict[str, list[int]], model_usage: Sequence[ModelUsage]
) -> list[tuple[str, tuple[int, int, int, int]]]:
    """응답이 있는 모델마다 `modelUsage`가 응답 셈보다 많은 몫(입력, 출력, 캐시 읽기, 캐시 쓰기).
    응답 셈이 많은 칸은 0이다. 모델은 `modelUsage`에 처음 나온 차례다."""
    totals: dict[str, list[int]] = {}
    for u in model_usage:
        model = _canonical(u.model)
        if model not in seen:
            continue
        t = totals.setdefault(model, [0, 0, 0, 0])
        t[0] += u.input_tokens
        t[1] += u.output_tokens
        t[2] += u.cache_read_tokens
        t[3] += u.cache_write_tokens
    gaps: list[tuple[str, tuple[int, int, int, int]]] = []
    for model, t in totals.items():
        s = seen[model]
        gap = (
            max(0, t[0] - s[0]),
            max(0, t[1] - s[1]),
            max(0, t[2] - s[2]),
            max(0, t[3] - s[3]),
        )
        if any(gap):
            gaps.append((model, gap))
    return gaps


def _substitute_usd(u: ModelUsage) -> float:
    """`modelUsage` 하나의 대신 셈 금액. 캐시 쓰기는 모두 5분 배수로 셈한다."""
    return _usd(
        _price(_canonical(u.model)),
        u.input_tokens,
        u.output_tokens,
        u.cache_read_tokens,
        u.cache_write_tokens,
        0,
    )


def _substitute(u: ModelUsage) -> Substitute:
    """`modelUsage` 하나를 대신 셈한 모델과 그 토큰으로 옮긴다."""
    tokens = Tokens(
        input=u.input_tokens,
        output=u.output_tokens,
        cache_read=u.cache_read_tokens,
        cache_write=u.cache_write_tokens,
        thinking=u.thinking_tokens,
    )
    return Substitute(model=_canonical(u.model), tokens=tokens)


def _merge_substitutes(substitutes: Iterable[Substitute]) -> tuple[Substitute, ...]:
    """같은 모델의 토큰을 처음 나온 자리에 한 항목으로 더한다."""
    merged: dict[str, Tokens] = {}
    for s in substitutes:
        before = merged.get(s.model)
        merged[s.model] = s.tokens if before is None else _add_tokens(before, s.tokens)
    return tuple(Substitute(model=m, tokens=t) for m, t in merged.items())


def round_cost(costs: Iterable[Cost]) -> Cost:
    """세션마다의 셈을 더한 회차의 셈. 대신 셈한 같은 모델은 처음 나온 자리에 한 항목으로 더한다.
    어느 쪽이든 빈 토큰 칸이 있으면 그 칸의 합은 빈 값이다."""
    usd = 0.0
    tokens = Tokens(input=0, output=0, cache_read=0, cache_write=0, thinking=None)
    substitutes: list[Substitute] = []
    for c in costs:
        usd += c.official_usd
        tokens = _add_tokens(tokens, c.tokens)
        substitutes += c.substitutes
    return Cost(official_usd=usd, tokens=tokens, substitutes=_merge_substitutes(substitutes))


def transcript_lines(transcript: Path) -> list[str]:
    """본 세션 기록 파일과 그 `subagents/`의 기록 파일(이름 차례)의 줄."""
    files = [transcript, *sorted((transcript.with_suffix("") / "subagents").glob("*.jsonl"))]
    lines: list[str] = []
    for path in files:
        # `splitlines`는 Node 가 이스케이프하지 않은 글 안의 U+2028 에서도 가른다
        lines += path.read_text(encoding="utf-8", errors="replace").split("\n")
    return lines


def session_cost(transcript: Path, model_usage: Sequence[ModelUsage]) -> Cost:
    """세션 하나(본 세션 기록 파일 `transcript`와 그 `subagents/`)의 공식 단가 셈."""
    return cost_of(transcript_lines(transcript), model_usage)
