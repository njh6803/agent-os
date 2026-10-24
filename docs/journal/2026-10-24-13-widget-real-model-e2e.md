# 2026-10-24 (13) 실제 모델을 부르는 위젯 e2e(web-widget 11)

## 사용자 프롬프트

> 사용자: /implement .scratch/web-widget/issues/11-widget-real-model-e2e.md (next-session 지시문. 나란히 여는 3 중 3, 브랜치 feature/11-widget-real-model-e2e, 범위는 PR과 병합까지. 나란히 도는 티켓은 07·10이고 tidy-checkouts는 묶음의 첫 세션이 돈다)

## 결정

명세(Testing Decisions 6)와 ADR 0024 이력 2026-10-23 둘째가 모양을 정해 두어, 사용자에게 물은 것은 없다. 구현에서 고른 것은 아래다.

- **프로젝트 `llm`은 변수 하나로 선다.** `AGENT_OS_WIDGET_LLM=1`일 때만 `playwright.config.ts`가 프로젝트 `llm`(`*.llm.ts`, 제한 시간 180초)을 더한다. 프로젝트마다 `testMatch`를 두어 기본 프로젝트 `chromium`은 `*.e2e.ts`만 본다. 그래서 로컬의 `playwright test`와 CI의 `e2e-widget`은 변수가 없어 그대로다(`--list`로 변수 없이 6개, 있을 때 7개를 손으로 봤다). Vitest의 node 프로젝트가 설정 파일을 불러 이 가름을 고정한다(`playwright.config.test.ts`).
- **실제 모델 모드의 준비.** 같은 `stack.ts`가 변수를 보고 저장소의 `plugins/`를 임시 플러그인 루트에 복사한 뒤 픽스처 플러그인을 얹고, 사이트 파일의 에이전트 목록에 `calc`를 더한다. `serve`의 트레이스 폴더는 `AGENT_OS_WIDGET_TRACES`가 있으면 그 자리다. 파이썬 시험이 그 자리를 자기 `tmp_path` 아래로 주어 `conftest.py`의 토큰 합계가 센다.
- **화면의 출력은 Playwright JSON 리포트의 주석으로 파이썬에 넘긴다.** 시험이 출력 문단의 글을 `화면의 출력` 주석으로 남기고, 파이썬이 `PLAYWRIGHT_JSON_OUTPUT_FILE`의 리포트에서 그것을 꺼내 트레이스의 `run_finished` 출력과 맞댄다. 기준 셋(통과 1·건너뜀 0, 트레이스의 `llm_called`, 화면과 트레이스의 출력이 같다)은 모아서 한 번에 알려, 하나가 빨개도 나머지의 글이 함께 보인다.
- **pnpm은 `shutil.which`의 경로로, 출력은 기록 파일로, 제한 시간에는 프로세스 나무째 끝낸다.** 경로로 띄우는 것은 ADR 0024의 측정이다. 윈도에서 `.cmd`는 cmd.exe가 다시 읽으므로 명령 줄에는 고정 인자만 두고 바뀌는 값은 작업 폴더와 환경으로 넘긴다. 제한 시간(600초)을 넘기면 `tools.run_checks.kill_tree`로 손자(serve, Next, chromium)까지 끝낸다.

## 한 것

- 실제 모델 위젯 e2e(`web/apps/widget/e2e/calc.llm.ts`): 위젯에서 `2 더하기 3은?`을 보내 출력 문단이나 실패 알림이 서기를 150초까지 기다리고, 실패 알림이 없다고 단언한다. 모델이 도구를 부를지는 단언하지 않는다(ADR 0024 이력).
- 감싸는 파이썬 시험(`tests/test_widget_llm.py`, 마커 `llm_widget`)과 그 부품의 시험 셋(pnpm 이 없을 때의 문구, 종료 코드와 기록, 제한 시간에 손자까지 끝내기). 마커는 `pyproject.toml`에 선언하고 기본 실행의 `addopts`가 `llm`과 함께 뺀다. 토큰 합계는 두 마커를 센다(`tests/conftest.py`, pytester 시험 둘을 먼저 빨갛게 봤다).
- 닫힌 문장을 고쳤다. 운영 문서 LLM 테스트 절(마커 둘, 둘째 명령과 계기, 원칙 I 판정이 아니라는 것), `CLAUDE.md` 검증 명령 두 곳, `.claude/rules/tests.md`·`http.md`("유일한 자리"를 풀었다), `.coderabbit.yaml`, CI 머리 주석, PR 템플릿, `tools/hook_env_read.py`의 안내, `tools/mutate.py` 사용법, `tools/llm_tokens.py`·`tests/conftest.py`·`tests/test_conftest.py`·`tests/test_main.py`·`tests/test_calc_plugin.py`·`tests/tools/test_llm_tokens.py`의 독스트링. 헌법 판 3.0.56. `-m llm`을 목록의 한 예로 든 문장(러너 독스트링, ADR 0035, 관리 화면 `stack.ts` 머리)은 여전히 참이라 두었다. 옛 표현의 grep 잔존은 0이다(`tests/test_main.py` 5행은 "이 파일에서는"으로 좁힌 문장이라 참이다).

## 막힌 것

- 큰 막힘은 없었다. 훅이 `cd web/apps/widget`(→ `pnpm -C`), `$(find …)`가 든 grep(`.env`에 닿을 수 있다), 판정 명령의 파이프를 막거나 경고해 그대로 고쳐 쳤다.

## 변이

`.scratch/web-widget/probes/widget_llm_mutations.toml`, 변이 여덟. 도구가 8 모두 기대대로로 판정했다. 실제 모델을 부르는 셋(Playwright 시험 건너뛰기, `serve`의 환경에서 키 빼기, 위젯이 출력의 끝 글자를 빼고 그리기)은 각자의 기준이 지은 글(`{'expected': 0, 'skipped': 1`, `트레이스 1개에 llm_called 가 없다`, `이 트레이스의 run_finished 출력 ['`)로 본다. 첫 실행에서 5(제한 시간에 자식만 끝내기)가 빨갛지만 표지 `where False = <function _stops_growing`이 없었다. pytest 가 함수 객체가 아니라 호출 꼴을 찍어서다. 원문 줄에 없고 운영체제에 기대지 않는 `where False = _stops_growing(`로 바꿔 5를 다시 돌렸다(첫 결과를 본 뒤 바꾼 기준이다). 3은 위젯을 다시 빌드해 171초였다.

기준선의 통과와 2의 빨강이 함께, `pnpm_spawn.py`가 재지 않은 것(Playwright 가 다시 띄우는 `serve`까지 `.env`의 키가 닿는지)을 양쪽으로 보였다. 키가 운영체제의 환경 변수에서 왔다는 해석은 `--env-file` 없이 친 같은 시험이 키 확인에서 실패한 것으로 갈랐다(손으로 봤다).

그 키 없는 실행에서 다른 것을 봤다. 키 확인 `assert "ANTHROPIC_API_KEY" in os.environ, …`이 실패하면 pytest 의 단언 재작성이 `os.environ` 전체를 실패 출력에 찍는다(기본은 잘리고 `-vv`면 다 찍힌다). 키가 없을 때의 일이라 그 키는 실리지 않지만, 같은 환경의 다른 비밀(토큰)이 실릴 수 있다. 같은 꼴이 `tests/core/test_model.py`와 `tests/test_main.py`에 일곱 곳 더 있는 관례라 이 티켓에서 한 곳만 바꾸지 않고 후속으로 넘긴다("다음").

## 카나리아

바꾼 하네스 문서 셋이 새 `claude -p` 세션에 실리는지 `tools/canary.py`로 봤다(claude 2.1.302). `CLAUDE.md`(`.scratch/web-widget/probes/canary/claude_md_llm_widget.toml`, 대조군은 바뀌기 전 커밋 `148652ef`이고 옛 문장을 옮겼다), `.claude/rules/tests.md`(`tests_rule_llm_widget.toml`), `.claude/rules/http.md`(`http_rule_llm_widget.toml`) 모두 통과 4였다. 원래 있던 `tests_rule_llm_tokens.toml`은 이번에 고치지 않은 문장을 물어 다시 돌리지 않았다.

## 검사(셀프 리뷰 전)

- `uv run ruff check .`, `uv run ruff format --check .`: 둘 다 초록.
- `uv run python tools/run_checks.py`: 모두 Passed(check-ticket 1.2s, zizmor 2.3s, lint-imports 2.5s, check-instructions 7.6s, check-type-escapes 9.1s, pyright 45.1s, pyright-linux 48.5s, run-hooks 90.0s, web-verify 371.2s, pytest 433.0s). 문서 고침을 마친 뒤의 작업 트리다. 그 뒤 고친 것은 이 일지와 티켓 체크박스, 운영 문서 한 문장(워크트리 경로를 글자로 적었다)이다.
- `uv run --env-file ../../../.env pytest -m llm_widget`: `1 passed, 5597 deselected in 55.59s`. 끝 줄은 `LLM 토큰 합계 6,555(입력 6,483, 출력 72). 트레이스 1개, 모델 호출 2건.`이었다. 시험 코드를 다 지은 뒤의 실행이고, 그 뒤 고친 것은 문서뿐이다. 변이 도구의 기준선도 같은 시험을 다시 돌려 `1 passed, 3 deselected in 32.17s`였다.
- 아직 치지 않은 것: 모델 없는 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`)를 바꾼 뒤에 다시 보기(바꾸기 전 기준은 6 passed, 45.2초. 바꾼 뒤에는 `--list`로 변수 없이 6개만 손으로 봤다), `-m llm`을 돌려 이 시험이 끼지 않은 것 보기(티켓 44행).

## 인계(셀프 리뷰 직전)

세션 컨텍스트가 문턱을 넘은 채 셀프 리뷰 직전에 와 인계했다(`hook_handoff`). 이 세션의 제목은 `feature/11-widget-real-model-e2e`였고 `feature/11-widget-real-model-e2e (인계함)`으로 바꾼다. 넘길 때의 상태:

- 변경은 모두 커밋하지 않았다. 수정 23, 미추적 8(`tests/test_widget_llm.py`, `web/apps/widget/e2e/calc.llm.ts`, `web/apps/widget/playwright.config.test.ts`, 변이 표, 카나리아 명세 셋, 이 일지).
- 셀프 리뷰는 시작하지 않았다(`code-review`를 불렀지만 단계를 밟기 전에 계기가 왔다). base 는 `148652ef`(origin/main, 이 브랜치의 merge-base)다. 명세는 티켓 파일과 `.scratch/web-widget/spec.md`의 Testing Decisions 6이다.
- 티켓 체크박스는 15~39행을 채웠다. 남은 것은 43행(검증 명령 모두 초록. 셀프 리뷰 반영 뒤 pre-commit으로 갈음)과 44행(`-m llm_widget`은 위 검사 절에 적었고 `-m llm`은 아직), 그리고 Status done 이다.
- 후속 후보 하나: 위 변이 절의 키 확인 단언이 `os.environ` 전체를 찍는 것(여덟 곳). 이 티켓 밖이라 별도 작업으로 넘길지, 회고 후보로 둘지는 이어받는 세션이 정한다.
- 주 체크아웃은 `148652ef [main]`(origin/main 과 같다).
- 제목을 바꿨고, 멈출 백그라운드 작업은 없었으며, `git worktree unlock C:/project/agent/.claude/worktrees/11-widget-real-model-e2e`가 오류 없이 끝났다.

인계 지시문:

```
다음 작업: .scratch/web-widget/issues/11-widget-real-model-e2e.md. 실제 모델을 부르는 위젯 e2e
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/11-widget-real-model-e2e.md
브랜치: feature/11-widget-real-model-e2e
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-13-widget-real-model-e2e.md의 "## 검사(셀프 리뷰 전)"와 "## 인계(셀프 리뷰 직전)"
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, base 148652ef)부터 한다. 그 뒤 모델 없는 위젯 e2e와 -m llm을 쳐 티켓 44행을 닫고, 일지의 셀프 리뷰·회고·다음을 마무리해 커밋·PR·병합까지 간다. docs/journal/2026-10-24-13-widget-real-model-e2e.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-24T12:04:08Z

## 이어받은 세션

인계 지시문으로 연 새 세션이 같은 워크트리(`.claude/worktrees/11-widget-real-model-e2e`)에 들어와 이었다. `origin/main`은 `148652ef`에서 움직이지 않았다(`git fetch` 뒤 `git log 148652ef..origin/main`이 비었다).

## 검사(셀프 리뷰 중)

- `pnpm -C web/apps/widget exec playwright test`: `6 passed (48.8s)`. 여섯 모두 `[chromium]`이고 프로젝트 `llm`의 시험은 목록에 없었다. 바꾸기 전 기준(6 passed, 45.2초)과 수가 같다. 셀프 리뷰 서브에이전트 둘이 도는 동안 친 것이라, 리뷰 반영이 위젯 e2e의 파일을 고치면 다시 친다.

## 셀프 리뷰

`/code-review`, base `148652ef`, 수정 23·미추적 8·커밋 0. 표준 축은 sonnet·high, 명세 축은 본 세션의 모델이다.

표준 축(Critical·Major 0, Minor 3, Nit 4)과 판정:

- Minor 1: `tests/test_main.py`의 `uvicorn_calls` 독스트링(838~839행)과 `test_토큰과_루프백이_갖춰지면_…` 독스트링(1007~1008행)이 포트를 실제로 여는 것을 "`-m llm` 과 두 e2e"가 잰다고 닫았다. `-m llm_widget`도 실제 `serve`를 띄운다. 일지 "한 것"의 "옛 표현의 grep 잔존은 0"은 티켓이 든 말로 센 것이라 이 문장을 잡지 못했다. → 고침. 목록에 하나를 더하지 않고, 실제 `serve` 서브프로세스를 띄우는 시험들이 잰다는 일반 조항으로 쓰고 목록은 `.claude/rules/http.md`의 테스트 줄 하나에 둔다. `web/apps/admin/e2e/stack.ts` 머리의 "실제 `serve` 를 띄우는 것은 이것과 위젯 e2e (`apps/widget/e2e/stack.ts`), `tests/test_main.py` 의 `-m llm` 테스트다"(주석 두 줄에 걸친다)는 `-m llm_widget`도 같은 `stack.ts`가 `serve`를 띄우므로 참이라 둔다.
- Minor 2: 치는 때가 문서마다 다르다. `docs/constitution/operations.md`, ADR 0024 이력, 명세, 티켓 36행은 "서버의 최종 사용자 경로와 항목의 투영"인데 `CLAUDE.md` 47행과 PR 템플릿 54행은 "항목의 투영"이 없다. → 고침. 바뀐 `CLAUDE.md` 문장은 카나리아(`claude_md_llm_widget.toml`)를 다시 돌린다.
- Minor 3: `tests/test_widget_llm.py`의 `_run_tree`가 `tools/run_checks.py`의 `run_one`·`_wait`와 겹친다(Duplicated Code 판단). → 보류. 공유할 핵심(`kill_tree`)은 이미 가져다 쓴다. 남은 겹침은 `Popen`과 기다림 열 줄 남짓이고, `run_one`은 환경을 받지 않으며(`Check`에 칸이 없다) 출력을 파이프로 받아 `_drain`의 제한 시간으로 끊는다. 이 시험은 손자(serve, Next, chromium)가 파이프를 쥐는 일을 피하려고 파일로 받는다(독스트링). 맞추려면 러너의 계약을 이 티켓에서 넓혀야 한다.
- Nit 4: `web/apps/widget/e2e/stack.ts` 머리 "모델은 부르지 않는다."와 `e2e/plugins.ts` 머리 "에이전트는 모델 없이 돈다."가 바로 아래 문단의 실제 모델 모드와 어긋난다. → 고침("기본은", "픽스처 에이전트는"으로 좁힌다). `.claude/rules/http.md`의 "모델을 부르지 않는 두 e2e" 괄호는 같은 문장이 바로 뒤에 `-m llm_widget`을 따로 들어 둔다.
- Nit 5: `web/apps/widget/e2e/env.ts`의 새 주석 "앞의 둘은"이 가리키는 상수보다 위에 있다. → 고침(이름으로 가리킨다).
- Nit 6: 두 언어에 같은 글자로 둔 상수 셋(`LLM_ENV`, `TRACES_ENV`, `SHOWN_ANNOTATION`)과, `_annotations`·`_error_messages`가 같은 모양으로 JSON을 훑는 것, `_read`라는 이름. → 상수는 둔다(언어가 달라 한 곳에 둘 수 없고, 어긋나면 기준과 변이 2·6이 빨갛게 잡는다). 훑기 둘은 리포트의 객체를 모두 내는 `_objects` 하나로 모으고 `_read`는 `_read_trace`로 바꾼다.
- Nit 7: 머리 독스트링 "못 보는 것"의 "그 임시 폴더가 남는다"는 코드를 읽고 쓴 문장이다(변이 5는 파이썬 손자만 끝내 봤다). → 고침(코드를 읽은 것이라 적는다).

명세 축(Minor 4, Nit 4. 확인한 것: 티켓 38행의 열 곳, 기준 다섯마다 시험과 그 기준만 짓는 글로 빨개지는 변이, `playwright.config.test.ts`가 vitest `node` 프로젝트에서 3 통과, 운영 문서의 다섯 요소, `CLAUDE.md` 두 곳, 헌법 판 3.0.56, `-m llm`으로 모으면 6개이고 이 시험은 빠진다)과 판정:

- Minor (a): `.scratch/web-widget/probes/pnpm_spawn.py` 독스트링(`148652ef`의 판)이 "Testing Decisions 6 은 … `-m llm` 파이썬 시험 하나가 … 돌린다고 정했다"와 "pytest 의 `-m llm` 표지"를 적었다. 진행 중인 기능의 프로브 독스트링은 살아 있는 문서다(`docs/constitution/operations.md` 문서 위치). ADR 0024 이력 2026-10-23 "실제 모델을 부르는 위젯 e2e는 LLM 시험 하나가 감싼다"가 마커를 `llm_widget`으로 정했다. → 고침. 일지 "한 것"의 잔존 0은 프로브를 훑지 않은 셈이었다.
- Nit (a): `CLAUDE.md`·PR 템플릿에 "항목의 투영"이 없다. → 표준 축 Minor 2와 같은 것이고 고쳤다.
- Nit (b): PR 템플릿에 `-m llm_widget` 계기를 더한 것은 요청 밖이고 셋째 사본이다. → 둔다. 그 줄은 PR이 칠 검증 명령의 목록이고, LLM 테스트를 `-m llm` 하나로 닫았다(티켓 38행이 고치라는 닫힌 문장의 꼴이다). 빼면 위젯을 건드린 PR이 그 명령을 떠올릴 자리가 없다. 사본 사이의 어긋남은 위 Minor 2에서 맞췄다.
- Minor (c): 프로브 README의 `widget_llm_mutations.toml` 행이 앞의 세 변이가 "각각 기준 하나…만 빨개지는지" 본다고 적었다. `tools/mutate.py`의 `expect_output`은 표지가 있는지만 보고, 1은 요청을 보내지 않아 트레이스와 화면의 출력도 없다. → 고침(그 기준이 빨개지는 것을 그 기준만 짓는 글로 본다고 쓴다).
- Minor (c): 제한 시간 시험의 자식은 파이썬을 바로 띄워, 티켓 31행이 짚은 길(`.cmd` → cmd.exe → node)을 지나지 않는다. → 고침. 자식을 실제 시험의 pnpm처럼 셸이 사이에 든 명령(윈도우 `.cmd`, POSIX 실행 권한을 준 `sh` 스크립트)으로 바꾸고 변이 5를 다시 돌린다.
- Minor (c, 갈래 밟기): POSIX에서 `start_new_session=True`라 pytest를 Ctrl-C로 끊으면 자식 쪽 그룹에 SIGINT가 닿지 않아 Playwright·serve·Next가 남는다. → 보류. 티켓 31행의 기준은 제한 시간이고, 끊긴 실행을 정리하는 시험은 이 티켓이 요구하지 않는다. 못 보는 것에 적는다(코드를 읽은 것이다).
- Nit (c): 변이 표 머리는 실제 모델 변이 하나가 "1~2분", README는 "1~3분"이고 3은 171초였다. → 고침(표 머리를 1~3분으로).
- Nit (c): `tests/test_main.py` 839·1007행. → 표준 축 Minor 1과 같은 것이고 고쳤다.
- 일지가 "여전히 참이라 두었다"고 한 셋(러너 독스트링, ADR 0035, 관리 화면 `stack.ts` 머리)은 명세 축도 참으로 봤다.

고친 것(반영으로 새로 쓴 사실 문장. PR 직전 리뷰에 밀 주장으로 넘긴다):

1. `tests/test_main.py` `uvicorn_calls`: "uvicorn 이 실제로 포트를 여는 것은 기본 스위트가 증명하지 않고 실제 serve 서브프로세스를 띄우는 시험들이 잰다. 그 목록은 `.claude/rules/http.md` 의 테스트 줄 하나에 둔다."
2. `tests/test_main.py` `test_토큰과_루프백이_갖춰지면_…`: "그것은 실제 serve 를 띄우는 시험들이 잰다(`uvicorn_calls` 의 독스트링)."
3. `CLAUDE.md` 47행: "위젯, api-client의 위젯 몫, 서버의 최종 사용자 경로와 항목의 투영을 건드렸으면 위젯의 실제 모델 e2e인 `-m llm_widget`도 친다." PR 템플릿 54행도 같은 낱말을 더했다.
4. `web/apps/widget/e2e/stack.ts` 머리: "기본은 모델을 부르지 않는다." `e2e/plugins.ts` 머리: "픽스처 에이전트는 모델 없이 돈다." `e2e/env.ts`: "아래 `LLM_ENV`·`TRACES_ENV` 는 거꾸로 실제 모델 e2e 를 감싸는 파이썬 시험(tests/test_widget_llm.py)이 러너에 주는 것이다".
5. `tests/test_widget_llm.py` 머리 "못 보는 것": "그 임시 폴더(`agent-os-widget-e2e-*`)가 남을 것이다. POSIX 에서 이 pytest 를 Ctrl-C 로 끊으면 SIGINT 가 제 세션을 연 자식에 닿지 않고 `_run_tree` 는 제한 시간만 받아, Playwright 와 그것이 띄운 serve·Next 가 시험을 마칠 때까지 남을 것이다. 둘 다 코드를 읽은 것이고 재지 않았다."
6. `tests/test_widget_llm.py` `_shell_wrapped`: "실제 시험의 `pnpm.CMD` 가 cmd.exe 로 읽혀 node 에 스크립트 파일을 넘기듯, 셸이 자식이 되고 파이썬은 그 아래에 뜬다."(`pnpm.CMD`의 끝 줄이 `"%_prog%"  "%dp0%\node_modules\pnpm\bin\pnpm.mjs" %*`인 것을 손으로 봤다) 제한 시간 시험: "`.cmd` 를 거친 자식만 끊으면 그 아래가 남을 수 있다(티켓 11)."
7. `tests/test_widget_llm.py`: JSON 리포트를 훑는 재귀를 `_objects` 하나로 모았고 `_read`를 `_read_trace`로 바꿨다. 독스트링 "리포트 안의 객체를 깊이와 상관없이 모두."
8. `.scratch/web-widget/probes/pnpm_spawn.py`: "Testing Decisions 6 은 위젯 e2e 의 Playwright 프로젝트 `llm` 을 마커 `llm_widget` 을 단 파이썬 시험 하나가 자식 프로세스로 돌린다고 정했다." "못 보는 것"의 "pytest 의 `llm_widget` 표지".
9. 프로브 README `widget_llm_mutations.toml` 행: "각각 기준 하나(…)가 빨개지는 것을 그 기준만 짓는 글로 본다. 다른 기준이 함께 빨개지는 것은 가리지 않는다(1은 요청을 보내지 않아 트레이스도 화면의 출력도 없다. 코드를 읽었다)." 결과 칸에 5의 재실행을 더했다. 변이 표 머리는 "1~3분".
10. 카나리아 `claude_md_llm_widget.toml`의 기대에 "서버의 최종 사용자 경로와 항목의 투영을 건드렸으면"을 더했다.

남긴 것: 표준 축 Minor 3(`_run_tree`와 러너의 겹침, 러너의 계약을 넓혀야 한다), 표준 축 Nit 6의 상수 셋(두 언어), 명세 축 Nit (b)(PR 템플릿의 계기는 닫힌 문장의 고침이다), 명세 축 Minor의 Ctrl-C(티켓 31행의 기준은 제한 시간이다. 못 보는 것에 적었다). 이유는 위 판정 줄마다 적었다.

## 검사(셀프 리뷰 뒤)

- `uv run ruff check`·`uv run ruff format --check`(고친 파이썬 파일 셋), `uv run pyright tests/test_widget_llm.py`: 초록.
- `uv run pytest -q tests/test_widget_llm.py tests/test_conftest.py`: `10 passed, 1 deselected`. 자식을 셸 스크립트로 바꾼 뒤 `tests/test_widget_llm.py`만 다시 쳐 `3 passed, 1 deselected`이고, 제한 시간 시험은 홀로 `6.47s call`이었다.
- `uv run python tools/mutate.py --check .scratch/web-widget/probes/widget_llm_mutations.toml`: 변이 8 모두 원문이 한 번씩 있다.
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/web-widget/probes/widget_llm_mutations.toml 5`: 기준선 `1 passed, 3 deselected in 52.68s`, 변이 `1 failed`, 도구가 기대대로로 판정했다. 기준선이 홀로 친 7.28초보다 길었던 까닭은 가르지 않았다(같은 때 다른 세션이 돌았을 수 있다는 어림이다).
- `uv run --env-file ../../../.env pytest -m llm_widget`: `1 passed, 5597 deselected in 91.41s (0:01:31)`. 끝 줄은 `LLM 토큰 합계 6,555(입력 6,483, 출력 72). 트레이스 1개, 모델 호출 2건.`이었다. 리포트 훑기를 `_objects`로 모은 뒤의 실행이다.
- `uv run python tools/canary.py --control-commit 148652ef .scratch/web-widget/probes/canary/claude_md_llm_widget.toml <스크래치>`(claude 2.1.302): `통과 4 · 실패 0`. 실험군은 "위젯, api-client의 위젯 몫, 서버의 최종 사용자 경로와 항목의 투영을 건드렸으면 위젯의 실제 모델 e2e인 `-m llm_widget`도 친다."를, 대조군은 옛 문장을 옮겼다. `--shape`도 통과.
- `uv run --env-file ../../../.env pytest -m llm`: `7 passed, 5591 deselected in 246.50s (0:04:06)`. 끝 줄은 `LLM 토큰 합계 47,811(입력 46,822, 출력 989). 트레이스 10개, 모델 호출 20건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.`였다. 돈 파일은 `tests/core/test_model.py`(1)와 `tests/test_main.py`(6)이고 `tests/test_widget_llm.py`는 들지 않았다(티켓 44행).
- `uv run ruff check .`: `All checks passed!`. `uv run ruff format --check .`: `1047 files already formatted`.
- `pnpm -C web/apps/widget exec playwright test`(위젯 e2e 파일의 주석을 고친 뒤): `6 passed (53.1s)`, 여섯 모두 `[chromium]`.
- `uv run python tools/sibling_overlap.py`: 번호 겹침 없음. 형제 워크트리 `10-widget-element-embed`가 `web/apps/widget/e2e/stack.ts`를 함께 고쳐, 나중에 병합하는 쪽에서 글자 충돌 후보다.
- 손으로 치는 다섯(pytest, 린트 둘, pyright, 경계, web)은 커밋의 pre-commit 결과로 갈음한다. 결과는 커밋 뒤 아래에 적는다.
- 첫 커밋 시도는 pre-commit의 `mutation tables`(`tools/mutate.py --staged`)에서 막혔다. `.scratch/harness/probes/llm_tokens_mutations.toml`의 "llm 마커를 보지 않는다"가 원문으로 든 `if item.get_closest_marker("llm") is None:`을 이 브랜치가 두 마커 판정으로 바꿨고, 그 변이의 `-k 돌지_않으면`이 고르던 시험 이름도 바꿨다. 같은 시도에서 다른 검사(ruff 둘, 병렬 검사 열, 마크다운 표, 줄 구분 문자, 카나리아 모양, 헌법 판, 인용)는 모두 Passed였다. 원문을 새 판정 줄로, `-k`를 `두_LLM_마커를_돌리지_않고`로 옮기고 머리와 README 행에 `-m llm_widget`을 더했다. `--check`는 변이 12 모두 원문이 한 번씩 있었고, `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/llm_tokens_mutations.toml 1`은 기준선 `1 passed, 6 deselected in 53.44s`, 변이 `1 failed`로 기대대로였다. 빨개진 까닭은 코드를 읽은 것이다(`if False:`면 마커 없는 시험도 세어 합계 줄이 찍히고, 마지막 단언 `"LLM 토큰 합계" not in`이 빨개진다). 셀프 리뷰 두 축과 일지 "한 것"의 잔존 grep이 이 표를 보지 못했다. 표가 든 것은 바뀐 줄의 옛 글자였고, 그것을 찾는 것은 pre-commit의 이 검사다.
- 둘째 커밋 시도(`b29b6094`): pre-commit이 모두 Passed였다. 병렬 검사 열(`parallel-checks` 405.72s) 가운데 pytest 405.2s, web-verify 295.0s, run-hooks 86.4s, pyright 45.3s, pyright-linux 43.5s였고, 변이 표 원문 확인과 카나리아 모양, 헌법 판, 커밋 메시지도 Passed였다. 인용 대조는 경고 3건이었다. 둘은 이 일지의 87·97행(옛 문장 인용)이라 아래 PR 직전 리뷰 반영에서 원문 그대로 고치고 판을 밝혔고, 하나는 `docs/constitution/README.md` 11행이 긴 한 줄이라 그 줄의 옛 인용까지 더한 줄로 잡힌 것이다. 손으로 치는 다섯은 이 결과로 갈음한다.

## PR 직전 리뷰

CodeRabbit CLI는 좌석이 없어 대체 둘을 나란히 돌렸다(`docs/constitution/operations.md` 리뷰 파이프라인 2). 기준 `148652ef`, 범위는 커밋 `b29b6094` 하나다. `origin/main`이 `148652ef`에서 움직이지 않아(`git fetch` 뒤) 합칠 것이 없었다.

보안(`/security-review`, 식별 서브태스크 하나): 후보 0이라 거르기 서브태스크는 띄우지 않았다. 따라간 길은 `.env` 읽기 훅(안내 문구만 바뀌었다), `ci.yml`(머리 주석만 바뀌었고 `pull_request`·`contents: read`이며 `e2e-widget`이 `AGENT_OS_WIDGET_LLM`을 주지 않아 프로젝트 `llm`이 서지 않는다), 키의 길(pytest → pnpm → Playwright → serve. 인자·단언 메시지·주석·리포트에 실리지 않는다), Next 빌드 환경(`next.config.ts`가 클라이언트에 넘기는 것은 두 값이고 `NEXT_PUBLIC_*`가 없다), pnpm 인자의 cmd.exe 다시 읽기(고정 글자), `copyRepoPlugins`와 `siteToml`이다.

버그·성능(`bug-perf-review`, 호출 40): 밀 주장 열둘 가운데 여덟(1·2·3·4·5·6·8·9)이 맞고 7은 오탐, 10·11·12는 일부만 봤다. 지적과 판정:

- Minor(유효): `tests/test_widget_llm.py`의 실제 모델 시험 독스트링 "준비가 띄운 프로세스의 출력은 끝에 `web/apps/widget/test-results/` 에 남는다"가 제한 시간 갈래에서 거짓이다. 그 로그는 준비의 정리(`e2e/stack.ts`의 teardown)가 쓰고, `kill_tree`로 끊으면 정리가 돌지 않는다. → 고침. 새 문장 둘: 시험 독스트링 "끝까지 돈 실행이면 준비가 띄운 프로세스의 출력이 `web/apps/widget/test-results/` 에 남는다(제한 시간에 끊긴 실행은 머리 독스트링의 못 보는 것)." 머리 "못 보는 것" "제한 시간에 끊으면 … 그 임시 폴더(`agent-os-widget-e2e-*`)가 남고, serve·Next 의 출력도 `test-results/` 에 쓰이지 않을 것이다(정리가 쓴다). 그때 실패 메시지에 실리는 것은 Playwright 가 표준 출력에 낸 것뿐이다. … 셋 다 코드를 읽은 것이고 재지 않았다." `LOGS`가 `join(APP, "test-results")`이고 쓰기가 teardown 안에만 있는 것을 `stack.ts`에서 열어 봤다. 출력을 파일에 이어 쓰게 바꾸는 안은 CI의 `e2e-widget`이 함께 쓰는 준비를 고쳐야 해 이 티켓 밖으로 둔다.
- Minor(보류 → 오탐): 모델 없는 시험 셋이 86.81초. → 손으로 쳐 봤다. `uv run pytest tests/test_widget_llm.py -q -p no:cacheprovider --durations=5`가 `3 passed, 1 deselected in 66.55s`였고 시험 본문은 제한 시간 시험 6.60s와 나머지 0.09s 이하였다. 같은 시험(`-k 끝난_명령의`) 하나만 친 두 번이 57.76초와 0.83초로 갈렸고 그 본문은 0.06초였다. 모으기만 친 것(`--collect-only`)은 0.71초, `tests/test_calc_plugin.py`는 1.52초였다. 시험 코드가 늦은 것이 아니다. 늦은 회차의 원인(기계 부하, 첫 실행의 비용)은 가르지 않았다(어림이다).
- Nit(보류 → 유효): 커밋 메시지 "키 확인 단언이 실패하면 pytest 가 os.environ 전체를 찍는" 관례의 "전체". → 스크래치 스크립트(커밋하지 않았다)로 봤다. 그 탐침이 `os.environ`을 가짜 값 200개(`FAKE_000`~`FAKE_199`)로 바꾼 뒤 같은 꼴의 단언을 실패시켰다(pytest 9.1.1, 설정 파일 없음. 저장소의 `addopts`에도 출력 길이를 바꾸는 선택이 없다). 첫 판은 표지를 첫 값과 마지막 값으로 골라 기본 출력에 둘 다 있는 것을 "전체"로 읽었는데, 기본 출력은 가운데를 `...`로 줄여 앞뒤를 남기는 꼴이라 그 표지로는 가를 수 없었다. 가운데 값 `FAKE_100`으로 다시 보니 기본 출력에는 0번, `-vv`에는 4번이었다. 기본은 앞뒤만, `-vv`면 전체다(위 변이 절의 "기본은 잘리고 `-vv`면 다 찍힌다"와 같다). 커밋 메시지는 고치지 않고(이미 커밋했다) PR 본문의 남긴 위험에 바른 꼴로 적는다. 앞뒤만 찍혀도 그 자리에 든 다른 비밀이 실릴 수 있다는 어림이라 후속 후보의 취지는 그대로다.
- Nit(유효): `.claude/rules/http.md` 테스트 줄의 "모델을 부르지 않는 두 e2e(… 위젯 `web/apps/widget/e2e/`)"인데 그 폴더에 실제 모델을 부르는 `calc.llm.ts`가 있다. → 고침("위젯 `web/apps/widget/e2e/`의 Playwright 프로젝트 `chromium`"). 바뀐 rules라 카나리아 `http_rule_llm_widget.toml`을 커밋하기 전의 작업 트리로 다시 돌려 `통과 4 · 실패 0`이었다(claude 2.1.302. 실험군은 그 나열의 마지막 항목을 옮기고 대조군은 "없음"). 명세의 최신 결과 줄에 더했고 `--shape`도 통과했다.
- 밀 주장 10·11: 10의 카나리아 둘은 이 세션이 셀프 리뷰 뒤(`claude_md_llm_widget.toml`)와 위 반영 뒤(`http_rule_llm_widget.toml`)에 다시 돌렸다. 11에서 리뷰가 보지 못한 `tests/tools/test_llm_tokens.py`는 이 브랜치가 머리 독스트링 한 줄만 바꿔, 변이 표의 `-k` 조각이 고르는 시험 이름이 그대로다(`git diff 148652ef HEAD`).
- 오탐 여섯(잘린 리포트의 `json.loads`, 화면 출력의 공백, 대화 영역의 `alert`, Windows의 `start_new_session`, `pnpm.CMD`를 띄우는 길, vitest가 `playwright.config.test.ts`를 고르는지)은 리뷰가 근거를 적은 대로 둔다. 마지막 것은 셀프 리뷰의 명세 축이 `node` 프로젝트에서 3 통과로 확인했다.

## 회고

후보 아홉, 승인 셋(새 행 하나, 회차 둘), 기각 여섯, 넘김 없음. 심각도 순이다.

1. **승인(고침, 새 행 463, 1회차).** LLM 시험의 키 확인 `assert "ANTHROPIC_API_KEY" in os.environ, …` 여덟 곳이 실패하면 pytest 가 `os.environ`의 repr을 찍는다(위 변이 절과 PR 직전 리뷰 절의 스크래치 스크립트). 사건: 앞 세션의 키 없는 실행이 그 출력을 냈다. 층: 시험 코드를 고친다(키 확인을 `pytest.fail`로 실패하는 함수 하나로 모은다). 되돌림: PR 하나. 이 티켓 밖의 두 파일과 `-m llm` 재실행이 들어, 이 PR에 싣지 않고 대기열에 둔다.
2. **승인(회차, 420의 6회차).** 새 마커가 거짓으로 만든 닫힌 문장 셋(`tests/test_main.py` 독스트링 둘, `.scratch/web-widget/probes/pnpm_spawn.py` 독스트링)을 구현의 잔존 grep이 놓쳐 셀프 리뷰가 잡았다. `CLAUDE.md` 작업 규약 4(구현 때 실리는 지침)를 어긴 것이다. 셀프 리뷰가 둔 `.claude/rules/http.md` 괄호를 PR 직전 리뷰가 다시 짚은 것도 같은 낱말을 놓친 일이라 이 회차에 함께 센다.
3. **승인(회차, 367의 3회차).** 이 세션의 스크래치 탐침이 "전체를 찍는가"의 표지를 첫 값과 마지막 값으로 골라, 가운데를 `...`로 줄인 기본 출력도 "전체"로 읽고 일지에 적었다. 회고를 쓰려고 일지 변이 절을 다시 읽다가 어긋남을 보고 가운데 값으로 다시 봤다. `.claude/rules/probes.md` 첫 항목(표지는 재려는 상황에서만 나는 문구)을 어긴 것이고, 스크래치 훅이 그 규칙을 알린 뒤였다. 367이 처방한 문장(고친 판의 표지는 고치기 전 판에서 나지 않는 관찰)과 같은 꼴이라 그 행에 세고, 행의 "어디로"에 3회차가 일반 조항을 요구한다고 덧붙였다. 367은 3회차가 되어 chore 계기다.
4. **기각.** 변이 표 `llm_tokens_mutations.toml`의 원문이 바뀐 코드 줄을 들어 첫 커밋이 막혔다. pre-commit의 `tools/mutate.py --staged`(대기열 312의 고침)가 그 자리에서 막았다. pre-commit은 실패한 훅 뒤에도 나머지를 다 돌아, 그 훅을 앞으로 옮겨도 기다린 시간은 줄지 않는다.
5. **기각.** 실제 모델 시험 독스트링의 "출력은 끝에 남는다"가 제한 시간 갈래에서 거짓이었다. `code-review` 두 브리프의 주장 검증 1(닫힌 주장)이 잡도록 둔 것을 PR 직전 리뷰가 잡았다. 검사로 옮길 수 없고 새 판단 기준도 아니다.
6. **기각.** 셀프 리뷰가 Nit(`http.md` 괄호)을 두기로 한 판단을 PR 직전 리뷰가 뒤집었다(그 문장의 잔존은 2에 셌다). 든 값은 카나리아 한 번이고 PR을 열기 전이라 푸시가 더 들지 않았다. 리뷰 층이 제 몫을 했다.
7. **기각.** 커밋 메시지의 "os.environ 전체를 찍는"이 일지 변이 절("기본은 잘리고")과 어긋났다. PR 직전 리뷰가 보류로 짚었고 PR 본문에서 바로잡는다. 리뷰가 잡도록 둔 기준이다.
8. **기각.** PR 직전 리뷰가 본 86.81초는 시험 코드의 결함이 아니었다(같은 시험 하나가 57.76초와 0.83초로 갈렸다). 사건이 비용이 아니다.
9. **기각.** 앱의 워크트리 가드가 일지에 덧붙이는 Bash heredoc을, 훅이 스크래치패드로 옮기는 `cd`를 막았다. 이미 있는 가드와 훅이 그 자리에서 막았고 Edit 도구와 경로 인자로 바로 쳤다.

만료: `uv run python tools/queue_open_rows.py`와 `--ref origin/main`(`git fetch origin` 뒤) 모두 만료할 행이 없었다. 새 훅·검사가 문턱을 새로 지난 것이 없어 `tools/hook_report.py`는 돌리지 않았다(420은 이미 문턱을 지났고 처방이 정해지지 않았다).

## 다음

- 이 티켓으로 web-widget의 실제 모델 e2e가 섰다. 남은 web-widget 티켓 07·10은 형제 세션이 돌고 있고(이 세션을 연 묶음), 08·09는 `ready-for-agent`다. 다음 작업은 병합 뒤 `next-session` 결정표가 정한다.
- 형제 워크트리 `10-widget-element-embed`가 `web/apps/widget/e2e/stack.ts`를 함께 고친다. 나중에 병합하는 쪽이 글자 충돌을 푼다(`tools/sibling_overlap.py`).
- 뒤로 넘긴 일: 대기열 463(키 확인 단언). 셀프 리뷰가 둔 `_run_tree`와 `tools/run_checks.py`의 겹침(러너의 계약을 넓혀야 한다)과, PR 직전 리뷰가 낸 "제한 시간에 끊겨도 serve·Next 로그를 남기기"(CI의 `e2e-widget`과 함께 쓰는 준비 `e2e/stack.ts`를 고쳐야 한다)는 대기열에 올리지 않았다. 사건이 비용이 되면 그때 센다.

## 인계(커밋 뒤)

PR 직전 리뷰 반영과 회고를 실은 커밋 뒤에 세션 컨텍스트가 문턱을 넘은 채(328,266 토큰) 인계 계기(`hook_handoff`, 경계 `커밋 뒤`)가 왔다. 그 커밋은 pre-commit을 모두 지났다(헌법 판은 고친 파일이 없어 Skipped). 이 세션은 앞 세션이 셀프 리뷰 직전에 넘긴 것을 이어받은 세션이고 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). 이 세션의 제목은 `feature/11-widget-real-model-e2e`였고 `feature/11-widget-real-model-e2e (인계함)`으로 바꾼다. 넘길 때의 상태:

- 커밋은 둘이고(구현, PR 직전 리뷰 반영·회고) 아직 푸시하지 않았다. PR도 없다. 이 절만 커밋하지 않았고 새 세션이 다음 커밋에 싣는다.
- 셀프 리뷰, PR 직전 리뷰(보안·버그 성능), 회고, 일지 "다음"은 마쳤다. 남은 것은 푸시, `/git-pr`로 PR 열기, `@coderabbitai review`, `tools/wait_ci.py` 대기, `/git-pr-feedback`, 워크트리 병합 길, 그 뒤 `next-session`이다.
- PR 본문의 "남긴 위험"에 키 확인 단언을 적을 때는 "기본은 `os.environ`의 앞뒤를, `-vv`면 전체를 찍는다"로 쓴다. 구현 커밋의 메시지는 "전체를 찍는"이라 틀렸다(위 PR 직전 리뷰 절). PR 체크리스트의 PR 직전 리뷰 줄은 위 "## PR 직전 리뷰"를 옮긴다.
- 이 세션이 고쳐 적은 것: PR 직전 리뷰 절의 "전체" 판정을 처음에 맞다로 적었다가, 탐침의 표지(첫 값·마지막 값)가 잘린 출력에도 남는 것을 보고 가운데 값으로 다시 봐 유효로 고쳤다(회고 3).
- 멈출 백그라운드 작업은 없다(서브에이전트 둘과 커밋은 끝났다).

인계 지시문:

```
다음 작업: .scratch/web-widget/issues/11-widget-real-model-e2e.md. 실제 모델을 부르는 위젯 e2e
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/11-widget-real-model-e2e.md
브랜치: feature/11-widget-real-model-e2e
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-13-widget-real-model-e2e.md의 "## PR 직전 리뷰", "## 회고", "## 다음", "## 인계(커밋 뒤)"
이어받을 상태: 인계: 커밋 뒤. 구현 커밋과 PR 직전 리뷰 반영·회고 커밋까지 했고 푸시하지 않았으며 PR이 없다. 셀프 리뷰, PR 직전 리뷰, 회고, 일지 "다음"은 마쳤다. 일지의 "## 인계(커밋 뒤)" 절만 커밋하지 않았다. 남은 것은 푸시와 /git-pr로 PR 열기(본문의 남긴 위험에 키 확인 단언은 "기본은 os.environ의 앞뒤를, -vv면 전체를 찍는다"로 적는다. 구현 커밋 메시지의 "전체"는 틀렸다), @coderabbitai review와 tools/wait_ci.py 대기, /git-pr-feedback, 워크트리 병합 길, 그 뒤 next-session이다. docs/journal/2026-10-24-13-widget-real-model-e2e.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 바꿨고, 멈출 백그라운드 작업은 없었으며, `git worktree unlock C:/project/agent/.claude/worktrees/11-widget-real-model-e2e`는 이미 풀렸다는 오류(`is not locked`)라 넘어갔다.

open-session을 부른다 2026-10-24T13:40:38Z

## 이어받은 세션(커밋 뒤)

인계 지시문으로 연 새 세션이 같은 워크트리에 들어와 이었다. `origin/main`은 `148652ef`에서 움직이지 않았고(`git fetch` 뒤 `git log 148652ef..origin/main`이 비었다), `tools/sibling_overlap.py`는 번호 겹침이 없었다. 위 인계 절과 이 절을 커밋한 뒤 푸시하고 PR을 연다.

PR #383을 열었다. CodeRabbit CLI는 이 PR에서도 `coderabbit auth status`가 `Seat: not assigned`였다.

## 봇 회차 1

헤드 `cfeeb3b4`에서 `tools/wait_ci.py`가 모두 통과로 끝났다(CodeRabbit `Review completed`). 두 봇 모두 첫 회차라 Minor·Nit도 지적마다 판단했다.

CodeRabbit(Critical 1, Minor 3):

- Critical: `tests/test_widget_llm.py` 199행 키 확인 단언이 실패하면 `os.environ`의 repr을 찍는다(`.coderabbit.yaml` 경로 지침의 "이벤트, 로그, 트레이스에 API 키·토큰·비밀번호가 실릴 수 있는 경로는 Critical이다."). → 고침. 이 PR이 새로 쓴 줄이라 `if … not in os.environ: pytest.fail(…)`로 바꿨다. 회고 1이 대기열 463으로 넘긴 나머지 일곱 곳(`tests/test_main.py` 여섯, `tests/core/test_model.py`)은 그대로이고, 463 행을 일곱 곳으로 고쳤다. 키 없이 친 `uv run pytest -m llm_widget -p no:cacheprovider -vv`가 `Failed: ANTHROPIC_API_KEY 가 없다. .env 를 확인한다`로 끝났고 출력에 `environ(`이 0번이었다(손으로 봤다).
- Minor: 211행 단언이 종료 코드를 보지 않는다. 시험이 통과해도 정리가 던지면 Playwright 는 0이 아닌 코드로 끝난다. → 고침. `_failures`가 종료 코드를 받아 `Playwright 가 종료 코드 {code} 로 끝났다`를 다른 기준과 함께 모은다. 어긋난 것이 하나라도 있으면 리포트의 `errors`도 싣는다. 변이 9(정리 끝에서 던지기)를 더했고 `PYTHONUTF8=1 uv run --env-file ../../../.env python tools/mutate.py .scratch/web-widget/probes/widget_llm_mutations.toml 9`가 기준선 `1 passed, 3 deselected in 71.34s`, 변이 `1 failed`로 기대대로였다(표지 `Playwright 가 종료 코드 1 로 끝났다`). 기준선의 통과가 정상 실행의 종료 코드가 0인 것도 보였다. 앞의 번호를 일지와 PR 본문이 가리켜 9는 표 끝에 두었다.
- Minor: `.scratch/harness/probes/llm_tokens_mutations.toml` 변이 1에 표지가 없다(`.claude/rules/probes.md` 첫 항목). → 고침. 변이를 손으로 넣고 친 실패 출력에서 마지막 단언의 설명 줄 `'LLM 토큰 합계' is contained here:`를 골랐고, `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/llm_tokens_mutations.toml 1`이 기대대로였다(기준선 `1 passed … in 204.83s`. 변이 9와 함께 돌아 늦었다). 나머지 열하나에 표지가 없는 것은 이 브랜치가 고치지 않은 변이라 두었다.
- Minor: 제한 시간 시험의 `_stops_growing`(표지 파일이 1초 자라지 않으면 끝난 것으로 본다) 대신 손자의 PID 를 적고 끝났는지 직접 보라. → 고치지 않는다. 그 꼴은 `.claude/rules/tests.md`가 선례로 든 `tests/tools/test_run_checks.py`의 같은 이름 함수이고, 손자가 산 채로 1초 동안 한 번도 쓰지 못해야 거짓 통과다. PID 로 보려면 윈도우에서 pid 의 생사를 보는 새 길이 든다(파이썬 `os.kill` 문서가 윈도우에서 두 콘솔 신호 밖의 값은 `TerminateProcess`로 끝낸다고 적은 것으로 기억한다. 이 세션에서 다시 열지 않았다). 두 시험을 함께 바꿔야 해 이 PR 밖이고, 거짓 통과가 사건이 되면 그때 센다. PR 코멘트에 남겼다.

claude-review(Minor 3, Nit 1, Critical·Major 0):

- Minor `_run_tree`와 러너의 겹침, Minor 두 언어의 상수 셋 → 둔다. 셀프 리뷰의 판정(위 "셀프 리뷰"의 표준 축 Minor 3·Nit 6)과 같고 PR 코멘트에 남겼다.
- Minor 키 확인 단언 → 위 CodeRabbit Critical 과 같은 자리이고 고쳤다.
- Nit 머리 독스트링은 "기준 다섯"인데 `_failures`는 "기준 셋"이다. → 고침("기준 다섯 가운데 한 바퀴의 결과인 앞의 셋"). 머리 독스트링의 첫째 기준에 종료 코드 0을 더했다.

검사: `uv run ruff check`·`ruff format --check`·`uv run pyright tests/test_widget_llm.py` 초록, `uv run pytest -q -p no:cacheprovider tests/test_widget_llm.py`가 `3 passed, 1 deselected`, 두 변이 표의 `--check`가 원문을 모두 한 번씩 찾았다. 나머지는 이 반영 커밋의 pre-commit 으로 갈음한다.
