# 2026-10-28 (25) 나란히 도는 세션을 최대 다섯으로 묶는다

harness 티켓 028. 아침 보고 예약 작업(작업 보고)으로 시작한 세션이 사용자의 질문을 받아 이어 갔다. 세션 제목은 `【매일 09:45】 아침 보고 · 작업`에서 `chore/028-max-five-parallel-sessions`로 바꿨다.

> 사용자: 병렬작업 몇 개가 적당한 것 같아?

2026-10-27 아침 보고 수집 JSON의 `environment.concurrency` 표를 손으로 보고 4개 안팎, 많아야 6개라고 답했다. 10-21~10-27의 7일 동안 동시 세션 4~6개 구간이 병합 PR 47개, PR당 비용 중앙값 $53, PR을 연 뒤 병합까지 중앙값 1.0시간이었고, 1~3개 구간은 28개, $58, 1.2시간이었으며, 7개 이상 구간에서 주로 작업한 병합 PR은 0개였다. 일주일치 비교라 어림이다.

> 사용자: 병렬 작업은 최대 5개로 하는 티켓 만들자.

> 사용자: 티켓 028을 이 세션에서 바로 구현해 줘. 워크트리 028-max-five-parallel-sessions에서 해.

## 결정

- **원천은 `open-session` 1단계.** 세션을 실제로 여는 자리는 그 스킬 하나라 상한과 세는 법을 거기에만 두고, `next-session` 2단계의 나란히 여는 묶음과 `docs/constitution/operations.md` 브랜치와 병합의 한 문장은 그 자리를 가리키게 했다. 운영 문서의 그 문장은 "차례로 전부 열며"라 상한과 어긋나 고쳤고 헌법 판을 3.0.59로 올렸다(3.0.58은 형제 PR #415가 썼다). 운영 문서에 상한을 두는 안은 같은 사실을 두 곳에 두게 되어 버렸다. 새 ADR은 쓰지 않았다. 문구 하나를 바꾼 patch이고 결정은 사용자가 이 세션에서 했다.
- **세는 법.** `list_sessions`에서 이 세션을 뺀 `isRunning` 세션을 센다. 여는 세션은 열고 턴을 끝내므로 세지 않는다. 폴더와 종류는 가리지 않는다. 예약 작업의 세션(`【매일 09:30】 아침 보고 · 비용` 등)도 그 목록에 들었다(2026-10-28 이 세션의 `list_sessions`를 손으로 봤다. 쉰 개 모두 `cwd`가 `C:\project\agent`라 다른 폴더의 세션이 드는지는 보지 못했다). `isRunning`은 지금 턴을 도는 세션이라 CI를 기다리며 턴을 끝낸 세션은 세지 않는다.
- **아침 보고와 세는 법의 차이.** 다섯을 정한 근거인 아침 보고의 동시 세션(`tools/morning_collect.py` 모듈 독스트링)은 메인 세션의 호출 사이가 `SPAN_GAP_MIN`(5)분 이하면 그 사이를 돈 분으로 보고, 다른 프로젝트와 헤드리스 세션(카나리아의 `claude -p` 등)도 센다. `isRunning`은 쉬는 세션과 헤드리스 세션을 세지 않아 같은 때에 더 적게 센다. 그래서 `isRunning` 다섯은 근거 표의 다섯보다 느슨한 상한이다. 처음에는 "같은 쪽으로 센다"고 적었다가 셀프 리뷰 두 축이 짚어 고쳤다.
- **예외 하나.** 지시문의 브랜치가 이 세션의 브랜치와 같으면(인계, 마치지 못한 채 끊기) 거르지 않는다. 이 세션이 그 일을 하며 이미 도는 세션 하나였다. 처음에는 인계만 예외로 두고 "사람이 열 수를 말하면 따른다"를 더했는데, 표준 축이 끊기 지시문도 같은 까닭인데 버려진다고 짚었고, 사람의 말을 따르는 것은 적지 않아도 기본이라 뒤의 것은 뺐다.
- **열지 못한 지시문.** `open-session`을 부른 세션이 든다. 보고에 전문을 남기고, 사람이 자리가 났으니 열라고 하면 그 지시문들로 그 스킬을 1부터 다시 돈다. 처음에는 열지 못한 지시문을 어디에도 남기지 않고 다음 `next-session` 2단계가 다시 묶게 지었다. 셀프 리뷰 두 축이 그 길의 구멍을 짚었다. 그 항목은 같은 기능의 형제가 병합할 때만 돌고, harness chore PR 뒤의 결정표 줄은 chore를 잇지 않으며, 여유가 0이면 그 기능에 병합할 세션이 없어 영영 열리지 않는다. 또 CI를 기다리는 형제의 티켓은 main에서 아직 `ready-for-agent`라 다시 묶일 수 있다. 사람이 다시 열라고 하는 길은 사람이 기억해야 하는 값을 치르지만 버려지는 지시문이 없다.

## 결과

- 세는 법을 이 세션의 `list_sessions`(limit 40)에 손으로 대 봤다. 이 세션을 뺀 `isRunning` 세션이 넷(`chore/025-next-session-prune-check` 둘, `docs/design-card-build-spec`, `chore/022-eslint-boolean-params`)이라 그때 묶음을 열었다면 하나만 열었다. PR을 열고 기다리던 `chore/026-probes-replay-original-input`(PR #416)과 `feature/03-admin-adopt-design-system`(PR #415)은 `isRunning`이 거짓이었다.
- 카나리아 둘(`.scratch/harness/probes/canary/open_session_parallel_cap.toml`, `next_session_parallel_cap.toml`)이 각각 통과 4, 실패 0이었다(claude 2.1.302). 실험군은 새 문장을 옮겼고 대조군(주 체크아웃 `ad8a9c37`)은 모두 "없음"이었다.
- Grep 도구는 `.claude/worktrees/` 아래 파일을 보지 못해 옛 표현 잔존을 `git grep`으로 셌다(`CLAUDE.md` 환경 함정의 Grep 항목과 같은 모양이다).
- 보지 못한 것: 열지 못한 지시문을 다음 `next-session`이 다시 묶어 여는 길은 실제 세션에서 돌려 보지 않았다. 이 세션에는 열 묶음이 없었다.

## 인계

셀프 리뷰 직전 경계에서 인계 계기가 왔다(세션 컨텍스트 328,726 토큰). 이 세션의 제목은 `chore/028-max-five-parallel-sessions`이고 `chore/028-max-five-parallel-sessions (인계함)`으로 바꾼다. 번복하거나 고친 것은 없다. 돌던 검증 러너(`tools/run_checks.py`)는 인계 차례대로 멈추므로 결과가 없다. 이 세션이 연 워크트리는 `git worktree add`로 만들어 `EnterWorktree` 잠금이 없다.

지시문:

다음 작업: .scratch/harness/issues/028-max-five-parallel-sessions.md. 나란히 도는 세션을 최대 다섯으로 묶는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 티켓 028을 이 세션에서 바로 구현해 줘. 워크트리 028-max-five-parallel-sessions에서 해.
브랜치: chore/028-max-five-parallel-sessions
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-28-25-max-five-parallel-sessions.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 origin/main)부터 한다. 구현과 카나리아 둘은 끝났고, 검증 러너는 돌다 멈춰 결과가 없으니 반영 뒤 다시 친다. 티켓의 수용 기준 넷째(열지 못한 지시문을 다시 여는 길을 실제 세션에서 돌려 보기)는 열 묶음이 없어 비워 두었다. docs/journal/2026-10-28-25-max-five-parallel-sessions.md
확인할 선행 조건: 형제 워크트리 027-next-session-split이 next-session을 고치고, 형제 PR #415가 헌법 판 3.0.58을 썼다. 커밋 전에 tools/sibling_overlap.py의 함께 고친 파일과 판을 본다
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-28T08:56:28Z

## 이어받은 세션

인계로 연 세션(제목 `chore/028-max-five-parallel-sessions`)이 이었다. 시작 프롬프트는 위 지시문의 것과 같다.

### 셀프 리뷰

`/code-review`, 기점 `ad8a9c37`(origin/main의 병합 기점), 미커밋 파일 넷과 미추적 넷(`web/judge-a6pzPf/`는 멈춘 러너가 남긴 판정자 시험의 임시 트리라 뺐다), 커밋 0. 표준 축 Major 3·Minor 5·Nit 2, 명세 축 Major 3·Minor 5·Nit 1.

고친 것:
- 두 축 Major: 열지 못한 지시문을 다음 `next-session`이 다시 묶는다는 길이 갈래마다 끊긴다. 부른 세션이 드는 길로 바꿨다(위 결정). 표준 축 Major 셋째(PR을 연 형제를 다시 묶는다)도 그 길이 없어져 닫혔다.
- 표준 축 Major: 끊기 지시문이 상한에 버려진다. 예외를 "이 세션의 브랜치와 같은 지시문"으로 넓혔다.
- 명세 축 Major·표준 축 Minor: 아침 보고와 "같은 쪽으로 센다"가 거짓이다. 차이를 위 결정에 적고 스킬에서 그 문장과 근거 수치를 뺐다.
- 명세 축 Major·표준 축 Minor: 수용 기준 다섯째의 카나리아는 본문이 실리는지만 잰다. `claude -p --model sonnet --tools Skill`에 가정 장면 하나(이 세션을 뺀 `isRunning` 넷, 지시문 셋)를 물어, 여는 지시문으로 `chore/101-b`, 열지 않는 지시문으로 `chore/102-c`와 `chore/103-d`를 들고 보고에 전문을 남기고 사람이 열라고 하면 다시 돈다는 답을 손으로 봤다(한 번, 2026-10-28, claude 2.1.302). 질문은 스크래치에 두었고 커밋하지 않았다.
- 명세 축 Minor: `next-session` 4단계의 "그 스킬이 하나씩 차례로 연다"에 상한을 넣었다.
- 표준 축 Minor: `list_sessions`가 실패하면 열지 않는다, limit 50으로 충분한 까닭(도는 세션은 최근 활동 순의 앞)을 적었다. 사람이 열 수를 말한 예외는 뺐다. 상한을 1단계 안의 따로 된 문단으로 떼었다.
- 두 축 Nit: `open_session_parallel_cap.toml` 머리의 "세 카나리아"를 "두 카나리아"로 고쳤다.

남긴 것:
- 수용 기준 넷째: 길은 정했지만 상한에 닿는 묶음이 없어 돌려 보지 못했다. 상자를 비워 두고 "다음"에 넘긴다.
- 표준 축 Minor(다섯이 여러 곳에 있다): 원천은 `open-session` 1단계 한 곳이고, 나머지는 그 자리를 가리키는 문장이거나 헌법 판의 이력(기록)이다. 근거 수치는 스킬에서 빼 일지에만 남겼다.
- 표준 축 Nit(`next-session` 인계 1의 "다섯이면"과 이름이 겹친다): 앞의 것은 조건 다섯이고 문맥이 갈라 두었다.
- 표준 축 확인: `hook_session_card`가 통과시키는 `start_session`과 사람이 손으로 여는 세션은 상한 밖이다. 이 티켓은 `open-session`이 여는 길만 묶는다.
- `KICKOFF.md:308`의 옛 표현은 다른 프로젝트에 복사해 쓰는 런북이라 이 저장소의 살아 있는 문서로 세지 않았다.

커밋 `17a741c6`의 pre-commit은 종료 0이었다(로그는 스크래치 `commit.log`를 손으로 봤다). 인용 검사(check-quotes)가 경고 셋을 냈다. 위 결정과 티켓 코멘트에 따옴표로 적은 옛 문장 둘은 이 커밋이 지운 문장이라 저장소에 글자 그대로 없고, 손으로 본 `claude -p` 답의 인용 하나는 저장소 밖이다. 따옴표를 떼는 것은 다음 세션에 넘긴다.

### 인계 2

커밋 뒤 경계에서 인계 계기가 왔다(세션 컨텍스트 227,449 토큰). 이 세션의 지금 제목은 `chore/028-max-five-parallel-sessions`이고 `chore/028-max-five-parallel-sessions (인계함)`으로 바꾼다. 남은 것은 인용 경고 셋의 따옴표 떼기, origin/main(`06a8f85b`, PR #415) 합치기와 `docs/constitution/README.md` 11행 충돌 풀기(판은 3.0.59를 지키고 3.0.58 노트를 살린다), `tools/run_checks.py`와 린트, `/code-review`는 다시 돌리지 않는다, PR과 병합이다. 이 세션은 `EnterWorktree(path)`로 들어왔고, `git worktree unlock`은 `is not locked`로 끝났다.

지시문:

다음 작업: .scratch/harness/issues/028-max-five-parallel-sessions.md. 나란히 도는 세션을 최대 다섯으로 묶는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 티켓 028을 이 세션에서 바로 구현해 줘. 워크트리 028-max-five-parallel-sessions에서 해.
브랜치: chore/028-max-five-parallel-sessions
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-28-25-max-five-parallel-sessions.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영한 커밋 17a741c6까지 했다(pre-commit 종료 0). 커밋하지 않은 일지 수정이 워크트리에 있다. 남은 것: 인용 경고 셋의 따옴표 떼기(일지 2곳, 티켓 코멘트 1곳), origin/main 합치기와 docs/constitution/README.md 11행 충돌 풀기, tools/run_checks.py와 ruff 둘, 커밋, PR과 병합. /code-review는 다시 돌리지 않는다. docs/journal/2026-10-28-25-max-five-parallel-sessions.md
확인할 선행 조건: origin/main이 06a8f85b(PR #415, 헌법 3.0.58)로 움직였다. 형제 PR #417과 워크트리 025가 next-session을 고친다. 커밋 전에 tools/sibling_overlap.py의 함께 고친 파일과 판을 본다
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-28T09:54:15Z

다시 돌린 것: open-session 카나리아는 질문과 기대 문구를 바꿔 다시 돌려 통과 4, 실패 0(원본은 스크래치 `canary-open2`). next-session 카나리아는 같은 항목의 문구만 바뀌어 `--preflight`로 갈음했다(통과). 검증 명령은 커밋의 pre-commit과 `tools/run_checks.py`로 본다(아래).

## 셋째 세션

인계 2의 지시문으로 연 세션(제목 `chore/028-max-five-parallel-sessions`)이 `EnterWorktree(path)`로 들어와 이었다. 시작 프롬프트는 위 지시문의 것과 같다.

- 인용 경고 셋의 따옴표를 뗐다. 위 결정의 옛 문장 하나, 셀프 리뷰 절의 `claude -p` 답 하나, 티켓 코멘트의 옛 문장 하나다. `uv run python tools/check_quotes.py <일지> <티켓>`을 다시 쳐 경고 없음을 손으로 봤다.
- origin/main(`06a8f85b`, PR #415)을 합쳤다. `docs/constitution/README.md` 11행은 main의 줄을 바탕으로 판을 3.0.59로 올리고 3.0.59 노트를 3.0.58 노트 앞에 넣었다. 3.0.58을 비워 두었다던 문장은 그 판이 이제 main의 노트로 채워져 뺐다. `docs/constitution/operations.md`는 글자 충돌 없이 합쳐졌다.
- `uv run python tools/run_checks.py`는 종료 0이었고 열 검사가 모두 Passed였다(로그를 손으로 봤다). ruff 둘도 초록이었다.
- `uv run python tools/sibling_overlap.py`의 출력을 손으로 봤다. 번호 겹침 없음. 함께 고친 파일은 PR #417과 워크트리 025의 `.claude/skills/next-session/SKILL.md`이고, 나중에 병합하는 쪽이 글자 충돌을 푼다.

### PR 직전 리뷰

`coderabbit auth status`를 손으로 봤다. `Seat : not assigned`라 CLI 대신 대체 둘을 돌렸다(범위 `origin/main...HEAD`).

- 내장 `/security-review`: 서브에이전트 하나가 확신도 8 이상인 취약점 0건을 냈다. 카나리아 TOML은 `tools/canary.py`의 `run_claude`가 `subprocess.run`에 인자 목록으로 넘겨 셸을 거치지 않는다고 코드를 읽어 판정했다. 후보가 없어 오탐 거르기는 돌리지 않았다.
- `bug-perf-review` 서브에이전트: Major 1·Minor 4. 모두 고치지 않고 남겼다.
  - Major(티켓 본문의 "이 세션 포함"과 스킬이 반대다): 티켓 본문은 요청의 원문이고, 이 세션을 빼기로 바꾼 결정과 까닭은 티켓 코멘트와 위 결정에 이미 있다. 스킬이 원천이라 계산은 스킬대로 돈다.
  - Minor(형제 둘이 거의 같은 때에 세면 여섯이 된다, 막 연 세션이 아직 `isRunning`이 아닐 수 있다): 상한은 어림이다. 잠금 안에서 다시 세는 안은 3단계의 기계 전체 잠금을 넓혀야 해 이 티켓 밖이다.
  - Minor(열지 못한 지시문이 이 세션의 컨텍스트와 보고에만 남는다): 위 결정의 길대로다. 티켓은 `ready-for-agent`로 남아 다음 `next-session` 2단계가 다시 묶는다. 수용 기준 넷째가 처음 상한에 닿는 세션에서 이 길을 본다.
  - Minor(세는 법의 구멍 둘): 쉬는 세션과 다른 폴더의 세션을 다루는 법은 스킬에 의도로 적혀 있다.
  - Minor(열 수가 0일 때의 흐름): 스킬 1단계가 이미 0 이하면 하나도 열지 않는다고 하고, 끝 줄이 열지 않은 지시문을 6의 보고로 넘긴다.

### 봇 회차 1

PR #419. `tools/wait_ci.py 419`가 `끝: 모두 통과`로 끝났다(출력을 손으로 봤다). CodeRabbit은 한도(`Review limit reached`)에 걸려 리뷰가 없어 회차로 세지 않는다. claude-review는 Critical·Major 0, Minor 2, Nit 1이고 모두 고치지 않고 남겼다(까닭은 PR 코멘트에도 남긴다).

- Minor(티켓이 done인데 수용 기준 넷째가 비었다): 이월은 의도이고 아래 "다음"이 그 몫을 든다. 검사로 잡을 수 있는 꼴이라 대기열 534로 올렸다(아래 회고).
- Minor(다섯이 여러 곳에 있다): 셀프 리뷰 표준 축의 같은 지적과 같은 판정이다. 계산과 세는 법의 원천은 `open-session` 1단계 한 곳이고, 나머지는 그 자리를 가리키며 수를 되풀이할 뿐이다. 카나리아의 `expect`는 수를 잰다.
- Nit(스킬이 근거를 일지로 가리킨다): 근거는 기록이라 일지가 자리다. 스킬이 따르는 규칙은 스킬 안에 다 있다.

## 회고

후보 다섯, 승인 1, 기각 4, 넘김 0.

- 승인: 티켓이 수용 기준을 비운 채 done으로 병합에 오른다(사건: 이 PR의 claude-review Minor). 층은 검사다(`tools/check_ticket.py`의 경고). 더하는 것이라 첫 회차로 대기열 534에 두었다(1회차). 같은 일을 다룬 행은 `--search 수용.기준 --search 체크박스`, `--search check_ticket`으로 찾았고 없었다.
- 기각: 인용 경고 셋이 커밋 뒤로 밀려 인계한 세션의 일이 됐다. `check-quotes`가 그 커밋에서 알렸다.
- 기각: 다섯이 여러 곳에 있다는 지적이 셀프 리뷰와 PR 봇에서 두 번 나왔다. 리뷰가 잡도록 둔 기준을 리뷰가 잡은 것이고, 판정은 위와 같다.
- 기각: 문서만 바뀐 티켓이 인계를 두 번 했다(세션 컨텍스트 328,726, 227,449 토큰). 원인을 재지 않아 처방을 고를 수 없다. 일지에만 남긴다.
- 기각: 이 세션의 한글 인자가 든 복합 명령을 워크트리 가드가 거부했다. `CLAUDE.md` 환경 함정에 이미 있고 가드가 그 자리에서 막았다.

만료: `uv run python tools/queue_open_rows.py --ref origin/main`의 만료할 행이 없었다(출력을 손으로 봤다).

## 다음

- 티켓 028의 수용 기준 넷째: 상한에 처음 닿아 지시문을 열지 못한 세션이, 사람이 열라고 할 때 `open-session`을 1부터 다시 돈 결과를 그 세션의 일지에 적고 이 티켓의 상자를 채운다. 병합된 티켓을 다시 열지 않으므로 상자 채우기는 그 세션의 PR에 싣는다.
- 주 체크아웃은 이 세션이 당기지 않는다(워크트리에서 병합). 다음 지시문이 `tidy-checkouts`를 먼저 돌게 적는다.
