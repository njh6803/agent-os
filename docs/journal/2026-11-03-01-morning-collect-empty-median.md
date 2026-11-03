# 2026-11-03 (01) 아침 수집이 빈 목록의 중앙값에서 멈춘 것을 고친다

브랜치 `chore/039-morning-collect-empty-median`, 티켓 `.scratch/harness/issues/039-morning-collect-empty-median.md`. 세션 제목은 `【매일 09:00】 아침 보고 · 종합`(예약 작업 세션)이다.

## 사용자 프롬프트

예약 작업 `daily-morning-report`가 이 세션을 열었다(지시문은 `tools/morning_tasks/common.md`·`summary.md`를 따르라는 것). 종합 보고의 수집이 실패한 뒤 다음 단계 상자의 버튼으로:

> 사용자: 고치기 시작

버튼이 보낸 글(이 세션이 버튼에 적은 것): "tools/morning_collect.py의 _summary_piece가 자동 압축이나 헤드리스 시작이 없는 날 빈 목록의 중앙값을 구해 죽는 버그를 시험 먼저 고치고, 11-02 아침 보고를 다시 돌려 줘."

## 한 것

- 09:11 KST 종합 보고 준비: 토큰 보고서는 11-02 날짜로 이미 갱신됨, 주간 한도 3% 기록. 수집(`uv run --directory C:/project/agent python -m tools.morning_collect --reports <보고 폴더> --day 2026-11-02`)이 종료 1, 마지막 줄 `statistics.StatisticsError: no median for empty data`. 트레이스백은 `_summary_piece`의 1152행(압축 직전 대화의 중앙값)이었다.
- 원인(코드를 읽었다): 요약 줄은 `(compact if before else "")`로 빈 목록을 거르려 했지만 `compact`·`first`를 그 앞에서 무조건 `statistics.median`으로 만들었다. #332(f0f80ea9)가 들인 두 줄이다.
- 고침: 두 글을 목록이 비지 않았을 때만 만든다. 시험에서 부르려고 `_summary_piece`를 `summary_piece`로 공개했다(`cost_rows`·`session_rows`처럼).
- 시험 `test_요약은_자동_압축도_사람이_열지_않은_세션도_없는_날에_중앙값_없이_나온다`가 고치기 전 코드에서 같은 `StatisticsError`로 빨갰고(손으로 봤다), 고친 뒤 `tests/tools/test_morning_collect.py` 67개가 모두 점으로 찍혔다(요약 줄은 백그라운드 결과로 아직 확인하지 않았다).
- 고친 워크트리 코드로 11-02 수집을 다시 쳐 종료 0, 첫 줄이 `...\reports\2026-11-02.data.json`이었다(손으로 봤다). 이 수집 JSON·시트는 보고 폴더에 남아 있고, 그리기는 아직 하지 않았다.
- 두 파일의 `ruff check`·`ruff format --check`·`pyright`는 초록. `tools/run_checks.py`를 백그라운드로 띄웠다가 인계로 멈췄다.

- (이어받은 세션) `uv run pytest tests/tools/test_morning_collect.py -q`를 다시 쳐 `67 passed in 102.13s`로 끝났다. 인계 때 요약 줄이 나오지 않은 것은 다른 명령과 겹친 탓으로 보며 재지는 않았다.
- "고치기 전 코드에서 빨갰다"는 함수 이름을 `summary_piece`로 먼저 바꾼 상태에서 본 것이다. 원본 그대로면 시험 모듈의 import가 먼저 실패한다. 셀프 리뷰 두 축이 원본(`git show 9d7ffcd3:tools/morning_collect.py`)의 함수를 스크래치 사본으로 불러, 두 목록이 빈 경우와 한쪽만 빈 경우, 직전 컨텍스트를 모르는 자동 압축만 있는 경우가 모두 `StatisticsError`인 것을 손으로 봤다.

## 셀프 리뷰 (`/code-review`, base 9d7ffcd3, 미커밋 파일 둘·미추적 둘·커밋 0)

- 표준 축: 하드 위반 없음. Minor로 티켓의 `**대기열:** 없음`(553행이 이 버그다), 수용 기준의 옛 이름 `_summary_piece`, 시험이 "중앙값"이 없다는 것만 봐 줄이 통째로 사라져도 초록인 것, 한쪽만 빈 경우의 시험 부재, `$12.86`의 출처 없음. 판단 항목으로 `compact`·`first`의 같은 꼴, `summary_piece`만 공개인 것, 코드 주석의 "등".
- 명세 축: Major로 대기열 553 누락. Minor로 원인 문장이 "자동 압축이 없었기 때문"으로 단정해 컨텍스트 없는 자동 압축의 갈래를 빠뜨린 것, 수용 기준의 옛 이름. Nit로 빨강 주장의 순서.
- 고친 것: 티켓의 대기열 칸을 `553`으로, 원인 문장을 두 갈래로 적고 11-02가 앞의 갈래인 근거를 수집 JSON의 `token:auto_compactions` 0과 `metric:cost` $12.86으로 들었다(손으로 봤다). 수용 기준의 이름을 `summary_piece`로. 코드 주석을 빈 목록이 생기는 기간 셋으로. 첫 시험이 개수 문구까지 단언하게 하고, 한쪽만 빈 두 경우와 비지 않은 목록의 괄호를 보는 시험 `test_요약은_빈_목록의_중앙값만_빼고_비지_않은_목록의_중앙값은_적는다`를 더했다. 대기열 553행을 이 티켓으로 닫았다.
- PR 직전 리뷰에 밀 주장: 티켓의 "`before`는 자동 압축 가운데 직전 컨텍스트를 아는 것만 모으므로, 자동 압축이 없는 날에도, 있어도 컨텍스트 기록이 모두 없는 날에도 빈다", "11-02는 앞의 갈래다", 코드 주석 "중앙값은 목록이 빈 기간(자동 압축이 없거나 그 직전 컨텍스트를 모두 모르는 기간, 사람이 열지 않은 세션이 없는 기간)에 구하지 않는다".
- 다시 돌린 것: `uv run pytest tests/tools/test_morning_collect.py -q -k 요약은 -p no:randomly`가 `2 passed`, `uv run ruff check .`·`uv run ruff format --check .`가 초록, `uv run python tools/run_checks.py`가 종료 0으로 열 검사(check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest 262.8초, web-verify 454.9초) 모두 Passed였다(손으로 봤다). 커밋의 pre-commit 결과는 PR 본문에 적는다.
- 남긴 것: `compact`·`first`의 같은 꼴은 두 줄이라 묶으면 오히려 읽기 어렵다. `summary_piece`만 공개인 것은 시험이 부르는 함수만 공개하는 이 파일의 관례(`start_rows`, `cost_rows`)를 따랐다. `first`라는 이름은 이 변경 전부터 있던 것이다.

## 커밋과 PR 직전 리뷰

- 커밋 첫 시도는 pre-commit의 pytest에서 `tests/tools/test_rerun_runner.py::test_다른_판의_확인을_쥐고_돌던_동안에도_첫_인계에서_멈춘다` 하나가 `assert False`로 빨개 막혔다(1 failed, 6151 passed). 그 시험만 따로 돌리니 `1 passed in 7.27s`였고, 10-27 일지 둘(2026-10-27-01, 2026-10-27-03)이 같은 시험의 같은 실패를 부하에 흔들리는 시험(대기열 306이 받아들여 닫은 종류)으로 보고 다시 쳐서 지난 것과 같아 다시 쳤다. 둘째 시도에서 pre-commit이 모두 지나 커밋 `1f5210a2`가 들어갔다(Skipped는 카나리아 명세·헌법 판 검사 둘로, 해당 파일이 없다). 인용 대조 경고 하나(이 일지의 버튼 글 인용)는 앞 세션이 버튼에 적은 글이라 저장소에 원문이 없어 막지 않는 경고로 두었다.
- CodeRabbit CLI: 대체 둘을 먼저 돌린 뒤 PR 템플릿대로 `coderabbit auth status`를 쳤더니, 10-31 일지들이 적은 `Plan: Free`·`Seat: not assigned` 줄 없이 `User info`(계정·조직)와 `Review access`(`Default : njh6803/njh6803`)만 나왔다. 그래서 `coderabbit review --committed --base-commit 9d7ffcd3`를 직접 쳤고 `Review complete`, `No findings ✔`, 5개 파일 리뷰로 끝났다(CLI 0.7.5, 0.9.2 업데이트 알림, 손으로 봤다). `docs/constitution/operations.md` 리뷰 파이프라인 2의 "유료 전환 전까지 PR 직전 CLI 축은 구조적으로 비어 있고"와 어긋나는 관찰이다. 한 번 돈 것이라 이 PR에서는 그 문서를 고치지 않고 회고 후보로 넘긴다.
- 대체 둘(CLI가 도는지 보기 전에 돌렸다). `/security-review`: 지적 없음(새 입력 출처·경로·subprocess·비밀 없음). `bug-perf-review`: 0건(유효 0, 오탐 2, 보류 0). 밀 주장 넷은 모두 맞다고 냈고, 11-02 JSON의 값만 열지 않아 보류로 남겼는데 이 세션이 그 파일을 Read로 열어 `token:auto_compactions`가 0인 것을 봤다. 같은 파일의 다른 `median`·`fmean`·`max`·`min` 호출은 모두 빈 입력을 막는다고 냈다(코드를 읽었다).

## 결정·번복

- 하네스 일이라 워크트리 `morning-empty-median`에서 했고, 처음 붙은 브랜치 `worktree-morning-empty-median`을 티켓 stem `chore/039-morning-collect-empty-median`으로 바꿨다.
- 셀프 리뷰 직전에 인계 계기(컨텍스트 206,064 토큰)가 와서 `/code-review`를 밟지 않고 넘긴다.

## 인계

- 바꾸기 전 제목: `【매일 09:00】 아침 보고 · 종합`.
- `uv run pytest tests/tools/test_morning_collect.py -q`(백그라운드 `brd9o3u8r`)는 점 67개와 `[100%]`를 찍은 뒤 요약 줄 없이 인계 때까지(약 10분 넘게) 끝나지 않아 TaskStop으로 멈췄다. 통과로 세지 않는다. 같은 때 수집·pyright·`run_checks.py`가 함께 돌았다. 새 세션은 다시 쳐서 끝나는지부터 본다.
- `run_checks.py`(`bl3gs8gp9`)도 멈췄다. 워크트리 잠금을 풀었다.

## 인계 지시문

```
다음 작업: .scratch/harness/issues/039-morning-collect-empty-median.md. 아침 수집이 자동 압축·헤드리스 시작이 없는 날 빈 목록의 중앙값에서 멈추던 것을 고친 변경을 리뷰·커밋·병합하고 11-02 종합 보고를 그린다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 일지 docs/journal/2026-11-03-01-morning-collect-empty-median.md 를 읽고 티켓 039의 셀프 리뷰부터 잇는다
브랜치: chore/039-morning-collect-empty-median
모델: Opus 5.5 / medium. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-03-01-morning-collect-empty-median.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(tools/morning_collect.py, tests/tools/test_morning_collect.py, 티켓 039, 이 일지)이 워크트리에 있고 셀프 리뷰(/code-review origin/main, 티켓 039)부터 한다. tools/run_checks.py 는 인계로 멈춰 결과가 없다. 병합 뒤에는 주 체크아웃이 당겨진 다음 C:\project\agent\tools\morning_tasks\common.md 의 "그리기와 보고"를 --report summary 로 따라 11-02 종합 메모를 쓰고 그린다(수집 JSON·시트는 보고 폴더에 이미 있다). docs/journal/2026-11-03-01-morning-collect-empty-median.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지, 그 뒤 11-02 종합 보고 그리기
```
open-session을 부른다 2026-11-03T02:38:48Z

## 인계 (커밋 뒤)

- 이 세션(지시문으로 연 둘째 세션)의 지금 제목: `chore/039-morning-collect-empty-median`. 일지 커밋 `7cd407c8` 뒤에 인계 계기(컨텍스트 226,975 토큰, 경계 `커밋 뒤`)가 와서 넘긴다. 이 절은 커밋하지 않았으니 새 세션이 다음 커밋에 싣는다.
- 회고 후보(retro가 판정): `coderabbit auth status`에 `Plan`·`Seat` 줄이 없고 CLI 리뷰가 실제로 돈 것이 `docs/constitution/operations.md` 리뷰 파이프라인 2의 "CLI 축은 구조적으로 비어 있다"와 어긋난다(위 "커밋과 PR 직전 리뷰" 절).

## 인계 지시문 (커밋 뒤)

```
다음 작업: .scratch/harness/issues/039-morning-collect-empty-median.md. 아침 수집이 빈 목록의 중앙값에서 멈추던 것을 고친 변경을 푸시·PR·병합하고 11-02 종합 보고를 그린다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 일지 docs/journal/2026-11-03-01-morning-collect-empty-median.md 를 읽고 티켓 039의 셀프 리뷰부터 잇는다
브랜치: chore/039-morning-collect-empty-median
모델: Opus 5.5 / medium. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-03-01-morning-collect-empty-median.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰·반영·검증·커밋 둘(1f5210a2 코드, 7cd407c8 일지)과 PR 직전 리뷰(/security-review, bug-perf-review, CodeRabbit CLI 모두 지적 없음)를 마쳤다. 푸시하지 않았고 열린 PR은 없다. 남은 단계: 일지의 "인계 (커밋 뒤)" 절(미커밋)을 커밋하고, 푸시와 PR(/git-pr. PR 체크리스트의 PR 직전 리뷰 줄은 일지 "커밋과 PR 직전 리뷰" 절의 결과), @coderabbitai review 코멘트와 merge.md 2의 봇 회차, 워크트리에서의 병합(merge.md "워크트리에서 병합할 때"), 회고. 병합 뒤에는 주 체크아웃이 당겨진 다음 C:\project\agent\tools\morning_tasks\common.md 의 "그리기와 보고"를 --report summary 로 따라 11-02 종합 메모를 쓰고 그린다(수집 JSON·시트는 보고 폴더에 이미 있다). docs/journal/2026-11-03-01-morning-collect-empty-median.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지, 그 뒤 11-02 종합 보고 그리기
```
open-session을 부른다 2026-11-03T03:21:02Z

## PR과 병합 (셋째 세션)

- 지시문으로 연 셋째 세션이 제목을 `chore/039-morning-collect-empty-median`으로 바꾸고 워크트리 `morning-empty-median`에 들어와 위 "인계 (커밋 뒤)" 절을 커밋했다(`edb25fce`, pre-commit 열 검사 모두 Passed, 손으로 봤다).
- `git fetch origin main` 뒤 `git log HEAD..origin/main`이 비어 rebase 없이 푸시하고 PR #456을 열었다. `@coderabbitai review`를 남기고 `tools/wait_ci.py 456`이 `끝: 모두 통과`(헤드 edb25fc)로 끝났다(손으로 봤다).
- 봇 첫 회차. CodeRabbit은 `No actionable comments`. claude-review는 Minor 하나(`test_요약은_빈_목록의_중앙값만_빼고_비지_않은_목록의_중앙값은_적는다`가 같은 `Period`를 바꿔 가며 시나리오 둘을 이어 단언한다)와 Nit 하나(줄 찾기 `next(...)` 네 줄의 반복)를 냈다. 둘 다 고쳤다. 그 시험을 `test_요약은_직전_컨텍스트를_모르는_자동_압축만_있으면_압축_중앙값만_뺀다`와 `test_요약은_사람이_열지_않은_세션이_없으면_첫_호출_중앙값만_뺀다`로 나누고, 기간을 만드는 `하루_기간`과 두 줄을 찾는 `압축_줄과_헤드리스_줄` 도우미를 두었다. 위 셀프 리뷰 절의 옛 시험 이름은 그때의 기록이라 두었다. `uv run pytest tests/tools/test_morning_collect.py -q -k 요약은 -p no:randomly`가 `3 passed`였다(손으로 봤다).

## 회고

후보 넷: 승인 하나, 기각 둘, 일지에만 남기는 것 하나. 넘긴 것은 없다.

- 승인(고침, 대기열 557, 1회차): `docs/constitution/operations.md` 리뷰 파이프라인 2의 "PR 직전 CLI 축은 구조적으로 비어 있다"가 이번 관찰(`coderabbit auth status`에 `Plan`·`Seat` 줄이 없고 `coderabbit review --committed`가 `No findings`로 돌았다, 위 "커밋과 PR 직전 리뷰" 절)과 어긋난다. 사건은 이 세션의 관찰이고, 층은 그 문서의 사실 고침이며, PR 하나로 되돌릴 수 있다. 한 번의 관찰이라 무료 판의 한도가 바뀐 것인지 가르지 못해 지금 고치지 않고, 다음 PR에서 같으면 고치도록 행에 적었다. PR 템플릿의 판정 길(PR마다 `auth status`를 본다)은 그대로라 ADR은 필요 없다.
- 기각: claude-review의 Minor(시나리오 둘을 한 시험에 이은 것). `CODING_STANDARDS.md` 리뷰 관점 4가 리뷰에 맡긴 기준을 리뷰가 잡은 것이라 회차 셈에서 빠지고, 검사로 옮길 꼴도 아니다.
- 기각: 둘째 세션 인계 때 `pytest`가 요약 줄 없이 멈춘 것. 같은 때 다른 무거운 명령이 함께 돌았고 다시 친 판은 끝났다(위 "한 것"). 원인을 가른 사건이 없다.
- 일지에만: 첫 코드 커밋의 pre-commit에서 `test_rerun_runner.py`의 시험 하나가 부하로 빨갰다. 대기열 306이 받아들여 닫은 종류의 새 사례라 잇지 않는다.
- 만료: `uv run python tools/queue_open_rows.py`와 `--ref origin/main`의 두 출력에 모두 든 349·351·363·364·366·371을 `만료 2026-11-03`으로 닫았다.

## 다음

- PR #456 병합 뒤 이 세션이 11-02 종합 아침 보고를 그린다(`C:\project\agent\tools\morning_tasks\common.md`의 "그리기와 보고", `--report summary`. 수집 JSON·시트는 보고 폴더에 있다).
- 대기열 557: 다음 PR의 PR 직전 리뷰에서 `coderabbit auth status`와 CLI 리뷰가 또 돌면 `operations.md` 리뷰 파이프라인 2를 고친다.
- 그 밖의 다음 작업은 `.scratch/plan.md`의 프론티어다.
