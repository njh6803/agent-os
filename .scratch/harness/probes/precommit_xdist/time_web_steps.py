"""web verify 의 여섯 단계를 차례로 따로 재서 JSON 한 줄씩 낸다(ADR 0035).

`pnpm -C web verify` 는 `&&` 로 여섯 단계를 차례로 잇는다(`web/package.json` 의 `verify`). 그
단계마다 걸리는 시간을 따로 본다. 단계 하나가 실패해도 다음 단계를 잰다. 단계마다 출력에서 그 단계가
돌았다는 표지를 찾는다. Prettier 와 Vitest 는 성공 요약 줄이 있고, 나머지(ESLint, tsc, 두 검사
스크립트)는 조용히 끝나 pnpm 이 찍는 명령 줄(`$ <명령>`)이 표지다. 표지가 없거나 종료 코드가 0 이
아닌 단계가 있으면 그 회차는 측정이 아니므로 종료 코드를 1 로 낸다(`.claude/rules/probes.md` 의 첫
항목). 단계의 원본 출력은 `results/web_steps_output.txt` 에 남긴다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/harness/probes/precommit_xdist/time_web_steps.py`. 출력은
`results/web_steps.jsonl`. `pnpm` 이 PATH 에 있어야 한다.

못 보는 것: 단계 안의 시간(Vitest 의 세 프로젝트별 시간). 같은 PC 에서 다른 세션이 CPU 를 쓰는 정도.
조용한 단계의 명령 줄은 그 단계가 시작했다는 표지일 뿐 검사가 끝까지 돌았다는 표지는 종료 코드 0
이다.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
# 단계 이름 -> 출력에서 찾을 표지(정규식). 순서는 `web/package.json` 의 verify 가 잇는 차례다.
MARKERS = {
    "check:api-client": re.escape("$ node tools/generate-api-client.ts --check"),
    "lint": re.escape("$ eslint --max-warnings 0"),
    "format": re.escape("All matched files use Prettier code style!"),
    "typecheck": re.escape("$ tsc --noEmit && pnpm -r exec tsc --noEmit"),
    "test": r"Tests\s+\d+ passed",
    "check:tsconfig": re.escape("$ node tools/check-tsconfig.ts"),
}
STEPS = tuple(MARKERS)


def main() -> int:
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        print(json.dumps({"error": "pnpm 을 찾지 못했다"}, ensure_ascii=False))
        return 1
    total = 0.0
    bad = False
    raw: list[str] = []
    for step in STEPS:
        start = time.monotonic()
        process = subprocess.run(
            [pnpm, "-C", "web", "run", step],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        seconds = time.monotonic() - start
        total += seconds
        marked = re.search(MARKERS[step], process.stdout) is not None
        bad = bad or process.returncode != 0 or not marked
        raw.append(f"===== {step} =====\n{process.stdout}")
        row = {
            "step": step,
            "seconds": round(seconds, 1),
            "returncode": process.returncode,
            "marked": marked,
        }
        print(json.dumps(row, ensure_ascii=False), flush=True)
    (HERE / "results" / "web_steps_output.txt").write_text("\n".join(raw), encoding="utf-8")
    print(json.dumps({"step": "합계", "seconds": round(total, 1)}, ensure_ascii=False), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
