# 2026-10-23 (11) 인용 대조가 `//` 주석을 펴고 넘겨받은 파일을 먼저 말뭉치에 넣는다

## 구현

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "대기열 436·398을 티켓 .scratch/harness/issues/008-quote-wrap-slash-comment.md로 쓰고 한다 / 다음 작업: (…) `tools/check_quotes.py`의 고침 둘. 감긴 원문을 풀 때 다음 줄 머리의 `//` 주석 기호도 벗기고(436), 넘겨받은 파일을 모두 말뭉치에 넣은 뒤 대조한다(398) / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 6 중 6. (…) / 브랜치: chore/008-quote-wrap-slash-comment / 모델: Opus 5.5 / medium. 레벨 스윕의 갈래 / (…) / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. 묶음의 여섯째 세션이라 `tidy-checkouts`는 돌지 않았다.
- `EnterWorktree(008-quote-wrap-slash-comment)` 뒤 `git branch -m chore/008-quote-wrap-slash-comment`. 기점은 origin/main `975bf04c`(#355)다.
- 티켓 번호는 지시문이 준 008을 썼다. 티켓 파일을 쓰기 전 `tools/sibling_overlap.py`는 다음 빈 번호를 005로 냈고(형제 003~007이 아직 티켓 파일을 쓰지 않았다), 쓴 뒤 다시 치니 `이 브랜치의 새 번호: 티켓 008`, 번호 겹침 없음이었다.
- 일지 번호는 처음에 06으로 만들었다가 형제 007과 번갈아 겹쳐(`--move`가 07, 08로 옮기는 사이 그쪽도 같은 번호로 옮겼다) 머리 한 줄 파일을 지우고, 셀프 리뷰 직전에 다시 받은 11로 만들었다. 만든 뒤 다시 친 도구가 `이 브랜치의 새 번호: 일지 2026-10-23-11`, 다음 빈 번호 12를 냈다.

### 고친 것

- `_WRAP`: 다음 줄 머리의 주석 표지로 `#` 말고 `//`(여럿 이어진 것 포함)도 벗긴다(436).
- `check`: 넘겨받은 파일을 먼저 모두 읽어 말뭉치에 넣고, 그 뒤 차례로 대조한다(398). 셈(`files_read` 등)과 뺀 사본·읽지 못한 파일의 처리는 그대로다.
- 모듈 독스트링: 감긴 줄의 주석 머리에 `//`를, 대조 전에 모두 넣는다는 문장을, 못 보는 것에 주석이 아니었던 줄 머리 `//`를 더했다. 그 못 보는 것은 못 보는 것 시험에 고정했다.
- 변이 표: 345의 변이 둘이 옛 `_WRAP` 문자열을 `old`로 들어 새 문자열로 고쳤고, 436·398을 하나씩 빼는 변이 둘을 더했다. 프로브 README 행에 결과를 적었다.
- 대기열 398·436 행을 이 티켓으로 닫았다.

### 빨강과 초록

- 고치기 전: 새 시험 셋(`//` 하나, 미추적 두 파일의 두 차례)이 모두 빨강이었다(`3 failed, 54 deselected`).
- 고친 뒤: `uv run pytest -q tests/tools/test_check_quotes.py` 57 passed.
- 변이: `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/quote_check_mutations.toml 18 19 20 21` → 넷 모두 기대대로 빨강(기준선 초록 57 passed).

## 셀프 리뷰 (`/code-review`)

기준 `975bf04c`, 바뀐 파일 다섯과 미추적 둘(티켓, 이 일지), 커밋 없음.

### 표준 축 (sonnet, high)

Critical·Major 없음, Minor 1, Nit 3. 잰 것: 시험 57 통과, `mutate.py --check` 변이 21 원문 있음, README의 번호 18·19·20·21과 수(열다섯, 넷, 둘)가 toml 차례와 맞음, `unwrap`을 `a\n// b`·`a\n/// b`·`a\n//b`·`a\n  //   b`·줄 머리가 아닌 `https://`로 불러 서술과 맞음, `check`의 셈이 둘째 루프에만 있음, 대기열 닫힘 문장의 수가 diff와 맞음, 살아 있는 문서에 옛 말 잔존 없음.

- Minor: 변이 결과("넷 모두 기대대로 빨강")를 리뷰가 다시 돌리지 못했다(코드를 바꾸는 도구라).
- Nit 1: 대기열 두 행의 닫힘 앞 `ADR 불필요.`의 마침표가 다수 서식과 다르다.
- Nit 2: 변이의 `expect_output`이 시험 이름이다(345의 선례와 같고, 고른 시험의 단언이 하나라 실해 없음).
- Nit 3(판단): `check`의 `readable` 3-튜플이 Data Clumps 냄새다.

### 반영

- Minor: 이 세션이 위 "빨강과 초록"에서 이미 18~21을 돌려 넷 모두 빨강을 봤다. 갈음한다.
- Nit 1: 고쳤다. 저장소의 `ADR 불필요 **닫힘`이 164, `ADR 불필요. **닫힘`이 34라 다수 쪽으로 맞췄다.
- Nit 2: 남긴다. 345의 선례이고 그 시험들은 단언이 하나씩이다.
- Nit 3: 남긴다. 한 함수 안에서만 쓰는 지역 값이고, 이름 붙은 형식을 더하면 고침 둘의 범위보다 커진다.

### 명세 축 (상속 모델)

Critical·Major 없음, 범위 넘침 없음, Nit 1. 잰 것: 고치기 전 `check_quotes.py`(975bf04c)를 스크래치 사본으로 꺼내 새 시험을 돌려 398 시험 두 차례가 서로 다른 쪽(`adr.md:1`, `journal.md:2`)을 경고하며 빨갛고, 436 시험과 못 보는 것의 `//` 단언도 빨갛다. 실제 사건 파일 `.scratch/design-reverse-sync/probes/tools_import.mjs`의 `//` 감긴 문장 넷을 한 줄로 옮겨 `_found_elsewhere`로 부르니 옛 판은 넷 모두 False, 새 판은 넷 모두 True였고, 빈 `//` 줄을 넘는 문단 잇기는 두 판 모두 False였다. 변이 20·21을 사본에 넣어 기대한 시험이 빨간 것을 봤다(18·19는 `old`가 한 번 맞는 것만 봤다).

- Nit: 못 보는 것의 괄호 "(제목과 앞 줄이 이어져 원문으로 센다)"가 `//` 줄을 빠뜨리고, 같은 문장에 `//`가 겹친다.

### 반영 (명세 축)

- Nit: 고쳤다. "마크다운 제목이나 주석이 아닌 글의 일부였던 것(그 줄과 앞 줄이 이어져 원문으로 센다)".

## 검사

- `uv run python tools/run_checks.py`(셀프 리뷰 반영 전, 백그라운드): 종료 0. check-ticket, lint-imports, check-instructions, zizmor, check-type-escapes, pyright, pyright-linux, run-hooks, web-verify(413.0s), pytest(491.2s) 모두 Passed.
- `uv run ruff check .`, `uv run ruff format --check .`: 0.
- 반영으로 바뀐 것은 대기열 두 행의 마침표와 독스트링 한 문장뿐이라, 커밋 직전의 다섯은 그 커밋의 pre-commit으로 갈음한다.
