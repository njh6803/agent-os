# 2026-10-16 (04) open_session.ps1이 새 앱의 노력 하위 메뉴를 고른다

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
