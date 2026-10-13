"""tests/tools/test_open_session.py 의 사례를 pwsh 하나에 묶는 길을 잰다(ADR 0030 이력).

지금의 이음매(`_call`)는 사례마다 pwsh 를 띄운다. 이 프로브는 pwsh 하나를 서버로 띄워 두고 사례마다
새 runspace 에서 부르는 `_call` 을 지어, ADR 0030 Consequences 가 묶을 때의 조건으로 든 셋을 잰다.
서버는 스크립트의 AST 를 한 번 파싱하고, 요청마다 새 runspace 에서 지금의 `_LOAD` 와 같은 순서로
고른 함수를 정의하고 `$given` 을 만든 뒤 본문을 돌린다. 경고와 정보(`Write-Host`) 스트림은 출력에
합쳐 차례를 지킨다. 요청과 답은 한 줄짜리 JSON 이고, 답 줄은 표지(`REPLY`)로 시작해 다른 출력과
가른다. 사례가 끝나면 그 사례가 바꾼 환경 변수를 되돌린다. 사례 하나의 시간 제한을 넘기면 서버를
끝내고 다음 요청이 새로 띄운다.

갈래:
- pytest <인자...>: 시험 모듈의 `_call` 을 서버판으로 바꿔 pytest 를 돈다. 바꿔치지 못하면 4로
  멈추고, 끝에 요청과 서버 기동의 수를 표지(`MARKER`)와 함께 찍는다. 아래 둘이 이것을 부른다.
- contract: 지금의 `_call` 과 서버판에 같은 요청을 주어 종료 코드·stdout·stderr 를 견준다(조건
  하나). 같아야 하는 요청(`_MUST_MATCH`)은 판정하고, 갈릴 것으로 본 요청(`_MAY_DIFFER`)은 결과만
  적는다. 그리고 환경 변수(조건 둘)와 전역 변수가 다음 사례에 보이는지, 되돌림을 끈 서버의 양성
  대조, 시간 제한의 까닭과 그 뒤 다음 요청이 도는지를 본다. 기대와 다른 것이 있으면 1로 끝난다.
- time [--rounds N]: 시험 파일 전체를 지금의 `_call` 과 서버판으로 번갈아 돌려 pytest 의 초를 낸다.
  서버판 회차는 출력에 표지가 있을 때만 측정으로 센다.
- mutate: open_session 의 변이 표 셋을 서버판 러너로 다시 돌린다(조건 셋). 시험 파일을 고치는 변이는
  지금의 `_call` 을 재는 것이라 뺀다. 임시 표를 지어 `tools/mutate.py` 에 넘기고 그 종료 코드로
  끝난다. 러너가 바꿔치지 못하면 4로 끝나 변이 도구가 오류로 판정하므로, 빨강은 서버판이 낸 것이다.

못 보는 것: ubuntu 러너에서의 동작(Windows 의 pwsh 7.6.6 에서만 돌렸다), 서버가 띄운 runspace 가
다시 띄우는 손자 프로세스(지금 시험에는 없다), runspace 사이에 남는 .NET 정적 상태(지금 시험은
정적 멤버를 가진 PowerShell 클래스 하나를 정의하고, 그것을 정의하는 focus 시험 둘이 서버판에서
이어서 통과했다).

돌리는 법: 저장소 루트에서 `PYTHONUTF8=1 uv run python .scratch/harness/probes/pwsh_case_server.py
<갈래>`. pwsh 가 PATH 에 있어야 한다. 시험 모듈의 비공개 이름(`_call`, `_TIMEOUT_SEC`)에 기대므로 그
이름이 바뀌면 멈춘다. `mutate` 는 이 체크아웃의 파일(`tools/open_session.ps1`,
`.claude/skills/open-session/SKILL.md`)을 고쳤다가 되돌리므로 도는 동안 그 체크아웃에서 다른 실행을
하지 않는다.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import IO

import pytest

ROOT = Path(__file__).resolve().parents[3]
TEST_FILE = ROOT / "tests" / "tools" / "test_open_session.py"
SCRIPT = ROOT / "tools" / "open_session.ps1"
TABLES = [
    ROOT / ".scratch" / "harness" / "probes" / f"open_session_{name}_mutations.toml"
    for name in ("quit", "model_line", "regression")
]
REPLY = "@@reply "
MARKER = "pwsh 서버판 _call:"
SUMMARY = re.compile(r"^(\d+) passed in ([\d.]+)s")

# 지금의 `_LOAD` 와 같은 순서다. 함수를 정의하고(없으면 그 이름으로 던진다) `$given` 을 만든 뒤
# 본문을 돈다. 출력은 `Out-String -Stream` 으로 콘솔과 같은 줄로 바꾼다. 종료 오류는 `Invoke` 가
# 던지고, 그 전의 출력은 넘긴 목록에 남는다. 경고·정보 스트림은 `MergeMyResults` 로 출력에 합치면
# 차례가 지켜진다(둘 다 스크래치패드에서 손으로 봤다).
_SERVER = r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$language = 'System.Management.Automation.Language'
$ast = ("$language.Parser" -as [type])::ParseFile($env:OPEN_SESSION_SCRIPT, [ref]$null, [ref]$null)
$definition = "$language.FunctionDefinitionAst" -as [type]
$restore = -not $env:OPEN_SESSION_NO_RESTORE
$resultTypes = [System.Management.Automation.Runspaces.PipelineResultTypes]
$in = [Console]::In
$out = [Console]::Out
while ($null -ne ($line = $in.ReadLine())) {
    $req = $line | ConvertFrom-Json
    $saved = [Environment]::GetEnvironmentVariables()
    $results = [System.Collections.Generic.List[psobject]]::new()
    $terminating = $null
    $rs = [runspacefactory]::CreateRunspace()
    $ps = [powershell]::Create()
    try {
        $rs.Open()
        $ps.Runspace = $rs
        $rs.SessionStateProxy.SetVariable('ast', $ast)
        $rs.SessionStateProxy.SetVariable('givenJson', $req.given)
        $texts = foreach ($name in $req.function -split ',' | Where-Object { $_ }) {
            $isTarget = {
                param($node) $node -is $definition -and $node.Name -eq $name
            }.GetNewClosure()
            $fn = $ast.Find($isTarget, $true)
            if ($null -eq $fn) { throw "$name 가 스크립트에 없다" }
            $fn.Extent.Text
        }
        $script = @(
            "`$PSStyle.OutputRendering = 'PlainText'"
            $texts
            '$given = $givenJson | ConvertFrom-Json'
            $req.body
        ) -join "`n"
        $command = [System.Management.Automation.Runspaces.Command]::new($script, $true)
        $command.MergeMyResults($resultTypes::Warning, $resultTypes::Output)
        $command.MergeMyResults($resultTypes::Information, $resultTypes::Output)
        [void]$ps.Commands.AddCommand($command)
        [void]$ps.AddCommand('Out-String').AddParameter('Stream')
        [void]$ps.Invoke($null, $results)
    } catch {
        $e = $_.Exception
        $wrapped = $e -is [System.Management.Automation.MethodInvocationException]
        if ($wrapped -and $e.InnerException) {
            $e = $e.InnerException
        }
        $terminating = $e.Message
    } finally {
        $errors = @($ps.Streams.Error | ForEach-Object { $_.ToString() })
        $ps.Dispose()
        $rs.Dispose()
        if ($restore) {
            $now = [Environment]::GetEnvironmentVariables()
            foreach ($key in @($now.Keys)) {
                if (-not $saved.Contains($key)) {
                    [Environment]::SetEnvironmentVariable($key, $null)
                }
            }
            foreach ($key in @($saved.Keys)) {
                if ($now[$key] -cne $saved[$key]) {
                    [Environment]::SetEnvironmentVariable($key, $saved[$key])
                }
            }
        }
    }
    $failed = $errors.Count -gt 0 -or $null -ne $terminating
    if ($null -ne $terminating) { $errors += $terminating }
    $reply = [ordered]@{
        code = if ($failed) { 1 } else { 0 }
        stdout = ($results | ForEach-Object { "$_`n" }) -join ''
        stderr = $errors -join "`n"
    }
    $json = $reply | ConvertTo-Json -Compress -EscapeHandling EscapeNonAscii
    $out.WriteLine($env:OPEN_SESSION_REPLY + $json)
    $out.Flush()
}
"""


class ServerCall:
    """지금의 `_call` 과 같은 모양으로 부르는 서버판. 서버는 첫 요청과 시간 제한 뒤에 띄운다.

    `server_env` 는 서버 프로세스의 환경에 더할 값이다. 양성 대조가 되돌림을 끌 때 쓴다.
    """

    def __init__(self, default_timeout: float, server_env: Mapping[str, str] | None = None) -> None:
        self._default_timeout = default_timeout
        self._server_env = dict(server_env or {})
        self._proc: subprocess.Popen[str] | None = None
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._stderr: IO[bytes] | None = None
        self.requests = 0
        self.starts = 0

    def _start(self) -> subprocess.Popen[str]:
        env = {
            **os.environ,
            "OPEN_SESSION_SCRIPT": str(SCRIPT),
            "OPEN_SESSION_REPLY": REPLY,
            **self._server_env,
        }
        if self._stderr is not None:
            self._stderr.close()
        self._stderr = tempfile.TemporaryFile()
        proc = subprocess.Popen(
            ["pwsh", "-NoProfile", "-NonInteractive", "-Command", _SERVER],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._stderr,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        lines: queue.Queue[str | None] = queue.Queue()
        stdout = proc.stdout
        assert stdout is not None

        def pump() -> None:
            for line in stdout:
                lines.put(line)
            lines.put(None)

        threading.Thread(target=pump, daemon=True).start()
        self._proc, self._lines = proc, lines
        self.starts += 1
        return proc

    def _server_stderr(self) -> str:
        if self._stderr is None:
            return ""
        self._stderr.seek(0)
        return self._stderr.read().decode("utf-8", "replace")[-2000:]

    def close(self) -> None:
        if self._proc is not None and self._proc.stdin is not None:
            self._proc.stdin.close()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None

    def __call__(
        self, function: str, body: str, given: dict[str, object], timeout: float | None = None
    ) -> subprocess.CompletedProcess[str]:
        limit = self._default_timeout if timeout is None else timeout
        # 지금의 `_call` 처럼 사례 하나의 전체 시간을 센다. 서버를 띄우는 시간도 든다.
        deadline = time.monotonic() + limit
        proc = self._proc if self._proc is not None and self._proc.poll() is None else self._start()
        assert proc.stdin is not None
        self.requests += 1
        request = {"function": function, "body": body, "given": json.dumps(given)}
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()
        noise: list[str] = []
        while True:
            try:
                line = self._lines.get(timeout=max(0.0, deadline - time.monotonic()))
            except queue.Empty:
                proc.kill()
                proc.wait()
                self._proc = None
                pytest.fail(
                    f"pwsh 가 {limit:g}초 안에 끝나지 않았다. "
                    "대기 루프가 끝나지 않는 회귀일 수 있다"
                )
            if line is None:
                self._proc = None
                pytest.fail(f"pwsh 서버가 끝났다: {''.join(noise)}{self._server_stderr()}")
            # 본문이 줄바꿈 없이 콘솔에 쓰면 답 표지가 그 줄 가운데에 붙는다(PR 직전 리뷰).
            at = line.find(REPLY)
            if at >= 0:
                noise.append(line[:at])
                break
            noise.append(line)
        reply = json.loads(line[at + len(REPLY) :])
        return subprocess.CompletedProcess(
            args=["pwsh-server", function],
            returncode=int(reply["code"]),
            stdout="".join(noise) + str(reply["stdout"]),
            stderr=str(reply["stderr"]),
        )


class ServerPlugin:
    """시험 모듈의 `_call` 을 서버판으로 바꾼다. 바꿔치지 못하면 pytest 를 4로 멈춘다."""

    def __init__(self) -> None:
        self._calls: list[ServerCall] = []

    # `-k` 가 고르기 전에 모은 시험 전부를 본다.
    @pytest.hookimpl(tryfirst=True)
    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        patched: set[str] = set()
        for item in items:
            module = getattr(item, "module", None)
            if not isinstance(module, ModuleType) or module.__file__ is None:
                continue
            if Path(module.__file__).resolve() != TEST_FILE or module.__name__ in patched:
                continue
            call = ServerCall(float(module._TIMEOUT_SEC))
            self._calls.append(call)
            module._call = call
            patched.add(module.__name__)
        if not patched:
            pytest.exit(f"{TEST_FILE} 의 시험을 모으지 못해 `_call` 을 바꾸지 못했다", returncode=4)

    def pytest_terminal_summary(self, terminalreporter: pytest.TerminalReporter) -> None:
        requests = sum(call.requests for call in self._calls)
        starts = sum(call.starts for call in self._calls)
        terminalreporter.write_line(f"{MARKER} 요청 {requests}, 서버 기동 {starts}")

    def pytest_unconfigure(self) -> None:
        for call in self._calls:
            call.close()


def _load_test_module() -> ModuleType:
    # 시험 모듈이 `tools` 를 import 한다. pytest 는 `pythonpath` 설정으로 루트를 넣는다.
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("open_session_server_probe", TEST_FILE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"{TEST_FILE} 를 불러오지 못했다")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


type Call = Callable[..., subprocess.CompletedProcess[str]]
type Request = tuple[str, str, str, dict[str, object]]

# (이름, 함수, 본문, given). 두 `_call` 이 같은 종료 코드·stdout 을 내고, 서버가 낸 오류 글이 같은
# 차례로 지금의 stderr 에 들어야 한다.
_MUST_MATCH: list[Request] = [
    ("없는 함수", "No-Such-Function", "'x'", {}),
    ("출력 뒤의 종료 오류", "", "'before'\nthrow 'boom'", {}),
    ("마지막 문장의 종료하지 않는 오류", "", "'before'\nWrite-Error 'soft'", {}),
    ("오류 둘의 차례", "", "Write-Error 'e1'\nWrite-Error 'e2'", {}),
    # runspace 의 `HadErrors` 는 잡은 종료 오류에도 참이라 그것으로 종료 코드를 정하면 focus 시험이
    # 빨갰다. 서버는 오류 스트림에 남은 기록으로 정한다.
    ("잡은 종료 오류", "", "try { throw 'x' } catch { 'caught' }", {}),
    ("호스트 출력의 차례", "", "'a'\nWrite-Host 'hosted'\n'b'", {}),
    ("줄바꿈 없는 콘솔 출력", "", "[Console]::Out.Write('partial')\n'after'", {}),
    ("여러 줄과 끝 공백", "", "'a  '\n''\n'b'", {}),
    ("한글과 전각 슬래시", "Normalize-Slash", "Normalize-Slash $given.text", {"text": "／한글"}),
    ("given 의 null 과 중첩", "", '"[$($given.a)]"\n$given.b.c', {"a": None, "b": {"c": "x"}}),
    ("스크립트의 인자", "", "$ast.ParamBlock.Parameters.Count", {}),
    ("스크립트의 종료 오류", "Get-EffortSteps,Read-ModelLine", "Read-ModelLine '모델: x'", {}),
]

# 두 `_call` 이 갈릴 것으로 본 요청. 결과를 적어 두고 판정하지 않는다.
_MAY_DIFFER: list[Request] = [
    ("앞 문장의 종료하지 않는 오류", "", "Write-Error 'soft'\n'after'", {}),
    # 지금의 `_call` 은 콘솔 호스트가 경고 앞에 지역화된 머리를 붙인다.
    ("경고", "", "'a'\nWrite-Warning 'warn'\n'b'", {}),
    # 아래 셋은 PR 직전 버그·성능 리뷰가 짚었다. 서버판은 정보 스트림을 선호도와 무관하게 합치고,
    # 콘솔의 오류 쓰기는 서버 프로세스의 stderr 로 가며, 종료 코드는 `$LASTEXITCODE` 를 보지 않는다.
    ("정보 스트림", "", "Write-Information 'info'\n'after'", {}),
    ("콘솔 오류에 직접 쓰기", "", "[Console]::Error.WriteLine('direct')\n'after'", {}),
    ("마지막 네이티브 명령의 실패", "", "'before'\ncmd /c exit 3", {}),
]


def _same_errors(process: str, server: str) -> bool:
    """한쪽만 비지 않고, 서버가 낸 오류 글이 모두 같은 차례로 지금의 stderr 에 든다.

    지금의 stderr 는 `-Command` 가 오류 글 앞뒤에 코드 발췌(`Line |`, `~~~`)를 붙인 것이고 서버는
    오류 글만 낸다. 시험은 오류 글을 단언하므로 발췌는 견주지 않는다. 공백은 하나로 접어 견준다.
    """
    flat = " ".join(process.split())
    messages = [" ".join(line.split()) for line in server.splitlines() if line.strip()]
    if bool(process.strip()) != bool(messages):
        return False
    at = 0
    for message in messages:
        found = flat.find(message, at)
        if found < 0:
            return False
        at = found + len(message)
    return True


def _compare(process: Call, server: Call) -> int:
    misses = 0
    for kind, requests in (("판정", _MUST_MATCH), ("참고", _MAY_DIFFER)):
        for name, function, body, given in requests:
            a = process(function, body, given)
            b = server(function, body, given)
            same = (
                a.returncode == b.returncode
                and a.stdout.rstrip("\n") == b.stdout.rstrip("\n")
                and _same_errors(a.stderr, b.stderr)
            )
            if kind == "판정" and not same:
                misses += 1
            print(
                f"{kind} {'같다' if same else '다르다'} {name}: "
                f"process=({a.returncode}, {a.stdout.rstrip()!r}) "
                f"server=({b.returncode}, {b.stdout.rstrip()!r}, {b.stderr!r})"
            )
    return misses


def _isolation(server: ServerCall, unrestored: ServerCall) -> int:
    misses = 0
    for label, call, expected in [
        ("되돌림", server, "[]"),
        ("되돌림 없음(양성 대조)", unrestored, "[x]"),
    ]:
        call("", "$env:OPEN_SESSION_PROBE_LEAK = 'x'", {})
        seen = call("", '"[$env:OPEN_SESSION_PROBE_LEAK]"', {}).stdout.strip()
        misses += 0 if seen == expected else 1
        print(f"판정 {'기대대로' if seen == expected else '어긋남'} 환경 변수 {label}: {seen}")
    server("", "$global:probeLeak = 'x'", {})
    seen = server("", '"[$global:probeLeak]"', {}).stdout.strip()
    misses += 0 if seen == "[]" else 1
    print(f"판정 {'기대대로' if seen == '[]' else '어긋남'} 전역 변수: {seen}")
    return misses


def _timeout(server: ServerCall) -> int:
    misses = 0
    try:
        server("", "Start-Sleep -Seconds 30", {}, timeout=3)
        print("판정 어긋남 시간 제한: 끝나지 않는 요청이 돌아왔다")
        misses += 1
    except pytest.fail.Exception as failed:
        # 서버가 뜨지 못해 끝나도 같은 예외라 까닭까지 본다.
        ok = "3초 안에 끝나지 않았다" in str(failed)
        misses += 0 if ok else 1
        print(f"판정 {'기대대로' if ok else '어긋남'} 시간 제한: {failed}")
    after = server("", "'ok'", {}).stdout.strip()
    misses += 0 if after == "ok" else 1
    print(f"판정 {'기대대로' if after == 'ok' else '어긋남'} 시간 제한 뒤의 요청: {after}")
    return misses


def _contract() -> int:
    module = _load_test_module()
    limit = float(module._TIMEOUT_SEC)
    server = ServerCall(limit)
    unrestored = ServerCall(limit, server_env={"OPEN_SESSION_NO_RESTORE": "1"})
    try:
        misses = _compare(module._call, server)
        misses += _isolation(server, unrestored)
        misses += _timeout(server)
    finally:
        server.close()
        unrestored.close()
    return 1 if misses else 0


class NotMeasured(Exception):
    """pytest 가 실패 없이 통과하지 않았거나 표지가 기대와 달라 그 회차가 측정이 아니다."""


def _pytest_seconds(command: Sequence[str], marked: bool) -> tuple[int, float]:
    done = subprocess.run(
        [*command, "-q", "-p", "no:cacheprovider", str(TEST_FILE.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    lines = done.stdout.strip().splitlines()
    last = lines[-1] if lines else ""
    match = SUMMARY.match(last)
    if done.returncode != 0 or match is None:
        raise NotMeasured(repr(last))
    if marked != any(line.startswith(MARKER) for line in lines):
        raise NotMeasured(f"표지가 {'없다' if marked else '있다'}")
    return int(match.group(1)), float(match.group(2))


def _time(rounds: int) -> int:
    commands = {
        "process": ([sys.executable, "-m", "pytest"], False),
        "server": ([sys.executable, str(Path(__file__).resolve()), "pytest"], True),
    }
    misses = 0
    for round_no in range(1, rounds + 1):
        order = ["process", "server"] if round_no % 2 else ["server", "process"]
        shown: list[str] = []
        for kind in order:
            command, marked = commands[kind]
            try:
                cases, seconds = _pytest_seconds(command, marked)
                shown.append(f"{kind}={cases}개 {seconds:.2f}s")
            except NotMeasured as miss:
                misses += 1
                shown.append(f"{kind}=측정 아님({miss})")
        print(f"round={round_no} first={order[0]} " + " ".join(shown))
    return 1 if misses else 0


def _toml_value(value: object) -> str:
    # JSON 의 문자열·정수·배열 표기는 TOML 의 기본 문자열·정수·배열로도 읽힌다.
    return json.dumps(value, ensure_ascii=False)


def _mutate() -> int:
    blocks = [
        "[runner.server]",
        f"command = {_toml_value([sys.executable, str(Path(__file__).resolve()), 'pytest'])}",
        'judge = "pytest"',
        "",
    ]
    skipped: list[str] = []
    for table in TABLES:
        spec = tomllib.loads(table.read_text(encoding="utf-8"))
        for mutation in spec["mutation"]:
            edits = mutation.pop("edit")
            if any(str(edit["file"]).startswith("tests/") for edit in edits):
                skipped.append(f"{table.name}: {mutation['name']}")
                continue
            mutation["name"] = f"{table.stem.removeprefix('open_session_')}: {mutation['name']}"
            mutation["runner"] = "server"
            blocks.append("[[mutation]]")
            blocks += [f"{key} = {_toml_value(value)}" for key, value in mutation.items()]
            for edit in edits:
                blocks.append("[[mutation.edit]]")
                blocks += [f"{key} = {_toml_value(value)}" for key, value in edit.items()]
            blocks.append("")
    for name in skipped:
        print(f"뺐다(시험 파일을 고치는 변이): {name}")
    sys.stdout.flush()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "pwsh_case_server_mutations.toml"
        path.write_text("\n".join(blocks), encoding="utf-8")
        done = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "mutate.py"), str(path)], cwd=ROOT, check=False
        )
    return done.returncode


def main() -> int:
    # pytest 의 인자는 argparse 가 해석하지 않고 그대로 넘긴다.
    if len(sys.argv) > 1 and sys.argv[1] == "pytest":
        return int(pytest.main(sys.argv[2:], plugins=[ServerPlugin()]))
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="kind", required=True)
    sub.add_parser("contract")
    timing = sub.add_parser("time")
    timing.add_argument("--rounds", type=int, default=2)
    sub.add_parser("mutate")
    args = parser.parse_args()
    match args.kind:
        case "contract":
            return _contract()
        case "time":
            return _time(args.rounds)
        case "mutate":
            return _mutate()
        case other:
            raise SystemExit(f"모르는 갈래: {other}")


if __name__ == "__main__":
    raise SystemExit(main())
