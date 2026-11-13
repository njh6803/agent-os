"""`tools/llm_local.py` 시험의 가짜 세계. 클라우드 없이 돈다.

외부 명령(terraform, git, 시험 자식)은 스크립트의 `execute` 한 함수를 지나고, 여기서는 그것을
`World`로 바꿔 끼운다. 모델 서버의 응답(`fetch_models`)과 시간(`pause`, `clock`), 상태 폴더의
뿌리(`state_root`), 프로세스의 명령 줄(`cmdline_of`)도 같은 방식이다. CI 의 리눅스에서도
돈다(`.claude/rules/tests.md`).
"""

from __future__ import annotations

import json
import shlex
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from tools.llm_local import Outcome

from tools import llm_local

KEY_ENV = "RUNPOD_API_KEY"
ACCOUNT_KEY = "rpa_ACCOUNT_SECRET_VALUE"
BRANCH = "feature/03-x"
COMMIT = "abc1234def5678abc1234def5678abc1234def56"
URL_1 = "https://podone-8000.proxy.runpod.net/v1"
URL_2 = "https://podtwo-8000.proxy.runpod.net/v1"
RUN_CMDLINE = ("python", "tools/llm_local.py", "run", "--yes")


class World:
    """외부 세계의 가짜. 부른 명령을 `calls`에 쌓는다."""

    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.root = tmp_path / "state-root"
        self.calls: list[tuple[str, ...]] = []
        self.child_envs: list[Mapping[str, str]] = []
        self.terraform_envs: list[tuple[tuple[str, ...], Mapping[str, str]]] = []
        self.timeouts_missing: list[tuple[str, ...]] = []
        self.terraform_version = "Terraform v1.7.1\non linux_amd64\n"
        self.branch = BRANCH
        self.apply_results: list[bool] = [True]
        self.destroy_results: list[bool] = [True]
        self.refresh_results: list[bool] = [True]
        self.pod_cost = 0.27
        self.echo_key = False
        self.child = Outcome(0, "2 passed", "")
        self.child_raises = False
        self.child_writes_pytest_files = True
        self.passed = 2
        self.alive = True
        self.alive_after_child = True
        self.child_ran = False
        self.now = 1000.0
        self.cmdlines: dict[int, tuple[str, ...]] = {}
        self.interrupt_on_git = False
        self.interrupt_on_init = False
        self.apply_times_out = False
        self.child_echoes_key = False
        monkeypatch.setattr(llm_local, "execute", self.execute)
        monkeypatch.setattr(llm_local, "fetch_models", self.fetch_models)
        monkeypatch.setattr(llm_local, "state_root", lambda: self.root)
        monkeypatch.setattr(llm_local, "cmdline_of", self.cmdline_of)
        monkeypatch.setattr(llm_local, "pause", self.pause)
        monkeypatch.setattr(llm_local, "clock", self.clock)
        monkeypatch.setenv(KEY_ENV, ACCOUNT_KEY)
        monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)

    # --- 시간과 프로세스 ---
    def pause(self, seconds: float) -> None:
        self.now += seconds

    def clock(self) -> float:
        return self.now

    def cmdline_of(self, pid: int) -> tuple[str, ...] | None:
        return self.cmdlines.get(pid)

    @property
    def folder(self) -> Path:
        return self.root / llm_local.folder_name(self.branch)

    # --- 모델 서버 ---
    def fetch_models(self, base_url: str, key: str) -> list[str] | None:
        alive = self.alive_after_child if self.child_ran else self.alive
        if not alive:
            return None
        return [m.model_id for m in llm_local.MODELS]

    # --- 외부 명령 ---
    def execute(
        self,
        argv: Sequence[str],
        *,
        env: Mapping[str, str],
        cwd: Path,
        timeout: float | None,
    ) -> Outcome:
        argv = tuple(argv)
        self.calls.append(argv)
        if timeout is None:
            self.timeouts_missing.append(argv)
        name = Path(argv[0]).name.removesuffix(".exe")
        if name == "git":
            if self.interrupt_on_git:
                raise KeyboardInterrupt
            if argv[1] == "branch":
                return Outcome(0, self.branch + "\n" if self.branch else "", "")
            return Outcome(0, COMMIT + "\n", "")
        if name == "terraform":
            return self.terraform(argv, env)
        return self.run_child(argv, env)

    def terraform(self, argv: tuple[str, ...], env: Mapping[str, str]) -> Outcome:
        self.terraform_envs.append((argv, dict(env)))
        if argv[1] == "-version":
            return Outcome(0, self.terraform_version, "")
        sub = argv[2] if argv[1].startswith("-chdir=") else argv[1]
        key = env.get("TF_VAR_server_key", "")
        echo = f"echo:{key}" if self.echo_key and key else ""
        state = self.state_path(argv) if sub in ("apply", "destroy") else Path()
        if sub == "init":
            if self.interrupt_on_init:
                raise KeyboardInterrupt
            return Outcome(0, "init ok", "")
        if sub == "output":
            return Outcome(0, json.dumps(self.outputs()), "")
        if sub == "apply" and "-refresh-only" in argv:
            ok = self.refresh_results.pop(0) if self.refresh_results else True
            return Outcome(0 if ok else 1, echo, echo)
        if sub == "apply" and self.apply_times_out:  # 시간 제한으로 죽어 상태 파일을 쓰지 못했다
            return Outcome(-1, "", "", timed_out=True)
        if sub == "apply":
            ok = self.apply_results.pop(0) if self.apply_results else True
            if not ok:
                return Outcome(1, echo, "Error: no instances available " + echo)
            self.write_state(state, key, resources=True)
            return Outcome(0, "Apply complete! " + echo, echo)
        if sub == "destroy":
            ok = self.destroy_results.pop(0) if self.destroy_results else True
            if not ok:
                return Outcome(1, echo, "Error: destroy failed " + echo)
            self.write_state(state, key, resources=False)
            return Outcome(0, "Destroy complete! " + echo, echo)
        return Outcome(2, "", f"unknown {sub}")

    def state_path(self, argv: tuple[str, ...]) -> Path:
        for arg in argv:
            if arg.startswith("-state="):
                return Path(arg.removeprefix("-state="))
        raise AssertionError(f"-state 가 없다: {argv}")

    def write_state(self, state: Path, key: str, *, resources: bool) -> None:
        if state.exists():  # 진짜 terraform 처럼 앞 상태를 백업으로 남긴다
            state.with_name(state.name + ".backup").write_text(
                state.read_text(encoding="utf-8"), encoding="utf-8"
            )
        pods = [{"type": "runpod_pod", "args": f"--api-key {key}"}] if resources else []
        body: dict[str, list[dict[str, str]]] = {"resources": pods}
        state.write_text(json.dumps(body), encoding="utf-8")
        cache = state.parent / ".tfdata" / "plan.cache"
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(f"cached {key}", encoding="utf-8")

    def outputs(self) -> dict[str, dict[str, object]]:
        return {
            "servers": {
                "value": [
                    {"n": "1", "model_id": llm_local.MODELS[0].model_id, "base_url": URL_1},
                    {"n": "2", "model_id": llm_local.MODELS[1].model_id, "base_url": URL_2},
                ]
            },
            "pods": {
                "value": [
                    {"id": "podone", "cost_per_hr": self.pod_cost},
                    {"id": "podtwo", "cost_per_hr": self.pod_cost},
                ]
            },
        }

    def run_child(self, argv: tuple[str, ...], env: Mapping[str, str]) -> Outcome:
        self.child_ran = True
        self.child_envs.append(dict(env))
        if self.child_raises:
            raise KeyboardInterrupt
        if self.child_writes_pytest_files:
            options = shlex.split(env.get("PYTEST_ADDOPTS", ""))
            junit = next(
                o.removeprefix("--junitxml=") for o in options if o.startswith("--junitxml=")
            )
            basetemp = next(
                o.removeprefix("--basetemp=") for o in options if o.startswith("--basetemp=")
            )
            total = self.passed + (0 if self.child.returncode == 0 else 1)
            failures = 0 if self.child.returncode == 0 else 1
            Path(junit).write_text(
                f'<testsuites><testsuite tests="{total}" failures="{failures}"'
                ' errors="0" skipped="0"/></testsuites>',
                encoding="utf-8",
            )
            trace = Path(basetemp) / "test_x0" / "trace.jsonl"
            trace.parent.mkdir(parents=True)
            trace.write_text(
                json.dumps({"input_tokens": 100, "output_tokens": 20}) + "\n", encoding="utf-8"
            )
        if self.child_echoes_key:
            return Outcome(0, "child saw " + env["AGENT_OS_LLM_LOCAL_1_API_KEY"], "")
        return self.child


def run_main(*args: str) -> int:
    return llm_local.main(list(args))


def printed(capsys: pytest.CaptureFixture[str]) -> str:
    captured = capsys.readouterr()
    return captured.out + captured.err


def terraform_calls(world: World, sub: str) -> list[tuple[str, ...]]:
    result: list[tuple[str, ...]] = []
    for call in world.calls:
        if Path(call[0]).name.removesuffix(".exe") != "terraform" or call[1] == "-version":
            continue
        name = call[2] if call[1].startswith("-chdir=") else call[1]
        if name == sub:
            result.append(call)
    return result


def record_files(world: World) -> list[Path]:
    return sorted((world.folder / "records").glob("*.json"))


def leave_live_lock(world: World, pid: int = 4242, cmdline: tuple[str, ...] = RUN_CMDLINE) -> None:
    world.root.mkdir(parents=True, exist_ok=True)
    lock = world.root / (llm_local.folder_name(world.branch) + ".lock")
    lock.write_text(json.dumps({"pid": pid, "started": 1.0}), encoding="utf-8")
    world.cmdlines[pid] = cmdline


def leave_resources(world: World) -> None:
    world.folder.mkdir(parents=True)
    (world.folder / llm_local.MARKER).write_text("llm_local\n", encoding="utf-8")
    (world.folder / "terraform.tfstate").write_text(
        json.dumps({"resources": [{"type": "runpod_pod"}]}), encoding="utf-8"
    )


def launch_calls(world: World) -> list[tuple[str, ...]]:
    """서버를 새로 띄우는 `terraform apply`. 상태만 맞추는 `-refresh-only`는 띄우는 것이 아니다."""
    return [c for c in terraform_calls(world, "apply") if "-refresh-only" not in c]
