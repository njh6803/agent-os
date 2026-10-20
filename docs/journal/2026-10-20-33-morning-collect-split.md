# 2026-10-20 (33) 아침 수집 도구를 바깥 명령 층과 절 짓기로 나눈다

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
- 컨텍스트 압축 뒤 모듈 독스트링의 "짜임" 문단이 "`_hook_section`만 훅 파일과 세션 기록을 `hook_report`로 읽는다"고
  적었는데, 그 함수가 `hook_report`를 거쳐 git도 불렀다. 문장을 고치기보다 훅 절을 읽기와 짓기로 나눠, 절을 짓는 함수는
  파일도 명령도 읽지 않는다는 문장을 참으로 만들었다.
- 셀프 리뷰를 띄우기 전에 `morning_sources` 독스트링의 "실패하거나 시간을 넘기면 None을 돌려주고(`worktree_list`는 빈
  목록)"가 `ticket_paths`(빈 사전)와 `latest_journal`(빈 글 둘)에서 틀린 것을 찾아, 목록·사전·글을 돌려주는 셋을 이름으로
  적었다.

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
  둘이 부르는 읽기 함수다." 그 뒤의 예 목록은 아래 명세 축 반영에서 `_gather_*`를 더해 지금 독스트링의 꼴이 되었다.
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
- 시험 독스트링이 `collect`를 실제로 돌려 확인한 근거로 일지 2026-10-20-22만 들어, 분리 전의 근거였다. "바깥 명령 층을 나눈
  뒤는 일지 2026-10-20-33 의 검사"를 덧붙였다.

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
  돌려준 것을 채워 돌려주며(…), 인자로 받은 것은 바꾸지 않는다." 괄호의 예는 셀프 리뷰 둘째 회차에서 `load_line`으로
  이름을 바꿨다.
- [Minor] `morning_sources` 머리의 "부르는 바깥 명령(gh·git·tasklist)"이 `hook_report`를 거친 git까지 덮는 것처럼 읽혔다. 새
  문장: "아침 보고 수집 도구(`tools/morning_collect.py`)가 직접 부르는 바깥 명령(gh·git·tasklist)과 그 출력의 풀이. 수집 도구가
  다른 도구(`hook_report`)를 거쳐 부르는 git은 그 도구에 있다."

남긴 것과 이유:
- [Nit] 1번이 두 함수만 빼라고 했는데 `_gather_ledger`·`_by_branch`·`_agent_costs`·`_merged_kinds`·`_ticket_row`도 뺐다. 4번(읽기와
  짓기를 가른다)을 위해 `collect` 안의 읽기와 계산을 이름으로 뗀 것이고 동작은 같다.

다시 돌린 명령: 두 축의 반영은 독스트링뿐이라 ruff 둘을 손으로 쳐 초록이었고, 나머지는 첫 커밋의 pre-commit으로 갈음한다.
첫 커밋 `3c90e0a9`의 pre-commit은 모두 Passed였다(pytest 228.3초, web-verify 343.4초, 카나리아 명세와 헌법 판은 해당 파일
없음으로 Skipped). 인용 대조 경고 7건은 고쳐 없앤 옛 문장을 이 일지가 인용한 것이고, 그 가운데 줄여 적은 셋을 원문대로
고치거나 따옴표를 뗐다(다음 커밋에 든다).

## 형제 판을 기다리는 동안의 계획

연 세션이 `chore/morning-report-full-detail`을 병합했다고 알리면(병합 커밋 SHA와 함께) 이 브랜치를 그 판 위에서 다시 나눈다.
첫 커밋은 그때 대 볼 본보기다.
- 같음 하네스의 "옛 판"을 병합된 판으로 바꿔 다시 녹화하고, 다시 나눈 판을 정상 길과 gh 전부 실패 길로 견준다.
- 완료 기준의 그리기를 병합된 판으로 다시 본다. 형제 판이 보고 형식을 바꾸므로, 폴더의 `2026-10-19.md`와 같은지가 아니라 병합된
  판의 `morning_report.py`가 그린 것과 같은지를 본다(요청의 완료 기준과 어긋나는 점은 PR 본문에 적는다).
- 두 축이 남긴 시험(`json_time`, `Collected.add`·`merged_got`)을 그때 더한다.
- 다시 나눈 diff로 셀프 리뷰를 한 번 더 돌린 뒤 PR 직전 리뷰, PR, 봇 회차, 병합으로 간다.

이 절을 쓰자 회고 계기 훅이 retro를 돌리라고 했다. 이 절은 단계를 닫는 것이 아니라 병합을 기다리는 동안의 중간 계획이고 이
세션이 뒤 일을 잇는다. retro의 계기(그 스킬 설명의 "단계를 닫을 때")에 들지 않아, 병합해 단계를 닫을 때 돌린다.

## 형제 판 위에서 다시 나누기

형제 세션이 PR #326의 병합을 알렸다. 알림 원문의 앞 두 문장:

> chore/morning-report-full-detail(PR #326)이 main에 병합됐습니다. 병합 커밋은 bea74a07ad8b560a1486982a925fc151972b24ec 입니다.
> 기다리시던 그 위에서 morning_collect.py 나누기를 이어 가시면 됩니다.

같은 알림이 "claude-review가 두 회차에 걸쳐 _token_section이 길다고 짚었고, 그 일은 그쪽 세션이 나눈다고 PR 코멘트에 적어
두었습니다"라고 넘겼다. PR #326의 리뷰 코멘트 셋이 모두 이 브랜치가 나눈다는 것을 근거로 들었다. claude-review 두 회차는
그것으로 병합을 막지 않았고, 그 세션의 판정은 그 Minor를 보류했다. 받는 쪽이 이 브랜치이므로 범위에 넣었다. 첫 판에서 요청의 넷에 없는 범위로 남긴 것과 갈리는
까닭은 이 넘김이다.

합치기. 앱의 `sync_with_base_branch`로 bea74a07을 합쳤다. 그 도구는 미커밋 변경이 있으면 거절해, 일지 고침을 표지를 단 stash로
비켰다가 합친 뒤 stash 커밋에서 그 파일만 꺼내 되살리고 그 항목을 지웠다(병합 중이라 `stash apply` 대신). 충돌은
`tools/morning_collect.py`의 열일곱 구역과 `tests/tools/test_morning_collect.py`의 import 자리 네 구역이었고(같은 세 커밋으로
`git merge-tree`를 다시 돌려 표지를 셌다), `morning_report.py`는 충돌 없이 합쳐졌다. 풀던 도중 컨텍스트가 한 번 더 압축되었다.

형제 판의 동작을 새 구조로 옮긴 자리:
- 훅 절의 "들인 날" 칸. `HookScan`에 `introduced`를 더해 `_gather_hooks`가 채우고, `_hook_section`은 형제 판의 열 칸 표를 그대로
  짓는다.
- 병렬 절. `_parallel_section`이 `shares`(`cost_by_concurrency`)를 받고 형제 판의 열한 칸 표, 구간 표, 동시 세션 설명 줄을
  그대로 둔 채 부하 줄만 `load_line`(첫 판의 `_load_line`)이 짓는다.
- 조각 하나가 표를 여럿 가진다. 형제 판이 비싼 작업 조각에 작업 종류 표를, 스윕 조각에 배정과 다르게 돈 브랜치 표를, 티켓
  조각에 티켓마다의 표를 더해 `Piece.table`을 `Piece.tables`로 바꿨다.
- 형제 판의 티켓 수 줄이 끝에 배정과 다르게 돈 브랜치 수를 적는다. 그 수는 스윕 조각이 세므로 `_sweep_piece`가 (조각, 그 수)를
  돌려주고 `_ticket_piece`가 `off` 인자로 받는다.
- 장부 읽기. 형제 판이 세션마다 사람이 연 세션인지(`human`)도 읽어, `_gather_ledger`가 `LedgerScan`(호출, 인계, 사람)을
  돌려준다. 같은 꼴의 사전 둘을 튜플로 돌려주면 자리를 바꿔 넘기기 쉬워서 이름을 붙였다.
- 티켓 행의 글자 수(`chars`)를 `_ticket_row`에 옮겼다.
- 형제 판의 `command_rows`는 셸 명령과 그 밖의 도구 조각을 `merged_got`으로 합쳤다. 한 절의 조각을 합치는 자리라 `Collected`
  독스트링의 규약대로 `got.add`로 바꿨다.

`_token_section` 나누기. 140줄(bea74a07)을 요약 조각 `_summary_piece`(59줄), 시작 구성 조각 `_start_piece`(9줄), 낭비 후보 조각
`_waste_piece`(55줄)와, 그것들과 표 셋(비용 구성, 비용이 큰 세션, 브랜치)을 차례로 잇는 `_token_section`(37줄)으로 나눴다.
요약과 시작 구성이 같이 쓰는 "구성을 아는 사람이 연 세션"은 `_human_parts`다. 값은 요약, 시작 구성, 낭비 후보 조각의 차례로
더해(시작 구성 조각은 값이 없다) 옛 차례와 같다. 줄 수는 셀프 리뷰 두 축을 반영한 뒤의 판이다(명세 축 반영 전에는 57·52줄이었고,
늘어난 것은 독스트링이다). 그 밖의 크기(bea74a07 → 이 판): `collect` 136 → 97줄, `_sweep_section` 181줄 → `_sweep_piece`
88줄과 `_ticket_piece` 67줄과 `_model_section` 13줄. 줄 수는 스크래치 스크립트가 AST로 def 줄부터 끝 줄까지 센 것이다.

시험. 형제 판의 시험은 그대로 두고, 첫 판에서 남긴 셋을 더했다. `Collected.add`가 자기만 채우고 더한 조각은 그대로인지,
`merged_got`이 넘겨받은 것을 바꾸지 않는지(기존 시험에 단언 하나), JSON 풀이가 꼴이 틀린 칸을 비우는지와 `json_time`이
시간대 없는 시각을 UTC로 읽는지다.

### 둘째 회차 검사

- 같음 하네스의 옛 판을 bea74a07의 `tools/morning_collect.py`로 바꿔 2026-10-19를 다시 녹화했다(첫 회차 파일은 스크래치패드의
  `v1/`로 옮김). 옛 판의 실제 수집과 그 재생이 같았고(놓친 호출 0), `_token_section`까지 나눈 새 판의 재생도 같았다(놓친 호출
  0, 수집 JSON과 목록 155,847바이트). gh를 모두 실패시킨 길도 옛 판과 새 판이 같았다(70,927바이트). 그 길에서 녹화에 없던
  워크트리 기록 시각과 브랜치 제목 31건은 두 판 모두 실제로 불렀다.
- 그리기. 보고 폴더의 `2026-10-19.data.json`·`notes.json`을 스크래치패드로 복사해 bea74a07과 이 판의 `morning_report.py`로
  그렸다. 둘의 md와 상태 파일이 바이트 단위로 같았고, 경고는 둘 다 같은 네 줄(상세 2·4·5·7의 해석 없음)이었다. 폴더의
  `2026-10-19.md`와는 두 판 모두 diff 49줄로 달랐고, 다른 자리는 형제 판이 상세 일곱 절을 `<details>` 접기에서 `###` 머리로,
  "제안별 바꿀 것"을 굵은 글로 바꾼 곳뿐이었다. 그때 폴더의 md로는 요청의 완료 기준(폴더 md와 같음)을 형제 판이 형식을 바꿔
  어느 판도 지킬 수 없어, 형제 판과 같은지로 대신했다. 그 뒤 폴더가 새로 쓰여 글자 그대로 지켜졌다(아래 셀프 리뷰 둘째 회차의
  명세 축).
- 시험 두 파일 107 통과, ruff 둘 초록, pyright 0(바뀐 다섯 파일).

### 셀프 리뷰 둘째 회차

범위: base `bea74a07`(병합 커밋을 만들면 merge-base가 될 SHA. 병합 중이라 `git merge-base`는 아직 `0262841b`를 준다), 바뀐 파일
여섯, 커밋 하나(`3c90e0a9`)와 진행 중인 병합, 미추적 0. 명세는 요청 원문, 병합 순서의 답, 넘겨받은 `_token_section` 나누기,
bea74a07의 옛 판정 아홉을 적은 스크래치 파일이다.

표준 축(sonnet·high). Critical·Major 0. bea74a07과 지금 판의 함수를 AST로 견줘 달라진 열 함수를 읽고 형제 판과 대 봤다고
했다. 지적:
- [Minor] 새 순수 함수(`_concurrency_buckets`, `_merged_kinds`, `_load_line`, `_ticket_row`, `_by_branch`, `_agent_costs`,
  `_human_parts`, `_*_piece`)에 시험이 없다(`.claude/rules/tests.md`). 같음 하네스는 커밋하지 않았다.
- [Minor] `_token_section`이 조각의 칸을 한쪽만 잇는다(줄은 시작 구성 조각의 것만, 값은 요약과 낭비 후보 조각의 것만).
- [Minor] 사람이 연 세션 가운데 구성을 아는 세션을 거르는 식이 `start_rows`와 `_human_parts`에 따로 있다.
- [Nit] `_sweep_piece`가 (조각, 수)를 돌려준다. `Part`와 `Piece`의 이름이 가깝다. `morning_sources`의 `open_prs`·`pr_view`·
  `processes`에 독스트링이 없는데 모듈 독스트링은 함수마다의 값의 원천으로 반환형과 독스트링을 든다.
- 주장: `HookScan`의 "등록된 훅마다 들인 날"은 틀렸다(`introduced_dates`는 기록에 없는 훅을 뺀다). 이 절의 `_waste_piece`
  51줄은 52줄이다. 첫 회차 표준 축 절이 새 문장으로 인용한 "짜임" 문장은 그 뒤 명세 축 반영으로 바뀌어 지금 독스트링과 끝이
  다르다. PR #326의 claude-review 두 회차는 병합을 막지 않는다고 했고 "보류"는 그 세션의 판정 쪽 말이다.
- 잔존[Nit]: 대기열 380(열린 행)이 `tools/morning_collect.py`의 `open_prs`를 든다. `.claude/rules/tools.md`의 `gh pr` 도구 수를
  grep으로 다시 세면 이제 `morning_sources.py`가 잡힌다.
- 맞음으로 닫은 것: 충돌 수 17·4, 나머지 줄 수, 스크립트 자리의 `find_spec("tools")`, 절을 짓는 함수가 읽지 않는다는
  문장(`model_sweep.arm`, `file_key_of`, `queue_open_rows.is_file`까지 대 봤다), 시험 주석 둘.

표준 축에서 고친 것(새로 쓴 문장은 PR 직전 `bug-perf-review`에 밀 주장으로 넘긴다):
- 요청 1이 뽑으라고 한 두 함수를 공개 이름 `concurrency_buckets`·`load_line`으로 바꾸고 시험 둘을 더했다. pyright strict의
  `reportPrivateUsage`가 시험에서 `_` 이름을 가져오지 못하게 해서다. `concurrency_buckets` 시험은 평균 동시 세션 구간, 돈 세션이
  없는 분의 1, 메인 세션 호출이 없는 PR의 제외, 서브에이전트까지 센 비용을 단언한다. 같은 함수 독스트링에 새 문장: "돈 세션이
  없는 분(`stamps`에 없는 분)은 1로 센다."
- `_token_section`이 세 조각의 줄과 값을 모두 잇는다(지금은 시작 구성 조각만 줄이 있고 그 조각만 값이 없어 출력은 같다).
- `HookScan` 독스트링의 새 문장: "`introduced`는 등록된 훅의 들인 날(`hook_report.introduced_dates`. git 기록에 없는 훅은
  빠지고 표에는 모름으로 적힌다)". 커밋한 훅과 없는 훅 이름으로 `introduced_dates`를 불러 없는 훅이 빠지는 것을 봤다.
- `morning_sources`의 세 함수에 독스트링을 더했다. `open_prs`: "열린 PR(`PR_LIMIT`개까지)과 그 상태(`open_state`). gh가
  실패하거나 JSON 목록이 아니면 None이고, 번호나 연 시각을 읽지 못한 PR은 뺀다." `pr_view`: "PR 하나의 제목·본문·브랜치·연
  시각·커밋. gh가 실패하거나 JSON 객체가 아니거나 빈 객체이면 None이다." `processes`: "`claude.exe` 프로세스의 (수, 메모리 합
  MB)(`tasklist_load`). `tasklist`가 없거나 실패하면 None이다." 스크래치 탐침이 `_gh_json`을 바꿔 끼워 None·글·수·빈 객체·빈
  목록·번호나 시각이 빠진 PR을 넣고, `subprocess.run`이 `FileNotFoundError`를 내게 해 세 문장대로 나오는 것을 봤다.
- 일지: `_waste_piece`와 `_token_section`의 줄 수, 첫 회차 절의 "짜임" 인용(지금 독스트링과 같은 데까지로 줄였다), PR #326
  코멘트의 "보류"가 누구의 말인지.

표준 축에서 남긴 것과 이유:
- 시험 없는 나머지 새 함수(`_merged_kinds`, `_by_branch`, `_agent_costs`, `_ticket_row`, `_human_parts`, `_*_piece`). bea74a07에서
  `collect`·`_sweep_section`·`_token_section` 안에 있던 계산을 이름으로 뗀 것이라 그 판에도 단위 시험이 없었고, 시험하려면 공개
  이름으로 바꿔야 한다. 출력은 같음 하네스가 바이트로 잡았다.
- 거르는 식이 `start_rows`와 `_human_parts`에 따로 있다. `start_rows`는 형제 판의 공개 함수이고 그 시험이 `Start` 열을 넘겨,
  식 하나를 나누려고 시그니처와 시험을 바꾸지 않았다.
- `_sweep_piece`의 (조각, 수). 형제 판의 티켓 줄이 스윕 조각의 수를 적어, 그 줄을 바이트로 지키는 대가다.
- `Part`와 `Piece`의 이름, `processes`의 이름. 독스트링이 가르고, `processes`는 bea74a07의 이름이다.
- 대기열 380. 그 행은 일지 2026-10-20-22의 사건을 적은 기록 칸이고, 그때 `open_prs`는 `morning_collect.py`에 있었다. 제안한
  검사는 `tools/` 전체를 본다.
- `.claude/rules/tools.md`의 `gh pr` 도구 수. 그 항목이 시키는 대로 다시 세면 잡히는 파일이 `morning_collect.py`에서
  `morning_sources.py`로 바뀌고 수는 넷 그대로다. 항목은 도구 단위로 `morning_collect`의 실패 갈래를 적어 참이다(첫 회차 판단).
  `tools/`를 `gh pr`과 `"pr",`으로 grep하니 열한 파일이 잡혔고, 하위 명령을 실제로 넘기는 자리는 `hook_pr_head_sync`
  (`args = ["pr", "view"]`), `wait_ci`(`_gh("pr", "view", …)`), `tidy_checkouts`(`["gh", "pr", "list", …]`),
  `morning_sources`(`_gh_json`의 `["gh", *args]`에 `"pr"`을 넘기는 세 자리)뿐이었다. 나머지 일곱(`morning_collect` 포함)은
  독스트링·주석·출처 문자열에서 이름만 든다.

명세 축(본 세션 모델). Critical·Major 0, 빠진 것과 범위 넘침 0. 리뷰 도중 표준 축 반영이 작업 트리에 들어와 그 판으로 다시
돌렸다고 했다. 따로 짠 녹화·재생 하네스로 bea74a07 판과 이 판을 네 갈래(정상, gh 전부 실패, 훅 git 실패, `gh pr view`만
실패)에서 돌려 수집 JSON·목록과 바깥 호출의 종류·횟수가 같았고(놓친 호출 0), 옛 판정 아홉이 모두 지켜졌다(`gh pr view`
41·88·42회, gh 실패 갈래의 `git log -1` 19회가 두 판 같음, 훅 git 실패 갈래의 `gh run list` 0회). 일지의 줄 수, 충돌 표지
수(17+4), PR #326 코멘트 인용, 값의 차례는 맞다고 했다. 지적:
- [Minor] 완료 기준의 그리기. 보고 폴더가 21:00~21:05(KST)에 새로 쓰였다. 옛 data·notes·md(md 20,026바이트)는 예약 작업
  폴더의 `old/reports-2026-10-19-v2/`로 옮겨졌고 새 data·notes·md(md 32,789바이트)가 생겼다. 지금 폴더의 data·notes로는 두 판
  모두 폴더 md와 바이트까지 같아 "어느 판도 지킬 수 없어"가 이제 틀렸다. 옮겨진 v2로는 일지 서술이 모두 맞았다. 폴더를 누가
  썼는지는 확인하지 못했다고 했다.
- [Minor] `_waste_piece` 독스트링의 "그 밖의 파일은 경로를 그대로 둔다". 함수를 불러 보니 `C:\Users\User\Notes\Foo.md`는
  `C:/Users/User/Notes/Foo.md`로, 다른 저장소의 워크트리 파일 `C:\other\.claude\worktrees\zz\Bar.md`는 `c:/other/bar.md`로,
  이 저장소의 워크트리 파일은 접두가 빠져 `tools/Hook_Y.py`로 나왔다. 동작은 옛 판과 같다.
- [Nit] `_summary_piece`의 "요약 표…와 그 값"에서 값 `token:skill_chars`는 요약 표에 없다.
- [Nit] PR #326 코멘트가 섞였다고 든 읽은 파일 집계와 큰 도구 결과 순위가 아직 `_waste_piece` 한 함수에 있다. 같은 표를
  짓는 일이라 받아들일 만하다고 했다.

명세 축에서 고친 것(새로 쓴 문장은 PR 직전 `bug-perf-review`에 밀 주장으로 넘긴다):
- 그리기를 지금 폴더로 다시 쟀다. 폴더의 `2026-10-19.data.json`·`notes.json`을 스크래치패드로 복사해 bea74a07과 이 판의
  `morning_report.py`로 그리니 둘 다 폴더의 `2026-10-19.md`(32,789바이트)와 바이트까지 같았고, 상태 파일도 폴더와 같았으며
  경고는 0이었다. 폴더 파일의 수정 시각은 검사 앞뒤로 같았다. 요청의 완료 기준이 글자 그대로 지켜진다. 위 둘째 회차 검사의
  문장은 그때의 폴더 기준이라고 고쳤다.
- 폴더를 쓴 쪽. 본 세션과 명세 축 서브에이전트의 트랜스크립트에서 입력에 `scheduled-tasks`가 든 도구 호출을 모두 찍었다(스크래치
  스크립트). 폴더가 바뀐 12:00~12:05 UTC에는 그런 호출이 없었고, 앞뒤의 호출은 모두 읽기(`ls`, `diff`, `cp`의 원본)였다. 그
  사이에 돈 명령은 명세 축의 하네스(`equiv.py`, 12:05:22 UTC에 시작해 폴더 md가 쓰인 시각과 1.4초 차이)뿐인데, 그 스크립트는
  보고 폴더를 앞 날 메모의 열쇠를 읽는 데(`latest_checks`)만 쓰고 출력은 스크래치패드에 쓴다. md와 상태 파일을 쓰는 그리기는
  그 하네스에 없다. 이 세션은 "이 폴더의 파일은 덮어쓰지 말고"를 어기지 않았다. 누가 썼는지는 이 세션에서 알 수 없다.
- `_waste_piece` 독스트링의 새 문장: "파일은 세션을 건너 가르는 열쇠(`token_report.file_key_of`. 역빗금을 `/`로, 글자를
  소문자로 바꾸고 첫 워크트리 접두를 벗긴다)로 묶고, 주 체크아웃(`main_checkout`) 아래의 열쇠는 그 아래의 상대 경로로 줄인다.
  그래서 이 저장소의 워크트리 파일도 주 체크아웃의 상대 경로로 적힌다. 적는 경로는 `shown_path`가 원래 경로의 꼬리로
  대소문자를 되살린 것이고, 꼬리가 열쇠와 맞지 않으면(다른 저장소의 워크트리 파일) 소문자 열쇠 그대로다." 명세 축의 탐침(주
  체크아웃 아래, 이 저장소의 워크트리, 밖, 다른 저장소의 워크트리)으로 다시 불러 넷 모두 이 문장대로 나왔다.
- `_summary_piece` 독스트링의 새 문장: "값에는 표에 없는 시작 스킬 목록 글자 수(구성을 아는 사람이 연 세션의 중앙값,
  `token:skill_chars`)도 들고, 구하지 못한 값은 남기지 않는다(`Collected.value`)." 빈 기간으로 불러 값이 셋만 남는 것(None인
  비중 둘과 스킬 글자 수가 빠진다)과, 2026-10-19 수집 JSON에 `token:skill_chars`가 든 것을 봤다.

명세 축에서 남긴 것과 이유:
- [Nit] `_waste_piece`의 두 집계. 한 표의 행을 짓는 일이고 독스트링 뒤의 본문이 47줄이라(넣어 55줄), 더 나누면 표 하나를 두
  함수가 나눠 짓는다.

다시 돌린 명령: 시험 두 파일 109 통과, ruff 둘 초록(전체), pyright 0(바뀐 다섯 파일). ruff가 표준 축 반영으로 더한 시험의
`json_int(True)`를 참거짓 위치 인자(FBT003)로 잡아 `json_int(json.loads("true"))`로 고쳤다. 같은 값을 JSON 글에서 읽어
넘기는 것이라 시험의 뜻은 같다. 명세 축 반영 뒤의 검사는 병합 커밋의 pre-commit으로 갈음한다.
