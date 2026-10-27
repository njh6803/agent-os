# 2026-10-27 (16) 화면 코드를 처음 고친 세션에 웹 편집 확인을 알리는 계기 훅 (design-reverse-sync 09)

## 시작

세션을 연 지시문의 시작 프롬프트와 범위다.

> 사용자: /implement .scratch/design-reverse-sync/issues/09-web-edit-hook.md (다음 작업: "화면 코드를 처음 고친 세션에 디자인 시스템의 웹 편집을 확인하라고 한 번 알리는 계기 훅을 더한다", 브랜치 feature/09-web-edit-hook, 모델 Opus 5.5 / xhigh. 레벨 스윕의 갈래, 읽을 것: 일지 docs/journal/2026-10-27-12-first-upload.md 의 "다음", 이어받을 상태: "PR #404의 claude-review 넷째 회차(e7ce64f1)는 고친 것이 없어 일지에 적지 않고 PR 코멘트에만 남겼다. Minor(upload-output.mjs에 시험이 없다)는 대기열 496, Nit(.design-sync/ 아래 새 파일이 빌드 설정인지 가르는 기준이 NOT_BUILD_CONFIG 주석뿐이다)은 보류다. 병합 뒤 원격 브랜치는 새로 켠 자동 삭제가 지웠다(대기열 497의 첫 관찰)", 확인할 선행 조건: "주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다", 이번 요청 범위: PR과 병합까지)

워크트리에 들어가기 전에 주 체크아웃에서 `tidy-checkouts`를 돌았다. 루트(main)를 `4f783dc0`에서 `35028cba`(08의 병합)로 당겼다. 워크트리 `admin-style-to-tickets`와 그 브랜치 `docs/admin-style-to-tickets`는 그 자리를 쥔 쉬는 세션 다섯의 프로세스를 `end-holders`로 끝낸 뒤 지웠고, 로컬 브랜치 `worktree-01-ui-settings-icon-password-widths`·`worktree-02-admin-organisms-take-props`도 지웠다. 휴지통에는 `admin-style-to-tickets`의 `web/node_modules`가 남았다(esbuild·node 프로세스 여섯이 쥐었다). 나머지 워크트리는 병합된 PR 없음, 목록 밖 세션의 프로세스, 바뀐 파일(`06-round-drive-record`), 앱의 표지 때문에 남겼다. 사람에게 넘긴 것은 없다. 그 뒤 `EnterWorktree`(name `09-web-edit-hook`)로 새 워크트리에 들어가 `feature/09-web-edit-hook`으로 바꿨다.

## 구현

티켓 09를 `in-progress`로 바꾸고 고친 것은 아래다. 커밋은 아직 없다.

- 새 훅 `tools/hook_web_edit_check.py`와 시험 `tests/tools/test_hook_web_edit_check.py`(64건). 판정 차례는 경로 → 표지 → 브랜치이고 침묵한 판정도 표지에 남긴다. 작업 트리는 고친 파일에서 위로 `.git`을 찾고, 워크트리의 `.git` 파일은 `gitdir:`를 따라가 `HEAD`를 읽으며 git을 띄우지 않는다. 작업 트리나 `HEAD`를 읽지 못하면 알리는 쪽이다(침묵은 들이기 브랜치를 알아본 때뿐이다). 따로 등록하는 까닭과 못 보는 것은 독스트링에 적었다.
- 등록은 `.claude/settings.json`의 첫 `Write|Edit` 묶음, `hook_ui_design` 뒤다. `tools/hook_payloads.toml`에 발동 둘(메인 세션의 디자인 토큰 CSS Edit, 서브에이전트의 앱 Write)과 침묵 하나(`web/tools` 아래 Edit)를 더했고, `tools/run_hooks.py`가 162건 어긋남 0이었다(도구가 찍은 줄).
- `writing-for-agents`를 부른 뒤 `/sync-design-system`의 설명(`확인` 갈래), 머리 주석의 부르는 쪽, 인자 표의 `확인` 줄에 이 훅의 알림을 더했다. `.claude/rules/tools.md`의 Write·Edit 훅 목록에 여덟째로 더했고 시간은 재지 않고 약 0.2초로 어림한다고 적었다.
- 판단: `KICKOFF.md`도 `hook_ui_design`을 들지만 새 프로젝트에 복사할 화면 디자인 묶음을 적은 런북 줄이라, 이 기능에 딸린 이 훅은 넣지 않았다.
- 변이 표 `.scratch/design-reverse-sync/probes/web_edit_hook_mutations.toml`(변이 18과 대조군 1). 첫 실행은 "변이 19 중 어긋남 4"였다. 6·13은 돌리기 전에 짐작한 시험의 빈틈이었고, 16은 시험이 이 워크트리에서 돌면 프로세스의 작업 폴더가 들이기 꼴 브랜치라 `cwd`를 무시해도 같은 침묵이 난 것이었다(코드 읽기, 고친 뒤의 빨강이 받친다). 17은 빨강이었지만 pytest가 첫 실패에서 멈춰 표지로 고른 시험까지 가지 않았다. 시험 셋을 고치고(잘못된 UTF-8 입력, 티켓 `09-x`, `monkeypatch.chdir`) 17의 표지를 처음 빨개지는 시험으로 바꾼 뒤 넷은 "변이 4 모두 기대대로", 표 전부는 "변이 19 모두 기대대로"였다(도구가 찍은 줄, 커밋하지 않은 작업 트리). 자세한 것은 프로브 README의 "2026-10-27 결과: `web_edit_hook_mutations.toml`" 절이다.
- 카나리아 둘(`.scratch/design-reverse-sync/probes/canary/tools_rule_web_edit_hook.toml`, `sync_design_system_web_edit_hook.toml`)이 claude 2.1.302에서 둘 다 통과 4였다(도구가 찍은 줄. 실험군 세 회차가 고친 문장을 옮겼고 대조군 주 체크아웃 한 회차는 "없음"이었다).
- 고친 것: ruff E501(한글 폭)은 `tools/rewrap_comments.py`와 ruff format으로 다시 감았다. 시험의 FBT001은 parametrize 인자를 알림 문장으로 바꿔 고쳤다. 변이 표에 처음 적은 시험 이름 열이 실제 이름과 달라, 돌리기 전에 시험 파일의 `def test_` 줄을 Grep으로 보고 고쳤다. 시험은 구현 전에 썼지만 구현 전에 돌려 빨강을 보지 않았다. 그 몫을 변이 표가 맡는다.
- `tools/sibling_overlap.py`(일지 번호를 받을 때): 번호 겹침 없음. PR #296·#297과 워크트리 `bug-perf-review-batch`·`measure-word-hook`이 같은 파일 셋(`.claude/rules/tools.md`, `.claude/settings.json`, `tools/hook_payloads.toml`)을 고쳐, 나중에 병합하는 쪽에서 글자 충돌 후보다.

## 인계 (셀프 리뷰 직전)

`/code-review`를 부른 `셀프 리뷰 직전` 경계에서 세션 컨텍스트가 약 27.2만 토큰으로 인계 문턱(20만)을 넘어 `hook_handoff`의 계기가 왔다(계기 문장의 수). 리뷰의 단계는 밟지 않았다(서브에이전트를 띄우지 않았다). 요청 범위가 PR과 병합까지이고, 곁 세션이 아니며(`get_session`의 `self`에 `parentSessionId`가 없다), 지시문의 이어받을 상태가 `인계:`로 시작하지 않고, `인계 못함` 줄이 없어 넘긴다.

- 사용자 프롬프트는 이 세션을 연 지시문 하나뿐이다(위 "시작" 절의 인용). 그 밖에 받은 것은 훅과 백그라운드 작업의 알림이다.
- 결정과 고친 것: 위 "구현" 절.
- 이 세션의 지금 제목: `feature/09-web-edit-hook`. 넘기기 전에 `feature/09-web-edit-hook (인계함)`으로 바꾼다.
- 남은 단계(새 세션이 한다):
  1. 이 일지를 이어 쓴다. 이 브랜치의 변경은 모두 커밋하지 않았다.
  2. `/code-review`. 기점은 `origin/main`이고, 미추적 다섯(`tools/hook_web_edit_check.py`, `tests/tools/test_hook_web_edit_check.py`, 변이 표, 카나리아 명세 둘)과 이 일지를 범위에 넣는다. 명세는 티켓 09와 `.scratch/design-reverse-sync/spec.md`의 "계기 훅"이다. 반영으로 새로 쓴 문장은 PR 직전 리뷰의 밀 주장으로 넘긴다.
  3. 검증 명령. `tools/run_checks.py`는 이 세션이 띄웠다가 끝나기 전에 멈췄다. 린트 둘(`ruff check .`, `ruff format --check .`)은 반영 전 판에서 0이었다.
  4. 티켓 09의 체크박스를 채우고 Status를 `done`으로 바꾼다. 기능은 닫지 않는다. 커밋 뒤 변이 표 전체를 한 번 더 돈다(`tools/mutate.py`가 커밋하지 않은 전체 실행이라고 알렸다).
  5. 커밋, PR 직전 리뷰, PR, 봇 회차, 회고, 병합, 지시문. 병합 뒤 10을 곧바로 돈다(티켓 09 머리).

지시문:

```
다음 작업: .scratch/design-reverse-sync/issues/09-web-edit-hook.md. 화면 코드를 처음 고친 세션에 디자인 시스템의 웹 편집을 확인하라고 한 번 알리는 계기 훅을 더한다
다음 단계: 구현
어디서: 새 세션. 인계라 같은 브랜치를 잇는다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/design-reverse-sync/issues/09-web-edit-hook.md
브랜치: feature/09-web-edit-hook
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 일지 docs/journal/2026-10-27-16-web-edit-hook.md 의 "구현"과 "인계 (셀프 리뷰 직전)" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 훅·시험·등록·페이로드 표·스킬과 규칙 문서·변이 표·카나리아 둘까지 했고(변이 19 모두 기대대로, 카나리아 둘 통과 4), 커밋하지 않은 변경(미추적 다섯 포함)이 워크트리에 있고 셀프 리뷰(/code-review, 기점 origin/main, 미추적 다섯과 이 일지 포함)부터 한다. run_checks는 끝나기 전에 멈췄고 티켓 09의 체크박스는 아직 채우지 않았다: docs/journal/2026-10-27-16-web-edit-hook.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `feature/09-web-edit-hook (인계함)`으로 바꿨고(앱이 묻지 않고 바꿨다), 띄워 둔 `run_checks`를 TaskStop으로 멈췄으며, `git worktree unlock C:/project/agent/.claude/worktrees/09-web-edit-hook`는 출력 없이 끝났다.

open-session을 부른다 2026-10-27T14:10:11Z

## 이어받기 (새 세션)

새 세션이 위 지시문으로 열렸다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/design-reverse-sync/issues/09-web-edit-hook.md (지시문은 위 "지시문"과 같다)

`set_session_title`로 제목을 `feature/09-web-edit-hook`으로 바꾸고, `git worktree list`에서 그 브랜치의 자리(`.claude/worktrees/09-web-edit-hook`)를 찾아 `EnterWorktree(path)`로 들어갔다. 커밋하지 않은 변경(수정 6, 미추적 6)은 인계 때 그대로였다.

## 셀프 리뷰

`/code-review`, 기점 `origin/main`(`35028cba`), 범위는 커밋하지 않은 변경 전부(수정 6, 미추적 6, 커밋 0). 명세는 티켓 09와 명세의 "계기 훅" 절. 표준 축은 Critical·Major 없이 Minor 다섯·Nit 둘·갈래 Minor 하나, 명세 축은 Major 하나·Minor 하나·Nit 다섯을 냈다. 리뷰하는 동안 표준 축이 변이 표 전부를 다시 돌려, 명세 축은 원문이 사라진 순간을 피해 떠 둔 사본으로 함수를 불렀다.

고칠 것:
- 명세 Major: 변이 표의 표지 열여덟이 모두 시험 함수 이름이다. `tools/mutate.py --check <표> 1…19`가 열여덟을 메아리로 걸고 2로 끝났고(명세 축의 보고), 새 표에는 `--staged`도 같은 판정을 걸어 pre-commit이 커밋을 막는다. 시험 이름은 그 시험의 어느 단언이 빨개져도 실패 머리에 실린다(`.claude/rules/probes.md`의 표지 항목, 대기열 417). 변이마다 `-k`로 시험 하나로 좁히고, 고른 단언이 실패할 때만 출력에 실리는 값을 손으로 넣은 변이의 실패 출력에서 다시 고른다. 같은 시험 이름을 함께 쓰던 8과 17(표준 Minor)도 여기서 갈린다.
- 표준 Minor: 독스트링의 "폴더로 끝나는 경로는 지나간다"가 넓다. 지나가는 것은 `web/packages/ui`와 `web/apps/<앱>` 그 자체뿐이고 그 아래의 폴더 경로는 화면 코드로 본다.
- 표준 Minor·명세 Nit: "꼴이 어긋난 입력은 예외 없이 침묵한다"의 반례. 깊게 중첩된 JSON(`b"[" * 200000`)은 `json.loads`가 `RecursionError`를 내고, `.git` 파일의 `gitdir:` 값에 NUL이 있으면 `_first_line`이 `ValueError`를 낸다(두 축이 함수를 불러 본 보고. 고칠 때 시험이 먼저 빨개지는지 본다).
- 표준 Minor: 못 보는 것의 "한 번 알린 뒤"에 이름 붙은 시험이 없다.
- 표준 Minor: `context_for(*, subagent: bool)`가 키워드 전용으로 옮겨 지나간 불리언 플래그다(`CODING_STANDARDS.md`). 알림 문장 둘을 상수로 둔다.
- 표준 갈래 Minor·명세 Minor: `/sync-design-system`의 `확인` 줄 "그 보고를 받은 부모 세션이 이것을 부른다"에 조건이 없다. 그대로 따르면 "계속한다"를 고른 부모가 확인을 다시 돌려 같은 질문을 다시 받고(명세 175행, 스토리 20), 들이기 세션이 띄운 서브에이전트의 보고가 들이기 부모에게 확인을 시킨다(스토리 25). 고친 뒤 카나리아 `sync_design_system_web_edit_hook.toml`을 다시 돈다.
- 명세 Nit: 페이로드 표의 발동 사례와 시험의 `_ui`가 디자인 토큰 CSS를 `src/tokens/theme.css`로 적었다. 실제는 `web/packages/ui/src/styles/theme.css`다(Glob으로 봤다).
- 명세 Nit: 독스트링이 알림 문장을 "이미 했으면 무시한다"로 인용했지만 글자 그대로가 아니다.
- 명세 Nit: 프로브 README의 카나리아 행이 티켓 09의 둘을 "이 스킬이 없거나 옛 판인 주 체크아웃"을 대조군으로 둔다고 적었지만 `tools_rule_web_edit_hook.toml`의 대조군은 옛 규칙이다.
- 명세 Nit(갈래): 한 응답에 Write·Edit를 나란히 여럿 보내면 알림은 그 쓰기가 모두 끝난 뒤에 닿는다. "첫 쓰기 뒤"의 서술에 더한다.

남길 것:
- 표준 Nit: `.claude/rules/tools.md`의 여덟째 훅 서술 "`HEAD` 한 줄을 읽고"는 워크트리에서 `.git` 파일 한 줄을 더 읽는다. 그 서술은 이미 "위로 `.git`을 찾고"를 들고, 시간은 재지 않은 어림이라 판정이 바뀌지 않는다. 고치면 그 규칙의 카나리아를 다시 돌려야 해서 두었다.
- 표준 Nit: 시험을 구현 전에 돌려 빨강을 보지 않은 것은 프로브 README가 밝혔고 변이 표가 그 몫을 맡는다.
- 명세 Nit(범위): 상대 경로를 페이로드의 `cwd`에서 푸는 갈래. 티켓의 "작업 트리는 고친 파일의 경로에서 찾는다"를 상대 경로에서도 지키는 몫이고, Claude가 일하는 자리는 `cwd`라는 것이 `.claude/rules/tools.md` 디렉터리 항목이라 범위 추가로 보지 않는다.

고친 것(위 "고칠 것" 전부):
- 시험을 먼저 고쳤다. `깊은_중첩` 사례와 `test_git_파일의_gitdir_에_NUL_이_있으면_알린다`를 더하고 훅에서는 알림 문장을 상수로 옮기는 것만 한 판에서, 둘만 빨갛고 65건은 초록이었다(`uv run pytest -q tests/tools/test_hook_web_edit_check.py`의 출력을 손으로 봤다). 깊은 중첩은 `RecursionError`로 빨개졌고, NUL 사례는 처음에 시험 폴더 이름을 `nul`로 지어 윈도의 예약 장치 이름 때문에 `FileNotFoundError`로 빨개졌다. 폴더 이름을 `co`로 바꾼 뒤 `ValueError: embedded null character`로 빨개졌다. 훅이 `json.loads`에서 `RecursionError`를, `_first_line`에서 `ValueError`를 잡게 고친 뒤 67건이 초록이었다(같은 명령).
- 알림 문장은 `context_for(*, subagent: bool)` 대신 상수 `MAIN_CONTEXT`·`SUBAGENT_CONTEXT`이고, `output_for`가 `agent_id`로 하나를 고른다.
- 못 보는 것 "한 번 알린 뒤"를 `test_못_보는_것_한_번_알린_뒤에는_같은_세션에_다시_알리지_않는다`로 고정했다. 시험과 페이로드 표의 디자인 토큰 CSS 경로를 `web/packages/ui/src/styles/theme.css`로 바꿨다.
- 독스트링: 폴더 문장, 인용, 나란히 보낸 쓰기, 꼴이 어긋난 입력의 목록과 `.git`·`HEAD`를 읽다 난 오류를 고쳤다.
- `/sync-design-system`의 `확인` 줄에 부모 세션이 부르는 조건을 더하고(이 세션의 `writing-for-agents`를 부른 뒤), 카나리아 `sync_design_system_web_edit_hook.toml`의 기대에 그 문장을 더해 다시 돌았다. "통과 4 · 실패 0"이었다(도구가 찍은 줄. 실험군 세 회차가 고친 문장을 옮겼고 대조군 주 체크아웃은 "없음"이었다).
- 변이 표: 원문을 새 코드에 맞추고 변이 둘(19 깊은 중첩, 20 `gitdir:`의 NUL)을 대조군 앞에 더했다(앞 실행의 번호를 README가 들어 1~18은 그대로 뒀다). 변이마다 `-k`로 시험 하나로 좁히고, 표지를 고른 단언의 실제 값으로 다시 골랐다. 고른 길과 결과는 프로브 README의 "셀프 리뷰 뒤" 절이다. `--check <표> 1…21`은 종료 0에 메아리 알림이 없었고, 번호를 모두 골라 돈 실행은 "변이 21 모두 기대대로"였다(도구가 찍은 줄, 커밋하지 않은 작업 트리).
- 프로브 README의 카나리아 행 대조군 서술과 변이 표 행을 고쳤다. 티켓 09의 체크박스 스물을 채웠다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장):
- 훅 독스트링 "`web/packages/ui`·`web/apps/<앱>` 그 자체(그 뒤에 토막이 없는 경로)는 지나간다. 그 아래의 폴더 경로(`web/apps/admin/src`)는 파일과 가르지 못해 화면 코드로 본다. Write·Edit 의 대상은 파일이다."
- 훅 독스트링 "꼴이 어긋난 입력(JSON 이 아니다, 풀다가 재귀 한도를 넘을 만큼 깊게 중첩됐다, 객체가 아니다, `tool_input` 이 객체가 아니다, `file_path` 가 문자열이 아니다)은 예외 없이 침묵한다. 작업 트리의 `.git`·`HEAD` 를 읽다 난 오류(경로에 NUL 이 든 `gitdir:` 포함)는 읽지 못한 것으로 보아 알린다."
- 훅 독스트링 "한 응답에 Write·Edit 를 나란히 여럿 보내면 알림은 그 쓰기가 모두 끝난 뒤에 닿는다(모델은 나란히 보낸 호출의 결과를 함께 받는다. 재지 않은 어림이다)."
- `/sync-design-system` `확인` 줄 "그 보고를 받은 부모 세션은 이 세션에서 아직 확인을 하지 않았고 들이기를 하는 세션이 아닐 때 이것을 부른다"
- 프로브 README의 변이 표 행("표지는 고른 단언이 실패할 때만 출력에 실리는 값")과 "셀프 리뷰 뒤" 절의 표지 고르기 서술, 카나리아 행의 "티켓 09의 둘은 그 문장이 없는 옛 판의 스킬과 규칙이 있는 주 체크아웃을" 대조군으로 둔다는 서술.

다시 돌린 명령: 위의 시험 파일 하나, ruff 둘(그 두 파일, 0), 변이 표, 카나리아 하나. 손으로 치는 다섯 검증 명령은 커밋의 pre-commit 결과로 갈음한다(결과는 커밋 뒤 이 일지에 적는다).
