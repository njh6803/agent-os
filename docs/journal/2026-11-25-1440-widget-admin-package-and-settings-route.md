# 2026-11-25 (14:40) widget-admin-server 티켓 01: 둘째 설치 묶음과 위젯 설정 읽는 경로

브랜치 `feature/01-widget-admin-package-and-settings-route`, 워크트리 `.claude/worktrees/01-widget-admin-package-and-settings-route`. 모델 Sonnet 5.5(지시문의 high). 기준은 `origin/dev` `3ba468f7a`다. 티켓은 `.scratch/widget-admin-server/issues/01-widget-admin-package-and-settings-route.md`이고, 넷 가운데 가장 크며 02·03·04가 이 티켓에 막혀 있다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 인자: .scratch/widget-admin-server/issues/01-widget-admin-package-and-settings-route.md
>
> 다음 작업: 위젯 관리 서버가 둘째 설치 묶음으로 서고, 표에 넣은 위젯 설정이 `/widget-settings/<사이트 이름>`에서 토큰 없이 읽힌다
> 이어받은 상태: 없음. 이 티켓이 넷 가운데 가장 크고 02·03·04가 이 티켓에 막혀 있다. 도중에 인계하면 티켓 본문의 묶음 단위로 끊고, 루트 `pyproject.toml`의 워크스페이스와 serve 이미지의 멤버 파일은 한 커밋에 넣는다
> 이번 요청 범위: PR과 병합까지

## 한 일

- 멤버 `widget-admin/`(패키지 `widget_admin`, 판 `0.0.0`, src 레이아웃)을 세우고 루트 `pyproject.toml`의 여섯 자리(작업공간 멤버와 원천, 개발 묶음, ruff `src`, pyright `include`와 `extraPaths`, import-linter의 `root_packages`와 독립 계약)를 고쳤다. `uv.lock`의 차이는 `widget-admin 0.0.0` 항목과 작업공간 멤버 표지뿐이다.
- 코드는 모듈로 나눴다. `settings`(사이트 이름의 꼴과 열아홉 칸의 모델), `database`(엔진, 마이그레이션, 읽기, 닫기), `errors`(봉투와 추적 식별자와 실패 한 줄, Agent OS 사본), `paths`(접두사 비교 사본), `server`(`create_app(*, database, stderr)` 하나와 응답 머리 미들웨어와 `/health`)다. 마이그레이션 `0001_sites`는 표 `sites`를 짓고 `downgrade`가 없다.
- 읽는 경로 `GET /widget-settings/{site}`는 꼴을 `re.fullmatch`로 이름 전체에 걸고 경로 인자의 `pattern`을 쓰지 않는다. 꼴이 틀린 이름과 등록되지 않은 이름은 글자까지 같은 404이고, 꼴이 틀린 이름은 데이터베이스에 묻지 않는다. 데이터베이스가 답하지 못하면 500 봉투다. 머리 셋은 `/widget-settings` 아래 모든 답(에러 포함)에만 붙는다.
- 계약 `widget-admin/openapi.json`은 `tools/export_widget_admin_openapi.py`로 뽑고, `schema_version`은 필수 `integer`다(`const`로 좁히지 않았다, 명세 검토 B2).
- 시험은 진짜 테스트 데이터베이스(접두 `widget_admin`)를 쓴다. `tests/widget_admin/`에 읽는 경로, 404와 실패, 머리, 표의 제약, 계약 최신성이 있고 저장소 상태 시험으로 `tests/test_widget_admin_workspace.py`(루트 `pyproject.toml`의 여섯 자리와 변이 열 사례), `tests/test_repo_version.py`(멤버의 판 셋), `tests/test_postgres_migration_shape.py`(위젯 쪽 폴더)를 더했다.
- `tools/release.py`의 `PRODUCT_PATHS`에 `widget-admin`을 더했다(`tests/tools/test_release.py`의 개수도 여섯으로 고쳤다). 노트 검사는 같은 목록을 가져다 쓰므로 고칠 것이 없었고, `PRODUCT_MIGRATIONS`는 04의 몫이라 그대로다. 그래서 이 PR 제목에는 느낌표가 없다.
- serve 이미지는 `deploy/images/serve.Dockerfile`과 그 `.dockerignore`에 멤버의 `pyproject.toml`만 들였다. 루트 `pyproject.toml`의 작업공간과 같은 커밋에 든다.
- 문서와 하네스는 `docs/constitution/tech.md`(패키지 관리 칸, 경계 칸, 위젯 관리 서버 문단), `CLAUDE.md`(레이어 목록), `README.md`(트리), `.claude/rules/http.md`(첫 항목에 범위가 `agent_os`라는 한 줄), `.claude/rules/widget-admin.md`(새 규칙)다. 헌법 판은 3.1.5에서 3.1.6으로 올렸다(`sibling_overlap`이 형제의 가장 높은 판을 3.1.5로 냈다).
- 전체 검사에서 시험 하나가 빨갰다. `tools/check_instructions.py`의 `OPTIONAL_BOOL_ROOTS`가 pyright의 `include`와 같아야 하는데 `widget-admin/src`가 빠져 있었다. 한 줄을 더해 초록이 됐고, 이 검사가 멤버의 코드도 보게 됐다. 첫 커밋 시도에서 pre-commit의 `mutation tables`가 `.scratch/harness/probes/instruction_check_mutations.toml`의 "훑는 범위에서 tests 를 뺀다"(35번) 원문이 사라졌다고 막았다. 원문과 바꿀 글을 새 줄(`widget-admin/src` 포함)에 맞춰 고쳤고, `uv run python tools/mutate.py --check <표>`는 변이 40개 모두 원문이 한 번씩 있다고 했으며, `uv run python tools/mutate.py <표> 35`는 기대대로 빨강이었다(손으로 봤다).

## 규칙 파일을 새 세션에서 불러 본 결과(카나리아)

새 규칙 `.claude/rules/widget-admin.md`와 고친 `http.md`는 실제 실행에서 실리는지 손으로 봤다. 명세마다 `uv run python tools/canary.py <명세 파일> <출력 폴더>`를 쳤고 각 명세의 `# 최신 결과:` 줄이 같은 결과를 적는다(claude 2.1.325, 이 PC, 커밋하기 전의 작업 트리).

| 명세 | 결과 |
|---|---|
| `.scratch/widget-admin-server/probes/canary/widget_admin_rule.toml`(새 규칙) | 통과 4, 실패 0, 대조군 "없음" |
| `.scratch/end-user-continuation/probes/canary/http_rule_continuation_422.toml` | 통과 4 |
| `.scratch/end-user-continuation/probes/canary/http_rule_pre_owner_damage.toml` | 통과 4 |
| `.scratch/web-widget/probes/canary/http_rule_llm_widget.toml` | 통과 4 |

셀프 리뷰가 `.claude/rules/tests.md`의 한 항목에 예외 한 줄을 더했으므로(`tests/widget_admin/`이 둘째 예외), 그 규칙을 원천으로 든 명세 다섯을 같은 방식으로 다시 돌렸다(`uv run python tools/canary.py <명세> <출력 폴더>`, claude 2.1.325, 이 PC, 커밋하기 전의 작업 트리). 다섯이 모두 통과 4, 실패 0, "없음" 섞인 통과 0이고 각 명세의 `# 최신 결과:` 줄을 고쳤다. 대상은 `tests_rule_linux_exec_bit`, `tests_rule_llm_tokens`, `tests_rule_pwsh_linux`, `tests_rule_timing_margin`(이상 `.scratch/harness/probes/canary/`)과 `tests_rule_llm_widget`(`.scratch/web-widget/probes/canary/`)이다. `--shape`도 다섯 모두 통과했다.

## 손으로 본 것

- `uv lock --check`는 0이다. `uv sync --frozen`도 0이다(셀프 리뷰 뒤에 다시 쳤고 "Audited 94 packages"가 나왔다). `uv sync --frozen` 뒤 `widget_admin`은 편집 가능한 꼴로 깔려 있다. 잠금의 차이는 `widget-admin 0.0.0` 항목과 작업공간 멤버 표지, 개발 묶음의 `widget-admin` 두 줄이다(`git diff`로 세었다).
- 경계. 멤버의 `widget_admin/paths.py`에 `import agent_os.sdk`를 잠깐 넣고 `uv run lint-imports`를 치니 1로 끝났고 `agent_os and widget_admin are independent (ADR 0064) BROKEN`과 `widget_admin.paths -> agent_os.sdk (l.10)`이 나왔다. 반대로 `agent_os/http/paths.py`에 `import widget_admin`을 넣으면 1로 끝났고 `agent_os.http.paths -> widget_admin (l.11)`이 나왔다. 둘 다 되돌렸고 `git status`에 `agent_os` 쪽 변경이 없다. 이 확인은 저장소 시험으로 두지 않았다.
- `uv run ruff check --show-files .`의 목록에 `widget-admin/src/widget_admin/server.py`, `widget-admin/src/widget_admin/migrations/versions/0001_sites.py`, `tests/widget_admin/test_read_widget_settings.py`가 든다.
- `uv run pytest -q tests/widget_admin -W default`는 87 통과이고 경고가 없다. 닫지 않은 엔진의 경고는 나지 않았다.
- 단독 배포 e2e(`pnpm -C web/packages/e2e-standalone exec playwright test`)는 15개가 모두 통과했다(2.2분). Docker가 켜져 있고 호스트의 80·443·3000이 비어 있었다. 방금 지어진 `agent-os-e2e/serve:0.1.0-rc.1` 안에서 `importlib.util.find_spec`으로 보니 `agent_os`는 있고 `widget_admin`은 없다. 이미지에는 멤버의 `pyproject.toml`만 들었기 때문이다.
- 전체 검사(`uv run python tools/run_checks.py`)는 check-ticket, check-notes, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, web-verify가 초록이었고, pytest는 8253 가운데 위의 한 시험만 빨갰다(고친 뒤 그 시험은 초록). pytest 한 바퀴는 756.74초였다.

## 아직 못 본 것

- CI `python` 잡의 시간과 pytest 단계의 시간(제한 25분, 앞의 성공 40회 최대 15.0분). 이 PR의 CI가 돈 뒤에 이 일지 끝에 적는다.
- 프로브가 재지 못한 넷 가운데 이 티켓이 보는 둘. CI 리눅스에서 `uv sync --frozen`과 검사 도구가 두 묶음으로 도는 것과 CI가 받은 uv의 판은 이 PR의 CI 기록에서 읽고, pre-commit 러너가 통째로 도는 것은 이 티켓의 커밋이 부르는 pre-commit의 결과로 본다.

## 셀프 리뷰(/code-review)

범위는 기준 SHA `3ba468f7a`, 변경된 추적 파일 19개, 미추적 22개, 커밋 0개다. 표준 축(sonnet, high)과 명세 축을 나란히 돌렸고 Critical·Major는 둘 다 0이다. 표준 축 Minor 3과 Nit 2, 명세 축 Minor 5와 Nit 몇이 나왔다.

고친 것(새로 쓴 사실 문장은 PR 직전 리뷰에 밀 주장이다).

- `database.py` 모듈 독스트링의 "alembic을 부르는 코드는 이 모듈뿐"은 `migrations/env.py`와 `0001_sites.py`가 반례였다. "엔진을 짓고 연결을 여는 코드는 `widget_admin` 안에서 이 모듈뿐이다"로 좁혔다.
- `ErrorCode`의 "상태 코드와 1:1"은 `_code_for(405)`가 `invalid_request`를 내서 거짓이었다. 이 문장은 계약 파일의 `description`에도 있었다. "표 안의 상태 코드와 1:1"로 좁히고 `widget-admin/openapi.json`을 다시 뽑았다.
- `tests/test_widget_admin_workspace.py`의 "여섯 자리"는 검사가 여덟 항목이라 어긋나 보였다. 여섯 자리가 무엇이고 그것을 여덟 항목으로 나누어 본다고 `workspace_problems` 독스트링에 적었다.
- `0001_sites.py`의 "열아홉 칸이 칸 열아홉이다"는 표가 `name`까지 스무 칸이라 모호했다. 고쳤다.
- `settings.py`의 "위젯 쪽 `WidgetSettings`와 같은 글자다"는 저장소에 그 모델이 없었다. 명세의 "답의 모양"이 정했다고 고쳤다. `WidgetSettings`의 독스트링은 명세의 예외(예시 질문은 빈 목록, 밝기 스위치 숨기기는 거짓)를 싣게 하고, 두 열거의 독스트링 낱말을 명세의 "로그인 전의 모양"과 "고지 전문"에 맞췄다.
- `server.py`의 두 까닭을 명세에 맞췄다. 꼴이 틀린 이름과 없는 이름의 답이 같은 까닭은 "위젯이 이름의 꼴을 따로 알 필요가 없다"이고(명세 사용자 이야기 6), 전역 앱을 두지 않는 까닭은 "시험이 시험마다 다른 데이터베이스를 쓰지 못하게 한다"이다. 낱말 중간에서 끊긴 주석 줄도 고쳤다.
- 쓰이지 않는 `WidgetAdminDatabase(url_text, *, versions=...)` 인자를 지웠다(명세에 없는 일반화).
- 시험을 더했다. 표에 늘어난 칸의 값이 답의 어디에도 없다는 것, 500 봉투에도 사이트 이름이 없다는 것이다(명세 시험 결정의 두 문장).
- `.claude/rules/tests.md`의 "`tests/` 미러링의 유일한 예외"는 `tests/widget_admin/`이 둘째 예외라 거짓이 되었다. 고쳤다.
- 이 일지의 `uv.lock` 문장과 `uv sync --frozen` 종료 코드를 바로잡았다.

남긴 것과 이유.

- Shotgun Surgery(열아홉 칸의 목록이 `COLUMNS`, 모델 필드, 읽기의 생성자, 마이그레이션에 흩어짐)는 판단 항목이다. 마이그레이션 쪽은 "올라간 파일은 고치지 않는다"의 사본이라 의도이고, 나머지 셋은 `test_contract.py`의 열쇠 단언과 읽기 시험이 어긋남을 잡는다.
- `pyproject.toml`의 `extraPaths` 주석과 `tech.md`, `env.py`의 "(ADR 0064)" 인용은 ADR이 정한 것이 아니라 명세와 프로브가 정한 것이라는 Nit. 인용이 가리키는 ADR이 설치 묶음 분할 자체를 정했으므로 그대로 둔다.
- `tools/hook_pyright_unchecked_path.py` 독스트링의 `include` 목록은 측정을 기록한 문장이라 그대로 둔다.
- 계약에 422가 실리는 것은 티켓이 적은 404·500 밖이지만, FastAPI가 제 모양을 붙이지 않게 하려는 것이고 `http.md`의 에러 문서 항목과 같다. 그대로 둔다.
- `tech.md`의 "런타임 의존성" 칸의 멤버 의존 문장과 `widget-admin.md`의 `paths`에 든 내보내기 도구는 범위가 조금 넓지만 같은 일의 한 자리라 그대로 둔다.

다시 돌린 것. `uv run pytest -q tests/widget_admin tests/test_widget_admin_workspace.py tests/test_repo_version.py tests/test_postgres_migration_shape.py tests/tools/test_release.py -W default`가 221 통과, `ruff check`와 `ruff format --check`(멤버와 시험 16개 파일) 초록, `uv run pyright` 0 오류, `uv run python tools/check_instructions.py` 0이다. 나머지 손으로 치는 명령은 커밋의 pre-commit 결과로 갈음한다.

## 회고

후보 일곱을 냈고 판정은 승인 0, 기각 7, 넘김 0이다. 대기열은 `uv run python tools/queue_open_rows.py`로 봤고 만료할 항목은 없었다. 같은 일을 다룬 항목은 `--search OPTIONAL_BOOL_ROOTS --search MSYS_NO_PATHCONV --search check_instructions.py`로 찾았고, 닫힌 항목 14개가 맞았지만 모두 다른 사건이다.

| 후보 | 판정 | 근거 |
|---|---|---|
| 새 설치 묶음의 소스 폴더를 `tools/check_instructions.py`의 `OPTIONAL_BOOL_ROOTS`에 빼먹어, 전체 검사의 시험 하나가 빨갰다 | 기각 | `tests/tools/test_check_instructions.py`의 범위 시험이 이미 잡았고 한 줄로 고쳤다. 막은 검사가 있어 4단계의 승인 조건 가운데 "층"에서 더할 것이 없다 |
| 합친 pytest 실행이 100%를 찍고도 끝나지 않아 프로세스를 끈 일 | 기각 | 원인을 가르지 못했다(일지에 적을 사건이 아니라 환경의 일회성). 사건 없이 떠올린 처방이다 |
| 워크트리 가드가 `cp … && git status …`를 거부해 명령을 나눠 다시 침 | 기각 | `CLAUDE.md` 환경 함정에 이미 있는 지침이고 앱의 가드가 그 자리에서 막았다 |
| `docker run --entrypoint /app/.venv/bin/python …`을 Git Bash가 윈도 경로로 바꿔 종료 127 | 기각 | `tools/hook_bash_msys_pathconv.py`의 독스트링이 `docker`를 못 보는 것으로 이미 적었다. 비용은 재시도 한 번이었고 손상은 없다. 더하는 것은 다섯 번째 반복이나 손상 한 번 전이라 반영하지 않는다(0195와 같은 계열, 모양은 다르다) |
| 첫 판의 시험이 `# type: ignore`를 썼다가 타입 우회 규칙에 따라 스스로 고침 | 기각 | 커밋 전에 스스로 고쳤고 `tools/check_type_escapes.py`가 어차피 막는다 |
| 일지에 "쟀다"를 적었다가 근거 알림이 와서 "손으로 봤다"와 명령으로 고침 | 기각 | `hook_probe_citing_doc`·근거 알림 훅이 그 자리에서 알렸다 |
| 겹침 검사가 헌법 판을 올리고 일지 인용을 만들라고 알림 | 기각 | `tools/sibling_overlap.py`가 그 몫을 했다 |

승인한 것이 없어 대기열에 더한 항목도 없다.

## 인계 (커밋 뒤)

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 커밋이 끝난 자리에서 넘긴다(`hook_handoff`의 `커밋 뒤`). 앞선 인계(`셀프 리뷰 직전`)로 연 두 번째 세션이 셀프 리뷰를 하고 커밋했다. 이 세션 제목은 `feature/01-widget-admin-package-and-settings-route`였고 `(인계함)`을 붙여 넘긴다. 이 세션이 받은 사용자 프롬프트는 위 "사용자 프롬프트"와 같은 지시문이고 범위는 "PR과 병합까지"다.

- 커밋은 `7f72b01f2`(feat: 위젯 관리 서버를 둘째 설치 묶음으로 세우고 위젯 설정 읽는 경로를 더한다 (widget-admin-server 01)) 하나이고 아직 푸시하지 않았다. 작업 트리는 깨끗하다. 첫 커밋 시도는 pre-commit의 `mutation tables`가 `.scratch/harness/probes/instruction_check_mutations.toml`의 원문을 막았고(위 "한 일"의 마지막 항목), 고친 뒤 두 번째 시도가 통과했다.
- 셀프 리뷰(위 `## 셀프 리뷰(/code-review)`)는 Critical·Major 0이고 Minor는 고쳤다. 회고(`## 회고`)는 앞선 세션에서 이미 돌았다.
- 남은 일은 순서대로 셋이다. (1) 푸시 전에 `origin/dev`를 이 브랜치에 병합한다. 지금 `origin/dev`는 `6b0646e`이고 이 브랜치의 기준은 `3ba468f7a`라 뒤처졌다(`uv run python tools/sibling_overlap.py`는 번호 겹침 없음, 헌법 판은 형제의 가장 높은 판 3.1.5보다 높은 3.1.6이다). 병합으로 파일 충돌이 나면 `.scratch/plan.md`는 `uv run python tools/plan_table.py`로 다시 만든다. (2) `/git-pr`로 PR을 연다. 제목에 느낌표를 붙이지 않는다(`PRODUCT_PATHS`에 `widget-admin`을 더했지만 올릴 때 운영자가 손댈 것은 없다). (3) 병합은 `.claude/skills/next-session/merge.md`를 Read로 열어 따른다("워크트리에서 병합할 때" 포함).
- PR의 CI가 돈 뒤 이 일지 끝에 CI `python` 잡의 시간과 pytest 단계의 시간, CI의 uv 판을 적고 티켓의 미체크 두 항목을 채운다(제한 25분, 앞의 성공 40회 최대 15.0분). 그 채우기는 PR에 커밋으로 싣는다.
- 셀프 리뷰가 새로 쓴 사실 문장(PR 직전 `bug-perf-review`가 겨낼 몫)은 위 `## 셀프 리뷰(/code-review)`의 "고친 것" 목록에 원문의 요지로 있다.
- 전체 검사(`uv run python tools/run_checks.py`)는 앞선 세션이 한 바퀴 돌았고(pytest 한 시험만 빨강이었고 고쳤다), 이 세션은 셀프 리뷰를 고친 뒤 위젯 관리 시험 221개, ruff 둘, pyright 0 오류, `check_instructions`만 다시 돌렸다. 나머지는 커밋의 pre-commit이 돌려 통과했다. 이 PR 안에서 카나리아 다섯(`tests_rule_*`)도 돌려 모두 통과 4였다.

## 다음

- 02(`02-widget-admin-client-package.md`), 03(`03-widget-admin-commands-and-startup-check.md`), 04(`04-standalone-compose-adds-widget-admin.md`)가 열렸다. 03이 `widget-admin serve`·`migrate` 명령과 연결 문자열 판정, 확인·다시 시도, 루프백 사본을 더하고, 04가 노트 검사의 `PRODUCT_MIGRATIONS`에 위젯 쪽 폴더를 더하고 레지스트리·CI 칸을 고친다.
- 03이 `create_app`에 더할 가장 바깥 미들웨어(데이터베이스 확인)의 자리는 `.claude/rules/widget-admin.md`와 명세 "응답 머리"의 끝 항목이 적은 대로다.

open-session을 부른다 2026-11-25T06:00Z
open-session을 부른다 2026-11-25T06:43Z
