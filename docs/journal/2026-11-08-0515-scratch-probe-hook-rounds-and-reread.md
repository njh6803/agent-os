# 2026-11-08 스크래치 프로브 훅: Rounds 없는 프로브를 짚고, 읽지 않은 재편집을 막는다 (harness scratch-probe-hook-rounds-and-reread)

세션 제목: `chore/scratch-probe-hook-rounds-and-reread`. 브랜치도 같다. 워크트리는 `.claude/worktrees/scratch-probe-hook-rounds-and-reread`.

## 사용자 프롬프트

> 사용자: 대기열 430과 426을 티켓 .scratch/harness/issues/scratch-probe-hook-rounds-and-reread.md로 쓰고 한다
> 다음 작업: 모델 Sonnet 5.5 / high. 읽을 것은 `docs/agents/issue-tracker.md`, `.claude/rules/tools.md`, `.scratch/retro-queue/0430.md`, `0426.md`. 이번 요청 범위: PR과 병합까지

## 한 것

- 티켓 `.scratch/harness/issues/scratch-probe-hook-rounds-and-reread.md`를 새로 썼다. 430과 426은 같은 훅을 고치므로 한 티켓으로 묶었다.
- 430(계기): `tools/hook_scratch_probe_rule.py`가 저장소 프로브(`.scratch` 뒤 `probes` 토막 아래 `.py`)를 Write·Edit한 뒤 `probe_kit`과 낱말 `Rounds`가 없으면 한 번 알린다. Write는 입력의 `content`를, Edit는 PostToolUse 시점에 이미 고쳐진 디스크의 파일을 읽는다. 읽지 못하면 알린다. 표지는 스크래치패드 알림과 이유(`rounds`)로 따로 둔다.
- 426(막는 훅): 새 훅 `tools/hook_scratch_probe_reread.py`(PreToolUse `Write|Edit`)가 스크래치 스크립트의 둘째 시도부터 `.claude/rules/probes.md`를 Read로 연 기록이 없으면 거부한다. 상태는 표지 파일이 아니라 대화 기록(`transcript_path`)에서 센다. 거부는 최대 두 번이고 그 뒤는 지나간다.
- 새 훅을 기존 훅과 나눈 까닭: `tools/run_hooks.py`의 `registered_hooks`가 훅 하나를 이벤트 둘에 등록하는 것을 거부하고, `coverage_gaps`가 발동 사례 없는 훅(읽음 표지만 쓰는 훅)을 받지 않는다. 그래서 표지 대신 기록을 읽는 설계로 바꿨다.
- 러너에 자리표시자 `${SCRATCH_WRITTEN_TRANSCRIPT}`, `${PROBES_READ_TRANSCRIPT}`를 더했다. 페이로드 표에 두 훅의 사례를 더했고(`hook_scratch_probe_rule`의 옛 침묵 사례는 README Edit로 바꿨다), `.claude/settings.json`에 등록했다.
- 변이 표: `scratch_probe_rule_hook_mutations.toml`에 Rounds 변이 열셋을 더했고, `scratch_probe_reread_hook_mutations.toml`을 새로 만들었다(변이 열아홉과 대조군 하나).
- 문서 맞춤: `.claude/rules/probes.md` 머리, `docs/agents/issue-tracker.md`의 프로브와 근거 절, `.claude/rules/tools.md`의 시간 항목, `.scratch/harness/probes/README.md`의 변이 표 행.
- 사전 등록 문서(426의 둘째 몫)에는 새 훅을 더하지 않았다. 일지 2026-10-22-08의 사건은 스크래치 스크립트가 설계 문서보다 먼저였고 거부 훅이 그 길을 덮는다. 설계 문서의 이름과 위치가 정해져 있지 않아 낱말로 거는 훅은 거짓 양성이 많을 것으로 본다(어림, 재지 않았다). 거부 훅이 선 뒤에도 설계 문서에서 어긴 일이 있으면 그 사건을 대기열에 센다.

## 변이 도중의 발견 (이 세션이 `tools/mutate.py` 출력으로 본 것)

- "거부 이유에서 규칙 파일 경로를 뺀다"는 이유 문장에 경로가 두 번 들어 있어 한 곳만 지우면 시험이 초록이었다. 두 곳을 모두 지우는 변이로 고쳐 빨강을 확인했다.
- "낱말 경계 없이 Rounds 를 찾는다"가 처음에 초록이었다. `MyRounds`, `RoundsList` 같은 이름에 `Rounds` 낱말이 들었다고 지나가지 않는다는 시험이 없었다. 시험을 더하고 다시 빨강을 확인했다.
- 리팩터가 기존 변이 둘의 원문을 어긋나게 했다(원문이 2곳 존재, 0곳 존재). `tools/mutate.py --check`로 알아보고 고쳤다.

## 다음

- 대기열 431(`pyright` 계기 훅)과 475(`hook_edit_during_commit` Bash 확장)도 `.claude/settings.json`과 `tools/hook_payloads.toml`을 건드린다. 이 티켓이 PreToolUse 등록 한 그룹과 페이로드 표의 `hook_scratch_probe_rule`·`hook_scratch_probe_reread` 사례를 고쳤으므로, 두 항목을 반영할 때 이 PR이 병합된 main에서 시작해 합친다. 같이 열지 않았다.
- 거부 훅이 선 뒤에도 사전 등록 문서(`.scratch/<slug>/design.md` 등)에서 같은 사고가 나면 그 사건을 대기열에 센다.
- retro 후보 둘이 이 chore의 몫이 아니다. 하나는 approval-rules 05 PR(njh6803/agent-os#491)의 CodeRabbit Minor(마스킹을 선언한 서버와 도구를 내는 서버가 다르면 `core/run.py`의 `_reject_masked_asks`와 실행 중 게이트의 규칙이 어긋난다)이고, 다른 하나는 `tests/tools/test_probe_kit.py`의 `test_배출은_줄이_계속_와도_제한_시간에_끝난다`가 부하에 흔들린 것이다. 이 세션이 마칠 때 retro가 후보로 판정한다.

## 인계 시점의 상태 (셀프 리뷰 직전)

세션 제목은 `chore/scratch-probe-hook-rounds-and-reread`였다. 컨텍스트가 인계 문턱을 넘어 `셀프 리뷰 직전`에서 넘겼다. 커밋은 아직 없다.

- 끝난 것(이 세션이 본 출력이다): 두 훅과 러너 자리표시자, 등록, 페이로드 표, 변이 표 둘, 문서 맞춤(`probes.md`, `issue-tracker.md`, `tools.md`, 프로브 README), 티켓 done(수용 기준 `[x]`).
- 검증: 훅 관련 시험 146건 통과(`uv run pytest tests/tools/test_hook_scratch_probe_rule.py tests/tools/test_hook_scratch_probe_reread.py tests/tools/test_run_hooks.py tests/tools/test_launch_hook.py -q`, 571초). `uv run python tools/run_checks.py` 한 바퀴에서 pyright와 pyright-linux가 각각 19건으로 실패했고(`ToolInput`에 `new_string` 없음, 새 훅의 대화 기록 줄을 `dict[Unknown, Unknown]`으로 읽음, 새 시험의 `json.loads` 결과), 나머지 run-hooks·pytest·web-verify·check-ticket·zizmor·lint-imports·check-instructions·check-type-escapes는 통과했다. 고친 뒤 `uv run pyright`는 종료 코드 0, `uv run ruff check .`와 `uv run ruff format`도 0, 두 시험 파일은 69건 통과(1.49초). pyright-linux는 고친 뒤 다시 치지 않았다.
- 카나리아: `uv run python tools/sibling_overlap.py`가 규칙 파일(`probes.md`, `tools.md`)을 바꿨으니 카나리아 명세를 다시 돌리라고 알렸다(종료 1, 번호 겹침은 없다). 영향받는 명세는 `.scratch/harness/probes/canary/tools_rule_scratch_probe_hook.toml` 하나였다. 이 세션이 `tools.md`의 `hook_scratch_probe_rule` 문장을 바꿔 기대 문구가 깨졌으므로 `expect`를 `"(저장소 프로브)일 때만 표지 파일 하나를 만든다"`로 고치고 머리 주석에 그 사유를 적었다. 사전 확인(`--preflight`)은 통과했다. 실제 회차는 `uv run python tools/canary.py .scratch/harness/probes/canary/tools_rule_scratch_probe_hook.toml <스크래치 출력 디렉터리>`로 돌렸고, 러너 출력에서 통과 4, 실패 0, "없음" 섞인 통과 0, 대조군 "없음", 러너가 찍은 커밋 `dd1c0190`을 봤다. 실험군이 바뀐 문장을 글자 그대로 옮겼다. 명세 머리의 `# 최신 결과:` 줄을 그 결과로 고쳤다.
- 아직 안 한 것: `/code-review`(범위는 `origin/main`과의 merge-base 이후 커밋 0개, 미커밋·미추적 전부), 반영, retro(이 일지의 "다음"에 적은 후보 둘과 이 인계 과정에서 본 것), 커밋(`git branch --show-current`와 `uv run python tools/sibling_overlap.py` 먼저), 푸시, PR(끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`), 봇 회차, 병합(`merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다).
- 병합 충돌 후보(`sibling_overlap.py` 출력): PR 492와 워크트리 `open-session-prompt-file-path-check`가 `.claude/settings.json`을, `origin/main`과 워크트리 `probe-conclusion-fixed-path-in-probe-file`·`mutate-marker-call-fragment`·`measure-word-journal-scope`가 `.scratch/harness/probes/README.md`를, 앞의 둘과 `measure-word-journal-scope`가 `docs/agents/issue-tracker.md`·`tools/hook_payloads.toml`·`.claude/rules/tools.md`를 함께 고친다. 병합 전에 `origin/main`을 합친다(`sync_with_base_branch`).

## 셀프 리뷰 (인계 받은 세션, 2026-11-07T20:5xZ. 기준 `dd1c0190`, 파일 11개 수정과 5개 미추적, 커밋 0개)

표준 축(sonnet·high)은 하드 위반 없이 Major 1, Minor 6, smell 2를 냈다. 명세 축은 Critical 없이 부분 구현 둘과 틀려 보이는 것 다섯을 냈다. 수 검증은 둘 다 맞았다(Rounds 변이 열셋, 거부 훅 변이 열아홉과 대조군 하나, `tools/mutate.py --check` 통과).

- Major(표준 1, 명세 c2): 같은 메시지에서 스크래치 스크립트 Write 형제를 병렬로 내고 기록에 형제의 `tool_use`가 이미 있으면, 첫 시도에서 서로를 앞선 시도로 세어 모두 거부한다(기록 모양을 흉내 낸 `count_history` 호출로 둘 다 확인했다. 실제 Claude Code가 형제 줄을 PreToolUse 전에 쓰는지는 재지 않았다).
- Minor: 실패한 Edit·거절된 Write도 `earlier`를 키운다(표준 2). "거부된 시도도 기록에 남는다"의 근거 종류가 없다(표준 3, 명세 c3). 독스트링 머리의 "같은 호출을 다시 부르면 우회"가 거부 이유의 안내와 모순이다(표준 4). 시험 `test_스크래치_스크립트_판정은_알림_훅과_같다`가 알림 훅의 함수와 견주지 않는다(표준 5). 독스트링 "앞에서 끝까지 한 번 읽는다"가 읽음에서 멈추는 코드와 다르다(표준 6). `tools.md`의 `hook_scratch_probe_rule` 줄이 "경로 문자열만 보고"로 시작해 같은 줄에서 Edit면 디스크를 읽는다고 적어 모순이다(표준 7).
- 명세 a1: 수용 기준 2 "가리키는 문장이 그 파일에 있다는 시험"이 이름만 본다(probes.md의 첫 항목 문장은 읽지 않는다). a2: 못 보는 것 몇 개(Edit가 읽는 파일은 이미 고쳐졌다, 측정이 아닌 프로브, 줄 모양이 바뀌어 조용히 문이 열리는 경우)에 전용 시험이 없다.
- 명세 c1: "거부가 사전 등록 길을 이미 덮는다"는 둘째 시도부터만 맞다. c4: 스크래치 쓰기가 셋 이상 이어진 기록(재개·긴 세션)은 읽지 않았어도 지나간다는 말이 없다. c5: 거부 이유가 읽지 않고 다시 부르면 한 번 더 막힌다는 순서를 말하지 않는다.

### 반영 (같은 세션, 2026-11-07T21:xxZ)

- 고쳤다, Major(병렬 형제): `tools/hook_scratch_probe_reread.py`의 `count_history`가 도구 결과(`tool_result` 줄의 `tool_use_id`)가 기록에 이미 있는 시도만 앞선 시도로 센다. 형제 호출은 결과가 아직 없어 서로를 세지 않는다. 결과 줄은 JSON으로 풀지 않고 `"tool_result"` 표지가 든 줄에서 `tool_use_id`만 정규식으로 건진다. 실제 기록의 모양은 이 PC의 앱 세션 기록 한 개를 `look_transcript.py`(스크래치 스크립트, 커밋하지 않았다)로 손으로 봤다: `tool_result` 블록의 키 순서는 `type`, `tool_use_id`, `content`였고 `type` 이 `user` 인 줄에 든다. 같은 기록에서 훅이 거부한 Bash·AskUserQuestion 호출의 `tool_use` 줄이 남고 뒤에 `is_error` 도구 결과가 붙은 것도 봤다(명령은 `uv run python -I <look_transcript.py> <기록 경로>`. `is_error` 결과 세 개를 찍었고 그중 둘이 훅이 거부한 호출이었다). "거부된 시도도 기록에 남는다"는 전제의 근거 종류가 그것이다(기록 한 개).
- 고쳤다, 러너: `tools/run_hooks.py`의 `_scratch_written_transcript`가 만드는 기록에도 도구 결과 줄을 더했다. 안 더하면 페이로드 표의 거부 사례가 결과 없는 시도로 지나간다.
- 고쳤다, 독스트링과 거부 이유: 머리의 "같은 호출을 다시 부르면 우회"가 이유의 안내와 어긋난 것을 "읽지 않고 같은 호출을 되풀이해 두 번 막힌 뒤 지나가는 것과 Bash heredoc"으로 바꿨다. 판정 절에 결과가 있는 시도만 센다는 것과 거부된 시도가 기록에 남는 근거를 적고, 못 보는 것에 실패한 시도·상한을 넘게 쌓인 기록·사전 등록 문서·결과가 아직 없는 시도를 더하고, "앞에서 끝까지 한 번 읽는다"를 읽음을 만나면 멈추고 못 만나면 끝까지 읽는다로 맞췄다. 거부 이유에 "읽지 않고 다시 부르면 이 훅이 한 번 더 막고, 세션마다 두 번까지만 막은 뒤 지나간다"를 더했다.
- 고쳤다, 시험: `test_hook_scratch_probe_reread.py`의 `_transcript`가 시도마다 결과 줄을 붙이고 `pending`으로 결과 없는 호출을 가른다. 병렬 형제(결과 없음이면 지나가고, 결과가 온 앞선 시도는 센다), 실패한 시도, 읽음이 기록에 아직 없을 때, 압축 뒤의 읽음, 상한을 넘게 쌓인 기록, 결과 줄의 모양이 바뀔 때, 측정이 아닌 도우미, 스크래치패드의 설계 문서, 거부 이유의 순서 문구를 더했다. 판정 대조 시험은 이제 알림 훅의 `is_scratch_script`와 같은 입력으로 견준다. `test_hook_scratch_probe_rule.py`에는 알림이 가리키는 첫 항목 문장이 `probes.md`에 있다는 시험(명세 a1)과 측정이 아닌 저장소 프로브 시험을 더했다.
- 고쳤다, 변이 표: 원문이 사라진 변이 다섯을 새 코드에 맞췄고 병렬 형제 변이를 하나 더해 변이 스물과 대조군 하나다. 처음 돈 판에서 "읽음이 있어도 거부한다"가 초록으로 살아남았다. `count_history`가 읽음에서 `earlier` 를 0 으로 돌려주도록 단순화해 `reason_for`의 `history.read` 검사가 중복이 된 탓이었다. 읽음일 때도 모은 시도 수를 돌려주게 되돌려 그 변이만 다시 돌려 빨강을 확인했다(`tools/mutate.py <표> 4`의 출력). 나머지 20은 되돌림 전의 판에서 기대대로였다. 첫 커밋 시도는 pre-commit의 `mutation tables`(`tools/mutate.py --staged`)가 빨강 변이 35개에 `expect_output`이 없다며 막았다(대기열 350, 다른 까닭의 빨강도 기대와 맞는 것을 막는 검사). 두 표를 다시 돌려 얻은 출력(거부 훅 21, 알림 훅 26 모두 기대대로)에서 변이마다 처음 빨개진 시험 id로 `FAILED <시험 파일>::<시험 이름>` 표지를 만들어 빨강 변이 45개(거부 훅 20, 알림 훅 25)에 채웠다. 채우기는 스크래치 스크립트(`fill_expect_output.py`, 커밋하지 않았다)로 했고 표를 임시 파일로 쓴 뒤 바꿔 끼웠다. 표지가 실제로 찍히는지는 거부 훅 표를 다시 돌린 `tools/mutate.py` 출력에서 보았고 알림 훅 표는 커밋의 `--staged`가 확인한다.
- 고쳤다, 문서: 티켓의 거부 설명에 결과 기준을, 사전 등록 문장에 둘째 스크래치 스크립트부터 덮는다는 것과 한 번만 쓰고 설계 문서를 쓰는 세션은 막지 않는다는 것을 적었다. `.claude/rules/tools.md`의 `hook_scratch_probe_rule` 줄은 스크래치패드는 경로 문자열만, 저장소 프로브는 내용을 읽는다고 갈라 자기모순을 걷었고 `hook_scratch_probe_reread` 줄에 결과 기준을 더했다.
- 남겼다: 표준 축의 smell·Nit 둘은 고치지 않았다. 알림 훅 `notice_for`가 `(kind, text)` 튜플을 돌려주고 빈 문자열이 스크래치패드 알림의 센티널이라는 Primitive Obsession은 판단 항목이고, 그 튜플은 한 파일 안에서만 쓰여 새 타입을 두면 앞서 만든 추상이 된다고 봤다(재지 않은 판단이다). 깊게 중첩된 줄의 `RecursionError`는 훅이 fail-open이라 무해하다고 표준 축이 직접 확인했다. 병렬 형제의 `tool_use` 줄이 PreToolUse 전에 기록에 실제로 오는지는 이 세션이 재지 않았다(결과 기준으로 어느 쪽이든 세지 않게 했으므로 값이 작다).
- 다시 돌렸다(러너 출력을 이 세션이 봤다): `uv run ruff check .`는 통과, `uv run ruff format --check .`는 1939개 이미 정렬, `uv run pyright`는 0 errors. `uv run python tools/run_checks.py`는 종료 코드 0이고 check-ticket·lint-imports·zizmor·check-instructions·check-type-escapes·pyright(40.6초)·pyright-linux(41.0초)·run-hooks(62.7초)·pytest(447.7초)·web-verify(534.2초)가 모두 Passed였다. 인계 때 다시 치지 못했던 pyright-linux도 이 판에서 통과했다. 카나리아는 `uv run python tools/canary.py .scratch/harness/probes/canary/tools_rule_scratch_probe_hook.toml <출력 디렉터리>`로 반영한 문장에 다시 돌려 통과 4, 실패 0, "없음" 섞인 통과 0, 대조군 "없음", 러너가 찍은 커밋 `dd1c0190`이었다. `sibling_overlap.py`가 `probes.md`를 원천으로 든 명세 여덟을 다시 돌리라고 알려, 여덟의 사전 확인(`uv run python tools/canary.py --preflight <여덟 경로>`)은 모두 통과했고 일반 명세 `probes_rule.toml`만 실제 회차를 돌려 통과 4, 실패 0, "없음" 섞인 통과 0을 봤다(`최신 결과` 줄을 고쳤다). 나머지 일곱은 실제 회차를 돌리지 않았다. 이 변경이 고친 것은 `probes.md`의 머리 문단뿐이고 일곱이 기대하는 문구(항목 본문, 예: `Rounds`, `LineReader`)는 건드리지 않았다는 것은 코드를 읽은 판단이다. 이 세션이 `-m llm`·e2e·사진 비교는 돌리지 않았다(이 변경은 그 영역을 건드리지 않았다).

open-session을 부른다 2026-11-07T20:45Z
