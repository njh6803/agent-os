"""패키지 A 의 시험이 쓰는 픽스처. 공용 도우미에 A 의 마이그레이션 함수와 접두를 넘겨 받는다."""

from __future__ import annotations

from pkg_a.database import upgrade
from tests.database import database_fixture, template_fixture

PREFIX = "toy_a"

template_database = template_fixture(PREFIX, upgrade)
database = database_fixture(PREFIX, upgrade)
