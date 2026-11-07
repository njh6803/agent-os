# 2026-11-08 (0112) 실행 전·연결 직후·재개의 검사 셋 (approval-rules 티켓 05)

세션 제목: `feature/05-checks-before-run-after-connect-and-on-resume`. 브랜치도 같다. 워크트리는 `.claude/worktrees/05-checks-before-run-after-connect-and-on-resume`.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/approval-rules/issues/05-checks-before-run-after-connect-and-on-resume.md`
> 다음 작업: 04가 남긴 틈 셋을 실행 전·연결 직후·재개의 검사로 닫는다. 모델: Sonnet 5.5 / high. 이번 요청 범위: PR과 병합까지

## 한 것 (커밋 전, 워크트리에 있다)

- `core/ports.py`: `Rule`에 `position: int | None = field(default=None, compare=False)`를 더했다(그 줄이 자기 배열에서 몇째인지, 비교에서는 빠진다). 어긋난 줄을 글자가 아니라 자리로 알리려는 계약 보강이다.
- `adapters/filesystem.py`: `_rule_of(line, position)`이 위치를 `Rule`에 싣는다. 한 배열 안의 같은 줄 둘은 하나로 합쳐지고 자리는 앞선 줄의 것이다(그래서 중복 줄은 앞선 줄의 자리만 보고된다. 한계).
- `core/rules.py`: 순수 질의 `unresolved_rule_lines(rules, *, agent, servers, specs)`(자리 목록 `agents.<에이전트>.<deny|ask|allow>.<번호>`), `_is_present`, `_place`, `_position_of`.
- `core/run.py`: `_prepare`가 규칙 파일을 읽은 뒤 `_reject_masked_asks`(마스킹 인자가 있는 도구가 `ask`·`default`에 걸리면 `PluginError`), `_attend`가 `_reject_unknown_declarations` 바로 뒤에 `_reject_unknown_rule_lines`(어긋난 줄이 있으면 `LookupError` → 원인 `tool_connection`), `_require_paused_call`이 서버도 대 본다(멈춤 기록의 `server`와 지금 연결의 그 이름 도구의 서버. 연결에 그 이름이 없으면 대지 않고 04의 "연결에 없는 이름의 거부"가 결정을 소비한다. 칸 없는 옛 기록은 이름과 인자만). `_labelled`의 서버 매개변수는 `str | None`이다(`RunPaused.server`가 `str | None`이라 pyright가 짚었다).
- 시험: `tests/adapters/test_filesystem.py`(위치 2), `tests/core/test_rules.py`(에이전트 표 검사의 순수 질의), `tests/core/test_run.py` 끝의 "실행 전·연결 직후·재개의 검사 셋(approval-rules 05)" 절과 준비 순서 시험 둘. 빨강을 먼저 봤다(25개 실패).
- 문서: `.claude/rules/core.md`(승인 게이트 항목, 재개 항목의 서버 대조, 실패 정책의 마스킹과 묻기·에이전트 표 검사, 준비 순서), `.claude/rules/sdk.md`(승인 게이트 필드 항목), `core/run.py` 모듈 독스트링과 `_prepare` 독스트링. `writing-for-agents`를 불러 쓴 뒤 고쳤다.
- 옛 표현 잔존: Grep으로 `approval-rules 05`·"이름과 인자만"·"서버 대조"·"재개가 서버"를 살아 있는 문서에서 찾았다. 남은 것은 시험의 절 머리 주석 둘(05를 가리키는 현재형 인용), `_require_paused_call` 독스트링의 칸 없는 옛 기록은 이름과 인자만 본다는 서술(맞는 서술), ADR 0044·0009의 이력, 명세·일지·티켓(기록)이다. 위젯 e2e `plugins.ts`와 `tests/test_main.py`의 `_write_rules`는 읽어 본 결과 새 검사를 지난다(`tools`의 `fixture:*`는 그 에이전트의 `mcp`에 fixture가 있고, `calc`의 `everything:*`와 `gatedcalc`도 같은 꼴). `plugins/rules.toml`도 같다.

## 변이 점검

`.scratch/approval-rules/probes/checks_mutations.toml`에 변이 열하나를 적어 돌렸다: 11 모두 기대대로(빨강). 표지(`expect_output`)는 변이를 넣어 모은 실패 출력(스크래치의 `show_mutation_output.py` → `mut_out.txt`)에서 골랐고(`Failed: DID NOT RAISE PluginError`, `At index 1 diff: …`, `Right contains one more item: 'agents.calc.…'` 따위), `--check`가 원문 11개를 한 번씩 확인했다. 변이를 돌린 뒤 `run.py`·`rules.py`가 백업과 바이트로 같음을 `cmp`로 봤다.

## 검증 (이 세션이 쳤다, 코드가 더는 바뀌지 않은 상태)

- `uv run python tools/run_checks.py`: check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest(434.1초), web-verify(552.3초) 모두 Passed. 이 실행은 pyright가 짚은 `_labelled` 수정 뒤의 작업 트리다.
- `uv run ruff format src tests`(175 files left unchanged), `uv run ruff check .`: 종료 코드 0.
- `uv run lint-imports`: 6 kept, 0 broken.
- **돌고 있는 것**: `uv run --env-file ../../../.env pytest -m llm -q`를 백그라운드로 띄웠다. 출력은 `C:\Users\User\AppData\Local\Temp\claude\C--project-agent\225ab650-8efc-48df-9010-19a0e9c19eda\scratchpad\llm.log`(마지막 줄이 `exit=<코드>`)다. 멈추지 않았다(멈추면 검증을 버린다). 새 세션은 이 파일의 끝을 먼저 읽는다. 끝났으면 결과를 이 일지에 옮기고 아직 돌면 기다린다.
- **아직 안 쳤다**: 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`), `-m llm_widget`(`uv run --env-file ../../../.env pytest -m llm_widget -q`). 관리 화면 e2e와 사진 비교는 치지 않는다(행동이 바뀌지 않는다, CI에 맡긴다).

## 셀프 리뷰 (두 번째 세션, base 778db404, 파일 10개·커밋 0·미추적 2)

표준 축(sonnet·high)과 명세 축(세션 모델) 서브에이전트를 병렬로 돌렸다.

- 명세 축: 요구 누락·범위 넘침·구현 오류 모두 없음. `Rule.position`은 티켓의 `<자리>`에 필요한 계약 보강이라 범위 넘침이 아니다(적은 곳이 `Rule` 독스트링뿐이라 PR 본문에 적는다). 체크박스는 시험에 하나씩 대응된다. `unresolved_rule_lines`를 경계 입력으로 불러 봤다(맨 `ghost`, mcp에 없는 `zz:get_*`·`zz:*`, 없는 `srv:nope`는 어긋남. 맨 `*`, `srv:*`, `add`는 통과).
- 표준 축: Critical·Major 0, Minor 4, Nit 3. 고친 것: (1) `test_deny_의_오타…`에 오류 문구·원인 `tool_connection`·`model.calls == 0` 단언을 더하고 이름을 "도구를 부르기 전에 드러난다"로 바꿨다(변이 표의 `-k`도 같이). (2) `test_마스킹된_인자를…`의 이름에서 "서버 순서"를 "선언 순서"로 고쳤다(서버는 `srv` 하나뿐). (3) `test_어긋난_줄이_여럿이면…`에 어긋난 `ask` 줄(`fake:nope`)을 끼워 deny→ask→allow 순서를 이 시험이 직접 재게 했다. (4) `unresolved_rule_lines` 독스트링의 근거를 ADR 0044 "모양"에서 이력 "그 에이전트의 표는 연결 뒤 대 본다"로 바로잡았다.
- 남긴 것: `_place`가 TOML 키 경로를 core에 두는 것은 명세가 문구를 정한 판단이라 둔다. `Rule.position`의 `None` 갈래(어댑터 밖에서 만든 값용)와 `_place`의 `kind: str`은 경미한 Nit이다. 번호가 모두 없고 줄이 여럿인 입력은 프로덕션에 없다(어댑터만 `Rule`을 만든다).
- 다시 돌린 명령: `uv run ruff check . && uv run ruff format --check .` 통과, `mutate.py --check` 원문 11개 한 번씩, `pytest tests/core/test_run.py tests/core/test_rules.py tests/adapters/test_filesystem.py -n 4` 628개 통과.

## 검증 결과 (두 번째 세션)

- `pytest -m llm`: 7개 통과(341초, 첫 세션이 띄운 것의 끝).
- `pytest -m llm_widget`: 1개 통과(148초).
- 위젯 e2e: 첫 판은 `-m llm_widget`과 동시에 돌려 15개가 모두 빨갰다(같은 `.next` 빌드 폴더를 둘이 쓴 것으로 어림한다. 로그에 `Could not find a production build in the '.next' directory`). 단독으로 다시 돌리자 15개가 통과했다(`pnpm -C web/apps/widget exec playwright test`, 종료 코드 0, 53.1초). 빨강 원인이 동시 실행이었다는 것은 어림이다. 같은 시험 하나를 단독으로 돌리면 통과하고 전체를 단독으로 돌려도 통과한 것까지만 봤다.
- 카나리아 일곱(`sibling_overlap.py`가 알린 `core.md` 다섯과 `sdk.md` 둘의 명세: `.scratch/approval-rules/probes/canary/core_rule_read_rules_port.toml`과 `.scratch/end-user-continuation/probes/canary/{core_rule_pre_owner_damage, core_rule_read_cap_thread, core_rule_runtime_only_events, core_rule_shortcuts, sdk_rule_failure_cause, sdk_rule_shortcut_patterns}.toml`)을 새 `claude -p` 세션으로 `tools/canary.py`에 돌렸다(claude 2.1.318, 커밋 778db404 위의 커밋하지 않은 작업 트리). 일곱 모두 통과 4, 실패 0이고, `core_rule_shortcuts`만 실험군 셋이 "없음" 섞임으로 표시됐다. 찍힌 답을 읽으니 굵은 문장을 글자 그대로 옮기고 (2)를 `_follow`로 답해 규칙이 실렸다. 각 명세의 `# 최신 결과:` 줄을 고치고 옛 줄을 `# 앞선 결과:`로 내렸다(`canary.py --shape` 일곱 모두 통과).
- 티켓 05는 체크박스 열여섯을 모두 체크하고 `Status: done`으로 바꿨다. 기능 계획 `.scratch/approval-rules/plan.md`의 `**끝:**` 줄은 적지 않았다. 06 티켓이 `origin/main`에서 `ready-for-agent`라 05가 마지막 열린 티켓이 아니다(`git ls-tree`와 06 티켓의 `Status` 줄을 읽었다). `plan_table.py`는 출력 없이 끝났고 `.scratch/plan.md`는 바뀌지 않았다.

## 첫 커밋 시도가 막힌 것 (pre-commit의 변이 표 검사)

첫 커밋의 pre-commit에서 `parallel-checks`(pytest 443.1초, web-verify 542.3초 포함)는 모두 `Passed`였고 변이 표 검사(`mutation tables`)만 `Failed`였다. 다른 기능의 변이 표 셋이 겨누던 원문을 이 변경이 바꾼 탓이다. `rules_file_read_mutations.toml`(`_rule_of`의 반환 줄에 `position=position`이 붙음), `runtime_mutations.toml`과 `prepare_mutations.toml`(`_prepare`의 규칙 읽기·꺼진 집합 읽기가 두 줄로 갈라짐). 원문을 새 줄로 옮기고 세 표를 표마다 돌렸다(`tools/mutate.py`, 종료 코드 모두 0). 그 과정에서 `rules_file_read_mutations.toml`의 변이 다섯(1·7·8·9·10)이 빨강이긴 한데 표지(`expect_output`)가 없다고 어긋났다. `Rule`의 repr에 `position=None`이 생겨 표지의 글자가 바뀐 것이다(어림이 아니라 같은 실행의 출력 줄 `where matches = Rule(server=None, tool='*', position=None).matches`를 읽었다). 표지를 `where True = matches(server=..., tool=...)` 줄로 바꾸고 그 다섯만 다시 돌려 통과했으나, 둘째 커밋 시도에서 `mutate.py --staged`가 그 줄을 막았다. pytest가 단언을 풀어 쓴 줄은 다른 까닭으로 빨개져도 같은 호출과 값이 찍히므로 표지가 될 수 없다는 검사 문구다. 그래서 `tests/core/test_rules.py`의 `test_규칙은_세_꼴과_별표_패턴대로_도구에_맞거나_안_맞는다`에 단언 메시지(`규칙 {rule}, 서버 {server}, 도구 {tool!r}`)를 더하고, 표지를 그 메시지의 글자로 바꿨다. 다섯 변이를 다시 돌려 모두 통과했다(`mutate.py` 종료 코드 0, `--check` 원문 13개 한 번씩). 인용 검사 경고(따옴표 인용 둘)는 따옴표를 떼서 풀었다.

## 두 번째 세션의 기록 (셀프 리뷰 직전에서 커밋 뒤까지)

세션 제목: `feature/05-checks-before-run-after-connect-and-on-resume`(둘째 세션). 인계하며 `… (인계함)`으로 바꾼다.

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/approval-rules/issues/05-checks-before-run-after-connect-and-on-resume.md` … 이어받을 상태: 인계: 셀프 리뷰 직전. … 이번 요청 범위: PR과 병합까지

- 한 일: `tidy-checkouts`로 주 체크아웃을 `origin/main`(778db404)에 맞췄다(워크트리 정리는 지울 것이 없었다). 워크트리에 들어와 셀프 리뷰, 반영, 위젯 e2e·`-m llm_widget`·카나리아 일곱, 티켓 05 `done`, 커밋까지 했다. 커밋은 `3c132b42`이다.
- 커밋이 두 번 막혔다. 둘 다 `mutate.py --staged`(변이 표 검사)였고 위 "첫 커밋 시도가 막힌 것"에 적었다. pytest·pyright·web-verify 등 나머지 검사는 모두 `Passed`였다.
- 이 세션이 번복한 것: 위젯 e2e의 첫 판 15개 빨강을 코드 결함으로 읽지 않고 동시 실행 탓으로 어림해 단독으로 다시 돌렸다(위 "검증 결과").

## 세 번째 세션의 기록 (커밋 뒤에서 PR까지)

세션 제목: `feature/05-checks-before-run-after-connect-and-on-resume`(셋째 세션).

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/approval-rules/issues/05-checks-before-run-after-connect-and-on-resume.md` … 다음 단계: PR 반영·병합 … 이번 요청 범위: PR과 병합까지

- 한 일: 워크트리에 들어가 `sibling_overlap.py`를 쳤다(번호 겹침 없음, 함께 고친 파일 없음, origin/main은 778db404로 그대로. 이 세션이 친 명령의 출력을 읽은 것이다: `uv run python tools/sibling_overlap.py`, `git log HEAD..origin/main`).
- 일지 커밋이 `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다` 하나에 막혔다(pre-commit의 pytest: 6628 통과 1 실패, 1265초). 이 브랜치는 `tools/`와 `tests/tools/`를 건드리지 않았다(`git diff --merge-base origin/main --stat -- tools tests/tools`가 빈 출력). 단독으로 4번 쳐서 4번 빨갰다. 손으로 쟀다. 시험의 자식이 첫 줄을 내기까지 0.125~0.891초(다섯 번, 스크래치 프로브)였고, 시험과 같은 방식의 `LineReader.drain(0.5)`는 회차에 따라 줄 7개를 받거나 0개를 받았다(셋 가운데 하나가 0, 스크래치 프로브 `drain_probe.py`). 원인 어림: 제한 0.5초가 자식 파이썬의 기동 시간을 포함하는데, 이 PC에 다른 세션이 여럿 돌아 기동이 0.5초 안팎이다. 그 뒤 다음 커밋의 pre-commit에서는 같은 시험이 든 pytest 전체가 통과했다(`pytest ... Passed (846.1s)`, 앞의 실패 때는 1265.45초였다). 부하에 따라 흔들린다는 어림과 맞지만 그 시험을 단독으로 다시 쳐서 통과한 것은 보지 못했고, `origin/main`에서도 빨간지는 재지 않았다. 원칙 II에 따라 시험은 고치지 않았다. 대기열 후보다(시험이 첫 줄을 기다리는 시간과 배출의 마감을 가르면 된다는 것은 어림이다).
- `origin/main`에 06(#490)이 병합돼 합쳤다(`git merge origin/main`, 충돌 없음). 06의 실제 모델 시험 `test_멈춘_사이_규칙_파일이_…`을 합친 작업 트리에서 `-m llm -k 멈춘_사이_규칙_파일`로 쳐서 통과했다(1개, 119.56초, 토큰 3,725, 모델 호출 2건). 05가 먼저 병합돼도 06이 초록이어야 한다던 걱정은 반대 순서로(06이 먼저) 풀렸다.
- 05가 기능의 마지막 열린 티켓이 되어(`.scratch/approval-rules/issues/`의 `Status:` 여섯이 모두 done을 Grep으로 봤다) 기능 계획 `.scratch/approval-rules/plan.md`에 `**끝:** 2026-11-08`을 적고 `uv run python tools/plan_table.py`로 `.scratch/plan.md`를 갱신했다(도구는 출력 없이 끝났고 파일 둘이 바뀐 것을 `git status`로 봤다). 이 변경들을 한 커밋으로 싣고 푸시해 PR을 연다.

### PR 직전 리뷰 (셋째 세션)

- CodeRabbit CLI는 돌지 못했다. `coderabbit-review` 서브에이전트가 `coderabbit auth status`를 읽었다: 버전 0.7.5, `Plan: Free`, `Seat: not assigned`. 그래서 `coderabbit review`는 돌리지 않았고 CLI 축은 비었다(서브에이전트의 보고를 옮긴 것이다). 대체 둘을 나란히 돌렸다.
- 보안(`/security-review`의 1단계를 서브에이전트로 돌렸다): 지적 없음. 서브에이전트가 `git diff origin/main...HEAD -- src` 전체와 호출 맥락(`core/run.py`의 `_call`·`_mask`·`_reject_masked_args`·`_reject_unknown_declarations`, `adapters/mcp.py`의 `connect`·`call`, `sdk/manifest.py`의 `secret_args_by_tool`)을 읽은 결과다. 코드를 읽은 판단이고 돌려 본 것은 아니다. 확신이 낮아 보고하지 않은 것 하나: `secret_args`는 도구 이름만으로 걸리고 `_reject_masked_asks`는 매니페스트에 선언한 서버로 규칙을 판정해, 선언한 서버와 실제 도구를 낸 서버가 다르면 실행 전 검사와 실행 중 판정이 어긋날 수 있다. 결과는 마스킹된 값을 보내려다 실패하는 가용성 문제이고 누출이 아니다(서브에이전트의 어림).

- 버그·성능(`bug-perf-review` 서브에이전트): 유효 1건(Minor), 오탐 0. `core/run.py`의 `_reject_masked_asks`가 연결을 보지 않고 매니페스트의 `secret_args`만 돌아, 규칙이 비어 있으면(적힌 규칙 없음은 `default`라 `ask`와 같이 거부된다) 오타 난 도구 이름(`sned`)에도 "마스킹된 인자를 가진 도구는 묻는 규칙에 걸릴 수 없다" 문구가 먼저 난다. 05 전에는 같은 입력이 `run_failed(tool_connection)`의 "secret_args 가 가리키는 도구가 없다"로 끝났다. 서브에이전트가 `FakePlugins(..., secret_args={'sned': ['key']}, rules=Rules())`로 넣어 문구를 봤다는 보고이고, 이 세션은 `_reject_masked_asks`(`run.py` 1638~1663)의 코드를 읽어 그 경로가 있음을 확인했다(돌려 보지는 않았다). 기존 시험 `test_비밀_선언이_실재하지_않는_도구를_가리키면…`이 초록인 것은 `FakePlugins`의 기본 규칙이 전부 allow라서라는 보고도 그 시험이 쓰는 기본값을 읽어 맞다고 본다(어림). 나머지 따라간 경로(`Rule.position`의 `compare=False`, `unresolved_rule_lines`, `_attend`의 원인, `_require_paused_call`)는 문제를 찾지 못했다는 보고다.
  - 판정: 유효, 보류. 오타 난 도구에도 실행 전에 거부되는 것은 같고(실행은 시작되지 않는다) 문구만 다르다. 문구에 도구 이름이 있어 운영자가 오타를 바로 알아본다. 고치려면 `core.md`의 실패 정책 문장과 `_reject_masked_asks` 독스트링을 고치고 빈 규칙 시험을 더해야 하는데, 변이 표(`checks_mutations.toml`의 원문 열하나)와 pre-commit 한 바퀴(15분)를 다시 치르는 값이 오타 한 가지의 문구 차이보다 크다고 판단했다. 방향 둘은 서브에이전트의 제안대로다: 의도라고 문서에 적고 빈 규칙 시험으로 고정하거나, 검사를 연결 뒤로 옮기거나 연결의 도구만 대상으로 줄인다(후자는 "실행 전 PluginError, 트레이스 없음" 계약이 바뀐다).
  - 뒤로 넘긴 일: 위 보류를 다음 지시문의 "이어받을 상태"에 옮긴다.

## 아직 안 한 것

- 봇 회차와 병합(`merge.md`의 "워크트리에서 병합할 때"), 병합 뒤 다음 지시문. 병합 직전에 06 티켓 상태를 다시 보고 05가 마지막 열린 티켓이 되면 기능 계획에 `**끝:**` 줄을 적는다.

## PR 본문과 일지에 적을 것

- `Rule.position` 계약 보강(비교에서 빠지는 선택 칸, 어긋난 줄을 글자가 아니라 자리로 알리려는 것).
- 한계: 한 배열 안의 같은 줄 둘은 합쳐져 앞선 줄의 자리만 보고된다.
- 병합 뒤 남는 잔여(명세가 받아들였다): 공통 표 deny의 오타, 에이전트 표의 에이전트 이름 오타, 패턴 줄의 오타.
- 06(`feature/06-real-model-resume-after-all-deny`)이 05와 나란히 돈다. 고치는 파일이 겹치지 않을 것이다(어림). 05가 먼저 병합돼도 06의 실제 모델 시험은 그대로 초록이어야 한다.
- 기본 규칙을 넣기 전의 빨강 수 같은 어림은 재지 않았다.

## 근거의 종류

- 시험·린트·타입체크·경계·`run_checks`·변이의 통과와 수치는 이 세션이 친 명령의 출력(로그 파일)을 본 것이다. 변이 표지는 변이를 넣어 모은 실패 출력에서 골랐고 `mutate.py --check`가 원문 한 번씩을 확인했다. `run.py`·`rules.py`가 백업과 같다는 것은 `cmp`의 종료 코드 0을 본 것이다.
- 저장소와 e2e의 규칙 파일이 새 검사를 지난다는 것은 `plugins/rules.toml`·`plugins.ts`·`tests/test_main.py`를 Read·Grep으로 읽고 `_is_present`의 규칙과 맞대어 본 어림이다. 그 파일들을 새 검사로 돌려 본 것은 `run_checks`의 pytest(저장소 상태 시험과 `test_main.py`, `test_calc_plugin.py` 포함)뿐이고, 위젯 e2e와 `-m llm`은 아직 결과가 없다.
- 옛 표현 잔존은 Grep으로 본 것이다. 06 티켓과 나란히 돈다는 것은 06 티켓 본문의 문장을 읽은 것이고 병합 순서는 재지 않았다.

## 새 세션이 알아야 할 것

- 워크트리 가드(데스크톱 앱)가 변수가 든 명령을 거부했다. 절대 경로를 풀어 쓰고 명령은 하나씩 친다.
- 변이 표(`checks_mutations.toml`)는 `run.py`·`rules.py`를 바이트로 되돌리므로 변이가 도는 동안 두 파일과 시험을 고치지 않는다. 소스를 다시 고치면 `--check`로 원문 11개가 한 번씩 있는지 본다.
- 커밋하지 않은 변경: `.claude/rules/core.md`, `.claude/rules/sdk.md`, 티켓 05, `adapters/filesystem.py`, `core/ports.py`, `core/rules.py`, `core/run.py`, `tests/adapters/test_filesystem.py`, `tests/core/test_rules.py`, `tests/core/test_run.py`, 미추적 `.scratch/approval-rules/probes/checks_mutations.toml`, 이 일지.

open-session을 부른다 2026-11-07T16:13Z

open-session을 부른다 2026-11-07T17:06Z
