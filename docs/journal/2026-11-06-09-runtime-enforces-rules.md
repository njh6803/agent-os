# 2026-11-06 (09) 런타임이 규칙 파일을 도구 호출마다 집행한다 (approval-rules 티켓 04)

세션 제목: `feature/04-runtime-enforces-rules-per-tool-call`. 브랜치도 같다. 워크트리는 `.claude/worktrees/04-runtime-enforces-rules-per-tool-call`.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/approval-rules/issues/04-runtime-enforces-rules-per-tool-call.md`
> 다음 작업: 런타임이 규칙 파일을 도구 호출마다 집행한다(막고, 묻고, 그냥 부른다). 다음 단계: 구현. 어디서: 새 세션. 모델: Sonnet 5.5 / high. 이번 요청 범위: 구현·리뷰·커밋까지

> 사용자: 이번 요청 범위: PR 병합까지

## 한 것 (커밋 전, 워크트리에 있다)

- `core/run.py`: 도구 호출 한 자리(`_Context._call`)가 연결에 없는 이름 → 운영자의 deny → 결정이 없을 때 멈춤(저자의 승인 요구·ask·적힌 규칙 없음) → allow의 차례가 됐다. 적용 규칙은 `_rule_of` 한 자리가 `applied_rule`을 불러 내고, 모델에 붙이는 도구 목록 거르기(`llm()`)와 게이트가 같은 값을 쓴다. 옛 `_deny`는 `_refuse`로 바뀌었다(`rule` 인자를 받는다). `_pause`는 `RunPaused(rule=, server=)`를 내고, `_record_tool_call`은 `rule`을 받는다.
- 준비(`_prepare`)가 `plugins.read_rules()`를 한 번 읽는다(꺼진 집합보다 앞). 재개도 준비를 다시 지나므로 다시 읽는다. 규칙 파일의 손상은 실행 식별자 전의 `PluginError`다.
- 결정이 적용된 호출의 `tool_called.rule`은 그 호출을 멈춘 `run_paused.rule`이다. 칸이 없는 옛 기록은 `requires_approval`로 읽는다. 재개 때 deny에 맞는 도구는 결정과 무관하게 `deny`로 거부된다.
- 시험: `tests/core/test_run.py`에 "운영자의 규칙을 도구 호출마다 집행한다" 절(22개)을 더했다. 가짜 플러그인 소스는 `Rules`와 규칙 읽기 횟수와 손상 심기를 들고, `ToolAwareFakeModel`은 `bind_tools`로 받은 도구 이름을 기록한다. 기본 규칙은 공통 표의 allow로 자기 서버 전부와 `DEFAULT_SERVER`를 연다. `==`로 이벤트 전체를 비교하던 기존 단언 셋은 새 두 칸을 기대 값에 적어 고쳤다. HTTP 두 면의 시험(`test_router.py`, `test_end_user.py`)은 깨진 규칙 파일의 500 봉투를 본다. 03이 남긴 `FakeConnection`의 `owners` 인자를 쓰는 시험도 이제 있다(`test_도구마다_서버가_달라도_적용_규칙은_그_도구의_서버로_낸다`).
- 저장소·e2e·`-m llm` 쪽: `plugins/rules.toml`(`[agents.calc] allow = ["everything:*"]`)과 `README.md` 트리 줄, `tests/test_calc_plugin.py`의 저장소 상태 시험, `tests/test_main.py`의 `_copy_repo_plugins`가 규칙 파일을 복사하고 `gatedcalc` 둘이 `fixture:*` 허락 파일을 쓰는 것(`_write_rules`), 위젯 e2e 꾸러미(`web/apps/widget/e2e/plugins.ts`)가 `tools`·`calc`의 허락 파일을 늘 쓰는 것.
- 문서: `.claude/rules/core.md`(승인 게이트, 거부, 재개, 준비 순서)와 `.claude/rules/sdk.md`(런타임이 두 칸을 채우는 때), `core/run.py`의 모듈 독스트링과 `_prepare` 독스트링. `writing-for-agents`를 불러 쓴 뒤 고쳤다. 서버 대조와 검사 둘은 05의 몫이라고 core.md에 분명히 적었다(그 전의 세 틈을 이미 막는다고 읽히는 문장이 없다).
- 옛 표현 잔존: "정책이 바뀌었어도 적용한다"를 살아 있는 문서에서 찾았다. 남은 곳은 ADR 0009·0044의 이력과 일지·명세뿐이고 `core.md`는 저자의 승인 요구로 좁혔다. `LookupError` 접두의 실패 결과라는 문장은 살아 있는 문서에 없었다(`adapters.md`의 `LookupError`는 어댑터가 던지는 예외 이야기다).
- 줄 끝: 패치 스크립트가 쓴 파일 일곱(`run.py`, `test_run.py`, `test_main.py`, `test_router.py`, `test_end_user.py`, `test_calc_plugin.py`, `README.md`)이 작업 트리에서 CRLF가 되어 있었다. 색인은 LF라 diff에는 안 보였고, 변이 도구의 `--check`가 "줄 끝이 다르다"로 짚어서 알았다. `sed -i 's/\r$//'`로 되돌렸다.

## 변이 점검

`.scratch/approval-rules/probes/runtime_mutations.toml`에 변이 일곱을 적어 돌렸다: 7 모두 기대대로(빨강). 멈춘 사이 deny가 된 도구가 결정으로 통과하는 것, 칸 없는 옛 기록의 기본이 `requires_approval`이 아닌 것, 모델 목록이 deny를 거르지 않는 것, 규칙 파일을 꺼진 집합 뒤에 읽는 것, ask와 저자의 승인 요구가 멈추지 않는 것, 연결에 없는 이름의 거부가 `rule`을 싣는 것, 운영자의 거부가 `deny`가 아닌 `rule`을 싣는 것이다. 처음 판에는 표지(`expect_output`)를 달지 않았다. 빨강의 출력이 시험 이름과 값 비교뿐이라 시험 파일에 글자 그대로 있는 문구가 되기 때문이라고 봤다. 커밋의 pre-commit(`mutate.py --staged`)이 표지 없는 빨강 변이를 막았다. 그래서 변이를 손으로 넣어 본 실패 출력에서 pytest가 찍는 비교 줄(`At index 0 diff: True != False`, `['add', 'send', 'ask_me'] != ['add', 'ask_me']`, `Actual message: '…'`, `output='unreachable'` 따위)을 표지로 달았고, 변이마다 `-k`로 겨눈 시험 하나나 둘로 좁혔다. 좁힌 판을 이 세션이 돌려 일곱이 표지까지 기대대로(빨강)였다. 변이 5는 손으로 넣어 두 시험의 출력을 봤다.

## 카나리아 (이 세션이 `tools/canary.py`로 돌렸다)

`.claude/rules/core.md`·`sdk.md`를 고쳤으므로 `tools/sibling_overlap.py`가 알린 카나리아 명세 일곱을 새 `claude -p` 세션으로 돌렸다(claude 2.1.318, HEAD `d0f5a195` 위의 커밋하지 않은 작업 트리). 여섯은 통과 4 · 실패 0이다(`core_rule_read_rules_port`, `core_rule_pre_owner_damage`, `core_rule_read_cap_thread`, `core_rule_runtime_only_events`, `sdk_rule_failure_cause`, `sdk_rule_shortcut_patterns`). `core_rule_shortcuts`는 첫 판이 통과 3 · 실패 1이었다. 실패 한 회차는 실험군이고 (1)의 굵은 문장을 글자 그대로 옮겨 규칙이 실린 채 (2)를 옛 대화 갈래의 `_walk`로 답했다(2026-10-24의 실패와 같은 모양이다). 이 브랜치는 그 항목의 문장을 고치지 않았다. 문구를 바꾸지 않고 다시 돌리자 통과 4였다. 일곱 명세의 `# 최신 결과:` 줄을 고쳤다.

## 검증 (이 세션이 쳤다)

- `uv run pytest tests -q -n 4 --ignore=tests/channel`(채널 시험은 앞서 따로 돌렸다): 6239 passed, 429초.
- `uv run ruff check .`와 `uv run ruff format --check .`: 둘 다 종료 코드 0(이 세션이 쳤다).
- `uv run python tools/run_checks.py`(이전 세션이 백그라운드로 띄워 둔 것을 이 세션이 로그로 읽었다): check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest(421.8초), web-verify(578.1초) 모두 Passed.
- `uv run --env-file ../../../.env pytest -m llm -q`(같은 백그라운드의 로그): 7 passed, 241초. LLM 토큰 합계 57,505(입력 56,584, 출력 921), 트레이스 10개, 모델 호출 22건.
- `pnpm -C web/apps/widget exec playwright test`(이 세션이 쳤다): 15 passed, 58.3초.
- `uv run --env-file ../../../.env pytest -m llm_widget -q`(이 세션이 쳤다): 1 passed, 45.78초. LLM 토큰 합계 6,937(입력 6,865, 출력 72), 트레이스 1개, 모델 호출 2건.
- 셀프 리뷰 반영 뒤에는 `ruff`·`pyright`(바꾼 두 파일)·`tests/core/test_run.py`를 다시 쳤다(아래 절). 전체 `run_checks`는 반영 전 작업 트리로 돌았고 반영 뒤 판은 커밋의 pre-commit이 갈음한다.
- 관리 화면 e2e와 사진 비교는 치지 않았다(티켓: 꾸러미의 행동이 바뀌지 않아 CI의 `e2e` 잡에 맡긴다). 기본 규칙을 넣기 전의 빨강 수는 재지 않았다(PR 본문에 그렇게 적는다).

## 셀프 리뷰 (이 세션이 `/code-review`로 돌렸다)

범위: base `d0f5a195`(= origin/main), 파일 18개, 커밋 0개, 미추적 3개(`runtime_mutations.toml`, `plugins/rules.toml`, 이 일지). 표준 축은 sonnet·high, 명세 축은 세션 모델을 상속했다. 둘 다 Critical·Major 0이다.

고친 것(반영 뒤 `uv run ruff check`·`ruff format --check` 통과, pyright 두 파일 0 errors, `tests/core/test_run.py` 405 passed, `tools/mutate.py --check`로 변이 일곱의 원문이 한 번씩 있음):
- `core/run.py`의 `_spec_of`를 `_connected_spec`으로 바꿨다. `CONTEXT.md` 동사 표가 `<명사>_of`를 "포트에 닿지 않는다"로 정의하는데 이 함수는 `self._tools.tools()`를 부른다.
- `_call`의 지역 변수 `rule`이 "적용 규칙"과 "기록에 남길 까닭"의 두 뜻이던 것을 `rule`과 `recorded`로 나눴다. 변이 표의 한 줄(`recorded = verdict.paused.rule or "requires_approval"`)을 따라 고쳤다.
- `tests/core/test_run.py`의 독스트링에서 옛 이름 `_deny`를 `_refuse`로, "첫 빨강:" 작성 과정의 서술을 지웠다.
- `_prepare` 독스트링의 끊긴 줄바꿈을 이었다.
- `README.md`의 "없으면 모든 호출이 묻는다"를 "없으면 연결에 있는 도구의 모든 호출이 묻는다"로 좁혔다(연결에 없는 이름은 묻지 않고 거부된다).

남긴 것과 이유:
- `run.py` 모듈 독스트링과 `core.md`의 "아직 없다(approval-rules 05)", 시험 `_open_rules`와 위젯 e2e `plugins.ts`의 현재형 설명: 05가 병합될 때 같이 고칠 문장이다. 05 티켓이 "04가 적은 틈의 문장" 잔존 grep을 이미 요구한다(표준 축이 05 티켓 39행으로 확인했다).
- 시험 헬퍼 `_rule(text)`가 어댑터의 파싱을 복제한 것: core 시험은 어댑터를 import하지 않는다(원칙 IV). 억제한다.
- `_refuse`가 기록과 `release`와 결과 반환을 함께 하는 것, `name, masked`가 함께 다니는 것: 옛 `_deny`의 모양 그대로이고 호출부 둘이 모두 반환값을 쓴다.
- `_ruled(...)`가 기본값과 같은 `requires_approval=[]`를 명시하는 것: 시험을 읽을 때 규칙 파일과 저자의 승인 요구가 둘 다 없음을 보이려는 것이다.
- `_refuse`가 `release()`도 부르는 것은 범위 넘침으로 보였으나 옛 승인자 거부 경로와 같은 흐름 정리다.
- 이 일지의 "22개"는 실제 23개다(파라미터 포함 24 케이스). 기록이라 위 '한 것' 줄은 고치지 않고 여기에 적는다.

근거의 종류(셀프 리뷰 절): 두 축의 지적과 "코드를 읽었다"는 서브에이전트 보고를 옮긴 것이다. 그 가운데 이 세션이 직접 본 것은 05 티켓 39행의 문구(Grep), `CONTEXT.md` 동사 표의 `<명사>_of` 정의(Read), `_call`과 `_spec_of`의 본문(Read), 변이 표의 `--check` 결과, ruff·pyright·`test_run.py`의 출력이다. "23개"와 "파라미터 포함 24 케이스"는 표준 축 보고의 수이고 이 세션이 세지 않았다.

근거의 종류: 위 시험·린트·변이·카나리아의 통과와 수치는 이 세션이 친 명령의 출력을 본 것이다. 옛 표현 잔존은 Grep으로 본 것이다. 줄 끝 CRLF는 `git ls-files --eol`의 출력과 변이 도구의 `--check` 메시지를 본 것이다. 변이 표의 "표지를 달지 않은 까닭"과 "빨강이 겨눈 시험에서 났다"는 변이 도구가 찍은 시험 이름을 읽은 것이다. 기본 규칙을 넣기 전의 빨강 수는 이 세션이 재지 않았다(티켓은 어림이라 했고 기준이 크게 다르면 PR 본문에 적으라 했다. 재지 않았다고 적는다).

## 인계 시점의 상태

- 컨텍스트가 인계 문턱을 넘어 `셀프 리뷰 직전`에서 넘겼다. `/code-review`는 돌지 않았고 커밋하지 않았다. 이 세션의 제목은 `feature/04-runtime-enforces-rules-per-tool-call`이었다.
- 끝난 것: 구현(`core/run.py`), core·채널 시험, 저장소·e2e의 규칙 파일, 문서(`core.md`·`sdk.md`·`run.py` 독스트링), 옛 표현 grep, 변이 점검(일곱), 카나리아 일곱과 `# 최신 결과:` 줄, `tools/sibling_overlap.py`(번호 겹침 없음, 일지는 이 파일이 09).
- 아직 안 한 것: 셀프 리뷰와 그 반영, `run_checks`·`-m llm`의 결과 확인, 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`), `-m llm_widget`, 티켓 04의 체크박스와 `Status: done`, 이 일지의 검증 절, 커밋, PR, 병합.
- 이 세션이 띄워 둔 백그라운드 둘은 멈추지 않았다(멈추면 검증을 버린다). 출력은 둘 다 스크래치패드 아래 파일이다: `C:\Users\User\AppData\Local\Temp\claude\C--project-agent\48d86ae0-4ddb-4594-8341-5991e340ed5f\scratchpad\checks.log`(`uv run python tools/run_checks.py`)와 `...\scratchpad\llm.log`(`uv run --env-file ../../../.env pytest -m llm -q`). 새 세션은 두 파일의 끝을 먼저 읽는다. 끝났으면 결과를 이 일지의 검증 절에 옮기고, 아직 돌면 기다린다. 실패가 있으면 그 시험을 고친다. `run_checks`가 web 검증을 도는 동안 작업 트리에 `web/judge-*/` 임시 폴더가 보일 수 있다(끝나면 사라진다. 이 세션은 커밋에 넣지 않았다).
- 새 세션이 알아야 할 것: 작업 트리의 파일을 Python으로 다시 쓰는 스크립트는 `newline="\n"`을 주거나 쓴 뒤 `git ls-files --eol`로 줄 끝을 본다(위 "줄 끝"). 변이 표(`runtime_mutations.toml`)는 `run.py`를 바이트로 되돌리므로 변이가 도는 동안 `run.py`와 `test_run.py`를 고치지 않는다.
- 묻지 않고 정한 것(이 줄 아래 `open-session` 줄이 마지막에 온다): `DEFAULT_SERVER`는 세 시험 파일에 따로 둔 채다(공용 상수로 올리지 않았다. 세 시험 파일이 서로를 import하지 않고 03의 선택을 그대로 둔다).

open-session을 부른다 2026-11-06T06:44Z

## 인계 시점의 상태 (커밋 뒤, 둘째 세션)

세션 제목은 `feature/04-runtime-enforces-rules-per-tool-call`이었다. 앞 세션의 인계를 받아 이어 쓴 세션이다.

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/approval-rules/issues/04-runtime-enforces-rules-per-tool-call.md` … 다음 단계: 구현 … 이어받을 상태: 인계: 셀프 리뷰 직전. … 이번 요청 범위: PR과 병합까지

- 한 것: 위 '셀프 리뷰'와 '검증' 절의 것이다. 백그라운드 `run_checks`와 `-m llm`의 결과를 읽고, 위젯 e2e와 `-m llm_widget`을 쳤고, 셀프 리뷰 두 축(Critical·Major 0)을 반영했고, 티켓을 `done`으로 바꿨다.
- 커밋: `e9f271c4`(브랜치 `feature/04-runtime-enforces-rules-per-tool-call`). 첫 커밋 시도는 pre-commit의 `mutate.py --staged`가 막았다(빨강을 기대한 변이 일곱에 `expect_output`이 없었다). 변이를 손으로 넣어 본 출력에서 표지를 골라 달고 변이마다 `-k`로 좁힌 뒤 다시 커밋했고, 둘째 시도는 pre-commit 전체(ruff 둘, `run_checks`의 열 검사, 마크다운 표·줄 구분 문자·변이 표·카나리아 모양)를 통과했다. 이 세션이 `git commit`의 종료 코드 0을 봤다.
- 푸시하지 않았다. PR도 없다. 아직 안 한 것: 푸시, PR 열기, 봇 회차와 병합. PR 본문에는 "기본 규칙을 넣기 전의 빨강 수는 재지 않았다"를 적는다(티켓이 어림이라 했고 기준이 크게 다르면 적으라 했다). 관리 화면 e2e와 사진 비교는 CI의 잡에 맡긴다(티켓).
- 병합 전에 05가 곧 이어진다는 티켓의 문장(04와 05는 연달아 병합한다)을 PR 본문과 병합 뒤 지시문에 옮긴다.
- 새 세션이 알아야 할 것: 이 일지의 '셀프 리뷰'에서 남긴 것(05가 병합될 때 같이 고칠 "아직 없다(approval-rules 05)" 문장들)은 05 티켓의 잔존 grep이 받는다(05 티켓 39행을 Grep으로 봤다).

open-session을 부른다 2026-11-06T07:24Z

## PR 직전 리뷰 (셋째 세션)

세션 제목은 `feature/04-runtime-enforces-rules-per-tool-call`이다. 둘째 세션의 인계로 이어 받았고 푸시와 PR 열기, 봇 회차, 병합이 이 세션의 몫이다.

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/approval-rules/issues/04-runtime-enforces-rules-per-tool-call.md` … 이어받을 상태: 인계: 커밋 뒤. … 이번 요청 범위: PR과 병합까지

- CodeRabbit CLI는 돌지 못했다. `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`를 보였고(이 세션이 직접 쳤다), `coderabbit-review` 서브에이전트도 같은 값을 보고 리뷰를 돌리지 않고 끝났다. 그래서 대체 둘을 돌렸다. origin/main은 이 브랜치의 merge-base(`d0f5a195`)와 같아 합칠 것이 없었다(`git fetch` 뒤 `git rev-parse`로 봤다).
- `/security-review`: 취약점을 찾는 서브태스크가 지적 없음을 보고했다. 후보가 없어 거짓 양성을 거르는 서브태스크는 돌리지 않았다. 참고로 적힌 것 하나(확신도 7 미만)는, 규칙 줄의 도구 칸 패턴이 `[^:\s]+`라서 이름에 `:`나 공백이 든 MCP 도구는 정확한 이름의 deny 줄을 쓸 수 없다는 것이다. 우회 경로가 아니고 하드닝이라 이 PR에서 고치지 않는다. 와일드카드 deny는 맞는다고 보고했다. 이 문장은 서브에이전트의 보고를 옮긴 것이고 이 세션이 그 패턴을 읽지 않았다.
- `bug-perf-review`: 유효 0 · 오탐 3 · 보류 0. 알려진 틈 셋(05의 몫)은 새 지적이 아니라고 분류했다. 오탐 셋은 `tools()`를 호출마다 다시 부르는 비용, 규칙 파일 읽기의 `PermissionError` 동기 재시도(`read_disabled`와 같은 기존 설계), 재생 구간이 규칙이 지금 deny여도 기록을 돌려주는 것(의도이고 문서화)이다. 이 보고는 서브에이전트가 `tests/core/test_run.py`의 24건과 `tests/channel`·`test_main.py`·`test_calc_plugin.py`·`test_server.py`를 돌려 통과를 봤다고 적었다(이 세션이 다시 치지 않았다). `tools/canary.py --shape`는 인자를 잘못 주어 보지 못했다고 적었다. 카나리아 명세 모양은 커밋의 pre-commit이 이미 통과했다.
- 두 보고 모두 지적이 없어 고친 것도, 남긴 것도 없다.
