# coderabbit-review가 `Seat: not assigned`에서 종료하지 않게 고친다 (harness coderabbit-review-seat-not-assigned)

세션 제목: `chore/coderabbit-review-seat-not-assigned`. 브랜치 `chore/coderabbit-review-seat-not-assigned`, 워크트리 `C:\project\agent\.claude\worktrees\coderabbit-review-seat-not-assigned`. 모델 Sonnet 5.5 / high.

## 사용자 프롬프트

> 사용자: 대기열 578을 티켓 .scratch/harness/issues/coderabbit-review-seat-not-assigned.md로 쓰고 한다

지시문의 이번 요청 범위는 PR과 병합까지다. 이 세션은 나란히 여는 다섯 가운데 셋째이고 `tidy-checkouts`는 첫 세션이 돈다.

## 한 것

- **티켓.** `.scratch/harness/issues/coderabbit-review-seat-not-assigned.md`를 `in-progress`로 먼저 썼고 마지막에 `done`으로 바꿨다. 대기열 578을 가리킨다.
- **`coderabbit-review` 정의.** 1단계가 `Seat: not assigned`여도 종료하지 않고 3으로 가며, `Seat:` 줄은 보고에 옮기는 값이고 CLI 축인지는 리뷰가 실제로 findings를 내는지가 가른다고 적었다. 3단계에는 파일 150개 한도(`Too many files`)와 `--dir`로 좁혀 돌리는 길을 더했다. 머리 문단의 "좌석 없음"은 "좌석 거절로 리뷰가 시작되지 못함"으로, "본 세션이 auth status로 좌석이 없는 것을 먼저 보고 이 정의를 부르지 않는 흔한 길"은 "이 정의를 부르지 않고 대체 둘로 가는 길"로 고쳤다.
- **같은 서술을 옮긴 자리.** `docs/constitution/operations.md` 리뷰 파이프라인 2(좌석 서술 둘과 "로그인·좌석 없음" 둘), `.github/PULL_REQUEST_TEMPLATE.md`의 "좌석은 PR마다 `auth status` 한 줄로 본다", `KICKOFF.md` 9단계 7의 "좌석이 있을 때만이다"와 복사 목록, `bug-perf-review` 정의의 "로그인·좌석 없음"을 같은 뜻으로 맞췄다. 지난 일지, ADR 0006, `docs/constitution/history.md`, 이미 닫힌 기능의 명세(`kickoff-auto-flow`·`web-admin`·`plugin-toggle`)는 기록이라 두었다.
- **대기열.** 0578을 닫았다. 0570은 사람이 좌석을 배정하는 몫이라 열어 두고, 본문에 "`Seat: not assigned`에서도 리뷰가 돌았다"를 한 줄 덧붙였다. 0570이 계속 필요한지는 사용자가 정한다.
- **카나리아.** 새 명세 `coderabbit_review_seat_not_assigned.toml`을 새 `claude -p` 세션으로 돌렸다. 통과 4, 실패 0, "없음" 섞임 0이다. 대조군은 옛 문장("그 사실만 보고하고 종료한다")을 옮겼고 실험군 셋은 새 문장을 옮겼다(러너의 집계 줄과 답을 손으로 읽었다). 이 명세와 기존 `coderabbit_review_seat_line_absent.toml`은 `--shape`가 통과했다. 기존 명세가 묻는 두 문구는 정의에 그대로 남아 있어 다시 돌리지 않았다.

## 검증

근거의 종류. `Seat: not assigned`에서 `coderabbit review`가 `review_completed`로 끝났다는 사실과 파일 616개의 `Too many files` 거절은 대기열 0578과 일지 2026-11-07-02에 적힌 손으로 본 관찰을 옮긴 것이고, 이 세션이 `coderabbit review`를 다시 돌려 보지는 않았다(재실행은 시간당 3회 한도를 쓴다). 카나리아와 ruff는 이 세션이 직접 돌려 출력에서 읽었다.

- `uv run ruff check .`, `uv run ruff format --check .` 통과.
- `uv run python tools/plan_table.py`는 출력 없이 끝났다.
- `uv run python tools/run_checks.py`(백그라운드)는 종료 코드 1이다. zizmor, check-ticket, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, web-verify는 통과했고 pytest만 6575 통과, 1 실패였다. 실패는 `tests/channel/cli/test_interrupt.py::test_도구_호출_도중에_한_번_누르면_서버를_닫고_중단으로_끝난다`의 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다"이고, 이 변경은 문서와 카나리아 명세만 바꿔 그 시험이 읽는 코드를 건드리지 않았다. 그 파일만 따로 `uv run pytest -q tests/channel/cli/test_interrupt.py`로 돌리자 6건 통과했다(다만 400초가 걸렸다). 이 PC가 다른 세션 때문에 바빠 30초 제한에 걸린 것으로 본다(어림이다. 부하를 재지 않았다). pre-commit의 pytest가 같은 시험에서 다시 빨개지면 이 기록을 보고 따로 돌려 본다.
- 러너를 돈 뒤에 `coderabbit-review.md`·`operations.md`·`0570.md`의 근거 문구("대기열 578에 적힌 손으로 본 관찰을 옮겼다")를 고쳤고 카나리아는 `--preflight`로 다시 통과했다. 러너의 결과는 그 고침 앞의 것이므로 커밋 직전의 pre-commit이 최종 판정이다.

## 인계

컨텍스트가 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전` 경계에 와서 새 세션에 넘긴다(`next-session` `handoff.md`). 이 세션은 커밋하지 않았다. 작업 트리의 변경(정의, `operations.md`, PR 템플릿, `KICKOFF.md`, `bug-perf-review.md`, 카나리아 명세, 대기열 0578·0570, 티켓, 계획 표 재생성, 이 일지)이 그대로 있고, 새 세션이 셀프 리뷰(`/code-review`), 커밋, PR, 병합을 한다. 셀프 리뷰는 아직 돌리지 않았다.

open-session을 부른다 2026-11-07T17:39:03Z

PR 직전 리뷰에서 밀 주장(이 세션이 새로 쓴 사실 문장):
- `operations.md` 리뷰 파이프라인 2: "`Seat: not assigned`에서도 `coderabbit review --agent --committed --base origin/main`이 종료 코드 0으로 끝나 `review_completed`·`findings: 0`을 냈다(대기열 578에 적힌 손으로 본 관찰을 옮겼다)", "파일이 150개를 넘으면 `Too many files`로 거절되므로 `--dir`로 좁혀 돌린다".
- `coderabbit-review.md` 3단계: "파일 616개에서 거절되고 `--dir tools`로 좁히면 15개가 돌았다. 손으로 봤다, 일지 2026-11-07-02". 폴더 하나씩 좁힌다는 서술은 `--dir`가 여러 폴더를 받는지 이 세션이 확인하지 않았다.
- `KICKOFF.md` 9단계 7: "`Seat: not assigned`여도 돌려 본다".
- 0570 본문 덧붙임: "`Seat: not assigned`(`Plan: Free`)에서도 `coderabbit review`가 돌아 `review_completed`로 끝났다".

## 셀프 리뷰 (인계받은 새 세션)

범위: base `778db404`, 변경 파일 7개, 커밋 0개, 미추적 3개. 표준 축은 sonnet·high, 명세 축은 본 세션의 모델을 따랐다. 두 보고는 이 턴에 옮긴다.

**두 축이 같이 낸 지적.**
- Major, 확정. 같은 좌석 서술이 살아 있는 문서에 남았다: `KICKOFF.md:108`("`not assigned`면 … CLI 축이 비어 있다 … 대체 경로로 간다")가 같은 파일 9단계 7과 어긋난다. `kickoff/pitfalls.md:32`("좌석은 PR마다 `auth status` 한 줄로 본다")와 `kickoff/facts.md:12`("무료면 `Seat: not assigned`로 … 끝난다")와 `tools/hook_security_review_journal.py` 독스트링("좌석이 없으면 … 대체 둘로 가므로")이 옛 전제를 그대로 둔다. `operations.md`의 굵은 소제목("좌석 미배정이다")도 같은 항목에 더한 "`Seat: not assigned`에서도 돌았다"와 모순이다. 티켓 수용 기준 3과 `CLAUDE.md` 작업 규약 4(잔존 0)를 어긴다.
- Major, 확정. 좌석 거절 길이 절차 어디에도 없다. 머리 문단은 그 길을 들었지만 1단계는 종료를 걷었고 3단계에는 거절 항목이 없어 "인증 오류"로 읽을지 갈린다.
- Minor. 판정 기준이 0건과 충돌한다("findings를 내는지"는 `findings: 0`인 관찰 578과 어긋난다). `--dir` 분할이 시간당 3회 한도와 루트 직속 파일을 다루지 않는다. 1단계 끝의 "좌석은 PR마다 바뀌었으므로 … 캐시다"가 잔여물이다.
- Nit(고치지 않음). 3단계 명령(`--agent --include-untracked`)이 578 관찰의 명령(`--committed --base origin/main`)과 다르다. 정의의 명령은 이전부터 그것이었고, `operations.md`는 관찰의 명령을 그대로 옮겼으므로 둘이 다른 것이 맞다.

**고친 것.** 위 Major 둘과 Minor 셋(Nit 제외)을 이 턴에 반영했다.
- 잔존 다섯: `KICKOFF.md` 준비 절 CodeRabbit 문단(그 값은 진행 파일에 적고 리뷰는 실제로 돌려 본다), `KICKOFF.md` 복사 목록 줄("좌석 확인" → "`Seat:` 줄 보고"), `kickoff/pitfalls.md`·`kickoff/facts.md`, 훅 독스트링, `operations.md` 굵은 소제목("좌석 거절이다").
- `coderabbit-review.md` 3단계에 좌석 거절 항목을 더했다(`You are not a member of the requested organization`이면 그 문구와 `auth status` 출력을 보고하고 종료). 1단계의 판정 기준을 "끝까지 도는지(`review_completed`, 0건이어도 같다)"로 바꿨고 `operations.md`도 같게 했다. `--dir` 항목에는 경로 하나만 받는다는 것(`coderabbit review --help`를 읽었다), 폴더마다 한도를 쓴다는 것, 한도에 걸리면 돌린 폴더만 트리아지하고 보지 못한 폴더와 루트 직속 파일은 보고에 적는다는 것을 더했다. 1단계 끝의 "캐시" 문장을 지웠다.
- 티켓 수용 기준 3의 문서 목록과 대기열 0578의 닫힘 문구(잔존 목록)를 맞췄다.

**남긴 것과 이유.**
- 줄 머리의 `Seat`와 콜론 사이에 공백이 여럿인 출력(`Seat         : not assigned`)을 정의가 글자 그대로의 `Seat:`로만 적는 점. 이전부터 있던 것이고 `KICKOFF.md` 준비 절이 그 모양을 따로 적는다. 이 티켓의 범위(종료 규칙)를 넘는다. 회고 후보로 남긴다.
- `--dir` 실행에 `--include-untracked`를 붙이는지. 리뷰를 돌려야 알 수 있고 시간당 3회 한도를 쓴다. 정의에는 붙이는지 적지 않았다.
- 한도가 걸린 첫 실행(`Too many files` 거절)이 시간당 한도를 쓰는지. 재지 않았다. 정의의 "재실행은 한도를 하나 더 쓴다"가 이미 있다.

**다시 돌린 것.** `uv run python tools/canary.py --preflight --control-commit 778db404 …/coderabbit_review_seat_not_assigned.toml`이 통과했다(실행 전 확인만, `claude`는 돌리지 않았다). 정의 1단계의 인용 문구("값이 `not assigned`여도 종료하지 않고 3으로 간다")는 그대로이고, 기존 `coderabbit_review_seat_line_absent.toml`이 묻는 두 문구("종료하지 않고 3으로 가서", "그 줄이 없었다고 적는다")도 정의에 남았다. 그 기존 명세는 이미 병합된 앞선 고침의 것이라 대조군 커밋을 주지 않으면 실행 전 확인이 실패하는 것이 원래 모양이다. `run_checks.py` 전체는 커밋의 pre-commit이 최종 판정이다.

`bug-perf-review.md` 머리 문단을 고쳤으므로 그 정의를 원천으로 든 카나리아 넷(`bug_perf_review_budget`·`counter`·`pushed_claims`·`report_line_and_call_paths`)을 새 `claude -p` 세션(claude 2.1.318)에서 돌렸다. 넷 모두 `통과 4 · 실패 0 · "없음" 섞인 통과 0`이고(러너의 집계 줄과 답을 손으로 읽었다), 명세마다 `# 최신 결과:` 줄을 고쳤다. 대조군 커밋은 각 명세 머리 주석의 것(`bd72bae`·`c1903e0`·`dbcdc6d`·`ebd09fb`)을 `--control-commit`으로 줬고, 실험군은 `778db404` 위의 커밋 전 변경이다. 모양 검사(`--shape`)와 전체 검증은 커밋의 pre-commit이 판정한다.

첫 커밋 시도: pre-commit의 `checks`가 pytest 한 건(`tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`, `assert lines`가 빈 목록)으로 빨갰다(6575 통과, 1 실패, 898초). 나머지 게이트는 통과했다(린트, 타입체크 둘, 경계, 지침 검사, 타입 우회 검사, 훅 러너, 웹 검증, 헌법 판, 카나리아 모양, 변이 표, 표 모양, 줄 구분 문자, 티켓). 그 파일만 따로 `uv run pytest -q tests/tools/test_probe_kit.py`로 돌리자 15건이 3.86초에 모두 통과했다(손으로 봤다). 이 변경은 그 시험이 읽는 `tools/probe_kit.py`를 건드리지 않았고, 네 카나리아와 다른 세션이 함께 돌던 때라 시간 제한(0.5초)에 걸린 것으로 본다(어림이다. 부하를 재지 않았다). 같은 시험이 다시 빨개지면 추측으로 고치지 않고 diagnosing-bugs로 간다.

헌법 판: `operations.md` 문구를 고쳤으므로 3.0.71에서 3.0.72(patch)로 올렸다(`docs/constitution/README.md`). 이유는 이 일지가 원천이다.

PR 직전 리뷰에 밀 주장(이 턴에 새로 쓴 사실 문장):
- `coderabbit-review.md` 3단계: "`--dir`는 경로 하나를 받는다, `coderabbit review --help`를 읽었다"(`--dir <path>` 단일 값이고 "Review only git changes inside this directory"를 읽었다). "폴더마다 2단계의 시간당 3회를 하나씩 쓰므로"는 어림이다.
- `coderabbit-review.md` 3단계: "`You are not a member of the requested organization`으로 즉시 끝나면 좌석 거절이다(2026-09-23, `operations.md` 리뷰 파이프라인 2)". 증상 문구와 날짜는 `operations.md`의 기존 문장에서 옮겼다.
- `kickoff/pitfalls.md`·`kickoff/facts.md`: "`Seat: not assigned`여도 리뷰가 돈 적이 있다, 2026-11-06"(일지 2026-11-06-07 57~58행의 관찰).
- `KICKOFF.md` 준비 절: "`not assigned`는 … CLI 축이 비었다는 뜻도 아니다".

## 인계 (커밋 뒤)

컨텍스트가 문턱(20만 토큰)을 넘은 채 `커밋 뒤` 경계에 와서 새 세션에 넘긴다(`next-session` `handoff.md`). 커밋은 `3d95c132`이고 푸시 전이다. 남은 일은 main 합치기, PR 직전 리뷰, PR, 병합이다. 이 세션은 `chore/coderabbit-review-seat-not-assigned (인계함)`으로 제목을 바꿨다.

open-session을 부른다 2026-11-07T18:48:36Z

## PR 직전 (커밋 뒤 이어받은 새 세션)

**main 합치기.** `git merge origin/main`이 충돌 없이 끝났다(34개 파일). `tools/sibling_overlap.py`는 번호 겹침 없음, 함께 고친 파일 없음이고 형제의 가장 높은 헌법 판이 3.0.71이라 3.0.72를 그대로 둔다. `tools/plan_table.py`는 합친 뒤에도 출력과 변경이 없다.

**pre-commit이 시간 의존 시험에서 세 번 빨갰다.** 이 일지의 인계 절 한 파일을 커밋하려던 시도마다 pytest 한두 건이 빨갰고(6572~6575 통과), 시험이 매번 달랐다. 첫 시도는 `test_interrupt.py` 하나, 둘째는 같은 파일 셋과 `test_rerun_runner.py` 하나, 셋째는 `test_rerun_runner.py` 둘이다. 실패 메시지는 앞의 파일이 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다", 뒤의 파일이 두 실행이 겹쳐 돌았는지 재는 단언(`assert 1 == 2`)이다. 빨간 뒤 그 두 파일만 따로 돌리자 부하가 낮을 때 69건이 모두 통과했다(5분이 걸렸다, `--durations`로 읽었다). 첫 실패 때 CPU 사용률이 100%였던 것은 손으로 봤고, 그 부하가 pre-commit이 pytest, web-verify, run-hooks를 함께 띄운 탓인지 다른 세션 탓인지는 가르지 않았다(어림이다). 이 변경은 문서와 카나리아 명세뿐이라 그 시험이 읽는 코드를 건드리지 않았다. 그래서 인계 절만 따로 커밋하지 않고 main을 합친 뒤 이 절과 함께 한 커밋에 실었는데, 그 커밋의 pre-commit도 넷째로 `test_rerun_runner.py`의 두 회차 겹침 단언(`assert 1 == 2`, `hang=1.0`초 고정 대기를 쓰는 시험이다, 코드를 읽었다) 하나로 빨갰다(6628 통과, 1 실패, 1425초). 합친 트리에서 두 파일을 따로 돌리자 69건이 모두 통과했고(152초), 그래서 이 커밋은 러너가 정식으로 읽는 `SKIP=pytest`로 pytest만 빼고 나머지 검사를 모두 돌렸다. 빠진 pytest는 이 PR의 CI가 판정한다. 이 시험들이 부하에 약한 것은 이 티켓의 범위 밖이라 고치지 않았고 회고 후보로 남긴다.

**`coderabbit-review` 서브에이전트(CLI 0.7.5).** `Seat: not assigned`(`Plan: Free`)인 채 `coderabbit review --agent --committed --base origin/main`이 종료 코드 0으로 끝났고 `review_completed`, 검토 파일 18개, 지적 2건이었다(보고를 읽었다). 이 정의가 고친 동작, 곧 `not assigned`에서 종료하지 않고 3단계로 가는 길이 실제로 도는 것이 한 번 더 확인됐다. 한도는 1회 썼다. 두 지적 모두 Minor로 낮춰 보았다.

- 정의 20행: `--dir`로 좁힐 때 루트 직속 파일이 안 보인다는 서술이 "한도에 걸리면" 문장 바로 뒤에 붙어, 한도에 걸리지 않고 폴더를 다 돌린 경우에도 적용되는지 모호했다. 유효로 판정하고 고쳤다. `--dir`로 좁혀 돌렸으면 한도에 걸렸든 아니든 `--dir`가 닿지 않은 몫을 보고에 적는 별도 항목으로 뗐다. 카나리아 명세가 묻는 두 문구는 건드리지 않았다.
- `KICKOFF.md:108`: 로그인 판정이 `Seat` 줄의 존재에 묶여 `Review access`만 보이는 출력(2026-11-03에 본 모양)을 다루지 않는다. 이번 변경이 바꾼 문장이 아니고 범위 밖이라 고치지 않았다. 회고 후보로 남긴다.

**밀 주장 판정.** 다섯 중 셋째와 넷째(`Seat: not assigned`여도 돈다)는 이번 실행이 같은 조건이라 확인됐다. 첫째의 `Too many files`와 `findings: 0`, 둘째의 `--dir` 시험 호출·폴더마다 3회·좌석 거절 문구는 이번 실행이 그 경로를 타지 않아 확인하지 못했다(근거는 일지 2026-11-07-02와 2026-09-23의 기록뿐이다). 다섯째는 살아 있는 문서에서 옛 전제가 남은 곳을 찾지 못했다. 보고가 알려 준 `docs/adr/0006-review-pipeline.md` 34·41행은 기록이라 두었고, 거기에 정정 이력을 쌓을지는 이 티켓의 범위 밖이다.
