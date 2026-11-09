# 2026-11-10 (04:21) mcp-http 접속

세션 제목 `02-connect-to-remote-mcp-server-by-url`. 브랜치 `feature/02-connect-to-remote-mcp-server-by-url`, 워크트리 `.claude/worktrees/02-connect-to-remote-mcp-server-by-url`(기준 `bc2b9c2d`). 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/mcp-http/issues/02-connect-to-remote-mcp-server-by-url.md
>
> 이번 요청 범위: PR과 병합까지

## 한 일

티켓 02를 구현했다. 어댑터의 http 갈래가 01의 `NotImplementedError` 대신 실행마다 매니페스트의 `url`에 streamable HTTP로 붙는다(`src/agent_os/adapters/mcp.py`).

- 헤더 값은 접속 직전에 `[server.headers]`의 환경 변수에서 매니페스트 순서로 읽는다. 없으면 `헤더 X의 환경 변수 V이 없다`, 헤더 값으로 쓸 수 없는 글자(탭과 0x20~0x7e 밖)가 있으면 `…의 값에 헤더 값으로 쓸 수 없는 글자가 있다`로 붙지 않는다. 문장에 값은 없다.
- 클라이언트는 `httpx2.AsyncClient`(기본 헤더, 기한 30초·읽기 300초)이고 mcp의 `streamable_http_client`에 넘긴다. 응답 훅이 POST의 오류 응답 상태를 받아 두었다가 여는 동안의 실패 문구 끝에 ` (HTTP <코드> <이유>)`을 붙인다. 2xx가 오면 지운다.
- 서버가 되울린 헤더 값은 `[가림: 헤더 <이름>]`으로 가리고 가렸으면 `from None`이다(여는 문구와 호출 실패 문구 둘).
- mcp 클라이언트 로거(`mcp.client.streamable_http`)는 DEBUG로 보내는 메시지 전체(`Sending client message: {…'secret': …}`)를 찍으므로 그 로거에 DEBUG를 버리는 필터를 달았다. 필터가 없으면 core의 DEBUG 시험이 빨간 것을 먼저 봤다.
- `httpx2>=2.13,<3`을 직접 의존으로 선언했고 import-linter 금지 목록 둘에 더했다. `uv lock`의 차이는 agent-os 자신의 의존 두 줄이고 패키지 84개는 그대로다(손으로 봤다).
- `.claude/rules/adapters.md`·`core.md`·`sdk.md`와 `docs/constitution/tech.md`의 stdio 전제·"아직 붙지 않는다" 문장을 고쳤다(`writing-for-agents`를 먼저 불렀다). 옛 표현을 저장소 전체에서 grep했고 살아 있는 문서의 잔존은 0이다(남은 곳은 명세·티켓·일지·카나리아 주석의 기록이다).
- 시험: HTTP 픽스처(`tests/mcp_http_server.py`, `tests/mcp_http.py`), 어댑터 시험의 "원격 서버" 절, core 시험 둘(꺼진 서버, DEBUG 로그), 매니페스트 시험 둘.

## 결정

사용자에게 물은 것은 없다. 01이 넘긴 판단 거리 셋은 이렇게 정했다(티켓 파일의 "정한 것"에도 있다).

- 제어 문자가 든 주소는 문구를 지을 때 `unicode_escape`로 이스케이프한다. 읽는 단계의 검사는 바꾸지 않는다.
- 헤더 이름 금지 목록에 `upgrade`, `te`, `trailer`, `keep-alive`, `proxy-authorization`을 더했고 `cookie`는 받는다.
- 쿼리 문자열의 비밀이 문구에 남는다는 ADR 0049의 결정은 시험으로 고정했다.
- 헌법 판을 3.0.76에서 3.0.77로 올렸다. 까닭은 `tech.md` 런타임 의존성 행의 문구 수정(httpx2가 선언된 의존이 되었다)이라 patch다.

## 접속 시험이 드러낸 것

닫힌 포트에서 난 `ConnectionError`의 문맥 사슬(`__context__`)에 mcp가 자기 태스크 그룹을 취소하며 남긴 `CancelledError`가 있었다(`ConnectionError` → `ExceptionGroup` → `CancelledError`). core의 `_connected`는 정리 코드가 덮은 기한의 취소를 이 사슬에서 찾아 다시 던지므로, 서버를 못 찾은 실패가 `run_failed` 없이 취소로 끝났다. 어댑터 시험은 `ConnectionError`만 보아 이것을 놓쳤고 core를 지나는 시험(`test_꺼진_원격_서버로_…`)이 빨개서 찾았다. 어댑터가 바깥 범위가 취소 중이 아닐 때만(`anyio.current_effective_deadline() != -inf`) 그 취소를 사슬에서 뗀다(`_forget_own_cancellation`). 어댑터 시험이 사슬에 취소가 없다는 것을 고정하고, 기한이나 바깥 취소는 그대로 남는다.

## 검증

- `uv run ruff check .`·`uv run ruff format --check .`·`uv run pyright`·`uv run lint-imports`는 초록이다(각 명령의 출력을 봤다).
- 러너 `uv run python tools/run_checks.py`(백그라운드, 종료 코드 0): pytest 642.6초, web-verify 805.0초, pyright 둘·lint-imports·지침 검사·타입 우회 검사·zizmor·훅 러너·커밋 검사 통과(러너의 출력 끝을 봤다). `pnpm -C web verify`는 러너가 돌렸고 이 티켓은 web과 `openapi.json`을 건드리지 않아 e2e·사진 비교는 치지 않았다.
- 빨강: 01의 임시 실패 시험을 실제 접속의 시험으로 바꾼 것이 첫 빨강이다. 로그 시험은 필터를 뺀 판에서 `Sending client message: … 'secret': 'tool-arg-secret-5d2c'`가 `caplog`에 남아 빨갰다(손으로 봤다). core의 꺼진 서버 시험은 `_forget_own_cancellation`이 없는 판에서 `CancelledError`로 빨갰고 고친 뒤 초록이다.
- 변이(손으로 넣었다. `tools/mutate.py` 표는 만들지 않았다): `_connecting`의 `from None`을 `from error`로 바꾸면 `test_서버가_되울린_값은_여는_동안의_실패_문구에서_가려진다`가 `error.__cause__ is None` 단언에서 빨갛고, 응답 훅이 2xx에서 상태를 지우지 않게 바꾸면 `test_지나간_307_은_…`이 `HTTP 307 Temporary Redirect`가 붙어 빨갰다. 둘 다 되돌렸다. 나머지 새 시험은 변이를 넣어 보지 않았다.
- 카나리아: `.claude/rules/adapters.md`·`core.md`·`sdk.md`를 원천으로 든 명세 열 개(adapters 셋, core 다섯, sdk 둘)를 `tools/canary.py`로 실제 돌렸다(claude 2.1.318, 커밋 `bc2b9c2d` 위의 커밋하지 않은 작업 트리). 열 개 모두 통과 4·실패 0·"없음" 섞인 통과 0이다. 같은 PR 안의 통과가 없어 사전 확인 갈음 조건에 맞지 않아 실제로 돌렸다(사전 확인도 열 개 통과). 각 명세의 `# 최신 결과:` 줄을 이 결과로 바꾸고 지난 줄은 `# 앞선 결과:`로 내렸다.
- `uv lock`의 차이는 agent-os 자신의 의존 두 줄(`{ name = "httpx2" }`와 `{ name = "httpx2", specifier = ">=2.13,<3" }`)이고 패키지 84개는 그대로다(`git diff uv.lock`을 손으로 봤다). 설치된 `httpx2` 2.13.0은 명세 검토가 재던 판과 같다.

## 인계

셀프 리뷰 직전에 컨텍스트가 문턱을 넘어 인계한다. 이 세션의 제목은 `feature/02-connect-to-remote-mcp-server-by-url`였고 `(인계함)`을 붙여 넘긴다. 구현, 게이트(러너 초록), 카나리아 열 개, 손으로 넣은 변이 둘은 끝났고 아무것도 커밋하지 않았다. 남은 것은 `/code-review`(기준 `bc2b9c2d`), 반영, 커밋, 이 일지의 "다음"·셀프 리뷰·회고 절, PR, 병합이다. 낸 지시문은 아래 그대로다.

```
다음 작업: .scratch/mcp-http/issues/02-connect-to-remote-mcp-server-by-url.md (원격 MCP 서버에 매니페스트의 주소로 실행마다 붙는다)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/mcp-http/issues/02-connect-to-remote-mcp-server-by-url.md
브랜치: feature/02-connect-to-remote-mcp-server-by-url
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-10-0421-mcp-http-connect.md
이어받을 상태: 인계: 셀프 리뷰 직전. 일지는 docs/journal/2026-11-10-0421-mcp-http-connect.md 이고 "인계"가 이 인계다. 커밋하지 않은 변경이 워크트리에 있고(구현·시험·rules·카나리아 명세 열·티켓 done·일지) 러너와 ruff는 이미 초록이니 /code-review(기준 bc2b9c2d)부터 한다. 티켓은 이미 done이고 plan_table은 돌렸다(03·04가 남아 끝 줄은 쓰지 않는다). 구현을 다시 하지 않는다. 남은 일: /code-review 반영(Critical·Major), 커밋(pre-commit 결과로 게이트 갈음), 일지에 셀프 리뷰·회고·"다음" 절, /git-pr(본문에 uv.lock 차이 두 줄, 접속 시험이 드러낸 취소 문제와 고침, 결정 셋), PR 연결, 봇 회차, merge.md의 워크트리 병합. 병합 뒤 next-session으로 티켓 03·04 지시문을 낸다(둘은 02 뒤에 나란히 돈다).
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-11-09T19:41:45Z

## 셀프 리뷰

이어받은 세션(같은 제목)이 `/code-review`를 돌렸다. 범위는 기준 `bc2b9c2d`, 파일 23개(작업 트리), 커밋 0개, 미추적 3개(`tests/mcp_http.py`, `tests/mcp_http_server.py`, 이 일지)다. 표준 축은 sonnet·high, 명세 축은 세션의 모델로 돌았다. 둘 다 Critical·Major는 없었다.

고친 것:

- 표준 Minor: 앞뒤에 공백이나 탭이 붙은 헤더 값(`"abc "`)은 `_read_headers`의 검사를 지나 `httpx2`가 값 그대로 실은 `LocalProtocolError`로 거부하고, 8자보다 짧으면 가림이 닿지 않아 값이 `ConnectionError`에 남았다. 서브에이전트의 측정을 직접 다시 돌려 확인했다(`' lead'`, `'trail '`, `'\ttab'`, `'tab\t'`는 `Illegal header value`, 안쪽 공백과 탭은 통과). 검사를 `value != value.strip(" \t")`까지 넓혔고 시험 다섯(`test_앞뒤에_공백이나_탭이_붙은_값은_…`)은 고치기 전에 빨갰다(문구가 `ConnectError`로 끝났다). 티켓 "정한 것"에 적었다.
- 명세 Minor: 어댑터 독스트링의 `serve` 종료로 취소된 실행이 DELETE를 보내지 않는다는 문장을 티켓처럼 어림으로 되돌렸다(`.scratch/mcp-http/probes/http_close.py`가 다시 내는 것은 기한뿐이다). http의 닫는 시간을 한 문장 더했다(닫을 프로세스가 없어 stdio의 닫는 시간이 걸리지 않는다고 코드를 읽어 적었고, 종료 요청의 왕복 시간은 어림이라고 적었다).
- 명세 Minor: 헤더 값이 어느 라이브러리 로거의 DEBUG 줄에도 실리지 않는다는 독스트링 문장을 `.scratch/mcp-http/probes/README.md`가 적은 `mcp`·`httpx2`·`httpcore2` 셋으로 좁혔다.
- 명세 Minor: `pyproject.toml` 주석의 "mcp 가 그 판을 정한다"가 틀렸다. 설치된 mcp의 `Requires-Dist`가 `httpx2>=2.10.0`(하한뿐)이라 `importlib.metadata`로 확인했고 "쓰는 판은 락이 정한다"로 고쳤다.
- 명세 Nit: `core/ports.py`의 `ToolSource` 독스트링 "첫 어댑터는 MCP stdio"를 "MCP(stdio와 http)"로 고쳤다.

남긴 것과 이유:

- 표준 Minor, 가림 경계(7자와 8자), 공백으로 나뉜 값의 나머지만 되울리는 경우, 긴 글부터 가리는 순서를 직접 가르는 시험이 없다. 가림 규칙은 되울림 모드의 시험 둘(값 전체와 `Bearer` 뒤 토큰이 함께 가려진다)이 지나고, 경계 시험은 사설 클래스(`_Attempt`)를 부르거나 8자 미만이 되울려 남는 한계를 단언해야 해서 이 PR에 넣지 않았다. 회고 후보가 아니라 사건 하나라 대기열 회차로 세지 않는다.
- 표준 판단 거리(`from None` 갈래가 두 자리에 반복, `_Attempt`가 가림과 상태를 함께 듦, `Timeout(30, read=300)`이 mcp의 비공개 상수를 복제): Minor·Nit이고 작다. 값 복제는 독스트링이 "mcp 가 쓰는 값"이라 적었으나 상수가 비공개 모듈에 있어 가져다 쓸 수 없다.
- 명세 Nit: 개행 값 시험이 닫힌 포트라 "서버에 붙지 않았다"를 단언하지 않는다(변수가 없는 시험은 `reached == []`로 가른다). 응답 훅이 GET·DELETE 응답을 받아 두지 않는 것을 가르는 시험이 없다(티켓 목록 밖). 공백 둘로 나뉜 값(`Bearer  tok`)은 한계 목록에 없다(명세가 "공백 하나로 나뉜 꼴"이라 어긋남은 아니다).
- 명세 Nit: `_forget_own_cancellation`과 픽스처의 `keep` 도구는 체크박스에 없으나 티켓 "접속 시험이 드러낸 것"과 로그 시험의 필요에 근거가 있어 범위 넘침으로 세지 않는다.

첫 커밋 시도가 pre-commit의 변이 표 검사(`check-mutations`)에 막혔다. `.scratch/mcp-shutdown/probes/ticket02_mutations.toml`의 변이 둘이 가리키던 `mcp.py`의 원문(`_connecting`과 `_session`이 `attempt` 인자를 받기 전의 모양)이 이 커밋에서 바뀌어 원문이 0번이었다. 원문 둘을 지금 코드 모양으로 고치고 `uv run python tools/mutate.py --check`(변이 3 모두 원문 한 번씩)와 실제 실행(`PYTHONUTF8=1 uv run python tools/mutate.py <그 파일>`, 변이 3 모두 기대대로 빨강)을 손으로 쳐서 봤다. 둘 다 이 세션이 손으로 본 결과다.

다시 돌린 명령: `uv run ruff check .`·`uv run ruff format --check .`·`uv run pyright`(0 errors)·`uv run lint-imports`(6 kept)는 고친 뒤 초록이고 `uv run pytest -q tests/adapters/test_mcp.py`는 41개 통과다(검사 확장 직후). 손으로 치는 나머지 다섯은 커밋의 pre-commit 결과로 갈음한다(결과는 커밋 뒤에 적는다).
