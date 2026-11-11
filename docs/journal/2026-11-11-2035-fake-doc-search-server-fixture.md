# 2026-11-11 (20:35) 가짜 문서 검색 서버 픽스처

세션 제목: `feature/02-fake-doc-search-server-fixture`. 브랜치 `feature/02-fake-doc-search-server-fixture`, 워크트리 `.claude/worktrees/02-fake-doc-search-server-fixture`, 기준 커밋 `377675eef`(#528). 모델 `claude-sonnet-5-5` / high. next-session 지시문으로 연 새 세션이다. 첫 턴에 제목을 바꾸고 `EnterWorktree`(name `02-fake-doc-search-server-fixture`)로 들어간 뒤 브랜치를 `worktree-02-fake-doc-search-server-fixture`에서 티켓 stem으로 바꿨다. 이 파일은 컨텍스트가 인계 문턱을 넘어 셀프 리뷰 직전에 인계하며 만들었다. 이어받는 세션이 같은 파일에 쓰고 커밋한다.

## 사용자 프롬프트

> 사용자: 다음 작업: .scratch/base-agent/issues/02-fake-doc-search-server-fixture.md. 시험이 실제 문서 검색 서버의 모양으로 답하는 별도 프로세스 픽스처(가짜 서버)를 만드는 티켓이다(03을 막는다)
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 2 중 2. 각자 워크트리다. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/base-agent/issues/02-fake-doc-search-server-fixture.md
> 브랜치: feature/02-fake-doc-search-server-fixture
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-11-1555-base-agent-tickets.md의 "다음", 나란히 도는 티켓 .scratch/base-agent/issues/01-contract-agent-manifest-turn-and-tool-call-limits.md
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 것 (모두 커밋 전, 작업 트리)

- 티켓 `Status`를 `in-progress`로 바꿨다(첫 편집). 체크박스는 아직 모두 비어 있고 `done`으로 바꾸지 않았다.
- `tests/fake_doc_search_server.py`(새): 프로브 `.scratch/base-agent/probes/fake_doc_search.py`를 옮겨 와 독스트링을 새로 썼다(옮긴 원천, 같게 둔 것, 다르게 둔 것, 표본, 05의 단언이 표본의 글자에 기댄다는 것, 선택 인자, 기록). 더한 것은 `Recording` 미들웨어(요청마다 기록 한 줄, `--expect-authorization`이면 다른 값을 401로 막고 막은 요청도 기록, `tools/call`의 줄에 `tool`과 `arguments`)와 인자 `record`다. `_guarded`를 시험이 부르도록 `guarded`로 공개했다. 시작 때 `ready` 줄을 찍지 않는다(띄우는 쪽이 TCP 접속으로 기다린다). 판은 `FORMAT_VERSION` 한 곳이다.
- `tests/fake_doc_search.py`(새): `DocSearchFixture(HttpFixture)`와 `serving`. `tool_calls()`가 기록에서 이름과 인자를 낸다.
- `tests/mcp_http.py`: `HttpFixture.__init__`에 키워드 인자 `server: Path = SERVER` 하나를 더했다(재사용을 위한 최소 고침, 기존 호출은 그대로).
- `tests/test_fake_doc_search.py`(새): 시험 15개. 실제 MCP 클라이언트(`streamable_http_client`와 `ClientSession`)로 붙는다. 도구 셋과 출력 스키마와 판, 창 상한이 도구 설명 글에 들어가는 것, 검색(top_k, 점수 순, 무관한 질문에도 조각), 형식마다의 위치, `include_text` 게이트, 전문의 네 모양, 창(블록 경계, `next_offset`, 마지막 창의 null, 785자가 셋), 오류(`invalid_argument` 열 갈래와 `knowledge_base_not_found`, `document_not_found`), `internal_error`(프로세스 안에서 `guarded`에 예외를 던지는 함수), 실패 모드 셋, 401과 통과, 헤더와 도구 호출의 기록, 끈 뒤 포트가 닫힘.
- `.scratch/base-agent/probes/fake_doc_search_fixture_mutations.toml`(새)과 같은 디렉터리 `README.md` 표의 줄 하나: 변이 여섯. 구현 뒤에 쓴 시험이라 빨강을 본 적이 없어서 `tools/mutate.py`로 넣었다. 여섯 모두 표지까지 기대대로 빨개졌다(도구가 찍었다). 첫 판은 표지 둘이 틀렸다(저장된 문자열이 따옴표 `"`를 써서 repr이 달랐다, 둘째 단언이 앞서 실패했다). 시험 메시지와 표지를 고치고 그 둘만 다시 돌려 확인했다. 표지가 시험 파일의 원문에 글자 그대로 있으면 변이 도구가 메아리로 알리므로 메시지에 값이 끼는 f-string으로 두었다.

## 검증

- `uv run ruff check .`와 `uv run ruff format --check .`: 통과(포매팅을 마친 뒤).
- `uv run python tools/run_checks.py`: 열 개 모두 Passed (lint-imports, check-ticket, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest 699.5초, web-verify 857.1초). 이 실행은 위의 모든 파일이 지금 모양일 때 돌았다. 그 뒤로 코드나 시험을 고치지 않았다(변이 표의 README 줄과 이 일지만 더했다).
- 새 시험만 따로: 15 passed. 서버를 시험마다 새로 띄워 한 시험이 7~100초 걸린다(다른 세션과 겹친 부하에서 한 시험이 125초 나온 적이 있다). 합친 시간이 부담이면 셀프 리뷰가 서버를 나눠 쓰는 방법을 짚을 수 있다. 이 세션은 합치지 않았다.

## 알아 둘 것

- 윈도의 venv 파이썬은 실행기가 진짜 파이썬을 자식으로 띄운다. `HttpFixture.stop()`이 `terminate()`한 직후에는 포트가 아직 열려 있을 수 있고 잠시 뒤 닫힌다(첫 시험은 즉시 견주어 빨갰고, 직접 본 프로세스는 곧 없었다). 시험은 기한 30초까지 거듭 견주게 고쳤다. 선례 픽스처의 `stop()`은 건드리지 않았다. 근거는 이 PC에서 본 현상 하나이고 실행기 구조는 어림이다.
- 티켓의 "프로브의 서버에 없던 헤더 확인처럼 픽스처에서 달라진 것"은 서버 독스트링의 "프로브의 서버에 없던 것"에 적었다.
- 프로브 `skill_follow.py`와 프로브의 가짜 서버는 건드리지 않았다. 03이 프로브가 이 픽스처를 띄우게 고치고 프로브의 서버를 지운다.

## 인계

경계 `셀프 리뷰 직전`. 세션 제목을 `feature/02-fake-doc-search-server-fixture (인계함)`으로 바꿨고(바꾸기 전 제목은 `feature/02-fake-doc-search-server-fixture`), 워크트리 잠금을 풀었다. 백그라운드 작업은 모두 끝나 있었다.

open-session을 부른다 2026-11-11T11:37:09Z

## 셀프 리뷰 (이어받은 세션, base `377675eef`, 변경 추적 파일 3개와 미추적 5개, 커밋 0)

두 축 모두 Critical·Major는 없었다. 표준 축(sonnet·high)은 하드 위반 0이고 판단 항목 일곱, 명세 축은 Minor만 냈다.

- **고친 것.**
  - `tests/test_fake_doc_search.py`: 포트 닫힘 상한 상수 주석의 "즉시 닫히는 값"이 일지의 "첫 시험은 즉시 견주어 빨갰다"와 어긋나서 고쳤다. 포트 닫힘을 기다리는 주석은 실행기 구조를 사실처럼 단정했는데 근거는 이 PC에서 본 현상 하나와 어림이어서 어림이라고 적었다.
  - `tests/fake_doc_search_server.py`: 프로브 독스트링에 없던 새 주장 "(실제 서버는 토큰을 검증한다)"를 지웠다. 옮긴 원천에서 확인한 것은 토큰 범위에 닿는 지식베이스만 낸다는 설명 글뿐이었다. "03과 05가 함께 쓴다"는 06(위젯 e2e)도 쓰므로 "같은 시험이 쓴다"로 열었다. `tests/fake_doc_search.py`의 같은 문장도 같게 고쳤다.
- **남긴 것.**
  - `_listening`이 `tests/mcp_http.py`와 시험에 같은 세 줄로 있다. 선례 쪽이 비공개 이름이라 가져다 쓰지 않았다(Minor).
  - `_is_object` 같은 TypeGuard가 서버, 시험, 선례 서버에 반복된다. `Mode`의 불리언 칸 둘을 열거로 두라는 지적, `guarded`가 세기와 결과를 함께 한다는 지적, `_search`의 Feature Envy 지적은 판단 항목이고 프로브에서 글자까지 옮긴 코드라 03이 프로브 서버를 지울 때까지 모양을 바꾸지 않았다.
  - 시험이 도구 설명 글과 출력 스키마의 칸 설명을 지키지 않고, `get_document` 입력 검증의 차례를 단일 오류 입력으로만 대 본다(명세 축 Minor). 명세 축 서브에이전트가 프로브와 픽스처 두 모듈을 불러 도구 정의와 표본을 견주었고 같다고 보고했다(이 세션이 다시 견주지는 않았다). 표준 축 서브에이전트는 두 서버 파일을 `diff`해 차이가 `guarded` 공개, `Recording`, `record` 인자, `ready` 줄 삭제뿐이라고 보고했다(같은 이유로 다시 재지 않았다).
  - 시험 주석 "첫 창이 제목 줄로 끝날 수 있다"에 맞는 단언이 없다.
- **다시 돌린 명령.** 고친 것은 주석과 독스트링 문장뿐이다. `ruff check`와 `ruff format --check`는 바뀐 파일에서 통과했고, 전체는 커밋의 pre-commit 결과로 갈음한다.

## 남은 일 (이 세션의 요청 범위는 PR과 병합까지)

1. `/code-review`(셀프 리뷰). 기준은 `origin/main` 이후의 이 브랜치 변경이고 모두 커밋 전이라 미추적 파일 넷이 든다(서버 모듈, 띄우는 쪽, 시험, 변이 표). 명세 축의 기준은 티켓 02와 `spec.md`의 "가짜 검색 서버" 절이다. Critical·Major를 고친다.
2. 티켓 체크박스를 모두 `[x]`로 바꾸고 `Status`를 `done`으로 바꾼다. 이 티켓이 기능의 마지막 열린 티켓은 아니므로 기능 계획의 `**끝:**` 줄은 쓰지 않는다. 기능 디렉터리에 다른 열린 티켓이 있는지 `.scratch/base-agent/issues/`에서 확인한다. 티켓을 `done`으로 바꾼 커밋은 `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`까지 싣는다.
3. 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`를 친다.
4. 커밋, 푸시, PR, 병합. `merge.md`를 Read로 열어 따른다(이 세션은 워크트리라 "워크트리에서 병합할 때"가 적용된다).
