"""장난감 시험 묶음의 뿌리 conftest. 저장소의 `tests/conftest.py` 자리다.

`database_url` 하나만 여기 둔다. 두 패키지의 시험이 같은 픽스처를 받아, 서버를 쓸 수 없을 때 같은
한 줄로 실패한다.

측정용으로만 있는 것이 하나다. `CLONE_PROBE_DUMP_AFTER`(초)를 주면 그 시간이 지나도 프로세스가 살아
있을 때 모든 스레드의 스택을 표준 오류에 찍는다. pytest 가 끝나지 않고 멈춘 실행이 한 번 있었고,
멈춘 자리를 보려는 것이다. 주 프로세스와 xdist 작업자 모두에서 건다.
"""

from __future__ import annotations

import faulthandler
import os
import sys

from tests.database import database_url_fixture

DUMP_ENV = "CLONE_PROBE_DUMP_AFTER"

if os.environ.get(DUMP_ENV) and sys.__stderr__ is not None:
    faulthandler.dump_traceback_later(float(os.environ[DUMP_ENV]), file=sys.__stderr__)

database_url = database_url_fixture()
