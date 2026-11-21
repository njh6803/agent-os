# ruff-format-hook-skips-staged-markdown: 명세 `.md`의 파이썬 코드 블록이 `ruff format` 모양과 달랐는데 커밋 둘의 pre-commit을 지나고, 병합한 뒤 손으로 친 저장소 전체 검사에서야 걸렸다

**상태:** 열림
**어디로:** pre-commit의 ruff 훅(`.pre-commit-config.yaml`): `ruff format --check`가 스테이지된 `.py`만 보므로, 스테이지된 `.md`도 넘겨 코드 블록을 보게 한다. 저장소 전체를 보는 `uv run ruff format --check .`는 `.md`까지 훑어(2521개 파일) 같은 곳을 짚는다. 먼저 훅이 `.md`를 넘겨도 되는지(`types_or`와 ruff의 마크다운 지원)를 재어 본다
**승인:** 자체 승인 2026-11-21, 0319의 3회차(0319가 닫혔고 2회차가 `.md` 안의 파이썬 코드 블록이었다), 일지 2026-11-21-0502-connection-check-spec.md. ADR 불필요

`.scratch/connection-check/spec.md`의 파이썬 코드 블록 하나(포트의 모양)에서 빈 줄 여섯 곳과 줄 나눔 한 곳이 `ruff format`의 모양과 달랐다. 명세를 커밋한 앞 세션들의 커밋 둘은 모두 지났고(커밋의 ruff 훅은 스테이지된 `.py`만 본다), 기준 브랜치를 합친 뒤 저장소 전체로 처음 친 `uv run ruff format --check .`가 짚었다. `uv run ruff format .scratch/connection-check/spec.md`로 고쳤다.
