# 네 프로세스가 이미지 안의 명시적 설정이 있을 때만 컨테이너 네트워크 쪽 주소에 묶인다 (release-image 티켓 03)

브랜치 `feature/03-processes-bind-container-network-in-image`. 이 세션의 제목은 인계 직전까지 `feature/03-processes-bind-container-network-in-image`이다. 구현과 검증을 마치고 셀프 리뷰 직전에 컨텍스트가 문턱을 넘어 인계한다. 커밋과 푸시는 하지 않았고 변경은 모두 워크트리에 있다.

## 사용자 프롬프트 원문

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/release-image/issues/03-processes-bind-container-network-in-image.md
>
> 다음 작업: .scratch/release-image/issues/03-processes-bind-container-network-in-image.md. 네 프로세스가 이미지 안의 명시적 설정이 있을 때만 컨테이너 네트워크 쪽 주소에 묶이게 한다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 2. EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/release-image/issues/03-processes-bind-container-network-in-image.md
> 브랜치: feature/03-processes-bind-container-network-in-image
> 모델: Sonnet 5.5 / high
> 읽을 것: 티켓 02, 04
> 이어받을 상태: 티켓 01이 PR 570으로 병합됐다. 세 세션이 함께 돌아 시간에 기대는 시험이 번갈아 빨갈 수 있다. tidy-checkouts는 묶음의 첫 세션이 돈다
> 이번 요청 범위: PR과 병합까지

사용자의 다른 말은 없었다.

## 한 것

- 예외의 판정을 네 프로세스에 복사해 넣었다. 조건은 표지 파일 `/etc/agent-os/image`가 있고 환경 변수 `AGENT_OS_CONTAINER_NETWORK=1`이 함께 있을 때다. 켜지면 듣는 주소로 `0.0.0.0` 하나가 늘고 관리 화면 상류 호스트로 `serve` 하나가 는다. 환경 변수가 없거나 비면 꺼진 것이고 다른 값은 구성 오류(`invalid-env`)이며 호스트 판정보다 먼저 난다.
  - 파이썬 `serve`: `src/agent_os/main.py`의 `ContainerNetwork`, `_container_network()`, `binding_problem`.
  - 관리 화면: `web/apps/admin/tools/loopback.ts`, `start.ts`, `next.config.ts`.
  - 위젯: `web/apps/widget/tools/start.ts`.
  - 위젯 미리보기 페이지: `web/apps/portal/server/config.ts`, `load.ts`, `tools/start.ts`.
- 판정은 표지 파일의 유무를 인자로 받는 순수 함수이고, 표지 파일을 읽는 자리는 네 곳이다(파이썬 `_container_network()`, 관리 화면 `loopback.ts`·위젯 `start.ts`·미리보기 페이지 `load.ts`의 `currentNetwork()`. 처음에 "둘뿐"이라 적은 것은 이름이 같은 함수를 하나로 센 틀린 문장이었고 셀프 리뷰가 잡았다). 환경 변수 `HOSTNAME`은 쓰지 않는다.
- 사례 표 `tests/fixtures/container_network/cases.json`과 `README.md`를 더했다(선례 `tests/fixtures/site_file/`). 파이썬 시험과 앱 셋의 `testing/container-network.ts`(같은 읽기 코드의 복사본 셋)가 그 표를 읽는다. 앱 사이 import는 층 경계가 막아 복사했다.
- `README.md`에 예외 한 줄과 픽스처 설명 한 줄을 더했다. 티켓 `Status`를 `done`으로 바꾸고 체크박스를 모두 채웠다. `uv run python tools/plan_table.py`는 `.scratch/plan.md`를 바꾸지 않았다.
- 티켓의 "ADR 본문은 고치지 않고" 항목: ADR 0010·0011·0015·0019·0024·0050에는 이미 `(바뀜: ADR 0056)` 포인터가 있어 본문을 고치지 않았다.

## 변이 시험(티켓 "손으로 한 번 본다")

- 명령: `pnpm -C <워크트리>/web/apps/widget exec vitest run tools/start.test.ts`
- 위젯 `start.ts`의 `enabled && host === CONTAINER_HOST`를 `if (enabled)`로 바꾸자 표를 읽는 시험 3건이 빨갰다(3 failed, 72 passed). 원래대로 되돌리자 75 passed였다. 한 곳의 판정만 바꾸면 표를 읽는 시험이 빨개진다는 것을 이로써 확인했다.

## 검증

- `uv run ruff check .`와 `uv run ruff format --check .`: 통과.
- `uv run python tools/run_checks.py`: 종료 0(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, pytest 911.8초, web-verify 1167.9초).
- e2e: 관리 화면, 위젯, 위젯 미리보기 페이지를 이 PC에서 돌렸다. 처음에 관리 화면의 결정 흐름 e2e(`e2e/decision.e2e.ts`)가 5초 제한에서 두 번, 위젯 e2e의 `add` 도구 대기가 한 번 빨갰다. 원인은 이 PC의 부하다(`import agent_os.adapters.mcp`가 부하가 높을 때 12.5초, 낮아지자 4.1초). 부하가 내려간 뒤 다시 돌리자 모두 통과했다. 정리 단계의 임시 폴더 `rmSync` EPERM(윈도)이 "1 error was not a part of any test"로 뜨는 일은 통과한 시험에도 났고 이 변경과 무관하다.
- 기준선 대조 실험(네 파일을 origin/dev 것으로 바꿔 e2e를 돌리는 것)은 globalSetup에서 실패했다. 새 시험 파일이 기준선의 `next build` 타입 검사에 걸렸기 때문으로 보며, 실험이 성립하지 않아 증거로 쓰지 않는다. 네 파일은 스크래치패드 사본으로 모두 되돌렸다.
- `sync-design-system 확인` 알림은 도구·시험·설정 파일만 고쳤고 화면은 건드리지 않아 따르지 않았다.

근거의 종류: 변이 시험의 수, ruff, `run_checks.py`의 종료 코드와 시간, e2e의 통과와 실패는 이 세션이 명령을 쳐서 출력으로 본 것이다. "원인은 PC 부하"는 `import agent_os.adapters.mcp`를 부하가 다른 두 때에 손으로 재어(12.5초, 4.1초) 세운 어림이고 프로브로 고정하지 않았다. 기준선 실험의 실패 까닭은 추정이다. `sync-design-system` 알림을 따르지 않은 판단은 고친 파일 목록을 읽은 것이다. 화면은 렌더해 보지 않았다.

## 셀프 리뷰 (2026-11-15, 이어받은 세션)

범위: base SHA `9a68c2bb9`(origin/dev), 변경 20개 파일과 미추적 5곳, 커밋 0. 표준 축은 sonnet·high, 명세 축은 본 세션 모델이 맡았다. 둘 다 Critical은 없었고, 네 곳의 판정은 코드를 읽어 대조한 것에서 어긋난 곳이 없었다(TS 시험은 명세 축이 돌리지 않았다).

고친 것:
- 표지 파일 존재 판정이 갈렸다. 파이썬은 `is_file()`, TS 셋은 `existsSync`여서 표지 경로가 디렉터리면 파이썬은 꺼지고 TS는 켜진다(두 축이 코드를 읽어 낸 것이고 돌려 보지는 않았다). 파이썬을 `exists()`로 맞추고 `ContainerNetwork` 독스트링에 "파일인지는 가리지 않는다"를 적었다.
- 낡은 "루프백만" 문장. `serve`의 `--help` 두 줄(`channel/cli/main.py`)에 이미지 안의 예외를 적고 같은 파일 주석을 고쳤다. README의 시작 래퍼 설명 둘(75·82행)과 관리 화면 상류 문장(135행)에 "이미지 안의 예외는 아래"를 달았다. `.scratch/plan-head.md` 한 줄도 고쳐 `plan_table.py`로 `.scratch/plan.md`에 옮겼다.
- README 136행의 괄호가 거꾸로였다. 표지 파일 없이 환경 변수만 있는 경우(개발 PC)와 환경 변수 없이 표지 파일만 있는 경우(`docker run`)로 갈라 적었다.
- 위젯 `start.ts` 머리 주석의 "목록을 바꾸면 넷을 함께 고친다"에 예외와 사례 표를 더했다.
- 위 "한 것"의 "표지 파일을 읽는 자리는 둘뿐"이라는 문장. 읽는 자리는 네 곳이고(파이썬 `_container_network()`, 관리 화면·위젯·미리보기 페이지의 `currentNetwork()` 셋) 이름이 같은 함수를 하나로 센 틀린 문장이어서 그 자리에서 고쳤다.

남긴 것과 이유:
- 표지 파일이 없고 환경 변수가 `1`인데 `0.0.0.0`이 아닌 주소(예 `192.168.0.10`)를 받으면 일반 루프백 진단만 나온다. 티켓 문장은 호스트를 가리지 않지만 "이미지 밖에서는 켜지지 않는다"는 말은 예외가 열어 줄 주소(`0.0.0.0`)를 받았을 때만 뜻이 있고 사례 표 README가 그렇게 좁혔다. 의도한 해석으로 두고 PR 본문에 적는다.
- 표지 경로가 디렉터리인 입력은 사례 표(`marker` 불리언)가 잠그지 못한다. 네 곳이 같은 존재 의미를 쓰도록 맞췄고 표에 칸을 더하지 않는다.
- smell 판단 항목(`ContainerNetwork` 이름, `host` 변수가 진단 문자열을 담는 이름, portal `hostOf`가 `envProblems`를 여러 번 부름, 불리언 칸)은 복사본 넷을 함께 건드려야 해 이 티켓의 범위를 넘으므로 고치지 않았다.

다시 돌린 것(이 세션이 친 명령의 출력): `uv run ruff check .`와 `uv run ruff format --check .` 통과, `uv run pytest -q tests/test_main.py tests/channel/cli` 통과(점만 찍혀 건수는 보지 않았다), `uv run python tools/plan_table.py`가 `.scratch/plan.md`를 바꿨다. 나머지 검증 명령은 커밋이 부르는 pre-commit의 결과로 갈음하고, 그 결과는 커밋 뒤 PR 본문에 적는다.

## 커밋 전 pytest가 부하로 빨갰던 일과 사용자의 결정

pre-commit의 검사 러너(`parallel-checks`)로 같은 변경을 네 번 커밋하려 했고 네 번 모두 pytest만 빨갰다. 나머지 검사 아홉(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, web-verify)은 네 번 모두 통과했다(이 세션이 그 출력을 읽었다). 빨간 시험은 시도마다 달랐다(4, 6, 1, 5건). 모두 제한 시간 안에 끝나는지를 재는 시험이었다(`test_interrupt` 매번 1~3건, `test_rerun_runner`·`test_rerun_gates`·`test_probe_kit`). 이 변경은 그 시험과 그 코드를 건드리지 않았다. 단독으로 다시 돌려 통과를 본 것은 `test_interrupt` 3건과 `test_rerun_runner` 1건이고(이 세션이 친 명령의 출력), 나머지는 단독으로 돌리지 않았다. 다른 세션 넷이 같은 PC에서 돌고 있었고(`list_sessions`의 `isRunning`), 그 부하 탓이라는 것은 어림이다. 부하를 직접 재지는 않았다.

> 사용자: (AskUserQuestion "커밋 방법"의 답) "pytest 검사만 건너뛰기". 고른 선택지의 설명: 검사를 한데 모아 돌리는 훅(`parallel-checks`, 열 검사)을 `SKIP`으로 건너뛰고 커밋합니다. 이 훅 하나가 빠지면 pytest 말고 린트·pyright·경계·지침 검사·web 검증도 함께 빠지므로, 그것들은 같은 변경으로 네 번 모두 통과한 결과를 근거로 삼고 pytest는 PR의 CI가 판정하게 둡니다. 훅을 건너뛰는 일이라 먼저 승인을 받습니다.

따라서 이 커밋은 `SKIP=parallel-checks`로 올린다. pytest는 CI가 판정한다. CI의 pytest는 한 프로세스라 이 PC의 xdist 부하 시험과 조건이 다르다(`docs/constitution/operations.md`가 러너와 CI의 차이를 적는다).

## 인계

- 인계 경계: 셀프 리뷰 직전. 제목을 `feature/03-processes-bind-container-network-in-image (인계함)`으로 바꿨고(바꾸기 전 제목은 브랜치 이름 그대로), 워크트리 잠금을 풀었다. 이 세션이 띄운 백그라운드 작업은 없다.
- open-session을 부른다 2026-11-14T17:26Z

## 남은 것

- 셀프 리뷰(`/code-review`)와 Critical·Major 반영, `uv run python tools/sibling_overlap.py`, 커밋 직전 `git branch --show-current`, 커밋, 푸시, PR, 봇 회차, 병합(`merge.md`), 일지 "다음", 회고(`retro`).
- 리뷰의 명세 출처는 티켓과 `.scratch/release-image/spec.md`의 "루프백 규칙의 예외"·"관리 화면의 상류", ADR 0056 결정 "루프백 규칙의 예외"다. 기준은 `origin/dev`다.
