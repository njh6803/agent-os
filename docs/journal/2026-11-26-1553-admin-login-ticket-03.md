# 2026-11-26 admin-login 티켓 03: 로그인·로그아웃·지금 누구인지·첫 계정 확인을 공유 토큰 옆에 더한다

브랜치 `feature/03-login-logout-me-and-setup-beside-shared-tokens`, 티켓 `.scratch/admin-login/issues/03-login-logout-me-and-setup-beside-shared-tokens.md`. 이 세션의 제목은 인계 전 `feature/03-login-logout-me-and-setup-beside-shared-tokens`였다. 이 일지는 인계 세션이 쓴 것이고 새 세션이 이어 쓴다(커밋은 새 세션이 한다).

## 사용자 프롬프트

붙여 넣은 `next-session` 지시문 하나뿐이다(원문은 길어 요지만 옮긴다).

> 사용자: 저장소는 `C:\project\agent`다. `.claude/skills/implement/SKILL.md`를 읽어 그대로 따르고 인자는 `.scratch/admin-login/issues/03-login-logout-me-and-setup-beside-shared-tokens.md`다. 다음 단계는 구현이고, 어디서는 새 세션, 모델은 Sonnet 5.5 / high다. 읽을 것은 일지 `2026-11-26-0131-admin-login-ticket-02.md`의 "다음"이다. 주 체크아웃이 미갱신이라 `tidy-checkouts`를 먼저 돌고 `EnterWorktree`로 들어가 브랜치를 바꾼다. 병합은 워크트리 `merge.md`를 따른다. 이번 요청 범위는 PR과 병합까지다.

사용자의 정정이나 피드백은 없었다.

## 한 것(커밋 전, 작업 트리에만 있다)

- 새 파일: `src/agent_os/admin/auth.py`(경로 넷과 모델), `src/agent_os/http/login_tokens.py`(순수 규칙), `src/agent_os/http/logins.py`(`SigningKeys`, `LoginService`), `tests/fake_accounts.py`, `tests/test_login_http.py`(51건), `tests/test_login_tokens.py`.
- 고친 파일: `http/auth.py`(`PUBLIC_PATHS` 셋, `LOGIN_ONLY_PATHS`, 공유 토큰과 쿠키를 함께 받는 기간), `http/accounts.py`·`adapters/postgres/accounts.py`·`account_tables.py`(포트 메서드 아홉과 표 둘), `http/passwords.py`, `server.py`, `main.py`(`serve`가 유지 시간을 읽어 틀리면 종료 코드 2), 계약 `openapi.json`과 `web/packages/api-client/src/generated/openapi.ts`, `tools/export_openapi.py`.
- 시험과 문서: `tests/test_server.py`(공개 경로 셋, 출처 사례 표 `ORIGIN_CASES`를 로그인도 씀), `tests/channel/http/test_router.py`, `tests/test_main.py`, `tests/adapters/test_postgres_accounts.py`, `tests/test_account_rules.py`, `tests/fake_database.py`, 배포 안내 `deploy/standalone/README.md` 13절 표(유지 시간 문구 둘)와 `tests/tools/test_deploy_guide.py`(`STOP_TEXT_LABELS` 넷 더함), `.claude/rules/http.md`(자격 표의 함께 받는 기간, `PUBLIC_PATHS` 셋, 테스트 항목의 진짜 데이터베이스).
- 전체 러너(`tools/run_checks.py`)가 빨갛게 나와 고친 것 둘: `tests/test_system_admin_command.py`의 `_RacingWork`에 포트가 새로 가진 메서드 아홉을 더하고 `record` 시그니처를 포트와 맞췄다(pyright). `web/packages/api-client/src/clients.test-d.ts`의 관리 경로 목록에 `/auth/login`·`/auth/logout`·`/auth/me`·`/auth/setup`을 더했다(web-verify).

## 판단과 결정

- 로그인 라우트(`/auth/login`)의 401에는 `WWW-Authenticate: Bearer`를 싣지 않는다. 그 라우트는 `Authorization` 머리를 읽지 않고, 미들웨어가 내는 401만 그 머리를 싣는다(티켓 "401의 `WWW-Authenticate: Bearer`는 이 기간에 지금 그대로"는 지금 있던 미들웨어의 401을 가리킨다고 읽었다). 명세 "401의 머리"의 이유("더는 `Authorization` 머리를 받지 않기 때문")가 로그인 라우트에는 처음부터 해당한다. 13이 머리를 걷을 때 로그인 라우트는 손댈 일이 없다. 틀렸다고 판단되면 라우트의 401에 `_CHALLENGE`를 싣는 한 줄과 시험 한 줄(`tests/test_login_http.py`의 `test_…네_갈래…`)을 고친다.
- 동시 틀림 시험은 횟수의 값을 단언하지 않는다(티켓 "횟수 자체는 단언하지 않는다"). 다섯 동시 뒤 맞는 로그인이 401, 넷 동시 뒤 204다.
- 유지 시간 문구의 배포 안내 행은 값 자리를 `<값>`·`<분>`으로 두고 시험이 제품 함수의 글에서 같은 자리 표시로 갈아 맞댄다.

## 검증 현황(이 세션이 본 것)

아래 통과와 실패는 모두 이 세션이 그 명령을 직접 쳐서 출력(pytest의 요약 줄, `pyright`의 `0 errors`, `pnpm -C web verify`의 종료 코드 0)으로 본 것이다. 러너의 한 바퀴는 `uv run python tools/run_checks.py`의 로그(`pytest` 8680 passed, 1 failed)로 봤고, 실패 시험을 혼자 돌린 통과는 `uv run pytest tests/tools/test_hook_push_behind_main.py -k dev의_유무를_조회하다`의 출력(`1 passed`)이다. "병렬 부하가 겹친 일시 실패"라는 까닭은 어림이다. 같은 시험을 병렬로 다시 돌려 재현하지 않았다.

- 통과: `tests/test_login_http.py` 51건, `tests/test_main.py` 309건, `tests/tools/test_deploy_guide.py` 34건, `uv run ruff check .`, `uv run ruff format --check .`, `uv run lint-imports`, `uv run pyright`(전체, 0 errors), `pnpm -C web verify`(종료 0).
- 러너(`run_checks.py`) 한 바퀴의 pytest는 8680건 통과, 1건 실패였다. 실패는 `tests/tools/test_hook_push_behind_main.py::test_dev의_유무를_조회하다_시간을_넘기면_재지_않는다`다. 이 변경이 건드리지 않은 훅의 시간 의존 시험(`GIT_TIMEOUT=0.0001`)이고 혼자 돌리면 통과했다. 병렬 부하가 겹친 일시 실패로 보고 두었다. 러너를 다시 치면 이 시험이 또 빨개질 수 있다.
- 아직 안 돌린 것: 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`. 이 세션이 백그라운드로 띄웠으나 인계로 멈췄다), `uv run --env-file ../../../.env pytest -m llm`, 로컬 모델 시험(`--yes` 없이 먼저 쳐 비용을 사용자에게 보인 뒤), 셀프 리뷰(`/code-review`), `tools/mutate.py`(한 번도 빨갛게 본 적 없는 시험), retro, 티켓 `Status`를 `done`으로, `uv run python tools/plan_table.py`, `uv run python tools/sibling_overlap.py`, 커밋, PR.

## 인계

경계 `셀프 리뷰 직전`(컨텍스트가 문턱을 넘음). 제목을 `<브랜치> (인계함)`으로 바꿨고, 백그라운드 e2e를 멈췄고, 워크트리 잠금을 풀었다.

open-session을 부른다 2026-11-26T06:54Z

## 이어받을 일

`code-review`를 `origin/dev` 기준 작업 트리 변경 전체(미추적 파일 포함)에 돌려 Critical·Major를 고치고, 위 "아직 안 돌린 것"을 마친 뒤 일지를 마무리해 커밋하고 PR을 열어 병합까지 간다.

## 셀프 리뷰(이어받은 세션, 기준 SHA d211b37c4, 파일 23 변경과 미추적 7, 커밋 0)

표준 축은 Critical·Major 없이 Minor 둘, Nit 둘과 냄새 판단이다. 명세 축은 Critical·Major 없이 Minor 다섯이다. 인계 세션의 판단(로그인 401에 `WWW-Authenticate`를 싣지 않음)은 명세 축이 방어 가능한 Minor로 판정했다(로그인은 본문으로 받으므로 Bearer 챌린지가 오해를 부른다).

고친 것:
- `http.md`의 `/health` 에 401과 403이 없는 까닭과 그 밖의 모든 라우트가 401을 낸다는 문장이 `PUBLIC_PATHS` 셋과 어긋나 `PUBLIC_PATHS`의 경로에는 미들웨어의 401이 없고 로그인의 401은 라우트가 낸다고 고쳤다.
- `http.md`의 `LoginVerifier` 위치(포트는 `http/auth.py`, 구현은 `http/logins.py`)와 "자격은 셋" 항목에 함께 받는 기간을 가리키는 괄호를 더했다.
- `logins.py` 모듈 독스트링의 "그 메모리가 스레드마다 남았다"(프로브 README가 어림이라 적은 원인 설명)를 측정한 수치(36~43개 스레드 685~818 MiB, 전용 넷 76 MiB)와 "남는 까닭은 어림이다"로 바꿨다.
- 안 쓰이는 `LoginService.durations` 프로퍼티를 지웠다. `"로그인하지 않았다"` 문구를 `NOT_LOGGED_IN_MESSAGE` 상수로 모았다. `LoginService._count`를 `_take_attempt`로, 어댑터의 열 이름 `SIGNING_KEY_BYTES`를 `SIGNING_KEY_VALUE`로 바꿨다(`logins.SIGNING_KEY_BYTES`는 길이 32라 뜻이 달랐다).

남긴 것과 이유:
- `LoginClaims.expires_at`(시험만 읽음), `auth_router`의 `token_minutes` 인자(`durations`와 겹침), `_open`의 튜플 반환, 쿠키 줄의 `list[str]`: 냄새 판단이고 동작에 영향이 없어 두었다.
- `forwarded_address`가 `::ffff:1.2.3.4`를 `::ffff:102:304`로 적고 `fe80::1%eth0`의 영역 번호를 남기는 것: 명세 "IP 주소로 읽힐 때만"을 어기지 않는다. 변형 입력을 고정하는 시험은 없다.
- `_open`이 None일 때 `counted.locked`면 "잠김"도 남기는 것: 해시가 그 사이 바뀌어 잠금이 지워졌을 수 있다. 명세 "로그인" 5·6이 이 갈래의 기록을 정하지 않았다. 04(갱신)나 06(비밀번호 정하기)가 해시를 바꾸는 길을 들일 때 정한다.
- ADR 0062에 "해시 전용 스레드 넷"의 이력이 없는 것: 명세가 정한 결정이고 ADR 본문은 틀리지 않는다. 이력은 사용자 승인이 필요해 이 PR에 넣지 않았다.
- `http.md`의 "(`/health`는 둘 다 지나 라우터의 405다)": `/health`에 대해서는 참이다. 로그인과 첫 계정 확인의 같은 갈래는 직접 돌려 보지 못해 넓히지 않았다.

## 사용자 결정: 로컬 모델 시험

> 사용자: (선택) "돌린다 (어림 $0.27~$0.59, 최악 $1.77)" — 설명: "RTX A5000 파드 2대를 먼저 띄우고, 재고가 없으면 RTX 3090, A40 순으로 시도합니다. 30분 기준 어림은 $0.27(A5000)에서 $0.59(A40)이고, 타이머가 90분 뒤 파드를 지우므로 최악은 $0.81(A5000)에서 $1.77(A40)입니다. 단가는 2026-11-13에 웹 요약에서 읽은 값이라 원문과 대조하지 않았습니다."

근거는 `uv run --env-file ../../../.env python tools/llm_local.py run`(`--yes` 없이)의 출력이다(종료 코드 4, 아무것도 띄우지 않음). 단가는 그 도구가 웹 요약에서 읽은 값이고 원문과 대조하지 않았다.

## 검증 결과(이 세션이 직접 친 것)

- `uv run pytest tests/test_login_http.py tests/test_login_tokens.py tests/adapters/test_postgres_accounts.py tests/test_server.py tests/test_system_admin_command.py -q -x`: 407 passed(리뷰 반영 뒤).
- `uv run --env-file ../../../.env pytest -m llm -q`: 24 passed, 504.53초(리뷰 반영 전의 작업 트리. 반영은 이름 바꾸기와 문구 상수 모으기라 동작을 바꾸지 않았다. 코드를 읽은 판단이다).
- `pnpm -C web/apps/admin exec playwright test`: 11 passed(1.2분).
- 카나리아 셋(`http_rule_continuation_422`, `http_rule_pre_owner_damage`, `http_rule_llm_widget`): 각각 통과 4, 실패 0, "없음" 섞인 통과 0. claude 2.1.325. 세 명세의 `# 최신 결과:` 줄을 고쳤다.
- `uv run --env-file ../../../.env python tools/llm_local.py run --yes`: 통과 4, A40 한 장(shared 배치), 449.1초, 시간당 $0.59(단가는 2026-11-13에 웹 요약에서 읽은 값이라 원문과 대조하지 않았다), 토큰 입력 6191·출력 112, 시험 종료 코드 0. 도구의 출력(JSON)에서 읽었다. 회차 파일은 `C:\Users\User\.agent-os\llm-local\feature%2F03-login-logout-me-and-setup-beside-shared-tokens\records\round-0001-20261126T072544Z.json`이다.
- `uv run ruff check . && uv run ruff format --check .`와 `uv run pyright`: 초록(리뷰 반영 중에 친 출력. ruff는 import 순서 한 건을 `--fix`로 고친 뒤 다시 통과).
- `uv run python tools/run_checks.py`(리뷰 반영 뒤 전체): 열아홉 가운데 러너가 돌리는 것 모두 `Passed`(pytest 813.2초, web-verify 937.4초, pyright 65.5초, run-hooks 110.4초). 출력의 마지막 줄들에서 읽었다.
- 첫 커밋 시도가 pre-commit의 변이 표 검사(`check-mutations`)에서 막혔다. `.scratch/end-user-channel/probes/contract_mutations.toml`의 변이 13(서명 토큰이 공유 토큰의 면도 연다)이 `auth.py`의 `case _Shared` 원문을 정확히 한 번 찾는데 이 변경이 그 블록에 `claims = await self._claims(request)` 줄을 더해 0번이 됐다. 원문과 바뀐 쪽 둘에 그 줄을 더해 고쳤다. `uv run python tools/mutate.py --check .scratch/end-user-channel/probes/contract_mutations.toml`는 변이 31 모두 원문이 한 번씩 있다고 답했고, `uv run python tools/mutate.py .scratch/end-user-channel/probes/contract_mutations.toml 13`은 기준선 초록, 변이 빨강(`test_자격은_자기_면만_연다_세_면마다_다른_두_자격은_401이다` 실패)으로 기대대로였다.
