# 2026-10-21 (09) mcp-shutdown 티켓 03: POSIX 런처

브랜치 `feature/03-posix-launcher`, 워크트리 `.claude/worktrees/03-posix-launcher`. 티켓은 `.scratch/mcp-shutdown/issues/03-posix-launcher.md`.

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/mcp-shutdown/issues/03-posix-launcher.md … 다음 작업: … Windows가 아닌 OS에서 MCP 서버를 런처 뒤에 띄워, 서버가 끝나거나 agent-os 프로세스가 죽으면 그 서버의 프로세스 그룹이 모두 내려간다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 2 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 … 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다 … 이번 요청 범위: PR과 병합까지"

나란히 여는 묶음의 둘째라 `tidy-checkouts`는 돌지 않았다(첫 세션이 돈다). `EnterWorktree`로 새 워크트리에 들어가 브랜치 이름을 `feature/03-posix-launcher`로 바꿨다. 기점은 origin/main `5040230c`(#337, 티켓 01)다.

## 빨강을 먼저 본다

닫기 테스트의 사례 2(자식을 남기는 서버의 정상 닫기)와 사례 5(연결을 연 프로세스가 갑자기 죽음)를 런처 없이 더했다. 사례 5는 시제품과 달리 자식이 연결을 연 뒤 남기는 표지(`connected`)를 기다려 끈다. 재려는 상황(연결을 연 프로세스가 죽는다)이 났다는 표지다. 이 PC(Windows)에서 두 사례가 초록이다(2 passed, 24.58초). Job Object가 거둔다. 바꾼 파일의 `uv run ruff check`·`ruff format --check`·`pyright`와 `pyright --pythonplatform Linux`가 모두 0이다(01의 CI가 리눅스 pyright에서만 빨갰던 일, 대기열 403).

실험 커밋 `b0ed462f`는 테스트 파일 하나만 든다(이 일지는 커밋하지 않았다). `sibling_overlap.py`는 겹침 없이 다음 빈 번호로 일지 09를 냈다. 그 커밋의 pre-commit은 모두 Passed였다. 러너는 429.12초(pytest 357.7초, web-verify 428.7초, run-hooks 155.0초, pyright 40.8초)였고, 표·카나리아 명세 모양·헌법 판·인용 대조는 그 파일이 없어 Skipped였다. 아직 푸시하지 않았고 PR이 없다.

## 인계 (커밋 뒤)

실험 커밋 직후 인계 계기가 왔다(세션 컨텍스트 220,338 토큰, 경계 `커밋 뒤`). 명세·티켓·01 일지를 읽는 데 컨텍스트를 썼다. 인계하지 않는 다섯 때에 들지 않는다. 커밋은 성공했고, 요청 범위는 PR과 병합까지이며, 지시문의 "이어받을 상태"는 `없음`이고, 이 세션이 쓴 `인계 못함` 줄은 없으며, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 지금 제목은 `feature/03-posix-launcher`다.

결정:

- 사례 5의 자식이 연결을 연 뒤 표지 파일(`connected`)을 남기고, 테스트는 그 표지를 기다려 끈다(시제품은 `stay.hb`를 기다렸다). 표지 이름은 자식 스크립트에 인자로 넘긴다.
- 실험 커밋에 일지를 넣지 않았다. 티켓이 "두 사례만 든 실험 커밋"이라서다.

새 세션이 알아 둘 것(이 세션이 읽은 것):

- CI의 `python` 잡은 `uv run pytest -q` 전체를 돌고, 같은 브랜치의 새 푸시가 앞 실행을 취소한다(`ci.yml`의 `concurrency`, `cancel-in-progress: true`). claude-review는 draft를 건너뛴다(`claude-code-review.yml`의 `if: !github.event.pull_request.draft`).
- 선례(`docs/constitution/operations.md` 9행)는 빨강이어야 하는 경우를 만든 실험 커밋을 푸시해 보고 되돌리는 것이다. 이 티켓은 되돌리지 않고 그 위에 런처를 얹는다(두 사례는 남는 테스트다).
- 시제품 런처는 `.scratch/mcp-shutdown/probes/prototype/src/agent_os/adapters/mcp_launcher.py`(68줄, 표준 라이브러리만), 어댑터 쪽은 같은 폴더 `mcp.py`의 `_parameters`와 `LAUNCHER`다. 지금 어댑터의 여는 함수는 `_session(stack, server)`이고 02가 같은 자리를 감싼다.
- `stale_parent.py`는 지금 폴더 아래 `src/agent_os/adapters/mcp_launcher.py`를 런처로 띄우고, 표준 에러에서 `이미 끝나`와 `런처:`를 찾는다.

새 세션이 할 것은 차례로 다음과 같다.

1. 브랜치를 푸시하고 draft PR을 연다. 그 CI 실행이 끝날 때까지 푸시하지 않는다(취소되면 다시 돌린다). `python` 잡에서 사례 2와 5가 하트비트가 자란 까닭(`하트비트가 자란다`)으로 빨간 것을 보고 그 실행의 URL을 PR 본문에 남긴다.
2. 기다리는 동안 로컬에서 런처, 명령 찾아보기, 문서·독스트링, 프로브(우두머리가 아닌 갈래)를 구현한다. 티켓의 나머지 체크박스 전부다.
3. 검사, 셀프 리뷰, 커밋, PR 직전 리뷰, 봇 회차, 기능 닫기 판정, 병합, 일지 `## 다음`과 next-session.

지시문:

다음 작업: .scratch/mcp-shutdown/issues/03-posix-launcher.md. Windows가 아닌 OS에서 MCP 서버를 런처 뒤에 띄워, 서버가 끝나거나 agent-os 프로세스가 죽으면 그 서버의 프로세스 그룹이 모두 내려간다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/mcp-shutdown/issues/03-posix-launcher.md
브랜치: feature/03-posix-launcher
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-21-09-posix-launcher.md(그 워크트리의 커밋하지 않은 파일)의 "빨강을 먼저 본다"와 "인계 (커밋 뒤)", .scratch/mcp-shutdown/issues/02-boundary-exceptions.md(나란히 도는 형제)
이어받을 상태: 인계: 커밋 뒤. `b0ed462f`(런처 없이 닫기 사례 2와 5를 더한 실험 커밋, pre-commit 모두 Passed)까지 했다. 아직 푸시하지 않았고 PR이 없다. 남은 단계는 차례로 푸시와 draft PR, 그 CI 실행에서 두 사례의 빨강을 보고 URL을 PR 본문에 남기기(그 실행이 끝날 때까지 푸시하지 않는다), 런처와 나머지 체크박스 구현, 검사, 셀프 리뷰, 커밋, PR 직전 리뷰, 봇 회차, 기능 닫기 판정, 병합, 일지 `## 다음`과 next-session이다. 워크트리에 커밋하지 않은 일지가 있다. docs/journal/2026-10-21-09-posix-launcher.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

제목을 `feature/03-posix-launcher (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었다(설치 둘과 커밋은 끝났다). 잠금 풀기는 오류 없이 지났다.

open-session을 부른다 2026-10-21T09:39:45Z

## 이어받은 세션

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: .scratch/mcp-shutdown/issues/03-posix-launcher.md … 어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다 … 이어받을 상태: 인계: 커밋 뒤. `b0ed462f`(런처 없이 닫기 사례 2와 5를 더한 실험 커밋, pre-commit 모두 Passed)까지 했다. … 이번 요청 범위: PR과 병합까지"

제목을 `feature/03-posix-launcher`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다(잠금은 앞 세션이 풀어 두어 막히지 않았다).

### 빨간 CI 실행

브랜치를 푸시하고 draft PR #338을 열었다. 실험 커밋의 CI 실행 39579303270이 끝까지 돌았고, Linux의 `python` 잡이 `2 failed, 4093 passed`였다. 빨간 것은 사례 2(`child.hb`)와 사례 5(`wrapper.hb, stay.hb`)뿐이고 둘 다 "하트비트가 자란다"였다. URL을 PR 본문에 남겼다. 그 실행이 끝날 때까지 푸시하지 않았다.

### 구현에서 정한 것

- **기다림을 스레드로 옮겼다.** 시제품은 `server.wait(timeout=0.2)`로 기다렸다. CPython 3.12의 POSIX `Popen._wait`는 시간 상한이 있으면 `waitpid(WNOHANG)`을 0.05초 간격으로 도는 바쁜 고리라(표준 라이브러리 원문을 읽었다), 티켓과 명세가 대가로 적은 "0.2초마다의 깨어남"과 맞지 않았다. 서버를 기다리는 스레드가 막힌 채 `wait()`하고 `threading.Event`를 세우며, 주 스레드는 `Event.wait(0.2)`로 0.2초마다 깨어나 부모를 본다. 서버가 끝나면 곧바로 깨어나므로 닫는 시간이 시제품보다 늘지 않는다.
- 런처의 한 줄 문구와 파일 이름은 시제품 그대로라 `stale_parent.py`의 상수를 고치지 않았다. 새 프로브는 같은 꼴로 `not_leader.py`라 지었다.
- 어댑터의 `_parameters`는 시제품 그대로다. 01의 `_session(stack, server)`가 그것을 부른다. 02가 여는 단계를 감싸면 찾아보기의 `FileNotFoundError`가 그 안에서 난다.

### Linux에서 본 것

Docker의 Linux에서 작업 트리를 복사해 돌렸다(결과는 `.scratch/mcp-shutdown/probes/README.md`의 "2026-10-21 결과 — 티켓 03의 런처"). 런처를 넣은 어댑터 테스트 12개가 모두 지났고, `stale_parent.py`·`not_leader.py`의 `refused`가 여섯 회차씩 모두 기대대로였다. 티켓이 손으로 한 번 돌려 적으라던 대조는 이렇다. 부모 감시를 뺀 사본(두 `if os.getppid() != parent:`를 `if False:`로)에서 닫기 테스트 셋 가운데 사례 5만 "하트비트가 자란다"로 빨갰다(1 failed, 2 passed). 우두머리 검사를 뺀 사본에서는 `not_leader.py --expect killed`가 기대대로였고 닫기 테스트는 셋 모두 지났다. `full_stack.py`에 새 프로브와 대조군을 엮은 뒤 `83f09401`의 트리로 Linux에서 한 번 돌렸고 어긋남 없이 0으로 끝났다. Windows(이 PC)에서는 어댑터와 처리기 테스트 18개가 지났다(353초, Docker 회차와 겹쳤다).

### 상류 이슈 초안

`.scratch/mcp-shutdown/upstream-issue.md`에 썼다. 재현 스크립트를 Docker의 Linux에서 `mcp==2.3.0`만 깔고 두 번 돌려 두 번 모두 자식이 남았고, 입력이 닫혀도 끝나지 않는 서버의 대조는 자식이 사라졌다. 저장소가 공개라 CI 실행 URL을 본문에 든다.

초안을 보내고 올릴지 물었다. 선택지는 "지금 올린다(추천)", "올리지 않는다", "직접 올린다"였다.

> 사용자: "올리지 않는다"

그래서 올리지 않았고, 그 사실을 초안 파일의 상태 줄과 런처 모듈의 독스트링에 적었다. 선택지의 설명에 적은 계정 이름(njh6803)은 저장소 주인의 이름이고 `gh`가 로그인한 계정을 대 보지는 않았다. 올리지 않아 쓰이지 않았다.

### 찾아보기의 빨강

서버 기동 실패 테스트는 Linux에서 명령 찾아보기가 지킨다. 구현 전부터 초록이던 테스트라 Docker의 Linux에서 찾아보기를 뺀 사본(`shutil.which(server.command)`를 `server.command`로)으로 돌렸다. 찾아보기가 있으면 1 passed, 빼면 `MCPError(-32000, 'Connection closed', None) [single exception in ExceptionGroup]`로 1 failed였다. 명세가 시제품으로 잰 `missing_command`와 같은 까닭이다.

### 커밋 전 검사

- ruff 둘은 깨끗했고, pyright는 이 PC(Windows)와 `--pythonplatform Linux` 둘 다 오류 0이었다.
- `uv run --env-file ../../../.env pytest -m llm`: 7 passed, 4095 deselected(248.23초). LLM 토큰 합계 51,518(입력 50,503, 출력 1,015), 트레이스 10개, 모델 호출 21건이다. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다. 이 줄을 커밋 뒤 검사 절에 옮긴다.
- `tools/run_checks.py` 전체는 돌리지 않았다. 셀프 리뷰를 반영한 뒤 커밋의 pre-commit으로 갈음한다.
- `git fetch` 뒤 `HEAD..origin/main`이 비어 있었다(이 세션 동안 main에 새 커밋이 없었다).

## 인계 (셀프 리뷰 직전)

셀프 리뷰(`/code-review`, 기준점 origin/main)를 부른 직후 인계 계기가 왔다(세션 컨텍스트 361,639 토큰, 경계 `셀프 리뷰 직전`). code-review의 단계는 밟지 않았다. 인계하지 않는 다섯 때에 들지 않는다. 계기를 낸 명령은 실패하지 않았고, 요청 범위는 PR과 병합까지이며, 이 세션의 지시문의 "이어받을 상태"는 `인계: 커밋 뒤`라 경계가 다르고, 이 세션이 쓴 `인계 못함` 줄은 없으며, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 지금 제목은 `feature/03-posix-launcher`다.

새 세션이 알아 둘 것(이 세션만 아는 것):

- 셀프 리뷰의 범위는 커밋한 실험 커밋 `b0ed462f`와 워크트리의 커밋하지 않은 변경, 미추적 파일 넷(`mcp_launcher.py`, `not_leader.py`, `upstream-issue.md`, 이 일지)이다. 명세는 `.scratch/mcp-shutdown/spec.md`, 티켓은 03이다. 사용자의 답("올리지 않는다", 위 "상류 이슈 초안")도 명세 축의 요구에 넣는다.
- `.claude/rules/adapters.md`에 더한 런처 항목은 02가 같은 파일에 더하는 경계 예외 항목과 병합에서 충돌할 수 있다.
- PR #338 본문에는 아직 빨간 CI 실행의 URL만 있다. 커밋 뒤 전체 템플릿으로 고치고 draft를 ready로 바꾼다(claude-review는 draft를 건너뛴다).

지시문:

다음 작업: .scratch/mcp-shutdown/issues/03-posix-launcher.md. Windows가 아닌 OS에서 MCP 서버를 런처 뒤에 띄워, 서버가 끝나거나 agent-os 프로세스가 죽으면 그 서버의 프로세스 그룹이 모두 내려간다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/mcp-shutdown/issues/03-posix-launcher.md
브랜치: feature/03-posix-launcher
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-21-09-posix-launcher.md(그 워크트리의 커밋하지 않은 파일)의 "이어받은 세션"과 "인계 (셀프 리뷰 직전)", .scratch/mcp-shutdown/issues/02-boundary-exceptions.md(나란히 도는 형제)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`, 기준점 origin/main)부터 한다. 런처와 나머지 체크박스는 구현했고, 티켓의 검증 명령 줄과 기능 닫기 줄만 남았다. 남은 단계는 차례로 셀프 리뷰와 반영, 커밋, 일지 검사 절, PR 본문 갱신과 draft에서 ready로 바꾸기, PR 직전 리뷰, 푸시, 봇 회차, 기능 닫기 판정, 병합, 일지 `## 다음`과 next-session이다. docs/journal/2026-10-21-09-posix-launcher.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

제목을 `feature/03-posix-launcher (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었다(`-m llm` 회차와 Docker 회차는 끝났다). 잠금 풀기는 `is not locked`로 끝났다(이미 풀려 있었다).

open-session을 부른다 2026-10-21T10:34:23Z

## 이어받은 세션 (셀프 리뷰부터)

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: .scratch/mcp-shutdown/issues/03-posix-launcher.md … 다음 단계: PR 반영·병합 / 어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다 … 이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`, 기준점 origin/main)부터 한다. … 이번 요청 범위: PR과 병합까지"

제목을 `feature/03-posix-launcher`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. `git fetch` 뒤 origin/main은 여전히 `5040230c`였다.

### 셀프 리뷰

기준점 origin/main, base `5040230c`. 변경 파일 8개, 커밋 1개(`b0ed462f`), 미추적 4개(`mcp_launcher.py`, `not_leader.py`, `upstream-issue.md`, 이 일지). 명세는 `.scratch/mcp-shutdown/spec.md`와 티켓 03이고, 사용자의 답("올리지 않는다")을 요구에 넣었다. 두 축에 외부 근거로 CPython 3.12.10 `Popen._wait`와 mcp 2.3.0 `_stop_server_process`·`_create_platform_compatible_process`의 발췌를 실었다.

두 축의 보고(표준 축은 sonnet·high, 명세 축은 이 세션의 모델):

- 표준 축: Critical·Major 0, Minor 5, Nit 6. Docker의 Linux에서 런처를 직접 불러 서버가 끝난 뒤 0.415초에 런처가 끝나는 것(`Event.wait`가 곧바로 깨어난다), 거부 둘이 2이고 띄우기 실패가 127인 것, 상류 이슈 초안의 재현 스크립트가 초안의 출력과 같은 것, 실행 39579303270의 headSha가 `b0ed462f`인 것을 손으로 봤다.
- 명세 축: 빠진 요구 0, 범위 넘침 0, Minor 2, Nit 2. 01이 쓴 세 문장의 잔존이 살아 있는 문서에 0건이고, `adapters.md` 런처 항목이 티켓의 여덟 요소를, 런처 독스트링이 티켓의 요소와 "올리지 않기로 해"를 모두 담았다고 봤다.

고친 것:

- (표준 Minor) 런처 독스트링 "상류는 부모가 죽는 경우를 다루지 않는다"가 Windows의 Job Object(`KILL_ON_JOB_CLOSE`)를 빠뜨린 보편 주장이었다. "상류는 POSIX 에서 부모가 죽는 경우를 다루지 않는다(윈도우는 Job Object 가 다룬다)"로 고쳤다. 근거는 설치본 mcp 2.3.0을 `pdeathsig|prctl|getppid|KILL_ON_JOB_CLOSE`로 grep해 `os/win32/utilities.py`에만 걸린 것이다. 상류 이슈 초안의 머리 문단도 같게 고쳤다.
- (표준 Minor) 알려진 한계 "서버가 스스로 새 세션으로 떼어 낸 자식"이 좁았다. 서버가 `process_group=0`으로 띄운 자식이 런처의 `killpg` 뒤에 살아 있었다(표준 축이 Docker에서 손으로 봤다). 반례만 덧붙이지 않고 성질로 적었다. 런처 독스트링은 "런처와 상류는 둘 다 프로세스 그룹을 끄므로, 서버의 자손 가운데 그 그룹을 떠난 것(스스로 새 세션이나 새 프로세스 그룹을 연 것)은 거두지 못한다", `adapters.md`는 "런처도 상류도 프로세스 그룹을 끄므로, 서버의 자손 가운데 그 그룹을 떠난 것(스스로 새 세션이나 새 프로세스 그룹을 연 것)은 거두지 못한다". ADR 0034 본문과 명세·티켓의 "새 세션으로 떼어 낸 자식"은 글자 그대로 여전히 참이라 고치지 않았다(`.claude/rules/adr.md`의 달지 않는 것).
- (표준 Minor, `CODING_STANDARDS.md` "에러 처리와 정상 흐름을 분리한다"의 "실패 분기마다 같은 출력·종료 코드·`continue`를 되풀이하는 것") 런처 `main`의 거부 넷을 `_refuse(message)`로 모았고, 입출력 바꾸기를 `_detach_stdio()`로, 기다림을 `_wait_for_server_or_parent()`로 뺐다(추상화 수준). `_refusal(argv) -> str | None`으로 한데 모으는 길은 pyright가 `os.killpg`·`os.getpgrp`를 윈도우에서 보지 않게 하는 `sys.platform == "win32"` 조기 반환이 `main` 안에 있어야 해서 고르지 않았다. 손 변이가 겨누는 두 줄(`if os.getppid() != parent:` 둘, `if os.getpgrp() != os.getpid():` 하나)의 글자와 수는 그대로다.
- (표준 Minor) `mcp.py` 독스트링의 "운영자와 플러그인 작성자가 알 것은 셋이다"를 "닫는 시간에 대해 …"로 좁혔다. 런처가 프로세스 목록에 보인다는 것은 런처 독스트링과 `adapters.md`가 든다.
- (표준 Minor) 프로브 README의 2026-10-21 결과가 커밋하지 않은 스크립트의 실행을 "돌렸다"로만 적었고, "상류가 런처를 늘 새 세션으로 띄워서다"는 해석이 어림이었다. 아래 Linux 회차를 다시 돌린 뒤 "손으로 봤다"와 그 단계로, 해석은 코드를 읽은 것으로 고친다.
- (명세 Minor, 일반 조항으로) `full_stack.py`의 대조군 판정이 `FAILED` 줄만 세어, 빨강이 없어야 하는 `no_leader_check`에서 수집 오류(2)나 고른 테스트가 없는 회차(5)도 기대대로였다. 빈 기대에만 막지 않고 모든 대조군에 pytest 종료 코드(실패를 기대하면 1, 아니면 0)를 더했다.
- (명세 Minor) 상류 이슈 초안의 "In practice this hits servers launched through a wrapper (`npx`, `uvx`, a shell script) …"가 재지 않은 일반화였다. 잰 꼴(입력이 닫히면 끝나는 부모와 남는 자식)로 좁히고 실제 `npx`·`uvx`는 보지 않았다고 적었다.
- (명세 Nit) 사례 5가 `connected` 표지만 기다렸다. 명세의 "각 사례는 닫기 전에 하트비트가 생긴 것을 먼저 기다린다"대로 표지와 하트비트 둘(`wrapper.hb`, `stay.hb`)을 모두 기다린 뒤 끄고, 생기지 않은 것을 이름으로 든다.
- (Nit, 두 축) "`Popen.wait`에 시간 상한을 주면 0.05초마다 깨어나므로"를 "1ms 에서 시작해 두 배씩 늘린 간격(많아야 0.05초)으로 깨어나므로(… POSIX `Popen._wait`를 읽었다)"로 고쳤다. 이 일지의 "구현에서 정한 것"의 "0.05초 간격으로 도는 바쁜 고리"도 같은 뜻으로 읽는다.
- (Nit) README init 항목의 "리눅스에서"를 "윈도우가 아닌 OS에서"로, 런처의 거부하는 때에 윈도우·인자 부족도 2라는 것을, 닿지 않는 `return 0`에 주석을, 번호 인자에 `isascii()`를 더했다.

남긴 것:

- (표준 Nit) `not_leader.py`와 `stale_parent.py`의 뼈대 중복, `full_stack.py` 변이 블록의 되풀이. 프로브는 표준 라이브러리만으로 홀로 도는 스크립트라(프로브 README) 공유 모듈을 두지 않는다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장):

- "상류는 POSIX 에서 부모가 죽는 경우를 다루지 않는다(윈도우는 Job Object 가 다룬다)."
- "런처와 상류는 둘 다 프로세스 그룹을 끄므로, 서버의 자손 가운데 그 그룹을 떠난 것(스스로 새 세션이나 새 프로세스 그룹을 연 것)은 거두지 못한다."
- "표준 라이브러리의 `Popen.wait`에 시간 상한을 주면 1ms 에서 시작해 두 배씩 늘린 간격(많아야 0.05초)으로 깨어나므로"
- `full_stack.py`의 "pytest 의 종료 코드가 실패를 기대하면 1, 빨강이 없어야 하면(우두머리 검사를 뺀 사본) 0이어야 한다. 실패 줄만 세면 수집 오류(2)나 고른 테스트가 없는 회차(5)도 빨강이 없는 것으로 보인다."
- 상류 이슈 초안의 "We have not checked whether real wrappers such as `npx` or `uvx` end up in this state; their child inherits stdin and may exit on its own."

반영 뒤 다시 돌린 것:

- 앞 세션의 손 실행 스크립트(`linux_launcher.sh`, 그 세션의 스크래치패드)를 이 세션의 스크래치패드로 옮겨, 반영한 작업 트리에 대고 Docker의 Linux에서 다시 돌렸다. 어댑터 테스트 12 passed(57.24초, 사례 5는 11.86초), `stale_parent.py --expect refused`와 `not_leader.py --expect refused`는 측정이 아닌 회차와 어긋난 회차가 없었고, 부모 감시를 뺀 사본은 사례 5만 "하트비트가 자란다"로 1 failed, 2 passed였으며, 우두머리 검사를 뺀 사본은 `not_leader.py --expect killed`가 지나고 닫기 테스트 셋이 지났다. 프로브 README의 결과 절을 "손으로 봤다"와 그 명령으로 고쳐 썼고, 우두머리 검사를 뺀 사본의 해석은 코드를 읽은 것(`_create_platform_compatible_process`의 `start_new_session=True`)으로 적었다.
- 고친 `full_stack.py`를 Linux에서 다시 쟀다(`--source`로 `83f09401`의 트리). 어긋난 단계 없이 0으로 끝났고 임시 폴더가 지워졌다. 우두머리 검사를 뺀 사본의 닫기 테스트는 종료 코드 0, 실패 0이었고, 앞의 대조군 넷은 종료 코드 1로 기대한 테스트만 기대한 까닭으로 빨갰다.
- 이 PC(Windows)에서 `tests/adapters/test_mcp.py -k 내려간다`가 3 passed(201.76초, Docker 회차와 겹쳤다).
- 바꾼 파일의 `ruff check`·`ruff format --check`·`pyright`·`pyright --pythonplatform Linux`가 모두 0이었고, `tools/check_type_escapes.py`가 0으로 끝났다.
- 커밋 직전 `sibling_overlap.py`가 1로 끝났다. `.claude/rules/adapters.md`를 바꿨는데 그 파일을 원천으로 든 카나리아 명세(`.scratch/end-user-continuation/probes/canary/adapters_rule_new_optional_fields.toml`)의 결과 줄을 고치지 않아서다. 그 명세는 다른 PR에서 통과해 사전 확인으로 갈음할 수 없어 `tools/canary.py`로 다시 돌렸다. 통과 4, 실패 0(실험군 셋이 규칙의 문구를 옮겼고 대조군은 "없음", claude 2.1.302, 이 워크트리의 커밋하지 않은 작업 트리). 런처 항목은 같은 파일이라 이 파일이 실리면 함께 실린다. 명세의 `# 최신 결과:` 줄을 고쳤고, 다시 친 `sibling_overlap.py`는 0이었다. 그 사이 origin/main에 #339(ticket-for-every-pr 명세와 티켓)가 들어왔고, 이 브랜치가 든 파일과 겹치지 않는다.
- CodeRabbit CLI는 `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 PR 직전 리뷰는 대체 둘(`/security-review`, `bug-perf-review`)로 한다.

### 막힌 커밋

첫 커밋이 pre-commit의 pytest에서 막혔다(487.0초, web-verify 533.2초, run-hooks 230.0초. 나머지 검사는 Passed). 막힌 명령이라 "커밋 뒤" 인계 계기는 경계가 아니었고(next-session "인계할 때" 1), 이 세션에서 이었다. 빨간 것은 둘이다.

- 사례 5: "30초 안에 생기지 않았다: ['connected', 'wrapper.hb', 'stay.hb']". 셀프 리뷰 전에도 연결 표지를 같은 30초로 기다렸으니 하트비트를 더한 탓이 아니다. 이 PC에서 사례 5의 자식을 홀로 세 번 띄워 보니 연결 표지까지 9.81~12.34초였고 하트비트 둘은 그보다 먼저 생겼다(세션 스크래치패드의 `case5_timing.py`, 손으로 봤다). 30초는 그 2.5~3배라 `.claude/rules/tests.md`의 시간 단언 항목(홀로 돈 시간의 넉넉한 배수)에 못 미쳤다. 사례 5에만 `CONNECT_WITHIN_SECONDS = 120`을 두었다. 홀로 돌린 사례 5는 1 passed(호출 15.45초)였다.
- `tests/tools/test_sibling_overlap.py::test_옮기기를_고르면_옮길_번호대로_옮기고_다시_대조한다`: 둘째 `--move`가 0이 아니라 2로 끝났다. 이 브랜치가 건드리지 않은 테스트이고 홀로 돌리면 1 passed(172.59초)였다. 부하에서 난 것으로 보지만 까닭은 가르지 않았다(어림). 다시 빨가면 diagnosing-bugs로 간다.
- 인용 대조 경고: 이 일지가 `CODING_STANDARDS.md`의 문구를 줄여 인용했다. 원문("실패 분기마다 같은 출력·종료 코드·`continue`를 되풀이하는 것")으로 고쳤다.
