"""지침 파일과 하네스 설정 검사. 규칙 배치는 런북 3단계와 ADR 0004의 기계 판정자이고, 경로 참조
두 가지(rules 의 glob, 훅 명령)는 2026-09-23 의 잠김(PR #52)에서, `@` 임포트와 임포트된 파일의
경로와 사본 센티널과 훅의 stdin 은 2026-09-28 의 하네스 감사(대기열 25·32 와 감사 지적)에서, 중첩
지침 파일은 web-admin 티켓 01 에서, rules 와 임포트된 파일 안의 `@` 는 2026-09-29 실측에서 왔다.

- `.claude/rules/` 아래(하위 폴더까지)의 규칙은 `paths` 프론트매터가 있어야 한다. 없으면 매 세션
  전부 실린다.
- 그 `paths`의 glob은 저장소에서 무언가를 가리켜야 한다. 아무것도 안 가리키면 그 규칙이 조용히
  안 실린다.
- `.claude/settings.json`의 훅은 저장소 파일을 `${CLAUDE_PROJECT_DIR}`로 부른다. 상대 경로면 세션이
  루트를 벗어나는 순간 깨진다.
- `CLAUDE.md`는 200줄 이하다.
- `CLAUDE.md`의 `@` 임포트는 `docs/constitution/principles.md` 하나뿐이다. 줄 머리만이 아니라
  문장 속 `@경로` 도 임포트다(공식 문서: "reference them with @ syntax anywhere"). 코드 스팬과
  펜스 안은 아니다.
- 임포트된 파일 안의 백틱 경로는 저장소 루트 기준으로 실재해야 한다. `@` 임포트의 상대 경로는 그
  임포트를 담은 파일 기준으로 풀리지만, 백틱 경로는 모델이 읽는 글자라 루트(작업의 자리) 기준으로
  읽혔다(대기열 32, PR #43 이 헌법의 형제 `README.md` 를 루트 README 로 읽어 버전을 못 찾았다).
- 원본 위에 덧댄 스킬 사본은 `프로젝트 사본` 주석을 지니고 있어야 하고, 그 주석을 지닌 사본은
  `PATCHED_SKILLS` 에 있어야 한다. 한쪽만 보면 목록 밖의 사본이 되돌려져도 초록이다.
- `tools/hook_*.py`는 stdin 을 바이트(`sys.stdin.buffer`)로 읽는다. 훅 환경에 `PYTHONUTF8` 이 있다고
  가정하지 않는다 — 없으면 텍스트 stdin 은 cp949 이고, 한글이 든 입력은 예외 없이 출력 0바이트가
  된다(대기열 25).
- 루트 밖에 `CLAUDE.md` 와 `AGENTS.md` 가 없다. `next dev` 가 앱 폴더에 두 파일을 만든다(ADR 0021,
  web-admin 티켓 01).
- rules 파일과 임포트된 파일 안에도 `@` 임포트가 없다. 그것들도 따라가서 실린다.

pre-commit이 커밋마다 돌린다. 규칙을 쓰는 시점에 걸리는 것과 나중에 전부 재배치하는 것은
비용이 다르다(선행 저장소 AAPP-15).
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent
MAX_LINES = 200
ALLOWED_IMPORTS = ["@docs/constitution/principles.md"]
PATCHED_SKILLS = (
    "code-review",
    "grilling",
    "implement",
    "retro",
    "to-spec",
    "to-tickets",
)
SENTINEL = "프로젝트 사본"
NESTED_INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md")
SETTINGS = Path(".claude") / "settings.json"
PROJECT_DIR_PLACEHOLDER = "${CLAUDE_PROJECT_DIR}"
# 백틱 토큰이 경로인지 가르는 확장자. 슬래시가 있으면 확장자와 무관하게 경로다. `agent_os.core` 나
# `Any` 처럼 슬래시도 이 확장자도 없는 토큰은 경로가 아니다.
PATH_EXTENSIONS = (".md", ".py", ".toml", ".json", ".yaml", ".yml", ".ps1", ".txt", ".sh")

_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
_PATHS_KEY = re.compile(r"^paths:[ \t]*(.*)$", re.M)
# 키 뒤의 주석(`paths:  # 설명`)을 넘고, 키와 같은 깊이의 항목(`- "src/**"`)도 받는다
# (YAML 이 받는다).
_PATHS_BLOCK = re.compile(r"^paths:[ \t]*(?:#[^\n]*)?\n((?:[ \t]*-[^\n]*\n?)+)", re.M)
_LIST_ITEM = re.compile(r"^[ \t]*-[ \t]*(.+?)[ \t]*$", re.M)
# 상대 경로처럼 생긴 토큰. 바로 앞 글자가 경로의 일부(`/`, `}`, 이름 글자)면 잡지 않아서
# `${CLAUDE_PROJECT_DIR}/tools/x.py` 의 `tools/x.py` 는 지나간다.
_PATH_TOKEN = re.compile(r"(?<![\w/}.~-])([\w.-]+(?:/[\w.-]+)+)")
# 백틱·물결 펜스, 목록 안의 들여쓴 펜스까지. 펜스 안의 `@경로` 는 임포트가 아니다(PR #91 리뷰).
_FENCE = re.compile(r"^[ \t]*(```|~~~).*?^[ \t]*\1[ \t]*$", re.M | re.S)
_CODE_SPAN = re.compile(r"`([^`\n]+)`")
# `@경로` 임포트. 앞이 공백이나 줄 머리이고 뒤가 공백이나 줄 끝인 토큰을 모두 센다. 한글이 든 것만
# 뺀다 — 조사가 붙은 `@x.md를` 은 실리지 않았다(2026-09-29 `claude -p` 2.1.281 실측). 앞이 공백이
# 아닌 `noreply@anthropic.com` 과 `(@x.md)` 도 아니다(같은 실측). 그 밖의 문장부호가 든 것(`@x.md.`,
# `@x.md,`, `@c++.md`)은 재지 않은 것까지 보수적으로 센다 — 실리는 파일을 놓치는 것보다 백틱으로
# 옮기는 것이 싸다. `@x.md.` 는 끝의 마침표까지 토큰이라 허용된 임포트와 다른 것으로 잡힌다.
_IMPORT_TOKEN = re.compile(r"(?<!\S)@([^\s가-힣]+)(?=\s|$)")
_PATHISH = re.compile(r"^\.?[\w.-]+(?:/[\w.*-]+)*/?$")


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


def _split_patterns(value: str) -> list[str]:
    """쉼표로 가른 패턴들. 중괄호(`*.{ts,tsx}`)와 따옴표 안의 쉼표는 가르지 않는다."""
    items: list[str] = []
    current: list[str] = []
    depth = 0
    quote = ""
    for char in value:
        if quote:
            quote = "" if char == quote else quote
        elif char in "\"'":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth = max(depth - 1, 0)
        elif char == "," and depth == 0:
            items.append("".join(current))
            current = []
            continue
        current.append(char)
    items.append("".join(current))
    return items


def _paths_patterns(text: str) -> list[str] | None:
    """`paths` 의 패턴들. 프론트매터나 키가 없거나 항목이 비었으면 없는 것(`None`)이다.

    공식 문서가 받는 모양 셋을 읽는다. 블록 목록(`- "src/**"`), 흐름 목록(`["src/**", "b/**"]`),
    쉼표로 가른 문자열(`"src/**, b/**"`). 두 검사가 이 판정을 같이 쓴다. 따로 쓰면 항목 없는
    `paths:` 가 둘 다를 빠져나간다. 못 보는 것: YAML 로 파싱되지 않는 프론트매터. Claude Code 는
    그때 `paths` 가 없는 것처럼 매 세션 싣는데, 이 판정은 YAML 파서가 아니라 그것을 모른다.
    """
    front = _front_matter(text)
    key = None if front is None else _PATHS_KEY.search(front)
    if front is None or key is None:
        return None
    inline = key.group(1).split(" #", 1)[0].strip()
    if inline.startswith("#"):
        inline = ""
    if inline.startswith("["):
        items = _split_patterns(inline.strip("[]"))
    elif inline:
        items = _split_patterns(inline.strip("\"'"))
    else:
        block = _PATHS_BLOCK.search(front)
        items = [] if block is None else [m.group(1) for m in _LIST_ITEM.finditer(block.group(1))]
    # YAML 뒷주석(`- "src/**"  # 설명`)은 패턴이 아니다.
    patterns = [item.split(" #", 1)[0].strip().strip("\"'").strip() for item in items]
    return [pattern for pattern in patterns if pattern] or None


def _rule_files(root: Path) -> list[Path]:
    """`.claude/rules/` 아래의 규칙 파일 전부. Claude Code 는 하위 폴더까지 재귀로 싣는다."""
    return sorted((root / ".claude" / "rules").rglob("*.md"))


def rules_without_paths(root: Path = ROOT) -> list[Path]:
    return [
        path
        for path in _rule_files(root)
        if _paths_patterns(path.read_text(encoding="utf-8")) is None
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
    for path in _rule_files(root):
        patterns = _paths_patterns(path.read_text(encoding="utf-8"))
        if patterns is None:
            continue
        rule = path.relative_to(root).as_posix()
        for pattern in patterns:
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


def _without_code(text: str) -> str:
    """펜스 블록과 코드 스팬을 뺀 마크다운. 공식 문서가 임포트 파서가 건너뛴다고 밝힌 자리다."""
    return _CODE_SPAN.sub("", _FENCE.sub("", text))


def at_imports(text: str) -> list[str]:
    """본문이 임포트하는 `@경로` 전부. 줄 머리든 문장 속이든 같다.

    2026-09-28 까지는 `line.startswith("@")` 만 봐서 "자세한 것은 @docs/PRD.md" 같은 한 구절이
    파일 하나를 매 세션 통째로 싣는데 검사는 초록이었다. 무엇을 세는지는 `_IMPORT_TOKEN` 이다.
    끝의 마침표는 토큰에 든다 — 그것을 떼어 맞추던 때는 실리지 않는
    `@docs/constitution/principles.md.` 가 허용 목록을 통과했다. 못 보는 것: 블록 HTML
    주석(공식 문서: 주입 전에 지운다)과 들여쓴 코드 블록(2026-09-29 실측) 안의 `@경로` 는
    Claude Code 가 싣지 않지만 여기서는 임포트로 센다. 허용된
    임포트 쪽의 거짓 초록은 `claude_md_problems` 가 한 줄 단독 검사로 막는다. 한글이 든 경로는
    임포트로 세지 않는다.
    """
    return ["@" + match.group(1) for match in _IMPORT_TOKEN.finditer(_without_code(text))]


def claude_md_problems(root: Path = ROOT) -> list[str]:
    lines = (root / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    problems: list[str] = []
    if len(lines) > MAX_LINES:
        problems.append(f"CLAUDE.md {len(lines)}줄 > {MAX_LINES}줄. 로드 시점 표로 다시 나눈다")
    imports = at_imports("\n".join(lines))
    if imports != ALLOWED_IMPORTS:
        problems.append(
            f"CLAUDE.md의 @ 임포트는 {ALLOWED_IMPORTS}뿐이어야 한다. 지금: {imports}."
            " 문장 속 @경로 도 임포트다. 가리키려면 백틱에 넣는다"
        )
    # 허용된 임포트는 실려야 한다. 주석이나 들여쓴 코드 블록 안이면 토큰으로는 세어지지만
    # 실리지 않는다.
    for allowed in ALLOWED_IMPORTS:
        if allowed not in lines:
            problems.append(
                f"CLAUDE.md의 {allowed} 는 한 줄에 단독으로, 들여쓰지 않고 적는다. 주석이나 들여쓴"
                " 코드 블록 안이면 헌법이 실리지 않는다"
            )
    return problems


def imports_outside_claude_md(root: Path = ROOT) -> list[str]:
    """rules 파일과 임포트된 파일 안의 `@경로`.

    임포트는 루트 `CLAUDE.md` 에서만 일어나지 않는다. 규칙 파일과 임포트된 파일 안의 `@경로` 도
    따라가서 통째로 실린다(2026-09-29 `claude -p` 2.1.281 실측, 공식 문서: 최대 네 단계 재귀).
    `CLAUDE.md` 의 허용 목록만 보면 그 문이 열려 있다. 판정은 `at_imports` 와 같다.
    """
    imported_files = [root / imported[1:] for imported in ALLOWED_IMPORTS]
    targets = _rule_files(root) + [path for path in imported_files if path.is_file()]
    problems: list[str] = []
    for path in targets:
        imports = at_imports(path.read_text(encoding="utf-8"))
        if imports:
            problems.append(
                f"{path.relative_to(root).as_posix()}: @ 임포트 {imports}. rules 와 임포트된 파일"
                " 안의 @경로 도 통째로 실린다(CLAUDE.md 의 허용 목록 밖). 가리키려면 백틱에 넣는다"
            )
    return problems


def _looks_like_path(token: str) -> bool:
    if _PATHISH.match(token) is None:
        return False
    return "/" in token or token.endswith(PATH_EXTENSIONS)


def _exists(root: Path, token: str) -> bool:
    if "*" in token:
        return next(root.glob(token), None) is not None
    if token.endswith("/"):
        return (root / token).is_dir()
    return (root / token).exists()


def imported_files_with_dead_paths(root: Path = ROOT) -> list[str]:
    """임포트된 파일의 백틱 경로가 저장소 루트 기준으로 실재하는지 본다.

    `@` 임포트의 상대 경로는 그 임포트를 담은 파일 기준으로 풀린다(공식 memory 문서). 그러나 백틱
    경로는 임포트가 아니라 모델이 읽는 글자이고, 모델은 그것을 작업의 자리인 루트 기준으로 읽었다.
    `principles.md` 가 형제 `README.md` 를 이름만으로 가리켰을 때 루트 README 로 읽혀 PR #43 이 헌법
    버전을 찾지 못했다(대기열 9·32). 경로로 보는 것은 슬래시가 있거나 `PATH_EXTENSIONS` 로 끝나는
    백틱 토큰이다. 못 보는 것: 백틱 없는 경로, 이름이 우연히 루트에도 있는 형제 파일(그때는 있다고
    보고 지나간다).
    """
    problems: list[str] = []
    for imported in ALLOWED_IMPORTS:
        relative = imported[1:]
        path = root / relative
        if not path.is_file():
            problems.append(f"CLAUDE.md 가 임포트하는 {relative} 이 없다")
            continue
        for token in _CODE_SPAN.findall(path.read_text(encoding="utf-8")):
            if _looks_like_path(token) and not _exists(root, token):
                problems.append(
                    f"{relative}: `{token}` 이 저장소 루트 기준으로 없다. 백틱 경로는 모델이 루트"
                    " 기준으로 읽으므로 형제 파일도 전체 경로로 적는다"
                )
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


def skills_with_sentinel_not_listed(root: Path = ROOT) -> list[str]:
    """센티널을 지닌 사본이 `PATCHED_SKILLS` 밖에 있는지 본다. 앞 검사의 역방향이다.

    목록은 손으로 유지된다. 사본을 새로 덧대며 주석은 붙이고 목록은 잊으면, 그 사본은 앞 검사가
    보지 않아 `npx skills update -p` 가 되돌려도 초록이다(2026-09-28 감사). 주석을 붙이는 커밋에서
    걸리므로 사람이 기억할 것이 없다.
    """
    problems: list[str] = []
    for path in sorted((root / ".claude" / "skills").glob("*/SKILL.md")):
        name = path.parent.name
        if name in PATCHED_SKILLS:
            continue
        if SENTINEL in path.read_text(encoding="utf-8"):
            problems.append(
                f".claude/skills/{name}/SKILL.md 에 '{SENTINEL}' 주석이 있는데"
                " tools/check_instructions.py 의 PATCHED_SKILLS 에 없다. 목록 밖의 사본은"
                " 되돌려져도 검사가 초록이다"
            )
    return problems


def _is_sys_stdin(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "stdin"
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
    )


def text_stdin_lines(source: str) -> list[int]:
    """`sys.stdin.buffer` 가 아닌 `sys.stdin` 과 `from sys import stdin` 이 나오는 줄들.

    못 보는 것: `import sys as s` 뒤의 `s.stdin`, `open(0)`, `io.TextIOWrapper(...)` 로 다시 감싼
    것. 훅이 그렇게 쓸 이유가 없어 닫지 않았다. 생기면 여기서 넓힌다.
    """
    tree = ast.parse(source)
    buffered = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "buffer" and _is_sys_stdin(node.value)
    }
    lines = {
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and _is_sys_stdin(node) and id(node) not in buffered
    }
    lines.update(
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "sys"
        and any(alias.name == "stdin" for alias in node.names)
    )
    return sorted(lines)


def hooks_reading_text_stdin(root: Path = ROOT) -> list[str]:
    """훅이 stdin 을 텍스트로 읽는지 본다.

    훅 프로세스에 `PYTHONUTF8` 이 없으면 텍스트 stdin 이 cp949 로 읽힌다. 한글이 든 페이로드는
    깨져서 매치되지 않고, 예외 없이 exit 0·출력 0바이트로 끝나 "발동 조건 아님" 과 구별되지 않는다
    (PR #60 에서 변이로 실측, 대기열 25). 판정은 AST 라 독스트링의 낱말은 세지 않는다.
    """
    problems: list[str] = []
    for path in sorted((root / "tools").glob("hook_*.py")):
        for lineno in text_stdin_lines(path.read_text(encoding="utf-8")):
            problems.append(
                f"{path.relative_to(root).as_posix()}:{lineno}: sys.stdin 을 텍스트로 읽는다."
                " 훅 환경은 cp949 라 한글이 깨진다. json.load(sys.stdin.buffer) 로 읽는다"
            )
    return problems


def nested_instruction_files(root: Path = ROOT) -> list[str]:
    """루트 밖의 `CLAUDE.md` 와 `AGENTS.md`.

    지침은 `.claude/rules/*.md` + `paths` 에 둔다(ADR 0004). 하위 디렉터리의 `CLAUDE.md` 는
    Claude 가 그 디렉터리의 파일을 Read 할 때 통째로 실리고(cwd 가 그 디렉터리면 시작 시),
    그 안의 `@` 임포트도 따라온다. 그래서 루트 지침에 거는 검사(200줄, 임포트 허용 목록) 밖에
    놓인다(2026-09-29 `claude -p` 2.1.281 실측). `next dev` 는 에이전트를 감지하면 앱 폴더에
    두 파일을 만든다(ADR 0021). `agentRules: false` 가 그것을 끄지만, 설정 한 줄을 보는
    테스트보다 결과를 보는 검사가 원인과 무관하게 잡는다.

    작업 트리를 훑으므로 pre-commit 은 추적하지 않는 파일도 보고, CI 는 체크아웃된 것(추적하는
    것)만 본다. 보지 않는 곳: 어느 깊이든 `node_modules`, 루트의 `.venv` 와 `.git`(설치된
    의존성과 git 의 것이라 이 저장소의 지침이 아니다), `.claude/worktrees`(다른 체크아웃의 루트
    `CLAUDE.md`). 못 보는 것: 대소문자가 다른 이름(`claude.md`), 다른 도구의 지침 파일
    이름(`GEMINI.md`, `.cursorrules`), 하위 디렉터리의 `CLAUDE.local.md` 와 `.claude/rules/`
    (공식 문서상 이것들도 그 디렉터리에서 실린다).
    """
    skipped = {root / ".venv", root / ".git", root / ".claude" / "worktrees"}
    found: list[str] = []
    for directory, subdirectories, files in os.walk(root):
        current = Path(directory)
        subdirectories[:] = sorted(
            name
            for name in subdirectories
            if name != "node_modules" and current / name not in skipped
        )
        if current == root:
            continue
        found.extend(
            (current / name).relative_to(root).as_posix()
            for name in NESTED_INSTRUCTION_FILES
            if name in files
        )
    return [
        f"{path}: 루트 밖의 지침 파일이다. 지침은 .claude/rules/*.md + paths 에 둔다(ADR 0004)."
        " next dev 가 만든 것이면 next.config 의 agentRules: false 를 본다(ADR 0021)"
        for path in sorted(found)
    ]


def main(root: Path = ROOT) -> int:
    """검사 열을 모아 돈다. `root` 는 CLI 첫 인자로도 받는다(임시 트리에서 빨강을 재는 테스트)."""
    problems = [
        f"{path.relative_to(root)}: paths 프론트매터 없음. 없으면 매 세션 실린다"
        for path in rules_without_paths(root)
    ]
    problems.extend(rules_with_dead_paths(root))
    problems.extend(hooks_with_relative_paths(root))
    problems.extend(claude_md_problems(root))
    problems.extend(imported_files_with_dead_paths(root))
    problems.extend(patched_skills_without_sentinel(root))
    problems.extend(skills_with_sentinel_not_listed(root))
    problems.extend(hooks_reading_text_stdin(root))
    problems.extend(nested_instruction_files(root))
    problems.extend(imports_outside_claude_md(root))
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT))
