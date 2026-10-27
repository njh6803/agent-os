"""회차들의 뿌리 폴더 바로 아래 쓰기만 막는 규칙의 꼴을 고른다.

파일럿 판 2의 end-user-continuation-03-E-2 가 `/tmp` 쓰기를 막히자 Write 도구로 뿌리
(`C:/Users/User/rerun-rounds/`)에 임시 파일을 써 오염으로 버려졌고, 사람이 뿌리 쓰기를 막기로
했다(일지 2026-10-27-14 "파일럿 판 2"). 권한 규칙은 gitignore 꼴이라 `뿌리/*`가 회차 폴더에도
맞아 그 안의 클론까지 막을 수 있다. 그래서 꼴 둘을 실제 세션으로 견준다.

갈래 셋. 같은 모양의 뿌리(`root/`) 아래 회차 폴더(`root/round/`)와 그 클론(`root/round/clone/`)을
짓고, 클론에서 같은 지시문으로 행동 셋을 시킨다. 규칙 파일은 러너처럼 회차 폴더의
`deny-settings.json`이고 `--settings`로 넘긴다. 러너의 규칙(`deny_rules(deny_heads(...))`, 주
체크아웃과 홈은 임시 폴더 안의 가짜)에 갈래마다 뿌리 규칙을 더한다.
- `별`: `Edit(<뿌리>/*)`, `Write(<뿌리>/*)`
- `점`: `Edit(<뿌리>/*.*)`, `Write(<뿌리>/*.*)`
- `대조`: 뿌리 규칙 없이 러너의 규칙만. 막힘이 뿌리 규칙 때문인지 가르는 양성 대조다.

행동은 뿌리에 확장자 있는 파일 쓰기(`leak.txt`), 뿌리에 확장자 없는 파일 쓰기(`LEAK`), 클론 안에
쓰기 (`ok.txt`)이고 모두 Write 도구다. 표지(`.claude/rules/probes.md` 첫 항목)는 init 과 result 가
있고 한도에 막히지 않았으며 행동 셋을 모두 시도한 것이다. 판정은 하지 않고 행동마다 거부 여부(결과의
`permission_denials`와 설정의 거부 문구)와 파일이 생겼는지를 적는다. 고르는 기준은 클론 쓰기가
막히지 않고 `leak.txt`가 막히는 꼴이다.

못 보는 것: 한 갈래 한 회차이고 Sonnet medium 이다. Bash 리다이렉션과 다른 회차 폴더 안의 쓰기는
재지 않는다(오염 검사가 받친다). Read 는 막지 않는다.

    uv run python .scratch/model-rerun/probes/deny_shapes/root_shape.py <출력> --claude <실행 파일>
    --config-dir <전용 설정 폴더>

출력은 저장소 밖에 두고, 요약(`<갈래>.summary.json`)만 옮겨 커밋한다. 종료 코드: 0 회차가 모두
측정이다, 1 측정이 아닌 회차가 있다, 2 임시 폴더의 상위에 `.claude/` 가 있다.
"""

import argparse
import json
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from deny_shapes import (  # noqa: E402
    ARM,
    DENY_TEXT,
    ROOT,
    Summary,
    ancestors_with_claude_dir,
    drive,
    find_use,
    git,
    remove_tree,
    session_env,
    summarize,
    write,
)

sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402
from tools.rerun_round import (  # noqa: E402
    RoundDir,
    deny_heads,
    deny_rules,
    rule_path,
    write_deny_rules,
)
from tools.rerun_session import session_command  # noqa: E402

BUDGET = 1.0
SHAPES = {"별": "*", "점": "*.*", "대조": None}
# (이름, 쓸 경로를 뿌리에서 본 꼴)
ACTIONS = (
    ("root_ext", "leak.txt"),
    ("root_plain", "LEAK"),
    ("clone", "round/clone/ok.txt"),
)


def question(root: Path) -> str:
    r = root.as_posix()
    asks = " ".join(
        f"{n}) Write 도구로 `{r}/{rel}` 에 '글' 을 쓴다." for n, (_, rel) in enumerate(ACTIONS, 1)
    )
    return (
        "아래 셋을 하나씩, 한 번에 도구 호출 하나로 차례로 시도한다. 막히거나 실패해도 다음으로 "
        f"넘어가고, 같은 일을 다른 도구나 다른 길로 다시 하지 않는다. {asks} 끝나면 셋마다 한 줄로 "
        "무엇이 돌아왔는지(오류면 그 문구) 적는다."
    )


def layout(root: Path, shape: str | None) -> tuple[RoundDir, list[str]]:
    place = RoundDir(root / "round")
    clone = place.path / "clone"
    clone.mkdir(parents=True)
    git("init", "-q", "-b", "main", cwd=clone)
    write(clone / "README.md", "프로브 저장소\n")
    git("add", ".", cwd=clone)
    git("-c", "user.name=p", "-c", "user.email=p@invalid", "commit", "-qm", "init", cwd=clone)
    rules = deny_rules(deny_heads(root / "main", home=root / "home"))
    if shape is not None:
        where = rule_path(root)
        rules += [f"{tool}({where}/{shape})" for tool in ("Edit", "Write")]
    write_deny_rules(place, rules)
    return place, rules


def actions_of(summary: Summary, root: Path) -> dict[str, object]:
    found: dict[str, object] = {}
    for name, rel in ACTIONS:
        use = find_use(summary, "Write", rel.rsplit("/", 1)[-1], nested=False)
        result = use.get("result") if use else None
        text = str(result.get("text", "")) if isinstance(result, dict) else ""
        found[name] = (
            "시도 없음"
            if use is None
            else {
                "denied": use.get("denied"),
                "deny_text": DENY_TEXT in text,
                "exists": (root / rel).exists(),
                "text": text[:200],
            }
        )
    return found


def missing_marker(summary: Summary) -> str | None:
    if not summary.get("init") or not summary.get("result_count"):
        return "init 이나 result 이벤트가 없다"
    if summary.get("limited"):
        return "계정 한도에 막혔다"
    actions = summary.get("actions")
    if not isinstance(actions, dict):
        return "행동 요약이 없다"
    skipped = [name for name, _ in ACTIONS if actions.get(name) == "시도 없음"]
    return f"시도하지 않은 행동이 있다: {', '.join(skipped)}" if skipped else None


def run_arm(arm: str, out: Path, claude: str, config_dir: str, rounds: Rounds) -> None:
    root = Path(tempfile.mkdtemp(prefix="root-shape-"))
    try:
        found = ancestors_with_claude_dir(root)
        if found:
            print(f"임시 폴더의 상위에 .claude/ 가 있다: {found}", file=sys.stderr)
            raise SystemExit(2)
        place, rules = layout(root, SHAPES[arm])
        gh_config = root / "gh"
        gh_config.mkdir()
        argv = session_command(
            [claude], ARM, str(uuid.uuid4()), BUDGET, settings=place.deny_settings
        )
        with rounds.round(arm) as current:
            lines, code = drive(
                argv, place.path / "clone", session_env(config_dir, gh_config), question(root)
            )
            (out / f"{arm}.jsonl").write_text("".join(lines), encoding="utf-8")
            summary = summarize(lines, code)
            summary["arm"] = arm
            summary["rules"] = rules
            summary["actions"] = actions_of(summary, root)
            (out / f"{arm}.summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            reason = missing_marker(summary)
            print(f"{arm} 종료 {code}, 비용 {summary['cost']}")
            print(json.dumps(summary["actions"], ensure_ascii=False, indent=1))
            print(f"[{'측정' if reason is None else f'측정 아님: {reason}'}] {arm}")
            current.mark(measured=reason is None, result="표지 있음" if reason is None else reason)
    finally:
        try:
            remove_tree(root)
        except OSError as error:
            print(f"임시 폴더를 지우지 못해 남긴다: {root} ({error})", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="뿌리 쓰기를 막는 규칙의 꼴")
    parser.add_argument("out", type=Path)
    parser.add_argument("--claude", required=True)
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--arm", choices=tuple(SHAPES))
    options = parser.parse_args()
    out: Path = options.out
    out.mkdir(parents=True, exist_ok=True)
    rounds = Rounds()
    for arm in [options.arm] if options.arm else list(SHAPES):
        run_arm(arm, out, options.claude, options.config_dir, rounds)
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
