# CI python 잡의 시간 제한 여유를 대기열 항목으로 올린다

PR #624를 병합하는 길에서 CI `python` 잡이 15분 제한에 두 번 연속 걸렸다. 병합을 마친 뒤 사용자에게 이 일을 대기열 항목으로 올릴지 물었고, 답을 받아 이 브랜치(`chore/ci-python-job-timeout-margin`)에서 항목만 쓴다. 고치는 일은 없다.

> 사용자: 네, 올려 주세요

## 한 일

- `.scratch/retro-queue/ci-python-job-timeout-margin.md`를 새로 썼다(처음 쓸 때 회차 1, 이 PR의 CI 취소로 2회차).
- 항목 찾기: `queue_open_rows.py --search`로 `timeout-minutes|시간 제한|15분`과 `ci_job_durations`·`14.3`을 쳤다. 맞은 닫힌 항목 0204·0477·0581을 열어 처방까지 대 봤다. 0477·0581은 단계가 멈춘 일이고 이번은 멈추지 않은 느림이라 따로 센다.
- harness 티켓 `.scratch/harness/issues/ci-python-job-timeout-margin.md`를 썼다.

## 근거

- PR #624의 `python` 잡(실행 45040618565, 시도별로 `gh api .../attempts/<시도>/jobs`의 시각을 손으로 뺐다): 시도 1은 pytest 단계가 13분 48초에 통과한 뒤 `check_instructions.py` 단계에서 잡이 15분에 취소됐고, 시도 2는 pytest 13분 54초 뒤 `check_type_escapes.py` 단계에서 취소됐다. 실패한 잡만 다시 돌린(`gh run rerun 45040618565 --failed`) 시도 3은 잡 12분 34초(pytest 11분 20초)로 지났다. 처음 항목을 쓸 때는 "pytest 단계가 취소됐다"고 적었고, PR 직전 CodeRabbit CLI 리뷰가 잡은 뒤 위 값으로 고쳤다.
- 앞선 언급 둘이 대기열에 오르지 않았다: 일지 `2026-11-17-1555-release-followup-timeouts-and-failure-table.md`(최대 14.3분, 제한의 1.05배, "후속 티켓이 필요하다")와 `2026-11-20-1407-standalone-compose-adds-postgres.md`(한 번 취소, 앞 dev 실행도 14분 35초).

## PR 직전 리뷰

CodeRabbit CLI 0.7.5(`Seat: not assigned`, Free)가 `review_completed`까지 돌았고 findings 1건을 냈다. 서브에이전트가 `gh api`로 직접 대 보고 둘을 유효로 판정했다.

- Major: 항목 머리와 티켓·일지의 근거가 "pytest 단계가 취소됐다"고 적었으나, pytest는 두 번 통과했고 그다음의 가벼운 검사 단계에서 잡이 잘렸다. "평소 13~14.5분"도 근거가 약했다(세 시도가 12.6분에서 15분 넘게). 이 세션이 `gh api .../attempts/1/jobs`로 시도 1의 취소 단계(`check_instructions.py`)를 다시 확인했고 세 곳을 고쳤다.
- Minor: 어디로 줄의 `tools/run_checks.py`와 프로브 경로가 괄호 밖이라 도구가 고칠 대상으로 센다. 두 경로를 괄호 안으로 옮겼다.
- 오탐 둘(0477·0581의 상태가 `만료`인데 닫힌 것으로 센 것, 티켓이 `done`인 것)은 도구의 셈과 규약대로라 그대로 뒀다.

## PR 봇 회차

- CodeRabbit 첫 회차(Minor 1): 항목의 `어디로` 줄이 프로브로 "단계별 소요 시간"을 재라고 했는데 `ci_job_durations.py`는 잡마다 전체 시간 하나만 낸다. 코드를 열어 맞는 것을 확인했고(`minutes`가 잡의 `started_at`~`completed_at`만 계산한다) 줄을 고쳐, 프로브는 잡 전체 시간, 단계별 시간은 `gh api .../attempts/<시도>/jobs`로 읽는다고 적었다.
- claude-review 첫 회차: 지적 없음.
- 이 PR의 CI `python` 잡도 15분 제한에 걸려 취소돼 `verify`가 빨갰고(실행 45103816619), 실패한 잡만 다시 돌렸다. 같은 신호가 PR #624에 이어 한 번 더 난 것이다. 다른 PR에서 같은 사건이 또 난 것이라 항목의 회차를 2회차로 올렸다(`queue_open_rows.py`가 읽는 승인 줄에 적었다).

## 회고

- 후보 1: `python` 잡 시간 제한의 여유를 대기열 항목으로 올린다. **넘김 후 승인**: 처방 가운데 제한을 올리는 길이 가드레일을 느슨하게 하는 쪽이라 넘김이고, 사용자가 올리라고 답했다. 항목은 어느 길을 고를지 정하지 않고 재는 데부터 시작한다. 사건은 위 PR #624의 두 번 연속 취소다. 항목: `ci-python-job-timeout-margin`(회차 1에서 시작해 PR #625의 취소로 2).
- 후보 2: 병합 전에 CI 취소가 시간 제한인지 코드인지 가르는 스킬 단계. **기각**: 이번에 `gh run view`의 단계 시각으로 바로 갈랐고, 사건이 하나다.
- 만료할 항목: `queue_open_rows.py`의 "만료할 항목"을 이 세션에서는 돌리지 않았다. 이 브랜치의 몫이 아니라 항목 하나를 더하는 일이라서다.

## 다음

대기열의 이 항목은 열림이고 회차 2이다. 다음은 앞서 낸 티켓 02(`.scratch/connection-check/issues/02-check-mcp-servers-remote-and-stdio.md`)와 03(`03-check-models-by-provider.md`)을 나란히 여는 것이다. 지시문은 `docs/journal/2026-11-22-1335-connection-check-01-contract.md`의 "## 다음"과 그 세션 보고에 있다.
