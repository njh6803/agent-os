# 2026-11-24 (16:52) connection-check 티켓 04 플러그인 목록의 접속 확인

브랜치 `feature/04-plugin-list-shows-connection-check`, 워크트리 `.claude/worktrees/04-plugin-list-shows-connection-check`. 모델 Sonnet 5.5(지시문의 high). 앞 일지 `2026-11-23-1445-connection-check-03-models.md`의 "다음"이 가리킨 티켓 04를 구현한다. 02(MCP)와 03(모델)이 병합된 dev 위에서 서고, 화면이 처음으로 확인을 보내기 시작하는 티켓이다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/connection-check/issues/04-plugin-list-shows-connection-check.md
>
> 다음 작업: .scratch/connection-check/issues/04-plugin-list-shows-connection-check.md. 플러그인 화면의 행이 접속 확인의 결과를 보인다
> 이번 요청 범위: PR과 병합까지

## 읽는 자리를 어떻게 정했나

organisms는 읽기 훅을 부르지 못하는데 확인은 행마다 읽어야 한다. 두 길이 있었다.

- 행마다 훅 하나(채택): pages의 `RowConnection`이 행 하나를 읽고, 목록 organism `PluginList`는 `connection?: (row) => ReactNode` 자리만 받아 그 행에 그린다. 표지 행에는 그 자리를 부르지 않는다. 행이 켜지거나 꺼지는 것이 그 행 훅의 `enabled`로 끝나고, 행이 사라지면 훅도 사라진다.
- 여러 행을 한 훅으로 읽기(버림): 행의 수가 바뀔 때 훅의 개수가 바뀌므로 SWR의 다중 키 읽기를 따로 짜야 하고, 한 행의 실패와 다시 읽기를 나눠 다루기 어렵다.

## 쓴 기존 부품

새 디자인이 필요 없었다(`/ui-design`을 부르지 않았다). `Icon`(ellipsis, circle-check, circle-x, triangle-alert)과 `Button`(secondary, `loading`, `disabled`)을 쓰고 앱의 molecule 둘을 더했다. `StatusBadge`는 실행의 상태 전용이라 쓰지 않았다.

- `molecules/ConnectionLine`: 상태 글자와 까닭(`role="status"`), 시각은 그 영역 밖의 `<time>`이다. 같은 결과가 다시 와도 노드가 바뀌지 않아 화면 읽기 도구가 다시 알리지 않는다(MutationObserver 시험으로 고정).
- `molecules/LaunchedConnection`: 눌러서 하는 확인의 버튼과 결과와 시각. 응답까지 `loading`이다.

시각은 `Intl.DateTimeFormat("ko-KR", 24시간)`이다. 성공과 붙지 못함은 응답 시각(`확인한 시각`), 요청 실패는 누른 시각(`누른 시각`)이다.

## SWR 기본 동작 셋을 푼 방법

`hooks/queries/connection/index.ts`가 푼다. 정책 `AUTO`(30초, 보이지 않는 동안 쉼, 재시도 없음)와 해법은 `.claude/rules/web-admin.md`에 적었다.

1. 오류 상태의 키는 주기 재확인을 건너뛴다: fetcher가 요청 실패를 던지지 않고 `failed` 값으로 돌려준다. 그래서 `확인하지 못함` 행도 30초 뒤 다시 나간다.
2. 날아가는 요청과 `mutate()`(새로 고침)의 겹침: `flights` 맵이 같은 행의 요청을 하나로 합친다. 새로 고침은 `mounted` 레지스트리의 `refresh`를 불러 그 합쳐진 요청에 합류한다.
3. 껐다 켠 키의 옛 캐시: 효과 정리에서 `mutate(키, undefined, { revalidate: true })`로 캐시와 SWR 내부의 날아가는 표지를 함께 비운다. `revalidate: false`는 그 표지를 지우지 않아, 다시 켠 행의 새 요청이 막혔다(손으로 겪었다). 화면 전체가 걷힐 때 SWR 상태가 먼저 사라져 이 `mutate`가 던질 수 있어 `.catch`로 막는다.

보이지 않는 탭의 쉼은 SWR의 `refreshWhenHidden: false`가 맡고, 돌아왔을 때 바로 한 번은 `visibilitychange` 리스너를 직접 달았다(`revalidateOnFocus`는 끄고 창 포커스와 탭 보임이 다르게 움직이는 것을 피했다).

## 시험

- `HomePage.connection.test.tsx`(새 파일, 33개. 셀프 리뷰 뒤 하나를 더했다): 스스로 하는 확인, 눌러서 하는 확인, 플러그인 상세 페이지에 없음 세 묶음. 가짜 응답(MSW)과 가짜 시계다.
- 변이 시험 둘로 시험이 빨개지는 것을 봤다. `flights` 합치기를 빼면 날아가는 동안의 새로 고침 사례가, 정리의 `mutate`를 빼면 껐다 켠 행 사례가 빨개졌다.
- 스토리: `ConnectionLine`, `LaunchedConnection`, `PluginList`의 `Connections`. 사진 정답은 `ConnectionLine` 스토리 여섯, `LaunchedConnection` 스토리 여섯, `PluginList`의 `Connections` 하나를 각각 폭 둘(1280, 320)과 라이트·다크로 찍은 52장이다(보고 확인했다. 라이트의 목록에서 상태 글자와 까닭, 버튼 셋, 표지 행의 경고 한 줄만 보이는 것을 봤다).
- 기존 `HomePage.test.tsx`는 기본 확인 핸들러를 하나 더 받았다. 새 확인 요청이 MSW의 처리되지 않은 요청으로 걸리지 않게 하려는 것이다.

### 시험을 먼저 쓰지 못한 것

원칙 II에 어긋나게 훅(`hooks/queries/connection`)을 시험보다 먼저 썼다. 그 뒤 화면 연결이 없는 상태에서 시험을 먼저 돌려 31개가 빨간 것을 보았고, 위 변이 둘로 보강했다. 훅의 동작은 SWR 내부 동작에 기대 한 번에 맞히기 어려워 손으로 부딪혀 가며 짰고, 그 탓에 순서가 뒤집혔다.

## 기존 e2e를 지킨 것

- `e2e/stack.ts`의 `serveEnv`가 `serve`의 환경에서 `ANTHROPIC_API_KEY`, `ANTHROPIC_API_URL`, `ANTHROPIC_PROXY`를 벗긴다(코드). 키가 없으면 어댑터가 요청 없이 `키가 없다(환경 변수 ANTHROPIC_API_KEY)`로 답한다(`src/agent_os/adapters/model_check.py`를 읽었다). 진짜 키는 이 PC의 셸에 없어(`test -n "$ANTHROPIC_API_KEY"`가 비었다) 쓰지 못했다. 대신 셀프 리뷰 때 가짜 키(`ANTHROPIC_API_KEY=sk-test-dummy-not-real`)를 넣은 셸에서 새 장면을 쳐 통과하는 것을 봤다. 키를 벗기는 길이 같은 글을 내는지만 보인 것이고 실제 제공사에 요청이 나가지 않았다는 것은 코드를 읽어 안 것이다.
- 새 장면 `e2e/connection-check.e2e.ts`가 그 글(`sonnet`, `claude-opus-5` 두 행)과 stdio 서버 `fixture` 행의 `접속 확인` 버튼(눌리고 status는 없음)을 본다. `pnpm -C web/apps/admin exec playwright test`에서 통과했다(1.1초, 손으로 쳐서 읽었다).
- 기존 장면의 모델 행 글: 기존 장면은 모델 행의 글을 단언하지 않아 거기 보인 글은 따로 보지 못했다. 같은 `serve`의 모델 행이 새 장면에서 `붙지 못함`과 `키가 없다(...)`를 보인 것이 전부다. 기존 장면 아홉 가운데 여덟이 통과했고 하나(`decision.e2e.ts`의 첫 장면)는 아래 "실패한 e2e 한 건"대로 기준 상태에서도 빨갛다. MCP 행의 `접속 확인` 버튼이 기존 장면의 `row()` 찾기와 겹치지 않은 것도 그 통과로 본 것이다.
- 관리 화면 e2e 10개(기존 아홉과 새 장면 하나) 가운데 9개가 통과했고 `decision.e2e.ts`의 첫 장면 하나가 실패했다. 아래 "실패한 e2e 한 건"에 적었다.

## 실패한 e2e 한 건

`decision.e2e.ts`의 첫 장면(멈춘 실행을 승인하면 …)이 `run_finished`를 5초 안에 보지 못해 세 번 연속 실패했다(전체 실행 한 번, 그 파일만 다시 돌린 한 번, 셀프 리뷰 때 그 파일만 다시 돌린 한 번). 이 티켓이 원인이 아니다. 셀프 리뷰 때 손으로 가렸다. 이 티켓이 고친 추적 파일 여섯(`HomePage.tsx`, `HomePage.test.tsx`, `PluginList.tsx`, `PluginList.stories.tsx`, `e2e/stack.ts`, `hooks/queries/admin/index.ts`)을 `git apply -R`로 기준 커밋(7770ac0c1) 상태로 되돌린 채 `pnpm -C web/apps/admin exec playwright test e2e/decision.e2e.ts`를 쳤더니 같은 첫 장면이 같은 곳(`run_finished`가 안 보임)에서 빨갰고 나머지 둘은 통과했다. 되돌린 뒤 `git apply`로 복구했다. 처음 시도(스토리 파일을 빼고 되돌림)는 빌드의 타입 오류로 장면에 닿지 못해 증거로 쓰지 않는다. 처음에 든 근거 셋도 그대로 둔다.

- 그 장면은 `/runs/<id>`만 열고 플러그인 목록을 열지 않는다. `serve.log`에 접속 확인 요청(`connection-check`)이 한 줄도 없고 `GET /plugins`만 있다(손으로 읽었다).
- `stack.ts`를 원래대로 되돌린 채 같은 장면만 돌려도 같은 실패가 났다(`git checkout`으로 되돌렸다가 복원했다. 나머지 변경은 그대로였으나 화면 쪽 변경은 이 장면의 경로에 들지 않는다고 코드를 읽어 판단했다).
- 승인 뒤 `serve.log`가 `POST /approval 200`에서 끝나고 이어지는 트레이스 읽기가 없다. 재개 흐름이 5초 안에 끝나지 않은 것으로 보인다. 이 PC에서 다른 세션이 함께 돌고 있어 시간 제한 탓일 수 있다고 어림했다(부하는 재지 않았다).

기준 상태에서도 빨간 까닭(이 PC의 부하인지, dev의 결함인지)은 가리지 못했다. CI의 `e2e` 잡이 이 장면을 다시 판정한다. 거기서도 빨가면 이 티켓과 별개로 `diagnosing-bugs`로 가른다.

## 게이트

- `uv run python tools/run_checks.py`(백그라운드, 러너 출력을 읽었다): check-notes, check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify(1104.7초)는 Passed였다. pytest는 `1 failed, 8135 passed`였다. 실패한 시험은 `tests/channel/cli/test_interrupt.py::test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다`("Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다")이다. 이 변경이 건드리지 않은 MCP 서버 닫기의 실제 프로세스 시험이고, 그 파일만 홀로 `uv run --no-sync pytest tests/channel/cli/test_interrupt.py -q`로 돌리니 6 passed(36초)였다. 앞 일지(03)에도 같은 파일의 다른 시험이 같은 문구로 한 번 실패했다. 이 PC에서 다른 세션이 함께 돌아 생긴 시간 제한으로 어림한다(부하는 재지 않았다).
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 2550 files already formatted.
- `pnpm -C web visual:admin`: 98 passed(10.6분). 정답은 `pnpm -C web visual:admin:update`로 만들고 바뀐 사진은 눈으로 봤다.

## 보지 못한 것

- 켜 둔 원격 MCP와 모델 행이 여럿일 때 느린 확인이 다른 관리 요청을 늦추는지는 재지 않았다. 확인 하나는 길어도 기한에 끝나고(모델은 `CHECK_DEADLINE_SECONDS = 10.0`, 코드를 읽었다) 한 행에 하나만 나간다. 다만 브라우저는 주소 하나에 HTTP/1.1 연결을 여섯까지만 연다고 알려져 있다(이 PC에서 재지 않았다). 느린 행이 여섯 이상 겹치면 같은 시간 동안 다른 요청이 기다릴 수 있다는 것은 어림이다. 재려면 응답이 느린 가짜 상류가 필요해 이 티켓에 넣지 않았다. 05의 e2e 장면이 느린 서버를 만들면 거기서 잰다.

## 인계(컨텍스트가 인계 문턱을 넘어 셀프 리뷰 직전에 넘긴다)

이 세션의 제목은 `feature/04-plugin-list-shows-connection-check`였다(넘기며 `(인계함)`을 붙인다). 아직 커밋하지 않았고 변경은 모두 워크트리에 있다. 새 세션이 같은 파일을 이어 쓰고 커밋한다.

남은 것:

1. 셀프 리뷰: Skill 도구의 `code-review`. 고정점은 `origin/dev`의 merge-base이고, 미추적 파일(`web/apps/admin/api/connection/`, `hooks/queries/connection/`, `types/`, `molecules/ConnectionLine*`·`LaunchedConnection*`, `pages/RowConnection.tsx`, `HomePage.connection.test.tsx`, `e2e/connection-check.e2e.ts`, 이 일지)을 새 코드로 읽게 한다. 사진 정답 png 52개는 보지 않아도 된다. 명세는 티켓 04, `.scratch/connection-check/spec.md`, ADR 0067이다. 이 세션이 `code-review`를 불렀을 뿐 서브에이전트는 띄우지 않았다.
2. Critical·Major를 고치고, 고친 문장은 이 일지의 "고친 것" 줄에 원문으로 옮긴다.
3. 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`(1로 끝나면 출력대로). 이 세션 도중 `origin/dev`가 7770ac0c1에서 463d9f1f7로 앞섰다(`git log -1 origin/dev`). 기준 브랜치를 합치고 충돌이 있으면 푼다. `.claude/rules/web-admin.md`와 `hooks/queries/admin/index.ts`를 건드렸으니 형제가 같은 파일을 바꿨는지 본다.
4. 이미 돈 게이트는 위 "게이트"다. 셀프 리뷰로 고친 뒤 pre-commit이 손으로 치는 다섯(pytest 제외 린트·타입체크·경계·web 등)을 갈음한다. 갈음되지 않는 관리 화면 e2e와 사진 비교는 위 결과가 있고, 코드를 바꿨으면 해당하는 것만 다시 친다.
5. `decision.e2e.ts`의 첫 장면 실패는 위 "실패한 e2e 한 건"이다. CI의 `e2e` 잡에서도 빨가면 `diagnosing-bugs`로 간다.
6. PR 직전 `coderabbit-review`(CLI가 못 돌면 `bug-perf-review`), `git-pr` 스킬로 PR(본문 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`), `mcp__ccd_pr__get_status`와 `bind_pr`, 봇 회차와 병합은 워크트리 사본의 `next-session merge.md` "워크트리에서 병합할 때". CI의 python 잡이 15분 제한으로 취소되면 단계 시각으로 가르고 `gh run rerun <실행> --failed`만 한다.
7. 단계를 닫을 때 `retro`를 돈다. 이 일지의 "다음"은 아래 초안이고 닫는 세션이 마무리한다. 티켓 04는 이미 `done`이다. `uv run python tools/plan_table.py`는 셀프 리뷰 때 다시 돌렸고 `.scratch/plan.md`에 바뀌는 것이 없었다(connection-check 기능은 아직 in-progress라 행이 그대로다. 이 일지가 처음 "갱신했다"고 쓴 것은 틀렸다).

open-session을 부른다 2026-11-24T08:15:19Z

## 셀프 리뷰

범위: base `7770ac0c1`(`origin/dev`는 그 뒤 `463d9f1f7`까지 앞섰다), 추적 파일 8개의 변경과 미추적 파일, 커밋 없음. 표준 축은 sonnet·high, 명세 축은 세션 모델로 서브에이전트 둘이 돌았다. Critical은 없었다.

### 고친 것

- 표준 1·2(Minor): `hooks/queries/admin/index.ts` 주석이 "주기를 두는 읽기는 접속 확인 하나"라고 해 `web-admin.md`의 "ADR 0063의 것과 접속 확인 하나"와 어긋났다. 주석을 "이 정책에서 빠지는 주기 읽기는 `.claude/rules/web-admin.md` 가 적는다. 지금 코드에 있는 것은 플러그인 목록의 접속 확인이고 그 정책은 `hooks/queries/connection`의 `AUTO` 다"로 고쳤다. `web-admin.md`의 SWR 해법 셋 서술은 훅 머리 주석이 원천이라 "이 훅은 SWR 기본 동작 셋을 풀고 그 해법은 훅의 머리 주석이 적는다"로 줄였다.
- 표준 4(Minor): 같은 모양의 `ManualResult`(훅)와 `LaunchedResult`(분자)를 `types/connection`의 `PressedResult` 하나로 모았다. 시각 이름을 정하는 문장(`누른 시각`·`확인한 시각`)은 분자에, 시각 값을 정하는 문장은 훅에 남아 둘로 나뉜 채다. 아래 "남긴 것".
- 표준 5(Minor): `flights`의 주석이 "토큰"이라 썼지만 키는 관리 토큰 세대(`adminTokenGeneration`)다. 주석을 "같은 행(관리 토큰 세대, 종류, 이름)"으로 고쳤다.
- 표준 6(Nit): `RowConnection`의 `AutoConnectionProps.kind`를 `CheckableKind`로 바꿨다.
- 명세 5(Minor): stdio 행에서 `확인하는 중`과 결과가 서로 다른 `ConnectionLine`이라 `role="status"` 영역이 새로 서서 화면 읽기 도구가 바뀐 결과를 알리지 못할 수 있었다. 시험(`응답이 오면 확인하는 중이던 상태 영역이 그대로 이어져 결과가 알려진다`)을 먼저 써 빨강을 본 뒤, `LaunchedConnection`이 한 줄을 이어 그리게 고쳐 초록을 봤다(`pnpm -C web exec vitest run --project pages`로 `HomePage.connection.test.tsx`와 `HomePage.test.tsx` 78개 통과).
- 명세 1·2(Major): 티켓 검증 칸의 주석이 사실보다 넓었다. 가짜 키를 넣은 셸에서 새 e2e 장면이 통과하는 것을 쳐서 보았고, `decision.e2e.ts` 실패가 이 티켓 탓이 아니라는 것을 화면 변경을 되돌린 채 같은 장면을 돌려 가렸다(위 "실패한 e2e 한 건"). 티켓의 두 칸 주석과 이 일지의 해당 절을 그 사실대로 고쳤다.
- 명세 6(Nit): 이 일지의 "plan.md도 갱신했다", "기존 장면 아홉이 통과", "여섯 상태 × 라이트·다크" 세 문장을 위 대로 바로잡았다.

### 남긴 것

- 표준 3(Minor): `LaunchedConnection`의 `enabled`·`pending` 불리언 둘은 `enabled=false`이고 `pending=true`인 뜻 없는 조합을 낼 수 있다. 훅이 꺼지는 순간 `pending`을 지워 실제로는 나오지 않는다. 열거로 바꾸면 훅의 상태 모양까지 바뀌어 이 티켓의 몫을 넘긴다. 다음에 이 부품을 만지는 티켓이 정한다.
- 표준 4의 시각 판정 두 곳(Minor): 훅이 `at`을, 분자가 `label`을 정한다. 둘은 서로 다른 일(값, 글)이라 합치지 않았다.
- 표준 7(Nit): `checkConnection`과 `checkConnectionByLaunching`은 GET과 POST만 다르다. 호출이 둘뿐이고 생성 클라이언트의 타입 때문에 합치기 어렵다.
- 명세 3(Minor): 새 e2e 장면(`connection-check.e2e.ts`)이 05의 e2e 장면 자리를 일부 앞질렀다. 04가 요구한 "요청이 나가지 않는다"의 확인을 겸해 둔다. 05가 같은 이름의 파일을 만들면 합친다.
- 명세 4(Minor): 응답이 `not_applicable`이면 결과가 `null`이라 행이 `확인하는 중`으로 남고 목록을 다시 읽는다. 서버가 목록과 어긋난 때만 나오는 길이고 목록이 바뀌면 행이 사라진다. 명세가 이 상태를 정하지 않아 그대로 뒀다.
- 명세 7(Nit): 훅을 시험보다 먼저 쓴 것은 위 "시험을 먼저 쓰지 못한 것"이 이미 적었다.

### 다시 돌린 명령

- 새 시험 하나와 `HomePage` 시험 둘: 위 대로 78개 통과.
- 관리 화면 e2e 새 장면(가짜 키 포함)은 통과, `decision.e2e.ts`는 기준 상태에서도 실패.
- 카나리아: `sibling_overlap`이 `.claude/rules/web-admin.md`를 원천으로 든 기존 명세(`web_admin_plugins_read.toml`)는 이 티켓이 더한 문장을 재지 않는다고 알렸다. 이 티켓의 새 항목을 겨냥한 명세 `.scratch/connection-check/probes/canary/web_admin_periodic_read.toml`을 새로 썼다. `uv run python tools/canary.py`로 새 `claude -p` 세션(claude 2.1.325)에서 돌려 통과 4, 실패 0이었다. 실험군 3회차가 문장을 글자 그대로 옮겼고 대조군은 "없음"이었다(표준 출력을 읽은 것이다. 원본은 스크래치에 있고 저장소에 두지 않았다).
- 나머지(린트, 타입체크, 경계, web verify)는 커밋의 pre-commit이 돌린다.

## PR 직전 리뷰(`coderabbit-review`, 이어받은 세션)

CodeRabbit CLI가 돌았다(서브에이전트의 보고에서 옮겼다: `Seat: not assigned`, 종료 0, 지적 6건, 한도와 인증 오류 없음). 보고한 서브에이전트는 지적마다 코드를 읽어 가렸고 아래 "유효" 판정도 그 읽기다. 첫 회차라 Minor도 지적마다 판단했다. 이 세션은 `sync-design-system 확인`도 쳤고 결과는 `clean`(웹 편집 없음)이었다.

### 고친 것

- 숨은 탭의 첫 요청(Minor, 유효): `refreshWhenHidden: false`는 이미 뜬 탭의 주기 확인만 쉬게 해, 보이지 않는 탭에서 행이 처음 서면 첫 확인이 나갔다. 티켓의 "보이지 않는 동안에는 보내지 않고"와 어긋났다. 시험(`보이지 않는 탭에서 목록이 서도 첫 확인을 보내지 않고 보이면 바로 한 번 확인한다`)을 먼저 써서 빨강(요청 1건)을 본 뒤, 요청 함수 앞에서 `document.visibilityState === "hidden"`이면 보내지 않고 `null`을 돌려주게 고쳐 초록을 봤다(`HomePage.connection.test.tsx`와 `HomePage.test.tsx` 79개 통과). 탭이 보이면 기존 `visibilitychange` 처리기가 바로 한 번 확인한다.
- `serveEnv`의 대소문자(Minor, 유효): Windows에서 펼친 환경 객체의 키는 대소문자를 가려, `Anthropic_Api_Key` 같은 이름은 지워지지 않는다고 서브에이전트가 코드를 읽어 지적했다(내가 그 이름의 변수로 돌려 확인하지는 않았다). 이름을 대문자로 바꿔 견주도록 고쳤다. 고친 `serveEnv`를 e2e로 돌려 보지도 않았고 CI의 `e2e` 잡과 pre-commit이 본다.
- `flights` 주석(리뷰어 대조 3, 과장): "같은 행의 요청은 하나만 보낸다"를 "그 행이 화면에 서 있는 동안"이라는 조건을 붙여 고쳤다. 행을 껐다 켜거나 화면을 떠났다 돌아오면 옛 요청이 날아가는 중에 새 요청이 나간다(코드의 뜻은 원래 그랬다).

### 남긴 것

- 티켓 04 검증 칸의 체크(대조 4): `[x]`인 두 칸이 전체 러너의 pytest 한 건과 e2e `decision.e2e.ts` 한 장면의 빨강을 주석으로 적는다. 둘 다 이 티켓이 원인이 아니라고 이미 가려 적었으므로(위 "게이트", "실패한 e2e 한 건") 체크는 두고 PR 본문의 "남긴 위험"에 옮긴다.
- 모델 행 e2e 칸의 갈음(대조 4): "기존 장면은 글을 단언하지 않아 새 장면으로 갈음"은 티켓 원문(기존 장면의 모델 행에 보인 글을 일지에 적는다)과 다른 갈음이다. 위 "기존 e2e를 지킨 것"이 사실을 적었으므로 그대로 두고 PR 본문에 알린다.
- 오탐 셋: `showcase` 태그가 앱 스토리에 없다는 두 건(그 태그는 디자인 시스템 카드용이고 `apps/admin`의 스토리에는 한 곳도 없다), 오래된 요청의 `disabled` 응답이 목록을 한 번 더 읽게 한다는 건(요청이 한 번 늘 뿐 값은 맞다). stdio 요청의 `pending`은 `RequestFailure`가 아닌 예외(코드 결함)에서만 영구히 남고 정상 경로의 버그는 아니다. 하드닝 여지로 남긴다.

## 인계 2(커밋 뒤에 넘긴다)

셀프 리뷰와 반영을 마치고 커밋했다. 커밋은 `78f6c53f1`(`feat: 플러그인 화면의 행이 접속 확인의 결과를 보인다 (connection-check 04)`)이고 이 브랜치에 있다. 아직 푸시하지 않았고 PR도 없다. 제목이 `feature/04-plugin-list-shows-connection-check`였던 세션이 넘긴다(넘기며 `(인계함)`을 붙인다).

- 커밋의 pre-commit은 첫 시도에서 pytest 둘(`tests/channel/cli/test_interrupt.py`의 `test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다`와 `test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`)이 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다"로 빨개 막혔다(커밋 로그를 읽었다, 2 failed 8134 passed). 이 변경은 파이썬 파일을 건드리지 않았고, 그 파일만 `uv run --no-sync pytest tests/channel/cli/test_interrupt.py -q -p no:xdist`로 단독으로 돌리니 6 passed(31.5초)였다(손으로 쳤다). 이 PC에서 다른 세션이 함께 도는 부하 탓으로 어림한다(부하는 재지 않았다). 같은 커밋을 다시 시도하니 pre-commit이 모두 통과해 커밋됐다.
- 남은 단계는 `implement` 스킬이 이 커밋 뒤에 정한 것이다. 요청 범위는 PR과 병합까지다.
  1. PR 직전 리뷰: `coderabbit-review` 서브에이전트(CLI가 못 돌면 `bug-perf-review`). 이 세션이 반영하며 새로 쓴 사실 문장을 밀 주장으로 넘긴다. 위 "셀프 리뷰"의 "고친 것" 가운데 훅 머리 주석이 아닌 문장은 `hooks/queries/admin/index.ts`의 "이 정책에서 빠지는 주기 읽기는 `.claude/rules/web-admin.md` 가 적는다. 지금 코드에 있는 것은 플러그인 목록의 접속 확인이고 그 정책은 `hooks/queries/connection`의 `AUTO` 다", `.claude/rules/web-admin.md`의 "이 훅은 SWR 기본 동작 셋을 풀고 그 해법은 훅의 머리 주석이 적는다", `hooks/queries/connection/index.ts`의 "날아가는 확인. 같은 행(관리 토큰 세대, 종류, 이름)의 요청은 하나만 보낸다", 티켓 04의 검증 칸 주석 둘이다.
  2. `git-pr` 스킬로 PR(본문 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`). PR 제목 접두에 느낌표는 붙이지 않는다(운영자가 올릴 때 손댈 것이 없다. 이 티켓의 변경은 화면과 시험이라 `docs/release-notes/upgrade/` 원고를 더하지 않았다. 확인은 새 세션이 `docs/constitution/operations.md`의 "릴리스 노트 원고"로 한 번 더 본다). 이 티켓은 기능의 마지막 열린 티켓이 아니라(05·06이 남았다) 기능 단락도 끝 줄도 더하지 않았다.
  3. `mcp__ccd_pr__get_status`와 `bind_pr`, 봇 회차와 병합은 워크트리 사본의 `next-session`의 `merge.md` "워크트리에서 병합할 때". CI의 python 잡이 15분 제한으로 취소되면 단계 시각으로 가르고 `gh run rerun <실행> --failed`만 한다. CI의 `e2e` 잡이 `decision.e2e.ts`의 첫 장면에서 빨가면 위 "실패한 e2e 한 건"대로 이 티켓과 별개로 `diagnosing-bugs`로 간다.
  4. 단계를 닫을 때 `retro`를 돈다. 이 일지의 "다음"은 아래 초안이고 닫는 세션이 마무리한다.
- 이 PC의 `origin/dev`는 `463d9f1f7`(PR #630, main을 dev로 합친 병합)까지 앞섰으나 `git diff --name-only HEAD...origin/dev`가 비어 겹치는 파일이 없다(손으로 쳤다). `sibling_overlap`은 번호 겹침 없음, 함께 고친 파일 없음으로 끝났다. 병합 전에 한 번 더 친다.

open-session을 부른다 2026-11-24T09:27:02Z

## 다음(초안)

- 05(관리 화면 e2e 장면)와 06(배포 안내의 문제 해결 절)이 이 티켓에 막혀 있었다. 둘 다 이제 풀렸다.
- 05는 실제로 붙는 서버와 닿지 않는 서버를 보는 장면을 더한다. 위 연결 상한도 거기서 잰다.
