"""CLI 인자. 하위 명령 둘, run 과 resume."""

from pathlib import Path

import pytest

from agent_os.channel.cli.main import DEFAULT_TRACES, ResumeArgs, RunArgs, parse_args
from agent_os.core.run import Approve, Deny


def test_실행_명령은_에이전트_이름과_요청을_위치_인자로_받는다() -> None:
    args = parse_args(["run", "calc", "2+2?"])

    assert isinstance(args, RunArgs)
    assert args.agent == "calc"
    assert args.request == "2+2?"
    assert args.model is None
    assert args.traces == DEFAULT_TRACES
    assert args.verbose is False


def test_옵션_셋은_모델_진행_표시_트레이스_디렉터리다() -> None:
    args = parse_args(["run", "calc", "hi", "--model", "m", "--verbose", "--traces", "out"])

    assert isinstance(args, RunArgs)
    assert args.model == "m"
    assert args.verbose is True
    assert args.traces == Path("out")


def test_하위_명령이_없으면_거부한다() -> None:
    with pytest.raises(SystemExit):
        parse_args([])


def test_재개_명령은_실행_식별자_하나만_있으면_된다() -> None:
    """멈춘 실행을 다시 찾아가는 일이 쉬워야 한다. 에이전트도 요청도 트레이스가 안다."""
    args = parse_args(["resume", "run-1", "--approve"])

    assert isinstance(args, ResumeArgs)
    assert args.run_id == "run-1"
    assert args.traces == DEFAULT_TRACES
    assert args.model is None
    assert args.verbose is False


def test_고른_결정이_core_가_받는_값으로_바뀐다() -> None:
    """플래그를 파싱만 하고 버리면 거부가 조용히 승인으로 돈다. 타입이 잡아 주지 않는 자리다."""
    args = parse_args(["resume", "run-1", "--approve"])

    assert isinstance(args, ResumeArgs)
    assert args.decision == Approve()


def test_재개도_모델과_진행_표시와_트레이스_디렉터리를_받는다() -> None:
    """재개는 재생이 끝난 뒤 실제로 이어 가므로 모델이 필요하다."""
    argv = ["resume", "run-1", "--approve", "--model", "m", "--verbose", "--traces", "o"]
    args = parse_args(argv)

    assert isinstance(args, ResumeArgs)
    assert args.model == "m"
    assert args.verbose is True
    assert args.traces == Path("o")


def test_결정을_고르지_않은_재개는_거부한다() -> None:
    """승인 없이 재개하는 길을 두면 승인자 없는 승인이 기본값으로 굳는다."""
    with pytest.raises(SystemExit):
        parse_args(["resume", "run-1"])


def test_거부는_사유와_함께_core_가_받는_값으로_바뀐다() -> None:
    args = parse_args(["resume", "run-1", "--deny", "--reason", "보낼 내용이 아니다"])

    assert isinstance(args, ResumeArgs)
    assert args.decision == Deny(reason="보낼 내용이 아니다")


def test_사유_없는_거부에는_진단을_낸다() -> None:
    """ApprovalDenied.reason 이 필수 필드다. CLI 가 빈 문자열을 지어내면 사유 없는 거부가 굳는다."""
    with pytest.raises(SystemExit):
        parse_args(["resume", "run-1", "--deny"])


def test_공백만_있는_사유도_없는_것으로_보고_진단을_낸다() -> None:
    with pytest.raises(SystemExit):
        parse_args(["resume", "run-1", "--deny", "--reason", "   "])


def test_승인과_거부를_둘_다_주면_진단을_낸다() -> None:
    with pytest.raises(SystemExit):
        parse_args(["resume", "run-1", "--approve", "--deny", "--reason", "x"])


def test_사유는_거부에만_쓴다() -> None:
    """승인에는 사유를 담을 자리가 없다. 조용히 버리면 승인자가 적은 말이 사라진다."""
    with pytest.raises(SystemExit):
        parse_args(["resume", "run-1", "--approve", "--reason", "좋다"])
