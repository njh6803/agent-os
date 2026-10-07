# 2026-10-07 (05) pre-commit의 무거운 검사가 커밋마다 두 번 돌던 것을 닫고 병렬화를 잰다

클라우드 세션(claude.ai/code)에서 `origin/main`(`cbb6a6c`) 위의 브랜치 `claude/funny-planck-itf28j`로 일했다. 브랜치
이름은 클라우드 세션이 정한 개발 브랜치다. 처음에는 열린 PR #156의 일지(`2026-10-07-01-tokens-story-seam-and-buttons.md`)를
보고 02를 매겼다. 커밋 직전에 PR #156이 병합돼 `162ae54`로 앞당겼고, 그 PR이 대기열 131을 먼저 써서 이 세션의 새 행을
132로 매겼다. 그 뒤 PR #157이 일지 `2026-10-07-02`와 대기열 132~134, 헌법 3.0.16을 먼저 병합해, 이 브랜치의 일지를
03·04·05로, 대기열 행을 135·136으로, 헌법 판을 3.0.17로 옮겼다(일지 2026-10-07-08). 다시 PR #159가 일지 04와
대기열 137을 쓰고 열린 PR #158이 일지 03, 대기열 135·136, 헌법 3.0.17을 써서, 일지를 05~09로, 대기열 행을
138~140으로, 헌법 판을 3.0.18로 옮겼다(일지 2026-10-07-09). 아래 "잰 것"은 모두
`cbb6a6c`의 트리에서 쟀다. PR #156은 web verify에 스토리 테스트를 더했으므로 그 뒤의 web verify는 더 길다(아래 검사).

## 계기

> 사용자: "pre-commit도 오래 걸리는 것 같은데 pre-commit도 병렬로 처리할 수 있어?"

## 잰 것

모두 이 컨테이너(Linux, CPU 4)에서 봤다. 사용자의 Windows PC와 절대값은 다르고 비율만 본다. 이 컨테이너에는 `pwsh`가
없어 `tests/tools/test_open_session.py`의 9건이 어느 실행에서나 실패한다(아래 검사).

- **훅별 시간과 동시 실행(프로브).** `.scratch/harness/probes/precommit_parallel.py`가 `always_run` 검사 일곱을 띄우는
  모양별로 잰다. 차례로(`serial`) 145.5초였다. 그 안에서 pyright 11.4초, import-linter 0.2초, pytest 68.9초, 지침 검사
  0.1초, 타입 우회 검사 1.0초, 훅 러너 5.0초, `pnpm -C web verify` 58.8초다. 파이썬 묶음(그 안은 차례로)과 web verify를
  나란히(`groups`) 띄우면 88.9초, 일곱을 한꺼번에(`all`) 띄우면 73.7초였다. 한꺼번에 띄운 실행에서는 그 실행의
  pytest(73.7초)가 가장 길었다. 각 명령의 종료 코드는 세 모양에서 같았다.
- **commit-msg 단계(손).** `uv run pre-commit run --hook-stage commit-msg --commit-msg-filename <파일>`이 pyright,
  import-linter, pytest, 지침 검사, 타입 우회 검사를 다시 돌려 80.1초였다. 그래서 커밋 한 번이 약 230초였다(대기열 118).
- **pre-commit은 훅을 동시에 돌지 않는다(코드 읽기).** 4.6.2 설치본의 `commands/run.py`에서 `_run_hooks`는
  `for hook in hooks` 반복문이다. 훅을 돌리는 길에서 동시 실행은 `require_serial`이 꺼진 훅 하나가 받은 파일 목록을
  나누는 `xargs.py`뿐이다.
- **pytest-xdist(손).** `uv run --with pytest-xdist pytest -q -n 4`(잠금 파일을 바꾸지 않는 일회성 실행)는 29.5초였고,
  결과는 9 failed(같은 `pwsh`), 1634 passed다.
- **함께 돌 때 서로 보는 파일(코드 읽기).** 경합을 일부러 만들어 재지는 않았다. Vitest의 판정자 테스트
  (`web/eslint.config.test.ts`)가 `web/judge-*`에 임시 트리를 쓰고, 지침 검사의 중첩 지침 파일 훑기(`os.walk`)가 그
  트리를 지난다. 찾는 이름을 만들지 않고, 도중에 사라진 디렉터리는 `os.walk`가 조용히 건너뛴다. 마크다운 표와 줄 구분
  문자 검사는 `git ls-files`로 훑어 미추적 파일을 보지 않는다. `tests/`에서 `web/` 아래에 파일을 열거나 쓰는 자리는 모두
  `tmp_path` 아래였다.

## 바꾼 것

- `.pre-commit-config.yaml`: pyright, lint-imports, pytest, check-instructions, check-type-escapes에 `stages: [pre-commit]`을
  두었다. 이유는 pyright 위의 주석 두 줄에 적고, run-hooks 위의 옛 주석("한 번 더 돈다")은 지웠다. 주석을 파일 머리가
  아니라 pyright 위에 둔 것은 열린 PR #156이 머리 주석 끝에 두 줄을 더해, 같은 자리에 쓰면 병합에서 부딪히기 때문이다.
- `KICKOFF.md`: 지침 검사를 등록하는 줄에 `stages: [pre-commit]`과 그 이유를 더했다. 그대로면 새 프로젝트에서 두 번 실행이
  다시 생긴다(셀프 리뷰 명세 축).
- `.scratch/harness/probes/precommit_parallel.py`와 그 README 행: 위 "잰 것"의 프로브다.
- `.scratch/retro-queue.md`: 118을 닫고, 115에 회차를 더하고, 138을 올렸다(아래 회고).

고친 뒤 commit-msg 단계는 0.3초이고 커밋 메시지 검사만 돈다. ruff 둘과 인용 대조는 받은 파일(커밋 메시지)이 맞지 않아
Skipped로 찍힌다.

## 병렬화는 러너 훅으로 간다

선택지 셋을 사용자에게 물었다. 셋 모두 ADR이 먼저다. 의존성을 더하거나 훅 시스템을 바꾸고, 러너도 `operations.md`
가드레일 절의 훅 서술을 바꾸는데 그 문서는 ADR 뒤에 쓴다(`CLAUDE.md` 지도).

1. **동시 실행 러너 훅 하나.** ruff 둘(파일을 고친다)은 앞에서 차례로 돌리고, 추적 파일을 고치지 않는 `always_run` 검사
   일곱을 스크립트 하나가 함께 띄워 결과를 모은다. 새 의존성은 없다. 위 프로브로 145.5초가 73.7초가 된다. 대가는
   pre-commit 출력의 훅별 줄과 `SKIP=<id>`의 단위가 러너 안으로 들어가는 것이다.
2. **prek.** Rust로 다시 쓴 pre-commit이고 같은 설정 파일을 읽는다. 같은 `priority`의 훅은 함께 돈다(prek 문서
   prek.j178.dev를 읽었다. 판은 보지 않았다). 새 도구라 ADR이 먼저이고, `operations.md`의 "훅 시스템은 pre-commit
   하나만 둔다"와 설치 절차가 함께 바뀐다.
3. **pytest-xdist.** pytest가 약 70초에서 약 30초로 준다. CI의 `python` 잡도 줄 것은 재지 않은 어림이다. ADR 0021의 첫째
   2026-10-01 이력이 거부한 안으로 미뤄 둔 새 의존성이다. `tests/conftest.py`의 skip 판정(원칙 II)이 워커로 나뉜
   실행에서도 서는지, 저장소 상태 테스트가 함께 돌아도 안전한지를 재야 한다.

> 사용자(질문에 답): "러너 훅 하나 (Recommended)"

ADR 초안은 ADR 0005의 이력으로 써서 이 세션의 답에 붙여 보이고, 승인을 받은 뒤 구현한다.

## 검사

- **commit-msg 단계(손).** 고치기 전 80.1초(위 다섯과 커밋 메시지 검사가 돌았다), 고친 뒤 0.3초(커밋 메시지 검사만
  Passed). 같은 명령을 스테이지한 설정으로 쳤다. 스테이지하지 않으면 pre-commit이 설정이 스테이지되지 않았다며 멈춘다.
- **pre-commit 단계(손).** `uv run pre-commit run --all-files`가 148초였다. 다섯 검사는 이 단계에서 그대로 돌았다. 실패는
  셋이었다. pytest는 `pwsh` 9건이다. 같은 pytest에 `files were modified by this hook`이 찍힌 것은 실행 도중 이 세션이
  일지와 설정 주석을 고쳤기 때문이다. 변이 표 검사는 `--all-files`가 커밋에 들지 않은 옛 표까지 넘겨 원문이 사라진 표
  여섯을 빨갛게 봤다. 이 훅은 커밋에 든 표만 보도록 설계됐고(설정 주석), 이 커밋에는 변이 표가 없다.
- **손으로 치는 검증 명령(마지막 판).** ruff check 통과, ruff format 435 파일, pyright 0 errors, import-linter 5 kept,
  `pnpm -C web verify` 종료 0, 지침 검사·타입 우회 검사 종료 0, `tools/run_hooks.py` 페이로드 61건 어긋남 0. pytest는
  9 failed, 1634 passed이고 실패는 모두 `tests/tools/test_open_session.py`의 "pwsh 가 없다"다. 원칙 II대로 이것은 초록이
  아니고, 이 컨테이너에서는 초록으로 만들 수 없다(대기열 138). 이 변경은 그 테스트가 지나는 코드에 닿지 않는다.
- **`162ae54`로 앞당긴 뒤(손).** ruff check 통과, ruff format 440 파일, pyright·import-linter·지침 검사·타입 우회 검사·
  훅 러너는 위와 같다. pytest도 위와 같은 9 failed, 1634 passed다. `pnpm -C web verify`는 73초에 종료 1이었다. Vitest의
  21파일 중 15파일 275건은 통과했고, PR #156이 더한 브라우저 스토리 테스트 6파일이 Playwright가 찾는
  `chromium_headless_shell-1243`이 없어 돌지 못했다(컨테이너에는 1194뿐). 이 컨테이너의 안내가 `playwright install`을
  치지 말라고 해서 설치하지 않았다. 그 뒤 단계인 tsconfig 검사는 따로 쳐서 종료 0이었다. 이것도 환경 탓이고 대기열
  138에 더했다.

## 셀프 리뷰

`/code-review`, base `cbb6a6c`, 수정 2, 미추적 1(일지), 커밋 0. 소스 파일이 없어 표준 축은 sonnet으로 돌렸다. 명세는
사용자 질문과 대기열 118이고, 이 세션이 한 것(주석 자리, 일지 순번, 측정 환경)은 리뷰어 참고로 갈랐다. 두 축 모두
Critical·Major는 없었다.

- **고쳤다, 표준 축 하드(근거 표기).** 병렬 측정을 세션 스크래치패드의 스크립트로 쟀는데 일지가 그것을 다음 결정의
  근거로 들었다. 스크립트를 `.scratch/harness/probes/precommit_parallel.py`로 커밋하고 README에 행을 두었으며, 차례 실행도
  같은 프로브에 넣어 "잰 것"의 수를 그 프로브로 다시 쟀다. 설정 주석에서는 수치를 빼고 일지를 가리켰고, 대기열 118의 닫힘
  칸에는 손으로 본 명령과 환경을 적었다. 나머지 수에는 손·코드 읽기·어림을 밝혔다.
- **고쳤다, 두 축의 Minor·Nit.** "동시 실행은 `xargs.py`뿐"을 훅을 돌리는 길로 좁혔다(`commands/autoupdate.py`도 스레드
  풀을 쓴다). `tests/`의 `web/` 주장을 파일을 열거나 쓰는 자리로 좁혔다. `tech.md`에는 훅 시스템 행이 없어 인용을
  `operations.md` 하나로 고쳤다. prek의 출처를 적고, CI `python` 잡이 줄 것은 어림이라 적고, "읽기만 하는"을 "추적 파일을
  고치지 않는"으로 고쳤다. 러너에도 ADR이 필요한 이유(`operations.md`는 ADR 뒤에 쓴다)를 적었다. `KICKOFF.md`의 지침 검사
  등록 줄에 `stages`를 더했다(명세 축).
- **남겼다.** 브랜치 이름은 `chore/<slug>`가 아니지만 클라우드 세션이 정한 개발 브랜치라 그대로 두었다. 최상위
  `default_stages: [pre-commit]`(표준 축의 제안)은 대기열 118이 훅별로 승인됐고 러너 변경이 같은 줄을 다시 짜므로 그
  변경에서 함께 다룬다.

## 회고

일지의 "다음"을 쓴 계기 훅으로 retro를 돌렸다. 후보 둘을 냈고 둘 다 승인됐다. 이 세션에서 반영한 것은 없고 138와 115로
갔다.

> 사용자(질문에 답): "대기열에 올린다 (Recommended)", "115에 회차를 더한다 (Recommended)"

1. **[정보 접근] 클라우드 세션은 검증 명령을 모두 초록으로 만들 수 없다(대기열 138).** 이 컨테이너에는 `pwsh`가 없어
   pytest 9건이 늘 빨갛고, web 의존성이 깔려 있지 않아 `pnpm -C web install --frozen-lockfile`을 손으로 쳤다. 대기열 80이
   "`pwsh`가 없는 것은 저장소 밖(클라우드 환경의 설정 스크립트)이다"라고 적고 넘긴 것과 같은 자리라 2회차다. 처방은
   claude.ai의 클라우드 환경 설정 Setup script에 `pwsh` 설치, `uv sync`, `pnpm -C web install --frozen-lockfile`을 두는
   것이고 사용자가 바꾼다. 승인 뒤 `162ae54`로 앞당기자 web verify의 스토리 테스트가 브라우저 판을 찾지 못해, 같은 행에
   `pnpm -C web exec playwright install --only-shell chromium`을 더했다.
2. **[도구 경제] 열린 PR과의 번호·자리 충돌(대기열 115, 4회차).** 열린 PR #156이 같은 날 일지 순번 01을 쓰고
   `.pre-commit-config.yaml`의 머리 주석 끝도 바꿨다. 이 세션은 열린 PR의 파일 목록을 보고 둘 다 피했지만, 그 목록을 받은
   GitHub MCP `pull_request_read`(`get_files`)가 패치까지 실어 242KB로 도구 결과 한도를 넘었다. 번호 대조에는 파일 이름만
   있으면 되므로, 115를 반영하는 브랜치가 이름만 받는 길을 함께 정한다.

후보로 내지 않은 것: 도구 호출 사이의 영어 문장 셋과 맨 `python3` 호출 하나는 기존 훅(`hook_midturn_korean`,
`hook_bash_python_stub`)이 그 자리에서 잡았다.

## 다음

- 러너 훅의 ADR 초안(ADR 0005 이력)에 대한 사용자의 승인을 받고, 그 뒤 `tools/run_checks.py`와 그 테스트, 설정, 가드레일
  절을 바꾼다. 최상위 `default_stages: [pre-commit]`(셀프 리뷰 표준 축의 제안)도 그 변경에서 함께 다룬다.
- PR #156이 web verify에 스토리 테스트(Playwright)를 더한다. 병합되면 web verify가 길어지므로, 러너를 구현할 때 프로브를
  다시 돌린다.
- 대기열 138은 저장소 밖이다. 사용자가 클라우드 환경 설정의 Setup script를 바꾼다.
