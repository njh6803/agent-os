# 2026-11-12 (22:23) 커스텀 에이전트 안내 문서와 이름만 바꾼 사본의 시험

세션 제목: `feature/04-custom-agent-guide-and-renamed-copy-test`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/04-custom-agent-guide-and-renamed-copy-test`, 기준 커밋 `9714908a0`(#547). 모델 `claude-sonnet-5-5` / high. next-session 지시문으로 연 새 세션이다. 첫 턴에 제목을 바꾸고 `tidy-checkouts`를 돈 뒤 `EnterWorktree`(name `04-custom-agent-guide-and-renamed-copy-test`)로 들어가 브랜치를 티켓 stem으로 바꿨다.

## 사용자 프롬프트

> 사용자: 다음 작업: .scratch/base-agent/issues/04-custom-agent-guide-and-renamed-copy-test.md. 커스텀 에이전트 안내 문서를 쓰고, 이름만 바꾼 사본이 원본과 같은 시험을 지나게 한다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 04-custom-agent-guide-and-renamed-copy-test)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/base-agent/issues/04-custom-agent-guide-and-renamed-copy-test.md
> 브랜치: feature/04-custom-agent-guide-and-renamed-copy-test
> 모델: Sonnet 5.5 / high
> 읽을 것: .scratch/base-agent/issues/05-real-model-assistant-answers-with-sources.md, .scratch/base-agent/issues/06-widget-real-model-assistant-case.md (나란히 도는 나머지 티켓)
> 이어받을 상태: 앞 PR 546(dev-release-pr-step)을 병합하며 보류한 일이 일지 docs/journal/2026-11-12-1623-dev-release-pr-step.md의 "다음"에 있다. 그중 claude-review 셋째 리뷰의 보류(merge.md 출시 PR의 dev 삭제 갈래는 밟은 적이 없다, 계기와 결정표의 같은 조건 중복, test_protection_json.py의 enforce_admins 설명 한 줄)는 일지에 아직 없고 PR 546의 코멘트에만 있다. 이 티켓의 일이 아니므로 하지 말고, 마칠 때 보고에 남긴다. 사용자에게 넘길 질문 하나가 앞 세션에 있었다(handoff.md에 여섯째 예외를 더할지)
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 다른 계정이면 gh 인증이 njh6803/agent-os에서 PR을 열고 병합할 권한을 갖는지
> 이번 요청 범위: PR과 병합까지

## 체크아웃 정리

주 체크아웃 세션에서 `tidy-checkouts`를 돌았다. 루트는 이미 dev였고 깨끗했으며 `HEAD`가 `origin/dev`(`9714908a0`)와 같아 당길 것이 없었다. `judge`의 줄은 모두 `남긴다`였고 지운 것은 없다. 까닭은 병합된 PR이 없다, 바뀐 파일이 있다, 폴더를 쥔 프로세스가 있다, 앱의 표지가 있다, 다시 만들 수 없는 무시된 항목이 있다였다. 브랜치도 `main`(지우지 않는다)과 막 딴 `worktree-local-model-tickets`만 남겼다.

## 한 것 (모두 커밋하지 않았다)

- **안내 문서 `plugins/README.md`(미추적).** 명세 "안내 문서"의 여덟과 붙이는 설정을 아홉 절로 썼다. 기본 에이전트의 네 자리(표), 사본을 만드는 세 걸음(bash와 PowerShell 복사 명령, 고친 매니페스트 전문, 규칙 표 코드 블록), 고치는 다섯 가지, 두 끝의 셈(`max_turns = max_tool_calls + 2`, 상한 10, 쓸모 있는 `max_tool_calls` 최댓값 8), 열기(사이트 파일 `agents = ["acme-assistant"]`와 `<agent-os-widget agent="acme-assistant">`), 사본은 원본을 따라가지 않는다, 스킬의 지시는 보장이 아니다와 코드에 고정 단계(`ctx.tool("search", query=...)`), 확인하는 법(`run`, `resume`, 트레이스), 문서 검색 서버에 붙이기(`url`, `DOC_SEARCH_AUTHORIZATION`에 `Bearer <토큰>` 전체, `RAG_ALLOWED_HOSTS`의 `rag-engine`, 421). 맨 끝 절에 돌려 본 것과 돌려 보지 못한 것을 갈라 적었다.
- **시험 `tests/test_assistant_plugin.py`(수정).** 실행 시험 열 함수를 `bundle` 픽스처(`원본`·`사본`)로 매개변수화했다(스무 사례). 사본은 시험이 안내 문서의 순서대로 만든다: `agents/assistant`을 `agents/acme-assistant`로 복사하고, 안내 문서의 ` ```toml ` 코드 블록 둘(고친 매니페스트, 규칙 표)을 글자 그대로 읽어 사본의 `plugin.toml`과 `rules.toml` 끝에 쓴다(`_guide_manifest`, `_guide_rules_table`). 문서와 시험이 같은 글자를 쓰게 하려는 것이다(셀프 리뷰 반영 뒤의 모양. 처음에는 매니페스트를 시험이 직접 고쳤다). 새 시험 여섯 함수: 안내 문서가 플러그인으로 읽히지 않음(`list_manifests`), 문서의 규칙 표가 기본 표와 같은 규칙을 든다(TOML로 읽어 대조), 문서의 `doc-search` 블록이 실제 연결 매니페스트의 `server` 표와 같음, 문서가 필수 조각을 모두 담음, 사본의 한계와 스킬의 한계를 밝힘(매개변수 셋), 안내 문서의 순서대로 만든 사본이 원본과 `name`·규칙 표만 다름(코드 파일은 바이트까지 같음). 처음에 한 번 빨갛게 확인했다(문서가 없을 때 `GUIDE.is_file()`에서 실패). 셀프 리뷰 뒤에는 문서의 매니페스트 블록을 일부러 `max_tool_calls = 5`로 틀려 사본의 순서 비교 시험과 사본의 끝 넘음 시험이 빨개지는 것을 보고 되돌렸다. 지금 34개 초록.
- **`README.md`(수정).** 저장소 지도의 `plugins/` 아래에 `README.md` 줄을 더했다.
- **티켓.** `Status`를 `done`으로, 수용 기준 일곱을 `[x]`로 바꿨다. 마지막 항목 "검증 명령이 모두 초록이다"는 아직 검증 전에 표시만 했다. 새 세션은 검증이 끝나기 전에 커밋하지 않는다. 04~07이 아직 열려 있어(05·06·07) 기능 계획의 `**끝:**` 줄은 쓰지 않는다. `plan_table.py`를 돌았고 `.scratch/plan.md`는 바뀌지 않았다.

## 돌려 본 것

근거의 종류: 아래 첫 두 항목은 손으로 친 명령의 출력이고, "코드로 대 본 문장"은 코드를 읽은 것이다(함수를 불러 대 보지는 않았다). ruff와 `run_checks.py`는 도구가 찍은 결과다.

- 문서의 복사 명령 둘(bash `cp -r`, PowerShell `Copy-Item -Recurse`)을 임시 복사본에서 쳐서 `agents/acme-assistant`가 생기는 것을 봤다.
- 문서의 `name` 고치기(`sed`)와 규칙 표 붙이기까지 한 임시 루트에서 `uv run agent-os run acme-assistant "<질문>" --model claude-opus-5 --verbose --plugins-root <임시> --traces <임시>`를 키 없이 쳤다. 사본이 오류 없이 로드되어 `run_started`의 `agent`가 `acme-assistant`이고, `DOC_SEARCH_AUTHORIZATION`이 없다는 문구를 든 `run_failed`(`cause` `tool_connection`)로 끝났다(종료 1). 문서 8·9절의 서술과 맞는다.
- 코드로 대 본 문장: 폴더 이름과 `name`이 다르면 로더 오류(`filesystem.py`의 "디렉터리와 name이 어긋난다"), `resume`의 `--pause-index` 필수와 일시정지 시 안내 명령 출력(종료 3), 플러그인 이름 패턴 `^[a-z][a-z0-9-]{1,62}$`, `ctx.tool(name, **args)`의 시그니처.
- `uv run ruff check .`와 `uv run ruff format --check .`: 통과.
- `uv run python tools/run_checks.py`(백그라운드, 로그는 스크래치패드 `checks.log`): 여덟 단계 Passed(check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks). 나머지 `pytest`와 `web-verify`는 도는 중에 인계하며 멈췄다. **새 세션이 `run_checks.py`를 처음부터 다시 돌아야 한다.**

## 돌려 보지 못한 것 (문서 끝 절에도 적었다)

- 실제 모델로 `run`을 끝까지 돌려 답을 받는 것. 키가 없는 환경이었고 그 몫은 티켓 05다.
- 실제 문서 검색 서버(`rag-engine`)에 붙는 것. 토큰과 `RAG_ALLOWED_HOSTS`가 실제 서버와 맞물리는지는 티켓 07의 몫이다.
- 문서 5절의 사이트 파일·위젯 속성은 서버를 띄워 확인하지 않았다. 사이트 파일의 키 이름(`agents`)과 위젯 속성 이름(`agent`)은 코드와 `EMBED.md`에서 읽은 것이다.

## 인계 (셀프 리뷰 직전)

컨텍스트가 문턱을 넘은 채 셀프 리뷰 직전에 왔다. 방금 `/code-review`를 불렀으나 서브에이전트는 띄우지 않았다. 새 세션이 셀프 리뷰부터 한다. 범위는 `git merge-base origin/dev HEAD`(`9714908a0`)부터 추적 파일 셋(`README.md`, `tests/test_assistant_plugin.py`, 티켓)과 미추적 파일 둘(`plugins/README.md`, 이 일지)이다. 명세는 `.scratch/base-agent/spec.md`의 "안내 문서"와 "플러그인 꾸러미의 시험", 티켓은 위 04 파일이다. 리뷰어가 짚을 만한 자리로 내가 보는 것: 문서 본문이 "이 시험이 한다"고 주장하는 문장(2절 끝, 마지막 절)이 시험의 실제 범위와 맞는지, 문서가 서술한 코드 동작(두 끝의 셈, `resume` 인자)이 코드와 맞는지, `README.md` 지도 줄.

사용자 질문 하나가 앞 세션(dev-release-pr-step)에서 넘어와 있다: `handoff.md`에 여섯째 "인계하지 않는 때"를 더할지. 이 티켓의 일이 아니다. 마칠 때 보고에 남긴다. 그 지시문의 이어받을 상태가 말한 PR 546 claude-review 셋째 리뷰의 보류 셋(출시 PR의 dev 삭제 갈래는 밟은 적이 없다, 계기와 결정표의 같은 조건 중복, `test_protection_json.py`의 `enforce_admins` 설명 한 줄)도 하지 말고 마칠 때 보고에 남긴다.

제목은 `feature/04-custom-agent-guide-and-renamed-copy-test (인계함)`으로 바꾼다. 인계 전의 제목은 `feature/04-custom-agent-guide-and-renamed-copy-test`였다.

open-session을 부른다 2026-11-12T13:24:35Z

## 셀프 리뷰 (이어받은 세션)

범위: 기준 `9714908a0`, 추적 파일 셋과 미추적 파일 둘(안내 문서, 이 일지), 커밋 0. 표준 축은 sonnet·high, 명세 축은 세션 모델로 병렬로 돌렸다. 명세는 티켓 04와 `.scratch/base-agent/spec.md`의 "안내 문서"·"플러그인 꾸러미의 시험"이다.

고친 것(지적마다 코드로 대 본 뒤 판정했다).

- 안내 문서 6절: "스킬과 규칙 표가 고쳐져도 사본은 그 고침을 받지 않는다"는 거짓이었다. 사본은 `skills`·`mcp`를 이름으로 가리키므로 스킬과 연결은 원본과 사본이 함께 쓴다(3절과 9절도 그렇게 말한다). 따라가지 않는 것은 코드와 매니페스트와 규칙 표뿐이라고 고치고, 스킬·연결을 함께 쓴다는 문단과 따로 두는 길을 더했다.
- 4절: 1만 더한 `max_turns`는 5이고 오류 문구는 `core/loop.py`의 `f"루프가 {max_turns}턴 안에 멈추지 않았다"`라서 "6턴"이 아니라 "5턴"이다. 코드를 읽어 고쳤고 5로 돌려 보지는 않았다.
- 8절: `run`이 표준 출력에 내는 것은 `승인:` 줄(끝에 `--approve`가 이미 있음)과 `거부:` 줄(`--deny --reason`에서 끝남) 둘이다(`channel/cli/main.py`의 `_approval_request`). 문서의 "끝에 붙인다" 서술을 이에 맞췄다.
- 9절: 명세에 없고 돌려 보지도 않은 서술("개발 PC에서 `http://127.0.0.1:8000/mcp`", "같은 컴퓨터나 같은 도커 네트워크 안의 서버에만")을 지웠다. 끝 절에는 이 저장소의 가짜 서버가 `RAG_ALLOWED_HOSTS`를 모르고 루프백 `Host`만 받는다는 것과, 9절의 `RAG_ALLOWED_HOSTS`·421은 문서 검색 서버 쪽 명세를 읽고 적은 것이지 이 저장소에서 잰 것이 아니라는 것을 밝혔다.
- 3절 `mcp` 항목: 규칙 표가 `doc-search:search`처럼 연결 이름에 묶이므로 연결 이름을 바꾸면 표도 고쳐야 한다는 것을 더했다. 고치지 않으면 표가 연결에 없는 서버를 가리켜 그 실행은 도구 연결 오류로 끝난다(`core.md` 실패 정책. 처음에 쓴 "기본값으로 묻게 된다"는 틀려서 바로 고쳤다).
- 시험: 문서 매니페스트 블록을 시험이 읽지 않고 직접 고쳐 쓰던 것을, 문서 블록을 글자 그대로 쓰도록 바꿨다. 문서의 `doc-search` 블록과 규칙 표는 TOML로 읽어 실제 파일과 대조한다. 문서 어디에든 있으면 통과하던 부분 문자열(`"10"`, `"max_turns"`, `"max_tool_calls"`, `"rag-engine"`)을 `max_turns = max_tool_calls + 2`와 `10을 넘`으로 좁혔다. 에이전트 목록의 `== {"assistant","calc"}`는 `ORIGINAL in`으로 풀었다.

남긴 것: 명세 축의 범위 넘침 둘(6절 끝 문단, 8절 트레이스 읽는 법)은 사실 오류가 없고 안내 문서의 목적에 맞아 두었다. 루트 `README.md`의 지도 줄은 구조 변경 규약상 맞다. `_copy_by_guide`와 `_plugins_copy`의 `copytree` 두 번은 작은 중복이라 두었다.

다시 돌린 것: `uv run ruff check .`·`ruff format --check .` 통과, `pytest tests/test_assistant_plugin.py` 34개 초록, `pyright` 0 오류. 전체 `run_checks.py`는 처음부터 다시 돌았다(결과는 아래 "마무리").

PR 직전 리뷰에 밀 주장(새로 쓴 사실 문장): (1) 6절 "스킬과 연결은 이름으로 가리키므로 사본이 같은 이름을 가리키는 동안 원본과 함께 쓴다", (2) 4절 "1만 더하면 … 루프가 5턴 안에 멈추지 않았다", (3) 8절 "`승인:` 줄은 `--approve`가 이미 붙어 있고 `거부:` 줄은 `--deny --reason`에서 끝난다", (4) 3절 "연결 이름을 바꾸고 표를 안 고치면 도구 연결 오류로 끝난다".
