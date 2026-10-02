"""훅 등록의 실행 래퍼. 인자로 받은 이름의 훅 파일이 이 파일 옆(`tools/`)에 없으면 막지 않고 0으로
끝나고, 있으면 같은 프로세스에서 그 훅을 `__main__` 으로 돌린다.

등록이 `python "${CLAUDE_PROJECT_DIR}/tools/<훅>.py"` 꼴이던 때는 훅 파일이 없으면 파이썬이 2로
끝났다. PreToolUse 에서 2는 "막아라"라 그 매처의 모든 호출이 막혔다(2026-09-29 실측). PR #120
세션이 다시 시작되며 워크트리의 settings.json(새 훅의 등록)을 싣고 `${CLAUDE_PROJECT_DIR}` 은 그
파일이 없는 주 체크아웃을 가리켜 Bash·PowerShell 이 전부 막혔다(대기열 91, 일지 2026-10-02-01).
새 훅을 병합한 뒤 주 체크아웃을 당기지 않은 채 워크트리에서 다시 시작한 세션도 같다. 이제 그 자리의
훅은 없는 것처럼 지나간다. `claude -p` 세션에서 없는 훅을 옛 모양으로 더하면 Bash 가 막혔고 이
래퍼로 더하면 돌았다(2026-10-02, `.scratch/harness/probes/hook_registration/run.sh`).

등록 명령의 모양은 그대로이고 스크립트 자리에 이 파일이, 끝에 훅 이름이 온다. 셸 문법(`[ -f … ]`)을
더하지 않으므로 등록이 셸에 기대는 몫(`${CLAUDE_PROJECT_DIR}` 의 전개와 따옴표)은 래퍼 전과 같다.
모양은 `tools/run_hooks.py` 가 대조한다. 래퍼는 훅 한 번에 약 10ms 를 더한다(2026-10-02,
`.scratch/harness/probes/hook_registration/time_launch.sh`).

훅이 있으면 종료 코드와 stdin·stdout 은 훅을 바로 돌릴 때와 같다. 훅 안의 예외도 1(막지 않는
오류)로 끝나지만, stderr 의 traceback 에는 래퍼와 runpy 의 프레임이 더해진다. 훅이 보는 `__name__`
은 `__main__` 이고, `__file__`·`sys.argv[0]` 은 같은 훅 파일을 가리키며(구분자 문자열은 다를 수
있다 — 지금 훅은 둘 다 쓰지 않는다), `sys.path[0]` 은 둘 다 `tools/` 다.

못 보는 것:
- 이 파일 자체가 없을 때. 그때는 예전처럼 파이썬이 2로 끝나고, 등록 열하나가 모두 그렇다. 2의 효과는
  이벤트마다 다르다 — PreToolUse 는 그 매처의 호출을 막고, UserPromptSubmit·Stop 도 2를 막기로
  읽는다(공식 hooks 문서, 재지 않았다). 주 체크아웃이 이 파일을 들인 커밋보다 뒤에 있으면 그렇다.
  이 파일을 들이는 PR 이 병합된 뒤 주 체크아웃을 당기기 전, 주 체크아웃이 그보다 앞서 딴 브랜치에
  있을 때, 이 파일의 이름을 바꾼 뒤다. 그래서 이 파일을 들인 PR 은 병합 직후 주 체크아웃을 당긴다.
- 훅 파일은 있지만 그 판이 등록과 맞지 않는 것(주 체크아웃의 옛 훅이 새 등록의 이벤트로 도는 것).
- 지나간 것을 세션에 알리지 않는다. stderr 에 한 줄을 남길 뿐이고(stdout 은 비어 러너는 침묵으로
  읽는다), 종료 0의 stderr 가 모델이나 사용자에게 보이는지는 재지 않았다. 그 훅이 꺼진 것을 세션이
  모를 수 있다.
"""

from __future__ import annotations

import os
import runpy
import sys

# pathlib 을 쓰지 않는다. pathlib 을 import 하지 않는 훅에서 그 import 가 훅 한 번에 약 8ms 를
# 더했다(손으로 견줬다, 일지 2026-10-02-02).
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))


def hook_path(argv: list[str]) -> str | None:
    """`argv` 의 훅 이름이 가리키는 `tools/` 의 파일. 이름이 하나가 아니거나 파일이 없으면 None."""
    if len(argv) != 2:
        return None
    path = os.path.join(TOOLS_DIR, argv[1])
    return path if os.path.isfile(path) else None


def main() -> int:
    path = hook_path(sys.argv)
    if path is None:
        sys.stderr.write(f"launch_hook: 훅 파일이 없어 지나간다: {sys.argv[1:]}\n")
        return 0
    sys.argv = [path]
    runpy.run_path(path, run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
