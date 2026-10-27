"""첫 턴 훅과 세션 사용량 훅의 헤드리스 가름 대조.

`tests/tools/test_hook_prompt_directive.py` 에 두지 않는 것은 `KICKOFF.md` 가 새 프로젝트에
`tests/tools/test_hook_*.py` 를 옮기면서 `tools/hook_session_usage.py` 는 옮기지 않기 때문이다.
그 파일이 이 훅을 import 하면 옮긴 프로젝트의 수집이 `ModuleNotFoundError` 로 멈춘다(PR #354
CodeRabbit). 이 파일은 그 글롭 밖이라 옮기지 않는다.
"""

from __future__ import annotations

from pathlib import Path

from tools.hook_prompt_directive import ATTENDED_VAR, HEADLESS_MARKER, is_attended
from tools.hook_session_usage import HEADLESS_MARKER as USAGE_MARKER
from tools.hook_session_usage import SUMMARY_SOURCE as USAGE_SOURCE
from tools.hook_session_usage import shows_summary as usage_shows_summary

TOOLS = Path(__file__).parents[2] / "tools"


def test_헤드리스_가름은_세션_사용량_훅과_같다() -> None:
    """훅은 서로 import 하지 않아 가름을 옮겨 왔다. 값의 갈래마다 두 사본을 대조한다.

    한쪽만 고치면 여기서 빨갛다. 갈래 하나하나의 근거는 tests/tools/test_hook_session_usage.py 다.
    마지막 단언은 두 훅이 같은 변수 이름을 읽는지 본다. 값 대조는 이름을 보지 않고, 그 훅에는 그
    이름의 상수가 없어 소스에서 찾는다.
    """
    values = (None, "", "0", "1", "true")
    for attended in values:
        for marker in values:
            assert is_attended(attended, marker) == usage_shows_summary(
                USAGE_SOURCE, attended, marker
            ), (attended, marker)
    assert HEADLESS_MARKER == USAGE_MARKER
    source = (TOOLS / "hook_session_usage.py").read_text(encoding="utf-8")
    assert f'os.environ.get("{ATTENDED_VAR}")' in source
