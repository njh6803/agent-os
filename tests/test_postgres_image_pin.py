"""PostgreSQL 이미지의 digest 가 쓰는 자리마다 같은지 본다(ADR 0066, 명세 postgres-foundation).

테스트 컨테이너(`compose.test.yaml`)와 CI 의 service container(`.github/workflows/ci.yml`)는 같은
이미지를 쓰는 약속이다. 한 자리만 올리면 이 PC 의 시험과 CI 의 시험이 다른 PostgreSQL 에서 돈다.
단독 배포용 compose 가 PostgreSQL 을 들이면(티켓 02) 그 자리도 이 시험이 같이 본다.

글에서 `image:` 줄을 읽는 얕은 읽기다. YAML 을 풀지 않으므로 줄 앞에 `#` 이 붙은 주석의 줄은
건너뛰고, 한 줄에 쓴 `image: postgres@sha256:…` 만 본다. 여러 줄로 접은 값이나 앵커로 가져온 값은 못
본다.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "compose.test.yaml"
CI = ROOT / ".github" / "workflows" / "ci.yml"

_IMAGE = re.compile(r"^[ \t]*-?[ \t]*image:[ \t]*(?P<value>[^\s#]+)", re.MULTILINE)
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


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


def pin_problems(compose_text: str, ci_text: str) -> list[str]:
    """두 자리의 digest 가 같지 않은 까닭들. 비어 있으면 같다.

    훑은 범위가 비면(이미지 줄을 하나도 못 읽으면) 같다고 하지 않고 까닭으로 센다. 경로나 읽기가
    틀려도 위반 0 으로 조용히 초록이 되는 일을 막으려는 것이다.
    """
    composed = postgres_images(compose_text)
    if len(composed) != 1:
        return [f"compose.test.yaml 의 PostgreSQL 이미지는 하나여야 한다: {len(composed)}개"]
    pinned = digest_of(composed[0])
    if pinned is None:
        return [f"compose.test.yaml 의 이미지에 digest 가 없다: {composed[0]}"]
    in_ci = postgres_images(ci_text)
    if not in_ci:
        return ["ci.yml 에 PostgreSQL service container 가 하나도 없다"]
    return [
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
CI_SAMPLE = """\
jobs:
  python:
    services:
      postgres:
        image: postgres@sha256:{digest}
"""
OLD = "a" * 64
NEW = "b" * 64


def test_이_저장소의_PostgreSQL_이미지는_테스트_컨테이너와_CI_가_같은_digest다() -> None:
    compose_text = COMPOSE.read_text(encoding="utf-8")
    ci_text = CI.read_text(encoding="utf-8")
    assert len(postgres_images(compose_text)) == 1
    ci_images = postgres_images(ci_text)
    missing = f"ci.yml 에 PostgreSQL service container 가 없다 ({len(ci_images)}개)"
    assert len(ci_images) >= 1, missing
    assert pin_problems(compose_text, ci_text) == []


def test_같은_digest_면_문제가_없다() -> None:
    assert pin_problems(COMPOSE_SAMPLE.format(digest=OLD), CI_SAMPLE.format(digest=OLD)) == []


def test_CI_의_digest_만_다르면_잡는다() -> None:
    problems = pin_problems(COMPOSE_SAMPLE.format(digest=OLD), CI_SAMPLE.format(digest=NEW))
    assert problems == [
        f"ci.yml 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: postgres@sha256:{NEW}"
    ]


def test_compose_의_digest_만_다르면_잡는다() -> None:
    problems = pin_problems(COMPOSE_SAMPLE.format(digest=NEW), CI_SAMPLE.format(digest=OLD))
    assert problems == [
        f"ci.yml 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: postgres@sha256:{OLD}"
    ]


def test_CI_에_PostgreSQL_service_container_가_없으면_잡는다() -> None:
    ci_without = "jobs:\n  python:\n    steps:\n      - run: echo\n"
    assert pin_problems(COMPOSE_SAMPLE.format(digest=OLD), ci_without) == [
        "ci.yml 에 PostgreSQL service container 가 하나도 없다"
    ]


def test_CI_의_이미지가_태그만_쓰면_잡는다() -> None:
    ci_tag = CI_SAMPLE.replace("postgres@sha256:{digest}", "postgres:18")
    assert pin_problems(COMPOSE_SAMPLE.format(digest=OLD), ci_tag) == [
        "ci.yml 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: postgres:18"
    ]


def test_CI_의_service_container_가_여럿이면_하나라도_다르면_잡는다() -> None:
    ci_two = CI_SAMPLE.format(digest=OLD) + f"      second:\n        image: postgres@sha256:{NEW}\n"
    problems = pin_problems(COMPOSE_SAMPLE.format(digest=OLD), ci_two)
    assert problems == [
        f"ci.yml 의 PostgreSQL 이미지가 compose.test.yaml 과 다르다: postgres@sha256:{NEW}"
    ]


def test_compose_에서_이미지를_읽지_못하면_같다고_하지_않는다() -> None:
    """읽은 범위가 비면 위반 0 으로 초록이 되지 않게 까닭으로 센다."""
    assert pin_problems("services: {}\n", CI_SAMPLE.format(digest=OLD)) == [
        "compose.test.yaml 의 PostgreSQL 이미지는 하나여야 한다: 0개"
    ]


def test_compose_의_이미지에_digest_가_없으면_잡는다() -> None:
    compose_tag = COMPOSE_SAMPLE.replace("postgres@sha256:{digest}", "postgres:18")
    assert pin_problems(compose_tag, CI_SAMPLE.format(digest=OLD)) == [
        "compose.test.yaml 의 이미지에 digest 가 없다: postgres:18"
    ]


def test_주석에_쓴_이미지는_읽지_않고_다른_이미지는_건너뛴다() -> None:
    text = "# image: postgres@sha256:" + NEW + "\nimage: redis@sha256:" + NEW + "\n"
    assert postgres_images(text) == []
