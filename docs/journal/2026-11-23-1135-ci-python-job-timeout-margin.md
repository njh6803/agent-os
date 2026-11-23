# CI python 잡의 시간 제한 여유를 대기열 항목으로 올린다

PR #624를 병합하는 길에서 CI `python` 잡이 15분 제한에 두 번 연속 걸렸다. 병합을 마친 뒤 사용자에게 이 일을 대기열 항목으로 올릴지 물었고, 답을 받아 이 브랜치(`chore/ci-python-job-timeout-margin`)에서 항목만 쓴다. 고치는 일은 없다.

> 사용자: 네, 올려 주세요

## 한 일

- `.scratch/retro-queue/ci-python-job-timeout-margin.md`를 새로 썼다(회차 1).
- 항목 찾기: `queue_open_rows.py --search`로 `timeout-minutes|시간 제한|15분`과 `ci_job_durations`·`14.3`을 쳤다. 맞은 닫힌 항목 0204·0477·0581을 열어 처방까지 대 봤다. 0477·0581은 단계가 멈춘 일이고 이번은 멈추지 않은 느림이라 따로 센다.
- harness 티켓 `.scratch/harness/issues/ci-python-job-timeout-margin.md`를 썼다.

## 근거

- PR #624의 `python` 잡: 두 시도 모두 pytest 단계 13분 48초와 13분 54초에서 잡이 15분에 취소됐고(`gh run view`의 시각을 손으로 읽었다), 실패한 잡만 다시 돌린(`gh run rerun 45040618565 --failed`) 세 번째에 지났다.
- 앞선 언급 둘이 대기열에 오르지 않았다: 일지 `2026-11-17-1555-release-followup-timeouts-and-failure-table.md`(최대 14.3분, 제한의 1.05배, "후속 티켓이 필요하다")와 `2026-11-20-1407-standalone-compose-adds-postgres.md`(한 번 취소, 앞 dev 실행도 14분 35초).

## 회고

- 후보 1: `python` 잡 시간 제한의 여유를 대기열 항목으로 올린다. **넘김 후 승인**: 처방 가운데 제한을 올리는 길이 가드레일을 느슨하게 하는 쪽이라 넘김이고, 사용자가 올리라고 답했다. 항목은 어느 길을 고를지 정하지 않고 재는 데부터 시작한다. 사건은 위 PR #624의 두 번 연속 취소다. 항목: `ci-python-job-timeout-margin`(회차 1).
- 후보 2: 병합 전에 CI 취소가 시간 제한인지 코드인지 가르는 스킬 단계. **기각**: 이번에 `gh run view`의 단계 시각으로 바로 갈랐고, 사건이 하나다.
- 만료할 항목: `queue_open_rows.py`의 "만료할 항목"을 이 세션에서는 돌리지 않았다. 이 브랜치의 몫이 아니라 항목 하나를 더하는 일이라서다.

## 다음

대기열의 이 항목은 열림이고 회차 1이다. 다음은 앞서 낸 티켓 02(`.scratch/connection-check/issues/02-check-mcp-servers-remote-and-stdio.md`)와 03(`03-check-models-by-provider.md`)을 나란히 여는 것이다. 지시문은 `docs/journal/2026-11-22-1335-connection-check-01-contract.md`의 "## 다음"과 그 세션 보고에 있다.
