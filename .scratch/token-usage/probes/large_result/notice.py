"""`tools/hook_large_result.py` 의 알림(`additionalContext`)이 실제 세션의 모델에게 닿는지 본다(티켓
06, `.claude/rules/tools.md` 의 새 훅이 함께 하는 넷).

픽스처는 `run.py` 의 것을 같은 출력 디렉터리에 짓는다.
- B_notice: 등록 모양(래퍼를 거쳐)의 실제 훅과 탐침 훅(`dump_posttool.py`)을 붙이고, `lines.txt`
  (줄 번호를 붙여 46991자)를 범위 없이 Read 한 뒤 그 호출에 붙어 온 훅 알림의 첫 문장을 묻는다.
  탐침 기록이 그 Read 하나이고 범위가 없을 때 측정이다. 답이 훅의 첫 문장(`LEAD`)을 옮기면 닿은
  것이다.
- C_control: B 의 대조군. `korean.txt`(425자)를 범위 없이 Read 한다. 탐침 기록이 그 Read 하나일 때
  측정이고, 답이 그 문장 없이 '알림 없음' 이면 기대대로다.
stream-json 에는 훅의 additionalContext 가 실리지
않으므로(`.scratch/harness/probes/webfetch_payload/` 의 B) 모델의 답으로 판정한다. 측정이 아니거나
기대와 다르면 1로 끝난다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/token-usage/probes/large_result/notice.py <저장소 밖 디렉터리>`. `claude`
CLI 와 인증이 들고 변형마다 haiku 세션 하나다. `--judge` 를 붙이면 claude 를 띄우지 않고 남은 기록만
다시 판정한다.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

from run import read_jsonl, write_fixture  # noqa: E402
from tools.hook_large_result import LEAD  # noqa: E402

NO_NOTICE = "알림 없음"
VARIANTS = {"B_notice": "lines.txt", "C_control": "korean.txt"}


def hook_entry(command: str) -> dict[str, object]:
    return {"type": "command", "command": command, "timeout": 30}


def run(out: Path, name: str, target: Path) -> None:
    root = ROOT.as_posix()
    log = (out / f"{name}_posttool.jsonl").as_posix()
    hooks = [
        hook_entry(
            f'uv run --project "{root}" --no-sync python "{root}/tools/launch_hook.py"'
            " hook_large_result.py"
        ),
        hook_entry(
            f'uv run --project "{root}" --no-sync python'
            f' "{(HERE / "dump_posttool.py").as_posix()}" "{log}"'
        ),
    ]
    settings = out / f"{name}.settings.json"
    settings.write_text(
        json.dumps(
            {"hooks": {"PostToolUse": [{"matcher": "Read|Bash|PowerShell", "hooks": hooks}]}}
        ),
        encoding="utf-8",
    )
    (out / f"{name}_posttool.jsonl").unlink(missing_ok=True)
    prompt = (
        f"Read 도구를 한 번만 부른다. file_path 는 '{target.as_posix()}' 이고"
        " offset·limit 은 주지 않는다. 결과 내용은 설명하지 않는다. 그 뒤 그 Read 호출에"
        " 붙어 온 훅 알림이나 시스템 리마인더가 있으면 그 첫 문장을 그대로 옮기고,"
        " 없으면 '알림 없음' 이라고 한국어 한 줄로 답한다."
    )
    with (out / f"{name}.jsonl").open("wb") as stream, (out / f"{name}.err").open("wb") as err:
        # 프롬프트는 stdin 으로 준다. `--tools` 뒤에 두면 가변 인자가 삼킨다(canary_init).
        subprocess.run(
            [
                "claude",
                "-p",
                "--setting-sources",
                "project,local",
                "--strict-mcp-config",
                "--model",
                "haiku",
                "--output-format",
                "stream-json",
                "--verbose",
                "--max-turns",
                "4",
                "--tools",
                "Read",
                "--allowed-tools",
                "Read",
                "--no-session-persistence",
                "--settings",
                str(settings),
            ],
            input=prompt.encode("utf-8"),
            stdout=stream,
            stderr=err,
            cwd=out,
            check=False,
            timeout=600,
        )


def final_answer(stream: list[dict[str, object]]) -> str:
    answers = [str(event.get("result", "")) for event in stream if event.get("type") == "result"]
    return answers[-1] if answers else ""


def check(out: Path, name: str, target: Path) -> list[str]:
    entries = read_jsonl(out / f"{name}_posttool.jsonl")
    answer = final_answer(read_jsonl(out / f"{name}.jsonl"))
    print(f"{name}: 탐침 기록 {len(entries)}건\n  답 {answer!r}")
    if len(entries) != 1:
        return [f"{name}: 측정 아님 — PostToolUse 기록이 {len(entries)}건이다"]
    tool_input = entries[0].get("tool_input")
    fields = tool_input if isinstance(tool_input, dict) else {}
    path = fields.get("file_path")
    if (
        entries[0].get("tool_name") != "Read"
        or not isinstance(path, str)
        or Path(path) != target
        or "offset" in fields
        or "limit" in fields
    ):
        return [f"{name}: 측정 아님 — 지시한 Read 가 아니었다({fields})"]
    if name == "B_notice" and LEAD not in answer:
        return [f"{name}: 답이 훅의 첫 문장을 옮기지 않았다"]
    if name == "C_control" and (LEAD in answer or NO_NOTICE not in answer):
        return [f"{name}: 대조군에 훅이 알렸거나 답이 '{NO_NOTICE}' 가 아니다"]
    return []


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    judge_only = "--judge" in args
    args = [arg for arg in args if arg != "--judge"]
    out = Path(args[0]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    fixture = write_fixture(out)
    problems: list[str] = []
    for name, file in VARIANTS.items():
        if not judge_only:
            run(out, name, fixture / file)
        problems += check(out, name, fixture / file)
    for problem in problems:
        print(f"[문제] {problem}")
    print(f"변형 {len(VARIANTS)}개, 문제 {len(problems)}건.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
