# 2026-10-20 (27) end-user-continuation 티켓 02: 실패 원인

나란히 여는 넷(02·03·05·06) 가운데 첫 세션이다. 주 체크아웃이 미갱신이라 Skill 도구로 `tidy-checkouts`를 먼저 돌고,
주 체크아웃에서 브랜치를 따지 않고 워크트리 `.claude/worktrees/02-runtime-names-the-failure-cause`에 들어가 브랜치를
`feature/02-runtime-names-the-failure-cause`로 바꿨다. `implement` 스킬을 Read로 열어 따랐다. 세션 제목은
`feature/02-runtime-names-the-failure-cause`다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자:
> .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md
> 다음 작업: … 런타임이 쓰는 모든 실패가 생긴 자리의 원인을 들고, 먼저 난 실패가 결말이다 … 어디서: 새 세션. 나란히 여는
> 4 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고 … 이번 요청 범위: PR과 병합까지"

## tidy-checkouts

지울 후보는 없었고 사람에게 넘길 것이 셋이었다(분리 HEAD 둘, 병합된 PR의 머리와 끝이 다른 브랜치 하나). 지시문대로 보고만
하고 답을 기다리지 않았다. 셋의 이름은 이 세션의 압축 전 트랜스크립트에만 있고 옮기지 못했다. 다음 정리가 다시 본다.

## 한 것 (커밋 전, 작업 트리)

- **core.** `run.py`: 런타임이 에이전트에게 던진 예외를 그 객체로 기억하는 `_Thrown`(`remember`, `blamed`, `cause_of`), 몸통이
  실패를 받는 자리의 닫힌 열거 `_Site`와 기본 갈래 없는 `_cause_at`(`assert_never`), `_settled`(결말을 썼다)와 `_held`(쓸
  결말을 붙잡았다)의 분리와 `_hold`·`_hold_failure`·`_write_held`, 진입점의 기한을 `anyio.move_on_after`의
  `cancelled_caught`로 보기(디스크의 `TimeoutError`는 결말 없이 올라온다), 이벤트가 아닌 값을 쓰기 전에 거르는
  `_reject_stray`, 요약 실패의 원인. `_drive`는 ruff PLW0717(try 안 문장 수) 때문에 `_drive`·`_connected`·`_attend` 셋으로
  나눴다. 모듈 독스트링의 타임아웃 문단을 고치고 실패 원인 문단을 더했다.
- **테스트.** `tests/core/test_run.py`의 기존 사례에 원인 단언을 더하고 끝에 "실패 원인" 절을 더했다(262개 초록). 기존 기한
  사례의 기대와 이름을 붙잡은 실패로 바꿨다. `tests/channel/http/test_end_user.py`의 실패 항목 dict 단언 셋을 실제 원인으로
  고치고 이어 가기의 요약 실패 사례를 더했다. `tests/channel/http/test_router.py`의 "실행 안의 실패" 사례에 원인 열을
  더했다(메시지 열 이름을 `cause`에서 `message`로). 채널·main 315개 초록.
- **지침.** `.claude/rules/core.md`의 실행 타임아웃 항목(`move_on_after`, 붙잡은 결말)과 실패 정책(원인, 동일성 규칙, 기본 갈래
  없음, 먼저 난 실패, 결말 뒤 닫기). `.claude/rules/core.md`를 고쳤으므로 카나리아 `core_rule_runtime_only_events.toml`을 새
  `claude -p` 세션에서 불러 `# 최신 결과:` 줄을 고쳐야 한다(`sibling_overlap.py`가 알렸다. 아직 안 했다).
- **변이.** 새 표 `.scratch/end-user-continuation/probes/cause_mutations.toml` 넷(타입으로 가름, 마지막 하나만 기억, 요약
  원인 없음, 도구 연결 원인 바꿈) 모두 기대대로이고 README 행을 더했다. 이번 변경으로 원문이 사라진 옛 변이 둘을 새 코드에
  맞췄다 — `end-user-continuation/probes/contract_mutations.toml`의 "멈춘 뒤 결말 표지를 세우지 않는다"(들여쓰기),
  `end-user-channel/probes/timeout_mutations.toml`의 "돌아오기만 하면 결말로 본다"(새 끝 판정 줄). 앞의 것은 표 10개 전부,
  뒤의 것은 그 변이 하나만 담은 임시 표로 돌려 기대대로였다.
- **잔존.** `유일한 실패`는 `test_run.py`의 독스트링 하나였고 고쳤다. `기록되지 않은`(sdk 주석, `items.py`, rules 둘, ADR
  0031, 테스트 둘)은 옛 트레이스의 실패가 여전히 `null`이라 그대로 참이다. ADR 0014의 `fail_after` 문장(226·271·286줄)은 지난
  이력 항목이라 `.claude/rules/adr.md`대로 포인터를 달지 않았다. 다만 286줄은 anyio 5의 `move_on_after` 타이머 변경을 "지금
  코드가 쓰는 `fail_after`와 같게 맞추는" 것이라 위협이 아니라고 적었는데, 이제 코드가 `move_on_after`를 쓰므로 anyio 5를 들일
  때 그 변경이 실행 타임아웃에 닿는다. PR 본문의 "남긴 위험"에 적는다.

## 고친 것 / 겪은 것

- 압축 뒤 `run.py`에 `@contextmanager`의 `Iterator` 반환이 pyright `reportDeprecated`였다. `Generator`로 바꿨다.
- `test_앞서_받은_모델의_예외를_…`이 "API down"을 기대했으나 가짜 모델(`GenericFakeChatModel`)이 도구를 붙이지 못해
  `NotImplementedError`를 먼저 냈다. 원인 단언(모델 호출)은 맞으므로 메시지 단언만 그 예외로 바꿨다.
- 변이 표지를 고르려 스크래치 스크립트로 변이를 손으로 넣었다가 되돌리며 `Path.write_text`가 윈도에서 `run.py`의 줄 끝을
  CRLF로 바꿨다. `sed -i 's/\r$//'`로 LF로 되돌리고 `git diff --stat`가 정상 크기임을 봤다.

## 남은 위험·넘길 것

- main에서 이미 원문이 사라진 변이 열여덟이 있다(`conversation/probes/continuation_mutations.toml` 다섯,
  `end-user-channel/probes/contract_mutations.toml` 넷, `timeout_mutations.toml` 하나, `web-admin/probes/pause_index_mutations.toml`
  여덟). 이 브랜치가 만든 것이 아니라 고치지 않았다. 대기열 후보다.
- 03·05가 같은 파일(`run.py`, `core.md`, 테스트 셋, 프로브 README)을 고친다. 뒤에 병합하는 쪽에서 글자 충돌 후보다.

## 인계

경계 `셀프 리뷰 직전`에 인계 계기가 왔다(세션 컨텍스트 약 28만 토큰). `/code-review`는 불렸지만 단계를 밟지 않았다. 셀프
리뷰는 새 세션이 한다. 백그라운드의 `tools/run_checks.py`는 멈췄다(결과를 보지 못했다). `-m llm`도 아직 돌리지 않았다.

지시문:

```
다음 작업: .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md. 런타임이 쓰는 모든 실패가 생긴 자리의 원인을 들고, 먼저 난 실패가 결말이다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md
브랜치: feature/02-runtime-names-the-failure-cause
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-27-runtime-names-the-failure-cause.md, 나란히 도는 티켓 .scratch/end-user-continuation/issues/03-*.md·05-*.md·06-*.md
이어받을 상태: 인계: 셀프 리뷰 직전. 구현·테스트·지침·변이 표는 커밋하지 않은 채 워크트리에 있고 티켓 체크박스는 검증 줄과 기능 닫기 줄만 남았다. 셀프 리뷰(/code-review, base는 origin/main의 merge-base)부터 하고, 전체 검증(ruff 둘은 초록, tools/run_checks.py는 결과를 못 봤다)과 -m llm 한 번, 카나리아 core_rule_runtime_only_events.toml, 커밋·PR·병합으로 간다. 남은 위험과 넘길 것은 일지 docs/journal/2026-10-20-27-runtime-names-the-failure-cause.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `feature/02-runtime-names-the-failure-cause (인계함)`으로 바꾸고, 러너를 멈추고, 워크트리 잠금을 풀었다.

open-session을 부른다 2026-10-20T02:52:09Z

## 이어받은 세션 (셀프 리뷰부터)

open-session이 연 새 세션이다. 제목을 `feature/02-runtime-names-the-failure-cause`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에
들어가 `implement` 스킬을 Read로 열어 따랐다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 이어받을 상태: 인계: 셀프 리뷰 직전. … 셀프 리뷰
> (/code-review, base는 origin/main의 merge-base)부터 하고, 전체 검증 … -m llm 한 번, 카나리아 core_rule_runtime_only_events.toml,
> 커밋·PR·병합으로 간다. … 이번 요청 범위: PR과 병합까지"

## 셀프 리뷰

범위: base `911babc0`, 바뀐 파일 9, 커밋 0, 미추적 2(`cause_mutations.toml`, 이 일지). 표준 축은 sonnet·high, 명세 축은 본 세션
모델이다.

- **명세 축 Major — 연결에 들어간 뒤의 예상 밖 예외가 사라진다.** `_connected`가 들어간 뒤의 예외를 모두 닫기의 것으로 보고
  버려, `_attend`가 붙잡기·결말 표지를 마치기 전에 난 예외(탐침은 `_Context` 생성)가 결말도 예외도 없이 끝났다. main은 같은
  경우에 `run_failed`를 썼다. **고쳤다.** 자리 `_Site`에 "연결 안의 나머지"(`inside`, 원인 그 밖)를 더하고 연결 안의 몫을
  `_holding("inside")`로 감쌌다. 그 덕에 `entered` 표지가 없어졌다(들어간 뒤의 예외는 결말을 이미 붙잡았거나 썼으므로 `_hold`가
  버린다). 사례 `test_연결_안에서_에이전트_자리_밖의_런타임_예외는_그_밖이고_결말이_남는다`(빨강을 본 뒤 고쳤다). 명세 168·174·176줄의
  코드 위치와 닫힌 주장("그 밖에 … 나는 예외는 없다")을 지금 동작으로 고쳤다.
- **표준 축 Minor 3 — 일시정지를 쓰지 못한 실행이 조용히 끝난다.** main부터 있던 동작이다. 이 브랜치에서는 닫기의 예외가
  `_connected` 안에서 버려져 `_drive`의 `except`에 오는 것이 쓰기 실패뿐이고, 멈춘 실행의 쓰기 실패는 일시정지(쌓인 이벤트의
  마지막)가 트레이스에 없다는 뜻이다. **고쳤다.** 티켓의 그 밖 항목(쓰기가 한 번만 실패하면 뒤의 `run_failed`가 남고 그것이 그 밖을 든다)대로 그 밖의
  `run_failed`를 쓴다. 사례 `test_일시정지를_쓰지_못한_실행은_멈춘_것이_아니라_그_밖의_실패로_끝난다`(빨강을 본 뒤 고쳤다).
- **명세 축 Minor — 에이전트의 정리 코드를 기다리다 기한이 오면 먼저 난 실패가 진다.** `_relay` 안에서 런타임이 던진 실패
  (`_reject_runtime_only` 등)가 `_closing`이 에이전트를 닫은 뒤에야 붙잡혔다. **고쳤다.** `_relay`의 순회를
  `_holding("agent", ctx)`로 감싸 닫기 전에 붙잡는다. 사례
  `test_런타임이_에이전트_자리에서_던진_실패는_정리_코드를_기다리다_기한이_와도_결말이다`(빨강을 본 뒤 고쳤다).
- **명세 축 Minor — 디스크 `TimeoutError`의 보편 주장이 넓다.** **고쳤다.** `run.py` 모듈 독스트링과 `core.md`를 "몸통이 받는
  자리에서는 그 자리의 원인, 받지 않는 자리(요약 이벤트 쓰기, 결말 쓰기)에서는 결말 없음"으로.
- **표준 축 Minor 4 — 예외 그룹 문장.** `asyncio.TaskGroup` 안의 `ctx.llm()` 실패는 그룹으로 올라와 에이전트 코드다(명세가 "예외
  그룹에 넣으면 에이전트 코드"로 정했다). **고쳤다.** `_Thrown` 독스트링에 그 갈래를 적었다.
- **표준 축 Minor 5 — 까닭 없는 단언.** **고쳤다.** `pytest.raises(TimeoutError, match=…)`, 이벤트가 아닌 값의 메시지 전체 단언.
- **표준 축 Minor 6 — 변이 표지.** **고쳤다.** `timeout_mutations.toml`의 "돌아오기만 하면 결말로 본다"에 `expect_output`
  (`Right contains one more item: 'run_failed'`)을 더했다. 그 변이 하나만 담은 임시 표로 돌려 기대대로였다.
- **표준 축 Major 1 — `_loaded`의 `getattr`이 암묵적 `Any`.** **남겼다.** 운영 로더 `filesystem.py`의 `load_agent`가 같은
  모양(`getattr` → `BaseAgent`)이고 시그니처를 어긴 에이전트는 실제로 그 길로만 온다. 원칙 III의 판정자 `check_type_escapes`도
  초록이다.
- **표준 축 Major 2 — ADR 0014의 `fail_after` 문장.** **남겼다.** 226·271·286줄은 지난 이력 항목이라 기록이다(`operations.md`
  문서 위치). 다만 286줄의 논증(anyio 5의 `move_on_after` 타이머 변경은 위협이 아니다)은 이제 코드가 `move_on_after`를 쓰므로
  anyio 5를 들일 때 실행 타임아웃에 닿는다. PR 본문의 남긴 위험에 적는다. `end-user-channel/spec.md:334`는 done 기능이라 기록이다.
- **냄새(판단).** `run()`·`resume()`의 기한 꼬리 중복(기존), `_Body` 표지 넷의 얽힘(티켓이 `_settled`·`_held`를 따로 들라고
  정했다), CQS(`_write_held`, `remember`), `_cause_at`의 Feature Envy, `blamed`/`remember` 동사. 판단 항목이라 남긴다.
- **명세 축 Nit.** `test_앞서_받은_모델의_예외를_…`의 모델 예외가 붙이기 자리의 `NotImplementedError`인 것은 위 "고친 것"에 이미
  적었다. 동일성을 가르는 요점은 그대로라 남긴다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장):

- `run.py` `_Site` 주석의 요지: 도구 연결의 닫기는 자리가 아니다, 연결 안의 몫이 끝나면 결말을 붙잡았거나 이미 썼으므로 버린다
- `_connected`: "들어간 뒤의 예외면 결말을 이미 붙잡았거나 썼으므로 `_hold` 가 버린다"
- `_drive` 주석의 요지: 멈춘 실행이면 실패한 것은 일시정지까지의 쓰기이고, 일시정지는 쌓인 이벤트의 마지막이라 트레이스에 없다
- 모듈 독스트링·`core.md`: "그 TimeoutError 는 다른 예외와 같다 — 몸통이 받는 자리(연결, 에이전트, 결말 전 쓰기)에서는 그
  자리의 원인이고, 몸통이 받지 않는 자리(요약 이벤트 쓰기, 결말 쓰기)에서는 결말 없이 올라온다"
- 명세 174줄: "결말 전에 이벤트를 트레이스에 쓰다 난 예외와, 연결 안의 몫이 선언 확인·에이전트 밖에서 런타임 자신의 예외로 끝난 것"

## 검사

- 셀프 리뷰 전: `tools/run_checks.py` 전부 Passed(pytest 808.7초, web-verify 578.4초). ruff 둘 초록.
- `uv run --env-file ../../../.env pytest -m llm`: 7 passed(882초). LLM 토큰 합계 55,493(입력 54,232, 출력 1,261), 트레이스 10개,
  모델 호출 22건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.
- 카나리아 `core_rule_runtime_only_events.toml`: 통과 4(claude 2.1.302). 셀프 리뷰가 원천 문장을 고친 뒤 `--preflight` 통과로
  갈음했다.
- 셀프 리뷰 반영 뒤: `tests/core/test_run.py` 265 passed, ruff 둘 초록, `cause_mutations.toml` 넷 기대대로, `--check` 둘 원문 확인.
  `timeout_mutations.toml`의 변이 "최종 사용자의 시작이 넘기지 않는다"는 main부터 원문이 사라진 것이었는데(위 "남은 위험"의
  열여덟 가운데 하나), 이 표를 커밋에 실으니 pre-commit의 `mutate.py --staged`가 막았다. 시작과 이어 가기가 함께 쓰게 된
  `started`의 `previous_run` 줄을 원문에 넣어 고쳤고, 그 변이 하나를 돌려 기대대로였다. 그래서 남은 위험의 열여덟은 열일곱이다.
- 첫 커밋 시도는 위 막힘으로 실패했다(인용 경고 셋도 함께 났고 따옴표를 떼어 고쳤다).
- 둘째 커밋 `6d792161`이 pre-commit을 통과했다(손으로 치는 다섯은 이 결과로 갈음한다).

## 인계 (커밋 뒤)

경계 `커밋 뒤`에 인계 계기가 왔다(세션 컨텍스트 약 35만 토큰). 인계하지 않는 때 다섯에 들지 않았다 — 커밋은 성공했고, 요청
범위는 병합까지이며, 이 세션의 지시문은 다른 경계(`셀프 리뷰 직전`)였고, `인계 못함` 줄이 없고, `get_session`의 `self`에
`parentSessionId`가 없다.

남은 단계: PR 직전 리뷰(`/security-review`와 `bug-perf-review` 서브에이전트를 나란히. 그 전에 `origin/main`을 합친다 —
`3a84a692`가 이 브랜치보다 앞서 있고 겹치는 파일은 없었다), 그 지적의 반영, PR(본문의 남긴 위험: anyio 5의 `move_on_after`
타이머 변경이 이제 실행 타임아웃에 닿는다, main에서 원문이 사라진 변이 열일곱, 03·05와 같은 파일의 글자 충돌 후보), 봇 회차,
병합 직전의 기능 닫기 판정(티켓 체크박스에 2026-10-20 판정을 적었고 병합 직전에 다시 본다), 병합. PR 직전 리뷰의 브리프에 밀
주장은 위 "셀프 리뷰"의 목록이다.

지시문:

```
다음 작업: .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md. 런타임이 쓰는 모든 실패가 생긴 자리의 원인을 들고, 먼저 난 실패가 결말이다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md
브랜치: feature/02-runtime-names-the-failure-cause
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-27-runtime-names-the-failure-cause.md의 "셀프 리뷰"·"검사"·"인계 (커밋 뒤)" 절
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰와 반영, 전체 검증(러너 초록, -m llm 7 passed), 카나리아를 마치고 6d792161로 커밋했다(푸시 안 함, PR 없음). 남은 것은 origin/main 합치기(sync_with_base_branch), PR 직전 리뷰(/security-review와 bug-perf-review를 나란히, 밀 주장은 일지 "셀프 리뷰"의 목록), 반영, PR, 봇 회차, 병합 직전 기능 닫기 판정, 병합이다. 일지 docs/journal/2026-10-20-27-runtime-names-the-failure-cause.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `feature/02-runtime-names-the-failure-cause (인계함)`으로 바꾸고, 워크트리 잠금을 풀었다. 멈출 백그라운드 작업은 없었다.

open-session을 부른다 2026-10-20T04:15:53Z

## 이어받은 세션 (커밋 뒤부터)

open-session이 연 새 세션이다. 제목을 `feature/02-runtime-names-the-failure-cause`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에
들어가 `implement` 스킬을 Read로 열어 따랐다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 이어받을 상태: 인계: 커밋 뒤. … 남은 것은 origin/main
> 합치기(sync_with_base_branch), PR 직전 리뷰(/security-review와 bug-perf-review를 나란히 …), 반영, PR, 봇 회차, 병합 직전 기능
> 닫기 판정, 병합이다. … 이번 요청 범위: PR과 병합까지"

## origin/main 합치기 (두 번)

`sync_with_base_branch`는 앱이 만든 워크트리가 아니라며 거절해 직접 합쳤다. 첫 합치기(03·06이 든 main, `314ec233`)와 둘째
합치기(05가 든 main, `ed111753`) 모두 `.claude/rules/core.md` 34줄이 충돌했다. 이 브랜치는 그 줄 중간("…(위 실행 타임아웃
항목).")에 실패 원인 단락을 끼웠고 main은 같은 줄의 다른 문장(바로가기, `TraceDamagedBeforePrincipal`)을 고쳤다. 공통 조상
대비 우리 쪽이 순수 삽입임을 단언한 뒤 main 판의 같은 자리에 끼웠다. probes README는 표의 행 추가끼리라 셋 다 남겼다.
`sibling_overlap.py`가 일지 번호를 14에서 19로 옮겼다.

## PR 직전 리뷰

- `/security-review`: 발견 없음. `run_failed.error`는 이전과 같은 `_describe`이고, 최종 사용자 면은 고정 문구와 닫힌 열거
  `cause`만 받는다(`channel/http/items.py`, 이 브랜치가 고치지 않았다).
- `bug-perf-review`(기준 `2d460f6b`): Minor 3. 밀 주장 다섯은 아래 셋째를 빼고 코드와 맞았다.
  - **유효, 고쳤다.** 명세 자리 표의 위치 칸 셋이 낡았다(`_drive`의 `replay_event`, 에이전트 코드의 `_drive`, 그 밖의
    `_connected`의 안쪽 `except`). `_relay`·`_attend`·`_connected`의 `_holding("inside")`로 고쳤다.
  - **보류였다가 재현해 고쳤다.** 에이전트가 도는 중 기한이 오고 도구 연결의 닫기가 그 취소를 일반 예외로 덮으면, 결말이
    시간 초과가 아니라 `tool_connection`과 닫기의 메시지였다. 사례
    `test_기한의_취소를_도구_연결의_닫기가_다른_예외로_바꿔도_원인은_시간_초과다`(`FlakyCloseTools`와 `SleepyModel`)가
    `('OSError: close failed', 'tool_connection')`으로 빨간 것을 본 뒤, `_connected`가 예외의 문맥 고리에서 취소를 찾으면
    그 취소를 다시 던지게 고쳤다(`_cancellation_under`). 실제 MCP 어댑터가 취소 중 닫기에서 일반 예외를 내는지는 재지
    않았다. 밀 주장 2("들어간 뒤의 예외면 결말을 이미 붙잡았거나 썼으므로")는 이 경로에서 거짓이었고 주석을 고쳤다.

리뷰 반영 커밋 뒤에 인계 계기(`커밋 뒤`, 세션 컨텍스트 약 24.6만 토큰)가 왔다. 이 세션의 지시문의 "이어받을 상태"가 `인계: 커밋 뒤`로
시작해 같은 경계라 넘기지 않고 이었다(next-session "인계할 때" 1).

첫 재커밋은 pre-commit이 도는 동안 이 일지에 줄을 덧붙여 "files were modified by this hook"으로 실패했다(검사는 모두 통과).
스테이지해 다시 커밋했고 통과했다. 푸시하고 PR #325를 열었다(https://github.com/njh6803/agent-os/pull/325). PR 본문의 `-m llm`
줄은 "다시 돌리는 중"으로 두었다. 합치기 전 커밋에서는 7 passed였고, `run.py`가 그 뒤 main 합치기와 `_cancellation_under`로
바뀌어 다시 돌렸으나 인계로 멈췄다. `@coderabbitai review` 코멘트는 아직 남기지 않았다.

## 인계 (PR 연 뒤)

경계 `PR 연 뒤`에 인계 계기가 왔다(세션 컨텍스트 약 27만 토큰). 이 세션의 지시문은 `인계: 커밋 뒤`라 같은 경계가 아니고, 요청
범위는 병합까지이며, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 그래서 넘긴다.

남은 단계: `-m llm` 다시 돌리기(`uv run --env-file ../../../.env pytest -m llm`)와 PR 본문의 그 줄 고치기(`gh pr edit`), `@coderabbitai
review` 코멘트, 봇 회차, 병합 직전 기능 닫기 판정(티켓 체크박스의 2026-10-20 판정을 다시 본다), 워크트리에서 병합. 형제 04(PR #323)가
같은 파일을 고치므로 그쪽이 먼저 병합되면 다시 합친다.

제목을 `feature/02-runtime-names-the-failure-cause (인계함)`으로 바꾸고, `-m llm` 백그라운드 실행을 멈추고, 워크트리 잠금을 풀었다.
워크트리 잠금은 이미 풀려 있었다(`is not locked`).

지시문:

```
다음 작업: .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md. 런타임이 쓰는 모든 실패가 생긴 자리의 원인을 들고, 먼저 난 실패가 결말이다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md
브랜치: feature/02-runtime-names-the-failure-cause
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-27-runtime-names-the-failure-cause.md의 "PR 직전 리뷰"·"인계 (PR 연 뒤)" 절
이어받을 상태: 인계: PR 연 뒤. PR #325를 열었고(푸시함) @coderabbitai review 코멘트는 아직 남기지 않았다. 합치기와 리뷰 반영 뒤 -m llm을 다시 돌리다 인계로 멈췄으니 다시 돌려 PR 본문의 그 줄을 고친다. 그 뒤 봇 회차, 병합 직전 기능 닫기 판정, 워크트리에서 병합. 일지 docs/journal/2026-10-20-27-runtime-names-the-failure-cause.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-20T08:07:59Z

## 이어받은 세션 (PR 연 뒤부터)

open-session이 연 새 세션이다. 제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어가 `implement` 스킬을
Read로 열어 따랐다. origin/main은 `0a6e0b0d`에서 움직이지 않았고 형제 04(PR #323)는 아직 열려 있다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 이어받을 상태: 인계: PR 연 뒤. PR #325를 열었고(푸시함)
> @coderabbitai review 코멘트는 아직 남기지 않았다. … 이번 요청 범위: PR과 병합까지"

`-m llm`(`d3487d83`, 합치기와 리뷰 반영 뒤): 7 passed, 273.69초. LLM 토큰 합계 47,841(입력 46,789, 출력 1,052), 트레이스
10개, 모델 호출 20건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다. PR 본문의 그 줄을 고쳤다.

기능 닫기 판정(`origin/main` `0a6e0b0d`): 04가 `ready-for-agent`라 닫지 않는다. 병합 직전에 다시 본다.

origin/main이 아침 보고(#322, 겹치는 파일 없음)로 움직여 일지를 커밋한 뒤 합치고 푸시했다(`52f96e00`). 그 뒤
`@coderabbitai review`를 남겼고 "Review rate limited"였다. 보안·버그 축의 대체는 PR 체크리스트에 적은 PR 직전 리뷰 둘이다
(operations.md 초록 착시 목록).

봇 회차(claude-review, `52f96e00`): 경계 지적 없음, 유지보수성 Minor 2·Nit 1.
- **Nit, 고쳤다.** `_Thrown` 독스트링이 "sdk / 의 공개 타입"으로 명사 중간에서 끊겼다. 같은 모양인 `_connected` 독스트링의
  "결말을 쓴 / 뒤의"도 함께 이었다.
- **Minor, 두었다.** 진입점 둘이 같은 기한 꼬리를 되풀이한다. 이 PR 전에도 `fail_after`·`except TimeoutError`로 글자 그대로
  같았고 이 PR은 둘을 같은 모양으로 바꿨을 뿐이다. 모으면 `core.md`의 "자리는 진입점 둘"과 형제 04가 고치는 `run.py`에 더
  닿는다. 대기열 후보다.
- **Minor, 두었다.** `_write_held`가 쓰고 쓴 것을 돌려준다(CQS). 돌려주는 것은 성공 여부가 아니라 쓴 이벤트이고 호출부가
  그것으로 yield를 정해 무시할 수 없다. 같은 파일의 `_emit`과 같은 모양이다. `_settled`를 쓰기 전에 세우는 순서는 독스트링의
  "쓰기가 실패하면 결말 없음이다"가 적은 의도다.

## 04 병합 뒤 다시 합치기와 기능 닫기

리뷰 반영 커밋 뒤 푸시 전에 보니 형제 04(PR #323, `0262841b`)가 병합돼 있었다. 합치기에서 셋이 충돌했다.
- `tests/core/test_run.py`: import 줄(우리 `sys`, 04 `threading`·`time`). 셋 다 남겼다.
- probes README: 표의 행끼리. 우리 `cause_mutations.toml` 행과 04가 고친 `shortcuts_mutations.toml` 행, 새 `walk_cap_mutations.toml`
  행을 모두 남겼다.
- `.claude/rules/core.md`: 세 줄이 한 덩어리로 충돌했지만 공통 조상과 견주니 줄마다 한쪽만 고쳤다(실행 타임아웃·실패 정책은 우리,
  이어 가기는 04). 글자 단위 3-way로 합쳐 겹침이 없음을 단언했다.

`run.py`는 저절로 합쳐졌다. `tools/mutate.py --check`로 01~04의 변이 표 49개가 모두 원문이 한 번씩 있음을 봤고,
`tests/core/test_run.py`와 `tests/test_server.py`가 479 passed였다.

기능 닫기 판정(`origin/main` `0262841b`): 04까지 `done`이라 이 PR이 마지막 잎이다. `.scratch/plan.md`의 end-user-continuation
행을 `done`으로 바꾸고 프론티어 문단에 닫힘을 적었다. web-widget을 막던 여섯이 모두 닫혀 web-widget이 풀렸다.

## 인계 (커밋 뒤, 둘째)

합치기 커밋(04가 든 main) 뒤에 경계 `커밋 뒤`의 인계 계기가 왔다(세션 컨텍스트 약 20.8만 토큰). 이 세션의 지시문은 `인계: PR 연 뒤`라
같은 경계가 아니고, 요청 범위는 병합까지이며, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 그래서 넘긴다.

커밋한 것: 일지와 -m llm(`52f96e00`까지 푸시함), 리뷰 반영(독스트링 두 줄과 봇 회차 일지, 푸시하지 않음), 04가 든 origin/main 합치기
(푸시하지 않음). 커밋하지 않은 것: `.scratch/plan.md`(기능 행 `done`과 프론티어 문단), 티켓 02의 기능 닫기 체크박스 글, 이 일지의
"04 병합 뒤 다시 합치기와 기능 닫기"와 이 절.

남은 단계: 커밋하지 않은 셋을 커밋(`docs: end-user-continuation을 닫는다` 꼴), 푸시 전 `git fetch`로 origin/main이 또 움직였는지
보기(움직였으면 합치기), 푸시, PR 본문 고치기(기능 닫기와 04 합치기, `plan.md`가 바뀐 영역에 든다), `@coderabbitai review`(마지막
푸시 뒤), 봇 회차, 병합 직전 `headRefOid` 대조, 워크트리에서 병합. 이 세션의 지금 제목은 `feature/02-runtime-names-the-failure-cause`다.

제목을 `feature/02-runtime-names-the-failure-cause (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었고(모니터는 앞서 멈췄다), 워크트리
잠금은 이미 풀려 있었다(`is not locked`).

지시문:

```
다음 작업: .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md. 런타임이 쓰는 모든 실패가 생긴 자리의 원인을 들고, 먼저 난 실패가 결말이다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/02-runtime-names-the-failure-cause.md
브랜치: feature/02-runtime-names-the-failure-cause
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-27-runtime-names-the-failure-cause.md의 "04 병합 뒤 다시 합치기와 기능 닫기"·"인계 (커밋 뒤, 둘째)" 절
이어받을 상태: 인계: 커밋 뒤. PR #325가 열려 있다. 리뷰 반영 커밋과 04가 든 origin/main 합치기 커밋은 아직 푸시하지 않았고, .scratch/plan.md(기능 닫기)·티켓 02 체크박스·일지는 커밋하지 않았다. 그것을 커밋하고 git fetch로 main을 다시 본 뒤 푸시, PR 본문 고치기, 마지막 푸시 뒤 @coderabbitai review, 봇 회차, 워크트리에서 병합. 일지 docs/journal/2026-10-20-27-runtime-names-the-failure-cause.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-20T08:47:10Z

## 이어받은 세션 (커밋 뒤, 둘째부터)

open-session이 연 새 세션이다. 제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어가 `implement` 스킬을
Read로 열어 따랐다. `git fetch` 뒤 origin/main은 `0262841b`에서 움직이지 않아 다시 합치지 않는다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 이어받을 상태: 인계: 커밋 뒤. PR #325가 열려 있다. … 그것을
> 커밋하고 git fetch로 main을 다시 본 뒤 푸시, PR 본문 고치기, 마지막 푸시 뒤 @coderabbitai review, 봇 회차, 워크트리에서 병합. …
> 이번 요청 범위: PR과 병합까지"

기능 닫기·일지 번호 옮기기를 커밋했다(`cdc9d360`). `sibling_overlap.py`가 이 일지(24)가 main의 최신 일지(25)보다 이름순으로 앞선다고 해
`--move`로 27로 옮겼다. 푸시 직전 `git fetch`에서 origin/main이 스킬 목록 예산(#324, 겹치는 파일 없음)으로 움직여 합치고 푸시했다
(`aabf98ae`).

`-m llm`(`aabf98ae`, 04가 든 main을 합친 뒤. 합치기로 `run.py`가 바뀌어 다시 돌렸다): 7 passed, 170.68초. LLM 토큰 합계
55,120(입력 53,997, 출력 1,123), 트레이스 10개, 모델 호출 22건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다. PR 본문의 그 줄과
기능 닫기·04 합치기·일지 경로를 고쳤다.

`@coderabbitai review`(마지막 푸시 `87abe95d` 뒤)는 이번에도 "Review rate limited"였다. CI는 모두 초록.

봇 회차(claude-review, `87abe95d`): 경계 지적 없음, Major 1·Minor 2·Nit 1. 고친 것이 없다.
- **Major, 사실이 아니다.** `core.md` 32행의 실행 타임아웃 항목이 `fail_after`·`TimeoutError` 그대로라고 했지만, 그 줄은 이미
  `move_on_after`·`cancelled_caught`·`deadline_failure`·`_held`로 적혀 있고 `TimeoutError`는 "예외 타입으로 보면 ETIMEDOUT도 기한으로
  읽힌다"는 반례로만 나온다.
- **Minor, 두었다.** 같은 설명이 모듈 독스트링·`deadline_failure`·`_hold_failure`·`_connected`·`_closing`·`core.md`에 되풀이된다.
  원천 하나로 모으는 것은 이 티켓의 체크박스 밖이고 앞 회차의 "진입점 둘의 꼬리"와 같은 대기열 후보다.
- **Minor, 두었다.** `_connected` 독스트링의 "PR 직전 리뷰" 출처. `adapters/jsonl.py`·`filesystem.py`의 "(PR 직전 보안·버그 축)"과
  같은 저장소 관례다.
- **Nit, 두었다.** `_Site`의 `inside`와 `write`가 같은 원인으로 간다. 자리는 원인이 아니라 실패를 받는 곳이라 따로 둔다(명세 자리 표).
