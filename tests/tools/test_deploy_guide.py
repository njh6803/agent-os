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

from tools.release import build_bundle

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


def 없는_항목(guide: str) -> list[str]:
    """안내에 없는 필수 낱말과 그 낱말이 지키는 항목."""
    return [f"{word}: {item}" for word, item in REQUIRED.items() if word not in guide]


def 샌_안의_말(guide: str) -> list[str]:
    """안내에 샌 저장소 안의 말."""
    return [word for word in INTERNAL_WORDS if word in guide]


def compose의_user(compose: str, service: str) -> str:
    """compose 파일에서 서비스 하나의 `user:` 값. 없으면 빈 글.

    값 뒤의 `# 주석`은 값에 넣지 않는다.
    """
    block = re.search(rf"^  {service}:\n((?:    .*\n|\n)+)", compose, flags=re.MULTILINE)
    assert block is not None, f"compose 에 서비스 {service} 가 없다"
    user = re.search(
        r'^    user:\s*"?([^"\n#]+?)"?\s*(?:#.*)?$', block.group(1), flags=re.MULTILINE
    )
    return "" if user is None else user.group(1)


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
        for service in ("serve", "admin", "widget", "portal")
        if compose의_user(compose, service)
    ]
    assert added == [], f"compose 가 user 를 더한 서비스: {added}"


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
