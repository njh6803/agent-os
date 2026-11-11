# 2026-11-11 (20:50) base-agent 티켓 01: 두 끝의 계약과 집행

세션 제목: `feature/01-contract-agent-manifest-turn-and-tool-call-limits`(인계 뒤 `(인계함)`). 브랜치 `feature/01-contract-agent-manifest-turn-and-tool-call-limits`, 워크트리 `.claude/worktrees/01-contract-agent-manifest-turn-and-tool-call-limits`, 기준 커밋 `377675eef`(#528). 모델 `claude-sonnet-5-5` high. next-session 지시문으로 연 새 세션이고, 첫 턴에 제목을 바꾸고 `tidy-checkouts`를 돈 뒤 `EnterWorktree`로 들어왔다. 파일 이름의 시각은 컨텍스트가 인계 문턱을 넘어 이 일지를 쓴 때다. 구현과 검증은 마쳤고 커밋하지 않았다.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/base-agent/issues/01-contract-agent-manifest-turn-and-tool-call-limits.md
>
> 다음 작업: 에이전트 매니페스트에 선택 칸 `max_turns`·`max_tool_calls`를 더하고 런타임이 지키게 하는 계약 티켓(03을 막는다)
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 2 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: `/implement .scratch/base-agent/issues/01-contract-agent-manifest-turn-and-tool-call-limits.md`
> 브랜치: `feature/01-contract-agent-manifest-turn-and-tool-call-limits`
> 모델: Sonnet 5.5 / high
> 읽을 것: `docs/journal/2026-11-11-1555-base-agent-tickets.md`의 "다음", 나란히 도는 티켓 `.scratch/base-agent/issues/02-fake-doc-search-server-fixture.md`
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

이 뒤로 사용자의 새 말은 없다(결정이나 교정 없음).

## 한 것

- **sdk.** `src/agent_os/sdk/manifest.py`에 `max_turns`·`max_tool_calls`를 더했다. 모양은 `conversation_limit`과 같다(1 이상의 엄격한 정수, 기본 없음, 숫자 기본값과 최댓값을 적지 않는다). 에이전트가 아닌 종류가 적으면 `requires_approval`처럼 거부한다.
- **core.** `core/loop.py`의 `run_loop`가 `max_turns` 인자를 받는다(기본 10). `core/run.py`에서 `_Limits`가 두 끝을 들고 `_prepare`가 맨 앞에서 `max_turns` 10 초과를 `PluginError`로 거부한다. `_Context._call`이 `_stay_paused()` 바로 뒤에 시도를 세고, `_take_verdict` + `_resume` 바로 뒤, 연결에 없는 이름 앞에서 끝 넘음을 거부한다(문구 `도구 호출 횟수를 넘었다: 이 실행은 도구를 <N>번까지 부른다`, `rule=None`).
- **계약 파일.** `openapi.json`(`PYTHONUTF8=1 uv run python tools/export_openapi.py`)과 api-client 생성물(`pnpm -C web run generate:api-client`)을 다시 뽑았다.
- **관리 화면.** 매니페스트를 손으로 적은 여섯 파일에 두 칸(`null`)을 더했다. 사진 정답은 PluginDetail 여덟 장(enabled·disabled × 1280·320 × light·dark)이 바뀌었고 차이 사진으로 본 바뀐 곳은 매니페스트 JSON 두 줄과 그 아래로 밀린 줄뿐이다. `visual:admin:update`로 다시 찍었고 다시 돌린 `visual:admin`은 초록이다.
- **문서.** `.claude/rules/core.md`(루프의 끝, 준비 순서, 승인 게이트의 끝 판정, 거부 문구, 재개의 `rule`)와 `.claude/rules/sdk.md`(두 칸 항목, `tool_called.rule` 비움)를 맞췄다. 루프 모듈·`_call`·`_refuse`·`_prepare`·모듈 독스트링도 맞췄다.
- **티켓.** 체크박스를 채우고(마지막 "검증 명령이 모두 초록이다"만 비워 둠) `Status: done`으로 바꿨다. `uv run python tools/plan_table.py`로 `.scratch/plan.md`를 갱신했다. 마지막 열린 티켓이 아니라 기능 계획의 `**끝:**` 줄은 적지 않았다(02~07 남음).
- **채널의 500.** 티켓 "채널은 그 거부를 … 500으로 낸다"는 새 코드가 필요 없다. `http/errors.py`의 `failure_for`가 기반 `PluginError`를 운영자 면 500(문구 그대로)·최종 사용자 면 500(고정 문구)로 이미 옮긴다(코드를 읽어 확인했다, 새 시험은 두지 않았다).

## 검증 결과

- `uv run ruff check .` 통과, `uv run ruff format --check .` 통과(2062개), `uv run pyright` 0 errors, `uv run lint-imports` 6 kept, `uv run python tools/check_instructions.py` 출력 없음(통과).
- `pnpm -C web verify` 종료 코드 0.
- `tests/sdk/test_manifest.py` 173개, `tests/core/test_run.py` 전체 통과.
- **변이 열 개**(`C:\Users\User\AppData\Local\Temp\claude\9060abe0b92613e9\e25e06df-0ad7-415f-a576-3eac0b85302c\scratchpad\limits_mutations.toml`, 커밋하지 않는 임시 표, 표지 `expect_output` 없이 빨강인지만 봤다). 열 개 모두 기대대로 빨강이었다. 겨눈 곳: 끝 판정의 경계, 10 초과 거부의 경계, 루프에 끝을 넘기지 않기, 거부의 `rule`, 연결에 없는 이름에도 끝 판정, 재생 호출을 세지 않는 올림 위치, 결정을 꺼내기 전의 끝 판정, 두 칸의 하한·엄격함·종류 거부.
- **카나리아.** `.claude/rules/core.md`를 고쳐 `tools/sibling_overlap.py`가 카나리아 알림을 냈다. 새 명세 `.scratch/base-agent/probes/canary/core_rule_tool_call_limit.toml`(미추적)을 지어 `tools/canary.py`로 돌렸다. 통과 4(claude 2.1.322, 실험군 셋이 두 문구를 글자 그대로 옮겼고 대조군은 "없음", "없음" 섞임 0). 명세의 `# 최신 결과:` 줄에 적었다. 기존 규칙 카나리아 명세 일곱(core 다섯, sdk 둘)은 이 브랜치에서 다시 돌리지 않았고 그 명세들의 `# 최신 결과:`는 그대로다(sibling_overlap의 알림이 이 일곱을 가리킨 채 남는다).
- **관리 화면 e2e** `pnpm -C web/apps/admin exec playwright test`: 9개 중 8개 통과, `decision.e2e.ts`의 첫 시험(승인 뒤 재개 스트림이 끝남)이 두 번 모두 5초 기대 시간에 걸려 실패했다. 서버 기록에서 일시정지까지 4~5초가 걸렸고 이 PC에서 `uv run python -c "import mcp"` 한 번이 6초(첫 판 24초)였다. 재개는 MCP 서버를 다시 띄우므로 시작 4~5초 + 픽스처의 2초 대기가 5초 기대 시간을 넘는다. 기대 시간을 30초로 늘린 임시 설정(지웠다)으로 그 파일 세 시험을 돌리자 모두 통과했다. 시간 탓이고 변경 탓이 아니라고 본다. 다만 main에서 같은 시험을 돌려 대조하지는 않았다. CI의 `e2e` 잡이 판정한다.

## 이어받은 세션이 한 것 (21:00 이후)

이어받은 세션이 `/implement`로 열려 EnterWorktree로 이 워크트리에 들어왔다. 사용자의 새 말은 없다. 아래 "아직 안 한 것" 1~3은 이 절이 닫았고 4~5는 이 절 뒤에 이어진다.

- **전체 러너.** `uv run python tools/run_checks.py`(task `bj6vwhf4k`, 13분 26초). `lint-imports`, `pyright`, `pyright-linux`, `web-verify`(1052초) 통과. pytest는 7058 통과 4 실패였고, 실패 넷은 시간에 민감한 프로세스 시험(`tests/channel/cli/test_interrupt.py` 둘, `tests/tools/test_rerun_gates.py`, `tests/tools/test_rerun_runner.py`)이다. 같은 세 파일을 홀로 다시 돌리자 모두 통과했다(종료 코드 0). 러너가 도는 동안 서브에이전트 둘과 다른 일이 같은 PC에서 돌았다. 이 변경이 닿지 않은 파일이라 부하 탓으로 본다. 러너 뒤에 주석·시험·규칙 문서를 고쳤으므로 커밋의 pre-commit이 다시 판정한다.
- **셀프 리뷰.** base `377675eef`, 커밋하지 않은 수정 25개 파일(사진 8장 포함)과 미추적 하나(카나리아 명세)를 두 축으로 봤다. 표준 축은 sonnet·high, 명세 축은 세션 모델. Critical·Major 없음.
  - 표준 축(하드 위반 0, Minor 2, Nit 3): 닫힌 주장 "거부의 주인은 넷"과 "준비 순서의 맨 앞"은 반례 없음.
  - 명세 축(Minor 3, Nit 3): 티켓 체크박스를 하나씩 코드·시험과 대 봐서 빠진 것도 범위 넘침도 없었다.
- **고친 것.**
  1. `max_turns`가 `ctx.llm()` 한 번의 루프 단위인데 "실행 전체 기준/한 실행"이라 쓴 곳 네 군데를 고쳤다(`loop.py` 독스트링, `manifest.py` 주석, `sdk.md`, `core.md`의 "끝은 `ctx.llm()` 한 번의 루프에 걸리고 재개해도 비워지지 않아 재생된 턴도 센다"). 근거는 `run.py`의 `_Context.llm`이 호출마다 `run_loop(..., max_turns=self._limits.turns)`를 새로 부르는 것과 ADR 0052의 같은 말이다. `max_tool_calls`는 실행 전체로 센다(ADR 0052).
  2. `sdk.md`의 "에이전트는 이 끝을 낮출 수만 있다"를 `max_turns`는 낮출 수만(10 초과는 거부), `max_tool_calls`는 올릴 수도 있다(ADR 0052의 커스텀 에이전트 항목)로 나눴다.
  3. `tests/sdk/test_manifest.py`의 거부 시험에 `match=field`를 달았다(CODING_STANDARDS "실패를 기대하는 테스트는 실패의 까닭까지 단언한다").
  4. 끝을 넘은 호출의 `args` 마스킹 시험을 더했다(`test_끝을_넘은_호출의_기록은_마스킹을_지난_인자를_싣는다`). `run.py`의 끝 넘음 거부가 `masked` 대신 `args`를 넘기게 변이하자 빨강이 되고(`{'a': 2} != {'a': '***'}`) 되돌리자 초록이다.
  5. 낮춘 끝 재개 시험에 `rule is None` 단언을 더했다.
  6. 카나리아 명세 머리 주석이 문구의 자리를 잘못 적은 것을 "거부는 실행을 끝내지 않는다 항목과 실패 정책 항목"으로 고쳤다.
- **남긴 것.** (a) 채널 500과 관리 화면 목록·상세에 에이전트가 그대로 보이는 것의 새 시험은 두지 않았다. `http/errors.py`의 `failure_for`가 기반 `PluginError`를 이미 500으로 옮기고 매니페스트 읽기는 이 변경으로 깨지지 않으며, 이 티켓이 채널 코드를 건드리지 않는다. 코드를 읽어 확인한 것이고 시험으로 돌려 본 것은 아니다. (b) `manifest.py`의 "에이전트가 아니면 갖지 않는다" 검증의 반복(Duplicated Code)과 `_Context._call`의 길이(Divergent Change 징후)는 기존 모양이고 판단 항목이라 후속으로 둔다. (c) `_resolve_limits` 독스트링의 어색한 띄어쓰기와 `_prepare` 독스트링의 "같은 순서" 표현은 Nit이라 손대지 않았다. (d) 사진 정답이 "두 줄뿐" 바뀌었는지는 명세 축이 못 봤다(PIL·Docker 없음). 앞 세션이 차이 사진으로 본 것을 이 일지의 "한 것"에 적었다.
- **카나리아.** 이 브랜치가 `.claude/rules/sdk.md`를 고쳐 `tools/sibling_overlap.py`가 sdk 규칙의 카나리아 알림을 냈다. 기존 명세 둘(`sdk_rule_failure_cause.toml`, `sdk_rule_shortcut_patterns.toml`)은 이 변경이 더한 문장을 보지 않아, 새 명세 `.scratch/base-agent/probes/canary/sdk_rule_two_limits.toml`을 지어 `tools/canary.py`로 돌렸다. 통과 4(claude 2.1.322, 실험군 셋이 `minimum: 1`과 `max_tool_calls`는 올릴 수도 있다를 글자 그대로 옮겼고 대조군은 "없음", 섞임 0). 기존 명세 둘은 다시 돌리지 않았으므로 알림은 그 둘을 가리킨 채 남을 수 있다.
- **근거의 종류.** 러너 결과와 시험 출력은 이 세션이 돌려 본 것이다. 명세 축의 "변이를 추론으로 했다"는 서브에이전트가 코드를 고치지 않고 읽어 판단한 것이고 측정이 아니다. 앞 세션이 돌린 열 변이는 별개로 실제 빨강을 본 것이다. e2e 실패 원인은 앞 세션 일지 그대로 미룬 것이다.

## 아직 안 한 것 (인계 시점의 목록. 1~3은 위 절이 닫았다)

1. **전체 러너.** `uv run python tools/run_checks.py`를 백그라운드(task `b9d7dvr3j`)로 돌리던 중 인계해서 멈춘다. 멈추기 전까지 `lint-imports`, `check-ticket`, `zizmor`, `check-instructions`, `check-type-escapes`, `pyright-linux`, `pyright`는 통과였고 pytest 프로세스들과 web 검증의 결과는 못 봤다. 셀프 리뷰를 반영한 뒤 커밋이 부르는 pre-commit이 손으로 치는 다섯(pytest, pyright, 린트, 경계 등)을 갈음하므로, 판단하기 전에 `uv run python tools/run_checks.py`를 한 번 더 돌려 pytest와 web 검증의 전체 결과를 보는 것이 좋다(3분을 넘으니 백그라운드로). `-m llm` 계열은 이 변경이 LLM 호출 경로를 건드리지 않아 돌리지 않았다(어림이 아니라 diff에 모델 호출 코드가 없다는 것을 읽은 것).
2. **티켓의 마지막 체크박스** "검증 명령이 모두 초록이다"는 위 러너를 마친 뒤 새 세션이 채운다. 관리 화면 e2e의 결정 시험 하나가 이 PC에서 5초 기대 시간에 걸려 실패한다는 것(위 검증 결과의 e2e 줄)을 PR 본문에 적는다.
3. **셀프 리뷰(`/code-review`)**: base는 `git merge-base main HEAD`(= `377675eef`). 범위는 커밋하지 않은 수정 파일과 미추적 `.scratch/base-agent/probes/canary/`. Critical·Major를 고친다. 명세는 `.scratch/base-agent/spec.md`와 이 티켓이다. 두 축 브리프에 이 일지의 "한 것"을 사실 주장 후보로 넘긴다. 특히 닫힌 주장 "거부의 주인은 넷이다", "준비 순서의 맨 앞", core.md의 새 문장 다섯 곳이다.
4. **커밋 → 푸시 → PR → 봇 회차 → 병합.** 병합은 이 워크트리 사본의 `merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`를 친다. 커밋에 `.scratch/plan.md` 변경과 카나리아 명세가 든다.
5. **병합된 PR의 뒷일.** 나란히 도는 티켓 02(`02-fake-doc-search-server-fixture`, 다른 세션)는 이 변경과 파일이 겹치지 않는다(`tools/sibling_overlap.py`가 겹침 없음, 02의 워크트리는 `377675eef` 그대로).

## 인계

경계 `셀프 리뷰 직전`. 컨텍스트가 인계 문턱(20만 토큰)을 넘어 `hook_handoff`의 계기를 받았다(274,148 토큰). 제목을 `<브랜치> (인계함)`으로 바꿨고, 백그라운드 전체 러너(task `b9d7dvr3j`)를 멈췄고, 워크트리 잠금을 풀었다.

open-session을 부른다 2026-11-11T11:53:36Z

## 알아 둘 것

- 변이 표와 카나리아 출력은 스크래치패드에 있고 저장소에 없다(변이 표는 커밋하지 않는다고 정했다). 명세의 카나리아 TOML만 커밋 대상이다.
- 이 세션에서 훅이 "화면 코드를 처음 고쳤다"며 `sync-design-system 확인`을 하라고 알렸다. 이 세션이 고친 화면 코드는 테스트·스토리의 매니페스트 데이터 두 칸과 사진 정답이라 디자인 변경이 아니라고 보고 넘겼다(판단이고 그 스킬은 부르지 않았다). 같은 알림이 새 세션에 다시 오면 같은 이유로 넘겨도 된다.
- 근거의 종류: 검증 결과의 명령 줄은 이 세션이 돌려 그 출력에서 본 것이다. 채널 500은 코드를 읽은 것이다. e2e 실패의 원인(재개 때 MCP 서버를 다시 띄우는 시간)은 서버 기록과 기대 시간을 늘린 임시 설정으로 통과한 것에서 미루어 본 것이고, main에서 같은 시험을 돌려 대조하지 않았다.
