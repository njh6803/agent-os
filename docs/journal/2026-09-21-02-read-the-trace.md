# 2026-09-21 · 인터럽트 02: 트레이스를 읽는다

인터럽트 슬라이스의 둘째 티켓. 재개(04)가 설 바닥을 미리 까는 프리팩터라 사용자에게 보이는 새
동작은 없다. `/implement`로 새 세션에서 시작했고 브랜치는 `feature/02-read-the-trace`. 이음매는
명세가 정한 트레이스 어댑터 하나이고, 주 이음매(`core`의 `run()`)는 가짜 포트에 `read`가 붙는 것
말고 바뀌지 않았다.

## 한 것

- `TraceSink` → `TraceStore`. `write(event)`에 `read(run_id) -> Trace | None`이 붙는다. 포트는
  다섯 그대로다. 부재는 `PluginSource.read_manifest`와 같이 `None`이다. 포트마다 부재 표현이
  다르면 읽는 쪽이 갈린다.
- 읽기 결과 타입 `Trace`(실행 식별자, 형식 버전, 이벤트 열)와 `UnknownEvent`를 어댑터에서
  `core/ports.py`로 옮겼다. 포트의 반환 타입은 포트를 선언하는 쪽이 소유해야 어댑터가 import할 수
  있다(원칙 IV). `ToolSpec`·`ToolResult`가 같은 자리에 있는 선례다. 헤더(`TraceHeader`)는 JSONL
  파일의 첫 줄이라는 디스크 형식이므로 어댑터에 남겼다.
- `read_trace(path)` 모듈 함수를 없앴다. 읽는 길이 둘이면 CLI 테스트가 포트를 우회해 파일 경로로
  읽는다. 이제 CLI 테스트도 같은 어댑터의 `read(run_id)`로 읽어, 04에서 `core`가 읽는 길과
  테스트가 검증하는 길이 하나다.
- 규칙 셋(`core.md` 포트 표, `adapters.md`, `tests.md`)을 코드와 같은 커밋에서 새 이름으로.
- 어댑터 테스트 셋을 더했다. 여러 실행이 섞여 쓰여도 한 실행의 이벤트만 쓴 순서대로, 쓴 적 없는
  실행은 `None`, 형식 1 파일은 읽히고 결과가 버전 1임을 말한다.

## 옛 이름 잔존

코드·규칙·README·CONTEXT에서 0이다. 남긴 것은 개명 결정 자체를 적은 ADR 0009와 인터럽트 명세,
지난 일지들, 닫힌 첫 슬라이스 명세다. 기록을 고치면 이력이 거짓이 되고, 현재 진실은 규칙 문서의
포트 표가 가리킨다. 명세 축 리뷰도 같은 판정을 냈다.

## 셀프 리뷰

두 축이 같은 Minor 하나를 집었다. `Trace.schema_version`이 어댑터 헤더의 `Literal["1", "2"]`에서
포트 경계에서 `str`로 넓어진다는 것. 04가 버전 1을 거부할 때 문자열 비교에 기대게 되고 가짜가
`"2"`를 리터럴로 들게 된다. 맞는 지적이라 고쳤다. 버전 집합 `TraceSchemaVersion`을 `core`가
소유하고 어댑터가 헤더에 그것을 쓴다. 버전이 뜻하는 것은 이벤트의 내용이지 파일이 아니기
때문이다. 쓰는 값 `TRACE_SCHEMA_VERSION = "2"`는 어댑터에 남는다. 그것은 "지금 무엇을 쓰나"이고
어댑터의 일이다.

남긴 것 넷, 전부 Nit이고 이유가 있다.

- 어댑터 테스트에서 `assert trace is not None`이 여섯 번 반복된다. 헬퍼로 빼면 포트 호출이
  헬퍼 뒤로 숨어 각 테스트가 무엇을 미는지 덜 보인다. CLI 테스트의 `_read`는 파일 경로에서
  출발해 어댑터를 지어야 해서 헬퍼가 값을 한다.
- `read()`가 빈 파일에서 `IndexError`, 깨진 헤더에서 `ValidationError`로 실패 형태가 둘이다.
  옮기기 전부터 있던 동작이고 명세 밖이다. 트레이스 조회를 노출하는 `admin-api`가 실패 형태를
  정할 때 같이 본다.
- `tests.md`의 예시 `trace: TraceStore = FakeTrace()`와 실제 픽스처(`def trace() -> FakeTrace`)의
  모양이 다르다. 적합성은 `_run(trace: TraceStore)` 호출 지점이 검사하므로 실질 위반은 아니고
  기존 상태다.
- `CONTEXT.md`에 `TraceStore`·`UnknownEvent` 항목이 없다. 포트 이름은 ADR 0009가 정했고 용어집은
  domain-modeling 스킬이 쓴다.

## 검사

`pytest` 145 passed, `ruff` check·format 통과, `pyright` 49파일 0 errors(`filesAnalyzed`로 먼저
확인), `lint-imports` 3 kept. 파이썬만 바뀌었고 LLM 호출 경로는 건드리지 않아 `-m llm`은 돌리지
않았다.

## 회고

이번 티켓은 앞 일지가 예고한 대로 갔다. 01의 "다음"이 "버전 1 읽기는 이미 성립하므로 02는
확인만 하면 된다"고 적어 둔 것이 그대로 맞았고, 읽는 데 든 시간이 짓는 데 든 시간보다 길었다.
프리팩터 티켓은 그래야 한다.

린트를 red 확인 직후에 돌렸다(01 회고의 반영). 이번 red는 ImportError 하나로 폭이 예상과
같았고, 린트가 잡은 것은 한국어 docstring의 표시 폭(E501, 한글 한 글자가 2)뿐이었다. 세 번
줄였다. 첫 줄 docstring을 쓸 때 한글은 50자 안이라고 세면 한 번에 끝난다.

규칙 후보는 없다. 새로 겪은 실수가 없다.

## 다음

- 커밋 뒤 PR 직전 CodeRabbit CLI(`coderabbit-review`), `/git-pr`, `@coderabbitai review`,
  `/git-pr-feedback`, `/git-pr-merge`. 병합은 이 세션이 한다.
- 다음 티켓은 03(게이트에서 멈춘다). 새 세션에서 시작한다. 마스킹 체크박스는 01이 닫았고,
  03은 일시정지 이벤트의 인자에도 같은 마스킹이 걸리는지와 `secret_args`의 실재 검사(ADR 0009
  이력)를 도구 연결 직후 검사 자리에 넣는다.
- 04가 이어받는 것: `TraceStore.read`는 부재를 `None`으로 돌려주고, `Trace.schema_version`은
  `TraceSchemaVersion`이라 `== "1"` 비교에서 pyright가 좁힌다. 버전 1 거부와 "일시정지가 아닌
  실행" 거부는 둘 다 04의 재개 진입점이 `PluginError`로 낸다.
- 워크트리 `.claude/worktrees/`의 옛 둘은 여전히 사람이 지운다.
