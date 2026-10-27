"""다시 풀기의 과제 고르기. main의 병합 기록에서 다시 풀 과제의 후보를 찾아 후보 표를 내고, 층과
씨앗으로 파일럿 셋과 본 측정 여덟을 고른다.

근거는 `.scratch/model-rerun/spec.md`의 "과제 고르기"(그 2026-10-22 주석 여섯 포함), "과제 목록의
칸", Testing Decisions의 "과제 고르기와 숨은 시험 가르기"와 티켓
`.scratch/model-rerun/issues/05-task-selection.md`다. 과제 목록의 꼴은 `tools/rerun_files.py`, 숨은
시험 가르기는 `tools/rerun_hidden.py`의 `sort_candidate`다. 회차의 결과는 읽지 않는다.

후보와 조건.
- 후보는 main의 첫 부모 줄의 커밋 M(부모가 하나인 squash 병합 커밋)이 바꾼 티켓
  파일(`.scratch/<slug>/issues/<NN>-*.md`) 가운데, B(M의 부모)의 `Status:` 값이 `done`으로 시작하지
  않고 M의 값이 `done`으로 시작하는 파일이 정확히 하나인 M이다. 그 파일이 푼 티켓이다. 값은
  `tools/check_ticket.py`의 `status_of`(줄 머리가 `Status:`나 `**Status:**`인 첫 줄의 첫 낱말)로
  읽고, B에 없는 파일은 값이 없다. 푼 티켓 파일이 둘 이상인 M은 후보가 아니고 표 끝에 PR 번호(없으면
  M의 해시 앞 여덟 자리)만 적는다.
- 싼 조건은 B에 티켓 파일이 있는지, 파일 이름에 `human-verification`이 드는지, M 제목 끝의 PR
  번호(`(#NNN)`), 브랜치 표에서 `prs`에 그 번호가 든 행이 정확히 하나이고 그 `branch`가
  `feature/`로 시작하는지, 바깥 검증 낱말, PR 앞 비용(`cost` − `cost_post_pr`)이 $70 이하인지다.
  낱말은 B의 티켓 글에서 대소문자를 가리지 않고 찾는다. 후보 표에는 걸린 까닭을 모두 적는다.
- 되살릴 목록(과제 id → 까닭)은 낱말로만 빠진 후보를 되살린다. 파일 이름은 낱말이 아니라 되살리지
  않는다(명세 "바깥 검증"의 주석). 목록의 id가 후보 하나에 맞지 않거나, 낱말에 걸리지 않았거나, 날짜
  밖의 싼 조건으로도 빠진 후보면 `SelectError`다. 날짜는 보지 않는다. 거슬러 채우기가 그 후보에
  닿을지는 숨은 시험을 가른 뒤에야 알고, 닿지 않으면 되살린 후보도 "닿지 않음"으로 빠진다.
- 날짜와 거슬러 채우기. B의 커밋 시각이 `DATE_FLOOR`(KST 2026-10-12 0시) 이후인 후보를 먼저 보고,
  남은 후보가 `MIN_CANDIDATES`보다 적으면 그 앞의 후보를 M의 커밋 시각이 늦은 것부터 하나씩 더한다.
  더한 후보도 모든 조건을 지나야 남는다. 채운 뒤의 후보는 "닿지 않음"으로 적고, 날짜의 까닭 뒤에 싼
  조건의 까닭을 함께 적는다.
- 숨은 시험은 싼 조건을 지난 후보만 `sort` 콜백(실제는 `sort_candidate`)으로 가르고, 파이썬 숨은
  시험이 `MIN_HIDDEN`보다 적거나 가르지 못하면 빠진다.
- 크기 지표는 B의 티켓 글에서 `BACKTICK_PATH`(소급 측정 `collect.py`와 같은 정규식)에 맞는 서로
  다른 파일 경로의 수다.

고르기(명세 "층과 수", "씨앗", "실행 차례").
- 남은 후보를 크기 지표로 정렬한다(동률은 M의 커밋 해시 순).
- 파일럿은 아래 ⌊n/3⌋개를 `SEED_PILOT`으로 섞어 앞에서 셋이다. 고른 차례의 첫째와 둘째의 갈래
  계획은 A 두 번, 셋째는 E 한 번이다(`PILOT_PLANS`).
- 본 측정은 커밋한 파일럿 목록의 과제를 뺀 m개를 아래·가운데 ⌊m/3⌋개(작은·중간 층)와 나머지(큰
  층)로 자르고, 층마다 `SEED_SMALL`·`SEED_MEDIUM`·`SEED_LARGE`로 섞어 셋·셋·둘을 고른다. 실행
  차례는 작은 1, 중간 1, 큰 1, 작은 2, …, 중간 3이고, 차례 i의 갈래 계획은 씨앗 `ARM_SEED_BASE` +
  i로 다섯 갈래를 섞은 것이다. 파일럿 셋은 다시 고르지 않는다.
- 회차 상한은 PR 앞 비용의 `CAP_MULTIPLIER`배와 `CAP_FLOOR_USD` 가운데 큰 값이다(명세 "상한과
  끄기").

두 층이다. 값만 받는 함수(`solved_tickets`, `parse_branches`, `checked_of`, `build_rows`,
`render_table`, `pick_pilot`, `pick_main`)는 git과 pytest를 부르지 않는다. `build_rows`는 숨은 시험
가르기를 `sort` 콜백으로 받아, 거슬러 채우기가 닿은 후보만 부른다. 바깥 층(`list_candidates`,
`main`)이 git을 부르고, 하위 프로세스마다 시간 제한을 둔다. 자식 환경에서
`tools.run_hooks.REPO_LOCATION_VARS`를 벗긴다.

쓰임: `uv run python -m tools.rerun_select {table,pilot,main} --branches <브랜치 표> --table
<후보 표> [--earlier-branches <옛 브랜치 표>] [--revive <되살릴 목록>] [--out <과제 목록>] [--pilot
<파일럿 목록>]`. 숨은 시험 가르기가 후보마다 작업 트리 둘에 준비를 돌려 오래 걸린다.

옛 브랜치 표를 주면 `with_earlier`가 브랜치마다 PR 앞 비용이 큰 쪽의 행을 쓴다. 2026-10-23 에
데스크톱 앱에서 세션 113개가 지워지며 기록 파일도 지워져, 다시 모은 표의 PR 앞 비용이 줄었기
때문이다(파일럿 티켓(11)이 사람과 정했다. 일지 2026-10-27-14).

종료 코드. 0 후보 표(와 목록)를 썼다, 1 후보 표는 썼지만 고를 후보가 모자라 목록을 쓰지 않았다,
2 입력(브랜치 표, 되살릴 목록, 파일럿 목록)이 틀렸거나, 출력 자리에 쓰지 못했거나(고른 값이 과제
목록의 꼴에 맞지 않거나 글이 UTF-8로 바뀌지 않을 때도 든다), git이 실패했다. 출력은 글을 다 짓고
바이트로 바꾼 뒤에야 열어, 꼴 거부나 인코딩 실패로 끝나면 그 자리를 건드리지 않는다. 브랜치 표의
`cost`·`cost_post_pr`은 0 이상의 유한한 수이고 `cost_post_pr`이 `cost`보다 크지 않아야 하며,
`top_model_effort`는 null이거나 비지 않은 글이어야 한다. 출력 자리는 숨은 시험을 가르기 전에 본다.
폴더가 있는지, 그 자리가 폴더가 아닌지, 이미 있는 파일이면 쓸 수 있는지(`os.access`)다.

못 보는 것.
- 푼 티켓은 `Status:` 줄의 값으로만 가린다. 티켓 파일 밖에서 끝난 일(티켓 없는 PR)과 꼬리의
  `(<slug> <NN>)`는 보지 않는다.
- 바깥 검증 낱말은 글자로 찾아 부정문("사진 비교도 CI에 맡긴다")에도 걸린다. 그 거짓 양성은 사람이
  후보 표를 보고 되살릴 목록으로 되살린다. 낱말 목록 밖의 말로 적은 바깥 검증(예: "브라우저로
  본다")은 걸리지 않는다.
- 브랜치 표가 낡았는지는 보지 않는다. 표가 낡아 행이 없는 브랜치는 "브랜치 표에 PR #N 의 행이
  없다"로 빠진다 (명세 "원래 세션의 PR 앞 비용"의 주석. 그래서 수집 도구를 `--refresh`로 다시 돈다).
- 같은 티켓을 푼 M이 둘이면 과제 id가 겹친다. 고를 후보에 겹친 id가 들면 목록을 짓지 않고 알린다.
- 출력 자리의 앞선 검사는 가르기 전의 한 번이라, 그 뒤에 쓸 수 없게 된 자리(그사이 그 자리에 생긴
  폴더)는 가르기가 끝나고 쓰는 때에야 2로 끝나 가른 결과를 잃는다.
- 병합 기록에서 온 slug로 지은 과제 id가 과제 목록의 꼴(`tools/rerun_files.py`의 `_TASK_ID`)에
  맞는지는 미리 보지 않는다. 맞지 않으면(대문자가 든 slug가 그 예다) 목록을 쓰는 때에야 2로 끝난다.
  후보 표는 남지만 표에는 숨은 시험의 수만 들어, 목록을 지으려면 가르기를 다시 돈다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

from tools.check_ticket import status_of
from tools.rerun_files import (
    ARMS,
    LIST_MAIN,
    LIST_PILOT,
    TIER_LARGE,
    TIER_MEDIUM,
    TIER_PILOT,
    TIER_SMALL,
    ShapeError,
    Task,
    TaskList,
    dumps_task_list,
    read_task_list,
)
from tools.run_hooks import REPO_LOCATION_VARS

from tools import rerun_hidden

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None
type Sorter = Callable[[str, str], rerun_hidden.Hidden | rerun_hidden.Failure]

# --- 정의에 드는 상수(명세 "과제 고르기". 파일럿 티켓(11)이 사전 등록 절로 옮긴다) ---

KST = timezone(timedelta(hours=9))
DATE_FLOOR = datetime(2026, 10, 12, tzinfo=KST)
MIN_CANDIDATES = 12
MIN_HIDDEN = 3
COST_LIMIT_USD = 70.0
# `-m llm`은 파일럿 티켓(11)이 사람과 정해 뺐다. 게이트에 들지 않아 점수에 닿지 않는다
EXTERNAL_TERMS = (
    "playwright",
    "pnpm -C web visual",
    "사진 비교",
    "Claude Design",
    "사람이 확인",
)
EXTERNAL_NAME = "human-verification"
BRANCH_PREFIX = "feature/"
# 소급 측정의 크기 지표와 같은 정규식(`.scratch/harness/probes/session_cost/collect.py`, 시험이
# 본다)
BACKTICK_PATH = re.compile(r"`([^`\s]+\.[A-Za-z][A-Za-z0-9]{0,4})`")
SEED_PILOT = 1
SEED_SMALL = 2
SEED_MEDIUM = 3
SEED_LARGE = 4
ARM_SEED_BASE = 100
PILOT_PLANS: tuple[tuple[str, ...], ...] = (("A", "A"), ("A", "A"), ("E",))
MAIN_COUNTS = (3, 3, 2)  # 작은·중간·큰 층에서 고르는 수
CAP_MULTIPLIER = 3.0
CAP_FLOOR_USD = 40.0
# 준비·게이트 명령이 닿는 파일(명세 "층과 수"의 주석). 후보 표에 B마다 있는지 적는다
SETUP_FILES = ("web/package.json", "tools/run_checks.py")

TICKET_PATH = re.compile(r"\.scratch/([^/]+)/issues/([0-9]{2})-[^/]*\.md")
PR_SUFFIX = re.compile(r"\(#([0-9]+)\)$")
DONE = "done"

GIT_TIMEOUT = 120.0


class SelectError(Exception):
    """입력이 틀렸거나 고를 수 없다. 까닭은 사람이 읽는 글이다."""


# --- 푼 티켓 ---


@dataclass(frozen=True)
class TicketChange:
    """M이 바꾼 티켓 파일 하나. 값은 `Status:` 줄의 첫 낱말이고, 그 커밋에 파일이 없으면
    None이다."""

    path: str
    base_status: str | None
    merge_status: str | None


def _done(status: str | None) -> bool:
    return status is not None and status.startswith(DONE)


def solved_tickets(changes: Sequence[TicketChange]) -> tuple[str, ...]:
    """B에서 `done`이 아니고 M에서 `done`인 티켓 파일. 받은 차례다."""
    return tuple(c.path for c in changes if _done(c.merge_status) and not _done(c.base_status))


def task_id_of(ticket: str) -> str:
    """티켓 경로의 과제 id(`<slug>-<NN>`)."""
    found = TICKET_PATH.fullmatch(ticket)
    if found is None:
        raise SelectError(f"티켓 경로가 아니다: {ticket}")
    return f"{found.group(1)}-{found.group(2)}"


@dataclass(frozen=True)
class Candidate:
    """푼 티켓이 하나인 병합 커밋 M과 B의 값(싼 조건을 보는 데 드는 것)."""

    merge: str
    base: str
    merged_at: datetime  # M의 커밋 시각
    base_at: datetime  # B의 커밋 시각
    pr: int | None  # M 제목 끝의 PR 번호
    ticket: str
    ticket_text: str | None  # B의 티켓 글. B에 없으면 None
    setup_present: tuple[str, ...]  # B에 있는 SETUP_FILES

    @property
    def task_id(self) -> str:
        return task_id_of(self.ticket)


# --- 브랜치 표 ---


@dataclass(frozen=True)
class BranchRow:
    """소급 측정 수집 도구(`collect.py`)가 쓴 브랜치 표의 한 행에서 쓰는 칸."""

    branch: str
    prs: tuple[int, ...]
    cost: float
    cost_post_pr: float
    top_model_effort: str | None


def _number(value: Json) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _branch_row(item: Json, index: int) -> BranchRow:
    where = f"브랜치 표의 branches[{index}]"
    if not isinstance(item, dict):
        raise SelectError(f"{where} 가 객체가 아니다")
    branch, prs = item.get("branch"), item.get("prs")
    cost, post = _number(item.get("cost")), _number(item.get("cost_post_pr"))
    top = item.get("top_model_effort")
    if not isinstance(branch, str) or not branch:
        raise SelectError(f"{where}.branch 가 글이 아니다")
    if not isinstance(prs, list) or not all(
        isinstance(p, int) and not isinstance(p, bool) for p in prs
    ):
        raise SelectError(f"{where}.prs 가 정수 목록이 아니다")
    if cost is None or post is None:
        raise SelectError(f"{where} 의 cost 나 cost_post_pr 가 수가 아니다")
    # 과제 목록은 PR 앞 비용을 0 이상의 유한한 수로만 받아(`rerun_files`), 여기서 거르지 않으면
    # 가르기가 끝난 뒤 목록을 쓸 때 터진다
    if not all(math.isfinite(n) and n >= 0 for n in (cost, post)):
        raise SelectError(f"{where} 의 cost 나 cost_post_pr 가 0 이상의 유한한 수가 아니다")
    if post > cost:
        raise SelectError(f"{where} 의 cost_post_pr({post:g}) 가 cost({cost:g}) 보다 크다")
    if top is not None and not isinstance(top, str):
        raise SelectError(f"{where}.top_model_effort 가 글이나 null 이 아니다")
    if top == "":  # 과제 목록이 빈 글을 받지 않는다(위 비용과 같은 까닭)
        raise SelectError(f"{where}.top_model_effort 가 빈 글이다")
    numbers = tuple(p for p in prs if isinstance(p, int))
    return BranchRow(branch=branch, prs=numbers, cost=cost, cost_post_pr=post, top_model_effort=top)


def parse_branches(text: str) -> tuple[BranchRow, ...]:
    """브랜치 표의 글을 행으로 푼다. 꼴이 다르면 `SelectError`다."""
    try:
        data: Json = json.loads(text)
    except json.JSONDecodeError as error:
        raise SelectError(f"브랜치 표가 JSON 이 아니다: {error}") from error
    rows = data.get("branches") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise SelectError("브랜치 표에 branches 목록이 없다")
    return tuple(_branch_row(item, i) for i, item in enumerate(rows))


def _by_branch(rows: Sequence[BranchRow], what: str) -> dict[str, BranchRow]:
    counts = Counter(row.branch for row in rows)
    doubled = sorted(branch for branch, n in counts.items() if n > 1)
    if doubled:
        raise SelectError(f"{what}에 " + ", ".join(f"{b} 의 행이 {counts[b]}개다" for b in doubled))
    return {row.branch: row for row in rows}


def with_earlier(rows: Sequence[BranchRow], earlier: Sequence[BranchRow]) -> tuple[BranchRow, ...]:
    """옛 브랜치 표와 견준 행. 브랜치마다 PR 앞 비용이 큰 쪽의 비용·모델 레벨을 쓰고 PR 번호는
    새 표의 것을 쓴다. 옛 표에만 있는 브랜치는 뒤에 더한다. 세션 기록이 지워지면 PR 앞 비용이
    줄기만 해서다(파일럿 티켓(11)이 사람과 정했다)."""
    new = _by_branch(rows, "브랜치 표")
    old = _by_branch(earlier, "옛 브랜치 표")
    out: list[BranchRow] = []
    for row in rows:
        before = old.get(row.branch)
        if before is None or pr_cost(before) <= pr_cost(row):
            out.append(row)
        else:
            out.append(
                BranchRow(
                    row.branch, row.prs, before.cost, before.cost_post_pr, before.top_model_effort
                )
            )
    out.extend(row for row in earlier if row.branch not in new)
    return tuple(out)


# --- 싼 조건 ---


def external_terms(text: str | None) -> tuple[str, ...]:
    """티켓 글이 걸린 바깥 검증 낱말. 대소문자를 가리지 않고 찾는다."""
    folded = (text or "").casefold()
    return tuple(term for term in EXTERNAL_TERMS if term.casefold() in folded)


def size_of(text: str | None) -> int:
    """크기 지표. 백틱으로 싼 서로 다른 파일 경로의 수다."""
    return len(set(BACKTICK_PATH.findall(text or "")))


def pr_cost(row: BranchRow) -> float:
    """원래 세션의 PR 앞 비용."""
    return round(row.cost - row.cost_post_pr, 4)


@dataclass(frozen=True)
class Checked:
    """후보 하나의 싼 조건. `others`는 낱말 밖의 까닭이고 날짜는 들지 않는다."""

    candidate: Candidate
    origin: BranchRow | None  # 브랜치 표에서 원래 브랜치의 행. 정확히 하나일 때만 든다
    terms: tuple[str, ...]
    revived: str | None  # 되살린 까닭
    others: tuple[str, ...]

    @property
    def reasons(self) -> tuple[str, ...]:
        words = (f"바깥 검증 낱말에 걸렸다({', '.join(self.terms)})",)
        return self.others + (words if self.terms and self.revived is None else ())

    @property
    def cost(self) -> float | None:
        return None if self.origin is None else pr_cost(self.origin)

    @property
    def size(self) -> int:
        return size_of(self.candidate.ticket_text)


def _origin(c: Candidate, rows: Sequence[BranchRow]) -> tuple[BranchRow | None, str | None]:
    """원래 브랜치의 행과, 찾지 못한 까닭."""
    if c.pr is None:
        return None, "M 제목 끝에 PR 번호가 없다"
    found = [r for r in rows if c.pr in r.prs]
    if not found:
        return None, f"브랜치 표에 PR #{c.pr} 의 행이 없다"
    if len(found) > 1:
        return None, f"브랜치 표에 PR #{c.pr} 의 행이 {len(found)}개다"
    if not found[0].branch.startswith(BRANCH_PREFIX):
        return None, f"원래 브랜치 {found[0].branch} 가 {BRANCH_PREFIX} 로 시작하지 않는다"
    return found[0], None


def checked_of(c: Candidate, rows: Sequence[BranchRow]) -> Checked:
    """날짜와 숨은 시험 밖의 조건을 본 값. 되살리기 전이다."""
    others: list[str] = []
    if c.ticket_text is None:
        others.append("B 에 티켓 파일이 없다")
    if EXTERNAL_NAME in c.ticket.rpartition("/")[2]:
        others.append(f"파일 이름에 {EXTERNAL_NAME} 가 든다")
    origin, missing = _origin(c, rows)
    if missing is not None:
        others.append(missing)
    if origin is not None and pr_cost(origin) > COST_LIMIT_USD:
        others.append(f"PR 앞 비용 ${pr_cost(origin):.2f} 가 ${COST_LIMIT_USD:g} 를 넘는다")
    return Checked(
        candidate=c,
        origin=origin,
        terms=external_terms(c.ticket_text),
        revived=None,
        others=tuple(others),
    )


def revive(checked: Sequence[Checked], wanted: Mapping[str, str]) -> tuple[Checked, ...]:
    """되살릴 목록을 들인다. 낱말로만 빠진 후보가 아니면 `SelectError`다."""
    by_id: dict[str, list[Checked]] = {}
    for item in checked:
        by_id.setdefault(item.candidate.task_id, []).append(item)
    errors: list[str] = []
    for task_id in wanted:
        found = by_id.get(task_id, [])
        if len(found) != 1:
            errors.append(f"{task_id}: 후보 {len(found)}개에 맞는다(하나여야 한다)")
        elif not found[0].terms:
            errors.append(f"{task_id}: 바깥 검증 낱말에 걸리지 않았다")
        elif found[0].others:
            errors.append(f"{task_id}: 다른 조건으로도 빠졌다({'; '.join(found[0].others)})")
    if errors:
        raise SelectError("되살릴 목록을 들이지 못했다: " + " / ".join(errors))
    return tuple(
        Checked(
            candidate=item.candidate,
            origin=item.origin,
            terms=item.terms,
            revived=wanted.get(item.candidate.task_id),
            others=item.others,
        )
        for item in checked
    )


def parse_revive(text: str) -> dict[str, str]:
    """되살릴 목록의 글(과제 id → 까닭의 JSON 객체)을 푼다."""
    try:
        data: Json = json.loads(text)
    except json.JSONDecodeError as error:
        raise SelectError(f"되살릴 목록이 JSON 이 아니다: {error}") from error
    if not isinstance(data, dict):
        raise SelectError("되살릴 목록은 과제 id 에서 까닭으로 가는 객체다")
    out: dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(value, str) or not value.strip():
            raise SelectError(f"되살릴 목록의 {key} 에 까닭이 없다")
        out[key] = value
    return out


# --- 날짜, 거슬러 채우기, 숨은 시험 ---


class Place(Enum):
    """후보가 표에 든 자리."""

    IN_WINDOW = "날짜 안"
    BACKFILL = "거슬러 채움"
    UNREACHED = "닿지 않음"


@dataclass(frozen=True)
class Row:
    """후보 표의 한 행. `reasons`가 비면 남은 후보다."""

    checked: Checked
    place: Place
    hidden: rerun_hidden.Hidden | rerun_hidden.Failure | None  # 가르지 않았으면 None
    reasons: tuple[str, ...]

    @property
    def kept(self) -> bool:
        return not self.reasons


def _hidden_reason(got: rerun_hidden.Hidden | rerun_hidden.Failure) -> str | None:
    if isinstance(got, rerun_hidden.Failure):
        return f"숨은 시험을 가르지 못했다: {got.reason}"
    if len(got.hidden_tests) < MIN_HIDDEN:
        return f"숨은 시험이 {len(got.hidden_tests)}개라 {MIN_HIDDEN}개보다 적다"
    return None


def _judge(item: Checked, place: Place, sort: Sorter) -> Row:
    if item.reasons:
        return Row(checked=item, place=place, hidden=None, reasons=item.reasons)
    got = sort(item.candidate.base, item.candidate.merge)
    reason = _hidden_reason(got)
    return Row(checked=item, place=place, hidden=got, reasons=() if reason is None else (reason,))


def _merge_order(c: Candidate) -> tuple[datetime, str]:
    """M의 커밋 시각과 해시. 늦은 차례로 둘 때의 키다."""
    return c.merged_at, c.merge


def _latest_first(items: Sequence[Checked]) -> list[Checked]:
    return sorted(items, key=lambda i: _merge_order(i.candidate), reverse=True)


def build_rows(
    checked: Sequence[Checked], sort: Sorter, *, need: int = MIN_CANDIDATES
) -> tuple[Row, ...]:
    """날짜 안의 후보를 모두 보고, 남은 후보가 `need`보다 적으면 그 앞을 늦은 것부터 하나씩 더한다.

    `sort(B, M)`은 싼 조건을 지난 후보에만, 날짜 안의 후보부터 M이 늦은 차례로 부른다. 행은 M이 늦은
    차례다.
    """
    inside = _latest_first([i for i in checked if i.candidate.base_at >= DATE_FLOOR])
    before = _latest_first([i for i in checked if i.candidate.base_at < DATE_FLOOR])
    rows = [_judge(item, Place.IN_WINDOW, sort) for item in inside]
    kept = sum(row.kept for row in rows)
    for item in before:
        if kept >= need:
            date = f"B 가 {DATE_FLOOR.date()} 앞이고 거슬러 채우기가 닿지 않았다"
            reasons = (date, *item.reasons)
            rows.append(Row(checked=item, place=Place.UNREACHED, hidden=None, reasons=reasons))
            continue
        row = _judge(item, Place.BACKFILL, sort)
        kept += row.kept
        rows.append(row)
    return tuple(sorted(rows, key=lambda r: _merge_order(r.checked.candidate), reverse=True))


# --- 후보 표 ---


_BREAKS = re.compile("[\r\n\x0b\x0c\x85" + chr(0x2028) + chr(0x2029) + "]+")


def _cell(text: str) -> str:
    """표의 칸 하나. 줄을 끊는 글자는 빈칸으로, `|`는 역슬래시로 감싼다."""
    flat = _BREAKS.sub(" ", text)
    return flat.replace("|", "\\|")


_MAX_GROUPS = 6


def dropped_summary(dropped: Sequence[rerun_hidden.Dropped]) -> str:
    """빠진 노드를 조건과 까닭으로 묶어 센 글. 묶음이 많으면 앞의 여섯과 남은 묶음 수다."""
    counts = Counter((d.condition, d.cause) for d in dropped)
    groups = sorted(counts.items(), key=lambda kv: (kv[0][0], -kv[1], kv[0][1]))
    parts = [f"조건 {cond} {cause} ×{n}" for (cond, cause), n in groups[:_MAX_GROUPS]]
    if len(groups) > _MAX_GROUPS:
        parts.append(f"외 {len(groups) - _MAX_GROUPS}가지")
    return "; ".join(parts)


def _hidden_cells(hidden: rerun_hidden.Hidden | rerun_hidden.Failure | None) -> tuple[str, str]:
    if not isinstance(hidden, rerun_hidden.Hidden):
        return "—", "—"
    return str(len(hidden.hidden_tests)), dropped_summary(hidden.dropped) or "—"


def _terms_cell(item: Checked) -> str:
    if not item.terms:
        return "—"
    words = ", ".join(item.terms)
    return words if item.revived is None else f"{words}(되살림: {item.revived})"


_HEAD = (
    "과제 id",
    "PR",
    "B",
    "M",
    "B 시각",
    "원래 브랜치",
    "자리",
    "남음",
    "빠진 까닭",
    "바깥 검증 낱말",
    "PR 앞 비용",
    "크기",
    "숨은 시험",
    "빠진 노드",
    *(f"B 의 `{f}`" for f in SETUP_FILES),
)


def _row_cells(row: Row) -> tuple[str, ...]:
    item = row.checked
    c = item.candidate
    count, dropped = _hidden_cells(row.hidden)
    return (
        c.task_id,
        "—" if c.pr is None else f"#{c.pr}",
        c.base[:8],
        c.merge[:8],
        c.base_at.isoformat(timespec="minutes"),
        "—" if item.origin is None else item.origin.branch,
        row.place.value,
        "남음" if row.kept else "빠짐",
        "; ".join(row.reasons) or "—",
        _terms_cell(item),
        "—" if item.cost is None else f"${item.cost:.2f}",
        str(item.size),
        count,
        dropped,
        *("있음" if f in c.setup_present else "없음" for f in SETUP_FILES),
    )


@dataclass(frozen=True)
class Counts:
    """후보 표 끝의 세 줄."""

    inside: int  # 날짜 안의 남은 후보
    backfilled: int  # 거슬러 채워 남은 후보
    backfilled_missing_setup: int  # 그 가운데 B에 SETUP_FILES 가운데 하나라도 없는 것


def counts_of(rows: Sequence[Row]) -> Counts:
    kept = [r for r in rows if r.kept]
    backfilled = [r for r in kept if r.place is Place.BACKFILL]
    missing = [
        r
        for r in backfilled
        if any(f not in r.checked.candidate.setup_present for f in SETUP_FILES)
    ]
    return Counts(
        inside=sum(r.place is Place.IN_WINDOW for r in kept),
        backfilled=len(backfilled),
        backfilled_missing_setup=len(missing),
    )


def render_table(rows: Sequence[Row], header: Sequence[str], ambiguous: Sequence[str]) -> str:
    """후보 표의 마크다운. `header`는 표 앞의 줄(입력의 출처), `ambiguous`는 푼 티켓 파일이 둘
    이상인 병합 커밋의 PR 표기다."""
    lines = ["# 다시 풀기 후보 표", "", *header, ""]
    lines.append("| " + " | ".join(_HEAD) + " |")
    lines.append("|" + "---|" * len(_HEAD))
    lines += ["| " + " | ".join(_cell(x) for x in _row_cells(r)) + " |" for r in rows]
    counts = counts_of(rows)
    floor = DATE_FLOOR.date()
    lines += [
        "",
        f"- B 가 {floor} 이후인 남은 후보: {counts.inside}개(문턱 {MIN_CANDIDATES}개)",
        f"- 거슬러 채워 남은 후보: {counts.backfilled}개",
        f"- 거슬러 채워 남은 후보 가운데 B 에 준비·게이트 파일"
        f"({', '.join(f'`{f}`' for f in SETUP_FILES)}) 가운데 하나라도 없는 것: "
        f"{counts.backfilled_missing_setup}개",
    ]
    if ambiguous:
        lines.append(f"- 푼 티켓 파일이 둘 이상이라 후보가 아닌 병합 커밋: {', '.join(ambiguous)}")
    return "\n".join(lines) + "\n"


# --- 고르기 ---


@dataclass(frozen=True)
class Pick:
    """남은 후보 하나와 그 숨은 시험."""

    checked: Checked
    hidden: rerun_hidden.Hidden


def picks_of(rows: Sequence[Row]) -> tuple[Pick, ...]:
    """남은 후보를 크기 지표 순(동률은 M의 해시 순)으로 둔다."""
    out = [
        Pick(checked=r.checked, hidden=r.hidden)
        for r in rows
        if r.kept and isinstance(r.hidden, rerun_hidden.Hidden)
    ]
    ids = Counter(p.checked.candidate.task_id for p in out)
    twice = sorted(i for i, n in ids.items() if n > 1)
    if twice:
        raise SelectError(f"남은 후보의 과제 id 가 겹친다: {', '.join(twice)}")
    return tuple(sorted(out, key=lambda p: (p.checked.size, p.checked.candidate.merge)))


def _shuffled[T](items: Sequence[T], seed: int) -> list[T]:
    out = list(items)
    random.Random(seed).shuffle(out)
    return out


def round_cap(cost: float) -> float:
    return round(max(CAP_MULTIPLIER * cost, CAP_FLOOR_USD), 4)


def _task(pick: Pick, *, tier: str, order: int, plan: tuple[str, ...]) -> Task:
    item = pick.checked
    row = item.origin
    if row is None:  # 남은 후보는 원래 브랜치의 행이 있다
        raise SelectError(f"{item.candidate.task_id}: 원래 브랜치의 행이 없다")
    cost = pr_cost(row)
    return Task(
        task_id=item.candidate.task_id,
        ticket=item.candidate.ticket,
        base=item.candidate.base,
        merge=item.candidate.merge,
        branch=row.branch,
        tier=tier,
        size=item.size,
        order=order,
        pilot=tier == TIER_PILOT,
        pr_cost_usd=cost,
        round_cap_usd=round_cap(cost),
        hidden_tests=pick.hidden.hidden_tests,
        support_files=pick.hidden.support_files,
        original_model_effort=row.top_model_effort,
        arm_plan=plan,
    )


def pick_pilot(picks: Sequence[Pick]) -> TaskList:
    """파일럿 셋. 정렬한 후보의 아래 삼분의 일을 `SEED_PILOT`으로 섞어 앞에서 고른다."""
    bottom = list(picks[: len(picks) // 3])
    if len(bottom) < len(PILOT_PLANS):
        raise SelectError(
            f"남은 후보 {len(picks)}개의 아래 삼분의 일이 {len(bottom)}개라 파일럿 "
            f"{len(PILOT_PLANS)}개를 고르지 못한다"
        )
    chosen = _shuffled(bottom, SEED_PILOT)[: len(PILOT_PLANS)]
    tasks = tuple(
        _task(p, tier=TIER_PILOT, order=i, plan=plan)
        for i, (p, plan) in enumerate(zip(chosen, PILOT_PLANS, strict=True))
    )
    return TaskList(kind=LIST_PILOT, tasks=tasks)


def arm_plan(order: int) -> tuple[str, ...]:
    """본 측정 실행 차례 `order`의 갈래 계획. 다섯 갈래를 씨앗 `ARM_SEED_BASE + order`로 섞는다."""
    return tuple(_shuffled([a.name for a in ARMS], ARM_SEED_BASE + order))


def pick_main(picks: Sequence[Pick], pilot: TaskList) -> TaskList:
    """본 측정 여덟. 파일럿 목록의 과제를 뺀 후보를 층 셋으로 잘라 층마다 섞어 고르고 엇갈린
    차례로 둔다."""
    if pilot.kind != LIST_PILOT:
        raise SelectError(f"파일럿 목록이 아니다(종류 {pilot.kind})")
    used = {t.task_id for t in pilot.tasks}
    rest = [p for p in picks if p.checked.candidate.task_id not in used]
    third = len(rest) // 3
    tiers = (
        (TIER_SMALL, rest[:third], SEED_SMALL),
        (TIER_MEDIUM, rest[third : 2 * third], SEED_MEDIUM),
        (TIER_LARGE, rest[2 * third :], SEED_LARGE),
    )
    chosen: list[tuple[str, list[Pick]]] = []
    for (tier, members, seed), want in zip(tiers, MAIN_COUNTS, strict=True):
        if len(members) < want:
            raise SelectError(
                f"파일럿을 뺀 후보 {len(rest)}개의 {tier} 층이 {len(members)}개라 "
                f"{want}개를 고르지 못한다"
            )
        chosen.append((tier, _shuffled(members, seed)[:want]))
    ordered = [
        (tier, members[k])
        for k in range(max(MAIN_COUNTS))
        for tier, members in chosen
        if k < len(members)
    ]
    tasks = tuple(
        _task(p, tier=tier, order=i, plan=arm_plan(i)) for i, (tier, p) in enumerate(ordered)
    )
    return TaskList(kind=LIST_MAIN, tasks=tasks)


# --- 바깥 층: git ---


_GIT = shutil.which("git") or "git"


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in REPO_LOCATION_VARS}


def git_name(args: Sequence[str]) -> str:
    """알림에 쓰는 git 명령 이름. 앞의 `-c <설정>`을 건너뛰고 하위 명령과 그 다음 낱말을 든다."""
    rest = list(args)
    while rest[:1] == ["-c"]:
        rest = rest[2:]
    return " ".join(["git", *rest[:2]])


def _git(repo: Path, args: Sequence[str], data: bytes | None = None) -> bytes:
    shown = git_name(args)
    try:
        done = subprocess.run(
            [_GIT, "-C", str(repo), *args],
            input=data,
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT,
            env=_env(),
        )
    except subprocess.TimeoutExpired as error:
        raise SelectError(f"{shown} 가 시간 제한({GIT_TIMEOUT:g}초)을 넘겼다") from error
    except OSError as error:
        raise SelectError(f"{shown} 를 띄우지 못했다: {error}") from error
    if done.returncode != 0:
        stderr = done.stderr.decode("utf-8", errors="replace").strip().splitlines()
        raise SelectError(f"{shown} 가 {done.returncode}로 끝났다: {stderr[-1] if stderr else ''}")
    return done.stdout


@dataclass(frozen=True)
class _Commit:
    sha: str
    parents: tuple[str, ...]
    at: datetime
    subject: str


def _commits(repo: Path, rev: str) -> list[_Commit]:
    out = _git(repo, ["log", "--first-parent", "-z", "--format=%H%x1f%P%x1f%cI%x1f%s", rev])
    commits: list[_Commit] = []
    for record in out.decode("utf-8", errors="replace").split("\0"):
        if not record.strip():
            continue
        sha, parents, at, subject = record.strip("\n").split("\x1f", 3)
        commits.append(_Commit(sha, tuple(parents.split()), datetime.fromisoformat(at), subject))
    return commits


def _ticket_changes(repo: Path, rev: str) -> dict[str, list[str]]:
    """첫 부모 줄의 커밋마다 바꾼 티켓 파일."""
    out = _git(
        repo,
        [
            "-c",
            "core.quotepath=false",
            "log",
            "--first-parent",
            "--no-renames",
            "--name-only",
            "--format=%x00%H",
            rev,
            "--",
            ".scratch/*/issues/*.md",
        ],
    )
    changes: dict[str, list[str]] = {}
    for block in out.decode("utf-8", errors="replace").split("\0"):
        lines = [line for line in block.splitlines() if line]
        if lines:
            changes[lines[0]] = [p for p in lines[1:] if TICKET_PATH.fullmatch(p)]
    return changes


def _at(commit: str, path: str) -> str:
    """`git cat-file`이 받는 `<커밋>:<경로>`."""
    return f"{commit}:{path}"


def _blobs(repo: Path, specs: Sequence[str]) -> dict[str, bytes | None]:
    """`_at`의 꼴마다 그 블롭. 없으면 None이다. `git cat-file --batch` 한 번으로 읽는다. 커밋은 전체
    해시만 넘겨 이름이 모호할 일이 없다."""
    if not specs:
        return {}
    out = _git(repo, ["cat-file", "--batch"], data="".join(f"{s}\n" for s in specs).encode())
    found: dict[str, bytes | None] = {}
    at = 0
    for spec in specs:
        end = out.index(b"\n", at)
        head = out[at:end].decode("utf-8", errors="replace")
        at = end + 1
        if head.endswith(" missing"):
            found[spec] = None
            continue
        size = int(head.rsplit(" ", 1)[1])
        kind = head.split(" ")[1]
        found[spec] = out[at : at + size] if kind == "blob" else None
        at += size + 1
    return found


def _text(data: bytes | None) -> str | None:
    return (
        None if data is None else data.decode("utf-8", errors="replace").removeprefix(chr(0xFEFF))
    )


def _status(data: bytes | None) -> str | None:
    text = _text(data)
    return None if text is None else status_of(text)


def _pr_of(subject: str) -> int | None:
    found = PR_SUFFIX.search(subject)
    return None if found is None else int(found.group(1))


@dataclass(frozen=True)
class Listing:
    """병합 기록에서 찾은 후보와, 푼 티켓 파일이 둘 이상인 병합 커밋의 PR 표기."""

    candidates: tuple[Candidate, ...]
    ambiguous: tuple[str, ...]


def list_candidates(repo: Path, rev: str) -> Listing:
    """`rev`의 첫 부모 줄에서 푼 티켓이 하나인 squash 병합 커밋을 후보로 찾는다."""
    commits = _commits(repo, rev)
    when = {c.sha: c.at for c in commits}
    changes = _ticket_changes(repo, rev)
    squashed = [c for c in commits if len(c.parents) == 1 and changes.get(c.sha)]
    specs: list[str] = []
    for c in squashed:
        base = c.parents[0]
        for path in changes[c.sha]:
            specs += [_at(base, path), _at(c.sha, path)]
        specs += [_at(base, f) for f in SETUP_FILES]
    blobs = _blobs(repo, specs)
    candidates: list[Candidate] = []
    ambiguous: list[str] = []
    for c in squashed:
        base = c.parents[0]
        ticket_changes = [
            TicketChange(p, _status(blobs[_at(base, p)]), _status(blobs[_at(c.sha, p)]))
            for p in changes[c.sha]
        ]
        solved = solved_tickets(ticket_changes)
        pr = _pr_of(c.subject)
        if len(solved) > 1:
            ambiguous.append(f"#{pr}" if pr is not None else c.sha[:8])
        if len(solved) != 1:
            continue
        candidates.append(
            Candidate(
                merge=c.sha,
                base=base,
                merged_at=c.at,
                base_at=when[base],  # 첫 부모 줄은 커밋마다 그 첫 부모를 다음 줄에 든다
                pr=pr,
                ticket=solved[0],
                ticket_text=_text(blobs[_at(base, solved[0])]),
                setup_present=tuple(f for f in SETUP_FILES if blobs[_at(base, f)] is not None),
            )
        )
    return Listing(candidates=tuple(candidates), ambiguous=tuple(ambiguous))


def _rev_sha(repo: Path, rev: str) -> str:
    return _git(repo, ["rev-parse", "--verify", f"{rev}^{{commit}}"]).decode().strip()


# --- 명령 줄 ---


def _read(path: Path, what: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SelectError(f"{what} {path} 를 읽지 못했다: {error}") from error


def _sorter(repo: Path, out: Callable[[str], None]) -> Sorter:
    """실제 숨은 시험 가르기(`sort_candidate`)에 진행을 알리는 줄을 붙인다."""

    def sort(base: str, merge: str) -> rerun_hidden.Hidden | rerun_hidden.Failure:
        out(f"숨은 시험을 가른다: B {base[:8]} M {merge[:8]}")
        got = rerun_hidden.sort_candidate(repo, base, merge, out=out)
        if isinstance(got, rerun_hidden.Failure):
            out(f"  가르지 못했다: {got.reason}")
        else:
            out(f"  숨은 시험 {len(got.hidden_tests)}개, 빠진 노드 {len(got.dropped)}개")
        return got

    return sort


def _shown(path: Path, repo: Path) -> str:
    """커밋할 표에 적는 입력 파일. 저장소 안이면 저장소 기준 상대 경로이고, 밖이면 이름만이라 사용자
    경로가 표에 들지 않는다."""
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.name


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _header(
    args: argparse.Namespace, sha: str, branches_text: str, earlier_text: str | None
) -> list[str]:
    revive = "없다" if args.revive is None else f"`{_shown(args.revive, args.repo)}`다"
    earlier = (
        "없다"
        if earlier_text is None
        else f"`{_shown(args.earlier_branches, args.repo)}`(SHA-256 앞 12자리 "
        f"`{_digest(earlier_text)}`)이고 브랜치마다 PR 앞 비용이 큰 쪽을 쓴다"
    )
    return [
        f"`tools/rerun_select.py` 가 지었다. main 은 `{sha[:12]}`(`{args.rev}`), 브랜치 표는 "
        f"`{_shown(args.branches, args.repo)}`(SHA-256 앞 12자리 `{_digest(branches_text)}`), "
        f"옛 브랜치 표는 {earlier}, 되살릴 목록은 {revive}.",
        f"조건은 그 모듈의 상수다. 날짜 바닥 {DATE_FLOOR.isoformat()}(B 의 커밋 시각), 후보 문턱 "
        f"{MIN_CANDIDATES}개, 숨은 시험 {MIN_HIDDEN}개 이상, PR 앞 비용 ${COST_LIMIT_USD:g} 이하, "
        f"원래 브랜치 `{BRANCH_PREFIX}`. 바깥 검증 낱말은 "
        f"{', '.join(f'`{t}`' for t in EXTERNAL_TERMS)}(대소문자를 가리지 않는다)과 파일 이름의 "
        f"`{EXTERNAL_NAME}`이다.",
        "행은 M 이 늦은 차례다. 자리의 `거슬러 채움`은 남은 후보가 모자라 B 가 날짜 바닥 앞인 "
        "후보를 늦은 것부터 더해 본 행이고, `닿지 않음`은 채운 뒤라 보지 않은 행이다. 빠진 노드는 "
        "숨은 시험 가르기(`tools/rerun_hidden.py`)가 뺀 노드를 조건과 까닭으로 묶어 센 것이다.",
    ]


def select_rows(
    repo: Path, sha: str, branches: Sequence[BranchRow], wanted: Mapping[str, str], sort: Sorter
) -> tuple[tuple[Row, ...], Listing]:
    """병합 기록 `sha`에서 후보를 찾아 조건을 보고 후보 표의 행을 짓는다."""
    listing = list_candidates(repo, sha)
    checked = revive([checked_of(c, branches) for c in listing.candidates], wanted)
    return build_rows(checked, sort), listing


type Out = Callable[[str], None]
type MakeSorter = Callable[[Path, Out], Sorter]


def _outputs(args: argparse.Namespace) -> list[tuple[Path, str]]:
    found = [(args.table, "후보 표")]
    if args.command != "table":
        found.append((args.out, "과제 목록"))
    return found


def _write(path: Path, what: str, text: Callable[[], str]) -> None:
    """글을 다 짓고 UTF-8 바이트로 바꾼 뒤에야 연다. 꼴 거부나 인코딩 실패면 그 자리를 건드리지
    않는다."""
    try:
        data = text().encode("utf-8")
        path.write_bytes(data)
    except (OSError, ValueError) as error:  # ValueError: 꼴 거부(`ShapeError`)와 인코딩 실패
        raise SelectError(f"{what} {path} 를 쓰지 못했다: {error}") from error


def _run(args: argparse.Namespace, out: Out, make_sorter: MakeSorter) -> int:
    for path, what in _outputs(args):  # 오래 걸리는 가르기 전에 본다
        if not path.parent.is_dir():
            raise SelectError(f"{what} {path} 의 폴더가 없다")
        if path.is_dir():
            raise SelectError(f"{what} {path} 가 폴더다")
        if path.exists() and not os.access(path, os.W_OK):
            raise SelectError(f"{what} {path} 에 쓸 수 없다")
    pilot = None
    if args.command == "main":
        try:
            pilot = read_task_list(args.pilot)
        except (OSError, ShapeError) as error:
            raise SelectError(f"파일럿 목록 {args.pilot} 를 읽지 못했다: {error}") from error
    branches_text = _read(args.branches, "브랜치 표")
    branches = parse_branches(branches_text)
    earlier_text = None
    if args.earlier_branches is not None:
        earlier_text = _read(args.earlier_branches, "옛 브랜치 표")
        branches = with_earlier(branches, parse_branches(earlier_text))
    wanted = {} if args.revive is None else parse_revive(_read(args.revive, "되살릴 목록"))
    sha = _rev_sha(args.repo, args.rev)
    rows, listing = select_rows(args.repo, sha, branches, wanted, make_sorter(args.repo, out))
    table = render_table(rows, _header(args, sha, branches_text, earlier_text), listing.ambiguous)
    _write(args.table, "후보 표", lambda: table)
    out(f"후보 표를 썼다: {args.table}")
    if args.command == "table":
        return 0
    try:
        picks = picks_of(rows)
        chosen = pick_pilot(picks) if pilot is None else pick_main(picks, pilot)
    except SelectError as error:
        out(f"목록을 짓지 못했다: {error}")
        return 1
    _write(args.out, "과제 목록", lambda: dumps_task_list(chosen))
    out(f"{chosen.kind} 목록을 썼다: {args.out}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="다시 풀기의 과제 고르기. 후보 표를 짓고 과제 목록을 고른다."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    commands = {
        "table": "후보 표만 짓는다",
        "pilot": "후보 표를 짓고 파일럿 목록을 고른다",
        "main": "후보 표를 짓고 파일럿 목록의 과제를 뺀 본 측정 목록을 고른다",
    }
    for name, help_text in commands.items():
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--branches", type=Path, required=True, help="수집 도구가 쓴 브랜치 표")
        p.add_argument(
            "--earlier-branches",
            type=Path,
            help="옛 브랜치 표. 브랜치마다 PR 앞 비용이 큰 쪽을 쓴다",
        )
        p.add_argument("--revive", type=Path, help="되살릴 목록(과제 id → 까닭의 JSON)")
        p.add_argument("--table", type=Path, required=True, help="쓸 후보 표(마크다운)")
        p.add_argument("--repo", type=Path, default=Path("."), help="병합 기록을 읽을 저장소")
        p.add_argument("--rev", default="origin/main", help="병합 기록의 끝(기본 origin/main)")
        if name != "table":
            p.add_argument("--out", type=Path, required=True, help="쓸 과제 목록")
        if name == "main":
            p.add_argument("--pilot", type=Path, required=True, help="커밋한 파일럿 목록")
    return parser


def main(argv: Sequence[str] | None = None, *, make_sorter: MakeSorter | None = None) -> int:
    """명령 줄 입구. `make_sorter`는 시험이 숨은 시험 가르기를 갈아 끼우는 자리다."""
    args = _parser().parse_args(argv)

    def out(line: str) -> None:
        print(line, file=sys.stderr, flush=True)

    try:
        return _run(args, out, make_sorter or _sorter)
    except SelectError as error:
        out(f"rerun_select: {error}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
