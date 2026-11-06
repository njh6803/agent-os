# 2026-11-07 (02) 회고 반영 대기열을 항목마다 파일 하나인 폴더로 나눈다 (retro-queue-per-item 02)

세션 제목: `feature/02-retro-queue-one-file-per-item`. 브랜치 `feature/02-retro-queue-one-file-per-item`, 워크트리 `.claude/worktrees/02-retro-queue-one-file-per-item`. 모델 Sonnet 5.5 / high. 일을 여덟 서브에이전트에 나눠 맡겼고, 아래에서 "서브에이전트 보고"라고 적은 것은 그 보고를 이 세션이 읽은 것이다(이 세션이 다시 재지 않았다).

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/retro-queue-per-item/issues/02-retro-queue-one-file-per-item.md

지시문의 다음 작업은 "회고 반영 대기열을 표 하나에서 항목마다 파일 하나인 폴더로 나누는 구현 티켓", 다음 단계 구현, 어디서는 새 세션(주 체크아웃 미갱신이라 `tidy-checkouts`를 먼저 돌고 `EnterWorktree`, name은 `02-retro-queue-one-file-per-item`), 모델 `Sonnet 5.5 / high`, 이번 요청 범위 "PR과 병합까지"였다. 티켓이 크다고 적혀 있어 한 세션에 다 못 하면 인계로 잇는 조건이었다.

## 한 일

1. **시작.** 세션 제목을 브랜치로 바꾸고 `tidy-checkouts`를 돌았다. 주 체크아웃을 `819782eb`에서 `288686a5`로 당겼고 브랜치 `worktree-01-retro-threshold-five`를 지웠다. 병합된 `05-default-model-required-and-checked` 워크트리는 `agent-os.exe`와 `python.exe`가 쥐어 이름 바꾸기가 막혀 남았다. 그 뒤 `EnterWorktree`로 들어가 브랜치를 `feature/02-retro-queue-one-file-per-item`으로 바꿨고 `uv sync`와 `pnpm -C web install --frozen-lockfile`을 쳤다. 첫 편집으로 티켓 `Status:`를 `in-progress`로 바꿨다.
2. **이행.** 옛 표(`.scratch/retro-queue.md`, 559행)를 `.scratch/retro-queue/<NNNN>.md` 559개로 옮겼다. 스크립트는 스크래치패드에서 한 번 돌렸고 저장소에 남기지 않았다. 옛 열림·닫힘 판정은 `HEAD`의 옛 `tools/queue_open_rows.py`를 스크래치패드에 풀어 그대로 썼다. 닫힘·만료 표지는 승인 칸 안의 `**닫힘 (…)**`·`**만료 …**`를 괄호 깊이를 세어 상태 줄로 옮겼고(표지가 승인 칸 끝이 아닌 일곱 행과 표지가 아닌 모양인 한 행(`306`, 앞에 "받아들여"가 붙었다)은 손으로 모양을 보았다), 취소선 한 쌍은 걷었다. 머리는 백틱과 괄호 밖에서 처음 만나는 `. `까지이고 굵게·취소선이 홀수면 닫을 때까지 늘렸다.
   - **세어 맞댄 것(옛 표 대 새 폴더, 손으로 쳐서 읽었다).** 항목 559개 대 파일 559개, 번호 집합 같음, 열림 117 대 117, 닫힘 442 대 442, 가장 큰 번호 581.
   - **항목마다 맞댄 방법.** 별도 스크립트(`verify.py`, 스크래치패드)가 옛 표를 옛 도구의 행 판정으로 읽고 새 파일을 따로 파싱해 항목 559개 모두에서 비교했다. 열린 117개는 상태가 `열림`, 어디로 줄이 옛 어디로 칸과 같음, 승인 줄이 옛 승인 칸과 같음, 머리와 본문을 이은 글이 옛 무엇 칸과 공백을 빼고 같음을 본다(`\|`는 `|`로 풀어 비교). 닫힌 442개는 상태가 `닫힘`·`만료`로 시작함, 어디로 줄 같음, 무엇 칸이 취소선 한 쌍을 걷은 글과 같음, 승인 줄과 상태의 글자가 옛 승인 칸의 글자와 같음을 본다. 결과는 "불일치 0".
   - **회차를 이은 항목.** 열린 항목 가운데 회차를 이은 것(승인 칸에 여러 회차가 쌓인 것)도 위 비교의 "승인 줄이 옛 승인 칸과 같음"에 든다. 수는 같아도 필드가 틀릴 수 있다는 걱정은 이 항목별 비교가 막는다.
   - **다시 합친 뒤 맞댐.** `git fetch origin` 뒤 `HEAD..origin/main`이 비어 있다. main이 옛 표를 이행 뒤에 바꾸지 않았다.
3. **도구와 시험.** `tools/queue_open_rows.py`를 폴더 읽기로 다시 썼다(서브에이전트 보고). `--queue`는 폴더를, `--ref`는 그 커밋의 폴더를 받고 `git ls-tree`와 `git cat-file --batch` 한 프로세스로 읽는다. 폴더 없는 이행 전 커밋은 종료 2이고 옛 파일로 돌아가지 않는다. `--search`는 파일 경로를 찍고 줄 번호를 찍지 않는다. 인용을 푸는 함수 `item_name`·`item_path`(573과 0573이 같은 `0573.md`)를 이 도구에 두었다. 시험은 항목 파일 픽스처로 옮겼고, 저장소 상태 시험 `tests/test_retro_queue_names.py`(옛 파일, 라벨 줄, 이름 상수 `MAX_OLD_NUMBER = 581`)를 새로 두었다. 빨강은 도구를 바꾸기 전 `ImportError: cannot import name 'Item'`이었다(모듈째).
4. **아침 보고.** `morning_collect`·`morning_sources`(`main_queue`)·`morning_report`가 origin/main의 폴더를 읽고 식별자를 문자열로 받는다. 이행 전후 대기열 절을 서브에이전트가 맞댔다: 2026-11-06 기준 열린 항목 117, 기한 지난 0, 사람 몫 2, 회차 5 이상 11개(420 430 431 565 558 579 214 475 499 535 578)가 옛 판과 같고, 이름표의 "행"이 "항목"으로 바뀐 것과 무엇 칸이 머리 한 문장이 된 것만 다르다(서브에이전트 보고). 시험으로 두지 않은 이유는 티켓 "이행 전후의 대기열 절"대로다(이행 뒤에는 옛 파일이 없고 CI는 깊이 1이다).
5. **번호 대조 도구.** `tools/sibling_overlap.py`에서 대기열 번호의 읽기·겹침·다음 빈 번호·옮길 번호·`--move`·합치는 중 처리·빈 자리 검사의 대기열 몫을 뗐다. 다음 빈 번호 줄은 `일지 X, 티켓 NNN`이다. 빨강은 `merge-base에 옛 대기열 표가 없어도 2로 끝나지 않는다` 시험이 "형제를 대조하지 못했다. merge-base 에서 번호의 자리가 비었다"로 종료 2인 것이었고, 전체로 76개가 빨갰다(서브에이전트 보고). 지운 시험은 대기열 행을 다루던 다섯이다.
6. **커밋 검사와 훅.** `tools/check_ticket.py`가 `.scratch/retro-queue/` 직계 `.md`를 면제로 보고(하위 폴더·`retro-queue-x/`·`issues/x.md`는 막는다), 옛 파일 면제는 지웠다. `hook_measure_word`·`hook_session_card`의 경로, `hook_journal_retro`·`run_hooks.py`의 번호 줄·픽스처를 맞췄다. 빨강은 18건이었다(서브에이전트 보고).
7. **스킬·지침·문서·런북.** `retro`·`next-session`·`directive.md`, `CLAUDE.md`, `CODING_STANDARDS.md`, `docs/agents/issue-tracker.md`, `docs/constitution/operations.md`, `KICKOFF.md`, `kickoff/claude-md-template.md`, `kickoff/pitfalls.md`를 고쳤다. 헌법 판을 3.0.66에서 3.0.67로 올렸다(형제가 쓴 가장 높은 판이 3.0.66이었다).
8. **카나리아.** 여덟 명세와 `directive.md`를 원천으로 든 `next_session_label_ticket_notice`를 새 꼴에 맞췄다. 새 `claude -p` 세션에서 아홉 모두 통과했다(실험군 3회차 통과, 대조군은 옛 커밋 사본). `tools/canary.py --shape`는 137 통과다(서브에이전트 보고). 대조군 커밋은 명세마다 달라 각 명세 머리 주석에 있다.
9. **변이 표와 프로브.** `queue_open_rows_mutations.toml`을 다시 썼고(88), `check_ticket_mutations.toml`(21)·`measure_word_hook_mutations.toml`(17)·`sibling_overlap_mutations.toml`(189)을 고쳐 `tools/mutate.py` 전체 실행에서 모두 기대대로였다(서브에이전트 보고). 프로브 `msys_pathconv/run.sh`·`time_hook.sh`·`session_cost/collect.py`·`journal_number_hook/run.py`와 두 프로브 README를 고쳤다.

## 결정·번복·확인

- **머리 자르기.** 처음 이행은 괄호 안의 마침표에서 머리를 끊어 `(이 브랜치의 514·506이 …같은 일이었다.`처럼 괄호가 열린 채 끝났다. 괄호 깊이를 세도록 스크립트를 고쳐 다시 돌렸다. 맞대기는 두 번 모두 불일치 0이었다.
- **열린 항목 가운데 분할이 해소하는 것은 없다고 보았다.** `retro-queue.md`·"다음 빈 번호"·`offset`·"대기열 행"·충돌을 든 열린 항목 여섯(0476 0505 0510 0532 0569 0570)을 읽었다. 0510("형제가 대기열에 더한 행의 머리를 찍는다")은 처방의 모양이 항목 파일로 바뀌지만 같은 일을 다룬 형제 항목을 알리는 일이 남아 열어 둔다. 0532는 전체 계획 생성 조각, 0476·0569는 일지 이름 조각, 0570은 사람 몫이다. 이 PR에서 닫은 항목은 없다.
- **`tools/sibling_overlap.py`의 줄 끝.** 변이 표 정리 서브에이전트가 시작 때 이 파일이 1943줄 전부 CRLF였던 것을 보고 LF로 바꿨다. 앞 서브에이전트의 패치가 CRLF로 썼을 것으로 보았다. `HEAD`는 LF이고 git diff 해시가 바꾸기 전후 같았다(서브에이전트 보고).
- **변이 표의 기존 결함.** 표지가 시험 원문에 글자 그대로 있어 전체 실행이 시작도 못 하는 변이가 `check_ticket_mutations.toml`에 넷, `sibling_overlap_mutations.toml`에 열넷 있었다. 대기열 변경과 무관한 기존 결함이고 표지를 다시 골랐다.
- **시험이 없어 표에서 뺐다가 되살린 변이 넷.** 처음에는 남은 코드를 겨누지만 그것을 잡던 시험이 대기열 시험과 함께 지워진 변이 넷(`옮기기가 둘 줄을 넘기지 않는다`, `main 의 판을 둘 줄에서 뺀다`, `줄 끝의 CR 을 떼지 않고 둘 줄과 견준다`, `main 보다 앞서면 다른 종류의 겹침 이동을 버린다`)을 표에서 뺐다. 셀프 리뷰 명세 축이 "지우지 말고 일지·ADR 픽스처로 옮겼어야 한다"고 짚었고 맞는 말이라, 서브에이전트가 시험 넷을 일지·ADR 픽스처로 다시 썼다(`tests/tools/test_sibling_overlap.py`의 `--move`가 같은 번호의 줄을 둔다·그 대조군·CRLF 파일의 둘 줄 견줌·앞선 일지와 ADR 번호 겹침의 동시 이동). 변이 110~113으로 되살렸고 `expect_output`은 변이를 손으로 넣어 실패 출력을 본 뒤 골랐다(서브에이전트 보고). 이 세션이 `pytest tests/tools/test_sibling_overlap.py` 125 통과와 `mutate.py --check` "변이 193 모두 원문이 한 번씩 있다"를 다시 쳐서 확인했다. 변이를 다시 돌려 빨강을 본 것은 서브에이전트의 몫이다.
- **`msys_pathconv/run.sh` C절.** 폴더가 아직 origin/main에 없어 우회 종료 코드가 기대와 다르게 나온다(1이 찍힌다). 이 PR이 병합된 뒤에 다시 돌려야 의미가 있다.
- **목록 밖에서 찾은 자리.** `kickoff/pitfalls.md`("열린 대기열 행"), `tools/hook_measure_word.py`의 알림 본문(`_BODY`의 "취소선, 닫힘 표지"를 "상태 줄을 열림에서 닫힘으로 고친 것"으로), 두 프로브 README의 행, `.scratch/harness/probes/session_cost/README.md` 끝 절(`retro_rows`의 뜻이 바뀐 것)이다. `.github/PULL_REQUEST_TEMPLATE.md:43`과 `.github/workflows/claude-code-review.yml:77·99`의 "일지·대기열·하네스 탐침 밖의 파일" 경로 거르기는 티켓 03(리뷰 봇의 경로 거르기)의 몫이라 두었다.
- **`KICKOFF.md`의 "경로 상수 다섯".** 번호 대조 도구에서 대기열 몫이 빠졌으니 숫자가 달라졌을 수 있었다. `tools/sibling_overlap.py`의 경로 상수는 `JOURNAL_DIR`·`ADR_DIR`·`CONSTITUTION`·`HARNESS_ISSUES` 넷이라(`git grep`으로 센 것) "넷"으로 고쳤다. 이 줄은 셀프 리뷰 명세 축이 짚었다.

## 셀프 리뷰 (`/code-review`)

범위: 기준 SHA `288686a57cd0241c16151223f1a9243ed31e5718`, 변경 파일 56개(이관한 폴더 제외), 커밋 0개(전부 미커밋), 미추적 2개와 `.scratch/retro-queue/` 560개. 표준 축은 `sonnet`·`high` 서브에이전트, 명세 축은 본 세션 모델 서브에이전트가 맡았다. 아래 판정은 두 보고를 이 세션이 근거를 대 보고 가른 것이다.

**고친 것.**
- `journal_number_hook/run.py` 독스트링의 "네 자리가 비면"을 "세 자리(일지, ADR, 헌법 판)가 비면"으로(대기열 몫이 빠져 `empty_places`가 세 자리다).
- `msys_pathconv/run.sh` 주석의 "`0425.md` 로 쟀다"를 "쓰도록 바꿨다(이 경로로는 아직 다시 돌리지 않았다)"로. 프로브 README는 C절 숫자가 옛 파일로 낸 것이라 적었으므로 "쟀다"는 거짓이었다.
- `queue_open_rows.py` 독스트링: "첫 줄 뒤의 빈 줄은 건너뛴다"를 "라벨 줄 앞의 빈 줄은 건너뛴다"로, 상태 값이 시작만 보이므로 `열림하지 않음`도 열림으로 읽는다는 것을 더했고, 인용 풀기 함수(`item_name`·`item_path`)를 아침 보고와 찾기가 가져다 쓴다는 거짓 문장을 "시험이 고정한다. 아침 보고는 스크립트라 가져오지 못해 `morning_report.queue_key`에 따로 두고, 찾기는 경로를 그대로 찍는다"로 바로잡았다.
- `morning_report.py` 독스트링의 "못 보는 것"에 `대기열 items가 많다`가 슬러그로 읽혀 `(이름 없음)`이 붙는 것과 `대기열 3항목`이 항목 3으로 읽히는 것을 적고, 시험 둘(`test_못_보는_것_대기열_뒤_영어_낱말은_…`, `test_못_보는_것_대기열_번호_뒤_항목은_…`)로 고정했다. 시험의 기대는 처음에 제가 출력 모양을 잘못 짐작해 한 번 빨갰고, 실제 출력(`대기열 items (이름 없음)가 많다`)에 맞췄다.
- `tests/test_retro_queue_names.py`에 `stray_problems`와 시험 둘을 더했다. 폴더 README는 "이름이 이 둘이 아니면 시험이 막는다"고 적었는데 `read_folder`는 `.md`만 읽어 `0582.txt`·하위 폴더·`.MD`를 보지 못했다.
- `KICKOFF.md` 289행의 "경로 상수 다섯"을 "넷"으로.
- `retro` 스킬 5단계에 "끊긴 뒤나 압축 뒤에 다시 들어온 회고는 새 제목을 짓기 전에 이 일지의 `## 회고` 절이 적은 식별자를 그대로 쓰고, 그 이름의 파일이 이미 있으면 새로 쓰지 않고 회차를 더한다"를, `next-session` 빼기 단계에 "번호는 앞의 0을 떼고 맞대어 `573`과 `0573`을 같은 항목으로 본다"를 더했다.

**남긴 것과 이유.**
- `.github/workflows/claude-code-review.yml:97`의 `\.scratch/retro-queue\.md$`와 `review_workflow.py`의 `QUEUE`: 티켓 03의 몫이다(`.scratch/retro-queue-per-item/spec.md` 168행·295행, `issues/03-review-bot-path-filter.md`). 리뷰 봇 워크플로를 바꾸는 PR은 따로 먼저 병합한다는 규약 때문에 이 PR에 실을 수 없다.
- `retro/SKILL.md` 6행 머리 주석의 "행", `MIN_ROWS`·`--rows`·`QueueRow`·`retro_rows` 같은 행 단위 이름: 이름 낡음이고 기록이거나 바꾸면 인용이 깨진다. 회고 후보로 올린다.
- 슬러그 정규식이 네 곳(`queue_open_rows.SLUG`, `morning_report.SLUG`, 이름 시험, README)에 있다. 훅·스크립트는 서로 import하지 않는 규약(`.claude/rules/tools.md`) 때문이고 `morning_report`는 그 까닭을 적었다.
- `morning_sources.main_queue`의 `contextlib.chdir`: `git_bytes`에 `cwd` 인자가 없어서다. Feature Envy 쪽 판단 항목이고 동작은 시험이 지킨다.
- 이 PR의 `retro`·`next-session`이 병합 전에는 `--ref origin/main`이 폴더 없는 main을 읽어 종료 2가 나는 갈래(명세 축 갈래 밟기 1): 이행 PR 자체에만 있는 전환기 일이다. 병합 뒤 main에는 폴더가 있다. 이 세션은 병합 전 회고를 로컬 폴더로 돌린다.
- 범위 넘침으로 짚은 `kickoff/pitfalls.md`, `hook_measure_word._BODY`, `session_cost/collect.py`: 위 "목록 밖에서 찾은 자리"에서 이유를 적었다. 변이 표의 기존 결함 열여덟 개도 같다(전체 실행이 시작도 못 하는 표라 고치지 않으면 `--staged`가 막는다).
- 열린 항목을 닫은 것이 0건인데 티켓 박스가 체크된 것(명세 축 (a)3): 박스는 "분할이 해소하는 열린 항목을 읽어 닫을 것을 닫는다"이고 읽은 결과 닫을 것이 없었다. PR 본문에 "없음"과 이유를 적는다.

**PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장 원문).**
- "`queue_open_rows`: 상태 값은 시작만 보므로 `열림하지 않음`도 열림으로 읽는다."
- "`morning_report`: 항목이 아닌 영어 낱말도 `대기열 ` 뒤에 오면 슬러그로 읽는다. 메모에 그 이름이 없으면 `(이름 없음)`이 붙고 경고가 난다(`대기열 items가 많다`). 번호 뒤에 `항목`이 붙은 `대기열 3항목`은 `COUNTERS`에 `항`이 없어 항목 3으로 읽는다."
- "`tests/test_retro_queue_names.py`: `stray_problems`가 하위 폴더와 다른 확장자와 대문자 확장자를 잡는다."
- "`KICKOFF.md`: `sibling_overlap.py`는 번호의 자리가 다르면 경로 상수 넷."
- retro·next-session에 더한 위 두 문장.

**다시 돌린 명령.** 전체 러너는 서브에이전트 보고를 받기 전에 한 번 돌았다. 결과: zizmor·lint-imports·지침 검사·타입 우회 검사·pyright 둘·훅 러너·pytest·web-verify가 초록이었고 `check-ticket`만 빨강이었다. 까닭은 티켓 파일이 색인에 없어서였고 `git add -A` 뒤 `uv run python tools/check_ticket.py`가 출력 없이 끝났다. 리뷰를 반영한 뒤의 다섯 게이트는 커밋의 pre-commit 결과로 갈음한다.

## PR 직전 리뷰

HEAD `8cb60333`(커밋 둘, 작업 트리 깨끗), origin/main(`288686a5`)을 이미 합친 상태에서 돌렸다.

- **카나리아(셀프 리뷰 반영의 문장 둘).** 두 명세에 그 문장을 묻는 물음을 하나씩 더해(`retro_row_search` 물음 5, `next_session_queue_open_rows` 물음 3) 새 `claude -p` 세션(2.1.318)에서 실제로 돌렸다. retro 통과 4, next-session 통과 4, "없음" 섞임 0, 대조군은 모든 물음에 "없음"이었다(러너 `tools/canary.py`가 찍은 집계 줄과 답을 손으로 읽었다). 결과는 두 명세의 `# 최신 결과:` 줄에 있다.
- **CodeRabbit CLI.** `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`였다. 전체 범위는 파일 616개가 한도 150을 넘어 거절됐다(`Too many files`. `coderabbit review --agent --include-untracked`의 출력을 손으로 봤다). 그래서 `coderabbit review --agent --dir tools`(파일 15개)로 좁혀 돌렸고 `findings: 0`으로 끝났다(출력의 `complete` 줄을 읽었다). `tests/`·`docs/`·`.claude/`는 이 CLI로 보지 못했다.
- **`bug-perf-review` 서브에이전트.** 유효 0건, Minor 1건이다. 밀어 둔 주장 넷(상태 값은 시작만 본다, `대기열 ` 뒤 영어 낱말이 슬러그로 읽힌다, `stray_problems`의 세 갈래, `check_ticket`의 면제 범위)은 모두 코드를 읽어 맞다고 판정했고, `queue_open_rows.py --ref origin/main`은 실제로 쳐서 종료 2와 `Not a valid object name`을 봤다. 관련 시험 325건 통과를 서브에이전트가 돌렸다(`test_sibling_overlap.py`는 돌리지 않았다). Minor는 `tests/test_retro_queue_names.py`의 잔여물 시험이 `dir.md`라는 하위 폴더를 넣지 않아 `entry.is_file()` 조건이 변이에 잡히지 않는다는 것이다. **고쳤다.** `dir.md` 폴더를 넣고 기대를 3에서 4로 올렸으며, `is_file()` 조건을 손으로 지우자 `assert 3 == 4`로 빨갛고(`uv run pytest tests/test_retro_queue_names.py -k 잔여물`) 되돌리자 10건 통과했다.
- **`/security-review`.** 지적 0건이다. 새로 외부 입력이 닿는 자리는 `queue_open_rows.py`의 `--ref`(git 인자 목록으로 넘기고 셸을 거치지 않으며, 파일 이름은 `is_item_name`을 지난 것만 읽는다)와 `morning_sources.py`의 `gh`·`git` 호출(고정 인자)뿐이었다. 근거는 코드를 읽은 것이고 변이나 입력을 넣어 돌려 보지는 않았다.

## 회고

후보 둘, 둘 다 승인(회차로 세는 것)이고 넘김은 없다. 기각 둘은 일지에만 남긴다.

1. **승인: `coderabbit-review` 정의의 `Seat: not assigned` 종료(대기열 0578에 6회차).**
   - 사건: 이 PR의 PR 직전 리뷰에서 서브에이전트가 `Seat: not assigned`만 보고 `coderabbit review`를 돌리지 않고 종료했다. 브리프가 "종료하지 말고 돌려서 판정하라"고 적었는데도 정의 1단계가 우선했다. 본 세션이 `coderabbit review --agent --include-untracked`를 직접 치자 연결·분석 단계까지 갔고, 파일 616개가 한도 150을 넘어 거절됐다(`Too many files`. 출력을 손으로 봤다). `--dir tools`로 좁히자 `findings: 0`으로 끝났다.
   - 새 사실: 무료 판의 CLI는 좌석이 없어도 돌고, 한 번에 보는 파일에 150개 한도가 있다. 대기열 이행처럼 파일이 많은 PR은 `--dir`로 나눠 돌려야 한다. 0578의 처방(1단계가 `Seat: not assigned`로 종료하지 않는다)에 이 한도 문장을 함께 넣는다.
   - 층: 정의 문장의 고침이다. 항목 0578이 5회차로 chore 배치 조건을 이미 채웠으니, 새로 만들지 않고 회차만 더했다(승인 줄 5회차에서 6회차).
2. **승인: 문장을 더한 셀프 리뷰 반영이 카나리아의 `expect`에 묶이지 않았다(대기열 0310에 3회차).**
   - 사건: 셀프 리뷰 반영이 `retro`와 `next-session`에 문장 둘을 더했는데, 두 카나리아 명세의 물음이 그 문장을 묻지 않아 다시 돌려도 그 문장이 실렸는지 알 수 없었다. 이 세션이 물음을 하나씩 더해(`retro_row_search` 5번, `next_session_queue_open_rows` 3번) 돌리고서야 확인했다.
   - 층: `tools/canary.py`가 판정하는 쪽은 대기열 538이 맡는다. 0310의 처방(바뀐 단락이 결정을 여럿 담으면 결정마다 카나리아 하나)과 같은 꼴이라 회차만 더했다.
3. **기각 둘.** 커밋 메시지 제목 72자 초과(`hook_bash_commit_msg`가 커밋 전에 막았다. 이미 있는 훅이 제 몫을 했다). 워크트리 가드의 "too complex" 거부(`git add`와 `cat` heredoc을 한 명령으로 묶은 것. `CLAUDE.md` 환경 함정이 이미 적은 모양이다).

0578은 이제 6회차이므로 다음 chore 배치 조건에 계속 든다.

## 인계

컨텍스트가 인계 문턱을 넘은 채 단계 경계 `커밋 뒤`에 닿아 이 세션을 같은 브랜치의 새 세션으로 넘긴다. 커밋은 pre-commit을 통과했고(종료 0) 푸시와 PR은 아직이다. 세션 제목은 `feature/02-retro-queue-one-file-per-item (인계함)`으로 바꿨고 워크트리 잠금을 풀었다.

open-session을 부른다 2026-11-06T20:31:20Z

## 다음

이 PR(티켓 02)이 병합되면 같은 기능의 막힘이 풀린 티켓은 03(리뷰 봇 경로 거르기)과 04(일지 이름)이고, 둘은 나란히 연다. 05 이후는 03·04가 끝나야 열린다.

- **먼저 할 것(병합 직후).** `.scratch/harness/probes/msys_pathconv/run.sh`의 C절을 병합된 main에서 다시 돌린다. 이 PR에서는 폴더가 origin/main에 없어 우회 종료 코드가 기대와 다르게 나왔다(1이 찍혔다). 코드를 읽은 것이 아니라 실행 결과를 받아야 하는 몫이다.
- **03의 몫으로 남긴 것.** `.github/workflows/claude-code-review.yml:97`의 `\.scratch/retro-queue\.md$` 거르기와 `review_workflow.py`의 `QUEUE`, `.github/PULL_REQUEST_TEMPLATE.md:43`·`claude-code-review.yml:77·99`의 "일지·대기열·하네스 탐침 밖의 파일" 경로 문구다. 리뷰 봇 워크플로를 바꾸는 PR은 따로 먼저 병합한다는 규약 때문에 이 PR에 싣지 않았다.
- **회고 후보.** `retro/SKILL.md` 머리 주석의 "행", `MIN_ROWS`·`--rows`·`QueueRow`·`retro_rows`처럼 행 단위로 남은 이름은 이름 낡음이라 바꾸면 인용이 깨진다. 지금은 두고 대기열 후보로 올릴지 다음 회고가 정한다.
- **CodeRabbit CLI.** 파일이 많은 PR은 150개 한도에 걸린다(0578의 6회차에 적었다). 03·04처럼 작은 PR은 전체를 돌린다.
- **주 체크아웃.** 이 세션은 병합 뒤 주 체크아웃을 당기지 않는다. 다음 세션이 워크트리에 들어가기 전에 `tidy-checkouts`를 먼저 돈다.
