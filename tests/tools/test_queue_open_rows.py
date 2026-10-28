"""tools/queue_open_rows.py 검증. 행 모양은 `.scratch/retro-queue.md`의 실제 행을 줄여 옮겼다."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from tools.queue_open_rows import (
    APPROVAL_HEAD,
    APPROVAL_TAIL,
    HEAD_CHARS,
    QUEUE,
    Hit,
    HitState,
    Row,
    by_target,
    main,
    paths_in,
    read_rows,
    render,
    render_hits,
    search,
)

ROOT = Path(__file__).resolve().parents[2]
TODAY = date(2026, 10, 19)

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
    approval = "사용자가 순서를 올렸다, 1회차, 2026-10-18"
    out = render(read_rows(queue(f"| 5 | 일 | `a.md` | {approval} |"))[0], [], TODAY)
    assert "회차 3 이상: (없음)" in out
    assert "만료할 행(승인 칸의 가장 늦은 날짜가 2026-10-05 전): (없음)" in out
    assert "날짜를 찾지 못한 행" not in out


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


def row(
    number: int,
    rounds: int | None,
    *targets: str,
    cited: tuple[str, ...] = (),
    last: date | None = None,
    human: bool = False,
) -> Row:
    cell = "승인" if rounds is not None else None
    return Row(number, rounds, cell, targets, cited, last, human)


def test_승인_칸의_가장_늦은_날짜와_사람_몫을_읽는다() -> None:
    rows, _ = read_rows(
        queue(
            "| 1 | 일 | `a.md` | 자체 승인 2026-10-01, 2회차, "
            "일지 2026-10-03-02-journal-number-uniqueness.md·2026-10-02-04 |",
            "| 2 | 일 | 사람 몫: 주 체크아웃에서 정리한다 | 사용자 승인 2026-10-13, 11회차 |",
            "| 3 | 일 | `b.md` | 승인, 1회차 |",
        )
    )
    assert [(r.number, r.last, r.human) for r in rows] == [
        (1, date(2026, 10, 3), False),
        (2, date(2026, 10, 13), True),
        (3, None, False),
    ]


def test_사람_몫은_어디로_칸이_사람_몫과_쌍점으로_시작할_때만이고_굵게_써도_읽는다() -> None:
    """셀프 리뷰: `사람 몫`으로만 견주자 `사람 몫이 아닌 …`이 사람 몫이 되고 `**사람 몫:**`은
    빠졌다."""
    rows, _ = read_rows(
        queue(
            "| 1 | 일 | **사람 몫:** 정리한다 | 1회차 |",
            "| 2 | 일 | 사람 몫이 아닌 `tools/y.py` | 1회차 |",
        )
    )
    assert [(r.number, r.human) for r in rows] == [(1, True), (2, False)]


def test_회차_3_이상인_행은_반영할_때까지_만료하지_않는다() -> None:
    """셀프 리뷰: chore 를 기능 뒤에만 여니 문턱을 넘은 행이 반영을 기다리다 14일을 넘겨 닫힐 수
    있었다."""
    out = render([row(1, 3, last=date(2026, 9, 1)), row(2, 2, last=date(2026, 9, 1))], [], TODAY)
    assert "회차 3 이상: 1(3회차)" in out
    assert "만료할 행(승인 칸의 가장 늦은 날짜가 2026-10-05 전): 2(2026-09-01)" in out.splitlines()


def test_사람_몫_행은_회차_3_이상에_넣지_않고_따로_적는다() -> None:
    """대기열 238: 사람이 할 일을 세션마다 다시 보며 회차가 11까지 쌓여 chore 계기가 됐다."""
    out = render([row(238, 11, human=True), row(306, 9)], [], TODAY)
    assert "회차 3 이상: 306(9회차)" in out
    assert "사람 몫(회차를 chore 계기로 세지 않고 만료하지 않는다): 238" in out


def test_승인_칸의_가장_늦은_날짜가_14일_넘게_지난_행을_만료로_적는다() -> None:
    out = render(
        [
            row(1, 1, last=date(2026, 10, 4)),
            row(2, 2, last=date(2026, 10, 5)),
            row(3, 1, last=date(2026, 10, 18)),
            row(4, 1, last=date(2026, 9, 1), human=True),
        ],
        [],
        TODAY,
    )
    assert "만료할 행(승인 칸의 가장 늦은 날짜가 2026-10-05 전): 1(2026-10-04)" in out.splitlines()


def test_없는_날짜는_넘고_남은_날짜에서_가장_늦은_것을_고른다() -> None:
    rows, _ = read_rows(queue("| 1 | 일 | `a.md` | 자체 승인 2026-10-01, 1회차, 반영 2026-02-30 |"))
    assert rows[0].last == date(2026, 10, 1)


def test_만료할_행이_없으면_없다고_적고_날짜가_없는_행은_따로_적는다() -> None:
    out = render([row(1, 1, last=date(2026, 10, 18)), row(4, None)], [], TODAY)
    assert "만료할 행(승인 칸의 가장 늦은 날짜가 2026-10-05 전): (없음)" in out
    assert "날짜를 찾지 못한 행: 4" in out


def test_날짜가_없어도_회차_3_이상인_행은_날짜를_찾지_못한_행에_적지_않는다() -> None:
    """PR 직전 버그 축: 만료하지 않는 행까지 적어, retro 가 그 행의 날짜를 git 에서 찾게 했다."""
    out = render([row(1, 3), row(4, 1)], [], TODAY)
    assert "날짜를 찾지 못한 행: 4" in out.splitlines()


def test_못_보는_것_회차가_아닌_날짜도_가장_늦은_날짜로_센다() -> None:
    """부분 반영을 적은 날이 늦으면 새 회차가 없어도 만료하지 않는다."""
    approval = "자체 승인 2026-09-21, 1회차, 일지 2026-09-21-01. 반영 2026-10-18"
    rows, _ = read_rows(queue(f"| 1 | 일 | `a.md` | {approval} |"))
    out = render(rows, [], TODAY)
    assert "만료할 행(승인 칸의 가장 늦은 날짜가 2026-10-05 전): (없음)" in out


def test_못_보는_것_무엇과_어디로_칸의_날짜는_보지_않는다() -> None:
    rows, _ = read_rows(queue("| 1 | 2026-10-18 에 난 일 | `a.md`(2026-10-18) | 1회차 |"))
    assert rows[0].last is None


def test_결정표의_조건을_모은다() -> None:
    """`next-session` 결정표의 chore 배치 조건은 회차 3 이상이다. 같은 대상 파일 셋 이상은
    계기가 아니라 배치를 고른 뒤 함께 묶을 행이다(ADR 0036)."""
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
    assert "같은 대상 파일이 3개 행 이상: (없음)" in shared
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
    assert "같은 대상 파일이 3개 행 이상: (없음)" in out


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


def test_main은_today를_기준일로_만료할_행을_찍는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "queue.md"
    path.write_text(queue("| 9 | 일 | `a.md` | 자체 승인 2026-09-01, 1회차 |"), encoding="utf-8")
    assert main(["--queue", str(path), "--today", "2026-09-15"]) == 0
    assert "만료할 행(승인 칸의 가장 늦은 날짜가 2026-09-01 전): (없음)" in capsys.readouterr().out
    assert main(["--queue", str(path), "--today", "2026-09-16"]) == 0
    assert "2026-09-02 전): 9(2026-09-01)" in capsys.readouterr().out
    assert main(["--queue", str(path), "--today", "어제"]) == 2


def test_main은_없는_파일이면_2로_끝난다(tmp_path: Path) -> None:
    assert main(["--queue", str(tmp_path / "없다.md")]) == 2


def test_main은_rows를_주면_행마다의_줄을_기본_출력_뒤에_찍는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "queue.md"
    path.write_text(queue("| 9 | 일 | `a/b.md`(`c/d.md`) | 3회차 |"), encoding="utf-8")
    assert main(["--queue", str(path)]) == 0
    assert "행마다:" not in capsys.readouterr().out
    assert main(["--queue", str(path), "--rows"]) == 0
    out = capsys.readouterr().out
    assert out.index("열린 행 1개") < out.index("행마다:")
    assert "  9 3회차(승인) 대상: a/b.md / 인용: c/d.md" in out


def test_main은_인자가_틀리면_쓰임을_내고_2로_끝난다(capsys: pytest.CaptureFixture[str]) -> None:
    for argv in (["--queue"], ["--모름"], ["--queue", "a.md", "--ref", "HEAD"]):
        assert main(argv) == 2
        assert "쓰임: uv run python tools/queue_open_rows.py" in capsys.readouterr().err


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


def find(text: str, *patterns: str) -> list[Hit]:
    return search(text, [re.compile(pattern) for pattern in patterns])


def test_search는_닫힌_행까지_행_원문에_맞춰_줄_번호와_함께_찾는다() -> None:
    """대기열 425: retro 5단계의 행 찾기는 닫힌 행도 찾아야 4단계의 회차대로 잇는다."""
    text = queue(
        "| 1 | ~~**닫힌 일.** 뒤~~ | `tools/a.py` | 자체 승인 2026-10-01, 2회차 **만료** |",
        "| 2 | **열린 일** | `tools/b.py` | 자체 승인 2026-10-02, 1회차 |",
        "| 3 | 맞지 않는 일 | `c.md` | 1회차 |",
    )
    hits = find(text, "tools/")
    assert [(hit.number, hit.line, hit.state, hit.rounds) for hit in hits] == [
        (1, 3, HitState.CLOSED, 2),
        (2, 4, HitState.OPEN, 1),
    ]


def test_search를_여러_번_주면_하나라도_맞은_행을_찾는다() -> None:
    text = queue(
        "| 1 | 일 | `a.md` | 1회차 |",
        "| 2 | 일 | `b.md` | 1회차 |",
        "| 3 | 일 | `c.md` | 1회차 |",
    )
    assert [hit.number for hit in find(text, r"a\.md", r"c\.md")] == [1, 3]


def test_무엇의_머리는_앞의_표지를_걷고_처음_닫는_표지까지다() -> None:
    hits = find(
        queue(
            "| 1 | **굵은 머리.** 뒤의 설명 | `a.md` | 1회차 |",
            "| 2 | ~~**닫힌 굵은 머리** 뒤~~ | `a.md` | 1회차 |",
            "| 3 | ~~취소선만 쓴 일.~~ 덧붙임 **굵은 꼬리** | `a.md` | 1회차 |",
            "| 4 | 표지 없는 일. 둘째 문장 | `a.md` | 1회차 |",
        ),
        r"a\.md",
    )
    assert [hit.head for hit in hits] == [
        "굵은 머리.",
        "닫힌 굵은 머리",
        "취소선만 쓴 일.",
        "표지 없는 일. 둘째 문장",
    ]


def test_머리가_길면_자르고_자른_글자_수를_적는다() -> None:
    exact = "가" * HEAD_CHARS
    (hit,) = find(queue(f"| 1 | **{exact}** | `a.md` | 1회차 |"), r"a\.md")
    assert hit.head == exact
    (hit,) = find(queue(f"| 1 | **{exact}나다** | `a.md` | 1회차 |"), r"a\.md")
    assert hit.head == f"{exact} …(2자 줄임)"


def test_승인_칸이_길면_가운데를_줄이고_줄인_글자_수를_적는다() -> None:
    """승인 칸은 첫 승인으로 시작해 회차와 닫힘을 뒤에 덧붙여 가므로 앞(첫 승인)과 끝(가장 늦게
    덧붙인 글의 꼬리)을 남긴다."""
    exact = "승" * (APPROVAL_HEAD + APPROVAL_TAIL)
    (hit,) = find(queue(f"| 1 | 일 | `a.md` | {exact} |"), r"a\.md")
    assert hit.approval == exact
    approval = "앞" * APPROVAL_HEAD + "가운데" + "끝" * APPROVAL_TAIL
    (hit,) = find(queue(f"| 1 | 일 | `a.md` | {approval} |"), r"a\.md")
    assert hit.approval == "앞" * APPROVAL_HEAD + " …(가운데 3자 줄임)… " + "끝" * APPROVAL_TAIL


def test_회차는_줄이기_전의_승인_칸에서_찾는다() -> None:
    """덧붙인 글이 길면 회차가 줄인 가운데에 들 수 있다."""
    approval = "앞" * APPROVAL_HEAD + " 7회차 " + "끝" * APPROVAL_TAIL
    (hit,) = find(queue(f"| 1 | 일 | `a.md` | {approval} |"), r"a\.md")
    assert hit.rounds == 7
    assert "7회차" not in hit.approval


def test_render_hits는_열린_행과_닫힌_행을_세고_행마다_한_줄을_찍는다() -> None:
    hits = find(
        queue(
            "| 1 | ~~**닫힌 일**~~ | `a.md` | 자체 승인 2026-10-01, 2회차 **만료 2026-10-20** |",
            "| 2 | **열린 일** | `a.md` | 자체 승인 |",
        ),
        r"a\.md",
    )
    assert render_hits(hits).splitlines() == [
        "맞은 행 2개(열린 행 1개, 닫힌 행 1개). 같은 일로 보이는 행은 그 줄을 Read 로 연다"
        "(offset 에 줄, limit 에 1):",
        "  1 줄 3 닫힘 2회차 머리: 닫힌 일 / 승인: 자체 승인 2026-10-01, 2회차 **만료 2026-10-20**",
        "  2 줄 4 열림 회차 모름 머리: 열린 일 / 승인: 자체 승인",
    ]


def test_render_hits는_맞은_행이_없으면_없다고_적는다() -> None:
    assert render_hits([]) == "맞은 행 없음"


def test_맞은_행의_칸이_넷이_아니면_그_행을_알리고_머리_줄에_따로_센다() -> None:
    hits = find(queue("| 7 | 일 | `a.md` | 승인 | 덤 |", "| 8 | 일 | `a.md` | 1회차 |"), r"a\.md")
    assert [(hit.number, hit.state) for hit in hits] == [(7, HitState.BROKEN), (8, HitState.OPEN)]
    out = render_hits(hits)
    assert "맞은 행 2개(열린 행 1개, 닫힌 행 0개, 칸이 넷이 아닌 행 1개)." in out
    assert "  7 줄 3 칸이 넷이 아니다" in out


def test_줄_번호는_줄바꿈으로만_센다() -> None:
    """`str.splitlines` 는 U+2028 에서도 갈라, 찍은 줄이 Read 의 줄과 어긋나고 행이 깨진다."""
    first = "| 1 | 일" + chr(0x2028) + "이어짐 | `a.md` | 1회차 |\n"
    text = HEAD + first + "| 2 | 일 | `a.md` | 1회차 |\n"
    hits = find(text, r"a\.md")
    assert [(hit.number, hit.line, hit.state) for hit in hits] == [
        (1, 3, HitState.OPEN),
        (2, 4, HitState.OPEN),
    ]


def test_못_보는_것_어디에_맞았는지는_찍지_않는다() -> None:
    """어디로 칸이나 잘린 자리에서만 맞은 행도 찍지만, 맞은 낱말은 출력에 없다."""
    hits = find(queue("| 1 | **머리** | `tools/숨은.py` | 1회차 |"), "숨은")
    out = render_hits(hits)
    assert "  1 줄 3 열림 1회차 머리: 머리 / 승인: 1회차" in out
    assert "숨은" not in out
    approval = "앞" * APPROVAL_HEAD + "숨은" + "끝" * APPROVAL_TAIL
    hits = find(queue(f"| 2 | **머리** | `a.md` | {approval} |"), "숨은")
    out = render_hits(hits)
    assert "  2 줄 3 열림 회차 모름 머리: 머리 / 승인: " in out
    assert "숨은" not in out


def test_못_보는_것_수를_찾으면_그_수를_품은_더_긴_수에도_맞는다() -> None:
    """번호는 앞뒤에 숫자가 없게 좁힌다. `\\b` 는 수와 한글 사이를 경계로 보지 않아 `425의` 를
    놓친다."""
    text = queue(
        "| 425 | 일 | `a.md` | 1회차 |",
        "| 1425 | 일 | `b.md` | 1회차 |",
        "| 7 | 425의 2회차 | `c.md` | 2회차 |",
    )
    assert [hit.number for hit in find(text, "425")] == [425, 1425, 7]
    assert [hit.number for hit in find(text, r"(?<!\d)425(?!\d)")] == [425, 7]
    assert [hit.number for hit in find(text, r"\b425\b")] == [425]


def test_못_보는_것_행_모양이_아닌_줄은_찾지_않는다() -> None:
    """`| N |` 로 시작하지 않는 줄(붙여 쓴 칸, 들여 쓴 행, 본문)은 기본 출력처럼 행이 아니다."""
    text = queue("|425| 붙여 쓴 행 | `a.md` | 1회차 |", "  | 9 | 들여 쓴 행 | `a.md` | 1회차 |")
    assert find(text + "본문의 425\n", r"425|a\.md") == []


def test_main은_search를_주면_맞은_행만_찍고_기본_출력을_내지_않는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "queue.md"
    path.write_text(
        queue("| 1 | 일 | `a.md` | 3회차 |", "| 2 | 일 | `b.md` | 1회차 | 덤 |"), encoding="utf-8"
    )
    assert main(["--queue", str(path), "--search", r"a\.md"]) == 0
    out = capsys.readouterr().out
    assert "  1 줄 3 열림 3회차" in out
    assert "회차 3 이상" not in out
    assert main(["--queue", str(path), "--search", r"b\.md"]) == 1
    assert "  2 줄 4 칸이 넷이 아니다" in capsys.readouterr().out


def test_main은_search의_인자가_틀리면_쓰임을_내고_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "queue.md"
    path.write_text(queue("| 1 | 일 | `a.md` | 1회차 |"), encoding="utf-8")
    wrong = (["--search"], ["--search", "a", "--rows"], ["--today", "2026-10-01", "--search", "a"])
    for extra in wrong:
        assert main(["--queue", str(path), *extra]) == 2
        assert "쓰임:" in capsys.readouterr().err
    assert main(["--queue", str(path), "--search", "("]) == 2
    assert "정규식이 틀렸다: (" in capsys.readouterr().err
    # re.error 가 아닌 것을 던지는 정규식도 트레이스백의 종료 1("칸이 넷이 아닌 행")이 아니라 2다
    for source in ("a{99999999999}", "(" * 5000 + ")" * 5000):
        assert main(["--queue", str(path), "--search", source]) == 2
        assert "정규식이 틀렸다:" in capsys.readouterr().err


def test_search를_실제로_불러_한글을_찍는다(tmp_path: Path) -> None:
    path = tmp_path / "queue.md"
    path.write_text(queue("| 9 | **찾을 일** | `a.md` | 자체 승인, 2회차 |"), encoding="utf-8")
    done = _run("--queue", str(path), "--search", "찾을", cwd=tmp_path)
    assert done.returncode == 0, done.stderr
    assert "  9 줄 3 열림 2회차 머리: 찾을 일 / 승인: 자체 승인, 2회차" in done.stdout


def test_이_저장소의_대기열에서_닫힌_행까지_찾는다() -> None:
    """실제 대기열의 모양(굵게·취소선 표지, 긴 칸)을 찾기가 읽는지 보는 스모크다. 닫힌 행 찾기
    자체는 앞의 임시 파일 시험이 고정한다. 425는 이 옵션을 처방한 행이고 이 옵션을 더한 티켓이
    닫았다. 행은 지우지 않으니 늘 있다."""
    hits = search(
        (ROOT / QUEUE).read_text(encoding="utf-8"), [re.compile("Omitted long matching line")]
    )
    assert [hit.state for hit in hits if hit.number == 425] == [HitState.CLOSED]
