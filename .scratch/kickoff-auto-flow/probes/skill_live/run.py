"""세션 도중에 만든 스킬을 그 세션에서 사람이 `/이름`으로 부를 수 있는지 잰다(ADR 0028 "첫 시작").

`claude -p` 세션 하나를 stream-json 입력으로 열어 턴을 차례로 보낸다. 스킬은
`disable-model-invocation: true` 이고(진행 스킬과 같다) 본문은 표지 한 줄만 답하라는 것이다. 스킬은
프로젝트 `.claude/skills` 에 만든다.

- C: 세션 전에 없던 `.claude/skills` 를 도중에 만들고 부른다. 새 기계의 사용자 레벨 폴더(아직
  없다)를 대신한다. 한 번 더 부르고, `/reload-skills` 뒤에 다시 부른다.
- D: 세션 전에 빈 `.claude/skills` 를 두고 도중에 스킬을 만들어 부른다. 폴더가 이미 있는 기계이고,
  실린다는 해석의 양성 대조다.
- E: C 와 같이 폴더가 없다가 생기고, 부르기 전에 `/reload-skills` 를 먼저 보낸다.

C 의 둘째 부르기는 "기다린 시간이 모자랐다"는 해석과 "그 폴더를 감시하지 않는다"는 해석을 가른다.
첫 부르기보다 한 턴 늦게 보내도 실리지 않으면 앞의 해석이 아니다.

부르기 턴마다 CLI 가 낸 표지 둘로 가른다(2026-10-12 저장한 원본 기록에서 봤다). 실렸으면
`--replay-user-messages` 가 다시 낸 사용자 메시지가 `<command-name>/이름</command-name>` 태그를 들고
그 턴의 `system/init` 의 `skills` 에 이름이 있으며 답이 표지 그대로다. 실리지 않았으면 다시 낸
사용자 메시지가 `/이름` 글자 그대로이고 `skills` 에 이름이 없다. 스킬 본문은 다시 낸 메시지에 실리지
않는다. 둘 중 어느 쪽도 아닌 턴(시간 초과, 표지가 섞임, 보낼 때 스킬 파일이 없음)은 측정이 아니라고
따로 세고, 하나라도 있으면 1로 끝난다.

사용자 레벨은 이 프로브가 재지 않는다. 사용자 레벨 스킬은 설정 출처에 `user` 가 있어야 실렸다. 이
프로브의 첫 판에 있던 대조군(세션 전에 `~/.claude/skills` 에 만든 스킬을 `project,local` 로
부른다)이 부르지 못했다(2026-10-12 손으로 봤다. 지금 판에는 그 변형이 없다). 그 출처를 켜면 이
기계의 `~/.claude/settings.json` 의 `hooks.Stop` 이 부르는 `~/.claude/hooks/stop-hook.sh` 가 턴마다
Slack 으로 알림을 보낸다(두 파일을 읽었다). 그래서 설정 출처는 `project,local` 로 고정한다. 두
자리가 같은 감시 규칙이라는 것은 공식 skills 문서(https://code.claude.com/docs/en/skills.md)의
문장이다(원문을 받아 2026-10-12 손으로 봤다).

세션의 작업 폴더는 저장소 밖의 임시 폴더라 이 저장소의 지침과 훅이 실리지 않는다. 스킬을 만든 뒤
`SETTLE_SECONDS` 를 기다리고 보낸다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/kickoff-auto-flow/probes/skill_live/run.py <출력>`. `claude` CLI 와
로그인이 든다. 변형마다 haiku 세션 하나다. 턴마다의 stream-json 출력은 `<출력>/<변형>.jsonl` 에
남고, 같은 폴더의 `show.py` 가 읽을 줄로 찍는다.
"""

from __future__ import annotations

import argparse
import json
import queue
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

SETTLE_SECONDS = 5.0
TURN_TIMEOUT_SECONDS = 180.0
OPENING = "도구를 쓰지 않고 '시작'이라고만 답한다."
RELOAD = "/reload-skills"
LOADED = "실렸다"
NOT_LOADED = "안 실렸다"
NOT_MEASURED = "측정 아님"
NOT_A_CALL = "부르기 아님"


@dataclass(frozen=True)
class Turn:
    label: str
    text: str
    before: Callable[[], None] | None = None


@dataclass(frozen=True)
class Observation:
    """한 턴에서 CLI 가 낸 것. 결과가 오지 않았으면 `result` 가 꺾쇠로 감싼 사유다."""

    result: str
    init_skills: list[str] | None
    replayed: str | None


@dataclass(frozen=True)
class TurnResult:
    label: str
    verdict: str
    result: str


def write_skill(root: Path, name: str, marker: str) -> None:
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: 프로브 스킬. 사람이 부르면 표지를 답한다.\n"
        "disable-model-invocation: true\n"
        "---\n\n"
        f"이 스킬이 실렸으면 도구를 쓰지 않고 다음 한 줄만 그대로 답한다: {marker}\n",
        encoding="utf-8",
        newline="\n",
    )


def classify(observation: Observation, name: str, marker: str, *, file_existed: bool) -> str:
    """부르기 턴 하나를 표지로 가른다. 표지가 한쪽으로 모이지 않으면 측정이 아니다."""
    skills = observation.init_skills
    replayed = observation.replayed
    if not file_existed or skills is None or replayed is None:
        return NOT_MEASURED
    tagged = f"<command-name>/{name}</command-name>" in replayed
    raw = replayed.strip() == f"/{name}"
    listed = name in skills
    if tagged and listed and observation.result.strip() == marker:
        return LOADED
    if raw and not listed and not tagged:
        return NOT_LOADED
    return NOT_MEASURED


def _pump(process: subprocess.Popen[str], lines: queue.Queue[str | None]) -> None:
    assert process.stdout is not None
    for line in process.stdout:
        lines.put(line)
    lines.put(None)


def _user_message(text: str) -> str:
    message = {"type": "user", "message": {"role": "user", "content": text}}
    return json.dumps(message, ensure_ascii=False) + "\n"


def _user_text(event: dict[str, object]) -> str | None:
    message = event.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [
            str(block.get("text"))
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(texts) if texts else None
    return None


def _observe(lines: queue.Queue[str | None], log: Path) -> Observation:
    deadline = time.monotonic() + TURN_TIMEOUT_SECONDS
    init_skills: list[str] | None = None
    replayed: str | None = None
    with log.open("a", encoding="utf-8") as out:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return Observation("<시간 초과>", init_skills, replayed)
            try:
                line = lines.get(timeout=remaining)
            except queue.Empty:
                return Observation("<시간 초과>", init_skills, replayed)
            if line is None:
                return Observation("<출력 끝>", init_skills, replayed)
            out.write(line)
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            kind = event.get("type")
            if kind == "system" and event.get("subtype") == "init":
                skills = event.get("skills")
                init_skills = [str(s) for s in skills] if isinstance(skills, list) else []
            elif kind == "user" and replayed is None:
                replayed = _user_text(event)
            elif kind == "result":
                text = event.get("result")
                result = text if isinstance(text, str) else json.dumps(event, ensure_ascii=False)
                return Observation(result, init_skills, replayed)


def converse(
    claude: str, cwd: Path, turns: list[Turn], name: str, marker: str, log: Path
) -> list[TurnResult]:
    command = [
        claude,
        "-p",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
        "--verbose",
        "--replay-user-messages",
        "--model",
        "haiku",
        "--strict-mcp-config",
        "--setting-sources",
        "project,local",
        "--max-turns",
        "2",
    ]
    log.write_text("", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
    )
    lines: queue.Queue[str | None] = queue.Queue()
    threading.Thread(target=_pump, args=(process, lines), daemon=True).start()
    assert process.stdin is not None
    skill_file = cwd / ".claude" / "skills" / name / "SKILL.md"
    results: list[TurnResult] = []
    try:
        for turn in turns:
            if turn.before is not None:
                turn.before()
                time.sleep(SETTLE_SECONDS)
            file_existed = skill_file.is_file()
            process.stdin.write(_user_message(turn.text))
            process.stdin.flush()
            observation = _observe(lines, log)
            if turn.text == f"/{name}":
                verdict = classify(observation, name, marker, file_existed=file_existed)
            else:
                verdict = NOT_A_CALL
            results.append(TurnResult(turn.label, verdict, observation.result))
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
    return results


def turns_for(variant: str, cwd: Path, name: str, marker: str) -> list[Turn]:
    call = f"/{name}"

    def make() -> None:
        write_skill(cwd / ".claude" / "skills", name, marker)

    if variant == "C":
        return [
            Turn("시작", OPENING),
            Turn("도중에 만들고 부른다", call, make),
            Turn("한 번 더 부른다", call),
            Turn(RELOAD, RELOAD),
            Turn("다시 부른다", call),
        ]
    if variant == "D":
        (cwd / ".claude" / "skills").mkdir(parents=True)
        return [Turn("시작", OPENING), Turn("도중에 만들고 부른다", call, make)]
    if variant == "E":
        return [
            Turn("시작", OPENING),
            Turn(f"도중에 만들고 {RELOAD}", RELOAD, make),
            Turn("부른다", call),
        ]
    raise ValueError(f"모르는 변형: {variant}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    parser.add_argument("--only", default="CDE", help="돌릴 변형의 머리글자")
    args = parser.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    claude = shutil.which("claude")
    if claude is None:
        print("claude CLI 를 찾지 못했다")
        return 2
    token = secrets.token_hex(4)
    marker = f"SKILL-LOADED-{token}"
    summary: dict[str, list[TurnResult]] = {}
    # 자식이 폴더를 쥔 채 끝나면 Windows 에서 정리가 실패한다. 측정 요약을 잃지 않게 넘긴다.
    with tempfile.TemporaryDirectory(prefix="skill-live-", ignore_cleanup_errors=True) as scratch:
        for variant in args.only:
            cwd = Path(scratch) / variant
            cwd.mkdir()
            name = f"probe-live-{token}-{variant.lower()}"
            turns = turns_for(variant, cwd, name, marker)
            log = out / f"{variant}.jsonl"
            summary[variant] = converse(claude, cwd, turns, name, marker, log)
    version = subprocess.run(
        [claude, "--version"], capture_output=True, text=True, encoding="utf-8", check=False
    )
    print(f"claude {version.stdout.strip()}, 표지 {marker}")
    unmeasured = 0
    for variant, results in summary.items():
        print(variant)
        for result in results:
            excerpt = " ".join(result.result.split())[:100]
            # 구분자는 ASCII 다. cp949 콘솔(PYTHONUTF8 없음)에서도 요약이 찍히게 한다.
            print(f"  {result.label}: {result.verdict} : {excerpt}")
            unmeasured += result.verdict == NOT_MEASURED
    print(f"측정이 아닌 부르기 턴: {unmeasured}")
    return 1 if unmeasured else 0


if __name__ == "__main__":
    raise SystemExit(main())
