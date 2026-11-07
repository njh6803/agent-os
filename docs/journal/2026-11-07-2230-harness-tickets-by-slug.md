# 하네스 티켓을 번호 없이 slug로 쓰게 한다 (retro-queue-per-item 07)

세션 제목: `feature/07-harness-tickets-by-slug` (인계하며 `feature/07-harness-tickets-by-slug (인계함)`으로 바꾼다). 브랜치 `feature/07-harness-tickets-by-slug`, 워크트리 `C:\project\agent\.claude\worktrees\07-harness-tickets-by-slug`. 모델 Sonnet 5.5 / high.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 인자: .scratch/retro-queue-per-item/issues/07-harness-tickets-by-slug.md

지시문의 이번 요청 범위는 PR과 병합까지다. 이어받을 상태는 없었다. 이 티켓은 기능 `retro-queue-per-item`의 마지막 티켓이다.

## 한 것

- **커밋 검사.** `tools/check_ticket.py`가 `chore/` 뒤의 글자를 그대로 stem으로 본다. 티켓 파일의 이름 모양은 `[a-z][a-z0-9-]*`이거나 옛 꼴 `NNN-<slug>`다. 막는 글은 번호 명령 대신 "번호 없이 영어 소문자로 시작하는 이름을 직접 짓는다"를 든다.
- **저장소 상태 시험.** `tests/test_harness_ticket_names.py`가 `LAST_NUMBER = 45`를 고정하고, 그보다 큰 번호로 시작하는 티켓과 같은 번호의 옛 티켓 둘을 잡는다. 상수가 실제 최대 번호와 같은지도 본다. main을 다시 합치면 이 값으로 옮긴다.
- **번호 대조 도구.** 서브에이전트(`tools-side-07`)가 `tools/sibling_overlap.py`에서 티켓 몫(다음 빈 티켓, 티켓 겹침과 누가 옮기나, 티켓 파일 이름과 브랜치 옮기기, 원격·PR 다시 열기)을 걷었다. 변이 표는 174에서 133이 됐다. `tools/morning_collect.py`는 `chore/<이름>`과 `.scratch/harness/issues/` 경로를 받고, `tools/hook_prompt_directive.py`의 `TICKET_NOTICE`는 이름을 직접 짓게 안내한다.
- **스킬·문서.** next-session(`directive.md`, `SKILL.md`), `code-review`, `retro`, `implement`, `sync-design-system/upload.md`, `docs/agents/issue-tracker.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `CLAUDE.md`, `docs/constitution/operations.md`(브랜치와 병합 절), `KICKOFF.md`를 새 이름 규칙으로 고쳤다. 헌법 판은 3.0.70에서 3.0.71이다.
- **ADR 0045 이력.** `### 2026-11-07 하네스 티켓 이름 티켓이 도구와 문서에서 정한 세부`를 더했고 `tools/check_adr_pointers.py`가 통과했다. 본문 포인터는 달지 않았다(옛 티켓 수 44는 결정 시점의 셈이라 이력 안에서 짚었다).
- **카나리아.** 명세 여섯(`implement_ticket_status`, `next_session_chore_tickets`, `next_session_label_ticket_notice`, `code_review_branch_ticket`, `retro_ticket_reflection`, 새로 만든 `sync_design_system_chore_branch`)을 새 `claude -p` 세션으로 돌렸다. 모두 통과 4, "없음" 섞임 0이었다. `code_review_branch_ticket`은 첫 실행에서 실험군 한 회차가 스킬을 불러 놓고 "없음"이라 답해 통과 3·실패 1이었고, 같은 명세를 다시 돌리자 통과 4였다. 그 사정과 결과는 각 명세 머리 주석의 "최신 결과"에 적었다. `--shape`는 여섯 모두 통과했다.
- **변이 표.** `check_ticket_mutations.toml`(27개), `prompt_directive_mutations.toml`(10개), `sibling_overlap_mutations.toml`(133개)의 `--check`가 모두 통과했다. 서브에이전트가 번호로 고른 24개와 내가 돌린 티켓 이름 시험 셋(131~133)이 기대대로 빨강이었다. 나머지는 돌리지 않았다.
- **티켓.** `Status:`를 `done`으로 바꾸고 체크박스를 모두 표시했다. 기능 계획(`.scratch/retro-queue-per-item/plan.md`)이 없고 하네스 기능은 `**슬라이스:**` 줄이 없어 `**끝:**` 줄은 적지 않는다. `uv run python tools/plan_table.py`는 변경 없이 끝났다.

## 검증

근거의 종류. 아래 명령의 결과와 위 카나리아·변이 `--check`·티켓 이름 시험 셋의 결과는 이 세션에서 그 명령을 직접 돌려 출력에서 읽은 것이다(카나리아는 `tools/canary.py`의 집계 줄, 변이는 `tools/mutate.py`의 출력). 서브에이전트가 번호로 골라 돌렸다는 변이 24개(처음 보고는 25개라 했으나 나열한 번호를 세면 24개다)와 그 결과는 서브에이전트의 최종 보고에서 옮긴 것이고 이 세션이 다시 돌리지 않았다(대신 변이 표 `--check`와 관련 시험 348개를 이 세션이 돌렸다). 위 "한 것"의 `tidy-checkouts`가 지우지 못한 휴지통 항목 서술은 이 세션 앞부분의 요약에서 옮긴 것이라 다시 보지 않았다.

- `uv run ruff check .`, `uv run ruff format --check .` 통과.
- `uv run python tools/run_checks.py`는 종료 코드 0이다(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest, web-verify 모두 통과).
- `uv run python tools/sibling_overlap.py`: origin/main `cd29fa1`, 번호 겹침 없음, 헌법 새 판 3.0.71.

## 셀프 리뷰 (이어받은 세션)

범위: base `cd29fa1e`, 33개 파일의 미커밋 변경과 미추적 2개, 커밋 0개. 표준 축과 명세 축 서브에이전트가 읽은 보고에서 옮겼다.

- **고친 것.** `.scratch/retro-queue/README.md` 27행의 `<NNN>-<slug>` 잔존을 `<slug>`로 고쳤다. `check_ticket.ticket_stem`이 `chore/` 뒤 이름에 `_HARNESS_STEM`을 걸어 `chore/Foo`·`chore/09-x`·`chore/a_b`를 티켓 모양이 아닌 브랜치로 본다(시험 사례 셋을 더했고 `check_ticket_mutations.toml` 18번의 원문을 새 코드에 맞췄다). `tools/mutate.py`로 18번을 직접 돌려 기대대로 빨강이었다. 막는 글에 허용 글자(소문자·숫자·하이픈)를 더했고 ADR 0045 이력, `docs/agents/issue-tracker.md` 15행, `check_ticket.py` 독스트링의 "그대로 stem" 서술을 같은 규칙으로 맞췄다. `sibling_overlap_mutations.toml`과 이 일지의 "25개"를 나열한 번호를 세어 24개로(나머지는 106개), 근거 종류를 서브에이전트 보고에서 옮긴 것이라 밝혔다. `next-session/SKILL.md` 58행의 "다음 번호의 새 harness 티켓"을 "새 이름의 새 harness 티켓"으로 고쳤다. `next-session/directive.md`의 이름 겹침 확인에 `git ls-tree --name-only origin/main`을 더하고, 나란히 도는 워크트리·열린 PR의 이름은 못 본다는 것과 겹치면 병합 때 충돌로 받는 세션이 바꾼다는 것을 적었다.
- **커밋 훅이 더 막은 것.** 첫 커밋 시도에서 mutation tables 검사가 `sibling_overlap_mutations.toml`의 변이 여섯(4·26·56·57·58·90)을 막았다. 이 PR이 `tools/sibling_overlap.py`를 고쳐 그 파일을 겨누는 변이가 새 규칙(고른 단언만 찍는 표지, 대기열 350·517)으로 다시 검사된 것이다. 변이마다 원문을 임시로 넣어 실패 출력을 본 뒤(스크래치 스크립트가 파일을 되돌렸고 `git status`로 확인했다) `expect_output`을 달았고, 여섯을 `uv run python tools/mutate.py <표> 4 26 56 57 58 90`으로 돌려 모두 기대대로 빨강이었다.
- **남긴 것.** `morning_collect.TICKET_BRANCH`의 `[\w.-]+`가 `check_ticket`보다 넓다(`chore/Foo`·`001-`을 티켓 행으로 맞춘다). 아침 보고는 보여 주기만 하고 게이트가 아니며, `test_morning_collect.py`가 `001-` 행을 고정해 둔 것이라 이 티켓에서 좁히지 않는다. `gather_tickets`의 하네스 폴더 가드는 실제로 닿지 않는 길이지만 동작에 해가 없다. `.scratch/harness/probes/README.md` 102행의 지운 변이 족 서술은 기록 표라 둔다. `TICKET_BRANCH`의 `$`가 개행 하나를 받는 것은 브랜치 이름에 개행이 못 든다. 변이 표 `check_ticket`·`prompt_directive` 새 변이는 `--check`(원문 확인)만 했고 전체 실행은 하지 않았다(`check_ticket_mutations` 18번만 직접 돌렸다).
- **다시 돌린 것.** `uv run ruff check . && uv run ruff format --check .` 통과, `uv run python tools/run_checks.py` 종료 코드 0, `tests/tools/test_check_ticket.py`·`test_morning_collect.py` 186건 통과(이 세션이 돌렸다), `uv run python tools/sibling_overlap.py` 번호 겹침 없음(origin/main `cd29fa1`).

## PR 직전 리뷰 (인계받은 세션)

CodeRabbit CLI는 `coderabbit auth status`가 `Seat: not assigned`(Plan Free)라 돌지 못했다. 대체 둘을 돌렸다(둘 다 base `cd29fa1e`, 커밋 둘).

- **`/security-review`.** 보고할 취약점 0건. 도구 변경은 정규식을 조이고 번호 처리 코드를 걷어낸 것이고, 새 `subprocess`·셸·파일 이름 변환이 없다.
- **`bug-perf-review` 서브에이전트.** Critical·Major 없음. Minor 둘을 판정했고 둘 다 이 PR에서 고치지 않는다.
  1. `tools/morning_collect.py:237`의 `TICKET_BRANCH` harness 갈래가 `check_ticket._HARNESS_STEM`보다 넓다. 위 "셀프 리뷰"의 "남긴 것"과 같은 지적이다. 아침 보고가 `chore/Foo` 같은 티켓 없는 브랜치를 "찾지 못한 PR" 줄에 올릴 뿐 값은 틀리지 않고, `test_morning_collect.py`가 `001-` 행을 고정하고 있어 이 티켓에서 좁히지 않는다.
  2. `_HARNESS_STEM`과 `tests/test_harness_ticket_names.py`의 `\d{3}`이 유니코드 숫자(`١٢٣`)를 받아 옛 `isascii()` 검사보다 넓다. 같은 이름의 파일을 일부러 싣는 사람만 닿고 막는 쪽(`check_ticket`)이 아니라 이름 규칙 쪽이 느슨해지는 것이라 해가 없다. 고치려면 정규식 세 곳(`check_ticket.py`, 시험, `sibling_overlap_mutations.toml`과 `check_ticket_mutations.toml`의 원문)을 함께 바꿔야 한다. 둘째 이후 회차에 Minor라 뒤로 넘긴다.
- 근거의 종류. 두 보고의 내용은 서브에이전트의 최종 보고에서 옮긴 것이다(보안 보고는 이 세션이 `tool-results`의 diff에서 `subprocess`·셸 호출을 Grep으로 찾아 새로 더해진 것이 시험 코드의 `_git` 호출뿐임을 본 뒤 코드를 읽어 쓴 판정이고, 다시 도구로 재현하지 않았다). `bug-perf-review`가 정규식에 입력을 넣어 불러 봤다는 사례와 그 시험 통과는 그 서브에이전트가 돌린 것이며 이 세션이 다시 돌리지 않았다. 둘째 지적의 정규식 위치 네 곳(`check_ticket.py:207`, `tests/test_harness_ticket_names.py:28`, 변이 표 두 곳)은 이 세션이 `\d{3}`을 Grep으로 찾아 확인했다.
- 위 둘은 병합 뒤 `chore/` 후속 티켓의 후보다(이름 규칙을 `morning_collect`와 `check_ticket`이 한 상수로 나누게 하면서 `[0-9]{3}`도 같이).

## 남은 일

1. (끝) 셀프 리뷰를 마쳤고 Critical·Major를 고쳤다(위 "셀프 리뷰").
2. (끝) 커밋했다. `9177b7c6`, 제목 꼬리 `(retro-queue-per-item 07)`. pre-commit(ruff, 러너 전체, 변이 표 검사 등)이 통과했다. 첫 시도는 변이 표 검사가 막았고 위 "커밋 훅이 더 막은 것"대로 고쳐 다시 커밋했다.
3. 푸시하고 PR을 열고 병합한다. 사용자가 `/git-pr`를 부르지 않았어도 이 요청의 범위가 "PR과 병합까지"다. PR 본문은 아래 "PR 본문에 적을 것"에 이 줄들을 더해 쓴다(변이 24개, 변이 표 훅이 더 막은 여섯 건의 고침, `chore/<이름>` 이름 규칙을 `ticket_stem`에 건 것, `morning_collect` 규칙이 `check_ticket`보다 넓은 것). 이 일지의 수정은 커밋하지 않았으니 새 세션이 커밋에 싣는다.
4. 병합 규약: 병합은 이 워크트리 사본의 next-session `merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 병합은 승인 없이 진행한다.

## 인계

세션 제목을 `feature/07-harness-tickets-by-slug (인계함)`으로 바꿨고(바꾸기 전 제목은 `feature/07-harness-tickets-by-slug`), 워크트리 잠금을 풀었다. 경계는 `셀프 리뷰 직전`이다.
open-session을 부른다 2026-11-07T13:31Z

두 번째 인계. 이 세션(셀프 리뷰 직전에 이어받았다)이 셀프 리뷰·반영·커밋(`9177b7c6`)을 마치고 컨텍스트 문턱을 넘어 경계 `커밋 뒤`에서 넘긴다. 받은 요청 범위는 "PR과 병합까지"라 경계에서 끝나지 않고, 이어받을 상태가 `인계: 셀프 리뷰 직전`이었으므로 같은 경계가 아니다. 세션 제목을 `feature/07-harness-tickets-by-slug (인계함)`으로 바꾼다(바꾸기 전 제목은 `feature/07-harness-tickets-by-slug`). 사용자 프롬프트는 위 "사용자 프롬프트"와 같다. 워크트리 잠금은 이미 풀려 있었다(`git worktree unlock`이 `is not locked`).
open-session을 부른다 2026-11-07T14:21Z

## PR 본문에 적을 것

- 명세 "바뀌는 자리" 목록 밖에서 찾은 자리: `.claude/skills/sync-design-system/upload.md`, `.scratch/harness/probes/canary/`의 새 명세, `tools/morning_collect.py`와 `tests/tools/test_morning_collect.py`, `tools/hook_payloads.toml`, `.scratch/ticket-for-every-pr/probes/`의 변이 표 둘.
- `tools/hook_journal_retro.py:35`의 옛 판 설명은 과거 기록이라 그대로 뒀다.
- `tidy-checkouts`가 `05-default-model-required-and-checked`의 휴지통 항목 하나를 지우지 못했다(이 세션 시작 때 본 것).
- `sibling_overlap_mutations.toml`은 133개 가운데 24개와 티켓 이름 시험 3개만 돌렸다. 나머지 106개는 `--check`로 원문만 봤다.
- `prompt_directive_mutations.toml` 9번은 `docs/agents/issue-tracker.md` 12행의 문구에 기댄다.

## 병합 세션이 한 일 (PR 489)

- PR 489를 열었다(제목 꼬리 `(retro-queue-per-item 07)`). CodeRabbit 로컬 CLI는 좌석이 없어 돌지 못했고, PR의 CodeRabbit은 무료 한도(`Review limit reached`)로 리뷰가 없었다. 그래서 CodeRabbit 회차는 세지 않는다. claude-review가 첫 회차(헤드 `ad3e6e5d`)에 Critical·Major 없이 Minor 둘과 Nit 하나를 냈다. 근거의 종류: `gh api`로 PR 코멘트를 읽은 것이고 `tools/wait_ci.py 489`의 출력(검사 모두 통과)도 이 세션이 돌렸다.
- **Minor 1, 규칙 세 곳(`check_ticket._HARNESS_STEM`, `test_harness_ticket_names._TICKET_NAME`, `morning_collect.TICKET_BRANCH`)이 따로 있다.** 이 PR에서 고치지 않는다. 앞서 "남긴 것"으로 적은 지적과 같고, 셋을 맞대는 시험이나 한 상수로 모으는 일은 도구 사이 import 규약(`.claude/rules/tools.md`)을 먼저 정해야 해서 이 티켓의 체크박스 밖이다.
- **Minor 2, 옛 꼴의 꼬리 `.+`가 제한 없어 `chore/001-[x]`가 티켓 stem으로 맞고 `tickets_on_disk`의 glob 패턴이 된다.** 이 PR에서 고치지 않는다. 판정은 `points_at`의 정확 비교라 바뀌지 않고 영향은 막는 글의 알림이 엉뚱한 파일을 가리키는 정도다. 꼬리를 `[a-z0-9-]+`로 좁히는 고침은 정규식 세 곳과 변이 표 원문 둘을 함께 바꾸므로 위 `[0-9]{3}`과 한 티켓에 묶는다.
- **Nit, 전환기가 끝나면 `LAST_NUMBER`와 `_HARNESS_STEM`의 옛 꼴 갈래를 걷는 후속이 필요하다.** 이 PR에서 고치지 않는다. 옛 티켓 번호가 더 늘 수 없을 때(옛 지시문을 든 세션이 모두 끝났을 때)의 일이다.

## 회고

후보 셋을 냈다. 승인 0, 기각 3, 넘김 0이다. 만료할 항목은 없었다(`git fetch origin` 뒤 `uv run python tools/queue_open_rows.py --ref origin/main`의 출력, 열린 항목 115개).

- **기각: 변이 표 검사가 첫 커밋을 막았다.** 사건은 실제로 났다(`sibling_overlap_mutations.toml`의 변이 여섯이 새 표지 규칙에 걸렸다). 막는 훅이 그 자리에서 막았고 고친 뒤 통과했으니 이미 있는 검사가 제 몫을 한 것이다.
- **기각: 카나리아 `code_review_branch_ticket` 첫 실행이 통과 3·실패 1이었다.** 같은 명세를 다시 돌려 통과 4였고 명세 머리 주석에 사정을 적었다. 사례 하나를 고친 것이고 종류를 세는 항목은 새로 서지 않는다.
- **기각: 도구 호출 사이 문장이 한국어가 아니라는 훅 알림과 워크트리 가드의 복합 명령 거부.** 훅과 앱 가드가 그 자리에서 알리거나 막았다(`CLAUDE.md` 환경 함정에 적힌 모양이다).
- **회차에서 뺀 것: claude-review의 Minor·Nit 셋.** 리뷰가 제 몫을 한 것이다. 셋은 코드의 후속 일(규칙을 한곳으로 모으기, 꼬리 좁히기, 전환기 걷기)이라 환경 개선 후보가 아니고, 아래 "다음"의 후속 티켓으로 둔다.

## 다음

- 이 일지의 PR 489는 봇 첫 회차를 지났다(claude-review Minor·Nit만, CodeRabbit은 무료 한도). 이 회고를 푸시한 뒤 `merge.md`의 "워크트리에서 병합할 때"대로 병합한다. 이 푸시로 도는 claude-review는 둘째 회차라 Critical·Major만 고친다.
- 이 기능(`retro-queue-per-item`)의 마지막 티켓이었다. 병합 뒤 `next-session` 결정표의 "그 기능의 마지막 티켓이었고 대기열에 회차 5 이상" 줄이 맞아 하네스 chore 배치로 간다(`queue_open_rows.py --ref origin/main`: 420 430 431 565 558 578 579 214 475 498 499 535).
- 뒤로 넘긴 일: (1) harness 티켓 stem 규칙이 세 곳에 따로 있고 `morning_collect`가 넓다. 셋을 맞대는 시험이나 한 상수로 모은다. (2) 그 규칙의 `\d{3}`을 `[0-9]{3}`으로, 옛 꼴 꼬리 `.+`를 `[a-z0-9-]+`로 좁힌다(변이 표 원문 둘도 함께). (1)과 (2)는 한 harness 티켓(예: `harness-ticket-stem-one-rule`)으로 묶는다. (3) 전환기가 끝나면 `LAST_NUMBER`와 옛 꼴 갈래를 걷는다. (4) `tidy-checkouts`가 `05-default-model-required-and-checked`의 휴지통 항목 하나를 지우지 못하고 있다.
