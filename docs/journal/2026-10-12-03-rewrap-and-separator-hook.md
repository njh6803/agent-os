# 2026-10-12 (03) 주석·독스트링 감기 도구와 편집 직후 줄 구분 문자 알림

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 112·160을 한 PR로 닫는다. 둘 다 Write·Edit 직후의 훅
`hook_ruff_line_width` 둘레라 묶었다. 세션은 2026-10-07에 주 체크아웃에서 열렸고, 지시문대로 `tidy-checkouts`를 먼저 돈
뒤 `EnterWorktree(name=rewrap-and-separator-hook)`로 들어가 `origin/main`(`d5ee5e4`, #170)에서
`chore/rewrap-and-separator-hook`을 땄다. 구현 중에 #171(`f71e577`)이 병합되어 커밋 전에 빨리 감았다.

세션은 셀프 리뷰를 반영한 뒤 검증 명령을 다시 돌리는 중에 끊겼고, 2026-10-12에 같은 워크트리에서 이어졌다. 그 사이
#166·#172가 병합되어 main에 `2026-10-11-01` 일지가 생겼다. 이름순으로 고르는 "최신 일지"가 이 일지를 지나치지 않게, 처음
`2026-10-07-20`으로 쓴 이 일지를 닫는 날의 번호로 옮겼다. 처음 고른 `2026-10-12-01`은 형제 워크트리(`admin-style-design`)가
먼저 쓰고 있어, 두 번째 커밋 직전의 `tools/sibling_overlap.py`가 알린 "옮길 번호"대로 03으로 비켜 갔다.

> 사용자: "대기열 112·160을 한 PR로 반영한다(주석·독스트링 감기 도구, 편집 직후 날것 줄 구분 문자 알림)"

> 사용자: "다시 시도" (세션이 끊긴 뒤)

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `4d34bee`에서 `d5ee5e4`로 당겼다. 스킬 파일은 바뀌지 않았다.
- **지운 것.** 없다. `지운다` 줄이 하나도 나오지 않았다.
- **사람에게 넘긴 것.** prunable `05-admin-hides-decision-for-end-user`, PR 머리가 다른 `skill-check-and-retro-section`,
  제목 모를 세션 때문에 넘긴 `tidy-before-worktree`(승인 명령이 붙었다), 분리 HEAD `unruffled-lalande-9017fa`, 등록 없는
  폴더 여섯(대기열 148). 지시문대로 답을 기다리지 않았다.

## 어떻게 했나

- **112: 넘친 꼬리만 다음 줄로 넘긴다.** 지난 도우미들이 혼자 선 `사용:` 줄을 다음 문장에 붙인 것은 문단을 통째로 다시
  채우며 짧은 줄을 끌어올렸기 때문이다. 그래서 넘친 줄의 꼬리 어절을 다음 줄 앞으로 보내고, 다음 줄이 넘치면 거듭하고,
  문단 끝이면 같은 머리로 새 줄을 낸다. 끌어올리지 않으니 그 실수가 구조적으로 생기지 않고, 바뀌는 줄은 넘친 줄부터
  넘침이 흡수되는 줄까지다. 경계는 틀려도 안전한 쪽으로 두었다. 경계가 하나 더 있으면 줄이 조금 들쭉날쭉할 뿐이지만
  놓치면 문장이 합쳐진다. 그래서 빈 줄, 머리가 다른 줄, 닫는 따옴표만 선 줄, 지시 주석, 역슬래시 줄 말고도 이름표 줄
  (`사용:`, `못 보는 것:`)과 목록 표지 줄을 새 문단의 시작으로 본다. 코드 스팬은 백틱 사이의 공백에서 가르지 않는다.
- **도구를 쓰며 바로 써 봤다.** 도구와 시험과 훅의 독스트링이 넘친 줄을 도구로 감았다. 그 과정에서 둘을 배웠다. 하나는
  손으로 괄호 앞(공백 없는 자리)에서 끊어 둔 줄로 꼬리를 넘기면 공백이 하나 생긴다는 것이다(`훅이다 (대기열`). 도구는
  줄바꿈을 공백으로 읽으므로 판정할 수 없는 자리라 "못 보는 것"에 적고, 문단을 한 줄로 써 두고 도구로 감으면 공백에서만
  끊긴다고 적었다. 다른 하나는 처음 쓴 도구 독스트링이 `` `# noqa` `` 코드 스팬을 손으로 갈라 둔 것이다. 손으로 고쳤다.
- **ruff와의 대조가 지시 주석 규칙을 찾았다.** 프로브 `rewrap_width.py`의 첫 판이 견준 33,676줄(덩어리가 둘 이상인 줄이고,
  프로브가 더한 줄 셋을 포함한다) 가운데 13줄에서 ruff와 폭이 갈렸고, 모두 `# noqa: E402` 같은 줄 끝 지시 주석으로 끝나는
  줄이었다. ruff는 그 주석을 빼고 잰다. 어느 주석이
  그런지는 스크래치 탐침으로 ruff 0.16.8에 직접 물어 정했다. `noqa`(대소문자 무관)·`nosec`·`type:`·`pyright:`·`pylint:`·
  `flake8:`·`ruff:`·`isort:`는 빼고 `fmt:`·`mypy:`·`pragma:`는 빼지 않는다. 코드를 들지 않은 `# noqa`는 그 줄의 E501 자체를
  끈다. 이것을 도구에 넣고 프로브의 예외 대조에 그 줄들을 더했다. 다시 돌리자 어긋남 0이었다.
- **160: 검사와 같은 판정을 편집 직후에.** 훅은 단독 실행이라 `check_line_separators`를 import하지 않고 같은 판정(처음
  8000 바이트의 NUL, BOM을 벗긴 UTF-8, 개행으로만 줄, 코드 포인트로 열)을 옮겨 적었다. 두 모듈의 문자 셋이 같은지를 시험이
  본다. 확장자와 자리는 가리지 않는다. 날것 줄 구분 문자는 어느 파일에서든 거의 늘 사고라서다. 러너의 페이로드 표에는 그
  문자를 둘 수 없어(커밋 전 검사가 표를 막는다) 러너가 `chr()`로 지은 파일을 가리키는 자리표시자 `${RAW_SEPARATOR}`를 더했다.
  침묵 사례는 그 문자를 `chr()`로 다루는 검사 자신의 Edit다.

## 바꾼 것

- `tools/rewrap_comments.py`(새 도구)와 `tests/tools/test_rewrap_comments.py`.
- `tools/hook_line_separators.py`(새 훅)와 `tests/tools/test_hook_line_separators.py`, `.claude/settings.json`의 등록,
  `tools/hook_payloads.toml`의 사례 둘, `tools/run_hooks.py`의 자리표시자.
- `tools/hook_ruff_line_width.py`의 안내 문구(감기 명령)와 독스트링(감기 도구가 필요 없다던 문장), 그 시험 하나.
- `.claude/rules/tools.md`의 비용 줄, `KICKOFF.md`의 훅 목록과 도구 항목, `README.md`의 `tools/` 줄(PR을 열기 전에 템플릿의
  하네스 항목이 묻는 README 트리를 보고 더했다. 훅은 `hook_*`로 이미 든다).
- 프로브: `rewrap_width.py`, `rewrap_comments_mutations.toml`, `line_separators_hook_mutations.toml`,
  `line_separators_hook_time.sh`, 그 README의 네 행.
- `.scratch/retro-queue.md`: 112·160 닫힘.

## 잔존 grep

`감기 도구`, `도구가 필요 없다`, `손으로 감는다`, Write·Edit 훅을 둘로 적은 문장을 일지와 대기열 밖에서 찾았다. 남은 것은 새
문장(KICKOFF.md 두 곳, 줄 폭 훅의 독스트링과 시험)뿐이다. `docs/constitution/operations.md` 환경 규약 상세에서 훅의
`.venv`가 비면 ruff를 띄우는 `hook_ruff_line_width` 하나만 침묵한다고 한 줄은, 새 훅이 표준 라이브러리만 써서 그대로 맞다.

## 검사

- 변이: 셀프 리뷰 반영 뒤 `rewrap_comments_mutations.toml` 서른아홉(반영 전 서른), `line_separators_hook_mutations.toml`
  열하나가 모두 기대대로였다. 변이마다 `-k`로 빨개질 테스트 하나를 좁혔고 그 하나만 빨갰다.
- 프로브: `rewrap_width.py`(ruff 0.16.8) 셀프 리뷰 반영 뒤 폭 대조 33,678줄(파일 194개와 더한 줄 5), 예외 대조 22줄,
  어긋남 0. `line_separators_hook_time.sh` 202~234ms(파이썬 파일에서 한 번 326ms).
- 훅 러너: 페이로드 67건, 어긋남 0. 새 훅의 발동과 침묵이 기대대로였다.
- 검증 명령: `uv run pytest -q` 1911 passed(7 deselected), `ruff check`·`ruff format --check`, `pyright` 0 errors,
  `lint-imports`, `pnpm -C web verify`(25파일 338개), 지침 검사, 타입 우회 검사가 초록이었다. 새 파일은 추적 전이라 줄 구분
  문자 검사와 마크다운 표 검사에 이름으로 넘겨 따로 돌렸다. 판정 명령은 파이프 없이 돌리고 로그 파일로 봤다. 위 수는 셀프
  리뷰 전의 것이고, 반영 뒤의 결과는 아래 셀프 리뷰 절에 적는다.
- 워크트리라 `pnpm -C web install --frozen-lockfile --offline`을 먼저 쳤다.

## 셀프 리뷰

`/code-review`(기준 `f71e577`, 수정 9·미추적 9, 커밋 0). 표준 축은 Critical·Major 없이 Minor 4·Nit 여럿, 명세 축은 빠진 요구와
범위 확장 없이 Minor 1·Nit 3이었다.

- **고친 것.**
  - 명세 Minor: 줄 폭 훅은 ruff 설정이 있는 어느 파일에서나 감기 명령을 싣는데 도구는 이 저장소의 100만 썼다. 리뷰어가 줄
    길이 60의 임시 설정으로 손으로 재현했다. 파일마다 ruff처럼 조상에서 가장 가까운 설정(`.ruff.toml`, `ruff.toml`, `tool.ruff`
    표가 든 `pyproject.toml`)을 찾아 `lint.pycodestyle.max-line-length`, `line-length`, 기본값 88 순으로 읽는다. 설정 밖이면
    종료 2다. 같은 수정이 표준 Minor(설정에 `line-length`가 없으면 KeyError로 종료 1이 나 "넘친 줄이 남았다"로 읽힌다, 인자 없는
    종료 2가 독스트링에 없다)도 닫았다.
  - 표준 Minor: 조합형(NFD) 한글의 가운뎃소리·끝소리 자모를 ruff는 폭 0으로 센다. 리뷰어가 스크래치 탐침으로 ruff 27, 도구
    47을 손으로 쟀다. 그 자모를 0으로 세고 프로브에 그 줄 둘을 더했다.
  - 표준 Minor: "못 보는 것"에 적은 셋(주석으로 막은 코드를 감는다, 공백 없이 끊어 둔 자리로 넘기면 공백이 생긴다, 홀로 선
    CR)을 재는 것이 없었다(`.claude/rules/tools.md`). 앞의 둘은 지금의 동작을 시험이 고정하고, 홀로 선 CR은 줄 번호가 갈린 채
    감지 않도록 거부하고(종료 2) 시험이 잰다. 명세 Nit의 혼자 선 짧은 줄도 같은 시험에 넣고 "못 보는 것"에 적었다.
  - 표준 Minor: `rewrap_source`가 문단 조립과 줄 끝 고르기를 한 함수에 섞었다. 문단 하나를 그리는 `_render`와 남은 줄을 세는
    `_remaining`으로 뗐다.
  - 명세 Nit: 겹 백틱 스팬을 갈랐다. 같은 수의 백틱끼리 짝짓는다. 섞인 줄 끝에서 끝 줄의 CRLF가 새 줄로 옮겨 갔다. 원래 줄은
    제 줄 끝을, 새 줄은 원래 끝 줄의 줄 끝을 쓴다.
  - 표준 Nit: `DIRECTIVE`와 `RUFF_PRAGMA`가 지시 주석 목록을 두 번 들었다(`RUFF_PRAGMAS` 하나로), `Row.opening`이 담는 것과
    이름이 갈렸다(`next_head`), `(lines, source)`가 늘 같이 다녔다(문단 함수는 소스만 받는다), `out_lines`·`out_endings` 나란한
    리스트(짝 하나로), 프로브 독스트링과 README가 근거로 드는 시험 수, 일지의 인용 문구와 줄 수의 뜻, 페이로드 표 머리 주석에서
    빠진 `${BROKEN_WEB}`.
  - 변이 표에서 줄 길이 시험이 "`tool.ruff` 없는 `pyproject.toml`도 설정으로 본다"를 가르지 못하는 것을 찾았다. 바깥 설정이
    기본값과 같은 88이었다. 77로 바꿨다.
- **남긴 것.** 자리표시자 하나를 더하는 데 두 파일 다섯 곳을 고쳐야 하는 Shotgun Surgery(판단 항목)는 러너의 기존 구조라 이
  PR의 범위 밖이다. `_rewrap`의 `heads`·`texts` 나란한 리스트(Nit)는 함수 안의 지역 상태라 두었다.
- **다시 돌린 것.** 설정 읽기는 처음에 TOML 표를 손으로 따라갔는데 pyright strict가 `dict`로 좁힌 원소를 Unknown으로 봐
  이 저장소의 다른 도구처럼 pydantic 모델로 읽게 바꿨다(정수가 아닌 값은 `ValidationError`, 곧 `ValueError`). 변이 서른아홉,
  프로브 어긋남 0(위 검사 절), `uv run pytest -q` 1916 passed(7 deselected), `ruff check`·`ruff format --check`, `pyright`
  0 errors, `lint-imports`, `pnpm -C web verify`, 지침 검사, 타입 우회 검사, 새 파일의 줄 구분 문자·마크다운 표 검사, 두 변이
  표의 원문 확인이 초록이었다.
- **세션이 다시 열릴 때.** 워크트리에서 다시 시작한 세션은 워크트리의 `.claude/settings.json`을 읽어 새 훅 등록이 실렸고,
  `${CLAUDE_PROJECT_DIR}`이 가리키는 주 체크아웃에는 그 훅 파일이 없어 `tools/launch_hook.py`가 알리고 지나갔다(Edit 직후
  additionalContext로 받았다). `.claude/rules/tools.md`가 적은 동작 그대로다.

## main 합치기

커밋(`f4792a2`) 뒤 origin/main(`57efd62`, #166·#172)을 합쳤다. 프로브 README와 대기열을 함께 고쳤지만 글자 충돌은 없었다.
main이 새로 세운 규약은 둘이다. ADR은 셀프 리뷰를 반영한 뒤 보이고, 사람에게 묻는 질문에 처음 나오는 기술 개념은 먼저
푼다. 이 PR에는 ADR이 없고 물은 것도 없다. pytest 매개변수 id 이스케이프를 끈 변경은 이 브랜치의 시험(한국어 매개변수 id
없음)에 닿지 않는다. 합친 나무에서 검증 명령을 모두 다시 돌렸다. `uv run pytest -q` 1919 passed(7 deselected)를 비롯해
모두 초록이었다.

## PR 직전 보안·버그·성능 축

`coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 대체 둘을 돌렸다.

- **보안(`/security-review`).** 발견이 없었다. 확신도 3으로 기각한 후보 하나는 줄 폭 훅의 안내 명령이 경로를 큰따옴표로만
  감싸는 것이다. 경로가 모델이 고른 Write·Edit 대상이고, 훅은 알리기만 하며, 실행은 Bash 권한 확인을 거친다.
- **버그·성능(`bug-perf-review`).** 처음에는 60턴 한도에 걸려 보고 없이 멈췄고, 이어 붙여 지금까지 본 것으로 보고를 받았다.
  Critical·Major 없이 유효 6(Minor 4·Nit 2)·보류 1·오탐 3이었다. 리뷰어는 저장소의 추적 파이썬 201파일을 줄 길이 30·60·75로
  감아 AST와 주석 어절열이 같고 다시 감아도 그대로인지를 손으로 쟀고 위반이 0이었다.
  - 고친 것(Minor 넷): `##` 제목과 `#:` 설명처럼 `#` 바로 뒤에 공백이 없는 주석을 감으면 줄이 합쳐지고 새 줄의 `#` 뒤 공백이
    사라졌다(문단에 넣지 않는다). 고쳐 쓰기가 try 밖이라 읽기 전용 파일에서 traceback과 종료 1(넘친 줄이 남았다)로 끝나고
    뒤의 파일을 건너뛰었다(종료 2로 알리고 다음 파일로 간다). SPDX 머리 줄을 ruff는 E501에서 빼는데 도구가 감았다(ruff
    0.16.8에 스크래치 탐침으로 물어 `#` 뒤 공백과 `SPDX-License-Identifier:`·`SPDX-FileCopyrightText:`만 빠지는 것을 보고 그대로
    넣었다. 다른 SPDX 줄은 문단에 넣지 않는다). doctest 출력이 `>>>` 줄에 붙었다(doctest 줄과 코드 펜스 안을 경계로 둔다).
  - 고친 것(보류 하나): 역슬래시 바로 뒤에서 끊으면 비 raw 문자열에서 다음 줄과 이어 읽힐 수 있다. 리뷰어는 재현하지 못했지만
    끊는 자리에서 피하게 하는 비용이 작아 넣었다.
  - "못 보는 것"에 더한 것(Nit 둘): 두 줄에 걸친 코드 스팬, 이 저장소 밖의 드문 문자의 폭(리뷰어가 전체 코드 포인트를
    ruff와 견줘 4,323자가 갈렸다. 미배정 코드 포인트와 일부 기호이고 저장소의 줄에는 없다).
  - 오탐으로 둔 것: 비정상 페이로드에서 새 훅의 예외(기존 훅과 같은 모양이고 PostToolUse의 종료 1은 막지 않는다), 윈도 경로의
    큰따옴표 인용, 쓰이지 않는다는 `ROOT`(시험이 import한다).
  - 반영하며 도구 독스트링을 도구로 감다가, 본문에 쓴 백틱 셋이 닫히지 않은 코드 스팬으로 읽혀 그 뒤가 한 어절이 되는 것을
    봤다. 글로 "백틱 셋"이라 적어 피했다.
  - 변이 표에 일곱을 더해 마흔여섯이 되었다. 첫 판에서 SPDX 줄의 경계 변이가 초록이었다. 시험의 줄 길이 20에서는
    `SPDX-FileContributor:` 첫 어절만으로 폭이 차서 끊을 자리가 없었기 때문이라 그 단언을 줄 길이 30으로 바꿨다. 프로브는 SPDX
    줄 넷을 더해 폭 대조 34,821줄(파일 201개와 더한 줄 5), 예외 대조 26줄에서 어긋남 0이었다.
