"""워크트리 세션의 명령 하나가 워크트리 밖에 파일을 쓰고 지울 수 있는지, 주 체크아웃의 `.env` 를
넘긴 환경에 변수의 이름이 실리는지를 본다. ADR 0058 이 돌려 보지 않았다고 적은 것 가운데 클라우드
없이 볼 수 있는 둘이다.

    uv run python .scratch/local-model/probes/outside_worktree.py
    uv run --env-file ../../../.env python <같은 경로> --env-file

첫 명령은 사용자 홈 아래에 이 프로브만 쓰는 이름의 폴더를 만들어 파일 하나를 쓰고 읽은 뒤 둘 다
지운다. 로컬 모델 시험의 상태 파일이 설 자리(명세의 "상태 폴더")와 같은 종류의 경로다. 표지는 읽어
돌아온 글이 쓴 글과 같고 그 자리가 작업 폴더 밖이라는 것이다. 첫 명령은 둘째 명령의 음성 대조도
함께 본다. `--env-file` 없이 띄운 환경에 `ANTHROPIC_API_KEY` 가 없어야 한다. 있으면 그 변수는 세션의
환경에 원래 있던 것이라 둘째 명령의 표지가 되지 못하므로, 그 회차를 측정 아님으로 센다.

둘째 명령은 같은 일에 더해 `.env` 가 준 환경을 본다. `--env-file` 이 실제로 들었다는 표지는
`ANTHROPIC_API_KEY` 가 환경에 있다는 것이다(`docs/constitution/operations.md` 의 LLM 테스트 절이 그
파일에 있다고 적는 이름이다). 그 표지가 없으면 그 회차는 측정이 아니다. 이 표지는 첫 명령의 음성
대조가 측정이었을 때만 "`--env-file` 이 넘겼다"는 뜻이다. `RUNPOD_API_KEY` 는 있는지만 찍는다.
사용자가 준비했는지를 보는 값이고 없다고 측정이 깨진 것은 아니다.

찍는 것은 참·거짓과 이름뿐이다. 값은 읽어 견주지도 찍지도 않고, 홈의 경로도 찍지 않는다.

이 프로브는 명령이 훅과 데스크톱 앱의 가드를 지나 실제로 돌았다는 것까지만 본다. 가드는 같은
모양의 명령에도 결과가 갈린 적이 있어(`CLAUDE.md` 환경 함정) 한 번 지난 것이 언제나 지난다는
뜻은 아니다.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.probe_kit import Rounds  # noqa: E402

ENV_FILE_MARKER = "ANTHROPIC_API_KEY"
PREPARED_BY_USER = "RUNPOD_API_KEY"


def _writes_outside() -> tuple[bool, bool]:
    """(홈 아래에 쓰고 읽고 지웠다, 그 자리가 작업 폴더 밖이다)."""
    home = Path.home().resolve()
    here = Path.cwd().resolve()
    folder = home / f".agent-os-probe-{uuid.uuid4().hex}"
    state = folder / "terraform.tfstate"
    folder.mkdir()
    try:
        state.write_text("{}", encoding="utf-8")
        read_back = state.read_text(encoding="utf-8") == "{}"
    finally:
        state.unlink(missing_ok=True)
        folder.rmdir()
    outside = not folder.is_relative_to(here) and not here.is_relative_to(home)
    return read_back and not folder.exists(), outside


def main(argv: list[str]) -> int:
    rounds = Rounds()
    with rounds.round("워크트리 밖 쓰기") as slot:
        wrote, outside = _writes_outside()
        print(f"홈 아래에 쓰고 읽고 지웠다: {wrote}")
        print(f"그 자리가 작업 폴더 밖이다: {outside}")
        slot.mark(measured=wrote and outside, result="썼다" if wrote else "쓰지 못했다")
    if "--env-file" in argv:
        with rounds.round("env-file 로 넘긴 환경") as slot:
            applied = ENV_FILE_MARKER in os.environ
            prepared = PREPARED_BY_USER in os.environ
            print(f"환경에 {ENV_FILE_MARKER}: {'있다' if applied else '없다'}")
            print(f"환경에 {PREPARED_BY_USER}: {'있다' if prepared else '없다'}")
            slot.mark(
                measured=applied,
                result=f"{PREPARED_BY_USER} {'있다' if prepared else '없다'}",
            )
    else:
        with rounds.round("env-file 없이 본 환경(음성 대조)") as slot:
            already = ENV_FILE_MARKER in os.environ
            print(f"env-file 없이 환경에 {ENV_FILE_MARKER}: {'있다' if already else '없다'}")
            slot.mark(measured=not already, result="있다" if already else "없다")
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
