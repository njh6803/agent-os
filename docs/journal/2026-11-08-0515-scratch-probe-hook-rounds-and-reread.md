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

## 회고

후보 네 개를 냈다. 승인 1(대기열에 둠), 기각 3, 넘김 0이다. 둘째 인계 세션이 일지에 남긴 후보 둘과 이 세션이 본 둘을 함께 판정했다.

- 승인(대기열에 둠): 같은 세션에서 `origin/main`을 합쳐 서브에이전트 정의(`.claude/agents/coderabbit-review.md`)가 바뀌었는데 서브에이전트가 세션 시작 사본으로 돌아 CLI를 건너뛰었다. 사건은 이 일지 "푸시와 PR 단계"의 세 번째 세션이고, 층은 지침(`CLAUDE.md` 환경 함정의 스킬 줄 곁)이며 PR 하나로 되돌릴 수 있다. 새 지침 문장이라 문턱(다섯 번째 반복)에 이르지 않아 `.scratch/retro-queue/subagent-definition-stale-after-merge.md`에 1회차로 두었다. 닫힌 0128·0189(주 체크아웃의 옛 훅·스킬 사본)와는 다른 일이라 잇지 않았다.
- 기각: `tests/tools/test_probe_kit.py`의 `test_배출은_줄이_계속_와도_제한_시간에_끝난다`가 부하에 흔들린 일. 닫힌 306이 "부하에서 시간 시험이 빨개지면 그 커밋을 다시 치는 값을 받아들이고 사례를 더 고치지 않는다"로 닫혔고(ADR 0036), 새 사례는 회차를 더하지 않고 일지에만 적는다.
- 기각: approval-rules 05 PR(njh6803/agent-os#491)의 CodeRabbit Minor(마스킹을 선언한 서버와 도구를 내는 서버가 다르면 `core/run.py`의 `_reject_masked_asks`와 실행 중 게이트의 규칙이 어긋난다). 환경이 아니라 제품 코드의 결함 후보라 retro의 범위가 아니다. approval-rules 기능 계획의 몫으로 "다음"에 적었다.
- 기각: `mcp__ccd_host__sync_with_base_branch`가 이 워크트리에서 "앱이 만든 워크트리가 아니다"라며 거부했다. 거부 문구가 이유를 말하고, 이 저장소의 병합 길 문서(`merge.md`)와 이 일지가 `git merge origin/main`을 가리킨다. 한 번의 호출 비용이고 이미 있는 안내가 그 자리에서 알렸다.
- 만료: `uv run python tools/queue_open_rows.py --ref origin/main`의 "만료할 항목"이 없었다. 닫은 항목은 0426·0430 둘이다(상태 줄에 이 티켓을 적었다).

## 다음

- 대기열 431(`pyright` 계기 훅)과 475(`hook_edit_during_commit` Bash 확장)도 `.claude/settings.json`과 `tools/hook_payloads.toml`을 건드린다. 이 티켓이 PreToolUse 등록 한 그룹과 페이로드 표의 `hook_scratch_probe_rule`·`hook_scratch_probe_reread` 사례를 고쳤으므로, 두 항목을 반영할 때 이 PR이 병합된 main에서 시작해 합친다. 같이 열지 않았다.
- 거부 훅이 선 뒤에도 사전 등록 문서(`.scratch/<slug>/design.md` 등)에서 같은 사고가 나면 그 사건을 대기열에 센다.
- approval-rules 05 PR(njh6803/agent-os#491)의 CodeRabbit Minor가 열린 채다. 마스킹을 선언한 서버와 도구를 내는 서버가 다르면 `core/run.py`의 `_reject_masked_asks`와 실행 중 게이트의 규칙이 어긋난다는 지적이다(일지 앞부분이 옮긴 보고에서 읽은 것이고 이 세션이 코드를 열어 확인하지 않았다). 환경 후보가 아니라 제품 코드 결함 후보라 retro가 기각했다. approval-rules 기능 계획의 티켓으로 쓸지는 그 기능을 이어 가는 세션이 정한다.
- `tests/tools/test_probe_kit.py`의 `test_배출은_줄이_계속_와도_제한_시간에_끝난다`가 부하에 흔들린 일은 닫힌 306이 받아들인 종류라 일지에만 남긴다(위 "회고").

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

## 인계 시점의 상태 (커밋 뒤)

세션 제목은 `chore/scratch-probe-hook-rounds-and-reread`였다. 컨텍스트가 인계 문턱을 넘어 `커밋 뒤`에서 두 번째로 넘긴다. 앞의 "셀프 리뷰 직전" 인계로 연 세션이 이 세션이고, 셀프 리뷰와 반영을 마치고 커밋했다.

- 커밋: `2bbb3e02 feat: Rounds 없는 프로브를 짚고 읽지 않은 재편집을 막는다`. pre-commit이 ruff 둘, checks, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest, web-verify, 표·줄 구분 문자·변이 표·카나리아 명세·헌법 판·따옴표 검사, 커밋 메시지 검사를 모두 통과했다(`git commit` 출력의 Passed 줄을 이 세션이 봤다). 작업 트리는 깨끗하다(`git status --short`가 비었다).
- 푸시하지 않았다. PR도 없다. 이 일지의 이 절과 마지막 줄은 커밋하지 않은 편집이므로, 새 세션이 일지를 이어 쓰며 다음 커밋에 싣는다.
- 안 한 것: `origin/main` 합치기(`mcp__ccd_host__sync_with_base_branch`), 합친 뒤 검사 재확인, `uv run python tools/sibling_overlap.py`, 푸시, PR(끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`), `ccd_pr`의 `get_status`와 `bind_pr`, 봇 회차, 병합(`merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다), retro(이 일지의 "다음"에 적은 후보 둘), 대기열 426·430의 항목 닫기.
- 합칠 때의 충돌 후보: 앞 인계 시점에 `sibling_overlap.py`가 알린 대로 `.claude/settings.json`, `tools/hook_payloads.toml`, `.claude/rules/tools.md`, `docs/agents/issue-tracker.md`, `.scratch/harness/probes/README.md`다.
- 일지 "셀프 리뷰"와 "반영"의 "남겼다" 줄이 새 세션에 남는 열린 것이다: 병렬 형제의 `tool_use` 줄이 PreToolUse 전에 기록에 실제로 오는지는 재지 않았고, 카나리아 명세 일곱은 사전 확인만 돌렸다.

open-session을 부른다 2026-11-07T21:59Z

## 푸시와 PR 단계 (세 번째 세션, 2026-11-07T22:0xZ부터)

- 첫 턴에 `tidy-checkouts`를 돌았다. 루트(main)를 `e575f661`에서 `fe461837`까지 당겼고 정리 스킬 파일은 바뀌지 않았다. 병합된 워크트리는 모두 쥔 프로세스(쉬는 세션의 `claude.exe` 포함)나 커밋하지 않은 변경이 있어 지울 것이 없었다. 휴지통(`.tidy-trash/`)에 `node_modules` 둘이 남았고 `empty-trash`가 `node.exe`(pid 2740)·`esbuild.exe`가 올린 `.node`·`.exe`에 막혀 지우지 못했다. 그 프로세스가 끝난 뒤의 정리가 다시 비운다.
- 일지 편집을 커밋(`1c123aae`)한 뒤 `origin/main`을 합쳤다. `mcp__ccd_host__sync_with_base_branch`는 "앱이 만든 워크트리가 아니다"라며 거부해(거부 문구는 "이 세션은 앱이 만든 워크트리에서 돌지 않는다"였다. 왜 그렇게 보였는지는 확인하지 않았다) `git merge origin/main`으로 직접 합쳤다. 충돌은 `.scratch/harness/probes/canary/probes_rule.toml` 머리의 `최신 결과` 주석 한 곳뿐이었다. 두 쪽의 결과 줄을 시간순으로 모두 남기고, 합친 뒤 카나리아를 다시 돌리지 않았다는 것을 최신 줄에 적었다(합쳐 들어온 `probes.md` 변경은 첫 항목 본문이고 이 명세가 옮기는 첫 제목과 종료 코드 조각은 그대로다. 코드를 읽은 판단이다). `probes.md`, 프로브 README는 자동으로 합쳐졌다.
- 병합 커밋 `d2127f52`의 pre-commit이 모두 통과했다(checks 463.5초 안에 pytest 303.4초·web-verify 463.3초·pyright 둘·run-hooks 57.9초, 변이 표·카나리아 모양·표·줄 구분 문자·따옴표·커밋 메시지 검사. `git commit` 출력의 Passed 줄을 이 세션이 봤다).
- PR 직전 리뷰: `coderabbit-review` 서브에이전트가 먼저 돌았으나 이 세션이 로드한 정의가 `origin/main`을 합치기 전의 옛 사본(좌석 `not assigned`면 종료)이라 CLI를 돌리지 않고 대체 둘을 권하며 끝났다. 서브에이전트가 자기 보고에서 이 워크트리의 `.claude/agents/coderabbit-review.md`가 다르다고 알렸고, 이 세션이 그 파일을 Read로 열어 15행이 "`not assigned`여도 종료하지 않고 3으로 간다"인 것을 봤다. 그래서 새 정의 3단계의 명령 `coderabbit review --agent --include-untracked`를 이 세션이 직접 백그라운드로 돌렸다. 러너 출력의 마지막 줄이 `{"type":"complete","status":"review_completed","findings":0,...}`이었고 본 파일 17개(규칙·설정·티켓·프로브 README와 변이 표 둘·`issue-tracker.md`·일지·시험 둘·`hook_payloads.toml`·훅 둘·`run_hooks.py`)가 `reviewedFiles`에 들었다. 서브에이전트 보고의 `Seat: not assigned`, `Plan: Free`, CLI 0.7.5는 그 보고에서 옮겼다. CLI 리뷰가 끝까지 돌았으므로 대체 둘(`/security-review`, `bug-perf-review`)은 돌리지 않았다.
- 푸시하려 하니 푸시 앞의 훅이 "이 브랜치는 origin/main 보다 1커밋 뒤처졌다"며 막았다(훅 이름은 확인하지 않았다). `origin/main`이 한 커밋 더 나아가 있었고, 다시 합치자(`git merge origin/main`) 충돌이 `.claude/rules/tools.md`의 `hook_probe_conclusion` 줄 근처 한 곳과 `docs/agents/issue-tracker.md`의 프로브 문장 한 곳이었다. 둘 다 이 브랜치의 문장(`hook_scratch_probe_rule`이 저장소 프로브도 본다, 거부 훅과 `Rounds` 알림)과 `origin/main`이 더한 문장(대기열 535의 `고친 길`)을 둘 다 남겨 풀었다. `issue-tracker.md`는 문장이 길어 스크래치패드의 풀기 스크립트로 풀었다. 병합 커밋 `b5f7d0aa`의 pre-commit이 모두 통과했다(checks 534초, `git commit` 출력의 Passed 줄을 이 세션이 봤다). 푸시 전 `uv run python tools/sibling_overlap.py`는 번호 겹침 없음이었다.
- PR #497을 열었다(제목 `feat: Rounds 없는 프로브를 짚고 읽지 않은 재편집을 막는다 (harness scratch-probe-hook-rounds-and-reread)`, 본문은 템플릿대로 썼다).

## 인계 시점의 상태 (PR 연 뒤)

세션 제목은 `chore/scratch-probe-hook-rounds-and-reread`였다. 컨텍스트가 인계 문턱을 넘어 `PR 연 뒤`에서 세 번째로 넘긴다.

- PR: https://github.com/njh6803/agent-os/pull/497 . 푸시한 머리는 `b5f7d0aa`이다. 이 일지의 이 절과 앞 절의 편집(위 "푸시와 PR 단계" 세 줄과 이 절)은 커밋하지 않았다. 새 세션이 이어 쓰고 봇 회차의 커밋에 싣는다(`merge.md` 3).
- 안 한 것: `@coderabbitai review` 코멘트(첫 코멘트는 새 세션이 남긴다), `ccd_pr`의 `get_status`와 `bind_pr`(이 세션은 `get_session`에서 `prNumber` 497, `prState` OPEN이 이미 보였다), 봇 회차와 반영, retro(이 일지 "다음"의 후보 둘과 이 세션이 본 것), 일지 "다음" 마무리, 대기열 426·430의 항목 닫기, 병합(`merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 주 체크아웃에서 열지 않았다), 병합 뒤 원격 정리.
- 이 세션이 본 것 하나: `mcp__ccd_host__sync_with_base_branch`가 이 워크트리에서 "앱이 만든 워크트리가 아니다"라며 거부했다. 병합 충돌을 풀 때는 `git merge origin/main`을 직접 쓴다.
- 이 세션이 본 것 둘: 서브에이전트 정의는 세션이 시작할 때 로드되어 `origin/main`을 합쳐도 같은 세션에서는 옛 사본이 돈다. 이 일지는 그것이 대기열 후보인지 판정하지 않았다(retro가 판정한다).
- 열린 것: 병렬 형제의 `tool_use` 줄이 PreToolUse 전에 기록에 실제로 오는지는 재지 않았다. 카나리아 명세 일곱은 사전 확인만 돌렸고 `probes_rule.toml`은 `origin/main`을 합친 뒤 다시 돌리지 않았다.
- 충돌 후보(`sibling_overlap.py`): PR #492와 워크트리 `open-session-prompt-file-path-check`가 `.claude/settings.json`을, 워크트리 `measure-word-journal-scope`가 `.scratch/harness/probes/README.md`·`docs/agents/issue-tracker.md`·`tools/hook_payloads.toml`을 함께 고친다. 병합 전에 `origin/main`을 다시 합친다. `sync_with_base_branch`가 거부하므로 `git merge origin/main`이다.

open-session을 부른다 2026-11-07T22:38Z

## 봇 회차 (이 세션, 2026-11-07T22:5xZ)

- `tools/wait_ci.py 497`의 끝 줄(이 세션이 본 출력)은 헤드 `b5f7d0a`에서 CodeRabbit NEUTRAL(`Review rate limited`), claude-review·e2e·e2e-widget·python·ticket·verify·visual·web 모두 SUCCESS이고 종료 0이었다. CodeRabbit의 PR 코멘트는 "다음 리뷰는 3분 뒤"라고 했고, 이 세션이 남긴 `@coderabbitai review` 코멘트에는 같은 한도 문구로 답했다. 한도에 걸린 푸시는 회차로 세지 않는다.
- claude-review의 첫 회차(PR 코멘트에서 읽었다): Critical·Major 없음, Minor 1, Nit 2. 셋 모두 고치지 않고 PR 코멘트에 이유를 남겼다. Minor(`History.earlier`가 읽음일 때와 아닐 때 뜻이 다르다)는 제안한 `earlier=0` 반환을 셀프 리뷰 반영 중 이미 해 보았고 그러면 `history.read` 검사가 중복이 되어 변이가 살아남아 되돌렸다는 이유다(위 "반영"). Nit 둘(알림 종류의 빈 문자열 센티널, `is_scratch_script` 복사)은 의도된 비용이고, 복사된 판정이 갈라지는 것은 `test_hook_scratch_probe_reread.py`의 판정 대조 시험이 이미 잡는다(그 시험 364행을 Grep으로 열어 같은 입력으로 견주는 것을 보았다). 뒤의 작업으로 넘기는 일은 없다.
