# 04: CI가 PR마다 같은 판정을 하고 가리키는 티켓이 done인지 본다

**What to build:** PR을 열거나 푸시하면 CI의 새 잡이 커밋 검사와 같은 판정을 PR 단위로 하고, 가리키는 티켓의 `Status:`가 done이 아니면 빨갛다. 그래서 훅을 건너뛴 커밋도 PR에서 막히고, 티켓을 done으로 바꾸지 않고 연 PR은 세션이 done으로 바꿔 다시 푸시해야 초록이 된다(사용자가 고른 값). 면제 모양만 바꾼 PR과 규약 전에 딴 PR(전환)은 지난다. PR이 아닌 실행(main의 push)에서는 한 줄을 찍고 곧바로 지나, 필수 검사 `verify`가 빨개지지 않는다.

근거는 `.scratch/ticket-for-every-pr/spec.md`의 "CI"와 그 2026-10-21 명세 검토 주석, "쓰는 때와 상태"의 주석(PR을 열기 전에 done), Testing Decisions의 "CI 판정"과 그 주석, 사용자 스토리 7·8·9·27·38이다. 결정은 ADR 0037이다. 이 티켓은 헌법(`docs/constitution/operations.md`, `docs/constitution/tech.md`)을 고친다(`CLAUDE.md` 작업 규약 2).

이 티켓의 브랜치는 커밋 검사(03)가 든 main에서 따므로, 제 PR이 전환으로 지나지 않고 판정을 받는다. 그래서 다른 브랜치를 base로 둔 실험 draft PR은 두지 않고, 이 PR 자신이 draft 동안 빨강과 초록을 보인다(명세의 주석).

**Blocked by:** 03

**Status:** done

### 판정

- [x] **CI 입력.** 검사 도구(`tools/check_ticket.py`)가 PR의 머리 브랜치 이름, 머리 커밋, base 커밋을 환경 변수로 받으면 CI의 판정을 한다. 판정 전체의 기준은 `origin/main` 대신 base 커밋이고, 브랜치 이름과 HEAD는 그 머리 브랜치와 머리 커밋이 대신한다. 체크아웃한 병합 커밋은 분리 HEAD라 판정 1을 체크아웃으로 보지 않는다(보면 모든 PR이 지난다). 판정 전에 받은 세 값과 체크아웃한 병합 커밋의 첫 부모를 한 줄 찍는다(아래 실제 실행이 base 값을 그 첫 부모와 견준다)
- [x] **바뀐 파일과 전환.** 바뀐 파일은 base와 머리의 merge-base에서 머리까지다. 전환의 첫 자기 커밋은 base에 없는 머리의 커밋 가운데 가장 오래된 것이고, 03처럼 커밋 날짜가 아니라 위상 순서로 가른다. 그래서 다른 브랜치를 base로 둔 PR은 그 base 브랜치의 커밋을 제 것으로 세지 않는다. 규약 전 PR의 브랜치를 검사가 든 main으로 rebase해 푸시하면 딴 자리가 옮겨져 판정을 받는다(03과 같다)
- [x] **가리키는 티켓의 `Status:`.** 가리키는 티켓은 판정 5의 그 파일이고, `docs/` 브랜치면 판정 6의 harness 티켓 전부다. 값은 머리 커밋의 그 파일에서 줄 머리가 `Status:`나 `**Status:**`인 첫 줄의 첫 낱말이다. 줄 어디서든 첫 출현을 읽지 않는다(티켓 열한 장이 수용 기준 본문에 `Status:`를 한 번 더 든다). done이 아니면 막고, 막는 글에 그 티켓 경로와 지금 값, done으로 바꿔 다시 푸시하라는 할 일을 싣는다
- [x] **PR이 아닌 실행.** 머리 브랜치 값이 없으면(push 이벤트) 한 줄을 찍고 0으로 끝난다
- [x] **독스트링.** CI의 입력과 기준, `Status:`를 읽는 규칙, push 실행, 그리고 03이 비워 둔 문장(CI가 같은 판정을 한다, 훅을 건너뛴 커밋은 CI가 잡는다)을 더하고 못 보는 것을 고친다

### 워크플로

- [x] **잡 하나를 새로 둔다.** python 잡의 스텝으로 두지 않는다(명세의 거부한 안). 체크아웃은 기본(PR의 병합 커밋)을 `fetch-depth: 0`, `persist-credentials: false`로 받는다. 머리 커밋을 체크아웃하지 않는다(규약 전에 딴 PR의 머리에는 검사 도구가 없다)
- [x] **PR의 값은 `env`로 넘긴다.** 워크플로 안에서 PR의 값을 식으로 바로 펼치지 않는다(zizmor의 주입 판정, ADR 0027)
- [x] **`timeout-minutes`.** 새 잡이라 지난 실행이 없으니 첫 값은 어림으로 정하고, 이 PR의 실행으로 `.scratch/harness/probes/ci_job_durations.py`를 다시 돌려 고친다(`ci.yml` 머리 주석, 대기열 204)
- [x] **`verify`의 needs에 넣는다.** 잡, needs, 잡 수를 든 문서는 한 커밋에 든다. 빠뜨리면 `verify`가 같은 실행의 잡 목록을 읽어 빨강으로 본다

### 시험

- [x] 03의 임시 저장소 시험에 CI 입력의 사례를 더한다. done이 아닌 티켓의 막힘, done의 지남, `**Status:**` 꼴과 `Status:` 꼴, 상태 줄보다 앞의 본문에 `Status:`를 다른 값과 함께 든 티켓(줄 머리의 것을 읽는다), push 실행의 지남, 다른 브랜치를 base로 둔 PR이 base 브랜치의 커밋을 제 것으로 세지 않는 것, 분리 HEAD인 병합 커밋 체크아웃에서의 판정, CI의 전환 갈래(base에 검사가 없던 자리에서 딴 머리), 그 머리를 검사가 든 base로 rebase한 머리(판정을 받는다), 커밋 날짜가 위상 순서와 어긋난 머리의 커밋
- [x] **빨강을 먼저 본다.** 줄 어디서든 첫 출현을 읽는 첫 판이나 `Status:`를 보지 않는 첫 판으로 막혀야 하는 사례가 빨간 것을 본다

### 실제 실행

- [x] **draft 동안 두 경우를 본다**(`docs/constitution/operations.md` 가드레일의 필수 검사 판정을 바꾸는 PR의 확인). 이 티켓의 `Status:`를 in-progress로 둔 채 PR을 draft로 열어 새 잡과 `verify`가 빨간 것을 보고, 그 실행을 `gh run rerun --failed`로 다시 돌려 본다. 두 시도 모두에서 잡이 찍은 base 커밋 값이 그 시도가 체크아웃한 병합 커밋의 첫 부모와 같은지 본다(명세 검토가 재지 못한 것. 다시 돌린 시도는 첫 실행의 `GITHUB_SHA`와 `GITHUB_REF`를 그대로 쓴다. GitHub 문서 "Re-running workflows and jobs"의 본문을 내려받아 그 문장을 대 봤다. 그래서 첫 시도와 견주면 같게 나오기 쉽고, 물을 것은 그 값이 명세가 가정한 base인지다). 다르면 바뀐 파일의 기준을 그 첫 부모로 바꿀지 일지에 적고 사람에게 묻는다. done으로 바꿔 푸시해 초록을 본다. 실행 번호와 결과를 일지에 적는다
- [x] CI의 전환 갈래는 이 PR에서 실제로 돌지 않는다. 병합 뒤 규약 전에 딴 열린 PR이 다음에 푸시될 때 처음 돈다는 것을 일지의 "다음"에 적는다

### 문서

- [x] `.github/workflows/ci.yml` 머리 주석의 잡 수
- [x] `docs/constitution/tech.md` 원격·CI 행의 잡 수("잡 넷")
- [x] `docs/constitution/operations.md` 가드레일 절의 `verify`가 기다리는 잡 수("네 잡", "넷이 모두")와, 03이 더한 커밋 검사가 CI 잡도 돈다는 말. 헌법 patch 판을 올린다(번호 도구의 "형제가 쓴 가장 높은 헌법 판"보다 높게)
- [x] `CLAUDE.md` 검증 명령 절의 "CI도 돌리고" 무리에 커밋 검사를 넣는다

> 메모(03 셀프 리뷰): 03은 CI 전의 사실을 두 자리에 적었다. 04가 CI 잡을 더하면 둘 다 거짓이 되니 같은 PR에서 고친다. `CLAUDE.md` 검증 명령 절의 "커밋 검사(`tools/check_ticket.py`, ADR 0037)는 아직 pre-commit에서만 돈다"와, `docs/constitution/operations.md` 가드레일 첫 문장의 한쪽에만 있는 검사 목록에 든 "브랜치의 변경을 커밋에 들 색인으로 보는 것이라 아직 pre-commit에만 있고"다.
- [x] `KICKOFF.md`의 `.github/workflows/ci.yml` 줄에 새 잡을 더한다
- [x] 고친 뒤 저장소를 다시 grep해 CI 잡의 수를 든 다른 살아 있는 자리가 없는지 본다(`CLAUDE.md` 작업 규약 4)

### 검증

- [x] 첫 편집으로 이 티켓의 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣는다. 이 티켓만은 PR을 in-progress로 draft로 열고(위 실제 실행의 빨강), 빨강을 본 뒤 `done`으로 바꿔 푸시하며, draft를 풀기(ready) 전에 done이다
- [x] 원칙 III를 지킨다
- [x] 검증 명령이 모두 초록이다
