# 2026-10-29 (14) 합치는 중의 sibling_overlap 대기열 행 뺌 (harness 024)

브랜치 `chore/024-sibling-overlap-merge-head`, 워크트리 `.claude/worktrees/024-sibling-overlap-merge-head`. 이 세션의 지금 제목은 `chore/024-sibling-overlap-merge-head`.

## 사용자 프롬프트

> 사용자: 대기열 492를 티켓 .scratch/harness/issues/024-sibling-overlap-merge-head.md로 쓰고 한다

(next-session 지시문으로 연 세션. 범위는 PR과 병합까지.)

> 사용자: 끝났어?

> 사용자: 훅을 건너뛰지 말고 pre-commit 커밋을 한 번 더 시도해 줘

이어받은 세션(2026-10-29)은 next-session 지시문으로 열렸다. 지시문의 시작 프롬프트는 위의 첫 줄과 같고, 범위는 PR과 병합까지.

## 한 것

- 티켓 `.scratch/harness/issues/024-sibling-overlap-merge-head.md` 를 쓰고(번호는 `tools/sibling_overlap.py` 의 다음 빈 번호), 대기열 492 를 닫음 표시로 고쳤다.
- 실패 시험을 먼저 써서 492 의 증상(`옮길 번호: 대기열 2 → 3`)을 재현했다.
- 번복: 대기열 행의 처방대로 `git merge-base <main> HEAD MERGE_HEAD` 로 구한 첫 판은 `test_sibling_overlap.py` 전체에서 기존 시험 둘(`test_합치다_대기열_행이_겹쳐도_옮기기는_main의_행을_둔다`, `test_합치기를_커밋하기_전에도_main이_들여온_파일은_이_브랜치의_변경이_아니다`)을 빨갛게 했다(손으로 봤다). merge-base 는 그대로 두고, 합치는 중이면 합칠 머리의 번호를 `taken` 에 넣고 `unshared` 로 빼며, 합칠 머리가 더한 행 가운데 `HEAD` 에 없고 작업 트리에 한 줄인 번호를 뺀다(`drop_merged_rows`).
- 셀프 리뷰(`/code-review`, base 5ccb51a). 명세 축이 프로브로 찾은 것: main 이 아닌 머리를 합치면 다음 빈 번호가 이미 쓴 번호를 낸다(Major), 두 줄 순서가 바뀌면 겹침을 놓친다(Minor), 티켓의 `unshared` 문장이 main 머리일 때만 맞다(Minor). 표준 축: 문서가 옛 판과 어긋남(리뷰가 옛 판을 읽음, 이미 고쳤다), "기존 시험 둘이 빨개졌다"의 꼴과 근거의 종류가 없음(인자 차례가 다른 꼴을 재어 초록), `k in committed` 갈래와 octopus 가 시험으로 고정되지 않음, smell 로 `queue_lines` 중복. 모두 고쳤다. `read_numbers` 가 `queue_lines` 를 쓰게 했고, `k in committed` 를 지운 변이에서 새 시험이 빨개진 것을 손으로 봤다. 나머지 smell(같은 `str` 인자 셋, 이름의 겹침)은 판단 항목이라 두었다.
- 합치기 관련 시험 13개(`-k 합치`)가 초록, 린트·포맷 초록. pre-commit 의 나머지 검사(pyright, lint-imports, check-instructions, check-type-escapes, run-hooks, web-verify 등)는 통과했다.

## 막힌 것

커밋을 pre-commit 으로 세 번 시도했고 세 번 모두 pytest 의 이 변경과 무관한 시간 의존 시험에서 막혔다. 이 PC 에 여러 세션이 함께 돌아 pytest 한 바퀴가 13~21분이었다. 아래 결과는 모두 `git commit -F` 의 pre-commit 출력과 `uv run pytest` 로그에서 손으로 봤다. 실패 원인을 부하로 본 것은 홀로 돌리면 통과한 것에 기댄 어림이다.

1. `tests/channel/cli/test_interrupt.py` 둘, `tests/tools/test_rerun_runner.py` 넷(6 failed). 두 파일을 홀로 돌리면 67 passed.
2. `test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다` 하나(`max(running) == 2` 가 1). 두 회차가 1초씩 겹쳐야 하는데 부하로 겹치지 않았다.
3. `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다` 하나(`assert []`).

이어받은 세션(2026-10-29)에서 두 번 더 시도했고 두 번 모두 pytest 에서 막혔다(나머지 검사는 Passed). 둘 다 `git commit -F` 의 pre-commit 출력에서 손으로 봤다.

4. `test_interrupt.py::test_도구_호출_도중에_한_번_누르면_서버를_닫고_중단으로_끝난다`("Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다"), `test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`(2 failed, pytest 17분 45초). 두 파일을 홀로 돌리면 67 passed 였고, 그것만 6분 6초가 걸렸다(`uv run pytest -q` 로 손으로 봤다).
5. `test_rerun_runner.py::test_동시에_둘까지_돌고_셋째는_자리가_빌_때_연다`(1 failed, pytest 10분 34초).

6. 사용자의 "지금 한 번 더" 로 친 일곱째 시도는 통과해 커밋됐다(`git commit -F` 의 종료 코드 0 을 손으로 봤다).

그 뒤 origin/main 을 `git merge` 로 합쳤고 충돌은 없었다(`tools/sibling_overlap.py`, 그 시험, `.scratch/retro-queue.md` 를 git 이 자동으로 합쳤다). 합친 뒤 `uv run pytest -q tests/tools/test_sibling_overlap.py` 125 passed, 두 파일의 pyright·ruff 초록을 손으로 봤다. 일지 번호는 main 이 앞서 가 `--move` 로 2026-10-29-14 로 옮겼다.

훅은 건너뛰지 않았다(사용자 지시). 시간 의존 시험의 고침은 별도 일이고, 스스로 내는 세션 카드는 훅이 막아(ADR 0037 "세션 카드") 여기 적는다.

## 인계

주간 한도 90% 도달로 인계(다른 세션의 마무리 요청). 새 세션·푸시·PR·병합을 하지 않고 멈춘다. 컨텍스트 인계 계기(`커밋 뒤`)도 왔지만 커밋이 성공하지 않아 경계가 아니었다.
