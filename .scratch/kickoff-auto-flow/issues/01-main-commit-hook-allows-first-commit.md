# 01: `hook_git_main_commit`이 커밋 없는 저장소의 main에서 첫 커밋을 지나가게 한다

**What to build:** 새 프로젝트의 킥오프는 7단계에서 `hook_git_main_commit`을 등록하고 8단계에서 첫 커밋을 main 위에 한다. 지금 훅은 브랜치 이름만 보아, `git init -b main`만 한 저장소의 첫 커밋도 막는다. 이 티켓 뒤에는 커밋이 하나도 없는 저장소의 main에서 훅이 침묵하고, 커밋이 있는 main은 지금처럼 막는다. 런북 7단계의 훅 설명도 같은 PR에서 새 동작으로 고친다. ADR 0028 "함께 바뀌는 것"이 훅과 그 설명을 함께 고친다고 적었다. 따로 들어가면 런북이 옛 훅을 두고 첫 커밋이 지나간다고 말한다(명세 검토의 지적, 일지 2026-10-12-39).

근거는 `.scratch/kickoff-auto-flow/spec.md`의 "`hook_git_main_commit`" 절, Testing Decisions의 같은 항목, 변경 표의 "`KICKOFF.md` 7단계 훅 목록" 행과 스토리 21·36이다. ADR 0028 "함께 바뀌는 것"(첫 커밋과 main 커밋 훅)이 앞선 결정이다. 같은 기능의 다른 티켓과 독립이다. 02가 같은 `KICKOFF.md`를 고치므로 02가 이 티켓 뒤에 돈다.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

### 훅 (테스트 먼저)

- [ ] **커밋 없는 저장소의 main에서 막지 않는다.** 판정은 페이로드의 `cwd`에서 `git rev-parse --verify HEAD`가 실패하는 것이다. 커밋이 있는 main은 지금처럼 막고, 작업 브랜치와 detached HEAD는 지금처럼 지나간다. 커밋의 유무도 브랜치를 읽을 때처럼 `GIT_DIR`·`GIT_WORK_TREE`·`GIT_COMMON_DIR`을 벗긴 환경으로 읽는다. 읽기가 실패하면(git이 없다) 지금처럼 막지 않는다
- [ ] **실제 임시 저장소로 세 갈래를 고정한다**(선례 `tests/tools/test_hook_git_main_commit.py`의 `_저장소를_만든다`). 커밋 없는 main은 지나간다. 커밋이 하나 있는 main은 막는다. 다른 브랜치에 커밋이 있고 main은 아직 커밋이 없는 저장소도 지나간다(못 보는 것의 고정). 실패를 기대하는 테스트는 막는 이유의 문구까지 단언한다. 테스트가 임시 저장소에 커밋을 만들 때도 작성자를 명령에 준다(`-c user.name=… -c user.email=…`). 작성자 설정이 없는 환경에서도 돌게 하기 위해서다(선례 `_unpushed_repository`)
- [ ] **커밋 유무를 읽을 때도 환경의 `GIT_DIR`을 무시한다.** 선례 `test_환경의_GIT_DIR_을_무시한다`처럼, 커밋이 있는 저장소의 `.git`을 `GIT_DIR`로 둔 채 커밋 없는 저장소의 `cwd`를 읽어 커밋이 없다고 나오는지 본다
- [ ] **독스트링.** "main 위의 커밋은 언제나 실수다"를 커밋이 있는 저장소로 좁힌다. 훅이 막으려던 사고(다른 세션이 체크아웃을 main으로 옮긴 뒤의 커밋)는 커밋 없는 저장소에서 일어나지 않는다. 못 보는 것에, `HEAD`가 아직 커밋을 가리키지 않는 main은 다른 브랜치에 커밋이 있어도 지나간다는 항목을 더한다(`.claude/rules/tools.md`). 막는 이유의 문구("이 저장소에서 언제나 실수다")도 같이 고친다

### 훅 러너

- [ ] **`tools/run_hooks.py`의 main 픽스처에 커밋 하나를 둔다.** 지금은 `git init -q -b main`만 한 빈 저장소라, 훅을 바꾸면 표의 deny 사례가 침묵이 된다. 커밋을 만드는 픽스처는 `GIT_*`를 벗긴 환경(`hook_environment()`)으로 돌고 작성자를 명령에 준다(`-c user.name=… -c user.email=…`). 선례는 같은 파일의 `_unpushed_repository`다
- [ ] **커밋 없는 main 저장소를 새 자리표시자로 따로 두고**, `tools/hook_payloads.toml`에 그 저장소의 첫 커밋이 침묵하는 사례를 더한다. 표 머리의 자리표시자 목록 줄, `tools/run_hooks.py` 독스트링의 자리표시자 수("열다섯")와 목록, `create_fixtures` 독스트링의 임시 저장소 열거(지금은 main, 작업 브랜치, 푸시하지 않은 커밋의 브랜치와 bare 저장소)를 고친다
- [ ] `uv run python tools/run_hooks.py`가 초록이다. main 위 커밋의 deny 사례는 여전히 deny이고 새 침묵 사례는 침묵이다. 러너 픽스처를 바꾸므로 `tests/tools/test_run_hooks.py`도 초록이다. 워크트리 세션의 훅은 주 체크아웃의 파일로 돌므로, 바뀐 훅의 확인은 이 러너와 테스트로 한다

### 런북

- [ ] **`KICKOFF.md` 7단계 훅 목록의 `hook_git_main_commit` 설명**을 커밋이 있는 저장소의 main 위 커밋 deny로 바꾸고, 커밋 없는 저장소의 첫 커밋은 지나간다(8단계)를 더한다. 그 한 항목만 고친다. 같은 문단의 다른 훅과 7단계의 나머지는 02와 03의 몫이다
- [ ] main 위의 커밋을 훅이 막는다고 적은 agent-os의 다른 문서(`CLAUDE.md`의 환경 함정 등)는 고치지 않는다. 커밋이 있는 이 저장소에서 그대로 참이다(명세 변경 표)

### 마감

- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다
