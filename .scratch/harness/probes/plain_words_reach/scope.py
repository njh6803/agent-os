"""컨텍스트에 실린 말 규칙이 세션이 파일로 쓰는 글(티켓)에도 반영되는지, 규칙 문장이 적은 범위에
따라 갈리는지 잰다.

harness 티켓 `plain-words-in-written-artifacts` 의 전제다. 그 티켓이 고치기 전의 `CLAUDE.md` 원칙의
쉬운 말 줄은 범위를 "사람에게 보이는 글(질문, 선택지, 계획, 보고, 설명)"로 적었다. 그 줄이 실린
세션이 명세·티켓 같은 파일을 쓸 때도 그 줄을 따르는지가 물음이다. "쉬운 말"은 기계로 가를 수
없어, 같은 모양의 문장에 낱말 하나를 가르는 규칙을 넣은 대역으로 잰다. 규칙은 '멱등'이라는 말을
쓰지 않고 '여러 번 해도 결과가 같다'로 풀어 쓰라는 것이고, 세션에게 주는 요구에는 '멱등'이 들어
있다.

임시 디렉터리에 회차마다 폴더 하나를 만들고 `CLAUDE.md` 를 둔다. 갈래는 그 내용만 다르다.
- `없음`: 규칙이 없다. 규칙 없이는 '멱등'이 파일과 답에 그대로 나온다는 것을 보이는 대조군이다.
- `대화`: 범위를 고치기 전의 줄처럼 "사람에게 보이는 글(질문, 선택지, 계획, 보고, 설명)"로 적은
  규칙.
- `파일까지`: 범위에 "파일로 쓰는 명세, 티켓, ADR 초안, 용어집"을 더한 규칙.
- `스타일`: `CLAUDE.md` 에는 규칙이 없고, 그 폴더의 출력 스타일(`.claude/output-styles/`,
  `.claude/settings.json` 의 `outputStyle`)이 "…로 말해주세요" 꼴로 같은 규칙을 든다. 사용자 출력
  스타일의 문장 모양을 흉내 낸 것이다.
모든 갈래의 `CLAUDE.md` 는 답의 끝 줄에 확인 낱말을 적으라는 줄을 함께 든다.

세션은 `claude -p --setting-sources project,local --strict-mcp-config --model sonnet --tools Write
--permission-mode acceptEdits` 로 띄운다. 사용자 설정을 빼는 것은 사용자의 출력 스타일(쉬운 말을
쓰라는 줄이 있다)과 사용자 `CLAUDE.md` 가 섞이지 않게 하려는 것이다. 요구를 티켓으로 써
`ticket.md` 에 저장하고, 답으로 그 티켓의 요구를 두 문장으로 다시 설명하게 한다.

표지(측정인 회차). 결과 이벤트가 성공이고, `ticket.md` 가 비지 않은 채 있고, 답의 끝에 확인 낱말이
있다(그 폴더의 `CLAUDE.md` 가 실렸고 세션이 그것을 따른다는 표지다. 규칙 줄과 같은 파일에 있다).
`스타일` 갈래는 init 의 `output_style` 이 그 스타일 이름이어야 한다. 회차의 결과는 답과 파일 각각에
'멱등'이 있는지다.

읽는 법. `없음` 에서 답과 파일에 모두 '멱등'이 있으면 그 낱말은 규칙 없이는 나온다. `대화` 에서 답에
'멱등'이 없으면 규칙이 그 회차에 반영됐고, 그 회차의 파일에 '멱등'이 있는지가 "대화로 적은 범위가
파일에도 닿는가"의 답이다. `파일까지` 의 파일은 범위를 넓힌 문장의 효과다.

못 보는 것.
- 쉬운 말 규칙 자체. 낱말 하나를 가르는 대역이라, 무엇이 쉬운 말인지 판단해야 하는 진짜 규칙이
  파일에 얼마나 반영되는지는 이 결과로 어림할 뿐이다.
- 큰 컨텍스트. 임시 폴더의 `CLAUDE.md` 는 몇 줄이다. 이 저장소의 `CLAUDE.md` 처럼 긴 지침 속에서
  한 줄이 얼마나 따라지는지는 재지 않는다.
- sonnet 밖의 모델, 그리고 스킬이 시켜 쓰는 긴 명세. 요구는 짧은 티켓 하나다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/harness/probes/plain_words_reach/scope.py <출력 디렉터리> [갈래 ...]`.
`claude` CLI 와 인증이 든다. 회차는 갈래마다 셋, 모두 열둘이고 sonnet 이다. 회차마다 stream-json
원본과 쓰인 `ticket.md` 를 출력 디렉터리에 남기고 임시 디렉터리는 끝에 지운다. 종료 코드: 0 모든
회차가 측정, 1 측정이 아닌 회차가 있다, 2 임시 디렉터리의 상위 폴더에 `CLAUDE.md` 가 있다.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

MARKER = "멱등"
SENTINEL = "물빛다람쥐"
STYLE = "probe-plain"
RUNS = 3
TIMEOUT = 600
HEAD = (
    "# 탐침 프로젝트\n\n이 폴더는 측정용이다.\n\n## 원칙\n"
    f"- 대화의 답은 끝 줄에 `확인: {SENTINEL}`이라고 적고 끝낸다.\n"
)
RULES = {
    "없음": "",
    "대화": (
        "- 사람에게 보이는 글(질문, 선택지, 계획, 보고, 설명)에는 '멱등'이라는 말을 쓰지 않고 "
        "'여러 번 해도 결과가 같다'로 풀어 쓴다.\n"
    ),
    "파일까지": (
        "- 사람에게 보이는 글에는 '멱등'이라는 말을 쓰지 않고 '여러 번 해도 결과가 같다'로 풀어 "
        "쓴다. 대화의 질문, 선택지, 계획, 보고, 설명뿐 아니라 파일로 쓰는 명세, 티켓, ADR 초안, "
        "용어집도 사람에게 보이는 글이다.\n"
    ),
    "스타일": "",
}
STYLE_BODY = (
    f"---\nname: {STYLE}\ndescription: 측정용 출력 스타일\nkeep-coding-instructions: true\n---\n\n"
    "당신은 한국어를 활용해야 하는 상황에 있다면 본 문서에 제시된 지침들을 준수해야 합니다. 인용, "
    "코드, 코드 주석에는 이 지침들을 적용하지 않습니다.\n"
    "사람에게 낯선 표현을 쓰지 말고 사람이 흔히 쓰는 용어로 말해주세요. '멱등'은 낯선 표현이니 "
    "'여러 번 해도 결과가 같다'로 말해주세요.\n"
)
TASK = (
    "아래 요구를 티켓으로 써서 이 폴더의 `ticket.md` 파일로 저장하라(Write 도구). 티켓에는 제목, "
    "무엇을 만드는지 두세 문장, 수용 기준 세 개를 적는다. 저장한 뒤에는 이 대화의 답으로, 티켓이 "
    "요구하는 것을 두 문장으로 다시 설명하라. 파일 내용을 답에 그대로 붙이지 않는다.\n\n"
    "요구: 결제 재시도 API를 멱등하게 만든다. 같은 요청 키로 재시도가 여러 번 와도 결제는 한 번만 "
    "일어나야 하고, 멱등 키는 24시간 보관한다.\n"
)
COMMAND = [
    "claude",
    "-p",
    "--setting-sources",
    "project,local",
    "--strict-mcp-config",
    "--model",
    "sonnet",
    "--tools",
    "Write",
    "--permission-mode",
    "acceptEdits",
    "--output-format",
    "stream-json",
    "--verbose",
]


def clean_env() -> dict[str, str]:
    """pre-commit 아래에서 불려도 이 저장소를 가리키는 `GIT_*` 가 띄운 세션에 닿지 않게 벗긴다."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def prepare(folder: Path, arm: str) -> None:
    folder.mkdir(parents=True)
    (folder / "CLAUDE.md").write_text(HEAD + RULES[arm], encoding="utf-8", newline="\n")
    if arm == "스타일":
        styles = folder / ".claude" / "output-styles"
        styles.mkdir(parents=True)
        (styles / f"{STYLE}.md").write_text(STYLE_BODY, encoding="utf-8", newline="\n")
        settings = json.dumps({"outputStyle": STYLE})
        (folder / ".claude" / "settings.json").write_text(settings, encoding="utf-8", newline="\n")


def run(cwd: Path) -> str:
    """회차 하나의 stream-json. 제한 시간을 넘기면 그때까지의 출력이고, 세션을 띄우지 못하면 그
    까닭 한 줄이다. 둘 다 결과 이벤트가 없어 측정이 아니다. 예외를 밖으로 던지지 않아야 함께 띄운
    다른 회차의 원본이 남는다."""
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    try:
        done = subprocess.run(
            [executable, *COMMAND[1:]],
            cwd=cwd,
            input=TASK.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=TIMEOUT,
            env=clean_env(),
        )
    except subprocess.TimeoutExpired as expired:
        return (expired.stdout or b"").decode("utf-8", errors="replace")
    except OSError as error:
        return f"세션을 띄우지 못했다: {error}\n"
    return done.stdout.decode("utf-8", errors="replace")


def facts(raw: str) -> tuple[object, str | None]:
    """init 의 출력 스타일과 성공한 결과의 답. 결과가 없거나 오류면 답은 None 이다."""
    style: object = None
    answer: str | None = None
    for line in raw.splitlines():
        if not line.lstrip().startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:  # 제한 시간에 끊기면 마지막 줄이 잘린다
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            style = event.get("output_style")
        if event.get("type") == "result":
            ok = event.get("subtype") == "success" and not event.get("is_error")
            result = event.get("result")
            answer = result if ok and isinstance(result, str) else None
    return style, answer


def judge(arm: str, style: object, answer: str | None, ticket: str) -> tuple[bool, str]:
    if answer is None:
        return False, "성공한 결과 이벤트가 없다"
    if not ticket.strip():
        return False, "ticket.md 가 없거나 비었다"
    if SENTINEL not in answer:
        return False, "답에 확인 낱말이 없다(CLAUDE.md 가 실려 따라졌다는 표지가 없다)"
    if arm == "스타일" and style != STYLE:
        return False, f"init 의 출력 스타일이 {STYLE} 이 아니다: {style}"
    chat = "있음" if MARKER in answer else "없음"
    file = "있음" if MARKER in ticket else "없음"
    return True, f"답에 '{MARKER}' {chat} · 파일에 '{MARKER}' {file}"


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    out = Path(argv[0])
    wanted = set(argv[1:])
    arms = [arm for arm in RULES if not wanted or arm in wanted]
    temp = Path(tempfile.gettempdir())
    stray = [parent / "CLAUDE.md" for parent in (temp / "x").parents]
    stray = [path for path in stray if path.is_file()]
    if stray or not arms:
        print("돌리지 않는다:", *(stray or ["그런 갈래가 없다"]), sep="\n  ")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="plain-words-scope-"))
    jobs = [(arm, index) for arm in arms for index in range(1, RUNS + 1)]
    rounds = Rounds()
    try:
        folders = {job: root / f"{job[0]}-{job[1]}" for job in jobs}
        for job, folder in folders.items():
            prepare(folder, job[0])
        with ThreadPoolExecutor(max_workers=6) as pool:
            raws = list(pool.map(lambda job: run(folders[job]), jobs))
        for job, raw in zip(jobs, raws, strict=True):
            label = f"{job[0]}-{job[1]}"
            (out / f"{label}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
            with rounds.round(label) as current:
                written = folders[job] / "ticket.md"
                ticket = written.read_text(encoding="utf-8") if written.is_file() else ""
                (out / f"{label}.ticket.md").write_text(ticket, encoding="utf-8", newline="\n")
                style, answer = facts(raw)
                measured, result = judge(job[0], style, answer, ticket)
                current.mark(
                    measured=measured, result=f"{job[0]}: {result}" if measured else result
                )
                print(f"[{'측정' if measured else '측정 아님'}] {label} · {result}")
                print("    답:", " ".join((answer or "결과 없음").split()))
    finally:
        try:
            shutil.rmtree(root)
        except OSError as error:
            print(f"임시 디렉터리를 다 지우지 못했다: {root} ({error})")
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
