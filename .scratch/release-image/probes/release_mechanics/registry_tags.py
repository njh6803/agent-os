"""release-image 명세의 "한 번 올라간 번호 태그를 다른 커밋의 이미지로 덮지 않는 방법"을 로컬
레지스트리에서 잰다. 결정은 하지 않고 회차마다 본 것을 한 줄씩 낸다.

저장소 루트에서

    uv run python .scratch/release-image/probes/release_mechanics/registry_tags.py
        [--sections tags,lookup,overwrite,guard,rebuild,load] [--work <원본 출력을 둘 폴더>]

필요한 것. 도는 Docker 데몬과 buildx, 로컬에 이미 있는 이미지 둘(아래 REGISTRY_IMAGE 와
BASE_IMAGE 의 digest 참조), 비어 있는 호스트 포트 39460(레지스트리)·39461(아무것도 듣지 않는
자리)·39462(상태 코드만 내는 가짜 서버). 모두 127.0.0.1 에만 연다. `index`·`load` 갈래는
docker-container 빌더를 만들며 moby/buildkit 과 docker/buildkit-syft-scanner 이미지를 Docker Hub
에서 받는다. 만드는 것은 이름이 `ri-rel-` 로 시작하는 컨테이너·빌더·이미지 태그뿐이고 끝에서 지운다.
모든 명령의 원본 출력은 --work(없으면 시스템 임시 폴더) 아래 raw.log 에 남긴다.

진실의 기준. 태그가 가리키는 digest 와 있고 없음은 레지스트리의 HTTP 응답으로 본다
(`HEAD /v2/<저장소>/manifests/<태그>` 의 상태 코드와 `Docker-Content-Digest`). 명령(`docker buildx
imagetools inspect`, `docker manifest inspect`)의 종료 코드와 글은 그 응답과 나란히 적는다.

갈래
- tags(길 가). 커밋 해시 태그로 올린 이미지에 `docker buildx imagetools create -t <번호>` 로 번호
  태그를 붙였을 때 두 태그의 digest 가 같은가. 원본이 한 플랫폼의 매니페스트일 때(기본값과
  `--prefer-index=false`), 원본이 증명이 붙은 이미지 색인일 때, 다른 저장소 이름으로 옮길 때. 표지는
  원본의 `Content-Type` 이 그 갈래가 기대한 꼴(매니페스트냐 색인이냐)인 것이다.
- lookup(길 나). 있는 태그, 없는 태그, 없는 저장소, 듣지 않는 포트, 401·429·500 만 내는 서버에 조회
  명령을 쳤을 때의 종료 코드와 글. 표지는 그 상황이 실제로 났다는 것(HTTP 상태, 연결 거부, 가짜
  서버가 그 요청을 받은 기록)이다.
- overwrite(양성 대조). 이미 있는 번호 태그에 다른 이미지를 같은 태그로 올리면 거부 없이 덮이는가.
  표지는 올리기 전의 digest 가 있었고 올린 명령이 0 으로 끝난 것이다.
- guard(가와 나를 함께). 조회해서 없으면 붙이고, 같은 digest 면 아무것도 하지 않고, 다른 digest 면
  거부하는 차례를 그대로 돌려 본다. 표지는 회차마다 HTTP 로 다시 본 앞뒤의 digest 다.
- rebuild. 같은 내용(같은 Dockerfile 과 같은 빌드 인자)을 증명과 함께 다시 지어 올리면 색인과 플랫폼
  매니페스트의 digest 가 같은가, 그때 guard 의 차례가 무엇을 하는가. 판 내기를 처음부터 다시 돌리면
  같은 커밋을 다시 짓는다. 캐시를 쓰는 갈래와 `--no-cache` 갈래. 표지는 빌드 기록에서 RUN 단계가 그
  갈래가 기대한 대로 캐시에서 왔거나(CACHED) 실제로 돈 것(DONE)이다.
- load(build-push-action 의 `load: true` 에 해당하는 `--load`). 러너에 실은 이미지와 뒤이어 캐시로
  다시 지어 올린 이미지가 같은가, 증명을 켠 채 `--load` 하면 어떻게 되는가. 표지는 데몬의 이미지
  저장 방식(스냅샷 저장소냐 아니냐)과 빌드 기록의 내보내기 줄이다.

못 보는 것. Docker Hub 자체(로그인, 받는 횟수 제한, 태그 불변 설정), 두 실행이 동시에 조회하고
붙이는 경합, GitHub 러너의 Docker(이미지 저장 방식이 이 PC 와 다를 수 있다), 여러 플랫폼 이미지.
결과는 같은 폴더의 README.md 에 있다.
"""

from __future__ import annotations

import argparse
import http.client
import http.server
import json
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeGuard

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

# 2026-11-13 에 받은 공식 이미지다. registry:3(distribution 3.1.2)과 alpine:3.22(3.22.8).
REGISTRY_IMAGE = "registry@sha256:82f6ff4a7f982960c8aa51617fea3aabc485df6e55cce80d22deb1de36f1bc3c"
BASE_IMAGE = "alpine@sha256:49340b346798875b5592e5d420241f2f9cfba5f47e62ebb1446a1b34734e898f"
PORT, PORT_CLOSED, PORT_STUB = 39460, 39461, 39462
HOST = f"127.0.0.1:{PORT}"
REPO = f"{HOST}/ri-rel/app"
REGISTRY_NAME, BUILDER = "ri-rel-registry", "ri-rel-builder"
MANIFEST_TYPES = (
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
)
INDEX_TYPES = (
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
)
SECTIONS = ("tags", "lookup", "overwrite", "guard", "rebuild", "load")


@dataclass(frozen=True)
class Done:
    code: int
    out: str
    err: str

    @property
    def tail(self) -> str:
        """오류 글의 마지막 줄. 조회 명령은 까닭을 여기 적는다."""
        lines = [line for line in (self.err or self.out).splitlines() if line.strip()]
        return lines[-1].strip() if lines else ""


@dataclass(frozen=True)
class Head:
    """레지스트리의 HTTP 응답 하나. status 가 0 이면 연결하지 못했다."""

    status: int
    digest: str = ""
    kind: str = ""


@dataclass
class Probe:
    work: Path
    token: str
    rounds: Rounds = field(default_factory=Rounds)
    tagged: list[str] = field(default_factory=list[str])

    def run(self, *args: str, timeout: float = 300) -> Done:
        try:
            done = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
            result = Done(done.returncode, done.stdout, done.stderr)
        except subprocess.TimeoutExpired:
            result = Done(-1, "", f"시간 제한 {timeout}초를 넘겼다")
        with (self.work / "raw.log").open("a", encoding="utf-8", newline="\n") as log:
            log.write(f"$ {' '.join(args)}\n[exit {result.code}]\n{result.out}\n{result.err}\n")
        return result

    def note(self, slot: Slot, *, measured: bool, result: str) -> None:
        slot.mark(measured=measured, result=result)
        print(f"{'측정' if measured else '측정 아님'}\t{slot.label}\t{result}", flush=True)


def fetch(port: int, repo: str, reference: str, *, body: bool = False) -> tuple[Head, object]:
    """매니페스트를 HEAD(또는 GET)로 읽는다. 연결하지 못하면 status 0 이다."""
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request(
            "GET" if body else "HEAD",
            f"/v2/{repo}/manifests/{reference}",
            headers={"Accept": ", ".join(INDEX_TYPES + MANIFEST_TYPES)},
        )
        response = connection.getresponse()
        raw = response.read()
    except OSError:
        return Head(0), None
    finally:
        connection.close()
    head = Head(
        response.status,
        response.getheader("Docker-Content-Digest") or "",
        (response.getheader("Content-Type") or "").split(";")[0],
    )
    if not body or response.status != 200:
        return head, None
    return head, json.loads(raw)


def head(reference: str, *, repo: str = "ri-rel/app", port: int = PORT) -> Head:
    return fetch(port, repo, reference)[0]


def is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def as_object(value: object) -> dict[str, object] | None:
    """JSON 객체면 그것, 아니면 None."""
    return value if is_object(value) else None


def as_list(value: object) -> list[object]:
    """JSON 배열이면 그것, 아니면 빈 목록."""
    return value if is_list(value) else []


def children(document: object) -> list[dict[str, object]]:
    """색인의 `manifests` 항목들. 색인이 아니면 빈 목록이다."""
    entries = as_list((as_object(document) or {}).get("manifests"))
    return [entry for entry in map(as_object, entries) if entry is not None]


def short(kind: str) -> str:
    if kind in INDEX_TYPES:
        return "색인" if "oci" in kind else "매니페스트 목록"
    return "매니페스트" if kind in MANIFEST_TYPES else (kind or "없음")


def write_context(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "Dockerfile").write_text(
        f'FROM {BASE_IMAGE}\nARG MARK\nRUN echo "$MARK" > /mark.txt\n',
        encoding="utf-8",
        newline="\n",
    )
    return folder


def start_registry(probe: Probe) -> bool:
    probe.run("docker", "rm", "-f", "-v", REGISTRY_NAME)
    started = probe.run(
        "docker", "run", "-d", "--name", REGISTRY_NAME, "-p", f"{HOST}:5000", REGISTRY_IMAGE
    )
    deadline = time.monotonic() + 30
    while started.code == 0 and time.monotonic() < deadline:
        connection = http.client.HTTPConnection("127.0.0.1", PORT, timeout=3)
        try:
            connection.request("GET", "/v2/")
            if connection.getresponse().status == 200:
                return True
        except OSError:
            time.sleep(0.5)
        finally:
            connection.close()
    return False


def push_plain(probe: Probe, context: Path, mark: str, tag: str) -> Done:
    """기본 빌더(docker 드라이버)로 지어 `docker push` 로 올린다. 증명 없는 한 플랫폼 이미지다."""
    reference = f"{REPO}:{tag}"
    built = probe.run(
        "docker", "build", "-q", "--build-arg", f"MARK={mark}", "-t", reference, str(context)
    )
    if built.code != 0:
        return built
    probe.tagged.append(reference)
    return probe.run("docker", "push", "-q", reference)


def ensure_builder(probe: Probe) -> bool:
    if probe.run("docker", "buildx", "inspect", BUILDER).code == 0:
        return True
    config = probe.work / "buildkitd.toml"
    config.write_text(f'[registry."{HOST}"]\n  http = true\n', encoding="utf-8", newline="\n")
    created = probe.run(
        "docker", "buildx", "create", "--name", BUILDER, "--driver", "docker-container",
        "--driver-opt", "network=host", "--buildkitd-config", str(config),
    )  # fmt: skip
    return created.code == 0


def push_index(probe: Probe, context: Path, mark: str, tag: str, *extra: str) -> Done:
    """docker-container 빌더로 출처 증명과 SBOM 을 붙여 바로 올린다. 결과는 이미지 색인이다."""
    return probe.run(
        "docker", "buildx", "build", "--builder", BUILDER, "--progress", "plain",
        "--build-arg", f"MARK={mark}", "--provenance=mode=max", "--sbom=true", "--push",
        *extra, "-t", f"{REPO}:{tag}", str(context),
        timeout=600,
    )  # fmt: skip


def create_tag(probe: Probe, target: str, source: str, *extra: str) -> Done:
    return probe.run("docker", "buildx", "imagetools", "create", *extra, "-t", target, source)


def section_tags(probe: Probe, context: Path) -> None:
    sha_a = f"sha-{secrets.token_hex(4)}"
    pushed = push_plain(probe, context, f"{probe.token}-A", sha_a)
    source = head(sha_a)
    for label, tag, extra in (
        ("tags/한 플랫폼 매니페스트, 기본값", "0.2.0", ()),
        ("tags/한 플랫폼 매니페스트, --prefer-index=false", "0.2.1", ("--prefer-index=false",)),
    ):
        with probe.rounds.round(label) as slot:
            created = create_tag(probe, f"{REPO}:{tag}", f"{REPO}:{sha_a}", *extra)
            after, document = fetch(PORT, "ri-rel/app", tag, body=True)
            inner = [str(entry.get("digest")) for entry in children(document)]
            same = "같다" if after.digest == source.digest else "다르다"
            inside = "같다" if inner == [source.digest] else "다르다"
            wraps = f", 목록 안의 digest 가 원본과 {inside}"
            probe.note(
                slot,
                measured=pushed.code == 0 and source.kind in MANIFEST_TYPES and created.code == 0,
                result=f"두 태그의 digest 가 {same}. 원본 {short(source.kind)}, 번호 태그 "
                f"{short(after.kind)}{wraps if inner else ''}",
            )
    if not ensure_builder(probe):
        probe.rounds.record("tags/증명이 붙은 색인", measured=False, result="빌더를 만들지 못했다")
        return
    sha_c = f"sha-{secrets.token_hex(4)}"
    built = push_index(probe, context, f"{probe.token}-C", sha_c)
    source, document = fetch(PORT, "ri-rel/app", sha_c, body=True)
    attested = any(
        isinstance(entry.get("annotations"), dict)
        and "attestation-manifest" in str(entry.get("annotations"))
        for entry in children(document)
    )
    for label, repo, tag in (
        ("tags/증명이 붙은 색인, 같은 저장소", "ri-rel/app", "0.3.0"),
        ("tags/증명이 붙은 색인, 다른 저장소 이름으로", "ri-rel/promoted", "0.3.0"),
    ):
        with probe.rounds.round(label) as slot:
            created = create_tag(probe, f"{HOST}/{repo}:{tag}", f"{REPO}:{sha_c}")
            after = head(tag, repo=repo)
            same = "같다" if after.digest == source.digest else "다르다"
            probe.note(
                slot,
                measured=built.code == 0
                and source.kind in INDEX_TYPES
                and attested
                and created.code == 0,
                result=f"두 태그의 digest 가 {same}. 원본 {short(source.kind)}(증명 매니페스트 "
                f"{'있음' if attested else '없음'}), 번호 태그 {short(after.kind)}",
            )


class Stub(http.server.BaseHTTPRequestHandler):
    """모든 요청에 정해진 상태 코드만 내고 받은 요청을 적는다."""

    status = 500
    seen: list[str] = []

    def _answer(self) -> None:
        type(self).seen.append(f"{self.command} {self.path}")
        self.send_response(type(self).status)
        if type(self).status == 401:
            self.send_header("WWW-Authenticate", 'Basic realm="ri-rel-stub"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_GET = _answer
    do_HEAD = _answer

    def log_message(self, format: str, *args: object) -> None:
        return


def port_refuses(port: int) -> bool:
    try:
        socket.create_connection(("127.0.0.1", port), timeout=3).close()
    except ConnectionRefusedError:
        return True
    except OSError:
        return False
    return False


def lookups(probe: Probe, reference: str) -> str:
    """조회 명령 둘의 종료 코드와 마지막 줄."""
    inspect = probe.run("docker", "buildx", "imagetools", "inspect", reference, timeout=180)
    manifest = probe.run("docker", "manifest", "inspect", "--insecure", reference, timeout=180)
    first = "" if inspect.code == 0 else f" '{inspect.tail[:110]}'"
    second = "" if manifest.code == 0 else f" '{manifest.tail[:110]}'"
    return (
        f"imagetools inspect 종료 {inspect.code}{first}, "
        f"manifest inspect 종료 {manifest.code}{second}"
    )


def section_lookup(probe: Probe, context: Path) -> None:
    sha = f"sha-{secrets.token_hex(4)}"
    pushed = push_plain(probe, context, f"{probe.token}-L", sha)
    with probe.rounds.round("lookup/있는 태그") as slot:
        truth = head(sha)
        probe.note(
            slot,
            measured=pushed.code == 0 and truth.status == 200,
            result=f"HTTP {truth.status}. {lookups(probe, f'{REPO}:{sha}')}",
        )
    with probe.rounds.round("lookup/없는 태그(저장소는 있다)") as slot:
        truth = head("9.9.9")
        probe.note(
            slot,
            measured=truth.status == 404 and head(sha).status == 200,
            result=f"HTTP {truth.status}. {lookups(probe, f'{REPO}:9.9.9')}",
        )
    with probe.rounds.round("lookup/없는 저장소") as slot:
        truth = head("0.2.0", repo="ri-rel/absent")
        probe.note(
            slot,
            measured=truth.status == 404,
            result=f"HTTP {truth.status}. {lookups(probe, f'{HOST}/ri-rel/absent:0.2.0')}",
        )
    with probe.rounds.round("lookup/아무것도 듣지 않는 포트") as slot:
        refused = port_refuses(PORT_CLOSED)
        probe.note(
            slot,
            measured=refused,
            result="연결 거부. " + lookups(probe, f"127.0.0.1:{PORT_CLOSED}/ri-rel/app:0.2.0"),
        )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT_STUB), Stub)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        for status in (401, 429, 500):
            with probe.rounds.round(f"lookup/레지스트리가 {status} 만 낸다") as slot:
                Stub.status, Stub.seen = status, []
                done = probe.run(
                    "docker", "buildx", "imagetools", "inspect",
                    f"127.0.0.1:{PORT_STUB}/ri-rel/app:0.2.0",
                    timeout=180,
                )  # fmt: skip
                asked = [line for line in Stub.seen if "/v2/" in line]
                probe.note(
                    slot,
                    measured=bool(asked),
                    result=f"imagetools inspect 종료 {done.code} '{done.tail[:140]}' "
                    f"(가짜 서버가 받은 요청 {len(Stub.seen)}건)",
                )
    finally:
        server.shutdown()
        server.server_close()


def section_overwrite(probe: Probe, context: Path) -> None:
    first, second = f"sha-{secrets.token_hex(4)}", f"sha-{secrets.token_hex(4)}"
    push_plain(probe, context, f"{probe.token}-O1", first)
    push_plain(probe, context, f"{probe.token}-O2", second)
    create_tag(probe, f"{REPO}:0.5.0", f"{REPO}:{first}", "--prefer-index=false")
    with probe.rounds.round("overwrite/docker push 로 같은 번호 태그") as slot:
        before = head("0.5.0")
        probe.run("docker", "tag", f"{REPO}:{second}", f"{REPO}:0.5.0")
        probe.tagged.append(f"{REPO}:0.5.0")
        pushed = probe.run("docker", "push", "-q", f"{REPO}:0.5.0")
        after = head("0.5.0")
        probe.note(
            slot,
            measured=before.status == 200 and before.digest == head(first).digest,
            result=f"push 종료 {pushed.code}, 태그의 digest 가 "
            f"{'바뀌었다(둘째 이미지)' if after.digest == head(second).digest else '그대로다'}",
        )
    with probe.rounds.round("overwrite/imagetools create 로 같은 번호 태그") as slot:
        before = head("0.5.0")
        created = create_tag(probe, f"{REPO}:0.5.0", f"{REPO}:{first}", "--prefer-index=false")
        after = head("0.5.0")
        moved = "바뀌었다(첫 이미지)" if after.digest == head(first).digest else "그대로다"
        probe.note(
            slot,
            measured=before.status == 200 and before.digest == head(second).digest,
            result=f"create 종료 {created.code}, 태그의 digest 가 {moved}",
        )


def looked_up(probe: Probe, reference: str) -> tuple[str, str]:
    """워크플로가 칠 조회. ('있다', digest) / ('없다', '') / ('모른다', 까닭)."""
    done = probe.run(
        "docker", "buildx", "imagetools", "inspect", reference, "--format", "{{json .Manifest}}",
        timeout=180,
    )  # fmt: skip
    if done.code == 0:
        document = as_object(json.loads(done.out))
        return "있다", str(document.get("digest")) if document is not None else ""
    if done.tail.endswith(": not found"):
        return "없다", ""
    return "모른다", done.tail


def attach_once(probe: Probe, target: str, source: str) -> str:
    """조회해서 없을 때만 번호 태그를 붙인다. 있으면 digest 를 대 보고 손대지 않는다."""
    state, existing = looked_up(probe, target)
    if state == "모른다":
        return "조회 실패라 붙이지 않았다"
    wanted_state, wanted = looked_up(probe, source)
    if wanted_state != "있다":
        return "원본을 찾지 못해 붙이지 않았다"
    if state == "있다" and existing == wanted:
        return "이미 같은 digest 라 그대로 뒀다"
    if state == "있다":
        return "다른 digest 라 거부했다"
    created = create_tag(probe, target, source, "--prefer-index=false")
    return "붙였다" if created.code == 0 else f"붙이지 못했다(종료 {created.code})"


def section_guard(probe: Probe, context: Path) -> None:
    first, second = f"sha-{secrets.token_hex(4)}", f"sha-{secrets.token_hex(4)}"
    push_plain(probe, context, f"{probe.token}-G1", first)
    push_plain(probe, context, f"{probe.token}-G2", second)
    wanted, other = head(first), head(second)
    ready = wanted.status == 200 and other.status == 200 and wanted.digest != other.digest
    for label, source, expect in (
        ("guard/태그가 없을 때", first, "붙였다"),
        ("guard/같은 커밋으로 다시", first, "이미 같은 digest 라 그대로 뒀다"),
        ("guard/다른 커밋이 같은 번호로", second, "다른 digest 라 거부했다"),
    ):
        with probe.rounds.round(label) as slot:
            before = head("0.6.0")
            outcome = attach_once(probe, f"{REPO}:0.6.0", f"{REPO}:{source}")
            after = head("0.6.0")
            kept = "첫 커밋의 digest" if after.digest == wanted.digest else "다른 digest"
            probe.note(
                slot,
                measured=ready and (before.status == 404) == (expect == "붙였다"),
                result=f"{outcome}. 뒤에 태그가 가리키는 것은 {kept}"
                + ("" if outcome == expect else f" (기대는 '{expect}')"),
            )
    with probe.rounds.round("guard/조회가 실패할 때(듣지 않는 포트)") as slot:
        outcome = attach_once(
            probe, f"127.0.0.1:{PORT_CLOSED}/ri-rel/app:0.6.0", f"{REPO}:{second}"
        )
        probe.note(slot, measured=port_refuses(PORT_CLOSED), result=outcome)


def run_step(log: str) -> str:
    """빌드 기록에서 RUN 단계가 캐시에서 왔는지(CACHED) 실제로 돌았는지(DONE)."""
    found = re.search(r"^#(\d+) \[\d+/\d+\] RUN ", log, re.MULTILINE)
    if not found:
        return ""
    for state in ("CACHED", "DONE"):
        if re.search(rf"^#{found.group(1)} {state}", log, re.MULTILINE):
            return state
    return ""


def platforms(document: object) -> list[str]:
    """색인 안의 플랫폼 매니페스트 digest. 증명 매니페스트는 뺀다."""
    return [
        str(entry.get("digest"))
        for entry in children(document)
        if "attestation-manifest" not in str(entry.get("annotations"))
    ]


def section_rebuild(probe: Probe, context: Path) -> None:
    """같은 커밋을 다시 지어 올리면(전체 다시 돌리기가 하는 일) digest 가 같은가."""
    if not ensure_builder(probe):
        probe.rounds.record("rebuild", measured=False, result="빌더를 만들지 못했다")
        return
    mark, first_tag = f"{probe.token}-R", f"sha-{secrets.token_hex(4)}"
    first = push_index(probe, context, mark, first_tag)
    base, base_document = fetch(PORT, "ri-rel/app", first_tag, body=True)
    create_tag(probe, f"{REPO}:0.7.0", f"{REPO}:{first_tag}")
    for label, extra, expected_step in (
        ("rebuild/같은 내용을 캐시로 다시 지어 올린다", (), "CACHED"),
        ("rebuild/같은 내용을 캐시 없이 다시 지어 올린다", ("--no-cache",), "DONE"),
    ):
        with probe.rounds.round(label) as slot:
            tag = f"sha-{secrets.token_hex(4)}"
            again = push_index(probe, context, mark, tag, *extra)
            after, document = fetch(PORT, "ri-rel/app", tag, body=True)
            index = "같다" if after.digest == base.digest else "다르다"
            same = platforms(document) == platforms(base_document)
            guard = attach_once(probe, f"{REPO}:0.7.0", f"{REPO}:{tag}")
            step = run_step(again.err + again.out)
            probe.note(
                slot,
                measured=first.code == 0
                and again.code == 0
                and base.kind in INDEX_TYPES
                and step == expected_step,
                result=f"색인 digest 가 {index}, 플랫폼 매니페스트 digest 가 "
                f"{'같다' if same else '다르다'}, 번호 태그 지키기는 '{guard}'",
            )


def section_load(probe: Probe, context: Path) -> None:
    if not ensure_builder(probe):
        probe.rounds.record("load", measured=False, result="빌더를 만들지 못했다")
        return
    driver = probe.run("docker", "info", "--format", "{{.Driver}} {{.DriverStatus}}").out.strip()
    snapshotter = "io.containerd.snapshotter" in driver
    store = "containerd 스냅샷 저장소" if snapshotter else f"옛 저장 방식({driver.split()[0]})"
    mark, local = f"{probe.token}-LOAD", f"ri-rel-load:{probe.token}"
    common = ("docker", "buildx", "build", "--builder", BUILDER, "--progress", "plain",
              "--build-arg", f"MARK={mark}")  # fmt: skip
    with probe.rounds.round("load/증명 없이 러너에 싣고, 뒤에 캐시로 다시 지어 올린다") as slot:
        loaded = probe.run(*common, "--provenance=false", "--load", "-t", local, str(context))
        probe.tagged.append(local)
        shown = probe.run("docker", "image", "inspect", local, "--format", "{{.Id}}")
        image_id = shown.out.strip()
        tag = f"sha-{secrets.token_hex(4)}"
        pushed = probe.run(*common, "--provenance=mode=max", "--sbom=true", "--push",
                           "-t", f"{REPO}:{tag}", str(context), timeout=600)  # fmt: skip
        document = fetch(PORT, "ri-rel/app", tag, body=True)[1]
        platform = [
            str(entry.get("digest"))
            for entry in children(document)
            if "attestation-manifest" not in str(entry.get("annotations"))
        ]
        found = fetch(PORT, "ri-rel/app", platform[0], body=True)[1] if platform else None
        manifest = as_object(found)
        config = as_object(manifest.get("config")) if manifest is not None else None
        config_digest = str(config.get("digest")) if config is not None else ""
        probe.note(
            slot,
            measured=loaded.code == 0 and pushed.code == 0 and "CACHED" in pushed.err + pushed.out,
            result=f"실은 이미지의 Id 와 올린 이미지의 config digest 가 "
            f"{'같다' if image_id and image_id == config_digest else '다르다'} ({store})",
        )
    with probe.rounds.round("load/증명을 켠 채 러너에 싣는다") as slot:
        attested = probe.run(*common, "--provenance=mode=max", "--sbom=true", "--load",
                             "-t", f"{local}-attested", str(context), timeout=600)  # fmt: skip
        probe.tagged.append(f"{local}-attested")
        probe.note(
            slot,
            measured="generating sbom" in attested.err + attested.out or attested.code != 0,
            result=f"종료 {attested.code}"
            + (f" '{attested.tail[:120]}'" if attested.code != 0 else "")
            + f" ({store})",
        )


def cleanup(probe: Probe) -> None:
    probe.run("docker", "rm", "-f", "-v", REGISTRY_NAME)
    probe.run("docker", "buildx", "rm", "-f", BUILDER)
    for reference in dict.fromkeys(probe.tagged):
        probe.run("docker", "rmi", reference)


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--sections", default=",".join(SECTIONS))
    parser.add_argument("--work", type=Path)
    arguments = parser.parse_args()
    wanted = [name for name in arguments.sections.split(",") if name]
    unknown = [name for name in wanted if name not in SECTIONS]
    if unknown:
        parser.error(f"모르는 갈래: {unknown}")
    work = arguments.work or Path(tempfile.mkdtemp(prefix="ri-rel-registry-"))
    work.mkdir(parents=True, exist_ok=True)
    probe = Probe(work=work, token=secrets.token_hex(4))
    print(f"원본 출력: {work / 'raw.log'}", flush=True)
    context = write_context(work / "context")
    runners = {
        "tags": section_tags,
        "lookup": section_lookup,
        "overwrite": section_overwrite,
        "guard": section_guard,
        "rebuild": section_rebuild,
        "load": section_load,
    }
    try:
        if not start_registry(probe):
            probe.rounds.record("준비", measured=False, result="레지스트리가 뜨지 않았다")
        else:
            for name in wanted:
                runners[name](probe, context)
    finally:
        cleanup(probe)
    print(probe.rounds.summary())
    return probe.rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
