# 2026-10-13 (08) open_session.ps1 회귀 시험의 길(ADR 0030, 대기열 17)

## 계기

일지 03의 "다음"이 낸 지시문으로 연 새 세션이다. 대기열 17은 3회차를 넘긴 하네스 항목인데 ADR이 필요해, 결정표의
하네스 chore 줄에서 따로 뺐다.

> 사용자: (지시문의 시작 프롬프트) "대기열 17의 ADR 초안을 쓴다. `tools/open_session.ps1`의 회귀 시험을 Pester로 들일지 pytest가 pwsh로 부를지 정하고, 셀프 리뷰를 반영한 뒤 초안을 보여 승인을 받는다"

## 앞 세션에서 넘겨받은 기록

지시문의 "이어받을 상태"가 일지 03에 적히지 않은 셋을 넘겼다. 병합 직전에 적으면 CI를 한 번 더 돌려야 해서 앞 세션이
두었다. PR #208의 claude-review 2회차는 지적이 없었고, 3회차의 Minor 하나와 Nit 둘은 PR 코멘트로 보류했다. main을 합친
병합 커밋은 `ccd1f51`이고 병합은 `185fe61`이다.

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했으며 원격에 없는 커밋이 없어 `f168f73`에서 `185fe61`(origin/main)로 당겼다. 당긴 커밋은 이
  스킬 파일을 바꾸지 않았다.
- **판정.** 실행 중인 세션 셋(`chore/webfetch-summary-hook`, `feature/01-main-commit-hook-allows-first-commit`,
  `feature/02-icon-stroke-and-removed-props`)의 제목을 넘겨 `judge`를 쳤다. `지운다` 줄은 없었다.
- **사람에게 넘긴 것.** prunable 둘(`05-admin-hides-decision-for-end-user`, `spec-pipeline-and-pytest-ids`), 분리 HEAD
  둘(`elegant-dijkstra-aaddb9`, `unruffled-lalande-9017fa`), PR 머리가 다른 `skill-check-and-retro-section`, 점유 탐침이
  옆 이름에 남긴 `spec-pipeline-and-pytest-ids.tidy-probe`다. 지시문대로 답을 기다리지 않았다.
- **남긴 것.** 대부분은 모듈을 올린 프로세스(`python.exe` 셋, `node.exe`, `esbuild.exe` 둘) 때문이었다. 그 밖에 잠금 pid가
  살아 있는 셋, 실행 중인 세션의 것 하나, 병합된 PR이 없는 다섯, 다시 만들 수 없는 무시된 항목이 있는 셋이다. 로컬
  브랜치는 모두 병합된 PR이 없어 남았다.

## 측정이 정한 것

이음매는 PR #107에 이미 서 있었고 사례 36개가 돌았다. 그래서 결정은 그 이음매를 둘지 Pester로 옮길지였다. 수는 프로브
`.scratch/harness/probes/pwsh_test_seam.py`가 다시 낸다.

- **Pester의 판은 이미 갈려 있다.** 이 PC의 pwsh가 보는 Pester는 Windows PowerShell 모듈 폴더의 3.4.0뿐이고, CI가 쓴 러너
  이미지(`ubuntu-24.04` 20261004.327.1)의 README를 받아 grep하니 5.9.0이었다(손으로 봤다). 어느 lock 파일도 이것을 고정하지
  못한다. 거부의 첫 까닭이 됐다. "판을 고정할 자리가 없다"만으로는 pwsh에도 똑같이 걸린다는 것을 셀프 리뷰가 짚었다.
- **비용.** 사례 하나가 0.87초이고 그중 pwsh 기동이 0.38~0.39초다. 시험 파일 하나는 유휴 상태에서 29.94초, 같은 날 pytest
  전체는 325초였다(둘 다 손으로 봤다). 첫 측정의 48.92초는 워크트리의 `.venv`를 막 만든 직후의 회차라 쓰지 않았다(왜
  느렸는지는 재지 않았다).
- **묶으면.** `Read-ModelLine`의 정상 사례 36개를 pwsh 하나에서 사례마다 새 runspace로 부르면 1.40~1.60초였다. 실패 사례를
  pytest에 사례별로 돌려주는 규약은 재지 않아 이번 결정에 넣지 않았다.
- **Mock 없이.** 시험 본문이 cmdlet과 같은 이름의 함수를 정의하면 떼어 낸 함수가 그 가짜를 부르고, 가짜가 받은 인자도
  나온다. Pester의 가장 큰 이점이 이 이음매로 된다.

## 바꾼 것

- **ADR 0030**과 색인 행.
- **헌법 3.0.30.** `tech.md` 테스트 행에 pwsh 전제와 Pester를 들이지 않는다는 것, `operations.md` 가드레일의 기계마다
  까는 것에 pwsh.
- **준비 목록.** `README.md` 시작 절, `.pre-commit-config.yaml` 머리.
- **프로브** `pwsh_test_seam.py`와 프로브 README 행.
- **대기열 17**에 부분 반영 표시. 남은 몫(세 함수의 시험, `-TimeoutSec` 인자 시험, `Get-AppQuitMarker`의 선택 떼기)은
  ADR 0030의 이음매 안이라 새 ADR이 필요 없다.

## 셀프 리뷰

`/code-review`, base `185fe61`, 추적 5·미추적 2·커밋 0. 바뀐 것이 문서·하네스뿐이라 표준 축은 sonnet이었고, 명세 축은
대기열 17 행과 지시문을 명세로 삼았다. 표준 축은 Minor 다섯·Nit 넷·smell 둘, 명세 축은 (a) 둘과 (c) 넷을 냈다.

- **두 축이 따로 같은 것을 잡았다.** runspace로 묶는 주장이 정상 사례만 잰 수에 기대 "새 ADR이 필요 없다"고 단정한 것,
  남은 몫에서 `-TimeoutSec` 인자 시험이 빠진 것, CI 날짜가 UTC인 것, `up`을 "글자 하나"로 적은 것이다.
- **고친 것.** 프로브에 대조군 둘을 더했다. 같은 runspace에서 부르면 둘째부터 35개 모두 누수가 보이고, 가짜가 받은
  `-Filter` 값이 나온다. 프로브의 갈래는 출력하며 오류 목록을 돌려주던 것을 줄을 돌려주고 예외로 실패하게 갈랐다(CQS).
  ADR의 닫힌 주장 둘("맨 위의 코드 셋", "깨질 때마다 사람이 찾았다")을 사실대로 고쳤다. Pester를 거부한 까닭은 실제 가름
  둘(pwsh는 어느 길이든 필요하다, Pester의 판은 major로 갈렸다)로 다시 썼고, 커버리지를 대가로 적었다. 결정에 "시험 사례는
  pytest의 사례 하나다"를 넣어 묶을 때의 경계로 삼았다. pwsh 전제는 `operations.md`·`README.md`·pre-commit 머리에도
  적었다(명세 축이 chromium 옆의 빈자리를 짚었다).
- **남긴 것.** 프로브가 시험 모듈의 비공개 이름에 기대는 것(Duplicated Code)은 그 이음매를 그대로 재려는 의도라 두고,
  이름이 바뀌면 멈춘다고 독스트링에 적었다.

## 승인

> 사용자(질문에 답): "승인 (Recommended)". 선택지의 설명: "status를 accepted로 바꾸고 일지를 쓴 뒤 커밋·PR·병합까지 갑니다. 대기열 17의 남은 시험(Normalize-Slash·Test-Needle·Convert-StartLine, -TimeoutSec, Get-AppQuitMarker 선택)은 후속 세션 제안으로 남깁니다."
