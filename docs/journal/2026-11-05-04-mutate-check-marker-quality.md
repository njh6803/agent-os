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
- 지적이 0건이라 트리아지할 것이 없다. 밀 주장 둘(독스트링 서술과 시험이 고정한 동작의 일치)은 CLI 쪽에서 나온 것이 없어 이 리뷰로 검증되지 않았다. 셀프 리뷰 때 시험으로 고정한 것이 근거의 전부다.
