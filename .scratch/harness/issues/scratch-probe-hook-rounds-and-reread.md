# scratch-probe-hook-rounds-and-reread: 스크래치 프로브 훅이 Rounds 없는 프로브를 짚고, 알린 뒤에도 probes.md를 열지 않은 재편집을 막는다

**What to build:** `tools/hook_scratch_probe_rule.py`는 지금 세션 스크래치패드의 실행 스크립트를 Write·Edit로 쓰면 `.claude/rules/probes.md`를 Read로 열라고 세션·에이전트마다 한 번 알릴 뿐이다. 이 티켓은 두 가지를 더한다. 하나는 저장소 프로브에 `Rounds`가 없을 때 짚는 계기(대기열 430)이고, 다른 하나는 알린 뒤에도 probes.md를 열지 않은 채 스크래치 스크립트를 다시 고치면 막는 것(대기열 426)이다.

**430, 계기.** 같은 훅(PostToolUse `Write|Edit`)이 `.scratch/**/probes/**/*.py`(`.scratch` 토막 뒤 어딘가에 `probes` 토막이 있고 확장자가 `.py`)를 Write·Edit한 뒤, 그 파일 내용에 `probe_kit`과 낱말 `Rounds`가 둘 다 없으면 알린다. Write는 `tool_input.content`를 보고, Edit는 `new_string`만으로는 파일 전체를 알 수 없어 PostToolUse에 이미 고쳐진 디스크의 파일을 읽는다. 읽지 못하면 놓치는 쪽보다 알리는 쪽으로 간다. 알림은 `.claude/rules/probes.md` 첫 항목(재려는 상황이 났다는 표지를 단언하고 표지 없는 회차를 측정으로 세지 않는다)과 `tools/probe_kit.py`의 `Rounds`(`round`로 감싸고 표지를 본 뒤 `mark`를 부르고 `exit_code`를 종료 코드로 쓴다)를 가리키고, 측정 스크립트가 아니면(도우미, 변이 표를 읽는 스크립트) 무시하라고 적는다. 표지는 세션·에이전트마다 한 번이고, 스크래치패드 알림의 표지와 이유(`rounds`)로 따로 둔다. 막지 않는다. `.claude/rules/tools.md`의 계기·막는 훅 가름에서 계기는 단계를 닫는 순간의 지침에 처음부터 붙이고, 막는 훅은 지침으로 적은 뒤에도 어겨진 것이 확인된 뒤에 더한다. 430은 저장소 프로브에 알림이 처음 서는 자리라 계기 쪽이다.

**426, 막는 훅.** 스크래치 스크립트를 쓴 세션이 probes.md를 Read로 열지 않은 채 스크래치 스크립트를 또 Write·Edit하려 하면 PreToolUse에서 거부한다. 거부 이유는 도구 결과로 모델에게 닿아(`.claude/rules/tools.md`의 PreToolUse 항목) 모델이 파일을 열게 한다. 새 파일 `tools/hook_scratch_probe_reread.py`로 나눈다. 같은 파일에 두려 했으나 `tools/run_hooks.py`의 `registered_hooks`가 훅 하나를 이벤트 둘에 등록하는 것을 거부하고(훅은 `hookEventName` 하나를 내므로), `coverage_gaps`는 발동 사례가 없는 훅(표지만 쓰는 읽음 훅)을 받지 않는다. 설계는 다음과 같다.

- 상태를 표지 파일이 아니라 대화 기록(`transcript_path`)에서 읽는다. 읽음 표지를 만들려면 PostToolUse `Read`에 침묵만 하는 훅을 등록해야 해서 러너가 받지 않는다. 기록에는 지금까지의 도구 호출이 모두 있다. 기록 한 줄은 `{"type":"assistant","isSidechain":false,"message":{"content":[{"type":"tool_use","id":…,"name":"Write","input":{"file_path":…}}]}}` 모양이다(실제 기록 파일 한 개에서 손으로 봤다. 키 이름은 `.scratch/harness/probes/pretool_text/`와 `tools/hook_midturn_korean.py`가 같이 쓴다).
- 센다. 기록에서 서브에이전트 쪽(`isSidechain`이 참)이 아닌 줄의 `tool_use` 블록을 훑어, 이 호출의 `tool_use_id`가 아닌 것 가운데 입력의 `file_path`가 스크래치패드 실행 스크립트인 Write·Edit의 수 `earlier`와, `file_path`가 `.claude/rules/probes.md`로 끝나는 Read의 유무를 본다. 이 호출의 기록이 PreToolUse 시점에 이미 있을 수도 없을 수도 있어(`hook_midturn_korean`의 독스트링) 자기 id를 뺀다. 도구 결과(`tool_result` 블록의 `tool_use_id`)가 기록에 이미 있는 시도만 센다. 같은 메시지에서 병렬로 내는 형제 호출은 결과가 아직 없어 서로를 앞선 시도로 세지 않는다(셀프 리뷰 Major, 일지 2026-11-08-0515).
- 거부한다. 읽음이 없고 `1 <= earlier <= DENY_LIMIT(2)`일 때다. 첫 시도(`earlier == 0`)는 지나가고 PostToolUse의 첫 알림이 나간다. 거부된 시도도 기록에 `tool_use`로 남아 `earlier`를 키우므로, 읽지 않고 세 번째까지 다시 불러도 두 번만 거부하고 네 번째에 지나간다. 측정이 아닌 도우미 스크립트일 수 있고 훅은 측정인지 가르지 못한다. 끝나지 않는 고리가 되지 않게 하고, 거짓 양성이 많은 규칙을 하드 게이트로 만들지 않기 위한 상한이다. 이 상한 뒤의 시도는 일부러 하는 우회이고 독스트링 머리에 그렇게 적는다.
- 막지 않는 길(fail-open). 기록 경로가 없거나 읽지 못하거나, `tool_use_id`가 없거나, 서브에이전트(`agent_id`)의 호출이다. 서브에이전트는 기록이 따로라 이 훅이 센 것이 그쪽을 보지 못한다. 서브에이전트에는 막지 않고 첫 알림만 나간다(재지 않았다).
- 읽음은 `.claude/rules/probes.md`를 직접 Read한 것만 센다. 저장소 프로브를 Read할 때 `paths` 규칙이 자동으로 싣는 probes.md는 기록에 `Read` 호출로 남지 않아 세지 않는다. 이때는 거부 이유대로 한 번 더 읽으면 된다(거짓 양성, 독스트링의 못 보는 것).

**등록과 표.** `.claude/settings.json`의 PreToolUse에 매처 `Write|Edit`로 새 훅을 더한다(시간 제한은 다른 Write·Edit 훅과 같은 20초). `tests/tools/test_hook_scratch_probe_reread.py`(기록 판정, 상한, fail-open 길, 등록 매처)와 `tests/tools/test_hook_scratch_probe_rule.py`(Rounds 알림)를 더한다. `tools/hook_payloads.toml`에 두 훅의 사례를 더한다. 새 훅이 쓰는 기록 사례를 위해 `tools/run_hooks.py`에 자리표시자 `${SCRATCH_WRITTEN_TRANSCRIPT}`(스크래치 스크립트 Write가 한 번 있고 probes.md Read는 없는 기록)와 `${PROBES_READ_TRANSCRIPT}`(그 Write 뒤에 probes.md Read도 있는 기록)를 더하고 모듈 독스트링의 목록에 적는다. 변이 표 `.scratch/harness/probes/scratch_probe_rule_hook_mutations.toml`에 Rounds 알림의 변이를 더하고 새 훅의 변이 표 `scratch_probe_reread_hook_mutations.toml`을 만들며 `.scratch/harness/probes/README.md`에 행을 맞춘다. `.claude/rules/tools.md`의 시간 항목(Write·Edit 목록), `.claude/rules/probes.md` 머리, `docs/agents/issue-tracker.md` 프로브와 근거 절의 스크래치패드 문장을 맞춘다. 독스트링에는 막는 대상이 실수인지 일부러 하는 우회까지인지(실수. 두 번 거부된 뒤의 시도와 Bash heredoc은 우회로 지나간다)와 못 보는 것을 적고, 항목마다 시험으로 고정한다.

**426의 둘째 몫, 사전 등록 문서.** 대기열 426은 사전 등록 절을 쓰는 `.scratch/<slug>/` 문서(측정 설계)에도 이 항목이 닿게 할지 함께 보라고 했다. 일지 2026-10-22-08(model-rerun-design)의 사건은 알림이 스크래치 측정 스크립트(`branch_cost.py`)에 나간 뒤 그 세션이 probes.md 대신 `docs/agents/issue-tracker.md`를 열었고, 이어 쓴 설계 문서 `.scratch/model-rerun/design.md`가 사전 등록을 6절만 옮겨 셀프 리뷰에 잡힌 것이다(일지의 기록을 읽은 것이다). 이 티켓은 설계 문서에 새 훅을 더하지 않는다. 스크래치 스크립트가 설계 문서보다 먼저였으므로 위 거부가 둘째 스크래치 스크립트부터 그 길을 덮는다(스크래치 스크립트를 한 번만 쓰고 설계 문서를 쓰는 세션은 이 훅이 막지 않는다). 설계 문서의 이름과 위치가 정해져 있지 않아(`design.md`, `spec.md`, 프로브 README 행) 낱말(`사전 등록`)로 거는 훅은 거짓 양성이 많을 것으로 본다(어림, 재지 않았다). 거부 훅이 선 뒤에도 설계 문서에서 어긴 일이 있으면 그 사건을 대기열에 센다.

**병합 충돌 메모.** 대기열 431(`pyright` 계기 훅)과 475(`hook_edit_during_commit` Bash 확장)도 `.claude/settings.json`과 `tools/hook_payloads.toml`을 건드린다. 이번에 같이 열지 않았으니, 이 티켓이 등록과 페이로드 표를 고친 것을 일지 "다음"에 적어 두 항목의 반영 때 합치게 한다.

**대기열:** 426, 430

**Status:** done

## 수용 기준

- [x] 저장소 프로브(`.scratch` 뒤 `probes` 토막 아래 `.py`)를 Write·Edit한 뒤 파일 내용에 `probe_kit`과 `Rounds`가 없으면 세션·에이전트마다 한 번 알리고, 둘 다 있으면 지나간다. Edit는 디스크의 파일을 읽고, 읽지 못하면 알린다
- [x] 알림이 probes.md 첫 항목과 `tools/probe_kit.py`의 `Rounds`를 가리키고, 가리키는 문장이 그 파일에 있다는 시험이 있다
- [x] 새 PreToolUse 훅이 스크래치 스크립트의 둘째 시도부터 probes.md Read가 기록에 없으면 거부하고, Read가 있으면 지나간다. 거부는 최대 두 번이다
- [x] 첫 시도, 서브에이전트, 기록을 읽지 못하는 호출, `tool_use_id` 없는 호출, 스크래치패드가 아닌 경로는 거부하지 않는다. 서브에이전트 쪽 기록(`isSidechain`)의 호출은 센 수에 넣지 않는다
- [x] 독스트링 머리에 막는 대상(실수)과 일부러 하는 우회를, 못 보는 것에 Bash heredoc·측정이 아닌 도우미의 거짓 양성·`paths` 자동 로드·서브에이전트·상한 뒤의 시도를 적고, 항목마다 시험으로 고정했다
- [x] 등록(PreToolUse `Write|Edit`)과 매처 시험, 페이로드 표 사례(발동·거부·침묵)와 러너 자리표시자, 변이 표(대조군 포함)를 맞췄다
- [x] `tools.md`의 시간 항목, `probes.md` 머리, `issue-tracker.md`의 스크래치패드 문장을 맞췄고 옛 표현의 잔존이 0이다
- [x] 일지 "다음"에 431·475와 페이로드 표·등록을 합쳐야 한다는 것을 적었다
- [x] 검증 명령이 모두 초록이다
