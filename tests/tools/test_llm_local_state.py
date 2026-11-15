"""`tools/llm_local.py`의 잠금, `sweep`, Terraform 구성, 실제 pytest 자식의 시험.

`sweep`이 지우는 길은 판정을 깨려는 입력(표지 없는 폴더, 뿌리 밖을 가리키는 링크, 살아 있는 잠금,
폴더 안의 링크)으로 반박한다(`.claude/rules/tools.md`). 링크는 윈도에서 junction, 리눅스에서
심볼릭 링크로 만든다. 환경이 모자라 skip 하지 않는다(`.claude/rules/tests.md`).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from tests.tools.llm_local_world import (
    World,
    leave_live_lock,
    run_main,
    terraform_calls,
)

from tools import llm_local

CONFIG = Path(__file__).resolve().parents[2] / "tools" / "llm_local_server" / "main.tf"


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    return World(tmp_path, monkeypatch)


def make_link(link: Path, target: Path) -> None:
    """`link`가 `target`을 가리키게 만든다. 윈도는 junction, 그 밖은 심볼릭 링크."""
    if sys.platform == "win32":
        done = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert done.returncode == 0, done.stderr
    else:
        os.symlink(target, link, target_is_directory=True)


def marked_folder(world: World, name: str, *, resources: bool) -> Path:
    folder = world.root / name
    folder.mkdir(parents=True)
    (folder / llm_local.MARKER).write_text("llm_local\n", encoding="utf-8")
    body: dict[str, object] = {"resources": [{"type": "runpod_pod"}] if resources else []}
    (folder / "terraform.tfstate").write_text(json.dumps(body), encoding="utf-8")
    return folder


# --- 잠금 ---


def test_같은_폴더에서_동시에_잠금을_얻으려_하면_하나만_얻는다(world: World) -> None:
    world.root.mkdir(parents=True)
    world.cmdlines[os.getpid()] = ("python", "tools/llm_local.py", "run")
    name = llm_local.folder_name(world.branch)
    barrier = threading.Barrier(8)
    results: list[llm_local.Lock | None] = []

    def attempt() -> None:
        barrier.wait()
        results.append(llm_local.acquire(world.root, name))

    threads = [threading.Thread(target=attempt) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    held = [r for r in results if r is not None]
    assert len(results) == 8 and len(held) == 1
    for lock in held:
        lock.release()


def test_판정_구간의_파일_잠금이_잡혀_있으면_기다리지_않고_산_잠금으로_본다(world: World) -> None:
    world.root.mkdir(parents=True)
    name = llm_local.folder_name(world.branch)
    with llm_local.file_guard(world.root / (name + ".guard")) as held:
        assert held
        assert llm_local.acquire(world.root, name) is None
    lock = llm_local.acquire(world.root, name)
    assert lock is not None
    lock.release()
    assert not (world.root / (name + ".lock")).exists()


def test_죽은_잠금을_치우고_새로_얻은_뒤에는_앞선_죽은_판정으로_그_잠금을_지울_수_없다(
    world: World,
) -> None:
    world.root.mkdir(parents=True)
    name = llm_local.folder_name(world.branch)
    leave_live_lock(world, pid=77)
    world.cmdlines.clear()  # 죽은 잠금
    first = llm_local.acquire(world.root, name)
    assert first is not None  # 죽은 것을 치우고 새로 얻었다
    world.cmdlines[os.getpid()] = ("python", "tools/llm_local.py", "run")
    # 같은 죽은 판정을 들고 온 둘째는 파일을 다시 읽어 산 잠금을 만난다
    assert llm_local.acquire(world.root, name) is None
    first.release()


# --- sweep ---


def test_sweep은_죽은_잠금의_폴더_자원을_destroy하고_폴더와_잠금을_지운다(world: World) -> None:
    folder = marked_folder(world, "dead", resources=True)
    key_file = folder / ".tfdata" / "x"
    key_file.parent.mkdir()
    key_file.write_text("k", encoding="utf-8")
    assert run_main("sweep") == 0
    assert len(terraform_calls(world, "destroy")) == 1
    assert not folder.exists()
    assert not (world.root / "dead.lock").exists()


def test_sweep은_자원이_없는_폴더를_terraform_없이_지운다(world: World) -> None:
    folder = marked_folder(world, "clean", resources=False)
    assert run_main("sweep") == 0
    assert terraform_calls(world, "destroy") == []
    assert not folder.exists()


def test_sweep은_지우지_못한_자원이_있으면_폴더를_두고_3이다(world: World) -> None:
    folder = marked_folder(world, "stuck", resources=True)
    world.destroy_results = [False]
    world.refresh_results = [False]
    assert run_main("sweep") == 3
    assert folder.exists()


def test_sweep은_표지_없는_폴더를_건드리지_않는다(world: World) -> None:
    world.root.mkdir(parents=True)
    other = world.root / "not-ours"
    other.mkdir()
    (other / "precious.txt").write_text("남의 파일", encoding="utf-8")
    assert run_main("sweep") == 0
    assert (other / "precious.txt").read_text(encoding="utf-8") == "남의 파일"


def test_sweep은_살아_있는_잠금의_폴더를_건드리지_않는다(world: World) -> None:
    folder = marked_folder(world, llm_local.folder_name(world.branch), resources=True)
    leave_live_lock(world)
    assert run_main("sweep") == 0
    assert folder.exists() and terraform_calls(world, "destroy") == []


def test_sweep은_뿌리_밖을_가리키는_링크를_따라가지_않는다(world: World, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / llm_local.MARKER).write_text("표지처럼 보인다\n", encoding="utf-8")
    (outside / "keep.txt").write_text("바깥", encoding="utf-8")
    world.root.mkdir(parents=True)
    make_link(world.root / "linked", outside)
    assert run_main("sweep") == 0
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "바깥"
    assert (outside / llm_local.MARKER).exists()


def test_sweep이_지우는_폴더_안의_링크는_링크만_끊고_바깥을_지키다(
    world: World, tmp_path: Path
) -> None:
    outside = tmp_path / "outside2"
    outside.mkdir()
    (outside / "keep.txt").write_text("바깥", encoding="utf-8")
    folder = marked_folder(world, "inner-link", resources=False)
    make_link(folder / "escape", outside)
    assert run_main("sweep") == 0
    assert not folder.exists()
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "바깥"


def test_sweep이_폴더를_지우는_동안_run은_그_폴더에서_잠금을_얻지_못한다(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = marked_folder(world, "busy", resources=True)
    world.cmdlines[os.getpid()] = ("python", "tools/llm_local.py", "sweep")
    seen: list[llm_local.Lock | None] = []
    inner = llm_local.destroy_folder

    def spying(target: Path, key: str | None) -> bool:
        seen.append(llm_local.acquire(world.root, "busy"))
        return inner(target, key)

    monkeypatch.setattr(llm_local, "destroy_folder", spying)
    assert run_main("sweep") == 0
    assert seen == [None]
    assert not folder.exists()


def test_sweep은_run이_먼저_잠금을_얻었으면_그_폴더를_건드리지_않는다(world: World) -> None:
    folder = marked_folder(world, "raced", resources=True)
    world.cmdlines[os.getpid()] = ("python", "tools/llm_local.py", "run")
    lock = llm_local.acquire(world.root, "raced")
    assert lock is not None
    assert run_main("sweep") == 0
    assert folder.exists() and terraform_calls(world, "destroy") == []
    lock.release()


def deep_folder(base: Path) -> Path:
    """윈도의 260자 한계를 넘는 경로(400자 남짓)를 `\\\\?\\` 접두로 만든다. 리눅스는 그냥 만든다."""
    target = base / "deep"
    for _ in range(12):
        target = target / ("d" * 30)
    made = llm_local.long_path(target)
    os.makedirs(made)
    (made / "keep.txt").write_text("서버 키 sk-deep", encoding="utf-8")
    return base / "deep"


def test_sweep이_지우는_폴더가_260자를_넘는_경로를_품어도_지운다(world: World) -> None:
    folder = marked_folder(world, "deep-folder", resources=False)
    deep_folder(folder)
    assert run_main("sweep") == 0
    assert not folder.exists()


def test_키_훑기는_260자를_넘는_경로_안의_키가_든_파일도_지운다(tmp_path: Path) -> None:
    folder = tmp_path / "state"
    folder.mkdir()
    deep = deep_folder(folder)
    llm_local.scrub_state(folder, "sk-deep")
    assert deep.exists()
    assert list(llm_local.long_path(deep).rglob("keep.txt")) == []


def test_키를_모를_때도_상태_파일과_백업은_지운다(tmp_path: Path) -> None:
    (tmp_path / "terraform.tfstate").write_text("{}", encoding="utf-8")
    (tmp_path / "terraform.tfstate.backup").write_text("{}", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("남긴다", encoding="utf-8")
    llm_local.scrub_state(tmp_path, None)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["keep.txt"]


def test_긴_경로_접두는_윈도의_절대_경로에만_붙고_정규화하지_않는다(tmp_path: Path) -> None:
    relative = Path("a") / "b."
    assert llm_local.long_path(relative) == relative
    absolute = tmp_path / "x" / "trail."
    prefixed = llm_local.long_path(absolute)
    if sys.platform == "win32":
        assert str(prefixed) == "\\\\?\\" + str(absolute)
        assert str(prefixed).endswith("trail.")
    else:
        assert prefixed == absolute


# --- Terraform 구성 ---


def test_구성의_파드_자원에는_계정_키를_싣는_변수가_없다() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    variables = re.findall(r'^variable\s+"([^"]+)"', text, flags=re.MULTILINE)
    assert variables, "변수를 읽지 못했다"
    assert not [v for v in variables if "api_key" in v or "account" in v]
    assert not re.search(r"RUNPOD_API_KEY\s*=", text)
    assert not re.search(r"var\.(runpod|api|account)", text)
    assert 'variable "server_key"' in text
    block = text[text.index('variable "server_key"') :]
    assert "sensitive" in block.split("}", 1)[0]


def test_구성은_공식_이미지와_프로바이더_판을_글자_그대로_묶고_첫째_구성은_포트_하나만_연다() -> (
    None
):
    text = CONFIG.read_text(encoding="utf-8")
    assert 'version = "= 2.0.0"' in text
    assert llm_local.VLLM_VERSION in text
    # 첫째 구성(pods)은 8000/http 하나, 둘째 구성(shared)은 서버 둘이라 8001/http가 더 든다
    assert 'local.shared ? ["8000/http", "8001/http"] : ["8000/http"]' in text
    # 컨테이너 디스크만 쓰고 저장 볼륨은 붙이지 않는다. 시작 명령은 bash로 바꾼다
    assert re.search(r"^\s*disk\s*=\s*60\s*$", text, flags=re.MULTILINE)
    assert "persistent_volume" not in text and "network_volumes" not in text
    assert 'entrypoint = ["/bin/bash", "-c"]' in text
    assert "--enable-auto-tool-choice" in text and "--api-key" in text


def _default_of(text: str, variable: str) -> str:
    block = text[text.index(f'variable "{variable}"') :].split("\n}", 1)[0]
    match = re.search(r'default\s*=\s*"?([^"\n]+)"?', block)
    assert match, f"{variable}의 기본값을 읽지 못했다"
    return match.group(1).strip()


def test_구성의_기본값과_서버_옵션은_스크립트의_상수와_어긋나지_않는다() -> None:
    text = CONFIG.read_text(encoding="utf-8")
    assert _default_of(text, "image") == llm_local.IMAGE
    assert int(_default_of(text, "timer_minutes")) == llm_local.TIMER_MINUTES
    assert float(_default_of(text, "shared_memory_utilization")) == llm_local.SHARED_UTILIZATION
    assert int(_default_of(text, "shared_kv_cache_bytes")) == llm_local.SHARED_KV_CACHE_BYTES
    for candidate in llm_local.candidates():
        for option in llm_local.server_options(candidate):
            for flag in re.findall(r"--[a-z-]+", option):
                assert flag in text, f"{flag}가 main.tf에 없다"
    shared = next(c for c in llm_local.candidates() if c.layout == "shared")
    ports = [
        int(m) for o in llm_local.server_options(shared) for m in re.findall(r"--port (\d+)", o)
    ]
    assert ports == [8000, 8001]
    assert "8000 + i" in text


def test_둘째_구성만_KV_캐시를_고정하고_서버_뒤에_health_대기_줄을_둔다() -> None:
    # 2026-11-14 파드 로그로 손으로 봤다: 한 GPU에 서버 둘을 동시에 시작하면 A.X의 KV 캐시 메모리가
    # -10.5 GiB로 잡혀 시작이 실패했다. gpt-oss가 먼저 자리를 잡은 뒤에 시작해도
    # `--gpu-memory-utilization 0.45`만으로는 남은 메모리(10.56 GiB)가 요구(19.99 GiB)보다 작아
    # 실패했다. KV 캐시를 고정하고 차례로 띄우면 섰다.
    text = CONFIG.read_text(encoding="utf-8")
    assert "--kv-cache-memory=${var.shared_kv_cache_bytes}" in text
    assert "/health" in text and "until curl" in text
    # 기다리는 줄과 KV 캐시 옵션은 둘 다 shared일 때만 든다(첫째 구성의 스크립트는 그대로다)
    assert re.search(r'local\.shared \? "until curl[^"]*" : ""', text)
    assert re.search(r'local\.shared \? "--kv-cache-memory=[^"]*" : ""', text)
    shared = next(c for c in llm_local.candidates() if c.layout == "shared")
    for option in llm_local.server_options(shared):
        assert f"--kv-cache-memory={llm_local.SHARED_KV_CACHE_BYTES}" in option
    pods = next(c for c in llm_local.candidates() if c.layout == "pods")
    assert not any("--kv-cache-memory" in o for o in llm_local.server_options(pods))


def test_health_대기_줄의_curl은_호출마다_요청_전체_시간_제한이_있다() -> None:
    # 첫 서버가 연결만 받고 응답을 끝내지 않으면 제한 없는 curl이 돌아오지 않아 둘째 서버를
    # 시작하지 못한다. 기다리는 도구가 부르는 외부 명령에는 호출마다 시간 제한을 둔다.
    text = CONFIG.read_text(encoding="utf-8")
    line = next(row for row in text.splitlines() if "until curl" in row)
    assert re.search(r"until curl[^\"]*--max-time \d+", line), line


def test_상태_폴더_자리가_링크면_아무것도_쓰거나_지우지_않고_4다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    # `root / 이름`이 다른 폴더를 가리키는 링크(윈도의 junction, 그 밖의 심볼릭 링크)면 `mkdir`이
    # 그 대상에서 성공하고, 대상 상태에 자원이 있으면 확인 전에 `terraform destroy`가 그 자원을
    # 지운다. 이 도구는 폴더를 링크로 만들지 않으므로 링크는 밖에서 온 것이다.
    target = marked_folder(world, "elsewhere", resources=True)
    before = sorted(path.name for path in target.iterdir())
    make_link(world.folder, target)
    assert run_main("run", "--yes") == 4
    assert terraform_calls(world, "destroy") == []
    assert terraform_calls(world, "apply") == []
    assert sorted(path.name for path in target.iterdir()) == before
    assert llm_local.state_has_resources(target)
    assert "링크" in capsys.readouterr().out


class _ProxyLikeHandler(BaseHTTPRequestHandler):
    """Runpod 프록시처럼 파이썬 기본 `User-Agent`를 403(`error code: 1010`)으로 거절하는 서버."""

    def do_GET(self) -> None:
        agent = self.headers.get("User-Agent", "")
        if agent.startswith("Python-urllib"):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"error code: 1010\n")
            return
        if self.headers.get("Authorization") != "Bearer secret-key":
            self.send_response(401)
            self.end_headers()
            return
        body = json.dumps({"data": [{"id": "skt/A.X-4.0-Light"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def test_준비_확인은_프록시가_거절하는_파이썬_기본_사용자_에이전트를_쓰지_않는다() -> None:
    # 2026-11-14 손으로 봤다: urllib의 기본 요청은 Runpod 프록시에서 403(`error code: 1010`)이었고
    # 다른 `User-Agent`를 붙이면 200이었다. 그 거절 때문에 서버가 떠 있어도 준비 확인이 통과하지
    # 않았다.
    server = HTTPServer(("127.0.0.1", 0), _ProxyLikeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}/v1"
        assert llm_local.fetch_models(base_url, "secret-key") == ["skt/A.X-4.0-Light"]
        assert llm_local.fetch_models(base_url, "wrong-key") is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


def test_terraform_자식은_사용자_환경의_TF_LOG_계열을_물려받지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # `TF_LOG_PATH`를 켜면 terraform의 로그가 비밀 가리기를 거치지 않고 상태 폴더 밖 파일에 써진다.
    # 프로바이더의 TRACE 로그에는 요청 내용이 실릴 수 있다(원칙 V).
    for name in ("TF_LOG", "TF_LOG_PATH", "TF_LOG_CORE", "TF_LOG_PROVIDER"):
        monkeypatch.setenv(name, "TRACE")
    env = llm_local.terraform_env(tmp_path, "sk-local-key")
    assert [name for name in env if name.startswith("TF_LOG")] == []


def test_앞_세션이_남긴_자원을_지우는_출력에서도_서버_키_꼴은_가린다() -> None:
    # 그 길은 앞 세션의 키를 모른 채(`key=None`) 돈다. 등록된 비밀만 찾으면 상태에 평문으로 남은
    # 앞 세션의 서버 키가 terraform의 실패 출력을 타고 화면에 나갈 수 있다.
    reporter = llm_local.Reporter()
    old_key = "sk-local-AbC_123-xyz"
    cleaned = reporter.clean(f"Error: destroy 실패 --api-key {old_key} 끝")
    assert old_key not in cleaned
    assert llm_local.MASK in cleaned


class _TruncatedBodyHandler(BaseHTTPRequestHandler):
    """`Content-Length`보다 짧은 본문을 보내고 연결을 닫는 서버(프록시가 응답 중간에 끊긴 꼴)."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", "1000")
        self.end_headers()
        self.wfile.write(b'{"data": [')

    def log_message(self, format: str, *args: object) -> None:
        return


def test_본문이_중간에_끊겨_들어온_응답은_예외가_아니라_답하지_않은_것으로_본다() -> None:
    # 준비 확인이 예외로 터지면 `run`이 서버를 지우지 못한 채 끝날 수 있다. 끊긴 본문은
    # `http.client.IncompleteRead`로 올라오고, 그 예외는 `OSError`도 `ValueError`도 아니다.
    server = HTTPServer(("127.0.0.1", 0), _TruncatedBodyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}/v1"
        assert llm_local.fetch_models(base_url, "secret-key") is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


def test_구성의_타이머는_이미지의_runpodctl_명령으로_파드를_멈추지_않고_지운다() -> None:
    # 2026-11-14 손으로 봤다: 이미지의 runpodctl 1.14.15는 `pod` 하위 명령이 없어 600초 뒤
    # 타이머가 `unknown command "pod"`로 실패했고, 파드 안에서 친 `runpodctl remove pod`는 주입된
    # 키로 파드를 지웠다. REST `/v2/pods/<id>`는 문서 페이지로 301이었다.
    text = CONFIG.read_text(encoding="utf-8")
    assert "sleep" in text and "runpodctl remove pod" in text
    assert "pod delete" not in text and "rest.runpod.io" not in text
    assert "pod stop" not in text and "stop pod" not in text


# --- 실제 pytest 자식 ---


def test_실제_pytest_자식이_PYTEST_ADDOPTS로_상태_폴더_안에_XML과_basetemp를_남기고_거기서_센다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    folder = tmp_path / "state"
    folder.mkdir()
    project = tmp_path / "child-project"
    project.mkdir()
    (project / "test_child.py").write_text(
        "import json\n"
        "def test_a(tmp_path):\n"
        "    (tmp_path / 'trace.jsonl').write_text(json.dumps(\n"
        "        {'input_tokens': 7, 'output_tokens': 3}) + '\\n')\n"
        "def test_b():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    env = llm_local.child_env(dict(os.environ), folder, [("u", "m", "k")] * 2)
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q"],
        cwd=project,
        env=env,
        capture_output=True,
        timeout=300,
        check=False,
    )
    assert done.returncode == 0, done.stdout.decode(errors="replace")
    assert (folder / "junit.xml").is_file()
    assert (folder / "basetemp").is_dir()
    results = llm_local.read_results(folder)
    assert results.passed == 2
    assert results.tokens is not None
    assert (results.tokens.input_tokens, results.tokens.output_tokens) == (7, 3)


def test_시간_제한에_걸린_명령은_손자_프로세스까지_끊는다(tmp_path: Path) -> None:
    """`uv run pytest`는 pytest를 손자로 띄운다. 직계 자식만 죽이면 서버를 지운 뒤에도
    시험이 돈다."""
    pidfile = tmp_path / "grandchild.pid"
    marker = "time.sleep(" + "321)"  # 한 덩어리로 적지 않아야 실패 출력의 표지로 쓸 수 있다
    script = tmp_path / "child.py"
    script.write_text(
        "import pathlib, subprocess, sys, time\n"
        f"grand = subprocess.Popen([sys.executable, '-c', 'import time; {marker}'])\n"
        f"pathlib.Path({str(pidfile)!r}).write_text(str(grand.pid))\n"
        "time.sleep(321)\n",
        encoding="utf-8",
    )
    outcome = llm_local.execute(
        (sys.executable, str(script)), env=dict(os.environ), cwd=tmp_path, timeout=10
    )
    assert outcome.timed_out
    assert pidfile.is_file(), "손자를 띄우기 전에 제한이 걸렸다(제한이 짧다)"
    pid = int(pidfile.read_text(encoding="utf-8"))
    words: tuple[str, ...] | None = None
    for _ in range(50):
        words = llm_local.cmdline_of(pid)
        if words is None or not any(marker in word for word in words):
            return
        time.sleep(0.2)
    raise AssertionError(f"끊지 못한 손자 프로세스 {pid}의 명령 줄: {words}")


def test_pytest가_아닌_자식이면_결과를_없음으로_읽는다(tmp_path: Path) -> None:
    results = llm_local.read_results(tmp_path)
    assert results.passed is None and results.tokens is None
