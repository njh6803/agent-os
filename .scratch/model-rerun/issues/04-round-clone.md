# 04: 회차의 자리 — 회차마다 B까지의 이력만 든 새 클론과 막는 규칙, 허용 목록 환경을 짓고, 표지를 본 폴더만 지운다

**What to build:** 회차 도구가 회차 하나를 열기 전의 자리를 짓는다. 사람이 준 뿌리 아래 회차마다 다른 폴더를 만들고 표지를 심는다. 그 안에 B를 `main`으로만 받은 로컬 bare 원격과 그 클론을 짓고, 클론에 B 뒤 커밋과 다른 ref가 없는지 대 본다(스토리 12·13·14). 클론에서 준비 명령을 돌리고 그 시간과 비용을 회차에 넣지 않는다(스토리 15). 클론의 `.claude/settings.local.json`에 막는 규칙을 쓴다(스토리 19·20). 세션에 넘길 환경을 허용 목록으로 짓고 gh 설정 폴더를 빈 폴더로 준다(스토리 18). 회차 폴더를 지우는 명령은 표지가 있는 폴더만 지운다(스토리 46). 세션을 띄우는 것은 06이다.

근거는 `.scratch/model-rerun/spec.md`의 "클론과 설정 폴더"의 회차 폴더·bare와 클론·준비·환경 변수와 그 2026-10-22 주석 셋(뿌리와 설정 폴더의 머리, 상위의 `.claude/`, 게이트 작업 트리와 회차 폴더를 지우는 때. 준비의 실패. 캐시 변수의 이름), "명령과 막는 규칙"의 막는 규칙 목록, "자리와 모듈"의 지우는 길과 `REPO_LOCATION_VARS` 항목, Testing Decisions "회차 하나"의 클론·지우기·환경 항목이다. 설계 5절이 원천이고 명세가 고친 자리(쓰기도 막는다, 웹 도구 전부, 바깥 상태를 바꾸는 도구, 윈도 기본값)는 명세가 원천이다. 프로브 `.scratch/model-rerun/probes/headless_flags/headless_flags.py`의 `layout`, `allowed_env`, `ancestors_with_claude_dir`, `remove_tree`가 같은 일을 프로브 크기로 한다.

01의 꼴을 쓴다. 03과 나란히 돌 수 있다. 이 티켓은 06과 07을 막는다.

**Blocked by:** 01

**Status:** ready-for-agent

### 뿌리와 회차 폴더

- [ ] **뿌리는 러너를 띄우는 쪽이 명령 줄로 준 절대 경로다.** 상대 경로면 아무것도 하지 않고 멈춘다. 뿌리와 전용 설정 폴더 둘 다 주 체크아웃(`git worktree list`의 첫 줄)과 사용자의 `~/.claude`를 경로 조각 단위로 머리로 가지면 멈춘다. `C:/Users/User/.claude-rerun`은 조각으로는 `~/.claude` 아래가 아니어서 받는다. 견줌은 대소문자와 `/`·`\`를 가리지 않는다
- [ ] **회차 폴더는 뿌리 아래 `<과제 id>-<갈래>-<회차 번호>-<짧은 난수>`이고(이름은 01의 함수로 짓는다), 만든 직후 표지 파일을 심는다.** 회차 번호는 부르는 쪽(10)이 01의 함수로 잡아 넘긴다. 그 안에 bare 원격, 클론, 원본 stream-json 자리, 빈 gh 설정 폴더가 든다. 회차마다 경로가 달라 세션 기록 폴더와 자동 메모리 경로가 갈린다
- [ ] **회차 폴더의 상위(홈은 뺀다)에 `.claude/`가 있으면 멈춘다**(프로브의 `ancestors_with_claude_dir`). 상위의 설정과 `CLAUDE.md`가 세션에 실리는 것을 막는다
- [ ] **지우기 명령은 사람이 부르고, 뿌리 아래에서 표지가 있는 회차 폴더만 지운다.** 표지가 없는 폴더는 건드리지 않고 이름을 보고한다. 링크는 따라가지 않고 링크만 끊는다(선례 `tools/canary.py`의 `_cut_links`, `tools/tidy_checkouts.py`의 `delete_path`). 커밋 전에 임시 저장소에서 판정을 깨려는 입력(폴더 안의 링크와 junction, 커밋하지 않은 파일, 윈도 경로 정규화가 바꾸는 이름, 표지 없는 비지 않은 폴더, 뿌리로 준 홈)으로 반박한다(`.claude/rules/tools.md`의 지우는 도구 항목)

### bare와 클론

- [ ] **주 저장소에서 B를 bare 저장소의 `main`으로만 민다.** 태그와 다른 ref는 밀지 않는다. 클론의 `origin`은 그 bare 저장소이고, 푸시가 GitHub에도 주 저장소에도 닿지 않는다
- [ ] **세션을 열기 전에 클론의 모든 ref가 B를 가리키고 `git rev-list --all`에 M이 없는지 대 본다.** 하나라도 아니면 그 회차를 열지 않고 멈춘다
- [ ] **git을 띄우는 자리와 그 시험은 `tools.run_hooks.REPO_LOCATION_VARS`를 자식 환경에서 벗긴다**(`.claude/rules/tools.md`의 pre-commit 항목)

### 준비

- [ ] **`uv sync`, `pnpm -C web install --frozen-lockfile`, `uv run pre-commit install`을 클론에서 차례로 돌린다.** 걸린 시간은 회차의 벽시계에 넣지 않는다. 하나라도 0이 아니게 끝나면 남은 준비를 돌리지 않고, 회차를 "측정 아님(준비)"로 낼 수 있게 어느 명령이 몇으로 끝났는지를 돌려준다. 러너를 멈추는 것은 10이다
- [ ] **준비 명령은 함수의 인자로 받는다.** 시험에서는 임시 저장소 안의 작은 명령으로 돌고, 실제 목록은 상수로 따로 단언한다

### 막는 규칙

- [ ] **클론의 `.claude/settings.local.json`의 `permissions.deny`에 명세 "명령과 막는 규칙"의 목록이 모두 든다.** `Bash(gh:*)`, `Bash(git push:*)`, 주 체크아웃과 사용자 `~/.claude`의 `Read`·`Edit`·`Write`, `Skill(open-session)`, `Bash(*open_session.ps1*)`, `Bash(*claude://*)`, `WebFetch`·`WebSearch`, 그리고 `SendMessage`, `ListAgents`, `RemoteTrigger`, `PushNotification`, `DesignSync`, `CronCreate`, `ScheduleWakeup`이다. 경로 규칙의 꼴은 프로브가 막는 것을 본 꼴(`Read(//<드라이브>/<경로>/**)`)을 따른다. 쓰기·편집 규칙과 도구 이름만 쓴 규칙은 프로브가 재지 않은 꼴이라 파일럿(11)이 본다
- [ ] **클론의 `.claude/settings.json`(B의 것)은 고치지 않는다.** 그 파일이 켠 플러그인은 그대로 실리고, 설정 확인(09)이 허용 모임으로 받는다

### 환경

- [ ] **세션에 넘길 환경은 허용 목록으로 짓는다.** 설계 5절의 목록(`PATH`, OS 기본값, `CLAUDE_CONFIG_DIR`, `DISABLE_AUTOUPDATER=1`)과 명세가 더한 윈도 기본값, 캐시 변수(`UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR`, `PNPM_HOME`, `XDG_CACHE_HOME`)이고, 부모 환경에 있는 것만 넘긴다. 여기에 회차 폴더의 빈 폴더를 가리키는 `GH_CONFIG_DIR`을 더한다
- [ ] **허용 목록은 상수 하나이고, 시험의 기대 집합도 그 상수에서 낸다**

### 시험과 검증

- [ ] **사례**(명세 Testing Decisions "회차 하나"의 클론·지우기·환경 항목과 덮이지 않았던 스토리 13·14·15): 뿌리 검사(상대 경로, 주 체크아웃 아래, `~/.claude` 아래, 이웃 이름 `~/.claude-rerun`은 받음), 상위의 `.claude/`, 회차마다 다른 경로, 클론에 B 뒤 커밋과 다른 ref가 없는 것(주 저장소에 태그와 M 뒤 브랜치를 둔 임시 저장소로), 클론의 `origin`이 bare 저장소인 것, 준비 실패가 측정 아님(준비)의 재료로 돌아오는 것과 준비 시간이 벽시계에 들지 않는 것, 막는 규칙 목록(덮이지 않았던 스토리 19·20), 부모 환경에 넣은 가짜 `GH_TOKEN`이 넘어가지 않고 넘긴 이름이 허용 목록과 `GH_CONFIG_DIR`뿐인 것, 지우기가 표지 없는 폴더와 링크를 건드리지 않는 것
- [ ] **하위 프로세스 호출마다 시간 제한을 둔다**(`.claude/rules/tools.md`의 시간 제한 항목)
- [ ] **원칙 III를 지킨다**
- [ ] 검증 명령이 모두 초록이다
- [ ] **기능을 닫지 않는다**
