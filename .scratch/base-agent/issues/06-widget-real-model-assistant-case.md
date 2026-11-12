# 06: 위젯의 실제 모델 e2e — 위젯에서 assistant에게 물으면 출처가 붙은 답이 화면에 뜬다

**What to build:** 최종 사용자가 위젯에서 `assistant`에게 근거가 있는 질문을 보내면, 화면의 답에 문서 제목, "출처", 갱신일이 보인다. 그 실행의 트레이스에 `llm_called`와 성공한 `search`가 있다. 손으로 치는 `-m llm_widget` 시험이 실제 브라우저와 실제 모델과 가짜 검색 서버(02)로 이 장면을 본다. e2e 준비 패키지의 픽스처가 `assistant`의 규칙 표와 가짜 검색 서버의 주소를 담고, 그 픽스처를 함께 쓰는 질문 페이지의 e2e와 실제 모델 e2e도 그대로 지난다.

근거는 `.scratch/base-agent/spec.md`의 Testing Decisions "위젯의 실제 모델 e2e"와 "고칠 자리의 묶음"의 F 줄이다. 앞선 결정은 ADR 0051 Consequences "위젯 e2e의 픽스처", ADR 0053과 그 2026-11-10 이력(위젯이 `[숫자]`를 위첨자로, "출처" 목록을 선 아래 작은 글자로 그린다. 이 기능과 서로 기다리지 않는다)이다. 선례는 `tests/test_widget_llm.py`와 그것이 돌리는 계산 사례 `web/apps/widget/e2e/calc.llm.ts`다.

**Blocked by:** 03 (기본 에이전트 assistant와 스킬 cite-sources, 연결 doc-search, 규칙 파일의 표를 기본 플러그인 루트에 둔다). 위젯 e2e는 저장소의 `plugins/`를 옮겨 쓰므로 그 플러그인이 03에서 선다.

**Status:** done

### 사례

- [x] 사례는 하나다. 위젯에서 `assistant`에게 근거가 있는 질문을 보내면 화면의 답에 문서 제목, "출처", 갱신일이 보이고, 트레이스에 `llm_called`와 성공한 `search`가 있다
- [x] 화면의 단언은 정해 둔 낱말이 보이는지로 한다. 화면의 글이 `run_finished`의 출력과 글자 그대로 같은지는 보지 않고, `[1]` 같은 대괄호 번호도 넣지 않는다. answer-markdown(ADR 0053)이 먼저 오든 나중에 오든 깨지지 않아야 한다
- [x] 승인 카드를 실제 모델과 함께 누르는 장면은 두지 않는다(사용자가 골랐다)

### 픽스처와 감싸는 시험

- [x] 감싸는 파이썬 시험이 가짜 검색 서버를 띄우고 그 주소를 환경 변수 `AGENT_OS_WIDGET_DOC_SEARCH_URL`로 Playwright 쪽에 넘긴다. `DOC_SEARCH_AUTHORIZATION`도 자식의 환경에 준다
- [x] e2e 준비 패키지(`web/packages/e2e-stack`)는 저장소의 플러그인을 옮긴 뒤 그 변수가 있으면 `doc-search` 매니페스트의 주소를 그 값으로 바꿔 쓴다
- [x] 픽스처의 규칙 파일에 `assistant`의 세 줄을 더하고, 실제 모델 e2e의 사이트가 여는 에이전트에 `assistant`를 더한다
- [x] 픽스처의 `assistant` 세 줄 곁에, 그것이 저장소 `plugins/rules.toml`의 사본이라는 것과 원본의 경로를 주석으로 적는다. 저장소의 표가 바뀌면(kb-selection이 `list_knowledge_bases`를 allow로 옮긴다. ADR 0051의 2026-11-10 이력) 이 사본도 손으로 맞춘다
- [x] 감싸는 시험의 기준에서 통과한 사례의 수가 1에서 2가 된다(건너뜀 0은 그대로)
- [x] 감싸는 시험의 출력 판정은 지금 트레이스 전체에서 `run_finished`의 출력이 하나라고 본다(`tests/test_widget_llm.py`의 `_failures`가 `len(outputs) != 1`을 본다). 실행이 둘이 되면 깨지므로 사례마다의 짝으로 바꾼다. 화면 글은 그 사례가 연 에이전트의 이름과 함께 싣고, 트레이스에서는 그 에이전트로 시작한 실행(`run_started`의 `agent`)의 출력을 고른다. 글자를 견주는 것은 계산 사례 하나이고 `assistant` 사례는 정해 둔 낱말만 본다. answer-markdown 03(`.scratch/answer-markdown/issues/03-widget-renders-answers-as-markdown.md`)이 같은 짝짓기를 짓는다. 그 티켓이 먼저 들어와 있으면 그 짝짓기와 비교 규칙(화면 글이 원문의 글자와 숫자의 부분열인지 보는 것)을 그대로 쓴다(`.scratch/answer-markdown/spec.md`의 "위젯의 시험"과 "실제 모델 시험의 비교 규칙")

### 함께 치는 것

- [x] 그 픽스처는 질문 페이지의 e2e와 그 실제 모델 e2e도 쓰므로(`web/apps/portal/e2e/stack.ts`가 같은 함수를 부른다), 질문 페이지 e2e(`pnpm -C web/apps/portal exec playwright test`)와 `-m llm_portal`도 친다. 질문 페이지 쪽 사례의 기대는 그대로다(그 사이트는 calc만 열고, 에이전트 표는 그 실행의 에이전트 것만 대 본다)
- [x] 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`), `uv run --env-file <.env 경로> pytest -m llm_widget`, `-m llm_portal`이 초록이다
- [x] 검증 명령이 모두 초록이다
