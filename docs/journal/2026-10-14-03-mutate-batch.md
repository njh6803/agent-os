# 2026-10-14 (03) mutate.py 의 종료 코드 판정과 표지, 첫 실패에서 멈추기, 실제 러너 시험

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 203·231·253을 한 PR로 닫는다. 대상은
`tools/mutate.py`와 그 시험이다. 앞 세션이 워크트리 `.claude/worktrees/mutate-batch`에 커밋하지 않은 시험 변경(203의
완료분과 253의 시험)과 231의 측정 스크립트를 남겼고, 이 세션은 `EnterWorktree(path)`로 그 워크트리에 들어가 이었다.

> 사용자: "대기열 203·231·253(대상 파일이 `tools/mutate.py`와 그 시험인 열린 행 셋)을 chore 한 PR로 반영한다" (지시문의 시작 프롬프트. 범위는 PR과 병합까지)

## 어떻게 했나

1. **253 구현.** 앞 세션이 쓴 시험 열하나가 빨간 채로 남아 있었다. 지시문의 설계대로 `RunnerSpec`에 `judge = "exit"`,
   `red_exit`(1 이상, exit 판정에만), `baseline_output`을, `Mutation`에 `expect_output`을 두었다. 빈 표지와 짝이 틀린
   `red_exit`는 변이 파일 오류다. 표지는 색 코드를 벗긴 출력에서 매 반복 찾고, 없으면 `표지 없음: …` 줄과 출력의 끝을
   내며 어긋남으로 센다. 기준선의 표지가 없으면 기준선은 초록이 아니다.
2. **환경 문제.** 시험 전체를 처음 돌리자 실제 프로세스 시험 넷이 "8초 안에 끝난다"에서 9.2~9.6초로 빨갰다.
   `taskkill /T` 한 번이 6~8초 걸렸고(스크래치의 `tk.py`로 세 번 쟀다), 원인은 PC에 멈춘 채 쌓인
   `docker stats --all --no-trunc --no-stream` 프로세스 1,580개(딸린 conhost·com.docker.cli까지 프로세스 5,195개)였다.
   `taskkill /T`는 자식을 찾으려고 전체 목록을 훑는다. 사용자에게 물었다.

   > 사용자: (고른 것) "Claude가 끝낸다" — "명령줄이 `docker stats ... --no-stream`인 docker.exe만 골라 Stop-Process로 끝냅니다. 데몬(`docker serve`)과 Docker Desktop은 건드리지 않습니다."

   끝낸 뒤 프로세스가 449개, `taskkill`이 0.16~0.19초가 됐고 시험 143개가 9.75초에 모두 지났다. 시험의 상한은 그대로 뒀다.
3. **231 측정.** 지시문의 측정 스크립트를 인자(임시 워크트리, 결과 디렉터리)를 받게 고쳐 `HEAD`(`e445a3d`)의 분리 임시
   워크트리에서 돌렸다. sibling_overlap 표본 여섯(1 12 23 34 45 56)을 그대로 돌리면 446초(기준선 72초, 변이 몫 약 351초),
   `-x`를 붙이면 163초(기준선 62초, 변이 몫 약 79초)였고 여섯 모두 두 갈래에서 기대대로 빨강이었다
   (`.scratch/harness/probes/mutate_231/231_*.txt`). `-x`는 첫 실패에서 멈출 뿐 종료 코드 1이 그대로라 빨강을 초록이나
   오류로 바꾸지 못한다. 그래서 `-k`(빨개진 시험만 고르기)는 재지 않았다. `-k`는 시험이 바뀌면 고른 시험 밖에서 빨개질
   변이를 놓칠 수 있고, `-x`가 이미 같은 몫을 줄였다. 이 PR에 넣었다. 표마다 `-x`를 적지 않고, 도구가 빨강을 기대한
   pytest 판정 변이에만 스스로 붙인다. 기준선과 초록을 기대한 변이는 모든 시험이 지나야 해 끝까지 돈다.
4. **검사기 프로브 옮기기.** `checker_mutations.mjs`의 변이 열하나 가운데 원문 치환인 아홉을
   `checker_mutations.toml`로 옮겼다. "보여 주기용 태그를 모두 걷는다"는 색인 전체가 아니라 Button의 두 스토리만 걷는다.
   원문이 정확히 한 번이어야 하고, 메시지가 그 컴포넌트의 것임을 더 좁게 단언한다. 파일을 만들거나 지우는 둘은 `.mjs`에
   남았다.
5. **showcase 표지.** 변이를 넣은 실제 출력(스크래치의 `showcase_raw.py`)에서 afterEach의
   `디자인 토큰에 없는 클래스를 그렸다: 규칙 없는 클래스 text-base`와 axe의 `to have no violations`·`/label?application=axeAPI`를
   골라 붙였다.
6. **새 변이 표.** 새 기능의 규칙 하나씩을 뺀 변이 열여섯(`mutate_exit_markers_mutations.toml`)을 더했다.

## 함정

- **`Path.write_text`가 CRLF를 썼다.** 큰 heredoc을 훅이 막아 패치를 파이썬 스크립트로 썼는데, 윈도우에서 `write_text`가
  `\n`을 `\r\n`으로 바꿔 `tools/mutate.py`와 `.mjs` 전체가 CRLF가 됐다. git은 커밋에서 LF로 고쳐 diff에 보이지 않았고,
  `--check`가 `mutate.py`를 바이트로 읽어 원문 스무 개 남짓이 사라졌다고 알려서야 알았다. HEAD 그대로인 임시 워크트리의
  `--check`는 모두 맞아 원인을 갈랐다. `write_bytes`로 LF를 되돌렸다. 이후 스크립트는 `read_bytes`·`write_bytes`를 쓴다.
- **05 워크트리의 생성물이 도중에 바뀌었다.** 처음 이 워크트리에 복사한 `ds-bundle/`에는 카드와 목록 타일이 있었는데, 몇십
  분 뒤 임시 워크트리에 복사한 것에는 없었다(그사이 05 워크트리의 `ds-bundle/`이 다시 지어졌다). 앞서 복사한 사본으로
  돌렸다.
- **멈춘 묶음 실행의 고아.** 표 묶음을 `TaskStop`으로 멈췄는데 셸 스크립트가 남아 다음 표를 이어 돌렸다. 스크립트와 그
  아래 프로세스를 `taskkill /T`로 끝냈다. 그 임시 워크트리는 `git worktree remove --force`가 `Invalid argument`로 폴더를
  지우지 못해(앞 세션과 같은 증상) 새 이름으로 다시 만들었다.

## 셀프 리뷰

기점 `e445a3d`, 커밋 하나(`82fef77`)와 커밋하지 않은 변경, 미추적은 `mutate_231/`과 이 일지다. 두 축 모두 Critical·Major는
없었다.

- 고친 것(두 축이 함께 짚은 것): `-x`가 `judge == "pytest"`를 열쇠로 써, pytest 판정만 빌린 훅 러너(`tools/run_hooks.py`,
  retro_hook·pr_head_sync 표)에도 붙었다. 지금은 그 명령이 인자를 읽지 않아 무해했을 뿐이다. 내장 pytest 러너에만 붙이고,
  시험을 vitest와 pytest 판정을 빌린 명령 두 갈래로 넓혔다.
- 고친 것(표준 축): 초록인 기준선에 표지가 없을 때 출력의 끝이 나오지 않았다(독스트링은 같은 일을 한다고 적었다). 기준선도
  표지를 넘기고 시험에 그 줄을 단언했다. 새 못 보는 것 "뒤의 시험이 표지를 찍었을지"를 실제 pytest 시험으로 고정했고,
  문장을 "뒤의 시험만 찍는 표지는 없어 어긋남으로 센다"로 고쳤다. "초록·오류를 볼 변이"를 "초록을 기대한 변이"로
  고쳤다(`expect`에 오류는 없다). `measure.sh`가 표지 없는 회차가 있어도 0으로 끝나던 것을 1로 끝나게 했다. `.mjs`의 죽은
  길(편집 루프, 카드·타일 복사, 전부 바꾸기)과 거짓이 된 주석을 걷었다.
- 고친 것(명세 축): exit 판정의 못 보는 것(node 의 잡히지 않은 예외도 1)과 `-x`의 못 보는 것(뒤 시험이 걸려 끝까지 돌면
  시간 제한을 넘겼을 변이도 빨강)을 적고 시험으로 고정했다. 231의 근거 문장이 측정(옛 도구에 표로 `-x`를 적어 기준선에도
  붙었다)을 구현의 효과처럼 들었다. 독스트링을 "변이 몫이 약 351초에서 79초"로 고치고, 시험 독스트링의 겹친 수는
  지웠다. `measure.sh` 머리에 잰 판(`e445a3d`)과 지금 도구로는 견줌이 되지 않는다는 것을 적었다. README 띄어쓰기 하나.
- 남긴 것: 시험의 exit 표지 러너 다섯이 `_변이면`과 같은 모양을 손으로 다시 쓴다(Minor, Duplicated Code). 몇은 반복마다
  출력이 다르거나 호출을 기록해 헬퍼에 그대로 들지 않고, 모양을 맞추는 것은 이 PR의 판정과 무관해 두었다.
  `_runners(spec)` 를 세 자리에서 다시 부르는 것(Nit)은 표가 작아 값이 없다.
- 남긴 것(뒤에 한다): README의 `mutate_231/`·`mutate_exit_markers` 행은 변이 표 전체를 돌린 결과와 함께 더한다.
  `durations_sibling_overlap.txt`(앞 세션이 2026-10-13 에 낸 것)는 그 행에서 출처를 적는다.
- 다시 돌린 것: `uv run pytest -q tests/tools/test_mutate.py` 151 통과, ruff·pyright(바뀐 두 파일) 초록, 영향받는 표 여덟의
  `--check` 모두 맞음, 남은 `.mjs` 둘 기대대로. 나머지 게이트는 커밋의 pre-commit으로 갈음한다.

## 검사

- **pre-commit.** `82fef77`과 `83f3bd6` 두 커밋 모두 모든 게이트가 초록이었다(pytest 339초, web-verify 167~172초가 가장 길었다). 첫 시도는
  pyright가 시험의 람다(`lambda *_: KeyboardInterrupt()`)의 인자 타입을 모른다고 막아 이름 있는 함수로 바꿨다.
- **변이 표 전체(`83f3bd6`, 분리 임시 워크트리).** 시험을 고쳤으므로 `mutate.py`를 재는 표를 모두 돌렸다. 모두 기대대로였다.

  | 표 | 변이 | 시간 |
  |---|---|---|
  | `checker_mutations.toml` | 9 | 4초 |
  | `mutate_exit_markers_mutations.toml` | 17 | 464초 |
  | `mutate_restore_mutations.toml` | 7 | 237초 |
  | `mutation_check_mutations.toml` | 8 | 311초 |
  | `retro_hook_mutations.toml` 26·27 | 2 | 12초 |
  | `mutate_timeout_select_mutations.toml` | 28 | 840초 |
  | `mutate_runners_mutations.toml` | 30 | 728초 |

  `showcase_mutations.toml` 둘은 `82fef77`에서 표지를 붙인 표로 돌려 둘 다 표지와 함께 빨강이었다(그 뒤 web은 바뀌지 않았다).
  첫 묶음(`82fef77`)은 `mutate_exit_markers`에서 "표지를 색 코드가 든 출력에서 찾는다"와 "표지를 마지막 반복에서만 본다"가 초록으로
  살아남았다. 색 코드가 표지의 바깥에만 있었고, 표지가 빠진 회차가 마지막이었다. 두 시험의 입력을 고쳤고, 시험을 고쳤으므로
  옛 시험을 재던 그 묶음은 멈추고 셀프 리뷰를 반영한 판으로 다시 돌렸다.
- **main 합치기 뒤.** main이 `tools/run_hooks.py`를 바꿔, 합친 판(`94249b4`)의 분리 임시 워크트리에서 retro_hook 26·27을 다시
  돌렸고 둘 다 기대대로였다. `mutate.py`와 그 시험은 main이 바꾸지 않았다.
- **잔존 grep.** 명세 축이 살아 있는 문서에서 "종료 코드로 말하는 node 검사기가", 판정 나열 "pytest, vitest, playwright, tsc",
  "실패의 까닭(을) 가르지"를 찾아 0건이었다.

## main 합치기

`origin/main`이 `7eebfd7`·`54eb5be`(PR #235·#237)로 나가 있었다. 앱의 `sync_with_base_branch`는 이 워크트리가 앱이 만든 것이 아니라며
거절해 `git merge --no-edit origin/main`으로 합쳤고 충돌은 없었다. main이 바꾼 `.claude/rules/tools.md`는 Grep 훅의 시간 기록뿐이라
이 브랜치의 판단에 닿지 않았다. 하네스 README는 main이 더한 행과 겹치지 않는 자리에 두 행을 더했다.
