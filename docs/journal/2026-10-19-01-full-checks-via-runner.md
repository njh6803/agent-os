# 2026-10-19 (01) 손으로 치는 전체 검사를 러너로 옮긴다

next-session 지시문으로 연 새 세션이다. 나란히 여는 둘 가운데 첫째라 `tidy-checkouts`를 먼저 돌고 워크트리에 들어갔다.

> 사용자: "대기열 334(셀프 리뷰 전 손으로 치는 전체 pytest를 tools/run_checks.py 러너로 옮기는 열린 행)를 chore 한 PR로
> 반영한다. 행의 "어디로" 칸이 원천이고, ADR 0035 이력 초안을 셀프 리뷰 뒤에 보이고 사용자에게 다시 묻는다"

## 정리

주 체크아웃은 깨끗한 main이었고 `528bd257`에서 `9220d4a6`(origin/main)로 당겼다. 당긴 커밋은 `tidy-checkouts` 스킬 파일을
바꾸지 않았다. 판정은 지울 워크트리를 내지 않았고, 휴지통에 남은 열셋을 `empty-trash`가 모두 비웠다. 판정이 낸
`remove-branch` 둘은 치지 않았다. `chore/scratch-probe-rule-hook`은 나란히 연 336 세션이 막 딴 브랜치이고(그 폴더는 등록
없이 `.git`이 있어 판정이 `넘긴다`로 냈다. 그 세션이 워크트리를 만드는 도중으로 보인다), `worktree-next-session-handoff-batch`는
`chore/next-session-handoff-batch` 세션이 도는 중이라 그 세션의 몫으로 두었다. 남은 것은 다음 정리가 다시 본다.

## 고친 것

세 줄 계획: (1) `CLAUDE.md` 테스트 줄과 `implement`의 끝 전체 실행에 러너를 친다는 구절을 넣는다. (2) ADR 0035에 이력을
쌓고 대가 문장에 포인터를 단다. (3) 옛 표현이 남은 PR 템플릿과 러너 독스트링을 맞추고 카나리아 명세를 짓는다. 계약(`sdk/`,
`openapi.json`, 헌법)에 닿지 않는다.

- `CLAUDE.md` 검증 명령의 테스트 줄: 변경을 마치고 전체를 볼 때는 `uv run pytest -q` 대신 `uv run python tools/run_checks.py`를
  치고 ruff 둘은 따로 친다는 문장을 더했다. 게이트 열셋과 손으로 치는 다섯의 셈은 그대로다.
- `.claude/skills/implement/SKILL.md`: 끝 전체 실행 문장 뒤에 같은 구절을 더하고, 머리 주석의 더한 것 목록을 여덟으로 고쳤다.
- `.github/PULL_REQUEST_TEMPLATE.md`: 체크 주석에 러너가 돌린 검사도 실행이라는 것을, 확인 방법을 ruff 줄과 러너 줄로 바꿨다.
- `tools/run_checks.py` 독스트링: 손으로 전체를 볼 때도 이 러너를 친다는 한 문장.
- ADR 0035: 이력 "변경을 마치고 전체를 볼 때는 손으로 치는 pytest 대신 러너를 친다"와 "나누는 자리"의 대가 문장 뒤 포인터.
- 카나리아 `.scratch/harness/probes/canary/implement_full_checks_runner.toml`. 짧은 질문 하나(`claude -p --setting-sources
  project,local --strict-mcp-config --model sonnet`)가 "You've hit your weekly limit · resets Oct 19, 6am (Asia/Seoul)"로 끝나
  실제 회차는 돌지 않고 `--preflight`만 통과했다.
- 대기열 334를 닫았다.

## 검사

- 대기열 행의 "어디로" 칸 그대로 `CLAUDE.md`와 `implement`를 고친 뒤 ruff 둘이 초록이었다(`All checks passed!`, 764 files
  already formatted). 러너(`uv run python tools/run_checks.py`)는 인계 전에 pytest와 web verify가 끝나지 않아 멈췄다. 그때까지
  check-instructions, zizmor, lint-imports, check-type-escapes, pyright, run-hooks가 통과였다. 커밋하지 않았다.

## 인계

셀프 리뷰 직전에 인계 계기가 왔다(세션 컨텍스트 213,405 토큰). 넘기는 경계는 `셀프 리뷰 직전`이다. 이 세션의 제목은
`chore/full-checks-via-runner`였다. 셀프 리뷰는 시작하지 않았다(`/code-review`를 불렀지만 단계를 밟지 않았다).

새 세션이 할 것: `/code-review`(base는 `git merge-base origin/main HEAD`, 원천은 대기열 334 행), 반영, 러너와 ruff 둘 재실행,
ADR 0035 이력 2026-10-17 초안을 사용자에게 보이고 승인받기(지시문이 그렇게 요구한다), 커밋, PR, 병합. 승인 전에는 대기열
334의 닫힘 표지가 앞당겨 적혀 있으니 사용자가 다른 길을 고르면 그 표지도 고친다.

지시문:

```
다음 작업: 기능 harness. 대기열 334(손으로 치는 전체 검사를 러너로)를 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 334(셀프 리뷰 전 손으로 치는 전체 pytest를 tools/run_checks.py 러너로 옮기는 열린 행)를 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이고, ADR 0035 이력 초안을 셀프 리뷰 뒤에 보이고 사용자에게 다시 묻는다
브랜치: chore/full-checks-via-runner
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-01-full-checks-via-runner.md(정리·고친 것·인계 절), docs/adr/0035의 이력 2026-10-17
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 일지는 docs/journal/2026-10-19-01-full-checks-via-runner.md이고 이어 쓴다. 카나리아 implement_full_checks_runner.toml은 계정 주간 한도(2026-10-19 06:00 KST)로 실제 회차를 돌지 못하고 사전 확인만 통과했다. 러너 한 바퀴는 pytest·web verify가 끝나기 전에 멈췄다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-17T14:06:09Z

## 이어서 (2026-10-19)

새 세션이 `EnterWorktree`로 이 워크트리에 들어와 이었다. 그사이 origin/main은 `655b19a8`까지 두 커밋(#290, #292) 앞섰다.

### 카나리아

계정 한도가 풀려 `implement_full_checks_runner.toml`을 두 번 돌렸다. 실험군 6회차 가운데 4회차가 기대 문장을 옮겼고, 대조군
2회차는 모두 바뀌기 전 문장("red가 예상보다 넓으면 린트를 먼저 돌린다.")을 옮겨 갈렸다. 실패한 2회차는 "없음"이었다. 이벤트
열을 견주자 실패 회차에는 생각(thinking) 이벤트 없이 곧바로 답이 나왔고, 입력 토큰 합(캐시 생성 + 캐시 읽기)은 통과 회차와
1토큰 안쪽(21,548~21,551)이었다. 그래서 본문은 실렸고 모델이 읽지 않고 답한 회차로 읽었다(손으로 견준 것이고 프로브는 아니다).

### 셀프 리뷰

base `9220d4a6`, 바뀐 파일 6개, 커밋 0개, 미추적 2개(카나리아, 이 일지).

명세 축: Major 둘(대기열 334를 승인 전에 닫았다, 카나리아가 돌지 않았다), Minor 넷(대조군이 "없음"이 아니라 다른 문장을
답한다는 것이 머리 주석에 없다, ADR의 "pre-commit의 나머지 넷"이 pre-commit이 돌리는 여섯과 맞지 않는다, 인계 절의 러너
재실행이 커밋의 pre-commit과 두 번 돈다, 이력 제목의 날짜). 범위는 PR 템플릿이 규약 4의 몫이고 러너 독스트링은 Nit이다.

표준 축: Major 하나(러너 한 바퀴가 Bash 기본 제한 2분을 넘는데 시간 제한 안내가 없다), Minor 넷(README·PR 템플릿 체크박스·ADR
본문 "11분"의 옛 안내, 러너가 일부만 빨갛거나 `SKIP`일 때의 안내, 334를 앞당겨 닫음, `CLAUDE.md` 카나리아 없음), smell
둘(같은 문장이 다섯 자리에 되풀이된다, "나머지 넷"의 이름), Nit 둘(`implement` 머리 주석 근거에 334가 없다, "8분"의 출처).

고친 것:
- 대기열 334를 "반영, ADR 0035 이력의 사용자 승인을 기다려 열어 둔다"로 되돌렸다. 승인 뒤 닫는다.
- 카나리아 머리 주석에 대조군이 답하는 문장과 최신 결과를 적었다.
- ADR 이력: "러너는 그 다섯 가운데 린트를 뺀 넷(pyright, lint-imports, pytest, web verify)과, pre-commit이 돌리는 여섯 가운데
  넷(지침 검사, 타입 우회 검사, 훅 러너, zizmor)을 한 번에 띄우는 명령이다. 마크다운 표 검사와 줄 구분 문자 검사는 러너 밖의
  pre-commit 훅이다." "자리"에 PR 템플릿의 체크 주석과 러너 독스트링을 더하고 "러너 한 바퀴는 Bash 도구의 기본 제한 2분을
  넘으므로 앞의 둘은 제한을 600000으로 주거나 백그라운드로 돌리라고 함께 적는다."를 더했다.
- `CLAUDE.md` 테스트 줄과 `implement`: "한 바퀴가 3분을 넘으니 Bash의 `timeout`을 600000으로 주거나 백그라운드로 돌린다."
- `implement` 머리 주석의 근거에 334를 더했다.

남긴 것과 이유:
- README의 `uv run pytest -q`와 `pnpm -C web verify`: 처음 설치한 사람이 환경을 확인하는 절이고 변경을 마친 뒤의 전체 실행이
  아니다.
- PR 템플릿의 체크박스: 게이트 다섯의 목록이고 셈은 그대로다. 러너가 돌린 것도 실행이라는 것은 체크 주석이 든다.
- ADR 본문의 "11분 남짓"·"같은 11분": 그 결정 시점의 수라 포인터를 달지 않는다(`.claude/rules/adr.md` 달지 않는 것).
- 러너가 일부만 빨갛거나 `SKIP`일 때: 실패한 검사의 출력을 러너가 찍고, `Skipped`가 갈음되지 않는다는 것은 `CLAUDE.md` 검증
  명령 절의 원천이 이미 든다. 같은 사실을 한 곳에 둔다.
- `CLAUDE.md` 카나리아: 매 세션 실리는 파일이고 바꾼 것은 한 줄의 문장이다. 스킬 카나리아가 같은 구절을 본다.
- 되풀이 smell: 다섯 자리가 각각 그 행동이 일어나는 자리(세션의 검증 명령, 스킬의 끝 실행, PR 본문, 러너를 여는 사람, 결정)다.
- 이력 제목의 날짜: 사용자 승인 때 함께 묻는다.

다시 돌린 명령: 커밋의 pre-commit으로 갈음한다(결과는 커밋 뒤에 적는다).

PR 직전 리뷰에 밀 주장: 위 고친 것의 ADR 두 문장, `CLAUDE.md`·`implement`의 시간 제한 문장, 카나리아 머리 주석의 "1토큰 차이".

### ADR 승인

셀프 리뷰를 반영한 뒤 ADR 0035 이력 초안을 쉬운 말로 풀어 보이고 물었다.

> 사용자: ADR 0035에 위 이력을 더하는 것을 "승인 (Recommended)", 이력 제목의 날짜는 "오늘 날짜로 (Recommended)"

그래서 이력 제목과 본문 포인터, 러너 독스트링의 날짜를 2026-10-19로 바꾸고 대기열 334를 닫았다. 위 인계 절의 "이력
2026-10-17"은 그때의 기록이라 두었다.
