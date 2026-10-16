"""tools/hook_large_result.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다.

결과 객체의 모양은 `.scratch/token-usage/probes/large_result/payloads.jsonl`(그 프로브가 저장한 실제
PostToolUse 페이로드)을 따른다. 끝의 시험은 그 원본에서 셈한 글자 수가 같은 호출의 기록
`tool_result` 길이에 맞는지 본다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.hook_large_result import (
    LEAD,
    READ_LIMIT,
    SHELL_LIMIT,
    HookPayload,
    ToolInput,
    context_for,
    result_chars,
)
from tools.run_hooks import registered_matchers

PAYLOADS = (
    Path(__file__).resolve().parents[2]
    / ".scratch"
    / "token-usage"
    / "probes"
    / "large_result"
    / "payloads.jsonl"
)


def _읽기(content: str, start: int = 1, **ranged: int) -> HookPayload:
    """Read 의 페이로드. `ranged` 는 Read 에 준 offset·limit 이다."""
    tool_input: ToolInput = {"file_path": "C:/scratch/big.txt"}
    if "offset" in ranged:
        tool_input["offset"] = ranged["offset"]
    if "limit" in ranged:
        tool_input["limit"] = ranged["limit"]
    lines = content.count("\n") + 1 if content else 0
    return {
        "tool_name": "Read",
        "tool_input": tool_input,
        "tool_response": {
            "type": "text",
            "file": {
                "filePath": "C:/scratch/big.txt",
                "content": content,
                "numLines": lines,
                "startLine": start,
                "totalLines": lines,
            },
        },
    }


def _셸(stdout: str, stderr: str = "", tool: str = "Bash", image: bool = False) -> HookPayload:
    return {
        "tool_name": tool,
        "tool_input": {"command": "seq 1 8000"},
        "tool_response": {
            "stdout": stdout,
            "stderr": stderr,
            "interrupted": False,
            "isImage": image,
            "noOutputExpected": False,
        },
    }


def _한_줄_글(chars: int) -> str:
    """줄 번호 접두(`1\\t`, 2자)를 더해 Read 결과가 `chars` 자가 되는 한 줄."""
    return "x" * (chars - 2)


def test_Read는_본문에_줄마다_줄_번호와_탭의_글자_수를_더한다() -> None:
    # 1~9줄은 접두 2자, 10~12줄은 3자다. 본문은 줄마다 "ab" 와 줄바꿈이고 끝 줄은 줄바꿈이 없다.
    content = "\n".join(["ab"] * 12)

    assert result_chars(_읽기(content)) == len(content) + 9 * 2 + 3 * 3


def test_Read의_줄_번호는_startLine부터_센다() -> None:
    content = "\n".join(["ab"] * 3)

    assert result_chars(_읽기(content, start=99)) == len(content) + 3 + 4 + 4


def test_Read_문턱은_2만_자를_넘을_때다() -> None:
    assert context_for(_읽기(_한_줄_글(READ_LIMIT))) is None

    context = context_for(_읽기(_한_줄_글(READ_LIMIT + 1)))

    assert context is not None
    assert context.startswith(LEAD)
    assert "20,001자" in context
    assert "20,000자" in context
    assert "C:/scratch/big.txt" in context
    assert "offset" in context
    assert "따르지 않아도 된다" in context


@pytest.mark.parametrize("ranged", [{"offset": 1}, {"limit": 5000}, {"offset": 1, "limit": 9}])
def test_범위를_준_Read는_문턱을_넘어도_침묵한다(ranged: dict[str, int]) -> None:
    assert context_for(_읽기(_한_줄_글(READ_LIMIT * 3), **ranged)) is None


@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
def test_셸_문턱은_1만_자를_넘을_때다(tool: str) -> None:
    assert context_for(_셸("x" * SHELL_LIMIT, tool=tool)) is None

    context = context_for(_셸("x" * SHELL_LIMIT, "e", tool=tool))

    assert context is not None
    assert context.startswith(LEAD)
    assert "10,001자" in context
    assert "10,000자" in context
    assert "seq 1 8000" in context
    assert "Select-Object" in context
    assert "따르지 않아도 된다" in context


def test_셸은_stdout과_stderr의_글자_수를_더한다() -> None:
    assert result_chars(_셸("a" * 7, "b" * 5)) == 12


def test_셸의_긴_명령은_앞만_든다() -> None:
    payload = _셸("x" * (SHELL_LIMIT + 1))
    payload["tool_input"] = {"command": "echo " + "y" * 500}

    context = context_for(payload)

    assert context is not None
    assert "y" * 75 + "…" in context
    assert "y" * 100 not in context


def _모양_밖(value: dict[str, object]) -> HookPayload:
    """`ToolResponse` 에 없는 칸을 든 페이로드. 훅은 실제 값의 형을 읽을 때마다 본다."""
    return json.loads(json.dumps(value))


def test_그림_결과는_0자라_침묵한다() -> None:
    picture = _모양_밖(
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "C:/scratch/pixel.png"},
            "tool_response": {
                "type": "image",
                "file": {"base64": "A" * 50_000, "type": "image/png"},
            },
        }
    )

    assert result_chars(picture) == 0
    assert context_for(picture) is None
    assert result_chars(_셸("A" * 50_000, image=True)) == 0


def test_파일로_옮겨진_셸_출력은_미리보기만_가므로_0자라_침묵한다() -> None:
    payload = _셸("1\n" * 15_000)
    response = payload.get("tool_response", {})
    response["persistedOutputPath"] = "C:/Users/u/.claude/tool-results/x.txt"
    response["persistedOutputSize"] = 38_893

    assert result_chars(payload) == 0
    assert context_for(payload) is None


def test_PDF와_노트북_결과도_0자로_센다() -> None:
    """노트북은 글이지만 못 보는 것에 적었다(거짓 음성)."""
    for kind in ("pdf", "notebook"):
        payload: HookPayload = {
            "tool_name": "Read",
            "tool_input": {"file_path": "C:/scratch/doc"},
            "tool_response": {"type": kind, "file": {"content": "x" * 50_000}},
        }
        assert result_chars(payload) == 0, kind


def test_결과_객체의_키가_바뀐_판에는_0자로_세어_침묵한다() -> None:
    payload = _모양_밖(
        {
            "tool_name": "Bash",
            "tool_input": {"command": "seq 1 8000"},
            "tool_response": {"output": "x" * 50_000},
        }
    )

    assert context_for(payload) is None


def test_결과가_객체가_아니거나_다른_도구면_보지_않는다() -> None:
    not_object = _모양_밖({"tool_name": "Bash", "tool_input": {}, "tool_response": "x" * 50_000})
    other = _모양_밖(
        {"tool_name": "Grep", "tool_input": {}, "tool_response": {"content": "x" * 50_000}}
    )

    assert context_for(not_object) is None
    assert context_for(other) is None


def test_서브에이전트의_호출에도_같은_문장을_낸다() -> None:
    """그 문장이 서브에이전트의 모델에 닿는지는 재지 않았다(못 보는 것). 입력의 `agent_id` 는
    `.scratch/harness/probes/pretool_text/` 의 B 가 본 서브에이전트 표지다."""
    payload: HookPayload = json.loads(
        json.dumps({**_읽기(_한_줄_글(READ_LIMIT + 1)), "agent_id": "a1b2c3"})
    )

    assert context_for(payload) == context_for(_읽기(_한_줄_글(READ_LIMIT + 1)))
    assert context_for(payload) is not None


def test_Read_결과에_덧붙는_리마인더는_세지_않아_문턱_바로_아래면_침묵한다() -> None:
    """리마인더는 `tool_response` 밖이라 셈에 들지 않는다(못 보는 것, 거짓 음성). 본문이 문턱보다
    50자 짧으면, 모델이 받는 글은 100자 리마인더가 붙어 문턱을 넘어도 훅은 침묵한다."""
    payload = _읽기(_한_줄_글(READ_LIMIT - 50))

    assert result_chars(payload) + 100 > READ_LIMIT
    assert context_for(payload) is None


def test_3만_자를_넘는_PowerShell_출력이_저장_키_없이_오면_잘린_stdout을_세어_알린다() -> None:
    """프로브에 그 표본이 없다(못 보는 것, 거짓 양성일 수 있다)."""
    assert context_for(_셸("x" * 30_000, tool="PowerShell")) is not None


def test_백그라운드_명령의_출력을_받는_다른_도구는_보지_않는다() -> None:
    payload = _모양_밖(
        {"tool_name": "TaskOutput", "tool_input": {}, "tool_response": {"stdout": "x" * 50_000}}
    )

    assert context_for(payload) is None


def test_같은_대상이_다시_넘어도_또_알린다() -> None:
    payload = _읽기(_한_줄_글(READ_LIMIT + 1))

    assert context_for(payload) is not None
    assert context_for(payload) is not None


def _저장한_페이로드() -> list[tuple[HookPayload, int]]:
    """프로브가 저장한 실제 페이로드와 같은 호출의 기록 본문 길이."""
    pairs: list[tuple[HookPayload, int]] = []
    for line in PAYLOADS.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        payload: HookPayload = record["payload"]
        pairs.append((payload, record["recorded"]["chars"]))
    return pairs


def test_저장한_실제_페이로드에서_셈한_글자_수가_기록의_본문_길이와_맞는다() -> None:
    """파일로 옮겨진 출력만 다르고 그 까닭은 독스트링에 적었다(0자로 센다)."""
    pairs = _저장한_페이로드()
    matched = [payload for payload, chars in pairs if result_chars(payload) == chars]
    persisted = [
        (payload, chars)
        for payload, chars in pairs
        if "persistedOutputPath" in payload.get("tool_response", {})
    ]

    assert len(pairs) == 8
    assert {payload.get("tool_name") for payload in matched} == {"Read", "Bash", "PowerShell"}
    assert len(matched) == 7
    assert len(persisted) == 1
    assert result_chars(persisted[0][0]) == 0 < persisted[0][1] < SHELL_LIMIT


def test_저장한_실제_페이로드_가운데_범위_없는_큰_Read와_큰_PowerShell만_알린다() -> None:
    noticed = {
        payload.get("tool_name"): result_chars(payload)
        for payload, _ in _저장한_페이로드()
        if context_for(payload) is not None
    }

    assert noticed == {"Read": 46_991, "PowerShell": 28_891}


def test_settings의_매처는_훅이_아는_도구_셋이다() -> None:
    """매처를 넓히면 훅이 이름으로 걸러 조용히 지나가고, 이름을 바꾸면 등록이 훅을 걸지 않는다."""
    assert registered_matchers("hook_large_result.py", "PostToolUse") == ["Read|Bash|PowerShell"]
