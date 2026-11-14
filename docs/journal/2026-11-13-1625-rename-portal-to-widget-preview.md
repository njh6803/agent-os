# 2026-11-13 용어 "질문 페이지"를 "위젯 미리보기 페이지"로 바꾼다 (harness rename-portal-to-widget-preview)

세션 제목: `chore/rename-portal-to-widget-preview` (인계하면 `<브랜치> (인계함)`으로 바뀐다)

## 사용자 프롬프트 원문

> 사용자: 질문 페이지를 위젯 미리보기 페이지로 바꾸는 chore를 티켓 .scratch/harness/issues/rename-portal-to-widget-preview.md로 쓰고 한다
>
> 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/rename-portal-to-widget-preview.md. 용어 "질문 페이지"를 "위젯 미리보기 페이지"로 바꾸는 이름 바꾸기 chore
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 rename-portal-to-widget-preview)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: 질문 페이지를 위젯 미리보기 페이지로 바꾸는 chore를 티켓 .scratch/harness/issues/rename-portal-to-widget-preview.md로 쓰고 한다
> 브랜치: chore/rename-portal-to-widget-preview
> 모델: Sonnet 5.5 / high
> 읽을 것: 일지 docs/journal/2026-11-13-0426-portal-login-ui-design.md의 "다음"의 "그 밖에 남은 일" 첫 항목, docs/agents/issue-tracker.md(harness 티켓의 서식·상태·이름)
> 이어받을 상태: 사람이 PR #557 병합 뒤 chore 브랜치 하나에서 따로 하기로 골랐다(일지 "다음"). 범위는 일지의 그 항목이 정한다. CONTEXT.md부터 고치고 명세·계획·코드 주석·화면 글의 옛 이름을 바꾸며, 일지와 ADR 본문은 기록이라 두고 ADR에는 이력 한 줄을 단다. 코드 이름 portal과 경로 /portal/은 그대로 둔다. 화면에 보이는 글을 바꾸면 그 글을 대는 e2e와 사진 비교의 기준도 걸릴 수 있어 받는 세션이 Grep으로 대 본다(이 세션은 대 보지 않았다). 이 chore 뒤의 다음 일은 위젯이 로그인 상태를 직접 그리는 방향의 설계 인터뷰다(같은 "다음" 절).
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 것

- 제목을 브랜치 이름으로 바꾸고 `tidy-checkouts`를 돌았다. 주 체크아웃(dev)은 깨끗했고 `e5c709c96`에서 `fe69c9971`로 당겼다. 병합된 로컬 브랜치 하나(`worktree-03-llm-local-command-rents-model-servers`)를 지웠고 휴지통의 `node_modules` 다섯을 비웠다. 워크트리는 하나도 지우지 않았다(병합된 PR이 없거나, 쥔 프로세스나 바뀐 파일이 있거나, 앱의 표지가 있거나, 돌고 있는 세션의 것이었다). 그 뒤 `EnterWorktree`로 `rename-portal-to-widget-preview` 워크트리에 들어가 브랜치를 `chore/rename-portal-to-widget-preview`로 바꿨다.
- 티켓 `.scratch/harness/issues/rename-portal-to-widget-preview.md`를 썼다. 범위는 일지 `2026-11-13-0426-portal-login-ui-design.md`의 "다음"이 정한 대로이고, 사용자의 말 "질문 페이지라고 하지말고 '위젯 미리보기 페이지'라고 해"와 그 뒤 바로잡은 쓰임("자기 웹 페이지가 없는 사이트를 대신하는 페이지"가 아니다)을 담았다. 수용 기준을 채우고 `Status: done`으로 바꿨다.
- `질문 페이지`를 `위젯 미리보기 페이지`로 바꿨다(바이트 단위 치환, 줄 끝은 LF 그대로. 바뀐 추적 파일은 ADR 이력과 `.scratch/plan.md`와 `CONTEXT.md`까지 더해 99개다). 제외한 것은 일지, ADR 본문과 색인(`docs/adr/README.md`)의 제목, `.scratch/*/design/`(그린 화면의 목업과 시작 프롬프트. 목업은 sha256으로 웹 편집을 가르므로 건드리지 않았다), 이 티켓과 `CONTEXT.md`의 `_Avoid_` 줄이다. 시험 이름과 화면에 찍히는 글(`web/apps/portal/server/diagnostics.ts`의 시작 로그, `tools/start.ts`와 `server/page.ts`의 오류 문구)도 같이 바뀌었고 그것을 맞대는 시험과 e2e의 준비(`stack.ts`)도 같은 치환으로 맞았다. 변이 표(`.scratch/pilot-portal/probes/*_mutations.toml`)의 `-t "질문 페이지…"` 필터도 같은 치환으로 맞았다. 카나리아 명세 둘의 기대 문장도 규칙 문장과 같이 바뀌었다.
- `CONTEXT.md`: 용어 둘(`위젯 미리보기 페이지(Portal)`, `위젯 미리보기 페이지 설정(Portal Settings)`)로 바꾸고, 정의에 `.scratch/pilot-portal/spec.md` Problem Statement가 적은 쓰임 둘과 "사이트가 자기 웹 페이지를 갖지 못했을 때 그것을 대신하는 페이지가 아니다"를 더했다. `_Avoid_`에서 "미리보기 페이지(이 페이지가 그 일도 한다)"를 빼고 옛 이름 "질문 페이지(옛 이름. 2026-11-13에 바꿨다)"를 넣었다. 고지·로그인 상태 정의의 "질문 페이지가 알리는 글" 같은 문장은 이름만 바꿨고 뜻은 그대로다. 위젯이 로그인 상태를 직접 그리는 방향의 설계 인터뷰가 그 문장들을 다시 정한다.
- ADR 여덟(0046, 0048, 0050, 0051, 0053, 0056, 0059, 0060)의 끝에 `### 2026-11-13 용어 "질문 페이지"를 "위젯 미리보기 페이지"로 바꿨다` 이력을 달았다. 이력 절이 없던 셋(0056, 0059, 0060)은 `## 이력` 절도 만들었다. 본문은 그대로다.
- 열린 대기열 항목 둘(`answer-estimate-before-reading-adr`, `design-line-leaves-interview-questions`)의 이름도 바꿨다. 첫째는 승인 칸이 가리키는 옛 세션의 말 한 구절이라 기록이지만, 열린 항목이라 살아 있는 문서로 세었다.
- `uv run python tools/plan_table.py`로 `.scratch/plan.md`를 다시 만들었다.
- 글자 수가 6자에서 11자로 늘어 100칸을 넘은 파이썬 줄 열네 곳(`.scratch/pilot-portal/probes/node_ts_workspace.py`, `src/agent_os/main.py`, `tests/test_calc_plugin.py`, `tests/test_conftest.py`, `tests/test_portal_llm.py`, `tools/mutate.py`)을 줄바꿈만 고쳐 `ruff check`를 통과시켰다. 줄을 넘기는 스크립트는 세션 스크래치패드에 있었고 저장소에는 없다. 그 스크립트는 연쇄로 넘치는 줄을 한 번에 다 못 풀어 같은 줄을 여러 번 다시 넘겼고, `node_ts_workspace.py` 45행만 `Edit`으로 직접 끊었다.

## 번복하거나 고친 것

- `CONTEXT.md`의 `_Avoid_`에 `사이트 대행 페이지`를 한때 넣었다가 뺐다. 사용자가 쓴 말이 아니라 이 세션이 지은 말이라서다.
- 처음 `tools/canary.py --shape`를 명세 파일 없이 쳐서 사용법만 길게 찍혔다. 명세 두 개를 넘겨 다시 쳤다.
- 워크트리 가드가 `&&`와 `;`로 이은 복합 `git` 명령을 거부했다(CLAUDE.md 환경 함정). 하나씩 쳐서 풀었다.

## 돌려서 본 것

- `uv run python tools/run_checks.py`: 종료 0. `check-ticket`, `zizmor`, `lint-imports`, `check-instructions`, `check-type-escapes`, `pyright-linux`, `pyright`, `run-hooks`, `pytest`(329.8초), `web-verify`(517.0초) 모두 Passed.
- `uv run ruff check --output-format concise .`와 `uv run ruff format --check .`: 초록. `pnpm -C web run format`(prettier): 초록.
- `pnpm -C web/apps/portal exec playwright test`: 41건 통과(41.9초). 시작 로그와 e2e 준비를 건드렸기 때문이다.
- `PYTHONUTF8=1 uv run python tools/mutate.py --check`로 `pilot-portal`의 변이 표 셋(변이 23, 14, 23)을 대 봤고 모두 원문이 한 번씩 있다. 이 확인은 원문만 본다. 변이를 다시 돌려 `-t` 필터와 시험 이름이 맞는지 본 것은 아니다.
- `tools/canary.py --shape`와 `--preflight`로 카나리아 명세 둘이 통과했다. `claude -p`는 돌리지 않았다(문구만 고친 명세를 사전 확인으로 갈음하는 규약).
- 잔존 확인: `git grep -IlE "질문 ?페이지" -- . ':!docs/journal' ':!docs/adr'`가 `.scratch/pilot-portal/design/`의 넷, `.scratch/portal-login/design/screens-prompt.md`, `CONTEXT.md`(`_Avoid_` 줄)만 낸다. 줄이 바뀌며 갈라진 꼴(`git grep -Pzc`)은 없었다.
- 돌리지 않은 것: `uv run --env-file .env pytest -m llm_portal`. 이 변경이 포털 e2e 코드의 주석과 문구만 바꾸고 모델 호출 경로는 건드리지 않아서다. 사진 비교는 포털에 없고 위젯·관리 화면·디자인 시스템 패키지를 건드리지 않았다.

## 인계 시점의 상태

- 커밋하지 않은 변경이 워크트리에 있다. 바뀐 추적 파일 99개와 미추적 둘(티켓, 이 일지)이다. 커밋은 아직 없다.
- 셀프 리뷰(`/code-review`)를 시작하려다 컨텍스트가 인계 문턱을 넘어 인계했다. 리뷰는 새 세션이 한다. 이 세션은 리뷰의 서브에이전트를 띄우지 않았다.
- 이 세션이 `uv run`과 `pnpm -C web install --frozen-lockfile`로 워크트리에 `.venv`와 `web/node_modules`를 만들었다(둘 다 무시되는 폴더다).
- 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다).
- 제목을 `chore/rename-portal-to-widget-preview (인계함)`으로 바꿨고 워크트리 잠금을 풀었다(`git worktree unlock`이 출력 없이 끝났다).
- open-session을 부른다 2026-11-13T07:26Z

## 셀프 리뷰와 반영 (이어받은 세션)

- 범위: 기준 SHA `fe69c9971`(origin/dev와 HEAD가 같다), 추적 파일 99개, 미추적 둘(티켓, 이 일지), 커밋 0개. 표준 축(sonnet·high)과 명세 축 서브에이전트가 읽기 전용으로 돌았다. 아래는 그 둘의 보고를 이 세션이 받아 판정한 것이다.
- 고친 것(둘 다 서브에이전트가 짚었고, 같은 자리를 이 세션이 `git grep -In "질문_페이지"`와 파일 읽기로 손으로 확인한 뒤 고쳤다).
  - `tests/test_portal_llm.py`의 시험 함수 이름 `test_질문_페이지에서_…`가 밑줄 꼴이라 `질문 ?페이지` grep을 지나갔다. `test_위젯_미리보기_페이지에서_…`로 바꿨다. 이름이 길어져 ruff E501(폭 100)을 넘어(102) `보낸_요청_하나에`를 `보낸_요청에`로 줄였다. 이 이름을 가리키는 곳은 서브에이전트가 `-k`와 변이 표에서 찾지 못했다고 보고했다.
  - 줄이 바뀌며 갈라진 꼴이 둘 남아 있었다(`web/apps/portal/browser/portal.ts` 21-22행, `web/apps/widget/tools/start.ts` 22-23행). 앞 세션의 `git grep -Pzc`는 이것을 잡지 못했다. 이 세션이 추적 파일 전부를 파이썬 정규식(공백·줄바꿈·주석 머리표·밑줄을 허용)으로 훑어 보니 기록 파일(`.scratch/*/design/`, `CONTEXT.md`의 `_Avoid_`) 밖에는 더 없었다.
  - `.scratch/pilot-portal/probes/node_ts_workspace.py`의 독스트링이 새 이름을 줄 가운데에서 갈라 두고 있어 이름이 한 줄에 들게 다시 감았다. 감은 뒤 폭이 105여서 한 번 더 감았다.
  - 티켓의 수용 기준 둘째가 "잔존은 다섯과 `_Avoid_`뿐"이라고 닫은 주장은, 이 티켓 파일이 옛 이름을 적고 있어 커밋되면 거짓이 되고 갈라진 꼴과 밑줄 꼴도 잡지 못했다. 이 티켓을 grep 제외에 밝히고 갈라진 꼴과 밑줄 꼴을 찾은 방법을 적었다. 수치 "파이썬 줄 열네 곳"은 서브에이전트가 12~13곳으로 셌고 diff로 재현되지 않아 수를 뺐다. 일지의 "90개 파일"은 99개로 고쳤다.
- 남긴 것: `docs/adr/README.md`의 색인 제목 둘에 옛 이름이 남은 것(티켓이 정한 바이고 ADR 제목과 같게 둔다). `.scratch/retro-queue/answer-estimate-before-reading-adr.md`의 시대착오(옛 세션이 새 이름을 말한 것처럼 읽힌다)는 티켓이 열린 항목이라 일부러 바꿨다고 적은 것이다. CONTEXT.md의 새 정의 둘째 문장이 앞 문장과 겹친다는 smell 지적은 판단 항목이라 두었다.
- 헌법 판: `uv run python tools/sibling_overlap.py`가 종료 1로, 헌법 파일(`operations.md`, `tech.md`)을 고치고 판을 올리지 않았다고 알렸다(출력을 읽었다). 형제 워크트리 `03-llm-local-command-rents-model-servers`가 3.0.95를 쓰고 있어 3.0.96으로 올리고, `docs/constitution/README.md`에 3.0.95를 형제가 비워 둔 판이라는 문장을 달았다(3.0.61 문장의 선례를 따랐다). 다시 치니 "이 브랜치의 새 번호: 헌법 3.0.96, 번호 겹침 없음"이었다.
- 커밋: `491b806b8`(pre-commit 통과. `checks` 러너 553초, pytest 363.3초, web-verify 552.7초, 헌법 판·변이 표·카나리아 명세 모양 검사 포함). 인용 대조(경고만 내는 검사)가 이 일지의 따옴표 인용 넷(앞 세션이 말을 줄여 따옴표를 붙인 것 둘, 도구 출력 둘)과 티켓·명세 인용 둘을 저장소에서 찾지 못했다고 알렸다. 막지 않는 경고이고 뜻을 바꾸지 않아 그대로 두었다.
- PR 직전 CodeRabbit CLI(`coderabbit-review` 서브에이전트 보고를 받았다): `Seat: not assigned`(`Plan: Free`, CLI 0.7.5)에서도 `review_completed`로 끝났고 지적 0건, 종료 코드 0이다. 파일 103개로 150개 한도 안이었다. 서브에이전트가 직접 대 본 것은 보고에 있다. 치환을 되돌려 견준 차이가 줄바꿈 머리표와 시험 이름의 `_하나` 삭제뿐이었고, 화면 글과 시험의 맞댐이 같았으며, 변이 표 셋(14·23·23)의 `--check`와 카나리아 `--shape`·`--preflight`가 통과했고, 고친 시험 이름을 가리키는 곳이 없었다. 서브에이전트가 돌리지 않은 것은 e2e, `-m llm_portal`, 사진 비교, `web verify`이고 정적 대조만 했다.
- 다시 돌린 명령: `uv run ruff check --output-format concise .`는 "All checks passed!", `uv run ruff format --check .`는 "2184 files already formatted"였다. 나머지 게이트는 커밋의 pre-commit 결과로 갈음한다(결과는 커밋 뒤에 적는다). 포털 e2e와 `web-verify`는 이번에 주석 둘과 파이썬 시험 이름·독스트링만 고쳐 다시 돌리지 않았다.

## 회고

후보 셋을 냈고 승인 하나, 기각 둘이다. 대기열을 `uv run python tools/queue_open_rows.py`로 세니 열린 항목 92개이고 만료할 항목은 없었다(출력을 읽었다). `--search 갈라진`, `줄.바뀌며`, `치환.chore`로 같은 일을 다룬 항목을 찾았으나 없었다.

- 승인(1회차, 대기열 `rename-residual-grep-misses-split-and-underscore-forms`): 앞 세션이 치환 뒤 잔존을 `git grep -E`와 `-Pzc`로 0이라 닫았는데 줄바꿈으로 갈라진 꼴 둘과 밑줄 꼴 하나가 남아 있었다(셀프 리뷰 두 축이 짚고 이 세션이 파이썬 정규식으로 다시 훑어 확인했다). 사건은 있고, 처방은 지침 한 줄이라 층은 낮지만 바뀌는 말이 chore마다 달라 검사로 고정할 꼴이 없다. 더하는 것이라 다섯 번째 반복이나 손상 전에는 대기열에서 회차를 센다. 이 세션에서는 반영하지 않았다.
- 기각: `tools/sibling_overlap.py`가 헌법 파일을 고치고 판을 올리지 않았다고 알린 것(종료 1). 이미 있는 검사가 막아 3.0.96으로 올려 풀었다.
- 기각: 시험 함수 이름이 길어져 `hook_ruff_line_width`가 E501을 알린 것. 이미 있는 훅이 알려 그 자리에서 고쳤다.
- 사용자에게 넘긴 것은 없다.

## 다음

이 chore가 병합되면 다음 일은 앞 일지 `docs/journal/2026-11-13-0426-portal-login-ui-design.md`의 "다음"이 정한 설계 인터뷰다. 위젯이 로그인 상태와 고지, 다크 모드를 직접 그리는 방향과 URL로 제공하는 방식을 한 인터뷰로 정한다. 정할 것과 넘길 입력은 그 일지에 있고 이 chore가 바꾼 것은 이름뿐이다. 그 일지와 ADR 0059·0060 본문은 기록이라 옛 이름 "질문 페이지"가 그대로 남는다. 새 인터뷰는 새 이름 "위젯 미리보기 페이지"로 쓴다.

- 남은 일(앞 일지가 넘긴 것): 짓기 도구의 U+FFFD 고침(`ds-upload-replacement-char-rejected`), schema_version Minor, 프로브 README의 Nit.
- 이 PR이 남긴 것: `docs/adr/README.md`의 색인 제목 둘에 옛 이름이 남는다(ADR 제목을 따른다). 인용 대조 경고 넷은 막지 않는 경고라 그대로 두었다.
