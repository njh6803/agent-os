"""바이트 그대로 되돌리는 변이 도구.

테스트가 무엇을 재는지 변이로 본다. 구현 전부터 초록인 가드, 구현 뒤에 쓴 테스트, 새 검사가 그
대상이다. 세션마다 스크래치에 변이 스크립트를 새로 짓다가 같은 함정을 두 번 밟아서 여기 있다(대기열
29). 텍스트로 되돌려 줄 끝이 CRLF 가 됐고, 기대 결과를 받지 않아 아무것도 재지 않은 변이가 초록으로
지나갔다. pytest 밖의 명령(Vitest, Playwright, tsc)도 돈다. web 티켓 03~08이 같은 규약의 JS 러너를
저마다 지었고 첫 판정이 틀렸다(대기열 59, tsc 의 종료 코드 2를 빨강으로, TS1360 을 문법 오류로).

사용: PYTHONUTF8=1 uv run python tools/mutate.py <변이 파일.toml> [이름|번호 ...] [--since <커밋>]
          [--check]
      uv run python tools/mutate.py --check <변이 파일.toml> <변이 파일.toml> ...
LLM 테스트가 대상이면 `PYTHONUTF8=1 uv run --env-file .env python tools/mutate.py …` 이고 tests 에
`-m llm` 을 넣는다. `--check` 는 원문만 본다 — 명령을 돌리지 않고, 고른 변이마다 원문이 파일에
정확히 한 번 있는지(와 러너의 자리, 되돌릴 파일)를 보고 틀린 것을 모두 알린다. 코드를 고친 뒤 다른
변이 파일의 원문이 옮겨 가지 않았는지 볼 때 쓴다. `--check` 만 변이 파일 여럿(`.toml` 로 끝나는
인자)을 받고, 그때는 이름·번호·`--since` 를 섞지 않는다. 고르지 않고 주면 줄마다 그 파일의 경로가
붙고 읽지 못한 파일이 있어도 나머지를 본다. pre-commit 이 커밋에 든 변이 표(`_mutations.toml`)를 이
모양으로 넘긴다 — 변이를 돌린 뒤 `ruff format` 이 코드를 고쳐 커밋한 표의 원문이 사라진 일이
있었다(대기열 92). 커밋에 들지 않은 옛 표는 보지 않는다. 옛 프로브의 원문은 코드가 바뀌면 썩어도
되고, 다시 돌리거나 고쳐 커밋할 때 이 확인이 알린다.

고르기. 이름, 번호, `--since <커밋>` 으로 고르고 함께 주면 합친다. 아무것도 주지 않으면 전부다.
번호는 표에 적힌 차례(1부터)이고, 출력의 줄 머리와 어긋났을 때의 마지막 줄(`다시 돌릴 번호`)에
찍힌다. 이름은 공백이 들어 따옴표 인자가 필요한데 워크트리 가드가 그런 인자를 거부한 적이 있어,
고를 때는 번호나 `--since` 를 쓴다(대기열 193). 그래서 이름을 숫자로만 짓지 않는다. `--since` 는
그 커밋에 있던 같은 표와 견주어 새로 더했거나 무엇이든(원문, 기대, 시험, 시간 제한, 그 변이가 쓰는
러너) 달라진 변이를 고른다. 그 커밋에 표가 없으면 모두 새것이다. 고를 것이 없으면 아무것도 돌리지
않고 2로 끝난다. 잘못 준 커밋이 0 으로 끝나면 잰 것처럼 보이기 때문이다. 줄 커밋은 그 표를
마지막으로 돌린 커밋이다(일지의 검사 절에 적어 둔다). 이 브랜치가 더하거나 고친 변이만 보려면
`origin/main` 이다. 커밋한 표를 다른 워크트리에서 돌리며 `HEAD` 를 주면 표가 같아 고를 것이 없다.
언제 전체를 돌리나: 시험을 고치거나 지웠으면 전체, 시험을 더하기만 했거나 코드만 바꿨으면 고른
것(원문을 고쳤거나 더한 변이)이다. 견주는 쪽은 그 표를 마지막으로 돌린 판이다. 시험을 더해서는
빨갛던 변이가 초록이 되지 않지만, 고치거나 지우면 다른 변이를 잡던 단언이 사라질 수 있다. 시험을
고친 판에서 그런 일을 전체 실행이 잡았다(일지 2026-10-12-16의 둘째 판). 못 보는 것: 코드만 바꾼
판에서 원문이 그대로인 변이도 둘레의 코드가 바뀌어 결과가 달라질 수 있다. 시험을 더하면 초록을
기대한 변이(대조군)가 빨개질 수 있다(일지 2026-10-12-29, `mutate_restore` 표). 고른 것만 돌리면 둘
다 보지 못한다.

변이 파일은 TOML 이다. 원문은 리터럴 여러 줄 문자열(`'''`)로 적으면 이스케이프가 없다. 여는 `'''`
바로 뒤의 줄바꿈은 TOML 이 버리지만 닫는 `'''` 앞의 줄바꿈은 원문에 든다. 그래서 닫는 `'''` 를 다음
줄에 두는 원문은 마지막 줄을 줄 끝까지 온전히 적고, 줄의 일부만 적을 때는 닫는 `'''` 를 같은 줄에
둔다(줄의 일부만 적은 원문 넷이 `--check` 에서 걸렸다, 대기열 152). 아래 예시는 네 칸 들여쓴 채라
옮길 때 그 네 칸을 걷어 낸다.

    [runner.vitest]                      # 선택. 이름은 마음대로이고 pytest 만 내장이라 못 쓴다
    command = ["pnpm", "exec", "vitest", "run"]
    cwd = "web"                          # 저장소 루트 기준. 기본은 루트
    judge = "vitest"                     # pytest, vitest, playwright, tsc, exit
    # red_exit = 1                          exit 판정이면 반드시(1 이상). 빨강으로 읽을 종료 코드
    # baseline_output = ["검사 12"]          선택. 기준선 출력에 있어야 할 표지

    [[mutation]]
    name = "꺼짐을 깨짐 앞에"
    runner = "pytest"                    # 선택. 기본은 내장 pytest(-q -p no:cacheprovider)
    tests = ["tests/core/test_run.py"]   # 명령 뒤에 붙는다. -k(pytest), -t(vitest)로 좁힌다
    expect = "red"                       # red, green, 또는 unhandled(vitest 판정만)
    repeat = 1                           # 선택. 매번 기대와 같아야 한다
    timeout = 600                        # 선택. 한 번 돌리는 시간 제한(초). 기본 600
    # diagnostic_in = "clients.test-d.ts"   tsc 판정이면 반드시. 빨강이 날 파일
    # expect_output = ["이름이 없다: a"]      선택. 매 반복의 출력에 있어야 할 표지
    # restore = ["web/gen/openapi.ts"]      선택. 명령이 고쳐 쓸 수 있어 되돌릴 파일

    [[mutation.edit]]                    # 여럿이면 차례로 들어간다
    file = "src/agent_os/core/run.py"    # 저장소 루트 기준
    old = '''
        servers = _resolve_servers(plugins, manifest)
        _reject_masked_approvals(manifest, servers)
        _reject_disabled(plugins.read_disabled(), manifest)
    '''
    new = '''
        _reject_disabled(plugins.read_disabled(), manifest)
        servers = _resolve_servers(plugins, manifest)
        _reject_masked_approvals(manifest, servers)
    '''

판정(`judge`). 종료 코드만으로는 빨강과 오류를 가를 수 없는 명령이 있어 판정마다 출력의 요약을
읽는다. 오류는 기대가 무엇이든 어긋남이다 — 문법 오류로 모든 것이 빨간 변이는 테스트의 이빨을 재지
않는다.
- pytest: 종료 코드 0 은 초록, 1 은 빨강, 나머지(수집 오류, 없는 경로, 선택된 테스트 없음)는 오류다.
  0 이어도 skip 이 섞였으면 오류다. 재지 않은 테스트가 있다(원칙 II).
- vitest: 종료 코드가 실패, 수집 오류, 처리하지 않은 에러에 모두 1 이다. 요약의 `Tests` 줄에 실패가
  셀 때만 빨강이고, 파일 단위의 FAIL(`[ 파일 ]` 로 끝나는 줄, 수집 오류)이 하나라도 있으면 오류다.
  실패 없이 `Errors` 줄만 있으면 처리하지 않은 에러(unhandled)다. 가드가 막는 것이 그것뿐인 변이는
  그것을 기대로 적는다. 초록은 통과한 테스트가 하나 이상일 때다.
- playwright: 요약에 `N failed` 가 셀 때만 빨강이다. 초록은 종료 코드 0 에 통과가 있고 skip 이 없을
  때다.
- tsc: 종료 코드가 문법 오류와 타입 에러에 같고(2) 오류 번호로도 가를 수 없다(`satisfies` 의
  어긋남이 TS1360 이다). 빨강은 `diagnostic_in` 파일에서 난 진단이고, 그 파일 밖에서만 나면 오류다.
  `diagnostic_in` 은 진단 경로의 꼬리로 맞춘다. 이름만 적으면 다른 디렉터리의 같은 이름
  (`index.ts`)도 맞으니, 이름이 겹치면 디렉터리까지 적는다.
- exit: 종료 코드로만 말하는 명령(node 검사기)이다. 0 은 초록, 러너의 `red_exit` 는 빨강,
  나머지(읽을 파일이 없다는 2 따위)는 오류다. 검사기 변이를 따로 짓던 프로브를 표로 옮기려고
  더했다(대기열 253).

표지(`expect_output`, `baseline_output`). 판정이 기대와 맞아도 엉뚱한 까닭의 빨강일 수 있다
(`.claude/rules/probes.md` 의 표지 항목). 그래서 변이마다 출력에 있어야 할 문구를 적을 수 있고, 색
코드를 벗긴 출력에서 매 반복 찾는다. 하나라도 없으면 `표지 없음: …` 줄과 출력의 끝을 내고 어긋남으로
센다. 러너의 `baseline_output` 은 기준선에서 같은 일을 한다. 없으면 기준선은 초록이 아니다. 종료
코드 0 만으로는 아무것도 읽지 않고 끝난 검사기와 가를 수 없다. 빈 문자열은 어느 출력에나 있어 변이
파일 오류다.

하는 일, 차례대로:
1. 변이 파일의 모양과 러너·판정의 짝을 보고, 변이마다 원문이 파일에 정확히 한 번 있는지, 러너의
   자리와 되돌릴 파일이 저장소 안에 있는지 본다. 하나라도 틀리면 아무 파일도 쓰지 않고 끝낸다.
2. 러너와 인자의 짝마다 변이 없이 한 번씩 돌린다(기준선). 시간 제한은 그 짝을 쓰는 변이 가운데
   가장 긴 것이다. 초록이 아니면 변이를 넣지 않는다. 기준선이 빨간데 변이가 빨가면 그 빨강은
   아무것도 말하지 않는다. 이름으로 좁힌 선택이 비었는지도 여기서 본다.
3. 빨강을 기대한 pytest 판정의 변이는 인자 끝에 `-x` 를 붙여 첫 실패에서 멈춘다. 빨강은 실패
   하나로 정해지고 `-x` 도 종료 코드 1 이라 판정이 같다. 기준선과 초록·오류를 볼 변이는 끝까지 돈다.
   sibling_overlap 표본 여섯이 446초에서 163초가 됐고 판정이 같았다(대기열 231,
   `.scratch/harness/probes/mutate_231/`). 변이마다 원래 바이트(되돌릴 파일 포함)를 쥐고 변이를 넣어
   돌린 뒤 `finally` 에서 그 바이트를 그대로 쓴다. 쓰기 전에 편집한 파일이 쓴 변이 바이트 그대로인지
   본다. 다르면 변이가 든 동안 다른 쓰기(편집기, 다른 세션)가 들어온 것이라 덮지 않고 알린다(대기열
   77). 되돌릴 파일(`restore`)은 명령이 고쳐 쓰는 파일이라 보지 않고 쓴다. 명령 한 번이 시간
   제한(`timeout`)을 넘기면 그 명령이 띄운 프로세스까지 끝내고(못 보는 것은 아래), 끊기 전의 출력이
   무엇이든 오류로 판정한 뒤 남은 반복(`repeat`)을 건너뛰고 되돌려 다음 변이로 간다. 검사 러너의
   변이가 러너→pytest→러너로 되풀이하며 10분 넘게 돌았고, 손으로 죽이자 변이된 한 줄이 파일에
   남았다(대기열 139). 기다리는 동안 예외(Ctrl+C 의 `KeyboardInterrupt`)가 올라와도 띄운
   프로세스까지 끝낸 뒤 되돌린다. 윈도우에서 실제 Ctrl+C 가 그 기다림을 끊는지는 재지 않았다(시험은
   그 예외를 넣는다).
4. 종료 코드: 모두 기대대로면 0, 어긋나거나(시간 제한을 넘긴 것 포함) 기준선이 초록이 아니면 1,
   변이 파일을 읽지 못했거나 틀렸거나 고른 것이 없으면 2(아무 파일도 쓰지 않았다), 테스트를 돌리지
   못했거나 되돌리지 못했으면 3.

제자리가 아닌 실행. 변이는 이 도구가 든 체크아웃을 고친다. 도는 동안(web 변이 수십 개는 40분이
넘는다) 그 체크아웃을 고치거나 소스를 읽는 리뷰를 띄우면 변이된 소스를 본다. 그래서 잴 코드를
커밋하고 다른 워크트리에서 그 워크트리의 도구로 돌린다. 변이 파일은 어느 경로여도 되고 편집의 `file`
은 도는 도구가 든 체크아웃 기준이다. pnpm 은 저장소(store)에서 링크만 해 네트워크를 타지
않는다(2026-10-01 13초, 일지 2026-10-01-01). `.env` 는 추적하지 않으므로 LLM 변이면 새 워크트리에
복사한다. 변이가 끝나면 지우는 워크트리라 사본이 남지 않는다. 남겨 두고 일하는 워크트리는 사본을
만들지 않고 `--env-file` 로 주 체크아웃의 것을 읽는다(operations.md LLM 테스트). 에이전트의
명령 상한(10분)을 넘는 실행은 백그라운드로 돌린다. 바깥에서 이 도구를 죽이는 것(셸의 `timeout`
명령, 백그라운드 실행의 상한)은 아래 못 보는 것의 강제 종료라 되돌림이 돌지 않을 수 있다. 시간은
변이마다의 `timeout` 으로 걸고, 바깥의 상한은 표 전체보다 넉넉히 준다. 도는 동안 변이한 파일을
고치면(되돌릴 파일로 적지 않았으면) 되돌림이 그 파일을 덮지 않고 3으로 멈추고, 변이는 손으로 걷어
낸다.

    git worktree add --detach <임시 경로> HEAD
    (그 경로에서) uv sync
    (그 경로에서) pnpm -C web install --frozen-lockfile --offline    # web 변이일 때
    (그 경로에서) PYTHONUTF8=1 uv run python tools/mutate.py <변이 파일>
    git worktree remove <임시 경로>

바이트코드 캐시는 소스의 수정 시각(초)과 크기로만 맞춰 보므로, 크기가 같은 변이가 같은 초에 쓰이면
낡은 캐시가 돈다. 그래서 변이를 쓴 직후와 되돌린 직후에 그 소스의 `__pycache__/<이름>.*.pyc`(CPython
의 것과 pytest assertion rewrite 의 것)를 지우고, 하위 명령은 `PYTHONDONTWRITEBYTECODE=1` 로 돌아
변이된 소스의 캐시를 새로 남기지 않는다. `-p no:cacheprovider` 는 변이의 실패가 `.pytest_cache` 의
lastfailed 에 남지 않게 한다.

못 보는 것: 프로세스가 강제로 죽으면(`finally` 가 돌지 않으면) 되돌리지 못한다. 되돌리는 쓰기가
실패하거나(파일이 잠겼다) 다른 쓰기가 들어왔으면 나머지 파일은 되돌리고 남은 파일을 알린다. 세 경우
모두 `git diff` 로 본다. 되돌릴 파일(`restore`, 편집한 파일을 함께 적은 것 포함)에 든 다른 쓰기는
명령의 쓰기와 가를 수 없어 덮는다. 편집한 파일을 읽은 뒤 쓰기까지의 틈에 든 쓰기도 덮는다. 틈은
다음과 같다.
- 원래 바이트를 읽고 변이를 쓰기까지.
- 되돌리기 전에 읽어 보고 다시 쓰기까지.
- 앞 파일의 변이 쓰기가 실패해 변이를 쓰지 못한 파일이면, 처음 읽은 뒤 되돌리기까지. 쓴 변이
  바이트가 없어 보지 않는다.

시간 제한으로 끝내는 프로세스는 윈도우에서 `taskkill /T` 가 부모를 따라 찾은 것이고, POSIX 에서는
자식이 이끄는 프로세스 그룹이다. 부모가 먼저 끝나 고아가 된 손자(윈도우)와 제 세션이나 프로세스
그룹을 따로 연 손자(POSIX)는 남는다. 남은 것이 출력 파이프를 쥐면 끊은 뒤 10초만 출력을 기다리고
그만 읽는다. 이 판단은 윈도우 10(19045)의 `taskkill` 과 CPython 3.12.10 위에서 시험으로 봤다.

원문의 줄 끝은 파일과 같아야 한다 — 변이 파일의 `\\n` 은 CRLF 파일에서 맞지 않는다. vitest 의 skip
은 세지 않는다. `-t` 로 좁히면 고르지 않은 테스트가 skipped 로 세어져 `it.skip` 과 가를 수 없다. tsc
의 빨강은 진단이 난 파일만 본다. 변이가 낸 문법 오류가 적은 파일까지 번져도 빨강이다. 윈도우에서
`pnpm.CMD` 같은 배치 파일은 cmd.exe 가 돌려 인자의 `&`·`%`·`^` 가 해석될 수 있다. 좁힌 선택이 비면
기준선이 오류로 잡는다(통과가 없다). 표지는 출력 어디서든 부분 문자열로 찾는다. 다른 까닭의
실패가 같은 문구를 찍으면(같은 이름의 다른 검사) 표지가 있는 것으로 센다. `-x` 로 멈춘 변이는
빨간 시험을 첫 하나만 보인다. 그 변이가 빨갛게 할 시험이 몇인지, 뒤의 시험이 표지를 찍었을지는 남지
않는다.

판정은 출력의 요약 문구에 기댄다. 초록과 빨강을 읽는 문구(vitest 의 `Tests` 줄, playwright 의
`N passed`·`N failed`, tsc 의 진단 줄)가 도구의 판에서 바뀌면 오류로 기운다. 초록이나 빨강을
거르는 표지(vitest 파일 단위 FAIL 의 `[ 파일 ]`, pytest·playwright 의 `N skipped`)가 바뀌면 그것을
못 봐 수집 오류가 섞인 실패가 빨강으로, skip 이 섞인 통과가 초록으로 지나간다.
"""

from __future__ import annotations

import contextlib
import io
import os
import re
import shutil
import signal
import subprocess
import sys
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TIMEOUT = 600  # 명령 한 번의 시간 제한(초). 변이마다 `timeout` 으로 바꾼다
_DRAIN_SECONDS = 10  # 끊은 뒤 출력 파이프가 닫히기를 기다리는 시간
_KILL_SECONDS = 30  # 윈도우의 `taskkill` 을 기다리는 시간

type Outcome = Literal["green", "red", "unhandled", "error"]
type JudgeName = Literal["pytest", "vitest", "playwright", "tsc", "exit"]

_LABELS: dict[Outcome, str] = {
    "green": "초록",
    "red": "빨강",
    "unhandled": "처리하지 않은 에러",
    "error": "오류",
}
_PYTEST_OUTCOMES: dict[int, Outcome] = {0: "green", 1: "red"}
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
_PYTEST_SKIPPED = re.compile(r"\b\d+ skipped\b")
_VITEST_SUMMARY = re.compile(r"^\s*(Test Files|Tests|Errors)\s+(.+?)\s*$", re.MULTILINE)
_VITEST_FAIL = re.compile(r"^\s*FAIL\s+(.+?)\s*$", re.MULTILINE)
_VITEST_FILE_LEVEL = re.compile(r"\[ .+ \]$")
_PLAYWRIGHT_COUNT = re.compile(
    r"^\s*(\d+) (passed|failed|skipped|flaky|interrupted|did not run)\b", re.MULTILINE
)
_PLAYWRIGHT_FAILED = re.compile(r"\s*\d+ failed\s*")
_TSC_DIAGNOSTIC = re.compile(r"(\S+)\((\d+),(\d+)\): error (TS\d+)")
_NUMBER = re.compile(r"[0-9]+")


class SpecError(Exception):
    """변이 파일을 읽지 못했거나 틀렸다. 아무 파일도 쓰기 전에 난다."""


class RestoreError(Exception):
    """변이를 되돌리지 못한 파일이 있다. 변이가 든 동안 다른 쓰기가 들어왔거나, 그 파일을 읽거나
    다시 쓰다가 `OSError` 가 났다."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Edit(_Model):
    file: str
    old: str
    new: str


class RunnerSpec(_Model):
    command: list[str] = Field(min_length=1)
    cwd: str = "."
    judge: JudgeName
    red_exit: int | None = Field(default=None, ge=1)  # exit 판정만. 빨강으로 읽을 종료 코드
    baseline_output: list[str] = Field(default_factory=list[str])  # 기준선 출력에 있어야 할 표지


class Mutation(_Model):
    name: str
    runner: str = "pytest"
    tests: list[str] = Field(default_factory=list[str])
    expect: Literal["red", "green", "unhandled"]
    diagnostic_in: str | None = None
    expect_output: list[str] = Field(default_factory=list[str])  # 매 반복의 출력에 있어야 할 표지
    restore: list[str] = Field(default_factory=list[str])
    repeat: int = Field(default=1, ge=1)
    timeout: int = Field(default=DEFAULT_TIMEOUT, ge=1)
    edit: list[Edit] = Field(min_length=1)


class Spec(_Model):
    runner: dict[str, RunnerSpec] = Field(default_factory=dict[str, RunnerSpec])
    mutation: list[Mutation] = Field(min_length=1)


_BUILTIN: dict[str, RunnerSpec] = {
    "pytest": RunnerSpec(
        command=[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], judge="pytest"
    )
}


@dataclass(frozen=True)
class CommandResult:
    """명령 한 번의 결과. 출력은 stdout 뒤에 stderr 를 이은 것이다. 시간 제한을 넘겨 끊었으면
    `timed_out_after` 가 그 제한(초)이고 출력은 끊을 때까지 읽은 것이다. 끊은 뒤에도 출력 파이프가
    닫히지 않아 그만 읽었으면 출력 대신 그 안내 한 줄이다."""

    exit_code: int
    output: str
    timed_out_after: int | None = None

    @property
    def plain(self) -> str:
        """색 코드를 벗긴 출력."""
        return _ANSI.sub("", self.output)


@dataclass(frozen=True)
class Verdict:
    """판정 하나. `failed` 는 빨간 테스트(tsc 면 진단)의 이름이다."""

    outcome: Outcome
    summary: str
    failed: tuple[str, ...] = ()


type Runner = Callable[[Sequence[str], Path, int], CommandResult]  # 명령, 자리, 시간 제한(초)


def _last_line(text: str, exit_code: int) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1].strip("= ") if lines else f"출력 없음(종료 코드 {exit_code})"


def _count(pattern: str, text: str) -> int:
    found = re.search(pattern, text)
    return int(found.group(1)) if found else 0


def _judge_pytest(exit_code: int, text: str) -> Verdict:
    summary = _last_line(text, exit_code)
    failed = tuple(
        line.split(" ", 1)[1].split(" - ", 1)[0]
        for line in text.splitlines()
        if line.startswith(("FAILED ", "ERROR "))
    )
    outcome = _PYTEST_OUTCOMES.get(exit_code, "error")
    if outcome == "green" and _PYTEST_SKIPPED.search(summary):
        outcome = "error"
    return Verdict(outcome, summary, failed)


def _judge_vitest(exit_code: int, text: str) -> Verdict:
    lines = {m.group(1): m.group(2) for m in _VITEST_SUMMARY.finditer(text)}
    summary = ", ".join(f"{key} {value}" for key, value in lines.items())
    tests = lines.get("Tests", "")
    fails = tuple(m.group(1) for m in _VITEST_FAIL.finditer(text))
    outcome: Outcome
    if any(_VITEST_FILE_LEVEL.search(fail) for fail in fails):
        outcome = "error"
    elif exit_code == 0:
        outcome = "green" if _count(r"(\d+) passed", tests) > 0 else "error"
    elif _count(r"(\d+) failed", tests) > 0:
        outcome = "red"
    elif "Errors" in lines:
        outcome = "unhandled"
    else:
        outcome = "error"
    return Verdict(outcome, summary or _last_line(text, exit_code), fails)


def _playwright_failed(text: str) -> tuple[str, ...]:
    """요약의 `N failed` 아래에 들여 적힌 `[프로젝트] › …` 줄들."""
    titles: list[str] = []
    lines = text.splitlines()
    for at, line in enumerate(lines):
        if _PLAYWRIGHT_FAILED.fullmatch(line):
            for follow in lines[at + 1 :]:
                if not follow.strip().startswith("["):
                    break
                titles.append(follow.strip())
    return tuple(titles)


def _judge_playwright(exit_code: int, text: str) -> Verdict:
    counts: dict[str, int] = {}
    for m in _PLAYWRIGHT_COUNT.finditer(text):
        counts[m.group(2)] = counts.get(m.group(2), 0) + int(m.group(1))
    summary = ", ".join(f"{n} {word}" for word, n in counts.items())
    outcome: Outcome
    if exit_code == 0:
        passed = counts.get("passed", 0) > 0 and counts.get("skipped", 0) == 0
        outcome = "green" if passed else "error"
    else:
        outcome = "red" if counts.get("failed", 0) > 0 else "error"
    return Verdict(outcome, summary or _last_line(text, exit_code), _playwright_failed(text))


def _judge_tsc(exit_code: int, text: str, diagnostic_in: str | None) -> Verdict:
    if exit_code == 0:
        return Verdict("green", "진단 없음")
    diagnostics = [(m.group(1), m.group(0)) for m in _TSC_DIAGNOSTIC.finditer(text)]
    summary = f"진단 {len(diagnostics)}" if diagnostics else _last_line(text, exit_code)
    target = diagnostic_in or ""
    hit = any(path == target or path.endswith(f"/{target}") for path, _ in diagnostics)
    return Verdict("red" if hit else "error", summary, tuple(line for _, line in diagnostics))


def _judge_exit(exit_code: int, text: str, red_exit: int | None) -> Verdict:
    outcome: Outcome = "green" if exit_code == 0 else "red" if exit_code == red_exit else "error"
    return Verdict(outcome, _last_line(text, exit_code))


def judge(
    kind: JudgeName,
    result: CommandResult,
    diagnostic_in: str | None = None,
    *,
    red_exit: int | None = None,
) -> Verdict:
    """명령의 결과를 초록, 빨강, 처리하지 않은 에러, 오류로 가른다. 색 코드는 벗기고 읽는다. 시간
    제한을 넘겨 끊은 결과는 끊기 전의 출력이 무엇이든 오류다. `red_exit` 는 exit 판정만 쓴다."""
    if result.timed_out_after is not None:
        return Verdict("error", f"시간 제한 {result.timed_out_after}초를 넘겨 끊었다")
    text = result.plain
    match kind:
        case "pytest":
            return _judge_pytest(result.exit_code, text)
        case "vitest":
            return _judge_vitest(result.exit_code, text)
        case "playwright":
            return _judge_playwright(result.exit_code, text)
        case "tsc":
            return _judge_tsc(result.exit_code, text, diagnostic_in)
        case "exit":
            return _judge_exit(result.exit_code, text, red_exit)


def _runners(spec: Spec) -> dict[str, RunnerSpec]:
    """내장 러너와 변이 파일의 러너 표."""
    return {**_BUILTIN, **spec.runner}


def _pairing_problems(spec: Spec) -> list[str]:
    """러너와 판정의 짝. 파일을 보지 않는다."""
    problems = [
        f"러너 이름 {name} 는 내장이다. 다른 이름을 쓴다"
        for name in spec.runner
        if name in _BUILTIN
    ]
    for name, command in spec.runner.items():
        if command.judge == "exit" and command.red_exit is None:
            problems.append(
                f"러너 {name}: exit 판정은 red_exit(빨강으로 읽을 종료 코드)가 있어야 한다"
            )
        if command.judge != "exit" and command.red_exit is not None:
            problems.append(f"러너 {name}: red_exit 는 exit 판정만 쓴다(이 러너는 {command.judge})")
        if "" in command.baseline_output:
            problems.append(f"러너 {name}: baseline_output 에 빈 표지가 있다. 어느 출력에나 있다")
    runners = _runners(spec)
    for m in spec.mutation:
        if m.runner not in runners:
            problems.append(f"{m.name}: 러너 {m.runner} 가 [runner.{m.runner}] 에 없다")
            continue
        kind = runners[m.runner].judge
        if kind == "tsc" and m.diagnostic_in is None:
            problems.append(f"{m.name}: tsc 판정은 diagnostic_in(빨강이 날 파일)이 있어야 한다")
        if kind != "tsc" and m.diagnostic_in is not None:
            problems.append(f"{m.name}: diagnostic_in 은 tsc 판정만 쓴다(이 러너는 {kind})")
        if "" in m.expect_output:
            problems.append(f"{m.name}: expect_output 에 빈 표지가 있다. 어느 출력에나 있다")
        if m.expect == "unhandled" and kind != "vitest":
            problems.append(f"{m.name}: expect unhandled 는 vitest 판정만 쓴다(이 러너는 {kind})")
    return problems


def load_spec(text: str) -> Spec:
    try:
        spec = Spec.model_validate(tomllib.loads(text))
    except (tomllib.TOMLDecodeError, ValidationError) as error:
        raise SpecError(str(error)) from error
    names = [m.name for m in spec.mutation]
    repeated = sorted({name for name in names if names.count(name) > 1})
    if repeated:
        raise SpecError(f"이름이 겹친다: {', '.join(repeated)}. 이름으로 골라 다시 돌린다")
    numeric = [name for name in names if _NUMBER.fullmatch(name)]
    if numeric:
        raise SpecError(f"이름이 숫자뿐이다: {', '.join(numeric)}. 번호와 가를 수 없다")
    problems = _pairing_problems(spec)
    if problems:
        raise SpecError("\n".join(problems))
    return spec


def read_spec(path: Path) -> Spec:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SpecError(f"{path} 를 읽지 못했다: {error}") from error
    return load_spec(text)


def select(spec: Spec, picks: Sequence[str]) -> Spec:
    """이름이나 번호(표에 적힌 차례, 1부터)로 고른다. 없으면 전부다. 고른 것은 표의 차례로 돌고 러너
    표는 그대로 둔다."""
    if not picks:
        return spec
    known = {m.name for m in spec.mutation}
    chosen: set[str] = set()
    unknown: list[str] = []
    outside: list[str] = []
    for pick in picks:
        if _NUMBER.fullmatch(pick):
            if 1 <= int(pick) <= len(spec.mutation):
                chosen.add(spec.mutation[int(pick) - 1].name)
            else:
                outside.append(pick)
        elif pick in known:
            chosen.add(pick)
        else:
            unknown.append(pick)
    problems = [f"변이 파일에 없는 이름: {', '.join(unknown)}"] if unknown else []
    if outside:
        problems.append(f"표 밖의 번호 {', '.join(outside)} (이 표는 1~{len(spec.mutation)})")
    if problems:
        raise SpecError("\n".join(problems))
    return Spec(runner=spec.runner, mutation=[m for m in spec.mutation if m.name in chosen])


def _numbers(spec: Spec) -> dict[str, int]:
    """이름마다 표에 적힌 차례(1부터). 고를 때와 출력의 줄 머리가 쓴다."""
    return {m.name: at for at, m in enumerate(spec.mutation, 1)}


def _labelled(names: Sequence[str], numbers: Mapping[str, int]) -> str:
    return ", ".join(f"{numbers[name]}. {name}" for name in names)


def changed_names(old: Spec, new: Spec) -> list[str]:
    """`new` 의 변이 가운데 `old` 에 없거나 달라진 것의 이름, 표의 차례대로. 변이의 무엇이든(원문,
    기대, 표지, 시험, 시간 제한) 다르거나 그 변이가 쓰는 러너의 명령·자리·판정·빨강 코드·기준선
    표지가 다르면 달라진 것이다."""
    before = {m.name: m for m in old.mutation}
    old_runners, new_runners = _runners(old), _runners(new)
    return [
        m.name
        for m in new.mutation
        if before.get(m.name) != m or old_runners.get(m.runner) != new_runners.get(m.runner)
    ]


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SpecError(f"git {args[0]} 를 돌리지 못했다: {error}") from error


def changed_since(path: Path, spec: Spec, ref: str) -> list[str]:
    """`ref` 커밋에 있던 같은 표와 견주어 새로 더했거나 달라진 변이의 이름(`changed_names`). 그
    커밋에 표가 없으면 모두다. 표가 git 저장소 밖에 있거나 그 저장소에서 `ref` 를 커밋으로 풀지
    못하면 `SpecError`."""
    where = path.resolve().parent
    inside = _git(where, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        raise SpecError(f"--since {ref}: 표가 든 {where} 가 git 저장소 안이 아니다")
    if _git(where, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode != 0:
        raise SpecError(f"--since {ref}: {where} 의 저장소에서 커밋으로 풀지 못했다")
    shown = _git(where, "show", f"{ref}:./{path.name}")
    if shown.returncode != 0:
        return [m.name for m in spec.mutation]
    try:
        old = load_spec(shown.stdout)
    except SpecError as error:
        raise SpecError(
            f"--since {ref}: 그 커밋의 표를 지금의 도구로 읽지 못했다."
            f" 번호나 이름으로 고른다\n{error}"
        ) from error
    return changed_names(old, spec)


def _inside(root: Path, relative: str) -> Path | None:
    """저장소 안이면 그 경로, 밖이면 None."""
    path = (root / relative).resolve()
    return path if path.is_relative_to(root.resolve()) else None


def _mutated(root: Path, mutation: Mutation) -> dict[Path, tuple[bytes, bytes]]:
    """파일마다 (원래 바이트, 변이된 바이트). 편집은 적힌 차례로 앞 편집의 결과 위에 들어간다."""
    files: dict[Path, tuple[bytes, bytes]] = {}
    for edit in mutation.edit:
        path = _inside(root, edit.file)
        if path is None:
            raise SpecError(f"{mutation.name}: {edit.file} 는 저장소 밖이다")
        if path not in files:
            try:
                data = path.read_bytes()
            except OSError as error:
                raise SpecError(f"{mutation.name}: {edit.file} 를 읽지 못했다: {error}") from error
            files[path] = (data, data)
        original, current = files[path]
        old = edit.old.encode("utf-8")
        count = current.count(old)
        if count != 1:
            raise SpecError(
                f"{mutation.name}: {edit.file} 에 원문이 {count}번 있다. 정확히 한 번이어야 한다"
                " (줄 끝과 들여쓰기까지 바이트로 맞춘다)"
            )
        files[path] = (original, current.replace(old, edit.new.encode("utf-8")))
    return files


def _file_problems(root: Path, spec: Spec) -> list[str]:
    """고른 변이의 원문, 그 변이들이 쓰는 러너의 자리, 되돌릴 파일. 아무 파일도 쓰지 않는다."""
    problems: list[str] = []
    for name in sorted({m.runner for m in spec.mutation} & spec.runner.keys()):
        where = _inside(root, spec.runner[name].cwd)
        if where is None or not where.is_dir():
            problems.append(
                f"러너 {name}: 자리 {spec.runner[name].cwd} 가 저장소 안의 디렉터리가 아니다"
            )
    for mutation in spec.mutation:
        try:
            _mutated(root, mutation)
        except SpecError as error:
            problems.append(str(error))
        for relative in mutation.restore:
            path = _inside(root, relative)
            if path is None or not path.is_file():
                problems.append(f"{mutation.name}: 되돌릴 파일 {relative} 가 저장소 안에 없다")
    return problems


def _validate(root: Path, spec: Spec) -> None:
    problems = _file_problems(root, spec)
    if problems:
        raise SpecError("\n".join(problems))


def _drop_bytecode(path: Path) -> None:
    """그 소스의 바이트코드 캐시를 지운다. CPython 의 것과 pytest assertion rewrite 의 것이다."""
    for cached in path.parent.glob(f"__pycache__/{path.stem}.*.pyc"):
        cached.unlink(missing_ok=True)


def _invoke(
    root: Path, spec: Spec, name: str, tests: Sequence[str], timeout: int, runner: Runner
) -> CommandResult:
    command = _runners(spec)[name]
    return runner([*command.command, *tests], root / command.cwd, timeout)


class _WrittenMeanwhile(Exception):
    """변이가 든 동안 다른 쓰기가 들어와, 파일이 쓴 변이 바이트가 아니다."""


def _restore_file(path: Path, original: bytes, written: bytes | None) -> None:
    """원래 바이트를 되쓴다. 쓴 변이 바이트(`written`)가 있는데 파일이 그것과 다르면 덮지 않고
    `_WrittenMeanwhile`."""
    if written is not None and path.read_bytes() != written:
        raise _WrittenMeanwhile
    path.write_bytes(original)
    _drop_bytecode(path)


def _restore(root: Path, name: str, held: dict[Path, bytes], written: dict[Path, bytes]) -> None:
    """쥔 파일을 모두 되쓰고, 남은 파일이 있으면 그 뒤에 `RestoreError`."""
    stuck: list[str] = []
    for path, original in held.items():
        relative = path.relative_to(root.resolve()).as_posix()
        try:
            _restore_file(path, original, written.get(path))
        except _WrittenMeanwhile:
            stuck.append(f"{relative} (변이가 든 동안 다른 쓰기가 들어와 덮지 않았다)")
        except OSError as error:
            stuck.append(f"{relative} ({error})")
    if stuck:
        raise RestoreError(f"{name}: {', '.join(stuck)}")


def _run_mutated(root: Path, spec: Spec, mutation: Mutation, runner: Runner) -> list[CommandResult]:
    files = _mutated(root, mutation)
    rewritable = [(root / relative).resolve() for relative in mutation.restore]
    held = {path: original for path, (original, _) in files.items()}
    for path in rewritable:
        held.setdefault(path, path.read_bytes())
    written: dict[Path, bytes] = {}  # 쓰기가 끝난 변이 바이트. 되돌릴 파일은 넣지 않는다
    try:
        for path, (_, mutated) in files.items():
            path.write_bytes(mutated)
            _drop_bytecode(path)
            if path not in rewritable:
                written[path] = mutated
        results: list[CommandResult] = []
        tests = mutation.tests
        if mutation.expect == "red" and _runners(spec)[mutation.runner].judge == "pytest":
            tests = [*tests, "-x"]  # 빨강은 실패 하나로 정해진다(독스트링의 하는 일 3)
        for _ in range(mutation.repeat):
            result = _invoke(root, spec, mutation.runner, tests, mutation.timeout, runner)
            results.append(result)
            if result.timed_out_after is not None:
                break  # 끊긴 판정은 이미 기대와 어긋나, 남은 반복은 변이를 든 채 시간만 쓴다
        return results
    finally:
        _restore(root, mutation.name, held, written)


def _missing(result: CommandResult, markers: Sequence[str]) -> list[str]:
    """색 코드를 벗긴 출력에 없는 표지."""
    text = result.plain
    return [marker for marker in markers if marker not in text]


def _details(
    judged: Sequence[tuple[CommandResult, Verdict]],
    out: Callable[[str], None],
    markers: Sequence[str] = (),
) -> None:
    """빨간 테스트의 이름, 그리고 빨강도 초록도 아니거나 표지가 없으면 출력의 끝."""
    for name in dict.fromkeys(name for _, verdict in judged for name in verdict.failed):
        out(f"   {name}")
    for result, verdict in judged:
        missing = _missing(result, markers)
        if missing:
            out(f"   표지 없음: {', '.join(missing)}")
        if verdict.outcome in ("error", "unhandled") or missing:
            for line in result.plain.splitlines()[-10:]:
                out(f"   | {line}")


def check(spec: Spec, *, root: Path, out: Callable[[str], None]) -> int:
    """원문만 본다. 명령을 돌리지 않는다. 모두 맞으면 0, 하나라도 틀리면 틀린 것을 모두 알리고 2."""
    problems = _file_problems(root, spec)
    for problem in problems:
        out(f"!! {problem}")
    if problems:
        out(f"원문 확인: 변이 {len(spec.mutation)} 중 문제 {len(problems)}")
        return 2
    out(f"원문 확인: 변이 {len(spec.mutation)} 모두 원문이 한 번씩 있다")
    return 0


def measure(
    spec: Spec,
    *,
    root: Path,
    runner: Runner,
    out: Callable[[str], None],
    numbers: Mapping[str, int] | None = None,
) -> int:
    """기준선을 재고 변이를 하나씩 넣어 돌린다. 모두 기대대로면 0, 아니면 1. `numbers` 는 줄 머리와
    `다시 돌릴 번호` 에 다는 표의 번호이고, 없으면 `spec` 안의 차례다. 그래서 `select` 로 좁힌
    `spec` 을 넘기는 쪽은 원본 표의 번호(`_numbers(원본)`)를 함께 넘긴다. 넘기지 않으면 번호가
    원본과 어긋나 다시 돌릴 번호가 다른 변이를 가리킨다(`main` 이 그렇게 넘긴다)."""
    _validate(root, spec)
    if numbers is None:
        numbers = _numbers(spec)

    # 기준선은 러너와 인자의 짝마다 한 번이고, 그 짝을 쓰는 변이 가운데 가장 긴 제한을 받는다
    baselines: dict[tuple[str, tuple[str, ...]], int] = {}
    for m in spec.mutation:
        key = (m.runner, tuple(m.tests))
        baselines[key] = max(baselines.get(key, 0), m.timeout)
    baseline_green = True
    for (name, tests), timeout in baselines.items():
        command = _runners(spec)[name]
        result = _invoke(root, spec, name, tests, timeout, runner)
        verdict = judge(command.judge, result, red_exit=command.red_exit)
        missing = _missing(result, command.baseline_output)
        absent = f" — 표지 없음: {', '.join(missing)}" if missing else ""
        out(
            f"기준선 {' '.join((name, *tests))}: {_LABELS[verdict.outcome]}"
            f" — {verdict.summary}{absent}"
        )
        if verdict.outcome != "green" or missing:
            _details([(result, verdict)], out)
            baseline_green = False
    if not baseline_green:
        out("기준선이 초록이 아니라 변이를 넣지 않았다. 빨간 기준선 위의 빨강은 재는 것이 없다")
        return 1

    mismatched: list[str] = []
    for mutation in spec.mutation:
        command = _runners(spec)[mutation.runner]
        results = _run_mutated(root, spec, mutation, runner)
        judged = [
            (
                result,
                judge(command.judge, result, mutation.diagnostic_in, red_exit=command.red_exit),
            )
            for result in results
        ]
        outcomes = ", ".join(_LABELS[verdict.outcome] for _, verdict in judged)
        matched = all(
            verdict.outcome == mutation.expect and not _missing(result, mutation.expect_output)
            for result, verdict in judged
        )
        head = "==" if matched else "!! 어긋남 —"
        out(
            f"{head} {numbers[mutation.name]}. {mutation.name}: 기대 {_LABELS[mutation.expect]},"
            f" 결과 {outcomes} — {judged[-1][1].summary}"
        )
        _details(judged, out, mutation.expect_output)
        if not matched:
            mismatched.append(mutation.name)

    if mismatched:
        labels = _labelled(mismatched, numbers)
        out(f"변이 {len(spec.mutation)} 중 어긋남 {len(mismatched)}: {labels}")
        out(f"다시 돌릴 번호: {' '.join(str(numbers[name]) for name in mismatched)}")
        return 1
    out(f"변이 {len(spec.mutation)} 모두 기대대로")
    return 0


def _kill_tree(process: subprocess.Popen[str]) -> None:
    """자식과 그 자식이 띄운 프로세스를 끝낸다. 윈도우는 `taskkill /T` 가 부모를 따라 찾고, POSIX 는
    자식이 이끄는 프로세스 그룹을 끝낸다(못 보는 것은 모듈 독스트링). `taskkill` 을 띄우지 못했거나
    시간을 넘겼어도, 그룹을 끝내지 못했어도 자식은 끝낸다."""
    if sys.platform == "win32":
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                capture_output=True,
                check=False,
                timeout=_KILL_SECONDS,
            )
    else:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
    process.kill()


def _drain(process: subprocess.Popen[str]) -> str:
    """끊은 뒤 남은 출력. 끝내지 못한 프로세스가 출력 파이프를 쥐고 있으면 `_DRAIN_SECONDS` 뒤에
    그만 읽는다."""
    try:
        stdout, stderr = process.communicate(timeout=_DRAIN_SECONDS)
    except subprocess.TimeoutExpired:
        return (
            f"(출력 파이프가 {_DRAIN_SECONDS}초 안에 닫히지 않아 그만 읽었다."
            " 끝내지 못한 프로세스가 남았을 수 있다)"
        )
    return stdout + stderr


def run_command(argv: Sequence[str], cwd: Path, timeout: int) -> CommandResult:
    """셸을 거치지 않는다. 윈도우의 `pnpm.CMD` 처럼 PATHEXT 로 찾는 이름은 `shutil.which` 가 풀고,
    그런 배치 파일은 cmd.exe 가 돌린다(독스트링의 못 보는 것). 시간 제한을 넘기거나 기다리는 동안
    예외(`KeyboardInterrupt` 등)가 올라오면 자식이 띄운 프로세스까지 끝낸다(`_kill_tree`)."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
    # `with` 로 열지 않는다. 그만 읽은 뒤 `with` 를 빠져나오면(파이프를 닫고 자식을 기다린다) 이
    # 윈도우 에서 남은 손자가 끝날 때까지 멈췄다(`test_못_보는_것_고아가_…`). 다 읽은 파이프는
    # `communicate` 가 닫는다
    process = subprocess.Popen(
        [shutil.which(argv[0]) or argv[0], *argv[1:]],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        start_new_session=True,  # POSIX 에서 자식이 제 프로세스 그룹을 이끈다. 윈도우는 무시한다
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(process)
        output = _drain(process)
        return CommandResult(process.wait(), output, timed_out_after=timeout)
    except BaseException:
        _kill_tree(process)
        raise
    return CommandResult(process.returncode, stdout + stderr)


def _check_files(paths: Sequence[str], *, root: Path, out: Callable[[str], None]) -> int:
    """변이 파일 여럿의 원문을 본다. 줄마다 앞에 그 파일의 경로를 붙이고, 읽지 못한 파일이 있어도
    나머지를 본다. 모두 맞으면 0, 하나라도 틀리면 2."""
    code = 0
    for path in paths:
        lines: list[str] = []
        try:
            code = max(code, check(read_spec(Path(path)), root=root, out=lines.append))
        except SpecError as error:
            lines.append(f"!! 변이 파일 오류: {error}")
            code = 2
        # 변이 파일 오류는 문제를 줄바꿈으로 잇는다. 줄마다 붙여야 둘째 줄의 출처가 보인다
        for line in "\n".join(lines).splitlines():
            out(f"{path}: {line}")
    return code


class _UsageError(Exception):
    """인자를 잘못 줬다. 아무 파일도 읽기 전에 난다."""


@dataclass(frozen=True)
class _Args:
    """가른 인자. `tables` 의 첫째가 돌리거나 볼 변이 파일이고, 여럿은 `--check` 에서만 온다."""

    checking: bool
    tables: list[str]
    picks: list[str]  # 이름이나 번호
    since: str | None


def _parse(argv: Sequence[str]) -> _Args:
    """인자를 가른다. 틀렸으면 알릴 말을 든 `_UsageError`."""
    checking = "--check" in argv
    rest = [arg for arg in argv if arg != "--check"]
    since: str | None = None
    if "--since" in rest:
        at = rest.index("--since")
        value = rest[at + 1] if at + 1 < len(rest) else "--"
        if value.startswith("--") or rest.count("--since") > 1:
            raise _UsageError("--since 뒤에는 커밋(브랜치, 태그, 해시) 하나를 한 번만 준다")
        since = value
        rest = rest[:at] + rest[at + 2 :]
    flags = [arg for arg in rest if arg.startswith("--")]
    if flags:
        raise _UsageError(
            f"모르는 선택: {', '.join(flags)}. 아는 것은 --check 와 --since <커밋> 이다"
        )
    if not rest:
        raise _UsageError(__doc__ or "")
    spec_path, *picks = rest
    more_tables = [pick for pick in picks if pick.endswith(".toml")]
    if more_tables and (not checking or len(more_tables) != len(picks) or since is not None):
        raise _UsageError(
            "변이 파일 여럿은 --check 로만 받고 이름·번호·--since 와 섞지 않는다."
            " 변이는 표 하나씩 돌린다"
        )
    if more_tables:
        return _Args(checking, [spec_path, *more_tables], [], since)
    return _Args(checking, [spec_path], picks, since)


def _since_picks(spec: Spec, args: _Args) -> list[str]:
    """`--since` 가 고른 이름. 주지 않았으면 없다. 이름·번호도 없이 고른 것이 없으면
    `SpecError` — 잘못 준 커밋이 0 으로 끝나면 잰 것처럼 보인다."""
    if args.since is None:
        return []
    fresh = changed_since(Path(args.tables[0]), spec, args.since)
    if not fresh and not args.picks:
        raise SpecError(
            f"--since {args.since}: 그 커밋 뒤로 바뀌거나 더한 변이가 없다. 돌릴 것이 없다"
        )
    return fresh


def main(
    argv: Sequence[str],
    *,
    root: Path = ROOT,
    runner: Runner = run_command,
    out: Callable[[str], None] = print,
) -> int:
    try:
        args = _parse(argv)
    except _UsageError as error:
        out(str(error))
        return 2
    if args.checking and not args.picks and args.since is None:
        return _check_files(args.tables, root=root, out=out)
    try:
        spec = read_spec(Path(args.tables[0]))
        fresh = _since_picks(spec, args)
        if args.since is not None:
            listed = f" — {_labelled(fresh, _numbers(spec))}" if fresh else ""
            out(f"--since {args.since}: 바뀌거나 더한 변이 {len(fresh)}{listed}")
        selected = select(spec, [*args.picks, *fresh])
        if args.checking:
            return check(selected, root=root, out=out)
        return measure(selected, root=root, runner=runner, out=out, numbers=_numbers(spec))
    except SpecError as error:
        out(f"변이 파일 오류(아무 파일도 쓰지 않았다): {error}")
        return 2
    except RestoreError as error:
        out(f"되돌리지 못했다. 남은 파일을 git diff 로 보고 변이만 걷어 낸다: {error}")
        if error.__context__ is not None:  # finally 에서 던져 가린, 그 전에 난 예외
            out(f"되돌리기 전에 난 예외: {error.__context__!r}")
        return 3
    except OSError as error:
        out(f"테스트를 돌리지 못했다(변이는 되돌렸다): {error}")
        return 3


if __name__ == "__main__":
    # pre-commit 훅 환경에 PYTHONUTF8 이 있다고 가정하지 않는다. 없으면 윈도우의 파이프는 cp949 다.
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
