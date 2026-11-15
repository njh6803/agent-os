"""`.scratch/local-model/probes/live_tool_call.py`(`run`의 `--` 뒤 자식으로 도는 프로브)의 시험.

프로브는 서버 키를 `Authorization` 헤더로 보낸다. 키 뒤에 개행이 붙은 채로 독립 실행하면(README가
안내한 길, 부모 명령의 비밀 가리기가 없다) 파이썬의 `http.client`가 헤더 값을 담은 `ValueError`를
내고, 프로브의 회차 기록과 마지막 요약이 그 글을 그대로 찍었다.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType

import pytest

PROBE = (
    Path(__file__).resolve().parents[2]
    / ".scratch"
    / "local-model"
    / "probes"
    / "live_tool_call.py"
)
SECRET = "sk-local-NEWLINE_SECRET_VALUE"


def load_probe() -> ModuleType:
    spec = importlib.util.spec_from_file_location("live_tool_call_under_test", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def set_servers(monkeypatch: pytest.MonkeyPatch, key: str) -> None:
    environment: Mapping[str, str] = {
        "AGENT_OS_LLM_LOCAL_1_BASE_URL": "http://127.0.0.1:9/v1",
        "AGENT_OS_LLM_LOCAL_1_MODEL_ID": "model-one",
        "AGENT_OS_LLM_LOCAL_1_API_KEY": key,
        "AGENT_OS_LLM_LOCAL_2_BASE_URL": "http://127.0.0.1:9/v1",
        "AGENT_OS_LLM_LOCAL_2_MODEL_ID": "model-two",
        "AGENT_OS_LLM_LOCAL_2_API_KEY": key,
    }
    for name, value in environment.items():
        monkeypatch.setenv(name, value)


def test_헤더로_보낼_수_없는_꼴의_키는_요청_전에_값_없이_거절한다() -> None:
    probe = load_probe()
    for bad in (SECRET + "\n", SECRET + "\r\n", "sk-local-a b", "sk-local-한글"):
        with pytest.raises(ValueError, match="헤더") as caught:
            probe.ask("http://127.0.0.1:9/v1", "model", bad)
        shown = f"{caught.value!r} {caught.value}"
        assert bad.strip() not in shown, shown
        assert "NEWLINE_SECRET_VALUE" not in shown, shown


def test_키에_개행이_섞여_독립_실행해도_회차_기록과_요약에_키가_없고_종료_코드는_1이다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    probe = load_probe()
    set_servers(monkeypatch, SECRET + "\n")
    assert probe.main() == 1
    seen = capsys.readouterr()
    assert "NEWLINE_SECRET_VALUE" not in seen.out + seen.err
