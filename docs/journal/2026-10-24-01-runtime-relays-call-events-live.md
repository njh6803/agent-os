# 2026-10-24 (01) 런타임이 호출 이벤트를 실행 도중에 흘린다 (web-widget 02)

인계로 넘긴 세션(`셀프 리뷰 직전`)이 쓰기 시작했다. 이어 받는 세션이 같은 파일을 이어 쓰고 커밋한다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/web-widget/issues/02-runtime-relays-call-events-live.md

(지시문 본문: 다음 작업 = 실행 도중 모델·도구 호출 이벤트를 소비자에게 바로 중계해 최종 사용자 스트림의 `calling`·도구 항목이 결말 전에 오게 한다. 브랜치 feature/02-runtime-relays-call-events-live, 모델 Opus 5.5 / medium(레벨 스윕의 갈래), 이번 요청 범위 PR과 병합까지. 이어받을 상태: PR #375 claude-review 둘째 회차의 Nit(`http/errors.py`의 `limit` 불변식)은 보류, 원격 브랜치 docs/web-widget-spec-2는 사람이 확인하기 전에 지우지 않는다.)

## 결정

- ADR 0039대로 `_Body._relay`가 anyio 태스크 그룹을 열고 에이전트를 자식 태스크(`_AgentTask`)에서 돌린다. 컨텍스트는 이벤트를 기록하는 자리 다섯(모델 호출 직전·기록 뒤, 도구 호출 직전·기록 뒤, 거부 뒤)과 에이전트 이벤트 큐잉에서 `release()`로 맞물린다. 신호는 크기 0의 메모리 흐름으로 건너는 `anyio.Event`이고 이벤트는 `_pending`에 남는다.
- 에이전트 태스크의 취소 아닌 예외는 객체 그대로 보관해 그룹 밖에서 다시 던진다(`_Thrown`의 동일성 판정 유지, anyio 4.15.1의 ExceptionGroup 감싸기 회피). 출력 인자 금지(CODING_STANDARDS) 때문에 `_Outcome` 대신 자기 상태를 가진 `_AgentTask`를 두었다.
- 소비자가 `run()`을 aclose하면 안쪽 제너레이터가 태스크 그룹의 범위 안에 멈춰 남아 "Attempted to exit a cancel scope that isn't the current tasks's current cancel scope"가 났다. `run()`·`resume()`·`events()`가 안쪽 제너레이터를 `aclosing`으로 닫게 했다.
- `BaseAgent.run` 독스트링에 플러그인 작성자가 알 것 셋(정리 코드가 도는 태스크, contextvars가 부른 쪽에 보이지 않음, 버려진 실행의 취소)을 적었다. sdk 파일이지만 동작 문서이고 시그니처는 그대로다.

## 번복하거나 고친 것

- 처음 쓴 "소비자가 닫는" 시험은 옛 core에서 기한 경로로 엉뚱하게 빨갰다. `assert not deadline.cancel_called`를 더해 재려는 상황을 단언했다.
- 시험 `..._정리_코드는_같은_태스크에서_돈다`를 `..._에이전트를_돌린_태스크에서_돈다`로 바꾸고 단언을 `closed_in is ran_in`으로 바꿨다. `.claude/rules/core.md`의 같은 문장도 고쳤다.

## TDD와 변이

- 새 시험: `tests/core/test_run.py` 끝 "실시간 중계" 절 넷, `tests/channel/http/test_router.py`의 프레임 순서 하나, `tests/channel/http/test_end_user.py`의 `calling` 항목 순서 하나.
- 변이 `.scratch/web-widget/probes/relay_mutations.toml` "도구 호출을 하나씩 들인다": 빨강, 표지 `AssertionError: ['run_started', 'tool_called', 'tool_called', 'run_failed']`가 맞았다.
- 기존 변이 "에이전트의 제너레이터를 닫지 않는다"(`.scratch/end-user-continuation/probes/contract_mutations.toml`)는 여전히 빨강이고 표지도 맞았다.

## 검사(인계 시점)

- core·channel·adapters 시험 673개 통과(`-n 4`).
- `tools/run_checks.py`와 `pytest -m llm`은 백그라운드로 돌다가 인계하며 멈췄다. 멈추기 전까지 본 러너 줄은 모두 Passed였다. 이어 받는 세션이 셀프 리뷰 반영 뒤 다시 친다.
- sibling_overlap: 카나리아 명세를 고치지 않고 바꾼 하네스 파일 둘(`.claude/rules/channel.md`, `.claude/rules/core.md`)을 알렸다. 커밋 전에 `tools/canary.py`로 그 명세들을 돌려 `# 최신 결과:` 줄을 고쳐야 한다. `.scratch/web-widget/probes/README.md`는 PR #376과 글자 충돌 후보다.
- probes/README.md의 relay_mutations 행이 가리키는 일지 이름은 아직 `2026-10-23-50-…`이다. 이 파일(`2026-10-24-01-runtime-relays-call-events-live.md`)로 고쳐야 한다.

## 세션 제목

- 넘긴 세션: feature/02-runtime-relays-call-events-live → `feature/02-runtime-relays-call-events-live (인계함)`
- 이어 받은 세션: `feature/02-runtime-relays-call-events-live`

## 이어 받은 세션

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/web-widget/issues/02-runtime-relays-call-events-live.md

(지시문은 위 인계 지시문과 같다. 워크트리 `.claude/worktrees/02-runtime-relays-call-events-live` 에 EnterWorktree(path)로 들어갔다.)

### 셀프 리뷰(/code-review, base 96d3e1df, 파일 8개, 커밋 0개, 미추적 2개)

표준 축(sonnet·high)과 명세 축 모두 Critical·Major는 없었다.

- 표준: Minor 넷(probes/README의 없는 일지 경로, sdk 독스트링의 두 주장을 시험이 밟지 않음, `_relay` 의 `except` 안에 쌓인 갈래, `release()` 가 `bind()` 없이 조용히 돌아감), Nit 넷(`run.py` 모듈 독스트링의 범위 문장이 태스크 그룹을 들지 않음, `_feed` 독스트링의 "그 자리에서 흘렸다", 초인종 비유와 다른 동사 계열이 섞인 이름, `run()`·`resume()` 의 같은 `aclosing` hunk).
- 명세: Minor 넷(서버 시험 둘이 옛 core에서 빨갰다는 기록이 일지에 없음, 계약 변이가 `-x` 라 세 사례 가운데 첫째만 보임, `channel/http/runs.py` 의 "실행 하나가 통째로 한 태스크에서 돌므로", probes/README 경로), Nit 둘(`test_end_user.py` 머리의 "둘째 구동자는 스트림의 수명에만 쓴다", 명세 21행의 "지금 core는 … 모은다"). 명세 축이 기준 커밋 사본에 새 시험만 넣고 돌린 결과는 5 failed, 1 passed였다. 서버 층 시험 둘은 TimeoutError로, core 새 시험 셋도 빨갰고, gather 악수 시험만 원래부터 초록인 가드라 초록이었다.

고친 것.
- probes/README 의 relay_mutations 행이 이 일지(`2026-10-24-01-…`)를 가리키게 했다. `2026-10-23-50` 은 main에서 PR #376의 일지가 가져갔다.
- `channel/http/runs.py` 독스트링: "에이전트와 그 호출은 core 의 몸통이 연 자식 태스크에서 돌지만(ADR 0039) 도구 연결은 몸통이 실행의 태스크 안에서 열고 닫으므로, MCP 어댑터의 anyio 취소 범위가 진입과 종료를 같은 태스크에서 본다." 근거는 `core/run.py` 의 `_connected` 가 `self._tools.connect` 를 몸통에서 열고 `_relay` 가 그 안에서 태스크 그룹을 여는 것이다.
- `core/run.py` 모듈 독스트링: "범위와 몸통이 에이전트를 돌리는 태스크 그룹(ADR 0039)이 yield 를 건너므로 부르는 쪽은 이벤트 사이에 await 하지 않는다." `core.md` 의 같은 문장과 맞췄다.
- `_feed` 독스트링: "에이전트가 낸 이벤트를 줄에 세우고 몸통을 깨운다. 호출 안의 이벤트는 컨텍스트가 기록하는 자리에서 같은 줄에 세우고 깨웠다."
- `tests/channel/http/test_end_user.py` 머리: 둘째 구동자는 "스트림을 읽는 도중에 오는 것을 볼 때 쓴다 — 도는 실행에 구독이 붙는 것, 토큰이 만료돼도 열린 스트림이 끊기지 않는 것, 결말 전에 오는 프레임."
- sdk `BaseAgent.run` 독스트링의 "정리 코드 안의 await도 취소된다"를 시험이 밟게 했다. `AbandonedAgent` 의 `finally` 가 `anyio.sleep_forever()` 를 기다리고 취소를 받으면 `cleanup_cancelled` 를 세우며, 소비자가 닫는 시험이 그것을 단언한다. 취소가 들어가지 않으면 그 await가 끝나지 않아 시험의 `fail_after(PACED)` 가 빨개진다.
- 계약 변이 "에이전트의 제너레이터를 닫지 않는다"를 사례 셋에 하나씩 돌렸다(스크래치 표, `tools/mutate.py`). 셋 다 빨갰다. "지어낸 실패"·"지어낸 요약"은 표지 `where False = <tests.core.test_run.ClosingAgent object at` 가 맞았고, "삼킨 일시정지"는 `assert agent.closed_in is agent.ran_in` 이 `Task-2`(가비지 수집이 다른 태스크에서 닫음)와 `_AgentTask.run` 태스크를 견주며 빨갰다. 변이가 겨누는 성질 그대로라 커밋된 표(`-x` 로 첫 사례만 보며 표지가 맞는다)는 고치지 않았다.

남긴 것과 이유.
- 표준 2의 둘째 주장(트레이스를 쓰지 못하면 에이전트가 기다리던 자리에 취소가 들어온다)은 고치지 않았다. 리뷰어는 `_record_model_call` 에서 쓰기가 실패한다고 읽었지만, 그 함수는 `_pending` 에 쌓기만 하고 쓰기는 몸통 바깥(`_Body` 의 `self._trace.write`)에서 한다. 그래서 쓰기 실패는 몸통의 예외이고 에이전트에는 취소로 들어간다. 독스트링이 맞다.
- 표준 3(`except` 안의 갈래)은 고치지 않았다. 남은 몸통은 취소를 다시 던지는 한 줄, 그룹 취소, 실패 보관 셋이고 그룹 밖에서 다시 던지는 순서가 이 셋에 기댄다. 함수로 빼면 그룹 범위를 넘겨야 해 읽기가 나아지지 않는다고 판단했다.
- 표준 4(`bind()` 없는 `release()`)는 고치지 않았다. `_Context` 는 core 안의 것이고 만드는 자리(`_attend` 의 `_Context(`)와 `bind` 를 부르는 자리(`_relay`)가 하나씩이다. `release()` 를 부르는 자리 여섯(컨텍스트의 다섯, `_feed` 하나)은 모두 에이전트 태스크 안이고, 그 태스크는 `_relay` 가 `bind` 를 부른 뒤에만 띄운다. 그래서 지금의 코드에서 `_bell` 이 없는 갈래는 지나지 않는다. 판단 사항으로 남긴다.
- 표준 7(이름의 비유)·8(같은 `aclosing` hunk), 명세 6(명세 21행)은 고치지 않았다. 7은 판단 사항이고, 8은 이번 변경 전부터 있던 두 진입점의 중복이며, 6은 명세가 동기를 적은 기록이다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장): 위 "고친 것"의 `runs.py`·`run.py`·`_feed`·`test_end_user.py` 문장 넷.

## 인계 지시문

```
다음 작업: .scratch/web-widget/issues/02-runtime-relays-call-events-live.md. 실행 도중에 모델·도구 호출 이벤트를 소비자에게 바로 중계해 최종 사용자 스트림의 calling 항목과 도구 항목이 결말 전에 오게 한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/02-runtime-relays-call-events-live.md
브랜치: feature/02-runtime-relays-call-events-live
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-01-runtime-relays-call-events-live.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, origin/main 기준, 미추적 relay_mutations.toml 포함)부터 한다. 그 뒤 티켓 done 처리, 일지의 probes/README 경로 고침, 카나리아 명세 갱신, 검사, 커밋, PR, 병합. 일지 docs/journal/2026-10-24-01-runtime-relays-call-events-live.md. PR #375 claude-review 둘째 회차의 Nit(src/agent_os/http/errors.py의 limit 불변식)은 보류했고 이유는 PR #375 코멘트에 있다. 원격 브랜치 docs/web-widget-spec-2는 사람이 확인하기 전에는 지우지 않는다
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-23T15:28:28Z
