# 토큰 사용 명세의 프로브

`.scratch/token-usage/spec.md`가 정한 값(큰 결과 알림의 문턱, 인계의 단계 경계)과 ADR 0033 이력 2026-10-16이 든 수를 낸다.
ADR 0033 본문의 수는 `.scratch/harness/probes/token_usage/`가 냈다.

| 프로브 | 무엇을 재나 | 근거로 드는 곳 | 다시 돌 때 |
|---|---|---|---|
| `measure.py results <시간>` | 이 저장소의 Read·Bash·PowerShell 결과 글자 수 분포와, 범위 없이 받은 결과가 문턱(1만~4만 자)을 넘은 수·글자의 몫·기록 항목 무게의 몫 | 명세 "큰 결과 알림 훅" | 저장소 루트에서 `PYTHONUTF8=1 uv run python .scratch/token-usage/probes/measure.py results 168`. 이 PC의 `~/.claude/projects/`(폴더 이름 `C--project-agent`로 시작) |
| `handoff_reach.py <밖 폴더> <주 체크아웃>` | 문턱을 낮춘 인계 훅 사본의 additionalContext 가 `claude -p` 모델에게 닿는지(A, 대조군 B), 기본 권한 모드의 워크트리 세션이 주 체크아웃과 자기 체크아웃의 스킬 파일을 Read 할 때 거부되는지(C, 양성 대조 D). 탐침 훅이 실제 입력을 남긴다 | `tools/hook_handoff.py` 독스트링(`skill_for`), `tools/hook_payloads.toml` 의 인계 훅 사례, 일지 2026-10-16-63 | 워크트리 루트에서 `uv run python .scratch/token-usage/probes/handoff_reach.py <저장소 밖 폴더> <주 체크아웃>`. `claude` CLI 와 인증, sonnet 세션 넷 |
| `handoff_time.py` | 인계 훅 둘의 한 번 시간을 등록 모양으로, 약 32MB 트랜스크립트에서 갈래 넷 다섯 번씩 | `.claude/rules/tools.md` 의 훅 시간 문단 | 저장소 루트에서 `uv run python .scratch/token-usage/probes/handoff_time.py` |
| `handoff_hook_mutations.toml` | 인계 훅 둘의 경계 판정·문턱·셈·표지와 `hook_pr_next_session` 문장을 바꾸면 시험이 빨개지는지 | 티켓 05 | `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/token-usage/probes/handoff_hook_mutations.toml` |
| `git_priority_load.py [회차] [모듈]` | 보통 우선순위의 CPU 소모 프로세스를 논리 CPU의 두 배 띄운 채, `main_checkout()`의 git 한 번이 보통·BELOW_NORMAL(작업 스케줄러 `Priority` 7)에서 걸리는 시간과, BELOW_NORMAL로 내려간 자식에서 `<모듈>.main_checkout()`이 성공하는지. 작업 아래의 손자가 BELOW_NORMAL을 물려받는지(`inherit`)도 본다 | `tools/token_report.py`의 `main_checkout_of` 독스트링, 일지 2026-10-19-24 | 저장소 루트에서 `uv run --no-project python .scratch/token-usage/probes/git_priority_load.py 5`. 고치기 전 판과 견주려면 `git show a60e2ddd:tools/token_report.py > tools/_old_token_report.py`로 꺼내 모듈 인자로 `tools._old_token_report`를 주고, 잰 뒤 지운다. 윈도에서만, 한 번에 수 분. 도는 동안 PC의 CPU가 꽉 찬다 |
| `token_report_mutations.toml` | `tools/token_report.py`의 겹침 거르기, 응답 ID의 주인 고르기, 증분, 계정 고르기, 보관의 링크, 잘린 줄, synthetic(티켓 02)과, 세션 행의 칸(큰 결과의 문턱과 대상, 큰 결과 알림 훅과 같은 판정, 다시 읽기, 인계, 시작 구성, PR), 지표 7~12, 경보 둘, 주간·4주 보고서(티켓 03)를 하나씩 깨면 시험이 빨개지는지 | 일지 2026-10-16-51, 2026-10-16-69 | 저장소 루트에서 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/token-usage/probes/token_report_mutations.toml` |
| `session_start_payload/run.sh <저장소 밖 디렉터리>`, `dump_session_start.py`, `start.jsonl`, `start_marker.jsonl` | SessionStart 훅이 받는 페이로드와 환경의 세션 표지 변수, `~/.claude.json` 의 계정 두 키가 있는지와 환경의 계정 변수가 그 값과 같은지(참거짓만). 갈래는 데스크톱 세션 안에서 띄운 `claude -p` 와 터미널의 대화형 `claude` 다. `start.jsonl` 이 저장한 원본이다. `start_marker.jsonl` 은 카나리아의 헤드리스 표지 `AGENT_OS_HEADLESS=1` 을 앞에 준 헤드리스 갈래의 원본이다 | `tools/hook_session_usage.py` 독스트링의 헤드리스 세션, 티켓 04 의 "이 티켓이 정할 것" 1 | 저장소 루트에서 `sh .scratch/token-usage/probes/session_start_payload/run.sh <저장소 밖 디렉터리의 절대 경로>`. 그 폴더는 비었거나 이 프로브의 표지 파일이 있어야 한다(아니면 2). 헤드리스 갈래는 haiku 호출 하나를 쓰고 `check_start.py` 가 그 줄의 표지를 단언한다(아니면 1). 대화형 갈래는 스크립트가 찍은 명령을 터미널의 저장소 루트에서 띄우고 시작 화면이 뜨면 프롬프트 없이 끈 뒤, 찍힌 확인 명령을 친다 |
| `session_start_payload/cli_attended.py <claude.exe>` | Claude Code 실행 파일에서 훅 환경의 `CLAUDE_CODE_SESSION_ATTENDED` 를 정하는 코드(자식 환경 함수, 그 판정 함수, 훅 명령을 띄우는 자리)의 세 표지 | 위와 같다 | 저장소 루트에서 `uv run python .scratch/token-usage/probes/session_start_payload/cli_attended.py <claude.exe>`. 데스크톱 앱의 CLI 는 그 세션의 `CLAUDE_CODE_EXECPATH` 다 |
| `session_usage_hook_mutations.toml` | `tools/hook_session_usage.py`(티켓 04)의 표지 판정(보고서 날짜, `O_EXCL`, 36시간 경계, 지역 날짜), 헤드리스·출처 판정, 계정 고르기, 다시 읽기, 출력 폴더와 러너의 헤드리스 변수 벗기기를 하나씩 깨면 시험이 빨개지는지 | 티켓 04 일지 | 저장소 루트에서 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/token-usage/probes/session_usage_hook_mutations.toml` |
| `session_usage_time.py` | 세션 시작 훅 한 번의 시간(등록 모양, 래퍼를 거친다). 이어 하기, 새 요약 뒤의 시작, 같은 요약의 둘째 시작, 읽지 못한 `.claude.json` 의 넷 | `.claude/rules/tools.md` 의 훅 시간 문단 | 저장소 루트에서 `uv run python .scratch/token-usage/probes/session_usage_time.py` |
| `measure.py boundaries <시간>` | 메인 세션 컨텍스트가 20만을 넘은 뒤 처음 오는 경계의 종류, 그 지점의 세션 컨텍스트, 그 뒤 환산 비용. ADR 0033의 경계(커밋, PR 열기)와 셀프 리뷰 시작을 더한 경계를 견준다 | 명세 Problem Statement와 "인계 훅", ADR 0033 이력 2026-10-16 | 같은 자리에서 `... measure.py boundaries 168`. 단가표는 `.scratch/harness/probes/session_cost/costs.py` |

| `large_result/run.py`, `large_result/payloads.jsonl` | PostToolUse 훅이 Read·Bash·PowerShell에서 받는 `tool_response`의 모양과, `hook_large_result`의 `result_chars`가 그 출력에서 셈한 글자 수가 같은 호출의 기록 `tool_result` 본문 길이와 맞는지(티켓 06). `run`이 저장소 밖에 픽스처(1200줄 파일, 한글 파일, 1×1 그림)를 짓고 탐침 훅(`dump_posttool.py`, 페이로드 그대로)만 붙인 `claude -p`(haiku)에 여덟 호출을 차례로 시킨 뒤, 페이로드마다 기록의 본문 길이·앞뒤 200자·그림 블록 여부를 붙여 `payloads.jsonl`에 쓴다(`--save`면 이 디렉터리로). `judge`는 여덟 호출이 한 번씩 기록과 함께 있을 때 측정으로 보고, 셈이 기록과 다르면 기대한 차이(`EXPECT_DIFF`) 밖일 때 1로 끝난다 | `tools/hook_large_result.py` 독스트링의 크기 셈, 파일로 옮겨진 출력, stderr 이음새. `tests/tools/test_hook_large_result.py`의 저장한 페이로드 시험 둘. `tools/hook_payloads.toml`의 결과 객체 모양 | 저장소 루트에서 `uv run python .scratch/token-usage/probes/large_result/run.py run <저장소 밖 디렉터리> [--save]`(haiku 세션 하나), 다시 판정만 하면 `... run.py judge`. 2026-10-16(claude 2.1.300) 결과: Read의 `tool_response` 키는 `type`·`file`이고 `file.content`에 줄마다 `<줄 번호>\t`를 붙인 길이가 기록과 같았다(범위 없는 1200줄 46991자, 끝 줄바꿈 뒤의 빈 1201번 줄까지. 범위 준 50줄 2049자, 한글 425자). 그림은 `type`이 `image`이고 기록 본문은 그림 블록뿐이라 0자였다. Bash의 키는 `stdout`·`stderr`·`interrupted`·`isImage`·`noOutputExpected`이고 `stdout`이 기록과 같았다(`seq 1 2000` 8892자, 끝 줄바꿈 없음). stderr로 쓴 줄도 `stdout`에 합쳐 왔고 `stderr`는 비었다(17자). `seq 1 8000`(38893자)은 `persistedOutputPath`·`persistedOutputSize`(38893)가 붙고 `stdout`은 앞 30000자로 잘렸으며, 기록 본문은 `<persisted-output>`으로 싼 경로와 미리보기 2323자였다. PowerShell 키는 `isImage`까지 넷이고 `stdout`이 기록과 같았다(CRLF 줄, 28891자). 판정 0, 기대한 차이는 파일로 옮겨진 것 하나다 |
| `large_result/notice.py` | `hook_large_result`의 알림이 실제 세션의 모델에게 닿는지. B는 등록 모양의 실제 훅과 탐침 훅을 붙여 46991자 Read 뒤 훅 알림의 첫 문장을 묻고, C는 425자 Read의 대조군이다. 탐침 기록이 지시한 범위 없는 Read 하나일 때 측정이고, 모델의 답으로 판정한다(stream-json에는 훅의 additionalContext가 실리지 않는다, `.scratch/harness/probes/webfetch_payload/`) | `tools/hook_large_result.py`의 `LEAD`, `.claude/rules/tools.md`의 새 훅이 함께 하는 넷 | `uv run python .scratch/token-usage/probes/large_result/notice.py <저장소 밖 디렉터리>`(haiku 세션 둘, `--judge`는 다시 판정만). 2026-10-16(claude 2.1.300) 결과: B의 답은 훅의 첫 문장을 옮겼고, C의 답은 "알림 없음"이었다 |
| `large_result/time_hook.sh` | 훅 한 번의 시간을 등록 모양(래퍼를 거쳐)으로 짧은 Bash(침묵), 1만 자 넘는 Bash(알림), 2만 자 넘는 Read(알림)에 일곱 번씩 잰다. 기대와 다르면 1로 끝난다 | `.claude/rules/tools.md` 시간 문단의 `hook_large_result` 문장 | `sh .scratch/token-usage/probes/large_result/time_hook.sh`(`.venv`가 있어야 한다). 2026-10-16 결과(이 PC, 워크트리): 스물하나 모두 기대대로였고 Bash 침묵 352~1034ms, Bash 알림 334~1064ms, Read 알림 329~752ms, 열일곱은 501ms 이하였다. 바로 뒤 `.scratch/harness/probes/grep_omitted/time_hook.sh`도 381~864ms로 그 행의 기록(258~523ms)보다 느렸다. 다른 세션이 여럿 돌던 때다 |
| `large_result_hook_mutations.toml` | `tools/hook_large_result.py`의 문턱(이상으로 바꾸기, 두 값 올리기, Read에 셸 문턱), 범위 판정(offset·limit 하나씩 빼기, 없애기), 셈(줄 번호 접두, startLine, 끝 줄바꿈 뒤의 빈 줄, 파일로 옮겨진 출력, 그림 셸 출력, stderr, 글이 아닌 Read)과 settings.json 매처를 하나씩 깬 변이 열다섯과 대조군 하나(알림 문구의 "약"은 시험이 재지 않는다) | `tests/tools/test_hook_large_result.py`가 무엇을 재는지 | 저장소 루트에서 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/token-usage/probes/large_result_hook_mutations.toml`. 2026-10-16 결과: 열여섯 모두 기대대로였다 |
| `handoff_cost.py [--projects <폴더>] [--repo <폴더 이름 머리>]` | 실제 인계 쌍(넘긴 세션 P, 이어받은 세션 H)마다 (가) H의 호출 수와 30번째·최대 세션 컨텍스트가 인계 시점 값의 몇 배인지, (나) P가 마지막 압축 뒤 인계 시점 전에 읽은 파일을 H가 그 사이 바뀐 것 없이 다시 읽은 횟수와 글자, (다) 인계하지 않았다면의 어림(H 호출 수 × 인계 시점 세션 컨텍스트 × P 모델의 캐시 읽기 단가)과 실제(H가 이미 있던 몫을 읽고 쓴 비용 + P가 인계 시점 뒤 H의 끝까지 쓴 비용). 쌍은 첫 프롬프트의 `이어받을 상태: 인계:` 줄로 알아보고, 인계 시점은 P의 인계 훅 첨부(`hook_additional_context`의 문턱 문장)로 정한다. P를 정하지 못했거나(H의 지시문에 일지 경로나 브랜치가 없거나, 그 일지를 Write·Edit로 쓴 같은 브랜치의 메인 세션이 기록에 없다. 일지를 Bash로만 쓴 세션은 P로 보지 않는다), 그 첨부나 첨부가 가리킨 응답이 없거나, 인계 시점의 세션 컨텍스트가 인계 문턱 20만 이하이거나, `gh`로 PR 상태를 읽지 못한 쌍은 표지 없는 쌍으로 따로 적고 1로 끝난다. H의 일이 끝나지 않은 쌍(H가 다시 넘기지 않았고 병합되거나 닫힌 PR이 없다)은 재지 않고 수만 적는다. (나)를 재지 못한 쌍과 셈에 드는 호출에 단가표 밖 모델이 있는 쌍은 (다)를 재지 않고 따로 세며 1로 끝난다. 인계 쌍이 하나도 없어도 1이다 | 티켓 09 "인계의 비용" | 워크트리나 저장소 루트에서 `uv run python .scratch/token-usage/probes/handoff_cost.py`. 이 PC의 `~/.claude/projects/`(폴더 이름이 주 체크아웃의 이름으로 시작). PR 상태는 `gh`로 본다 |
| `skill_listing_entries.py <기록.jsonl> --cwd <폴더>` | 세션 기록에서 첫 모델 호출 전 `skill_listing` 첨부(모델에게 간 스킬 목록)의 출처별 글자 수, 본문 항목 수와 첨부의 `names` 수, 설명이 남은 항목과 이름만 남은 항목, `anthropic-skills`·`slack`·`cowork-plugin-management` 항목, 대조로 `jira-*` 항목, 첫 모델 호출 뒤에 다시 온 첨부의 시각·글자 수·`names` 수. 첨부가 있고 첨부마다 `names` 목록이 있고 기록의 첫 `cwd`가 `--cwd`와 같고 남기는 `anthropic-skills:built-in-browser`가 목록에 있을 때만 측정이고, 아니면 1로 끝난다 | ADR 0033 이력 2026-10-20 | 저장소 루트에서 `uv run python .scratch/token-usage/probes/skill_listing_entries.py <기록> --cwd <세션의 작업 폴더>`. 모델을 부르지 않는다. 2026-10-20(claude 2.1.299) 주 체크아웃에서 시작한 앱 세션 `1d37e692`: 첫 목록 26,462자, 항목 72개, `anthropic-skills` 10,211자 17개, 프로젝트·사용자·내장 9,904자, `slack` 3,712자 13개, `claude-security` 999자, `cowork-plugin-management` 725자 2개, `coderabbit` 468자, `frontend-design` 240자, `claude-hud` 203자, `jira-*` 0개. 설정을 바꾼 워크트리에서 사용자가 연 앱 세션 `5682dc15`(claude 2.1.299. 측정용으로 `grilling` off, `frontend-design@claude-plugins-official` false, `skillListingBudgetFraction` 0.003을 잠시 더했다): 첫 목록 8,676자, 항목 57개(`names` 57개). `slack`·`frontend-design`·`grilling`·`jira-*`는 0개였고, `cowork-plugin-management` 2개와 `anthropic-skills` 17개는 그대로 있었다. 끄는 키를 목록의 이름 그대로 적었는데 동기화된 스킬과 플러그인에는 먹지 않았다. 예산 0.003에서 설명을 지킨 것은 19개(프로젝트 `code-review`·`next-session`·`open-session`·`tidy-checkouts`, 내장 `security-review`, 아래 `skill_listing_budget.py` 행의 내장 열넷)이고 38개는 이름만 남았다(`retro`·`writing-for-agents`·`diagnosing-bugs`·`tdd`·`git-*`·플러그인 스킬·`anthropic-skills:*` 전부). `1d37e692`는 이름만 남은 항목이 0개였고, 첫 목록 뒤에 첨부가 셋 더 있었다(02:39 UTC 26,461자 `names` 72개, 03:02 22,749자 59개, 03:47 22,749자 59개). 그 셋은 설정을 바꾼 세션 안의 목록이라 근거로 쓰지 않는다. 03:02의 본문에 `slack:` 줄이 없는 것은 손으로 봤다. 위의 수 가운데 `names`, 설명·이름만, 뒤의 첨부는 2026-10-20 셀프 리뷰가 그것을 세게 고친 판으로 두 기록을 다시 읽어 냈고, 앞의 수는 고치기 전과 같았다 |
| `skill_listing_cli.py [--settings <파일>] [--out <폴더>]` | `skillOverrides`가 동기화된 스킬(`anthropic-skills:*`)을 CLI 세션의 첫 목록에서 빼는지. 저장소 밖 임시 폴더에서 설정이 없는 A와 `skillOverrides`만 둔 B를 `claude -p`(haiku, 설정 출처 `project,local`)로 한 턴씩 띄우고, 그 세션 기록을 위 프로브의 함수로 읽는다. B의 값은 `--settings` 파일의 것이고, 주지 않으면 측정 때 프로젝트 설정에 있던 끄는 키 열여섯(`MEASURED_OFF`)이다. 끄는 `anthropic-skills:*` 키가 없거나, A에 `anthropic-skills:*`가 없거나, A나 B에 `built-in-browser`가 없으면 측정이 아니다 | ADR 0033 이력 2026-10-20 | 저장소 루트에서 `uv run python .scratch/token-usage/probes/skill_listing_cli.py`. 갈래마다 haiku 호출 하나다. 2026-10-20(claude 2.1.302): A와 B 모두 `anthropic-skills:*` 0개라 측정이 아니었다(1로 끝났다). 설정 출처가 `project,local`인 CLI 세션에는 동기화된 스킬이 실리지 않았고, `user`를 넣으면 실리는지는 재지 않았다. `user`를 넣는 갈래는 사용자 설정 Stop 훅의 Slack 알림 때문에 두지 않았다. 처음 판은 끄는 키를 프로젝트 설정에서 읽었고, 그 키를 뺀 뒤 기본값을 `MEASURED_OFF`로 고친 판으로 2026-10-20(claude 2.1.302) 다시 돌려 같은 결과였다(끈 16개, A와 B 모두 0개, 측정이 아닌 것 1) |
| `skill_listing_budget.py [--skills <폴더>] [--out <폴더>]` | `skillListingBudgetFraction`을 낮추면 첫 스킬 목록에서 어느 항목의 설명이 먼저 줄거나 빠지는지. 저장소 밖 임시 폴더마다 이 저장소의 `.claude/skills`를 복사하고 비율만 둔 설정(0.05 대조, 설정 없음, 0.005, 0.0025, 0.001)으로 `claude -p`(haiku, 설정 출처 `project,local`)를 한 턴씩 띄운 뒤, 항목마다 대조와 견줘 줄었다·이름만·본문에 없다·아예 없다로 가른다. 대조 본문에 `diagnosing-bugs`가 설명과 함께 없거나, 대조보다 짧은 갈래가 하나도 없으면 측정이 아니다 | ADR 0033 이력 2026-10-20의 고르지 않은 안 "스킬 목록 예산을 낮춘다" | 저장소 루트에서 `uv run python .scratch/token-usage/probes/skill_listing_budget.py`. 갈래마다 haiku 호출 하나다. 2026-10-20(claude 2.1.302): 대조 8,822자 27개. 설정 없음과 0.005는 대조와 같았다. 0.0025는 7,361자로 11개(`diagnosing-bugs`·`domain-modeling`·`grill-with-docs`·`grilling`·`open-session`·`retro`·`tdd`·`tidy-checkouts`·`writing-for-agents`·`init`·`security-review`), 0.001은 6,811자로 13개(앞의 것과 `code-review`·`next-session`)가 이름만 남았다. 잘린 설명과 사라진 이름은 없었다. 0.0025에서 남은 프로젝트 스킬 둘은 그날 이 PC의 `~/.claude.json` `skillUsage` 횟수로 1·2위였다(`next-session` 354, `code-review` 294. 이름과 횟수만 손으로 찍었다. 횟수는 그날의 값이다). 측정이 아닌 것 0 |
| `skill_listing_deny.py [--skills <폴더>] [--out <폴더>]` | `permissions.deny`의 `Skill(이름)` 규칙이 첫 스킬 목록에서 그 항목을 빼는지. 저장소 밖 임시 폴더마다 이 저장소의 `.claude/skills`를 복사하고, 설정 없는 A와 `Skill(grilling)`·`Skill(retro)`을 거부한 B를 `claude -p`(haiku, 설정 출처 `project,local`)로 한 턴씩 띄워 두 대상과 대조 `code-review`를 가른다. C는 B와 같은 설정에서 `grilling`을 부르게 해 도구 결과가 `blocked by permission rules` 오류인지 본다. A에 대상이 설명과 함께 없거나, B에 `code-review`가 설명과 함께 없거나, C에 거부 문구가 없으면 측정이 아니다 | ADR 0033 이력 2026-10-20의 "권한 거부 규칙도 목록에서 빼지 못한다" | 저장소 루트에서 `uv run python .scratch/token-usage/probes/skill_listing_deny.py`. haiku 호출 셋이다. 2026-10-20(claude 2.1.302): A와 B 모두 본문 8,822자, `names` 27개이고 세 항목이 모두 설명과 함께 그대로였다. C의 `grilling` 호출은 거부 문구를 단 오류로 막혔다. 측정이 아닌 것 0 |

표지, 판정의 정의(훅보다 넓은 커밋 판정 포함), 못 보는 것은 `measure.py` 독스트링이 원천이다.

## 결과 (2026-10-16 17:14 UTC, 이 PC, 창 168시간)

두 하위 명령 모두 표지를 지나 0으로 끝났다. 같은 날 16:38 UTC에 돌린 첫 판은 셀프 리뷰를 이름의 끝(`code-review`)으로
갈랐고 불리언 인자가 있었다. 명세의 셀프 리뷰를 반영해 판정을 인계 훅의 것과 맞춘 판이 아래다. 그 뒤 PR 직전 버그 리뷰를
반영해 줄바꿈 없이 잘린 마지막 줄을 넘기게 고쳤다. 아래 실행은 그 전 판이 예외 없이 끝난 것이라 그런 줄이 없었고, 수는
같다.

**results 168**: 메인 세션 876개, 서브에이전트 399개. 범위(`offset`·`limit`)를 주지 않은 결과만 문턱과 견줬다. 무게의 분모는
기록에 남은 항목이다(독스트링).

| 도구(메인 세션) | 결과 | 중앙값 | 99% | 문턱 | 넘은 결과 | 그 도구 글자의 몫 | 기록 항목 무게의 몫 |
|---|--:|--:|--:|--:|--:|--:|--:|
| Read | 3,771(범위 준 것 1,719) | 2,933자 | 43,529자 | 1만 | 483 | 50.4% | 5.43% |
| Read | | | | 2만 | 275 | 38.5% | 3.43% |
| Read | | | | 3만 | 150 | 26.1% | 1.70% |
| Bash | 15,893 | 175자 | 10,053자 | 1만 | 164 | 15.8% | 3.10% |
| Bash | | | | 2만 | 10 | 1.6% | 0.42% |
| PowerShell | 363 | 100자 | 2,533자 | 1만 | 1 | 12.8% | 0.03% |

메인 세션에서는 넘은 결과의 수와 세션·대상 쌍의 수가 모든 문턱에서 같았다. 같은 세션에서 같은 대상(파일, 명령)이 문턱을
두 번 넘은 일이 없었다. 서브에이전트에서는 1만 자 Read에서 한 번 있었다. 서브에이전트는 Read 2만 자를 넘은 것이 161개, Bash
1만 자를 넘은 것이 402개였다. Bash 결과의 최대는 메인 세션 24,463자, 서브에이전트 29,581자였다.

**boundaries 168**: 창 안에서 시작한 메인 세션 793개, 모델 호출 22,481회, 환산 비용 $2,886.72(단가표 밖 0회). 20만을 넘지 않은
세션 708개, 40만을 넘은 세션 75개. 20만을 넘은 세션은 85개다.

| 규칙 | 20만을 넘은 뒤 처음 온 것 | 세션 | 그 뒤 비용 |
|---|---|--:|--:|
| ADR 0033(커밋, PR 열기) | 커밋(PR을 열기 전) | 78 | $1,468.01 |
| ADR 0033(커밋, PR 열기) | 경계 없음 | 7 | $52.09 |
| 셀프 리뷰 시작을 더함 | 셀프 리뷰 시작 | 66 | $1,612.16 |
| 셀프 리뷰 시작을 더함 | 커밋(PR을 열기 전) | 13 | $243.36 |
| 셀프 리뷰 시작을 더함 | 경계 없음 | 6 | $39.34 |

| 규칙 | 문턱에서 그 경계까지 호출 중앙값 | 그 사이 40만을 넘은 세션 | 그 경계의 세션 컨텍스트 중앙값 |
|---|--:|--:|--:|
| ADR 0033(커밋, PR 열기) | 98 | 49 | 418,970 |
| 셀프 리뷰 시작을 더함 | 55 | 21 | 327,338 |

모든 경계(20만을 넘었는지와 상관없이)에서 잰 세션 컨텍스트 중앙값은 PR을 열기 전 커밋(216개) 477,328, 그 세션이 PR을 연 뒤의
커밋(194개) 584,724, PR 열기(78개) 524,999, 셀프 리뷰 시작(101개) 297,143이었다. 모음이 서로 달라 한 세션 안에서 얼마나
늘었는지는 이 수로 말할 수 없다.

"그 사이 40만을 넘은 세션"은 지금의 기록(자동 압축 약 96.7만)에서 세션 컨텍스트가 40만을 넘은 것이다. 자동 압축 창을 40만으로
두면 그 세션은 경계보다 압축이 먼저 온다(어림. 압축 뒤의 경로는 재지 않았다). "그 뒤 비용"은 인계했다면 새 세션이 맡았을
몫이고, 새 세션에서 얼마가 될지는 재지 않았다.

## 결과: SessionStart 페이로드와 헤드리스 표지 (2026-10-16, 이 PC, 티켓 04)

`session_start_payload/run.sh` 의 두 갈래가 `start.jsonl` 에 한 줄씩 남겼다. 헤드리스 갈래는 데스크톱 세션(앱의 CLI 2.1.295)의
Bash 에서 띄운 `claude -p`(PATH 의 2.1.300)이고, 대화형 갈래는 터미널 패널의 PowerShell 에서 워크트리 폴더로 띄운 `claude`
(2.1.300)다. 두 줄 모두 `hook_event_name` 이 `SessionStart`, `source` 가 `startup` 이라 재려는 상황(시작의 훅)이 났다.

| | 헤드리스 | 대화형 | 이 데스크톱 세션의 셸(Bash 도구) |
|---|---|---|---|
| 페이로드의 키 | `session_id`, `transcript_path`, `cwd`, `scratchpad_dir`, `hook_event_name`, `source` | 왼쪽과 같고 `model` 이 더 있다 | (재지 않았다) |
| `CLAUDE_CODE_SESSION_ATTENDED` | `0` | `1` | `1` |
| `CLAUDE_CODE_ENTRYPOINT` | `claude-desktop`(부모에게서 물려받았다) | `cli` | `claude-desktop` |
| `CLAUDE_CODE_CHILD_SESSION` | `1` | `1` | `1` |
| `~/.claude.json` 의 계정 두 키 | 있다 | 있다 | |
| 환경의 `CLAUDE_CODE_ACCOUNT_UUID`·`CLAUDE_CODE_USER_EMAIL` | 있고 파일의 두 값과 같다 | 없다 | |

셋째 열은 `start.jsonl` 밖이다. 이 세션의 Bash 에서 `printenv <이름>` 으로 이름마다 손으로 봤다. 페이로드에는 대화형을 가를
칸이 없다. `model` 은 헤드리스에 없었지만 데스크톱 세션(앱이 SDK 로 띄운다)의 페이로드는 재지 못해 그 칸으로 가르지 않았다.
`CLAUDE_CODE_CHILD_SESSION` 은 훅 자신의 환경이라 언제나 `1` 이다(아래 표지 1).

`cli_attended.py` 는 2.1.295 와 2.1.300 에서 실행 파일의 판 줄과 표지 다섯을 모두 찾아 0으로 끝났다. 첫 판은 표지 셋(1~3)만
봤고, 셀프 리뷰가 셸 도구 자리와 판정이 읽는 두 값의 출처는 프로브 밖에서 grep 으로만 봤다고 짚어 표지 4·5 와 판 줄을 더했다.
자식 환경 함수는 `CLAUDE_CODE_SESSION_ATTENDED` 를 판정 함수의 참거짓으로 `"1"`·`"0"` 으로 두고, 훅 명령을 띄우는 자리와
셸 도구가 명령을 띄우는 자리가 모두 그 함수를 펼친다. 대화형 여부는 시작 인자로, 자식 세션 여부는 시작할 때의 환경
`CLAUDE_CODE_CHILD_SESSION` 으로 정한다(표지 5). 판정 함수는 `CLAUDE_CODE_SESSION_KIND` 가 `bg`·`daemon`·`daemon-worker` 이거나
축약된 이름의 함수 하나(2.1.295 의 `eb()`, 2.1.300 의 `L_()`. 무엇인지는 읽지 못했다)가 값을 내면 거짓, 대화형이면
참, 아니면 시작할 때 `CLAUDE_CODE_CHILD_SESSION` 이 없었고 진입점이 목록(`claude-vscode`, `claude-desktop`,
`claude-desktop-3p`, `local-agent`, `local_agent`, `remote`, `remote_desktop`, `remote_mobile`, `remote_projects`,
`remote_cowork`, `ssh-remote`, `claude-in-slack`, `claude_in_slack`, `claude-in-teams`, `claude-coworker`,
`claude-coworker-terminal`)에 있을 때 참이다.

해석: 헤드리스 갈래는 부모 세션의 `CLAUDE_CODE_CHILD_SESSION` 을 물려받아 자식 세션이라 `0` 이고, 대화형 갈래는 대화형이라
`1` 이다. 두 갈래가 판정 함수의 셈과 맞는 것이 양성 대조다. 데스크톱 세션의 훅이 받는 값은 훅으로 재지 않았다. 그 세션은
자식 세션이 아니고 진입점이 `claude-desktop` 이라 셈으로는 `1` 이고, 같은 세션의 셸이 `1` 을 받았다. "훅은 셸과 다른 환경을
받는다"는 다른 해석은 표지 3·4(훅 명령과 셸 도구의 환경을 같은 함수로 짓는다)가 가른다. 실제 데스크톱 세션에서 요약이 보이는지는 티켓
09 가 첫 일간 보고서 뒤에 본다.

셀프 리뷰의 명세 축이 이 내부 값만으로 가르는 것을 명세가 정한 길(카나리아의 표지 변수)을 승인 없이 바꾼 것으로 짚었고,
사용자가 둘 다 쓰는 길을 골랐다(일지 2026-10-16-66). 그래서 `tools/canary.py` 가 띄우는 세션의 환경에 `AGENT_OS_HEADLESS=1` 을
붙인다. 그 변수가 `claude -p` 세션의 훅까지 전해지는지는 같은 `run.sh` 를 `AGENT_OS_HEADLESS=1 sh …/run.sh <디렉터리>` 로 돌려
봤다(`start_marker.jsonl`). 탐침 훅의 `env_values` 에 `AGENT_OS_HEADLESS` 가 `1` 로 들었고 `CLAUDE_CODE_SESSION_ATTENDED` 는 `0`
이었다. 대화형 갈래는 다시 돌리지 않았다.

## 결과: 실제 인계의 비용 (2026-10-17 00:40 지역, 이 PC, 티켓 09)

`handoff_cost.py`는 1로 끝났다. 인계 쌍 넷 가운데 표지 없는 쌍이 하나, 잰 쌍이 셋이다. PR 상태를 읽지 못한 쌍과 끝나지
않은 쌍은 없다. 셀프 리뷰를 반영한 판(시각으로 견주는 P의 변경, H 자신의 두 번째 읽기 빼기, 번호 줄 없는 결과는 측정 불가)으로
다시 돌려도 수가 같았다.

| 쌍(P → H) | 경계 | 인계 시점 세션 컨텍스트 | (가) H 호출 · 30번째(비) · 최대(비) | (나) 다시 읽기 | (다) 어림 · 실제 · 차 |
|---|---|--:|---|---|---|
| 5c0106b4 → 31425665(`chore/precommit-xdist-runner`, 창 적용 전) | 커밋 뒤 | 426,586 | 88 · 191,083(0.448) · 345,911(0.811) | 1회 9,961자(H의 Read 83,639자의 11.9%) | $7.51 · $4.15 · $3.36 |
| 31425665 → 820d124c(같은 브랜치, 창 적용 전, 일지 경로를 `이어받을 상태` 줄 밖에서 찾음) | PR 연 뒤 | 312,342 | 105 · 208,187(0.667) · 359,768(1.152) | 0회(H의 Read 115,910자) | $6.56 · $4.56 · $2.00 |
| 717679b8 → 73167c0e(`feature/08-apply-outside-settings`) | 셀프 리뷰 직전 | 표지 없음 | | | |
| 73167c0e → 402aedd6(같은 브랜치) | 커밋 뒤 | 208,649 | 86 · 153,318(0.735) · 261,027(1.251) | 1회 2,769자(H의 Read 8,442자의 32.8%) | $3.59 · $3.29 · $0.30 |

- 표지 없는 쌍은 앞 세션의 기록 파일이 2026-10-16T12:16:43Z에 앱에서 지워졌다(`<id>.desktop-released.json`, `reason: delete`).
  그 인계에서 새 세션은 잠금에 막혀 사용자가 앞 세션을 멈춘 뒤 들어갔고(일지 2026-10-16-71, 대기열 326), 지운 것은 새 세션이
  열리고 26분 뒤다. 지운 까닭은 기록에 없다. 일지 71은 그 인계 시점을 218,302로 적었다.
- 인계 시점의 값은 세 쌍 모두 훅 문장에 든 값과 같았다.
- 30번째 호출 비의 중앙값은 0.667, 차의 중앙값은 $2.00이다. 둘 다 쌍이 다섯(`MIN_PAIRS`)보다 적어 판정하지 않았다.
- 실제 비용의 구성: H 첫 호출의 세션 컨텍스트가 91,874~91,975로 ADR 0033이 가정한 시작 3만의 약 세 배였다. P가 인계
  시점 뒤에 쓴 호출(17·22·19회, $1.97·$1.98·$1.32)이 실제의 40~48%를 차지했다. 이 몫에는 계속했어도 썼을 일지 쓰기가
  들어 실제를 높게 잡는다(독스트링의 쏠림). 셋째 쌍의 차가 작은 것은 어림이 인계 시점의 값(208,649, 문턱 바로 위)에
  비례하기 때문으로 어림한다.
- 앞의 두 쌍은 자동 압축 창을 40만으로 두기(11:41Z) 전에 열려, 어림이 가정한 "계속했다면"의 길이 지금과 다르다.

## 결과: 실제 인계의 비용, 잰 쌍 다섯 (2026-10-17 15:00 지역, 이 PC, 티켓 09)

같은 판(커밋 `aa93cf7b`)을 다시 돌렸다. `handoff_cost.py`는 1로 끝났다. 인계 쌍 여섯 가운데 표지 없는 쌍이 하나(위 절과 같은
717679b8 → 73167c0e), 잰 쌍이 다섯이다. PR 상태를 읽지 못한 쌍, 끝나지 않은 쌍, (나)를 재지 못한 쌍, 단가표 밖 쌍은 없다.
위 절의 세 쌍은 값이 같았고, 아래 두 쌍이 새로 끝났다.

| 쌍(P → H) | 경계 | 인계 시점 세션 컨텍스트 | (가) H 호출 · 30번째(비) · 최대(비) | (나) 다시 읽기 | (다) 어림 · 실제 · 차 |
|---|---|--:|---|---|---|
| 3f37b873 → 10c30451(`feature/09-human-verification`) | 커밋 뒤 | 275,465 | 101 · 132,721(0.482) · 310,619(1.128) | 0회(H의 Read 71,768자) | $5.56 · $6.53 · −$0.97 |
| 10c30451 → d70ff8fd(같은 브랜치) | PR 연 뒤 | 268,193 | 81 · 167,330(0.624) · 267,902(0.999) | 1회 2,769자(H의 Read 55,753자의 5.0%) | $4.34 · $3.25 · $1.10 |

- 다섯 쌍의 판정(쌍 다섯이 `MIN_PAIRS`에 닿았다): (가) 30번째 호출 비의 중앙값 0.624, 최대 0.735로 알리는 기준(중앙값 0.5
  초과)에 걸렸다. (다) 차의 중앙값 $1.10, 최대 $3.36으로 멈추는 기준(중앙값 0 이하)에 걸리지 않았다.
- 셋마다 다섯 쌍의 중앙값과 최대(위 판정 밖의 것): (가) 최대 호출 비는 중앙값 1.128, 최대 1.251이다. (나)는 횟수 중앙값 1회,
  최대 1회이고, 글자 중앙값 2,769자, 최대 9,961자다.
- 다섯 쌍 가운데 둘(H 31425665, 820d124c)은 자동 압축 창을 적용하기 전에 열렸다(위 절의 마지막 항목, 출력의 "적용하기 전에 열렸다" 줄).
- 3f37b873은 인계 약 16분 전(15:53:03Z)에 세션 컨텍스트 367,136에서 자동 압축됐다(일지 2026-10-17-03 "적용 뒤 확인"). 위 행의
  인계 시점 값 275,465는 압축 뒤의 값이고, (나)는 독스트링대로 그 압축 뒤의 읽기만 센다. 그래서 그 쌍의 0회에는 압축 전에
  읽은 것이 처음부터 들지 않는다.
- H 첫 호출의 세션 컨텍스트는 다섯 쌍 모두 91,864~92,346이었고, 30번째 호출은 첫 호출보다 40,857~116,313 컸다. 프로브가 앞
  세션에 이미 있던 몫으로 더한 다시 읽기와 일지 읽기는 쌍마다 6,575~19,707토큰이었다(출력의 "이미 있던 몫" 줄. H 전체에서
  센 값이다). 그래서 30번째 호출 비의 중앙값이 0.5를 넘은 것은 다시 읽기보다 시작 몫과 그 뒤의 일에서 왔다고 어림한다. 그
  뒤의 일 가운데 새 일과 프로브가 가르지 못한 몫(독스트링 (다)의 마지막 항목)은 나누지 않았다.
- 작업 스케줄러가 만든 10/16 보고서 9절에서 사람이 연 메인 세션 37개의 첫 호출 중앙값이 95,850이고 헤드리스 세션 311개의
  중앙값이 18,645라, 인계 세션은 사람이 연 세션의 크기로 시작한다. ADR 0033이 머리 단락과 "근거"에 든 시작 3만은
  `.scratch/harness/probes/token_usage/`의 `simulate 72`가 메인 세션 522개로 낸 중앙값 30,002다. 그 명령(`measure.py`의
  `cmd_simulate`)은 이 PC의 `~/.claude/projects/` 전체에서 창(`simulate 72`면 지난 72시간) 안에 시작해 모델 호출이 둘 이상인
  세션을 서브에이전트 기록만 빼고 센다. 다른 프로젝트의 세션도 들고, 사람이 연 세션과 헤드리스 세션을 가르지 않는다(코드를
  읽었다).
- 차가 음수인 쌍(10c30451)은 P가 인계 시점 뒤에 21회 $4.24를 썼다. 실제의 65%다. P가 넘긴 뒤에 사람의 답과 자동 보안
  리뷰의 지적을 받아 H에게 전한 호출이 들었다(일지 2026-10-17-01 "이어받은 세션"). 다른 네 쌍의 그 몫은 실제의 40~48%였다.
- 새 두 쌍의 지시문은 모두 `이어받을 상태` 줄에 일지 경로가 있었다(대체 길을 쓴 쌍은 위 절의 820d124c 하나다).

## 결과: 여섯째 쌍 (2026-10-17 16:10 지역, 이 PC, 티켓 09)

위 절 뒤에 같은 판을 다시 돌렸다(PR 직전 버그 리뷰가 짚었다). 1로 끝났다. 위 다섯 쌍은 값이 같았고, 위 절을 쓴 세션
ec703311에서 넘겨받은 d4316239가 다시 넘겨 그 쌍이 끝났다. 끝나지 않은 쌍은 d4316239 → 63d8ff5f(이 절을 쓴 세션) 하나이고, 표지 없는 쌍이
하나 더(H 8d9be70c, `chore/handoff-notice-and-runbook-quotes`, 앞 세션을 정하지 못했다) 나왔다.

| 쌍(P → H) | 경계 | 인계 시점 세션 컨텍스트 | (가) H 호출 · 30번째(비) · 최대(비) | (나) 다시 읽기 | (다) 어림 · 실제 · 차 |
|---|---|--:|---|---|---|
| ec703311 → d4316239(`feature/09-human-verification-checks`) | 셀프 리뷰 직전 | 281,281 | 100 · 183,010(0.651) · 325,007(1.155) | 3회 13,163자(H의 Read 82,988자의 15.9%) | $5.63 · $4.14 · $1.49 |

- 여섯 쌍의 판정: (가) 30번째 호출 비의 중앙값 0.637, 최대 0.735로 알리는 기준에 걸렸다. (다) 차의 중앙값 $1.29, 최대
  $3.36으로 멈추는 기준에 걸리지 않았다. 다섯 쌍의 판정과 같다.
- (나)는 여섯 쌍에서 횟수 중앙값 1회, 최대 3회이고 글자 중앙값 2,769자, 최대 13,163자다. 이 쌍에서 가장 많이 다시 읽은
  파일은 앞 티켓 회차의 일지(2026-10-17-01, 7,863자)다. 이미 있던 몫은 19,186토큰으로 위 절의 범위(6,575~19,707) 안이다.
