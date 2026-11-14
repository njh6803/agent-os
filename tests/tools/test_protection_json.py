"""`tools/protection.json`(main)과 `tools/protection-dev.json`(dev)의 값이 문서가 근거로 든 값과
같은지 본다.

두 파일은 `gh api repos/.../branches/<브랜치>/protection --input`이 읽는 본문이다. 문서는 이 값을
근거로 든다. `operations.md` 가드레일은 두 브랜치가 선형 이력을 강제하지 않는다고 적고,
`next-session`의 `merge.md`는 main이 strict라서 출시 PR 뒤에 main을 dev에 되돌려 합치고 dev는
strict가 아니라서 머리가 main인 되돌려 합치기 PR이 막히지 않는다고 적는다(ADR 0043 이력 2026-11-12
"출시 PR 뒤에도 main을 dev에 되돌려 합친다"). 값이 바뀌고 문서가 그대로면 어긋나도 아무 검사가
알리지 못했다(`dev-branch-create` PR의 claude-review가 짚었다).

이 시험이 보는 것은 파일의 값이다. GitHub에 실제로 적용된 값은 `gh api`로 읽어야 하고 이 시험은 읽지
않는다 (네트워크가 필요하다). 파일을 고치고 적용을 빠뜨린 어긋남은 못 본다.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parents[2]


class _StatusChecks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contexts: list[str]
    strict: bool


class _Protection(BaseModel):
    """`gh api`가 받는 보호 본문. 모르는 키가 끼면 실패시켜 새 설정을 문서가 놓치지 않게 한다."""

    model_config = ConfigDict(extra="forbid")

    allow_deletions: bool
    allow_force_pushes: bool
    enforce_admins: bool
    required_linear_history: bool
    required_pull_request_reviews: None
    required_status_checks: _StatusChecks
    restrictions: None


def _load(name: str) -> _Protection:
    return _Protection.model_validate_json((ROOT / "tools" / name).read_text(encoding="utf-8"))


def test_main은_strict이고_선형_이력을_강제하지_않는다() -> None:
    main = _load("protection.json")
    assert main.required_status_checks.strict is True
    assert main.required_linear_history is False


def test_dev는_strict가_아니고_선형_이력을_강제하지_않는다() -> None:
    dev = _load("protection-dev.json")
    assert dev.required_status_checks.strict is False
    assert dev.required_linear_history is False


def test_두_브랜치_모두_삭제와_강제_푸시를_막고_필수_검사는_verify다() -> None:
    for name in ("protection.json", "protection-dev.json"):
        protection = _load(name)
        assert protection.allow_deletions is False, name
        assert protection.allow_force_pushes is False, name
        assert protection.required_status_checks.contexts == ["verify"], name


def test_두_브랜치_모두_관리자_우회를_허용한다() -> None:
    for name in ("protection.json", "protection-dev.json"):
        assert _load(name).enforce_admins is False, name
