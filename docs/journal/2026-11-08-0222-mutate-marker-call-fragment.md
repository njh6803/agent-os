# 변이 표지가 호출 한 토막이면 mutate.py가 알린다 (harness mutate-marker-call-fragment, 대기열 579)

세션 제목: `chore/mutate-marker-call-fragment` (인계하며 `chore/mutate-marker-call-fragment (인계함)`으로 바꾼다). 브랜치 `chore/mutate-marker-call-fragment`, 워크트리 `C:\project\agent\.claude\worktrees\mutate-marker-call-fragment`. 모델 Sonnet 5.5 / high.

## 사용자 프롬프트

> 사용자: 대기열 579를 티켓 .scratch/harness/issues/mutate-marker-call-fragment.md로 쓰고 한다

지시문의 다음 작업은 받는 세션이 `.scratch/harness/issues/mutate-marker-call-fragment.md`를 쓰고, 변이 표 표지가 pytest 단언 풀이 줄의 호출 한 토막(이름(...) 꼴)일 때 `tools/mutate.py`의 `--check`와 `--staged`가 알리게 하는 것이었다(대기열 579, 6회차). 다음 단계 구현, 이번 요청 범위는 PR과 병합까지, 이어받을 상태는 없음, 모델은 Sonnet 5.5 / high였다.

## 한 것

- 새 워크트리에 들어가 브랜치 `chore/mutate-marker-call-fragment`를 땄다. 기준은 `origin/main`의 `778db404`다.
- 티켓 `.scratch/harness/issues/mutate-marker-call-fragment.md`를 코드를 고치기 전에 썼고, 지금은 수용 기준을 모두 체크하고 `Status: done`으로 바꿔 두었다. 커밋 전이다.
- 거짓 양성을 먼저 어림했다. 커밋하지 않은 스크래치 스크립트로 `.scratch/**/*_mutations.toml`을 `tomllib`로 읽어 손으로 셌다. pytest 판정(러너 정의가 없으면 도구의 기본 러너)이고 빨강을 기대한 변이의 표지 1330개 가운데 줄 머리가 `이름(` 꼴인 것이 12개, 줄 머리를 따지지 않고 `이름(…)`이 든 것이 95개였다. 12개 가운데 `zeta(7회차) …` 둘은 목록 출력이라 호출이 아니다(처음 적은 "넷"은 틀렸고 셀프 리뷰 두 축이 다시 세어 고쳤다).
- 그래서 줄 머리 기준으로 가고, `이름(` 뒤가 인자처럼 생긴 것(`)`, 따옴표나 괄호, 숫자나 식별자 뒤의 `,` `)`, 식별자 뒤의 `=` `,` `)` `(`)만 받는 정규식 `_CALL_FRAGMENT`를 `tools/mutate.py`에 더했다. 인자 줄(`rule = Rule(…)`), `Received:` 줄, `At index 0 diff: Hit(…)`는 줄 머리가 호출이 아니라 알리지 않는다. `.claude/rules/probes.md`에 예를 따로 더하지 않았다. 거짓 양성이 적어서다.
- 시험을 먼저 썼다(`tests/tools/test_mutate.py`): 알리는 여덟 사례, 알리지 않는 일곱 사례, pytest가 아닌 판정과 초록 기대, 못 보는 것 둘(값의 repr 줄 머리는 알린다, 줄 머리가 아닌 호출 조각은 받는다), 색인 확인의 한 사례. 구현 전에 열 사례가 빨갛고 구현 뒤에 `-k "표지 or 호출 or 원문_확인 or 색인_확인"`로 고른 116개가 모두 초록이었다.
- `tools/mutate.py` 모듈 독스트링의 "표지의 품질" 문단(둘→셋, 새 항목, 합친 "못 보는 것")과 두 요약 문장, `_quality_problems` 독스트링, `.claude/rules/probes.md`의 해당 문장(호출 한 토막, 대기열 579)을 고쳤다. `writing-for-agents` 기준으로 보고 `probes.md`에 덧붙였던 중복 문장은 지웠다.
- 수용 기준의 손 확인: 현재 `rules_file_read_mutations.toml`의 11·109·124·139행만 옛 호출 한 토막 표지로 되돌린 사본(세션 스크래치패드, 커밋하지 않았다)에 `uv run python tools/mutate.py --check <사본> 1 7 8 9`를 쳐서 넷 모두 호출 한 토막 알림과 종료 2를 봤다. 현재 표는 같은 선택에서 종료 0이었다. 옛 판은 병합 전에 고쳐져 커밋에 남아 있지 않다.
- `uv run python tools/plan_table.py`를 돌렸고 `.scratch/plan.md`는 바뀌지 않았다(harness 티켓은 전체 계획에 들지 않는다).
- `uv run ruff check .`와 `uv run ruff format --check .`는 초록이었다.

## 고친 것과 번복한 것

- 티켓 첫 판의 두 문장이 사실과 달라 고쳤다. 옛 표가 커밋 `e9bbfcc9`에 남아 있다고 적었으나 남아 있지 않았다. 구현 전에 통과한 사례 열둘을 "알리지 않는 새 시험"이라 적었으나 기존 시험이 섞여 있었다.

## 셀프 리뷰 (이어받은 세션, base `778db404`, 파일 3개 수정과 미추적 2개, 커밋 0)

표준 축(sonnet·high)과 명세 축이 돌았다. 고친 것:

- Minor. 티켓·일지·`mutate.py` 독스트링의 "zeta 넷"이 틀렸다. 내가 다시 센 결과 줄 머리가 `이름(` 꼴인 표지 12개 가운데 `zeta(7회차) …`는 둘이고 새 정규식은 열을 알린다. 세 곳을 고쳤다.
- Minor. 둘째 알림이 셋으로 늘었는데 옛 문장이 남았다. `check_picked` 독스트링과 `tests/tools/test_mutate.py`의 절 머리 주석을 고쳤다.
- Minor. 변이 표 `.scratch/harness/probes/mutate_marker_quality_mutations.toml`에 새 규칙의 변이가 없었다. 새 규칙을 빼는 변이와 줄 머리 기준을 `search`로 넓히는 변이를 더했다. 분리 임시 워크트리에서 그 둘만 돌려 기준선 초록(`8 passed`, `1 passed`)과 기대한 빨강을 도구가 찍은 줄로 봤다(`변이 2 모두 기대대로`). 프로브 README 행도 맞췄다.
- 명세 축 (a) 정규식이 서술보다 좁다. 소수·접두 문자열·`*args`·음수 식별자·첨자·한글 인자·줄 끝 `Rule(`는 알리지 않는데 독스트링의 못 보는 것에 없었다. 독스트링에 적고 시험 여덟 사례(`test_못_보는_것_인자가_정수_식별자_따옴표로_시작하지_않는_호출_조각은_받는다`)로 고정했다. 정규식은 손으로 대 보고(`uv run python -c`) 적었다.
- 표준 축 (b) 안내가 틀린 길. 알림 문구와 티켓이 `Received:` 줄을 고르라고 했으나 pytest는 그 줄을 찍지 않는다(vitest 몫). 알림 문구를 "인자 줄이나 단언에 싣는 메시지"로 고치고 독스트링에서 `Received:`를 뺐다. 알리지 않는 시험의 `Received:` 사례는 줄 머리 꼴만 고정하므로 두었다.

남긴 것:

- 표준 축 Minor. 독스트링의 "손으로 셌다" 수치에 커밋한 프로브가 없다. 앞 티켓 041의 "1883·176"과 같은 꼴이고 `tomllib`로 읽어 세었다는 방법을 함께 적었다. 선례를 따라 두었다.
- 표준 축 판단. `_ASSERT_REWRITE`/`_NOTE`와 `_CALL_FRAGMENT`/`_NOTE`가 같은 쌍 모양이다. `if/elif`로 충분하고 셋째 규칙이 생기면 표로 바꿀 만하다. 두었다.
- 티켓 상태. 마지막 수용 기준(검증 명령)은 아래 검증 뒤에 체크한다.

다시 돌린 명령: `uv run python tools/run_checks.py` 한 바퀴(리뷰 반영 전 판, 18분)가 3개 실패했다(`test_probe_kit`의 배출, `test_interrupt`의 닫는 도중 한 번 더, `test_rerun_runner`의 두 회차 번호). 셋을 따로 돌리면 모두 통과했다(20초). 서브에이전트와 시험이 같은 PC에서 겹쳐 돈 부하의 시간 의존 실패로 본다.

## 카나리아

`.claude/rules/probes.md` 첫 항목을 고쳤으므로 `tools/sibling_overlap.py`가 그 파일을 원천으로 든 명세 여덟을 알렸다(종료 1). 같은 PR 안의 통과가 없어 `probes_rule.toml`을 실제로 돌렸다. 도구가 찍은 줄: 통과 4, 실패 0, "없음" 섞인 통과 0, 두 갈래 커밋 `778db404`, 돌린 뒤 `claude --version`은 2.1.318(손으로 쳤다). 나머지 일곱은 `--preflight`로 갈음했다(일곱 모두 통과, claude는 돌리지 않았다). 더한 문장이 그 명세들이 묻는 자리 밖이라는 근거는 문장의 위치를 읽은 판단이다. 여덟 명세의 머리 주석에 이 결과와 갈음을 덧붙였고 `uv run python tools/canary.py --shape`를 쳤다.

## 커밋 시도

pre-commit이 세 번 pytest 하나만 빨갛게 막았다(나머지 검사는 모두 Passed. 도구가 찍은 줄). 시도마다 실패한 시험이 달랐다. 첫 시도(1179.6초)는 `test_interrupt`의 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다", `test_probe_kit`의 배출, `test_rerun_runner` 둘이었고, 둘째(1038.6초)는 `test_interrupt` 셋과 `test_rerun_gates` 하나, 셋째(다른 세션의 `run_checks`가 모두 끝난 뒤, pytest 578.5초)는 `test_rerun_runner`의 `test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다` 하나였다. 첫 실패 묶음 중 셋과 둘째 시도의 `test_interrupt`·`test_rerun_runner` 시험들을 단독으로 돌리자 모두 통과했다(`9 passed in 130.28s`, 앞의 `3 passed in 20.10s`, 명령의 출력). 바꾼 파일은 `tools/mutate.py`와 그 시험, 규칙 문서, 프로브 표뿐이라 이 시험들이 부르는 코드를 건드리지 않았다. 일지 2026-10-30-07이 같은 두 시험의 부하 아래 시간 실패를 기록했고 그때도 단독 통과를 확인한 뒤 커밋을 다시 시도했다. 그 절차를 따랐다. 대기열 회차는 세지 않았다(이 세션에서 확인하지 않았다).

## 아직 안 한 것

- 반영 뒤 커밋이 부르는 pre-commit(`CLAUDE.md` 검증 명령 절이 갈음하는 것과 갈음되지 않는 것), `sibling_overlap.py`, PR, 봇 회차, 병합(`merge.md`의 워크트리 길)이 남았다.

## 인계

인계 계기 `셀프 리뷰 직전`(세션 컨텍스트 211,487 토큰, 문턱 200,000)에 `handoff.md`대로 넘겼다. 제목을 `chore/mutate-marker-call-fragment (인계함)`으로 바꿨고, 띄운 `run_checks` 대기를 TaskStop으로 멈췄고, 워크트리 잠금을 풀었다.

open-session을 부른다 2026-11-07T17:24Z

## 이어받은 세션의 인계 (커밋 뒤)

셀프 리뷰 직전 인계를 받은 세션이 셀프 리뷰, 반영, 카나리아, 커밋(`3ef6312d`, pre-commit 모두 통과. 위 "커밋 시도"와 "카나리아" 절)까지 마쳤다. 세션 제목은 `chore/mutate-marker-call-fragment`였고 인계하며 `chore/mutate-marker-call-fragment (인계함)`으로 바꾼다. 이 일지의 앞 절들이 그 세션이 한 것이다. 사용자 프롬프트는 처음 하나뿐이었고(위 "사용자 프롬프트") 이번 세션에서 새로 받은 결정은 없다.

인계 계기 `커밋 뒤`(세션 컨텍스트 287,026 토큰, 문턱 200,000)에 `handoff.md`대로 넘긴다. 아직 푸시하지 않았고 PR도 열지 않았다. 남은 것은 푸시, PR 열기(본문에 검증 결과와 카나리아, 변이, 커밋 시도 경위), 봇 회차, `merge.md`의 워크트리 길로 병합이다. 이 커밋에 일지가 이미 들었으므로 이 절을 쓴 뒤의 변경은 일지만이고 새 세션이 같은 파일을 이어 쓴다.

open-session을 부른다 2026-11-07T20:12Z
