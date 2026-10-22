"""프로브(`.scratch/**/probes/`)가 나눠 쓰는 두 가지. 회차마다 받은 표지로 측정인 회차와 아닌
회차를 세는 `Rounds` 와, 하위 프로세스의 출력 줄을 제한 시간 안에 읽는 `LineReader` 다.

왜. 새 프로브의 첫 판이 `.claude/rules/probes.md` 의 두 항목을 되풀이해 어겼다. 첫 항목(재려는
상황이 그 회차에 났다는 표지를 보고, 표지 없는 회차가 있으면 0 으로 끝내지 않는다)을 어긴 판을
셀프 리뷰가 잡았고, 다섯째 항목(막히는 `readline` 대신 읽는 스레드와 큐)을 어긴 판은 하위
프로세스의 첫 줄을 막히는 `readline` 으로 읽고 끝까지 도는 루프에 마감이 없었으며, 기록 파일이
없으면 예외로 앞서 모은 회차를 잃었다. 뒤의 것은 셀프 리뷰와 PR 직전 리뷰를 지나 PR 의
CodeRabbit 이 잡았다(대기열 339, 일지 2026-10-17-10·2026-10-20-36·2026-10-21-12). 그때마다 프로브가
스레드와 큐와 셈을 새로 짰다. 그래서 그 둘을 여기 두고 그 두 항목이 이것을 가리킨다.

쓰임. 프로브는 저장소 루트를 `sys.path` 에 넣고 가져온다(선례
`.scratch/harness/probes/edit_during_commit_time.py`). 회차 하나를 `with rounds.round(<이름>) as
current:` 로 감싸고, 재려는 상황이 났다는 표지를 본 뒤 `current.mark(measured=..., result=...)` 를
부른다. 끝에 `print(rounds.summary())` 와 `return rounds.exit_code()` 다. 하위 프로세스는
`stdout=subprocess.PIPE`, 읽지 않는 stderr 는 `subprocess.DEVNULL` 로 띄우고(파이프로 받고 읽지
않으면 버퍼가 차서 멈춘다) `LineReader(process.stdout)` 로 읽는다.

못 보는 것.
- 표지의 정의. 무엇이 재려는 상황인지는 프로브가 정한다. 고친 판이 고친 길을 지났다는 표지를
  고치기 전 판에도 나는 관찰로 정하면 이 셈은 그것을 가르지 못한다(대기열 367 이 그 정의를
  맡는다).
- `KeyboardInterrupt` 와 `SystemExit`. 회차 안에서 나면 회차로 적지 않고 그대로 올린다. 프로브를
  끊는 것은 측정이 아니다.
- 읽는 스레드가 막힌 `readline` 에 남은 채 프로브가 끝나는 것. 스레드는 daemon 이라 파이썬의 끝을
  막지 않지만, 그 하위 프로세스를 끄는 일은 프로브의 몫이다(`.claude/rules/probes.md` 의 끄기
  항목).
"""

from __future__ import annotations

import queue
import threading
from collections import Counter
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import IO


@dataclass(frozen=True)
class Entry:
    """회차 하나. `measured` 는 재려는 상황이 그 회차에 났다는 표지를 봤는지, `result` 는 측정인
    회차면 결과의 갈래, 아니면 측정이 아닌 까닭이다."""

    label: str
    measured: bool
    result: str


@dataclass
class Slot:
    """`Rounds.round` 가 내주는 회차 하나의 자리. `mark` 를 부르지 않고 끝나면 측정이 아니다."""

    label: str
    entry: Entry | None = None

    def mark(self, *, measured: bool, result: str = "") -> None:
        self.entry = Entry(self.label, measured, result)


@dataclass
class Rounds:
    """회차를 모아 측정인 회차와 아닌 회차를 센다."""

    entries: list[Entry] = field(default_factory=list[Entry])

    def record(self, label: str, *, measured: bool, result: str = "") -> None:
        self.entries.append(Entry(label, measured, result))

    @contextmanager
    def round(self, label: str) -> Generator[Slot]:
        """회차 하나. 본문이 예외(`Exception`)로 끝나면 그 예외를 측정이 아닌 까닭으로 적고 삼킨다.
        그래야 앞서 모은 회차와 뒤 회차를 잃지 않는다. 본문이 `mark` 없이 끝나도 측정이 아니다."""
        slot = Slot(label)
        try:
            yield slot
        except Exception as error:  # 회차 하나의 실패가 다른 회차를 잃게 하지 않는다
            self.record(label, measured=False, result=f"예외: {error!r}")
            return
        if slot.entry is None:
            self.record(label, measured=False, result="표지를 적지 않았다")
        else:
            self.entries.append(slot.entry)

    @property
    def measured(self) -> list[Entry]:
        return [entry for entry in self.entries if entry.measured]

    @property
    def unmeasured(self) -> list[Entry]:
        return [entry for entry in self.entries if not entry.measured]

    def exit_code(self) -> int:
        """측정인 회차가 하나 이상이고 측정이 아닌 회차가 없을 때만 0, 아니면 1."""
        return 0 if self.measured and not self.unmeasured else 1

    def summary(self) -> str:
        """측정인 회차와 아닌 회차의 수, 측정인 회차의 결과 갈래별 수, 측정이 아닌 회차마다 그
        까닭. 결론은 측정인 회차로만 낸다."""
        measured, unmeasured = self.measured, self.unmeasured
        lines = [f"측정 {len(measured)}회차, 측정 아님 {len(unmeasured)}회차"]
        counts = Counter(entry.result for entry in measured)
        if counts:
            lines.append("결과: " + ", ".join(f"{name} {count}" for name, count in counts.items()))
        lines.extend(f"측정 아님 {entry.label}: {entry.result}" for entry in unmeasured)
        return "\n".join(lines)


class LineReader:
    """하위 프로세스 출력의 줄을 제한 시간 안에 읽는다. 막히는 `readline` 은 루프의 제한 시간으로
    끊지 못해(`.claude/rules/tools.md` 의 시간 제한 항목) daemon 스레드가 읽어 큐에 넣는다.
    스레드는 EOF 에서 끝 표시(None)를 넣고, 그 표시를 꺼낸 읽기는 `ended` 로 기억해 뒤의 읽기와
    배출이 같은 표시를 다시 기다리며 막히지 않는다. 바이트 흐름은 UTF-8 로 풀고 풀지 못한 바이트는
    바꿔 넣는다."""

    def __init__(self, stream: IO[bytes] | IO[str]) -> None:
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._ended = False
        threading.Thread(target=self._pump, args=(stream,), daemon=True).start()

    def _pump(self, stream: IO[bytes] | IO[str]) -> None:
        try:
            while raw := stream.readline():
                text = raw if isinstance(raw, str) else raw.decode("utf-8", errors="replace")
                self._lines.put(text)
        except (OSError, ValueError):  # 프로브가 흐름을 먼저 닫았다
            pass
        finally:
            self._lines.put(None)

    @property
    def ended(self) -> bool:
        """EOF 표시를 꺼냈는가. `readline` 의 None 이 제한 시간인지 EOF 인지 이것으로 가른다."""
        return self._ended

    def readline(self, timeout: float) -> str | None:
        """줄 하나. 제한 시간 안에 줄이 오지 않았거나 EOF 면 None 이다."""
        if self._ended:
            return None
        try:
            line = self._lines.get(timeout=max(timeout, 0))
        except queue.Empty:
            return None
        if line is None:
            self._ended = True
        return line

    def drain(self, timeout: float) -> list[str]:
        """남은 줄을 EOF 나 줄 사이의 제한 시간까지 모은다. 하위 프로세스가 띄운 손자가 출력을
        쥐고 남으면 EOF 가 오지 않으므로 제한 시간으로 끝난다."""
        lines: list[str] = []
        while (line := self.readline(timeout)) is not None:
            lines.append(line)
        return lines
