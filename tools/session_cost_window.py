"""소급 측정 `collect.py --since`의 창. 무엇을 창과 관계없이 보고 무엇을 창 안에서만 세는지를
정한다.

레벨 스윕의 판정(`tools/model_sweep_judge.py`)은 `collect.py --since <스윕 시작>`이 쓴
`branches.json`을 읽는다. 그 창은 판정이 2026-12-15 뒤에 한 번 돌아 그 전에 회귀를 잡을 자리가
없었다. 그래서 PR #224가 판정 함수를 옮긴 뒤 이 창도 프로브에서 옮겨
`tests/tools/test_session_cost_window.py`로 고정했다(PR #220 claude-review 셋째 회차 답글, 일지
2026-10-13-42 "다음"). 이 파일은 턴의 머리(`TurnHead`)와 시각만 받는 순수 함수다.

이 파일이 정하는 것:
- 창 안인가(`in_window`, 창의 시작 시각을 들인다)와 창 값 읽기(`parse_since`).
- 브랜치의 첫 사람 트리거(`first_humans`)는 창과 관계없이 본다. 그 시각과 글은 표지 모집단과
  배정(`모델:`·`브랜치:` 줄)의 재료라 창 앞 기록까지 본다(PR #220 CodeRabbit). 그래서 창 앞에서
  시작한 브랜치는 첫 트리거가 창 앞이다.
- 첫 지시문의 시각(`first_directive`)은 창 안에서 시작한 턴만 보고, 귀속하지 못한 턴도 본다.
- 사람 개입의 지시문 아닌 메시지(`human_nondirective`)는 창 안에서 시작한 사람 턴이고, 브랜치의 첫
  사람 트리거가 지시문이 아니면 과제 진술이라 하나를 뺀다. 그 첫 트리거가 창 앞이면 처음부터 세지
  않았으므로 빼지 않는다.
- 시각이 없는 `cost-state`는 창 안에 기록이나 응답이 있는 세션의 것만 남긴다(`cost_state_sessions`).
  그 세션의 창 앞 몫까지 드는 것은 `collect.py` 독스트링이 적는다.

`collect.py`에 남은 것: 기록 읽기, 턴 짓기와 브랜치 귀속(창과 관계없이), 그리고 `in_window`를 어느
시각에 거는지다. 턴과 그 안의 표지는 턴의 시작 시각으로, 응답의 비용은 응답 시각으로 창에 걸고,
`cost-state` 대조에 쓰는 세션 비용은 창 없이 더한다. 그 자리는 pytest가 아니라 옮기기 전후의
`branches.json` 비교로만 봤다(일지 2026-10-13-51).

못 보는 것: 턴은 시작 시각 하나로 창에 넣거나 빼므로 창 경계에 걸친 턴은 통째로 창 안이나 밖이다.
턴 안 응답의 비용은 응답 시각으로 따로 가르므로, 창 앞에서 시작한 턴의 창 안 응답은 비용에 들고 턴
수와 시간에는 들지 않는다. 지시문은 사람 트리거이고 글에 `다음 작업:`이 드는 턴이다(`collect.py`의
`DIRECTIVE_MARK`와 같다). 글의 다른 표지는 보지 않는다.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

DIRECTIVE_MARK = "다음 작업:"


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_since(value: str | None) -> datetime | None:
    """`--since` 값. 비었으면 창이 없다. 시각대 없는 값은 UTC로 본다. 그대로 두면 기록의 aware
    시각과 견줄 때 TypeError가 난다."""
    if not value:
        return None
    since = parse_ts(value)
    return since.replace(tzinfo=UTC) if since.tzinfo is None else since


def in_window(ts: str, since: datetime | None) -> bool:
    return since is None or parse_ts(ts) >= since


@dataclass(frozen=True)
class TurnHead:
    """턴 하나의 머리. `branch`가 비면 귀속하지 못한 턴이다. `trigger`는 `collect.py`의 `turns_of`가
    넣는 넷 가운데 하나다. `human`·`auto`·`interrupt`는 턴을 연 기록의 `classify_trigger` 값이고,
    `start`는 세션의 첫 기록이 트리거가 아니어서 트리거 없이 연 첫 턴이다. 이 파일은 `human`만
    가리고 나머지는 같게 다룬다."""

    start: str
    branch: str
    trigger: str
    text: str

    @property
    def directive(self) -> bool:
        return self.trigger == "human" and DIRECTIVE_MARK in self.text


def first_humans(turns: Iterable[TurnHead]) -> dict[str, tuple[str, str]]:
    """브랜치마다 가장 이른 사람 트리거 턴의 (시작, 글). 창과 관계없이 본다. 시작이 같으면 앞에 온
    턴이다."""
    firsts: dict[str, tuple[str, str]] = {}
    for t in turns:
        if not t.branch or t.trigger != "human":
            continue
        old = firsts.get(t.branch)
        if old is None or t.start < old[0]:
            firsts[t.branch] = (t.start, t.text)
    return firsts


def first_directive(turns: Iterable[TurnHead], since: datetime | None) -> str:
    """창 안에서 시작한 지시문 턴 가운데 가장 이른 것의 시작. 귀속하지 못한 턴도 본다. 없으면 빈
    문자열이다."""
    starts = [t.start for t in turns if t.directive and in_window(t.start, since)]
    return min(starts, default="")


def human_nondirective(
    turns: Iterable[TurnHead], first: tuple[str, str] | None, since: datetime | None
) -> int:
    """한 브랜치의 사람 개입 가운데 지시문 아닌 사람 메시지 수. `turns`는 그 브랜치의 턴이고
    `first`는 그 브랜치의 첫 사람 트리거(`first_humans`)다."""
    n = sum(
        1 for t in turns if t.trigger == "human" and not t.directive and in_window(t.start, since)
    )
    if first is not None and DIRECTIVE_MARK not in first[1] and in_window(first[0], since):
        n -= 1
    return max(0, n)


def cost_state_sessions(
    sessions: Iterable[str], stamps: Mapping[str, Iterable[str]], since: datetime | None
) -> set[str]:
    """`cost-state`를 남길 세션. `stamps`는 세션마다 기록과 응답의 시각이다. 창이 없으면 모두
    남긴다."""
    if since is None:
        return set(sessions)
    return {sid for sid in sessions if any(in_window(ts, since) for ts in stamps.get(sid, ()))}
