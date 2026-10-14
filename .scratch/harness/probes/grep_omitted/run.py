"""Grep 도구가 긴 일치 줄을 `[Omitted long matching line]` 으로만 내는 것을 PostToolUse 훅이 보는지,
`tools/hook_grep_omitted.py` 의 알림이 모델에게 닿는지 잰다(대기열 145).

픽스처는 저장소 밖 출력 디렉터리 아래 `fixture/` 다. `lines.txt` 는 같은 패턴(`PROBE`)이 맞는 짧은
줄, 500자 줄, 501자 줄을 들고, `korean.txt` 는 한글로 채운 500자 줄(1488바이트)과 501자 줄을,
`wide.txt` 는 2000자 줄 하나를 든다. 500자와 501자는 이 세션이 Grep 도구로 손으로 찾은 문턱의
양쪽이다(500자까지 그대로, 501자부터 표지). 한글 줄은 문턱이 바이트가 아니라 글자 수인지 가른다.
- A_payload: 탐침 훅(`dump_posttool.py`)만 붙이고 `fixture/` 를 content 모드로 한 번 훑는다. 훅이
  받은 `tool_response` 의 키와 타입, 표지가 어느 키에 몇 번 실렸는지, 그 줄에 파일 경로와 줄 번호가
  붙는지 본다. 기록이 하나이고 그 호출이 지시한 패턴·경로의 content 모드일 때 측정이다(B·C 도
  같다). 500자 줄 둘(영문, 한글)이 그대로 실리고 표지가 셋(501자 줄 둘과 2000자 줄)이면 기대대로다.
- B_notice: 등록 모양(래퍼를 거쳐)의 실제 훅과 탐침 훅을 붙이고 같은 호출을 한 뒤, 그 호출에 붙어
  온 훅 알림의 첫 문장을 묻는다. 탐침 기록이 지시한 호출이고 표지가 있을 때 측정이고, 답이 훅의
  첫 문장(`LEAD`)을 옮기면 닿은 것이다.
- C_control: B 의 대조군. 짧은 줄만 맞는 패턴(`PROBE short`)이다. 탐침 기록이 지시한 호출이고
  일치가 있고 표지가 없을 때 측정이고, 답이 그 문장 없이 '알림 없음' 이면 기대대로다.
stream-json 에는 훅의 additionalContext 가 실리지 않으므로(`webfetch_payload/` 의 B) 모델의 답으로
판정한다.

측정이 아닌 변형, 기대와 다른 변형, 모르는 변형 이름이 하나라도 있으면 1로 끝난다.
돌리는 법: 저장소 루트에서 `uv run python .scratch/harness/probes/grep_omitted/run.py <저장소 밖
디렉터리> [변형 ...]`. 변형을 주지 않으면 셋 다 돈다. `claude` CLI 와 인증이 들고 변형마다 haiku
세션 하나다. 저장소 밖에서 `--setting-sources project,local` 로 돌려 이 저장소와 사용자 전역의 훅을
뺀다. `--judge` 를 붙이면 claude 를 띄우지 않고 남은 기록만 다시 판정한다.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
# 훅의 상수를 가져오지 않고 따로 적는다. Claude Code 가 내는 표지를 재는 자리라, 훅의 상수가 틀리면
# 여기서 어긋나야 한다(같은 까닭이 tools/run_hooks.py 의 NOTICE_ONLY_EVENTS 주석에 있다).
MARKER = "[Omitted long matching line]"
NO_NOTICE = "알림 없음"
VARIANTS = ("A_payload", "B_notice", "C_control")
SHORT = "PROBE short"
AT_LIMIT = "PROBE " + "x" * (500 - len("PROBE "))
OVER_LIMIT = "PROBE " + "y" * (501 - len("PROBE "))
WIDE = "PROBE " + "z" * (2000 - len("PROBE "))
KOREAN_AT_LIMIT = "PROBE " + "가" * (500 - len("PROBE "))
KOREAN_OVER_LIMIT = "PROBE " + "나" * (501 - len("PROBE "))
BASE = [
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
    "Grep",
    "--allowed-tools",
    "Grep",
    "--no-session-persistence",
]
ASK_NOTICE = (
    "그 뒤 그 Grep 호출에 붙어 온 훅 알림이나 시스템 리마인더가 있으면 그 첫 문장을 그대로 옮기고,"
    " 없으면 '알림 없음' 이라고 한국어 한 줄로 답한다."
)


def write_fixture(out: Path) -> Path:
    fixture = out / "fixture"
    fixture.mkdir(parents=True, exist_ok=True)
    lines = (SHORT, AT_LIMIT, OVER_LIMIT)
    (fixture / "lines.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    korean = "\n".join((KOREAN_AT_LIMIT, KOREAN_OVER_LIMIT)) + "\n"
    (fixture / "korean.txt").write_text(korean, encoding="utf-8", newline="\n")
    (fixture / "wide.txt").write_text(WIDE + "\n", encoding="utf-8", newline="\n")
    return fixture


def hook_entry(command: str) -> dict[str, object]:
    return {"type": "command", "command": command, "timeout": 30}


def dump_hook(out: Path, name: str) -> dict[str, object]:
    log = (out / f"{name}_posttool.jsonl").as_posix()
    return hook_entry(
        f'uv run --project "{ROOT.as_posix()}" --no-sync python'
        f' "{(HERE / "dump_posttool.py").as_posix()}" "{log}"'
    )


def real_hook() -> dict[str, object]:
    root = ROOT.as_posix()
    return hook_entry(
        f'uv run --project "{root}" --no-sync python "{root}/tools/launch_hook.py"'
        " hook_grep_omitted.py"
    )


def run(out: Path, name: str, hooks: list[dict[str, object]], prompt: str) -> None:
    settings = out / f"{name}.settings.json"
    settings.write_text(
        json.dumps({"hooks": {"PostToolUse": [{"matcher": "Grep", "hooks": hooks}]}}),
        encoding="utf-8",
    )
    (out / f"{name}_posttool.jsonl").unlink(missing_ok=True)
    with (out / f"{name}.jsonl").open("wb") as stream, (out / f"{name}.err").open("wb") as err:
        # 프롬프트는 stdin 으로 준다. `--tools` 뒤에 두면 가변 인자가 삼킨다(canary_init).
        subprocess.run(
            ["claude", "-p", *BASE, "--settings", str(settings)],
            input=prompt.encode("utf-8"),
            stdout=stream,
            stderr=err,
            cwd=out,
            check=False,
            timeout=600,
        )


def grep_prompt(fixture: Path, pattern: str) -> str:
    return (
        f"Grep 도구를 한 번만 부른다. pattern 은 '{pattern}', path 는 '{fixture.as_posix()}',"
        " output_mode 는 'content', -n 은 true 다."
    )


def read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    records: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            records.append({str(key): value for key, value in record.items()})
    return records


def final_answer(stream: list[dict[str, object]]) -> str:
    answers = [str(event.get("result", "")) for event in stream if event.get("type") == "result"]
    return answers[-1] if answers else ""


def response_text(entry: dict[str, object]) -> str:
    """`tool_response` 의 문자열 값을 모두 이은 것."""
    response = entry.get("tool_response")
    if not isinstance(response, dict):
        return ""
    return "\n".join(value for value in response.values() if isinstance(value, str))


def marker_total(entry: dict[str, object]) -> int:
    return response_text(entry).count(MARKER)


def call_problem(name: str, entry: dict[str, object], fixture: Path, pattern: str) -> str | None:
    """기록이 지시한 Grep 호출(PostToolUse, content 모드, 그 패턴, `fixture/` 경로)이 아니면 까닭.

    지시와 다른 호출의 결과로도 표지와 답의 조건이 맞을 수 있어, 세 변형 모두 먼저 본다."""
    tool_input = entry.get("tool_input")
    fields = tool_input if isinstance(tool_input, dict) else {}
    mode, got, path = fields.get("output_mode"), fields.get("pattern"), fields.get("path")
    if entry.get("hook_event_name") != "PostToolUse" or entry.get("tool_name") != "Grep":
        return f"{name}: 측정 아님 — 이벤트·도구가 다르다"
    if mode != "content":
        return f"{name}: 측정 아님 — content 모드가 아니었다({mode})"
    if got != pattern or not isinstance(path, str) or Path(path) != fixture:
        return f"{name}: 측정 아님 — 지시한 호출이 아니었다(pattern {got!r}, path {path!r})"
    return None


def check_payload(out: Path, fixture: Path) -> list[str]:
    entries = read_jsonl(out / "A_payload_posttool.jsonl")
    for entry in entries:
        print(
            f"A {entry.get('hook_event_name')} {entry.get('tool_name')}\n"
            f"  입력 키 {entry.get('payload_keys')}\n"
            f"  tool_input {json.dumps(entry.get('tool_input'), ensure_ascii=False)}\n"
            f"  tool_response 타입 {entry.get('response_type')}"
            f" 키와 타입 {entry.get('response_types')}\n"
            f"  표지 수 {entry.get('marker_counts')}"
        )
        for line in response_text(entry).splitlines():
            if MARKER in line or len(line) < 200:
                print(f"  | {line}")
            else:
                print(f"  | ({len(line)}자 줄)")
    if len(entries) != 1:
        return [f"A: 측정 아님 — Grep 의 PostToolUse 기록이 {len(entries)}건이다"]
    entry = entries[0]
    wrong_call = call_problem("A", entry, fixture, "PROBE")
    if wrong_call:
        return [wrong_call]
    text = response_text(entry)
    at_limit = (("영문", AT_LIMIT), ("한글", KOREAN_AT_LIMIT))
    missing = [name for name, line in at_limit if line not in text]
    if missing:
        return [f"A: 500자 줄({', '.join(missing)})이 그대로 실리지 않았다(문턱이 다르다)"]
    if marker_total(entry) != 3:
        return [f"A: 표지가 {marker_total(entry)}번이다(기대 3 — 501자 줄 둘과 2000자 줄)"]
    return []


def check_notice(out: Path, name: str, lead: str, fixture: Path) -> list[str]:
    notice = name == "B_notice"
    entries = read_jsonl(out / f"{name}_posttool.jsonl")
    answer = final_answer(read_jsonl(out / f"{name}.jsonl"))
    print(
        f"{name} 탐침 기록 {len(entries)}건, 표지 {[marker_total(e) for e in entries]}\n"
        f"  답 {answer!r}"
    )
    if len(entries) != 1:
        return [f"{name}: 측정 아님 — Grep 의 PostToolUse 기록이 {len(entries)}건이다"]
    wrong_call = call_problem(name, entries[0], fixture, "PROBE" if notice else SHORT)
    if wrong_call:
        return [wrong_call]
    markers = marker_total(entries[0])
    if notice and markers == 0:
        return [f"{name}: 측정 아님 — 그 호출의 결과에 표지가 없었다"]
    if not notice and (markers or SHORT not in response_text(entries[0])):
        return [f"{name}: 측정 아님 — 그 호출이 표지 없는 일치가 아니었다"]
    if notice and lead not in answer:
        return [f"{name}: 답이 훅의 첫 문장을 옮기지 않았다"]
    if not notice and (lead in answer or NO_NOTICE not in answer):
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
    variants = args[1:] or list(VARIANTS)
    problems = [f"모르는 변형 {name} — 재지 않았다" for name in variants if name not in VARIANTS]
    fixture = write_fixture(out)
    if not judge_only:
        for name in variants:
            if name == "A_payload":
                run(
                    out,
                    name,
                    [dump_hook(out, name)],
                    grep_prompt(fixture, "PROBE") + " 그 뒤 '끝' 이라고만 답한다.",
                )
            elif name == "B_notice":
                run(
                    out,
                    name,
                    [real_hook(), dump_hook(out, name)],
                    f"{grep_prompt(fixture, 'PROBE')} {ASK_NOTICE}",
                )
            elif name == "C_control":
                run(
                    out,
                    name,
                    [real_hook(), dump_hook(out, name)],
                    f"{grep_prompt(fixture, SHORT)} {ASK_NOTICE}",
                )
    if "A_payload" in variants:
        problems += check_payload(out, fixture)
    notice_variants = [name for name in variants if name in ("B_notice", "C_control")]
    if notice_variants:
        sys.path.insert(0, str(ROOT))
        from tools.hook_grep_omitted import LEAD

        for name in notice_variants:
            problems += check_notice(out, name, LEAD, fixture)
    for problem in problems:
        print(f"[문제] {problem}")
    print(f"변형 {len(variants)}개, 문제 {len(problems)}건.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
