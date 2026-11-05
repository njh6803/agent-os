# 2026-11-05 (04) harness 041: `mutate.py --check`가 표지 없는 빨강과 단언 풀이 줄 표지를 알린다 (구현 세션)

세션 제목은 `chore/041-mutate-check-marker-quality`이다. 티켓은 `.scratch/harness/issues/041-mutate-check-marker-quality.md`이다.

## 사용자 프롬프트

> 사용자: 대기열 350·517을 티켓 .scratch/harness/issues/041-mutate-check-marker-quality.md로 쓰고 한다
> (다음 작업 지시문의 요지: `tools/mutate.py --check`가 빨강을 기대한 변이에 `expect_output`이 없거나, 표지가 pytest의 단언 풀이 줄이면 알린다. 이번 요청 범위는 PR과 병합까지다.)

## 한 것

- 시작: 제목을 브랜치 이름으로 바꾸고 `tidy-checkouts`를 돌았다. 루트를 `5b255a18`에서 `ea1453cd`(`origin/main`)로 당겼다. 병합된 워크트리 셋(`02-read-skill-document-into-sdk-value`, `03-runtime-prepares-skills-per-run`, `05-calc-uses-answer-format-skill`)과 브랜치를 지웠다. `05-default-model-required-and-checked`는 `agent-os.exe`(pid 7960)·`python.exe`(pid 26204, 38052)가 쥐고 있어 남겼다. 나머지는 바뀐 파일이 있거나, 병합된 PR이 없거나, 실행 중 세션이 쥐거나, 앱의 표지가 있어 남겼다. `EnterWorktree`로 들어간 뒤 브랜치를 `chore/041-mutate-check-marker-quality`로 바꿨다.
- 티켓 041을 썼다(`Status: in-progress`).
- 결정: 새 확인 둘(빨강을 기대했는데 `expect_output`이 없다 = 대기열 350, pytest 판정 러너의 표지가 단언 풀이 줄 `where … = …(`·`assert … == …` = 517)은 고른 `--check`(번호·이름·`--since`)와 `--staged`의 새 변이에만 걸고 변이를 돌리는 실행(`_validate`)에는 걸지 않는다. 까닭은 옛 표를 소급하지 않기 위해서다. `.scratch/**/*_mutations.toml`을 `tomllib`로 읽어 이 세션에서 손으로 세니 변이 3613 가운데 빨강 3571, 그중 표지 없는 것 1883, 단언 풀이 줄 표지를 든 빨강 176이었다. 돌리는 실행에 걸면 옛 표를 다시 돌릴 때마다 멈춘다.
- 시험을 먼저 썼다(원칙 II). `tests/tools/test_mutate.py` 끝에 새 시험 함수 열하나(매개변수까지 열아홉 사례, 코드를 읽고 센 수다. `_표지_표`·`_표지_없음`·`_단언_풀이` 도우미 포함)를 더하고 구현 전에 빨강을 봤다(`test_고른_원문_확인은_빨강을_기대했는데_표지가_없는_변이를_알린다`가 `assert 0 == 2`로 실패, pytest 출력). 구현 뒤 새 시험은 모두 초록이었고, 기존 시험 다섯(표지 없는 빨강을 새로 알리게 돼 걸린 것)은 그 시험이 원문만 보려던 것이라 초록 기대(`expect="green"`)로 고쳤다. `_시험이_든_저장소`는 `expect` 키워드를 받게 하고 표지를 두지 않는 시험 하나만 초록으로 불렀다. 기준: 시험의 뜻을 바꾸지 않고 새 알림에 걸리지 않게 하는 것.
- 구현: `tools/mutate.py`에 `_ASSERT_REWRITE`(줄 머리 정규식), `_ASSERT_REWRITE_NOTE`, `_quality_problems(spec)`을 더했다. `check_picked`와 `staged`의 새 변이(`fresh`)에 이어 붙였고 `_picked_problems`는 건드리지 않아 `_validate`(돌리는 실행)에는 걸리지 않는다. 모듈 독스트링에 "표지의 품질" 절(못 보는 것 포함)을 더했고 `.claude/rules/probes.md` 첫 항목에 한 문장을 더했다.
- 변이 표 `.scratch/harness/probes/mutate_marker_quality_mutations.toml`(열 개)을 짓고 `--check`로 원문을 본 뒤 돌렸다. 처음 돌린 판에서 2번("초록을 기대한 변이도 표지를 요구한다")만 초록으로 살아남았다. `-k`의 낱말 `표지_없어도`가 시험 이름 `표지가_없어도`와 어긋나 그 시험이 골라지지 않아서였다(도구가 찍은 기준선 `11 passed`). 낱말만 고쳐 2번을 다시 돌려 빨강을 봤다. 열 모두 기대대로다(도구가 찍은 줄). 프로브 README 표에 한 줄을 더했다.
- 대기열 350·517 행을 취소선과 `닫힘 (티켓 경로, 2026-11-05, …)`으로 닫았다.
- 검증: `uv run ruff check .`·`uv run ruff format --check .` 초록, `uv run python tools/run_checks.py` 초록(도구가 찍은 줄: pytest 436.9초, web-verify 666.5초, pyright 41.9초 등 모두 Passed). 이 실행은 셀프 리뷰 전이다.
- 인계: 컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전` 경계에 와서 넘긴다. 커밋하지 않은 변경이 이 워크트리에 있다. 세션 제목은 인계 직전에 `chore/041-mutate-check-marker-quality`였고 `chore/041-mutate-check-marker-quality (인계함)`으로 바꿨다. 워크트리 잠금은 풀었다(`git worktree unlock`).
- open-session을 부른다 2026-11-05T04:24:48Z

## 셀프 리뷰 (이어받은 세션)

범위: base `ea1453cd`, 수정 파일 5개, 미추적 3개, 커밋 0개. 표준 축은 sonnet·high, 명세 축은 본 세션 모델로 돌았다. 두 서브에이전트는 구현 자체(걸리는 자리, `_validate`에 안 걸림, 수 3613·3571·1883·176, 종료 코드 2)를 정규식과 함수를 직접 불러 맞다고 보고했다. 그 보고는 서브에이전트의 말이고 이 세션이 다시 부르지는 않았다. 아래 지적은 이 세션이 코드를 읽어 판정했다.

- 고친 것
  - 못 본다고 적었는데 시험이 없던 입력 둘(명세 축 a2, 표준 축 판단 1): 판정이 exit인 러너의 명령이 pytest여도 보지 않는다, 처리하지 않은 에러를 기대한 변이는 알리지 않는다. 시험 둘을 더했다.
  - 정규식이 `==`만 보고 `assert … ==`로 시작하는 메시지 문구도 알린다는 것(명세 축 c1, 표준 축 판단 2)을 모듈 독스트링의 못 보는 것에 적고 시험으로 고정했다. 거짓 음성(`!=`, `in`, `is`)은 사례 셋, 거짓 양성(메시지 문구)은 사례 하나.
  - 독스트링의 vitest는 이 모양의 줄을 찍지 않는다는 문장은 재지 않은 주장이라 뺐다. 시험이 고정하는 것은 vitest 판정의 표지를 보지 않는다는 동작뿐이다.
  - 모듈 독스트링 `--staged` 문단에 품질 확인을 적었다(명세 축 a3, 표준 축 판단 4).
  - `_ASSERT_REWRITE_NOTE`를 `_quality_problems`보다 앞으로 옮겼다(표준 축 판단 5).
- 남긴 것
  - 변이 표 1·3·6·7·8번이 같은 표지 `AssertionError: 원문 확인: 변이 1 모두 원문이 한 번씩 있다`를 쓴다는 지적(표준 축 판단 3): 이 문구는 `assert code == 2, 출력`이 빨개질 때 그 메시지에 실린 출력이다. 곧 알려야 할 자리에서 도구가 모두 맞다고 찍었다는 뜻이고 호출 기록이나 코드 조각이 아니다. 같은 `-k` 안의 어느 규칙을 뺐는지는 가르지 못하지만, 규칙마다 뺀 변이가 따로 있고 열 모두 빨강을 봤다. 규칙별로 더 가르려면 시험을 쪼개야 해서 이 티켓의 몫이 아니다.
  - `_runners(spec)`를 `_picked_problems`와 따로 만드는 중복(표준 축 판단 6): 낮은 우선순위의 판단 항목이라 두었다.
  - 티켓 본문의 "변이 3613"은 이 표를 더하기 전의 수다(더한 뒤는 3623). 티켓에 "이 세션에서 손으로 셌다"고 적혀 있어 시점이 읽히므로 고치지 않는다.
  - 닫힘 문장의 경로를 백틱으로 감싸지 않은 불일치(표준 축 기타): 사소해서 두었다.
- 다시 돌린 것: `uv run ruff check`·`ruff format`(두 파일) 초록, 새 시험을 포함한 `tests/tools/test_mutate.py -k`(표지·단언·색인 확인 등) 114 passed. 전체 게이트는 커밋이 부르는 pre-commit으로 갈음한다. 결과는 커밋 뒤에 적는다.
- 카나리아: `.claude/rules/probes.md` 첫 항목에 문장을 더했으므로 `tools/sibling_overlap.py`가 그 파일을 원천으로 든 명세 여덟을 알렸다. 같은 PR 안의 통과가 없어 갈음 조건에 맞지 않아서 `probes_rule.toml`(첫 항목이 든 규칙 파일이 실리는지를 재는 명세)을 실제로 돌렸다. 도구가 찍은 줄: 통과 4, 실패 0, "없음" 섞인 통과 0, 두 갈래 커밋 `ea1453cd`(커밋하지 않은 판), 돌린 뒤 `claude --version`은 2.1.318. 나머지 일곱은 `--preflight`로 갈음했고(여덟 모두 통과, claude는 돌리지 않았다) 더한 문장이 그 명세들이 묻는 자리 밖이라는 근거는 문장의 위치를 읽은 판단이다. 여덟 명세의 머리 주석에 이 결과와 갈음을 덧붙였고 `--shape`는 여덟 모두 통과했다.
- 커밋: `9680699e`(브랜치 `chore/041-mutate-check-marker-quality`, 16개 파일). 커밋이 부른 pre-commit이 모두 Passed였다(도구가 찍은 줄: parallel-checks 498.91초, 그 안의 pytest 375.4초, web-verify 498.7초, pyright 39.7초, check-instructions·check-type-escapes·lint-imports·run-hooks·zizmor·check-ticket, mutation tables, canary specs, commit message. constitution version은 해당 파일이 없어 Skipped). 이 커밋 직전 `uv run ruff check`·`ruff format`도 두 파일에서 초록이었다.
- 인계: 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤` 경계에 와서 넘긴다. 푸시와 PR은 아직 없다. 세션 제목은 인계 직전에 `chore/041-mutate-check-marker-quality`였고 `chore/041-mutate-check-marker-quality (인계함)`으로 바꿨다. 워크트리 잠금은 풀었다(`git worktree unlock`).
- open-session을 부른다 2026-11-05T04:44:40Z
- PR 직전 리뷰에 밀 주장: 모듈 독스트링 "못 보는 것"의 `!=`·`in`·`is` 거짓 음성과 `assert … ==`로 시작하는 메시지 거짓 양성.

## PR 직전 리뷰 (이어받은 세션)

- 시작: 새 세션이 제목을 바꾸고 이 워크트리에 들어왔다. `git fetch origin main` 뒤 `origin/main`은 여전히 `ea1453cd`이고 `tools/sibling_overlap.py`는 번호 겹침 없음이었다(일지 `2026-11-05-04`를 앞서는 형제는 042 워크트리의 `2026-11-05-05`, 그쪽이 먼저 병합되면 옮긴다).
- `coderabbit auth status`: `Plan: Free`, `Seat: not assigned`. 그래도 `coderabbit-review` 서브에이전트가 `coderabbit review --agent --include-untracked`를 실제로 돌렸고 CLI 0.7.5가 `review_completed`, 지적 0건으로 끝났다(서브에이전트가 찍은 줄이고 이 세션이 다시 돌리지는 않았다). 검토한 파일 16개는 커밋 `9680699e`의 파일 16개와 같다. 한도나 인증 오류는 없었다. CLI 축은 돌았으므로 대체 둘(`/security-review`, `bug-perf-review`)은 돌리지 않았다.
- PR #467을 헤드 `8f50a563`로 열었다. `tools/wait_ci.py`가 찍은 줄: 검사 모두 SUCCESS(claude-review 포함), CodeRabbit NEUTRAL. CodeRabbit의 PR 리뷰는 코멘트를 읽어 보니 "Review limit reached"(무료 OSS 한도)로 리뷰가 없었다. `@coderabbitai review` 요청도 "Review rate limited"로 답했다. 그 몫은 위 PR 직전 CLI 리뷰(지적 0건)가 맡았다.
- claude-review 첫 회차(코멘트를 읽었다): Minor 1, Nit 2. 판정은 이 세션이 `tools/mutate.py`를 `Grep`으로 읽어 했다.
  - Minor, 독스트링에서 "받는다"가 두 뜻(163번 줄은 알린다, 166번 줄 이하와 135번 줄 등은 지나간다)이라는 지적: 맞다. 한계를 서술하는 절이라 거꾸로 읽히면 한계가 뒤집힌다. 163번 줄만 "앞에 있어도 같은 줄로 보고 알린다"로 고쳤다. `ruff check` 초록.
  - Nit, `_quality_problems`가 `_runners(spec)`를 다시 만드는 중복: 셀프 리뷰에서 낮은 우선순위로 둔 것과 같다. 두었다.
  - Nit, `--staged` 절을 통째로 다시 줄바꿈해 diff가 커졌다는 지적: 이미 커밋된 줄바꿈이라 되돌리면 또 한 바퀴 돈다. 두었다.
- 앞의 CLI 리뷰는 지적이 0건이라 트리아지할 것이 없었다. 밀 주장 둘(독스트링 서술과 시험이 고정한 동작의 일치)은 CLI 쪽에서 나온 것이 없어 이 리뷰로 검증되지 않았다. 셀프 리뷰 때 시험으로 고정한 것이 근거의 전부다.
- 병합 충돌: 반영 커밋을 푸시한 뒤 `tools/wait_ci.py`가 `끝: 충돌`을 찍었다. 그 사이 `origin/main`에 042(`b98b8dd5`, PR #466)가 병합되어 있었다. 앱의 `sync_with_base_branch`는 "앱이 만든 워크트리가 아니다"라며 거절했고(도구 오류 문구를 읽었다), 직접 `git merge origin/main`을 쳐 `.scratch/retro-queue.md` 한 파일에서 충돌했다. 516은 main 쪽 줄(042가 닫음)을, 350·517은 이 브랜치 쪽 줄(041이 닫음)을 살렸다. 병합 커밋 `35207446`의 pre-commit이 모두 통과했고, `wait_ci`는 이 헤드에서 `끝: 모두 통과`(CodeRabbit SKIPPED)였다. `gh pr view`의 `headRefOid`와 로컬 `git rev-parse HEAD`가 같았다(손으로 봤다).
- 봇 둘째·셋째 회차(claude-review 코멘트를 읽었다). 둘째(헤드 `0c0c4a9a`)는 Minor 둘(`_runners` 중복, `where ` 줄 머리 정규식의 거짓 양성이 독스트링 "못 보는 것"에 없음)과 Nit 하나, 셋째(헤드 `35207446`)는 Minor 하나(`_runners` 중복)와 Nit 하나였다. Critical·Major는 없었다. 규칙대로 둘째 회차부터는 고치지 않고 PR 코멘트에 보류 이유를 남기고 병합한다. 그 가운데 `where ` 거짓 양성의 독스트링 한 문장과 시험은 뒤로 넘기는 일이라 아래 "다음"에 적었다.

## 회고

후보 다섯: 승인 0, 기각 넷, 일지에만 하나. 넘긴 것은 없다.

- 기각: claude-review 첫 회차 Minor("받는다"가 알림과 통과의 두 뜻). `CODING_STANDARDS.md`가 리뷰에 맡긴 기준을 리뷰가 잡은 것이라 회차 셈에서 빠지고, 낱말의 뜻을 가르는 검사는 만들 수 없다.
- 기각: claude-review 둘째 회차 Minor(`where ` 거짓 양성이 독스트링에 없음). 위와 같은 까닭이다. 이미 `.claude/rules/tools.md`에 "못 본다고 적은 주장도 잰다"는 항목이 있어, 이 사건은 그 지침을 어긴 사건이지만 리뷰가 제 몫을 했다.
- 기각: 앱의 `sync_with_base_branch`가 앱이 만든 워크트리가 아니라며 거절한 것. 앱 가드가 그 자리에서 알렸고 직접 병합하는 길이 `merge.md`에 있다. 한 번의 호출 낭비였다.
- 기각: `.scratch/retro-queue.md` 병합 충돌. 시작 때 `tools/sibling_overlap.py`가 "함께 고친 파일: 042 워크트리의 `.scratch/retro-queue.md`"로 이미 알렸다. 이미 알린 검사가 있다.
- 일지에만: `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`였는데 `coderabbit review --agent --include-untracked`(CLI 0.7.5)가 `review_completed`, 지적 0건으로 끝났다(서브에이전트가 찍은 줄). 2026-09-23의 `Seat: not assigned`가 즉시 끝나던 것(`operations.md` 리뷰 파이프라인 2)과 다르다. 대기열 570(사람 몫, 열림)의 새 자료이지만 그 행은 회차를 세지 않고 사람이 정한다. 같은 날 PR 쪽 CodeRabbit은 "Review limit reached"(무료 OSS 한도, 다음 리뷰까지 56분)로 리뷰하지 못했다(PR 코멘트를 읽었다).
- 만료: `uv run python tools/queue_open_rows.py`와 `--ref origin/main`의 두 출력에 모두 든 247·393·399·401·402·405·409·410을 `만료 2026-11-05`로 닫았다. 닫은 뒤 다시 센 출력의 "만료할 행"은 없음이었다.

## 다음

- PR #467 병합 뒤: 워크트리에서 병합했으므로 주 체크아웃은 새 세션이 `tidy-checkouts`로 당긴다(`merge.md` "워크트리에서 병합할 때" 4).
- 뒤로 넘긴 일(PR #467 둘째 회차 Minor): `tools/mutate.py` 모듈 독스트링 "못 보는 것"에 `where `로 시작하는 메시지 문구의 거짓 양성(`_ASSERT_REWRITE`의 `where\s.+=.+\(` 갈래)을 한 문장 더하고 시험으로 고정한다. 티켓 041은 `done`이라 다시 열지 않고, 하려면 다음 번호의 새 harness 티켓이다. 대기열 행은 따로 쓰지 않았다.
- 대기열 570: 이번 PR 직전 리뷰에서 `Seat: not assigned`인데 CLI가 돌았다는 자료가 생겼다. 사람이 그 행을 정할 때 본다.
- 그 밖의 다음 작업은 `.scratch/plan.md`의 프론티어다.
