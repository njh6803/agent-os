# 2026-11-10 (19:58) 실제 모델 시험: 질문 페이지에서 고지를 확인하고 calc에 질문한다 (pilot-portal 09)

세션 제목 `feature/09-real-model-calc-on-portal`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/09-real-model-calc-on-portal`. 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/pilot-portal/issues/09-real-model-calc-on-portal.md
>
> 다음 작업: .scratch/pilot-portal/issues/09-real-model-calc-on-portal.md. 실제 모델 시험: 질문 페이지에서 고지를 확인하고 calc에 질문하면 답이 서고 익명 주체의 트레이스가 남는다
> 다음 단계: 구현
> 이번 요청 범위: PR과 병합까지

이 세션에서 사용자가 더한 말은 없었다. 08(`08-site-switching-and-assurance-modes`)과 나란히 도는 둘째 지시문이다. 질문 페이지 e2e의 준비를 둘 다 고칠 수 있어 나중에 병합하는 쪽이 main을 받아 맞춘다.

## 한 일 (커밋하지 않은 작업 트리)

- 마커 `llm_portal`: `pyproject.toml`의 `markers`와 `addopts`의 `-m`에 더했고, `tests/conftest.py`의 `_LLM_MARKERS`에 더했다. `tests/test_conftest.py`에 `llm_portal` 사례(`test_llm_portal_시험이_tmp_path_에_남긴_트레이스도_합계에_든다`)를 더하고 기본 실행 사례를 세 마커로 넓혔다. 구현 전에 3건이 빨갛다가(`test_deselect_…`, 새 사례, 기본 실행 사례) 구현 뒤 초록이어야 한다. 이 세션은 초록을 다시 돌려 보지 않았다.
- 래퍼 `tests/test_portal_llm.py`: 위젯 래퍼(`tests/test_widget_llm.py`)와 같은 모양이다. 위젯 래퍼의 변이 표(`.scratch/web-widget/probes/widget_llm_mutations.toml`)가 그 파일의 글자를 겨누어, 공통 도우미를 따로 빼지 않고 같은 코드를 따로 두었다. 위젯 래퍼의 제한 시간·pnpm 부재 시험 셋은 옮기지 않았다(독스트링에 그렇게 적었다).
- 질문 페이지 e2e: `e2e/env.ts`에 `LLM_ENV`(`AGENT_OS_PORTAL_LLM`)·`TRACES_ENV`(`AGENT_OS_PORTAL_TRACES`), `playwright.config.ts`에 `LLM_ENV`가 `1`일 때만 서는 프로젝트 `llm`(`**/*.llm.ts`, 180초), `playwright.config.test.ts`(프로젝트 목록 시험 셋. 구현 전에 한 건이 빨갛다가 초록), `e2e/stack.ts`의 LLM 모드(저장소 플러그인 루트 복사, 첫 사이트의 설정 에이전트와 사이트 파일 에이전트에 `calc`), `e2e/calc.llm.ts`(사례 하나. 주체는 여기서 `발급자|anon-<32자리 16진수>`로 본다).
- 문서: `CLAUDE.md`(검증 명령의 테스트 줄에 `-m llm_portal`과 치는 때, 갈음되지 않는 것 줄), `.claude/rules/tests.md`, `.claude/rules/http.md`, `docs/constitution/operations.md`(LLM 테스트 절에 `llm_portal` 문단), 헌법 판 3.0.82 → 3.0.83(`docs/constitution/README.md`. `sibling_overlap.py`가 겹침 없음을 확인했다), `.github/workflows/ci.yml` 머리 주석, `.github/PULL_REQUEST_TEMPLATE.md`, `.coderabbit.yaml`, 도구 독스트링(`tools/hook_env_read.py`의 거부 문구, `tools/mutate.py`, `tools/llm_tokens.py`)과 시험 독스트링(`tests/test_main.py`, `tests/test_calc_plugin.py`, `tests/tools/test_llm_tokens.py`), `web/packages/e2e-stack/src/plugins.ts`의 주석.
- 티켓 09의 `Status:`를 `in-progress`로 바꿨다(첫 편집).

## 결정

- 에이전트 이름을 첫 사이트만 `firstAgent`로 갈랐다(`agentOf`). 사이트 파일의 그 사이트 에이전트는 `[echo, calc]`(중복 없이), 나머지 사이트는 `[echo]`다. 기본 모드는 이전과 같다.
- 사례의 `?site=` 없는 열기는 `/portal/`로 연다(`e2e/acknowledge.e2e.ts`는 `?site=`를 쓴다).
- 위젯 래퍼와의 중복을 허용했다. 이유는 위의 변이 표다.

## 확인한 것 (이 세션이 출력을 읽은 것)

- `uv run --env-file ../../../.env pytest -m llm_portal`: `1 passed, 6878 deselected in 146.98s`, `LLM 토큰 합계 6,937(입력 6,865, 출력 72). 트레이스 1개, 모델 호출 2건`. (로그: 스크래치패드 `portal_llm_1.log`)
- 빨강 먼저: `e2e/calc.llm.ts`의 `anon-`을 `anon2-`로 틀리게 둔 판은 `Expected pattern: /^anon2-[0-9a-f]{32}$/u`, `Received string: "anon-8f798e9db21dd320a356387447c97eb6"`로 빨개졌고 래퍼가 `프로젝트 llm 이 통과 1, 건너뜀 0 이 아니다`를 냈다. 되돌렸다(`anon-`). (로그: `portal_llm_red.log`)
- 질문 페이지 e2e 기본 프로젝트: `18 passed (29.2s)`. LLM 모드 변경에 흔들리지 않았다.
- `uv run ruff check .`와 `ruff format --check .`: 통과(이 세션의 마지막 편집 전에 쳤다. 그 뒤 편집은 문서와 주석, 카나리아 명세뿐이다).
- 카나리아: `tests_rule_llm_widget.toml` 통과 4, `http_rule_llm_widget.toml` 통과 4. 둘 다 이 세션이 기대 문장을 새 문장으로 고쳤고 "최신 결과" 줄을 적었다. 둘 다 커밋 전 작업 트리로 돌렸다.
- `uv run python tools/sibling_overlap.py`: 번호 겹침 없음(헌법 3.0.83). 카나리아 알림 둘(`tests.md`, `http.md`의 카나리아)은 위 두 명세를 돌려 처리했다.

## 이어받은 세션 (셀프 리뷰와 마무리)

세션 제목 `feature/09-real-model-calc-on-portal`. 지시문의 범위는 "PR과 병합까지"다. 이 세션이 사용자에게 더한 말은 없다.

- CLAUDE.md 카나리아(`claude_md_llm_widget.toml`): `통과 4 · 실패 0 · "없음" 섞인 통과 0`(실험군 3/3 커밋 2a8bd35d 작업 트리, 대조군 1/1 커밋 148652ef). 머리의 "최신 결과" 줄을 적었다. 이 세션이 러너 출력(스크래치패드 `canary_claude_md.log`)을 읽었다.
- 셀프 리뷰 `/code-review`, base `2a8bd35d`, 추적 파일 25개 변경에 미추적 넷(`tests/test_portal_llm.py`, `e2e/calc.llm.ts`, `playwright.config.test.ts`, 이 일지), 커밋 0. 표준 축은 sonnet·high, 명세 축은 세션 모델.
  - 명세 축: 요구 누락 없음. 지적 하나, `tests/conftest.py` 6행 머리 독스트링의 "두 LLM 마커를 뺀다"가 셋으로 안 바뀐 잔존(`llm_widget` grep으로는 안 걸리고 "두 마커" 계열 grep으로만 걸린다). 고쳤다.
  - 표준 축 Major: `.scratch/web-widget/probes/widget_llm_mutations.toml` 의 변이 "기본 실행이 llm 만 빼면 …"의 `old` 가 옛 `addopts` 줄이라 `tools/mutate.py --check` 가 `원문이 0번` 으로 빨갛다. 이 세션이 `--check` 로 같은 빨강을 다시 봤다. 새 `addopts` 로 `old` 를, 변이를 `not llm and not llm_portal` 로 고쳤고(이름도 "기본 실행이 llm_widget 을 빼먹으면 그 시험이 돌아 빨갛다"), `--check` 초록(변이 9 모두 원문 한 번씩), 그 변이 8번만 돌려 `기대 빨강, 결과 빨강` 을 봤다.
  - 표준 축 Minor: `tests/test_conftest.py` 의 기본 실행 시험이 `WIDGET_TRACED` 에서 `PORTAL_TRACED` 로 바뀌며 `llm` 마커 사례가 빠져 `addopts` 의 `not llm` 만 지워도 초록일 수 있었다. 이 세션이 두 소스를 대 보아 `llm` 사례가 없음을 확인했고, `ALL_MARKERS_TRACED` 로 세 마커를 모두 붙인 시험 소스를 두어 기대를 `1 passed, 3 deselected` 로 고쳤다. 위젯 변이 8번의 `expect_output` 도 같은 문구로 맞췄다.
  - 표준 축 Minor: `web/apps/portal/e2e/sites.ts` 의 "모든 사이트가 여는 픽스처 에이전트"는 실제 모델 모드에서 거짓이다(첫 사이트가 `calc`). 두 문장에 "기본 모드에서"를 붙였다.
  - 표준 축 Minor: `tests/test_portal_llm.py` 독스트링의 제한 시간·pnpm 부재 시험을 위젯 파일에서 잰다는 말은 위젯 사본만 재는 시험이라 이 사본이 갈라져도 못 잡는다는 말로 고쳤다. 위젯 독스트링의 "코드를 읽은 것이고 재지 않았다"를 이 사본의 "못 보는 것"에도 옮겼다.
  - 표준 축 Nit: `playwright.config.ts` 의 `chromium` 상수가 프로젝트 이름과 같아 `desktopChrome` 으로 바꿨다.
  - 남김: 표준 축이 `_run_tree`·`_pnpm`·`_read_report`·`_failures`·`_read_trace` 약 150줄의 복제(Duplicated Code)를 판단 항목으로 냈다. 이 세션은 복제를 유지한다. 근거는 위젯 변이 표(`file = "tests/test_widget_llm.py"` 를 겨누는 변이 둘)가 그 파일의 글자를 겨누는 것이다(Grep 으로 그 줄 둘을 셌다). 또 티켓 09 가 `tests/test_widget_llm.py` 와 같은 모양이라고 적으며 도우미 추출을 요구하지 않는다. 도우미로 빼는 일은 위젯 변이 표를 다시 쓰는 별도 일이다.
  - 표준 축의 `.scratch/harness/probes/README.md` 108행과 `llm_tokens_mutations.toml` 머리의 "-m llm 과 -m llm_widget"은 프로브 기록이라 두었다. 그 변이 표는 `--check` 에서 12 모두 원문이 있다.
- 반영 뒤 다시 돌린 것(이 세션이 출력을 읽었다):
  - `uv run --env-file ../../../.env pytest -m llm_portal -q`: `1 passed, 6878 deselected in 124.26s`, `LLM 토큰 합계 6,937(입력 6,865, 출력 72). 트레이스 1개, 모델 호출 2건`.
  - `pnpm -C web/apps/portal exec playwright test`: `18 passed (33.7s)`.
  - `uv run ruff check .`: `All checks passed!`, `uv run ruff format --check .`: `2018 files already formatted`.
  - `uv run python tools/run_checks.py`: pytest 통과(434.3s), pyright·pyright-linux·lint-imports·check-instructions·check-type-escapes·run-hooks 통과, `web-verify` 만 실패했다. 까닭은 eslint 의 `playwright.config.test.ts was not found by the project service`(미추적 새 파일이 `web/apps/portal/tsconfig.json` 의 `include` 에 없었다). `include` 에 그 파일을 더하고 `pnpm -C web verify` 를 다시 쳐 통과(Vitest `119 passed`, `1849 passed | 1 skipped`)를 보았다. 그 파일 하나만 친 `vitest run apps/portal/playwright.config.test.ts` 도 3건 통과.
- 티켓 09 의 체크박스를 모두 `[x]`, `Status:` 를 `done` 으로 바꿨다. `uv run python tools/plan_table.py` 는 `.scratch/plan.md` 를 바꾸지 않았다(파일 차이 없음). 08 이 `ready-for-agent` 라 기능 계획에 `**끝:**` 줄은 적지 않았다.
- 디자인 시스템 훅 알림(`sync-design-system 확인`): 이 세션이 고친 `web/apps/portal` 파일은 e2e 설정·시험·준비뿐이고 화면 코드(컴포넌트, 스타일)가 아니라서 부르지 않았다.

## 남은 일 (처음 인계 때의 목록)

아래 1~5는 위 "이어받은 세션"에서 끝냈다(커밋은 이 일지와 함께). 남은 것은 6 뿐이고 이 세션이 이어서 한다.

1. `.scratch/web-widget/probes/canary/claude_md_llm_widget.toml`: `CLAUDE.md` 갈래다. 이 세션이 기대 셋째 줄을 `-m llm·-m llm_widget·-m llm_portal·e2e·사진 비교`로 고쳤다. 다음 명령으로 돌려 통과 4면 머리의 "최신 결과" 줄을 적는다. `uv run python tools/canary.py --control-commit 148652ef .scratch/web-widget/probes/canary/claude_md_llm_widget.toml <출력 디렉터리>`. 대조군은 옛 판이라 새 기대로는 그 갈래가 "없음"이 된다. 러너 출력으로 판단한다.
2. 셀프 리뷰 `/code-review`. 이 세션이 스킬을 불렀지만 서브에이전트를 띄우기 전에 인계했다. 범위는 `origin/main`(`2a8bd35d`) 이후의 작업 트리 전체와 미추적 파일 셋(`tests/test_portal_llm.py`, `web/apps/portal/e2e/calc.llm.ts`, `web/apps/portal/playwright.config.test.ts`).
3. 바꾼 rules(`tests.md`, `http.md`)가 새 세션에서 Read로 실리는지 본다(티켓 문서 절 둘째 체크박스). 위 카나리아 둘이 그 확인이다. 이 세션은 카나리아를 통과로 보았으므로, 새 세션은 그 결과를 체크박스의 근거로 옮겨도 된다.
4. 티켓 09의 체크박스를 확인한 것만큼 `[x]`로 바꾸고 `Status:`를 `done`으로 바꾼 뒤 `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`까지 싣는다. 08이 아직 열려 있으면 기능 계획 `**끝:**` 줄은 쓰지 않는다. 08이 이미 병합됐으면 이 티켓이 마지막이므로 `.scratch/pilot-portal/plan.md`에 `**끝:** YYYY-MM-DD`를 적는다(그 커밋의 로컬 날짜).
5. 전체 검증 `uv run python tools/run_checks.py`(백그라운드), 그 뒤 커밋. 이 세션은 전체 검증을 돌리지 않았다. 질문 페이지 e2e와 `-m llm_portal`은 위처럼 돌렸다.
6. 푸시와 PR, 봇 회차, 병합(범위가 "PR과 병합까지"이므로 `merge.md`).

## 이 세션의 제목

`feature/09-real-model-calc-on-portal` (인계 때 `(인계함)`을 붙인다)

## 인계

첫 인계: 컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 셀프 리뷰 직전에 와서 `인계: 셀프 리뷰 직전`으로 넘겼다. 이 세션은 `/code-review`의 서브에이전트를 띄우지 않았다. 지시문은 스크래치패드 `directive-09.txt`에 있다. 잠금을 풀었다(`git worktree unlock`).

open-session을 부른다 2026-11-10T10:59:37Z

둘째 인계(`인계: 커밋 뒤`): 이어받은 세션이 셀프 리뷰, 검증, 티켓 done까지 마치고 커밋 `0463e24e`를 만들었다. pre-commit 통과(출력 끝 `32 files changed`). 인용 대조 경고 둘은 일지의 따옴표를 떼어 처리했고 그 편집은 커밋하지 않았다. 남은 일은 푸시, PR 열기, 봇 회차, 병합(`merge.md`)이다. 컨텍스트가 인계 문턱을 넘은 채 커밋 뒤에 와서 넘긴다. 이 세션의 제목은 `feature/09-real-model-calc-on-portal (인계함)`으로 바꾼다.

open-session을 부른다 2026-11-10T11:41:50Z

열기가 폴더 오류로 멈췄다(2026-11-10T11:42Z). 새 세션 화면의 폴더가 C:\projectag-engine 이었고 보내지 않았다. 지시문은 새 세션 화면에 남아 있어 사람이 폴더와 모델을 맞춰 보낸다. 지시문 파일은 스크래치패드 directive-09-b.txt다. 같은 파일로 다시 돌리지 않는다.

다시 열기(사용자 요청, 2026-11-10 21:25 로컬)는 sent= 로 끝났다. 폴더 C:\projectgent, 모델 Sonnet 5.5 / high. 앞의 폴더 오류 줄은 이 줄로 풀렸다.

## PR 직전 리뷰 (coderabbit-review 서브에이전트)

CodeRabbit CLI 0.7.5(`Plan: Free`, `Seat: not assigned`)가 `coderabbit review --agent --include-untracked --base origin/main`으로 파일 32개를 끝까지 리뷰해 지적 0건을 냈다. 이 세션은 서브에이전트의 보고를 읽었고 CLI를 직접 치지 않았다. 보고가 코드를 읽고 덧붙인 관찰 둘은 아래처럼 판정해 둘 다 보류했다.

- Minor, `web/apps/portal/e2e/stack.ts`의 질문 페이지 프로세스가 `process.env`를 통째로 물려받아 실제 모델 모드에서 `ANTHROPIC_API_KEY`를 받는다. 위젯 e2e의 준비와 같은 모양을 따른 것이고 키가 로그나 트레이스로 새는 경로는 서브에이전트가 읽은 범위에서 찾지 못했다. 질문 페이지와 위젯의 자식 환경을 함께 다듬는 별도 일이라 뒤로 넘긴다.
- Nit, `tests/test_portal_llm.py`의 키 확인(`"ANTHROPIC_API_KEY" not in os.environ`)은 빈 문자열 키를 통과시킨다. `llm_called` 단언이 있어 초록 착시는 없고 실패 문구만 덜 직접적이라 보류한다.
