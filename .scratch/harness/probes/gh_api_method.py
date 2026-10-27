"""대기열 408. `gh api` 가 옵션의 꼴마다 어느 HTTP 메서드로 요청하는지 잰다.
도움말(`gh api --help`)은 필드(`-f`·`-F`)가 있으면 POST 라고만 하고 `--input` 만 준 꼴은 말하지
않는다. `hook_pr_next_session` 과 `hook_handoff` 가 `gh api …/pulls` 를 PR 열기로 볼지 이 값으로
정한다.

회차. `GH_DEBUG=api` 를 켜고 `--hostname localhost`(이 PC 의 443 번 포트, 닫혀 있다)로
`repos/o/r/pulls` 를 부른다. 토큰은 가짜(`GH_ENTERPRISE_TOKEN`)다. 연결은 실패하지만 디버그 기록이
보내려던 요청 줄(`> <메서드> /api/v3/repos/o/r/pulls`)을 찍는다. 밖으로는 아무것도 나가지 않는다.

갈래. 필드 없음(GET 이어야 한다, 음성 대조), `-f`(POST, 양성 대조), `-X POST`(POST, 양성 대조),
`--input` 만, `--input` 과 `-X GET`, `-X=POST`(짧은 옵션에 `=` 를 붙인 꼴, PR 직전 리뷰).

표지. 출력에 그 요청 줄이 있고, 대조 갈래면 그 메서드가 기대(`CONTROLS`)와 같다. 아니면 그 회차는
측정이 아니다(`tools/probe_kit.py` 의 `Rounds`). 대조가 어긋나면 gh 판이나 디버그 기록의 꼴이 바뀐
것이라 다른 갈래의 값도 믿지 않는다.

쓰임: 저장소 루트에서 `PYTHONUTF8=1 uv run python .scratch/harness/probes/gh_api_method.py`.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

ENDPOINT = "repos/o/r/pulls"
REQUEST_LINE = re.compile(r"^> ([A-Z]+) /api/v3/repos/o/r/pulls\b", re.MULTILINE)
CONTROLS = {"필드 없음": "GET", "-f": "POST", "-X POST": "POST"}


def main() -> int:
    rounds = Rounds()
    environment = {
        **os.environ,
        "GH_DEBUG": "api",
        "GH_ENTERPRISE_TOKEN": "dummy",
        "GH_PROMPT_DISABLED": "1",
        "NO_COLOR": "1",
    }
    with tempfile.TemporaryDirectory(prefix="gh-api-method-") as folder:
        body = Path(folder) / "body.json"
        body.write_text('{"title": "x"}\n', encoding="utf-8")
        branches = {
            "필드 없음": [],
            "-f": ["-f", "title=x"],
            "-X POST": ["-X", "POST"],
            "--input 만": ["--input", str(body)],
            "--input 과 -X GET": ["--input", str(body), "-X", "GET"],
            "-X=POST": ["-X=POST"],
        }
        for label, options in branches.items():
            command = ["gh", "api", "--hostname", "localhost", *options, ENDPOINT]
            with rounds.round(label) as slot:
                done = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=environment,
                    timeout=60,
                    check=False,
                )
                found = REQUEST_LINE.search(done.stdout + done.stderr)
                expected = CONTROLS.get(label)
                if found is None:
                    slot.mark(measured=False, result=f"요청 줄 없음(종료 {done.returncode})")
                elif expected is not None and found.group(1) != expected:
                    slot.mark(measured=False, result=f"대조 어긋남: {found.group(1)} ≠ {expected}")
                else:
                    slot.mark(measured=True, result=f"{label} → {found.group(1)}")
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
