# 2026-11-03 (03) skill-plugin 명세

## 사용자 프롬프트 원문

> 사용자: .claude/skills/to-spec/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자:
>
> 다음 작업: 기능 skill-plugin. 스킬을 실행마다 읽어 컨텍스트로 넘기는 플러그인으로 정한 설계(ADR 0041, PR #457로 병합)의 명세
> 다음 단계: 명세
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 skill-plugin-spec)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /to-spec
> 브랜치: docs/skill-plugin-spec
> 모델: Fable 5.1 / xhigh
> 읽을 것: docs/journal/2026-11-03-02-skill-plugin-design.md의 "다음" 절(명세가 정할 것 여섯: 머리말을 본문에서 떼는 자리, yaml.YAMLError를 PluginError로 바꾸는 층, 스킬 문서 단건 읽기의 시그니처와 돌려주는 값의 자리, 예시 스킬의 이름과 본문, 머리말 두 칸의 값이 문자열이 아닐 때의 거부, 깨진 SKILL.md가 PluginError로 서고 문구에 원문이 없음을 고정하는 시험)과 "봇 회차 (셋째 세션)" 절, docs/adr/0041-skill-is-a-plugin-read-per-run-into-the-context.md
> 이어받을 상태: 봇 회차(claude-review 첫·둘째 회차)의 Minor 둘이 승인된 ADR 0041 본문을 바꾸지 않고 명세로 넘어왔다. 하나는 yaml.YAMLError를 PluginError로 바꾸는 층을 sdk 안 예외로 정하자는 것이고, 다른 하나는 read_skill이 sdk의 Skill을 돌려준다고 정하자는 것이다(원문을 돌려주고 core가 파싱하면 core가 import yaml을 하게 된다). 명세가 두 질문을 한 번에 받아 정하고 결과를 ADR 0041 이력과 ADR 0012 이력에 쌓는다. 이력을 쌓는 ADR 수정은 사용자 승인이 필요하다. 명세 브랜치 선례는 docs/<slug>-spec.
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: 명세 작성과 PR·병합까지

첫 턴에 `tidy-checkouts`를 돌고 `EnterWorktree(skill-plugin-spec)`로 들어가 `docs/skill-plugin-spec` 브랜치를 땄다(origin/main 2ba2780d). 세션 제목은 브랜치 이름으로 붙였다.

## 선택 화면 (명세를 쓴 뒤)

명세 초안을 쓴 뒤 to-spec의 이음매 확인과 예시 스킬의 갈래를 선택 화면 하나로 물었다. 묻기 전에 "시험을 붙이는 자리(이음매)"를 어느 층에 가짜를 꽂고 어느 층의 바깥 행동을 단언할지로 풀었다. 고른 라벨과 설명은 글자 그대로다.

- "스킬 기능의 시험을 주로 어디에 붙일까요?" → **런타임에 가짜 저장소를 꽂는다 (Recommended)**. 설명: "core의 run()·resume()에 가짜 플러그인 소스를 꽂아 준비 순서, 오류 문구, 컨텍스트에 실린 스킬 열, 읽은 횟수를 잽니다(지금 가짜 소스가 매니페스트·모델 읽은 횟수를 세는 것과 같은 길). 파일을 만들지 않아 빠르고 결정적입니다. 바깥 경계(sdk의 읽는 함수, 실제 폴더 어댑터, HTTP 두 면, 관리 화면, calc 프롬프트)는 기존 시험 자리에 얇게 하나씩 더하고, 실제 모델 호출은 기존 calc 시험에 단언 하나만 더합니다. 모델 플러그인 명세가 고른 자리와 같습니다." 고르지 않은 둘: "실제 폴더를 만들어 어댑터까지 돌린다"(임시 폴더에 `plugin.toml`과 `SKILL.md`를 실제로 쓰고 실제 어댑터로 `run()`을 돌린다. 파일 읽기까지 한 번에 보지만 결함 둘을 함께 심는 사례를 파일로 꾸미기가 번거롭고 읽은 횟수는 어댑터를 감싸야 셀 수 있다. 얼마나 느린지는 재지 않았다, 어림), "HTTP 요청을 넣어 응답으로만 본다"(상태 코드와 봉투로만 잰다. 컨텍스트의 열이나 읽은 횟수는 응답에 나오지 않아 잴 수 없고 준비 순서도 오류 문구로만 가늠한다).
- "저장소에 둘 예시 스킬(calc가 고르는 하나)은 어느 것으로 할까요?" → **답 형식 스킬 (answer-format) (Recommended)**. 설명: "본문 세 문장: 답은 값 하나만 쓴다, 단위·설명·계산 과정을 붙이지 않는다, 계산할 수 없으면 왜 할 수 없는지 한 문장으로 답한다. calc의 머리 문장 "최종 답만 짧게 답한다"(지금 코드)와 같은 방향이라 실제 모델 시험의 답이 바뀌지 않을 것으로 봅니다(돌려 보지 않았다, 어림). 본문이 짧아 프롬프트가 조금만 큽니다." 고르지 않은 것: "한국어 계산 요청 읽기 스킬 (korean-arithmetic)"(더하기·빼기·곱하기·나누기·제곱·나머지·퍼센트·우선순위를 연산으로 옮기는 규칙. 본문이 길어 프롬프트가 커지고 규칙이 모델의 답을 바꿀 여지가 있어 실제 모델 시험을 다시 봐야 할 수 있다. 돌려 보지 않았다, 어림).

선택 화면의 설명에 든 사실은 띄우기 전에 대 봤다. 모델 플러그인 명세의 이음매 절(`.scratch/model-plugin/spec.md` "이음매 (사용자가 골랐다)")이 같은 자리를 골랐고, `tests/core/test_run.py`의 `FakePlugins`가 `manifest_reads`·`model_reads`·`disabled_reads`를 세며, calc의 머리 문장은 `plugins/agents/calc/agent.py`의 `PROMPT` 그대로다. 첫 호출은 훅이 막아(처음 뜨는 선택 화면의 사실 확인) 대 본 뒤 어림을 적어 다시 띄웠다.

## 명세가 정한 것 (인계 전까지)

- 명세 `.scratch/skill-plugin/spec.md`(Status ready-for-agent)를 썼다. 서두의 셈은 넘겨받은 것 열하나, 사용자가 고른 것 둘, 명세가 정한 것 열셋, 이력 둘, 거부한 안 스물넷이다. 셈은 세션 스크래치패드의 일회성 스크립트로 세었다(`거부한 안:` 24, `(명세가 정했다` 12에 예시 스킬 절의 "엮는 모양은 명세가 정했다" 1).
- 봇 회차가 보류한 둘의 답. `yaml.YAMLError`를 바꾸는 층은 sdk다 — `parse_skill(text) -> Skill`이 그것을 고정 문구의 `ValueError`(`머리말이 YAML로 읽히지 않는다: <오류 종류> (줄 N, 칸 M)`)로 바꿔 던지고, 어댑터의 `read_skill`은 매니페스트의 `_parse`와 같은 집합을 잡아 `PluginError`를 만든다. 포트는 `read_skill(name: PluginName) -> Skill | None`이고 sdk의 `Skill`(frozen dataclass, `name`·`description`·`body`)을 돌려준다.
- 그 밖에 명세가 정한 것 열하나는 명세 서두의 목록이다. 줄 단위 `---` 가르기, strict pydantic 두 칸, 읽지 못한 문구와 이름 어긋남 문구, `skills`의 중복 거부, 준비 순서와 없음의 문구 둘, `AgentContext.skills: tuple[Skill, ...]`, calc의 `지침 <이름>:` 블록, sdk 밖의 `yaml` import를 막는 import-linter 계약, 고칠 자리의 묶음 넷(계약과 읽기 → 런타임·관리 화면 → 예시), 실제 모델 호출은 `tests/test_main.py`의 calc 시험에 단언 하나.
- 근거의 종류. 쟀다: `.scratch/skill-plugin/probes/frontmatter_split.py`(16회차), `frontmatter_values.py`(19회차), 설계의 `yaml_frontmatter.py`. 원문을 읽었다: Agent Skills 표준 페이지(https://agentskills.io/specification)와 참조 구현 `skills-ref`의 `parser.py`·`validator.py`(github `agentskills/agentskills` main, 내장 브라우저), 설치된 PyYAML 6.0.3의 `yaml/scanner.py` `check_document_start`와 네 모듈(`scanner`·`parser`·`composer`·`constructor`)의 `%r` 자리(스크래치패드 스크립트로 훑었다). 코드를 읽었다: `core/run.py`의 `_prepare`·`_resolve_servers`·`_reject_disabled`, `adapters/filesystem.py`의 `_parse`·`_describe`·`read_manifest`, `tests/core/test_run.py`의 `FakePlugins`, `tests/test_main.py`의 `_copy_repo_plugins`, `web/apps/widget/e2e/plugins.ts`의 `copyRepoPlugins`, `tests/test_plugins_boundary.py`(`*.py`만 읽는다), `pyproject.toml`의 import-linter 계약. 어림: 매니페스트의 BOM을 `tomllib`이 거부하는지, 실제 폴더를 주 이음매로 썼을 때 얼마나 느린지, 예시 스킬로 모델의 답이 바뀌지 않는지.
- 용어와 이력. `CONTEXT.md`에 "스킬 문서" 용어를 더했다(머리말 정의가 이미 쓰던 말). ADR 0041에 `## 이력`과 2026-11-03 이력 "명세가 머리말 가르기와 두 칸의 모양, 바꾸는 층, 포트의 시그니처, 예시 스킬을 정했다"를 쓰고 본문 문장 여섯에 포인터를 달았다(웹 요약을 원문과 대 보지 않았다는 문장, 거부 조건 문장, 떼는 자리, 바꾸는 층, 시그니처와 값의 자리, 예시 스킬의 이름과 본문). ADR 0012에 같은 날 둘째 이력 "`read_skill`은 이름을 받아 sdk의 `Skill`을 돌려주고 없으면 `None`이다"를 썼다. `uv run python tools/check_adr_pointers.py`와 `tools/check_line_separators.py`가 초록이었다. `tools/check_md_tables.py`도 초록이라 적었으나, 넷째 세션의 셀프 리뷰 표준 축이 돌리니 `.scratch/plan.md` 6행에 적은 `Skill | None`의 `|`가 표의 칸을 깨어 빨강이었다(아래 "셀프 리뷰 (넷째 세션)"). `.scratch/plan.md`의 6행에 명세와 측정의 경로, 고른 것과 정한 것을 적었다. 두 ADR 이력은 아직 사용자 승인을 받지 않았다(셀프 리뷰를 반영한 뒤 보여 준다).

## 이 세션이 번복하거나 고친 것

- 프로브 `frontmatter_split.py`의 첫 판은 머리말 안의 `---` 줄을 큰따옴표 스칼라 한 자리만 쟀는데, 명세가 그것을 "유효한 머리말 안에 있을 수 없다"로 넓혀 썼다. 프로브를 인용하는 문서의 계기 훅에 따라 블록 스칼라와 평문 스칼라의 이어지는 줄 두 자리를 더해 14회차에서 16회차로 다시 쟀고(둘은 `ComposerError`), 까닭은 스캐너의 `check_document_start`를 읽어 적었다. README의 그 절에 결과를 본 뒤 바꾼 것으로 적었다.
- `frontmatter_values.py`의 받는 회차에 `compatibility`를 더했다. 명세가 표준의 선택 칸 넷이 무시된다고 적는데 첫 판은 셋만 넣었다. 19회차 그대로다.
- 명세의 거부한 안 수를 열다섯에서 스물넷으로 고쳤다(손으로 센 수가 틀려 스크립트로 셌다). "500줄 권고"를 원문과 같았다는 목록에서 뺐다(이 세션이 원문에서 대 보지 않았다). `problem` 문구가 원문의 글자를 든다는 근거를 `scanner.py` 한 파일에서 네 모듈의 `%r` 자리로 고쳐 적었다.
- 선택 화면의 첫 호출은 훅이 막았다(처음 뜨는 화면의 사실 확인). 모델 플러그인 명세의 이음매, 가짜 소스의 읽은 횟수, calc의 머리 문장을 대 본 뒤 돌려 보지 않은 것에 어림을 적어 다시 띄웠다.

## 인계 (셀프 리뷰 직전)

셀프 리뷰 직전의 계기 훅이 세션 컨텍스트 304,771 토큰으로 문턱을 넘었다고 알렸다. 곁 세션이 아니고(`get_session self`에 `parentSessionId`가 없다) 요청 범위가 병합까지라 인계한다. 셀프 리뷰는 새 세션이 한다. 이 세션의 제목은 `docs/skill-plugin-spec`이었고 `docs/skill-plugin-spec (인계함)`으로 바꾼다. 주 체크아웃은 main 2ba2780d이고 `git fetch origin` 뒤 `origin/main`과 같다(`git worktree list`와 `git rev-parse origin/main`으로 봤다). 이 세션이 띄운 백그라운드 작업은 없다.

지시문:

```
다음 작업: 기능 skill-plugin. 스킬을 실행마다 읽어 컨텍스트로 넘기는 플러그인으로 정한 설계(ADR 0041, PR #457로 병합)의 명세
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/skill-plugin-spec
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-03-03-skill-plugin-spec.md 전체(선택 화면의 답, 명세가 정한 것, 이 세션이 고친 것), .scratch/skill-plugin/spec.md, .scratch/skill-plugin/probes/README.md의 명세 세션 두 절, docs/adr/0041-skill-is-a-plugin-read-per-run-into-the-context.md의 "## 이력"과 docs/adr/0012-ports-stay-five-lists-are-added.md의 2026-11-03 둘째 이력(승인받을 초안)
이어받을 상태: 인계: 셀프 리뷰 직전 docs/journal/2026-11-03-03-skill-plugin-spec.md. 커밋하지 않은 변경이 워크트리 C:/project/agent/.claude/worktrees/skill-plugin-spec에 있고 셀프 리뷰(/code-review origin/main)부터 한다. 변경은 명세 .scratch/skill-plugin/spec.md(새 파일), 프로브 둘 .scratch/skill-plugin/probes/frontmatter_split.py·frontmatter_values.py(새 파일)와 그 README.md, CONTEXT.md의 용어 "스킬 문서", ADR 0041의 포인터 여섯과 새 "## 이력" 절, ADR 0012의 2026-11-03 둘째 이력, .scratch/plan.md의 6행, 이 일지다. 두 ADR 이력 초안은 아직 사용자 승인을 받지 않았다. 셀프 리뷰를 반영한 뒤 보여 주고 승인받는다(CLAUDE.md 작업 규약 5). 사용자가 고른 둘(core에 가짜 플러그인 소스를 꽂는 이음매, 예시 스킬 answer-format)은 일지의 선택 화면 절에 글자 그대로 있다. 남은 단계는 to-spec의 순서대로 셀프 리뷰 반영 → 서두의 수 다시 세기 → ADR 이력 승인 → 커밋(커밋 전 git branch --show-current와 uv run python tools/sibling_overlap.py) → 일지 마무리(결과와 근거의 종류, "다음") → PR 직전 리뷰 → /git-pr → 봇 회차 → 병합은 이 워크트리 사본의 next-session merge.md "워크트리에서 병합할 때" → next-session(다음은 to-tickets)
확인할 선행 조건: 없음
이번 요청 범위: 명세 작성과 PR·병합까지
```

제목을 `docs/skill-plugin-spec (인계함)`으로 바꿨고 `git worktree unlock`이 조용히 끝났다. open-session을 부른다 2026-11-03T10:10:16Z

## 셀프 리뷰 (넷째 세션)

인계 지시문으로 연 넷째 세션이다. 제목을 `docs/skill-plugin-spec`으로 바꾸고, `git worktree list`에서 브랜치가 체크아웃된 워크트리 `skill-plugin-spec`에 `EnterWorktree(path)`로 들어갔다. `git fetch origin` 뒤 HEAD와 `origin/main`이 같은 `2ba2780d`였다(손으로 봤다).

본 범위: base `2ba2780d`, 변경 파일 5(`.scratch/plan.md`, 프로브 README, `CONTEXT.md`, ADR 0012, ADR 0041), 커밋 0, 미추적 4(명세, 프로브 둘, 이 일지). 표준 축은 sonnet·high, 명세 축은 이 세션의 모델. 두 브리프에 표준 페이지와 참조 구현 `parser.py`·`validator.py`의 발췌와 URL을 실었고, 참조 구현 원문 둘을 `curl`로 세션 스크래치패드에 내려받아 두 축이 그 사본으로 대 봤다(명세 축이 그렇게 적었다).

### 표준 축 보고 (sonnet·high)

도구: `check_md_tables.py`는 실패(`.scratch/plan.md:25: 칸 6, 머리 행 5`), `check_line_separators.py`와 `check_adr_pointers.py`는 통과. 프로브 둘은 다시 돌려 16회차와 19회차, 측정 아님 0.

1. [Major, 하드] 명세 "읽지 못한 문구" 절의 닫힌 주장. `parse_skill`이 `yaml.YAMLError`만 바꾸는데 `yaml.safe_load`는 `YAMLError`가 아닌 예외를 낸다. 손으로 쳐 봤다. `description: !!int sk-ant-probe-secret`는 값이 든 `ValueError`이고 어댑터 `_describe`가 `str(error)`를 그대로 싣는다. `!!bool`은 `KeyError`, `!!timestamp`는 `AttributeError`라 `except (OSError, ValidationError, ValueError)` 밖으로 나간다. 프로브는 이 길을 재지 않았다. 사용자 이야기 12의 약속이 깨진다.
2. [Major, 도구가 판정] `.scratch/plan.md` 6행에 늘어난 문장의 코드 스팬 `Skill | None`이 표를 깬다. 일지는 `check_md_tables`가 초록이라 적었으니 그 문장도 거짓이다.
3. [Minor, 출처] ADR 0041 이력은 "PR 직전 리뷰가 보류한 둘", ADR 0012 이력은 "PR 직전 리뷰가 짚었다"고 적는다. 일지 665행 이후를 보면 보류한 것은 PR 봇 claude-review(셋째 세션)다. 바꾸는 층은 CLI(PR 직전 리뷰)가 냈고 값의 자리는 봇이 냈다. 명세 서두("봇 회차")와도 어긋난다. 이력 서두의 "넘긴 넷"과 "보류 둘"은 겹친다.
4. [Minor, 하드] ADR 0041 이력과 명세 Out of Scope가 "패턴이 보지 않는 것(연속 하이픈, 64자)"이라 적는다. 패턴 `^[a-z][a-z0-9-]{1,62}$`는 64자를 거부하고 끝 하이픈은 통과시킨다. ADR 0041 본문 26행과 어긋난다.
5. [Minor] 로컬 `skills-ref` 사본에서 `parser.py`는 `strictyaml`을 쓰고 `validator.py`는 `ALLOWED_FIELDS`로 모르는 키를 거부하며 NFKC 정규화도 한다. 명세는 "원문을 읽었다"면서 모르는 키를 허용하는 결정과 부딪히는 이 사실을 적지 않았다.
6. [Minor, 프로브] `split_front_matter`는 `rstrip("\r")`로 여러 개를 떼는데 규칙은 "하나"다. 세 자리 회차는 `YAMLError` 종류만 보고 README가 든 Scanner/Composer 종류를 단언하지 않는다. `---` 줄을 뺀 입력이 통과하는 대조도 없다. README는 근거 자리를 "절 셋"이라 적었는데 바꾸는 층 절도 `frontmatter_values.py`를 인용한다.
7. [Minor] 규칙은 "본문은 글 그대로"인데 어댑터의 `read_text`는 CRLF를 LF로 바꾼다.
8. [Nit] plan.md는 "명세가 정한 열셋"이라 쓰고 괄호에는 열둘만 있다. 명세 Solution에 `_Avoid_`인 "스킬 파일"이 있다. 고칠 자리 묶음은 구현 경로를 나열하는데 "ADR이 든 경로는 옮겨 적는다"는 예외는 to-spec에 없는 명세 자체의 예외다. 냄새(판단): ADR 0041 이력이 문구를 명세와 이중으로 들어 Duplicated Code 가능성.

주장 검증에서 맞은 것: 서두의 수, 프로브 회차와 README 결과 문장, 열거한 테스트 이름과 식별자, `_prepare` 순서, `mcp` 중복이 조용히 하나가 됨(실제 호출), `YAMLError`는 `ValueError`가 아니고 TOML·pydantic 오류는 그 하위, `ReaderError`에 `problem_mark` 없음, 설치된 판 둘, `langchain-core`가 pyyaml을 끌어옴, sdk 계약 넷에 `yaml` 없음, `src`에 `import yaml` 0, 스킬이 다른 종류의 칸을 쓰면 전부 거부, ADR 0008 이력 실재, 두 ADR의 새 이력 제목 구분. 대 보지 못한 것: 스크래치패드의 `%r` 훑기, 내장 브라우저로 읽었다는 것(로컬 사본과 발췌는 일치), 500줄 권고.

### 명세 축 보고 (이 세션의 모델)

- (a) [Minor] plan.md 6행 "명세가 정한 열셋"의 나열이 열둘이고(sdk의 `Skill`·`parse_skill`이 "바꾸는 층"에 합쳐짐), "묶음 넷(계약과 읽기 → 런타임·관리 화면 → 예시)"이 명세의 의존(A→B, A→C, B→D. C→D 없음)과 다르다.
- (b) [Minor] `skills` 중복 거부(sdk 검증자, 새 문구). ADR 0041은 "`mcp = [...]`와 같은 모양"으로만 정했고 넘긴 넷·보류 둘에 없다. 계약 규칙이 하나 느는 것이라 ADR 이력 승인 때 따로 짚을 것.
- (c)1 [Minor, 가장 심각] ADR 0041 이력 "PR 직전 리뷰가 보류한 둘"과 ADR 0012 이력 "(PR 직전 리뷰가 짚었다)". 일지는 '어느 층' 질문을 PR 직전 리뷰가 냈고, 둘의 보류와 "core가 `import yaml`" 논증은 봇 회차로 적는다. 또 ADR 본문은 바꾸는 층도 명세가 정한다로 넘겼으니 넘긴 것은 넷이 아니라 다섯이다.
- (c)2 [Minor] ADR 0041 이력 "계산할 수 없으면 한 문장으로 답한다" — 사용자 답·명세는 "왜 할 수 없는지 한 문장으로".
- (c)3 [Minor] 명세 "예시 스킬" 절 "같은 방향이라 모델이 다른 답을 내지 않는다" — 사용자 답은 어림인데 단정이 됐다.
- (c)4 [Minor] "이음매" 절 "바깥 경계는 … 얇은 시험 하나씩" vs "시험할 모듈" sdk 항목(프로브 사례 전부)과 스토리 24. 사용자 답 "sdk의 읽는 함수 … 얇게 하나씩"과 다르다. 의도면 sdk가 예외라고 적을 것.
- (c)5 [Nit] "다른 멤버의 열이 모두 `tuple`" — 컨텍스트에 열 멤버는 `Conversation.exchanges` 하나다.
- (c)6 [Nit] ADR 0012 첫 이력의 "명세가 정한다" 문장에 둘째 이력 포인터가 없다.

주장 검증에서 맞은 것: 넘겨받은 열하나와 ADR Consequences, 서두의 수, "지금의 순서"와 `_prepare`(순서 시험 10개 통과), 줄·칸 계산(프로브를 돌렸다), calc 머리 문장 인용 둘, 묶음 넷이 ADR "고칠 곳"을 빠짐없이 덮음, `tests/test_main.py:551`의 실제 모델 시험이 `LlmCalled`를 읽고 `plugins/` 전체를 복사, Out of Scope 받는 쪽 없음, ADR 0012 첫 이력·ADR 0008 이력 옮김, 참조 구현 인용 여섯(스크래치패드 원문), 경로 14개와 계약 이름 둘과 sdk 밖 층 일곱. BOM 어림은 `tomllib.loads`가 BOM 글을 거부하는 것을 손으로 봐 어림 표기가 맞았다. 보류의 걱정(날것 `YAMLError`의 500 유출)은 `failure_for`가 `str(error)`만 싣고 HTTP 층에 traceback 기록이 없어 닫힌다. 잔존 0.

### 판정과 반영

표준 1(Major)은 고쳤다. 네 태그를 `uv run python -c`로 다시 쳐 같은 결과를 봤고(손으로 봤다. `!!float`도 값이 든 `ValueError`였다), `frontmatter_values.py`에 태그 회차 넷과 `!!python` 태그의 `ConstructorError` 대조 하나를 더해 쟀다(24회차, 측정 아님 0). 명세 "바꾸는 층" 절을 `parse_skill`이 `yaml.safe_load` 호출 하나를 `except Exception`으로 감싸 모든 예외를 고정 문구 `ValueError`로 바꾸는 것으로 고치고, 문구는 종류만이 기본이고 `MarkedYAMLError`에만 줄·칸이 붙게 했다. 거부한 안에 "`YAMLError`만 잡는 것(첫 판)"을 더해 스물다섯이 됐다. ADR 0041 이력의 셋째 불릿과 "sdk의 스킬 값" 절, "읽지 못한 문구" 절의 닫힌 주장(이제 참이 됐다), 시험 둘을 함께 고쳤다. 표준 2(Major)는 plan.md의 `Skill | None`을 말로 풀어 고치고 이 일지의 틀린 문장을 고쳤다(`check_md_tables.py` 초록, 손으로 돌렸다). 표준 3과 명세 (c)1은 설계 일지의 "PR 직전 리뷰"·"다음"·"봇 회차 (셋째 세션)" 절을 읽어 두 ADR 이력의 주체를 고쳤다. 명세 축의 "넷이 아니라 다섯"은 받지 않았다(이 판정은 틀렸다. 아래 "PR 직전 리뷰 (넷째 세션)"). ADR 0041 본문에 "명세가 정한다"로 미룬 문장은 셋(떼는 자리, 시그니처와 값의 자리, 예시 스킬)과 "묶음으로 나누는 것은 명세" 하나로 넷이고(grep으로 봤다), 바꾸는 층은 본문이 아니라 설계 일지 "다음"이 넘겼다. 그래서 이력 첫 문단을 "넘긴 넷, PR 직전 리뷰가 낸 하나, 보안 리뷰가 더한 둘, 봇이 ADR에서 닫으라 했으나 셋째 세션이 보류한 둘의 답"으로 썼다. 표준 4는 `sdk/ids.py`의 패턴을 읽어 명세 둘(거부한 안, Out of Scope)과 ADR 0041 이력을 "끝 하이픈, 연속 하이픈"으로 고쳤다. 표준 5는 내려받은 원문(`parser.py`의 `import strictyaml`, `validator.py`의 `ALLOWED_FIELDS` 여섯과 NFKC)을 읽어 명세 서두와 "두 칸" 절, README의 갈래 불릿에 사실로 적었다(결정은 ADR 0041 그대로다). 표준 6은 프로브의 표지 줄 판정을 `\r` 하나만 떼는 `_is_marker`로 바꾸고 `---\r\r\n` 거부 회차, 세 자리의 클래스 단언, `---` 줄만 뺀 대조 셋을 더했으며 README의 "절 셋"을 넷으로 고쳤다. 표준 7은 `adapters/filesystem.py` `_parse`의 `read_text(encoding="utf-8")`를 읽고 프로브에 파일 회차 셋(CRLF→LF, BOM 남음, 매니페스트의 BOM을 `tomllib`이 거부)을 더해 쟀다(23회차, 측정 아님 0). 명세 "떼는 규칙"에 어댑터의 읽기 길 불릿을 더했고 BOM 어림을 측정으로 바꿨다. 표준 8 가운데 plan.md의 열셋 목록과 "스킬 파일"→"스킬 문서"(명세 Solution)는 고쳤다. ADR 0041 본문의 같은 낱말은 승인된 글이라 두었다. 명세 (a)1은 plan.md의 묶음 의존을 "A → B와 C, B → D"로 고쳤다. 명세 (c)2·(c)3·(c)5는 글자대로 고쳤다. 명세 (c)4는 "이음매" 절에 sdk의 `parse_skill`과 머리말 모델만 프로브 사례 전부로 시험하는 예외를 밝혔다. 사용자가 고른 답을 그 함수에서 넓힌 자리라 승인 때 짚는다.

남긴 것과 이유. 명세 (b)1 `skills` 중복 거부: 명세가 넘겨받은 것 안에서 정한 것으로 서두와 ADR 0041 이력 "명세가 더 정한 것"에 이미 있다. 매니페스트 검증 규칙 하나가 느는 계약 변경이라 ADR 이력 승인 때 사용자에게 따로 짚는다. 표준 8의 고칠 자리 묶음의 구현 경로: ADR 0041 "구현 티켓이 고칠 곳"이 원천이고 to-tickets가 항목을 이름으로 받아야 해 두었다(명세가 그 예외를 절 머리에 밝힌다). 표준 8의 이력 중복 냄새: `.claude/rules/adr.md`가 명세가 정한 것을 그 ADR의 이력에 적으라 하므로 두었다. 명세 (c)6: 같은 규칙의 "달지 않는 것: 앞의 이력을 바꾼 뒤의 이력(지난 이력 항목은 기록이다)"이라 두었다.

### 반영으로 새로 쓴 문장 (PR 직전 리뷰에 밀 주장)

1. 명세 "바꾸는 층": `yaml.safe_load`가 내는 예외는 `YAMLError`만이 아니다 — 명시적 태그(`!!int`, `!!float`, `!!bool`, `!!timestamp`)의 값 변환이 실패하면 변환 함수의 `ValueError`·`KeyError`·`AttributeError`가 그대로 올라오고, 앞의 셋은 `str`에 운영자가 적은 값을 싣는다. 넓은 `except`의 선례는 어댑터의 진입점 import `_import`다.
2. 명세 "떼는 규칙": 어댑터는 스킬 문서를 매니페스트와 같은 길(텍스트 모드 `read_text(encoding="utf-8")`)로 읽는다. 그 길은 파이썬의 보편 줄 바꿈이라 CRLF 파일의 줄 끝이 `parse_skill`에 닿기 전에 `\n`이 된다. BOM은 그 길로 읽어도 U+FEFF가 첫 글자로 남아 거부된다. 매니페스트도 BOM 뒤의 TOML을 `tomllib`이 거부한다. `\r`이 둘이면 표지 줄이 아니다.
3. 명세 "두 칸": 참조 구현의 `validator.py`는 표준의 여섯 칸 밖의 키를 거부하고 `name`을 NFKC로 정규화한다. 저장소 `.claude/skills` 가운데 다섯이 쓰는 `disable-model-invocation`이 참조 구현의 검증을 지나지 못하는 예다. 패턴이 ASCII 소문자만 받으므로 전각 글자처럼 정규화해야 맞는 이름은 그대로 거부된다. 참조 구현은 머리말 읽기에 strictyaml을 쓰고 이 가르기는 라이브러리와 무관하다.
4. 명세 "거부한 안"·Out of Scope·ADR 0041 이력: 패턴이 보지 않는 것은 끝 하이픈 금지와 연속 하이픈 금지이고, 64자 이름은 패턴이 63자까지라 이미 받지 않는다.
5. 명세 "이음매": sdk의 `parse_skill`과 머리말 모델은 얇은 하나가 아니라 프로브 두 파일의 사례 전부를 같은 입력으로 시험한다. 사용자가 고른 답은 sdk의 읽는 함수도 "얇게 하나씩"에 넣었는데 이 명세가 그 함수만 이렇게 넓혔다.
6. ADR 0041 이력 첫 문단: 설계 세션의 PR 직전 리뷰가 낸 하나(바꾸는 층), 둘째 세션의 PR 직전 보안 리뷰가 더한 둘, PR 봇 claude-review가 ADR에서 닫으라 했고 셋째 세션이 보류한 둘. ADR 0012 이력: PR 봇 claude-review가 짚었다.
7. README: 참조 구현은 머리말 읽기에 PyYAML이 아니라 strictyaml을 쓴다. `!!binary`는 틀린 글자를 버리고 bytes를 내 거부되지 않는다(손으로 봤다).
8. 명세 "예시 스킬": 고르지 않은 것은 규칙이 모델의 답을 바꿀 여지가 있어 그 시험을 다시 봐야 할 수 있었다(어림).

### 다시 돌린 명령

프로브 둘(`PYTHONUTF8=1 uv run python .scratch/skill-plugin/probes/frontmatter_split.py`·`frontmatter_values.py`): 23회차·24회차, 측정 아님 0. `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 1235 files already formatted. `uv run python tools/check_md_tables.py`·`tools/check_line_separators.py`·`tools/check_adr_pointers.py`: 출력 없이 종료 0. 서두의 수를 스크립트로 다시 셌다(`(명세가 정했다` 절 제목 12에 "엮는 모양은 명세가 정했다" 1, `거부한 안:` 25, 넘겨받은 것 (1)~(11), 사용자가 고른 절 둘). 손으로 치는 다섯은 커밋의 pre-commit으로 갈음하고 결과는 커밋 뒤에 적는다.

## ADR 이력 승인 (넷째 세션)

셀프 리뷰를 반영한 두 ADR 이력 초안(ADR 0041 "명세가 머리말 가르기와 두 칸의 모양, 바꾸는 층, 포트의 시그니처, 예시 스킬을 정했다", ADR 0012 "`read_skill`은 이름을 받아 sdk의 `Skill`을 돌려주고 없으면 `None`이다")을 보여 주며 따로 짚은 셋 — `skills`의 중복 거부가 매니페스트 규칙 하나를 더하는 계약 변경인 것, 사용자가 고른 이음매 답의 "sdk의 읽는 함수는 얇게 하나씩"을 명세가 프로브 사례 전부로 넓힌 것, `parse_skill`이 `yaml.safe_load` 호출 하나를 `except Exception`으로 감싸는 것 — 을 함께 물었다(2026-11-04).

> 사용자: 승인

셋 모두 그대로 간다.

## 커밋 (넷째 세션)

`git branch --show-current`는 `docs/skill-plugin-spec`. `uv run python tools/sibling_overlap.py`는 번호 겹침 없음(다음 빈 번호는 일지 `2026-11-04-01`, 대기열 565, 티켓 041). 종료 코드와 무관한 줄 둘: 형제 `agent-os-direction` 워크트리의 새 일지 2026-11-03-04가 이 일지 2026-11-03-03과 이름순으로 엇갈려 그쪽이 먼저 병합되면 이 일지를 옮긴다는 줄, `mcp-shutdown-spec` 워크트리가 `.scratch/plan.md`를 함께 고쳤다는 줄(나중에 병합하는 쪽의 글자 충돌 후보).

커밋 `dd0150b0`(파일 9, +845/-7). pre-commit: ruff 둘 Passed(프로브 `.py` 둘이 스테이지되어 `Skipped`가 아니다), 러너의 열(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 357초, web-verify 496초) 모두 Passed, 러너 전체 497초. 마크다운 표·줄 구분 문자·변이 표·인용 대조·커밋 메시지 Passed. 커밋 검사는 바뀐 아홉이 모두 면제 모양(일지, ADR, `CONTEXT.md`, `.scratch/plan.md`, 명세, 프로브)이라 지났다. `Skipped`는 카나리아 명세 모양과 헌법 판 둘이고 둘 다 `(no files to check)`다. 손으로 쳐 보니 카나리아 모양 검사는 명세 파일을 인자로 받는 도구라 인자 없이는 사용법만 찍고(종료 2), 이 커밋에 카나리아 명세가 없으며 저장소의 명세 전부는 pytest의 저장소 상태 시험이 보고 그 pytest가 지났다. 헌법 판은 `uv run python -m tools.check_constitution_version`이 "이 가지가 고친 헌법 파일이 없다"(종료 0). 손으로 치는 다섯은 이 pre-commit으로 갈음했고, `-m llm`·`-m llm_widget`·e2e·사진 비교는 코드를 건드리지 않아 해당 없다.

인용 대조 경고 17건(막지 않는다). 명세의 셋은 PyYAML의 오류 문구("found unexpected end of stream"), 구현 티켓이 `docs/constitution/tech.md`에 더할 런타임 의존성 줄(지금 `tech.md`와 `pyproject.toml`에 `pyyaml`이 없다, grep으로 봤다), 가짜 플러그인 소스가 흉내 낼 상황의 이름이라 저장소에 아직 없는 것이 맞다. 일지의 열넷 가운데 여덟은 선택 화면의 질문과 선택지 원문(저장소 밖), 셋(78행·91행·92행)은 셀프 리뷰 두 축의 보고가 고치기 전 문장을 인용한 것이라 이제 ADR 0041과 명세에 없는 것이 맞고, 셋(101행 둘, 103행)은 이 일지가 명세의 거부한 안과 ADR 0041 이력 첫 문단, `.claude/rules/adr.md`의 문장을 줄여 인용한 것이다. 원문과 다른 뜻으로 옮긴 것은 없다(하나씩 봤다).

## PR 직전 리뷰 (넷째 세션)

`coderabbit auth status`(CLI 0.7.5)에 `Seat:`·`Plan` 줄 없이 `Review access: Default njh6803/njh6803`만 보여(2026-11-03의 두 PR과 같은 모양) `coderabbit-review` 서브에이전트를 띄웠다(기준 `2ba2780d`, 커밋 `dd0150b0`, 미커밋은 이 일지뿐. 셀프 리뷰 반영으로 새로 쓴 문장 여덟을 밀 주장으로 브리프에 실었다). `coderabbit review --agent --include-untracked`가 `review_completed`, findings 2로 끝났고 아홉 파일을 훑어 CLI 축이 채워졌다. 대체 둘(`/security-review`, `bug-perf-review`)은 돌리지 않았다(리뷰 파이프라인 2).

### 보고

CLI 둘(모두 `frontmatter_split.py`)과 여덟 주장 대조에서 나온 넷. Critical·Major 없음.
1. [Minor] 평문 스칼라 갈래의 거부 입력(`앞\n---\n뒤`)과 대조(`앞\n  뒤`)가 `---` 줄만 다른 쌍이 아니다. 들여쓰기도 다르다.
2. [Minor] 참조 구현 `split("---", 2)` 갈래가 끊긴 자리만 보고 YAML이 낸 값(`{'name': 'pdf-processing', 'description': '가'}`)은 단언하지 않는다. README는 그 값을 `{'description': '가'}`로 줄여 적었다.
3. [Minor] ADR 0041 이력 첫 문단의 "넘긴 넷 + PR 직전 리뷰가 낸 하나". 본문 27행이 바꾸는 층도 "명세가 시그니처와 함께 정한다"로 넘겼으므로 본문이 넘긴 것은 다섯이다. 셀프 리뷰 판정(명세 축 (c)1을 물리친 "grep으로 봤다")이 틀렸다.
4. [Minor] `!!binary`가 "거부되지 않는다"는 항상 참이 아니다. base64 길이 규칙에 맞지 않거나(17자) ASCII 밖 글자면 `ConstructorError`다.
5. [Minor] `\r` 둘의 거부는 글을 직접 넘길 때만이다. 어댑터의 `read_text`가 `---\r\r\n`을 `---\n\n`으로 바꿔 받아들이고 홀로 선 `\r` 파일도 받아들인다. 명세의 어댑터 불릿은 CRLF만 말했다.
6. [Minor, 보류] 표준과 참조 구현은 유니코드 소문자 이름을 허락하는데 플러그인 이름 패턴은 ASCII뿐이고, 이 어긋남이 명세에 없다. 사용자 이야기 8의 "그대로 들이기"가 비ASCII 이름에서는 성립하지 않는다.

여덟 주장: 1·3·4·5·8 맞다. 2는 `\r` 둘 문장이 어댑터 경로에서 어긋난다(5). 6은 "넷 + 하나"가 어긋난다(3). 7은 `!!binary` 문장이 어긋난다(4). 오탐 둘: `parse_skill`의 `__cause__`에 남는 원본 예외(`src`에 `logging`·`traceback`이 없고 CLI와 HTTP 표가 `str(error)`만 싣는다), 단순 grep의 `disable-model-invocation` 일곱(둘은 주석 속 언급이라 다섯이 맞다). 대 보지 못한 것 둘: `yaml.safe_load`의 `Any`를 `isinstance`로 좁히는 것이 pyright strict와 원칙 III를 지나는지(워크트리 가드가 임시 pyright 설정 명령을 거부했다. 구현 티켓의 `uv run pyright` 몫), 사용자 승인 메시지의 원문.

### 판정과 반영

여섯 모두 근거를 먼저 봤다. 3은 ADR 0041 본문을 `어느 층이`로 grep해 그 문장을 확인했다(셀프 리뷰 때 `명세가 정한다`로 grep해 "명세가 시그니처와 함께 정한다"를 놓쳤다). 4는 세 값(16자, 17자, 한글)을 손으로 쳐 같은 결과를 봤다. 5는 `\r\r\n`이 보편 줄 바꿈에서 `\n\n`이 되는 것을 손으로 봤다. 여섯 모두 고치는 값이 작아 고쳤다(보류 6도 리뷰 파이프라인 2대로 확인을 기다리지 않았다).
- 1·2·5: `frontmatter_split.py` 셋째 판. 평문 갈래의 거부 입력을 들여쓴 줄 앞에 `---` 줄을 둔 쌍으로, 참조 구현 갈래가 YAML 값까지 단언하게, `\r` 둘과 홀로 선 `\r` 파일을 어댑터의 길로 읽는 회차 둘과 홀로 선 `\r` 글의 거부 대조 하나를 더했다(26회차, 측정 아님 0. 첫 실행에서 새 회차 둘이 측정 아님이었는데 기대한 머리말을 긴 `HEAD`로 써서였다. 짧은 `SHORT_HEAD`로 고쳤다. 표지 없는 회차를 세는 `Rounds`가 그대로 잡았다). README의 split 절(제목, 참조 구현 값, 세 자리 대조, 파일에서 읽는 길, 재지 않은 것, 셋째 판)과 명세 "떼는 규칙" 셋째 불릿에 어댑터 경로에서는 그 둘이 받아들여진다는 문장을 더했다.
- 3: ADR 0041 이력 첫 문단을 "본문이 명세에 넘긴 다섯(… 바꾸는 층(설계 세션의 PR 직전 리뷰가 냈고 본문이 명세에 넘겼다) …)"으로 고쳤다. 승인받은 글이라 병합 전에 다시 보인다. 이 일지의 셀프 리뷰 판정 문장에 틀렸다는 표시를 달았다.
- 4: `frontmatter_values.py` 독스트링과 README의 `!!binary` 문장을 좁혔다(손으로 봤다).
- 6: 명세 "두 칸" 절에 거부한 안(패턴을 유니코드 소문자로 넓히는 것)을, Out of Scope에 유니코드 이름을, 사용자 이야기 8에 "이름이 플러그인 이름 패턴에 맞을 때"를 더했다. 거부한 안 스물여섯.

### 다시 돌린 명령

프로브 둘 26회차·24회차, 측정 아님 0. `uv run ruff check .` All checks passed, `uv run ruff format --check .` 1235 files already formatted. `check_md_tables.py`(바뀐 문서 넷)·`check_line_separators.py`(바뀐 파일 여섯)·`check_adr_pointers.py` 종료 0. 서두의 수를 스크립트로 다시 셌다(정했다 13, 거부한 안 26, 넘겨받은 (1)~(11), 사용자가 고른 절 둘).

## 둘째 커밋 (넷째 세션)

`git branch --show-current`는 `docs/skill-plugin-spec`. `uv run python tools/sibling_overlap.py`는 첫 실행에서 종료 1이었다. 위 "커밋" 절이 다음 빈 번호로 적은 일지 `2026-11-04-01`을 어디에도 없는 일지 번호의 인용으로 잡아, 출력대로 코드 스팬에 넣고 다시 돌려 번호 겹침 없음(대기열 565·566·567은 이 브랜치의 새 번호). 종료 코드와 무관한 둘은 그대로다(agent-os-direction 워크트리의 일지 2026-11-03-04가 이 일지를 이름순으로 앞선다, mcp-shutdown-spec 워크트리가 `.scratch/plan.md`를 함께 고쳤다).

커밋 `6090fc31`(파일 7, +154/-45). pre-commit은 전부 Passed(병렬 검사 473초, pytest 324초, web-verify 473초), Skipped 둘(`no files to check`, 카나리아 모양·헌법 판). 헌법 판 검사는 `uv run python -m tools.check_constitution_version`으로 손으로 쳐 "이 가지가 고친 헌법 파일이 없다"였고, 카나리아 모양 검사는 커밋에 카나리아 명세가 없어 넘길 파일이 없다(대기열 567의 사건과 같은 꼴). 인용 대조 경고 5건: 대기열 566의 셀프 리뷰 지적 요약은 원문이 아니라 따옴표를 뗐다(셋째 커밋). 일지의 넷(101·145·156행)은 위 "커밋" 절에서 판정한 고치기 전 문장과 줄여 인용한 것이다.

셋째 커밋(일지의 이 절과 대기열 566의 따옴표)의 첫 pre-commit은 pytest에서 둘이 빨개 실패했다(2 failed, 6151 passed, 323초). `tests/channel/cli/test_interrupt.py`의 `test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다`는 자식이 쓰는 `cancelled` 파일을 아직 빈 채로 읽어 `float('')`의 `ValueError`였고, `tests/tools/test_rerun_runner.py`의 `test_다른_판의_확인을_쥐고_돌던_동안에도_첫_인계에서_멈춘다`는 `--confirm-handoff` 줄이 없었다. 둘 다 이 브랜치가 건드리지 않은 시간 시험이고, 두 파일만 다시 돌리면 69 모두 지났다(152초. 이 PC에 다른 세션이 여럿 돈다). 대기열 306이 받아들여 닫은 종류(부하에서만 빨간 시간 시험)의 새 사례라 회차를 더하지 않고 여기에만 적고(retro 5단계 행의 종류), 같은 커밋을 다시 쳤다. 앞의 것은 닫힌 531과 파일이 같고 시험은 다르다.

## 회고

후보 여섯. 승인 넷(모두 대기열. 이 세션에서 반영하지 않는다), 기각 둘, 넘김 없음.

1. [승인, 회차] 명세가 프로브가 잰 상황 밖으로 넓혀 적었다. `\r` 둘의 거부를 프로브는 글을 직접 넘기는 함수에서 쟀는데 명세는 어댑터 경로의 사실처럼 적었고, `!!binary`는 한 값을 손으로 본 것을 "거부되지 않는다"로 일반화했다. 둘 다 PR 직전 리뷰가 잡았다(위 "PR 직전 리뷰" 4·5). `.claude/rules/probes.md` 끝 항목(프로브의 결론을 명세로 옮길 때 셋째 항목을 대 본다)과 그 계기 훅 `tools/hook_probe_citing_doc.py`(harness 035, 대기열 540)가 있는데도 어겼다. 지침을 어겨 리뷰가 잡은 사건이라 회차로 센다. 540이 닫혀 새 행 565에 `179의 8회차`로 이었다(179 → 346(179의 4회차) → 506(179의 5회차) → 540(179의 6회차, 2회차에 179의 7회차). 540의 승인 칸을 열어 봤다). 처방 후보 둘은 그 행에 적었다. 회차 3 이상이라 chore 계기다. 훅 후보가 문턱을 지나므로 `uv run python tools/hook_report.py`를 돌렸다(28일 창, 기록 파일 6885개). 뺄 후보는 없어 넘길 것이 없고, `hook_probe_citing_doc.py`는 2026-11-03에 알림 셋이라 계기가 닿고도 어긴 사건이다.
2. [승인, 대기열] 셀프 리뷰 명세 축의 지적("넘긴 것은 넷이 아니라 다섯")을 고정 어구 `명세가 정한다`의 grep으로 물리쳤는데, ADR 0041 본문의 문장은 "명세가 시그니처와 함께 정한다"였다. PR 직전 리뷰가 잡았고 승인받은 ADR 이력을 다시 고쳐 다시 보이게 됐다(사건). 검사로 잡을 수 없는 판단이라 `code-review` 반영 절 2 "근거를 먼저 본다"에 더할 문장 후보이고(층), 더하는 것이라 세 번째까지 대기열에서 센다. 새 행 566, 1회차. 되돌림은 PR 하나.
3. [승인, 대기열] pre-commit 출력의 `Skipped`를 손으로 치라는 CLAUDE.md 검증 명령 절을 따라 `(no files to check)`인 둘을 손으로 쳤는데 둘 다 헛돌았다(카나리아 모양 검사는 인자 없이 사용법 11KB를 찍었고, 헌법 판 검사는 고친 헌법 파일이 없다고 끝났다. 위 "커밋"). 지침 문장 후보라 세 번째까지 센다. 새 행 567, 1회차.
4. [승인, 회차] 인용 대조 경고 17건 가운데 여덟이 선택 화면의 질문·선택지·설명 원문이었다(위 "커밋"). 열린 563(설계 일지의 선택지 라벨 인용을 검사가 경고한다)이 이미 처방한 사건이라 563에 2회차를 더했다. 이 일지의 꼴은 `(설명:`이 따르는 라벨만이 아니라 질문 문장과 선택지 설명도 들어, 563의 처방이 그 꼴까지 덮어야 한다는 것을 그 행이 3회차에 이르면 함께 본다.
5. [기각] `tools/check_constitution_version.py`를 스크립트로 쳐 `ModuleNotFoundError`가 났다. 독스트링이 `-m`을 적고 오류가 바로 알렸다. 이미 있는 안내가 잡았다.
6. [기각] 새 파일 회차 둘이 첫 실행에서 측정 아님이었다(기대 머리말을 긴 `HEAD`로 썼다). `tools/probe_kit.py`의 `Rounds`가 그 자리에서 잡았다.

만료: `uv run python tools/queue_open_rows.py`와 `git fetch origin` 뒤의 `--ref origin/main` 두 출력에 모두 든 열둘(102, 372, 373, 374, 375, 380, 382, 383, 385, 387, 388, 392. 모두 승인 칸 2026-10-20)을 `만료 2026-11-04`로 닫았다. 날짜를 찾지 못한 행은 없었다.

## 인계 (커밋 뒤, 넷째 세션)

셋째 커밋(a70a3b30) 직후의 계기 훅이 세션 컨텍스트 224,154 토큰으로 문턱을 넘었다고 알렸다. 인계하지 않는 때 다섯에 들지 않는다. 계기를 낸 커밋은 성공했고(둘째 시도. 첫 시도는 위 "둘째 커밋" 절의 시간 시험 둘), 요청 범위는 PR·병합까지라 이 경계에서 끝나지 않고, 이 세션의 지시문 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 같은 경계가 아니고, 이 일지에 `인계 못함` 줄이 없고, `get_session self`에 `parentSessionId`가 없다. 이 세션의 제목은 `docs/skill-plugin-spec`이고 `docs/skill-plugin-spec (인계함)`으로 바꾼다. 주 체크아웃은 main 2ba2780d로 `origin/main`과 같다(`tools/sibling_overlap.py`의 형제 줄). 이 세션이 띄운 백그라운드 작업은 커밋뿐이고 끝났다. 이 브랜치에 PR은 없다(`gh pr view docs/skill-plugin-spec`이 없다고 끝났다). 푸시하지 않았다.

지시문:

```
다음 작업: 기능 skill-plugin. 스킬을 실행마다 읽어 컨텍스트로 넘기는 플러그인으로 정한 설계(ADR 0041, PR #457로 병합)의 명세
다음 단계: 명세
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-spec
브랜치: docs/skill-plugin-spec
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-03-03-skill-plugin-spec.md의 "## PR 직전 리뷰 (넷째 세션)"부터 끝까지(반영한 여섯, 둘째·셋째 커밋, 회고, 다음, 이 인계), docs/adr/0041-skill-is-a-plugin-read-per-run-into-the-context.md의 "## 이력"(첫 문단의 "다섯"은 승인받은 글을 고친 것이라 병합 전 재승인), PR 본문 초안 C:/Users/User/AppData/Local/Temp/claude/C--project-agent/85b8699a-f6aa-4eb5-9314-e8b41df12624/scratchpad/pr-body.md(템플릿을 다 채운 것. 열리지 않으면 템플릿을 새로 채운다)
이어받을 상태: 인계: 커밋 뒤 docs/journal/2026-11-03-03-skill-plugin-spec.md. 브랜치의 커밋 셋(dd0150b0 명세·프로브·ADR 이력, 6090fc31 PR 직전 리뷰 여섯 반영·회고·다음, a70a3b30 둘째 커밋 기록·대기열 566 따옴표)까지 했고 pre-commit은 모두 초록이다. 셀프 리뷰, PR 직전 리뷰(CodeRabbit CLI 축, 여섯 모두 반영), 회고(대기열 565·566·567 신설, 563에 2회차, 열둘 만료)까지 끝났다. 푸시하지 않았고 PR은 없다. 남은 단계: 푸시와 /git-pr(관련 티켓은 면제 PR(기능의 명세)) → ccd_pr get_status, 안 잡히면 bind_pr → 봇 회차(merge.md 2. 첫 @coderabbitai review 코멘트, tools/wait_ci.py 백그라운드, 둘째 회차부터 Critical·Major만, 반영마다 명세 서두의 수(정했다 13, 거부한 안 26, 넘겨받은 (1)~(11), 사용자가 고른 절 2)를 다시 센다) → 병합 전에 ADR 0041 이력 첫 문단을 사용자에게 보여 재승인(승인 원문은 일지에 인용) → merge.md "워크트리에서 병합할 때" 1~4 → next-session(다음은 to-tickets). 사용자가 이미 승인한 것(두 ADR 이력 초안, skills 중복 거부, parse_skill 시험 범위, except Exception)은 다시 묻지 않는다(위 "ADR 이력 승인 (넷째 세션)")
확인할 선행 조건: 없음
이번 요청 범위: 명세 작성과 PR·병합까지
```
제목을 `docs/skill-plugin-spec (인계함)`으로 바꿨고 `git worktree unlock`은 `is not locked`로 끝나 넘어갔다. open-session을 부른다 2026-11-03T17:15:05Z

## PR과 봇 회차 (다섯째 세션)

지시문대로 제목을 `docs/skill-plugin-spec`으로 바꾸고 워크트리 `.claude/worktrees/skill-plugin-spec`에 들어갔다(HEAD a70a3b30, `origin/main`은 2ba2780d 그대로라 리베이스 없음). 커밋 셋을 푸시하고 앞 세션의 본문 초안으로 PR #458을 열었다(제목은 첫 커밋의 제목). 앱의 PR 바에 저절로 묶였다(`get_status`의 `bound: true`). `@coderabbitai review`를 남기고 `tools/wait_ci.py 458`을 백그라운드로 띄웠다. 끝 줄은 `끝: 모두 통과`, CodeRabbit·claude-review·verify를 포함한 아홉이 SUCCESS. CodeRabbit은 리뷰를 실제로 돌렸다(요약 코멘트의 `Reviewing files … between 2ba2780d and a70a3b30`. 시간당 포함 리뷰 1회를 썼다고 적혔다).

### 첫 회차 보고

CodeRabbit 둘(인라인 없음, 리뷰 본문에 둘)과 claude-review 다섯. 모두 `.scratch/skill-plugin/spec.md`를 가리킨다.
1. [claude-review, Major] `parse_skill`이 원인을 `__cause__`로 남기면 어댑터가 `from`으로 잇거나 서버가 예외 사슬을 로그에 찍을 때 운영자가 적은 값이 트레이스백으로 나간다. `from None`과 그 단언을 넣거나 로그에 안 나가는 근거를 적으라.
2. [claude-review, Minor] 같은 사실이 명세 본문·ADR 0041 이력·ADR 0012 이력 세 곳에 거의 그대로 있다. 이력을 두세 줄로 줄이라.
3. [claude-review, Minor] ADR 0041 본문의 `(바뀜: 이력 …)` 포인터 여섯이 문단 중간에 있다. 문단 머리에 하나면 된다.
4. [claude-review, Minor] 서두의 수가 손으로 맞춘 값이고 PR 본문과 표기가 갈린다("열하나"와 "(1)~(11)"). 수를 빼라.
5. [claude-review, Nit] 서두 문단이 길다. 불릿으로 나누라.
6. [CodeRabbit, Minor] 쓰지 않는 칸의 명시적 태그 변환 실패(`other: !!int invalid`)가 스킬 전체를 거부하는데 명세는 그 칸을 "읽지도 거부하지도 않는다"고 한다. 값을 만들지 않고 읽거나 명세와 시험에 거부를 적으라.
7. [CodeRabbit, Nit] 실제 모델 단언은 저장소 본문을 코드에 베낀 calc도 지난다. 임시 `SKILL.md`의 새 본문이 프롬프트에 드는 시험을 더하라.

### 판정과 반영

첫 회차라 Major는 고치고 Minor·Nit은 지적마다 판단했다(`merge.md` 2 회차 세기). 근거를 먼저 봤다.
- 1: 유효. 명세 둘째 판이 "원인은 `__cause__`"로 정했고, PR 직전 리뷰는 `src`에 `logging`·`traceback`이 없다는 것으로 오탐이라 했는데(위 "PR 직전 리뷰"), 그것은 오늘의 코드이지 약속이 아니다. `frontmatter_values.py` 셋째 판에 잇기 회차 셋을 더해 쟀다 — `from error`로 이으면 `traceback.format_exception` 출력에 값이 실리고(양성 대조), `from None`은 출력에 없지만 `__context__`에 원래 예외가 남고, `except` 밖에서 던지면 둘 다 `None`이다. 명세 "바꾸는 층"에 불릿 하나(`except`에서 종류와 줄·칸만 뽑고 블록 밖에서 던진다. 시험은 `__cause__`·`__context__`가 `None`인 것을 단언한다)와 거부한 안 둘(`__cause__`로 잇기, `from None`만)을 더했다. ADR 0041 이력은 `str(error)`와 `problem` 문구만 말해 손대지 않았다.
- 6: 유효. 같은 프로브에 쓰지 않는 칸 회차를 더해 쟀다(`other: !!int <값>`이 `ValueError`이고 `str`에 값이 실린다). 명세 "두 칸" 절에 무시는 모델의 좁힘에서이고 YAML 단계의 실패는 머리말 전체의 거부라는 문장과 거부한 안 하나(두 칸만 만드는 것)를 더했다. ADR 0041 본문의 "읽지도 거부하지도 않는다"는 칸의 값을 보지 않는다는 뜻이고 같은 본문의 "머리말이 YAML로 읽히지 않거나"가 그 앞에 있어 포인터는 달지 않았다.
- 7: 받았다. calc 시험은 저장소 `plugins/`를 실제 어댑터로 읽어(`tests/test_calc_plugin.py`의 `_run_calc`. 코드를 읽었다) `FRESH_PROMPT`도 실제 모델 단언도 베낀 calc를 가르지 못한다. "스킬이 둘" 시험을 임시 루트에 시험만 아는 본문의 둘째 스킬을 더하는 모양으로 정했다.
- 2·3·4·5: 보류. 이유는 PR 코멘트에 남겼다. 2는 ADR이 결정의 살아 있는 자리이고(`docs/constitution/operations.md` 문서 위치. 끝난 기능의 명세는 기록이 된다) 이력이 승인받은 글이라 줄이면 재승인이 또 필요하다. 3은 `.claude/rules/adr.md`가 바뀐 문장 바로 뒤에 달라 하고 포인터는 결정을 바꾸지 않는 표시라 재승인 대상이 아니며, 27행의 둘은 사이에 바뀌지 않은 문장이 있어 묶음이 아니다. 4는 to-spec 스킬이 수를 세고 반영마다 다시 세라 하며(대기열 105·207) "열하나"와 "(1)~(11)"은 같은 수의 두 표기다. 5는 다른 명세 둘과 같은 꼴이라 이 PR에서 바꾸지 않는다.

프로브 `frontmatter_values.py` 28회차·`frontmatter_split.py` 26회차, 측정 아님 0. 프로브의 ruff·pyright, `check_md_tables.py`(바뀐 문서 둘), `check_line_separators.py`(바뀐 파일 셋) 종료 0. 서두의 수를 다시 셌다(정했다 13, 거부한 안 29, 넘겨받은 (1)~(11), 사용자가 고른 절 2). 첫 문장을 쓸 때 프로브가 재지 않은 트레이스백 출력을 "찍는다"로 적었다가, 프로브 인용 계기 훅(`hook_probe_citing_doc`)의 문장을 대 보고 양성 대조 회차를 더해 잰 범위로 좁혔다(리뷰 전에 스스로 잡았다).

## 회고 (다섯째 세션)

후보 넷. 승인 둘(모두 회차. 이 세션에서 반영하지 않는다), 기각 둘, 넘김 없음.

1. [승인, 회차] PR 직전 리뷰가 오탐이라 한 `parse_skill`의 `__cause__` 지적을 PR 봇 claude-review가 Major로 다시 짚어 고쳤다(위 "판정과 반영" 1. 푸시 한 번과 봇 회차 하나가 더 든다). 오탐의 근거는 `src`에 `logging`·`traceback`이 없다는 grep과 CLI·HTTP 표가 `str(error)`만 싣는다는 코드 읽기였는데, 명세는 앞으로 쓸 코드의 약속이라 오늘의 코드에 없는 것은 근거가 못 된다. 열린 566(셀프 리뷰 지적을 근거 문장을 열지 않고 고정 어구의 grep으로 물리쳤다)의 처방이 어구 grep에 걸리지 않는 것을 근거로 삼지 않는 것이라 이미 처방한 사건이고, 566에 2회차를 더했다. 이번 꼴은 지적이 든 문장이 아니라 지적이 가리키는 쓰임(명세가 약속한 예외를 어댑터와 서버가 어떻게 다룰지)을 오늘의 코드로 판정한 것이라, 처방이 3회차에 그 꼴까지 덮어야 한다는 것을 그 행에 적었다. 닫힌 190(PR 직전 리뷰의 지적을 두었다가 봇이 다시 짚어 고쳤다)과 겉모양이 같지만 190의 처방(두는 지적은 판정과 값을 PR 체크리스트에 적는다)은 지켰다(PR 본문 "리뷰어 참고"의 오탐 판정). 어긴 것은 판정의 근거라 566으로 센다. `--search 190의`에 이은 행은 없었다.
2. [기각] CodeRabbit의 Minor(쓰지 않는 칸의 태그 실패가 스킬을 거부한다). 명세 "두 칸"의 무시된다는 문장은 프로브가 잰 그대로(모델의 좁힘)이고, 빠진 것은 "바꾸는 층"이 이미 적은 YAML 단계의 거부와의 관계였다. 두 절의 정합은 리뷰가 잡도록 둔 것이고 리뷰가 잡았다. 검사로 옮길 수 없고 코드의 판단 기준도 아니다.
3. [기각] 프로브가 재지 않은 트레이스백 출력을 "찍는다"로 적었다가 리뷰 전에 잰 범위로 좁혔다(위 "판정과 반영" 끝). 계기 훅 `hook_probe_citing_doc`이 그 자리에서 알렸고 알림대로 양성 대조 회차를 더했다. 훅이 제 몫을 했다. 565(179의 8회차)와 같은 지침인데 이번에는 알림이 닿아 어기지 않았다.
4. [승인, 회차] 반영 커밋의 pre-commit에서 `(no files to check)`로 Skipped인 둘을 `CLAUDE.md` 검증 명령 절대로 손으로 쳐 헛돌았다(헌법 판 검사는 고친 헌법 파일이 없다고 끝났고, 카나리아 모양 검사는 넘길 파일이 없다. 아래 "반영 커밋"). 열린 567이 처방한 사건이라 567에 2회차를 더했다. 회고 절을 쓴 뒤에 난 사건이라 여기에 더했다.

만료: `uv run python tools/queue_open_rows.py`는 만료할 행이 없고, `git fetch origin` 뒤의 `--ref origin/main`은 넷째 세션이 이미 닫은 열둘(102, 372, …, 392)만 냈다. 두 출력에 모두 든 행이 없어 닫은 것이 없다. 새 훅·검사 후보가 문턱에 닿지 않아 `tools/hook_report.py`는 돌리지 않았다.

### 반영 커밋

보류 넷의 이유를 PR 코멘트로 남기고 PR 본문을 첫 봇 회차 반영으로 고친 뒤(`merge.md` 병합 전 1) 커밋 직전에 `uv run python tools/sibling_overlap.py`를 쳤더니 종료 1이었다. 형제 `agent-os-direction` 워크트리(HEAD는 `origin/main`과 같은 2ba2780, 커밋하지 않은 변경)가 대기열 564를 먼저 썼다. 출력대로 `--move`로 이 브랜치의 564·565·566을 565·566·567로 옮겼다(인용을 고친 파일은 대기열과 이 일지). 도구가 옮기지 않는다고 적은 꼴(`새 행 564에`처럼 낱말 없이 든 번호, `564(179의 8회차)`처럼 괄호가 따르는 번호, "다음"의 `·`로 이은 목록)은 `git diff --merge-base origin/main`을 `56[4-7]`로 훑어 손으로 고쳤고, PR 본문의 괄호(낱말 없이 든 번호라 도구가 옮길 인용이 없다고 했다)도 다시 `gh pr edit`했다. 넷째 세션의 "커밋" 절이 적은 다음 빈 번호도 도구가 565로 옮겼다. 그때 찍힌 값은 564였고 이 절이 그 사실을 든다.

커밋 `1d4a34ca`(파일 5, +173/-24). pre-commit은 전부 Passed(병렬 검사 456초, pytest 307초, web-verify 456초), Skipped 둘(`no files to check`, 카나리아 모양·헌법 판). 헌법 판 검사는 `uv run python -m tools.check_constitution_version`으로 손으로 쳐 "이 가지가 고친 헌법 파일이 없다"였고, 카나리아 모양 검사는 커밋에 카나리아 명세가 없어 넘길 파일이 없다(위 회고 4, 567의 2회차). 인용 대조 경고 1건: 프로브 README의 해석 갈래 문장(`from None`이면 원래 예외가 남지 않는다)이 저장소에 글자 그대로 없는 인용이라 따옴표를 떼고 해석이라 적었다(둘째 커밋). 커밋이 도는 동안 인계 계기 훅이 왔다(세션 컨텍스트 226,005 토큰, 경계 `커밋 뒤`). 이 세션을 연 지시문의 "이어받을 상태"가 `인계: 커밋 뒤`로 시작해 `handoff.md` 1의 인계하지 않는 때 셋째에 들어 넘기지 않고 이었다.

## 재승인 (다섯째 세션)

PR을 연 턴의 마무리 상자로 ADR 0041 이력 첫 문단을 "본문이 명세에 넘긴 다섯"으로 고친 글을 그대로 두어도 되는지 물었다(선택지는 승인과 원래대로 되돌려). 반영 커밋의 pre-commit이 도는 동안 답이 왔다.

> 사용자: 승인

고친 글을 그대로 둔다. 이력 첫 문단은 넷째 세션의 "PR 직전 리뷰" 3이 고친 판이고 그 뒤 다시 고치지 않았다. 이 인용을 실은 커밋이 병합 전 마지막 푸시에 든다.

## 다음

- 명세는 `ready-for-agent`다. 다음 단계는 to-tickets(새 세션). `/to-tickets` 직전에 `spec-reviewer` 서브에이전트가 체크리스트 일곱과 질문 둘로 명세를 본다(그 정의의 설명).
- 구현 티켓이 이어받을 것 셋. (1) `yaml.safe_load`의 `Any`를 `isinstance`로 좁히는 것이 pyright strict와 원칙 III(`cast` 없이)를 지나는지는 PR 직전 리뷰가 대 보지 못했다(워크트리 가드가 임시 pyright 설정 명령을 거부했다). 묶음 A의 sdk 티켓이 `uv run pyright`로 본다. (2) 머리말의 `name`은 ASCII 패턴이라 비ASCII 이름의 스킬 폴더는 들어오지 않는다(명세 Out of Scope). (3) 어댑터 경로의 시험은 `\r` 둘·홀로 선 `\r`의 거부를 기대하지 않는다(명세 "떼는 규칙" 셋째 불릿).
- ADR 0041 이력 첫 문단을 PR 직전 리뷰 뒤 "본문이 명세에 넘긴 다섯"으로 고쳤다. 승인받은 글이라 병합 전에 사용자에게 다시 보였고 재승인을 받았다(위 "재승인"). 병합은 묻지 않는다.
- PR #458 첫 봇 회차(위 "판정과 반영"): Major·Minor·Nit 하나씩 반영, 넷 보류. 뒤로 넘긴 일은 없다. 둘째 회차부터 Critical·Major만 고친다.
- 병합 뒤 주 체크아웃은 당기지 않는다(`merge.md` "워크트리에서 병합할 때" 4). 새 세션이 워크트리에 들어가기 전에 `tidy-checkouts`를 돈다.
- 회고: 넷째 세션에 대기열 565(179의 8회차. 회차 3 이상이라 chore 계기)·566·567 신설, 563에 2회차, 열둘 만료. 다섯째 세션에 566·567에 2회차. 이 번호는 반영 커밋 전에 옮긴 것이다(위 "반영 커밋").
