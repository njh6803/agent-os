# 2026-11-23 (15:01) connection-check 티켓 02 MCP 서버의 접속 확인

브랜치 `feature/02-check-mcp-servers-remote-and-stdio`, 워크트리 `.claude/worktrees/02-check-mcp-servers-remote-and-stdio`. 모델 Sonnet 5.5(지시문의 high). 기준은 `origin/dev`다. 앞 일지 `2026-11-22-1335-connection-check-01-contract.md`의 "다음"이 가리킨 티켓 02를 구현했다. 요청 범위는 PR과 병합까지다. 세션 컨텍스트가 문턱을 넘어 `셀프 리뷰 직전`에서 인계한다(이 일지는 커밋하지 않았고 `## 다음`도 없다. 새 세션이 이어 쓰고 커밋한다).

세션 제목: `feature/02-check-mcp-servers-remote-and-stdio`(인계하며 `(인계함)`을 붙인다).

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/connection-check/issues/02-check-mcp-servers-remote-and-stdio.md
>
> 다음 작업: MCP 서버의 접속 확인: 원격 서버는 스스로, stdio 서버는 눌러서 붙어 본다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 2 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 02-check-mcp-servers-remote-and-stdio)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/connection-check/issues/02-check-mcp-servers-remote-and-stdio.md
> 브랜치: feature/02-check-mcp-servers-remote-and-stdio
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-22-1335-connection-check-01-contract.md의 "## 다음"
> 이어받을 상태: 없음
> 이번 요청 범위: PR과 병합까지

(지시문의 나머지 줄은 같은 뜻이라 줄였다. 이 세션에서 사용자가 더 한 말은 없다.)

## 한 것

- `src/agent_os/adapters/mcp.py`: `McpTools`에 `check_remote`·`check_stdio`를 더했다. 둘 다 모듈 함수 `_check(name, server, seconds)` 하나로 간다. 실행이 서버 하나를 여는 길(`_opened`)을 그대로 열고 닫는다. 기한은 `REMOTE_CHECK_SECONDS = 10`, `STDIO_CHECK_SECONDS = 20`이고 어댑터를 만들 때 `McpTools(remote_check_seconds=, stdio_check_seconds=)`로 바꾼다. 모듈 독스트링에 "접속 확인은 서버 하나를 실행이 여는 길로 열고 닫는다" 문단을 더했다.
- `tests/adapters/test_mcp.py`: "접속 확인(ADR 0067)" 구역에 시험 16개를 더했다(파일 전체 65개 통과).
- `tests/mcp_http_server.py`: 가짜 서버에 `--list-sleep <초>` 옵션(도구 목록 응답을 늦춘다)을 더했다.
- `.claude/rules/adapters.md`: 접속 확인이 아직 붙어 보지 않는다는 옛 항목을 MCP 몫(동작한다)과 모델 소스 몫(`ManifestModels.check`는 아직 `NotImplementedError`)으로 갈랐다. 03이 모델 쪽을 고칠 때 이 파일에서 충돌이 날 수 있고 그것은 예상한 것이다.
- 카나리아 명세: 새 `adapters_rule_mcp_check.toml`, 고친 `adapters_rule_check_gap.toml`. 둘 다 통과 4(실험군 셋은 기대 구절을 글자 그대로 옮겼고 대조군은 "없음").
- 티켓 02: 상태를 `in-progress`로 바꾸고 19칸 가운데 16칸을 채웠다. 검증 세 칸(43~45줄)은 비워 뒀다.

## 결정과 고친 것

- **도구 확인에는 `PluginError` 길이 없다.** 헤더 환경 변수가 비었거나 명령이 없는 것은 모두 여는 단계의 실패라 `Unreached`가 된다. `core/ports.py`의 `ToolSource` 독스트링 "구성 오류는 실행과 같은 예외로 올린다"는 건드리지 않고, 어댑터 쪽 문서(`mcp.py` 독스트링, `adapters.md`)에 MCP 확인에는 그 길이 없다고 적었다.
- **기한을 `scope.cancel_called`로 알아본다.** 라이브러리가 기한의 취소를 예외로 바꿔 `_connecting`이 `ConnectionError`로 만들 수 있다. 그때 연결 오류의 글이 나오면 안 되므로 `cancel_called`면 시간 초과의 글로 돌린다. `if True:`로 바꾼 변이가 처음 시험에 살아남았고, `_opened`를 바꿔치기해 그 갈래를 밟는 시험을 더해 잡았다.
- **취소 범위는 여는 것과 닫는 것을 함께 감싼다.** 안 그러면 anyio가 범위 중첩 위반을 낸다. `Reached`인지는 도구 목록을 읽은 뒤 `opened = True`로 정한다. 닫는 중 난 예외와 바깥 취소는 바꾸지 않고 그대로 올린다.
- 시험에서 stdio 침묵 서버는 `mcp_lingering.py`에 역할을 더하지 않고 시험 안의 표준 라이브러리 스크립트(`_SILENT`)로 했다. 부하가 큰 PC에서 느려지는 것을 피하려는 것이다. `mcp_lingering.py`는 고쳤다가 되돌려 변경이 없다.
- 환경 함정 셋: 워크트리 가드가 git 복합 명령(`&&`)을 막아 하나씩 쳤고, 40줄 넘는 heredoc은 훅이 막아 Write로 썼으며, 카나리아 도구의 `--help`는 출력이 커서 `claude --version`(2.1.325)만 쳤다.

## 요청 수(티켓 02의 "요청의 수" 칸)

가짜 원격 MCP 서버로 한 번 확인할 때 서버가 받는 요청이다. 시험(`tests/adapters/test_mcp.py`)이 세어 단언한다: POST 3(초기화, 초기화 알림, 도구 목록), GET 많아야 1(알림 스트림), DELETE 1(세션 종료). 화면이 30초마다 되풀이해도 서버 하나가 확인 한 번에 받는 것은 이 수다.

## 검증 상태

- 통과: `ruff check`, `ruff format --check`, pyright, lint-imports, 러너 한 바퀴(check-ticket, check-notes, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 908.9초, web-verify 1181.5초). 모두 Passed다. 셀프 리뷰를 반영한 뒤에 `uv run python tools/run_checks.py`를 다시 쳐 모두 Passed다(손으로 쳤다. pytest 545.9초, web-verify 792.1초).
- **`-m llm`은 이어받은 세션에서 다시 쳐 23개가 통과했다**(666초, 토큰 합계 264,095, 모델 호출 61건). 셀프 리뷰 반영 가운데 `mcp.py`의 한 줄(빈 글 채우기)은 이 실행 뒤에 들어갔다. 그 줄은 어댑터를 거치는 실행의 길(`connect`)이 아니라 확인의 길(`_check`)에만 있다.
- **로컬 모델 시험은 아직 안 했다.** 병합 직전에 기준 브랜치를 합친 뒤 `--yes` 없이 쳐 예상 비용을 사용자에게 보이고 확인받은 뒤에 `--yes`로 돈다. 03이 먼저 병합되면 다시 돈다.
- 티켓의 검증 세 칸은 위 둘이 끝난 뒤에 채운다.

## 셀프 리뷰(이어받은 세션)

범위: base `36aa7db5a`, 파일 6개 변경, 커밋 0개, 미추적 2개. 표준 축은 sonnet·high, 명세 축은 세션의 모델로 돌렸다.

**고친 것**

- 표준 축 1(티켓 "빈 글을 채운다"가 코드에 없었다): `_check`가 `Unreached(str(error) or type(error).__name__)`로 채운다. 여는 단계의 변환(`_connecting`)을 지나지 않은 `ConnectionError`(해제 중의 `BrokenPipeError` 등)는 글이 빌 수 있고, 빈 글이 가면 관리가 응답을 만들지 못해 500이다. 시험 `test_글이_빈_연결_오류도_비지_않은_글의_Unreached다`를 더했다. 명세 축 1도 같은 지적이다.
- 표준 축 2와 명세 축 4(닫는 도중에 기한이 오는 갈래와 닫는 도중의 `ConnectionError`에 시험이 없었다): 시험 둘을 더했다(`…닫는_도중에_기한이_오면_Reached다`, `…닫는_도중의_연결_오류는_바꾸지_않고_올린다`). 닫는 도중의 기한은 `Reached`이고 닫는 도중의 연결 오류는 그대로 올라온다.
- 표준 축 3: 시험의 상한 `CHECK_WITHIN_SECONDS`(120)와 stdio 확인의 기한을 같이 쓰던 것을 갈랐다(`LONG_DEADLINE_SECONDS = 100`). 기한 전에 세션이 열려야 하는 두 사례의 기한을 4초와 5초에서 모두 8초로 올렸다(부하가 큰 PC의 흔들림. 명세 축 3도 같은 지적). `test_바깥의_취소는_삼키지_않는다`에 `fail_after`를 더했다. `test_접속_확인의_기본_기한…`은 상수만 리터럴과 견주던 것을 어댑터를 인자 없이 만들어 확인 함수가 받는 기한을 보게 바꿨다(기본값이 배선되어 있는지를 본다).

**남긴 것과 이유**

- 접두 문구 `MCP 서버 {name}({where})에 붙지 못했다: `이 `_connecting`·`_check`와 시험의 도우미에 셋이다(Duplicated Code, 판단 호출). 셋이 한 문구를 공유한다는 사실이 시험으로 고정되어 있고, 합치면 `_connecting`의 시그니처를 바꿔야 해 이 티켓의 범위 밖이다.
- `opened` 표지와 `except` 안의 갈래(제어 신호 표지의 모양): 기한의 범위가 여는 동작과 닫는 동작을 함께 감싸야 해서 다른 모양이 없다(독스트링에 까닭이 적혀 있다).
- 포트 독스트링(`core/ports.py`)의 "구성 오류는 실행과 같은 예외로 올린다"가 그대로이고 어댑터 문서만 "이 길에는 `PluginError`가 없다"를 적은 점(명세 축 2): 실행에서도 이 실패는 `PluginError`가 아니라 `ConnectionError`라 모순은 아니다. 포트 쪽을 고치려면 계약에 닿아 이 티켓 밖이다.
- 문서가 가리킨 "문맥을 범위 안에서 열고 밖에서 닫으면 anyio가 거부한다"의 프로브는 없고 코드를 읽은 설명이다. 독스트링의 단정은 그대로 두었다. 이 세션이 그 단정을 따로 재지는 않았다(명세 축이 `mcp_lingering` 서버로 기한을 0.5~4초로 바꿔 돌린 직접 실행에서 4초는 닫는 도중의 기한이라 `Reached`였다고 보고했다. 그 스크립트는 스크래치패드의 것이라 커밋하지 않았다).

반영 뒤 확인: `uv run pytest tests/adapters/test_mcp.py -q`가 68개 통과(손으로 쳤다. 230초), `uv run ruff check . && uv run ruff format --check .`와 `uv run pyright src/agent_os/adapters/mcp.py tests/adapters/test_mcp.py`가 통과(손으로 쳤다). 빈 글 시험은 고친 줄을 `Unreached(str(error))`로 되돌린 변이에서 빨강(`reason: '' != 'BrokenPipeError'`)을 본 뒤 줄을 되돌렸다(손으로 쳤다). 닫는 도중의 시험 둘은 변이로 빨강을 보지 않았다.

## 남은 일

1. 커밋하고 PR을 연다. 티켓은 `done`이고 검증 칸의 첫째만 채웠다. 둘째와 셋째 칸(로컬 모델 시험)은 병합 직전에 채운다.
2. 봇 회차를 반영한다.
3. 병합 직전에 기준 브랜치를 합친 뒤 `uv run --env-file ../../../.env python tools/llm_local.py run`을 `--yes` 없이 쳐 예상 비용을 사용자에게 보인다(이어받은 세션에서 쳐 보았다. 파드 둘 기준 어림 30분에 $0.27~$0.59, 최악 90분에 $0.81~$1.77, 공유 서버 1대 $0.29~$0.88. 단가는 2026-11-13에 웹 요약에서 읽은 값이라 원문과 대조하지 않았다). 확인을 받은 뒤 `--yes`로 돈다.
4. 병합(워크트리 사본의 `next-session` `merge.md` "워크트리에서 병합할 때")하고 이 일지에 이어 쓴다.

## 인계

둘째 인계(커밋 뒤). 앞 세션의 인계는 셀프 리뷰 직전이었다. 이어받은 세션이 한 것은 셀프 리뷰(표준 축과 명세 축)와 반영, `-m llm` 23개 통과, 러너 한 바퀴 Passed, 티켓 `done`(검증 칸은 첫째만 채움), 일지 갱신, 커밋 `5fec36723`(pre-commit 통과)이다. 푸시와 PR은 아직 하지 않았다. 위 "남은 일"의 1은 커밋까지 끝났고 푸시와 PR이 남았다. 새 세션은 푸시하고 PR을 열고 봇 회차를 거쳐 병합하며, 병합 직전에 `llm_local`을 사용자에게 비용을 보여 확인받고 돈다.

- 세션 제목: `feature/02-check-mcp-servers-remote-and-stdio`(인계하며 `(인계함)`을 붙인다).
- 사용자 프롬프트: 첫 절의 것과 같다(이어받은 세션의 첫 메시지도 같은 지시문이었고 사용자가 더 한 말은 없다).
- open-session을 부른다 2026-11-23T06:45Z
