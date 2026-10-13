# 2026-10-13 (21) open_session.ps1 의 남은 회귀 시험(대기열 17)

## 계기

일지 12의 "다음"이 낸 지시문으로 연 새 세션이다. ADR 0030이 길을 정했고, 남은 몫은 그 이음매 안의 하네스 chore다.

> 사용자: (지시문의 시작 프롬프트) "대기열 17의 남은 몫을 한 chore PR로 반영한다. ADR 0030의 이음매(pytest가 AST에서 뗀 함수를 pwsh로 부른다)로 시험을 먼저 쓰고, 대기 루프를 부르는 시험을 들이면 _call에 시간 제한을 단다"

## 앞 세션에서 넘겨받은 기록

지시문의 "이어받을 상태"가 일지 12에 적히지 않은 둘을 넘겼다. PR #211의 claude-review 셋째 회차는 Minor 하나와 Nit
둘이었고 PR 코멘트로 보류했다. 병합은 `fcacc97`이다. 병합 직전에 적으면 CI를 한 번 더 돌려야 해서 앞 세션이 두었다.

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했으며 원격에 없는 커밋이 없어 `3e9e544`에서 `fcacc97`(origin/main)로 당겼다. 당긴 커밋은 이
  스킬 파일을 바꾸지 않았다.
- **판정.** 실행 중인 세션 둘(`feature/02-human-share-lines-and-prep-section`, `feature/03-four-themes-and-colors`)의
  제목을 넘겨 `judge`를 쳤다. `지운다` 줄은 없었다.
- **사람에게 넘긴 것.** 일지 12와 같은 여섯이다. prunable 둘(`05-admin-hides-decision-for-end-user`,
  `spec-pipeline-and-pytest-ids`), 분리 HEAD 둘(`elegant-dijkstra-aaddb9`, `unruffled-lalande-9017fa`), PR 머리가 다른
  `skill-check-and-retro-section`, 점유 탐침이 옆 이름에 남긴 `spec-pipeline-and-pytest-ids.tidy-probe`다. 지시문대로 답을
  기다리지 않았다.
- **남긴 것.** 대부분은 모듈을 올린 `python.exe` 둘(pid 33588, 21716) 때문이었다. 그 밖에 잠금 pid가 살아 있는 여덟,
  병합된 PR이 없는 다섯, 다시 만들 수 없는 무시된 항목이 있는 넷이다. 로컬 브랜치는 모두 병합된 PR이 없어 남았다.

## 시험을 먼저

- **이미 있는 함수.** `Normalize-Slash`·`Test-Needle`·`Convert-StartLine`·`Focus-Session`의 시험은 처음부터 초록이라 빨강은
  변이로 봤다. `-TimeoutSec` 시험은 가짜를 최소로 둔다. `Focus-Session`→`Find-RowByTitle`→`Wait-For`가 진짜로 돌고, 창과
  행 누르기와 UIAutomation 조건(`New-Object`, `$Auto`·`$Types`·`$Scope`)만 가짜다. ADR 0030이 말한 같은 이름 함수의 길을
  시험에 처음 썼다.
- **뗄 함수.** `Find-MainStart`·`Select-QuitLogs`의 시험을 먼저 써서 일곱이 "스크립트에 없다"로 빨간 것을 본 뒤
  `Get-AppQuitMarker`를 나눴다. 껍질은 시험 밖이라 프로브의 같은 이름 함수 갈래와 이 PC의 실제 앱으로 다시 돌렸다.
- **시간 제한.** `_call`에 60초를 달았다. 대기 루프를 끝나지 않게 바꾼 변이가 그 제한에서 실패로 끝나, pytest가 멈추지
  않는 것까지 변이로 봤다.
- **훅 대조.** `test_hook_prompt_directive.py`가 ps1 소스를 글자로 쪼개 훅과 대 보던 시험을, `Convert-StartLine`을 pwsh로
  불러 그 출력을 훅에 넘기는 시험으로 옮겼다.

## 셀프 리뷰

`/code-review`, base `fcacc97`, 바뀐 파일 7·미추적 2·커밋 0. `tests/`와 `tools/`가 바뀌어 표준 축은 기본 모델이었다. 명세는
대기열 17 행(옛 판), ADR 0030 Consequences의 마지막 항목, 지시문이었다. 표준 축은 Minor 둘·Nit 여섯·smell 넷, 명세 축은
Minor 셋·Nit 둘을 냈다. 두 축 모두 옛 `Get-AppQuitMarker`와 판정이 같다고 대 봤다.

- **두 축이 따로 같은 것을 잡았다.** ADR 이력의 시간 수치와 실제 앱으로 다시 돌렸다는 문장이 근거 절
  (`docs/agents/issue-tracker.md` 프로브와 근거)을 어겼다. 스크래치패드에서 손으로 돌리고 잰 것처럼 적었다. 대기열 18 행의
  "회귀 시험을 만들 때 함께 간다"가 낡았고, 18도 판정을 떼면 이음매로 잴 수 있다는 ADR 본문과 이력이 어긋나 읽혔다.
- **고친 것.** 손으로 돌린 둘을 프로브로 커밋했다(`open_session_test_time.py`, `quit_marker_real_app.ps1`). 명세 축이 짚은
  빈 고리 둘에 시험을 더했다. 스킬과 복구 안내가 넘기는 `-<이름>`이 모두 스크립트의 `param` 블록에 있는지 AST로 보는
  시험(focus 시험은 본문이 `$TimeoutSec`을 정의해 그 고리를 재지 않았다)과, 시각을 모르는 앱 프로세스가 있으면 판정하지
  않는 시험이다. 뒤의 것은 정렬이 null을 맨 앞에 두는 데 기대므로 `Find-MainStart` 주석에 그렇게 적었다. 변이 셋을 더해
  스물셋이 됐다. 그 밖에 시각 변환 조각을 셋이 함께 쓰게 했고, 가짜 창 인자 `before`를 `rows_before`로, 훅 대조 시험이 실제
  `implement` 스킬 대신 임시 저장소를 쓰게 했다. 대기열 17 행의 취소선을 칸 전체로 넓히고 18 행에 이 행 없이 닫힌 까닭을
  적었다. `_TIMEOUT_SEC` 주석의 가장 긴 사례, README 행의 주어, 대소문자 변이의 어림 표기를 바로잡았다.
- **남긴 것.** 새 헬퍼 이름이 영문인 것(`.claude/rules/tools.md`는 `tests/tools`의 헬퍼를 한국어로 써 왔다고 한다)은 이
  파일의 헬퍼가 원래 영문(`_find_quit_marker`, `_read_model_line`)이라 그 관례를 따랐다. 떼어 낼 함수 목록이 ps1의 호출
  관계를 이름으로 따라 적는 것(Shotgun Surgery)은 ADR 0030의 이음매가 함수를 이름으로 고르는 데서 오는 값이라 두었다.
  `returncode` 단언의 되풀이는 이 파일의 기존 모양이라 두었다.

## 커밋과 main 합치기

- **일지 번호.** 처음 받은 번호는 17이었다. 커밋 직전의 `sibling_overlap.py`가 1로 끝났다. 그 사이 origin/main에 #212와
  #213이 병합돼 최신 일지가 18이 되어, 이 일지가 이름순으로 앞섰다. 출력의 "옮길 번호"대로 21로 옮기고 이 브랜치가 넣은 옛
  번호(ADR 0030 이력, 대기열 17·18 행)를 고쳤다. 합친 두 PR이 바꾼 `CLAUDE.md`(지도에 `docs/model-selection.md` 행)와
  `operations.md`(카나리아 결과 표기)에는 이 브랜치가 따를 새 규약이 없었다.
- **커밋 `828c9f4`.** pre-commit의 검사가 모두 통과했고 `Skipped`인 검사는 없었다(pytest 452.4초, web-verify 313.0초).
  인용 대조는 경고가 없었다. 그 뒤 `git merge origin/main`으로 충돌 없이 합쳤다(`69bf654`).

## PR 직전 보안·버그·성능 축

`coderabbit auth status`가 `Seat: not assigned`라 CLI 축은 돌지 못했다. 커밋하고 origin/main을 합친 뒤 대체 둘을 나란히
돌렸다.

- **`/security-review`.** 식별 서브태스크의 후보가 0이라 거짓 양성을 거르는 단계는 돌리지 않았다. 새 입력은 신뢰 경계 안의
  것(CIM 프로세스 목록, `LOCALAPPDATA`·`APPDATA`, 프로브의 CLI 플래그)뿐이고, 파일은 `-LiteralPath`로 읽기만 하며, 프로브의
  `git show`는 셸 없이 인자 목록으로 부른다.
- **`bug-perf-review`.** 다섯(유효 넷, 보류 하나). 옛 판과 갈리는 입력은 코드를 읽어 찾지 못했다.
  - **고친 것.**
    - Minor: 시간 프로브가 강제로 끊기면 옛 판 복사본(`test_*.py`)이 남아 다음 pytest가 줍고 커밋될 수 있다. 복사본 이름을
      `open_session_base_copy.py`로 바꿔 전체 pytest가 줍지 않게 하고(명령 줄에 직접 준 파일은 모은다), `.gitignore`에
      넣고, 남은 복사본은 다음 실행이 덮어쓴다.
    - Minor: 껍질이 만든 속성 이름과 `Select-QuitLogs`가 읽는 이름의 고리를 재는 시험이 없어, 한쪽만 바뀌면 판정이 늘 null인
      채 가드가 조용히 꺼진다. 프로세스와 파일 시스템의 cmdlet 다섯을 모두 같은 이름 함수로 가린 껍질 시험을 더했다. 경로는
      `Join-Path`의 구분자가 플랫폼마다 달라 `\`로 맞춰 대 본다. 변이 둘(돌림 파일 시각의 속성 이름, MSIX 로그 폴더)이
      빨개져 스물다섯이 됐다.
    - Nit: ADR 이력의 "위 변이 표"가 가리킬 표가 ADR에 없었다. "위 변이 파일의 11번째"로 고쳤다.
  - **다음으로 넘긴 것.** Minor: 시험 시간이 ADR 0030의 문턱을 넘었을 가능성이 높다. 리뷰어도 69.28초를 쟀다. 이 브랜치는
    판정을 미루고(ADR 0030 이력), 유휴 상태의 측정과 묶을지의 결정을 아래 "다음"에 둔다. 리뷰어가 낸 가장 싼 길은 순수 함수의
    사례를 함수마다 pwsh 한 번에 JSON 배열로 돌려 모듈 범위 픽스처로 캐시하고 사례별 pytest id를 지키는 것이다.
  - **보류.** Nit: `_call`의 시간 제한은 직접 자식만 끝낸다. 지금 시험에는 손자 프로세스가 없다(`Invoke-Row`를 가짜로 가렸다).
    `Start-Job`이나 `Start-Process`를 부르는 길을 시험에 들일 때 프로세스 그룹으로 끊는다.
  - **두었다.** 리뷰어가 덤으로 낸 시간 제한 시험의 1초 줄이기는, 이미 적은 측정값이 3초 판의 것이고 아끼는 몫이 2초라 두었다.
