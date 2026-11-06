# 2026-11-07 (01) 회고 항목의 반영 문턱을 다섯으로 올린다 (retro-queue-per-item 01)

세션 제목: `feature/01-retro-threshold-five`. 브랜치 `feature/01-retro-threshold-five`, 워크트리 `.claude/worktrees/01-retro-threshold-five`. 이 일지는 인계 세션(셀프 리뷰 직전)을 위해 먼저 쓴 것이고 `## 다음`과 회고는 아직 없다. 이어받는 세션이 같은 파일을 이어 쓰고 커밋한다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/retro-queue-per-item/issues/01-retro-threshold-five.md

지시문의 다음 작업은 "회고 항목의 반영 문턱을 회차 다섯으로 올리는 구현 티켓", 다음 단계 구현, 어디서는 새 세션(주 체크아웃 미갱신이라 `tidy-checkouts`를 먼저 돌고 `EnterWorktree`, name은 `01-retro-threshold-five`), 브랜치 `feature/01-retro-threshold-five`, 모델 `Sonnet 5.5 / high`, 이번 요청 범위 "PR과 병합까지"였다.

## 한 일

1. **시작.** 세션 제목을 브랜치로 바꾸고 `tidy-checkouts`를 돌았다. 주 체크아웃을 `07d80b96`에서 `819782eb`로 당겼고 `worktree-retro-queue-per-item-spec` 브랜치를 지웠다. 병합된 `05-default-model-required-and-checked` 워크트리는 `agent-os.exe`와 `python.exe`가 쥐어 이름 바꾸기가 막혀 남았다(그 프로세스가 끝난 뒤의 정리가 다시 본다). 그 뒤 `EnterWorktree`로 들어가 브랜치를 `feature/01-retro-threshold-five`로 바꿨다. `uv sync`와 `pnpm -C web install --frozen-lockfile`을 쳤다.
2. **빨강을 먼저 봤다.** `tests/tools/test_queue_open_rows.py`를 5로 옮기고(회차 4 행은 승인 칸의 가장 늦은 날짜가 14일 넘으면 만료 후보, 회차 5 행은 아닌 사례를 `test_회차_5_이상인_행은_반영할_때까지_만료하지_않는다`에 둠) 상수를 바꾸기 전의 도구로 돌려 7건이 빨간 것을 봤다. 그 뒤 `MIN_ROUNDS = 5`로 바꿨다.
3. **도구·시험.** `tools/queue_open_rows.py`(상수, 독스트링의 "회차 3"), `tools/morning_collect.py`의 독스트링 둘("3회차 이상"), `tools/morning_tasks/environment.md`의 "(3회차 이상)"을 5로 고쳤다. `tests/tools/test_morning_collect.py`는 4회차 행(243)을 두어 표에서 빠지는 것을 보이고 240을 5회차로 옮겼다. `tests/tools/test_morning_report.py`는 이름표 문구만 5로 고쳤다.
4. **문장.** `CLAUDE.md`(지도의 `CODING_STANDARDS.md` 행, 교정 루프), `CODING_STANDARDS.md` 머리, `retro` SKILL.md(4단계 더하는 문턱, 대기열 어디로 칸의 문구, 5단계의 회차 5 이상 둘, 같은 실수의 반복, 만료 문단의 "회차 5 이상"·"다섯 번째에 닿는다"), `next-session` SKILL.md(결정표의 "회차 5 이상인 항목", "다섯 번째 전이면 묶지 않는다"), `KICKOFF.md` 셋, `kickoff/claude-md-template.md` 둘, `.scratch/morning-report-split/design.md`를 고쳤다. 끝이 열린 결함 종류의 "세 번째 사례부터"와 "가장 큰 회차에 하나를 더한 값"은 그대로 뒀다.
5. **열린 항목의 옛 문구 61행.** `.scratch/retro-queue.md`의 열린 행에서 고쳤다(스크래치 스크립트로 번호별로 치환하고 `git diff --stat`이 61줄 61줄인 것을 봤다).
   - "세 번째"를 더하는 문턱의 뜻으로 담은 43행 모두 "다섯 번째"로: 411 438 452 457 462 465 466 468 469 470 471 472 473 477 487 488 489 491 494 503 504 505 521 522 523 528 539 547 548 549 550 551 552 554 555 556 564 571 573 574 575 577 581. 앞뒤 45자를 읽으면 모두 어디로 칸의 처방이거나 "문턱은 세 번째 반복" 문장이었다.
   - 숫자로 문턱을 적은 명세 목록의 넷: 467(인용한 retro 문장과 "회차 3 이상은 그 줄의 조건"을 5로, "대기열 214의 3회차"라는 지난 사건은 둔다), 468("회차 3 이상인 열린 행 가운데"를 5로, "214가 3회차로 문턱을 지났다"는 지난 사건이라 둔다), 565와 579("회차 3 이상이라 chore 계기"를 5로. 둘 다 회차가 8과 6이라 5 이상이 맞다).
   - **명세 목록 밖에서 찾은 열다섯 행.** "N회차에 …를 고른다/반영한다/(N회차에)" 꼴로 문턱을 숫자로 적은 362("3회차가 되면")·420·490·493·500·559·560·561·562·563·566·567·568·569·580을 "5회차에"로 고쳤다(362만 "5회차가 되면"). 고치지 않으면 retro가 이 행들을 3회차에 반영하라는 뜻으로 읽는다. PR 본문에 목록 밖 자리로 적을 것.
   - 합계: 468은 첫째 목록(43행)과 둘째 목록(숫자 넷)에 모두 들어 있어 43 + 4 + 15 = 62에서 겹침 하나를 빼면 61행이다.
   - 둔 것: 닫힌 항목 전부(기록), 306("세 번째 사례"가 아니라 끝이 열린 결함 종류), 411의 "20자 문턱은 42가 정했다", 574의 "문턱 아래 참고로만", 576의 "문턱 전이라 회차만 센다"(숫자 없음), 시험 `test_회차를_말로만_적은_행은_모른다고_센다`의 "세 번째 반복"(말로만 적은 회차를 모른다고 세는 사례라 문턱 뜻이 아니다).
6. **만료 후보.** 상수를 바꾼 도구를 `--today 2026-11-06`으로 돌리니 열린 행 132개, 만료할 행은 `435(2026-10-22)` 하나였다. 명세가 2026-11-06에 센 것과 같다. 회차 5 이상은 `420(11회차) 430(9) 431(8) 565(8) 558(7) 579(6) 214(5) 475(5) 499(5) 535(5)`로 열이다. 435를 만료로 닫는 일은 retro가 만료 문단대로 한다(이 티켓이 닫지 않았다).
7. **카나리아 네 개를 새 `claude -p` 세션에서 돌렸다.**
   - `claude_md_addition_threshold`: 통과 4. 대조군은 주 체크아웃(`819782eb`).
   - `claude_md_retro_self_approve`와 `retro_threshold_and_expiry`: 처음에는 `--control-commit` 없이 돌렸더니 "명세 오류: 대조군 사본의 원천에 카나리아가 있다"로 아무것도 돌리지 않고 2로 끝났다. 바뀌지 않은 기대 문구(`후보의 승인도 retro가 스스로 판정하고`, `뺄 후보`, `세 번째 사례부터는 사례를 고치지 않는다`, `가장 큰 회차에 하나를 더한 값이다`)를 주 체크아웃이 이미 싣고 있어서다. 이 명세들의 머리 주석이 일러 둔 대로 옛 커밋을 `--control-commit`으로 줬다(`6b439aa`, `be04b6e1`. 인자 순서는 `--control-commit <커밋> <명세> <출력 디렉터리>`이고 처음에 출력 디렉터리와 명세를 바꿔 한 번 2로 끝났다). 둘 다 통과 4.
   - **새 명세** `next_session_queue_threshold.toml`을 더했다. `next-session` SKILL.md의 "회차 5 이상인 항목(사람 몫은 뺀다)"과 "다섯 번째 전이면 묶지 않는다"를 원천으로 든다(번호 대조 도구의 카나리아 검사가 바뀐 스킬 본문마다 그 경로를 원천으로 든 명세가 있는지 본다). 통과 4, 대조군(`819782eb`)은 옛 문구 "회차 3 이상인 항목"과 "세 번째 전이면"을 옮겼다.
   - 네 명세의 머리 주석 "최신 결과:" 줄을 이 실행으로 고쳤다(옛 결과는 "그 전 결과:" 줄로 남겼다). `tools/canary.py --shape`도 통과했다.
8. **변이 표.** `queue_open_rows_mutations.toml`의 이름 둘과 `expect_output`의 "회차 3 이상"을 5로 고치고 변이 하나(`회차 문턱을 셋으로 되돌린다`, 14번)를 더했다. `tools/mutate.py --check`로 원문을, 이어 전체(60개)를 돌려 "변이 60 모두 기대대로"였다. `.scratch/harness/probes/README.md`의 해당 행(개수 예순, 이름 둘, 결과 한 줄)을 고쳤다.
9. **티켓.** `.scratch/retro-queue-per-item/issues/01-retro-threshold-five.md`의 `Status:`를 `in-progress`로 바꿨다가 `done`으로 바꿨고, 체크박스를 모두 `[x]`로 바꿨다.
10. **검증.** `uv run ruff check .`와 `uv run ruff format --check .` 초록. `uv run python tools/run_checks.py` 초록(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, pytest 296.1초, web-verify 469.5초). 아직 커밋하지 않았다.

11. **셀프 리뷰(`/code-review`, 기준 `819782eb`, 20개 파일, 커밋 0, 미추적 2).** 표준 축은 하드 위반 0이고 Minor 일곱을 냈다. 명세 축은 둘을 냈다. 서브에이전트 둘이 낸 것을 이 세션이 다시 확인했다.
    - **고친 것 1: `CODING_STANDARDS.md` 12행.** 처음 고친 문장이 "2026-10-12부터는 같은 실수의 다섯 번째에"라 문턱이 그날부터 다섯이었다는 거짓이 되었다. `git diff -- CODING_STANDARDS.md`로 본 사실이다. "2026-10-12부터는 같은 실수의 세 번째에, 2026-11-06부터는 다섯 번째에 retro가 스스로 더하고"로 갈랐다. 2026-11-06은 ADR 0036 이력의 날짜이고 문장 끝에 그 이력을 근거로 달았다.
    - **고친 것 2: 만료 후보를 오늘 날짜로도 적는다.** `uv run python tools/queue_open_rows.py --today 2026-11-07`(손으로 침)이 만료할 행 15개를 낸다: 435 319 362 438 439 441 443 444 446 447 450 451 452 453 454. 옛 도구(`git show HEAD:tools/queue_open_rows.py`를 스크래치패드에 풀어 같은 날짜로 손으로 침)는 13개이고 435와 362가 빠진다. 문턱을 올려 하루 사이에 보호선을 잃고 경계를 넘은 행이 이 둘이다. 2026-11-06 기준 435 하나는 앞 단계 그대로다. 만료를 닫는 일은 retro가 한다.
    - **고친 것 3: 5항의 합계.** 468이 두 목록에 겹친다는 줄을 더했다.
    - **고친 것 4: 첫 커밋 시도에서 pre-commit의 `check-mutations`(`tools/mutate.py --staged`)가 실패했다(종료 2).** 이름을 고치거나 더한 변이 셋(14 "회차 문턱을 셋으로 되돌린다", 25 "사람 몫을 회차 5 이상과 만료에서 빼지 않는다", 36 "만료에서 회차 5 이상을 빼지 않는다")에 `expect_output`이 없다는 이유다(대기열 350). 이 인계 세션이 돌린 `--check`와 전체 실행(60개 모두 기대대로)은 이것을 알리지 않는다. 변이를 손으로 넣어(`MIN_ROUNDS = 3`, `counted = rows`, `waiting = counted`를 `Edit`로 넣고 `uv run pytest tests/tools/test_queue_open_rows.py -k …`를 쳐 출력을 파일로 받은 뒤 `Edit`로 되돌렸다) 실패 출력을 읽고 표지를 골랐다. 14는 `회차 3 이상: 1(5회차) 2(4회차)`, 25는 `회차 5 이상: 238(11회차) 306(9회차)`, 36은 `전): 1(2026-09-01) 2(2026-09-01) 3(2026-09-01)`이다. 셋 다 시험 파일 원문에 글자 그대로 없고 변이된 출력에서만 나온다. `uv run python tools/mutate.py <표> 14`와 `25 36`을 쳐 "기대대로"를 봤다(손으로 봤다).
    - **남긴 것:** (a) 티켓의 첫 체크박스 "첫 커밋에 `in-progress`를 싣는다"는 이 인계가 커밋 없이 `done`까지 와서 첫 커밋에 `done`이 실린다. 도구가 막는지는 pre-commit의 `check_ticket`이 본다. (b) 카나리아 결과 줄에 `claude` 버전이 없다. 운영 규약이 요구하는 것을 찾지 못했다. (c) retro SKILL에서 반영 문턱(다섯)과 끝이 열린 결함 종류(셋)가 다른 까닭이 스킬에 없고 ADR 0036 이력에만 있다. 세 번째 사례 때 회고가 후보로 다룬다. (d) 같은 수가 문장 약 20곳에 흩어진 것(Shotgun Surgery)은 명세가 정한 범위의 결과라 둔다. (e) 위 사용자 프롬프트 인용이 `/implement` 호출이라 조작 지시이다. 이 일지는 인계 세션이 쓴 것이라 그대로 둔다.
    - **재현하지 못한 근거:** "카나리아 통과 4", "pytest 296.1초", "web-verify 469.5초", "빨강 7건"은 표준 축이 다시 재지 못했다. 이 인계 세션의 실행 기록이라 이 세션은 커밋 때의 pre-commit과 전체 러너로 다시 본다.

## 결정·번복·확인

- ADR 0036 이력 2026-11-06이 이미 병합되어 있어(PR #481) 이 티켓은 ADR을 고치지 않았다. 문턱·계기·보호선·옛 문구는 그 이력이 말한 대로다. "행은 항목 파일이다"는 티켓 02가 세운다.
- 명세 목록 밖의 자리는 위 5의 열다섯 행과 새 카나리아 명세 하나다(`next_session_queue_threshold.toml`). PR 본문에 적는다.
- 지시문의 "이어받을 상태"가 말한 `tests/tools/test_rerun_runner.py::test_다른_판의_확인을_쥐고_돌던_동안에도_첫_인계에서_멈춘다`는 이 세션의 전체 러너(pytest 296.1초)에서 빨갛지 않았다. 원인은 진단하지 않았다.
- `ctx.py`·`ctx2.py`·`fix_queue.py`는 세션 스크래치패드에 둔 읽기·치환 스크립트다. 저장소에 넣지 않았고 측정이 아니라 근거로 쓰지 않는다.
- 이 세션의 컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전` 경계에 와서 인계한다.

## 이어받는 세션이 할 일

셀프 리뷰(`/code-review`, main 대비 이 브랜치의 변경 전체와 미추적 `next_session_queue_threshold.toml`·이 일지) → Critical·Major 반영 → 커밋(커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`) → PR(`/git-pr`) → `merge.md`의 봇 회차 → 일지 "다음"과 회고(retro) → 병합 → `tidy-checkouts`. 요청 범위는 "PR과 병합까지"다.

## 인계 세션 이후 (커밋 뒤 인계)

세션 제목: `feature/01-retro-threshold-five`(인계로 열린 세션). 이 절은 두 번째 인계(`커밋 뒤`, 컨텍스트 20만 토큰 초과)를 위해 쓴다. 커밋하지 않았고 `## 다음`과 회고는 아직 없다.

### 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/retro-queue-per-item/issues/01-retro-threshold-five.md (지시문의 이어받을 상태는 `인계: 셀프 리뷰 직전`, 이번 요청 범위는 "PR과 병합까지")

### 한 일

1. 세션 제목을 브랜치로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어갔다. `git worktree list --porcelain`에 이 브랜치의 워크트리가 있었다.
2. 셀프 리뷰(`/code-review`)를 돌렸다. 범위는 기준 `819782eb`, 20개 파일, 커밋 0, 미추적 2였다. 표준 축(sonnet·high)과 명세 축 서브에이전트 둘이 보고했고, 위 11항에 지적과 판정을 적었다. 이 세션이 다시 확인한 것: `CODING_STANDARDS.md` 12행의 날짜 거짓, 오늘 날짜의 만료 후보 15개(옛 도구 13개).
3. 커밋을 두 번 시도했다. 첫 시도는 pre-commit의 `check-mutations`에서 실패했고(위 11항 고친 것 4), 고친 뒤 둘째 시도가 들어갔다. 커밋은 `083927ba`(`feat: 회고가 항목을 반영하는 문턱을 같은 실수의 다섯 번째로 올린다 (retro-queue-per-item 01)`)이고, 둘째 시도의 pre-commit 출력(스크래치패드 `commit2.txt`)에서 `Failed`가 없고 `Passed`가 19줄이었다(손으로 셌다). `ruff`와 `Skipped`는 세지 않았다. 갈음된 다섯 게이트(pytest·pyright·lint-imports·ruff·check-instructions 등)는 이 커밋의 pre-commit 결과다.
4. 커밋 뒤 이 일지에 이 절만 더했다. 이 절과 마지막 `open-session을 부른다` 줄은 커밋하지 않았다.

### 남은 단계

- 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`(이 절을 커밋하는 다음 커밋도).
- PR(`/git-pr`)을 열고 `merge.md`의 봇 회차 → 일지 `## 다음`과 회고(`retro`) → 병합 → `tidy-checkouts`. 요청 범위는 "PR과 병합까지"다.
- PR 본문에 적을 것(티켓 요구): 명세 목록 밖에서 고친 열린 행 15개(362 420 490 493 500 559 560 561 562 563 566 567 568 569 580), 새 카나리아 명세 `next_session_queue_threshold.toml`, 만료 후보(2026-11-06 기준 435 하나는 명세와 같고, 2026-11-07 기준은 15개이며 옛 문턱에서의 13개에 435와 362가 더해진다), 위 "재현하지 못한 근거"(pytest 296.1초 등은 인계 세션의 실행이고 커밋 때 pre-commit이 다시 돌았다).
- 변이 표 `queue_open_rows_mutations.toml`은 커밋에 `expect_output` 셋이 들어 있다. 로컬 `tools/mutate.py --staged`가 "문제 0"이었다.
- 티켓 `Status:`는 이미 `done`이다(티켓 체크박스 "첫 커밋에 `in-progress`를 싣는다"는 인계 세션이 커밋 없이 `done`까지 와서 첫 커밋에 `done`이 실린 것이 사실이다).

open-session을 부른다 2026-11-06T16:05:16Z

open-session을 부른다 2026-11-06T16:36:11Z

## 이어받은 세션 (PR부터)

인계 지시문(이어받을 상태 `인계: 커밋 뒤`)으로 연 세션이 이었다(Sonnet 5.5 / high). `git worktree list`에서 브랜치가 `.claude/worktrees/01-retro-threshold-five`에 있어 `EnterWorktree(path)`로 들어갔고, 제목은 브랜치 이름으로 바꿨다. 푸시 전 상태는 커밋 `083927ba` 하나와 커밋하지 않은 이 일지 변경이었다. `git fetch origin main` 뒤 `HEAD..origin/main`이 비어 rebase할 것이 없었고, `uv run python tools/sibling_overlap.py`는 번호 겹침 없음, 함께 고친 파일 없음으로 끝났다(종료 0). 요청 범위가 "PR과 병합까지"라 PR 제목·본문 확인은 묻지 않고 연다.

## PR 직전 리뷰

PR 체크리스트가 요구하는 `coderabbit-review` 서브에이전트를 푸시한 뒤 PR을 열기 전에 돌렸다(인계 세션들은 셀프 리뷰만 돌렸다). 서브에이전트의 보고에서 읽은 것이다(이 세션이 CLI를 직접 치지 않았다): `coderabbit review --agent --include-untracked --base origin/main`, 버전 0.7.5, 계정 Free 플랜, 출력에 `Seat: not assigned`가 있었지만 리뷰는 끝까지 돌아 `review_completed`, `findings: 0`(22개 파일, Critical·Major·Minor 모두 0)이었다. 대기열 578의 처방 대상 사건이 이번에도 났다는 뜻이지만(좌석 표시가 `not assigned`인데 리뷰는 돌았다) 이 세션에서 578의 회차를 더하지 않는다. 이 세션은 `coderabbit-review` 정의를 읽지 않았고, 서브에이전트가 그 정의의 1단계와 어긋난다고 보고한 것을 근거로만 안다. 지적이 0건이라 고칠 것도 보류할 것도 없다. 이 리뷰는 CLI 축 하나라 `/security-review`와 `bug-perf-review`는 돌리지 않았다.

## 회고

후보 넷을 냈다. 승인 0, 기각 넷, 넘김 없음.

- **기각: 첫 커밋 시도에서 pre-commit의 `check-mutations`가 `expect_output` 없는 변이 셋(14·25·36)을 알렸다.** 이미 있는 훅이 커밋 앞에서 막은 것이고 처방한 열린 행(350 닫힘, 579 열림 6회차)이 있다. 인계 세션의 `--check`와 전체 실행은 그것을 알리지 않았다는 사실은 11항 "고친 것 4"에 적혀 있다. 훅이 제 몫을 했다.
- **기각: 카나리아 둘을 `--control-commit` 없이 돌려 "명세 오류"로 아무것도 돌리지 않고 2로 끝났다.** 도구가 그 자리에서 까닭과 처방을 냈고 두 명세의 머리 주석이 이미 그 인자를 일러 두었다.
- **기각: `CODING_STANDARDS.md` 12행에 "2026-10-12부터는 같은 실수의 다섯 번째"라는 거짓 날짜를 썼다.** 셀프 리뷰의 표준 축이 잡았다. 기준을 어겨 리뷰가 잡은 사건이 아니라 이 PR의 사실 오류를 리뷰가 제 몫으로 잡은 것이라 회차로 세지 않고, 검사로 옮길 수 있는 꼴(날짜와 문턱의 대응)도 아니다.
- **기각: 컨텍스트가 20만 토큰을 넘어 인계가 두 번 있었다.** 인계 계기가 설계대로 돈 것이고 이 세션이 일을 잃지 않았다.

**만료.** `uv run python tools/queue_open_rows.py`와 `git fetch origin` 뒤 `--ref origin/main`을 붙인 출력이 "만료할 행"으로 같은 열다섯(435 319 362 438 439 441 443 444 446 447 450 451 452 453 454)을 냈다. 문턱을 올려 보호선이 5회차로 오른 값이다. 열다섯 모두 취소선과 `만료 2026-11-07 (ADR 0036)`을 달아 닫았고, 닫은 뒤 같은 도구가 열린 행 117개, 만료할 행 (없음)을 냈다(처음 132개). 435와 362는 옛 도구에서 빠지던 행이다(앞 세션이 `git show HEAD:tools/queue_open_rows.py`를 풀어 같은 날짜로 손으로 쳐서 본 것이고, 11항 "고친 것 2"에 있다. 이 세션은 옛 도구를 다시 치지 않았다). 열 줄 수와 "처음 132개"는 이 세션이 위 두 명령과 닫은 뒤의 같은 명령을 손으로 쳐서 본 출력이다. 이 열다섯을 닫은 변경은 이 PR의 `.scratch/retro-queue.md` diff 30줄에 든다.

회차를 더한 행도, 이 세션에서 반영한 것도 없다. 문턱이 오른 뒤 chore 계기는 회차 5 이상 열 행(420 430 431 565 558 579 214 475 499 535)이고, 앞 회고가 계기로 본 578은 앞 회고가 4회차로 적었고 위 "회차 5 이상" 출력에 들지 않아 더는 계기가 아니다(출력은 이 세션이 손으로 쳐서 읽었고, 578의 회차 수는 앞 일지 `2026-11-06-12-retro-queue-per-item-spec.md`에서 읽었다).

## 다음

이 PR이 retro-queue-per-item의 티켓 01(문턱 다섯)을 닫는다. 구현은 티켓이 차례로 연다.

- **막힌 것이 없는 티켓은 02(대기열 분할)다.** `.scratch/retro-queue-per-item/issues/02-retro-queue-one-file-per-item.md`의 `Blocked by`가 01뿐이고 이 PR이 병합되면 풀린다. 티켓이 크다고 적어 두었으니 한 세션에 못 하면 인계로 잇는다. 02는 옛 대기열 파일을 고친 열린 PR이 적은 때에 병합한다(티켓 02 "PR을 연 뒤").
- **02 뒤에 03(리뷰 봇 경로 거르기)과 04(일지 이름)가 나란히 열린다.** 05는 03과 04 뒤, 06은 05 뒤, 07은 06 뒤다.
- **이 PR이 명세 목록 밖에서 고친 것**은 PR 본문에 있다. 열린 행 열다섯(362 420 490 493 500 559 560 561 562 563 566 567 568 569 580)과 새 카나리아 명세 `next_session_queue_threshold.toml`이다.
- **인계 세션이 잰 것 가운데 이 세션이 다시 재지 않은 것**(pytest 296.1초, web-verify 469.5초, 빨강 7건, 카나리아 통과 4)은 커밋 때의 pre-commit이 다시 돌았고, PR의 CI가 전체를 다시 돈다.
- 지시문이 말한 `tests/tools/test_rerun_runner.py::test_다른_판의_확인을_쥐고_돌던_동안에도_첫_인계에서_멈춘다`는 인계 세션의 전체 러너에서 빨갛지 않았고 원인을 진단하지 않았다. 다시 빨가면 `diagnosing-bugs`로 간다.
