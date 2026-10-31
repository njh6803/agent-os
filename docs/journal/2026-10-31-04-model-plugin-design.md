# 2026-10-31 (04) 모델 플러그인을 런타임이 읽게 하는 설계 인터뷰

## 시작

> 사용자: (새 세션 지시문) /grill-with-docs … 다음 작업: 새 기능(slug는 인터뷰가 정한다). `.scratch/plan.md`의 프론티어에 남은
> 기능이 없어, `docs/PRD.md`의 범위에서 다음 기능을 고르는 설계 인터뷰를 한다 / 다음 단계: 설계 인터뷰 / 어디서: 새 세션. 주
> 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고 … 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree로 새
> 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 브랜치: docs/next-feature-grill / 모델: Fable 5.1 / xhigh / 읽을 것:
> `docs/journal/2026-10-31-03-sonnet-high-cell-and-sweep-removal.md`의 "다음" / 이어받을 상태: 기능의 slug가 아직 없어 브랜치
> 이름은 임시다. 인터뷰가 slug를 정하면 푸시하기 전에 브랜치를 `docs/<slug>`로 바꾸고 세션 제목도 그 이름으로 맞춘다 … 이번
> 요청 범위: PR과 병합까지

next-session 지시문으로 연 새 세션이다. 제목을 `docs/next-feature-grill`로 바꾸고, 주 체크아웃 미갱신이라 `tidy-checkouts`를
먼저 돌았다. 루트를 `f01ce1e9`에서 `8f0e5f81`로 당겼고, 지운 것은 워크트리 `03-upload-plan-first-canonical`과 브랜치
`feature/03-upload-plan-first-canonical`이다. 남긴 것은 도는 세션의 `031-sonnet-high-cell-and-sweep-removal`, 쉬는 세션의
`claude.exe`·`pwsh.exe`가 작업 디렉터리로 쥔 넷(`05-first-canonical-upload`, `08-admin-decision-column`, `12-main-run`,
`fable-design-spec`. 도구가 "끝낸다"가 아니라 "남긴다"로 냈다), 바뀐 파일이 있는 `06-round-drive-record`, 병합된 PR이 없는
명세 워크트리 넷(`admin-style-spec`, `admin-style-to-spec`, `mcp-shutdown-spec`, `web-widget-spec`), 앱 표지가 있는 둘이다.
사람에게 넘길 것은 없었다. 그 뒤 `EnterWorktree`로 `.claude/worktrees/next-feature-grill`에 들어가 브랜치를
`docs/next-feature-grill`로 바꿨다. 기준은 origin/main `8f0e5f81`이다. `grill-with-docs`로 시작했다.

## 찾은 사실

사실 조사는 서브에이전트 하나에 맡기고, 선택지 설명에 넣은 사실은 이 세션이 코드를 직접 읽어 대 봤다.

- **프론티어(손으로 봤다).** `.scratch/plan.md`의 기능 17개가 모두 `done`이다. 일지 2026-10-31-03의 "다음"이 새 기능을 고르는
  설계 인터뷰를 가리켰다.
- **플러그인 네 종류(코드를 읽었다).** PRD는 agent, mcp, skill, model 네 종류를 로드해 실행하는 런타임을 만든다고 적었는데,
  로더가 실제로 읽는 종류는 agent와 mcp 둘이다(`core/run.py`의 `_requested_manifest`·`_resolve_servers`). `plugins/skills/`와
  `plugins/models/`는 `.gitkeep`만 있다(`ls -la`). `PluginKind`는 넷이고(`sdk/manifest.py:19-27` "디렉터리와 값만 예약"),
  파일시스템 어댑터는 네 디렉터리와 운영자 파일의 네 키를 모두 안다(`adapters/filesystem.py:51-56, 73-92`). 관리 API의 `/plugins`
  목록은 `for kind in PluginKind`로 네 종류를 모두 훑는다(`admin/http.py:140-146`). 그래서 `plugins/models/`에 `plugin.toml`을
  두면 지금도 목록에 뜨고 켜고 끌 수 있지만, ADR 0017:49대로 "지금은 효과가 없다".
- **모델 호출(코드를 읽었다).** 모델은 프로세스 하나에 하나다. 이름은 플래그 → 환경변수 `AGENT_OS_MODEL` → 기본값
  `claude-opus-5` 순이고 빈 값은 거부한다(`adapters/anthropic.py:13-30`). `main.py:128-130`이 `ChatAnthropic`을 한 번 만들어
  `run`·`resume`·`serve`에 넘기고, `serve`의 독스트링은 "모델은 여기서 한 번 풀고 요청마다 고르지 않는다(ADR 0014)"다. 에이전트
  매니페스트에는 모델 칸이 없고(`sdk/manifest.py:56-82`), `ctx.llm(prompt)`은 인자가 프롬프트 하나다(`sdk/agent.py:57`). 루프는
  `bound.ainvoke`로 답이 끝난 뒤 한 덩어리를 받는다(`core/loop.py:65-66`). 이벤트의 `model`은 응답 메타데이터의 실제 모델
  이름이다(`core/model.py:40-43`).
- **미룬 결정(ADR을 읽었다).** ADR 0014:18은 "요청마다 모델을 고른다"를 "채널 토큰을 가진 쪽이 비용을 정하게 되고, 모델 플러그인이
  예약만 된 지금 이름을 검증할 기준이 없다"며 거부했다. ADR 0022:96-99는 대화 한도의 기본값을 모델의 컨텍스트 크기에 맞추는 일을
  "에이전트마다 모델이 달라질 때(모델 플러그인) 다시 본다"로 미뤘다. 반대 방향의 선례는 킥오프 때 헌법 v1.2.0이 모델 로더를
  비목표로 둔 것이다(일지 2026-09-19:226. 첫 슬라이스의 비목표였다).
- **스킬(서브에이전트가 grep으로 봤다, 이 세션이 다시 grep했다).** `src/`에 `SKILL.md`를 읽는 코드가 없다. 용어집은
  "에이전트의 컨텍스트에 주입되는 절차 지식의 폴더"로만 정의한다.
- **토큰 단위 스트리밍(ADR을 읽었다).** ADR 0014:31이 범위 밖으로 두었다.
- **후보 목록(일지를 읽었다).** 킥오프 일지 2026-09-19:170의 "확신 높음" 가운데 아직 없는 것은 스케줄러·웹훅 트리거, 토큰
  스트리밍, 에이전트가 에이전트 호출, 병렬 도구, 스킬 로더, 핫리로드·레지스트리, 원격·컨테이너 에이전트, 멀티 프로바이더, 모델
  라우팅, 비용 계량, RAG, 트레이스 DB·OTel, PII·가드레일, Docker다. 미정(:172)은 WASM, 빌더 UI, LangGraph Studio, Slack,
  카카오톡이다. `.scratch/retro-queue.md`에는 다음 기능 후보가 없다.
- **의존성(tech.md를 읽었다).** 모델 패키지는 `langchain-anthropic` 하나이고 anthropic SDK는 그 뒤에서 온다. core는
  `langchain-core`의 `BaseChatModel`을 포트로 쓴다(`.claude/rules/core.md`의 포트 표).

## 라운드

1라운드는 뿌리 셋(다음 기능, 범위, PRD)이었다. 셋 다 추천대로였다. 추천의 근거는 모델 플러그인이 PRD의 네 종류 가운데 빈 것이고,
이미 두 ADR이 그것이 생길 때 다시 보기로 미룬 결정을 들고 있어 다른 결정이 그 위에 선다는 것이었다.

> 사용자(질문에 답): "모델을 플러그인으로 등록 (Recommended)" — 설명: 지금은 서버 하나에 모델 하나뿐입니다(실행 플래그 → 환경변수
> AGENT_OS_MODEL → 기본값 순). plugins/models/ 폴더는 비어 있고, 거기에 plugin.toml을 두면 관리 목록에 뜨고 켜고 끌 수는 있지만
> 런타임이 읽지 않아 효과가 없습니다(ADR 0017). 고르면 런타임이 그 파일의 설정(제공사, 모델 id, 기본 파라미터)으로 실제 모델을
> 만들어 쓰고, 에이전트마다 다른 모델을 쓰는 길이 열립니다. 매니페스트와 관리 API 계약이 바뀝니다.

> 사용자(질문에 답): "기능 하나만 정함 (Recommended)" — 설명: 이번에 고른 기능 하나의 설계만 끝까지 묻고, 계획표(.scratch/plan.md)에는
> 그 기능의 행 하나를 더합니다. 다음 기능은 이 기능이 닫힐 때 다시 인터뷰로 고릅니다.

> 사용자(질문에 답): "성공의 정의에 다음 줄을 더함 (Recommended)" — 설명: 고른 기능으로 다음 성공의 정의 한 줄을 이번 인터뷰가
> 초안으로 씁니다. PRD는 사용자 승인으로만 바뀌므로 초안을 보여 드린 뒤 승인받아 같은 PR에 싣습니다. 성공의 정의가 원천이라 다음
> 기능의 '끝'이 PRD에 적힙니다.

2라운드는 모델 플러그인의 첫 가지 여덟이었고 호출 둘로 올렸다. 첫 호출의 넷 가운데 셋은 추천대로였고, 모델 파일의 내용은 추천(제공사와
id만)과 달리 닫힌 파라미터를 지금 넣기로 했다. 올리기 전에 서브에이전트 둘째가 모델 이름이 쓰이는 자리, 포트의 모양, 매니페스트
검증, 관리 화면의 매니페스트 표시를 조사했다(아래 "찾은 사실 (2)").

> 사용자(질문에 답): "model-plugin (Recommended)" — 설명: 폴더는 .scratch/model-plugin/, 이 브랜치는 docs/model-plugin, 구현 티켓
> 브랜치는 feature/NN-… 이 됩니다. 기존 기능 이름(plugin-toggle, mcp-shutdown, end-user-channel)처럼 단수입니다. 같은 이름의 폴더는
> 없습니다(ls .scratch로 봤습니다).

> 사용자(질문에 답): "매니페스트에 모델 이름 한 칸 (Recommended)" — 설명: 에이전트의 plugin.toml에 model = "이름" 한 칸을 둡니다(MCP를
> mcp = [...]로 적는 ADR 0002와 같은 모양). 실행 하나는 모델 하나를 쓰고, ctx.llm()은 지금처럼 인자가 프롬프트 하나입니다(sdk/agent.py).
> 칸이 없으면 서버 기본 모델(다음 질문)을 씁니다.

> 사용자(질문에 답): "플러그인 이름을 받는 서버 기본 모델로 (Recommended)" — 설명: --model과 AGENT_OS_MODEL은 모델 플러그인의 이름을
> 받고, 모델을 적지 않은 에이전트가 그것을 씁니다. 저장소가 기본 모델 플러그인 하나를 plugins/models/에 함께 둡니다. 코드에 박힌
> 기본값 claude-opus-5는 없어지고, 플래그도 환경변수도 없으면 지금 빈 모델 이름을 거부하는 자리(main.py가 ValueError를 받아 실패
> 코드로 끝내는 곳)에서 구성 오류로 실행 전에 끝납니다. 모든 모델이 관리 목록에 보이고 켜고 끌 수 있습니다. 시험과 CI가 넘기는 모델
> 이름을 플러그인 이름으로 바꿉니다(어느 자리가 넘기는지는 서브에이전트가 세는 중).

> 사용자(질문에 답): "제공사, id, 닫힌 파라미터 몇 개" — 설명: max_tokens, temperature처럼 이름을 정한 선택 칸을 지금 넣습니다. 칸마다
> 타입과 범위를 sdk가 검증하고 어댑터가 그대로 넘깁니다. 어떤 칸을 넣을지가 다음 라운드의 질문이 됩니다.

2라운드 둘째 호출은 모델 파일의 내용이 정해진 뒤에 열린 넷(파라미터의 범위, 제공사, 반영 시점, 관리 화면)이었고 넷 다 추천대로였다.
올리기 전에 설명의 사실을 대 봤다. langchain-anthropic 1.7.2의 `chat_models.py` 필드 줄(`max_tokens` 1098, `temperature` 1108,
`top_k`·`top_p`·`timeout`·`max_retries`·`stop_sequences` 1111-1124), `PluginList.tsx:23`의 `WITHOUT_LOADER`, `PluginDetail.tsx:43`의
`formatJson`, `core/run.py`의 `_requested_manifest`·`_resolve_servers`, `ports.py:34`, `tech.md`의 모델 패키지 한 줄이다.

> 사용자(질문에 답): "max_tokens와 temperature 둘 (Recommended)" — 설명: 둘 다 선택 칸입니다. max_tokens는 1 이상의 정수(없으면 지금의
> 고정값 16000), temperature는 0 이상 1 이하의 실수(없으면 제공사 기본값)입니다. 설치된 langchain-anthropic 1.7.2의 ChatAnthropic이
> 같은 이름의 필드로 받습니다(chat_models.py:1098, 1108). 값의 범위는 매니페스트를 읽는 단계에서 거부합니다(conversation_limit과 같은
> 엄격 검증).

> 사용자(질문에 답): "anthropic 하나 (Recommended)" — 설명: provider 값은 닫힌 목록이고 지금은 anthropic 하나입니다. 설치된 모델
> 패키지가 langchain-anthropic 하나입니다(docs/constitution/tech.md). 다른 값은 매니페스트를 읽는 단계에서 거부합니다. 멀티
> 프로바이더는 뒤 기능으로, 목록에 값을 더하는 가산 변경입니다.

> 사용자(질문에 답): "다음 실행부터 바로 (Recommended)" — 설명: 에이전트와 MCP 매니페스트처럼 실행을 시작할 때마다 파일에서
> 읽습니다(core/run.py의 _requested_manifest·_resolve_servers, ADR 0003). 서버를 다시 띄우지 않아도 되고 켜고 끄기도 다음 실행부터
> 듣습니다. 대가는 둘입니다. 모델 객체를 실행마다 만들고(만드는 것이 네트워크를 타지 않는다는 것은 어림), core의 모델 포트가 "모델
> 하나"(ports.py:34의 type ChatModel = BaseChatModel)에서 "모델 설정으로 모델을 만드는 것"으로 바뀌어 ADR이 필요합니다.

> 사용자(질문에 답): "안내 줄만 걷고 상세는 JSON 그대로 (Recommended)" — 설명: PluginList.tsx:23의 "로더 없는 종류" 집합에서 model을
> 빼, 모델 행의 "로더가 생기기 전에는 효과가 없다" 줄이 사라집니다. 상세는 지금처럼 매니페스트 JSON을 통째로 보여(PluginDetail.tsx:43)
> 새 칸이 그대로 보입니다. 화면 디자인 단계가 없고 생성 타입이 바뀌어 스토리·테스트 리터럴만 고칩니다.

3라운드는 2라운드가 연 가지 넷(기본 모델 플러그인의 이름, 서버 기본 모델을 시작 때 확인하는지, 모델 파일의 칸 이름, 트레이스에 플러그인
이름을 남기는지)이었다. 셋은 추천대로였고, 이름은 사용자가 선택지 밖의 답을 직접 적었다. 같은 opus라도 버전이 다른 플러그인을 나란히
등록할 수 있어야 하므로 이름이 버전을 들어야 한다는 조건이 섰고, 추천한 `opus`는 그 조건에 맞지 않아 물린다. 정확한 글자는 4라운드에서
정한다(이름 패턴 `^[a-z][a-z0-9-]{1,62}$`가 `.`을 받지 않아 `opus5.5` 그대로는 쓸 수 없다, 아래 "찾은 사실 (3)"). 올리기 전에 대 본 사실도
"찾은 사실 (3)"에 있다.

> 사용자(질문에 답): "opus5, opus5.5 등 같은 opus라도 버전이 다르면 추가로 등록할 수 있어야해"

> 사용자(질문에 답): "시작 때 그 이름을 한 번 읽어 확인 (Recommended)" — 설명: serve가 시작할 때 그 이름의 모델 매니페스트를 한 번 읽어,
> 없거나 읽히지 않으면 지금 빈 이름을 거부하는 구성 오류 목록(main.py의 _configuration_problems. 토큰·호스트·사이트 파일 문제와 한
> 목록으로 한 번에 나옵니다)에 들어 실행 전에 끝납니다. 오타(AGENT_OS_MODEL=opsu)가 첫 요청의 500이 아니라 시작에서 보입니다. 사이트
> 파일을 시작 때 한 번 읽는 자리(ADR 0023)와 같은 자리입니다. 꺼짐은 보지 않습니다(운영자가 언제든 바꾸는 상태라 실행마다 판정해 409).
> 실행은 시작 때 읽은 것을 쓰지 않고 실행마다 다시 읽습니다(앞 라운드의 결정). CLI run·resume도 지금 빈 이름을 거부하는 자리에서 같은
> 확인을 합니다. 대가: 시작이 플러그인 폴더를 한 번 읽습니다(지금 serve 시작은 FilesystemPlugins를 만들기만 하고 읽지 않습니다). API 키는
> 지금처럼 시작 때 보지 않습니다.

> 사용자(질문에 답): "provider, model_id (Recommended)" — 설명: 모델 파일은 provider = "anthropic", model_id = "claude-opus-5"와 선택 칸
> max_tokens, temperature입니다. 용어집(CONTEXT.md의 모델 항목)이 모델을 'provider, model id, 기본 파라미터'로 부르는 말 그대로입니다.
> 에이전트 파일의 칸은 model = "opus"(플러그인 이름)이라, 모델 파일의 id 칸을 model로 두면 같은 키가 두 파일에서 다른 뜻이 됩니다.
> 매니페스트는 종류별로 칸을 거부하므로(sdk/manifest.py:84-102) 네 칸은 model 밖에서, model 칸은 agent 밖에서 거부합니다.

> 사용자(질문에 답): "남기지 않는다 (Recommended)" — 설명: 트레이스는 지금처럼 모델 호출 이벤트(llm_called)와 대화 요약 이벤트의 model
> 칸에 응답이 돌려준 실제 모델 이름(core/model.py:40-43)을 남깁니다. 어느 플러그인이었는지는 그 이름과 매니페스트로 거슬러 봅니다. 이벤트
> 형식, openapi.json, 관리 화면의 필드 이름 표가 바뀌지 않습니다. 대가: 같은 id를 가리키며 파라미터만 다른 두 플러그인은 트레이스로
> 가르지 못합니다.

4라운드는 이름의 글자, PRD 줄의 초안, 합의 요약(질문에 올리지 않고 가정한 것 일곱 묶음)이었고 셋 다 추천대로였다. 이것으로 프론티어가
비었다. 올리기 전에 대 본 사실은 `PluginSource.read_manifest(kind, name)`가 이미 있다는 것(`core/ports.py:343`), ADR 0008이 버전을
올리는 기준을 "기존 필드의 뜻이나 필수 여부가 바뀔 때"로 적고 필드가 는 두 번(2026-09-21, 2026-10-03)을 자기 이력에 쌓았다는 것(:27, :33-37),
ADR 0002 본문은 "에이전트 매니페스트의 `mcp = [...]`에 적힌 mcp 플러그인만 런타임이 연결한다"라 모델 칸이 늘어도 그대로 참이라는 것,
`plan.md`의 슬라이스 번호가 1~4까지 쓰였다는 것(행 17개를 Grep으로 셌다)이다.

> 사용자(질문에 답): "claude-opus-5 (Recommended)" — 설명: 이름이 제공사의 모델 id 그대로입니다. 다음 버전은 claude-opus-5-5로 그것도 id
> 그대로라 이름 규칙을 따로 정할 것이 없고, 두 플러그인이 나란히 선 관리 목록에서 어느 것이 무엇인지 바로 보입니다. 이름 패턴(sdk/ids.py:22,
> 소문자·숫자·하이픈)을 지납니다. 폴더는 plugins/models/claude-opus-5/plugin.toml, 서버 기본 모델은 AGENT_OS_MODEL=claude-opus-5입니다. 대가:
> 깁니다.

> 사용자(질문에 답): "이 초안으로 (Recommended)" — 설명: 넣을 줄: "- 그다음: 모델 플러그인. 에이전트가 매니페스트로 고른 모델로 돌고, 모델
> 파일을 고치거나 켜고 끈 것이 서버를 다시 띄우지 않아도 다음 실행부터 듣는다." 지금 세 줄(2026-09-22 LLM 호출, 2주 안 CLI, 그다음 슬라이스
> 셋) 바로 뒤에 선다. 문체는 셋째 줄("그다음 슬라이스 셋: …")과 같고 기한은 적지 않습니다(셋째 줄도 기한이 없습니다). PRD는 사용자 승인으로만
> 바뀝니다.

> 사용자(질문에 답): "요약대로 맞다 (Recommended)" — 설명: 1) 모델 파일: plugins/models/<이름>/plugin.toml에 공통 넷(schema_version "1", kind
> "model", name, version)과 provider, model_id, 선택 max_tokens·temperature. 이 다섯 칸은 다른 종류에서, 에이전트의 model 칸은 다른 종류에서
> 거부. 형식 버전은 "1" 그대로(기존 칸의 뜻이 안 바뀜. ADR 0008 이력에 적음). 2) 읽기: 실행마다 에이전트의 model(없으면 서버 기본 모델
> 이름)으로 모델 매니페스트를 기존 포트 메서드(read_manifest)로 읽고 그 설정으로 모델 객체를 만듦. 없거나 읽히지 않으면 깨짐(PluginError,
> 운영자 500, 최종 사용자 고정 문구 500), 꺼졌으면 Disabled 409(순서 에이전트 → mcp → 모델). 재개도 같은 준비를 지나 지금 매니페스트의
> 모델, 대화 요약도 그 실행의 모델. core의 ChatModel 포트가 '모델 설정으로 모델을 만드는 것'이 되고(포트 수 다섯 그대로) 어댑터
> anthropic_chat_model이 provider anthropic의 구현, main이 조립. API 키는 지금처럼 ANTHROPIC_API_KEY 환경변수이고 모델 파일에 없으며 시작
> 때 보지 않음. 3) 서버 기본 모델: --model과 AGENT_OS_MODEL의 이름·순서는 그대로, 값이 플러그인 이름. 코드 기본값 제거. 둘 다 없거나
> 비었거나 그 이름의 모델 매니페스트가 없거나 읽히지 않으면 구성 오류로 실행 전 종료(serve는 목록, CLI run·resume은 지금 ValueError 자리).
> 꺼진 기본 모델은 시작을 막지 않고 그것을 쓰는 실행이 409. 4) 트레이스·관리: 이벤트 형식 그대로. 관리 API 경로는 안 늘고(네 종류를 이미
> 다룸) openapi.json의 PluginManifest에 새 칸이 들어 계약 변경이라 첫 티켓이 계약 티켓. 5) 저장소·시험: 기본 모델 파일 하나(model_id
> claude-opus-5, max_tokens 16000, 지금 동작 그대로). calc 에이전트는 model 칸 없이 기본 모델. 시험·CI·e2e 스택 둘이 기본 플러그인 이름을
> 넘김. -m llm 시험은 그 플러그인으로 실제 호출. 6) 범위 밖: 토큰 스트리밍, 요청마다 모델 고르기(ADR 0014 거부 유지), 둘째 제공사,
> thinking·model_kwargs·나머지 파라미터, 대화 한도의 모델별 기본값(ADR 0022가 모델 플러그인 때 다시 보기로 한 것. 다시 봤고 이번에 넣지
> 않음. 그 이력에 적음), 스킬 로더. 7) 이 PR의 산출물: ADR 0040 초안(셀프 리뷰 뒤 승인), ADR 0010·0014·0017·0022 본문 포인터와 ADR
> 0008·0022 이력, CONTEXT.md에 '기본 모델(Default Model): 운영자가 서버나 CLI를 시작할 때 이름으로 고른 모델. 모델을 적지 않은 에이전트가
> 쓴다' 추가(모델 항목은 그대로), plan.md에 슬라이스 5 model-plugin 행(todo)과 프론티어 문단, PRD 줄. 규칙 파일(.claude/rules의
> sdk·core·adapters)과 코드는 구현 티켓이 고침. 바로 다음 단계는 명세(to-spec, 사용자가 부름).

## 찾은 사실 (2)

서브에이전트 둘째의 보고다. 이 세션이 선택지에 쓴 것은 다시 열어 봤다.

- **모델 이름이 쓰이는 자리(서브에이전트가 Grep으로 봤다).** `tests/adapters/test_anthropic.py:16-36`(빈 환경이면 기본값, 환경 값,
  플래그 우선, 빈 문자열 거부. 생성에는 원시 이름), `tests/test_main.py:1049-1068`(`anthropic_chat_model`을 몽키패치해 받은 이름
  기록, 328·1081은 `--model ""`), `tests/channel/cli/test_main.py:33·75·153`(`--model m`), `tests/core/test_model.py:78-79`(`-m llm`,
  환경에서 이름을 푼다). `.github/workflows`, `README.md`, `web/`에는 일치가 없고, 두 e2e 스택(`admin/e2e/stack.ts:75-95`,
  `widget/e2e/stack.ts:108-133`)은 `--model` 없이 `serve`를 띄워 부모 환경을 펼치므로 모델은 `AGENT_OS_MODEL`이거나 기본값이다(코드를
  읽었다).
- **포트와 진입점(코드를 읽었다).** `core/ports.py:34`의 `type ChatModel = BaseChatModel`은 타입 별칭이고 "첫 어댑터는 langchain-anthropic의
  ChatAnthropic이고 main.py가 만든다"(:33). `run()`·`resume()`은 `model: ChatModel`을 키워드 전용으로 받아 `_Body(model=model)`로
  넘기고(`run.py:664-677, 752-765`), 대화 요약 `summarize(model, …)`도 같은 인스턴스를 받는다(`continuation.py:610-632`,
  `run.py:1180-1189`). `.claude/rules/adapters.md:11`은 "ChatAnthropic 인스턴스는 `adapters/anthropic.py`의 factory로 `main.py`가
  만든다", ADR 0014:29는 "모델은 `serve` 수준에서 시작 때 한 번 푼다. … 모델 플러그인이 생기면 다시 본다"다.
- **매니페스트 검증(코드를 읽었다, `sdk/manifest.py:84-102`).** `entrypoint`는 agent만 필수이고 다른 종류는 있으면 거부, `mcp`·
  `requires_approval`·`conversation_limit`은 agent 밖에서 적기만 해도 거부, `server`는 mcp만 필수. `extra="forbid"`라 model 종류는
  지금 `schema_version`·`kind`·`name`·`version`만 가질 수 있고 새 필드는 모르는 키로 거부된다. 최소 model 매니페스트가 읽히는지 보는
  양성 시험은 `test_manifest.py`에 없고, `test_server.py:154-161`의 `SONNET`이 그 꼴로 파싱될 뿐이다. `test_filesystem.py:236`은
  `list_manifests(MODEL) == ()`다.
- **관리 화면(코드를 읽었다).** 매니페스트용 라벨 표는 없고 `PluginDetail.tsx:43`이 `formatJson(plugin.manifest)`로 매니페스트를
  통째로 JSON 글자로 보인다. `PluginList.tsx:15-20`의 `KIND_NAMES`에 `model: "모델"`이 있고, :23의 `WITHOUT_LOADER`에 model이 들어
  :226-231이 "로더가 생기기 전에는 효과가 없다" 줄을 그린다. 생성 타입 `PluginManifest`(`openapi.ts:567, 581`)는 앱이 직접 import하지
  않고 `api/plugins/index.ts:8-10`의 `Plugin`·`PluginRow`를 거쳐 `PluginDetail.tsx:43`과 `RunDecision.tsx:75`(`row.manifest.mcp`)가
  쓴다. 스토리·테스트 리터럴(PluginDetail·PluginList·RunDetail의 stories, HomePage·PluginPage·RunPage.decision의 test)이 매니페스트
  필드를 전부 적는다. 필드가 늘면 직렬화 스키마에서 required가 되어 그 리터럴이 컴파일에서 깨진다는 것은 어림이다.
- **매니페스트 리터럴(서브에이전트가 git grep으로 봤다).** 공통 픽스처는 없고 파일마다 헬퍼가 따로 있어 파이썬 7곳(`test_run.py:115`,
  `test_end_user.py:158`, `test_router.py:115`, `test_main.py:70`, `test_server.py:123`, `test_filesystem.py:55`, `test_manifest.py:10`),
  TS 2곳(`admin/e2e/stack.ts`의 `manifest()`, `widget/e2e/plugins.ts:56`)이다. `plugins/agents/calc/plugin.toml`은 여섯 줄이고
  `mcp = ["everything"]`까지다.

## 찾은 사실 (3)

3라운드를 올리기 전에 이 세션이 직접 대 본 것이다.

- **재개가 읽는 매니페스트(코드를 읽었다).** `run.py`의 `resume()`은 `_prepare(plugins, _recorded_manifest(plugins, resumption.started))`로
  트레이스의 시작 이벤트가 든 에이전트 이름으로 지금 디스크의 매니페스트를 읽는다. 없으면 "실행 … 의 에이전트 플러그인이 없다"
  `PluginError`(`run.py:1397`). 그래서 멈춘 사이 에이전트의 모델 칸을 바꾸면 재개는 새 모델을 쓰고, 재생 구간은 기록된 응답을 되살리므로
  기록 끝 이후의 호출만 새 모델에 간다(mcp와 같은 규칙). 준비(`_prepare`, `run.py:1217-1240`)의 순서는 깨짐(`_resolve_servers`, 마스킹과
  승인의 충돌) → 꺼짐(`_reject_disabled`) → 진입점 import이고, 대화 요약 `summarize(model, …)`은 `run.py:1189`에서 그 실행의 모델을 받는다.
- **시작 이벤트의 칸(코드를 읽었다, `sdk/events.py:53-61`).** `RunStarted`는 `agent`, `request`, `principal`, `previous_run`, `shortcuts`뿐이고
  모델 칸이 없다. `LlmCalled.model`은 `str`이다(:86).
- **플러그인 이름 패턴(코드를 읽었다, `sdk/ids.py:22`).** `^[a-z][a-z0-9-]{1,62}$`. 소문자, 숫자, 하이픈뿐이라 `opus5.5`는 거부되고
  `opus5`, `opus-5`, `claude-opus-5`, `claude-opus-5-5`는 지난다.
- **serve 시작의 검사(코드를 읽었다, `main.py:106-180`).** `main()`은 serve를 먼저 가르고(주석: "serve 가 빈 모델 지정을 다른 구성 오류와 한
  목록에 모아 내기 때문"), CLI 길은 `_chat_model(args.model)`의 `ValueError`를 받아 `EXIT_FAILED`다. `_serve()`는 토큰·OS 사용자·사이트
  파일(`_read_sites`, 시작 때 한 번 읽고 요청마다 읽지 않는다, ADR 0023)을 `_configuration_problems`에 모아 한 번에 내고, 플러그인은
  `FilesystemPlugins(args.plugins_root)`를 `create_app`에 넘기기만 하며 시작 때 읽지 않는다. API 키는 시작 때 보지 않는다.
- **`tools/`의 `--model`(코드를 읽었다).** `tools/canary.py:535`와 `tools/rerun_session.py:225`의 `--model`은 `claude` CLI를 띄우는 인자라
  런타임의 플래그와 무관하다. `.github/`, `web/`의 `.ts`, `.claude/`의 `.md`에는 `--model`도 `AGENT_OS_MODEL`도 없다(Grep).
- **기본값 글자(Grep).** `claude-opus-5`를 적는 곳은 `src/`에서 `adapters/anthropic.py:13`의 `DEFAULT_MODEL` 하나다. `tests/`의 일치는 모두
  `tools/` 시험의 `claude-opus-5-5`(Claude Code 세션 모델)라 런타임 시험은 그 글자를 직접 적지 않고 상수를 쓴다. `.env.example`은
  `PYTHONUTF8`, `ANTHROPIC_API_KEY`, 관리·채널 토큰 넷이고 `AGENT_OS_MODEL`은 없다.
- **PRD(읽었다, `docs/PRD.md`).** 성공의 정의는 세 줄이고 셋째가 "그다음 슬라이스 셋: HTTP 채널, 관리 API와 화면, 위젯. 순서와 의존은
  `.scratch/plan.md`."다. 운영자 문제 문장이 "어떤 에이전트, 도구, 모델이 등록돼 돌아가는지 한 곳에서 보고 켜고 끄고 싶다"다.
- **용어집(읽었다, `CONTEXT.md:94-96`).** 모델(Model): "이름을 가진 LLM 설정. provider, model id, 기본 파라미터를 묶는다. API 키 값은 담지
  않는다. _Avoid_: 프로바이더 설정, 엔드포인트, 모델 프로필". 기본 모델이라는 용어는 없다.
- **옛 결정의 문장(읽었다).** ADR 0014:29 "모델은 `serve` 수준에서 시작 때 한 번 푼다. … 모델 플러그인이 생기면 다시 본다", ADR 0014:18
  "요청마다 모델을 고른다. … 거부했다", ADR 0010:159 "`serve`에 `--model`이 는다. CLI와 같은 규칙(`--model` > `AGENT_OS_MODEL` > 기본값)으로
  시작 때 한 번 푼다", ADR 0017:49 "skill과 model은 로더가 생길 때 그 로더가 켜짐을 본다. 지금은 효과가 없다", ADR 0022:33 "요약은 그
  실행이 쓰는 모델과 … 모델은 CLI와 `serve`가 같은 규칙(…)으로 푼다(ADR 0014)", ADR 0022:96-99 "기본 한도를 모델의 컨텍스트 크기에 맞추는
  일은 에이전트마다 모델이 달라질 때(모델 플러그인) 다시 본다". `docs/model-selection.md`는 Claude Code 세션 모델의 문서라 런타임 기본
  모델과 무관하다(Grep).

## 산출물

선례는 mcp-shutdown 설계 세션(일지 2026-10-16-36)이다. 규칙 파일(`.claude/rules/sdk.md`·`core.md`·`adapters.md`)과 코드는 구현 티켓이
고친다(ADR 0040 Consequences). 명세(`to-spec`)는 사용자가 부르는 다음 단계다.

- `docs/adr/0040-model-is-a-plugin-built-per-run-from-its-manifest.md` 초안과 `docs/adr/README.md`의 색인 행. 승인 전이라 status는
  `proposed`이고 승인 뒤 `accepted`로 바꾼다.
- 본문 포인터 넷 `(바뀜: ADR 0040)`(0010의 것은 이어받은 세션이 뗐다. 아래 "이어받음" 절): ADR 0014의 "모델은 `serve` 수준에서 시작 때 한 번 푼다", ADR 0010 이력의 "`serve`에 `--model`이
  는다", ADR 0017의 "skill과 model은 로더가 생길 때 … 지금은 효과가 없다", ADR 0022의 "모델은 CLI와 `serve`가 같은 규칙(`--model` > `AGENT_OS_MODEL` > 기본값)으로 푼다".
  ADR 0014:18의 "요청마다 모델을 고른다 … 거부했다"는 거부한 안의 그때 근거라 달지 않았고(`.claude/rules/adr.md`의 "달지 않는 것"),
  ADR 0002 본문("`mcp = [...]`에 적힌 mcp 플러그인만 런타임이 연결한다")은 그대로 참이다.
- 이력 둘: ADR 0008(모델 매니페스트의 칸 넷과 에이전트의 모델 칸, `schema_version` "1" 그대로), ADR 0022(대화 한도의 모델별 기본값은
  두지 않는다).
- `CONTEXT.md`에 기본 모델(Default Model) 항목. 모델 항목은 그대로다.
- `.scratch/plan.md`에 슬라이스 5 `model-plugin` 행(`todo`)과 프론티어 문단의 끝 두 문장.
- `docs/PRD.md` 성공의 정의 넷째 줄(4라운드에서 승인받은 초안 그대로).

## 검증

- `uv run ruff check .` 초록, `uv run ruff format --check .` 초록(1187 files already formatted). 이 브랜치는 `.py`를 바꾸지 않았다.
- `uv run python tools/run_checks.py`는 백그라운드로 띄웠다가 인계하며 멈췄다(아래 "인계"). 결과가 없으니 새 세션이 다시 돌린다.

## 인계

셀프 리뷰 직전에 인계 계기(`hook_handoff`, 세션 컨텍스트 327,100 토큰)가 와서 `next-session` `handoff.md`를 따랐다. 인계하지 않는 때 다섯에
들지 않았다(계기를 낸 명령이 실패하지 않았고, 요청 범위는 PR과 병합까지이고, 지시문의 이어받을 상태는 `인계:`로 시작하지 않았고, 일지에
`인계 못함` 줄이 없고, `get_session self`에 `parentSessionId`가 없다). 이 세션의 제목은 `docs/model-plugin`이었고 넘기며 `docs/model-plugin
(인계함)`으로 바꾼다. 셀프 리뷰(`/code-review`)는 밟지 않았다. 새 세션이 한다. 이 세션이 번복하거나 고친 것은 3라운드의 추천 `opus`가
사용자의 조건(버전이 다른 opus를 나란히 등록한다)에 밀려 4라운드에서 `claude-opus-5`로 정해진 것 하나다.

지시문:

```
다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계 인터뷰의 마무리(셀프 리뷰, ADR 0040 승인, PR과 병합)
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /grill-with-docs
브랜치: docs/model-plugin
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-10-31-04-model-plugin-design.md(라운드 넷의 답과 합의 요약, "산출물"·"검증"·"인계" 절)
이어받을 상태: 인계: 셀프 리뷰 직전 docs/journal/2026-10-31-04-model-plugin-design.md. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main)부터 한다. 인터뷰는 끝났고(4라운드에서 합의 요약을 확인받아 프론티어가 비었다) 산출물은 다 썼다. ADR 0040은 status proposed이고 셀프 리뷰를 반영한 뒤 사용자에게 보여 승인받고 accepted로 바꾼다(docs/adr/README.md의 색인 행도). 넘기며 멈춘 run_checks는 결과가 없어 다시 돌린다. ruff 둘은 초록이었다. 면제 PR(docs/ 브랜치, 티켓 없음)이고 PR 뒤는 merge.md의 "워크트리에서 병합할 때", 그 뒤 retro와 next-session(다음 단계는 명세 to-spec, 사용자가 부른다).
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-31T04:51:26Z

## 이어받음 (셀프 리뷰 직전)

위 지시문으로 연 새 세션이다. 첫 턴 훅대로 제목을 `docs/model-plugin`으로 바꾸고, `git worktree list`에서 그 브랜치가 체크아웃된 워크트리 `next-feature-grill`(`8f0e5f81`, origin/main과 같다)을 찾아 `EnterWorktree(path)`로 들어갔다. `grill-with-docs`가 가리키는 `grilling`·`domain-modeling`은 Skill 도구로 한 번씩 불렀고, 인터뷰는 4라운드에서 프론티어가 비었으므로 라운드를 다시 올리지 않고 셀프 리뷰부터 이었다. `uv run python tools/sibling_overlap.py`는 번호 겹침 없음이었다(이 브랜치의 새 번호는 일지 2026-10-31-04와 ADR 0040, 다음 빈 번호는 일지 2026-10-31-05, 대기열 554, 티켓 032). 함께 고친 파일로 `mcp-shutdown-spec` 워크트리의 `.scratch/plan.md`를 들었다.

- **run_checks(인계하며 멈춘 것을 다시 돌렸다).** `uv run python tools/run_checks.py`를 백그라운드로 돌려 pytest만 빨갰다(1 failed, 5917 passed, 379초). 실패는 `tests/tools/test_check_adr_pointers.py::test_이_저장소의_ADR_포인터는_전부_이력_제목과_맞는다`이고 출력은 `0010-http-surface-assembled-by-server.md:159: (바뀜: ADR 0040) — 이력 절 안에 있다`였다. 앞 세션이 ADR 0010 이력(2026-09-24 항목)의 "`serve`에 `--model`이 는다" 뒤에 단 포인터가 `## 이력` 절 안이라 검사가 거부한다(`tools/check_adr_pointers.py` 독스트링의 "포인터가 `## 이력` 절 안에 있다. 포인터는 본문의 표시이고, 지난 이력 항목은 기록이다"와 `.claude/rules/adr.md`의 달지 않는 것). 그 포인터를 뗐고 ADR 0010은 origin/main과 같아졌다. `uv run python tools/check_adr_pointers.py`가 출력 없이 끝났다. 나머지 검사(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify 457초)는 Passed였다. 합의 요약 7)의 "ADR 0010·0014·0017·0022 본문 포인터" 가운데 0010의 그 문장은 본문이 아니라 이력이라 포인터 없이 두고, ADR 0040 Consequences의 "ADR 0014와 ADR 0010 이력의 '시작 때 한 번 푼다'가 바뀐다"는 산문 그대로다.
- **PR 직전 리뷰의 길.** `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 CLI 축은 돌지 못하고 대체 둘(`/security-review`, `bug-perf-review`)로 간다. `git fetch origin` 뒤에도 origin/main은 `8f0e5f81`이다.

## 셀프 리뷰

`/code-review`의 두 축을 서브에이전트로 돌렸다. 범위는 base `8f0e5f81`(HEAD와 같다), 바뀐 추적 파일 아홉, 커밋 0, 미추적 둘(ADR 0040, 이 일지)이다. 명세는 티켓이 없어 이 일지 라운드 절의 사용자 답(라벨과 설명 글자 그대로)과 합의 요약 일곱 묶음이었고, "산출물"·"찾은 사실" 절은 요구가 아닌 참고로 넘겼다.

### 표준 축 (sonnet·high) 보고와 판정

1. Major. ADR 0010:159의 `(바뀜: ADR 0040)`이 `## 이력` 절 안이다(`check_adr_pointers.py` rc=1). → 고쳤다(위 "이어받음"의 run_checks 항목. 리뷰 전에 같은 실패를 보고 뗐다).
2. Major(판단). 두 e2e 스택은 `--plugins-root`로 임시 루트(`join(work, "plugins")`)를 쓰고 관리 스택은 `models/sonnet/plugin.toml`을 공통 넷만으로 쓴다(`admin/e2e/stack.ts:68·84·232`, `widget/e2e/stack.ts:95·117`). 이름만 넘기면 시작 때 구성 오류다. → 고쳤다. ADR 0040 "저장소가 기본 모델 플러그인 하나를 둔다"에 격리된 루트에 모델 매니페스트를 두는 문장과 두 스택의 지금 모양을 적었다. 이 세션이 두 스택의 그 줄과 `manifest` 헬퍼(`stack.ts:163-164`, 공통 넷에 `extra`를 붙인다)를 다시 읽었고, 위젯 e2e의 `plugins.ts`에는 모델 픽스처가 없었다(grep).
3. Minor(판단). ADR 0008 새 이력의 "옛 매니페스트가 다르게 해석될 여지가 없다"는 공통 넷뿐인 모델 매니페스트(`tests/test_server.py:154-161`의 `SONNET`)가 거부되는 것을 가린다. → 고쳤다. 소리 나는 거부라고 바로 적고 그 픽스처를 구현 티켓이 고친다고 ADR 0008 이력과 ADR 0040 "모델 매니페스트의 모양"에 적었다. `schema_version` "1"은 사용자가 확인한 요약 1) 그대로다.
4. Minor. "`ChatAnthropic`이 받는 파라미터 … `model_kwargs`까지다"가 닫힌 주장인데 `betas`, `output_config`, `reasoning_effort` 등이 더 있다. → 고쳤다. `ChatAnthropic.model_fields`를 `uv run python -c`로 세니 36개였고, 목록을 성질(생성 파라미터, 호출 설정, 그대로 넘기는 칸)의 예시로 바꿨다. `timeout`은 `default_request_timeout`의 별칭이다(`chat_models.py:1117`, grep).
5. Minor. "ADR 0022·0031의 선례"에서 0022는 형식을 3으로 올린 반례다(ADR 0022:23을 읽었다). → 고쳤다. 선례를 ADR 0031과 ADR 0009의 2026-09-22 이력으로 바꾸고 0022는 올린 쪽이라고 적었다.
6. Nit. ADR 0003은 파일시스템이 원천이라고만 한다(ADR 0003을 읽었다). → 고쳤다. 실행마다 읽는 근거를 코드(`_requested_manifest`·`_resolve_servers`)로 적었다.
7. Minor. `README.md:40`의 "skill과 model은 로더가 생길 때 그 로더가 켜짐을 본다"가 구현 뒤 거짓이 되는데 고칠 곳 목록에 없다. → 고쳤다. ADR 0040 "이번 범위 밖"의 구현 티켓이 고치는 목록에 더했다. 이 세션이 같은 낱말들(`--model`, `AGENT_OS_MODEL`, `DEFAULT_MODEL`, `claude-opus-5`, `ChatAnthropic`, `로더가 생길`, `모델 하나`, `시작 때 한 번`)로 README·CLAUDE.md·CONTEXT.md·CODING_STANDARDS.md·docs/constitution·docs/agents·.claude/rules·.claude/skills·plugins를 grep하니 그 밖은 Claude Code CLI의 `--model`(operations.md:76)과 이미 든 adapters.md:11뿐이었다.
8. Nit. 용어집은 "기본 모델"인데 ADR 0040과 plan.md 행이 "서버 기본 모델"을 쓴다. → 고쳤다. ADR 0040·0008·0022와 plan.md 행에서 "기본 모델"로 바꿨다(sed, 남은 것 0). 일지의 인용은 기록이라 그대로다.
9. Nit. ADR 0022 새 이력의 "위 이력의"가 2026-10-15 이력 둘 가운데 어느 것인지 모른다. → 고쳤다. 둘째 이력의 제목을 적었다.

표준 축이 맞다고 확인한 것: 포인터 셋(0014·0017·0022)의 자리와 모양, ADR 0022 이력 인용, `read_manifest`(`ports.py:343`), 준비 순서, `_recorded_manifest`, `_configuration_problems`, `is_plugin_name`(`opus5.5`·`Opus` 거부, `claude-opus-5`·`claude-opus-5-5`·`opus`·`opus5` 수용), `conversation_limit`의 `strict=True, ge=1`, ADR 0023:39, `core/model.py:40-43`, 일지의 파일:줄 인용 12곳, PRD 줄의 승인, plan.md 행의 형식, 기준선 냄새 없음. `check_md_tables`·`check_line_separators` rc=0.

### 명세 축 (이 세션의 모델) 보고와 판정

1. Minor. 요약 7)의 "ADR 0010·0014·0017·0022 본문 포인터" 가운데 0010의 것이 작업 트리에 없다(리뷰 도중 뗐다). 그 문장은 `## 이력` 안이라 기록이고 포인터를 달지 않는 것이 맞다고 보고했다. → 뗀 것이 맞다. "산출물" 절의 그 항목에 뗐다는 괄호를 달았다.
2. Minor. 3라운드 "시작 때 그 이름을 한 번 읽어 확인"의 대가 "시작이 플러그인 폴더를 한 번 읽습니다(지금 serve 시작은 FilesystemPlugins를 만들기만 하고 읽지 않습니다)"가 ADR에 없다. → 고쳤다. ADR 0040 "기본 모델"에 그 대가를 적었다(`main.py`의 `_serve`가 `FilesystemPlugins(args.plugins_root)`를 `create_app`에 넘기기만 하는 것은 위 "찾은 사실 (3)"이 읽은 코드다).
3. Minor. 2라운드 "안내 줄만 걷고 상세는 JSON 그대로"의 "화면 디자인 단계가 없고"가 ADR에 없다. 하네스가 화면 작업 전에 `ui-design`을 부르므로 명세 단계가 헛 디자인 단계를 열 수 있다. → 고쳤다. ADR 0040 "계약이 바뀐다"에 "화면 디자인 단계(`ui-design`)는 없다"를 적었다.
4. Nit. plan.md 행이 요약 3)의 조건(비었거나, 읽히지 않으면, CLI run·resume)을 줄였다. → 고쳤다. 행에 네 조건과 serve·CLI의 자리를 적었다.
5. Nit. ADR의 거부한 안 가운데 `default`·`id`는 사용자에게 올라간 선택지가 아니다(일지에 기록 없음). 거부 근거 문장이라 결정은 아니다. → 고쳤다. 그 둘은 선택지로 올리지 않고 이 세션이 견준 안이라고 ADR에 적었다. `opus`는 추천했다가 물린 것, `model`은 3라운드 설명이 견준 것으로 출처를 갈랐다.
6. Nit. CONTEXT.md의 `_Avoid_: 폴백 모델, 서버 모델, 전역 모델`은 요약 7)에 없던 줄이고 ADR의 "서버 기본 모델"과 긴장이 있다. → 용어집 형식(CONTEXT-FORMAT.md)이 `_Avoid_`를 두므로 줄은 두고, 표준 축 8의 용어 통일로 긴장을 풀었다.
7. Nit. "(ADR 0003)" 출처 귀속. → 표준 축 6과 같은 지적이고 고쳤다.

명세 축이 맞다고 잰 것: 준비 순서와 `core.md:34`, `http/errors.py:290·305-306`의 409·500, `MAX_TOKENS = 16000`, `DEFAULT_CONVERSATION_LIMIT = 20_000`, `uv.lock:531`의 1.7.2, 이벤트 이름(`events.py:85·185`), `uv run python` 프로브로 이름 패턴(`opus5.5` 거부, `opus5`·`claude-opus-5`·`claude-opus-5-5`·`default` 통과)과 `conversation_limit`의 엄격 검증(`"16000"`·`16000.0`·`true`·`0`·`-1` 거부, mcp 종류에 적으면 거부)과 지금 매니페스트가 `provider`·에이전트 `model` 칸을 거부하는 것(extra forbid), 인용 일치(PRD 줄 글자 그대로, CONTEXT '기본 모델' 본문, ADR 0008:27 기준, 0022:98-99, 0014:18, 0017:49, PRD:8, sdk.md:16, adapters.md:11, core.md:15), ADR 번호 열 개의 제목, 범위 밖 여섯, 요약 1)~5)의 조건, 잔존 grep 0건.

고친 것: 표준 축 1~9, 명세 축 1~5·7(위). 남긴 것: 없음(명세 축 6은 용어 통일로 풀렸다). 다시 돌린 명령: `uv run python tools/check_adr_pointers.py` 출력 없음. 나머지 검증 명령은 커밋의 pre-commit으로 갈음하고 결과는 커밋 뒤에 적는다.

반영으로 새로 쓴 사실 문장(PR 직전 `bug-perf-review`에 밀 주장으로 넘긴다): ADR 0040의 "설치된 langchain-anthropic 1.7.2의 `ChatAnthropic.model_fields`는 36개다", "`timeout`은 `default_request_timeout`의 별칭이다", "선택 칸을 더하며 형식을 그대로 둔 선례는 ADR 0031과 ADR 0009의 2026-09-22 이력이다. ADR 0022는 재개의 입력이 되는 이벤트가 늘어 3으로 올린 쪽이다", "공통 넷만 적은 모델 매니페스트(`tests/test_server.py`의 `SONNET`, 관리 화면 e2e 스택의 `models/sonnet` 픽스처가 그 꼴이다)는 필수 칸이 없어 같은 단계에서 거부되고", "두 스택(…)은 지금 `--plugins-root`로 임시 루트에 픽스처 플러그인을 쓰고 `--model` 없이 띄워 기본값에 기대며, 관리 스택의 모델 픽스처 `models/sonnet`은 공통 넷뿐이라 새 규칙에서 읽히지 않는다", "이름만 넘기면 `serve`가 시작 때 구성 오류로 끝난다", "지금 `serve` 시작은 `FilesystemPlugins`를 만들기만 하고 읽지 않는다", "실행마다 읽는 것은 `core/run.py`의 `_requested_manifest`·`_resolve_servers`다", "`README.md`의 `disabled.toml` 줄", "`model`은 3라운드 선택지의 설명이 견줬고 `id`는 선택지로 올리지 않고 이 세션이 견준 안이다", "`opus`는 이 세션이 추천했으나 … `default`는 선택지로 올리지 않고 이 세션이 견준 안"; ADR 0008 이력의 "런타임은 지금까지 모델 매니페스트를 읽지 않았고 저장소에도 파일이 없어, 옛 파일이 다른 뜻으로 읽힐 동작이 없다"와 "공통 넷만 적은 모델 매니페스트(ADR 0017대로 운영자가 두었을 수 있고, …)는 새 필수 칸이 없어 매니페스트를 읽는 단계에서 검증 오류로 거부된다"; ADR 0022 이력이 가리키는 이력 제목; plan.md 행의 "기본 모델이 없거나 비었거나 그 이름의 모델 매니페스트가 없거나 읽히지 않으면 구성 오류다(`serve`는 시작 때 한 목록으로, CLI `run`·`resume`은 지금 빈 이름을 거부하는 자리에서)".

## ADR 0040 승인

셀프 리뷰를 반영한 뒤 ADR 0040 전문과 초안에서 고친 것(ADR 0010 포인터 뗌, 용어 "기본 모델" 통일, e2e 스택의 격리 루트, 공통 넷뿐인 옛 모델 파일의 거부, `ChatAnthropic` 필드 36개, 트레이스 형식 선례, README 잔존, 시작 때 폴더 읽기의 대가, 화면 디자인 단계 없음, `default`·`id`의 출처)을 보여 승인을 물었다.

> 사용자(질문에 답): "승인한다 (Recommended)" — 설명: ADR 0040의 status를 accepted로, docs/adr/README.md 색인 행의 상태도 accepted로 바꿉니다. 그 뒤 회고(retro), 커밋, PR 직전 보안 리뷰, PR, 봇 리뷰 반영, 병합까지 묻지 않고 진행합니다. 4라운드에서 확인한 결정은 그대로이고 위에 적은 사실 문장 고침만 더해진 상태로 승인하는 것입니다.

ADR 0040의 `status`와 `docs/adr/README.md`의 0040 행을 `accepted`로 바꿨다.

## PR 직전 리뷰

CodeRabbit CLI 자리가 없어(위 "이어받음") `bug-perf-review` 서브에이전트에 위 "셀프 리뷰" 끝의 밀 주장 열둘을 넘겼다. 기준 `8f0e5f81`, 범위 10개 파일(추적 8, 미추적 2)이고 호출 40번에 닿아 멈췄으며 백그라운드 작업은 남기지 않았다. 보안 축(`/security-review`)은 커밋 뒤에 돈다. 보고를 받기 전에 이 세션의 컨텍스트가 자동 압축으로 한 번 접혔다(요약으로 이었다).

### 버그·성능 축 보고와 판정

1. Minor. `temperature`가 엄격 검증인지 ADR이 적지 않았다(`max_tokens`만 "엄격한 정수"). 2라운드 답의 설명은 둘 다 "conversation_limit과 같은 엄격 검증"이다. 글자대로 `Field(ge=0, le=1)`로 구현하면 TOML의 `true`가 1.0으로, `"0.5"`가 0.5로 통과한다. → 유효, 고쳤다. 이 세션이 pydantic 2.13.5(`uv.lock`)로 `TypeAdapter(Annotated[float, Field(strict=True, ge=0, le=1)])`를 불러 `True`·`"0.5"`의 거부(`float_type`)와 `0`·`1`·`0.5`의 수용, `2.0`·`-0.1`의 범위 거부를 봤다(lax는 `True`→1.0, `"0.5"`→0.5로 통과한다). ADR 0040 "모델 매니페스트의 모양"에 둘 다 엄격 검증이고 정수 `0`·`1`은 받는다고 적었다.
2. Minor. 구현 티켓이 고칠 곳 목록에 넷이 빠졌다. `README.md:96`의 `serve` 줄(모델 이름 없이 띄우면 구성 오류가 된다), `.env.example`(`AGENT_OS_MODEL`이 없다. 이 세션이 열어 보니 `PYTHONUTF8`, `ANTHROPIC_API_KEY`, 토큰 둘뿐이다), `.claude/rules/core.md:34`의 `Disabled` 문장(에이전트와 그 mcp까지만 든다), `.claude/rules/sdk.md:12`의 종류별 칸 불릿. → 유효, 고쳤다. ADR 0040 "준비 단계에 모델 판정이 는다"와 "이번 범위 밖"의 목록에 더했다.
3. Minor. 기본 모델의 이름이 core에 드는 입구(`run()`·`resume()`은 지금 `model: ChatModel` 하나를 받는다)와 모델의 없음·깨짐이 준비의 어디에 서는지가 침묵이다. → 유효, 고쳤다. ADR 0040 "준비 단계에 모델 판정이 는다"에 둘은 명세가 정하고 시험이 고정한다고 적었다. 꺼짐의 자리(에이전트 → mcp → 모델)는 이미 있었다.
4. Minor(보류). `default`·`id`를 "선택지로 올리지 않았다"는 문장을 일지로 확인하지 못했다(일지는 고른 답만 적는다). → 유효였고, 이 세션의 셀프 리뷰 반영이 틀렸던 것이다. 앞 세션의 기록 파일(`~/.claude/projects/C--project-agent--claude-worktrees-next-feature-grill/c9fbb918-….jsonl`)에서 `AskUserQuestion` 입력을 스크립트로 읽으니 3라운드의 두 질문은 선택지 셋씩이었다. 이름은 `opus (Recommended)`·`claude-opus-5`·`default`(사용자는 선택지 밖의 답을 적었다, 위 3라운드 인용), 칸 이름은 `provider, model_id (Recommended)`·`provider, id`·`provider, model`이었다. 명세 축 지적 5("일지에 기록 없음")를 일지만 보고 받아들여 ADR에 "선택지로 올리지 않고 이 세션이 견준 안"이라 썼던 것을 되돌리고, 두 선택지의 설명이 견준 것으로 고쳤다. 고르지 않은 두 선택지의 설명 원문은 아래다.

> `default`: 폴더 이름이 쓰임새(기본)를 말합니다. 대가는 말이 겹치는 것입니다. '서버 기본 모델'은 운영자가 --model로 고른 어느 플러그인이든 될 수 있어 이름 default인 플러그인이 기본이 아닌 상태가 생기고, 둘째 모델 플러그인을 들이면 이름이 내용(어느 모델인지)을 말하지 않습니다.

> `provider, id`: 가장 짧습니다. 대가: 플러그인 이름 name과 제공사의 모델 id인 id가 같은 파일에 나란히 서서, 파일만 봐서는 어느 것이 관리 목록의 이름이고 어느 것이 제공사에 보내는 값인지 헷갈립니다.

맞다고 확인한 것(오탐 없음): 밀 주장 열둘이 모두 코드·문서와 맞았다(`ChatAnthropic.model_fields` 36개와 `timeout` 별칭, 트레이스 형식 선례, 두 e2e 스택과 `models/sonnet`, `_serve`가 `FilesystemPlugins`를 만들기만 함, `_prepare`의 순서, README·sdk.md·adapters.md 인용, ADR 0008 이력과 `schema_version`, ADR 0022 이력 제목과 `DEFAULT_CONVERSATION_LIMIT`, `_configuration_problems`와 CLI의 `EXIT_FAILED`, ADR 0010 포인터 뗌, ADR 0040 안의 모순 없음). 성능: `ChatAnthropic` 생성자는 0.07ms이고 인스턴스 20개가 httpx 클라이언트를 공유한다. pydantic 2.13.5에서 `model_id`는 보호 이름공간 경고가 없다. 따라가지 못한 것: `tests/test_server.py`의 `SONNET`(셀프 리뷰 표준 축이 `:154-161`로 읽었다), `create_app`, `FilesystemPlugins`의 생성자, `admin/http.py`.

고친 것: 1~4(ADR 0040의 다섯 자리). 남긴 것: 없음. 다시 돌린 명령: `tools/check_quotes.py`(두 미추적 파일을 넘겨 인용 58건, 경고 6건. 모두 ADR을 고치기 전의 옛 문구를 적은 기록, 작은따옴표로 바꾼 인용, 줄을 넘는 인용이고, "산출물" 절의 ADR 0022 인용 하나는 괄호를 뺀 줄임이라 원문 그대로 고쳤다), `check_md_tables.py`·`check_line_separators.py`·`check_adr_pointers.py` 출력 없음.

## 회고

retro 스킬대로 돌았다(`writing-for-agents`를 불렀고, 원천은 이 일지와 이 세션이다. 압축 뒤라 위 "PR 직전 리뷰" 절까지 읽고 돌았다). `uv run python tools/queue_open_rows.py`와 `git fetch origin` 뒤 `--ref origin/main`의 출력이 같았다. 열린 행 153, 회차 3 이상 28행(442가 10회차), 사람 몫 238, 만료할 행 없음. 후보 일곱, 승인 둘(이 세션에서 반영 하나, 대기열 하나), 기각 다섯, 넘김 없음.

1. 승인, 반영. **`uv run python -I`로 돌린 스크래치 스크립트의 한글 출력이 cp949로 나가 깨졌다.** 앞 세션의 기록 파일에서 `AskUserQuestion` 입력을 읽는 스크립트(위 "PR 직전 리뷰" 4)의 첫 실행이 15,370자의 깨진 글자로 돌아와 `sys.stdout.reconfigure(encoding="utf-8")`을 넣고 다시 돌렸다. 열린 행 484(40의 2회차)가 처방한 사건 그대로라 3회차이고, 더하는 것(규약 한 줄)의 문턱을 지나 이 세션에서 반영했다. `docs/constitution/operations.md` 환경 규약 상세의 `PYTHONUTF8` 줄 아래에 `-I`는 `PYTHON*` 환경 변수를 모두 무시하니 `-X utf8`을 함께 준다는 줄을 더했고(`print("한글 출력 확인")`이 `-I`만으로는 깨지고 `-I -X utf8`과 `-I` 없이는 그대로인 것을 손으로 봤다), 면제 PR이라 harness 티켓 032(`.scratch/harness/issues/032-isolated-python-utf8-line.md`)를 같은 PR에 쓰고 484를 그 경로로 닫았다. 새 훅·검사가 아니라 `hook_report.py`는 돌리지 않았다.
2. 승인, 대기열 554(1회차). **설계 인터뷰의 일지가 고른 답만 적어, 고르지 않은 선택지가 ADR의 거부한 안으로 들어가도 저장소에 그 출처가 없다.** 사건은 위 "PR 직전 리뷰" 4다. 셀프 리뷰 명세 축이 일지에 기록이 없다며 `default`·`id`를 선택지가 아니었다고 냈고, 이 세션이 일지만 보고 받아들여 ADR에 거짓 출처를 썼다. 층은 지침(`grilling` 사본의 "옮길 때")이라 세 번째에 더한다. 닫힌 46(고른 선택지의 설명을 옮긴다)이 덮지 못한 틈이고 같은 일은 아니라 새 행이다.
3. 기각. 앞 세션이 ADR 0010 `## 이력` 안에 단 포인터는 저장소 상태 테스트(`tests/tools/test_check_adr_pointers.py`)가 run_checks에서 잡았다. 검사가 제 몫을 했다.
4. 기각. 도구 결과가 문턱 10,000자를 넘은 호출 셋(`core.md` grep 13,289자, 일지 `sed` 10,621자, 위 1의 깨진 출력 15,370자)은 `hook_large_result`가 그 자리에서 알렸다.
5. 기각. PR 직전 리뷰가 잡은 ADR의 빠짐 셋(`temperature` 엄격 검증, 고칠 곳 넷, 이름의 입구와 깨짐의 자리)은 리뷰가 제 몫을 한 것이고, 검사로 옮길 수 없으며 표준에 더할 새 판단 기준도 아니다.
6. 기각. `hook_choice_facts`가 승인 화면을 처음 한 번 막고 같은 화면을 다시 불러 떴다. 그 훅의 설계대로다.
7. 기각. `bug-perf-review`가 호출 40번에 닿아 넷을 따라가지 못했으나 놓친 지적이 없었다. 상한은 그 에이전트 정의의 값이고 사건이 없다.

이 세션의 컨텍스트는 PR 직전 리뷰 보고를 기다리는 사이 자동 압축으로 한 번 접혔다(위 "PR 직전 리뷰"). 요약에 인계 계기의 흔적이 없어 세지 않는다.

## 다음

기능 model-plugin은 설계가 끝났고 `.scratch/model-plugin/`이 없는 단계다. 다음은 명세(`/to-spec`, 사람이 부른다)이고, `next-session` 결정표의 "설계는 끝났고 `spec.md`가 없다" 줄이라 새 세션을 Fable 5.1 / xhigh로 연다. 화면 디자인 단계는 없다(ADR 0040 "계약이 바뀐다"). 명세가 정할 것은 ADR 0040이 "명세가 정한다"고 미룬 것이다. 격리된 플러그인 루트(시험·CI·두 e2e 스택)에 둘 모델 매니페스트의 이름, 기본 모델의 이름이 core에 드는 입구(`run()`·`resume()`의 새 인자인지, 모델을 만드는 것이 이름을 드는지)와 그 이름을 `read_manifest`에 넘기기 전에 `is_plugin_name`으로 거를지(아래 "PR 직전 보안 리뷰" 2. 지금 `resolve_model_name`은 빈 값만 거부하고, 디렉터리 이름과 매니페스트 `name`의 대조가 어차피 막는다), 모델의 없음·깨짐이 깨짐 안에서 mcp의 앞인지 뒤인지, 그리고 구현 티켓이 고칠 곳 목록(README의 `serve` 줄과 `disabled.toml` 줄, `.env.example`, `.claude/rules/core.md`·`adapters.md`·`sdk.md`의 문장들, `tests/test_server.py`의 `SONNET`과 관리 스택의 `models/sonnet` 픽스처, `PluginList.tsx`의 로더 없는 종류 집합)이다. 3라운드 두 질문의 선택지 전부와 고르지 않은 둘의 설명은 위 "PR 직전 리뷰" 4에 있다(대기열 554). 이 PR은 면제 PR(`docs/model-plugin`)에 회고가 쓴 harness 티켓 032를 함께 싣는다(헌법 3.0.64). PR과 병합, 그 뒤의 `next-session` 지시문은 이 세션이 이어서 한다.

- 워크트리에서 병합하므로 주 체크아웃은 당기지 않는다. 주 체크아웃 미갱신: 루트는 main(`git worktree list`의 첫 줄, 커밋 뒤 이어받은 세션이 봤다). 새 세션이 워크트리에 들어가기 전에 `tidy-checkouts`로 당긴다.

## 인계 (커밋 뒤)

커밋 `209b2f6a`(14개 파일, 463줄 더함·18줄 지움)가 pre-commit을 지나 섰다. `checks`(run_checks의 CHECKS 전부), 마크다운 표, 줄 구분 문자, 변이 표, 헌법 판, 인용 대조, 커밋 메시지가 Passed이고, `ruff` 둘과 canary specs는 대상 파일이 없어 Skipped다. 인용 대조 경고 7건은 README의 옛 메모 둘과 이 일지가 ADR을 고치기 전 문구를 적은 기록 다섯이라 막지 않았다. 커밋이 서자 인계 계기(`hook_handoff`. 세션 컨텍스트 354,831 토큰, 경계 `커밋 뒤`)가 왔고, `handoff.md`를 Read로 열어 따랐다. 인계하지 않는 때 다섯에 들지 않는다. 커밋은 성공했고, 요청 범위는 PR과 병합까지라 이 경계에서 끝나지 않고, 이 세션의 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 같은 경계가 아니고, 이 일지에 `인계 못함` 줄이 없고, `get_session self`에 `parentSessionId`가 없다. 열린 PR은 없다(`gh pr view docs/model-plugin`이 없음으로 끝났다). 그래서 넘긴다.

이 세션의 사용자 프롬프트는 둘이다. 첫째는 위 "인계" 절의 지시문을 `open-session`이 `.claude/skills/grill-with-docs/SKILL.md 를 읽어 그대로 따른다. … 인자:` 한 줄로 옮긴 것이고, 둘째는 위 "ADR 0040 승인"의 답이다. 이 세션이 번복하거나 고친 것은 위 "셀프 리뷰"(표준 축 아홉, 명세 축 일곱), "PR 직전 리뷰"(넷. 그 4는 이 세션의 셀프 리뷰 반영이 틀렸던 것을 되돌렸다), "회고"(대기열 484 닫음, 554 신설, harness 티켓 032, 헌법 3.0.64)에 있다. 이 세션의 제목은 `docs/model-plugin`이고, 아래 지시문을 낸 뒤 `docs/model-plugin (인계함)`으로 바꾼다.

새 세션이 할 일은 커밋 뒤의 남은 단계다. `/security-review`(보고를 이 일지에), 푸시와 PR(`/git-pr`. 면제 PR에 harness 티켓 032가 함께 든다), `@coderabbitai review` 코멘트와 `wait_ci`의 봇 회차, 워크트리에서의 병합(`merge.md` "워크트리에서 병합할 때"), 그 뒤 `next-session`(다음 단계는 명세 `/to-spec`, 사람이 부른다)이다. 회고는 이 세션이 커밋 전에 돌았다(위 "회고"). 이 절은 커밋하지 않았으므로 새 세션이 다음 커밋에 싣는다.

지시문:

```
다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계 인터뷰의 마무리(PR 직전 보안 리뷰, PR과 병합, next-session)
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /grill-with-docs
브랜치: docs/model-plugin
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-10-31-04-model-plugin-design.md의 "이어받음 (셀프 리뷰 직전)" 절부터 끝까지("다음"과 "인계 (커밋 뒤)" 절까지)
이어받을 상태: 인계: 커밋 뒤 docs/journal/2026-10-31-04-model-plugin-design.md. 브랜치의 커밋 하나(209b2f6a, pre-commit 초록. ruff 둘과 canary specs는 대상 파일이 없어 Skipped)에 셀프 리뷰 반영, ADR 0040 승인(accepted), PR 직전 bug-perf-review 반영, 회고(대기열 484 닫음·554 신설, harness 티켓 032, 헌법 3.0.64), 일지 "다음"까지 실었다. 푸시하지 않았고 열린 PR은 없다. 인터뷰는 끝났으니 라운드를 올리지 않는다. 남은 것: /security-review(보고를 일지에), 푸시와 PR(/git-pr. 면제 PR에 harness 032 동봉), @coderabbitai review 코멘트와 wait_ci의 봇 회차, 워크트리에서의 병합(merge.md "워크트리에서 병합할 때"), 그 뒤 next-session(다음 단계는 명세 to-spec, 사람이 부른다. 명세 브랜치 선례는 docs/<slug>-spec). 회고는 앞 세션이 커밋 전에 돌았다(일지 "회고"). 일지의 "인계 (커밋 뒤)" 절은 커밋하지 않았으니 다음 커밋에 싣는다.
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-31T05:54:35Z

## 이어받음 (커밋 뒤)

위 지시문으로 연 새 세션이다. 첫 턴 훅대로 제목을 `docs/model-plugin`으로 바꾸고, `git worktree list`에서 그 브랜치가 체크아웃된 워크트리 `next-feature-grill`(`209b2f6a`)을 찾아 `EnterWorktree(path)`로 들어갔다. `grill-with-docs`가 가리키는 `grilling`·`domain-modeling`은 Skill 도구로 한 번씩 불렀고, 인터뷰는 끝났으므로 라운드를 올리지 않고 커밋 뒤의 남은 단계부터 이었다. `git fetch origin` 뒤에도 origin/main은 `8f0e5f81`로 이 브랜치의 밑과 같다. `uv run python tools/sibling_overlap.py`는 번호 겹침 없음이었다(다음 빈 번호는 일지 `2026-10-31-06`, 대기열 555, 티켓 034. 이 브랜치의 일지 2026-10-31-04를 이름순으로 앞서는 형제는 `wireframe-optional` 워크트리의 2026-10-31-05이고, 함께 고친 파일은 `mcp-shutdown-spec` 워크트리의 `.scratch/plan.md`다). `coderabbit auth status`는 여전히 `Plan: Free`, `Seat: not assigned`라 CLI 축은 돌지 못한다(PR 템플릿대로 PR마다 다시 봤다).

## PR 직전 보안 리뷰

운영 규약(리뷰 파이프라인 2)의 대체 둘 가운데 보안 축이다(버그·성능 축은 앞 세션의 위 "PR 직전 리뷰"). 내장 `/security-review`를 커밋 `209b2f6a` 위에서 돌렸다. origin/main 위에 바로 선 브랜치라 합칠 것이 없었고, 그 명령이 모은 범위는 커밋 하나와 바뀐 파일 14개(전부 마크다운)다. 커밋하지 않은 이 일지의 "인계 (커밋 뒤)" 절은 그 diff에 들지 않아 서브태스크에 따로 보라고 넘겼다. 취약점을 찾는 서브태스크 하나(general-purpose, 호출 24번)를 띄웠고, 보고가 발견 없음이라 오탐을 거르는 서브태스크는 띄우지 않았다.

### 보안 축 보고와 판정

보고는 High·Medium 발견 없음이고 확인한 것은 넷이다. 이 세션이 보고가 인용한 네 자리(`sdk/ids.py:22`의 패턴, `adapters/filesystem.py:132-135`의 이름 대조와 `:173-175`의 `_manifest_path`, `adapters/anthropic.py:18-24`의 `resolve_model_name`)를 `sed`로 다시 읽으니 보고와 같았다.

1. 비밀 값(명령으로 봤다). diff 전체를 좁은 패턴(`sk-ant-`, `ghp_`, `AKIA`, `-----BEGIN`, `api_key = "…"`, `Bearer`)과 넓은 패턴(`api.?key`, `token`, `secret`, `password`)으로 훑어 일치 0건. `ANTHROPIC_API_KEY`는 환경 변수 이름으로만 나온다(ADR 0040과 이 일지).
2. 플러그인 이름으로 경로를 잇는 자리의 경로 탐색(코드를 읽었다). `_manifest_path`는 루트, 종류 폴더, 이름, `plugin.toml`을 검증 없이 잇지만, `read_manifest`가 읽은 매니페스트의 `name`이 디렉터리 이름과 다르면 `PluginError`를 내고, 그 `name`은 `sdk/manifest.py:63`에서 `PLUGIN_NAME_PATTERN`(`^[a-z][a-z0-9-]{1,62}$`)으로 묶여 `.`·`/`·`\`가 든 이름은 설령 경로 조립까지 닿아도 이름 대조에서 거부된다. HTTP 경계(`admin/http.py:160·189`, `channel/http/bodies.py:28`)도 같은 패턴으로 막고, ADR 0040은 관리 API의 경로를 늘리지 않는다. `--model`·`AGENT_OS_MODEL`은 신뢰된 값으로 봤다. 참고로 지금 `resolve_model_name`은 빈 값만 거부하고 `is_plugin_name`을 부르지 않으며, ADR 0040 "기본 모델"도 그 이름을 `read_manifest`에 넘기기 전의 패턴 판정을 적지 않는다. 취약점은 아니고(이름 대조가 막는다) 심층 방어 거리라 발견으로 올리지 않았다.
3. 매니페스트 값의 노출(코드와 문서를 읽었다). 모델 매니페스트의 칸(`provider`, `model_id`, `max_tokens`, `temperature`)에 비밀이 될 칸이 없고 API 키는 환경 변수 그대로다(ADR 0040, `adapters/anthropic.py:3`). 트레이스는 바뀌지 않는다. `adapters/filesystem.py:257-269`의 `_parse`가 pydantic 오류 문구(`input_value`가 든다)를 `PluginError`에 싣고 운영자 면이 그 원문을 500으로 내는 것(`http/errors.py:306`. 최종 사용자 면은 고정 문구)은 기존 동작이고 모델 파일에 비밀이 없어 신규 노출이 아니다. 요청 경로를 바꾸는 칸(`default_headers`, `base_url`, `model_kwargs`)을 모델 파일에 두는 안은 ADR 0040이 거부했다.
4. 인증·인가, 주입, 역직렬화. 새 HTTP 경로와 인증 변경이 없고, 매니페스트는 `tomllib`과 pydantic으로 읽으며 `eval`·`pickle`·YAML은 설계에 없다. 커밋하지 않은 일지 수정에도 비밀 값이 없다.

고친 것: 없음. 남긴 것: 없음. 2의 심층 방어 거리(기본 모델 이름을 `read_manifest`에 넘기기 전에 `is_plugin_name`으로 거를지)는 ADR 0040이 기본 모델 이름이 core에 드는 입구를 명세에 미뤘으므로 위 "다음"의 명세가 정할 것에 더했다.

## 인계 (PR 연 뒤)

커밋 `277fe0e9`(이 일지만, 47줄 더함·1줄 지움)가 pre-commit을 지나 섰다. `checks`(러너의 CHECKS 전부. pytest 426초, web-verify 565초), 마크다운 표, 줄 구분 문자, 변이 표, 인용 대조(인용 2건, 경고 없음), 커밋 메시지가 Passed이고, `ruff` 둘(이 세션이 손으로 쳐 `All checks passed!`, `1188 files already formatted`)과 canary specs, 헌법 판 검사는 대상 파일이 없어 Skipped다. 커밋이 서자 `커밋 뒤` 인계 계기(컨텍스트 225,256 토큰)가 왔으나, 이 세션의 지시문의 "이어받을 상태"가 `인계: 커밋 뒤`로 시작해 인계하지 않는 때 3이라 넘기지 않고 이었다. 브랜치를 푸시하고 `/git-pr`대로 PR #442(머리 `277fe0e9`, base main)를 열었다. 사용자가 앞 세션에서 PR·봇 반영·병합까지 묻지 않고 진행한다고 승인했으므로(위 "ADR 0040 승인"의 설명) 그 스킬의 생성 전 확인은 묻지 않았다. PR을 열자 `PR 연 뒤` 인계 계기(컨텍스트 253,049 토큰)가 왔고 `handoff.md`를 Read로 열어 따랐다. 인계하지 않는 때 다섯에 들지 않는다. PR은 열렸고, 요청 범위는 PR과 병합까지라 이 경계에서 끝나지 않고, 이 세션의 지시문의 "이어받을 상태"는 `인계: 커밋 뒤`라 같은 경계가 아니고, 이 일지에 `인계 못함` 줄이 없고, `get_session self`에 `parentSessionId`가 없다. 그래서 넘긴다. `@coderabbitai review` 코멘트는 남기지 않았고 `wait_ci` 대기도 띄우지 않았다(새 세션이 `merge.md` 2부터 한다). 앱은 PR #442를 이 세션에 묶었다(`get_session self`의 `prNumber`가 442).

이 세션의 사용자 프롬프트는 하나다. 위 "인계 (커밋 뒤)" 절의 지시문을 `open-session`이 `.claude/skills/grill-with-docs/SKILL.md 를 읽어 그대로 따른다. … 인자:` 한 줄로 옮긴 것이다. 이 세션이 번복하거나 고친 것은 없다. 더한 것은 위 "이어받음 (커밋 뒤)"·"PR 직전 보안 리뷰" 절과 "다음"의 두 줄(기본 모델 이름의 `is_plugin_name` 판정, 주 체크아웃 미갱신)이다. 이 세션의 제목은 `docs/model-plugin`이고, 아래 지시문을 낸 뒤 `docs/model-plugin (인계함)`으로 바꾼다.

새 세션이 할 일은 `merge.md` 2(봇 회차)부터다. `@coderabbitai review` 코멘트, `wait_ci`, 봇 회차의 반영, 워크트리에서의 병합("워크트리에서 병합할 때"), 그 뒤 `next-session`(다음 단계는 명세 `/to-spec`, 사람이 부른다)이다. 이 절은 커밋하지 않았으므로 새 세션이 봇 회차의 커밋에 싣는다.

지시문:

```
다음 작업: 기능 model-plugin. 모델 플러그인을 런타임이 읽게 하는 설계 PR #442의 봇 회차와 병합, 그 뒤 next-session
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /grill-with-docs
브랜치: docs/model-plugin
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-10-31-04-model-plugin-design.md의 "이어받음 (커밋 뒤)" 절부터 끝까지("다음" 절은 그 앞에 있고 이미 갱신됐다), .claude/skills/next-session/merge.md
이어받을 상태: 인계: PR 연 뒤 docs/journal/2026-10-31-04-model-plugin-design.md. PR #442(머리 277fe0e9, 커밋 둘, origin/main 8f0e5f81 위, 면제 PR에 harness 032 동봉)를 열었고 @coderabbitai review 코멘트와 wait_ci는 아직이다. merge.md 2(봇 회차)부터 한다: 코멘트를 남기고 wait_ci를 백그라운드로 띄운다. 인터뷰는 끝났으니 라운드를 올리지 않는다. 병합은 워크트리에서 한다(merge.md "워크트리에서 병합할 때". 주 체크아웃 미갱신 줄은 일지 "다음"에 이미 있다). 일지의 "인계 (PR 연 뒤)" 절은 커밋하지 않았으니 봇 회차의 커밋에 싣는다(고친 것이 없는 회차면 merge.md 2의 뒤로 넘긴 일과 3의 일지 규칙대로). 병합 뒤 next-session의 다음 단계는 명세 /to-spec(사람이 부른다. 결정표 "설계는 끝났고 spec.md가 없다" 줄, Fable 5.1 / xhigh. 명세 브랜치 선례는 docs/<slug>-spec). 회고는 앞 세션이 돌았다(일지 "회고").
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-31T06:18:44Z

## 이어받음 (PR 연 뒤)과 봇 회차

위 지시문으로 연 새 세션이다. 첫 턴 훅대로 제목을 `docs/model-plugin`으로 바꾸고 워크트리 `next-feature-grill`(`277fe0e9`)에 `EnterWorktree(path)`로 들어갔다. `grill-with-docs`가 가리키는 `grilling`·`domain-modeling`은 인터뷰가 끝났고 이번 범위가 PR과 병합까지라 부르지 않았다. 지시문대로 `merge.md` 2부터 이었다.

`@coderabbitai review` 코멘트를 남기고 `gh pr checks`를 한 번 읽으니 `python`·`visual`이 pending이라 `wait_ci`를 백그라운드로 띄웠고, 출력 마지막 줄이 `끝: 모두 통과`였다(머리 `277fe0e9`. 출력 파일을 손으로 읽었다).

- **CodeRabbit.** 무료 오픈소스 한도에 걸려 리뷰가 없다(`gh pr view 442 --json comments`로 읽은 CodeRabbit 코멘트의 `Review limit reached`와 `Review rate limited`, 다음 리뷰는 코멘트가 말한 약 56분 뒤. 검사는 `wait_ci` 출력에서 `NEUTRAL`). 한도에 걸린 푸시는 회차로 세지 않는다(`merge.md` 2).
- **claude-review 첫 회차.** 같은 명령으로 읽은 코멘트 본문에 Critical·Major 없음. Minor 둘(ADR 0010 이력의 "시작 때 한 번 푼다"에 포인터 없음, ADR 0001 이력의 "ChatModel 포트" 문장)과 Nit 하나(Consequences 첫 불릿에 칸 목록과 검증 기록이 섞임)를 고치지 않았다. 앞의 둘은 지난 이력 항목이라 기록이고(`.claude/rules/adr.md`의 "달지 않는 것"), ADR 0010 포인터는 앞 세션이 달았다가 `test_check_adr_pointers.py`가 막아 걷은 것이다(위 "회고" 3). 뒤로 넘기는 일은 아니라 "다음"에 더한 것이 없다. 보류 이유는 PR 코멘트에 지적마다 남겼다.

고친 것이 없는 회차라 이 절과 위 "인계 (PR 연 뒤)" 절만 일지 커밋으로 푸시한다. 그 푸시로 도는 claude-review는 둘째 회차라 Critical·Major만 고치고, 보류한 일은 PR 코멘트에 적는다.
