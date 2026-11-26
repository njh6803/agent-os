# 2026-11-26 admin-login 티켓 04: 갱신과 서명 키 바꾸기

브랜치 `feature/04-refresh-and-signing-key-rotation`, 티켓 `.scratch/admin-login/issues/04-refresh-and-signing-key-rotation.md`. 이 세션의 제목은 인계 전 `feature/04-refresh-and-signing-key-rotation`이었다. 이 일지는 인계 세션이 쓴 것이고 새 세션이 이어 쓴다(커밋은 새 세션이 한다).

## 사용자 프롬프트

붙여 넣은 `next-session` 지시문 하나뿐이다(원문은 길어 요지만 옮긴다).

> 사용자: 저장소는 `C:\project\agent`다. `.claude/skills/implement/SKILL.md`를 읽어 그대로 따르고 인자는 `.scratch/admin-login/issues/04-refresh-and-signing-key-rotation.md`다. 다음 단계는 구현이고, 어디서는 새 세션(나란히 여는 2 중 1), 모델은 Sonnet 5.5 / high다. 읽을 것은 일지 `2026-11-26-1553-admin-login-ticket-03.md`의 "첫 봇 회차" 끝의 "뒤로 넘긴 일"과 "다음"이다. 만료된 짧은 JWT로 `/auth/logout`을 부르면 401이라 갱신용 번호가 서버에 남는 문제를 이 티켓이 정한다. 나란히 여는 05는 `.scratch/admin-login/issues/05-permission-table-and-accounts-on-runs.md`다. 주 체크아웃이 미갱신이라 `tidy-checkouts`를 먼저 돌고 `EnterWorktree`(name `04-refresh-and-signing-key-rotation`)로 들어가 브랜치를 바꾼다. 병합은 워크트리 `merge.md`의 "워크트리에서 병합할 때"를 따른다. 로컬 모델 시험은 재고가 없으면 시간을 두고 다시 치고 그때마다 사용자에게 비용 확인을 받는다. 이번 요청 범위는 PR과 병합까지다.

사용자의 정정이나 피드백은 없었다.

## 한 것(커밋 전, 작업 트리에만 있다)

- 순수 규칙: `src/agent_os/http/login_tokens.py`에 `REFRESH_GRACE`(10초), `RefreshRefusal`, `ENDS_LOGIN`, `judge_refresh`(여덟 갈래 가운데 앞 여섯의 판정 순서: 끊김, 쉼, 총 시간, 비활성, 잠김, 10초 지난 재사용). 시험은 `tests/test_login_tokens.py`의 "갱신의 판정" 절 아홉 건.
- 포트 `src/agent_os/http/accounts.py`: `RefreshRow`, `RecordKind`에 `refresh_reused`·`signing_key_rotated`, `AccountWork`에 `replace_signing_key`·`lock_refresh`·`find`·`use_refresh_token`·`touch_login` 다섯. 어댑터 `src/agent_os/adapters/postgres/accounts.py`가 같은 시그니처로 만족한다(`RefreshRecord`, 번호와 로그인 한 건을 `JOIN ... FOR UPDATE`로 함께 잠그고 계정은 잠그지 않는다. 계정을 잠그고 로그인 줄을 지우는 `_open`과 교착하지 않게 하려는 것이다).
- 서비스 `src/agent_os/http/logins.py`의 `LoginService.refresh(token, address=)`. 거절하는 갈래 가운데 끊는 것(비활성, 잠김, 재사용)은 예외가 아니라 정상 반환이라 트랜잭션이 커밋된다. 시각은 줄을 잠근 뒤에 주입된 시계에서 읽는다.
- 라우트 `src/agent_os/admin/auth.py`의 `POST /auth/refresh`(`refresh_login`). 거절은 `HTTPException`이 아니라 `error_envelope` 봉투를 직접 만들고 지우는 `Set-Cookie` 줄 둘을 얹는다. 401 문서에 `Set-Cookie` 머리를 적었다. `src/agent_os/http/auth.py`의 `PUBLIC_PATHS`가 넷이다.
- 서버 명령: `src/agent_os/channel/cli/operator.py`의 `rotate_key_command`와 `ROTATED_TEXT`, `src/agent_os/channel/cli/main.py`의 `RotateKeyArgs`와 `rotate-key` 하위 명령, `src/agent_os/main.py`의 `_rotate_key`와 `_on_database`(옛 `_system_admin_database`를 두 명령이 나눠 쓰도록 바꿨다).
- 시험: `tests/test_login_http.py`(갱신 절 아래 셋째 항목, 서명 키 바꾸기 연속 시험 포함 78건), `tests/test_rotate_key_command.py`(신규), `tests/adapters/test_postgres_accounts.py`(새 포트 메서드 넷), 대역 `tests/fake_accounts.py`·`tests/test_system_admin_command.py`의 `_RacingWork`에 새 메서드, `tests/test_server.py`(공개 경로 넷, `/auth/refresh`의 GET은 405).
- 계약: `openapi.json`(`uv run python tools/export_openapi.py`), `web/packages/api-client/src/generated/openapi.ts`(`pnpm -C web generate:api-client`), `web/packages/api-client/src/clients.test-d.ts`의 관리 경로 목록에 `/auth/refresh`.
- 문서: `.claude/rules/http.md`의 `PUBLIC_PATHS` 문장 둘(넷, 갱신은 쿠키 하나로 서비스가 판정하고 401은 지우는 줄 둘).
- 티켓 `Status`는 `in-progress`다. `done`으로 바꾸고 체크박스를 치는 일은 남았다.

## 판단과 결정

- 만료된 짧은 JWT로 `/auth/logout`을 부르면 401이라 갱신용 번호가 남는 문제(03 일지의 "뒤로 넘긴 일"): 명세가 이미 정했다. 화면이 갱신을 먼저 하고 그 다음 로그아웃을 부르며, 갱신이 거절되면 그 401이 쿠키를 지운다. 이 티켓이 서버 쪽에 더할 코드는 없다. 화면 규칙은 티켓 09가 짓는다.
- 갱신의 번호 판정은 `judge_refresh`가 하고 어댑터는 줄을 잠그고 읽고 적을 뿐이다(`.claude/rules/adapters.md`). 쉬는 시간과 총 시간의 비교는 `>=`다(경계에서 거절).
- 유예: 쓴 지 10초가 안 된 번호가 다시 오면 끊지 않고 새 번호를 하나 더 낸다. 이때 `use_refresh_token`은 처음 쓴 시각을 그대로 둔다(`used_at IS NULL`일 때만 적는다). 그래서 9초 뒤 재사용은 통과, 10초 뒤는 거절이다.
- 갱신의 401은 `WWW-Authenticate`를 싣지 않는다(로그인 401과 같은 이유: 이 경로는 `Authorization` 머리를 읽지 않는다).
- ADR은 쓰지 않았다. `PUBLIC_PATHS`가 넷으로 자란 것은 ADR 0011 2026-11-15 이력이 이미 셋(로그인, 갱신, 링크로 비밀번호 정하기)으로 예고했고 ADR 0062 결정 "자격"과 맞다. 이력을 더하려면 사용자 승인이 필요해 이 일지에 적기만 한다.

## 시험 중 고친 것

- `test_갱신으로_온_번호도_다음_로그인이_치울_때_로그인과_함께_사라진다`가 처음 빨갰다. 시험이 처음 번호만 거듭 써서 둘째 갱신이 "10초 지난 재사용"이 되어 로그인이 끊겼다. 시험을 새 번호를 이어 쓰게 고쳤다(구현은 맞았다).

## 검증 현황(이 세션이 직접 친 것)

- 통과: `uv run pytest -q tests/test_login_http.py`(78건), 그 앞 실행(`-x`로 첫 실패에서 멈춤)에서 `tests/test_login_tokens.py`·`tests/test_rotate_key_command.py`와 합쳐 142건 통과 뒤 위 시험 오류 1건에서 멈췄고, 고친 뒤 `tests/test_login_http.py` 78건이 모두 통과했다. `tests/test_system_admin_command.py`는 그 `-x` 실행이 멈추기 전에 닿지 못해 고친 뒤에 다시 돌리지 않았다. 아래 "안 돌린 것"에 넣는다, `uv run pyright`(0 errors), `uv run lint-imports`(9 kept), `uv run ruff format src tests`와 `uv run ruff check src tests`(import 순서 한 건을 `--fix`로 고친 뒤 통과), `uv run python tools/mutate.py --check .scratch/end-user-channel/probes/contract_mutations.toml`(변이 31 모두 원문 있음).
- 아직 안 돌린 것(새 세션이 한다): `tests/adapters/test_postgres_accounts.py`와 `tests/test_server.py`의 새 시험(쓰기만 하고 돌리지 않았다), 전체 러너 `uv run python tools/run_checks.py`(이 세션이 백그라운드로 띄웠으나 인계로 멈췄다), `pnpm -C web verify`와 `pnpm -C web/apps/admin exec playwright test`, `uv run --env-file ../../../.env pytest -m llm`, 로컬 모델 시험(`--yes` 없이 먼저 쳐 비용을 사용자에게 보이고 확인받은 뒤), 셀프 리뷰(`/code-review`, 방금 스킬을 불렀으나 인계로 넘겨 밟지 않았다), `tools/mutate.py`로 새 시험의 빨강 확인, retro, 티켓을 `done`으로, `uv run python tools/plan_table.py`, `uv run python tools/sibling_overlap.py`, 커밋, PR.

## 인계

경계 `셀프 리뷰 직전`(컨텍스트가 문턱을 넘음). 제목을 `<브랜치> (인계함)`으로 바꾸고, 백그라운드 러너를 멈추고, 워크트리 잠금을 푼다.

open-session을 부른다 2026-11-26T12:18Z
인계 못함 셀프 리뷰 직전: open-session의 열기 호출(pwsh tools/open_session.ps1 -Action send)을 자동 모드 판정기가 거절했다(사유 Unsanctioned Communication). 우회하지 않았다. 제목을 되돌렸다. 이 세션에서 셀프 리뷰부터 잇는다(위 "인계" 절의 지시문은 이 세션이 그대로 따른다). 백그라운드 전체 러너는 멈췄으므로 다시 띄운다.

## 셀프 리뷰(이 세션이 이어서 했다)

범위: 기준 `e0e6974258990e7df95a2029339fe6de0b63dfe3`, 수정 파일 20개, 커밋 0개, 미추적 2개. 표준 축과 명세 축 서브에이전트 둘 모두 Critical과 Major가 없었다.

고친 것(Minor 중 근거를 확인한 것):

- 줄 잠금 순서. `lock_refresh`가 번호와 로그인을 `JOIN ... FOR UPDATE`로 잡으면 번호 줄을 먼저 잡을 수 있어, 로그인 줄을 잡은 뒤 외래 키 CASCADE로 번호 줄을 잡는 `delete_ended_logins`와 순서가 엇갈려 교착할 수 있었다. 로그인 줄을 먼저 잠그고 번호 줄을 새 문장으로 읽도록 바꿨다(앞선 갱신이 커밋한 쓴 시각도 보인다). 포트 독스트링도 맞췄다.
- 총 시간이 1초 미만 남았을 때 성공 응답의 갱신 쿠키가 `Max-Age=0`이 되어 곧바로 지워졌다. 0 아래로 내려갔을 때만 0이고, 남아 있으면 최소 1초를 준다(`refresh_max_age`와 시험 하나).
- `refresh`의 입력 거르기(128자 초과, 비ASCII)에 시험이 없었다. 129자와 비ASCII 번호를 더했다.
- `parse_args`가 `rotate-key`가 아니면 무조건 `SystemAdminArgs`로 떨어졌다. `system-admin`을 명시하고 모르는 하위 명령은 오류로 바꿨다.
- `ROTATED_TEXT`의 둘째 문장이 "그 뒤로"로 모호했다. "10초가 지나면"으로 고쳤다. 명세의 문구는 그대로다.
- 문서: `logins.py` 모듈 독스트링에 갱신을 더했고, `.claude/rules/http.md`의 `WWW-Authenticate` 문장에 갱신 라우트를 더했다.

남긴 것과 이유(Nit 또는 판단 항목):

- 시험 하네스 복사(`test_system_admin_command.py`와 `test_rotate_key_command.py`의 `_run_plainly` 등). 두 파일의 하네스를 합치면 이 티켓 범위를 넘고 기존 파일을 크게 건드린다. 다음에 세 번째 명령이 오면 합친다.
- `find`·`use_refresh_token`·`touch_login` 이름과 `10초`를 글자로 적은 곳(`ROTATED_TEXT`, 도움말). 값이 바뀔 일이 없는 명세 고정 값이라 두었다.
- 대역 둘의 스텁 번짐. 포트에 메서드를 더하면 대역이 따라 늘어나는 것은 포트와 어댑터 구조의 대가다.
- 갱신 401 문구가 로그인과 같은 공유 문구인 것은 명세가 정한 보안 모양이다(이유를 알리지 않는다).

## 로컬 모델 시험의 비용 확인

`uv run --env-file ../../../.env python tools/llm_local.py run`을 `--yes` 없이 쳐 예상 비용을 받았다(Runpod 가격 페이지를 2026-11-13에 웹 요약에서 읽은 값, 원문과 대조하지 않음). 어림 30분이 약 $0.27~$0.59, 최악 90분이 $0.81~$1.77이고 재고가 없으면 다음 후보로 넘어간다. 그 뒤 사용자에게 물었다.

> 사용자(`AskUserQuestion` 답): 질문 "로컬 모델 시험을 돌릴까요? … 가격은 2026-11-13에 웹 요약에서 읽은 값이라 원문과 대조하지 않았습니다." 답 "돌린다 (Recommended)"(설명: "--yes를 붙여 실행합니다. 이 티켓 파일의 검증 항목이 요구하는 시험입니다.").

그래서 `--yes`를 붙여 돌렸다. 결과: GPU 후보 넷(RTX A5000 파드 둘, RTX 3090 파드 둘, A40 파드 둘, A40 shared 하나)이 모두 "There are no longer any instances available"(HTTP 400)로 파드를 만들지 못했다. 종료 코드 2, 무효 회차 1번(회차 파일 `round-0001-20261126T130116Z.json`). 끝난 뒤 Runpod의 파드 목록이 비어 있는 것을 읽어 남은 파드와 비용이 없음을 확인했다.

> 사용자(`AskUserQuestion` 답, 둘째): 질문 "로컬 모델 시험을 다시 시도할까요? … 비용 예상은 이전과 같습니다. 어림 30분이면 약 $0.27~$0.59, 가장 오래 걸리는 경우(타이머 90분)에도 $0.81~$1.77입니다(가격은 2026-11-13에 웹 요약에서 읽은 값이고 원문과 대조하지 않았습니다)." 답 "지금 다시 친다 (Recommended)"(설명: "--yes를 붙여 한 번 더 시도합니다. 재고가 없으면 또 비용 없이 끝납니다.").

## 검증 결과(리뷰 반영 뒤)

- `uv run python tools/run_checks.py` 모두 통과(check-ticket, check-notes, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 644초, web-verify 785초). ruff는 러너 밖이라 `uv run ruff check .`와 `uv run ruff format --check .`를 따로 쳐 통과했다(마지막 고침 뒤에는 `src`와 `tests`에 다시 쳐 통과).
- `uv run pytest -q tests/adapters/test_postgres_accounts.py tests/test_server.py tests/test_system_admin_command.py tests/test_rotate_key_command.py` 309건 통과. 리뷰 반영 뒤 `tests/test_login_http.py`·`tests/test_login_tokens.py`와 함께 230건 통과.
- 관리 화면 e2e `pnpm -C web/apps/admin exec playwright test`: 11건 가운데 `decision.e2e.ts`의 "멈춘 실행을 승인하면 …" 한 건이 첫 판에 5초 기한에 닿아 빨갰고(이벤트 구역에 `run_finished`가 아직 없었다), 그 파일만 다시 치자 셋 모두 통과했다. 이 변경과 닿는 곳이 아니고 같은 시험이 두 번 연속 빨갛지 않아 진단 절차는 걸지 않았다. 원인은 재지 않았다(부하와 겹친 일시적 지연이라는 것은 어림이다).
- `uv run --env-file ../../../.env pytest -m llm -q` 24건 통과, 토큰 272,696(입력 267,397, 출력 5,299).
- 카나리아: 알림이 가리킨 명세 셋(`http_rule_continuation_422`, `http_rule_pre_owner_damage`, `http_rule_llm_widget`)을 새 `claude -p` 세션(2.1.325)으로 실제로 돌려 모두 통과 4, 실패 0, "없음" 섞임 0이다(커밋하기 전의 작업 트리, 커밋 `e0e697425` 위). 이 PR 안에서 처음 도는 것이라 사전 확인으로 갈음하지 않았다. 세 명세의 `# 최신 결과:` 줄을 고쳤다.
- 로컬 모델 시험: 두 번 시도했고 둘 다 GPU 후보 넷이 재고 없음(HTTP 400)으로 무효 회차다(연달은 무효 2번, 러너가 멈추고 사용자에게 보고하라고 했다). 파드가 하나도 뜨지 않았고 Runpod 파드 목록이 비어 있어 비용은 들지 않았다. 병합 조건이라 이 시험이 통과하기 전에는 병합하지 않는다.

## 이어받을 일

셀프 리뷰와 위 검증은 끝났다. 남은 것은 로컬 모델 시험(재고가 풀리면 `--yes` 없이 쳐 비용을 사용자에게 다시 보이고 확인받은 뒤 `--yes`)과, 통과한 뒤 티켓을 `done`으로 바꾸고 마지막 체크박스를 치는 일이다. 05(`permission-table-and-accounts-on-runs`)와 나란히 돈다. 늦게 병합하는 쪽이 권한 표(05가 짓는다)에 `refresh_login`(로그인 없이 연다) 줄을 더한다. 병합 전에 `origin/dev`에 05가 들어왔는지 보고, 들어왔으면 합친 뒤 05의 전수 검사가 초록인지 본다. `openapi.json`과 생성 TS는 손으로 합치지 말고 다시 뽑는다. 05가 같은 파일(`.claude/rules/http.md`, `src/agent_os/admin/auth.py`, `src/agent_os/http/auth.py`)을 고치므로 글자 충돌이 날 수 있다.
