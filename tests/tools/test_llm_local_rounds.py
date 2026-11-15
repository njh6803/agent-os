"""`tools/llm_local.py` `run`의 실패 갈래, 종료 코드, 비밀 가리기, 기록 묶음의 시험.

가짜 세계는 `tests/tools/llm_local_world.py`. 종료 코드의 뜻은 스크립트의 독스트링이 원천이다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.tools.llm_local_world import (
    ACCOUNT_KEY,
    URL_1,
    URL_2,
    World,
    launch_calls,
    printed,
    record_files,
    run_main,
    terraform_calls,
)
from tools.llm_local import Outcome

from tools import llm_local


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> World:
    return World(tmp_path, monkeypatch)


def last_record(world: World) -> dict[str, llm_local.Json]:
    files = record_files(world)
    assert files, "회차 파일이 없다"
    loaded: llm_local.Json = json.loads(files[-1].read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def server_options(record: dict[str, llm_local.Json]) -> list[str]:
    options = record["server_options"]
    assert isinstance(options, list)
    return [str(o) for o in options]


# --- 시험의 판정: 0, 1, 2 ---


def test_서버가_살아_있는데_시험이_실패하면_1이다(world: World) -> None:
    world.child = Outcome(1, "1 failed", "")
    world.alive_after_child = True
    assert run_main("run", "--yes") == 1
    assert len(terraform_calls(world, "destroy")) == 1


def test_시험이_실패했는데_서버가_답하지_않으면_무효_회차_2다(world: World) -> None:
    world.child = Outcome(1, "1 failed", "")
    world.alive_after_child = False
    assert run_main("run", "--yes") == 2
    assert len(terraform_calls(world, "destroy")) == 1
    assert "무효" in str(last_record(world)["reason"])


def test_시간_제한에_걸린_시험은_실패한_시험으로_보고_서버가_살아_있으면_1이다(
    world: World,
) -> None:
    world.child = Outcome(-1, "", "", timed_out=True)
    world.alive_after_child = True
    assert run_main("run", "--yes") == 1


def test_시간_제한에_걸린_시험은_서버가_답하지_않으면_2다(world: World) -> None:
    world.child = Outcome(-1, "", "", timed_out=True)
    world.alive_after_child = False
    assert run_main("run", "--yes") == 2


def test_시험을_통과했으면_서버_확인_없이_0이다(world: World) -> None:
    world.alive_after_child = False  # 통과한 회차는 확인하지 않는다
    assert run_main("run", "--yes") == 0


def test_시험이_Ctrl_C로_끊기면_지운_뒤_2다(world: World) -> None:
    world.child_raises = True
    assert run_main("run", "--yes") == 2
    assert len(terraform_calls(world, "destroy")) == 1
    assert "끊겼" in str(last_record(world)["reason"])


def test_시험을_돌리다_뜻밖의_예외가_나도_서버를_지운_뒤_그_예외를_올린다(world: World) -> None:
    # 서버가 뜬 뒤에는 어떤 예외로 끝나도 지우기를 지나야 한다. 건너뛰면 파드가 타이머가 지울
    # 때까지(최대 90분) 청구된다.
    world.child_error = RuntimeError("뜻밖의 예외")
    with pytest.raises(RuntimeError, match="뜻밖의 예외"):
        run_main("run", "--yes")
    assert len(terraform_calls(world, "destroy")) == 1
    assert not llm_local.state_has_resources(world.folder)


def test_지우기가_실패하면_상태_폴더의_경로와_함께_3이고_시험이_실패했어도_3이다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    world.child = Outcome(1, "1 failed", "")
    world.destroy_results = [False, False]
    world.refresh_results = [True]
    code = run_main("run", "--yes")
    assert code == 3, f"종료 코드가 {code}다(3이어야 한다)"
    assert str(world.folder) in printed(capsys)
    assert (world.folder / "terraform.tfstate").exists()
    record = last_record(world)
    assert record["exit_code"] == 3
    assert record["test_exit_code"] == 1


def test_타이머가_먼저_지워_destroy가_실패하면_refresh_only로_맞춘_뒤_다시_지운다(
    world: World,
) -> None:
    world.destroy_results = [False, True]
    assert run_main("run", "--yes") == 0
    refresh = [c for c in terraform_calls(world, "apply") if "-refresh-only" in c]
    assert len(refresh) == 1
    assert len(terraform_calls(world, "destroy")) == 2


# --- 띄우기 ---


def test_재고가_없으면_다음_후보로_가고_실패한_apply_뒤에_남은_자원을_지운다(
    world: World,
) -> None:
    world.apply_results = [False, True]
    assert run_main("run", "--yes") == 0
    applies = [c for c in terraform_calls(world, "apply") if "-refresh-only" not in c]
    assert len(applies) == 2
    first_env = [e for a, e in world.terraform_envs if a in applies][:2]
    assert first_env[0]["TF_VAR_gpu_type_id"] != first_env[1]["TF_VAR_gpu_type_id"]
    assert last_record(world)["gpu"] == llm_local.candidates()[1].gpu.label


def test_후보_모두_재고가_없으면_2이고_셋째_구성으로_가지_않고_멈춘다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    world.apply_results = [False] * len(llm_local.candidates())
    assert run_main("run", "--yes") == 2
    assert world.child_envs == []
    assert "시험을 어떻게 나눌지" in printed(capsys)


def test_띄운_뒤_시간당_값의_합이_예상보다_크면_지우고_2로_끝난다(world: World) -> None:
    world.pod_cost = 0.40  # 둘의 합 0.80 > 예상 0.54
    assert run_main("run", "--yes") == 2
    assert world.child_envs == []
    assert len(terraform_calls(world, "destroy")) == 1


def test_준비_상한을_넘기면_지우고_2로_끝난다(world: World) -> None:
    world.alive = False
    assert run_main("run", "--yes") == 2
    assert world.child_envs == []
    assert world.now - 1000.0 >= llm_local.READY_LIMIT_SECONDS
    assert len(terraform_calls(world, "destroy")) == 1


# --- 비밀 ---


def test_terraform이_키를_되울려도_출력과_기록에_그_값이_없고_가린_것이_있었다고_남긴다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    world.echo_key = True
    world.apply_results = [False, True]
    assert run_main("run", "--yes") == 0
    key = world.child_envs[0]["AGENT_OS_LLM_LOCAL_1_API_KEY"]
    out = printed(capsys)
    leaked = [line for line in out.splitlines() if key in line][:1]
    assert key not in out, f"출력에 서버 키가 그대로 남았다: {leaked}"
    assert "***" in out
    record_text = record_files(world)[-1].read_text(encoding="utf-8")
    assert key not in record_text
    assert last_record(world)["terraform_output_masked"] is True


def test_가린_것이_없으면_그_칸은_거짓이다(world: World) -> None:
    assert run_main("run", "--yes") == 0
    assert last_record(world)["terraform_output_masked"] is False


def test_지우기가_성공한_회차_뒤에는_상태_폴더의_어느_파일에도_서버_키가_없다(
    world: World,
) -> None:
    assert run_main("run", "--yes") == 0
    key = world.child_envs[0]["AGENT_OS_LLM_LOCAL_1_API_KEY"].encode()
    hits = [p for p in world.folder.rglob("*") if p.is_file() and key in p.read_bytes()]
    assert hits == []
    # 백업을 지운 것이 아니라 키가 든 것만 지웠는지: 회차 파일은 남아 있다
    assert record_files(world)


def test_지우기가_실패한_회차의_상태는_sweep이_지울_때까지_그대로_둔다(world: World) -> None:
    world.destroy_results = [False, False]
    assert run_main("run", "--yes") == 3
    key = world.child_envs[0]["AGENT_OS_LLM_LOCAL_1_API_KEY"].encode()
    state = world.folder / "terraform.tfstate"
    assert state.exists() and key in state.read_bytes()


# --- 기록 묶음 ---


def test_기록_묶음은_칸을_모두_갖추고_서버_키와_주소를_싣지_않는다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_main("run", "--yes") == 0
    record = last_record(world)
    for field in (
        "commit",
        "models",
        "engine",
        "server_options",
        "gpu",
        "passed",
        "tokens",
        "elapsed_seconds",
        "cost_per_hour",
        "terraform_output_masked",
        "exit_code",
    ):
        assert field in record, field
    assert record["commit"] == "abc1234def5678abc1234def5678abc1234def56"
    assert record["models"] == [m.model_id for m in llm_local.MODELS]
    assert "0.33.0" in str(record["engine"])
    assert record["passed"] == 2
    assert record["exit_code"] == 0
    tokens = record["tokens"]
    assert isinstance(tokens, dict)
    assert tokens["input_tokens"] == 100 and tokens["output_tokens"] == 20
    key = world.child_envs[0]["AGENT_OS_LLM_LOCAL_1_API_KEY"]
    text = record_files(world)[-1].read_text(encoding="utf-8") + printed(capsys)
    assert key not in text and ACCOUNT_KEY not in text
    assert URL_1 not in text and URL_2 not in text and "proxy.runpod.net" not in text
    options = server_options(record)
    assert len(options) == len(llm_local.MODELS)
    for option in options:
        assert key not in option
        assert "--enable-auto-tool-choice" in option


def test_서버_옵션은_파서를_모델마다_다르게_싣는다(world: World) -> None:
    assert run_main("run", "--yes") == 0
    options = " ".join(server_options(last_record(world)))
    assert "--tool-call-parser hermes" in options
    assert "--tool-call-parser openai" in options


def test_자식이_pytest가_아니어서_XML이_없으면_통과_수와_토큰은_없음이고_판정은_종료_코드다(
    world: World,
) -> None:
    world.child_writes_pytest_files = False
    assert run_main("run", "--yes", "--", "python", "probe.py") == 0
    record = last_record(world)
    assert record["passed"] == "없음" and record["tokens"] == "없음"
    child = next(c for c in world.calls if c[0] == "python")
    assert child == ("python", "probe.py")


def test_이어받은_세션은_회차_파일로_연달은_무효_회차를_센다(world: World) -> None:
    world.apply_results = [False] * len(llm_local.candidates())
    assert run_main("run", "--yes") == 2
    world.now += 1.0
    world.apply_results = [False] * len(llm_local.candidates())
    assert run_main("run", "--yes") == 2
    counted = llm_local.consecutive_invalid_rounds(world.folder)
    assert counted == 2, f"연달은 무효 회차를 {counted}로 셌다"


def test_성공한_apply가_키를_되울려도_출력과_기록에_그_값이_없고_가린_것이_있었다고_남긴다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    world.echo_key = True
    assert run_main("run", "--yes") == 0
    key = world.child_envs[0]["AGENT_OS_LLM_LOCAL_1_API_KEY"]
    out = printed(capsys)
    assert key not in out
    assert key not in record_files(world)[-1].read_text(encoding="utf-8")
    masked = last_record(world)["terraform_output_masked"]
    assert masked is True, f"terraform_output_masked가 {masked}로 남았다"


def test_시험_자식의_출력에서만_가렸으면_terraform_출력_칸은_거짓이다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    world.child_echoes_key = True
    assert run_main("run", "--yes") == 0
    key = world.child_envs[0]["AGENT_OS_LLM_LOCAL_1_API_KEY"]
    out = printed(capsys)
    assert key not in out and "child saw ***" in out
    assert last_record(world)["terraform_output_masked"] is False


# --- 앞 회차의 결과와 끊긴 자리 ---


def test_앞_회차가_남긴_XML과_basetemp는_pytest가_아닌_자식의_기록에_실리지_않는다(
    world: World,
) -> None:
    stale = world.folder
    (stale / "basetemp" / "test_old0").mkdir(parents=True)
    (stale / "basetemp" / "test_old0" / "trace.jsonl").write_text(
        '{"input_tokens": 999, "output_tokens": 999}\n', encoding="utf-8"
    )
    (stale / "junit.xml").write_text(
        '<testsuites><testsuite tests="9" failures="0" errors="0" skipped="0"/></testsuites>',
        encoding="utf-8",
    )
    world.child_writes_pytest_files = False
    assert run_main("run", "--yes", "--", "python", "probe.py") == 0
    record = last_record(world)
    assert record["passed"] == "없음", f"통과 수가 {record['passed']}로 기록됐다"
    assert record["tokens"] == "없음", f"토큰이 {record['tokens']}로 기록됐다"


def test_띄우기를_시작하기_전_terraform_init에서_Ctrl_C로_끊기면_4이고_아무것도_띄우지_않는다(
    world: World,
) -> None:
    world.interrupt_on_init = True
    code = run_main("run", "--yes")
    assert code == 4, f"종료 코드가 {code}다(4여야 한다)"
    assert launch_calls(world) == []
    assert record_files(world) == []


def test_apply가_시간_제한에_걸려_상태가_없으면_다음_후보로_가지_않고_3으로_멈춘다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    world.apply_times_out = True
    code = run_main("run", "--yes")
    assert code == 3, f"종료 코드가 {code}다(3이어야 한다)"
    assert len(launch_calls(world)) == 1
    assert world.child_envs == []
    assert "Runpod" in printed(capsys)


def test_apply_도중_Ctrl_C로_끊겨_상태에_자원이_없으면_3이고_콘솔_확인을_알린다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    # 죽은 apply는 상태 파일을 쓰지 못했을 수 있다. 시간 제한 갈래와 같이 파드가 떠 있을 수
    # 있다고 알리고 멈춘다. 아무것도 띄우지 않았다(4)고 읽히면 안 된다.
    world.interrupt_on_apply = True
    code = run_main("run", "--yes")
    assert code == 3, f"종료 코드가 {code}다(3이어야 한다)"
    assert world.child_envs == []
    assert "Runpod" in printed(capsys)
    assert "끊겼" in str(last_record(world)["reason"])


def test_무효_회차가_연달으면_그_수를_찍고_둘_이상이면_멈춰_보고하라고_알린다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    world.apply_results = [False] * len(llm_local.candidates())
    assert run_main("run", "--yes") == 2
    first = printed(capsys)
    assert "연달은 무효 회차 1" in first and "멈춰" not in first
    world.now += 1.0
    world.apply_results = [False] * len(llm_local.candidates())
    assert run_main("run", "--yes") == 2
    second = printed(capsys)
    assert "연달은 무효 회차 2" in second and "멈춰" in second


# --- PR 리뷰(CodeRabbit)가 낸 지적 ---


def test_기본_시험_선택이_비어_있으면_서버를_빌리기_전에_멈추고_4다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    # 티켓 05가 `llm_local` 마커의 시험을 더하기 전에는 기본 명령의 선택이 비어, pytest가 종료
    # 코드 5로 끝난다. 서버를 먼저 띄우면 시험 하나 없는 회차에 비용만 든다.
    world.collect_result = Outcome(5, "no tests collected (2 deselected)", "")
    assert run_main("run", "--yes") == 4
    assert terraform_calls(world, "apply") == []
    assert world.child_envs == []
    text = printed(capsys)
    assert "llm_local" in text and "--" in text


def test_기본_시험_선택을_확인하지_못하면_그_출력의_끝을_보이고_서버를_빌리지_않는다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    # 마커가 선언되지 않았으면 pytest가 종료 코드 4(사용법 오류)로 끝난다. 0이 아니면 모두
    # "선택이 시험을 고른다고 확인하지 못했다"이다.
    world.collect_result = Outcome(4, "", "ERROR: 'llm_local' not found in `markers` configuration")
    assert run_main("run", "--yes") == 4
    assert terraform_calls(world, "apply") == []
    assert "not found in `markers`" in printed(capsys)


def test_비용_표만_보는_회차에서도_기본_시험_선택이_비어_있으면_먼저_알린다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    world.collect_result = Outcome(5, "no tests collected", "")
    assert run_main("run") == 4
    text = printed(capsys)
    assert "llm_local" in text and "예상 비용" not in text


def test_사용자가_명령을_주면_기본_시험_선택을_확인하지_않는다(world: World) -> None:
    world.collect_result = Outcome(5, "no tests collected", "")  # 줬다면 쓰이지 않는다
    assert run_main("run", "--yes", "--", "python", "probe.py") == 0
    assert not [c for c in world.calls if "--collect-only" in c]
    assert len(terraform_calls(world, "apply")) == 1


def test_기본_시험_선택을_확인하는_호출에도_시간_제한이_있다(world: World) -> None:
    assert run_main("run", "--yes") == 0
    assert any("--collect-only" in c for c in world.calls)
    assert not world.timeouts_missing, f"시간 제한 없는 호출: {world.timeouts_missing}"


def test_명령에_섞여_든_계정_키와_긴_비밀_꼴은_출력과_기록에_남지_않고_나머지_명령은_남는다(
    world: World, capsys: pytest.CaptureFixture[str]
) -> None:
    # `-- curl -H "Authorization: Bearer $RUNPOD_API_KEY"`처럼 셸이 키를 풀어 넣은 명령은 그 값이
    # 화면과 회차 파일(영구 저장)에 그대로 실렸다. 기록에는 알아볼 수 있는 꼴(짧은 낱말, 옵션,
    # 경로)만 남기고 나머지는 가린다.
    other = "sk-ant-api03-" + "x" * 60
    command = (
        "python",
        "probe.py",
        "--flag",
        f"Authorization: Bearer {ACCOUNT_KEY}",
        ACCOUNT_KEY,
        other,
        ".scratch/local-model/probes/live_tool_call.py",
    )
    assert run_main("run", "--yes", "--", *command) == 0
    text = record_files(world)[-1].read_text(encoding="utf-8") + printed(capsys)
    assert ACCOUNT_KEY not in text and other not in text
    recorded = last_record(world)["test_command"]
    assert isinstance(recorded, list)
    assert recorded[:3] == ["python", "probe.py", "--flag"]
    assert recorded[-1] == ".scratch/local-model/probes/live_tool_call.py"
    assert recorded[3:6] == [llm_local.MASK] * 3


def test_기본_명령은_기록에_그대로_남는다(world: World) -> None:
    assert run_main("run", "--yes") == 0
    assert last_record(world)["test_command"] == list(llm_local.DEFAULT_TEST_COMMAND)


def test_시험_자식의_환경에는_UV_ENV_FILE도_넘기지_않는다(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 자식의 `uv run`이 같은 파일을 다시 읽으면 환경에서 뺀 계정 키가 되돌아온다. 값이 이미 든
    # 부모 환경은 그대로 넘어가므로 변수만 뺀다. `UV_NO_ENV_FILE=1`은 자식이 스스로 주는
    # `--env-file`까지 끄므로 쓰지 않는다(2026-11-15 uv로 손으로 봤다).
    monkeypatch.setenv("UV_ENV_FILE", "account.env")
    assert run_main("run", "--yes") == 0
    for name in ("UV_ENV_FILE", "UV_NO_ENV_FILE"):
        assert name not in world.child_envs[0], f"자식 환경에 {name}이 넘어갔다"
