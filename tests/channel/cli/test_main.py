"""CLI 인자. run 하위 명령의 위치 인자 둘과 옵션 셋."""

from pathlib import Path

import pytest

from agent_os.channel.cli.main import DEFAULT_TRACES, parse_run_args


def test_실행_명령은_에이전트_이름과_요청을_위치_인자로_받는다() -> None:
    args = parse_run_args(["run", "calc", "2+2?"])

    assert args.agent == "calc"
    assert args.request == "2+2?"
    assert args.model is None
    assert args.traces == DEFAULT_TRACES
    assert args.verbose is False


def test_옵션_셋은_모델_진행_표시_트레이스_디렉터리다() -> None:
    args = parse_run_args(["run", "calc", "hi", "--model", "m", "--verbose", "--traces", "out"])

    assert args.model == "m"
    assert args.verbose is True
    assert args.traces == Path("out")


def test_하위_명령이_없으면_거부한다() -> None:
    with pytest.raises(SystemExit):
        parse_run_args([])
