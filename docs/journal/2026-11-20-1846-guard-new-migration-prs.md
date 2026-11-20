# 2026-11-20 (18:46) 새 마이그레이션 파일을 더한 PR은 느낌표와 번호의 꼴을 검사받는다

브랜치 `feature/04-guard-new-migration-prs`, 워크트리 `.claude/worktrees/04-guard-new-migration-prs`. 모델 Sonnet 5.5 / high로 시작했다. 티켓은 `.scratch/postgres-foundation/issues/04-guard-new-migration-prs.md`다. 이 파일은 컨텍스트가 인계 문턱(20만 토큰)을 넘은 `셀프 리뷰 직전`에 인계하며 만들었다. 커밋하지 않았고 `## 다음`도 쓰지 않았다. 새 세션이 이어 쓰고 커밋한다. 이 세션의 제목은 `feature/04-guard-new-migration-prs`였다.

## 사용자 프롬프트

> 사용자(붙여 넣은 지시문):
> 다음 작업: .scratch/postgres-foundation/issues/04-guard-new-migration-prs.md. 새 마이그레이션 파일을 더한 PR은 느낌표와 번호의 꼴을 검사받는다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 2 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/postgres-foundation/issues/04-guard-new-migration-prs.md
> 브랜치: feature/04-guard-new-migration-prs
> 모델: Sonnet 5.5 / high
> 읽을 것: 나란히 도는 .scratch/postgres-foundation/issues/03-serve-requires-database.md(04와 고치는 파일이 겹치지 않는다. 둘 가운데 늦게 병합하는 쪽이 기능의 끝 줄과 기능 단락을 적는다). 일지 docs/journal/2026-11-20-1407-standalone-compose-adds-postgres.md의 "## 셀프 리뷰"와 "## PR 611 뒤"
> 이어받을 상태: 02가 PR 611로 병합됐다. 이 티켓이 기다리던 제품 마이그레이션 0001(src/agent_os/adapters/postgres/migrations/versions/0001_first.py)과 단독 배포용 업그레이드 노트(docs/release-notes/upgrade/standalone-postgres.md)가 이제 dev에 있어, 저장소 상태 시험과 노트 검사의 짝을 실제 파일에 대 볼 수 있다. 02에서 이 티켓이 이어 볼 것은 없다.
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 이 세션이 한 것

`EnterWorktree`가 만든 브랜치 `worktree-04-guard-new-migration-prs`를 인계 직전에 `git branch -m`으로 지시문의 브랜치 `feature/04-guard-new-migration-prs`로 바꿨다(`git branch --show-current`로 봤다). 티켓 `Status:`는 `in-progress`로 바꿨다. 아래는 모두 커밋하지 않은 변경이다.

- `tools/check_notes.py`: `PRODUCT_MIGRATIONS = "src/agent_os/adapters/postgres/migrations/versions"` 상수를 더했다. `title_problems`가 느낌표 없는 제목에서 그 폴더에 새로 더한(`A`) 파일마다 문제를 낸다. 글은 `제목 접두에 느낌표가 없는데 제품 마이그레이션 <경로> 를 새로 더했다`로 시작한다. 느낌표가 있으면 그 분기는 지나가고 지금의 `upgrade/` 원고 판정이 뒤를 잇는다. 모듈 독스트링의 (가) 문단에 이 짝을 적었다. 시험용 폴더(`tests/` 아래), 제품 폴더 밖의 파일(`env.py` 등), 고치기만 한 파일은 대상이 아니고 이름 바꾸기는 지운 것과 더한 것 둘로 센다.
- `tests/tools/test_check_notes.py`: 짝의 사례를 더했다. 순수 함수 사례(`title_problems`)와 임시 저장소의 진짜 프로세스 사례(`--ci`, `--title-only`)다. 이 저장소가 지금 통과함을 재는 `test_이_저장소의_짝은_마이그레이션_파일이_든_폴더를_가리킨다`도 있다.
- `tests/test_postgres_migration_shape.py`(새 파일): 제품 폴더의 꼴을 보는 `shape_problems`(ast로 읽는다. 번호 차례, 앞 번호의 사슬, 마지막 번호 하나, `downgrade` 없음, 파일 이름 꼴, `revision` 값)와 `test_이_저장소의_마이그레이션_폴더는_꼴이_맞다`, 변이 시험들. 훑은 파일이 없으면 실패한다.
- `.scratch/postgres-foundation/probes/migration_guard_mutations.toml`(새 파일): 변이 12개. 첫 판의 표지가 시험 원문에 글자 그대로 있어 도구가 거부했고, `any(...)`로 단언한 시험은 실패 출력에 받은 값이 찍히지 않아 목록 전체 비교로 바꿨다. 지금 판은 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/postgres-foundation/probes/migration_guard_mutations.toml`로 12개 모두 "기대 빨강, 결과 빨강"이었고(`변이 12 모두 기대대로`) 소스는 원래대로 돌아왔다. `--check`도 "변이 12 모두 원문이 한 번씩 있다"였다. 이 표를 가리키는 프로브 README 줄은 아직 없다.

## 검사

- 변경한 세 파일의 `ruff check`·`ruff format --check`·`pyright`는 깨끗했다(저장소 전체 `ruff check .`는 `All checks passed!`, `ruff format --check .`는 `2498 files already formatted`, `pyright` 세 파일 `0 errors`).
- `tests/tools/test_check_notes.py`와 `tests/test_postgres_migration_shape.py`는 각각 초록이었다(첫 판에서 겹친 번호 시험이 파일 이름순이 아니라 읽은 순서로 나와 빨갰고, 이름순 정렬을 구현에 넣어 고쳤다).
- **티켓이 요구한 실제 실행.** 임시 저장소(main에 `src/app.py`와 제품 마이그레이션 `0001`, 가지에서 `0002_second.py`를 더함)에서 `tools/check_notes.py`를 CI처럼 환경 변수를 주어 진짜 프로세스로 불렀다. 스크립트는 `C:\Users\User\AppData\Local\Temp\claude\9060abe0b92613e9\204ae121-b0ac-4564-abb3-9881a7567dd6\scratchpad\real_run.py <워크트리 루트>`다. 회차마다 종료 코드와 표지(짝이 낸 글 `제품 마이그레이션 \`<경로>\` 를 새로 더했다`, 원고 판정이 낸 글 `에 새로 더한 파일이 없다`)를 단언했고 `측정 아님 0회차`였다.
  - `--ci` 제목 `feat: 표를 더한다` → 종료 1, 짝의 글.
  - `--title-only` 같은 제목 → 종료 1, 짝의 글. CI가 PR 제목을 보는 두 길(`.github/workflows/ci.yml`의 `python3 tools/check_notes.py --ci`와 `.github/workflows/pr-title.yml`의 `--title-only`)이 모두 `title_problems`를 부른다.
  - `--ci` 제목 `feat!: 표를 더한다`(원고 없음) → 종료 1, 짝의 글은 없고 원고 판정의 글(`upgrade/` 에 새로 더한 파일이 없다).
  - `docs/release-notes/upgrade/tables.md`를 더하고 `--ci`, `--title-only` 둘 다 `feat!:` → 종료 0, 출력 없음.

## 셀프 리뷰 (이어받은 세션)

이어받은 세션이 `/code-review`를 돌렸다. 고정점은 `origin/dev`의 `7b52bbd616029d1f7edecc1b8c30b89ad4f63e6b`, 변경 파일 수정 4개와 미추적 3개(일지 포함), 커밋 0개다. 표준 축은 sonnet·high, 명세 축은 세션 기본 모델이다. 둘 다 Critical·Major는 없었다.

- **고친 것.**
  - 약한 단언: `test_짝은_느낌표가_있으면_지나가고_원고_판정이_뒤를_잇는다`와 `test_CI는_느낌표가_있어도_원고가_없으면_막는다`가 `upgrade/` 낱말만 봐서 짝이 잘못 발동해도 통과했다(두 글이 모두 그 낱말을 말한다). 원고 판정의 글(`에 새로 더한 파일이 없다`)을 보고 짝의 글(`제품 마이그레이션`)은 없음을 단언하도록 고쳤다.
  - `downgrade` 탐지: `downgrade = upgrade`, `downgrade: object = None`, `from x import downgrade`, `import downgrade`를 놓쳤다. 시험을 먼저 더해 빨강을 본 뒤(`assert [] == [...]`) `_binds_downgrade`로 넓혔다. 이름에 `downgrade`가 들었을 뿐인 것(`downgrade_note`, `downgrade_helper`)은 잡지 않는 시험도 더했다.
  - 틀린 독스트링 문구: 꼴 시험의 모듈 독스트링이 코드에 없는 따옴표 문구 `"값을 못 읽었다"`를 적었다. 실제 문구(`글자 값이 아니다`, `글자 값으로 읽지 못했다`)로 바꿨다.
  - `check_notes.py` 독스트링에 짝이 세는 파일의 범위(하위 폴더와 확장자를 가리지 않고, `__init__.py`나 `README.md`도 센다)를 한 줄 적었다. 명세 축이 그 셋을 실제로 불러 확인했다.
  - 변이 표: 표지를 단언마다 갈리게 바꿨다(처음 판은 다섯 변이가 모두 `Right contains one more item`). 윈도 경로 구분자에 묶인 표지(`migrations\versionz`)를 `versionz`로 풀었다. `downgrade` 탐지를 넓힌 데 맞춰 변이 셋(12·13·14번)을 더해 열다섯이 됐다.
  - 낡은 문서: `.github/workflows/ci.yml`과 `pr-title.yml`의 머리 주석이 새 짝을 적지 않았다. 한 구절씩 더했다(거짓이 아니라 불완전한 문장이었다). `docs/constitution/operations.md`의 "보는 자리"도 같았는데 아래 남긴 것을 본다.
  - 첫 커밋 시도가 `check-constitution-version`에 막혔다. 위 `operations.md`를 고쳤더니 헌법 파일을 고치고 판을 올리지 않았다고 나왔다(`docs/constitution/README.md`의 판 줄). 헌법 파일의 개정은 ADR과 사용자 승인이 필요해서(`CLAUDE.md` 지도 표) 그 편집을 `git restore`로 되돌렸다. 나머지 검사는 그 시도에서 모두 통과했다(pytest 1152.3초, web-verify 1300.8초).
  - 프로브 README에 `migration_guard_mutations.toml` 줄을 더했다(티켓 01의 변이 표가 선례다).
- **남긴 것.**
  - `title_problems`의 `added`와 `migrations`가 같은 모양의 리스트 컴프리헨션이다(Duplicated Code, 표준 축의 판단 항목). 둘뿐이고 메시지가 달라 `_added_under`로 뽑을 만큼은 아니라고 봤다. 셋째가 생기면 뽑는다.
  - 폴더에 파일이 있는지 보는 시험 둘(`test_이_저장소의_짝은_…`, `test_이_저장소의_마이그레이션_폴더는_꼴이_맞다`)이 겹친다. 티켓이 둘을 따로 요구한다.
  - `shape_problems(sources)[1:]`처럼 문제의 차례에 기대는 단언이 있다(표준 축 Nit). 차례는 `shape_problems`가 번호 정렬로 정하고 시험이 그 차례를 고정하는 것이라 뒀다.
  - `docs/constitution/operations.md` 릴리스 노트 원고 절의 "보는 자리" 문단은 노트 검사의 (가)를 느낌표와 `upgrade/` 파일의 짝으로만 적는다. 새 짝(제품 마이그레이션 파일을 새로 더하고 느낌표가 없으면 막는다)이 빠졌다. 거짓이 아니라 불완전한 문장이고 노트 검사의 독스트링이 원천이다. 헌법 파일이라 고치려면 ADR과 사용자 승인과 판 올림이 따르므로 이 PR에서 고치지 않았다. 다음에 그 절을 고치는 PR(ADR 승인을 받는 헌법 개정)에 함께 싣는다. 받는 쪽은 아직 없다.
  - 계산해서 만든 이름(`globals()['downgrade'] = …`)은 `ast`로 보지 못한다. 독스트링의 못 보는 것에 적었다.
- **다시 돌린 것.** `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/postgres-foundation/probes/migration_guard_mutations.toml`: 변이 15 모두 기대대로(변이마다 `1 failed`), 기준선 셋 초록, 끝난 뒤 `git status`와 상수·구현 줄 grep으로 소스가 원상태임을 봤다. `--check`는 변이 15 모두 원문이 한 번씩이다. `uv run ruff check .`는 `All checks passed!`, `uv run ruff format --check .`는 `2499 files already formatted`. `uv run python tools/run_checks.py`는 check-ticket, check-notes, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest, web-verify 모두 Passed(pytest 1773.6초, web-verify 1860.0초. 다른 세션이 함께 돌던 때다).
- **기준선이 빨갰다는 보고.** 두 서브에이전트가 같은 워크트리에서 `mutate.py`를 따로 돌렸는데, 둘 다 기준선 시험이 한 번 빨갰다고 보고했다. 단독으로 다시 돌리면 초록이었다고 한다. 원본 출력은 받지 않았다. 원인은 다른 쪽 실행이 소스에 넣어 둔 변이로 보인다(추정이고 다시 재현하지는 않았다). 근거는 둘이다. 명세 축이 빨갛다고 적은 시험이 `env.py`·`database.py` 사례였고, 표준 축이 돌린 전체 실행에서 그 사례의 시험(`test_짝은_시험용_폴더와_제품_폴더_밖의_파일을_대상으로_삼지_않는다[…env.py]`)이 4번 변이(제품 폴더 밖 `src` 파일을 대상으로 세기)의 빨강으로 찍혔다(위 전체 실행의 로그를 손으로 대 본 것이다). 위 전체 실행의 기준선 셋과 러너의 pytest는 초록이었다.

## 회고

후보 둘을 냈다. 승인 둘(회차로 세는 것), 기각 하나, 넘김 0이다.

- **승인 1, 나란히 띄운 변이 도구 둘(대기열 `mutate-parallel-runs`의 5회차).** 사건은 위와 같다. 셀프 리뷰 서브에이전트 둘이 같은 워크트리에서 `tools/mutate.py`를 따로 돌려, 한쪽의 변이가 든 소스를 다른 쪽이 시험으로 돌았다. 그 항목이 처방한 둘째 시작 거부(`_running_marker`의 고정 경로 잠금)가 아직 구현되지 않았다. 이 PR은 티켓 04의 PR이라 `tools/mutate.py`를 고치지 않고, 항목의 승인 줄에 5회차를 더했다. 회차 5 이상이라 chore 배치 조건에 닿았다. 이 세션이 표준 축에 준 브리프가 전체 변이 실행을 오래 걸리면 하지 않아도 된다고만 적고 막지 않은 것도 이어진다(`code-review` 스킬의 문장이 아니라 이 세션이 쓴 브리프다). 브리프를 고치는 것은 도구의 잠금이 서면 필요 없어져 따로 올리지 않는다.
- **승인 2, 살아 있는 문서가 새 검사를 따라가지 못함(대기열 `0420`의 15회차).** 새 검사(마이그레이션 짝)를 더했는데 그 검사를 설명하는 `docs/constitution/operations.md`의 "보는 자리"와 `ci.yml`·`pr-title.yml`의 머리 주석이 짝을 적지 않았고, 셀프 리뷰 표준 축이 Minor로 잡았다. 옛 말이 틀린 것이 아니라 새 것을 빠뜨린 불완전한 문장이라 `0420`의 "옛 표현 잔존"과 꼴이 조금 다르다. 같은 지침(`CLAUDE.md` 작업 규약 4)이 겨눈 일이라 회차로 센다. 이미 14회차인 항목이라 처방은 그 항목에 있다.
- **기각 1, 약한 단언 둘.** `upgrade/` 낱말만 보는 단언은 `CODING_STANDARDS.md`의 "실패의 까닭까지 단언한다"를 어긴 것이고, 리뷰가 잡도록 둔 기준을 어겨 리뷰가 잡은 사건이라 리뷰가 제 몫을 한 것이다(4단계, 회차로 세지 않는다).
- **만료.** `uv run python tools/queue_open_rows.py`와 `--ref origin/dev`를 붙인 실행이 같은 항목 다섯(564, 566, 571, 572, 573. 승인 줄의 가장 늦은 날짜가 2026-11-04~05)을 만료할 항목으로 냈다. 상태 줄을 `만료 2026-11-20 (ADR 0036)`로 고쳤다. 날짜를 찾지 못한 항목은 없었다.
- **받아들인 종류의 새 사례(회차를 더하지 않는다).** 두 번째 커밋 시도의 pre-commit pytest(7995개)에서 `tests/tools/test_check_md_tables.py::test_한_줄에_겹친_목록_표식이_선형이다`가 `1.0049518999876454 < 1.0`으로 빨갰다(pre-commit 출력에서 읽었다). 이 변경이 건드리지 않은 시험이고, 혼자 돌리면 0.34초에 통과했다(`uv run pytest tests/tools/test_check_md_tables.py -q -k 겹친_목록_표식`). 대기열 `0306`이 부하에서 빨개지는 시간 시험은 그 커밋을 다시 치는 값을 받아들이기로 하고 닫았으므로, 사례를 고치지 않고 커밋을 다시 쳤다.
- **이 세션에서 반영한 것.** 없다. 두 승인 모두 회차만 더했고 `tools/mutate.py`의 잠금은 그 항목이 5회차에 닿아 chore가 다룬다.

## 다음

1. 커밋(티켓 `done`, `.scratch/plan.md`는 `plan_table.py`를 돌려도 바뀌지 않았다). 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`(이 세션에서 한 번 쳤고 번호 겹침과 함께 고친 파일 없음이었다)를 다시 친다.
2. PR 제목은 `src/`를 고치지 않아 느낌표가 없다. 접두는 `chore:`나 `test:`처럼 제품 변경이 아닌 것이다(티켓 이름 괄호는 `(04-guard-new-migration-prs)`). 이 PR은 마이그레이션 파일을 더하지 않아 이 티켓의 검사에 스스로 걸리지 않는다. 제품 경로(`tools/release.py`의 `PRODUCT_PATHS`)를 고치지 않아 기능 단락도 필요 없다.
3. 병합 직전에 `git fetch origin` 뒤 `origin/dev`를 합치고 `test_이_저장소의_…` 둘을 돌린다. 03(`03-serve-requires-database`)이 그때 `done`인지 `.scratch/postgres-foundation/issues/`의 `Status:`로 다시 본다. 지금(2026-11-20) 03은 `ready-for-agent`이고 03 세션이 돌고 있다. 03이 아직 열려 있으면 이 PR은 `끝:` 줄과 기능 단락 없이 병합하고, 03을 닫는 쪽이 `.scratch/postgres-foundation/plan.md`의 `**끝:** YYYY-MM-DD`와 `docs/release-notes/features/postgres-foundation.md`(운영자 말로 쓴 빈 줄 없는 400자 이하 한 단락)를 싣는다. 03이 이미 `done`이고 `끝:` 줄이 없으면 이 PR이 마지막이므로 둘 다 싣고 `plan_table.py`를 돌린다.
4. 병합은 이 워크트리 사본의 `next-session` `merge.md`(없으면 `SKILL.md`)의 "워크트리에서 병합할 때"를 따른다.
5. 스크래치패드의 `real_run.py`와 `edit_markers.py`는 저장소 밖이라 커밋하지 않는다.

## 인계

open-session을 부른다 2026-11-20T09:47:44Z

## 인계 (커밋 뒤)

이어받은 세션(제목 `feature/04-guard-new-migration-prs`)도 컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `커밋 뒤` 경계에 왔다. 한 일은 위 `## 셀프 리뷰 (이어받은 세션)`과 `## 회고`에 있다. 커밋은 세 번째 시도에 통과했다(첫 시도는 헌법 판 검사, 둘째는 부하에서 빨간 시간 시험). 이 인계 절을 쓴 편집은 커밋하지 않았다. 새 세션이 푸시 전에 커밋에 싣는다. 남은 일은 위 `## 다음`의 1~4(커밋은 끝났으니 2부터)와 푸시, PR 열기, PR 반영(봇 회차), 병합이다. 이 세션의 제목은 `feature/04-guard-new-migration-prs`였고 지금은 `feature/04-guard-new-migration-prs (인계함)`이다.

open-session을 부른다 2026-11-20T12:02:14Z

## PR 612 반영 (봇 회차 1)

이어받은 세션이 일지 편집을 커밋(첫 시도는 부하에서 빨간 `test_rerun_runner.py`의 시간 시험 때문에 실패했고 혼자 돌리면 통과해 다시 쳤다)하고 푸시해 PR 612를 열었다. 검사는 모두 초록이었고 claude-review는 지적 없음이었다. CodeRabbit의 첫 회차가 Minor 둘을 냈고 둘 다 고쳤다.

- `tests/test_postgres_migration_shape.py`의 `_literal`이 같은 이름의 첫 최상위 대입에서 바로 돌려줘, 파일 끝에서 `revision`·`down_revision`을 다시 대입해도 지나갔다. 같은 이름의 최상위 대입이 둘 이상이면 읽지 못한 것으로 세게 고치고, 시험 `test_revision과_down_revision을_뒤에서_다시_대입하면_잡는다`를 더했다.
- 변이 표 12·13번의 표지가 시험 ID 조각(`[downgrade = upgrade`)이라 단언 전에 예외로 끝나도 맞을 수 있었다. 목록 비교 단언이 내는 `Right contains one more item: '0002_second.py: \`downgrade\``로 바꿨다. 16번(`len(values) != 1`을 `not values`로 바꿔 첫 대입만 읽게 한다)을 더했다.
- 다시 돌린 것: `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/postgres-foundation/probes/migration_guard_mutations.toml`는 변이 16 모두 기대대로(변이마다 `1 failed`)였고 `--check`는 16 모두 원문이 한 번씩이었다. 두 시험 파일은 점만 찍고 통과했다(142개). 두 번 다 pytest 프로세스가 끝난 뒤에도 종료하지 않아 멈췄다(원인은 보지 않았다). 프로브 README의 개수와 줄을 열여섯으로 고쳤다.
- 보류한 것: 없다. 뒤로 넘기는 일도 없다.
