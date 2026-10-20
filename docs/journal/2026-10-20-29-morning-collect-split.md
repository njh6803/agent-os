# 2026-10-20 (29) 아침 수집 도구를 바깥 명령 층과 절 짓기로 나눈다

브랜치 `chore/morning-collect-split`. PR #322(아침 보고 형식 개선, 일지 2026-10-20-22)의 claude-review가 Minor로 짚은 구조 넷을
받은 후속이다. PR #322를 연 세션("일일 아침 9시 보고서 등록")이 이 세션을 곁 세션으로 열었다. 동작을 바꾸지 않는 리팩터라
보고의 형식과 모으는 값은 그대로다. 구현 도중 컨텍스트가 한 번 압축되었다.

## 요청

이 세션의 첫 메시지는 사람이 아니라 연 세션이 쓴 글이다. 원문:

```
Background (from the session that started this one):
매일 아침 09:10에 예약 작업 `daily-morning-report`가 저장소의 `tools/morning_collect.py`(수치를 data.json으로 수집)와 `tools/morning_report.py`(data.json과 모델 메모를 합쳐 보고서 md로 렌더)를 부른다. 두 도구는 PR #322로 main에 병합되었다(b78317fe). PR 봇의 둘째 회차에서 구조에 관한 Minor 넷을 이 후속 작업으로 넘기기로 판정했고, 그 내용은 일지 2026-10-20-22의 "다음"에 적혀 있다. 이 작업은 동작을 바꾸지 않는 리팩터링이다. 그러므로 보고서의 형식이나 수집하는 값을 바꾸지 않는다. 예약 작업은 주 체크아웃의 `tools/`를 부르므로, 병합 뒤 주 체크아웃을 당기는 일은 `tidy-checkouts`가 맡는다.

Task:
`tools/morning_collect.py`(약 1,850줄)의 구조를 동작은 그대로 두고 나눈다. PR #322(njh6803/agent-os)의 claude-review가 Minor로 짚은 넷이 범위다.

1. `collect()`(약 130줄)에서 병합 PR의 동시성 버킷 계산과 부하 문구 조립을 이름 있는 함수로 뺀다.
2. `_sweep_section`을 레벨 스윕 절과 티켓 분할 절로 나눈다.
3. JSON 풀이 함수 `_obj`·`_list`·`_str`·`_int`가 `tools/morning_collect.py`와 `tools/morning_report.py`에 같은 모양으로 둘씩 있다. 한 곳에 두고 두 도구가 함께 쓰게 한다.
4. 바깥 명령 층(gh·git·tasklist 호출)과 절 조립을 가른다. `Collected.value()`가 자기 값을 바꾸는 방식과 `merged_got`이 새 객체를 돌려주는 방식이 섞여 있으므로 한쪽으로 맞춘다.

시작 전에 읽을 것: `docs/journal/2026-10-20-22-morning-report-format.md`의 "다음"과 "PR 봇 첫 회차" 절, `.claude/rules/tools.md`(바깥 명령의 시간 제한 규칙), CLAUDE.md의 작업 규약.

완료 기준:
- `tests/tools/test_morning_collect.py`와 `tests/tools/test_morning_report.py`가 그대로 통과한다. 동작을 바꾸는 시험 수정은 하지 않는다.
- 기존 `~/.claude/scheduled-tasks/daily-morning-report/reports/2026-10-19.data.json`과 `2026-10-19.notes.json`으로 새 `morning_report.py`를 돌린 결과가, 같은 폴더의 `2026-10-19.md`와 바이트 단위로 같다. 이 폴더의 파일은 덮어쓰지 말고, 출력은 스크래치패드에 낸다.
- 검증 명령(`uv run python tools/run_checks.py`와 ruff 둘)이 초록이고, 저장소 규약대로 셀프 리뷰, PR, 일지, 병합까지 간다.
- 브랜치는 `chore/morning-collect-split`이고 `origin/main`에서 딴다.
```

## 한 일

- 바깥 명령 층. 새 `tools/morning_sources.py`에 gh·git·tasklist를 부르는 함수와 그 출력의 풀이를 옮겼다(`_run`과
  `CALL_TIMEOUT`, `merged_prs`, `open_prs`, `pr_view`, `ci_runs`, `processes`, `worktree_entries`, `journal_next`,
  옛 `_latest_journal`인 `latest_journal`, 옛 `_tickets`인 `ticket_paths`). `collect`가 git 한 줄씩을 바로 부르던 자리 셋은 이름 있는 함수로
  뺐다(`worktree_list`, `main_text`, `branch_subject`).
- JSON 풀이. `morning_report.py`의 `_obj`·`_list`·`_str`·`_int`를 공개 `json_obj`·`json_list`·`json_str`·`json_int`로
  바꾸고, `morning_collect`의 `_time`을 `json_time`으로 그 곁에 옮겼다. 수집 도구 둘이 그것을 가져다 쓴다. 따로 모듈을 두지
  않은 것은 그리기 도구가 스크립트(`python tools/morning_report.py`)로 돌아 `tools` 패키지를 가져오지 못해서다. 스크립트
  자리에서 `importlib.util.find_spec("tools")`가 None인 것을 스크래치 탐침으로 손으로 봤다(커밋하지 않음).
- `collect()`를 133줄에서 93줄로 줄였다. 동시성 버킷은 `_concurrency_buckets`, 병합 PR의 날짜별 갈래 수는 `_merged_kinds`,
  부하 줄과 그 값은 `_load_line`이다. 여러 번 읽거나 읽은 것으로 다음에 읽을 것을 고르는 일은 `_gather_ledger`,
  `_gather_rounds`, `_gather_tickets`, `_gather_worktrees`, `_gather_hooks`, `_gather_prs`가 맡는다.
- `_sweep_section`을 `_sweep_piece`(레벨 스윕 표와 줄)와 `_ticket_piece`(티켓 분할 표와 줄)로 나누고, 둘을 상세 7 한 절로
  묶는 `_model_section`을 두었다. 보고 형식이 상세 7 한 절에 표 둘이라 절 번호와 원본 줄은 그대로다. 절의 한 조각(표 하나,
  그 아래 줄, 모은 것)은 `Piece`이고, 비싼 작업 표(`_works_piece`, 옛 `_works_table`)도 같은 모양이다.
- 읽기와 짓기. 절을 짓는 함수(`_*_section`, `_*_piece`)는 받은 값으로만 짓는다. 훅 절은 `_gather_hooks`(설정, 들인 날, 주
  체크아웃, 세션 기록, 표에 오른 훅 파일)와 `_hook_section`으로, 어제 절은 `_gather_worktrees`(워크트리마다 기록 시각과
  브랜치 제목)와 `_yesterday_section`으로 갈랐다. 대기열 절은 `main_text`가 읽은 글을 받는다.
- `Collected`는 한쪽으로 맞췄다. 절을 짓는 함수마다 자기 것을 하나 만들어 `value`와 새 `add`로 채우고 돌려주며, 인자로 받은
  것은 바꾸지 않는다. `merged_got`은 새것 하나에 `add`로 합친다. 값을 더할 때마다 새 객체를 돌려주는 쪽은 절마다 값이 수십
  개라 짓는 코드가 길어지고, 바꾸는 범위를 그 함수가 만든 객체로 좁히면 출력 인자를 쓰지 않는다는 `CODING_STANDARDS.md`의
  기준도 지킨다.
- 시험. `tests/tools/test_morning_collect.py`는 옮긴 함수 아홉의 import 자리와 독스트링 첫 문장만 고쳤다.
  `test_morning_report.py`는 그대로다.

## 판단

- 바깥 호출의 수까지 옛 판과 맞췄다. 옛 `_hook_section`은 설정을 읽지 못하면 일찍 돌아가 `gh run list`를 부르지 않았다. 새
  판은 `_gather_hooks`가 까닭을 돌려주면 `collect`가 `ci_runs`를 부르지 않는다. 훅 파일의 하는 일은 옛 판처럼 표에 오른 훅만
  읽어, 표 밖 훅 파일의 인코딩 오류가 새로 수집을 멈추지 않게 했다.
- `_last_record`(워크트리 폴더 세션 기록의 수정 시각)는 `morning_collect`에 두었다. gh·git·tasklist가 아니라 세션 기록을 읽는
  자리라 `scan_transcripts`와 같은 쪽이다.
- `.claude/rules/tools.md`의 클라우드 gh 항목은 고치지 않았다. 그 항목은 도구 단위(`morning_collect`)의 실패 갈래와
  `gh pr …`를 부르는 도구 수(넷)를 적는다. 호출 자리가 `morning_sources`로 옮겨 가도 CLI는 `morning_collect` 하나이고
  `morning_sources`는 진입점이 없어, 갈래와 수가 그대로 참이다. 그래서 그 항목의 카나리아도 다시 돌리지 않았다.
- 컨텍스트 압축 뒤 모듈 독스트링의 "짜임" 문단이 "`_hook_section`만 훅 파일과 세션 기록을 읽는다"고 적었는데, 그 함수가
  `hook_report`를 거쳐 git도 불렀다. 문장을 고치기보다 훅 절을 읽기와 짓기로 나눠 "절을 짓는 함수는 파일도 명령도 읽지
  않는다"를 참으로 만들었다.
- 셀프 리뷰를 띄우기 전에 `morning_sources` 독스트링의 "실패하면 None(`worktree_list`는 빈 목록)"이 `ticket_paths`(빈
  사전)와 `latest_journal`(빈 글 둘)에서 틀린 것을 찾아, 목록·사전·글을 돌려주는 셋을 이름으로 적었다.

## 검사

- 같음 하네스(세션 스크래치패드의 `equiv.py`, 커밋하지 않음). `subprocess.run`(다른 도구가 부르는 git 포함)과
  `_last_record`를 녹화하고 재생하며, `now`와 앞 날 메모의 열쇠도 녹화한 값을 쓴다. 2026-10-19를 옛 판(`origin/main`
  사본)으로 실제로 모은 것과 그 녹화를 재생한 옛 판이 바이트 단위로 같았다(놓친 호출 0). 새 판의 재생도 같았다(놓친 호출
  0, 수집 JSON과 목록 98,928바이트). 훅 절을 나눈 뒤에 다시 돌려 같았다.
- gh를 모두 실패시킨 길. 병합 PR을 몰라 "모름"으로 남는 워크트리의 기록 시각과 브랜치 제목 28개는 녹화에 없어 실제로
  부른다. 훅 절을 나눈 뒤의 대조에서 한 브랜치(`feature/02-runtime-names-the-failure-cause`)의 마지막 커밋 제목이 달랐다. 옛
  판을 돌린 18:06과 새 판을 돌린 사이인 18:11에 다른 세션이 그 브랜치에 커밋했다. 옛 판을 다시 돌리자 새 판과 바이트 단위로
  같았다.
- 완료 기준의 그리기. 보고 폴더의 `2026-10-19.data.json`·`notes.json`을 스크래치패드로 복사해 옛 판과 새 판의
  `morning_report.py`로 그렸다. 둘 다 폴더의 `2026-10-19.md`(20,026바이트)와 같았고 상태 파일도 같았으며 경고는 0이었다.
  보고 폴더에는 쓰지 않았다.
- 실제 CLI. `uv run python -m tools.morning_collect --reports <스크래치> --day 2026-10-19`가 0으로 끝나 수집 JSON(70,241바이트)과
  목록 147줄을 냈다. 하네스는 `collect`와 `_sheet`를 바로 불러 진입점을 거치지 않았기 때문에 따로 돌렸다.
- 시험 두 파일 86 통과, ruff 둘 초록, pyright 0. `uv run python tools/run_checks.py`는 여덟 검사 모두 Passed였다(pytest
  243.0초, web-verify 280.8초). 훅 절을 나눈 뒤, `morning_sources` 독스트링을 고치기 전이다.

## 병합 순서

셀프 리뷰 직전 `tools/sibling_overlap.py`가 `morning-report-format` 워크트리에서 같은 파일을 고친 것을 알렸다. 그 워크트리는
`chore/morning-report-full-detail`(일지 2026-10-20-28, 커밋 전)로, 이 세션을 연 세션이 사용자 요청으로 아침 보고의 상세를
되살리며 `morning_collect.py`에 429줄을 더하고 있다. 같은 네 파일을 두 세션이 크게 고치므로 연 세션에 병합 순서를 물었다.
추천은 그쪽이 먼저 병합하고 이 세션이 그 판 위에서 다시 나눈 뒤 같음 비교를 그 판과 다시 하는 것이다.

연 세션의 답(세션 사이 메시지 원문의 앞 두 줄):

> 병합 순서는 추천대로 chore/morning-report-full-detail을 먼저 병합합니다.
> 그쪽은 셀프 리뷰와 로컬 커밋까지만 하고 기다려 주세요. 이쪽은 지금 셀프 리뷰를 반영하는 중이고, 그 뒤 PR 직전 리뷰, 봇
> 회차, 병합 순으로 갑니다. 병합하면 병합 커밋 SHA와 함께 다시 알리겠습니다.

같은 메시지가 다시 나눌 때의 참고로 넘긴 것: 그 변경은 `morning_collect.py`에 순수 함수
열하나(`cost_by_concurrency`, `ticket_cells`, `off_cells`, `kind_rows`, `agent_rows`, `cost_rows`, `start_rows`,
`branch_rows`, `shown_path`, `DayRow.sessions` 필드, `hook_rows`의 `[:3]` 제거)를 더하고, `_token_section`(인자 `handoff`·`pr_at`
추가), `_parallel_section`(`shares` 인자 추가), `_works_table`(표 목록을 돌려준다), `queue_part`, `_sweep_section`의 모양을
바꾼다. `TOP_COMMANDS`는 10, `TOP_TOOLS`는 5, 새 상수 `TOP_LARGE`는 3이다. 그 판의 출력이 바뀌므로 녹화·재생 비교는 병합된
판과 다시 한다.

## 셀프 리뷰

인계 계기가 `셀프 리뷰 직전`에 왔다(컨텍스트 200,969). 이 세션은 `parentSessionId`가 있고 `detached`가 거짓인 곁 세션이라
`next-session`의 인계하지 않는 때에 들어 넘기지 않고 이었다.

범위: base `0262841b`, 바뀐 파일 셋, 커밋 0, 미추적 둘(`tools/morning_sources.py`, 이 일지의 머리 한 줄).

### 표준 축

Critical·Major 0. 서브에이전트가 옛 판과 새 판의 `collect --day 2026-10-19`를 같은 루트에서 돌려, 실시간 값(메모리 MB, "N분
전")만 다르고 나머지가 같다고 보고했다. 지적은 문서 사실의 Minor 다섯과 Nit 둘, 판단 몫의 냄새였다.

고친 것(새로 쓴 문장은 PR 직전 `bug-perf-review`에 밀 주장으로 넘긴다):
- `morning_collect` 독스트링의 "gh·git·tasklist는 `morning_sources`가 부른다"에 `hook_report`가 부르는 git(`_gather_hooks`,
  `_handoff_from`)이 반례였다. 새 문장: "이 도구가 부르는 gh·git·tasklist는 `morning_sources`에 있고, 다른 도구를 불러 쓰는
  읽기는 그 도구의 명령을 그대로 쓴다(훅의 들인 날과 주 체크아웃을 찾는 git은 `hook_report`의 것이라 시간 제한과 실패
  갈래도 그 도구의 것이다)."
- 같은 독스트링 "짜임"의 읽는 함수 목록에 `main`(`latest_checks`)과 `token_report`·`hook_report`의 읽기가 빠졌다. 닫힌 목록을
  일반 조항으로 바꾸고 목록은 예로 두었다. 새 문장: "파일과 명령을 읽는 것은 `main`(앞 날의 메모), `collect`, 그리고 그
  둘이 부르는 읽기 함수다. 읽기 함수의 예는 `morning_sources`, `token_report`·`hook_report`의 읽기, `scan_transcripts`,
  `_handoff_from`, `_last_record`이고, …"
- `Collected` 독스트링이 "`value`·`add`로 채운다"고 했으나 `refs`·`branches`·`queue`는 칸에 바로 넣는다. 새 괄호: "(값은
  `value`로, 이름 지을 것은 그 칸에 바로, 다른 조각이 모은 것은 `add`로)".
- `morning_sources` 독스트링의 "목록·사전·글을 돌려주는 셋은 빈 것을 돌려준다"에 `merged_prs`·`open_prs`·`ci_runs`(목록이지만
  None)와 `main_text`·`branch_subject`가 반례였다. 새 문장: "실패하거나 시간을 넘기면 대개 None을 돌려주고, 빈 값과 실패를
  가르지 않는 함수는 빈 것을 돌려준다(예: `worktree_list`, `ticket_paths`, `latest_journal`). 함수마다의 값은 그 반환형과
  독스트링이 원천이고, …"
- `latest_journal` 독스트링(옛 `_latest_journal`의 것을 그대로 옮겼다)이 접두 일치와 읽기 실패를 적지 않았다. 새 문장:
  "`origin/main`에서 `## 다음`으로 시작하는 줄이 있는 가장 늦은 일지의 (경로, 그 일지의 `## 다음` 절). 그런 일지가 없으면 빈
  글 둘이다. 그 일지를 읽지 못하거나 그 줄이 `## 다음(…)`처럼 덧붙은 것뿐이면 절은 빈 글이다(`journal_next`)." 경계 입력
  셋(정확한 머리, 덧붙은 머리, 머리 없음)으로 `journal_next`를 불러 `'- 할 일'`, `''`, `''`을 봤다(스크래치 탐침).
- [Nit] `ticket_paths` 독스트링이 코드보다 좁았다. 새 문장: "`origin/main`의 `.scratch` 아래에서 경로에 `/issues/`가 든 `.md`
  파일을 이름(확장자를 뗀 것)마다."
- 클라우드 gh 서술. `.claude/rules/tools.md`는 `gh pr view <번호> --json number`가 됐다고 적는데 두 독스트링이 `gh pr view`가
  실패한다고 했다. 새 문장(`morning_collect`): "클라우드 세션에서 `gh pr list`는 GraphQL이 막혀 실패했고, `gh pr view`는 요청한
  필드에 따라 실패하기도 되기도 했다(`.claude/rules/tools.md`). 이 도구가 `gh pr view`로 요청하는 필드와 `gh run list`는
  클라우드에서 본 기록이 없다." `morning_sources`에도 같은 뜻으로 적었다.
- 시험 독스트링의 "`collect`를 실제로 돌려 확인했다(일지 2026-10-20-22)"는 분리 전의 근거였다. "바깥 명령 층을 나눈 뒤는 일지
  2026-10-20-29 의 검사"를 덧붙였다.

남긴 것과 이유:
- [Nit] `.claude/rules/tools.md` 25행의 `morning_collect`. 위 판단 절대로 도구 단위 서술이 참이다.
- 긴 인자 목록과 짝으로 다니는 값(`_yesterday_section` 여덟, `_gather_tickets` 일곱, `(active, leftover)`, `(views, rounds)`).
  옛 `collect`의 지역 변수를 그대로 넘긴 것이고, 묶을 형식을 새로 지으면 요청의 넷을 넘는다. 판단 몫이다.
- 원시 값 집착(`ActiveWorktree.pr`의 글, `HookScan | str`, `(경로, 브랜치)` 튜플). `worktree_pr`의 글 갈래와 실패 까닭을 절의
  줄에 그대로 적는 흐름은 옛 판을 옮긴 것이다. 판단 몫이다.
- `collect`(독스트링까지 98줄)와 `_token_section`(89줄)의 크기. 요청의 넷에 없는 범위다.
- 시험이 없는 새 함수(`_load_line`, `_concurrency_buckets`, `Collected.add`, `json_int`, `json_time`). 출력은 같음 하네스가
  바이트로 잡았다. 시험 파일은 먼저 병합하는 형제 판도 고치므로, 그 판 위에서 다시 나눌 때 공개 함수(`json_time`)와
  `Collected.add`·`merged_got`의 시험을 더한다.
- [Nit] `test_morning_sources.py`를 따로 두지 않았다. 요청이 시험 두 파일을 그대로 통과시키라고 해서 시험 자리를 옮기지 않았다.
- 같은 모양의 JSON 풀이가 `hook_report`·`token_report`에도 있다. 요청은 아침 보고 도구 둘이라 범위 밖이다.
- [Nit] `c in FAILED or c.upper() in FAILED`와 `Collected.value`의 이름은 옛 판 그대로다.
- `latest_journal`이 `## 다음(…)` 머리의 일지를 가장 늦은 것으로 고르면 "다음"이 빈 글이 되는 것은 옛 판의 동작이다. 동작을
  바꾸지 않는 리팩터라 고치지 않고 후속으로 둔다.

### 명세 축

Critical·Major 0. 요청한 넷이 모두 들었고 옛 판정 아홉이 모두 지켜졌다고 보고했다. 서브에이전트가 따로 짠 녹화·재생
하네스로 네 갈래(정상, gh 전부 실패, 훅 설정 git 실패, `gh pr view`만 실패)를 돌려 수집 JSON·목록과 바깥 호출의 종류·횟수가
옛 판과 같았고, 훅 git이 실패한 갈래에서 `gh run list`는 0회였다. 2번(스윕 절 나누기)을 절이 아니라 조각 둘로 나눈 것은 보고
형식을 지키는 해석으로 맞다고 봤다. 표준 축과 겹친 지적(첫 문단의 gh·git·tasklist, `latest_journal`의 빈 글 둘,
`ticket_paths`, `tools.md`의 도구 수)은 위에서 고쳤거나 남겼다.

고친 것(새로 쓴 문장은 PR 직전 `bug-perf-review`에 밀 주장으로 넘긴다):
- [Nit] "짜임"의 "여러 번 읽거나 읽은 것으로 다음에 읽을 것을 고르는 일이 `_gather_*`다"에 `scan_transcripts`·`latest_journal`이
  반례였다. `_gather_*`를 그 일의 전부가 아니라 정의로 적었다. 새 문장: "`_gather_*`는 `collect`를 줄이려고 뗀 읽기로, 여러 번
  읽거나 읽은 것으로 다음에 읽을 것을 고른다."
- [Nit] `Collected` 독스트링의 "절을 짓는 함수마다 제 것을 하나 만들어"에 `_parallel_section`(`_load_line`이 만든 것을 이어받아
  채운다)이 반례였다. 새 문장: "절을 짓는 함수와 그 도움 함수(`_load_line` 등)는 스스로 만든 것이나 자기가 부른 도움 함수가
  돌려준 것을 채워 돌려주며(…), 인자로 받은 것은 바꾸지 않는다."
- [Minor] `morning_sources` 머리의 "부르는 바깥 명령(gh·git·tasklist)"이 `hook_report`를 거친 git까지 덮는 것처럼 읽혔다. 새
  문장: "아침 보고 수집 도구(`tools/morning_collect.py`)가 직접 부르는 바깥 명령(gh·git·tasklist)과 그 출력의 풀이. 수집 도구가
  다른 도구(`hook_report`)를 거쳐 부르는 git은 그 도구에 있다."

남긴 것과 이유:
- [Nit] 1번이 두 함수만 빼라고 했는데 `_gather_ledger`·`_by_branch`·`_agent_costs`·`_merged_kinds`·`_ticket_row`도 뺐다. 4번(읽기와
  짓기를 가른다)을 위해 `collect` 안의 읽기와 계산을 이름으로 뗀 것이고 동작은 같다.

다시 돌린 명령: 두 축의 반영은 독스트링뿐이라 ruff 둘을 손으로 쳐 초록이었고, 나머지는 첫 커밋의 pre-commit으로 갈음한다.

## 다음

연 세션이 `chore/morning-report-full-detail`을 병합했다고 알리면(병합 커밋 SHA와 함께) 이 브랜치를 그 판 위에서 다시 나눈다.
첫 커밋은 그때 대 볼 본보기다.
- 같음 하네스의 "옛 판"을 병합된 판으로 바꿔 다시 녹화하고, 다시 나눈 판을 정상 길과 gh 전부 실패 길로 견준다.
- 완료 기준의 그리기를 병합된 판으로 다시 본다. 형제 판이 보고 형식을 바꾸므로, 폴더의 `2026-10-19.md`와 같은지가 아니라 병합된
  판의 `morning_report.py`가 그린 것과 같은지를 본다(요청의 완료 기준과 어긋나는 점은 PR 본문에 적는다).
- 두 축이 남긴 시험(`json_time`, `Collected.add`·`merged_got`)을 그때 더한다.
- 다시 나눈 diff로 셀프 리뷰를 한 번 더 돌린 뒤 PR 직전 리뷰, PR, 봇 회차, 병합으로 간다.

이 절을 쓰자 회고 계기 훅이 retro를 돌리라고 했다. 이 절은 단계를 닫는 것이 아니라 병합을 기다리는 동안의 중간 계획이고 이
세션이 뒤 일을 잇는다. retro의 계기(그 스킬 설명의 "단계를 닫을 때")에 들지 않아, 병합해 단계를 닫을 때 돌린다.
