# 2026-10-20 (25) 원문 교환이 50개를 넘으면 접고, 거슬러 읽기는 100개에서 멈추며, 이어 가기의 판정은 스레드 하나에서 돈다

end-user-continuation 티켓 04의 구현 세션이다. 03 세션이 병합 뒤 연 04 세션은 다른 워크트리 폴더에 열려 첫 턴에 멈춰,
06 세션의 일지 "다음"이 낸 지시문으로 새로 열렸다. 주 체크아웃 미갱신이라 `tidy-checkouts`를 먼저 돌았다.

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/end-user-continuation/issues/04-exchange-count-read-cap-and-thread.md"

그 뒤에 붙은 지시문 원문:

```
다음 작업: .scratch/end-user-continuation/issues/04-exchange-count-read-cap-and-thread.md. 교환 수와 상한과 스레드. 짧은 말이 수백 번 쌓여도 한 번에 읽는 실행이 묶이고, 이어 가기의 거슬러 읽기가 서버를 멈추지 않는다
다음 단계: 구현
어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/04-exchange-count-read-cap-and-thread.md
브랜치: feature/04-exchange-count-read-cap-and-thread
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 나란히 도는 티켓 02·05(.scratch/end-user-continuation/issues/), docs/journal/2026-10-20-16-admin-shows-cause-and-shortcut-links.md의 "다음"
이어받을 상태: 03 세션이 병합 뒤 연 04 세션(앱 제목 "교환 수 읽기 상한과 스레드")은 다른 워크트리 폴더에 열려 첫 턴에 멈췄고 브랜치를 따지 않았다. 그 세션은 쓰지 않는다
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

이 세션의 지금 제목: `feature/04-exchange-count-read-cap-and-thread`. 구현 도중 컨텍스트가 한 번 압축되었다.

## 정리

`tidy-checkouts`가 주 체크아웃을 `911babc0`에서 `2d460f6b`로 당겼다. 지운 워크트리와 브랜치는 없다. 사람에게 넘긴 것은
셋이다(보고만 하고 기다리지 않았다). `confident-wright-2d3ebf`와 `elegant-dijkstra-aaddb9`는 분리 HEAD이고 그 커밋이
`origin/main`에 없다. `skill-check-and-retro-section`은 병합된 PR의 머리가 브랜치 끝과 다르다.

## 결정

- 값은 core가 든다. `EXCHANGE_COUNT_LIMIT = 50`과 `READ_CAP = 100`을 `core/continuation.py`의 기본 대화 한도 옆에 두었다.
  매니페스트 필드가 아니다.
- 요약의 계기는 글자 수가 한도를 넘거나(`over_size`) 원문 교환이 50개를 넘는 것이다. 꼬리는 가장 최근부터 합이 한도의
  절반을 넘지 않고 수가 25개를 넘지 않는 데까지다. 목표 글자 수는 교환 수로 접혀도 한도의 4분의 1을 올림한 값이다.
- 읽은 수를 세는 자리. 옛 대화의 `_walk`는 부르는 쪽이 읽은 앞 실행을 1로 세고 시작한다. 이어 가기와 재개가 같은 앞
  실행부터 같은 수를 세어 같은 자리에서 멈춘다. 바로가기의 `_follow`는 이어 가기에서 이미 읽은 앞 실행(`known`)을 1로
  세고, 재개에서는 실제로 읽은 것만 센다. 재개 쪽이 상한에 닿을 만큼 모은 이어 가기는 교환 수 기준을 넘겨 접혔으므로,
  그 재개는 자기 요약의 덮는 끝에서 상한보다 먼저 멈춘다.
- 상한의 자리는 읽지 않고 가를 수 있는 판정(처음, 순환, 덮는 끝) 뒤, 읽기 바로 앞이다. 그 판정의 깨짐은 상한에 닿아도
  깨짐이다.
- `run()`이 `gather_continued` 전부를 `anyio.to_thread.run_sync` 한 번으로 부른다. 인자는 기본값 그대로라 취소가 오면
  읽기가 끝나기를 기다리고(`abandon_on_cancel=False`), 제한기도 anyio의 기본(동시 40개)이다. 재개의 거슬러 읽기는 루프
  위에 남는다(ADR 0014의 첫 걸음 불변식).
- 스레드 테스트의 가짜 트레이스(`BlockingTrace`)는 막은 읽기마다 그동안 박동이 뛰었는지를 따로 쌓는다. 그래서 읽기마다
  막는 가짜 하나가 두 부분 구현(고리만 스레드로 보낸 것, 앞 실행 읽기만 보낸 것)을 모두 잡는다. 티켓이 요구한 앞 실행에서만
  막는 가짜는 고리만 보낸 구현만 잡는다. 변이 표가 둘을 나눠 고정한다.
- 취소 테스트는 가짜가 읽기를 시작했다는 표시(`threading.Event`)를 본 뒤 바깥 범위를 취소하고, 그 뒤 0.2초에 읽기를 풀어
  준다. 취소가 읽기 앞이나 뒤에 오는 회차가 없다.

## 변이와 카나리아

- 새 변이 표 `.scratch/end-user-continuation/probes/walk_cap_mutations.toml` 18개. 첫 실행은 16개 모두 기대한 색이었고 어긋난
  셋은 표지 탓이었다. 1번은 pytest가 목록 차이를 `At index 1 diff`로 찍었고, 매개변수 둘을 `-k` 하나로 고른 두 변이는
  pytest가 첫 실패에서 멈춰 뒤의 매개변수가 돌지 않았다. 그 둘을 노드 식별자로 나눠 18개가 되었다. 재개와 취소 변이의 첫
  표지는 실패한 단언 둘레의 코드 조각에도 실리는 문구라, 없는 표지를 달아 실패 출력을 본 뒤 그 단언에서만 나오는 문구로
  바꿨다. 고친 아홉을 다시 돌려 모두 기대대로였다.
- 이 변경이 다른 표의 원문 여섯을 썩혔다. `.scratch/conversation/probes/continuation_mutations.toml`의 다섯(덮는 끝, 준비
  순서, 한도와 같음, 요약 글을 세지 않음, 긴 마지막 교환)과 `shortcuts_mutations.toml`의 하나(앞 실행을 다시 읽지 않음)다.
  새 모양으로 고치고 `--since origin/main`으로 그 여섯을 돌려 모두 기대대로 빨갰다. 같은 `--check`가 알린 나머지는
  `.scratch/web-admin/probes/pause_index_mutations.toml` 여덟(`run.py` 다섯, `router.py` 셋)과 end-user-channel 표 둘의 다섯
  (`end_user.py`)이다. `router.py`와 `end_user.py`는 이 브랜치가 고치지 않았다. `run.py`를 가리킨 다섯이 main에서 이미
  썩었는지는 확인하지 않았다(커밋의 pre-commit `--staged`가 이 커밋이 깬 원문만 알린다).
- 고친 판의 두 변이 실행(conversation, shortcuts)을 한 메시지에 나란히 보내 같은 `continuation.py`를 두 실행이 함께 고쳤을
  수 있었다. 끝난 뒤 소스에 변이가 남지 않았는지 grep으로 보고 `tests/core/test_run.py`를 다시 돌려 279 passed를 봤다.
- 카나리아 `.scratch/end-user-continuation/probes/canary/core_rule_read_cap_thread.toml` 통과 4(claude 2.1.302). 실험군이
  `READ_CAP`, `EXCHANGE_COUNT_LIMIT`, `abandon_on_cancel=False`를 3/3 옮겼고 대조군은 "없음"이었다.

## 검사(셀프 리뷰 전)

- `tests/core/test_run.py` 279 passed. `uv run ruff check .`와 `uv run ruff format --check .` 종료 0.
- `uv run --env-file ../../../.env pytest -m llm -q`: 7 passed, 3820 deselected(307.10초). LLM 토큰 합계 54,986(입력
  53,819, 출력 1,167). 트레이스 10개, 모델 호출 22건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다. 최종 사용자
  경로의 이어 가기 LLM 테스트가 든다(티켓의 바깥 이음매).
- `uv run python tools/run_checks.py`(백그라운드) 종료 0: zizmor, check-instructions, lint-imports, check-type-escapes,
  pyright, run-hooks(76.2초), web-verify(304.0초), pytest(388.4초) 모두 Passed. 그 뒤에 고친 것은 일지와 티켓뿐이다.

## 셀프 리뷰 직전에 인계

`/code-review`를 부른 순간 인계 계기가 왔다(세션 컨텍스트 306,383 토큰). 곁 세션이 아니다(`get_session` self에
`parentSessionId` 없음). 리뷰의 단계는 밟지 않았고 새 세션이 한다. 이 세션의 제목은 인계 직전에
`feature/04-exchange-count-read-cap-and-thread (인계함)`으로 바꾼다.

인계 지시문:

```
다음 작업: .scratch/end-user-continuation/issues/04-exchange-count-read-cap-and-thread.md. 교환 수와 상한과 스레드. 짧은 말이 수백 번 쌓여도 한 번에 읽는 실행이 묶이고, 이어 가기의 거슬러 읽기가 서버를 멈추지 않는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/04-exchange-count-read-cap-and-thread.md
브랜치: feature/04-exchange-count-read-cap-and-thread
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 일지 docs/journal/2026-10-20-25-exchange-count-read-cap-and-thread.md(커밋하지 않았다. 워크트리에 있다)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`, base는 origin/main의 merge-base)부터 한다. 구현·테스트·변이 표 18개·다른 표 원문 여섯의 고침·카나리아·-m llm(7 passed)은 마쳤고 티켓은 done으로 고쳤다. 비워 둔 체크박스 둘(검증 명령, 병합 직전 판정)은 새 세션이 채운다. 리뷰 전의 run_checks와 린트 둘은 초록이었고(일지 검사 절), 리뷰 반영 뒤의 다섯은 커밋의 pre-commit으로 갈음한다. walk_cap_mutations.toml의 전체 실행은 리뷰를 반영해 커밋한 뒤에 한 번 돈다. --check가 알린 pause_index 표의 run.py 원문 다섯이 main에서 이미 썩었는지는 확인하지 않았다. 일지 docs/journal/2026-10-20-25-exchange-count-read-cap-and-thread.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 바꿨고, 이 세션이 띄운 백그라운드 작업(변이, 카나리아, `-m llm`, `run_checks`)은 모두 끝나 멈출 것이 없었으며,
`git worktree unlock C:/project/agent/.claude/worktrees/04-exchange-count-read-cap-and-thread`가 오류 없이 끝났다.

open-session을 부른다 2026-10-20T05:55:58Z

## 이어받은 세션

> 사용자: ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/end-user-continuation/issues/04-exchange-count-read-cap-and-thread.md"

그 뒤에 붙은 지시문은 위 인계 지시문과 같다. 제목을 `feature/04-exchange-count-read-cap-and-thread`로 바꾸고
`git worktree list`에서 그 브랜치의 워크트리를 찾아 `EnterWorktree(path)`로 들어왔다. `origin/main`은 `2d460f6b`
그대로라 merge-base가 같다.

인계가 남긴 미확인 하나를 닫았다. `pause_index_mutations.toml`의 원문 가운데 `--check`가 알린 여덟(`run.py` 다섯,
`router.py` 셋)은 `origin/main`의 소스에도 0번 있다(스크래치패드 스크립트가 표의 `old`를 `git show origin/main:<경로>`에서
셌다. `cli/main.py`의 셋은 1번). 그 표는 이 브랜치 전부터 썩어 있었고 이 브랜치가 깬 것이 아니다.

## 셀프 리뷰

`/code-review`, base `2d460f6b`(origin/main의 merge-base), 추적 파일 9개 변경과 미추적 3개, 커밋 0개. 명세는 티켓 04와
end-user-continuation 명세. 표준 축은 sonnet·high, 명세 축은 이 세션의 모델을 물려받았다.

표준 축(6): Major 1 — `plan.md` conversation 행에 "긴 고리가 `serve`의 이벤트 루프를 막는 것은 알려진 한계다"가 남았다
(`operations.md` 문서 위치 절은 `plan.md`를 살아 있는 문서로 든다. 티켓의 "plan.md의 done인 conversation 행 따위"가 그
절을 잘못 읽었다). Minor 4 — `_next_link(..., *, capped: bool)`이 `CODING_STANDARDS.md`의 불리언 플래그 기준에 걸린다,
"상한에 닿는 것은 옛 대화뿐"에 이 diff 자신의 테스트(03과 04 사이의 바로가기 대화)가 반례다, "0.5초 안팎"에 작은
트레이스로 잰 값이라는 단서가 빠졌다, 01 티켓의 "(03·04가 묶는다)". Nit 1 — 비운 체크박스 둘, 카나리아 결과가 리뷰 전의
판, 모듈 독스트링 첫 줄에 교환 수가 없다. 확인한 것: 세 표의 `--check`, `plan_fold` 무작위 16,482건, 바로가기 읽기 최대
52(실제 `run()` 200번), anyio 4.15.1의 기본값 둘, 판정 순서.

명세 축(5): Minor 3 — "재개는 루프 위다"의 근거로 든 `tests/test_server.py`의 `disk_seconds`는 켜고 끄기 테스트이고
`test_router.py`의 동시 재개는 이어 가지 않은 실행이라, 이어 간 실행의 재개에만 await를 넣는 구현이 초록이다; "옛 대화뿐"
(표준 축과 같다, 재개의 단서에도 같은 틈); 상한에 닿으면 "새 요약은 언제나 앞 요약을 접어 만들어진다"(`continuation.py`)와
sdk의 두 문장(`events.py`의 주석, `Conversation` 독스트링)이 거짓이 된다(옛 고리 150개 탐침으로 재현). Nit 2 — `plan.md`
(표준 축과 같다), 프로브 README의 "18 모두 기대대로"가 한 번에 돈 결과가 아니다. 범위 밖 없음.

고친 것:
- `_next_link`를 읽지 않는 판정 `_older_run(link, summary, visited) -> RunId | None`으로 줄이고 상한과 읽기를 `_walk`로
  올렸다. 순서(처음 → 순환 → 덮는 끝 → 상한 → 읽기)는 그대로이고 `_follow`와 같은 모양이 됐다.
- core 테스트 `test_이어_간_실행에_동시에_온_결정_둘은_하나만_받아들여져_도구가_한_번_불린다`를 더했다. 변이 표에 둘을
  더했다 — 이어 간 실행의 재개에만 `await anyio.to_thread.run_sync(...)`을 넣으면 새 테스트가 빨갛고(19번) 채널의 동시
  재개 테스트는 초록이다(20번, 초록 기대).
- 새로 쓴 사실 문장(PR 직전 `bug-perf-review`에 밀 주장):
  - `continuation.py` 모듈 독스트링: "새 요약은 만난 가장 가까운 요약을 접어 만들어진다. 읽기 상한(아래)에 닿아 그 요약을
    만나지 못한 대화에서는 상한 너머의 요약과 교환이 새 요약에 들지 않는다."
  - `EXCHANGE_COUNT_LIMIT` 주석과 `core.md`: "그 수는 이벤트 다섯의 작은 트레이스로 잰 것이라, 도구 결과가 큰 트레이스가
    이어지는 대화의 재개는 그 예산을 넘을 수 있다(명세의 어림)."
  - `READ_CAP` 주석, `core.md`, 테스트 절 머리, `plan.md` end-user-continuation 행, 명세 230행 주석, 티켓 3행: "닿는
    것은 옛 대화와, 교환 수 기준이 서기 전(티켓 03과 04 사이)에 쓰인 바로가기 대화뿐이다."
  - `core.md` 재개 단서: "상한을 들이기 전에 멈춘 실행 가운데 읽을 실행이 100개를 넘는 것 — 옛 대화와 티켓 03과 04 사이의
    바로가기 대화 — 은 재개 대조로 실패할 수 있고"
  - `core.md` 재개 항목: "그 테스트는 이어 가지 않은 실행을 재개해 거슬러 읽기를 지나지 않으므로, 이어 간 실행의 거슬러
    읽기만 스레드로 보내는 변경은 `tests/core/test_run.py`의 이어 간 실행 동시 재개 테스트가 깬다."
  - `sdk/events.py` 주석: "새 요약은 거슬러 읽기가 만난 가장 가까운 요약을 접어 만들어지므로 시작은 그 에이전트의 첫
    교환이다. 거슬러 읽기가 읽기 상한(core)에 닿아 멈춘 적이 있는 대화는 그 상한 너머가 빠진다."
  - `sdk/conversation.py` 독스트링: "런타임이 거슬러 읽는 실행의 수에 상한을 두므로, 그 상한에 닿은 긴 대화에서는 상한이
    멈춘 자리부터다."
  - `plan.md` conversation 행: "긴 고리가 `serve`의 이벤트 루프를 막던 한계는 end-user-continuation 티켓 04가
    닫았다(이어 가기의 거슬러 읽기는 스레드, 읽는 실행 수에 상한)."
- 모듈 독스트링 첫 줄, 티켓의 구현 메모 둘, 명세 321행 주석, 두 프로브 README의 결과 줄.
- 변이: `--check`로 세 표가 모두 한 번씩이다. 원문을 고친 walk_cap 6·7과 새 19·20, conversation 표의 `--since
  origin/main` 다섯을 돌려 모두 기대대로였다(19번은 처음 단 표지가 pytest가 줄여 찍은 목록과 맞지 않아 차이 줄로 바꿔 다시
  돌렸다).

남긴 것:
- 01 티켓 11행 "(03·04가 묶는다)": "병합 뒤에 틈이 있다" 문단 안에서 틈이 있던 동안을 말하고, 그 틈을 묶는 티켓을 든
  문장이라 지금도 참이다. 04의 요구는 01·03이 코드와 문서에 쓴 미래형 문장이고 티켓 파일 자신이 아니다(01 티켓 94행
  "뒤 티켓이 `02`~`06`·`틈`으로 grep해 다시 읽는다"가 가리키는 것은 그 티켓이 쓰는 문장이다).
- 비운 체크박스 둘은 커밋 뒤와 병합 직전에 채운다. 카나리아는 `core.md`를 고쳤으므로 커밋 뒤 다시 돈다.

다시 돌린 것(커밋 전): `tests/core/test_run.py`와 `tests/sdk` 353 passed, 바꾼 넷의 pyright 0 errors, ruff check·format
초록. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

## 커밋

리뷰 반영을 한 커밋으로 넣었다(16 files). 첫 시도는 commit-msg 훅이 제목 길이(72자 초과)로 막아 제목을 줄였다.
pre-commit은 ruff check·format, checks(lint-imports, zizmor, check-instructions, check-type-escapes, pyright 29.6초,
run-hooks 84.5초, pytest 229.6초, web-verify 264.1초), markdown tables, line separators, mutation tables(`--staged`),
canary specs, commit message가 모두 Passed다. constitution version은 헌법 파일을 고치지 않아 `Skipped`(no files)다.
quotes는 경고 2건이다. 이 일지 셀프 리뷰 절의 두 인용("긴 고리가 …알려진 한계다", "새 요약은 언제나 …")은 리뷰가 고쳐
지운 옛 문장이라 저장소에 없는 것이 맞다. 그래서 손으로 치는 다섯은 이 pre-commit으로 갈음됐다.

## 커밋 뒤에 인계

커밋이 끝나자 인계 계기가 왔다(세션 컨텍스트 354,623 토큰, 경계 `커밋 뒤`). 이 세션의 지시문은 `인계: 셀프 리뷰 직전`이라
경계가 다르고, 요청 범위는 PR과 병합까지이며, 곁 세션이 아니다(`get_session` self에 `parentSessionId` 없음). 이 브랜치에
열린 PR이 없어 다음 단계는 이 세션의 지시문 값(구현)을 옮긴다. `tools/model_sweep.py`는 `Opus 5.5 / xhigh`를 냈다. 이 세션의
지금 제목은 `feature/04-exchange-count-read-cap-and-thread`이고 인계 직전에 `(인계함)`을 붙인다.

인계 지시문:

```
다음 작업: .scratch/end-user-continuation/issues/04-exchange-count-read-cap-and-thread.md. 교환 수와 상한과 스레드. 짧은 말이 수백 번 쌓여도 한 번에 읽는 실행이 묶이고, 이어 가기의 거슬러 읽기가 서버를 멈추지 않는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/end-user-continuation/issues/04-exchange-count-read-cap-and-thread.md
브랜치: feature/04-exchange-count-read-cap-and-thread
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: 일지 docs/journal/2026-10-20-25-exchange-count-read-cap-and-thread.md(셀프 리뷰 절의 "새로 쓴 사실 문장", 커밋 절. 끝의 "커밋 뒤에 인계" 절은 커밋하지 않아 워크트리에만 있다)
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰(두 축)와 그 반영을 커밋까지 마쳤고 pre-commit은 모두 초록이다(손으로 치는 다섯은 갈음됨). 남은 단계는 차례로 (1) walk_cap_mutations.toml 20개 전체 실행(리뷰 반영 뒤에는 6·7·19·20만 돌렸다), (2) core.md를 고쳤으므로 카나리아 core_rule_read_cap_thread.toml 다시 돌기, (3) 티켓의 "검증 명령" 체크박스 채우기(pre-commit 결과와 -m llm 7 passed가 일지에 있다), (4) origin/main 합치기, (5) PR 직전 리뷰에 일지 셀프 리뷰 절의 "새로 쓴 사실 문장"을 밀 주장으로 넘기기, (6) PR, 봇 회차, 병합 직전 판정 체크박스, 워크트리 길로 병합, next-session이다. 셀프 리뷰가 남긴 지적 하나(01 티켓 11행)의 이유는 일지에 있다. 일지 docs/journal/2026-10-20-25-exchange-count-read-cap-and-thread.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 바꿨고, 이 세션이 띄운 백그라운드 작업은 끝난 커밋뿐이라 멈출 것이 없었으며,
`git worktree unlock C:/project/agent/.claude/worktrees/04-exchange-count-read-cap-and-thread`는 `is not locked`로
끝났다(넘어간다).

open-session을 부른다 2026-10-20T06:41:59Z

`tools/open_session.ps1 -Action send`가 `page=` 뒤에 멈췄다. 새 세션 화면이 앱의 마지막 폴더인
`C:\project\agent\.claude\worktrees\skill-listing-budget`(같은 때 돌던 `chore/skill-listing-budget` 세션의 워크트리)로 열려
그 폴더의 신뢰 대화상자가 떴고, 스크립트는 루트가 아닌 폴더를 수락하지 않아 보내지 않았다(`sent=` 없음, 세션은 생기지
않았다). 제목을 `feature/04-exchange-count-read-cap-and-thread`로 되돌렸고, 이 세션에서 `커밋 뒤`의 다음 단계를 잇는다.

인계 못함 커밋 뒤

## 커밋 뒤

- `walk_cap_mutations.toml` 전체 실행(커밋 `2a4ce5b0`): 변이 20 모두 기대대로. 15·20은 초록 기대대로 초록이고, 나머지
  열여덟은 표지까지 맞았다. 끝난 뒤 작업 트리에 변이가 남지 않았다(`git status --porcelain`).
- 카나리아 `core_rule_read_cap_thread.toml`(claude 2.1.302, 커밋 `2a4ce5b0`): 통과 4. 실험군 3/3이 `READ_CAP`,
  `EXCHANGE_COUNT_LIMIT`, `abandon_on_cancel=False`를 옮겼고 대조군은 "없음"이었다. 명세의 `# 최신 결과:` 줄과 프로브
  README의 walk_cap 결과 칸을 고쳤다.

## main 합치기

`origin/main`이 `ed111753`(#320 skill-listing-trim, #321 티켓 05)으로 움직여 합쳤다. 충돌은 넷이고 모두 이웃한 자리를
양쪽이 따로 고친 글자 충돌이었다. 양쪽이 바꾼 단어를 `git diff --word-diff=porcelain <merge-base> <쪽>`으로 본 뒤 풀었다.
- `tests/core/test_run.py`: 같은 모듈의 import 둘을 한 줄로 합쳤다.
- `.scratch/plan.md`: conversation 행은 이 브랜치 판(알려진 한계를 닫은 문장), end-user-channel 행은 main 판(05의 좁힘
  괄호), end-user-continuation 행은 main 판에 이 브랜치의 고침("와 기준이 서기 전에 쓰인 바로가기 대화")을 얹었다.
- `.scratch/conversation/probes/README.md`: 두 티켓의 문단을 모두 남기고 05를 앞에 두었다.
- `.claude/rules/core.md`: 이어 가기 항목은 이 브랜치 판, 실패 정책 항목은 main 판이다. 푼 결과가 HEAD와는 main의 고침만,
  main과는 이 브랜치의 단어 변경 20개만 다른 것을 다시 봤다.

05의 `before_principal()`이 `gather_continued`의 첫 읽기를 감싸, 합친 판에서는 그 감싸개가 스레드 안에서 돈다. 스레드의
예외가 그대로 올라오므로 타입이 바뀌지 않는다. 합친 판에서 `tests/core/test_run.py`·`tests/channel/http/test_end_user.py`·
`tests/sdk` 439 passed, `mutate.py --check`로 표 넷(walk_cap 20, shortcuts 15, continuation 30, pre_owner_damage 8)의
원문이 모두 한 번씩, `pre_owner_damage_mutations.toml` 8개를 돌려 모두 기대대로 빨갰다. 합치기 커밋(`28a11976`)의
pre-commit은 ruff 둘, checks 여덟, markdown tables, line separators, mutation tables, quotes, commit message가 모두
Passed이고 canary specs와 constitution version은 고친 파일이 없어 `Skipped`다.

## PR 직전 리뷰

CodeRabbit CLI는 좌석이 없어 돌지 못하는 상태 그대로라(`operations.md` 리뷰 파이프라인 2) 대체 둘을 합친 뒤에 나란히
돌렸다. `bug-perf-review`의 브리프에는 셀프 리뷰 절의 "새로 쓴 사실 문장" 여덟과, 합친 판에서 감싸개가 스레드 안에서 도는
자리를 밀 주장으로 넣었다.

- `/security-review`(범위 `ed111753` 이후): 취약점을 찾는 서브태스크가 신뢰도 0.7 이상인 HIGH·MEDIUM 지적을 내지 않아
  거를 것이 없었다. 따라간 것은 스레드 뒤의 인가 순서(예외 타입이 그대로 `http/errors.py`의 표에 닿는다), 읽기 상한과
  주체 검사(교환을 모으는 실행은 모두 주체를 확인한 뒤), 워커 스레드의 읽기와 루프의 쓰기의 겹침(어댑터에 가변 공유 상태가
  없다)이다. 제한기 공유와 취소 때의 기다림은 가용성이라 제외 기준에 들었다.
- `-m llm`(합친 판 `28a11976`, `uv run --env-file ../../../.env pytest -m llm -q`): 7 passed, 3832 deselected(162.71초).
  LLM 토큰 합계 54,665(입력 53,620, 출력 1,045). 트레이스 10개, 모델 호출 22건. 트레이스를 남기지 않은 LLM 테스트 1개는
  세지 못했다. 셀프 리뷰의 리팩터링(`_older_run`)과 합치기 뒤의 판이라 다시 돌렸다.
- `coderabbit auth status`: `Plan: Free`, `Seat: not assigned`(PR마다 보는 확인).
- `bug-perf-review`(기준 `ed111753`, 16 파일, 호출 40): 유효 Minor 2, 오탐 5, Critical·Major 없음. 밀 주장 여덟 가운데
  2·3·4·5는 참이고(3은 옛 고리 99/100/101/150에서 읽기 99/100/100/100, 바로가기 고리는 읽기 52에서 접힘을 직접 불러
  봤다), 1·6·7은 글자 그대로는 참이되 아래 첫 지적의 변형이 빠졌고, 8이 둘째 지적이다. 합친 자리(`before_principal` +
  스레드)는 `anyio.to_thread.run_sync(gather_continued, …)`를 직접 불러 예외 타입이 그대로임을 봤다(앞 실행 손상은
  정확한 `TraceDamagedBeforePrincipal`, 고리 중간 손상은 정확한 `PluginError`). 오탐 다섯은 반쯤 쓴 줄(어댑터가 끝나지
  않은 마지막 줄을 아직 안 쓰인 것으로 읽는다), 취소의 자리, `_follow`의 이어 가기·재개 읽기 수 비대칭(티켓 04 뒤의
  데이터에서는 상한 전에 접히거나 멈춘다), `plan_fold` 경계, 상한의 하나 어긋남이다.
  - Minor 1 — 요약을 만났는데 그 덮는 끝에 닿기 전에 상한에 걸리면 덮는 끝과 멈춘 자리 사이의 교환이 요약에도 원문에도
    들지 않고, 접히면 영구히 빠진다(스크래치패드 프로브: 같은 에이전트 200개 옛 고리, r190의 요약이 r50까지 덮음,
    r199에서 이어 가기 → 요약과 r100~r199, r51~r99 빠짐). 동작은 명세가 받아들인 범위라 문장만 고쳤다. 반례를
    덧붙이지 않고 성질로 고쳤다. 상한이 멈춘 자리보다 오래된 교환 가운데 만난 요약이 덮지 않은 것이 빠진다는 성질이다. 처음에
    "오래된 것이 무엇이든 빠진다"로 썼다가, 만난 요약 자체는 새 요약에 접히므로 그 문장이 거짓인 것을 다시 대 보고
    바로잡았다.
  - Minor 2 — `plan.md` conversation 행의 "티켓 04가 닫았다"가 재개는 루프 위에 남는다는 명세·`core.md`와 어긋난다
    (명세 248행: 옛 대화의 재개는 첫 읽기로 0.6~0.9초, 어림). "묶었다"로 고치고 재개를 괄호에 넣었다.
- 반영으로 새로 쓴 사실 문장(PR 봇이 겨눌 자리):
  - `continuation.py` 모듈 독스트링과 `core.md` 이어 가기 항목: "읽기 상한(아래)에 닿은 대화에서는 상한이 멈춘 자리보다
    오래된 교환 가운데 만난 요약이 덮지 않은 것이 새 요약에 들지 않는다. 그 요약을 만나지 못했으면 상한 너머의 요약과
    교환이, 만났어도 그 요약이 덮는 끝에 닿기 전에 멈췄으면 그 사이의 교환이 빠지고, 그 뒤 계기가 서서 접히면 빠진 것은
    다시 읽히지 않는다."
  - `sdk/conversation.py` 독스트링: "그 상한에 닿은 긴 대화에서는 상한이 멈춘 자리보다 오래된 교환 가운데 거슬러 읽기가
    만난 요약이 덮지 않은 것이 이 값에 들지 않는다(그 뒤 접힌 새 요약에도 들지 않는다)."
  - `sdk/events.py` 주석: "거슬러 읽기가 읽기 상한(core)에 닿아 멈춘 적이 있는 대화는 그 상한 너머의 교환 가운데 만난
    요약이 덮지 않은 것이 빠진다."
  - `plan.md` conversation 행: "긴 고리가 `serve`의 이벤트 루프를 막던 한계는 end-user-continuation 티켓 04가
    묶었다(이어 가기의 거슬러 읽기는 스레드로 보내고, 루프 위에 남는 재개의 거슬러 읽기는 읽는 실행 수의 상한이 묶는다)."
- 반영 뒤: 고친 파이썬 셋의 ruff check·format 초록. `core.md`를 고쳐 카나리아를 다시 돌려 통과 4(커밋 `28a11976` 위의
  작업 트리). 손으로 치는 다섯은 이 반영 커밋의 pre-commit으로 갈음한다.

## PR

PR #323(https://github.com/njh6803/agent-os/pull/323)을 반영 커밋 `bd434631` 위에서 열었다. GitHub MCP의
`create_pull_request`는 확인 양식을 띄운다고 했으나 사용자 화면에 양식이 뜨지 않았다.

> 사용자: "안떠있는데"

그래서 `gh pr list --head`로 PR이 없는 것을 본 뒤, 제목과 본문을 JSON 파일로 만들어 `gh api repos/njh6803/agent-os/pulls
--method POST --input <파일>`로 열었다(제목의 공백을 셸 인자로 넘기지 않으려고). 연 직후 `@coderabbitai review`를 본문
파일로 남겼다. 첫 상태는 claude-review·e2e pass, CodeRabbit `Review rate limited`(요청 코멘트 전의 자동 판정),
python·web·visual pending이라 `tools/wait_ci.py 323`을 백그라운드로 띄웠다. 앱이 PR을 이미 묶어 `bind_pr`은 필요 없었다.
일지 267행의 따옴표 인용(인용 대조 경고)은 따옴표를 떼어 풀어 쓴 문장으로 바꿨고, 병합 전의 일지 커밋에 싣는다.

## 봇 회차

`tools/wait_ci.py 323`이 헤드 `bd43463`에서 종료 0으로 끝났다. python·web·e2e·visual·verify·claude-review 모두 SUCCESS이고
CodeRabbit은 요청 코멘트에도 `Review rate limited`였다(다음 리뷰는 48분 뒤라는 코멘트). claude-review의 첫 회차는 지적
없음이었다(경계와 유지보수성을 보고 `_older_run`의 판정·읽기 가름, 상한의 자리, 동시 재개 테스트를 짚었다). CodeRabbit의
보안·버그 축은 PR 직전 리뷰의 결과(PR 체크리스트)가 대신하고, 병합은 재리뷰를 기다리지 않는다(`operations.md` 리뷰
파이프라인). 고칠 지적이 없어 반영 커밋은 없고, 이 일지와 티켓의 병합 직전 판정, 대기열만 커밋해 푸시한다.

병합 직전 판정: `git fetch` 뒤 `origin/main`에서 05·06은 `done`, 02는 `ready-for-agent`라 기능을 닫지 않았다. 그 판정과
회고를 커밋(`ae607f28`)한 뒤 푸시 전에 다시 fetch하니 `origin/main`이 #322(아침 보고 형식, `b78317fe`)로 움직여 합쳤다.
충돌은 대기열 끝 하나였고, main의 380행을 두고 이 브랜치의 새 행을 381·382로 뒤에 붙였으며, 378은 두 쪽이 각자 센
다른 사건을 합쳐 4회차로 적었다(아래 회고 1). 합친 판에서도 02는 `ready-for-agent`다. main에 일지 2026-10-20-22가
들어와 이 일지(21)가 이름순으로 앞서게 되어 `tools/sibling_overlap.py --move`로 25로 옮겼고, PR 본문의 일지 경로도
`gh pr edit`으로 고쳤다. 같은 때 02 세션이 PR #325를 열었다.

## 회고

이 티켓의 세 세션(구현 세션, 셀프 리뷰 직전에 이어받은 세션, 커밋 뒤 인계를 못 해 이어 간 이 세션)을 함께 본다. 낸 후보는
여덟이고 승인 3(회차 하나, 새 행 둘), 기각 5, 넘김 0이다. 만료할 행은 이 브랜치와 `origin/main` 두 출력 모두 없었다
(`tools/queue_open_rows.py`). 378이 문턱(3회차)을 넘어 `tools/hook_report.py`를 돌렸고 뺄 후보는 없었다. 새 행은
처음에 380·381로 썼는데 형제 워크트리 `morning-report-format`(PR #322)이 380을 먼저 써서 `tools/sibling_overlap.py --move`로
381·382로 옮겼다.

1. **승인(회차): 커밋 뒤 인계의 새 세션 화면이 앱의 마지막 폴더인 다른 워크트리(`skill-listing-budget`)로 열렸다**(위
   "커밋 뒤에 인계"). 원인이 378과 같아(앱의 마지막 폴더가 다른 워크트리) 378에 회차를 더했다. 커밋 뒤 main을 합칠 때 아침 보고 세션
(일지 2026-10-20-22)이 자기 인계 실패라는 다른 사건으로 먼저 3회차를 더해 둔 것과 만나, 합친 행은 4회차다. 스크립트는 신뢰 대화상자
   앞에서 멈춰 그때는 세션이 생기지 않았는데, 지시문이 채워진 채 남은 그 화면이 뒤에 보내져 이 브랜치를 제목으로 한 세션
   (`feature/04-exchange-count-read-cap-and-thread (중복, 멈춤)`, `get_session`의 생성 07:15:01Z, 마지막 활동 07:18:58Z,
   `cwd` 루트)이 생겼다. 이 세션과 제목이 겹쳐 멈춘 것으로 보고, 그 세션의 기록은 읽지 않았다. 이 워크트리의 작업 트리와
   커밋에는 손이 닿지 않았다(`git status --porcelain`, `git log`). 378은 더하는 것이라 이 티켓 PR에서 반영하지 않고, 회차가
   3 이상이라 기능을 닫는 세션의 결정표가 chore 배치의 계기로 센다.
2. **승인(새 행 381): 구현 세션이 `tools/mutate.py`의 측정 실행 둘을 같은 체크아웃에서 나란히 띄웠다**(위 "변이와
   카나리아"). 두 실행이 같은 `continuation.py`에 변이를 넣고 되돌렸을 수 있었다. 끝난 뒤 변이가 남지 않은 것을 보았고
   손상은 없었다. 처방은 도구의 가드(같은 git 디렉터리에 pid가 살아 있는 다른 표지가 있으면 시작하지 않는다)이고, 첫
   사건이라 1회차로 둔다.
3. **승인(새 행 382): GitHub MCP의 `create_pull_request`가 확인 양식을 띄웠다며 PR을 만들지 않았는데 양식이 뜨지 않았다**
   (위 "PR"). 사용자가 알려 주어 한 턴이 더 들었다. 처방은 `operations.md` 브랜치와 병합에 PR을 `gh api …/pulls --input
   <파일>`로 여는 길을 적는 것이고, 첫 사건이라 1회차로 둔다.
4. **기각: 변이 표의 첫 표지 셋이 어긋났다**(위 "변이와 카나리아": pytest의 `At index 1 diff`, `-k` 하나로 고른 매개변수
   둘, 코드 조각에도 실리는 표지). 앞의 둘과 셀프 리뷰 반영 때의 19번 표지는 `tools/mutate.py`가 그 자리에서 어긋남을
   알렸다. 셋째는 `.claude/rules/probes.md` 첫 항목(표지를 고르기 전에 실패 출력을 본다)을 처음에 따르지 않은 것이지만,
   리뷰가 아니라 구현 세션이 실패 출력을 보고 스스로 바꿨고 그 규칙을 처방한 열린 행도 없어(290은 닫혔다) 회차로 세는
   것에 들지 않는다.
5. **기각: 셀프 리뷰가 `plan.md`의 알려진 한계 문장(Major)과 옛 대화뿐이라는 닫힌 주장의 반례를 잡았다.** 티켓이
   `operations.md` 문서 위치 절을 잘못 읽어 `plan.md`를 기록으로 적은 것이 앞의 것의 뿌리다. 리뷰가 잡도록 둔 기준
   (`code-review` 브리프의 닫힌 주장·잔존 항목)을 리뷰가 잡은 것이라 셈에서 뺀다.
6. **기각: PR 직전 `bug-perf-review`가 셀프 리뷰 반영으로 새로 쓴 문장 넷의 빠진 변형을 잡았다.** 260이 닫히며 둔 처방
   (반영으로 새로 쓴 문장을 PR 직전 리뷰에 밀 주장으로 넘긴다)이 그대로 돌아 잡은 것이다. 그 반영에서 처음 쓴 일반 문장
   ("오래된 것이 무엇이든 빠진다")이 거짓인 것은 커밋 전에 스스로 다시 대 보고 바로잡았다.
7. **기각: 워크트리 가드가 파이프가 든 git 명령을 거부했고, bash 큰따옴표 안의 역따옴표가 명령 치환이 되어
   `serve: command not found`가 났다.** 앞의 것은 앱 가드가 막았고 `CLAUDE.md` 환경 함정이 적는다. 뒤의 것은 스크립트의
   assert가 막아 파일이 바뀌지 않았고, 긴 스크립트를 파일로 쓰라는 같은 절의 지침대로 다시 돌렸다.
8. **기각: 훅이 알렸다**(중간 문장이 한국어가 아님 세 번, 큰 결과, Grep의 생략 줄, heredoc 줄 수). 이미 있는 훅이 그 자리에서
   알리거나 막은 것이다.

## 다음

이 PR은 워크트리에서 병합하고 주 체크아웃을 당기지 않는다. 주 체크아웃 미갱신: 루트는 main.

이 PR은 end-user-continuation을 닫지 않는다. 남은 잎 02는 자기 세션(`feature/02-runtime-names-the-failure-cause`, 워크트리
`.claude/worktrees/02-runtime-names-the-failure-cause`, 아직 PR 없음)이 맡는다. 그래서 이 세션은 지시문을 내지 않는다.
02가 병합되며 기능을 닫고 다음 지시문을 낸다. 그때 결정표가 세는 회차 3 이상 행에 378이 든다.
