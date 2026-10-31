# 2026-10-31 (07) 모델 플러그인 명세

## 시작

> 사용자: `.claude/skills/to-spec/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가
> 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: 다음 작업: 기능 model-plugin.
> 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세 / 다음 단계: 명세 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill
> 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서
> 브랜치를 따지 않고 EnterWorktree(name은 model-plugin-spec)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트:
> /to-spec / 브랜치: docs/model-plugin-spec / 모델: Fable 5.1 / xhigh. 결정표의 "설계는 끝났고 spec.md가 없다" 줄 / 읽을 것:
> docs/journal/2026-10-31-06-model-plugin-design.md의 "다음" 절(명세가 정할 것의 목록),
> docs/adr/0040-model-is-a-plugin-built-per-run-from-its-manifest.md / 이어받을 상태: 설계 PR #442는 병합됐다(squash d5e2f1ec).
> 봇 넷째 회차(claude-review)가 보류한 Minor 셋은 일지에 없고 여기에만 있다. (1) ADR 0008 이력과 ADR 0040의 "실행 길은 / 실행
> 길이 읽은 적 없고"가 "실행 길이"로 끊겨 읽히니 "실행 경로"로 바꾼다(명세가 두 ADR의 그 자리를 다시 만질 때). (2) ADR 0040
> Consequences 첫 불릿(모델 매니페스트의 모양)이 길어 칸 정의와 호환성(거부되는 옛 파일, GET /plugins 500)을 불릿 둘로 나누고,
> 고칠 곳 목록의 두 곳 중복을 한 곳으로 모은다. (3) .scratch/plan.md의 model-plugin 행에 /to-spec이 입구와 깨짐의 자리를 첫
> 항목으로 받는다는 표시를 둔다(core.md의 준비 순서 불변식 부재 → 깨짐 → 꺼짐에 닿는다). 또 ADR 0008 이력에 schema_version "1"
> 유지의 예외(읽은 적도 실물 파일도 없던 종류의 첫 필수 칸)를 승인 뒤에 더했다. 결정은 그대로이고 근거만 정리했으니 명세를 쓰며
> ADR 0040을 다시 볼 때 사용자에게 짚는다. 회고는 설계 세션이 돌았다 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은
> 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다 / 이번 요청 범위:
> PR과 병합까지

첫 턴 훅이 짚은 차례대로 세션 제목을 `docs/model-plugin-spec`으로 바꾸고, `tidy-checkouts`를 돌고, 워크트리에 들어갔다.

## tidy-checkouts 보고

- 루트: main을 `8f0e5f81`에서 `d5e2f1ec`(origin/main)로 당겼다.
- 지운 것: 워크트리와 브랜치 넷. `031-sonnet-high-cell-and-sweep-removal`(`chore/031-…`), `05-first-canonical-upload`(`feature/05-…`), `12-main-run`(`feature/13-main-run-judge`), `fable-design-spec`(`chore/030-fable-design-spec-cells`).
- 남긴 것: `08-admin-decision-column`(`remove`가 종료 1. 이름 바꾸기가 WinError 5로 거부됐고 읽을 수 있는 프로세스에서 쥔 것을 찾지 못했다. 망가뜨린 것 없이 남았다), `06-round-drive-record`(바뀐 파일), `admin-style-spec`·`admin-style-to-spec`·`mcp-shutdown-spec`·`web-widget-spec`(병합된 PR 없음), `confident-wright-2d3ebf`·`elegant-dijkstra-aaddb9`(앱 표지), `next-feature-grill`(도는 세션 docs/model-plugin), `wireframe-optional`(세션 셋의 `claude.exe`·`pwsh.exe`가 쥠).
- 사람에게 넘길 것 없음. 휴지통 줄 없음.

그 뒤 `EnterWorktree(name=model-plugin-spec)`로 `C:\project\agent\.claude\worktrees\model-plugin-spec`에 들어가 `origin/main`(`d5e2f1ec`)에서 `docs/model-plugin-spec`을 만들고 임시 브랜치 `worktree-model-plugin-spec`을 지웠다. `uv run python`이 워크트리에 `.venv`를 새로 만들었고 `pnpm -C web install --frozen-lockfile`을 백그라운드로 돌렸다.

## 읽은 것

to-spec 스킬, 설계 일지 2026-10-31-06의 전문, ADR 0040·0008·0017(이력 2026-10-03)·0012, `.scratch/plan.md`의 model-plugin 행과 프론티어, `docs/agents/issue-tracker.md`, 선례 명세 셋의 서두 모양(`.scratch/mcp-shutdown/spec.md` 등), `.claude/rules/probes.md`·`adr.md`·`core.md`·`sdk.md`·`adapters.md`·`tests.md`, `core/ports.py`·`run.py`·`loop.py`·`main.py`·`server.py`·`adapters/anthropic.py`·`filesystem.py`·`sdk/manifest.py`·`ids.py`·`http/errors.py`, `tests/core/test_run.py`의 가짜 포트와 `_run`, `tests/test_server.py`의 `_admin_app`과 `SONNET`, `tests/test_main.py`의 `workspace`와 `-m llm` 시험, `tests/adapters/test_anthropic.py`, 두 e2e 스택과 `PluginList.tsx`, `CONTEXT.md`의 모델·기본 모델, langchain-anthropic 1.7.2의 `ChatAnthropic` 필드(`uv run python`으로 봤다).

## 프로브

설계 ADR이 구현 티켓에 넘긴 측정("만드는 것이 네트워크를 타지 않는다는 것은 어림")은 결과가 결정(실행마다 만든다)을 바꿀 수 있어 명세가 쟀다(to-spec 3단계). `.scratch/model-plugin/probes/`의 둘이고 결과는 그 `README.md`다.

- `build_without_key.py`: 측정 14회차. 어댑터와 같은 인자로 `ChatAnthropic`을 만드는 데 0.1~0.2ms, 키 없이도 죽은 주소를 줘도 클라이언트를 만들지 않는다. 죽은 주소로의 호출(양성 대조)은 `APIConnectionError`, 키 없는 호출은 네트워크 전에 langchain-anthropic의 `TypeError`("Anthropic authentication failed: no API key …")다. 첫 판의 표지(`anthropic_api_key is None`)가 1.7.2의 기본값(빈 `SecretStr`)과 어긋나 만들기 10회차가 측정 아님으로 섰고, 코드를 읽고 표지를 빈 글로 바꿨다. 결과는 두 판에서 같았다.
- `manifest_fields.py`: 측정 29회차. 받은 사례 7과 거부 사례 19가 모두 기대한 값·표지다. 직렬화 스키마에서 새 칸 다섯이 모두 `required`에 들고 `null`을 허락하며 `provider`는 이름 있는 정의 `ModelProvider`다. 칸 이름 `model_id`·`model`은 pydantic 2.13.5의 기본 보호 이름 공간 경고를 내지 않는다(양성 대조 `protected_namespaces=("model_",)`는 낸다).

## ADR 문구 손질

지시문의 Minor 셋 가운데 (1)과 (2)를 반영했다. ADR 0040 Consequences 첫 불릿을 "모델 매니페스트의 모양"과 "공통 넷만 적은 모델 파일은 거부된다"로 나누고, 둘째·셋째·"이번 범위 밖" 불릿에 흩어진 "구현 티켓이 고친다"를 새 불릿 "구현 티켓이 고칠 곳" 하나로 모았다. ADR 0040과 ADR 0008 이력의 "실행 길은/실행 길이"를 "실행 경로는/실행 경로가"로 바꿨다. 결정은 바뀌지 않았다. ADR 0008 이력의 예외 문장이 승인 뒤에 더해진 것은 이음매 질문 앞에서 사용자에게 짚었다.

## 이음매 (사용자가 골랐다)

> 질문: 모델 플러그인 기능의 시험을 주로 어느 자리에 붙일까요? 추천 자리는 core의 실행 함수(run·resume)에 가짜 플러그인 소스와 가짜 모델 만들기를 꽂는 자리이고, 경계(매니페스트 검증, 어댑터, 서버 시작 진단, HTTP 두 면, 관리 화면, 두 e2e 스택)마다 기존 시험 자리에 얇은 시험 하나씩과 실제 모델 호출 시험 하나(-m llm)를 더합니다.
>
> 사용자: core 함수에 가짜 꽂기 (Recommended) — 지금 tests/core/test_run.py가 하는 방식 그대로. 준비 순서(지금은 없음→깨짐→꺼짐→import이고 그 뒤에 모델 만들기가 늘 예정), 매니페스트를 몇 번 읽는지, 에이전트가 고른 모델이 쓰이는지를 가짜 부품의 기록으로 재서 빠르고 결정적으로 돈다. 바깥 경계는 얇은 시험 하나씩이 맡는다.

고르지 않은 둘은 "HTTP 앱에 요청 넣기"(`create_app()`에 가짜 포트를 꽂고 요청을 밀어 상태 코드로 본다. 준비 순서와 읽기 횟수를 응답으로 가르기 어렵고 CLI 길은 따로 시험이 필요해 주 자리가 둘이 된다)와 "실제 서버 프로세스 띄우기"(가장 바깥이지만 다른 프로세스라 가짜 모델을 꽂을 수 없어 실제 모델 호출이 들고 느리다)였다. 선택 화면의 설명에 적은 사실은 훅이 짚어 지금 코드에 대 봤다(`tests/core/test_run.py`의 `_run`과 `FakePlugins`, `tests/test_server.py`의 ASGI 이음매, `.claude/rules/core.md`의 준비 순서 문장).

## 산출물

- `.scratch/model-plugin/spec.md`(Status: ready-for-agent). 서두의 수는 넘겨받은 것 열둘, 사용자가 고른 것 하나(이음매), 명세가 정한 것 열하나(절 제목에 표시), 이력 하나, 거부한 안 열셋이다. 수는 `grep`으로 본문의 표시를 세어 맞췄다.
- `.scratch/model-plugin/probes/`의 `build_without_key.py`·`manifest_fields.py`와 결과 `README.md`.
- ADR 0040. 지시문의 문구 손질 둘(위)과, 명세가 정한 넷과 잰 것 하나를 적은 2026-10-31 이력 초안, 본문의 "어림이고 구현 티켓이 본다" 문장에 그 이력을 가리키는 포인터. 이력은 셀프 리뷰 뒤 사용자 승인을 받는다(작업 규약 5).
- ADR 0008 이력의 "실행 경로".
- `.scratch/plan.md`의 model-plugin 행(명세 경로, /to-spec이 입구와 깨짐의 자리를 첫 항목으로 받았다는 표시, 명세가 정한 것의 요지, 사용자가 고른 것)과 프론티어 문단(다음은 명세 검토와 티켓).

검사: `tools/check_md_tables.py`·`check_line_separators.py`·`check_adr_pointers.py`가 0, `check_quotes.py`는 막지 않는 경고만이고 이 브랜치의 파일에는 없다(출력을 grep으로 봤다). 프로브 둘은 `ruff check`·`ruff format --check`가 지나간다.

## 인계

셀프 리뷰를 위해 Skill 도구로 `code-review`를 부른 직후 인계 계기(`hook_handoff`. 세션 컨텍스트 342,011 토큰, 경계 `셀프 리뷰 직전`)가 와서 `next-session` `handoff.md`를 Read로 열어 따랐다. 인계하지 않는 때 다섯에 들지 않는다. 계기를 낸 명령이 실패하지 않았고, 요청 범위는 PR과 병합까지라 이 경계에서 끝나지 않고, 이 세션의 지시문의 "이어받을 상태"는 `인계:`로 시작하지 않고, 이 일지에 `인계 못함` 줄이 없고, `get_session self`에 `parentSessionId`가 없다. 열린 PR은 없다(`gh pr view docs/model-plugin-spec`이 없음으로 끝났다). 그래서 넘긴다. `code-review`의 서브에이전트 둘은 띄우지 않았다. 셀프 리뷰는 새 세션이 처음부터 한다.

이 세션의 사용자 프롬프트는 위 "시작"의 지시문 하나와 위 "이음매"의 답 하나다. 이 세션이 번복하거나 고친 것은 넷이다. `build_without_key.py`의 표지(위 "프로브"), spec.md 서두의 수(처음 적은 "명세가 정한 것 열셋, 거부한 안 열하나"가 본문의 표시와 어긋나 열하나와 열셋으로 고쳤다), 이음매 질문의 선택지 설명(첫 호출은 설명의 사실을 코드에 대 보라는 훅에 막혔고, `tests/core/test_run.py`·`tests/test_server.py`·`.claude/rules/core.md`를 확인해 설명을 보강한 뒤 같은 질문과 라벨로 다시 물었다), 프로브 둘의 E501(ruff가 한글을 폭 2로 세어 `tools/rewrap_comments.py`로 독스트링을 감고 `ruff format`과 `ruff check --fix`로 맞췄다). 이 세션의 제목은 `docs/model-plugin-spec`이고, 아래 지시문을 낸 뒤 `docs/model-plugin-spec (인계함)`으로 바꾼다.

새 세션이 할 일은 셀프 리뷰부터다. `/code-review`의 고정점은 `origin/main`(`d5e2f1ec`)이고, 명세 축의 근거는 ADR 0040, 설계 일지 2026-10-31-06의 "다음" 절(명세가 정할 것의 목록), 위 "시작"의 지시문 원문(봇이 보류한 Minor 셋. 모두 반영했다. (1)·(2)는 ADR 0040·0008에, (3)은 `.scratch/plan.md`에), 위 "이음매"의 사용자 답이다. 코드가 아니라 문서와 프로브다. 셀프 리뷰를 반영한 뒤 spec.md 서두의 수를 다시 세고, ADR 0040의 2026-10-31 이력 초안을 사용자에게 보여 승인을 받은 뒤 커밋한다(작업 규약 5). ADR 0008 이력의 예외 문장은 이미 사용자에게 짚었다(위 "ADR 문구 손질"). 커밋은 0이고 변경은 모두 워크트리의 작업 트리에 있다. 커밋 뒤는 to-spec 스킬의 순서대로 PR과 병합까지 가고(면제 PR. 병합은 워크트리에서 `merge.md` "워크트리에서 병합할 때"), 그 뒤 `next-session`의 다음 단계는 티켓 `/to-tickets`다(사람이 부른다). 회고는 설계 세션이 돌았다(일지 2026-10-31-06 "회고"). 이 절은 커밋하지 않았으므로 새 세션이 다음 커밋에 싣는다.

지시문:

```
다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계(ADR 0040)의 명세 마무리(셀프 리뷰, ADR 0040 이력 승인, PR과 병합)
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/model-plugin-spec
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-10-31-07-model-plugin-spec.md 전문("시작"의 지시문 원문과 Minor 셋, "이음매"의 사용자 답, "산출물", "인계"), docs/journal/2026-10-31-06-model-plugin-design.md의 "다음" 절, docs/adr/0040-model-is-a-plugin-built-per-run-from-its-manifest.md
이어받을 상태: 인계: 셀프 리뷰 직전 docs/journal/2026-10-31-07-model-plugin-spec.md. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main)부터 한다. 명세 축의 근거는 ADR 0040, 설계 일지의 "다음" 절, 지시문 원문의 Minor 셋(모두 반영했다), 이음매의 사용자 답이다. 코드가 아니라 문서와 프로브다(spec.md, probes/ 셋, ADR 0040·0008, plan.md, 일지). 셀프 리뷰를 반영한 뒤 spec.md 서두의 수를 다시 세고, ADR 0040의 2026-10-31 이력 초안을 사용자에게 보여 승인받은 뒤 커밋한다. ADR 0008 이력의 예외는 이미 짚었다. 면제 PR(docs/ 브랜치, 티켓 없음)이고 병합은 워크트리에서 한다(merge.md "워크트리에서 병합할 때"). 그 뒤 next-session의 다음 단계는 티켓 /to-tickets(사람이 부른다). 회고는 설계 세션이 돌았다. 일지의 "인계" 절은 커밋하지 않았으니 다음 커밋에 싣는다.
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 바꾸고 워크트리 잠금을 푼 뒤 open-session을 부른다 2026-10-31T10:19:47Z

## 이어받음 (셀프 리뷰 직전)과 셀프 리뷰

위 지시문으로 연 새 세션이다. 첫 턴 훅대로 제목을 `docs/model-plugin-spec`으로 바꾸고, `git worktree list`에서 그 브랜치가 체크아웃된 워크트리 `model-plugin-spec`(`d5e2f1ec`. origin/main과 같다)을 찾아 `EnterWorktree(path)`로 들어갔다. 커밋은 0이고 변경은 모두 작업 트리에 있었다. `uv run python tools/sibling_overlap.py`는 번호 겹침 없음이었다(다음 빈 번호는 일지 2026-10-31-08, 대기열 555, 티켓 034. `mcp-shutdown-spec` 워크트리가 `.scratch/plan.md`를 함께 고쳤다).

`/code-review`(고정점 `origin/main` = `d5e2f1ec`. 범위는 수정 3, 미추적 5, 커밋 0)를 돌렸다. 표준 축(sonnet·high)은 Critical·Major 0, Minor 7, Nit 2이고, 명세 축(명세 원천은 ADR 0040, 설계 일지 "다음" 절, 지시문의 Minor 셋, 이음매의 사용자 답, to-spec 스킬)은 Critical·Major 0, Minor 3, Nit 4다. ADR 0040의 포인터 지적은 두 축이 함께 냈다. 두 축이 맞다고 확인한 밀 주장(서두의 수, 포트 다섯, mcp 문구의 꼴, 이름과 경로의 실재, 설치된 판, 프로브의 종료 코드와 회차 수, ADR 0010·0017 이력의 날짜, 설계 일지 "다음"의 일곱 항목에 결정이 있음, 지시문의 Minor 셋 반영, 이음매의 답 그대로)은 고칠 것이 없었다.

고친 것은 열셋이다.

1. [표준 Minor] 시작 때의 확인의 "이름이 없거나 비었다(지금 그대로)". 지금 `resolve_model_name`은 환경변수가 없으면 코드의 기본값으로 가고 빈 값만 거부하므로(`adapters/anthropic.py`를 읽었다) "비었다는 지금 그대로이고, 없다는 코드의 기본값이 사라져 새로 드는 갈래다"로 고쳤다.
2. [표준 Minor] 매니페스트의 경계를 잰 것이 실제 sdk 클래스가 아니라 같은 설정의 시제품이라는 것을 명세에 적었다("sdk `PluginManifest`와 같은 설정의 시제품으로 쟀다").
3. [표준 Nit] 서두의 표시 문구를 "각 절 제목의 괄호에 '명세가 정했다'로 표시한다"로 고쳤다. 제목 열하나 가운데 넷이 "(넘겨받았다. 내용은 명세가 정했다)" 같은 변형이라 글자 그대로의 "(명세가 정했다)"가 아니었다. 수는 맞았다.
4. [표준 Nit] 명세의 "로더 없는 종류" 따옴표를 뗐다. 코드의 주석은 "로더가 아직 없는 종류"다(`PluginList.tsx`를 읽었다). ADR 0040 본문의 같은 따옴표는 병합된 글이라 두었다(`.claude/rules/adr.md`의 "본문의 다른 글자는 고치지 않는다").
5. [표준 Minor] `build_without_key.py`의 `invoke_dead_base_url` 회차에 호출 뒤 `_async_client`가 인스턴스 `__dict__`에 있는지를 더했다. 만들기 회차의 "클라이언트 안 만듦"을 읽는 `__dict__` 탐지가 만들어진 클라이언트를 실제로 잡는다는 양성 대조다(`.claude/rules/probes.md` 셋째 항목). 비공개 속성을 직접 건드리지 않으려고 새 회차 대신 그 회차의 확인에 넣었다. 회차 수는 14 그대로다. 독스트링과 README에 적었다.
6. [표준 Minor] 시간 수치. 이 세션의 두 실행(종료 코드 0, 측정 14회차·측정 아님 0)에서 만들기는 중앙 0.1ms·최대 0.3ms, 죽은 주소 호출 2.0~2.3초, 키 없는 호출 2.5~2.9ms였다(앞 세션의 두 판은 0.1~0.2ms, 2.0~2.2초, 2.5~2.8ms). README·명세·ADR 0040 이력의 수를 이 범위로 고쳤다("0.2ms 아래"는 "1ms 아래(중앙 0.1ms)"로).
7. [표준·명세 Minor] ADR 0040 본문의 "명세가 정하고 시험이 고정한다"(준비 단계 불릿)와 "어느 이름을 둘지는 명세가 정한다"(저장소 불릿)에 2026-10-31 이력의 포인터를 달았다(`.claude/rules/adr.md`. 선례는 ADR 0034의 2026-10-17 포인터 셋). `tools/check_adr_pointers.py`는 0이다.
8. [표준·명세 Nit] ADR 0040 "구현 티켓이 고칠 곳"의 "어느 티켓이 어느 자리를 맡는지는 명세가 나눈다"를 "묶음으로 나누는 것은 명세이고, 묶음을 티켓으로 쪼개는 것은 to-tickets다"로 고쳐 명세와 맞췄다. 그 문장은 main에 없는 이 브랜치의 새 글이다(`git show origin/main:` 사본을 grep했다).
9. [명세 Minor] 프로브 README의 "이 둘은 … 다시 잰 것이다". `ChatAnthropic.model_fields` 36개는 어느 프로브도 세지 않으므로 `temperature`의 수용과 거부만 다시 쟀다고 고쳤다.
10. [명세 Minor] 명세 "계약"의 "스토리·테스트·e2e 스택의 매니페스트 리터럴에 `null`". 두 e2e 스택은 매니페스트를 TOML 문자열로 쓴다(`web/apps/admin/e2e/stack.ts`의 `manifest`와 `web/apps/widget/e2e/plugins.ts`의 `manifest`를 읽었다). e2e 스택을 그 문장과 계약 묶음에서 빼고 격리 루트 절로 보냈다.
11. [명세 Nit] ADR 0040 이력의 "클라이언트는 첫 호출에서 만들어진다"를 "만들 때 클라이언트를 만들지 않는다(쟀다). 첫 호출에서 생기는 것은 코드를 읽은 `cached_property`"로 갈랐다.
12. [명세 Nit] "실제 모델 호출 하나"가 무엇인지를 적었다. `tests/test_main.py`의 calc 시험에 드는 단언이고, 나머지 `-m llm` 시험(그 파일의 다른 다섯, `tests/core/test_model.py`의 하나. `pytest.mark.llm`을 grep했다)은 수가 늘지 않는다.
13. [인용 대조] `tools/check_quotes.py`의 경고 다섯(모두 `spec.md`). 제안 문구 둘은 코드 스팬으로, 풀어 쓴 둘은 따옴표를 떼고, 선례 시험 이름은 실제 함수 이름 `test_정한_이름이_그대로_모델_인스턴스에_닿는다`로 옮겼다. 앞 세션의 "이 브랜치의 파일에는 없다"는 셀프 리뷰 전의 판을 본 것이었다.

남긴 것은 하나다. [표준 Minor, 명세 Nit] Implementation Decisions의 구현 파일 경로(`adapters/anthropic.py`, `adapters/filesystem.py`, `main.py`, `sdk/ids.py`, `PluginList.tsx`, 두 `stack.ts`). 보류한다. ADR 0040과 설계 일지가 든 경로를 옮긴 것이고, 선례 명세도 같이 적었으며(`mcp-shutdown`이 `core/run.py`·`main.py`, `web-widget`이 `core/run.py`. grep으로 봤다), to-spec 스킬이 그 리뷰를 오탐으로 적어 두었다(대기열 30).

서두의 수를 다시 셌다. 넘겨받은 것 12, 사용자가 고른 것 1, 절 제목의 "명세가 정했다" 11, 이력 1, "거부한 안:" 표시 13(서두 설명 줄 제외)으로 서두와 같다.

다시 돌린 명령: `ruff check`·`ruff format --check`(프로브 폴더, 초록), 프로브 `build_without_key.py` 두 번(위 6), `tools/check_md_tables.py`·`check_line_separators.py`·`check_adr_pointers.py`(0), `check_quotes.py`(경고 0. 13을 고친 뒤). 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다. pyright의 `include`는 `src`·`tests`·`tools`라 프로브는 대상이 아니다.

PR 직전 리뷰에 밀 주장(이 반영으로 새로 쓴 사실 문장): "두 e2e 스택은 매니페스트를 TOML 문자열로 쓰므로 생성 타입이 닿지 않고", "없다는 코드의 기본값이 사라져 새로 드는 갈래다", "나머지 `-m llm` 시험(`tests/test_main.py`의 다른 다섯, `tests/core/test_model.py`의 하나)은 수가 늘지 않고", "중앙 0.1ms, 최대 0.3ms", "호출 뒤에는 `_async_client`가 `__dict__`에 있다(2회 모두, 탐침이 찍었다)", "36개는 어느 프로브도 다시 세지 않았다".

## ADR 0040 이력 승인

셀프 리뷰를 반영한 뒤 ADR 0040의 2026-10-31 이력 초안(명세가 정한 넷과 잰 것 하나. 본문의 포인터는 기존 하나에 이 세션이 둘을 더해 셋)을 사용자에게 보였다(작업 규약 5). 질문은 "ADR 0040의 2026-10-31 이력 초안(위 인용문)을 이대로 승인할까요? 승인하면 커밋하고 PR 직전 리뷰, PR, 봇 회차, 병합까지 묻지 않고 진행합니다."였고, 답은 이렇다.

> 사용자: 승인한다 (Recommended) — 이력 초안과 본문의 포인터 셋(기존 하나에 이 세션이 둘을 더했고 grep으로 셋을 확인했다)을 이대로 둔 채 커밋하고, merge.md의 규약대로 PR과 병합까지 묻지 않고 이어서 진행합니다.

고르지 않은 선택지는 "고쳐서 다시 보여 달라"(고칠 점을 적어 주시면 이력과 명세를 그에 맞게 고친 뒤 다시 보여 드리고, 그 전에는 커밋하지 않습니다)였다. 첫 호출은 선택지 설명의 사실을 대 보라는 훅에 막혔고, 포인터 수를 grep으로 센 뒤 같은 질문과 라벨로 다시 물었다.
