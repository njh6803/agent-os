"""지침 파일 검사. 런북 3단계와 ADR 0004의 기계 판정자.

- `.claude/rules/*.md`는 `paths` 프론트매터가 있어야 한다. 없으면 매 세션 전부 실린다.
- `CLAUDE.md`는 200줄 이하다.
- `CLAUDE.md`의 `@` 임포트는 `docs/constitution/principles.md` 하나뿐이다.
- 원본 위에 덧댄 스킬 사본은 `프로젝트 사본` 주석을 지니고 있어야 한다.

pre-commit이 커밋마다 돌린다. 규칙을 쓰는 시점에 걸리는 것과 나중에 전부 재배치하는 것은
비용이 다르다(선행 저장소 AAPP-15).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_LINES = 200
ALLOWED_IMPORTS = ["@docs/constitution/principles.md"]
PATCHED_SKILLS = ("code-review", "implement", "retro")
SENTINEL = "프로젝트 사본"


def rules_without_paths() -> list[Path]:
    bad: list[Path] = []
    for path in sorted((ROOT / ".claude" / "rules").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        front = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if front is None or re.search(r"^paths:\s*$", front.group(1), re.M) is None:
            bad.append(path)
    return bad


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
    problems.extend(claude_md_problems())
    problems.extend(patched_skills_without_sentinel())
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
