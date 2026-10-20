# 2026-10-20 (21) 원문 교환이 50개를 넘으면 접고, 거슬러 읽기는 100개에서 멈추며, 이어 가기의 판정은 스레드 하나에서 돈다

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
읽을 것: 일지 docs/journal/2026-10-20-21-exchange-count-read-cap-and-thread.md(커밋하지 않았다. 워크트리에 있다)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`, base는 origin/main의 merge-base)부터 한다. 구현·테스트·변이 표 18개·다른 표 원문 여섯의 고침·카나리아·-m llm(7 passed)은 마쳤고 티켓은 done으로 고쳤다. 비워 둔 체크박스 둘(검증 명령, 병합 직전 판정)은 새 세션이 채운다. 리뷰 전의 run_checks와 린트 둘은 초록이었고(일지 검사 절), 리뷰 반영 뒤의 다섯은 커밋의 pre-commit으로 갈음한다. walk_cap_mutations.toml의 전체 실행은 리뷰를 반영해 커밋한 뒤에 한 번 돈다. --check가 알린 pause_index 표의 run.py 원문 다섯이 main에서 이미 썩었는지는 확인하지 않았다. 일지 docs/journal/2026-10-20-21-exchange-count-read-cap-and-thread.md
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
읽을 것: 일지 docs/journal/2026-10-20-21-exchange-count-read-cap-and-thread.md(셀프 리뷰 절의 "새로 쓴 사실 문장", 커밋 절. 끝의 "커밋 뒤에 인계" 절은 커밋하지 않아 워크트리에만 있다)
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰(두 축)와 그 반영을 커밋까지 마쳤고 pre-commit은 모두 초록이다(손으로 치는 다섯은 갈음됨). 남은 단계는 차례로 (1) walk_cap_mutations.toml 20개 전체 실행(리뷰 반영 뒤에는 6·7·19·20만 돌렸다), (2) core.md를 고쳤으므로 카나리아 core_rule_read_cap_thread.toml 다시 돌기, (3) 티켓의 "검증 명령" 체크박스 채우기(pre-commit 결과와 -m llm 7 passed가 일지에 있다), (4) origin/main 합치기, (5) PR 직전 리뷰에 일지 셀프 리뷰 절의 "새로 쓴 사실 문장"을 밀 주장으로 넘기기, (6) PR, 봇 회차, 병합 직전 판정 체크박스, 워크트리 길로 병합, next-session이다. 셀프 리뷰가 남긴 지적 하나(01 티켓 11행)의 이유는 일지에 있다. 일지 docs/journal/2026-10-20-21-exchange-count-read-cap-and-thread.md
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
