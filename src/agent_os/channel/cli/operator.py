"""운영자 명령(`agent-os operator ...`). `system-admin` 과 `rotate-key` 둘이다.

`rotate-key` 는 로그인 쿠키의 서명 키를 새 난수로 바꾼다(ADR 0062 결정 "서명 키"). 데이터베이스에
닿는 방식은 `system-admin` 과 같고 비밀번호는 받지 않는다.

시스템 관리자는 서버에서 이 명령으로 만든다(ADR 0062 결정 "첫 계정"). 같은 명령이 만들기와 비밀번호
다시 정하기를 함께 한다. 한 데이터베이스 트랜잭션 안에서 시스템 관리자의 줄을 잠가 읽고 갈래를
정한다.

- 시스템 관리자가 없고 그 이름의 계정도 없으면 만든다.
- 그 이름의 시스템 관리자가 있으면 비밀번호를 다시 정하고 틀린 횟수와 잠금을 지우고 그 계정의
  로그인을 모두 끊는다.
- 다른 이름의 시스템 관리자가 있으면 바꾸지 않고 그 이름을 적어 멈춘다. 시스템 관리자는 하나뿐이다.
- 시스템 관리자는 없는데 그 이름의 관리자 단계 계정이 있으면 바꾸지 않고 멈춘다.

비밀번호는 명령의 인자로 받지 않는다(프로세스 목록과 셸 이력에 남는다). 표준 입력이 터미널이면
글자를 보이지 않고 두 번 받아 서로 견주고(숨길 수 없으면 받지 않고 멈춘다), 터미널이 아니면 첫 줄
하나를 받는다(줄 끝의 개행만 뗀다).
스크립트와 e2e가 파이프로 넣기 위해서다. 비밀번호와 그 해시는 어느 출력에도, 로그인 기록의 어느
줄에도 싣지 않는다(원칙 V). 해시는 데이터베이스에 닿기 전에 만들어, 느린 해시가 연결을 쥐고 있지
않게 한다.

두 계정이 같은 이름을 동시에 넣으면 시스템 관리자에만 거는 유일 색인이 하나를 `"taken"`으로 막고,
진 쪽은 같은 트랜잭션에서 다시 읽어 이긴 쪽의 줄을 보고 갈래를 다시 정한다.
"""

from __future__ import annotations

import os
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from getpass import GetPassWarning
from typing import TextIO

from agent_os.channel.cli.main import EXIT_FAILED, EXIT_FINISHED
from agent_os.core.ports import Clock
from agent_os.http.accounts import (
    ACCOUNT_NAME_RULE_TEXT,
    AccountStore,
    AccountWork,
    Tier,
    fold_account_name,
    is_account_name,
)
from agent_os.http.logins import SIGNING_KEY_BYTES
from agent_os.http.passwords import PASSWORD_RULE_TEXT, hash_password, password_problem

PASSWORD_PROMPT = "비밀번호: "
CONFIRM_PROMPT = "비밀번호를 한 번 더: "
PASSWORD_MISMATCH_TEXT = "입력한 두 비밀번호가 다릅니다. 아무것도 바꾸지 않았습니다."
NO_PASSWORD_TEXT = (
    "표준 입력에서 비밀번호 한 줄을 읽지 못했습니다. 터미널에서 치거나, 파이프로 첫 줄에 비밀번호를"
    " 넣어 주십시오. 아무것도 바꾸지 않았습니다."
)
NOT_UTF8_TEXT = (
    "표준 입력이 UTF-8 글이 아닙니다. 비밀번호를 UTF-8로 넣어 주십시오. 아무것도 바꾸지 않았습니다."
)
CANNOT_HIDE_TEXT = (
    "터미널이 글자를 숨기지 못해 비밀번호를 받지 않았습니다. 터미널을 확인하거나, 파이프로 첫 줄에"
    " 비밀번호를 넣어 주십시오. 아무것도 바꾸지 않았습니다."
)
_NOT_CHANGED = "아무것도 바꾸지 않았습니다."


@dataclass(frozen=True)
class Refused:
    """명령이 데이터베이스에 닿기 전에 입력을 받아들이지 않은 까닭. 그대로 표준 오류에 찍는다."""

    text: str


def check_name(raw: str) -> str | Refused:
    """들어온 이름의 영문 대문자만 소문자로 바꾸고 이름 규칙에 댄다."""
    name = fold_account_name(raw)
    if is_account_name(name):
        return name
    return Refused(f"{ACCOUNT_NAME_RULE_TEXT}\n  {_NOT_CHANGED}")


def password_hash_of(stdin: TextIO, ask: Callable[[str], str]) -> str | Refused:
    """비밀번호를 받아 규칙에 대고 해시를 만든다. 받아들이지 않으면 까닭을 돌려준다.

    `ask` 는 글자를 보이지 않고 한 줄을 받는 함수(터미널에서는 `getpass.getpass`)다. 표준 입력이
    터미널이면 두 번 묻고, 아니면 `stdin` 의 첫 줄 하나를 읽는다.
    """
    password = _read_password(stdin, ask)
    if isinstance(password, Refused):
        return password
    if password_problem(password) is not None:
        return Refused(f"{PASSWORD_RULE_TEXT}\n  {_NOT_CHANGED}")
    return hash_password(password)


def _read_password(stdin: TextIO, ask: Callable[[str], str]) -> str | Refused:
    if stdin.isatty():
        # 터미널의 입력 표시를 끌 수 없으면 getpass 는 경고만 내고 글자가 보이는 입력으로 받는다.
        # 경고를 오류로 바꿔 입력을 받기 전에 멈춘다
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", GetPassWarning)
                first = ask(PASSWORD_PROMPT)
                second = ask(CONFIRM_PROMPT)
        except GetPassWarning:
            return Refused(CANNOT_HIDE_TEXT)
        if first != second:
            return Refused(PASSWORD_MISMATCH_TEXT)
        return first
    try:
        line = stdin.readline()
    except UnicodeDecodeError:
        # 예외의 글에는 읽던 바이트와 위치가 실려 비밀번호의 일부가 새므로 글을 싣지 않고 막는다
        return Refused(NOT_UTF8_TEXT)
    if not line:
        return Refused(NO_PASSWORD_TEXT)
    # 줄 끝의 개행만 뗀다. 윈도의 파이프가 붙이는 `\r\n` 도 한 개행으로 본다
    return line.removesuffix("\n").removesuffix("\r")


@dataclass(frozen=True)
class _Created:
    pass


@dataclass(frozen=True)
class _Reset:
    pass


@dataclass(frozen=True)
class _OtherSystemAdmin:
    name: str


@dataclass(frozen=True)
class _AdminTier:
    pass


type _Outcome = _Created | _Reset | _OtherSystemAdmin | _AdminTier


@dataclass(frozen=True)
class _NewAccount:
    name: str
    tier: Tier
    password_hash: str
    created_at: datetime


async def system_admin_command(
    name: str,
    password_hash: str,
    *,
    accounts: AccountStore,
    clock: Clock,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """시스템 관리자를 만들거나 비밀번호를 다시 정한다. 종료 코드를 돌려준다.

    `name` 은 이름 규칙을 지난 값이고 `password_hash` 는 규칙을 지난 비밀번호의 해시다. 데이터베이스
    예외는 잡지 않고 부르는 쪽(`main`)이 까닭만 싣는 글로 바꾼다.
    """
    now = clock.now()
    async with accounts.transaction() as work:
        outcome = await _decide(work, name, password_hash, now)
    match outcome:
        case _Created():
            stdout.write(f"시스템 관리자 {name} 계정을 만들었습니다.\n")
            return EXIT_FINISHED
        case _Reset():
            stdout.write(
                f"시스템 관리자 {name} 의 비밀번호를 다시 정했습니다."
                " 잠금을 풀고 이 계정의 로그인을 모두 끊었습니다.\n"
            )
            return EXIT_FINISHED
        case _OtherSystemAdmin(other):
            stderr.write(
                f"시스템 관리자는 이미 {other} 입니다. 시스템 관리자는 하나뿐이라 {name} 으로"
                " 바꾸지 않았습니다.\n"
                f"  맡은 사람이 바뀌었다면 {other} 의 비밀번호를 다시 정해 넘기십시오.\n"
            )
            return EXIT_FAILED
        case _AdminTier():
            stderr.write(
                f"{name} 은 관리자 단계의 계정입니다. 시스템 관리자로 바꾸지 않았습니다."
                " 다른 이름을 고르십시오.\n"
            )
            return EXIT_FAILED


ROTATED_TEXT = (
    "서명 키를 새로 만들어 바꿨습니다. 도는 `serve`는 10초 안에 새 키를 씁니다."
    " 10초가 지나면 옛 키로 서명한 짧은 로그인 쿠키는 받지 않지만, 갱신으로 로그인은 이어집니다."
)


async def rotate_key_command(*, accounts: AccountStore, clock: Clock, stdout: TextIO) -> int:
    """서명 키의 줄을 새 난수로 바꾸고 로그인 기록에 남긴 뒤 종료 코드를 돌려준다.

    옛 키는 남기지 않는다. 키 값은 어느 출력에도 기록에도 싣지 않는다(원칙 V). 데이터베이스 예외는
    잡지 않고 부르는 쪽(`main`)이 까닭만 싣는 글로 바꾼다.
    """
    now = clock.now()
    async with accounts.transaction() as work:
        await work.replace_signing_key(os.urandom(SIGNING_KEY_BYTES), at=now)
        await work.record("signing_key_rotated", at=now, account=None)
    stdout.write(f"{ROTATED_TEXT}\n")
    return EXIT_FINISHED


async def _decide(work: AccountWork, name: str, password_hash: str, now: datetime) -> _Outcome:
    """줄을 잠가 읽고 갈래를 정해 적는다. 같은 트랜잭션 안에서 둘이 겹치면 한 번 다시 읽는다."""
    # 두 번이면 충분하다. 첫 시도가 막히면(넣기가 "taken" 이거나, 두 조회 사이에 같은 이름의 시스템
    # 관리자가 커밋됐으면) 이긴 쪽의 줄이 이미 있어 둘째 시도는 읽기만 한다
    for _attempt in range(2):
        owner = await work.lock_system_admin()
        if owner is not None:
            if owner.name != name:
                return _OtherSystemAdmin(owner.name)
            await work.reset_password(name, password_hash=password_hash)
            await work.end_logins(name, at=now)
            await work.record("system_admin_set", at=now, account=name)
            return _Reset()
        existing = await work.lock(name)
        if existing is not None:
            if existing.tier == "admin":
                return _AdminTier()
            # 시스템 관리자를 먼저 읽은 뒤에 같은 이름의 시스템 관리자가 커밋됐다. 다음 바퀴가
            # 읽는다
            continue
        added = await work.add(
            _NewAccount(name=name, tier="system_admin", password_hash=password_hash, created_at=now)
        )
        if added != "taken":
            await work.record("system_admin_set", at=now, account=name)
            return _Created()
    raise RuntimeError("계정을 넣다 두 번 막혔다")
