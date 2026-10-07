"""바꾼 규칙·스킬이 새 `claude -p` 세션에 실리는지 카나리아 질문으로 잰다.

절차의 원천은 `docs/constitution/operations.md` 환경 규약 상세의 카나리아 항목이다. 세션마다
스크래치에 카나리아 스크립트를 새로 짓다가 커밋되지 않아 리뷰가 다시 잴 수 없었고(대기열 129),
규칙 명령에 둔 `.claude/` 읽기 거부가 `paths` 규칙의 로드까지 막아 실험군과 대조군이 모두
"없음"인 채로 확인이 조용히 비었다(대기열 127, 일지 2026-10-06-15). 워크트리 세션에서는 회차를
반복문으로 묶은 명령을 앱의 가드가 거부했다(대기열 120). 그래서 명세 파일 하나를 받아 모든 회차를
이 도구 안에서 돌리고, 셸에는 단순 명령 하나만 남긴다.

사용: uv run python tools/canary.py <명세.toml> <출력 디렉터리>

명세는 TOML 이다. 체크아웃은 이 도구를 부른 폴더 기준이다.

    kind = "rule"                    # rule 이면 --tools Read, skill 이면 --tools Skill
    model = "sonnet"                 # 선택. 기본 sonnet
    question = '''
    Read 도구로 `{target}` 하나만 통째로 읽어라. ...없으면 "없음"이라고만 답하라.
    '''                              # stdin 으로 간다. rule 이면 {target} 이 갈래의 대상으로 바뀐다
    expect = ["식별자는 영문"]        # 카나리아. 바뀐 본문에만 있는 글. 질문에 있으면 안 된다
    # skill = "tidy-checkouts"       skill 이면 선택. 실험군 회차마다 이 스킬을 Skill 로 불러야 한다

    [[arm]]
    name = "실험군"                  # 출력 파일 이름의 머리
    role = "experiment"              # experiment, control
    checkout = "."                   # 선택. 기본 "."
    target = "tools/hook_env_read.py"   # rule 이면 반드시, skill 이면 쓰지 않는다
    # runs = 3                       선택. 기본은 실험군 3, 대조군 1

    [[arm]]
    name = "대조군"
    role = "control"
    target = "README.md"             # 규칙의 paths 밖 파일

판정. 회차마다 아래가 모두 맞아야 통과다.
- init 의 `tools` 가 그 도구 하나이고 `mcp_servers` 가 비었다.
- `result` 가 성공이고 `claude` 가 0 으로 끝났다.
- rule: Read 를 한 번 이상 불렀고 모두 `<체크아웃>/<target>` 이다. 다른 파일(특히 규칙 파일)을
  읽었으면 답이 실린 규칙이 아니라 그 파일에서 왔을 수 있다.
- skill: 실린 스킬 본문의 자리(`Base directory for this skill:` 줄)는 모두 `<체크아웃>/.claude/
  skills/` 바로 아래다. 워크트리는 주 체크아웃 안에 있어 접두사가 아니라 자리 전체로 견준다.
  `skill` 을 주었으면 실험군은 그 스킬을 Skill 로 불렀고 그 이름의 자리 줄이 있다. 줄이 없으면
  자리 판정이 비므로 실패다. 대조군에는 요구하지 않는다. 새 스킬은 옛 사본에 없다.
- 실험군: 답이 "없음"이 아니고 카나리아를 모두 담았다. "없음"은 바뀐 본문이 실리지 않았다는 뜻이고,
  대조군과 같은 답이면 확인이 빈 것이지 통과가 아니다.
- 대조군: 답에 카나리아가 하나도 없다. "없음"이든 옛 줄이든 된다. 카나리아가 있으면 질문이 답을
  흘렸거나 대조군이 새 사본이다.
카나리아 대조는 백틱과 `*` 를 걷고 공백을 하나로 모은 뒤의 부분 문자열이다. 돌리기 전에 질문과
rule 갈래의 대상 파일에 카나리아가 있는지, 갈래의 체크아웃이 있는지 보고, 어긋나면 돌리지 않는다.

모델이 부르지 못하는 스킬(`disable-model-invocation: true`)은 질문 머리에 슬래시 명령으로 넣고
`skill` 을 주지 않는다. 그 본문은 프롬프트에 펼쳐져 Skill 호출도 자리 줄도 남기지 않는다
(claude 2.1.291 에서 `/grill-me` 로 손으로 봤다, 일지 2026-10-07-02).

못 보는 것.
- 규칙이 실렸다는 흔적은 stream-json 에 없다(claude 2.1.291 에서 손으로 봤다, 일지
  2026-10-07-02). 규칙은 답의 카나리아와 Read 호출로만 본다.
- 슬래시 명령으로 넣은 스킬이 어느 체크아웃의 사본인지. 세션을 시작한 체크아웃의 사본이 실린다는
  `operations.md` 항목에 기댄다.
- skill 의 답이 스킬 본문이 아니라 목록의 설명에서 왔는지는 `skill` 로 호출을 요구할 때만 가른다.
  설명에도 있는 낱말을 카나리아로 고르면 가르지 못한다.
- 질문이 카나리아를 바꿔 말해 드러냈는지. 글자 그대로 든 것만 명세 오류로 잡고, 나머지는 대조군이
  잡는다(대조군 답에 카나리아가 있으면 실패).
- Read 의 결과가 오류였는지. 돌리기 전에 대상 파일이 있는지만 본다.

종료 코드: 0 모두 통과, 1 실패한 회차가 있다, 2 명세나 인자가 틀렸다(아무것도 돌리지 않았다),
3 `claude` 를 띄우지 못했다(원본을 남기지 않았다).
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

type Kind = Literal["rule", "skill"]
type Role = Literal["experiment", "control"]

_TOOLS: dict[Kind, str] = {"rule": "Read", "skill": "Skill"}
_DEFAULT_RUNS: dict[Role, int] = {"experiment": 3, "control": 1}
_ROLE_NAMES: dict[Role, str] = {"experiment": "실험군", "control": "대조군"}
_SKILL_DIR = re.compile(r"^Base directory for this skill:\s*(.+?)\s*$", re.MULTILINE)
_NONE_NOISE = re.compile(r"[\s`*_\"'“”‘’.。!]")
_ANSWER_WIDTH = 160


class SpecError(Exception):
    """명세를 읽지 못했거나 틀렸다. 아무 회차도 돌리기 전에 난다."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Arm(_Model):
    name: str = Field(pattern=r"^[^/\\:]+$")
    role: Role
    checkout: str = "."
    target: str | None = None
    runs: int | None = Field(default=None, ge=1)

    @property
    def times(self) -> int:
        return self.runs if self.runs is not None else _DEFAULT_RUNS[self.role]


class Spec(_Model):
    kind: Kind
    model: str = "sonnet"
    question: str = Field(min_length=1)
    expect: list[str] = Field(min_length=1)
    skill: str | None = None
    arm: list[Arm] = Field(min_length=1)

    @model_validator(mode="after")
    def _consistent(self) -> Spec:
        problems: list[str] = []
        if any(not canary.strip() for canary in self.expect):
            problems.append("expect 에 빈 카나리아가 있다")
        shown = [c for c in self.expect if c.strip() and _flat(c) in _flat(self.question)]
        if shown:
            problems.append(f"question 이 카나리아를 드러낸다: {', '.join(shown)}")
        roles = {arm.role for arm in self.arm}
        if roles != {"experiment", "control"}:
            problems.append("실험군과 대조군이 하나 이상씩 있어야 한다")
        names = [arm.name for arm in self.arm]
        repeated = sorted({name for name in names if names.count(name) > 1})
        if repeated:
            problems.append(f"갈래 이름이 겹친다: {', '.join(repeated)}")
        if self.kind == "rule":
            if "{target}" not in self.question:
                problems.append("rule 의 question 에 {target} 자리가 없다. 읽을 파일을 알려야 한다")
            if self.skill is not None:
                problems.append("skill 은 kind 가 skill 일 때만 쓴다")
            missing = [arm.name for arm in self.arm if arm.target is None]
            if missing:
                problems.append(f"rule 갈래에 target 이 없다: {', '.join(missing)}")
        else:
            extra = [arm.name for arm in self.arm if arm.target is not None]
            if extra:
                problems.append(f"skill 갈래는 target 을 쓰지 않는다: {', '.join(extra)}")
        if problems:
            raise ValueError("; ".join(problems))
        return self


@dataclass(frozen=True)
class Facts:
    """회차 하나의 stream-json 에서 뽑은 것. init 이 없으면 `tools` 가 None 이다."""

    tools: tuple[str, ...] | None
    servers: tuple[str, ...]
    reads: tuple[str, ...]
    skills: tuple[str, ...]
    skill_dirs: tuple[str, ...]
    answer: str | None
    error: str | None


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    stdout: str
    stderr: str


type Runner = Callable[[Sequence[str], Path, str], RunResult]


class _Block(TypedDict, total=False):
    type: str
    name: str
    input: dict[str, object]
    text: str


class _Message(TypedDict, total=False):
    content: list[_Block] | str


class _Event(TypedDict, total=False):
    type: str
    subtype: str
    tools: list[str]
    mcp_servers: list[dict[str, object] | str]
    message: _Message
    result: str
    is_error: bool


def load_spec(text: str) -> Spec:
    try:
        return Spec.model_validate(tomllib.loads(text))
    except (tomllib.TOMLDecodeError, ValidationError) as error:
        raise SpecError(str(error)) from error


def read_spec(path: Path) -> Spec:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SpecError(f"{path} 를 읽지 못했다: {error}") from error
    return load_spec(text)


def command(spec: Spec) -> list[str]:
    """질문은 넣지 않는다. `--tools` 는 가변 인자라 뒤에 둔 질문까지 도구 이름으로 삼킨다."""
    return [
        "claude",
        "-p",
        "--setting-sources",
        "project,local",
        "--strict-mcp-config",
        "--model",
        spec.model,
        "--tools",
        _TOOLS[spec.kind],
        "--output-format",
        "stream-json",
        "--verbose",
    ]


def prompt_for(spec: Spec, arm: Arm) -> str:
    if spec.kind == "rule" and arm.target is not None:
        return spec.question.replace("{target}", arm.target)
    return spec.question


def _event(line: str) -> _Event | None:
    if not line.lstrip().startswith("{"):
        return None
    try:
        event: _Event = json.loads(line)
    except ValueError:  # claude 가 중간에 끝나면 마지막 줄이 잘린다
        return None
    return event


def _server_name(server: dict[str, object] | str) -> str:
    if isinstance(server, str):
        return server
    name = server.get("name")
    return name if isinstance(name, str) else repr(server)


def _blocks(event: _Event) -> list[_Block]:
    content = event.get("message", {}).get("content", [])
    return [] if isinstance(content, str) else content


def read_facts(lines: Iterable[str]) -> Facts:
    tools: tuple[str, ...] | None = None
    servers: tuple[str, ...] = ()
    reads: list[str] = []
    skills: list[str] = []
    skill_dirs: list[str] = []
    answer: str | None = None
    error: str | None = None
    for line in lines:
        event = _event(line)
        if event is None:
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            tools = tuple(event.get("tools", []))
            servers = tuple(_server_name(server) for server in event.get("mcp_servers", []))
        elif kind == "assistant":
            for block in _blocks(event):
                if block.get("type") != "tool_use":
                    continue
                arguments = block.get("input", {})
                if block.get("name") == "Read":
                    path = arguments.get("file_path")
                    reads.append(path if isinstance(path, str) else repr(arguments))
                elif block.get("name") == "Skill":
                    name = arguments.get("skill")
                    skills.append(name if isinstance(name, str) else repr(arguments))
        elif kind == "user":
            for block in _blocks(event):
                if block.get("type") == "text":
                    skill_dirs.extend(_SKILL_DIR.findall(block.get("text", "")))
        elif kind == "result":
            subtype = event.get("subtype", "")
            text = event.get("result", "")
            if subtype == "success" and not event.get("is_error", False):
                answer, error = text, None
            else:
                answer, error = None, f"{subtype or '결과 없음'}: {text}"
    return Facts(tools, servers, tuple(reads), tuple(skills), tuple(skill_dirs), answer, error)


def _flat(text: str) -> str:
    return " ".join(text.replace("`", "").replace("*", "").split())


def _says_none(answer: str) -> bool:
    return _NONE_NOISE.sub("", answer) == "없음"


def _same_place(path: str, expected: Path, checkout: Path) -> bool:
    seen = Path(path) if Path(path).is_absolute() else checkout / path
    return os.path.normcase(os.path.normpath(seen)) == os.path.normcase(os.path.normpath(expected))


def judge(spec: Spec, arm: Arm, facts: Facts, checkout: Path) -> list[str]:
    """통과면 빈 목록, 아니면 실패의 이유들."""
    reasons: list[str] = []
    tool = _TOOLS[spec.kind]
    if facts.tools is None:
        reasons.append("init 이벤트가 없다. 세션이 시작되지 않았다")
    elif facts.tools != (tool,):
        reasons.append(f"도구가 {tool} 하나가 아니다: {', '.join(facts.tools) or '없음'}")
    if facts.servers:
        reasons.append(f"MCP 서버가 실렸다: {', '.join(facts.servers)}")
    if spec.kind == "rule" and arm.target is not None:
        target = checkout / arm.target
        if not facts.reads:
            reasons.append("Read 를 부르지 않았다. 규칙이 실릴 계기가 없다")
        outside = [path for path in facts.reads if not _same_place(path, target, checkout)]
        if outside:
            reasons.append(f"{arm.target} 밖을 읽었다: {', '.join(outside)}")
    if spec.kind == "skill":
        home = checkout / ".claude" / "skills"
        foreign = [
            folder
            for folder in facts.skill_dirs
            if not _same_place(str(Path(folder).parent), home, checkout)
        ]
        if foreign:
            reasons.append(f"{checkout} 가 아닌 사본이 실렸다: {', '.join(foreign)}")
        if spec.skill is not None and arm.role == "experiment":
            if spec.skill not in facts.skills:
                reasons.append(f"스킬 {spec.skill} 을 부르지 않았다")
            if not any(Path(folder).name == spec.skill for folder in facts.skill_dirs):
                reasons.append(f"스킬 {spec.skill} 이 실린 자리 줄이 없다. 자리 판정이 빈다")
    if facts.answer is None:
        reasons.append(f"세션이 답을 내지 못했다: {facts.error or '결과 이벤트가 없다'}")
        return reasons
    answer = _flat(facts.answer)
    canaries = [_flat(canary) for canary in spec.expect]
    if arm.role == "experiment":
        if _says_none(facts.answer):
            reasons.append('실험군이 "없음"이라 답했다. 바뀐 본문이 실리지 않았다')
        else:
            missing = [canary for canary in canaries if canary not in answer]
            if missing:
                reasons.append(f"실험군 답에 카나리아가 없다: {', '.join(missing)}")
    else:
        present = [canary for canary in canaries if canary in answer]
        if present:
            reasons.append(
                f"대조군 답에 카나리아가 있다(질문이 흘렸거나 새 사본이다): {', '.join(present)}"
            )
    return reasons


def target_problems(spec: Spec, arm: Arm, checkout: Path) -> list[str]:
    """rule 갈래의 대상 파일이 없거나 카나리아를 담았으면 그 문제들. 답이 파일에서 올 수 있다."""
    if arm.target is None:
        return []
    target = checkout / arm.target
    try:
        text = _flat(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        return [f"{arm.name}: 대상 {target} 이 없다: {error}"]
    found = [canary for canary in spec.expect if _flat(canary) in text]
    if found:
        return [f"{arm.name}: 대상 {arm.target} 에 카나리아가 있다: {', '.join(found)}"]
    return []


def run_claude(args: Sequence[str], cwd: Path, stdin: str) -> RunResult:
    executable = shutil.which(args[0]) or args[0]
    completed = subprocess.run(
        [executable, *args[1:]],
        cwd=cwd,
        input=stdin.encode("utf-8"),
        capture_output=True,
        check=False,
    )
    return RunResult(
        completed.returncode,
        completed.stdout.decode("utf-8", "replace"),
        completed.stderr.decode("utf-8", "replace"),
    )


@dataclass(frozen=True)
class _Job:
    arm: Arm
    index: int
    checkout: Path


def _summary(facts: Facts) -> str:
    answer = " ".join((facts.answer or facts.error or "").split())
    if len(answer) > _ANSWER_WIDTH:
        answer = answer[:_ANSWER_WIDTH] + "…"
    reads = ", ".join(Path(path).name for path in facts.reads) or "-"
    skills = ", ".join(facts.skills) or "-"
    tools = ", ".join(facts.tools) if facts.tools is not None else "init 없음"
    return f"도구 {tools} · 서버 {len(facts.servers)} · 읽음 {reads} · 스킬 {skills} · 답: {answer}"


def main(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    runner: Runner = run_claude,
    out: Callable[[str], None] = print,
) -> int:
    if len(argv) != 2:
        out(__doc__ or "")
        return 2
    base = cwd if cwd is not None else Path.cwd()
    try:
        spec = read_spec(Path(argv[0]))
    except SpecError as error:
        out(f"명세 오류(아무것도 돌리지 않았다): {error}")
        return 2
    output = Path(argv[1])
    places = {arm.name: Path(os.path.abspath(base / arm.checkout)) for arm in spec.arm}
    jobs = [
        _Job(arm, index, places[arm.name]) for arm in spec.arm for index in range(1, arm.times + 1)
    ]
    problems = [
        f"{arm.name}: 체크아웃 {places[arm.name]} 이 없다"
        for arm in spec.arm
        if not places[arm.name].is_dir()
    ]
    problems += [
        problem for arm in spec.arm for problem in target_problems(spec, arm, places[arm.name])
    ]
    if problems:
        out("명세 오류(아무것도 돌리지 않았다):")
        for problem in problems:
            out(f"  {problem}")
        return 2
    output.mkdir(parents=True, exist_ok=True)
    args = command(spec)

    def run(job: _Job) -> RunResult:
        return runner(args, job.checkout, prompt_for(spec, job.arm))

    try:
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            results = list(pool.map(run, jobs))
    except OSError as error:
        out(f"claude 를 띄우지 못했다(원본을 남기지 않았다): {error}")
        return 3
    failed = 0
    for job, result in zip(jobs, results, strict=True):
        stem = f"{job.arm.name}-{job.index}"
        (output / f"{stem}.jsonl").write_text(result.stdout, encoding="utf-8")
        (output / f"{stem}.err").write_text(result.stderr, encoding="utf-8")
        facts = read_facts(result.stdout.splitlines())
        reasons = judge(spec, job.arm, facts, job.checkout)
        if result.exit_code != 0:
            last = (result.stderr.strip().splitlines() or ["stderr 없음"])[-1]
            reasons.append(f"claude 가 종료 코드 {result.exit_code} 로 끝났다: {last}")
        label = f"{job.arm.name}({_ROLE_NAMES[job.arm.role]}) {job.index}/{job.arm.times}"
        out(f"[{'실패' if reasons else '통과'}] {label}")
        for reason in reasons:
            out(f"  - {reason}")
        out(f"  {_summary(facts)}")
        failed += bool(reasons)
    out(f"통과 {len(jobs) - failed} · 실패 {failed}. 원본은 {output}")
    return 1 if failed else 0


if __name__ == "__main__":
    # 윈도우의 파이프는 PYTHONUTF8 이 없으면 cp949 다. 한글 출력이 깨지지 않게 고정한다.
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
