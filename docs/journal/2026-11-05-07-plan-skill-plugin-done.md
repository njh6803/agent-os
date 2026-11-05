# 2026-11-05 (07) plan.md의 skill-plugin 행을 done으로 고친다 (harness 043)

세션 제목은 `chore/043-plan-skill-plugin-done`이다. 티켓은 `.scratch/harness/issues/043-plan-skill-plugin-done.md`이다. 앞 세션(harness 041, 일지 2026-11-05-04)이 병합을 마친 뒤 같은 세션이 이어 했다.

## 사용자 프롬프트

> 사용자: 고친다 (앞 턴의 물음 "plan.md의 skill-plugin 행을 done으로 고치는 작은 PR을 이어서 할까요?"에 대한 답이다.)

## 한 것

- `uv run python tools/sibling_overlap.py`로 다음 빈 번호(티켓 043, 일지 07)를 받고, `git switch -c chore/043-plan-skill-plugin-done origin/main`으로 새 브랜치를 땄다. 기준은 origin/main `050bb13b`(harness 041 병합)이다.
- `.scratch/skill-plugin/issues/`의 `Status:` 줄 다섯이 모두 `done`임을 `grep`으로 다시 봤다. `git log origin/main`으로 PR 번호를 맞췄다(01 #462, 02 #461, 03 #463, 05 #464, 04 #465).
- `.scratch/plan.md` 25번 줄(슬라이스 6)의 상태 칸을 `done`으로 바꾸고 끝에 03·05·04의 병합과 닫힘을 적었다. 44번 줄(프론티어 문단) 끝의 "04와 05가 03을 기다린다"를 닫힘 문장으로 바꿨다. 슬라이스 7 행은 그대로다.

## 셀프 리뷰 (`code-review`, base `050bb13b`, 파일 둘: 수정 1·미추적 1, 커밋 0)

표준 축과 명세 축 모두 하드 위반이나 누락이 없고, PR 번호·일지 번호·날짜·04의 서술을 직접 대조해 맞다고 보고했다. 지적은 다음과 같다.

- 프론티어 문장의 "슬라이스 8 이후는 앞 행에 막혀 있다"가 부정확하다(슬라이스 7의 mcp-trust·principal-propagation도 막혀 있다). 고쳤다: "나머지 행은 모두 앞 행에 막혀 있다".
- 티켓 수용 기준 3의 grep이 티켓 자신의 인용에 걸린다. 고쳤다: 기준에 "이 티켓이 옛 문장을 인용한 곳과 일지·ADR 이력 같은 기록은 뺀다"를 적었다.
- 티켓 수용 기준 4가 무엇으로 초록인지 적혀 있지 않다. 고쳤다: 손으로 친 검사와 pre-commit 갈음을 적었다.
- 남긴 것: 25번 줄 앞부분의 "첫 티켓 둘이 나란히 돈다"가 현재형이다. 계획 시점의 서술을 보존한 줄이고 다른 닫힌 행도 같은 식이라 그대로 둔다.

## 검증

- 손으로 친 것: `plan.md`를 읽는 시험 네 파일 172개 통과, `check_md_tables.py`·`check_instructions.py` 출력 없음(통과).
- 나머지 손으로 치는 명령은 커밋의 pre-commit 결과로 갈음한다(`.py` 변경이 없어 ruff는 `Skipped`일 수 있다).

## 회고

후보 둘, 승인 1(대기열에 둠), 기각 1, 넘김 0.

- **승인: 마지막 티켓이 병합돼도 `plan.md`의 기능 행이 `in-progress`로 남았다.** 사건: skill-plugin의 티켓 다섯이 모두 `done`인데 행이 `in-progress`였고, 이 PR(043)이 고쳤다. 층: 저장소 상태 시험이 사다리에서 가장 높은 층이다(행 546의 처방). 되돌림: PR 하나다. 같은 일을 다룬 행을 `queue_open_rows.py --search plan.md --search 마지막.티켓 --search in-progress`로 찾았다. 닫힌 104(1회차)와 만료한 399(2회차)가 "마지막 티켓이 `plan.md`를 done으로 바꾸는 자리"였고, 열린 546은 첫 티켓의 같은 틈을 시험으로 막자는 처방이다. 그래서 546에 회차를 더해 3회차로 올리고 처방을 "티켓이 모두 done이면 행도 done"까지 넓혔다. 3회차라 chore 계기다. 반영은 아직 하지 않았다.
- **기각: 티켓 수용 기준의 체크박스를 검증 전에 `sed`로 한꺼번에 `[x]`로 바꿨다.** 표준 축 리뷰가 "검증 명령 초록"의 근거가 티켓에 없다고 Minor로 잡았고 그 자리에서 고쳤다. 리뷰가 제 몫을 한 사건이라 회차로 세지 않는다. 같은 꼴의 열린 행 551(결과 절을 쓰며 하지 않은 일의 체크박스를 닫았다)이 이미 있다.
- 만료: `tools/queue_open_rows.py`가 만료할 행 없음을 냈다(앞 세션이 여덟을 닫았다).

## 다음

- 대기열 546이 3회차가 되어 chore 계기다. `.scratch/plan.md`의 기능 행 상태를 티켓의 `Status:`와 맞추는 저장소 상태 시험(티켓이 모두 `done`이면 행도 `done`, 하나라도 `done`이면 `todo`가 아니다)을 새 harness 티켓으로 쓴다. 먼저 main의 지금 상태가 그 시험을 지나는지 본다.
- 프론티어는 `approval-rules` 하나이고 설계 인터뷰부터다. `docs/approval-rules-design` 세션이 이미 돌고 있으면 그 세션의 몫이다.
- 일지 2026-11-05-04의 "다음"에 적은 `tools/mutate.py`의 `where ` 줄 머리 거짓 양성(독스트링 한 문장과 시험)은 새 harness 티켓이 필요하다.
