"""세션을 시작할 때 실린 `CLAUDE.md` 를 Read 없이 Edit 로 고칠 수 있는지 잰다.

왜. `.claude/rules/agent-docs.md` 는 `paths` 에 `CLAUDE.md` 를 든다. 경로 규칙은 Read 로 그 경로를
열 때 실리고(`CLAUDE.md` 지도 표의 rules 행), Edit 는 그 대화에서 먼저 Read 를 요구한다(Edit 도구
설명). 세션을 시작할 때 지침으로 실린 `CLAUDE.md` 를 읽은 것으로 쳐서 Read 없이 Edit 가 되면, 그
규칙은 `CLAUDE.md` 를 고치는 세션에 실리지 않을 수 있다(ADR 0033 이력 2026-10-20 "하네스가 스킬을
부르는 자리를 감사하고, 설명에만 기대던 계기를 하네스로 옮긴다").

갈래 둘. 회차마다 새 임시 폴더에 `CLAUDE.md` 와 `notes.md` 를 두고, `claude -p` 를 `--tools Edit`
로만 띄워 Read 없이 한 파일의 낱말 하나를 바꾸게 한다.
- `claude-md`: 대상이 `CLAUDE.md` 다. 세션을 시작할 때 지침으로 실린다.
- `notes`(양성 대조): 대상이 실리지 않는 `notes.md` 다. 여기서 Edit 가 거부되어야 "먼저 Read 를
  요구한다"가 이 판에서 선다.

표지. 그 회차가 측정인 것은 셋이 모두 맞을 때다. 대상 파일을 겨눈 Edit 호출과 그 결과가 스트림에
있고, 모델의 글에 `CLAUDE.md` 의 표지 문장이 있고(지침이 실렸다는 표지), 결과가 아래 두 갈래 가운데
하나다. 표지 없는 회차는 따로 세고, 하나라도 있으면 종료 코드 1 이다.
- `read-first`: 대상 Edit 결과가 모두 오류이고 그 문구에 `READ_FIRST` 가 있으며, 파일이 그대로다.
- `edited`: 오류가 아닌 대상 Edit 결과가 있고, 파일이 바뀌었다.
다른 까닭의 거부(낱말을 찾지 못함, 권한 거부)는 재려는 상황이 아니라 `other` 로 두고 측정으로 세지
않는다. 첫 판은 Edit 결과가 있기만 하면 측정으로 셌다. PR 직전 버그 축이 짚어 거부 문구를 표지로
더했다(일지 2026-10-20-35).

돌리는 법: 저장소 루트에서
    uv run python .scratch/harness/probes/claude_md_edit_without_read.py <출력 디렉터리> [갈래 이름]
갈래 이름을 주면 그 갈래만 돈다. 출력 디렉터리에는 회차마다 stream-json 원본과, 끝에 결과 한 줄씩의
`results.jsonl` 이 남는다. 출력 디렉터리는 만들기만 하고 지우지 않는다.

못 보는 것: 데스크톱 앱 세션(이 탐침은 `claude -p` 다), 대상이 하위 폴더의 `CLAUDE.md` 이거나 상위
폴더에서 실린 것, `--setting-sources project,local` 밖의 설정이 바꾸는 것.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RUNS = 2
TIMEOUT = 300
MARKER = "파란 고래 일곱"
OLD = "카나리아-원본"
NEW = "카나리아-바뀜"
ARMS = {"claude-md": "CLAUDE.md", "notes": "notes.md"}
# Edit 가 먼저 Read 를 요구하며 거부할 때의 문구. 2026-10-20 첫 실행의 원본에서 본 결과 문구
# "File has not been read yet. Read it first before writing to it." 의 앞 조각이다.
READ_FIRST = "has not been read yet"
PROMPT = (
    "답은 반드시 `표지: ` 로 시작하는 줄로 시작한다. 그 뒤에는 이 세션에 실린"
    " 프로젝트 지시에서 '표지 문장:' 뒤의 낱말을 글자 그대로 옮기고, 없으면"
    " '없음'이라고 쓴다. 그다음 이 폴더의 `{target}` 파일에서 낱말 `{old}` 을 `{new}` 으로"
    " 바꿔라. Edit 도구만 쓴다. Edit 가 거부되면 다시 시도하지 말고"
    " 거부 문구를 그대로 옮긴 뒤 끝낸다."
)


def command(claude: str) -> list[str]:
    return [
        claude,
        "-p",
        "--setting-sources",
        "project,local",
        "--strict-mcp-config",
        "--model",
        "sonnet",
        "--permission-mode",
        "acceptEdits",
        "--output-format",
        "stream-json",
        "--verbose",
        "--tools",
        "Edit",
    ]


def events(raw: Path) -> list[dict[str, object]]:
    """원본의 줄을 JSON 으로 푼다. 풀리지 않는 줄(잘린 마지막 줄)은 넘긴다."""
    parsed: list[dict[str, object]] = []
    for line in raw.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            parsed.append({str(key): item for key, item in value.items()})
    return parsed


def blocks(event: dict[str, object]) -> list[dict[str, object]]:
    message = event.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [
        {str(key): item for key, item in block.items()}
        for block in content
        if isinstance(block, dict)
    ]


def judge(raw: Path, target: str, *, changed: bool) -> dict[str, object]:
    """Edit 호출과 그 결과, 답의 표지를 모으고 회차를 가른다."""
    edit_ids: set[str] = set()
    results: list[dict[str, object]] = []
    # 표지 줄은 Edit 를 부르기 전의 글 블록에 오기도 해서(첫 실행의 원본에서 봤다) `result` 만 보지
    # 않고 모델의 글 블록을 모두 모은다.
    texts: list[str] = []
    answer = ""
    for event in events(raw):
        kind = event.get("type")
        for block in blocks(event):
            if kind == "assistant" and block.get("type") == "text":
                text = block.get("text")
                texts.append(text if isinstance(text, str) else "")
            if kind == "assistant" and block.get("type") == "tool_use":
                arguments = block.get("input")
                path = arguments.get("file_path") if isinstance(arguments, dict) else None
                if (
                    block.get("name") == "Edit"
                    and isinstance(path, str)
                    and Path(path).name == target
                ):
                    edit_ids.add(str(block.get("id")))
            if kind == "user" and block.get("type") == "tool_result":
                if str(block.get("tool_use_id")) in edit_ids:
                    content = block.get("content")
                    text = content if isinstance(content, str) else json.dumps(content)
                    results.append({"is_error": block.get("is_error") is True, "text": text[:300]})
        if kind == "result":
            final = event.get("result")
            answer = final if isinstance(final, str) else ""
    return {
        "edit_calls": len(edit_ids),
        "edit_results": results,
        "outcome": outcome(results, changed=changed),
        "loaded": any(MARKER in text for text in [*texts, answer]),
        "answer_head": answer[:300],
    }


def outcome(results: list[dict[str, object]], *, changed: bool) -> str:
    """대상 Edit 결과와 파일이 바뀌었는지로 회차를 가른다. 까닭이 다른 거부는 `other` 다."""
    if not results:
        return "other"
    rejected = [
        result
        for result in results
        if result.get("is_error") is True and READ_FIRST in str(result.get("text"))
    ]
    if len(rejected) == len(results) and not changed:
        return "read-first"
    if changed and any(result.get("is_error") is not True for result in results):
        return "edited"
    return "other"


def run_once(claude: str, arm: str, number: int, out: Path) -> dict[str, object]:
    target = ARMS[arm]
    raw = out / f"{arm}-{number}.jsonl"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
        work = Path(folder)
        (work / "CLAUDE.md").write_text(
            f"# 탐침 지시\n\n표지 문장: {MARKER}\n\n{OLD}\n", encoding="utf-8"
        )
        (work / "notes.md").write_text(f"# 메모\n\n{OLD}\n", encoding="utf-8")
        prompt = PROMPT.format(target=target, old=OLD, new=NEW)
        with raw.open("w", encoding="utf-8") as sink:
            try:
                completed = subprocess.run(
                    command(claude),
                    input=prompt,
                    text=True,
                    encoding="utf-8",
                    cwd=work,
                    stdout=sink,
                    stderr=subprocess.DEVNULL,
                    timeout=TIMEOUT,
                    check=False,
                )
                code = completed.returncode
            except subprocess.TimeoutExpired:
                code = 124
        changed = NEW in (work / target).read_text(encoding="utf-8")
    row: dict[str, object] = {"arm": arm, "run": number, "exit": code, "changed": changed}
    row.update(judge(raw, target, changed=changed))
    row["measured"] = row["loaded"] is True and row["outcome"] != "other"
    return row


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2
    claude = shutil.which("claude")
    if claude is None:
        print("claude 를 찾지 못했다")
        return 2
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    arms = [sys.argv[2]] if len(sys.argv) == 3 else list(ARMS)
    rows = [run_once(claude, arm, number, out) for arm in arms for number in range(1, RUNS + 1)]
    with (out / "results.jsonl").open("w", encoding="utf-8") as sink:
        for row in rows:
            line = json.dumps(row, ensure_ascii=False)
            sink.write(line + "\n")
            print(line)
    unmeasured = [row for row in rows if not row["measured"]]
    print(f"측정 {len(rows) - len(unmeasured)} / 표지 없음 {len(unmeasured)}")
    return 1 if unmeasured else 0


if __name__ == "__main__":
    raise SystemExit(main())
