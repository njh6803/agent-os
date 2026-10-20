# 2026-10-20 (11) 관리 화면이 실패 원인을 글자로, 바로가기를 링크로 그린다

일지 2026-10-16-60의 "다음"이 낸 지시문(나란히 여는 4 중 4)으로 연 새 세션이다. 제목을 브랜치 이름
`feature/06-admin-shows-cause-and-shortcut-links`로 바꿨다. 묶음의 첫 세션이 아니라 `tidy-checkouts`는 돌지 않았다. 주
체크아웃에서 브랜치를 따지 않고 워크트리 `.claude/worktrees/06-admin-shows-cause-and-shortcut-links`에 들어가 브랜치를
바꾸고 `uv sync`와 `pnpm -C web install --frozen-lockfile`을 쳤다. `implement` 스킬을 Read로 열어 따랐다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자:
> .scratch/end-user-continuation/issues/06-admin-shows-cause-and-shortcut-links.md
> 다음 작업: … 관리 화면의 실행 상세가 실패 원인을 글자로, 바로가기를 그 실행으로 가는 링크로 그린다 … 이번 요청 범위:
> PR과 병합까지"

## 한 것

- **테스트 먼저.** 실행 상세 페이지 테스트(`web/apps/admin/components/pages/RunPage.test.tsx`)에 실패 원인 하나, 바로가기
  다섯(에이전트마다의 링크, 옛 실행의 `null`, 빈 지도의 `{}`, 칸의 `.`·`..`, 지도가 아닌 값 넷)을 더하고, HTML 사례에
  바로가기의 적대적인 에이전트 이름과 실행 식별자를 더했다. 시작 이벤트의 필드만 바꾸는 `withStarted`와 계약 이름으로 값
  칸을 찾는 `fieldValue`를 두고 기존 `.`·`..` 사례도 `withStarted`로 바꿨다. 구현 전에 빨강 넷(링크 사례, `.`·`..` 둘, HTML)이
  났다. 앞의 셋은 바로가기가 링크로 그려지지 않아서, HTML 사례는 지도를 JSON 글자로 그려 에이전트 이름의 따옴표가 `\"`로
  적혀 `toContain(agent)`가 실패해서였다(셀프 리뷰 명세 축이 짚어 고쳤다. 처음에는 넷 모두 링크가 없어서라고 적었다).
- **구현.** `EventItem.tsx`의 `FieldValue`가 비지 않은 바로가기 지도를 `Shortcuts`로 그린다. 칸마다 에이전트 이름은
  글자(`dt`), 실행 식별자는 `RunLink`(`dd`)다. `RunLink`는 앞 실행·덮는 끝과 같은 `runHref`를 지나 `.`·`..`이면 글자다. 지도인지는
  타입 단언 없이 술어 `isRunMap`(값이 모두 문자열인 객체, 배열 아님)으로 좁힌다. 빈 지도와 지도가 아닌 값은 `asText`로
  내려간다. 모듈 머리 주석과 `RUN_FIELDS`·`FieldValue`의 독스트링에 바로가기를 더했다.
- **변이.** `.scratch/end-user-continuation/probes/admin_mutations.toml`(9개)과 그 README 줄. 바꾼 `FieldValue`가 conversation
  표(`continuation_mutations.toml`)의 변이 29("앞 실행이 없어도 링크를 그린다")의 원문을 옮겨, 새 모양으로 고치고 그 README
  결과 절에 한 문단을 더했다.
- **티켓.** 체크박스 아홉을 표시했다. 남은 것은 "검증 명령이 모두 초록"과 "기능을 닫는지는 병합 직전에 판정"이다.

## 결정

- **지도는 중첩 `<dl>`로 그린다.** 중첩 `<ul>`이면 페이지 테스트의 `getAllByRole("listitem")`이 이벤트 항목 수를 잘못
  센다. 이름과 값의 짝이라 `dt`·`dd`가 뜻에도 맞고, 테스트는 `term`과 그 다음 형제의 링크로 짝을 본다.
- **`FieldValue`는 용어집 표의 판정(`isEventField`)을 먼저 한다.** 바로가기의 `name === "shortcuts"` 비교가 `EventField`에서
  타입 검사를 받게 한다(필드가 계약에서 빠지면 컴파일에서 깨진다).
- **잔존.** 01이 바로가기의 그리기를 `06`·`틈`으로 가리킨 문장은 01 티켓 파일의 두 줄(병합 뒤의 틈 문단, 필드 이름 표의
  체크박스)뿐이다. 이 기능이 아직 done이 아니라 01 티켓은 살아 있는 문서다(문서 위치 절). 두 줄 모두 고치지 않았다. 13행은
  "병합 뒤에 틈이 있다"는 01 병합 시점의 문단 안에 있고 괄호 "(06이 바로가기를 링크로 그린다)"가 지금도 참이다. 74행은 01이 한
  일을 적은 체크박스이고 "(바로가기의 링크는 06)"도 참이다. conversation 01의 틈 문단도 02가 닫은 뒤 그대로 남았다(티켓
  체크박스의 괄호에 적었다. 처음에는 "01 병합 때의 기록이라"고 적었고 셀프 리뷰 두 축이 짚어 고쳤다).

## 고친 것

- 프로브 README의 "이 기계에서 약 4분"은 재지 않은 수라 지우고 vitest를 기준선 9번, 변이 9번 돈다는 문구로 바꿨다(그때의
  기준선은 8번이었다. 셀프 리뷰 두 축이 짚었고, 변이 둘을 더한 지금은 9번이다).
- conversation 프로브 README의 새 문단이 처음에 "`--check`가 잡았다"고 적었는데, 실제로는 먼저 고친 뒤 `--check`로 원문을
  확인했다. 그 순서대로 고쳤다.

## 검사(셀프 리뷰 전)

- 실행 상세 페이지 테스트 35개 통과. `pnpm -C web run lint`·`typecheck` 초록, `format`은 테스트 파일의 Prettier 한 건을 고친
  뒤 초록.
- `uv run ruff check .`·`ruff format --check .` 0.
- `admin_mutations.toml` 변이 9 모두 기대대로 빨갰고 표지가 섰다(각 1 failed, `.`·`..` 변이는 2 failed). conversation 표의 변이
  29는 1 failed로 기대대로였다. `--check`가 conversation 표의 나머지 다섯을 0번이라 알렸고, core·http 쪽에서 앞서 썩은
  원문이라 그대로 두었다.
- `uv run python tools/run_checks.py`를 백그라운드로 띄웠다가 인계로 멈췄다. 멈추기 전에 check-instructions, zizmor,
  lint-imports, check-type-escapes, pyright가 통과였고 나머지(pytest, web-verify 등)의 결과는 없다.

## 인계

셀프 리뷰 직전(`/code-review`를 부른 직후)에 세션 컨텍스트가 260,063 토큰으로 인계 문턱 20만을 넘어 계기가 왔다. 인계하지
않는 때 다섯에 들지 않아(곁 세션이 아니다, `parentSessionId` 없음) 결정표의 인계 줄로 넘긴다. 이 세션의 지금 제목은
`feature/06-admin-shows-cause-and-shortcut-links`이다. 셀프 리뷰는 새 세션이 한다.

다음 작업: .scratch/end-user-continuation/issues/06-admin-shows-cause-and-shortcut-links.md. 관리 화면의 실행 상세가 실패 원인을 글자로, 바로가기를 그 실행으로 가는 링크로 그린다
다음 단계: 구현
어디서: 새 세션. 인계로 같은 브랜치를 잇는다. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/06-admin-shows-cause-and-shortcut-links.md
브랜치: feature/06-admin-shows-cause-and-shortcut-links
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 나란히 도는 티켓 02·03·05(.scratch/end-user-continuation/issues/)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 이 세션이 띄운 run_checks는 인계로 멈춰 pytest·web-verify 결과가 없으니 리뷰를 반영한 뒤 다시 돌린다. admin_mutations.toml의 전체 실행은 리뷰를 반영해 커밋한 뒤 한 번 돌고 그때 잰 시간을 프로브 README 줄에 적는다. 일지: docs/journal/2026-10-20-11-admin-shows-cause-and-shortcut-links.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-20T02:05:33Z

## 셀프 리뷰 (인계받은 세션)

인계받은 새 세션이 제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어갔다. 앞 세션의 `run_checks`가
인계로 멈추며 `web/eslint.config.test.ts`의 `afterAll`이 돌지 못해 남은 임시 fixture `web/judge-O2Bymh/`(생성 클라이언트로
가는 junction 하나)를 보고, junction만 `[System.IO.Directory]::Delete(경로, $false)`로 뗀 뒤 지웠다. 대상
`web/packages/api-client`는 남았다.

`/code-review`(기준 `911babc0`, 바뀐 파일 6, 미추적 2, 커밋 0). 표준 축은 sonnet·high, 명세 축은 본 세션 모델이다.

**표준 축.**
- Major: 06 티켓 괄호에 적은, 바로가기의 그리기를 06에 미룬 살아 있는 문장이 없었다는 판단과 일지의 "01 병합 때의
  기록이라"가 틀렸다. 문서 위치 절은 done이 아닌 기능의 티켓을 살아 있는 문서로 정한다. 01 티켓 13행 "관리 화면은 원인과 바로가기를
  글자로 보인다(06이 바로가기를 링크로 그린다)"와 74행 "(바로가기의 링크는 06)"이 걸린다.
- Minor: 프로브 README의 "기준선 9번"은 8번이다(`_baseline_runs`는 러너와 `tests` 짝마다 한 번이고 변이 1·2가 짝을
  나눈다). "지도가 아닌 값 셋"은 넷이고 `null`을 든 객체를 겨누는 변이가 없다. README의 "2026-10-20 모두 기대대로"는 리뷰
  전 실행이다. 테스트의 기대 `typeof shortcuts === "string" ? shortcuts : JSON.stringify(shortcuts, null, 2)`는 `asText`의
  복제다(`CODING_STANDARDS.md` 리뷰 관점 4).
- Nit: 표지 `'Found multiple elements with the role "link"'`는 값이 든 문구가 아니고 `"/runs/r-calc"`는 접두로도 맞는다.
  테스트의 `nextElementSibling instanceof HTMLElement` 갈래가 `fieldValue`와 비슷한 모양이다.
- 통과: 스토리 26의 글자, 계약의 `map | null`, 링크 자리가 `RunLink` 둘뿐, `.`·`..` 가드가 `runHref` 하나, conversation
  표 `--check`의 문제 다섯(core 넷, http 하나)과 29번, admin 표 원문 9, 페이지 테스트 35, 인코딩 주소, 일지의 `<ul>`·타입
  검사 주장.

**명세 축.** 빠진 것·범위 넘침·틀린 구현 없음.
- Minor: 기준선 8번(표준과 같다). "지도가 아닌 값 셋"은 넷이고 넷째에 변이가 없다. 에이전트 이름 HTML 사례가 구현 전에
  빨갰던 까닭은 링크가 없어서가 아니라 `asText`(`JSON.stringify`)가 `"`를 `\"`로 적어 `toContain(agent)`가 실패해서였고,
  변이 9도 같은 단언에서 빨개 `querySelector("iframe")` 단언은 빨강을 본 적이 없다. 01 티켓의 두 줄은 살아 있는 문장이고,
  고치지 않는 결론은 선례(conversation 01의 틈 문단)와 맞을 수 있으나 까닭은 "병합 뒤라는 시점을 적은 문단이라"여야 한다.
- Nit: `Shortcuts` 독스트링의 "운영자가 그 에이전트의 앞 대화로 곧장 간다"는 스토리 42의 글자라 "스토리 26·42"다. 티켓
  `Status:`가 아직 `ready-for-agent`다.

**판정과 고친 것.**
- 01 티켓의 두 줄(표준 Major, 명세 Minor): 살아 있는 문서라는 지적은 맞다(문서 위치 절이 done이 아닌 기능의 티켓을 살아
  있는 문서로 정한다). 줄은 고치지 않고 이유를 고쳤다. 13행은 "병합 뒤에 틈이 있다"는 01 병합 시점의 문단 안에 있고 괄호가
  06을 닫는 쪽으로 이미 든다. conversation 01의 틈 문단도 02(#132)가 닫은 뒤 바뀌지 않았다(그 파일의 마지막 커밋은 #131이다,
  `git log`). 고친 자리는 06 티켓 체크박스의 괄호와 이 일지의 결정 절이다. 형제 티켓 02·03·05가 같은 문단의 9~12행을 다시
  읽을 때 06만 다른 모양으로 고쳐 두면 문단이 갈리고 이웃한 줄의 충돌도 생긴다.
- 기준선 횟수: README를 "기준선은 러너와 `tests` 인자의 짝마다 한 번이라 vitest 를 기준선 9번, 변이 11번 돈다"로 고쳤다
  (변이 1·2와 9·11이 짝을 나눈다). 앞 세션의 고친 것 줄에도 그때 8번이었다고 덧붙였다.
- 지도가 아닌 값 넷과 `null`을 든 객체의 변이: README·표 머리 주석을 넷으로 고치고 변이 10 "바로가기 칸의 null 을 실행
  식별자로 본다"를 더했다. 손으로 넣어 본 실패 출력의 testing-library 목록에 `href="/runs/null"`이 실려 표지를 `/runs/null`로
  골랐다.
- HTML 사례가 빨갰던 까닭과 `iframe` 단언: README·표 머리 주석·이 일지의 한 것 절을 고치고 변이 11 "바로가기의 에이전트 이름을
  글자 옆에 HTML 로도 그린다"를 더했다. 이름이 글자로도 남아 `toContain(agent)`는 지나고 `iframe` 단언만 빨개진다. 손으로 넣어
  본 실패 머리가 `AssertionError: expected <iframe …(1)></iframe> to be null`이라 표지를 `></iframe> to be null`로 골랐다.
  변이 10·11을 도구로 돌려 둘 다 기대대로 빨갰다(각 1 failed).
- 테스트의 `asText` 복제: 지도가 아닌 값 넷의 표에 기대 글자를 셋째 칸으로 적었다. 페이지 테스트 35개 통과.
- 스토리 번호: `Shortcuts` 독스트링을 "스토리 26·42"로 고쳤다.
- README의 결과 칸: "셀프 리뷰 전에 1~9번, 리뷰를 반영하며 더한 10·11번이 기대대로였다. 전체 실행은 PR 직전 리뷰를 반영해
  커밋한 뒤 돈다"로 고쳤다. 전체 실행 뒤 날짜와 걸린 시간을 적는다.

**남긴 것.**
- 표지 `'Found multiple elements with the role "link"'`(변이 5·7)와 `"/runs/r-calc"`(변이 6)는 그대로 둔다(Nit). 그 테스트마다 링크
  질의가 하나뿐이라 고른 단언의 실패에서만 나오고, 변이 6의 테스트에는 `r-calc`로 시작하는 다른 링크가 없다.
- 테스트의 `nextElementSibling instanceof HTMLElement` 갈래(Nit, 판단 사항)는 그대로 둔다. `fieldValue`는 계약 이름의 `code`로
  칸을 찾고 바로가기 행은 에이전트 이름의 `dt`에서 짝을 보아 찾는 기준이 다르다.
- 티켓 `Status:`는 검증 명령과 기능 닫기 판정을 마친 커밋에서 `done`으로 바꾼다.

**다시 돌린 명령.** `uv run ruff check .`·`ruff format --check .` 0. `uv run python tools/run_checks.py`의 여덟(lint-imports,
zizmor, check-instructions, check-type-escapes, pyright, run-hooks, web-verify 497.3초, pytest 524.9초)이 모두 Passed다.
`admin_mutations.toml` `--check` 변이 11 모두 원문이 한 번씩 있다.

**첫 커밋이 막힌 것.** pre-commit의 `check-mutations`(`tools/mutate.py --staged`)가 커밋에 든 conversation 표의 원문
다섯이 0번이라 막았다(커밋에 든 표는 모든 원문을 본다). 앞 세션이 core·http 쪽에서 썩은 것이라 그대로 둔 다섯이다. 표를
고치지 않는 길도 없었다(이 커밋이 바꾼 `EventItem.tsx`를 가리키는 29번이 부모 판에서 맞다가 깨진다). 다섯을 지금 코드의
자리로 옮기고 `--since origin/main`으로 여섯(5·6·8·15·23·29번)을 돌려 모두 기대대로 빨갰다. 그 README 문단도 고쳤다. 같은
커밋의 `check-quotes` 경고 둘(일지의 옛 문구 인용)은 따옴표를 떼고 풀어 썼다. 커밋이 실패해 인계 계기의 `커밋 뒤` 경계에
온 것이 아니었다.

**PR 직전 `bug-perf-review`에 밀 주장(반영으로 새로 쓴 사실 문장).**
- 표 머리 주석: "에이전트 이름의 HTML 사례는 지도를 JSON 글자로 그려 이름의 따옴표가 `\"` 로 적히는 바람에 이름이 글자 그대로
  보이지 않아서 빨갰다. 그 사례의 `iframe` 단언은 HTML 로만 그리는 변이가 앞의 글자 단언에서 멈춰 빨강을 보지 못하므로, 글자
  옆에 HTML 로도 그리는 변이가 따로 겨눈다."
- README 줄: "기준선은 러너와 `tests` 인자의 짝마다 한 번이라 vitest 를 기준선 9번, 변이 11번 돈다", "표지는 고른 단언이 실패할
  때만 나오는 문구이고, 변이마다 손으로 넣거나 첫 실행의 출력에서 그 문구가 그 단언의 실패에서 나온 것을 봤다".
- 06 티켓 괄호: "틈 문단의 줄은 01 병합 시점을 적은 문단 안에 있고 괄호 "(06이 바로가기를 링크로 그린다)"가 지금도 참이다",
  "conversation 01의 틈 문단도 02가 닫은 뒤 그대로 남았다".
- `Shortcuts` 독스트링의 "(end-user-continuation 스토리 26·42)".
