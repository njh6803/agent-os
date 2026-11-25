"""경로가 접두사 아래인가. 접두사 비교는 여기 한 곳이다(ADR 0064).

`agent_os.http.paths` 의 사본이다. 두 설치 묶음은 서로를 import 하지 않으므로(독립 계약) 같은 뜻의
비교를 따로 든다. 머리를 다는 자리와 예외 표가 같은 비교를 쓰면, 같은 경로가 한쪽에서는 접두사
아래이고 다른 쪽에서는 아닌 일이 없다.
"""

from __future__ import annotations


def is_under(path: str, prefix: str) -> bool:
    """경로가 접두사 아래인가(질의). 경로 조각 단위로 본다.

    `/widget-settings` 는 `/widget-settings` 와 `/widget-settings/…` 에 걸리고 `/widget-settingsx`
    에는 걸리지 않는다. 문자열 접두사면 이름이 우연히 겹친 경로가 다른 접두사로 넘어간다.
    """
    return path == prefix or path.startswith(f"{prefix}/")
