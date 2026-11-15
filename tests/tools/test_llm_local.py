"""`tools/llm_local.py`의 시험(이름, 예상 비용, 걸음 1~5, 한 바퀴). 클라우드 없이 돈다. 가짜 세계는
`tests/tools/llm_local_world.py`."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from tests.tools.llm_local_world import (
    ACCOUNT_KEY,
    KEY_ENV,
    URL_1,
    URL_2,
    World,
    launch_calls,
    leave_live_lock,
    leave_resources,
    printed,
    run_main,
    terraform_calls,
)
from tools.llm_local import Outcome

from tools import llm_local


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    return World(tmp_path, monkeypatch)


# --- 이름과 표 ---


def test_환경_변수_이름_여섯은_한_자리의_상수다() -> None:
    assert llm_local.ENV_NAMES == (
        "AGENT_OS_LLM_LOCAL_1_BASE_URL",
        "AGENT_OS_LLM_LOCAL_1_MODEL_ID",
        "AGENT_OS_LLM_LOCAL_1_API_KEY",
        "AGENT_OS_LLM_LOCAL_2_BASE_URL",
        "AGENT_OS_LLM_LOCAL_2_MODEL_ID",
        "AGENT_OS_LLM_LOCAL_2_API_KEY",
    )
    assert llm_local.env_names(2) == llm_local.ENV_NAMES[3:]


def test_상태_폴더_이름에는_구분자가_없고_다른_브랜치는_다른_이름이다() -> None:
    name = llm_local.folder_name("feature/03-llm-local")
    assert "/" not in name and "\\" not in name and ":" not in name
    assert llm_local.folder_name("a/b") != llm_local.folder_name("a_b")
    assert llm_local.folder_name("a/b") != llm_local.folder_name("a%2Fb")
    # `.`가 남으면 `<이름>.lock`과 겹치고 sweep이 그 폴더를 잠금 파일로 읽어 건너뛴다
    assert "." not in llm_local.folder_name("fix/v1.2.lock")


def test_예상_비용은_후보마다_단가_파드_수_삼십분과_구십분의_값을_찍는다() -> None:
    table = llm_local.cost_table()
    assert "RTX A5000" in table and "RTX 3090" in table and "A40" in table
    assert llm_local.PRICE_TABLE_DATE in table
    # A5000 파드 둘: 시간당 0.54 → 30분 0.27, 90분 0.81
    assert "0.54" in table and "0.27" in table and "0.81" in table
    first = llm_local.candidates()[0]
    assert (first.layout, first.gpu.label, first.pods) == ("pods", "RTX A5000", 2)
    assert llm_local.expected_cost(first, 30) == pytest.approx(0.27)
    assert llm_local.expected_cost(first, 90) == pytest.approx(0.81)


# --- 걸음 1~5: 아무것도 띄우지 않고 끝나는 길 ---


def test_모자란_환경은_이름으로_들고_4로_끝난다(
    world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv(KEY_ENV)
    world.terraform_version = "Terraform v1.5.5\n"
    world.branch = ""
    assert run_main("run", "--yes") == 4
    out = printed(capsys)
    assert KEY_ENV in out and "1.6" in out and "브랜치" in out
    assert terraform_calls(world, "apply") == []


def test_테라폼이_없으면_이름으로_들고_4로_끝난다(
    world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def missing(
        argv: Sequence[str], *, env: Mapping[str, str], cwd: Path, timeout: float | None
    ) -> Outcome:
        if Path(argv[0]).name.removesuffix(".exe") == "terraform":
            return Outcome(127, "", "찾지 못했다")
        return world.execute(argv, env=env, cwd=cwd, timeout=timeout)

    monkeypatch.setattr(llm_local, "execute", missing)
    assert run_main("run", "--yes") == 4
    assert "terraform" in printed(capsys).lower()


def test_yes_없는_run은_apply를_부르지_않고_예상_비용만_찍고_4로_끝난다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_main("run") == 4
    out = printed(capsys)
    assert llm_local.cost_table().splitlines()[0] in out
    assert terraform_calls(world, "apply") == []
    assert terraform_calls(world, "init") == []
    assert world.child_envs == []


def test_산_잠금을_만나면_아무것도_건드리지_않고_4로_끝난다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    leave_resources(world)
    leave_live_lock(world)
    assert run_main("run", "--yes") == 4
    assert "쓰고 있다" in printed(capsys)
    assert terraform_calls(world, "destroy") == [] and terraform_calls(world, "apply") == []
    assert (world.folder / "terraform.tfstate").exists()


@pytest.mark.parametrize(
    "case",
    [
        "죽은 번호",
        "다른 프로세스가 받은 번호",
        "이 스크립트의 다른 하위 명령",
        "명령 줄을 읽지 못함",
    ],
)
def test_죽은_잠금은_번호와_명령_줄로_가른다(world: World, case: str) -> None:
    if case == "죽은 번호":
        leave_live_lock(world)
        world.cmdlines.clear()
    elif case == "다른 프로세스가 받은 번호":
        leave_live_lock(world, cmdline=("vim", "notes.txt"))
    elif case == "이 스크립트의 다른 하위 명령":
        leave_live_lock(world, cmdline=("python", "tools/llm_local.py", "--help"))
    else:
        leave_live_lock(world)
        world.cmdlines.clear()
    lock = llm_local.acquire(world.root, llm_local.folder_name(world.branch))
    assert lock is not None
    lock.release()


def test_run과_sweep의_명령_줄은_산_잠금으로_읽는다(world: World) -> None:
    for sub in ("run", "sweep"):
        leave_live_lock(world, cmdline=("python", "tools/llm_local.py", sub))
        assert llm_local.acquire(world.root, llm_local.folder_name(world.branch)) is None


def test_죽은_잠금_아래_자원은_띄우기_전에_destroy하고_yes가_없으면_4로_끝난다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    leave_resources(world)
    leave_live_lock(world, pid=99)
    world.cmdlines.clear()
    assert run_main("run") == 4
    assert len(terraform_calls(world, "destroy")) == 1
    assert launch_calls(world) == []
    assert "지웠다" in printed(capsys)


def test_죽은_잠금_아래_자원을_지우지_못하면_3이고_새로_띄우지_않는다(world: World) -> None:
    leave_resources(world)
    world.destroy_results = [False, False]
    assert run_main("run", "--yes") == 3
    assert launch_calls(world) == []
    assert (world.folder / "terraform.tfstate").exists()


def test_띄우기_전에_Ctrl_C로_끊기면_4다(world: World) -> None:
    world.interrupt_on_git = True
    assert run_main("run", "--yes") == 4
    assert terraform_calls(world, "apply") == []


# --- 한 바퀴 ---


def test_통과한_회차는_서버를_띄워_시험하고_지운_뒤_0으로_끝난다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_main("run", "--yes") == 0
    assert len(terraform_calls(world, "apply")) == 1
    assert len(terraform_calls(world, "destroy")) == 1
    assert world.child_envs, "시험 자식이 돌지 않았다"
    out = printed(capsys)
    assert "통과 2" in out
    assert not world.timeouts_missing, f"시간 제한 없는 호출: {world.timeouts_missing}"


def test_자식에게_환경_변수_여섯과_서버_키를_넘기고_계정_키는_뺀다(world: World) -> None:
    assert run_main("run", "--yes") == 0
    env = world.child_envs[0]
    for name in llm_local.ENV_NAMES:
        assert env.get(name), name
    assert env["AGENT_OS_LLM_LOCAL_1_BASE_URL"] == URL_1
    assert env["AGENT_OS_LLM_LOCAL_2_BASE_URL"] == URL_2
    assert env["AGENT_OS_LLM_LOCAL_1_MODEL_ID"] == llm_local.MODELS[0].model_id
    assert env["AGENT_OS_LLM_LOCAL_2_MODEL_ID"] == llm_local.MODELS[1].model_id
    assert env["AGENT_OS_LLM_LOCAL_1_API_KEY"] == env["AGENT_OS_LLM_LOCAL_2_API_KEY"]
    assert KEY_ENV not in env, f"자식 환경에 남은 계정 키 변수: {[n for n in env if n == KEY_ENV]}"
    assert "--junitxml=" in env["PYTEST_ADDOPTS"] and "--basetemp=" in env["PYTEST_ADDOPTS"]


def test_자식에게_원래_PYTEST_ADDOPTS를_앞에_두고_그_뒤에_더한다(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTEST_ADDOPTS", "-q")
    assert run_main("run", "--yes") == 0
    assert world.child_envs[0]["PYTEST_ADDOPTS"].startswith("-q --junitxml=")


def test_terraform에는_서버_키와_상태_자리를_변수로_넘기고_계정_키는_변수로_넘기지_않는다(
    world: World,
) -> None:
    assert run_main("run", "--yes") == 0
    env = next(e for argv, e in world.terraform_envs if "apply" in argv)
    assert env["TF_VAR_server_key"] == world.child_envs[0]["AGENT_OS_LLM_LOCAL_1_API_KEY"]
    assert Path(env["TF_DATA_DIR"]).is_relative_to(world.folder)
    assert not any(k.startswith("TF_VAR_") and ACCOUNT_KEY in v for k, v in env.items())
    apply = terraform_calls(world, "apply")[0]
    assert any(a == f"-state={world.folder / 'terraform.tfstate'}" for a in apply)
