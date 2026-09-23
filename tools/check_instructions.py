"""지침 파일과 하네스 설정 검사. 규칙 배치는 런북 3단계와 ADR 0004의 기계 판정자이고, 경로 참조
두 가지(rules 의 glob, 훅 명령)는 2026-09-23 의 잠김(PR #52)에서 왔다.

- `.claude/rules/*.md`는 `paths` 프론트매터가 있어야 한다. 없으면 매 세션 전부 실린다.
- 그 `paths`의 glob은 저장소에서 무언가를 가리켜야 한다. 아무것도 안 가리키면 그 규칙이 조용히
  안 실린다.
- `.claude/settings.json`의 훅은 저장소 파일을 `${CLAUDE_PROJECT_DIR}`로 부른다. 상대 경로면 세션이
  루트를 벗어나는 순간 깨진다.
- `CLAUDE.md`는 200줄 이하다.
- `CLAUDE.md`의 `@` 임포트는 `docs/constitution/principles.md` 하나뿐이다.
- 원본 위에 덧댄 스킬 사본은 `프로젝트 사본` 주석을 지니고 있어야 한다.

pre-commit이 커밋마다 돌린다. 규칙을 쓰는 시점에 걸리는 것과 나중에 전부 재배치하는 것은
비용이 다르다(선행 저장소 AAPP-15).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent
MAX_LINES = 200
ALLOWED_IMPORTS = ["@docs/constitution/principles.md"]
PATCHED_SKILLS = ("code-review", "implement", "retro")
SENTINEL = "프로젝트 사본"
SETTINGS = Path(".claude") / "settings.json"
PROJECT_DIR_PLACEHOLDER = "${CLAUDE_PROJECT_DIR}"

_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
_PATHS_BLOCK = re.compile(r"^paths:[ \t]*\n((?:[ \t]+-[^\n]*\n?)+)", re.M)
_LIST_ITEM = re.compile(r"^[ \t]+-[ \t]*(.+?)[ \t]*$", re.M)
# 상대 경로처럼 생긴 토큰. 바로 앞 글자가 경로의 일부(`/`, `}`, 이름 글자)면 잡지 않아서
# `${CLAUDE_PROJECT_DIR}/tools/x.py` 의 `tools/x.py` 는 지나간다.
_PATH_TOKEN = re.compile(r"(?<![\w/}.~-])([\w.-]+(?:/[\w.-]+)+)")


class _HookCommand(TypedDict, total=False):
    type: str
    command: str


class _HookGroup(TypedDict, total=False):
    matcher: str
    hooks: list[_HookCommand]


class _Settings(TypedDict, total=False):
    hooks: dict[str, list[_HookGroup]]


def _front_matter(text: str) -> str | None:
    match = _FRONT_MATTER.match(text)
    return None if match is None else match.group(1)


def _paths_block(text: str) -> str | None:
    """`paths:` 아래 항목들. 키만 있고 항목이 없으면 없는 것으로 본다.

    두 검사가 이 판정을 같이 쓴다. 따로 쓰면 항목 없는 `paths:` 가 둘 다를 빠져나간다.
    """
    front = _front_matter(text)
    block = None if front is None else _PATHS_BLOCK.search(front)
    return None if block is None else block.group(1)


def rules_without_paths(root: Path = ROOT) -> list[Path]:
    return [
        path
        for path in sorted((root / ".claude" / "rules").glob("*.md"))
        if _paths_block(path.read_text(encoding="utf-8")) is None
    ]


def rules_with_dead_paths(root: Path = ROOT) -> list[str]:
    """`paths`의 glob마다 저장소에서 하나라도 가리키는지 본다.

    파일을 옮기거나 나누면 그 이름을 적은 규칙이 조용히 안 실린다. 훅과 달리 아무 오류도 나지
    않아서, 판정자가 없으면 아무도 모른다. `paths` 가 없는 파일은 `rules_without_paths` 가 잡는다.

    판정은 `pathlib` 의 glob 이다. 이 저장소의 패턴은 `dir/**` 와 정확한 파일 경로뿐이라 그것으로
    충분하다. 못 보는 것: 중괄호 확장처럼 `pathlib` 이 모르는 문법은 살아 있어도 죽었다고 본다(쓰게
    되면 이 판정을 먼저 넓힌다). `dir/**` 는 빈 디렉터리도 살아 있다고 본다. glob 이 gitignore 된
    로컬 파일을 보고 윈도에서 대소문자를 무시하므로, 로컬 초록이 CI 에서 빨강이 될 수 있다 — 그때는
    CI 가 맞다.
    """
    problems: list[str] = []
    for path in sorted((root / ".claude" / "rules").glob("*.md")):
        block = _paths_block(path.read_text(encoding="utf-8"))
        if block is None:
            continue
        rule = path.relative_to(root).as_posix()
        for item in _LIST_ITEM.finditer(block):
            # YAML 뒷주석(`- "src/**"  # 설명`)은 패턴이 아니다.
            pattern = item.group(1).split(" #", 1)[0].strip().strip("\"'")
            try:
                dead = next(root.glob(pattern), None) is None
            except (ValueError, NotImplementedError) as error:
                problems.append(f"{rule}: paths 의 '{pattern}' 를 glob 으로 읽을 수 없다({error})")
                continue
            if dead:
                problems.append(
                    f"{rule}: paths 의 '{pattern}' 가 아무 파일도 가리키지 않는다. 그 규칙이"
                    " 조용히 안 실린다"
                )
    return problems


def _hook_commands(root: Path) -> Iterator[tuple[str, str]]:
    """`.claude/settings.json` 의 훅 명령을 (이벤트, 명령) 으로 하나씩 낸다. 설정이 없으면 없다."""
    path = root / SETTINGS
    if not path.exists():
        return
    settings: _Settings = json.loads(path.read_text(encoding="utf-8"))
    for event, groups in settings.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                yield event, hook.get("command", "")


def hooks_with_relative_paths(root: Path = ROOT) -> list[str]:
    """훅 명령이 저장소 파일을 상대 경로로 부르는지 본다.

    훅은 세션의 현재 디렉터리에서 돈다. 상대 경로면 세션이 저장소 루트를 벗어나는 순간 스크립트를
    못 찾고, 파이썬은 그때 종료 코드 2 로 끝나는데 PreToolUse 에서 2 는 "막아라" 다. 그래서 경로
    하나가 틀리면 모든 Bash 호출이 막힌다(2026-09-23, PR #52).

    저장소에 실재하는 파일을 가리키는 토큰만 잡는다. 모든 훅에 `${CLAUDE_PROJECT_DIR}` 을 요구하면
    `echo` 나 홈 디렉터리에 쓰는 훅처럼 저장소 파일을 부르지 않는 훅이 커밋을 막는다.

    받는 모양은 경로 앞의 `${CLAUDE_PROJECT_DIR}/` 하나다. 그래서 잡는 것 중에 동작하는 것도 있다 —
    `cd "$CLAUDE_PROJECT_DIR" && python tools/x.py` 처럼 먼저 옮기는 훅, 그리고 저장소 경로를
    데이터로만 쓰는 훅(`grep -q docs/x.md`). 못 보는 것: 백슬래시 경로(`tools\\x.py`),
    루트의 파일을 이름만으로 부르는 것(`python x.py`), `$PWD/…`, 그리고 `uv run` 에
    `--project` 가 빠진 것(저장소 밖에서
    프로젝트가 아니라 시스템 파이썬으로 돈다). 지금 이 저장소의 훅은 어느 쪽에도 해당하지 않는다.
    """
    problems: list[str] = []
    for event, command in _hook_commands(root):
        for token in _PATH_TOKEN.finditer(command):
            relative = token.group(1)
            if (root / relative).is_file():
                problems.append(
                    f"{SETTINGS.as_posix()} 의 {event} 훅이 저장소 파일을 상대 경로로 부른다:"
                    f" {relative}. 훅은 세션의 현재 디렉터리에서 돌아 루트를 벗어나면 못 찾는다."
                    f' "{PROJECT_DIR_PLACEHOLDER}/{relative}" 로 쓴다'
                )
    return problems


def claude_md_problems() -> list[str]:
    lines = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    problems: list[str] = []
    if len(lines) > MAX_LINES:
        problems.append(f"CLAUDE.md {len(lines)}줄 > {MAX_LINES}줄. 로드 시점 표로 다시 나눈다")
    imports = [line.strip() for line in lines if line.startswith("@")]
    if imports != ALLOWED_IMPORTS:
        problems.append(f"CLAUDE.md의 @ 임포트는 {ALLOWED_IMPORTS}뿐이어야 한다. 지금: {imports}")
    return problems


def patched_skills_without_sentinel(root: Path = ROOT) -> list[str]:
    """덧댄 사본이 `npx skills update -p`에 덮어써졌는지 본다.

    무엇을 덧댔는지는 각 파일의 `<!-- 프로젝트 사본 ... -->` 주석이 기록한다.
    주석이 사라졌으면 사본이 원본으로 되돌아간 것이고, 그 뒤로도 리뷰는 초록이다.
    """
    problems: list[str] = []
    for name in PATCHED_SKILLS:
        path = root / ".claude" / "skills" / name / "SKILL.md"
        if not path.exists():
            problems.append(f".claude/skills/{name}/SKILL.md 없음. 사본이 사라졌다")
        elif SENTINEL not in path.read_text(encoding="utf-8"):
            problems.append(
                f".claude/skills/{name}/SKILL.md에 '{SENTINEL}' 주석 없음."
                " npx skills update가 덧댄 것을 되돌렸다"
            )
    return problems


def main() -> int:
    problems = [
        f"{path.relative_to(ROOT)}: paths 프론트매터 없음. 없으면 매 세션 실린다"
        for path in rules_without_paths()
    ]
    problems.extend(rules_with_dead_paths())
    problems.extend(hooks_with_relative_paths())
    problems.extend(claude_md_problems())
    problems.extend(patched_skills_without_sentinel())
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
