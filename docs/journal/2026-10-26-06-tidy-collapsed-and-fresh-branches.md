# 2026-10-26 (06) tidy_checkouts 가 접힌 무시 폴더와 막 딴 브랜치를 바로 가른다 (harness 017)

## 구현

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "대기열 464·440을 티켓 .scratch/harness/issues/017-tidy-collapsed-and-fresh-branches.md로 쓰고 한다 / 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/017-tidy-collapsed-and-fresh-branches.md. tools/tidy_checkouts.py가 git이 접어 찍은 무시 폴더(web/apps/widget/public/) 때문에 병합된 워크트리를 남기는 것(대기열 464)과, 막 딴 형제 브랜치를 지우라고 내는 것(대기열 440)을 고친다 … 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. 나란히 연 여덟 가운데 여덟째라 `tidy-checkouts` 는 돌지 않았다(묶음의 첫 세션이 돈다).
- `EnterWorktree(017-tidy-collapsed-and-fresh-branches)` 뒤 워크트리 안에서 `git branch -m` 으로 `chore/017-tidy-collapsed-and-fresh-branches` 로 바꿨다. `sibling_overlap` 이 낸 다음 빈 번호가 일지 06·티켓 017이라, 일지 머리를 먼저 만들고 티켓을 쓴 뒤 다시 친 대조가 "번호 겹침 없음"이었다. 형제 016 의 일지가 `2026-10-26-07` 로 이름순 뒤에 선다.

### 손으로 본 것

둘 다 세션 스크래치패드의 셸 스크립트로 git 2.32.0.windows.2 의 임시 저장소에서 봤다(커밋하지 않았다. 시험이 같은 모양을 표지로 고정한다).

- `status --porcelain --ignored`(기본 `traditional`)는 무시된 것만 든 미추적 폴더를 그 폴더 하나로 접어 찍었다. `/w/public/fonts/`·`/w/public/element.js` 만 무시하고 `w/` 를 추적하지 않은 저장소에서 `!! w/` 하나였다(대기열 464 가 적은 `!! web/apps/widget/public/` 와 같은 결). `--ignored=matching` 은 `!! w/public/element.js`·`!! w/public/fonts/` 처럼 패턴에 맞은 자리만 찍었고, 무시된 `.env` 와 `__pycache__/` 가 함께 든 미추적 폴더도 둘로 풀었다. `--untracked-files=no` 와 함께 주면 128(`Unsupported combination`)이었다. `gather` 의 무시 목록 읽기는 기본(`normal`)이라 걸리지 않는다.
- `git log -g -n 1 --format=%gd --date=unix refs/heads/<브랜치>` 는 `chore/x@{1792996632}` 를 찍었다. 워크트리 안에서 `git branch -m worktree-x chore/x` 로 바꾼 브랜치는 바꾼 기록(`Branch: renamed …`)이 맨 위였다. `-c core.logAllRefUpdates=false` 로 딴 브랜치는 빈 출력에 0, 없는 브랜치는 128 이었다. 윈도에서 `Chore/Upper` 가 `chore/Upper` 로 찍힌 브랜치도 찍힌 이름으로 기록을 읽었다.

### 결정

- **464 는 `--ignored=matching` 으로 읽는다.** 대기열 행이 든 두 길 가운데 접힌 폴더를 `RECREATABLE_PATHS` 의 조상으로 받아 안을 다시 걷는 길은 git 이 이미 아는 무시 판정을 도구가 흉내 내야 한다. `matching` 은 git 이 패턴에 맞은 자리를 그대로 찍어 판정 2의 견줌이 바뀌지 않는다. `remove` 의 옮기기도 같은 목록을 쓰므로 풀어 읽은 항목이 하나씩 휴지통으로 간다.
- **`web/apps/widget/public/element.js` 는 `RECREATABLE_PATHS` 의 파일 자리다.** 이름이 흔해 자리째로 본다. 그 집합은 끝의 `/` 로 폴더와 파일을 가르고, 워크트리 판정(`unrecreatable`)과 등록 없는 폴더 판정(`_recreatable_file`)이 그 집합의 파일 자리를 함께 본다(덤프 접미사는 이 변경 전부터 워크트리 판정만 본다).
- **440 은 브랜치 reflog 의 마지막 기록으로 가른다.** 행이 든 "첫 기록 시각" 대신 마지막 기록을 고른 것은, 이 세션처럼 `EnterWorktree` 가 딴 `worktree-*` 를 `git branch -m` 으로 바꾸면 첫 기록은 딴 때이고 마지막 기록이 바꾼 때라서다. 창(`FRESH_SECONDS`)은 한 시간이다. 경합의 틈은 초 단위로 어림했고(재지 않았다) 브랜치를 먼저 따고 나중에 체크아웃하는 길까지 넉넉히 덮는 값이다. 떠난 세션의 브랜치는 다음 정리가 지운다.
- **창은 PR 없이 끝이 `origin/main` 에 있는 길에만 건다.** 병합된 PR 로 지우는 두 길(머리와 같은 끝, 머리보다 뒤인 끝)에 걸면, 주 체크아웃에서 병합하고 main 으로 옮긴 직후의 정리가 그 브랜치를 한 시간 남긴다.
- **기록이 없는 브랜치는 판정 1대로 지운다.** 막 딴 것인지 모르지만 잃는 것은 이름이고, 이 저장소의 기본 설정에서는 막 딴 브랜치에 늘 기록이 있다. 독스트링의 못 보는 것에 적고 시험으로 고정했다. 앞날 시각의 기록은 남긴다(시계가 어긋난 PC).
- **스킬은 3단계의 줄임 한 문장만 고쳤다.** tidy-checkouts 3단계의 체크아웃되지 않은 브랜치 문장에 "reflog의 마지막 기록이 한 시간 안이면 막 딴 브랜치라 남기고"를 더했다. 무시된 항목을 읽는 모드는 스킬이 원천으로 가리키는 독스트링에만 적었다.

## 검사

- `uv run python tools/run_checks.py`: 열 모두 Passed. pytest 1222.1초, web-verify 904.2초로 평소보다 느렸다(나란히 연 여덟 세션과 겹쳤다).
- `uv run ruff check .`, `uv run ruff format --check .`: 초록.
- 변이: `--check` 가 183개 원문 한 번씩. `--since origin/main` 으로 고른 열(바뀐 48·53, 새 176~183) 가운데 아홉이 기대대로였다. 177은 빨갰지만 표지가 찍히지 않았다. pytest 가 값 줄을 `['web/apps/wi...c/element.js']` 로 줄여 찍어서라, 표지를 `Left contains one more item: 'web/apps/widget/public/element.js'` 로 고쳐 번호로 다시 돌렸고 기대대로였다.
- 카나리아 `.scratch/harness/probes/canary/tidy_skill_fresh_branch.toml`: 통과 4. 실험군(이 워크트리) 셋이 새 문장을 글자 그대로 옮겼고, 대조군(주 체크아웃 `92b61458`)은 막 딴 브랜치가 없는 옛 문장을 옮겼다.

## 셀프 리뷰

`/code-review` 를 base `92b61458` 로 돌렸다. 커밋 0, 바뀐 파일 다섯, 미추적 셋.

### 표준 축 (sonnet, high)

Critical·Major 없음. 주장 검증에서 `touched_at` 의 경계 입력과 일지 "손으로 본 것"의 git 2.32 사실 문장을 임시 저장소로 다시 봐 모두 맞았고, 변이 번호와 대기열 닫힘 줄도 맞았다.

- 고침(Minor): `.scratch/harness/probes/README.md` 의 변이 표 줄이 "표는 백일흔다섯" 그대로였다. 2026-10-26 결과와 일지 번호를 더했다.
- 고침(Minor): 카나리아 명세의 "최신 결과 … 일지 2026-10-26-06" 이 일지에 없었다. 위 검사 절에 적었다.
- 고침(Minor): 변이 178의 표지 `widget/public/element.js` 는 값 문구이고, 181의 `assert 0 == 1` 은 반환 코드를 견주는 단언이면 어디서나 나온다. 맞지 않을 임시 표지로 한 번 돌려 실패 출력을 본 뒤, 178은 `등록 없는 폴더에 커밋에 없는 파일이 1개 있다: web/apps/widget/public/element.js`, 181은 `where 0 = main(['remove-branch', 'worktree-x'` 로 바꿔 다시 돌렸고 기대대로였다.
- 고침(Minor, 갈래 밟기): `judge` 가 두 목록을 읽는 사이에 형제 세션이 체크아웃한 오래된 브랜치(reflog 가 창 밖)는 지울 후보로 찍힌다. `remove-branch` 가 등록을 다시 읽어 막아 잃는 것은 없다. 독스트링 못 보는 것에 "체크아웃은 그 브랜치의 reflog 에 기록을 남기지 않아 지울 후보로 찍힌다. `remove-branch` 가 워크트리 등록을 다시 읽어 남긴다" 를 적고, git 호출을 감싸 브랜치 목록을 읽기 직전에 `git worktree add <경로> chore/old` 를 치는 시험으로 고정했다.
- 남김(Minor, Data Clumps): `contained`·`behind`·`fresh` 세 키워드 불리언이 판정 함수 넷을 함께 다닌다. `CODING_STANDARDS.md` 의 불리언 플래그 줄은 함수가 두 가지 일을 하는 모드 플래그를 겨누고, 이 셋은 순수 판정 함수에 넣는 브랜치의 사실이다. 앞의 둘은 이 변경 전부터 있었고 묶는 것은 따로 할 정리라 남긴다.
- 남김(Nit): 스킬의 "한 시간" 이 `FRESH_SECONDS` 와 값을 겹쳐 적는다. 스킬 3단계는 판정의 줄임이고 원천은 독스트링과 상수라고 스스로 적는다. 창을 바꾸면 카나리아의 `expect` 가 빨개져 알린다.
- 남김(Nit, Middle Man): `_fresh` 는 PR 이 있거나 `origin/main` 밖이면 reflog 를 읽지 않게 막는 일을 해 둔다(리뷰어도 그렇게 봤다).

### 명세 축 (Opus 5.5, 세션 노력 상속)

Critical·Major 없음. 수용 기준 1~7이 채워졌다고 봤다. 병합된 PR 두 길이 창을 보지 않는 것, reflog 없는 브랜치를 두 하위 명령이 지우는 것, 이 저장소에 `core.logAllRefUpdates=true` 가 있는 것, `remove` 의 다시 판정이 `matching` 으로 읽고 항목을 하나씩 옮기는 것, `public/fonts` 가 정션이어도 링크만 지우는 것을 임시 저장소와 직접 호출로 확인했다.

- 고침(Minor, 옛 판정을 되돌림): Grimp 는 `.grimp_cache/` 안에 `# Automatically created by Grimp.` 와 `*` 두 줄의 `.gitignore` 를 둔다(주 체크아웃의 2026-09-27 폴더를 손으로 봤다). 루트 `.gitignore` 는 그 폴더를 무시하지 않아, 옛 기본 모드는 `!! .grimp_cache/` 한 줄로 찍어 `RECREATABLE_DIRS` 의 이름과 맞았는데 `matching` 은 그 안을 하나씩 찍어 모두 다시 만들 수 없는 것이 됐다. 그 이름 하나를 더 받는 대신 조상 폴더가 다시 만들 수 있는 폴더(이름이나 폴더 자리)인 항목을 다시 만들 수 있는 것으로 본다(`_under_recreatable_dir`). 안의 하위 폴더(`sub/`)도 그 길로 지난다. 다른 `RECREATABLE_DIRS` 는 루트가 어느 깊이에서나 무시해 폴더째 찍힌다. 순수 시험에 Grimp 꼴과 반례(`a.grimp_cache/`, 파일 이름 `.grimp_cache`, `notes/`, 파일 자리를 조상으로 쓴 `element.js/x`)를, 실제 git 시험에 `.grimp_cache` 는 지우고 같은 꼴의 `notes` 는 남기는 둘을 더했고 변이 184 로 잰다.
- 고침(Minor, 틀린 사실): `_recreatable_file` 독스트링과 이 일지 결정의 "같은 집합" 이 거짓이었다. 덤프 접미사(`RECREATABLE_SUFFIXES`)는 이 변경 전부터 워크트리 판정만 본다. 동작은 두고 문장을 "`RECREATABLE_PATHS` 의 파일 자리는 워크트리 판정(`unrecreatable`)과 같이 본다. 덤프(`RECREATABLE_SUFFIXES`)는 워크트리 판정만 본다" 로 고쳤고, 티켓 기준 2 도 같은 뜻으로 고쳤다.
- 고침(Minor, 반박 입력을 다른 자리에): 이름 바꾸기(`chore/renamed`)와 앞날 기록(`ahead-clock`)을 `remove-branch` 에도 넣어 1 로 남기는지 본다.
- 고침(Nit): 앞날 기록에도 이유 줄이 "60분 안이다" 로 찍혔다. "60분 안이거나 앞날이다" 로 고치고, 못 보는 것에 "시계가 어긋난 PC 에서 남긴 앞날 시각의 기록. 막 딴 것으로 보아, 시계가 그 시각을 지나 창이 끝날 때까지 정리마다 남긴다(남기는 쪽이다)" 를 적었다(하루 앞 기록을 남기는 기존 시험이 고정한다). 스킬 문장은 줄임이라 앞날을 더하지 않았다.

### 반영하며 새로 쓴 사실 문장 (PR 직전 리뷰에 밀 주장)

- 독스트링 판정 2: "그래서 안쪽 `.gitignore` 로만 무시되는 폴더(`.grimp_cache/`)는 그 안의 항목이 하나씩 찍히고, 조상 폴더가 다시 만들 수 있는 폴더인 항목은 다시 만들 수 있는 것으로 본다."
- 독스트링 등록 없는 폴더의 링크 항목: "`.grimp_cache` 는 Grimp 가 그 안에 둔, `*` 줄이 든 `.gitignore` 로 무시된다. 주 체크아웃의 것을 손으로 봤다"
- 못 보는 것: "`judge` 가 워크트리 목록을 읽은 뒤 브랜치 목록을 읽기 전에 형제 세션이 체크아웃한 브랜치 가운데 reflog 의 마지막 기록이 창 밖인 것. 체크아웃은 그 브랜치의 reflog 에 기록을 남기지 않아 지울 후보로 찍힌다. `remove-branch` 가 워크트리 등록을 다시 읽어 남긴다."
- 못 보는 것: "시계가 어긋난 PC 에서 남긴 앞날 시각의 기록. 막 딴 것으로 보아, 시계가 그 시각을 지나 창이 끝날 때까지 정리마다 남긴다(남기는 쪽이다)."
- `_recreatable_file` 독스트링: "덤프(`RECREATABLE_SUFFIXES`)는 워크트리 판정만 본다."
- 이 일지 결정: "덤프 접미사는 이 변경 전부터 워크트리 판정만 본다"

### 다시 돌린 것

- `uv run pytest tests/tools/test_tidy_checkouts.py -q -n 4`: 222 passed.
- 변이: 임시 표지로 178·181·184 를 돌려 실패 출력을 본 뒤 표지를 달아 셋 모두 기대대로, 시험 이름이 바뀐 182·183 도 기대대로. `--check` 184개 원문 한 번씩.
- 손으로 치는 다섯은 커밋의 pre-commit 으로 갈음한다(결과는 커밋 뒤 아래에 적는다).
- 첫 커밋의 pre-commit 은 pytest 한 시험으로 막혔다(5607 통과, 1 실패, 1645초). 이 브랜치가 건드리지 않은 `tests/tools/test_rerun_runner.py` 의 `test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다` 다. 홀로 두 번 더 돌려 두 번 빨갰고(23초) 셋째에 지났다(31초). 빨간 회차의 임시 폴더에서 파일 시각을 보니, `hang=3.0` 인 B 회차가 36.06초에 끝나 A 의 두 번째 회차(36.92초)보다 앞섰고, 그 빈 자리에 각본 없는 C 회차가 열려 "호출"로 끝나 러너가 1을 냈다. 시험은 B 가 매달린 동안 A 의 두 회차가 끝난다고 기대하는데, 나란히 연 여덟 세션의 부하에서 A 의 두 번째 회차 하나가 9.4초였다. 부하에서 흔들리는 시간 시험의 새 사례라 ADR 0036 대로 고치지 않고 회차도 더하지 않으며, 커밋을 다시 쳤다.
