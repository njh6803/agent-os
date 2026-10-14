"""병합된 워크트리와 로컬 브랜치를 판정하고, 후보 하나씩 지운다. `tidy-checkouts` 스킬 3이 부른다.

세션마다 판정과 삭제 스크립트를 스크래치에 새로 짓다가, 사용자가 끊은 호출이 지우는 도중에 죽어
지우다 만 폴더가 생겼다(대기열 132, 일지 2026-10-07-02). 그래서 판정은 이 도구가 한 번에 내고,
삭제는 후보 하나마다 따로 부른다. 끊긴 호출이 망가뜨리는 것은 많아야 하나다.

사용(주 체크아웃에서):
    uv run python tools/tidy_checkouts.py judge [--running "<세션 제목>" ...]
    uv run python tools/tidy_checkouts.py remove "<경로>" <브랜치> <HEAD>
    uv run python tools/tidy_checkouts.py remove-branch <브랜치> <커밋>
    uv run python tools/tidy_checkouts.py remove-stray "<경로>"

`--running` 은 `list_sessions` 에서 이 세션을 뺀 `isRunning` 세션의 제목이다. 도구는 앱의 세션을
보지 못해 부르는 쪽이 넘긴다. `judge` 는 줄마다 `지운다`·`남긴다`·`넘긴다`(사람에게)와 이유를 찍고,
지울 것에는 부를 `remove`·`remove-branch`·`remove-stray` 명령을 붙인다. 경로나 브랜치 이름에 셸이 풀
수 있는 글자가 들었으면 명령 없이 넘긴다. git 은 모두 `core.longpaths=true` 로 친다
(스킬 머리 문단).

판정. 워크트리마다 아래 순서로 보고 처음 어긋난 것을 이유로 찍는다. 모두 맞아야 지운다.
- 자리. 등록이 `prunable` 이거나 폴더가 없거나, 그 폴더에서 `git rev-parse --show-toplevel` 이 그
  경로가 아니면 사람에게 넘긴다. `.git` 파일이 없는 폴더에서 친 git 은 루트 저장소에 닿아, 그
  status 는 루트의 것이다(대기열 135, 일지 2026-10-07-03).
- 판정 1, 병합됐다. 분리 HEAD 면 넘긴다. 병합된 PR 중 머리 브랜치 이름이 같은 것의 `headRefOid` 가
  브랜치 끝(그 워크트리의 HEAD)과 같아야 한다. 이름이 같은 PR 이 없으면 남기고, 있는데 머리가 다르면
  넘긴다. 이름만 보면 포크의 같은 이름 브랜치를 잡으므로 머리를 견준다. squash 라 `git log` 로는
  가르지 못하고, 브랜치 끝이 `origin/main` 의 조상인 것으로도 판정하지 않는다. 막 따고 커밋하지 않은
  브랜치도 조상이다(일지 2026-10-05-05). 병합된 PR 은 `gh pr list` 한 번에 최근 1000개를 읽는다.
  그보다 오래된 것은 병합되지 않은 것으로 보여 남는다(안전한 쪽).
- 판정 2, 깨끗하다. `status --porcelain --untracked-files=all` 의 stdout 과 stderr 가 모두 비어야
  한다. stderr 의 경고는 git 이 그 아래를 보지 못했다는 뜻이다. `status --ignored` 의 `!!` 항목은
  다시 만들 수 있는 것(`RECREATABLE_*`, 루트와 바이트가 같은 `.claude/settings.local.json`)뿐이어야
  한다.
  `git worktree remove` 는 무시된 파일을 묻지 않고 지운다. `.env` 나 `traces/` 가 있으면 남긴다.
- 판정 3, 주인이 없다. 제목이 그 브랜치인 실행 중 세션이 있으면 남긴다. 잠금 사유는
  `claude session <이름> (pid <N>)` 모양이고 그 pid 가 살아 있으면 남긴다. 죽었으면 `remove` 가 풀고
  지운다. 사유가 다른 모양이면 넘긴다. 잠금이 없다고 주인이 없는 것은 아니다. `git worktree add` 로
  판 워크트리와 `EnterWorktree(path)` 로 들어간 워크트리는 잠기지 않는다(일지 2026-10-06-04).
  잠금 다음에는 그 폴더나 그 아래를 작업 디렉터리로 쥔 프로세스를 보고, 있으면 이름과 pid 를
  들어 남긴다(대기열 186). 쉬는 세션은 `isRunning` 이 아니라 제목으로 잡히지 않는데, 데스크톱 앱이
  `--resume` 으로 띄운 그 세션의 `claude.exe` 가 워크트리 루트를 쥐고 있었다(판정 4의 1의 근거).
  이 단계가 없던 판은 그 워크트리를 지운다(또는 아래처럼 넘긴다)로 내고 `remove` 의 점유 탐침에서야
  막혔다. 2026-10-12 에 작업 디렉터리로 쥐여 있던 셋 중 둘은 그 판이 제목 모를 세션 때문에 넘겨
  사람에게 승인을 물었고, 하나는 판정 2가 먼저 남겼다. 이 판으로 같은 자리를 다시 판정하니 그 둘을
  `claude.exe` 의 pid 를 들어 남겼다(일지 2026-10-12-14). 프로세스는 `judge` 한 번에 한 번 훑는다.
  그 세션에서 `lock_holder.py --folder` 가 프로세스 720개 중 539개의 작업 디렉터리를 0.11초 안에
  읽었다. 볼 수 없으면(윈도·리눅스 밖의 OS, 32비트 파이썬, 읽다 실패) 이 단계를 건너뛰고 판정 4의
  점유 탐침에 맡긴다.
  작업 디렉터리 다음에는 그 폴더 아래 파일을 모듈로 올린 프로세스를 보고, 있으면 이름과 pid 를
  들어 남긴다(대기열 201). 올린 모듈은 이름 바꾸기를 막지 않아(`lock_holder.py` 의 G,
  `worktree_occupancy.py` 의 E) 판정 4의 1을 지나고, 앞지우기가 그 파일에서 `WinError 5` 로
  막힌다(`.scratch/harness/probes/module_holder.py` 의 G·E). 프로세스마다 올린 모듈의 매핑
  이름(`GetMappedFileNameW`)과 그 파일의 다른 하드링크 이름(`FindFirstFileNameW`)을 폴더와 견주므로,
  워크트리 밖 이름으로 올린 것(E)도 잡는다. uv 의 `.venv` 와 pnpm 의 `node_modules` 는 기본으로 모듈
  파일 다수를 캐시에서 하드링크로 채워, 다른 체크아웃의 파이썬이나 node 가 올린 모듈이 이 워크트리의
  같은 파일을 막는다. 2026-10-13 에 이 판정이 병합된 워크트리 대부분을 같은 pid 몇으로 남겼다(대기열
  217). 그래서 Claude 세션의 uv 는 설정 `env` 의 `UV_LINK_MODE=copy` 로 패키지를 복사로 깐다.
  복사 `.venv` 는 다른 `.venv` 의 파이썬이 올린 모듈에 잡히지 않고 그 파일이 지워졌으며, 자기
  `.venv` 에서 띄운 파이썬은 여전히 잡혔다(`.scratch/harness/probes/venv_link_mode.py`, 세 번). 그
  값 전에 깐 패키지와 사용자 터미널의 uv 가 깐 패키지, pnpm 의 `node_modules` 는 하드링크로 남아 이
  판정이 그대로 본다. 2026-10-12 에 옆 이름에 남은 `spec-pipeline-and-pytest-ids.tidy-probe`
  의 `.venv` 와 `node_modules` 에서 모듈을 올린 프로세스(`module_holder.py --folder` 가 pid 를 댔다)
  가운데 파이썬은 다른 워크트리의 `.venv` 에서 돈 pytest 와 명령줄이 `-mpre_commit hook-impl` 인
  것이었고 (그 명령줄은 `Get-CimInstance Win32_Process` 로 손으로 봤다, 일지 2026-10-12-38),
  나머지는 실행 파일 이름이 `node.exe`·`esbuild.exe` 였다. 그 파일들의 링크 수는 30~38 이었다.
  `remove` 가 그 폴더의 `.pyd` 에서 다섯 번 막힌 때에 무엇이 쥐었는지는 재지 않았다. 모듈은 `judge`
  한 번에 한 번 훑는다. 그 프로브의 `--folder` 에서 프로세스 770~771개, 항목 3만여 개에 0.90~1.22초,
  갈래에서 0.94~1.03초였다. 윈도 밖은 보지 않는다. 그 OS 는 적재한 파일도 지울 수 있는 것으로 알고
  있다(어림).
  제목이 체크아웃된 어느 브랜치와도 맞지 않는 실행 중 세션이 있으면 지울 워크트리 후보를 모두
  넘긴다. 그 세션이 어느 워크트리에 있는지 알 수 없다(일지 2026-10-06-03). 등록 없는 폴더는 넘기지
  않는다. git 으로 일할 수 없는 자리라 세션이 쓰는 워크트리가 아니고, 그 자리를 작업 디렉터리로 쥔
  세션은 위의 훑기가 잡는다. 사람이 그 세션이 후보에 없다고 답하면 부르는 쪽이 `remove` 를 부른다.
  `remove` 의 재판정은 세션을 보지 않고, 쥔 프로세스는 앞지우기 직전에만 다시 본다(판정 4의 2).
체크아웃되지 않은 로컬 브랜치는 판정 1만 본다. `.claude/worktrees/` 아래인데 등록이 없는 폴더는
아래 "등록 없는 폴더"로 가른다.

판정 4, 지운다(`remove`). 후보 하나를 다시 판정하고(세션과 쥔 프로세스는 빼고. 쥔 프로세스는
1의 탐침과 2의 다시 거르기가 본다) 브랜치와 HEAD 가 인자와 같을 때만, 아래 순서로 지운다.
1. 점유 탐침. 워크트리 폴더를 옆 이름으로 바꿨다가 되돌린다. 윈도에서 그 아래를 작업 디렉터리로
   쥔 프로세스나 그 안의 파일을 연 프로세스가 있으면 이름 바꾸기가 막힌다. 그대로 지우면 git 은
   `Permission denied`·`Invalid argument` 로 지우다 만 폴더를 남긴다(`.scratch/harness/probes/
   worktree_occupancy.py` 의 B·C). 막히면 아무것도 바꾸지 않고 멈추고, 그 폴더나 그 아래를 작업
   디렉터리로 쥔 프로세스의 이름과 pid 를 이유에 붙인다(대기열 177). 윈도는 프로세스마다 PEB 의
   작업 디렉터리를, 리눅스는 `/proc/<pid>/cwd` 를 읽는다. 2026-10-12 에 DELETE 권한으로 열리지
   않던(공유 위반) 워크트리 셋은 모두 `claude.exe` 가 그 루트를 작업 디렉터리로 쥐었다. Restart
   Manager 는 폴더를 받지 않고 작업 디렉터리를 보지 못한다. 그중 한 워크트리의 파일 4만여 개를
   5000개 덩이로 등록하면 209초였고 덩이 일부는 오류 29 로 실패했으며, 쥔 `claude.exe` 대신 다른
   프로세스를 댔다(여기까지 `.scratch/harness/probes/lock_holder.py`). 그 `claude.exe` 셋의 부모는
   데스크톱 앱이었고, 그 세션들은 `list_sessions` 에서 `isRunning` 이 아니었다(손으로 봤다,
   `Get-CimInstance Win32_Process` 와 `list_sessions`, 일지 2026-10-12-08).
   되돌리기가 막히면 `RESTORE_WAITS` 만큼 기다리며 다시 시도하고, 끝내 막히면 멈춘다(종료 3).
   2026-10-12 에 옮기기는 지났는데 되돌리기가 `WinError 5` 로 한 번 막혀 폴더가 옆 이름에 남고
   등록이 폴더를 잃었다(대기열 202, 일지 2026-10-12-28). 그 틈에 무엇이 폴더를 쥐었는지는 재지
   않았다.
2. 다시 거르기. 판정 1~3을 한 번 더 내고, 지울 무시된 항목도 그때 읽는다. 판정 뒤에 생긴 `.env` 나
   새 파일을 앞지우기가 지우지 않게 한다. 이때는 프로세스를 한 번 훑어 쥔 프로세스(작업 디렉터리와
   모듈)도 본다. 리눅스의 탐침은 작업 디렉터리를, 윈도의 탐침은 올린 모듈을 보지 못해, `judge` 뒤에
   들어온 주인은 여기서 잡는다(PR #184 리뷰, 대기열 201). 어긋나면 아무것도 바꾸지 않고 멈춘다.
3. 죽은 잠금을 푼다. 1·2가 막히면 잠금도 그대로 남도록 그 뒤다.
4. 앞지우기. 2가 읽은 무시된 항목을 이 도구가 git 보다 먼저 지운다. 막히면 멈춘다. 등록과
   `.git` 파일은 남는다(프로브의 F). 워크트리 밖의 하드링크 이름으로 같은 DLL 을 적재한 프로세스는
   이름 바꾸기를 지나는데 git 은 지우다 만 폴더를 남긴다(프로브의 E). 2가 그런 프로세스를 남기므로
   여기서 막히는 것은 2가 보지 못한 것(2 뒤에 올린 모듈, 열 수 없는 프로세스가 올린 모듈, 윈도 폴더
   아래 모듈의 다른 이름, 연 파일)이다. 2026-10-07 에 `mutate-restore-guard` 가 `Invalid argument`
   로 `yaml` 의 `.pyd` 에서 멈췄다(손으로 봤다, 일지 2026-10-07-15). `.venv` 가 하드링크일 수
   있어(판정 3) 이 도구 자신이 서드파티 확장 모듈을 올리면 지울 워크트리의 같은 파일을 쥐므로, 이
   도구는 표준 라이브러리만 쓴다. 링크(심볼릭 링크, 정션)는 따라가지 않고 링크 자체만 지운다.
5. `git worktree remove <경로>`. git 2.32 는 지우다 실패해도 등록을 지우고(`.scratch/harness/probes/
   worktree_longpath.py`), 그 폴더의 `.git` 파일도 지운다(`worktree_occupancy.py` 의 B·C·E).
6. `git branch -D <브랜치>`. squash 병합이라 `-d` 는 병합을 알아보지 못한다.

등록 없는 폴더(`remove-stray`, 대기열 148). `.claude/worktrees/` 바로 아래인데 등록이 없는 폴더다.
지우다 실패한 `git worktree remove` 가 등록과 `.git` 파일만 지우고 남긴 폴더와 빈 폴더가 쌓였다
(2026-10-12 에 일곱 가운데 빈 폴더 셋, 지우다 만 폴더 셋이었다. 손으로 봤다, 일지 2026-10-12-38).
그 안에서 git 은
루트에 닿아 판정 2를 내지 못하므로 내용으로 가른다. 아래 순서로 보고 처음 어긋난 것을 찍는다.
그 자리 자신이 링크(심볼릭 링크, 정션)면 안을 읽지 않고 넘긴다.
- `.git` 이 있으면 넘긴다. 어느 등록이 그 폴더를 잃었을 수 있다. 점유 탐침이 옆 이름에 남긴
  폴더이고 원래 이름의 등록이 폴더를 잃은 채 남아 있으면, 되돌릴 자리를 알린다.
- 읽다 막히면 남긴다.
- 링크가 있으면 남긴다. 다시 만들 수 있는 폴더(`RECREATABLE_DIRS` 의 이름, `RECREATABLE_PATHS` 의
  자리)는 링크여도 들어가지 않는다. `RECREATABLE_DIRS` 의 이름은 `.grimp_cache` 말고는 루트의
  `.gitignore` 가 어느 깊이에서나 무시한다(`.grimp_cache` 가 어떻게 무시되는지는 보지 않았다). 그
  폴더의 `.gitignore` 는 지우다 만 폴더에서 먼저 지워졌을 수 있어 보지 않는다.
- 나머지 파일은 내용이 참조(브랜치, 원격, 태그, `refs/stash`)에서 닿는 커밋에 있어야 한다. 파일마다
  git 의 블롭 이름을 셈해 `git rev-list --all --objects` 와 견준다. git 이 텍스트로 보는 내용은 CRLF
  를 LF 로 바꾼 이름도 본다(`.gitattributes` 의 `* text=auto eol=lf`). 텍스트인지는 git 의
  판별(NUL, 홀로 쓰인 CR, 인쇄 문자 128개당 비인쇄 문자 하나를 넘는 비율)을 흉내 낸다. 그 판별은
  git 소스를 읽지 않고 알고 있던 것이고(어림), 테스트가 입력 몇에서 `git hash-object` 와 같은 이름을
  내는지 본다. 다시 만들 수 있는 파일과 루트와 바이트가 같은 설정 파일은 뺀다. 커밋에 없는 파일(새
  파일, 고친 파일, `.env`)이 하나라도 있으면 남긴다.
- 쥔 프로세스(판정 3의 작업 디렉터리와 모듈)가 있으면 남긴다.
`remove-stray` 는 그 자리가 `.claude/worktrees/` 바로 아래의 등록 없는 폴더인지 다시 보고, 판정을
다시 내고, 판정 4의 1의 탐침을 거쳐, 쥔 프로세스까지 넣어 다시 판정한 뒤 폴더째 지운다(링크는
따라가지 않는다). git 은 그 폴더에서 부르지 않는다.

못 보는 것.
- 앞지우기 뒤에 남은 추적 파일을 다른 프로세스가 워크트리 밖의 하드링크 이름으로 적재한 것.
  추적 파일은 하드링크가 아니라 드물다.
- 탐침과 git 사이에 새로 생긴 점유와 파일. 다시 거른 뒤 git 이 지울 때까지의 틈이다.
- 세션이 쓰던 워크트리인지. 제목, 잠금, 작업 디렉터리로만 가린다(판정 3). 앱이 그 세션의 CLI 를
  띄워 두지 않았으면 작업 디렉터리로도 잡히지 않는다.
- 맥과 리눅스의 점유. 재지 않았다. 그 OS 는 열린 파일과 작업 디렉터리가 이름 바꾸기를 막지 않는
  것으로 알고 있어(어림) 탐침이 점유를 보지 못한다고 본다. 리눅스에서 작업 디렉터리로 쥔 것은
  판정 3과 판정 4의 2가 남긴다. 2 뒤에 들어온 것은 위의 탐침과 git 사이의 틈과 같은 결로 보지
  못한다.
- 작업 디렉터리와 모듈 말고 다른 것으로 쥔 프로세스. 그 안의 파일을 연 프로세스
  (`lock_holder.py` 의 C)는 판정 3을 지나고, `remove` 에서 이름 바꾸기를 막아도 쥔 것을 찾지
  못했다고 적힌다.
- 열 수 없는 프로세스의 작업 디렉터리와 모듈. 2026-10-12 에 이 PC 의 프로세스 672개 중 493개의
  작업 디렉터리를 읽었다(`lock_holder.py --folder`). 읽지 못한 것은 건너뛴다. 그것이 무엇인지
  (다른 사용자, 높은 권한)는 재지 않았다.
- 32비트 프로세스. 건너뛰지 않고 64비트 PEB 를 읽는데, 그 사본은 32비트 코드가 바꾼 작업
  디렉터리를 따르지 않는다고 알고 있어 낡은 경로로 이름을 댈 수 있다(어림, 재지 않았다). 그
  프로세스가 올린 32비트 모듈은 `LIST_MODULES_ALL` 로 함께 읽는다고 알고 있다(어림, 재지 않았다).
- 윈도 폴더(`SystemRoot`) 아래 모듈의 다른 하드링크 이름. 펼치지 않는다.
- 등록 없는 폴더에서 `WHOLE_READ_LIMIT`(64MiB)를 넘는 파일의 줄 끝을 바꾼 이름. 덩이로 그대로의
  이름만 셈해, git 이 텍스트로 넣은 큰 파일은 커밋에 없는 것으로 보여 남는다(안전한 쪽).
- 드라이브 문자가 없는 장치(네트워크 공유, 문자 없는 마운트 지점)에서 올린 모듈. 매핑 이름을
  드라이브 경로로 바꾸지 못해 버린다.
- 등록 없는 폴더에서, 같은 내용이 다른 경로로 커밋된 파일과 빈 파일(참조에서 닿는 커밋에 빈 파일이
  하나라도 있으면). 커밋에 있는 것으로 본다. 내용은 그 참조가 남아 있는 동안 되살릴 수 있다. 같은
  정리에서 `remove-branch` 가 그 참조(병합된 브랜치)를 지우면 로컬에서는 닿지 않게 된다. 실행 비트와
  빈 폴더는 보지 않는다. 리플로그에만 남은 커밋과 맨 위가 아닌 stash 의 내용은 커밋에 없는 것으로
  보여 남는다(안전한 쪽). 텍스트 판별이 git 과 갈리면, 도구가 텍스트로 본 내용은 LF 이름까지 셈해
  줄 끝만 다른 내용을 커밋에 있는 것으로 보고(지우는 쪽, 줄 끝만 잃는다), 바이너리로 본 내용은
  그대로의 이름만 셈해 남긴다(안전한 쪽).

종료 코드. `judge`: 0 찍었다, 2 인자가 틀렸거나 주 체크아웃이 아니다, 3 git 이나 gh 가 실패했다.
`remove`·`remove-branch`: 0 지웠다. 1 망가뜨린 것 없이 멈췄다. 아무것도 바꾸지 않았거나(1·2에서
멈췄다), 죽은 잠금을 풀고 다시 만들 수 있는 것만 지웠거나(4에서 멈췄다. 등록과 `.git` 이 남는다),
워크트리는 지웠는데 브랜치가 남았다(6).
다음 후보로 가도 된다. 2 인자가 틀렸거나 주 체크아웃이 아니다. 3 멈추고 사람에게 넘긴다. 지우다 만
폴더나 옆 이름에 남은 폴더가 생겼을 수 있거나, git·gh 를 부르지 못했다.
`remove-stray`: 0 지웠다. 1 망가뜨린 것 없이 멈췄다. 아무것도 바꾸지 않았거나, 지우다 막혀 다시
만들 수 있거나 커밋에 있는 것만 지웠다. 2·3 은 `remove` 와 같다.
"""

from __future__ import annotations

import argparse
import csv
import ctypes
import functools
import hashlib
import json
import os
import re
import shutil
import stat
import string
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

type Action = Literal["delete", "keep", "human", "hold"]
type GitRunner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]
type Json = dict[str, Json] | list[Json] | str | int | float | bool | None
type ProcessPath = tuple[int, str, str]  # (pid, 실행 파일 이름, 작업 디렉터리나 모듈의 경로)
type HolderKind = Literal["cwd", "module"]

COMMAND = "uv run python tools/tidy_checkouts.py"
WORKTREES_DIR = ".claude/worktrees"
SETTINGS = ".claude/settings.local.json"
PROBE_SUFFIX = ".tidy-probe"
MERGED_LIMIT = 1000
RECREATABLE_DIRS = frozenset(
    {
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".import_linter_cache",
        ".grimp_cache",
        "node_modules",
        ".next",
        "test-results",
        "playwright-report",
        "blob-report",
        "coverage",
    }
)
RECREATABLE_FILES = frozenset({"next-env.d.ts"})
# 이름이 흔해 자리째로 본다. `.gitignore` 가 앵커를 붙인 디자인 시스템 패키지의 빌드다(ADR 0026)
RECREATABLE_PATHS = frozenset({"web/packages/ui/dist/", "web/packages/ui/storybook-static/"})

_LOCK_PID = re.compile(r"^claude session \S+ \(pid (\d+)\)$")
# 찍은 명령을 에이전트가 셸에 그대로 친다. git 은 브랜치 이름에 `$`·`;`·`(`·백틱을 허락해, 그런
# 이름이 든 명령은 찍지 않고 사람에게 넘긴다(셀프 보안 리뷰, 일지 2026-10-07-15)
_SHELL_UNSAFE = re.compile(r"[\s$`\"'\\;&|<>(){}*?\[\]!#~]")
_ACTIONS: dict[Action, str] = {
    "delete": "지운다",
    "keep": "남긴다",
    "human": "넘긴다",
    "hold": "넘긴다",
}
_HOLDER_LABELS: dict[HolderKind, str] = {
    "cwd": "작업 디렉터리로 쥔 프로세스",
    "module": "모듈을 올린 프로세스",
}
# git 의 텍스트 판별에서 비인쇄로 세는 바이트. 32 아래에서 백스페이스·탭·ESC·폼 피드와 CR·LF 를 뺀
# 것과 DEL 이다(`looks_text`)
_NONPRINTABLE = bytes(byte for byte in [*range(32), 127] if byte not in (8, 9, 10, 12, 13, 27))
# 등록 없는 폴더의 파일을 통째로 읽어 블롭 이름을 셈하는 크기의 상한(바이트). 넘으면 덩이로
# 읽는다(`file_blob_ids`, PR 직전 버그·성능 리뷰)
WHOLE_READ_LIMIT = 64 * 1024 * 1024
# 되돌리기를 다시 시도하기 전에 기다리는 초. 옮기기가 지난 뒤 되돌리기가 `WinError 5` 로 한 번
# 막혔다(대기열 202). 무엇이 그 틈에 폴더를 쥐었는지는 재지 않았다
RESTORE_WAITS = (0.2, 0.5, 1.0, 2.0)


class ToolError(Exception):
    """git 이나 gh 를 부르지 못했다. 판정을 낼 수 없다."""


@dataclass(frozen=True)
class Worktree:
    """`git worktree list --porcelain` 의 한 항목. `locked` 는 잠금 사유다(사유가 없으면 "")."""

    path: str
    head: str | None = None
    branch: str | None = None
    locked: str | None = None
    prunable: bool = False
    bare: bool = False


@dataclass(frozen=True)
class Facts:
    """판정 2와 자리 판정의 재료. 자리가 어긋나면 status 를 읽지 않아 빈 값이다."""

    exists: bool
    toplevel: str | None
    status: str
    status_err: str
    ignored: tuple[str, ...]
    settings_same: bool


@dataclass(frozen=True)
class Verdict:
    """`hold` 는 지울 것이었는데 제목 모를 세션 때문에 넘긴 것이다. 사람이 승인하면 지운다.
    `human` 은 사람이 직접 본다. `unlock` 은 지우기 전에 죽은 잠금을 풀어야 한다는 뜻이다."""

    action: Action
    path: str
    reason: str
    branch: str | None = None
    head: str | None = None
    unlock: bool = False


@dataclass(frozen=True)
class Holder:
    """워크트리 폴더를 쥔 프로세스. `image` 는 실행 파일 이름이다(모르면 ""). `kind` 는 쥔 모양이다.
    `cwd` 는 작업 디렉터리로, `module` 은 그 아래 파일(하드링크 이름 포함)을 모듈로 올려 쥐었다."""

    pid: int
    image: str
    kind: HolderKind = "cwd"


# --- 바깥을 부르는 것 ---------------------------------------------------------------------------


def real_git(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """`GIT_OPTIONAL_LOCKS=0`: 남의 워크트리에서 친 `status` 가 색인을 고쳐 쓰며 잠그지 않는다."""
    return subprocess.run(
        ["git", "-c", "core.longpaths=true", *args],
        cwd=cwd,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def gh_merged_heads(root: Path) -> dict[str, frozenset[str]]:
    fields = "headRefName,headRefOid"
    command = ["gh", "pr", "list", "--state", "merged", "--limit", str(MERGED_LIMIT)]
    try:
        result = subprocess.run(
            [*command, "--json", fields],
            cwd=root,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        raise ToolError(f"gh 를 띄우지 못했다: {error}") from error
    if result.returncode != 0:
        raise ToolError(f"gh pr list 가 {result.returncode} 로 끝났다: {result.stderr.strip()}")
    try:
        return parse_merged(result.stdout)
    except ValueError as error:
        raise ToolError(f"gh pr list 의 출력을 읽지 못했다: {error}") from error


def process_alive(pid: int) -> bool:
    """그 pid 의 프로세스가 있는지. 알 수 없으면 있다고 본다(지우지 않는 쪽)."""
    if sys.platform == "win32":
        query = ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"]
        try:
            result = subprocess.run(query, capture_output=True, text=True, errors="replace")
        except OSError:
            return True
        return result.returncode != 0 or tasklist_has(result.stdout, pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _linux_cwds() -> list[ProcessPath]:
    """`/proc/<pid>/cwd` 를 읽는다. 읽을 수 없는 프로세스(다른 사용자의 것)는 건너뛴다."""
    found: list[ProcessPath] = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            cwd = os.readlink(f"/proc/{entry}/cwd")
        except OSError:
            continue
        try:
            image = os.path.basename(os.readlink(f"/proc/{entry}/exe"))
        except OSError:
            image = ""
        found.append((int(entry), image, cwd))
    return found


if sys.platform == "win32":
    _QUERY_LIMITED = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
    _VM_READ = 0x0010  # PROCESS_VM_READ
    # x64 의 자리: PEB.ProcessParameters, 그 안의 CurrentDirectory.DosPath(UNICODE_STRING)
    _PEB_PARAMS = 0x20
    _PARAMS_CWD = 0x38
    _LIST_MODULES_ALL = 0x03  # 32비트와 64비트 모듈 모두
    _LONG_PATH = 32768
    _INVALID_HANDLE = ctypes.c_void_p(-1).value

    class _BasicInformation(ctypes.Structure):
        """PROCESS_BASIC_INFORMATION. `peb` 가 그 프로세스 안의 PEB 주소다."""

        _fields_ = [
            ("exit_status", ctypes.c_void_p),
            ("peb", ctypes.c_void_p),
            ("affinity", ctypes.c_void_p),
            ("priority", ctypes.c_void_p),
            ("pid", ctypes.c_void_p),
            ("parent", ctypes.c_void_p),
        ]

    def _windows_api() -> tuple[ctypes.WinDLL, ctypes.WinDLL]:
        """핸들과 포인터가 64비트에서 잘리지 않게 원형을 적은 kernel32 와 ntdll."""
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        ntdll = ctypes.WinDLL("ntdll")
        dword, handle, pointer = ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p
        kernel.OpenProcess.restype = handle
        kernel.OpenProcess.argtypes = [dword, ctypes.c_int, dword]
        kernel.CloseHandle.argtypes = [handle]
        kernel.ReadProcessMemory.argtypes = [
            handle,
            pointer,
            pointer,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        kernel.QueryFullProcessImageNameW.argtypes = [
            handle,
            dword,
            ctypes.c_wchar_p,
            ctypes.POINTER(dword),
        ]
        kernel.K32EnumProcesses.argtypes = [ctypes.POINTER(dword), dword, ctypes.POINTER(dword)]
        kernel.K32EnumProcessModulesEx.argtypes = [
            handle,
            ctypes.POINTER(ctypes.c_void_p),
            dword,
            ctypes.POINTER(dword),
            dword,
        ]
        kernel.K32GetMappedFileNameW.argtypes = [handle, pointer, ctypes.c_wchar_p, dword]
        kernel.QueryDosDeviceW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, dword]
        kernel.FindFirstFileNameW.restype = handle
        kernel.FindFirstFileNameW.argtypes = [
            ctypes.c_wchar_p,
            dword,
            ctypes.POINTER(dword),
            ctypes.c_wchar_p,
        ]
        kernel.FindNextFileNameW.argtypes = [handle, ctypes.POINTER(dword), ctypes.c_wchar_p]
        kernel.FindClose.argtypes = [handle]
        ntdll.NtQueryInformationProcess.argtypes = [handle, ctypes.c_int, pointer, dword, pointer]
        return kernel, ntdll

    def _windows_pids(kernel: ctypes.WinDLL) -> list[int]:
        size = 1024
        while True:
            array = (ctypes.c_ulong * size)()
            used = ctypes.c_ulong()
            if not kernel.K32EnumProcesses(array, ctypes.sizeof(array), ctypes.byref(used)):
                return []
            count = used.value // ctypes.sizeof(ctypes.c_ulong)
            if count < size:
                return list(array[:count])
            size *= 2

    def _read_memory(kernel: ctypes.WinDLL, handle: int, address: int, size: int) -> bytes | None:
        buffer = ctypes.create_string_buffer(size)
        got = ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle, address, buffer, size, ctypes.byref(got)):
            return None
        return buffer.raw if got.value == size else None

    def _peb_cwd(kernel: ctypes.WinDLL, ntdll: ctypes.WinDLL, handle: int) -> str | None:
        info = _BasicInformation()
        size = ctypes.sizeof(info)
        status = ntdll.NtQueryInformationProcess(handle, 0, ctypes.byref(info), size, None)
        peb = info.peb
        if status != 0 or not isinstance(peb, int):
            return None
        raw = _read_memory(kernel, handle, peb + _PEB_PARAMS, 8)
        if raw is None:
            return None
        raw = _read_memory(kernel, handle, int.from_bytes(raw, "little") + _PARAMS_CWD, 16)
        if raw is None:
            return None
        length = int.from_bytes(raw[0:2], "little")
        buffer = int.from_bytes(raw[8:16], "little")
        if length == 0 or buffer == 0:
            return None
        text = _read_memory(kernel, handle, buffer, length)
        return text.decode("utf-16-le", errors="replace") if text is not None else None

    def _image_name(kernel: ctypes.WinDLL, handle: int) -> str:
        buffer = ctypes.create_unicode_buffer(1024)
        size = ctypes.c_ulong(len(buffer))
        if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return ""
        return os.path.basename(buffer.value)

    def _windows_cwds() -> list[ProcessPath] | None:
        """프로세스마다 PEB 의 작업 디렉터리를 읽는다. 열지 못하는 프로세스는 건너뛴다.

        x64 의 자리만 안다. 32비트 파이썬이면 None 이다.
        """
        if ctypes.sizeof(ctypes.c_void_p) != 8:
            return None
        kernel, ntdll = _windows_api()
        found: list[ProcessPath] = []
        for pid in _windows_pids(kernel):
            handle = kernel.OpenProcess(_QUERY_LIMITED | _VM_READ, False, pid)
            if not handle:
                continue
            try:
                cwd = _peb_cwd(kernel, ntdll, handle)
                if cwd is not None:
                    found.append((pid, _image_name(kernel, handle), cwd))
            finally:
                kernel.CloseHandle(handle)
        return found

    def _drives(kernel: ctypes.WinDLL) -> dict[str, str]:
        """장치 경로(`\\Device\\HarddiskVolume2`)에서 드라이브(`C:`)로."""
        found: dict[str, str] = {}
        buffer = ctypes.create_unicode_buffer(1024)
        for letter in string.ascii_uppercase:
            if kernel.QueryDosDeviceW(f"{letter}:", buffer, len(buffer)):
                found[buffer.value] = f"{letter}:"
        return found

    def _module_paths(kernel: ctypes.WinDLL, handle: int, drives: Mapping[str, str]) -> list[str]:
        """그 프로세스가 적재한 모듈(실행 파일 자신 포함)의 경로. 읽지 못하면 빈 목록.

        이름은 `GetMappedFileNameW` 로 읽는다. `GetModuleFileNameExW` 로 읽는 훑기 고리 전체가
        프로세스 743개(모듈 2만 8천여 개)에서 5.5초였고, 모듈 목록과 이 길만 따로 재니
        0.6초였다(스크래치 스크립트로 손으로 봤다. 두 스크립트의 잰 범위가 같지 않다, 일지
        2026-10-12-38). 바꾼 판의 훑기 전체는 `module_holder.py` 에서 1초 안팎이었다. 앞의 길이 느린
        까닭은 재지 않았다.
        """
        size = 512
        while True:
            array = (ctypes.c_void_p * size)()
            needed = ctypes.c_ulong()
            listed = kernel.K32EnumProcessModulesEx(
                handle, array, ctypes.sizeof(array), ctypes.byref(needed), _LIST_MODULES_ALL
            )
            if not listed:
                return []
            count = needed.value // ctypes.sizeof(ctypes.c_void_p)
            if count <= size:
                break
            size = count
        buffer = ctypes.create_unicode_buffer(_LONG_PATH)
        paths: list[str] = []
        for module in array[:count]:
            if module is None or not kernel.K32GetMappedFileNameW(
                handle, module, buffer, len(buffer)
            ):
                continue
            path = dos_path(buffer.value, drives)
            if path is not None:
                paths.append(path)
        return paths

    def _link_names(kernel: ctypes.WinDLL, path: str) -> list[str]:
        """같은 파일의 하드링크 이름 전부(`path` 자신 포함). 읽지 못하면 빈 목록.

        `FindFirstFileNameW` 는 드라이브 없는 경로를 주어 `path` 의 드라이브를 붙인다. 하드링크는
        같은 볼륨 안에만 있다.
        """
        drive = os.path.splitdrive(_without_long_prefix(path))[0]
        buffer = ctypes.create_unicode_buffer(_LONG_PATH)
        length = ctypes.c_ulong(len(buffer))
        found = kernel.FindFirstFileNameW(long_path(path), 0, ctypes.byref(length), buffer)
        if found is None or found == _INVALID_HANDLE:
            return []
        names: list[str] = []
        try:
            while True:
                names.append(drive + buffer.value)
                length = ctypes.c_ulong(len(buffer))
                if not kernel.FindNextFileNameW(found, ctypes.byref(length), buffer):
                    return names
        finally:
            kernel.FindClose(found)

    def _windows_modules() -> list[ProcessPath] | None:
        """프로세스마다 적재한 모듈의 경로와 그 파일의 다른 하드링크 이름. 열지 못하는 프로세스는
        건너뛴다. 윈도 폴더 아래 모듈은 링크를 펼치지 않는다(그 링크는 WinSxS 안에 있다고 알고
        있다, 어림)."""
        if ctypes.sizeof(ctypes.c_void_p) != 8:
            return None
        kernel, _ = _windows_api()
        drives = _drives(kernel)
        loaded: list[tuple[int, str, str]] = []
        for pid in _windows_pids(kernel):
            handle = kernel.OpenProcess(_QUERY_LIMITED | _VM_READ, False, pid)
            if not handle:
                continue
            try:
                image = _image_name(kernel, handle)
                modules = _module_paths(kernel, handle, drives)
                loaded.extend((pid, image, path) for path in modules)
            finally:
                kernel.CloseHandle(handle)
        system = os.environ.get("SystemRoot", "C:\\Windows")
        names: dict[str, list[str]] = {}
        for _, _, path in loaded:
            if path not in names:
                names[path] = [] if is_within(path, system) else _link_names(kernel, path)
        found: list[ProcessPath] = []
        for pid, image, path in loaded:
            found.append((pid, image, path))
            found.extend((pid, image, name) for name in names[path] if not same_path(name, path))
        return found


def _process_cwds() -> list[ProcessPath] | None:
    """프로세스마다 (pid, 실행 파일 이름, 작업 디렉터리). 이 OS 에서 볼 수 없으면 None."""
    if sys.platform == "win32":
        return _windows_cwds()
    if sys.platform == "linux":
        return _linux_cwds()
    return None


def scan_processes() -> list[ProcessPath] | None:
    """프로세스마다 (pid, 실행 파일 이름, 작업 디렉터리). 이 OS 에서 볼 수 없거나 읽다 실패하면
    None.

    `judge` 는 한 번에 한 번(판정 3) 부른다. `remove` 는 점유 탐침이 막히면 이유를 대려고(판정 4의
    1), 지나가면 앞지우기 직전의 다시 거르기에서(판정 4의 2) 한 번 부른다.
    """
    try:
        return _process_cwds()
    except (OSError, AttributeError, ValueError, ctypes.ArgumentError):
        # DLL 이나 함수를 싣지 못했거나(OSError, AttributeError) 인자를 바꾸지 못했다. 읽다 난
        # 실패가 판정과 이유 줄을 지우지 않게 볼 수 없는 것으로 돌려준다(PR #182 claude-review)
        return None


def scan_modules() -> list[ProcessPath] | None:
    """프로세스마다 (pid, 실행 파일 이름, 적재한 모듈의 경로나 그 파일의 다른 하드링크 이름).
    윈도 밖이거나 읽다 실패하면 None. 부르는 때는 `scan_processes` 와 같다."""
    if sys.platform != "win32":
        return None
    try:
        return _windows_modules()
    except (OSError, AttributeError, ValueError, ctypes.ArgumentError):
        return None


def holders_in(
    processes: Sequence[ProcessPath] | None, folder: str, kind: HolderKind = "cwd"
) -> list[Holder] | None:
    """경로가 `folder` 이거나 그 아래인 프로세스를 pid 마다 하나. 볼 수 없었으면(None) None."""
    if processes is None:
        return None
    found: dict[int, Holder] = {}
    for pid, image, path in processes:
        if pid not in found and is_within(path, folder):
            found[pid] = Holder(pid, image, kind)
    return list(found.values())


def cwd_holders(folder: Path) -> list[Holder] | None:
    """한 폴더만 볼 때. 훑기와 거르기를 한 번에 한다(프로브 `lock_holder.py` 가 부른다)."""
    return holders_in(scan_processes(), str(folder))


def long_path(path: str | os.PathLike[str]) -> str:
    """윈도에서 MAX_PATH 를 넘는 경로를 파이썬이 다루도록 `\\\\?\\` 를 붙인 절대 경로.

    이미 절대 경로면 정규화하지 않고 구분자만 바꾼다. `os.path.abspath` 는 끝의 점과 공백을 떼고
    `nul` 같은 장치 이름을 장치로 바꿔, 등록 없는 폴더의 `trail.` 을 `trail` 로 읽고 그 폴더를 지울
    것으로 냈다(PR 직전 버그 리뷰가 손으로 재현했다). 그래서 `..` 이 든 절대 경로는 받지 않는다
    (`\\\\?\\` 경로에서 풀리지 않아 OSError 로 멈춘다).
    """
    text = os.fspath(path)
    if sys.platform != "win32":
        return os.path.abspath(text)
    if text.startswith("\\\\?\\"):
        return text
    if not os.path.isabs(text):
        text = os.path.abspath(text)
    text = text.replace("/", "\\")
    if text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + text[2:]
    return "\\\\?\\" + text


def _writable_retry(function: Callable[[str], object], target: str, error: BaseException) -> None:
    """읽기 전용 파일이면 쓰기를 켜고 한 번 더 지운다. 그래도 막히면 그 예외로 멈춘다."""
    if not isinstance(error, PermissionError):
        raise error
    os.chmod(target, stat.S_IWRITE)
    function(target)


def delete_path(path: Path) -> None:
    """무시된 항목 하나를 지운다. 링크는 따라가지 않고 링크 자체만 지운다. 막히면 OSError."""
    target = long_path(path)
    if os.path.islink(target) or os.path.isjunction(target):
        os.unlink(target)
    elif os.path.isdir(target):
        shutil.rmtree(target, onexc=_writable_retry)
    elif os.path.lexists(target):
        try:
            os.unlink(target)
        except PermissionError as error:
            _writable_retry(os.unlink, target, error)


@dataclass(frozen=True)
class Ops:
    """바깥을 부르는 자리. 테스트가 실패를 넣는다."""

    git: GitRunner = real_git
    merged: Callable[[Path], dict[str, frozenset[str]]] = gh_merged_heads
    pid_alive: Callable[[int], bool] = process_alive
    rename: Callable[[str, str], None] = os.rename
    delete: Callable[[Path], None] = delete_path
    processes: Callable[[], list[ProcessPath] | None] = scan_processes
    modules: Callable[[], list[ProcessPath] | None] = scan_modules
    sleep: Callable[[float], None] = time.sleep


def holders_from(
    processes: Sequence[ProcessPath] | None, modules: Sequence[ProcessPath] | None, folder: str
) -> list[Holder] | None:
    """훑은 작업 디렉터리와 모듈에서 `folder` 를 쥔 프로세스."""
    return combine_holders(holders_in(processes, folder), holders_in(modules, folder, "module"))


def holders_now(ops: Ops, folder: str) -> list[Holder] | None:
    """`folder` 를 작업 디렉터리로 쥐었거나 그 아래 모듈을 올린 프로세스. 훑기를 한 번씩 한다."""
    return holders_from(ops.processes(), ops.modules(), folder)


# --- 읽기 ---------------------------------------------------------------------------------------


def parse_worktrees(porcelain: str) -> list[Worktree]:
    worktrees: list[Worktree] = []
    fields: dict[str, str] = {}
    for line in [*porcelain.splitlines(), ""]:
        if line:
            key, _, value = line.partition(" ")
            fields[key] = value
            continue
        if "worktree" in fields:
            branch = fields.get("branch")
            worktrees.append(
                Worktree(
                    path=fields["worktree"],
                    head=fields.get("HEAD"),
                    branch=branch.removeprefix("refs/heads/") if branch is not None else None,
                    locked=fields.get("locked"),
                    prunable="prunable" in fields,
                    bare="bare" in fields,
                )
            )
        fields = {}
    return worktrees


def lock_pid(reason: str) -> int | None:
    match = _LOCK_PID.match(reason)
    return int(match.group(1)) if match else None


def parse_merged(text: str) -> dict[str, frozenset[str]]:
    """`gh pr list --json headRefName,headRefOid` 의 출력. 모양이 어긋나면 ValueError."""
    parsed: Json = json.loads(text)
    if not isinstance(parsed, list):
        raise ValueError("배열이 아니다")
    heads: dict[str, set[str]] = {}
    for row in parsed:
        if not isinstance(row, dict):
            raise ValueError("객체가 아닌 항목이 있다")
        name = row.get("headRefName")
        oid = row.get("headRefOid")
        if not isinstance(name, str) or not isinstance(oid, str):
            raise ValueError("headRefName 이나 headRefOid 가 문자열이 아니다")
        heads.setdefault(name, set()).add(oid)
    return {name: frozenset(oids) for name, oids in heads.items()}


def tasklist_has(output: str, pid: int) -> bool:
    """`tasklist /FO CSV /NH` 의 출력에 그 pid 의 줄이 있는지. 둘째 칸이 pid 다."""
    return any(len(row) >= 2 and row[1] == str(pid) for row in csv.reader(output.splitlines()))


def unrecreatable(ignored: Sequence[str], settings_same: bool) -> list[str]:
    """`status --ignored` 의 `!!` 항목 중 다시 만들 수 없는 것. 디렉터리는 `/` 로 끝난다."""
    kept: list[str] = []
    for entry in ignored:
        name = entry.rstrip("/").rsplit("/", 1)[-1]
        if entry.endswith("/"):
            if name in RECREATABLE_DIRS or entry in RECREATABLE_PATHS:
                continue
        elif name in RECREATABLE_FILES or (entry == SETTINGS and settings_same):
            continue
        kept.append(entry)
    return kept


def same_path(left: str, right: str) -> bool:
    return os.path.normcase(os.path.normpath(left)) == os.path.normcase(os.path.normpath(right))


def _without_long_prefix(path: str) -> str:
    """`\\\\?\\UNC\\` 와 `\\\\?\\` 머리를 뗀다. 그 머리째 작업 디렉터리를 옮긴 프로세스는 PEB 에
    머리가 남는다(PR 직전 버그 리뷰가 손으로 봤다)."""
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[len("\\\\?\\UNC\\") :]
    return path.removeprefix("\\\\?\\")


def dos_path(device_path: str, drives: Mapping[str, str]) -> str | None:
    """`GetMappedFileNameW` 가 준 장치 경로를 드라이브 경로로. 드라이브 문자가 없는 장치(네트워크
    공유, 문자 없는 마운트 지점)면 None 이다. `drives` 는 장치 경로에서 드라이브(`C:`)로."""
    for device, drive in drives.items():
        if device_path.startswith(device + "\\"):
            return drive + device_path[len(device) :]
    return None


@functools.cache
def _normalized(path: str) -> str:
    """견주려고 정규화한 경로. 판정 한 번에 모듈 항목 수만큼의 경로를 워크트리마다 다시 견주므로
    기억해 둔다(PR 직전 버그·성능 리뷰)."""
    return os.path.normcase(os.path.normpath(_without_long_prefix(path)))


def is_within(child: str, parent: str) -> bool:
    """`child` 가 `parent` 자신이거나 그 아래인지. `x2` 는 `x` 의 아래가 아니다."""
    inner = _normalized(child)
    outer = _normalized(parent)
    return inner == outer or inner.startswith(outer.rstrip(os.sep) + os.sep)


def combine_holders(
    cwd: Sequence[Holder] | None, module: Sequence[Holder] | None
) -> list[Holder] | None:
    """작업 디렉터리로 쥔 것과 모듈을 올린 것. 둘 다 볼 수 없었을 때만 None 이다."""
    if cwd is None and module is None:
        return None
    return [*(cwd or ()), *(module or ())]


def describe_holders(holders: Sequence[Holder] | None) -> str:
    """남긴 이유에 붙일 쥔 프로세스. 못 찾은 것(빈 목록)과 볼 수 없는 것(None)을 가른다."""
    if holders is None:
        return "쥔 프로세스를 찾지 못했다(이 OS 에서 볼 수 없거나 프로세스를 읽다 실패했다)"
    if not holders:
        # 한쪽 훑기만 볼 수 있었어도 빈 목록이 온다(리눅스는 모듈을 보지 않는다). 그래서 무엇을
        # 보았는지 단정하지 않고 이 도구가 대는 범위만 적는다
        return (
            "읽을 수 있는 프로세스에서 쥔 것을 찾지 못했다. 이 도구는 작업 디렉터리와 (윈도에서) "
            "올린 모듈만 대고, 읽지 못한 프로세스(다른 사용자, 높은 권한)와 그 안의 파일을 연 "
            "프로세스는 대지 못한다"
        )
    parts: list[str] = []
    for kind, label in _HOLDER_LABELS.items():
        names = ", ".join(
            f"{holder.image or '(이름 모름)'}(pid {holder.pid})"
            for holder in holders
            if holder.kind == kind
        )
        if names:
            parts.append(f"{label}: {names}")
    return "; ".join(parts)


# --- 판정 ---------------------------------------------------------------------------------------


def judge(
    wt: Worktree,
    facts: Facts,
    merged: Mapping[str, frozenset[str]],
    running: Sequence[str],
    alive: Callable[[int], bool],
    holders: Sequence[Holder] | None,
) -> Verdict:
    """워크트리 하나의 판정. 순서와 근거는 모듈 독스트링. `holders` 는 그 폴더를 작업 디렉터리로
    쥔 프로세스이고, 볼 수 없었으면 None 이다."""

    def verdict(action: Action, reason: str) -> Verdict:
        return Verdict(action, wt.path, reason, wt.branch, wt.head)

    if wt.prunable:
        return verdict("human", "등록이 prunable 이다. 지우다 만 폴더일 수 있다")
    if not facts.exists:
        return verdict("human", "등록은 있는데 폴더가 없다")
    if facts.toplevel is None or not same_path(facts.toplevel, wt.path):
        return verdict("human", f"그 폴더의 git 이 다른 저장소({facts.toplevel})를 읽는다")
    if wt.branch is None or wt.head is None:
        return verdict("human", "분리 HEAD 다")
    heads = merged.get(wt.branch)
    if not heads:
        return verdict("keep", "병합된 PR 이 없다")
    if wt.head not in heads:
        return verdict("human", "병합된 PR 의 머리와 브랜치 끝이 다르다")
    if facts.status:
        return verdict("keep", "바뀐 파일이 있다")
    if facts.status_err:
        return verdict("keep", f"git status 가 경고를 냈다: {facts.status_err.strip()[:120]}")
    extra = unrecreatable(facts.ignored, facts.settings_same)
    if extra:
        return verdict("keep", f"다시 만들 수 없는 무시된 항목: {', '.join(extra[:5])}")
    if wt.branch in running:
        return verdict("keep", "그 브랜치가 제목인 세션이 돈다")
    pid = None if wt.locked is None else lock_pid(wt.locked)
    if wt.locked is not None and pid is None:
        return verdict("human", f"잠금 사유에 pid 가 없다: {wt.locked or '(사유 없음)'}")
    if pid is not None and alive(pid):
        return verdict("keep", f"잠금 pid {pid} 가 살아 있다. 그 세션: {wt.locked}")
    if holders:
        return verdict("keep", f"{describe_holders(holders)}. 그 프로세스가 끝나야 지운다")
    if pid is None:
        return verdict("delete", "")
    dead = f"잠금 pid {pid} 는 죽었다. remove 가 풀고 지운다"
    return Verdict("delete", wt.path, dead, wt.branch, wt.head, unlock=True)


def hold_for_strangers(
    verdicts: Sequence[Verdict], running: Sequence[str], checked_out: set[str]
) -> list[Verdict]:
    """제목이 체크아웃된 어느 브랜치와도 맞지 않는 실행 중 세션이 있으면 지울 것을 넘긴다."""
    strangers = [title for title in running if title not in checked_out]
    if not strangers:
        return list(verdicts)
    reason = f"제목이 체크아웃된 어느 브랜치와도 맞지 않는 세션이 돈다: {', '.join(strangers)}"
    return [
        replace(v, action="hold", reason=reason) if v.action == "delete" else v for v in verdicts
    ]


def judge_branch(branch: str, tip: str, merged: Mapping[str, frozenset[str]]) -> Verdict:
    """체크아웃되지 않은 로컬 브랜치의 판정 1."""
    heads = merged.get(branch)
    if not heads:
        return Verdict("keep", branch, "병합된 PR 이 없다", branch, tip)
    if tip not in heads:
        return Verdict("human", branch, "병합된 PR 의 머리와 브랜치 끝이 다르다", branch, tip)
    return Verdict("delete", branch, "", branch, tip)


@dataclass(frozen=True)
class StrayFacts:
    """등록 없는 폴더의 판정 재료. `.git` 이 있으면 안을 읽지 않아 나머지는 빈 값이다.
    `error` 는 읽다 막힌 이유(없으면 ""), `links` 와 `uncommitted` 는 폴더 안의 상대 경로다."""

    has_git: bool
    error: str
    links: tuple[str, ...]
    uncommitted: tuple[str, ...]


def judge_stray(
    path: str,
    facts: StrayFacts,
    holders: Sequence[Holder] | None,
    orphan_home: str | None = None,
) -> Verdict:
    """등록 없는 폴더 하나의 판정. 순서와 근거는 모듈 독스트링의 "등록 없는 폴더". `orphan_home` 은
    이 폴더가 점유 탐침의 옆 이름일 때 폴더를 잃은 채 남은 원래 이름의 등록 경로다."""

    def verdict(action: Action, reason: str) -> Verdict:
        return Verdict(action, path, reason)

    if facts.has_git:
        reason = "등록 없는 폴더인데 .git 이 있다. 어느 등록이 이 폴더를 잃었을 수 있다"
        if orphan_home is not None:
            reason = (
                f"점유 탐침이 옆 이름에 남긴 폴더이고 {orphan_home} 의 등록이 폴더를 잃었다. 그"
                " 이름으로 되돌리면 등록이 다시 맞는다"
            )
        return verdict("human", reason)
    if facts.error:
        return verdict("keep", f"등록 없는 폴더를 읽다 막혔다: {facts.error}")
    if facts.links:
        return verdict("keep", f"등록 없는 폴더에 링크가 있다: {', '.join(facts.links[:5])}")
    if facts.uncommitted:
        shown = ", ".join(facts.uncommitted[:5])
        count = len(facts.uncommitted)
        return verdict("keep", f"등록 없는 폴더에 커밋에 없는 파일이 {count}개 있다: {shown}")
    if holders:
        return verdict("keep", f"{describe_holders(holders)}. 그 프로세스가 끝나야 지운다")
    return verdict("delete", "등록 없는 폴더")


def looks_text(data: bytes) -> bool:
    """git 이 줄 끝을 바꾸는 텍스트로 볼 내용인지. NUL, 홀로 쓰인 CR, 인쇄 문자 128개당 비인쇄 문자
    하나를 넘는 비율이면 바이너리다. CR·LF 는 어느 쪽에도 세지 않고, 끝의 `\\x1a` 하나도 어느
    쪽에도 세지 않는다. git 소스를 읽지 않고 알고 있던 규칙이라(어림) 테스트가 `git hash-object` 와
    견준다."""
    if b"\0" in data or data.count(b"\r") != data.count(b"\r\n"):
        return False
    counted = len(data) - len(data.translate(None, _NONPRINTABLE))
    printable = len(data) - counted - data.count(b"\r") - data.count(b"\n")
    nonprintable = counted - 1 if data.endswith(b"\x1a") else counted
    return (printable >> 7) >= nonprintable


def blob_ids(data: bytes) -> set[str]:
    """git 이 이 내용에 붙일 블롭 이름. `.gitattributes` 의 `* text=auto eol=lf` 라 git 이 텍스트로
    보는 내용은 CRLF 를 LF 로 바꾼 이름도 든다(`looks_text`)."""
    candidates = {data}
    if b"\r\n" in data and looks_text(data):
        candidates.add(data.replace(b"\r\n", b"\n"))
    return {
        hashlib.sha1(b"blob %d\0" % len(body) + body, usedforsecurity=False).hexdigest()
        for body in candidates
    }


# --- 배관 ---------------------------------------------------------------------------------------


def _checked(git: GitRunner, args: Sequence[str], cwd: Path) -> str:
    result = git(args, cwd)
    if result.returncode != 0:
        raise ToolError(f"git {' '.join(args)} 가 {result.returncode} 로 끝났다: {result.stderr}")
    return result.stdout


def _same_bytes(left: Path, right: Path) -> bool:
    try:
        return left.read_bytes() == right.read_bytes()
    except OSError:
        return False


def _misplaced(*, exists: bool, toplevel: str | None) -> Facts:
    """자리가 어긋나 status 를 읽지 않은 재료. 그 폴더의 git 은 루트에 닿을 수 있다."""
    return Facts(
        exists=exists, toplevel=toplevel, status="", status_err="", ignored=(), settings_same=False
    )


def gather(root: Path, wt: Worktree, git: GitRunner) -> Facts:
    path = Path(wt.path)
    if not path.is_dir():
        return _misplaced(exists=False, toplevel=None)
    top = git(["rev-parse", "--show-toplevel"], path)
    toplevel = top.stdout.strip() if top.returncode == 0 else None
    if toplevel is None or not same_path(toplevel, wt.path):
        return _misplaced(exists=True, toplevel=toplevel)
    status = git(["status", "--porcelain", "-z", "--untracked-files=all"], path)
    status_err = status.stderr or ("" if status.returncode == 0 else f"exit {status.returncode}")
    listed = git(["status", "--porcelain", "-z", "--ignored"], path)
    if listed.returncode != 0 and not status_err:
        status_err = listed.stderr or f"exit {listed.returncode}"
    ignored = tuple(item[3:] for item in listed.stdout.split("\0") if item.startswith("!! "))
    settings_same = _same_bytes(root / SETTINGS, path / SETTINGS)
    return Facts(
        exists=True,
        toplevel=toplevel,
        status=status.stdout,
        status_err=status_err,
        ignored=ignored,
        settings_same=settings_same,
    )


def reachable_objects(root: Path, git: GitRunner) -> frozenset[str]:
    """참조(브랜치, 원격, 태그, stash)에서 닿는 객체의 이름. 리플로그에만 남은 것과 매달린 객체는
    빼 둔다. 둘 다 시간이 지나면 git 이 지운다."""
    listed = _checked(git, ["rev-list", "--all", "--objects"], root)
    return frozenset(line.split(" ", 1)[0] for line in listed.splitlines() if line)


def _recreatable_dir(name: str, relative: str) -> bool:
    return name in RECREATABLE_DIRS or relative + "/" in RECREATABLE_PATHS


def _walk_stray(folder: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """((파일의 상대 경로, 그 파일을 열 경로), 링크의 상대 경로). 다시 만들 수 있는 폴더는 링크여도
    들어가지 않고 건너뛴다. 링크(심볼릭 링크, 정션)는 따라가지 않는다. 읽다 막히면 OSError.

    여는 경로는 `scandir` 가 준 그대로 들고 다닌다. 상대 경로를 다시 이어 붙여 정규화하면 끝에
    점이 붙은 이름이 점 없는 다른 파일로 읽힌다(`long_path`).
    """
    files: list[tuple[str, str]] = []
    links: list[str] = []
    pending = [("", long_path(folder))]
    while pending:
        relative, opened = pending.pop()
        with os.scandir(opened) as entries:
            for entry in entries:
                child = f"{relative}/{entry.name}" if relative else entry.name
                linked = entry.is_symlink() or entry.is_junction()
                directory = linked or entry.is_dir(follow_symlinks=False)
                if directory and _recreatable_dir(entry.name, child):
                    continue
                if linked:
                    links.append(child)
                elif directory:
                    pending.append((child, entry.path))
                else:
                    files.append((child, entry.path))
    return sorted(files), sorted(links)


def gather_stray(root: Path, folder: Path, reachable: Callable[[], frozenset[str]]) -> StrayFacts:
    """등록 없는 폴더의 재료. git 은 그 폴더에서 부르지 않는다(`.git` 이 없어 루트에 닿는다).
    `reachable` 은 확인할 파일이 있을 때만 부른다."""
    if os.path.lexists(long_path(folder / ".git")):
        return StrayFacts(has_git=True, error="", links=(), uncommitted=())
    try:
        files, links = _walk_stray(folder)
        named = [
            (relative, file_blob_ids(opened))
            for relative, opened in files
            if not _recreatable_file(root, folder, relative)
        ]
    except OSError as error:
        return StrayFacts(has_git=False, error=str(error), links=(), uncommitted=())
    known = reachable() if named else frozenset[str]()
    uncommitted = tuple(relative for relative, ids in named if ids.isdisjoint(known))
    return StrayFacts(has_git=False, error="", links=tuple(links), uncommitted=uncommitted)


def _recreatable_file(root: Path, folder: Path, relative: str) -> bool:
    """다시 만들 수 있는 파일(`RECREATABLE_FILES` 의 이름, 루트와 바이트가 같은 설정 파일)."""
    if relative.rsplit("/", 1)[-1] in RECREATABLE_FILES:
        return True
    return relative == SETTINGS and _same_bytes(root / SETTINGS, folder / SETTINGS)


def file_blob_ids(path: str) -> set[str]:
    """파일 하나의 `blob_ids`. `WHOLE_READ_LIMIT` 를 넘는 파일은 통째로 읽지 않고 덩이로 그대로의
    이름만 셈한다. 줄 끝을 바꾼 이름이 빠져, git 이 텍스트로 넣은 큰 파일은 남는 쪽이다."""
    size = os.stat(path).st_size
    with open(path, "rb") as handle:
        if size <= WHOLE_READ_LIMIT:
            return blob_ids(handle.read())
        digest = hashlib.sha1(b"blob %d\0" % size, usedforsecurity=False)
        for chunk in iter(functools.partial(handle.read, 1 << 20), b""):
            digest.update(chunk)
    return {digest.hexdigest()}


def _place(cwd: Path, git: GitRunner) -> tuple[Path, list[Worktree]]:
    """주 체크아웃의 루트와 워크트리 목록. 주 체크아웃이 아니면 ValueError."""
    top = git(["rev-parse", "--show-toplevel"], cwd)
    if top.returncode != 0:
        raise ValueError(f"git 저장소가 아니다: {top.stderr.strip()}")
    listing = parse_worktrees(_checked(git, ["worktree", "list", "--porcelain"], cwd))
    if not listing or not same_path(top.stdout.strip(), listing[0].path):
        raise ValueError("이 폴더는 워크트리다. 주 체크아웃 세션에서 돈다")
    prefix = _checked(git, ["rev-parse", "--show-prefix"], cwd).strip()
    if prefix.startswith(WORKTREES_DIR + "/"):
        raise ValueError(f"지우다 만 워크트리 폴더 안이다({prefix}). git 이 루트에 닿는다")
    return Path(listing[0].path), listing


def _unregistered(root: Path, listing: Sequence[Worktree]) -> list[Path]:
    """`.claude/worktrees/` 바로 아래인데 등록이 없는 폴더와 폴더를 가리키는 링크."""
    holder = root / WORKTREES_DIR
    if not holder.is_dir():
        return []
    return sorted(
        path
        for path in holder.iterdir()
        if path.is_dir() and not any(same_path(str(path), wt.path) for wt in listing)
    )


def _is_link(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _strays(root: Path, listing: Sequence[Worktree]) -> list[Path]:
    """등록 없는 폴더. 링크는 안을 읽지 않으려고 뺀다(`judge` 는 따로 넘긴다)."""
    return [path for path in _unregistered(root, listing) if not _is_link(path)]


def _orphan_home(stray: Path, listing: Sequence[Worktree]) -> str | None:
    """`stray` 가 점유 탐침의 옆 이름이고 원래 이름의 등록이 폴더를 잃은 채 남았으면 그 경로."""
    if not stray.name.endswith(PROBE_SUFFIX):
        return None
    home = stray.with_name(stray.name.removesuffix(PROBE_SUFFIX))
    registered = any(same_path(str(home), wt.path) for wt in listing)
    return home.as_posix() if registered and not os.path.lexists(home) else None


def _render_worktree(verdict: Verdict) -> str:
    command = f'{COMMAND} remove "{verdict.path}" {verdict.branch} {verdict.head}'
    return _render(verdict, "", command)


def _render_branch(verdict: Verdict) -> str:
    command = f"{COMMAND} remove-branch {verdict.branch} {verdict.head}"
    return _render(verdict, "브랜치를 ", command)


def _render_stray(verdict: Verdict) -> str:
    return _render(verdict, "", f'{COMMAND} remove-stray "{verdict.path}"')


def _render(verdict: Verdict, prefix: str, command: str) -> str:
    """판정 한 줄. `prefix` 는 라벨 앞에 붙는 말이다(브랜치 줄은 `브랜치를 `)."""
    label = prefix + _ACTIONS[verdict.action]
    names = (verdict.path, verdict.branch or "", verdict.head or "")
    if verdict.action in ("delete", "hold") and any(map(_SHELL_UNSAFE.search, names)):
        hand_off = prefix + "넘긴다"
        return f"{hand_off} {verdict.path} — 셸이 풀 수 있는 글자가 든 이름이라 명령을 찍지 않는다"
    if verdict.action == "hold":
        return f"{label} {verdict.path} — {verdict.reason}. 승인하면 → {command}"
    if verdict.action != "delete":
        return f"{label} {verdict.path} — {verdict.reason}"
    note = f" ({verdict.reason})" if verdict.reason else ""
    return f"{label} {verdict.path}{note} → {command}"


def _reachable(root: Path, git: GitRunner) -> Callable[[], frozenset[str]]:
    """참조에서 닿는 객체를 처음 부를 때 한 번만 읽는다."""
    return functools.cache(lambda: reachable_objects(root, git))


def _judge_all(root: Path, listing: list[Worktree], running: Sequence[str], ops: Ops) -> int:
    merged = ops.merged(root)
    others = [wt for wt in listing[1:] if not wt.bare]
    processes = ops.processes()
    modules = ops.modules()
    verdicts = [
        judge(
            wt,
            gather(root, wt, ops.git),
            merged,
            running,
            ops.pid_alive,
            holders_from(processes, modules, wt.path),
        )
        for wt in others
    ]
    checked_out = {wt.branch for wt in listing if wt.branch is not None}
    for verdict in hold_for_strangers(verdicts, running, checked_out):
        print(_render_worktree(verdict))
    reachable = _reachable(root, ops.git)
    for place in _unregistered(root, listing):
        path = place.as_posix()
        if _is_link(place):
            print(f"넘긴다 {path} — 등록 없는 자리가 링크다. 안을 읽지 않는다")
            continue
        facts = gather_stray(root, place, reachable)
        holders = holders_from(processes, modules, path)
        print(_render_stray(judge_stray(path, facts, holders, _orphan_home(place, listing))))
    refs = _checked(
        ops.git, ["for-each-ref", "refs/heads", "--format=%(refname:short) %(objectname)"], root
    )
    for line in refs.splitlines():
        branch, _, tip = line.partition(" ")
        if branch and branch not in checked_out:
            print(_render_branch(judge_branch(branch, tip, merged)))
    return 0


def _remove(
    root: Path, listing: list[Worktree], target: str, branch: str, head: str, ops: Ops
) -> int:
    """판정 4. 단계의 순서와 종료 코드는 모듈 독스트링."""
    wt = next((w for w in listing[1:] if same_path(w.path, target)), None)
    if wt is None:
        print(f"남겼다 {target} — 등록된 워크트리가 아니다")
        return 1
    if (wt.branch, wt.head) != (branch, head):
        print(f"남겼다 {target} — judge 뒤에 바뀌었다: 지금 {wt.branch} {wt.head}")
        return 1
    merged = ops.merged(root)
    if _still_candidate(root, wt, merged, ops, "지우기 전에", ()) is None:
        return 1
    stop = _probe(Path(wt.path), ops)
    if stop is not None:
        return stop
    # 판정 뒤에 생긴 것(`.env`, 새 파일, 작업 디렉터리 주인, 모듈을 올린 프로세스)을 앞지우기가
    # 지우지 않게, 쥔 프로세스까지 다시 판정해 지울 목록을 읽는다. 리눅스의 탐침은 작업 디렉터리를,
    # 윈도의 탐침은 올린 모듈을 보지 못한다(PR #184 리뷰, 대기열 201)
    holders = holders_now(ops, wt.path)
    again = _still_candidate(root, wt, merged, ops, "앞지우기 직전에", holders)
    if again is None:
        return 1
    verdict, facts = again
    if verdict.unlock and not _unlock(root, wt, ops.git):
        return 1
    if not _pre_delete(Path(wt.path), facts.ignored, ops.delete):
        return 1
    return _git_remove(root, wt.path, branch, ops.git)


def _still_candidate(
    root: Path,
    wt: Worktree,
    merged: Mapping[str, frozenset[str]],
    ops: Ops,
    moment: str,
    holders: Sequence[Holder] | None,
) -> tuple[Verdict, Facts] | None:
    """판정 1~3(세션은 빼고)을 다시 낸다. 지울 것이 아니면 이유를 찍고 None."""
    facts = gather(root, wt, ops.git)
    verdict = judge(wt, facts, merged, (), ops.pid_alive, holders)
    if verdict.action != "delete":
        print(f"남겼다 {wt.path} — {moment} 다시 판정했다: {verdict.reason}")
        return None
    return verdict, facts


def _probe(path: Path, ops: Ops) -> int | None:
    """점유 탐침. 지나면 None, 막히면 1(바꾼 것 없음), 끝내 되돌리지 못하면 3.

    막혔을 때만 쥔 프로세스를 찾아 이유에 붙인다. 지나간 지우기는 앞지우기 직전의 다시 거르기에서
    한 번 훑는다(판정 4의 2). 되돌리기는 `RESTORE_WAITS` 만큼 기다리며 다시 시도한다(대기열 202).
    """
    aside = path.with_name(path.name + PROBE_SUFFIX)
    if os.path.lexists(aside):
        print(f"남겼다 {path.as_posix()} — 탐침 자리 {aside.as_posix()} 가 이미 있다")
        return 1
    try:
        ops.rename(long_path(path), long_path(aside))
    except OSError as error:
        print(
            f"남겼다 {path.as_posix()} — 다른 프로세스가 쥐고 있다(이름 바꾸기가 막혔다: {error}). "
            f"{describe_holders(holders_now(ops, str(path)))}"
        )
        return 1
    failures: list[OSError] = []
    for wait in (0.0, *RESTORE_WAITS):
        if wait:
            ops.sleep(wait)
        try:
            ops.rename(long_path(aside), long_path(path))
        except OSError as error:
            failures.append(error)
            continue
        if failures:
            print(
                f"다시 시도해 되돌렸다 {path.as_posix()} — {len(failures) + 1}번째에 지났다. "
                f"처음 막힌 이유: {failures[0]}"
            )
        return None
    print(
        f"멈췄다 {path.as_posix()} — 폴더가 {aside.as_posix()} 에 남았다. 되돌리기를 "
        f"{len(failures)}번 시도했다: {failures[-1]}"
    )
    return 3


def _unlock(root: Path, wt: Worktree, git: GitRunner) -> bool:
    unlocked = git(["worktree", "unlock", wt.path], root)
    if unlocked.returncode != 0:
        print(f"남겼다 {wt.path} — 잠금을 풀지 못했다: {unlocked.stderr.strip()}")
        return False
    return True


def _pre_delete(path: Path, entries: Sequence[str], delete: Callable[[Path], None]) -> bool:
    """앞지우기. 막히면 그 자리에서 멈추고 False. 등록과 `.git` 은 남는다."""
    for entry in entries:
        try:
            delete(path / entry)
        except OSError as error:
            print(
                f"남겼다 {path.as_posix()} — 다시 만들 수 있는 {entry} 를 지우다 막혔다({error}). "
                "등록과 .git 은 남았다"
            )
            return False
    return True


def _git_remove(root: Path, path: str, branch: str, git: GitRunner) -> int:
    removed = git(["worktree", "remove", path], root)
    if removed.returncode != 0:
        print(
            f"멈췄다 {path} — git worktree remove 가 {removed.returncode} 로 끝났다: "
            f"{removed.stderr.strip()}. 등록과 .git 파일이 지워졌을 수 있다"
        )
        return 3
    deleted = git(["branch", "-D", branch], root)
    if deleted.returncode != 0:
        print(f"지웠다 {path}, 브랜치는 남았다 — git branch -D: {deleted.stderr.strip()}")
        return 1
    print(f"지웠다 {path} 와 브랜치 {branch}")
    return 0


def _remove_branch(root: Path, listing: list[Worktree], branch: str, tip: str, ops: Ops) -> int:
    if any(wt.branch == branch for wt in listing):
        print(f"남겼다 {branch} — 체크아웃돼 있다")
        return 1
    current = ops.git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], root)
    if current.returncode != 0 or current.stdout.strip() != tip:
        print(f"남겼다 {branch} — judge 뒤에 바뀌었다: 지금 {current.stdout.strip() or '없음'}")
        return 1
    verdict = judge_branch(branch, tip, ops.merged(root))
    if verdict.action != "delete":
        print(f"남겼다 {branch} — 다시 판정했다: {verdict.reason}")
        return 1
    deleted = ops.git(["branch", "-D", branch], root)
    if deleted.returncode != 0:
        print(f"남겼다 {branch} — git branch -D: {deleted.stderr.strip()}")
        return 1
    print(f"지웠다 브랜치 {branch}")
    return 0


def _remove_stray(root: Path, listing: list[Worktree], target: str, ops: Ops) -> int:
    """등록 없는 폴더 하나를 지운다. 단계의 순서와 종료 코드는 모듈 독스트링의 "등록 없는 폴더"."""
    # 인자를 그대로 쓰지 않고 목록에서 찾은 폴더를 쓴다. 이후 단계가 같은 자리를 본다
    path = next((stray for stray in _strays(root, listing) if same_path(target, str(stray))), None)
    if path is None:
        print(f"남겼다 {target} — {WORKTREES_DIR}/ 바로 아래의 등록 없는 폴더가 아니다")
        return 1
    reachable = _reachable(root, ops.git)
    if _still_stray(root, path, reachable, "지우기 전에", ()) is None:
        return 1
    stop = _probe(path, ops)
    if stop is not None:
        return stop
    if _still_stray(root, path, reachable, "지우기 직전에", holders_now(ops, str(path))) is None:
        return 1
    try:
        ops.delete(path)
    except OSError as error:
        print(
            f"남겼다 {path.as_posix()} — 지우다 막혔다({error}). 남은 것은 다시 만들 수 있거나 "
            "커밋에 있는 것이다"
        )
        return 1
    print(f"지웠다 {path.as_posix()}")
    return 0


def _still_stray(
    root: Path,
    path: Path,
    reachable: Callable[[], frozenset[str]],
    moment: str,
    holders: Sequence[Holder] | None,
) -> Verdict | None:
    """등록 없는 폴더의 판정을 다시 낸다. 지울 것이 아니면 이유를 찍고 None."""
    facts = gather_stray(root, path, reachable)
    verdict = judge_stray(path.as_posix(), facts, holders)
    if verdict.action != "delete":
        print(f"남겼다 {path.as_posix()} — {moment} 다시 판정했다: {verdict.reason}")
        return None
    return verdict


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tidy_checkouts", description="병합된 워크트리와 로컬 브랜치를 판정하고 하나씩 지운다"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    judged = commands.add_parser("judge", help="워크트리와 로컬 브랜치를 판정해 찍는다")
    judged.add_argument("--running", action="append", default=[], help="실행 중 세션의 제목")
    removed = commands.add_parser("remove", help="워크트리 후보 하나를 지운다")
    removed.add_argument("path")
    removed.add_argument("branch")
    removed.add_argument("head")
    branch = commands.add_parser("remove-branch", help="체크아웃되지 않은 브랜치 하나를 지운다")
    branch.add_argument("branch")
    branch.add_argument("tip")
    stray = commands.add_parser("remove-stray", help="등록 없는 워크트리 폴더 하나를 지운다")
    stray.add_argument("path")
    return parser


def main(
    argv: Sequence[str] | None = None, *, cwd: Path | None = None, ops: Ops | None = None
) -> int:
    args = _parser().parse_args(argv)
    tools = ops if ops is not None else Ops()
    try:
        root, listing = _place(cwd if cwd is not None else Path.cwd(), tools.git)
    except ValueError as error:
        print(f"주 체크아웃 세션에서 돈다: {error}", file=sys.stderr)
        return 2
    except ToolError as error:
        print(error, file=sys.stderr)
        return 3
    command: str = args.command
    try:
        if command == "judge":
            running: list[str] = args.running
            return _judge_all(root, listing, running, tools)
        if command == "remove":
            return _remove(root, listing, args.path, args.branch, args.head, tools)
        if command == "remove-stray":
            return _remove_stray(root, listing, args.path, tools)
        return _remove_branch(root, listing, args.branch, args.tip, tools)
    except ToolError as error:
        print(error, file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
