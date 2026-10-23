# 2026-10-23 (40) web-widget 명세

next-session 지시문으로 연 새 세션이다. 제목을 브랜치 이름으로 바꾸고, 주 체크아웃에서 `tidy-checkouts`를 먼저 돌았다(루트를
`8575f57d`에서 `934f8dfa`로 당겼다). 주 체크아웃에서 브랜치를 따지 않고 워크트리 `.claude/worktrees/web-widget-spec-2`에
들어가 브랜치를 `docs/web-widget-spec-2`로 바꿨다. `to-spec` 스킬을 Read로 열어 따랐다.

> 사용자: ".claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. … 인자: web-widget … 다음 작업: 기능 web-widget. 위젯
> 화면 여덟이 병합되어 디자인이 끝났다. 명세를 쓴다 … 이어받을 상태: PR #368 이 origin/main 에 병합됐다(934f8dfa). 명세가
> 정할 것은 디자인 README 의 제안과 탐색용 가정 목록 전부와 일지 '다음'의 항목이다. 옛 docs/web-widget-spec 브랜치와
> 워크트리(PR 없음, 커밋 8acd9a48)가 남아 있다. 명세 세션이 정한다 … 이번 요청 범위: 티켓까지"

## 이어받은 것

`tidy-checkouts`는 워크트리 `.claude/worktrees/03-rerun-judge`와 브랜치 `feature/03-rerun-judge`를 지웠다. 그 워크트리를 쥔
쉬는 세션 다섯을 `end-holders`로 끈 뒤였다. 병합된 PR이 없는 워크트리 열(옛 `web-widget-spec` 포함), 프로세스가 쥔 워크트리
일곱, 앱의 표지가 있는 워크트리 둘은 남겼다. 휴지통의 `worktree-overrides-pc-check~~.venv`는 python.exe(pid 41176)가 쥐어
`empty-trash`가 1로 끝났다. 지시문대로 보고만 하고 답을 기다리지 않았다.

화면 파일 여덟과 `canvas.json`은 웹 편집 확인을 지났다(아티팩트 판 1792723018-d2f3과 줄 끝을 빼고 같다). 웹에서 고친 것은 없다.

## 이음매와 계약의 물음

`to-spec` 2단계의 이음매와, 근거 문서에 답이 없거나 확정된 화면을 바꾸는 셋을 한 선택 화면에 물었다. 묻기 전에 도구 항목이
호출 뒤에만 온다는 것(`core/run.py`의 `_record_tool_call`이 결과를 받아 `ToolCalled`를 쓴다), 429 봉투가 어느 상한인지만
사람의 글로 말하고 누구 몫인지는 말하지 않는다는 것(`.claude/rules/http.md`), 띠 모양 부품이 디자인 시스템에 없다는 것,
이음매 다섯을 풀어 적었다. 처음 띄운 화면은 훅이 사실을 대 보라고 한 번 막았고, 대 본 뒤 같은 글로 다시 띄웠다.

> 사용자(질문에 답): "서버가 '도구를 부르기 시작함'을 새로 보낸다" — 설명: 새 이벤트 종류를 더해 화면 그대로 '<도구> 부르는
> 중'을 보입니다. 대신 이벤트 형식(sdk), 트레이스, 계약(openapi.json), ADR이 바뀌고, 그 계약 티켓이 위젯의 다른 티켓을 막아
> 이 기능이 커집니다.

추천("도구 이름 없이 고정 문구")과 달랐다.

> 사용자(질문에 답): "서버가 상한의 종류를 코드로 준다" — 설명: 거절 봉투에 '동시 실행/시간당' 같은 종류 칸을 더해(계약 변경,
> ADR 0023 이력) 종류마다 문구를 다르게 합니다. 누구 몫의 상한인지는 여전히 말하지 않으므로 문구는 화면보다 덜 구체적입니다.

추천("종류를 가르지 않는 문구 하나")과 달랐다.

> 사용자(질문에 답): "위젯 앱의 자기 부품 (추천)" — 설명: 위젯 앱(apps/widget) 안에 띠 부품 하나를 디자인 시스템의
> 토큰·아이콘·진행 표시로 짓습니다. 위젯의 Storybook과 사진 비교가 판정합니다. 디자인 시스템 패키지와 Claude Design의 카드는
> 바뀌지 않습니다.

> 사용자(질문에 답): "실제 모델을 부르는 e2e를 하나 더" — 설명: 위의 다섯에 더해, 실제 모델을 부르는 에이전트로 위젯에서 요청
> 하나를 끝까지 보내는 e2e를 LLM 테스트로 둡니다. 돌 때마다 모델 비용이 들고 키가 있는 환경에서만 돕니다.

추천("이대로 다섯 자리")과 달랐다.

## 첫 답의 설명을 바로잡아 다시 물었다

첫 답을 옮기기 전에 그 설명의 기술 조건을 코드에 대 보았다. 둘이 틀렸다. 모델 호출 이벤트(`llm_called`)가 모델이 요청한
도구 목록(`tool_calls`)을 도구를 실행하기 전에 이미 기록해(`sdk/events.py`), 새 이벤트 종류와 트레이스 형식 변경은 필요 없다.
대신 런타임이 호출 안에서 만든 이벤트는 컨텍스트에 쌓였다가 에이전트가 다음 이벤트를 낼 때 한꺼번에 나온다(`core/run.py`의
`_relay`와 `take_events`). 프로브 `.scratch/web-widget/probes/event_timing.py`가 쟀다. 계산 에이전트의 모양(`ctx.llm()` 한
번 뒤 끝남)에서 도구 둘이 0.5초씩 잠들었는데 모델 호출 셋과 도구 줄 둘이 모두 1.53초에 끝남과 함께 나왔고, 양성 대조(에이전트가
도구 사이에 자기 이벤트를 낸다)에서는 첫 도구 줄이 0.51초에 나왔다. 그래서 지금은 화면이 그린 "도구 줄이 실행 도중 쌓이는
모습"도 일어나지 않는다. grilling의 '옮길 때'에 따라 바로잡은 사실을 풀어 적고 다시 물었다. 상한 종류 코드의 설명은 맞았고,
에러 봉투의 필드 넷을 적은 ADR 0010 문장에도 포인터가 붙는다는 것만 덧붙였다. 처음 띄운 화면은 훅이 사실을 대 보라고 한 번
막았고, 확인하지 않은 "관리 화면도 실시간"을 운영자 채널로 좁혀 다시 띄웠다.

> 사용자(질문에 답): "이 기능에서 core까지 바꾼다" — 설명: core가 모델·도구 호출 중의 이벤트를 바로 내보내게 바꾸고(ADR),
> 최종 사용자 항목에 '부르는 중'을 더합니다(계약). 화면 그대로 도구 줄이 쌓이고 지금 도구가 보이며, 운영자 채널(/runs)의
> 스트림도 실시간이 됩니다. 대신 명세가 그 구조를 지금 시제로 재서 정해야 하고, 그 티켓이 위젯 티켓을 막습니다. 에이전트가
> 모델 없이 직접 부른 도구는 미리 알 수 없어 그때만 고정 문구입니다.

추천("이번엔 고정 문구, 실시간은 다음 기능으로")과 달랐다.

## 실시간 중계의 시제품

답의 설명이 "명세가 그 구조를 지금 시제로 재서 정해야"라고 했으므로 core를 고친 시제품을 지어 쟀다. 에이전트를 anyio 태스크 그룹의
자식 태스크에서 돌리고, 컨텍스트가 모델·도구 호출을 기록하면 몸통에 신호(`anyio.Event`)를 보내 몸통이 그 이벤트를 꺼내
내보내고 다음을 청할 때까지 기다린다(맞물림). 이벤트는 컨텍스트의 줄에 남기고 신호만 메모리 흐름으로 건넌다. 에이전트
태스크는 취소가 아닌 예외를 모두 그 객체 그대로 붙잡아 몸통에 넘기고(`_Thrown`의 동일성 판정이 서도록), 몸통은 자기
예외를 태스크 그룹 안에서 붙잡아 그룹을 취소한 뒤 밖에서 다시 던진다. anyio 4.15.1의 태스크 그룹이 몸통의 예외를
`BaseExceptionGroup`으로 감싸기 때문이다. 기존 시험 가운데 에이전트의 정리 코드가 `run()`을 부른 태스크에서 돈다는
단언 셋만 깨져, 그것을 "에이전트를 돌린 태스크에서 돈다"로 바꿨다. 그 단언이 닫지 않는 구현을 여전히 잡는지는
`contract_mutations.toml`의 변이를 손으로 넣어 봤다.

시제품은 `.scratch/web-widget/probes/live_relay.patch`(커밋 934f8dfa에 대한 diff)로 남기고 작업 트리의 `src/`·`tests/`는
되돌렸다. `live_relay.py`가 그 커밋을 `git archive`로 꺼낸 사본 둘(그대로, 패치를 댄 것)에서 `event_timing.py`를 돌려 견주고,
패치를 댄 사본에서 기존 시험과 실제 MCP의 트레이스 쓰기 실패를 돌린다. `event_timing.py`에는 동시 갈래(`asyncio.gather`)와
많은 호출 갈래(이벤트 하나의 비용)를 더했다. 판정 기준을 결과를 본 뒤 한 번 바꿨다. "첫 도구 줄이 시작 0.75초 안"은 첫
모델 호출 앞의 준비 시간이 섞여 시제품에서도 거짓이었고, 이벤트 사이의 간격 둘로 바꿨다.

첫 실행(9분 48초)에서 `tests/channel/cli/test_interrupt.py`의 Ctrl+C 시험 둘이 자식이 30초 안에 끝나지 않아 실패했다. 그때
CPU는 88%였고 node 프로세스가 136개였다. 그 자식은 `core/run.py`를 import하지 않는다(어댑터가 `core/ports.py`만 부른다).
경쟁하는 해석(패치 몫, 부하 몫)을 가르는 회차(실패한 시험만 두 사본에서 다시 돌린다)를 더해 다시 돌렸고, 둘째 실행에서는
553개가 모두 지나(1분 59초) 그 회차는 돌지 않았다. 둘째 실행의 수: 지금 core의 한 번 갈래는 모델 호출과 도구 줄이 모두
결말과 같은 1.30초에, 시제품은 첫 모델 호출 0.10초, 도구 줄 0.61초·1.11초. 동시 갈래는 둘 다 0.50초 남짓으로 겹쳤다.
이벤트 하나는 11µs에서 76µs(첫 실행 18µs에서 101µs). 실제 MCP의 네 사례는 두 실행 모두 기대대로였다. 결과 표는 프로브
README의 2026-10-23 결과다.

## 결정의 자리

`origin/main`이 `db92d68a`로 앞서 있었고 앱이 이 워크트리를 만든 것이 아니라 `sync_with_base_branch`가 거부해, 직접
`git merge origin/main`(fast-forward)했다. ADR 0038이 main에 이미 있어 새 ADR은 0039다.

- ADR 0039 초안(proposed): 런타임은 모델·도구 호출의 이벤트를 기록하는 자리에서 흘리고, 에이전트는 몸통과 맞물린 제
  태스크에서 돈다. 거부한 안 넷(지금처럼 모음, 같은 태스크의 되돌아 나오기, 맞물리지 않는 자식, 이벤트를 메모리 흐름으로)과
  대가(정리 코드의 태스크, 버려진 실행에서 끊기는 자리, 이벤트 하나의 비용)를 적었다. 메모리 흐름이 항목을 잃는 창은
  anyio의 `memory.py`를 읽은 어림이라 그렇게 적었다.
- `CONTEXT.md`에 "상한(Limit)"을 더했다. 429가 종류는 싣고 범위는 숨기므로 두 말을 가르고, 대화 요약의 계기인 "한도"와
  섞지 않게 했다.
- ADR 0023의 이력(부르는 중 항목, 429의 상한 종류)과 ADR 0010·0024의 포인터·이력은 명세의 이름이 선 뒤에 쓴다.

## 명세

Explore 서브에이전트 하나에 코드 사실 열둘(최종 사용자 경로와 상태 코드, 항목과 투영, `LlmCalled`, 429와 `Limit`, 사이트
파일, 404·409·422의 범위, 구독, web의 현재 상태, 관리 화면의 스트림, nginx와 `serve` 인자, LLM 시험 규약, 시험 파일)을 맡겼다.
명세에 바로 걸린 어긋남 셋을 보고했다. `readFrames`가 `id:`를 버린다, ADR 0024의 허용 출처 표기 픽스처가 없고 파이썬은 `"*"`
하나만 거절한다, `deploy/nginx/`가 없다. 셋 다 명세의 결정으로 받았다.

`.scratch/web-widget/spec.md`의 남은 절을 채웠다. 서두의 수는 넘겨받은 것 38(plan.md 행 20, 화면 README의 제안과 가정 9,
어긋남 7, 일지 30의 옛 브랜치 1, ADR 0024의 위젯 경로 이름 1), 사용자가 고른 것 4, 명세가 정한 것 51이다. 표시를 grep으로
세어 처음 50이었고, 넘겨받은 항목과 하나씩 대 보다 빠진 둘(화면 README의 보내기 버튼 높이, plan.md 행의 위젯 CSS가
빌드·Storybook에서 서는지)을 채워 51이 됐다. 이름은 명세가 정했다(`calling`·`tools`, `LimitEnvelope`·`limit`의 세 값,
`/widget`, `AGENT_OS_SITE_FILE`, vitest 프로젝트 `widget-pages`·`widget-storybook`, CI 잡 `e2e-widget`).

- ADR 0023 이력 2026-10-23 "최종 사용자 스트림에 도구를 부르기 시작함 항목이 늘고, 429 봉투가 상한의 종류를 든다"를 쓰고
  본문 56행 뒤와 ADR 0010 봉투 문장 뒤에 포인터를 달았다.
- ADR 0024에 첫 `## 이력`(2026-10-23 "이어 가기와 구독의 404는 한 번 더 시도한 뒤 저장을 지우고, 위젯 경로의 이름은 명세가
  짓는다")을 만들고 본문 둘(404 문장, "실제 이름은 계약 티켓이 짓는다")에 포인터를 달았다.
- `plan.md` web-widget 행에 2026-10-23 명세 괄호를 더했다. 상태는 규약대로 `todo`다.
- `tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`가 바뀐 문서에서 0으로 끝났다.

명세를 쓰며 손으로 본 것: 화면 여덟이 쓴 아이콘 여덟이 모두 `IconName` 안에 있다(화면 파일 grep). 진행 표시의 도는 아이콘이
`motion-reduce:animate-none`을 단다. `934f8dfa`와 `db92d68a` 사이 `src/agent_os/core`·`tests/core`의 diff가 비었다. `uv run
--env-file <임시 파일>`이 `node`와 `pnpm.cmd`에는 환경 변수를 넘겼고 `pnpm`은 `Failed to spawn: pnpm`으로 띄우지 못했다. 그래서
실제 모델 e2e는 `-m llm` 파이썬 시험이 Playwright를 자식 프로세스로 감싸는 것으로 정했다. 그 확인이 `pnpm -C web exec`로
이 워크트리의 `web/node_modules`를 설치했다(무시된 폴더).

이 세션이 고친 것: ADR 0023 이력의 "이름은 계약 티켓이 짓는다" 두 문장을 "명세가 정했다"로 바꿨다. 이름까지 명세에
확정해야 계약 티켓이 도중에 멈추지 않는다. ADR 0024 이력의 결정 404 문장("저장의 어느 것도 가리키지 않는")이 틀려(멈춘
실행은 다시 붙을 실행으로 저장에 든다) "승인 묻기와 다시 붙을 실행만 걷는다"로 고쳤다.

## 인계

셀프 리뷰 직전에 컨텍스트가 인계 문턱을 넘어 `hook_handoff`가 왔다. `/code-review`를 부른 직후다. 리뷰의 단계는 밟지 않았고
새 세션이 처음부터 한다. 이 세션의 지금 제목은 `docs/web-widget-spec-2`이고 인계하며 `docs/web-widget-spec-2 (인계함)`으로
바꿨다. 워크트리 잠금을 풀었다(`git worktree unlock`이 0으로 끝났다). 띄운 백그라운드 작업은 없었다.

인계 지시문:

```
다음 작업: 기능 web-widget. 명세 초안이 커밋 전으로 섰고, 셀프 리뷰부터 이어 티켓까지 간다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec web-widget
브랜치: docs/web-widget-spec-2
모델: Opus 5.5 / xhigh
읽을 것: docs/journal/2026-10-23-40-web-widget-spec.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(명세, ADR 0039 초안, ADR 0023·0024 이력과 0010 포인터, CONTEXT.md, plan.md, 프로브, 일지)이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main)부터 한다. 그 뒤 to-spec의 차례대로 리뷰 반영, 서두의 수 다시 세기, ADR 0039 초안과 이력·포인터를 사용자에게 보여 승인받기(승인 뒤 0039를 accepted로), 커밋이고, 이어 spec-reviewer, /to-tickets(.claude/skills/to-tickets/SKILL.md를 Read로 열어 따른다), PR이다. 옛 docs/web-widget-spec 브랜치는 명세가 대신한다고 정했고, 지우기는 병합 뒤 주 체크아웃 세션이 사람에게 확인받고 한다. 일지 docs/journal/2026-10-23-40-web-widget-spec.md
확인할 선행 조건: 실제 모델 e2e를 감싸는 pytest가 Windows에서 pnpm을 자식 프로세스로 띄우는지는 재지 않았다(uv run --env-file로 pnpm.cmd와 node가 뜨는 것만 손으로 봤다)
이번 요청 범위: 티켓까지
```

open-session을 부른다 2026-10-23T05:33:46Z

## 이어받은 세션

위 지시문으로 연 새 세션이다. 제목을 `docs/web-widget-spec-2`로 바꾸고, `git worktree list`에서 그 브랜치가
`.claude/worktrees/web-widget-spec-2`에 체크아웃된 것을 보고 EnterWorktree(path)로 들어갔다. `to-spec`을 Read로 열어
따랐다. `origin/main`은 그대로 `db92d68a`였다.

> 사용자: ".claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. … 인자: web-widget … 이어받을 상태: 인계: 셀프
> 리뷰 직전 … 확인할 선행 조건: 실제 모델 e2e를 감싸는 pytest가 Windows에서 pnpm을 자식 프로세스로 띄우는지는
> 재지 않았다 … 이번 요청 범위: 티켓까지"

셀프 리뷰(`/code-review`, base `db92d68a`, 바뀐 추적 파일 7, 미추적 6, 커밋 0)의 두 축을 띄우고, 도는 동안 선행
조건을 쟀다. 그 결과가 명세의 테스트 결정 6을 바꿀 수 있어서다(`to-spec` 3단계의 측정 규칙).

- `.scratch/web-widget/probes/pnpm_spawn.py`를 지었다. `uv run --env-file` 아래의 pytest가 `pnpm`을 이름으로는 띄우지
  못하고(`FileNotFoundError`, uv 직접도 `Failed to spawn`), `shutil.which("pnpm")`의 경로로는 띄워 `.env`의 값이 node까지
  닿고 Playwright 1.63.0이 떴다. 측정 4회차, 측정 아님 0회차. 첫 실행은 `--env-file`의 역슬래시 경로 탓에, 둘째는
  pytest 출력의 진행 점 탓에 측정이 아닌 회차가 났고, 탐침을 고쳐 셋째가 결과다. 판정 기준은 바꾸지 않았다.
- 프로브 README 표에서 앞 세션이 더한 줄 둘(`event_timing.py`, `live_relay.py`)이 빈 줄 뒤에 붙어 표 밖의 머리 없는
  조각이었다. 빈 줄을 옮겨 표에 붙이고 `pnpm_spawn.py`의 줄을 더했다.

### 셀프 리뷰 — 표준 축

sonnet·high. Critical 0, Major 0, Minor 9, Nit 6. 도구 판정 넷(포인터, 표, 줄 구분 문자, 지침)과 프로브 ruff는 0이었고,
서두의 수(38, 4, 51)와 이음매 여섯, 시험 553개, `IconName` 16, 상한 범위 3·2·1을 세어 맞다고 했다.

- Minor: ADR 0039 거부한 안 넷째(이벤트를 메모리 흐름으로)의 근거가 취소의 종류에 갈린다. 받는 쪽이 기다리는 중에
  `send_nowait` 뒤 anyio `CancelScope.cancel()`이면 항목이 닿고, 날 `task.cancel()`이면 사라졌다(리뷰가 `uv run
  python`으로 손으로 봤다).
- Minor: ADR 0039가 선택을 "설계 인터뷰"에서 했다고 적었다. 이 일지는 명세 세션이다(거부한 안 첫째의 "설계 인터뷰가
  추천한 안"도).
- Minor: 명세의 "부르는 쪽은 이벤트 사이에 await 하지 않는다"는 `channel.md`가 아니라 `core.md`의 문장이다. 구현 티켓이
  고칠 문서에 `core.md`의 그 줄이 빠졌다.
- Minor: ADR 0039의 용어집 인용이 원문("생기는 대로 채널이 내보내는 열")에서 낱말 하나가 빠졌다.
- Minor: BMP 밖 글자 20,000자의 본문 240,000바이트는 모두 `\u`로 이스케이프하는 인코더에서만이다. 브라우저
  `JSON.stringify`는 이스케이프하지 않아 80,026바이트였다(리뷰가 node로 손으로 봤다). 그래서 e2e의 본문 크기 경계
  사례는 위젯으로는 닿지 않는다.
- Minor: 45초 무응답 판정이 api-client의 읽기(keepalive 주석을 내지 않는다)와 부딪힌다. 오래 걸리는 도구에서 헛
  재접속이 난다.
- Minor: 명세의 테스트 결정 6이 pnpm을 경로로 띄운다는 것을 적지 않았다(`pnpm_spawn.py`의 결과).
- Minor: 근거의 종류가 빠진 문장 셋("시제품에서 봤다", "세 사례 가운데 둘에서 맞았다", "모델 호출 하나가 수백 ms").
- Minor: `CONTEXT.md`의 "상한"이 `_Avoid_`에 "쿼터"를 넣었는데 용어집의 동사 표와 코드(`RunQuota`)가 그 낱말을 쓰고,
  정의가 요청 글자 수를 빠뜨렸다.
- Nit 여섯: 구현 파일 경로(`web/tools/visual.ts` 등), 고정 문구 "요청을 처리하고 있습니다."를 디자인의 제안으로 적음,
  Out of Scope 둘의 받는 쪽, 정리 코드 시험의 이름, 시제품 조각의 출력 인자, `event_timing.py`의 겹침 판정의 양성 대조.

표준 축의 첫 Minor를 `.scratch/web-widget/probes/anyio_facts.py`로 쟀다(측정 5회차). 날 `Task.cancel()`에서만 항목이
사라졌고 anyio 범위 취소에서는 닿았다. 같은 프로브가 태스크 그룹의 `ExceptionGroup` 감쌈도 쟀다. 이 저장소의 취소는
모두 anyio 범위다(`channel/cli/interrupt.py`, `channel/http/runs.py`를 grep했다. ADR 0034 2026-10-21 이력으로 CLI의 첫
Ctrl+C도 범위다).

### 셀프 리뷰 — 명세 축

본 세션의 모델을 물려받았다. Critical 0, Major 2, Minor 11, Nit 4(표준 축과 겹치는 것을 빼면 Major 2, Minor 8, Nit 1).
서두의 수와 표시 51, 사용자의 네 답과 조건, 거절 표의 상태 코드, ADR 포인터는 맞다고 했다.

- Major: 페이지 안 방식의 `<script type="module">`은 다른 출처에서 CORS로 받으므로 `element.js`에
  `Access-Control-Allow-Origin`이 없으면 사이트에서 실리지 않는다. 명세는 그 헤더를 글꼴에만 달았다.
- Major: 테스트 결정 6의 까닭("uv가 이름으로 못 띄움")이 `pnpm_spawn.py`의 결과로 틀렸고, 경로로 띄운다는 것이 없다.
- Minor: 구독 행에 422·표 밖의 상태·응답 전 네트워크 실패가 없다.
- Minor: 이어 가기의 404에 에이전트가 없거나 열 에이전트 밖인 것도 들어, 대화를 지운 뒤 시작이 다시 404를 받는다.
- Minor: `CLAUDE.md` 검증 명령 절의 "게이트는 열다섯"과 "CI만 돈다"가 새 잡으로 거짓이 되는데 함께 고칠 문서에 없다.
  `operations.md`의 LLM 테스트를 고치는 근거 ADR이 없다.
- Minor: 사진 비교 도우미를 `@agent-os/ui`의 내보내기로 두는 것이 셋째 답의 "디자인 시스템 패키지 … 바뀌지
  않습니다"와 글자로 부딪힌다.
- Minor: 거부하면 `decided` 뒤에 그 도구의 `progress`가 와서(명세 축이 스크래치 탐침으로 손으로 봤다) 이름이 두 번
  빠진다.
- Minor: 멈춘 스트림이 닫히는 것이 "결말 없이 끝남"으로 읽혀 끝없이 다시 붙을 수 있다.
- Minor: 서버 층의 실시간 시험 둘이 지금 core에서도 참이라 옛 core와 새 core를 가르지 못한다.
- Minor: "지금의 시험 전부(553개)"의 553은 core·채널·MCP뿐이다.
- Nit: 거부 사유를 다듬는 글자가 JS `trim`과 파이썬 `strip`에서 다르다(`"\x1c\x1d"`, U+FEFF).
- 겹친 것: keepalive와 45초, "상한" 정의, ADR 0039의 출처와 인용, 161행 인용, "세 사례 가운데 둘", Out of Scope의 받는 쪽.

### 셀프 리뷰 반영

고친 것. 지적마다 근거를 코드와 측정에 대 본 뒤 고쳤다.

- 페이지 안 방식의 번들을 classic 스크립트(IIFE)로 바꾸고, 기준 주소를 `document.currentScript`에서 읽게 했다. 명세에
  "번들의 꼴" 결정 하나를 더했고, e2e에 다른 출처 페이지에서 `<script src>` 한 줄로 번들이 실리는 사례를 더했다(Major).
- 테스트 결정 6의 까닭을 `pnpm_spawn.py`의 결과로 고치고, pnpm을 `shutil.which`의 경로로 띄운다고 적었다. 실제 모델 e2e가
  LLM 테스트 규약을 바꾸므로 ADR 0024에 이력 "실제 모델을 부르는 위젯 e2e는 LLM 시험 하나가 감싼다"를 더했다(Major와
  명세 축 Minor의 근거 ADR).
- ADR 0039의 거부한 안 넷째를 `anyio_facts.py`의 측정으로 다시 썼다. 출처를 "명세를 쓰며"로, 거부한 안 첫째의 추천자를
  "명세를 쓰던 세션"으로, 용어집 인용을 원문대로, "모델 호출 하나가 수백 ms"를 어림으로 고쳤다.
- 명세의 구현 티켓이 고칠 문서에서 `core.md`의 두 문장과 `channel.md`의 문장을 원문대로 인용했다. 근거 없는 "세 사례
  가운데 둘에서 맞았다"는 지웠다(기록이 남지 않았다).
- api-client의 새 읽기가 keepalive 블록도 값으로 내고, 무응답 판정이 프레임과 keepalive를 함께 센다. 끊김 정의에서
  `paused` 뒤에 닫힌 스트림을 뺐다.
- 진행 표시 이름표의 `decided` 규칙을 지우고, 거부한 도구는 그 `progress`(실패)로 빠진다고 적었다. 고정 문구는 명세가
  정한 것이라고 출처를 바로잡았다.
- 거부 사유를 다듬는 글자를 파이썬 `str.strip()`과 같게 정했다("다듬는 글자" 결정 하나를 더했다).
- 거절 표의 구독 행에 422·표 밖의 상태를 500과 함께, 응답 전의 네트워크 실패를 재접속으로 넣었다. 이어 가기 404 뒤의
  시작이 다시 404면 시작의 404 행대로 한다고 적었다.
- nginx 본문 상한의 근거를 다시 쟀고, e2e의 본문 크기 경계 사례를 위젯 밖에서 이스케이프한 본문으로 보내게 했다.
- 서버 층의 실시간 시험 둘을, 가짜 도구가 시험이 받은 프레임을 본 뒤에야 끝나는 모양으로 바꿔 지금 core에서 빨개지게
  했다. 553의 범위와 정리 코드 시험의 이름(매개변수 세 사례)을 바로잡았다.
- `CLAUDE.md` 검증 명령 절에서 고칠 셋(web 괄호, 게이트 수, CI만 도는 것)을 적었다.
- 사진 비교 도우미를 `@agent-os/ui/visual` 하위 경로로 내보낸다고 바꾸고, 띠 절의 "패키지를 바꾸지 않는다"를 띠 때문에
  컴포넌트를 바꾸지 않는 것으로 좁혔다. 사용자 답의 글자와 부딪히는 자리라 승인 때 알린다.
- 시제품 조각의 `outcome` 출력 인자에 `CODING_STANDARDS.md`의 규칙을 달았다. 구현 파일 경로 둘(`web/tools/visual.ts`,
  `http/cors.py`)을 명령과 모듈의 이름으로 바꿨다. Out of Scope 둘을 "넘기지 않는다"로 고쳤다.
- `CONTEXT.md`의 "상한"에 요청 글자 수를 넣고 `_Avoid_`에서 "쿼터"를 뺐다.
- 서두의 수를 다시 셌다. 넘겨받은 것 38, 사용자가 고른 것 4, 명세가 정한 것 51에서 53(번들의 꼴, 다듬는 글자)이다.
  표시 53과 맞다.

남긴 것과 이유.

- Nit: `event_timing.py`의 겹침 판정에 따로 둔 양성 대조가 없다. 대조 갈래(차례로 부름)의 결말 1.01초가 줄 세웠을 때의
  기준이고 README가 그렇게 적었다. 그 갈래가 양성 대조를 겸하므로 고치지 않는다.
- Nit: 그 밖의 구현 경로(`apps/widget/.storybook/` 등)는 ADR 이력과 테스트 선례가 든 자리라 남긴다(`to-spec`의 경로 규칙).

반영으로 새로 쓴 사실 문장(PR 직전 `bug-perf-review`에 밀 주장으로 넘긴다).

- 명세: "다른 출처의 `<script type="module">`은 CORS로 받으므로 번들 응답에 `Access-Control-Allow-Origin`이 없으면
  사이트에서 실리지 않는다. classic 스크립트는 CORS 없이 실리고, 청크로 나뉘지 않아"
- 명세: "`document.currentScript`의 `src` … 그 값은 classic 스크립트가 최상위를 실행하는 동안에만 있다"
- 명세: "런타임은 거부한 도구를 부르지 않고 실패한 도구 호출로 기록하기 때문이다(런타임의 거부 처리와 항목의 투영을
  코드로 읽었다)"
- 명세: "JS의 `trim()`은 U+001C~U+001F와 U+0085를 지우지 않고 U+FEFF를 지워"(node와 `uv run python`으로 글자마다 대
  보았다)
- 명세: "가장 긴 에이전트 이름(63자)과 그 요청을 든 시작 본문이 240,091바이트였다. … `JSON.stringify` … 80,088바이트"
- 명세: "이어 가기의 404에는 에이전트가 없거나 그 사이트의 열 에이전트 밖인 것도 들어"
- 명세: "`paused` 뒤에 닫힌 스트림을 끊김으로 세면, 다시 이을 때마다 같은 `paused`까지 받고 또 닫혀 끝없이 다시 잇는다"
- 명세: "지금 core에서는 그 프레임이 도구가 끝난 뒤에야 나오므로 제한 시간에 걸려 빨개진다"
- ADR 0039: "이 저장소의 취소는 지금 모두 anyio 범위라(실행 타임아웃, 연결이 끊긴 HTTP 응답, CLI의 Ctrl+C. 채널의 취소
  자리를 grep했다)"
- ADR 0024 이력: "CI의 위젯 e2e 잡은 이 프로젝트를 돌리지 않는다", "그 안에서는 실제 모델이 낸 출력이 스트림을 지나 위젯
  화면에 서는 길을 보는 시험이 없다"

다시 돌린 명령: `tools/check_adr_pointers.py`, `tools/check_md_tables.py`와 `tools/check_line_separators.py`(미추적 문서를
인자로 넘겨서)가 모두 0으로 끝났다. 나머지 검증 명령은 커밋의 pre-commit으로 갈음한다.

### 결정의 승인

반영 뒤 ADR 0039 초안, ADR 0023 이력과 ADR 0010 포인터, ADR 0024 이력 둘, `CONTEXT.md`의 "상한"을 쉬운 말로 풀어
보이고 물었다. 사진 비교 도우미가 셋째 답의 설명("디자인 시스템 패키지 … 바뀌지 않습니다")과 글자로 부딪히는 것도
따로 물었다. 처음 띄운 화면은 훅이 설명의 사실을 대 보라고 한 번 막았고, 도우미의 줄 수(142줄)를 세어 "140줄 남짓"을
"지금 142줄"로 고쳐 다시 띄웠다.

> 사용자(질문에 답): "모두 승인 (추천)" — 설명: ADR 0039를 accepted로 바꾸고 명세와 함께 커밋한 뒤, 명세 검토와 티켓
> 나누기로 넘어갑니다.

> 사용자(질문에 답): "패키지의 하위 경로로 내보냄 (추천)" — 설명: 디자인 시스템 패키지에서 시험 도구가 놓이는 자리만
> 바뀌고(@agent-os/ui/visual), 컴포넌트와 토큰은 그대로입니다. 도구는 한 곳에만 있고 위젯과 디자인 시스템이 함께 씁니다.

승인에 따라 ADR 0039를 `accepted`로 바꾸고 색인과 명세의 "proposed"를 고쳤다. plan.md의 web-widget 행에 ADR 0024의
둘째 이력을 함께 적었다.

### 커밋

커밋 직전 `git branch --show-current`는 `docs/web-widget-spec-2`였고, `tools/sibling_overlap.py`는 번호 겹침 없음(origin/main
`db92d68`)이었다. `6a3436e8`로 커밋했고 푸시하지 않았다(PR 없음). pre-commit은 모두 지났다. pytest 307.5초,
web-verify 237.2초 등이 Passed였고, 카나리아 명세와 헌법 판 검사는 해당 파일이 없어 Skipped였다. 인용 대조가 막지 않는
경고 13건을 냈다. 명세의 화면 문구 8건(거절 표와 상한 띠의 새 문구)은 명세가 정한 문구라 원문이 없다. 프로브 README
76행 "pnpm이 그 환경의 PATH에 없다"는 해석을 따옴표로 묶은 것이다. 일지의 4건 가운데 132행 "저장의 어느 것도 가리키지
않는"은 ADR 0024에 글자 그대로 없다고 나왔다. 넷 모두 아직 하나씩 보지 않았다.

## 인계 (커밋 뒤)

커밋 뒤 컨텍스트가 인계 문턱을 넘어 `hook_handoff`가 왔다. 지금 경계(`커밋 뒤`)는 이 세션이 넘겨받은 경계(`셀프 리뷰
직전`)와 다르고, 요청 범위가 티켓까지이며, `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이 아니다. 그래서
넘긴다. 이 세션의 지금 제목은 `docs/web-widget-spec-2`이고 `docs/web-widget-spec-2 (인계함)`으로 바꾼다. 띄운 백그라운드
작업(커밋)은 끝났다. `tools/model_sweep.py docs/web-widget-spec-2`는 `스윕 밖`이었다.

인계 지시문:

```
다음 작업: 기능 web-widget. 명세가 커밋됐고(ADR 0039 accepted), 명세 검토부터 이어 티켓까지 간다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec web-widget
브랜치: docs/web-widget-spec-2
모델: Opus 5.5 / xhigh
읽을 것: docs/journal/2026-10-23-40-web-widget-spec.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영, 서두의 수 다시 세기, ADR 승인(0039 accepted, 0023·0024 이력, 사진 비교 도우미는 @agent-os/ui/visual)을 마치고 6a3436e8로 커밋했다. 푸시하지 않았고 PR은 없다. 남은 단계는 spec-reviewer 서브에이전트, /to-tickets(.claude/skills/to-tickets/SKILL.md를 Read로 열어 따른다), PR이다. PR 직전 bug-perf-review에 밀 주장은 일지의 "셀프 리뷰 반영" 절에 있다. pre-commit의 인용 대조 경고 13건(일지의 "커밋" 절)은 아직 하나씩 보지 않았다. 옛 docs/web-widget-spec 브랜치는 명세가 대신하고, 지우기는 병합 뒤 주 체크아웃 세션이 사람에게 확인받고 한다. 일지 docs/journal/2026-10-23-40-web-widget-spec.md
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

제목을 바꿨고(`set_session_title`이 묻지 않고 바꿨다), 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-23T07:00:52Z

## 이어받은 세션 (커밋 뒤)

위 지시문으로 연 새 세션이다. 제목을 `docs/web-widget-spec-2`로 바꾸고, `git worktree list`에서 그 브랜치가
`.claude/worktrees/web-widget-spec-2`에 체크아웃된 것을 보고 EnterWorktree(path)로 들어갔다. `to-spec`을 Read로 열어
따랐다. `origin/main`은 그대로 `db92d68a`였다.

> 사용자: ".claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. … 인자: web-widget … 이어받을 상태: 인계: 커밋
> 뒤 … 남은 단계는 spec-reviewer 서브에이전트, /to-tickets(.claude/skills/to-tickets/SKILL.md를 Read로 열어
> 따른다), PR이다 … 이번 요청 범위: 티켓까지"

`spec-reviewer`를 백그라운드로 띄우고(특히 볼 자리는 티켓 사이의 계약 셋, 명세가 티켓에 넘긴 것, 실제 모델 e2e, 사이트
파일의 두 값과 표기 픽스처), 도는 동안 커밋의 인용 대조 경고를 하나씩 봤다.

### 인용 대조 경고

커밋 뒤라 기본 모드(작업 트리가 HEAD에 더한 줄)로는 볼 줄이 없어, 같은 검사 함수를 `origin/main`에 대한 diff의 줄로
돌렸다(세션 스크래치패드의 스크립트로 손으로 봤다). 커밋 때의 13건이 11건(명세 8, 일지 3)으로 나왔다. 프로브 README의
"pnpm이 그 환경의 PATH에 없다"와 일지 132행은 이번에 경고되지 않았다.

- 명세 8건(283·286·288·290·294·310·311·313행)은 명세가 정한 화면 문구라 원문이 없다. 그대로 둔다.
- 일지 65행 "이번엔 고정 문구, 실시간은 다음 기능으로"는 선택 화면의 추천 라벨이라 원문이 저장소 밖이다. 그대로 둔다.
- 일지 69행은 사용자 답의 설명을 바꿔 옮긴 인용이었다. 원문("명세가 그 구조를 지금 시제로 재서 정해야")대로 고쳤다.
- 일지 74행은 시험의 단언을 풀어 쓴 문장을 따옴표로 묶었다. 따옴표를 뗐다.

### 명세 검토

`spec-reviewer`(본 세션의 모델을 물려받았다)가 blocker 1, should-fix 12, nit 6을 냈다. 근거를 하나씩 코드에 대 봤다.
blocker의 전제(기본 실행이 `-m "not llm"`이고, skip은 세션 실패이며, 토큰 합계는 `llm` 마커의 시험만 센다, 이 PC의 PATH에
nginx가 없다)와 should-fix의 계약 시험 셋, `Limit` 열거의 한국어 값이 맞았다.

- blocker: 실제 모델 e2e가 `-m llm` 안에 있으면 원칙 I의 판정 명령이 nginx(TLS), Next·Vite 빌드, 브라우저를 요구한다.
  위젯은 nginx를 거쳐서만 `/end-user`에 닿는다(ADR 0024). core나 채널을 고칠 때마다 그것이 있어야 하고, 없으면 skip이
  실패라 판정이 빨개진다.

그 blocker를 풀어 적고 물었다. 처음 띄운 화면은 훅이 사실을 대 보라고 한 번 막았고, 토큰 합계 줄을 세게 하는 것이
`tests/conftest.py`를 고치는 일이라는 것과 CI의 위젯 e2e가 명세대로라면이라는 것을 설명에 더해 다시 띄웠다.

> 사용자(질문에 답): "따로 치는 명령으로 뗀다 (추천)" — 설명: 지금의 `-m llm`은 그대로 nginx 없이 돕니다. 위젯의 실제
> 모델 e2e에는 새 마커(`llm_widget`)를 달아 기본 실행과 `-m llm`에서 빼고, 위젯이나 최종 사용자 스트림을 건드렸을 때만
> `uv run --env-file .env pytest -m llm_widget`으로 칩니다. nginx·빌드·브라우저는 그때만 필요합니다. 토큰 합계 줄은
> `tests/conftest.py`를 고쳐 그 마커도 세게 합니다. 대신 명령이 둘이 되고, core만 고친 작업은 실제 모델로 위젯 화면까지
> 확인하지 않습니다(명세대로라면 CI의 위젯 e2e가 모델 없는 에이전트로 확인합니다).

### 명세 검토 반영

blocker는 사용자의 답대로 고쳤다. 테스트 결정 6이 `llm_widget` 마커와 따로 치는 명령, 그 계기, conftest가 그 마커도
세는 것, 시험의 기준 다섯(Playwright JSON 리포터로 통과 1·건너뜀 0, `tmp_path`의 트레이스에 `llm_called`, 화면 출력이
트레이스의 `output`과 같음, pnpm이 없을 때의 실패 문구, 제한 시간에 프로세스 트리 정리와 고정 인자), 그것들을 한
티켓에 묶는 것을 든다. ADR 0024의 둘째 이력은 제목을 그대로 두고 본문을 고쳤다. 명령이 원칙 I의 판정과 따로라는 문단을
더하고, 거부한 안에 `-m llm`에 넣는 안과 nginx를 빼는 안을 더해 넷이 됐다.

should-fix 열둘과 nit 여섯은 모두 명세에 반영했다.

- S1: 티켓 차례를 계약 → core로 고정하고, 최종 사용자와 운영자의 실시간 시험 둘을 core 티켓이 든다고 적었다.
  `calling`의 한 줄 설명은 시점을 말하지 않는다.
- S2: 429만 `LimitEnvelope`라는 규칙과 함께 고칠 시험 넷(봉투 단언 둘, 항목 유니온 멤버 수, LLM 시험의 독스트링)을
  이름으로 적었다. 독스트링은 검토가 "사이트 파일 절"로 짚은 것과 달리 실제 `serve`의 LLM 시험에 있었다(줄을 읽었다).
- S3: `limit`의 값 집합 컴포넌트를 `LimitKind`로, `code`는 `ErrorEnvelope`와 같은 `ErrorCode` 참조로 정했다.
- S4: 사이트 파일의 판은 `"1"` 그대로이고 까닭을 적었다. serve의 구성 오류 문구가 항목과 규칙을 말한다.
- S5: 표기 규칙에 IPv4·IPv6·포트의 정규형을 더하고, 검토가 손으로 본 다섯을 막히는 사례로 적었다.
- S6: 변수가 없을 때와 준 파일을 읽지 못할 때를 갈랐고(뒤는 빌드 실패), 두 언어가 같은 TOML 사이트 파일 픽스처를
  읽어 두 값을 고정하는 시험과, 픽스처와 두 언어의 판정이 한 티켓에 드는 것을 적었다.
- S7·S8·N5: 위 blocker 반영에 들었다. "serve까지 값이 닿는지"는 `apps/admin/e2e/stack.ts` 90행이 부모 환경을
  펼치는 것을 읽고, 둘째 기준이 실행 때 확인한다고 적었다.
- S9: 화면 동작 테스트에 스토리 6·9·11·18·31·36·38과 45초·Enter와 조합·keepalive를 더했고, 스크롤은 스토리 시험으로
  옮겼다. jsdom 30.1.1이 `isComposing`을 넘기고 `scrollHeight`가 0인 것은 세션 스크래치패드의 스크립트로 손으로 봤다.
- S10·S11: 저장의 판 번호와 그것이 틀릴 때 지우는 것, 교환은 `started`가 올 때 저장에 들고 거절과 알림과 입력창의 글은
  저장하지 않는 것을 정했다.
- S12: 끊김을 그 실행에서 마지막으로 받은 항목으로 가르고, 결정 응답이 `decided` 전에 끝나는 경우를 거절 표의 결정
  행에 넣었다.
- N1: vite가 이미 `^8.3.1`(잠금 8.3.1)인 것을 적었다(두 파일을 grep했다). N2: `tools`의 최소 길이 1. N3: S2에 들었다.
  N4: sdk 독스트링에 적을 것을 셋으로. N6: 공개 표면을 바꿀 때의 줄을 임베드 안내 목차에 더했다.
- 확인하지 못한 것 가운데 둘을 받았다. 스토리 14를 "새 탭에서 열면"으로 좁히고 닫은 탭 되살리기는 확인하지 않았다고
  적었다(묶음 견주기가 막는다). 사이트의 엄격한 `style-src`는 e2e 사례와 임베드 안내의 갈래로 넣었다.
- e2e의 로컬 nginx는 `AGENT_OS_NGINX`, 없으면 PATH의 `nginx`, 둘 다 없으면 실패로 정했다.

서두의 수를 다시 셌다. 사용자가 고른 것이 넷에서 다섯, 명세가 정한 것이 53에서 61이다. 표시를 grep하니 반영 전 파일
54, 지금 62이고 서두 자신이 드는 표시 하나를 빼면 53과 61이다. 서두의 묶음 열여덟을 더해도 61이다.

반영으로 새로 쓴 사실 문장(PR 직전 `bug-perf-review`에 밀 주장으로 넘긴다).

- 명세: "Node 24.19.0의 `new URL(v).origin`이 … 다섯을 … 바꿨다(명세 검토가 임시 스크립트로 손으로 봤다)"
- 명세: "jsdom 30.1.1은 `KeyboardEvent`의 `isComposing`을 그대로 넘겼다", "`scrollHeight`가 0이었다"
- 명세: "관리 화면 e2e의 준비가 serve의 환경에 부모의 환경을 펼치므로(`apps/admin/e2e/stack.ts`를 읽었다) 그것을 본뜨면 닿고"
- 명세: "`.cmd`를 거친 자식을 끊어도 손자 node가 남을 수 있었다"
- 명세: "Node 파서가 키 경로를 잘못 읽으면 위젯은 조용히 20,000을 쓰고 서버는 422를 내는데"
- 명세: "조여서 막히는 표기는 전에도 브라우저가 보내는 어떤 `Origin`과도 맞지 않던 항목"

다시 돌린 명령: `tools/check_adr_pointers.py`(0), `tools/check_md_tables.py`와 `tools/check_line_separators.py`(바뀐
문서 셋, 출력 없음), `tools/check_quotes.py`(경고 1건은 명세가 새로 정한 독스트링 문구라 따옴표 인용이 아니게 고쳤다).

### 티켓 나누기

`to-tickets`를 Read로 열어 따랐다. 열하나로 나눈 안(01 계약과 위젯 클라이언트, 02 core, 03 위젯 앱의 뼈대, 04 사이트
파일, 05 대화, 06 nginx와 e2e, 07 실패와 거절, 08 승인 묻기, 09 저장과 재접속, 10 페이지 안 방식과 임베드 안내, 11 실제
모델 e2e)을 표로 보이고, 고친 ADR 0024의 둘째 이력의 재승인과 함께 물었다. 앞선 답의 설명("core 티켓이 위젯 티켓을
막는다")과 달리 core가 실제 서버를 띄우는 e2e(06)부터 막고 대화(05)는 나란히 간다는 것을 짚었다. 처음 띄운 화면은 훅이
사실을 대 보라고 한 번 막았고, 합치는 안의 "여덟에서 아홉"을 "열하나에서 아홉"으로 고쳐 다시 띄웠다.

> 사용자(질문에 답): "이대로 열하나 (추천)" — 설명: 위 표대로 `.scratch/web-widget/issues/`에 파일 열하나를 씁니다.
> 대화(05)는 core(02)를 기다리지 않고 나란히 갑니다. core는 실제 서버를 띄우는 e2e(06)부터 막습니다.

> 사용자(질문에 답): "승인 (추천)" — 설명: 고친 이력을 명세와 함께 커밋합니다. 제목은 그대로이고, 본문에 '명령은 원칙
> I의 판정 명령과 따로다' 문단이 더해지며, 거부한 안이 둘에서 넷으로 늡니다.

표대로 `.scratch/web-widget/issues/`에 `01-contract-calling-item-and-limit-kind.md`부터
`11-widget-real-model-e2e.md`까지 열하나를 썼다. 모두 `ready-for-agent`이고, 막는 관계는 표 그대로다(01·03은
없음, 02는 01, 04는 03, 05는 01·04, 06은 02·05, 07은 06, 08은 07, 09는 08, 10·11은 06). 근거는 티켓마다 명세의
절 이름으로 가리키고, 화면이 있는 티켓은 `.scratch/web-widget/design/`의 화면 이름을 든다(디자인 README의 표와
대 보아 05에 `mk-limit`의 글자 수 둘을, 07에 `mk-rejection`을 더했다). 06과 10에는 설계 인터뷰의 프로브
(`nginx_relay/`, `widget_stack/`, `widget_tailwind/`)를 근거로 더했다.

명세에 없던 연결이 셋 생겨 티켓에 적었다. 첫째, 05·07·08은 뒤 티켓이 채울 자리를 그동안 어떻게 그리는지(병합
뒤의 틈)를 적고, 받는 티켓이 그 틈 동안의 시험을 바꾼다고 적었다. 둘째, 07이 06 뒤에 오는 까닭을 "06의 위젯 e2e가
CI에서 매번 돌아 화면을 크게 바꾸는 티켓부터 그 위에서 회귀를 본다"로 적었다. 셋째, 11은 기본 실행의 제외를
`-m "not llm"` 하나로 적은 곳(`tests/conftest.py` 독스트링)을 함께 고치고 잔존을 grep하라고 적었다. 셋 다 명세의
결정을 바꾸지 않는 차례와 범위의 글이라 명세는 고치지 않았다.

`.scratch/plan.md`의 web-widget 행에 2026-10-23 티켓 괄호를 더하고, 명세 괄호의 "core 티켓이 위젯의 티켓을
막는다"를 사용자가 고른 나누기대로 "계약 티켓 다음이 core 티켓이고, core 티켓은 실제 서버를 띄우는 위젯 e2e
티켓부터 막는다"로 고쳤다. 행의 상태는 `todo` 그대로다(`docs/agents/issue-tracker.md`, 티켓이 생긴 것만으로는
`todo`). 보안 훅이 10의 `<script src>`에 무결성 해시를 달라고 경고했는데, 티켓의 글이고 명세가 SRI를 범위 밖으로
둔 결정(Out of Scope)이 있어 그대로 두었다.

검사: `tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`가 티켓 열하나와 바뀐
문서에서 0으로 끝났다. 인용 대조(origin/main에 더한 줄만 보는 임시 스크립트)는 티켓에서 0건이었고, 일지의 "명세 검토
반영" 절에서 명세를 줄여 옮긴 인용 셋이 원문과 달라 원문 그대로 고쳤다(`paused` 뒤에 닫힌 스트림, 관리 화면 e2e의
준비, Node 파서의 키 경로). 셋 다 PR 직전 리뷰에 밀 사실 목록의 줄이다.

## 인계 (셀프 리뷰 직전)

티켓 열하나와 plan.md·일지를 마치고 커밋 전 셀프 리뷰(`/code-review`)를 부르자, 컨텍스트가 인계 문턱을 넘어
`hook_handoff`가 왔다. 지금 경계(`셀프 리뷰 직전`)는 이 세션이 넘겨받은 경계(`커밋 뒤`)와 다르고, 요청 범위("티켓까지")가
이 경계에서 끝나지 않으며, 일지에 이 세션의 `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없어 곁
세션이 아니다. 그래서 넘긴다. 이 세션의 지금 제목은 `docs/web-widget-spec-2`이고 `docs/web-widget-spec-2 (인계함)`으로
바꾼다. 띄운 백그라운드 작업은 없다(기록을 grep하던 명령은 TaskStop으로 멈췄다). `tools/model_sweep.py
docs/web-widget-spec-2`는 `스윕 밖`이었고 브랜치에 열린 PR이 없다.

커밋하지 않은 변경: `.scratch/web-widget/spec.md`와 `docs/adr/0024-…`(명세 검토 반영, 이 세션의 "명세 검토 반영" 절),
`.scratch/web-widget/issues/` 열하나(새 파일), `.scratch/plan.md`의 web-widget 행, 이 일지.

인계 지시문:

```
다음 작업: 기능 web-widget. 명세 검토 반영과 티켓 열하나를 썼고, 커밋 전 셀프 리뷰부터 이어 PR까지 간다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec web-widget
브랜치: docs/web-widget-spec-2
모델: Opus 5.5 / xhigh
읽을 것: docs/journal/2026-10-23-40-web-widget-spec.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main)부터 한다. 변경은 명세 검토 반영(spec.md, ADR 0024 둘째 이력, 사용자 재승인 받음), 티켓 열하나(.scratch/web-widget/issues/, 미추적), plan.md의 web-widget 행, 일지다. 명세 축의 요구는 spec.md와 일지의 "명세 검토"·"티켓 나누기" 절의 사용자 답 원문이다. 그 뒤 커밋, PR 직전 bug-perf-review(밀 주장은 일지의 "셀프 리뷰 반영"과 "명세 검토 반영" 절), PR, 병합이다. 옛 docs/web-widget-spec 브랜치는 명세가 대신하고, 지우기는 병합 뒤 주 체크아웃 세션이 사람에게 확인받고 한다. 일지 docs/journal/2026-10-23-40-web-widget-spec.md
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

제목을 바꿨고(`set_session_title`이 묻지 않고 바꿨다), 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-23T08:24:50Z

## 이어받은 세션 (셀프 리뷰 직전)

위 지시문으로 연 새 세션이다. 제목을 `docs/web-widget-spec-2`로 바꾸고, `git worktree list`에서 그 브랜치가
`.claude/worktrees/web-widget-spec-2`에 체크아웃된 것을 보고 EnterWorktree(path)로 들어갔다. `to-spec`을 Read로 열어
따랐다. `origin/main`은 `893e0fe8`(model-rerun 06, #370)로 앞서 있었다. 그 커밋이 바꾼 파일 15개는 모두 model-rerun의
것이고 이 브랜치가 바꾼 파일과 겹치지 않는다(`git diff --stat db92d68a origin/main`). 리뷰 도중에 합치면 두 축이 보는
`git diff db92d68a`에 model-rerun의 변경이 섞이므로, 리뷰의 고정점은 갈라진 자리 `db92d68a`로 두고 커밋한 뒤에 합친다.

> 사용자: ".claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. … 인자: web-widget … 이어받을 상태: 인계: 셀프
> 리뷰 직전 … 그 뒤 커밋, PR 직전 bug-perf-review(밀 주장은 일지의 "셀프 리뷰 반영"과 "명세 검토 반영" 절), PR,
> 병합이다 … 이번 요청 범위: 티켓까지"

셀프 리뷰(`/code-review`, base `db92d68a`, 바뀐 파일 15, 커밋 1, 미추적 11)의 두 축을 띄웠다. 커밋 `6a3436e8`까지는 앞선
셀프 리뷰를 지났으므로, 두 브리프에 `git diff HEAD`와 티켓 열하나를 먼저 보라고 적었다. 명세 축의 요구는 `spec.md`,
`to-tickets`의 나누기·꼴 규칙, 사용자 답 아홉의 라벨과 설명 원문, `to-spec`의 서두 수 세기다.

### 둘째 셀프 리뷰 — 표준 축

sonnet·high. Major 1, Minor 4, Nit 3. Node의 출처 다섯, jsdom 둘, `trim`과 `strip`, `stack.ts` 90행, vite 판, 서두의 수
(38, 5, 61), 시험 이름 다섯, 바이트 수 둘, conftest의 세 사실, 티켓의 Blocked by, 구현 파일 경로 없음을 맞다고 했다.

- Major: 명세 187행과 티켓 04의 "조여서 막히는 표기는 전에도 브라우저가 보내는 어떤 `Origin`과도 맞지 않던 항목"이
  거짓이다. 반례는 `null`(샌드박스 iframe, `file:`)과 http(s)가 아닌 스킴(`capacitor://localhost`)이다. 리뷰가
  `CORSMiddleware`의 `is_allowed_origin`에 둘을 넣어 True를 손으로 봤다.
- Minor: 명세 360행과 티켓 02의 "553개를 돌려 모두 지났다"가 프로브 README의 첫 실행 실패 단서를 뺐다.
- Minor: 명세 165행 "이 티켓이 위젯의 티켓을 막는다"가 431행과 티켓 03·04(계약과 나란히 감)와 부딪힌다.
- Minor: 티켓 06이 `docs/constitution/tech.md` 17행의 "잡 다섯"을 함께 고칠 목록에 넣지 않았다.
- Minor: 티켓 11에 `tests/conftest.py`가 `llm_widget`도 세게 하는 변경의 시험 기준이 없다(선례 `tests/test_conftest.py`).
- Nit: 손으로 본 측정 넷(Node 출처, jsdom, `.cmd` 손자, `trim`)에 명령이 없다. 명세 190행의 Vitest가 중복 프로젝트
  이름을 거부한다는 문장에 근거가 없다. 같은 알림 문구가 티켓 05·07·08·09에 되풀이된다.

### 둘째 셀프 리뷰 — 명세 축

본 세션의 모델을 물려받았다. Major 1, Minor 5, Nit 3. 서두의 수, S1~S12·N1~N6의 반영, Blocked by와 plan.md 행, ADR 0024
둘째 이력의 마커·명령·계기·거부한 안, 시험 이름과 rules 인용, 손으로 본 측정 다섯을 맞다고 했다.

- Major: 표준 축의 Major와 같다(`null`, 리뷰가 Starlette를 불러 손으로 봤다).
- Minor: 티켓 04 18행이 명세 185행의 "서버가 거절할 키나 값"을 셋으로 좁혔다. `main.py`는 판, 엄격한 타입, 발급자
  겹침과 `|`, PEM, `kid` 겹침, 에이전트 이름도 거절한다.
- Minor: 명세 213행 "iframe 방식의 요청은 같은 출처라 CORS를 지나지 않는다"가 어느 티켓에도 없다.
- Minor: 명세 190행 "두 산출물의 빌드에서 서는지는 e2e가 본다"의 iframe 몫이 티켓 06에 없다.
- Minor: ADR 0024 둘째 이력 95행이 사용자 답의 조건 "`tests/conftest.py`를 고쳐 그 마커도 세게 합니다"를 빠뜨렸다.
- Minor: 06과 11이 거짓으로 만드는 닫힌 문장이 함께 고칠 목록에 없다. `.claude/rules/http.md`의 "매 푸시에서 도는 것은
  e2e 하나다"와 "유일한 자리", `tests/test_main.py` 1967행의 "유일한 자리", `.claude/rules/tests.md`와 `operations.md`
  6행의 "LLM을 실제로 호출하는 테스트는 `llm` 마커를 붙인다".
- Nit: 사진 비교 도우미는 사용자가 고른 것인데 191행이 "(명세가 정했다)"로 표시했다. 그러면 서두의 수가 6과 60이다.
- Nit: 명세가 결정으로 받은 `mk-a11y` 메모의 "대화 목록 자체는 읽히지 않는다"가 본문과 티켓에 없다.
- Nit: 티켓 06의 What to build에 "실행 도중 도구 줄이 결말 전에 서는 것도 본다"의 수용 기준이 없고, "07이 그 위에 사례를
  더한다"는 07과 맞지 않는다.

### 둘째 셀프 리뷰 반영

지적마다 근거를 코드와 명령에 대 본 뒤 고쳤다. 두 축의 Major는 같은 것이었고, `CORSMiddleware`에 `"null"`과
`"capacitor://localhost"`를 주면 `is_allowed_origin`이 True임을 세션 스크래치패드의 스크립트로 손으로 다시 봤다. 허용
출처를 쓰는 것이 서버의 CORS 하나인 것(`server.py`의 조립과 `Sites.origins`)과, 그 CORS가 `Origin`을 글자 그대로 견주는
것(`https://Example.com`·`https://example.org:443`·`http://127.1`을 주면 브라우저의 직렬화에 모두 False)도 같은 길로 봤다.

고친 것.

- Major: 명세의 "사이트 파일의 판은 `"1"` 그대로다"를 다시 썼다. 막히는 표기를 두 갈래로 나눠, 대문자·기본 포트·경로·
  정규형이 아닌 IP는 전에도 죽어 있던 항목이고 `null`과 http(s)가 아닌 스킴은 전에 맞던 항목이라 이 검사가 뜻을 바꾸는
  의도한 비호환이라고 적었다. 판은 그대로 두는 결정을 유지했다. 그런 파일로는 serve가 구성 오류로 멈춰 조용히 바뀌지
  않는다. Out of Scope에 웹뷰 앱과 브라우저 확장을 더했다. 티켓 04의 같은 문장과 막히는 사례(`null`, `capacitor://localhost`)도
  고쳤다. 판을 올리지 않는 결정을 바꾸지 않아 묻지 않았다.
- 명세 185행과 티켓 04: 빌드가 읽지 못하는 것을 파일의 모양(깨진 TOML, 판, 모르는 키, 엄격한 타입)과 빌드가 읽는 두 값으로
  정하고, 서버만 읽는 값의 뜻(발급자, PEM과 `kid`, 에이전트 이름)은 빌드가 다시 판정하지 않는다고 좁혔다. 그런 파일로는
  serve가 뜨지 못해 조용히 지나가지 않는다. 티켓 04의 빌드 설정 시험을 그 갈래마다로 넓혔다.
- 명세 165행: 계약 티켓이 막는 것을 계약을 쓰는 티켓(core, 위젯 클라이언트를 쓰는 화면)으로 좁히고, 뼈대와 사이트 파일은
  나란히 간다고 적었다(사용자가 고른 나누기, Further Notes와 같다).
- 명세 360행과 티켓 02: 553개가 둘째 실행이고 첫 실행에서 Ctrl+C 시험 둘이 부하 아래 실패했으며 패치 몫은 가르지 못했다는
  단서를 더했다.
- 닫힌 문장의 잔존(표준 축 tech.md, 명세 축 넷): 반례만 덧붙이지 않고 일반 조항으로 적었다. 명세 Testing Decisions 4와 6,
  티켓 06과 11에 새 잡(새 마커)이 거짓으로 만드는 닫힌 문장을 그런 말로 grep해 잔존이 0인지 보는 조항을 두고, 지금 아는 자리를 예로 들었다
  (`tech.md`의 "잡 다섯", `http.md` 문장 셋, `tests/test_main.py` 독스트링, `tests.md`, `operations.md` 6행 둘). 헌법
  문서는 판을 patch로 올린다는 것(`tools/check_constitution_version.py`)과 바꾼 rules를 새 세션에서 확인한다는 것도 적었다.
- 티켓 11: conftest의 셈을 pytester 시험이 먼저 빨갛게 보는 기준(선례 `tests/test_conftest.py`의 토큰 합계 시험 둘)을 더했다.
- ADR 0024 둘째 이력: 사용자 답의 조건 "`tests/conftest.py`를 고쳐 그 마커도 세게 합니다"를 본문에 더했다(지금 합계는
  `llm` 마커만 센다). 승인받은 이력에 사용자 답의 글을 채운 것이라 다시 묻지 않았다.
- 티켓 05: iframe의 API 기준 주소(같은 출처, CORS 없음)와, 대화 목록 자체에 `aria-live`·`role="log"`를 달지 않는 것을
  더했다. 명세 접근성 절에도 그 한 줄을 넣었다(`mk-a11y` 메모의 "대화 목록 자체는 읽히지 않는다").
- 티켓 06: "도구 줄이 결말 전에 선다"와 iframe 산출물의 CSS를 수용 기준으로 더하고, 첫 사례에 같은 출처의 요청을 더했다.
  "07이 사례를 더한다"를 "07과 08은 사례를 더하지 않고 이 e2e로 회귀를 본다"로 고쳤다. 명세 e2e 목록의 "SSE가 결말 전에 흐르는 것"에 그것을
  위젯 화면에서 보는 법을 붙였다.
- 서두의 수: 사진 비교 도우미는 결정을 승인받을 때 사용자가 고른 것이라 191행을 사용자 선택으로 표시하고, 서두를 여섯과
  예순으로, 배치와 빌드 묶음을 여덟로 고쳤다. "(명세가 정했다" 표시는 61개이고 서두 자신의 하나를 빼면 60이며, 묶음
  열여덟의 합도 60이다.
- 손으로 본 측정의 명령: Node 출처 다섯(`node -e`로 `new URL(v).origin`), `trim`과 `strip`(`node -e`와 `uv run python -c`),
  jsdom(`node -e`로 `web`의 jsdom 30.1.1)을 다시 돌려 명령과 함께 적었다. 모두 명세의 서술과 같았다. `.cmd` 손자는 명세
  검토가 보고했고 명령이 남지 않았다고 적었다. Vitest의 중복 이름 거부는 Vitest 5.0.2 배포 코드의 오류 문구를 grep해
  근거로 적었다.

남긴 것과 이유.

- 표준 축 Nit(같은 알림 문구가 티켓 05·07·08·09에 되풀이): 티켓은 새 컨텍스트 하나에서 혼자 읽혀야 한다(`to-tickets`의
  vertical slice 규칙). 문구의 원천은 명세의 표이고 티켓은 그것을 옮긴 것이다.
- 인용 대조 경고 둘(일지 421·424행): 앞 세션이 그때의 명세 문장을 옮긴 기록이고 이번 반영이 원문을 고쳤다.

반영으로 새로 쓴 사실 문장(PR 직전 `bug-perf-review`에 밀 주장으로 넘긴다).

- 명세: "지금 허용 출처를 쓰는 것은 서버의 CORS 하나이고(서버의 조립을 읽었다), 그 CORS는 `Origin`을 글자 그대로 견준다"
- 명세: "`allow_origins`에 `"null"`과 `"capacitor://localhost"`를 주면 둘에 True였고"
- 명세: "`null`은 브라우저가 출처가 불투명한 문맥(샌드박스 iframe, `file:` 페이지)에서 보내는 값이라 어느 사이트든 그런
  문맥을 지어 그 항목에 맞출 수 있으므로"
- 명세: "서버만 읽는 값의 뜻(발급자의 빔·겹침·구분 문자, 공개 키의 PEM과 `kid`의 겹침, 열 에이전트의 이름 패턴)은 빌드가
  다시 판정하지 않는다. 그 값이 틀린 파일로는 serve가 뜨지 못해"
- 명세: "같은 `node -e`에서 `height: 50px; overflow: auto`인 상자에 문단 둘을 넣어도 `scrollHeight`가 0이었다"
- 명세: "Vitest 5.0.2의 배포 코드에 `is not unique. All projects should have unique names.`라는 오류 문구가 있다"
- 명세와 티켓 06·11: 닫힌 문장의 지금 아는 자리 목록(`tech.md`의 "잡 다섯", `http.md`의 "둘째 구동자", "e2e 하나",
  "유일한 자리", `tests/test_main.py` 독스트링, `tests.md`, `operations.md`)과 "`tools/check_constitution_version.py`가
  그것을 본다"
- ADR 0024 이력: "지금 토큰 합계는 `llm` 마커의 시험만 세므로"

다시 돌린 명령: `tools/check_adr_pointers.py`(0), `tools/check_md_tables.py`(0)와 `tools/check_line_separators.py`(0)를 바뀐
문서에, `tools/check_quotes.py`를 바뀐 문서와 티켓 열하나에 돌렸다. 인용 경고 넷 가운데 명세 190행은 저장소 밖 원문이라
코드 스팬으로 바꾸고 일지 528행은 리뷰의 요약이라 따옴표를 뗐다. 나머지 검증 명령은 커밋의 pre-commit으로 갈음한다.

### 커밋 (둘째)

커밋 직전 `git branch --show-current`는 `docs/web-widget-spec-2`였다. `tools/sibling_overlap.py`가 1로 끝났다. 번호 겹침은
없었지만 이 일지(2026-10-23-34)가 origin/main의 최신 일지 2026-10-23-36보다 이름순으로 앞이라, 다음 세션이 이 일지의
"다음"을 지나친다는 판정이었다. `--move`로 이 일지를 2026-10-23-40으로 옮겼고, 도구가 명세, ADR 0023·0024·0039,
`plan.md`, 프로브 `pnpm_spawn.py`, 이 일지의 인용을 함께 고쳤다. 도구가 옮기지 않는 꼴을 grep해 이 일지의 "일지 34"
하나를 "이 일지"로 고쳤다. origin/main이 `db92d68a`에서 `893e0fe8`로 움직였고 그사이 바뀐 파일은 모두 model-rerun의 것이라
이 브랜치가 따를 새 규약은 없었다(`git diff --name-only HEAD...origin/main`).

커밋 `d91df0b1`(파일 19, +1240 −348). pre-commit은 모두 통과했다. ruff 둘, `tools/run_checks.py`의 검사 열(zizmor,
check-ticket, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, web-verify 323.7초,
pytest 342.2초), 마크다운 표, 줄 구분 문자, 변이 표, 인용 대조, 커밋 메시지다. 카나리아 명세 모양과 헌법 판은 대상 파일이
없어 `Skipped`였다(이 커밋은 헌법 문서를 고치지 않았다). 그래서 손으로 치는 검증 명령 다섯은 이 결과로 갈음한다.

인용 대조 경고 다섯 가운데 421·424행은 위 "남긴 것"대로 둔다. 600행은 명세 187행과 글자가 같은데 원문 안의 따옴표와 코드
스팬 때문에 경고가 났다. 572행은 요약을 따옴표로 감싼 것이라 따옴표를 뗐고, 581행은 티켓 06 5행의 "사례를 더하지 않고"를
빠뜨려 원문대로 고쳤다. 이 두 고침은 커밋 뒤라 아직 커밋하지 않았다.

## 인계 (커밋 뒤)

커밋 `d91df0b1`이 지나자 컨텍스트가 인계 문턱을 넘은 채 경계 `커밋 뒤`에 와 `hook_handoff`가 왔다. 커밋은 성공했고, 지금
경계(`커밋 뒤`)는 이 세션이 넘겨받은 경계(`셀프 리뷰 직전`)와 다르며, 요청 범위("티켓까지")는 PR과 병합까지라 이 경계에서
끝나지 않는다. 일지에 이 세션의 `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이 아니다.
그래서 넘긴다. 이 세션의 지금 제목은 `docs/web-widget-spec-2`이고 `docs/web-widget-spec-2 (인계함)`으로 바꾼다. 띄운
백그라운드 작업은 남지 않았다(커밋 명령은 끝났다). `tools/model_sweep.py docs/web-widget-spec-2`는 `스윕 밖`이었고, 브랜치에
열린 PR이 없다(`gh pr view`가 `no pull requests found`). 커밋은 아직 푸시하지 않았다.

커밋하지 않은 변경: 이 일지(인용 두 줄 고침, 커밋 결과, 이 인계 절).

인계 지시문:

```
다음 작업: 기능 web-widget. 명세 검토 반영과 티켓 열하나를 커밋했고(d91df0b1), origin/main을 합친 뒤 PR 직전 리뷰부터 PR과 병합까지 간다
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec web-widget
브랜치: docs/web-widget-spec-2
모델: Opus 5.5 / xhigh
읽을 것: docs/journal/2026-10-23-40-web-widget-spec.md
이어받을 상태: 인계: 커밋 뒤. 둘째 셀프 리뷰를 반영해 d91df0b1로 커밋했고 pre-commit은 모두 통과했다(카나리아 명세 모양과 헌법 판은 대상 파일이 없어 Skipped). 푸시하지 않았고 열린 PR은 없다. 커밋하지 않은 변경은 이 일지(인용 두 줄 고침, 커밋 결과, 인계 절)다. 남은 단계는 origin/main을 합치고(git merge origin/main), 일지를 커밋하고, PR 직전 /security-review와 bug-perf-review를 나란히 돌려(밀 주장은 일지의 "셀프 리뷰 반영", "명세 검토 반영", "둘째 셀프 리뷰 반영" 절) 반영한 뒤, PR을 열고 반영과 병합까지 가는 것이다. 옛 docs/web-widget-spec 브랜치는 명세가 대신하고, 지우기는 병합 뒤 주 체크아웃 세션이 사람에게 확인받고 한다. 일지 docs/journal/2026-10-23-40-web-widget-spec.md
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

제목을 바꿨고(`set_session_title`이 묻지 않고 바꿨다), 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-23T09:07:04Z

## 이어받은 세션 (커밋 뒤, 둘째)

위 지시문으로 연 새 세션이다. 제목을 `docs/web-widget-spec-2`로 바꾸고, `git worktree list`에서 그 브랜치가
`.claude/worktrees/web-widget-spec-2`에 체크아웃된 것을 보고 EnterWorktree(path)로 들어갔다. `to-spec`을 Read로 열어
따랐다.

> 사용자: ".claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. … 인자: web-widget … 이어받을 상태: 인계: 커밋
> 뒤 … 남은 단계는 origin/main을 합치고(git merge origin/main), 일지를 커밋하고, PR 직전 /security-review와
> bug-perf-review를 나란히 돌려 … 반영한 뒤, PR을 열고 반영과 병합까지 가는 것이다 … 이번 요청 범위: 티켓까지"

`git fetch origin` 뒤 `origin/main`은 그대로 `893e0fe8`이었고, `git merge origin/main`이 충돌 없이 병합 커밋을 만들었다
(model-rerun 06의 파일 15개, 이 브랜치가 바꾼 파일과 겹치지 않는다). `tools/sibling_overlap.py`는 번호 겹침 없음이었다.
함께 고친 파일 후보는 `.scratch/plan.md` 하나(PR #356, 워크트리 `02-build-tokens-json`·`mcp-shutdown-spec`)다.

이 일지를 `a5364812`로 커밋했다. pre-commit은 검사 러너 열(pytest 332.4초, web-verify 280.3초 등), 마크다운 표, 줄 구분 문자,
변이 표, 인용 대조, 커밋 메시지가 Passed였고, ruff 둘과 카나리아 명세·헌법 판은 대상 파일이 없어 Skipped였다.

### ruff 서식이 명세의 코드 블록을 짚었다

Skipped인 ruff 둘을 CLAUDE.md 검증 명령 절대로 손으로 쳤다. `uv run ruff check .`는 초록이었고 `uv run ruff format
--check .`가 1로 끝났다. ruff 0.16.8이 마크다운 안의 파이썬 코드 블록까지 서식을 판정해, 명세의 시제품 조각(최상위 함수
둘 사이의 빈 줄 하나)을 짚었다. pre-commit의 ruff 훅은 `types: [python]`이라 스테이지된 `.py`만 받고, CI는 `ruff format
--check .`로 저장소 전체를 본다. 그래서 앞 커밋 `d91df0b1`에서 ruff 둘이 Passed였어도 명세는 보지 않았고, 푸시했으면 CI의
`python` 잡이 빨갰다. `uv run ruff format .scratch/web-widget/spec.md`로 빈 줄 하나를 더해 고쳤다(1018 파일 초록).

회고 후보: pre-commit의 ruff 훅이 CI와 같은 파일을 보지 않는다. `.md`만 바꾼 커밋은 ruff가 Skipped라 손으로 쳐서 잡히지만,
`.py`와 `.md`를 함께 바꾼 커밋은 Passed로 나와 갈음으로 읽힌다. 고침은 훅의 `types`를 `types_or: [python, markdown]`으로
넓히는 것이고, 그 전에 ruff가 실제로 보는 확장자를 재야 한다. 단계를 닫는 회고에 넘긴다.

### PR 직전 리뷰

`coderabbit auth status`가 `Seat: not assigned`(Plan Free)라 CLI 축이 돌지 못해 대체 둘을 돌렸다. `bug-perf-review`는 변경
파일 26개를 둘로 나눠 나란히 띄웠다(A: 명세·티켓 01~05·ADR 0039·0023·0010·용어집·core 프로브, B: 티켓 06~11·ADR
0024·plan.md·프로브 README·`pnpm_spawn.py`·일지). 밀 주장은 위 세 반영 절의 목록을 스물둘로 나눠 넘겼다. 호출 예산
40을 A는 41, B는 40에서 마쳤다. `/security-review`는 일지를 커밋하고 origin/main을 합친 뒤에 돌렸다.

- `/security-review`: 후보 하나(Medium, 확신 7). 페이지 안 번들이 `document.currentScript`의 `src`에서 기준 주소를 읽는데,
  사이트 페이지의 `<img name="currentScript" src="https://<다른 출처>/">`가 그 자리를 가리면(DOM clobbering) 요청마다
  서명 토큰이 그 출처로 간다. 거짓 양성 거르기가 확신 6을 줘 스킬의 문턱(8) 밖이라 보고는 "발견 없음"이다. 구현이
  `instanceof`로 좁힐지 `getAttribute`로 좁힐지 문서가 정하지 않았고 고치는 값이 작아 고쳤다.
- `bug-perf-review` A: 유효 Minor 4, 보류 1. 밀 주장 열하나는 모두 근거와 맞았다(5번은 수치는 맞고 전제가 어긋났다).
  - Minor: `256k`의 근거 "서버가 받는 가장 큰 본문"이 틀렸다. 결정 본문의 거부 사유는 최대 길이가 없다(결정 본문
    모델을 읽어 확인했다).
  - Minor: classic 스크립트가 CORS 없이 실리는 것은 `crossorigin` 속성이 없을 때뿐이다.
  - Minor: 허용 출처 표기 규칙에 포트의 범위가 없다. 이 세션이 `node`로 재니 Node 24.19.0의 `new URL`이 65536과
    99999를 `ERR_INVALID_URL`로 거절하고 65535와 0은 받았다.
  - Minor: 티켓 04의 빌드 실패 갈래에 필수 키 빠짐이 없다(서버의 사이트 파일 모델에서 기본값 없는 다섯을 grep했다).
  - 보류: IPv4를 품은 IPv6의 `compressed`가 브라우저와 갈릴 수 있다. 이 세션이 재니 파이썬 3.12.10과 Node 24.19.0이
    모두 `::ffff:102:304`를 냈다. 오탐이지만 판에 따라 갈릴 수 있는 자리라 막히는 사례로 픽스처에 넣었다.
- `bug-perf-review` B: 유효 Major 1, Minor 1, 보류 1. 밀 주장은 맞다 8, 어긋난다 1(9번, 아래 Minor), 확인 못 함 2.
  - Major: 티켓 11이 Playwright 프로젝트 `llm`을 CI에서만 빼, 11이 병합된 뒤로 06의 로컬 명령(프로젝트를 지정하지
    않은 `playwright test`)이 실제 모델을 부른다. 07~10의 검증이 그 명령이다(티켓을 읽어 확인했다).
  - Minor: 닫힌 문장의 지금 아는 자리 목록이 `stack.ts` 머리 주석, `tests/test_main.py`의 둘, `tests/test_conftest.py`,
    `tools/llm_tokens.py`, `.coderabbit.yaml`, `tools/hook_env_read.py`를 빠뜨렸다. grep으로 줄마다 확인했다.
  - 보류: Windows의 nginx는 master와 worker가 따로라 `stack.ts`의 `kill()`로는 다 내리지 못할 수 있다.

고친 것.

- 명세 "API의 기준 주소"와 티켓 10: `HTMLScriptElement`의 인스턴스일 때만 `src` 속성에서 읽고, 아니면 요청도 토큰
  함수도 부르지 않고 위험 알림을 보인다. e2e에 가리는 `<img>`를 둔 페이지 사례를 더했다.
- 명세 "번들의 꼴"·"글꼴"과 티켓 10: 번들 응답에도 `Access-Control-Allow-Origin: *`를 단다. e2e에
  `crossorigin="anonymous"` 사례를 더했다.
- 명세 "승인 묻기"와 티켓 08: 사유에 입력창과 같은 상한을 둔다. 새 결정이라 표시 "(명세가 정했다: 사유의 상한)"을 달고
  `256k`의 근거를 요청 글자 수로 묶인 본문으로 좁혔다. 티켓 06의 틀 주석에 413의 갈래를 더했다.
- 명세 "허용 출처의 표기 검사"와 티켓 04: 포트는 65535 이하, 막히는 사례 둘(`:65536`, `[::ffff:1.2.3.4]`), 필수 키 빠짐.
- 명세 Testing Decisions 6과 티켓 11: 프로젝트 `llm`은 감싸는 시험이 준 `AGENT_OS_WIDGET_LLM=1`이 있을 때만 서고,
  위젯 앱의 vitest `node` 시험이 그 목록을 본다.
- 명세 Testing Decisions 4·6과 티켓 06·11: 닫힌 문장의 자리를 더하고 grep 말에 백틱 없는 llm 마커와 `-m llm`을 넣었다.
  "구동자"가 ASGI로 직접 부르는 시험의 이름과 겹친다는 것을 적었다.
- 티켓 06: nginx는 master와 worker를 함께 거두고, 이 PC에서 돌린 뒤 남은 프로세스와 포트를 본다.
- 서두의 수: 명세가 정한 것 예순에서 예순하나. "(명세가 정했다" 표시는 62개이고 서두 자신의 하나를 빼면 61이며, 묶음의
  합(승인 셋)도 61이다.

ADR 0023 54행과 ADR 0024 49행(nginx의 본문 상한을 사이트 파일의 요청 크기보다 크게 두어 파이썬의 422가 답하게 한다)은 요청 크기
초과의 문장이라 결정 본문의 사유에는 닿지 않아 글자 그대로 참이다. 포인터를 달지 않았다.

다시 돌린 명령: `tools/check_md_tables.py`와 `tools/check_line_separators.py`(바뀐 문서 여섯, 출력 없음),
`tools/check_quotes.py`(같은 여섯, 인용 19건에 경고 없음), `tools/check_adr_pointers.py`(0), `uv run ruff format --check .`(1018
파일 초록).

### 커밋과 PR

커밋 직전 `git branch --show-current`는 `docs/web-widget-spec-2`였고 `tools/sibling_overlap.py`는 번호 겹침 없음(origin/main
`893e0fe`)이었다. `443eb66f`로 커밋했다(파일 7, +98 −25). pre-commit은 검사 러너 열(pytest 383.5초, web-verify 275.5초,
run-hooks 94.1초 등), 마크다운 표, 줄 구분 문자, 변이 표, 인용 대조, 커밋 메시지가 Passed였고, ruff 둘과 카나리아 명세·헌법
판은 대상 파일이 없어 Skipped였다. ruff 둘은 위에서 손으로 쳤다. 인용 대조 경고 1건(이 일지의 ADR 0023·0024 요약을 따옴표로
감싼 줄)은 따옴표를 떼고 괄호로 고쳤다. 이 고침은 커밋 뒤라 아직 커밋하지 않았다.

`git fetch origin` 뒤 origin/main은 그대로 `893e0fe8`이었다. 브랜치를 푸시하고 PR [#373](https://github.com/njh6803/agent-os/pull/373)을
열었다(제목 `docs: 위젯 명세와 티켓 열하나를 쓰고 런타임이 호출 이벤트를 흘린다는 결정을 올린다 (web-widget)`). PR 체크리스트에
PR 직전 리뷰 셋의 결과와 반영을 적었다. `@coderabbitai review` 코멘트는 아직 남기지 않았다.

## 인계 (PR 연 뒤)

PR을 열자 컨텍스트가 인계 문턱을 넘은 채 경계 `PR 연 뒤`에 와 `hook_handoff`가 왔다(`hook_pr_next_session`도 함께 왔다).
PR은 열렸고, 지금 경계(`PR 연 뒤`)는 이 세션이 넘겨받은 경계(`커밋 뒤`)와 다르며, 요청 범위("티켓까지")는 병합까지라 이
경계에서 끝나지 않는다. 일지에 이 세션의 `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이
아니다. 그래서 넘긴다. 앞서 `443eb66f` 커밋 때 온 `커밋 뒤` 계기는 이 세션의 지시문이 `인계: 커밋 뒤`로 시작해 넘기지 않았다.

이 세션의 지금 제목은 `docs/web-widget-spec-2`이고 `docs/web-widget-spec-2 (인계함)`으로 바꾼다. 띄운 백그라운드 작업은 남지
않았다(커밋 둘과 리뷰 서브에이전트 넷은 끝났다). `tools/model_sweep.py docs/web-widget-spec-2`는 `스윕 밖`이었다.

커밋하지 않은 변경: 이 일지(인용 한 줄 고침, 커밋과 PR 절, 이 인계 절).

인계 지시문:

```
다음 작업: 기능 web-widget. PR #373(명세와 티켓 열하나)을 열었고, 봇 회차부터 반영과 병합까지 간다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec web-widget
브랜치: docs/web-widget-spec-2
모델: Sonnet 5.5 / high
읽을 것: docs/journal/2026-10-23-40-web-widget-spec.md
이어받을 상태: 인계: PR 연 뒤. PR #373을 열었고 순서 1의 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. 커밋하지 않은 변경은 일지(인용 한 줄 고침, "커밋과 PR" 절, 인계 절)이고 봇 회차의 반영 커밋이나 단계를 닫는 일지 커밋에 싣는다. 이 세션이 명세 단계를 닫으므로 병합 전에 회고(retro)와 일지 "다음"을 마쳐 푸시한다. 회고에 넘길 후보는 일지 "ruff 서식이 명세의 코드 블록을 짚었다" 절(pre-commit의 ruff 훅이 .md의 코드 블록을 보지 않는다)이다. 옛 docs/web-widget-spec 브랜치와 워크트리는 명세가 대신하고, 지우기는 병합 뒤 주 체크아웃 세션이 사람에게 확인받고 한다. 일지 docs/journal/2026-10-23-40-web-widget-spec.md
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

제목을 바꿨고(`set_session_title`이 묻지 않고 바꿨다), 워크트리 잠금은 이미 풀려 있었다(`is not locked`). PR #373은 앱에 묶여 있다(`get_status`의 `bound: true`).

open-session을 부른다 2026-10-23T09:51:55Z

## 이어받은 세션 (PR 연 뒤)

위 지시문으로 연 새 세션이다. 제목을 `docs/web-widget-spec-2`로 바꾸고, `git worktree list`에서 그 브랜치가
`.claude/worktrees/web-widget-spec-2`에 체크아웃된 것을 보고 EnterWorktree(path)로 들어갔다. `to-spec`을 Read로 열어
따랐다. 앱에는 PR #373이 묶여 있지 않아(`get_status`의 `bound: false`) `bind_pr`로 묶었다.

> 사용자: ".claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. … 인자: web-widget … 다음 작업: 기능 web-widget.
> PR #373(명세와 티켓 열하나)을 열었고, 봇 회차부터 반영과 병합까지 간다 … 이번 요청 범위: 티켓까지"

## 봇 회차

`gh pr view`의 `headRefOid`가 로컬 HEAD와 같은 `443eb66f`인 것을 보고 `@coderabbitai review`를 남긴 뒤 `tools/wait_ci.py 373`을
백그라운드로 띄웠다. 대기는 `끝: 모두 통과. CodeRabbit: Review rate limited`로 끝났다. 검사 여덟(`python`, `claude-review`,
`e2e`, `ticket`, `verify`, `visual`, `web`, `CodeRabbit`)이 모두 SUCCESS였다.

- CodeRabbit: 한도에 걸려 리뷰가 없다(요약 코멘트가 `Review limit reached`, 다음 무료 리뷰까지 51분). 한도에 걸린 푸시는 회차로
  세지 않는다(next-session 순서 1의 2). 보안·버그·성능 축은 PR 직전에 돈 대체 둘(`/security-review`, `bug-perf-review` 둘)의 결과가 맡는다
  (`operations.md` 리뷰 파이프라인 3의 "CodeRabbit PR 리뷰는 OSS 시간당 한도에 자주 걸린다" 항목). 51분을 기다려 다시 청하지 않는다.
- claude-review: 첫 회차이고 `지적 없음`이다(헤드 `443eb66f`). 코멘트가 실제로 있고, ADR 포인터 달림(0023·0024)과 ADR 0039가
  거짓으로 만드는 `core.md` 문장의 고침 자리(티켓 02)까지 대조해 적었다. 문서만 바뀐 PR이라 `sdk`·`openapi.json`의 계약 변경과
  디스크 형식 변경이 없다는 것도 적었다.
- 반영할 지적이 없어 고친 것도, 뒤로 넘긴 일도 없다. PR 본문은 이 세션이 범위를 넓히지 않아 고치지 않았다.

## 회고

이 단계(web-widget 명세와 티켓)를 닫는 회고다. 원천은 이 일지 전체(다섯 번 인계한 여섯 세션)와 이 세션이다. 후보 하나, 승인 1,
기각 0, 넘김 없음. 이 세션은 지시문대로 봇 회차와 일지, 병합만 해 새로 난 실수가 없었다. 일지에 "번복"이나 "갈린 곳" 절은 없다.

1. **승인(대기열 319에 2회차).** 일지 "ruff 서식이 명세의 코드 블록을 짚었다" 절의 사건이다. pre-commit의 ruff 훅이 `types:
   [python]`이라 스테이지된 `.py`만 받는데 CI는 `ruff format --check .`로 저장소 전체를 본다. 명세(`.md`)의 시제품 조각을 ruff 0.16.8이
   짚었고, 앞 커밋 `d91df0b1`에서 ruff 둘이 Passed였어도 명세는 보지 않았다. 푸시했으면 CI의 `python` 잡이 빨갰다. 손으로 쳐서
   푸시 전에 잡았다. 대기열 319(병합 커밋 뒤 전체 린트를 돌리지 않아 CI가 잡은 사건, 1회차)와 같은 가족이라 새 행을 쓰지 않고 그
   행에 회차를 더했다. 4단계의 세 조건은 다음과 같다. 사건: 위. 층: 훅(pre-push의 전체 린트)이 지침보다 높다. 되돌림: PR 하나.
   더하는 것의 문턱(세 번째 또는 손상)에 아직 닿지 않아(손상은 없었다) 지금 반영하지 않는다. 처방에 `ruff format --check .`와 `.md`
   코드 블록, 훅의 `types_or`로 넓히는 길이 병합 커밋 뒤의 전체 린트를 덮지 못한다는 것, 넓히기 전에 ruff가 실제로 보는 확장자를
   잰다는 것을 더했다.

일지에만 남기는 것: 인용 대조(`check_quotes`)가 일지가 옮긴 인용을 여러 번 짚었고, 그때마다 훅이 그 자리에서 알려 고쳤다. 이미 있는
검사가 잡은 것이라 후보로 세지 않는다. 스펙 검토(`spec-reviewer`)가 낸 blocker(실제 모델 e2e를 `-m llm`에 두면 원칙 I의 판정이
nginx를 요구한다)는 리뷰가 제 몫을 한 것이다. 선택 화면의 설명에 틀린 기술 조건이 들어 한 번 바로잡아 다시 물은 일은 `grilling`의 '옮길 때'가
이미 처방한 절차를 따른 것이다. 대기열 만료는 `tools/queue_open_rows.py`와 `git fetch origin` 뒤 `--ref origin/main`
둘 다에서 없었다(두 출력 모두 열린 행 106개).

## 다음

- 병합 뒤의 다음 단계는 구현이다. `.scratch/web-widget/issues/`의 티켓 열하나 가운데 `Blocked by`가 없는 것은 01(계약: `calling`
  항목과 `Limit` 종류, api-client의 위젯 클라이언트)과 03(위젯 앱의 뼈대, `/widget` iframe 페이지)이다. 둘은 서로 막지 않아 나란히 여는
  묶음이다(`next-session` 2단계의 1). 시작 프롬프트는 `/implement .scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md`와
  `/implement .scratch/web-widget/issues/03-widget-app-skeleton.md`, 모델 `Opus 5.5 / xhigh`다. 02는 01이, 04는 03이, 05는 01·04가
  막고, 06은 02·05가 막는다.
- 01은 계약 티켓이라 `sdk`·`openapi.json`·ADR 0023·0010의 포인터를 건드린다. 02(core)가 `.claude/rules/core.md`의 "같은 태스크에서 돈다"와
  `tests/core/test_run.py`의 단언을 ADR 0039대로 고친다. 병합 직후 01과 02 사이의 틈에서 문서와 코드가 어긋나지 않게 01은 `calling`의
  한 줄 설명이 시점을 말하지 않는다(티켓 01의 "병합 뒤에 틈이 있다" 문단).
- 옛 `docs/web-widget-spec` 브랜치와 워크트리(PR 없음, 커밋 `8acd9a48`)는 이 명세가 대신한다. 지우기는 병합 뒤 주 체크아웃 세션이 사람에게
  확인받고 한다. `tidy-checkouts`는 PR이 없는 워크트리를 지우지 않는다.
- 이 PR은 워크트리에서 병합한다. 주 체크아웃은 당기지 않는다.
- 봇 회차에서 뒤로 넘긴 일은 없다. 대기열 319는 2회차로 열려 있고 3회차를 기다린다.
