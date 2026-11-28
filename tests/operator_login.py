"""실제 `serve` 프로세스를 미는 시험이 운영자로 로그인하는 길.

운영자 경로는 로그인 쿠키로만 열린다(공유 토큰은 걷혔다). 그래서 실제 `serve` 를 띄우는 시험은 서버
명령(`operator system-admin`)으로 시스템 관리자 계정을 만들고, 로그인 경로를 HTTP 로 불러 받은
쿠키를 `Cookie` 머리로 직접 싣는다. 가짜 계정 저장소를 쓰는 `ASGITransport` 시험은 이 길을 타지
않고 `tests/fake_accounts.py` 의 `operator_cookie()` 를 쓴다.
"""

import os
import subprocess
import sys
from pathlib import Path

from httpx import Client
from tools.database_for_tests import ScopedDatabase

from agent_os.http.login_tokens import ACCESS_COOKIE, REFRESH_COOKIE
from agent_os.main import DATABASE_URL_ENV

OPERATOR_NAME = "root.kim"
OPERATOR_PASSWORD = "Pw-canary-9!"


def create_system_admin(root: Path, database: ScopedDatabase) -> None:
    """서버 명령(`operator system-admin`)으로 시스템 관리자 계정을 만든다. 비밀번호는 파이프로
    넣는다(표준 입력이 터미널이 아니다). 어느 출력에도 비밀번호가 실리지 않아야 한다."""
    env = {**os.environ, "PYTHONUTF8": "1", DATABASE_URL_ENV: database.text()}
    result = subprocess.run(
        [sys.executable, "-m", "agent_os.main", "operator", "system-admin", OPERATOR_NAME],
        cwd=root,
        input=f"{OPERATOR_PASSWORD}\n",
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, f"계정을 만들지 못했다: {result.stderr}"
    assert OPERATOR_PASSWORD not in result.stdout + result.stderr


def log_in(client: Client) -> str:
    """로그인 경로를 HTTP 로 불러 받은 두 쿠키를 `Cookie` 머리 한 줄로 만든다.

    실제 `serve` 는 평문 `http` 라 httpx 가 `Secure` 쿠키를 다음 요청에 싣지 않는다. 그래서 응답의
    `Set-Cookie` 에서 값을 꺼내 머리로 직접 싣는다. 쿠키 통은 비워, 머리만이 길이 되게 한다.
    """
    response = client.post(
        "/auth/login", json={"name": OPERATOR_NAME, "password": OPERATOR_PASSWORD}
    )
    assert response.status_code == 204, f"로그인이 {response.status_code} 로 답했다"
    pairs = [line.partition(";")[0] for line in response.headers.get_list("set-cookie")]
    sent = [pair for pair in pairs if pair.startswith((f"{ACCESS_COOKIE}=", f"{REFRESH_COOKIE}="))]
    names = [pair.partition("=")[0] for pair in pairs]
    assert len(sent) == 2, f"로그인 쿠키가 둘이 아니다: {names}"
    client.cookies.clear()
    return "; ".join(sent)
