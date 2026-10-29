# 2026-10-29 (02) next-session 스킬을 상황마다 나누기 (harness 027)

## 시작

세션을 연 지시문의 시작 프롬프트와 범위다.

> 사용자: 티켓 .scratch/harness/issues/027-next-session-split.md 를 한다 (다음 단계 구현, 브랜치 chore/027-next-session-split, 모델 Opus 5.5 / xhigh, 이번 요청 범위 PR과 병합까지. 확인할 선행 조건: 같은 SKILL.md 를 고치는 harness 025(PR #417)가 병합됐는지 보고, 병합되지 않았으면 프로브까지 하고 멈춰 보고한다)

세션 제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path)` 로 이 워크트리에 들어갔다. `git log origin/main` 에 harness 025 의 커밋이 없어(`094a9a17` 이 머리, 손으로 봤다) 025 는 병합 전이다.

도중에 사용자가 둘을 말했다.

> 사용자: 병합이 완료되면 다음 지시문으로 새 세션은 열지마. 한도가 부족해.

> 사용자: 이 티켓과 관련된 작업은 계속 이어서 해야해. 인계라던지 이 티켓과 관련된 후속 작업이라던지.

그래서 이 티켓을 병합한 뒤의 다음 작업은 지시문만 내고 새 세션을 열지 않는다. 이 티켓의 인계와 후속 작업은 이어 간다.

## 프로브(수용 기준 1)

`.scratch/harness/probes/next_session_reads.py` 를 지었다. 장부의 next-session 폴더 Read 를 세션 기록과 맞대 길(고침, 인계 훅, 인계 받음, 병합 뒤, 그 밖, 기록 없음)로 가른다. 고치기 전 이레의 값, 양성 대조, 다른 해석, 결과를 본 뒤 바꾼 판정 기준 둘은 티켓의 `## Comments` 에 적었다(모두 그 프로브가 찍은 값이고, 대조는 `--list` 와 세션 기록의 글을 손으로 맞댄 것이다).

티켓 머리의 "약 4.6만 자"는 바이트였다. `SKILL.md` 는 23,419자다(`wc -c` 와 `len` 으로 손으로 셌다). 티켓 Comments 의 바로잡음에 적었다.

## 나누는 범위

025 를 기다리는 동안 조사 서브에이전트가 참조를 훑었다(파일을 읽거나 Grep 한 보고). 카나리아 22개가 모두 `kind = "skill"` 이라 회차 세션이 Skill 도구만 받아, 하위 파일로 옮긴 본문은 그 꼴로 시험하지 못한다. `tools/canary.py` 의 `rule` 종류(`--tools Read`, 대상 파일을 통째로 읽힘)는 대조군 사본에 원천이 없으면 새 파일로 받아 준다(`source_problems` 를 읽었다). 그래서 도구는 고치지 않고 옮긴 본문의 카나리아를 그 종류로 바꿔 다시 돌리면 된다. 사전 확인으로 갈음하는 조건(같은 PR 안의 통과)은 맞지 않는다(`docs/constitution/operations.md` 카나리아 항목). 다시 도는 수가 한도에 닿아 사용자에게 물었다.

> 질문: next-session 스킬을 얼마나 나눌까요? (카나리아는 시험 하나마다 Sonnet 세션 4번이고 옮긴 문장을 가리키는 카나리아는 모두 다시 돌린다는 설명과 함께)
> 사용자가 고른 답: "네 파일로 모두 나누기" — "병합 절차(merge.md)까지 떼어 냅니다. 인계를 받은 세션도 병합 단계에서 약 0.75만 자만 읽게 되어(어림) 효과가 가장 큽니다. 다만 다시 돌릴 카나리아가 20개 안팎이고, Sonnet 세션은 약 80번입니다(어림)."

다른 선택지는 "인계와 지시문만 떼기(추천)"(카나리아 8개 안팎, 세션 약 32번)와 "나누고 시험은 나중에"였다.

## 바로잡음: rule 종류로는 하위 파일 카나리아를 돌리지 못한다

위 "나누는 범위"의 "도구는 고치지 않고 rule 종류로 바꾸면 된다"는 틀렸다. `rule` 종류는 `target_problems` 가 실험군의 대상 파일에 카나리아가 있으면 돌리지 않는데, 하위 파일 카나리아는 그 파일 자체에 있어야 하므로 그 종류로는 늘 막힌다(`tools/canary.py` 를 다시 읽었다). 그래서 `skill` 종류에 `skill_files` 칸을 더했다. 그 칸이 참이면 명령의 도구가 `Skill,Read` 이고, 판정은 Read 가 그 스킬 폴더 안에만 닿았는지와 실험군이 원천(하위 파일)을 읽었는지를 더 보며, 돌리기 전 확인은 실험군의 `SKILL.md` 에 카나리아가 없는지를 본다. 시험은 `tests/tools/test_canary.py` 의 "하위 파일 갈래" 절이다.

## 지금까지 한 것

- 하위 파일 셋을 썼다. `merge.md`(병합 전 1~4와 워크트리에서 병합할 때, 7,104자), `handoff.md`(인계 순서 1~6과 인계 줄, 5,491자), `directive.md`(형식과 칸마다 1~6, 4,551자). 글자 수는 `uv run python` 의 `len` 으로 셌다. 025 의 원격 정리(`ls-remote`)는 `merge.md` 에 이미 들었다.
- `hook_handoff` 는 작업 폴더의 사본에서 `handoff.md` 를, 없으면 `SKILL.md` 의 `## 인계할 때` 를 고르고, 둘 다 없으면 훅과 같은 체크아웃의 `handoff.md` 로 간다. `hook_pr_next_session` 의 문장은 순서 1이 가리키는 병합 절차와 인계 절차 파일을 말한다. 첫 턴 훅 시험은 `directive.md` 의 `## 형식` 으로 가른다.
- 살아 있는 문서의 옛 절 참조(`1단계`, `3단계`, "워크트리에서 병합할 때", "인계할 때", 결정표의 인계 줄)를 새 파일로 고쳤다. `tools/` 주석 여섯, `tests/tools/` 주석 셋, 스킬 여섯(`implement`, `open-session`, `tidy-checkouts`, `code-review`, `sync-design-system`, 에이전트 `bug-perf-review`), `.claude/rules/tools.md`, `CLAUDE.md`, `KICKOFF.md`(복사 목록에 하위 파일 셋), `kickoff/pitfalls.md`, `docs/model-selection.md`, 헌법 `operations.md`(판은 아래 합치기 뒤 3.0.60), 대기열의 열린 행 여덟, 프로브 README 둘이다. ADR 본문은 `.claude/rules/adr.md` 의 "본문의 다른 글자는 고치지 않는다" 대로 두었다. 한 번 고쳤다가 되돌렸다. 기록(일지, done 인 티켓, done 인 기능 디렉터리, ADR 이력, 헌법 판 기록)도 두었다.
- 새 `SKILL.md` 의 초안을 스크래치에 지었다(아래 남은 일 2). 이 브랜치의 판(025 전)으로 지으면 7,836자다.

## 사용량

> 사용자: 작업하다가 한도가 98프로가 되면 새 계정으로 이어서 작업할 수 있게 마무리해줘.

이 말을 받은 때 `get_usage` 의 주간 전체가 93%였다. 남은 일 가운데 카나리아를 다시 돌리는 몫(Sonnet 세션 약 80번, 어림)이 가장 커서 이 계정으로 다 하지 못할 수 있다. 98%에 닿으면 이 절 아래 "남은 일" 을 고친 뒤 멈춘다.

## 025 가 멈췄다

025 의 병합을 다섯 시간 기다렸으나(대기 스크립트가 `TIMEOUT state=open false` 로 끝났다) PR #417 은 열린 채였다. REST 로 보니 머리는 `a1c453e4`, `mergeable_state` 는 `dirty`(main 과 충돌), 마지막 갱신은 2026-10-28T10:54Z 였고, 그 세션(`chore/025-next-session-prune-check`)은 `list_sessions` 에서 `isRunning` 이 거짓, 마지막 활동 11:02Z 였다. 그래서 025 가 먼저 병합된다는 선행 조건은 그 세션을 다시 깨우거나 순서를 바꾸지 않으면 차지 않는다. 어느 쪽으로 갈지 사용자에게 물었다.

> 사용자: 025 세션을 깨워 충돌을 풀고 먼저 병합하게 한 뒤 027을 이어서 해.

그 세션에 이 원문과 할 일(origin/main 합치기와 충돌 풀기, 봇 회차, 워크트리 길로 병합, 병합 뒤 새 세션을 열지 않기, 끝나면 이 세션에 한 줄 알리기)을 `SendMessage` 로 보냈고 전달됐다(그 세션의 턴이 시작됐다는 도구 결과). 같은 대기 스크립트를 다시 띄웠다.

025 세션이 병합했다고 알려 왔고, `git log origin/main` 의 머리가 그 squash 커밋 `f8410d01` 인 것을 손으로 봤다. 작업 트리의 변경을 이름 붙인 stash 로 치우고 origin/main 을 합친 뒤(머지 커밋 `37759ef2`) SHA 로 되돌렸다. 충돌 넷(`open-session` 스킬, 대기열, 헌법 README·`operations.md`)은 main 쪽을 받고 참조 고침을 다시 얹었다. main 이 헌법 판 3.0.59(harness 028)를 가져가 이 브랜치의 판은 3.0.60 으로 비켰다. 앞의 대기열 스크립트가 윈도의 `write_text` 로 그 파일을 CRLF 로 썼던 것을 stash 경고에서 보고 LF 로 되돌렸다. 025 가 병합한 "워크트리에서 병합할 때" 와 `merge.md` 의 같은 절을 견주니 다른 것은 이 브랜치가 일부러 바꾼 가리킴과 줄인 괄호뿐이었다(스크래치 스크립트의 diff). 새 `SKILL.md` 를 합친 판으로 지어 덮었고(7,836자), 스킬·훅을 보는 시험 일곱 파일 802개가 통과했다.

## 카나리아(수용 기준 5)

`respec.py` 로 열다섯을, 손으로 025 의 `remote_branch_check` 를 하위 파일 갈래로 옮겼다. 혼합 명세 넷은 옮긴 물음을 뺐고, 뺀 기대가 모두 하위 파일을 원천으로 둔 다른 명세에 이미 드는 것을 grep 으로 봤다. `--preflight --control-commit 37759ef2` 로 스물넷을 보니 옮긴 열여섯 가운데 `model_sweep` 하나가 막혔다. 같은 PR 이 `tools/model_sweep.py` 주석을 고쳐 그 경로가 갈래 세션의 git 상태에 실렸기 때문이라, 카나리아를 `tools/model_sweep.py <브랜치>` 로 넓혔다. 혼합 넷과 옮기지 않은 넷은 대조군 쪽만 막혔다(옛 사본도 그 글을 들어 대조가 서지 않는다).

이 세션을 이어받을 때 주간 사용량이 93%였다. 남은 열셋을 돌리면 98%에 닿을까 봐, 하위 파일마다 하나씩 셋을 먼저 돌려 Read 길이 도는 것을 본 뒤 사용량을 보며 넷·다섯·넷으로 나눠 돌렸다. 열여섯 모두 통과 4였고 사용량은 94%에 머물렀다. `handoff_row` 의 실험군 한 회차가 1번 물음에 "없음."이라 쓴 뒤 같은 줄에서 바른 글자를 옮겨 "없음" 섞임으로 찍혔다(그 명세 머리 주석). `# 최신 결과:` 줄은 새로 넣고 옛 줄의 머리는 `# 옮기기 전 결과:` 로 바꿨다(스크래치 스크립트가 임시 파일에 쓴 뒤 바꿨다).

## 인계 확인(수용 기준 6)

`hook_handoff.context_for` 가 지은 실제 문장(`커밋 뒤`)과 가상의 티켓 999 상황을 프롬프트로, 이 워크트리에서 `claude -p --tools Read,Skill --model sonnet` 을 한 번 띄웠다. Read 는 `handoff.md` 와 `directive.md` 둘뿐이었고 Skill 은 부르지 않았다. 낸 지시문의 "이어받을 상태"는 `인계: 커밋 뒤.` 로 시작해 일지 경로로 끝났다(티켓 Comments 에 자세히, 손으로 봤다).

같은 때 옛 표현을 다시 grep 하니 열린 대기열 행 셋(383·420·434)이 옛 자리(next-session 1단계, 3단계)를 가리켜 새 자리를 괄호로 더했다. 나머지 일치는 카나리아 머리 주석(그때 더한 것의 기록), 닫힌 대기열 행, 티켓이 모두 done 인 기능 디렉터리(model-rerun, ticket-for-every-pr, token-usage), 헌법 판 기록, 훅 독스트링의 옛 판 설명이다.

## 인계(셀프 리뷰 직전)

검증을 띄우고(ruff 둘은 통과, `run_checks` 는 백그라운드) 워크트리 사본의 `code-review` 를 부르자 인계 계기가 왔다(세션 컨텍스트 246,697 토큰). 계기 문장은 주 체크아웃의 옛 훅이 낸 것이라 `SKILL.md` 를 열어 결정표의 인계 줄을 따르라고 했다. 그 파일의 `## 인계할 때` 가 `handoff.md` 를 가리켜 판이 어긋난 갈래로도 인계 절차에 닿았다(수용 기준 3의 옛 훅 갈래를 실제로 밟았다). `handoff.md` 1의 다섯에 들지 않아 넘긴다(`get_session` 의 `self` 에 `parentSessionId` 가 없다). 셀프 리뷰는 새 세션이 하고, 띄운 `run_checks` 는 4의 대기 멈추기로 멈춘다(결과를 보지 않았다). 이 세션의 지금 제목은 `chore/027-next-session-split` 이다. 주 체크아웃은 `main` 이지만 origin/main 보다 뒤라(025 세션이 당기지 않았다) 지시문에 미갱신을 적는다. 모델은 `tools/model_sweep.py` 가 `Opus 5.5 / xhigh` 를 내 스윕의 갈래 표지를 단다. 낸 지시문:

```
다음 작업: .scratch/harness/issues/027-next-session-split.md. next-session 스킬을 네 파일로 나눈 변경의 셀프 리뷰부터 병합까지를 잇는다
다음 단계: 구현
어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 티켓 .scratch/harness/issues/027-next-session-split.md 를 한다
브랜치: chore/027-next-session-split
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-29-02-next-session-split.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 이 브랜치가 next-session·code-review 스킬을 고쳤으니 고정점 origin/main으로 워크트리 사본을 부르고, 병합한 뒤에는 다음 작업의 지시문만 내고 새 세션은 열지 않는다(사용자 말, 일지의 "남은 일"). docs/journal/2026-10-29-02-next-session-split.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

제목을 `chore/027-next-session-split (인계함)` 으로 바꿨고, `run_checks` 를 멈췄고, 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-29T02:48:09Z

## 이어받음(셀프 리뷰부터)

> 사용자: 티켓 .scratch/harness/issues/027-next-session-split.md 를 한다 (위 지시문의 시작 프롬프트. 이어받을 상태 `인계: 셀프 리뷰 직전`, 이번 요청 범위 PR과 병합까지)

새 세션이 제목을 `chore/027-next-session-split` 으로 바꾸고 주 체크아웃에서 `tidy-checkouts` 를 돌았다. 루트를 `4919e196` 에서 `f8410d01` 로 당겼고, 병합된 워크트리 026·028(쥐고 있던 쉬는 세션의 프로세스를 `end-holders` 로 끈 뒤)과 브랜치 `worktree-04-admin-frame-common-states` 를 지웠다. 그 뒤 `EnterWorktree(path)` 로 들어왔다. `origin/main` 은 머지 커밋 `37759ef2` 뒤로 움직이지 않았다. `sibling_overlap` 이 이 일지의 번호가 main 의 최신 일지(2026-10-29-01)보다 앞이라고 해 `--move` 로 2026-10-29-02 로 옮겼다. 이 세션의 지금 제목은 `chore/027-next-session-split` 이다.

## 셀프 리뷰

`code-review` 를 워크트리 사본(Read)으로 따랐다. base `f8410d01`, 추적 파일 57개, 커밋 2개, 미추적 5개. 표준 축(sonnet·high)은 Major 1·Minor 3·Nit 2, 명세 축은 Major 3·Minor 4·Nit 1을 냈다. 표준 축이 다시 잰 글자 수, 겹침 0, `skill_for`·`canary` 함수의 경계 입력은 맞았다. 반영 전 상태의 `run_checks` 는 모두 통과였다(종료 0).

고친 것:
- (표준 Major) `handoff.md` 2가 일지 번호 규칙을 `merge.md` 3에 미루면서 그 파일을 열라고 하지 않았다. 열게 고쳤다.
- (명세 Major) `SKILL.md` 순서 1의 "PR을 병합한 뒤에 불렸거나 끊을 때면 2부터 한다"는 나누기 전 판에 없던 지름길이라, 병합 명령 직후 `hook_pr_next_session` 계기로 다시 불린 세션이 `merge.md` 의 병합 뒤 단계(원격 정리, 미갱신 줄, `tidy-checkouts`)를 건너뛸 수 있었다. `merge.md` 의 끝 줄이 찰 때까지 마친 뒤 2로 오게 고쳤다.
- (명세 Major) `handoff.md` 1 끝의 "커밋 뒤나 PR 연 뒤면 `merge.md`"는 나누기 전 판의 "PR 연 뒤면"을 넓혀, 범위가 커밋에서 끝나는 세션까지 병합 절차로 보냈다. "PR 연 뒤면"으로 되돌렸다.
- (명세 Major) `tools/sibling_overlap.py` 의 `HARNESS` 가 스킬 폴더의 `SKILL.md` 밖 파일을 보지 않아, 하위 파일만 고치면 카나리아 누락을 알리지 않았다. 카나리아의 `skill_files` 가 받는 꼴과 같게 스킬 폴더 바로 아래 마크다운 전부로 넓혔다. 시험을 먼저 고쳐 빨강을 봤다.
- (명세 Minor) `SKILL.md` 의 하위 파일 대체 길이 나누기 전에 딴 워크트리에서 작업 폴더 밖 파일로 갔다. 그때는 작업 폴더의 `SKILL.md` 판을 따르게 했다(`hook_handoff.skill_for` 와 같은 갈래).
- (명세 Minor) `tools/canary.py` 못 보는 것에 `skill_files` 명세의 대조군이 옮기기 전 커밋일 때 원천 확인이 비어서 지나간다는 항목을 더했다. (표준 Nit) `skill_for` 독스트링에 사본을 `SKILL.md` 로 알아본다고 적었다.
- (표준 Minor, 명세 Minor) 티켓의 "같은 사실" 주장을 잰 범위(글자가 같은 문장)로 좁히고 리뷰가 든 요약 셋을 적었다. 명세 수(24), 반영 뒤 글자 수, 인계 길의 셋째 파일 갈래를 고쳐 적었다.
- (표준 Minor 일부, 명세 Nit) 대기열 372행과 카나리아 명세 셋(`model_sweep`, `worktree_copy_read`, `label_ticket_notice`)의 첫 줄에 지금 자리를 괄호로 더했다.

남긴 것과 이유:
- `KICKOFF.md` 의 "next-session 4단계"와 "그 스킬의 1단계는 병합까지 가므로"는 새 `SKILL.md` 에도 순서 1(병합까지 마친다)·4(연다)가 있어 맞는 가리킴이다. `model_sweep/README.md` 150행의 "결정표의 인계 줄"은 "조건 변경(ADR 0033)" 절이 PR #276 병합 때의 사실을 적은 기록이다.
- 카나리아 질문의 "2단계의 나란히 여는 묶음"은 `SKILL.md` 결정표의 "2단계의 묶음"과 같은 글이다. 대소문자만 다른 `skill.md` 는 이 저장소에 생기지 않는다.

반영으로 새로 쓴 사실 문장(PR 직전 리뷰에 밀 주장):
- `SKILL.md` 순서 1: "병합 명령 직후 훅의 계기로 불렸어도 병합 뒤의 단계가 남아 있다(주 체크아웃이면 `merge.md` 4의 `tidy-checkouts`, 워크트리면 "워크트리에서 병합할 때" 3·4)."
- `SKILL.md` 표 위: "작업 폴더에 `SKILL.md`는 있고 그 파일이 없으면 나누기 전에 딴 워크트리라, 작업 폴더의 `SKILL.md`를 Read로 열어 그 판의 순서를 따른다."
- `tools/canary.py` 못 보는 것의 새 항목, `tools/sibling_overlap.py` 독스트링의 "`SKILL.md` 가 Read 로 열게 하는 하위 파일도 카나리아의 `skill_files` 가 원천으로 받는다".
- 티켓 Comments 의 반영 뒤 글자 수(8,071·5,495, 상황별 10,046·19,726·12,622, 갈래 17,150·18,117, 넷의 합 25,221).

다시 돌린 명령: `tests/tools/test_sibling_overlap.py` 118 통과. 나머지 손으로 치는 다섯은 커밋의 pre-commit 으로 갈음하고 결과는 커밋 뒤에 적는다.

## 카나리아(셀프 리뷰 뒤)

`sibling_overlap` 이 이 브랜치가 옛 절 참조를 고친 하네스 일곱(`bug-perf-review`, `tools.md` 규칙, `code-review`·`implement`·`open-session`·`sync-design-system`·`tidy-checkouts`)의 카나리아 명세를 하나도 고치지 않았다고 알렸다. 이때 주간 사용량은 94%였다. 파일마다 바뀐 문단을 묻는 명세 하나와, 고친 기대("2의 2")가 한 번도 돌지 않은 `next_session_deferred_merge_running_scope` 를 돌린다. 대조군은 카나리아가 원천에 처음 들어온 커밋의 부모다(`git log -S` 로 찾았다. `implement_ticket_status` 는 그 명세가 적은 `caaa062b`). 모든 명세의 사전 확인에서 이 브랜치가 실험군 원천의 카나리아를 지운 것은 `code_review_overlap_exit_two` 하나였고(`code-review` 6단계 끝의 괄호를 `merge.md` 3으로 고쳤다) 그 기대를 새 글로 고쳤다. 이 브랜치가 고치지 않은 원천에서 실험군 카나리아가 없다고 막힌 넷(`web_design_artifact`, `web_design_colors`, `web_design_props_icon_card`, `tidy_skill_cwd_owner`)은 범위 밖이라 두었다.

결과: 여덟 모두 통과 4 · 실패 0 · "없음" 섞인 통과 0, 종료 0(러너가 찍었다. claude 2.1.312, 실험군은 `37759ef2` 위의 커밋 전 변경, 대조군 커밋은 각 명세의 `# 최신 결과:` 줄). 원본은 세션 스크래치패드의 `run_a.log`·`run_b.log` 와 `canary/` 아래에 두었고 저장소에는 두지 않았다. 각 명세의 `# 최신 결과:` 줄을 새 결과로 바꾸고 옛 줄은 "그 전:"으로 내렸다. 그 뒤 `sibling_overlap` 은 종료 0으로 하네스 알림이 없었다(이때 주간 사용량 95%).

## 남은 일

1~8. 끝났다(위 절들, 티켓 Comments, 아래 회고와 다음).
9. ruff 둘, 브랜치 확인, `sibling_overlap`, 티켓 done, 커밋은 끝났다(아래 인계 절). 남은 것은 푸시, PR, 봇 회차, `merge.md` 의 워크트리 길로 병합이다. 병합 뒤에는 다음 작업의 지시문만 내고 새 세션은 열지 않는다(위 사용자 말).

## 인계(커밋 뒤)

ruff 둘은 통과, 브랜치는 `chore/027-next-session-split`, `sibling_overlap` 은 겹침 없음이었다. 커밋 `952147f6` 의 pre-commit 은 두 번째 시도에서 모두 Passed 였고 Skipped 는 없었다(러너가 찍었다. 첫 시도의 두 빨강은 위 회고 절). 그래서 손으로 치는 다섯은 이 결과로 갈음한다. 커밋 직후 인계 계기가 왔다(`커밋 뒤`, 계기 문장의 세션 컨텍스트 254,703 토큰). 요청 범위가 병합까지이고 넘겨받은 경계(셀프 리뷰 직전)와 다르며, `get_session` 의 `self` 에 `parentSessionId` 가 없어 `handoff.md` 1의 다섯에 들지 않는다. 그래서 넘긴다. 이때 주간 사용량은 95%였다. 이 세션의 지금 제목은 `chore/027-next-session-split` 이다. 주 체크아웃은 `main` 이고 `origin/main` 과 같은 `f8410d01` 이다. 모델은 `tools/model_sweep.py` 가 `Opus 5.5 / xhigh` 를 냈다. 낸 지시문:

```
다음 작업: .scratch/harness/issues/027-next-session-split.md. next-session 스킬을 네 파일로 나눈 커밋을 푸시하고 PR·봇 회차·병합까지 잇는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 티켓 .scratch/harness/issues/027-next-session-split.md 를 한다
브랜치: chore/027-next-session-split
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-29-02-next-session-split.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영, 카나리아 여덟, 회고와 일지 "다음"까지 마치고 952147f6 으로 커밋했다(pre-commit 모두 Passed). 일지의 이 인계 절은 커밋하지 않았다. 남은 단계는 이 일지를 커밋하고 푸시, PR(/git-pr), merge.md 2(봇 회차), merge.md의 "워크트리에서 병합할 때"로 병합이다. 이 브랜치가 next-session을 고쳤으니 merge.md는 워크트리 사본을 Read로 열어 따르고, 병합한 뒤에는 다음 작업의 지시문만 내고 새 세션은 열지 않는다(사용자 말, 일지 "시작"). 주간 사용량이 98%에 닿으면 새 계정으로 이어 갈 수 있게 일지의 남은 일을 고치고 멈춘다(사용자 말, 일지 "사용량"). docs/journal/2026-10-29-02-next-session-split.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

## 회고

후보 일곱, 승인 2 · 기각 5 · 넘김 0. 뒤의 둘(531 회차, 변이 표)은 아래 커밋 문단의 사건이라 회고를 마친 뒤 더했다.

- 승인(회차로 세는 것, 대기열 531, 3회차): `test_interrupt` 의 같은 시각 값 비교가 하네스만 바꾼 커밋의 pre-commit 을 막았다. 그 행이 이미 처방(시계 값 대신 자식이 쓰는 순서로 가르기)을 들었다.
- 기각: 셀프 리뷰 뒤 반영에서 고친 코드의 변이 원문 셋을 변이 표에 맞추지 않았다. 이미 있는 검사(pre-commit 의 `tools/mutate.py --staged`)가 그 자리에서 막았다.

- 승인(고침, 대기열 539, 1회차): 카나리아 명세 넷(`web_design_artifact`, `web_design_colors`, `web_design_props_icon_card`, `tidy_skill_cwd_owner`)의 기대 글이 원천에서 다른 PR 이 고친 뒤에도 남아 `--preflight` 가 막는다. 사건은 이 세션의 사전 확인 실패이고(`tools/canary.py --preflight` 가 넷 모두 "원천에 카나리아가 없다"를 찍었다. `tidy_skill_cwd_owner` 의 글은 origin/main 의 원천에도 없다, `git grep` 으로 손으로 봤다), 층은 명세 고침과 세 번째에 `sibling_overlap` 검사, 되돌림은 PR 하나다. 이 PR 의 범위 밖이고 다시 돌리면 Sonnet 세션 열여섯이 들어 주간 95%에서 반영하지 않았다.
- 기각: 앞 세션의 "rule 종류로 바꾸면 도구는 고치지 않아도 된다"는 잘못된 주장. 사건은 있으나 이 PR 이 `skill_files` 갈래로 도구를 고쳐 같은 자리가 다시 나지 않는다.
- 기각: 셀프 리뷰의 명세 Major 셋(옮기며 생긴 지름길, 인계 길의 범위 넓힘, `HARNESS` 의 하위 파일 누락). 리뷰가 잡도록 둔 기준을 리뷰가 잡은 것이라 셈에서 뺐고, 옮긴 글의 뜻이 바뀌었는지는 검사로 옮길 수 없다. `HARNESS` 누락은 이 PR 에서 고쳤다.
- 기각: 워크트리 가드와 `cd` 훅이 이 세션의 복합 명령(`cd … &&`, 한글 정규식 인자와 리다이렉트)을 막았다. 이미 있는 가드·훅이 그 자리에서 막았다.
- 기각: 셀프 리뷰 뒤에야 카나리아 여덟을 따로 돌린 비용. 앞서 알았어도 돌릴 회차 수는 같아 사건이 되는 비용이 아니다.

첫 커밋의 pre-commit 에서 둘이 빨갰다(러너가 찍었다). pytest 는 `tests/channel/cli/test_interrupt.py` 의 `test_도구_호출_도중에_한_번_누르면_서버를_닫고_중단으로_끝난다` 가 `assert 1793245021.2453017 < 1793245021.2453017` 로 빨갰다(5992 통과, 1 실패). 이 브랜치가 건드리지 않은 시험이고 대기열 531 과 같은 꼴이라 그 행에 3회차를 더했다(회차로 세는 것, 이제 chore 계기다). 변이 표 검사(`tools/mutate.py --staged`)는 이 브랜치가 고친 `tools/sibling_overlap.py`·`tools/hook_handoff.py`·`tools/hook_pr_next_session.py` 의 원문 셋을 찾지 못했다. 셀프 리뷰 뒤 반영에서 코드를 고치고 변이 표를 다시 보지 않은 것이다. 지금 코드에 맞게 원문을 고치고 변이 둘을 더했으며(`HARNESS` 가 `SKILL.md` 만 보는 쪽, 작업 폴더의 나누기 전 사본을 고르지 않는 쪽), 고친 다섯을 돌려 모두 기대대로 빨강이었다(`tools/mutate.py` 가 찍었다).

대기열: 141·257 을 만료로 닫았다(작업 트리와 origin/main 의 `queue_open_rows` 출력 모두에 들었다). 520(카나리아 스킬 갈래의 보조 파일 Read)은 이 티켓의 `skill_files` 가 그 처방이라 이 티켓 경로로 닫았다.

## 다음

- 2026-11-05 이후에 병합 뒤 이레의 값을 같은 프로브로 다시 잰다(티켓 수용 기준 7). `uv run python .scratch/harness/probes/next_session_reads.py --first <병합 다음 날> --last <그 뒤 엿새째>` 로 길마다 next-session 폴더 Read 의 글자를 내고, 티켓 Comments 의 고치기 전 이레 값과 견준다. 인계 받음과 병합 뒤 길에서 줄었는지가 이 티켓의 효과다.
- 대기열 539: 범위 밖 카나리아 넷의 기대를 지금 원천 글로 고치고 다시 돌린다.
- 대기열 531 이 3회차가 되어 chore 계기다(`test_interrupt` 의 시각 비교가 문서·하네스 커밋을 막는다).
- 그 밖의 다음 작업은 병합 뒤 next-session 이 정한다. 이 세션은 지시문만 내고 새 세션을 열지 않는다(위 사용자 말).

제목을 `chore/027-next-session-split (인계함)` 으로 바꿨고, 멈출 백그라운드 작업은 없었고, 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-29T03:55:50Z

## 이어받음(커밋 뒤)

> 사용자: 티켓 .scratch/harness/issues/027-next-session-split.md 를 한다 (위 지시문의 시작 프롬프트. 이어받을 상태 `인계: 커밋 뒤`, 이번 요청 범위 PR과 병합까지)

새 세션이 제목을 `chore/027-next-session-split` 으로 바꾸고 `EnterWorktree(path)` 로 이 워크트리에 들어왔다. `git fetch origin` 뒤에도 `origin/main` 은 `f8410d01` 그대로였다(`git log --oneline -3 origin/main` 으로 손으로 봤다). 이때 주간 사용량은 95%였다(`get_usage` 가 찍었다). 이 인계 절과 함께 일지를 커밋해 푸시하고, PR 을 연 뒤 워크트리 사본의 `merge.md` 를 Read 로 열어 봇 회차와 병합을 잇는다.

## PR 직전 리뷰

`coderabbit auth status` 가 `Seat: not assigned` 를 찍어(손으로 봤다) CLI 대신 대체 둘을 나란히 돌렸다. 둘 다 일지 커밋 `9ce00d1c` 를 푸시한 뒤, origin/main 을 합친 브랜치에서 돌았다.

- 보안(`/security-review`): 식별 서브태스크 하나가 `tools/` 의 바뀐 코드와 프로브 `next_session_reads.py` 를 읽고 지적 0건을 냈다(서브에이전트 보고). 그래서 거짓 양성 거르기 서브태스크는 띄우지 않았다. 보고의 요지: subprocess 는 모두 목록 인자이고 `shell=True` 가 없다. `skill_files` 는 `--tools` 값만 `Skill,Read` 로 바꾸고 권한을 넓히는 플래그는 없다. `skill_for` 는 훅 입력의 `cwd` 위로 `is_file`·`read_text` 만 하고 막는 훅(`hook_push_delete_open_pr`)의 판정은 바뀌지 않았다. 프로브는 `json.loads` 만 쓰고 키나 토큰을 찍지 않는다.
- 버그·성능(`bug-perf-review`): Critical·Major 0, 유효 2(Minor 1, Nit 1), 오탐 4(서브에이전트 보고). 둘 다 고쳤다.
  - (Minor, 고침) `next_session_reads.py` 의 `ledger_reads` 가 장부 Read 의 `at` 이 빈 글이면 `datetime.fromisoformat("")` 의 `ValueError` 로 프로브 전체가 죽었다. `tools/token_report.py` 의 `_iso_of` 가 시각을 못 읽으면 빈 글을 쓰고 "그 행은 어느 날에도 들지 않는다"고 독스트링에 적는다(코드를 읽었다). 서브에이전트는 그 행을 넣어 그 예외를 재현했다고 보고했다. 그런 Read 는 빼고 세어 출력과 결과 JSON(`untimed`)에 싣고, 하나라도 있으면 종료 코드를 1로 둔다(시각이 없으면 날의 합에 넣을 수 없어 측정 아님과 같다). 빈 글·깨진 시각·바른 시각 세 행을 넣은 스크래치 스크립트에서 바른 하나만 들고 2를 셌다(손으로 봤다). 실제 장부에 빈 `at` 이 있는지는 재지 않았다.
  - (Nit, 고침) `.scratch/token-usage/probes/handoff_reach.py` 의 `_lowered_copy` 가 사본에 `SKILL.md` 만 두고 독스트링이 이 브랜치가 없앤 `SKILL_PATH` 를 가리켰다. 그래서 A·B 갈래의 훅 문장이 사본에 없는 `handoff.md` 를 가리켰다. 스킬 폴더째 복사하고 독스트링을 `HANDOFF_PATH` 로 고쳤다. 고친 함수로 만든 사본에서 복사한 훅의 `HANDOFF_PATH` 가 있는 파일이고 문턱이 1000 인 것을 스크래치 스크립트로 봤다(손으로 봤다). 프로브 자체(`claude -p` 네 갈래)는 돌리지 않았다.
  - 오탐으로 둔 것: 장부 사전 거름이 `json.dumps` 의 기본 구분자에 기댄다(쓰는 쪽이 기본 구분자다), 상대 경로 Read(Read 는 절대 경로를 받는다), `HARNESS` 가 다른 스킬의 하위 파일에도 카나리아 알림을 낸다(독스트링에 적은 의도), 기록 폴더 훑기의 `is_file` 수(프로브라 문제 삼지 않는다).
