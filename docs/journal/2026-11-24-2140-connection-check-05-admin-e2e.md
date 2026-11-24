# 2026-11-24 (21:40) connection-check 티켓 05 관리 화면 e2e의 접속 확인 장면

브랜치 `feature/05-admin-e2e-scene-for-connection-check`, 워크트리 `.claude/worktrees/05-admin-e2e-scene-for-connection-check`. 모델 Sonnet 5.5(지시문의 high). 기준은 `origin/dev`(767a9be59)이고 앞 일지 `2026-11-24-1652-connection-check-04-plugin-list.md`의 "다음"이 가리킨 티켓 05를 구현한다. 04(PR #631)가 병합됐고 06(배포 안내의 문제 해결 절)이 나란히 돈다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/connection-check/issues/05-admin-e2e-scene-for-connection-check.md
>
> 다음 작업: .scratch/connection-check/issues/05-admin-e2e-scene-for-connection-check.md. 관리 화면 e2e에 실제로 붙는 원격 MCP 서버와 닿지 않는 모델의 행을 보는 장면을 더한다
> 이번 요청 범위: PR과 병합까지

## 한 일

- 준비(`web/apps/admin/e2e/stack.ts`): 저장소의 시험용 원격 MCP 서버(`tests/mcp_http_server.py`)를 이 준비가 따로 띄운다. 어댑터 시험이 쓰는 `tests/mcp_http.py`의 `serving`은 파이썬 시험용 컨텍스트 매니저라 쓰지 않고, 같은 서버 파일을 `launch`로 띄워 다른 프로세스처럼 끝에 거두고 출력을 `test-results/remote-mcp.log`에 남긴다. 포트는 `freePort()`가 잠깐 열었다 닫은 번호로 받고, 서는 것은 TCP 접속으로 기다린다.
- 픽스처 둘을 임시 플러그인 루트에 쓴다. 원격 MCP `remote-docs`(`transport = "http"`, 주소는 띄운 서버)와 `openai-compatible` 모델 `offline-model`(주소는 같은 방식으로 잠깐 열었다 닫은 포트). 어느 에이전트도 쓰지 않는다. 이름에 다른 장면이 찾는 `fixture`·`sonnet` 같은 글자가 들지 않게 했다(`row()`가 글자 포함으로 행을 찾는다).
- 장면(`e2e/connection-check.e2e.ts`의 둘째 장면): 관리 토큰을 넣고 플러그인 화면을 열면 `remote-docs` 행의 상태 영역이 정확히 `붙음`이고(`toHaveText`), 그 행에 `접속 확인` 버튼이 없다. `offline-model` 행의 상태 영역에 `붙지 못함`과 `서버에 닿지 못했다`가 든다. 기다리는 시간은 25초다(기한 10초와 중계를 넘고 30초 간격은 안 넘는다). 04가 앞질러 더한 첫 장면은 그대로 두고 같은 파일에 합쳤다.
- 위젯·위젯 테스트 페이지·단독 배포 e2e가 함께 쓰는 `web/packages/e2e-stack`은 건드리지 않았다. 그래서 그 e2e들은 돌리지 않았다.

## 빨강과 변이

모두 `pnpm -C web/apps/admin exec playwright test e2e/connection-check.e2e.ts`를 손으로 쳐서 출력 로그를 읽은 것이다.

- 준비 없이 새 장면만 먼저 쳐서 빨강을 봤다(`remote-docs` 행의 상태 영역을 25초 안에 찾지 못함, 첫 장면은 통과).
- 준비를 더한 뒤 둘 다 통과했다(둘째 장면 2.9초).
- 변이: 모델 픽스처의 주소를 닫힌 포트에서 떠 있는 원격 MCP 서버의 포트로 바꾸고 쳤다. 모델 행이 `서버가 오류로 답했다(HTTP 404)`를 보이고 `서버에 닿지 못했다` 단언이 빨개졌다. 되돌렸다(되돌린 줄은 `grep`으로 읽었다). 원격 MCP 쪽은 서버를 안 띄우는 변이를 따로 치지 않았고, 준비 없이 친 빨강이 그 몫이다.

## 이 장면이 실제로 본 것(명세 Further Notes의 "재지 않은 것" 대조)

- 실제 `serve`와 실제 관리 화면 중계를 지나, 떠 있는 streamable HTTP 서버에 대한 접속 확인이 첫 확인으로 `붙음`을 보인다(장면 2.9초, 가짜 서버가 저장소의 시험용 서버라 제3자의 실제 MCP 서버는 아니다).
- 닫힌 포트를 가리키는 `openai-compatible` 모델의 `서버에 닿지 못했다`가 어댑터의 글에서 화면의 행까지 그대로 닿는다(`http://127.0.0.1:<포트>/v1`이 `붙지 못했다` 문장에 들어 보이는 것까지는 보지 않았다).
- 재지 않은 것: 원격 MCP 서버가 확인 한 번에 받는 요청의 수(서버의 기록 파일은 임시 폴더에 있어 장면이 끝나면 지워진다. 읽는 코드를 쓰지 않았다). 중계의 30초 제한에 닿았을 때 화면에 오는 것. 04가 남긴 브라우저 연결 여섯 개 상한과 응답 처리가 끝났음을 알리는 표지를 정하는 일(느린 가짜 상류가 있어야 한다. 이 티켓의 체크박스가 아니라 만들지 않았다).

## 수락 조건 대조(명세 "수락 조건을 덮는 자리")

일부러 깨뜨린 배포 셋을 덮는 시험이다.

| 깨뜨린 모양 | 덮는 시험 | 수준 |
|---|---|---|
| 모델 서버 꺼짐 | `tests/adapters/test_model_check.py`의 `test_openai_compatible_닫힌_포트는_서버에_닿지_못했다이다`와 `test_anthropic_닫힌_포트는_서버에_닿지_못했다이다` | 이유 글 |
| 모델 서버 꺼짐, 화면까지 | 이 티켓의 둘째 장면(`openai-compatible`만) | 실제 `serve`·중계·화면의 행 |
| MCP 서버 꺼짐 | `tests/adapters/test_mcp.py`의 `test_닫힌_포트의_원격_서버는_연결_오류의_글로_Unreached다` | 이유 글 |
| 토큰 불일치 | `tests/adapters/test_mcp.py`의 `test_틀린_토큰의_원격_서버는_글_끝에_HTTP_401이_붙은_Unreached다` | 이유 글 |

꺼진 MCP 서버와 토큰 불일치를 화면의 행까지 잇는 장면은 없다. 명세가 이 장면에 맡긴 것이 닿지 않는 모델 하나이기 때문이다.

## e2e 결과

`pnpm -C web/apps/admin exec playwright test`(11개, 손으로 쳐서 출력을 읽었다): 10개 통과, 1개 실패. 실패한 것은 04 일지가 적은 `decision.e2e.ts`의 첫 장면(`run_finished`가 5초 안에 안 보임)이다. 04 일지는 기준 상태에서도 같은 곳에서 빨갰다고 적었다(그 일지를 읽었다. 이 세션이 기준 상태에서 다시 쳐 보지는 않았다). 이번 로그가 더 보여 주는 것: 이벤트 칸에는 `run_started`(12:40:12)와 `run_paused`(12:40:15)만 있다. 시작에서 멈춤까지 3초가 걸렸다. 그 장면의 에이전트는 stdio 픽스처 서버를 띄워 도구를 부르므로 그 기동이 3초쯤이고, 재개 때 서버를 다시 띄우는 몫(어림 3초)에 에이전트의 2초 잠을 더하면 5초 상한을 넘는다고 어림한다. 이 PC의 부하나 기동 속도 탓일 수 있다. 원인은 가르지 못했고 이 티켓이 고치지 않는다. CI의 `e2e` 잡이 PR #631에서 통과했다고 04 일지가 적었다(그 일지를 읽었다. 그 잡이 이 장면을 돌렸는지는 가르지 못했다고 같은 일지가 적는다).

## 보지 못한 것

- 가짜 키가 아니라 진짜 키를 가진 셸에서의 `serveEnv`는 04가 이미 적은 대로다. 이 티켓은 그 길을 바꾸지 않았다.
- 원격 MCP 서버의 행이 30초 뒤 다시 확인하는 것은 보지 않았다(티켓이 첫 확인만 보라고 한다).

## 셀프 리뷰(`code-review`, 이어받은 세션)

범위: base `767a9be59`, 파일 4개(추적 3, 미추적 1: 이 일지), 커밋 0개. 표준 축과 명세 축 서브에이전트 둘이 돌았다. Critical·Major는 없었다.

고친 것:

- 장면의 제한 시간. 시험의 기본 상한 30초 안에 첫 대기(25초)와 둘째 단언이 함께 들지 않는다. 실패가 단언의 글이 아니라 시간 초과로 보일 수 있어 둘째 장면 앞에 `test.setTimeout(2 * FIRST_CHECK_MS)`를 더했다. 평소에는 두 확인이 함께 나가 앞서 잰 대로 둘째 장면이 2.9초에 끝난다(구현 시점에 손으로 쳐서 본 값이다. 이 수정 뒤 값은 아래 e2e 결과에 적는다).
- `stack.ts`의 낡은 주석 셋. `freePort` 설명("닫은 뒤 곧바로 관리 화면이 가져간다")은 이제 가짜 원격 MCP 서버와 닫힌 모델 주소에도 쓰이는 것을 적는다. "두 프로세스의 출력은 끝에 `test-results/`에 남긴다"는 `serve`·관리 화면·가짜 원격 MCP 서버로 고쳤다. 머리의 픽스처 설명에 접속 확인 장면의 서버 둘을 더했다.

남긴 것(이유):

- `closedPort`가 뒤에 받는 관리 화면 포트와 같은 번호가 될 가능성. 운영체제가 방금 닫힌 번호를 곧바로 다시 주는 일은 드물다고 어림한다(재 보지 않았다). 겹치면 모델 행이 `서버에 닿지 못했다` 대신 HTTP 404를 보인다는 것은 앞 "빨강과 변이"의 변이에서 본 것(주소를 떠 있는 서버의 포트로 바꿨을 때)이고, 그때 장면이 빨개졌다. 티켓이 요구한 것("정해 둔 번호에 기대지 않는다")은 채웠다.
- `remote-mcp` 프로세스가 이 셸의 환경 전체를 물려받는 것. 시험용 서버(`tests/mcp_http_server.py`)에 환경 변수를 읽는 줄이 없다(`grep -n "environ\|getenv\|os.env"`가 빈 결과였다). 데이터베이스를 만드는 호출(`spawnSync`)도 같은 환경을 쓴다.
- 원격 MCP 쪽의 변이(서버를 안 띄우는 것). 티켓 칸이 변이를 요구하지 않고, 준비 없이 친 빨강이 그 몫이다.
- `접속 확인` 버튼이 없다는 단언(`toHaveCount(0)`)은 티켓 칸에 없지만 명세 "스스로 하는 확인"에 맞아 두었다.

다시 돌린 것: 리뷰 반영 뒤 `pnpm -C web/apps/admin exec playwright test`를 손으로 쳤다(출력을 파일로 받아 읽었다, 4.0분). 11개 가운데 10개 통과, 1개 실패. 실패는 앞과 같은 `decision.e2e.ts:12`의 첫 장면(`run_finished`가 안 보임)이고 이 변경이 닿는 코드가 아니다. 접속 확인 장면은 둘 다 통과했다(첫 장면 800ms, 둘째 장면 3.7초). 나머지 게이트는 커밋의 pre-commit 결과로 갈음한다.

## 인계(셀프 리뷰 직전에 넘긴다)

이 세션의 제목은 `feature/05-admin-e2e-scene-for-connection-check`였다(넘기며 `(인계함)`을 붙인다). 컨텍스트가 인계 문턱을 넘은 채 셀프 리뷰 직전에 왔다. 커밋하지 않았고 변경은 모두 이 워크트리에 있다. 새 세션이 같은 파일을 이어 쓰고 커밋한다.

### 이 세션이 한 것(저장소로 알 수 없는 것만)

- `tidy-checkouts`를 먼저 돌았다. 루트를 `origin/dev`(767a9be59)로 당겼고(깨끗했고 앞선 커밋 없음), 병합된 워크트리 일곱과 그 브랜치를 지웠다. 휴지통(`.claude/worktrees/.tidy-trash/`)에 `node_modules` 몇 개가 남았다. 다른 세션의 `node.exe`·`esbuild.exe`가 `.pnpm` 안의 `esbuild.exe`를 쥐고 있어 지우지 못했고, 다음 정리가 다시 비운다. 지금 루트는 dev이고 깨끗하다. 그래서 새 세션 지시문에 "주 체크아웃 미갱신" 줄이 필요 없다.
- 워크트리 `05-admin-e2e-scene-for-connection-check`에 들어가 `origin/dev`에서 브랜치 `feature/05-admin-e2e-scene-for-connection-check`를 땄다. `uv sync`와 `pnpm -C web install --frozen-lockfile`을 쳤다. 테스트 컨테이너(`compose.test.yaml`)가 떠 있다.
- 티켓 05의 `Status:`를 `in-progress`로 바꿨다. "픽스처", "장면", "일지에 남길 것" 열한 칸을 체크했다. "기능을 닫는 일"과 "검증"은 남겼다.
- 위 "한 일", "빨강과 변이", "이 장면이 실제로 본 것", "수락 조건 대조", "e2e 결과"는 구현을 마친 시점의 일이다. 관리 화면 e2e 11개 가운데 10개가 통과했고 실패 하나는 04가 적은 `decision.e2e.ts`의 첫 장면이다. prettier와 eslint는 바뀐 e2e 두 파일만 쳐서 통과했다(손으로 쳤다).
- `sync-design-system 확인`은 하지 않았다. 웹 편집 훅이 `web/apps/admin/e2e/connection-check.e2e.ts`를 고친 직후 알렸으나, 이 변경은 e2e 시험 파일과 준비 코드뿐이고 화면 부품이나 `web/packages/ui`는 건드리지 않았다. 새 세션이 화면 코드(예: 아래 04에서 넘어온 `LaunchedConnection`)를 고치게 되면 그 전에 `/sync-design-system 확인`을 한다.

### 남은 것

1. 셀프 리뷰: Skill 도구의 `code-review`. 고정점은 `origin/dev`의 merge-base(지금 `767a9be59`, 커밋은 0개)이고 미추적 파일은 이 일지 하나다. 추적 파일 변경은 셋이다(`web/apps/admin/e2e/stack.ts`, `web/apps/admin/e2e/connection-check.e2e.ts`, 티켓 05 파일). 명세는 티켓 05, `.scratch/connection-check/spec.md`(Testing Decisions 넷째), ADR 0067이다.
2. Critical·Major를 고치고 고친 문장은 이 일지에 원문으로 옮긴다. 고쳤으면 e2e를 다시 친다(`pnpm -C web/apps/admin exec playwright test`, 약 1.3분, 빌드 포함. 파이프 없이 파일로 리다이렉트).
3. 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`(1로 끝나면 출력대로). 커밋은 티켓을 `done`으로 바꾼 것과 같이 한다. `Status:`를 `done`으로 바꾸고, 검증 칸 둘의 체크는 커밋의 pre-commit 결과로 채운다(칸의 뜻은 티켓). 그 뒤 `uv run python tools/plan_table.py`는 이 PR이 마지막이 아니면 바뀌는 것이 없다.
4. "기능을 닫는 일"은 병합 직전에 판정한다. 이 인계 시점에 `origin/dev`의 06 티켓은 `ready-for-agent`이고 06 세션이 따로 돈다(워크트리 `.claude/worktrees/06-deploy-guide-troubleshooting-section`, 병합된 PR 없음). 06이 먼저 병합되면 이 PR이 마지막이라 `**끝:**` 줄, 기능 단락 `docs/release-notes/features/connection-check.md`, `plan_table.py`로 돌린 `.scratch/plan.md`를 같은 커밋에 싣는다. 이 PR이 먼저 병합되면 병합 뒤 `git fetch origin`으로 06을 다시 본다.
5. PR 직전 `coderabbit-review`(CLI가 못 돌면 `bug-perf-review`), `git-pr`로 PR(본문 끝 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`), `mcp__ccd_pr__get_status`와 `bind_pr`, 봇 회차와 병합은 워크트리 사본의 `next-session` `merge.md`. 마지막 봇 회차의 커밋에 이 일지의 마무리를 싣는다. CI의 python 잡이 15분 제한에 닿아 취소되면 단계 시각으로 가르고 `gh run rerun <실행> --failed`만 한다.
6. 단계를 닫을 때 `retro`를 돈다. 일지의 `## 다음`은 이 세션이 쓰지 않았다. 닫는 세션이 쓴다.

### 04에서 넘어온 일(이 세션은 컴포넌트를 만지지 않았다)

04 병합 때 둘째 회차의 Minor 둘이 05로 넘어왔다(PR #631 코멘트 `#issuecomment-7130650536`). 이 세션은 `LaunchedConnection`과 `RowConnection`을 열지 않았다. 둘 다 티켓 05의 체크박스가 아니라 이 장면 작업이 컴포넌트를 만지지 않아 하지 않았다. 새 세션이 컴포넌트를 만지게 되면 함께 하고, 아니면 일지의 `## 다음`에 다시 적어 넘긴다.

- `LaunchedConnection`의 불리언 둘(`enabled`·`pending`)을 열거로 바꾸는 일.
- 응답이 `not_applicable`일 때 행이 `확인하는 중`으로 남는 갈래의 화면을 명세로 정한 뒤 시험 사례를 더하는 일. 04가 이 동작을 "명세 4"로 남겼다(04 일지의 "남긴 것").
- 04 일지가 넘긴 "느린 가짜 상류" 일(브라우저의 연결 여섯 개 상한과 응답 처리 시점)은 이 티켓의 체크박스가 아니라 만들지 않았다.

open-session을 부른다 2026-11-24T12:43:10Z
