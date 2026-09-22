"""식별자 넷. 경계에서 한 번만 감싸고 JSON 형식은 문자열 그대로다(ADR 0008).

NewType이라 런타임 비용이 없고, 실행 식별자 자리에 에이전트 이름을 넣는 실수를 pyright가 잡는다.
런타임 검증이 0이라는 바로 그 성질 때문에 두 식별자의 문자 집합을 아래에 패턴으로 둔다.
"""

from __future__ import annotations

import re
from typing import NewType

RunId = NewType("RunId", str)
AgentName = NewType("AgentName", str)
PluginName = NewType("PluginName", str)
Principal = NewType("Principal", str)

# 플러그인 이름의 문자 집합. 매니페스트의 name 이 이미 이것을 만족한다.
PLUGIN_NAME_PATTERN = r"^[a-z][a-z0-9-]{1,62}$"

# 실행 식별자의 문자 집합. Clock 이 내는 uuid4 를 담는 안전한 집합이고 uuid4 그 자체가 아니다.
# 형식을 어댑터 하나에 묶으면 다른 Clock 구현이 자기 계약을 어기게 된다.
RUN_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"

# 둘이 패턴인 이유는 이 값들이 파일 경로로 조립되고(`plugins/{kind}/{name}/plugin.toml`,
# `traces/{run_id}.jsonl`) HTTP 가 그것을 원격 입력으로 바꾸기 때문이다. `.` 과 경로 구분자를
# 집합에서 빼면 `..` 과 절대 경로가 루트를 벗어나는 길이 함께 막힌다(윈도는 역슬래시도 구분자다).
# 실행 목록이 내는 식별자는 언제나 이것을 만족한다. 만족하지 않는 이름의 트레이스 파일은 런타임이
# 만들 수 없는 것이라 목록에서 빠지고, 되물을 수 없는 식별자가 목록에 실리지 않는다. 매니페스트
# 쪽은 사람이 만드는 디렉터리라 같지 않고 표지로 남는다(`.claude/rules/core.md`).

# `match` 가 아니라 `fullmatch` 인 이유는 파이썬 `re` 의 `$` 가 문자열 끝 *또는 꼬리 개행
# 바로 앞*에서 맞기 때문이다. 같은 상수를 쓰는 pydantic 과 FastAPI 의 정규식 엔진(rust)은
# 끝에서만 맞으므로, `match` 로 두면 판정자가 매니페스트의 `Field(pattern=...)` 보다 느슨해져
# 같은 값에 대해 둘이 다르게 대답한다. 패턴 문자열은 두 엔진이 공유하므로 파이썬 전용인 `\Z` 를
# 넣지 않고 부르는 쪽을 맞춘다.
_PLUGIN_NAME = re.compile(PLUGIN_NAME_PATTERN)
_RUN_ID = re.compile(RUN_ID_PATTERN)


def is_plugin_name(value: str) -> bool:
    """패턴을 만족하는가. 판정이 한 곳인 이유는 어댑터 둘과 라우트가 같은 규칙을 봐야 해서다."""
    return _PLUGIN_NAME.fullmatch(value) is not None


def is_run_id(value: str) -> bool:
    return _RUN_ID.fullmatch(value) is not None
