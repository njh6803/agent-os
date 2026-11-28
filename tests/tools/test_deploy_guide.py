"""단독 배포 안내(`deploy/standalone/README.md`)가 배포 파일 묶음의 틀과 어긋나지 않는지 보는 저장소
상태 시험.

안내는 운영자가 따라 치는 명령과 채울 파일 이름을 적는다. 그 이름과 소유가 틀(compose 파일, 프록시
설정, 위젯 미리보기 페이지 설정, Dockerfile)과 어긋나면 운영자가 안내대로 하고도 컨테이너가 서지
않는다(예: 키의 그룹이 컨테이너가 도는 사용자와 다르면 프록시나 위젯 미리보기 페이지가 시작에서
끝난다). 안내를 쓴 티켓이 이 PC의 리눅스 Docker에서 명령을 돌려 본 결과는 일지에 있고, 여기서는
Docker 없이 그 정합이 깨지지 않는지만 잠근다.
"""

from __future__ import annotations

import re
import tarfile
import tomllib
from pathlib import Path

import pytest
from tools.release import build_bundle

from agent_os.adapters.postgres.database import (
    DEFAULT_RETRY_SECONDS,
    Alignment,
    Failure,
    already_current_text,
    close_text,
    misaligned_text,
    retry_notice,
    unexpected_text,
    unreached_text,
    upgrade_failed_text,
    upgraded_text,
)
from agent_os.http.login_tokens import (
    IDLE_MINUTES_ENV,
    TOKEN_MINUTES_ENV,
    TOTAL_MINUTES_ENV,
    read_login_durations,
)
from agent_os.main import NO_DATABASE_URL_DIAGNOSTIC, UNREADABLE_DATABASE_URL_DIAGNOSTIC
from widget_admin import database as widget_database
from widget_admin import main as widget_main

REPO = Path(__file__).resolve().parents[2]
STANDALONE = REPO / "deploy" / "standalone"
GUIDE = STANDALONE / "README.md"

# 명세 "배포 안내"가 늘어놓은 항목과 위 절들이 넘긴 문장에서 안내가 반드시 가져야 할 낱말. 낱말마다
# 그 낱말이 지키는 항목을 적는다.
REQUIRED: dict[str, str] = {
    "28.3.3": "지원하는 Docker Engine 의 최소 판",
    "2.20.2": "지원하는 Docker Compose 의 최소 판",
    "DOCKER_INSECURE_NO_IPTABLES_RAW": "Docker 문서의 경고 한 문장",
    "28.0.0": "Docker 문서의 경고 다른 한 문장",
    "rootless": "rootless 모드에서는 재지 않았다는 말",
    "firewalld": "firewalld 에서는 재지 않았다는 말",
    "ufw": "ufw 에서는 재지 않았다는 말",
    "Podman": "0.1 판의 범위 밖",
    "ARM": "0.1 판의 범위 밖",
    "1.6GiB": "서버의 메모리",
    "A 레코드": "도메인에는 IPv4 주소만 등록할 것",
    "AAAA": "IPv6 주소를 등록하면 닿지 못한다는 말",
    "userland-proxy": "0.0.0.0 을 지우면 IPv6 방문자가 주소 하나로 뭉치는 것",
    "chmod 600 .env": "환경 변수 파일은 운영자만 읽게 둘 것",
    "root:101": "프록시 키 파일의 소유",
    "root:10001": "위젯 미리보기 페이지 개인 키의 소유",
    "openssl req -x509": "스스로 서명한 인증서를 만드는 명령",
    "ssh -L 3000:127.0.0.1:3000": "관리 화면에 닿는 SSH 포트 포워딩",
    "docker compose up -d": "띄우기",
    "docker compose ps": "컨테이너 상태 확인",
    "Ready": "관리 화면이 떴는지는 기록의 Ready 줄이 아니라 상태 확인으로 본다는 말",
    "docker compose restart serve widget portal": "사이트 파일을 고친 뒤 다시 띄울 것",
    "nginx -c /etc/agent-os/proxy/nginx.conf -t": "프록시 설정을 고친 뒤 먼저 문법을 볼 것",
    "-s reload": "프록시 설정을 고친 뒤 다시 읽힐 것",
    "request_chars": "요청 글자 수를 크게 올리면 413 이 먼저 답할 수 있다는 것",
    "413": "요청 글자 수를 크게 올리면 413 이 먼저 답할 수 있다는 것",
    "약 10초": "컨테이너를 다시 만들거나 판을 올린 직후",
    "user:": "compose 에 user 를 더하지 말 것",
    "npx": "인터넷이 막힌 곳에서 npx 로 띄우는 MCP 서버가 서지 않는 것",
    "10001:10001": "바인드 마운트로 바꿀 때 두 폴더의 소유",
    "docker save": "인터넷이 막힌 곳의 반입",
    "docker load": "인터넷이 막힌 곳의 반입",
    "sha256sum": "인터넷이 막힌 곳의 반입의 해시 대조",
    "docker image inspect": "대조할 해시가 이미지의 ID 라는 것",
    "100회": "Docker Hub 의 받는 횟수 제한(로그인하지 않은 때)",
    "200회": "Docker Hub 의 받는 횟수 제한(무료 개인 계정)",
    "올릴 때 할 일": "판을 바꿀 때 먼저 노트의 그 절을 본다는 것",
    "AGENT_OS_VERSION": "끝자리만 오른 판은 한 줄만 바꾼다는 것",
    "새 이미지의 예시 플러그인으로 갱신되지 않고": "플러그인 볼륨은 처음 붙을 때만 채워진다는 것",
    "calc": "틀의 에이전트를 운영자의 에이전트로 바꿀 것",
    "docker compose ps -a": "migrate 는 끝난 뒤 ps -a 에 Exited (0) 으로 남는다는 것",
    "docker compose logs migrate": "migrate 가 멈춘 까닭을 보는 명령",
    "docker volume rm agent-os_database": "처음 띄우기가 끊긴 배치의 데이터베이스 볼륨 지우기",
    "AGENT_OS_DATABASE_PASSWORD=unused": "인터넷이 되는 PC 의 두 명령에만 붙이는 값",
    "agent-os-postgres:local": "PostgreSQL 이미지를 태그로 옮기는 것",
    "이 판보다 새롭습니다": "표를 바꾼 판에서 앞의 판으로 되돌리면 migrate 가 멈춘다는 것",
    "unset AGENT_OS_DATABASE_PASSWORD COMPOSE_ENV_FILES": "비밀번호 바꾸기의 첫 줄",
    "\\password agent_os\"' &&": "비밀번호 바꾸기가 평문을 문장에 싣지 않는 셋째 줄",
    "ALTER ROLE": "비밀번호를 문장에 넣어 바꾸면 거절된 문장이 평문째 로그에 남는다는 것",
    "WIDGET_ADMIN_DATABASE_PASSWORD": "위젯 쪽 데이터베이스 비밀번호 칸",
    "agent-os_widget-database": "위젯 쪽 데이터를 담는 볼륨",
    "docker volume rm agent-os_widget-database": "처음 띄우기가 끊긴 배치의 위젯 쪽 볼륨 지우기",
    "docker compose logs widget-admin-migrate": "widget-admin-migrate 가 멈춘 까닭을 보는 명령",
    "WIDGET_ADMIN_DATABASE_PASSWORD=unused": "인터넷이 되는 PC 의 두 명령에만 붙이는 위젯 쪽 값",
    "unset WIDGET_ADMIN_DATABASE_PASSWORD COMPOSE_ENV_FILES": "위젯 쪽 비밀번호 바꾸기의 첫 줄",
    "\\password widget_admin\"' &&": "위젯 쪽 비밀번호 바꾸기가 평문을 문장에 싣지 않는 셋째 줄",
    "  widget-admin-postgres:\n    image: agent-os-postgres:local": (
        "덮어쓰기 파일에서 위젯 쪽 PostgreSQL 이 같은 태그를 쓰는 것"
    ),
    "위젯 설정을 받아 오지 못했습니다.": "위젯 쪽 비밀번호를 바꾸는 동안 위젯이 보이는 글",
}

# 운영자는 쓰지 않는 저장소 안의 말. 안내에 새면 운영자가 뜻을 알 수 없다.
INTERNAL_WORDS = (
    ".scratch",
    "ADR",
    "티켓",
    "docs/",
    "release-image",
    "명세",
    "CONTEXT.md",
    "probes",
    "세션",
)


# 13절(문제 해결)이 꼭 가져야 할 낱말(명세 connection-check Testing Decisions 의 여섯째).
# 4절에 이미 있는 낱말(`Exited (0)`, `Ready`, 위젯의 종료 1)은 안내 전체에서 찾으면 13절에서
# 빠져도 초록이므로, 이 낱말들은 13절만 잘라 찾는다.
SECTION_13_TITLE = "## 13. 문제 해결"
SECTION_13_REQUIRED: dict[str, str] = {
    "docker compose ps --all": "먼저 칠 명령, 끝난 컨테이너까지 보인다",
    "docker compose logs": "서비스 하나의 기록을 보는 명령",
    "healthy": "뜬 것으로 읽는 상태",
    "Exited (0)": "migrate 가 일을 마친 상태는 고장이 아니라는 것",
    "Restarting": "볼 것으로 읽는 상태",
    "Created": "볼 것으로 읽는 상태",
    "Ready": "관리 화면은 Ready 줄 뒤에도 실패할 수 있어 상태로 본다는 것",
    "종료 1": "위젯이 종료 1 로 끝났을 때의 뜻",
    "사이트 파일": "위젯이 종료 1 로 끝나는 까닭",
    "docker compose exec serve agent-os --version": "떠 있는 판을 읽는 명령",
    "AGENT_OS_VERSION": "다음에 띄울 판이라 떠 있는 판과 다를 수 있다는 것",
    "docker compose config": "남에게 보내면 안 되는 출력 하나",
    "docker inspect": "남에게 보내면 안 되는 출력 둘",
    "Application startup failed. Exiting.": "웹 서버가 붙이는 줄이고 까닭이 아니라는 것",
    "ERROR:": "웹 서버가 서버 시작에서 멈출 때 글 앞에 붙이는 머리",
    "접속 확인": "서버는 떴는데 에이전트가 답하지 않을 때 볼 화면",
    "붙지 못함": "접속 확인이 보이는 결과",
    "서버에 닿지 못했다": "붙지 못함의 글을 읽는 예, 꺼진 모델 서버",
    "키를 받아들이지 않았다(HTTP 401)": "붙지 못함의 글을 읽는 예, 틀린 키",
    "(HTTP 401 Unauthorized)": "붙지 못함의 글을 읽는 예, 원격 MCP 서버의 토큰 불일치",
    "20초": "처음 띄울 때 내려받는 stdio 서버는 20초를 넘기면 붙지 못함으로 보일 수 있다는 것",
    "헤더": "원격 MCP 서버의 토큰은 주소가 아니라 헤더에 둔다는 것",
    "widget-admin-migrate": "위젯 쪽 migrate 의 상태 읽기",
    "docker compose logs widget-admin": "위젯 관리 서버가 찍은 글을 보는 명령",
    "widget-admin-postgres:5432/widget_admin": "위젯 쪽 글의 자리",
}

# 제품이 멈출 때와 다시 시도할 때 찍는 글의 갈래(명세 postgres-foundation "멈출 때의 글"의
# 표). 시험이 제품 코드에서 글을 가져오는 함수(`제품의_멈출_때의_글`)가 이 갈래를 빠짐없이
# 내는지 지킨다.
STOP_TEXT_LABELS = (
    "변수가 없거나 비었다",
    "읽지 못했다",
    "다시 시도한다",
    "로그인 증표의 수명이 범위 밖이다",
    "로그인 쉬는 시간이 범위 밖이다",
    "로그인 총 시간이 범위 밖이다",
    "로그인 증표의 수명이 쉬는 시간 이상이다",
    "닿지 못했다",
    "비밀번호",
    "접속을 허락하지 않았다",
    "데이터베이스 없음",
    "그 밖",
    "표가 뒤처졌다",
    "표가 더 새롭다",
    "확인하다 멈췄다",
    "닫다 실패했다",
    "올렸다",
    "이미 마지막 판이다",
    "올리다 실패했다",
)


def 없는_항목(guide: str) -> list[str]:
    """안내에 없는 필수 낱말과 그 낱말이 지키는 항목."""
    return [f"{word}: {item}" for word, item in REQUIRED.items() if word not in guide]


def 열세째_절(guide: str) -> str:
    """안내에서 13절(제목부터 다음 절 앞이나 끝까지). 13절이 없으면 빈 글."""
    start = guide.find(SECTION_13_TITLE)
    if start < 0:
        return ""
    after = start + len(SECTION_13_TITLE)
    following = re.search(r"^## ", guide[after:], flags=re.MULTILINE)
    return guide[start:] if following is None else guide[start : after + following.start()]


def 네째_절(guide: str) -> str:
    """안내에서 4절(제목부터 5절 앞까지)."""
    start = guide.index("## 4. 띄우기와 확인")
    return guide[start : guide.index("## 5. ", start)]


def 없는_13절_항목(guide: str) -> list[str]:
    """13절 안에 없는 필수 낱말과 그 낱말이 지키는 항목. 13절이 없으면 전부다."""
    section = 열세째_절(guide)
    return [f"{word}: {item}" for word, item in SECTION_13_REQUIRED.items() if word not in section]


def 로그인_설정의_글(env: dict[str, str]) -> str:
    """유지 시간 설정을 틀리게 준 `serve` 가 찍는 글. 맞는 값이면 글이 없으므로 시험이 실패한다."""
    result = read_login_durations(env)
    assert isinstance(result, str), env
    return result


def 제품의_멈출_때의_글() -> dict[str, str]:
    """제품이 멈출 때와 다시 시도할 때 찍는 글. 갈래마다 제품 코드가 글을 짓는 자리에서 가져온다.

    값이 들어가는 자리(주소, 까닭, 판)는 `<자리>`, `<까닭>`, `<판>` 으로 채운다. 안내의 표가 같은
    자리 표시로 그 글을 싣는다. 다시 시도하는 시간은 기본 값(30초)이고 안내가 그 숫자를 적는다.
    """
    place, reason, revision, value = "<자리>", "<까닭>", "<판>", "<값>"
    seconds = DEFAULT_RETRY_SECONDS
    return {
        "변수가 없거나 비었다": NO_DATABASE_URL_DIAGNOSTIC,
        "읽지 못했다": UNREADABLE_DATABASE_URL_DIAGNOSTIC,
        "다시 시도한다": retry_notice(place, seconds),
        "로그인 증표의 수명이 범위 밖이다": 로그인_설정의_글({TOKEN_MINUTES_ENV: value}),
        "로그인 쉬는 시간이 범위 밖이다": 로그인_설정의_글({IDLE_MINUTES_ENV: value}),
        # 총 시간의 아래 한도는 쉬는 시간의 값을 따라간다. 기본값(30분)이 아닌 600분으로 만들어,
        # 글이 아래 한도를 고정값으로 찍으면 안내의 자리표시자와 어긋나게 한다
        "로그인 총 시간이 범위 밖이다": 로그인_설정의_글(
            {IDLE_MINUTES_ENV: "600", TOTAL_MINUTES_ENV: value}
        ).replace("600분 이상", "<쉬는 시간>분 이상"),
        "로그인 증표의 수명이 쉬는 시간 이상이다": 로그인_설정의_글(
            {TOKEN_MINUTES_ENV: "10", IDLE_MINUTES_ENV: "10"}
        ).replace("10분", "<분>분"),
        "닿지 못했다": unreached_text(Failure.TRANSIENT, place, reason, seconds),
        "비밀번호": unreached_text(Failure.PASSWORD, place, reason, seconds),
        "접속을 허락하지 않았다": unreached_text(Failure.NOT_ALLOWED, place, reason, seconds),
        "데이터베이스 없음": unreached_text(Failure.NO_DATABASE, place, reason, seconds),
        "그 밖": unreached_text(Failure.OTHER, place, reason, seconds),
        "표가 뒤처졌다": misaligned_text(Alignment.BEHIND, revision, revision),
        "표가 더 새롭다": misaligned_text(Alignment.AHEAD, revision, revision),
        "확인하다 멈췄다": unexpected_text(place, reason),
        "닫다 실패했다": close_text(place, reason),
        "올렸다": upgraded_text(revision, revision),
        "이미 마지막 판이다": already_current_text(revision),
        "올리다 실패했다": upgrade_failed_text(reason, revision),
    }


def 위젯_관리_서버의_멈출_때의_글() -> dict[str, str]:
    """위젯 관리 서버가 멈출 때와 다시 시도할 때 찍는 글. 제품의 글과 같은 자리 표시로 채운다.

    갈래 이름은 Agent OS 쪽과 같아 한 사전에 넣을 수 없다. 그래서 따로 모아 같은 `없는_글`로 견준다.
    글자가 같은 열둘은 Agent OS 쪽 행에, 다른 셋(변수가 없거나 비었다, 읽지 못했다, 표가 뒤처졌다)은
    위젯 쪽 행에 맞는다.
    """
    place, reason, revision = "<자리>", "<까닭>", "<판>"
    seconds = widget_database.DEFAULT_RETRY_SECONDS
    failure, alignment = widget_database.Failure, widget_database.Alignment
    return {
        "변수가 없거나 비었다": widget_main.NO_DATABASE_URL_DIAGNOSTIC,
        "읽지 못했다": widget_main.UNREADABLE_DATABASE_URL_DIAGNOSTIC,
        "다시 시도한다": widget_database.retry_notice(place, seconds),
        "닿지 못했다": widget_database.unreached_text(failure.TRANSIENT, place, reason, seconds),
        "비밀번호": widget_database.unreached_text(failure.PASSWORD, place, reason, seconds),
        "접속을 허락하지 않았다": widget_database.unreached_text(
            failure.NOT_ALLOWED, place, reason, seconds
        ),
        "데이터베이스 없음": widget_database.unreached_text(
            failure.NO_DATABASE, place, reason, seconds
        ),
        "그 밖": widget_database.unreached_text(failure.OTHER, place, reason, seconds),
        "표가 뒤처졌다": widget_database.misaligned_text(alignment.BEHIND, revision, revision),
        "표가 더 새롭다": widget_database.misaligned_text(alignment.AHEAD, revision, revision),
        "확인하다 멈췄다": widget_database.unexpected_text(place, reason),
        "닫다 실패했다": widget_database.close_text(place, reason),
        "올렸다": widget_database.upgraded_text(revision, revision),
        "이미 마지막 판이다": widget_database.already_current_text(revision),
        "올리다 실패했다": widget_database.upgrade_failed_text(reason, revision),
    }


def 없는_글(guide: str, texts: dict[str, str]) -> list[str]:
    """13절의 표가 싣지 않은 제품의 글. 들여쓴 설명 줄은 들여쓰기를 뗀다.

    글마다 첫 줄을 든 표의 행 하나를 찾고, 그 행에 나머지 줄이 모두 있는지 본다. 13절 어디에든
    줄이 있으면 통과시키면, 같은 줄을 담은 예시 기록이나 다른 행이 빠진 행을 가린다. 첫 줄을 든
    행이 없으면 그 글의 줄을 모두 낸다.
    """
    rows = [line for line in 열세째_절(guide).splitlines() if line.startswith("|")]
    missing: list[str] = []
    for label, text in texts.items():
        lines = [line for line in (part.strip() for part in text.splitlines()) if line]
        row = next((candidate for candidate in rows if lines[0] in candidate), "")
        missing.extend(f"{label}: {line}" for line in lines if line not in row)
    return missing


def 샌_안의_말(guide: str) -> list[str]:
    """안내에 샌 저장소 안의 말."""
    return [word for word in INTERNAL_WORDS if word in guide]


def compose의_user(compose: str, service: str) -> str:
    """compose 파일에서 서비스 하나의 `user:` 값. 없으면 빈 글.

    값 뒤의 `# 주석`은 값에 넣지 않는다.
    """
    user = re.search(
        r'^    user:\s*"?([^"\n#]+?)"?\s*(?:#.*)?$',
        compose의_서비스(compose, service),
        flags=re.MULTILINE,
    )
    return "" if user is None else user.group(1)


def compose의_서비스(compose: str, service: str) -> str:
    """compose 파일에서 서비스 하나의 본문(네 칸 들인 줄들). 없으면 던진다."""
    block = re.search(rf"^  {service}:\n((?:    .*\n|\n)+)", compose, flags=re.MULTILINE)
    assert block is not None, f"compose 에 서비스 {service} 가 없다"
    return block.group(1)


# 배포 안내 7절이 적는 PostgreSQL 의 전제와 그 컨테이너의 권한 넷(명세 postgres-foundation "저장소
# 상태 시험"의 셋째). 줄마다 그 줄이 빠지거나 바뀌면 무엇이 깨지는지 적는다.
POSTGRES_LINES: dict[str, str] = {
    'user: "999:999"': "데이터 폴더의 소유와 어긋난다(안내 7절)",
    "read_only: true": "루트 파일시스템에 쓰지 못한다",
    "cap_drop: [ALL]": "첫 프로세스의 권한 집합이 빈다",
    'security_opt: ["no-new-privileges:true"]': "권한을 다시 얻지 못한다",
    "init: true": "첫 프로세스가 멈춤 신호를 넘기고 끝난 자식을 거둔다",
}


POSTGRES_SERVICES = ("postgres", "widget-admin-postgres")


def postgres의_문제(compose: str, service: str = "postgres") -> list[str]:
    """compose 의 PostgreSQL 서비스(`postgres`, `widget-admin-postgres`)가 안내의 전제와 권한 넷을
    어긴 까닭들. 비어 있으면 맞다.

    `ports` 가 있으면 데이터베이스가 비밀번호 하나로 서버 밖에 열린다(안내 7절). 줄은 앞뒤 공백을
    뗀 글자 그대로 견주고(들여쓰기 깊이는 보지 않아 서비스 최상위에 있는지는 가리지 못한다), 값
    뒤의 `# 주석` 은 떼고 본다.
    """
    block = compose의_서비스(compose, service)
    lines = {line.split(" #", 1)[0].strip() for line in block.splitlines()}
    problems = [
        f"{service} 에 `{line}` 이 없다: {why}"
        for line, why in POSTGRES_LINES.items()
        if line not in lines
    ]
    if re.search(r"^    ports:", block, flags=re.MULTILINE):
        problems.append(f"{service} 에 ports 가 있다: 데이터베이스가 서버 밖에 열린다(안내 7절)")
    return problems


def dockerfile의_앱_gid(dockerfile: str) -> str:
    """Dockerfile 이 앱 사용자 `agentos` 의 그룹으로 만드는 번호.

    마지막 `USER` 가 `agentos` 이고(그 이름이나 번호가 아니면 이 시험의 전제가 깨진 것이다) 그
    그룹을 `groupadd --gid N agentos` 로 만든 번호를 돌려준다.
    """
    users = re.findall(r"^USER\s+(\S+)\s*$", dockerfile, flags=re.MULTILINE)
    assert users, "Dockerfile 에 USER 줄이 없다"
    assert users[-1] == "agentos", f"마지막 USER 가 agentos 가 아니다: {users[-1]}"
    gid = re.search(r"groupadd\s+--gid\s+(\d+)\s+agentos", dockerfile)
    assert gid is not None, "Dockerfile 이 agentos 그룹을 번호로 만들지 않는다"
    return gid.group(1)


def test_이_저장소의_배포_안내는_넘겨받은_항목을_모두_싣는다() -> None:
    missing = 없는_항목(GUIDE.read_text(encoding="utf-8"))
    assert missing == [], f"안내에 없는 항목: {missing}"


def test_필수_낱말_하나가_빠진_안내를_잡는다() -> None:
    guide = GUIDE.read_text(encoding="utf-8").replace("sha256sum", "")
    missing = 없는_항목(guide)
    assert missing != []
    assert all(entry.startswith("sha256sum:") for entry in missing)


def test_이_저장소의_배포_안내는_저장소_안의_말을_쓰지_않는다() -> None:
    leaked = 샌_안의_말(GUIDE.read_text(encoding="utf-8"))
    assert leaked == [], f"안내에 샌 저장소 안의 말: {leaked}"


def test_저장소_안의_말이_샌_안내를_잡는다() -> None:
    assert 샌_안의_말("자세한 것은 ADR 0056을 본다") == ["ADR"]


def test_이_저장소의_배포_안내는_13절에_넘겨받은_항목을_모두_싣는다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    assert 열세째_절(guide) != "", "안내에 13절이 없다"
    missing = 없는_13절_항목(guide)
    assert missing == [], f"13절에 없는 항목: {missing}"


def test_13절의_필수_낱말_하나가_빠진_안내를_잡는다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    section = 열세째_절(guide)
    changed = guide.replace(section, section.replace("docker inspect", ""))
    missing = 없는_13절_항목(changed)
    assert missing != []
    assert all(entry.startswith("docker inspect:") for entry in missing)


def test_4절에_이미_있는_낱말이_13절에서_빠진_안내를_잡는다() -> None:
    """`Exited (0)` 은 4절에도 있다. 안내 전체에서 찾으면 13절에서 빠져도 초록이 된다."""
    guide = GUIDE.read_text(encoding="utf-8")
    assert "Exited (0)" in 네째_절(guide)
    section = 열세째_절(guide)
    changed = guide.replace(section, section.replace("Exited (0)", ""))
    assert "Exited (0)" in changed
    assert [entry for entry in 없는_13절_항목(changed) if entry.startswith("Exited (0):")] != []


def test_13절이_없는_안내는_13절의_항목을_모두_빠진_것으로_본다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    without = guide[: guide.index(SECTION_13_TITLE)]
    assert len(없는_13절_항목(without)) == len(SECTION_13_REQUIRED)


def test_4절은_13절을_가리킨다() -> None:
    assert "13절" in 네째_절(GUIDE.read_text(encoding="utf-8"))


def test_제품이_멈출_때_찍는_글의_갈래는_명세의_표와_같다() -> None:
    assert tuple(제품의_멈출_때의_글()) == STOP_TEXT_LABELS


def test_제품의_접속_실패와_표_견줌의_갈래마다_표의_글이_하나씩_있다() -> None:
    """제품에 갈래가 늘면 이 시험이 빨개져, 안내의 표와 글의 목록이 함께 늘게 한다."""
    texts = set(제품의_멈출_때의_글().values())
    place, reason, seconds = "<자리>", "<까닭>", DEFAULT_RETRY_SECONDS
    for failure in Failure:
        assert unreached_text(failure, place, reason, seconds) in texts, failure
    for alignment in Alignment:
        if alignment is Alignment.CURRENT:
            continue
        assert misaligned_text(alignment, "<판>", "<판>") in texts, alignment


def test_맞는_표에는_맞지_않는_글이_없다() -> None:
    with pytest.raises(ValueError):
        misaligned_text(Alignment.CURRENT, "<판>", "<판>")


def test_이_저장소의_13절의_표는_제품이_멈출_때_찍는_글을_빠짐없이_싣는다() -> None:
    missing = 없는_글(GUIDE.read_text(encoding="utf-8"), 제품의_멈출_때의_글())
    assert missing == [], f"13절에 없는 제품의 글: {missing}"


def test_제품의_글이_바뀐_사본이면_안내의_검사가_빨개진다() -> None:
    texts = 제품의_멈출_때의_글()
    texts["비밀번호"] = texts["비밀번호"].replace("받아들이지", "받지")
    missing = 없는_글(GUIDE.read_text(encoding="utf-8"), texts)
    assert missing != []
    assert all(entry.startswith("비밀번호:") for entry in missing)


def test_안내의_표에서_제품의_글_한_줄이_빠진_안내를_잡는다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    line = "표가 이미 마지막 판(<판>)입니다."
    assert line in 열세째_절(guide)
    section = 열세째_절(guide)
    changed = guide.replace(section, section.replace(line, ""))
    assert 없는_글(changed, 제품의_멈출_때의_글()) == [f"이미 마지막 판이다: {line}"]


def test_표의_행에서만_설명_줄이_빠진_안내를_예시_기록에_같은_줄이_있어도_잡는다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    line = 제품의_멈출_때의_글()["비밀번호"].splitlines()[1].strip()
    rows = [row for row in 열세째_절(guide).splitlines() if row.startswith("|") and line in row]
    assert len(rows) == 1
    assert line in 열세째_절(guide).replace(rows[0], "")  # 예시 기록에 같은 줄이 또 있다
    changed = guide.replace(rows[0], rows[0].replace(line, ""))
    missing = 없는_글(changed, 제품의_멈출_때의_글())
    assert missing == [f"비밀번호: {line}"]


def test_같은_안내_줄을_쓰는_두_행_가운데_한_행에서만_빠져도_잡는다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    texts = 제품의_멈출_때의_글()
    hint = texts["접속을 허락하지 않았다"].splitlines()[1].strip()
    assert hint == texts["데이터베이스 없음"].splitlines()[1].strip()
    row = next(
        row
        for row in 열세째_절(guide).splitlines()
        if row.startswith("|") and texts["접속을 허락하지 않았다"].splitlines()[0].strip() in row
    )
    changed = guide.replace(row, row.replace(hint, ""))
    assert 없는_글(changed, texts) == [f"접속을 허락하지 않았다: {hint}"]


def test_위젯_관리_서버가_멈출_때_찍는_글의_갈래는_로그인_설정을_뺀_제품과_같다() -> None:
    # 로그인이 유지되는 시간(`AGENT_OS_LOGIN_*`)은 `serve` 만 읽는 설정이라 위젯 관리 서버에는 없다.
    without_login = tuple(label for label in STOP_TEXT_LABELS if not label.startswith("로그인 "))
    assert without_login != STOP_TEXT_LABELS, "제품의 갈래에서 뺄 로그인 갈래가 없다"
    assert tuple(위젯_관리_서버의_멈출_때의_글()) == without_login


def test_위젯_관리_서버의_접속_실패와_표_견줌의_갈래마다_표의_글이_하나씩_있다() -> None:
    """위젯 쪽에 갈래가 늘면 이 시험이 빨개져, 안내의 표와 글의 목록이 함께 늘게 한다."""
    texts = set(위젯_관리_서버의_멈출_때의_글().values())
    place, reason, seconds = "<자리>", "<까닭>", widget_database.DEFAULT_RETRY_SECONDS
    for failure in widget_database.Failure:
        assert widget_database.unreached_text(failure, place, reason, seconds) in texts, failure
    for alignment in widget_database.Alignment:
        if alignment is widget_database.Alignment.CURRENT:
            continue
        assert widget_database.misaligned_text(alignment, "<판>", "<판>") in texts, alignment


def test_이_저장소의_13절의_표는_위젯_관리_서버가_멈출_때_찍는_글을_빠짐없이_싣는다() -> None:
    missing = 없는_글(GUIDE.read_text(encoding="utf-8"), 위젯_관리_서버의_멈출_때의_글())
    assert missing == [], f"13절에 없는 위젯 쪽의 글: {missing}"


def test_위젯_쪽에만_있는_글_한_줄이_빠진_안내를_잡는다() -> None:
    """Agent OS 쪽 글과 글자가 다른 위젯 쪽 글이 표에서 빠지면 잡는다."""
    guide = GUIDE.read_text(encoding="utf-8")
    texts = 위젯_관리_서버의_멈출_때의_글()
    only_widget = [
        (label, text) for label, text in texts.items() if text not in 제품의_멈출_때의_글().values()
    ]
    assert only_widget, "위젯 쪽에만 있는 글이 없다"
    label, text = only_widget[0]
    line = next(part.strip() for part in text.splitlines() if part.strip())
    row = next(row for row in 열세째_절(guide).splitlines() if row.startswith("|") and line in row)
    changed = guide.replace(row, row.replace(line, ""))
    missing = 없는_글(changed, texts)
    assert missing != []
    assert any(entry.startswith(f"{label}: ") for entry in missing)


def test_위젯_관리_서버의_글에는_안내가_쓰지_않는_저장소_안의_말이_없다() -> None:
    for label, text in 위젯_관리_서버의_멈출_때의_글().items():
        assert 샌_안의_말(text) == [], f"{label} 의 위젯 쪽 글에 저장소 안의 말이 있다"


def test_제품의_글에는_안내가_쓰지_않는_저장소_안의_말이_없다() -> None:
    """안내가 제품의 글을 그대로 옮기므로, 글에 저장소 안의 말이 있으면 안내에 새 버린다."""
    for label, text in 제품의_멈출_때의_글().items():
        assert 샌_안의_말(text) == [], f"{label} 의 글에 저장소 안의 말이 있다"


def test_compose의_user_값은_주석을_떼고_읽는다() -> None:
    compose = 'services:\n  proxy:\n    user: "101:101"  # 프록시\n  serve:\n    image: x\n'
    assert compose의_user(compose, "proxy") == "101:101"
    assert compose의_user(compose, "serve") == ""


def test_안내가_적은_인증서와_키의_이름은_프록시_설정이_읽는_이름이다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    site = (STANDALONE / "proxy" / "site.conf").read_text(encoding="utf-8")
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    assert "ssl_certificate /etc/nginx/tls/fullchain.pem;" in site
    assert "ssl_certificate_key /etc/nginx/tls/privkey.pem;" in site
    assert "./tls:/etc/nginx/tls:ro" in compose
    assert "tls/fullchain.pem" in guide
    assert "tls/privkey.pem" in guide


def test_안내가_적은_개인_키의_이름은_위젯_미리보기_페이지_설정이_읽는_이름이다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    config = tomllib.loads((STANDALONE / "portal" / "portal.toml").read_text(encoding="utf-8"))
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    assert "./portal:/etc/agent-os/portal:ro" in compose
    configured = f"portal/{config['portal']['private_key']}"
    assert configured in guide, f"안내에 없는 개인 키 경로: {configured}"


def test_틀의_환경_변수_칸은_모두_안내에_있다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    template = (STANDALONE / ".env.example").read_text(encoding="utf-8")
    names = re.findall(r"^([A-Z][A-Z0-9_]*)=", template, flags=re.MULTILINE)
    assert names != []
    assert [name for name in names if name not in guide] == []


def test_안내가_적은_소유의_그룹은_컨테이너가_도는_사용자의_그룹이다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    proxy_user = compose의_user(compose, "proxy")
    assert ":" in proxy_user, f"프록시의 user 가 uid:gid 꼴이 아니다: {proxy_user!r}"
    proxy_gid = proxy_user.split(":")[1]
    portal_gid = dockerfile의_앱_gid(
        (REPO / "deploy" / "images" / "portal.Dockerfile").read_text(encoding="utf-8")
    )
    for command in (
        f"sudo chown root:{proxy_gid} tls/privkey.pem",
        f"sudo chown root:{portal_gid} portal/keys/portal.pem",
    ):
        assert command in guide, f"안내에 없는 명령: {command}"
    assert guide.count("sudo chmod 640") == 2


def test_compose가_우리_이미지에_user를_더하지_않는다는_안내의_전제가_맞다() -> None:
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    added = [
        service
        for service in (
            "serve",
            "migrate",
            "admin",
            "widget",
            "portal",
            "widget-admin-migrate",
            "widget-admin",
        )
        if compose의_user(compose, service)
    ]
    assert added == [], f"compose 가 user 를 더한 서비스: {added}"


def test_compose가_위젯_관리_서버를_밖에_열지_않는다() -> None:
    """안내 7절: 위젯 관리 서버는 어느 주소에도 발행하지 않는다."""
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    for service in ("widget-admin", "widget-admin-migrate"):
        assert not re.search(r"^    ports:", compose의_서비스(compose, service), re.MULTILINE), (
            f"{service} 에 ports 가 있다"
        )


def test_위젯_관리_서버에_ports를_더한_compose를_잡는다() -> None:
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    published = compose.replace(
        "  widget-admin:\n", '  widget-admin:\n    ports:\n      - "8100:8100"\n', 1
    )
    assert re.search(r"^    ports:", compose의_서비스(published, "widget-admin"), re.MULTILINE)


def test_위젯_관리_서버에_user를_더한_compose를_잡는다() -> None:
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    changed = compose.replace("  widget-admin:\n", '  widget-admin:\n    user: "0:0"\n', 1)
    assert compose의_user(changed, "widget-admin") == "0:0"


WIDGET_PASSWORD_REFERENCES = 3


def 필수_표시_없는_위젯_비밀번호(compose: str) -> list[str]:
    """compose 가 위젯 쪽 비밀번호 칸을 읽는 `${…}` 가운데 `:?` 꼴이 아닌 것들과, 읽는 곳의 수가
    셋(위젯 쪽 PostgreSQL 의 비밀번호, 표를 올리는 서비스와 서버의 연결 문자열)이 아닌 것.

    `:?` 가 없으면 `.env` 에 줄이 빠진 채 띄울 때 compose 가 어느 줄이 없는지 말하지 않고 빈
    비밀번호로 띄운다(사용자 이야기 12). 비면 맞다.
    """
    references = re.findall(r"\$\{WIDGET_ADMIN_DATABASE_PASSWORD([^}]*)\}", compose)
    problems = [
        f"`:?` 가 없는 참조: ${{WIDGET_ADMIN_DATABASE_PASSWORD{tail}}}"
        for tail in references
        if not tail.startswith(":?")
    ]
    if len(references) != WIDGET_PASSWORD_REFERENCES:
        problems.append(
            f"참조가 {len(references)}곳이다. {WIDGET_PASSWORD_REFERENCES}곳이어야 한다"
        )
    return problems


def test_이_저장소의_compose는_위젯_쪽_비밀번호를_읽는_세_곳_모두_없으면_멈추게_한다() -> None:
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    assert 필수_표시_없는_위젯_비밀번호(compose) == []


def test_위젯_쪽_비밀번호의_필수_표시_하나가_빠진_compose를_잡는다() -> None:
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    relaxed = re.sub(
        r"\$\{WIDGET_ADMIN_DATABASE_PASSWORD:\?[^}]*\}",
        "${WIDGET_ADMIN_DATABASE_PASSWORD}",
        compose,
        count=1,
    )
    problems = 필수_표시_없는_위젯_비밀번호(relaxed)
    assert problems == ["`:?` 가 없는 참조: ${WIDGET_ADMIN_DATABASE_PASSWORD}"]


def test_위젯_쪽_비밀번호를_읽는_곳_하나가_빠진_compose를_잡는다() -> None:
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    dropped = re.sub(r"\$\{WIDGET_ADMIN_DATABASE_PASSWORD:\?[^}]*\}", "x", compose, count=1)
    assert 필수_표시_없는_위젯_비밀번호(dropped) == ["참조가 2곳이다. 3곳이어야 한다"]


def 프록시의_위젯_설정_문제(site: str) -> list[str]:
    """프록시 설정이 위젯 설정 경로를 다루는 규칙을 어긴 까닭들. 비면 맞다.

    - 위젯 관리 서버로 넘기는 줄(`proxy_pass http://up_widget_admin…`)은 `/widget-settings/` 위치의
      한 줄뿐이다. 그래야 `/operator/` 와 `/internal/` 이 마지막 `location /` 의 404 로 끊긴다.
    - 그 위치에는 `add_header` 와 `limit_req` 를 적지 않는다. 열린 머리 셋은 서버가
      달고(`add_header` 를 하나라도 적으면 server 의 머리가 물려지지 않는다), 요청 수는 세지 않는다.
    """
    forwards = re.findall(r"proxy_pass\s+http://up_widget_admin[^;]*;", site)
    problems = (
        []
        if forwards == ["proxy_pass http://up_widget_admin/widget-settings/;"]
        else [f"위젯 관리 서버로 넘기는 줄이 `/widget-settings/` 위치의 한 줄이 아니다: {forwards}"]
    )
    block = re.search(
        r"^    location /widget-settings/ \{\n(.*?)^    \}", site, re.MULTILINE | re.DOTALL
    )
    if block is None:
        return [*problems, "`location /widget-settings/` 가 없다"]
    # 넘기는 줄이 한 줄뿐인 것은 위에서 봤다. 그 한 줄이 이 위치 안에 있는지도 본다.
    if "proxy_pass http://up_widget_admin/widget-settings/;" not in block.group(1):
        problems.append("`/widget-settings/` 위치 안에 위젯 관리 서버로 넘기는 줄이 없다")
    problems += [
        f"`/widget-settings/` 위치에 `{directive}` 가 있다"
        for directive in ("add_header", "limit_req")
        if re.search(rf"^\s*{directive}\b", block.group(1), re.MULTILINE)
    ]
    return problems


def test_이_저장소의_프록시는_위젯_설정_경로만_위젯_관리_서버로_넘긴다() -> None:
    site = (STANDALONE / "proxy" / "site.conf").read_text(encoding="utf-8")
    assert 프록시의_위젯_설정_문제(site) == []


@pytest.mark.parametrize("directive", ["add_header X-Test 1;", "limit_req zone=token;"])
def test_위젯_설정_위치에_머리나_요청_수_제한을_적은_프록시를_잡는다(directive: str) -> None:
    site = (STANDALONE / "proxy" / "site.conf").read_text(encoding="utf-8")
    changed = site.replace(
        "    location /widget-settings/ {\n",
        f"    location /widget-settings/ {{\n        {directive}\n",
        1,
    )
    assert changed != site
    assert 프록시의_위젯_설정_문제(changed) == [
        f"`/widget-settings/` 위치에 `{directive.split()[0]}` 가 있다"
    ]


def test_넘기는_줄이_위젯_설정_위치_밖으로_옮겨진_프록시를_잡는다() -> None:
    site = (STANDALONE / "proxy" / "site.conf").read_text(encoding="utf-8")
    # 넘기는 줄 하나는 그대로 있지만 `/widget-settings/` 위치는 비고, 줄은 다른 위치 안에 있다.
    changed = site.replace(
        "    location /widget-settings/ {\n"
        "        proxy_pass http://up_widget_admin/widget-settings/;\n"
        "    }\n",
        "    location /widget-settings/ {\n    }\n",
        1,
    ).replace(
        "    location / {\n",
        "    location /other/ {\n"
        "        proxy_pass http://up_widget_admin/widget-settings/;\n"
        "    }\n\n"
        "    location / {\n",
        1,
    )
    assert changed != site
    assert 프록시의_위젯_설정_문제(changed) == [
        "`/widget-settings/` 위치 안에 위젯 관리 서버로 넘기는 줄이 없다"
    ]


def test_위젯_관리_서버로_넘기는_위치가_하나_더_생긴_프록시를_잡는다() -> None:
    site = (STANDALONE / "proxy" / "site.conf").read_text(encoding="utf-8")
    changed = site.replace(
        "    location / {\n",
        "    location /operator/ {\n"
        "        proxy_pass http://up_widget_admin/operator/;\n"
        "    }\n\n"
        "    location / {\n",
        1,
    )
    problems = 프록시의_위젯_설정_문제(changed)
    assert len(problems) == 1
    assert problems[0].startswith("위젯 관리 서버로 넘기는 줄이")


@pytest.mark.parametrize("service", POSTGRES_SERVICES)
def test_이_저장소의_compose는_PostgreSQL을_밖에_열지_않고_좁힌_권한으로_띄운다(
    service: str,
) -> None:
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    assert postgres의_문제(compose, service) == []
    assert compose의_user(compose, service) == "999:999"


def _postgres를_고친(old: str, new: str, service: str = "postgres") -> str:
    """이 저장소의 compose 에서 PostgreSQL 서비스 본문 안의 `old` 한 곳만 `new` 로 바꾼 글.

    프록시도 같은 권한 줄(`init: true` 등)을 가지므로 파일 전체에서 바꾸면 프록시의 줄이 바뀐다.
    """
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    block = compose의_서비스(compose, service)
    assert old in block, f"{service} 에 없는 줄: {old}"
    return compose.replace(block, block.replace(old, new, 1), 1)


@pytest.mark.parametrize("service", POSTGRES_SERVICES)
@pytest.mark.parametrize("line", list(POSTGRES_LINES))
def test_PostgreSQL의_전제나_권한_한_줄이_빠진_compose를_잡는다(line: str, service: str) -> None:
    problems = postgres의_문제(_postgres를_고친(f"    {line}\n", "", service), service)
    assert len(problems) == 1
    assert problems[0].startswith(f"{service} 에 `{line}` 이 없다: ")


@pytest.mark.parametrize("service", POSTGRES_SERVICES)
def test_PostgreSQL의_user가_바뀐_compose를_잡는다(service: str) -> None:
    changed = _postgres를_고친('    user: "999:999"', '    user: "70:70"', service)
    assert postgres의_문제(changed, service) == [
        f'{service} 에 `user: "999:999"` 이 없다: 데이터 폴더의 소유와 어긋난다(안내 7절)'
    ]


@pytest.mark.parametrize("service", POSTGRES_SERVICES)
def test_PostgreSQL에_포트를_발행한_compose를_잡는다(service: str) -> None:
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    published = compose.replace(
        f"  {service}:\n", f'  {service}:\n    ports:\n      - "127.0.0.1:5432:5432"\n', 1
    )
    assert postgres의_문제(published, service) == [
        f"{service} 에 ports 가 있다: 데이터베이스가 서버 밖에 열린다(안내 7절)"
    ]


def test_사이트_파일을_고친_뒤_다시_띄우라는_서비스는_compose에_있고_사이트_파일을_읽는다() -> None:
    guide = GUIDE.read_text(encoding="utf-8")
    compose = (STANDALONE / "compose.yaml").read_text(encoding="utf-8")
    found = re.search(r"docker compose restart ([a-z ]+)\n", guide)
    assert found is not None
    for service in found.group(1).split():
        block = re.search(rf"^  {service}:\n((?:    .*\n|\n)+)", compose, flags=re.MULTILINE)
        assert block is not None, f"compose 에 서비스 {service} 가 없다"
        assert "./site:/etc/agent-os/site:ro" in block.group(1), (
            f"{service} 가 사이트 파일을 읽지 않는다"
        )


def test_배포_파일_묶음에_안내가_든다(tmp_path: Path) -> None:
    built = build_bundle(STANDALONE, tmp_path, "0.1.0-rc.1", "agent-os")
    with tarfile.open(built) as archive:
        guide = archive.extractfile("agent-os-0.1.0-rc.1/README.md")
        assert guide is not None
        assert guide.read().decode("utf-8") == GUIDE.read_text(encoding="utf-8")
