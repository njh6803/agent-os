"""식별자 둘의 문자 집합. 이 값들이 파일 경로로 조립되고 HTTP 가 원격 입력으로 바꾼다."""

from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from agent_os.sdk import (
    PLUGIN_NAME_PATTERN,
    RUN_ID_PATTERN,
    is_plugin_name,
    is_run_id,
)

# 경로를 벗어나는 모양들. 윈도가 주 환경이라 역슬래시도 구분자이고, 절대 경로는 루트를 지운다 —
# pathlib 의 `/` 는 오른쪽이 절대 경로면 왼쪽을 버린다.
_ESCAPES = (
    "..",
    "../../etc/passwd",
    "..\\..\\windows",
    "a/b",
    "a\\b",
    "/etc/passwd",
    "C:\\windows",
    "\\\\server\\share",
    "a.b",
    "",
    " ",
    "한글",
    # 파이썬 `re` 의 `$` 가 꼬리 개행 앞에서도 맞는다. pydantic 은 같은 패턴으로 이것을 거부하므로,
    # 판정자가 `match` 면 같은 값에 대해 둘이 다르게 대답한다(PR 직전 리뷰 두 축이 실측으로 잡았다).
    "abc\n",
    "a\nb",
    "calc\n",
)


def test_시계가_내는_실행_식별자가_패턴을_만족한다() -> None:
    """Clock 의 uuid4 가 자기 계약을 어기면 목록이 자기가 쓴 파일을 빼게 된다."""
    assert all(is_run_id(str(uuid4())) for _ in range(100))


def test_경로를_벗어나는_모양은_실행_식별자가_아니다() -> None:
    assert [value for value in _ESCAPES if is_run_id(value)] == []


def test_경로를_벗어나는_모양은_플러그인_이름이_아니다() -> None:
    assert [value for value in _ESCAPES if is_plugin_name(value)] == []


def test_실행_식별자는_예순넷까지다() -> None:
    """파일 이름이 터지는 것을 막는다. 상한이 없으면 이름 하나가 경로 길이 제한에 걸린다."""
    assert is_run_id("a" * 64)
    assert not is_run_id("a" * 65)


def test_플러그인_이름은_소문자로_시작하는_두_글자_이상이다() -> None:
    """매니페스트의 name 이 이미 거는 패턴 그대로다. 조회 쪽에도 같은 것을 건다."""
    assert is_plugin_name("calc") and is_plugin_name("my-agent") and is_plugin_name("a1")
    assert not is_plugin_name("MyAgent")
    assert not is_plugin_name("a")
    assert not is_plugin_name("-leading")
    assert not is_plugin_name("1leading")


# 패턴 문자열 하나를 엔진 둘이 읽는다. 파이썬 `re`(판정자)와 rust(pydantic 의 Field, FastAPI 의
# 경로·질의 검증). 규칙은 "판정자는 하나씩"인데 실제로 값을 판정하는 자리가 둘이므로, 그 둘이
# 갈리는 것을 여기서 잡는다. 검사 넷은 코드가 자기 자신과 맞는지만 보고 이 차이를 보지 못한다.
_CANDIDATES = (
    *_ESCAPES,
    "calc",
    "my-agent",
    "a1",
    "MyAgent",
    "a",
    "-leading",
    "1leading",
    str(uuid4()),
    "a" * 64,
    "a" * 65,
    "run-1",
    "under_score",
    "\ttab",
    "sp ace",
    "trailing ",
)


class _Probe(BaseModel):
    """pydantic 이 같은 패턴으로 무엇을 받는지 묻는 자리. 디스크 형식이 아니라 대조용이다."""

    model_config = ConfigDict(frozen=True)

    plugin_name: str = Field(pattern=PLUGIN_NAME_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)


def _accepts(field: str, value: str) -> bool:
    other = {"plugin_name": "calc", "run_id": "run-1"}
    try:
        _Probe.model_validate({**other, field: value})
    except ValidationError:
        return False
    return True


def test_판정자와_pydantic이_같은_값에_같게_답한다() -> None:
    """갈리면 라우트가 받은 값과 어댑터가 판정한 값이 다른 집합이 된다.

    실제로 갈렸던 자리는 파이썬 `re` 의 `$` 다 — 문자열 끝 또는 꼬리 개행 앞에서 맞으므로
    `match` 로 부르면 판정자가 rust 엔진보다 느슨해진다. `fullmatch` 가 그것을 닫는다.
    """
    disagreements = [
        (field, value)
        for field, judge in (("plugin_name", is_plugin_name), ("run_id", is_run_id))
        for value in _CANDIDATES
        if judge(value) != _accepts(field, value)
    ]

    assert disagreements == []
