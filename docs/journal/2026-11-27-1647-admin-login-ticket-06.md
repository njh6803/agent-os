# 2026-11-27 admin-login 티켓 06: 계정을 다루는 경로, 링크로 비밀번호 정하기, 내 비밀번호 바꾸기

브랜치 `feature/06-account-routes-set-password-and-change-my-password`, 티켓 `.scratch/admin-login/issues/06-account-routes-set-password-and-change-my-password.md`. 아래는 커밋 전이고 작업 트리에만 있다.

## 사용자 프롬프트

붙여 넣은 `next-session` 지시문 하나뿐이다(원문은 길어 요지만 옮긴다).

> 사용자: `.claude/skills/implement/SKILL.md`를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`다. 인자는 `.scratch/admin-login/issues/06-account-routes-set-password-and-change-my-password.md`다. 다음 작업: 시스템 관리자가 계정을 만들고 비밀번호 링크를 주고받는 경로 일곱과, 로그인한 운영자가 자기 비밀번호를 바꾸는 경로를 계약에 더한다. 브랜치: `feature/06-account-routes-set-password-and-change-my-password`. 모델: Sonnet 5.5 / high. 이번 요청 범위: PR과 병합까지. 로컬 모델 시험은 `--yes` 없이 쳐 예상 비용을 사용자에게 보이고 확인받은 뒤에만 `--yes`를 붙인다.

사용자의 정정이나 피드백은 없었다. 이 세션에서 사용자가 답한 것은 하나다. 로컬 모델 시험의 비용 확인 선택 화면에서 글자 그대로 "돌린다 (Recommended)"를 골랐다. 그 설명은 "--yes를 붙여 실행합니다. 단가는 2026-11-13에 웹 요약에서 읽은 값이라 원문과 대조하지 않았습니다(어림). 후보별 30분 비용은 $0.27에서 $0.59 사이이고, 최악 후보는 90분에 $1.77입니다."였다. 보여 준 표는 pods RTX A5000 2대 시간당 $0.54(30분 $0.27, 최악 90분 $0.81), RTX 3090 2대 $1.00($0.50, $1.50), A40 2대 $1.18($0.59, $1.77), shared A40 1대 $0.59($0.29, $0.88)였다. 이 확인은 지금 도는 한 번의 실행에만 해당한다.

## 한 것(커밋 전, 작업 트리에만 있다)

- 새 파일: `src/agent_os/admin/accounts.py`(계정 다섯 경로의 라우터와 모델), `src/agent_os/http/account_admin.py`(`AccountAdmin` 서비스: 만들기, 링크 만들기, 활성 바꾸기, 잠금 풀기, 목록), `tests/test_account_routes_http.py`(68건), `.scratch/admin-login/probes/account_routes_mutations.toml`(변이 14, 모두 기대 빨강).
- 고친 파일: `admin/auth.py`(`change_my_password`, `set_password_by_link`), `http/logins.py`(링크로 정하기와 바꾸기), `http/accounts.py`·`adapters/postgres/accounts.py`·`account_tables.py`(포트, 어댑터, 링크 표 `PASSWORD_LINKS`), `http/permissions.py`(일곱 줄), `http/auth.py`(`PUBLIC_PATHS` 다섯, `LOGIN_ONLY_PATHS`에 `/auth/password`), `server.py`(계정 라우터 조립), `openapi.json`과 생성 TS 타입, `.claude/rules/admin.md`(409 문장)와 `.claude/rules/http.md`(공개 경로 다섯, 로그인만 여는 경로).
- 시험을 맞춘 곳: `tests/fake_accounts.py`, `tests/test_system_admin_command.py`, `tests/test_server.py`(공개 경로 다섯), `tests/test_login_http.py`, `tests/adapters/test_postgres_accounts.py`(+7), `tests/channel/http/test_router.py`(새 컴포넌트 여덟, 409 목록을 계정 경로 넷과 채널 경로로 가름), `tests/test_operator_accounts_on_runs.py`(`_GATED`에 계정 다섯), `web/packages/api-client/src/clients.test-d.ts`(경로 여섯).

## 판단과 결정

근거의 종류: 아래 가운데 `/auth/me`와 겹쳐 띄운 검증의 문장은 이 세션이 시험의 실패 출력과 `eslint.config.test.ts`의 ENOENT 출력을 직접 본 것이다. `/auth/me`는 `tests/test_account_routes_http.py`의 첫 실패(끊은 뒤 401을 기대한 단언)를 본 뒤 코드를 읽고 고쳤고 고친 시험이 통과했다. 겹침이 원인이라는 문장은 단독으로 돈 러너의 web-verify가 통과했다는 것으로 갈랐고, 겹쳐 돌린 `web verify`를 다시 쳐서 재현하지는 않았다(어림). 나머지 판정 규칙과 차례는 코드를 쓰며 정한 설계이고 시험이 단언한다.

- 판정 규칙은 `http`에, 행 잠금과 읽기쓰기는 어댑터에 둔다(원칙 IV). 잠금 차례는 계정 줄, 그다음 링크와 로그인 줄이다.
- 링크 토큰은 `secrets.token_urlsafe(32)`이고 SHA-256 해시만 저장한다. 기한은 만든 때부터 24시간이다. 새 링크는 앞의 쓰지 않은 링크를 못 쓰게 한다.
- 내 비밀번호 바꾸기는 횟수를 먼저 늘린 뒤 견주고, 견준 뒤 둘째 짧은 트랜잭션에서 해시가 그대로인지 다시 본다. 바뀌었으면 아무것도 쓰지 않고 `body.current_password` 422다.
- `/auth/me`는 짧은 JWT만 읽으므로 로그인을 끊은 뒤에도 그 짧은 JWT가 살아 있는 동안은 200이다. 끊김은 `/auth/refresh`의 401과 데이터베이스의 `ended_at`으로 본다.
- 이 실행에서 `run_checks.py`와 `pnpm -C web verify`를 동시에 띄웠더니 `web verify`가 `judge-*` 임시 폴더를 서로 지워 `eslint.config.test.ts`가 ENOENT로 빨개졌다. 코드 문제가 아니라 겹침이었고, 단독으로 돈 러너의 web-verify는 통과했다. 같은 검증을 겹쳐 띄우지 않는다.

## 검증 현황(이 세션이 본 것)

아래는 이 세션이 그 명령을 직접 쳐서 출력으로 본 것이다.

- `uv run ruff check .`, `uv run ruff format --check .`(2698개 서식 맞음), `uv run pyright`(0 errors) 통과.
- `uv run python tools/run_checks.py`: check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest(751.0초), web-verify(807.3초) 모두 Passed.
- 관리 화면 e2e `pnpm -C web/apps/admin exec playwright test`: 11 passed.
- `uv run --env-file ../../../.env pytest -m llm`: 24 passed(토큰 262,088, 트레이스 30개, 모델 호출 61건, 트레이스를 남기지 않은 LLM 테스트 2개는 세지 못했다).
- 변이 표 `account_routes_mutations.toml` 14개가 모두 기대 빨강·결과 빨강이었다.
- 로컬 모델 시험(`uv run --env-file ../../../.env python tools/llm_local.py run`): 먼저 `--yes` 없이 쳐 예상 비용 표를 받았고(종료 4, 아무것도 띄우지 않음) 사용자가 위처럼 확인한 뒤 `--yes`로 한 번 쳤다. 통과(종료 0)다. 모델은 `GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`와 `openai/gpt-oss-20b`, 엔진은 vLLM 0.33.0, GPU는 A40 1대에 두 모델을 함께(shared) 띄웠다. `pytest -m llm_local` 4 passed(56.82초), 토큰은 입력 6,191·출력 112·모델 호출 4건·트레이스 2개다. 걸린 시간 350.0초이고 단가 시간당 $0.59(2026-11-13 웹 요약 값이라 원문과 대조하지 못함)로 어림하면 약 $0.06이며 청구서는 보지 않았다. 기록 묶음의 `commit`은 기준 커밋 `c3ad162fc`이고 시험한 것은 커밋 전 작업 트리다. 회차 파일은 `C:\Users\User\.agent-os\llm-local\feature%2F06-account-routes-set-password-and-change-my-password\records\round-0001-20261127T075500Z.json`이다.

## 셀프 리뷰(`/code-review`)

범위: base `c3ad162fc4e9d1e8d5cf712f566cf78148bc0688`(= `origin/dev`, `git fetch` 뒤 맨 위가 같았다), 수정 파일 20개, 커밋 0개, 미추적 5개(본 코드 둘, 시험 하나, 변이 표 하나, 일지). 표준 축(sonnet·high)과 명세 축 두 서브에이전트가 돌았다. Critical·Major는 둘 다 없었다. 아래 판정은 이 세션이 코드를 열어 확인한 것이다.

고친 것:
- `.claude/rules/http.md`: "걸리는 라우터는 … 셋"을 `accounts_router`를 더한 넷으로 고쳤다(두 축이 같은 자리를 냈다. `Grep`으로 `REQUIRE_PERMISSION`이 걸린 라우터 넷을 확인했다). 409 설명을 나눠 쓰는 라우트에 계정을 다루는 라우트를 더하고, 계정 만들기와 내 비밀번호 바꾸기는 자기 설명을 `descriptions`로 적는다고 덧붙였다(두 라우트의 선언을 열어 봤다).
- `src/agent_os/http/routes.py`의 409 주석, `src/agent_os/admin/http.py`의 "관리 라우트는 409 를 내지 않는다" 독스트링이 같은 이유로 낡아 고쳤다(명세 축 3번, 약한 지적이지만 admin.md와 어긋났다).
- `tests/test_login_http.py`: 시험 이름에서 빠진 `/auth/set-password`를 더했고, "비활성으로 바꾸는 경로는 06이 짓는다" 미래형 주석을 현재형으로 고쳤다.
- `AccountAdmin.set_active(active: bool)`를 `enable`/`disable`로 나눴다(표준 축 4번, `CODING_STANDARDS.md`의 불리언 플래그 항목. 두 갈래의 부수 효과가 다르다). 라우트는 PUT과 본문 `active` 그대로이고 라우터가 `body.active`로 고른다.
- 해시 함수 둘(`link_digest`, `logins._digest`)을 `token_digest` 하나로 합쳤다. `account_admin.py`가 따로 정의하던 `Taken`은 `http/accounts.py`의 것을 가져온다(표준 축은 "쓰이지 않는다"고 했으나 80행의 반환 주해로 쓰이고 있었다. 중복 정의라는 점만 맞았다).
- `admin/accounts.py`가 `admin/auth.py`와 글자까지 같은 `_invalid`와 `NOT_LOGGED_IN_MESSAGE`를 다시 정의하던 것을 `invalid_field`(공개 이름)와 상수를 가져오게 했다.
- `change_password`: 견주는 사이 계정이 지워졌거나 비활성이 되면 `wrong_current`(422 "지금 비밀번호가 맞지 않는다")가 아니라 `gone`(401)을 낸다. 같은 계정이 첫 트랜잭션에서는 401이고 로그인의 같은 갈래(`test_견주는_사이_계정이_꺼지면_맞았어도_로그인이_아니다`)도 401이라 맞췄다. 비밀번호는 맞았는데 틀렸다는 거짓 문구가 나가던 것이다. 티켓은 해시가 바뀐 경우만 422로 정했고 그 갈래는 그대로다. 시험 `test_견주는_사이_계정이_꺼지면_바꾸지_않고_401이다`가 401을 고정한다.
- 변이 표 12번의 원문을 새 조건문(`if row.password_hash != attempt.stored_hash:` 두 줄)에 맞췄다. `mutate.py --check`가 14개 모두 원문이 한 번씩이라 했고, 5·6·12번을 돌려 모두 "기대 빨강, 결과 빨강"이었다(출력을 읽었다).

남긴 것과 이유:
- `unlock`이 잠긴 적 없이 틀린 횟수만 쌓인 계정에도 `unlocked`를 남긴다(명세 축 4번). 횟수를 지운 것도 한 일이고 시험 `틀린_횟수만_쌓이고_잠기지_않은_계정도…`가 그 해석을 고정한다. 명세 표의 "시스템 관리자가 잠금을 풀었다"와 어긋난다고 읽을 수도 있어 사용자에게 알린다(PR 본문).
- `auth.py`에서 `forwarded_address(request.headers.getlist("x-forwarded-for"))`가 다섯 번 되풀이되는 것(Duplicated Code, Nit). 이 변경이 더한 것은 둘이고 나머지는 앞 티켓이 쓴 것이다. 헬퍼로 묶으려면 그 라우트들을 함께 만져야 해 이 티켓의 몫이 아니다.
- `link_token`·`link_expires_at`이 `PasswordLink`, `CreatedAccount`(응답 모델), `IssuedLink`, `CreatedAccount`(서비스의 데이터클래스)에 걸쳐 다니고, 같은 이름의 `CreatedAccount`가 두 모듈에 있다(Data Clumps·이름 충돌, Nit). 응답 모델은 계약에 이름이 서야 해서 `CreatedAccount`를 바꾸면 계약이 바뀐다. 서비스 쪽 이름만 바꿀 수도 있으나 작성자 재량으로 둔다.

밀 주장(PR 직전 리뷰에 넘길 새 문장): ① `http.md`의 "걸리는 라우터는 … 계정 라우터(`accounts_router`) 넷이다"(근거는 `Grep`으로 본 `REQUIRE_PERMISSION`의 사용처 넷). ② `http.md`의 "계정 만들기와 내 비밀번호 바꾸기는 자기 설명을 `descriptions`로 적는다"(근거는 두 라우트의 선언을 읽은 것). ③ `admin/http.py` 독스트링의 "409 를 내는 관리 라우트는 계정을 다루는 것과 내 비밀번호 바꾸기다"(근거는 계약의 409 경로를 센 명세 축 보고와 `test_409_는_채널_라우트와_계정을_다루는_라우트에만_있다`가 통과한 것).

다시 돌린 명령(전부 이 세션이 쳐서 출력을 봤다): `uv run ruff format .`(변경 없음), `uv run ruff check .`, `uv run pyright`(0 errors), `uv run lint-imports`(9 kept), 영향받는 시험 여덟 파일 618 passed(296.47초). 전체 러너·e2e·`-m llm`은 반영 전에 초록이었고, 반영 뒤에는 커밋의 pre-commit이 갈음한다. 로컬 모델 시험은 반영 전 작업 트리로 쳤고 반영은 `src/agent_os/http`와 `admin`의 모양 정리와 한 갈래의 상태 코드라, 그 시험이 재는 실제 모델 경로를 건드리지 않았다고 본다(어림이다. 코드를 읽은 판단이고 다시 재지 않았다).

## 카나리아(규칙 파일을 고친 변경)

`.claude/rules/admin.md`와 `http.md`를 고쳤고 `tools/sibling_overlap.py`가 그 두 파일을 원천으로 든 카나리아 명세 다섯(`admin_rule_first_item`, `admin_rule_conversation_list`, `http_rule_continuation_422`, `http_rule_pre_owner_damage`, `http_rule_llm_widget`)을 다시 돌리라고 알렸다. 셋은 같은 `claude -p` 세션 규약으로 커밋 전 작업 트리에서 `uv run python tools/canary.py <명세> <스크래치>`로 실제 돌렸다(`claude --version`이 2.1.325). 다섯 모두 출력의 집계 줄이 "통과 4 · 실패 0 · "없음" 섞인 통과 0"이었다(이 세션이 집계 줄을 읽었다). 갈래의 커밋은 `c3ad162fc`다. 다섯 명세의 `# 최신 결과:` 줄 앞에 이번 판을 더했고 `canary.py --shape`가 다섯 모두 통과했다. 고친 뒤 `sibling_overlap.py`는 카나리아 알림 없이 끝났다.

## 커밋 뒤 인계(이 일지에 이어 쓴다)

이 세션의 지금 제목은 `feature/06-account-routes-set-password-and-change-my-password`다(인계하며 `(인계함)`을 붙인다). 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤`에 와서 넘긴다(`handoff.md`). 이 세션은 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다).

- 커밋 `82588066638eb097462e85d540e130e862824836`(`feat: 계정을 다루는 경로와 링크로 비밀번호 정하기와 내 비밀번호 바꾸기를 더한다 (admin-login 06)`)이 두 번째 시도에서 pre-commit을 모두 지났다(백그라운드 명령이 종료 코드 0). 첫 시도는 pytest 한 건(`tests/tools/test_rerun_runner.py::test_첫_인계가_나면_새_회차를_열지_않는다`)이 `JSONDecodeError: Extra data`로 실패해 막혔다. 같은 파일을 홀로 돌리면 63개가 모두 통과했다(`uv run pytest -q tests/tools/test_rerun_runner.py`, 196.09초). 이 변경이 건드리지 않은 시험이고 병렬 러너에서만 난 출력 섞임으로 보았다(어림. 원인을 재현하지는 않았다).
- 푸시와 PR은 아직 없다. 티켓 `Status`는 `done`이고 체크박스는 마지막 칸(`adapters/`를 고쳐 LLM 시험의 병합 조건 범위에 든다)만 비어 있다. 그 칸은 마지막 봇 회차를 반영한 뒤 로컬 모델 시험이 통과하면 채운다.
- 로컬 모델 시험은 한 번 통과했다(위 "검증 현황"). 시험한 것은 셀프 리뷰 반영 전의 작업 트리라 `merge.md` 병합 전 3대로 마지막 봇 회차 뒤에 다시 쳐야 한다. 사용자의 비용 확인("돌린다 (Recommended)")은 그 한 번에만 해당한다. 다시 칠 때는 `--yes` 없이 쳐 예상 비용을 사용자에게 보이고 새로 확인받은 뒤에만 `--yes`를 붙인다.
- PR 본문에 알릴 것: ① `unlock`이 잠긴 적 없이 틀린 횟수만 쌓인 계정에도 `unlocked`를 남긴다(위 "셀프 리뷰"의 남긴 것. 명세 표의 "시스템 관리자가 잠금을 풀었다"와 어긋난다고 읽을 수도 있다). ② 09 세션의 워크트리(`09-admin-ui-login-and-refresh-rule`)가 `web/packages/api-client/src/clients.test-d.ts`를 함께 고치는 중이라 나중에 병합하는 쪽에서 글자 충돌이 날 수 있다(`sibling_overlap.py`가 알렸다).
- 푸시 전과 병합 전에 `origin/dev`가 이 일지 쓸 때의 `c3ad162fc`에서 움직였는지 본다. 움직였으면 dev를 합치고 `tests/test_permissions.py`(권한 표 전수 검사)와 `tests/test_server.py`(계약 신선도)가 새로 더해진 경로나 번호와 부딪히는지 본다.
- 인계 직전의 작업 트리에는 이 일지의 이 절이 커밋 없이 남아 있다. 새 세션이 같은 파일을 이어 쓰고 커밋한다.
- 인계: 커밋 뒤. 이 세션의 제목을 `feature/06-account-routes-set-password-and-change-my-password (인계함)`으로 바꿨고(바꾸기 전 제목은 `feature/06-account-routes-set-password-and-change-my-password`), 멈출 백그라운드 작업은 없었으며, `git worktree unlock`이 출력 없이 끝났다.
- open-session을 부른다 2026-11-27T08:57:00Z

## PR 열기와 봇 회차(새 세션이 이어 씀)

PR은 #656이다(머리 `3f21aeb83`로 열었다). 새 세션이 `EnterWorktree`로 들어와 `origin/dev`가 `c3ad162fc`에서 움직이지 않았음을 `git fetch`로 보고 `sibling_overlap.py`를 쳤다(번호 겹침 없음, 글자 충돌 후보는 09 워크트리의 `clients.test-d.ts` 하나). 일지의 인계 절을 커밋(`3f21aeb83`)하고 푸시했다. PR 본문에 `unlock_account` 항목과 09와 겹칠 수 있는 후보를 적었다.

**CodeRabbit.** PR을 연 직후 `@coderabbitai review`를 남겼으나 무료 한도에 걸려 리뷰가 없다(`Review rate limited`, "다음 38분 뒤"). 한도에 걸린 푸시는 회차로 세지 않는다. 대신 CLI(0.7.5, `Seat: not assigned`)로 `--base origin/dev` 로컬 리뷰를 `coderabbit-review` 서브에이전트로 돌렸다. 리뷰는 끝까지 돌았고 6건이다. Critical 없음, 서브에이전트가 코드를 읽어 CodeRabbit의 Major 둘을 오탐으로 판정했다(링크 판정과 사용은 이미 한 트랜잭션이고, 계정 라우터는 이미 라우터 전체에 `REQUIRE_PERMISSION`이 걸려 있다. 이 세션이 `accounts.py`와 `logins.py`를 열어 둘째는 확인했다).

**claude-review 첫 회차**(이 PR의 첫 리뷰). 경계 문제 없음, 느낌표 맞음. Minor 둘, Nit 둘이다. 판정은 지적마다 한다.
- `token_digest`가 계정 관리 모듈에 있고 `logins.py`가 거기서 가져온다(Minor): 응집은 맞는 지적이다. 이동은 `login_tokens.py`와 두 import를 만지고 다시 전체 검증을 도는 값이 들어 뒤로 넘긴다.
- `CreatedAccount` 이름 겹침(Minor): 응답 모델의 이름은 계약에 서 있고 서비스 쪽 이름만 바꿀 수 있다. 위 셀프 리뷰에서 작성자 재량으로 뒀던 것이라 뒤로 넘긴다.
- `forwarded_address(...)` 되풀이와 `_address`(Nit), `invalid_field`와 `NOT_LOGGED_IN_MESSAGE`의 자리(Nit): 앞 티켓의 라우트를 함께 만져야 해 이 티켓의 몫이 아니다. 뒤로 넘긴다.

**로컬 CodeRabbit 리뷰의 Minor(이 세션이 코드를 열어 확인한 것).**
- 고쳤다: 비활성 계정의 링크 시험 공백. 링크는 살려 둔 채 계정 줄의 `disabled_at`만 직접 세워도 404인지 보는 시험(`test_링크가_살아_있어도_계정이_비활성이면_404이고_비밀번호가_정해지지_않는다`)을 더했다. `_usable_link`의 계정 상태 검사를 지운 변이에서 이 시험이 빨개졌고(종료 1) 되돌린 코드에서 통과했다. 기존 시험은 활성 바꾸기 경로로 끄는데 그 경로가 링크도 못 쓰게 해서 그 검사가 빠져도 통과했다.
- 뒤로 넘겼다(아래 "다음"): 링크가 든 201 두 응답에 `Cache-Control: no-store`가 없다(`admin/http.py`의 다른 비밀성 응답만 싣는다는 것은 `Grep`으로 확인했다. 다만 POST 응답은 기본이 캐시되지 않고, 더하면 `openapi.json`의 응답 머리 문서가 바뀌는 계약 변경이라 이 티켓에 넣지 않았다). `change_password`가 그 계정의 쓰지 않은 링크를 못 쓰게 하지 않는 점은 명세에 그런 줄이 없어(명세는 링크 새로 만들기와 비활성으로 바꾸기에서만 못 쓰게 한다고 적었다) 사용자가 정할 일이다. `claims.login_id`가 끊겼는지 보지 않고 `keep`에 쓰는 점, `list_accounts`의 쪽 나누기 없음, 링크 줄이 지워지지 않고 쌓이는 점, `/auth/set-password`의 호출 횟수 제한 없음, 기존 `forwarded_address`가 `X-Forwarded-For`를 그대로 믿는지(이 변경 밖의 코드라 서브에이전트가 읽지 않았다).
- 오탐으로 판정: CodeRabbit의 "약한 비밀번호 응답을 링크를 쓰기 전에 검사하라"는 이미 `test_링크가_죽었으면_비밀번호_규칙보다_먼저…`가 살아 있는 링크에 약한 비밀번호를 보내 422와 링크 미소비를 본다.
