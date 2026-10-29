"""인계 훅의 실행 확인 프로브(티켓 05). 네 갈래를 잰다.

- A_reach: 문턱을 1,000 으로 낮춘 `tools/hook_handoff.py` 사본과 탐침 훅을 PostToolUse(Bash)에, 같은
  문턱의 `tools/hook_handoff_notice.py` 사본과 탐침 훅을 Stop 에 붙이고, 임시 저장소에 빈 커밋을
  하나 하게 한다. 모델에게 그 호출에 붙어 온 훅 알림의 첫 두 문장을 옮기게 한다. 옮기면
  additionalContext 가 닿은 것이다. 탐침 훅이 받은 실제 입력(PostToolUse, Stop)을
  `<out>/A_reach_payloads.jsonl` 에 남긴다.
- B_control: A 의 대조군. 같은 훅을 붙이고 경계가 아닌 `git status` 를 하게 한다. '알림 없음' 이어야
  한다.
- C_read_main: 이 워크트리를 작업 폴더로, 기본 권한 모드에서 주 체크아웃의 next-session 스킬 파일을
  Read 로 열게 한다. 결과 JSON 의 `permission_denials` 로 승인 질문(비대화형이라 거부로 나타난다)이
  났는지 본다.
- D_read_own: C 의 양성 대조. 같은 자리와 모드에서 작업 폴더 안의 사본(이 워크트리의 스킬 파일)을
  열게 한다. 거부가 없고 2행을 옮겨야 한다. C 의 거부가 "작업 폴더 밖이라서"이고 "Read 가 막혀서"가
  아님을 가른다.

시험 세션은 세션 컨텍스트가 20만을 넘기 어려워 문턱을 낮춘 사본을 `<out>` 에 두고 돌린다(커밋하지
않는다). 사본 옆에 스킬 파일의 사본을 두어 훅 문장의 경로가 실제로 있는 파일을 가리키게 한다. A·B 는
저장소 밖에서, C·D 는 이 워크트리에서 `--setting-sources local` 로 돌려 이 저장소와 사용자 전역의
훅과 권한 규칙을 뺀다.

돌리는 법: 워크트리 루트에서 `uv run python .scratch/token-usage/probes/handoff_reach.py <저장소 밖
디렉터리> <주 체크아웃 루트>`. `claude` CLI 와 인증이 든다. 갈래마다 sonnet 세션 하나다. 출력은
갈래마다 판정 한 줄이고, 표지가 없는 갈래(측정 아님)가 하나라도 있으면 1로 끝난다.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
SKILL = Path(".claude") / "skills" / "next-session" / "SKILL.md"
LOWERED = 1_000
DUMP = """import sys
from pathlib import Path
with Path(sys.argv[1]).open("ab") as out:
    out.write(sys.stdin.buffer.read().strip() + b"\\n")
"""
ASK = (
    "그 뒤 다른 도구는 부르지 말고, 그 Bash 호출에 붙어 온 훅 알림(additionalContext 나 시스템 "
    "리마인더)이 있으면 그 첫 두 문장을 그대로 옮기고, 없으면 '알림 없음' 이라고 한 줄로 답한다."
)


def _lowered_copy(out: Path) -> Path:
    """문턱을 낮춘 두 훅과 next-session 스킬 폴더의 사본.

    훅의 `HANDOFF_PATH` 는 사본 옆의 `handoff.md` 를 가리킨다. 그 파일이 가리키는 `directive.md` 도
    같은 폴더라 폴더째 옮긴다.
    """
    copy = out / "copy"
    (copy / "tools").mkdir(parents=True, exist_ok=True)
    for name in ("hook_handoff.py", "hook_handoff_notice.py"):
        text = (ROOT / "tools" / name).read_text(encoding="utf-8")
        assert "THRESHOLD = 200_000" in text, name
        lowered = text.replace("THRESHOLD = 200_000", f"THRESHOLD = {LOWERED}")
        (copy / "tools" / name).write_text(lowered, encoding="utf-8")
    shutil.copytree(ROOT / SKILL.parent, copy / SKILL.parent, dirs_exist_ok=True)
    (out / "dump.py").write_text(DUMP, encoding="utf-8")
    return copy


def _settings(out: Path, copy: Path, name: str) -> Path:
    python = Path(sys.executable).as_posix()
    payloads = (out / f"{name}_payloads.jsonl").as_posix()
    dump = f'"{python}" "{(out / "dump.py").as_posix()}" "{payloads}"'

    def hook(script: str) -> dict[str, object]:
        return {
            "type": "command",
            "command": f'"{python}" "{(copy / "tools" / script).as_posix()}"',
        }

    settings = {
        "hooks": {
            "PostToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [{"type": "command", "command": dump}, hook("hook_handoff.py")],
                }
            ],
            "Stop": [
                {"hooks": [{"type": "command", "command": dump}, hook("hook_handoff_notice.py")]}
            ],
        }
    }
    path = out / f"{name}.settings.json"
    path.write_text(json.dumps(settings, ensure_ascii=False), encoding="utf-8")
    return path


def _claude(cwd: Path, prompt: str, args: list[str], log: Path) -> dict[str, object]:
    command = [
        "claude",
        "-p",
        "--strict-mcp-config",
        "--model",
        "sonnet",
        "--output-format",
        "json",
    ]
    done = subprocess.run(
        [*command, *args],
        cwd=cwd,
        input=prompt.encode("utf-8"),
        capture_output=True,
        timeout=600,
        check=False,
    )
    log.write_bytes(done.stdout + b"\n--- stderr ---\n" + done.stderr)
    parsed: dict[str, object] = json.loads(done.stdout)
    return parsed


def _hook_saw(payloads: Path, command: str) -> bool:
    """표지: 탐침 훅이 그 명령의 PostToolUse 입력을 받았다(명령이 돌았고 훅이 붙었다)."""
    if not payloads.is_file():
        return False
    for line in payloads.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("hook_event_name") == "PostToolUse":
            if command in str(record.get("tool_input", {}).get("command", "")):
                return True
    return False


def _hook_branches(out: Path, repo: Path) -> int:
    """A·B 를 돌리고 표지가 없는 갈래 수를 돌려준다."""
    copy = _lowered_copy(out)
    common = ["--setting-sources", "local", "--max-turns", "4"]
    common += ["--tools", "Bash", "--allowed-tools", "Bash"]
    identity = "-c user.name=p -c user.email=p@localhost"
    unmeasured = 0
    for name, command, expected in (
        (
            "A_reach",
            f"git -C {repo.as_posix()} {identity} commit --allow-empty -m probe",
            "인계의 계기",
        ),
        ("B_control", f"git -C {repo.as_posix()} status --short", "알림 없음"),
    ):
        payloads = out / f"{name}_payloads.jsonl"
        payloads.unlink(missing_ok=True)
        settings = _settings(out, copy, name)
        prompt = f"Bash 도구로 정확히 이 명령 하나만 한 번 실행한다: {command}\n{ASK}"
        result = _claude(out, prompt, [*common, "--settings", str(settings)], out / f"{name}.json")
        answer = str(result.get("result"))
        seen = _hook_saw(payloads, command)
        unmeasured += 0 if seen else 1
        verdict = ("맞다" if expected in answer else "다르다") if seen else "측정 아님"
        print(f"{name}: {verdict} — {json.dumps(answer, ensure_ascii=False)}")
    return unmeasured


def _read_branch(out: Path, name: str, target: Path, *, expect_denied: bool) -> int:
    """C·D 하나를 돌린다. 표지는 답이 2행(`name: next-session`)을 옮겼거나 거부가 찍힌 것이다."""
    args = ["--setting-sources", "local", "--max-turns", "3", "--tools", "Read"]
    args += ["--permission-mode", "default"]
    prompt = (
        f"Read 도구로 {target.as_posix()} 를 열어 2행을 그대로 옮긴다. 열지 못하면 그 까닭을 "
        "한 줄로 적는다."
    )
    result = _claude(ROOT, prompt, args, out / f"{name}.json")
    denials = result.get("permission_denials")
    answer = str(result.get("result"))
    copied = "name: next-session" in answer
    if not copied and not denials:
        print(f"{name}: 측정 아님 — {json.dumps(answer, ensure_ascii=False)}")
        return 1
    verdict = "맞다" if bool(denials) == expect_denied and copied != expect_denied else "다르다"
    shown = json.dumps(denials, ensure_ascii=False)
    print(f"{name}: {verdict} — 거부={shown} 답={json.dumps(answer, ensure_ascii=False)}")
    return 0


def main() -> int:
    out = Path(sys.argv[1]).resolve()
    main_root = Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    repo = out / "repo"
    if not repo.exists():
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
    unmeasured = _hook_branches(out, repo)
    unmeasured += _read_branch(out, "C_read_main", main_root / SKILL, expect_denied=True)
    unmeasured += _read_branch(out, "D_read_own", ROOT / SKILL, expect_denied=False)
    return 1 if unmeasured else 0


if __name__ == "__main__":
    raise SystemExit(main())
