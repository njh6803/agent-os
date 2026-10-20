# 2026-10-20-07 하네스가 더해지기만 하는 길을 막는다 (ADR 0036)

브랜치 `chore/hook-census`, 워크트리 `.claude/worktrees/hook-census`. 이 세션의 제목은 "하네스 작업 진행"이었고, 셀프 리뷰 직전에 인계 계기가 와서 `chore/hook-census (인계함)`으로 바꾸고 넘긴다. 커밋은 아직 없다. 새 세션이 이 파일을 이어 쓰고 커밋한다.

## 사용자 프롬프트 원문

> 사용자: 계속 하네스 작업만 하는것 같은데 도대체 언제 끝나??

> 사용자: 교정루프(피드백) 등을 어떻게 하는지 조사해봐

> 사용자: 클로드나 빅테크들은 어떻게 해?

> 사용자: 다시 한 번 더 조사해서 사실인지 확인해줘

> 사용자: 나머지는 필요없어?

> 사용자: 고친결론 1,2 번은 진행하고, 나머지는 더 보완하거나 수정해야할 껀 없어?

> 사용자: 1번으로하는데 하네스 비율은 빼자

선택지 1은 측정·철거, 모델 교체 뒤 재검토, 제품 먼저, 승인 문턱, 대기열 만료를 한 ADR에 담는 안이었다. 하네스 PR 비율의 상한은 사용자가 뺐다.

> 사용자: 근데 대기열 306(전체 스위트의 부하 아래에서 흔들리는 시간 시험을 사례마다 원인을 갈라 고치는 열린 행) 같은건 기준이 좀 달라야 하는거 아니야?

> 사용자: 2주 동안 다시 일어나지 않으면 만료 기준도 달라야하는거 아니야?
> 막는 훅은 그렇다치고 저런 부하같은건 아주 가끔 걸리는 것일 수도 있잖아

> 사용자: 이 세션"하네스 작업 진행"의 모든 작업이 끝날 때 까지 현재 열린 세션들에게 현재 작업중인 것 까지만 마무리하고 다음 작업은 이어하지 않도록 지시하고 통제할 수 있어?
> 이 세션"하네스 작업 진행"의 모든 작업이 끝나면 재개할 수 있도록 해줘.

> 사용자: 끝났어?

(조작 지시인 "다시 시도" 둘과 중단 한 번은 뺐다.)

이어받은 세션(2026-10-20)의 시작 프롬프트는 앞 세션의 첫 프롬프트와 같다("계속 하네스 작업만 하는것 같은데 도대체 언제 끝나??"). 셀프 리뷰를 반영한 뒤 ADR 0036을 풀어 보이고 선택 화면으로 물었다.

> 사용자(선택 화면): 승인 (Recommended) — "이대로 커밋하고 PR을 열어 병합합니다. 병합 뒤 다음 작업은 제품 기능(end-user-continuation 티켓 01)이고, 멈춰 둔 세션들에 재개 메시지를 보냅니다."

설명의 "티켓 01"은 틀렸다. 답을 받은 뒤 대 보니 01은 이미 `done`이고, 01이 막던 02~06이 `ready-for-agent`다(origin/main의 02도 같다). ADR의 결정과는 무관한 덧붙임이라 승인은 그대로 두고 보고에서 바로잡았다.

## 결정

결정과 근거는 ADR 0036(`docs/adr/0036-harness-grows-on-third-occurrence-and-queue-rows-expire.md`)이 원천이다. 셀프 리뷰를 반영한 판을 2026-10-20에 사용자가 승인했다(위 선택 화면). 요지만 적는다. 셀프 리뷰가 더한 것(회차 3 이상은 만료하지 않는다, 만료가 이어질 때 가장 큰 회차에 하나를 더한다, 받아들여 닫은 행은 잇지 않는다, 계기 훅은 지침과 함께 간다)은 아래 셀프 리뷰 절이다.

- 제품 먼저: chore 배치는 기능의 마지막 티켓 뒤에만 연다. 같은 대상 파일 셋 이상은 계기가 아니라 묶음이다. 하네스 chore PR 뒤에는 프론티어로 간다.
- 더하는 문턱: 새 훅·검사·지침 문장·`CODING_STANDARDS.md` 줄은 같은 실수의 세 번째이거나 손상 한 번일 때 더한다. 고침은 사건 하나로 한다. 막는 훅의 첫 사건 예외를 손상으로 좁혔다.
- 쓰이는지 센다: `tools/hook_report.py`. retro가 새 훅·검사 전에 돌려 뺄 후보를 넘긴다.
- 모델이 바뀌면 다시 본다: `docs/model-selection.md` 4절 순서 8.
- 행의 종류: 같은 실수의 반복, 끝이 열린 결함 종류(306), 사람 몫(238). 사용자의 306 질문에 대한 답이다.
- 만료: 14일. 만료한 행의 실수가 다시 나면 회차를 이어 센다. 사용자의 "아주 가끔 걸리는 것" 질문에 대한 답이다.
- 처음 적용: 만료 13행과 날짜를 git에서 찾은 3행(4·13·16)을 닫고, 306을 받아들여 닫았다(`.scratch/retro-queue.md`). 열린 행이 94개에서 77개가 됐다.

## 한 것

- `tools/hook_report.py`와 `tests/tools/test_hook_report.py`(시험 31개), 변이 표 `.scratch/harness/probes/hook_report_mutations.toml`(열아홉).
- `tools/queue_open_rows.py`에 사람 몫·만료할 행·날짜를 찾지 못한 행·`--today`를 더했고, 시험을 37개로 늘렸고, 변이 열하나를 표에 더했다(서른넷).
- retro 4·5단계, next-session 결정표 세 줄, `CLAUDE.md` 교정 루프 셋째 줄, `.claude/rules/tools.md` 막는 훅 예외, `docs/model-selection.md` 4절, `KICKOFF.md`, `kickoff/claude-md-template.md`.
- ADR 0036 초안과 색인 행, ADR 0035의 두 문장에 `(바뀜: ADR 0036)` 포인터.
- 카나리아 명세 넷(`next_session_product_first`, `retro_threshold_and_expiry`, `claude_md_addition_threshold`, `tools_rule_damage_exception`)을 새로 쓰고, `next_session_number_body_batch`의 셋째 물음을 걷었다(그 조건이 계기에서 빠졌다). 프로브 README의 두 행.
- 새 파일은 리뷰가 diff로 보도록 `git add -N`(intent-to-add)으로 표시해 두었다.
- 위와 아래 검사 절의 시험·변이 수는 셀프 리뷰 전의 것이다. 반영 뒤의 수(시험 71개, 변이 서른일곱·스물)는 셀프 리뷰 절의 다시 돌린 명령에 있다.

## 번복하거나 고친 것

- 원칙 II를 어겼다. `hook_report.py`의 첫 판은 빨간 시험을 보기 전에 구현했다. 그 뒤 `queue_open_rows.py`는 빨강 11개를 먼저 봤다.
- `hook_report.py`의 `_is_notice`에서 쓰이지 않던 디코딩 갈래를 지웠다(래퍼가 처음부터 한글을 이스케이프하지 않았다, git log).
- 들인 날을 처음 더한 날에서 마지막으로 더한 날로 바꿨다(지웠다가 다시 들인 훅).
- 변이를 짓다가 시험이 비어 있던 자리 넷(UTC 변환, 가장 긴 조각, 등록 안 됨, 다시 들인 훅)과 대기열 도구의 둘(만료 경계를 줄의 앞부분만 견줌, 없는 날짜)을 찾아 시험을 더하거나 고쳤다.
- next-session 카나리아의 질문을 세 번 고쳤다(낱말 혼동, 카나리아가 질문 범위 밖, 줄을 모호하게 짚음). retro 카나리아는 사전 확인이 git 상태에 보이는 카나리아를 막아 바꿨다. 경위는 각 명세의 `# 최신 결과:` 줄.
- ruff `DTZ011`(`date.today()`)을 `datetime.now().astimezone().date()`로 고쳤다(선례 `tools/sibling_overlap.py`).

## 검사

- `tests/tools/test_queue_open_rows.py` 37개 통과(272.85초, 이 PC에 파이썬 프로세스 63개가 돌던 때). `tests/tools/test_hook_report.py` 31개 통과(앞 세션).
- 변이: `hook_report_mutations.toml` 열아홉 모두 기대대로, `queue_open_rows_mutations.toml`의 24~34 열하나 모두 기대대로, `--check`로 서른넷의 원문 확인.
- 카나리아 넷 모두 통과 4(2026-10-20, claude 2.1.302).
- `uv run ruff check .`는 고친 뒤 통과, `uv run ruff format --check .` 통과.
- `uv run python tools/run_checks.py`는 인계로 멈춰 끝나지 않았다. pyright는 마지막 변경(`datetime`) 뒤 돌리지 않았다.
- `tools/canary.py --preflight`를 모든 명세에 돌리니 원천에 카나리아가 없는 것은 `tidy_skill_cwd_owner.toml` 하나였다. 이 브랜치가 건드리지 않은 `tidy-checkouts` 스킬이다.

## 세션 통제

사용자의 요청대로 열린 세션에 지시를 보냈다. 요지는 지금 하던 일까지만 마무리하고 다음 작업으로 넘어가지 말 것, 인계하면 이 지시를 새 지시문에 옮겨 적을 것, chore/hook-census 세션이 끝나면 재개 메시지를 보낸다는 것이다. 처음 보낸 대상은 앞 세션의 요약에 있고, 2026-10-19 22:55Z쯤 인계로 새로 생긴 여섯에 다시 보냈다(`local_59152ef3` issue-tracker-batch, `local_e9f08d98` tools-rule-batch PR 312, `local_d1765060` timing-tests-under-load, `local_48850536` 대기열 313·317·358·359 PR 반영, `local_d928b27e` canary-runner-batch-retro, `local_c55fa64e` worktree-overrides-pc-check). 앞서 인계된 세션들이 이 지시를 잃고 다음 일을 이어 간 것이 그 까닭이다. 이 PR을 병합한 세션이 재개 메시지를 보낸다.

이어받은 세션(2026-10-20)에 `local_bbb2d881`(chore/issue-tracker-batch)이 메시지를 보냈다. 정지 지시를 받고 PR 없이 멈췄고, 재개 메시지는 그 세션으로 보내 달라고 했다. 커밋 4c80cb78(대기열 104·172·371 반영)과 origin/main 병합 커밋 00158572가 로컬에만 있다. 사용자가 그 세션에서 "멈추고 기다린다"를 고른 까닭은 ADR 0036과의 충돌이다. 그 브랜치는 104행을 "반영함"으로 닫는데 이 브랜치는 같은 행을 만료로 닫고, 세 행 모두 1회차에 지침 문장을 더하는 것이라 새 문턱에 미치지 못한다. 재개 뒤에 그 세션이 main을 당기고 새 규약으로 브랜치를 다시 본다. 이 세션에서 할 일은 없다.

## 셀프 리뷰

앞 세션은 `/code-review`를 부른 직후 인계 계기가 와서 단계를 밟지 않았다. 이어받은 세션(2026-10-20)이 기점 `5e7fa88d`로 했다. 범위는 diff의 파일 23개(새 파일 다섯은 intent-to-add), 커밋 0개, 미추적 1개(이 일지)다. 명세는 ADR 0036 초안과 이 일지의 사용자 프롬프트 원문이다. 리뷰 전에 `tools/run_checks.py` 전체(pyright 포함 여덟 검사 통과)와 ruff 두 줄(통과)을 돌렸다.

표준 축은 Major 2·Minor 9·판단 항목 여럿, 명세 축은 Major 2·Minor 10·Nit 3을 냈다. 두 축이 같은 것을 짚은 것은 셋이다(만료가 회차 3 이상까지 닫는다, `사람 몫` 판정, 처음 적용의 열여섯).

고친 것.
- (표준 Major) 변이 둘("회차 문턱을 넘는 것만 센다", "같은 대상 파일의 문턱을 둘로 낮춘다")이 이 브랜치가 이름을 바꾼 시험을 `-k 결정표의_두_조건`으로 골라 아무 시험도 고르지 못했다. 선택자를 `결정표의_조건을_모은다`로 고치고 서른일곱 전체를 돌렸다.
- (두 축 Major) 만료가 회차 3 이상인 행까지 닫아, chore를 기다리는 행의 세 번째 문턱이 조용히 사라질 수 있었다. 도구가 회차 3 이상을 만료에서 빼고(시험을 먼저 빨갛게 봤다), ADR·retro 5단계·도구 독스트링에 적었다. 고친 도구로 기점의 대기열을 다시 세니 만료 13행은 같고 그 가운데 회차 3 이상은 없었다(회차 3 이상은 306·227·358·359).
- (명세 Major) 만료한 행을 이은 행도 만료하면 다음 사건이 어느 회차를 이을지 정해져 있지 않았다. k는 행 찾기에 걸린 행 가운데 가장 큰 회차에 하나를 더한 값이라고 ADR과 retro에 적었다.
- (두 축 Minor) `사람 몫` 판정이 쌍점을 보지 않아 `사람 몫이 아닌 …`이 사람 몫이 되고 `**사람 몫:**`은 빠졌다. `사람 몫:`으로 보고 앞의 `**`를 벗긴다(시험 먼저).
- (표준 Minor) `hook_report.py`가 래퍼의 두 문구 가운데 하나(훅 파일이 없다)만 걸렀다. 둘째(훅 이름 인자가 하나가 아니다)도 거른다(시험 먼저, 변이 하나 더).
- (표준 Minor) 두 도구의 `main` 인자 시험이 종료 코드만 봤다. stderr의 까닭까지 본다.
- (표준 Minor) retro 5단계가 "날짜를 찾지 못한 행"을 어떻게 할지 적지 않았다. 그 행의 글이 대기열에 처음 든 커밋을 git 기록에서 찾아 적는다고 썼다. 번호로 찾으면 재번호 전의 다른 행이 걸린다(13을 `-S"| 13 |"`로 찾으니 대기열을 만든 #43이 나왔고, 글로 찾으니 #47이었다).
- (표준 Minor) 닫힌 행이면 잇는다는 규칙과, 받아들여 닫은 종류의 새 사례는 회차를 더하지 않는다는 규칙이 부딪쳤다. 받아들여 닫은 행은 행 찾기에 걸려도 잇지 않는다고 ADR과 retro에 적었다.
- (두 축 Minor) 처음 적용에서 닫는 행은 열여섯이 아니라 열일곱(만료 열여섯과 306)이다. ADR을 고쳤다.
- (명세 Minor) 13·16은 PR #46이 아니라 PR #47(`29e00fa0`)에서 들어왔다. ADR과 대기열의 두 승인 칸을 고쳤다.
- (명세 Minor) ADR의 따옴표 인용 둘이 원문과 달랐다. 원문대로 옮기거나 따옴표를 뗐다.
- (명세 Minor) 묶는 조건이 ADR과 next-session에서 달랐다. ADR을 next-session의 "그 행과 대상 파일이 같은 고침 행"에 맞췄다.
- (명세 Minor) 단계를 닫는 지침에 처음부터 붙이는 계기 훅이 새 문턱에 걸리는지 ADR이 말하지 않았다. 따로 세지 않고 그 지침과 함께 간다고 ADR과 retro 4단계에 적었다.
- (명세 Minor) ADR의 거부한 안이 받아들여 닫은 306의 종류(부하에서만 빨간 시험)를 회차를 이어 세는 예로 들었다. 예를 고쳤다.
- (명세 Minor) 워크트리의 retro가 옛 사본으로 만료할 수 있었다. `--ref origin/main`으로도 돌려 두 출력에 모두 든 행만 닫는다고 썼다.
- (명세 Minor) chore 배치가 새 훅 행을 반영할 때 `hook_report.py`를 거치지 않았다. 돌리는 때를 반영하기 전에서 "문턱을 지나면(이 세션에서 반영하든 대기열에 두든) 그 전에"로 바꿨다.
- (두 축 Minor) 뺄 후보 점검이 드물게 돌고 모델 교체 14일을 알리는 장치가 없다. 장치를 더하지 않고 ADR Consequences에 적었다.
- (표준 판단·잔존) 훅 독스트링 둘(`hook_user_settings_read`, `hook_bash_cd_outside`)이 옛 예외를 지금의 규칙처럼 인용했다. 과거형으로 고쳤다. `hook_env_read`는 이미 과거형("갔다")이라 두었다. `.claude/rules/tools.md`의 "예외는 둘이다"는 지난 예외를 두 예외 뒤로 옮겼다.
- (명세 Minor) 런북: `KICKOFF.md`의 옛 예외("실패가 조용해")를 뗐고, 복사 목록에 두 도구를 더했고, 결정표 줄의 설명에 제품 먼저와 만료를 더했다. 템플릿의 손상 정의에 "체크아웃"을 더했다(Nit). 대기열 머리말의 닫기 규약에 만료와 받아들여 닫기를 더했다(Nit).
- (표준 Minor) 낡은 카나리아 `next_session_queue_open_rows.toml`의 질문이 옮겨 간 칸을 가리켰다. 칸을 고치고 고친 질문으로는 돌리지 않았다고 적었다. 고친 문장을 기대 문구로 든 `retro_threshold_and_expiry.toml`은 기대와 질문을 고쳐 다시 돌렸다.
- (표준 판단) ADR "바뀌는 곳"에 카나리아, 프로브 README, 훅 독스트링을 더했다.

남긴 것과 까닭.
- ADR이 `status: accepted`인데 승인 전이다(표준 Minor): 이 저장소의 ADR 36개가 모두 `accepted`로 쓰여 있고 `proposed`는 없다. 승인은 커밋 전에 받는다.
- 새 변이에 표지(`expect_output`)가 없다(표준 Minor): `tools/mutate.py`가 수집 오류와 선택된 시험 없음을 빨강이 아니라 오류로 센다(그 독스트링). 남는 것은 `-k`로 좁힌 시험이 겨냥하지 않은 까닭으로 빨개진 경우이고, 두 표의 앞선 스물셋도 표지가 없다. 프로브 README 행에 적었다.
- 판단 항목: `(모름)`·`(여럿)` 표지 문자열과 `kind: str`(Primitive Obsession), `_record_firings`의 튜플(Data Clump), `folder_name_of`의 중복(독스트링이 `token_report.py`와 같다고 적는다), 손상 정의의 중복(템플릿은 새 프로젝트가 홀로 읽는 사본이고 ADR은 기록이다), 스킬 본문의 경위 문장(이 저장소의 스킬은 규칙마다 까닭과 사례를 둔다. retro 4단계의 "2026-10-19까지는" 하나는 줄였다).
- 시간대(표준 판단): 들인 날은 커밋한 자리의 시간대 날짜이고 창은 UTC 날짜다. 창 첫날 무렵에 들인 훅만 하루 차이로 판정이 갈린다.
- 프론티어가 빈 때 고를 줄이 없다(명세 Minor): 이 diff 전부터 "그 기능의 마지막 티켓이었다" 줄도 같다. 이 변경이 만든 틈이 아니다.
- 닫은 날 `만료 2026-10-20`과 ADR의 `--today 2026-10-19`(명세 Nit): 두 날 모두 같은 13행이다(명세 축이 확인). 닫은 날을 적은 것이다.

다시 돌린 명령.
- `uv run pytest -q -p no:cacheprovider tests/tools/test_queue_open_rows.py tests/tools/test_hook_report.py`: 새 시험 셋이 먼저 빨갛고(둘은 기존 동작을 단단히 한 것이라 초록), 구현 뒤 71개 통과.
- `PYTHONUTF8=1 uv run python tools/mutate.py`: `queue_open_rows_mutations.toml` 서른일곱, `hook_report_mutations.toml` 스물 모두 기대대로 빨강. `--check`로 두 표의 원문 확인.
- `uv run python tools/canary.py --shape`(카나리아 여섯 통과)와 `--preflight`(고친 다섯 가운데 넷 통과. `next_session_queue_open_rows.toml`의 대조군 실패는 이 변경 전부터다). `retro_threshold_and_expiry.toml`을 다시 돌려 통과 4·실패 0(실험군은 고친 문장을 옮겼고 대조군은 "없음").
- `uv run python tools/queue_open_rows.py --ref 5e7fa88d --today 2026-10-19`(열린 94, 만료 13, 날짜 없음 4·13·16)와 `--today 2026-10-20`(열린 77, 만료 없음, 회차 3 이상 227·358·359, 사람 몫 238).
- 손으로 치는 다섯은 커밋의 pre-commit 결과로 갈음한다. 결과는 커밋 뒤에 적는다.

PR 직전 리뷰에 밀 주장(반영하며 새로 쓴 사실 문장).
- ADR·retro: "회차 3 이상인 행은 chore가 반영할 때까지 남긴다", "k는 행 찾기에 걸린 행(만료한 행과 그 행을 이은 행) 가운데 가장 큰 회차에 하나를 더한 값이다", "워크트리에서는 `git fetch origin` 뒤 `--ref origin/main`으로도 돌려 두 출력에 모두 든 행만 닫는다".
- retro: "번호로 찾으면 재번호 전의 다른 행이 걸릴 수 있다".
- ADR: "13과 16은 PR #47을 병합한 2026-09-23", "처음 적용에서 닫히는 행은 열린 94행 가운데 열일곱이다", "모델을 바꾼 지 14일이 된 날을 알리는 장치도 없다".
- 프로브 README: "`tools/mutate.py`가 수집 오류와 선택된 시험 없음을 빨강이 아니라 오류로 세므로, 표지 없이 지나가는 것은 `-k`로 좁힌 시험이 겨냥하지 않은 까닭(다른 단언, 준비 단계의 오류)으로 빨개진 경우다".
- `hook_report.py` 독스트링: 래퍼가 지나간 알림은 `launch_hook.skip_reason`의 두 문구다.
- `KICKOFF.md`: 두 도구 줄의 "(바꿀 곳 0)".

## 인계 지시문

```
다음 작업: chore/hook-census (ADR 0036). 하네스는 세 번째나 손상 한 번에 더하고, 쓰이지 않는 훅은 빼자고 넘기며, 대기열 행은 14일 뒤 만료한다는 변경의 셀프 리뷰·승인·커밋·PR·병합과 멈춘 세션의 재개
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 계속 하네스 작업만 하는것 같은데 도대체 언제 끝나??
브랜치: chore/hook-census
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-07-harness-stops-growing.md, docs/adr/0036-harness-grows-on-third-occurrence-and-queue-rows-expire.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 5e7fa88d, 명세는 ADR 0036 초안과 일지의 사용자 프롬프트 원문)부터 한다. 새 파일은 git add -N으로 표시해 두었다. 리뷰를 반영한 뒤 ADR 0036을 사용자에게 보여 승인받는다(306을 받아들여 닫은 것과 대기열의 처음 적용 16행이 든다). 승인 뒤 일지를 마무리하고 커밋한다. origin/main이 이 브랜치의 기점보다 앞서 있어 PR 전에 sync_with_base_branch로 합친다. .claude/rules/tools.md와 대기열은 열린 PR 312 등과 겹칠 수 있다. 병합한 뒤에는 사용자의 요청대로 멈춰 둔 세션들에 재개 메시지를 보낸다. 대상과 경위는 일지의 "세션 통제" 절이고, 보내기 전에 list_sessions로 그사이 새로 생긴 세션도 찾는다. 재개 메시지에는 main을 당긴 뒤 디스크의 SKILL.md를 Read로 열어 새 규약을 따르라고 적는다. 병합 전까지 새로 생긴 세션에는 같은 정지 지시를 보낸다. 일지 docs/journal/2026-10-20-07-harness-stops-growing.md
확인할 선행 조건: tools/run_checks.py 전체와 pyright를 마지막 변경 뒤 돌리지 못했다(인계로 멈췄다)
이번 요청 범위: PR과 병합까지, 그 뒤 멈춘 세션의 재개까지
```

열기 직전 `list_sessions`에서 인계로 또 생긴 둘(`local_bbb2d881` chore/issue-tracker-batch, `local_96616a7c` chore/tools-rule-batch PR 312)을 찾아 같은 정지 지시를 보냈다(앞은 queued, 뒤는 delivered). 재개 메시지의 대상에 둘을 더한다.

제목을 `chore/hook-census (인계함)`으로 바꿨고, 백그라운드 `run_checks`(br60vd8gh)를 멈췄다. 워크트리는 이미 잠겨 있지 않았다(`is not locked`).

open-session을 부른다 2026-10-19T23:19:41Z

## 커밋 (이어받은 세션, 2026-10-20)

첫 커밋 시도는 pre-commit의 ruff format이 `tests/tools/test_queue_open_rows.py`의 한 호출을 한 줄로 합쳐(가짜 날짜를 `반영 2026-02-30`으로 줄여 줄에 들어가게 됐다) 1로 끝났다. 같은 실행에서 ruff check와 검사 러너 여덟(check-instructions, zizmor, lint-imports, check-type-escapes, pyright, run-hooks, pytest, web-verify, 187초)과 표·줄 구분 문자·변이 표·카나리아 모양 검사는 통과했고, 헌법 판 검사는 고친 헌법 파일이 없어 `Skipped`였다. 인용 대조가 이 일지의 따옴표 셋을 경고해, 요지를 옮긴 둘은 따옴표를 떼고 하나는 retro 본문의 글자 그대로로 바꿨다. 고친 줄을 스테이지해 다시 커밋했다.

커밋 직전 `list_sessions`에서 정지 지시 뒤에 인계로 생긴 `local_eda9fa35`(chore/timing-tests-under-load)를 찾아 같은 정지 지시를 보냈다(delivered). 재개 메시지의 대상에 더한다. PR 312(tools-rule-batch)는 그사이 병합됐다.

다시 친 커밋 `7bf2e4fc`의 pre-commit은 모두 통과했다. ruff check·format, 검사 러너 여덟(zizmor, check-instructions, lint-imports, check-type-escapes, pyright 27.2초, run-hooks 60.3초, pytest 153.2초, web-verify 201.7초, 합 201.95초), 표·줄 구분 문자·변이 표·카나리아 모양, 인용 대조(경고 없음), 커밋 메시지다. 헌법 판 검사는 고친 헌법 파일이 없어 `Skipped`였다.

## main 합치기 (이어받은 세션, 2026-10-20)

`sync_with_base_branch`는 이 세션이 앱이 만든 워크트리가 아니라고 거절해, `git merge --no-edit origin/main`으로 `51572a31`(#307~#313 여섯)을 합쳤다. 병합 커밋은 `33ccba49`이고, 그 pre-commit의 검사 러너 여덟이 통과했다(pytest 269.0초, 합 269.34초. ruff 둘은 병합에서 고친 `.py`가 없어 `Skipped`).

- 충돌은 `.scratch/retro-queue.md`의 306 행 하나였다. main 쪽은 회고 둘(일지 2026-10-19-34·2026-10-20-06)이 회차를 11로 올렸고, 이 브랜치는 그 행을 받아들여 닫았다. main 쪽 내용을 살리고 그 위에 취소선과 닫힘 표지를 얹었으며, 표지 끝에 "10·11회차(일지 2026-10-19-34·2026-10-20-06)는 이 결정을 병합하기 전에 나란히 돈 회고가 더했다"를 더했다. `.claude/rules/tools.md`와 프로브 README는 다른 줄이라 저절로 합쳐졌다.
- ADR 0036의 "나흘에 9회차가 쌓였다(그 행의 승인 칸)"는 합친 뒤 그 칸이 11회차라 맞지 않게 되어, 괄호를 "이 결정을 쓴 때 그 행의 승인 칸. 이 결정을 병합하기 전에 나란히 돈 회고가 11회차까지 더했다"로 고쳤다.
- 합친 대기열을 `uv run python tools/queue_open_rows.py --today 2026-10-20`으로 다시 셌다. 열린 행 69개, 만료할 행 없음, 회차 3 이상은 227 하나(358·359는 #308이 닫았다), 사람 몫 238이다.
- #312가 `tools/`의 subprocess 호출에 시간 제한을 요구하는 검사를 더했다. 이 브랜치의 두 도구는 이미 `GIT_TIMEOUT`을 두어 병합 커밋의 check-instructions가 통과했다. #308의 변이 표 가드 아래에서 `tools/mutate.py --check`로 두 표(서른일곱·스물)의 원문을 다시 확인했다. 두 표에는 표지가 없어 판정 낱말 가드(대기열 313)에 걸리지 않는다.
- `tools/sibling_overlap.py`는 번호 겹침 없음이었다. 다음 빈 번호는 일지 `2026-10-20-09`, 대기열 374이고, 형제 `timing-tests-under-load`의 일지 2026-10-20-08이 이 일지를 이름순으로 앞선다(그쪽이 먼저 병합되면 이 일지를 옮긴다).

PR 직전 리뷰에 밀 주장에 더한다(합치며 새로 쓴 사실 문장): 위 306 표지의 문장과 ADR 16행의 괄호.

## 인계 (커밋 뒤)

병합 커밋 뒤에 인계 계기(세션 컨텍스트 252,278 토큰, 경계 `커밋 뒤`)가 왔다. 인계하지 않는 다섯에 들지 않았다. 계기를 낸 병합 커밋은 성공했고, 요청 범위는 병합과 재개까지이며, 이 세션의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 같은 경계가 아니고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 제목은 `chore/hook-census`이고 `chore/hook-census (인계함)`으로 바꾼다.

남은 단계(새 세션이 한다): 이 일지의 고친 부분을 커밋, 푸시, PR 직전 리뷰, PR 열기, 봇 회차, 병합, next-session, 재개 메시지.
- PR 직전 리뷰: `coderabbit auth status`가 `Seat: not assigned`라 CLI가 돌지 못한다. 대체 둘(`/security-review`와 `bug-perf-review`)을 나란히 돌린다. `bug-perf-review`의 기준은 `origin/main`이고, 밀 주장은 셀프 리뷰 절의 목록과 위 합치기 절의 둘이다.
- 재개 메시지 대상: 세션 통제 절의 여섯과 둘(`local_bbb2d881`, `local_96616a7c`), 그리고 `local_eda9fa35`. 처음 보낸 대상은 앞 세션의 요약에만 있어, 보내기 전에 `list_sessions`에서 정지 지시를 받고 멈춘 세션을 다시 찾는다. 병합 전에 새로 생긴 세션에는 같은 정지 지시를 보낸다.
- 사용자에게 할 보고: 병합 뒤 다음 작업은 제품(end-user-continuation 티켓 02~06이 `ready-for-agent`)이다. 선택 화면 설명의 "티켓 01"이 틀렸다는 것을 바로잡는다.

```
다음 작업: chore/hook-census (ADR 0036). 하네스는 세 번째나 손상 한 번에 더하고, 쓰이지 않는 훅은 빼자고 넘기며, 대기열 행은 14일 뒤 만료한다는 변경의 푸시·PR 직전 리뷰·PR·병합과 멈춘 세션의 재개
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 계속 하네스 작업만 하는것 같은데 도대체 언제 끝나??
브랜치: chore/hook-census
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-20-07-harness-stops-growing.md, docs/adr/0036-harness-grows-on-third-occurrence-and-queue-rows-expire.md
이어받을 상태: 인계: 커밋 뒤. ADR 0036은 사용자가 승인했다. 커밋 7bf2e4fc와 origin/main 병합 커밋 33ccba49까지 했고 아직 푸시하지 않았으며 열린 PR이 없다. 일지의 "main 합치기"와 "인계 (커밋 뒤)" 절은 커밋하지 않았다. 그 일지 변경을 커밋하고, 푸시하고, PR 직전 리뷰(CodeRabbit 좌석이 없어 /security-review와 bug-perf-review를 나란히, 밀 주장은 일지)를 반영한 뒤 PR을 열어 봇 회차와 병합까지 한다. 병합한 뒤에는 사용자의 요청대로 멈춰 둔 세션들에 재개 메시지를 보낸다. 대상은 일지의 "세션 통제"와 "인계 (커밋 뒤)" 절이고, 보내기 전에 list_sessions로 그사이 새로 생긴 세션도 찾는다. 재개 메시지에는 main을 당긴 뒤 디스크의 SKILL.md를 Read로 열어 새 규약을 따르라고 적는다. 병합 전까지 새로 생긴 세션에는 같은 정지 지시를 보낸다. 사용자에게 할 보고는 일지의 "인계 (커밋 뒤)" 절에 있다. 일지 docs/journal/2026-10-20-07-harness-stops-growing.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지, 그 뒤 멈춘 세션의 재개까지
```

제목을 `chore/hook-census (인계함)`으로 바꿨다. 띄운 백그라운드 작업은 모두 끝나 있었고, 워크트리는 이미 잠겨 있지 않았다(`is not locked`).

open-session을 부른다 2026-10-20T00:25:49Z

## 푸시와 PR (셋째 세션, 2026-10-20)

시작 프롬프트는 앞 두 세션과 같다("계속 하네스 작업만 하는것 같은데 도대체 언제 끝나??"). 제목을 `chore/hook-census`로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다(잠겨 있지 않았다). 병합 커밋 뒤 origin/main은 움직이지 않았다(`git log 33ccba49..origin/main`이 비었다).

- `tools/sibling_overlap.py`가 1로 끝났다. 위 합치기 절의 "다음 빈 번호" 인용이 어디에도 없는 일지 번호라서다. 일부러 적은 번호라 코드 스팬에 넣었다. 그 밖의 겹침은 없고, 열린 PR #296·#297·#314와 형제 워크트리 넷이 `.scratch/retro-queue.md`·`.claude/rules/tools.md`·프로브 README를 함께 고친다(뒤에 병합하는 쪽의 충돌 후보).
