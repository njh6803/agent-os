# ci-python-job-timeout-25: CI python 잡의 시간 제한을 15분에서 25분으로 올린다

**What to build:** CI `python` 잡(`.github/workflows/ci.yml`)이 2026-11-24에 15분 제한에 걸려 잇달아 취소됐다. PR #633의 실행 45390683089는 pytest 단계(8136 passed, 813.63초)와 그다음 `check_instructions.py` 단계를 지난 뒤 `check_type_escapes.py` 단계에서 취소됐고, 실행 45396000251은 두 시도가 모두 pytest 단계 도중에 취소됐다. dev 푸시의 실행 45388134923도 같은 이유로 취소돼 dev의 CI가 빨갰다. 대기열 `ci-python-job-timeout-margin`이 넘긴 두 길(pytest를 잡 둘로 나누기, 제한 올리기) 가운데 사용자가 제한을 25분으로 올리는 길을 골랐다(일지 `docs/journal/2026-11-24-2227-ci-python-job-timeout-25.md`에 원문). 이 PR은 그 값을 넣고, 근거 프로브를 다시 돌려 README 행에 적고, 대기열 항목을 닫는다.

**대기열:** ci-python-job-timeout-margin

**Status:** done

## 수용 기준

- [x] `python` 잡의 `timeout-minutes`가 25이고, 그 잡의 주석이 까닭(잰 최대, 머리 주석의 네 배 규칙과 다른 값을 사용자가 고른 것, 프로브가 취소된 실행을 세지 않는 것)을 적는다
- [x] `ci.yml` 머리 주석이 2026-11-24에 잰 잡 가운데 네 배에 못 미치는 잡을 바로 적는다
- [x] 프로브 `.scratch/harness/probes/ci_job_durations.py`를 다시 돌린 결과를 `.scratch/harness/probes/README.md`의 그 프로브 행에 적는다
- [x] 대기열 `ci-python-job-timeout-margin`의 상태 줄이 이 티켓으로 닫힌다
- [x] 검증 명령이 모두 초록이다(`uv run python tools/run_checks.py` 종료 0, ruff 둘. zizmor는 pre-commit이 돌린다)
- [x] PR 본문 "남긴 위험"에 정말로 멈춘 잡을 10분 늦게 끊게 된다는 것과 25분이면 충분하다는 것이 어림이라는 것을 적는다

## 확인한 근거 (2026-11-24)

- 프로브 출력(`ci_job_durations.py 40`)과 지금 제한과의 배수는 `.scratch/harness/probes/README.md`의 그 프로브 행에 있다.
- 취소된 실행의 시각은 `gh run view`와 잡 시각으로 손으로 읽었다(일지 `docs/journal/2026-11-24-2227-ci-python-job-timeout-25.md`의 근거 절).
- 시험 가운데 `timeout-minutes` 값을 단언하는 것은 없다(`tests/`를 grep했다).
