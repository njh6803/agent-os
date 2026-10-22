# 2026-10-23 (10) 프로브 README 계기가 근거의 종류와 결과를 본 뒤 바꾼 기준을 밝히라고 짚는다 (harness 003)

## 구현 (첫 세션)

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "대기열 421을 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md로 쓰고 한다 / 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md. 프로브 README를 고칠 때 뜨는 계기 문장에, 결과마다 근거의 종류(탐침이 단언하거나 찍은 것, 저장한 원본을 손으로 본 것, 어림)와 결과를 본 뒤 바꾼 기준을 밝히라는 문장을 더한다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 6 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: 대기열 421을 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md로 쓰고 한다 / 브랜치: chore/003-probe-conclusion-evidence-kind / 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래 / 읽을 것: docs/agents/issue-tracker.md(harness 티켓의 서식·상태·번호). 나란히 여는 나머지 티켓: .scratch/harness/issues/004-optional-bool-annotation-check.md, 005-hook-report-prompt-notices.md, 006-eslint-judge-tree-cleanup.md, 007-env-read-glob-matches-rg.md, 008-quote-wrap-slash-comment.md / 이어받을 상태: 없음 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. 실행 중 세션의 시작 프롬프트와 다 견주지 못했다(검색 결과 수가 한도 50과 같았다) / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다.
- `tidy-checkouts`: 루트 main을 `9999e83e` → `975bf04c`(그때의 origin/main, #355)로 당겼다. 워크트리 `002-ui-design-skill`·`05-first-turn-ticket-notice`를 쥔 쉬는 세션 아홉(다섯과 넷)을 `end-holders`로 끝내고, 두 워크트리와 브랜치 `chore/002-ui-design-skill`·`feature/05-first-turn-ticket-notice`를 지웠다. 휴지통의 `worktree-overrides-pc-check~~.venv`는 `python.exe`(pid 41176)가 모듈을 쥐어 남았다.
- 첫 `judge`가 브랜치 `chore/006`·`007`·`008`을 "커밋이 모두 origin/main에 있다"며 지우라고 냈다. 나란히 연 형제 세션이 막 딴 브랜치였고, 그 세션들은 첫 `list_sessions`를 읽은 때 제목을 아직 바꾸지 않아 `--running`에 들지 않았다(005는 "훅 리포트 프롬프트 알림 처리"였다). 지우지 않고 목록을 다시 읽으니 넷 모두 브랜치 이름으로 바뀌어 돌고 있었고, 그 제목을 `--running`에 넣어 다시 친 `judge`에서는 그 줄이 사라졌다. 같은 판정에서 `007`·`008`은 "등록 없는 폴더인데 .git이 있다"로 넘겨졌는데, 다시 친 판정에서는 넘기는 줄이 없었다. 형제의 `EnterWorktree`가 도는 중에 판정이 그 자리를 본 것으로 어림한다(재지 않았다).
- `EnterWorktree(003-probe-conclusion-evidence-kind)` 뒤 `chore/003-probe-conclusion-evidence-kind`를 땄다. `sibling_overlap`이 다음 빈 번호로 티켓 009를 냈지만 지시문이 준 003은 아무도 쓰지 않아, 티켓을 쓴 뒤 다시 친 대조가 "번호 겹침 없음"이었다.

### 한 것 (커밋하지 않았다)

- 티켓 `.scratch/harness/issues/003-probe-conclusion-evidence-kind.md`(in-progress).
- `tools/hook_probe_conclusion.py`: 알림을 "아래 두 가지"로 나눴다. 첫째는 그대로의 셋째 항목이고, 둘째는 결과와 결론의 문장마다 근거의 종류(탐침이 단언하거나 찍은 것, 저장한 원본을 손으로 본 것, 어림)를 밝히고, 한 행에 섞이면 손으로 본 쪽에 그렇다고 붙이고, 결과를 본 뒤 바꾼 판정 기준과 까닭을 적으라는 것이다. 근거의 갈래와 사례는 `docs/agents/issue-tracker.md` 프로브와 근거 절을 가리킨다. 독스트링의 첫 문단, 왜(대기열 421의 세 사례), 못 보는 것 둘(README 밖의 결과, 근거를 이미 밝힌 편집)을 고쳤다.
- `tests/tools/test_hook_probe_conclusion.py`: 근거 몫을 단언하는 시험, 알림이 가리키는 절 제목이 문서에 있는지 보는 시험, 근거를 이미 밝힌 편집에도 알리는 시험을 더하고, README 밖 시험에 대기열 421의 두 자리(`tools/hook_choice_facts.py`, `contrast_module_mutations.toml`)를 더했다.
- 빨강: 알림을 고치기 전에 새 시험 하나가 `AssertionError: 탐침이 단언하거나 찍은 것`으로 빨갰고 나머지 23개는 초록이었다. 고친 뒤 24개 모두 초록.
- `tools/hook_payloads.toml`: 발동 사례의 `contains`에 "근거의 종류"와 `docs/agents/issue-tracker.md`를 더했다. `tools/run_hooks.py`: 156건 어긋남 0.
- 변이 `.scratch/harness/probes/probe_conclusion_hook_mutations.toml`: 줄 배치가 바뀌어 원문이 맞지 않게 된 "알림에서 규칙 파일 경로를 뺀다"를 고치고, 알림의 근거 몫 다섯과 문서의 절 제목 하나를 더했다. 스물둘 모두 기대대로였다(`mutate.py`가 찍었다). 새 표지의 양성 대조로 교차 사본 둘(15번에 14번 표지, 12번에 13번 표지)을 돌리니 둘 다 어긋났다. 그 프로브 README 행을 맞췄다.
- `docs/agents/issue-tracker.md` 프로브와 근거 절: 근거 항목에 "결과를 본 뒤 판정 기준을 바꿨으면 바꾼 기준과 까닭을 결과와 함께 적는다"를 더하고, 그 훅이 짚는 것을 적은 문장을 두 몫으로 고쳤다.
- 대기열 421을 이 티켓으로 닫았다.

### 결정

- 알림이 근거의 종류를 셋만 든다. 프로브 README의 결과는 탐침이 찍거나 손으로 보거나 어림하는 셋이 대부분이고, 코드 읽기와 웹 요약까지 든 갈래 전체는 그 절이 원천이라 알림은 그 절을 가리킨다.
- "결과를 본 뒤 바꾼 기준"을 알림에만 두지 않고 그 절의 근거 항목에도 한 문장으로 더했다. 알림이 그 절을 근거의 원천으로 가리키는데 그 절에 그 규칙이 없으면 가리킴이 비기 때문이다.
- `.claude/rules/probes.md` 셋째 항목의 "그 훅이 이 항목을 짚는다"는 지금도 맞아 고치지 않았다. 그래서 바뀐 rules가 없고 새 세션에서 rules를 불러 볼 몫도 없다.

### 고친 것 (이 세션이 스스로)

- 훅 독스트링의 왜에 처음 "그 절이 생긴 뒤에도 일곱 번 어겨졌다"고 적었다. 일곱은 닫힌 대기열 45의 회차부터 센 수라 틀렸고, 그 절이 선 뒤의 위반은 5~7회차 셋이라 "세 번(45부터 세어 5~7회차)"으로 고쳤다. 같은 문단의 "셋 다 프로브 README에 들었다"도, 첫째와 셋째는 훅 독스트링과 변이 표 머리에도 들어 "README에도"로 고치고 그 두 자리를 못 보는 것과 시험에 더했다.
- 프로브 README 행에 처음 "둘째의 실패 출력에는 `AssertionError: 저장한 원본을 손으로 본 것`만 있었다"고 적었다. 같은 출력에 그 단언의 `assert '...' in` 줄도 있어 지나쳤고, 첫째의 출력은 보지 않은 채였다. 둘의 실패 줄을 보고 "첫째가 근거 절 경로의 단언, 둘째가 손으로 본 것의 단언이었다"로 고쳤다. 고치기 전의 판으로 옛 사본의 이 훅이 떴다.

### 검사 (커밋 전, 셀프 리뷰 전)

- `uv run pytest -q tests/tools/test_hook_probe_conclusion.py`: 24 passed.
- `uv run ruff check .`, `uv run ruff format --check .`: 둘 다 0.
- `uv run python tools/run_hooks.py`: 훅 페이로드 156건 어긋남 0, 래퍼 알림 5건 어긋남 0.
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/probe_conclusion_hook_mutations.toml`: 변이 22 모두 기대대로.
- `uv run python tools/run_checks.py`(백그라운드): check-instructions, lint-imports, check-type-escapes, pyright, pyright-linux가 통과한 뒤, pytest와 web이 끝나기 전에 인계로 멈췄다(TaskStop).

### 인계 (셀프 리뷰 직전)

- `/code-review`(base `origin/main`)를 부르자 `hook_handoff`가 세션 컨텍스트 276,551 토큰으로 `셀프 리뷰 직전` 계기를 냈다. "인계할 때" 1의 다섯 가운데 맞는 것이 없어(요청 범위는 PR과 병합까지, 이어받을 상태 없음, `get_session`의 `self`에 `parentSessionId` 없음) 넘긴다. 셀프 리뷰의 단계는 밟지 않았다.
- 차례에서 대기 멈추기(검사 러너)를 제목 바꾸기보다 먼저 했다. 제목이 거절되면 이 세션에서 검사를 다시 돌린다.
- 이 세션의 지금 제목: `chore/003-probe-conclusion-evidence-kind`(인계 전).
- 지시문:

```
다음 작업: .scratch/harness/issues/003-probe-conclusion-evidence-kind.md를 잇는다. 프로브 README를 고칠 때 뜨는 계기 문장에, 결과마다 근거의 종류(탐침이 단언하거나 찍은 것, 저장한 원본을 손으로 본 것, 어림)와 결과를 본 뒤 바꾼 기준을 밝히라는 문장을 더한다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 421을 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md로 쓰고 한다
브랜치: chore/003-probe-conclusion-evidence-kind
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: .scratch/harness/issues/003-probe-conclusion-evidence-kind.md, docs/journal/2026-10-23-10-probe-conclusion-evidence-kind.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(미추적 티켓과 일지 포함)이 워크트리에 있고 셀프 리뷰(/code-review, base origin/main, 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md)부터 한다. docs/journal/2026-10-23-10-probe-conclusion-evidence-kind.md
확인할 선행 조건: 검사 러너(tools/run_checks.py)는 pytest와 web이 끝나기 전에 인계로 멈췄다. 셀프 리뷰를 반영한 뒤 커밋의 pre-commit으로 갈음하거나 다시 돈다
이번 요청 범위: PR과 병합까지
```

- 제목을 `chore/003-probe-conclusion-evidence-kind (인계함)`으로 바꿨다. 워크트리 잠금을 풀었다(`git worktree unlock C:/project/agent/.claude/worktrees/003-probe-conclusion-evidence-kind`, 출력 없음).
- open-session을 부른다 2026-10-22T17:58:24Z

## 셀프 리뷰와 PR (둘째 세션)

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "대기열 421을 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md로 쓰고 한다 / 다음 작업: .scratch/harness/issues/003-probe-conclusion-evidence-kind.md를 잇는다. 프로브 README를 고칠 때 뜨는 계기 문장에, 결과마다 근거의 종류(탐침이 단언하거나 찍은 것, 저장한 원본을 손으로 본 것, 어림)와 결과를 본 뒤 바꾼 기준을 밝히라는 문장을 더한다 / 다음 단계: 구현 / 어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다 / 시작 프롬프트: 대기열 421을 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md로 쓰고 한다 / 브랜치: chore/003-probe-conclusion-evidence-kind / 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래 / 읽을 것: .scratch/harness/issues/003-probe-conclusion-evidence-kind.md, docs/journal/2026-10-23-10-probe-conclusion-evidence-kind.md / 이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(미추적 티켓과 일지 포함)이 워크트리에 있고 셀프 리뷰(/code-review, base origin/main, 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md)부터 한다. docs/journal/2026-10-23-10-probe-conclusion-evidence-kind.md / 확인할 선행 조건: 검사 러너(tools/run_checks.py)는 pytest와 web이 끝나기 전에 인계로 멈췄다. 셀프 리뷰를 반영한 뒤 커밋의 pre-commit으로 갈음하거나 다시 돈다 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. `git worktree list`에서 브랜치가 워크트리 `003-probe-conclusion-evidence-kind`(`975bf04c`)에 있어 `EnterWorktree(path)`로 들어갔다. 커밋하지 않은 변경 아홉 파일(미추적 둘)이 첫 세션이 적은 대로 있었다.
- `git fetch origin` 뒤 `HEAD..origin/main`이 비었다(origin/main은 그대로 `975bf04c`). `sibling_overlap`: 번호 겹침 없음. 이름순으로 앞서는 형제는 없고 008(`2026-10-23-11`)이 뒤에 선다. 함께 고친 파일은 PR #296·#297과 형제 워크트리 다섯이 든 `.scratch/harness/probes/README.md`, `.scratch/retro-queue.md`, `docs/agents/issue-tracker.md`, `tools/hook_payloads.toml`이다.
- 셀프 리뷰(`/code-review`): base `975bf04c`, 바뀐 파일 일곱, 미추적 둘, 커밋 0. 표준 축(sonnet·high)과 명세 축을 나란히 띄웠다.

### 셀프 리뷰 보고

표준 축(Critical·Major 0). 밀어 본 주장(5~7회차와 세 사례, 셋 다 README에도 들었다, 두 파일의 자리, 변이 스물둘과 번호, 알림과 문서의 서술)은 모두 맞았다. 변이는 다시 돌리지 않았다.

1. Minor: 근거 몫 시험의 `"어림" in context`는 첫째 몫의 "어림이라고 적는다"에도 맞아, 둘째 몫에서 "어림인가."를 지워도 통과한다(알림 문자열에서 지워 `True`를 봤다고 했다). 그 종류만 뺀 변이도 없다.
2. Minor(판단): 알림이 근거의 종류를 셋 가운데 고르는 닫힌 물음으로 내, 절의 넷(프로브, 손, 코드 읽기, 어림)과 웹 요약 가운데 코드 읽기와 웹 요약의 칸이 없다. 절의 "손으로 돌려 본 것은 그 명령과 함께"도 알림에 없어 421의 둘째 사례(명령 없이 적은 문장)를 알림이 바로 짚지 못한다.
3. Nit: 근거를 이미 밝힌 편집의 시험이 결론이 아닌 편집의 시험과 같은 일을 하고, `json.loads(json.dumps(...))`의 까닭(`ToolInput`이 `file_path`만 든다)을 같은 파일의 다른 시험처럼 주석으로 적지 않았다.
4. Nit: `docs/agents/issue-tracker.md`의 "밝히라는 위 항목"에서 바로 위 항목은 웹 요약 항목이다.
5. Nit: 프로브 README 행이 커밋하지 않은 스크래치 사본으로 본 양성 대조에 "(`mutate.py`가 찍었다)"를 붙였다. 앞 판은 같은 대조를 "손으로 봤다"고 적었다. 기점도 "커밋 전 작업 트리"뿐이다.
6. Nit: 티켓 `Status`가 `in-progress`이고 수용 기준이 미체크다.
7. Nit: 새 규칙(결과를 본 뒤 바꾼 기준)이 `.claude/skills`에 0건이고 `code-review` 주장 검증 7에 없다.

갈래 밟기: 한 번 알린 뒤의 결과에 다시 알리지 않는 것은 독스트링의 못 보는 것에 이미 있다.

명세 축. 직접 돌린 것: 시험 24 passed, `run_hooks.py` 156건 어긋남 0, `mutate.py` 변이 22 모두 기대대로(종료 0). 셋째 항목 몫의 뜻은 기준 판과 같고, 수용 기준 6의 서술은 `context_for`가 내는 문장과 맞으며, 왜가 든 일지 셋의 내용도 맞았다.

1. Minor: 독스트링의 "그 절이 선 뒤에도 세 번 어겨졌다"는 닫힌 주장이 틀렸다. 열린 대기열 227이 "근거 절(대기열 45)이 지침이 된 뒤에도 어겼고"를 5회차로 세고(일지 2026-10-13-26~2026-10-22-08), 닫힌 303도 같은 경우다. 세 번은 421이 센 수다.
2. Minor: 시험이 "어림"과 "그 까닭"을 고정하지 못한다. 스크래치 스크립트로 `_BODY`에서 "어림인가"나 "그 까닭"을 빼도 단언이 모두 초록인 것을 손으로 봤다고 했다. 그 둘을 빼는 변이도 없다.
3. Minor: 절 제목 시험이 알림에서 절 이름을 읽지 않고 두 시험에 박은 문구로만 잇는다. 문서 제목을 바꾸며 그 시험만 고치면 알림이 없는 절을 가리켜도 초록이다.
4. Minor: 프로브 README 행의 스크래치 사본 대조 "(`mutate.py`가 찍었다)"가 421의 6회차와 같은 꼴이다. 알림의 근거 셋이 "명령이 있는가"를 가르지 않아 왜의 둘째 사례를 알림이 바로 덮지 못한다.
5. Nit: 못 보는 것의 "첫째와 셋째 사례는 … 에도 들었다"가 둘째 사례(명세에 들었다, 일지 2026-10-22-16)를 빠뜨렸다.
6. Nit: 페이로드 표 `contains`에 바꾼 기준의 문구가 없다.
7. Nit: `issue-tracker.md`의 "위 항목"이 헷갈린다(표준 축 4와 같다).

범위 넘침 Nit: 근거 항목에 더한 바꾼 기준의 문장은 티켓에 없지만 421이 "그 절을 어겼다"고 적은 것과 수용 기준 6의 서술이 참이 되려면 필요해 넘침은 아니고, 티켓 What to build에 한 줄 적으면 된다. 첫 세션의 결정이 든 까닭("가리킴이 비기 때문")은 알림이 그 절을 갈래와 사례로만 가리키므로 조금 어긋난다.

갈래 밟기 Nit: 못 보는 것 "한 번 알린 뒤의 결론"과 시험 이름 `README_밖에_적은_결론은`이 이번에 결과까지 넓힌 범위를 따라가지 않았다.

### 반영

판정의 근거: 명세 축 1은 대기열 227·303 행을 열어 맞는 것을 봤다. 명세 축 5는 일지 2026-10-22-16 회고 승인 2가 명세에 든 문장 셋을 든 것을 봤다. 두 축의 "어림" 단언은 알림 문장에 "어림이라고 적는다"가 첫째 몫에 있는 것으로 봤다.

고친 것:
- 알림(`_BODY`): "커밋하지 않은 스크립트나 사본으로 돌린 것도 손으로 본 것이고, 손으로 본 것은 그 명령과 함께 적는다."를 더하고(표준 2, 명세 4), 절을 가리키는 문장을 "코드 읽기와 웹 요약까지 든 근거의 갈래 전체와 사례는 `docs/agents/issue-tracker.md` 프로브와 근거 절이다."로 열었다(표준 2의 닫힌 물음).
- 시험: 종류의 단언을 "어림인가"로 좁히고, 새 문장 셋과 "바꾼 기준과 그 까닭"을 단언했다(표준 1, 명세 2). 절 시험은 알림에서 문서와 절 이름을 정규식으로 읽어 그 문서의 `## <절>` 줄을 댄다(명세 3). README 밖 시험에 `.scratch/model-rerun/spec.md`를 더하고, 못 보는 것 시험 둘의 이름을 결과까지 넓혔으며(`README_밖에_적은_결과와_결론은`, `결과도_결론도_아닌_편집에도`, `한_번_알린_뒤의_결과와_결론은`), JSON으로 칸을 싣는 까닭을 주석으로 적었다(표준 3, 갈래 밟기 Nit).
- 독스트링: 첫 문단에 명령 몫을 더했다. 왜의 닫힌 수를 "선 뒤에도 거듭 어겨졌다. 손으로 본 것에 측정 낱말(`쟀다`·`재니`·`실측`)을 쓴 갈래는 열린 대기열 227 이, 임시 스크립트의 결과를 명세에 프로브로 적은 갈래는 닫힌 303 이 따로 세고, 대기열 421 은 그 가운데 세 번(45 부터 세어 5~7회차)을 센다."로 고쳤다(명세 1). 못 보는 것을 "대기열 421 의 세 사례는 README 밖에도 들었다. 첫째는 훅 독스트링(`tools/hook_choice_facts.py`), 둘째는 명세(`.scratch/model-rerun/spec.md`), 셋째는 변이 표 머리(`.scratch/design-reverse-sync/probes/contrast_module_mutations.toml`)다."로 고치고(명세 5), 결론만 들던 항목 셋을 결과와 결론으로 넓혔다.
- 변이 표: 줄 배치가 바뀐 변이 셋의 원문을 고치고, 새 단언마다 그것만 빼는 변이 다섯(어림, 커밋하지 않은 실행, 명령, 까닭, 코드 읽기와 웹 요약)과 알림의 절 이름을 바꾸는 변이 하나를 더했다. 절 제목 변이의 표지는 시험의 새 메시지(`AssertionError: docs/agents/issue-tracker.md: 프로브와 근거`)로 바꿨다.
- `tools/hook_payloads.toml`: `contains`에 "그 명령과 함께"와 "결과를 본 뒤 판정 기준"을 더했다(명세 6).
- `docs/agents/issue-tracker.md`: "위 항목"을 "이 절의 \"근거는 무엇으로 섰는지 밝힌다\" 항목"으로 바꿨다(표준 4, 명세 7).
- 프로브 README 행: 변이 스물일곱과 대조군 하나로 맞추고, 결과를 이 판으로 바꿨다. 스크래치 사본의 양성 대조는 "커밋하지 않은 사본 표로 손으로 봤다"와 명령으로 적었다(표준 5, 명세 4).
- 티켓: What to build에 근거 항목의 문장과 명령 몫을 더한 까닭을 한 줄로 적고(범위 넘침 Nit), `Status: done`, 수용 기준을 체크했다(표준 6).
- 대기열 421의 닫힘 문구에 명령 몫을 더했다. 열린 227의 처방 칸에, 프로브 README는 이 훅이 이미 짚으니 반영할 때 두 계기의 겹침을 보라는 한 줄을 더했다(명세 1을 판정하며 227의 처방이 프로브 README도 대상으로 든 것을 봤다).

남긴 것:
- 표준 7(`code-review` 주장 검증 7에 바꾼 기준이 없다): 이 티켓의 범위는 알림이고, 그 항목은 근거의 종류를 다루며 바꾼 기준과 어긋나는 문장이 없어 잔존이 아니다. 스킬을 고치면 새 세션의 확인도 든다. 다음 회차가 나면 retro가 센다.
- 첫 세션의 결정이 든 까닭(위 "결정" 둘째 줄의 "가리킴이 비기 때문")은 명세 축의 지적대로 조금 어긋난다. 실제 까닭은 421이 "그 절을 어겼다"고 적었는데 그 절에 바꾼 기준의 규칙이 없었고, 수용 기준 6의 서술이 참이 되려면 그 절에 그 문장이 있어야 했다는 것이다. 기록은 고치지 않고 여기 적는다.
- 갈래 밟기의 두 길(결과가 아닌 첫 편집이 알림을 넘기는 틈, 워크트리 세션에서 주 체크아웃의 옛 알림이 도는 것)은 독스트링의 못 보는 것과 `.claude/rules/tools.md`에 이미 있다. 이 세션의 README 편집에도 옛 알림(셋째 항목만)이 떴다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 사실 문장): 위 고친 것의 따옴표 문장 넷(알림 두 문장, 왜, 못 보는 것), `issue-tracker.md`의 항목 이름 인용, 프로브 README 행의 2026-10-23 결과 문장, 대기열 227에 더한 문장.

다시 돌린 것:
- `uv run pytest -q tests/tools/test_hook_probe_conclusion.py`: 24 passed(반영 뒤 두 번).
- `uv run python tools/run_hooks.py`: 훅 페이로드 156건 어긋남 0, 래퍼 알림 5건 어긋남 0.
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/probe_conclusion_hook_mutations.toml`: 변이 28 모두 기대대로(종료 0).
- 양성 대조: 15번에 14번 표지, 22번에 21번 표지를 넣은 세션 스크래치패드의 사본 표(`swap_markers.toml`)를 같은 명령으로 돌려 둘 다 "표지 없음"으로 어긋났고(종료 1), 실패 줄이 명령의 단언과 `'## 근거'`의 단언인 것을 손으로 봤다.
- 잔존: 옛 표현 여덟을 저장소의 `*.md`·`*.py`·`*.toml`에서 Grep으로 찾아 살아 있는 문서에 0곳(남은 것은 기록인 일지와 다른 프로브의 "변이 스물하나").
- 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다. 결과는 커밋 뒤에 적는다.

### 커밋

- 커밋 직전: 브랜치 `chore/003-probe-conclusion-evidence-kind`, `sibling_overlap` 번호 겹침 없음(origin/main 그대로, PR #358이 `2026-10-23-11`로 이름순 뒤에 섰다).
- `ec920f03`(`chore: 프로브 README 계기가 근거의 종류와 결과를 본 뒤 바꾼 기준을 짚는다 (harness 003)`). pre-commit: ruff check·ruff format·checks(lint-imports, check-ticket, zizmor, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks 299.1s, web-verify 511.2s, pytest 568.8s)·markdown tables·line separators·mutation tables·quotes·commit message 모두 Passed. canary specs와 constitution version은 대상 파일이 없어 Skipped.

### 인계 (커밋 뒤)

- 커밋을 백그라운드로 띄우자 `hook_handoff`가 세션 컨텍스트 276,033 토큰으로 `커밋 뒤` 계기를 냈다. 커밋이 성공해 경계에 왔고, "인계할 때" 1의 다섯 가운데 맞는 것이 없다(요청 범위는 PR과 병합까지, 이어받은 경계는 `셀프 리뷰 직전`이라 다르다, `인계 못함` 줄 없음, `get_session`의 `self`에 `parentSessionId` 없음). 열린 PR이 없어 다음 단계는 이 세션 지시문의 "구현"을 그대로 옮긴다.
- 이 세션이 띄운 백그라운드 작업(리뷰 서브에이전트 둘, 변이 실행, 커밋)은 모두 끝났다.
- 이 세션의 지금 제목: `chore/003-probe-conclusion-evidence-kind`(인계 전).
- 지시문:

```
다음 작업: .scratch/harness/issues/003-probe-conclusion-evidence-kind.md를 잇는다. 셀프 리뷰를 반영해 커밋했고, PR 직전 리뷰와 PR, 병합이 남았다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 421을 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md로 쓰고 한다
브랜치: chore/003-probe-conclusion-evidence-kind
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: .scratch/harness/issues/003-probe-conclusion-evidence-kind.md, docs/journal/2026-10-23-10-probe-conclusion-evidence-kind.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영한 커밋까지 했고 푸시하지 않았다(PR 없음). 일지의 둘째 세션 절 가운데 "커밋"과 "인계 (커밋 뒤)"는 커밋 뒤에 적어 워크트리에 커밋하지 않은 채 있으니 다음 커밋에 싣는다. 남은 단계는 PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2. 밀 주장은 일지 "반영"의 "PR 직전 리뷰에 밀 주장" 줄), 푸시와 PR, 봇 회차, 병합이다. docs/journal/2026-10-23-10-probe-conclusion-evidence-kind.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `chore/003-probe-conclusion-evidence-kind (인계함)`으로 바꿨다. 잠금 풀기(`git worktree unlock C:/project/agent/.claude/worktrees/003-probe-conclusion-evidence-kind`)는 `is not locked`로 끝났다. 이 세션은 `EnterWorktree(path)`로 들어왔는데 그 워크트리가 잠기지 않았다(잠금이 어디서 풀렸는지는 보지 않았다).
- open-session을 부른다 2026-10-22T18:49:53Z

## PR 직전 리뷰와 병합 (셋째 세션)

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "대기열 421을 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md로 쓰고 한다 / 다음 작업: .scratch/harness/issues/003-probe-conclusion-evidence-kind.md를 잇는다. 셀프 리뷰를 반영해 커밋했고, PR 직전 리뷰와 PR, 병합이 남았다 / 다음 단계: 구현 / 어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다 / 시작 프롬프트: 대기열 421을 티켓 .scratch/harness/issues/003-probe-conclusion-evidence-kind.md로 쓰고 한다 / 브랜치: chore/003-probe-conclusion-evidence-kind / 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래 / 읽을 것: .scratch/harness/issues/003-probe-conclusion-evidence-kind.md, docs/journal/2026-10-23-10-probe-conclusion-evidence-kind.md / 이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영한 커밋까지 했고 푸시하지 않았다(PR 없음). 일지의 둘째 세션 절 가운데 \"커밋\"과 \"인계 (커밋 뒤)\"는 커밋 뒤에 적어 워크트리에 커밋하지 않은 채 있으니 다음 커밋에 싣는다. 남은 단계는 PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2. 밀 주장은 일지 \"반영\"의 \"PR 직전 리뷰에 밀 주장\" 줄), 푸시와 PR, 봇 회차, 병합이다. docs/journal/2026-10-23-10-probe-conclusion-evidence-kind.md / 확인할 선행 조건: 없음 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. `git worktree list`에서 브랜치가 워크트리 `003-probe-conclusion-evidence-kind`(`ec920f03`)에 있어 `EnterWorktree(path)`로 들어갔다. 거부 없이 들어갔다. 커밋하지 않은 변경은 이 일지 하나였다.
- `git fetch origin` 뒤 `HEAD..origin/main`이 비었다.

### PR 직전 리뷰

- `coderabbit auth status`: `Plan: Free`, `Seat: not assigned`. CLI가 돌지 못해 대체 둘을 나란히 돌렸다.
- `/security-review`: 식별 서브태스크가 "No vulnerabilities found"를 냈다. 런타임 변경이 `_BODY` 상수와 독스트링뿐이고, 페이로드 값이 출력에 실리지 않으며, 표지 파일 이름이 SHA-256 16진이라 경로를 벗어나지 못한다는 것을 따라갔다. 걸러 볼 후보가 없어 오탐을 거르는 서브태스크는 띄우지 않았다.
- `bug-perf-review`(`[호출 43]`): 유효 0, 보류 1이고, 밀 주장 일곱은 자리를 열어 대 보니 모두 맞아 오탐으로 냈다. 보류는 그 서브에이전트가 띄운 변이 표 재실행이 기준선 일곱 줄 뒤로 출력이 늘지 않아 끝을 보지 못한 것이다. 코드 읽기로는 변이 27과 대조군 1, `expect_output`을 단 변이의 묶음(넷, 열, 둘), 원문 28개가 훅 파일에 한 번씩 있는 것을 대 봤다고 했다. 그 실행은 TaskStop으로 멈췄고, 멈춘 뒤 `git status`에 변이된 파일이 남지 않았다고 했다.
- 둘째 사례의 README 밖 자리(명세)에서 어긴 문장은 "명령 없이 적은 문장"이 아니라 재지 않은 키 이름 같은 다른 문장이지만, 같은 근거 종류의 위반이라 사례 묶음으로는 맞다고 짚었다. 지적이 아니라 고치지 않았다.
- 보류의 처리: 이 세션이 저장소 루트에서 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/probe_conclusion_hook_mutations.toml`을 백그라운드로 다시 돌렸다. 변이 28 모두 기대대로였고(종료 0, `mutate.py`가 찍었다), 끝난 뒤 `git status`에 변이가 남지 않았다. 23번(표지 이름에서 에이전트를 뺀다)의 시험이 70.59초로 길었고 나머지는 2초 안이었다. 서브에이전트의 실행이 멈춘 듯 보인 까닭이 이 긴 시험인지는 보지 않았다(어림).
- PR 본문의 알림 길이: 서브에이전트가 "약 330자에서 약 800자"로 어림한 것을, 두 커밋의 훅 파일을 `git show`로 읽어 `_BODY.format(lead=LEAD)`의 길이를 세는 세션 스크래치패드 스크립트(`body_len.py`)로 손으로 셌다. `975bf04c` 307자, `ec920f03` 654자.

### origin/main 합치기

- 리뷰 동안 #359(harness 004)가 병합되어 origin/main이 `e205147d`로 움직였다. 함께 고친 파일은 `.scratch/harness/probes/README.md`, `.scratch/retro-queue.md`이고 다른 행이다. `git merge --no-edit origin/main`으로 충돌 없이 합쳤다(`fe8ac791`). 병합 커밋에는 커밋 메시지 검사만 돌았다.
- #359가 고친 파일을 이 브랜치가 드는 자리는, 첫 세션 절이 인용한 사용자 프롬프트의 티켓 004 경로 하나뿐이다. `git diff -G`로 그 파일 이름들을 찾아 손으로 봤다. 기록된 인용이라 고치지 않았다. #359가 더한 `bool | None` 주석 검사는 다음 커밋의 pre-commit(check-instructions)이 이 브랜치의 코드에도 돈다.
