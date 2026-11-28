# 2026-11-28 admin-login 티켓 13: 공유 토큰을 걷고 운영자 경로를 로그인 쿠키로만 연다

브랜치 `feature/13-remove-shared-tokens`, 티켓 `.scratch/admin-login/issues/13-remove-shared-tokens.md`. 새 세션(Sonnet 5.5 / high)이 워크트리 `13-remove-shared-tokens`에서 구현했다.

## 사용자 프롬프트

붙여 넣은 `next-session` 지시문 하나뿐이다(원문은 길어 요지만 옮긴다).

> 사용자: 다음 작업은 `.scratch/admin-login/issues/13-remove-shared-tokens.md`다. 공유 토큰 둘(`AGENT_OS_ADMIN_TOKEN`, `AGENT_OS_CHANNEL_TOKEN`)을 걷고 운영자 경로를 로그인 쿠키로만 연다(PR 제목에 느낌표). 다음 단계: 구현. 이번 요청 범위: PR과 병합까지. 이어받을 상태: 열린 PR #651(티켓 04, 단독 배포 compose)이 `README.md`와 `deploy/standalone`을 같이 고치므로 나중에 병합하는 쪽이 충돌을 푼다. 단독 배포 e2e와 로컬 모델 시험(비용 확인)은 티켓 본문 '검증'대로 한다.

선택 화면의 답은 하나다. 로컬 모델 시험을 돌릴지 물었고, 도구가 낸 예상 비용(첫 후보 RTX A5000 파드 2대가 어림 30분에 $0.27, 다음 후보로 넘어가면 최악 90분 기준 $0.81에서 $1.77, 단가는 웹 요약에서 읽은 값이라 원문과 대조하지 않은 어림)을 보인 질문에 사용자는 다음 선택지를 골랐다.

> 사용자: 돌린다 (Recommended) — --yes를 붙여 로컬 모델 시험을 돌립니다. 티켓의 검증 명령에 들어 있고, 비용은 위 어림 안입니다.

사용자의 정정이나 피드백은 없었다.

## 한 것

- 서버: `http/auth.py`의 `RequireToken`이 접두사→자격 표에서 `SharedToken`을 잃고 `SiteSigned` 하나만 남겼다. 표에 없는 경로의 기본값이 운영자 로그인(`LoginVerifier`로 쿠키 `__Host-aos_at`의 짧은 JWT 검증)이라 `/runs`도 쿠키로만 열린다. 운영자 경로의 401은 `WWW-Authenticate`를 싣지 않고, 최종 사용자 경로의 401은 싣는다. `Authorization` 머리는 운영자 경로에서 읽지 않는다.
- `http/permissions.py`: `SHARED_TOKEN_PERMISSIONS`를 걷고, 로그인 없는 요청이 권한을 요구하는 자리에 닿으면 `LookupError`다.
- `server.py`의 `create_app`과 `tools/export_openapi.py`는 토큰 인자를 받지 않는다. `openapi.json`은 설명 한 줄만 바뀌었다.
- `main.py`: `serve`가 두 변수를 읽지 않는다. 환경에 남았으면 변수마다 "…은 더 쓰지 않습니다. 지워도 됩니다." 한 줄을 찍고(이름만, 값은 싣지 않는다) 그대로 뜬다(`RETIRED_TOKEN_ENVS`, `_note_retired_tokens`). `--host` 비루프백 진단은 토큰이 아니라 로그인을 말한다.
- 웹: `createAdminClient`와 `createChannelClient`, `AdminClient`·`ChannelClient` 타입, `bearer`를 걷었다. 남은 것은 `createOperatorClient`와 위젯 클라이언트다. e2e 하네스(e2e-stack, 관리 화면·위젯·위젯 테스트 페이지, e2e-standalone)는 서버 명령으로 계정을 만들고 로그인한다. 단독 배포 e2e는 `docker compose exec -T serve agent-os operator system-admin e2e-operator`로 계정을 만들고 비밀번호는 표준 입력으로 넣는다.
- 시험: `tests/fake_accounts.py`의 `operator_cookie()`와 `UnusedAccounts`의 기본 서명 키로 단위 시험이 데이터베이스 없이 로그인 쿠키를 만든다. 서브프로세스 시험이 쓰는 `tests/operator_login.py`(`create_system_admin`, `log_in`)를 새로 뒀다.
- 문서: `.env.example` 둘, `deploy/standalone/README.md`, `README.md`, `CONTEXT.md`, `.claude/rules/http.md`(`writing-for-agents`를 먼저 불렀다), `tests/tools/test_deploy_guide.py`, 새 업그레이드 조각 `docs/release-notes/upgrade/remove-shared-tokens.md`.
- 하위 에이전트 넷에게 시험과 웹 하네스 이전을 나눠 맡겼고(같은 워크트리), 보고를 받은 뒤 `tests/test_server.py`와 `tests/test_permissions.py`의 269개를 직접 다시 돌려 통과를 봤다.

## 이 세션이 번복하거나 정한 것

- 인계(`hook_handoff`)의 계기가 `셀프 리뷰 직전`에 왔을 때 로컬 모델 시험이 유료 파드를 띄운 채 백그라운드로 돌고 있었다. 인계 절차의 "대기 멈추기"가 이 작업을 멈추면 파드가 90분 타이머까지 청구되므로 인계하지 않고 이 세션에서 이었다.
- `.scratch/end-user-channel/probes/cors_scoped.py`는 `SharedToken`을 쓰던 옛 프로브라 이제 그대로는 돌지 않는다. pyright 검사 범위(`src`, `widget-admin/src`, `tests`, `tools`) 밖이고 결과와 근거는 명세에 남아, 독스트링에 그 사실만 적었다.
- 옛 이름 잔존은 허용한 예외만 남았다. `main.py`의 안내와 그 시험, `useForgetOldTokens`와 `SettingsPage.test.tsx`(옛 입력 칸이 없음을 보는 부재 시험), `tests/tools/test_check_quotes.py`의 임의 문자열 픽스처, `web/packages/ui`(디자인 시스템 동기화의 범위), `docs/constitution/history.md`의 이력.
- ADR 0011·0015에 이력 항목을 더하는 일은 승인이 필요해 이 PR에 넣지 않았다.

## 검증 결과(셀프 리뷰 전, 이 세션이 직접 친 명령의 결과)

- `uv run ruff check .`와 `uv run ruff format --check .` 통과. `uv run pyright` 전체 0 오류.
- `uv run python tools/run_checks.py` 통과(check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify, pytest).
- 하위 에이전트가 친 것을 보고로 받았다. 관리 화면 e2e는 처음에 12건 가운데 `decision.e2e.ts`의 한 건이 5초 안에 `run_finished`를 보지 못해 실패했고, 그 파일만 다시 쳐 3건이 통과했다(한 번 난 시간 초과로 본다). 위젯 e2e 19건, 위젯 테스트 페이지 e2e 41건, 단독 배포 e2e 15건 통과.
- `uv run --env-file ../../../.env pytest -m llm -q`: 24개 통과(13분 37초, LLM 토큰 합계 270,530, 트레이스를 남기지 않은 LLM 테스트 2개는 세지 못했다). `-m llm_widget`: 1개 통과(LLM 토큰 합계 17,047). `-m llm_portal`: 1개 통과(LLM 토큰 합계 6,997).
- 로컬 모델 시험(`uv run --env-file ../../../.env python tools/llm_local.py run --yes`)은 사용자 확인 뒤 돌렸다. 먼저 `--yes` 없이 쳐 예상 비용을 보였고, 실행에서는 앞선 후보에 재고가 없다는 400이 나 A40 파드 2대로 넘어갔다. 도구의 JSON 출력에 `passed` 4, `test_exit_code` 0, `elapsed_seconds` 333.4, `cost_per_hour` 1.18(단가표 2026-11-13)이 있다. 회차 파일은 `C:\Users\User\.agent-os\llm-local\feature%2F13-remove-shared-tokens\records\round-0001-20261128T023640Z.json`이다. 파드가 지워졌는지는 도구가 "시험이 끝났다"로 끝냈다는 것까지만 봤고 Runpod 쪽에서 따로 확인하지 않았다.

## 셀프 리뷰(`/code-review`, 표준 축과 명세 축 서브에이전트 둘)

범위: 기준 `a11fffed48`(origin/dev와의 merge-base), 파일 50개와 미추적 3개(`remove-shared-tokens.md`, `tests/operator_login.py`, `e2e-standalone/e2e/login.ts`), 커밋 0개. 보고는 두 서브에이전트가 낸 것을 받았다(표준 축은 sonnet·high).

- 고친 것(표준 축): `README.md` 관리 화면 절에 남은 "공유 토큰 둘은 `serve`가 아직 시작할 때 요구하지만(걷어내는 일은 admin-login 티켓 13)" 문장(Major, 미래형 잔존)을 "공유 토큰은 없다. 관리 API와 운영자 채널(`/runs`)은 로그인 쿠키로만 열린다."로 바꿨다. `tests/fake_accounts.py` 독스트링의 "공유 토큰으로 도는 지금의 시험"을 "로그인 쿠키로 도는 시험"으로 고쳤다. `http/auth.py`의 `_refused`가 불리언 인자(`challenge`)를 받던 것을 `CODING_STANDARDS.md`의 불리언 플래그 규칙대로 `headers` 인자로 바꿨다.
- 고친 것(명세 축): `deploy/standalone/compose.yaml:97` 주석의 "토큰, "을 지웠다. 업그레이드 조각을 다시 썼다. 올리기 전 판에는 로그인 화면이 없어 따를 수 없는 "관리 화면의 로그인 화면이 입력 칸 대신…" 안내와, 같은 묶음의 `operator-accounts.md`가 표 여섯을 더한다고 적은 것과 어긋나는 "이 판은 데이터베이스 표를 바꾸지 않습니다" 문장을 걷고, 올린 뒤 첫 계정을 만드는 명령과 포트 포워딩 로그인을 적었다.
- 남긴 것과 이유:
  - e2e-stack과 위젯·위젯 테스트 페이지의 `e2e/stack.ts`는 토큰만 걷고 계정을 만들지 않는다. 그 e2e들은 운영자 경로를 부르지 않는다(명세 축이 grep으로 봤고 `serve.ts` 주석도 그렇게 적는다). 티켓 문구("계정을 만들고 로그인하는 길로 바꾼다")보다 좁은 해석이라 PR 본문에 적는다.
  - 로그인 쿠키 `Set-Cookie`를 `Cookie` 머리로 모으는 같은 일이 `web/apps/admin/e2e/channel.ts`, `web/packages/e2e-standalone/e2e/login.ts`, `tests/operator_login.py`에 있다(Minor, 중복). 다른 패키지와 다른 언어라 공유할 자리가 마땅찮아 둔다.
  - `--host` 진단의 새 문구를 단언하는 시험이 없다(지적 수준). 유지 시간 값이 틀려 `serve`가 종료 코드 2로 끝나는 길에서는 서버가 뜨지 않아 옛 변수 안내가 찍히지 않는다. 티켓은 "그대로 뜬다"만 요구한다.
  - 같은 묶음의 `operator-accounts.md` 2번 줄("이 판의 서버는 이전과 똑같이 동작합니다")은 이 묶음의 로그인 티켓들 때문에 이미 어긋나 있고 이 티켓의 범위 밖이다.
  - 표준 축 Nit: `.claude/rules/http.md:23`의 "접두사는 경로 조각 단위로 보고 (`/end-userx`는…" 문장이 어색하다.
- 다시 돌린 명령: `uv run ruff check src tests README.md`, `uv run ruff format --check src tests`, `uv run pyright src/agent_os/http/auth.py tests/fake_accounts.py` 통과. 나머지 손으로 치는 게이트는 커밋의 pre-commit 결과로 갈음한다(결과는 커밋 뒤에 적는다).
- 카나리아: `.claude/rules/http.md`를 고쳤다는 알림이 가리킨 명세 셋(`http_rule_continuation_422.toml`, `http_rule_pre_owner_damage.toml`, `http_rule_llm_widget.toml`)을 `uv run python tools/canary.py <명세> <출력 디렉터리>`로 돌려 셋 모두 통과 4(실패 0, "없음" 섞인 통과 0, claude 2.1.325, 커밋하기 전의 작업 트리)였고 각 명세의 `# 최신 결과:` 줄을 고쳤다. 처음에는 `--control-commit a11fffed48`을 붙여 돌렸는데, 이 명세들의 대조군은 같은 체크아웃의 규칙 밖 파일이고 옛 커밋의 `http.md`에도 카나리아가 있어 돌리기 전 확인이 명세 오류로 막았다. 그 인자 없이 앞 판들과 같은 방식으로 다시 돌렸다.
- 변이 표: 첫 커밋 시도가 `tools/mutate.py --staged`에서 막혔다. 공유 토큰 코드(`LOGIN_ONLY_PATHS`, `SHARED_TOKEN_PERMISSIONS`, `_Shared`, `AdminPaths`, `ChannelPaths`, `bearer`)가 사라져 원문이 0번인 변이 일곱 건이었다. 걷힌 동작을 겨냥한 다섯(`account_routes_mutations.toml`, `permission_mutations.toml`, `contract_mutations.toml`의 하나씩과 `api_client_mutations.toml`의 둘)은 지웠다. `api_client_mutations.toml`의 "패키지의 타입 에러를 typecheck 가 본다"는 원문을 `createOperatorClient` 줄로 옮기고 `expect_output = ["error TS2322"]`를 더했다(그 변이만 따로 돌려 `src/clients.ts(39,14): error TS2322`를 봤다). `widget_llm_mutations.toml`의 키 빼기 변이는 원문을 새 `serve.ts`의 줄로 옮겼다(실제 모델이 필요한 `llm_widget` 변이라 돌려 보지는 않았다). 그 뒤 `--staged`가 문제 0이었다.
- 새 시험이 빨강을 보는지: 저장소에 두지 않는 스크래치 표(`remove_tokens_mutations.toml`)의 변이 셋을 `uv run python tools/mutate.py <표>`로 돌려 셋 모두 기대대로 빨강이었다. 운영자 경로의 401에 챌린지 머리를 싣게 한 변이는 `test_옛_공유_토큰으로는_운영자_경로가_401이고_챌린지_머리도_없다`가, 최종 사용자 경로의 401에서 머리를 뺀 변이는 `test_최종_사용자_경로는_서명_토큰이_없으면_401이고_챌린지_머리를_싣는다`가, 옛 변수 안내가 값을 싣게 한 변이는 `test_더_쓰지_않는_토큰_변수_둘이_남아도_서버가_뜨고_변수마다_안내_한_줄을_찍고_값은_싣지_않는다`가 잡았다.
- 첫 커밋 시도의 pytest에서 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`가 한 번 실패했다(`assert 1 == 2`). 그 시험만 홀로 다시 쳐 2개가 통과했고(87.72초), 이 변경이 건드리지 않은 파일이라 부하가 겹친 실행의 시간 민감 실패로 본다. 둘째 시도에서는 pytest가 통과했다.
- 인계: 커밋 뒤 경계에서 컨텍스트가 문턱을 넘어 넘긴다. 이 세션의 제목을 `feature/13-remove-shared-tokens (인계함)`으로 바꾸고 워크트리 잠금을 풀었다. open-session을 부른다 2026-11-28T03:34:26Z

## 인계 상세 (커밋 뒤, 새 세션이 이어받을 일)

커밋 ad68887fe까지 했고 푸시하지 않았으며 PR도 없다. 티켓은 이미 done이고 `.scratch/plan.md`도 같은 커밋에 있다.

1. `git fetch origin dev` 뒤 origin/dev를 이 브랜치에 합친다. `tools/sibling_overlap.py`가 dev에서 같이 고쳐진 파일로 CONTEXT.md, README.md, tests/test_main.py, web/apps/admin/e2e/channel.ts, decision.e2e.ts, plugin-toggle.e2e.ts, web/apps/widget/e2e/stack.ts, web/eslint.config.test.ts, web/packages/e2e-stack/src/serve.ts를 알렸다. 충돌을 풀 때 이 브랜치의 뜻(공유 토큰 없음, 로그인 쿠키만)을 지킨다. 합친 뒤 고친 파일을 가리키는 시험과 `tools/mutate.py --staged`를 다시 본다. 합친 변경이 `.claude/rules/http.md`를 고쳤으면 카나리아 명세 셋(`http_rule_continuation_422.toml`, `http_rule_pre_owner_damage.toml`, `http_rule_llm_widget.toml`)을 다시 돌린다.
2. PR을 연다. 제목은 `feat!:`로 시작한다. 본문에 업그레이드 조각(`docs/release-notes/upgrade/remove-shared-tokens.md`)과, e2e-stack과 위젯·위젯 테스트 페이지 stack.ts는 운영자 경로를 부르지 않아 토큰만 걷고 계정은 만들지 않았다는 점과, 열린 PR #651이 `README.md`·`deploy/standalone`을 같이 고쳐 나중에 병합하는 쪽이 충돌을 푼다는 점을 적는다. 열면 ccd_pr `get_status`로 PR을 확인하고 없으면 `bind_pr`로 묶는다.
3. merge.md의 봇 회차와 병합. 워크트리에서 병합하는 세션은 이 워크트리 사본의 next-session merge.md "워크트리에서 병합할 때"를 따른다.

Runpod의 `agent-os-llm-local-shared` 파드는 이 세션이 만들지 않았고 건드리지 않았다. ADR 0011·0015에 이력 항목을 더하는 일은 사용자 승인이 필요해 이 PR에 넣지 않았다.
- open-session을 다시 부른다 2026-11-28T03:36:21Z (첫 시도는 URL 8376자로 상한 8000을 넘어 지시문을 줄였다)
