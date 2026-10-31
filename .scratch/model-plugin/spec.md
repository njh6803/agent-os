# model-plugin 명세: 모델 플러그인을 런타임이 실행마다 읽어 모델을 만든다

Status: ready-for-agent

설계는 ADR 0040과 설계 일지 2026-10-31-06이다. 이 명세는 그 설계가 명세에 넘긴 것을 정하고, 설계가 이미 정한 것은 다시 결정하지 않고 티켓이 읽을 자리에 옮긴다. 용어는 `CONTEXT.md`의 모델(이름을 가진 LLM 설정)과 기본 모델(운영자가 서버나 CLI를 시작할 때 이름으로 고른 모델)이다.

**넘겨받은 것은 열둘이다.** (1) 모델은 `plugins/models/<이름>/plugin.toml`의 플러그인이고 에이전트는 매니페스트의 선택 칸 `model`로 고르며 없으면 기본 모델이다. (2) 기본 모델은 `--model` > `AGENT_OS_MODEL` 순으로 받는 모델 플러그인의 이름이고 코드의 기본값은 없어지며, 둘 다 없거나 비었거나 그 이름의 모델 매니페스트가 없거나 읽히지 않으면 구성 오류다(`serve`는 시작 때 한 목록으로, CLI `run`·`resume`은 지금 빈 이름을 거부하는 자리에서). (3) 런타임은 실행을 준비할 때마다 `PluginSource.read_manifest(MODEL, 이름)`으로 그 매니페스트를 읽고, 없거나 읽히지 않으면 없는 mcp와 같은 `PluginError`(운영자 면 500, 최종 사용자 면 고정 문구 500), 꺼졌으면 `Disabled`(409)다. 꺼짐의 순서는 에이전트 → mcp → 모델이고 재개도 같은 준비를 지나며 대화 요약은 그 실행의 모델이다. (4) core의 모델 포트가 "모델 하나"에서 "모델 설정으로 모델을 만드는 것"으로 바뀌고 포트는 다섯 그대로이며, `adapters/anthropic.py`가 `anthropic`의 구현이고 `main.py`가 조립하며 모델 객체는 실행마다 만든다. (5) 모델 매니페스트의 칸은 공통 넷에 `provider`(닫힌 목록, `anthropic`), `model_id`, 선택 `max_tokens`(1 이상의 엄격한 정수, 없으면 어댑터의 16000), 선택 `temperature`(0 이상 1 이하의 엄격한 실수, 없으면 제공사 기본값)이고, 다른 종류에 적힌 이 칸들과 에이전트가 아닌 종류의 `model`은 거부하며, `schema_version`은 "1" 그대로이고 공통 넷만 적은 옛 모델 파일은 읽는 단계에서 거부되어 상세는 500이고 `GET /plugins`는 그 파일의 행만 표지 행으로 낸다. (6) API 키는 모델 파일에 담지 않고 제공사의 환경변수이며 시작 때 보지 않는다. (7) 저장소가 `plugins/models/claude-opus-5/plugin.toml`을 두고 `calc`는 `model` 없이 기본 모델을 쓰며, 격리된 플러그인 루트로 `serve`를 띄우는 시험과 CI, 두 e2e 스택은 그 루트에 기본 모델이 가리키는 모델 매니페스트를 두고 그 이름을 넘기고, `-m llm` 시험은 그 플러그인으로 실제 모델을 부른다. (8) 계약이 바뀐다. `openapi.json`의 `PluginManifest`에 새 칸이 들고 생성 타입과 스토리·테스트의 매니페스트 리터럴이 바뀌며 관리 API의 경로는 늘지 않고, 관리 화면은 `PluginList.tsx`의 로더 없는 종류 집합에서 model을 빼 안내 줄을 걷고 상세는 매니페스트 JSON 그대로이며 화면 디자인 단계는 없고 첫 티켓이 계약 티켓이다. (9) 트레이스는 바뀌지 않는다. (10) 꺼진 모델의 최종 사용자 면은 종류와 이름 없는 고정 문구의 409다(ADR 0017의 2026-10-03 이력). (11) 이번 범위 밖은 ADR 0040의 "이번 범위 밖" 불릿이다. (12) 구현 티켓이 고칠 곳은 ADR 0040의 "구현 티켓이 고칠 곳" 불릿이다.

**하나는 사용자가 이 명세를 쓰며 골랐다.** 시험을 붙이는 자리(Testing Decisions의 "이음매").

**열하나는 명세가 넘겨받은 것 안에서 스스로 정했고 각 절 제목의 괄호에 "명세가 정했다"로 표시한다.** 포트의 모양, 기본 모델의 입구, 경계의 이름 검증, 시작 때 확인의 내용, 실행 준비의 순서, 모델 만들기의 자리와 실패의 종류, 어댑터의 모양, 꺼진 모델의 문구, 저장소의 기본 모델 플러그인과 격리 루트(이름, 넘기는 길, 둘째 모델 픽스처, 운영자 문서의 값), 고칠 자리의 묶음, 실제 모델 호출 하나.

**이력은 하나다.** ADR 0040의 2026-10-31 이력(명세가 정한 넷과 잰 것 하나).

(2026-10-31 명세 검토와 to-tickets: 검토가 "고칠 자리"의 묶음 경계에서 blocker 둘을 찾았다. 계약 묶음이 혼자 초록일 수 없고, 런타임과 가장자리는 나란히 돌 수 없으며 의존이 거꾸로였다. to-tickets가 묶음 셋을 티켓 여섯으로 다시 나눴고 사용자가 그 분할과 결정 칸의 미리 알림, 04와 06 사이의 화면 틈을 골랐다(일지 2026-10-31-08). 결정을 바꾸거나 더한 자리는 각 절 끝의 같은 표시 주석이고, 티켓은 `.scratch/model-plugin/issues/`다)

**거부한 안은 열셋이고 각 절의 "거부한 안:" 표시에 있다.**

측정은 `.scratch/model-plugin/probes/`의 둘이고 결과는 그 `README.md`다. 이 명세에서 "쟀다"는 그 둘을 가리키고, 손으로 본 것과 코드를 읽은 것과 어림은 그렇게 적는다.

## Problem Statement

운영자 관점. 모델은 서버 프로세스 하나에 하나이고, 코드의 기본값과 `--model`·`AGENT_OS_MODEL`로만 정해진다. 관리 화면에는 `plugins/models/`에 둔 파일이 모델 행으로 뜨고 켜고 끌 수 있지만 "로더가 생기기 전에는 효과가 없다"는 안내 줄이 붙어 있고, 실제로 런타임이 그 파일을 읽지 않아 켜고 꺼도 아무것도 달라지지 않는다. 모델을 바꾸려면 서버를 다시 띄워야 하고, 에이전트마다 다른 모델을 쓸 수 없으며, `max_tokens` 같은 파라미터는 코드의 고정값이다. PRD의 운영자는 어떤 에이전트, 도구, 모델이 등록돼 돌아가는지 한 곳에서 보고 켜고 끄고 싶어 한다.

## Solution

모델이 다른 셋(에이전트, mcp, 스킬)과 같은 플러그인이 된다. 운영자는 `plugins/models/<이름>/plugin.toml`에 제공사와 모델 id와 파라미터를 적고, `--model`이나 `AGENT_OS_MODEL`로 그 가운데 하나를 기본 모델로 고른다. 에이전트 개발자는 매니페스트의 `model` 칸으로 다른 모델을 고른다. 런타임은 실행을 준비할 때마다 그 모델 파일을 읽어 모델 객체를 만들므로, 파일을 고치거나 관리 화면에서 켜고 끈 것이 서버를 다시 띄우지 않아도 다음 실행부터 듣는다. 기본 모델의 오타는 서버와 CLI가 시작할 때 드러나고, 꺼진 모델을 쓰는 실행은 꺼진 mcp처럼 409로 거부된다. 관리 화면의 모델 행에서 안내 줄이 사라진다. 에이전트 코드(`ctx.llm()`)와 트레이스는 바뀌지 않는다.

## User Stories

1. As an 운영자, I want 모델을 `plugins/models/<이름>/plugin.toml`에 두고 이름으로 고르기, so that 코드를 고치지 않고 모델을 등록한다.
2. As an 운영자, I want 모델 파일의 `max_tokens`·`temperature`를 바꾸면 다음 실행부터 듣기, so that 서버를 다시 띄우지 않고 파라미터를 조정한다.
3. As an 운영자, I want 관리 화면에서 모델을 끄면 그 모델을 쓰는 다음 실행이 409로 거부되기, so that 켜고 끄기가 실제 효과를 가진다.
4. As an 운영자, I want 운영자 채널의 409·500 메시지에 플러그인의 종류와 이름과 그것을 쓰는 에이전트가 적히기, so that 어느 파일을 고칠지 바로 안다.
5. As an 운영자, I want `serve`가 시작할 때 기본 모델의 문제(이름 없음, 패턴 위반, 파일 없음, 읽히지 않음)를 토큰·사이트 파일 문제와 한 목록으로 내기, so that 첫 요청이 실패할 때까지 오타를 모르지 않는다.
6. As an 운영자, I want CLI `run`·`resume`도 시작할 때 같은 확인을 하기, so that 서버와 CLI의 진단이 같다.
7. As an 운영자, I want `--model`이 `AGENT_OS_MODEL`을 이기기, so that 지금의 우선순위가 그대로다.
8. As an 운영자, I want 모델을 끈 것이 서버 시작을 막지 않기, so that 운영 중에 켜고 끄는 상태가 시작의 조건이 되지 않는다.
9. As an 운영자, I want 공통 넷만 적은 옛 모델 파일이 조용히 무시되지 않고 목록의 표지 행과 상세의 500으로 알리기, so that 등록했다고 믿는 것과 실제가 어긋나지 않는다.
10. As an 운영자, I want API 키를 모델 파일이 아니라 환경변수에 두기, so that 비밀이 플러그인 파일과 관리 API 응답에 실리지 않는다.
11. As an 운영자, I want 관리 화면의 모델 행에서 "로더가 생기기 전에는 효과가 없다"가 사라지기, so that 화면이 지금의 동작을 말한다.
12. As an 운영자, I want 관리 화면의 모델 상세에서 `provider`·`model_id`·파라미터를 그대로 보기, so that 어느 설정이 돌고 있는지 확인한다.
13. As an 에이전트 개발자, I want 매니페스트에 `model = "<플러그인 이름>"`을 적어 다른 모델을 쓰기, so that 에이전트마다 모델이 다르다.
14. As an 에이전트 개발자, I want `model`을 적지 않으면 기본 모델이 쓰이기, so that 지금 있는 에이전트가 그대로 돈다.
15. As an 에이전트 개발자, I want `ctx.llm()`이 그대로이기, so that 에이전트 코드를 고치지 않는다.
16. As an 에이전트 개발자, I want 매니페스트의 오타(이름 패턴 위반, 다른 종류의 칸, 범위 밖의 값)가 읽는 단계에서 소리 나게 거부되기, so that 실행 중에 엉뚱한 모델로 돌지 않는다.
17. As an 에이전트 개발자, I want 내 에이전트가 가리키는 모델이 없을 때 그 에이전트 이름과 모델 이름이 든 오류를 받기, so that 어느 매니페스트가 틀렸는지 안다.
18. As a 최종 사용자, I want 꺼진 모델 때문에 거부될 때 종류와 이름 없는 고정 문구의 409를 받기, so that 서버 안쪽의 구성이 밖으로 새지 않는다.
19. As a 최종 사용자, I want 없거나 깨진 모델 때문에 실패할 때 고정 문구의 500을 받기, so that 위젯이 저장한 대화를 지우지 않는다.
20. As a 최종 사용자, I want 이어 가기와 재개가 지금 디스크의 모델 파일대로 돌기, so that 운영자가 바꾼 모델이 내 다음 요청부터 듣는다.
21. As an 운영자, I want 트레이스의 `llm_called.model`이 응답이 돌려준 실제 모델 이름 그대로이기, so that 트레이스 형식과 관리 화면이 바뀌지 않는다.
22. As a 저장소 기여자, I want 격리된 플러그인 루트의 시험과 두 e2e 스택이 기본 모델 매니페스트를 두고 `--model`로 넘겨 지금처럼 초록이기, so that 셸 환경에 기대지 않는다.
23. As a 저장소 기여자, I want 실제 모델 호출 시험 하나가 저장소의 모델 플러그인으로 돌기, so that 어댑터가 `model_id`를 제공사에 실제로 보내는 것을 본다.
24. As a 저장소 기여자, I want 생성된 TS 타입이 새 칸을 필수로 받아 옛 리터럴이 타입 검사에서 깨지기, so that 계약 변경이 조용히 지나가지 않는다.
25. As a 저장소 기여자, I want 포트가 다섯 그대로이고 가짜 하나로 core를 시험하기, so that 시험이 빠르고 결정적이다.
26. As an 운영자, I want 둘째 제공사를 들일 때 `provider`의 값 하나를 더하는 가산 변경이면 되기, so that 지금의 모양이 그 길을 막지 않는다.

## Implementation Decisions

구현 파일의 경로와 코드 조각은 새로 짓지 않는다. 규칙 문서·ADR·테스트 선례의 경로와 ADR 0040이 이미 든 구현 경로는 옮겨 적는다.

### 모델 매니페스트의 칸 (넘겨받았다. 세부는 쟀다)

- 공통 넷(`schema_version = "1"`, `kind = "model"`, `name`, `version`)에 `provider`, `model_id`, 선택 `max_tokens`, 선택 `temperature`다. `provider`는 sdk의 닫힌 열거(`StrEnum`)이고 값은 `anthropic` 하나다. 열거의 이름은 `ModelProvider`이고 그 이름 그대로 `openapi.json`의 컴포넌트가 된다(`PluginKind`처럼 이름 있는 정의여야 생성 클라이언트가 재사용한다, ADR 0008). `model_id`는 비지 않은 문자열이다. `max_tokens`는 `conversation_limit`과 같은 엄격 검증(`strict=True`, 1 이상)이고 `temperature`는 엄격한 실수(0 이상 1 이하)다.
- 받고 거부하는 경계를 sdk `PluginManifest`와 같은 설정의 시제품으로 쟀다(`manifest_fields.py`, 사례 26. 실제 클래스에 칸을 더하는 것은 아래 계약 묶음이고, 시험이 같은 사례로 그 클래스를 잰다). TOML의 정수 `0`·`1`은 `temperature`에서 실수 `0.0`·`1.0`으로 받히고, `max_tokens`의 `0`·`2.0`·`true`·`"16"`, `temperature`의 `1.5`·`-0.1`·`"0.5"`·`true`, 모르는 `provider`, 빈 `model_id`, 모르는 칸, 종류에 맞지 않는 칸(모델이 아닌 종류의 네 칸, 에이전트가 아닌 종류의 `model`)은 읽는 단계에서 거부된다. 거부의 표지(pydantic 오류의 `type`과 검증자의 문구)는 그 프로브 README에 있고 시험은 같은 표지로 실패의 까닭을 단언한다(`CODING_STANDARDS.md`).
- 칸 이름 `model_id`와 `model`은 pydantic 2.13.5의 기본 보호 이름 공간 경고를 내지 않는다(쟀다, 같은 프로브의 양성 대조 포함). sdk가 `protected_namespaces`를 손대지 않는다.
- `schema_version`은 "1" 그대로다(ADR 0008의 2026-10-31 이력). 공통 넷만 적은 모델 파일은 필수 칸이 없어 거부되고 관리 API의 상세는 500이고 목록은 그 파일의 행만 표지 행이다(ADR 0040 "공통 넷만 적은 모델 파일은 거부된다").

### 에이전트 매니페스트의 `model` 칸 (넘겨받았다)

플러그인 이름 패턴의 선택 칸이고 없으면 기본 모델이다. 패턴은 sdk의 `PluginName` 그대로라 런타임이 다시 검증하지 않는다. 에이전트가 아닌 종류가 적으면 `requires_approval`처럼 거부한다. 가리키는 모델 플러그인이 실재하는지는 매니페스트만으로 알 수 없어 실행 준비가 본다(아래 "실행 준비의 순서").

### 포트의 모양 (명세가 정했다)

- `.claude/rules/core.md` 포트 표의 모델 행이 `ChatModel`(모델 하나)에서 `ModelSource`(모델 매니페스트를 받아 모델을 돌려주는 것)로 바뀐다. 메서드는 하나다. 모델 매니페스트(`PluginManifest`)를 받아 모델(`ChatModel`)을 돌려준다. 이름은 `ToolSource`·`PluginSource`와 같은 꼴이고, 첫 어댑터 칸은 langchain-anthropic의 `ChatAnthropic`을 만드는 것이다. (2026-10-31 명세 검토: 메서드는 동기다. 재개는 준비를 결정 이벤트 쓰기 앞에서 하므로 모델 만들기도 재개의 첫 걸음 안이고, 그 첫 걸음에 `await`가 없다는 불변식(`.claude/rules/core.md`의 재개 항목, HTTP 채널의 동시 재개 시험)이 이 메서드에 걸린다. 메서드의 이름과, `run()`·`resume()`·`create_app`이 모델 소스를 받는 인자의 이름은 티켓 04가 짓는다. 기본 모델의 인자 `default_model`은 아래 "기본 모델의 입구"가 정했다)
- `ChatModel`(`type ChatModel = BaseChatModel`)은 포트가 아니라 만든 모델의 타입으로 남는다. 루프와 대화 요약은 지금처럼 그 타입을 받는다. core가 닿는 바깥 지점은 그대로라 포트는 다섯이고(ADR 0012) 메서드가 는 포트는 없다.
- 가짜는 포트 Protocol을 상속하지 않고 시그니처로 만족하며 픽스처가 포트 타입으로 annotate한다(`.claude/rules/tests.md`). 가짜 모델 소스는 어느 매니페스트로 몇 번 만들었는지 기록하고 지금의 `GenericFakeChatModel`을 돌려준다.
- 거부한 안: 여섯째 포트로 `ModelSource`를 두고 `ChatModel` 포트도 남기는 것. 닿는 지점이 그대로인데 포트가 는다(ADR 0012). 거부한 안: sdk에 모델 설정의 값 타입을 따로 두고 포트가 그것을 받는 것. ADR 0040이 "모델 매니페스트를 받아"라고 정했고, 종류 판정이 sdk의 검증자와 변환 둘로 갈린다.

### 기본 모델의 입구 (명세가 정했다)

- 기본 모델의 이름은 `run()`·`resume()`의 키워드 전용 필수 인자 `default_model`(타입 `PluginName`)로 core에 든다. 앱 조립(`create_app`)과 CLI의 `run`·`resume` 명령 함수가 같은 인자를 받아 그대로 넘긴다. core는 에이전트 매니페스트의 `model`이 없을 때 그 이름을 쓴다.
- 거부한 안: 모델 소스(어댑터)가 기본 모델의 이름을 들고 core는 모르는 것. 에이전트가 `model`을 적지 않으면 기본 모델이라는 판정이 어댑터로 새고, 꺼짐 판정이 이름을 요구한다.

### 경계의 이름 검증 (명세가 정했다)

- `--model`과 `AGENT_OS_MODEL`의 값은 조립(`main.py`)이 `is_plugin_name`으로 거른 뒤 `PluginName`으로 감싼다(`sdk/ids.py`의 경계 규칙). 패턴을 어기면 빈 이름과 같은 자리의 구성 오류다. 문구는 값과 패턴을 든다.
- 거부한 안: 패턴 검증을 실행 준비에 맡기는 것. 오타가 첫 실행까지 숨고, 준비 단계의 `PluginError`가 구성 오류를 대신한다.

### 시작 때의 확인 (넘겨받았다. 내용은 명세가 정했다)

- `serve`의 구성 문제 목록에 기본 모델의 항목이 네 갈래로 든다. 이름이 없거나 비었다(비었다는 지금 그대로이고, 없다는 코드의 기본값이 사라져 새로 드는 갈래다), 플러그인 이름 패턴이 아니다, 그 이름의 모델 매니페스트가 없다, 있지만 읽히지 않는다(어댑터의 `PluginError` 문구 그대로). 그래서 구성 문제 목록을 내는 자리가 플러그인 소스를 받아 매니페스트를 한 번 읽는다. 읽은 매니페스트는 확인에만 쓰고 버린다. 실행은 실행마다 다시 읽는다(ADR 0040). 꺼짐은 보지 않는다. (2026-10-31 명세 검토: 지금 그 문구는 pydantic 오류의 입력값(`input_value`)을 들어, 모델 파일에 잘못 적은 키 값(`api_key = "sk-…"`)이 `extra_forbidden` 거부 문구에 실리므로, 이 절의 확인이 들어서면 그 값이 표준 에러에 나간다. 관리 목록의 표지 행 `reason`과 상세 500에는 지금도 나간다(서브에이전트가 임시 스크립트로 손으로 봤다). 티켓 02가 매니페스트 거부 문구에서 입력값을 빼 목록·상세·실행 500·`serve`·CLI 다섯 출구를 함께 닫고, 시작 때의 확인은 그 뒤 티켓 05가 들인다. 패턴 위반만 그 앞 티켓 04가 지금 빈 이름을 거부하는 자리에 든다)
- CLI `run`·`resume`은 지금 빈 이름을 거부하는 자리에서 같은 네 갈래를 확인하고, 어기면 표준 에러에 한 줄을 적고 `EXIT_FAILED`로 끝난다(설계 일지 2026-10-31-06의 3라운드 답). (2026-10-31 명세 검토: 읽히지 않음의 문구는 경로와 검증 오류로 여러 줄이라 "한 줄"이 아니라 그 문구를 적는다. 티켓 05) 실행 준비에서 같은 매니페스트를 다시 읽는 것은 서버와 같다.
- 거부한 안: CLI는 시작 확인 없이 준비 단계의 `PluginError`에만 맡기는 것. 설계의 답이 "같은 확인"이고, 서버와 CLI의 진단이 갈린다.

### 실행 준비의 순서 (명세가 정했다)

- 지금의 순서 부재 → 깨짐(mcp 없음 → 마스킹과 승인의 충돌 → 운영자 파일의 손상) → 꺼짐(에이전트 → 매니페스트에 적힌 순서의 mcp) → 진입점 import(`.claude/rules/core.md`)가 이렇게 된다. **부재 → 깨짐(mcp 없음 → 마스킹과 승인의 충돌 → 모델 없음·읽히지 않음 → 운영자 파일의 손상) → 꺼짐(에이전트 → mcp → 모델) → 진입점 import → 모델 만들기.** 깨짐과 꺼짐이 같은 순서(에이전트 → mcp → 모델) 하나다.
- 모델의 이름은 에이전트 매니페스트의 `model`, 없으면 `default_model`이다. 없음의 문구는 mcp와 같은 꼴이다. 에이전트가 적은 모델이면 `에이전트 X 이 지정한 model 플러그인이 없다: 이름`, 기본 모델이면 `기본 모델 플러그인이 없다: 이름`이다(둘 다 이 명세가 정한 새 문구다). 읽히지 않음은 어댑터의 `PluginError` 그대로다.
- 모델 매니페스트는 준비 한 번에 한 번 읽는다(mcp와 같다). 꺼진 집합도 지금처럼 한 번 읽어 셋을 본다.
- 재개는 기록된 에이전트의 매니페스트를 지금 디스크에서 읽어 같은 순서를 지난다. 이어 가기의 대화 요약은 그 실행의 모델이다(ADR 0022).
- 거부한 안: 모델의 없음·읽히지 않음을 mcp 앞에 두는 것. 꺼짐의 순서(에이전트 → mcp → 모델)와 어긋나 규칙이 둘이 된다. 거부한 안: 모델 만들기를 진입점 import 앞에 두는 것. 만들기는 키도 네트워크도 요구하지 않아 실패할 길이 없고(아래), 지금 마지막인 import의 시험 불변식(꺼진 에이전트를 import하지 않는다, `tests/core/test_run.py`)을 그대로 둔다.

### 모델 만들기는 실행마다이고 실패는 실행 전 실패다 (명세가 정했다. 비용은 쟀다)

- 준비의 마지막에 모델 소스가 모델 매니페스트로 모델을 만들고, 준비 결과가 그것을 들어 몸통에 넘긴다. 실행마다 새 객체다.
- 어댑터와 같은 인자로 `ChatAnthropic`을 만드는 데 중앙 0.1ms, 최대 0.3ms이고(두 실행), API 키가 없어도 아무도 듣지 않는 주소를 줘도 클라이언트를 만들지 않는다(`build_without_key.py`, 만들기 10회차). 네트워크는 호출에서 탄다(같은 프로브의 양성 대조, 죽은 주소로의 호출이 `APIConnectionError`). ADR 0040이 "어림이고 구현 티켓이 본다"고 한 것을 이 명세가 쟀고 그 ADR의 이력에 적었다.
- 그래서 만들기의 실패는 구성 오류(`PluginError`, 실행 전 실패)이고 `run_started` 전이다. 운영자 면 500, 최종 사용자 면 고정 문구 500이다.
- API 키가 없는 것은 만들 때가 아니라 첫 호출에서 드러난다. langchain-anthropic 1.7.2는 네트워크에 닿기 전에 `TypeError`("Anthropic authentication failed: no API key or authorization credentials were provided. Set the ANTHROPIC_API_KEY environment variable, …")를 낸다(쟀다, 같은 프로브). 그 실행은 지금처럼 `run_failed`이고 원인은 `model_call`이다(ADR 0031). 바뀌지 않는다.
- 거부한 안: 만든 모델을 매니페스트 내용으로 캐시하는 것. 1ms도 안 되는 만들기를 아끼려고 "실행마다 파일에서 읽는다"는 반영 시점의 규칙에 두 번째 상태가 생긴다.

### 어댑터의 모양 (명세가 정했다)

- `adapters/anthropic.py`에 모델 소스의 구현 하나가 선다. `provider`를 닫힌 열거로 가르며(`match`. 값이 늘면 pyright가 빠진 갈래를 본다), `anthropic`이면 `model_id`를 모델 이름으로, `max_tokens`가 없으면 지금의 고정값 16000을, `temperature`는 있을 때만 넘기고, `timeout`·`stop`은 지금처럼 비워 `ChatAnthropic`을 만든다. `provider`나 `model_id`가 없는 매니페스트(모델이 아닌 종류)는 `PluginError`다. 선례는 `entrypoint` 없는 매니페스트를 `load_agent`가 거부하는 문구(`adapters/filesystem.py`)다. (2026-10-31 명세 검토: 거르는 갈래는 `match` 앞의 하나다. `provider`나 `model_id`가 없으면 `PluginError`이고, 칸의 타입이 선택이라 pyright strict가 이 좁힘을 요구한다. `anthropic` 갈래 안에서 `model_id`를 다시 좁히면 sdk의 검증자가 둘이 함께 있음을 보장해 어떤 입력도 닿지 않는 갈래가 된다. core는 `read_manifest(MODEL, …)`가 종류를 거르고 칸을 꺼내 쓰지 않으므로 다시 거르지도 시험하지도 않는다. 시험은 `tests/adapters/test_anthropic.py`에서 에이전트 매니페스트로 한 번이다. 티켓 04)
- 코드의 기본 모델 이름(`DEFAULT_MODEL`)과 그 갈래가 없어진다. 이름을 푸는 규칙은 플래그 > 환경변수 둘뿐이고 둘 다 없으면 빈 값과 같은 `ValueError`다. 이름으로 모델 하나를 만들던 함수는 모델 소스의 안으로 들어간다.
- 거부한 안: `provider`가 없으면 `anthropic`으로 보는 것. 모델이 아닌 종류의 매니페스트가 조용히 모델이 된다(fail-open).

### 꺼진 모델 (넘겨받았다. 문구는 명세가 정했다)

- 꺼진 모델을 쓰는 실행은 `Disabled`다. 운영자 면의 문구는 mcp와 같은 꼴 `꺼진 플러그인이다: model 이름 (에이전트 X 이 쓴다)`이다(이 명세가 정한 새 문구다). 최종 사용자 면은 `failure_for`의 표가 지금처럼 종류와 이름 없는 고정 문구(`UNAVAILABLE_MESSAGE`)의 409로 덮는다(`.claude/rules/http.md`). 라우트도 표도 바뀌지 않고 시험이 고정한다.
- 기본 모델이 꺼진 것은 시작의 조건이 아니다. 그것을 쓰는 실행이 409다.
- (2026-10-31 to-tickets에서 사용자가 고른 것) 관리 화면의 결정 칸은 멈춘 실행의 에이전트 매니페스트가 `model`로 가리킨 모델이 꺼져 있으면 에이전트·mcp처럼 미리 알리고 결정 버튼을 막는다. 기본 모델은 관리 API가 그 이름을 내지 않아 화면이 모르므로 누른 뒤의 409 봉투가 말한다. ADR 0019의 미리 알림 문장("꺼진 에이전트나 그 mcp")에 이력 한 줄이 들고, 티켓 06이 그 초안을 쓰고 승인을 받는다. 명세 검토가 찾은 빈칸이다.

### 저장소의 기본 모델 플러그인과 격리 루트 (명세가 정했다)

- 저장소의 `plugins/models/claude-opus-5/plugin.toml`은 `provider = "anthropic"`, `model_id = "claude-opus-5"`, `max_tokens = 16000`이고 `temperature`는 적지 않는다(지금의 동작 그대로). `version`은 `0.1.0`이다.
- 격리된 플러그인 루트(실제 `serve`를 띄우는 시험, CI, 관리 화면 e2e 스택 `web/apps/admin/e2e/stack.ts`, 위젯 e2e 스택 `web/apps/widget/e2e/stack.ts`)의 기본 모델도 같은 이름 `claude-opus-5`이고 내용은 받아들여지는 모델 매니페스트면 된다. 시험과 스택은 `--model claude-opus-5`를 명시해 넘기고 셸의 `AGENT_OS_MODEL`에 기대지 않는다. 저장소 루트에서 실제 CLI를 돌리는 `-m llm` 시험도 `--model claude-opus-5`를 명시한다. 위젯 스택의 실제 모델 모드는 저장소의 플러그인을 복사하므로 그 파일이 함께 오고(`copyRepoPlugins`), 복사 뒤에는 두 모드 모두 같은 루트에 픽스처를 쓴다(`writeFixturePlugins`. 둘 다 코드를 읽었다). 그래서 위젯 스택의 픽스처 `claude-opus-5`는 저장소 파일과 같은 `model_id`를 적는다. 다른 id를 적으면 실제 모델 모드에서 복사해 온 저장소 파일이 그 픽스처로 덮여 `-m llm_widget`이 가짜 id를 제공사에 보낸다(코드를 읽은 시나리오이고 돌리지 않았다).
- 둘째 모델 픽스처 `sonnet`(`tests/test_server.py`의 `SONNET`, 관리 스택의 `models/sonnet`)은 지우지 않고 `provider`·`model_id`를 갖춘 모델 매니페스트로 고친다. 목록에 모델이 둘 있어야 켜고 끄기와 "에이전트가 고른 모델" 시나리오를 잰다. 관리 화면 e2e(`web/apps/admin/e2e/admin-token.e2e.ts`)가 모델 행에 "로더가 생기기 전에는 효과가 없다"가 있다고 단언하는 줄은 그 줄이 없다는 단언으로 바뀐다.
- 운영자 문서의 값. `.env.example`에 `AGENT_OS_MODEL=claude-opus-5` 줄이 들고, `README.md`의 `serve` 줄은 `--model claude-opus-5`를 적거나 그 환경변수를 안내하며, `disabled.toml` 줄의 "skill과 model은 로더가 생길 때" 문장에서 model이 빠진다. (2026-10-31 명세 검토: `serve` 줄은 `--model claude-opus-5`를 적는다. 티켓 03이다. `disabled.toml` 줄은 켜고 끄기가 실제로 듣게 된 뒤라 티켓 06이다)
- 거부한 안: 격리 루트의 기본 모델을 `fake-model` 같은 다른 이름으로 두는 것. README·`.env.example`·스택·시험의 `--model` 값이 둘이 된다. 거부한 안: 스택이 `AGENT_OS_MODEL` 환경변수로 넘기는 것. 개발자 셸의 같은 변수에 가려지고, `--model`이 그것을 이긴다. 거부한 안: `sonnet` 픽스처를 지우고 기본 모델 하나만 두는 것. 둘째 모델이 없으면 켜고 끄기와 에이전트별 선택을 잴 수 없다.

### 계약 (넘겨받았다. 세부는 쟀다)

- `openapi.json`의 `PluginManifest`에 다섯 칸(`model`, `provider`, `model_id`, `max_tokens`, `temperature`)이 들고 `ModelProvider`가 컴포넌트로 선다. 직렬화 스키마에서 다섯 칸은 모두 `required`이고 `null`을 허락한다(`manifest_fields.py`로 쟀다. `json_schema_serialization_defaults_required` 때문이고 `conversation_limit`과 같다). 그래서 생성된 TS 타입은 다섯 칸을 `… | null`의 필수로 받고, 관리 화면의 스토리·테스트의 매니페스트 리터럴은 지금 `conversation_limit: null`을 적듯 다섯 칸의 `null`을 적는다. 생성기를 돌리지 않았으니 리터럴이 깨지는 것은 어림이고 계약 티켓의 타입 검사가 빨강으로 보인다. 두 e2e 스택은 매니페스트를 TOML 문자열로 쓰므로 생성 타입이 닿지 않고(코드를 읽었다), 그 모델 픽스처는 위 "저장소의 기본 모델 플러그인과 격리 루트"대로 고친다. (2026-10-31 명세 검토: 리터럴이 깨지는 것은 같은 장치의 결과인 `conversation_limit: number | null`이 생성 타입에 이미 있어 코드를 읽어 닫힌다. 모델 리터럴은 `provider: "anthropic"`과 `model_id`를 적어 서버가 낼 수 있는 모양으로 둔다. 매니페스트 JSON을 그대로 그리는 모델 상세(`PluginDetail`)의 사진 정답 여덟 장이 리터럴과 함께 바뀌므로 티켓 01이 `pnpm -C web visual:admin:update`로 다시 만들고 바뀐 사진을 PR 본문에 적는다. 사진이 바뀐다는 것은 코드를 읽은 어림이고 돌리지 않았다. 공통 넷만 적은 `sonnet` 픽스처 둘(`tests/test_server.py`의 `SONNET`은 모듈을 import할 때 읽힌다, 관리 스택의 `models/sonnet`)은 sdk가 바뀌는 순간 깨지므로 가장자리가 아니라 티켓 01이다)
- 관리 API의 경로는 늘지 않는다. 관리 화면은 `PluginList.tsx`의 로더 없는 종류 집합에서 model을 빼 안내 줄을 걷고, 상세는 매니페스트 JSON 그대로다. 화면 디자인 단계는 없다. (2026-10-31 명세 검토와 to-tickets: 안내 줄을 걷는 것은 계약이 아니라 켜고 끄기가 실제로 듣게 된 뒤라 티켓 06이다. 같은 줄을 단언하는 vitest(`components/pages/HomePage.test.tsx`)와 관리 화면 e2e의 단언이 함께 간다. 계약에 두면 그 사이 main에서 화면이 효과가 있다고 말하는데 실제로는 없다. 06을 따로 두면 04와 06 사이에 화면이 효과가 없다고 낮춰 말하는 틈이 있고 사용자가 받아들였다)
- 계약 티켓이 먼저다(`CLAUDE.md` 작업 규약 2). sdk의 칸과 열거, `openapi.json` 내보내기, 생성 타입, 리터럴의 `null`, 그리고 포트의 모양(`ModelSource`와 `run()`·`resume()`·`create_app`의 새 인자 `default_model`)까지가 계약이다. 시그니처가 바뀌는 자리를 한 티켓이 모두 옮겨야 나머지 티켓이 나란히 돈다. (2026-10-31 명세 검토: 포트의 모양과 `default_model`은 계약에서 뺀다. 포트가 바뀌는 순간 core는 모델 매니페스트를 읽어야 모델을 얻으므로 준비 단계, 어댑터의 모델 소스, 격리 루트의 매니페스트가 모두 끌려와 계약 티켓이 혼자 초록일 수 없다. 또 `default_model`(`PluginName`)을 만드는 쪽과 `is_plugin_name`으로 거르는 쪽이 갈려 계약 티켓만 병합된 main에서 검증 없는 이름이 감싸진다. 둘 다 `openapi.json`에 실리지 않고 `CLAUDE.md` 작업 규약 2가 드는 계약(`sdk/`, `openapi.json`, 헌법)도 아니다. 계약 티켓 01은 sdk의 칸·열거·종류별 거부, `openapi.json`, 생성 타입, 리터럴, 사진 정답, `sonnet` 픽스처 둘, `.claude/rules/sdk.md`이고, 포트와 `default_model`과 이름 검증과 어댑터의 모델 소스는 한 티켓 04다)
- 거부한 안: 새 칸을 직렬화 스키마에서 선택으로 두어 리터럴을 그대로 두는 것. 늘 실리는 칸을 required로 내보내는 결정(ADR 0010의 2026-09-23 이력, `.claude/rules/sdk.md`)을 뒤집는다.

### 트레이스 (넘겨받았다)

이벤트 형식 3 그대로다. `llm_called.model`과 `conversation_summarized.model`은 응답이 돌려준 실제 모델 이름이다. 시작 이벤트에 모델 플러그인의 이름을 남기지 않는다(ADR 0040이 거부했다). 같은 id에 파라미터만 다른 두 플러그인은 트레이스로 가르지 못한다.

### 고칠 자리 (명세가 정했다. 목록은 ADR 0040의 "구현 티켓이 고칠 곳" 불릿)

티켓으로 나누는 것은 to-tickets의 몫이고, 여기서는 자리를 셋으로 묶는다.

- **계약 묶음.** sdk의 칸·열거·종류별 거부, `openapi.json`, 생성 타입, 관리 화면의 스토리·테스트의 리터럴, `PluginList.tsx`의 집합, 포트의 모양과 새 인자 `default_model`(조립과 CLI 명령 함수의 시그니처까지), `.claude/rules/sdk.md`의 두 문장, `.claude/rules/core.md`의 포트 표.
- **런타임 묶음.** 실행 준비의 순서와 문구, 모델 만들기, 어댑터의 모델 소스와 기본값 갈래 제거, 시작 때의 확인(서버와 CLI), 경계의 이름 검증, `.claude/rules/core.md`의 준비 순서 문장과 `Disabled` 문장, `.claude/rules/adapters.md`의 "`main.py`가 만든다".
- **가장자리 묶음.** 저장소의 `plugins/models/claude-opus-5`, 격리 루트의 기본 모델과 `--model`(실제 `serve`를 띄우는 시험, 두 e2e 스택), `sonnet` 픽스처 둘, 관리 화면 e2e의 안내 줄 단언, `README.md`의 두 줄, `.env.example`, `-m llm` 시험이 든 파일 둘(`tests/core/test_model.py`, `tests/test_main.py`)이 기본값 대신 저장소의 모델 플러그인을 쓰게 하는 것, 어댑터 시험(`tests/adapters/test_anthropic.py`)의 기본값 사례.

(2026-10-31 명세 검토와 to-tickets: 이 세 묶음은 경계마다 빨강이 나서 티켓 여섯으로 다시 나눴다. 01 계약(sdk·`openapi.json`·생성 타입·리터럴·사진 정답·`sonnet` 픽스처 둘·`sdk.md`), 02 매니페스트 거부 문구에서 입력값을 뺀다, 03 저장소의 `claude-opus-5`와 격리 루트의 기본 모델 매니페스트·`--model`·`.env.example`·README `serve` 줄(01에 막힌다. 지금 코드에서 그 이름이 기본값과 같아 동작이 바뀌지 않는 준비다), 04 런타임(포트·`default_model`·이름 검증·준비 순서와 문구·모델 만들기·어댑터의 모델 소스·rules 문장·실제 모델 시험. 01·02·03에 막히고 코드의 기본값은 남긴다), 05 코드의 기본값을 걷고 시작 때 확인(04에 막힌다), 06 관리 화면의 안내 줄과 결정 칸의 미리 알림·README `disabled.toml` 줄(04에 막힌다)이다. 검토가 이 목록에 없던 자리를 더했다. 시그니처가 바뀌는 호출 자리(`tools/export_openapi.py`, `tests/test_calc_plugin.py`, `tests/channel/http/test_router.py`·`test_end_user.py`), 바뀌는 규칙 문장(`.claude/rules/core.md` 대화 요약 항목의 "그 실행의 모델 포트 그대로", `.claude/rules/http.md` 최종 사용자 500 목록의 "요청한 에이전트와 그것이 쓰는 mcp와 진입점"), `main.py`와 `channel/cli/main.py`의 "시작 때 한 번 푼다"는 독스트링, 원문에 `model=model,`과 준비 호출을 든 변이 표 둘(`.scratch/end-user-channel/probes/timeout_mutations.toml`, `.scratch/conversation/probes/continuation_mutations.toml`)이다. 사용자가 to-tickets에서 고른 것으로 결정 칸의 꺼짐 미리 알림(`web/apps/admin/components/organisms/RunDecision.tsx`)과 ADR 0019 이력 한 줄이 더해졌다. 티켓의 셀프 리뷰(일지 2026-10-31-08)가 티켓이 짚은 구현 자리 넷을 더했다. 매니페스트를 읽지 못한 문구를 짓는 `adapters/filesystem.py`의 `_parse`, 빈 모델 지정을 진단하는 `main.py`의 `_model_problem`, `--model` 도움말을 다는 `channel/cli/main.py`의 `_add_model`, 위젯 e2e의 픽스처를 쓰는 `web/apps/widget/e2e/plugins.ts`다. 어느 티켓이 받는지는 티켓 파일이 든다)

## Testing Decisions

### 이음매 (사용자가 골랐다)

주 이음매는 core의 `run()`·`resume()`에 가짜 플러그인 소스와 가짜 모델 소스를 꽂는 자리다(`tests/core/test_run.py`의 `_run`과 `FakePlugins`). 가짜 플러그인 소스가 모델 매니페스트를 이름별로 들고, 가짜 모델 소스가 어느 매니페스트로 몇 번 만들었는지 기록한다. 준비의 순서, 매니페스트를 읽은 횟수, 에이전트가 고른 모델이 쓰이는지, 꺼진 모델의 `Disabled`, 없는 모델의 `PluginError`, 재개가 지금 디스크의 매니페스트를 쓰는 것을 여기서 잰다. 바깥 경계는 기존 시험 자리에 얇은 시험 하나씩이 맡고, 더하는 실제 모델 호출은 `-m llm` 하나다(아래 "실제 모델 호출 하나"). 고르지 않은 둘(HTTP 앱에 요청 넣기, 실제 서버 프로세스 띄우기)은 일지 2026-10-31-07에 있다. (2026-10-31 명세 검토: 이어 가기의 대화 요약이 그 에이전트의 모델로 도는 것(스토리 20)도 여기서 잰다. 가짜 모델 소스가 매니페스트마다 다른 가짜 모델을 돌려주고, 요약 이벤트의 `model`이 에이전트가 고른 모델 쪽인지 본다. 티켓 04)

### 좋은 시험

- 바깥 행동만 단언한다. 이벤트의 열, 예외의 타입과 문구, 상태 코드와 봉투, 가짜가 기록한 호출과 그 인자. 어느 함수가 어느 순서로 불렸는지는 단언하지 않는다. 준비의 순서는 두 결함을 함께 심어 어느 오류가 먼저 나오는지로 잰다(선례는 `tests/core/test_run.py`의 준비 순서 시험들).
- 실패를 기대하는 시험은 실패의 까닭(표지)을 단언한다(`CODING_STANDARDS.md`). 매니페스트 거부는 프로브 README의 표지를 그대로 쓴다.
- 환경이 없으면 skip이 아니라 실패다(`.claude/rules/tests.md`). `-m llm`은 `ANTHROPIC_API_KEY`가 없으면 실패한다(지금과 같다).
- 빨강을 먼저 본다(헌법 원칙 II). 계약 묶음의 첫 빨강은 리터럴이 타입 검사에서 깨지는 것과 `openapi.json` 최신성 시험이고, 런타임 묶음의 첫 빨강은 가짜 모델 소스가 한 번도 불리지 않는 것이다.

### 시험할 모듈과 선례

- sdk 매니페스트: 칸 넷과 `model`의 받기·거부, 종류별 거부, 직렬화 스키마의 `required`. 선례 `tests/sdk/test_manifest.py`(종류별 칸 거부, `conversation_limit`의 엄격 검증).
- core 준비: 위 이음매. 선례 `tests/core/test_run.py`.
- 어댑터: `provider = "anthropic"`의 매니페스트로 만든 인스턴스에 `model_id`·`max_tokens`·`temperature`가 닿는지, 없는 `max_tokens`가 16000인지, 모델이 아닌 종류가 `PluginError`인지. 선례 `tests/adapters/test_anthropic.py`의 `test_정한_이름이_그대로_모델_인스턴스에_닿는다`.
- 조립과 CLI: `serve`의 구성 문제 목록 네 갈래, `--model`이 환경변수를 이기는 것, CLI `run`·`resume`의 시작 확인과 종료 코드, 패턴 위반. 선례 `tests/test_main.py`의 `serve --model`과 구성 문제 시험, `workspace` 픽스처(기본 모델 매니페스트를 함께 쓰고 `--model`을 넘긴다). (2026-10-31 명세 검토: 꺼진 기본 모델이 `serve`의 시작을 막지 않는 것(스토리 8)을 더한다. `workspace`의 `disabled.toml`에 그 모델을 적고 uvicorn을 가로챈 기록으로 서는 것을 본다. 티켓 05)
- HTTP 두 면: 운영자 채널에서 없는 모델 500(원문)과 꺼진 모델 409(종류·이름·에이전트), 최종 사용자 면에서 고정 문구 500과 409, `GET /plugins`가 모델 행을 새 칸과 함께 내는 것, 공통 넷만 적은 모델 파일의 상세 500과 목록의 표지 행. 선례 `tests/test_server.py`(`_admin_app`, `SONNET`, 두 면의 상태 코드 시험).
- 관리 화면: `PluginList`의 모델 행에 안내 줄이 없는 것(vitest·스토리), 리터럴의 새 칸. 선례 `web/apps/admin/components/organisms/PluginList.stories.tsx`와 `components/pages/PluginPage.test.tsx`. (2026-10-31 명세 검토: 안내 줄을 단언하는 vitest는 `components/pages/HomePage.test.tsx`다)
- 두 e2e 스택: 기본 모델 매니페스트와 `--model`로 지금처럼 초록, 관리 화면 e2e의 모델 행 단언. 선례 `web/apps/admin/e2e/stack.ts`, `web/apps/widget/e2e/stack.ts`.
- 저장소 상태: `plugins/models/claude-opus-5/plugin.toml`이 읽히는 것(플러그인 경계 시험 `tests/test_plugins_boundary.py`가 플러그인 파일을 읽는 자리와 같은 꼴). (2026-10-31 명세 검토: 그 경계 시험은 `*.py`만 읽는다. 저장소의 플러그인을 실제 어댑터로 읽는 선례는 `tests/test_calc_plugin.py`다)

### 실제 모델 호출 하나 (명세가 정했다)

더하는 하나는 새 시험이 아니라 `tests/test_main.py`의 calc 시험(실제 CLI로 calc가 답하고 트레이스에 모델 호출이 남는 것을 보는 `-m llm` 시험)에 드는 단언이다. 저장소 루트에서 실제 CLI를 `--model claude-opus-5`로 돌리고, 트레이스의 `llm_called.model`이 저장소 매니페스트의 `model_id`와 같은지 본다. 어댑터가 `model_id`를 제공사에 실제로 보냈다는 바깥 증거다. 나머지 `-m llm` 시험(`tests/test_main.py`의 다른 다섯, `tests/core/test_model.py`의 하나)은 수가 늘지 않고, 기본값 대신 저장소의 모델 플러그인을 쓰도록 `--model claude-opus-5`를 넘기거나 저장소 매니페스트로 모델 소스가 만든 모델을 쓰게 고칠 뿐이다. 위젯의 실제 모델 e2e(`-m llm_widget`)는 스택이 저장소 플러그인을 복사하므로, 픽스처 모델이 그 파일을 다른 `model_id`로 덮지 않는 한(위 "저장소의 기본 모델 플러그인과 격리 루트") 그대로다. (2026-10-31 명세 검토: 이 단언은 어떤 구현에서도 초록이다. 플러그인 이름과 `model_id`와 옛 기본값이 모두 `claude-opus-5`라, 어댑터가 `model_id` 대신 플러그인 이름을 보내도 런타임 이전 코드에서도 같은 값이 돌아온다. 그래서 calc 시험은 저장소의 플러그인을 복사한 `--plugins-root`에서 모델 플러그인의 이름을 `model_id`와 다르게 두고 `--model <그 이름>`으로 돌려, `llm_called.model`이 `model_id`인지 본다. 어댑터의 단위 시험도 이름과 `model_id`가 다른 매니페스트로 인스턴스의 모델 이름을 본다. 응답이 요청한 모델 이름을 그대로 돌려준다는 전제는 `tests/core/test_model.py`의 지금 단언에서 읽었고 API를 불러 보지 않았다. 티켓 04)

## Out of Scope

- 토큰 단위 스트리밍(ADR 0014 그대로), 요청마다 모델 고르기(ADR 0014·0040이 거부), 둘째 제공사(`provider` 목록에 값을 더하는 가산 변경), `max_tokens`·`temperature` 밖의 파라미터와 `thinking`·`model_kwargs`, 대화 한도의 모델별 기본값(ADR 0022가 다시 보기로 한 것. 다시 봤고 넣지 않는다), 스킬 로더(ADR 0040).
- 관리 화면의 모델 전용 화면이나 편집. 목록·상세·켜고 끄기 그대로다.
- 시작 이벤트에 모델 플러그인의 이름을 남기는 것(ADR 0040이 거부).
- 다른 기능에 넘기는 것은 없다. 위는 모두 이 기능 뒤의 가산 변경이고 받는 기능이 아직 없다. `.scratch/plan.md`에 더한 행이 없다.

## Further Notes

- ADR 0008의 2026-10-31 이력에 `schema_version` "1" 유지의 예외 문장(실행 경로가 읽은 적 없고 실물 파일도 없던 종류의 첫 필수 칸은 버전을 올리지 않는다)이 승인 뒤에 더해졌다(설계 PR #442의 봇 둘째 회차). 결정은 그대로이고 근거 정리라 이 명세는 그 문장을 따르고, 이 명세 세션이 사용자에게 짚었다(일지 2026-10-31-07).
- 이 명세 세션이 지시문대로 ADR 0040의 Consequences 첫 불릿을 둘로 나누고 흩어진 "구현 티켓이 고친다"를 한 불릿으로 모았으며, ADR 0040과 ADR 0008 이력의 "실행 길"을 "실행 경로"로 바꿨다. 결정은 바뀌지 않았다.
- 프로브 둘은 `.scratch/model-plugin/probes/`다. 결과를 본 뒤 바꾼 표지 하나(`build_without_key.py`의 키 없음 표지)는 그 README에 까닭과 함께 있다.
- to-tickets에 주는 것. 계약 묶음이 다른 둘을 막는다. 런타임 묶음과 가장자리 묶음은 계약 묶음 뒤에 나란히 돌 수 있되, 가장자리 묶음의 `-m llm`과 실제 `serve`를 띄우는 시험은 런타임 묶음이 들어와야 초록이다. (2026-10-31 명세 검토: 방향이 반대다. 런타임이 코드의 기본값을 걷으면 기본 모델 매니페스트가 없는 격리 루트의 시험과 두 e2e 스택이 빨갛고, `DEFAULT_MODEL`·`anthropic_chat_model`을 import하거나 가로채는 시험 파일 셋이 수집이나 실행에서 깨진다. 가장자리 준비(매니페스트를 두고 `--model claude-opus-5`를 명시)는 지금 코드에서도 초록이다. 그래서 가장자리 준비(티켓 03)가 런타임(04)을 막고, 기본값을 걷는 것은 05로 뒤에 둔다. 기본값에 기대는 시험의 수정은 그것을 걷는 티켓이 함께 한다)
