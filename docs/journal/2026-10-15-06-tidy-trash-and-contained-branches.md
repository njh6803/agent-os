# 2026-10-15 (02) 워크트리가 쌓이는 원인을 고친다: 휴지통으로 옮기고, origin/main 에 든 것을 지운다

## 계기

사용자가 주 체크아웃 세션에서 워크트리와 로컬 브랜치가 지워지지 않고 쌓인다고 했다.

> 사용자: 워크트리는 계속 쌓이기만 하는것 같은데 스킬이나 워크플로우 등 뭐가 잘못된건지 확인하고 삭제될 수
> 있도록 수정해줘

> 사용자: 그리고 로컬브랜치도 계속 쌓여있는데 원격 브랜치 정리할 때 로컬브랜치도 같이 정리하게 해줘

시작 상태: 등록된 워크트리 79개(주 체크아웃 포함), 로컬 브랜치 132개, 원격 브랜치 4개. 원격은 `--delete-branch`로
지워지고 있었고 로컬만 남았다.

## 원인(옛 판의 `judge`를 그대로 돌려 봤다)

`uv run python tools/tidy_checkouts.py judge`(실행 중 세션 제목 없이)의 결과는 지운다 0, 남긴다 65, 넘긴다 13,
브랜치를 남긴다 61이었다. 갈래마다:

1. **모듈을 올린 프로세스(판정 3)가 병합된 워크트리 55개를 남겼다.** 같은 pid 일곱(python 넷, node, esbuild 둘)이
   모든 워크트리에 붙었다. 몇 분 뒤 `Get-CimInstance Win32_Process`로 보니 일곱 중 둘만 살아 있었고(다섯은 끝났다),
   그 둘은 pre-commit(`-mpre_commit hook-impl`)과 다른 워크트리 `.venv`의 pytest였다. 즉 다른 세션의 테스트가
   도는 동안 판정이 돌면 하드링크된 `.venv`·`node_modules`의 같은 파일을 쥔 것으로 보여 전부 남고, 그 판정은
   경쟁 상태다. uv의 `UV_LINK_MODE=copy`(대기열 217)는 그 뒤에 만든 `.venv`에만 닿고 pnpm은 그대로였다(대기열 258).
2. **`worktree-*` 브랜치 53개가 PR 없이 남았다.** `EnterWorktree`가 워크트리를 만들며 붙이는 브랜치이고 세션은
   곧 자기 브랜치로 옮긴다. 체크아웃되지 않은 브랜치는 병합된 PR 로만 판정해서 영원히 남았다. 끝은 모두
   `origin/main`의 조상이다.
3. **분리 HEAD 워크트리 일곱**(모델 스윕의 스크래치 `mrun2~4`·`m231`, 옛 세션의 `elegant-dijkstra`·`unruffled-lalande`,
   `C:/project/agent-canary-55ba299`)이 늘 "넘긴다"였고 아무도 처리하지 않았다. 넷은 커밋이 `origin/main`에 있다.
4. **prunable 등록 둘**(폴더 없음, `.git` 없이 `web/`만 남은 폴더)과 **옆 이름 `.tidy-probe`에 남은 폴더 하나**가
   "되돌리면 등록이 맞는다"는 안내만 받은 채 사흘을 남았다.
5. **다시 만들 수 없다고 본 무시된 항목** 여섯 자리(`.design-sync/.cache/`, `.design-sync/sb-reference/`, `.ds-sync/`,
   `ds-bundle/`, `.scratch/harness/probes/session_cost/cache/`, `*.stackdump`, `.claude/plans/`)가 워크트리 여섯을
   남겼다.
6. **제목이 어느 브랜치와도 맞지 않는 세션이 돌면 후보 전부를 넘겼다.** 새 세션의 첫 턴은 답을 기다리지 않으니
   그 턴에는 아무것도 지워지지 않았다. 실행 중 세션 다섯의 `claude.exe`가 모두 그 워크트리를 작업 디렉터리로
   쥐고 있었다(`EnterWorktree`로 들어간 세션 포함. 도구의 `scan_processes`로 봤다). 그러니 프로세스를 읽을 수
   있는 OS 에서는 그 규칙이 필요 없다.

## 한 일

`tools/tidy_checkouts.py`와 그 테스트, `tidy-checkouts` 스킬 3단계.

- **휴지통.** `remove`가 다시 만들 수 있는 무시된 항목을 제자리에서 지우던 앞지우기를, 휴지통
  `.claude/worktrees/.tidy-trash/<워크트리>~~<경로>`로 이름 바꾸기 하는 옮기기로 바꿨다. 올린 모듈은 그 폴더의
  이름 바꾸기를 막지 않는다(프로브 `lock_holder.py`의 G, `worktree_occupancy.py`의 E가 이미 쟀다). git이 워크트리를
  지운 뒤 휴지통을 비우고, 막힌 것만 쥔 프로세스와 함께 남긴다. `judge`가 휴지통을 찍고 `empty-trash`가 다시
  지운다. 판정 3은 모듈을 보지 않는다. 모듈 훑기는 등록 없는 폴더와 휴지통의 쥔 프로세스를 대는 데만 쓴다.
- **origin/main 판정.** 체크아웃되지 않은 브랜치는 PR 이 없어도 끝이 `origin/main`에서 닿으면 지운다(`main`·`master`
  제외). 분리 HEAD 워크트리는 커밋이 `origin/main`에 있을 때만 깨끗함·주인 판정을 거쳐 지운다(`remove`의 브랜치
  인자는 `.detached`).
- **자리.** 폴더 없는 등록은 지운다(git 2.32 의 `worktree remove`가 등록만 걷는다. 임시 저장소에서 봤다). 다만 잠긴
  등록과 커밋이 `origin/main`에 없는 분리 HEAD 는 넘긴다(아래 셀프 리뷰의 Critical). `.git` 없는 prunable 폴더는
  등록 없는 폴더의 판정으로 내용을 가른 뒤 휴지통으로 옮기고 등록을 걷는다(폴더가 있는 채로는 git이 걷지
  않는다. `validation failed`, 임시 저장소에서 봤다). 옆 이름 폴더에는 `restore`를 찍고 그 명령이 되돌린다. 원래
  등록은 "남긴다"로 찍어 사람에게 두 번 넘기지 않는다.
- **제목 모를 세션**은 프로세스의 작업 디렉터리를 읽을 수 없는 OS 에서만 후보를 넘긴다.
- `RECREATABLE_PATHS`에 `/design-sync` 산출물 넷과 소급 측정 캐시, `RECREATABLE_SUFFIXES`에 `.stackdump`.
  `.claude/plans/`는 첫 판에 넣었다가 셀프 리뷰로 뺐다(아래).
- `remove-stray`도 폴더째 휴지통으로 옮긴 뒤 지운다. `_move_whole`로 지우다 만 폴더와 공유한다.
- 변이 표 `tidy_checkouts_mutations.toml`: 옮겨 간 원문 서른을 고치고 열하나를 더했다(131).
- 문서: 스킬 3단계의 판정 요약과 명령 목록, 하지 않는 것 표. `operations.md`의 `UV_LINK_MODE` 항목에 판정 3이 모듈을
  보지 않는다는 것(헌법 3.0.36). 프로브 README 행 셋과 `.claude/rules/tools.md`의 gh 문장. 카나리아 명세
  `tidy_skill_stray_and_modules.toml`의 기대 구절(사전 확인 통과 1). 대기열 258 닫힘.

## 잰 것

- **고친 뒤의 `judge`(실행 중 세션 다섯의 제목을 넘겨, 셀프 리뷰 반영 뒤)**: 지운다 61, 브랜치를 지운다 61, 되돌린다 1,
  남긴다 13, 넘긴다 4. 남긴 13은 실행 중 세션의 워크트리 다섯("병합된 PR 이 없다"), `claude.exe`·`tail.exe`·`grep.exe`가
  작업 디렉터리로 쥔 셋, `.claude/plans/`가 든 둘, PR 없는 `web-widget-spec`, 옆 이름 폴더가 남은 등록 하나,
  `main`이다. 넘긴 4는 분리 HEAD 셋(`mrun2~4`, 커밋이 `origin/main`에 없다)과 병합된 PR 머리와 끝이 다른
  `skill-check-and-retro-section`이다.
- **실제 자식 프로세스 테스트(윈도)**: 자식 파이썬이 워크트리 `.venv`의 `.pyd`를 올린 채 `judge`는 지울 후보로 찍고,
  `remove`는 워크트리와 브랜치를 지운 뒤 `.venv`만 그 pid 와 함께 휴지통에 남겼다. `empty-trash`는 자식이 살아 있을 때 1,
  끝난 뒤 0이었다. 옮긴 뒤 매핑 이름은 옛 자리를 가리켜 휴지통 자리로는 pid 를 대지 못했고(첫 판의 실패), 자리
  이름에서 옛 자리를 거꾸로 셈해(`origin_of`) 둘로 견주게 고쳤다.
- **git 2.32**: 폴더 없는 등록에 `worktree remove`는 브랜치·분리 HEAD 모두 종료 0으로 등록을 걷는다. 폴더가 있고 `.git`만
  없으면 `validation failed`(128)로 거부한다. `git check-ref-format --branch`는 `.detached`를 128로 거부하고 `@`는
  허락했다(표준 축 리뷰가 봤다).
- `uv run pytest -q tests/tools/test_tidy_checkouts.py` 152 passed. 전체 `uv run pytest -q` 2721 passed(셀프 리뷰 전).
  `ruff check`·`ruff format --check`·`pyright`·`lint-imports`·지침 검사·타입 우회 검사 모두 0.
- 변이: 아래 "검사".

## 셀프 리뷰

`/code-review`, 기점 `983bf491`(origin/main), 커밋 0, 수정 8개, 미추적 1개(이 일지). 표준 축은 기본 모델(`tools/`가
들어서), 명세 축은 사용자 요청 둘과 옛 판정 목록을 명세로 썼다.

명세 축(Critical 1, Major 2, Minor 3): **Critical** 폴더 없는 분리 HEAD 등록을 `contained`를 보지 않고 걷어, 커밋이
`origin/main`에 없으면 참조를 잃는다(리뷰가 임시 저장소에서 `fsck`의 dangling commit 으로 재현했다. `mrun2~4`가 Temp
청소 뒤 정확히 그 길에 든다). **Major** 카나리아 명세 `tidy_skill_stray_and_modules.toml`이 지운 구절 "모듈(하드링크 이름
포함)"을 기대한다. **Major** `.claude/plans/`는 `.gitignore`가 "저장소의 기록이 아니다"라 적었을 뿐 산출물이 아니고 옛
테스트가 다시 만들 수 없는 것으로 고정했었다. Minor: 잠긴 등록의 폴더가 없으면 지운다로 찍는다, PR 없는 모든
contained 브랜치를 지우는 것은 요구(`worktree-*`)보다 넓다, 옆 이름 등록을 "넘긴다"와 "되돌린다" 두 줄로 찍는다. 수치는
워크트리 79·브랜치 132·`worktree-*` 53·분리 HEAD 일곱·변이 131·148 passed 모두 재현했고, "일곱 중 셋 살아 있음"과
"일곱 중 여섯 끝남"이 충돌한다고 했다.

표준 축(Major 2, Minor 6): **Major** "git 은 브랜치 이름으로 `@` 하나를 허락하지 않는다"가 거짓(`git branch @`가 종료 0).
**Major** 같은 수치 충돌. Minor: `module_holder.py`는 지우기만 재고 이름 바꾸기는 재지 않는데 이름 바꾸기의 근거로
인용했다, "앞지우기" 잔존(독스트링 둘, 변이 이름 다섯, 테스트 이름·독스트링, README "(표는 백스물)", `tools.md`의
"`remove-stray`는 gh를 부르지 않는다" 닫힌 주장), 못 보는 것 두 항목(`origin_of`, `origin/main` 부재)에 테스트가 없다,
`restore`·`empty-trash`의 실패 테스트가 종료 코드만 본다, `hold_for_strangers(processes_seen)`이 불리언 플래그다, 일지의
빈 절. 갈래: `origin_of`가 `__pycache__`를 `//pycache//`로 깨뜨린다, `-\d+$` 떼기가 이름과 충돌할 수 있다, 옮기기가 둘째에서
막힌 뒤 다음 `judge`가 다시 지운다로 내는 것은 맞다. Smell: `if modules is None` 셋(Duplicated Code), `_move_whole -> Path |
int`, `_judge_all`의 Divergent Change.

고친 것:
- 분리 HEAD 는 폴더가 없어도 `gather`가 `contains`를 먼저 보고, `origin/main`에 없으면 넘긴다. 잠긴 등록은 폴더가 없어도
  넘긴다. 테스트 둘(단위·통합. 통합은 `cat-file -t`로 커밋이 남았는지 본다).
- `DETACHED`를 `.detached`로(점으로 시작하는 이름은 git 이 거부한다. `check-ref-format`으로 봤다).
- 수치: 일곱 중 다섯이 끝났다(살아 있던 둘은 pre-commit 과 pytest). 독스트링·대기열 258·이 일지를 맞췄다.
- 카나리아 명세의 기대 구절을 "작업 디렉터리로 쥔 프로세스가 없는지"로. 그 회차는 돌리지 않고 `--preflight`로
  갈음했다(주 체크아웃에서 딴 브랜치라 실험군 워크트리가 없고, 바뀐 것은 기대 구절뿐이다. 그 사유를 명세의 머리에
  적었다).
- `.claude/plans/`를 다시 만들 수 없는 것으로 되돌렸다. 그 때문에 워크트리 둘(`confident-wright-2d3ebf`,
  `elegant-dijkstra-aaddb9`)이 남는다. 사람이 계획 파일을 보고 지운다.
- 옆 이름이 남은 등록은 "남긴다(되돌린다 줄의 restore 가 되돌린다)"로 한 줄만 사람에게 가게 했다.
- 휴지통 자리 이름을 `<이름>~~<flatten(경로)>~<번호>`로 바꾸고 `flatten`/`unflatten`(`%`→`%25`, `/`→`%2F`)으로
  `__pycache__`가 되돌아오게 했다. 테스트가 네 경로와 번호 붙은 자리를 되돌린다. 남은 어긋남(`~~`가 든 이름, `~숫자`로
  끝나는 경로)은 못 보는 것에 적었다.
- `origin/main`이 없는 저장소에서 분리 HEAD 와 PR 없는 브랜치가 모두 남는 것을 테스트로 고정하고 못 보는 것에 적었다.
- 이름 바꾸기의 근거를 `lock_holder.py` G·`worktree_occupancy.py` E로, 지우기가 막히는 근거를 `module_holder.py` G·E로
  갈라 적었다(두 곳).
- "앞지우기" 잔존을 살아 있는 문서에서 걷었다(독스트링 둘, 변이 이름, 테스트 이름·독스트링, README 세 행과 "(표는
  백서른하나)", `tools.md`의 gh 문장을 "`gh_merged_heads`를 부르지 않는 하위 명령"으로). 독스트링 판정 4의 4의 "2026-10-15
  까지는 제자리에서 지웠는데(앞지우기)"는 옛 용어를 설명하는 자리라 두었다.
- `restore`·`empty-trash`의 실패 단언에 까닭 문구를 더했다.
- `_judge_all`의 모듈 훑기를 `functools.cache(ops.modules)`로 한 번만 하게 했다.

남긴 것과 이유:
- `hold_for_strangers(processes_seen)`: 모드 스위치가 맞지만 부르는 곳이 하나이고 함수가 열 줄이다. 가르면 두 함수가
  같은 세 줄을 나눈다. 두었다.
- PR 없는 contained 브랜치 전부를 지우는 것: `worktree-*`만 지우면 옛 세션의 `claude/*`와 `docs/admin-style-spec`처럼
  이름만 남은 브랜치가 그대로 쌓인다. 잃는 것이 이름뿐이라 그대로 두고 못 보는 것에 적었다.
- `_move_whole -> Path | int`, `_judge_all`의 Divergent Change: 결과형을 하나 더 짓는 값보다 읽는 값이 작다고 봤다. 도구
  전체의 모양이라 이 PR 에서 가르지 않는다.
- `-\d+$` 떼기 충돌: `~<번호>`로 바꿔 `-1`로 끝나는 폴더 이름과는 충돌하지 않게 했고, `~숫자`로 끝나는 경로는 못 보는
  것에 적었다.

다시 돌린 명령: 커밋의 pre-commit으로 갈음한다(결과는 아래 "검사").

## 검사

(커밋 뒤에 적는다)

## 다음

- 이 PR 을 병합한 뒤 주 체크아웃에서 `tidy-checkouts`를 돌려 후보를 실제로 지운다(이 세션이 병합 전에 도구로 먼저 돌린
  결과는 "검사"에 적는다).
- `mrun2~4`(모델 스윕의 스크래치 워크트리, 커밋이 `origin/main`에 없다)와 `skill-check-and-retro-section`(병합된 PR 머리와
  끝이 다르다), `.claude/plans/`가 든 워크트리 둘은 사람이 본다.
