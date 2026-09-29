# 2026-09-29 (04) 지침이 실리는 길과 강제 장치 — 조사 두 건의 적용

web-admin 티켓 01(일지 03) 세션이 이어서 했다. 티켓 PR #99가 도는 동안 사용자가 붙여 넣은 설명 둘을 워크플로 둘로
확인했고(일지 03의 "사용자 질문 둘"), #99를 병합한 뒤 적용을 이 chore 한 PR로 묶었다. 브랜치는
`chore/instruction-loading-and-enforcement`, 주 체크아웃에서 했다.

> 사용자: "확인해보고 적용할만한 것은 적용하자. (필요하면 KICKOFF.md도 갱신)"

사용자 판단이 필요한 넷은 물어서 모두 적용하기로 했다.

> 사용자(질문에 답): "ADR 0004·0021 문구 이력, 관리자 우회 문장 + ADR 0005, .env deny 넓히기, 대기열 53에 편집 직후
> ruff" / 키 회전: "회전했다" / `/context`: "재서 붙여 넣겠다"

## 적용한 것

- **지침이 실리는 계기.** `paths` 규칙과 하위 CLAUDE.md는 Read 도구로 연 파일에만 실린다. 주 세션에서 재현했다.
  `sed -n`으로 `adapters/clock.py`를 읽었을 때는 `adapters.md`가 실리지 않았고, Read로 열자 실렸다. `CLAUDE.md` 지도,
  템플릿, KICKOFF의 로드 시점 문단(항상 실리는 것에 스킬 description·`MEMORY.md`·MCP 서버 지침을 더했다), 부록 A·C,
  티켓 05의 확인 항목을 고쳤다. ADR 0004에 이력을 쌓았다.
- **지침 판정자의 구멍.** `tools/check_instructions.py`를 고쳤다.
  - rules를 하위 폴더까지 본다(`rglob`).
  - `paths`의 흐름 목록과 쉼표 문자열, 키 뒤의 주석, 키와 같은 깊이의 항목을 읽는다(중괄호 안의 쉼표는 가르지
    않는다).
  - `@` 임포트는 앞이 공백이나 줄 머리, 뒤가 공백이나 줄 끝인 토큰을 한글이 든 것만 빼고 모두 센다. 끝의 마침표를
    떼던 때는 실리지 않는 `@docs/constitution/principles.md.`가 허용 목록을 통과했다. 허용된 임포트는 한 줄에
    단독으로 있어야 한다(주석이나 들여쓴 블록 안이면 실리지 않는다).
  - rules와 임포트된 파일 안의 `@`를 잡는다(검사 열).
  - "임포트된 파일은 루트에서 읽힌다"는 틀렸다. `@`의 상대 경로는 담은 파일 기준이고, 루트 기준으로 읽힌 것은
    모델이 읽는 백틱 경로다. 독스트링 셋과 KICKOFF를 고쳤다.
- **`.env`의 세 층.** deny를 `Read(//**/.env)`·`Edit(//**/.env)`로 넓혔다(`./`는 세션 cwd 기준이다). PowerShell에는
  `Get-Content`·`Select-String` 두 규칙을 더했다. 처음에는 모양 여섯을 넣었는데, 리뷰 뒤 Read 규칙만 둔 채 다시 재자
  `Get-Content`가 가짜 `.env`를 읽었다(Read 규칙은 PowerShell을 덮지 않는다). 별칭(`gc`·`cat`·`type`·`sls`)은 정규화되어
  두 규칙으로 막힌다. 패턴이 `*.env*`라 `.env.example` 읽기와 `.env`를 언급하는 코드 검색도 PowerShell에서는 막힌다
  (Read·Grep 도구로는 된다). 결과는 `.scratch/harness/probes/env_deny_probe.md`에 있다. `[IO.File]` 읽기는 여전히
  지나간다. 셋째 층은 키 자체라는 것(사용 한도, 실린 키는 회전)을 `operations.md`·KICKOFF·훅 독스트링에 적었다.
  `uv run --env-file`은 막히지 않는 것을 확인했다.
- **보호 설정의 사실.** KICKOFF 8단계의 "직접 푸시·삭제 금지"는 사실과 달랐다(`required_pull_request_reviews: null`).
  직접 푸시를 막는 설정은 없고, 필수 검사(`verify`, strict)가 검사를 지나지 않은 커밋의 푸시를 막을 뿐이며 관리자는
  그것도 우회한다. 막히는 것은 강제 푸시와 삭제다. 관리자 우회가 에이전트에게도 열려 있다는 것을 `operations.md`에
  적고 ADR 0005에 이력을 남겼다(`enforce_admins`는 켜지 않는다).
- **훅.** `tools.md`에 fail-open을 적었다(예외와 timeout은 막지 않고 지나간다. 없는 스크립트는 2로 끝나 모두 막는다 —
  다시 쟀다). 게이트 훅의 경고가 대안(파일로 리다이렉트)을 함께 준다. 이 세션에서 새 문장으로 실제로 발동했다.
- **컨텍스트.** 플러그인 스킬은 `skillOverrides`로 끌 수 없다(공식 skills 문서 원문 확인). KICKOFF를 `/plugin`·`/mcp`로
  고쳤다. 부록 B에 `/clear`·서브에이전트 항목과, 같은 것을 두 번 넘게 교정했으면 `/clear`한다는 기준(공식
  best-practices)을 더했다. 대기열 53에 편집 직후 ruff 되먹임 후보를 더했다.
- ADR 0021에 `next dev` 파일이 실리는 길의 이력을 쌓았다. 헌법은 3.0.1이다(운영 문구 셋).

## `/context` (사용자 실측, 2026-09-29)

Messages 658.3k(66%), MCP tools 12.6k(지연분 125.3k는 맥락 밖), System tools 20.2k, Skills 9.4k, Memory files 6.5k,
System prompt 3.8k, Custom agents 860. 사용자 수준 정리 후보는 문서 스킬 두 벌(anthropic-skills와 document-skills),
skill-creator 세 벌, 인증되지 않은 Slack 플러그인, Playwright MCP 두 벌이다. 사용자 설정이라 바꾸지 않았다.

## 적용하지 않은 것

- 네 축 틀(시점·대상·판정 방식·비용)을 강제 사다리에 들이지 않았다. 공식 분류가 아니고, 이 저장소의 기준으로 층을
  잘못 고른 사건이 없다.
- `enforce_admins`를 켜지 않았다. CI 장애 때 사람도 막히고, 에이전트가 우회한 사건이 없다.
- 하위 디렉터리에서 띄운 세션은 루트 훅을 읽지 않는다. 이것은 부록 C에만 적었다. 한 번의 관찰로 CLAUDE.md 함정을
  만들지 않았다. 그런 세션에서도 git의 pre-commit 훅은 돈다.
- 샌드박스, 편집 직후 되먹임 훅 자체, `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`은 건드리지 않았다.

## TDD와 변이

판정자의 새 판정은 테스트를 먼저 써서 빨강을 봤다. 구현 전부터 초록이던 가드(백틱 안의 `@`)와, 빨강을 본 테스트가
제 줄을 지키는지(`main` 배관, rules 재귀, 토큰 끝의 경계)는 `tools/mutate.py`로 쟀다
(`.scratch/harness/probes/instruction_check_mutations.toml`). 첫 실행에서 도구가 이빨 없는 테스트 하나를 찾았다.
"백틱 안의 `@`는 임포트가 아니다"의 픽스처에 ASCII 경로가 없어서, 코드 스팬을 벗기지 않는 변이에서도 초록이었다.
픽스처를 `` `@docs/x.md` ``로 바꾸자 넷 모두 기대대로 빨강이었다. 리뷰 뒤 토큰 정규식과 함수 이름이 바뀌어 변이의
`old` 둘이 옛 코드를 가리켰고, 고쳐 다시 돌렸다. 게이트 훅의 대안 문장은 테스트를 먼저 써 빨강을 봤다.

## 셀프 리뷰

`/code-review` 두 축(표준, 그리고 사용자 요청과 승인 넷을 명세로 한 축)을 돌렸다. 고친 것:

- 따옴표 인용이 원문과 달랐다. ADR 0004·0021 이력의 인용과 ADR 0005의 런북 인용을 원문에 맞췄다.
- 사실 주장. ADR 0005의 "막히는 것은 강제 푸시와 삭제다"만으로는 직접 푸시가 열린 이유가 빠졌다(위). `.env` deny의
  PowerShell 층은 다시 재어 가렸다(위). `kickoff/facts.md`의 행을 인용과 범위(PreToolUse 기준, `/context`와
  `/memory`의 몫)에 맞췄다. `prompting.md`의 "티켓마다 새 세션으로 이것을 지킨다"는 이 세션이 반례라 고쳤다.
- 판정자. `@` 토큰을 보수적으로 세고(재지 않은 문장부호도 센다), 허용된 임포트의 한 줄 단독 검사를 더했다.
  `paths:` 키 뒤 주석과 같은 깊이의 목록을 읽는다. `claude_md_imports`는 rules에도 쓰여 `at_imports`로 바꿨다.
- 대기열 53의 셋째 칸(승인 출처)을 덮어썼던 것을 되돌렸다. README의 "열 때"를 "Read 도구로 열 때"로 맞췄다.

남긴 것: `.claude/rules/*.md` 표기는 그대로다. 규칙 파일을 가리키는 말이고 하위 폴더가 없으며, 재귀는 판정자
독스트링이 적는다.

## 회고

후보 셋을 냈고 하나가 승인됐다.

> 사용자: (회고 후보) "Bash 읽기 규칙 누락 훅 (Recommended)"

- **승인 — 대기열 57.** `paths` 규칙은 Read 도구로 열 때만 실리는데, 이 세션의 auto 모드 지시는 파일을
  `cat`·`sed`·`head`로 읽으라고 권했다. 이 세션도 `tools/*.py`를 `cat`으로 읽는 동안 `tools.md`가 빠져 있었다.
  실리지 않은 것은 아무 신호가 없다.
- **올리지 않았다 둘.** 대기열 53(한국어 E501)의 회차 — 첫 검사 8건, 문단 일부만 바꿔 뒷문장이 한 줄로 붙는 연쇄로
  2·1·1건. 대기열 45(근거의 종류)의 2회차 — Read 규칙과 PowerShell 규칙을 한 번에 바꾼 전후 비교로 "Read 규칙은
  PowerShell을 덮지 않는다"를 잰 것처럼 적었고, 리뷰 뒤 규칙 하나씩 다시 쟀다.
- **일지에만 둔다.** 대기열 53의 승인 출처 칸을 덮어썼다(리뷰가 잡았다). 일지에 요약을 따옴표 안에 넣었다(인용
  대조 검사가 잡았다). 리팩터 뒤 변이 파일의 `old` 둘이 옛 코드를 가리켰다. 인용 대조 검사를 인자 없이 돌려
  저장소 전체의 경고 157줄을 통째로 읽었다 — 바뀐 파일의 줄만 골라 읽으면 됐다.

## 검사

리뷰 반영 뒤 전부 스테이지하고 스크립트 하나로 파이프 없이 돌렸다(출력은 스크래치 로그로, 종료 코드만 모았다).
ruff는 첫 판에 E501 둘을 냈고(독스트링을 고치며 뒷문장이 한 줄로 붙었다) 다시 감았다.

- `uv run pytest -q`: 976 passed, 4 deselected
- `ruff check .`, `ruff format --check .`, `pyright`, `lint-imports`, `pnpm -C web verify` 통과
- `tools/check_instructions.py`, `tools/check_type_escapes.py`, `tools/check_md_tables.py`,
  `tools/check_line_separators.py`, `tools/run_hooks.py` 통과
- `tools/mutate.py`: 이 chore의 변이 넷과 web-admin의 하네스 변이 모두 기대대로

잔존 grep: "모양 여섯", `claude_md_imports`, "Other exit codes", "직접 푸시 금지"는 이 일지의 경위 서술 밖에 0건이다.

## 다음

- **web-admin의 03과 04가 둘 다 풀렸다.** 01(#99)과 02(#98)가 병합됐다. 03(생성 클라이언트)이 05~08의 임계
  경로라 먼저 하고, 04는 01만 기다려 03과 나란히 갈 수 있다.
- 탐침 `instruction_loading/run.sh`를 다시 돌리면 사용자 전역 Stop 훅이 실행마다 알림을 보낸다(스크립트 머리에
  적었다).
