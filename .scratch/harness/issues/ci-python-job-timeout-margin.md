# ci-python-job-timeout-margin: CI python 잡의 시간 제한 여유 문제를 대기열 항목으로 올린다

**What to build:** PR #624(티켓 `connection-check` 01)의 CI에서 `python` 잡이 15분 제한에 두 번 연속 걸려 취소되고 `verify`가 빨갰다(실행 45040618565). pytest 단계는 두 번 모두 통과했고 그다음의 가벼운 검사 단계에서 잡이 잘렸다. 코드가 원인이 아니었고 실패한 잡만 다시 돌린 세 번째는 잡 12분 34초에 지났다. 같은 잡이 앞서 2026-11-17(최대 14.3분이 제한에 닿음)과 2026-11-20(한 번 취소)에도 같은 신호를 냈으나 대기열에 오르지 않았다. 사용자가 올리라고 답해(2026-11-23), 대기열 항목 하나를 쓴다. 고치는 일은 이 티켓에 없다. 항목이 처방과 회차 기준(다섯 번째)을 든다.

**대기열:** ci-python-job-timeout-margin

**Status:** done

## 수용 기준

- [x] `.scratch/retro-queue/ci-python-job-timeout-margin.md`가 상태·어디로·승인 줄을 이 차례로 갖는다
- [x] 항목을 쓰기 전에 `tools/queue_open_rows.py --search`로 같은 일을 다룬 항목을 찾아 0581·0477·0204를 열어 대 봤고, 원인이 달라(멈춤 대 느림) 따로 센다고 승인 줄에 적었다
- [x] 일지 `docs/journal/2026-11-23-1135-ci-python-job-timeout-margin.md`가 근거와 사용자의 답 원문을 적는다
- [x] 검증 명령이 모두 초록이다(저장소 상태 시험이 항목 모양을 본다)

## 확인한 근거 (2026-11-23)

- 실행 45040618565를 시도별로 `gh api repos/<저장소>/actions/runs/<실행>/attempts/<시도>/jobs`로 읽었다(시각을 손으로 뺐다. 프로브로 다시 재지는 않았다). 시도 1은 잡 15분 04초에 취소됐고 pytest 단계가 13분 48초에 통과한 뒤 `check_instructions.py` 단계에서 잘렸다. 시도 2는 pytest 13분 54초 뒤 `check_type_escapes.py` 단계에서 잘렸다. 시도 3은 잡 12분 34초(pytest 11분 20초)로 지났다. 최대 14.3분은 앞 일지의 프로브 출력이다.
