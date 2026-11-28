"""PostgreSQL 이미지의 digest 가 쓰는 자리마다 같은지 본다(ADR 0066, 명세 postgres-foundation).

단독 배포용 compose(`deploy/standalone/compose.yaml`), 테스트 컨테이너(`compose.test.yaml`), CI
의 service container(`.github/workflows/ci.yml`)는 같은 이미지를 쓰는 약속이다. 한 자리만 올리면
운영자의 배포와 이 PC 의 시험과 CI 의 시험이 다른 PostgreSQL 에서 돈다.

글에서 `image:` 줄을 읽는 얕은 읽기다. YAML 을 풀지 않으므로 줄 앞에 `#` 이 붙은 주석의 줄은
건너뛰고, 한 줄에 쓴 `image: postgres@sha256:…` 만 본다. 여러 줄로 접은 값이나 앵커로 가져온 값은 못
본다.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose.test.yaml"
STANDALONE = ROOT / "deploy" / "standalone" / "compose.yaml"
CI = ROOT / ".github" / "workflows" / "ci.yml"

_IMAGE = re.compile(r"^[ \t]*-?[ \t]*image:[ \t]*(?P<value>[^\s#]+)", re.MULTILINE)
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")

_STANDALONE_NAME = "deploy/standalone/compose.yaml"

# 단독 compose 의 PostgreSQL 은 둘이다. Agent OS 쪽(`postgres`)과 위젯 쪽(`widget-admin-postgres`)이
# 데이터베이스를 따로 쓴다. 둘 다 같은 이미지(같은 digest)를 쓰는 약속이다.
STANDALONE_POSTGRES_COUNT = 2


def postgres_images(text: str) -> list[str]:
    """`image:` 줄 가운데 PostgreSQL 이미지의 값. 주석의 줄은 건너뛴다."""
    found: list[str] = []
    for match in _IMAGE.finditer(text):
        value = match.group("value")
        repository = value.split("@", 1)[0].split(":", 1)[0]
        if repository == "postgres":
            found.append(value)
    return found


def digest_of(image: str) -> str | None:
    """`postgres@sha256:…` 의 digest. 태그만 쓴 값이면 `None`."""
    if "@" not in image:
        return None
    match = _DIGEST.fullmatch(image.split("@", 1)[1])
    return match.group(0) if match else None


def pin_problems(compose_text: str, ci_text: str, standalone_text: str) -> list[str]:
    """세 자리의 digest 가 같지 않은 까닭들. 비어 있으면 같다. 기준은 `compose.test.yaml` 이다.

    훑은 범위가 비면(이미지 줄을 하나도 못 읽으면) 같다고 하지 않고 까닭으로 센다. 경로나 읽기가
    틀려도 위반 0 으로 조용히 초록이 되는 일을 막으려는 것이다. 단독 compose 와 테스트 컨테이너에는
    PostgreSQL 이 하나씩이고, CI 에는 잡마다 붙으므로 그 수를 세지 않는다(명세 "저장소 상태 시험").
    """
    composed = postgres_images(compose_text)
    if len(composed) != 1:
        return [f"compose.test.yaml 의 PostgreSQL 이미지는 하나여야 한다: {len(composed)}개"]
    pinned = digest_of(composed[0])
    if pinned is None:
        return [f"compose.test.yaml 의 이미지에 digest 가 없다: {composed[0]}"]
    problems: list[str] = []
    standalone = postgres_images(standalone_text)
    if len(standalone) != STANDALONE_POSTGRES_COUNT:
        problems.append(
            f"{_STANDALONE_NAME} 의 PostgreSQL 이미지는 {STANDALONE_POSTGRES_COUNT}개여야 한다"
            f"(Agent OS 쪽과 위젯 쪽): {len(standalone)}개"
        )
    problems += [
        f"{_STANDALONE_NAME} 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: {image}"
        for image in standalone
        if digest_of(image) != pinned
    ]
    in_ci = postgres_images(ci_text)
    if not in_ci:
        return [*problems, "ci.yml 에 PostgreSQL service container 가 하나도 없다"]
    return problems + [
        f"ci.yml 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: {image}"
        for image in in_ci
        if digest_of(image) != pinned
    ]


COMPOSE_SAMPLE = """\
services:
  postgres:
    # postgres:18 (Debian trixie)
    image: postgres@sha256:{digest}
"""
STANDALONE_SAMPLE = """\
services:
  postgres:
    # postgres:18 (Debian trixie)
    image: postgres@sha256:{digest}
  widget-admin-postgres:
    image: postgres@sha256:{widget_digest}
  serve:
    image: ${{AGENT_OS_NAMESPACE}}/agent-os-runtime:${{AGENT_OS_VERSION}}
"""
CI_SAMPLE = """\
jobs:
  python:
    services:
      postgres:
        image: postgres@sha256:{digest}
"""
OLD = "a" * 64
NEW = "b" * 64


def _samples(
    compose: str = OLD,
    ci: str = OLD,
    standalone: str = OLD,
    widget: str | None = None,
) -> tuple[str, str, str]:
    """`widget` 은 단독 compose 의 위젯 쪽 PostgreSQL digest 다. 비우면 Agent OS 쪽과 같다."""
    return (
        COMPOSE_SAMPLE.format(digest=compose),
        CI_SAMPLE.format(digest=ci),
        STANDALONE_SAMPLE.format(digest=standalone, widget_digest=widget or standalone),
    )


def test_이_저장소의_PostgreSQL_이미지는_세_자리가_같은_digest다() -> None:
    compose_text = COMPOSE.read_text(encoding="utf-8")
    ci_text = CI.read_text(encoding="utf-8")
    standalone_text = STANDALONE.read_text(encoding="utf-8")
    assert len(postgres_images(compose_text)) == 1
    assert len(postgres_images(standalone_text)) == STANDALONE_POSTGRES_COUNT
    ci_images = postgres_images(ci_text)
    missing = f"ci.yml 에 PostgreSQL service container 가 없다 ({len(ci_images)}개)"
    assert len(ci_images) >= 1, missing
    assert pin_problems(compose_text, ci_text, standalone_text) == []


def test_같은_digest_면_문제가_없다() -> None:
    assert pin_problems(*_samples()) == []


def test_CI_의_digest_만_다르면_잡는다() -> None:
    assert pin_problems(*_samples(ci=NEW)) == [
        f"ci.yml 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: postgres@sha256:{NEW}"
    ]


def test_테스트_컨테이너의_digest_만_다르면_다른_자리를_다_잡는다() -> None:
    assert pin_problems(*_samples(compose=NEW)) == [
        f"{_STANDALONE_NAME} 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: "
        f"postgres@sha256:{OLD}",
        f"{_STANDALONE_NAME} 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: "
        f"postgres@sha256:{OLD}",
        f"ci.yml 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: postgres@sha256:{OLD}",
    ]


def test_단독_compose_의_위젯_쪽_digest_만_다르면_잡는다() -> None:
    assert pin_problems(*_samples(widget=NEW)) == [
        f"{_STANDALONE_NAME} 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: "
        f"postgres@sha256:{NEW}"
    ]


def test_단독_compose_의_위젯_쪽_PostgreSQL_이_빠지면_잡는다() -> None:
    compose_text, ci_text, standalone_text = _samples()
    without_widget = standalone_text.replace(
        f"  widget-admin-postgres:\n    image: postgres@sha256:{OLD}\n", ""
    )
    assert without_widget != standalone_text
    assert pin_problems(compose_text, ci_text, without_widget) == [
        f"{_STANDALONE_NAME} 의 PostgreSQL 이미지는 {STANDALONE_POSTGRES_COUNT}개여야 한다"
        "(Agent OS 쪽과 위젯 쪽): 1개"
    ]


def test_단독_compose_의_digest_만_다르면_잡는다() -> None:
    assert pin_problems(*_samples(standalone=NEW, widget=OLD)) == [
        f"{_STANDALONE_NAME} 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: "
        f"postgres@sha256:{NEW}"
    ]


def test_단독_compose_에_PostgreSQL_이_없으면_잡는다() -> None:
    compose_text, ci_text, _ = _samples()
    without = "services:\n  serve:\n    image: x/agent-os-runtime:1\n"
    assert pin_problems(compose_text, ci_text, without) == [
        f"{_STANDALONE_NAME} 의 PostgreSQL 이미지는 {STANDALONE_POSTGRES_COUNT}개여야 한다"
        "(Agent OS 쪽과 위젯 쪽): 0개"
    ]


def test_단독_compose_의_이미지가_태그만_쓰면_잡는다() -> None:
    compose_text, ci_text, standalone_text = _samples()
    tagged = standalone_text.replace(f"postgres@sha256:{OLD}", "postgres:18", 1)
    assert pin_problems(compose_text, ci_text, tagged) == [
        f"{_STANDALONE_NAME} 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: postgres:18"
    ]


def test_CI_에_PostgreSQL_service_container_가_없으면_잡는다() -> None:
    compose_text, _, standalone_text = _samples()
    ci_without = "jobs:\n  python:\n    steps:\n      - run: echo\n"
    assert pin_problems(compose_text, ci_without, standalone_text) == [
        "ci.yml 에 PostgreSQL service container 가 하나도 없다"
    ]


def test_CI_의_이미지가_태그만_쓰면_잡는다() -> None:
    compose_text, ci_text, standalone_text = _samples()
    ci_tag = ci_text.replace(f"postgres@sha256:{OLD}", "postgres:18")
    assert pin_problems(compose_text, ci_tag, standalone_text) == [
        "ci.yml 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: postgres:18"
    ]


def test_CI_의_service_container_가_여럿이면_하나라도_다르면_잡는다() -> None:
    compose_text, ci_text, standalone_text = _samples()
    ci_two = ci_text + f"      second:\n        image: postgres@sha256:{NEW}\n"
    assert pin_problems(compose_text, ci_two, standalone_text) == [
        f"ci.yml 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: postgres@sha256:{NEW}"
    ]


def test_compose_에서_이미지를_읽지_못하면_같다고_하지_않는다() -> None:
    """읽은 범위가 비면 위반 0 으로 초록이 되지 않게 까닭으로 센다."""
    _, ci_text, standalone_text = _samples()
    assert pin_problems("services: {}\n", ci_text, standalone_text) == [
        "compose.test.yaml 의 PostgreSQL 이미지는 하나여야 한다: 0개"
    ]


def test_compose_의_이미지에_digest_가_없으면_잡는다() -> None:
    compose_text, ci_text, standalone_text = _samples()
    compose_tag = compose_text.replace(f"postgres@sha256:{OLD}", "postgres:18")
    assert pin_problems(compose_tag, ci_text, standalone_text) == [
        "compose.test.yaml 의 이미지에 digest 가 없다: postgres:18"
    ]


def test_주석에_쓴_이미지는_읽지_않고_다른_이미지는_건너뛴다() -> None:
    text = "# image: postgres@sha256:" + NEW + "\nimage: redis@sha256:" + NEW + "\n"
    assert postgres_images(text) == []
