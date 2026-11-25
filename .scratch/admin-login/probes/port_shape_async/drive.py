"""런타임 몫(port_shape_async). `run.py` 가 임시 사본의 `src` 를 `PYTHONPATH` 앞에 두고 띄운다.

받는 것: 환경 변수 `PORT_SHAPE_ASYNC_URL`(테스트 컨테이너에 `run.py` 가 만든 빈 데이터베이스의
`postgresql://…` 주소). 그 데이터베이스에 표 `accounts` 하나를 만들고, 임시 사본의 `agent_os.main`
에 붙인 조립 함수(`probe_scenario`)로 사례마다 어댑터를 지어 포트 자리에 넘겨 돌린다. 줄마다 `<종류>
<json>` 하나를 찍는다. 종류는 `ORIGIN`(가져온 `agent_os` 의 자리), `VERSION`(서버 판), `RESULT`(사례
하나), `DETAIL`(유일 제약 위반의 글)이다.

`DETAIL` 사례는 같은 이름을 두 번 넣어 서버가 낸 예외의 글과 사슬을 본다. 넣는 이름은 실행마다
무작위로 지어 소스 코드의 줄에 나오지 않는다. 그래서 역추적의 글에 그 이름이 있으면 소스가 아니라
예외의 글에서 온 것이다. 대조로 그 예외를 원인으로 이은 예외의 역추적에 이름이 실리는지도 본다.

`WORK` 줄은 트랜잭션 포트(`agent_os.http.account_work`)의 사례다. 셋이다.

- 겹침(`overlap`). 한 계정에 실패 적기(`record_failed_attempt`) 둘을 한 이벤트 루프에서 함께 돌린다.
  첫째가 줄을 읽은 뒤 견줌의 자리(`compare`)에서 `PAUSE` 초를 기다리고, 둘째는 첫째가 읽은 뒤에야
  트랜잭션을 연다(`asyncio.Event`). 그동안 셋째 연결(AUTOCOMMIT, 문장마다 새 트랜잭션이라
  `pg_stat_activity` 가 문장마다 새로 읽힌다)이 `WAIT_SQL` 로 이 데이터베이스에서 기다리는 잠금을
  `POLL` 초마다 훑는다. 둘째가 트랜잭션을 연 뒤 읽기를 받기까지의 시간(`second_wait`)과 첫째가
  끝나기 전에 둘째가 읽었는지도 찍는다. 모양마다 `REPEATS` 번이다.
- 되돌림(`rollback`). 횟수에 5를 더해 적고 같은 트랜잭션에서 다시 읽은 뒤 예외로 블록을 나온다.
  새 트랜잭션에서 다시 읽은 횟수를 찍는다. 대조로 예외 없이 나오는 판(`commit`)도 돈다.
- 연결 반납(`pool`). 사례를 다 돈 뒤 엔진의 연결 묶음에서 빌려 간 연결 수.

표와 데이터베이스는 지우지 않는다. 데이터베이스는 `run.py` 가 지운다.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import traceback
import uuid
from collections.abc import Awaitable, Callable

URL_ENV = "PORT_SHAPE_ASYNC_URL"
SCENARIOS = (
    "ga_walk",
    "na_property_walk",
    "na_factory_walk",
    "taken_core",
    "taken_injected",
    "taken_recognized",
    "taken_result",
    "untranslated_core",
    "untranslated_injected",
    "untranslated_recognized",
)
DDL = """
CREATE TABLE accounts (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    tier text NOT NULL,
    password_hash text,
    failures integer NOT NULL,
    locked_until timestamptz,
    CONSTRAINT accounts_name_key UNIQUE (name)
)
"""

PAUSE = 0.5
POLL = 0.05
REPEATS = 3
OVERLAP_STYLES = ("context", "class", "unlocked")
ROLLBACK_STYLES = ("context", "class")
WAIT_SQL = """
SELECT l.locktype, l.mode, a.wait_event_type, a.wait_event, a.query
FROM pg_locks AS l JOIN pg_stat_activity AS a ON a.pid = l.pid
WHERE NOT l.granted AND a.datname = current_database()
"""

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


def emit(kind: str, payload: Json) -> None:
    print(f"{kind} {json.dumps(payload, ensure_ascii=False)}", flush=True)


def chain(error: BaseException) -> list[BaseException]:
    seen: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and all(current is not item for item in seen):
        seen.append(current)
        current = current.__cause__ or current.__context__
    return seen


def sqlstate(error: BaseException) -> str | None:
    for item in chain(error):
        state = getattr(item, "sqlstate", None)
        if isinstance(state, str):
            return state
    return None


def text_attrs(error: BaseException, name: str) -> list[str]:
    found: list[str] = []
    for item in chain(error):
        value = getattr(item, name, None)
        if isinstance(value, str):
            found.append(value)
    return found


async def scenario(run: Callable[[str, str], Awaitable[object]], url_text: str, name: str) -> None:
    try:
        value = await run(url_text, name)
    except Exception as error:  # 사례의 실패는 그 종류와 오류 번호로 적는다
        emit(
            "RESULT",
            {
                "scenario": name,
                "error": type(error).__name__,
                "error_module": type(error).__module__,
                "sqlstate": sqlstate(error),
            },
        )
        return
    emit("RESULT", {"scenario": name, "value": json.loads(json.dumps(value))})


async def detail(url_text: str) -> None:
    from agent_os.core.conflicts import NameTaken
    from sqlalchemy import insert
    from sqlalchemy.exc import IntegrityError

    from agent_os.adapters.postgres.accounts import PostgresAccounts, accounts
    from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url
    from agent_os.http.accounts import Draft

    url = parse_database_url(url_text)
    if url is None:
        raise RuntimeError("주소를 읽지 못했다")
    database = PostgresDatabase(url, notice=lambda _message: None)
    raw_marker = f"dup_{uuid.uuid4().hex[:12]}"
    port_marker = f"dup_{uuid.uuid4().hex[:12]}"
    try:
        statement = insert(accounts).values(name=raw_marker, tier="admin", failures=0)
        raw: IntegrityError | None = None
        for _ in range(2):
            try:
                async with database.engine.begin() as connection:
                    await connection.execute(statement)
            except IntegrityError as error:
                raw = error
        store = PostgresAccounts(database.engine)
        await store.add(Draft(name=port_marker, tier="admin"))
        port_error: NameTaken | None = None
        try:
            await store.add(Draft(name=port_marker, tier="admin"))
        except NameTaken as error:
            port_error = error
    finally:
        await database.close()
    if raw is None:
        emit("DETAIL", {"raw": None})
        return
    raw_text = str(raw)
    try:
        raise RuntimeError("원인을 이은 대조") from raw
    except RuntimeError as chained:
        chained_text = "".join(traceback.format_exception(chained))
    port_text = "" if port_error is None else "".join(traceback.format_exception(port_error))
    emit(
        "DETAIL",
        {
            "raw_type": f"{type(raw).__module__}.{type(raw).__name__}",
            "raw_sqlstate": sqlstate(raw),
            "raw_has_marker": raw_marker in raw_text,
            "raw_has_detail_word": "DETAIL" in raw_text,
            "raw_hides_parameters": "hide_parameters=True" in raw_text,
            "raw_shape": raw_text.replace(raw_marker, "<넣은 이름>"),
            "detail_attrs": [
                value.replace(raw_marker, "<넣은 이름>") for value in text_attrs(raw, "detail")
            ],
            "detail_attr_has_marker": any(
                raw_marker in value for value in text_attrs(raw, "detail")
            ),
            "chain_types": [
                f"{type(item).__module__}.{type(item).__name__}" for item in chain(raw)
            ],
            "chain_str_has_marker": [raw_marker in str(item) for item in chain(raw)],
            "chained_traceback_has_marker": raw_marker in chained_text,
            "port_error_seen": port_error is not None,
            "port_error_cause_none": port_error is not None and port_error.__cause__ is None,
            "port_error_context_none": port_error is not None and port_error.__context__ is None,
            "port_traceback_has_marker": port_marker in port_text,
            "port_message": "" if port_error is None else str(port_error),
        },
    )


async def seeded(database: object, prefix: str) -> str:
    """실패 0번인 계정 하나를 넣고 그 이름을 돌려준다."""
    from agent_os.adapters.postgres.accounts import PostgresAccounts
    from agent_os.adapters.postgres.database import PostgresDatabase
    from agent_os.http.accounts import Draft

    if not isinstance(database, PostgresDatabase):
        raise TypeError("데이터베이스 어댑터가 아니다")
    name = f"{prefix}_{uuid.uuid4().hex[:10]}"
    await PostgresAccounts(database.engine).add(Draft(name=name, tier="admin"))
    return name


async def overlap(database: object, observer: object, style: str, repeat: int) -> Json:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncEngine

    from agent_os.main import probe_attempt, probe_read_failures  # 임시 사본에만 있다

    if not isinstance(observer, AsyncEngine):
        raise TypeError("훑는 엔진이 아니다")
    name = await seeded(database, f"overlap_{style}")
    first_read = asyncio.Event()
    first_done = asyncio.Event()
    times: dict[str, float] = {}
    base = time.perf_counter()

    def stamp(key: str) -> None:
        times[key] = round(time.perf_counter() - base, 4)

    async def first_compare() -> None:
        stamp("first_read")
        first_read.set()
        await asyncio.sleep(PAUSE)

    async def second_compare() -> None:
        stamp("second_read")

    async def first() -> object:
        try:
            return await probe_attempt(database, style, name, first_compare)
        finally:
            stamp("first_done")
            first_done.set()

    async def second() -> object:
        await first_read.wait()
        stamp("second_start")
        result = await probe_attempt(database, style, name, second_compare)
        stamp("second_done")
        return result

    async def observe() -> list[Json]:
        samples: list[Json] = []
        await first_read.wait()
        async with observer.connect() as connection:
            while not first_done.is_set():
                rows = (await connection.execute(text(WAIT_SQL))).all()
                for locktype, mode, wait_type, wait_event, query in rows:
                    samples.append(
                        {
                            "locktype": str(locktype),
                            "mode": str(mode),
                            "wait_event_type": str(wait_type),
                            "wait_event": str(wait_event),
                            "for_update": "FOR UPDATE" in str(query),
                        }
                    )
                await asyncio.sleep(POLL)
        return samples

    first_result, second_result, samples = await asyncio.wait_for(
        asyncio.gather(first(), second(), observe()), timeout=30
    )
    final = await probe_read_failures(database, style, name)
    distinct = sorted({json.dumps(item, sort_keys=True) for item in samples})
    second_wait = times["second_read"] - times["second_start"]
    return {
        "case": "overlap",
        "style": style,
        "repeat": repeat,
        "first": json.loads(json.dumps(first_result)),
        "second": json.loads(json.dumps(second_result)),
        "final": final,
        "times": {key: value for key, value in sorted(times.items())},
        "second_wait": round(second_wait, 4),
        "second_read_before_first_done": times["second_read"] < times["first_done"],
        "wait_samples": len(samples),
        "waits": [json.loads(item) for item in distinct],
    }


async def rollback(database: object, style: str, *, abort: bool) -> Json:
    from agent_os.http.account_work import AbortedAfterWrite

    from agent_os.main import probe_read_failures, probe_write_then  # 임시 사본에만 있다

    name = await seeded(database, f"rollback_{style}")
    before = await probe_read_failures(database, style, name)
    returned: int | None = None
    seen_inside: int | None = None
    raised: str | None = None
    try:
        returned = await probe_write_then(database, style, name, abort=abort)
    except AbortedAfterWrite as error:
        seen_inside = error.seen_inside
        raised = f"{type(error).__module__}.{type(error).__name__}"
    after = await probe_read_failures(database, style, name)
    return {
        "case": "rollback" if abort else "commit",
        "style": style,
        "before": before,
        "returned": returned,
        "seen_inside": seen_inside,
        "raised": raised,
        "after": after,
    }


async def work_cases(url_text: str) -> None:
    from sqlalchemy.engine import make_url
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url

    url = parse_database_url(url_text)
    if url is None:
        raise RuntimeError("주소를 읽지 못했다")
    database = PostgresDatabase(url, notice=lambda _message: None)
    observer = create_async_engine(
        make_url(url_text).set(drivername="postgresql+asyncpg"),
        poolclass=NullPool,
        isolation_level="AUTOCOMMIT",
    )

    async def guarded(label: Json, case: Awaitable[Json]) -> None:
        try:
            value = await case
        except Exception as error:  # 사례 하나의 실패가 뒤 사례를 잃게 하지 않는다
            emit("WORK", {"case": "error", "label": label, "error": repr(error)})
            return
        emit("WORK", value)

    try:
        for repeat in range(REPEATS):
            for style in OVERLAP_STYLES:
                case = overlap(database, observer, style, repeat)
                await guarded(f"overlap {style} {repeat}", case)
        for style in ROLLBACK_STYLES:
            for abort in (True, False):
                await guarded(f"rollback {style} {abort}", rollback(database, style, abort=abort))
        pool = database.engine.pool
        checked = getattr(pool, "checkedout", None)
        emit(
            "WORK",
            {
                "case": "pool",
                "pool": type(pool).__name__,
                "checked_out": checked() if callable(checked) else None,
            },
        )
    finally:
        await observer.dispose()
        await database.close()


async def main() -> int:
    from sqlalchemy import text
    from sqlalchemy.engine import make_url
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    import agent_os
    from agent_os.main import probe_scenario  # 임시 사본에만 있다

    emit("ORIGIN", {"agent_os": agent_os.__file__})
    url_text = os.environ[URL_ENV]
    engine = create_async_engine(
        make_url(url_text).set(drivername="postgresql+asyncpg"),
        poolclass=NullPool,
        hide_parameters=True,
    )
    try:
        async with engine.begin() as connection:
            await connection.execute(text(DDL))
            version = (await connection.execute(text("SHOW server_version"))).scalar_one()
    finally:
        await engine.dispose()
    emit("VERSION", {"server_version": str(version)})
    for name in SCENARIOS:
        await scenario(probe_scenario, url_text, name)
    await detail(url_text)
    await work_cases(url_text)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
