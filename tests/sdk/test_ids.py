"""식별자 둘의 문자 집합. 이 값들이 파일 경로로 조립되고 HTTP 가 원격 입력으로 바꾼다."""

from uuid import uuid4

from agent_os.sdk import is_plugin_name, is_run_id

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
