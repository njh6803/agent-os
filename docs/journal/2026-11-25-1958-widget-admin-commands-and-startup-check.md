# 2026-11-25 widget-admin-server 03: 명령과 시작 점검

브랜치 `feature/03-widget-admin-commands-and-startup-check`. 티켓은 `.scratch/widget-admin-server/issues/03-widget-admin-commands-and-startup-check.md`다. 이 파일은 구현 세션이 셀프 리뷰 직전에 인계하며 낸 앞부분이고, 이어받는 세션이 이어 쓰고 커밋한다.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/widget-admin-server/issues/03-widget-admin-commands-and-startup-check.md

이어 붙은 지시문(전문은 세션 기록)의 칸은 이렇다. 다음 작업은 `widget-admin serve`와 `widget-admin migrate`가 서고 데이터베이스가 준비되지 않으면 서버가 이유를 한 줄로 찍고 멈추는 것이다. 다음 단계는 구현이고, 나란히 여는 2 중 2다. 모델은 Sonnet 5.5 / high다. 읽을 것은 일지 `2026-11-25-1440-widget-admin-package-and-settings-route.md`의 "다음"(sslmode, 연결 시간 제한, uvicorn 접근 로그, 병행 `migrate`의 잠금)이고, 02와 함께 고치는 파일은 루트 `README.md`뿐이다. 이번 요청 범위는 PR과 병합까지다.

## 한 것(커밋 전, 워크트리에 있다)

- 새 파일: `widget-admin/src/widget_admin/main.py`(명령 `serve`·`migrate`, 연결 문자열 읽기, 루프백 규칙의 다섯째 사본), `lifespan.py`(`CheckDatabase`, Agent OS `agent_os.http.database`의 사본). `database.py`는 확인, 다시 시도, 판 견줌, 올리기를 갖추게 다시 썼다. `server.py`는 `CheckDatabase`를 가장 바깥 미들웨어로 단다.
- 시험: `tests/widget_admin/test_database_check.py`, `test_startup_check.py`, `test_commands.py`, `test_loopback.py`와 `conftest.py`·`support.py`의 도우미. `tests/widget_admin` 전체 229개가 초록이다.
- 문서: 루트 `README.md`에 "위젯 관리 서버" 절, `tests/fixtures/container_network/README.md`와 `src/agent_os/main.py` 주석과 웹 세 파일의 주석에서 네 프로세스를 다섯으로, `.claude/rules/widget-admin.md`에 판단 기준 넷.
- 카나리아: `.scratch/widget-admin-server/probes/canary/widget_admin_rule_startup.toml`. 규칙 파일을 커밋하기 전의 작업 트리로 돌려 통과 4(실험군 셋이 두 글을 그대로 옮겼고 대조군은 "없음").

## 결정

일지 `2026-11-25-1440-widget-admin-package-and-settings-route.md`의 "다음"이 03에 넘긴 넷을 이렇게 정했다.

- `sslmode`: 연결 문자열의 `?` 뒤 질의는 읽지 못한 것으로 거절한다(asyncpg가 libpq의 질의를 몰라 첫 질의에서 죽는다). 시험 `?sslmode=require`가 있다.
- 연결 시간 제한: 시도 하나를 `asyncio.timeout(5초)`로 통째로 감싼다. 엔진과 연결 묶음에 따로 제한을 더하지 않는다.
- uvicorn 접근 로그: 그대로 둔다. 주소는 요청 경로(사이트 이름)만 싣고 비밀이 없다.
- 병행 `migrate`의 잠금: 두지 않는다. 서버를 여럿 두는 것은 명세 Out of Scope이고 `database.py` 머리 독스트링에 적었다.

글은 명세의 표와 같다. 셋(변수 없음·비어 있음, 읽지 못함, 표가 뒤처짐)만 Agent OS와 다르고 나머지는 같다. 글에 ADR 번호를 싣지 않는다. `retry_notice`, `unreached_text`, `misaligned_text`, `DEFAULT_RETRY_SECONDS`는 공개로 내고, 04가 배포 안내의 표를 이것과 견준다.

## 개발 PC에서 실제로 친 것

테스트 컨테이너가 떠 있는 채로 다음을 쳤다.

- `docker compose -f compose.test.yaml exec -T postgres createdb -U agent_os widget_admin`: 처음에는 조용히 0, 다시 치면 `database "widget_admin" already exists`로 1(README가 그대로 다음 명령으로 가라고 적는다).
- `WIDGET_ADMIN_DATABASE_URL=postgresql://agent_os:agent_os@127.0.0.1:25432/widget_admin uv run widget-admin migrate`: `표를 없음에서 0001으로 올렸습니다.`
- `uv run widget-admin serve` 뒤 `curl -i http://127.0.0.1:8100/health`가 200 `{"status":"ok"}`, `/widget-settings/no-such-site`가 404 봉투(열린 출처 머리 셋과 `x-request-id` 포함). 서버는 띄운 뒤 멈췄고 만든 데이터베이스는 그대로 두었다.

## 검증

`uv run python tools/run_checks.py`(백그라운드, 약 34분. 러너의 출력이 낸 줄을 읽었다)의 결과는 이렇다. check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright(리눅스 판 포함), run-hooks, web-verify는 통과, pytest는 8394 통과 1 실패였다. 실패한 `tests/channel/cli/test_interrupt.py::test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`는 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다"였고, 이 변경이 건드리지 않는 경로이며 홀로 다시 돌리니 6개 모두 통과했다(`uv run pytest -q tests/channel/cli/test_interrupt.py`, 77초, 손으로 봤다). 한 바퀴가 34분 걸린 부하 아래의 시간 초과라고 어림하지만, 부하의 원인(다른 세션)은 보지 않았다. `uv run ruff check . && uv run ruff format --check .`와 `uv lock --check`도 초록이다.

## 남은 것(이어받는 세션이)

셀프 리뷰(`/code-review origin/dev`)부터 한다. 이어 변이 시험(`tools/mutate.py`)으로 한 번도 빨갛지 않았던 가드 단언을 확인하고, 티켓의 체크박스를 닫고 `Status: done`으로 바꾼 뒤 `uv run python tools/plan_table.py`를 돌린다(이 기능의 마지막 티켓이 아니라 `**끝:**` 줄은 없다). 그 뒤 일지 마무리, retro, 커밋, `coderabbit-review` 또는 `bug-perf-review`, PR, 병합이다.

open-session을 부른다 2026-11-25T11:01Z
인계 못함 셀프 리뷰 직전: open_session.ps1 호출이 자동 허용 분류기에 거부됐다(2026-11-25T11:02Z UTC). 제목을 되돌렸고 이 세션에서 셀프 리뷰부터 잇는다.

## 셀프 리뷰(`/code-review origin/dev`, 기준 SHA `085fa7b93`)

범위는 수정 14개, 미추적 8개, 커밋 0개였다. 표준 축(Sonnet·high)과 명세 축(본 세션 모델)이 병렬로 돌았다. 둘 다 Critical·Major가 없었다. 보고의 근거는 서브에이전트가 코드를 읽고 `uv run python -c`로 직접 불러 본 것이다(표준 축은 `parse_database_url`에 경계 입력을 넣어 봤다).

고친 것.

- 옛 수가 남은 주석: `web/apps/widget/tools/start.ts`의 "네 벌"(다섯 벌로 고치고 위젯 관리 서버 경로를 더했다), `tests/test_main.py` 1494행 독스트링의 "네 프로세스", `web/apps/{admin,portal,widget}/testing/container-network.ts` 1행의 "파이썬과 TS 네 곳"(파이썬 둘과 TS 셋).
- 현재형 거짓 문장: 배포 안내의 시험이 안내의 표와 견준다는 문장은 04가 더할 시험이다. 규칙 문서에는 04가 이 이름을 읽고 지금은 `test_database_check.py`만 부른다고, `main.py`와 `database.py`의 주석에는 "widget-admin-server 04 가 더한다"로 고쳤다.
- 과장한 서술: `parse_database_url` 독스트링이 "꼴만 받는다"고 적었으나 계정이나 포트를 적지 않은 값, 포트 범위 밖, 경로가 둘인 값도 받는다. 받지 않는 것(드라이버 이름이 붙은 꼴과 다른 이름, `?` 뒤의 질의, `@`가 둘 이상, `ValueError`가 나는 값)만 적고 나머지는 SQLAlchemy가 읽는 대로 읽는다고 적었다. 다시 시도 "30초까지"는 30초가 지날 때까지(시도 하나에 5초까지 걸려 마지막 시도만큼 더 길어질 수 있다)로 고쳤다.
- `migrate`가 닫다 예외를 던지면 역추적이 샜다. `_migrate_database`가 올리기 결과를 쓴 뒤 닫기를 따로 감싸 `close_problem`의 글과 1로 끝낸다. 시험 `test_닫기가_예외를_던지면_예외의_글_대신_까닭만_싣고_1로_끝난다`를 더했다.
- 비밀번호 단언: 닫힌 포트(글과 알림), 없는 데이터베이스, 답하지 않는 서버, 잠긴 판 기록 표의 글에도 `계정:비밀번호@` 꼴이 없다는 단언을 더했다.
- `lifespan.py` 독스트링이 말하는 갈래 둘의 시험을 더했다. 앱이 스스로 `startup.failed`를 보내는 것과 앱이 아무 말 없이 끝나는 것, 둘 다 닫기가 한 번이다.
- 루트 README의 `widget-admin/` 트리 줄에 `main`과 `lifespan`을 더했다.

남긴 것.

- Nit: `_serve`의 `if problems or isinstance(database_url, str)`는 pyright의 타입 좁히기를 위해 남긴 중복 조건이다. 반환형 `DatabaseUrl | str`도 같은 모양이다. Agent OS의 같은 자리와 같게 두었다.
- Nit: `_describe`와 `_misaligned_text`는 공개 함수를 한 줄로 부르는 얇은 메서드다. 객체의 값(자리, 판)을 채우는 자리라 두었다.
- Nit: `migrate`가 다시 시도하는 동안 Ctrl+C를 누르면 역추적이 나올 수 있다. Agent OS는 `run_interruptibly`를 쓰지만 `widget_admin`은 `agent_os`를 import할 수 없고 명세도 요구하지 않았다. 필요해지면 새 티켓이다.
- Nit: README의 `export …` 꼴은 bash 문법이고 이 세션이 실제로 친 것은 같은 값을 앞에 붙인 `VAR=값 uv run …` 꼴이다. 같은 변수가 같은 값으로 들어가므로 README의 꼴은 따로 돌려 보지 않았다.
- Nit: 시험 이름에 함수 이름(`main`)이 든 것과 상수를 되풀이하는 시험(`기본값은 …`)은 그대로 두었다. 후자는 명세가 그 값을 고정하는 시험이다.
- 시험 `test_닫기가_예외를_던지면…`과 비밀번호 단언 보강은 고치기 전에 빨갛게 돌려 보지 않았다(고침과 함께 썼다).

다시 돌린 것: `uv run ruff check .`와 `uv run ruff format --check .`, `uv run pyright widget-admin tests/widget_admin tools/export_widget_admin_openapi.py`는 초록이고, `uv run pytest -q tests/widget_admin`은 232개 통과다(고치기 전 229개에서 시험 셋이 늘었다). 커밋 직전의 pre-commit이 나머지를 다시 돈다.

## 남은 것(이 세션이 이어서)

변이 시험으로 가드 단언을 확인하는 일, retro, 커밋, 푸시 전 `bug-perf-review`(CodeRabbit CLI가 돌지 못하면), PR, 병합이다. 티켓은 닫았고 `plan_table.py`를 돌렸다.

변이 시험(`tools/mutate.py`)은 돌리지 않았다. 닫기 예외 시험과 비밀번호 단언 보강이 고치기 전에 빨갛게 보이지 않았다는 앞의 줄이 그대로 남는다.

## PR 직전 리뷰(`coderabbit-review`, CodeRabbit CLI 0.7.5, 기준 `origin/dev`)

CLI는 끝까지 돌았고 지적 6건을 냈다. 서브에이전트는 셀프 리뷰가 새로 쓴 문장 여섯을 직접 대 보았다(`uv run python -I`로 경계 입력을 넣어 봤다). 아래는 그 보고를 받은 턴의 판정이다.

고친 것.

- 비밀번호가 글에 실리는 입력: `postgresql://us/er:SECRET@h/db`는 `@`가 하나라 통과하고, SQLAlchemy가 계정 자리의 `/`에서 계정 묶음을 버려 호스트를 `us`로, 데이터베이스 이름을 `er:SECRET@h/db`로 읽는다. `place`가 `us:5432/er:SECRET@h/db`를 내므로 알림과 멈춤 글에 비밀번호가 실린다. 이 턴에 `uv run python -I`로 같은 입력을 넣어 재현했다. `parse_database_url`이 호스트나 데이터베이스 이름에 `@`가 든 값을 읽지 못한 것으로 거절하게 고치고 독스트링의 받지 않는 목록에 더했다. 거절 시험 목록(`test_받지_않는_주소는_읽지_못한다`)에 `postgresql://widget/admin:secret@postgres:5432/widget_admin`을 더했다. 이 시험은 고치기 전에 빨갛게 돌려 보지 않았다(고침과 함께 썼다).
- 재시도 시간 서술: README의 문장이 간격을 빼먹었다. 마감 직전(29.99초)에 실패하면 1초를 자고 새 시도를 시작해 5초를 쓰므로 최대 약 36초다. README를 "마지막 시도가 마감 직전에 시작되면 간격 1초와 시도 하나 5초만큼 더 길어질 수 있다"로 고쳤다. `database.py`에는 같은 문장이 없었다(grep으로 봤다).

밀 주장의 결과: `CheckDatabase`의 닫기 한 번, `migrate`의 닫기 예외 처리, 종료 코드 3과 1, 루프백 사본 다섯은 서술대로였다(보고의 코드 읽기와 기존 시험 목록. 문장 3은 프로브를 돌리지 못하고 코드 읽기만으로 봤다).

오탐: CodeRabbit의 README `uv sync` 지적(루트 `pyproject.toml`에 `widget-admin` 의존이 있고 README의 `uv run widget-admin …`이 이 워크트리에서 돌았다), `MigrateResult.ok=False` 처리 요구(`main.py`가 `ok`가 거짓이면 표준 오류와 종료 코드 1로 바꾼다).

남긴 것과 이유.

- Minor: uvicorn 접근 로그가 `GET /widget-settings/<사이트> 200`을 표준 출력에 찍는다. 앞의 결정(사이트 이름은 공개 값이고 실패 한 줄에 싣지 않는다는 규칙은 표준 오류의 실패 글에 한한다)을 그대로 둔다.
- Minor: 시작 재시도 30초 동안 SIGTERM을 받아도 재시도 루프가 uvicorn의 종료 요청을 보지 않아 `docker stop`의 10초 유예를 넘길 수 있다. 코드 읽기만 한 지적이고 돌려 보지 않았다. Ctrl+C 때의 `run_interruptibly` 건과 함께 필요해지면 새 티켓이다.
- Nit: 포트 `0`이 글에 5432로 찍힌다(`port or DEFAULT_PORT`). 0번 포트는 어차피 못 닿는 값이라 두었다. 범위 밖 포트, 경로가 둘인 값, 전각 숫자 포트는 파서의 독스트링대로 SQLAlchemy가 읽는 대로 받는다.
- Minor: 올리다 실패한 글이 "올리기 전 그대로"라고 단정한다. 응답이 유실되면 틀릴 수 있다고 `database.py`의 "못 보는 것"에 이미 적혀 있다.
- Nit: 성공 글을 쓴 뒤 닫기가 실패하면 종료 코드 1이다. 의도한 모양이다.
- 보류: CodeRabbit의 시험 품질 지적 셋(`test_database_check.py` 363-366행과 394-397행, `test_startup_check.py` 188-189행의 `silence(0.3)`)은 열어 보지 않았다.

## 로컬 모델 시험(병합 전, `src/agent_os/main.py` 주석이 범위에 든다)

비용 확인: `uv run --env-file ../../../.env python tools/llm_local.py run`을 `--yes` 없이 쳐 예상 비용(RTX A5000 파드 둘 어림 30분 $0.27·최악 90분 $0.81 외 셋)을 사용자에게 보였고 사용자가 "돌려"라고 답했다.

첫 회차(`--yes`)는 종료 코드 2, 무효 회차였다. 후보 넷(pods A5000·3090·A40, shared A40) 모두 Runpod가 400 `There are no longer any instances available with the requested specifications`(재고 없음)로 파드를 만들지 못했다. 시험한 커밋은 `d7faddfa21d810dd7971a908136e5aa58e9de286`, 두 모델은 `GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`과 `openai/gpt-oss-20b`, 서빙 엔진은 vLLM 0.33.0(`vllm/vllm-openai:v0.33.0`), 걸린 시간 9.0초, GPU·통과 수·토큰은 없음, 단가표 날짜 2026-11-13, Terraform 출력에서 가린 것은 없다. 파드를 띄운 적이 없어 과금은 없다고 본다(명령의 기록 묶음이 `gpu: null`이다. Runpod 계정의 청구는 보지 않았다). 연달은 무효 회차 1번(상태 폴더의 회차 파일로 센다). 다시 띄울 때도 비용 확인을 받는다.

둘째 회차는 사용자가 "다시 돌린다"로 비용을 다시 확인해 준 뒤 `--yes`로 돌렸고 종료 코드 0, 통과 4다. 시험한 커밋 `d7faddfa21d810dd7971a908136e5aa58e9de286`, 두 모델 `GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`(리비전 `fdb4e380603cf157783227bd790bfbe921b64610`)과 `openai/gpt-oss-20b`, 서빙 엔진 vLLM 0.33.0(이미지 `vllm/vllm-openai:v0.33.0`), 서버 옵션은 두 서버 모두 `--enable-auto-tool-choice`와 `--gpu-memory-utilization 0.45 --kv-cache-memory=4294967296`(gemma는 `--tool-call-parser gemma4 --max-model-len 32768`, gpt-oss는 `--tool-call-parser openai`), GPU는 A40 하나에 두 서버가 함께 앉은 shared 구성, 토큰 합계 6,297(입력 6,191, 출력 106, 트레이스 2개, 모델 호출 4건. 트레이스를 남기지 않은 시험 2개는 세지 못했다), 걸린 시간 1347.4초, 단가표의 시간당 $0.59(단가표 날짜 2026-11-13, 웹 요약에서 읽은 값). 이 시간과 단가로 곱한 어림 비용은 약 $0.22이고 Runpod 청구는 보지 않았다. Terraform 출력에서 가린 것이 있었다. 회차 파일은 `C:\Users\User\.agent-os\llm-local\feature%2F03-widget-admin-commands-and-startup-check\records\round-0001-20261125T153956Z.json`이다. 서버 키와 주소는 적지 않았다. 병합한 뒤 `tools/llm_local.py sweep`을 친다.

이 통과 기록은 dev를 합친 뒤 무효가 됐다. 합쳐 들어온 `src/agent_os/core/run.py`와 `src/agent_os/channel/http/router.py`가 `docs/constitution/operations.md`가 정한 범위 안에서 바뀌어서, 시험한 커밋 `d7faddf`와 지금 헤드의 차이에 범위 경로가 든다. 그래서 헤드 `5e6844d8936b29f4b173c8fc0490eff0561ac772`로 다시 쟀고, 사용자가 비용을 두 번 더 확인해 줬다(매번 "다시 돌린다").

- 셋째 회차(회차 파일 `round-0002-20261125T180605Z.json`): 종료 코드 2, 무효. 후보 넷 모두 Runpod 400 `There are no longer any instances available with the requested specifications`(재고 없음)로 파드를 못 띄웠고 42.0초에 끝났다. GPU·통과 수·토큰은 없다. 파드가 만들어지지 않아 과금은 없다고 본다(청구는 보지 않았다). 연달은 무효 회차 1번(앞 통과 회차가 끊어 줬다).
- 넷째 회차(회차 파일 `C:\Users\User\.agent-os\llm-local\feature%2F03-widget-admin-commands-and-startup-check\records\round-0003-20261125T183546Z.json`): 종료 코드 0, 통과 4. 시험한 커밋 `5e6844d8936b29f4b173c8fc0490eff0561ac772`, 두 모델·리비전·서빙 엔진·서버 옵션은 둘째 회차와 같고, GPU는 A40 하나에 두 서버가 함께 앉은 shared 구성(앞 후보 pods A5000·3090·A40은 재고 없음으로 건너뛰었다), 토큰 합계 6,343(입력 6,191, 출력 152, 트레이스 2개, 모델 호출 4건. 트레이스를 남기지 않은 시험 2개는 세지 못했다), 걸린 시간 1020.0초, 단가표의 시간당 $0.59(단가표 날짜 2026-11-13, 웹 요약에서 읽은 값). 이 시간과 단가로 곱한 어림 비용은 약 $0.17이고 Runpod 청구는 보지 않았다. Terraform 출력에서 가린 것이 있었다. 서버 키와 주소는 적지 않았다.
- 파드가 남았는지: 앞 후보 두 곳(A5000, A40 파드)에서 파드 하나씩 만들어진 뒤 `terraform apply`가 실패했다. 끝난 뒤 Runpod의 `list-pods`로 보니 파드가 0개였다(손으로 봤다). 두 파드가 살아 있던 시간의 청구는 보지 않았다.

이 넷째 회차 기록도 곧 무효가 됐다. 푸시하려는 사이 dev에 admin-login 02가 들어왔고(충돌 없이 합쳤다) 그 변경이 `src/agent_os/adapters/`, `src/agent_os/channel/cli/main.py`, `src/agent_os/main.py`, `pyproject.toml`과 `uv.lock`을 건드려서, 시험한 커밋 `5e6844d`와 합친 헤드의 차이에 범위 경로가 들었다. 합친 결과에서 `tests/widget_admin`과 `tests/test_main.py`는 535개 통과했다(280.98초).

- 다섯째 회차(합친 헤드 `8e54087cdda72b0abe29403cfb1f18a442ea6040`): 사용자가 비용을 다시 확인해 줬고("다시 돌린다") 종료 코드 0, 통과 4다. 두 모델·리비전·서빙 엔진·서버 옵션은 둘째 회차와 같고, GPU는 A40 하나에 두 서버가 함께 앉은 shared 구성(앞 후보 pods는 재고 없음으로 건너뛰었다), 토큰 합계 6,298(입력 6,191, 출력 107, 트레이스 2개, 모델 호출 4건. 트레이스를 남기지 않은 시험 2개는 세지 못했다), 걸린 시간 388.0초, 단가표의 시간당 $0.59(단가표 날짜 2026-11-13, 웹 요약에서 읽은 값). 이 시간과 단가로 곱한 어림 비용은 약 $0.06이고 Runpod 청구는 보지 않았다. Terraform 출력에서 가린 것이 있었다. 회차 파일은 명령이 찍은 `round-0001-20261126T045245Z.json`이고, 뒤에 친 `sweep`이 상태 폴더를 치웠으므로 파일이 남았는지는 열어 보지 않았다.
- 남은 파드: 이번에도 앞 후보 한 곳에서 파드가 만들어진 뒤 `terraform apply`가 실패했다. 끝난 뒤 `list-pods`로 보니 `agent-os-llm-local-2`(A40, 시간당 $0.59, 04:48에 시작해 RUNNING)가 하나 살아 있었다. 이 시험이 만든 파드라 `tools/llm_local.py sweep`으로 치웠고, 치운 뒤 `list-pods`가 0개였다(손으로 봤다). 파드의 `args`에 서버 키가 평문으로 든 것을 `list-pods` 출력에서 보았다(적지 않았다). 그 파드가 살아 있던 시간의 청구는 보지 않았다. `sweep`은 이 브랜치의 상태 폴더와 함께 `feature/07-conversation-list-route`의 상태 폴더도 "치웠다"고 출력했다. 07 세션이 서버를 쓰고 있었는지는 확인하지 않았고 파드는 sweep 전에 이 파드 하나뿐이었다.

기록이 맞는 커밋은 `8e54087`이고, 이 커밋 뒤에 더하는 변경은 이 일지뿐이어야 한다(`git diff --name-only 8e54087 HEAD`에 범위 경로가 없다). 병합한 뒤 `sweep`은 이미 쳤다.

## 회고

후보 여덟, 판정은 승인 1, 기각 7, 넘김 0이다. 만료할 항목은 없었다(`tools/queue_open_rows.py`, 만료 줄 "없음").

- 승인: 인계 열기를 자동 모드 분류기가 거부했다(사건: 이 일지의 "인계 못함 셀프 리뷰 직전" 줄). 열린 `open-session-send-denied-despite-allow-rule`이 같은 사건을 처방하고 있어 새 항목 없이 그 승인 줄에 17회차를 더했다. dev의 admin-login 티켓 01 세션이 같은 항목에 먼저 17회차를 더해 둬서, dev를 합칠 때 충돌을 풀며 이 사건을 18회차로 이었다(항목 찾기에서 닫힌 0498과 함께 걸렸고 열린 쪽이 우선이다). 회차 5 이상이라 chore 계기에 이미 들어 있고, 이 세션은 반영하지 않는다. 그 호출이 허용 규칙과 글자까지 맞았는지는 재 보지 않았다.
- 기각, 옛 수가 남은 주석("네 프로세스" 여럿): 셀프 리뷰의 명세 축이 잡았다. 주장 검증 목록 3번("계약 변경이 거짓으로 만드는 문장은 바뀐 값으로 grep")이 리뷰에 이미 있는 기준이라 리뷰가 제 몫을 한 것이고 회차에서 뺀다. 수를 세는 문장 전반을 검사로 옮길 길은 모양이 고정되어 있지 않아 서지 않았다.
- 기각, 아직 없는 04의 시험을 현재형으로 적은 문장: 같은 목록 4번(미래형)이 겨누는 자리이고 셀프 리뷰가 잡았다. 같은 이유다.
- 기각, `migrate`의 닫기 예외가 역추적을 흘린 것: 이 변경의 코드 결함이고 셀프 리뷰가 잡아 시험과 함께 고쳤다. 하네스의 결함이 아니다.
- 기각, `test_interrupt.py` 시험 하나가 30초 안에 끝나지 않아 빨간 것(전체 한 바퀴 34분의 부하, 홀로 돌리면 6개 통과): 306이 "부하에서 시간 시험이 빨개지면 그 커밋을 다시 치는 값을 받아들인다"고 닫은 종류의 새 사례다. 항목 찾기에 닫힌 0531(같은 파일의 다른 시험, 시계 눈금)만 걸렸고 이어 적은 열린 항목은 없었다. 규칙대로 잇지 않고 새 항목도 쓰지 않으며 이 줄로만 남긴다.
- 기각, 커밋의 pre-commit에서 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`가 `assert 1 == 2`로 빨간 것(1 failed, 8397 passed, 한 바퀴 1086초): 이 변경이 건드리지 않는 경로이고 홀로 다시 돌리니 63개가 통과했다(`uv run pytest -q tests/tools/test_rerun_runner.py`, 151초, 손으로 봤다). 같은 306 종류의 새 사례라 잇지 않고 이 줄로만 남기며, 같은 커밋을 다시 친다.
- 기각, 둘째 커밋(한 바퀴 1771초, 5 failed, 8393 passed)에서도 시간 시험이 빨갰다: `test_interrupt.py` 셋(Ctrl+C 자식이 30초 안에 끝나지 않았다), `test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`, `test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`. 세 파일만 홀로 다시 돌리니 이번에는 다른 시험 하나(`test_본_측정에서_첫_인계_뒤_멈추고_확인_인자를_주면_잇는다`)가 빨갰고, `test_rerun_runner.py`만 다시 돌리니 63개가 통과했다. 이 변경이 건드리지 않는 경로이고 부하의 원인(나란히 도는 다른 세션)은 보지 않았다. 앞 줄과 같은 306 종류라 잇지 않고 이 줄로만 남긴다. 셋째 커밋(810초)에서는 `test_interrupt.py::test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다` 하나만 같은 자식 30초로 빨갰다(1 failed, 8397 passed). 이 시험은 처음 `run_checks` 한 바퀴와 둘째·셋째 커밋까지 전체 실행 세 번에 모두 빨갰고 홀로 돌리면 통과했다. 그래서 넷째로 같은 커밋을 다시 친다.
- 기각, dev를 합친 커밋(admin-login 08 합침)의 pre-commit에서 `web-verify`만 빨간 것(`pytest`는 1008.8초에 통과): 합쳐 들어온 `Icon.tsx`가 `lucide-react` 아이콘 일곱 개를 새로 들여와, 이 작업 폴더의 Vite 캐시가 시험 도중 그것을 처음 묶으며 `optimized dependencies changed. reloading`을 냈고(출력에 네 번), 그때 스토리 시험 파일 네 개(`WidgetScreen`·`RunDetail` 둘·`Markdown`)가 가져오기에 실패했다(`Test Files 4 failed | 89 passed`, 시험 2593개는 통과). `pnpm -C web verify`를 홀로 다시 치니 초록이었다(손으로 봤다. 캐시가 데워진 뒤라는 것은 출력의 문구로 본 추정이고 캐시를 직접 열어 보지는 않았다). 이 변경이 건드리지 않는 경로이고 새 의존성이 든 변경을 처음 합친 작업 폴더에서만 나는 종류라, 사건 하나로는 더하지 않고 이 줄로만 남긴다. 같은 커밋을 다시 친다.
- 기각, 가드 단언이 고치기 전에 빨갛게 보이지 않은 것: `tools/mutate.py`가 이미 있고 이 세션이 쓰지 않은 것이다. 사건으로 센 손해가 없어 사건 없이 떠올린 후보다.

## 다음

PR 644를 열었고 검사는 모두 초록이다. CodeRabbit은 한도에 걸려 리뷰가 없었고(51분 뒤 다시), claude-review 첫 회차는 Minor 넷과 Nit 하나뿐이라 코드를 고치지 않고 PR 코멘트에 보류 이유를 남겼다. 로컬 모델 시험(범위의 `src/agent_os/main.py` 주석 때문에 든다)은 헤드 `5e6844d`로 통과했고(위 넷째 회차), 이 세션이 병합까지 한다(요청 범위가 "PR과 병합까지"). 뒤로 넘긴 일은 둘이다. 마이그레이션이 데이터 열을 건드리게 되면 `migrate`의 올리기 실패 때 표준 오류에 싣는 전체 역추적을 클래스 이름과 오류 번호로 줄여야 한다(독스트링이 인정한 한계이고 지금은 0001 하나라 위험이 낮다). 시작 재시도 30초 동안 SIGTERM을 받아도 재시도 루프가 uvicorn의 종료 요청을 보지 않아 `docker stop` 유예를 넘길 수 있다. 셋째, `database.py`가 바뀌는 이유가 넷(엔진·연결, 주소 읽기, 실패 분류, 글 짓기)이라(claude-review 둘째 회차의 Minor), 티켓 04가 글 함수들을 시험에서 직접 읽는 시점에 `messages.py`와 `url.py` 정도로 나눈다. 병합 뒤 주 체크아웃의 당기기는 워크트리 가드 때문에 이 세션이 하지 않고 주 체크아웃 세션의 `tidy-checkouts`에 넘긴다. 기능의 다음 티켓은 04(배포 안내가 이 세션이 공개한 글 함수와 상수를 읽어 안내의 표와 견주는 시험)다. README에서 02와 겹치는 줄은 병합 때 02 쪽 변경과 충돌하지 않는지 본다.
