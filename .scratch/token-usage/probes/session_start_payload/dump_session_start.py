"""탐침 SessionStart 훅. 받은 입력과 그 순간의 환경 일부를 `run.sh` 가 넘긴 파일에 한 줄씩 덧붙인다.

티켓 04(`.scratch/token-usage/issues/04-session-start-hook.md`)가 대화형 세션과 `claude -p` 세션을
가를 칸이 페이로드에 있는지 보려고 짓는다. 페이로드는 통째로 적는다(세션 ID, 트랜스크립트 경로,
작업 폴더, 출처, 모델 같은 값이라 비밀이 없다).

환경 변수는 이름만 적고(값에 토큰이 있을 수 있다, 원칙 V), 세션의 종류를 가를 후보인 `SAFE` 의
값만 적는다. 계정은 값을 적지 않는다. `~/.claude.json` 의 `oauthAccount` 에 두 키가 있는지와,
환경의 `CLAUDE_CODE_ACCOUNT_UUID`·`CLAUDE_CODE_USER_EMAIL` 이 그 두 값과 같은지의 참거짓만
적는다(대기열 272). 둘째 인자는 갈래의 이름표다.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SAFE = (
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_SESSION_ATTENDED",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_SIMPLE",
    "CLAUDECODE",
    "AI_AGENT",
    "CLAUDE_CODE_REMOTE",
    # `tools/canary.py` 가 띄우는 세션에 붙이는 헤드리스 표지. 그 세션의 훅까지 전해지는지 본다.
    "AGENT_OS_HEADLESS",
)


def account_facts() -> dict[str, bool | None]:
    """`~/.claude.json` 의 계정 두 키가 있는지와 환경 변수가 그 값과 같은지. 읽지 못하면 None."""
    try:
        data = json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"read": None}
    account = data.get("oauthAccount")
    if not isinstance(account, dict):
        return {"read": True, "has_oauth_account": False}
    uuid = account.get("accountUuid")
    email = account.get("emailAddress")
    env_uuid = os.environ.get("CLAUDE_CODE_ACCOUNT_UUID")
    env_email = os.environ.get("CLAUDE_CODE_USER_EMAIL")
    return {
        "read": True,
        "has_oauth_account": True,
        "has_account_uuid": isinstance(uuid, str),
        "has_email": isinstance(email, str),
        "env_uuid_present": env_uuid is not None,
        "env_uuid_equals_file": env_uuid is not None and env_uuid == uuid,
        "env_email_present": env_email is not None,
        "env_email_equals_file": env_email is not None and env_email == email,
    }


def main() -> int:
    out = Path(sys.argv[1])
    label = sys.argv[2] if len(sys.argv) > 2 else ""
    payload = json.loads(sys.stdin.buffer.read())
    entry = {
        "label": label,
        "payload": payload,
        "env_names": sorted(
            name for name in os.environ if name.startswith(("CLAUDE", "AI_AGENT", "ANTHROPIC"))
        ),
        "env_values": {name: os.environ.get(name) for name in SAFE},
        "account": account_facts(),
    }
    with out.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
