# 2026-10-26 (04) 프로브 규칙 첫 항목에 표지의 일반 조항을 더한다 (harness 015)

## 구현 (첫 세션)

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다 / 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/015-probes-marker-rule.md. .claude/rules/probes.md 첫 항목에, 고친 길을 지났다는 표지는 다른 해석 아래에서는 나지 않는 관찰로 정한다는 일반 조항을 더한다(대기열 367) / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 8 중 6. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: 대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다 / 브랜치: chore/015-probes-marker-rule / 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래 / 읽을 것: docs/agents/issue-tracker.md. 나란히 여는 나머지 티켓: .scratch/harness/issues/010-journal-evidence-hook.md, 011-mutate-check-and-marker.md, 012-env-read-option-records.md, 013-proc-cmdline-linux.md, 014-open-session-deeplink-lock.md, 016-visual-focus-flake.md, 017-tidy-collapsed-and-fresh-branches.md / 이어받을 상태: 없음 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. 첫 턴 훅의 말대로 `tidy-checkouts`는 돌지 않았다(묶음의 첫 세션 몫이다).
- `EnterWorktree(015-probes-marker-rule)` 뒤 `chore/015-probes-marker-rule`로 이름을 바꿨다. 기준은 `92b61458`(그때의 origin/main, #387)이다.
- `sibling_overlap`은 첫 대조에서 다음 빈 번호로 티켓 012를 냈다(형제 010·011이 먼저 썼다). 지시문이 준 015로 티켓을 쓴 뒤 다시 친 대조가 "이 브랜치의 새 번호: 티켓 015", "번호 겹침 없음"이었다. 일지 04도 같은 대조가 "옮길 번호" 없이 받았다. 형제 012·016이 05를 함께 쓰고 있다고 나왔으나 이 일지의 번호와는 겹치지 않는다.

### 한 것 (커밋하지 않았다)

- 티켓 `.scratch/harness/issues/015-probes-marker-rule.md`(in-progress).
- `.claude/rules/probes.md` 첫 항목: "표지는 재려는 상황에서만 나오는 문구로 고른다"를 "문구나 관찰"로 넓히고, 바로 뒤에 일반 조항(그 표지로 가르려는 다른 해석 아래에서는 나지 않는 관찰이고, 두 해석 아래에서 모두 나는 관찰은 표지가 못 된다)과 그 두 꼴(고친 길의 표지는 고치기 전 판이라면 실패했을 회차에서만 나는 관찰, 출력이 잘리지 않았다는 표지는 잘린 출력에서 빠지는 자리의 값)을 더했다. 사례 끝에 "대기열 367의 사례"로 세 회차와 선례 둘(`mutate_ctrl_c.py`의 `passed_past_first_window`, `open_session_pattern_timed.py`의 멈춘 사례보다 오래 기다리고 통과한 회차)을 더했다.
- 카나리아 `.scratch/harness/probes/canary/probes_rule_marker_other_reading.toml`(새 명세). 실험군은 선례 프로브 `mutate_ctrl_c.py`, 대조군은 paths 밖 `plan.md`다.
- `tools/probe_kit.py` 독스트링의 못 보는 것: "대기열 367 이 그 정의를 맡는다"를 "그 정의는 `.claude/rules/probes.md` 첫 항목이 맡는다, 대기열 367"로 고쳤다. 행이 닫혀 열린 일을 가리키게 되기 때문이다.
- 대기열 367을 이 티켓으로 닫았다.

### 결정

- 일반 조항은 새 문장을 따로 세우지 않고 기존 "재려는 상황에서만 나오는 문구로 고른다" 바로 뒤에 붙였다. 그 문장이 같은 뜻의 한 쌍(상황이 났다, 나지 않았다)만 말하던 것을 넓히는 일이라, 떨어뜨리면 같은 뜻이 두 자리로 흩어진다. 이어지는 변이(`expect_output`) 문장은 손대지 않았다. 그 문장이 가르는 다른 해석(다른 단언이 빨개졌다)도 일반 조항의 한 꼴로 읽히고, 기존 카나리아 `probes_rule_stream_delete_marker.toml`의 조각 "값까지 든 `Received:` 줄"이 그 문장에 있다.
- "문구"를 "문구나 관찰"로 넓혔다. 두 선례의 표지는 출력의 문구가 아니라 잰 값(걸린 시간, 기다린 시간)이라, "문구"만으로는 두 선례가 그 문장에 들지 않는다.
- 339 행의 꼬리("367이 맡는다")와 `edit_during_commit_launcher.py`의 인용(`probes.md` 첫 항목, 대기열 367)은 고치지 않았다. 앞의 것은 닫힌 행의 기록이고, 뒤의 것은 규칙 자리와 행 번호를 함께 들어 지금도 맞다.

### 검사 (커밋 전, 셀프 리뷰 전)

- `uv run python tools/canary.py --preflight .scratch/harness/probes/canary/probes_rule_marker_other_reading.toml`: 통과 1.
- `uv run python tools/canary.py .scratch/harness/probes/canary/probes_rule_marker_other_reading.toml <스크래치>`: 통과 4(claude 2.1.302). 실험군 셋은 두 문장을 글자 그대로 옮겼고 대조군은 "없음"이었다. 첫 판의 질문은 옮길 둘째 문장을 "그 바로 앞에서"라는 자리로 골라, 돌리기 전에 operations.md 카나리아 항목대로 내용("어떤 관찰은 표지로 쓸 수 없다고 일반적으로 정하는 문장")으로 바꿨다. 돈 것은 바꾼 판이다.
- 살아 있는 문서(규칙, 스킬, 서브에이전트, `tools/`, `tests/`, 헌법, `docs/agents/`, 프로브)를 "대기열 367"과 "재려는 상황에서만"으로 grep했다. 고칠 것은 `tools/probe_kit.py` 하나였다.
- `uv run ruff check .`: 통과. `uv run ruff format --check .`: 1054 files already formatted.
- `uv run python tools/run_checks.py`(백그라운드): 끝나기 전에 인계로 멈췄다(TaskStop). 결과는 보지 않았다.

### 인계 (셀프 리뷰 직전)

`/code-review 92b61458`을 부른 직후 `hook_handoff`가 세션 컨텍스트 219,394 토큰으로 경계 `셀프 리뷰 직전`을 알렸다. `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이 아니고, "인계하지 않는 때" 다섯에 들지 않아 넘긴다. 셀프 리뷰의 단계는 밟지 않았다. 이 세션의 지금 제목은 `chore/015-probes-marker-rule`이고, 넘기기 전에 `chore/015-probes-marker-rule (인계함)`으로 바꾼다.

지시문:

```
다음 작업: .scratch/harness/issues/015-probes-marker-rule.md. .claude/rules/probes.md 첫 항목에, 고친 길을 지났다는 표지는 다른 해석 아래에서는 나지 않는 관찰로 정한다는 일반 조항을 더한다(대기열 367)
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다
브랜치: chore/015-probes-marker-rule
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-04-probes-marker-rule.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review 92b61458)부터 한다. 티켓·규칙·카나리아 명세·대기열 닫힘·probe_kit 독스트링은 이미 썼다. 카나리아 probes_rule_marker_other_reading.toml은 지금 판에서 통과 4였고, 셀프 리뷰가 규칙 본문이나 명세를 고치면 operations.md 카나리아 항목대로 사전 확인으로 갈음하거나 다시 돈다. 린트 둘은 통과했고 tools/run_checks.py는 끝나기 전에 인계로 멈췄다. 일지 docs/journal/2026-10-26-04-probes-marker-rule.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 바꿨고, `tools/run_checks.py` 대기를 TaskStop으로 멈췄으며, `git worktree unlock C:/project/agent/.claude/worktrees/015-probes-marker-rule`이 오류 없이 끝났다.

open-session을 부른다 2026-10-26T06:48:18Z

## 셀프 리뷰부터 (둘째 세션)

> 사용자: (인계 지시문을 첫 메시지로 받았다) "대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다 / 다음 작업: .scratch/harness/issues/015-probes-marker-rule.md. .claude/rules/probes.md 첫 항목에, 고친 길을 지났다는 표지는 다른 해석 아래에서는 나지 않는 관찰로 정한다는 일반 조항을 더한다(대기열 367) / 다음 단계: 구현 / 어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다 / 이어받을 상태: 인계: 셀프 리뷰 직전. … / 확인할 선행 조건: 없음 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. `git worktree list`에서 `chore/015-probes-marker-rule`은 `.claude/worktrees/015-probes-marker-rule`(잠김 없음, `92b61458`)이라 `EnterWorktree(path)`로 들어갔다. 커밋하지 않은 변경 여섯 파일이 그대로 있었다.

### 셀프 리뷰 (`/code-review 92b61458`)

범위: base `92b61458`, 바뀐 추적 파일 셋(`.claude/rules/probes.md`, `.scratch/retro-queue.md`, `tools/probe_kit.py`), 커밋 0, 미추적 셋(티켓, 카나리아 명세, 이 일지). 표준 축은 sonnet·high, 명세 축은 이 세션의 모델이다.

표준 축: Critical·Major 0, Minor 1, Nit 2, 확인하지 못한 것 1.

- Minor(고친다): 규칙의 선례 문장이 `open_session_pattern_timed.py`도 "센다"고 적었는데, 그 프로브의 `summarize`는 통과하며 1초 넘게 기다린 값(`passed_waited_over_1000ms`)과 기다린 시간의 분포(`waited_ms`)를 낼 뿐이고 맞대어 세는 것은 독스트링대로 읽는 쪽이 한다(그 파일 25~27행, 302~306행을 열어 봤다). `mutate_ctrl_c.py`의 `passed_past_first_window`는 782행에서 실제로 세지만, "다음 창으로 간"은 판정 `_멈추는지`가 1.5초(`PAST_FIRST_WINDOW_SECONDS`)를 넘게 걸린 것으로 가늠한 것이라(그 파일 72~73행, 135~136행, 511행) 규칙에 그 문턱을 함께 적는다.
- Nit(남긴다): 카나리아 질문이 답이 놓일 자리(칸, 절)를 묻지 않는다(operations.md 79행). 규칙 파일의 한 항목이라 이름 붙은 칸이 없고, 같은 규칙의 기존 카나리아 `probes_rule_stream_delete_marker.toml`도 같은 꼴로 통과했으며, 이번 대조군이 "없음"이라 질문이 답을 흘리지 않았다. 질문을 바꾸면 사전 확인으로 갈음할 수 없어 네 회차를 다시 돌아야 한다.
- Nit(고친다): 티켓 What to build의 "판정은 검사가 할 수 없어"에 까닭이 없다. 한 구절로 까닭을 더한다.
- 확인하지 못한 것(반영): `.claude/rules/agent-docs.md`는 규칙을 고치기 전에 `writing-for-agents`를 부르라고 하는데 첫 세션의 일지에 그 기록이 없다. 이 세션이 규칙을 고치기 전에 불렀고, 그 기준으로 새 문장을 다시 봤다. 금지문("표지가 못 된다")은 긍정 목표("다른 해석 아래에서는 나지 않는 관찰")와 짝지어 있어 그대로 둔다.
- 판단 항목(남긴다): 첫 항목이 사례 여섯과 일반 조항을 한 불릿에 담아 길다(Divergent Change 가능성). 저장소의 이 규칙이 이미 그 꼴이고 이 티켓의 범위가 아니다.

명세 축: (a) 빠진 요구 0, (b) 요청하지 않은 동작 0, (c) Major 1, Minor 1, Nit 2.

- Major(고친다): 표준 축의 Minor와 같은 자리다. `open_session_pattern_timed.py`가 "센다"는 거짓이고, 명세 축은 `summarize`를 경계 입력으로 불러 회차 수를 내지 않는 것을 봤다(스크래치패드의 `spec_probe_015.py`).
- Minor(고친다): `passed_past_first_window`도 일반 조항을 엄밀히는 채우지 못한다. 고치기 전 시험은 `assert not _뛰는지(심장)`이고 `_뛰는지`는 크기를 읽고 0.5초 잔 뒤 한 번 견준다(`git show 5e7fa88d^:tests/tools/test_mutate.py`의 416~419행, 473행). 지금 `_멈추는지`는 1초 창마다 견주고(`tests/tools/test_mutate.py` 424~437행), 프로브는 그 호출이 1.5초를 넘은 것으로 다음 창으로 갔다고 가늠한다(프로브 72~73행, 511행). 그래서 러너가 돌아온 뒤 0.5~1초 사이에만 자란 회차는 두 판 모두 통과하는데 이 셈에 든다. 티켓이 이 선례를 지정했으므로 빼지 않고, 규칙에 그 틈을 적어 깨끗한 선례(`open_session_pattern_timed.py`)를 앞에 두었다.
- Nit(고친다): "셋 다 … 나서 셀프 리뷰가 두 번 Major로 잡았다"가 셀프 리뷰가 셋을 다 잡은 것처럼 읽힌다. 일지 2026-10-19-25에서 앞의 둘은 셀프 리뷰 Major(340행의 명세 축, 520·547행의 N1·S3)이고, 셋째("기다림 ≥ 1초")는 N1·S3를 고친 뒤 다시 잰 측정이 드러냈다(565~566행). 그대로 나눠 적었다.
- Nit(남긴다): "곧 … 관찰이고"가 앞 문장의 "문구나"를 떨어뜨렸다. 출력의 문구도 관찰의 하나라 뜻이 좁아지지 않고, 그 뒤의 카나리아 조각("두 해석 아래에서 모두 나는 관찰은 표지가 못 된다")과 낱말이 맞는다.

고친 것(PR 직전 리뷰에 밀 주장으로 넘긴다):

1. `.claude/rules/probes.md`: "셋 다 고치기 전 판이 통과한 회차에도 났다. 앞의 둘은 셀프 리뷰가 Major로 잡았고, 셋째는 둘째를 고친 뒤 다시 잰 측정이 드러냈다(일지 2026-10-19-25)."
2. `.claude/rules/probes.md`: "`.scratch/harness/probes/precommit_xdist/open_session_pattern_timed.py`는 고친 판의 지연 0 사례가 통과하며 기다린 시간과 멈춘 사례가 기다린 시간을 내고, 앞의 것이 같은 측정에서 뒤의 것의 가장 긴 값보다 긴 회차를 읽는 쪽이 센다. 그 측정에서 1초 제한은 그 시각까지 모두 걸렸으므로 고치기 전 판이라면 실패했을 회차로 본다."
3. `.claude/rules/probes.md`: "같은 폴더의 `mutate_ctrl_c.py`가 세는 `passed_past_first_window`는 그보다 느슨하다. 판정 `_멈추는지`가 1.5초 넘게 걸린 것으로 첫 1초 창에서 자람을 봤다고 가늠하고 통과한 회차를 세는데, 고치기 전 판정은 러너가 돌아온 직후 0.5초만 견줬으므로 0.5~1초 사이에만 자란 회차는 두 판 모두 통과하고도 이 셈에 든다."
4. 티켓 What to build: "어떤 관찰이 다른 해석 아래에서도 나는지는 프로브마다 그 해석을 읽어야 가를 수 있어 검사가 판정할 수 없고, 그래서 층은 그 항목이 실리는 자리의 문장이다."

남긴 것: 카나리아 질문이 자리를 묻지 않는 Nit, 첫 항목의 길이(판단 항목), "문구나"를 떨어뜨린 Nit. 까닭은 위 지적마다 적었다.

다시 돌린 것: 고친 곳이 규칙 본문뿐이고 claude 판(2.1.302)·명세의 칸·`expect`가 그대로라, operations.md 카나리아 항목대로 `uv run python tools/canary.py --preflight .scratch/harness/probes/canary/probes_rule_marker_other_reading.toml`로 갈음했다. 통과 1. 명세의 `# 최신 결과:` 줄 뒤에 갈음을 덧붙였다. 손으로 치는 검증 다섯은 커밋의 pre-commit으로 갈음하고, 결과는 커밋 뒤에 적는다.

### 커밋

- 첫 커밋 시도는 pre-commit의 pytest 하나로 막혔다(1141.1초, 5589 통과 1 실패). 실패는 이 브랜치가 건드리지 않은 `tests/tools/test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`의 `assert 1 == 0`이었고, 따로 돌리니 38.59초에 지났다. 나머지 검사(ruff 둘, lint-imports, check-ticket, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify, 표·줄 구분 문자·변이 표·카나리아 명세 모양·인용)는 지났다. 나란히 여는 형제 세션 여럿이 함께 돌던 때다. 같은 파일의 다른 시험이 일지 2026-10-24-10과 2026-10-25-02에서 같은 꼴로 빨갰고, 그 세션들은 대기열 306이 받아들여 닫은 종류(전체 스위트의 부하 아래에서만 빨간 시험)로 보고 일지에만 적었다. 같이 하고 커밋을 다시 쳤다. 첫 시도는 막혔으므로 인계 계기의 `커밋 뒤` 경계가 아니었다.
- 둘째 시도도 pytest에서 막혔다(844.0초, 5588 통과 2 실패). 같은 파일의 다른 시험 둘(`test_본_측정에서_첫_인계_뒤_멈추고_확인_인자를_주면_잇는다`의 안내 줄 단언, `test_동시에_둘까지_돌고_셋째는_자리가_빌_때_연다`의 `assert 1 == 0`)이었고, 둘을 따로 돌리니 48.16초에 지났다. 대기열 306의 닫힘(ADR 0036)이 이 종류는 커밋을 다시 치는 값을 받아들이고 사례를 고치지 않는다고 정해 두어, 시험을 고치지 않고 셋째로 다시 쳤다. 이 파일의 시험이 다른 세션 둘(일지 2026-10-24-10, 2026-10-25-02)과 이 세션 두 번에서 모두 넷 빨갰다는 것은 회고가 볼 수 있게 여기 적어 둔다.
- 셋째 시도도 pytest에서 막혔다(1195.8초, 5588 통과 2 실패). `tests/channel/cli/test_interrupt.py::test_도구_호출_도중에_한_번_누르면_서버를_닫고_중단으로_끝난다`("Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다")와, 둘째 시도에서도 빨갰던 `test_동시에_둘까지_돌고_셋째는_자리가_빌_때_연다`다. 같은 시험이 두 번 연속 빨갰으므로 그대로 다시 치지 않고 부하를 봤다. CPU 100%, python 119개·node 92개·claude 35개가 떠 있었다(형제 세션들의 pre-commit이 함께 돌던 때다). ADR 0036이 받아들인 길(다시 친다)을 따르되, CPU가 20초 간격으로 세 번 연달아 60% 아래일 때까지 기다린 뒤 친다(스크래치패드의 `wait_load.ps1`, 최대 45분). 시험은 고치지 않는다.
- 45분 동안 부하가 내려가지 않았다(끝에 CPU 100%, python 74개). 그래서 pytest를 pre-commit에서 빼고(`SKIP=pytest`, `tools/run_checks.py`가 같은 id로 읽는다) 손으로 쳤다. 스테이지된 판(작업 트리와 같다)에서 `uv run pytest -q -p no:cacheprovider`를 한 프로세스로 돌려 5590 통과, 8 deselected(LLM 마커)로 지났다(4421.92초). 그 뒤 이 일지 줄만 더하고 `SKIP=pytest`로 커밋했다. 이 일지 고침은 pre-commit의 표·줄 구분 문자 검사가 본다.
