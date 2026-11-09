# 2026-11-09 (21:38) mcp-http 티켓

세션 제목 `docs/mcp-http-tickets`. 브랜치 `docs/mcp-http-tickets`, 워크트리 `.claude/worktrees/mcp-http-tickets`(기준 `5af643d7`). 모델 Opus 5.5 / xhigh(지시문).

## 사용자 프롬프트

> .claude/skills/to-tickets/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/mcp-http/spec.md
>
> 다음 작업: 기능 mcp-http. 원격 MCP 서버에 주소로 접속해, 실행마다 MCP 서버를 새로 띄우는 시작 비용을 없앤다
> 다음 단계: 티켓
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /to-tickets .scratch/mcp-http/spec.md
> 브랜치: docs/mcp-http-tickets
> 모델: Opus 5.5 / xhigh
> 읽을 것: docs/journal/2026-11-09-1611-mcp-http-spec.md("다섯째 세션(커밋 뒤 인계를 받은 쪽)"의 봇 회차 2·3, 승인, 다음, 다음(추가)과 그 앞 "넷째 세션"의 다음). 명세 .scratch/mcp-http/spec.md, 기능 계획 .scratch/mcp-http/plan.md. 티켓 서식은 docs/agents/issue-tracker.md
> 이어받을 상태: 명세 PR(#501)이 병합됐다(5af643d7). 명세 검토(spec-reviewer 서브에이전트)는 아직 안 했으니 /to-tickets 전에 먼저 돌린다. 티켓을 쪼개기 전에 사용자에게 물을 것이 셋 있다. 하나, 어댑터의 클라이언트가 리디렉션을 따를지(정하지 않았다. 일지 "다음"과 명세 Further Notes). 둘, 서버가 유효한 Authorization 값을 JSON-RPC 오류 글에 담아 돌려줄 때 실패 문구에서 가릴지(CodeRabbit 둘째 회차 Major를 새 설계 결정이라 보류했다. 일지 "다음(추가)"). 셋, ADR 0049 결정 "닫기" 첫 문장이 이력 2026-11-09와 글자로 어긋난 것에 포인터를 달지(claude-review 셋째 회차 Minor. ADR 본문이라 사용자 승인이 필요하고 구현 티켓 본문에 이력의 해당 문장을 적는 것으로 갈음해도 된다). 셋 다 병합을 막지 않았고, 둘째를 가리기로 하면 명세 서두의 "스스로 정한 것 열넷"에 하나가 더해지므로(to-spec 3단계) 명세 본문을 고치는 별도 PR이 먼저다. 대기열 0518의 "세 번"은 넷이 맞다는 것은 다음 회고가 바로잡는다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main(baf39230. origin/main은 5af643d7). 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: 티켓까지

## 체크아웃 정리

지시문대로 제목을 `docs/mcp-http-tickets`로 바꾼 뒤 워크트리에 들어가기 전에 `tidy-checkouts`를 돌았다. 루트는 main이고 깨끗했으며 `git merge --ff-only --no-overwrite-ignore origin/main`이 `baf39230`에서 `5af643d7`로 당겼다(스킬 파일은 바뀌지 않았다). `judge`는 `worktree-pilot-portal-screens` 브랜치 하나를 지울 것으로 냈고 `remove-branch`가 지웠다. 남긴 것: `03-default-model-plugin-and-explicit-flag`·`06-round-drive-record`·`approval-rules-spec`·`approval-rules-tickets`는 바뀐 파일이 있고, `admin-style-spec`·`admin-style-to-spec`·`mcp-shutdown-spec`·`pilot-portal-screens`·`web-widget-spec`은 병합된 PR이 없고, `confident-wright-2d3ebf`·`elegant-dijkstra-aaddb9`는 앱 표지가 있고, `mcp-http-spec`은 그 브랜치가 제목인 세션이 돌고, `pilot-portal-design`은 쉬는 세션 다섯의 `claude.exe`와 세션을 모르는 `pwsh.exe` 다섯이 작업 디렉터리로 쥐었다. 모두 `judge`의 출력이다. 그 뒤 `EnterWorktree(name: mcp-http-tickets)`로 들어가 `git switch -c docs/mcp-http-tickets`로 브랜치를 바꿨다(기준 `5af643d7`).

## 명세 검토

`spec-reviewer` 서브에이전트가 체크리스트 일곱과 질문 둘에 더해 본 세션이 넘긴 세 자리(리디렉션, 서버 오류 글의 헤더 값, ADR 0049 "닫기" 첫 문장)와 묶음 A만 병합된 main을 봤다. 끝줄은 `blocker 2, should-fix 7, nit 6`이다. 검토는 임시 스크립트 둘(`C:\Users\User\AppData\Local\Temp\claude\C--project-agent\70761106-3400-4203-b392-5d808bdba430\scratchpad\mcp_http_review\redirect_echo.py`는 httpx2 MockTransport로 되울림·같은 출처와 다른 출처의 307·어댑터식 DELETE를, `C:\Users\User\AppData\Local\Temp\claude\C--project-agent\70761106-3400-4203-b392-5d808bdba430\scratchpad\mcp_http_review\delete_disconnect.py`는 DELETE 연결이 끊기는 서버를 본다. 둘 다 Windows에서 한 번)과 잠금 파일 사본(`…\scratchpad\mcp_http_review\lock\`)을 저장소 밖에서 돌렸다. 그 결과는 임시 스크립트로 손으로 본 것이고 커밋한 프로브가 아니다.

본 세션은 핵심 주장을 코드로 다시 대 봤다.

- mcp 2.3.0 `mcp/shared/_httpx_utils.py`의 `create_mcp_http_client` 독스트링은 "Redirect following is left at the httpx2 default (off)"이고, 같은 파일의 `request_within_origin`은 요청마다 `follow_redirects=False`로 보내며 같은 출처의 리디렉션만 스스로 따르고 클라이언트 설정은 보지 않는다(읽었다). 명세 Further Notes의 "mcp가 자기 클라이언트를 만들 때는 따르게 한다"(어림)는 틀렸고, ADR 0049 Consequences "리다이렉트"는 맞다.
- httpx2 2.13.0 `_client.py`의 `_redirect_headers`는 출처가 다를 때 `Authorization`만 떼고(같은 호스트의 http→https는 떼지 않는다) 나머지 헤더는 옮긴다(읽었다).
- mcp 2.3.0 `client/streamable_http.py` 398~416줄은 400 이상 응답의 본문이 JSON-RPC 오류면 그 오류를 그대로 올린다(읽었다). 서버가 그 글에 헤더 값을 담으면 `_connecting`의 문구에 들어간다.
- `McpServer(` 생성 자리는 `tests`·`src`에 열 곳이다(`grep -rn "McpServer(" tests src`에서 정의 줄을 뺀 수). `sdk/manifest.py` 149줄의 문구가 `(command, args)`를 든다.
- ADR 0049 20줄 첫 문장은 "세션 종료 요청(DELETE)과 클라이언트 닫기를 `CancelScope(shield=True)`와 기한 2초로 감싸"이고 같은 문단에 "2초를 넘기면 그만둔다"가 있으며 포인터 셋은 다른 문장 뒤에 있다. 12줄 요약도 "종료 요청과 클라이언트 닫기를 취소에서 보호하되 2초 안에 끝내고"다(읽었다).
- pydantic 2.13.5에서 키와 값에 패턴을 건 `dict`의 직렬화 스키마는 `patternProperties`(키 패턴 → 값 패턴)다(`uv run python -c`로 모델 하나를 만들어 손으로 봤다).

## 결정 (사용자가 골랐다)

선택 화면 한 번에 넷을 물었다. 첫 호출은 PreToolUse 훅이 사실 대조를 요구해 막았고, ADR 0049 20줄과 12줄, httpx2 `_redirect_headers`를 읽어 대 본 뒤 "15줄 남짓"을 검토의 어림이라고, 되울림과 라이브러리 안내가 같은 예외 종류로 온다는 것을 검토가 임시 스크립트로 본 것이라고 고쳐 다시 불렀다. 질문 문장과 라벨은 그대로다.

> 질문: 원격 MCP 서버가 오류를 돌려주면서 우리가 보낸 토큰(Authorization 값)을 오류 글에 그대로 담으면, 그 글이 실행 실패 문구와 트레이스 파일에 남습니다. 어떻게 막을까요?
>
> 사용자: 보낸 토큰을 찾아 가린다 (Recommended) — 접속 직전에 환경에서 읽은 헤더 값을 실패 문구에서 찾아 가린 표시로 바꿉니다. 값이 `Bearer xxx` 꼴이면 뒤의 토큰 부분도 따로 찾습니다. 도구 호출이 실패할 때의 문구에도 똑같이 적용합니다. 서버가 값을 바꿔서(인코딩하거나 일부만) 돌려보내면 놓칩니다. 아주 짧은 값은 상관없는 글자까지 가릴 수 있어서 최소 길이를 명세에서 정합니다. 그 밖의 진단 글은 그대로 남습니다. ADR 0049에 이력을 하나 더하고, 그 초안은 셀프 리뷰를 반영한 뒤 따로 보여 드리고 승인을 받습니다.

> 질문: 어댑터가 직접 보내는 세션 종료 요청(DELETE)에 서버가 '다른 주소로 가라'(리디렉션)고 답하면 어떻게 할까요?
>
> 사용자: 같은 서버 안에서만 따라간다 (Recommended) — 라이브러리가 자기 요청에 쓰는 규칙과 같습니다(mcp 2.3.0 코드를 읽었습니다). scheme·호스트·포트가 같고 메서드가 바뀌지 않는 리디렉션만 따라가고, 다른 서버로는 가지 않습니다. 짧은 코드(검토의 어림으로 15줄 남짓)와, 시험용 서버에 리디렉션하는 모드 하나가 더 듭니다.

> 질문: ADR 0049 '닫기' 결정의 첫 문장은 '종료 요청과 클라이언트 닫기를 함께 2초 기한으로 감싼다'고 적혀 있습니다. 그런데 이미 승인하신 이력(2026-11-09)은 '2초는 종료 요청에만 걸고, 닫기는 기한이 지나도 반드시 한다'로 바꿨습니다. 그 문장과 머리 요약 문장에 '바뀜: 이력 …' 표시를 달까요?
>
> 사용자: 이 PR에서 표시를 단다 (Recommended) — ADR 규칙(.claude/rules/adr.md)은 이력이 본문 문장의 범위를 바꿨으면 그 문장 뒤에 표시를 달라고 하고, 티켓 글로 대신하는 길은 두지 않습니다. 결정 내용은 바뀌지 않고, 20줄 첫 문장과 12줄 요약 뒤에 이력 '닫기 보호는 … 직접 보낸다'를 가리키는 표시만 더해집니다.

> 질문: 검토가 명세에서 고칠 자리를 열 군데 남짓 찾았습니다(틀린 전제, 빠진 시험 사례, 티켓 사이의 틈). 그 명세 고침을 어디에 실을까요?
>
> 사용자: 이 티켓 PR에 함께 싣는다 (Recommended) — approval-rules의 티켓 PR이 같은 방식으로 명세를 고쳤습니다(일지 2026-11-05-11의 '명세 고침'). 명세 고침과 티켓이 한 번의 리뷰에 들어가서, 둘이 서로 맞는지 함께 봅니다. 명세와 티켓 파일 모두 커밋 검사(tools/check_ticket.py)가 면제하는 모양이라 검사도 지납니다.

고르지 않은 안: 되울림은 "서버가 쓴 오류 글을 싣지 않는다"(라이브러리 안내까지 사라진다)와 "지금대로 두고 한계로 적는다"(원칙 V와 글자로 어긋난다). 리디렉션은 "마지막 성공 주소로 보낸다", "따라가지 않는다(지금대로)", "어디로든 따라간다". 표시는 "티켓 글로 대신한다". 명세 고침은 "명세 PR을 먼저 따로 연다"(앞 지시문이 적은 순서. 이 결정으로 그 순서를 따르지 않는다).

## 명세 고침

approval-rules 티켓 세션의 선례대로 옛 문장은 지우지 않고 `(2026-11-09 명세 검토: …)` 주석을 각 절에 달았다. 자리는 서두(검토 요약과 수의 변화), "매니페스트"(패턴의 타입 제약, 헤더 이름 아홉의 거부), "계약과 관리 화면"(A의 `transport` 갈래와 http 갈래의 임시 실패, `McpServer(` 생성 자리 열 곳, `[server]` 없음 문구, 스토리 14·15 시험), "접속"(종료 요청의 세 조각을 B2에 묶는다), "실패 문구"(응답 훅은 POST 응답만 받아 두고 2xx면 지운다, 가리기), "닫기"(리디렉션), "로그"(따르지 않은 리디렉션의 WARNING 줄), "고칠 자리의 묶음"(A·B1·B2·C), "다른 문서", Testing Decisions(픽스처 모드 셋과 더한 사례), Further Notes다.

주석에 넣기 전에 코드로 대 본 것: mcp 2.3.0 `handle_get_stream`은 GET 흐름의 오류 응답을 `raise_for_status` 뒤 `except Exception`으로 삼키고 다시 시도한다(읽었다). httpx2 2.13.0 `_send_handling_redirects`는 리디렉션 응답을 포함해 응답마다 응답 훅을 부르고, `follow_redirects=False`면 `response.next_request`를 채워 돌려주며, `max_redirects`는 한 번의 `send` 안의 `history`로만 센다(읽었다). mcp의 `_unfollowed_redirect`는 따르지 않은 리디렉션을 `logger.warning`으로 찍는다(390~391줄). `.claude/rules/adapters.md` 예외 항목은 "원래 예외가 `__cause__`다"라 가리기를 들이는 B1이 함께 고친다. `core/run.py`의 `_cancellation_under`는 닫기의 정리 코드가 덮은 취소를 `__context__`로 찾으므로(1105줄의 쓰임) 가린 예외는 `except` 밖이 아니라 `from None`으로 던진다.

수는 다시 셌다. "거부한 안:" 표시는 main 12개(서두 문장 하나 포함)에서 19개로, 서두 문장을 빼면 열하나에서 열여덟이다. "명세가 정했다" 표시는 23개에서 27개로 넷이 늘었고 매니페스트 주석의 하나가 둘을 덮어 다섯이다.

ADR 0049는 이력 "서버가 되울린 헤더 값을 실패 문구에서 가린다"를 더하고, 그 포인터를 요약·결정 "실패"·Consequences "문구에 실리는 것과 실리지 않는 것"의 세 문장에, 첫째 이력의 포인터를 결정 "닫기" 첫 문장과 요약의 닫기 문장에 달았다. 같은 문단의 "2초를 넘기면 그만둔다"는 첫 문장의 포인터가 덮는다고 새 이력에 적었다(사용자가 고른 자리가 첫 문장과 요약이었다). `uv run python tools/check_adr_pointers.py`는 출력 없이 끝났다. 새 이력의 승인은 셀프 리뷰를 반영한 뒤에 받는다(작업 규약 5).

## 분할 (사용자가 골랐다)

to-tickets 4단계의 질문이다. 첫 호출은 PreToolUse 훅이 사실 대조를 요구해 막았고, 프로브 README의 `deadline_plain` 행(종료 요청 닿지 않음)과 mcp 2.3.0 `streamable_http_manager.py`의 `session_idle_timeout` 기본값 1800초를 대 본 뒤 정상 종료 문장에 "(프로브의 normal 사례)"만 더해 다시 불렀다.

> 질문: mcp-http 티켓을 몇 장으로 나눌까요? (티켓 하나가 PR 하나입니다. '틈'은 앞 티켓만 병합된 동안 잠시 생기는 모자란 동작이고, '종료 요청'은 실행이 끝날 때 원격 서버에 '이 세션은 끝났다'고 알리는 요청입니다.)
>
> 사용자: 네 장 (Recommended) — ① 매니페스트에 원격 서버 모양을 더한다(sdk 모델, openapi.json, 생성 TS 타입) → ② 원격 MCP 서버에 붙는다(접속, 실패 문구, 토큰 가리기) → ③ 취소된 실행에서도 종료 요청을 보낸다(리디렉션 포함)와 ④ 실제 모델로 calc 예시를 원격 서버에 붙여 본다(③과 나란히, ② 뒤). 틈은 둘입니다. ①만 병합된 동안 원격 서버를 적은 실행은 '아직 구현되지 않았다'는 도구 연결 실패로 끝납니다. ②까지 병합된 동안 실행 기한에 걸린 실행은 종료 요청을 보내지 않아 서버가 그 세션을 유휴 만료까지 쥡니다(보내지 않는 것은 명세의 프로브가 쟀고, 만료 30분은 mcp 서버의 기본값을 읽은 것입니다). 정상 종료는 ②에서도 종료 요청을 보냅니다(프로브의 normal 사례).

고르지 않은 안: "세 장, 실제 모델 시험을 ②에 합친다"(②의 PR이 `-m llm`까지 품어 커진다), "세 장, 계약과 접속을 합친다"(한 세션에 들기 어렵다는 어림).

## 티켓

`.scratch/mcp-http/issues/`에 네 장을 썼다. 막는 선은 01 → 02 → {03, 04}이고 03과 04는 나란히 돈다.

- 01 `contract-mcp-server-transport-stdio-or-http`: 계약(sdk 두 모델과 합, `openapi.json`, 생성 TS 타입, 관리 화면 픽스처와 스토리), 어댑터의 `transport` 갈래와 http 갈래의 임시 실패, `McpServer(` 생성 자리 열 곳, 스토리 14·15 시험. Blocked by 없음.
- 02 `connect-to-remote-mcp-server-by-url`: 접속, 실패 문구와 응답 훅의 상태, 가리기, `httpx2` 의존과 import-linter, 규칙 문서 둘, HTTP 픽스처(되울림·리디렉션 모드), 꺼진 서버의 `tool_connection`과 DEBUG 로그 수락. Blocked by 01. 정상 닫기의 종료 요청은 라이브러리 기본값이 보내고, 취소된 실행의 틈은 03이 닫는다고 본문에 적었다.
- 03 `session-close-request-from-cancelled-runs`: `terminate_on_close=False`, 응답 훅의 세션 식별자, 어댑터가 보내는 종료 요청과 리디렉션 판정, 픽스처의 DELETE 모드 셋, 기한 결말 시험과 스토리 12 시험. Blocked by 02.
- 04 `real-model-calc-over-remote-mcp-server`: calc의 `-m llm` 시험 하나. Blocked by 02.

넘긴 것과 받는 쪽: 기능 계획 수락의 앞 절(calc가 원격 서버의 도구를 쓴다)은 04, 뒤 절(꺼진 서버면 `tool_connection`)은 02. ADR 0049 Consequences "로그"의 DEBUG 수락과 "approval-rules와의 접점"의 `ToolSpec.server` 사례는 02. 명세가 넘겨받은 것 (15)(기한 결말과 종료 요청)과 스토리 12는 03. 명세 "실제 모델 시험 하나" 주석의 규칙 파일 함정은 04. 검토가 저장소 밖 사본에서 본 `uv lock`의 차이는 02가 다시 돌려 PR 본문에 적는다. 받는 티켓마다 Blocked by가 넘기는 쪽(명세와 01·02)을 품는지 봤다.

이음매를 코드로 대 본 것(to-tickets 5단계): core `run()`은 도구 포트를 인자로 받는다(`tests/core/test_run.py`의 `_run(..., tools=...)`). 그래서 02·03의 core 시험에 실제 어댑터와 HTTP 픽스처를 넘길 수 있다. `tests/channel/http/test_end_user.py`의 앱 조립 도우미 `_app`은 `tools`를 받는다(03의 스토리 12 시험). `tests/test_main.py`의 실제 모델 선례 둘(트리 전체 복사와 `_copy_repo_plugins`)은 모두 `plugins/rules.toml`을 옮긴다(04).

쓰며 고친 것: 01의 스토리 14 선례가 "임시 플러그인 루트"였는데 `tests/test_server.py`의 기본 클라이언트는 저장소 플러그인을 읽어, 시험 이름(`test_mcp_매니페스트의_command_와_args_도_가리지_않고_내보낸다`)과 "시험이 만든 플러그인 루트"로 고쳤다. 02에 명세가 고칠 자리로 정하지 않은 구현 파일 경로(`core/run.py`)를 적었다가 to-tickets 템플릿 뒤 문단을 다시 읽고 함수 이름과 명세 주석으로 바꿨다. 03의 스토리 번호(종료 요청은 9·12, 2초는 10)를 명세의 User Stories에 대 고쳤다. `uv run python tools/plan_table.py`는 차이를 내지 않았다(티켓이 생겨도 done이 없어 행은 todo 그대로다).

## 인계 (셀프 리뷰 직전)

일지에 "티켓" 절을 쓰고 문서 검사 셋(`tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`, 모두 종료 0)을 돈 뒤 `/code-review`를 불렀을 때, 세션 컨텍스트가 210,360 토큰으로 문턱 200,000을 넘었다는 인계 계기(`셀프 리뷰 직전`)가 왔다. `handoff.md` 1의 인계하지 않는 때 다섯에 들지 않는다(명령은 성공했다, 요청 범위는 병합까지다, 지시문의 이어받을 상태가 `인계:`로 시작하지 않는다, 이 일지에 `인계 못함`이 없다, `get_session`의 `self`에 `parentSessionId`가 없다). 그래서 셀프 리뷰는 밟지 않고 새 세션에 넘긴다. 이 세션의 지금 제목은 `docs/mcp-http-tickets`다. 커밋하지 않은 변경은 명세(`.scratch/mcp-http/spec.md`), ADR 0049, 티켓 네 장, 이 일지다.

지시문:

```
다음 작업: 기능 mcp-http. 원격 MCP 서버에 주소로 접속해, 실행마다 MCP 서버를 새로 띄우는 시작 비용을 없앤다
다음 단계: 티켓
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/mcp-http/spec.md
브랜치: docs/mcp-http-tickets
모델: Opus 5.5 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-09-2138-mcp-http-tickets.md 전체(사용자 프롬프트, "결정"과 "분할"의 사용자 답 원문, 명세 고침, 티켓, 인계). 티켓 .scratch/mcp-http/issues/의 네 장
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다(일지 docs/journal/2026-11-09-2138-mcp-http-tickets.md). 기점은 origin/main이고 미추적 파일(티켓 네 장과 일지)을 범위에 넣으며, 명세 축의 원천은 .scratch/mcp-http/spec.md와 to-tickets 스킬, 사용자의 답은 일지 "결정"·"분할"의 원문이다. 셀프 리뷰를 반영한 뒤 ADR 0049의 새 이력 "서버가 되울린 헤더 값을 실패 문구에서 가린다"와 그 포인터의 초안을 사용자에게 보이고 승인을 받는다(작업 규약 5. 아직 받지 않았다). 그 뒤 커밋, PR 직전 리뷰, PR, 봇 회차, 병합(이 워크트리 사본의 next-session merge.md "워크트리에서 병합할 때"를 Read로 연다), 회고, 다음 지시문이다. 대기열 0518의 "세 번"이 넷이 맞다는 것은 다음 회고가 바로잡는다
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

open-session을 부른다 2026-11-09T13:16:43Z

## 새 세션(인계를 받은 쪽)

세션 제목 `docs/mcp-http-tickets`(앞 세션이 붙인 것과 같다). 사용자 프롬프트는 위 인계의 지시문 그대로다(첫 줄 `.claude/skills/to-tickets/SKILL.md 를 읽어 그대로 따른다. …`, 끝에 `이번 요청 범위: 티켓까지`). 지시문대로 `git worktree list`에서 브랜치가 체크아웃된 자리를 찾아 `EnterWorktree(path)`로 들어왔고 셀프 리뷰부터 했다. origin/main은 그사이 `9d789569`(#502, pilot-portal 화면)로 움직였다. `uv run python tools/sibling_overlap.py`는 "이 브랜치의 새 번호 없음", "번호 겹침 없음", "함께 고친 파일 없음"을 냈다.

### 셀프 리뷰 보고(`/code-review`, 기점 `5af643d7`)

범위: base `5af643d7`, 수정 파일 둘(명세, ADR 0049), 미추적 다섯(티켓 넷, 이 일지), 커밋 0. 두 축 모두 주장 검증 목록과 밀 주장(수, 인용, 선례 이름, 프로브 갈래, 이음매)을 받았다.

표준 축(sonnet/high): Critical·Major 0, Minor 4, Nit 5.

- Minor 1. 04의 "03과 파일이 겹치지 않는다"에 반례가 있다. 04가 02의 픽스처를 공용 자리로 옮길 수 있고 03은 같은 픽스처에 인자 셋을 더한다.
- Minor 2. 01은 `McpServer(` 열 곳만 센다. 합이 되면 `server.command`를 읽는 `tests/adapters/test_filesystem.py` 207줄도 pyright에서 깨진다(`tests/sdk/test_manifest.py` 95~96줄은 sdk 시험 몫).
- Minor 3. 02의 "실행 기한이나 `serve` 종료로 취소된 실행은 보내지 않아(`deadline_plain`)"에서 프로브는 기한만 잰다. "유휴 만료 1800초"는 코드를 읽은 값인데 02·03에 그 표시가 없다.
- Minor 4. ADR 새 이력의 "본문이 JSON-RPC 오류면"에는 `content-type: application/json` 전제가 빠졌다(`streamable_http.py` 403줄). 명세 "로그" 주석의 "실리는 것은 서버가 정한 위치이고 매니페스트의 `url`이 아니다"는 서버가 위치에 쿼리를 옮겨 적으면 반례다. 되울림 관찰은 커밋하지 않은 임시 스크립트에만 있다.
- Nit. ADR "닫기"의 포인터가 셋째 문장("2초를 넘기면 그만둔다") 바로 뒤가 아니다(사용자가 고른 자리). 04가 "규칙 줄을 지우면 묻는다로 멈춘다"를 `_copy_repo_plugins` 독스트링에 돌리는데 그 독스트링은 규칙 파일이 없을 때다. 일지에 머리 줄(세션 제목·브랜치·워크트리·모델)이 없다. 명세 서두 주석이 한 문단으로 길다. 일지 끝의 `open-session을 부른다` 줄이 군더더기다.
- 맞다고 본 것: "거부한 안:" 12→19, "명세가 정했다" 23→27, 포인터 다섯의 제목, 거부 위치 넷과 `union_tag_not_found`·`oneOf`(프로브), `AnyHttpUrl`의 변형(직접 돌렸다), 기한 30/300초, 응답 훅이 리디렉션 응답에서도 돈다는 것, 302·303→GET, 프로브 갈래 이름 여덟, 선례 시험 이름들, `_cancellation_under`의 `__context__`.

명세 축(본 세션 모델): Major 2, Minor 4, Nit 1.

- Major 1. 02의 "리디렉션 모드에서 … 그 뒤 다른 까닭으로 도구 호출이 실패해도 원인 끝에 `HTTP 307`이 붙지 않는다"는 어떤 구현에서도 초록이다. 상태 덧붙임은 여는 동안의 실패에만 걸리고, 픽스처에 "다른 까닭"의 실패를 일으키는 모드가 없다.
- Major 2. `docs/constitution/tech.md` 14줄의 "mcp-http의 첫 티켓이 선언한다"가 거짓이 되고(선언은 02다) 고칠 티켓이 없다.
- Minor 3. "`run()`은 도구 포트를 인자로 받으므로 실제 어댑터를 넘겨 잰다"(02·03)는 절반만 맞다. 서버 모양은 플러그인 포트에서 오는데 `tests/core/test_run.py`의 `_mcp_manifest`와 `tests/channel/http/test_end_user.py`의 `CALC_SERVER`는 stdio 모양이고, 스토리 12 선례의 `asking`은 mcp가 없으며, 03 기한 시험의 선례는 기한이 모델 호출(`SleepyModel`)에 떨어진다.
- Minor 4. 02가 01의 틈 문장("아직 붙지 않는다")을 닫으라고 적지 않았다.
- Minor 5. 표준 축 Minor 1과 같다.
- Minor 6. 리디렉션 조건(기본 포트의 같은 호스트에서 http→https, 위치의 사용자 정보)이 사용자 답의 설명("scheme·호스트·포트가 같고 메서드가 바뀌지 않는")보다 넓다. 라이브러리 규칙과는 같다(`next_request_within_origin`을 불러 봤다). ADR 이력 승인 때 함께 보이라고 했다.
- Nit 7. 02가 따옴표로 든 "mcp 2가 httpx 대신 httpx2를 쓴다"는 `pyproject.toml` 원문(`mcp 는 2 에서 httpx 대신 httpx2 를 쓴다`)과 다르다.
- 맞다고 본 것: 묶음 A·B1·B2·C와 티켓의 대응, 스토리 번호, 기능 계획 수락의 두 절, `McpServer(` 열 곳, 인용들, 수, `patternProperties`, 사용자 답의 조건(8자, 도구 호출 문구, 포인터 자리, 틈 둘), 02의 DEBUG 시험이 빨개질 수 있다는 것, WARNING 단언을 수락으로 세지 않는 까닭.

### 반영(셀프 리뷰)

지적마다 근거를 열고 판정했다.

고친 것:

- 명세 Major 1. 02의 사례를 "리디렉션 모드에 도구 목록 요청을 JSON-RPC 오류로 답하는 인자를 겹쳐 붙으면 여는 동안 실패하고 원인 끝에 `HTTP 307`이 붙지 않는다"로 바꾸고 픽스처의 선택 인자를 넷으로 늘렸다. 상태 덧붙임이 여는 동안의 실패에만 걸린다는 것은 명세 106줄("실패 문구"의 `<원인>` 항목)과 ADR 0049 둘째 이력을 읽어 확인했다. 명세 "실패 문구"의 첫 주석은 "그 뒤의 도구 호출이 … 실패하면"이 같은 잘못이라 여는 단계의 다른 요청으로 고쳤고, Testing Decisions의 주석에 인자와 사례를 더했다.
- 명세 Major 2. `docs/constitution/tech.md` 14줄의 "mcp-http의 첫 티켓이 선언한다"를 "mcp-http의 접속 티켓(02)이 선언한다"로 고치고 헌법 판을 3.0.75로 올렸다(`docs/constitution/README.md`. origin/main의 판도 3.0.74라 `sibling_overlap`의 안내대로 그보다 높다). 판을 올린 까닭은 ADR 0049 새 이력의 "티켓 분할이 바꾼 것" 문단이다. 02에는 선언한 뒤 그 괄호를 선언한 사실과 `uv lock` 결과로 고치는 수락 기준을 더했다. 헌법 개정이라 ADR 초안과 함께 승인을 받는다.
- 명세 Minor 3. 02의 "core를 지나는 시험" 머리에 가짜 플러그인 포트(`FakePlugins`·`_mcp_manifest`)를 http 모양까지 넓힌다는 것을, 03의 기한 시험에 선례의 기한이 `SleepyModel`에 떨어지니 잠드는 도구로 도구 호출 도중에 오게 한다는 것을, 03의 스토리 12 시험에 `CALC_SERVER`가 stdio이고 `asking`이 mcp를 고르지 않는다는 것을 적었다(`tests/core/test_run.py` 159~167줄·5998~6015줄, `tests/channel/http/test_end_user.py` 169~183줄·294줄·2389~2405줄을 읽었다).
- 명세 Minor 4. 02의 잔존 grep에 01의 틈 문장(`.claude/rules/sdk.md`와 어댑터의 독스트링·주석, `아직 구현되지 않았다`)을 더했다.
- 표준 Minor 1·명세 Minor 5. 02가 픽스처와 띄우는 도우미를 처음부터 어댑터 시험과 04가 함께 쓰는 자리에 두게 하고, 04에서 픽스처를 옮기는 절을 걷었다.
- 표준 Minor 2. 01에 `server.command`·`server.args`를 읽는 자리를 더했다(`grep -rn "server\.command\|server\.args" src tests`로 `tests/adapters/test_filesystem.py` 207줄과 `tests/sdk/test_manifest.py` 95~96줄을 손으로 봤다).
- 표준 Minor 3. 02의 틈 문장에서 `serve` 종료를 어림으로 가르고, 유휴 만료를 코드를 읽은 값으로 적었다(mcp 2.3.0 `server/streamable_http_manager.py` 38줄 `DEFAULT_SESSION_IDLE_TIMEOUT: Final = 30 * 60`). 03의 같은 괄호도 그렇게 고쳤다.
- 표준 Minor 4. ADR 새 이력과 명세 "실패 문구" 주석의 되울림 근거에 "400 이상의 오류 응답이 `content-type: application/json`이고"를 더했다(398~416줄을 다시 읽었다). ADR의 관찰 문장은 "손으로 봤다"와 구현 티켓의 되울림 모드 시험이 고정한다는 것으로 고쳤다. 명세 "로그" 주석의 "실리는 것은 서버가 정한 위치이고 매니페스트의 `url`이나 헤더 값이 아니다"는 `_unfollowed_redirect`(72~84줄)를 읽고 "위치 전체가 실리고 헤더 값은 실리지 않는다. 위치에 쿼리를 옮겨 적으면 그것도 실린다"로 고쳤다.
- 명세 Minor 6. ADR 새 이력의 리디렉션 문장을 라이브러리 규칙 그대로(기본 포트의 같은 호스트에서 http→https, 위치의 사용자 정보)로 고쳤다. 사용자 답의 설명보다 넓은 두 조건은 승인 때 함께 보인다.
- 명세 Nit 7. 02의 인용을 `pyproject.toml` 37줄 원문으로 고쳤다.
- 표준 Nit. 04의 "규칙 줄을 지우면 묻는다로 멈춘다"의 근거를 `plugins/rules.toml` 머리 주석("어디에도 맞지 않으면 묻는다")과 ADR 0044로 바꿨다. 일지 머리 줄을 더했다.

남긴 것:

- 표준 Nit, ADR "닫기"의 포인터 자리. 사용자가 첫 문장과 요약을 골랐고, 새 이력이 셋째 문장("2초를 넘기면 그만둔다")까지 덮는다고 적었다.
- 표준 Nit, 명세 서두 주석의 길이. 수의 변화와 그 근거를 한 자리에 모은 주석이라 나누면 수가 흩어진다.
- 표준 Nit, 일지 끝의 `open-session을 부른다` 줄. `next-session` `handoff.md` 4가 쓰라고 하고 5가 읽는 표지라 지우지 않는다.
- 표준 Minor 4의 일부, 되울림 관찰이 커밋한 프로브가 아니라는 것. 근거의 줄기는 코드 읽기(398~416줄)이고 관찰은 손으로 봤다고 적었다. 02의 되울림 모드 시험이 같은 사례를 시험으로 고정한다.

반영으로 새로 쓴 사실 문장(PR 직전 리뷰에 밀 주장으로 넘긴다):

1. 02 "`serve` 종료로 취소된 실행도 같은 취소라 보내지 않는다고 본다(어림. 프로브는 기한만 잰다)"
2. 02 "`DEFAULT_SESSION_IDLE_TIMEOUT`이 `30 * 60`초다"
3. 02·명세 "리디렉션 모드에 도구 목록 요청을 JSON-RPC 오류로 답하는 인자를 겹쳐 붙으면 여는 동안 실패하고, 원인 끝에 `HTTP 307`이 붙지 않는다", "옛 규칙 '2xx가 아닌 응답의 마지막 하나'면 지나간 307이 붙는다"
4. 01 "`grep -rn "server\.command\|server\.args" src tests`로 어댑터 밖에서 나오는 것은 `tests/adapters/test_filesystem.py`의 매니페스트 읽기 시험 하나와 `tests/sdk/test_manifest.py`의 서버 표 시험이다"
5. 03 "그 선례는 기한이 모델 호출(`SleepyModel`)에 떨어진다", "`CALC_SERVER`는 stdio 모양이고 … `asking`은 mcp를 고르지 않아, 실제 어댑터를 넘겨도 서버를 열지 않는다"
6. 04 "규칙 줄을 지우기만 하면 calc의 도구 호출이 어느 규칙에도 맞지 않아 묻는다로 멈춘다"
7. ADR·명세 "400 이상의 오류 응답이 `content-type: application/json`이고 본문이 JSON-RPC 오류면 그 오류의 글을 그대로 예외로 올린다"
8. 명세 "실리는 것은 서버가 정한 위치 전체이고 헤더 값은 실리지 않는다", "서버가 그 위치에 매니페스트 `url`의 쿼리 문자열을 옮겨 적으면 그것도 실린다"
9. ADR "라이브러리가 자기 요청에 쓰는 규칙대로, 같은 출처(scheme·호스트·포트가 같거나, 기본 포트를 쓰는 같은 호스트의 http에서 https로)이고 메서드를 지키며 위치에 사용자 정보가 없는 리디렉션만 따른다"
10. ADR·tech.md "`httpx2`의 선언이 첫 티켓(계약)이 아니라 둘째 티켓(접속)으로 갔다"

다시 돌린 명령: `uv run python tools/check_adr_pointers.py`, `uv run python tools/check_md_tables.py`, `uv run python tools/check_line_separators.py`가 모두 출력 없이 끝났다(종료 0). 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

ADR 이력을 고치기 전에 `.claude/rules/adr.md`대로 Skill 도구로 `domain-modeling`을 불렀다. 이력이 쓰는 "원격 MCP 서버"는 `CONTEXT.md` 219줄의 항목과 같고, 세션 종료 요청과 가리기는 어댑터의 동작이라 용어집에 넣지 않는다. 가리기는 결정 "실패"의 개정이라 새 ADR이 아니라 그 이력이다.

### 승인(AskUserQuestion, 2026-11-09)

첫 호출은 PreToolUse 훅이 사실 대조를 요구해 막았다. 포인터 다섯(요약 둘, 결정 "실패"·"닫기" 하나씩, Consequences 하나)과 `tech.md` 14줄, 판 3.0.74, `30 * 60`초는 이미 대 봤다. 리디렉션 조건은 임시 스크립트(`C:\Users\User\AppData\Local\Temp\claude\C--project-agent\d948bda6-56b7-49f6-81b7-49bcfe239e0f\scratchpad\redirect_rule.py`, httpx2 `MockTransport`로 `http://rag/mcp`의 DELETE에 307을 돌려준다)를 `uv run python`으로 한 번 돌려 mcp 2.3.0 `next_request_within_origin`이 `https://rag/mcp/`는 따르고(`DELETE https://rag/mcp/`) `http://user:pw@rag/mcp/`와 `http://other/mcp/`는 따르지 않는 것을 손으로 봤다(Windows). 명세 "닫기" 주석(122줄)과 티켓 03에 같은 조건이 적힌 것도 grep으로 봤다. 설명의 예시 주소를 본 모양(`http://rag/mcp` → `https://rag/mcp/`)으로 고쳐 다시 불렀다. 질문 문장과 라벨은 그대로다.

> 질문: ADR 0049의 새 이력(서버가 되돌려 보낸 토큰을 실패 문구에서 가린다)과 헌법 tech.md 문구 고침(httpx2를 선언하는 티켓을 '첫 티켓'에서 '접속 티켓(02)'으로, 판 3.0.75)을 이 초안대로 승인하시겠어요?
>
> 사용자: 초안대로 승인 (Recommended) — ADR 0049에 이력이 하나 더해지고 본문 다섯 문장 뒤에 '바뀜' 표시가 붙습니다(새 이력을 가리키는 셋, 앞서 고르신 '닫기' 표시 둘). 헌법 tech.md 14줄의 문구 하나가 바뀌고 판이 3.0.74에서 3.0.75가 됩니다. 결정의 내용은 앞서 고르신 '보낸 토큰을 찾아 가린다' 그대로입니다.

승인 화면의 미리 보기는 이력 전문을 줄인 요약이었다(까닭, 가리기, 남는 한계, 거부한 안, 같은 검토가 함께 바꾼 것, 티켓 분할이 바꾼 것의 여섯 문단). 파일의 이력은 `docs/adr/0049-…` 83~95줄이다.

> 질문: 세션 종료 요청이 리디렉션될 때, 라이브러리 규칙에 있는 조건 두 개(같은 호스트에서 http를 https로 올리는 리디렉션은 따라간다, 주소에 user:pass@가 들면 따라가지 않는다)도 그대로 둘까요?
>
> 사용자: 라이브러리 규칙 그대로 (Recommended) — 예를 들어 http://rag/mcp 에 보낸 종료 요청을 서버가 https://rag/mcp/ 로 보내라고 하면 따라갑니다(mcp 2.3.0의 판정 함수에 넣어 손으로 확인했습니다). 같은 서버로 암호화된 연결을 타고 가는 것이라 토큰이 덜 드러납니다. user:pw@가 든 주소와 다른 호스트로는 따라가지 않습니다. 명세의 '닫기' 주석과 티켓 03에 이미 이렇게 적혀 있어 바뀌는 것이 없습니다.

고르지 않은 안: "고칠 곳이 있다", "scheme까지 같아야만 따라간다".

### 커밋

커밋 전에 `git branch --show-current`가 `docs/mcp-http-tickets`였고, `git fetch origin` 뒤 `uv run python tools/sibling_overlap.py`는 "이 브랜치의 새 번호: 헌법 3.0.75", "번호 겹침 없음", "함께 고친 파일 없음"을 냈다. `uv run python tools/plan_table.py`는 `.scratch/plan.md`를 바꾸지 않았다(done 티켓이 없다). 바꾼 파일은 모두 `tools/check_ticket.py`의 면제 모양이다(`_EXEMPT_FILES`에 `docs/constitution/tech.md`·`README.md`가 든다, 읽었다).

`4797c95b` "docs: mcp-http 티켓 네 장을 쓰고 명세 검토를 반영하며 ADR 0049에 가리기 이력을 남긴다". pre-commit은 ruff 둘이 `.py`가 없어 Skipped, 병렬 검사 열(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 356.9초, web-verify 512.3초)과 마크다운 표·줄 구분·변이 표·헌법 판·커밋 메시지 검사가 Passed였다(카나리아 명세는 해당 파일 없음으로 Skipped). 인용 대조는 경고 12건을 냈고 막지 않았다. 모두 이 일지가 리뷰 서브에이전트의 보고나 옛 문장을 따옴표로 줄여 든 자리라 저장소에 글자 그대로 없는 것이다.

## 인계(커밋 뒤)

커밋 뒤 세션 컨텍스트가 300,899 토큰으로 문턱 200,000을 넘었다는 인계 계기(`커밋 뒤`)가 왔다. `handoff.md` 1의 인계하지 않는 때 다섯에 들지 않는다(커밋은 성공했다, 요청 범위는 병합까지다, 지시문의 이어받을 상태는 `인계: 셀프 리뷰 직전`이라 경계가 다르다, 이 일지에 `인계 못함`이 없다, `get_session`의 `self`에 `parentSessionId`가 없다). `gh pr view docs/mcp-http-tickets --json state`는 PR이 없다고 냈고, 아직 푸시하지 않았다. 이 세션의 지금 제목은 `docs/mcp-http-tickets`다.

지시문:

```
다음 작업: 기능 mcp-http. 원격 MCP 서버에 주소로 접속해, 실행마다 MCP 서버를 새로 띄우는 시작 비용을 없앤다
다음 단계: 티켓
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /to-tickets .scratch/mcp-http/spec.md
브랜치: docs/mcp-http-tickets
모델: Opus 5.5 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-09-2138-mcp-http-tickets.md의 "새 세션(인계를 받은 쪽)"부터 끝까지(셀프 리뷰 보고, 반영과 "반영으로 새로 쓴 사실 문장" 열, 승인, 커밋, 인계)
이어받을 상태: 인계: 커밋 뒤. 커밋 4797c95b까지 셀프 리뷰 반영과 사용자 승인(ADR 0049 새 이력과 포인터, 헌법 tech.md 문구와 판 3.0.75, 리디렉션 조건)을 마쳤다. 아직 푸시하지 않았고 열린 PR이 없다. 남은 단계는 PR 직전 리뷰(coderabbit-review. 못 돌면 /security-review와 bug-perf-review이고, 그 브리프에 일지 "반영으로 새로 쓴 사실 문장" 열을 밀 주장으로 넘긴다), 푸시와 PR, 봇 회차, 병합(이 워크트리 사본의 next-session merge.md "워크트리에서 병합할 때"를 Read로 연다), 회고, 다음 지시문이다. 대기열 0518의 "세 번"이 넷이 맞다는 것은 다음 회고가 바로잡는다(docs/journal/2026-11-09-2138-mcp-http-tickets.md)
확인할 선행 조건: 없음
이번 요청 범위: 티켓까지
```

open-session을 부른다 2026-11-09T13:54:21Z

## 셋째 세션(커밋 뒤 인계를 받은 쪽)

세션 제목 `docs/mcp-http-tickets`(훅이 시킨 대로 다시 붙였다. 앞 제목은 "MCP HTTP 티켓"이었다). 사용자 프롬프트는 위 "인계(커밋 뒤)"의 지시문 그대로다. `git worktree list`에서 브랜치가 `.claude/worktrees/mcp-http-tickets`에 체크아웃된 것을 보고 `EnterWorktree(path)`로 들어왔다. `git fetch origin` 뒤 origin/main은 `9d789569`(#502)였고, `git merge --no-edit origin/main`으로 합쳤다(두 명령의 출력에서 충돌 없음과 커밋 메시지 검사 Passed를 봤다). `/security-review`가 merge-base부터 diff를 모으므로 PR 직전 리뷰 전에 합쳤다(`docs/constitution/operations.md` 리뷰 파이프라인 2).

### PR 직전 리뷰(`coderabbit-review`)

브리프에 위 "반영으로 새로 쓴 사실 문장" 열을 밀 주장으로 넘기고, 그 가운데 코드로 대 볼 여덟 가지(오류 응답의 되울림 조건, 유휴 만료, 같은 출처 판정, 따르지 않은 리디렉션의 경고 글, `server.command` 자리와 `McpServer(` 열 곳, 03의 선례, 02의 307 사례가 빨개질 수 있는지, 가린 예외가 원인 체인으로 새는지)를 따로 적었다. 서브에이전트의 보고: CLI 0.7.5, `auth status`는 `Plan: Free`·`Seat: not assigned`·`Review access Default: njh6803/njh6803`. 친 명령은 `coderabbit review --agent --committed --base origin/main`이고 종료 코드 0, `review_completed`, `findings: 5`, 9개 파일을 모두 봤다. CLI 축이다.

CLI 지적 다섯은 유효 하나(명세 131줄. 원인은 CLI의 주장과 반대 방향이다)와 오탐 넷이었고, 서브에이전트가 CLI 밖에서 유효 Minor 하나, 보류 Minor 둘, Nit 하나를 더 냈다. 밀 주장 열 가운데 8번은 틀렸고 나머지는 맞다고 봤다(3·9번은 라이브러리가 보낸 URL과 같은 사용자 정보를 허용하지만 매니페스트가 사용자 정보를 거부하므로 실제로는 같다는 단서를 달았다).

- 유효 Minor. 명세 131줄 "실리는 것은 서버가 정한 위치 전체이고 … 쿼리 문자열을 옮겨 적으면 그것도 실린다"는 틀렸다. `_unfollowed_redirect`가 부르는 `redirect_location`이 사용자 정보·쿼리·조각을 뗀다.
- 유효 Minor. 02의 가리기 시험이 `__cause__`만 봐서 `from None`을 빠뜨린 구현(`except` 안에서 `from` 없이 던짐)도 초록이다. 그때 `__context__`의 원래 예외가 트레이스백에 실린다.
- 보류 Minor. 응답 훅이 GET 응답을 받아 두지 않는다는 쪽을 빨갛게 할 사례가 없다. 픽스처에 GET을 405로 답하는 인자를 더하자는 제안이다.
- 보류 Minor. 변수 이름 칸에 토큰 자체를 적는 실수(패턴 `^[A-Za-z0-9_]+$`를 지나는 토큰)가 "환경 변수 <변수 이름>이 없다"로 실패 문구에 실리는데 알려진 한계에 없다.
- Nit. 02가 어댑터 모듈 독스트링의 `__cause__` 문장을 이름으로 들지 않는다.
- 오탐 넷: ADR "닫기"의 셋째 문장 뒤 포인터(사용자가 고른 자리), 01의 `additionalProperties: false`(pydantic 2.13이 `patternProperties`만 내고 읽는 단계가 `string_pattern_mismatch`로 거부한다는 것을 서브에이전트가 스크래치패드 스크립트로 봤다. 01이 그 거부 시험을 요구한다), 02의 `isError` 본문과 8자 미만 토큰(둘 다 사용자가 고른 한계로 ADR 새 이력과 명세 111줄에 적혀 있다), 명세 131줄의 WARNING 쿼리 노출(라이브러리가 이미 뗀다. 근거가 된 문장의 잘못은 위 첫 유효로 옮겼다).

### 반영(PR 직전 리뷰)

고친 것:

- 명세 131줄. mcp 2.3.0 `shared/_httpx_utils.py` 172~177줄의 `redirect_location`(`copy_with(userinfo=b"", query=None, fragment=None)`, 독스트링 "without userinfo, query or fragment")과 `client/streamable_http.py` 70~84줄을 읽고 "사용자 정보·쿼리 문자열·조각을 뗀 주소(scheme·호스트·포트·경로)이고 … 서버가 그 위치의 경로에 옮겨 적은 글은 실린다"로 고쳤다. 같은 문장이 다른 파일에 있는지 `Redirect to|not followed|따르지 않은 리디렉션`으로 명세·티켓·ADR 0049를 grep해 131줄 한 곳뿐인 것을 봤다. 위 셀프 리뷰 반영의 표준 Minor 4 항목과 "반영으로 새로 쓴 사실 문장" 8번은 그때 쓴 기록이라 고치지 않고 여기에 틀렸다고 적는다. 그 반영이 `_unfollowed_redirect`만 읽고 그것이 부르는 함수를 따라가지 않았다.
- 02 53줄과 명세 177줄. 가리기 시험에 "`__suppress_context__`가 참이라 `traceback.format_exception`으로 펼친 글에도 값이 없다"를 더하고 그 까닭을 적었다. 스크래치패드 스크립트(`C:\Users\User\AppData\Local\Temp\claude\C--project-agent\8936549f-c8b3-4de6-a00e-3e4a72df16f0\scratchpad\suppress_context.py`)를 `uv run python -I`로 한 번 돌려, `except` 안에서 `from None`으로 던지면 `__cause__=None`, `__suppress_context__=True`, 트레이스백 글에 비밀이 없고, `from` 없이 던지면 `__cause__=None`이어도 `__suppress_context__=False`라 트레이스백 글에 비밀이 실리는 것을 손으로 봤다(Windows. 두 경우 모두 `__context__`에는 비밀이 든다).
- Nit. 02의 독스트링 항목에 "원인(`__cause__`)에는 mcp 의 원래 예외가 남는다"와 "원래 예외가 `__cause__` 다"를 가린 경우를 들어 고친다는 괄호를 더했다(`src/agent_os/adapters/mcp.py` 6~9줄을 읽었다).

남긴 것:

- 보류 Minor, GET 405 사례. mcp 2.3.0 클라이언트는 `notifications/initialized`를 보낼 때 GET 흐름을 따로 연다(`client/streamable_http.py` 637~639줄의 `start_get_stream()`, 224~272줄의 `handle_get_stream`을 읽었다). 그래서 GET의 405와 도구 목록 요청의 응답은 순서가 정해지지 않는다. 새 규칙은 POST의 2xx에서 지우므로 GET을 받아 두는 구현이 빨개지려면 405가 마지막 POST 응답 뒤, 실패 문구를 짓기 전에 와야 하고, 그 순서를 픽스처가 고정하려면 클라이언트 안쪽의 시점에 기대야 한다(어림. 돌려 보지 않았다). 명세 167줄은 응답 훅 같은 안쪽을 시험하지 않는다고 정했다. PR 체크리스트에 판정과 값을 적는다.
- 보류 Minor, 변수 이름 칸의 토큰. 그 칸에 토큰을 적으면 그 토큰은 이미 플러그인 매니페스트 파일에 있고, 관리 API의 매니페스트 응답도 파일 그대로다(명세 105줄). 실패 문구에서 변수 이름을 빼면 운영자가 어느 변수가 없는지 모른다. 한계 한 줄을 더해도 막는 것이 없어 두었다. PR 체크리스트에 적는다.
