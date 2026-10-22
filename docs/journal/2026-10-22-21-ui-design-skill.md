# 2026-10-22 (21) /ui-design 스킬과 디자인 폴더 계기 훅을 들인다

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
- 스킬 2단계의 계정 판정. 표준 축이 `paths`를 준 `read`의 머리에 "owned by you"가 없고 "published by a writer of the artifact"만 나온 것을 봤다. 고친 문장: "`read`로 `paths` 없이 읽어 머리를 본다. `paths`를 준 읽기의 머리에는 주인 문구가 나오지 않았다(셀프 리뷰 서브에이전트가 봤다, 일지 2026-10-22-21). 머리가 지금 계정을 주인("owned by you")으로 적거나 편집할 수 있다("writer")고 적어야 한다. 누가 올렸는지를 적는 "published by a writer of the artifact"는 이 판정이 아니다."
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
읽을 것: docs/journal/2026-10-22-21-ui-design-skill.md(셀프 리뷰 절의 고친 것과 인계 절)
이어받을 상태: 인계: 커밋 뒤. 커밋 9fc49ed5까지 티켓의 수용 기준을 모두 채우고 셀프 리뷰를 반영해 커밋했다(아직 푸시하지 않았고 PR도 없다). 남은 단계는 일지의 인계 절이 든 인용 경고 둘을 고쳐 커밋하는 것, PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2. 셀프 리뷰를 반영하며 새로 쓴 문장은 일지 셀프 리뷰 절의 고친 것 줄에 원문으로 있고 bug-perf-review 브리프에 밀 주장으로 나열한다), 푸시와 PR, 봇 회차, 병합이다. 일지의 "다음" 절과 회고는 아직 없다. docs/journal/2026-10-22-21-ui-design-skill.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. sibling_overlap이 함께 고친 파일로 PR #296·#297·#347과 티켓 03 워크트리(KICKOFF.md, docs/agents/issue-tracker.md)를 들었다. 그쪽이 먼저 병합되면 origin/main을 합칠 때 충돌을 본다
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-22T10:35:36Z

## 이어 한 세션

새 세션이 제목을 바꾸고 주 체크아웃에서 `tidy-checkouts`를 돌았다. 루트는 이미 origin/main(`96fbe241`)과 같았다. 지운 것은 `worktree-01-contrast-module` 브랜치와 휴지통의 `node_modules` 다섯이고, 병합된 워크트리 다섯은 쉬는 세션과 셸 프로세스가 쥐어 남았으며, 등록 없이 `.git`이 있는 `01-contrast-module` 폴더는 사람에게 넘겼다. 휴지통의 `.venv` 하나는 python.exe가 쥐어 남았다. 그 뒤 `EnterWorktree(path)`로 이 워크트리에 들어왔다.

인계 절의 인용 경고 둘은 따옴표를 떼고 서술로 고쳤다. 앞의 것은 원문의 `"files"` 따옴표가 인용 경계를 깨뜨린 것이었다.

origin/main(`96fbe241`, PR #347)을 합쳤다. `plan.md` design-reverse-sync 행이 충돌했고, main의 티켓 열 문장 위에 이 브랜치의 과거형(sha256으로 정했다)을 얹었다. main이 들인 티켓 07의 `/ui-design` 조건문(저장소에 있으면 넣고 없으면 넘긴다)은 이 PR로 스킬이 먼저 들어오므로 확정 문장으로 고쳤다.

## PR 직전 리뷰

CodeRabbit CLI는 좌석이 없어(`Seat: not assigned`) 대체 둘을 돌렸다. `/security-review`는 지적이 없었다(표지 이름은 해시라 경로 순회가 없고, 자식 프로세스와 셸이 없다). `bug-perf-review`는 Critical·Major 없이 Minor 7, Nit 2를 냈고 값이 작아 PR 전에 고쳤다.

- 7단계 경로 가드가 윈도의 `C:x`, 대체 스트림 `:`, 끝의 점을 놓쳤다. 거부 목록을 허용 목록(`project/` 아래, 조각마다 글자·숫자·`._-`·공백, `.`·공백으로 끝나지 않는다)으로 바꿨다(`.claude/rules/tools.md`의 허용 목록 항목과 같은 모양).
- 옮긴 곳이 `design/canvas.json`인지 `design/project/canvas.json`인지 정하지 않았다. `project/`를 뗀다고 적고, 웹 편집 확인이 그 경로를 따옴표로 `git show`하며 HEAD에 없으면 새 화면으로 본다고 더했다.
- 아티팩트가 둘이 되는 길 둘. 만든 뒤 `아티팩트:` 줄을 적기 전에 끊긴 길은 `list` `type: "Design"`에서 같은 제목을 먼저 찾게 했고, 시작 프롬프트가 여럿일 때는 3에서 쓰거나 고른 파일 하나라고 정했다. 줄의 주소가 "artifact not found"인 갈래도 더했다. `list`가 제목을 내는지는 재지 못한 것에 더했다.
- `tokens.json`이 둘 이상이면 사람에게 고르게 했다. 계정 판정은 문구가 지금 계정을 가리키는지로 본다고 적었다("not owned by you" 반례). 2단계를 건너뛰면 5의 만들기가 계정 판정이라고 끝 조건에 적었다.
- `next-session` 결정표 "화면 디자인" 줄의 조건 묶음이 모호해, README에 줄이 없다는 조건을 앞으로 빼고 둘 가운데 하나로 풀었다.
- 훅의 `design_slug`가 `..`를 기능으로 읽었다(일지가 Minor로 남긴 것). `posixpath.normpath`로 먼저 접게 했고 반례 다섯을 시험 하나로 고정했다(빨강을 본 뒤 고쳤다, 20개 통과).

오탐으로 본 것: 와이어프레임과 완성 화면의 두 바퀴가 아티팩트를 둘 만든다(둘째 바퀴가 첫 바퀴의 줄을 읽는다), 줄바꿈으로 sha256이 어긋난다(`.gitattributes`가 `eol=lf`. 이 근거는 아티팩트의 파일이 LF일 때만 성립한다. 셀프 리뷰 둘째 절이 바로잡았다), 훅 문장의 형식 문자열 주입(`.format`은 값을 다시 풀지 않는다).

## 인계 (둘째)

PR 직전 리뷰 지적을 반영한 뒤 커밋 전 셀프 리뷰(`/code-review`)를 부르자, 세션 컨텍스트가 인계 문턱을 넘어 `hook_handoff`의 `셀프 리뷰 직전` 계기가 왔다. 이 세션의 지시문은 `인계: 커밋 뒤`로 시작해 같은 경계가 아니고, 곁 세션이 아니며(`get_session`의 `self`에 `parentSessionId`가 없다), 요청 범위가 병합까지라 넘긴다. 이 세션의 지금 제목은 `chore/002-ui-design-skill`이고 `chore/002-ui-design-skill (인계함)`으로 바꾼다.

커밋하지 않은 변경은 다섯 파일이다. `.claude/skills/ui-design/SKILL.md`, `.claude/skills/next-session/SKILL.md`(결정표 "화면 디자인" 줄), `tools/hook_ui_design.py`, `tests/tools/test_hook_ui_design.py`(20개 통과), 이 일지. 커밋 메시지 초안은 위 "PR 직전 리뷰" 절의 고친 것 여섯 줄을 요약한 것이다. 반영하며 새로 쓴 문장은 그 여섯 줄이 원문을 가리킨다(스킬 2·5·7단계와 웹 편집 확인, 결정표 줄, `design_slug` 독스트링). 이 PR은 아직 푸시하지 않았고 PR도 없다.

지시문:

다음 작업: .scratch/harness/issues/002-ui-design-skill.md. 화면 디자인 스킬 /ui-design과 디자인 폴더 계기 훅을 들인 커밋의 PR을 열고 병합한다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: ADR 0033과 ADR 0025의 2026-10-20 이력이 다음 PR로 넘긴 /ui-design 스킬과 그 "함께 고치는 것"을 티켓 .scratch/harness/issues/002-ui-design-skill.md로 쓰고 한다
브랜치: chore/002-ui-design-skill
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-21-ui-design-skill.md(이어 한 세션 절, PR 직전 리뷰 절, 인계 (둘째) 절)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경 다섯 파일(PR 직전 리뷰 반영분)이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 HEAD, 커밋하지 않은 변경만)부터 한다. origin/main(96fbe241)은 이미 합쳤고, CodeRabbit CLI는 좌석이 없어 대체 둘(/security-review 지적 없음, bug-perf-review Minor 7·Nit 2)을 돌려 반영까지 마쳤다. 남은 단계는 셀프 리뷰 반영, 커밋, 푸시와 PR(PR 체크리스트에 대체 둘의 결과를 적는다), 봇 회차, 병합, 일지의 "다음" 절과 회고다. docs/journal/2026-10-22-21-ui-design-skill.md
확인할 선행 조건: 주 체크아웃은 main이고 origin/main(96fbe241)과 같다(이 세션의 tidy-checkouts). 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. sibling_overlap이 함께 고친 파일로 PR #296·#297·#350과 워크트리 bug-perf-review-batch·mcp-shutdown-spec·measure-word-hook을 들었다. 그쪽이 먼저 병합되면 origin/main을 합칠 때 충돌을 본다
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-22T11:09:34Z

## 이어 한 세션 (둘째)

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "ADR 0033과 ADR 0025의 2026-10-20 이력이 다음 PR로 넘긴 /ui-design 스킬과 그 "함께 고치는 것"을 티켓 .scratch/harness/issues/002-ui-design-skill.md로 쓰고 한다 … 이번 요청 범위: PR과 병합까지"

새 세션이 제목을 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 앞 세션의 인계 절이 말한 커밋 메시지 초안은 파일로 남지 않아 새로 썼다.

## 셀프 리뷰 (둘째)

`/code-review`(base `6a9ec9ae`, 커밋하지 않은 변경 다섯 파일, 커밋 0, 미추적 0). 표준 축(sonnet·high)은 Major 1(판단 항목)·Minor 7·Nit 6, 명세 축은 Minor 4·Nit 2를 냈고 두 축이 여러 자리에서 겹쳤다.

고친 것. 반영하며 새로 쓴 문장은 PR 직전 리뷰에 밀 주장이다.
- 5단계에서 제목으로 찾기(표준 Major, 명세 Minor). `design-system`의 제목에 날짜가 들어 다른 날 다시 부르면 찾지 못하고, 같은 기능의 둘째 프롬프트가 끝난 아티팩트를 끊긴 것으로 읽었다. 고친 문장: "제목에 프롬프트 파일 이름이 들어 다른 프롬프트의 아티팩트와 겹치지 않으므로, 하나 있으면 만든 뒤 줄을 적기 전에 끊긴 것이라 그 주소를 줄에 적고 이어 그린다. 둘 이상이거나 `list`가 실패하면 멈추고 사람에게 알린다." 제목은 `<기능> 화면 · <프롬프트 파일 이름>`과 `디자인 시스템 탐색 · <프롬프트 파일 이름>`이다.
- 3단계에 프롬프트가 여럿일 때 고르는 규칙이 없었다(두 축). 고친 문장: "여럿이면 화면이 README 표에 아직 없는 것을 쓰고, 그래도 여럿이면 사람에게 고르게 한다. 그 화면이 모두 README 표에 있는 프롬프트(끝난 것)는 다시 쓰지 않는다. `design-system`의 방향을 다시 탐색하면 새 프롬프트 파일을 쓴다."
- 웹 편집 확인에서 HEAD에 없는 갈래를 받는 끝 조건이 없었고 괄호가 원인을 하나로 닫았다(두 축). 고친 문장: "HEAD에 그 파일이 없으면(옮긴 뒤 아직 커밋하지 않았거나, 커밋한 뒤 옮기거나 지웠다) 맞대지 않고 그 화면과 까닭을 사람에게 알린다. 옮긴 뒤 커밋하지 않은 것이면 커밋한 뒤에 다시 맞댄다." 끝 조건에 "HEAD에 없어 사람에게 알렸다"를 더했다.
- 7단계 허용 목록이 빈 조각, 점으로 시작하는 조각(`.git`), 윈도 예약 이름을 지나보냈고, 이 저장소가 그 폴더에 쓰는 파일을 덮어쓸 수 있었다(두 축). 고친 문장(줄임): `/`로 가른 조각마다 비지 않고, 글자·숫자·`.`·`_`·`-`·공백만 들며, `.`으로 시작하거나 `.`·공백으로 끝나지 않고, 확장자를 뗀 이름이 윈도 예약 이름(…)이 아닌 것만 옮긴다. … 옮긴 곳이 이 저장소가 그 폴더에 쓰는 파일(`README.md`, `*-prompt.md`, 충돌 목록)과 같으면 옮기지 않는다. 원문은 스킬 7단계다.
- 2단계의 따옴표 문구 하나가 원문 없는 가상의 반례였다(표준). 따옴표를 떼고 "주인이 다른 계정이라고 적은 문구는 낱말 owned가 들어도 아니다"로 고쳤다. 끝 조건의 건너뛴 갈래는 "이 단계를 건너뛰었으면 끝 조건도 없고, 계정은 5의 만들기가 성공한 것으로 판정한다"로 갈랐다(명세 Nit).
- 머리의 닫힌 목록(단계가 막혔을 때로 설치 허락과 계정 둘을 든 것)에 반례(`tokens.json` 고르기, "artifact not found")가 생겼다(표준). 일반 조항 "단계가 혼자 나아갈 수 없을 때(… 후보가 여럿이라 고를 근거가 없을 때, 찾던 아티팩트가 없을 때 등)"로 올렸다.
- `next-session` 결정표 줄의 "그 폴더"가 가리키는 곳이 모호했다(두 축). "`.scratch/<slug>/design/README.md`에 그릴 화면의 줄이 하나라도 없고(폴더나 README가 없어도 그렇다)"로 고쳤다.
- 훅. 독스트링의 헛된 단서("기능 자리에 오지 않는 한")를 "접히지 않고 남는 `..` 는 경로 맨 앞뿐이라 `.scratch` 뒤에 오지 않고 판정을 바꾸지 않는다"로 고쳤고, 그 주장을 시험 하나로 고정했으며(21개 통과), 접기를 빼는 변이를 변이 표에 더했다. `_SPLIT`을 `_SEPARATORS`로 바꾸고, 함수 독스트링의 겹친 설명을 덜고 발견의 출처를 셀프 리뷰와 PR 직전 리뷰 둘로 고쳤다.
- 일지의 오탐 판정 "줄바꿈으로 sha256이 어긋난다"의 근거가 반대 방향이었다(표준). `eol=lf`는 커밋 때 LF로 바꾸므로 아티팩트가 CRLF면 어긋난다. 그 줄에 단서를 달았다. 아티팩트 파일의 줄바꿈은 재지 못했다.

남긴 것.
- 스킬을 PR 직전에 다시 고친 뒤 새 세션에서 불러 본 기록(작업 규약 3)은 카나리아로 갈음한다(아래).
- 스킬과 결정표 줄의 카나리아 둘은 반영 뒤 다시 돌려 둘 다 통과 4였다(대조군 주 체크아웃 `96fbe241`은 "없음"). 반영한 문장이 새 세션에 실리는지는 이 둘이 보고, 문장의 뜻이 따르는 대로 도는지는 첫 그리기가 확인한다.
- 표준 축 Nit 가운데 알림이 그 스킬이 쓰는 README에도 한 번 난다는 것과 변이 표의 `expect_output` 없음은 앞 셀프 리뷰가 남긴 판단을 그대로 둔다.

다시 돌린 것: `tests/tools/test_hook_ui_design.py` 21개 통과, 변이 표 `ui_design_hook_mutations.toml` 변이 11 모두 기대대로(대조군 포함), 카나리아 둘 통과 4. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

커밋 `4c302a9b`(pre-commit 통과. ruff 둘, lint-imports, pyright 둘, web-verify, pytest가 Passed). 인용 대조 경고 셋은 커밋 뒤 이 일지에서 따옴표를 떼어 고쳤다(아직 커밋하지 않았다).

## 인계 (셋째)

커밋 `4c302a9b` 뒤 세션 컨텍스트가 인계 문턱을 넘어 `hook_handoff`의 `커밋 뒤` 계기가 왔다. 이 세션의 지시문은 `인계: 셀프 리뷰 직전`으로 시작해 같은 경계가 아니고, 곁 세션이 아니며(`get_session`의 `self`에 `parentSessionId`가 없다), 요청 범위가 병합까지라 넘긴다. 이 세션의 지금 제목은 `chore/002-ui-design-skill`이고 `chore/002-ui-design-skill (인계함)`으로 바꾼다.

커밋하지 않은 변경은 이 일지 하나다(커밋 결과 줄, 인용 경고 고침, 이 절). 아직 푸시하지 않았고 PR도 없다. 셀프 리뷰 둘째 절의 고친 것 줄에 반영하며 새로 쓴 문장이 원문으로 있다. PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2)는 그 문장들을 밀 주장으로 다시 돈다. 앞의 PR 직전 리뷰는 셀프 리뷰 둘째보다 먼저 돌아 이 문장들을 보지 못했다.

지시문:

다음 작업: .scratch/harness/issues/002-ui-design-skill.md. 화면 디자인 스킬 /ui-design과 디자인 폴더 계기 훅을 들인 커밋의 PR을 열고 병합한다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: ADR 0033과 ADR 0025의 2026-10-20 이력이 다음 PR로 넘긴 /ui-design 스킬과 그 "함께 고치는 것"을 티켓 .scratch/harness/issues/002-ui-design-skill.md로 쓰고 한다
브랜치: chore/002-ui-design-skill
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-21-ui-design-skill.md(PR 직전 리뷰 절, 셀프 리뷰 (둘째) 절, 인계 (셋째) 절)
이어받을 상태: 인계: 커밋 뒤. 커밋 4c302a9b까지 셀프 리뷰 둘째를 반영해 커밋했다(pre-commit 통과, 시험 21개, 변이 11 모두 기대대로, 카나리아 둘 통과 4). 커밋하지 않은 변경은 일지 하나(인용 경고 고침과 인계 절)이고 아직 푸시하지 않았으며 PR도 없다. 남은 단계는 PR 직전 리뷰(CodeRabbit CLI는 좌석이 없어 대체 둘. bug-perf-review 브리프에 일지 셀프 리뷰 (둘째) 절 고친 것 줄의 새 문장을 밀 주장으로 나열한다)와 반영, 일지 커밋, 푸시와 PR(PR 체크리스트에 대체 둘의 결과를 적는다), 봇 회차, 병합, 일지의 "다음" 절과 회고다. docs/journal/2026-10-22-21-ui-design-skill.md
확인할 선행 조건: 주 체크아웃은 main이고 origin/main(96fbe241)과 같다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. sibling_overlap이 함께 고친 파일로 PR #296·#297·#350과 워크트리 03-commit-check-blocks-ticketless·bug-perf-review-batch·mcp-shutdown-spec·measure-word-hook을 들었다. 그쪽이 먼저 병합되면 origin/main을 합칠 때 충돌을 본다
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-22T11:37:24Z

## 이어 한 세션 (셋째)

새 세션이 제목을 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. origin/main이 `e62eb052`(PR #350, 티켓 없는 브랜치의 커밋을 막는 검사)로 움직여, 이 일지를 커밋한 뒤 합친다.

일지만 바꾼 첫 커밋 시도에서 pre-commit의 pytest가 `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다` 하나로 실패했다(4261 통과). 자식 파이썬이 `drain(0.5)` 안에 한 줄도 내지 못한 것이고, 같은 때 web-verify가 함께 돌았다. 그 파일만 단독으로 치자 15개 통과였다. 대기열에 이 시험의 흔들림 기록은 없어 회고 후보로 둔다. 다시 친 커밋은 pytest까지 통과했다.

## PR 직전 리뷰 (둘째)

`bug-perf-review`(범위 `96fbe241...4c302a9b`)에 셀프 리뷰 둘째 절의 고친 것 여덟을 밀 주장으로 넘겼다. Critical·Major 없이 Minor 4(유효)·Nit 1(보류)이었고, 훅의 `design_slug`는 역슬래시·드라이브 문자·대소문자·`..`·UNC 입력 열여섯을 함수에 넣어 반례가 없었다. 넷 모두 값이 작아 PR 전에 스킬에서 고쳤다.

- 7단계 허용 목록이 윈도 예약 이름을 마지막 확장자만 떼고 대어 `CON.tar.gz`를 지나보냈고, 대소문자와 유니코드 숫자를 가르지 않았다. 숫자를 ASCII로 좁히고 첫 `.` 앞의 이름을 대소문자 없이 대게 고쳤다(셀프 리뷰 셋째가 다시 고쳤다).
- 저장소가 그 폴더에 쓰는 파일과의 견줌이 대소문자를 갈라 `readme.md`가 윈도에서 `README.md`를 덮어쓸 수 있었다. 대소문자 없이 견주고 색인 안의 대소문자만 다른 경로도 옮기지 않게 고쳤다.
- 7단계에 sha256이 다를 때의 갈래가 없었다. README 표를 채우지 않고 알리는 갈래를 더했다(셀프 리뷰 셋째가 다시 고쳤다). 웹 편집 확인은 sha256이 다르면 CRLF를 LF로 바꿔 `diff`로 다시 맞대게 했다(`eol=lf`가 커밋 때 줄바꿈을 바꾸므로).
- 웹 편집 확인의 "커밋한 뒤에 다시 맞댄다"가 읽기만 하는 세션에게 남의 파일을 커밋하라는 말이 될 수 있었다. 옮긴 세션이 커밋한다고 좁혔다.

남긴 것(Nit, 보류): 웹 편집 확인의 `git show "HEAD:<경로>"`는 따옴표 인자라 워크트리 세션의 가드가 거부할 수 있다. 공백과 한글이 든 파일 이름이 있어 따옴표를 뺄 수 없고, 거부되면 그 세션이 우회(파일로 경로를 넘기기)를 고른다. 첫 웹 편집 확인에서 본다.

카나리아 둘은 다시 돌리지 않았다. 기대값(5단계의 굵은 글씨와 폴더 이름)이 고친 7단계·웹 편집 확인과 겹치지 않고, 이번 고침은 스킬이 실리는지를 바꾸지 않는다.

origin/main(`e62eb052`)을 충돌 없이 합쳤다. 새 `tools/check_ticket.py`는 이 브랜치를 "규약 전에 연 브랜치"로 지나보냈다.

## 셀프 리뷰 (셋째)

`/code-review`(고정점 `b98be1cd`, 스테이지한 두 파일, 커밋 0, 미추적 0). 표준 축(sonnet·high)은 Major 2·Minor 3·Nit 4와 smell 넷, 명세 축은 Minor 3·Nit 1을 냈다. 두 축 모두 이 PC에서 예약 이름 파일을 실제로 써 봤다.

고친 것. 반영하며 새로 쓴 문장은 PR 직전 리뷰에 밀 주장이다.
- 예약 이름 견줌이 첫 `.` 앞 이름의 끝 공백을 남겨 `con .txt`를 지나보냈다(두 축, 표준 Major). 두 축이 써 보니 장치로 빠져 내용이 사라졌다. 고친 문장: "첫 `.` 앞의 이름에서 끝 공백을 뗀 것이 대소문자를 가리지 않고 윈도 예약 이름(`CON`, `PRN`, `AUX`, `NUL`, `COM1`~`COM9`, `LPT1`~`LPT9`)이 아닌 것만 옮긴다(`C:`, `..`, `\`, 대체 스트림의 `:`, `.git`, `con.tar.gz`, `con .txt`가 여기서 걸린다. 윈도는 예약 이름에 쓴 내용을 장치로 보내 버린다)."
- sha256이 다른 화면이 검증하지 못한 파일을 `design/`에 남기고 이어지지 않았다(표준 Major). 옮긴 파일을 작업 트리에서 지우고 다시 옮길지 묻게 고쳤다(PR 직전 리뷰 셋째가 다시 고쳤다).
- 옮기지 않은 경로를 알리는 말이 "그 밖의 경로도"에만 걸렸고 끝 조건에 그 갈래가 없었다(두 축). 고친 문장: "옮기지 않은 경로는 모두 까닭과 함께 사람에게 알린다." 끝 조건: "고른 화면마다 파일이 `design/`에 있고 README 표에 줄이 있거나, 옮기지 못한 까닭을 사람에게 알려 사람이 그 화면을 어떻게 할지 답했으며".
- 대소문자 견줌이 `design/`에 이미 있는 파일과 디렉터리 조각을 빼먹었다(두 축). 고친 문장: "옮긴 곳이 이 저장소가 그 폴더에 쓰는 파일(`README.md`, `*-prompt.md`, 충돌 목록)과 같거나 대소문자만 다를 때, 그리고 `design/`에 이미 있는 파일이나 색인 안의 다른 경로와 조각의 대소문자만 다를 때는 옮기지 않는다."
- 웹 편집 확인의 "옮긴 세션이 커밋한 뒤"는 그 자리를 밟을 계기가 없었다(두 축). 7단계에 "옮긴 파일과 README 표는 이 세션의 다음 커밋에 넣는다"를 두고, 웹 편집 확인은 까닭을 `git status --short -- <경로>`로 가르게 했다(나오면 아직 커밋하지 않은 것, 나오지 않으면 커밋한 뒤 옮기거나 지운 것).
- 줄바꿈을 바꾸는 쪽을 `text=auto eol=lf`로 고쳤고(표준 Nit, 임시 저장소에서 재현), 아티팩트 파일의 줄바꿈을 재지 못한 것에 더했다(표준 Minor).

남긴 것.
- `docs/agents/issue-tracker.md`의 웹 편집 줄은 sha256으로 가른다고만 적는다(표준 Minor). 그 절은 요지이고 절차의 원천은 스킬이라, 줄바꿈 갈래는 스킬에만 둔다.
- 훅 `design_slug`가 윈도의 뒤 점 별칭(`design./x.html`은 `design/`에 써진다)을 놓친다(표준, diff 밖). Write·Edit 페이로드에서 그 경로가 올 일이 드물어 회고 후보로 둔다.
- 7단계 한 단락에 규칙이 모인 sprawl, 경로 판정 규칙이 스킬·`tools.md`·훅에 흩어진 것, 금지문의 긍정 짝, 본문의 변경 이력 괄호는 smell 판단 항목이다. 이번에 괄호의 이력("허용 목록으로 좁혔다")은 뺐다.
- `sha256sum`을 파이프로 치면 가드와 `$?` 함정에 걸릴 수 있다(표준 Nit). 스킬은 명령 모양을 정하지 않는다.

카나리아 기대값은 바뀐 7단계·웹 편집 확인과 여전히 겹치지 않는다(두 축이 확인).

커밋 `0018f0d5`(pre-commit 통과. check-ticket, pyright 둘, web-verify, pytest 등 모두 Passed, 인용 대조 경고 없음).

## PR 직전 리뷰 (셋째)

`/security-review`(커밋 `0018f0d5`, origin/main `e62eb052`을 합친 뒤)는 신뢰도 8 이상의 지적이 없었다. 실행 코드는 훅 하나이고, 표지 이름은 sha256 해시라 경로를 벗어나지 못하며, `O_EXCL`로 만들고, 셸·`subprocess`·`eval`이 없다. 그 명령이 모은 커밋 목록에는 합친 뒤 main에 병합된 PR #351이 섞여, 하위 작업에 범위를 `e62eb052..0018f0d5`로 좁혀 넘겼다.

`bug-perf-review`(셀프 리뷰 셋째의 새 문장 여섯을 밀 주장으로)는 Major 1·Minor 1(유효), 보류 1, 오탐 1을 냈다. 예약 이름 주장은 끝 점·탭·`CONIN$`·디렉터리 조각에서도 성립했다.

- Major: 웹 편집 뒤 다시 옮기다 sha256이 어긋나면 "작업 트리에서 지운다"가 커밋된 옛 판을 지우고 다음 커밋이 그 삭제를 담는다. HEAD에 있는 파일은 되돌리고 없는 파일은 지우게 고쳤다(셀프 리뷰 넷째가 명령을 바로잡았다).
- Minor: 색인에 `a.html`과 `a.html/b.js`가 함께 있으면 둘째를 쓸 때 실패한다. 한쪽이 다른 쪽의 폴더 조각이면 옮기지 않게 고쳤다(셀프 리뷰 넷째가 대소문자 갈래를 더했다).
- 보류: 7단계의 sha256 대조에는 웹 편집 확인의 CRLF 갈래가 없다. 쓰는 도구가 줄바꿈을 바꾸는지는 읽기로 닫히지 않고, 어긋나면 위의 되돌림과 사람에게 묻는 길을 탄다. 첫 옮기기에서 본다(재지 못한 것의 줄바꿈 줄).
- 오탐: 대소문자 견줌이 같은 이름의 정상 재이동을 막는다는 것. 같은 철자는 대소문자만 다른 것이 아니다.

## 셀프 리뷰 (넷째)

`/code-review`(고정점 `0018f0d5`, 미커밋 두 파일, 커밋 0, 미추적 0). 두 축이 같은 Major를 냈다.

고친 것. 반영하며 새로 쓴 문장은 PR 봇이 겨냥할 주장이다.
- `git restore -- <경로>`는 `--source`가 없으면 HEAD가 아니라 인덱스에서 되살려, 이미 스테이지한 파일은 검증하지 못한 판이 남았다. 새로 스테이지한 파일은 지워도 `AD`로 남아 커밋에 든다(두 축, Major, 두 축 모두 임시 저장소에서 쳤다). 고친 명령을 세션 스크래치패드의 임시 저장소에서 쳐 봤다. 스테이지한 뒤 덮어쓴 파일이 HEAD 판으로 돌아왔고, 새로 스테이지한 파일은 인덱스와 작업 트리에서 빠졌으며, 없는 경로는 오류 없이 지났다(git 2.32). 고친 문장: "다르면 sha256이 다른 파일만 되돌리고(HEAD에 있으면 `git restore --source=HEAD --staged --worktree -- <경로>`, 없으면 `git rm --cached --ignore-unmatch -- <경로>` 뒤 그 파일을 지운다. 이미 스테이지했어도 그렇게 된다) 그 화면의 README 줄을 고치지 않은 채, 그 화면을 다시 옮길지 사람에게 묻는다."
- 화면끼리 함께 쓰는 파일(`canvas.json`, 지원 파일)을 한 화면이 어긋났다고 되돌려 다른 화면의 줄이 깨진 파일을 가리켰다(두 축, Minor). 위 문장의 "sha256이 다른 파일만"이 받는다.
- 폴더 조각 갈래의 까닭이 없었고(표준 Minor) 대소문자와 겹친 경우가 비었다(명세 Nit). "대소문자를 가리지 않고 한쪽이 다른 쪽의 폴더 조각일 때"와 "같은 이름의 파일과 폴더는 함께 둘 수 없다"를 더했다.
- 일지가 7단계의 줄바꿈 갈래를 넘긴 재지 못한 것의 줄이 웹 편집 확인만 말했다(명세 Minor). 그 줄에 7에서 옮긴 파일이 받은 바이트 그대로인지와, 7에는 줄바꿈 갈래가 없어 되돌림과 묻기로 간다는 것을 더했다.

남긴 것: 7단계 한 단락의 sprawl과 일지가 고친 문장을 통째로 인용해 낡기 쉬운 것(표준, smell 판단 항목). 7단계를 쪼개는 일은 첫 옮기기에서 실제 막힘을 본 뒤에 한다.

PR 직전 리뷰는 다시 돌리지 않는다. 이번 문장은 두 축이 명령을 쳐 본 것을 그대로 옮긴 것이고, 다음 층은 PR 봇이다.

커밋 `8eb340da`(pre-commit 통과, 인용 대조 경고 하나는 그 뒤 따옴표를 떼어 고쳤다). 푸시 직전 origin/main이 `c47bedce`(PR #351)로 움직여 합쳤고(충돌 없음), `sibling_overlap.py`가 main의 최신 일지 2026-10-22-16보다 이 일지가 이름순으로 앞선다고 해 `--move`로 이 일지를 2026-10-22-21로 옮겼다. 인용을 고친 파일은 스킬, 프로브 README, 카나리아 명세 셋이고, 옛 번호의 잔존은 0이다.
