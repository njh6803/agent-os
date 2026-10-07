# 2026-10-07 (15) tidy-checkouts의 판정과 삭제를 도구로 옮긴다

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 132·134를 한 PR로 닫고, 작업 중에 형제 PR #158이
병합되어 같은 파일의 대기열 135도 함께 닫는다. 세션은 주 체크아웃에서 열렸고, 지시문대로 `tidy-checkouts`를 먼저 돈 뒤
`EnterWorktree(name=tidy-checkouts-tool)`로 들어가 `origin/main`(`88b5150`)에서 `chore/tidy-checkouts-tool`로 이름을
바꿨다. 커밋 전에 `origin/main`(`49d9630`)으로 빨리 감았다. 순번은 처음에 10이었다. PR을 연 뒤 main에 든 #161이 같은 10을 써서, 형제 워크트리가 쓴 11~14 다음인 15로 옮겼다(대기열 행도 141에서, 형제와 다시 겹쳐 148로).

> 사용자: "대기열 132·134를 한 PR로 반영한다(tidy-checkouts의 판정·삭제 도구와 당긴 뒤 새 사본 다시 읽기)"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗해 `162ae54`에서 `88b5150`(#157, #159)으로 당겼다. 당긴 커밋이 스킬 파일을 바꾸지 않아 Skill
  도구가 실은 사본이 그대로 맞았다(대기열 134의 상황이 아니었다).
- **판정.** 손으로 쓴 판정 스크립트로 워크트리 16개를 봤다. 지울 후보 9개, 잠금 pid가 살아 있어 남긴 것 둘
  (`01-tokens-story-seam-and-buttons`, `canary-procedure-and-runner`), 병합되지 않았거나 PR이 없는 것 둘, 사람에게 넘길
  것 셋(prunable `05-admin-hides-decision-for-end-user`, PR 머리가 다른 `skill-check-and-retro-section`, 분리 HEAD
  `unruffled-lalande-9017fa`)이었다.
- **삭제.** 첫 후보 `mutate-restore-guard`에서 `git worktree remove`가 `Invalid argument`로 실패했다. 스킬대로 나머지 8개와
  브랜치 삭제를 멈췄다. 등록과 `.git` 파일은 지워지고 폴더(`.venv`, `web/node_modules` 등 파일 약 2만 개)가 남았다.

`mutate-restore-guard`가 멈춘 자리를 좁혔다(손으로 봤다). git의 삭제는 NTFS 순서로 `site-packages`를 지우다
`.venv/Lib/site-packages/yaml/_yaml.cp312-win_amd64.pyd`에서 멈췄고, 그 파일은 링크 수가 19였다. uv가 캐시에서 하드링크로
채운 파일이다. 지금은 그 경로를 명령줄에 담은 프로세스도 파이썬 프로세스도 없었고, 폴더 이름 바꾸기도 지났다. 그때 어느
체크아웃의 파이썬이 PyYAML을 실었다는 것은 어림이다(형제 세션이 pre-commit을 돌렸을 수 있다). 아래 프로브 E가 같은 모양을
재현한다.

여기서 한 번 실수했다. 남은 폴더를 보려고 Bash에서 `cd`로 그 폴더에 들어갔고, 셸의 작업 디렉터리가 거기 남아 워크트리
가드가 그 뒤의 모든 명령을 거부했다. `EnterWorktree(path=<이 워크트리>)`로 돌아왔다. `.git`이 없는 그 폴더에서 git을 쳤다면
루트에 닿았다. 스킬의 "하지 않는 것"에 한 줄을 더했다.

## 어떻게 했나

- **프로브 먼저(대기열 132의 "탐침은 프로브로 먼저 잰다").** `.scratch/harness/probes/worktree_occupancy.py`가 점유 갈래
  여섯을 임시 저장소에서 잰다. 이름 바꾸기는 작업 디렉터리(B)와 트리 안의 열린 파일(C)을 막았다. 트리 밖 하드링크 이름으로
  같은 DLL을 적재한 것(E)은 이름 바꾸기를 지나는데 git이 `Invalid argument`로 지우다 만 폴더를 남겼다. 오늘의 실패와 같다.
  그래서 이름 바꾸기만으로는 오늘의 실패를 막지 못한다. F는 무시된 폴더를 `shutil.rmtree`로 먼저 지우는 갈래이고, 막히면
  `.git` 파일과 등록이 남았다. 도구는 이 순서(탐침, 앞지우기, git)를 따른다.
- **표준 라이브러리만.** `.venv/.../pydantic_core/*.pyd`도 링크 수 22였다(손으로 봤다). 도구가 pydantic을 실으면 지울
  워크트리의 같은 파일을 도구 자신이 쥔다. 그래서 카나리아 러너와 달리 pydantic 없이 `type Json` 별칭으로 gh 출력을 좁혔고,
  import가 표준 라이브러리뿐인지 AST로 보는 테스트를 뒀다.
- **판정은 한 번, 삭제는 하나씩.** `judge`가 `--running`으로 실행 중 세션의 제목을 받아 모두 판정하고, 지울 것에 칠 명령을
  붙인다. `remove`·`remove-branch`는 후보 하나를 다시 판정하고 브랜치와 HEAD가 인자와 같을 때만 지운다. 종료 1은 등록과
  `.git`이 남은 채로 다음 후보로 가도 된다는 뜻이고, 종료 3만 멈춘다. 지난 세션에서 사용자가 물은 "하나라도 실패하면
  전부 롤백을 하는거야?"(일지 2026-10-07-02)에 대해, 이제 git에 닿기 전의 실패는 망가뜨리지 않아 이어 간다.
- **판정에 더한 것.** 자리 판정(prunable, 폴더 없음, toplevel)이 판정 1 앞에 선다(대기열 135). 제목 모를 세션 때문에
  넘긴 후보에는 `승인하면 →`와 명령을 붙인다. 등록 없는 `.claude/worktrees/` 폴더를 넘긴다. 남의 워크트리에서 친
  `status`가 색인을 잠그지 않게 `GIT_OPTIONAL_LOCKS=0`을 준다. 다시 만들 수 있는 목록에 `.gitignore`가 앵커를 붙인
  `web/packages/ui/dist/`와 `storybook-static/`을 더했다(#156 뒤로 생겼고 스킬 목록에 없었다).
- **TDD.** 테스트를 먼저 쓰고 시그니처만 둔 뼈대로 빨강(51 failed, 표준 라이브러리 가드 하나만 초록)을 본 뒤 구현했다.

## 바꾼 것

- `tools/tidy_checkouts.py`: 새 도구. 판정 1~4의 순서와 근거, 다시 만들 수 있는 목록, 종료 코드, 못 보는 것이 독스트링에 있다.
- `tests/tools/test_tidy_checkouts.py`: 순수 판정, 앞지우기(링크를 따라가지 않는다, 읽기 전용), 임시 저장소의 실제 git
  워크트리로 `judge`·`remove`·`remove-branch` 배관, 하위 프로세스 CLI.
- `.claude/skills/tidy-checkouts/SKILL.md`: 2의 끝에 당긴 뒤 새 사본 다시 읽기(대기열 134), 2의 "다른 브랜치다"에 판정 1의
  명령, 3을 도구 호출로, "하지 않는 것"에 두 줄.
- `.scratch/harness/probes/`: `worktree_occupancy.py`, `tidy_checkouts_mutations.toml`, `canary/tidy_skill_tool.toml`과
  README 표. `worktree_longpath.py`의 근거 자리를 도구 독스트링으로 옮겼다.
- `.scratch/retro-queue.md`: 132·134·135 닫힘. `README.md`: tools 줄에 체크아웃 정리.

## 잔존 grep

옛 3의 손 절차 표현(`gh pr list --state merged --head`, `Get-Process -Id`, `3의 판정 2·4`)을 저장소의 md·py·toml 등에서
찾았다. 남은 것은 스킬 2의 "3의 판정 1"과 "3의 판정 3"(요약으로 살아 있다)과 닫은 대기열 135의 원문뿐이다.
`next-session`의 "(`tidy-checkouts` 3의 판정 3)" 인용은 요약과, 살아 있는 잠금을 남길 때 찍는 잠금 사유(세션 이름)가
받는다. 앞의 것은 셀프 리뷰가 잡아 더했다.

## 검사

- 실제 저장소에서 `judge`를 읽기 전용으로 돌렸다(이 워크트리의 도구를 루트에 부르는 스크래치 스크립트). 손으로 낸 판정과
  지울 후보 8개, 남긴 것, 넘긴 것이 같았고, 손으로는 보지 않던 등록 없는 폴더 6개와 지울 수 있는 로컬 브랜치 5개를 더 찾았다.
- 실제 윈도에서 도구의 `remove`를 임시 저장소의 B·E 점유와 깨끗한 것에 돌렸다(스크래치 스크립트, 손으로 봤다). B는 이름
  바꾸기에서 막혀 종료 1에 아무것도 바뀌지 않았고, E는 앞지우기가 `linked.pyd`에서 막혀 종료 1에 등록과 `.git`이 남았고,
  깨끗한 것은 종료 0에 워크트리와 브랜치가 지워졌다.
- 변이 쉰넷 모두 기대대로(프로브 README의 줄. 마지막 하나는 PR 직전 보안 축 뒤에 더해 골라 돌렸다).
- 카나리아 `tidy_skill_tool.toml` 통과 4(claude 2.1.292).

## 셀프 리뷰

`/code-review`(기준 `49d9630`, 수정 5·미추적 6, 커밋 0). 표준 축 12건(Major 1, Minor 6, Nit 5), 명세 축 7건(Minor 5,
Nit 2)이었다. 두 축이 겹쳐 짚은 것이 넷이다.

- **고친 것.**
  - Major: 앞지우기가 둘째 `gather`의 무시된 항목을 판정 2로 다시 거르지 않고 모두 지웠다. 판정 뒤에 생긴 `.env`가
    지워질 수 있었다. 앞지우기 직전에 다시 판정하고, 어긋나면 1로 멈춘다(테스트와 변이).
  - 탐침을 죽은 잠금 풀기보다 앞으로 옮겼다. 탐침이 막혔을 때 "아무것도 바꾸지 않았다"가 참이 된다(테스트와 변이).
  - 종료 코드 설명의 반례 셋(브랜치 삭제 실패인데 1, 잠금을 푼 뒤 막혔는데 1, gh 실패인데 3)을 독스트링과 스킬
    3.2에서 맞췄고, 브랜치 삭제 실패 길에 테스트를 더했다.
  - 살아 있는 잠금을 남길 때 잠금 사유(세션 이름)를 찍는다. `next-session`이 기대는 자리다.
  - `.git` 파일의 근거를 `worktree_longpath.py`에서 `worktree_occupancy.py`의 B·C·E로 옮겼다. 재지 않은 보편 주장 둘은
    손으로 본 것과 어림으로 밝혔다. 인용 셋을 원문에 맞췄고, 폴더 수를 여섯으로 맞췄고, 변이 표 머리의 "tasklist"를
    "pid"로 고쳤다. 테스트 이름에서 함수명을 뺐고, 스킬 3의 원천을 독스트링과 `RECREATABLE_*` 상수로 나눠 적었다.
- **남긴 것.**
  - 스킬 3의 판정 요약(단일 원천과 겹친다는 Minor). `next-session`이 "3의 판정 3"을 인용하고 스킬 2가 판정 1·3을
    쓴다. 줄인 이유를 그 자리에 적었다.
  - 스킬 2의 판정 1 gh 질의(Nit). 루트의 브랜치는 도구가 판정하지 않는다.
  - `Verdict.path`에 브랜치 이름이 드는 것과 `_render`의 두 갈래(Nit). 동작에 해가 없다.
  - 스킬 "하지 않는 것"의 `cd` 줄(명세 축 Minor, 사건 한 번으로 만든 규칙). 회고 2에서 사용자가 고른 선택지가 그
    줄을 이미 넣었다고 적었다.

## PR 직전 보안 축

CodeRabbit CLI는 좌석이 없어(`Seat: not assigned`) 대기열 136의 대체대로 내장 `/security-review`를 돌렸다. 신뢰도 8 이상의
취약점은 없었다. 기준 아래(신뢰도 5~6)의 관찰 하나를 반영했다. `judge`가 찍는 명령에 브랜치 이름이 따옴표 없이 들어가고,
git은 브랜치 이름에 `$`·`;`·`(`·백틱을 허락하며, 스킬은 그 명령을 Bash에 그대로 치라고 한다. 경로나 브랜치 이름에 셸
메타문자가 있으면 명령 없이 넘긴다(테스트와 변이). 처음에는 허용 목록(ASCII)으로 짰다가, 윈도의 `tmp_path`에 든 한글에
테스트 둘이 걸려 막는 목록으로 바꿨다. 한글은 셸이 푸는 글자가 아니다.

## PR 리뷰 반영

PR #163. CI 여섯이 모두 `9d99e35`에서 초록이었다. CodeRabbit은 OSS 시간당 한도에 걸려 리뷰하지 않았다("Review rate
limited", 41분 뒤). 보안·버그 축은 위 `/security-review`가 대신한다. claude-review가 Minor 셋과 Nit 둘을 냈고 모두 고쳤다.

- `_remove`가 검증·재판정·탐침·잠금 풀기·앞지우기·git을 한 함수에서 했다(추상화 수준). 단계 함수 다섯으로 나누고
  `_remove`에는 순서만 남겼다.
- `Verdict.held`가 `human` 판정 안의 숨은 모드였다(불리언 플래그). `Action`에 `hold`를 더했고, 판정 도우미의 `unlock`
  인자도 뺐다.
- 죽은 잠금을 푼 뒤에 앞지우기 직전 재판정이 멈추면 잠금만 풀린 채 "남겼다"였다. 재판정을 잠금 풀기 앞으로 옮겼다
  (테스트와 변이). 독스트링의 단계 번호와 종료 코드 1의 설명을 단계에 맞췄다.
- `Ops.pid_alive`와 같은 이름이던 모듈 함수를 `process_alive`로 바꿨고, `Facts`를 키워드 인자로 만든다.

변이는 쉰다섯 모두 기대대로다.

2회차(`dd245ff`). CI 일곱이 초록이었고 CodeRabbit은 다시 한도에 걸렸다. claude-review가 Minor 셋과 Nit 하나를 냈다.

- 고친 것: `_render(kind)`의 두 값 `Literal`은 사실상 불리언 플래그 인자다. `_render_worktree`와 `_render_branch`로
  나누고 셸 안전 검사와 `hold` 처리는 `_render`가 함께 갖는다. 변이 쉰다섯이 그대로 기대대로다.
- 보류한 것: 단계 함수가 출력과 종료 신호를 함께 낸다는 CQS 지적. 1회차가 요구한 단계 분리 위에 구조를 다시 바꾸는
  것이고 `CODING_STANDARDS.md`가 Minor는 후속을 허용한다. 대기열 137이 짚은 "회차마다 새 Minor" 모양이라 이 PR에서
  돌지 않는다. 모듈이 판정과 삭제를 함께 갖는다는 지적은 리뷰 스스로 후속 검토로 두었다. `human`과 `hold`가 같은
  라벨이라는 Nit은 리뷰가 그대로 둬도 된다고 했다.

## 회고

후보 셋을 냈고 모두 승인됐다. 하나는 대기열로 가고 둘은 일지에만 남긴다.

> 사용자: (고른 것) "1. 남은 폴더 정리 명령, 2. cd 실수는 일지에만, 3. 이유를 안 보는 테스트는 일지에만"

1. **등록 없는 워크트리 폴더가 '사람에게 넘긴다'인 채 쌓인다(대기열 148).** 새 도구의 `judge`가 처음으로 이 폴더들을
   모두 찾았고 여섯이었다(prunable로 등록이 남은 `05-admin-hides-decision-for-end-user`는 따로 센다). 지우다 실패한 `git worktree remove`가 남긴 것과 출처 모를 것이 섞였다. 처방은 도구에 마저
   지우는 하위 명령을 두는 것인데, 출처 모를 폴더에 커밋하지 않은 내용이 있는지 가리는 법이 먼저다. 1회차.
2. **Bash의 `cd`로 `.git` 없는 폴더에 들어가 셸이 묶였다(일지에만).** 위 "첫 턴의 tidy-checkouts"의 실수다. 워크트리
   가드가 막아 해가 없었고, 스킬의 "하지 않는 것"에 한 줄을 더했다. 1회차라 규칙이나 훅은 만들지 않는다.
3. **종료 코드만 보는 테스트가 다른 이유로 지났다(일지에만).** "탐침 자리가 이미 있으면" 테스트가 윈도의 rename 동작
   때문에 점유 판정으로도 1을 받아 변이가 초록이었다. 변이 검사가 이미 이런 것을 잡는 장치라 새 규칙은 두지 않는다.

## 다음

- 사람에게 넘긴 것. 지우다 만 폴더 `mutate-restore-guard`(이 세션), `05-admin-hides-decision-for-end-user`(prunable),
  등록 없는 폴더 `ci-parallel-jobs`·`design-system-tickets`·`harness-audit`·`hook-registration-fail-open`·
  `mutate-any-runner`. PR 머리가 다른 `skill-check-and-retro-section`, 분리 HEAD `unruffled-lalande-9017fa`.
- 이 PR이 병합되면 다음 `tidy-checkouts`가 새 도구로 남은 후보 8개와 로컬 브랜치 5개를 본다.
