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
- `SKIP=pytest` 커밋이 `b39a3698`로 지났다. ruff 둘, lint-imports, check-ticket, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks(317.2초), web-verify(734.7초), 표, 줄 구분 문자, 변이 표, 카나리아 명세 모양, 인용, 커밋 메시지가 `Passed`이고, pytest는 `Skipped`(위 손으로 친 한 프로세스 실행이 갈음한다), 헌법 판은 고친 파일이 없어 `Skipped`다. `-m llm`·`-m llm_widget`·e2e·사진 비교는 이 변경(규칙 문장, 독스트링, 티켓, 카나리아 명세, 대기열, 일지)이 닿지 않아 돌리지 않았다.

### 인계 (커밋 뒤)

`SKIP=pytest` 커밋에서 `hook_handoff`가 세션 컨텍스트 300,760 토큰으로 경계 `커밋 뒤`를 알렸다. 커밋은 성공했고, 요청 범위는 PR과 병합까지이며, 이 세션의 지시문의 이어받을 상태는 `인계: 셀프 리뷰 직전`이라 같은 경계가 아니고, 이 세션이 쓴 `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이 아니다. 그래서 넘긴다. 브랜치에 열린 PR은 없다(`gh pr view`가 "no pull requests found"). 이 세션의 지금 제목은 `chore/015-probes-marker-rule`이고, 넘기기 전에 `chore/015-probes-marker-rule (인계함)`으로 바꾼다.

남은 단계:

1. 푸시(아직 하지 않았다).
2. PR 직전 리뷰. CodeRabbit CLI는 이 세션의 `coderabbit auth status`에서 `Seat: not assigned`였다. 그래서 operations.md 리뷰 파이프라인 2의 대체 둘을 돈다. `/security-review`는 origin/main을 합친 뒤에 돌고, `bug-perf-review`의 브리프에는 위 셀프 리뷰 절의 "고친 것" 1~4를 밀 주장으로 넘긴다.
3. 티켓을 `done`으로 바꾸고 마지막 수용 기준(검증 명령)에 표시한다. 손으로 치는 다섯은 커밋 `b39a3698`의 pre-commit과 위 한 프로세스 pytest로 갈음했다.
4. PR, 봇 회차, 병합(워크트리라 next-session의 "워크트리에서 병합할 때").

주의: 형제 011의 PR #388도 `.claude/rules/probes.md`를 고친다. 그쪽이 먼저 병합되면 origin/main을 합칠 때 첫 항목에서 글자 충돌을 푼다.

지시문:

```
다음 작업: .scratch/harness/issues/015-probes-marker-rule.md. .claude/rules/probes.md 첫 항목에, 고친 길을 지났다는 표지는 다른 해석 아래에서는 나지 않는 관찰로 정한다는 일반 조항을 더한다(대기열 367)
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다
브랜치: chore/015-probes-marker-rule
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-04-probes-marker-rule.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영해 b39a3698로 커밋했고(pytest는 부하로 세 번 막혀 SKIP=pytest로 빼고 한 프로세스로 손으로 쳐 초록) 아직 푸시하지 않았다. 열린 PR은 없다. 푸시, PR 직전 리뷰(CodeRabbit CLI 좌석 없음이라 /security-review와 bug-perf-review, 밀 주장은 일지의 셀프 리뷰 "고친 것" 1~4), 티켓 done, PR, 봇 회차, 병합이 남았다. 일지에 커밋하지 않은 인계 절이 있다. PR #388도 .claude/rules/probes.md를 고친다. 일지 docs/journal/2026-10-26-04-probes-marker-rule.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/015-probes-marker-rule (인계함)`으로 바꿨다. 돌던 백그라운드 작업은 없었다. `git worktree unlock C:/project/agent/.claude/worktrees/015-probes-marker-rule`은 `is not locked`로 끝나 넘어갔다(첫 세션이 푼 뒤 이 세션의 `EnterWorktree(path)`는 잠그지 않은 것으로 보인다).

open-session을 부른다 2026-10-26T10:41:36Z

## PR과 병합 (셋째 세션)

> 사용자: (인계 지시문을 첫 메시지로 받았다) "대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다 / … / 이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영해 b39a3698로 커밋했고(pytest는 부하로 세 번 막혀 SKIP=pytest로 빼고 한 프로세스로 손으로 쳐 초록) 아직 푸시하지 않았다. … / 확인할 선행 조건: 없음 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. `git worktree list`에서 `chore/015-probes-marker-rule`은 `.claude/worktrees/015-probes-marker-rule`(`b39a3698`)이라 `EnterWorktree(path)`로 들어갔다. 커밋하지 않은 것은 이 일지의 인계 절 하나였다.
- `git fetch origin` 뒤 `git log 92b61458..origin/main`이 비어, origin/main은 기준에서 움직이지 않았다. 합칠 것이 없다.
- 형제 011의 PR #388은 아직 열려 있고, `.claude/rules/probes.md`의 같은 첫 항목 한 줄을 고친다(`gh pr diff 388`). 늦게 병합되는 쪽에서 그 줄의 글자 충돌이 난다.
- 푸시했다(`chore/015-probes-marker-rule`, 원격 새 브랜치).

### PR 직전 리뷰

CodeRabbit CLI는 `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 operations.md 리뷰 파이프라인 2의 대체 둘을 나란히 돌렸다.

- `/security-review`: origin/main이 기준과 같아 합치지 않고 돌렸다. 식별 서브태스크가 "No findings"를 내 거를 후보가 없었다. 바뀐 파일 가운데 실행되는 것은 카나리아 명세뿐이고, 그 값은 커밋된 고정 상수이며 `tools/canary.py`가 셸 인자나 `eval`에 넘기지 않는다고 그 서브태스크가 따라가 봤다.
- `bug-perf-review`(기준 `92b61458`, 호출 36): 유효 2, 보류 2, 오탐 4. 밀 주장 넷(셀프 리뷰 절의 "고친 것" 1~4)은 모두 근거와 맞았다.

트리아지와 처리:

1. 유효(고쳤다): 규칙의 선례 문장이 멈춘 사례의 비교 값을 "가장 긴 값"으로만 적어 프로브 독스트링의 "(두 판 가운데 긴 것)"이 빠졌다. `summarize`가 판(파일)마다 `waited_ms`를 따로 내므로 한 측정에 max가 둘이다(`open_session_pattern_timed.py` 22~24행, 316~324행을 열어 봤다). 규칙에 그 구절을 더했다.
2. 유효(고쳤다): `mutate_ctrl_c.py` 독스트링 70~73행이 `passed_past_first_window`를 단서 없이 고친 길의 표지로 적어 규칙과 어긋났다. `.scratch/harness/probes/`는 살아 있는 문서라(operations.md 문서 위치) 그 문단 끝에 단서 한 문장을 더했다. 같은 지적이 함께 든 ADR 0035 87행은 `### 2026-10-18` 이력 항목 안이라 기록이어서 고치지 않았다. 프로브 README 166행도 그 프로브의 지난 결과를 적은 행이라 두고, 정의의 원천인 독스트링만 고쳤다.
3. 보류였던 것(고쳤다): 걸린 시간 가늠이 느슨한 방향이 0.5~1초 하나만이 아니다. 지금 `_멈추는지`는 크기를 읽고 `time.sleep(1)` 뒤 한 번 견주고 같으면 참이다(`tests/tools/test_mutate.py` 424~437행). 부하로 그 sleep이 1.5초를 넘기면 자람이 없어도 `past_first_window`가 참이고, 그 회차는 고치기 전 판도 통과한다. 코드로 닫혀 2의 단서 문장에 함께 적었다. 규칙은 이미 "가늠하고"로 한정했고 틈 하나를 예로 들어 두었다.
4. 보류(병합 때 한다): PR #388과의 글자 충돌. 늦게 병합되는 쪽에서 풀고 두 문장이 모두 남았는지 본 뒤, 카나리아 둘(`probes_rule_marker_other_reading.toml`, `probes_rule_stream_delete_marker.toml`)을 사전 확인으로 다시 본다.

다시 돌린 것: 규칙 본문과 실험군 대상 파일(`mutate_ctrl_c.py`)이 바뀌었고 claude 판·명세의 칸·`expect`가 그대로라, `uv run python tools/canary.py --preflight .scratch/harness/probes/canary/probes_rule_marker_other_reading.toml`로 갈음했다. 통과 1. 더한 독스트링 문장에는 `expect`의 두 조각이 없다. `uv run ruff check`와 `uv run ruff format --check`를 그 프로브 파일에 쳐 통과했다.

### 커밋과 PR

- 커밋 직전 `git branch --show-current`가 `chore/015-probes-marker-rule`이었고, `uv run python tools/sibling_overlap.py`가 "번호 겹침 없음"이었다.
- 반영과 티켓 done(마지막 수용 기준 표시)을 `d6f9c51f`로 커밋했다. pre-commit은 ruff 둘, lint-imports, zizmor, check-ticket, check-instructions, check-type-escapes, pyright 둘, run-hooks(368.3초), web-verify(772.9초), pytest(913.2초), 표, 줄 구분 문자, 변이 표, 인용, 커밋 메시지가 `Passed`였다. 카나리아 명세 모양과 헌법 판은 스테이지된 해당 파일이 없어 `Skipped`였다. 이 세션은 `SKIP`을 쓰지 않았다.
- 그 커밋에서 `hook_handoff`가 세션 컨텍스트 246,042 토큰으로 경계 `커밋 뒤`를 알렸다. 이 세션의 지시문의 이어받을 상태가 `인계: 커밋 뒤`로 시작해(같은 경계에 다시 왔다) next-session "인계할 때" 1대로 넘기지 않고 이었다.
- 푸시하고 PR #390을 열었다(`gh pr create --body-file`). 앱의 PR 바가 이 세션에 묶었다(`get_status`의 `bound: true`). 연 직후 검사는 통과 2, 대기 6이었다.

### 인계 (PR 연 뒤)

PR을 연 명령에서 `hook_handoff`가 세션 컨텍스트 267,118 토큰으로 경계 `PR 연 뒤`를 알렸다. PR이 열렸고, 요청 범위는 PR과 병합까지이며, 이 세션의 지시문의 이어받을 상태(`인계: 커밋 뒤`)는 같은 경계가 아니고, 이 세션이 쓴 `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이 아니다. 그래서 넘긴다. 함께 온 `hook_pr_next_session`의 계기보다 인계 줄이 앞선다. `@coderabbitai review` 코멘트는 남기지 않았다(새 세션 몫). 이 세션의 지금 제목은 `chore/015-probes-marker-rule`이고, 넘기기 전에 `chore/015-probes-marker-rule (인계함)`으로 바꾼다.

이 절과 바로 위 "커밋과 PR" 절은 커밋하지 않았다. 새 세션이 봇 회차의 커밋에 싣는다.

지시문:

```
다음 작업: .scratch/harness/issues/015-probes-marker-rule.md. .claude/rules/probes.md 첫 항목에, 고친 길을 지났다는 표지는 다른 해석 아래에서는 나지 않는 관찰로 정한다는 일반 조항을 더한다(대기열 367)
다음 단계: PR 반영·병합
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다
브랜치: chore/015-probes-marker-rule
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-04-probes-marker-rule.md
이어받을 상태: 인계: PR 연 뒤. PR #390을 d6f9c51f로 열었다(PR 직전 리뷰 반영과 티켓 done까지 든 커밋, pre-commit 전부 통과). 순서 1의 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. 일지에 커밋하지 않은 셋째 세션 끝의 두 절(커밋과 PR, 인계)이 있어 병합 전에 봇 회차의 커밋에 싣는다. 형제 PR #388이 같은 규칙 첫 항목을 고쳐, 늦게 병합하는 쪽에서 글자 충돌을 풀고 두 문장이 남았는지 본 뒤 카나리아 둘(probes_rule_marker_other_reading.toml, probes_rule_stream_delete_marker.toml)을 --preflight로 다시 본다. 일지 docs/journal/2026-10-26-04-probes-marker-rule.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/015-probes-marker-rule (인계함)`으로 바꿨다. 돌던 백그라운드 작업은 없었다. `git worktree unlock C:/project/agent/.claude/worktrees/015-probes-marker-rule`은 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-10-26T11:20:13Z

## 봇 회차와 병합 (넷째 세션)

> 사용자: (인계 지시문을 첫 메시지로 받았다) "대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다 / … / 다음 단계: PR 반영·병합 / … / 이어받을 상태: 인계: PR 연 뒤. PR #390을 d6f9c51f로 열었다(PR 직전 리뷰 반영과 티켓 done까지 든 커밋, pre-commit 전부 통과). 순서 1의 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. … / 확인할 선행 조건: 없음 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. `git worktree list`에서 `chore/015-probes-marker-rule`은 `.claude/worktrees/015-probes-marker-rule`(`d6f9c51f`)이라 `EnterWorktree(path)`로 들어갔다. 커밋하지 않은 것은 이 일지의 셋째 세션 끝 두 절이었다.
- `git fetch origin` 뒤 `git log 92b61458..origin/main`이 비었다. 형제 PR #388은 아직 열려 있다.

### claude-review 첫 회차 (`d6f9c51f`)

CodeRabbit은 아직 요청하지 않아 "Review skipped: manual review required"였다. claude-review가 Critical·Major 0, Minor 1, Nit 1을 냈다.

- Nit(고쳤다): `passed_past_first_window`의 틈을 규칙 본문과 `mutate_ctrl_c.py` 독스트링이 둘 다 적는다. 한 뜻을 한 곳에 두려고 규칙 쪽은 "그보다 느슨하다"와 까닭 한 구절만 남기고 세부는 그 독스트링을 가리키게 줄였다. 세부를 독스트링에 둔 것은 그 셈을 짓는 코드 바로 위라 셈을 바꿀 때 함께 고치기 때문이다.
- Minor(보류): 첫 항목이 지침 문장, 사례, 일반 조항을 한 불릿에 담아 길다. 이 규칙이 이미 그 꼴이고(셀프 리뷰의 판단 항목, PR 본문의 리뷰어 참고), 나누면 형제 PR #388이 고치는 같은 줄과 겹치며 두 카나리아의 조각 자리가 함께 움직인다. 두 PR이 병합된 뒤의 일로 넘기고 "다음"에 적는다.

다시 돌린 것: 고친 곳이 규칙 본문뿐이고 claude 판·명세의 칸·`expect`가 그대로라 `uv run python tools/canary.py --preflight`로 갈음했다. `probes_rule_marker_other_reading.toml` 통과 1, 같은 규칙의 `probes_rule_stream_delete_marker.toml`도 통과 1. 앞의 명세의 `# 최신 결과:` 줄에 셋째 세션과 이 세션의 갈음을 덧붙였다(셋째 세션은 일지에만 적었다).

### main 합치기

회고에서 친 `uv run python tools/sibling_overlap.py`가 origin/main을 `9805a5a`로 적었다. 시작 때의 fetch 뒤에 형제 013(#389)이 병합됐다. 겹친 파일은 `.scratch/retro-queue.md` 하나였고(#389는 456행만 닫았다) `git merge --no-edit origin/main`이 충돌 없이 끝났다. 이 저장소는 `pre-merge-commit` 훅을 깔지 않아 병합 커밋에서는 commit-msg 검사만 돌았다.

## 회고

후보 다섯. 승인 둘(둘 다 대기열에 둔다), 기각 셋, 넘김 없음.

1. 기각(306의 받아들인 종류, 일지에만). 나란히 여는 여덟이 함께 돌던 동안 이 티켓의 커밋이 pre-commit의 pytest에서 세 번 막혔다(1141.1초, 844.0초, 1195.8초). 빨간 시험은 모두 이 브랜치가 건드리지 않은 시간 시험이었고, CPU 100%가 45분 동안 내려가지 않아 `SKIP=pytest`로 빼고 한 프로세스 pytest를 손으로 쳤다(4421.92초). 한 문단짜리 규칙 고침에 벽시계로 세 시간 넘게 들었다. 대기열 306이 받아들여 닫은 종류(부하에서 시간 시험이 빨개지면 다시 친다)의 새 사례라 회차를 더하지 않는다. 다만 이번에는 다시 쳐도 형제들의 부하가 이어져 수렴하지 않았다. `tools/run_checks.py` 독스트링이 "세션 둘이 같은 시각에 커밋하면 … 잠금은 두지 않았다"고 적는 틈이 그 까닭이다. 그 종류를 다시 열지는 사용자가 정한다.
2. 승인(더하는 것, 1회차). 셋째 세션이 PR 직전 리뷰 반영 뒤 카나리아를 `--preflight`로 갈음하고 일지에만 적었고, 명세의 `# 최신 결과:` 줄에 덧붙이지 않았다(`docs/constitution/operations.md` 카나리아 항목). 이 세션이 명세를 열어서야 알고 덧붙였다. 층은 갈음하는 순간에 그 명령의 출력이 알리는 것이 가장 높다. 문턱 전이라 대기열 473(1회차)에 둔다.
3. 승인(고침, 대기열에 둔다). `.claude/rules/probes.md` 첫 항목이 지침, 일반 조항, 사례 다섯을 한 불릿에 담아 길다. 셀프 리뷰의 판단 항목과 claude-review Minor가 같은 자리를 짚었다. 형제 #388이 같은 줄을 고치고 있어 지금 나누면 충돌이 커지고 두 카나리아의 조각 자리가 함께 움직여, 두 PR이 병합된 뒤의 일로 대기열 474(1회차)에 둔다.
4. 기각(사건 미확인). 첫 세션의 일지에 규칙을 고치기 전 `writing-for-agents`를 부른 기록이 없다고 셀프 리뷰가 적었다(`.claude/rules/agent-docs.md`). 기록이 없을 뿐 부르지 않았는지는 확인하지 못했고, 둘째 세션이 고치기 전에 불러 새 문장을 다시 봤다.
5. 기각(원인을 가리지 못했다). 한 문단 고침이 세션 넷(인계 셋)으로 이어졌다. 인계는 ADR 0033대로 돌았고, 첫 세션이 셀프 리뷰 전에 21만 토큰을 어디에 썼는지는 이 세션이 그 기록을 보지 않아 가리지 못했다. 둘째 세션의 30만 토큰은 위 1의 pytest 세 번과 기다림이 컸다.

`uv run python tools/queue_open_rows.py`와 `--ref origin/main`(fetch 뒤) 모두 만료할 행이 없었다. 새 훅·검사가 문턱을 지난 것이 없어 `tools/hook_report.py`는 돌리지 않았다.

## 다음

- 대기열 474(`.claude/rules/probes.md` 첫 항목 나누기)는 이 PR과 형제 #388이 모두 병합된 뒤의 일이다. 그 행의 카나리아를 다시 돈다.
- 형제 #388이 이 PR보다 늦게 병합되면 그쪽이 첫 항목의 글자 충돌을 풀고, 두 문장이 남았는지 본 뒤 카나리아 둘(`probes_rule_marker_other_reading.toml`, `probes_rule_stream_delete_marker.toml`)을 `--preflight`로 본다.
- 회고 1의 부하 비용(306의 받아들인 종류)을 다시 열지는 사용자가 정한다.

## 인계 (커밋 뒤, 넷째 세션)

- claude-review 첫 회차의 반영과 회고·다음을 `c68fd594`로 커밋했다. pre-commit은 병렬 검사 열(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks 153.7초, web-verify 482.3초, pytest 499.9초), 표, 줄 구분 문자, 변이 표, 카나리아 명세 모양, 인용, 커밋 메시지가 `Passed`였다. ruff 둘은 스테이지된 `.py`가 없어, 헌법 판은 고친 헌법 파일이 없어 `Skipped`였다. `SKIP`은 쓰지 않았다. 아직 푸시하지 않았다.
- 그 커밋을 띄운 명령에서 `hook_handoff`가 세션 컨텍스트 256,473 토큰으로 경계 `커밋 뒤`를 알렸다. 커밋은 성공했고, 요청 범위는 PR과 병합까지이며, 이 세션의 지시문의 이어받을 상태(`인계: PR 연 뒤`)는 같은 경계가 아니고, 이 세션이 쓴 `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션이 아니다. 그래서 넘긴다. 이 세션의 지금 제목은 `chore/015-probes-marker-rule`이고, 넘기기 전에 `chore/015-probes-marker-rule (인계함)`으로 바꾼다.
- 남은 단계: 이 인계 절을 새 세션의 시작 기록과 함께 커밋한 뒤 한 번에 푸시한다(일지만 따로 푸시하면 claude-review가 한 번 더 돈다). 푸시 전에 PR 본문을 넓힌다(순서 1의 1. 대기열 473·474, #389 합침, 첫 항목 길이의 보류, 체크리스트의 pytest 줄). 그 뒤 `@coderabbitai review`, 대기, 봇 회차, claude-review 첫 회차 Minor의 보류 이유 PR 코멘트, 병합(워크트리 길)이다.

지시문:

```
다음 작업: .scratch/harness/issues/015-probes-marker-rule.md. .claude/rules/probes.md 첫 항목에, 고친 길을 지났다는 표지는 다른 해석 아래에서는 나지 않는 관찰로 정한다는 일반 조항을 더한다(대기열 367)
다음 단계: PR 반영·병합
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다
브랜치: chore/015-probes-marker-rule
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-04-probes-marker-rule.md
이어받을 상태: 인계: 커밋 뒤. claude-review 첫 회차(d6f9c51f)의 Nit을 반영하고 origin/main(#389)을 합친 뒤 회고와 "다음"까지 실어 c68fd594로 커밋했다(pre-commit 통과). 아직 푸시하지 않았다. 일지 끝의 인계 절은 커밋하지 않았으니 새 세션의 시작 기록과 함께 커밋한 뒤 한 번에 푸시한다. 푸시 전에 순서 1의 1대로 gh pr edit으로 PR 본문을 넓힌다(대기열 473·474를 더했다, 리뷰어 참고의 첫 항목 길이는 대기열 474로 두었다, #389를 합쳤다, 체크리스트의 pytest 줄은 새 머리의 pre-commit). 그 뒤 순서 1의 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트는 아직 없다. claude-review 첫 회차의 Minor(첫 항목이 길다)를 보류한 이유를 PR 코멘트로 남긴다(일지의 "claude-review 첫 회차" 절). 형제 #388과의 첫 항목 충돌은 일지 "다음". 일지 docs/journal/2026-10-26-04-probes-marker-rule.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/015-probes-marker-rule (인계함)`으로 바꿨다. 돌던 백그라운드 작업은 없었다. `git worktree unlock C:/project/agent/.claude/worktrees/015-probes-marker-rule`은 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-10-26T11:41:56Z

## 봇 회차와 병합 (다섯째 세션)

> 사용자: (인계 지시문을 첫 메시지로 받았다) "대기열 367을 티켓 .scratch/harness/issues/015-probes-marker-rule.md로 쓰고 한다 / … / 다음 단계: PR 반영·병합 / … / 이어받을 상태: 인계: 커밋 뒤. claude-review 첫 회차(d6f9c51f)의 Nit을 반영하고 origin/main(#389)을 합친 뒤 회고와 "다음"까지 실어 c68fd594로 커밋했다(pre-commit 통과). 아직 푸시하지 않았다. … / 확인할 선행 조건: 없음 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. `git worktree list`에서 `chore/015-probes-marker-rule`은 `.claude/worktrees/015-probes-marker-rule`(`c68fd594`)이라 `EnterWorktree(path)`로 들어갔다. 커밋하지 않은 것은 이 일지의 넷째 세션 끝 인계 절이었다.
- `git fetch origin` 뒤 `git log HEAD..origin/main`이 비었다(origin/main은 합친 `9805a5a7` 그대로다). 형제 PR #388은 아직 열려 있다.
- 순서 1의 1대로 푸시 전에 `gh pr edit`으로 PR 본문을 넓혔다(대기열 473·474, #389 합침, 리뷰어 참고의 첫 항목 길이는 대기열 474, 체크리스트의 pytest 줄은 `c68fd594`의 pre-commit).
