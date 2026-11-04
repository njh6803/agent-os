# 02: 스킬 문서를 읽는다 — `SKILL.md`가 이름·설명·본문의 값이 되고, 깨진 문서는 값을 되울리지 않는 오류를 낸다

**What to build:** 스킬 폴더의 `SKILL.md`를 플러그인 소스로 읽으면 이름·설명·본문을 든 불변 값 `Skill`이 나온다. 파일이 없으면 값으로 없음(`None`)이고, 깨졌으면(머리말이 없거나 닫히지 않음, YAML로 읽히지 않음, 두 칸이 없거나 문자열이 아님, `name`이 폴더 이름과 다름, UTF-8 아님) 경로와 줄·칸과 오류 종류만 든 `PluginError`이며 머리말에 적은 값은 문구에도 예외 사슬에도 없다. 표준의 선택 칸과 제품별 키는 무시되어 다른 제품용 스킬 폴더가 그대로 들어온다. 에이전트 코드는 `ctx.skills`를 읽을 수 있고 지금은 늘 빈 열이다. sdk 밖에서 `import yaml`을 하면 `uv run lint-imports`가 빨개진다.

03을 막는다. 01과 나란히 돈다. 수용 기준의 고칠 자리로 대 본 겹침은 줄이 다른 두 파일이다. `.claude/rules/sdk.md`(이 티켓은 스킬 줄, 01은 종류별 칸의 불릿)와 `tests/test_server.py`(이 티켓은 가짜 소스의 `read_skill`, 01은 표지 행 시험)다. 구현하며 겹치는 파일이 더 나와도 같다. 어느 파일이든 뒤에 병합되는 쪽이 앞의 것을 합친다. 머리말 규칙과 그 시험이 크고 프로브 두 파일의 사례를 옮기는 일이라 계약 칸과 나눴다(to-tickets에서 사용자가 골랐다).

**병합 뒤에 틈이 있다.** 어댑터의 `read_skill`을 부르는 곳이 없고 `ctx.skills`는 늘 빈 열이다. 03이 이 틈을 닫는다. 이 티켓이 쓰는 문장은 틈 동안에도 참이어야 하고, `AgentContext.skills`의 독스트링은 계약이 약속하는 것을 말한다. 런타임이 실행을 준비할 때마다 읽는다는 말은 03이 쓴다.

근거는 `.scratch/skill-plugin/spec.md`의 "머리말을 본문에서 떼는 규칙", "머리말의 두 칸과 값의 모양", "sdk의 스킬 값과 읽는 함수", "머리말 거부를 `PluginError`로 바꾸는 층", "포트 `read_skill`의 시그니처와 돌려주는 값의 자리", "읽지 못한 문구와 이름 어긋남 문구"와 그 2026-11-04 명세 검토 주석, "컨텍스트 멤버의 타입과 신뢰 경계 문구"와 그 주석, "YAML의 import 경계"와 그 주석, Testing Decisions의 "sdk 스킬 값과 읽는 함수"·"어댑터"·"경계"다. 앞선 결정은 ADR 0041과 그 2026-11-03·2026-11-04 이력, ADR 0012의 2026-11-03 둘째 이력(`read_skill`)이다. 경계는 프로브 `.scratch/skill-plugin/probes/frontmatter_split.py`와 `frontmatter_values.py`가 쟀고 표지는 그 `README.md`에 있다. 프로브를 import하지 않는다(프로브는 저장소 코드가 아니다).

**Blocked by:** None (can start immediately)

**Status:** done

### sdk — 값과 읽는 함수

- [x] **`Skill`은 `Conversation`·`Exchange`와 같은 `frozen` dataclass이고 멤버는 `name`(`PluginName`), `description`(`str`), `body`(`str`) 셋뿐이다.** `parse_skill(text) -> Skill`과 함께 sdk의 공개 표면(`agent_os.sdk`)에 든다. 머리말 모델은 올리지 않는다. 폴더 이름과의 대조는 이 함수의 몫이 아니다
- [x] **가르기 규칙과 두 칸의 모양을 프로브 두 파일의 사례 전부로 같은 입력을 넣어 시험한다**(스토리 24). 목록은 명세 Testing Decisions의 "sdk 스킬 값과 읽는 함수"다. 가르기 다섯과 거부 다섯, 값 안의 `---`, 빈 머리말, 머리말 안 `---` 줄 세 자리와 그 대조 셋, 받는 셋과 거부 열둘(표지는 프로브 README), 명시적 태그 넷과 쓰지 않는 칸의 태그 하나다. 문구에 값이 없는 것은 값이 있어야 할 양성 대조(`str(error)`)와 함께 본다
- [x] **실패는 세 종류이고 모두 `ValueError` 계열이다.** 가르기와 맵 아님은 고정 문구의 `ValueError`, 두 칸은 `ValidationError`, YAML 읽기는 아래 문구의 `ValueError`다. 어댑터가 잡는 예외의 집합이 매니페스트와 같아진다
- [x] **`yaml.safe_load` 호출 하나에서 난 모든 예외를 `머리말이 YAML로 읽히지 않는다: <오류 종류>`로 바꾼다.** `MarkedYAMLError`이고 `problem_mark`가 있으면 ` (줄 N, 칸 M)`이 붙고 파일 기준 1부터 센다(줄은 여는 `---` 줄만큼 더 더한다, 명세). `str(error)`와 `problem`·`context` 문구는 어디에도 싣지 않는다. 사례는 닫히지 않은 따옴표와 `!!int` 태그(`YAMLError`가 아닌 길)의 둘이고 문구에 적은 값이 없음을 단언한다
- [x] **바꿔 던진 예외의 `__cause__`와 `__context__`가 모두 `None`이다.** `except`에서는 종류와 줄·칸만 뽑고 그 블록 밖에서 던진다. `from None`은 `__context__`를 남겨 거부한 안이다(쟀다, `frontmatter_values.py`의 잇기 회차). `import yaml`은 이 함수가 사는 모듈만 한다

### 일지 2026-11-03-03이 넘긴 셋

- [x] **`yaml.safe_load`의 `Any`를 `isinstance`로 좁히는 것이 `uv run pyright`와 `tools/check_type_escapes.py`를 `cast` 없이 지나는지 본다.** PR 직전 리뷰가 대 보지 못한 채 넘겼다. 스텁이 실제로 실렸는지 `reveal_type`으로 먼저 보고(양성 대조, `CLAUDE.md`의 "검사 도구가 내가 생각하는 것을 실제로 봤는지"), 지나지 못하면 우회하지 않고 멈춰 보고한다(원칙 III)
- [x] **비ASCII 이름은 들어오지 않음을 시험으로 고정한다.** 한글 이름과 전각 글자 이름의 `name`이 `string_pattern_mismatch`이고 정규화하지 않는다(명세 Out of Scope, `.scratch/plan.md`의 claude-code-compat 행이 받는다)
- [x] **어댑터 경로의 시험은 `\r` 둘과 홀로 선 `\r`의 거부를 기대하지 않는다.** 텍스트 모드 읽기가 `\r`을 모두 `\n`으로 바꿔 받아들인다(쟀다, `frontmatter_split.py`의 파일 회차). 두 거부는 글을 직접 넘기는 sdk 시험에서만 본다

### 어댑터

- [x] **`PluginSource.read_skill(name: PluginName) -> Skill | None`을 파일시스템 어댑터가 구현한다.** 동기다. 파일을 매니페스트와 같은 길(텍스트 모드 `read_text(encoding="utf-8")`)로 읽고 `parse_skill`을 부르며, 머리말의 `name`을 인자와 대조한다. 경로는 인자의 `PluginName`으로만 조립한다. 시험: 한 폴더의 스킬 문서가 `name`으로 다른 스킬을 가리켜도 그 스킬의 파일을 읽어 돌려주지 않고 어긋남 `PluginError`다
- [x] **문구는 `스킬 문서를 읽을 수 없다: <경로>` 한 줄 뒤에 `_describe`의 이유 한 줄이고, 어긋남은 `디렉터리와 머리말의 name이 어긋난다: <경로> 는 <이름> 자리인데 <머리말의 name>`이다.** 잡는 집합은 `OSError`, `ValidationError`, `ValueError`이고 어댑터는 YAML을 모른다
- [x] **`read_skill`도 예외를 잇지 않는다.** `except`에서 이유 문구만 만들고 `PluginError`는 그 블록 밖에서 던진다. 매니페스트 `_parse`의 `from error` 모양을 따르면 `description: [비밀]`의 `ValidationError`가 `__cause__`에 남아 `traceback.format_exception`의 출력에 값이 실린다(명세 "읽지 못한 문구"의 주석). 매니페스트 `_parse`의 같은 사슬은 이 티켓이 고치지 않는다
- [x] **어댑터 시험은 실제 폴더에서 본다.** 파일 없음과 폴더 없음의 `None`, 읽힘, 이름 어긋남, CRLF 파일의 LF 본문, BOM의 거부, UTF-8 아님, 닫히지 않은 따옴표 뒤에 비밀처럼 보이는 값을 둔 문서의 `PluginError`(문구에 경로·`ScannerError`·줄이 있고 값이 없다), `description: [비밀]`의 `__cause__`·`__context__`가 `None`이고 `traceback.format_exception`의 출력에 값이 없는 것이다. 선례는 `tests/adapters/test_filesystem.py`의 `test_없는_플러그인은_None이다`, `test_디렉터리와_name이_어긋나면_에러다`, `test_칸에_잘못_적은_값은_매니페스트를_읽지_못한_문구에_다시_나오지_않는다`다
- [x] **같은 이름의 `read_skill` 사이에 파일을 고치면 둘째가 고친 글을 돌려준다**(스토리 9의 어댑터 몫. 캐시가 없다)
- [x] **`SKILL.md` 없는 폴더와 머리말이 깨진 폴더가 `list_manifests`의 보통 행이다**(스토리 16). 목록은 매니페스트만 읽는다. core의 가짜 `list_manifests`는 `NotImplementedError`라 이 자리다

### 포트와 가짜

- [x] **포트 표 `.claude/rules/core.md` 13행의 `PluginSource`에 메서드가 는다.** 포트는 다섯 그대로다(ADR 0012, 스토리 20). 포트의 독스트링이 부재는 값, 손상은 `PluginError`를 적는다
- [x] **포트를 시그니처로 만족하는 가짜에 `read_skill`을 더한다.** `tests/core/test_run.py`의 `FakePlugins`, `tests/test_server.py`, `tests/channel/http/test_router.py`, `tests/channel/http/test_end_user.py`, `tools/export_openapi.py`의 `_SchemaOnlyPlugins`다. `tests/adapters/test_filesystem.py`의 Protocol `_DisabledReader`와 대역 `_FailingReader`는 `read_disabled`만 보아 해당하지 않는다. 가짜는 이 티켓에서 최소한으로 둔다. 이름별 문서와 읽은 횟수를 드는 것은 03이다

### 컨텍스트 멤버

- [x] **`AgentContext.skills`는 읽기 전용 속성이고 타입은 `tuple[Skill, ...]`이다.** core의 컨텍스트는 이 티켓에서 빈 열을 들고, 가짜 컨텍스트 셋(`tests/sdk/test_agent.py`, `tests/sdk/test_conversation.py`, `tests/adapters/test_filesystem.py`)이 같은 이름의 속성을 둔다. 빠뜨리면 pyright가 잡는다. core 시험에는 가짜 컨텍스트가 없고 실제 컨텍스트를 지난다
- [x] **core 시험이 실행의 `ctx.skills`가 `()`임을 본다**(스토리 3). 판정 에이전트가 값을 출력에 옮기는 선례는 `test_이어_가지_않은_실행의_멤버는_요약이_없고_교환이_비어_있다`다
- [x] **sdk의 독스트링(`AgentContext`와 `Skill`의 모듈)이 신뢰 경계를 `conversation`의 반대편으로 적는다**(스토리 5). 스킬 본문은 운영자가 플러그인 폴더에 둔 파일이라 에이전트 코드와 같은 신뢰 수준이고 지시로 엮어도 된다. 런타임은 `llm()`에 붙이지 않는다

### 의존성과 경계

- [x] **`pyproject.toml`의 직접 의존성에 `pyyaml>=6.0`이 들고, `docs/constitution/tech.md`의 런타임 의존성 줄에 "sdk: `pyyaml`(스킬 문서의 머리말, ADR 0041)"이 든다.** `uv lock`을 치고 `uv.lock`의 변경을 함께 커밋한다. 패키지 수는 늘지 않고 루트 패키지의 의존성 줄이 바뀔 것이다(어림). 다른 패키지의 판이 움직이면 멈춰 본다
- [x] **sdk 밖의 일곱 층(`agent_os.core`, `agent_os.adapters`, `agent_os.channel`, `agent_os.admin`, `agent_os.http`, `agent_os.server`, `agent_os.main`)이 `yaml`을 직접 import하지 못하는 `forbidden` 계약을 `pyproject.toml`의 `[tool.importlinter]`에 둔다**(스토리 22). 선례 "core knows no provider"처럼만 쓰면 서지 못한다. **`allow_indirect_imports = true`가 필요하다.** 없으면 일곱 층 모두 `agent_os.sdk → agent_os.sdk.skill → yaml` 사슬로 깨진다(명세 검토 세션이 사본에 `lint-imports --config`를 쳐 손으로 봤다. 그 키가 있으면 KEPT이고, 있어도 어댑터에 직접 `import yaml`을 더하면 BROKEN이다). 이 계약이 막는 것은 직접 import다
- [x] **계약의 빨강을 실제로 본다.** 어댑터에 `import yaml`을 넣어 `uv run lint-imports`가 그 계약으로 빨개지는 것을 보고 되돌린다. 계약을 넣기 전과 넣은 뒤의 집계 줄도 본다

### 문서

- [x] **`.claude/rules/sdk.md` 17행 "스킬은 절차 지식이다"를 이 멤버를 적는 줄로 바꾼다**(값의 모양, 신뢰 경계, 런타임이 `llm()`에 붙이지 않는 것). `.claude/rules/core.md` 13행도 함께다. 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`). 틈 동안에도 참인 문장이어야 한다
- [x] **옛 표현을 저장소 전체에서 grep해 살아 있는 문서에 잔존이 0인지 본다**(`CLAUDE.md` 작업 규약 4). 기록은 고치지 않는다

### 검증

- [x] **빨강을 먼저 본다**(헌법 원칙 II). 첫 빨강은 sdk의 가르기·두 칸 사례와 import-linter 계약이다
- [x] **검증 명령이 모두 초록이다.** 손으로 치는 다섯이다. 런타임이 아직 스킬을 읽지 않아 `-m llm`과 e2e는 이 티켓이 닿지 않는다
