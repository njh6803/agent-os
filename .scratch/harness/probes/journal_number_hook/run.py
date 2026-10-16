"""PostToolUse 훅이 일지 Write 에서 받는 입력과, `hook_journal_retro` 의 번호 알림이 모델에게 닿는지
잰다 (대기열 232).

- A_payload: 탐침 훅(`dump_posttool.py`)만 붙이고 같은 일지 파일을 Write 로 새로 만들고, Write 로
  다시 쓰고, Edit 로 고친다. 훅이 받은 `tool_response` 의 키와 `type`, `originalFile` 이 null 인지
  본다. 새 파일을 만든 Write 와 있는 파일을 덮어쓴 Write 를 결과의 어느 값이 가르는지가 재려는
  것이다.
- B_clash: 등록 모양(래퍼를 거친 실제 훅)과 탐침 훅을 함께 붙인 임시 저장소에서, main 의 일지와 같은
  순번의 새 일지를 Write 로 만든 뒤 그 호출에 붙어 온 훅 알림의 첫 문장을 묻는다. 훅의 첫
  문장(`tools/hook_journal_retro.py` 의 `NUMBER_LEAD`)을 옮기면 additionalContext 가 닿은 것이다.
- C_next: B 의 대조군. 다음 빈 순번으로 새 일지를 만들고 같은 것을 묻는다. 훅이 침묵하면 '알림 없음'
  이다.

임시 저장소는 변형마다 새로 짓는다. origin 은 같은 디렉터리의 bare 저장소이고, main 에는 오늘 날짜의
01 일지와 ADR, 대기열 행, 헌법 판이 있다(`tools/sibling_overlap.py` 는 merge-base 에서 네 자리가
비면 2로 끝난다). 작업 브랜치는 main 에서 딴 `chore/probe` 다. 오늘은 이 기계의 지역 날짜로, 그
도구와 같다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/harness/probes/journal_number_hook/run.py <저장소 밖 디렉터리> [변형 ...]`.
변형을 주지 않으면 셋 다 돈다. `claude` CLI 와 인증이 든다. 변형마다 haiku 세션 하나다. 저장소
밖에서 `--setting-sources project,local` 로 돌려 이 저장소와 사용자 전역의 훅을 뺀다. 탐침 기록이
없거나 재려는 Write 가 돌지 않은 변형은 측정이 아니라고 세고, 측정이 아니거나 기대와 다른 변형이
하나라도 있으면 1로 끝난다.
"""

from __future__ import annotations

import ast
import io
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.run_hooks import journal_repository  # noqa: E402

NO_NOTICE = "알림 없음"
VARIANTS = ("A_payload", "B_clash", "C_next")
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
    "6",
]
ASK_NOTICE = (
    "그 뒤 그 Write 호출에 붙어 온 훅 알림이나 시스템 리마인더가 있으면 그 첫 문장을 그대로 옮기고,"
    f" 없으면 '{NO_NOTICE}' 라고 한국어 한 줄로 답한다."
)


def today() -> str:
    return datetime.now().astimezone().date().isoformat()


def hook_command(script: Path, *args: str) -> dict[str, object]:
    quoted = " ".join(f'"{arg}"' for arg in args)
    command = (
        f'uv run --project "{ROOT.as_posix()}" --no-sync python "{script.as_posix()}" {quoted}'
    )
    return {"type": "command", "command": command.rstrip(), "timeout": 30}


def real_hook() -> dict[str, object]:
    """등록 모양의 실제 훅. 시간 제한도 `.claude/settings.json` 의 그 훅과 같다."""
    entry = hook_command(ROOT / "tools" / "launch_hook.py", "hook_journal_retro.py")
    entry["timeout"] = 45
    return entry


def write_settings(path: Path, hooks: list[dict[str, object]]) -> None:
    settings = {"hooks": {"PostToolUse": [{"matcher": "Write|Edit", "hooks": hooks}]}}
    path.write_text(json.dumps(settings, ensure_ascii=False), encoding="utf-8")


def fixture_repo(where: Path) -> Path:
    """main 에 오늘 날짜의 01 일지가 있고 작업 브랜치가 그 위인 저장소(`tools/run_hooks.py` 의
    `journal_repository`). 그 함수가 임시 저장소를 짓는 동안 저장소를 가리키는 `GIT_*` 를 벗긴다."""
    for path in (where / "origin.git", where / "repo"):
        if path.exists():
            shutil.rmtree(path)
    for name in [name for name in os.environ if name.startswith("GIT_")]:
        del os.environ[name]
    return journal_repository(where, today())


def run_claude(cwd: Path, settings: Path, tools: str, prompt: str, stream: Path) -> None:
    command = ["claude", "-p", *BASE, "--tools", tools, "--allowed-tools", tools]
    command += ["--settings", str(settings)]
    with stream.open("wb") as out, (stream.with_suffix(".err")).open("wb") as err:
        subprocess.run(
            command,
            cwd=cwd,
            input=prompt.encode("utf-8"),
            stdout=out,
            stderr=err,
            check=False,
            timeout=600,
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


def lead() -> str:
    """훅의 번호 알림 첫 문장(`NUMBER_LEAD`). 훅 파일의 대입문을 읽는다."""
    tree = ast.parse((ROOT / "tools" / "hook_journal_retro.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "NUMBER_LEAD" for t in node.targets)
            and isinstance(value := ast.literal_eval(node.value), str)
        ):
            return value
    raise SystemExit("tools/hook_journal_retro.py 에 NUMBER_LEAD 가 없다")


def variant_a(out: Path) -> tuple[bool, bool, str]:
    work = out / "A_payload"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    log = out / "A_payload_posttool.jsonl"
    log.unlink(missing_ok=True)
    settings = out / "A_payload.settings.json"
    write_settings(settings, [hook_command(HERE / "dump_posttool.py", log.as_posix())])
    name = f"docs/journal/{today()}-01-probe.md"
    prompt = (
        f"아래를 차례로 한다. 1) Write 도구로 {name} 를 '# {today()} (01) probe' 한 줄로"
        f" 새로 만든다. 2) Write 도구로 같은 파일을 '# {today()} (01) probe' 와 빈 줄, '더함'"
        " 세 줄로 다시 쓴다. 3) Edit 도구로 그 파일의 '더함' 을 '고침' 으로 바꾼다."
        " 그 뒤 '끝' 이라고만 답한다."
    )
    run_claude(work, settings, "Write,Edit", prompt, out / "A_payload.jsonl")
    entries = read_jsonl(log)
    for entry in entries:
        print(f"A_payload: {json.dumps(entry, ensure_ascii=False)}")
    kinds = [
        (entry.get("tool_name"), (entry.get("tool_response") or {}).get("type"))
        for entry in entries
    ]
    # Edit 가 돌았다는 것도 측정의 표지다. "Edit 의 결과에는 type 이 없다" 의 근거다
    ran = ("Write", "create") in kinds and ("Write", "update") in kinds and ("Edit", None) in kinds
    return ran, ran, f"Write·Edit 결과의 type: {kinds}"


def variant_bc(out: Path, name: str, seq: str, *, expect_notice: bool) -> tuple[bool, bool, str]:
    where = out / name
    where.mkdir(parents=True, exist_ok=True)
    repo = fixture_repo(where)
    log = out / f"{name}_posttool.jsonl"
    log.unlink(missing_ok=True)
    settings = out / f"{name}.settings.json"
    write_settings(settings, [real_hook(), hook_command(HERE / "dump_posttool.py", log.as_posix())])
    journal = f"docs/journal/{today()}-{seq}-probe.md"
    prompt = (
        f"Write 도구로 {journal} 를 '# {today()} ({seq}) probe' 한 줄로 새로 만든다."
        f" 한 번만 부른다. {ASK_NOTICE}"
    )
    run_claude(repo, settings, "Write", prompt, out / f"{name}.jsonl")
    entries = read_jsonl(log)
    created = any(
        entry.get("tool_name") == "Write"
        and (entry.get("tool_response") or {}).get("type") == "create"
        and str(entry.get("file_path", "")).replace("\\", "/").endswith(journal)
        for entry in entries
    )
    answer = final_answer(read_jsonl(out / f"{name}.jsonl"))
    print(f"{name}: 새 일지 Write 가 돌았다={created}, 답={answer!r}")
    if expect_notice:
        ok = lead() in answer
    else:
        ok = NO_NOTICE in answer and lead() not in answer
    return created, ok, answer


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    out = Path(sys.argv[1]).resolve()
    variants = sys.argv[2:] or list(VARIANTS)
    out.mkdir(parents=True, exist_ok=True)
    bad = 0
    for variant in variants:
        if variant == "A_payload":
            measured, ok, detail = variant_a(out)
        elif variant == "B_clash":
            measured, ok, detail = variant_bc(out, variant, "01", expect_notice=True)
        elif variant == "C_next":
            measured, ok, detail = variant_bc(out, variant, "02", expect_notice=False)
        else:
            print(f"모르는 변형: {variant}")
            bad += 1
            continue
        verdict = "기대대로" if ok else "기대와 다르다"
        print(f"{variant}: {'측정' if measured else '측정이 아니다'}, {verdict}. {detail}")
        bad += 0 if measured and ok else 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
