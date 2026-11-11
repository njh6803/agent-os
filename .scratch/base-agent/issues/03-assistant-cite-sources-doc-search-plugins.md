# 03: 기본 에이전트 assistant와 스킬 cite-sources, 연결 doc-search, 규칙 파일의 표를 기본 플러그인 루트에 둔다

**What to build:** 기본 플러그인 루트 `plugins/`로 `serve`를 띄우면 에이전트 목록에 `assistant`가 보인다. `assistant`에게 질문하면 모델이 문서 검색 도구를 스스로 불러 찾은 조각의 근거로만 답하고, 문장 끝의 `[1]`과 답 끝의 "출처" 목록(문서 제목, 위치, 갱신일)을 단다. 검색은 묻지 않고 불리고, 문서 전문 읽기는 승인 카드에서 멈추며, 지식베이스 목록은 모델의 도구 목록에 오르지 않는다. 문서 검색 서버의 주소는 `doc-search` 매니페스트에 있고, 토큰은 환경 변수 `DOC_SEARCH_AUTHORIZATION`의 값이 `Authorization` 헤더로 간다. 변수가 없으면 그 실행이 원인 `tool_connection`으로 끝난다. 이 동작을 대본 모델과 가짜 검색 서버(02)와 실제 MCP 어댑터로 PR마다 본다. 프로브는 그 뒤로 제 초안이 아니라 저장소의 플러그인과 이 픽스처를 쓴다.

에이전트 코드에는 어떤 일의 이름도 도구의 이름도 없다. 문서 검색에 해당하는 것은 스킬, 연결 플러그인, 규칙 파일의 표 세 자리에 있다(ADR 0051).

근거는 `.scratch/base-agent/spec.md`의 Implementation Decisions "기본 에이전트의 매니페스트", "기본 에이전트의 코드", "연결 플러그인 doc-search", "규칙 파일의 표", "스킬 cite-sources", "고칠 자리의 묶음"의 C 줄, Testing Decisions "플러그인 꾸러미의 시험", Further Notes "스킬을 고칠 때"다. 매니페스트, 프롬프트의 세 상수, `doc-search` 매니페스트, 규칙 파일의 표, 스킬 문서 전체의 글자는 그 명세에 코드 블록으로 있고 이 티켓은 그 글자를 그대로 옮긴다. 앞선 결정은 ADR 0051(본문과 이력 셋), ADR 0052(두 끝), ADR 0049(http 모양의 MCP 플러그인, 헤더는 변수 이름), ADR 0044와 그 2026-11-05 이력 "그 에이전트의 표는 연결 뒤 대 본다"다. 선례는 calc(`plugins/agents/calc`)와 스킬 `answer-format`, 시험 `tests/test_calc_plugin.py`다.

**Blocked by:** 01 (계약 — 에이전트 매니페스트에 턴의 끝과 도구 호출의 끝이 생기고 런타임이 지킨다). `assistant` 매니페스트가 두 칸을 적으므로 그 칸이 없는 판에서는 읽히지 않는다. 02 (가짜 문서 검색 서버). 꾸러미 시험과 프로브가 그 픽스처에 붙는다.

**Status:** ready-for-agent

### 플러그인 셋과 규칙 파일

- [ ] `plugins/agents/assistant`의 매니페스트가 명세의 글자 그대로다(`mcp = ["doc-search"]`, `skills = ["cite-sources"]`, `max_turns = 6`, `max_tool_calls = 4`, `model`과 `requires_approval`은 적지 않는다)
- [ ] 에이전트 코드는 스킬 블록, 앞 대화 블록, 요청 줄을 이어 프롬프트 하나를 만들고 `ctx.llm()`을 한 번 불러 그 반환을 출력으로 낸다. 예외를 잡지 않는다. 프롬프트의 글자는 명세의 세 상수(`PROMPT`, `SKILL`, `PREVIOUS`)와 블록 규칙 그대로다
- [ ] `plugins/skills/cite-sources`의 매니페스트는 공통 넷뿐이고, `SKILL.md`는 명세의 스킬 문서 전체와 글자 그대로 같다
- [ ] `plugins/mcp/doc-search`의 매니페스트가 명세의 글자 그대로다(`transport = "http"`, `url = "http://rag-engine:8000/mcp"`, `[server.headers]`의 `Authorization = "DOC_SEARCH_AUTHORIZATION"`, `[server.secret_args]` 없음)
- [ ] `plugins/rules.toml`에 `[agents.assistant]` 표(allow `doc-search:search`, ask `doc-search:get_document`, deny `doc-search:list_knowledge_bases`)를 더하고 calc의 표와 머리 주석은 그대로 둔다
- [ ] 저장소의 규칙 파일이 calc의 표 하나라는 지금의 시험(`tests/test_calc_plugin.py`의 `test_저장소의_rules_toml_은_실제_어댑터로_읽혀_calc_의_표_하나가_된다`)을 표 둘로 고친다

### 꾸러미 시험 (명세 "플러그인 꾸러미의 시험")

저장소의 `plugins/`를 임시 루트에 복사하고 `doc-search`의 주소만 가짜 검색 서버의 것으로 바꿔 쓴 뒤, 실제 플러그인 어댑터와 실제 MCP 어댑터와 대본 모델로 런타임의 실행 함수를 부른다. 환경 변수 `DOC_SEARCH_AUTHORIZATION`은 시험이 준다.

- [ ] 프롬프트: 이어 가지 않은 실행의 프롬프트가 `지침 cite-sources: <스킬 본문>\n\n요청: <요청>`과 글자 그대로 같다(시험이 스킬 파일을 직접 읽어 만든다). 이어 간 실행의 프롬프트에는 앞 대화 블록이 그 사이에 든다. 매니페스트의 `skills`를 지운 사본의 프롬프트는 `요청: <요청>` 한 줄이다
- [ ] 검색: 대본 모델이 `search`를 내면 묻지 않고 불리고(`rule`이 `allow`) 결과 글에 형식의 판과 표본 조각이 있다. 판의 글자는 가짜 검색 서버 모듈의 상수에서 읽는다. 가짜 서버의 기록에 `Authorization` 헤더가 시험이 준 값으로 남는다
- [ ] 전문 읽기: 대본 모델이 `get_document`를 내면 `run_paused`(`rule`이 `ask`, `server`가 `doc-search`)로 멈춘다. 승인하면 가짜 서버가 `include_text`가 참인 호출을 받고 결과에 전문의 첫 창이 있다. 거부하면 `tool_called(ok=false)`가 모델에 돌아가고 실행이 답으로 끝난다
- [ ] 막힌 도구: 모델에 붙은 도구 목록에 `list_knowledge_bases`가 없고, 대본 모델이 그 이름을 내면 "운영자가 거부했다"로 돌아온다
- [ ] 저장소의 파일: 규칙 파일이 실제 어댑터로 읽혀 calc와 assistant의 표 둘이 된다. `assistant` 매니페스트의 두 끝이 4와 6이고 `model`이 없다. `doc-search` 매니페스트가 http 모양이고 헤더가 변수 이름 `DOC_SEARCH_AUTHORIZATION`을 든다. 스킬 문서가 실제 어댑터로 읽혀 이름이 `cite-sources`이고 본문에 정해진 문장이 글자 그대로 있다
- [ ] 실물의 두 끝: 대본 모델이 `search`를 다섯 번 내면 다섯째가 끝 넘음의 문구로 돌아오고 실행이 답으로 끝난다. 여섯 턴 내내 도구를 내면 `loop_limit`이다
- [ ] 변수가 없을 때: 환경 변수를 주지 않으면 실행이 원인 `tool_connection`으로 끝난다
- [ ] 플러그인이 sdk만 import하는지는 지금의 경계 시험(`tests/test_plugins_boundary.py`)이 새 에이전트 파일에도 걸린다

### 프로브 (명세 Further Notes "스킬을 고칠 때")

- [ ] `.scratch/base-agent/probes/skill_follow.py`가 저장소의 `plugins/`를 임시 루트에 옮겨 `doc-search`의 주소만 바꿔 쓰는 꼴(꾸러미 시험과 같은 꼴)로 돌고, 가짜 서버는 02의 픽스처를 띄운다. `probes/draft/`와 `probes/fake_doc_search.py`를 지운다
- [ ] 프로브가 쓰던 모드 넷(끝 넘음 흉내, 검색 실패, 빈 색인, 창의 상한)이 픽스처의 실패 모드 셋과 창의 상한으로 돈다(명세 "스킬을 고칠 때")
- [ ] 고친 프로브가 서는지 사례 전체를 한 바퀴 돌려 본다(실제 모델 비용이 든다. 고친 꼴이 도는지는 돌려 봐야 안다, `CLAUDE.md` 작업 규약 3). 측정 아님이 0인지와 판정이 2026-11-11의 초안 7 결과와 같은지를 `.scratch/base-agent/probes/README.md`에 새 절로 적는다. 판정이 다른 사례가 있으면 스킬의 글자를 고치지 않고 그 차이를 적은 뒤 멈춰 보고한다. 글자는 초안과 같으므로, 다르면 프로브의 꼴을 바꾼 것이나 회차 사이의 흔들림이 판정을 바꾼 것이다
- [ ] README의 표("다시 돌 때", "잰 판")가 새 꼴을 적는다
- [ ] 지운 `probes/draft/`와 `probes/fake_doc_search.py`를 지금의 자리로 가리키는 명세 문장(머리의 측정 문단, "기본 에이전트의 매니페스트", "기본 에이전트의 코드", "스킬 `cite-sources`", "가짜 검색 서버"의 옮긴 것의 원천과 표본, Further Notes "스킬을 고칠 때")을 저장소의 플러그인과 02의 픽스처를 가리키게 고친다. 잰 때의 자리를 적은 문장(프로브 README의 지난 절, 일지)은 기록이라 그대로 둔다(`docs/constitution/operations.md` 문서 위치)

### 마무리

- [ ] 검증 명령이 모두 초록이다
