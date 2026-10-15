# 2026-10-16 (23) 기존 훅 고침 넷(대기열 246·252·284·296)

## 계기

대기열 246·252·284·296. 넷 다 이미 있는 훅과 `tools/hook_payloads.toml` 둘레다. 246은 커밋 메시지 훅이 커밋하는 저장소의
판정 스크립트를 권한 확인 전에 띄우는 것(데스크톱 앱의 백그라운드 보안 검토), 252는 하위 폴더 `cd` 알림(대기열 225)을 받은
뒤에도 같은 세션이 하위 폴더로 두 번 더 옮긴 것(일지 2026-10-13-62), 284는 설계 인터뷰 계기 훅이 워크트리 세션의
`.claude/worktrees/<이름>:grill-with-docs` 호출을 놓치는 것(일지 2026-10-16-13), 296은 PR #257 claude-review 둘째 회차가 낸
Minor 둘(푸시 훅 옵션 표의 `recurse-submodules` 칸, 일지 훅 `number_context`의 추상화 수준)을 보류한 것이다. 넷째 회차의
Minor 하나(옵션 표가 git의 옵션 목록을 손으로 옮긴 것이라 낡는다는 것을 못 보는 것에 적는다)를 296과 함께 했다.

> 사용자: (next-session 지시문의 시작 프롬프트) "대기열 246·252·284·296을 한 PR로 반영한다(기존 훅과 tools/hook_payloads.toml
> 둘레). 각 행의 "어디로" 칸이 원천이다"

지시문의 "이번 요청 범위"는 PR과 병합까지다. 세션은 주 체크아웃에서 열렸다. `tidy-checkouts`로 루트를 `5b5e632d`에서
`a2df7f7c`로 당겼고, 병합된 로컬 브랜치 `worktree-probes-rule-batch`를 지웠고, 휴지통의 `.venv` 넷을 비웠다(직전 일지
2026-10-16-21이 `python.exe`가 쥐어 지우지 못했다고 적은 것도 넷이었다. 이름까지 같은지는 그 일지에 없다). 워크트리 스물일곱 가운데 하나(`skill-check-and-retro-section`, 병합된 PR의 머리와
브랜치 끝이 다르다)는 사람에게 넘겼고 답을 기다리지 않았다. 나머지는 잠금 pid가 살았거나, 그 폴더를 작업 디렉터리로 쥔
`claude.exe`가 있거나, 실행 중인 세션의 브랜치이거나, 병합된 PR이 없거나, 다시 만들 수 없는 `.claude/plans/`가 있어 남겼다. 그
뒤 `EnterWorktree`로 들어와 브랜치 이름을 `chore/existing-hook-fixes`로 바꿨다.

## 한 일

- 246: `tools/hook_bash_commit_msg.py`의 `checker_for`가 이 훅 파일이 든 체크아웃(`HOOK_CHECKOUT`)의 저장소를 git 없이 읽는다
  (`repository_roots`). 그 체크아웃의 `.git`이 폴더면 그것이, 파일이면 `gitdir:`이 가리키는 폴더의 `commondir`가 공통
  폴더이고, 그 체크아웃 자신, 이름이 `.git`인 공통 폴더의 부모, 공통 폴더의 `worktrees/*/gitdir`이 가리키는 `.git`의 부모가 이
  훅의 저장소다. 경로는 `realpath`와 `normcase`로 골라 견준다. 커밋 저장소가 그 밖이면 판정 스크립트를 띄우지 않고 None이다.
  등록에서 거꾸로 대 보므로 `.git` 파일이 이 저장소의 워크트리 관리 폴더를 가리키게 지은 폴더도 밖이다. `deny_reason`이 이 훅의
  체크아웃을 인자로 받는다.
- 252: `tools/hook_bash_cd_outside.py`가 하위 폴더로 옮기는 `cd`를 알리던 갈래를 막는 이유(`_subfolder_reason`)로 바꿨다.
  판정(어떤 `cd`가 작업 폴더를 남기는지, 서브셸·파이프·백그라운드는 세지 않는다)은 그대로다. 밖으로 옮기는 자리가 있으면 그
  이유를 먼저 낸다. `decision`과 `subfolder_notice`를 걷어 `deny_reason` 하나로 합쳤다.
- 284: `tools/hook_grill_design_check.py`의 `is_this_skill`이 그대로의 이름과 `.claude`로 시작하는 경로 접두에
  `:grill-with-docs`가 붙은 이름을 받는다. 플러그인 접두와 다른 폴더의 접두(`web:grill-with-docs`)는 지나간다. 인계 훅
  명세(`.scratch/token-usage/spec.md`)가 `code-review`를 가르는 판정과 같다. 독스트링의 사실과 다른 못 보는 것("이 저장소의
  스킬은 접두사 없는 이름 하나다")을 걷었다.
- 296: `tools/hook_push_delete_open_pr.py`의 `_PUSH_LONG`에서 `recurse-submodules`를 값을 먹는 옵션으로 고쳤다. 표가 git의
  옵션 목록을 손으로 옮긴 것이라 낡는다는 것을 못 보는 것에 적었다. `tools/hook_journal_retro.py`의 `number_context`에서 출력
  파싱을 `read_numbers`(결과 `Numbers`)로, 순번 판정을 `_is_next`로, 문장을 `_misnamed`·`_move_notice`로 떼었다. 동작은 그대로다.
- 시험: 다섯 훅의 `tests/tools/` 시험. 246은 실제 `git init`·`git worktree add`로 주 체크아웃·워크트리·다른 저장소·중첩
  저장소·지은 `.git` 파일을 가르고, 밖의 판정 스크립트가 띄워지면 표지 파일을 남기게 지어 띄우지 않았음을 대조와 함께 본다.
  296은 이 기계의 `git push -h`가 적는 옵션마다 값을 끼운 지우는 푸시를 git처럼 읽는지 본다.
- `tools/hook_payloads.toml`: 커밋 메시지 훅의 발동·침묵 사례를 이 저장소(`${ROOT}`)에서 커밋하게 옮기고 밖의 저장소 침묵
  사례를 더했다. 하위 폴더 `cd` 사례를 deny로 바꿨다. 경로 접두의 grill 호출과 `--recurse-submodules check` 푸시의 발동 사례를
  더했다. `tools/run_hooks.py`는 `${COMMIT_MSGS}`의 설명만 고쳤다.
- 프로브: 변이 표 `existing_hook_fixes_mutations.toml`, 시간 프로브 `commit_msg_hook/time_hook.py`를 이 저장소에서 커밋하는
  꼴로 고치고 밖의 저장소 갈래를 더했다. 그 README 행.
- 대기열 246·252·284·296을 닫았다. `.claude/rules/tools.md`는 고치지 않았다(아래 "정한 것").

## 잰 것

- git 2.32(이 PC)에서 `git push --recurse-submodules check nosuch-remote --delete x`는 `nosuch-remote`를 저장소로 읽었고,
  `--recurse-submodules nosuch-remote …`는 `bad recurse-submodules argument: nosuch-remote`, `--signed nosuch-remote …`는
  `nosuch-remote`를 저장소로 읽었다(임시 저장소에서 손으로 봤다). 직전 일지가 손으로 본 것과 같다.
- 트랜스크립트의 Skill 입력에서 접두 꼴은 `.claude/worktrees/<이름>:<스킬>`(슬래시)이었다(`code-review`·`next-session`, grep으로
  셌다).
- 도움말 시험의 첫 실행은 `--recurse-submodules` 하나만 어긋난다고 냈다. 이 PC의 `git push -h`가 적는 다른 옵션은 모두 표와
  같았다.
- 시험은 다섯 파일 모두 고치기 전에 빨강을 봤다(246·252·284·296의 새 시험. 296의 파싱 분리는 새 함수가 없어 수집 오류).
- 변이(`existing_hook_fixes_mutations.toml`): 첫 판 열일곱이 모두 빨강이었다. 옛 표 `cd_outside_hook_mutations.toml`에서 원문이
  이미 없던 둘을 지금 원문으로 옮겨 따로 돌려 둘 다 빨강이었다. `--check`로 옛 표 셋을 대 보니 이 변경이 원문을 바꾼 것이 넷
  (`bash_hooks_commit_msg_cd_mutations.toml`의 하나, `journal_number_and_guards_mutations.toml`의 셋)이었고 같은 판정을 새 표가 잇는다.
- 시간(`commit_msg_hook/time_hook.py`, 래퍼를 거쳐 다섯 번씩, 등록된 워크트리 스물여덟): `commit` 글자 없음 176~185ms, `-F`
  없는 커밋 174~203ms, 맞는 제목 282~303ms, 긴 제목 281~293ms, 저장소 밖의 긴 제목 184~193ms. `.claude/rules/tools.md`가 적은
  판정 길의 범위(281~375ms) 안이다.
- 훅 페이로드 108건이 어긋남 없이 돌았다.

## 셀프 리뷰

`/code-review`(base `a2df7f7c`, 바뀐 파일 열다섯, 미추적 둘, 커밋 없음). 명세는 네 행의 "어디로"와 PR #257 넷째 회차 Minor다.
훅이 넣는 문구를 바꿔 두 브리프에 갈래 밟기 문단을 넣었다. 두 축 모두 네 행과 그 Minor가 구현됐다고 봤다.

고친 것.
- Major(두 축): `KICKOFF.md`의 훅 목록이 하위 폴더 `cd`를 "막지 않고 알린다", `hook_bash_cd_outside`를 "체크아웃 밖은 막고 하위
  폴더는 알리며"로 적었다. 새 프로젝트가 복사해 가는 살아 있는 런북이다. 막는다로 고치고, 같은 줄의 `hook_bash_commit_msg`
  설명에 246의 신뢰 경계를 더했다(명세 축).
- Minor(두 축, 갈래): 셸이 이미 하위 폴더에 있을 때 막는 이유가 "체크아웃 루트에서 옮긴다"고 적었다. 모델이 그 전제로 루트 기준
  상대 경로를 주면 하위 폴더에서 풀린다. 이유가 지금 작업 폴더와 `cd <루트>`로 돌아오는 길을 적게 하고 시험과 변이를 더했다.
- Minor(표준, 갈래): 서브에이전트의 Bash는 호출마다 작업 폴더가 처음으로 돌아간다. claude 실행 파일의 서브에이전트 프롬프트에
  "Agent threads always have their cwd reset between bash calls"가 있는 것을 읽었다(재지 않았다). 그래서 그 하위 폴더 `cd`를 막는 것은
  거짓 양성이다. 판정은 바꾸지 않고 못 보는 것에 적고 시험으로 고정했다. `agent_id`로 가르면 그 입력과 동작을 재야 해 이 PR 밖이다.
- Minor(표준): `_move_notice`의 불리언 플래그 인자(`CODING_STANDARDS.md` 14행). 문장을 둘(`_move_notice`와 `MOVE_NOTE`)로
  나눴다. 같은 김에 Nit 둘을 고쳤다. `read_numbers`는 읽지 못한 까닭을 문자열 대신 `Unreadable`로, 결과는 `JournalNumbers`로
  돌려준다.
- Minor(두 축): 푸시 훅의 새 못 보는 것 "표에 없는 짧은 옵션이 값을 먹으면"은 시험이 없었고, 짧은 옵션에는 표가 없다(`-o` 판정
  하나다). 문장을 고치고 시험으로 고정했다.
- Minor(표준): 도움말 시험이 "git 처럼 읽는다"고 적었지만 git은 `--delete`와 `--all`·`--mirror`·`--tags`의 조합을 거절하는데 훅은
  지우는 푸시로 읽는다(임시 저장소에서 git 2.32의 `--delete is incompatible with --all, --mirror and --tags`를 손으로 봤다).
  판정은 바꾸지 않고 못 보는 것(거짓 양성, git이 어차피 거절한다)에 적고 시험으로 고정했다. 도움말 시험은 낱말을 가르는 것만
  본다고 이름과 독스트링을 고쳤다.
- Minor(두 축): grill 훅의 "첫 판은 … 그 호출을 놓쳤다(지난 7일 … 21회)"는 `grill-with-docs`를 놓친 사건처럼 읽히고 근거의 종류와
  기준 날짜가 없었다. 사건은 없고 21회는 인계 훅 명세가 2026-10-16에 `code-review`를 손으로 센 수라고 고쳤다.
- Minor(명세): 284의 "어디로"가 든 페이로드 표에 플러그인 접두의 침묵 사례가 없었다. 지은 입력임을 적고 더했다. 표준 축 Nit대로
  그 절의 머리 주석이 사례의 출처를 가르게 고치고, 트랜스크립트의 실제 이름(`.claude/worktrees/harness-audit:code-review`)으로 새
  갈래의 침묵 사례를 더했다.
- Minor(명세): `.scratch/harness/probes/cd_outside_hook_time.sh` 머리 주석의 "대기열 225 뒤로는 알린다"를 고쳤다.
- Nit: `_same`을 `_canonical`로(같은 파일의 `_same_path`와 헷갈린다), 시험의 `_도움말_옵션`을 `_도움말_옵션_줄`로 바꿨다. 252 닫힘
  표지의 거짓 양성 문장, 시간 프로브 README와 독스트링의 근거 종류(`ls`로 셌다, 코드를 읽은 것), 옛 표의 변이를 "옮겼다"는 말(옛
  표에 그대로 있어 "다시 적었다")을 고쳤다.

남긴 것.
- Nit(표준): `.claude/rules/tools.md`의 "`skill` 이름만 보고 `grill-with-docs`일 때만 계기를 낸다"는 글자 그대로는 접두 꼴을
  빠뜨린다. 접두 꼴도 같은 스킬이라 뜻은 참이고, rules를 고치면 카나리아가 든다. 다음 `.claude/rules/tools.md` 묶음(대기열
  141·291·292)이 함께 고친다(아래 "다음").
- Nit(표준): 시험 도우미 `_판정_파일`의 `commit_msg_hook: bool`은 옛 `_저장소`의 인자를 옮긴 것이다. 시험 도우미라 둔다.
- Nit(표준): `run_hooks.py` 독스트링의 "context (`additionalContext`)"는 감기 도구가 줄바꿈을 빈칸으로 바꾼 것이다. 줄바꿈도
  빈칸으로 읽혀 뜻이 같다.
- Nit(명세): 닫힘 표지의 "ADR 불필요 **닫힘"은 대기열에서 마침표 없는 꼴이 95행, 있는 꼴이 32행이라 다수의 꼴을 따랐다.
- 곁가지(명세): 리뷰어가 친 `git push -h`를 `hook_push_behind_main`이 푸시로 보고 막았다. 이 PR 밖이라 회고 후보로 넘긴다.

다시 돌린 것: 고친 다섯 훅의 시험(파일마다), 페이로드 러너 110건 어긋남 0, 새로 더한 변이 넷(옛 표에서 다시 적은 둘, 반영으로
더한 둘) 모두 빨강, ruff·format·pyright 통과. 손으로 치는 다섯의 나머지는 커밋의 pre-commit으로 갈음한다.

## PR 직전 리뷰

커밋 `d58fb139`과 origin/main 병합 `db1777d2`(대기열 296·297행에서 글자 충돌. 닫은 296행을 두고 main이 더한 297행을 붙였다)
뒤에 돌렸다. CodeRabbit CLI는 좌석이 없어(`Seat: not assigned`) 대체 둘을 나란히 돌렸다.

- `/security-review`: 후보 하나. `checker_for`가 커밋 폴더의 조상을 거슬러 오르다 드라이브 문자만 남은 `C:`에 닿으면, 존재
  확인과 판정 스크립트(`C:/…`)는 드라이브 루트를, 경계 판정(`realpath("C:")`)과 설정 읽기(`C:.pre-commit-config.yaml`)는 훅의
  현재 폴더를 본다. 드라이브 루트에 `.git`과 `tools/check_commit_msg.py`를 둔 사람이 있으면 경계를 지난다. 거르기 하위 작업이
  3/10으로 걸렀다(그 파일을 심을 수 있는 사람은 이미 같은 권한을 가졌고, PR 전 코드는 경계가 없어 더 넓었다). 정확성으로는
  맞아 `ancestors`가 그 자리를 `C:/`로 맞추게 고치고 시험과 변이를 더했다.
- `bug-perf-review`:
  - Minor, 유효: 워크트리 폴더를 git 없이 지우면 등록(`worktrees/<이름>/gitdir`)이 남고, 그 자리에 새로 만든 저장소의 판정
    스크립트를 띄웠다(임시 저장소로 재현했다). 이 PR이 닫으려던 길이라 고쳤다. 등록된 워크트리는 그 `.git` 파일의 `gitdir:`이
    다시 그 등록을 가리킬 때만 센다(`_linked_worktree`). `.git`이 폴더인 새 저장소와 다른 저장소를 가리키는 `.git` 파일 두
    갈래를 시험으로 고정했다.
  - Nit, 유효: `--separate-git-dir` 저장소의 워크트리에 든 훅은 주 체크아웃의 커밋을 밖으로 본다(거짓 음성). 못 보는 것에 적고
    시험으로 고정했다.
  - Nit, 유효: `is_this_skill`의 `startswith(".claude")`가 `.claudeX`·`.claude-plugin`도 받았다. `.claude` 자체이거나
    `.claude/`·`.claude\`로 시작할 때만 받게 좁혔다. 명세의 "`.claude`로 시작하는 경로"를 경로의 첫 토막으로 읽었다고 독스트링에
    적었다.
  - Nit, 유효: 하위 폴더 이유의 `cd <루트>`에 따옴표가 없어 공백이 든 루트에서 안내대로 치면 실패한다. `shlex.quote`로 인용한다.
    한글이 든 경로도 인용된다(셸에서 해는 없다).
  - Minor, 보류: 도움말 시험이 CI 리눅스의 새 git에서 빨개질 수 있다. 이 PR의 CI가 그 git에서 돌아 판정한다.
  - Nit: `.claude/rules/tools.md`의 커밋 메시지 훅 시간 문장은 `repository_roots` 전의 수다. 리뷰어가 워크트리 서른에서
    `repository_roots`만 재 26.7ms였고, 이 세션이 래퍼를 거쳐 잰 판정 길(282~303ms)도 그 문장의 범위 안이라 둔다.
  - 오탐·문제 없음으로 확인한 것: 정션·한글·공백·짧은 이름·대문자 경로의 판정, 서브셸 안내, 흔한 명령 가운데 하위 폴더 `cd`를
    안내하는 문서(0건), `_PUSH_LONG`의 다른 옵션, `read_numbers` 분리 뒤의 동작.

반영 뒤 다섯 훅의 시험을 파일마다 돌려 초록이었고, 변이 표에 넷(거꾸로 대 보기 둘, 드라이브 루트, `.claude` 접두)을 더해
스물다섯 전체를 돌려 모두 빨강이었다. 손으로 치는 다섯은 이 반영의 커밋에서 pre-commit으로 갈음한다.

## 정한 것

- 246의 "이 훅의 저장소"는 `CLAUDE_PROJECT_DIR`이 아니라 훅 파일(`__file__`)의 체크아웃에서 읽는다. 래퍼가 `runpy`로 띄워도
  `__file__`은 그 파일이고, 러너와 시험이 같은 길을 밟는다. git을 띄우지 않아 판정 길에 자식 하나를 더하지 않는다.
- 246의 페이로드 발동 사례는 커밋 폴더를 `${ROOT}`로 옮겼다. 메시지 파일은 그대로 `${COMMIT_MSGS}`의 것이다(스크래치패드의 파일로
  이 저장소에서 커밋하는 실제 꼴). 그 임시 저장소는 밖의 저장소 침묵 사례가 된다. 옛 훅이었다면 막았을 입력이라 새 판정을 가른다.
- 284의 접두 판정은 명세의 문장("`.claude`로 시작하는 경로 접두")을 글자 그대로 따른다. 인계 훅이 같은 판정을 쓰기 때문이다.
- `.claude/rules/tools.md`는 고치지 않는다. rules를 바꾸면 카나리아(새 `claude -p` 세션)가 든다. 그 파일의 이 훅들 문장("`skill`
  이름만 보고 `grill-with-docs`일 때만", `hook_bash_commit_msg`의 판정 길 281~375ms)은 접두 꼴도 같은 스킬이고 다시 잰 시간도 그
  범위 안이라 이 변경 뒤에도 참이다.
- 296의 도움말 시험은 다른 판의 git(CI)이 표에 없는 옵션을 적으면 그 git에서 빨개진다. 조용히 낡는 표를 시끄럽게 하는 것이 그
  시험의 몫이라 그대로 둔다.
