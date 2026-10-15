# 2026-10-16 (11) open_session.ps1이 새 앱의 노력 하위 메뉴를 고른다

## 계기

2026-10-15 23:18(KST)에 `tools/open_session.ps1 -Action send`가 `page=` 뒤 `Read-DraftDefaults`에서 "5초 안에 지시문
입력창의 노력 버튼 을(를) 찾지 못했다"로 멈췄다. 사람이 그 화면에서 `Opus 5.5 / xhigh`를 손으로 골라 보냈다.

> 사용자: (지시문의 시작 프롬프트) "tools/open_session.ps1이 지금 앱의 새 세션 입력창에서 노력 버튼을 다시 찾도록 아래
> 지시문대로 고친다"

지시문은 앱 업데이트가 원인이라는 것을 사용자의 어림으로 두고, 표지 화면만 여는 프로브로 다시 재고, `Get-EffortLabels`와
주석의 "앱 2.19675.0.0"도 함께 다시 보고, 고친 send를 사람 앞에서 한 번 열어 보라고 했다. 범위는 PR과 병합까지다.

## 잰 것

- 도는 앱은 2026-10-14에 깔린 2.37337.1.0이다(실행 중인 프로세스의 경로, `Get-AppxPackage`). 2.42304.0.0의 설치 폴더가
  2026-10-15 21:37에 생겼지만 돌지 않는다. 앱을 다시 켜면 그 판이 돌 수 있다(어림, 재지 않았다).
- 읽기만 하는 스크래치 덤프로 창을 보니 `노력:` 버튼이 없고 `모델: Opus 5.5 중간`(다른 세션의 입력창) 버튼 하나가
  자식 Text로 모델과 노력을 보였다. 그 버튼의 메뉴에 MenuItem `노력 엑스트라`가 있었다.
- 노력 하위 메뉴는 펼치기 패턴으로 열리지 않았다(상태 `Collapsed`, 새 요소 0). 포커스 뒤 → 키로 열렸다. 키는
  `SendKeys`가 아니라 `PostMessage`로 Claude 창 핸들에 넣어도 열렸고, 메모장이 정말 앞에 있으면 열리지 않았다(스크래치
  `post_key.ps1`로 먼저 보고, 저장소 프로브 `composer_menu_tree.ps1 -Effort -Behind`로 다시 쟀다).
- 칸마다 고르기, 버튼 글, 메뉴 닫힘, 고속 모드의 `빠름`, Ultracode의 글은 프로브 README의 composer_ 네 행이 원천이다.
- 딥링크 `code/new` 처리기는 2.37337.1.0에서도 모델을 읽지 않는다(`asar_grep.mjs`, `source`만 더 읽는다).
- 고속 모드가 새 세션 화면의 기본값에서 켜졌다 꺼졌다 했다. 프로브는 체크박스를 건드리지 않으며 누가 바꿨는지는 가르지
  못했다.

## 한 일

- `tools/open_session.ps1`: 모델 버튼의 자식 Text로 모델과 노력을 읽는다(`Split-ComposerTexts`, 첫 글이 모델이고 마지막
  글이 노력이다). 노력은 모델 메뉴를 펼치고, `노력` 항목에 포커스를 준 뒤 → 키를 PostMessage로 넣어 하위 메뉴를 열고,
  열렸는지를 먼저 기다린 다음 `SelectionItem.Select`로 고른다(`Select-ComposerEffortItem`·`Open-EffortSubmenu`).
  옛 `Test-ButtonShows`·`Get-EffortButtonStep`·`Find-ModelItem`·`Move-EffortSlider`를 지웠다.
- 시험: 버튼 글 가르기, 노력 이름의 칸, 메뉴 항목 이름 대조. 변이 여섯(`open_session_composer_mutations.toml`) 모두 빨강.
- 프로브 넷을 새 모양으로 다시 쓰고 키(`SendKeys`)를 값 설정·패턴·PostMessage로 바꿨다. README 행과 `asar_grep.mjs` 행.
- ADR 0029 이력 2026-10-16 초안과 본문 포인터 넷, open-session 스킬 3단계의 오류 목록, `docs/model-selection.md`의 세 줄.

## 셀프 리뷰

기점 `ae538ca6`, 추적 파일 11개와 미추적 1개(`open_session_composer_mutations.toml`), 커밋 0개.

### 명세 축

빠진 요구와 범위 밖 변경은 없다고 했다(사람 앞 실행과 PR·병합은 아직 차례가 아니라 세지 않았다). Minor 여섯과 판정:

1. `Set-ComposerModel` 주석이 딥링크 처리기가 읽는 인자에서 `source`를 빠뜨렸고, 프로브 README의 `asar_grep.mjs` 행에 2026-10-16 결과가 없다. 고친다.
2. ADR 0029 "기본값을 되돌리는 까닭"의 "고르기 전의 값을 버튼 이름으로 먼저 읽어 두고"가 이제 거짓인데 포인터가 없다. 단다.
3. `composer_menu_tree.ps1 -Effort`가 새 요소를 펼치기 전 스냅숏과만 견줘, 라디오 항목이 펼치기 패턴과 → 키 가운데 어느 쪽에서 생겼는지 가르지 못한다. `노력` MenuItem의 패턴(Invoke 없음)도 README에 없다. 펼치기 패턴 뒤의 새 요소 수를 따로 찍게 고치고 패턴을 적는다. `-Behind` 회차는 펼치기 패턴이 Claude 창이 앞일 때 돌고도 새 요소가 0이어서 두 해석을 가르는 갈래였다.
4. "모델 메뉴를 펼치면 앱이 창을 앞으로 올린다"를 `composer_patterns.ps1`이 고르기까지 끝낸 뒤에만 쟀다. 펼친 직후에도 찍게 고쳐 다시 잰다.
5. `Select-ComposerEffortItem`이 고른 뒤 모델 메뉴를 접지 않는다. 프로브의 "메뉴가 스스로 닫혔다"는 하위 메뉴 항목이 사라진 것만 봤다. 모델 버튼의 상태를 찍게 프로브를 고쳐 다시 재니 노력을 고른 뒤 모두 `Collapsed`였다. 그래서 코드는 고치지 않고 주석과 README를 그 측정으로 고친다(표준 축 3의 셋째).
6. 하위 메뉴가 열렸는지를 따로 보지 않아 "그 모델에 그 칸이 없다"와 "창이 뒤에 있다"가 같은 오류로 나온다. 하위 메뉴가 열렸는지를 먼저 기다리고, 항목은 그 뒤에 따로 찾게 고친다.

사람 앞 실행은 지금 기본값(`Opus 5.5 / 엑스트라`)과 모델·노력이 모두 다른 `Haiku 5.5 / low`로 하라는 의견이었고, 준비한 시험 파일과 같다.

### 표준 축

Minor 넷, Nit 둘, 냄새 넷(모두 Nit), 커밋 전 절차 하나. 판정:

1. ADR 0029 본문 58행("버튼 이름으로 먼저 읽어 두고")과 96행("슬라이더 칸")에 포인터가 없다. 명세 축 2와 같다. 둘 다 단다.
2. 새 변이 파일이 `expect = "red"`만 적어 실패의 표지가 없다(`.claude/rules/probes.md` 첫 항목). 변이마다 빨개져야 할 시험 이름을 표지로 단다.
3. 근거의 종류와 해석의 갈래 넷.
   - "창이 뒤면 하위 메뉴가 안 열린다"의 근거인 `-Behind` 한 회차는 고속 모드가 켜진 화면이라 두 조건이 겹쳤다. 다시 잰 `-Effort` 회차가 고속 모드가 켜진 채 창이 앞에 있었고 열렸다. 그 회차를 갈래로 적는다.
   - "펼치면 앱이 창을 앞으로 올린다"는 고른 뒤에만 쟀다. 명세 축 4와 같다. `composer_patterns.ps1 -Background`가 펼친 직후를 찍게 고쳐 다시 쟀고 `True`였다. "보통은"을 잰 회차 수로 바꾼다.
   - "고르면 메뉴가 닫혔다"는 하위 메뉴만 쟀다. 명세 축 5와 같다. 다시 잰 회차에서 노력을 고른 뒤 모델 버튼이 `Collapsed`였다. 코드는 고치지 않고 주석과 README를 그 측정으로 고친다. 혹시 열린 채 남아도 제출 확인(입력창이 비었는지)이 막고 `restore=필요`를 낸다.
   - PostMessage가 다른 앱으로 가지 않는다는 문장에 출처가 없다. Win32 문서 원문을 받아 대 보고 출처를 적는다.
4. "q·prompt·folder·file 과 SSH 인자만"이 `source`를 빠뜨렸다. 명세 축 1과 같다. 고친다.
5. (Nit) "차례와 이름은 슬라이더 때와 같다"를 "덧붙임을 뗀 이름"으로 좁힌다.
6. (Nit) README 근거 칸이 이제 그 프로브를 들지 않는 함수를 적었다. 고친다.
7. 커밋 전 절차(ADR 승인, 사람 앞 실행)는 남은 단계로 한다.

냄새: 원인 가설을 박은 오류 문구는 명세 축 6과 함께, 하위 메뉴가 열렸는지를 먼저 기다리게 고쳐 없앤다. `"$what 의"`는 파일의 관례대로 `${what}의`로 쓴다. 매직 넘버(`0x014D0001` 등)에는 이름과 비트의 뜻을 단다. 빈 문자열을 스위치로 쓰던 `Find-ComposerShowing`은 이름 붙은 인자로 부르게 바꾼다. 두 `Select-Composer…Item`과 PostMessage 블록의 중복은 그대로 둔다. 프로브는 단독 실행이 규약이고, 두 함수는 메뉴를 여는 길이 달라 묶으면 갈래 인자가 생긴다.

갈래 밟기: Ultracode가 기본값인 화면의 버튼 글은 재지 않은 어림 입력이었다. `composer_patterns.ps1 -Effort Ultracode`로 잰다. 고속 모드에 노력이 없는 모델이면 `빠름`을 노력으로 읽는다는 지적은, Haiku로 바꾸자 `빠름`이 빠진 회차가 있어 아직 그런 모델을 보지 못했다. 그 경우도 칸이 `$null`이라 되돌리지 않을 뿐이고 주석에 적혀 있어 두고 넘긴다.

### 반영

- 고친 것: 주석의 `source`, ADR 본문 포인터 둘(58·96행), 변이 표지, 근거 문장(펼치기 직후 창, 고른 뒤 모델 메뉴, 고속
  모드와 창의 갈래, PostMessage 문서 원문), "덧붙임을 뗀 이름", README 근거 칸과 `asar_grep.mjs` 행, 하위 메뉴가 열렸는지를
  먼저 기다리는 길과 그 오류 문구, `${what}의`, PostMessage 상수의 이름, `Find-ComposerShowing`의 이름 붙은 인자, 스킬
  3단계의 괄호. 프로브 셋을 고쳐 다시 쟀다(`composer_patterns.ps1 -Background`, `composer_menu_tree.ps1 -Effort`,
  `composer_effort_labels.ps1`, Ultracode 회차).
- 남긴 것: 두 `Select-Composer…Item`과 PostMessage 블록의 중복(프로브는 단독 실행이 규약이고, 묶으면 갈래 인자가 생긴다).
  고속 모드에 노력이 없는 모델의 버튼 글(그런 모델을 아직 못 봤다. 보면 칸이 `$null`이라 되돌리지 않을 뿐이다). 고른 뒤
  모델 메뉴를 접는 코드(다시 재니 닫혔다).
- 다시 돌린 명령: `uv run pytest -q tests/tools/test_open_session.py` 90 passed, 변이 여섯 모두 기대대로(표지 포함). 커밋
  `530c4a41`의 pre-commit이 손으로 치는 다섯(pytest, ruff 둘, pyright, lint-imports, web verify)을 모두 통과했다.

## 실제 실행

고친 판으로 `모델: Haiku 5.5 / low` 줄이 든 시험 지시문을 한 번 보냈다(같은 파일로 두 번 돌리지 않았다). 출력은 `idle=660s`,
`model=Haiku 5.5 원래 Opus 5.5`, `effort=low 원래 xhigh`, `sent=00:55:55.602 via invoke`, `restored=Opus 5.5 / xhigh`였다.
그 세션(`open_session.ps1 시험 세션`)의 `get_session`은 `claude-haiku-5-5`·`low`, `cwd`는 루트였다. 뒤에 연 표지 화면의
기본값은 `Opus 5.5 빠름 엑스트라`였다. `idle=660s`라 사람이 지켜봤는지는 모른다.

## 카나리아와 main

`sibling_overlap.py`가 open-session 스킬을 고치고 카나리아 명세를 고치지 않았다고 1로 끝났다. main이 카나리아 도구를
바꿔 있어(PR #244) 커밋한 뒤 origin/main을 합쳤고(충돌 없음), 스킬 3단계의 괄호를 묻는 새 명세
`canary/open_session_effort_errors.toml`을 그 도구로 돌렸다. 통과 4, "없음" 섞임 0(실험군 커밋 `f1fc7126`, 대조군 주
체크아웃 `df705c17`은 옛 "슬라이더" 목록을 옮겼다, claude 2.1.300). 그 뒤 `sibling_overlap.py`는 0으로 끝났다.

## PR 직전

CodeRabbit CLI는 좌석이 없어(`Seat: not assigned`) 대체 둘을 나란히 돌렸다. 커밋하고 origin/main을 합친 뒤다.

- `/security-review`: 발견 없음. PostMessage는 고정된 키를 정해진 핸들에만 넣고, 지시문이 고를 수 있는 값이 없으며, `SendKeys`를 없앤 것은 위험을 줄였다고 했다.
- `bug-perf-review`: 16건(유효 5, 보류 4, 오탐 7), Critical·Major 없음.
  - 유효 Minor `Invoke-PatternTimed`의 8초 제한이 멈춘 호출에서 걸리지 않는다(`finally`의 `Remove-Job -Force`가 그 호출을 기다린다). 고쳤다. 시간을 넘긴 잡은 지우지 않고 `$script:HungCalls`로 세며, 스크립트 끝의 `Invoke-Action`이 멈춘 호출이 남았으면 출력과 오류 문구를 낸 뒤 `[Environment]::Exit`로 끝낸다. 남기기만 하면 pwsh가 그 스레드를 기다려 끝나지 않는 것을 새 프로브 `hung_thread_job.ps1`로 쟀다. 시험(가짜 요소가 3초 멈추고 제한 1초)을 먼저 빨갛게 본 뒤 고쳤다.
  - 유효 Nit 넷 가운데 둘을 고쳤다. PostMessage의 반환값과 0 핸들을 보고 멈춘다. ADR의 "고속 모드는 그 전부터 켜져 있었다"에 근거(00:49 회차)를 달았다.
  - 남긴 유효 Nit 둘: 노력이 없는 모델을 고르면 "글이 적다" 오류가 "버튼을 찾지 못했다"로 가려진다(그런 모델을 못 봤고 보내기 전에 멈춘다). 프로브 넷의 뒷정리(`Timed`의 같은 `Remove-Job`, 중간에 던지면 기본값·표지·메모장이 남는다, `composer_patterns.ps1 -Background`가 창이 뒤에 없던 회차를 종료 코드로 가르지 않는다)는 손으로 돌리는 진단이라 두고 PR 체크리스트에 적는다.
  - 보류에서 고친 것: 열린 하위 메뉴를 기다릴 때 항목을 매번 다시 찾는다(낡은 요소면 열린 메뉴를 놓친다).
  - 보류로 둔 것: `SetFocus`·`FindAll`의 시간 제한(실제 멈춤을 재지 못했다), 펼치기 실패 뒤 접기 결과의 알림, 분할 보기에서 창 전체로 찾는 메뉴 항목(고른 뒤 입력창 묶음의 버튼 글을 대 보므로 틀리게 고르면 보내기 전에 멈춘다).
- 다시 돈 것: `tests/tools/test_open_session.py` 92 passed. 바뀐 길을 세션을 만들지 않는 `-Action defaults`로 실제 앱에서 두 번 밟았다(`Opus 5.5 / high`로 바꾸고 `xhigh`로 되돌렸다, 둘 다 종료 0).

## PR 검사

PR #250의 첫 회차에서 CodeRabbit(`Review completed`)·claude-review·e2e·visual·web은 초록이었고 `python`과 그에 걸린 `verify`가 빨갰다. 리눅스 러너의 pwsh에는 `UIAutomationClient` 어셈블리가 없어, 새 시험 둘(`test_패턴_호출은_제한_시간에_돌아오고_멈춘_호출을_센다`)이 `Cannot find path ... UIAutomationClient.dll`로 실패했다(2 failed, 2850 passed). 시험 본문이 진짜 어셈블리를 먼저 부르고(`-ErrorAction Stop`을 잡는다), 형식이 없으면 같은 이름의 대역 형식(`ExpandCollapsePattern.Pattern`)을 정의하게 고쳤다. 스크립트는 그대로다. 윈도의 pwsh는 그 형식을 처음부터 찾아 대역 길을 밟지 않는다. 그래서 그 길의 두 전제를 따로 쟀다. Add-Type으로 정의한 형식을 스레드 잡 안에서 이름으로 찾았고, 시험 서버는 `-ErrorAction Stop`으로 잡은 `Add-Type -AssemblyName` 오류를 실패로 세지 않았다(종료 0). 리눅스에서 실제로 통하는지는 다음 CI가 판정한다.

## PR 리뷰

첫 회차(헤드 `a232a40`).

- CodeRabbit: 고칠 지적 없음. 보안 구조 평가가 Low 우려 하나를 남겼다. 시간을 넘긴 고르기 호출이 나중에 끝나 기본값을 바꿀 수 있다는 것이다. 그 경우 고른 값이 원래 값과 다르면 보내기 전에 `restore=필요` 줄이 사람의 복구 명령을 남기고, 프로세스는 바로 끝난다. 앱 쪽에 이미 건너간 호출을 멈출 길은 없어 PR 코멘트에 이유를 남기고 두었다.
- claude-review: Minor 셋, Nit 둘, Critical·Major 없음.
  - 고친 것: catch가 낡을 수 있는 `$trigger`로 `Test-Expanded`를 부르던 것(다시 찾는다, 찾다 던져도 원래 오류를 가리지 않는다), lParam 리터럴(반복 횟수·스캔 코드·비트로 조립하고 값이 옛 리터럴과 같은지 봤다), 함수 순서(부르는 함수 셋을 위로).
  - 둔 것: 두 고르기 함수의 골격 중복(셀프 리뷰와 같은 판단), `Invoke-Action`의 종료 경로가 프로브로만 확인된 것(시험 서버 안에서 `[Environment]::Exit`를 부르면 서버가 끝난다).
- 바꾼 길은 `-Action defaults`로 다시 밟았다(`high`로 바꾸고 `xhigh`로 되돌림, 둘 다 종료 0).

## ADR 승인

ADR 0029 이력 2026-10-16 초안을 셀프 리뷰와 PR 직전 리뷰를 반영한 뒤 보여 주고 물었다.

> 사용자: ADR 0029 이력 2026-10-16 초안을 승인한다. CI가 초록이면 병합까지 진행해 줘.

이력 끝에 승인 줄을 더했다.

## 회고

후보 넷, 승인 둘(대기열 281·282), 기각 둘, 넘김 없음.

1. **승인(대기열 281).** 새 pwsh 시험이 윈도 전용 어셈블리를 불러 이 PC에서는 초록이고 CI의 리눅스 pwsh에서만 빨갰다. 사건: PR #250의 `python` 잡(2 failed)과 CI 한 바퀴. 층: 그 경로의 rules(`.claude/rules/tests.md`)에 행동이 일어나는 자리의 문장. 시험 본문의 모양이 갈래마다 달라 검사로 잡기 어렵다. 되돌림: 문장 하나. rules를 고치면 카나리아를 다시 돌려야 해 이 세션에서는 반영하지 않았다.
2. **승인(대기열 282).** 스레드 잡의 `Remove-Job -Force`가 시간 제한을 무력하게 했다. 사건: 2026-10-12부터 있던 `Invoke-PatternTimed`를 셀프 리뷰가 놓치고 PR 직전 `bug-perf-review`가 잡았다. 층: `.claude/rules/tools.md`의 시간 제한 항목에 그 모양을 더하는 문장(같은 항목이 `capture_output`의 손자 프로세스를 이미 같은 결로 적었다). 되돌림: 문장 하나. 프로브 넷의 `Timed`에 같은 모양이 남아 반영 때 함께 본다.
3. **기각.** 첫 근거 문장들("펼치면 창이 앞으로 온다", "고르면 메뉴가 닫혔다", "창이 뒤면 안 열린다")이 해석을 가르지 않고 일반화했다. `.claude/rules/probes.md` 셋째 항목이 이미 이를 말하고, 셀프 리뷰 두 축이 잡아 다시 쟀다. 설계대로 잡혔다.
4. **기각.** 파이썬 `write_text`가 윈도에서 프로브 README와 변이 표에 CRLF를 썼다. git이 경고했고 커밋 전에 LF로 고쳤다. 저장소에 해가 남지 않았다.

## 다음

- 대기열 281·282는 이 세션이 올렸다(rules 두 문장).
- 앱 2.42304.0.0이 이미 내려받혀 있다. 앱을 다시 켜 그 판이 돈 뒤 open-session이 보내기 전에 멈추면, 이 세션처럼 표지 화면 프로브(`composer_defaults.ps1`, `composer_menu_tree.ps1 -Effort`, `composer_effort_labels.ps1`)로 다시 잰다.
- 새 세션 화면의 고속 모드(`빠름`) 기본값이 켜졌다 꺼졌다 했다. 스크립트는 고속 모드를 고르지 않으므로 지시문 세션이 고속 모드로 열릴 수 있다. 누가 바꾸는지는 가르지 못했다.
- 시험 세션(`open_session.ps1 시험 세션`, Haiku 5.5 / low)이 사이드바에 남았다. 보관은 사람이 한다.
- 이 PR은 워크트리에서 병합한다. 주 체크아웃은 다음 새 세션의 `tidy-checkouts`가 당긴다.

## 일지 번호

병합 직전에 main이 일지 `2026-10-16-07`을 들여, 이 일지(처음 받은 번호 04)가 이름순으로 그 앞이 되었다. `sibling_overlap.py`가 "옮길 번호: 일지 2026-10-16-04 → 2026-10-16-11"을 냈고, `--move`로 옮기려 하자 GitHub에 열린 PR #253의 `refs/pull/253/head`가 없어(같은 PR의 `merge` 참조는 있었다) 형제 대조가 종료 2로 멈췄다. 10분을 기다려도 그 참조는 생기지 않았다. 그래서 도구가 낸 번호 11로 손으로 옮겼다. 그 전에 도구가 보는 자리(형제 워크트리 디스크의 일지, 열린 PR #253·#241의 파일 목록)에 `2026-10-16-11`이 없는 것을 직접 봤고, 이 브랜치의 인용 넷(ADR 0029의 승인 줄, 대기열 281·282, 카나리아 명세의 결과 줄)과 머리 줄을 함께 고쳤다.
