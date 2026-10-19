# 2026-10-19 (23) 워크트리 스킬 끄기 훅을 이 PC의 앱에서 확인하다

브랜치 `chore/worktree-overrides-pc-check`. 일지 2026-10-19-14의 "다음"이 남긴 확인, 곧 #304의 훅
`tools/hook_worktree_skill_overrides.py`(대기열 274)가 이 PC의 데스크톱 앱에서도 먹는지를 실제 `EnterWorktree`로 했다. 데스크톱
앱 세션(기록 줄의 `version`으로 Claude Code 2.1.299)이 주 체크아웃에서 시작해 워크트리에 들어갔다. 지시문은 클라우드 세션이
냈고, 확인 절차(일곱 걸음)는 그 세션이 짜서 지시문의 "이어받을 상태"에만 있었다.

> 사용자: #304 뒤 이 PC의 데스크톱 앱에서 두 가지를 확인한다. 하나, 주 체크아웃의 .claude/settings.local.json 이 git status 에
> 나오지 않는다. 둘, 주 체크아웃의 스킬 파일이 바뀐 뒤에도 그 워크트리의 스킬 사본이 경로를 단
> 이름(.claude/worktrees/<워크트리>:<스킬>)으로 스킬 목록에 붙지 않는다. 결과를 일지와 훅 독스트링의 못 보는 것에 적는다

결과는 하나는 기대대로, 둘은 기대와 달랐다. 지시문은 기대와 다르면 고치지 않고 원인 후보와 함께 보고하라고 해서 훅은 고치지
않았고, 측정과 그 결과에 어긋나는 문장만 고쳤다.

## 한 일

### 앞 단계

- `tidy-checkouts`: 지시문은 주 체크아웃 미갱신이라 했지만, 세션이 시작될 때 루트는 이미 `main` 5f38d61(= `origin/main`, #304)이었다.
  당길 것도 지울 것도 없었다. 병합된 PR이 없는 워크트리 열과, 세션 프로세스가 작업 디렉터리로 쥔 병합된 워크트리 여덟을
  남겼다. 사람에게 넘긴 셋은 분리 HEAD 커밋이 `origin/main`에 없는 `confident-wright-2d3ebf`·`elegant-dijkstra-aaddb9`와, 병합된 PR의
  머리와 브랜치 끝이 다른 `skill-check-and-retro-section`이다. 지시문대로 답을 기다리지 않았다.
- 루트가 이미 #304였으므로 이 세션의 훅 등록도 #304의 것이다. 지시문이 걱정한 "세션 도중에 당긴 등록"은 이 측정에 끼지 않는다.
- `EnterWorktree(name=worktree-overrides-pc-check)`로 들어가 브랜치를 `git branch -m`으로 바꿨다.

### 하나: 주 체크아웃의 local 설정이 `git status`에 나오지 않는다

- 들어가기 전 주 체크아웃에서 `git check-ignore -v .claude/settings.local.json`이
  `"C:\\Users\\User/.config/git/ignore":3:**/.claude/settings.local.json`(그 뒤 탭과 경로)을 냈다. 저장소의 `.gitignore`가 아니라
  사용자 전역 ignore다.
- 그때 local에는 다른 앱 세션 둘(`mutate-ctrl-c-under-load`, `sibling-overlap-batch`)의 `EnterWorktree`에서 이 훅이 적은 키가 서른둘
  있었고, `git status --porcelain`은 stdout과 stderr가 모두 비었다. 그러니 이 PC의 앱 세션에서 훅이 쓴 파일이 `git status`에
  나오지 않는 것은 이미 일어난 사실로 봤다.
- 들어간 뒤 `git -C C:/project/agent status --porcelain`은 워크트리 세션의 가드가 "redirects git to the shared checkout via -C"라며
  거부했다. 무시 규칙은 경로로 걸리므로 들어가기 전의 확인을 결과로 둔다.

### 둘: 경로를 단 이름이 꺼지는가

- 들어가자 훅이 이 워크트리의 스킬 열여섯(폴더 수와 같다)에 `"off"`를 적었다. 주 체크아웃의 local을 이 워크트리 접두의 줄만
  Grep으로 봤다.
- 양성 대조로 워크트리에 새 스킬 `.claude/skills/late-check/SKILL.md`를 만들었다. 그 뒤 몇 분 동안 도구 호출을 여러 번 했는데도
  `skill_listing` 추가분이 하나도 없었다. 만든 것만으로는 목록에 실리지 않았다.
- 들어간 뒤 이 세션의 기록 파일이 `~/.claude/projects/C--project-agent/`에서 사라지고 워크트리 이름의 프로젝트 폴더
  `C--project-agent--claude-worktrees-worktree-overrides-pc-check/`로 옮겨졌다. 옮긴 파일에 첫 목록(12번째 줄)부터 세션 전체가
  있었다. 지시문의 (5)가 적은 자리(주 체크아웃 폴더)는 이 판에서 맞지 않았다.
- 기준 줄 366을 적고 사람에게 주 체크아웃의 `.claude/skills/tdd/SKILL.md` 끝에 빈 줄을 더해 달라고 했다. 사람이 저장하고 다음
  메시지를 보냈다(파일의 수정 시각 17:29:13 +0900).
- 17초 뒤(08:29:30Z) 378번째 줄에 추가분 하나가 붙었다. 훅이 끈 이름 가운데 목록에 실리는 열하나가 모두 경로를 단 이름으로
  들었고, `late-check`가 맨 이름으로, 주 체크아웃의 스킬 넷(`diagnosing-bugs`, `domain-modeling`, `tdd`, `writing-for-agents`)이 맨
  이름으로 다시 들었다(넷이 왜 다시 실렸는지는 보지 않았다). 끈 열여섯 가운데 나머지 다섯(`grill-me`, `implement`,
  `setup-matt-pocock-skills`, `to-spec`, `to-tickets`)은 머리말이 `disable-model-invocation: true`라 원래 목록에 없다. 그 턴에 모델에게
  보인 스킬 목록에도 경로를 단 이름이 "scoped to … use this instead of the unscoped …" 설명과 함께, `late-check`가 "from
  …/.claude/skills — applies when working on files under …" 설명과 함께 실렸다.
- 판정 스크립트의 첫 판(세션 스크래치패드)은 표지를 경로를 단 `late-check`로만 잡아 "측정 아님"을 냈다. 원본을 보니 앱은 주
  체크아웃에 같은 이름의 스킬이 있는 사본에만 경로를 달았다. 표지의 뜻(목록이 워크트리 사본을 다시 훑었다)은 맨 이름으로도
  서므로 두 꼴을 다 받게 넓혀 `.scratch/harness/probes/worktree_overrides_app.py`로 옮겼고, 측정이고 실패로 판정됐다.
- 원인 후보는 셋이고 가르지 않았다. 하나, 들어간 뒤 세션이 워크트리의 local을 읽는다. 기록 파일이 옮겨졌고 첨부의 `cwd`가
  워크트리였으며, 워크트리의 local 사본에는 `skillOverrides` 줄은 있어도 이 워크트리의 키가 없었다(워크트리를 만들 때 복사된 뒤에
  훅이 주 체크아웃에만 썼다). CLI 프로브는 `git worktree add`로 만들어 local 사본이 없는 워크트리에 `EnterWorktree(path)`로
  들어갔다. 둘, 2.1.299가 경로를 단 키를 맞추지 않는다. 앱이 묶은 실행 파일
  (`%APPDATA%\Claude\claude-code\2.1.299\…\claude.exe`)에서 `skillOverrides`가 든 줄은 `grep -a -c`로 19였다. 셋, Windows에서
  바꿔 끼운(`os.replace`) 파일을 설정 감시가 보지 못한다.
- `late-check`는 판정 뒤 지웠고, 사람에게 빈 줄을 되돌려 달라고 했다.

### 기록

- 프로브 `.scratch/harness/probes/worktree_overrides_app.py`와 README 행. 앱 세션은 스크립트로 띄울 수 없어 절차는 독스트링에 적고
  판정만 한다.
- 훅 독스트링: 머리 문단에 앱 세션에서는 붙었다는 한 문장, 못 보는 것의 "데스크톱 앱이 묶은 판" 항목을 측정 결과와 원인 후보로
  바꾸고 "Windows에서 세션이 읽는 local의 자리" 항목을 그 안의 셋째 후보로 합쳤다.
- 작업 규약 4로 "훅이 돈 세션에서는 꺼진다"는 살아 있는 문장 셋을 CLI의 측정이라고 좁히고 앱 세션의 결과를 더했다.
  `docs/constitution/operations.md` 환경 규약 상세의 워크트리 항목(헌법 3.0.45), `tools/hook_grill_design_check.py` 독스트링,
  `.claude/rules/tools.md`의 Skill 훅 문장이다. 일지와 닫힌 대기열 행은 그때의 기록이라 두었다.
- `.claude/rules/tools.md`를 고쳐 `tools/sibling_overlap.py`가 카나리아를 요구했다(종료 1). 바꾼 조각을 기대값으로 든 명세
  `.scratch/harness/probes/canary/tools_rule_worktree_skill_overrides.toml`의 머리 주석과 넷째 기대값("그 이름이 꺼져 있다" →
  "이 PC의 앱 세션에서는 붙었다")을 고치고, 앞 결과를 `# 이전 결과:` 줄(선례 `tests_rule_pwsh_linux.toml`)로 내렸다.

## 검사

- `uv run ruff check .`, `uv run ruff format --check .`가 초록이었다(788 파일).
- 카나리아 `tools_rule_worktree_skill_overrides.toml`이 통과 4였다(이 PC, claude 2.1.302, 갈래 커밋 5f38d61 위의 커밋하지 않은 판).
  실험군 셋이 새 조각을 글자 그대로 옮겼고 대조군은 "없음"이었다. `uv run python tools/canary.py --shape`도 통과였다.
- `uv run python tools/run_checks.py`를 백그라운드로 띄웠는데 인계 때문에 멈췄다. 멈추기 전에 zizmor, 지침, 경계, 타입 우회,
  pyright, 훅 러너(379초)가 지났고 pytest와 web은 결과를 보지 못했다. 새 세션이 다시 돈다.
- 새 워크트리라 처음 `uv run`이 `.venv`에 패키지 85개를 까는 데 2분 27초가 걸렸다.

## 인계

셀프 리뷰 직전에 인계 계기(`hook_handoff`, 세션 컨텍스트 298,701 토큰)가 왔다. `code-review`를 부른 직후라 그 단계는 밟지 않았다.
인계하지 않는 때 다섯에 들지 않았다(계기를 낸 호출은 성공했고, 요청 범위는 병합까지이며, 지시문의 이어받을 상태는 `인계:`로
시작하지 않고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다). 이 세션의 지금 제목은
`chore/worktree-overrides-pc-check`이고 `chore/worktree-overrides-pc-check (인계함)`으로 바꾼다. 차례로는 제목이 먼저인데 백그라운드
검사를 먼저 멈췄다.

남은 순서(지시문의 이어받을 상태가 가리킨다):

1. 셀프 리뷰 `/code-review 5f38d61`. 추적하지 않는 새 파일 둘(`.scratch/harness/probes/worktree_overrides_app.py`, 이 일지)을
   범위에 넣는다. 측정은 끝났고(측정이고 실패, 앱 2.1.299에서 훅의 키가 경로를 단 이름 열하나를 끄지 못했다) 지시문대로 훅은
   고치지 않았다.
2. `uv run python tools/run_checks.py`를 다시 돈다. 앞 회차는 pytest·web 전에 멈췄다.
3. 커밋하고, 기준 브랜치를 합친다(`origin/main`이 `.scratch/harness/probes/README.md`를 고쳤다). PR을 열고 병합한다.
4. 병합 뒤 지시문의 (7)대로 워크트리를 지우고, 주 체크아웃에서 `git status --porcelain`에 `.claude/settings.local.json`이 없는지 한
   번 더 본다(워크트리 안에서는 `git -C`가 가드에 막혔다).
5. 원인을 가르는 실험은 이 요청 범위 밖이라 후속 세션 제안으로 남긴다.
6. 사람이 주 체크아웃의 `.claude/skills/tdd/SKILL.md` 끝에 더한 빈 줄을 되돌렸는지 본다. 이 세션이 두 번 부탁했고 마지막에 본 끝
   바이트는 `\r\n\r\n`이었다(워크트리 사본은 LF로 끝난다. 편집기가 줄 끝을 CRLF로 바꿨을 수 있다). 주 체크아웃의 `git status`가
   깨끗하지 않으면 사람에게 다시 부탁한다.

제목을 바꿨고(앱이 묻지 않고 바꿨다), `git worktree unlock C:/project/agent/.claude/worktrees/worktree-overrides-pc-check`가 출력
없이 지났다.

open-session을 부른다 2026-10-19T09:07:32Z

첫 열기는 `tools/open_session.ps1`이 URL 8062자(상한 8000)로 쏘기 전에 거부했다(`fired=` 전이라 세션은 생기지 않았다). 지시문의
이어받을 상태와 확인할 선행 조건의 세부를 위 남은 순서로 옮기고 줄인 지시문을 새 파일로 다시 연다.

넘기는 지시문:

```
다음 작업: #304의 훅(tools/hook_worktree_skill_overrides.py, 대기열 274)이 이 PC의 데스크톱 앱에서도 먹는지 실제 EnterWorktree로 확인하고 결과를 기록한다
다음 단계: 구현(실제 실행 확인과 기록)
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: #304 뒤 이 PC의 데스크톱 앱에서 두 가지를 확인한다. 하나, 주 체크아웃의 .claude/settings.local.json 이 git status 에 나오지 않는다. 둘, 주 체크아웃의 스킬 파일이 바뀐 뒤에도 그 워크트리의 스킬 사본이 경로를 단 이름(.claude/worktrees/<워크트리>:<스킬>)으로 스킬 목록에 붙지 않는다. 결과를 일지와 훅 독스트링의 못 보는 것에 적는다
브랜치: chore/worktree-overrides-pc-check
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-23-worktree-overrides-pc-check.md 전체
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review 5f38d61, 추적하지 않는 새 파일 둘 포함)부터 한다. 측정은 끝났고(실패) 훅은 고치지 않았다. 남은 순서는 일지의 인계 절. 일지 docs/journal/2026-10-19-23-worktree-overrides-pc-check.md
확인할 선행 조건: 사람이 주 체크아웃의 .claude/skills/tdd/SKILL.md 끝에 더한 빈 줄을 되돌렸는지(이 세션은 확인하지 못했다)
이번 요청 범위: 확인과 기록(일지, 훅 독스트링의 못 보는 것)의 PR과 병합까지
```

open-session을 부른다 2026-10-19T09:09:53Z

## 이어받은 세션

- 제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path=C:/project/agent/.claude/worktrees/worktree-overrides-pc-check)`로 들어갔다.
- 확인할 선행 조건: 주 체크아웃의 `.claude/skills/tdd/SKILL.md`에는 빈 줄이 아직 남아 있었다. 줄 끝의 `\r`을 지우고 워크트리
  사본과 견주면 39번째 줄(빈 줄) 하나만 달랐고, 끝 바이트는 `\r\n\r\n`이었다. 사람에게 다시 부탁했다.
- 이 세션이 주 체크아웃에서 시작할 때 앱이 넣은 git status 스냅샷에는 `M .claude/skills/tdd/SKILL.md` 하나만 있었고
  `.claude/settings.local.json`은 없었다. 확인 하나를 두 번째로 본 것이다.
- 이 세션도 `EnterWorktree(path)` 뒤 기록 파일이 `~/.claude/projects/C--project-agent/`에서 사라지고 워크트리 이름의 프로젝트
  폴더에 있었다. 앞 세션의 `EnterWorktree(name)`과 같은 모양이다(손으로 봤다).
- 앞 세션이 멈춘 `run_checks.py`가 `web/eslint.config.test.ts`의 임시 폴더 `web/judge-jZnujf/`를 남겼다(`afterAll`이 돌지
  못했다). 테스트의 정리와 같은 Node `rmSync`로 지웠고, 그 안의 junction이 가리키던 `web/packages/api-client`는 그대로였다.
- 인계 절 남은 순서 4의 "지시문의 (7)"은 넘긴 지시문에는 없고 앞 세션이 받은 지시문에만 있었다. 뜻은 병합 뒤 이 워크트리를
  지우는 것이다. 그 뒤 주 체크아웃의 `git status`를 다시 본 결과는 아래 병합 절에 적는다.

## 셀프 리뷰

`/code-review 5f38d61`(base `5f38d61c`, 바뀐 파일 일곱, 커밋 0, 추적하지 않는 새 파일 둘). 표준 축은 sonnet·high, 명세 축은 이
세션의 모델이다. 명세는 사용자 요청이고, 앞 지시문의 "기대와 다르면 고치지 않고 원인 후보와 함께 보고"를 요구에 넣었다.

표준 축(Major 2, Minor 3, Nit 3):
- (Major) 훅이 사용자에게 내는 알림의 끝 문장 "주 체크아웃의 스킬이 바뀌어도 경로를 단 사본이 목록에 붙지 않는다."가 이 측정과
  어긋난다. 작업 규약 4의 잔존이다. → 고쳤다. 동작은 그대로 두고 문장만 CLI와 이 PC의 앱 세션의 결과로 나눴고, 그 줄을 쥔 변이
  명세 `worktree_skill_overrides_hook_mutations.toml`의 대조군 원문도 옮겼다. 훅의 판정을 고친 것이 아니라 지시문의 "고치지
  않는다"에 들지 않는다고 봤다.
- (Major) 프로브 독스트링의 전제 "추가분은 늘어난 이름만 담으므로(다른 세션 기록의 추가분이 이름 1~4개였다)"가 기록과 어긋난다.
  378번째 줄에 첫 목록의 이름 넷이 다시 들었다. → 고쳤다. `late-check`가 기준 줄 앞에 실리면 측정이 아닌 까닭을 "목록이 사람의
  편집 전에 워크트리를 다시 훑었다"로 바꿨다. 판정 코드는 그대로다.
- (Minor) "앱 2.1.299 는 주 체크아웃에 같은 이름의 스킬이 있는 사본에만 경로를 달고"는 한 회차의 일반화다. → 프로브 독스트링과
  README 행을 그 회차의 관찰로 좁혔다. 이 일지 위 "둘" 절의 같은 문장은 그때의 기록이라 두었다.
- (Minor) 합친 항목에서 공식 문서 settings 인용이 후보 셋 뒤에 붙어 후보 하나의 근거가 엉뚱한 자리에 있었다. → 후보 하나 안으로
  옮기고, 옛 항목에 있던 어림("운영 규약의 모드 표에 기대어 주 체크아웃의 local 로 보았다")을 되살려 이 후보가 맞으면 그 어림이
  틀렸다고 적었다.
- (Minor) 프로브 3걸음의 "기준 줄을 크게 주어 돌리면 `additions_before` 가 빈다"가 거꾸로 읽힌다. 인자 오류도 종료 1로 섞인다. →
  3걸음을 "모든 추가분이 `additions_before`에 담기고 거기에 `late-check`가 없어야 한다"로 고쳤고, 인자가 넷이 아니면 2로
  끝나게 했다. 기준 줄 1000000으로 돌려 `not_measured_because`에 "late-check 가 기준 줄 앞 추가분에 이미 실렸다"가 뜨는 것과,
  인자 셋으로 종료 2를 봤다.
- (Nit) `.claude/skills/late-check/` 빈 폴더가 남았다. → 지웠다. (Nit) "실행 파일에 `skillOverrides` 는 있었다"는 후보 둘의
  근거가 못 된다. → 손으로 본 것이고 그 판이 설정을 안다는 것만 보인다고 고쳤다. (Nit) 프로브가 판정 때 local을 다시 읽는다. →
  명세 축의 Major와 같은 지적이라 함께 고쳤다(아래).
- (남김) 앱이 보낸 `EnterWorktree(name)` 페이로드 모양(`tool_input`에 `name`만)을 고정한 테스트가 없다. 훅은 결과의
  `worktreePath`를 먼저 읽고, 그 갈래는 `test_주_체크아웃의_워크트리_자리로_들어간_호출만_고른다`가 이미 고정한다. 앱의 결과에
  `worktreePath`가 있었으므로(앞 세션 기록의 그 호출의 `toolUseResult`, 손으로 봤다) 입력의 `name`은 판정에 닿지 않는다.

명세 축(Major 1, Minor 3, Nit 2, 범위 넘침 없음):
- (Major) 프로브는 훅의 키를 판정할 때 local에서 읽어, 이 워크트리를 지운 뒤 누구든 `EnterWorktree`를 하면 훅이 그 키를 걷고
  같은 명령이 "측정 아님"을 낸다. 기록 경로도 저장소에 없다. → 주 체크아웃의 local에서 이 워크트리 접두의 키 열여섯만 꺼내
  `.scratch/harness/probes/worktree_overrides_app_keys.json`으로 옮겼다(다른 설정 값은 옮기지 않았다, 키 열여섯은 스킬 폴더
  열여섯과 같았다). README 행의 판정 명령이 그 파일을 셋째 인자로 쓰고, 기록 파일의 자리를 적었다. 그 파일로 다시 돌려 측정이고
  실패, `hooked` 16, `leaked` 11로 같았다. 프로브 독스트링의 못 보는 것에 측정 때의 키를 더했다.
- (Minor) 확인 하나의 결과가 데스크톱 앱 항목의 셋째 후보 뒤에 붙어 그 근거처럼 읽히고, 원래 항목 "local 설정이 git 에서
  무시되는지"는 고치지 않았다. → 그 결과를 원래 항목으로 옮겼다.
- (Minor) 프로브 전제 "늘어난 이름만" → 표준 축 Major와 같이 고쳤다.
- (Minor) 고친 문서들이 차이를 CLI와 앱으로 갈랐는데, 후보 하나는 워크트리를 만든 길(local 사본의 유무)의 차이다. → 그 추론을
  하는 `operations.md`("그래서 앱 세션에서는…")에 두 측정의 조건(`git worktree add`+`EnterWorktree(path)`와
  `EnterWorktree(name)`)과 무엇이 갈랐는지 가르지 않았다는 문장을 넣었고, 훅 독스트링 후보 하나에 "갈린 것은 앱과 CLI 가 아니라
  워크트리에 local 사본이 있었는지일 수 있다"를 넣었다. `.claude/rules/tools.md`와 `tools/hook_grill_design_check.py`의 괄호와 훅
  알림은 두 결과를 나란히 적을 뿐 까닭을 말하지 않고 그 훅의 못 보는 것을 가리켜 두었다. `rules/tools.md`를 다시 고치면 카나리아를
  다시 돌려야 하는데 뜻이 바뀌지 않는다.
- (Nit) `late-check`를 지웠다면서 빈 폴더가 남았다 → 지웠다. (Nit) 일지가 옮긴 `check-ignore` 출력이 원문과 다르다 → 이
  워크트리에서 다시 친 출력(`"C:\\Users\\User/.config/git/ignore":3:…`)으로 고쳤다. (Nit) "지시문의 (7)"이 넘긴 지시문에 없다 →
  위 이어받은 세션 절에 뜻을 적었다.

두 축이 함께 맞다고 잰 것: 17초·378번째 줄, 키 서른둘(16+16), `disable-model-invocation` 다섯, `grep -a -c` 19, 워크트리 local
사본의 이 워크트리 키 0개, CLI 프로브가 `git worktree add`(350행)로 만들고 `EnterWorktree(path)`로 들어가는 것, 훅 diff가
독스트링뿐이었던 것, 헌법 3.0.45가 patch인 것, 옛 표현("꺼져 있다", "CLI 2.1.303 에서만 쟀다", "데스크톱 앱이 묶은 판")이 살아
있는 문서에 남지 않은 것.

반영하며 새로 쓴 사실 문장(PR 직전 리뷰에 밀 주장):
- 훅 알림: "CLI 세션에서는 주 체크아웃의 스킬이 바뀌어도 경로를 단 사본이 목록에 붙지 않았지만, 이 PC 의 데스크톱 앱 세션에서는
  붙었다."
- 훅 독스트링 local 항목: "이 PC 의 주 체크아웃에서는 사용자 전역 ignore(`~/.config/git/ignore` 의
  `**/.claude/settings.local.json`)가 덮어, 이 PC 의 앱 세션들이 이 훅으로 키를 적은 local 이 `git status` 에 나오지 않았다"
- 훅 독스트링 후보 하나: "이 훅은 운영 규약의 모드 표가 `EnterWorktree` 로 들어온 세션의 훅 등록을 주 체크아웃의 것으로 적은 데
  기대어 그 곁을 주 체크아웃의 local 로 보았는데(어림), 이 후보가 맞으면 그 어림이 틀렸다." "이 후보가 맞으면 갈린 것은 앱과 CLI
  가 아니라 워크트리에 local 사본이 있었는지일 수 있다."
- 훅 독스트링 후보 둘: "실행 파일에 `skillOverrides` 가 든 줄이 있다는 것만 손으로 봤고(`grep -a -c`), 그것은 그 판이 그 설정을
  안다는 것만 보인다"
- `operations.md`: "이것은 CLI에서 `git worktree add`로 만든 워크트리에 `EnterWorktree(path)`로 들어간 측정이다." "그 회차의
  `EnterWorktree(name)`은 워크트리에 local 사본을 남겼고, git이 추적하지 않는 파일이라 `git worktree add`는 남기지 않는다"
- 프로브 독스트링: "2026-10-19 회차의 378번째 줄에 첫 목록의 이름 넷이 맨 이름으로 다시 들었다", 종료 코드 0·1·2와 트레이스백의
  1, 3걸음의 "모든 추가분이 `additions_before` 에 담긴다", 못 보는 것의 "워크트리를 지운 뒤 다른 `EnterWorktree` 에서 훅이 그
  워크트리의 키를 걷으면"
- README 행: "그 회차의 키는 워크트리를 지우면 훅이 걷으므로", 기록 파일의 자리

다시 돌린 명령: 반영 전 `uv run python tools/run_checks.py`(백그라운드)는 zizmor·경계·지침·타입 우회·pyright·훅 러너·web이
통과였고 pytest가 3595 통과, 1 실패였다. 실패는 이 변경이 닿지 않은
`tests/tools/test_hook_midturn_korean.py::test_트랜스크립트_파일이_없으면_기다리지_않는다`의 시간 단언(훅 프로세스 하나가 3.1초, 상한 2초)이고, 리뷰 서브에이전트 둘과
web-verify가 함께 돌던 때다. 그 시험만 홀로 다시 돌리니 통과였다. `.claude/rules/tests.md`의 시간 단언 항목이 말하는 모양이라
후속으로 넘긴다. 반영 뒤 `uv run ruff check`(바꾼 파이썬 둘)가 통과였고, 변이 `대조군: 알림의 끝 문장을 바꾼다` 하나를 돌려
기준선 24 통과와 기대대로 초록을 봤다. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.
