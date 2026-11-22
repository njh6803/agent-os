# 2026-11-22 (13:35) connection-check 티켓 01 계약

브랜치 `feature/01-contract-connection-check-routes-and-port-methods`, 워크트리 `.claude/worktrees/01-contract-connection-check-routes-and-port-methods`. 모델 Sonnet 5.5(지시문의 high). 기준은 `origin/dev`이고 앞 일지 `2026-11-22-0159-connection-check-tickets.md`의 "다음"이 가리킨 티켓 01을 구현했다. 처음 요청 범위는 구현·리뷰·커밋까지였고, 커밋 뒤에 사용자가 PR을 열고 병합하라고 해 같은 세션이 PR 직전 리뷰, 회고, PR과 병합까지 이었다(아래 "PR 직전 리뷰"부터).

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/connection-check/issues/01-contract-connection-check-routes-and-port-methods.md
>
> 다음 작업: 접속 확인의 관리 경로 둘과 응답, 포트의 확인 메서드 계약을 연다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 01-contract-connection-check-routes-and-port-methods)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/connection-check/issues/01-contract-connection-check-routes-and-port-methods.md
> 브랜치: feature/01-contract-connection-check-routes-and-port-methods
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-22-0159-connection-check-tickets.md의 "다음" 절
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: 구현·리뷰·커밋까지

사용자에게 물은 것은 하나다(검증 단계의 비용 확인). 아래 "검증"에 답을 적었다.

## 만든 것

- core: `core/ports.py`에 결과 타입 `Reached`·`Unreached`·`CheckOutcome`. 도구 포트에 `check_remote`·`check_stdio`, 모델 포트에 `check`(셋 모두 비동기). 약속(붙지 못한 것은 예외가 아니라 `Unreached`, 기한에 닿으면 연 것을 닫고 `Unreached`, 취소는 삼키지 않음, 구성 오류는 `PluginError`)을 두 포트의 독스트링에 적었다. 모델 포트의 "동기다"는 모델을 만드는 `build`의 불변식으로 좁혔다.
- 관리 층: `admin/connection_check.py`(응답 모델 넷과 판별 유니온 `ConnectionCheck`, 닫힌 열거 `CheckableKind`, 확인 함수 묶음 둘 `AutomaticChecks`·`LaunchingChecks`). `admin/http.py`의 `admin_router`가 포트가 아니라 묶음 둘을 받고, 오퍼레이션 둘(`check_connection`, `check_connection_by_launching`)이 선다. 둘 다 `async def`이고 단건 조회보다 먼저 선언한다.
- 조립: `server.py`가 도구 포트의 두 메서드와 모델 포트의 `check`만 꺼내 묶음을 채운다. 라우터는 `connect`를 부를 길이 없다.
- 실제 어댑터(`adapters/mcp.py`, `adapters/models.py`)의 확인 메서드는 `NotImplementedError`를 던지는 자리로 두었다(티켓의 "병합 뒤에 틈이 있다"). 직접 부르면 500이다.
- 계약: `openapi.json`과 생성 TS 타입을 다시 만들었고, `clients.test-d.ts`에 관리 경로 목록과 `status`로 좁히는 타입 시험(`@ts-expect-error` 둘)을 더했다.
- 가짜 포트: 기존 가짜 열두 곳이 새 메서드를 시그니처로 만족하게, 불리면 터뜨리는 바탕 둘을 `tests/fake_checks.py`에 두고 상속하게 했다. 바탕은 포트가 아니라서 "가짜는 포트를 상속하지 않는다"는 규칙(`.claude/rules/tests.md`)을 어기지 않는다.
- 규칙 문서(`writing-for-agents`를 먼저 불렀다): `.claude/rules/admin.md`(첫 항목과 접속 확인 항목), `core.md`(포트 표의 두 행), `adapters.md`(자리 항목). 옛 문장 "관리 라우터는 도구 포트를 받지 않는다"는 글자 그대로 남겼다. 모델 포트도 받지 않는다는 말과 묶음 둘을 그 뒤에 덧붙였다(명세 309줄이 그 첫 문장이 그대로 선다고 적었기 때문이다).

## 정한 것(티켓이 이 티켓에 맡긴 것)

- **오류 응답에는 `Cache-Control: no-store`를 싣지 않는다.** 200 응답에만 싣는다(OpenAPI에도 200의 헤더로만 적었다). 오류는 다시 쓰일 결과가 아니라 요청의 문제다. 404·422·500과 미들웨어의 401을 시험에 고정했다.
- **플러그인 파일 읽기는 이벤트 루프에서 그대로 읽는다.** 스레드로 넘기지 않는다. 파일이 작고 쓰기 라우트와 같은 비용이다. `admin/http.py` 모듈 독스트링에 "조회 라우트는 동기 `def`" 문장의 예외로 적었다.
- **컴포넌트 이름:** `CheckableKind`, `ConnectionCheck`(유니온), `ConnectionReached`·`ConnectionUnreached`·`ConnectionDisabled`·`ConnectionNotApplicable`.
- **`unreached`는 서버 기록에 한 줄도 남기지 않고, 확인 함수가 던진 예외만 500이다.** 둘 다 시험으로 고정했다.

## 막힌 것과 고친 것

- 첫 전체 검증에서 둘이 빨갰다. 하나는 prettier가 `clients.test-d.ts`의 서식을 거부한 것이고(`prettier --write`로 고침), 하나는 `tests/channel/http/test_router.py`의 "계약 컴포넌트 집합" 시험이 새 컴포넌트 여섯을 모르는 것이다(관리 쪽이 더한 이름이라 `EXISTING_COMPONENTS`에 더했다). 나머지 8056개는 초록이었다.
- Bash 도구가 `&&`와 셸 함수로 엮은 긴 명령을 워크트리 밖일 수 있다고 거부해, 파일마다 Edit 한 번씩으로 임포트를 더했다.

## 검증

- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`(0 errors), `uv run lint-imports`(7 kept): 초록.
- `uv run python tools/run_checks.py`: 첫 판에서 위 둘만 빨갰다. 고친 뒤 `tests/channel/http/test_router.py`의 그 시험과 `pnpm -C web verify`를 다시 돌려 초록을 봤다. `run_checks.py` 전체를 두 번째로 돌리지는 않았다.
- 새 시험은 `tests/test_server.py`의 "접속 확인" 절이고 `tests/test_server.py` 전체(213개)가 초록이었다.
- 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`): 9개가 모두 통과했다(돌려 봤다, 1.3분, 종료 코드 0).
- `uv run --env-file ../../../.env pytest -m llm -q`: 23개 통과(7분 49초). LLM 토큰 합계 257,754(입력 252,328, 출력 5,426), 트레이스 30개, 모델 호출 61건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다고 러너가 알렸다. 이 줄의 수는 위 명령을 손으로 쳐서 러너 출력에서 읽었다.
- 로컬 모델 시험(`tools/llm_local.py run --yes`): 2개 통과(종료 코드 0). 사용자가 비용 어림(가장 싼 갈래 약 $0.27, 90분 최악 $0.81~1.77. 2026-11-13의 웹 요약에서 가져온 값이라 재 보지 않았다)을 보고 "돌린다"고 답한 뒤 쳤다. 파드 둘 갈래 셋(A5000, 3090, A40) 가운데 앞 둘은 재고 없음(400)으로 `terraform apply`가 실패했고, 셋째 후보인 `shared` A40 한 파드에서 돌았다(경과 389.5초, 시간당 $0.59, 가격표 2026-11-13). 앞 시도에서 파드가 일부 만들어졌다고 출력에 나왔으나(`g847bx365k2sq6`, `7zz2jxd64v6880`) Runpod 목록 조회(`list-pods`)로 지금 남은 파드가 0개인 것을 봤다. 토큰 합계 6,297(입력 6,191, 출력 106), 모델 호출 4건. 기록 묶음의 회차 파일은 `C:\Users\User\.agent-os\llm-local\feature%2F01-contract-connection-check-routes-and-port-methods\records\round-0001-20261122T045435Z.json`이다. 이 변경은 실제 어댑터에 `NotImplementedError` 자리만 더했으므로 시험 대상 동작은 바뀌지 않았다.

- 리뷰 반영 뒤 `uv run python tools/run_checks.py`(백그라운드): 종료 코드 0. check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest(548.9초), web-verify(662.8초)가 모두 Passed(러너 출력을 손으로 읽었다).
- 카나리아(규칙 셋을 바꿨다는 `sibling_overlap.py`의 알림에 따라 `tools/canary.py`로 새 `claude -p` 세션에서 불러 봤다): `.scratch/connection-check/probes/canary/`의 새 명세 셋 `admin_rule_first_item.toml`, `adapters_rule_check_gap.toml`, `core_rule_port_table_check.toml`이 각각 통과 4(실험군 셋이 바뀐 구절을 글자 그대로 옮겼고 대조군은 "없음", "없음" 섞인 통과 0, claude 2.1.325, 2026-11-22). 기존 명세가 이미 있는 `adapters.md`·`core.md`의 다른 항목은 이 변경이 고치지 않아 다시 돌리지 않았다.

## 셀프 리뷰(`/code-review`)

범위: base `a2c318849b8a285fd167865bce08f6a81439d60c`(`origin/dev`와의 merge-base), 커밋 0개, 수정 파일 20개, 미추적 3개(코드 둘 `admin/connection_check.py`·`tests/fake_checks.py`와 이 일지). 서브에이전트 둘이 병렬로 봤다(표준 축은 sonnet·high, 명세 축은 세션 모델). Critical과 Major는 없었다.

**표준 축.** Minor 4, 냄새 판단 2, Nit 3.

- 고친 것: ①`Unreached.reason`의 "비지 않는다" 약속이 포트 독스트링에 없었다(어댑터가 빈 `str(예외)`를 그대로 담으면 응답 모델의 `min_length=1`에서 500이 난다. 실제로 `_connection_of(Unreached(""))`가 `ValidationError`를 냄을 서브에이전트가 `uv run python`으로 불러 확인). `core/ports.py`의 `Unreached` 독스트링에 약속을 적고, 채울 몫이 생기는 티켓 02·03의 체크박스에 한 줄씩 넘겼다. ②`admin/http.py` 모듈 독스트링의 "행마다 30초에 한 번 부르는 라우트"는 `POST`에 틀리고 간격 값은 명세 몫이라 그 문장을 지웠다. "유일한 예외"도 `PUT enabled`와 섞여 읽혀 "예외"로 줄였다. ③같은 독스트링의 "대가는 읽는 동안 루프가 멈추는 것"에 `_retrying`(윈도우에서 잠긴 파일을 만나면 짧게 쉬며 다시 읽음)의 쉬는 시간을 더했다.
- 남긴 것: `ToolSource` 독스트링의 "구성 오류는 실행과 같은 예외로 올린다"가 예외 타입을 대지 않는다(`ModelSource`는 `PluginError`로 못박음). 도구 쪽의 구성 오류가 무엇인지는 02 티켓이 어댑터를 쓰며 정할 일이고, 이 문장은 명세 308줄의 글자 그대로라 02가 구체화한다. 두 라우트의 앞부분 중복(`Duplicated Code`)과 `PluginKind(kind)` 변환의 반복은 라우트가 둘뿐이고 갈라지는 길이 02·03·04에서 더 생길 수 있어 합치지 않았다(판단 항목). 묶음 둘의 `plugins`와 `admin_router(plugins=)`가 서로 다른 인스턴스를 받을 수 있다는 점은 조립 층 한 곳(`server.py`)만 만들므로 두었다. `tests/fake_checks.py`의 바탕 상속은 `.claude/rules/tests.md`의 "포트를 상속하지 않는다"의 글자를 지키고 독스트링이 이유를 적었다. Nit 셋(주석 표현, 독스트링 줄 감기, `Reached` 이름)은 고치지 않았다.

**명세 축.** Minor 3, Nit 3. 02~06의 몫을 미리 쓴 범위 넘침은 없었다. 티켓 체크박스는 계약·판정·포트·시험·규칙이 충족이고, 검증 체크박스 셋은 이 세션이 직접 돌려 닫았다(위 "검증").

- 고친 것: ①`.claude/rules/admin.md` 첫 항목을 티켓의 문장("관리 라우터는 도구 연결을 여는 길(`ToolSource.connect`)을 받지 않고 접속 확인만 받는다")으로 좁혔다. 앞선 구현은 명세 309줄("첫 항목 … 글자 그대로 선다")을 따라 옛 문장을 남겼으나 티켓 체크박스가 더 구체적이고 ADR 0067 Consequences가 "성질이 좁아진다"고 적어, 티켓을 따랐다. ②실제 어댑터 둘의 확인 메서드가 `#` 주석뿐이어서 메서드 독스트링(메서드가 있다는 것과 아직 붙어 보지 않는다는 것)을 더했다. ③확인 함수가 `PluginError`(구성 오류)를 올리는 길의 시험이 없었다. 이 오류는 고정 문구가 아니라 표(`failure_for`)를 지나 운영자 면에서 글을 그대로 싣는다. `tests/test_server.py`에 `test_확인_함수가_구성_오류를_올리면_운영자에게_그_글이_가는_500이다`를 더했다(모델 `GET`과 stdio `POST`).
- 남긴 것: `adapters.md`는 기존 MCP·모델 소스 항목을 고치지 않고 새 항목 하나를 더했다(기존 항목들이 예외 타입과 제공사 가르기를 다룬 것이라 확인 메서드의 틈은 따로 두는 쪽이 읽기 쉽다. 티켓의 "해당 항목은 함께 적는다"는 새 항목이 채운다고 봤다). 단건 조회 가로채기 시험이 200만 단언하는 것은 순서가 뒤집히면 422가 되어 잡히므로 두었다. `unreached`의 서버 기록 0줄 단언이 성공 응답에서 원래 참에 가깝다는 지적은 명세 "결과가 남는 자리"가 요구한 모양이라 두었다.

**다시 돌린 명령(고친 뒤).** `uv run ruff check .`(통과), `uv run ruff format --check .`(2538개 이미 서식 맞음), `uv run pyright`(0 errors), `uv run pytest tests/test_server.py -q -k 확인`(32개 통과, 새 시험 둘 포함). 전체 `run_checks.py`와 관리 화면 e2e는 이 리뷰 반영 뒤 다시 돌리지 않았다. 반영이 고친 것은 독스트링·주석·규칙 문장 몇 개와 시험 하나뿐이고 계약(`openapi.json`)과 코드 동작은 바뀌지 않았다. 커밋의 pre-commit이 린트·타입·경계·pytest·web을 한 번 더 돌린다.

**밀 주장(PR 직전 리뷰에 넘길 새 문장).** ①"`Unreached.reason` 은 비지 않은 글이어야 한다. … 빈 글이 오면 관리가 응답을 만들지 못해 500 이다"(`core/ports.py`), ②"윈도우에서 다른 핸들이 연 파일을 만나면 읽기가 잠깐 쉬며 다시 시도하는 시간(`_retrying`)도 그 대가에 든다"(`admin/http.py` 모듈 독스트링), ③"구성 오류는 실행 전 실패와 같은 `PluginError` 이고 표가 운영자 면에서는 글을 그대로 싣는다"(`tests/test_server.py` 새 시험의 독스트링. 근거는 `http/errors.py` 305~306줄의 `str(error) if operator else INTERNAL_MESSAGE`).

## PR 직전 리뷰

`coderabbit-review` 서브에이전트가 `coderabbit review --agent --include-untracked --base origin/dev`로 돌았다(작업 트리가 깨끗해 기준을 주지 않으면 비교할 변경이 없을 수 있어 `--base`를 더했다). `coderabbit auth status`의 줄은 `Plan: Free`, `Seat: not assigned`이고 리뷰는 좌석 거절 없이 끝까지 돌았다(종료 코드 0, 마지막 이벤트 `review_completed`, 본 파일 29개, `Too many files` 없음). findings는 0건이었다. 서브에이전트가 diff를 직접 읽고 낸 것은 CLI 지적이 아니며 모두 Minor 이하다.

- **고친 것: 없음.**
- **남긴 것.** ①실제 어댑터의 확인 메서드가 `NotImplementedError`라 02·03이 채우기 전에 병합본을 올리면 켜 둔 항목의 확인이 500이다. 티켓 01이 이미 밝힌 틈이고, 이 기능의 출시는 티켓 02·03이 병합된 뒤의 끝 줄을 적는 커밋 이후다. ②`ConnectionUnreached.reason`에 어댑터가 `str(error)`를 그대로 넣으면 주소·헤더 값이 응답에 샐 수 있다는 점은 이 커밋에 어댑터 본문이 없어 아직 일이 아니다. 받는 쪽이 이미 수용 기준으로 든다. 티켓 02는 서버가 되울린 헤더 값이 `reason`에 없는 것(16·31줄), 티켓 03은 되울린 키, 주소의 사용자 정보와 쿼리, 환경 변수의 값이 `reason`에 없는 것(44·46·51줄)이다. 원격 주소 자체가 `reason`에 실리는 길은 앞 일지가 받아들인 위험이다. ③두 확인 라우트가 `async def`인데 파일 읽기가 동기라 윈도우에서 읽기 재시도(`_retrying`)가 쉴 때 루프가 그만큼 멈춘다. 모듈 독스트링이 이 대가를 이미 적었다.
- **밀 주장은 넘길 곳이 없었다.** 위 "밀 주장" 셋은 CLI가 돌아 `bug-perf-review`가 돌지 않았으므로 CLI에 넘기지 못한다(CLI 호출에 주장을 넘기는 인자가 없다. `code-review` 6단계의 1). 서브에이전트는 diff를 읽다 ②와 같은 `reason` 서술을 짚었으나 문장의 거짓을 내지 않았다.

## 회고

후보 둘: 기각 2, 승인 0, 넘김 0. 사용자에게 넘긴 것은 없다. 만료는 `uv run python tools/queue_open_rows.py`가 "만료할 항목: (없음)"이었다(출력을 손으로 읽었다). `--ref origin/dev`로는 다시 돌리지 않았다. 두 출력에 모두 든 항목만 닫는 규칙이라 앞의 출력이 비면 닫을 것이 없다.

- **명세 309줄("첫 항목 … 글자 그대로 선다")과 티켓의 "좁힌다"가 갈려 구현 중에 티켓을 따랐다: 기각.** 셀프 리뷰 명세 축이 짚어 고쳤다(위 "셀프 리뷰"). 이미 있는 리뷰 절차가 그 자리에서 잡았고, 남은 티켓 02~06은 `admin.md`의 그 항목을 건드리지 않아 같은 어긋남이 다시 나올 자리가 없다.
- **윈도 Bash 가드의 거부, 커밋 제목 72자 초과, 일지의 "실측" 낱말, 인용 대조 경고 둘: 기각.** 모두 이미 있는 가드·훅·검사가 그 자리에서 막거나 알렸다(`CLAUDE.md` 환경 함정과 pre-commit의 `commit message`, 낱말 훅, `check-quotes`). 인용 대조 경고 둘은 막지 않는 경고라 두었다.

## 다음

- **병합 직후 할 일은 기능 connection-check의 티켓 02와 03을 나란히 구현하는 것이다.** 둘 다 `ready-for-agent`이고 `Blocked by`가 01뿐이며, 01은 이 PR로 `done`이다. 02는 `adapters/mcp.py`, 03은 `adapters/models.py`와 헌법 문서를 고쳐 대상 파일이 서로 겹치지 않는다. 티켓마다 새 세션으로 가고 브랜치는 `feature/02-check-mcp-servers-remote-and-stdio`, `feature/03-check-models-by-provider`다(`/implement .scratch/connection-check/issues/<파일>`). 04는 02·03 뒤, 05와 06은 04 뒤에 나란히 돈다.
- **로컬 모델 시험은 01에서 한 번 돌렸고(2개 통과) 남은 것은 02·03·06의 세 번이다.** 02와 03은 병합 직전에 기준 브랜치를 합친 뒤에 돌아야 한다(상대가 먼저 병합되면 합치기 전의 기록은 무효다). 비용 확인은 시험 직전에 사용자에게 받는다.
- **이 PR이 남긴 틈.** 실제 어댑터의 확인 메서드는 `NotImplementedError`를 던지는 자리다. 02와 03이 채운다. 둘 다 `Unreached.reason`이 비지 않게 채우는 것과 비밀을 가리는 것을 수용 기준으로 이미 가졌다.
- **기능을 닫는 일(끝 줄, 기능 단락, 계획 표)은 05와 06 가운데 늦게 병합하는 쪽이 맡는다.**
