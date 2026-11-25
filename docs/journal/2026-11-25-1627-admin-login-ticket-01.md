# 2026-11-25 (16:27) admin-login 티켓 01: 계정 필드, 403, 출처 검사

브랜치 `feature/01-contract-account-fields-forbidden-and-origin-check`, 워크트리 `.claude/worktrees/01-contract-account-fields-forbidden-and-origin-check`. 모델 Sonnet 5.5(지시문의 high). 기준은 `origin/dev` `6b0646e80`(admin-login 명세 검토와 티켓 14장, PR 641의 병합)이다. 세션은 2026-11-25 오전에 시작했고 중간에 컨텍스트가 한 번 압축됐다. 이 일지는 사용자에게 로컬 모델 시험의 비용을 묻고 답을 받은 직후에 만들었다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/admin-login/issues/01-contract-account-fields-forbidden-and-origin-check.md
> 다음 작업: .scratch/admin-login/issues/01-contract-account-fields-forbidden-and-origin-check.md. 계정 필드와 403을 계약에 더하고 출처 검사를 세우는 첫 티켓(막는 것 없음)
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 01-contract-account-fields-forbidden-and-origin-check)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/admin-login/issues/01-contract-account-fields-forbidden-and-origin-check.md
> 브랜치: feature/01-contract-account-fields-forbidden-and-origin-check
> 모델: Sonnet 5.5 / high
> 읽을 것: 일지 docs/journal/2026-11-25-1007-admin-login-tickets.md의 "다음" 절(01 뒤 02·07·08이 나란히 돌 수 있고, 로그아웃과 갱신 경합이 남긴 위험이다)
> 이어받을 상태: 없음. PR #641(명세 검토와 티켓 14장)은 병합됐다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev(3ba468f7a, origin/dev는 6b0646e80). 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 일

- 이벤트에 계정 필드를 더했다. `run_started.requesting_account`, `approval_granted`·`approval_denied`의 `deciding_account`이고 모두 `str | None`, 기본값 `None`이며 형식 번호는 3 그대로다. `run()`과 `resume()`은 키워드 인자로 받고, 에이전트가 이 필드를 채우면 런타임이 `run_failed`로 막는다(`_reject_runtime_only`). 관리 화면 이벤트 항목의 필드 이름 표에 "요청한 계정", "결정한 계정"을 더했다. 목록 요약과 최종 사용자 항목에는 싣지 않는다.
- 에러 코드 `forbidden`(403)을 더했다. 어휘는 일곱이고 상태 코드와 1:1이다. `documented_errors`가 403을 알고, 관리 API 일곱 라우트(`/health` 제외)와 `/runs` 셋이 403을 계약에 적는다. 최종 사용자 면과 `/health`는 적지 않는다. 429는 그대로다.
- 요청 출처 검사 미들웨어(`src/agent_os/http/origin.py`)를 세웠다. `Sec-Fetch-Site`가 있으면 `same-origin`만, 없으면 `Origin`도 없을 때만 지난다. `/health`와 최종 사용자 접두사는 검사 밖이다. 자리는 예기치 않은 예외의 변환 바로 안쪽, 인증 바로 바깥이다. 문구는 "이 요청의 출처를 받지 않는다" 하나다.
- `openapi.json`과 생성된 TS 타입을 같은 변경에 다시 뽑았다. 규칙 문서 `http.md`·`channel.md`·`core.md`·`sdk.md`를 고쳤다.
- 시험은 `tests/sdk/test_events.py`, `tests/core/test_run.py`, `tests/test_server.py`에 더했고, 403이 계약에 들어와 달라진 기대 셋(`tests/channel/http/test_router.py`)을 고쳤다. 웹 쪽 시험 부품(`RunPage`·`RunDetail`)에는 새 필드를 채웠다.

## 검증

- `uv run python tools/run_checks.py`: 첫 판에서 `test_router.py`의 계약 시험 셋이 빨갰다. 403이 응답 목록에 들어온 것이 원인이라 기대를 고쳤고 그 파일을 다시 돌려 108개가 통과했다. 그 밖의 8177개와 web verify, pyright, 경계 검사는 통과했다. 린트는 `routes.py`의 import 순서 하나를 고쳐 통과했다.
- e2e: 관리 화면 11개, 위젯 19개, 위젯 테스트 페이지 41개가 통과했다.
- `-m llm` 24개 통과(토큰 합계 255,563. 입력 250,535, 출력 5,028. 트레이스 30개, 모델 호출 60건. 트레이스를 남기지 않은 LLM 테스트 2개는 세지 못했다).
- 카나리아: 바뀐 규칙 파일 넷(`core.md`·`channel.md`·`sdk.md`·`http.md`)의 명세를 하나씩 실제로 돌려 모두 통과 4(claude 2.1.325)였고 명세 머리의 `# 최신 결과:` 줄을 갱신했다. 나머지 열두 명세는 `--preflight`만 통과했다.

## 사용자에게 물은 것: 로컬 모델 시험 비용

`tools/llm_local.py run`을 `--yes` 없이 쳐 예상 비용을 받았다(Runpod 단가는 2026-11-13에 웹 요약에서 읽은 값이라 원문과 대조하지 않은 어림이다). 후보 넷은 파드 2대 셋과 공유 서버(파드 1대) 하나이고, 첫 후보는 RTX A5000 어림 30분 $0.27, 최악 90분 $0.81, 마지막 후보 A40은 최악 $1.77까지다. 선택 화면은 훅이 한 번 막아 설명의 수를 출력과 대 본 뒤 다시 불렀다.

> 질문: 로컬 모델 시험(llm_local)을 --yes로 실제 실행해도 될까요? 빌린 GPU 서버(Runpod)를 띄우며, 출력이 알린 예상 비용은 첫 후보 기준 어림 30분에 약 $0.27(파드 2대), 최악 90분에 약 $0.81입니다. 재고가 없으면 다음 후보로 넘어가 최대 $1.77까지 오를 수 있고, 90분 뒤 서버는 자동으로 지워집니다. 단가는 웹 요약에서 읽은 값이라 원문과 대조하지 않은 어림입니다.
> 선택지: 실행한다(--yes를 붙여 시험을 돌립니다. 도는 동안 셀프 리뷰와 PR 준비를 이어서 하고, 결과는 PR 본문에 적습니다) / 이번에는 건너뛴다
> 사용자: 실행한다

## 로컬 모델 시험 결과

`uv run --env-file ../../../.env python tools/llm_local.py run --yes`가 통과 4로 끝났다(출력의 기록 묶음, 종료 코드 0). 기록 묶음은 GPU A40, 배치 `pods`(파드 2대, 시간당 $1.18)로 돌았다고 적는다. 로그 끝에서 파드를 만들다 "no longer any instances available"(Runpod 응답 400)로 실패한 시도를 봤고, 그 앞 후보들이 모두 그렇게 실패했는지는 로그 전체를 읽지 않아 확인하지 못했다. 기준 커밋은 `6b0646e80`이고 작업 트리는 커밋 전이다. 모델은 `GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`과 `openai/gpt-oss-20b`, 엔진은 vLLM 0.33.0이다. 걸린 시간 328초, 토큰은 입력 6,191·출력 97·호출 4건·트레이스 2개다. 회차 파일은 `C:\Users\User\.agent-os\llm-local\feature%2F01-contract-account-fields-forbidden-and-origin-check\records\round-0001-20261125T073307Z.json`이다.

## 인계

이 세션의 컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전` 경계에 왔다. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`)부터 남았다. 남은 일: 셀프 리뷰 반영, 티켓 상태를 `done`으로, `uv run python tools/plan_table.py`, `tools/sibling_overlap.py`, 이 일지의 "다음" 절과 회고, 커밋, 푸시, PR, 병합(워크트리 사본의 `merge.md` "워크트리에서 병합할 때"). 로컬 모델 시험의 예상 비용은 사용자가 확인했고 이미 돌았으므로 다시 묻지 않는다. 백그라운드 작업은 없다.

이 세션의 제목은 `feature/01-contract-account-fields-forbidden-and-origin-check`에서 `... (인계함)`으로 바꿨고 워크트리 잠금은 풀었다.

open-session을 부른다 2026-11-25T07:34:13Z

## 셀프 리뷰(`/code-review`)

범위: 기준 `6b0646e80`, 수정 파일 29개, 미추적 2개(`src/agent_os/http/origin.py`, 이 일지), 커밋 0개. 표준 축은 `sonnet`·high, 명세 축은 이 세션의 모델로 돌렸다. 읽기만 하는 서브에이전트라 저장소는 바뀌지 않았다.

표준 축 보고(Critical·Major 없음). 판정은 이 세션이 코드와 ADR 원문을 열어 대 보고 내렸다.

- Minor, 고쳤다: `origin.py`가 `path in PUBLIC_PATHS`로 검사 밖을 정해, 티켓 03이 그 목록에 로그인 경로를 더하면 그 경로가 출처 검사에서 조용히 빠진다. ADR 0011 122행("다섯 가운데 `/health` 밖의 넷은 요청 출처 검사를 지난다")이 같은 뜻이다. `/health`를 이름(`_HEALTH_PATH`)으로 빼고 독스트링과 `http.md`에 이유를 적었다. 목록이 늘어도 그 경로가 검사를 받는 것을 고정하는 시험(`test_인증_없이_열린_경로의_목록이_늘어도_그_경로는_출처_검사를_받는다`, `PUBLIC_PATHS`를 시험 안에서 바꿔 봄)을 더했다.
- Minor, 고쳤다: 운영자 경로의 `Origin` 없는 `OPTIONS`가 401이라는 문서(`cors.py`, `http.md`)를 고정하는 시험이 없었다. `test_출처_머리가_없는_OPTIONS_는_검사를_지나_운영자_경로에서_인증의_401이다`를 더했다.
- Nit, 고쳤다: `dispatch`의 같은 반환을 둔 `if` 둘을 하나로 합쳤다. `http.md`의 새 항목 앞 빈 줄을 지웠다.
- Nit, 남겼다: `documented_errors(401, 403, ...)`를 라우트마다 적은 것(운영자 면 공통 묶음이 없다), `_reject_runtime_only`의 같은 모양의 사례 셋, 계정 이름이 맨 `str | None`인 것. 앞의 둘은 테스트가 전수로 막고 위험이 낮다. 계정 이름의 NewType은 ADR 0063이 패턴을 두지 않기로 정한 결정과 같은 줄이라 이 티켓에서 바꾸지 않는다.

명세 축 보고: 수용 기준 (a)~(e)에서 빠진 요구도 범위 넘침도 없다. 미들웨어 순서와 403 봉투에 `WWW-Authenticate`가 없는 것도 명세와 같다고 보고했다. 그 가운데 `Sec-Fetch-Site`·`Origin`이 빈 문자열이거나 대소문자가 다른 값을 모두 거절하는 것을 명세 표가 말하지 않는 보수적 해석이라고 짚었다(Minor 이하). 코드는 `==`로 견주므로 맞다. ADR 0011에 `Origin`이 든 preflight가 403이 된 사실을 적은 이력이 없다는 지적은 ADR 개정이라 사용자 승인이 필요해 이 티켓에서 쓰지 않았고, ADR 0062가 일반적으로 다룬다.

다시 돌린 것: `tests/test_server.py`(통과, 종료 0), `ruff check`·`ruff format --check`(종료 0). 나머지 검증 명령은 커밋의 pre-commit이 갈음한다.

인계 못함 셀프 리뷰 직전: `tools/open_session.ps1 -Action send` 호출이 자동 모드 분류기에 "Unsanctioned Communication" 사유로 거부됐다. 새 세션이 열리지 않았다. 거부를 돌아가지 않고 제목을 원래(`feature/01-contract-account-fields-forbidden-and-origin-check`)대로 되돌렸다. 워크트리 잠금은 풀린 채다(다시 잠그지 않는다). 이 세션이 셀프 리뷰부터 잇고, 컨텍스트는 자동 압축이 받는다.

## 커밋 전 검사가 부하로 막힌 일

커밋(pre-commit)을 다섯 번 시도했고 모두 pytest 단계가 빨갰다. 그 가운데 뒤의 셋은 웹 검증을 포함해 pytest 밖의 검사가 모두 통과했다. 실패는 이 변경이 건드리지 않은 `tests/channel/cli/test_interrupt.py`("Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다")와 `tests/tools/`의 몇 개(`test_rerun_runner.py` 등)였고, 시도마다 1~5개로 달랐다. 같은 시각에 다른 세션 셋이 pytest 워커를 8개씩 돌리고 있었다(rag-engine 워크트리 셋과 agent 워크트리 하나가 돌던 때에 워커가 64개였고 남은 메모리는 2GB였다). 앞 두 시도에는 메모리 부족 흔적도 있었다(윈도 오류 1455 "페이징 파일이 너무 작습니다", git "malloc failed", vitest 워커 종료 코드 `0xC0000409`). 실패한 파일 셋(`test_interrupt.py`, `test_rerun_runner.py`, `test_probe_kit.py`)을 단독으로 돌리면 84개가 447초에 모두 통과했다.

> 질문: 커밋 전 검사의 pytest 단계가 다섯 번 시도에서 한 번도 통과하지 못했습니다. 실패한 테스트는 이 변경이 건드리지 않은 `channel/cli`와 `tools/` 쪽이고, 방금 실패한 파일들을 단독으로 돌리니 84개가 모두 통과했습니다. 어떻게 진행할까요?
> 선택지: 부하가 줄 때까지 기다린다(다른 세션의 pytest가 끝나기를 기다렸다가 같은 커밋을 다시 시도합니다. 우회는 없지만, 한 번 시도에 약 25~35분이 걸렸고 언제 통과할지는 알 수 없습니다) / pytest 단계만 건너뛰고 커밋한다(`SKIP=pytest`로 이 커밋 하나에서만 pytest 단계를 뺍니다. 나머지 검사는 그대로 돌고, 전체 pytest는 PR의 CI가 깨끗한 환경에서 다시 돕니다. 건너뛴 사실은 일지와 PR 본문에 적습니다)
> 사용자: 부하가 줄 때까지 기다린다

기다린 뒤(시작 직전 다른 세션의 pytest 워커 16개, 남은 메모리 약 11.5GB) 여섯 번째로 시도했지만 pytest 단계가 또 빨갰다. 웹 검증(2000.6초)과 나머지 검사는 모두 통과했고 pytest는 2123.1초에 6개 실패, 8176개 통과였다. 실패는 `test_interrupt.py` 셋, `test_rerun_runner.py` 둘, `test_probe_kit.py` 하나로 앞 시도와 같은 시험들이다. 이 변경이 스테이지한 30개 파일에 `channel/cli`와 `tools/`는 없다. 대기열 0531(같은 `test_interrupt.py` 시험이 깨져 사용자가 `SKIP=pytest`로 넘긴 4회차 기록)과 306·332(부하에서 흔들리는 시간 시험)가 이 종류를 이미 다룬다. 기다리면 통과한다는 가정이 틀렸으므로 다시 물었다.

> 질문: 부하가 줄어든 뒤 번째(여섯 번째) 커밋 시도도 같은 테스트 여섯(`test_interrupt.py` 셋, `test_rerun_runner.py` 둘, `test_probe_kit.py` 하나)이 깨져 pytest 단계가 또 막혔습니다. 시작 직전 다른 세션의 pytest 워커는 16개, 남은 메모리는 약 11.5GB였습니다. 이 변경이 건드리지 않은 시험이고 대기열 0531에는 같은 시험이 깨져 사용자가 `SKIP=pytest`로 넘긴 선례가 있습니다. 어떻게 진행할까요?
> 선택지: pytest 단계만 건너뛰고 커밋한다(`SKIP=pytest`로 이 커밋 하나에서만 pytest 단계를 뺍니다. 나머지 검사는 이번에 모두 통과했습니다. 세 번째 시도에서는 8181개가 통과하고 하나만 실패했고, 실패 파일을 단독으로 돌리면 84개가 통과했습니다. 전체 pytest는 PR의 CI가 깨끗한 환경에서 다시 돌므로 그 결과로 확인합니다. 건너뛴 사실은 일지와 PR 본문에 적습니다) / 한 번 더 시도한다
> 사용자: pytest 단계만 건너뛰고 커밋한다 (Recommended)

따라서 기능 커밋 `4fa0e54fb`는 `SKIP=pytest`로 쳤다. 그 커밋의 pre-commit에서는 pytest 단계가 돌지 않았다. 대신 앞 시도들의 결과(세 번째 시도 8181 통과·1 실패, 첫 `run_checks.py` 판은 `test_router.py` 셋을 고친 뒤 그 파일 108개 통과)와 실패 파일 단독 실행(84 통과)이 근거였다. 이어 origin/dev를 합친 커밋 `c4730cb05`는 전체 게이트를 `SKIP` 없이 지나 pytest 단계가 `Passed (822.7s)`였으므로(통과한 시도는 개수를 찍지 않는다), 푸시한 머리 트리에는 pytest 통과 기록이 있다. 그 커밋에서 ruff 두 검사는 스테이지에 `.py`가 없어 `Skipped`였고 린트는 손으로 쳤다. 전체 pytest는 PR의 CI가 다시 돈다.

## PR 직전 리뷰

기준 `origin/dev`, 커밋 둘(기능 커밋 `4fa0e54fb`, origin/dev를 합친 커밋 `c4730cb05`). 합치기에서 `http.md`와 카나리아 명세 `http_rule_continuation_422.toml`의 글자 충돌 둘이 났고, 둘 다 dev 쪽 문장에 이 변경의 `origin` 모듈 언급과 최신 결과 줄을 얹어 풀었다. 합친 트리에서 관련 시험 네 파일이 872개 통과했고, 합치기 커밋의 pre-commit은 pytest까지 모두 통과했다(세 번째 시도. 앞 두 시도는 대기열 306·332 종류의 시간 시험 하나씩이 빨갰다).

- CodeRabbit CLI(`coderabbit review --agent --base origin/dev`)는 리뷰가 시작되지 못했다. `Rate limit exceeded`(포함된 리뷰 셋을 모두 썼고 좌석에 묶이지 않았다, 대기 약 9분). 다시 돌리면 한도를 하나 더 쓰므로 돌리지 않았고, 템플릿 규정대로 내장 `/security-review`와 `bug-perf-review`를 대신 돌렸다. `coderabbit auth status`의 `Seat:` 줄은 `not assigned`다.
- CodeRabbit 서브에이전트가 코드와 ADR을 직접 읽고 낸 Minor 하나: 출처 검사 문서가 "ADR 0011의 2026-11-15 이력"을 인용하는데 "다섯 가운데 `/health` 밖의 넷은 요청 출처 검사를 지난다"는 문장은 2026-11-24 이력(122행)에 있다. 판정: 오탐이다. 우리 문장은 "그 목록에 로그인·갱신 같은 경로가 들어와도 그 경로는 이 검사를 받는다"이고 이 근거는 2026-11-15 이력 113행("쿠키로 여는 경로와 로그인 경로는 요청의 출처도 본다")에 글자 그대로 있다. "넷"이라는 수는 우리 문장이 근거로 들지 않았다. 고치지 않았다.
- `/security-review`(식별 서브에이전트 하나, 코드만 읽음): 취약점 없음(확신 7 이상 0건, 검증 단계는 대상이 없었다). 따져 본 우회 입력은 머리 이름 대소문자, `Sec-Fetch-Site` 중복과 빈 값, `Origin` 빈 값, `Sec-Fetch-Site` 없음과 `Origin` 있음, `OPTIONS` preflight, 면제 경로의 경계(`/healthx`, `/health/`, `/end-userx`, `//end-user`), `request.url.path`와 `scope["path"]`의 차이(퍼센트 인코딩된 `?`·`#`, 면제 접두사로 시작하는 운영자 라우트가 없어 우회 불가), 미들웨어 순서, 403 봉투의 정보 노출, 이벤트 필드가 토큰을 싣는지다. `Origin` 없는 교차 출처 GET이 지나가는 것은 이 PR에 쿠키 로그인이 없고 인증이 `Authorization` 머리라 새 악용 경로가 아니라고 판정했다(쿠키 로그인은 뒤 티켓의 몫이다).
- `bug-perf-review`(기준 `6b0646e80`, 범위 파일 27개): Critical·Major 없음, Minor 하나와 Nit 하나. 서브에이전트가 직접 돌려 본 것은 `Origin: ""`·`Origin: null`·대문자 `Same-Origin`·`Origin`이 든 OPTIONS가 모두 403인 것, `_reject_runtime_only`가 `resume()` 뒤에 에이전트가 낸 이벤트도 막는 것(호출 자리는 `_feed` 하나, 계정 관련 시험 14개 통과), 출처 관련 `test_server` 23개 통과다. `channel/http/router.py`, `openapi.json`, 웹 파일은 열지 않았다고 적었다.
  - Minor(보류): 독스트링과 `http.md`의 "브라우저가 이 머리를 붙인다"가 조건 없는 닫힌 주장이다. 서브에이전트는 `Sec-Fetch-*`를 브라우저가 https와 localhost에만 붙인다고 기억하며(재 보지 않았다고 적었다), 평문 http로 선 관리 화면은 같은 출처의 쓰기에 `Origin`만 붙어 403이 된다고 짚었다. 판정: 이 세션도 재지 못했다. 단독 배포는 TLS 프록시가 받고(ADR 0056의 TLS 인증서 항목), 그 ADR은 프록시 없이 평문으로 잘못 발행하는 것을 "잃는 것"으로 적는다. 평문 http로 선 관리 화면을 지원할지는 ADR 0062가 정할 몫이라 이 티켓에서 문장을 더하지 않았고, 뒤 티켓(07·08)이 쿠키 로그인을 세울 때 브라우저로 재도록 아래 "다음"의 위험에 적는다.
  - 같은 지적이 짚어 고친 것: 독스트링이 "이 서버의 관리 화면 중계와 시험이 그런 프로그램(두 머리를 다 안 보낸다)"이라고 적었는데, 중계(Next `rewrites`, `web/apps/admin/next.config.ts`)는 브라우저가 낸 요청을 넘기므로 틀렸다. ADR 0062의 쿠키 프로브가 관리 화면 자신의 페이지가 보낸 요청이 서버에 `Sec-Fetch-Site: same-origin`으로 닿는 것을 보인다. `origin.py`의 그 문장을 "이 서버의 시험이 그런 프로그램이고 중계는 브라우저가 붙인 `Sec-Fetch-Site`를 단 채 온다"로 고쳤다. `http.md`와 다른 문서에는 같은 표현이 없다(저장소 전체 grep).
  - Nit(보류): `Sec-Fetch-Site`가 중복되면 `headers.get`이 첫 값만 본다. 브라우저는 이 머리를 한 번만 보내고 페이지 스크립트가 바꿀 수 없어 실제 경로가 없다.
## PR 645과 사진 비교

PR 645(`headRefOid` `bad9bcefb`)를 열고 `@coderabbitai review`를 남겼다. CodeRabbit은 `Review rate limited`(NEUTRAL)로 리뷰하지 못했고, `claude-review`는 SUCCESS였다. CI에서 `visual`(관리 화면 사진 비교)과 그것을 묶는 `verify`가 FAILURE였다. 로그를 읽으니 `organisms-rundetail--*` 이야기 열두 개가 1280과 320, 밝은 테마와 어두운 테마 넷씩 모두 빨갰고(예: 1280×2286 정답 대 1280×2388 결과), 나머지 이야기는 통과였다. 이 변경이 `RunDetail` 이야기의 시작 이벤트에 `requesting_account`를 채워 이벤트 항목에 "요청한 계정" 줄이 하나 더 서기 때문이다. 이 PR을 푸시하기 전에 로컬에서 `pnpm -C web visual:admin`을 치지 않았다(이야기를 바꾼 줄이 `RunDetail.stories.tsx`였는데 그 점검을 놓쳤다). 고침은 `pnpm -C web visual:admin:update`(Docker)로 정답 사진 48장을 다시 찍은 것이고 바뀐 파일은 모두 `organisms-rundetail--*`뿐이다. 결정 자리 이야기 한 장을 열어 "요청한 계정 requesting_account null" 줄이 시작 이벤트에 선 것을 눈으로 봤다.

## 회고

후보 5건, 판정은 승인 4건(모두 회차를 더하는 것), 기각 1건, 넘김 0건이다. 사용자에게 물을 것은 없다.

| 후보 | 판정 | 사건과 조건 | 간 자리 |
|---|---|---|---|
| 인계 열기를 분류기가 거부했다 | 승인, 회차 | 셀프 리뷰 직전 인계 열기가 "Unsanctioned Communication"으로 거부됐고 `인계 못함`을 적었다(위 "인계" 절). 열린 항목이 이미 처방한 사건이다 | `open-session-send-denied-despite-allow-rule` 16회차에서 17회차 |
| `인계 못함` 뒤에도 인계 계기가 다시 왔다 | 승인, 회차 | 백그라운드 커밋 호출 직후마다 계기가 왔고 `인계 못함`을 압축 뒤에도 요약이 들고 있어 넘기지 않았다 | `0518` 8회차에서 9회차 |
| 백그라운드 커밋 직후 계기가 끝 알림 전에 왔다 | 승인, 회차 | 위와 같은 사건이다. 이 항목은 계기를 내는 때가 다르다 | `handoff-trigger-before-background-commit-ends` 14회차에서 15회차 |
| 여러 세션의 pytest가 겹쳐 메모리가 모자랐다 | 승인, 회차 | 첫 두 커밋 시도가 윈도 오류 1455와 git "malloc failed", vitest 종료 코드 `0xC0000409`로 죽었다. 같은 시각 pytest 일꾼이 64개였다 | `run-checks-out-of-memory-with-parallel-sessions` 6회차에서 7회차 |
| 관리 화면 이야기를 바꾸고 사진 비교를 로컬에서 치지 않았다 | 기각 | `RunDetail.stories.tsx`를 바꿨는데 `pnpm -C web visual:admin`을 치지 않아 CI의 `visual`이 이야기 열두 개에서 빨갰다(위 "PR 645과 사진 비교"). `CLAUDE.md` 검증 명령 절이 이미 "`apps/admin`을 건드렸으면 그 앱의 것을 친다"고 적었고 CI의 `visual` 잡이 그 자리에서 막았다. 이미 있는 검사가 알린 것이라 기각이고, 이 대기열에 같은 사건을 센 항목도 없다 | 없음 |

승인한 네 항목 모두 회차 5 이상이라 `next-session` 결정표의 chore 배치 조건에 이미 든 것들이다. 이 세션은 반영하지 않는다. 이 PR은 계약 티켓이고 고칠 자리(`tools/hook_handoff.py`, `tools/run_checks.py`)가 이 변경과 겹치지 않는다.

일지에만 남기는 것:

- 부하에서만 빨간 시간 시험(`test_interrupt.py` 셋, `test_rerun_runner.py` 둘, `test_probe_kit.py` 하나)이 커밋 시도 여섯 번을 막았다. 대기열 0306 종류(부하에서 흔들리는 시간 시험)라 받아들인 종류다. 규칙대로 새 항목도 회차도 더하지 않는다. 사용자가 `SKIP=pytest` 한 번을 허락했고(위 "커밋 전 검사가 부하로 막힌 일") 그 선례는 0531이다.
- 만료할 항목은 없다(`tools/queue_open_rows.py`의 "만료할 항목"이 비었다).

## 다음

이 PR을 병합하면 admin-login의 다음 티켓은 02·07·08이 서로 막지 않고 나란히 돌 수 있다(`.scratch/admin-login/issues/`의 `02-account-tables-and-system-admin-command.md`, `07-conversation-list-route.md`, `08-design-system-icons-and-account-badge.md`). 03은 02 뒤다.

남긴 위험:

- 평문 http로 선 관리 화면에서 같은 출처의 쓰기 요청이 403이 되는지 실제 브라우저로 재지 못했다. 브라우저는 `Sec-Fetch-*` 머리를 https와 localhost에만 붙인다는 것이 서브에이전트의 기억이고 재 본 값이 아니다. 쿠키 로그인을 세우는 티켓 07·08 이후(03, 09)가 브라우저로 먼저 잰다. 단독 배포는 TLS 프록시가 받으므로(ADR 0056) 영향이 없을 것으로 보지만 확인한 것은 아니다.
- ADR 0011에 `Origin`이 든 preflight가 403이 된다는 이력이 없다. ADR 개정이라 사용자 승인이 필요해 쓰지 않았다. 뒤 티켓이 ADR을 건드릴 때 초안을 보여 주고 승인을 받는다.
- `.claude/rules/http.md`, 카나리아 명세 `http_rule_continuation_422.toml`, `.scratch/plan.md`는 나란히 도는 다른 티켓과 글자 충돌이 날 수 있다. 병합 직전에 `origin/dev`를 합칠 때 풀어야 한다.
