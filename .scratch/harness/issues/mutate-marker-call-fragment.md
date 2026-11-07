# mutate-marker-call-fragment: 변이 표지가 호출 한 토막이면 `mutate.py`의 `--check`와 `--staged`가 알린다

**What to build:** `tools/mutate.py`의 표지 품질 검사(`_quality_problems`)는 pytest 판정에서 빨강을 기대한 변이의 표지가 단언 풀이 줄의 머리(`where … = …(`, `assert … ==`)로 시작할 때만 알린다. 그런데 `.scratch/approval-rules/probes/rules_file_read_mutations.toml`의 변이 1·7·8·9가 표지로 고른 `matches(server='other-server', tool='add')`, `Rule(server=None, tool='*')` 같은 부분 문자열은 `+  where False = matches(…)` 줄 안에 든 호출 한 토막이라 줄 머리 기준을 지나갔고, 이 검사가 알리지 못한 것을 표준 축 셀프 리뷰가 `.claude/rules/probes.md`의 항목 위반으로 잡았다(517의 6회차, 대기열 579). 코드를 읽었다(`tools/mutate.py`의 `_ASSERT_REWRITE`는 `re.match`로 줄 머리만 본다).

표지가 호출 한 토막, 곧 줄 머리가 `이름(` 꼴이고 그 뒤가 인자처럼 생긴 것(`)`, 따옴표, 괄호, 숫자나 식별자 뒤의 `,`·`)`, 식별자 뒤의 `=`·`,`·`)`·`(`)이면 같은 자리(고른 `--check`와 `--staged`의 새 변이)에서 같이 알린다. 알림의 문구는 호출 한 토막이라고 짚고, 인자 줄(`rule = …`)이나 단언에 싣는 메시지를 고르라고 안내한다(pytest는 `Received:` 줄을 찍지 않는다). 변이를 돌리는 실행에는 걸지 않는다(옛 표를 소급하지 않으려는 기존 규칙 그대로다).

거짓 양성이 얼마나 되는지 먼저 손으로 세어 봤다. 커밋하지 않은 스크래치 스크립트로 `.scratch/**/*_mutations.toml`을 `tomllib`로 읽어, pytest 판정(러너 정의가 없으면 도구의 기본 러너)이고 빨강을 기대한 변이의 표지 1330개를 셌다. 줄 머리가 `이름(` 꼴인 것이 12개(약 0.9%), 줄 머리를 따지지 않고 `이름(…)`이 어디든 든 것이 95개였다. 줄 머리 기준으로 가면 인자 줄(`rule = Rule(…), server = …`)이나 `At index 0 diff: Hit(…)`처럼 앞에 낱말이 붙은 표지는 걸리지 않는다. 12개 가운데 `zeta(7회차) …` 둘은 목록 출력이라 호출이 아니어서, 인자처럼 생긴 것만 받는 조건으로 거른다(셀프 리뷰가 다시 세어 넷이 아니라 둘로 고쳤다. 나머지 열은 알린다). 그래서 `.claude/rules/probes.md`에 예를 따로 더하지 않고, 이 검사가 알리는 모양을 적은 문장에 호출 한 토막을 더한다.

**대기열:** 579

**Status:** done

## 수용 기준

- [x] 실패하는 시험을 먼저 썼다: 줄 머리가 호출 한 토막인 표지(`matches(server='other-server', tool='add')`, `Rule(server=None, tool='*')`, 접두 `+ `·`E ` 붙은 것)는 고른 `--check`에서 종료 2와 호출 한 토막 알림을 내고, `--staged`는 새 변이에 같은 알림을 낸다(구현 전에 새 시험 열 사례가 빨간 것을 봤다. 같은 `-k`로 고른 나머지 열두 사례는 초록이었고 그중에 알리지 않아야 하는 새 사례가 든다)
- [x] 알리지 않는 것을 시험으로 고정했다: 인자 줄(`rule = Rule(…)`), `Received:` 줄, `At index 0 diff: Hit(…)`, 인자처럼 생기지 않은 `zeta(7회차) …`, pytest가 아닌 판정, 초록·처리하지 않은 에러를 기대한 변이. 변이를 돌리는 실행과 부모 판과 같은 옛 변이는 이 티켓 전의 시험이 이미 고정하고, 호출 꼴은 따로 더하지 않았다(같은 함수가 같은 자리에서만 부른다)
- [x] 못 보는 것을 독스트링에 적고 시험으로 고정했다: 호출 꼴이지만 값의 repr인 줄 머리(`Hit(ident=…`)도 알린다(거짓 양성), 줄 머리가 아닌 호출 조각은 받는다(거짓 음성)
- [x] `tools/mutate.py` 모듈 독스트링의 "표지의 품질" 문단과 `.claude/rules/probes.md`의 해당 문장이 호출 한 토막을 같이 말한다
- [x] 고친 `mutate.py`로 변이 1·7·8·9의 표지가 `matches(…)`·`Rule(…)`이던 표를 `--check`에 넣어 알림이 뜨는지 손으로 봤다. 그 옛 판은 병합 전에 고쳐져 커밋에 남지 않았다. 그래서 현재 `rules_file_read_mutations.toml`의 11·109·124·139행만 옛 표지로 되돌린 사본(세션 스크래치패드, 커밋하지 않았다)으로 `uv run python tools/mutate.py --check <사본> 1 7 8 9`를 쳐서 넷 모두 호출 한 토막 알림과 종료 2를 봤고, 현재 표는 같은 선택에서 종료 0이었다
- [x] 새 규칙을 빼 보는 변이 둘을 `.scratch/harness/probes/mutate_marker_quality_mutations.toml`에 더했고 기대대로 빨강이다(셀프 리뷰 반영)
- [x] 검증 명령이 모두 초록이다(손으로 치는 명령 전부와 `uv run python tools/run_checks.py`. 커밋 직전의 pre-commit이 갈음하는 것은 그 결과로 갈음한다)
