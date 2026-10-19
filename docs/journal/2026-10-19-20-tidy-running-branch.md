# 2026-10-19 (20) tidy_checkouts judge 의 브랜치 지우기가 실행 중 세션의 제목을 본다 (대기열 286)

브랜치 `chore/tidy-running-branch`. 대기열 286을 chore 한 PR로 반영한다.

> 사용자: 대기열 286(tidy_checkouts.py judge의 브랜치 지우기 판정이 --running 제목을 보지 않는 열린 행)을 chore 한 PR로
> 반영한다. 행의 "어디로" 칸이 원천이다

지시문의 "어디서" 줄에 주 체크아웃 미갱신 머리가 없어 `tidy-checkouts`는 돌지 않았다. `EnterWorktree(name: tidy-running-branch)`가
거부 없이 워크트리를 만들었고(앞 세션에서 `EnterWorktree(path)`가 두 번 낸 "the protected checkout … could not be resolved"는
이번에 나지 않았다), `git branch -m`으로 브랜치 이름을 바꿨다. 세션 제목은 `chore/tidy-running-branch`다.

## 한 일

- `tools/tidy_checkouts.py`. `judge_branch`가 `running`(실행 중 세션의 제목)을 필수 인자로 받는다. 옛 몸통은 판정 1인
  `_judge_branch_merged`로 옮겼고, `judge_branch`는 그 판정이 `delete`일 때만 제목을 견주어 같으면 `keep`과
  `_RUNNING_REASON`("그 브랜치가 제목인 세션이 돈다", 워크트리의 판정 3과 같은 문구라 상수로 뺐다)으로 바꾼다. 판정 1이 남기거나
  넘긴 것은 그 이유를 그대로 든다(워크트리처럼 처음 어긋난 것을 이유로 찍는다). `_judge_all`은 `running`을 넘기고,
  `_remove_branch`의 재판정은 `()`를 넘긴다(`remove`처럼 세션을 보지 않는다. 그 하위 명령은 제목을 받지 않는다).
- 처음에는 제목을 글자 그대로 견줬다. 반박 시험(아래)이 윈도에서 `chore/x` 옆에 만든 `Chore/Upper`를 `for-each-ref`가
  `chore/Upper`로 찍는 것을 찾아, 체크아웃되지 않은 브랜치는 대소문자를 가리지 않고(`casefold`) 견주게 고쳤다. 잘못 맞아도
  남기는 쪽이다. 워크트리의 판정 3은 글자 그대로 두었다(`wt.branch in running`, 쥔 프로세스가 대신 잡는다).
- 독스트링: 체크아웃되지 않은 브랜치 문단에 판정 3의 제목, 대소문자, `remove-branch`의 재판정을 더했고, 못 보는 것에
  "제목이 브랜치 이름과 앞뒤 공백까지 같지 않은 세션" 항목을 더했다.
- 시험 넷(`tests/tools/test_tidy_checkouts.py`): 두 지우는 길 모두 남김과 판정 1의 이유 보존, 못 보는 것(앞뒤 공백, 워크트리의
  대소문자), 실제 임시 저장소의 `judge --running` 두 길과 다른 제목, 윈도에서 대소문자가 바뀌어 찍힌 브랜치(윈도면 그
  `for-each-ref` 출력까지 단언). 옛 `judge_branch` 호출 시험 둘은 `()`를 더했다.
- 변이 표(`.scratch/harness/probes/tidy_checkouts_mutations.toml`): 새 변이 셋(49 브랜치 판정 3을 끈다, 50 대소문자를 가린다,
  51 `judge`가 `running`을 넘기지 않는다)과 원문을 고친 48(`remove-branch`의 재판정)에 표지(`expect_output`)를 붙였다.
- `.claude/skills/tidy-checkouts/SKILL.md` 3의 체크아웃되지 않은 브랜치 문장이 판정 1과 판정 3의 제목을 든다. 그 카나리아로
  새 명세 `.scratch/harness/probes/canary/tidy_skill_running_branch.toml`을 썼다.
- 대기열 286을 닫았다.

## 검사

- TDD: 시험을 먼저 써 빨강을 봤다(통합 시험은 `브랜치를 지운다 chore/loose → … remove-branch …`가 찍혀 실패, 순수 함수 시험은
  없는 인자로 실패). 고친 뒤 `-k "브랜치 or 제목 or 대소문자"` 27건 초록(부하로 247초).
- 반박 시험(세션 스크래치패드의 `refute_286.py`, 커밋하지 않았다. 손으로 본 것이다): 임시 저장소에서 `main(["judge", …])`를
  가짜 `merged`로 불렀다. PR 머리로 지울 브랜치와 origin/main에 든 브랜치는 같은 제목이면 남고 제목이 없으면 지운다,
  `--running=<제목>` 꼴도 같다, 앞 토막만 같은 제목(`chore/x`)은 `chore/x-2`를 남기지 않는다, `refs/heads/` 를 붙인 제목과
  뒤 공백 제목은 지운다(못 보는 것), `main`은 브랜치 줄이 없다, 체크아웃된 브랜치는 워크트리 줄이 남긴다. 첫 회차에서
  `Chore/Upper`가 `chore/Upper`로 찍혀 글자 그대로의 판은 지울 후보로 냈고, 고친 뒤 `브랜치를 남긴다 chore/Upper`였다.
- 변이: `--since origin/main` 넷(48~51) 모두 기대대로 빨강. 일부러 없는 표지를 넣어 실패 출력을 본 뒤 고른 단언의 값이 든
  문구를 표지로 골랐다. 49는 단언에 판정을 메시지로 붙였다(`'delete' == 'keep'`만으로는 같은 시험의 다른 단언과 갈리지
  않는다). 표지를 넣은 회차도 넷 모두 기대대로. `--check` 136 모두 원문 있음.
- 카나리아 `tidy_skill_running_branch.toml`: 통과 4(claude 2.1.302). 실험군 셋이 새 두 문장을 옮겼고, 대조군(주 체크아웃
  `a7d93133`)은 "없음"이었다.
- `ruff check`·`ruff format --check`(바꾼 파이썬 둘)는 초록. 전체 검증(`tools/run_checks.py`)과 pyright·lint-imports는 아직 돌리지
  않았다.

## 셀프 리뷰에 밀 주장

반영 전이지만 이 세션이 새로 쓴 사실 문장이다. 셀프 리뷰와 PR 직전 리뷰가 겨냥한다.

- `judge_branch` 독스트링: "윈도에서 낱개 참조의 폴더가 이미 다른 대소문자로 있으면 `for-each-ref` 가 그 폴더의 이름으로
  찍어, 친 그대로인 제목과 갈린다", "테스트가 윈도에서 고정한다", "잘못 맞아도 남기는 쪽이다".
- 모듈 독스트링: "잠금과 쥔 프로세스는 워크트리의 것이라 보지 않고, `remove-branch` 의 재판정은 `remove` 처럼 세션을 보지
  않는다", 못 보는 것의 "체크아웃되지 않은 브랜치는 대신 잡는 것이 없어 지울 후보로 찍힌다".
- 새 시험의 독스트링: "대소문자를 가린 판은 그 세션의 브랜치를 지울 후보로 냈다(대기열 286 의 반박 시험)".

## 셀프 리뷰

새 세션(같은 브랜치, 워크트리에 `EnterWorktree(path)`로 들어갔다)이 `/code-review`를 돌렸다. 범위: base `a7d93133`, 바뀐
파일 다섯, 커밋 없음, 미추적 둘(카나리아 명세, 이 일지). 명세는 대기열 286 행의 "어디로" 칸이다. 표준 축은 sonnet·high다.

### 표준 축

Critical·Major 없음. Minor 셋과 Nit. 직접 잰 것: `tools/mutate.py --check` 136 모두 원문 있음, 카나리아 `expect` 두 문자열이
`SKILL.md`에 한 번씩, 새·바뀐 시험 10건 초록, 윈도에서 `chore/x`를 먼저 만들면 `Chore/Upper`가 `chore/Upper`로 찍히고 순서를
바꾸면 `chore/x`가 `Chore/x`로 찍힌다, `judge_branch`가 `" chore/x"`·`"chore/x "`·`refs/heads/chore/x`·`chore/x-2`를 지움으로
내고 `CHORE/X`를 남긴다.

1. Minor. `remove-branch`의 재판정이 세션을 못 보는 갈래(`judge --running chore/loose`가 남긴 브랜치를 `remove-branch`가 종료
   0으로 지운다)를 못 보는 것에 올리지 않았고 시험으로 고정하지 않았다(`.claude/rules/tools.md` 못 보는 것 항목). 워크트리의
   `remove`는 탐침과 쥔 프로세스가 받치지만 브랜치에는 받치는 것이 없다.
2. Minor. 새 못 보는 것 항목의 서술이 혼란스럽다. 체크아웃되지 않은 브랜치의 대소문자 접기는 보는 쪽인데 못 보는 것에 들었고,
   시험 이름은 "보지 않는다"인데 마지막 단언은 `"Chore/X"` → `keep`이다. "쥔 프로세스로 남지만"은 그 시험이 고정하지 않고,
   "지울 후보로 찍힌다"는 판정 1이 지울 것으로 낸 브랜치에만 맞다.
3. Minor. `.scratch/harness/probes/README.md`의 `tidy_checkouts_mutations.toml` 행이 "(표는 백서른셋)"이고 대기열 286의 변이와
   결과가 없다(`docs/agents/issue-tracker.md` 프로브마다 한 줄).
4. Nit. 대소문자 통합 시험은 윈도 밖에서 글자 그대로의 판도 통과한다. `_RUNNING_REASON`이 `_ACTIONS`와 `_HOLDER_LABELS`
   사이에 끼었다. `_judge_branch_merged`가 `contained`도 다루는데 이름이 절반만 말한다.
5. 냄새(판단). 워크트리는 글자 그대로(`wt.branch in running`), 브랜치는 `casefold`로 같은 개념을 다른 규칙으로 견준다.

### 명세 축

요구 넷은 모두 들었다. `casefold`는 범위 넘침이 아니라 "같은 이름"을 지키는 데 필요하다(packed-refs로 묶은 뒤 만든
`Chore/Upper`는 그대로 찍혀 독스트링의 "폴더가 이미 있으면" 조건과 맞고, 윈도에서 낱개 참조 `Feat`를 `feat` 옆에 만들면
git이 거부한다).

1. Major. 반박 시험이 찾은 입력(윈도에서 대소문자가 바뀌어 찍히는 브랜치)이 같은 판정의 체크아웃 견줌도 깬다.
   `_judge_all`의 `branch not in checked_out`과 `_remove_branch`의 `wt.branch == branch`. `chore/x` 옆에
   `worktree add -b Chore/Upper`로 만든 워크트리에 커밋하지 않은 파일을 두고 `judge`를 치면 워크트리 줄은 `남긴다 … 바뀐 파일이
   있다`인데 브랜치 줄은 `브랜치를 지운다 chore/Upper → remove-branch`이고, 그 명령은 종료 0으로 지워 워크트리의 HEAD
   (`ref: refs/heads/Chore/Upper`)가 끊긴다(`rev-parse HEAD` 1). base에도 있던 결함이다.
2. Minor. 판정 1이 넘긴 브랜치는 세션 이야기 없이 `브랜치를 넘긴다 chore/run — 병합된 PR 의 머리와 브랜치 끝이 다르다`로 나간다.
3. Minor. `judge` 뒤에 같은 제목의 세션이 열리고 `remove-branch`를 치면 지운다. 못 보는 것에도 스킬 3.2에도 없고, `되돌린다`
   뒤의 "judge를 한 번 더"도 `list_sessions`를 다시 읽으라고 하지 않는다.
4. Nit. 대기열 닫힘의 "변이 셋(표지 포함)"이 원문과 표지를 고친 48을 빠뜨렸다.

### 판정

명세 축의 탐침(세션 스크래치패드 `spec286/probe.py`)을 본 세션이 다시 돌려 명세 1을 재현했다(위 문구 그대로, 끝에
`for-each-ref`가 `chore/x`와 `main`만 찍었다).

- 고친다: 명세 1(체크아웃 견줌 둘의 대소문자), 표준 1과 명세 3(못 보는 것 항목과 시험), 표준 2(못 보는 것 항목과 시험 이름),
  표준 3(프로브 README 행), 표준 4의 `_RUNNING_REASON` 자리, 명세 4(닫힘 문구).
- 남긴다: 명세 2. 워크트리의 판정도 "병합된 PR 의 머리와 브랜치 끝이 다르다"를 세션보다 먼저 찍는다(`judge`에서 판정 1의
  `human`이 판정 3의 제목보다 앞이고, 모듈 독스트링 머리가 "처음 어긋난 것을 이유로 찍는다"). 넘긴 줄에는 명령이 붙지 않아
  지워지지 않는다. 명세 3의 `되돌린다` 뒤 재판정은 이 PR 전부터 있던 문장이고 워크트리에도 같은 틈이며, 새 못 보는 것 항목이
  그 틈(판정 뒤에 열린 세션)을 적는다. 표준 4의 윈도 밖 통과는 시험 독스트링과 변이 이름이 윈도라고 밝혔고 순수 함수 시험이
  윈도 밖에서도 접기를 고정한다. `_judge_branch_merged`의 이름은 git의 병합(끝이 main에서 닿는다)이 두 길을 모두 덮는다고 보아
  둔다. 표준 5는 워크트리 쪽이 286의 "어디로"(브랜치 지우기 판정) 밖이고, 제목이 맞지 않는 세션은 작업 디렉터리로 쥔 프로세스가
  판정 3에서 남긴다.

### 고친 것

- 명세 1: `same_branch(name, branch)`(대소문자를 가리지 않는 견줌)를 두고 세 자리(`judge_branch`의 제목, `_judge_all`의
  체크아웃 견줌, `_remove_branch`의 체크아웃 가드)가 같이 쓴다. 시험 `test_judge_와_remove_branch_는_대소문자가_바뀌어_찍힌_체크아웃된_브랜치를_지우지_않는다`를
  먼저 써 빨강(`브랜치를 지운다 chore/Upper`)을 봤다. 변이 둘(체크아웃 견줌 둘을 글자 그대로)을 더했고, 초록 기대이던
  "remove-branch: 체크아웃됐는지 보지 않는다"는 git의 `branch -D`가 대소문자가 바뀐 이름을 막지 않아 빨강 기대로 바꿨다.
- 표준 1·명세 3: 못 보는 것에 "`judge` 뒤에 열린 세션의 체크아웃되지 않은 브랜치"를 더하고
  `test_remove_branch_는_judge_가_세션으로_남긴_브랜치도_지운다`로 고정했다(지나간다고 단언).
- 표준 2: 못 보는 것 항목을 "제목이 브랜치 이름과 다른 세션"으로 다시 쓰고 시험 이름을
  `test_다른_제목은_보지_않고_대소문자만_다르면_브랜치에서는_같다고_본다`로 바꿨다. 꼬리 제목(`chore/x (인계함)`)을 입력에 더했다.
- 표준 3: 프로브 README 행에 대기열 286의 변이와 빨강 기대로 바꾼 가드, 일지 번호를 더했다.
- 표준 4: `_RUNNING_REASON`을 `_HOLDER_LABELS` 뒤로 옮겼다.
- 명세 4: 대기열 286 닫힘 문구의 수(시험 여섯, 변이 다섯을 더하고 셋을 고쳤다)를 고쳤다.

### 다시 돌린 것

- `tests/tools/test_tidy_checkouts.py` 전체 160 초록(152초). `ruff check`·`ruff format --check`(바꾼 파이썬 둘) 초록.
- 변이 `--since origin/main` 여덟 가운데 일곱이 기대대로였다. 어긋난 50(제목의 대소문자)은 고른 시험 둘 가운데 앞의 순수
  함수 시험에서 pytest가 멈춰 표지(통합 시험의 문구)가 찍히지 않은 것이라, 통합 시험 하나로 좁혀 번호로 다시 돌렸고
  기대대로였다(기준선 215초, 다른 세션이 함께 돌던 때다). `--check` 138 모두 원문 있음.
- 명세 축의 탐침(`spec286/probe.py`, 커밋하지 않았다. 손으로 본 것이다)을 고친 판으로 다시 돌렸다. `Chore/Upper` 워크트리의
  브랜치 줄이 사라지고 `remove-branch chore/Upper`가 `남겼다 chore/Upper — 체크아웃돼 있다`(종료 1)로 멈추며 워크트리의
  `rev-parse HEAD`가 0이었다.
- 손으로 치는 다섯(pytest, pyright, lint-imports, web, 린트)은 커밋의 pre-commit 결과로 갈음한다. 결과는 커밋 뒤 아래에 적는다.
- 첫 커밋 시도는 pre-commit의 pytest에서 막혔다. 이 브랜치가 건드리지 않은
  `test_hook_midturn_korean.py::test_트랜스크립트_파일이_없으면_기다리지_않는다`가 2.0초 상한에 2.6초였고(pytest 한 바퀴 546초,
  3495 통과), 나머지 검사(pyright, lint-imports, 타입 우회, run-hooks, web-verify, 린트 둘, 표·줄 구분·변이 표)는 초록이었다. 그
  시험만 따로 돌리면 통과했다. 일지 2026-10-19-03의 부하 실패와 같은 갈래로 보고 다시 커밋한다.

PR 직전 리뷰에 밀 새 사실 문장(반영으로 새로 썼다):

- `same_branch` 독스트링: "`for-each-ref` 는 그 폴더의 이름으로 찍고, 제목과 등록은 친 그대로다", "부르는 곳 셋 모두 맞으면
  남기므로 잘못 맞아도 남기는 쪽이다".
- 모듈 독스트링: "글자 그대로 견준 판은 윈도에서 대소문자가 바뀌어 찍힌 체크아웃된 브랜치를 지울 후보로 냈고 `remove-branch` 가
  지웠다", 못 보는 것의 "워크트리에서는 대소문자만 다른 제목도 그렇다", "워크트리는 그 세션이 작업 디렉터리로 쥐었으면 판정
  3의 쥔 프로세스가 남긴다", "옮기기 직전에 쥔 프로세스를 다시 보는 것도 없어 판정 1이 지울 것으로 낸 브랜치를 지운다".
- 새 시험 독스트링: "git 의 `branch -D` 도 대소문자를 가려 막지 않았다".
- 변이 표 주석과 README 행: "대소문자가 같은 이름은 git 이 `branch -D` 를 스스로 거부한다", "윈도에서 대소문자가 바뀌어
  찍힌 이름은 git이 막지 않아".

## 이어받은 일

- 앞 지시문의 "이어받을 상태": PR #295(병합됨)의 claude-review 셋째 회차 Nit(`limit_message`를 블록 묶기와 한도 판정으로
  나누기)은 PR 코멘트에만 있고, 일지 2026-10-19-03 "다음"의 `limit_message`·`_blocks` 같은 결과 시험과 함께 볼 일이다. 이 PR
  밖이라 "다음"으로 옮긴다.

## 인계

`/code-review`를 부른 직후 인계 계기가 왔다(셀프 리뷰 직전, 세션 컨텍스트 346,927 토큰). 리뷰 단계는 밟지 않았고, 새 세션이
셀프 리뷰부터 한다(고정점 origin/main, 명세는 `.scratch/retro-queue.md` 286 행의 "어디로" 칸). 변경은 모두 커밋하지 않은 채
워크트리에 있다. 이 세션의 제목은 `chore/tidy-running-branch`였고 `chore/tidy-running-branch (인계함)`으로 바꾼다. `## 다음`은
단계를 닫는 새 세션이 쓴다. 회고도 그 세션이 이 일지까지 읽고 돈다.

지시문:

```
다음 작업: 기능 harness. 대기열 286(tools/tidy_checkouts.py judge가 체크아웃되지 않은 로컬 브랜치를 지울 후보로 낼 때 실행 중 세션의 브랜치를 보지 않는 것)을 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 286(tidy_checkouts.py judge의 브랜치 지우기 판정이 --running 제목을 보지 않는 열린 행)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/tidy-running-branch
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-20-tidy-running-branch.md(한 일, 검사, 셀프 리뷰에 밀 주장, 이어받은 일, 인계)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main, 명세는 .scratch/retro-queue.md 286 행의 "어디로" 칸)부터 한다. 밀 주장은 일지 "셀프 리뷰에 밀 주장" 절이다. 리뷰 뒤 검증 명령(tools/run_checks.py, 린트 둘)은 아직 돌리지 않았다. 대기열 286은 이 세션이 이미 닫았다. PR #295의 Nit(limit_message 나누기)은 이 PR 밖이라 "다음"으로 옮긴다(일지 "이어받은 일"). 일지는 docs/journal/2026-10-19-20-tidy-running-branch.md이고 "## 다음"은 아직 없다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/tidy-running-branch (인계함)`으로 바꿨고, 백그라운드 작업은 없었으며, 워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-19T04:09:16Z

## 둘째 세션과 인계

> 사용자: 대기열 286(tidy_checkouts.py judge의 브랜치 지우기 판정이 --running 제목을 보지 않는 열린 행)을 chore 한 PR로
> 반영한다. 행의 "어디로" 칸이 원천이다

위 지시문으로 연 둘째 세션이다. 제목을 `chore/tidy-running-branch`로 붙이고 `EnterWorktree(path)`로 이 워크트리에 들어갔다(거부
없이 들어갔다). 셀프 리뷰(위 "셀프 리뷰" 절)를 돌려 명세 축의 Major(체크아웃 견줌의 대소문자)와 Minor를 고치고, 두 번째
커밋 시도에서 pre-commit 전부가 초록이었다(pytest 643초, web-verify 469초, run-hooks 150초). 첫 시도는 위 "다시 돌린 것"의
부하 실패다. 결정: 명세 축 지적 2(판정 1이 넘긴 브랜치)는 워크트리 판정의 순서를 따라 남겼고, 체크아웃 견줌의 대소문자는 286의
반박 시험 요구로 보아 이 PR에서 고쳤다.

커밋 직후 인계 계기가 왔다(커밋 뒤, 세션 컨텍스트 299,742 토큰). 첫 커밋 시도 뒤에도 같은 계기가 왔지만 그 커밋이 실패해
경계가 아니었다. 이 세션이 넘겨받은 경계는 `셀프 리뷰 직전`이라 같은 경계가 아니고, 곁 세션도 아니다(`get_session`의 `self`에
`parentSessionId`가 없다). 그래서 넘긴다. `origin/main`이 이 브랜치를 딴 뒤 PR #298만큼 앞으로 갔고 아직 합치지 않았다. 이 인계
절은 커밋하지 않았다. 이 세션의 제목은 `chore/tidy-running-branch`였고 `chore/tidy-running-branch (인계함)`으로 바꾼다.

지시문:

```
다음 작업: 기능 harness. 대기열 286(tools/tidy_checkouts.py judge가 체크아웃되지 않은 로컬 브랜치를 지울 후보로 낼 때 실행 중 세션의 브랜치를 보지 않는 것)을 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 286(tidy_checkouts.py judge의 브랜치 지우기 판정이 --running 제목을 보지 않는 열린 행)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/tidy-running-branch
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-20-tidy-running-branch.md(셀프 리뷰, 이어받은 일, 둘째 세션과 인계)
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰와 그 반영을 한 커밋(대기열 286)이 pre-commit 전부를 지났고, 남은 단계는 origin/main 합치기, PR 직전 리뷰(밀 주장은 일지 "셀프 리뷰 > 고친 것"의 "PR 직전 리뷰에 밀 새 사실 문장"), PR 열기, 봇 회차, 병합이다(일지 docs/journal/2026-10-19-20-tidy-running-branch.md). 아직 푸시하지 않았고 열린 PR이 없다. 일지의 "둘째 세션과 인계" 절은 커밋하지 않은 채 워크트리에 있다. 대기열 286은 이미 닫았다. PR #295의 Nit(limit_message 나누기)은 이 PR 밖이라 "다음"으로 옮긴다(일지 "이어받은 일"). 일지 "## 다음"은 아직 없다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/tidy-running-branch (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, `git worktree unlock`은 `is not locked`로 끝났다(이 세션이 `EnterWorktree(path)`로 들어간 이 워크트리는 잠겨 있지 않았다).

open-session을 부른다 2026-10-19T05:15:21Z

## 셋째 세션

> 사용자: 대기열 286(tidy_checkouts.py judge의 브랜치 지우기 판정이 --running 제목을 보지 않는 열린 행)을 chore 한 PR로
> 반영한다. 행의 "어디로" 칸이 원천이다

위 지시문으로 연 셋째 세션이다. 제목을 `chore/tidy-running-branch`로 붙이고 `EnterWorktree(path)`로 이 워크트리에 들어갔다(거부
없이 들어갔다). 남은 단계(origin/main 합치기, PR 직전 리뷰, PR, 봇 회차, 병합)를 잇는다.

### PR 직전

origin/main(`a89ec15c`, #298)을 합쳤다. 충돌은 없었다(겹친 파일은 프로브 README와 대기열이고 자동으로 합쳐졌다). #298이 바꾼
`.claude/rules/tools.md`는 PreToolUse 계기 훅의 항목이라 이 브랜치의 `tools/tidy_checkouts.py`에 닿는 새 규약이 없었다. 합친 뒤
`sibling_overlap`은 번호 겹침 없음이었다. 합친 트리에서 `tools/run_checks.py` 여덟 검사(pytest 406초, web-verify 439초)와 ruff
두 명령이 초록이었다.

`coderabbit auth status`가 `Seat: not assigned`라 대체 둘을 나란히 돌렸다.
- `/security-review`: 지적 없음. 새 하위 프로세스 호출이 없고, `--running` 제목은 `same_branch`의 견줌에만 쓰이며, 세 호출
  자리 모두 맞으면 남기거나 거부해 지우는 판정을 늘리지 않는다.
- `bug-perf-review`(기준 `a89ec15c`, 호출 38, 하네스가 센 도구 호출 39): 이슈 없음, 오탐 넷. 밀 주장 넷은 모두 임시 저장소
  실측과 맞았다(`pack-refs --all` 뒤에도 `chore/Upper`로 찍힌다, 대소문자를 바꾼 `branch -D FEAT/Z`가 체크아웃된 `feat/z`를
  지운다). 오탐으로 둔 것: 접은 견줌의 부수 효과 둘(`_judge_all`에서 그 브랜치의 `human` 줄도 빠진다, 리눅스에서 대소문자만
  다른 다른 브랜치에 `remove-branch`가 "체크아웃돼 있다"로 거절한다. 둘 다 남기는 쪽이고 `judge`가 후보로 내지 않는다),
  `merged.get(branch)`의 글자 그대로 견줌(바뀐 줄이 아니고 남기는 쪽), 윈도 전용 단언이 리눅스 CI에서 초록인 것(README가
  적어 둔 관행). 워크트리 가드가 그 리뷰의 스크래치 heredoc을 다섯 번 거부해, `same_branch`를 빈 문자열·`ß`·`None`으로 직접
  부르지 못하고 코드 읽기와 좁힌 시험 10건(48.55초)으로 갈음했다.

## 회고

세 세션 전부(이 일지의 "한 일"부터 "PR 직전"까지)를 원천으로 셋째 세션이 돌았다. 후보 아홉. 승인 넷, 기각 다섯, 넘김 없음.
넘긴 것이 없어 묻지 않았다.

승인(심각도 순):
- 첫 세션의 반박 시험이 판정을 깨는 입력(윈도에서 `for-each-ref`가 대소문자를 바꿔 찍은 브랜치)을 찾고도 고치던 견줌(세션
  제목)에만 넣었다. 같은 입력이 체크아웃 견줌 둘을 깨 체크아웃된 브랜치를 지우는 길은 셀프 리뷰 명세 축이 Major로 잡았다.
  `.claude/rules/tools.md`의 지우는 도구 항목(116·278이 낸 지침)을 반쯤 어긴 사건이라 회차로 센다. 검사로 판정할 수 없어
  행동이 일어나는 자리의 문장으로 승인했다. → 대기열 361(278의 2회차, 행은 1회차).
- 첫 세션이 `remove-branch` 재판정이 세션을 보지 않는 것을 독스트링 문단에만 적고 못 보는 것과 시험에 넣지 않았다. 셀프
  리뷰 표준 축이 Minor로 잡았다. `tools.md`의 못 보는 것 항목(187이 낸 지침)을 어긴 사건이라 회차로 센다. 판단이라 검사로
  옮길 수 없고 지침은 이미 그 자리에 있어 회차를 감시한다. → 대기열 362(187의 2회차, 행은 1회차).
- 둘째 세션의 첫 커밋이 이 브랜치가 건드리지 않은
  `test_hook_midturn_korean.py::test_트랜스크립트_파일이_없으면_기다리지_않는다`(2.0초 상한에 2.6초)로 pre-commit에서 막혔고
  따로 돌리면 지났다. 열린 306이 처방한 사건이다. → 대기열 306(7회차).
- 셋째 세션의 PR 직전 `bug-perf-review`가 워크트리 가드에 스크래치 heredoc을 다섯 번 거부당해 `same_branch`를 경계 입력으로
  부르지 못하고 코드 읽기와 좁힌 시험으로 갈음했다. 열린 320이 처방한 사건이다. → 대기열 320(2회차).

기각:
- 셀프 리뷰 표준 축 Minor 3(프로브 README 행의 "표는 백서른셋"과 286의 변이가 빠졌다). 리뷰가 제 몫을 했다. 그 README에서
  표의 수를 적은 행은 이 하나라, 수를 대 보는 검사를 세울 근거가 사건 하나로는 약하다.
- 셀프 리뷰 명세 축 Nit(대기열 286 닫힘 문구의 수). 리뷰가 제 몫을 했고 어긴 지침이 없다.
- 변이 50이 표지 없이 어긋난 것(고른 시험 둘 가운데 앞의 순수 함수 시험에서 pytest가 멈췄다). `tools/mutate.py`가 그
  자리에서 어긋남을 알렸고 시험을 좁혀 다시 돌렸다.
- 둘째 세션의 실패한 첫 커밋 뒤에 온 인계 계기. `next-session` "인계할 때" 1이 경계가 아니라고 가르게 했고 그대로 갈랐다.
- 셋째 세션이 대기열 diff를 통째로 찍어 결과가 73KB였다. 하네스가 결과를 파일로 돌렸고 그 뒤로는 줄을 골라 읽었다.

## 셋째 세션과 인계

회고 뒤에 `sibling_overlap`이 겹침 둘을 알렸다. 형제 `pre-commit-batch`가 대기열 358·359를, main이 일지 2026-10-19-11을
먼저 가져갔다. `--move`로 일지를 그날의 순번 12로, 새 행을 361·362로 옮겨 커밋했다(`f8334068`, pre-commit 전부 초록, pytest
439초). 그 사이 main에 #302(`tests.md`의 리눅스 조항)와 #299가 들어와 합쳤다. 대기열 끝의 새 행끼리 충돌해 351 뒤에 361·362를
두었고 pre-commit 전부가 초록이었다(`7157680e`). 새 `tests.md` 조항(`tests/tools/` 시험은 리눅스 CI에서도 돈다)은 이 브랜치의
시험 둘이 지킨다. 윈도 전용 단언은 `sys.platform` 조건 안에 있고, 리눅스에서는 `remove-branch chore/Upper`가 접은 체크아웃
가드에서 1로 멈춘다(코드를 읽었다).

푸시 직전에 main이 다시 움직였다(#300: pre-commit이 색인의 변이 표 원문과 카나리아 명세 모양을 본다). 이 브랜치의 변이 표와
카나리아에 닿아 합쳤다. 대기열 충돌 두 곳(인접한 286·287이 양쪽에서 닫혔다, 끝의 새 행)을 풀어 286은 이 브랜치의 닫힘, 287은
main의 닫힘, 끝은 358·359·360 뒤에 361·362로 두었다. 새 검사 둘을 손으로 쳐 보니 지났다(`tools/mutate.py --check` 138 모두
원문 있음, `tools/canary.py --shape` 통과). 그 병합 커밋의 pre-commit은 두 시도 모두 3563 통과·2 실패였고 실패한 시험이 달랐다.
첫째는 `test_mutate.py`의 시간 단언 둘(13.8초·8.7초 대 상한 8초)과 run-hooks의 `hook_push_behind_main` 어긋남 하나, 둘째는
`test_check_constitution_version.py`의 분리 HEAD 하나와 `test_hook_midturn_korean.py`의 시간 단언 하나, run-hooks의
`hook_journal_retro` 시간 초과 하나였다(둘째 시도는 pyright 126초, web-verify 1027초로 부하가 컸다). 실패한 넷은 단독으로 모두
통과했고(44초, 9.8초), run-hooks를 단독으로 돌리니 129건 어긋남 0이었으며, web-verify는 두 시도 모두 초록이었다. 그래서 일지
2026-10-19-04의 길대로 `SKIP=pytest,run-hooks,web-verify`로 커밋했다(`e097579c`, 나머지 검사는 초록). PR의 CI가 셋을 다시 돈다.
부하 실패는 회고에서 306에 이 일지를 이미 세어 회차를 더하지 않았다.

결정:
- 일지 번호는 푸시 뒤에도 main의 새 일지(`2026-10-19-13`)보다 앞이다. `sibling_overlap`이 `-16`으로 옮기라고 했지만, pre-commit
  한 바퀴가 부하로 13~17분이고 main이 그새 또 움직일 수 있어, 옮기기는 병합 직전의 마지막 커밋("## 다음"과 함께)에서 한다.
- PR #303을 열었다. 본문에 PR 직전 리뷰 결과와 위 SKIP 경위를 적었다. `@coderabbitai review` 코멘트는 남기지 않았다(인계
  경계 `PR 연 뒤`의 몫이다).

PR을 연 직후 인계 계기가 왔다(`PR 연 뒤`, 세션 컨텍스트 344,891 토큰). 이 세션이 넘겨받은 경계는 `커밋 뒤`라 같은 경계가
아니고, 곁 세션도 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). 그 전에 온 `커밋 뒤` 계기 넷은 넘겨받은 경계와
같아 넘기지 않았다. 이 인계 절은 커밋하지 않았다. 이 세션의 제목은 `chore/tidy-running-branch`였고
`chore/tidy-running-branch (인계함)`으로 바꾼다.

지시문:

```
다음 작업: 기능 harness. 대기열 286(tools/tidy_checkouts.py judge가 체크아웃되지 않은 로컬 브랜치를 지울 후보로 낼 때 실행 중 세션의 브랜치를 보지 않는 것)을 반영한다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 286(tidy_checkouts.py judge의 브랜치 지우기 판정이 --running 제목을 보지 않는 열린 행)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/tidy-running-branch
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 일지의 "셀프 리뷰", "이어받은 일", "셋째 세션과 인계" 절
이어받을 상태: 인계: PR 연 뒤. PR #303이 열려 있고 순서 1의 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. 일지의 "셋째 세션과 인계" 절은 커밋하지 않은 채 워크트리에 있다. 병합 직전의 마지막 커밋에서 할 일이 둘이다. sibling_overlap --move로 일지 번호를 main의 최신 일지 뒤로 옮기고, 일지 "## 다음"을 쓴다(PR #295의 Nit인 limit_message 나누기를 "이어받은 일"에서 옮긴다). 회고는 이미 돌았다(일지 "## 회고"). 이 PC는 다른 세션의 부하로 pre-commit의 시간 시험이 시도마다 다르게 빨갰다(일지 "셋째 세션과 인계"). 일지는 docs/journal/2026-10-19-20-tidy-running-branch.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/tidy-running-branch (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, `git worktree unlock`은 `is not locked`로 끝났다.

open-session을 부른다 2026-10-19T06:56:30Z

## 넷째 세션

> 사용자: 대기열 286(tidy_checkouts.py judge의 브랜치 지우기 판정이 --running 제목을 보지 않는 열린 행)을 chore 한 PR로
> 반영한다. 행의 "어디로" 칸이 원천이다

위 지시문으로 연 넷째 세션이다. 제목을 `chore/tidy-running-branch`로 붙이고 `EnterWorktree(path)`로 이 워크트리에 들어갔다(거부
없이 들어갔다). 순서 1의 2(봇 회차)부터 한다.

### 봇 회차

PR #303의 head(`e097579c`)가 로컬 HEAD와 같았고, 검사 여섯(claude-review, python, web, e2e, visual, verify)은 이미 초록이었다.
CodeRabbit은 별이 적어 자동 리뷰를 하지 않았다는 코멘트만 있어 `@coderabbitai review`를 남기고 `tools/wait_ci.py 303`을
백그라운드로 띄웠다.

claude-review 첫 회차(`e097579c`)는 Minor 하나와 Nit 하나였다. 첫 회차라 지적마다 판단했다.
- Minor(워크트리 판정 3의 `wt.branch in running`이 글자 그대로라 체크아웃되지 않은 브랜치의 `same_branch`와 견줌 규칙이 둘이다):
  두고 이유를 남긴다. 뒤로 넘기지도 않는다. 두 규칙은 견주는 값의 출처가 달라 갈렸다. `same_branch`가 대소문자를 접는 것은
  `for-each-ref`가 윈도에서 폴더의 이름으로 찍어 친 이름과 갈리기 때문이고(그 독스트링), 워크트리의 `wt.branch`는 등록이라 제목처럼
  친 그대로다. 모아서 더 잡는 것은 사람이 제목을 다른 대소문자로 친 경우뿐이고, 그 세션은 작업 디렉터리로 쥔 프로세스가 판정 3에서
  남긴다. 셀프 리뷰 표준 5와 같은 지적이고 그때의 판단(워크트리 쪽은 286의 "어디로"인 브랜치 지우기 판정 밖이다)도 그대로다. 모으면
  모듈 독스트링의 못 보는 것 항목, 그 항목을 고정한 시험, `docs/constitution/operations.md`의 `EnterWorktree` 전 세션 확인("거르는
  법은 판정 3과 같다")까지 같이 바뀐다.
- Nit(`_remove_branch`가 `judge_branch`의 `running`에 `()`를 위치 인자로 넘긴다): 두고 이유를 남긴다. 같은 함수의 `remove` 재판정
  (`judge(wt, facts, merged, (), ops.pid_alive, holders)`)이 이 PR 전부터 같은 꼴이고 바로 위 주석이 이유를 댄다. 한쪽만 키워드로
  바꾸면 두 재판정의 꼴이 갈리고, 바꾸면 변이 48의 원문도 함께 고쳐야 한다.

CodeRabbit 첫 회차(`a60e2ddd`..`e097579c`)는 "No actionable comments"였다. 병합 위험은 Minimal이고, 보안 구조 검토의 강화 제안
하나(`remove-branch`가 지우는 순간에도 세션을 보게 하라)는 이 PR 전부터 있던 한계라고 그 리뷰가 스스로 적었다. 모듈 독스트링의
못 보는 것("`judge` 뒤에 열린 세션의 체크아웃되지 않은 브랜치")과 시험 `test_remove_branch_는_judge_가_세션으로_남긴_브랜치도_지운다`가
이미 그 한계를 적고 고정한다. 그 리뷰가 시간당 한도 하나를 썼다고 알렸다("0 remain after this review").

고친 것이 없는 회차라 이 일지(번호 옮기기와 "다음")만 커밋해 푸시하고, 두 봇의 둘째 회차는 Critical·Major만 고친다. 보류
이유는 PR 코멘트로 남겼다. `sibling_overlap --move`는 일지를 순번 20으로 옮겼다(처음 친 때는 19였는데 끝나기 전에 형제가
가져갔다, 부하로 2분을 넘겼다). 그 도구가 셋째 세션의 옮기기 기록(그때 순번 12로 옮겼다)까지 20으로 고쳐, 그 문장은 손으로
되돌렸다. 앞 지시문 두 곳의 "읽을 것" 경로가 20으로 바뀐 것은 지금 있는 파일을 가리키므로 두었다.

## 다음

- 대기열 286은 이 PR로 닫혔다. `tools/tidy_checkouts.py`를 대상으로 든 열린 행은 266(`judge` 끝의 이유별 요약 줄)과 361(대상은
  `.claude/rules/tools.md`이고 `tidy_checkouts`는 선례 인용)이고, 둘 다 286과 다른 주제다.
- PR #295(병합됨) claude-review 셋째 회차의 Nit: `tools/wait_ci.py`의 `limit_message`를 블록 묶기와 한도 판정으로 나눈다. 일지
  2026-10-19-03 "다음"의 `limit_message`·`tools/gh_run_summary.py`의 `_blocks` 같은 결과 시험과 함께, 두 파일 가운데 하나를 고칠
  때 한다. 코멘트에만 있던 일이라 여기 옮긴다(위 "이어받은 일").

## 넷째 세션과 인계

일지 번호 옮기기와 "다음"을 든 커밋(`e1a4a095`)이 pre-commit 전부를 지났다(pytest 395초, web-verify 407초, run-hooks 186초).
아직 푸시하지 않았다. 커밋 직후 인계 계기가 왔다(`커밋 뒤`, 세션 컨텍스트 220,002 토큰). 이 세션이 넘겨받은 경계는 `PR 연 뒤`라
같은 경계가 아니고, 곁 세션도 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). 그래서 넘긴다. 이 인계 절은 커밋하지
않았다. 이 세션의 제목은 `chore/tidy-running-branch`였고 `chore/tidy-running-branch (인계함)`으로 바꾼다.

결정: 두 봇의 첫 회차는 끝났다(claude-review는 Minor·Nit을 두었고 보류 이유를 PR 코멘트로 남겼다, CodeRabbit은 지적이 없었다).
남은 단계는 푸시, `@coderabbitai review`, 대기, 둘째 회차(Critical·Major만 고친다), 병합이다. 새 세션이 이 인계 절을 커밋하지 않은
채 `e1a4a095`만 푸시하면, 병합 직전에 일지만 바꾼 커밋 하나와 봇 회차가 한 번 더 든다. 그래서 푸시하기 전에 이 절을 새 세션의 첫
기록과 함께 커밋해 한 번에 푸시하기를 권한다. CodeRabbit은 첫 회차에서 시간당 한도를 다 썼다고 알렸으므로(07:03Z), 그 뒤 한 시간
안의 요청은 `Review rate limited`로 지나갈 수 있다. 그때 이 회차의 보안·버그 축은 PR 직전 리뷰의 결과(PR 본문)로 갈음한다
(`docs/constitution/operations.md` 리뷰 파이프라인의 초록 착시 목록).

지시문:

```
다음 작업: 기능 harness. 대기열 286(tools/tidy_checkouts.py judge가 체크아웃되지 않은 로컬 브랜치를 지울 후보로 낼 때 실행 중 세션의 브랜치를 보지 않는 것)을 반영한다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 286(tidy_checkouts.py judge의 브랜치 지우기 판정이 --running 제목을 보지 않는 열린 행)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/tidy-running-branch
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 일지의 "넷째 세션", "다음", "넷째 세션과 인계" 절
이어받을 상태: 인계: 커밋 뒤. PR #303이 열려 있고 커밋 e1a4a095(일지 번호를 20으로 옮기고 "다음"을 썼다)는 아직 푸시하지 않았다. 푸시와 순서 1의 2(봇 회차)부터 한다. 두 봇의 첫 회차는 끝났고 claude-review의 Minor·Nit 보류 이유는 PR 코멘트에 있어, 이번 푸시의 리뷰는 둘째 회차라 Critical·Major만 고친다. 일지의 "넷째 세션과 인계" 절은 커밋하지 않은 채 워크트리에 있고, 푸시 전에 함께 커밋하기를 권한다(그 절의 결정). 그 커밋 전에 sibling_overlap으로 일지 번호를 다시 본다. 일지는 docs/journal/2026-10-19-20-tidy-running-branch.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/tidy-running-branch (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, `git worktree unlock`은 `is not locked`로 끝났다.

open-session을 부른다 2026-10-19T07:35:23Z

## 다섯째 세션

> 사용자: 대기열 286(tidy_checkouts.py judge의 브랜치 지우기 판정이 --running 제목을 보지 않는 열린 행)을 chore 한 PR로
> 반영한다. 행의 "어디로" 칸이 원천이다

위 지시문으로 연 다섯째 세션이다. 제목을 `chore/tidy-running-branch`로 붙이고 `EnterWorktree(path)`로 이 워크트리에 들어갔다(거부
없이 들어갔다). `sibling_overlap`은 번호 겹침 없음이었고(origin/main은 `a60e2ddd` 그대로), 넷째 세션의 결정대로 "넷째 세션과
인계" 절을 이 절과 함께 커밋해 `e1a4a095`와 한 번에 푸시한다. 형제 PR #304(클라우드 세션, 대기열 271·274)가
`tools/tidy_checkouts.py`와 그 시험·변이 표·스킬을 함께 고쳐, 나중에 병합하는 쪽에 글자 충돌 후보로 찍혔다.

그 커밋(`9e2edec3`, pre-commit 전부 초록, pytest 598초)을 푸시하려 하자 `hook_push_behind_main`이 막았다. 그새 #304가 main에
들어왔다. 합치니 충돌이 둘이었다. `tidy-checkouts` 3의 한 문단은 두 쪽이 다른 문장을 고쳤다(#304는 독스트링을 `--help`로 보라는
문장을 넣었고 이 브랜치는 체크아웃되지 않은 브랜치 문장에 판정 3의 제목을 넣었다). main 판에 이 브랜치의 브랜치 문장을 넣었고,
이 브랜치 판에서 그 문장만 되돌리면 main 판과의 차이가 `--help` 문장의 삽입 하나뿐인 것을 스크립트로 봤다. 대기열은 끝의 새
행끼리라 361·362 뒤에 main의 363·364를 두었다. 자동으로 합쳐진 `tools/tidy_checkouts.py`에서 #304가 바꾼 자리는 설정 사본의
같음(`settings_equivalent`)과 `--help`라 이 브랜치의 브랜치 판정과 겹치지 않는다. 합친 판에서 `tools/mutate.py --check`는
`tidy_checkouts_mutations.toml` 138, `tidy_settings_equivalent_mutations.toml` 6 모두 원문이 있었고, 두 카나리아
(`tidy_skill_running_branch.toml`, `tidy_skill_help_doc.toml`)의 `expect` 문자열이 모두 스킬에 있었다. 해소 스크립트의
`Path.write_text`가 윈도에서 스킬을 CRLF로 써 git이 경고했고, 줄 끝을 LF로 되돌렸다(대기열 264와 같은 꼴, 커밋에서는 git이
고쳤을 것이라 사건으로 세지 않는다).

이 푸시의 봇 리뷰는 두 봇 모두 둘째 회차라 Critical·Major만 고친다. 그 회차에서 보류한 지적은 회차 세기와 뒤로 넘긴 일의
규칙대로 일지에 다시 적어 푸시하지 않고 PR 코멘트에 남긴다. 병합은 워크트리에서 한다. 주 체크아웃 미갱신: 루트는 main(병합 뒤
`tidy-checkouts`가 당긴다).
