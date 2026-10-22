# 2026-10-22 (15) /ui-design 스킬과 디자인 폴더 계기 훅을 들인다

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "ADR 0033과 ADR 0025의 2026-10-20 이력이 다음 PR로 넘긴 /ui-design 스킬과 그 "함께 고치는 것"을 티켓 .scratch/harness/issues/002-ui-design-skill.md로 쓰고 한다 … 이번 요청 범위: PR과 병합까지"

## 체크아웃 정리

제목을 `chore/002-ui-design-skill`로 바꾸고 `tidy-checkouts`를 돌았다. 루트는 main이고 `aba71813`이 origin/main과 같아 당길 것이 없었다. 병합된 워크트리 넷(`01-harness-ticket-numbers`, `02-docs-and-skills-teach-tickets`, `07-morning-report-harness-branches`, `design-reverse-sync-spec`)은 쉬는 세션 말고도 셸 프로세스가 작업 디렉터리로 쥐어 `남긴다`였고 `끝낸다` 줄이 없었다. 휴지통의 다섯 항목은 node·esbuild·python 프로세스가 올린 모듈 때문에 `empty-trash`가 종료 1로 남겼다. 그 뒤 `EnterWorktree`(이름 `002-ui-design-skill`)로 들어가 브랜치 이름을 바꿨다.

## 정한 것

두 이력과 `plan.md` admin-style 행이 이 PR에 넘긴 셋을 정했다. Design 형식의 지침은 Artifact 도구로 형식을 읽어(`action: "read"`, `type_url`, 판 `1792645138-4a28`) 봤다. 아티팩트는 만들지 않았다.

- **디자인 시스템을 붙이는 법.** 형식 지침의 설치는 `project/ds/<폴더>/tokens.json`과 색인의 `designSystems` 기록이고, 디자인 시스템이 `tokens.json`을 내지 않으면 그 파일 없이 붙이고 그렇다고 말하라고 적는다(형식 지침을 읽었다). 우리 디자인 시스템 아티팩트에는 그 파일이 아직 없으므로(ADR 0025의 2026-10-20 이력) 기록만 두고 붙인다. 첫 그리기가 design-reverse-sync의 구현보다 먼저 와도 막히지 않는다. 폴더 이름은 `agent-os`.
- **화면을 받아 옮기는 법.** `read`로 `project/canvas.json`과 고른 아트보드를 받아 `design/`에 같은 이름으로 둔다. 와이어프레임과 완성 화면은 아티팩트 하나에 두고 페이지로 가른다.
- **목업의 웹 편집을 가르는 법.** 판 id는 사람이 고치지 않아도 올라(ADR 0025의 2026-10-21 이력) 쓰지 않고, 화면 파일마다 `read` 머리의 sha256을 커밋한 파일의 sha256과 맞댄다. 커밋한 파일이 곧 기록이라 README 표에 sha256을 따로 적지 않는다. Design 아티팩트의 머리에 sha256이 나오는지는 재지 못했다(스킬의 "재지 못한 것").
- `/ui-design`이 design-reverse-sync의 스킬보다 먼저 들어오므로 그리기 전 확인은 그쪽 스킬 티켓이 넣는다(그 명세의 Out of Scope).
- 형식 지침이 사람이 청하지 않으면 확인하지 말라고 적어(영문 지침을 옮겼다), `frontend-design`의 찍어 보고 고치기는 사람이 청할 때만으로 두었다.

이 셋은 ADR 0025 이력이 이 PR에 정하라고 넘긴 칸을 채운 것이라 ADR 이력을 새로 쓰지 않았다. 결정의 자리는 스킬 본문과 `docs/agents/issue-tracker.md` 화면 디자인 절, `plan.md` admin-style 행의 2026-10-22 괄호다.

## 한 일

- 티켓 `.scratch/harness/issues/002-ui-design-skill.md`(번호는 `sibling_overlap.py`의 `티켓 002`, 쓴 뒤 다시 쳐 겹침 없음).
- `.claude/skills/ui-design/SKILL.md`. 단계 일곱(설치, 계정과 디자인 시스템, 참고 디자인과 시작 프롬프트, `frontend-design` 부르기, 그리기, 고르기, 옮기기)과 "웹 편집 확인", "재지 못한 것". 쓰기 전에 `writing-for-agents`를 불렀다.
- `tools/hook_ui_design.py`(PostToolUse Write|Edit 계기 훅)와 `tests/tools/test_hook_ui_design.py`. 시험을 먼저 써서 모듈이 없어 수집 오류로 빨간 것을 보고, 훅을 쓴 뒤 등록 시험 하나만 빨간 것을 보고 등록했다. 페이로드 표 두 건, 등록, 변이 표 `.scratch/harness/probes/ui_design_hook_mutations.toml`(열 모두 기대대로).
- `next-session` 결정표에 "화면 디자인" 줄. 시작 프롬프트 `/ui-design <slug>`는 `open_session.ps1`의 `Convert-StartLine`이 인자째 스킬 파일을 읽으라는 줄로 옮긴다(코드를 읽었다).
- 문서: `docs/agents/issue-tracker.md` 화면 디자인 절(계정 문단, 시작 프롬프트, 옮기기, 표의 판 id), `KICKOFF.md`(7단계 설치와 복사 목록, 9단계 디자인 절차), `kickoff/prompting.md`(사람과 세션의 일, 브라우저 요령을 뺐다, 계정 문단), `.scratch/admin-style/design/screens-prompt.md`(하는 법, 양식 절을 뺐다, 고른 뒤), `.design-sync/NOTES.md`의 계정 문장 둘, `.claude/rules/tools.md`의 Write·Edit 훅 목록, `plan.md` admin-style 행.
- 충돌 목록 `.scratch/design-system/design/frontend-design-conflicts.md`(표의 머리만)와 그것을 가리키는 `refresh-prompt.md`·같은 폴더 `README.md`의 문장.
- 카나리아 명세 셋(`ui_design_skill`, `next_session_ui_design_row`, `tools_rule_ui_design_hook`).

`frontend-design` 플러그인은 이 PC에 사용자 범위로 이미 켜져 있었다(`claude plugin list`). 이 저장소의 프로젝트 설정에 넣는 설치(`--scope project`)는 하지 않았다. 스킬의 1단계가 켜져 있는지만 보므로 지금 범위로 돈다.

새 스킬의 설명이 스킬 목록 예산(0.006)에서 빠지는지는 재지 않았다. 빠져도 결정표 줄과 훅이 이름을 들어 부른다.

## 검사

- 시험 `tests/tools/test_hook_ui_design.py` 19개 통과. 변이 표 열 모두 기대대로(대조군 포함).
- `tools/run_hooks.py` 152건 어긋남 0(셀프 리뷰 반영 뒤, 침묵 입력 하나를 더한 판).
- 카나리아 셋 모두 통과 4이고 대조군(주 체크아웃 `aba71813`)은 "없음"이었다. 스킬과 결정표 줄은 셀프 리뷰를 반영한 뒤 다시 돌려 다시 통과 4였다.
- 반영 전에 `uv run python tools/run_checks.py`가 종료 0, pyright·lint-imports·`check_type_escapes`·`check_instructions`가 0이었다. 반영 뒤 바뀐 것은 문서와 페이로드 표뿐이라 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

## 셀프 리뷰

`/code-review`(base `aba71813`, 추적 13개, 커밋 0, 미추적 10개). 표준 축(sonnet·high)과 명세 축.

고친 것.
- 스킬 2단계의 계정 판정. 표준 축이 `paths`를 준 `read`의 머리에 "owned by you"가 없고 "published by a writer of the artifact"만 나온 것을 봤다. 고친 문장: "`read`로 `paths` 없이 읽어 머리를 본다. `paths`를 준 읽기의 머리에는 주인 문구가 나오지 않았다(셀프 리뷰 서브에이전트가 봤다, 일지 2026-10-22-15). 머리가 지금 계정을 주인("owned by you")으로 적거나 편집할 수 있다("writer")고 적어야 한다. 누가 올렸는지를 적는 "published by a writer of the artifact"는 이 판정이 아니다."
- `tokens.json`의 경로. 디자인 시스템 아티팩트 안의 경로는 어디에도 정해지지 않았다(명세 축). 스킬 2단계에 두 문장을 더했다. 앞의 것은 `list`의 `files` 범위에서 이름이 `tokens.json`인 파일을 찾아 그 경로로 읽는다는 것이고, 뒤의 것은 그 파일을 올릴 경로를 design-reverse-sync의 구현이 정한다는 것이다(원문은 스킬 2단계). 재지 못한 것에도 더했다.
- 새 프로젝트의 첫 `design-system` 탐색이 "artifact not found"에 막히는 갈래. 고친 문장: "화면 디자인 절에 디자인 시스템 아티팩트의 주소가 아직 없으면 이 단계를 건너뛴다. 계정은 5에서 만드는 아티팩트의 주인이다."
- 끊긴 뒤 다시 부르면 아티팩트가 둘이 되는 갈래(두 축). 고친 문장: "시작 프롬프트 끝에 `아티팩트:` 줄이 있으면 끊긴 뒤 다시 부른 것이다. 새로 만들지 않고 그 주소를 `read`해 그 아티팩트에 이어 그린다. … 바로 그 주소를 시작 프롬프트 끝의 `아티팩트:` 줄에 적는다."
- 그리는 차례가 화면 프롬프트(와이어프레임을 고른 뒤 완성 화면)와 갈린 것(두 축). 고친 문장: "무엇을 어떤 차례로 그릴지는 시작 프롬프트가 정한다. 와이어프레임을 먼저 고르게 하면 5~6을 와이어프레임으로 돈 뒤 완성 화면으로 한 번 더 돈다." `screens-prompt.md`의 "4의 안 고르기"를 "3의 안 고르기"로 고쳤다.
- README에 줄이 이미 있을 때 웹 편집 확인 뒤의 끝(두 축). 고친 문장: "그 뒤 더 그리거나 다시 그릴 화면이 지시문이나 사람의 말에 있거나 `design-system`의 재탐색이면 3부터 잇고, 아니면 거기서 끝난다."
- 1단계의 멈춤이 2·3을 막는지 모호했다. "2·3은 이어 한 뒤 4 앞에서 그 스킬이 불릴 때까지 멈춘다"로 고쳤다.
- 7단계에 색인 경로 가드. "색인의 경로에 `..`·`\`가 들었거나 `/`로 시작하면 옮기지 않고 사람에게 알린다(형식 지침의 경로 가드)."
- 웹 편집 확인이 작업 트리의 파일을 셀 수 있었다(`.claude/rules/probes.md`의 스냅샷 항목). "커밋한 같은 파일(`git show HEAD:<경로>`, 작업 트리의 고친 판이 아니다)"로 고치고, 머리에 sha256이 없을 때 `diff`로 맞대는 길을 더했다.
- 닫힌 주장 "사람에게는 둘만 묻는다"(스킬)와 "사람에게 남기는 일은 둘이다"(`kickoff/prompting.md`)에 반례(설치 허락, 계정, 참고 디자인)가 있었다. 둘 다 "디자인에서 사람이 판단하는 것은 방향과 확정할 화면이고, 그 밖에는 단계가 막혔을 때만 사람을 부른다"는 일반 조항으로 고쳤고, 티켓 수용 기준 문장도 맞췄다.
- `next-session` 결정표 줄의 조건이 admin-style 행에 "명세 전"이라는 말이 없어 성립하지 않을 수 있었고(명세 축), `design-system` 재탐색은 `spec.md`와 README 줄이 있어 성립하지 않았다(표준 축). "`plan.md`의 그 기능 행이 명세 전에 화면을 그린다고 적거나 `.scratch/<slug>/design/`에 시작 프롬프트(`*-prompt.md`)가 있는데, … 디자인 시스템의 방향을 다시 탐색할 때도 `spec.md`와 README의 줄이 있든 없든 이 줄이다"로 고쳤다.
- 살아 있는 문서의 옛 표현과 미래형. `plan.md` web-widget 행(명세 직전에 Claude Design에서 그려 내보낸다는 옛 문장)과 admin-style 행 머리(Claude Design에서 디자인 시스템으로 화면을 그린다는 옛 문장), admin-style·design-reverse-sync 행의 "그 스킬을 들이는 PR이 정한다", `.scratch/design-reverse-sync/spec.md` Out of Scope 두 줄("아직 저장소에 없다 … 다음 PR", "`/ui-design`을 들이는 PR이 … 정한다"), `.scratch/design-system/design/README.md` 머리를 `/ui-design`과 과거형으로 고쳤다.
- 일지의 따옴표 인용 하나가 영문 형식 지침의 번역이었다. 따옴표를 빼고 옮긴 것이라고 적었다.
- `tools/hook_payloads.toml`에 근접 반례 침묵 입력(`.scratch/harness/probes/design/x.toml`)을 더했다(대기열 24).

남긴 것.
- 변이 표에 `expect_output`이 없다(표준 축, 판단 항목). 이 표를 뺀 훅 변이 표 스물 가운데 열일곱이 쓰지 않는 선례(2026-10-22 `grep -c expect_output`)를 따랐고, 시험 파일 하나만 도는 표라 다른 원인으로 빨개질 자리가 좁다.
- `design_slug`가 정규화하지 않은 `..` 경로에서 거짓 양성, 상대 경로에서 거짓 음성을 낸다(표준 축이 함수를 불러 봤다). Write·Edit 페이로드의 `file_path`는 절대 경로라 Minor로 두었다.
- 디자인 폴더에 처음 쓴 파일이 충돌 목록이면 훅이 `design-system`을 알린다(명세 축, Minor). 알림의 "이미 부른 세션이면 무시" 문장이 받는다.
- ADR 0033이 "찍어 보고 고치기"를 `frontend-design` 몫으로 적었는데 스킬이 사람이 청할 때만으로 좁힌 것, `design-system` 탐색의 색·글꼴 예외, 폴더 이름 `agent-os`(형식 README는 번들 전역에서 짓는다)는 판단 항목이다. 앞의 것은 형식 지침과 맞추려고 정했고 이 일지의 "정한 것"이 근거다.
- 훅 셋의 같은 모양(`marker_name`·`claim_first`·`main`)은 훅끼리 import하지 않는 규약의 비용이다(`.claude/rules/tools.md`).

다시 돌린 것: `run_hooks.py`(152건 어긋남 0), `check_md_tables`·`check_instructions`·`check_line_separators`(0), 카나리아 둘(통과 4). 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

## 인계

커밋 `9fc49ed5`(pre-commit 통과) 뒤 세션 컨텍스트가 인계 문턱을 넘어 `hook_handoff`의 `커밋 뒤` 계기가 왔다. 곁 세션이 아니고(`get_session`의 `self`에 `parentSessionId`가 없다) 요청 범위가 병합까지라 넘긴다. 이 세션의 지금 제목은 `chore/002-ui-design-skill`이고 `chore/002-ui-design-skill (인계함)`으로 바꾼다.

이 절은 커밋하지 않았다. 새 세션이 이어 쓰고 커밋한다. pre-commit의 인용 대조가 이 일지에 경고 둘을 냈다(막지 않는다). 셀프 리뷰 절의 `list scope: files에서…` 인용은 스킬 원문을 줄여 옮기며 `…`를 넣은 것이고, `화면은 Claude Design에서 그 디자인 시스템으로 그린다`는 이번에 고쳐 저장소에서 사라진 옛 문장이다. 새 세션이 따옴표를 떼거나 원문대로 맞춘다. `.scratch/plan.md` 17행의 `"그리기 직전의 /design-sync"` 경고는 이 PR 전부터 있던 문장이다.

지시문:

다음 작업: .scratch/harness/issues/002-ui-design-skill.md. 화면 디자인 스킬 /ui-design과 디자인 폴더 계기 훅을 들인 커밋의 PR을 열고 병합한다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: ADR 0033과 ADR 0025의 2026-10-20 이력이 다음 PR로 넘긴 /ui-design 스킬과 그 "함께 고치는 것"을 티켓 .scratch/harness/issues/002-ui-design-skill.md로 쓰고 한다
브랜치: chore/002-ui-design-skill
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-15-ui-design-skill.md(셀프 리뷰 절의 고친 것과 인계 절)
이어받을 상태: 인계: 커밋 뒤. 커밋 9fc49ed5까지 티켓의 수용 기준을 모두 채우고 셀프 리뷰를 반영해 커밋했다(아직 푸시하지 않았고 PR도 없다). 남은 단계는 일지의 인계 절이 든 인용 경고 둘을 고쳐 커밋하는 것, PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2. 셀프 리뷰를 반영하며 새로 쓴 문장은 일지 셀프 리뷰 절의 고친 것 줄에 원문으로 있고 bug-perf-review 브리프에 밀 주장으로 나열한다), 푸시와 PR, 봇 회차, 병합이다. 일지의 "다음" 절과 회고는 아직 없다. docs/journal/2026-10-22-15-ui-design-skill.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. sibling_overlap이 함께 고친 파일로 PR #296·#297·#347과 티켓 03 워크트리(KICKOFF.md, docs/agents/issue-tracker.md)를 들었다. 그쪽이 먼저 병합되면 origin/main을 합칠 때 충돌을 본다
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-22T10:35:36Z

## 이어 한 세션

새 세션이 제목을 바꾸고 주 체크아웃에서 `tidy-checkouts`를 돌았다. 루트는 이미 origin/main(`96fbe241`)과 같았다. 지운 것은 `worktree-01-contrast-module` 브랜치와 휴지통의 `node_modules` 다섯이고, 병합된 워크트리 다섯은 쉬는 세션과 셸 프로세스가 쥐어 남았으며, 등록 없이 `.git`이 있는 `01-contrast-module` 폴더는 사람에게 넘겼다. 휴지통의 `.venv` 하나는 python.exe가 쥐어 남았다. 그 뒤 `EnterWorktree(path)`로 이 워크트리에 들어왔다.

인계 절의 인용 경고 둘은 따옴표를 떼고 서술로 고쳤다. 앞의 것은 원문의 `"files"` 따옴표가 인용 경계를 깨뜨린 것이었다.
