# 2026-10-19 (09) tidy_checkouts judge 의 브랜치 지우기가 실행 중 세션의 제목을 본다 (대기열 286)

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
읽을 것: docs/journal/2026-10-19-09-tidy-running-branch.md(한 일, 검사, 셀프 리뷰에 밀 주장, 이어받은 일, 인계)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main, 명세는 .scratch/retro-queue.md 286 행의 "어디로" 칸)부터 한다. 밀 주장은 일지 "셀프 리뷰에 밀 주장" 절이다. 리뷰 뒤 검증 명령(tools/run_checks.py, 린트 둘)은 아직 돌리지 않았다. 대기열 286은 이 세션이 이미 닫았다. PR #295의 Nit(limit_message 나누기)은 이 PR 밖이라 "다음"으로 옮긴다(일지 "이어받은 일"). 일지는 docs/journal/2026-10-19-09-tidy-running-branch.md이고 "## 다음"은 아직 없다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/tidy-running-branch (인계함)`으로 바꿨고, 백그라운드 작업은 없었으며, 워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-19T04:09:16Z
