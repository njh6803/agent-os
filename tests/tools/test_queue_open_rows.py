"""tools/queue_open_rows.py 검증. 행 모양은 `.scratch/retro-queue.md`의 실제 행을 줄여 옮겼다."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from tools.queue_open_rows import QUEUE, Row, by_target, main, paths_in, read_rows, render

ROOT = Path(__file__).resolve().parents[2]

HEAD = "| # | 무엇 | 어디로 | 승인 |\n|---|---|---|---|\n"


def queue(*rows: str) -> str:
    return HEAD + "".join(row + "\n" for row in rows)


def test_취소선으로_시작하는_행은_닫힌_행이라_세지_않는다() -> None:
    rows, broken = read_rows(
        queue(
            "| 1 | ~~닫힌 일~~ | `a.md` | 사용자 승인, 3회차 **닫힘** |",
            "| 2 | **열린 일** | `b.md` | 사용자 승인, 1회차 |",
            "| 3 | 열린 일 | `c.md` | 사용자 승인, 1회차 |",
            "| 4 | **~~굵게 시작한 닫힌 일~~** | `d.md` | 자체 승인, 1회차 |",
        )
    )
    assert [row.number for row in rows] == [2, 3]
    assert broken == []


def test_회차는_승인_칸에서_먼저_찾는다() -> None:
    rows, _ = read_rows(queue("| 5 | 일. 2회차의 근거 | `a.md` | 자체 승인, 1회차, 일지 |"))
    assert rows[0].rounds == 1
    assert rows[0].round_cell == "승인"


def test_승인_칸에_회차가_없으면_무엇_칸에서_찾는다() -> None:
    """대기열 167의 사건: 회차를 무엇 칸에 적은 옛 행(17)이 손으로 센 목록에서 빠졌다."""
    rows, _ = read_rows(
        queue(
            "| 17 | **회귀 시험이 없다.** **근거 추가**: 근거. **3회차**: 근거 | `x.ps1` | 승인 |"
        )
    )
    assert rows[0].rounds == 3
    assert rows[0].round_cell == "무엇"


def test_한_칸에_회차가_여럿이면_가장_큰_것을_쓴다() -> None:
    rows, _ = read_rows(queue("| 9 | 일. **2회차**: 근거. **3회차**: 근거 | `a.md` | 승인 |"))
    assert rows[0].rounds == 3


def test_어느_칸에도_회차가_없으면_모른다() -> None:
    rows, _ = read_rows(queue("| 4 | 일 | `a.md` | 일지 06 |"))
    assert rows[0].rounds is None
    assert "회차를 찾지 못한 행: 4" in render(rows, [])


def test_괄호_밖의_경로는_대상이고_괄호_안의_경로는_인용이다() -> None:
    """옛 스크래치 스크립트는 둘을 가르지 않아 `.claude/rules/tools.md`가 대상 아홉으로 나왔다."""
    targets, citations = paths_in(
        "`tools/hook_x.py`와 그 시험, `tools/hook_payloads.toml`. 어겨지면 막는 훅"
        "(`.claude/rules/tools.md`의 계기·막는 훅 가름)"
    )
    assert targets == ("tools/hook_x.py", "tools/hook_payloads.toml")
    assert citations == (".claude/rules/tools.md",)


def test_겹친_괄호_안도_인용이고_닫힌_뒤는_다시_대상이다() -> None:
    targets, citations = paths_in("(가름(`a/b.md`) 뒤 `c/d.md`) 그리고 `e/f.md`")
    assert targets == ("e/f.md",)
    assert citations == ("a/b.md", "c/d.md")


def test_코드_스팬_안의_괄호는_깊이를_바꾸지_않는다() -> None:
    targets, citations = paths_in("`f(x)` 를 고친다 `a/b.py`")
    assert targets == ("a/b.py",)
    assert citations == ()


def test_경로가_아닌_코드_스팬은_세지_않는다() -> None:
    """식별자, 옵션, 스킬 이름, 슬래시 명령, 자리표시가 든 URL 은 파일이 아니다."""
    targets, _ = paths_in(
        "`_PUSH_LONG`과 `--update`, `next-session`, `/security-review`, "
        "`repos/{owner}/{repo}/logs`, `${KEY}`, `uv.lock`, `CODING_STANDARDS.md`, `docs/adr/`"
    )
    assert targets == ("uv.lock", "CODING_STANDARDS.md", "docs/adr/")


def test_같은_행에서_대상이면서_인용인_경로는_대상으로만_센다() -> None:
    targets, citations = paths_in("`a/b.md` 한 줄(`a/b.md`의 절, `c/d.md`)")
    assert targets == ("a/b.md",)
    assert citations == ("c/d.md",)


def test_대상과_인용을_가르지_못하는_자리를_고정한다() -> None:
    """못 보는 것 둘. 본문의 인용은 대상으로, 괄호 안의 대상은 인용으로 센다(대기열 286·141)."""
    targets, _ = paths_in("판정 고침. 지우는 길이라 `.claude/rules/tools.md`의 반박 시험을 거친다")
    assert targets == (".claude/rules/tools.md",)
    targets, citations = paths_in("`a/rule.md`에 한 항목, 사용처(`tools/hook.py`)의 클라우드 길")
    assert targets == ("a/rule.md",)
    assert citations == ("tools/hook.py",)


def test_고칠_파일이_아닌_경로_모양도_대상으로_센다() -> None:
    """못 보는 것. git 이 만드는 잠금 파일(293), 훅이 지켜보는 경로(227), 부분 반영 행의 끝난
    몫(141)."""
    rows, _ = read_rows(
        queue(
            "| 293 | 일 | `tools/`의 훅. 커밋이 돌면(그 git 디렉터리의 `index.lock`) 알린다. "
            "`index.lock`을 잰다 | 2회차 |",
            "| 227 | 일 | 새 훅: `docs/adr/`에 더한 줄이면 알린다 | 1회차 |",
            "| 141 | 일 | `.claude/rules/tools.md`에 한 항목 | 1회차 **부분 반영: 더했다** |",
        )
    )
    assert [r.targets for r in rows] == [
        ("tools/", "index.lock"),
        ("docs/adr/",),
        (".claude/rules/tools.md",),
    ]


def test_사용자가_순서를_올린_행은_표지가_없어_세지_않는다() -> None:
    """못 보는 것. 결정표의 둘째 조건은 행에서 읽지 않는다."""
    out = render(read_rows(queue("| 5 | 일 | `a.md` | 사용자가 순서를 올렸다, 1회차 |"))[0], [])
    assert "회차 3 이상: (없음)" in out
    assert "5" not in out.split("\n", 1)[1]


def test_회차를_말로만_적은_행은_모른다고_센다() -> None:
    """못 보는 것. `<수>회차`만 읽는다."""
    rows, _ = read_rows(queue("| 6 | 일 | `a.md` | 사용자 승인, 세 번째 반복 |"))
    assert rows[0].rounds is None


def test_같은_파일을_다른_이름으로_적으면_다른_대상이다() -> None:
    """못 보는 것. 이름을 풀지 않아 짧은 이름과 긴 경로, 디렉터리와 그 아래 파일이 갈린다."""
    rows, _ = read_rows(
        queue(
            "| 1 | 일 | `operations.md` | 1회차 |",
            "| 2 | 일 | `docs/constitution/operations.md` | 1회차 |",
            "| 3 | 일 | `tools/` | 1회차 |",
            "| 4 | 일 | `tools/a.py` | 1회차 |",
        )
    )
    assert list(by_target(rows)) == [
        "docs/constitution/operations.md",
        "operations.md",
        "tools/",
        "tools/a.py",
    ]


def test_칸이_넷이_아닌_행은_빠뜨리지_않고_알린다() -> None:
    rows, broken = read_rows(
        queue("| 7 | 일 | `a.md` | 승인 | 덤 |", "| 8 | 일 \\| 이스케이프 | `b.md` | 1회차 |")
    )
    assert [row.number for row in rows] == [8]
    assert broken == [7]
    assert "칸이 넷이 아닌 행: 7" in render(rows, broken)


def row(number: int, rounds: int | None, *targets: str, cited: tuple[str, ...] = ()) -> Row:
    return Row(number, rounds, "승인" if rounds is not None else None, targets, cited)


def test_결정표의_두_조건을_모은다() -> None:
    """`next-session` 결정표의 chore 배치 조건: 회차 3 이상, 같은 대상 파일 셋 이상."""
    out = render(
        [
            row(167, 3, "tools/"),
            row(238, 7),
            row(68, 1, "CODING_STANDARDS.md"),
            row(71, 2, "CODING_STANDARDS.md"),
            row(107, 1, "CODING_STANDARDS.md"),
            row(64, 1, "web/a.mjs"),
            row(65, 1, "web/a.mjs"),
        ],
        [],
    )
    assert "열린 행 7개" in out
    assert "회차 3 이상: 238(7회차) 167(3회차)" in out
    assert "`CODING_STANDARDS.md`: 68 71 107" in out
    assert "web/a.mjs" not in out


def test_디렉터리와_패턴은_같은_대상_파일_조건에_세지_않고_따로_찍는다() -> None:
    """표준 축 리뷰: `tools/`가 여덟 행을 묶어 결정표의 셋째 조건이 늘 켜졌다."""
    out = render(
        [
            row(1, 1, "tools/", "a/*.toml"),
            row(2, 1, "tools/", "a/*.toml"),
            row(3, 1, "tools/", "a/*.toml"),
        ],
        [],
    )
    shared, rest = out.split("디렉터리·패턴 대상")
    assert "같은 대상 파일이 셋 이상: (없음)" in shared
    assert "`tools/`: 1 2 3" in rest
    assert "`a/*.toml`: 1 2 3" in rest


def test_괄호_안의_인용도_행_번호와_함께_기본_출력에_찍는다() -> None:
    """명세 축 리뷰: 인용으로 넘긴 진짜 대상(141)을 사람이 가르려면 기본 출력에 있어야 한다."""
    out = render([row(141, 1, "a/rule.md", cited=("tools/hook.py",)), row(2, 1)], [])
    assert "괄호 안의 인용으로 센 경로" in out
    assert "`tools/hook.py`: 141" in out


def test_조건에_드는_것이_없으면_없다고_적는다() -> None:
    out = render([row(1, 1, "a.md")], [])
    assert "회차 3 이상: (없음)" in out
    assert "같은 대상 파일이 셋 이상: (없음)" in out


def test_이_저장소의_대기열을_빠짐없이_읽는다() -> None:
    rows, broken = read_rows((ROOT / QUEUE).read_text(encoding="utf-8"))
    assert rows, "열린 행이 하나도 없다. 경로나 닫힘 판정이 틀렸을 수 있다"
    assert broken == []


def test_main을_실제로_불러_임시_대기열의_조건을_찍는다(tmp_path: Path) -> None:
    path = tmp_path / "queue.md"
    path.write_text(
        queue("| 9 | 일 | `a.md` | 3회차 |", "| 10 | 일 | `a.md` | 1회차 | 덤 |"),
        encoding="utf-8",
    )
    done = subprocess.run(
        [sys.executable, "tools/queue_open_rows.py", "--queue", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert done.returncode == 1, done.stderr
    assert "회차 3 이상: 9(3회차)" in done.stdout
    assert "칸이 넷이 아닌 행: 10" in done.stdout


def test_main은_없는_파일이면_2로_끝난다(tmp_path: Path) -> None:
    assert main(["--queue", str(tmp_path / "없다.md")]) == 2


def test_main은_인자가_틀리면_2로_끝난다() -> None:
    assert main(["--queue"]) == 2
    assert main(["--모름"]) == 2
    assert main(["--queue", "a.md", "--ref", "HEAD"]) == 2


def test_main은_대시로_시작하는_ref를_git에_넘기지_않는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """PR 직전 버그 리뷰: `--ref --output=<경로>` 는 git 이 옵션으로 읽어 파일을 쓰려 했다.

    git 이 그 경로를 열지 못해도 2로 끝나므로, git 까지 가지 않고 사용법 오류로 막혔는지를 본다.
    """
    written = tmp_path / "x"
    assert main(["--ref", f"--output={written}"]) == 2
    assert "쓰임:" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())


def test_main은_UTF8이_아닌_대기열이면_2로_끝난다(tmp_path: Path) -> None:
    """PR 직전 버그 리뷰: 해독 실패가 트레이스백의 1로 끝나 칸 오류와 섞였다."""
    path = tmp_path / "queue.md"
    path.write_bytes(queue("| 1 | 일 | `a.md` | 1회차 |").encode("cp949"))
    assert main(["--queue", str(path)]) == 2


def test_닫히지_않은_백틱_뒤의_경로는_세지_않는다() -> None:
    """못 보는 것."""
    targets, _ = paths_in("`a/b.md`와 `열림 `c/d.md`")
    assert targets == ("a/b.md",)


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "queue_open_rows.py"), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_ref로_커밋의_대기열을_읽고_모두_읽으면_0으로_끝난다(tmp_path: Path) -> None:
    """워크트리에서 병합한 뒤 `--ref origin/main`으로 다른 PR이 더한 행까지 센다(독스트링의
    쓰임)."""
    _git(tmp_path, "init", "-q")
    path = tmp_path / QUEUE
    path.parent.mkdir(parents=True)
    path.write_text(queue("| 1 | 일 | `a.md` | 3회차 |"), encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "q")
    path.write_text(queue("| 2 | 일 | `b.md` | 1회차 |"), encoding="utf-8")
    from_ref = _run("--ref", "HEAD", cwd=tmp_path)
    assert from_ref.returncode == 0, from_ref.stderr
    assert "회차 3 이상: 1(3회차)" in from_ref.stdout
    from_disk = _run(cwd=tmp_path)
    assert from_disk.returncode == 0, from_disk.stderr
    assert "회차 3 이상: (없음)" in from_disk.stdout
    missing = _run("--ref", "없는-커밋", cwd=tmp_path)
    assert missing.returncode == 2
    assert "대기열을 읽지 못했다" in missing.stderr
