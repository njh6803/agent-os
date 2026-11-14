# rename-portal-to-widget-preview: 용어 "질문 페이지"를 "위젯 미리보기 페이지"로 바꾼다

**What to build:** 이 저장소가 함께 내는 사이트 여럿을 담는 웹 페이지와 그 서버(`web/apps/portal/`)의 용어집 이름이 "질문 페이지"인데, 사용자가 2026-11-13 portal-login 화면 설계 세션에서 "위젯 미리보기 페이지"로 바꾸기로 했다. 이름만 바꾸는 chore다. 동작도 코드 이름도 바꾸지 않는다.

> 사용자: 명칭을 다시 하자. 질문 페이지라고 하지말고 "위젯 미리보기 페이지"라고 해. (일지 `docs/journal/2026-11-13-0426-portal-login-ui-design.md`)

이 이름은 쓰임도 바로잡는다. 이 페이지는 사이트가 자기 웹 페이지를 갖지 못했을 때 대신 쓰는 페이지가 아니다. `.scratch/pilot-portal/spec.md`의 Problem Statement가 적은 두 까닭, 곧 위젯을 붙일 사이트나 토큰을 서명할 서버가 없을 때 위젯을 보여 주고 질문해 볼 자리와, 사이트마다의 설정으로 그린 위젯을 골라 보고 질문해 볼 자리라는 뜻이다. `CONTEXT.md`의 정의는 이 뜻으로 쓴다.

사람이 이번 일을 portal-login 화면 설계 PR(#557)이 병합된 뒤 chore 브랜치 하나에서 따로 하기로 골랐다(같은 일지의 "다음"). 위젯이 로그인 상태를 직접 그리는 방향의 설계 인터뷰는 이 chore 뒤에 하므로, 그 인터뷰와 ADR은 새 이름으로 쓰인다.

**바꾸는 것.** `질문 페이지`를 `위젯 미리보기 페이지`로 바꾼다. 조사가 붙는 자리(`질문 페이지가`, `질문 페이지의`)는 끝 글자가 같아 그대로 맞고, 시험 이름과 변이 표의 `-t` 필터와 화면에 찍히는 글(시작 로그, 오류 문구)과 그것을 맞대는 시험도 같이 바뀐다. 용어집 `CONTEXT.md`를 먼저 고치고, 그다음 헌법 문서, 규칙, 지침, `README.md`, CI 설정, PR 틀, 마커 설명(`pyproject.toml`), 코드 주석과 시험, 기능 계획과 명세와 티켓과 프로브, 열린 대기열 항목이다.

**바꾸지 않는 것.**
- 코드 이름 `portal`과 경로 `/portal/`, 패키지 이름 `@agent-os/portal`, 마커 `llm_portal`, CI 잡 `e2e-portal`. 용어집의 영어 이름 `Portal`도 코드 이름이라 그대로다.
- 일지(`docs/journal/`)와 ADR 본문. 기록이라 옛 말이 남는다. ADR 색인(`docs/adr/README.md`)의 제목도 ADR 제목을 따라 그대로 둔다. 옛 말이 든 ADR마다 이력 한 줄로 이름이 바뀐 것을 알린다.
- `.scratch/<기능>/design/`의 파일. 그려서 아티팩트에 올린 화면의 목업(`*.dc.html`, `canvas.json`)은 파일마다의 sha256으로 웹 편집을 가르고(`docs/agents/issue-tracker.md` 화면 디자인 절), 시작 프롬프트는 그림을 그릴 때 보낸 글의 기록이다.
- `docs/constitution/history.md`, 일지처럼 기록인 것.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] `CONTEXT.md`의 용어 "질문 페이지(Portal)"와 "질문 페이지 설정(Portal Settings)"이 "위젯 미리보기 페이지"로 바뀌고, 정의가 위 쓰임(자기 페이지를 대신하는 곳이 아니라 위젯을 미리 보고 질문해 보는 자리)을 말한다. `_Avoid_`에서 "미리보기 페이지"를 빼고 옛 이름 "질문 페이지"를 넣는다. 그 용어를 쓰는 다른 줄도 같이 바뀐다
- [x] 위 "바꾸는 것"의 파일에서 `질문 페이지`(`질문페이지`와 줄이 바뀌며 갈라진 꼴 포함)의 잔존이 0이다. 잔존 grep은 `git grep`이고 일지, ADR 본문과 색인, `.scratch/*/design/`과 이 티켓(옛 이름을 적는 것이 일이라 커밋되면 걸린다)을 뺀다. 이 grep(`git grep -IlE "질문 ?페이지"`)은 손으로 쳤다. 줄이 바뀌며 갈라진 꼴(`질문` 끝에서 줄을 바꾸고 다음 줄의 `//`·`*`·`#`·`>` 머리표 뒤에 `페이지`가 오는 꼴)과 밑줄 꼴(`질문_페이지`)은 grep으로는 못 잡아, 추적 파일 전부를 파이썬 정규식으로 훑어 두 가지를 더 찾아 고쳤다(`web/apps/portal/browser/portal.ts`, `web/apps/widget/tools/start.ts`의 주석에서 갈라진 꼴 둘, `tests/test_portal_llm.py`의 시험 함수 이름 밑줄 꼴). 고친 뒤 남은 것은 `.scratch/*/design/`의 기록 파일 다섯(`pilot-portal/design/` 넷, `portal-login/design/screens-prompt.md`)과 `CONTEXT.md`의 `_Avoid_`뿐이다
- [x] 화면에 찍히는 글(포털의 시작 로그 `diagnostics.ts`, 오류 문구 `start.ts`·`page.ts`)을 바꾸면서 그 글을 맞대는 시험(`diagnostics.test.ts`, `start.spawn.test.ts`, e2e의 준비 `stack.ts`)도 같은 글로 바꿨다. `pnpm -C web verify`(러너 `web-verify`)와 `pnpm -C web/apps/portal exec playwright test`(41건)가 초록이다
- [x] 변이 표의 시험 이름 필터(`-t "질문 페이지…"`)가 바뀐 시험 이름과 맞는다. `PYTHONUTF8=1 uv run python tools/mutate.py --check`로 `pilot-portal`의 변이 표 셋을 대 보니 모든 변이의 원문이 한 번씩 있다. 이 확인은 원문만 본다. `-t` 필터와 시험 이름이 맞는지는 같은 치환으로 양쪽을 함께 바꿨다는 것으로 갈음하고 변이를 다시 돌려 보지는 않았다
- [x] 카나리아 명세(`.scratch/web-widget/probes/canary/http_rule_llm_widget.toml`, `tests_rule_llm_widget.toml`)의 기대 문장이 바뀐 규칙 문장과 맞는다. `tools/canary.py --shape`와 `--preflight`가 둘 다 통과했다. `claude -p`는 돌리지 않았다(문구만 고친 명세를 사전 확인으로 갈음하는 규약, `docs/constitution/operations.md`의 카나리아 항목)
- [x] 옛 이름이 든 ADR 여덟(0046, 0048, 0050, 0051, 0053, 0056, 0059, 0060)마다 이력 한 항목을 달았다. 본문과 색인은 그대로다
- [x] `.scratch/plan.md`를 `uv run python tools/plan_table.py`로 다시 만들어 같은 커밋에 실었다
- [x] 글자 수가 늘어(6자에서 11자) 100칸을 넘은 파이썬 줄(`.scratch/pilot-portal/probes/node_ts_workspace.py`, `src/agent_os/main.py`, `tests/test_calc_plugin.py`, `tests/test_conftest.py`, `tests/test_portal_llm.py`, `tools/mutate.py`)의 줄바꿈을 고쳐 `ruff check`와 `ruff format --check`가 초록이다
- [x] 검증 명령이 모두 초록이다(`uv run python tools/run_checks.py`가 종료 0이고 `pytest`·`web-verify`·`pyright`·`lint-imports`·`check-instructions`를 포함한다. `ruff` 둘과 `prettier`는 따로 쳤다. 커밋 직전의 pre-commit이 갈음하는 것은 그 결과로 갈음한다). 갈음하지 못하는 것: 실제 모델을 부르는 `-m llm_portal`은 치지 않았다. 이 PR이 포털 e2e 코드의 주석과 문구만 바꾸고 그 시험은 모델 호출 경로를 건드리지 않아서다. 사진 비교는 포털에 없고 이 PR은 위젯·관리 화면·디자인 시스템 패키지를 건드리지 않았다
