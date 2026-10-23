"""`tools/rerun_cost.py`: 다시 풀기 회차의 공식 단가 셈.

티켓은 `.scratch/model-rerun/issues/07-gates-and-official-cost.md`의 "공식 단가"다. 세션 기록 줄은
사용량 장부(`tools/token_report.py`의 `read_stream`)가 읽는 꼴(`type`이 `assistant`인 줄의
`message.id`·`message.model`·`message.usage`)로 짓고, 그 꼴의 칸 이름은 커밋한 프로브 원본
`서브-2.jsonl`로 한 번 대 본다.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from tools.rerun_cost import (
    HAIKU_LONG_PRICE,
    HAIKU_LONG_PROMPT,
    PRICES,
    WRITE_1H,
    WRITE_5M,
    Cost,
    Price,
    PriceError,
    cost_of,
    round_cost,
    session_cost,
)
from tools.rerun_files import ModelUsage, Substitute, Tokens

ROOT = Path(__file__).resolve().parents[2]
PROBE_STREAM = ROOT / ".scratch/model-rerun/probes/headless_flags/2026-10-22/서브-2.jsonl"

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
HAIKU = "claude-haiku-5-5"


def _응답(
    mid: str | None,
    model: str,
    *,
    input: int = 0,
    output: int = 0,
    read: int = 0,
    w5: int = 0,
    w1: int = 0,
    total: int | None = None,
    uuid: str | None = None,
) -> str:
    """세션 기록 파일의 assistant 줄 하나. `total`을 주면 캐시 쓰기 합을 나눈 몫과 다르게 둔다."""
    message: dict[str, object] = {
        "model": model,
        "usage": {
            "input_tokens": input,
            "output_tokens": output,
            "cache_read_input_tokens": read,
            "cache_creation_input_tokens": w5 + w1 if total is None else total,
            "cache_creation": {
                "ephemeral_5m_input_tokens": w5,
                "ephemeral_1h_input_tokens": w1,
            },
        },
    }
    if mid is not None:
        message["id"] = mid
    line: dict[str, object] = {"type": "assistant", "message": message, "effort": "high"}
    if uuid is not None:
        line["uuid"] = uuid
    return json.dumps(line)


def _usd(
    price: Price, *, input: int = 0, output: int = 0, read: int = 0, w5: int = 0, w1: int = 0
) -> float:
    """시험이 따로 적은 공식 단가 셈. 캐시 쓰기는 5분과 1시간 배수다."""
    return (
        input * price.input
        + output * price.output
        + read * price.cache_read
        + w5 * price.input * WRITE_5M
        + w1 * price.input * WRITE_1H
    ) / 1e6


def test_단가는_model_selection_2절의_표다() -> None:
    """옮긴 값을 한 번 적어 둔다. 문서와 묶지는 않는다(티켓 "단가 상수")."""
    assert PRICES == {
        "claude-fable-5-1": Price(10.0, 50.0, 0.25),
        OPUS: Price(4.0, 20.0, 0.20),
        SONNET: Price(2.0, 10.0, 0.10),
        HAIKU: Price(0.10, 0.50, 0.01),
    }
    assert HAIKU_LONG_PRICE == Price(0.50, 2.50, 0.05)
    assert HAIKU_LONG_PROMPT == 100_000
    assert (WRITE_5M, WRITE_1H) == (1.25, 2.0)


def test_응답마다_입력_출력_캐시_읽기와_5분_1시간_캐시_쓰기를_셈한다() -> None:
    줄 = [
        _응답("m1", OPUS, input=10, output=200, read=3000, w5=400, w1=0),
        _응답("m2", OPUS, input=5, output=100, read=0, w5=0, w1=700),
        _응답("m3", OPUS, input=1, output=1, read=1, w5=50, w1=60),
    ]
    got = cost_of(줄, ())
    want = (
        _usd(PRICES[OPUS], input=10, output=200, read=3000, w5=400)
        + _usd(PRICES[OPUS], input=5, output=100, w1=700)
        + _usd(PRICES[OPUS], input=1, output=1, read=1, w5=50, w1=60)
    )
    assert math.isclose(got.official_usd, want, rel_tol=1e-12)
    assert got.tokens == Tokens(
        input=16, output=301, cache_read=3001, cache_write=1210, thinking=None
    )
    assert got.substitutes == ()


def test_같은_message_id_의_줄은_한_번만_세고_출력이_가장_큰_usage_를_쓴다() -> None:
    줄 = [
        _응답("m1", SONNET, input=3, output=5, read=100, w1=20),
        _응답("m1", SONNET, input=3, output=90, read=100, w1=20),
        _응답("m1", SONNET, input=3, output=40, read=100, w1=20),
    ]
    got = cost_of(줄, ())
    assert math.isclose(
        got.official_usd, _usd(PRICES[SONNET], input=3, output=90, read=100, w1=20), rel_tol=1e-12
    )
    assert got.tokens == Tokens(input=3, output=90, cache_read=100, cache_write=20, thinking=None)


def test_id_가_없는_응답은_uuid_로_가르고_둘_다_없으면_줄마다_센다() -> None:
    줄 = [
        _응답(None, SONNET, output=10, uuid="u1"),
        _응답(None, SONNET, output=20, uuid="u1"),
        _응답(None, SONNET, output=7),
        _응답(None, SONNET, output=7),
    ]
    assert cost_of(줄, ()).tokens.output == 20 + 7 + 7


def test_나눈_캐시_쓰기의_합이_맞지_않으면_남는_몫을_5분으로_본다() -> None:
    """장부의 `_cache_writes`와 같은 셈이다. 1시간 몫이 합보다 크면 합으로 자른다."""
    모자람 = cost_of([_응답("m1", OPUS, w5=0, w1=300, total=1000)], ())
    assert math.isclose(모자람.official_usd, _usd(PRICES[OPUS], w5=700, w1=300), rel_tol=1e-12)
    assert 모자람.tokens.cache_write == 1000
    넘침 = cost_of([_응답("m1", OPUS, w5=500, w1=900, total=600)], ())
    assert math.isclose(넘침.official_usd, _usd(PRICES[OPUS], w1=600), rel_tol=1e-12)
    assert 넘침.tokens.cache_write == 600
    갈래_없음 = json.dumps(
        {
            "type": "assistant",
            "message": {
                "id": "m9",
                "model": OPUS,
                "usage": {"input_tokens": 1, "output_tokens": 1, "cache_creation_input_tokens": 80},
            },
        }
    )
    got = cost_of([갈래_없음], ())
    assert math.isclose(got.official_usd, _usd(PRICES[OPUS], input=1, output=1, w5=80))


@pytest.mark.parametrize(
    ("input", "read", "w5", "w1", "price"),
    [
        (0, 99_999, 0, 0, PRICES[HAIKU]),
        (1, 90_000, 9_999, 0, PRICES[HAIKU]),
        (0, 50_000, 25_000, 25_000, PRICES[HAIKU]),
        (1, 100_000, 0, 0, HAIKU_LONG_PRICE),
        (2, 50_000, 30_000, 20_000, HAIKU_LONG_PRICE),
    ],
)
def test_Haiku_는_응답의_프롬프트가_10만_토큰을_넘으면_높은_단가다(
    input: int, read: int, w5: int, w1: int, price: Price
) -> None:
    got = cost_of([_응답("h", HAIKU, input=input, output=30, read=read, w5=w5, w1=w1)], ())
    want = _usd(price, input=input, output=30, read=read, w5=w5, w1=w1)
    assert math.isclose(got.official_usd, want, rel_tol=1e-12)


def test_Haiku_의_단가는_응답마다_가른다() -> None:
    작은 = _응답("h1", HAIKU, input=10, output=5, read=1_000)
    큰 = _응답("h2", HAIKU, input=10, output=5, read=150_000)
    got = cost_of([작은, 큰], ())
    want = _usd(PRICES[HAIKU], input=10, output=5, read=1_000) + _usd(
        HAIKU_LONG_PRICE, input=10, output=5, read=150_000
    )
    assert math.isclose(got.official_usd, want, rel_tol=1e-12)


def test_synthetic_과_assistant_밖의_줄과_풀지_못한_줄은_세지_않는다() -> None:
    synthetic = json.dumps(
        {
            "type": "assistant",
            "message": {
                "id": "s",
                "model": "<synthetic>",
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        }
    )
    사용자 = json.dumps({"type": "user", "message": {"id": "u", "usage": {"input_tokens": 9}}})
    usage_없음 = json.dumps({"type": "assistant", "message": {"id": "x", "model": OPUS}})
    줄 = [synthetic, 사용자, usage_없음, "{깨진 줄", "", _응답("m", OPUS, output=1)]
    got = cost_of(줄, ())
    assert got.tokens == Tokens(input=0, output=1, cache_read=0, cache_write=0, thinking=None)
    assert math.isclose(got.official_usd, _usd(PRICES[OPUS], output=1), rel_tol=1e-12)


def test_날짜나_1m_꼬리가_붙은_이름은_떼고_단가를_찾는다() -> None:
    got = cost_of(
        [
            _응답("a", f"{SONNET}-20261001", output=10),
            _응답("b", f"{OPUS}[1m]", output=10),
        ],
        (),
    )
    want = _usd(PRICES[SONNET], output=10) + _usd(PRICES[OPUS], output=10)
    assert math.isclose(got.official_usd, want, rel_tol=1e-12)


def test_단가가_없는_모델은_PriceError_다() -> None:
    with pytest.raises(PriceError, match="claude-unknown-9"):
        cost_of([_응답("a", "claude-unknown-9", output=1)], ())
    with pytest.raises(PriceError, match="claude-unknown-9"):
        cost_of((), (_사용("claude-unknown-9", output=1),))


def test_모델이_없는_응답은_빼지_않고_PriceError_다() -> None:
    """빼면 그 응답의 비용이 셈에서 빠져 낮게 나온다. 장부는 그런 줄을 `(모름)`으로 센다."""
    모델_없음 = json.dumps(
        {"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": 1_000_000}}}
    )
    with pytest.raises(PriceError, match="모델이 없는 응답"):
        cost_of([모델_없음, _응답("m", OPUS, output=1)], ())


def _사용(
    model: str,
    *,
    input: int = 0,
    output: int = 0,
    read: int = 0,
    write: int = 0,
    thinking: int | None = None,
) -> ModelUsage:
    return ModelUsage(
        model=model,
        input_tokens=input,
        output_tokens=output,
        cache_read_tokens=read,
        cache_write_tokens=write,
        thinking_tokens=thinking,
        cost_usd=0.5,
    )


def test_기록에_응답이_없는_모델은_modelUsage_를_5분_배수로_대신_셈하고_따로_적는다() -> None:
    """Haiku 의 대신 셈은 응답마다의 크기를 몰라 10만 토큰 이하의 단가로 셈한다(명세 주석)."""
    줄 = [_응답("m1", SONNET, input=2, output=10, read=50, w1=30)]
    사용 = (
        _사용(SONNET, input=2, output=999, read=50, write=30, thinking=0),
        _사용(HAIKU, input=4, output=231, read=150_000, write=16_332, thinking=88),
    )
    got = cost_of(줄, 사용)
    want = _usd(PRICES[SONNET], input=2, output=10, read=50, w1=30) + _usd(
        PRICES[HAIKU], input=4, output=231, read=150_000, w5=16_332
    )
    assert math.isclose(got.official_usd, want, rel_tol=1e-12)
    assert got.substitutes == (
        Substitute(
            model=HAIKU,
            tokens=Tokens(input=4, output=231, cache_read=150_000, cache_write=16_332, thinking=88),
        ),
    )
    # 토큰 합은 응답 셈에서만 낸다. 대신 셈한 몫은 `substitutes`에만 든다.
    assert got.tokens == Tokens(input=2, output=10, cache_read=50, cache_write=30, thinking=None)


def test_modelUsage_의_1m_꼬리는_기록의_이름과_같은_모델로_본다() -> None:
    got = cost_of([_응답("m1", OPUS, output=1)], (_사용(f"{OPUS}[1m]", output=500),))
    assert got.substitutes == ()
    assert math.isclose(got.official_usd, _usd(PRICES[OPUS], output=1), rel_tol=1e-12)


def _기록_파일(folder: Path, name: str, lines: list[str]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8", newline="\n")
    return path


def test_세션_하나는_본_세션_기록과_그_subagents_를_함께_셈한다(tmp_path: Path) -> None:
    프로젝트 = tmp_path / "projects" / "C--clone"
    sid = "8e3768b8-9180-48c4-a7a0-a1c2cb66c726"
    본 = _기록_파일(프로젝트, f"{sid}.jsonl", [_응답("m1", SONNET, input=2, output=16, w1=6039)])
    _기록_파일(
        프로젝트 / sid / "subagents",
        "agent-a1.jsonl",
        [_응답("h1", HAIKU, input=2, output=21, w5=15643), _응답("h1", HAIKU, output=3)],
    )
    _기록_파일(프로젝트 / sid / "subagents", "agent-a2.jsonl", [_응답("h2", HAIKU, output=4)])
    # 다른 세션의 기록과 subagents 밖의 파일은 들지 않는다.
    _기록_파일(프로젝트, "other.jsonl", [_응답("x", OPUS, output=1_000_000)])
    _기록_파일(프로젝트 / sid, "notes.jsonl", [_응답("y", OPUS, output=1_000_000)])

    got = session_cost(본, ())

    want = (
        _usd(PRICES[SONNET], input=2, output=16, w1=6039)
        + _usd(PRICES[HAIKU], input=2, output=21, w5=15643)
        + _usd(PRICES[HAIKU], output=4)
    )
    assert math.isclose(got.official_usd, want, rel_tol=1e-12)
    assert got.tokens == Tokens(input=4, output=41, cache_read=0, cache_write=21682, thinking=None)


def test_subagents_가_없는_세션도_셈한다(tmp_path: Path) -> None:
    본 = _기록_파일(tmp_path, "s.jsonl", [_응답("m1", OPUS, output=3)])
    assert math.isclose(session_cost(본, ()).official_usd, _usd(PRICES[OPUS], output=3))


def test_본_세션_기록_파일이_없으면_FileNotFoundError_다(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        session_cost(tmp_path / "없다.jsonl", ())


def test_회차의_합은_세션마다의_합이다(tmp_path: Path) -> None:
    첫 = _기록_파일(
        tmp_path / "a", "s1.jsonl", [_응답("m1", OPUS, input=3, output=7, read=9, w1=2)]
    )
    둘 = _기록_파일(tmp_path / "b", "s2.jsonl", [_응답("m2", SONNET, input=1, output=5, w5=4)])
    _기록_파일(tmp_path / "b" / "s2" / "subagents", "agent.jsonl", [_응답("h", HAIKU, output=8)])
    셋_사용 = (_사용(HAIKU, input=1, output=2, thinking=3),)
    셋 = _기록_파일(tmp_path / "c", "s3.jsonl", [_응답("m3", OPUS, output=1)])
    # 날짜 꼬리가 붙은 이름도 같은 모델이라 단가를 찾은 이름으로 적고 하나로 더한다.
    넷_사용 = (_사용(f"{HAIKU}-20261001", input=10, output=20, thinking=None),)
    넷 = _기록_파일(tmp_path / "d", "s4.jsonl", [_응답("m4", OPUS, output=2)])

    하나씩 = [
        session_cost(첫, ()),
        session_cost(둘, ()),
        session_cost(셋, 셋_사용),
        session_cost(넷, 넷_사용),
    ]
    got = round_cost(하나씩)

    assert math.isclose(got.official_usd, sum(c.official_usd for c in 하나씩), rel_tol=1e-12)
    assert got.tokens == Tokens(input=4, output=23, cache_read=9, cache_write=6, thinking=None)
    # 대신 셈한 같은 모델은 하나로 더하고, 어느 세션의 생각 토큰이 비면 합도 빈 값이다.
    assert got.substitutes == (
        Substitute(
            model=HAIKU,
            tokens=Tokens(input=11, output=22, cache_read=0, cache_write=0, thinking=None),
        ),
    )
    # 세션 하나만 셈해도 같은 함수로 부른다.
    assert round_cost([하나씩[0]]) == 하나씩[0]


def test_세션이_없는_회차는_0_이다() -> None:
    assert round_cost([]) == Cost(
        official_usd=0.0,
        tokens=Tokens(input=0, output=0, cache_read=0, cache_write=0, thinking=None),
        substitutes=(),
    )


def test_커밋한_프로브_원본의_응답_칸을_읽는다() -> None:
    """`서브-2.jsonl`의 assistant 줄(본 세션 Sonnet 셋, 서브에이전트 Haiku 둘, 그 하나는 두 줄)로
    칸 이름을 대 본다. 원본의 응답 usage 에는 생각 토큰 칸이 없어 생각 합은 빈 값이다. stream 의
    assistant 줄은 출력 토큰이 끝까지 쌓이기 전의 값이라 이 셈은 그 결과 이벤트의 `costUSD`와 맞지
    않는다(그 대조는 세션 기록 파일로 파일럿이 한다)."""
    lines = PROBE_STREAM.read_text(encoding="utf-8").splitlines()
    assert sum(json.loads(line)["type"] == "assistant" for line in lines) == 6, "원본이 바뀌었다"

    got = cost_of(lines, ())

    assert got.tokens == Tokens(
        input=12, output=112, cache_read=77_562, cache_write=23_423, thinking=None
    )
    want = _usd(PRICES[SONNET], input=8, output=88, read=61_919, w1=7_091) + _usd(
        PRICES[HAIKU], input=4, output=24, read=15_643, w5=16_332
    )
    assert math.isclose(got.official_usd, want, rel_tol=1e-12)
