# 2026-10-16 (57) 인계 훅 둘과 그것이 바꾸는 문장

token-usage 티켓 05(`.scratch/token-usage/issues/05-handoff-hooks-and-sentences.md`)를 구현했다. 브랜치
`feature/05-handoff-hooks-and-sentences`, 워크트리 `.claude/worktrees/05-handoff-hooks-and-sentences`.

## 시작

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/token-usage/issues/05-handoff-hooks-and-sentences.md
>
> 다음 작업: .scratch/token-usage/issues/05-handoff-hooks-and-sentences.md. 인계 훅 둘(hook_handoff, hook_handoff_notice)과 그것이 바꾸는 문장
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/token-usage/issues/05-handoff-hooks-and-sentences.md
> 브랜치: feature/05-handoff-hooks-and-sentences
> 모델: Opus 5.5 / medium. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-16-47-runner-notice-expectation.md의 "다음"
> 이어받을 상태: 대기열 311(표 머리의 기대 목록과 러너의 Expectation 대조 시험)은 러너 모듈 독스트링의 "기대는 다섯"도 같은 시험이 볼 세 번째 자리다(PR #271 claude-review 1회차, 그 PR 코멘트에만 적었다). 이 티켓은 기대 값을 바꾸지 않지만 표에 notice 사례를 더하며 그 세 곳이 그대로인지 본다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

`tidy-checkouts`가 루트를 `d71d8c96`에서 `e52e8da3`로 당겼고, 로컬 브랜치 `worktree-ruff-boolean-trap`을 지웠다.
`skill-check-and-retro-section` 워크트리는 병합된 PR의 머리와 브랜치 끝이 달라 사람에게 넘겼다(답을 기다리지 않았다).

## 한 것

- 새 훅 `tools/hook_handoff.py`(PostToolUse `Bash|PowerShell|Skill|<GitHub MCP PR 만들기 둘>`)와
  `tools/hook_handoff_notice.py`(Stop). 시험은 `tests/tools/test_hook_handoff.py`.
- `tools/hook_pr_next_session.py`의 계기 문장에 인계 계기가 함께 오면 Skill 도구 대신 그 계기를 따른다는 한 마디.
- `next-session`: 설명, 8행, 1단계의 3, 3단계의 스윕 조건, 결정표 맨 위의 인계 줄, 끊는 줄의 모델 칸, 새 절 "인계할 때".
- 헌법 운영 브랜치와 병합(판 3.0.39), `docs/model-selection.md`, `KICKOFF.md` 7단계 둘(`.claude/settings.json`·
  `next-session` 항목)과 9단계 항목 8.
- 러너 자리표시자 셋(`${OVER_HANDOFF_TRANSCRIPT}`, `${UNDER_HANDOFF_TRANSCRIPT}`, `${EMPTY_TEMP}`), 표 사례 넷.
- `.claude/rules/tools.md`의 시간 목록, 카나리아 명세 셋, 변이 표, 프로브 둘(`.scratch/token-usage/probes/`).

## 결정

이 티켓이 정할 것 셋(티켓 끝).

1. 문구. 인계 문장은 크기·문턱·경계 이름을 들고, "인계의 계기다", 스킬 파일을 Read 도구로 열고 Skill 도구로 부르지
   않는다(까닭 한 마디), 인계하지 않는 때에 들면 넘기지 않고 잇는다를 적는다. 셀프 리뷰 직전과 PR 연 뒤에는 티켓이
   정한 덧붙임을 단다. Stop 알림은 크기, 다음 경계 셋, 넘기지 않는 두 때, 한 번만 낸다를 적는다.
2. 표지 이름. 임시 폴더 아래 `agent-os-handoff/` 에 세션 ID 의 sha256 hex(`launch_hook` 의 `agent-os-launch-hook`
   과 다른 폴더).
3. 카나리아 갈래. 스킬 명세 둘(`next_session_handoff_row.toml`: 같은 경계·받은 범위·두 계기·PR 연 뒤·스윕 조건,
   `next_session_handoff_steps.toml`: 제목 모양·거절·압축 뒤)과 규칙 명세 하나(`tools_rule_handoff_hooks.toml`).

### 문장이 가리키는 자리를 다시 정했다

티켓이 시킨 확인이다. 워크트리 세션이 주 체크아웃의 스킬 파일을 Read 할 때 승인 질문이 뜨는지.

- 이 세션(auto 모드, 추가 작업 폴더 `C:\project`)에서는 묻지 않고 열렸다.
- `claude -p` 기본 권한 모드, 이 워크트리를 작업 폴더로(`--setting-sources local`)는 거부됐다(승인 질문의 비대화형
  모양). 양성 대조로 같은 자리·모드에서 워크트리 안의 사본은 거부 없이 열렸다
  (`.scratch/token-usage/probes/handoff_reach.py` 의 C·D, claude 2.1.300).

승인할 사람이 없는 세션은 인계 첫 단계에서 멈춘다. 그래서 훅이 `skill_for` 로 고른다. 페이로드의 `cwd` 에서 위로
올라가 처음 만나는 next-session 사본에 인계 절(`## 인계할 때`)이 있으면 그것, 없으면 훅 파일과 같은 체크아웃의
사본이다. 처음 만난 사본에 절이 없으면 더 올라가지 않는다. 워크트리는 주 체크아웃 아래라 올라가면 승인을 묻는 자리에
닿는다. 남는 것은 인계 절이 없는 옛 워크트리의 세션이고, 독스트링의 못 보는 것에 적었다.

## 확인

- 모델 도달(`handoff_reach.py` A): 문턱을 1,000 으로 낮춘 사본에서 커밋 뒤 모델이 인계 문장의 첫 문장을 그대로 옮겼다.
  대조군 B(`git status`)는 "알림 없음". 탐침 훅이 저장한 실제 입력을 표 사례에 썼다.
- 시간(`handoff_time.py`, 약 32MB 트랜스크립트, 다섯 번씩 두 회차, 다른 세션이 여럿 돌던 때). 경계 아닌 Bash
  248~628ms·250~260ms, 문턱 위 커밋 257~314ms·272~744ms, 문턱 위 Stop 247~775ms·345~360ms, 문턱 아래 Stop
  319~732ms·265~328ms.
- 러너: 훅 페이로드 114건, 어긋남 0. 대기열 311의 세 자리(표 머리의 기대 목록, 러너 독스트링의 "기대는 다섯",
  `Expectation`)는 바꾸지 않았다.
- 변이: `.scratch/token-usage/probes/handoff_hook_mutations.toml` 14개. 첫 실행에서 12(표지를 쓰지 못해도 알린다)가
  초록이었다. 표지 폴더 자리의 파일은 `makedirs` 가 `FileExistsError` 로 알려 변이된 코드도 "이미 있다"로 읽었다. 임시
  폴더 후보가 없는 시험(`tempfile.gettempdir` 가 `FileNotFoundError`)을 더하자 빨강이었다. 셀프 리뷰 뒤 원문이 바뀐 3·4도
  다시 돌려 빨강이었다.
- 카나리아 셋(`next_session_handoff_row`, `next_session_handoff_steps`, `tools_rule_handoff_hooks`) 모두 통과 4, "없음" 섞임
  0. 셀프 리뷰를 반영한 뒤 사전 확인으로 갈음했다. 기존 next-session·tools 카나리아는 대조군이 이미 병합된 사본이라 다시
  돌리지 않고, `expect` 조각이 고친 원천에 남았는지 대 봤다. 끊는 줄의 문구를 바꿔 `next_session_model_line` 의 조각
  "남은 것이 PR 반영·병합뿐이면"을 한때 깨뜨렸고 되살렸다. `next_session_deferred_merge_running_scope` 의 조각 하나는
  main 의 사본에도 글자 그대로 없다(원천은 백틱을 두른다). 이 브랜치 전부터다.
- 전체 `uv run pytest -q` 0, `pnpm -C web verify` 0, ruff·pyright·lint-imports 0(셀프 리뷰 반영 전 판).

## 셀프 리뷰

`/code-review` 두 축(base `e52e8da3`, 커밋 0, 추적 파일 10, 미추적 11).

고친 것:

- (표준) 프로브 README 에 새 프로브 셋의 행이 없었다. 더했다.
- (표준·명세) `.claude/rules/tools.md` 의 "Skill 에는 훅이 둘"은 매처 없는 `hook_midturn_korean` 을 빠뜨렸다. 셋으로 고쳤다.
- (표준) `KICKOFF.md` 의 "위 매처 목록은 그 둘을 뺀 것이다"는 목록에 없는 다른 매처(`hook_user_settings_read`)도 있어
  거짓이었다. "그 둘의 매처를 넣지 않았다"로 고쳤다.
- (표준·명세) 경계 판정의 어긋남. `gh pr create --help` 를 경계로 봤고, `git --git-dir=… commit`, `gh -R o/r pr create`,
  `gh pr new`, `git commit -- path -h` 를 놓쳤다. 판정을 넓혀 잡게 했다. 넓히지 않은 것(명령 앞의 `time`·`env`·`sudo`·`!`,
  경로로 부른 git, 인용 없는 `-m -h`)은 독스트링의 못 보는 것에 적고 시험으로 고정했다.
- (명세) 못 보는 것 가운데 시험이 없던 둘(실패한 커밋·PR 의 "성공했으면", 병렬 호출 앞쪽의 이전 응답)을 고정했다.
- (표준) `session_context` 가 깨진 기록(문자열 message, 목록 usage, 문자열 토큰)에서 예외로 1로 끝났다. 넘기게 했다.
- (표준) `skill_for` 가 상대 경로 cwd(`C:` 포함)에서 상대 경로를 돌려줬다. 훅의 사본으로 돌린다.
- (표준) 셸 접두 정규식 `_PREFIX` 를 `_COMMAND_PREFIX` 로 바꿔 경로 접두와 가렸다.
- (표준·명세) 근거의 일반화 둘. 훅 독스트링의 "승인을 물었다"를 잰 조건(`claude -p`, 추가 작업 폴더 없음, 거부)과 이
  세션(auto, 추가 작업 폴더, 열렸다)으로 갈라 적었다. 스킬의 제목 바꾸기 근거에 "auto 모드에서 손으로 한 번"을 붙였다.
- (명세) 표 주석 "경로만 자리표시자로 바꿨다"는 세션 ID·`duration_ms` 도 바꾸고 두 필드를 뺀 것과 달랐다. 고쳤다.
- (명세) "인계할 때" 3의 "실행 중 세션 확인"을 적용하지 않는다는 말은 명세에 없는 것이라 뺐다.
- (갈래 밟기, 두 축) "인계할 때"를 고쳤다. 압축이 차례 중간에 오면 끝나지 않은 단계부터 잇는다(제목이 이미 `(인계함)`
  이면 제목만 건너뛴다). 열기에 실패하면 일지에 `인계 못함 <경계>` 를 적어, 압축 뒤의 판정이 `open-session을 부른다`
  줄을 "이미 열렸다"로 읽지 않게 했다. 제목 거절도 같은 줄을 적고, 1이 그 줄을 보면 다시 시도하지 않는다(경계마다의
  되풀이). 압축 뒤 실행 중 세션을 볼 때 제목이 그 브랜치이거나 아직 없는 세션만 센다(무관한 형제). 되돌리는 제목은 2가
  일지에 적은 바꾸기 전 제목이다. "이 세션의 지시문"을 결정표 "이 세션" 줄로 이어 간 세션까지 정의했다. 두 계기의
  우선을 절 머리로 옮기고, 넘기지 않을 때 셀프 리뷰는 그대로 밟고 PR 연 뒤면 순서 1단계부터 따른다고 적었다. 훅
  문장의 "code-review 의 단계는 밟지 않는다"는 "넘길 때는"으로 조건을 달았다. PR 감시 알림이 넘긴 세션에만 간다는 것을
  6에 적었다.

남긴 것과 이유:

- (표준, 냄새) usage 기록 짓기가 시험·러너·프로브 세 곳에 있다. 셋은 서로 import 하지 않는 자리(시험, 러너의 픽스처,
  커밋된 프로브)라 그대로 둔다.
- (표준, 냄새) `context_for` 의 경계 비교 되풀이. 경계가 셋이고 문장이 다 다르므로 둔다.

다시 돌린 것: 고친 두 시험 파일 57건 초록, ruff·pyright(바뀐 파일) 0, 변이 3·4 빨강, 카나리아 셋 사전 확인 통과. 손으로
치는 다섯은 커밋의 pre-commit 으로 갈음한다.

PR 직전 리뷰에 밀 새 문장(반영으로 새로 썼다):

- `tools/hook_handoff.py` 독스트링: "기본 권한 모드에서 추가 작업 폴더 없이(`--setting-sources local`) 워크트리를 작업
  폴더로 띄운 `claude -p` 세션은 주 체크아웃의 그 파일 Read 를 거부당했고(승인 질문의 비대화형 모양), 같은 자리의
  워크트리 사본은 열었다", "auto 모드에 추가 작업 폴더로 `C:/project` 를 둔 데스크톱 세션에서는 묻지 않고 열렸다".
- 같은 독스트링의 못 보는 것: 명령 앞의 래퍼(`time`, `env X=1`, `sudo`, `!`)와 경로로 부른 git, `git commit -m -h`.
- `next-session` "인계할 때" 1·4·5·6의 새 문장(`인계 못함` 줄, 끝나지 않은 단계부터, 제목이 그 브랜치이거나 아직 없는
  세션, PR 감시 알림이 넘긴 세션에만 간다).
- `.claude/rules/tools.md`: "Skill에는 … 훅이 셋 붙는다".
