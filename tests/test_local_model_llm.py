"""로컬 모델 시험. 실제 CLI 프로세스가 모델 서버에 붙어 calc 를 돌린다(`-m llm_local`).

모델 서버는 `uv run python tools/llm_local.py run` 이 Runpod 에 빌려 띄우고 이 시험이 쓸 주소와
모델 이름을 환경 변수로 넘긴다(ADR 0058). 이름은 `tools/llm_local.py` 의 상수가 원천이라 여기서
다시 적지 않는다. 필수 넷(두 모델 각각의 주소와 모델 이름)이 하나라도 없으면 skip 이 아니라
실패한다(원칙 II). 키는 선택이고 이 시험은 키 값을 읽지 않는다. 변수가 환경에 있는지만 보고 그
이름을 모델 파일의 `api_key_env` 에 적는다. 환경 검사는 마커 없이 기본 실행에서도 돈다.

calc 는 한 프로세스에서 하나의 사례를 두 모델로 매개변수화해 돈다. 단언은 `tests/test_main.py` 의
`-m llm` calc 시험과 같고 둘만 다르다. 성공한 도구 호출이 하나 이상이어야 하고, 모델 이름은
`model_id` 와 같은지가 아니라 비어 있지 않고 `unknown` 이 아닌지를 본다. 서버가 응답에 적는 이름은
서버가 정하기 때문이다. 시험 안에 다시 시도를 두지 않는다. 한 번 실패하면 실패다.
"""

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.ports import UnknownEvent
from agent_os.sdk import Event, LlmCalled, RunId, ToolCalled, parse_skill
from tools import llm_local

REPO_ROOT = Path(__file__).resolve().parents[1]

# 시험이 돌리는 서버의 필수 변수. 모델마다 앞의 둘(주소와 모델 이름)이고 키는 선택이다.
REQUIRED_VARIABLES = tuple(
    name for model in llm_local.MODELS for name in llm_local.env_names(model.number)[:2]
)
RUN_HINT = "uv run python tools/llm_local.py run"
CHILD_TIMEOUT_SECONDS = 10 * 60


def missing_variables(env: Mapping[str, str]) -> list[str]:
    """필수 변수 가운데 없거나 빈 것의 이름. 빈 값은 없는 것으로 센다."""
    return [name for name in REQUIRED_VARIABLES if not env.get(name)]


def require_variables(env: Mapping[str, str]) -> None:
    """없는 변수가 있으면 그 이름을 든 문구로 실패한다. 값은 싣지 않는다."""
    missing = missing_variables(env)
    if missing:
        raise AssertionError(
            f"로컬 모델 시험에 필요한 환경 변수가 없다: {', '.join(missing)}. "
            f"{RUN_HINT} 가 모델 서버를 띄우고 넘긴다"
        )


def model_manifest(number: int, env: Mapping[str, str]) -> str:
    """모델 `number` 의 모델 파일. 주소와 모델 이름은 환경 변수에서 온다. `max_tokens` 는 적지
    않고 `temperature` 는 0 이다. 키 변수가 환경에 있으면 그 이름만 `api_key_env` 에 적는다."""
    base_url_name, model_id_name, key_name = llm_local.env_names(number)
    lines = [
        'schema_version = "1"',
        'kind = "model"',
        f'name = "{model_name(number)}"',
        'version = "0.1.0"',
        'provider = "openai-compatible"',
        f"model_id = {json.dumps(env[model_id_name])}",
        f"base_url = {json.dumps(env[base_url_name])}",
        "temperature = 0",
    ]
    if key_name in env:
        lines.append(f'api_key_env = "{key_name}"')
    return "\n".join(lines) + "\n"


def model_name(number: int) -> str:
    return f"local-model-{number}"


def _copy_calc_plugins(root: Path) -> None:
    """저장소의 calc 와 그것이 쓰는 mcp(`everything`)와 스킬(`answer-format`), 운영자의 규칙 파일을
    임시 루트에 복사한다. 규칙 파일이 없으면 calc 의 도구 호출이 묻는다로 멈춘다."""
    for kind, name in (("agents", "calc"), ("mcp", "everything"), ("skills", "answer-format")):
        shutil.copytree(
            REPO_ROOT / "plugins" / kind / name,
            root / "plugins" / kind / name,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    shutil.copy2(REPO_ROOT / "plugins" / "rules.toml", root / "plugins" / "rules.toml")


def _events(traces: Path, run_id: str) -> list[Event]:
    trace = JsonlTrace(traces).read(RunId(run_id))
    assert trace is not None
    return [e for e in trace.events if not isinstance(e, UnknownEvent)]


def test_필수_변수가_모두_있으면_환경_검사가_통과한다() -> None:
    env = dict.fromkeys(REQUIRED_VARIABLES, "값")

    assert missing_variables(env) == []
    require_variables(env)


def test_필수_변수는_두_모델의_주소와_모델_이름_넷이고_이름은_도구의_상수가_원천이다() -> None:
    expected = [
        name for model in llm_local.MODELS for name in llm_local.env_names(model.number)[:2]
    ]

    assert list(REQUIRED_VARIABLES) == expected
    assert len(REQUIRED_VARIABLES) == 4
    assert all(name in llm_local.ENV_NAMES for name in REQUIRED_VARIABLES)


def test_필수_변수가_하나라도_없으면_없는_변수의_이름을_들고_실패한다() -> None:
    env = dict.fromkeys(REQUIRED_VARIABLES, "값")
    absent = REQUIRED_VARIABLES[2]
    del env[absent]

    with pytest.raises(AssertionError) as error:
        require_variables(env)

    message = str(error.value)
    assert absent in message
    assert all(name not in message for name in REQUIRED_VARIABLES if name != absent)
    assert RUN_HINT in message


def test_빈_값은_없는_것으로_세고_모두_없으면_넷을_다_든다() -> None:
    assert missing_variables({}) == list(REQUIRED_VARIABLES)
    assert missing_variables(dict.fromkeys(REQUIRED_VARIABLES, "")) == list(REQUIRED_VARIABLES)


def test_환경_검사_문구는_값을_싣지_않는다() -> None:
    secret = "http://secret-host:8000/v1"
    env = dict.fromkeys(REQUIRED_VARIABLES, secret)
    del env[REQUIRED_VARIABLES[0]]

    with pytest.raises(AssertionError) as error:
        require_variables(env)

    assert secret not in str(error.value)


def test_모델_파일은_주소와_모델_이름을_환경에서_받고_키_변수가_없으면_키_칸을_적지_않는다() -> (
    None
):
    base_url_name, model_id_name, _ = llm_local.env_names(1)
    env = {base_url_name: "http://model-server:8000/v1", model_id_name: "skt/A.X-4.0-Light"}

    manifest = model_manifest(1, env)

    assert 'provider = "openai-compatible"' in manifest
    assert 'base_url = "http://model-server:8000/v1"' in manifest
    assert 'model_id = "skt/A.X-4.0-Light"' in manifest
    assert "temperature = 0" in manifest
    assert "max_tokens" not in manifest
    assert "api_key_env" not in manifest


def test_키_변수가_환경에_있으면_모델_파일에_그_이름만_적고_값은_싣지_않는다() -> None:
    base_url_name, model_id_name, key_name = llm_local.env_names(2)
    secret = "비밀값-유출되면-안-된다"
    env = {
        base_url_name: "http://model-server:8000/v1",
        model_id_name: "openai/gpt-oss-20b",
        key_name: secret,
    }

    manifest = model_manifest(2, env)

    assert f'api_key_env = "{key_name}"' in manifest
    assert secret not in manifest


@pytest.mark.llm_local
@pytest.mark.parametrize("number", [model.number for model in llm_local.MODELS])
def test_calc_가_로컬_모델_서버로_답하고_트레이스에_모델_호출과_도구_호출이_남는다(
    number: int, tmp_path: Path
) -> None:
    """바깥 이음매. 실제 CLI 프로세스, 실제 모델 서버, 실제 stdio 서버. 트레이스는 tmp_path 에
    남긴다. 저장소의 플러그인을 복사한 루트에 `openai-compatible` 모델 파일 하나를 적어 `--model`
    로 준다."""
    require_variables(os.environ)
    _copy_calc_plugins(tmp_path)
    name = model_name(number)
    directory = tmp_path / "plugins" / "models" / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(model_manifest(number, os.environ), encoding="utf-8")
    traces = tmp_path / "traces"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_os.main",
            "run",
            "calc",
            # calc 의 머리 문장은 도구를 권고할 뿐이라, 암산이 되는 요청은 모델이 도구 없이 답한다
            # (gpt-oss-20b 가 그랬다, 2026-11-15 첫 실제 시험). 도구 호출이 트레이스에 남는지 보는
            # 시험이라 요청에 도구를 적는다.
            "add 도구로 17 더하기 25를 계산해 줘",
            "--traces",
            str(traces),
            "--plugins-root",
            str(tmp_path / "plugins"),
            "--model",
            name,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        timeout=CHILD_TIMEOUT_SECONDS,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "42" in result.stdout
    (trace_file,) = sorted(traces.iterdir())
    events = _events(traces, trace_file.stem)
    types = [e.type for e in events]
    assert "llm_called" in types
    assert "tool_called" in types
    assert types[-1] == "run_finished"
    # 재개의 입력이 되는 필드가 관찰이 아니라 실제 실행에서 차 있는지(ADR 0009).
    tool_calls = [e for e in events if isinstance(e, ToolCalled)]
    assert any(e.ok for e in tool_calls)
    assert any(e.tool_calls for e in events if isinstance(e, LlmCalled))
    assert any(e.args for e in tool_calls)
    assert any(e.content for e in tool_calls)
    # 모델 서버가 응답에 적는 이름은 서버가 정한다. 같은 값을 요구하지 않고 이름이 있는지만 본다.
    assert all(e.model and e.model != "unknown" for e in events if isinstance(e, LlmCalled))
    # 저장소의 스킬 문서가 파일에서 읽혀 calc 가 엮은 프롬프트로 모델에 갔다.
    skill_file = REPO_ROOT / "plugins" / "skills" / "answer-format" / "SKILL.md"
    body = parse_skill(skill_file.read_text(encoding="utf-8")).body.strip()
    assert body
    first_prompt = next(e.prompt for e in events if isinstance(e, LlmCalled) and e.prompt)
    assert body in first_prompt
